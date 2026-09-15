# -*- coding: utf-8 -*-
"""Alpha review, vòng 1 — `CHOT:alpha-giong-vong-1` (15/09/2026): đổi giọng, 3 TTS tải về so với OneCore An.

Ngưỡng đăng ký trước khi đo giây nào.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:alpha-giong-vong-1` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "giây máy tạo giọng chia giây âm thanh, 10 câu video, CPU máy này": "≤ 2,0",
    "tỉ lệ lỗi chữ khi faster-whisper small nghe lại 10 câu": "≤ OneCore An + 5 điểm %",
    "tên tiếng Anh faster-whisper nghe ra đúng chính tả": "≥ 10/13",
    "ca đối chứng OneCore An, hàng tên tiếng Anh": "< 10/13",
    "Sếp nghe mù 3 câu đầu, 4 giọng A–D xáo thứ tự": "xếp đủ 4 hạng",
    "Sếp xem lại video Skibidi đọc bằng giọng xếp đầu: muốn xem hết": "có",
}


def _khoi() -> str:
    m = re.search(r"<!-- CHOT:alpha-giong-vong-1 -->(.*?)<!-- /CHOT:alpha-giong-vong-1 -->",
                  (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:alpha-giong-vong-1"
    return m.group(1)


def test_SAU_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
