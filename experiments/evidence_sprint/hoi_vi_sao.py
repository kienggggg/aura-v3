# -*- coding: utf-8 -*-
"""Hỏi model VÌ SAO nó chọn thẻ đó — lượt chẩn đoán, KHÔNG phải phép đo.

Sếp muốn xem model nghĩ gì lúc làm. Kiểm 19/08: `qwen2.5-coder:7b` KHÔNG có
suy luận ẩn — truyền `think: true` thì Ollama trả HTTP 400. Nên không có gì để
mở ra xem; cách duy nhất là HỎI nó.

Mà hỏi thì đổi đề bài: bảo model giải thích trước khi viết là đã cho nó thêm
một bước nghĩ, và điểm sẽ khác. Vì thế lượt này chạy RIÊNG, sau khi phép đo
chính xong, và KHÔNG được cộng vào bảng điểm nào cả.

Cái nó trả lời cũng phải đọc dè chừng: model kể lại lý do SAU KHI đã chọn thì
đó là lời kể, không phải nguyên nhân. Người cũng thế. Dùng nó để tìm chỗ khay
thẻ mô tả chưa rõ, đừng dùng nó làm bằng chứng về cơ chế bên trong.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\hoi_vi_sao.py [so_de]
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import bang_khay, loc_khay, sinh_khay        # noqa: E402

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
GOC = Path(__file__).resolve().parent.parent.parent
SO = Path(__file__).resolve().parent / "so_nong_khay.json"
DE = {d[0]: d for d in json.loads(
    (Path(__file__).resolve().parent / "de_khay.json").read_text(encoding="utf-8"))["de"]}


def hoi(p: str, tran: int = 300) -> str:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": tran,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as x:
        return (json.loads(x.read().decode()).get("response") or "").strip()


def main() -> int:
    if not SO.is_file():
        print("  chưa có sổ nóng — chạy do_khay_loc.py trước")
        return 2
    so = json.loads(SO.read_text(encoding="utf-8"))
    # Chỉ hỏi những đề CÓ KHAY mà vẫn chọn sai — đó là chỗ khay chưa đủ rõ.
    hong = [x for x in so if not x["dat"] and x["so_the"] > 0]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    hong = hong[:n]
    if not hong:
        print("  không có đề nào CÓ KHAY mà chọn sai — không cần hỏi")
        return 0

    khay_day = sinh_khay(GOC)
    print(f"  hỏi {len(hong)} đề (có khay mà vẫn chọn sai)\n")
    ra = []
    for x in hong:
        ten, viec, can = DE[x["de"]]
        khay = loc_khay(khay_day, viec, 15) if x["so_the"] < len(khay_day) else khay_day
        p = (f"Bạn viết mã Python cho dự án AURA.\n\n"
             f"KHAY HÀM CÓ SẴN:\n{bang_khay(khay)}\n\n"
             f"Việc cần làm: {viec}\n\n"
             f"ĐỪNG viết mã. Chỉ trả lời ba dòng:\n"
             f"CHON: <tên đúng một hàm trong khay bạn sẽ dùng>\n"
             f"VISAO: <một câu, vì sao chọn nó>\n"
             f"LOAI: <tên hàm nào trong khay bạn đã cân nhắc rồi loại, và vì sao>\n")
        loi = hoi(p)
        chon = ""
        for d in loi.splitlines():
            if d.strip().upper().startswith("CHON"):
                chon = d.split(":", 1)[-1].strip().strip("`")
                break
        khop = chon == can
        print(f"  --- {x['de']}   cần `{can}`")
        print(f"      lúc viết mã nó dùng : {'ĐÚNG' if x['dat'] else 'SAI'}")
        print(f"      khi được HỎI nó chọn: {chon or '(không nói)'}"
              f"   {'KHỚP' if khop else 'vẫn lệch'}")
        for d in loi.splitlines():
            if d.strip().upper().startswith(("VISAO", "LOAI")):
                print(f"      {d.strip()[:150]}")
        print()
        ra.append({"de": x["de"], "can": can, "chon_khi_hoi": chon,
                   "dat_khi_viet_ma": x["dat"], "loi": loi})

    khop = sum(1 for r in ra if r["chon_khi_hoi"] == r["can"])
    print(f"  ===== {khop}/{len(ra)} đề: HỎI thì chọn đúng, mà VIẾT MÃ thì sai =====")
    if khop:
        print("  -> model BIẾT thẻ nào đúng nhưng không dùng khi viết mã.")
        print("     Chỗ hỏng nằm ở bước viết, không ở bước hiểu khay.")
    else:
        print("  -> model KHÔNG biết thẻ nào đúng. Chỗ hỏng nằm ở mô tả thẻ.")
    (Path(__file__).resolve().parent / "vi_sao_chon.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
