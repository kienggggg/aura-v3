# -*- coding: utf-8 -*-
"""Câu mở phải GIỚI THIỆU, không chỉ nhắc tên đề — `CHOT:mo-truyen-gioi-thieu` (14/09/2026).

Sổ lỗi L-01. Bản X bị chê mở "…ngồi trên chiếc xe ba bánh" rồi nói ngay ông muốn gì;
bản Y cùng cặp CŨNG mở bằng nguyên văn đề ("… là người đàn ông …") mà được khen. Phép
thử đăng ký trước; mã sản phẩm CHƯA đổi.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:mo-truyen-gioi-thieu` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "lọt cửa một lần sinh, nhánh G, 15 lượt": "G ≥ 0 − 2",
    "lọt cửa một lần sinh, nhánh D, 15 lượt": "D ≥ 0 − 2",
    "Sếp chấm mù ba câu đầu, 3 bộ ba": "nhánh được đổi xếp trên 0 ở ≥ 2/3 đề",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:mo-truyen-gioi-thieu -->(.*?)<!-- /CHOT:mo-truyen-gioi-thieu -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:mo-truyen-gioi-thieu"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
