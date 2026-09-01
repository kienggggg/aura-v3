# -*- coding: utf-8 -*-
"""Đếm dòng phải đếm XUỐNG DÒNG THẬT, không dùng `str.splitlines()`.

VÌ SAO CÓ TỆP NÀY. Ngày 01/09/2026, `tools/do_cua_cung_the.py` báo cửa 4 TRƯỢT
với **327 thẻ "tả sai"** — nghĩa là sửa một ô thì vết sửa lan ra ngoài thẻ ấy.
Một con số đủ lớn để nghĩ rằng bộ lưu đang hỏng.

Đào ra thì cả 327 nằm gọn trong MỘT tệp, và nguyên nhân là MỘT ký tự:

    interface/the_api.py có `bai_tap_cua_toi\\x0bi_du.py` trong một chú thích.

`\\x0b` là tab dọc. Ai đó viết `"...bai_tap_cua_toi\\vi_du.py"` trong một chuỗi
Python — `\\v` là escape của tab dọc, nên `/v` bị nuốt mất.

`str.splitlines()` **tách trên tám ký tự ngoài xuống dòng**: `\\v` `\\f` `\\x1c`
`\\x1d` `\\x1e` `\\x85` `\\u2028` `\\u2029`. libcst và trình soạn thảo thì không.
Một ký tự ấy làm bộ đo đếm 1513 dòng trong khi tệp có 1512 — lệch một dòng, và
MỌI thẻ nằm sau nó đều bị chấm trượt:

    trước khi sửa   690 thẻ, 327 SAI  (chu_thich 90 · gan 134 · goi_ham 21 · tra_ve 82)
    sau khi sửa     690 thẻ,   0 SAI

Hai bản vá, hai đầu khác nhau: bỏ ký tự lạ khỏi nguồn, VÀ dạy bộ đo đừng để bị
lừa. Chỉ làm cái thứ nhất thì lần sau có tệp khác dính là lại 327.

Bài học chung: một phép đo trả về con số lớn đáng ngờ thì nghi MÁY ĐO trước.
327/8288 thẻ "tả sai" mà tập trung hết vào một tệp — phân bố ấy đã đủ để nghi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT

sys.path.insert(0, str(Path(PROJECT_ROOT, "tools")))

# Tám ký tự `str.splitlines()` tách thêm, ngoài `\n` `\r\n` `\r`.
TACH_THEM = ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", " ", " "]


def test_bo_tach_dong_ton_tai_va_dung_moi_noi():
    """Không còn chỗ nào trong công cụ dùng thẳng `str.splitlines()`."""
    nguon = Path(PROJECT_ROOT, "tools", "do_cua_cung_the.py").read_text(encoding="utf-8")
    ma = "\n".join(d for d in nguon.splitlines()
                   if not d.lstrip().startswith("#"))
    # Bỏ docstring của chính hàm `_tach_dong` — nó GIẢI THÍCH tại sao không
    # dùng `splitlines()`, nên dò thô sẽ tự bắt lời giải thích.
    i = ma.find("def _tach_dong(")
    assert i > 0, "thiếu hàm `_tach_dong` — công cụ vẫn đếm dòng bằng splitlines()"
    j = ma.find("\ndef ", i + 1)
    ngoai = ma[:i] + ma[j:]
    assert ".splitlines()" not in ngoai, (
        "còn chỗ dùng `str.splitlines()` ngoài `_tach_dong`. Nó tách thêm trên "
        "tám ký tự mà libcst coi là ký tự giữa dòng — lệch một dòng là mọi thẻ "
        "phía sau bị chấm trượt (đo 01/09: 327 thẻ)."
    )


@pytest.mark.parametrize("ky_tu", TACH_THEM)
def test_tach_dong_KHONG_cat_tren_tam_ky_tu_kia(ky_tu):
    from do_cua_cung_the import _tach_dong

    # KHÔNG có xuống dòng ở cuối, và so NỘI DUNG chứ không so SỐ LƯỢNG.
    #
    # Bản đầu để một `\n` ở cuối rồi so `len(...)`. Gieo thử chứng minh nó MÙ:
    # dấu xuống dòng cuối làm `split` đẻ thêm một phần tử rỗng, còn
    # `splitlines()` bỏ phần tử ấy nhưng đẻ thêm một phần tử do cắt trên
    # `ky_tu` — hai bên tình cờ bằng nhau (4 = 4). Thay cả thân `_tach_dong`
    # bằng `splitlines()` mà cửa vẫn xanh.
    nguon = f"a = 1\nb = 'x{ky_tu}y'\nc = 3"
    mong = ["a = 1", f"b = 'x{ky_tu}y'", "c = 3"]
    assert _tach_dong(nguon) == mong, (
        f"`_tach_dong` cắt trên {ky_tu!r} — đúng cái bẫy nó sinh ra để tránh"
    )
    assert nguon.splitlines() != mong, (
        "ca đối chứng: `splitlines()` PHẢI cho kết quả KHÁC, nếu không thì "
        f"{ky_tu!r} không phải ký tự nó tách và phép thử này chứng minh rỗng"
    )


@pytest.mark.parametrize("kieu", ["\n", "\r\n", "\r"])
def test_tach_dong_VAN_cat_tren_xuong_dong_that(kieu):
    from do_cua_cung_the import _tach_dong

    assert _tach_dong(f"a{kieu}b{kieu}c") == ["a", "b", "c"], (
        f"không cắt trên {kieu!r} thì bộ đo coi cả tệp là một dòng"
    )


def test_khong_tep_nguon_nao_con_ky_tu_ngat_dong_la():
    """Nguồn của repo không được chứa tám ký tự ấy.

    Chúng lọt vào một cách lặng lẽ — `\\v` trong một chuỗi Python trông y hệt
    một dấu gạch chéo và chữ v. Không trình soạn thảo nào vẽ chúng ra.
    """
    bo = {"venv", ".git", "__pycache__", "node_modules", "data", "build", "dist"}
    dinh = []
    for p in Path(PROJECT_ROOT).rglob("*.py"):
        if any(x in p.parts for x in bo):
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Bỏ chính tệp này: nó PHẢI chứa tám ký tự ấy để thử được.
        if p.name == Path(__file__).name:
            continue
        co = [repr(k) for k in TACH_THEM if k in s]
        if co:
            dinh.append(f"{p.relative_to(PROJECT_ROOT)}: {', '.join(co)}")
    assert not dinh, (
        "tệp nguồn chứa ký tự ngắt dòng lạ:\n  " + "\n  ".join(dinh) +
        "\nMột ký tự như thế trong `interface/the_api.py` đã làm cửa 4 báo "
        "327 thẻ tả sai, trong khi không thẻ nào tả sai thật."
    )
