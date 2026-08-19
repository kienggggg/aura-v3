# -*- coding: utf-8 -*-
"""Khay thẻ: sinh từ mã thật, lọc theo việc, và biết thẻ nào đã cũ.

Không test "lọc ra đúng 6/6" — con số đó đổi theo kho mã, test kiểu ấy chỉ đo
cái kho chứ không đo mã. Test những tính chất KHÔNG được phép đổi.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.khay_the import (
    The, bang_khay, bo_dau, loc_khay, sinh_khay, the_da_cu,
)


@pytest.fixture
def kho(tmp_path: Path) -> Path:
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "a.py").write_text(
        'def cau_gio(now):\n'
        '    """Nói bây giờ là mấy giờ, lấy từ đồng hồ máy."""\n'
        '    return "3 gio"\n\n'
        'def _rieng_tu():\n'
        '    """Hàm nội bộ, KHÔNG được thành thẻ."""\n'
        '    return 1\n\n'
        'def bo_dau_chuoi(s):\n'
        '    """Bỏ dấu tiếng Việt khỏi chuỗi."""\n'
        '    return s\n',
        encoding="utf-8")
    return tmp_path


def test_sinh_the_tu_ma_that_bo_ham_noi_bo(kho):
    ten = {t.ten for t in sinh_khay(kho, ("core",))}
    assert ten == {"cau_gio", "bo_dau_chuoi"}
    assert "_rieng_tu" not in ten          # gạch dưới = nội bộ, không phát thẻ


def test_the_mang_chu_ky_va_mo_dun_that(kho):
    t = next(x for x in sinh_khay(kho, ("core",)) if x.ten == "cau_gio")
    assert t.chu_ky == "cau_gio(now)"
    assert t.mo_dun == "core.a"
    assert "đồng hồ máy" in t.mo_ta


def test_the_da_cu_khi_ma_doi(kho):
    """Thẻ chép tay sẽ cũ đi và model gọi hàm đã xoá MỘT CÁCH TỰ TIN.

    Đây là lý do thẻ sinh-ra phải sinh lại mỗi lần, và phải biết mình đã cũ.
    """
    khay = sinh_khay(kho, ("core",))
    assert the_da_cu(khay, kho) == []      # chưa đổi gì

    (kho / "core" / "a.py").write_text(
        'def cau_gio(now, mui_gio):\n'
        '    """Đổi chữ ký rồi."""\n'
        '    return "3 gio"\n',
        encoding="utf-8")
    cu = the_da_cu(khay, kho)
    assert {t.ten for t in cu} == {"cau_gio", "bo_dau_chuoi"}


def test_bo_dau_de_so_duoc_tieng_viet():
    assert bo_dau("hỏi giờ") == "hoi gio"
    assert bo_dau("Đường") == "Duong"


def test_loc_uu_tien_TEN_hon_MO_TA():
    """Tên là thứ người viết đặt để gọi đúng việc; mô tả là văn xuôi dễ trùng."""
    khay = [
        The("bo_dau", "core.x", "bo_dau(s)", "xử lý chuỗi", "aa"),
        The("xu_ly", "core.y", "xu_ly(s)", "hàm này bỏ dấu tiếng Việt khỏi chuỗi", "bb"),
    ]
    ra = loc_khay(khay, "bỏ dấu chuỗi", 1)
    assert ra[0].ten == "bo_dau"


def test_loc_khong_bao_gio_tra_qua_so_yeu_cau():
    khay = [The(f"ham_{i}", "core.x", f"ham_{i}()", "tra cứu dữ liệu", f"h{i}")
            for i in range(30)]
    assert len(loc_khay(khay, "tra cứu dữ liệu", 5)) == 5


def test_loc_khay_rong_khong_no():
    assert loc_khay([], "việc gì đó", 8) == []


def test_tu_hiem_thang_tu_pho_bien():
    """Từ có ở 9/10 thẻ gần như vô nghĩa; từ chỉ có ở 1 thẻ mới đáng tin.

    Bản đầu đếm từ chung trần trụi nên chỉ giữ được thẻ đúng 3/6 — mọi thẻ đều
    được 1 điểm nhờ một từ phổ biến, và thứ tự thành ngẫu nhiên.
    """
    khay = [The(f"pho_bien_{i}", "core.x", f"pho_bien_{i}()", "tra cứu mạng", f"p{i}")
            for i in range(9)]
    khay.append(The("hiem", "core.y", "hiem()", "bỏ dấu tiếng Việt", "z9"))
    ra = loc_khay(khay, "tra cứu bỏ dấu", 1)
    assert ra[0].ten == "hiem"


def test_bang_khay_in_du_chu_ky_va_mo_dun():
    b = bang_khay([The("f", "core.x", "f(a)", "làm việc gì đó", "h")])
    assert "f(a)" in b and "core.x" in b and "làm việc gì đó" in b
