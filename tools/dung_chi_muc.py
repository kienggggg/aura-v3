# -*- coding: utf-8 -*-
"""Dựng chỉ mục cho `core/tra_cuu.py`. Chạy TAY, một lần, không nằm trên đường chat.

    venv\\Scripts\\python.exe tools/dung_chi_muc.py

Đo 08/09/2026: **437 đoạn · 649,8 giây** (10,8 phút) · chỉ mục 6.659.925 byte.
(Nguyên mẫu chưa lọc `docs/lich_su/` là 946 đoạn · 1.058 giây · 13.050.301 byte
— kế hoạch còn nhắc con số ấy, nhưng bản chạy thật nhỏ hơn một nửa.)
Nhét việc này vào đường chat thì lượt đầu mỗi ngày treo 11 phút — nên nó ở đây,
trong `tools/`, ngoài hàng rào `test_v3_ranh_gioi.py`.

CORPUS — bỏ `docs/lich_su/`, và đó là CURATION chứ không phải mẹo. 60+ tệp bàn
giao **đã bị thay thế** chiếm 511/946 đoạn và chen chỗ của `CLAUDE.md`. Đo bộ A:
bỏ chúng đi thì RRF top-1 lên 6/10 -> 8/10. Kho tra cứu giữ SỰ THẬT HIỆN TẠI,
không giữ biên bản đã hết hiệu lực.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core.paths import PROJECT_ROOT  # noqa: E402
from core.tra_cuu import CHI_MUC, MODEL_NHUNG  # noqa: E402

CAP_CHU = 1500
LO = 128
BO_THU_MUC = ("docs/lich_su/",)
NGOAI = (Path(r"D:\KHO_CONG_NGHE.md"), Path(r"D:\CONG_NGHE_TONG_HOP.md"))


def cat_doan(tep: Path, ten: str) -> list[dict]:
    """Cắt theo TIÊU ĐỀ markdown, không cắt mù theo số ký tự.

    Cắt mù thì một câu trả lời bị xé đôi giữa hai đoạn và cả hai đều điểm thấp.
    """
    van = tep.read_text(encoding="utf-8", errors="replace")
    ra, tieu, buf = [], "(mở đầu)", []

    def xa():
        n = "\n".join(buf).strip()
        while n:
            ra.append({"tep": ten, "tieu_de": tieu, "noi_dung": n[:CAP_CHU]})
            n = n[CAP_CHU:]

    for d in van.splitlines():
        if d.startswith("#"):
            xa()
            buf = []
            tieu = d.lstrip("#").strip()
        else:
            buf.append(d)
    xa()
    return ra


def gom_tep() -> list[tuple[Path, str]]:
    r = subprocess.run(["git", "ls-files", "*.md"], cwd=str(PROJECT_ROOT),
                       capture_output=True, text=True, encoding="utf-8")
    ds = [(PROJECT_ROOT / d, d) for d in r.stdout.split()
          if (PROJECT_ROOT / d).is_file()
          and not any(b in d for b in BO_THU_MUC)]
    ds += [(p, p.name) for p in NGOAI if p.is_file()]
    return ds


def nhung(lo: list[str]) -> list[list[float]]:
    import httpx
    r = httpx.post("http://127.0.0.1:11434/api/embed",
                   json={"model": MODEL_NHUNG, "input": lo,
                         "keep_alive": "30m"}, timeout=1800.0)
    r.raise_for_status()
    return r.json()["embeddings"]


def main() -> int:
    tep = gom_tep()
    doan: list[dict] = []
    for p, ten in tep:
        doan.extend(cat_doan(p, ten))
    print(f"{len(tep)} tệp · {len(doan)} đoạn")

    vector: list[list[float]] = []
    t0 = time.perf_counter()
    for i in range(0, len(doan), LO):
        lo = [f"{d['tieu_de']}\n{d['noi_dung']}" for d in doan[i:i + LO]]
        try:
            vector.extend(nhung(lo))
        except Exception as e:
            # FAIL-CLOSED: chỉ mục nửa vời tệ hơn không có chỉ mục, vì nó chạy
            # được và không ai biết nửa sau bị bỏ.
            print(f"HỎNG ở đoạn {i}: {type(e).__name__}: {e}")
            print("KHÔNG ghi chỉ mục nửa vời. Kiểm Ollama rồi chạy lại.")
            return 2
        xong = min(i + LO, len(doan))
        t = time.perf_counter() - t0
        print(f"  {xong:>4}/{len(doan)}  {t:6.1f}s  "
              f"(còn ~{t / xong * (len(doan) - xong):5.0f}s)", flush=True)

    assert len(vector) == len(doan), f"{len(vector)} vector / {len(doan)} đoạn"
    CHI_MUC.parent.mkdir(parents=True, exist_ok=True)
    CHI_MUC.write_text(json.dumps({"doan": doan, "vector": vector}),
                       encoding="utf-8")
    print(f"\nxong {time.perf_counter() - t0:.1f}s · "
          f"{CHI_MUC} · {CHI_MUC.stat().st_size:,} byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
