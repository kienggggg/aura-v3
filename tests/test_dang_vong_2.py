# -*- coding: utf-8 -*-
"""Đăng tự động, vòng 2 — `CHOT:dang-vong-2` (14/09/2026).

Kịch bản ĐẠT của phòng viết thành chương nháp trong một truyện tuyển tập trên Wattpad.
Ngưỡng đăng ký trước khi viết mã.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:dang-vong-2` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "kịch bản thật của phòng viết thành chương nháp, đọc lại khớp, 5 truyện": "5/5",
    "chương đăng trùng khi chạy hàng chờ lần hai": "0",
    "lần đăng công khai ngoài ý muốn": "0",
    "thời gian mỗi chương": "< 90 s",
    "truyện đã đăng của Sếp, so trước và sau": "giống hệt",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:dang-vong-2 -->(.*?)<!-- /CHOT:dang-vong-2 -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:dang-vong-2"
    return m.group(1)


def test_NAM_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
