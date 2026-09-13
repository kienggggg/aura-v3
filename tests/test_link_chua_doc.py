# -*- coding: utf-8 -*-
"""Máy nói cho model biết AURA không mở được trang — `CHOT:link-chua-doc` (13/09/2026).

Sau khi bộ che tha link bài báo (`CHOT:url-dau-vao`), "tóm tắt bài này: <link>"
bị model BỊA 2/3 lượt, và lượt thật gọi báo Nhân Dân là "bài đăng Facebook".
Máy đặt một dữ kiện cạnh câu hỏi khi câu có link và lượt ấy không có nguồn.
"""
from __future__ import annotations

import re
import uuid

import pytest

from core.chat_contract import ChatRequest, SourceCitation
from core.local_first_gateway import OllamaConfig, OllamaGateway
from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:link-chua-doc` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "bịa, \"tóm tắt\" có ghi chú, 4 lượt": "0/4",
    "nhận chưa đọc được trang, \"tóm tắt\" có ghi chú": "≥ 3/4",
    "\"báo nào\" có ghi chú nêu đúng Nhân Dân": "2/2",
    "lời nhắc câu không có link": "y hệt từng byte",
}
# Chép TAY đầu dữ kiện máy: đổi chữ trong mã mà quên bài này thì đỏ.
DAU_GHI_CHU = "MÁY GHI SẴN — AURA KHÔNG mở được trang web"
LINK = "https://nhandan.vn/dan-so-trung-binh-cua-viet-nam-nam-2025-dat-1023-trieu-nguoi-post934760.html"


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:link-chua-doc -->(.*?)<!-- /CHOT:link-chua-doc -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:link-chua-doc"
    return m.group(1)


def _luot_nguoi_dung(text: str, sources=()) -> str:
    """CHỈ lượt của người dùng: lời dặn hệ thống có giờ thật, so nó là xanh theo lịch."""
    return OllamaGateway(OllamaConfig())._messages(
        ChatRequest(request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
                    actor_id="owner", channel="test", text=text),
        history=(), sources=sources)[-1]["content"]


def test_BON_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


@pytest.mark.parametrize("cau", [
    "giá vàng hôm nay",
    "closure trong JavaScript là gì",
    # Chữ "https" mà không có "://": không phải link.
    "trang https là gì",
])
def test_CAU_KHONG_CO_LINK_luot_nguoi_dung_y_het(cau):
    assert _luot_nguoi_dung(cau) == cau


@pytest.mark.parametrize("cau", [f"tóm tắt bài này: {LINK}", f"{LINK} nói gì vậy?"])
def test_CAU_CO_LINK_khong_nguon_co_DUNG_MOT_ghi_chu_sau_cau_hoi(cau):
    nd = _luot_nguoi_dung(cau)
    assert nd.startswith(cau + "\n\n"), "dữ kiện máy phải đứng SAU câu hỏi"
    assert nd.count(DAU_GHI_CHU) == 1


def test_CAU_CO_LINK_co_nguon_KHONG_ghi_chu():
    nguon = tuple(SourceCitation(title=f"Nguồn {i}", url=f"https://vi.du/{i}",
                                 retrieved_at="2026-09-13T05:00:00+00:00", supports=f"Dữ kiện {i}")
                  for i in (1, 2))
    assert DAU_GHI_CHU not in _luot_nguoi_dung(f"tóm tắt bài này: {LINK}", nguon)
