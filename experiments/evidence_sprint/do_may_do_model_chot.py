# -*- coding: utf-8 -*-
r"""E5 - MAY DO TRUOC, MODEL CHOT SAU. Do 22/08/2026.

VI SAO. Bay huong da do deu la MODEL LAM MOT MINH:

    nen  va tung cho          2/9 xanh, 0/9 dung nghia
    C    doi mot o the        1/9, 1/9
    C2   ep khuon JSON        0/9
    C3   ep enum              0/9
    E3   viet lai ca ham      0/9, 0/9
    E2   khoet dung cho       1/9, 0/9
    E4   E2 + chan cau truc   1/9, 0/9

E1 la MAY LAM MOT MINH: 3/9 (3 de loi don), khong goi model.

CHUA AI DO: may do truoc, model chot sau. Ma do chinh la cau ket luan ca tuan:
"may lam tham tu, model lam nguoi ke lai".

CACH DO. Moi luot, may lam het phan tim:
    1. tim test do, chon test tat dinh
    2. truy vet -> tap dong DA CHAY
    3. sinh ung vien lat nguoc, LOC theo dong da chay (65 -> 15 tren may_tinh)
Roi dua danh sach da loc cho model, hoi DUY NHAT mot cau: chon so may.

Model khong phai tim, khong phai viet, khong phai nho cu phap. No chi CHON.

NGUONG DAT TRUOC - viet 22/08 truoc khi chay:
    >= 5/9 dung nghia  -> phoi hop thang ca hai, dung vao app
    3-4/9              -> ngang E1 mot minh; model thua, dung E1 thoi
    <= 2/9             -> model lam HONG ca thong tin may dua cho

Nhanh cuoi nghe kho tin nhung rat co the: E4 cho thay model DUNG YEN khi bi
chan, E2 cho thay 60% nuoc di cua no la CHEP DONG BEN CANH.
"""
from __future__ import annotations

import ast
import io
import json
import random
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(NHA))
sys.path.insert(0, str(GOC))

from dung_de_loi import chay_test, dot_bien                        # noqa: E402
from core.lat_nguoc import _chon_test_va_dong, tao_cac_ung_vien    # noqa: E402

MODEL = "qwen2.5-coder:7b"     # DUNG model cua nen 2/9
TRAN_LUOT = 4                  # DUNG tran cua nen
SO = NHA / "so_may_do_model_chot.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"


def hoi(p):
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 200,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(),
                               method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=600) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _so_dau(s):
    """Model tra ve mot so. Lay so nguyen dau tien, khong doan gi them."""
    cur = ""
    for ch in s:
        if ch.isdigit():
            cur += ch
        elif cur:
            break
    return int(cur) if cur else None


def mot_de(tam, d):
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")
    chuan = ast.unparse(ast.parse(goc))
    ma, mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "khong gieo duoc"}
    f.write_text(ma, encoding="utf-8")

    ghi = []
    hien = ma
    da_thu = []          # so da chon va TRUOT, de khong hoi lai y het
    try:
        for luot in range(1, TRAN_LUOT + 1):
            # ---- MAY LAM PHAN TIM ----
            r_chon = _chon_test_va_dong(tam, tep, tep_test,
                                        deadline=time.monotonic() + 90)
            if r_chon.get("trang_thai") == "khong_chay":
                return {"trang_thai": "khong_do_duoc",
                        "vi_sao": r_chon.get("vi_sao", "?"), "ghi": ghi}
            dong_chay = set()
            for x in (r_chon.get("dong_da_chay") or []):
                if int(x) > 0:
                    dong_chay.add(int(x))
            truoc = len(tao_cac_ung_vien(hien))
            uv = tao_cac_ung_vien(hien, dong_chay or None)
            if not uv:
                return {"trang_thai": "khong_do_duoc",
                        "vi_sao": "loc con 0 ung vien", "ghi": ghi}

            bang = "\n".join(
                "%2d. dong %-4d %s" % (i, dg, mt)
                for i, (dg, mt, _) in enumerate(uv[:40], 1))
            # 22/08: luot dau ban nay KHONG co dong nay, nen loi nhac luot 2
            # y het luot 1 -> model tra loi y het (chon "1" bon lan). Do la do
            # tinh tat dinh cua giai ma, khong phai do model bat luc.
            cam = ""
            if da_thu:
                cam = ("\nDA THU VA TRUOT: %s. DUNG chon lai nhung so nay.\n"
                       % ", ".join(str(x) for x in da_thu))
            p = ("May da dinh vi xong. Duoi day la %d cho CO THE dang sai, may "
                 "da loc bo nhung cho test khong chay qua.\n\n"
                 "=== TEST DANG DO ===\n%s\n\n"
                 "=== DANH SACH UNG VIEN ===\n%s\n%s\n"
                 "Chon DUNG MOT so trong danh sach tren. Chi tra ve CON SO, "
                 "khong giai thich, khong viet gi them.\n=== TRA LOI ===\n"
                 % (len(uv), (r_chon.get("loi") or "")[-700:], bang, cam))
            ra, giay = hoi(p)
            chon = _so_dau(ra)
            ghi.append({"luot": luot, "giay": round(giay, 1),
                        "truoc_loc": truoc, "sau_loc": len(uv),
                        "model_tra": ra[:40], "chon": chon})
            if not chon or not (1 <= chon <= len(uv)):
                continue

            thu = uv[chon - 1][2]
            f.write_text(thu, encoding="utf-8")
            # 22/08: mot phep lat co the lam test TREO (vi du lat hang so trong
            # dieu kien vong lap). `chay_test` nem TimeoutExpired chu khong tra
            # ma loi, nen ca phep do chet giua chung o de thu 4. Treo = TRUOT,
            # khong phai su co.
            try:
                m2, bao = chay_test(tam, tep_test)
            except Exception as e:                               # noqa: BLE001
                ghi[-1]["treo"] = str(e)[:60]
                m2, bao = 1, "treo"
            if m2 == 0:
                try:
                    dung = ast.dump(ast.parse(thu)) == ast.dump(ast.parse(chuan))
                except SyntaxError:
                    dung = False
                return {"trang_thai": "dat", "luot": luot, "ghi": ghi,
                        "dung_nghia": dung, "mo_ta_gieo": mo}
            # 22/08: ban dau chon sai van GIU nguyen phep lat sai -> trang thai
            # troi (15 ung vien thanh 4 o luot sau) va de thanh khong giai duoc.
            # E1 chi giu phep lat NAO DOI CHU KY loi; o day model chua co co
            # che ay, nen tra ve nguyen trang.
            da_thu.append(chon)
            f.write_text(hien, encoding="utf-8")
        return {"trang_thai": "het_luot", "luot": TRAN_LUOT, "ghi": ghi,
                "dung_nghia": False, "mo_ta_gieo": mo}
    finally:
        f.write_text(goc, encoding="utf-8")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chua chay - KHONG DO DUOC")
        return 2
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo = {}
    for x in loi:
        theo.setdefault(x["tep"], []).append(x)
    rng = random.Random(19082026)      # Y HET cac phep do truoc - cung 9 de
    de = []
    for tep, ds in theo.items():
        for so_loi in (1, 2, 3):
            if len(ds) >= so_loi:
                de.append({"tep": tep, "tep_test": ds[0]["tep_test"],
                           "cho": [x["cho"] for x in rng.sample(ds, so_loi)],
                           "so_loi": so_loi})
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    de = de[:n]

    so = []
    if SO.is_file():
        so = json.loads(SO.read_text(encoding="utf-8"))
        xong = set()
        for x in so:
            xong.add((x["tep"], x["so_loi"]))
        de = [d for d in de if (d["tep"], d["so_loi"]) not in xong]

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    print("  %d de - %s - MAY do truoc, MODEL chi CHON SO\n" % (len(de), MODEL))
    try:
        for d in de:
            t0 = time.monotonic()
            r = mot_de(tam, d)
            r.update({"tep": d["tep"], "so_loi": d["so_loi"],
                      "giay": round(time.monotonic() - t0, 1)})
            so.append(r)
            SO.write_text(json.dumps(so, ensure_ascii=False, indent=1),
                          encoding="utf-8")
            g = r.get("ghi") or [{}]
            print("  %-22s %d loi  %-14s dung nghia: %-5s  %s->%s  %4.0fs"
                  % (d["tep"].split("/")[-1][:22], d["so_loi"],
                     r["trang_thai"], r.get("dung_nghia"),
                     g[0].get("truoc_loc", "?"), g[0].get("sau_loc", "?"),
                     r["giay"]))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)
    xanh = 0
    dung = 0
    for x in so:
        if x.get("trang_thai") == "dat":
            xanh += 1
        if x.get("dung_nghia"):
            dung += 1
    print("\n  xanh %d/%d   DUNG NGHIA %d/%d" % (xanh, len(so), dung, len(so)))
    return 0 if dung >= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
