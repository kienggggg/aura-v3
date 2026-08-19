# -*- coding: utf-8 -*-
"""Khay ĐÃ LỌC so với khay đầy — vòng cuối của chuỗi đo 19/08.

Chuỗi đã đi:
    lượt 1  Python cơ bản       tự do 8/8  ·  khay 4/8   -> khay TRÓI TAY
    lượt 2  hàm riêng của kho   tự do 0/6  ·  khay 6/6   -> khay CỨU HẲN
    lượt 3  khay 6/20/60 thẻ    5/6 · 5/6 · 4/6          -> khay to thì tụt

Lượt này thêm bước Sếp nói từ đầu: *trước khi code thì nhặt nhóm thẻ cần dùng*.
`core.khay_the.loc_khay` chấm thẻ theo ĐỘ HIẾM của từ khoá, thuần máy, không
gọi model — lọc mà phải gọi model thì tự chuốc lại đúng cái chậm đang tránh.

Bộ lọc tự nó đã đo riêng: giữ được thẻ đúng 5/6 ở cỡ 8, 6/6 ở cỡ 15. Lượt này
đo phần còn lại: khay đã lọc thì MODEL có gọi đúng hàm hơn không.

    A  khay ĐẦY   65 thẻ, không lọc
    B  khay LỌC   65 -> 15 thẻ theo mô tả việc

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_khay_loc.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import bang_khay, loc_khay, sinh_khay      # noqa: E402

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
GOC = Path(__file__).resolve().parent.parent.parent

# 28 đề, nạp từ tệp. Sáu đề của các lượt trước quá ít: một đề đổi là 17%, nên
# mọi chênh lệch ±1 đều lẫn vào nhiễu — mà tôi đã ba lần đọc ±1 thành kết luận.
# Ở 28 đề thì một đề chỉ còn 3,6%.
#
# Đề đã qua bộ kiểm LỘ TÊN: không mô tả nào chứa mảnh tên hàm đích (>=4 ký tự,
# đã bỏ dấu). Lộ tên thì bên TỰ DO cũng đoán ra được, và phép so hỏng.
DE = [tuple(x) for x in json.loads(
    (Path(__file__).resolve().parent / "de_khay.json").read_text(encoding="utf-8"))["de"]]


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


def tu_dinh_nghia(ma: str) -> set[str]:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return set()
    return {n.name for n in ast.walk(cay)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def nhap_tu_kho(ma: str) -> set[str]:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return set()
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in (
                "core", "interface", "tools"):
            ra |= {a.asname or a.name for a in n.names}
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in ("core", "interface", "tools"):
                    ra.add(a.name.split(".")[-1])
    return ra


def dung_ham_kho(ma: str, can: str) -> bool:
    """Có THẬT SỰ dùng hàm `can` CỦA KHO không.

    HAI LỖI CỦA BẢN TRƯỚC — bắt được nhờ thử bộ chấm bằng đầu vào biết trước
    đáp án, TRƯỚC khi số về chứ không phải sau:

    1. DƯƠNG TÍNH GIẢ. Model tự viết `def cau_gio(...)` rồi gọi hàm của chính
       nó, bản cũ tính là "gọi đúng". Có thật: lượt 6 đề trước, `khoa_khong_dau`
       gọi chính `khoa_khong_dau` nó vừa định nghĩa. Lỗi này THỔI PHỒNG BÊN TỰ
       DO, vì bên không có khay mới là bên phải tự viết lấy.
    2. ÂM TÍNH GIẢ. Nhập rồi tham chiếu mà không gọi thì bị bỏ sót.

    Luật chặt: phải NHẬP TỪ KHO (hoặc gọi qua mô-đun của kho), và KHÔNG được là
    hàm do chính mã ấy định nghĩa.
    """
    if can in tu_dinh_nghia(ma):
        return False
    qua_mo_dun = bool(re.search(
        rf"\b(core|interface|tools)\.\w+\.{re.escape(can)}\s*\(", ma))
    if can not in nhap_tu_kho(ma) and not qua_mo_dun:
        return False
    return can in goi_ham_nao(ma)


def goi_ham_nao(ma: str) -> set[str]:
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


SO_NONG: list[dict] = []
TEP_SO = Path(__file__).resolve().parent / "so_nong_khay.json"


def _luu_so() -> None:
    """Ghi sổ SAU MỖI ĐỀ, không đợi hết vòng — soát dở chừng mới kịp chỉnh."""
    TEP_SO.write_text(json.dumps(SO_NONG, ensure_ascii=False, indent=1),
                      encoding="utf-8")


def mot_luot(nhan: str, khay_day: list, kieu: str) -> tuple[int, float, int]:
    """kieu: "khong" (không khay) · "day" (cả khay) · "loc" (khay đã lọc).

    Điều kiện "khong" là điều kiện QUAN TRỌNG NHẤT và bản trước thiếu hẳn: nó
    trả lời câu "khay thẻ có ăn không". So khay-đầy với khay-lọc chỉ là so hai
    kiểu khay với nhau.
    """
    dung = 0
    giay = 0.0
    tong_the = 0
    print(f"\n  === {nhan} ===")
    for ten, viec, can in DE:
        khay = [] if kieu == "khong" else (
            loc_khay(khay_day, viec, 15) if kieu == "loc" else khay_day)
        tong_the += len(khay)
        if kieu == "khong":
            p = (f"Bạn viết mã Python cho dự án AURA.\n"
                 f"Viết hàm `{ten}` để {viec}.\nCHỈ trả về mã Python.\n")
        else:
            p = (f"Bạn viết mã Python cho dự án AURA.\n\n"
                 f"KHAY HÀM CÓ SẴN — chỉ được dùng hàm trong khay này:\n"
                 f"{bang_khay(khay)}\n\n"
                 f"Viết hàm `{ten}` để {viec}. Gọi đúng hàm trong khay, "
                 f"nhớ import từ module ghi kèm.\nCHỈ trả về mã Python.\n")
        ra, g = hoi(p)
        giay += g
        ma = _boc_rao(ra)
        ok = dung_ham_kho(ma, can)
        goi = goi_ham_nao(ma)
        # LƯU NGUYÊN VĂN. Chín lần hôm nay tôi báo số rồi mới phát hiện bộ chấm
        # sai; không giữ đầu ra thì không soát lại được, chỉ còn cách chạy lại.
        SO_NONG.append({"dieu_kien": nhan, "de": ten, "can": can, "dat": ok,
                        "so_the": len(khay), "giay": round(g, 1), "ma": ma})
        _luu_so()
        dung += ok
        nhat = sorted({t.ten for t in khay} & goi)[:3]
        print(f"    {ten:<20}{'ĐÚNG' if ok else 'sai ':<6}{can:<26}"
              f"{len(khay):>3} thẻ  nhặt {nhat}  {g:.0f}s")
    return dung, giay, tong_the // len(DE)


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    khay = sinh_khay(GOC)
    print(f"  khay sinh từ mã thật: {len(khay)} thẻ")
    n = len(DE)
    d0, g0, c0 = mot_luot("A · KHÔNG KHAY (tự do)", khay, "khong")
    da, ga, ca = mot_luot("B · KHAY ĐẦY (không lọc)", khay, "day")
    db, gb, cb = mot_luot("C · KHAY LỌC (-> 15 thẻ)", khay, "loc")

    print("\n  ===== KẾT QUẢ =====")
    print(f"    {'':<16}{'thẻ/đề':>8}{'gọi ĐÚNG':>11}{'%':>7}{'giây':>8}")
    for nhan, d, c, g in (("A không khay", d0, c0, g0),
                          ("B khay đầy", da, ca, ga),
                          ("C khay lọc", db, cb, gb)):
        print(f"    {nhan:<16}{c:>8}{f'{d}/{n}':>11}{100*d/n:>6.0f}%{g:>8.0f}")
    _luu_so()
    print(f"    nguyên văn {len(SO_NONG)} lượt -> {TEP_SO.name}")
    print(f"\n    khay có ăn không    : {d0}/{n} -> {da}/{n}   (không khay -> khay đầy)")
    print(f"    lọc có ăn thêm không: {da}/{n} -> {db}/{n}   (khay đầy -> khay lọc)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
