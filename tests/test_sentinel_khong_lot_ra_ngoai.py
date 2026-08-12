# -*- coding: utf-8 -*-
"""Máy móc trong bụng KHÔNG được lọt ra mặt tiền.

10/08/2026, câu thật của Sếp gõ vào màn hình chat:

    HỎI : Tỷ giá USD sang VND hiện nay bao nhiêu?
    ĐÁP : [[AURA_REQUIRES_WEB]]          <- status "ok", 50,9 giây

`ChatService` tra mạng xong, đưa nguồn cho model, model trả lại đúng cái cờ nội
bộ lần nữa — và cờ đó được gán nhãn "ok" rồi in ra cho người đọc.
"""
from __future__ import annotations

import asyncio
import uuid

from core.chat_contract import ChatRequest, ChatStatus, SourceCitation
from core.chat_service import ChatMessage, ChatService, ModelReply


class _LuonDoiTraMang:
    """Model bướng: đưa bao nhiêu nguồn cũng vẫn đòi tra tiếp."""

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, request, *, history=(), sources=()):
        self.calls += 1
        return ModelReply(text="[[AURA_REQUIRES_WEB]]", requires_web=True)


class _CoNguon:
    async def search(self, query):
        return (
            SourceCitation(
                title="Tỷ giá hôm nay",
                url="https://example.com/ty-gia",
                retrieved_at="2026-08-10T12:00:00+00:00",
                supports="1 USD = 25.000 VND",
            ),
        )


class _So:
    """Sổ phiên rỗng — đúng hợp đồng `SessionStore` (async, hai method)."""

    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        return None


def _hoi(text: str):
    # Dùng KHIÊN THẬT.  Khiên giả thiếu method thì `AttributeError` của chính nó
    # nổi lên thành `backend_error` và giả dạng lỗi sản phẩm — tôi đã sập đúng
    # bẫy này một lần rồi, và lần đó suýt đi sửa nhầm chỗ.
    from core.secret_guard import SecretContentGuard

    service = ChatService(
        model=_LuonDoiTraMang(),
        store=_So(),
        guard=SecretContentGuard(),
        web=_CoNguon(),
        timeout_s=30.0,
    )
    return asyncio.run(
        service.reply(
            ChatRequest(
                request_id=str(uuid.uuid4()),
                session_id=str(uuid.uuid4()),
                actor_id="owner:web",
                channel="web",
                text=text,
            )
        )
    )


def test_co_noi_bo_khong_bao_gio_thanh_cau_tra_loi():
    result = _hoi("Tỷ giá USD sang VND hiện nay bao nhiêu?")
    assert "AURA_REQUIRES_WEB" not in (result.text or "")
    assert "[[" not in (result.text or "")


def test_bo_tay_thi_KHONG_bao_gio_gan_nhan_ok():
    """Trả cờ nội bộ mà gán "ok" là nói dối hai lần: sai nhãn và sai nội dung.

    Cố ý chỉ khẳng định "không phải OK" thay vì đòi đúng một mã: khi model bó
    tay, `cannot_answer` và `web_unavailable` đều là câu trả lời trung thực —
    thứ KHÔNG được phép là `ok`.  Khoá cứng một mã ở đây sẽ biến bài test thành
    bản chụp cách hiện thực chạy hôm nay, đúng thói quen mà v3 đang bỏ.
    """
    result = _hoi("Tỷ giá USD sang VND hiện nay bao nhiêu?")
    assert result.status is not ChatStatus.OK
    assert result.status in (
        ChatStatus.CANNOT_ANSWER, ChatStatus.WEB_UNAVAILABLE,
    )


def test_adapter_bat_ky_tra_prose_kem_co_cung_bi_chan_o_cua_ra():
    """Không phụ thuộc adapter cloud/local có nhớ tự gỡ cờ hay không."""

    class _AdapterCu:
        async def generate(self, request, *, history=(), sources=()):
            return ModelReply(
                text="Đây là phần trả lời vẫn dùng được. [[AURA_REQUIRES_WEB]]",
                requires_web=False,
            )

    from core.secret_guard import SecretContentGuard

    service = ChatService(
        model=_AdapterCu(), store=_So(), guard=SecretContentGuard(), timeout_s=30.0,
    )
    result = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Giải thích một khái niệm ổn định.",
    )))
    assert result.status is ChatStatus.OK
    assert result.text == "Đây là phần trả lời vẫn dùng được."
    assert "AURA_REQUIRES_WEB" not in result.text


def test_adapter_bat_ky_tra_moi_co_khong_duoc_gan_nhan_ok():
    class _AdapterCu:
        async def generate(self, request, *, history=(), sources=()):
            return ModelReply(text="[[AURA_REQUIRES_WEB]]", requires_web=False)

    from core.secret_guard import SecretContentGuard

    service = ChatService(
        model=_AdapterCu(), store=_So(), guard=SecretContentGuard(), timeout_s=30.0,
    )
    result = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Giải thích một khái niệm ổn định.",
    )))
    assert result.status is ChatStatus.CANNOT_ANSWER
    assert "AURA_REQUIRES_WEB" not in result.text
