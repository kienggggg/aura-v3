# -*- coding: utf-8 -*-
"""Chạy MỌI cửa JS trong `tests/`, thoát mã 1 nếu có cái nào đỏ.

VÌ SAO CÓ TỆP NÀY, 26/08/2026:

`tests/test_the_connector_ui.js` ĐỎ SUỐT HAI NGÀY mà không ai thấy. Nó chốt
cứng "12 thẻ lệnh" từ 24/08; ngày 25/08 khay thẻ thêm năm thẻ thành 17, và
phép so `=== 12` đỏ từ lúc ấy.

Không ai thấy vì thói quen chạy cửa JS là gõ TÊN TỪNG TỆP:

    node --test tests/test_moi_nut_co_handler.js
    node --test tests/test_the_parity.js

Tệp nào không nằm trong thói quen ấy thì không ai chạy. Bên Python không có
bệnh này vì `pytest tests -q` tự quét cả thư mục.

Bắt được hôm nay chỉ vì một lần tình cờ gõ `for t in tests/*.js`. Đó là may,
không phải quy trình — nên dựng tệp này để lần sau không cần may.

Cách chạy:

    venv\\Scripts\\python.exe tools\\chay_cua_js.py

Thoát mã:  0 = mọi cửa xanh · 1 = có cửa đỏ · 2 = không chạy được (thiếu node)
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GOC = Path(__file__).resolve().parent.parent
THU_MUC_TEST = GOC / "tests"


def _so(kx: str, ten: str) -> int:
    """Đọc `# pass 5` / `ℹ pass 5` từ kết xuất của `node --test`."""
    m = re.search(rf"^[#ℹ]\s*{ten}\s+(\d+)", kx, re.MULTILINE)
    return int(m.group(1)) if m else -1


def main() -> int:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print("KHÔNG CHẠY ĐƯỢC: không gọi được `node`.")
        return 2

    cac_tep = sorted(THU_MUC_TEST.glob("*.js"))
    if not cac_tep:
        print("KHÔNG CHẠY ĐƯỢC: không thấy tệp .js nào trong tests/.")
        return 2

    print(f"  {len(cac_tep)} cửa JS trong tests/\n")
    tong_dat = tong_do = 0
    cac_do: list[str] = []

    for t in cac_tep:
        r = subprocess.run(
            ["node", "--test", str(t.relative_to(GOC)).replace("\\", "/")],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(GOC))
        kx = (r.stdout or "") + (r.stderr or "")
        dat, do = _so(kx, "pass"), _so(kx, "fail")
        tong_dat += max(dat, 0)
        tong_do += max(do, 0)
        nhan = "ĐẠT" if r.returncode == 0 else "ĐỎ"
        if r.returncode != 0:
            cac_do.append(t.name)
        print(f"  {t.name:<36} {dat:>3} đạt · {do:>2} đỏ   {nhan}")

    print(f"\n  TỔNG: {tong_dat} đạt · {tong_do} đỏ")
    if cac_do:
        print("  ĐỎ: " + " · ".join(cac_do))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
