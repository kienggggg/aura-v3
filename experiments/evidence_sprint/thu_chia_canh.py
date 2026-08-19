# -*- coding: utf-8 -*-
"""Chia chương thành 4 cảnh ngắn có hơn viết một phát 1.998 chữ không?

Giả thuyết đến từ số của người khác, không phải cảm giác: tài liệu 2026 ghi
Llama 3.3 **8B** viết tốt tới ~500 từ, và "truyện trên 1.000 từ thì chất lượng
suy giảm — đây là giới hạn nền tảng của model cỡ 8B".

Ta đang bắt `qwen3.5:4b` — NHỎ HƠN 8B — viết 1.998 chữ một lượt. Gấp đôi ngưỡng
mà model to gấp đôi đã bắt đầu đuối.

Nên trước khi đổ cho bộ luật văn phong hay cho model, thử đổi CỠ ĐỀ: 4 cảnh
400-500 chữ, mỗi lượt nằm trong vùng model còn giữ được mạch, rồi ghép.

Mỗi cảnh được biết cảnh trước kết ở đâu — nếu không thì ghép ra bốn mẩu rời.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

import gates  # noqa: E402
from writer import DEFAULT_MODEL, generate_chapter  # noqa: E402

GOC = Path(__file__).resolve().parent

CANH = [
    "Cảnh 1 — MỞ: Kael bước vào Sector 4, nhận ra có gì đó sai.",
    "Cảnh 2 — DẤN: Kael tìm ra manh mối, và manh mối đó khiến anh phải trả giá.",
    "Cảnh 3 — VỠ: điều Kael tin là đúng hoá ra sai.",
    "Cảnh 4 — ĐÓNG: Kael quyết định, và quyết định đó đóng chương lại.",
]


def prompt_canh(bible: dict, style: dict, so: int, mo_ta: str, duoi_truoc: str) -> str:
    p = (f"Bạn là tiểu thuyết gia. Viết CẢNH {so}/4 của chương 3, tiểu thuyết "
         f"'{bible['title']}'.\n\nBỐI CẢNH:\n{bible['setting']}\n\nNHÂN VẬT:\n")
    for c in bible["characters"]:
        p += f"- {c['name']} ({c['role']}): {c['description']}\n"
    p += f"\nVIỆC CỦA CẢNH NÀY:\n{mo_ta}\n"
    if duoi_truoc:
        # Không đưa cả cảnh trước — chỉ đoạn cuối. Nhét cả 1.500 chữ vào ngữ
        # cảnh thì prefill lâu và model lại phải giữ nhiều thứ cùng lúc, đúng
        # cái ta đang tránh.
        p += f"\nCẢNH TRƯỚC KẾT Ở ĐÂY (viết tiếp cho liền mạch):\n…{duoi_truoc}\n"
    p += "\nVĂN PHONG:\n"
    for r in style["rules"]:
        p += f"- {r}\n"
    p += ("\nYÊU CẦU CỨNG:\n- Độ dài 400 đến 550 chữ.\n"
          "- Chỉ viết cảnh này, KHÔNG tóm tắt, KHÔNG viết sang cảnh khác.\n"
          "- Không xuất ra prompt hay lời giải thích.\n"
          f"\nBẮT ĐẦU CẢNH {so}:\n")
    return p


def main() -> int:
    bible = gates.load_json(str(GOC / "data_inputs" / "bible.json"))
    style = gates.load_json(str(GOC / "data_inputs" / "style_card.json"))

    phan: list[str] = []
    duoi = ""
    tong = 0.0
    for i, mo_ta in enumerate(CANH, start=1):
        t0 = time.monotonic()
        chu, _ = generate_chapter(
            prompt_canh(bible, style, i, mo_ta, duoi),
            model=DEFAULT_MODEL, seed=42 + i, max_tokens=900)
        giay = round(time.monotonic() - t0, 1)
        tong += giay
        chu = chu.strip()
        phan.append(chu)
        duoi = chu[-260:]
        print(f"  cảnh {i}: {len(chu.split()):>4} chữ · {giay:>6.1f}s")

    ghep = "\n\n".join(phan)
    ra = GOC.parent.parent / "data" / "evidence_sprint" / "cham_mu" / "ban_C_chia_canh.md"
    ra.write_text(ghep, encoding="utf-8")
    print(f"\n  GHÉP: {len(ghep.split())} chữ · tổng {tong:.1f}s")
    print(f"  -> {ra}")
    print("\n  So với: bản A (baseline) 1.691 chữ/364s · bản B (writer) 1.998 chữ/407s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
