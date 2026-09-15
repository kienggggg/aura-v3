# -*- coding: utf-8 -*-
"""Robot, hướng A — `CHOT:robot-nghiem-thu` (15/09/2026): nghiệm thu lại trên xe thật với bản vá.

Ngưỡng đăng ký trước khi nạp firmware, trước khi cài APK, trước khi đo lượt nào.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:robot-nghiem-thu` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "chip chạy đúng firmware mới, đọc dòng READY": "1/1",
    "Vivo chạy đúng APK mới, đọc versionCode": "1/1",
    "18 câu nói vào app Vivo: lệnh tới ESP32 đúng như muốn": "18/18",
    "12 câu chat AURA v2 cộng nút dừng chay_xe: lệnh tới ESP32 đúng như muốn": "13/13",
    "nút DỪNG trên app khi xe đang chạy": "3/3",
    "thả tay khỏi nút giữ": "3/3",
    "tắt app Vivo giữa lúc tự tuần tra: Serial ra MOTION:STOPPED trong 2,5 s": "3/3",
    "vật cản 10–15 cm, giữ nút tiến và bật tự tuần tra: 0 dòng MOTION:FORWARD": "6/6",
}


def _khoi() -> str:
    m = re.search(r"<!-- CHOT:robot-nghiem-thu -->(.*?)<!-- /CHOT:robot-nghiem-thu -->",
                  (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:robot-nghiem-thu"
    return m.group(1)


def test_TAM_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
