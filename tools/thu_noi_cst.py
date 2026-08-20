# -*- coding: utf-8 -*-
r"""Nối `the_cst` vào API TRONG BỘ NHỚ rồi đo cửa 5. Không sửa tệp nào.

VÌ SAO — 20/08/2026.

Bốn cửa ĐẠT hết trên `--cst`, nhưng `interface/the_api.py` vẫn nạp `the_v1`, nên
app vẫn chạy bằng `ast` và cửa 5 (đường thật) vẫn phá mã. Không cửa nào trong
bốn cửa phát hiện được rằng THỨ CHÚNG ĐO KHÔNG PHẢI THỨ ĐANG CHẠY.

Tệp này chứng minh một dòng import gỡ được cửa 5, mà không phải sửa tệp
Antigravity đang cầm (luật CLAUDE.md mục 7: đọc trước khi viết đè). Thay hàm
trong bộ nhớ, dựng máy chủ thật bằng `aiohttp.test_utils`, rồi đọc lại tệp từ
đĩa.

Đo được 9/9: đúng 1 dòng đổi, `elif` còn là `elif`, chú thích cuối dòng nguyên
vẹn kể cả khoảng trắng, chú kiểu và giá trị mặc định giữ hết.

MỘT CHI TIẾT BẮT BUỘC khi nối thật: handler lưu gọi
`doc_chuoi_py_sang_cay_the(raw_bytes_goc, ...)` với BYTES, còn `the_cst` nhận
CHUỖI. Bọc lại đúng một chỗ, đừng đổi chữ ký.

    venv\Scripts\python.exe -X utf8 tools\thu_noi_cst.py

Mã thoát 0 đạt / 1 đo được mà không đạt / 2 không đo được.
"""
import sys, io, json, hashlib, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
TAM = GOC / "data" / "the_v1" / "_thu_noi_tam.py"

MAU = (
    "import os\n\n\n"
    "def cong(a: int = 1, b: int = 2) -> int:   # hàm cộng\n"
    "    tong = a + b        # cộng lại\n"
    "    if tong > 10:\n"
    "        return 10\n"
    "    elif tong < 0:      # âm thì kẹp về 0\n"
    "        return 0\n"
    "    else:\n"
    "        return tong\n\n\n"
    'GHI = ["# đây là chuỗi", ""]    # đây mới là chú thích\n'
)

from interface import the_api
from core import the_cst


def _doc_chuoi(nguon, duong_dan=None):
    """API truyền BYTES; the_cst nhận chuỗi. Bọc lại đúng một chỗ."""
    if isinstance(nguon, (bytes, bytearray)):
        nguon = bytes(nguon).decode("utf-8")
    return the_cst.doc_chuoi_py_sang_cay_the(nguon, duong_dan)


the_api.doc_tep_py_sang_cay_the = the_cst.doc_tep_py_sang_cay_the
the_api.doc_chuoi_py_sang_cay_the = _doc_chuoi
the_api.luu_cay_the_ra_tep_py = the_cst.luu_cay_the_ra_tep_py

from aiohttp.test_utils import TestClient, TestServer
from interface.the_app import tao_app


async def chay():
    """Dựng máy chủ thật với bộ đọc LibCST thay trong bộ nhớ, rồi đo cửa 5."""
    TAM.parent.mkdir(parents=True, exist_ok=True)
    TAM.write_text(MAU, encoding="utf-8")
    h = {"X-Auth-Token": the_api.AUTH_TOKEN}
    sv = TestServer(tao_app())
    cl = TestClient(sv)
    await cl.start_server()
    try:
        r = await cl.post("/api/mo_tep", json={"duong_dan": str(TAM)},
                          headers=h)
        d = await r.json()
        print("  1. mở qua API : mã %s" % r.status)
        if r.status != 200:
            print("     %s" % str(d)[:200])
            return 2
        cay = d.get("tree") or []

        def di(ns):
            for n in ns:
                yield n
                yield from di(n.get("than") or [])

        ds = list(di(cay))
        print("     %d thẻ: %s" % (len(ds), sorted({n["ma"] for n in ds})))
        dich = next((n for n in ds if n["ma"] == "neu"
                     and n["o"].get("noi_tiep")), None)
        nhan = "elif" if dich else "if thường"
        if dich is None:
            dich = next(n for n in ds if n["ma"] == "neu")
        print("  2. đổi ô dieu_kien của thẻ %s: %r -> 'tong < -5'"
              % (nhan, dich["o"]["dieu_kien"]))
        dich["o"]["dieu_kien"] = "tong < -5"
        dich["da_sua"] = True

        than = {"duong_dan": str(TAM), "tree": cay,
                "has_modifications": True}
        if "sha256" in d:
            than["expected_sha256"] = d["sha256"]
        r2 = await cl.post("/api/luu_tep", json=than, headers=h)
        d2 = await r2.json()
        print("  3. lưu qua API: mã %s" % r2.status)
        if r2.status != 200:
            print("     %s" % str(d2)[:250])
            return 1

        tren_dia = TAM.read_text(encoding="utf-8")
        g, rr = MAU.splitlines(), tren_dia.splitlines()
        doi = [i + 1 for i in range(min(len(g), len(rr))) if g[i] != rr[i]]
        print("  4. đọc TỪ ĐĨA : %d dòng đổi %s" % (len(doi), doi))
        for i in doi:
            print("       gốc: %r" % g[i - 1])
            print("       nay: %r" % rr[i - 1])
        print()
        kt = [
            ("giá trị mới thật sự trên đĩa", "tong < -5" in tren_dia),
            ("chỉ 1 dòng đổi", len(doi) == 1),
            ("giữ elif", "    elif tong < -5:" in tren_dia
             or "    if tong < -5:" in tren_dia and nhan == "if thường"),
            ("giữ chú thích dòng elif", "# âm thì kẹp về 0" in tren_dia),
            ("giữ chú kiểu + mặc định", "a: int = 1, b: int = 2" in tren_dia),
            ("giữ kiểu trả về", "-> int" in tren_dia),
            ("giữ chú thích của def", "# hàm cộng" in tren_dia),
            ("giữ dấu thăng trong chuỗi", '"# đây là chuỗi"' in tren_dia),
            ("số dòng không đổi", len(g) == len(rr)),
        ]
        for t, ok in kt:
            print("     %-32s %s" % (t, "ĐẠT" if ok else "*** TRƯỢT ***"))
        return 0 if all(k[1] for k in kt) else 1
    finally:
        await cl.close()
        TAM.unlink(missing_ok=True)


print("=" * 62)
print("  THỬ NỐI the_cst VÀO API (trong bộ nhớ, không sửa tệp)")
print("=" * 62)
ma = asyncio.run(chay())
print()
print("  %s" % ("ĐƯỜNG THẬT ĐẠT — một dòng import gỡ được cửa 5"
                if ma == 0 else "vẫn TRƯỢT (mã %d)" % ma))
raise SystemExit(ma)
