# -*- coding: utf-8 -*-
"""Câu hỏi về SỔ PHIÊN không được đẩy ra máy chủ tìm kiếm.

BẮT ĐƯỢC BẰNG CÁCH CHẠY APP THẬT, KHÔNG BẰNG ĐỌC MÃ (10/09/2026). Lượt thứ tư
của một phiên thật:

    "câu đầu tiên tôi hỏi là gì"
    -> HTTP 200 · status=web_unavailable · 50,7 giây
    -> "Câu này cần tra nguồn mới, nhưng AURA chưa lấy đủ nguồn đáng tin cậy."

Sổ phiên của chính nó nằm ngay đó. `is_search_request` trả `False` cho cả sáu
cách hỏi — luật từ vựng đúng; thứ lật ngược là `loai_cau_hoi` xếp câu vào
`tra_cuu` qua `_HOI_DINH_NGHIA` ("là gì"), rồi `requires_web` bật fail-closed.

Nền đo được: **bộ A 1/6 · bộ B 0/6**. Cách hỏi duy nhất còn sống là câu có chữ
"phiên này" — đúng câu được vá riêng 12/08/2026, còn mọi cách hỏi bên cạnh thì
không. Đúng ca *"vá xong một trường không nói gì về trường bên cạnh"*.

Ngưỡng chép TAY từ khối `CHOT:so-phien-khong-di-tra-mang`.
"""
from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.chat_contract import ChatRequest  # noqa: E402
from core.chat_service import DeterministicFreshnessPolicy  # noqa: E402
from core.paths import PROJECT_ROOT  # noqa: E402

# Chép TAY. Không nhập từ tệp đo — hai bên phải cãi nhau được.
DAC_TA_BO_A = 6
DAC_TA_BO_B = 5
DAC_TA_DOI_CHUNG = 11

BO_A = ("câu đầu tiên tôi hỏi là gì",
        "câu hỏi đầu tiên của tôi là gì",
        "câu thứ 2 là gì",
        "câu hỏi thứ ba là gì",
        "câu thứ nhất tôi hỏi là gì",
        "câu hỏi thứ 2 tôi hỏi trong phiên này là gì")

BO_B = ("câu thứ tư là gì",
        "câu hỏi đầu là gì",
        "câu hỏi thứ 5 tôi đã hỏi là gì",
        "câu thứ hai là gì",
        "câu hỏi thứ 1 là gì")

# Phán quyết NỀN, đo trước khi vá. Bản vá không được đổi một dòng nào ở đây —
# nới rộng bừa là mở lại lỗ bịa tiểu sử 13/08/2026.
DOI_CHUNG_NEN = (
    ("Phạm Xuân Kiên là ai", True),
    ("Nguyễn Tất Thành hỏi gì", False),
    ("giá vàng hôm nay bao nhiêu", True),
    ("thời tiết Hà Nội thế nào", True),
    ("viết một bài thơ về Hồ Chí Minh", False),
    ("hôm nay là ngày mấy", False),
    ("1247 nhân 38 bằng bao nhiêu", False),
    ("lỗi này là gì", False),
    # HAI CA THÊM 10/09 SAU KHI GIEO CHỨNG MINH BỘ CŨ MÙ.
    #
    # Gieo hai phép nới bừa mà cả 8 ca cũ đều xanh:
    #   "mien theo _DAU_HIEU mot minh"  -> VẪN XANH
    #   "bo chan _TEN_RIENG"            -> VẪN XANH
    #
    # Vì không ca nào vừa khớp luật hẹp vừa mang tên riêng, và không ca nào
    # cần mạng mà lại chứa "hỏi gì". Ca đối chứng chỉ đối chứng được thứ nó
    # phân biệt nổi — 8 ca "giữ nguyên" không chứng minh gì về hai chiều ấy.
    ("câu thứ 2 của Nguyễn Tất Thành là gì", True),   # bỏ _TEN_RIENG -> đổi
    ("người ta hỏi gì về giá vàng hôm nay", True),
    # CA THỨ 11: LẦN THỬ ĐẦU CHO CHIỀU NÀY CŨNG TRƯỢT, vì lý do khác hẳn.
    #
    # "người ta hỏi gì về giá vàng hôm nay" khớp `_DAU_HIEU` đúng như tính,
    # nhưng `is_search_request` TỰ NÓ trả True cho câu ấy ("giá", "hôm nay").
    # `requires_web` vẫn True bất kể `loai_cau_hoi` nói gì, nên phép gieo vẫn
    # xanh. Ca đối chứng phải nằm ở chỗ mà ĐÚNG cái đang thử là thứ duy nhất
    # giữ nó lại:
    #
    #     lex=False · loai=tra_cuu · _DAU_HIEU=True · luật hẹp=False
    #
    # Hai lần trượt, hai nguyên nhân khác nhau, cùng một bài học: một ca đối
    # chứng chỉ đối chứng được thứ nó PHÂN BIỆT NỔI — và "phân biệt nổi" phải
    # được KIỂM, không được suy ra.
    ("câu hỏi kinh điển của triết học là gì", True),  # nới _DAU_HIEU -> đổi
)


class _Tin:
    def __init__(self, role: str, content: str) -> None:
        self.role, self.content = role, content


LICH_SU = [_Tin("user", "1247 nhân 38 bằng bao nhiêu"),
           _Tin("assistant", "47.386"),
           _Tin("user", "hôm nay là ngày mấy"),
           _Tin("assistant", "Hôm nay là thứ Năm, ngày 10 tháng 9 năm 2026."),
           _Tin("user", "Chào Sếp, giới thiệu ngắn gọn về bản thân đi"),
           _Tin("assistant", "Tôi là AURA"),
           _Tin("user", "phòng epsilon kiểm được mấy ngôn ngữ"),
           _Tin("assistant", "năm"),
           _Tin("user", "bộ dịch rust đã xong chưa"),
           _Tin("assistant", "rồi")]


def _can_mang(text: str) -> bool:
    return DeterministicFreshnessPolicy().requires_web(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="sep", channel="web", text=text))


@pytest.mark.parametrize("cau", BO_A + BO_B)
def test_cau_hoi_ve_SO_PHIEN_khong_bi_day_di_tra_mang(cau: str):
    """Không đi tra mạng, VÀ sổ trả lời được.

    Hai vế phải cùng đúng. Miễn khỏi tra mạng mà sổ không trả lời được thì câu
    rơi xuống model đoán — đo 13/08/2026 trên đúng lối ấy được **1/5**, tức
    tệ hơn là nói thẳng "chưa lấy được nguồn".
    """
    from core.doc_so_phien import tra_loi_thang, tra_so

    assert not _can_mang(cau), f"vẫn bị đẩy đi tra mạng: {cau!r}"
    assert tra_loi_thang(cau, LICH_SU) or tra_so(cau, LICH_SU), (
        f"miễn tra mạng nhưng sổ không trả lời được: {cau!r}")


def test_DEM_du_hai_bo_de():
    """`parametrize` trên bộ thiếu thì xanh vì rỗng — `KHÔNG ĐO ĐƯỢC` đội lốt."""
    assert len(BO_A) == DAC_TA_BO_A, f"bộ A còn {len(BO_A)} câu"
    assert len(BO_B) == DAC_TA_BO_B, f"bộ B còn {len(BO_B)} câu"
    assert len(DOI_CHUNG_NEN) == DAC_TA_DOI_CHUNG


@pytest.mark.parametrize("cau,nen", DOI_CHUNG_NEN)
def test_DOI_CHUNG_giu_nguyen_phan_quyet_NEN(cau: str, nen: bool):
    """Tám câu này KHÔNG được đổi. Đây là nhóm quan trọng nhất của bản vá.

    `_DAU_HIEU` của `doc_so_phien` có `hoi gi`, nên miễn trừ theo nó thì
    *"Nguyễn Tất Thành hỏi gì"* cũng thoát — mở lại đúng lỗ 13/08/2026 khi
    AURA bịa nguyên một tiểu sử trong 5,2 giây.
    """
    assert _can_mang(cau) is nen, (
        f"phán quyết đổi so với nền: {cau!r} nền={nen} nay={_can_mang(cau)}")


def test_CHO_THIEU_da_biet_van_o_lai_va_van_NOI_THAT():
    """*"câu đầu tiên là gì"* CỐ Ý không được miễn — và đó là ca đối chứng.

    `_DAU_HIEU` không nhận ra nó nên sổ không trả lời được. Miễn nó thì câu rơi
    xuống model đoán. Bài này giữ cho chỗ thiếu ấy **được biết**: ai nới
    `hoi_ve_so_phien` rộng ra thì phải sửa cả đặc tả, không nới lặng lẽ.

    Nó cũng là ca đối chứng cho bài trên: nếu miễn trừ mà rộng tới đây thì
    điều kiện đã không còn là "đúng cửa vào của `tra_so`".
    """
    from core.doc_so_phien import hoi_ve_so_phien, tra_loi_thang, tra_so

    cau = "câu đầu tiên là gì"
    assert not hoi_ve_so_phien(cau)
    assert not (tra_loi_thang(cau, LICH_SU) or tra_so(cau, LICH_SU))


def test_MIEN_TRU_dung_CHUNG_mot_ham_khong_phai_ban_sao():
    """Hai bản sao của một luật sẽ trôi khỏi nhau.

    `chat_service` đã ghi sẵn lời cảnh báo về *"một luật biểu thức chính quy
    thứ hai cạnh tranh"*. Bài này giữ cho `loai_cau_hoi` NHẬP hàm ấy chứ không
    chép các mẫu của `doc_so_phien` sang.
    """
    van = (PROJECT_ROOT / "core" / "loai_cau_hoi.py").read_text(encoding="utf-8")
    assert "from core.doc_so_phien import hoi_ve_so_phien" in van, (
        "loai_cau_hoi không còn nhập hoi_ve_so_phien")
    for mau in ("cau\\s*hoi|cau\\s*thu", "dau\\s*tien|dau"):
        assert mau not in van, f"luật của doc_so_phien bị chép sang: {mau}"


def test_NGUONG_khop_khoi_dac_ta():
    """Ngưỡng phải có chỗ đứng ngoài mã, để hai bên cãi nhau được."""
    khoi = re.search(
        r"<!-- CHOT:so-phien-khong-di-tra-mang -->(.*?)"
        r"<!-- /CHOT:so-phien-khong-di-tra-mang -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:so-phien-khong-di-tra-mang"
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", khoi.group(1), re.M))
    a = hang.get("bộ A sau vá", "")
    b = hang.get("bộ B sau vá", "")
    dc = hang.get("đối chứng", "")
    assert f"{DAC_TA_BO_A}/6" in a, f"đặc tả bộ A: {a!r}"
    assert f"{DAC_TA_BO_B}/6" in b, f"đặc tả bộ B: {b!r}"
    assert f"{DAC_TA_DOI_CHUNG}/11" in dc, f"đặc tả đối chứng: {dc!r}"
    # Cái nền phải ở lại: "6/6" đứng một mình không nói được nó hơn cái gì.
    assert "nền 1/6" in a and "nền 0/6" in b, "cắt mất số NỀN khỏi đặc tả"
