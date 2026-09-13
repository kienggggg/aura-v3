# -*- coding: utf-8 -*-
"""Khối nguồn đưa model — `CHOT:cat-khoi-nguon` (13/09/2026).

Cắt khối nguồn (bỏ dòng URL + đoạn trích 400 -> 250 ký tự) rút khúc model ĐỌC
0,78 lần, và ĐẠT cả ba ngưỡng viết trước. Nhưng đọc tay lộ ra thước thiếu một
chiều — độ ĐỦ: giá mua vào 143 triệu, chỉ nằm sau mốc cắt, bản đầy đủ nhắc 2/2,
bản cắt 0/2. Nên KHÔNG đưa vào.

Sếp chọn (b) — chỉ bỏ dòng URL — và nó được đo riêng ở `CHOT:bo-dong-url`. Cửa
ghim khối nguồn (không URL, đoạn trích ĐỦ 400 ký tự) nằm ở
`tests/test_bo_dong_url.py`; bài này chỉ còn giữ ngưỡng của lần đo V12.
"""
from __future__ import annotations

import re

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
