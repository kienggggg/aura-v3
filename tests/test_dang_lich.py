# -*- coding: utf-8 -*-
"""Lịch tự chạy hàng chờ đăng — `CHOT:dang-lich` (14/09/2026).

Đọc ngưỡng đăng ký trước, và canh khoá + sổ lịch của `tools/dang_truyen_worker.py` — không
Playwright, không mở trình duyệt, không đụng `F:\\aura-dang\\` thật.
"""
from __future__ import annotations

import os
import re
import time

import pytest

from core.paths import PROJECT_ROOT
from tools import dang_truyen_worker as w

# Chép TAY từ `CHOT:dang-lich` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "kịch bản mới qua /api/dispatch thành chương nháp, không ai chạy lệnh": "≤ 15 phút",
    "lượt không có việc vẫn ghi sổ lịch": "1 dòng mỗi lượt",
    "lượt chạy khi đang có lượt khác giữ khoá": "bỏ qua, 0 chương trùng",
    "lần đăng công khai ngoài ý muốn": "0",
}


def _khoi() -> str:
    m = re.search(r"<!-- CHOT:dang-lich -->(.*?)<!-- /CHOT:dang-lich -->",
                  (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:dang-lich"
    return m.group(1)


def test_BON_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


@pytest.fixture
def goc(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "GOC_HO_SO", tmp_path)
    monkeypatch.setattr(w, "TEP_KHOA", tmp_path / "dang_hang_cho.lock")
    monkeypatch.setattr(w, "SO_LICH", tmp_path / "lich_chay.jsonl")
    monkeypatch.setattr(w, "TEP_TRUYEN_THU", tmp_path / "truyen_thu.json")
    w._ghi_truyen_thu("wattpad_tuyen_tap", {"id": "1", "url": "u"})
    return tmp_path


def test_KHOA_giu_duoc_mot_lan_tha_ra_thi_giu_lai_duoc(goc):
    assert w._giu_khoa() is True
    assert w._giu_khoa() is False, "lượt thứ hai giữ được khoá — hai lượt sẽ chạy chồng"
    w._tha_khoa()
    assert w._giu_khoa() is True
    w._tha_khoa()


def test_KHOA_CU_qua_mot_gio_thi_coi_la_cua_luot_da_chet(goc):
    assert w._giu_khoa()
    cu = time.time() - w.KHOA_CU_GIAY - 60
    os.utime(w.TEP_KHOA, (cu, cu))
    assert w._giu_khoa() is True
    w._tha_khoa()


def test_DANG_CO_KHOA_thi_hang_cho_BO_QUA_khong_mo_trinh_duyet(goc, monkeypatch):
    monkeypatch.setattr(w, "_hang_cho", lambda nt: [{"sha256": "x"}])
    assert w._giu_khoa()
    kq = w.dang_hang_cho("wattpad")
    assert kq["trang_thai"] == "BO_QUA_DANG_CO_LUOT_KHAC" and kq["ket"] == [], kq
    w._tha_khoa()


def test_LUOT_KHONG_VIEC_van_ghi_SO_LICH_va_tha_khoa(goc, monkeypatch):
    monkeypatch.setattr(w, "_hang_cho", lambda nt: [])
    kq = w.lich_chay("wattpad")
    dong = w.SO_LICH.read_text(encoding="utf-8").splitlines()
    assert len(dong) == 1 and kq["so_viec"] == 0 and kq["trang_thai"] == "XONG", dong
    assert not w.TEP_KHOA.exists(), "lượt xong mà không thả khoá — mọi lượt sau sẽ bỏ qua"


def test_LUOT_LOI_van_ghi_SO_LICH_va_tha_khoa(goc, monkeypatch):
    def _no(nt):
        raise RuntimeError("gieo: hỏng giữa chừng")
    monkeypatch.setattr(w, "_hang_cho", _no)
    kq = w.lich_chay("wattpad")
    assert kq["trang_thai"] == "LOI" and "gieo" in kq["loi"], kq
    assert len(w.SO_LICH.read_text(encoding="utf-8").splitlines()) == 1
    assert not w.TEP_KHOA.exists()


def test_PYTHONW_khong_co_stdout_thi_khong_chet(goc, monkeypatch):
    """Task Scheduler chạy `pythonw.exe`: `sys.stdout` là None. Gọi `reconfigure` trên None
    là chết TRƯỚC khi ghi sổ lịch — và lịch trông như không bao giờ chạy."""
    monkeypatch.setattr(w, "_hang_cho", lambda nt: [])
    monkeypatch.setattr(w.sys, "stdout", None)
    assert w.main(["dang_truyen_worker.py", "lich_chay", "wattpad"]) == 0
    assert len(w.SO_LICH.read_text(encoding="utf-8").splitlines()) == 1
