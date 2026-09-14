# -*- coding: utf-8 -*-
"""Sổ lỗi phòng AURA phải đọc được bằng máy — `SO_LOI_PHONG_AURA.md` (14/09/2026).

Sổ ấy sẽ được phòng viết đọc lúc chạy (kế hoạch §6), nên một mục thiếu trường, trùng
mã hay có câu dặn chép lại câu sai thì hỏng LẶNG: lời nhắc vẫn ra, chỉ là mang nhầm
thứ. Canh ngay từ khi sổ mới có năm mục.
"""
from __future__ import annotations

import re

from core.paths import PROJECT_ROOT

# Chép TAY từ phần "Luật của sổ" và kế hoạch §6 — hai chỗ, cãi nhau được.
TRUONG = ("ngày", "ai thấy", "loại", "lỗi", "ví dụ", "câu dặn", "số lần gặp", "trạng thái")
LOAI = {"A", "B", "C"}
TRANG_THAI = {"chờ đo", "đang dặn", "đã thành cửa", "đã sửa máy", "bỏ"}
TRAN_KY_TU = 480
TU_LIEN_TOI_DA = 4          # trùng từ 5 từ liền trở lên là chép


def _so() -> str:
    return (PROJECT_ROOT / "SO_LOI_PHONG_AURA.md").read_text(encoding="utf-8")


def _muc() -> list[tuple[str, dict]]:
    ra = []
    for ma, than in re.findall(r"^### (L-\d{2})\n((?:- [^\n]*\n?)+)", _so(), re.M):
        truong = dict(re.findall(r"^- ([^:\n]+): (.*)$", than, re.M))
        ra.append((ma, truong))
    return ra


def _tu(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


def test_CO_MUC_de_ma_kiem():
    """Không đọc ra mục nào thì mọi bài dưới xanh vì rỗng — KHÔNG ĐO ĐƯỢC đội lốt đạt."""
    assert len(_muc()) >= 5, f"chỉ đọc được {len(_muc())} mục"
    assert len(_muc()) == _so().count("\n### "), "có mục viết sai dạng nên máy không đọc ra"


def test_MA_KHONG_TRUNG():
    ma = [m for m, _ in _muc()]
    assert len(ma) == len(set(ma)), ma


def test_MOI_MUC_du_truong_va_dung_gia_tri():
    for ma, t in _muc():
        thieu = [k for k in TRUONG if k not in t]
        assert not thieu, f"{ma} thiếu {thieu}"
        assert t["loại"] in LOAI, f"{ma}: loại {t['loại']!r}"
        assert t["trạng thái"] in TRANG_THAI, f"{ma}: trạng thái {t['trạng thái']!r}"
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", t["ngày"]), f"{ma}: ngày {t['ngày']!r}"
        assert t["số lần gặp"].isdigit() and int(t["số lần gặp"]) >= 1, ma


def test_CHI_LOAI_C_co_cau_dan():
    """A và B chữa bằng máy, tốn 0 token — chúng mà mang câu dặn là tốn ngữ cảnh vô ích."""
    for ma, t in _muc():
        if t["loại"] == "C":
            assert t["câu dặn"] not in ("", "—"), f"{ma} loại C mà không có câu dặn"
        else:
            assert t["câu dặn"] == "—", f"{ma} loại {t['loại']} không được có câu dặn"


def test_CAU_DAN_khong_chep_cau_sai():
    """Bản đồ bị chép nguyên chữ vào 2/15 truyện — câu sai vào lời nhắc thì model chép câu sai."""
    for ma, t in _muc():
        dan, vd = _tu(t["câu dặn"]), _tu(t["ví dụ"])
        n = TU_LIEN_TOI_DA + 1
        chung = {tuple(dan[i:i + n]) for i in range(len(dan) - n + 1)} & \
                {tuple(vd[i:i + n]) for i in range(len(vd) - n + 1)}
        assert not chung, f"{ma}: câu dặn chép {n} từ liền của câu sai: {sorted(chung)}"


def test_KHOI_CAU_DAN_trong_tran():
    khoi = [t["câu dặn"] for _, t in _muc()
            if t["loại"] == "C" and t["trạng thái"] in ("chờ đo", "đang dặn")]
    assert khoi, "không có câu dặn nào để đo trần — bài này xanh vì rỗng"
    dai = len("\n".join(khoi))
    assert dai <= TRAN_KY_TU, f"khối câu dặn {dai} ký tự, trần {TRAN_KY_TU} (~150 token)"


def test_TRAN_trong_so_khop_ban_chep_tay():
    assert f"**{TRAN_KY_TU} ký tự**" in _so(), "trần trong sổ và trong cửa canh lệch nhau"
