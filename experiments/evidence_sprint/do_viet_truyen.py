# -*- coding: utf-8 -*-
"""Đo model 1-bit MoE ở việc nó CÓ THỂ mạnh: viết truyện.

VÌ SAO ĐỔI VIỆC: đo 18/08 trên cùng máy, cùng llama.cpp —

    model                       nạp prompt    sinh chữ    cỡ
    qwen2.5-coder:7b Q4          76,0 t/s      4,01 t/s   4,36 GiB
    Qwen3-30B-A3B  IQ1_S          6,85 t/s     4,38 t/s   8,42 GiB

Model 30 TỶ sinh chữ NHANH HƠN model 7 tỷ (4,38 so với 4,01) vì MoE chỉ bật
3,3 tỷ tham số mỗi token. Nhưng nạp prompt chậm gấp 11 lần: nạp xử lý cả LÔ
token cùng lúc, lô đó chạm gần hết 128 chuyên gia, nên phải đọc gần cả 8,42
GiB — đúng cái mà tài liệu gọi là "coi lớp MoE như lớp dày, không tính đến
kích hoạt có điều kiện và thưa".

Suy ra chỗ nó hợp: việc có **lời nhắc NGẮN, đầu ra DÀI**. Viết truyện đúng
kiểu đó — vài trăm token vào, vài nghìn token ra. Phòng Delta thì ngược lại
(4.000 token vào), nên ép nó vào đó là ép vào chỗ nó chắc chắn thua.

CÁCH ĐO: cùng một lời nhắc, cùng seed, hai model. Chạy LẦN LƯỢT chứ không song
song — máy 11,7 GB không chứa nổi cả hai, chạy chung thì đo nhầm sang "máy
ngợp" chứ không phải "model nhanh chậm".

CHẤM: máy đếm chữ và giây; CÒN HAY DỞ THÌ SẾP CHẤM MÙ. Không có cửa cứng nào
chấm được "đoạn này đọc có cuốn không" — đã ghi trong tài liệu, và đó là lý do
kiểu Reflexion vô dụng cho việc viết.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_viet_truyen.py
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GOC = Path(__file__).resolve().parent
RA = GOC.parent.parent / "data" / "evidence_sprint" / "cham_mu"
GGUF = Path("F:/models/Qwen3-30B-A3B-UD-IQ1_S.gguf")
LLAMA = Path("D:/llamacpp")
CONG = 8099
SO_CHU = 1200


def loi_nhac() -> str:
    import gates
    bible = gates.load_json(str(GOC / "data_inputs" / "bible.json"))
    style = gates.load_json(str(GOC / "data_inputs" / "style_card.json"))
    p = (f"Bạn là tiểu thuyết gia. Viết chương 3 của tiểu thuyết "
         f"'{bible['title']}'.\n\nBỐI CẢNH:\n{bible['setting']}\n\nNHÂN VẬT:\n")
    for c in bible["characters"]:
        p += f"- {c['name']} ({c['role']}): {c['description']}\n"
    p += "\nVĂN PHONG:\n"
    for r in style["rules"]:
        p += f"- {r}\n"
    p += (f"\nYÊU CẦU CỨNG:\n- Độ dài khoảng {SO_CHU} chữ.\n"
          "- Chỉ viết chương truyện, KHÔNG tóm tắt, không giải thích.\n\n"
          "BẮT ĐẦU CHƯƠNG 3:\n")
    return p


def qua_ollama(model: str, p: str) -> tuple[float, str, dict]:
    b = json.dumps({"model": model, "prompt": p, "stream": False, "think": False,
                    "keep_alive": "2m",
                    "options": {"seed": 42, "temperature": 0.8,
                                "num_predict": 2600, "num_ctx": 8192}}).encode()
    r = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                               headers={"Content-Type": "application/json"},
                               method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=3600) as x:
        k = json.loads(x.read().decode())
    return (time.monotonic() - t0, (k.get("response") or "").strip(),
            {"nap_token": k.get("prompt_eval_count"), "sinh_token": k.get("eval_count"),
             "sinh_t_s": round(k.get("eval_count", 0) / max(k.get("eval_duration", 1) / 1e9, 1e-9), 2)})


def qua_llamacpp(p: str) -> tuple[float, str, dict]:
    sv = subprocess.Popen(
        [str(LLAMA / "llama-server.exe"), "-m", str(GGUF), "--host", "127.0.0.1",
         "--port", str(CONG), "-dev", "none", "-ngl", "0", "-c", "8192", "-t", "4",
         "--no-warmup"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(180):                       # model 8,42 GiB nạp từ đĩa, chờ lâu
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{CONG}/health", timeout=5)
                break
            except Exception:                                    # noqa: BLE001
                time.sleep(5)
        else:
            return 0.0, "", {"loi": "llama-server không lên sau 15 phút"}

        b = json.dumps({"prompt": p, "n_predict": 2600, "temperature": 0.8,
                        "seed": 42, "cache_prompt": False}).encode()
        r = urllib.request.Request(f"http://127.0.0.1:{CONG}/completion", data=b,
                                   headers={"Content-Type": "application/json"},
                                   method="POST")
        t0 = time.monotonic()
        with urllib.request.urlopen(r, timeout=7200) as x:
            k = json.loads(x.read().decode())
        tm = k.get("timings") or {}
        return (time.monotonic() - t0, (k.get("content") or "").strip(),
                {"nap_token": tm.get("prompt_n"), "sinh_token": tm.get("predicted_n"),
                 "nap_t_s": round(tm.get("prompt_per_second") or 0, 2),
                 "sinh_t_s": round(tm.get("predicted_per_second") or 0, 2)})
    finally:
        sv.terminate()
        try:
            sv.wait(timeout=30)
        except subprocess.TimeoutExpired:
            sv.kill()


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    p = loi_nhac()
    print(f"  lời nhắc {len(p)} ký tự (~{len(p)//3.2:.0f} token)\n")
    kq = {}

    # 1) Model 30B 1-bit qua llama.cpp — nhả Ollama trước cho đủ RAM.
    print("  [1/2] Qwen3-30B-A3B IQ1_S (8,42 GiB) — nhả Ollama rồi nạp…")
    subprocess.run(["ollama", "stop", "qwen3.5:4b"], capture_output=True)
    subprocess.run(["ollama", "stop", "qwen2.5-coder:7b"], capture_output=True)
    time.sleep(5)
    g, chu, tk = qua_llamacpp(p)
    kq["moe30b"] = {"giay": round(g, 1), "so_chu": len(chu.split()), **tk}
    (RA / "truyen_moe30b.md").write_text(chu, encoding="utf-8")
    print(f"        {len(chu.split())} chữ · {g:.0f}s · {tk}\n")

    # 2) qwen3.5:4b qua Ollama
    print("  [2/2] qwen3.5:4b (3,4 GB) qua Ollama…")
    g2, chu2, tk2 = qua_ollama("qwen3.5:4b", p)
    kq["qwen35_4b"] = {"giay": round(g2, 1), "so_chu": len(chu2.split()), **tk2}
    (RA / "truyen_qwen35_4b.md").write_text(chu2, encoding="utf-8")
    print(f"        {len(chu2.split())} chữ · {g2:.0f}s · {tk2}\n")

    # 3) Xáo nhãn cho Sếp chấm mù — máy KHÔNG chấm hay/dở được.
    ban = [("moe30b", RA / "truyen_moe30b.md"),
           ("qwen35_4b", RA / "truyen_qwen35_4b.md")]
    random.Random(18082026).shuffle(ban)
    dap = {}
    for nhan, (that, f) in zip("PQ", ban):
        (RA / f"truyen_{nhan}.md").write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        dap[nhan] = that
    (RA / "DAP_AN_TRUYEN.json").write_text(json.dumps(dap, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print("  ===== SỐ MÁY ĐO ĐƯỢC =====")
    for k, v in kq.items():
        print(f"    {k:<12}{v}")
    print(f"\n  Sếp chấm mù: truyen_P.md · truyen_Q.md  (đáp án trong DAP_AN_TRUYEN.json)")
    (RA / "so_do_truyen.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
