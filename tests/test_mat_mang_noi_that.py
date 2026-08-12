# -*- coding: utf-8 -*-
"""Mất mạng KHÁC nguồn xấu — và Sếp phải phân biệt được.

11/08/2026 Sếp mất mạng, hỏi AURA hai câu. Câu tra mạng trả về:

    "Câu này cần tra nguồn mới, nhưng AURA chưa lấy đủ nguồn đáng tin cậy."

Câu đó nghe như NGUỒN XẤU. Sự thật là KHÔNG CÓ MẠNG. Một cái Sếp chờ được, một
cái Sếp phải đi cắm lại wifi — nói nhầm là để Sếp ngồi đợi một thứ không tự đến.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, ChatStatus
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.secret_guard import SecretContentGuard


class _So:
    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        return None


class _WebRong:
    async def search(self, query):
        return ()          # tra hụt: không nguồn nào


class _Model:
    history_window = 24

    async def generate(self, request, *, history=(), sources=()):
        return ModelReply(text="không tới đây", requires_web=False)


def _hoi(monkeypatch, *, co_mang: bool):
    monkeypatch.setattr("core.chat_service.mang_co_song", lambda *a, **k: co_mang)
    service = ChatService(
        model=_Model(), store=_So(), guard=SecretContentGuard(),
        web=_WebRong(), timeout_s=30.0,
    )
    return asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web",
        text="giá vàng hôm nay bao nhiêu",
    )))


def test_MAT_MANG_thi_noi_la_mat_mang(monkeypatch):
    ket_qua = _hoi(monkeypatch, co_mang=False)
    assert ket_qua.status is ChatStatus.WEB_UNAVAILABLE
    assert "KHÔNG có mạng" in ket_qua.text
    assert "wifi" in ket_qua.text.lower(), "phải nói Sếp cần làm gì"
    assert "nguồn kém" in ket_qua.text, "phải nói rõ KHÔNG phải lỗi nguồn"


def test_CO_MANG_ma_tra_hut_thi_giu_cau_cu(monkeypatch):
    """Có mạng mà không ra nguồn thì đúng là chuyện nguồn — đừng đổ cho wifi."""
    ket_qua = _hoi(monkeypatch, co_mang=True)
    assert ket_qua.status is ChatStatus.WEB_UNAVAILABLE
    assert "KHÔNG có mạng" not in ket_qua.text
    assert "nguồn" in ket_qua.text


def test_chi_hoi_mang_KHI_DA_tra_hut(monkeypatch):
    """Dò mạng ở mọi lượt là bắt Sếp trả tiền cho một phép thử hiếm khi cần."""
    dem = {"lan": 0}

    def _dem(*a, **k):
        dem["lan"] += 1
        return True

    monkeypatch.setattr("core.chat_service.mang_co_song", _dem)

    class _TraLoiDuoc:
        history_window = 24

        async def generate(self, request, *, history=(), sources=()):
            return ModelReply(text="Hà Nội.", requires_web=False)

    service = ChatService(
        model=_TraLoiDuoc(), store=_So(), guard=SecretContentGuard(),
        web=_WebRong(), timeout_s=30.0,
    )
    asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Thủ đô Việt Nam là gì?",
    )))
    assert dem["lan"] == 0, "lượt bình thường không được đụng tới mạng"


def test_ham_do_mang_khong_gui_du_lieu_gi():
    """Dò bằng ổ cắm TCP rồi đóng — không byte nào của Sếp đi ra ngoài."""
    import inspect

    from core import web_search

    nguon = inspect.getsource(web_search.mang_co_song)
    assert "socket.create_connection" in nguon
    for cam in ("requests", "urlopen", "httpx", "send", "sendall"):
        assert cam not in nguon, f"phép dò mạng đang gửi dữ liệu: {cam}"
