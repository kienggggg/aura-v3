# -*- coding: utf-8 -*-
"""core/lat_nguoc.py — Worker E1: Lật ngược đột biến & lọc theo vết thực thi.

ĐẶC TẢ SẢN PHẨM (Chỉ-phân-tích):
1. Nhận tệp nguồn và tệp test, chạy hoàn toàn trên bản sao tạm (temp clone).
2. Tuyệt đối không gọi dot_bien(), không gieo lỗi vào mã, không biết đáp án trước.
3. Không gọi model/AI, không kết nối mạng, không publish/submit bên ngoài.
4. Không ghi đè hay sửa đổi bất kỳ byte nào trên tệp nguồn thật.
5. Thực hiện 5 phép nghịch AST chuẩn (so sánh, bool op, bỏ unary not, đảo bool, trừ 1 số nguyên).
6. Fail-closed: xóa sạch thư mục tạm sau khi hoàn tất.
"""
from __future__ import annotations

import ast
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.trace_runtime import chot_test_can_trace, chay_trace_mot_test, TraceResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable or str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe")

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
    """Lật ĐÚNG MỘT chỗ, chỉ số `muc`. Đếm theo cùng thứ tự với phép duyệt AST."""

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
            if self._lay(f"số {n.value} -> {n.value - 1}", n, tu=str(n.value), sang=str(n.value - 1)):
                return ast.Constant(value=n.value - 1)
        return n


def _liet_ke_cho(ma: str) -> list[tuple[int, int, str]]:
    """Liệt kê (chỉ số, dòng, mô tả) theo đúng thứ tự hậu duyệt của _Lat."""
    d = _Lat(-1)
    d.visit(ast.parse(ma))
    return [(chi_so, dong, ten) for chi_so, dong, ten in d.danh_sach]


def _ma_sau_lat(nguon: str, chi_so: int) -> tuple[str, str]:
    """Lật đúng chỉ số trên một cây AST mới."""
    bd = _Lat(chi_so)
    bd.visit(ast.parse(nguon))
    if bd.target_node is not None:
        moi = lat_tren_van_ban(nguon, bd.target_node, bd.tu, bd.sang)
        return moi, bd.da
    return nguon, ""


def tao_cac_ung_vien(ma: str, dong_da_chay: Optional[Set[int]] = None) -> list[tuple[int, str, str]]:
    """Tạo danh sách ứng viên (dong, mo_ta_phep, ma_moi)."""
    cac_cho = _liet_ke_cho(ma)
    res = []
    for chi_so, dong, mo_ta in cac_cho:
        if dong_da_chay is not None and dong not in dong_da_chay:
            continue
        ma_moi, da = _ma_sau_lat(ma, chi_so)
        res.append((dong, mo_ta, ma_moi))
    return res


def _tao_unified_diff(goc_str: str, moi_str: str, filename: str) -> str:
    """Tạo unified diff giữa hai bản văn bản."""
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
    tep_nguon: str,
    tep_test: str,
    deadline: float,
) -> dict:
    """Chọn test đỏ theo thứ tự 3 tầng và trả về kết quả trace từ trace_runtime."""
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {
            "trang_thai": "khong_chay",
            # `ma_ly_do` là MÃ cho máy đọc; `vi_sao` là câu cho người đọc.
            # Xem chú thích 25/08 ở chỗ dùng nó bên dưới.
            "ma_ly_do": "het_tran_truoc_trace",
            "vi_sao": "hết trần 60 giây trước trace",
            "test": "",
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
    ten_chot, so_khac, danh_sach = chot_test_can_trace(
        tep_nguon=tep_nguon,
        tep_test=tep_test,
        cwd=tam,
    )
    if not ten_chot or not danh_sach:
        return {
            "trang_thai": "khong_chay",
            "ma_ly_do": "khong_co_test_do",
            "vi_sao": "không có test nào bị đỏ trong tệp test",
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }

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


def chay_e1_dinh_vi(
    project_root: Path,
    tep_nguon_rel: str,
    tep_test_rel: str,
    source_sha256: str = "",
    test_sha256: str = "",
    timeout_s: float = 180.0,
    filter_mutate_timeout_s: float = 60.0,
) -> dict:
    """Thực thi phân tích định vị lỗi E1 trên bản sao tạm (temp clone)."""
    t0_tong = time.monotonic()
    deadline_tong = t0_tong + timeout_s

    # Chuẩn hóa đường dẫn tương đối (posix)
    tep_nguon_rel = tep_nguon_rel.replace("\\", "/")
    tep_test_rel = tep_test_rel.replace("\\", "/")

    tam_goc = Path(tempfile.mkdtemp(prefix="aura_e1_"))
    tam = tam_goc / "kho"

    try:
        # Clone repo sang temp
        shutil.copytree(
            project_root,
            tam,
            ignore=shutil.ignore_patterns(
                "venv",
                ".venv*",
                ".git",
                "__pycache__",
                ".pytest_cache",
                "data",
                "_rac",
                "*.pyc",
            ),
        )
        (tam / "data").mkdir(exist_ok=True)

        target_file = tam / tep_nguon_rel
        if not target_file.is_file():
            return {
                "trang_thai": "khong_do_duoc",
                "source_path": tep_nguon_rel,
                "source_sha256": source_sha256,
                "test_file": tep_test_rel,
                "test_sha256": test_sha256,
                "selected_test": "",
                "other_red_test_count": 0,
                "executed_lines": [],
                "candidate_count_before": 0,
                "candidate_count_after": 0,
                "scope_operations": PHAM_VI_PHEP,
                "elapsed_filter_mutate_s": 0.0,
                "elapsed_full_suite_s": 0.0,
                "analysis_on_temp_copy": True,
                "model_calls": 0,
                "external_submit": False,
                "candidates": [],
                "reason": f"Tệp nguồn không tồn tại trong bản sao: {tep_nguon_rel}",
                "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
            }

        nguon_text = target_file.read_text(encoding="utf-8")
        cac_cho = _liet_ke_cho(nguon_text)
        so_cho_truoc_loc = len(cac_cho)

        # Bước 1: Trace dòng & chọn test đỏ
        t0_loc = time.monotonic()
        deadline_loc_lat = min(deadline_tong, t0_loc + filter_mutate_timeout_s)
        trace = _chon_test_va_dong(tam, tep_nguon_rel, tep_test_rel, deadline=deadline_loc_lat)

        if trace.get("trang_thai") != "trace_du":
            giay_loc = round(time.monotonic() - t0_loc, 1)
            vi_sao = trace.get("vi_sao", "Không thu thập được vết dòng đầy đủ")
            # 25/08: TRƯỚC ĐÂY DÒNG NÀY DÒ CHUỖI CON TRÊN CÂU TIẾNG VIỆT.
            #
            #     trang_thai_ra = ("khong_tim_thay"
            #                      if "không có test nào bị đỏ" in vi_sao
            #                      else "khong_do_duoc")
            #
            # `vi_sao` là câu viết cho NGƯỜI ĐỌC. Đem nó ra quyết định luồng
            # điều khiển thì sửa lại câu chữ cho dễ đọc là đủ đổi kết quả.
            # Chạy thử 25/08, hai cách viết cùng nghĩa:
            #
            #     "không có test nào bị đỏ trong tệp test"  ->  khong_tim_thay
            #     "không có test nào ĐỎ trong tệp test"     ->  khong_do_duoc
            #
            # Mà hai trạng thái ấy NGƯỢC NHAU trong kỷ luật của kho:
            # `khong_tim_thay` = ĐO ĐƯỢC mà không thấy;
            # `khong_do_duoc`  = KHÔNG đo được.
            # Ghi nhầm loại là sổ bằng chứng nói sai về chính phép đo.
            #
            # Đúng họ bệnh §4 "đừng tự chấm điểm bằng dò chuỗi con" — kho này
            # đã trả giá năm lần trong một ngày cho nó ("ai" khớp trong "thứ
            # hai"; "phiên này" bỏ dấu thành "p·hien nay" rồi khớp "hiện nay").
            #
            # Nay `_chon_test_va_dong` trả kèm `ma_ly_do` — mã cho máy đọc,
            # tách khỏi `vi_sao` cho người đọc. Đổi câu chữ không còn đổi được
            # kết quả nữa. Hành vi giữ NGUYÊN: đường duy nhất cho ra
            # `khong_tim_thay` vẫn đúng là đường "không có test nào bị đỏ".
            trang_thai_ra = ("khong_tim_thay"
                             if trace.get("ma_ly_do") == "khong_co_test_do"
                             else "khong_do_duoc")
            return {
                "trang_thai": trang_thai_ra,
                "source_path": tep_nguon_rel,
                "source_sha256": source_sha256,
                "test_file": tep_test_rel,
                "test_sha256": test_sha256,
                "selected_test": "",
                "other_red_test_count": 0,
                "executed_lines": [],
                "candidate_count_before": so_cho_truoc_loc,
                "candidate_count_after": 0,
                "scope_operations": PHAM_VI_PHEP,
                "elapsed_filter_mutate_s": giay_loc,
                "elapsed_full_suite_s": 0.0,
                "analysis_on_temp_copy": True,
                "model_calls": 0,
                "external_submit": False,
                "candidates": [],
                "reason": vi_sao,
                "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
            }

        dong_da_chay = set(trace.get("dong_da_chay", []))
        test_do_duoc_chon = trace.get("test", "")
        so_test_do_khac = trace.get("so_test_do_khac", 0)

        # Bước 2: Lọc ứng viên theo dòng chạy
        cho_sau_loc = [
            (chi_so, dong, mo_ta)
            for chi_so, dong, mo_ta in cac_cho
            if dong in dong_da_chay
        ]
        so_cho_sau_loc = len(cho_sau_loc)

        # Bước 3: Thử lật từng ứng viên
        xanh_selected: list[dict] = []
        qua_gio = False

        for chi_so, dong, mo_ta in cho_sau_loc:
            con_lai = deadline_loc_lat - time.monotonic()
            if con_lai <= 0:
                qua_gio = True
                break
            try:
                moi_text, phep_ten = _ma_sau_lat(nguon_text, chi_so)
            except Exception:
                continue
            if moi_text == nguon_text:
                continue

            target_file.write_text(moi_text, encoding="utf-8")
            try:
                r_test = subprocess.run(
                    [
                        PY, "-X", "utf8", "-m", "pytest", test_do_duoc_chon,
                        "-q", "--no-header", "--tb=line", "-p", "no:cacheprovider",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(tam),
                    timeout=max(0.1, min(15.0, con_lai)),
                )
                if r_test.returncode == 0:
                    diff = _tao_unified_diff(nguon_text, moi_text, tep_nguon_rel)
                    xanh_selected.append({
                        "index": chi_so,
                        "line": dong,
                        "operation": phep_ten,
                        "unified_diff": diff,
                        "ma": moi_text,
                    })
            except subprocess.TimeoutExpired:
                qua_gio = True
                break
            except Exception:
                continue

        giay_loc_va_lat = round(time.monotonic() - t0_loc, 1)

        if qua_gio and not xanh_selected:
            return {
                "trang_thai": "khong_do_duoc",
                "source_path": tep_nguon_rel,
                "source_sha256": source_sha256,
                "test_file": tep_test_rel,
                "test_sha256": test_sha256,
                "selected_test": test_do_duoc_chon,
                "other_red_test_count": so_test_do_khac,
                "executed_lines": sorted(dong_da_chay),
                "candidate_count_before": so_cho_truoc_loc,
                "candidate_count_after": so_cho_sau_loc,
                "scope_operations": PHAM_VI_PHEP,
                "elapsed_filter_mutate_s": giay_loc_va_lat,
                "elapsed_full_suite_s": 0.0,
                "analysis_on_temp_copy": True,
                "model_calls": 0,
                "external_submit": False,
                "candidates": [],
                "reason": "Lọc + lật vượt trần thời gian quy định",
                "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
            }

        # Bước 4: Chạy full suite cho các ứng viên làm test chọn xanh
        t0_suite = time.monotonic()
        candidates_out: list[dict] = []
        co_ban_va_xanh_suite = False

        for cand in xanh_selected:
            target_file.write_text(cand["ma"], encoding="utf-8")
            full_suite_status = "ĐỎ"
            so_test_hong = 0
            ly_do_khong_do = ""
            con_lai_tong = deadline_tong - time.monotonic()
            if con_lai_tong > 0:
                try:
                    r_suite = subprocess.run(
                        [
                            PY, "-X", "utf8", "-m", "pytest", "tests",
                            "-m", "not e1_control",
                            "-q", "--no-header", "-p", "no:cacheprovider",
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        cwd=str(tam),
                        timeout=max(1.0, min(120.0, con_lai_tong)),
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
                    ly_do_khong_do = "Quá giờ suite"
                    so_test_hong = 0
                except Exception as exc:
                    full_suite_status = "suite_khong_do_duoc"
                    ly_do_khong_do = f"Ngoại lệ: {exc}"
                    so_test_hong = 0
            else:
                full_suite_status = "suite_khong_do_duoc"
                ly_do_khong_do = "Hết thời gian tổng"
                so_test_hong = 0

            cand_entry = {
                "index": cand["index"],
                "line": cand["line"],
                "operation": cand["operation"],
                "unified_diff": cand["unified_diff"],
                # 24/08: xem ghi chu cung ten o tools/_worker_e1_exec.py
                "diff_basis": "van_ban_goc_temp_copy",
                "selected_test_status": "XANH",
                "full_suite_status": full_suite_status,
                "so_test_hong": so_test_hong if full_suite_status == "ĐỎ" else 0,
                "ma": cand["ma"],
            }
            if ly_do_khong_do:
                cand_entry["ly_do_suite"] = ly_do_khong_do
            candidates_out.append(cand_entry)

        giay_suite = round(time.monotonic() - t0_suite, 1)

        # Trạng thái nghiệp vụ
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
            "selected_test": test_do_duoc_chon,
            "other_red_test_count": so_test_do_khac,
            "executed_lines": sorted(dong_da_chay),
            "candidate_count_before": so_cho_truoc_loc,
            "candidate_count_after": so_cho_sau_loc,
            "scope_operations": PHAM_VI_PHEP,
            "elapsed_filter_mutate_s": giay_loc_va_lat,
            "elapsed_full_suite_s": giay_suite,
            "analysis_on_temp_copy": True,
            "model_calls": 0,
            "external_submit": False,
            "candidates": candidates_out,
            "reason": reason,
            "limitation": doc_thong_tin_gioi_han(project_root),
        }

    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)
