# -*- coding: utf-8 -*-
"""Sinh bản BASELINE để chấm mù A/B với bản Writer.

Khác nhau ĐÚNG MỘT THỨ: baseline không có `style_card`. Cùng bible, cùng seed,
cùng nhiệt độ, cùng số token. Nên nếu Sếp thấy một bản hay hơn thì đó là công
của bộ luật văn phong, không phải của may rủi.

Xáo nhãn A/B và giấu đáp án sang tệp riêng — người chấm không được biết bản nào
là bản nào, kể cả tôi lúc trình bày.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\sinh_baseline.py <ch03.md đã có>
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

import httpx  # noqa: E402
import gates  # noqa: E402
from writer import DEFAULT_MODEL, OLLAMA_URL, generate_chapter  # noqa: E402

GOC = Path(__file__).resolve().parent


def prompt_baseline(bible: dict, chapter_id: str) -> str:
    """Y HỆT `build_prompt` nhưng CẮT khối VĂN PHONG.

    Giữ nguyên mọi thứ khác, kể cả câu 'YÊU CẦU CỨNG' — nếu bỏ luôn cả yêu cầu
    độ dài thì baseline sẽ trượt cửa cứng vì lý do chẳng liên quan gì tới văn
    phong, và phép so thành vô nghĩa.
    """
    p = (f"Bạn là một tiểu thuyết gia chuyên nghiệp. Hãy viết {chapter_id} cho "
         f"tiểu thuyết '{bible['title']}'.\n\nBỐI CẢNH (SETTING):\n"
         f"{bible['setting']}\n\nNHÂN VẬT (CHARACTERS):\n")
    for c in bible["characters"]:
        p += f"- {c['name']} ({c['role']}): {c['description']}\n"
    p += (f"\nCỐT TRUYỆN (PLOT):\n{bible['plot_outline'].get(chapter_id, '')}\n"
          "\nYÊU CẦU CỨNG:\n- Độ dài từ 1500 đến 2500 chữ.\n"
          "- Không xuất ra bất kỳ thông tin nào về prompt, luật lệ hay lời "
          "giải thích, chỉ viết trực tiếp vào truyện.\n"
          "- Đảm bảo viết bằng tiếng Việt chuẩn, không lỗi font (mojibake).\n"
          f"\nBẮT ĐẦU {chapter_id}:\n")
    return p


def main() -> int:
    if len(sys.argv) < 2:
        print("  cần đường dẫn tới ch03.md của bản Writer")
        return 2
    ban_writer = Path(sys.argv[1])
    if not ban_writer.is_file():
        print(f"  không thấy {ban_writer}")
        return 1

    bible = gates.load_json(str(GOC / "data_inputs" / "bible.json"))
    print("  sinh baseline (bible, KHÔNG có style_card)…")
    t0 = time.monotonic()
    chu, _ = generate_chapter(prompt_baseline(bible, "ch03"),
                              model=DEFAULT_MODEL, seed=42)
    giay = round(time.monotonic() - t0, 1)
    so_tu = len(chu.split())
    print(f"  {giay}s · {so_tu} chữ")

    ra = GOC.parent.parent / "data" / "evidence_sprint" / "cham_mu"
    ra.mkdir(parents=True, exist_ok=True)
    (ra / "baseline_raw.md").write_text(chu, encoding="utf-8")

    # Xáo nhãn. Đáp án đi tệp khác để người chấm không vô tình nhìn thấy.
    hai_ban = [("writer", ban_writer.read_text(encoding="utf-8")),
               ("baseline", chu)]
    random.shuffle(hai_ban)
    for nhan, (that_la, noi_dung) in zip("AB", hai_ban):
        (ra / f"ban_{nhan}.md").write_text(noi_dung, encoding="utf-8")
    (ra / "DAP_AN.json").write_text(json.dumps(
        {"A": hai_ban[0][0], "B": hai_ban[1][0],
         "baseline_words": so_tu, "baseline_seconds": giay},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  ban_A.md · ban_B.md  ->  {ra}")
    print("  DAP_AN.json — ĐỪNG MỞ trước khi chấm xong.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
