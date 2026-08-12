# -*- coding: utf-8 -*-
"""Con số TIỀN lệch một bậc nghìn phải bị chặn trước khi tới mắt Sếp.

10/08/2026, phiên thật của Sếp:
    HỎI : giá vàng ở miền bắc Việt Nam hôm nay là bao nhiêu
    ĐÁP : ...khoảng 137.500 đồng/lượng (mua vào) và 141.000 đồng/lượng (bán ra)
Sai 1000 lần — đúng là 137,5 TRIỆU đồng/lượng.
"""
from __future__ import annotations

import pytest

from core.kiem_tien import don_vi_dang_ngo, gan_canh_bao


@pytest.mark.parametrize("cau", [
    "Giá vàng miếng SJC hôm nay khoảng 137.500 đồng/lượng (mua vào).",
    "Vàng bán ra 141.000 đồng/lượng.",
    "Giá vàng nhẫn 14.050 đồng/chỉ.",
    "Xăng RON95 hiện 2.150 đồng/lít.",
])
def test_bat_duoc_so_lech_mot_bac_nghin(cau):
    assert don_vi_dang_ngo(cau) is True
    assert "không chắc ĐƠN VỊ" in gan_canh_bao(cau)


@pytest.mark.parametrize("cau", [
    "Giá vàng miếng SJC hôm nay khoảng 137.500.000 đồng/lượng.",
    "Vàng miếng bán ra 141 triệu đồng/lượng.",
    "Giá vàng khoảng 137,5 triệu đồng/lượng.",
    "Vàng nhẫn 14.050.000 đồng/chỉ.",
    "Xăng RON95 hiện 21.500 đồng/lít.",
])
def test_so_hop_ly_thi_de_yen(cau):
    assert don_vi_dang_ngo(cau) is False
    assert gan_canh_bao(cau) == cau


@pytest.mark.parametrize("cau", [
    "Hà Nội.",
    "Quả chuối chín màu vàng.",
    "def reverse_string(s): return s[::-1]",
    "",
    "Còn 144 ngày nữa đến 01/01/2027.",
])
def test_cau_khong_dinh_tien_thi_khong_dong_vao(cau):
    """Gắn cảnh báo bừa vào mọi câu là làm Sếp mất tin vào cảnh báo."""
    assert don_vi_dang_ngo(cau) is False
    assert gan_canh_bao(cau) == cau


def test_KHONG_TU_SUA_con_so():
    """Máy chắc được "số này vô lý"; nó KHÔNG chắc số đúng là bao nhiêu.

    Tự nhân lên 1000 rồi tuyên bố con số mới là AURA bịa ra giá — và bịa một
    con số tiền thì tệ hơn nhiều so với nói "em không chắc".
    """
    goc = "Giá vàng khoảng 137.500 đồng/lượng."
    ra = gan_canh_bao(goc)
    assert ra.startswith(goc), "câu gốc phải giữ nguyên"
    assert "137.500.000" not in ra
    assert "137,5 triệu" not in ra


def test_da_cam_vao_duong_tra_loi():
    """Viết bộ soát mà quên cắm thì viết cho ai xem."""
    import inspect

    from core import chat_service

    nguon = inspect.getsource(chat_service)
    assert "gan_canh_bao(text)" in nguon
