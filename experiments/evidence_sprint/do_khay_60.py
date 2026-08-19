# -*- coding: utf-8 -*-
"""Khay 60 thẻ: tổ hợp có cắn không?

Lượt 2 (`do_khay_the_kho.py`) đo khay **6 thẻ**, mỗi đề đúng một thẻ:

    A tự do      gọi đúng hàm 0/6
    B khay thẻ   gọi đúng hàm 6/6

Nhưng 6 thẻ thì gần như không phải chọn. Câu Sếp hỏi 19/08: **khi khay to lên
thì tổ hợp có cắn không.** Lượt này đổi ĐÚNG MỘT BIẾN: khay từ 6 lên 60 thẻ,
đề giữ nguyên, chấm giữ nguyên.

Sáu thẻ đúng vẫn nằm trong khay — chỉ bị vùi giữa 54 thẻ nhiễu, đều là hàm CÓ
THẬT trong `core/`, `interface/`, `tools/` nên tên nào cũng nghe hợp lý. Đây là
phép thử nhiễu, không phải phép thử bẫy.

BA MỨC ĐỂ THẤY TỔ HỢP CẮN Ở ĐÂU:
    6  thẻ   (lượt trước, để so)
    20 thẻ
    60 thẻ

LUẬT ĐẶT TRƯỚC KHI CHẠY:
    nếu 60 thẻ vẫn >= 5/6  -> khay to KHÔNG cắn ở cỡ này
    nếu tụt xuống 3-4/6    -> bắt đầu cắn, cần bước lọc khay trước khi đưa model
    nếu <= 2/6             -> khay to vô dụng nếu không lọc

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_khay_60.py
"""
from __future__ import annotations

import ast
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
GOC = Path(__file__).resolve().parent

DE = [
    ("tra_loi_gio", "trả lời câu hỏi về ngày giờ hiện tại", "cau_gio"),
    ("tra_loi_phep_tinh", "trả lời một câu hỏi có chứa phép tính", "tinh_giup"),
    ("hoi_luot_truoc", "trả lời câu hỏi của người dùng về các lượt chat trước đó", "tra_so"),
    ("co_duoc_tra_mang", "quyết định câu hỏi này có được phép đẩy ra máy tìm kiếm không",
     "la_chuyen_rieng_cua_sep"),
    ("khoa_khong_dau", "biến câu tiếng Việt thành khoá tìm kiếm không dấu", "bo_dau"),
    ("co_the_tra_mang", "kiểm tra trước khi tra mạng xem có kết nối không", "mang_co_song"),
]
CAN = {d[2] for d in DE}


def nap_khay() -> list[dict]:
    return json.loads((GOC / "khay_50.json").read_text(encoding="utf-8"))


def dung_khay(tat_ca: list[dict], co: int, rng: random.Random) -> list[dict]:
    """Khay cỡ `co`: LUÔN có 6 thẻ đúng, phần còn lại là nhiễu, xáo thứ tự.

    Xáo là bắt buộc: để thẻ đúng luôn nằm đầu thì đo được cái khác — đo xem
    model có đọc hết khay không, chứ không đo tổ hợp.
    """
    dung = [t for t in tat_ca if t["ten"] in CAN]
    nhieu = [t for t in tat_ca if t["ten"] not in CAN]
    rng.shuffle(nhieu)
    khay = dung + nhieu[: max(co - len(dung), 0)]
    rng.shuffle(khay)
    return khay


def hoi(p: str) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 320,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=900) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _boc_rao(ra: str) -> str:
    t = ra.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def goi_ham_nao(ma: str) -> set[str]:
    """Đọc CÂY CÚ PHÁP, không dò chuỗi — tên hàm nằm trong chú thích hay trong
    chuỗi ký tự thì dò chuỗi tính nhầm thành 'đã gọi'."""
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return set()
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                ten.add(f.id)
            elif isinstance(f, ast.Attribute):
                ten.add(f.attr)
    return ten


def mot_co(khay: list[dict]) -> tuple[int, int, float, list]:
    bang = "\n".join(f"  {t['chu_ky']}   (từ {t['mo_dun']})"
                     + (f"\n      {t['mo_ta']}" if t["mo_ta"] else "")
                     for t in khay)
    dung = sai_the = 0
    giay = 0.0
    ghi = []
    for ten, viec, can in DE:
        p = (f"Bạn viết mã Python cho dự án AURA.\n\n"
             f"KHAY HÀM CÓ SẴN — chỉ được dùng hàm trong khay này:\n{bang}\n\n"
             f"Viết hàm `{ten}` để {viec}. Gọi đúng hàm trong khay, "
             f"nhớ import từ module ghi kèm.\nCHỈ trả về mã Python.\n")
        ra, g = hoi(p)
        giay += g
        goi = goi_ham_nao(_boc_rao(ra))
        ok = can in goi
        dung += ok
        # Có nhặt THẺ NÀO trong khay không, dù nhặt sai? Phân biệt "chọn nhầm
        # thẻ" với "bỏ khay đi tự viết" — hai bệnh khác nhau.
        trong_khay = {t["ten"] for t in khay} & goi
        if not ok:
            sai_the += bool(trong_khay)
            ghi.append({"de": ten, "can": can, "nhat": sorted(trong_khay)[:4]})
    return dung, sai_the, giay, ghi


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    tat_ca = nap_khay()
    print(f"  khay đầy đủ: {len(tat_ca)} thẻ (hàm có thật)\n")
    print(f"  {'cỡ khay':>8}{'gọi ĐÚNG':>11}{'nhặt SAI thẻ':>15}{'giây':>8}")
    ket = {}
    for co in (6, 20, 60):
        khay = dung_khay(tat_ca, co, random.Random(19082026))
        d, s, g, ghi = mot_co(khay)
        ket[co] = (d, s, g, ghi)
        print(f"  {len(khay):>8}{f'{d}/{len(DE)}':>11}{s:>15}{g:>8.0f}")

    print("\n  ===== ĐỌC =====")
    d6, d60 = ket[6][0], ket[60][0]
    n = len(DE)
    if d60 >= 5:
        print(f"    60 thẻ vẫn {d60}/{n} -> tổ hợp CHƯA cắn ở cỡ này")
    elif d60 >= 3:
        print(f"    60 thẻ còn {d60}/{n} -> ĐÃ CẮN, cần lọc khay trước khi đưa model")
    else:
        print(f"    60 thẻ còn {d60}/{n} -> khay to vô dụng nếu không lọc")
    for co in (20, 60):
        if ket[co][3]:
            print(f"\n    cỡ {co} chọn nhầm:")
            for x in ket[co][3]:
                print(f"      {x['de']:<20}cần {x['can']:<26}nhặt {x['nhat']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
