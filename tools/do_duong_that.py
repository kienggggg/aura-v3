# -*- coding: utf-8 -*-
r"""CỬA 5 — đường THẬT: UI -> JSON -> API -> tệp trên đĩa.

VÌ SAO CÓ CỬA NÀY — 20/08/2026, Codex bắt được và bắt đúng.

Bốn cửa trong `do_cua_cung_the.py` đặt `da_sua` THẲNG lên đối tượng Python. Chúng
chứng minh bộ đọc/ghi chạy được, KHÔNG chứng minh app chạy được — giữa hai chỗ ấy
còn `TheNode.from_dict()` và hai handler HTTP, và lỗi hoàn toàn có thể nằm ở đó.

Cửa này dựng máy chủ thật, gọi HTTP thật, rồi đọc lại tệp TỪ ĐĨA.

Đo lần đầu 20/08: bốn cửa kia ĐẠT hết trên `the_cst`, mà đường thật vẫn phá mã —
vì `interface/the_api.py` còn nạp `the_v1`. Không cửa nào trong bốn cửa kia phát
hiện được chuyện đó.

    venv\Scripts\python.exe -X utf8 tools\do_duong_that.py

Mã thoát: 0 đạt · 1 đo được mà không đạt · 2 không đo được (máy chủ không lên).
"""
import sys, io, json, time, hashlib, urllib.request, urllib.error, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
CONG = 8097
TAM = GOC / "data" / "the_v1" / "_e2e_tam.py"

MAU = (
    "import os\n"
    "\n"
    "\n"
    "def cong(a: int = 1, b: int = 2) -> int:   # hàm cộng\n"
    "    tong = a + b        # cộng lại\n"
    "    if tong > 10:\n"
    "        return 10\n"
    "    elif tong < 0:      # âm thì kẹp về 0\n"
    "        return 0\n"
    "    else:\n"
    "        return tong\n"
    "\n"
    "\n"
    'GHI = ["# đây là chuỗi", ""]    # đây mới là chú thích\n'
)


def goi(duong, than, tok):
    r = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (CONG, duong),
        data=json.dumps(than).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Auth-Token": tok},
        method="POST")
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {"loi": e.read().decode("utf-8", "replace")[:200]}
    except Exception as e:
        return -1, {"loi": repr(e)[:200]}


def di(ns):
    for n in ns:
        yield n
        yield from di(n.get("than") or [])


TAM.parent.mkdir(parents=True, exist_ok=True)
TAM.write_text(MAU, encoding="utf-8")
goc_b = TAM.read_bytes()

nk = subprocess.Popen(
    [str(GOC / "venv" / "Scripts" / "python.exe"), "-X", "utf8", "-u",
     "-m", "interface.the_app", "--port", str(CONG), "--no-browser"],
    cwd=str(GOC), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, encoding="utf-8", errors="replace")
tok = ""
t0 = time.time()
while time.time() - t0 < 40:
    d = nk.stdout.readline()
    if not d:
        break
    if "thông hành" in d or "hanh" in d.lower():
        tok = d.strip().split(":")[-1].strip()
        break
if not tok:
    print("KHÔNG ĐO ĐƯỢC: máy chủ không khởi động")
    nk.kill()
    TAM.unlink(missing_ok=True)
    raise SystemExit(2)

try:
    print("=" * 64)
    print("  ĐƯỜNG THẬT — UI -> JSON -> API -> tệp")
    print("=" * 64)

    ma, ra = goi("/api/mo_tep", {"duong_dan": str(TAM)}, tok)
    print("  1. mở tệp qua API      : mã %s" % ma)
    if ma != 200:
        print("     %s" % ra)
        raise SystemExit(1)
    cay = ra.get("tree") or []
    if not cay:
        print("     KHÔNG THẤY cây thẻ trong phản hồi. Khoá có:",
              list(ra.keys())[:8])
        raise SystemExit(1)
    ds = list(di(cay))
    print("     %d thẻ, các loại: %s"
          % (len(ds), sorted({n["ma"] for n in ds})))

    # tìm thẻ elif (thẻ hay hỏng nhất ở bản v1) rồi ĐỔI ĐIỀU KIỆN
    dich = next((n for n in ds
                 if n["ma"] == "neu" and n["o"].get("noi_tiep")), None)
    if dich is None:
        dich = next((n for n in ds if n["ma"] == "neu"), None)
    if dich is None:
        print("     không có thẻ Nếu nào để thử")
        raise SystemExit(1)
    print("  2. đổi ô trong JSON    : thẻ %s dòng %s, dieu_kien %r -> %r"
          % (dich["ma"], (dich.get("vi_tri") or {}).get("line_start"),
             dich["o"].get("dieu_kien"), "tong < -5"))
    dich["o"]["dieu_kien"] = "tong < -5"
    dich["da_sua"] = True

    than = {"duong_dan": str(TAM), "tree": cay, "has_modifications": True}
    for k in ("sha256", "sha", "version", "phien_ban"):
        if k in ra:
            than[k] = ra[k]
    ma2, ra2 = goi("/api/luu_tep", than, tok)
    print("  3. lưu qua API         : mã %s" % ma2)
    if ma2 != 200:
        print("     %s" % ra2)
        raise SystemExit(1)

    tren_dia = TAM.read_text(encoding="utf-8")
    g, r = MAU.splitlines(), tren_dia.splitlines()
    doi = [i + 1 for i in range(min(len(g), len(r))) if g[i] != r[i]]
    print("  4. đọc lại TỪ ĐĨA      : %d dòng đổi %s" % (len(doi), doi))
    for i in doi:
        print("       gốc: %r" % g[i - 1])
        print("       nay: %r" % r[i - 1])

    print()
    kt = [
        ("giá trị mới THẬT SỰ trên đĩa", "tong < -5" in tren_dia),
        ("chỉ 1 dòng đổi", len(doi) == 1),
        ("giữ `elif`, không thành else/if", "    elif tong < -5:" in tren_dia),
        ("giữ chú thích trên dòng elif", "# âm thì kẹp về 0" in tren_dia),
        ("giữ chú kiểu + mặc định", "a: int = 1, b: int = 2" in tren_dia),
        ("giữ kiểu trả về", "-> int" in tren_dia),
        ("giữ chú thích của def", "# hàm cộng" in tren_dia),
        ("giữ dấu thăng trong chuỗi", '"# đây là chuỗi"' in tren_dia),
        ("số dòng không đổi", len(g) == len(r)),
    ]
    for ten, ok in kt:
        print("     %-34s %s" % (ten, "ĐẠT" if ok else "*** TRƯỢT ***"))
    print()
    print("  %s" % ("ĐƯỜNG THẬT ĐẠT" if all(k[1] for k in kt)
                    else "ĐƯỜNG THẬT TRƯỢT"))
    ma_thoat = 0 if all(k[1] for k in kt) else 1
except SystemExit as e:
    ma_thoat = int(e.code or 1)
finally:
    nk.kill()
    TAM.unlink(missing_ok=True)
raise SystemExit(ma_thoat)
