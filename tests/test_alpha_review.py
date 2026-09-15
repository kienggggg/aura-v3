# -*- coding: utf-8 -*-
"""Alpha review — cửa chống bịa của `tools/alpha_review.py` (`CHOT:alpha-review-vong-0`, 15/09/2026).

Không gọi mạng, không gọi model: `kiem_cau` và `lam_sach` là hàm thuần, nên đưa câu xấu vào được.
"""
from __future__ import annotations

from tools import alpha_review as ar

NGUON = ("The first episode of Skibidi Toilet was released on 7 February 2023 (UTC), with an 11-second "
         "runtime. By November 2023, YouTube videos associated with Skibidi Toilet had accumulated "
         "over 65 billion views.\n")
TRICH_DAU = "The first episode of Skibidi Toilet was released on 7 February 2023 (UTC), with an 11-second runtime."
CAU_DAU = "Tập đầu tiên của Skibidi Toilet ra mắt ngày 7 tháng 2 năm 2023 và chỉ dài vỏn vẹn 11 giây."


def test_cau_dung_qua_cua():
    assert ar.kiem_cau(CAU_DAU, TRICH_DAU, "11 giây", NGUON) == []


def test_trich_bia_bi_bac():
    """Model bịa đoạn trích 'nghe giống nguồn' — sai MỘT chữ cũng không có nguyên văn trong nguồn."""
    bia = "The first episode of Skibidi Toilet was released on 7 February 2023 (UTC), with a 12-second runtime."
    loi = ar.kiem_cau(CAU_DAU.replace("11", "12"), bia, "12 giây", NGUON)
    assert any("KHÔNG có nguyên văn" in x for x in loi)


def test_trich_ngan_bi_bac():
    """Đoạn ngắn thì khớp được vào đâu cũng được — đúng bệnh dò chuỗi con."""
    loi = ar.kiem_cau(CAU_DAU, "11-second runtime", "11 giây", NGUON)
    assert any("cần ≥ 8" in x for x in loi)


def test_con_so_khong_co_trong_trich_bi_bac():
    loi = ar.kiem_cau(CAU_DAU + " Nó có 90 tỷ lượt xem.", TRICH_DAU, "11 giây", NGUON)
    assert any("con số không có trong đoạn trích" in x and "90" in x for x in loi)


def test_thang_chu_anh_doi_ra_so():
    """'February' trong đoạn trích cho phép số 2 trong câu Việt ('tháng 2'); 'November' cho 11."""
    trich = "By November 2023, YouTube videos associated with Skibidi Toilet had accumulated over 65 billion views."
    assert ar.kiem_cau("Tới tháng 11 năm 2023, các video liên quan tới Skibidi Toilet đã vượt 65 tỷ lượt xem.",
                       trich, "65 tỷ lượt xem", NGUON) == []


def test_chu_tieng_anh_la_bi_bac_ten_rieng_thi_mien():
    loi = ar.kiem_cau("Tập đầu tiên của Skibidi Toilet cực kỳ viral, ra mắt ngày 7 tháng 2 năm 2023, dài 11 giây.",
                      TRICH_DAU, "11 giây", NGUON)
    assert any("viral" in x for x in loi)
    assert not any("Skibidi" in x or "Toilet" in x for x in loi)


def test_lam_sach_bo_chu_thich_va_giu_hop_thong_tin():
    h = ('<table class="infobox"><tr><th class="infobox-label">No. of episodes</th><td>81</td></tr></table>'
         '<p>The first episode was released on 7 February 2023, with an 11-second runtime.<sup class="reference">'
         '<a href="#c1">[17]</a></sup></p><p>ngắn</p>')
    ra = ar.lam_sach(h).splitlines()
    assert "No. of episodes: 81" in ra
    assert "The first episode was released on 7 February 2023, with an 11-second runtime." in ra
    assert not any("[17]" in x for x in ra)
