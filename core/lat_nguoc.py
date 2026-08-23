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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.trace_runtime import chot_test_can_trace, chay_trace_mot_test, TraceResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable or str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe")


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
    """Lật ĐÚNG MỘT chỗ, chỉ số `muc`. Đếm theo cùng thứ tự với phép duyệt AST."""

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
            if self._lay("so sánh %s" % type(n.ops[0]).__name__, n):
                n.ops = [NGHICH_SS[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay("logic %s" % type(n.op).__name__, n):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay("bool %s" % n.value, n):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            if self._lay("số %d" % n.value, n):
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
    moi = ast.unparse(ast.fix_missing_locations(bd.visit(ast.parse(nguon))))
    return moi, bd.da


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


def _tao_unified_diff(goc_ast_str: str, moi_ast_str: str, filename: str) -> str:
    """Tạo unified diff giữa hai bản AST chuẩn hóa."""
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
    """Chọn test đỏ theo thứ tự 3 tầng và trả về kết quả trace từ trace_runtime."""
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {
            "trang_thai": "khong_chay",
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
        chuan_ast = ast.unparse(ast.parse(nguon_text))
        cac_cho = _liet_ke_cho(nguon_text)
        so_cho_truoc_loc = len(cac_cho)

        # Bước 1: Trace dòng & chọn test đỏ
        t0_loc = time.monotonic()
        deadline_loc_lat = min(deadline_tong, t0_loc + filter_mutate_timeout_s)
        trace = _chon_test_va_dong(tam, tep_nguon_rel, tep_test_rel, deadline=deadline_loc_lat)

        if trace.get("trang_thai") != "trace_du":
            giay_loc = round(time.monotonic() - t0_loc, 1)
            vi_sao = trace.get("vi_sao", "Không thu thập được vết dòng đầy đủ")
            trang_thai_ra = "khong_tim_thay" if "không có test nào bị đỏ" in vi_sao else "khong_do_duoc"
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
                    diff = _tao_unified_diff(chuan_ast, ast.unparse(ast.parse(moi_text)), tep_nguon_rel)
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
            suite_pass = False
            so_test_hong = 0
            con_lai_tong = deadline_tong - time.monotonic()
            if con_lai_tong > 0:
                try:
                    r_suite = subprocess.run(
                        [
                            PY, "-X", "utf8", "-m", "pytest", "tests",
                            "-q", "--no-header", "-p", "no:cacheprovider",
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        cwd=str(tam),
                        timeout=max(1.0, min(120.0, con_lai_tong)),
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
                            so_test_hong = max(1, out_text.count("FAILED"))
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

        giay_suite = round(time.monotonic() - t0_suite, 1)

        # Trạng thái nghiệp vụ
        if co_ban_va_xanh_suite:
            trang_thai = "tim_thay"
            reason = f"Đã tìm thấy {sum(1 for c in candidates_out if c['full_suite_status'] == 'XANH')} bản vá xanh toàn bộ suite."
        elif candidates_out:
            trang_thai = "ung_vien_khong_qua_suite"
            reason = f"Có {len(candidates_out)} ứng viên làm xanh test chọn nhưng không vượt qua toàn bộ test suite."
        else:
            trang_thai = "khong_tim_thay"
            reason = "Không tìm thấy phép lật nào làm xanh test chọn trong phạm vi 5 họ phép E1."

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
