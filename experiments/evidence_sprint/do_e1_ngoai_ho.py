# -*- coding: utf-8 -*-
r"""Do E1 tren bo de NGOAI HO. 22/08/2026.

Cau hoi: E1 lam gi khi gap loi no KHONG duoc thiet ke de lat?

Bo de: `de_ngoai_ho.json`, 64 de tren 4 tep loi, moi de da qua hai khau:
    1. khong phep lat DON nao cua `_Lat` khoi phuc duoc ban goc
    2. test DO ON DINH (chay hai lan)

NGUONG DAT TRUOC:

    = 0/N   DUNG NHU THIET KE. In con so ay len giao dien:
            "Chi do duoc 5 ho. Da thu N loi ngoai ho, khong do ra ca nao."

    > 0/N   PHAI MO RA XEM TUNG CA.
            E1 lam test xanh tren mot loi no khong hieu = va de len trieu chung.
            Voi moi ca, doi chieu AST ban va voi ban goc:
               KHOP  -> may man, ghi lai
               LECH  -> LOI NANG: app se de nghi nguoi dung mot ban va SAI
                        ma test xanh. Bao ngay.

    Nhanh `> 0` moi nguy hiem, khong phai nhanh `= 0`.

CHAM BANG AST, KHONG BANG "test co xanh khong". Ca tuan nay do duoc: nen
`2/9 xanh` nhung `0/9 dung nghia`. Xanh la dieu kien can, khong phai du.

    venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\do_e1_ngoai_ho.py [so_de]
"""
from __future__ import annotations

import ast
import collections
import io
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(NHA))
sys.path.insert(0, str(GOC))

from core.lat_nguoc import _ma_sau_lat, chay_e1_dinh_vi     # noqa: E402

DE = NHA / "de_ngoai_ho.json"
RA = GOC / "data" / "evidence_sprint" / "e1_ngoai_ho.json"


def _ban_va(kq: dict, ma_dot_bien: str) -> list[str]:
    """Dung lai MA DA VA tu chi so ung vien.

    22/08: `chay_e1_dinh_vi` KHONG tra ve ma da va. `candidates` chi co
    `index · line · operation · unified_diff · trang_thai`. Nen khong the so
    AST tu dau ra cua no - phai lat lai bang chinh `_ma_sau_lat` voi chi so ay.

    Ban dau toi do ten truong bang cach doan (`ma_da_va`, `ma_moi`, ...) va
    tra ve chuoi rong. Hau qua: moi ca `tim_thay` se ghi `dung_nghia = None`,
    tuc la ca nhanh NGUY HIEM cua phep do bi cam. Doan ten truong la mot dang
    do chuoi - dung cai ma CLAUDE.md §4 cam.
    """
    ra = []
    for c in (kq.get("candidates") or []):
        if c.get("full_suite_status") != "XANH":
            continue
        try:
            moi, _ = _ma_sau_lat(ma_dot_bien, int(c["index"]))
        except Exception:                                    # noqa: BLE001
            continue
        ra.append(moi)
    return ra


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if not DE.is_file():
        print("  KHONG DO DUOC - chua co %s" % DE.name)
        return 2
    de = json.loads(DE.read_text(encoding="utf-8"))["de"]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(de)
    de = de[:n]

    so = []
    if RA.is_file():
        so = json.loads(RA.read_text(encoding="utf-8")).get("ket_qua", [])
        xong = {(x["tep"], x["muc"]) for x in so}
        de = [d for d in de if (d["tep"], d["muc"]) not in xong]

    RA.parent.mkdir(parents=True, exist_ok=True)
    print("  %d de ngoai ho - chay E1 tren tung de\n" % len(de))
    t0 = time.monotonic()
    try:
        for i, d in enumerate(de, 1):
            tam_goc = Path(tempfile.mkdtemp())
            tam = tam_goc / "kho"
            shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
                "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))
            f = tam / d["tep"]
            goc = f.read_text(encoding="utf-8")
            chuan = ast.unparse(ast.parse(goc))
            f.write_text(d["ma"], encoding="utf-8")
            t1 = time.monotonic()
            try:
                kq = chay_e1_dinh_vi(tam, d["tep"], d["tep_test"],
                                     timeout_s=150.0)
            except Exception as e:                           # noqa: BLE001
                kq = {"trang_thai": "khong_do_duoc", "vi_sao": str(e)[:80]}
            giay = time.monotonic() - t1
            shutil.rmtree(tam_goc, ignore_errors=True)

            ts = str(kq.get("trang_thai", "?"))
            tim_thay = ts in ("tim_thay", "dat", "xanh")
            dung = None
            if tim_thay:
                bv = _ban_va(kq, d["ma"])
                if bv:
                    # Co nhieu ban va xanh thi DUNG chi khi it nhat mot ban
                    # khoi phuc dung ban goc. Con lai deu la "xanh ma sai".
                    dung = False
                    for m in bv:
                        try:
                            if ast.dump(ast.parse(m)) == ast.dump(ast.parse(chuan)):
                                dung = True
                                break
                        except SyntaxError:
                            continue
            so.append({"tep": d["tep"], "muc": d["muc"], "ho": d["ho"],
                       "mo_ta": d["mo_ta"], "dong": d["dong"],
                       "co_ve_sap": d["co_ve_sap"], "trang_thai": ts,
                       "tim_thay": tim_thay, "dung_nghia": dung,
                       "giay": round(giay, 1)})
            RA.write_text(json.dumps(
                {"_vi_sao": "E1 tren loi NGOAI ho cua _Lat", "ket_qua": so},
                ensure_ascii=False, indent=1), encoding="utf-8")
            canh = ""
            if tim_thay and dung is False:
                canh = "   <<< XANH MA SAI - MO RA XEM"
            print("  %3d/%-3d [%-11s] %-20s %-14s dung: %-5s %4.0fs%s"
                  % (i, len(de), d["ho"], d["tep"].split("/")[-1][:20],
                     ts[:14], dung, giay, canh))
    finally:
        pass

    print()
    tim = [x for x in so if x["tim_thay"]]
    sai = [x for x in tim if x["dung_nghia"] is False]
    print("  E1 TIM RA BAN VA : %d/%d" % (len(tim), len(so)))
    print("     trong do KHOP ban goc : %d" % sum(1 for x in tim if x["dung_nghia"]))
    print("     trong do XANH MA SAI  : %d   <- nhanh nguy hiem" % len(sai))
    print()
    c = collections.Counter(x["ho"] for x in so)
    ct = collections.Counter(x["ho"] for x in tim)
    print("  %-14s %6s %8s" % ("ho", "so de", "tim ra"))
    for h in sorted(c):
        print("  %-14s %6d %8d" % (h, c[h], ct.get(h, 0)))
    print()
    print("  %.0f phut" % ((time.monotonic() - t0) / 60))
    for x in sai:
        print("  XANH MA SAI: %s dong %d  [%s] %s"
              % (x["tep"], x["dong"], x["ho"], x["mo_ta"]))
    return 1 if sai else 0


if __name__ == "__main__":
    raise SystemExit(main())
