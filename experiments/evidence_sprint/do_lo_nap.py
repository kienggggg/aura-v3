# -*- coding: utf-8 -*-
"""Nạp prompt chậm 11 lần — thử xem có phải do LÔ QUÁ TO không.

GIẢ THUYẾT (chưa đo, nên viết ra TRƯỚC khi chạy):

Qwen3-30B-A3B có 128 chuyên gia, mỗi token chọn 8. Sinh chữ đi từng token một
-> mỗi bước chỉ chạm 8/128 chuyên gia ~ 0,5 GB -> vừa RAM -> 4,38 t/s.

Nạp prompt đi theo LÔ. llama.cpp mặc định lô vật lý 512 token. 512 token x 8
lựa chọn thì gần như chạm ĐỦ 128 chuyên gia -> phải đọc gần cả 8,42 GiB cho MỘT
lô. Máy chỉ còn ~5 GB trống, nên lô sau lại đá lô trước ra khỏi bộ đệm -> đọc
lại từ đĩa mỗi lô. Đó là giã đĩa, không phải model chậm.

Nếu đúng: hạ lô vật lý (-ub) xuống thì tập chuyên gia cần cho mỗi bước co lại
vừa bộ đệm, nạp phải NHANH LÊN — dù lô nhỏ thì tính toán kém song song hơn.

Nếu sai: nạp chậm đều ở mọi cỡ lô -> nút thắt nằm chỗ khác, và đóng hồ sơ
"1-bit MoE không dùng cho việc lời nhắc dài" cho xong.

LUẬT TỰ ĐẶT TRƯỚC KHI ĐO: coi là ĐƯỢC nếu có cỡ lô nào cho nạp >= 20 t/s (mốc
này để 4.000 token nạp trong 200 giây thay vì 584 giây). Dưới 20 thì vẫn là
không dùng được cho phòng Delta, dù có nhanh lên chút ít.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GGUF = "F:/models/Qwen3-30B-A3B-UD-IQ1_S.gguf"
BENCH = "D:/llamacpp/llama-bench.exe"
RA = Path("D:/AURA_v3/data/evidence_sprint/cham_mu/so_do_lo_nap.json")


def chay(ub: int) -> dict:
    # -dev none: Vulkan cấp bộ nhớ GPU cả khi -ngl 0, đo 18/08 -> ErrorOutOfDeviceMemory
    lenh = [BENCH, "-m", GGUF, "-dev", "none", "-ngl", "0", "-t", "4",
            "-ub", str(ub), "-b", str(max(ub, 512)), "-p", "512", "-n", "0", "-r", "1"]
    t0 = time.monotonic()
    k = subprocess.run(lenh, capture_output=True, text=True, timeout=3600)
    g = time.monotonic() - t0
    m = re.search(r"pp512\s*\|\s*([\d.]+)", k.stdout)
    if not m:
        return {"ub": ub, "trang_thai": "khong_do_duoc",
                "vi_sao": (k.stderr or k.stdout)[-300:]}
    return {"ub": ub, "nap_t_s": float(m.group(1)), "giay_ca_lenh": round(g, 1),
            "trang_thai": "do_duoc"}


def main() -> int:
    subprocess.run(["ollama", "stop", "qwen3.5:4b"], capture_output=True)
    time.sleep(3)
    ket = []
    for ub in (512, 128, 32, 8):
        print(f"  -ub {ub:<4} …", end="", flush=True)
        r = chay(ub)
        ket.append(r)
        print(f" {r.get('nap_t_s', r['trang_thai'])} t/s")

    do_duoc = [r for r in ket if r["trang_thai"] == "do_duoc"]
    tot = max(do_duoc, key=lambda r: r["nap_t_s"]) if do_duoc else None
    print("\n  ===== KET QUA =====")
    for r in ket:
        print(f"    ub={r['ub']:<5}{r.get('nap_t_s', r['trang_thai'])}")
    if tot:
        # Luật đặt TRƯỚC khi đo, không sửa sau khi thấy số.
        cho = "DUOC" if tot["nap_t_s"] >= 20 else "VAN KHONG DU (< 20 t/s)"
        print(f"\n    tốt nhất ub={tot['ub']} -> {tot['nap_t_s']} t/s  [{cho}]")
        print(f"    4.000 token nạp mất {4000 / tot['nap_t_s']:.0f} giây")
    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
