# -*- coding: utf-8 -*-
"""Đo xem RÀNG BUỘC NGỮ PHÁP có xoá được lỗi sai định dạng không.

Ý của Sếp 19/08: đóng gói lệnh thành THẺ, model chỉ việc nhặt thẻ trong khay
thay vì tự gõ. Nửa dưới của ý đó — model không được phép gõ ra thứ sai khuôn —
chính là kỹ thuật `grammar-constrained decoding`, và `llama-server` hỗ trợ sẵn
bằng GBNF. Không phải cài gì, không phải huấn luyện gì.

VÌ SAO ĐÁNG ĐO: đo 18/08 trên bộ đề Delta,

    qwen2.5-coder:7b, 10 đề:  4/10 = 40% chết vì `sai_dinh_dang`

Bốn lượt đó chưa hề được chấm về nội dung — chúng chết ở chỗ GÕ. Nếu ràng buộc
ngữ pháp xoá được loại lỗi ấy thì 40% lượt được trả lại cho phần suy luận.

PHÉP ĐO NÀY CHỈ ĐO ĐÚNG MỘT ĐIỀU: tỉ lệ đầu ra đúng khuôn. Nó KHÔNG đo được
model sửa đúng hay sai — đó là chuyện khác, và bộ đề Delta đã mất cùng
`D:\\alpha_bench` nên không chấm lại được hôm nay.

    A  tự do    : hỏi thường, dặn bằng lời "chỉ trả về mã Python"
    B  ràng buộc: cùng lời nhắc, cộng ngữ pháp GBNF ép khuôn

Chấm bằng MÁY, không dò chuỗi: `ast.parse()` — hoặc cây cú pháp dựng được và
có đúng một `def` ở cấp ngoài, hoặc không.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_gbnf.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

MAY = "http://127.0.0.1:8090"

# Ngữ pháp cho MỘT hàm Python. Cố ý hẹp: đủ cho việc viết lại một hàm nhỏ,
# không cố bao cả Python — ngữ pháp càng rộng càng gần với "không ràng buộc".
#
# Đây chính là "khay thẻ" ở dạng thô nhất: model không chọn được token nào
# dẫn ra ngoài khuôn này, nên nó KHÔNG THỂ trả lời kèm lời rào, kèm khối
# markdown, hay kèm giải thích — ba thứ đã giết 4/10 lượt hôm 18/08.
NGU_PHAP = r'''
root        ::= "def " ten "(" thamso ")" ":" nl than
ten         ::= [a-zA-Z_] [a-zA-Z0-9_]*
thamso      ::= "" | ten ( ", " ten )*
than        ::= cau+
cau         ::= "    " lenh nl
lenh        ::= tra | gan | neu | goi
tra         ::= "return " bieuthuc
gan         ::= ten " = " bieuthuc
neu         ::= "if " bieuthuc ":" nl "        " ( tra | gan )
goi         ::= ten "(" ( bieuthuc ( ", " bieuthuc )* )? ")"
bieuthuc    ::= hang | ten | ten " " pheptoan " " hang | chuoi
hang        ::= "-"? [0-9]+ | "True" | "False" | "None"
pheptoan    ::= "+" | "-" | "*" | "==" | "!=" | "<" | ">" | ">=" | "<="
chuoi       ::= "\"" [a-zA-Z0-9 _.,!?-]* "\""
nl          ::= "\n"
'''

DE = [
    "Viết hàm `cong_hai_so` nhận a, b và trả về tổng.",
    "Viết hàm `la_so_chan` nhận n, trả về True nếu n chia hết cho 2.",
    "Viết hàm `lon_hon_muoi` nhận x, trả về True nếu x lớn hơn 10.",
    "Viết hàm `nhan_ba` nhận n và trả về n nhân 3.",
    "Viết hàm `bang_khong` nhận v, trả về True nếu v bằng 0.",
    "Viết hàm `tru_mot` nhận so và trả về so trừ 1.",
    "Viết hàm `chao` không tham số, trả về chuỗi Xin chao.",
    "Viết hàm `am_hay_khong` nhận n, trả về True nếu n nhỏ hơn 0.",
]
LOI_DAN = ("Bạn viết mã Python. {de}\n"
           "CHỈ trả về mã Python, không giải thích, không khối markdown, "
           "không lời rào đầu hay cuối.\n")


def hoi(p: str, ngu_phap: str | None) -> tuple[str, float]:
    b = {"prompt": p, "n_predict": 220, "temperature": 0.2, "seed": 42,
         "cache_prompt": False}
    if ngu_phap:
        b["grammar"] = ngu_phap
    d = json.dumps(b).encode()
    r = urllib.request.Request(MAY + "/completion", data=d, method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=600) as x:
        k = json.loads(x.read().decode())
    return (k.get("content") or "").strip(), time.monotonic() - t0


def dung_khuon(ra: str) -> tuple[bool, str]:
    """Máy chấm: cây cú pháp dựng được, và có ĐÚNG MỘT def ở cấp ngoài.

    Không dò chuỗi. Dò chuỗi để chấm là kiểu sai đã mắc sáu lần trong kho này.
    """
    if not ra.strip():
        return False, "rỗng"
    try:
        cay = ast.parse(ra)
    except SyntaxError as e:
        return False, f"không parse được: {str(e)[:45]}"
    ham = [n for n in cay.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(ham) != 1:
        return False, f"có {len(ham)} hàm ở cấp ngoài, cần đúng 1"
    if len(cay.body) != 1:
        return False, f"có {len(cay.body)} khối cấp ngoài, thừa lời rào"
    return True, ""


def chay(nhan: str, ngu_phap: str | None) -> tuple[int, float, list]:
    dat, giay, ghi = 0, 0.0, []
    print(f"\n  === {nhan} ===")
    for i, de in enumerate(DE, 1):
        ra, g = hoi(LOI_DAN.format(de=de), ngu_phap)
        giay += g
        ok, vi_sao = dung_khuon(ra)
        dat += ok
        print(f"    {i}/{len(DE)}  {'ĐÚNG KHUÔN' if ok else 'SAI  — ' + vi_sao:<44} {g:.0f}s")
        if not ok:
            ghi.append({"de": i, "vi_sao": vi_sao, "ra": ra[:160]})
    return dat, giay, ghi


def main() -> int:
    try:
        urllib.request.urlopen(MAY + "/health", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  llama-server chưa lên ở " + MAY + " — KHÔNG ĐO ĐƯỢC")
        return 2

    a, ga, ghi_a = chay("A · TỰ DO (chỉ dặn bằng lời)", None)
    b, gb, ghi_b = chay("B · RÀNG BUỘC (ngữ pháp GBNF)", NGU_PHAP)
    n = len(DE)

    print("\n  ===== KẾT QUẢ =====")
    print(f"    A tự do     đúng khuôn {a}/{n} = {100*a/n:.0f}%   ({ga:.0f}s)")
    print(f"    B ràng buộc đúng khuôn {b}/{n} = {100*b/n:.0f}%   ({gb:.0f}s)")
    print(f"\n    ghi chú: phép đo này CHỈ đo đúng khuôn, KHÔNG đo đúng nội dung.")
    if ghi_a:
        print("\n    A hỏng vì:")
        for x in ghi_a:
            print(f"      đề {x['de']}: {x['vi_sao']}")
            print(f"        {x['ra'][:100]!r}")
    if ghi_b:
        print("\n    B hỏng vì:")
        for x in ghi_b:
            print(f"      đề {x['de']}: {x['vi_sao']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
