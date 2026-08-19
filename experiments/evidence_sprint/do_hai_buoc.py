# -*- coding: utf-8 -*-
"""Tách bước CHỌN THẺ khỏi bước VIẾT MÃ, và ghi lại cả hai để soi từng đề.

GIẢ THUYẾT ĐANG ĐO. Lượt hỏi-vì-sao 19/08 trên 5 đề hỏng:

    2/5 đề: HỎI thì chọn ĐÚNG thẻ, mà lúc VIẾT MÃ lại không dùng
    3/5 đề: hỏi cũng chọn sai

Nhóm 2/5 nói rằng model BIẾT thẻ nào đúng nhưng đánh rơi nó trong lúc viết —
chỗ hỏng ở bước viết, không ở khay. Nếu đúng thì tách hai bước sẽ cứu được
nhóm đó: bước 1 chỉ chọn, bước 2 chỉ viết, và bước 2 chỉ còn ĐÚNG MỘT thẻ
trước mắt nên không đánh rơi được nữa.

    MỘT BƯỚC   khay -> "viết hàm dùng thẻ trong khay"          (đã đo: 22/28)
    HAI BƯỚC   khay -> "chọn MỘT thẻ"  ->  thẻ đó -> "viết hàm"

BỐN Ô, không gộp — mỗi ô một cách chữa khác nhau:

    chọn ĐÚNG + dùng thẻ đã chọn   -> ĐẠT
    chọn ĐÚNG + KHÔNG dùng         -> vẫn đánh rơi, tách bước không cứu
    chọn SAI  + dùng thẻ đã chọn   -> hỏng ở bước CHỌN, khay chưa đủ phân biệt
    chọn SAI  + KHÔNG dùng         -> hỏng cả hai bước

VÌ SAO CHỈ 8 ĐỀ: Sếp bắt được rằng lượt trước tôi chạy một mạch 84 lượt mà chỉ
soi 2 đề. Lượt này chạy ít, ghi đủ, đọc hết, rồi mới mở rộng.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_hai_buoc.py [so_de]
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import bang_khay, sinh_khay                  # noqa: E402
from do_khay_loc import _boc_rao, dung_ham_kho, goi_ham_nao     # noqa: E402

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
GOC = Path(__file__).resolve().parent.parent.parent
NHA = Path(__file__).resolve().parent
DE = [tuple(x) for x in json.loads(
    (NHA / "de_khay.json").read_text(encoding="utf-8"))["de"]]


def hoi(p: str, tran: int) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": tran,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=900) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def buoc_chon(khay, viec: str) -> tuple[str, str, float]:
    """Bước 1: CHỈ chọn thẻ. Không viết một dòng mã nào."""
    p = (f"Bạn chọn công cụ cho dự án AURA.\n\n"
         f"KHAY HÀM CÓ SẴN:\n{bang_khay(khay)}\n\n"
         f"Việc cần làm: {viec}\n\n"
         f"ĐỪNG viết mã. Trả lời đúng hai dòng:\n"
         f"CHON: <tên đúng một hàm trong khay>\n"
         f"VISAO: <một câu ngắn>\n")
    ra, g = hoi(p, 160)
    ten_co = {t.ten for t in khay}
    chon = ""
    for d in ra.splitlines():
        if d.strip().upper().startswith("CHON"):
            t = d.split(":", 1)[-1].strip().strip("`*. ")
            chon = t.split("(")[0].split(".")[-1].strip()
            break
    # Model có thể gọi tên một hàm không có trong khay — ghi lại, đừng sửa hộ.
    return (chon if chon in ten_co else chon), ra, g


def buoc_viet(the, ten_ham: str, viec: str) -> tuple[str, float]:
    """Bước 2: CHỈ viết mã, và chỉ còn MỘT thẻ trước mắt."""
    p = (f"Bạn viết mã Python cho dự án AURA.\n\n"
         f"HÀM PHẢI DÙNG:\n{the.dong_khay()}\n\n"
         f"Viết hàm `{ten_ham}` để {viec}.\n"
         f"Bắt buộc gọi hàm ở trên, nhớ `from {the.mo_dun} import {the.ten}`.\n"
         f"CHỈ trả về mã Python.\n")
    ra, g = hoi(p, 320)
    return _boc_rao(ra), g


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    khay = sinh_khay(GOC)
    theo_ten = {t.ten: t for t in khay}
    de = DE[:n]
    print(f"  {len(de)} đề · khay {len(khay)} thẻ · hai bước\n")

    so = []
    o = {"dat": 0, "chon_dung_khong_dung": 0, "chon_sai_dung_the": 0, "hong_ca_hai": 0}
    for ten, viec, can in de:
        chon, loi1, g1 = buoc_chon(khay, viec)
        chon_dung = chon == can
        the = theo_ten.get(chon)
        if the is None:
            ma, g2 = "", 0.0
            dung_the_chon = False
        else:
            ma, g2 = buoc_viet(the, ten, viec)
            dung_the_chon = chon in goi_ham_nao(ma)
        dat = dung_ham_kho(ma, can) if ma else False

        if dat:
            o["dat"] += 1
        elif chon_dung and not dung_the_chon:
            o["chon_dung_khong_dung"] += 1
        elif not chon_dung and dung_the_chon:
            o["chon_sai_dung_the"] += 1
        else:
            o["hong_ca_hai"] += 1

        print(f"  --- {ten}   cần `{can}`")
        print(f"      bước 1 CHỌN : {chon or '(không nói)':<28}"
              f"{'ĐÚNG' if chon_dung else 'sai'}   {g1:.0f}s")
        print(f"      bước 2 VIẾT : {'dùng thẻ đã chọn' if dung_the_chon else 'KHÔNG dùng thẻ đã chọn':<28}"
              f"{'ĐẠT' if dat else 'trượt'}   {g2:.0f}s")
        vs = next((d.strip() for d in loi1.splitlines()
                   if d.strip().upper().startswith("VISAO")), "")
        if vs:
            print(f"      {vs[:120]}")
        print()
        so.append({"de": ten, "can": can, "chon": chon, "chon_dung": chon_dung,
                   "dung_the_chon": dung_the_chon, "dat": dat,
                   "loi_chon": loi1, "ma": ma, "giay": round(g1 + g2, 1)})
        (NHA / "so_hai_buoc.json").write_text(
            json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")

    print("  ===== BỐN Ô =====")
    for k, v in o.items():
        print(f"    {k:<26}{v}/{len(de)}")
    print(f"\n    bước 1 chọn đúng: {sum(1 for x in so if x['chon_dung'])}/{len(de)}")
    print(f"    một bước (đã đo) : 22/28 = 79%")
    print(f"    hai bước         : {o['dat']}/{len(de)} = {100*o['dat']/len(de):.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
