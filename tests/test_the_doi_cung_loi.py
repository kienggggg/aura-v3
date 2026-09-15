# -*- coding: utf-8 -*-
"""Thẻ phải đổi ĐÚNG LÚC câu của nó bắt đầu — `core/phong_alpha.py::dai_moi_the` (sửa 15/09/2026).

Bản 06/09 lấy thời lượng thẻ = phần CÓ TIẾNG của câu (`kt - bd`) rồi nối liền các thẻ, trong khi mốc
phụ đề mang cả khe im lặng. Đo trên video thật: review Skibidi thẻ đổi sớm 0,15 → 1,33 s (tăng đúng
một khe mỗi câu); video truyện thẻ cuối đứng 14,2 s trên 60 s. `kiem_video` không đo chỗ này.
"""
from __future__ import annotations

from itertools import accumulate

from core import phong_alpha as pa

# Mốc thật của 4 câu đầu video review Skibidi (15/09): khe 0,15 s giữa các câu.
MOC = [(0.0, 7.08), (7.23, 13.81), (13.96, 20.98), (21.13, 25.90)]


def test_the_i_bat_dau_dung_luc_cau_i_bat_dau():
    dai = pa.dai_moi_the(MOC, 27.0, len(MOC))
    bat_dau = [0.0] + list(accumulate(dai))[:-1]
    for (bd, _), t in zip(MOC, bat_dau):
        assert abs(t - bd) < 1e-6, f"thẻ bắt đầu {t:.2f}, câu bắt đầu {bd:.2f}"


def test_the_cuoi_keo_toi_het_giong():
    dai = pa.dai_moi_the(MOC, 27.0, len(MOC))
    assert abs(sum(dai) - 27.0) < 1e-6


def test_khong_co_moc_thi_chia_deu():
    assert pa.dai_moi_the(None, 12.0, 3) == [4.0, 4.0, 4.0]
    assert pa.dai_moi_the(MOC[:2], 12.0, 3) == [4.0, 4.0, 4.0]   # số mốc lệch số thẻ: lui về chia đều
