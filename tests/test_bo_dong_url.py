# -*- coding: utf-8 -*-
"""Chỉ bỏ dòng URL khỏi khối nguồn — `CHOT:bo-dong-url` (13/09/2026).

Sếp chọn phương án (b) của `CHOT:cat-khoi-nguon`. Nó chưa đo riêng, và dòng URL
mang thứ tiêu đề không có — TÊN TRANG: nguồn [1] câu tỷ giá có tiêu đề "Tỷ giá",
chỉ URL cho biết đó là trang của Vietcombank. Bảy ngưỡng đăng ký TRƯỚC khi chạy
model (commit deafd5c); 40 lượt ĐẠT cả bảy, nên khối nguồn bỏ dòng URL. Bài này
giữ ngưỡng đúng như lúc đăng ký, và ghim khối nguồn đúng như đã đo.
"""
from __future__ import annotations

import re
import uuid

from core.chat_contract import ChatRequest, SourceCitation
from core.local_first_gateway import OllamaConfig, OllamaGateway
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


URL_1 = "https://vi.du/gia-vang-hom-nay-13-9-sjc-146-trieu"
URL_2 = "https://ngan-hang.vi.du/vi-VN/KHCN/Ty-gia"
TRICH_1 = ("Giá vàng SJC bán ra 146 triệu, mua vào 143 triệu đồng/lượng. " * 8)[:400]
TRICH_2 = ("Tỷ giá USD bán ra 26.148 đồng, mua vào 25.894 đồng. " * 9)[:400]


def _nguoi_dung() -> str:
    tin = OllamaGateway(OllamaConfig())._messages(
        ChatRequest(request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
                    actor_id="owner", channel="test", text="giá vàng hôm nay"),
        history=(),
        sources=(
            SourceCitation(title="Giá vàng hôm nay", url=URL_1,
                           retrieved_at="2026-09-13T05:00:00+00:00", supports=TRICH_1),
            SourceCitation(title="Tỷ giá", url=URL_2,
                           retrieved_at="2026-09-13T05:00:00+00:00", supports=TRICH_2),
        ))
    return tin[-1]["content"]


def test_KHOI_NGUON_bo_URL_nhung_giu_DU_tieu_de_va_doan_trich():
    assert "ĐƯA VU VÀO `_messages`" in _khoi(), (
        "khối đặc tả không còn ghi quyết định đưa VU vào — mã và đặc tả lệch nhau")
    nd = _nguoi_dung()
    # Soi TÊN MIỀN chứ không chỉ cả chuỗi URL: bỏ "https://" mà để lại
    # "vi.du/..." thì model vẫn thấy tên trang, và phép đo không đo trường hợp ấy.
    assert "vi.du" not in nd, "tên trang còn trong lời nhắc — phép đo là bỏ HẲN dòng URL"
    # Nguyên cặp tiêu đề + đoạn trích ĐỦ 400 ký tự, liền nhau: cắt đoạn trích là
    # phương án (a), Sếp đã bác vì mất giá mua vào 143 (V0 2/2, V12 0/2).
    assert f"[1] Giá vàng hôm nay\n{TRICH_1}" in nd
    assert f"[2] Tỷ giá\n{TRICH_2}" in nd
