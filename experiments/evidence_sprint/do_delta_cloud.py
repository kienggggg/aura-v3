# -*- coding: utf-8 -*-
"""M3 — đổi MODEL, giữ nguyên mọi thứ còn lại.

M0/M1/kỹ năng 2 đều đổi GIÀN GIÁO và đều ra 0. Đây là biến cuối cùng chưa ai
động: model. Cùng 38 đề, cùng ba cửa, cùng bộ vá theo tên hàm, cùng cách chấm —
chỉ thay chỗ gọi từ Ollama cục bộ sang Gemini 2.5-flash.

Trả lời đúng một câu: con số 0 kia là của MÁY NÀY, hay của AI nói chung trên mã
của AURA?

Ghi ra tệp RIÊNG (`ket_qua_cloud.json`) để không đụng cột cục bộ.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_delta_cloud.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.argv = ["cloud", "--lan=1"]        # ép SO_LAN=1 trước khi nạp do_delta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import do_delta as D                                            # noqa: E402


def _env(tep: Path) -> dict:
    kv = {}
    for l in tep.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


E = _env(Path("D:/AURA_OS_v2/.env"))
BASE = E["OPENAI_BASE_URL"].rstrip("/")
KHOA = E["OPENAI_API_KEY"]
TEN_MODEL = E.get("OPENAI_MODEL", "gemini-2.5-flash")


def hoi_cloud(model, ten, ma, test, loi, lan_truoc=None):
    """Cùng CHỮ KÝ và cùng LỜI NHẮC như bản cục bộ — chỉ khác chỗ gửi đi.

    Giữ nguyên lời nhắc là bắt buộc: đổi cả model lẫn prompt thì số ra không
    quy được cho cái nào.
    """
    p = D.hoi.__wrapped__(model, ten, ma, test, loi, lan_truoc) \
        if hasattr(D.hoi, "__wrapped__") else None
    # Không gọi được prompt gốc thì dựng lại đúng như do_delta.hoi
    p = (
        "Bạn sửa lỗi trong mã Python. Test dưới đây đang ĐỎ.\n"
        f"Sửa MÃ NGUỒN ({ten}) cho test xanh. KHÔNG được sửa test.\n\n"
        "CÁCH TRẢ LỜI: viết lại TOÀN VĂN hàm cần sửa, từ dòng `def` tới hết "
        "thân hàm. Chỉ mã Python, không giải thích, không khối markdown.\n"
        "- Chỉ viết hàm nào bạn thực sự sửa, không chép lại cả tệp.\n"
        "- Hàm chưa có thì cứ viết mới, nó sẽ được thêm vào tệp.\n"
        "- Sửa được nhiều hàm thì viết lần lượt từng hàm.\n\n"
        f"=== MÃ NGUỒN ({ten}) ===\n{ma}\n"
        f"=== TỆP TEST ===\n{test}\n"
        f"=== TEST BÁO LỖI ===\n{loi}\n"
    )
    if lan_truoc:
        p += (f"\n=== LẦN TRƯỚC BẠN TRẢ LỜI (KHÔNG ĂN) ===\n{lan_truoc[0]}\n"
              f"=== VÌ SAO KHÔNG ĂN ===\n{lan_truoc[1]}\n"
              "Đừng lặp lại cách đó. Sửa khác đi.\n")
    p += "=== TRẢ LỜI ===\n"

    b = json.dumps({"model": TEN_MODEL,
                    "messages": [{"role": "user", "content": p}],
                    "temperature": 0.2}).encode()
    t0 = time.monotonic()
    for lan in range(4):
        try:
            r = urllib.request.Request(
                f"{BASE}/chat/completions", data=b, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {KHOA}"})
            with urllib.request.urlopen(r, timeout=300) as x:
                k = json.loads(x.read().decode())
            ra = (k["choices"][0]["message"].get("content") or "").strip()
            return time.monotonic() - t0, ra
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and lan < 3:
                cho = 20 * (lan + 1)      # tầng miễn phí có hạn mức phút
                print(f"      HTTP {e.code}, chờ {cho}s rồi thử lại")
                time.sleep(cho)
                continue
            raise
    return time.monotonic() - t0, ""


D.hoi = hoi_cloud
D.MODEL = [TEN_MODEL]
D.SO = Path("D:/alpha_bench/ket_qua_cloud.json")

if __name__ == "__main__":
    print(f"  M3 · {TEN_MODEL} qua {BASE}")
    print(f"  cùng 38 đề · cùng ba cửa · chỉ đổi model\n")
    raise SystemExit(D.main())
