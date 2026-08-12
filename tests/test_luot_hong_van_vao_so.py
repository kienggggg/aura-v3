# -*- coding: utf-8 -*-
"""Màn hình và trí nhớ của AURA phải kể CÙNG MỘT câu chuyện.

10/08/2026 Sếp hỏi "câu hỏi thứ 2 tôi hỏi trong phiên này là gì", AURA trả lời
"vậy AI là gì" trong khi trên màn hình câu thứ 2 rõ ràng là "giá vàng hôm nay".

Truy ra thì AURA **không sai theo trí nhớ của nó**: lượt "giá vàng" kết thúc ở
`cannot_answer`, và `persist=True` chỉ có ở đúng ĐƯỜNG THÀNH CÔNG.  Mọi lượt
hỏng bốc hơi khỏi sổ nhưng vẫn nằm trên màn hình.

Đây là lỗi nặng hơn cả việc đếm sai: hai bên nói chuyện với hai bản ghi khác
nhau, và không ai biết.

Ngoại lệ DUY NHẤT là lượt bị từ chối vì bí mật — cổng bí mật đã hứa với Sếp
"em không ghi nó vào nhật ký hội thoại", và lời hứa đó thắng.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, ChatStatus
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.secret_guard import SecretContentGuard


class _So:
    def __init__(self) -> None:
        self.da_ghi: list[tuple[str, str]] = []

    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        self.da_ghi.append((request.text, result.text))


class _KhongTraMang:
    async def search(self, query):
        return ()


class _Model:
    history_window = 24

    def __init__(self, reply=None, loi=None) -> None:
        self._reply = reply
        self._loi = loi

    async def generate(self, request, *, history=(), sources=()):
        if self._loi:
            raise self._loi
        return self._reply


def _hoi(model, text="Giải thích decorator trong Python"):
    # Câu mặc định KHÔNG được chứa từ khoá tra mạng.  Bản đầu tôi dùng "giá
    # vàng hôm nay" cho mọi ca, và luật tra mạng nổ trước khi tới model nên hai
    # test đo nhầm `web_unavailable` thay vì thứ định đo.
    so = _So()
    service = ChatService(
        model=model, store=so, guard=SecretContentGuard(),
        web=_KhongTraMang(), timeout_s=30.0,
    )
    ket_qua = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text=text,
    )))
    return ket_qua, so


def test_luot_CANNOT_ANSWER_van_phai_vao_so():
    """Đúng lượt đã bốc hơi trong phiên của Sếp."""
    ket_qua, so = _hoi(_Model(reply=ModelReply(text="", requires_web=False)))
    assert ket_qua.status is ChatStatus.CANNOT_ANSWER
    assert len(so.da_ghi) == 1, "lượt hỏng vừa bốc hơi khỏi sổ"
    assert so.da_ghi[0][0] == "Giải thích decorator trong Python"


def test_luot_WEB_UNAVAILABLE_van_phai_vao_so():
    ket_qua, so = _hoi(
        _Model(reply=ModelReply(text="[[AURA_REQUIRES_WEB]]", requires_web=True)),
        text="tin tức mới nhất về AI",
    )
    assert ket_qua.status is ChatStatus.WEB_UNAVAILABLE
    assert len(so.da_ghi) == 1


def test_luot_QUA_GIO_van_phai_vao_so():
    """Lỗ hổng cuối, vá 10/08/2026.

    Chỗ ghi sổ dùng chính `deadline` — mà `deadline` vừa hết, nên bản đầu tôi
    để quá giờ KHÔNG vào sổ cho an toàn.  Nay cấp một khoản ân hạn riêng có
    trần (`_AN_HAN_GHI_SO`) chỉ để ghi lại thứ Sếp đã nhìn thấy.
    """
    class _ChamQua:
        history_window = 24

        async def generate(self, request, *, history=(), sources=()):
            await asyncio.sleep(5)
            return ModelReply(text="về muộn", requires_web=False)

    so = _So()
    service = ChatService(
        model=_ChamQua(), store=so, guard=SecretContentGuard(),
        web=_KhongTraMang(), timeout_s=0.05,
    )
    ket_qua = asyncio.run(service.reply(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Giải thích decorator",
    )))
    assert ket_qua.status is ChatStatus.TIMEOUT
    assert len(so.da_ghi) == 1, "lượt quá giờ vẫn bốc hơi khỏi sổ"
    assert so.da_ghi[0][0] == "Giải thích decorator"
    assert "về muộn" not in so.da_ghi[0][1], "kết quả về muộn lọt vào sổ"


def test_luot_LOI_BO_NAO_thi_CO_Y_khong_vao_so():
    """Ranh giới cuối cùng: ghi cái AURA ĐÃ NÓI, không ghi cái máy hỏng.

    `backend_error` nghĩa là bộ não gãy trước khi AURA kịp nói với Sếp điều gì.
    Khác `timeout`: quá giờ thì Sếp vẫn thấy một lượt hoàn chỉnh trên màn hình.
    """
    from core.chat_runtime import ModelGatewayError

    ket_qua, so = _hoi(_Model(loi=ModelGatewayError("ollama chết")))
    assert ket_qua.status is ChatStatus.BACKEND_ERROR
    assert so.da_ghi == []


def test_luot_TU_CHOI_VI_BI_MAT_thi_TUYET_DOI_khong_vao_so():
    """Ngoại lệ duy nhất, và nó thắng mọi lý lẽ về tính nhất quán."""
    ket_qua, so = _hoi(
        _Model(reply=ModelReply(text="không tới đây", requires_web=False)),
        text="mật khẩu wifi nhà mình là gì",
    )
    assert ket_qua.status is ChatStatus.REJECTED
    assert so.da_ghi == [], "vừa ghi một câu hỏi bí mật vào nhật ký"


def test_luot_thanh_cong_van_vao_so_nhu_cu():
    ket_qua, so = _hoi(
        _Model(reply=ModelReply(text="Hà Nội.", requires_web=False)),
        text="Thủ đô Việt Nam là gì?",
    )
    assert ket_qua.status is ChatStatus.OK
    assert so.da_ghi == [("Thủ đô Việt Nam là gì?", "Hà Nội.")]
