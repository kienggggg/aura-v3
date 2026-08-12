# -*- coding: utf-8 -*-
"""Chữ nằm trong ĐƯỜNG DẪN không phải lời Sếp nói.

11/08/2026, Sếp dán một khối lỗi npm để hỏi "lỗi này là gì". Trong đó có dòng:

    C:\\Users\\baloa\\AppData\\Local\\Google\\Cloud SDK>ollama launch opencode

Chữ "Google" nằm giữa một đường dẫn thư mục khớp vào danh sách "Sếp bảo tra
mạng". AURA tưởng được lệnh đi google, đi tra thật — mà lúc đó đang MẤT MẠNG,
nên trả về `web_unavailable` sau 0,2 giây, chưa từng chạm tới bộ não local.

Một AI local mà mất mạng là câm thì nó không phải AI local.
"""
from __future__ import annotations

import pytest

from core.web_search import is_search_request, loi_sep_noi

LOI_NPM = (
    "lỗi này là gì: C:\\Users\\baloa\\AppData\\Local\\Google\\Cloud SDK>"
    "ollama launch opencode\n\nInstalling OpenCode...\nnpm error code 1\n"
    "npm error path C:\\Users\\baloa\\AppData\\Roaming\\npm\\node_modules\\opencode-ai\n"
    "Error: failed to install opencode: exit status 1"
)


def test_dung_cau_lam_AURA_di_tra_mang_luc_mat_mang():
    assert is_search_request(LOI_NPM) is False


@pytest.mark.parametrize("cau", [
    "lỗi ở C:\\Users\\baloa\\Google Drive\\a.txt là gì",
    "sao mở https://google.com/search không được",
    "chạy `google-chrome --headless` bị lỗi",
    "file /home/tim/thong-tin/data.json hỏng rồi",
])
def test_ten_trong_duong_dan_URL_va_ma_deu_khong_phai_lenh(cau):
    assert is_search_request(cau) is False


@pytest.mark.parametrize("cau", [
    "google giúp tôi giá vàng hôm nay",
    "tra mạng xem Python bản mới nhất là gì",
    "tìm thông tin về tỷ giá hiện nay",
])
def test_SEP_BAO_TRA_thi_van_phai_tra(cau):
    """Vá xong đừng làm AURA điếc trước lệnh thật của Sếp."""
    assert is_search_request(cau) is True


def test_loi_sep_noi_chi_dung_cho_kham_tu_khoa():
    """Câu gửi lên model phải NGUYÊN VẸN — model cần thấy đường dẫn để hiểu lỗi."""
    con_lai = loi_sep_noi(LOI_NPM)
    assert "google" not in con_lai.lower()
    assert "lỗi này là gì" in con_lai          # phần Sếp thật sự viết thì giữ
    assert "C:\\Users" not in con_lai
