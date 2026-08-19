# -*- coding: utf-8 -*-
"""Mổ con số 0/34 ra làm ba kỹ năng, vì "thua" không nói được thua ở đâu.

M0 ra 0/34. Nhưng sửa một lỗi gồm ít nhất ba việc rất khác nhau, và một con số
gộp cả ba thì không quyết được việc gì tiếp theo:

    1. ĐỊNH VỊ  — hàm nào hỏng?
    2. SỬA      — cho đúng hàm rồi thì viết được bản vá không?
    3. TỰ KIỂM  — nhìn một bản vá, biết nó xanh hay đỏ không?

Vì sao chấm được bằng máy: **ta có sẵn đáp án**. Commit thật cho biết đúng hàm
nào đã đổi. Không phải nhờ ai chấm, không phải đọc bằng mắt.

Vì sao đáng làm: nếu model ĐỊNH VỊ ĐƯỢC mà không sửa được → công cụ có cửa giúp.
Nếu nó không định vị nổi → thêm công cụ cũng vô ích, câu hỏi chuyển thẳng sang
cỡ model. Một con số 0 nói "thua"; ba con số nói "thua ở đâu".

CHI PHÍ (tính theo tốc độ nạp ĐO ĐƯỢC 17,3 tok/s, không phải ước đoán):
    kỹ năng 1  ~1.200 token vào  ->  ~80 giây/đề  ->  34 đề ≈ 45 phút
    kỹ năng 2  ~1.500 token vào  ->  ~160 giây/đề + pytest
    kỹ năng 3  2 lượt/đề         ->  ~160 giây/đề
Nên mặc định CHỈ chạy kỹ năng 1. Hai cái kia phải bật bằng cờ.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\mo_ba_ky_nang.py [--ky-nang=1,2,3]
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

MODEL = "qwen2.5-coder:7b"
DE = Path("D:/alpha_bench/de_sach.json")
RA = Path("D:/alpha_bench/ba_ky_nang.json")
CHON = {int(x) for x in
        next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--ky-nang=")),
             "1").split(",")}
TRAN_TEST = 2500


def hoi(prompt: str, npred: int = 220) -> tuple[float, str]:
    b = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                    "think": False, "keep_alive": "15m",
                    "options": {"seed": 42, "temperature": 0.2,
                                "num_predict": npred, "num_ctx": 8192}}).encode()
    r = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                               headers={"Content-Type": "application/json"},
                               method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=900) as x:
        k = json.loads(x.read().decode())
    return time.monotonic() - t0, (k.get("response") or "").strip()


def git(repo: str, *a) -> str:
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def dap_an_dinh_vi(d: dict) -> tuple[set[str], list[str], str]:
    """ĐÁP ÁN lấy từ commit thật: những hàm/lớp mà lời giải ĐÃ ĐỘNG VÀO.

    Cách lấy: đọc số dòng trong hunk của diff, rồi ánh xạ sang cây AST của bản
    SAU khi sửa. Không đoán theo tên, không đoán theo thứ tự — hai thứ đã từng
    làm hỏng sổ soát link (30 tóm tắt đúng nội dung mà sai URL).
    """
    repo = d["repo"]
    ma_moi = git(repo, "show", f"{d['sha']}:{d['nguon']}")
    ma_cu = git(repo, "show", f"{d['sha']}~1:{d['nguon']}")
    diff = git(repo, "diff", f"{d['sha']}~1", d["sha"], "--", d["nguon"])

    dong_doi: set[int] = set()
    for m in re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff):
        d0, n = int(m.group(1)), int(m.group(2) or 1)
        dong_doi |= set(range(d0, d0 + max(n, 1)))

    try:
        cay = ast.parse(ma_moi)
    except SyntaxError:
        return set(), [], ma_cu
    nut_all = [n for n in ast.walk(cay)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    ten_all = [n.name for n in nut_all]

    # Gán mỗi dòng đã đổi cho nút TRONG CÙNG chứa nó, không gán cho mọi nút bao
    # ngoài. Thân lớp bao trùm thân phương thức, nên nhận cả lớp là mở rộng đáp
    # án vô cớ: model trả lời "OllamaGateway" sẽ luôn trúng dù chỗ sửa thật nằm
    # ở "_messages". Đó đúng kiểu thước mềm đã làm hỏng 5 phép chấm trước đây.
    dap = set()
    for dong in dong_doi:
        trong = [n for n in nut_all
                 if n.lineno <= dong <= (n.end_lineno or n.lineno)]
        if trong:
            dap.add(min(trong, key=lambda n: (n.end_lineno or n.lineno) - n.lineno).name)
    return dap, sorted(set(ten_all)), ma_cu


def ky_nang_1(d: dict, dap: set[str], ten_all: list[str], test: str, loi: str) -> dict:
    p = ("Một test Python đang ĐỎ. Hãy chỉ ra ĐÚNG MỘT hàm hoặc lớp cần sửa.\n"
         "Chỉ trả về TÊN, không giải thích, không viết mã.\n\n"
         f"=== CÁC HÀM/LỚP CÓ TRONG {d['nguon']} ===\n" + ", ".join(ten_all) + "\n\n"
         f"=== TỆP TEST ===\n{test}\n\n"
         f"=== PYTEST BÁO LỖI ===\n{loi}\n\n"
         "=== TÊN HÀM CẦN SỬA ===\n")
    giay, ra = hoi(p, 40)
    # So bằng ĐỐI CHIẾU TỪ nguyên vẹn, không dò chuỗi con: "ai" từng khớp bên
    # trong "thứ hai" và làm hỏng 5 phép chấm.
    tu = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ra))
    dat = bool(tu & dap)
    return {"dat": dat, "giay": round(giay, 1), "model_tra": ra[:80],
            "dap_an": sorted(dap)}


def _than(ma: str, ten: str) -> str:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ""
    dong = ma.splitlines(keepends=True)
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and n.name == ten:
            return "".join(dong[n.lineno - 1:n.end_lineno])
    return ""


def ky_nang_2(d: dict, dap: set[str], test: str, loi: str, ma_cu: str,
              tam: Path, py: str) -> dict:
    """ĐƯA SẴN đúng hàm cần sửa, rồi mới hỏi bản vá.

    Vì sao đáng đo riêng: kỹ năng 1 cho thấy 55% số lần model trả lời bằng tên
    hàm trong tệp TEST — nó không giữ được ranh giới phạm vi. Bệnh đó có thể
    đang đè cả điểm SỬA ở M0 (0/34). Ở đây ta gỡ hẳn bệnh phạm vi ra: chỉ tận
    tay hàm nào, chỉ hỏi mỗi việc viết lại hàm đó.

    Còn 0 thì mới kết luận được là model KHÔNG VIẾT NỔI bản vá — chứ không phải
    nó lạc chỗ.
    """
    ten = sorted(dap)[0]
    than_cu = _than(ma_cu, ten)
    if not than_cu:
        return {"dat": None, "vi_sao": "không trích được thân hàm"}
    p = ("Hàm dưới đây có lỗi làm test ĐỎ. Viết lại TOÀN VĂN hàm đã sửa.\n"
         "Chỉ mã Python, không giải thích, không khối markdown.\n\n"
         f"=== HÀM CẦN SỬA ({ten} trong {d['nguon']}) ===\n{than_cu}\n\n"
         f"=== TỆP TEST ===\n{test}\n\n"
         f"=== PYTEST BÁO LỖI ===\n{loi}\n\n"
         "=== HÀM ĐÃ SỬA ===\n")
    giay, ra = hoi(p, 900)

    import do_delta as D                                        # noqa: PLC0415
    f = tam / d["nguon"]
    goc_ma = f.read_text(encoding="utf-8", errors="replace")
    sua, hong = D.ap_ham(goc_ma, ra)
    if hong:
        return {"dat": False, "vi_sao": f"định dạng: {hong}", "giay": round(giay, 1)}
    f.write_text(sua, encoding="utf-8")
    try:
        m2, _, _ = D.pytest_(py, tam, d["test"], 300)
        them = (D.pytest_(py, tam, ["tests"], 200)[2] - set(d.get("do_nen") or ())) \
            if m2 == 0 else set()
    except subprocess.TimeoutExpired:
        return {"dat": None, "vi_sao": "test treo", "giay": round(giay, 1)}
    finally:
        f.write_text(goc_ma, encoding="utf-8")                  # trả lại trạng thái đề
    return {"dat": bool(m2 == 0 and not them), "giay": round(giay, 1),
            "ham": ten, "lam_do_them": sorted(them)[:3]}


def ky_nang_3(d: dict, dap: set[str], test: str, ma_cu: str) -> dict:
    """Cho xem một hàm, hỏi 'test có xanh không'. Hai lượt: bản ĐÚNG và bản HỎNG."""
    repo, ten = d["repo"], sorted(dap)[0]
    def than(ma: str) -> str:
        try:
            cay = ast.parse(ma)
        except SyntaxError:
            return ""
        dong = ma.splitlines(keepends=True)
        for n in ast.walk(cay):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                    and n.name == ten:
                return "".join(dong[n.lineno - 1:n.end_lineno])
        return ""
    cap = [(than(git(repo, "show", f"{d['sha']}:{d['nguon']}")), True),
           (than(ma_cu), False)]
    dung = 0
    tong = 0.0
    for ma, that in cap:
        if not ma:
            return {"dat": None, "vi_sao": "không trích được thân hàm"}
        p = ("Đọc hàm dưới đây và test đi kèm. Test sẽ XANH hay ĐỎ?\n"
             "Chỉ trả lời đúng một từ: XANH hoặc ĐỎ.\n\n"
             f"=== HÀM ===\n{ma}\n\n=== TEST ===\n{test}\n\n=== TRẢ LỜI ===\n")
        giay, ra = hoi(p, 12)
        tong += giay
        doan = "XANH" in ra.upper()
        dung += (doan == that)
    return {"dat": dung == 2, "dung": dung, "giay": round(tong, 1)}


def main() -> int:
    de = json.loads(DE.read_text(encoding="utf-8"))
    so = json.loads(RA.read_text(encoding="utf-8")) if RA.exists() else {}
    print(f"  {len(de)} đề · {MODEL} · kỹ năng {sorted(CHON)}\n")

    dem = {1: [0, 0], 2: [0, 0], 3: [0, 0]}
    bo = 0
    for i, d in enumerate(de, start=1):
        khoa = f"{d['sha'][:8]}:{d['nguon']}"
        r = so.get(khoa) or {}
        try:
            dap, ten_all, ma_cu = dap_an_dinh_vi(d)
        except Exception as e:                                   # noqa: BLE001
            print(f"  · [{i:>2}] {khoa[:40]:<42} không lấy được đáp án: {e}")
            bo += 1
            continue
        if not dap or not ten_all:
            # Lời giải sửa ở ngoài mọi hàm (import, hằng cấp module) -> đề này
            # không đo được kỹ năng ĐỊNH VỊ. Ghi riêng, không tính là trượt.
            print(f"  · [{i:>2}] {khoa[:40]:<42} lời giải nằm ngoài hàm nào")
            bo += 1
            continue

        goc = Path(tempfile.mkdtemp())
        tam = goc / "de"
        try:
            subprocess.run(["git", "clone", "-q", d["repo"], str(tam)],
                           check=True, timeout=300)
            for a in (["checkout", "-q", d["sha"]],
                      ["checkout", "-q", f"{d['sha']}~1", "--", d["nguon"]]):
                subprocess.run(["git", "-C", str(tam), *a], capture_output=True,
                               timeout=120)
            test = "\n\n".join((tam / t).read_text(encoding="utf-8", errors="replace")
                               for t in d["test"])[:TRAN_TEST]
            x = subprocess.run([str(Path(d["repo"]) / "venv/Scripts/python.exe"),
                                "-X", "utf8", "-m", "pytest", *d["test"], "-q",
                                "--no-header", "--tb=line", "--ignore=tests/legacy",
                                "-p", "no:cacheprovider"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=str(tam), timeout=300)
            loi = (x.stdout or "")[-1200:]

            if 1 in CHON and "k1" not in r:
                r["k1"] = ky_nang_1(d, dap, ten_all, test, loi)
            if 2 in CHON and "k2" not in r:
                r["k2"] = ky_nang_2(d, dap, test, loi, ma_cu, tam,
                                    str(Path(d["repo"]) / "venv/Scripts/python.exe"))
            if 3 in CHON and "k3" not in r:
                r["k3"] = ky_nang_3(d, dap, test, ma_cu)
        finally:
            shutil.rmtree(goc, ignore_errors=True)
        so[khoa] = r
        RA.write_text(json.dumps(so, ensure_ascii=False, indent=2), encoding="utf-8")

        bao = []
        for k, nhan in ((1, "k1"), (2, "k2"), (3, "k3")):
            if nhan in r and r[nhan].get("dat") is not None:
                dem[k][1] += 1
                dem[k][0] += bool(r[nhan]["dat"])
                bao.append(f"{nhan}={'✓' if r[nhan]['dat'] else '✗'}")
        print(f"  [{i:>2}/{len(de)}] {d['nguon'][:26]:<28}{' '.join(bao):<12}"
              f"đáp án={','.join(sorted(dap))[:26]:<28}model={r.get('k1',{}).get('model_tra','')[:24]}")

    print()
    for k, ten in ((1, "ĐỊNH VỊ (chỉ đúng hàm hỏng)"),
                   (2, "SỬA (đã đưa sẵn đúng hàm)"),
                   (3, "TỰ KIỂM (biết xanh hay đỏ)")):
        if dem[k][1]:
            print(f"  kỹ năng {k} · {ten}: {dem[k][0]}/{dem[k][1]}")
    print(f"  {bo} đề không đo được kỹ năng định vị (lời giải nằm ngoài hàm)")
    print(f"  -> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
