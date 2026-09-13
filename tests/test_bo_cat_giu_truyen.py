# -*- coding: utf-8 -*-
"""Bộ cắt không được xoá truyện — `CHOT:bo-cat-giu-truyen` (13/09/2026).

Lời nhắc xin 320 từ, model viết trung vị 460; bộ cắt bỏ trung vị 48 % số câu,
cách một câu bỏ một câu, bắt đầu từ câu thứ 2 — đúng câu đặt nhân vật. Bài này
giữ ngưỡng đúng như lúc đăng ký.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:bo-cat-giu-truyen` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "tỉ lệ câu bị cắt, trung vị, lời nhắc C + bộ cắt mới": "≤ 0,15",
    "lọt cửa một lần sinh, 15 lượt": "C + cắt mới ≥ 0 + cắt cũ − 2",
    "bộ cắt mới bỏ 2 câu đầu hoặc 2 câu cuối": "0 lần",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:bo-cat-giu-truyen -->(.*?)<!-- /CHOT:bo-cat-giu-truyen -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:bo-cat-giu-truyen"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
