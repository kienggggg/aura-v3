# -*- coding: utf-8 -*-
"""Cửa tra mạng phải HẸP — mở rộng quá thì AURA đi hỏi Google về chính nó.

10/08/2026, câu đời thường đầu tiên gõ vào màn hình chat v3:

    HỎI : Chào AURA, hôm nay em làm được gì cho Sếp?
    ĐÁP : ...ứng dụng Aura (nguồn [1]) để quản lý cuộc sống hiệu quả hơn...

51 giây, trích nguồn đàng hoàng, và nói về một app App Store không liên quan.
Gốc rễ không nằm ở lời dặn model — nằm ở `is_search_request`: `"hôm nay"` khớp
CHUỖI CON nên mọi câu chứa hai chữ đó đều bị đẩy đi tra mạng.
"""
from __future__ import annotations

import pytest

from core.web_search import is_search_request


@pytest.mark.parametrize("cau", [
    "Chào AURA, hôm nay em làm được gì cho Sếp?",
    "Chào buổi sáng",
    "AURA ơi, em là ai?",
    "Giới thiệu về bản thân em đi",
    "Hôm nay em nhớ gì về Sếp?",
])
def test_noi_voi_AURA_ve_chinh_no_thi_khong_tra_mang(cau):
    assert is_search_request(cau) is False


@pytest.mark.parametrize("cau", [
    "Hôm nay là thứ mấy, ngày bao nhiêu?",
    "Bây giờ mấy giờ rồi?",
    "Còn bao nhiêu ngày nữa tới ngày 1 tháng 9?",
])
def test_hoi_chinh_ngay_gio_thi_dung_dong_ho_chu_khong_tra_mang(cau):
    """`core/dong_ho.py` đã đưa giờ máy vào lời dặn — tra mạng là tốn công vô ích.

    Đo 10/08: câu đầu tốn 43,5 giây tra mạng rồi trả về đúng cái ngày mà đồng
    hồ đã đưa sẵn.
    """
    assert is_search_request(cau) is False


@pytest.mark.parametrize("cau", [
    "Giá Bitcoin hôm nay?",
    "Tin tức hôm nay có gì?",
])
def test_hoi_SU_KIEN_gan_chu_hom_nay_thi_van_phai_tra(cau):
    """Ranh giới hẹp: hỏi NGÀY thì dùng đồng hồ, hỏi GIÁ thì vẫn phải tra."""
    assert is_search_request(cau) is True


@pytest.mark.parametrize("cau", [
    "Tỷ giá USD sang VND hiện nay bao nhiêu?",
    "Giá Bitcoin hôm nay?",
    "Tin tức AI mới nhất",
    "Thời tiết Hà Nội hôm nay thế nào?",
])
def test_hoi_su_kien_ben_ngoai_thi_van_phai_tra_mang(cau):
    assert is_search_request(cau) is True


@pytest.mark.parametrize("cau", [
    "Tra giúp anh xem AURA nghĩa là gì",
    "Google hộ em cái này",
])
def test_Sep_bao_tra_thi_luon_tra_du_co_nhac_ten_AURA(cau):
    """Lệnh thẳng của Sếp thắng mọi luật khác — Sếp bảo tra thì tra."""
    assert is_search_request(cau) is True
