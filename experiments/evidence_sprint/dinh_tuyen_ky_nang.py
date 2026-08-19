# -*- coding: utf-8 -*-
"""Định tuyến theo KỸ NĂNG, không theo phòng.

Ý tưởng đến từ hai chỗ gặp nhau:

  - SkillOrchestra (arXiv 2602.19672) mô hình hoá **năng lực VÀ chi phí của
    từng agent theo từng kỹ năng nhỏ**, rồi chọn theo đánh đổi hiệu năng-chi
    phí. Họ phải học bảng đó bằng RL.
  - Phép mổ ba kỹ năng ngày 17/08 đã ĐO SẴN bảng đó cho hai model của ta:

        kỹ năng            qwen2.5-coder:7b     gemini-2.5-flash
        định vị hàm hỏng   88% (khi đúng tệp)   chưa đo
        viết bản vá        0/34                 3/9 = 33%
        chi phí            353 s/đề, miễn phí   ~30 s/đề, 20 lượt/ngày

Chia theo PHÒNG thì cả hai nửa của một việc cùng đi một nơi, và nửa mạnh (88%)
bị nửa yếu (0%) kéo xuống 0. Chia theo KỸ NĂNG thì mỗi nửa đi đúng chỗ nó mạnh.

    chặng 1  cục bộ   : đọc danh sách hàm + test + lỗi -> gọi tên hàm hỏng
    chặng 2  cloud    : CHỈ nhận đúng hàm đó -> viết lại hàm đã sửa
    chặng 3  máy      : vá theo tên hàm (AST) + ba cửa chấm cũ

VÌ SAO ĐÁNG THỬ, và vì sao có thể THUA — nói trước để khỏi tự lừa:
  - Nếu hai chặng độc lập: 0,88 × 0,33 ≈ 29%, tức là THẤP HƠN cloud một mình
    (33%). Bù lại cloud chỉ nhận ~1 hàm thay vì 14.000 ký tự.
  - Nhưng cloud nhận đúng một hàm có thể LÀM TỐT HƠN 33%, vì hết phải tự dò
    trong vùng lớn. Kỹ năng 2 đã đo điều đó cho model cục bộ (0/16); chưa ai
    đo cho cloud.
  Hai khả năng ngược nhau, nên phải đo chứ không đoán.

ĐÁP ÁN THẬT chỉ dùng để CHẤM SAU, không bao giờ vào lời nhắc.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\dinh_tuyen_ky_nang.py
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.argv = ["dt", "--lan=1"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import do_delta as D                                            # noqa: E402
import mo_ba_ky_nang as M                                       # noqa: E402

DE = Path(os.environ.get("DELTA_DE") or "D:/alpha_bench/de_vong1.json")
RA = Path(os.environ.get("DELTA_KET_QUA") or "D:/alpha_bench/ket_qua_dinh_tuyen.json")
CUC_BO = "qwen2.5-coder:7b"


def _env(p: Path) -> dict:
    kv = {}
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


E = _env(Path("D:/AURA_OS_v2/.env"))
CLOUD = E.get("OPENAI_MODEL", "gemini-2.5-flash")


def hoi_cloud(prompt: str) -> tuple[float, str]:
    b = json.dumps({"model": CLOUD, "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}]}).encode()
    t0 = time.monotonic()
    for lan in range(4):
        try:
            r = urllib.request.Request(
                E["OPENAI_BASE_URL"].rstrip("/") + "/chat/completions",
                data=b, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {E['OPENAI_API_KEY']}"})
            with urllib.request.urlopen(r, timeout=300) as x:
                k = json.loads(x.read().decode())
            return time.monotonic() - t0, (k["choices"][0]["message"].get("content") or "").strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and lan < 3:
                time.sleep(20 * (lan + 1))
                continue
            raise
    return time.monotonic() - t0, ""


def _than_ham(ma: str, ten: str) -> str:
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


def _ten_ham(ma: str) -> list[str]:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(cay)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def mot_de(d: dict) -> dict:
    repo = Path(d["repo"])
    py = str(repo / "venv" / "Scripts" / "python.exe")
    goc = Path(tempfile.mkdtemp())
    tam = goc / "de"
    try:
        subprocess.run(["git", "clone", "-q", str(repo), str(tam)], check=True, timeout=300)
        for a in (["checkout", "-q", d["sha"]],
                  ["checkout", "-q", f"{d['sha']}~1", "--", d["nguon"]]):
            subprocess.run(["git", "-C", str(tam), *a], capture_output=True, timeout=120)

        f_nguon = tam / d["nguon"]
        ma = f_nguon.read_text(encoding="utf-8", errors="replace")
        test_day = "\n\n".join((tam / t).read_text(encoding="utf-8", errors="replace")
                               for t in d["test"])
        test = D.cat_dong(test_day, D.TRAN_TEST)
        _, loi, _ = D.pytest_(py, tam, d["test"], 300)
        ten_all = _ten_ham(ma)

        # ---- CHẶNG 1: cục bộ định vị (miễn phí) -------------------------
        #
        # CÓ VÒNG NHẮC LẠI (thêm 18/08). Lý do: 4 lần đo trên 4 việc khác nhau,
        # model 7B đều trả tên hàm nằm trong TỆP TEST thay vì tệp nguồn — nó
        # không giữ được ranh giới phạm vi. Nhưng ta CÓ SẴN danh sách tên hàm
        # thật, nên đây là thứ MÁY chặn được, không cần model khá hơn.
        #
        # Đếm riêng số lần phải nhắc: "trả lời đúng ngay" và "trả lời đúng sau
        # khi bị nhắc" là hai năng lực khác nhau, gộp lại là báo cáo một năng
        # lực model không có.
        def _hoi_cuc_bo(prompt: str) -> tuple[float, str]:
            b = json.dumps({"model": CUC_BO, "prompt": prompt, "stream": False,
                            "think": False, "keep_alive": "10m",
                            "options": {"seed": 42, "temperature": 0.2,
                                        "num_predict": 40, "num_ctx": 8192}}).encode()
            yc = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                                        headers={"Content-Type": "application/json"},
                                        method="POST")
            t0 = time.monotonic()
            with urllib.request.urlopen(yc, timeout=900) as r:
                ra = (json.loads(r.read().decode()).get("response") or "").strip()
            return time.monotonic() - t0, ra

        import re as _re
        p1 = ("Một test Python đang ĐỎ. Hãy chỉ ra ĐÚNG MỘT hàm hoặc lớp cần sửa.\n"
              "Chỉ trả về TÊN, không giải thích, không viết mã.\n\n"
              f"=== CÁC HÀM/LỚP CÓ TRONG {d['nguon']} ===\n" + ", ".join(ten_all) + "\n\n"
              f"=== TỆP TEST ===\n{test}\n\n=== PYTEST BÁO LỖI ===\n{loi}\n\n"
              "=== TÊN HÀM CẦN SỬA ===\n")
        g1 = 0.0
        chon = None
        phai_nhac = 0
        tra_dau = ""
        for lan in range(2):
            giay, ra1 = _hoi_cuc_bo(p1)
            g1 += giay
            if lan == 0:
                tra_dau = ra1[:60]
            tu = _re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ra1)
            chon = next((x for x in tu if x in ten_all), None)
            if chon is not None:
                break
            phai_nhac += 1
            # Nhắc bằng SỰ THẬT kiểm được: tên vừa nêu không có trong tệp nguồn.
            p1 = (f"Tên bạn vừa trả lời — {ra1[:40]!r} — KHÔNG CÓ trong tệp mã "
                  f"nguồn {d['nguon']}. Nhiều khả năng đó là tên hàm trong tệp "
                  "TEST; bạn đang được hỏi về tệp NGUỒN.\n\n"
                  "Chọn lại, và CHỈ được chọn một tên trong danh sách sau:\n"
                  + ", ".join(ten_all) + "\n\n"
                  f"=== TỆP TEST ===\n{test}\n\n=== PYTEST BÁO LỖI ===\n{loi}\n\n"
                  "=== TÊN HÀM CẦN SỬA (chép đúng một tên từ danh sách trên) ===\n")

        if chon is None:
            return {"trang_thai": "chan1_hut", "giay": round(g1, 1),
                    "cuc_bo_tra": tra_dau, "chan1_phai_nhac": phai_nhac,
                    "vi_sao": "vẫn nêu tên ngoài tệp nguồn sau khi đã nhắc"}

        than = _than_ham(ma, chon)
        if not than:
            return {"trang_thai": "chan1_hut", "giay": round(g1, 1),
                    "cuc_bo_tra": chon, "chan1_phai_nhac": phai_nhac,
                    "vi_sao": "không trích được thân hàm"}
        # ---- CHẶNG 2: cloud chỉ nhận ĐÚNG hàm đó ------------------------
        p2 = ("Hàm dưới đây có lỗi làm test ĐỎ. Viết lại TOÀN VĂN hàm đã sửa.\n"
              "Chỉ mã Python, không giải thích, không khối markdown.\n\n"
              f"=== HÀM CẦN SỬA ({chon} trong {d['nguon']}) ===\n{than}\n\n"
              f"=== TỆP TEST ===\n{test}\n\n=== PYTEST BÁO LỖI ===\n{loi}\n\n"
              "=== HÀM ĐÃ SỬA ===\n")
        g2, ra2 = hoi_cloud(p2)

        sua, hong = D.ap_ham(ma, ra2)
        if hong:
            return {"trang_thai": "sai_dinh_dang", "vi_sao": hong,
                    "giay": round(g1 + g2, 1), "ham_chon": chon,
                    "chan1_phai_nhac": phai_nhac,
                    "giay_cuc_bo": round(g1, 1), "giay_cloud": round(g2, 1)}

        # ---- CHẶNG 3: máy chấm, ba cửa cũ -------------------------------
        f_nguon.write_text(sua, encoding="utf-8")
        nen = set(d.get("do_nen") or ())
        try:
            m2, _, _ = D.pytest_(py, tam, d["test"], 300)
            them = (D.pytest_(py, tam, ["tests"], 200)[2] - nen) if m2 == 0 else set()
        except subprocess.TimeoutExpired:
            return {"trang_thai": "khong_do_duoc", "vi_sao": "test treo"}

        # Đáp án thật: CHỈ để chấm sau, cho biết chặng 1 có đúng không.
        dap, _, _ = M.dap_an_dinh_vi(d)
        return {"trang_thai": "dat" if (m2 == 0 and not them) else "truot",
                "ham_chon": chon, "chan1_phai_nhac": phai_nhac, "dinh_vi_dung": chon in dap,
                "dap_an": sorted(dap),
                "giay": round(g1 + g2, 1),
                "giay_cuc_bo": round(g1, 1), "giay_cloud": round(g2, 1)}
    except Exception as e:                                       # noqa: BLE001
        return {"trang_thai": "khong_do_duoc",
                "vi_sao": f"{type(e).__name__}: {str(e)[:80]}"}
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    de = json.loads(DE.read_text(encoding="utf-8"))
    so = json.loads(RA.read_text(encoding="utf-8")) if RA.exists() else {}
    print(f"  {len(de)} đề · chặng 1 {CUC_BO} (cục bộ) · chặng 2 {CLOUD} (cloud)\n")
    dat = truot = hut = sai = bo = 0
    dv_dung = 0
    gcb = gcl = 0.0
    for i, d in enumerate(de, start=1):
        khoa = f"{d['sha'][:8]}:{d['nguon']}"
        r = so.get(khoa)
        if r and r.get("trang_thai") == "khong_do_duoc":
            r = None
        r = r or mot_de(d)
        so[khoa] = r
        RA.write_text(json.dumps(so, ensure_ascii=False, indent=2), encoding="utf-8")
        t = r["trang_thai"]
        dat += t == "dat"; truot += t == "truot"; hut += t == "chan1_hut"
        sai += t == "sai_dinh_dang"; bo += t == "khong_do_duoc"
        dv_dung += bool(r.get("dinh_vi_dung"))
        gcb += r.get("giay_cuc_bo", 0.0); gcl += r.get("giay_cloud", 0.0)
        dau = {"dat": "✓", "truot": "✗", "chan1_hut": "①", "sai_dinh_dang": "≠",
               "khong_do_duoc": "·"}[t]
        print(f"  {dau} [{i:>2}/{len(de)}] {d['nguon'][:26]:<28}"
              f"{r.get('ham_chon', r.get('cuc_bo_tra', ''))[:22]:<24}"
              f"{r.get('giay', 0):>6.1f}s  {r.get('vi_sao', '')}")
    do = dat + truot
    print(f"\n  ĐẠT {dat}/{do} đo được"
          f"  ·  {hut} chặng 1 hụt  ·  {sai} sai định dạng  ·  {bo} không đo được")
    print(f"  định vị ĐÚNG hàm: {dv_dung}/{do}" if do else "")
    print(f"  giờ máy cục bộ {gcb:.0f}s  ·  giờ cloud {gcl:.0f}s"
          f"  ·  cloud chỉ nhận 1 hàm thay vì cả vùng")
    print(f"  -> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
