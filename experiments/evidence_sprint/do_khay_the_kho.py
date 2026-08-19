# -*- coding: utf-8 -*-
"""Đo lại KHAY THẺ trên SÂN ĐÚNG: thẻ sinh từ hàm CÓ THẬT trong kho mã.

VÌ SAO ĐO LẠI. Lượt 1 (`do_khay_the.py`) ra kết quả ngược dự đoán:

    A tự do      khuôn 8/8   việc 8/8    43 giây
    B khay thẻ   khuôn 8/8   việc 4/8   206 giây

Khay thẻ THUA, và chậm gấp 5 lần. Nhưng tám đề đó là hàm một dòng — cộng hai
số, kiểm số chẵn — tức SÂN NHÀ của model, nó đã thấy hàng triệu lần. Ràng buộc
ở đó chỉ tổ trói tay: bốn lượt hỏng của B đều vì khay thiếu thẻ "ngược lại thì
trả về", nên hàm rơi khỏi đáy và trả `None`.

Bài học lượt 1: **trần của khay do người thiết kế khay đặt, không do model.**

LƯỢT NÀY ĐỔI ĐÚNG MỘT BIẾN: đề chuyển sang chỗ model KHÔNG THỂ thạo — các hàm
riêng của kho AURA, không có trong dữ liệu huấn luyện của bất kỳ model nào.
Đây đúng nhóm lỗi đã đo 18/08:

    37% lượt trượt của gemini vì cần một cái tên nằm ở TỆP KHÁC

Nếu khay thẻ có ăn ở đâu thì phải ăn ở đây. Nếu ở đây cũng không ăn thì ý
"khay thẻ giúp model" coi như đóng hồ sơ.

    A  TỰ DO   : chỉ mô tả việc. Model tự nghĩ cách.
    B  KHAY THẺ: cùng đề, kèm khay liệt kê hàm CÓ THẬT + chữ ký.

Chấm bằng máy: mã có gọi ĐÚNG hàm cần dùng không (đọc cây cú pháp, không dò
chuỗi), và có chạy nổi không.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_khay_the_kho.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"

# ---- KHAY THẺ: hàm CÓ THẬT trong kho, lấy nguyên chữ ký ------------------- #
KHAY = [
    ("cau_gio", "core.dong_ho", "cau_gio() -> str",
     "Trả về câu mô tả ngày giờ hiện tại bằng tiếng Việt, lấy từ ĐỒNG HỒ MÁY."),
    ("tinh_giup", "core.may_tinh", "tinh_giup(text: str) -> str | None",
     "Nhận câu hỏi có phép tính, trả lời bằng MÁY tính; None nếu không phải phép tính."),
    ("tra_so", "core.doc_so_phien", "tra_so(text: str, history) -> str | None",
     "Tra sổ phiên chat để trả lời câu hỏi về lượt trước; None nếu không tra được."),
    ("la_chuyen_rieng_cua_sep", "core.web_search", "la_chuyen_rieng_cua_sep(text: str) -> bool",
     "True nếu câu hỏi là chuyện riêng của Sếp, KHÔNG được đẩy ra máy tìm kiếm."),
    ("bo_dau", "core.web_search", "bo_dau(text: str) -> str",
     "Bỏ dấu tiếng Việt khỏi chuỗi."),
    ("mang_co_song", "core.web_search", "mang_co_song(han_giay: float = 1.5) -> bool",
     "True nếu máy đang có mạng."),
]

# ---- ĐỀ: mỗi đề PHẢI dùng đúng một hàm trong khay ------------------------- #
DE = [
    ("tra_loi_gio", "trả lời câu hỏi về ngày giờ hiện tại", "cau_gio"),
    ("tra_loi_phep_tinh", "trả lời một câu hỏi có chứa phép tính", "tinh_giup"),
    ("hoi_luot_truoc", "trả lời câu hỏi của người dùng về các lượt chat trước đó", "tra_so"),
    ("co_duoc_tra_mang", "quyết định câu hỏi này có được phép đẩy ra máy tìm kiếm không",
     "la_chuyen_rieng_cua_sep"),
    ("khoa_khong_dau", "biến câu tiếng Việt thành khoá tìm kiếm không dấu", "bo_dau"),
    ("co_the_tra_mang", "kiểm tra trước khi tra mạng xem có kết nối không", "mang_co_song"),
]


def hoi(p: str) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 320,
                     "num_ctx": 4096}}
    d = json.dumps(b).encode()
    r = urllib.request.Request(OLLAMA, data=d, method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=600) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _boc_rao(ra: str) -> str:
    """Bóc khối markdown. Lượt 1 quên bước này và chấm 8/8 lượt thành 'sai
    cú pháp' cho ba dấu nháy ngược — model viết mã đúng hoàn toàn."""
    t = ra.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def goi_nhung_ham_nao(ma: str) -> set[str]:
    """Đọc CÂY CÚ PHÁP để biết mã gọi hàm nào.

    Không dò chuỗi: `bo_dau` xuất hiện trong chú thích, trong tên biến, trong
    một chuỗi ký tự — dò chuỗi tính hết thành 'đã gọi'. Đó là kiểu chấm sai đã
    mắc sáu lần trong kho này.
    """
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


def mot_luot(nhan: str, dua_khay: bool) -> tuple[int, int, float, list]:
    dung_ham = chay_duoc = 0
    giay = 0.0
    ghi = []
    print(f"\n  === {nhan} ===")
    for ten, viec, can in DE:
        if dua_khay:
            bang = "\n".join(f"  {c}   (từ {m})\n      {mo}"
                             for c, m, _, mo in
                             [(k[2], k[1], k[0], k[3]) for k in KHAY])
            p = (f"Bạn viết mã Python cho dự án AURA.\n\n"
                 f"KHAY HÀM CÓ SẴN — chỉ được dùng hàm trong khay này:\n{bang}\n\n"
                 f"Viết hàm `{ten}` để {viec}. Gọi đúng hàm trong khay, "
                 f"nhớ import từ module ghi kèm.\n"
                 f"CHỈ trả về mã Python.\n")
        else:
            p = (f"Bạn viết mã Python cho dự án AURA.\n"
                 f"Viết hàm `{ten}` để {viec}.\n"
                 f"CHỈ trả về mã Python.\n")
        ra, g = hoi(p)
        giay += g
        ma = _boc_rao(ra)
        goi = goi_nhung_ham_nao(ma)
        ok_ham = can in goi
        try:
            ast.parse(ma)
            ok_chay = True
        except SyntaxError:
            ok_chay = False
        dung_ham += ok_ham
        chay_duoc += ok_chay
        trang = ("gọi ĐÚNG " + can) if ok_ham else ("KHÔNG gọi " + can)
        print(f"    {ten:<20}{trang:<34}{'cú pháp ok' if ok_chay else 'CÚ PHÁP HỎNG':<14}{g:>5.0f}s")
        if not ok_ham:
            ghi.append({"de": ten, "can": can, "goi": sorted(goi)[:6],
                        "ma": ma[:130]})
    return dung_ham, chay_duoc, giay, ghi


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    n = len(DE)
    ha, ca, ga, gha = mot_luot("A · TỰ DO (không đưa khay)", False)
    hb, cb, gb, ghb = mot_luot("B · KHAY THẺ (đưa hàm có thật)", True)

    print("\n  ===== KẾT QUẢ =====")
    print(f"    {'':<14}{'gọi ĐÚNG hàm':>14}{'cú pháp ok':>12}{'giây':>8}")
    print(f"    {'A tự do':<14}{f'{ha}/{n}':>14}{f'{ca}/{n}':>12}{ga:>8.0f}")
    print(f"    {'B khay thẻ':<14}{f'{hb}/{n}':>14}{f'{cb}/{n}':>12}{gb:>8.0f}")
    print(f"\n    gọi đúng hàm: {100*ha/n:.0f}% -> {100*hb/n:.0f}%")
    for nhan, gh in (("A", gha), ("B", ghb)):
        if gh:
            print(f"\n    {nhan} không gọi đúng:")
            for x in gh:
                print(f"      {x['de']:<20}cần {x['can']:<26}gọi {x['goi']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
