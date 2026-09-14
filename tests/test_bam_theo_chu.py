# -*- coding: utf-8 -*-
"""Lớp thích nghi, nhánh A — `_bam_theo_chu` (`CHOT:dang-vong-1`, 15/09/2026).

Không easyocr, không trình duyệt: thay `_doc_chu` bằng kết quả OCR giả và trang bằng một
vật giả ghi lại mọi cú bấm. Canh đúng một điều — bấm NHẦM nút thì hỏng cả tài khoản của Sếp.
"""
from __future__ import annotations

import ast

import pytest

from core.paths import PROJECT_ROOT
from tools import dang_truyen_worker as w

O_LUU = ([[100, 40], [160, 40], [160, 70], [100, 70]], "Lưu", 0.9)
O_DANG = ([[20, 40], [110, 40], [110, 70], [20, 70]], "Đăng tải", 0.9)


class TrangGia:
    def __init__(self, chu_tai_cho: str | None, dpr: float = 2.0):
        self.chu_tai_cho, self.dpr, self.bam = chu_tai_cho, dpr, []
        self.mouse = self

    def screenshot(self):
        return b"anh"

    def evaluate(self, js, doi=None):
        return self.dpr if doi is None else self.chu_tai_cho

    def click(self, x, y):
        self.bam.append((x, y))


def _ocr(monkeypatch, *o):
    monkeypatch.setattr(w, "_doc_chu", lambda anh: list(o))


def test_DUNG_MOT_O_va_phan_tu_dung_chu_thi_BAM_dung_tam(monkeypatch):
    _ocr(monkeypatch, O_DANG, O_LUU)
    t = TrangGia("Lưu", dpr=2.0)
    kq = w._bam_theo_chu(t, "Lưu")
    assert kq["bam"] and t.bam == [(65.0, 27.5)], (kq, t.bam)      # tâm (130,55) chia dpr 2


def test_PHAN_TU_TAI_CHO_la_nut_khac_thi_KHONG_BAM(monkeypatch):
    _ocr(monkeypatch, O_LUU)
    for sai in ("Đăng tải", "Lưu & Đăng", "Lưu lại", None, ""):
        t = TrangGia(sai)
        assert not w._bam_theo_chu(t, "Lưu")["bam"] and t.bam == [], sai


def test_OCR_THAY_0_hay_2_O_thi_KHONG_BAM_khong_doan(monkeypatch):
    for o in ((), (O_LUU, O_LUU)):
        _ocr(monkeypatch, *o)
        t = TrangGia("Lưu")
        assert not w._bam_theo_chu(t, "Lưu")["bam"] and t.bam == []


def test_NHAN_MANG_CHU_DANG_thi_NO_truoc_ca_khi_chup(monkeypatch):
    _ocr(monkeypatch, O_DANG)
    t = TrangGia("Đăng tải")
    with pytest.raises(ValueError):
        w._bam_theo_chu(t, "Đăng tải")
    assert t.bam == []


def test_OCR_mat_dau_van_de_xuat_duoc_nhung_TRANG_moi_quyet(monkeypatch):
    """OCR hay rụng dấu ("Luu"). Nó được ĐỀ XUẤT chỗ; bấm hay không là chữ thật trên trang."""
    _ocr(monkeypatch, ([[0, 0], [10, 0], [10, 10], [0, 10]], "Luu", 0.5))
    assert w._bam_theo_chu(TrangGia("Lưu", 1.0), "Lưu")["bam"]
    assert not w._bam_theo_chu(TrangGia("Luu", 1.0), "Lưu")["bam"]


def test_CU_BAM_nam_SAU_cau_hoi_trang():
    nguon = (PROJECT_ROOT / "tools" / "dang_truyen_worker.py").read_text(encoding="utf-8")
    than = next(n for n in ast.walk(ast.parse(nguon))
                if isinstance(n, ast.FunctionDef) and n.name == "_bam_theo_chu")
    goi = [(n.lineno, n.func.attr) for n in ast.walk(than)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    bam = [l for l, a in goi if a == "click"]
    hoi = [l for l, a in goi if a == "evaluate"]
    assert len(bam) == 1 and len(hoi) == 2 and max(hoi) < bam[0], goi
