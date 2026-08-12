# -*- coding: utf-8 -*-
""""Em quên" và "em không biết" phải là HAI câu khác nhau.

10/08/2026 đo trên máy thật: đặt dữ kiện ở lượt 1, lấp đầy 7 lượt không liên
quan, hỏi lại ở lượt 9 — AURA đáp "AURA chưa thể trả lời câu này một cách đáng
tin cậy."  Đúng là nó không trả lời được, nhưng câu ấy khiến Sếp tưởng AURA
dốt, trong khi sự thật là đoạn đó đã rơi khỏi cửa sổ trí nhớ.

Hai chuyện ấy dẫn tới hai hành động khác nhau: một bên đi hỏi chỗ khác, một bên
chỉ cần NHẮC LẠI một câu là xong.
"""
from __future__ import annotations

import asyncio
import uuid

from core.chat_contract import ChatRequest, ChatStatus
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.secret_guard import SecretContentGuard


class _BoTay:
    """Model trả rỗng — `ChatService` sẽ chốt là `cannot_answer`."""

    history_window = 24

    async def generate(self, request, *, history=(), sources=()):
        return ModelReply(text="", requires_web=False)


class _BoTayKhongKhaiTamNhin(_BoTay):
    history_window = 0


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


class _KhongTraMang:
    async def search(self, query):
        return ()


def _hoi(model, so_tin_trong_so: int):
    service = ChatService(
        model=model, store=_So(so_tin_trong_so), guard=SecretContentGuard(),
        web=_KhongTraMang(), timeout_s=30.0,
    )
    return asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web",
        text="Xe đạp của tôi màu gì?",
    )))


def test_so_dai_hon_tam_nhin_thi_NOI_RO_LA_QUEN():
    ket_qua = _hoi(_BoTay(), so_tin_trong_so=40)     # 40 tin > tầm nhìn 24
    assert ket_qua.status is ChatStatus.CANNOT_ANSWER
    assert "QUÊN" in ket_qua.text
    assert "nhắc lại" in ket_qua.text.lower(), "phải bảo Sếp làm gì tiếp"


def test_chua_rot_tin_nao_thi_DUNG_do_cho_tri_nho():
    """Đổ cho trí nhớ khi chưa mất gì cũng là một kiểu nói dối."""
    ket_qua = _hoi(_BoTay(), so_tin_trong_so=4)      # 4 tin < tầm nhìn 24
    assert ket_qua.status is ChatStatus.CANNOT_ANSWER
    assert "QUÊN" not in ket_qua.text


def test_cong_khong_khai_tam_nhin_thi_giu_cau_mac_dinh():
    """Không biết tầm nhìn thì im, đừng đoán bừa là đã quên."""
    ket_qua = _hoi(_BoTayKhongKhaiTamNhin(), so_tin_trong_so=40)
    assert "QUÊN" not in ket_qua.text


def test_hai_cong_that_deu_khai_duoc_tam_nhin():
    """Cắm cơ chế mà cổng thật không khai thì cơ chế nằm không."""
    from core.local_first_gateway import (
        LocalFirstGateway, OllamaConfig, OllamaGateway,
    )

    local = OllamaGateway(OllamaConfig(), client=object())
    assert local.history_window == 24
    assert LocalFirstGateway(local=local).history_window == 24
