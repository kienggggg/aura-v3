# -*- coding: utf-8 -*-
"""E2 — CHO SẴN CHỖ, chỉ hỏi ĐIỀN GÌ. Đo giả thuyết "sinh được, sửa không được".

VÌ SAO — 20/08/2026, Sếp nêu và số liệu cả ngày khớp.

Sếp gọi tên bằng một ví dụ: hỏi *"mẹ Cristiano Ronaldo là ai"* thì model đáp
ngay *Dolores Aveiro*; hỏi ngược *"Dolores Aveiro là mẹ của ai"* thì tịt. Cùng
một quan hệ, đổi chiều thì hỏng. Model sinh ra để **viết mã**, nên chiều
**sửa mã** với nó là chiều ngược.

Số cả ngày khớp một cách ĐƠN ĐIỆU, mà tôi không nhận ra:

    nền  viết lại TOÀN VĂN hàm   (gần với SINH)      2/9   <- CAO NHẤT
    C    đổi một ô thẻ            (SỬA)               1/9
    C2   đổi một ô + ép khuôn     (SỬA hẹp hơn)       0/9
    C3   đổi một ô enum           (SỬA hẹp nhất)      0/9

Càng kéo về phía "sửa" thì càng tệ, không một ngoại lệ. Cả ngày tôi đẩy model
RA XA thứ nó giỏi, rồi kết luận nó dở.

PHÉP ĐO NÀY tách hẳn hai chiều bằng cách CHO KHÔNG khâu định vị:

    máy khoét đúng chỗ đột biến thành `____`
    model chỉ phải trả lời: chỗ trống ấy điền gì

Đây cũng đúng cảnh app thẻ tạo ra — Sếp nói: "vì đã trực quan hóa nên thẻ báo
đỏ ngay nên model không cần tìm". Nếu model vẫn hỏng ở đây thì giả thuyết
"sinh được, sửa không được" KHÔNG đứng, vì đã cho không phần tìm.

CHẤM HAI CỘT, không gộp (bài học 20/08: xanh không phải đúng):

    xanh        test đỏ -> xanh
    đúng nghĩa  cây cú pháp trùng bản gốc

NGƯỠNG ĐẶT TRƯỚC:
    >= 6/9 đúng nghĩa   giả thuyết ĐỨNG -> app chia việc: MÁY định vị, MODEL sinh
    3..5/9              đứng một phần
    <= 2/9              không hơn nền 2/9 -> giả thuyết KHÔNG đứng, và chỗ hỏng
                        không phải chiều sinh/sửa

    venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_dien_cho_trong.py [so_de]
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
TRAN_LUOT = 4                  # ĐÚNG trần của nền 2/9
SO = NHA / "so_dien_cho_trong.json"
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


def mot_de(tam: Path, d: dict) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")
    ma, mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc"}
    chuan = ast.unparse(ast.parse(goc))
    da_khoet, dap = khoet(chuan, ma)
    if not dap:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "không khoét được chỗ nào"}

    f.write_text(ma, encoding="utf-8")
    _, loi = chay_test(tam, tep_test)

    lich_su = ""
    ghi = []
    try:
        for luot in range(1, TRAN_LUOT + 1):
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
            # ghép lại: thay đúng những dòng đã khoét
            d_ra = da_khoet.splitlines()
            k = 0
            for i, l in enumerate(d_ra):
                if l.strip() == CHO_TRONG:
                    d_ra[i] = dong_moi[k]
                    k += 1
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
    print("  %d đề · %s · trần %d lượt · CHO SẴN CHỖ, chỉ hỏi điền gì\n"
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
