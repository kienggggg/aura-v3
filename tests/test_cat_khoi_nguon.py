# -*- coding: utf-8 -*-
"""Khối nguồn đưa model — `CHOT:cat-khoi-nguon` (13/09/2026).

Cắt khối nguồn (bỏ dòng URL + đoạn trích 400 -> 250 ký tự) rút khúc model ĐỌC
0,78 lần, và ĐẠT cả ba ngưỡng viết trước. Nhưng đọc tay lộ ra thước thiếu một
chiều — độ ĐỦ: giá mua vào 143 triệu, chỉ nằm sau mốc cắt, bản đầy đủ nhắc 2/2,
bản cắt 0/2. Nên KHÔNG đưa vào; quyết định là của Sếp.

Bài này ghim khối nguồn hiện nay chừng nào khối đặc tả còn ghi CHỜ SẾP. Đổi định
dạng khối nguồn thì phải sửa bài này VÀ khối đặc tả cùng lúc — tức là phải cố ý.
"""
from __future__ import annotations

import re
import uuid

from core.chat_contract import ChatRequest, SourceCitation
from core.local_first_gateway import OllamaConfig, OllamaGateway
from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:cat-khoi-nguon`.
DAC_TA_DOC = "× 0,85"
DAC_TA_TRUNG = "≥ số trúng của V0 − 1"
DAC_TA_NHAY = "V12 trúng ≥ V0 trúng"


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:cat-khoi-nguon -->(.*?)<!-- /CHOT:cat-khoi-nguon -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:cat-khoi-nguon"
    return m.group(1)


def test_NGUONG_khop_khoi_dac_ta():
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M))
    assert DAC_TA_DOC in hang.get("khúc đọc V12 so với V0", "")
    assert DAC_TA_TRUNG in hang.get("trúng thước V12, 18 lượt", "")
    assert DAC_TA_NHAY in hang.get("câu nhạy lãi suất 12 tháng", "")


def test_KHOI_NGUON_giu_nguyen_khi_quyet_dinh_con_CHO_SEP():
    assert "**CHỜ SẾP**" in _khoi(), (
        "khối đặc tả không còn ghi CHỜ SẾP — sửa bài này theo quyết định mới")
    url = "https://vi.du/gia-vang-hom-nay-13-9-sjc-146-trieu"
    trich = ("Giá vàng SJC bán ra 146 triệu, mua vào 143 triệu đồng/lượng. " * 8)[:400]
    tin = OllamaGateway(OllamaConfig())._messages(
        ChatRequest(request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
                    actor_id="owner", channel="test", text="giá vàng hôm nay"),
        history=(),
        sources=(SourceCitation(title="Giá vàng hôm nay", url=url,
                                retrieved_at="2026-09-13T05:00:00+00:00",
                                supports=trich),))
    nguoi_dung = tin[-1]["content"]
    assert f"\n{url}\n" in nguoi_dung, "dòng URL biến mất — Sếp chưa duyệt cắt nguồn"
    assert trich in nguoi_dung, "đoạn trích bị cắt — Sếp chưa duyệt cắt nguồn"
