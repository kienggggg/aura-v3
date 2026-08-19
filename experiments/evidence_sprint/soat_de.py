# -*- coding: utf-8 -*-
"""Soát lại từng đề trước khi đưa vào bộ chấm.

VÌ SAO CẦN: `dung_de_alpha.py` nhận đề khi pytest thoát khác 0. Nhưng "khác 0"
gộp nhiều thứ rất khác nhau:

    1  test chạy và ĐỎ            -> đề THẬT
    2  gãy lúc thu gom (import)   -> mã hỏng thật, vẫn là đề (nhưng khác loại)
    3  lỗi nội bộ pytest          -> RÁC
    4  sai tham số dòng lệnh      -> RÁC, lỗi của giàn giáo
    5  không thu được test nào    -> RÁC, đề rỗng

Có 3 đề in "(không rõ)" ở cửa 2 vì không có dòng tóm tắt `x failed` — đúng cái
chỗ mã thoát 2/4/5 trốn được. Gộp cả năm mã vào một chữ "đỏ" là tự cho đề rác
lọt vào thước.

Đây là bước "verify trước, xoá sau" của CLAUDE.md, làm ngược lại: verify trước,
DÙNG sau.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\soat_de.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

DE = Path("D:/alpha_bench/de.json")
RA = Path("D:/alpha_bench/de_sach.json")

NGHIA = {0: "XANH (đề hỏng: lùi tệp mà test vẫn xanh)",
         1: "test ĐỎ", 2: "gãy lúc thu gom", 3: "lỗi nội bộ pytest",
         4: "sai tham số", 5: "không thu được test nào"}
NHAN = {1: "do", 2: "gay_import"}          # chỉ hai mã này là đề dùng được


def soat(d: dict) -> dict:
    repo = Path(d["repo"])
    py = str(repo / "venv" / "Scripts" / "python.exe")
    goc = Path(tempfile.mkdtemp())
    tam = goc / "de"
    try:
        subprocess.run(["git", "clone", "-q", str(repo), str(tam)], check=True,
                       timeout=300)
        for a in (["checkout", "-q", d["sha"]],
                  ["checkout", "-q", f"{d['sha']}~1", "--", d["nguon"]]):
            subprocess.run(["git", "-C", str(tam), *a], capture_output=True,
                           timeout=120)
        x = subprocess.run([py, "-X", "utf8", "-m", "pytest", *d["test"], "-q",
                            "--no-header", "--tb=line", "--ignore=tests/legacy",
                            "-p", "no:cacheprovider"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(tam), timeout=300)
        ra = (x.stdout or "") + (x.stderr or "")
        return {"ma_thoat": x.returncode,
                "nghia": NGHIA.get(x.returncode, f"mã lạ {x.returncode}"),
                "dau_ra": "\n".join(ra.strip().splitlines()[-4:])[:600]}
    except subprocess.TimeoutExpired:
        return {"ma_thoat": -1, "nghia": "TREO quá 300s", "dau_ra": ""}
    except Exception as e:                                       # noqa: BLE001
        return {"ma_thoat": -2, "nghia": f"{type(e).__name__}: {str(e)[:60]}",
                "dau_ra": ""}
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    if not DE.exists():
        print(f"  chưa có {DE}")
        return 2
    de = json.loads(DE.read_text(encoding="utf-8"))
    print(f"  soát {len(de)} đề\n")

    giu, bo = [], []
    dem: dict[int, int] = {}
    for i, d in enumerate(de, start=1):
        r = soat(d)
        ma = r["ma_thoat"]
        dem[ma] = dem.get(ma, 0) + 1
        ok = ma in NHAN
        (giu if ok else bo).append({**d, **r, "loai_de": NHAN.get(ma, "rac")})
        print(f"  {'✓' if ok else '✗'} [{i:>2}/{len(de)}] {d['sha'][:8]} "
              f"{d['nguon'][:30]:<30} mã {ma} — {r['nghia']}")
        if not ok and r["dau_ra"]:
            print(f"        {r['dau_ra'].splitlines()[-1][:100]}")

    RA.write_text(json.dumps(giu, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  phân bố mã thoát: "
          + "  ".join(f"{k}:{v}" for k, v in sorted(dem.items())))
    print(f"  GIỮ {len(giu)}  ·  BỎ {len(bo)}  ->  {RA}")
    for l, n in sorted({g['loai_de']: sum(1 for x in giu if x['loai_de'] == g['loai_de'])
                        for g in giu}.items()):
        print(f"     {l}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
