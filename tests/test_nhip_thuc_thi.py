# -*- coding: utf-8 -*-
"""test_nhip_thuc_thi.py — Kiểm thử đối chiếu Đáp Án Chuẩn (Ground Truth, Dung sai = 0 nhịp).

Kiểm tra chính xác số nhịp và cấu trúc nhịp của 4 hàm chuẩn trong Ma trận nghiệm thu:
1. Nhóm 1: core/dong_ho.py :: cau_gio -> 1 nhịp (KKX, khuyết B)
2. Nhóm 2: core/web_search.py :: _public_http_url -> 6 nhịp (KBX | BX | BX | KBX | BX | KKX)
3. Nhóm 3: core/doc_so_phien.py :: tra_so -> 5 nhịp (KBX | KBX | KBKKBKBX | BX | KBKX)
4. Ca biên: core/kiem_tien.py :: don_vi_dang_ngo -> 2 nhịp (KBBKBKBKKKBKBX | X, nhịp rỗng chỉ có X)
"""
from __future__ import annotations

from pathlib import Path
import pytest

from core.nhip_thuc_thi import (
    NhipThucThi,
    chia_nhip_thuc_thi,
    phan_tich_nhip_cho_ham,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_nhom_1_dong_ho_cau_gio():
    """Nhóm 1: core/dong_ho.py :: cau_gio — 3 thẻ, đúng 1 nhịp (KKX, khuyết B)."""
    tep = PROJECT_ROOT / "core" / "dong_ho.py"
    nhip_list = phan_tich_nhip_cho_ham(tep, "cau_gio")

    assert len(nhip_list) == 1, f"cau_gio phải có đúng 1 nhịp, nhận được {len(nhip_list)}"
    nhip_1 = nhip_list[0]
    assert nhip_1.mat_cat == "KKX"
    assert nhip_1.co_khuyet_b is True
    assert nhip_1.co_rong is False


def test_nhom_2_web_search_public_http_url():
    """Nhóm 2: core/web_search.py :: _public_http_url — đúng 8 nhịp.

    CON SỐ ĐỔI 6 -> 8 NGÀY 25/08/2026, VÀ ĐÂY KHÔNG PHẢI NỚI NGƯỠNG.

    Hàm này có HAI khối `try/except ValueError` (`core/web_search.py:303` và
    `:330`). Trước 25/08 khay thẻ không có thẻ nào cho `try`, nên mỗi khối gom
    thành ĐÚNG MỘT thẻ `ma_tho`. Từ khi có thẻ `thu` và `bat_loi`, mỗi khối
    tách thành hai thẻ có cấu trúc — cộng đúng 2 nhịp.

    Kiểm được: đếm `try:` trong hàm ra 2, và 6 + 2 = 8. Bất biến thật của phép
    đo — MỌI nhịp phải đóng bằng `X` — không đổi và vẫn được khẳng định dưới.
    """
    tep = PROJECT_ROOT / "core" / "web_search.py"
    nhip_list = phan_tich_nhip_cho_ham(tep, "_public_http_url")

    assert len(nhip_list) == 8, f"_public_http_url phải có đúng 8 nhịp, nhận được {len(nhip_list)}"
    mat_cat_cac_nhip = [n.mat_cat for n in nhip_list]
    assert all(mc.endswith("X") for mc in mat_cat_cac_nhip)
    assert "".join(mat_cat_cac_nhip) == "KBXKKXBXBXKBXKKKBXBXKKX"


def test_nhom_3_doc_so_phien_tra_so():
    """Nhóm 3: core/doc_so_phien.py :: tra_so — 20 thẻ, đúng 5 nhịp."""
    tep = PROJECT_ROOT / "core" / "doc_so_phien.py"
    nhip_list = phan_tich_nhip_cho_ham(tep, "tra_so")

    assert len(nhip_list) == 5, f"tra_so phải có đúng 5 nhịp, nhận được {len(nhip_list)}"
    mat_cat_cac_nhip = [n.mat_cat for n in nhip_list]
    assert all(mc.endswith("X") for mc in mat_cat_cac_nhip)
    assert "".join(mat_cat_cac_nhip) == "KBXKBXKBKKBKBXBXKBKX"


def test_ca_bien_kiem_tien_don_vi_dang_ngo():
    """Ca biên: core/kiem_tien.py :: don_vi_dang_ngo — 15 thẻ, đúng 2 nhịp (nhịp 2 rỗng chỉ có X)."""
    tep = PROJECT_ROOT / "core" / "kiem_tien.py"
    nhip_list = phan_tich_nhip_cho_ham(tep, "don_vi_dang_ngo")

    assert len(nhip_list) == 2, f"don_vi_dang_ngo phải có đúng 2 nhịp, nhận được {len(nhip_list)}"
    assert nhip_list[0].mat_cat == "KBBKBKBKKKBKBX"
    assert nhip_list[1].mat_cat == "X"
    assert nhip_list[1].co_rong is True, "Nhịp thứ 2 phải là nhịp rỗng (chỉ có X)"
