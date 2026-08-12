"""Hết hạn mức phải nói là hết hạn mức, không nói là "bộ não hỏng".

10/08/2026: đo thật 5 câu qua lõi Chat v1 — 2 câu trả `backend_error` kèm câu chữ
"AURA đang gặp lỗi ở bộ não. Vui lòng thử lại sau."  Gọi thẳng API thì ra
``HTTP 429 — You exceeded your current quota``.

Mã không sai; hạn mức hết.  Nhưng Sếp đọc câu đó sẽ đi sửa thứ không hỏng — đúng
bài toán im lặng cũ trong bộ áo mới: hôm qua AURA câm nên tưởng nó điếc, hôm nay
nó kêu "lỗi bộ não" nên tưởng nó hỏng.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, ChatStatus
from core.chat_runtime import ModelGatewayError, ModelQuotaExceeded
from core.chat_service import ChatMessage, ChatService, ModelReply


class _QuotaModel:
    async def generate(self, request, *, history=(), sources=()):
        raise ModelQuotaExceeded("cloud model refused: HTTP 429")


class _PlainBrokenModel:
    async def generate(self, request, *, history=(), sources=()):
        raise ModelGatewayError("cloud model network request failed")


class _Store:
    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        return None


def _ask(model) -> object:
    """Dùng bộ che THẬT: bộ che giả tự viết thiếu phương thức thì AttributeError
    của chính nó sẽ giả dạng thành 'lỗi bộ não' và làm test đo nhầm thứ."""
    from core.secret_guard import SecretContentGuard

    service = ChatService(
        model=model, store=_Store(), guard=SecretContentGuard(), web=None
    )
    request = ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="chào AURA",
    )
    return asyncio.run(service.reply(request))


def test_het_han_muc_noi_dung_ly_do():
    result = _ask(_QuotaModel())
    assert result.status == ChatStatus.BACKEND_ERROR
    low = result.text.lower()
    assert "hạn mức" in low, f"không nói ra lý do thật: {result.text!r}"
    assert "bộ não" not in low, "vẫn đổ tội cho bộ não trong khi bộ não vô can"


def test_bao_cho_Sep_biet_phai_lam_gi():
    text = _ask(_QuotaModel()).text.lower()
    assert "không hỏng" in text or "khoá" in text or "chờ" in text


def test_khong_lo_nha_cung_cap_hay_dia_chi():
    """Câu an toàn là câu KHÔNG kèm URL, khoá, tên máy chủ."""
    text = _ask(_QuotaModel()).text.lower()
    for leak in ("http", "://", "googleapis", "gemini", "api_key", "bearer", "sk-"):
        assert leak not in text, f"lộ chi tiết nhà cung cấp: {leak}"


def test_loi_thuong_van_giu_cau_chung():
    """Chỉ hết hạn mức mới có câu riêng; lỗi khác không được đoán bừa lý do."""
    result = _ask(_PlainBrokenModel())
    assert result.status == ChatStatus.BACKEND_ERROR
    assert "hạn mức" not in result.text.lower()
    assert result.text.strip()


def test_cong_model_phan_biet_429_voi_loi_khac():
    assert issubclass(ModelQuotaExceeded, ModelGatewayError)
    assert ModelQuotaExceeded("x").user_message
    assert ModelGatewayError("x").user_message is None
