# -*- coding: utf-8 -*-
"""Gõ không dấu vẫn phải ra cùng một kết quả.

Người Việt gõ không dấu rất nhiều, nhất là lúc vội.  Trước 10/08/2026 mọi luật
trong `web_search.py` so chuỗi CÓ DẤU, nên:

    "tỷ giá USD hiện nay"  -> tra mạng
    "ty gia USD hien nay"  -> KHÔNG tra gì cả

Cùng một câu hỏi, hai số phận, và Sếp không có cách nào đoán được vì sao.

Nhưng bỏ dấu làm nghĩa nhoè, nên không bỏ tuốt: "giá" mất dấu thành "gia",
đụng ngay "gia đình", "gia hạn", "đánh giá", "tham gia".
"""
from __future__ import annotations

import pytest

from core.web_search import bo_dau, is_search_request, la_chuyen_rieng_cua_sep


def test_bo_dau_xu_ly_ca_chu_d_gach():
    assert bo_dau("Tỷ giá hiện nay") == "ty gia hien nay"
    assert bo_dau("Đường Hà Nội") == "duong ha noi"


@pytest.mark.parametrize("co_dau,khong_dau", [
    ("Tin tức AI mới nhất", "Tin tuc AI moi nhat"),
    ("Thời tiết hôm nay thế nào?", "Thoi tiet hom nay the nao?"),
    ("Tra mạng giúp tôi cái này", "Tra mang giup toi cai nay"),
    ("Xu hướng công nghệ gần đây", "Xu huong cong nghe gan day"),
])
def test_co_dau_hay_khong_deu_RA_CUNG_MOT_KET_QUA(co_dau, khong_dau):
    assert is_search_request(co_dau) == is_search_request(khong_dau) is True


@pytest.mark.parametrize("co_dau,khong_dau", [
    ("Xe đạp của tôi màu gì?", "Xe dap cua toi mau gi?"),
    ("Lúc nãy tôi kể gì với em?", "Luc nay toi ke gi voi em?"),
])
def test_chuyen_rieng_cung_nhan_ra_khi_khong_dau(co_dau, khong_dau):
    assert la_chuyen_rieng_cua_sep(co_dau) is True
    assert la_chuyen_rieng_cua_sep(khong_dau) is True


@pytest.mark.parametrize("cau", [
    "Hom nay la thu may",
    "Bay gio may gio roi?",
])
def test_hoi_ngay_gio_khong_dau_van_dung_dong_ho(cau):
    assert is_search_request(cau) is False


@pytest.mark.parametrize("cau", [
    "Gia đình tôi có 4 người",
    "Gia hạn thẻ ngân hàng thế nào?",
    "Đánh giá của em về việc này ra sao?",
    "Tham gia câu lạc bộ có tốn phí không?",
])
def test_KHONG_nham_gia_dinh_thanh_gia_ca(cau):
    """Vá không dấu mà quét bừa thì "gia đình" hoá "giá cả" — tra mạng vô cớ.

    Đây là lý do `_MO_HO_KHI_BO_DAU` tồn tại: vài từ mất dấu là thành từ khác
    hẳn, nên chúng chỉ được so ở dạng CÓ DẤU.
    """
    assert is_search_request(cau) is False


def test_van_giu_dung_cho_co_dau():
    """Vá xong đừng làm hỏng đường cũ."""
    assert is_search_request("Giá Bitcoin hôm nay?") is True
    assert is_search_request("Thủ đô nước Pháp là gì?") is False
