"""Canh bộ phân loại câu hỏi — thứ quyết định AURA bịa hay nói không biết.

13/08/2026 Sếp test thật: "Phạm Xuân Kiên là ai" -> AURA bịa nguyên một tiểu sử
về chính tên Sếp trong 5,2 giây. Cùng phiên, "Nguyễn Tất Thành là ai" ra một
người khác hẳn Hồ Chí Minh.

Sai một nhãn ở đây kéo theo hai loại hỏng ngược nhau:
  bỏ sót TRA_CUU  -> AURA bịa dữ kiện về người thật
  bắt nhầm TRA_CUU -> câu tự làm được bị đẩy đi tra 20-30 giây vô ích
"""
from __future__ import annotations

import pytest

from core.loai_cau_hoi import SANG_TAC, TRA_CUU, TU_NGHI, loai


# --------------------------------------------------------------------------- #
# TRA CỨU — dữ kiện về thực thể có thật, PHẢI có nguồn
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cau", [
    "Hồ Chí Minh là ai",
    "Nguyễn Tất Thành là ai",
    "Phạm Xuân Kiên là ai",       # chính câu làm AURA bịa
    "CEO của Apple là ai",
    "Công ty VinFast thành lập năm nào",
    "Trần Hưng Đạo sinh năm nào",
    "giá vàng hôm nay",
])
def test_hoi_du_kien_that_thi_phai_tra_cuu(cau):
    assert loai(cau) == TRA_CUU, cau


def test_hoi_nguoi_luon_phai_tra_du_noi_tieng_toi_dau():
    """Không có ngoại lệ cho người nổi tiếng.

    Chính chỗ "model chắc là nó biết" mới là chỗ nó bịa tự tin nhất — Hồ Chí
    Minh và Nguyễn Tất Thành là cùng một người, mà AURA trả về hai tiểu sử.
    """
    assert loai("Hồ Chí Minh là ai") == TRA_CUU


# --------------------------------------------------------------------------- #
# SÁNG TÁC — bịa là ĐÚNG VIỆC, và không được đi tra
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cau", [
    "Viết một bài thơ về mùa thu",
    "Làm giúp em bài thơ tặng mẹ",
    "Sáng tác giúp em lời chúc sinh nhật",
    "Viết một truyện ngắn về con mèo",
    "Viết kịch bản cho video 30 giây",
])
def test_sang_tac_thi_tu_lam(cau):
    assert loai(cau) == SANG_TAC, cau


def test_sang_tac_THANG_ten_rieng():
    """"Viết bài thơ về Hồ Chí Minh" là làm thơ, không phải tra tiểu sử."""
    assert loai("Viết một bài thơ về Hồ Chí Minh") == SANG_TAC


@pytest.mark.parametrize("cau", [
    "Viết một bài thơ về mùa thu năm nay",
    "Sáng tác giúp em lời chúc cho ngày hôm nay",
    "Viết caption về xu hướng mới nhất",
])
def test_sang_tac_THANG_chu_chi_do_moi(cau):
    """Thứ tự xét CÓ Ý NGHĨA — và đây mới là ca chứng minh được điều đó.

    Bản đầu tôi viết test bằng "Viết bài thơ về Hồ Chí Minh" rồi tưởng nó canh
    được thứ tự. Đảo thứ tự trong mã thì test VẪN XANH: câu đó không khớp luật
    TRA_CUU nào cả, nên xếp trước hay sau đều ra SANG_TAC.

    Ca thật là câu sáng tác có kèm chữ chỉ độ mới. Xét TRA_CUU trước thì
    "năm nay" / "hôm nay" / "mới nhất" kéo nó đi tra 20-30 giây, để rồi vẫn
    phải tự làm thơ.
    """
    assert loai(cau) == SANG_TAC, cau


# --------------------------------------------------------------------------- #
# TỰ NGHĨ — đừng làm chậm những câu đang chạy tốt
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cau", [
    "AI là gì",
    "1247 nhân 38 bằng bao nhiêu",
    "Viết hàm Python đảo ngược một chuỗi",   # "viết" nhưng là lập trình
    "Tóm tắt đoạn văn sau",
    "Còn while thì sao",
    "Hàm vừa rồi có xử lý chuỗi rỗng không",
])
def test_viec_tu_lam_thi_khong_di_tra(cau):
    assert loai(cau) == TU_NGHI, cau


def test_o_dau_ve_MA_CUA_SEP_khong_bi_day_di_tra():
    """"ở đâu" chỉ tính khi có tên riêng đi kèm.

    Bản đầu dùng char class `[A-ZĐÀ-Ỹ]` để dò tên riêng — dải `À-Ỹ` BAO CẢ CHỮ
    THƯỜNG có dấu, nên "ở đâu" tự khớp làm tên riêng và câu hỏi về mã của Sếp
    bị đẩy ra Internet.
    """
    for cau in ("lỗi này nằm ở đâu", "hàm vừa rồi lỗi ở đâu", "biến đó khai ở đâu"):
        assert loai(cau) == TU_NGHI, cau


def test_cau_rong_khong_no():
    for cau in ("", "   ", None):
        assert loai(cau) == TU_NGHI


# ---------------------------------------------------------------------------
# DẠNG ĐẦU RA cho câu sáng tác — bản tương đương trưng cất tri thức lúc suy luận
#
# 13/08/2026: Sếp gõ "viết 1 bài thơ về AURA", AURA trả về ĐOẠN VĂN XUÔI gạch
# đầu dòng. Trưng cất thật phải huấn luyện lại trọng số — máy này 11,7 GB RAM
# không GPU rời. Cái làm được là đưa VÍ DỤ MẪU vào lời dặn cạnh câu hỏi.
# ---------------------------------------------------------------------------


def test_xin_tho_thi_dan_xuong_dong_va_co_mau():
    from core.loai_cau_hoi import loi_dan_dang

    ra = loi_dan_dang("viết 1 bài thơ về AURA")
    assert ra is not None
    assert "MỘT DÒNG" in ra, "phải dặn mỗi câu một dòng"
    assert "Ví dụ" in ra, "phải có mẫu để model bắt chước dạng"
    # Mẫu phải THẬT SỰ nhiều dòng, không thì nó dạy sai đúng thứ cần dạy.
    assert ra.count("\n") >= 5


def test_cau_sang_tac_bi_cam_gach_dau_dong():
    """Ảnh chụp phiên thật: bài thơ trả về mở đầu bằng "- "."""
    from core.loai_cau_hoi import loi_dan_dang

    for cau in ("viết 1 bài thơ về AURA", "viết truyện ngắn về con mèo",
                "sáng tác lời chúc sinh nhật"):
        ra = loi_dan_dang(cau)
        assert ra is not None and "không dùng gạch đầu dòng" in ra.lower(), cau


def test_cau_KHONG_sang_tac_thi_khong_dan_gi():
    """Đừng nhét lời dặn thừa vào câu đang chạy tốt — mỗi chữ là thời gian chờ."""
    from core.loai_cau_hoi import loi_dan_dang

    for cau in ("AI là gì", "1247 nhân 38", "Hồ Chí Minh là ai",
                "Viết hàm Python đảo chuỗi"):
        assert loi_dan_dang(cau) is None, cau


def test_luat_gach_dau_dong_trong_loi_dan_he_thong_da_co_dieu_kien():
    """Khối ĐỊNH DẠNG viết bằng gạch đầu dòng, và model chép lại CÁI DẠNG đó."""
    from core.local_first_gateway import OllamaConfig

    assert "CHỈ dùng gạch đầu dòng KHI Sếp xin" in OllamaConfig().system_prompt


def test_DA_CAM_loi_dan_dang_VAO_CONG():
    """Viết bộ dặn dạng mà quên cắm thì viết cho ai xem.

    Test ở trên chỉ canh HÀM. Gỡ `loi_dan_dang` khỏi `_messages` thì chúng vẫn
    xanh hết — đã đột biến thử và không cái nào đỏ. Test này canh chỗ CẮM.
    """
    import asyncio
    import uuid

    from core.chat_contract import ChatRequest
    from core.local_first_gateway import OllamaConfig, OllamaGateway

    gate = OllamaGateway(OllamaConfig(), client=None)
    msgs = gate._messages(
        ChatRequest(
            request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
            actor_id="owner:web", channel="web",
            text="viết 1 bài thơ về mùa thu",
        ),
        history=(),
        sources=(),
    )
    # Đi kèm CÂU HỎI, không chôn trong lời dặn hệ thống.
    cuoi = msgs[-1]
    assert cuoi["role"] == "user"
    assert "DẠNG ĐẦU RA" in cuoi["content"], "lời dặn dạng chưa tới được model"
    assert "Ví dụ" in cuoi["content"]
    del asyncio
