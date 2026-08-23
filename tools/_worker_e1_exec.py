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
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.trace_runtime import chot_test_can_trace

PY = sys.executable


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


class _Lat(ast.NodeTransformer):
    """Lật ĐÚNG MỘT chỗ theo chỉ số `muc`. Đếm theo thứ tự duyệt AST."""

    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.da = ""
        self.danh_sach: list[tuple[int, int, str]] = []

    def _lay(self, ten: str, nut: ast.AST) -> bool:
        d = self.dem
        self.danh_sach.append((d, int(getattr(nut, "lineno", 0) or 0), ten))
        self.dem += 1
        if d == self.muc:
            self.da = ten
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            op_cls = type(n.ops[0])
            target_cls = NGHICH_SS[op_cls]
            if self._lay(f"so sánh {op_cls.__name__} -> {target_cls.__name__}", n):
                n.ops = [target_cls()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.And):
            if self._lay("logic And -> Or", n):
                n.op = ast.Or()
        elif isinstance(n.op, ast.Or):
            if self._lay("logic Or -> And", n):
                n.op = ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            target_val = not n.value
            if self._lay(f"bool {n.value} -> {target_val}", n):
                return ast.Constant(value=target_val)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            # Parity AST legacy: n -> n - 1 (với literal âm -5 là USub(Constant(5)) -> USub(Constant(4)) tức -4)
            if self._lay(f"số {n.value} -> {n.value - 1}", n):
                return ast.Constant(value=n.value - 1)
        return n


def _liet_ke_cho(ma: str) -> list[tuple[int, int, str]]:
    d = _Lat(-1)
    d.visit(ast.parse(ma))
    return [(chi_so, dong, ten) for chi_so, dong, ten in d.danh_sach]


def _ma_sau_lat(nguon: str, chi_so: int) -> tuple[str, str]:
    bd = _Lat(chi_so)
    moi = ast.unparse(ast.fix_missing_locations(bd.visit(ast.parse(nguon))))
    return moi, bd.da


def tao_cac_ung_vien(ma: str, dong_da_chay: Optional[Set[int]] = None) -> list[tuple[int, str, str]]:
    cac_cho = _liet_ke_cho(ma)
    res = []
    for chi_so, dong, mo_ta in cac_cho:
        if dong_da_chay is not None and dong not in dong_da_chay:
            continue
        ma_moi, da = _ma_sau_lat(ma, chi_so)
        res.append((dong, mo_ta, ma_moi))
    return res


def _tao_unified_diff(goc_ast_str: str, moi_ast_str: str, filename: str) -> str:
    lines_goc = goc_ast_str.splitlines(keepends=True)
    lines_moi = moi_ast_str.splitlines(keepends=True)
    diff = difflib.unified_diff(
        lines_goc,
        lines_moi,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def _chon_test_va_dong(
    tam: Path,
    tep_nguon: str,
    tep_test: str,
    deadline: float,
) -> dict:
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {"trang_thai": "khong_chay", "vi_sao": "Hết trần thời gian trước khi trace", "test": "", "so_test_do_khac": 0, "dong_da_chay": []}

    ten_chot, so_khac, danh_sach = chot_test_can_trace(
        tep_nguon=tep_nguon,
        tep_test=tep_test,
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
        chuan_ast_goc = ast.unparse(ast.parse(raw_goc))
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
                diff_text = _tao_unified_diff(chuan_ast_goc, ma_moi, tep_nguon_rel)
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
        suite_pass = False
        so_test_hong = 0
        try:
            r_suite = subprocess.run(
                [
                    PY, "-B", "-X", "utf8", "-m", "pytest", tep_test_rel, "tests",
                    "-m", "not e1_control",
                    "-q", "--no-header", "--tb=no", "-x", "-p", "no:cacheprovider",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tam_clone),
                timeout=full_suite_timeout_s,
            )
            if r_suite.returncode == 0:
                suite_pass = True
                co_ban_va_xanh_suite = True
            else:
                out_text = (r_suite.stdout or "") + "\n" + (r_suite.stderr or "")
                for line in out_text.splitlines():
                    if "failed" in line:
                        m = re.search(r"(\d+)\s+failed", line)
                        if m:
                            so_test_hong = int(m.group(1))
                            break
                if so_test_hong == 0:
                    so_test_hong = max(1, out_text.count("FAILED") or 1)
        except Exception:
            suite_pass = False
            so_test_hong = 1

        candidates_out.append({
            "index": cand["index"],
            "line": cand["line"],
            "operation": cand["operation"],
            "unified_diff": cand["unified_diff"],
            "diff_basis": "ast_normalized_temp_copy",
            "selected_test_status": "XANH",
            "full_suite_status": "XANH" if suite_pass else "ĐỎ",
            "so_test_hong": so_test_hong if not suite_pass else 0,
            "ma": cand["ma"],
        })

    # Khôi phục lại file gốc
    target_file.write_text(raw_goc, encoding="utf-8")
    elapsed_suite = round(time.monotonic() - t0_suite, 1)

    if co_ban_va_xanh_suite:
        trang_thai = "tim_thay"
        reason = f"Đã tìm thấy {sum(1 for c in candidates_out if c['full_suite_status'] == 'XANH')} bản vá xanh toàn bộ suite."
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
