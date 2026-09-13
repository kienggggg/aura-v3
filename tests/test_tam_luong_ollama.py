# -*- coding: utf-8 -*-
"""Bốn nơi gọi `qwen3.5:4b` gửi CÙNG `num_thread` và `num_ctx` — `CHOT:tam-luong-ollama`.

Đo 13/09/2026 trên máy này (i5-1135G7, 4 nhân / 8 luồng): 8 luồng rút khúc
model ĐỌC lời nhắc 39,3 s -> 34,3 s. Nhưng chat nạp model với 8 luồng thì lời
gọi của phòng không nhắc `num_thread` NẠP LẠI 8,0 s, quay về chat nạp lại thêm
8,0 s — lợi 5 s bị lỗ 16 s mỗi vòng chuyển nếu chỉ một nơi đổi.

Bắt LỜI GỌI THẬT — chặn đúng hàm gửi của từng nơi — không đọc chữ trong mã.
Ngưỡng chép TAY từ khối đặc tả.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import uuid

from core import omega, phong_noi_bo, viet_truyen
from core.chat_contract import ChatRequest
from core.local_first_gateway import OllamaConfig, OllamaGateway
from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:tam-luong-ollama`.
DAC_TA_DOC = "≤ −10 %"
DAC_TA_VIET = "chậm không quá 5 %"
DAC_TA_SO_NOI = 4
DAC_TA_NAP_LAI = "0 lần"

# Nơi gọi model SINH CHỮ — danh sách ĐÓNG. Nơi thứ năm xuất hiện thì
# `test_KHONG_co_noi_goi_thu_nam` đỏ cho tới khi nó vào đây VÀ bị bắt lời gọi.
NOI_GOI = frozenset({
    "core/local_first_gateway.py",
    "core/omega.py",
    "core/phong_noi_bo.py",
    "core/viet_truyen.py",
})


def _tuy_chon_chat() -> dict:
    bat = {}

    class _Client:
        async def post(self, url, json=None):
            bat["json"] = json

            class _R:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "Chào Sếp, em đây."}}

            return _R()

    asyncio.run(OllamaGateway(OllamaConfig(), client=_Client()).generate(
        ChatRequest(request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
                    actor_id="owner", channel="test", text="Chào Sếp")))
    return bat["json"]


class _Tra:
    """Phản hồi giả của `urllib`: đủ trường cho cả ba phòng đọc."""

    def __init__(self, goi):
        self._b = json.dumps(goi).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _goi_phong(monkeypatch) -> dict[str, dict]:
    bat: list[dict] = []

    def urlopen(req, timeout=None):
        bat.append(json.loads(req.data.decode("utf-8")))
        return _Tra({"response": "một hai ba", "eval_count": 10,
                     "eval_duration": 10**9})

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    ra = {}
    for ten, goi in (("omega", lambda: omega._hoi("x")),
                     ("phong_noi_bo", phong_noi_bo.do_toc_do_model),
                     ("viet_truyen", lambda: viet_truyen._xin_model("x", 1))):
        bat.clear()
        goi()
        assert len(bat) == 1, f"{ten}: bắt được {len(bat)} lời gọi, cần 1"
        ra[ten] = bat[0]
    return ra


def test_BON_NOI_GOI_gui_CUNG_num_thread_va_num_ctx(monkeypatch):
    chat = _tuy_chon_chat()
    tat_ca = {"chat": chat, **_goi_phong(monkeypatch)}
    assert len(tat_ca) == DAC_TA_SO_NOI
    goc = chat["options"]
    assert goc.get("num_thread") == (os.cpu_count() or 4), goc
    for ten, goi in tat_ca.items():
        assert goi["model"] == "qwen3.5:4b", f"{ten} gọi model khác: {goi['model']}"
        o = goi["options"]
        for khoa in ("num_thread", "num_ctx"):
            assert o.get(khoa) == goc.get(khoa), (
                f"{ten} gửi {khoa}={o.get(khoa)!r}, chat gửi {goc.get(khoa)!r} — "
                "lệch một tuỳ chọn là Ollama nạp lại model 8,0 s mỗi lần chuyển")


def test_KHONG_co_noi_goi_thu_nam():
    """Hỏi `ast` chứ không dò chữ: tệp nào dựng một `dict` có khoá `num_predict`
    là tệp đang gọi model sinh chữ."""
    co = set()
    for thu_muc in ("core", "interface"):
        for tep in (PROJECT_ROOT / thu_muc).rglob("*.py"):
            cay = ast.parse(tep.read_text(encoding="utf-8"))
            if any(isinstance(n, ast.Dict) and any(
                    isinstance(k, ast.Constant) and k.value == "num_predict"
                    for k in n.keys) for n in ast.walk(cay)):
                co.add(tep.relative_to(PROJECT_ROOT).as_posix())
    assert co == NOI_GOI, (
        f"thêm: {sorted(co - NOI_GOI)} · mất: {sorted(NOI_GOI - co)} — nơi gọi mới "
        "phải gửi cùng num_thread/num_ctx, và phải vào NOI_GOI")


def test_NGUONG_khop_khoi_dac_ta():
    khoi = re.search(
        r"<!-- CHOT:tam-luong-ollama -->(.*?)<!-- /CHOT:tam-luong-ollama -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert khoi, "mất khối đặc tả CHOT:tam-luong-ollama"
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", khoi.group(1), re.M))
    assert DAC_TA_DOC in hang.get("khúc đọc đường có nguồn, trạng thái ổn định", "")
    assert DAC_TA_VIET in hang.get("khúc viết", "")
    assert f"{DAC_TA_SO_NOI}/{DAC_TA_SO_NOI}" in hang.get(
        "nơi gọi `qwen3.5:4b` gửi cùng `num_thread` và `num_ctx`", "")
    assert DAC_TA_NAP_LAI in hang.get("nạp lại khi chuyển chat ↔ phòng", "")
