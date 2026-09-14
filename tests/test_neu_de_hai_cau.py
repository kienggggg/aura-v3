# -*- coding: utf-8 -*-
"""Cửa nêu đề nới sang câu 1–2 — `CHOT:neu-de-hai-cau` (14/09/2026).

53/60 bản gần nhất mở câu 1 bằng đúng nguyên văn đề, vì lời nhắc ép "dùng lại chính
những chữ đó trong câu mở". Phép thử đăng ký trước; mã sản phẩm CHƯA đổi.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:neu-de-hai-cau` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "lọt cửa một lần sinh, 15 lượt mỗi nhánh": "N ≥ 0 − 2",
    "câu 1 bắt đầu bằng nguyên văn đề, 15 lượt mỗi nhánh": "N ≤ một nửa của nhánh 0",
    "Sếp chấm mù ba câu đầu, 3 cặp": "N hơn ở ≥ 2/3",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:neu-de-hai-cau -->(.*?)<!-- /CHOT:neu-de-hai-cau -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:neu-de-hai-cau"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
