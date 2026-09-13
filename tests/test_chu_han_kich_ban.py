# -*- coding: utf-8 -*-
"""Kịch bản phòng AURA không được mang chữ Hán — `CHOT:chu-han-kich-ban` (13/09/2026).

Đo 13/09: 10/30 bản gốc của `qwen3.5:4b` chứa chữ Hán (工具箱 · 光亮 · 哒哒…), và
6/25 bản ĐÃ LỌT CỬA vẫn còn chữ Hán sau khi cắt — đi thẳng vào giọng đọc video.
"""
from __future__ import annotations

import re

import pytest

import core.viet_truyen as vt
from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:chu-han-kich-ban` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "chữ Hán, kana, chữ Hàn trong bản lọt cửa": "0",
    "chữ Latin mở rộng và dấu rời (mọi chữ tiếng Việt)": "lọt hết",
}
DE = "ông lão đội nón lá"
# 19 từ mỗi câu, đủ dấu tiếng Việt: 12 câu = 228 từ, lọt 215–250.
MAU = "Câu thứ {n}: ông lão đội nón lá bước chậm qua phố ướt đẫm, mưa rơi lộp độp mãi."


def _hop_le() -> str:
    return " ".join(MAU.format(n=n) for n in range(1, 13))


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:chu-han-kich-ban -->(.*?)<!-- /CHOT:chu-han-kich-ban -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:chu-han-kich-ban"
    return m.group(1)


def test_HAI_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


def test_BAN_HOP_LE_lot_cua():
    """Ca đối chứng: bỏ đi thì mọi bài 'bị bác' dưới đây có thể đỏ vì lý do khác."""
    tt, ly_do, so = vt.do_kich_ban(_hop_le())
    assert tt == "DAT", ly_do
    assert so["so_tu"] == 228


@pytest.mark.parametrize("chen", ["工具箱", "哒哒", "かな", "カタカナ", "한국어", "，", "。", "镶嵌"])
def test_CHU_KHONG_DOC_DUOC_bang_giong_Viet_thi_BI_BAC(chen):
    van = _hop_le().replace("mưa rơi", f"mưa {chen} rơi", 1)
    tt, ly_do, _ = vt.do_kich_ban(van)
    assert tt == "KHONG_DAT", f"{chen!r} lọt cửa"
    assert any(chen in l for l in ly_do), f"lý do bác không chỉ ra chữ lạ: {ly_do}"


def test_MOI_CHU_TIENG_VIET_dung_san_lan_dau_roi_deu_LOT():
    latin = "".join(chr(c) for c in [*range(0xC0, 0x250), *range(0x1E00, 0x1F00)])
    dau_roi = "a" + "".join(chr(c) for c in range(0x300, 0x370))
    van = _hop_le().replace("mãi.", f"mãi {latin} {dau_roi}.", 1)
    tt, ly_do, _ = vt.do_kich_ban(van)
    assert tt == "DAT", ly_do


def test_CO_CHU_HAN_thi_SINH_LAI_va_nhan_ban_sach(monkeypatch):
    ban = [_hop_le().replace("mưa rơi", "mưa 淅沥 rơi", 1), _hop_le()]
    goi = []

    def _gia(loi, hat):
        goi.append(hat)
        return ban[len(goi) - 1], 1.0

    monkeypatch.setattr("core.viet_truyen._xin_model", _gia)
    kq = vt.viet_kich_ban(DE)
    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert kq["so_lan_thu"] == 2 and len(goi) == 2
    assert "淅沥" not in kq["van_ban"]
