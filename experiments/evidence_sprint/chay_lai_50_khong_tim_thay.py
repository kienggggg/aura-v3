# -*- coding: utf-8 -*-
r"""Chay lai 50 ca `khong_tim_thay` cua bo de NGOAI HO, voi ba so dem moi.

CAU HOI. Ban ghi 22/08 (`data/evidence_sprint/e1_ngoai_ho.json`) ket luan
`0/64 tim ra`, trong do 50 ca mang trang_thai `khong_tim_thay`. Nhung ma luc ay
GOP hai chuyen vao mot nhan:

    "da thu N phep lat, khong phep nao xanh"      <- da do, ket luan dung
    "co phep chua tung duoc thu"                  <- CHUA do het

Vi vong lat co hai cho `except Exception: continue` bo qua ung vien ma khong ai
dem (sua 30/08/2026). Bao cao chi ghi `candidate_count_after` = so ung vien DINH
thu, nen "sau loc 4, tim ra 0" doc thanh "da thu 4". Nay co them
`candidate_tried_count` va `candidate_skipped_count` de tach ra.

NGUONG DAT TRUOC, viet TRUOC khi chay:

    bo_qua == 0 o ca 50 ca
        Ket luan "0/64 tim ra" ĐUNG NGUYEN VEN. Ghi lai va di tiep.

    bo_qua > 0 o mot so ca
        Ket luan cu YEU HON no tuong. Voi nhung ca do, cau dung phai la
        "da thu <tried>, con <skipped> phep chua thu duoc vi <ly do>".
        PHAI mo ra xem ly do, va phai sua lai cau ket luan tren giao dien.

    Khong nhanh nao lam "0/64" thanh sai. Nhanh thu hai chi lam no HEP hon.

KHONG chay lai 14 ca con lai (10 `ung_vien_khong_qua_suite`, 4 `khong_do_duoc`):
chung da mang nhan rieng, khong bi gop.

    venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\chay_lai_50_khong_tim_thay.py [so_de]
"""
from __future__ import annotations

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
sys.path.insert(0, str(GOC))

from core.lat_nguoc import chay_e1_dinh_vi                    # noqa: E402

DE = NHA / "de_ngoai_ho.json"
CU = GOC / "data/evidence_sprint/e1_ngoai_ho.json"
RA = GOC / "data/evidence_sprint/e1_ngoai_ho_chay_lai_50.json"


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not DE.is_file() or not CU.is_file():
        print("  KHONG DO DUOC — thieu %s hoac %s" % (DE.name, CU.name))
        return 2

    de_theo_khoa = {(d["tep"], d["muc"]): d
                    for d in json.loads(DE.read_text(encoding="utf-8"))["de"]}
    cu = json.loads(CU.read_text(encoding="utf-8"))["ket_qua"]
    can_chay = [x for x in cu if x["trang_thai"] == "khong_tim_thay"]
    print("  %d ca `khong_tim_thay` trong ban ghi 22/08" % len(can_chay))

    thieu = [x for x in can_chay if (x["tep"], x["muc"]) not in de_theo_khoa]
    if thieu:
        print("  *** KHONG DO DUOC: %d ca khong tim thay de goc ***" % len(thieu))
        return 2

    so = []
    if RA.is_file():
        so = json.loads(RA.read_text(encoding="utf-8")).get("ket_qua", [])
        xong = {(x["tep"], x["muc"]) for x in so}
        can_chay = [x for x in can_chay if (x["tep"], x["muc"]) not in xong]
        print("  da chay truoc do: %d ca, con %d" % (len(so), len(can_chay)))

    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(can_chay)
    can_chay = can_chay[:n]
    RA.parent.mkdir(parents=True, exist_ok=True)
    print("  chay %d ca\n" % len(can_chay))

    t0 = time.monotonic()
    for i, x in enumerate(can_chay, 1):
        d = de_theo_khoa[(x["tep"], x["muc"])]
        tam_goc = Path(tempfile.mkdtemp())
        tam = tam_goc / "kho"
        shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
            "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))
        (tam / d["tep"]).write_text(d["ma"], encoding="utf-8")
        t1 = time.monotonic()
        try:
            kq = chay_e1_dinh_vi(tam, d["tep"], d["tep_test"], timeout_s=150.0)
        except Exception as e:                                # noqa: BLE001
            kq = {"trang_thai": "khong_do_duoc", "vi_sao": str(e)[:120]}
        giay = time.monotonic() - t1
        shutil.rmtree(tam_goc, ignore_errors=True)

        ban = {
            "tep": d["tep"], "muc": d["muc"], "ho": d["ho"], "dong": d["dong"],
            "trang_thai_cu": x["trang_thai"],
            "trang_thai_moi": str(kq.get("trang_thai", "?")),
            "sau_loc": kq.get("candidate_count_after"),
            "da_thu": kq.get("candidate_tried_count"),
            "bo_qua": kq.get("candidate_skipped_count"),
            "ly_do_bo_qua": [y.get("reason") for y in (kq.get("candidate_skipped") or [])],
            "giay": round(giay, 1),
        }
        so.append(ban)
        RA.write_text(json.dumps(
            {"_vi_sao": "Chay lai 50 ca khong_tim_thay voi ba so dem moi (30/08/2026)",
             "ket_qua": so}, ensure_ascii=False, indent=1), encoding="utf-8")
        canh = "   <<< CO PHEP CHUA TUNG THU" if (ban["bo_qua"] or 0) > 0 else ""
        print("  %3d/%-3d %-22s muc %-3d %-11s sau_loc %-4s da_thu %-4s bo_qua %-4s %4.0fs%s"
              % (i, len(can_chay), d["tep"], d["muc"], d["ho"],
                 ban["sau_loc"], ban["da_thu"], ban["bo_qua"], giay, canh))

    # ---------------- tong ket ----------------
    print("\n  === TONG KET (%d ca, %.0f phut) ===" % (len(so), (time.monotonic() - t0) / 60))
    doi_nhan = [x for x in so if x["trang_thai_moi"] != x["trang_thai_cu"]]
    co_bo_qua = [x for x in so if (x["bo_qua"] or 0) > 0]
    print("  trang_thai moi: %s" % dict(collections.Counter(x["trang_thai_moi"] for x in so)))
    print("  doi nhan so voi 22/08 : %d ca" % len(doi_nhan))
    print("  CO phep chua tung thu : %d/%d ca" % (len(co_bo_qua), len(so)))
    if co_bo_qua:
        ly_do = collections.Counter(r for x in co_bo_qua for r in x["ly_do_bo_qua"])
        print("  ly do bo qua: %s" % dict(ly_do))
        print("\n  => Ket luan cu '0/64 tim ra' HEP HON no tuong: voi %d ca," % len(co_bo_qua))
        print("     cau dung la 'da thu <it hon>, con lai chua thu duoc'.")
    else:
        print("\n  => bo_qua = 0 o ca %d ca. Ket luan '0/64 tim ra' DUNG NGUYEN VEN." % len(so))
    print("\n  ban ghi: %s" % RA.relative_to(GOC).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
