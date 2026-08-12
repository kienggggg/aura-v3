# -*- coding: utf-8 -*-
"""`used_web` phải trả lời đúng câu Sếp thật sự quan tâm.

Câu đó không phải "câu trả lời có trích nguồn không" — nhìn khối nguồn dưới bong
bóng chat là thấy.  Câu đó là: **"lượt vừa rồi câu hỏi của tôi có bị gửi ra máy
chủ bên ngoài không?"**

Cách tính cũ (`used_web = bool(sources)`) báo SAI ở hai chỗ, cả hai đều theo
hướng giấu bớt:
  - tra mạng xong, model không rút được gì từ nguồn  -> báo False
  - tra mạng ra dưới 2 nguồn nên fail-closed         -> báo False
Cả hai trường hợp câu hỏi ĐỀU đã rời khỏi máy rồi.
"""
from __future__ import annotations

import asyncio
import uuid

from core.chat_contract import ChatRequest, ChatStatus, SourceCitation
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.secret_guard import SecretContentGuard


def _nguon(i: int) -> SourceCitation:
    return SourceCitation(
        title=f"Nguồn {i}", url=f"https://vi.dụ{i}.com/bai",
        retrieved_at="2026-08-10T12:00:00+00:00", supports="dữ kiện",
    )


class _So:
    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        return None


class _Web:
    def __init__(self, so_nguon: int) -> None:
        self._nguon = tuple(_nguon(i) for i in range(1, so_nguon + 1))
        self.lan_goi = 0

    async def search(self, query):
        self.lan_goi += 1
        return self._nguon


class _Model:
    """Nhận nguồn rồi vẫn bó tay — đúng ca "Tỷ giá USD" đo được 10/08."""

    history_window = 24

    def __init__(self, van_doi_mang: bool) -> None:
        self._van_doi = van_doi_mang

    async def generate(self, request, *, history=(), sources=()):
        if self._van_doi:
            return ModelReply(text="[[AURA_REQUIRES_WEB]]", requires_web=True)
        return ModelReply(text="Đáp án dựa trên nguồn [1][2].", requires_web=False)


def _hoi(model, web):
    service = ChatService(
        model=model, store=_So(), guard=SecretContentGuard(),
        web=web, timeout_s=30.0,
    )
    return asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web",
        text="Tỷ giá USD sang VND hiện nay bao nhiêu?",
    )))


def test_tra_mang_xong_ma_model_bo_tay_VAN_khai_la_da_tra():
    web = _Web(so_nguon=4)
    ket_qua = _hoi(_Model(van_doi_mang=True), web)
    assert web.lan_goi >= 1, "phép thử hỏng: chưa gọi mạng lần nào"
    assert ket_qua.used_web is True, "đã gửi câu của Sếp ra ngoài mà báo là không"
    assert ket_qua.status is ChatStatus.CANNOT_ANSWER


def test_co_nguon_ma_bo_tay_thi_DUNG_do_cho_tri_nho():
    """Nhìn trên màn hình 10/08: mang về 4 nguồn tỷ giá rồi bảo "em quên".

    Đổ oan cho trí nhớ, và bỏ phí 4 cái link đang nằm ngay dưới bong bóng chat.
    """
    ket_qua = _hoi(_Model(van_doi_mang=True), _Web(so_nguon=4))
    assert "QUÊN" not in ket_qua.text, "có nguồn trong tay thì không phải chuyện quên"
    assert "4 nguồn" in ket_qua.text
    assert len(ket_qua.sources) == 4, "bó tay thì cũng phải đưa nguồn cho Sếp tự đọc"


def test_tra_mang_ra_du_nguon_thi_van_dung_nhu_cu():
    web = _Web(so_nguon=4)
    ket_qua = _hoi(_Model(van_doi_mang=False), web)
    assert ket_qua.used_web is True
    assert ket_qua.status is ChatStatus.OK
    assert len(ket_qua.sources) == 4


def test_KHONG_goi_mang_thi_van_phai_bao_la_khong():
    """Chiều ngược lại quan trọng ngang: đừng dọa Sếp là đã tra khi chưa tra."""
    web = _Web(so_nguon=0)

    class _TuTraLoi:
        history_window = 24

        async def generate(self, request, *, history=(), sources=()):
            return ModelReply(text="Hà Nội.", requires_web=False)

    service = ChatService(
        model=_TuTraLoi(), store=_So(), guard=SecretContentGuard(),
        web=web, timeout_s=30.0,
    )
    ket_qua = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Thủ đô Việt Nam là gì?",
    )))
    assert web.lan_goi == 0
    assert ket_qua.used_web is False
