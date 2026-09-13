# -*- coding: utf-8 -*-
"""Bộ luật phòng AURA, bản gọn — `CHOT:bo-luat-aura` (13/09/2026).

Ngày 16/08 một bộ luật văn phong trong lời nhắc đã THUA bản không luật. Bản gọn
sáu dòng chỉ vào lời nhắc khi đo ra nó thắng. Bài này giữ ngưỡng như lúc đăng ký,
và giữ sáu dòng ấy đúng từng chữ với bản đem đi đo — sửa một chữ là phép đo không
còn nói về bản mới.
"""
from __future__ import annotations

import hashlib
import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:bo-luat-aura` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "lọt cửa phòng viết, 15 lượt mỗi nhánh": "L ≥ 0 − 2",
    "em chấm mù, 3 cặp": "L thắng ≥ 2/3",
    "Sếp chấm lại mù, 3 cặp": "L thắng ≥ 2/3",
}
# SHA-256 (16 ký tự đầu) của sáu dòng "CÁCH VIẾT" lúc đăng ký, 13/09/2026.
SHA_CACH_VIET = "306F2CB11D74270B"


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:bo-luat-aura -->(.*?)<!-- /CHOT:bo-luat-aura -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:bo-luat-aura"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


def test_SAU_DONG_CACH_VIET_dung_ban_da_dang_ky():
    van = (PROJECT_ROOT / "docs" / "BO_LUAT_PHONG_AURA_2026-09-13.md").read_text(encoding="utf-8")
    m = re.search(r"```\n(CÁCH VIẾT:\n.*?)\n```", van, re.S)
    assert m, "mất khối CÁCH VIẾT trong bộ luật"
    assert m.group(1).count("\n- ") == 6
    assert hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()[:16].upper() == SHA_CACH_VIET
