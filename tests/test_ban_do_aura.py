# -*- coding: utf-8 -*-
"""Nhánh BẢN ĐỒ cho phòng AURA — `CHOT:ban-do-aura` (14/09/2026).

Sếp: "để AURA tự do phát huy nhưng đừng để nó đi lạc". Bản đồ viết 13/09 trước
mọi lượt đo; bài này giữ nó đúng từng chữ với bản đem đi đo, và giữ ngưỡng như lúc
đăng ký.
"""
from __future__ import annotations

import hashlib
import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:ban-do-aura` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "lọt cửa một lần sinh, 15 lượt": "B ≥ 0 − 2",
    "em chấm mù, 3 bộ ba": "B xếp trên 0 ở ≥ 2/3 đề",
    "Sếp chấm lại mù, 3 bộ ba": "B xếp trên 0 ở ≥ 2/3 đề",
}
# SHA-256 (16 ký tự đầu) của khối BẢN ĐỒ lúc đăng ký — commit 29ac982, 13/09.
SHA_BAN_DO = "05B01CE0381B46F6"


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:ban-do-aura -->(.*?)<!-- /CHOT:ban-do-aura -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:ban-do-aura"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


def test_BAN_DO_dung_ban_da_dang_ky():
    van = (PROJECT_ROOT / "docs" / "BO_LUAT_PHONG_AURA_2026-09-13.md").read_text(encoding="utf-8")
    m = re.search(r"```\n(BẢN ĐỒ — .*?)\n```", van, re.S)
    assert m, "mất khối BẢN ĐỒ trong bộ luật"
    assert hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()[:16].upper() == SHA_BAN_DO
