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
    assert any("con số không có" in x and "90" in x for x in loi)


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


def test_chep_cau_da_co_bi_bac():
    """Lần 2: ý 10 và 11 lặp NGUYÊN VĂN câu của ý 09 — lời nhắc đưa câu trước vào, model chép lại."""
    cau09 = ("Tờ Washington Post nhận xét sự độc đáo khi loạt phim kể trọn vẹn một câu chuyện chỉ bằng các "
             "đoạn video ngắn.")
    trich = ("An article by theatre firm The Civilians argued the series reflects Generation Alpha's fear of "
             "surveillance and dehumanization.")
    loi = ar.kiem_cau(cau09, trich, "Nỗi sợ bị giám sát", NGUON_LAN_1, cau_da_co=(cau09,))
    assert any("lặp từ 6 từ liền" in x for x in loi)


def test_so_trong_cung_doan_nguon_duoc_phep():
    """Lần 2, ý 07: câu trích "By June, … that month." không mang năm; năm 2023 nằm ở câu liền trước của
    CÙNG đoạn — câu Việt nói "tháng 6 năm 2023" là đúng, không phải bịa."""
    trich = ("By June, the channel had gained five billion views, making it the most viewed YouTube channel "
             "in the U.S. that month.")
    assert ar.kiem_cau("Theo Tubefilter, trong tháng 6 năm 2023 kênh là kênh YouTube được xem nhiều nhất tại Mỹ "
                       "trong tháng đó.", trich, "Nhiều nhất tháng 6", NGUON_LAN_1) == []


def test_chu_viet_tat_khong_phai_het_cau():
    """Lần 3, ý 12: "A. V. Club" bị đọc thành ba câu và câu đúng bị bác cả 3 lượt."""
    nguon = NGUON + "The A. V. Club said that adapting Internet culture into traditional formats would be difficult.\n"
    trich = "The A. V. Club said that adapting Internet culture into traditional formats would be difficult."
    loi = ar.kiem_cau("Trang A. V. Club nhận xét rằng chuyển văn hoá mạng sang định dạng truyền thống sẽ rất khó.",
                      trich, "Chuyển thể khó", nguon)
    assert not any("hơn một câu" in x for x in loi), loi


def test_nam_trong_ngoac_khong_bat_buoc():
    """Lần 3, ý 03: "(born 1997 or 1998)" là chi tiết phụ — không bắt câu phải nói năm sinh."""
    nguon = NGUON + ("Skibidi Toilet is produced by Alexey Gerasimov (Russian: name, born 1997 or 1998), also known "
                     "by his alias Blugray.\n")
    trich = "Skibidi Toilet is produced by Alexey Gerasimov (Russian: name, born 1997 or 1998), also known by his alias Blugray."
    assert ar.kiem_cau("Loạt phim Skibidi Toilet do Alexey Gerasimov, còn có biệt danh Blugray, sản xuất.",
                       trich, "Alexey Gerasimov", nguon) == []


def test_bo_chu_rao_don_bi_bac():
    """Lần 3, ý 06: "may have helped" thành "giúp" — nói chắc điều nguồn chỉ nói là có thể."""
    trich = ("Since YouTube's recommendation algorithm tends to prefer frequent uploaders, the initial upload "
             "schedule may have helped the show go viral.")
    sai = ar.kiem_cau("Nhịp đăng dày lúc đầu giúp phim lan nhanh vì thuật toán YouTube thích người đăng tải thường xuyên.",
                      trich, "Thuật toán YouTube", NGUON_LAN_1)
    assert any("rào đón" in x for x in sai)
    dung = ar.kiem_cau("Nhịp đăng dày lúc đầu có thể đã giúp phim lan nhanh vì thuật toán YouTube thích người đăng "
                       "thường xuyên.", trich, "Thuật toán YouTube", NGUON_LAN_1)
    assert dung == []


def test_lam_sach_bo_chu_thich_va_giu_hop_thong_tin():
    h = ('<table class="infobox"><tr><th class="infobox-label">No. of episodes</th><td>81</td></tr></table>'
         '<p>The first episode was released on 7 February 2023, with an 11-second runtime.<sup class="reference">'
         '<a href="#c1">[17]</a></sup></p><p>ngắn</p>')
    ra = ar.lam_sach(h).splitlines()
    assert "No. of episodes: 81" in ra
    assert "The first episode was released on 7 February 2023, with an 11-second runtime." in ra
    assert not any("[17]" in x for x in ra)
