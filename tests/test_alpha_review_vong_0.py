# -*- coding: utf-8 -*-
"""Alpha review, vòng 0 — `CHOT:alpha-review-vong-0` (15/09/2026): video phân tích Skibidi Toilet.

Ngưỡng đăng ký trước khi viết dòng mã nào.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:alpha-review-vong-0` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "câu kịch bản có đoạn trích nguyên văn từ 8 từ trở lên, máy tìm thấy trong nguồn ghim": "100%",
    "con số trên video có mặt trong nguồn ghim": "100%",
    "câu tiếng Việt nói đúng như đoạn trích, em đọc lại từng câu": "100%",
    "khung hình, âm thanh hay nhạc lấy từ phim": "0",
    "dựng xong một video trên máy này": "< 15 phút",
    "Sếp xem xong: muốn xem hết": "có",
}


def _khoi() -> str:
    m = re.search(r"<!-- CHOT:alpha-review-vong-0 -->(.*?)<!-- /CHOT:alpha-review-vong-0 -->",
                  (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:alpha-review-vong-0"
    return m.group(1)


def test_SAU_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
