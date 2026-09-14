# -*- coding: utf-8 -*-
"""Kịch bản phòng AURA không được mang chữ Anh — `CHOT:chu-anh-kich-ban` (14/09/2026).

"giũ áo wet", "ánh sáng golden", "bàn tay calloused" lọt vào bản vào video. Kiểm
theo CẤU TẠO âm tiết tiếng Việt, không theo danh sách từ Anh — danh sách thì bắt
nhầm "no", "so", "can", "ban", "tin".
"""
from __future__ import annotations

import re

import pytest

import core.viet_truyen as vt
from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:chu-anh-kich-ban` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "từ tiếng Việt thật bị bắt nhầm, bộ B": "0",
    "chữ Anh đã biết trong bộ B (wet, golden, calloused)": "3/3 bị bắt",
}
MAU = "Câu thứ {n}: ông lão đội nón lá bước chậm qua phố ướt đẫm, mưa rơi lộp độp mãi."
DE = "ông lão đội nón lá"


def _hop_le() -> str:
    return " ".join(MAU.format(n=n) for n in range(1, 13))      # 12 × 19 = 228 từ


def _bac(*chu: str) -> list:
    return [f"có chữ không phải âm tiết tiếng Việt: {' '.join(chu)}"]


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:chu-anh-kich-ban -->(.*?)<!-- /CHOT:chu-anh-kich-ban -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:chu-anh-kich-ban"
    return m.group(1)


def test_HAI_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


# "nghách" (bộ B: "ngóc nghách" — sai chính tả của "ngách") và "cé" canh luật k/gh/ngh
# và c/g/ng: bỏ hai luật ấy thì chúng lọt.
@pytest.mark.parametrize("chen", ["wet", "golden", "calloused", "hot", "light", "love", "bus", "cũnghiêng",
                                  "nghách", "cé"])
def test_CHU_KHONG_PHAI_AM_TIET_VIET_thi_BI_BAC(chen):
    van = _hop_le().replace("mưa rơi", f"mưa {chen} rơi", 1)
    assert vt.kiem_chu_la(DE, van) == _bac(chen), f"{chen!r} lọt cửa"


# Tiếng Việt thật — gồm đúng những chỗ luật chính tả dễ gãy: gi nuốt i, qu mang u,
# k/gh/ngh trước i/e/ê, tắc âm cuối có dấu sắc/nặng, vần hiếm.
VIET = ("gì gìn giếng giết giữa quỳnh quyết quý quốc quà nghiêng nghe ghế kính kể "
        "khuya khuỷu hót họt người ước ươm hươu oái oằn thuở quờ ừ ạ ở ấy yêu yến "
        "xuyên huỳnh hoạch ngoằn nghèo tuyết đẹp kịp so no can ban tin anh em").split()


def test_TIENG_VIET_THAT_deu_LOT():
    assert vt.chu_khong_phai_tieng_viet(" ".join(VIET)) == []
    # Ca đối chứng cho mọi bài "bị bác": bản mẫu lọt cả cửa hình dạng lẫn cửa này.
    assert vt.do_kich_ban(_hop_le())[0] == "DAT"
    assert vt.kiem_chu_la(DE, _hop_le()) == []


def test_TU_MUON_lot_con_bus_thi_khong():
    assert vt.chu_khong_phai_tieng_viet("một chiếc taxi và cái video cũ") == []
    assert vt.chu_khong_phai_tieng_viet("chuyến xe bus cuối ngày") == ["bus"]


def test_CHUA_CHAN_DUOC_chu_Anh_trung_hinh_am_tiet_Viet():
    """Ghi thành bài để không ai đọc cửa này thành 'đã chặn mọi chữ Anh'."""
    assert vt.chu_khong_phai_tieng_viet("the so man") == []


def test_CHU_CUA_DE_duoc_MIEN_theo_TU_khong_theo_chuoi_con():
    van = _hop_le().replace("mưa rơi", "mưa iPhone Phone rơi", 1)
    assert vt.kiem_chu_la("chiếc iPhone cũ", van) == _bac("Phone")
    # Ca đối chứng: cùng văn bản, đề không mang chữ ấy thì cả hai bị bác.
    assert vt.kiem_chu_la(DE, van) == _bac("Phone", "iPhone")


@pytest.mark.parametrize("de", ["Facebook", "chiếc iPhone cũ", "mưa axit"])
def test_DE_MANG_CHU_LA_van_DAT_duoc(monkeypatch, de):
    """Bản đầu 14/09 bác cả ba đề 3/3 lần dù model làm đúng lời nhắc: cửa nêu đề
    đòi chữ của đề ở câu mở, cửa chữ lạ cấm chính chữ ấy."""
    mo = f"Câu thứ 1: {de} hiện ra khi ông lão đội nón lá bước chậm qua phố ướt đẫm, mưa rơi."
    ban = " ".join([mo] + [MAU.format(n=n) for n in range(2, 13)])
    monkeypatch.setattr("core.viet_truyen._xin_model", lambda loi, hat: (ban, 1.0))
    kq = vt.viet_kich_ban(de)
    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert kq["so_lan_thu"] == 1


def test_CO_CHU_ANH_thi_SINH_LAI_va_nhan_ban_sach(monkeypatch):
    ban = [_hop_le().replace("mưa rơi", "mưa golden rơi", 1), _hop_le()]
    goi = []

    def _gia(loi, hat):
        goi.append(hat)
        return ban[len(goi) - 1], 1.0

    monkeypatch.setattr("core.viet_truyen._xin_model", _gia)
    kq = vt.viet_kich_ban("ông lão đội nón lá")
    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert kq["so_lan_thu"] == 2 and "golden" not in kq["van_ban"]
