# -*- coding: utf-8 -*-
r"""E4 - CHO SAN CHO va CHAN BA NUOC DI SAI. Do 21/08/2026.

E2 ra 1/9 xanh, 0/9 dung nghia. Soi 57 lan dien (`soi_nuoc_di.py`):

    chep dong co san        34  60%   (trung vi cach o trong 3 dong,
                                       12 lan chep dung dong NGAY CANH)
    sai kieu cau lenh       16  28%
    dung kieu sai noi dung   6  11%
    giu nguyen dot bien      1   2%

Ba loai dau la loi CAU TRUC. May tu kiem duoc ca ba, khong can model hop tac.
Phep do nay chan chung roi bat lam lai, xem con so co nhuc nhich.

VI SAO chan kieu cau lenh la CONG BANG: trong app, o trong nam TRONG mot the
con nguyen - the `neu` van la the `neu`, chi co o dieu kien trong. E2 khoet ca
DONG nen xoa mat thong tin ay. Chan nay tra lai dung thu app co.

NGUONG DAT TRUOC - viet 21/08 truoc khi chay:
    >=4/9 dung nghia  -> chan cau truc la don bay that, dung vao app
    2-3/9             -> co tac dung, chua du de doi thiet ke
    <=1/9             -> ba loai kia chi la VO. Model chep dong ben canh vi BI,
                         khong phai vi tuong phai chep; chan duong chep thi no
                         doi sang bia. Buc tuong van nguyen.

C2 (ep JSON Schema) va C3 (ep enum) da mot lan hua hen kieu nay roi ra 0/9.
Khac biet: C2/C3 ep GIA TRI cua toan tu; o day chan THU GI duoc nam trong o.
Khong cung mot chuyen, nen C2/C3 khong bac truoc duoc - cung khong hua ho duoc.
"""

from __future__ import annotations

import ast
import io
import json
import random
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(NHA))

from dung_de_loi import chay_test, dot_bien            # noqa: E402

MODEL = "qwen2.5-coder:7b"     # ĐÚNG model của nền 2/9
TRAN_LUOT = 4      # so lan CHAM TOI TEST — y het E2
TRAN_GOI  = 10     # so lan goi model; luot bi CHAN khong tinh vao TRAN_LUOT                  # ĐÚNG trần của nền 2/9
SO = NHA / "so_chan_cau_truc.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
CHO_TRONG = "____"


def hoi(p: str) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 120,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(),
                               method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=900) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def khoet(chuan: str, ma: str) -> tuple[str, list[tuple[int, str]]]:
    """Khoét những dòng KHÁC bản gốc thành `____`. Máy làm, model không thấy.

    Trả (mã đã khoét, [(số dòng, nguyên văn dòng đúng)]). Dòng đúng chỉ dùng để
    CHẤM, không bao giờ đưa cho model.
    """
    a, b = chuan.splitlines(), ma.splitlines()
    ra, dap = [], []
    for i in range(len(b)):
        if i < len(a) and a[i] != b[i]:
            thut = len(b[i]) - len(b[i].lstrip())
            ra.append(b[i][:thut] + CHO_TRONG)
            dap.append((i + 1, a[i]))
        else:
            ra.append(b[i])
    return "\n".join(ra), dap


def _boc_rao(s: str) -> str:
    t = s.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()



def _kieu(s: str) -> str:
    """Kieu cau lenh theo AST. Dong mo khoi dung mot minh phai va than gia."""
    try:
        cay = ast.parse(s.strip())
    except SyntaxError:
        try:
            cay = ast.parse(s.strip() + chr(10) + "    pass")
        except SyntaxError:
            return "?"
    return type(cay.body[0]).__name__ if cay.body else "?"


def chan(tra, dap, ma_khoet, dot_dong):
    """Ba cua may tu gac. Tra ly do chan, hoac chuoi rong neu lot."""
    co_san = {l.strip() for l in ma_khoet.splitlines()
              if l.strip() and l.strip() != CHO_TRONG}
    for i, t in enumerate(tra):
        t2 = t.strip()
        if t2 in dot_dong:
            return "dong %d: do CHINH LA dong dang do. Khong duoc dien lai no." % (i + 1)
        if t2 in co_san:
            return ("dong %d: `%s` da co nguyen van o cho khac trong ma. O trong "
                    "phai la mot dong KHAC, khong phai ban sao." % (i + 1, t2[:60]))
        kd, kt = _kieu(dap[i]), _kieu(t)
        if kd != kt:
            return ("dong %d: o nay phai la cau lenh loai %s, ban viet loai %s."
                    % (i + 1, kd, kt))
    return ""


def mot_de(tam: Path, d: dict) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")
    ma, mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc"}
    chuan = ast.unparse(ast.parse(goc))
    da_khoet, dap = khoet(chuan, ma)
    _dm = ma.splitlines()
    dot_dong = {_dm[n - 1].strip() for n, _ in dap if n - 1 < len(_dm)}
    if not dap:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "không khoét được chỗ nào"}

    f.write_text(ma, encoding="utf-8")
    _, loi = chay_test(tam, tep_test)

    lich_su = ""
    ghi = []
    try:
        da_thu = 0
        for luot in range(1, TRAN_GOI + 1):
            if da_thu >= TRAN_LUOT:
                break
            p = ("Dưới đây là mã Python có %d chỗ bị xoá, đánh dấu `%s`.\n"
                 "Test đang ĐỎ vì những chỗ ấy còn trống.\n"
                 "Bạn KHÔNG phải tìm lỗi — chỗ cần điền đã được chỉ sẵn.\n"
                 "Chỉ viết lại ĐÚNG %d dòng đó, mỗi dòng một dòng, theo thứ tự "
                 "xuất hiện, giữ nguyên thụt đầu dòng. Không giải thích, không "
                 "khối markdown.\n\n"
                 "=== MÃ (%s) ===\n%s\n"
                 "=== PYTEST BÁO ===\n%s\n%s\n=== %d DÒNG CẦN ĐIỀN ===\n"
                 % (len(dap), CHO_TRONG, len(dap), tep, da_khoet[:9000],
                    loi[-900:], lich_su, len(dap)))
            ra, giay = hoi(p)
            dong_moi = [l for l in _boc_rao(ra).splitlines() if l.strip()]
            ghi.append({"luot": luot, "giay": round(giay, 1),
                        "tra_ve": dong_moi[:6]})
            if len(dong_moi) < len(dap):
                lich_su = ("\n=== LƯỢT %d BẠN TRẢ %d DÒNG, CẦN %d ===\n"
                           % (luot, len(dong_moi), len(dap)))
                continue
            # CHAN CAU TRUC - may gac, model khong phai hop tac
            vi_sao = chan(dong_moi[:len(dap)], [x[1] for x in dap],
                          da_khoet, dot_dong)
            if vi_sao:
                ghi[-1]["chan"] = vi_sao
                lich_su = (chr(10) + "=== LUOT %d BI CHAN ===" + chr(10)
                           + "%s" + chr(10)) % (luot, vi_sao)
                continue
            # ghép lại: thay đúng những dòng đã khoét
            d_ra = da_khoet.splitlines()
            k = 0
            for i, l in enumerate(d_ra):
                if l.strip() == CHO_TRONG:
                    # 21/08: chỗ này TỪNG vứt thụt đầu dòng đi. `khoet()` viết ra
                    # `"    ____"` — MÁY biết dòng ấy thụt bao nhiêu — rồi lúc ghép
                    # lại thay cả dòng bằng lời model, nên model phải tự đoán thụt.
                    # 28/32 lượt chết ở đó, và sổ ghi "0/9" cho một phép đo chưa
                    # hề chạm tới câu hỏi. Máy biết cái gì thì máy giữ cái đó.
                    thut = l[:len(l) - len(l.lstrip())]
                    d_ra[i] = thut + dong_moi[k].lstrip()
                    k += 1
            da_thu += 1     # chi dem khi THAT SU sap chay test
            sua = "\n".join(d_ra) + "\n"
            try:
                ast.parse(sua)
            except SyntaxError as e:
                ghi[-1]["hong"] = "vỡ cú pháp: %s" % str(e)[:60]
                lich_su = "\n=== LƯỢT %d VỠ CÚ PHÁP ===\n%s\n" % (luot, str(e)[:120])
                continue
            f.write_text(sua, encoding="utf-8")
            m2, bao = chay_test(tam, tep_test)
            if m2 == 0:
                try:
                    dung = ast.dump(ast.parse(sua)) == ast.dump(ast.parse(chuan))
                except SyntaxError:
                    dung = False
                return {"trang_thai": "dat", "luot": luot, "ghi": ghi,
                        "dung_nghia": dung, "so_cho_khoet": len(dap),
                        "dap_an": [x[1].strip()[:70] for x in dap]}
            lich_su = ("\n=== LƯỢT %d VẪN ĐỎ ===\n%s\nĐừng lặp lại cách đó.\n"
                       % (luot, bao[-400:]))
        return {"trang_thai": "het_luot", "luot": TRAN_LUOT, "ghi": ghi,
                "dung_nghia": False, "so_cho_khoet": len(dap),
                "dap_an": [x[1].strip()[:70] for x in dap]}
    finally:
        f.write_text(goc, encoding="utf-8")


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo: dict[str, list] = {}
    for x in loi:
        theo.setdefault(x["tep"], []).append(x)
    rng = random.Random(19082026)      # Y HỆT do_sua_loi.py — cùng 9 đề
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
        xong = {(x["tep"], x["so_loi"]) for x in so}
        de = [d for d in de if (d["tep"], d["so_loi"]) not in xong]

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    print("  %d đề · %s · trần %d lượt · CHO SẴN CHỖ + CHẶN CẤU TRÚC\n"
          % (len(de), MODEL, TRAN_LUOT))
    try:
        for d in de:
            t0 = time.monotonic()
            r = mot_de(tam, d)
            r.update({"tep": d["tep"], "so_loi": d["so_loi"],
                      "giay": round(time.monotonic() - t0, 1)})
            so.append(r)
            SO.write_text(json.dumps(so, ensure_ascii=False, indent=1),
                          encoding="utf-8")
            print("  %-22s %d lỗi  %-10s đúng nghĩa: %-5s %4.0fs"
                  % (d["tep"].split("/")[-1][:22], d["so_loi"],
                     r["trang_thai"], r.get("dung_nghia"), r["giay"]))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    dat = sum(1 for x in so if x["trang_thai"] == "dat")
    dung = sum(1 for x in so if x.get("dung_nghia"))
    print("\n" + "=" * 62)
    print("  E2 — CHO SẴN CHỖ, chỉ hỏi ĐIỀN GÌ")
    print("=" * 62)
    print("  nền viết lại cả hàm      : 2/9 xanh (đúng nghĩa chưa đo)")
    print("  xanh                     : %d/%d" % (dat, len(so)))
    print("  ĐÚNG NGHĨA               : %d/%d   <- cột quyết định" % (dung, len(so)))
    print()
    if dung >= 6:
        print("  ĐẠT — giả thuyết ĐỨNG: model sinh được, không sửa được.")
        print("  App phải chia việc: MÁY định vị, MODEL sinh.")
    elif dung >= 3:
        print("  ĐỨNG MỘT PHẦN (%d/9)" % dung)
    else:
        print("  KHÔNG ĐẠT — đã cho không khâu tìm mà vẫn hỏng, nên chỗ hỏng")
        print("  KHÔNG phải chiều sinh/sửa.")
    print("  sổ: %s" % SO)
    return 0 if dung >= 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
