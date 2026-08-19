# -*- coding: utf-8 -*-
"""Đo KHAY THẺ: model chỉ được nhặt thẻ trong khay, thay vì tự gõ mã.

Ý của Sếp 19/08: đóng gói lệnh thành thẻ, model chỉ việc kéo thả trong khay
có sẵn — "giống một bài trắc nghiệm, đáp án này không đúng thì chọn đáp án
khác". Nửa dưới của ý đó là kỹ thuật RÀNG BUỘC ĐẦU RA: chặn cứng mọi token
dẫn ra ngoài khuôn, nên model KHÔNG THỂ trả lời sai định dạng.

VÌ SAO ĐÁNG ĐO — số đo 18/08 trên bộ đề Delta:

    qwen2.5-coder:7b, 10 đề:  4/10 = 40% chết vì `sai_dinh_dang`

Bốn lượt đó chưa hề được chấm về nội dung; chúng chết ở chỗ GÕ. Xoá được loại
lỗi ấy là trả 40% lượt về cho phần suy luận.

ĐỊNH DÙNG llama.cpp GBNF, nhưng `D:\\llamacpp` đã bị xoá cùng `D:\\alpha_bench`.
Dùng `format` của Ollama thay: truyền một lược đồ JSON, model bị ép sinh đúng
lược đồ. Hoá ra HỢP HƠN với ý Sếp — vì `enum` trong lược đồ CHÍNH LÀ khay thẻ:
model chỉ chọn được tên lệnh có trong danh sách, không gõ ra được thứ khác.

    A  TỰ DO   : xin mã Python, dặn khuôn bằng LỜI
    B  KHAY THẺ: cùng đề, ép lược đồ — chỉ nhặt thẻ trong khay

Máy chấm hai mức, KHÔNG dò chuỗi:
    đúng khuôn : A phải `ast.parse` được và có đúng 1 hàm; B phải hợp lược đồ
                 và dịch được sang Python
    đúng việc  : chạy thử hàm với đầu vào thật, so kết quả với đáp án

Hai mức tách nhau có chủ ý. Ràng buộc chỉ hứa chữa mức 1. Nếu mức 2 không nhúc
nhích thì đó là bằng chứng cho đúng điều đã đo: khay thẻ không dạy model hiểu bài.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_khay_the.py
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

# ---- KHAY THẺ ------------------------------------------------------------- #
# Mỗi thẻ là một lệnh. `enum` là khay: model KHÔNG chọn được gì ngoài danh sách.
THE = ["tra_ve", "gan", "neu_tra_ve"]
PHEP = ["+", "-", "*", "==", "!=", "<", ">", "<=", ">=", "%"]

# MỘT THẺ CHỈ ĐƯỢC CÓ MỘT CÁCH ĐIỀN.
#
# Bản đầu cho mỗi thẻ ba trường `trai`/`phai`/`gia_tri` và không nói trường nào
# dùng khi nào. Model điền `trai`+`phai`, bộ dịch của tôi lại đọc `gia_tri` —
# nên nó vứt giá trị đi và sinh ra `return None` cho 7/8 đề. Model nhặt thẻ
# ĐÚNG; cái sai là cái khay.
#
# Bài học cho thiết kế thẻ: thẻ mơ hồ là thẻ hỏng. Mỗi thẻ đúng một bộ trường,
# mỗi giá trị đúng một tên.
LUOC_DO = {
    "type": "object",
    "properties": {
        "ten_ham": {"type": "string"},
        "tham_so": {"type": "array", "items": {"type": "string"}},
        "the": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lenh": {"type": "string", "enum": THE},
                    # dùng cho `gan`: tên biến được gán
                    "ten_bien": {"type": "string"},
                    # dùng cho `neu_tra_ve`: điều kiện, ví dụ "n % 2 == 0"
                    "dieu_kien": {"type": "string"},
                    # dùng cho CẢ BA: giá trị hoặc biểu thức, ví dụ "a + b"
                    "bieu_thuc": {"type": "string"},
                },
                "required": ["lenh", "bieu_thuc"],
            },
        },
    },
    "required": ["ten_ham", "tham_so", "the"],
}

GIAI_THICH_THE = (
    "tra_ve      -> cần `bieu_thuc`. Ví dụ: bieu_thuc=\"a + b\"\n"
    "gan         -> cần `ten_bien` và `bieu_thuc`. Ví dụ: ten_bien=\"tong\", bieu_thuc=\"a + b\"\n"
    "neu_tra_ve  -> cần `dieu_kien` và `bieu_thuc`. Ví dụ: dieu_kien=\"n % 2 == 0\", bieu_thuc=\"True\"\n"
)


def the_sang_python(d: dict) -> str:
    """MÁY dịch thẻ sang mã. Model không gõ một ký tự Python nào."""
    dong = [f"def {d['ten_ham']}({', '.join(d.get('tham_so') or [])}):"]
    for t in d.get("the") or []:
        l, bt = t.get("lenh"), (t.get("bieu_thuc") or "None")
        if l == "tra_ve":
            dong.append(f"    return {bt}")
        elif l == "gan":
            dong.append(f"    {t.get('ten_bien') or '_x'} = {bt}")
        elif l == "neu_tra_ve":
            dong.append(f"    if {t.get('dieu_kien') or 'False'}:")
            dong.append(f"        return {bt}")
    if len(dong) == 1:
        dong.append("    pass")
    return "\n".join(dong)


# ---- ĐỀ ------------------------------------------------------------------- #
DE = [
    ("cong_hai_so", "nhận a, b và trả về tổng của chúng", ["a", "b"],
     [((2, 3), 5), ((0, 0), 0), ((-1, 1), 0)]),
    ("la_so_chan", "nhận n, trả về True nếu n chia hết cho 2, ngược lại False", ["n"],
     [((4,), True), ((7,), False), ((0,), True)]),
    ("lon_hon_muoi", "nhận x, trả về True nếu x lớn hơn 10", ["x"],
     [((11,), True), ((10,), False), ((-5,), False)]),
    ("nhan_ba", "nhận n và trả về n nhân 3", ["n"],
     [((2,), 6), ((0,), 0), ((-4,), -12)]),
    ("bang_khong", "nhận v, trả về True nếu v bằng 0", ["v"],
     [((0,), True), ((3,), False)]),
    ("tru_mot", "nhận so và trả về so trừ đi 1", ["so"],
     [((5,), 4), ((0,), -1)]),
    ("am_hay_khong", "nhận n, trả về True nếu n nhỏ hơn 0", ["n"],
     [((-2,), True), ((0,), False), ((7,), False)]),
    ("binh_phuong", "nhận n và trả về n nhân chính nó", ["n"],
     [((3,), 9), ((0,), 0), ((-2,), 4)]),
]


def hoi(p: str, luoc_do: dict | None) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 300,
                     "num_ctx": 2048}}
    if luoc_do:
        b["format"] = luoc_do
    d = json.dumps(b).encode()
    r = urllib.request.Request(OLLAMA, data=d, method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=600) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _boc_rao(ra: str) -> str:
    """Bóc khối markdown quanh mã.

    Model viết `def cong_hai_so(a, b): return a + b` ĐÚNG HOÀN TOÀN rồi bọc
    trong ```python. Chấm thẳng bằng ast.parse thì 8/8 lượt thành "invalid
    syntax line 1" — tức là ba dấu nháy ngược, không phải model không viết nổi.
    """
    t = ra.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def chay_thu(ma: str, ten: str, cap: list) -> tuple[bool, str]:
    """Chấm ĐÚNG VIỆC: chạy hàm thật với đầu vào thật."""
    moi: dict = {}
    try:
        exec(compile(ma, "<the>", "exec"), moi)
    except Exception as e:                                       # noqa: BLE001
        return False, f"chạy không nổi: {type(e).__name__}"
    f = moi.get(ten)
    if not callable(f):
        return False, f"không có hàm tên {ten}"
    for vao, mong in cap:
        try:
            that = f(*vao)
        except Exception as e:                                   # noqa: BLE001
            return False, f"{ten}{vao} nổ: {type(e).__name__}"
        if that != mong or type(that) is not type(mong):
            return False, f"{ten}{vao} ra {that!r}, cần {mong!r}"
    return True, ""


def mot_luot(nhan: str, dung_khay: bool) -> tuple[int, int, float, list]:
    khuon = viec = 0
    giay = 0.0
    hong = []
    print(f"\n  === {nhan} ===")
    for ten, mo_ta, ts, cap in DE:
        if dung_khay:
            p = (f"Viết hàm tên `{ten}` {mo_ta}.\n"
                 f"Tham số: {', '.join(ts)}.\n"
                 f"Chỉ dùng các thẻ có sẵn, mỗi thẻ điền đúng trường của nó:\n"
                 f"{GIAI_THICH_THE}")
            ra, g = hoi(p, LUOC_DO)
            try:
                d = json.loads(ra)
                d["ten_ham"] = ten          # máy khoá tên, khỏi lệch
                ma = the_sang_python(d)
                ok_khuon, vi_sao = True, ""
            except Exception as e:                               # noqa: BLE001
                ma, ok_khuon, vi_sao = "", False, f"JSON hỏng: {type(e).__name__}"
        else:
            p = (f"Bạn viết mã Python. Viết hàm tên `{ten}` {mo_ta}. "
                 f"Tham số: {', '.join(ts)}.\n"
                 "CHỈ trả về mã Python, không giải thích, không khối markdown, "
                 "không lời rào đầu hay cuối.\n")
            ra, g = hoi(p, None)
            ma = _boc_rao(ra)
            try:
                cay = ast.parse(ma)          # `ma` ĐÃ bóc rào, không phải `ra`
                ham = [n for n in cay.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(cay.body) != 1 or len(ham) != 1:
                    ok_khuon, vi_sao = False, f"{len(cay.body)} khối cấp ngoài, cần 1"
                else:
                    ok_khuon, vi_sao = True, ""
            except SyntaxError as e:
                ok_khuon, vi_sao = False, f"không parse được: {str(e)[:40]}"
        giay += g
        khuon += ok_khuon
        ok_viec, ly_do = (chay_thu(ma, ten, cap) if ok_khuon else (False, vi_sao))
        viec += ok_viec
        trang = ("KHUÔN ok · VIỆC ok" if ok_viec else
                 ("KHUÔN ok · VIỆC SAI — " + ly_do) if ok_khuon else
                 "KHUÔN SAI — " + vi_sao)
        print(f"    {ten:<16}{trang:<52}{g:>5.0f}s")
        if not ok_viec:
            hong.append({"de": ten, "khuon": ok_khuon, "vi_sao": ly_do or vi_sao,
                         "ma": ma[:150]})
    return khuon, viec, giay, hong


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2

    n = len(DE)
    ka, va, ga, ha = mot_luot("A · TỰ DO (dặn khuôn bằng lời)", False)
    kb, vb, gb, hb = mot_luot("B · KHAY THẺ (ép lược đồ)", True)

    print("\n  ===== KẾT QUẢ =====")
    print(f"    {'':<14}{'đúng KHUÔN':>12}{'đúng VIỆC':>12}{'giây':>8}")
    print(f"    {'A tự do':<14}{f'{ka}/{n}':>12}{f'{va}/{n}':>12}{ga:>8.0f}")
    print(f"    {'B khay thẻ':<14}{f'{kb}/{n}':>12}{f'{vb}/{n}':>12}{gb:>8.0f}")
    print(f"\n    khuôn: {100*ka/n:.0f}% -> {100*kb/n:.0f}%"
          f"   ·   việc: {100*va/n:.0f}% -> {100*vb/n:.0f}%")
    for nhan, h in (("A", ha), ("B", hb)):
        if h:
            print(f"\n    {nhan} hỏng:")
            for x in h:
                print(f"      {x['de']:<16}{x['vi_sao'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
