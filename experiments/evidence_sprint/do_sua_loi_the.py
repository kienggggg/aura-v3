# -*- coding: utf-8 -*-
"""CHẶNG C — Delta sửa lỗi bằng cách ĐỔI MỘT Ô THẺ, không viết lại cả hàm.

VÌ SAO — 20/08/2026.

`do_sua_loi.py` bắt model viết lại TOÀN VĂN hàm rồi ghi đè: nền 2/9. Giả thuyết
là model trượt không phải vì dốt mà vì **bề mặt sửa quá rộng** — mỗi lượt viết
lại cả hàm là một cơ hội làm hỏng dòng không liên quan.

Chặng B đo được ba con số nói rằng bề mặt thu lại được:

    28/29 chỗ đột biến nằm trong THẺ THẬT
    29/29 đột biến chạm đúng MỘT dòng
    29/29 đột biến chạm đúng MỘT thẻ
    15/29 rơi vào thẻ `neu` — tức là đổi đúng ô `dieu_kien`

Nên ở đây model không viết mã. Nó trả về `{"id": "...", "o": {...}}`.

ĐỔI ĐÚNG MỘT BIẾN so với nền 2/9: cùng model `qwen2.5-coder:7b`, cùng 9 đề ấy,
cùng trần 4 lượt, cùng cách chấm (test đỏ -> xanh). Chỉ khác **hình dạng câu trả
lời**.

NGƯỠNG ĐẶT TRƯỚC:
    >= 5/9   hướng đúng, đi tiếp và chạy đủ 24 đề
    3..4/9   đo được mà không đạt — n=9 thì một đề là 11 điểm phần trăm,
             3/9 so với 2/9 nằm trong nhiễu, phải thêm đề mới kết luận được
    <= 2/9   không hơn nền, đóng hồ sơ hướng này

ĐO RIÊNG HAI THỨ, không gộp:
    chọn đúng thẻ   — model có trỏ vào thẻ chứa đột biến không
    sửa đúng giá trị — ô mới có làm test xanh không
Gộp lại thì không biết nên chữa cách trình bày thẻ hay chữa model.

    venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_sua_loi_the.py [so_de]
"""
from __future__ import annotations

import ast
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(NHA))

from core.the_cst import (doc_chuoi_py_sang_cay_the,           # noqa: E402
                          luu_cay_the_ra_tep_py,
                          O_HUU_HAN as O_HUU_HAN_THE)
from dung_de_loi import chay_test, dot_bien                                # noqa: E402

MODEL = "qwen2.5-coder:7b"     # ĐÚNG model của nền 2/9, đừng đổi
TRAN_LUOT = 4                  # ĐÚNG trần của nền 2/9
PY = str(GOC / "venv" / "Scripts" / "python.exe")
EP_KHUON = "--ep" in sys.argv
BO_SAU = "--sau" in sys.argv          # bổ thẻ biểu thức, bản vẽ của Sếp 20/08
SO = NHA / ("so_sua_loi_the_%s.json" % ("sau" if BO_SAU else "ep")
            if EP_KHUON else "so_sua_loi_the.json")
TRAN_THE = 60                  # số thẻ tối đa bày ra cho model
OLLAMA = "http://127.0.0.1:11434/api/generate"


def hoi(p: str, khuon: dict | None = None) -> tuple[str, float]:
    """Hỏi model. `khuon` là JSON Schema — Ollama ÉP câu trả lời vào đúng nó.

    Đo 20/08: Ollama 0.32.14 nhận `format` là cả một lược đồ, kể cả `enum`. Nên
    `id` thẻ ép được vào danh sách thẻ CÓ THẬT, và ô có tập giá trị hữu hạn ép
    được vào đúng tập ấy — model không còn chỗ để bịa id `75` hay xuất JSON gãy.
    """
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 200,
                     "num_ctx": 8192}}
    if khuon:
        b["format"] = khuon
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(),
                               method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=900) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _phang(ns):
    ra = []
    for n in ns:
        ra.append(n)
        ra += _phang(n.than)
    return ra


def bay_the(nguon: str, dong_nghi: set[int] | None = None):
    """Bày cây thẻ ra cho người đọc, kèm bản đồ id -> thẻ.

    Chỉ bày thẻ THẬT có ô sửa được. Thẻ `ma_tho` bày ra cũng vô ích: model
    không sửa được nó bằng một ô, mà nó chiếm chỗ trong ngữ cảnh.
    """
    rec = doc_chuoi_py_sang_cay_the(nguon, bo_sau=BO_SAU)
    ds = [n for n in _phang(rec.tree) if n.ma != "ma_tho" and n.o]
    if dong_nghi:
        loc = [n for n in ds if n.line_start in dong_nghi]
        if loc:
            ds = loc
    ds = ds[:TRAN_THE]
    dong = nguon.splitlines()
    d = []
    for n in ds:
        goc = (dong[n.line_start - 1].strip()[:70]
               if n.line_start and n.line_start <= len(dong) else "")
        o = " · ".join("%s=%r" % (k, v[:60]) for k, v in n.o.items())
        d.append("  %-14s dòng %-4s %-10s %s\n      | %s"
                 % (n.id, n.line_start, n.ma, o, goc))
    return "\n".join(d), rec, {n.id: n for n in ds}


# Ô nào có tập giá trị HỮU HẠN thì ép luôn vào tập ấy. Ngoài danh sách này thì
# để model gõ tự do — ép bừa một tập không đầy đủ còn tệ hơn không ép.
O_HUU_HAN: dict[str, list[str]] = {}


def dung_khuon(ban_do: dict) -> dict:
    """JSON Schema cho câu trả lời: id ép vào thẻ CÓ THẬT, ô ép vào ô CÓ THẬT.

    Ô nào thuộc thẻ biểu thức thì ép luôn GIÁ TRỊ vào tập hữu hạn. Gom theo
    TÊN Ô chứ không theo thẻ, vì lược đồ JSON không nói được "ô này phụ thuộc
    id kia" — nên `phep` nhận hợp của mọi tập `phep`. Vẫn chặt hơn chữ tự do
    rất nhiều: 23 ký hiệu thay vì vô hạn, và model không nhét nổi cả hàm vào.
    """
    o_co = sorted({k for n in ban_do.values() for k in n.o})
    hh: dict[str, set] = {}
    for n in ban_do.values():
        for o_ten, ds in O_HUU_HAN_THE.get(n.ma, {}).items():
            if o_ten in n.o:
                hh.setdefault(o_ten, set()).update(ds)
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string", "enum": sorted(ban_do)},
            "o": {
                "type": "object",
                "properties": {k: ({"type": "string", "enum": sorted(hh[k])}
                                   if k in hh else {"type": "string"})
                               for k in o_co},
                "minProperties": 1,
            },
        },
        "required": ["id", "o"],
    }


def doc_tra_loi(ra: str) -> tuple[dict | None, str]:
    """Rút JSON từ câu trả lời. Không có thì nói rõ, đừng đoán hộ model."""
    t = ra.strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None, "không thấy JSON trong câu trả lời"
    try:
        d = json.loads(t[i:j + 1])
    except json.JSONDecodeError as e:
        return None, "JSON hỏng: %s" % str(e)[:60]
    if not isinstance(d, dict) or "id" not in d or "o" not in d:
        return None, "JSON thiếu khoá `id` hoặc `o`"
    if not isinstance(d["o"], dict) or not d["o"]:
        return None, "khoá `o` phải là object không rỗng"
    return d, ""


def ap_the(rec, ban_do: dict, tra: dict) -> tuple[bytes | None, str]:
    """Áp một sửa đổi lên đúng MỘT thẻ. Từ chối mọi thứ ngoài khuôn.

    Giữ đúng ràng buộc mà `the_api._rang_buoc_cau_truc_va_danh_dau` áp cho
    đường thật: chỉ được sửa Ô của thẻ ĐÃ CÓ, không thêm không xoá thẻ.
    """
    nut = ban_do.get(tra["id"])
    if nut is None:
        return None, "không có thẻ id %r" % tra["id"]
    la = set(nut.o)
    xin = set(tra["o"])
    if not xin <= la:
        return None, "thẻ %s không có ô %s" % (tra["id"], sorted(xin - la))
    doi = False
    for k, v in tra["o"].items():
        if not isinstance(v, str):
            return None, "ô %s phải là chuỗi" % k
        if v != nut.o[k]:
            nut.o[k] = v
            doi = True
    if not doi:
        return None, "ô mới giống hệt ô cũ, không có gì để sửa"
    nut.da_sua = True
    rec.has_modifications = True
    try:
        return luu_cay_the_ra_tep_py(rec), ""
    except Exception as e:                                       # noqa: BLE001
        return None, "áp thẻ hỏng: %s" % (repr(e)[:70])


def mot_de(tam: Path, d: dict) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")

    ma, _mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc",
                "vi_sao": "không gieo đủ %d lỗi" % len(d["cho"])}
    f.write_text(ma, encoding="utf-8")
    _, loi = chay_test(tam, tep_test)

    # DÒNG ĐỘT BIẾN THẬT — chỉ để CHẤM, không đưa cho model.
    chuan = ast.unparse(ast.parse(goc))
    a, b = chuan.splitlines(), ma.splitlines()
    dong_that = {i + 1 for i in range(min(len(a), len(b))) if a[i] != b[i]}

    lich_su = ""
    ghi = []
    chon_dung = False
    try:
        for luot in range(1, TRAN_LUOT + 1):
            bang, rec, ban_do = bay_the(ma)
            p = ("Bạn sửa lỗi mã Python. Test đang ĐỎ.\n\n"
                 "Mã đã được tách thành THẺ. Mỗi thẻ có id, số dòng, loại, và "
                 "các Ô sửa được.\n"
                 "Bạn KHÔNG viết lại mã. Bạn chọn MỘT thẻ và đổi MỘT ô của nó.\n\n"
                 "=== CÁC THẺ TRONG %s ===\n%s\n\n"
                 "=== PYTEST BÁO ===\n%s\n%s"
                 "\nTrả lời ĐÚNG khuôn hai phần:\n"
                 "SUYLUAN:\n<lỗi nằm ở thẻ nào, vì sao — tối đa 3 câu>\n"
                 "JSON:\n{\"id\": \"<id thẻ>\", \"o\": {\"<tên ô>\": \"<giá trị mới>\"}}\n"
                 % (tep, bang, loi[-900:], lich_su))
            ra, giay = hoi(p, dung_khuon(ban_do) if EP_KHUON else None)
            tra, hong = doc_tra_loi(ra)
            suy = ra.split("JSON")[0].replace("SUYLUAN:", "").strip()[:400]
            if tra is None:
                ghi.append({"luot": luot, "giay": round(giay, 1),
                            "hong": hong, "ra": ra[:300]})
                lich_su = "\n=== LƯỢT %d KHÔNG ĐỌC ĐƯỢC ===\n%s\n" % (luot, hong)
                continue
            nut = ban_do.get(tra["id"])
            dung_the = bool(nut and nut.line_start in dong_that)
            chon_dung = chon_dung or dung_the
            moi, hong = ap_the(rec, ban_do, tra)
            ghi.append({"luot": luot, "giay": round(giay, 1), "suy_luan": suy,
                        "id": tra["id"], "o": tra["o"],
                        "chon_dung_the": dung_the, "hong": hong})
            if moi is None:
                lich_su = "\n=== LƯỢT %d KHÔNG ÁP ĐƯỢC ===\n%s\n" % (luot, hong)
                continue
            f.write_bytes(moi)
            m2, bao = chay_test(tam, tep_test)
            if m2 == 0:
                # Test của đề xanh rồi thì chạy CẢ BỘ, bắt kiểu sửa liều làm
                # hỏng chỗ khác. `chay_test` mặc định chỉ chạy một tệp.
                x = subprocess.run(
                    [PY, "-X", "utf8", "-m", "pytest", "tests", "-q",
                     "--no-header", "-p", "no:cacheprovider"],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", cwd=str(tam), timeout=600)
                # XANH KHÔNG PHẢI ĐÚNG — xem lời dặn cùng tên trong
                # do_sua_loi.py. Chấm thêm: có khôi phục đúng bản gốc không.
                try:
                    dung_nghia = (ast.dump(ast.parse(moi.decode("utf-8")))
                                  == ast.dump(ast.parse(ast.unparse(ast.parse(goc)))))
                except SyntaxError:
                    dung_nghia = False
                return {"trang_thai": "dat" if x.returncode == 0 else "vo_cho_khac",
                        "luot": luot, "ghi": ghi, "chon_dung_the": chon_dung,
                        "dung_nghia": dung_nghia,
                        "ca_bo": (x.stdout or "")[-200:]}
            ma, loi = moi.decode("utf-8"), bao
            lich_su = ("\n=== LƯỢT %d VẪN ĐỎ ===\n%s\nĐừng lặp lại cách đó.\n"
                       % (luot, bao[-400:]))
        return {"trang_thai": "het_luot", "luot": TRAN_LUOT, "ghi": ghi,
                "chon_dung_the": chon_dung}
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
    theo_tep: dict[str, list] = {}
    for x in loi:
        theo_tep.setdefault(x["tep"], []).append(x)

    # DỰNG ĐỀ Y HỆT `do_sua_loi.py`: cùng hạt giống, cùng thứ tự, cùng cách gom.
    # Lệch một chi tiết là hai bảng số không còn so được với nhau.
    rng = random.Random(19082026)
    de = []
    for tep, ds in theo_tep.items():
        for so_loi in (1, 2, 3):
            if len(ds) >= so_loi:
                cho = [x["cho"] for x in rng.sample(ds, so_loi)]
                de.append({"tep": tep, "tep_test": ds[0]["tep_test"],
                           "cho": cho, "so_loi": so_loi})
    so_tay = [a for a in sys.argv[1:] if a.isdigit()]
    n = int(so_tay[0]) if so_tay else 9   # nền chỉ có 9 đề
    de = de[:n]

    so = []
    if SO.is_file():
        so = json.loads(SO.read_text(encoding="utf-8"))
        xong = {(x["tep"], x["so_loi"]) for x in so}
        de = [d for d in de if (d["tep"], d["so_loi"]) not in xong]
        print("  đã có %d đề trong sổ, còn %d đề\n" % (len(so), len(de)))

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__",
        "data", "_rac", "*.pyc"))
    print("  %d đề · model %s · trần %d lượt · sửa bằng ĐỔI MỘT Ô THẺ\n"
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
            print("  %-24s %d lỗi  %-14s %4.0fs  chọn đúng thẻ: %s"
                  % (d["tep"][:24], d["so_loi"], r["trang_thai"], r["giay"],
                     r.get("chon_dung_the")))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    dat = sum(1 for x in so if x["trang_thai"] == "dat")
    vo = sum(1 for x in so if x["trang_thai"] == "vo_cho_khac")
    het = sum(1 for x in so if x["trang_thai"] == "het_luot")
    kdd = sum(1 for x in so if x["trang_thai"] == "khong_do_duoc")
    dung_the = sum(1 for x in so if x.get("chon_dung_the"))
    print("\n" + "=" * 62)
    print("  CHẶNG C%s — sửa lỗi bằng ĐỔI MỘT Ô THẺ"
          % ("3 (ÉP KHUÔN + BỔ SÂU)" if BO_SAU else
             "2 (ÉP KHUÔN)" if EP_KHUON else ""))
    print("=" * 62)
    print("  nền (viết lại cả hàm)     : 2/9")
    if EP_KHUON:
        print("  chặng C (thẻ, chưa ép)    : 1/9")
    print("  đạt                       : %d/%d" % (dat, len(so)))
    print("  vỡ chỗ khác (test đề xanh nhưng cả bộ đỏ): %d" % vo)
    print("  hết lượt                  : %d" % het)
    print("  không đo được             : %d" % kdd)
    print("  CHỌN ĐÚNG THẺ             : %d/%d   <- đo riêng với 'sửa đúng giá trị'"
          % (dung_the, len(so)))
    print("  trong số ĐẠT, ĐÚNG NGHĨA  : %d/%d   <- xanh mà khôi phục đúng bản gốc"
          % (sum(1 for x in so if x.get("dung_nghia")), dat))
    print("  tổng thời gian            : %.0f phút"
          % (sum(x.get("giay", 0) for x in so) / 60))
    print("  sổ: %s" % SO)
    return 0 if dat >= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
