# -*- coding: utf-8 -*-
"""Đăng tự động, vòng 1 — `CHOT:dang-vong-1` (15/09/2026): lớp tự thích nghi khi giao diện đổi.

Ngưỡng đăng ký trước khi viết mã. Hàng "bấm nhầm" là hàng loại thẳng.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:dang-vong-1` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "bộ tìm của kịch bản gãy dưới giao diện giả lập, 10 lần": "10/10",
    "nhánh A lưu nháp được và đọc lại khớp, 10 lần": "≥ 9/10",
    "nhánh B lưu nháp được và đọc lại khớp, 10 lần": "≥ 7/10",
    "cú bấm vào nút khác nút định bấm": "0",
    "lần đăng công khai ngoài ý muốn": "0",
}


def _khoi() -> str:
    m = re.search(r"<!-- CHOT:dang-vong-1 -->(.*?)<!-- /CHOT:dang-vong-1 -->",
                  (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:dang-vong-1"
    return m.group(1)


def test_NAM_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
