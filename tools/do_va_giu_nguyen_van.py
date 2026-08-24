# -*- coding: utf-8 -*-
"""tools/do_va_giu_nguyen_van.py — bản vá E1 có giữ nguyên văn tệp không?

Ngày 24/08/2026, E1 công bố "sửa 2 dòng" nhưng thứ nó ghi lên bản sao tạm là
`ast.unparse` CẢ TỆP:

    tệp            diff công bố   khác thật   chú thích     dòng ma thuật
    dong_ho.py         2 dòng      24 dòng      1 -> 0          MẤT
    may_tinh.py        2 dòng     231 dòng     50 -> 0          MẤT
    web_search.py      2 dòng     409 dòng     94 -> 0          MẤT

Cả ba bản vá đều ĐÚNG (`AST(ma) == AST(gốc)` 3/3) — suite đỏ chỉ vì chuẩn hoá.
Bốn mốc lọc `65->15 · 87->28 · 1->1 · 10->2` KHÔNG hề xê dịch, nên ngưỡng cũ
không bắt được gì. Tệp này là ngưỡng bắt được.

Vì sao đo được dù không giữ bản sao đã gieo lỗi: `do_cua_cung_e1_app.gieo_ma`
gieo bằng `oracle_lat_van_ban` — cũng lật trên VĂN BẢN — nên bản đã gieo lỗi
có đúng số dòng và đúng số chú thích như tệp thật. Đã kiểm 24/08 trên
`core/dong_ho.py`: gieo xong vẫn 40 dòng, 1 chú thích, dòng ma thuật còn.

    ĐẠT (0)              mọi ứng viên giữ nguyên văn
    KHÔNG ĐẠT (1)        có ứng viên làm rụng chú thích / đổi số dòng
    KHÔNG ĐO ĐƯỢC (2)    không tìm thấy sổ, hoặc sổ thiếu trường `ma`
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent


def dem_chu_thich(s: str) -> int:
    return sum(1 for d in s.splitlines() if d.strip().startswith("#"))


def dem_dong_khac(a: str, b: str) -> int:
    import difflib
    return sum(
        1
        for d in difflib.unified_diff(a.splitlines(), b.splitlines(), n=0)
        if d[:1] in "+-" and d[:3] not in ("---", "+++")
    )


def main() -> int:
    # Nhận đường dẫn một lượt chạy cụ thể, để còn chấm lại lượt cũ mà kiểm xem
    # cửa này có HỎNG ĐƯỢC không. Cửa không hỏng được là cửa vô dụng.
    if len(sys.argv) > 1:
        lan = Path(sys.argv[1])
        if not lan.is_dir():
            print(f"KHÔNG ĐO ĐƯỢC: không có thư mục {lan}")
            return 2
    else:
        runs = sorted(glob.glob(str(REPO / "data/evidence_sprint/runs/e1_app_*")))
        if not runs:
            print("KHÔNG ĐO ĐƯỢC: chưa có lượt chạy nào dưới data/evidence_sprint/runs/")
            return 2
        lan = Path(runs[-1])
    so = sorted(glob.glob(str(lan / "raw" / "*_e1_raw.json")))
    if not so:
        print(f"KHÔNG ĐO ĐƯỢC: {lan.name} không có tệp raw nào")
        return 2

    print("=" * 70)
    print(f"  BẢN VÁ E1 CÓ GIỮ NGUYÊN VĂN KHÔNG — {lan.name}")
    print("=" * 70)
    print()
    print("%-14s %-5s %8s %10s %9s %9s" % ("tệp", "ứng", "chú/gốc", "dòng/gốc", "dòng-1", "diff"))

    tong = 0
    hong = 0
    thieu_ma = 0

    for f in so:
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        ten = os.path.basename(f).replace("_e1_raw.json", "")
        cands = j.get("candidates") or []
        if not cands:
            print("%-14s %-5s %8s %10s %9s %9s" % (ten, "0", "-", "-", "-", "-"))
            continue

        goc_path = REPO / j["source_path"]
        if not goc_path.is_file():
            print(f"{ten:<14} KHÔNG ĐO ĐƯỢC: thiếu {j['source_path']}")
            thieu_ma += 1
            continue
        goc = goc_path.read_text(encoding="utf-8")
        c_goc, d_goc = dem_chu_thich(goc), len(goc.splitlines())

        for c in cands:
            tong += 1
            ma = c.get("ma")
            if not isinstance(ma, str):
                thieu_ma += 1
                continue

            c_ma, d_ma = dem_chu_thich(ma), len(ma.splitlines())
            ma_thuat = bool(ma.splitlines()) and ma.splitlines()[0].strip().startswith("#")
            goc_co_ma_thuat = goc.splitlines()[0].strip().startswith("#")
            n_diff = dem_dong_khac(goc, ma)

            # Bản vá lật đúng một token nên chỉ được lệch đúng 2 dòng (một -, một +).
            # Nếu nó trùng luôn chỗ đã gieo lỗi thì 0 dòng — cũng hợp lệ.
            dat = (
                c_ma == c_goc
                and d_ma == d_goc
                and (ma_thuat or not goc_co_ma_thuat)
                and n_diff <= 2
            )
            if not dat:
                hong += 1
            print("%-14s #%-4s %8s %10s %9s %9s   %s" % (
                ten, c.get("index", "?"),
                f"{c_ma}/{c_goc}", f"{d_ma}/{d_goc}",
                "còn" if ma_thuat else "MẤT",
                n_diff,
                "" if dat else "<- HỎNG",
            ))

    print()
    print("-" * 70)
    print(f"  ứng viên đo được : {tong - thieu_ma}")
    print(f"  giữ nguyên văn   : {tong - thieu_ma - hong}")
    print(f"  HỎNG             : {hong}")
    if thieu_ma:
        print(f"  thiếu trường `ma`: {thieu_ma}  (không đo được)")
    print("-" * 70)

    if thieu_ma and tong == thieu_ma:
        print("  KHÔNG ĐO ĐƯỢC")
        return 2
    if hong:
        print("  KHÔNG ĐẠT")
        return 1
    if tong == 0:
        print("  KHÔNG ĐO ĐƯỢC: không lượt nào sinh ứng viên")
        return 2
    print("  ĐẠT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
