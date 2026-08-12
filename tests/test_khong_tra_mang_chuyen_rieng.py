# -*- coding: utf-8 -*-
"""Chuyện riêng của Sếp thì KHÔNG đẩy ra máy tìm kiếm.

10/08/2026 đo trên màn hình thật: sau khi dữ kiện rơi khỏi cửa sổ trí nhớ, câu
"Xe đạp của tôi màu gì?" làm AURA đi tra mạng **55,4 giây** rồi mới chịu nói là
mình quên.  Google không biết xe đạp của Sếp màu gì — và chuyện tệ hơn cả chậm
là câu hỏi riêng tư ấy vừa bị đẩy ra một máy chủ bên ngoài.

Luật `is_search_request` đã bảo câu này không cần mạng.  Cái đòi tra là MODEL,
và lời model chỉ là ý kiến hạng hai — nó không được phép lật luật.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, ChatStatus
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.secret_guard import SecretContentGuard
from core.web_search import la_chuyen_rieng_cua_sep


@pytest.mark.parametrize("cau", [
    "Xe đạp của tôi màu gì?",
    "Con mèo của mình tên gì ấy nhỉ?",
    "Lúc nãy tôi kể gì với em?",
    "Em còn nhớ tôi nói gì không?",
    "Wifi nhà tôi tên là gì?",
])
def test_nhan_ra_chuyen_rieng(cau):
    assert la_chuyen_rieng_cua_sep(cau) is True


@pytest.mark.parametrize("cau", [
    "Giá Bitcoin hôm nay bao nhiêu?",
    "Tin tức AI mới nhất",
    "Thủ đô nước Pháp là gì?",
])
def test_chuyen_ngoai_doi_thi_khong_phai_chuyen_rieng(cau):
    assert la_chuyen_rieng_cua_sep(cau) is False


class _DoiTraMang:
    history_window = 24

    async def generate(self, request, *, history=(), sources=()):
        return ModelReply(text="[[AURA_REQUIRES_WEB]]", requires_web=True)


class _MayTimKiem:
    def __init__(self) -> None:
        self.lan_goi = 0

    async def search(self, query):
        self.lan_goi += 1
        return ()


class _So:
    def __init__(self, so_tin: int) -> None:
        self._tin = tuple(
            ChatMessage(role="user" if i % 2 == 0 else "aura", content=f"tin {i}")
            for i in range(so_tin)
        )

    async def load(self, *, actor_id, session_id):
        return self._tin

    async def append_exchange(self, *, request, result):
        return None


def _hoi(text: str, *, so_tin: int = 40):
    web = _MayTimKiem()
    service = ChatService(
        model=_DoiTraMang(), store=_So(so_tin), guard=SecretContentGuard(),
        web=web, timeout_s=30.0,
    )
    ket_qua = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text=text,
    )))
    return ket_qua, web


def test_KHONG_goi_may_tim_kiem_cho_chuyen_rieng():
    """Đây là cả tiền lẫn quyền riêng tư, không chỉ là tốc độ."""
    ket_qua, web = _hoi("Xe đạp của tôi màu gì?")
    assert web.lan_goi == 0, "vừa đẩy chuyện riêng của Sếp ra máy tìm kiếm"
    assert ket_qua.status is ChatStatus.CANNOT_ANSWER
    assert ket_qua.used_web is False


def test_van_noi_ro_la_QUEN_chu_khong_phai_khong_biet():
    ket_qua, _ = _hoi("Xe đạp của tôi màu gì?", so_tin=40)
    assert "QUÊN" in ket_qua.text


@pytest.mark.parametrize("cau", [
    "Viết giúp tôi hàm Python kiểm tra một tên miền có hợp lệ không",
    "viet ham python dao nguoc chuoi",          # gõ không dấu
    "Sửa lỗi giúp em đoạn này với",
    "Gợi ý tên miền cho trang bán sách cũ",
])
def test_viec_TU_LAM_thi_khong_di_tra_mang(cau):
    """10/08, chat thật: câu viết hàm làm AURA tra mạng 71,7 giây.

    Model tự đòi (luật đã bảo là không cần), rồi mang về 3 nguồn chẳng liên
    quan cho một hàm 10 dòng. Internet không viết hộ hàm được.
    """
    from core.web_search import la_viec_tu_lam

    assert la_viec_tu_lam(cau) is True
    _, web = _hoi(cau)
    assert web.lan_goi == 0, "vừa đi tra mạng cho một việc phải tự làm"


def test_chuyen_ngoai_doi_thi_VAN_duoc_tra_mang():
    """Vá hẹp thôi — đừng vá xong lại làm AURA mù tịt chuyện thế giới."""
    _, web = _hoi("Phiên bản Python mới nhất là gì?")
    assert web.lan_goi >= 1
