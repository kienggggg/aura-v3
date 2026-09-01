# -*- coding: utf-8 -*-
"""Chỉ được có MỘT bộ đọc Python → thẻ, và nó phải là bộ app thật sự dùng.

VÌ SAO CÓ TỆP NÀY — và đây là cửa sinh ra từ một lần TÔI BÁO SAI, không phải
từ một lỗi của app.

Ngày 01/09/2026 repo có hai bộ đọc trông y hệt nhau từ bên ngoài:

    core/the_v1.py   bằng `ast`      — KHÔNG AI GỌI
    core/the_cst.py  bằng `libcst`   — app dùng (the_api.py:703 mở tệp, :921 lưu)

Tôi đo cái thứ nhất rồi báo với Sếp rằng app không dựng nổi năm loại thẻ
`nhap · thu · bat_loi · bo_qua · dung_lap`, và `ma_tho` chiếm 22,1%. Số THẬT
của bộ đọc app dùng, trên cùng 5 tệp: 46 · 19 · 26 · 7 · 1, và `ma_tho` chỉ
7,3%. Tôi còn "đính chính" một quan sát ĐÚNG trên màn hình bằng số lấy từ bộ
đọc chết — tức là lấy mã chết bác bỏ thứ nhìn thấy tận mắt.

Mã chết bình thường chỉ tốn chỗ. Mã chết TRÔNG GIỐNG mã thật thì làm người
đọc kết luận sai, và đó là thứ đắt nhất trong ngày hôm ấy.

Phân tích khả đạt từ đúng những gì app + test import: 10/30 mục cấp module của
`the_v1.py` không ai với tới — 588 dòng. Đã xoá. Cửa này giữ cho nó không mọc
lại.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT

# Tên của ba việc chỉ được có ĐÚNG MỘT nơi làm.
TEN_BO_DOC = ("doc_chuoi_py_sang_cay_the", "doc_tep_py_sang_cay_the",
              "luu_cay_the_ra_tep_py")


def _ham_cap_module(p: Path) -> set[str]:
    cay = ast.parse(p.read_text(encoding="utf-8"))
    return {n.name for n in cay.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def test_the_v1_khong_con_bo_doc_thu_hai():
    ten = _ham_cap_module(Path(PROJECT_ROOT, "core", "the_v1.py"))
    thua = sorted(set(TEN_BO_DOC) & ten)
    assert not thua, (
        f"`core/the_v1.py` lại định nghĩa {thua} — đó là bộ đọc thứ hai. "
        "Nó từng làm tôi báo sai với Sếp về chính app này. Nếu cần sửa bộ đọc "
        "thì sửa `core/the_cst.py`, nơi app thật sự gọi."
    )


def test_dung_MOT_module_lam_bo_doc():
    """Quét cả `core/` — không được có module thứ hai làm cùng ba việc ấy."""
    nguoi_lam = {}
    for p in sorted(Path(PROJECT_ROOT, "core").glob("*.py")):
        ten = _ham_cap_module(p)
        chung = set(TEN_BO_DOC) & ten
        if chung:
            nguoi_lam[p.name] = sorted(chung)
    assert list(nguoi_lam) == ["the_cst.py"], (
        f"phải đúng một module làm bộ đọc, đang có: {nguoi_lam}"
    )


def test_the_api_lay_bo_doc_TU_THE_CST():
    """Đây là điều tôi đã không kiểm, và vì thế đo nhầm."""
    nguon = Path(PROJECT_ROOT, "interface", "the_api.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    tu_dau = {}
    for n in ast.walk(cay):
        if isinstance(n, ast.ImportFrom) and n.module:
            for a in n.names:
                if a.name in TEN_BO_DOC:
                    tu_dau[a.name] = n.module
    assert tu_dau, "the_api.py không import hàm đọc nào — app mở tệp bằng gì?"
    for ten, mod in tu_dau.items():
        assert mod == "core.the_cst", (
            f"`the_api.py` lấy `{ten}` từ `{mod}`. Bộ đọc của app phải là "
            "`core.the_cst`; lấy chỗ khác là app chạy một đường, người đo đọc "
            "một đường."
        )


# Mẫu nhỏ mang đủ năm cấu trúc mà tôi từng báo nhầm là app không dựng nổi.
MAU = (
    "import math\n"
    "from os import path as p\n"
    "\n"
    "i = 0\n"
    "while i < 10:\n"
    "    i = i + 1\n"
    "    if i % 2 == 0:\n"
    "        continue\n"
    "    if i > 7:\n"
    "        break\n"
    "\n"
    "try:\n"
    "    x = 1 / 0\n"
    "except ZeroDivisionError as e:\n"
    "    print(e)\n"
)


# ĐẾM chứ không hỏi "có mặt không". Gieo thử 01/09 cho thấy vì sao: mẫu có HAI
# dạng import (`import math` và `from os import path as p`), nên tắt một nhánh
# `cst.Import` mà cửa VẪN XANH — nhánh `cst.ImportFrom` còn sinh ra `nhap`.
# Một khẳng định "có mặt" chỉ cần một nửa cơ chế còn sống là qua.
SO_THE_MONG_DOI = {"nhap": 2, "thu": 1, "bat_loi": 1, "bo_qua": 1, "dung_lap": 1}


@pytest.mark.parametrize("ma_the, so_luong", sorted(SO_THE_MONG_DOI.items()))
def test_bo_doc_that_dung_duoc_nam_the_toi_tung_bao_nham(ma_the, so_luong):
    """Khẳng định theo HÀNH VI, không theo tên hàm.

    Đổi bộ đọc sang một bản yếu hơn thì cửa này đỏ, dù mọi tên gọi vẫn y nguyên
    — đó chính là ca đã lừa tôi.
    """
    import collections

    from core.the_cst import doc_chuoi_py_sang_cay_the

    cay = doc_chuoi_py_sang_cay_the(MAU, "mau.py").tree
    dem = collections.Counter()

    def di(ns):
        for n in ns:
            dem[n.ma] += 1
            if getattr(n, "than", None):
                di(n.than)

    di(cay)
    assert dem[ma_the] == so_luong, (
        f"mẫu phải cho {so_luong} thẻ `{ma_the}`, bộ đọc cho {dem[ma_the]}. "
        f"Cả mẫu ra: {dict(dem)}. Ngày 01/09 tôi báo với Sếp rằng app không "
        "dựng nổi thẻ này — và tôi đã đo nhầm bộ đọc."
    )


def test_ma_tho_khong_duoc_phinh_len():
    """Ngưỡng đăng ký trước: `ma_tho` trên 5 tệp thật đo được 7,3%.

    Để 12% cho chỗ thở. Vượt qua nghĩa là bộ đọc vừa yếu đi — hoặc ai đó vừa
    thay nó bằng bản `ast` cũ, nơi con số này là 22,1%.
    """
    import collections

    from core.the_cst import doc_chuoi_py_sang_cay_the

    d = collections.Counter()
    for t in ("core/dong_ho.py", "core/soi_model.py", "core/the_v1.py",
              "core/web_search.py", "interface/the_app.py"):
        rec = doc_chuoi_py_sang_cay_the(
            Path(PROJECT_ROOT, t).read_text(encoding="utf-8"), t)

        def di(ns):
            for n in ns:
                d[n.ma] += 1
                if getattr(n, "than", None):
                    di(n.than)

        di(rec.tree)

    tong = sum(d.values())
    ty_le = d["ma_tho"] / tong * 100
    assert tong > 1000, f"chỉ đọc được {tong} thẻ — mẫu quá nhỏ để kết luận"
    assert ty_le < 12.0, (
        f"`ma_tho` chiếm {ty_le:.1f}% ({d['ma_tho']}/{tong}). Đo 01/09 là 7,3%; "
        "bản `ast` đã xoá cho 22,1%. Vọt lên nghĩa là bộ đọc vừa yếu đi."
    )
