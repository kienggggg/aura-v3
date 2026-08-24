# -*- coding: utf-8 -*-
"""tools/_worker_e1_exec.py — E1 Worker thực thi phân tích định vị lỗi bên trong temp clone.

Chạy hoàn toàn bên trong temp clone, không truy cập kho gốc hay mạng bên ngoài.
Thực hiện 4 bước:
1. Thu vết dòng chạy trên test chọn (Trace).
2. Liệt kê 5 họ phép nghịch AST và lọc ứng viên theo dòng chạy.
3. Lật thử trên test chọn (chỉ giữ ứng viên làm test chọn XANH).
4. Kiểm thử hồi quy toàn bộ suite bằng selector:
   `python -B -X utf8 -m pytest tests -m "not e1_control" -q --no-header -p no:cacheprovider`
"""
from __future__ import annotations

import ast
import difflib
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.trace_runtime import chot_test_can_trace

PY = sys.executable

OP_STR = {
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Eq: "==",
    ast.NotEq: "!=",
}


def doc_thong_tin_gioi_han(project_root: Path) -> str:
    """Đọc động số liệu giới hạn thực tế từ sổ bằng chứng ngoài họ."""
    sprint_file = project_root / "data" / "evidence_sprint" / "e1_ngoai_ho.json"
    if sprint_file.is_file():
        try:
            data = json.loads(sprint_file.read_text(encoding="utf-8"))
            danh_sach = data.get("ket_qua", [])
            tong_de = len(danh_sach)
            tim_ra = sum(1 for d in danh_sach if d.get("tim_thay"))
            if tim_ra == 0:
                return f"Chỉ dò được 5 họ lỗi so sánh/logic. Đã thử {tong_de} lỗi NGOÀI 5 họ đó — không dò ra ca nào."
            else:
                return f"Chỉ dò được 5 họ lỗi so sánh/logic. Đã thử {tong_de} lỗi NGOÀI 5 họ đó (tìm ra {tim_ra} ca)."
        except Exception:
            pass
    return "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi."

NGHICH_SS = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}

PHAM_VI_PHEP = [
    "so_sanh",
    "logic",
    "bo_phu_dinh",
    "bool_constant",
    "int_constant",
]


def lat_tren_van_ban(nguon: str, node: ast.AST, tu: str, sang: str) -> str:
    """Đổi ĐÚNG một token toán tử trong vùng của node, giữ nguyên mọi byte khác."""
    dong = nguon.splitlines(keepends=True)
    bat_dau = sum(len(d) for d in dong[:node.lineno - 1]) + node.col_offset
    ket = sum(len(d) for d in dong[:node.end_lineno - 1]) + node.end_col_offset
    if isinstance(node, ast.Constant):
        return nguon[:bat_dau] + sang + nguon[ket:]
    vung = nguon[bat_dau:ket]
    for tok in tokenize.generate_tokens(io.StringIO(vung).readline):
        if tok.string == tu and tok.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER):
            r0 = sum(len(l) for l in vung.splitlines(keepends=True)[:tok.start[0] - 1]) + tok.start[1]
            return nguon[:bat_dau + r0] + sang + nguon[bat_dau + r0 + len(tu):]
    raise ValueError(f"khong thay token '{tu}' trong vung node")


class _Lat(ast.NodeTransformer):
    """Lật ĐÚNG MỘT chỗ theo chỉ số `muc`. Đếm theo thứ tự duyệt AST."""

    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.da = ""
        self.danh_sach: list[tuple[int, int, str]] = []
        self.target_node: Optional[ast.AST] = None
        self.tu: str = ""
        self.sang: str = ""

    def _lay(self, ten: str, nut: ast.AST, tu: str = "", sang: str = "") -> bool:
        d = self.dem
        self.danh_sach.append((d, int(getattr(nut, "lineno", 0) or 0), ten))
        self.dem += 1
        if d == self.muc:
            self.da = ten
            self.target_node = nut
            self.tu = tu
            self.sang = sang
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            op_cls = type(n.ops[0])
            target_cls = NGHICH_SS[op_cls]
            tu = OP_STR[op_cls]
            sang = OP_STR[target_cls]
            if self._lay(f"so sánh {op_cls.__name__} -> {target_cls.__name__}", n, tu=tu, sang=sang):
                n.ops = [target_cls()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.And):
            if self._lay("logic And -> Or", n, tu="and", sang="or"):
                n.op = ast.Or()
        elif isinstance(n.op, ast.Or):
            if self._lay("logic Or -> And", n, tu="or", sang="and"):
                n.op = ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n, tu="not", sang=""):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            target_val = not n.value
            if self._lay(f"bool {n.value} -> {target_val}", n, tu=str(n.value), sang=str(target_val)):
                return ast.Constant(value=target_val)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            # Parity AST legacy: n -> n - 1 (với literal âm -5 là USub(Constant(5)) -> USub(Constant(4)) tức -4)
            if self._lay(f"số {n.value} -> {n.value - 1}", n, tu=str(n.value), sang=str(n.value - 1)):
                return ast.Constant(value=n.value - 1)
        return n


def _liet_ke_cho(ma: str) -> list[tuple[int, int, str]]:
    d = _Lat(-1)
    d.visit(ast.parse(ma))
    return [(chi_so, dong, ten) for chi_so, dong, ten in d.danh_sach]


def _ma_sau_lat(nguon: str, chi_so: int) -> tuple[str, str]:
    bd = _Lat(chi_so)
    bd.visit(ast.parse(nguon))
    if bd.target_node is not None:
        moi = lat_tren_van_ban(nguon, bd.target_node, bd.tu, bd.sang)
        return moi, bd.da
    return nguon, ""


def tao_cac_ung_vien(ma: str, dong_da_chay: Optional[Set[int]] = None) -> list[tuple[int, str, str]]:
    cac_cho = _liet_ke_cho(ma)
    res = []
    for chi_so, dong, mo_ta in cac_cho:
        if dong_da_chay is not None and dong not in dong_da_chay:
            continue
        ma_moi, da = _ma_sau_lat(ma, chi_so)
        res.append((dong, mo_ta, ma_moi))
    return res


def _tao_unified_diff(goc_str: str, moi_str: str, filename: str) -> str:
    lines_goc = goc_str.splitlines(keepends=True)
    lines_moi = moi_str.splitlines(keepends=True)
    diff = difflib.unified_diff(
        lines_goc,
        lines_moi,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def _chon_test_va_dong(
    tam: Path,
    tep_nguon_rel: str,
    tep_test_rel: str,
    deadline: float,
) -> dict:
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {"trang_thai": "khong_chay", "vi_sao": "Hết trần thời gian trước khi trace", "test": "", "so_test_do_khac": 0, "dong_da_chay": []}

    ten_chot, so_khac, danh_sach = chot_test_can_trace(
        tep_nguon=tep_nguon_rel,
        tep_test=tep_test_rel,
        cwd=tam,
    )
    if not ten_chot or not danh_sach:
        return {"trang_thai": "khong_chay", "vi_sao": "Không có test nào bị đỏ trong tệp test", "test": "", "so_test_do": 0, "so_test_do_khac": 0, "dong_da_chay": []}

    chot_res = danh_sach[0]
    return {
        "trang_thai": chot_res.trang_thai,
        "vi_sao": chot_res.thong_diep,
        "test": ten_chot,
        "so_test_do": so_khac + 1,
        "so_test_do_khac": so_khac,
        "dong_da_chay": chot_res.dong_da_chay,
        "so_buoc": chot_res.tong_buoc,
    }


def chay_worker(
    tam_clone: Path,
    tep_nguon_rel: str,
    tep_test_rel: str,
    source_sha256: str = "",
    test_sha256: str = "",
    filter_mutate_timeout_s: float = 60.0,
    full_suite_timeout_s: float = 180.0,
) -> dict:
    t0_tong = time.monotonic()
    tep_nguon_rel = tep_nguon_rel.replace("\\", "/")
    tep_test_rel = tep_test_rel.replace("\\", "/")

    target_file = tam_clone / tep_nguon_rel
    test_file = tam_clone / tep_test_rel

    if not target_file.is_file() or not test_file.is_file():
        return {
            "trang_thai": "khong_do_duoc",
            "reason": "Tệp nguồn hoặc tệp test không tồn tại trong clone",
        }

    raw_goc = target_file.read_text(encoding="utf-8")
    try:
        ast.parse(raw_goc)
    except Exception as exc:
        return {
            "trang_thai": "khong_do_duoc",
            "reason": f"Không thể parse AST tệp nguồn: {exc}",
        }

    cac_cho_all = _liet_ke_cho(raw_goc)
    n_before = len(cac_cho_all)

    # Bước 1: Trace dòng chạy trên test đỏ
    t0_loc = time.monotonic()
    deadline_loc = t0_loc + filter_mutate_timeout_s
    trace = _chon_test_va_dong(tam_clone, tep_nguon_rel, tep_test_rel, deadline_loc)

    if trace.get("trang_thai") != "trace_du":
        return {
            "trang_thai": "khong_tim_thay" if trace.get("so_test_do") == 0 else "khong_do_duoc",
            "source_path": tep_nguon_rel,
            "source_sha256": source_sha256,
            "test_file": tep_test_rel,
            "test_sha256": test_sha256,
            "selected_test": trace.get("test", ""),
            "other_red_test_count": trace.get("so_test_do_khac", 0),
            "executed_lines": trace.get("dong_da_chay", []),
            "candidate_count_before": n_before,
            "candidate_count_after": 0,
            "scope_operations": PHAM_VI_PHEP,
            "elapsed_filter_mutate_s": round(time.monotonic() - t0_loc, 1),
            "elapsed_full_suite_s": 0.0,
            "analysis_on_temp_copy": True,
            "model_calls": 0,
            "external_submit": False,
            "candidates": [],
            "reason": trace.get("vi_sao", "Không có vết dòng đầy đủ"),
            "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
        }

    selected_test = trace["test"]
    dong_da_chay = set(trace["dong_da_chay"])

    # Bước 2: Lọc các chỗ nằm trên dòng đã chạy
    cac_cho_loc = [c for c in cac_cho_all if c[1] in dong_da_chay]
    n_after = len(cac_cho_loc)

    # Bước 3: Lật thử trên test chọn
    xanh_selected: list[dict] = []
    for chi_so, dong, mo_ta in cac_cho_loc:
        if time.monotonic() > deadline_loc:
            break
        ma_moi, da = _ma_sau_lat(raw_goc, chi_so)
        target_file.write_text(ma_moi, encoding="utf-8")
        try:
            r = subprocess.run(
                [PY, "-B", "-X", "utf8", "-m", "pytest", tep_test_rel, "-q", "--no-header", "-x", "-p", "no:cacheprovider"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tam_clone),
                timeout=10.0,
            )
            if r.returncode == 0:
                diff_text = _tao_unified_diff(raw_goc, ma_moi, tep_nguon_rel)
                xanh_selected.append({
                    "index": chi_so,
                    "line": dong,
                    "operation": mo_ta,
                    "ma": ma_moi,
                    "unified_diff": diff_text,
                })
        except Exception:
            continue

    # Khôi phục file về nguyên trạng sau bước lọc + lật
    target_file.write_text(raw_goc, encoding="utf-8")
    t_lat_end = time.monotonic()
    elapsed_filter_mutate = round(t_lat_end - t0_loc, 1)

    if elapsed_filter_mutate > filter_mutate_timeout_s:
        return {
            "trang_thai": "khong_do_duoc",
            "source_path": tep_nguon_rel,
            "source_sha256": source_sha256,
            "test_file": tep_test_rel,
            "test_sha256": test_sha256,
            "selected_test": selected_test,
            "other_red_test_count": trace.get("so_test_do_khac", 0),
            "executed_lines": sorted(dong_da_chay),
            "candidate_count_before": n_before,
            "candidate_count_after": n_after,
            "scope_operations": PHAM_VI_PHEP,
            "elapsed_filter_mutate_s": elapsed_filter_mutate,
            "elapsed_full_suite_s": 0.0,
            "analysis_on_temp_copy": True,
            "model_calls": 0,
            "external_submit": False,
            "candidates": [],
            "reason": "Lọc + lật vượt trần thời gian quy định",
            "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
        }

    # Bước 4: Full suite regression cho các ứng viên làm test chọn XANH
    t0_suite = time.monotonic()
    candidates_out: list[dict] = []
    co_ban_va_xanh_suite = False

    for cand in xanh_selected:
        target_file.write_text(cand["ma"], encoding="utf-8")
        full_suite_status = "ĐỎ"
        so_test_hong = 0
        ly_do_khong_do = ""
        try:
            r_suite = subprocess.run(
                [
                    PY, "-B", "-X", "utf8", "-m", "pytest", "tests",
                    "-m", "not e1_control",
                    "-q", "--no-header", "-p", "no:cacheprovider",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tam_clone),
                timeout=full_suite_timeout_s,
            )
            out_text = (r_suite.stdout or "") + "\n" + (r_suite.stderr or "")
            if r_suite.returncode == 0:
                full_suite_status = "XANH"
                co_ban_va_xanh_suite = True
                so_test_hong = 0
            else:
                if "ERROR collecting" in out_text or "errors during collection" in out_text or r_suite.returncode not in (0, 1):
                    full_suite_status = "suite_khong_do_duoc"
                    ly_do_khong_do = "Lỗi thu thập test suite"
                    so_test_hong = 0
                else:
                    found_failed = False
                    for line in out_text.splitlines():
                        if "failed" in line:
                            m = re.search(r"(\d+)\s+failed", line)
                            if m:
                                so_test_hong = int(m.group(1))
                                found_failed = True
                                break
                    if not found_failed:
                        count_f = out_text.count("FAILED")
                        if count_f > 0:
                            so_test_hong = count_f
                            found_failed = True
                    if found_failed and so_test_hong > 0:
                        full_suite_status = "ĐỎ"
                    else:
                        full_suite_status = "suite_khong_do_duoc"
                        ly_do_khong_do = "Không đo được kết quả suite"
                        so_test_hong = 0
        except subprocess.TimeoutExpired:
            full_suite_status = "suite_khong_do_duoc"
            ly_do_khong_do = f"Quá giờ ({full_suite_timeout_s}s)"
            so_test_hong = 0
        except Exception as exc:
            full_suite_status = "suite_khong_do_duoc"
            ly_do_khong_do = f"Ngoại lệ: {exc}"
            so_test_hong = 0

        cand_entry = {
            "index": cand["index"],
            "line": cand["line"],
            "operation": cand["operation"],
            "unified_diff": cand["unified_diff"],
            # 24/08: diff nay sinh tu _tao_unified_diff(raw_goc, ma_moi) — van ban
            # goc, KHONG con di qua ast.unparse. Nhan cu doc nguoc voi thuc te.
            "diff_basis": "van_ban_goc_temp_copy",
            "selected_test_status": "XANH",
            "full_suite_status": full_suite_status,
            "so_test_hong": so_test_hong if full_suite_status == "ĐỎ" else 0,
            "ma": cand["ma"],
        }
        if ly_do_khong_do:
            cand_entry["ly_do_suite"] = ly_do_khong_do
        candidates_out.append(cand_entry)

    # Khôi phục lại file gốc
    target_file.write_text(raw_goc, encoding="utf-8")
    elapsed_suite = round(time.monotonic() - t0_suite, 1)

    if co_ban_va_xanh_suite:
        trang_thai = "tim_thay"
        reason = f"Đã tìm thấy {sum(1 for c in candidates_out if c['full_suite_status'] == 'XANH')} bản vá xanh toàn bộ suite."
    elif any(c["full_suite_status"] == "suite_khong_do_duoc" for c in candidates_out) and not any(c["full_suite_status"] == "XANH" for c in candidates_out):
        trang_thai = "suite_khong_do_duoc"
        reasons_list = [c["ly_do_suite"] for c in candidates_out if c.get("ly_do_suite")]
        reasons_str = f" ({', '.join(reasons_list)})" if reasons_list else ""
        reason = f"Ứng viên làm xanh test chọn nhưng suite không đo được{reasons_str}."
    elif candidates_out:
        trang_thai = "ung_vien_khong_qua_suite"
        reason = f"Có {len(candidates_out)} ứng viên làm xanh test chọn nhưng không vượt qua toàn bộ test suite."
    else:
        trang_thai = "khong_tim_thay"
        reason = "Không có ứng viên nào trong phạm vi 5 phép làm xanh test chọn."

    return {
        "trang_thai": trang_thai,
        "source_path": tep_nguon_rel,
        "source_sha256": source_sha256,
        "test_file": tep_test_rel,
        "test_sha256": test_sha256,
        "selected_test": selected_test,
        "other_red_test_count": trace.get("so_test_do_khac", 0),
        "executed_lines": sorted(dong_da_chay),
        "candidate_count_before": n_before,
        "candidate_count_after": n_after,
        "scope_operations": PHAM_VI_PHEP,
        "regression_suite_selector": "not e1_control",
        "elapsed_filter_mutate_s": elapsed_filter_mutate,
        "elapsed_full_suite_s": elapsed_suite,
        "analysis_on_temp_copy": True,
        "model_calls": 0,
        "external_submit": False,
        "candidates": candidates_out,
        "reason": reason,
        "limitation": doc_thong_tin_gioi_han(tam_clone),
    }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"trang_thai": "khong_do_duoc", "reason": "Thiếu tham số chạy worker"}))
        sys.exit(1)

    tep_nguon = sys.argv[1]
    tep_test = sys.argv[2]
    source_sha = sys.argv[3] if len(sys.argv) > 3 else ""
    test_sha = sys.argv[4] if len(sys.argv) > 4 else ""

    tam_clone = Path(".").resolve()

    # Worker GHI ĐÈ tệp nguồn để thử từng phép lật (dòng 245 + vòng lặp bên dưới),
    # và chỉ ghi trả lại ở cuối. Chạy nhầm ở kho thật thì mỗi lần nó chết giữa
    # chừng là để lại tệp ĐANG MANG LỖI GIEO trên đĩa.
    #
    # Đã xảy ra 24/08/2026: `core/dong_ho.py` trên đĩa lệch HEAD 1762/1722 byte.
    # Lần ấy chỉ là 40 dòng CRLF vì lượt ghi trả lại có chạy — nhưng nó chứng minh
    # worker đã đụng vào kho thật, và lần sau chết sớm hơn thì mất nội dung.
    #
    # Bản sao do e1_supervisor_bootstrap.py dựng KHÔNG chép `.git` (dòng 192).
    # Kho thật thì có. Đó là dấu hiệu rẻ nhất và không đoán được nhầm.
    if (tam_clone / ".git").exists():
        print(json.dumps({
            "trang_thai": "khong_do_duoc",
            "reason": (
                "Từ chối chạy: thư mục hiện tại có .git nên đây là kho thật, "
                "không phải bản sao tạm. Worker ghi đè tệp nguồn khi thử phép lật. "
                "Hãy gọi qua tools/e1_supervisor_bootstrap.py, hoặc cd sang bản sao."
            ),
            "cwd": str(tam_clone),
        }, ensure_ascii=False, indent=2))
        sys.exit(2)

    res = chay_worker(
        tam_clone=tam_clone,
        tep_nguon_rel=tep_nguon,
        tep_test_rel=tep_test,
        source_sha256=source_sha,
        test_sha256=test_sha,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
