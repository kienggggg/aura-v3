# -*- coding: utf-8 -*-
"""Dựng đề cho phòng Delta từ LỊCH SỬ GIT THẬT của hai repo.

Vì sao không tự viết đề: nếu Codex và tôi soạn bài, chúng tôi sẽ vô thức soạn
loại bài mà cách làm của mình giải được. Đó không phải nghi ngờ thiện chí, đó
là cách thiên vị hoạt động. Lỗi trong lịch sử git là lỗi THẬT, đã sửa THẬT, và
không ai chọn nó cho phép đo này.

MỘT ĐỀ = MỘT TỆP MÃ NGUỒN bị kéo lùi về commit trước, trong khi test giữ ở
commit sau. Commit đụng 3 tệp thì thử lùi RIÊNG từng tệp: tệp nào một mình nó
làm test đỏ thì tệp đó là một đề độc lập.

  cửa 1  test của commit XANH ở trạng thái lời giải   -> không thì bỏ cả commit
  cửa 2  lùi riêng tệp X      -> test phải ĐỎ          -> đỏ thì X thành một đề
  cửa 3  cả bộ test XANH ở trạng thái lời giải        -> không thì bỏ cả commit

Cửa 3 chạy MỘT LẦN cho mỗi commit chứ không mỗi đề: nó kiểm tính chất của
commit, không phải của tệp. Và chỉ chạy khi commit đã đẻ ra ít nhất một đề —
bộ test mất 64s, không tiêu nó cho commit sẽ bỏ.

SỐ ĐO CỦA KHO NÀY (đo 16/08, không phải đoán):
  222 commit v2, chỉ 61 cái đụng tệp test  -> đó là TRẦN TUYỆT ĐỐI
  trong 61 cái: 14 đụng 1 tệp mã · 13 đụng 2 · 14 đụng 3 · 18 đụng ≥4
Con số 35 là chỉ tiêu trong kế hoạch, không phải sự thật về kho này.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\dung_de_alpha.py [số đề tối đa]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# line_buffering: chạy nền thì stdout ra TỆP, mà ghi ra tệp Python đệm theo khối
# 8KB — lần đầu chạy nền tệp log rỗng suốt trong khi 6 pytest con đang chạy thật.
# Không có dòng này thì "đang chạy" và "đã treo" nhìn giống hệt nhau.
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

REPO = [Path("D:/AURA_OS_v2"), Path("D:/AURA_v3")]
RA = Path("D:/alpha_bench")

# Thư mục mã nguồn: lấy từ ĐO phân bố thật, không từ trí nhớ. Bản đầu chỉ liệt
# core/interface/factory/tools và bỏ sót arena — riêng arena đã 101 lượt.
THU_MUC = ("core", "arena", "interface", "tools", "skills", "ui", "scripts",
           "factory", "evolution", "brains", "agents")

# 200s = 64,11s (đo: v2 380 passed + 1 skipped) × 3. Bản đầu để 420s và đề số 1
# bị loại ở 423,1s — loại vì GIÀN GIÁO TREO chứ không phải vì đề dở. Chỗ treo là
# tests/legacy: trong đó có script gọi sys.exit() ở cấp module, pytest gặp là
# chết cả phiên (CLAUDE.md mục 1). Trần rộng không cứu được, phải BỎ QUA nó.
TRAN_CUA3 = 200
BO_QUA = "--ignore=tests/legacy"
TOI_DA_TEP = 6          # commit đụng quá 6 tệp mã thì không còn là "một lỗi"


def git(repo: Path, *a, cwd: Path | None = None):
    return subprocess.run(["git", "-C", str(cwd or repo), *a],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def ung_vien(repo: Path) -> list[dict]:
    ra = git(repo, "log", "--format=%H|%s")          # cả lịch sử, không cắt
    kq = []
    for dong in ra.stdout.splitlines():
        if "|" not in dong:
            continue
        sha, tieu_de = dong.split("|", 1)
        tep = [t for t in git(repo, "show", "--name-only", "--format=", sha)
               .stdout.split() if t.endswith(".py")]
        test = [t for t in tep if t.startswith("tests/") and "legacy" not in t]
        nguon = [t for t in tep
                 if not t.startswith("tests/") and t.split("/")[0] in THU_MUC]
        if test and 1 <= len(nguon) <= TOI_DA_TEP:
            kq.append({"repo": str(repo), "sha": sha, "tieu_de": tieu_de[:90],
                       "test": test, "nguon": nguon})
    return kq


def chay(py: str, tam: Path, muc: list[str], tran: int) -> tuple[int, str, set[str]]:
    """Trả (mã thoát, dòng tóm tắt, TẬP test đỏ).

    Phải trả tập tên test chứ không chỉ mã thoát: bộ test ở các commit cũ đỏ sẵn
    3-6 cái vì venv hôm nay chạy mã tháng trước. Đòi "xanh tuyệt đối" thì loại
    sạch commit tốt — đo được ở 6 commit đầu, 6/6 bị loại oan.
    """
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
    py = str(repo / "venv" / "Scripts" / "python.exe")
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
        # KHÔNG loại khi cả bộ đỏ. Ghi lại ĐỎ NỀN = tập test vốn đã đỏ ở trạng
        # thái lời giải. Bộ chấm sẽ đòi "không đỏ thêm ngoài tập này", chứ không
        # đòi xanh tuyệt đối — thứ mà repo này chưa bao giờ có.
        # CỬA 4 (thêm 18/08/2026) — đề phải có lời giải NẰM TRONG tầm nhìn.
        #
        # Ba cửa trên chỉ chứng minh "có một lỗi thật, test bắt được". Chúng
        # KHÔNG chứng minh model nhìn thấy được chỗ sửa. Bộ chấm đưa cho model
        # một VÙNG CẮT của tệp, và ở 28/38 đề đầu tiên hàm cần sửa nằm NGOÀI
        # vùng đó — đề bất khả thi, model giỏi đến đâu cũng chịu.
        #
        # Hai ngày liền mọi điểm 0 đều nhiễm lỗi này, và nó chỉ lộ ra khi áp
        # cái ngưỡng ghi trước lúc đo: "cloud điểm thấp -> nghi cái THƯỚC
        # trước, đừng nghi model".
        #
        # Dùng lời giải thật ở ĐÂY là hợp lệ — nó chỉ để KIỂM đề có giải được
        # không, không bao giờ đi vào lời nhắc.
        import do_delta as _dd
        for d in list(de):
            ma_cu = git(repo, "show", f"{uv['sha']}~1:{d['nguon']}").stdout
            test_day = (chr(10) * 2).join(
                git(repo, "show", f"{uv['sha']}:{t}").stdout for t in uv["test"])
            vung = _dd.chon_vung(ma_cu, test_day)
            dap = _ham_da_doi(repo, uv["sha"], d["nguon"])
            trong = bool(dap) and all(
                (f"def {x}" in vung or f"class {x}" in vung) for x in dap)
            if not trong:
                in_(f"      loại (cửa 4): lời giải ngoài vùng — {d['nguon']} "
                    f"[{','.join(sorted(dap)) or 'không rõ hàm'}]")
                de.remove(d)
        if not de:
            return []

        for d in de:
            d["cua3"] = t3
            d["do_nen"] = sorted(nen_do)
        if nen_do:
            in_(f"      (đỏ nền {len(nen_do)} test — bộ chấm sẽ trừ đi)")
        return de
    except Exception as e:                                       # noqa: BLE001
        in_(f"      bỏ commit: {type(e).__name__}: {str(e)[:60]}")
        return []
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def _ham_da_doi(repo: Path, sha: str, nguon: str) -> set[str]:
    """Commit thật đã đổi những hàm/lớp nào — dùng để KIỂM đề, không đưa vào prompt."""
    import ast as _ast
    import re as _re
    ma_moi = git(repo, "show", f"{sha}:{nguon}").stdout
    diff = git(repo, "diff", f"{sha}~1", sha, "--", nguon).stdout
    dong_doi: set[int] = set()
    for m in _re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff):
        d0, n = int(m.group(1)), int(m.group(2) or 1)
        dong_doi |= set(range(d0, d0 + max(n, 1)))
    try:
        cay = _ast.parse(ma_moi)
    except SyntaxError:
        return set()
    nut = [n for n in _ast.walk(cay)
           if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef))]
    ra = set()
    for dong in dong_doi:
        trong = [n for n in nut if n.lineno <= dong <= (n.end_lineno or n.lineno)]
        if trong:
            ra.add(min(trong, key=lambda n: (n.end_lineno or n.lineno) - n.lineno).name)
    return ra


def main() -> int:
    han = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    tat_ca: list[dict] = []
    for r in REPO:
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
        (RA / "de.json").write_text(json.dumps(dat, ensure_ascii=False, indent=2),
                                    encoding="utf-8")

    print(f"\n  {len(dat)} ĐỀ HỢP LỆ / {len(tat_ca)} commit ứng viên"
          f"  ->  {RA / 'de.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
