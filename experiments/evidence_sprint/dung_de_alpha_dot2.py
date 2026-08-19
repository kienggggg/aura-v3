# -*- coding: utf-8 -*-
"""Dựng đề phòng Delta ĐỢT 2 từ các kho mã nguồn bổ sung.

Tuân thủ nghiêm ngặt:
- KHÔNG nới cửa (3 cửa bất biến).
- KHÔNG ghi đè lên D:/alpha_bench/de.json (ghi ra de_dot2.json).
- Giữ nguyên ràng buộc: 1 đề = đúng 1 tệp mã nguồn lùi về commit trước.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

REPO = [
    Path("D:/hermes-agent"),
    Path("D:/xlkit"),
    Path("D:/jobradar"),
]
RA = Path("D:/alpha_bench")
RA_FILE = RA / "de_dot2.json"

TRAN_CUA3 = 200
BO_QUA = "--ignore=tests/legacy"
TOI_DA_TEP = 6


def git(repo: Path, *a, cwd: Path | None = None):
    return subprocess.run(["git", "-C", str(cwd or repo), *a],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def ung_vien(repo: Path) -> list[dict]:
    if not (repo / ".git").exists():
        return []
    ra = git(repo, "log", "--format=%H|%s")
    kq = []
    for dong in ra.stdout.splitlines():
        if "|" not in dong:
            continue
        sha, tieu_de = dong.split("|", 1)
        tep = [t for t in git(repo, "show", "--name-only", "--format=", sha)
               .stdout.split() if t.endswith(".py")]
        test = [t for t in tep if t.startswith("tests/") and "legacy" not in t]
        nguon = [t for t in tep if not t.startswith("tests/")]
        if test and 1 <= len(nguon) <= TOI_DA_TEP:
            kq.append({"repo": str(repo), "sha": sha, "tieu_de": tieu_de[:90],
                       "test": test, "nguon": nguon})
    return kq


def get_python_exe(repo: Path) -> str:
    # Ưu tiên venv của repo nếu có, fallback về D:/AURA_v3/venv
    v = repo / "venv" / "Scripts" / "python.exe"
    if v.exists():
        return str(v)
    return str(Path("D:/AURA_v3/venv/Scripts/python.exe"))


def chay(py: str, tam: Path, muc: list[str], tran: int) -> tuple[int, str, set[str]]:
    x = subprocess.run([py, "-X", "utf8", "-m", "pytest", *muc, "-q", "--no-header",
                        "--tb=no", "-rf", BO_QUA, "-p", "no:cacheprovider"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(tam), timeout=tran)
    ra = x.stdout or ""
    dong = [d for d in ra.splitlines() if "passed" in d or "failed" in d]
    do = {d.split()[1] for d in ra.splitlines()
          if d.startswith("FAILED ") and len(d.split()) > 1}
    return x.returncode, (dong[-1] if dong else "(không rõ)"), do


def mot_commit(uv: dict, in_) -> list[dict]:
    repo = Path(uv["repo"])
    py = get_python_exe(repo)
    goc = Path(tempfile.mkdtemp())
    tam = goc / "de"
    try:
        subprocess.run(["git", "clone", "-q", str(repo), str(tam)], check=True,
                       timeout=300)
        git(repo, "checkout", "-q", uv["sha"], cwd=tam)

        ma, tt, _ = chay(py, tam, uv["test"], 300)
        if ma != 0:
            in_(f"      bỏ commit: test đã đỏ sẵn ở lời giải · {tt}")
            return []

        de = []
        for f in uv["nguon"]:
            git(repo, "checkout", "-q", f"{uv['sha']}~1", "--", f, cwd=tam)
            try:
                m, t, _ = chay(py, tam, uv["test"], 300)
            except subprocess.TimeoutExpired:
                m, t = 0, "treo"
            git(repo, "checkout", "-q", uv["sha"], "--", f, cwd=tam)
            if m != 0:
                de.append({"repo": uv["repo"], "sha": uv["sha"],
                           "tieu_de": uv["tieu_de"], "test": uv["test"],
                           "nguon": f, "cua2": t})

        if not de:
            return []
        try:
            _, t3, nen_do = chay(py, tam, ["tests"], TRAN_CUA3)
        except subprocess.TimeoutExpired:
            in_("      bỏ commit: cả bộ test treo")
            return []
        for d in de:
            d["cua3"] = t3
            d["do_nen"] = sorted(nen_do)
        if nen_do:
            in_(f"      (đỏ nền {len(nen_do)} test — bộ chấm sẽ trừ đi)")
        return de
    except Exception as e:
        in_(f"      bỏ commit: {type(e).__name__}: {str(e)[:60]}")
        return []
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    han = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tat_ca: list[dict] = []
    for r in REPO:
        if not r.exists():
            continue
        uv = ung_vien(r)
        print(f"  {r.name}: {len(uv)} commit ứng viên "
              f"({sum(len(x['nguon']) for x in uv)} tệp mã để thử)")
        tat_ca += uv

    RA.mkdir(parents=True, exist_ok=True)
    dat: list[dict] = []
    for i, uv in enumerate(tat_ca, start=1):
        if len(dat) >= han:
            break
        t0 = time.monotonic()
        ra = mot_commit(uv, print)
        giay = time.monotonic() - t0
        for d in ra:
            dat.append(d)
            print(f"  ✓ [{len(dat):>2}] {uv['sha'][:8]} {d['nguon'][:34]:<34}"
                  f"{d['cua2'][:30]}")
        if not ra:
            print(f"  · [{i:>3}/{len(tat_ca)}] {uv['sha'][:8]} "
                  f"không ra đề {giay:>6.1f}s")
        RA_FILE.write_text(json.dumps(dat, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    print(f"\n  {len(dat)} ĐỀ HỢP LỆ (ĐỢT 2) / {len(tat_ca)} commit ứng viên"
          f"  ->  {RA_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
