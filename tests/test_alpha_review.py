# -*- coding: utf-8 -*-
"""Alpha review — cửa chống bịa của `tools/alpha_review.py` (`CHOT:alpha-review-vong-0`, 15/09/2026).

Không gọi mạng, không gọi model: `kiem_cau` và `lam_sach` là hàm thuần, nên đưa câu xấu vào được.
"""
from __future__ import annotations

from tools import alpha_review as ar

# Câu mẫu trích từ Wikipedia tiếng Anh, bài "Skibidi Toilet", bản sửa 1374917295 (14/09/2026),
# giấy phép CC BY-SA 4.0 — https://en.wikipedia.org/w/index.php?oldid=1374917295
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


# ---- Ba luật thêm sau lần 1 (15/09): 12/12 câu qua cửa máy nhưng em đọc lại thì 4/12 sai nghĩa. ----
# Các ca dưới là CÂU THẬT model viết ở lần 1, trích từ cùng bài Wikipedia bản 1374917295.
NGUON_LAN_1 = NGUON + (
    "According to Tubefilter rankings, by the end of April 2023, DaFuq!?Boom! entered the 50 most viewed "
    "YouTube channels in the U.S., at 33rd place. By June, the channel had gained five billion views, making "
    "it the most viewed YouTube channel in the U.S. that month.\n"
    "An article by theatre firm The Civilians argued the series reflects Generation Alpha's fear of "
    "surveillance and dehumanization.\n"
    "Despite early reports saying that Bay was directing a Skibidi Toilet film, he denied them on 24 May 2025.\n"
    "Since YouTube's recommendation algorithm tends to prefer frequent uploaders, the initial upload "
    "schedule may have helped the show go viral.\n")


def test_trich_hai_cau_bi_bac():
    """Lần 1, câu 07: trích hai câu rồi viết "kênh xem nhiều nhất nước Mỹ", bỏ vế "trong tháng đó"."""
    trich = ("According to Tubefilter rankings, by the end of April 2023, DaFuq!?Boom! entered the 50 most viewed "
             "YouTube channels in the U.S., at 33rd place. By June, the channel had gained five billion views, "
             "making it the most viewed YouTube channel in the U.S. that month.")
    loi = ar.kiem_cau("Theo xếp hạng Tubefilter, kênh đã trở thành kênh YouTube được xem nhiều nhất tại Mỹ.",
                      trich, "Kênh xem nhiều nhất Mỹ", NGUON_LAN_1)
    assert any("hơn một câu" in x for x in loi)


def test_bo_moc_thoi_gian_bi_bac():
    """Lần 1, câu 12: "Bay lại bác bỏ tin đồn" — bỏ ngày, và bỏ luôn tin đồn nào."""
    trich = "Despite early reports saying that Bay was directing a Skibidi Toilet film, he denied them on 24 May 2025."
    loi = ar.kiem_cau("Dự án phim điện ảnh đã bắt đầu sản xuất nhưng đạo diễn Bay lại bác bỏ tin đồn.",
                      trich, "Bay bác bỏ tin đồn", NGUON_LAN_1)
    assert any("bỏ mốc thời gian" in x for x in loi)


def test_nhan_dinh_phai_neu_ten():
    """Lần 1, câu 10: "Các nhà nghiên cứu cho thấy…" — nguồn là một bài của nhóm kịch The Civilians."""
    trich = ("An article by theatre firm The Civilians argued the series reflects Generation Alpha's fear of "
             "surveillance and dehumanization.")
    sai = ar.kiem_cau("Các nhà nghiên cứu cho thấy loạt phim phản ánh nỗi sợ bị giám sát của thế hệ Alpha.",
                      trich, "Nỗi sợ bị giám sát", NGUON_LAN_1)
    assert any("nhận định của" in x for x in sai)
    dung = ar.kiem_cau("Một bài viết của nhóm kịch The Civilians lập luận rằng loạt phim phản ánh nỗi sợ bị giám sát.",
                       trich, "Nỗi sợ bị giám sát", NGUON_LAN_1)
    assert dung == []


def test_may_viet_thuong_khong_phai_thang_nam():
    """Bản đầu của luật mốc thời gian đọc "may have helped" thành tháng Năm và bác một câu đúng."""
    trich = ("Since YouTube's recommendation algorithm tends to prefer frequent uploaders, the initial upload "
             "schedule may have helped the show go viral.")
    assert ar.kiem_cau("Vì thuật toán YouTube ưa người đăng thường xuyên nên lịch đăng dày lúc đầu có thể giúp "
                       "loạt phim lan truyền.", trich, "Thuật toán YouTube", NGUON_LAN_1) == []


def test_lam_sach_bo_chu_thich_va_giu_hop_thong_tin():
    h = ('<table class="infobox"><tr><th class="infobox-label">No. of episodes</th><td>81</td></tr></table>'
         '<p>The first episode was released on 7 February 2023, with an 11-second runtime.<sup class="reference">'
         '<a href="#c1">[17]</a></sup></p><p>ngắn</p>')
    ra = ar.lam_sach(h).splitlines()
    assert "No. of episodes: 81" in ra
    assert "The first episode was released on 7 February 2023, with an 11-second runtime." in ra
    assert not any("[17]" in x for x in ra)
