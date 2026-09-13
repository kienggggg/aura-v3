# -*- coding: utf-8 -*-
"""Chỉ bỏ dòng URL khỏi khối nguồn — `CHOT:bo-dong-url` (13/09/2026).

Sếp chọn phương án (b) của `CHOT:cat-khoi-nguon`. Nó chưa đo riêng, và dòng URL
mang thứ tiêu đề không có — TÊN TRANG: nguồn [1] câu tỷ giá có tiêu đề "Tỷ giá",
chỉ URL cho biết đó là trang của Vietcombank. Bảy ngưỡng đăng ký TRƯỚC khi chạy
model; bài này giữ chúng đúng như lúc đăng ký.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:bo-dong-url` — TOÀN BỘ ô, so bằng `==`. So `in` thì
# "VU ≤ V0" nằm gọn trong "VU ≤ V0 − 1", và "0" nằm trong "10".
DAC_TA = {
    "token khúc đọc VU so với V0, 18 lượt": "trung vị ≤ × 0,95",
    "trúng thước VU, 18 lượt": "≥ số trúng của V0 − 1",
    "câu nhạy lãi suất 12 tháng": "VU trúng ≥ V0 trúng",
    "giá mua vào 143, 4 lượt giá vàng": "VU nhắc ≥ V0 nhắc − 1",
    "lượt có đánh số [n], 18 lượt": "VU ≥ V0 − 1",
    "lượt có [k] ngoài 1..số nguồn, 20 lượt": "VU ≤ V0",
    "link bịa, 20 lượt VU": "0",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:bo-dong-url -->(.*?)<!-- /CHOT:bo-dong-url -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:bo-dong-url"
    return m.group(1)


def test_BAY_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
