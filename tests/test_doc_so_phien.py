# -*- coding: utf-8 -*-
"""Hỏi "câu thứ mấy" là việc ĐẾM, không phải việc đoán.

10/08/2026, phiên thật của Sếp:
    1. Viết hàm Python đảo ngược chuỗi...
    2. giá vàng hôm nay là bao nhiêu
    3. vậy AI là gì
    4. "câu hỏi thứ 2 tôi hỏi bạn trong phiên chat này là hỏi về cái gì"

AURA đáp: "Câu hỏi thứ hai của bạn yêu cầu định nghĩa AI..."  Đó là câu THỨ BA.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest
from core.chat_service import ChatMessage
from core.doc_so_phien import tra_so

PHIEN_THAT = (
    ChatMessage(role="user", content="Viết hàm Python đảo ngược chuỗi."),
    ChatMessage(role="aura", content="def reverse_string(s): return s[::-1]"),
    ChatMessage(role="user", content="giá vàng hôm nay là bao nhiêu"),
    ChatMessage(role="aura", content="Em tra được 4 nguồn nhưng chưa dám chốt."),
    ChatMessage(role="user", content="vậy AI là gì"),
    ChatMessage(role="aura", content="AI là lĩnh vực khoa học máy tính..."),
)


def test_dung_cau_AURA_da_tra_loi_SAI():
    câu = tra_so("câu hỏi thứ 2 tôi hỏi bạn trong phiên chat này là hỏi về cái gì",
                 PHIEN_THAT)
    assert câu is not None
    assert "giá vàng hôm nay là bao nhiêu" in câu
    assert "AI là gì" not in câu, "đó là câu thứ BA"


@pytest.mark.parametrize("hoi,mong_doi", [
    ("câu hỏi đầu tiên của tôi là gì?", "Viết hàm Python"),
    ("câu thứ nhất tôi hỏi gì", "Viết hàm Python"),
    ("câu hỏi thứ ba là gì", "vậy AI là gì"),
    ("cau hoi thu 2 la gi", "giá vàng"),          # gõ không dấu
])
def test_dem_dung_nhieu_kieu_hoi(hoi, mong_doi):
    câu = tra_so(hoi, PHIEN_THAT)
    assert câu is not None and mong_doi in câu


def test_dan_ro_la_NHAC_LAI_chu_khong_phai_TRA_LOI_LAI():
    """10/08/2026, phiên thật của Sếp — lỗi ở câu chữ TÔI viết, không ở model.

    Câu số 2 là "bạn là 1 AI hay 1 Agent".  Sếp hỏi "câu hỏi thứ 2 tôi hỏi bạn
    là gì", AURA đáp "Tôi là một mô hình ngôn ngữ lớn (AI)..." — nó TRẢ LỜI LẠI
    câu đó.  Dữ kiện đưa đúng, nhưng lời dặn cũ ("Dựa đúng vào câu này") đọc
    kiểu nào cũng ra "hãy trả lời câu này".
    """
    câu = tra_so("câu hỏi thứ 2 tôi hỏi bạn là gì", PHIEN_THAT)
    assert câu is not None
    assert "NHẮC LẠI" in câu
    assert "không trả lời nội dung của nó" in câu
    assert "XEM LẠI một lượt cũ" in câu


def test_hoi_qua_so_luot_thi_NOI_THANG_chu_dung_bia():
    câu = tra_so("câu hỏi thứ 9 là gì", PHIEN_THAT)
    assert câu is not None
    assert "mới hỏi 3 câu" in câu and "đừng bịa" in câu


@pytest.mark.parametrize("khong_hoi_ve_luot", [
    "Thủ đô Việt Nam là gì?",
    "Chào AURA",
    "giá vàng hôm nay là bao nhiêu",
])
def test_cau_thuong_thi_KHONG_chen_gi(khong_hoi_ve_luot):
    assert tra_so(khong_hoi_ve_luot, PHIEN_THAT) is None


def test_so_rong_thi_im():
    assert tra_so("câu hỏi thứ 2 là gì", ()) is None


def test_dem_tren_TOAN_BO_so_khong_phai_phan_model_nhin_thay():
    """Cửa sổ chỉ giữ 24 tin; đếm trên phần bị cắt thì "câu thứ 2" ra câu khác.

    Dựng 40 tin: câu hỏi thứ 2 nằm ở đầu sổ, ngoài tầm nhìn của model.
    """
    dai = [
        ChatMessage(role="user" if i % 2 == 0 else "aura",
                    content=f"câu số {i // 2 + 1}" if i % 2 == 0 else "vâng ạ")
        for i in range(40)
    ]
    câu = tra_so("câu hỏi thứ 2 là gì", dai)
    assert câu is not None and '"câu số 2"' in câu


def test_da_cam_vao_cong_local():
    """Máy trả lời THẲNG câu "câu thứ mấy" — KHÔNG gọi model.

    13/08/2026 đổi hành vi, có số: bản cũ đưa model một lời dặn "nhắc lại, đừng
    trả lời" rồi trông vào nó nghe lời. Chạy 5 lần trên một phiên có sẵn hai
    lượt đầy ngày tháng: ĐÚNG 1/5 — bốn lần AURA trả lời lại câu cũ.

    Đáp án được xác định hoàn toàn bởi sổ, nên không có việc gì cho model làm.
    Test này canh đúng chỗ đó: KHÔNG có lệnh gọi nào ra ngoài, và câu trả lời
    mang nguyên văn câu hỏi cũ.
    """
    from core.local_first_gateway import OllamaConfig, OllamaGateway

    goi = []

    class _Client:
        async def post(self, url, json=None):     # pragma: no cover — không được gọi
            goi.append(json)
            raise AssertionError("đã gọi model cho câu mà máy trả lời được")

    gate = OllamaGateway(OllamaConfig(), client=_Client())
    tra_loi = asyncio.run(gate.generate(
        ChatRequest(
            request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
            actor_id="owner:web", channel="web",
            text="câu hỏi thứ 2 tôi hỏi là gì",
        ),
        history=PHIEN_THAT,
    ))
    assert goi == [], "không được gọi model"
    assert "thứ 2" in tra_loi.text
    # Nguyên văn câu cũ phải có trong câu trả lời, không phải đáp án của nó.
    assert PHIEN_THAT[2].content in tra_loi.text
