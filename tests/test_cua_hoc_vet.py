# -*- coding: utf-8 -*-
"""Cửa chặn học vẹt phải BẮT ĐƯỢC bản gian, và không bắt oan bản thật.

Test quan trọng nhất là `test_bat_duoc_ban_hoc_vet`: một cửa chặn gian mà chưa
từng chặn được cái gì thì chỉ là lời hứa. Ở đây nó phải bắt đúng bản gian kinh
điển — ghi cứng đáp án của ví dụ đã cho.
"""
from __future__ import annotations

import pytest

from core.cua_hoc_vet import De, cham

DE = De(
    ten_ham="cong",
    mo=[((2, 3), 5), ((0, 0), 0)],
    kin=[((10, 7), 17), ((-4, 4), 0), ((100, 1), 101)],
)

THAT = "def cong(a, b):\n    return a + b\n"

# Bản gian: ghi cứng đúng hai ví dụ MỞ, còn lại trả 0.
HOC_VET = (
    "def cong(a, b):\n"
    "    if a == 2 and b == 3:\n"
    "        return 5\n"
    "    if a == 0 and b == 0:\n"
    "        return 0\n"
    "    return 0\n"
)


def test_ban_that_thi_dat():
    k = cham(THAT, DE)
    assert k.trang_thai == "dat"
    assert bool(k) is True
    assert (k.mo_dat, k.kin_dat) == (2, 3)


def test_bat_duoc_ban_hoc_vet():
    """Bản gian khớp 100% ví dụ MỞ — cửa vẫn phải chặn."""
    k = cham(HOC_VET, DE)
    assert k.trang_thai == "hoc_vet"
    assert k.mo_dat == k.mo_tong == 2      # mở: khớp sạch
    assert k.kin_dat < k.kin_tong          # kín: lòi ra
    assert bool(k) is False


def test_sai_hoan_toan_thi_truot_khong_phai_hoc_vet():
    """Ba trạng thái không được gộp: trượt KHÁC học vẹt."""
    k = cham("def cong(a, b):\n    return 999\n", DE)
    assert k.trang_thai == "truot"


def test_thieu_ham_thi_khong_do_duoc():
    k = cham("x = 1\n", DE)
    assert k.trang_thai == "khong_do_duoc"


def test_ma_hong_cu_phap_thi_khong_do_duoc():
    k = cham("def cong(a, b:\n", DE)
    assert k.trang_thai == "khong_do_duoc"


def test_loi_nhac_KHONG_lo_vi_du_kin():
    """Rò một ví dụ kín vào lời nhắc là hỏng cả cái cửa."""
    p = DE.loi_nhac()
    assert "(2, 3)" in p and "5" in p
    for vao, ra in DE.kin:
        assert repr(vao) not in p, f"lộ ví dụ kín {vao}"
    assert "17" not in p and "101" not in p


def test_phan_biet_True_voi_1():
    """True == 1 trong Python. 'trả về True' khác 'trả về 1'."""
    d = De(ten_ham="la_duong", mo=[((5,), True)], kin=[((-1,), False)])
    assert cham("def la_duong(n):\n    return n > 0\n", d).trang_thai == "dat"
    assert cham("def la_duong(n):\n    return 1\n", d).trang_thai == "truot"


def test_ma_lap_vo_han_khong_treo_may_do():
    """Mã model sinh lặp vô hạn là chuyện thường — cửa phải tự cắt."""
    k = cham("def cong(a, b):\n    while True:\n        pass\n", DE)
    assert k.trang_thai == "khong_do_duoc"
    assert "treo" in k.ly_do
