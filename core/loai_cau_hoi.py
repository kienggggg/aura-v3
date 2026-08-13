# -*- coding: utf-8 -*-
"""Câu này thuộc loại nào — tự nghĩ, đi tra, hay được phép bịa.

13/08/2026, Sếp test thật và bắt được chỗ nguy nhất:

    Sếp: "Phạm Xuân Kiên là ai"
    AURA: "một nhà văn, nhà báo, một trong những người sáng lập Báo chí Việt Nam"

Bịa hoàn toàn, về chính tên Sếp, và nói chắc nịch trong 5,2 giây. Cùng phiên:
"Nguyễn Tất Thành là ai" ra một người khác hẳn Hồ Chí Minh — hai câu liền nhau,
cùng một người, hai tiểu sử khác nhau.

VÌ SAO LỌT: luật cũ chỉ có MỘT TRỤC — "câu này có cần dữ liệu MỚI không".
"giá vàng hôm nay" có chữ chỉ độ mới nên đi tra; "X là ai" thì không, nên model
tự trả lời từ trí nhớ tham số. Model 1.7B không có tri thức đó, và nó không im.

THIẾU TRỤC THỨ HAI: **câu này có đáp án KIỂM CHỨNG ĐƯỢC ngoài đời không.**
Tiểu sử một người là dữ kiện, không phải ý kiến — sai là sai, và sai về người
thật thì tệ hơn nhiều so với nói "em không biết".

BA LOẠI, đúng như Sếp mô tả:

    SANG_TAC   bịa là ĐÚNG VIỆC — thơ, truyện, kịch bản, lời chúc.
               Tra mạng ở đây là vô nghĩa và tốn 20-30 giây.
    TU_NGHI    máy/model tự làm — toán, mã, dịch, tóm tắt, giải thích khái niệm.
               Đáp án nằm trong chính câu hỏi hoặc trong năng lực suy luận.
    TRA_CUU    dữ kiện về một thực thể có thật — PHẢI có nguồn, hoặc nói không
               biết. Đây là loại vừa làm AURA bịa.

Trả `TRA_CUU` là bật đường fail-closed đã có sẵn trong `ChatService`: tra được
thì trả lời kèm nguồn, tra không đủ nguồn thì trạng thái `web_unavailable` và
AURA nói thẳng là chưa lấy được nguồn. **Không có đường nào dẫn tới bịa.**

Cố ý dùng LUẬT TỪ KHOÁ chứ không hỏi model: quyết định "có tra hay không" phải
xem lại được và không đổi giữa hai lần chạy — cùng lý do đã ghi ở
`web_search.is_search_request`.
"""
from __future__ import annotations

import re
import unicodedata

SANG_TAC = "sang_tac"
TU_NGHI = "tu_nghi"
TRA_CUU = "tra_cuu"

# --------------------------------------------------------------------------- #
# SÁNG TÁC — bịa là đúng việc.
# Phải có ĐỘNG TỪ TẠO RA + THỨ ĐỂ SÁNG TÁC, không bắt mỗi chữ "viết": "viết hàm
# Python" là lập trình, không phải sáng tác.
# --------------------------------------------------------------------------- #
_DONG_TU_TAO = r"(?:viet|lam|sang tac|soan|ke|nghi ra|tuong tuong|dat)"
_THU_SANG_TAC = (
    r"(?:bai tho|tho|truyen|truyen ngan|kich ban|loi bai hat|bai hat|van|"
    r"doan van|bai van|loi chuc|cau chuyen|tieu thuyet|slogan|khau hieu|"
    r"loi thoai|cau tho|ca dao|ve|tut|caption|status)"
)
_SANG_TAC = re.compile(rf"(?<!\w){_DONG_TU_TAO}\s+(?:\w+\s+){{0,2}}{_THU_SANG_TAC}(?!\w)")

# --------------------------------------------------------------------------- #
# TRA CỨU — dữ kiện về thực thể có thật.
# --------------------------------------------------------------------------- #

# "X là ai" — hỏi về một NGƯỜI. Đây là mẫu đã làm AURA bịa hai lần trong một
# phiên. Không có ngoại lệ nào: kể cả người rất nổi tiếng cũng phải có nguồn,
# vì chính chỗ "model chắc là nó biết" mới là chỗ nó bịa tự tin nhất.
_HOI_NGUOI = re.compile(r"(?<!\w)la\s+ai(?!\w)")

# Câu hỏi mà ĐỒNG HỒ MÁY đã có sẵn đáp án. `cau_gio()` gắn mốc thời gian vào
# mỗi lượt, nên đẩy mấy câu này ra Internet là vừa chậm 20-30 giây vừa SAI —
# model chép ngày trên trang web thay vì đọc mốc ngay trước mặt.
#
# Đòi hỏi cả VẾ THỜI GIAN lẫn VẾ HỎI, không bắt mỗi "hôm nay": "giá vàng hôm
# nay" phải đi tra thật, chỉ "hôm nay NGÀY MẤY" mới là hỏi đồng hồ.
_HOI_GIO_MAY = re.compile(
    r"(?<!\w)(?:hom nay|bay gio|hien tai|luc nay|hom qua|ngay mai|tuan nay"
    r"|thang nay|nam nay)(?!\w)[^\n]{0,24}"
    r"(?:ngay may|thu may|may gio|ngay bao nhieu|la ngay|la thu|la may)(?!\w)"
    r"|(?<!\w)(?:ngay may|thu may|may gio)(?!\w)[^\n]{0,24}"
    r"(?:hom nay|bay gio|roi)(?!\w)"
)

# "X là gì" — hỏi ĐỊNH NGHĨA. Bản đầu tôi chỉ bắt "là ai" và tưởng thế là đủ.
#
# 13/08/2026 Sếp gõ "claude là gì" -> "Claude là một tên người, một trong những
# người sáng lập hệ thống điều khiển trí tuệ tại EPFL". Dựng lại trong phiên
# MỚI TINH: "Claude là một loại ngôn ngữ mã nguồn mở". Hai lần, hai câu bịa
# khác nhau, 0 nguồn. Sếp hỏi có phải do phiên chat cũ không — không, do luật
# thiếu.
#
# Cùng ngày, "AI là gì" cũng ra sai hai lần: "Hệ thống Điều khiển Trí tuệ" rồi
# "Hệ thống Tự động" (đúng là "trí tuệ nhân tạo"). Tức model 1.7B KHÔNG đáng
# tin cho câu định nghĩa, kể cả với thứ nó có vẻ phải biết.
#
# GIÁ PHẢI TRẢ: mỗi câu "là gì" giờ mất 20-30 giây vì phải ra mạng. Đổi tốc độ
# lấy việc không bịa. Sếp đã chốt hướng đó: "giờ chỉ cần AURA trả lời được".
_HOI_DINH_NGHIA = re.compile(r"(?<!\w)la\s+(?:gi|cai gi)(?!\w)")

# ...TRỪ khi câu hỏi trỏ vào thứ NGAY TRONG cuộc trò chuyện: "lỗi này là gì"
# (Sếp vừa dán một khối lỗi), "hàm vừa rồi là gì". Đáp án nằm trong lịch sử,
# không nằm ngoài Internet — đẩy đi tra là vừa chậm vừa sai chỗ, và còn đẩy
# chuyện riêng của Sếp ra ngoài.
_TRO_VE_NGU_CANH = re.compile(
    r"(?<!\w)(?:nay|do|kia|vua roi|vua noi|tren|duoi|ben tren|o tren|"
    r"tren day|ban dau|luc nay|phia tren)(?!\w)"
)

# Vị từ hỏi một DỮ KIỆN cụ thể — trả lời sai là sai hẳn, không phải "diễn đạt
# khác đi". Có thực thể viết hoa đi kèm thì bắt buộc tra.
_VI_TU_DU_KIEN = re.compile(
    r"(?<!\w)(?:"
    r"thanh lap (?:nam|khi|tu) nao|thanh lap nam|ra doi nam nao|"
    r"sinh (?:nam|ngay) nao|mat (?:nam|ngay) nao|qua doi nam nao|"
    r"bao nhieu tuoi|sinh nhat|que (?:o|quan)|"
    r"tru so|dat o dau|nam o dau|o dau|"
    r"giam doc|ceo|nguoi sang lap|chu tich|tong giam doc|"
    r"dan so|dien tich|cao bao nhieu|dai bao nhieu|"
    r"gia bao nhieu|bao nhieu tien|doanh thu|von hoa"
    r")(?!\w)"
)

# Tên riêng: một chữ viết hoa KHÔNG đứng đầu câu ("VinFast", "Hồ Chí Minh").
# Đầu câu không tính — câu nào chẳng viết hoa chữ đầu.
#
# LIỆT KÊ THẲNG chữ hoa, không dùng dải: `[A-ZĐÀ-Ỹ]` trông có vẻ đúng nhưng dải
# `À-Ỹ` (U+00C0–U+1EF8) BAO CẢ CHỮ THƯỜNG có dấu. Đo 13/08: "lỗi này nằm ở đâu"
# bị nhận là có tên riêng vì "ở đâu" khớp — chữ "ở" nằm trong dải đó. Hậu quả:
# một câu hỏi về mã của Sếp bị đẩy đi tra mạng.
#
# Và phải nhận tên MỘT CHỮ: bản đầu bắt buộc hai chữ hoa liền nhau nên
# "Công ty VinFast thành lập năm nào" lọt — "Công" đứng đầu câu bị loại, còn
# "VinFast" một mình thì không đủ.
_HOA = (
    "A-Z"
    "ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ"
    "ĂĐĨŨƠƯ"
    "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ"
)
_TEN_RIENG = re.compile(rf"(?<!^)(?<![.!?]\s)\b[{_HOA}][\wÀ-ỹ]*")

# Chữ báo "câu này cần dữ liệu ngoài", dùng chung với `web_search`.
# KHÔNG nhập từ đó để tệp này đứng một mình, đọc là hiểu.
_CHU_DO_MOI = re.compile(
    r"(?<!\w)(?:hom nay|hien nay|bay gio|moi nhat|gan day|nam nay|"
    r"tin tuc|dang hot|xu huong|vua ra|vua cong bo|cap nhat)(?!\w)"
)


def _bo_dau(text: str) -> str:
    tach = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in tach if not unicodedata.combining(c)).replace("đ", "d")


def loai(text: str) -> str:
    """Phân loại câu hỏi. Thứ tự xét CÓ Ý NGHĨA.

    1. SÁNG TÁC thắng trước: "viết một bài thơ về Hồ Chí Minh" là làm thơ, không
       phải tra tiểu sử. Xét sau thì tên riêng kéo nó sang TRA_CUU và AURA đi
       tra 30 giây để rồi vẫn phải tự làm thơ.
    2. TRA CỨU: hỏi về người, hoặc dữ kiện cụ thể, hoặc cần dữ liệu mới.
    3. Còn lại TỰ NGHĨ — giữ nguyên hành vi cũ, không làm chậm những câu đang chạy tốt.
    """
    if not isinstance(text, str) or not text.strip():
        return TU_NGHI

    moc = _bo_dau(text)

    if _SANG_TAC.search(moc):
        return SANG_TAC

    # ĐỒNG HỒ THẮNG TRƯỚC MỌI LUẬT TRA MẠNG.
    #
    # 13/08/2026, hỏi AURA đang chạy: "Hôm nay là ngày mấy?" -> "Hôm nay là
    # ngày 06/08/2026", KÈM 4 NGUỒN. Sai 7 ngày, và sai vì nó đi tra mạng rồi
    # chép ngày trên một trang web.
    #
    # Trớ trêu: `cau_gio()` lúc đó trả đúng "12:28 Thứ Năm, ngày 13 tháng 8 năm
    # 2026", và trong chính câu đó có dòng "đừng đoán và đừng tra mạng để biết
    # ngày". Máy biết đúng, lời dặn ghi rõ, mà bộ phân loại vẫn đẩy đi tra —
    # rồi model tin trang web hơn tin lời dặn.
    #
    # Lời dặn không phải hàng rào. Hàng rào là ĐỪNG ĐỂ CÂU ĐÓ ĐI TRA.
    if _HOI_GIO_MAY.search(moc) and not _TEN_RIENG.search(text):
        return TU_NGHI

    if _HOI_NGUOI.search(moc):
        return TRA_CUU
    if _CHU_DO_MOI.search(moc):
        return TRA_CUU
    # Xét SAU `_CHU_DO_MOI`: "giá vàng hôm nay là gì" đã thành TRA_CUU ở trên,
    # nên chữ "nay" trong "hôm nay" không kịp bị hiểu nhầm là trỏ ngữ cảnh.
    if _HOI_DINH_NGHIA.search(moc) and not _TRO_VE_NGU_CANH.search(moc):
        return TRA_CUU
    # Dữ kiện cụ thể CHỈ tính khi có tên riêng: "ở đâu" trong "lỗi này nằm ở
    # đâu" là hỏi về mã của Sếp, không phải hỏi địa chỉ một nơi có thật.
    if _VI_TU_DU_KIEN.search(moc) and _TEN_RIENG.search(text):
        return TRA_CUU

    return TU_NGHI


# Thứ để sáng tác có DẠNG riêng. Model 1.7B không tự suy ra được, phải đưa mẫu.
#
# 13/08/2026: Sếp gõ "viết 1 bài thơ về AURA", AURA trả về một ĐOẠN VĂN XUÔI
# gạch đầu dòng — "AURA là một người phụ nữ đầy sức sống..." — kèm đúng một câu
# trong ngoặc kép. Xin thơ, nhận văn.
#
# Đây là bản tương đương của trưng cất tri thức Ở LÚC SUY LUẬN: trưng cất thật
# phải huấn luyện lại trọng số, mà máy này 11,7 GB RAM không GPU rời (cùng rổ
# với Unsloth và DiffusionGemma đã loại). Cái làm được là đưa VÍ DỤ MẪU vào lời
# dặn để model bắt chước dạng — trưng cất vào lời dặn thay vì vào trọng số.
#
# Mẫu cố tình NGẮN và TẦM THƯỜNG về nội dung: nó dạy DẠNG, không dạy ý. Mẫu hay
# quá thì model chép luôn cả ý.
_MAU_THO = (
    "Ví dụ ĐÚNG DẠNG (chỉ học cách trình bày, đừng chép nội dung):\n"
    "Nắng lên trên mái hiên nhà\n"
    "Gió đưa hương lúa bay qua cánh đồng\n"
    "Chiều về nghiêng bóng bên sông\n"
    "Một mình ta đứng ngóng trông cuối trời"
)

_THO = re.compile(r"(?<!\w)(?:tho|bai tho|cau tho|ca dao|luc bat|tho \w+ chu)(?!\w)")
_TRUYEN = re.compile(r"(?<!\w)(?:truyen|truyen ngan|cau chuyen|tieu thuyet|kich ban)(?!\w)")


def loi_dan_dang(text: str) -> str | None:
    """Lời dặn về DẠNG đầu ra, gắn cạnh câu hỏi. `None` nếu không cần.

    Đặt cạnh CÂU HỎI chứ không nhét vào `system_prompt`: luật đã trả giá trong
    `local_first_gateway._messages` — nhét vào lời dặn hệ thống thì model bỏ
    qua, hoặc tệ hơn là ĐỌC THUỘC LÒNG nó ra mặt Sếp.
    """
    if loai(text) != SANG_TAC:
        return None

    moc = _bo_dau(text)
    chung = (
        "DẠNG ĐẦU RA: đây là bài sáng tác. TUYỆT ĐỐI không dùng gạch đầu dòng, "
        "không mở đầu bằng \"- \", không giải thích, không nói \"đây là bài thơ "
        "của tôi\". Viết thẳng tác phẩm."
    )
    if _THO.search(moc):
        return (
            f"{chung}\n"
            "Thơ thì phải xuống dòng: mỗi câu MỘT DÒNG riêng, ít nhất 4 dòng, "
            "có vần hoặc có nhịp. Không viết thành đoạn văn xuôi.\n"
            f"{_MAU_THO}"
        )
    if _TRUYEN.search(moc):
        return (
            f"{chung}\n"
            "Truyện thì phải có mở đầu, diễn biến và kết — kể chuyện, đừng mô tả "
            "chung chung."
        )
    return chung


__all__ = ["loai", "loi_dan_dang", "SANG_TAC", "TU_NGHI", "TRA_CUU"]
