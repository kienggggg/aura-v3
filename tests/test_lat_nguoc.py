# -*- coding: utf-8 -*-
"""test_lat_nguoc.py — kiểm thử `core/lat_nguoc.py` (Worker E1).

VÌ SAO TỆP NÀY SINH RA, 25/08/2026:

`core/lat_nguoc.py` dài 547 dòng và có **0 test**. Nó là bộ máy E1 — thứ
`tools/_worker_e1_exec.py` nhập 5 tên vào dùng. Không có test nghĩa là:

1. Đổi nó không ai biết hỏng.
2. Nó KHÔNG dùng làm tệp bộ đề được. Bộ sinh đề gieo lỗi rồi hỏi "test nào
   đỏ"; tệp không có test thì mọi đề đều `khong_do_duoc`. Sau năm bộ đề, kho
   đã hết tệp độc lập — `lat_nguoc` là tệp lớn duy nhất còn lại (547 dòng),
   nên viết test cho nó vừa là việc đúng, vừa mở đường cho bộ đề thứ sáu.

TỆP NÀY CHỨA CẢ HAI TẦNG:
1. TẦNG THUẦN (NEO 1–6): 21 test neo nền do Codex / Tech Lead viết.
2. TẦNG TÍCH HỢP (NEO 7–13): kiểm thử _chon_test_va_dong, chay_e1_dinh_vi,
   các nhánh lỗi, 5 lời hứa an toàn và fail-closed do Antigravity viết.

RANH GIỚI CHIA VIỆC — theo chỗ mã thật sự gãy làm hai, không chia theo số dòng:

    TẦNG THUẦN     không đụng đĩa, không gọi tiến trình con, tất định,
                   mỗi test dưới 10ms. `lat_tren_van_ban`, `_Lat`,
                   `_liet_ke_cho`, `_ma_sau_lat`, `tao_cac_ung_vien`,
                   `_tao_unified_diff`, `doc_thong_tin_gioi_han`.

    TẦNG TÍCH HỢP  chép kho vào thư mục tạm rồi chạy `pytest` bằng tiến
                   trình con. `_chon_test_va_dong`, `chay_e1_dinh_vi`.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import core.lat_nguoc as lat_nguoc_module
from core.lat_nguoc import (
    NGHICH_SS,
    OP_STR,
    PHAM_VI_PHEP,
    _Lat,
    _chon_test_va_dong,
    _liet_ke_cho,
    _ma_sau_lat,
    _tao_unified_diff,
    chay_e1_dinh_vi,
    doc_thong_tin_gioi_han,
    lat_tren_van_ban,
    tao_cac_ung_vien,
)
from core.trace_runtime import TraceResult


def _lat_het(ma: str):
    """Lật lần lượt MỌI chỗ trong `ma`. Trả [(mô tả, mã mới)]."""
    return [(mo_ta, _ma_sau_lat(ma, chi_so)[0])
            for chi_so, _dong, mo_ta in _liet_ke_cho(ma)]


# ==============================================================================
# NEO 1 — năm họ phép, mỗi họ đúng một ca
# ==============================================================================

@pytest.mark.parametrize("ma, mong_doi", [
    ("a < b\n", "a <= b\n"),
    ("x = a and b\n", "x = a or b\n"),
    ("y = not z\n", "y =  z\n"),
    ("c = True\n", "c = False\n"),
    ("n = 5\n", "n = 4\n"),
])
def test_nam_ho_phep_lat_dung_mot_token(ma, mong_doi):
    """`PHAM_VI_PHEP` khai báo 5 họ; mỗi họ phải lật được và chỉ đổi 1 token."""
    cac = _lat_het(ma)
    assert len(cac) == 1, cac
    assert cac[0][1] == mong_doi


def test_pham_vi_phep_dung_nam_ho():
    assert PHAM_VI_PHEP == [
        "so_sanh", "logic", "bo_phu_dinh", "bool_constant", "int_constant"]


def test_bang_nghich_va_bang_chu_phu_nhau():
    """Mọi phép trong `NGHICH_SS` phải có ký hiệu trong `OP_STR`.

    Thiếu một cặp thì `visit_Compare` ném KeyError giữa lúc lật — và nó ném
    ở tận trong `_Lat`, nơi lỗi khó lần ngược về đây.
    """
    for cu, moi in NGHICH_SS.items():
        assert cu in OP_STR, cu
        assert moi in OP_STR, moi


# ==============================================================================
# NEO 2 — TOÁN TỬ NẰM TRONG CHUỖI KHÔNG ĐƯỢC ĐỤNG TỚI
# ==============================================================================
#
# Đây là lý do `lat_tren_van_ban` đi qua `tokenize` chứ không `str.replace`.
# Dò chuỗi con thì `s = "a < b"` bị lật luôn dấu `<` bên trong chuỗi — mã vẫn
# chạy, kết quả vẫn sai, và không ai thấy. Đúng họ bệnh §4 của CLAUDE.md.

@pytest.mark.parametrize("ma, phai_con_nguyen", [
    ('s = "a < b"\nif s < t:\n    pass\n', '"a < b"'),
    ('if "x and y" and z:\n    pass\n', '"x and y"'),
    ('x = "True" == True\n', '"True"'),
])
def test_toan_tu_trong_chuoi_khong_bi_lat(ma, phai_con_nguyen):
    for mo_ta, moi in _lat_het(ma):
        assert phai_con_nguyen in moi, (mo_ta, moi)
        ast.parse(moi)


def test_moi_ban_lat_van_la_python_hop_le():
    """Bản lật hỏng cú pháp thì E1 không đo được gì — phải luôn parse được."""
    ma = (
        'def f(a, b, co=True):\n'
        '    if a < b and not co:\n'
        '        return a[1]\n'
        '    return b\n'
    )
    cac = _lat_het(ma)
    assert len(cac) >= 5, cac
    for mo_ta, moi in cac:
        ast.parse(moi)      # nổ ở đây nghĩa là bản lật hỏng cú pháp


# ==============================================================================
# NEO 3 — thứ tự hậu duyệt, và chỉ số ngoài tầm
# ==============================================================================

def test_thu_tu_la_hau_duyet_con_truoc_cha():
    """`_liet_ke_cho` phải liệt kê theo hậu duyệt: nút con trước nút cha.

    `tao_cac_ung_vien` và `_ma_sau_lat` đếm ĐỘC LẬP trên hai cây AST khác
    nhau; hai bên chỉ khớp khi thứ tự đếm giống hệt. Đổi thứ tự duyệt là làm
    lệch chỉ số giữa hai bên, mà lệch chỉ số thì E1 báo "lật chỗ X" rồi sinh
    ra bản vá của chỗ Y.
    """
    cho = _liet_ke_cho('if a < b and not c:\n    pass\n')
    assert [ten for _i, _d, ten in cho] == [
        "so sánh Lt -> LtE", "bỏ phủ định", "logic And -> Or"]

    # `not not z`: `not` TRONG được đánh số trước `not` NGOÀI
    trong, ngoai = _ma_sau_lat('y = not not z\n', 0)[0], _ma_sau_lat('y = not not z\n', 1)[0]
    assert trong == 'y = not  z\n'
    assert ngoai == 'y =  not z\n'


def test_chi_so_ngoai_tam_tra_ve_nguyen_ban():
    """Không có chỗ nào mang chỉ số ấy thì trả nguyên bản và mô tả rỗng."""
    goc = 'a < b\n'
    moi, mo_ta = _ma_sau_lat(goc, 99)
    assert moi == goc
    assert mo_ta == ""


# ==============================================================================
# NEO 4 — những cấu trúc PHẢI bị bỏ qua
# ==============================================================================

@pytest.mark.parametrize("ma", [
    'if a < b < c:\n    pass\n',       # so sánh dây: len(ops) != 1
    'if a is not b:\n    pass\n',      # IsNot không có trong NGHICH_SS
    'if a in b:\n    pass\n',          # In không có trong NGHICH_SS
    's = "chuoi thuan"\n',             # Constant chuỗi: không lật
])
def test_cau_truc_ngoai_nam_ho_thi_khong_sinh_ung_vien(ma):
    assert _liet_ke_cho(ma) == []


# ==============================================================================
# NEO 5 — lọc theo dòng đã chạy
# ==============================================================================

def test_loc_theo_dong_da_chay():
    ma = 'if a < b:\n    pass\nif c > d:\n    pass\n'
    assert [d for d, _m, _c in tao_cac_ung_vien(ma)] == [1, 3]
    assert [d for d, _m, _c in tao_cac_ung_vien(ma, {1})] == [1]
    assert tao_cac_ung_vien(ma, set()) == []


def test_khong_loc_va_loc_bang_toan_bo_dong_cho_cung_ket_qua():
    """`dong_da_chay=None` phải bằng đúng việc truyền vào mọi dòng có chỗ lật."""
    ma = 'if a < b and not c:\n    pass\nx = 5\n'
    khong_loc = tao_cac_ung_vien(ma)
    moi_dong = tao_cac_ung_vien(ma, {d for d, _m, _c in khong_loc})
    assert khong_loc == moi_dong


# ==============================================================================
# NEO 6 — diff
# ==============================================================================

def test_diff_rong_khi_hai_ban_giong_nhau():
    assert _tao_unified_diff("a\n", "a\n", "x.py") == ""


def test_diff_co_dau_cong_tru_va_ten_tep():
    d = _tao_unified_diff("a = 1\n", "a = 2\n", "core/x.py")
    assert "--- a/core/x.py" in d
    assert "+++ b/core/x.py" in d
    assert "-a = 1" in d
    assert "+a = 2" in d


# ==============================================================================
# TẦNG THUẦN — các nhánh offset và sổ chỉ số còn hở ngày 25/08/2026
# ==============================================================================

def test_py_luon_la_trinh_thong_dich_dang_chay(monkeypatch):
    """Phải nhập cô lập với đường dẫn khác fallback mới phân biệt được `or`
    và `and`; trong kho thật hai đường dẫn venv tình cờ trùng nhau.
    """
    dang_chay = r"Z:\python-dang-chay.exe"
    spec = importlib.util.spec_from_file_location(
        "_lat_nguoc_import_test", lat_nguoc_module.__file__)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    monkeypatch.setattr(sys, "executable", dang_chay)
    spec.loader.exec_module(module)

    assert module.PY == dang_chay


def test_lat_constant_o_dong_sau_dung_nhanh_thay_truc_tiep():
    """Constant đi tắt, nên offset dòng 2 phải được neo độc lập với tokenize;
    bỏ `keepends` làm điểm bắt đầu lệch đúng một byte.
    """
    ma = "dau = 0\nx = True\n"
    node = ast.parse(ma).body[1].value

    assert lat_tren_van_ban(ma, node, "True", "False") == (
        "dau = 0\nx = False\n")


@pytest.mark.parametrize("ma, mong_doi, mo_ta", [
    ("n = -1\n", "n = -0\n", "số 1 -> 0"),
    ("n = 0\n", "n = -1\n", "số 0 -> -1"),
])
def test_so_am_lat_constant_chu_khong_lat_dau(ma, mong_doi, mo_ta):
    """25/08 đã đo `-1` là UnaryOp chứa Constant 1: E1 phải giữ dấu và
    sinh `-0`, kể cả khi bản lật ấy không đổi hành vi vì `-0 == 0`.
    """
    assert _lat_het(ma) == [(mo_ta, mong_doi)]


def test_lat_token_dong_dau_cua_node_nhieu_dong():
    """Token ở hàng tương đối 1 giữ lát cắt `[:0]`; đổi mốc 1 thành 2 sẽ
    cộng nhầm gần trọn vùng nhiều dòng dù token nằm ngay hàng đầu.
    """
    ma = "if a and (\n    b\n):\n    pass\n"
    node = ast.parse(ma).body[0].test

    assert lat_tren_van_ban(ma, node, "and", "or") == (
        "if a or (\n    b\n):\n    pass\n")


def test_lat_token_o_dong_sau_trong_node_giu_byte_xuong_dong():
    """Token ở hàng tương đối 2 cần tính cả byte xuống dòng trước nó;
    `splitlines(keepends=False)` làm phép thay lệch sang trái một byte.
    """
    ma = "if (\n    a\n    and b\n):\n    pass\n"
    node = ast.parse(ma).body[0].test

    assert lat_tren_van_ban(ma, node, "and", "or") == (
        "if (\n    a\n    or b\n):\n    pass\n")


def test_lay_ghi_dung_chi_so_dong_va_ket_qua_chon():
    """Mã sinh ra vẫn hợp lệ khi sổ lệch một chỉ số, nên phải quan sát
    thẳng cả `danh_sach` lẫn ba giá trị trả về False/True/False.
    """
    bo_lat = _Lat(1)
    cac_node = [ast.Pass(), ast.Pass(lineno=0), ast.Pass(lineno=7)]

    ket_qua = [
        bo_lat._lay(ten, node)
        for ten, node in zip(("dau", "chon", "cuoi"), cac_node)
    ]

    assert ket_qua == [False, True, False]
    assert bo_lat.dem == 3
    assert bo_lat.danh_sach == [
        (0, 0, "dau"),
        (1, 0, "chon"),
        (2, 7, "cuoi"),
    ]
    assert bo_lat.da == "chon"
    assert bo_lat.target_node is cac_node[1]


@pytest.mark.parametrize("ma, ma_sau_lat, muc_so", [
    ("n = 5\n", "n = 4", (0, 1, "số 5 -> 4")),
    ("co = True\n", "co = False", (0, 1, "bool True -> False")),
])
def test_visit_constant_tra_cay_da_lat_va_phan_biet_bool_int(
        ma, ma_sau_lat, muc_so):
    """`True` cũng là `int` trong Python. Neo cây AST trả về, không chỉ văn
    bản sinh từ `sang`, để bắt trường hợp visitor trả sai hằng số.
    """
    bo_lat = _Lat(0)

    cay = bo_lat.visit(ast.parse(ma))

    assert ast.unparse(cay) == ma_sau_lat
    assert bo_lat.danh_sach == [muc_so]
    assert bo_lat.da == muc_so[2]


# ==============================================================================
# TẦNG TÍCH HỢP — KIỂM THỬ _chon_test_va_dong VÀ chay_e1_dinh_vi (25/08/2026)
# ==============================================================================

# ==============================================================================
# NEO 7 — _chon_test_va_dong: DEADLINE, FAIL-CLOSED VÀ RÀNG BUỘC NGẦM
# ==============================================================================

def test_chon_test_va_dong_qua_deadline():
    """Khi deadline đã qua hoặc con_lai <= 0, phải fail-closed ngay lập tức."""
    t_qua = time.monotonic() - 10.0
    res = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=t_qua)
    assert res["trang_thai"] == "khong_chay"
    assert res["vi_sao"] == "hết trần 60 giây trước trace"
    assert res["test"] == ""
    assert res["so_test_do_khac"] == 0
    assert res["dong_da_chay"] == []


def test_chon_test_va_dong_deadline_ngay_lap_tuc():
    """Biên con_lai <= 0: deadline bằng đúng thời điểm hiện tại (bắt lỗi so sánh < 0)."""
    t_fixed = 100.0
    with patch("time.monotonic", return_value=t_fixed):
        with patch("core.lat_nguoc.chot_test_can_trace", side_effect=AssertionError("CẤM GỌI KHI CON_LAI == 0")):
            res = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=t_fixed)
            assert res["trang_thai"] == "khong_chay"
            assert res["vi_sao"] == "hết trần 60 giây trước trace"


def test_chon_test_va_dong_deadline_con_du_thoi_gian():
    """Biên con_lai > 0: deadline còn 0.5s phải tiếp tục chạy chot_test_can_trace."""
    with patch("core.lat_nguoc.chot_test_can_trace") as mock_chot:
        mock_chot.return_value = ("", 0, [])
        res = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=time.monotonic() + 0.5)
        assert res["vi_sao"] == "không có test nào bị đỏ trong tệp test"


def test_chon_test_va_dong_khong_co_test_do():
    """Khi không có test đỏ nào trong tệp test, trả về khong_chay và so_test_do == 0."""
    with patch("core.lat_nguoc.chot_test_can_trace") as mock_chot:
        mock_chot.return_value = ("", 0, [])
        res = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=time.monotonic() + 60.0)
        assert res["trang_thai"] == "khong_chay"
        assert res["vi_sao"] == "không có test nào bị đỏ trong tệp test"
        assert res["test"] == ""
        assert res["so_test_do"] == 0
        assert res["so_test_do_khac"] == 0
        assert res["dong_da_chay"] == []


def test_chon_test_va_dong_chot_test_thieu_ten_chot_hoac_danh_sach():
    """Phòng thủ rẽ nhánh: ten_chot rỗng hoặc danh_sach rỗng."""
    with patch("core.lat_nguoc.chot_test_can_trace") as mock_chot:
        # Trường hợp 1: ten_chot rỗng nhưng danh_sach có phần tử
        mock_res = TraceResult(
            trang_thai="trace_du",
            thong_diep="ok",
            tong_buoc=1,
            ten_test="test_x",
            so_test_do_khac=0,
            dong_da_chay=[1],
        )
        mock_chot.return_value = ("", 0, [mock_res])
        res1 = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=time.monotonic() + 60.0)
        assert res1["trang_thai"] == "khong_chay"
        assert res1["so_test_do"] == 0

        # Trường hợp 2: ten_chot có tên nhưng danh_sach rỗng
        mock_chot.return_value = ("tests/test_x.py::test_1", 0, [])
        res2 = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=time.monotonic() + 60.0)
        assert res2["trang_thai"] == "khong_chay"
        assert res2["so_test_do"] == 0


def test_chon_test_va_dong_rang_buoc_ngam_chot_luon_la_danh_sach_0():
    """RÀNG BUỘC NGẦM: lat_nguoc luôn lấy danh_sach[0] làm kết quả của test được chốt.

    Đóng đinh bất biến: danh_sach[0] phải là test được chốt, so_test_do = so_khac + 1,
    và các trường trang_thai, vi_sao, dong_da_chay, so_buoc phải trích xuất đúng từ danh_sach[0].
    """
    res0 = TraceResult(
        trang_thai="trace_du",
        thong_diep="Trace thành công test 0",
        tong_buoc=7,
        ten_test="tests/test_x.py::test_uu_tien",
        so_test_do_khac=2,
        dong_da_chay=[5, 10],
    )
    res1 = TraceResult(
        trang_thai="trace_cut",
        thong_diep="Trace test 1",
        tong_buoc=5000,
        ten_test="tests/test_x.py::test_phu",
        so_test_do_khac=2,
        dong_da_chay=[99],
    )
    with patch("core.lat_nguoc.chot_test_can_trace") as mock_chot:
        mock_chot.return_value = ("tests/test_x.py::test_uu_tien", 2, [res0, res1])
        res = _chon_test_va_dong(Path("."), "core/x.py", "tests/test_x.py", deadline=time.monotonic() + 60.0)
        assert res["trang_thai"] == "trace_du"
        assert res["vi_sao"] == "Trace thành công test 0"
        assert res["test"] == "tests/test_x.py::test_uu_tien"
        assert res["so_test_do"] == 3  # 2 + 1
        assert res["so_test_do_khac"] == 2
        assert res["dong_da_chay"] == [5, 10]  # Khớp res0, không bị lẫn res1
        assert res["so_buoc"] == 7  # Khớp res0


# ==============================================================================
# NEO 8 — chay_e1_dinh_vi: XỬ LÝ ĐƯỜNG DẪN, BẢN SAO VÀ TRƯỜNG TỆP NGUỒN KHÔNG TỒN TẠI
# ==============================================================================

def test_chay_e1_dinh_vi_chuan_hoa_duong_dan_windows(tmp_path):
    """Đường dẫn dạng Windows gạch chéo ngược phải được chuẩn hóa về posix."""
    src = tmp_path / "core" / "app.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x > 0\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_app.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_dummy(): pass\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "khong_chay",
            "ma_ly_do": "khong_co_test_do",
            "vi_sao": "không có test nào bị đỏ trong tệp test",
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
        res = chay_e1_dinh_vi(
            tmp_path,
            "core\\app.py",
            "tests\\test_app.py",
            source_sha256="sha_src",
            test_sha256="sha_tst",
        )
        assert res["source_path"] == "core/app.py"
        assert res["test_file"] == "tests/test_app.py"
        assert res["source_sha256"] == "sha_src"
        assert res["test_sha256"] == "sha_tst"


def test_chay_e1_dinh_vi_thu_muc_data_da_ton_tai_khong_bi_loi(tmp_path):
    """Bản sao tạm phải mkdir(exist_ok=True) cho data/, không được ném FileExistsError."""
    src = tmp_path / "core" / "app.py"
    src.parent.mkdir(parents=True)
    src.write_text("x = 1\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_app.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_dummy(): pass\n", encoding="utf-8")
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "some_file.txt").write_text("test", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "khong_chay",
            "ma_ly_do": "khong_co_test_do",
            "vi_sao": "không có test nào bị đỏ trong tệp test",
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
        res = chay_e1_dinh_vi(tmp_path, "core/app.py", "tests/test_app.py")
        assert res["trang_thai"] == "khong_tim_thay"


def test_chay_e1_dinh_vi_tep_nguon_khong_ton_tai(tmp_path):
    """Khi tệp nguồn không có trong bản sao tạm, trả về khong_do_duoc với hợp đồng dict đầy đủ."""
    tst = tmp_path / "tests" / "test_app.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): pass\n", encoding="utf-8")

    res = chay_e1_dinh_vi(
        tmp_path,
        "core/khong_ton_tai.py",
        "tests/test_app.py",
        source_sha256="sha_src_123",
        test_sha256="sha_tst_123",
    )
    assert res["trang_thai"] == "khong_do_duoc"
    assert res["source_path"] == "core/khong_ton_tai.py"
    assert res["source_sha256"] == "sha_src_123"
    assert res["test_file"] == "tests/test_app.py"
    assert res["test_sha256"] == "sha_tst_123"
    assert res["selected_test"] == ""
    assert res["other_red_test_count"] == 0
    assert res["executed_lines"] == []
    assert res["candidate_count_before"] == 0
    assert res["candidate_count_after"] == 0
    assert res["scope_operations"] == PHAM_VI_PHEP
    assert res["elapsed_filter_mutate_s"] == 0.0
    assert res["elapsed_full_suite_s"] == 0.0
    assert res["analysis_on_temp_copy"] is True
    assert res["model_calls"] == 0
    assert res["external_submit"] is False
    assert res["candidates"] == []
    assert "Tệp nguồn không tồn tại trong bản sao: core/khong_ton_tai.py" in res["reason"]
    assert res["limitation"] == "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi."


# ==============================================================================
# NEO 9 — chay_e1_dinh_vi: PHÂN NHÁNH TRACE THẤT BẠI HOẶC KHÔNG CÓ TEST ĐỎ
# ==============================================================================

def test_chay_e1_dinh_vi_khong_co_test_do_tra_ve_khong_tim_thay(tmp_path):
    """Khi trace báo không có test nào bị đỏ, trạng thái trả ra là khong_tim_thay."""
    src = tmp_path / "core" / "logic.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(a, b):\n    if a < b:\n        return True\n    return False\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_logic.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_x(): pass\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "khong_chay",
            "ma_ly_do": "khong_co_test_do",
            "vi_sao": "không có test nào bị đỏ trong tệp test",
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
        res = chay_e1_dinh_vi(tmp_path, "core/logic.py", "tests/test_logic.py")
        assert res["trang_thai"] == "khong_tim_thay"
        assert res["reason"] == "không có test nào bị đỏ trong tệp test"
        assert res["candidate_count_before"] >= 1
        assert res["candidate_count_after"] == 0
        assert res["selected_test"] == ""
        assert res["other_red_test_count"] == 0
        assert res["executed_lines"] == []
        assert res["analysis_on_temp_copy"] is True
        assert res["model_calls"] == 0
        assert res["external_submit"] is False
        assert res["candidates"] == []
        assert res["limitation"] == "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi."


def test_chay_e1_dinh_vi_trace_khong_du_tra_ve_khong_do_duoc(tmp_path):
    """Khi trace thất bại vì lý do khác (vd: chạm trần bước), trả về khong_do_duoc."""
    src = tmp_path / "core" / "loop.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f():\n    return 1\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_loop.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_f(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_cut",
            "vi_sao": "KHÔNG ĐO ĐƯỢC: Chạm trần ở bước 5000",
            "test": "tests/test_loop.py::test_f",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
        }
        res = chay_e1_dinh_vi(tmp_path, "core/loop.py", "tests/test_loop.py")
        assert res["trang_thai"] == "khong_do_duoc"
        assert res["reason"] == "KHÔNG ĐO ĐƯỢC: Chạm trần ở bước 5000"
        assert res["candidates"] == []


# ==============================================================================
# NEO 10 — chay_e1_dinh_vi: QUÁ GIỜ LỌC VÀ LẬT (FILTER/MUTATE TIMEOUT)
# ==============================================================================

def test_chay_e1_dinh_vi_qua_gio_loc_va_lat(tmp_path):
    """Khi quá giờ lọc và lật mà chưa có ứng viên làm xanh test chọn, trả về khong_do_duoc."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 2,
            "so_test_do_khac": 1,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        # filter_mutate_timeout_s = 0 ép hết giờ ngay khi vào vòng lặp lật
        res = chay_e1_dinh_vi(
            tmp_path,
            "core/calc.py",
            "tests/test_calc.py",
            filter_mutate_timeout_s=-1.0,
        )
        assert res["trang_thai"] == "khong_do_duoc"
        assert res["reason"] == "Lọc + lật vượt trần thời gian quy định"
        assert res["selected_test"] == "tests/test_calc.py::test_1"
        assert res["other_red_test_count"] == 1
        assert res["executed_lines"] == [2]
        assert res["candidate_count_before"] >= 1
        assert res["candidate_count_after"] >= 1
        assert res["candidates"] == []
        assert res["analysis_on_temp_copy"] is True
        assert res["model_calls"] == 0
        assert res["external_submit"] is False


def test_chay_e1_dinh_vi_loc_va_lat_con_du_thoi_gian_bien(tmp_path):
    """Biên con_lai = 0.5s: phải không bị xem là qua_gio (bắt lỗi con_lai <= 1)."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            # Cung cấp đủ 0.5 giây trong vòng lặp lật
            t_now = 100.0
            with patch("time.monotonic", side_effect=lambda: t_now):
                res = chay_e1_dinh_vi(
                    tmp_path,
                    "core/calc.py",
                    "tests/test_calc.py",
                    timeout_s=100.0,
                    filter_mutate_timeout_s=0.5,
                )
                assert res["trang_thai"] == "tim_thay"


def test_chay_e1_dinh_vi_loc_va_lat_con_lai_bang_0(tmp_path):
    """Khi con_lai == 0.0 trong vòng lặp lật, phải dừng lặp và coi là quá giờ (bắt lỗi con_lai < 0)."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "trace_du", "vi_sao": "ok", "test": "tests/test_calc.py::test_1", "dong_da_chay": [2]}):
        with patch("subprocess.run", side_effect=AssertionError("CẤM CHẠY KHI CON_LAI == 0")):
            t_fixed = 100.0
            with patch("time.monotonic", return_value=t_fixed):
                res = chay_e1_dinh_vi(
                    tmp_path,
                    "core/calc.py",
                    "tests/test_calc.py",
                    timeout_s=100.0,
                    filter_mutate_timeout_s=0.0,
                )
                assert res["trang_thai"] == "khong_do_duoc"
                assert res["reason"] == "Lọc + lật vượt trần thời gian quy định"


def test_chay_e1_dinh_vi_lam_tron_thoi_gian_chinh_xac_1_chu_so(tmp_path):
    """Khẳng định thời gian elapsed_* phải được làm tròn đúng 1 chữ số thập phân (round(..., 1))."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    def make_timer():
        cur = 100.0
        def _get():
            nonlocal cur
            val = cur
            cur += 0.12345
            return val
        return _get

    # Ca 1: Trace thất bại -> elapsed_filter_mutate_s ở line 329
    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "khong_chay", "vi_sao": "ko co test do"}):
        with patch("time.monotonic", side_effect=make_timer()):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["elapsed_filter_mutate_s"] == 0.1

    # Ca 2: Tìm thấy ứng viên -> elapsed_filter_mutate_s ở line 536 và elapsed_full_suite_s ở line 537
    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "trace_du", "vi_sao": "ok", "test": "t1", "dong_da_chay": [2]}):
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            with patch("time.monotonic", side_effect=make_timer()):
                res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
                # elapsed_* luôn làm tròn 1 chữ số thập phân
                assert res["elapsed_filter_mutate_s"] == round(res["elapsed_filter_mutate_s"], 1)
                assert str(res["elapsed_filter_mutate_s"]).split(".")[1].__len__() <= 1
                assert str(res["elapsed_full_suite_s"]).split(".")[1].__len__() <= 1


def test_chay_e1_dinh_vi_qua_gio_do_subprocess_timeout(tmp_path):
    """Khi chạy test ứng viên bị subprocess.TimeoutExpired, ghi nhận qua_gio."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=15)):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "khong_do_duoc"
            assert res["reason"] == "Lọc + lật vượt trần thời gian quy định"


def test_chay_e1_dinh_vi_bo_qua_ung_vien_loi_lat_hoac_khong_doi(tmp_path):
    """Bỏ qua ứng viên khi _ma_sau_lat ném ngoại lệ hoặc mã mới trùng mã cũ."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        with patch("core.lat_nguoc._ma_sau_lat", side_effect=RuntimeError("Lỗi lật thử nghiệm")):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "khong_tim_thay"
            assert res["candidates"] == []


def test_chay_e1_dinh_vi_mac_dinh_so_test_do_khac_la_0(tmp_path):
    """Khi trace không có khoá so_test_do_khac, mặc định là 0."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "dong_da_chay": [2],
        }
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["other_red_test_count"] == 0


# ==============================================================================
# NEO 11 — chay_e1_dinh_vi: BỐN TRẠNG THÁI NGHIỆP VỤ KHI THỬ ỨNG VIÊN
# ==============================================================================

def test_chay_e1_dinh_vi_khong_co_ung_vien_nao_lam_xanh_test_chon(tmp_path):
    """Không có phép lật nào làm xanh test chọn -> trạng thái khong_tim_thay."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        # Mọi phép lật đều khiến pytest trả returncode = 1 (vẫn đỏ)
        mock_proc = MagicMock(returncode=1, stdout="1 failed", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "khong_tim_thay"
            assert res["reason"] == "Không có ứng viên nào trong phạm vi 5 phép làm xanh test chọn."
            assert res["candidates"] == []


def test_chay_e1_dinh_vi_tim_thay_ban_va_xanh_toan_bo_suite(tmp_path):
    """Ứng viên làm xanh test chọn VÀ xanh toàn bộ test suite -> trạng thái tim_thay."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        # Cả test đơn và full suite đều trả returncode = 0
        mock_proc = MagicMock(returncode=0, stdout="1 passed\n", stderr="")
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            # Lấy đúng 1 ứng viên để kiểm tra chính xác câu chữ '1 bản vá'
            def fake_lat(ma, chi_so):
                if chi_so == 1:
                    return "def f(x):\n    return x <= 5\n", "so sánh Lt -> LtE"
                return ma, ""

            with patch("core.lat_nguoc._ma_sau_lat", side_effect=fake_lat):
                res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
                assert res["trang_thai"] == "tim_thay"
                assert res["reason"] == "Đã tìm thấy 1 bản vá xanh toàn bộ suite."
                assert len(res["candidates"]) == 1
                cand = res["candidates"][0]
                assert cand["selected_test_status"] == "XANH"
                assert cand["full_suite_status"] == "XANH"
                assert cand["so_test_hong"] == 0
                assert cand["diff_basis"] == "van_ban_goc_temp_copy"
                assert "--- a/core/calc.py" in cand["unified_diff"]
                assert "+    return x <= 5" in cand["unified_diff"]

                # Khẳng định cờ subprocess.run
                for call in mock_run.call_args_list:
                    assert call.kwargs.get("capture_output") is True
                    assert call.kwargs.get("text") is True

                assert res["analysis_on_temp_copy"] is True
                assert res["model_calls"] == 0
                assert res["external_submit"] is False


def test_chay_e1_dinh_vi_ung_vien_khong_qua_suite_regex_failed(tmp_path):
    """Ứng viên làm xanh test chọn nhưng full suite đỏ (bắt số test hỏng qua regex 'N failed')."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:  # Full suite call
                return MagicMock(returncode=1, stdout="======= 2 failed, 10 passed =======", stderr="")
            # Test đơn lẻ được chọn
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "ung_vien_khong_qua_suite"
            assert "không vượt qua toàn bộ test suite" in res["reason"]
            assert len(res["candidates"]) >= 1
            cand = res["candidates"][0]
            assert cand["selected_test_status"] == "XANH"
            assert cand["full_suite_status"] == "ĐỎ"
            assert cand["so_test_hong"] == 2
            assert res["analysis_on_temp_copy"] is True
            assert res["model_calls"] == 0
            assert res["external_submit"] is False


def test_chay_e1_dinh_vi_ung_vien_khong_qua_suite_fallback_count_failed(tmp_path):
    """Ứng viên làm xanh test chọn nhưng full suite đỏ (bắt số test hỏng qua đếm chữ FAILED đơn lẻ)."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:  # Đúng 1 dòng FAILED, không có dòng tổng hợp "failed"
                return MagicMock(returncode=1, stdout="FAILED test_calc.py::test_2\n", stderr="")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "ung_vien_khong_qua_suite"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "ĐỎ"
            assert cand["so_test_hong"] == 1


def test_chay_e1_dinh_vi_suite_loi_collection(tmp_path):
    """Khi suite bị lỗi ERROR collecting tests trong stderr -> suite_khong_do_duoc."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                # stderr chứa chuỗi lỗi
                return MagicMock(returncode=2, stdout="", stderr="ERROR collecting tests/test_x.py\nImportError")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            assert "suite không đo được" in res["reason"]
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert cand["ly_do_suite"] == "Lỗi thu thập test suite"
            assert cand["so_test_hong"] == 0


def test_chay_e1_dinh_vi_suite_timeout(tmp_path):
    """Khi suite bị TimeoutExpired -> suite_khong_do_duoc kèm lý do 'Quá giờ suite'."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                raise subprocess.TimeoutExpired(cmd="pytest", timeout=120)
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert cand["ly_do_suite"] == "Quá giờ suite"
            assert cand["so_test_hong"] == 0


def test_chay_e1_dinh_vi_suite_ngoai_le_he_thong(tmp_path):
    """Khi chạy suite gặp ngoại lệ Exception -> suite_khong_do_duoc kèm Ngoại lệ."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                raise OSError("Lỗi I/O tiến trình")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert "Ngoại lệ: Lỗi I/O tiến trình" in cand["ly_do_suite"]
            assert cand["so_test_hong"] == 0


def test_chay_e1_dinh_vi_suite_khong_parse_duoc_ket_qua(tmp_path):
    """Khi returncode != 0 và out_text có chữ failed nhưng là '0 failed' -> Không đo được kết quả suite."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }

        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                return MagicMock(returncode=1, stdout="0 failed, 5 passed", stderr="")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert cand["ly_do_suite"] == "Không đo được kết quả suite"
            assert cand["so_test_hong"] == 0


def test_chay_e1_dinh_vi_suite_het_thoi_gian_tong(tmp_path):
    """Khi deadline_tong hết trước khi chạy suite -> Hết thời gian tổng."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        current_t = 100.0

        def fake_time():
            nonlocal current_t
            return current_t

        def fake_run(*args, **kwargs):
            nonlocal current_t
            # Khi subprocess.run ở step 3 chạy xong, nâng giờ lên để step 4 thấy deadline_tong đã quá hạn
            current_t = 200.0
            return mock_proc

        with patch("time.monotonic", side_effect=fake_time):
            with patch("subprocess.run", side_effect=fake_run):
                res = chay_e1_dinh_vi(
                    tmp_path,
                    "core/calc.py",
                    "tests/test_calc.py",
                    timeout_s=50.0,
                    filter_mutate_timeout_s=60.0,
                )
                assert res["trang_thai"] == "suite_khong_do_duoc"
                cand = res["candidates"][0]
                assert cand["full_suite_status"] == "suite_khong_do_duoc"
                assert cand["ly_do_suite"] == "Hết thời gian tổng"
                assert cand["so_test_hong"] == 0


def test_chay_e1_dinh_vi_suite_con_lai_tong_bien(tmp_path):
    """Biên con_lai_tong: 0.5s vẫn đủ chạy suite; 0.0s bị chặn hết thời gian tổng."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        # Ca 1: con_lai_tong = 0.5s -> tiếp tục chạy suite (bắt lỗi con_lai_tong > 1)
        current_t = 100.0
        with patch("time.monotonic", side_effect=lambda: current_t):
            with patch("subprocess.run", return_value=mock_proc):
                res = chay_e1_dinh_vi(
                    tmp_path,
                    "core/calc.py",
                    "tests/test_calc.py",
                    timeout_s=0.5,
                    filter_mutate_timeout_s=0.5,
                )
                assert res["trang_thai"] == "tim_thay"


def test_chay_e1_dinh_vi_suite_con_lai_tong_bang_0(tmp_path):
    """Khi con_lai_tong == 0.0 ở bước full suite, phải không chạy subprocess (bắt lỗi >= 0)."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "trace_du", "vi_sao": "ok", "test": "t1", "dong_da_chay": [2]}):
        mock_proc = MagicMock(returncode=0, stdout="1 passed", stderr="")
        current_t = 100.0

        def fake_time():
            nonlocal current_t
            return current_t

        def fake_run(cmd, *args, **kwargs):
            nonlocal current_t
            if "tests" in cmd:
                raise AssertionError("CẤM GỌI FULL SUITE KHI CON_LAI_TONG == 0")
            current_t = 150.0  # Nâng giờ lên đúng bằng deadline_tong (100 + 50)
            return mock_proc

        with patch("time.monotonic", side_effect=fake_time):
            with patch("subprocess.run", side_effect=fake_run):
                res = chay_e1_dinh_vi(
                    tmp_path,
                    "core/calc.py",
                    "tests/test_calc.py",
                    timeout_s=50.0,
                    filter_mutate_timeout_s=60.0,
                )
                assert res["trang_thai"] == "suite_khong_do_duoc"
                cand = res["candidates"][0]
                assert cand["ly_do_suite"] == "Hết thời gian tổng"


def test_chay_e1_dinh_vi_suite_loi_collection_qua_stderr(tmp_path):
    """Khi returncode == 1 và lỗi ERROR collecting nằm trong stderr (bắt lỗi logic Or r_suite.stderr and '')."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "trace_du", "vi_sao": "ok", "test": "t1", "dong_da_chay": [2]}):
        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                # returncode = 1 (không nằm ngoài (0, 1)), stdout rỗng, stderr chứa chuỗi lỗi
                return MagicMock(returncode=1, stdout="", stderr="ERROR collecting tests/test_foo.py\nImportError")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert cand["ly_do_suite"] == "Lỗi thu thập test suite"


def test_chay_e1_dinh_vi_suite_khong_co_chu_failed_thi_khong_do_duoc(tmp_path):
    """Khi returncode == 1 nhưng stdout không có chữ failed hay FAILED -> Không đo được kết quả suite (bắt lỗi count_f >= 0)."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x):\n    return x < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong", return_value={"trang_thai": "trace_du", "vi_sao": "ok", "test": "t1", "dong_da_chay": [2]}):
        def fake_run(cmd, *args, **kwargs):
            if "tests" in cmd:
                return MagicMock(returncode=1, stdout="Chương trình ngắt đột ngột", stderr="")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "suite_khong_do_duoc"
            cand = res["candidates"][0]
            assert cand["full_suite_status"] == "suite_khong_do_duoc"
            assert cand["ly_do_suite"] == "Không đo được kết quả suite"


def test_chay_e1_dinh_vi_vua_co_xanh_vua_co_suite_khong_do_duoc_thi_uu_tien_tim_thay(tmp_path):
    """Khi có 1 ứng viên XANH và 1 ứng viên suite_khong_do_duoc -> trạng thái là tim_thay."""
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(x, y):\n    if x < 5:\n        return y > 0\n    return False\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2, 3],
            "so_buoc": 3,
        }

        dem_suite = 0

        def fake_run(cmd, *args, **kwargs):
            nonlocal dem_suite
            if "tests" in cmd:
                dem_suite += 1
                if dem_suite == 1:
                    return MagicMock(returncode=0, stdout="1 passed", stderr="")
                return MagicMock(returncode=2, stdout="ERROR collecting tests", stderr="")
            return MagicMock(returncode=0, stdout="1 passed", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")
            assert res["trang_thai"] == "tim_thay"
            assert "bản vá xanh toàn bộ suite" in res["reason"]


# ==============================================================================
# NEO 12 — NĂM LỜI HỨA AN TOÀN VÀ FAIL-CLOSED (KIỂM BẰNG CÁCH CHẠY THẬT)
# ==============================================================================

def test_loi_hua_1_va_2_va_3_khong_doi_byte_tep_that_khong_goi_model(tmp_path):
    """LỜI HỨA 1, 2, 3:
    1. Chạy hoàn toàn trên bản sao tạm (SHA256 của tệp nguồn thật không đổi).
    2. Không ghi đè byte nào trên tệp test thật (SHA256 tệp test thật không đổi).
    3. Không gọi model (model_calls == 0), không kết nối mạng (external_submit is False).
    """
    src = tmp_path / "core" / "toan.py"
    src.parent.mkdir(parents=True)
    src_content = "def kiem_tra(a, b):\n    return a == b\n"
    src.write_text(src_content, encoding="utf-8")

    tst = tmp_path / "tests" / "test_toan.py"
    tst.parent.mkdir(parents=True)
    tst_content = "from core.toan import kiem_tra\ndef test_kt():\n    assert kiem_tra(1, 2) is False\n"
    tst.write_text(tst_content, encoding="utf-8")

    sha_src_truoc = hashlib.sha256(src.read_bytes()).hexdigest()
    sha_tst_truoc = hashlib.sha256(tst.read_bytes()).hexdigest()

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "khong_chay",
            "ma_ly_do": "khong_co_test_do",
            "vi_sao": "không có test nào bị đỏ trong tệp test",
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
        res = chay_e1_dinh_vi(
            tmp_path,
            "core/toan.py",
            "tests/test_toan.py",
            source_sha256=sha_src_truoc,
            test_sha256=sha_tst_truoc,
        )

    sha_src_sau = hashlib.sha256(src.read_bytes()).hexdigest()
    sha_tst_sau = hashlib.sha256(tst.read_bytes()).hexdigest()

    # Bằng chứng SHA-256 thật từ đĩa
    assert sha_src_sau == sha_src_truoc
    assert sha_tst_sau == sha_tst_truoc
    assert src.read_text(encoding="utf-8") == src_content
    assert tst.read_text(encoding="utf-8") == tst_content

    # Bằng chứng khoá an toàn
    assert res["analysis_on_temp_copy"] is True
    assert res["model_calls"] == 0
    assert res["external_submit"] is False


def test_loi_hua_4_fail_closed_xoa_sach_thu_muc_tam_ke_ca_khi_nem_loi(tmp_path):
    """LỜI HỨA 4: Fail-closed: xoá sạch thư mục tạm hệ thống, kể cả khi hàm ném ngoại lệ."""
    src = tmp_path / "core" / "sample.py"
    src.parent.mkdir(parents=True)
    src.write_text("x = 1\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_sample.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_s(): pass\n", encoding="utf-8")

    temp_root = Path(tempfile.gettempdir())

    def _dem_aura_temp():
        try:
            return sum(1 for p in temp_root.iterdir() if p.is_dir() and p.name.startswith("aura_e1_"))
        except Exception:
            return 0

    so_truoc = _dem_aura_temp()

    # Chạy bình thường và khẳng định shutil.rmtree được gọi với ignore_errors=True
    with patch("shutil.rmtree", wraps=shutil.rmtree) as mock_rm:
        with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
            mock_trace.return_value = {
                "trang_thai": "khong_chay",
                "ma_ly_do": "khong_co_test_do",
                "vi_sao": "không có test nào bị đỏ trong tệp test",
                "test": "",
                "so_test_do": 0,
                "so_test_do_khac": 0,
                "dong_da_chay": [],
            }
            chay_e1_dinh_vi(tmp_path, "core/sample.py", "tests/test_sample.py")
        so_sau_bt = _dem_aura_temp()
        assert so_sau_bt <= so_truoc
        assert any(call.kwargs.get("ignore_errors") is True for call in mock_rm.call_args_list)

    # Chạy khi có lỗi bất ngờ ném ra giữa chừng
    with patch("core.lat_nguoc._liet_ke_cho", side_effect=RuntimeError("Cố ý ném lỗi để kiểm tra finally cleanup")):
        with pytest.raises(RuntimeError):
            chay_e1_dinh_vi(tmp_path, "core/sample.py", "tests/test_sample.py")

    so_sau_loi = _dem_aura_temp()
    assert so_sau_loi <= so_truoc


def test_loi_hua_5_tuyet_doi_khong_goi_dot_bien(tmp_path):
    """LỜI HỨA 5: Tuyệt đối không gọi dot_bien(), không gieo lỗi vào mã, không biết đáp án trước.

    Chặn bằng cách monkeypatch dot_bien ném lỗi AssertionError; chay_e1_dinh_vi phải chạy trót lọt.
    """
    src = tmp_path / "core" / "sample.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(a, b):\n    return a < b\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_sample.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_f(): pass\n", encoding="utf-8")

    def fake_dot_bien(*args, **kwargs):
        raise AssertionError("CẤM GỌI dot_bien TRONG QUY TRÌNH CHỈ-PHÂN-TÍCH E1!")

    with patch("experiments.evidence_sprint.dung_de_loi.dot_bien", side_effect=fake_dot_bien):
        with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
            mock_trace.return_value = {
                "trang_thai": "khong_chay",
                "ma_ly_do": "khong_co_test_do",
                "vi_sao": "không có test nào bị đỏ trong tệp test",
                "test": "",
                "so_test_do": 0,
                "so_test_do_khac": 0,
                "dong_da_chay": [],
            }
            res = chay_e1_dinh_vi(tmp_path, "core/sample.py", "tests/test_sample.py")
            assert res["trang_thai"] == "khong_tim_thay"


# ==============================================================================
# NEO 13 — doc_thong_tin_gioi_han
# ==============================================================================

def test_doc_thong_tin_gioi_han_khi_khong_co_tep_hoac_loi_json(tmp_path):
    """Không có tệp bằng chứng e1_ngoai_ho.json hoặc JSON hỏng -> trả về thông điệp mặc định."""
    msg1 = doc_thong_tin_gioi_han(tmp_path)
    assert msg1 == "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi."

    rac_file = tmp_path / "data" / "evidence_sprint" / "e1_ngoai_ho.json"
    rac_file.parent.mkdir(parents=True, exist_ok=True)
    rac_file.write_text("JSON HỎNG KHÔNG PARSE ĐƯỢC", encoding="utf-8")
    msg2 = doc_thong_tin_gioi_han(tmp_path)
    assert msg2 == "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi."


def test_doc_thong_tin_gioi_han_khi_co_tep_0_ca_tim_ra(tmp_path):
    """Tệp e1_ngoai_ho.json có số liệu nhưng tim_ra == 0."""
    f = tmp_path / "data" / "evidence_sprint" / "e1_ngoai_ho.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"ket_qua": [{"tim_thay": False}, {"tim_thay": False}]}), encoding="utf-8")
    msg = doc_thong_tin_gioi_han(tmp_path)
    assert msg == "Chỉ dò được 5 họ lỗi so sánh/logic. Đã thử 2 lỗi NGOÀI 5 họ đó — không dò ra ca nào."


def test_doc_thong_tin_gioi_han_khi_co_tep_co_ca_tim_ra(tmp_path):
    """Tệp e1_ngoai_ho.json có số liệu và tim_ra > 0."""
    f = tmp_path / "data" / "evidence_sprint" / "e1_ngoai_ho.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"ket_qua": [{"tim_thay": True}, {"tim_thay": False}, {"tim_thay": True}]}), encoding="utf-8")
    msg = doc_thong_tin_gioi_han(tmp_path)
    assert msg == "Chỉ dò được 5 họ lỗi so sánh/logic. Đã thử 3 lỗi NGOÀI 5 họ đó (tìm ra 2 ca)."


# ==============================================================================
# NEO 14 — hai chỗ Claude vá ngày 25/08 sau khi kiểm chứng bài nộp
# ==============================================================================

def test_khong_quyet_dinh_trang_thai_bang_DO_CHUOI_CON(tmp_path):
    """`khong_tim_thay` / `khong_do_duoc` phải quyết bằng MÃ, không bằng câu chữ.

    VÌ SAO CÓ TEST NÀY: `core/lat_nguoc.py:316` trước 25/08 viết

        trang_thai_ra = ("khong_tim_thay"
                         if "không có test nào bị đỏ" in vi_sao
                         else "khong_do_duoc")

    `vi_sao` là câu viết cho NGƯỜI ĐỌC. Đo thật trước khi vá — hai cách viết
    cùng nghĩa cho hai kết quả ngược nhau:

        "không có test nào bị đỏ trong tệp test"  ->  khong_tim_thay
        "không có test nào ĐỎ trong tệp test"     ->  khong_do_duoc

    Mà `khong_tim_thay` là ĐO ĐƯỢC mà không thấy, còn `khong_do_duoc` là KHÔNG
    đo được — hai điều ngược nhau trong kỷ luật của kho. Sửa một câu thông báo
    cho dễ đọc là đủ làm sổ bằng chứng ghi sai loại.

    Đúng họ bệnh §4 "đừng tự chấm điểm bằng dò chuỗi con".

    Test này giữ cho ai đó về sau đừng quay lại lối cũ: đổi CÂU CHỮ mà giữ MÃ
    thì kết quả KHÔNG được đổi.
    """
    src = tmp_path / "core" / "x.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(a):\n    return a < 5\n", encoding="utf-8")
    tst = tmp_path / "tests" / "test_x.py"
    tst.parent.mkdir(parents=True)
    tst.write_text("def test_1(): assert False\n", encoding="utf-8")

    def _chay(ma_ly_do, vi_sao):
        tra = {
            "trang_thai": "khong_chay",
            "ma_ly_do": ma_ly_do,
            "vi_sao": vi_sao,
            "test": "",
            "so_test_do": 0,
            "so_test_do_khac": 0,
            "dong_da_chay": [],
        }
        with patch("core.lat_nguoc._chon_test_va_dong", return_value=tra):
            return chay_e1_dinh_vi(tmp_path, "core/x.py", "tests/test_x.py")["trang_thai"]

    goc = _chay("khong_co_test_do", "không có test nào bị đỏ trong tệp test")
    assert goc == "khong_tim_thay"

    # Câu chữ viết lại, MÃ giữ nguyên -> kết quả PHẢI giữ nguyên.
    # Bản cũ (dò chuỗi con) sẽ trả `khong_do_duoc` ở đây.
    viet_lai = _chay("khong_co_test_do", "không có test nào ĐỎ trong tệp test")
    assert viet_lai == goc, (
        "Đổi câu chữ đã đổi kết quả — dòng 316 lại đang dò chuỗi con")

    # Mã khác -> phải là `khong_do_duoc`, kể cả khi câu chữ tình cờ chứa
    # đúng cụm cũ. Chiều ngược lại cũng phải đóng đinh.
    khac = _chay("het_tran_truoc_trace", "không có test nào bị đỏ trong tệp test")
    assert khac == "khong_do_duoc", (
        "Câu chữ đang thắng mã — dòng 316 lại đang dò chuỗi con")


def test_loi_hua_1_2_tren_DUONG_CO_CHAY_THAT(tmp_path):
    """SHA-256 tệp nguồn và tệp test KHÔNG đổi trên đường `trace_du`.

    VÌ SAO CÓ TEST NÀY, 25/08: đã có một test băm SHA trước/sau — phép đo đúng,
    nhưng nó mock `_chon_test_va_dong` trả `khong_chay`, mà
    `core/lat_nguoc.py:313` THOÁT NGAY khi trạng thái khác `trace_du`. Nên nó
    chứng minh "đường thoát sớm không ghi gì" — đường gần như không làm gì.

    Đếm trên tệp này lúc ấy: 23 test đi qua đường `trace_du` — đường THẬT SỰ
    lật mã và chạy suite con — và không test nào trong 23 kiểm tệp nguồn sau đó.

    Lời hứa "chạy hoàn toàn trên bản sao tạm" chỉ có giá trị ở chỗ nó CÓ ghi.

    Ở đây KHÔNG mock `_ma_sau_lat`: để phép lật thật chạy, để đường ghi thật
    được đi qua. Chỉ mock `subprocess.run` để khỏi gọi pytest con.
    """
    src = tmp_path / "core" / "calc.py"
    src.parent.mkdir(parents=True)
    src_noi_dung = "def f(x):\n    return x < 5\n"
    src.write_text(src_noi_dung, encoding="utf-8")

    tst = tmp_path / "tests" / "test_calc.py"
    tst.parent.mkdir(parents=True)
    tst_noi_dung = "def test_1(): assert False\n"
    tst.write_text(tst_noi_dung, encoding="utf-8")

    sha_src_truoc = hashlib.sha256(src.read_bytes()).hexdigest()
    sha_tst_truoc = hashlib.sha256(tst.read_bytes()).hexdigest()

    with patch("core.lat_nguoc._chon_test_va_dong") as mock_trace:
        mock_trace.return_value = {
            "trang_thai": "trace_du",          # đường CÓ lật mã và chạy suite
            "vi_sao": "ok",
            "test": "tests/test_calc.py::test_1",
            "so_test_do": 1,
            "so_test_do_khac": 0,
            "dong_da_chay": [2],
            "so_buoc": 3,
        }
        with patch("subprocess.run",
                   return_value=MagicMock(returncode=0, stdout="1 passed\n", stderr="")):
            res = chay_e1_dinh_vi(tmp_path, "core/calc.py", "tests/test_calc.py")

    # Đường này PHẢI đã thật sự làm việc — nếu nó lại thoát sớm thì test này
    # quay về vô nghĩa y như bản cũ.
    assert res["trang_thai"] == "tim_thay", res["trang_thai"]
    assert res["candidate_count_before"] > 0, "không sinh ứng viên nào — chưa đi vào đường ghi"

    # Bằng chứng: byte trên đĩa không đổi
    assert hashlib.sha256(src.read_bytes()).hexdigest() == sha_src_truoc
    assert hashlib.sha256(tst.read_bytes()).hexdigest() == sha_tst_truoc
    assert src.read_text(encoding="utf-8") == src_noi_dung
    assert tst.read_text(encoding="utf-8") == tst_noi_dung

    # Và bản vá đề xuất PHẢI khác bản gốc — nếu giống thì phép lật không chạy,
    # và "nguồn không đổi" trở thành hiển nhiên chứ không phải bằng chứng.
    diff = res["candidates"][0]["unified_diff"]
    assert "--- a/core/calc.py" in diff
    assert diff.strip() != ""

    assert res["analysis_on_temp_copy"] is True
    assert res["model_calls"] == 0
    assert res["external_submit"] is False
