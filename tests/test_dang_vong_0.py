# -*- coding: utf-8 -*-
"""Đăng tự động, vòng 0 — `CHOT:dang-vong-0` (14/09/2026).

Ghi vào MỘT bản nháp cố định trên Wattpad và Sáng Tác Việt, đọc lại từ trang. Ngưỡng
đăng ký trước khi viết kịch bản ghi.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:dang-vong-0` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "ghi nháp và đọc lại khớp, Wattpad, 10 lần": "≥ 9/10",
    "ghi nháp và đọc lại khớp, Sáng Tác Việt, 10 lần": "≥ 9/10",
    "thời gian mỗi lần ghi": "< 60 s",
    "lần đăng công khai ngoài ý muốn": "0",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:dang-vong-0 -->(.*?)<!-- /CHOT:dang-vong-0 -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:dang-vong-0"
    return m.group(1)


def test_BON_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
