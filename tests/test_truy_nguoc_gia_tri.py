# -*- coding: utf-8 -*-
"""Neo phép rút gọn chuỗi truy ngược mà không đổi tập dòng tìm được."""
from __future__ import annotations

from experiments.evidence_sprint.truy_nguoc_gia_tri import (
    _rut_gon_chuoi_theo_dong,
    truy_nguoc,
)


def test_rut_gon_giu_muc_dau_va_khong_gom_dong_khong_ro():
    """25/08: chỉ dòng nguyên mới chứng minh được hai mục trùng vị trí;
    gom mọi mục thiếu dòng vào cùng khoá None sẽ làm mất dữ liệu thật.
    """
    dau = {"dong": 7, "ten_bien": "a"}
    lap = {"dong": 7, "ten_bien": "b"}
    khong_ro_1 = {"dong": None, "ten_bien": "c"}
    khong_ro_2 = {"dong": None, "ten_bien": "d"}

    day_du = [dau, lap, khong_ro_1, khong_ro_2]
    ket_qua = _rut_gon_chuoi_theo_dong(day_du)

    assert ket_qua == [dau, khong_ro_1, khong_ro_2]
    assert ket_qua[0] is dau
    assert day_du == [dau, lap, khong_ro_1, khong_ro_2]


def test_truy_nguoc_gom_luot_ghi_lap_nhung_giu_nguyen_tap_dong():
    """25/08: hai biến và hai nhánh hàng đợi cùng quay về một dòng từng tạo
    5 mục cho 3 dòng; người dùng chỉ phải thấy mỗi dòng đúng một lần.
    """
    nguon = (
        "def f():\n"
        "    x = 1\n"
        "    a = b = x\n"
        "    return a + b\n"
    )
    su_kien = [
        {"buoc": 1, "dong": 2, "ten_bien": "x", "gia_tri_moi": 1,
         "su_kien": "gan", "dong_ma": "x = 1"},
        {"buoc": 2, "dong": 3, "ten_bien": "a", "gia_tri_moi": 1,
         "su_kien": "gan", "dong_ma": "a = b = x"},
        {"buoc": 3, "dong": 3, "ten_bien": "b", "gia_tri_moi": 1,
         "su_kien": "gan", "dong_ma": "a = b = x"},
        {"buoc": 4, "dong": 4, "ten_bien": "<tra_ve>", "gia_tri_moi": 2,
         "su_kien": "tra_ve", "dong_ma": "return a + b"},
    ]

    ket_qua = truy_nguoc(su_kien, nguon)

    assert ket_qua["dong"] == [4, 3, 2]
    assert [muc["dong"] for muc in ket_qua["chuoi"]] == [4, 3, 2]
    assert len(ket_qua["chuoi"]) == len(ket_qua["dong"])


def test_rut_gon_khong_lam_mat_canh_qua_ham():
    """25/08: độ chính xác 0,77 đến từ cạnh qua hàm; rút phần hiển thị
    không được chặn lượt duyệt từ outer() vào inner().
    """
    nguon = (
        "def inner(x):\n"
        "    y = x + 1\n"
        "    return y\n"
        "\n"
        "def outer(a):\n"
        "    b = inner(a)\n"
        "    return b\n"
    )
    su_kien = [
        {"buoc": 1, "dong": 2, "ten_bien": "y", "gia_tri_moi": 2,
         "su_kien": "gan", "dong_ma": "y = x + 1"},
        {"buoc": 2, "dong": 3, "ten_bien": "<tra_ve>", "gia_tri_moi": 2,
         "su_kien": "tra_ve", "dong_ma": "return y"},
        {"buoc": 3, "dong": 6, "ten_bien": "b", "gia_tri_moi": 2,
         "su_kien": "gan", "dong_ma": "b = inner(a)"},
        {"buoc": 4, "dong": 7, "ten_bien": "<tra_ve>", "gia_tri_moi": 2,
         "su_kien": "tra_ve", "dong_ma": "return b"},
    ]

    ket_qua = truy_nguoc(su_kien, nguon)

    assert ket_qua["dong"] == [7, 6, 3, 2]
    assert [muc["dong"] for muc in ket_qua["chuoi"]] == [7, 6, 3, 2]
    assert len(ket_qua["chuoi"]) == len(ket_qua["dong"])
