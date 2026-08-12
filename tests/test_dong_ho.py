# -*- coding: utf-8 -*-
"""AURA phải biết hôm nay là ngày nào — và phải biết ở CẢ HAI cổng.

10/08/2026, hỏi "Hôm nay là thứ mấy trong tuần theo lịch Việt Nam?":

    ĐÁP : Hôm nay là Thứ Ba ngày 21 tháng Bảy năm 2026 [[1]].

Sai 20 ngày, nói chắc nịch, lại còn trích nguồn.  Model không có đồng hồ.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

import pytest

from core.chat_contract import ChatRequest
from core.dong_ho import cau_gio
from core.local_first_gateway import OllamaConfig, OllamaGateway


def test_cau_gio_noi_dung_thu_va_ngay():
    # 10/08/2026 là Thứ Hai.
    câu = cau_gio(datetime(2026, 8, 10, 15, 4))
    assert "Thứ Hai" in câu
    assert "ngày 10 tháng 8 năm 2026" in câu
    assert "15:04" in câu


@pytest.mark.parametrize("ngay,thu", [
    (datetime(2026, 8, 10), "Thứ Hai"),
    (datetime(2026, 8, 15), "Thứ Bảy"),
    (datetime(2026, 8, 16), "Chủ Nhật"),
])
def test_thu_trong_tuan_dung_kieu_Viet(ngay, thu):
    """Python đếm Thứ Hai = 0; đếm nhầm một nấc là sai suốt cả tuần."""
    assert thu in cau_gio(ngay)


def test_cau_gio_cam_doan_mo_va_cam_tra_mang_de_biet_ngay():
    câu = cau_gio(datetime(2026, 8, 10))
    assert "đừng đoán" in câu
    assert "đừng tra mạng" in câu


def test_cong_LOCAL_gui_gio_len_model():
    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "Hôm nay là Thứ Hai."}}

            return _Response()

    gate = OllamaGateway(OllamaConfig(), client=_Client())
    asyncio.run(gate.generate(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="Hôm nay thứ mấy?",
    )))
    system = sent["json"]["messages"][0]["content"]
    assert "BÂY GIỜ là" in system


def test_cong_CLOUD_cung_gui_gio():
    """Thầy mà không biết ngày thì lượt nào mượn thầy là lượt đó sai ngày."""
    from core.chat_runtime import OpenAICompatibleConfig, OpenAICompatibleModelGateway

    gate = OpenAICompatibleModelGateway(
        OpenAICompatibleConfig(
            base_url="https://example.com/v1", api_key="k", model="m",
        )
    )
    messages = gate._messages(
        ChatRequest(
            request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
            actor_id="owner:web", channel="web", text="Hôm nay thứ mấy?",
        ),
        history=(), sources=(),
    )
    assert "BÂY GIỜ là" in messages[0]["content"]
