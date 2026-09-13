# -*- coding: utf-8 -*-
"""Bộ cắt không được xoá truyện — `CHOT:bo-cat-giu-truyen` (13/09/2026).

Lời nhắc xin 320 từ, model viết trung vị 460; bộ cắt bỏ trung vị 48 % số câu,
cách một câu bỏ một câu, bắt đầu từ câu thứ 2 — đúng câu đặt nhân vật. Bài này
giữ ngưỡng đúng như lúc đăng ký.
"""
from __future__ import annotations

import hashlib
import re

import pytest

import core.viet_truyen as vt
from core.paths import PROJECT_ROOT

# SHA-256 (16 ký tự đầu) của đúng lời nhắc đã đem đi đo 13/09 — tính TRƯỚC khi
# sửa mã sản phẩm, từ bản máy đo tự ghép. Mã sản phẩm phải ra đúng từng byte.
SHA_LOI_DA_DO = {
    "chiếc la bàn gãy kim": "53E04B7A10F227E7",
    "người thợ sửa khoá đầu ngõ": "A25FA95A52A15EB8",
}

# Chép TAY từ `CHOT:bo-cat-giu-truyen` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "tỉ lệ câu bị cắt, trung vị, lời nhắc C + bộ cắt mới": "≤ 0,15",
    "lọt cửa một lần sinh, 15 lượt": "C + cắt mới ≥ 0 + cắt cũ − 2",
    "bộ cắt mới bỏ 2 câu đầu hoặc 2 câu cuối": "0 lần",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:bo-cat-giu-truyen -->(.*?)<!-- /CHOT:bo-cat-giu-truyen -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:bo-cat-giu-truyen"
    return m.group(1)


def test_BA_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


@pytest.mark.parametrize("de", SHA_LOI_DA_DO)
def test_LOI_TRUYEN_dung_TUNG_BYTE_ban_da_do(de):
    assert hashlib.sha256(vt._loi_truyen(de).encode("utf-8")).hexdigest()[:16].upper() == SHA_LOI_DA_DO[de]


def test_BAI_NOI_chua_doi_vong_nay():
    loi = vt._loi_bai_noi("X")
    assert "320" in loi and "ít nhất 18 câu" in loi, loi


@pytest.mark.parametrize(("vao", "ra"), [
    ("1. Một hai ba.\n2. Bốn năm sau.", "Một hai ba. Bốn năm sau."),
    ("2) Một hai.\n**3.** Ba bốn.", "Một hai. Ba bốn."),
    ("1. Một hai ba\n2. Bốn.", "Một hai ba. Bốn."),
    ("1. A b.\n\n\n2. C d.", "A b. C d."),
    # Dấu chấm hàng nghìn GIỮA câu: chỉ ăn ở đầu dòng.
    ("1. Giá 10.000 đồng.", "Giá 10.000 đồng."),
    ("Không đánh số.\nDòng hai.", "Không đánh số. Dòng hai."),
])
def test_BO_SO_THU_TU(vao, ra):
    assert vt.bo_so_thu_tu(vao) == ra


def _cau(n: int, so_tu: int) -> list:
    return [f"Câu{i:02d} " + " ".join(["chữ"] * (so_tu - 2)) + " hết." for i in range(n)]


@pytest.mark.parametrize("n", range(5, 41))
def test_CAT_GIU_TRUYEN_khong_bao_gio_dung_2_cau_dau_2_cau_cuoi(n):
    cau = _cau(n, 40)                      # 40 từ/câu: buộc cắt SÂU
    van, bo = vt.cat_giu_truyen(" ".join(cau))
    con = vt._tach_cau(van)
    assert con[:2] == cau[:2] and con[-2:] == cau[-2:], f"n={n}: đụng câu đầu/cuối"
    assert len(con) == n - bo


def test_CAT_GIU_TRUYEN_het_cau_giua_van_dai_thi_DUNG_chu_khong_an_vao_hai_dau():
    """Thêm sau lượt gieo đầu: bỏ hàng rào mà bài trên VẪN XANH.

    Câu dài đều nhau thì cắt từ giữa ra tự để lại hai đầu — hàng rào không bao
    giờ phải làm việc. Nó chỉ làm việc khi câu Ở HAI ĐẦU dài mà câu giữa ngắn:
    4 × 65 + 10 × 10 = 360 từ, trung bình 25,7 — cắt hết phần giữa vẫn 260 từ.
    Ca ấy lọt được trần 22,7 nếu phần giữa đông hơn, nên nó có thật trong luồng.
    """
    dai, ngan = _cau(4, 65), _cau(10, 10)
    cau = dai[:2] + [c.replace("Câu", "Giữa") for c in ngan] + dai[2:]
    van, bo = vt.cat_giu_truyen(" ".join(cau))
    con = vt._tach_cau(van)
    assert bo == 10
    assert con == dai, "hết câu giữa mà vẫn ăn vào hai đầu"


def test_CAT_GIU_TRUYEN_cat_tu_GIUA_ra_thanh_MOT_lo_lien():
    cau = _cau(30, 12)                     # 360 từ -> phải bỏ ~10 câu
    van, bo = vt.cat_giu_truyen(" ".join(cau))
    con = set(vt._tach_cau(van))
    mat = [i for i, c in enumerate(cau) if c not in con]
    assert bo == len(mat) > 0
    assert 15 in mat, "không bắt đầu từ giữa"
    assert mat == list(range(mat[0], mat[-1] + 1)), f"lỗ thủng không liền: {mat}"
    assert len(van.split()) <= vt.SO_TU_MAX


def test_CAT_GIU_TRUYEN_de_nguyen_ban_da_vua():
    van = " ".join(_cau(13, 18))           # 234 từ
    assert vt.cat_giu_truyen(van) == (van, 0)


def _gia_model(monkeypatch, ban):
    monkeypatch.setattr("core.viet_truyen._xin_model", lambda loi, hat: (ban, 1.0))


def test_TRUYEN_bo_so_roi_moi_cham_va_KHONG_de_so_lot_vao_video(monkeypatch):
    dong = [f"{i}. Ông lão số {i} bước chậm qua phố ướt, mưa rơi lộp độp trên mái tôn cũ suốt buổi chiều."
            for i in range(1, 14)]
    _gia_model(monkeypatch, "\n".join(dong))
    kq = vt.viet_kich_ban("ông lão")
    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert not re.search(r"(^|\s)\d{1,2}\.\s", kq["van_ban"]), kq["van_ban"][:120]
    # 13 × 20 = 260 từ -> phải cắt đúng 1 câu. Bộ cắt CŨ bỏ câu thứ 2 trước tiên
    # — đúng câu đặt nhân vật; bộ cắt mới bỏ câu giữa.
    assert kq["so"]["so_cau"] == 12
    assert "Ông lão số 2 " in kq["van_ban"], "truyện đang dùng bộ cắt cũ: mất câu thứ 2"


def test_BAI_NOI_van_dung_BO_CAT_CU(monkeypatch):
    """Phạm vi: bộ cắt mới chỉ đo cho truyện. Bài nói phải ra đúng như `cat_cho_vua`."""
    tho = " ".join(f"Ông lão giải thích điều số {i} bằng mười hai chữ đơn giản dễ nghe thôi."
                   for i in range(30))
    _gia_model(monkeypatch, tho)
    kq = vt.viet_kich_ban("ông lão", the_loai="bai_noi")
    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert kq["van_ban"] == vt.cat_cho_vua(tho)[0]
    assert kq["van_ban"] != vt.cat_giu_truyen(tho)[0], "hai bộ cắt ra giống nhau — bài này mù"
