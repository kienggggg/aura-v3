# -*- coding: utf-8 -*-
"""Link bài báo Sếp dán vào câu — `CHOT:url-dau-vao` (13/09/2026).

Đo 13/09: "tóm tắt bài này: https://nhandan.vn/dan-so-…-post934760.html" qua
`check_input` thành `https://nhandan.vn/[REDACTED_LONG_TOKEN].html` — model, máy
tìm kiếm và sổ phiên đều chỉ thấy bản ấy. Sửa ở `scrub_for_log`, cửa chung của
đầu vào, lịch sử, câu trả lời và trí nhớ: sửa riêng đầu vào thì lượt SAU
`scrub_history` lại che link trước khi tới model.
"""
from __future__ import annotations

import asyncio
import re
from uuid import uuid4

import pytest

from core.chat_contract import Channel, ChatRequest, ChatStatus
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.paths import PROJECT_ROOT
from core.secret_guard import SecretContentGuard, _che_chu, scrub_for_log
from tests.test_url_nguon_slug import _G, _SLUG, DOI_CHUNG, TUNG_ROI

# Chép TAY từ `CHOT:url-dau-vao` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "câu dán link bài báo": "16/16 ra nguyên vẹn",
    "ca đối chứng trong câu": "19/19 y hệt bộ che cũ",
    "link đứng sau ngữ cảnh bí mật": "5/5 không ra nguyên vẹn",
    "câu vừa có link vừa có bí mật": "3/3 link nguyên vẹn, bí mật vẫn che",
    "câu bộ che cũ không đụng": "1/1 ra y hệt",
    "lượt thật qua `ChatService`": "model và sổ phiên thấy link nguyên vẹn",
    "`test_secret_guard.py`": "xanh hết, không sửa bài nào",
}

KHUON = ("tóm tắt bài này: {}", "{} nói gì vậy?", "đọc giúp em bài này ({})",
         "so sánh {} với bài hôm qua.")
CAU_LINK = [KHUON[i % len(KHUON)].format(u) for i, u in enumerate(TUNG_ROI)] + [
    f"đọc {TUNG_ROI[0]} và {TUNG_ROI[10]} rồi so giúp em",
    # Thêm sau lượt gieo đầu: cho link nuốt cả `,` thì không ca nào đỏ.
    f"tóm tắt {TUNG_ROI[2]}, ngắn thôi"]

LINK = f"https://vi.du/{_SLUG}.html"
# Chép TAY tiền tố chuỗi tạm của mã: lệch nhau thì ca "có sẵn chuỗi tạm" đỏ.
GIU_CHO = "AURAGIULINK"
DOI_CHUNG_CAU = {
    **{ten: f"xem giúp em {u}" for ten, u in DOI_CHUNG.items()},
    # Không có khoảng trắng trước `http` — không nhận là link, che như cũ.
    "link dính liền sau chuỗi dài": f"abcdefghijklmnopqrstuvwxyz0123-{LINK}",
    "câu có sẵn chuỗi tạm": f"{GIU_CHO}0X {LINK}",
}
NGU_CANH = {
    "mật khẩu:": f"mật khẩu: {LINK}",
    "password=": f"password={LINK}",
    # Bộ che cũ để lọt `Bearer https://vi.du/` rồi chỉ che slug; nay che cả link.
    "Authorization: Bearer": f"Authorization: Bearer {LINK}",
    "cookie:": f"cookie: {LINK}",
    "api_key=": f"api_key={LINK}",
}
# Thêm sau lượt gieo đầu: bộ che cũ KHÔNG che câu này (luật Bearer gãy ở `:` sau
# `https`). Bỏ lối tắt "bộ che cũ không đụng link thì để nguyên" thì chuỗi tạm bị
# luật Bearer nuốt — câu đổi, tức bản sửa lan ra ngoài những link nó sinh ra để cứu.
KHONG_DUNG = {"Bearer + link ngắn": "Authorization: Bearer https://sjc.com.vn/"}
TRON = {  # (câu, bí mật phải biến mất)
    "mật khẩu": (f"{LINK} mật khẩu: abc12345xyz", "abc12345xyz"),
    "khoá sk-": (f"{LINK} và sk-{_G}", f"sk-{_G}"),
    "số điện thoại": (f"{LINK} gọi 0912345678", "0912345678"),
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:url-dau-vao -->(.*?)<!-- /CHOT:url-dau-vao -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:url-dau-vao"
    return m.group(1)


def test_SAU_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
    for ten, so in (("câu dán link bài báo", len(CAU_LINK)),
                    ("ca đối chứng trong câu", len(DOI_CHUNG_CAU)),
                    ("link đứng sau ngữ cảnh bí mật", len(NGU_CANH)),
                    ("câu vừa có link vừa có bí mật", len(TRON)),
                    ("câu bộ che cũ không đụng", len(KHONG_DUNG))):
        assert DAC_TA[ten].startswith(f"{so}/{so} "), ten


@pytest.mark.parametrize("cau", CAU_LINK)
def test_CAU_DAN_LINK_ra_NGUYEN_VEN(cau):
    assert _che_chu(cau) != cau, "bộ che cũ không đụng câu này — nó thôi làm chứng"
    assert scrub_for_log(cau) == cau


@pytest.mark.parametrize("ten", DOI_CHUNG_CAU)
def test_CA_DOI_CHUNG_trong_cau_Y_HET_bo_che_cu(ten):
    cau = DOI_CHUNG_CAU[ten]
    assert _che_chu(cau) != cau, f"{ten}: bộ che cũ không che — không đối chứng cho gì"
    assert scrub_for_log(cau) == _che_chu(cau), f"{ten}: khác bộ che cũ"


@pytest.mark.parametrize("ten", NGU_CANH)
def test_LINK_sau_NGU_CANH_bi_mat_KHONG_ra_nguyen_ven(ten):
    ra = scrub_for_log(NGU_CANH[ten])
    assert LINK not in ra, f"{ten}: link đứng ở chỗ bí mật mà ra nguyên vẹn"
    assert "REDACTED" in ra


@pytest.mark.parametrize("ten", KHONG_DUNG)
def test_CAU_bo_che_cu_KHONG_DUNG_thi_ra_Y_HET(ten):
    cau = KHONG_DUNG[ten]
    assert _che_chu(cau) == cau, f"{ten}: bộ che cũ có đụng — ca này thôi làm chứng"
    assert scrub_for_log(cau) == cau, f"{ten}: bản sửa lan ra ngoài phạm vi"


@pytest.mark.parametrize("ten", TRON)
def test_CAU_TRON_link_nguyen_ven_bi_mat_van_che(ten):
    cau, bi_mat = TRON[ten]
    ra = scrub_for_log(cau)
    assert LINK in ra, f"{ten}: link bị che"
    assert bi_mat not in ra, f"{ten}: bí mật lọt"


def test_LUOT_THAT_model_va_so_phien_thay_link_nguyen_ven():
    url = TUNG_ROI[10]
    cu = ChatMessage("user", f"hôm qua em đọc {url}")

    class _So:
        def __init__(self):
            self.ghi = []

        async def load(self, *, actor_id, session_id):
            return (cu,)

        async def append_exchange(self, *, request, result):
            self.ghi.append(request)

    class _Model:
        def __init__(self):
            self.goi = []

        async def generate(self, request, *, history, sources=()):
            self.goi.append((request, tuple(history)))
            return ModelReply("Bài nói dân số 102,3 triệu người.")

    so, model = _So(), _Model()
    kq = asyncio.run(ChatService(model=model, store=so, guard=SecretContentGuard()).reply(
        ChatRequest(request_id=str(uuid4()), session_id=str(uuid4()), actor_id="owner",
                    channel=Channel.TEST, text=f"tóm tắt bài này: {url}")))
    assert kq.status is ChatStatus.OK
    yeu_cau, lich_su = model.goi[0]
    assert url in yeu_cau.text, "model không thấy link Sếp dán"
    # Vá một nửa của một cặp: sổ giữ link mà `scrub_history` che lại ở lượt sau.
    assert any(url in m.content for m in lich_su), "lượt sau model không thấy link cũ"
    assert url in so.ghi[0].text, "sổ phiên không giữ link"
