# -*- coding: utf-8 -*-
"""Chạy N đề bốc ngẫu nhiên để đối chiếu với số của người khác báo về.

VÌ SAO KHÔNG GỌI THẲNG do_delta.py: nó ghi vào `ket_qua.json` và có logic bỏ
qua đề đã đo. Chạy thẳng thì Antigravity sẽ THỪA HƯỞNG kết quả của Claude thay
vì tự đo — và phép đối chiếu mất sạch ý nghĩa. Tệp này gọi thẳng `mot_de()`,
ghi ra tệp riêng, không đụng `ket_qua.json`.

BỐC BẰNG HẠT CỐ ĐỊNH, và hạt được GHI RA. Bốc rồi mới công bố là mở đường cho
"chạy vài lần, lấy lần đẹp". Hạt nằm trong tệp kết quả, ai cũng bốc lại được
đúng ba đề đó.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\doi_chieu.py [hạt] [số đề]
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

HAT = int(sys.argv[1]) if len(sys.argv) > 1 else 16082026
SO_DE = int(sys.argv[2]) if len(sys.argv) > 2 else 3
MODEL = "qwen2.5-coder:7b"

sys.argv = ["doi_chieu", "--lan=1"]        # ép SO_LAN=1 trước khi nạp do_delta
sys.path.insert(0, str(Path(__file__).resolve().parent))
import do_delta                                                # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

RA = Path("D:/alpha_bench/doi_chieu_claude.json")


def main() -> int:
    de = json.loads(Path("D:/alpha_bench/de_sach.json").read_text(encoding="utf-8"))
    rng = random.Random(HAT)
    chon = rng.sample(de, min(SO_DE, len(de)))
    print(f"  hạt {HAT} · bốc {len(chon)}/{len(de)} đề · {MODEL} · --lan=1\n")
    for d in chon:
        print(f"    {d['sha'][:8]} {d['nguon']:<32} [{d.get('loai_de','?')}]")
    print()

    kq = {}
    for i, d in enumerate(chon, start=1):
        t0 = time.monotonic()
        r = do_delta.mot_de(MODEL, d)
        kq[d["sha"][:8] + ":" + d["nguon"]] = r
        dau = {"dat": "✓", "truot": "✗", "khong_do_duoc": "·"}[r["trang_thai"]]
        print(f"  {dau} [{i}/{len(chon)}] {d['sha'][:8]} {d['nguon'][:30]:<30}"
              f" {r['trang_thai']:<14} {time.monotonic() - t0:>6.1f}s"
              f"  {r.get('vi_sao', '')}")

    dat = sum(1 for r in kq.values() if r["trang_thai"] == "dat")
    do_duoc = sum(1 for r in kq.values() if r["trang_thai"] in ("dat", "truot"))
    RA.write_text(json.dumps({"hat": HAT, "model": MODEL, "so_lan": 1,
                              "ket_qua": kq}, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    print(f"\n  ĐẠT {dat}/{do_duoc} đo được  ->  {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
