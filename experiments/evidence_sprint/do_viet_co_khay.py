# -*- coding: utf-8 -*-
"""E3 — CÙNG MỘT HÀM, HAI CHIỀU: bắt model VIẾT thay vì SỬA. Có khay thẻ.

VÌ SAO — 20/08/2026. Thiết kế này là của Sếp:

    "LLM tạo code dễ hơn sửa code vì nó được huấn luyện như thế. Nếu cho một
     khay thẻ sẵn để model vừa ghép thẻ vừa viết để chạy, chắc model làm tốt
     hơn việc gắn thẻ để sửa lỗi."

Kho đã có sẵn một nửa số liệu mà tôi không nhận ra mình có:

    SINH có khay   model viết mã dùng hàm kho, khay 24 thẻ    25/28 = 89%
    SỬA  có thẻ    model gắn thẻ để sửa lỗi                     1/9 = 11%

Cùng model, cùng kho hàm, cùng cái khay. Chiều sinh 89%, chiều sửa 11%. Nhưng
hai con số ấy đo HAI VIỆC KHÁC NHAU nên chưa so ngang hàng được.

E3 so ngang hàng: **cùng 9 đề, cùng những hàm ấy, chỉ đổi CHIỀU của câu hỏi.**

    nền  đưa hàm ĐÃ HỎNG + lỗi pytest  ->  "sửa đi"        (chiều SỬA)
    E3   đưa chữ ký + tài liệu + test  ->  "viết thân đi"   (chiều SINH)

Thân hàm bị khoét sạch, chỉ giữ `def` và docstring — docstring chính là bản đặc
tả, và test là bản nghiệm thu. Model không hề thấy mã hỏng.

MỘT CHỖ BẤT ĐỐI XỨNG PHẢI NÓI TRƯỚC, không giấu:

    Với chiều SỬA, "đúng" = khôi phục đúng bản gốc — vì bản gốc CHÍNH LÀ đáp án.
    Với chiều SINH, model viết khác bản gốc mà vẫn đúng là chuyện bình thường.

Nên E3 chấm bằng **cả bộ test**, không phải chỉ tệp test của đề — đó là hàng rào
duy nhất còn lại khi không so được với bản gốc. Cột "trùng bản gốc" vẫn ghi, để
biết bao nhiêu lần model viết ra đúng thứ người đã viết.

NGƯỠNG ĐẶT TRƯỚC:
    >= 5/9 xanh CẢ BỘ   chiều sinh mạnh hơn chiều sửa rõ rệt -> app chốt thiết kế
    3..4/9              hơn nhưng chưa dứt khoát
    <= 2/9              không hơn nền, giả thuyết KHÔNG đứng

    venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_viet_co_khay.py [so_de]
"""
from __future__ import annotations

import ast
import io
import json
import random
import re
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

from core.khay_the import bang_khay, loc_khay, sinh_khay      # noqa: E402
from dung_de_loi import chay_test, dot_bien                   # noqa: E402

MODEL = "qwen2.5-coder:7b"     # ĐÚNG model của nền 2/9
TRAN_LUOT = 4                  # ĐÚNG trần của nền 2/9
PY = str(GOC / "venv" / "Scripts" / "python.exe")
SO = NHA / "so_viet_co_khay.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
CO_KHAY = 24                   # cỡ khay đã chốt 20/08


def hoi(p: str) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "5m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": 1200,
                     "num_ctx": 8192}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(),
                               method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=1200) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def ham_dinh_loi(chuan: str, ma: str) -> list[str]:
    """Hàm nào chứa chỗ đột biến. MÁY tính, chỉ để khoét — model không thấy."""
    a, b = chuan.splitlines(), ma.splitlines()
    lech = [i + 1 for i in range(min(len(a), len(b))) if a[i] != b[i]]
    ra = []
    for n in ast.walk(ast.parse(chuan)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(n.lineno <= x <= (n.end_lineno or n.lineno) for x in lech):
                ra.append(n.name)
    return sorted(set(ra))


def khoet_than(chuan: str, ten_ham: list[str]) -> tuple[str, dict[str, str]]:
    """Xoá sạch THÂN của những hàm nêu tên, giữ `def` và docstring.

    Docstring chính là bản đặc tả — giữ lại thì model có đủ để viết, mà vẫn
    không thấy một dòng nào của lời giải.
    """
    dong = chuan.splitlines()
    can = set(ten_ham)
    goc_than: dict[str, str] = {}
    bo = set()
    chen: dict[int, list[str]] = {}
    for n in ast.walk(ast.parse(chuan)):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if n.name not in can:
            continue
        d0 = n.body[0]
        co_doc = (isinstance(d0, ast.Expr)
                  and isinstance(d0.value, ast.Constant)
                  and isinstance(d0.value.value, str))
        bat_dau = (d0.end_lineno if co_doc else n.lineno) + 1
        het = n.end_lineno or n.lineno
        goc_than[n.name] = "\n".join(dong[bat_dau - 1:het])
        for i in range(bat_dau, het + 1):
            bo.add(i)
        thut = " " * (len(dong[het - 1]) - len(dong[het - 1].lstrip()))
        chen[bat_dau] = ["%s# >>> VIẾT THÂN HÀM `%s` Ở ĐÂY <<<" % (thut, n.name),
                         "%spass" % thut]
    ra = []
    for i, l in enumerate(dong, 1):
        if i in chen:
            ra += chen[i]
        if i not in bo:
            ra.append(l)
    return "\n".join(ra) + "\n", goc_than


def _boc_rao(s: str) -> str:
    t = s.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def ap_ham(nguon: str, va: str) -> tuple[str, str]:
    """Thay nguyên hàm bằng hàm model viết. Chỉ nhận `def` cấp mô-đun."""
    try:
        cay_va = ast.parse(_boc_rao(va))
    except SyntaxError as e:
        return "", "bản vá vỡ cú pháp: %s" % str(e)[:60]
    moi = {n.name: n for n in cay_va.body
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not moi:
        return "", "bản vá không có hàm nào"
    try:
        cay = ast.parse(nguon)
    except SyntaxError as e:
        return "", "nguồn hỏng: %s" % str(e)[:60]
    thay = 0
    for i, n in enumerate(cay.body):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in moi:
            cay.body[i] = moi.pop(n.name)
            thay += 1
    if not thay:
        return "", "không tìm thấy hàm %s trong tệp" % sorted(moi)[:2]
    return ast.unparse(ast.fix_missing_locations(cay)), ""


def mot_de(tam: Path, d: dict, khay_day: list) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")
    chuan = ast.unparse(ast.parse(goc))
    ma, _mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc"}
    ten_ham = ham_dinh_loi(chuan, ma)
    if not ten_ham:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "không xác định được hàm"}
    da_khoet, _than_goc = khoet_than(chuan, ten_ham)

    f.write_text(da_khoet, encoding="utf-8")
    _, loi = chay_test(tam, tep_test)
    ma_test = (tam / tep_test).read_text(encoding="utf-8")

    lich_su = ""
    ghi = []
    hien = da_khoet
    try:
        for luot in range(1, TRAN_LUOT + 1):
            k = loc_khay(khay_day, " ".join(ten_ham) + " " + tep, CO_KHAY)
            p = ("Bạn VIẾT mã Python. Thân của %d hàm dưới đây đã bị xoá, chỗ "
                 "cần viết đánh dấu `# >>> VIẾT THÂN HÀM ... <<<`.\n"
                 "Docstring của hàm là bản đặc tả. Tệp test là bản nghiệm thu.\n\n"
                 "KHAY HÀM CÓ SẴN trong kho (dùng nếu cần):\n%s\n\n"
                 "=== MÃ NGUỒN (%s) ===\n%s\n"
                 "=== TỆP TEST ===\n%s\n%s"
                 "\nCÁCH TRẢ LỜI: viết lại TOÀN VĂN %d hàm đó, từ dòng `def` tới "
                 "hết thân. Chỉ mã Python, không giải thích, không khối markdown.\n"
                 "=== TRẢ LỜI ===\n"
                 % (len(ten_ham), bang_khay(k), tep, hien[:7000],
                    ma_test[:4000], lich_su, len(ten_ham)))
            ra, giay = hoi(p)
            sua, hong = ap_ham(hien, ra)
            ghi.append({"luot": luot, "giay": round(giay, 1), "hong": hong,
                        "va": ra[:1500]})
            if hong:
                lich_su = "\n=== LƯỢT %d KHÔNG ÁP ĐƯỢC ===\n%s\n" % (luot, hong)
                continue
            f.write_text(sua, encoding="utf-8")
            m2, bao = chay_test(tam, tep_test)
            if m2 == 0:
                # CẢ BỘ TEST — hàng rào duy nhất còn lại khi không so được với
                # bản gốc, vì viết khác bản gốc mà đúng là chuyện bình thường.
                x = subprocess.run(
                    [PY, "-X", "utf8", "-m", "pytest", "tests", "-q",
                     "--no-header", "-p", "no:cacheprovider"],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", cwd=str(tam), timeout=900)
                try:
                    trung = ast.dump(ast.parse(sua)) == ast.dump(ast.parse(chuan))
                except SyntaxError:
                    trung = False
                return {"trang_thai": "dat" if x.returncode == 0 else "vo_cho_khac",
                        "luot": luot, "ghi": ghi, "trung_ban_goc": trung,
                        "ham": ten_ham, "ca_bo": (x.stdout or "")[-200:]}
            hien, loi = sua, bao
            lich_su = ("\n=== LƯỢT %d VẪN ĐỎ ===\n%s\nĐừng lặp lại cách đó.\n"
                       % (luot, bao[-400:]))
        return {"trang_thai": "het_luot", "luot": TRAN_LUOT, "ghi": ghi,
                "trung_ban_goc": False, "ham": ten_ham}
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

    khay_day = sinh_khay(GOC)
    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    print("  %d đề · %s · trần %d lượt · khay %d thẻ · VIẾT chứ không SỬA\n"
          % (len(de), MODEL, TRAN_LUOT, CO_KHAY))
    try:
        for d in de:
            t0 = time.monotonic()
            r = mot_de(tam, d, khay_day)
            r.update({"tep": d["tep"], "so_loi": d["so_loi"],
                      "giay": round(time.monotonic() - t0, 1)})
            so.append(r)
            SO.write_text(json.dumps(so, ensure_ascii=False, indent=1),
                          encoding="utf-8")
            print("  %-22s %d lỗi  %-13s trùng bản gốc: %-5s %4.0fs  %s"
                  % (d["tep"].split("/")[-1][:22], d["so_loi"],
                     r["trang_thai"], r.get("trung_ban_goc"), r["giay"],
                     ",".join(r.get("ham", []))[:28]))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    dat = sum(1 for x in so if x["trang_thai"] == "dat")
    vo = sum(1 for x in so if x["trang_thai"] == "vo_cho_khac")
    trung = sum(1 for x in so if x.get("trung_ban_goc"))
    print("\n" + "=" * 64)
    print("  E3 — VIẾT (chiều sinh) so với nền SỬA (chiều sửa)")
    print("=" * 64)
    print("  nền: sửa hàm đã hỏng      2/9 xanh")
    print("  E3 xanh CẢ BỘ test        : %d/%d   <- cột quyết định" % (dat, len(so)))
    print("  xanh test đề nhưng vỡ chỗ khác: %d" % vo)
    print("  viết TRÙNG bản gốc        : %d/%d" % (trung, len(so)))
    print("  thời gian                 : %.0f phút" % (sum(x.get("giay", 0) for x in so) / 60))
    print()
    if dat >= 5:
        print("  ĐẠT — chiều SINH mạnh hơn chiều SỬA rõ rệt.")
        print("  App chốt được thiết kế: MÁY định vị & khoét, MODEL viết lại.")
    elif dat >= 3:
        print("  HƠN NỀN nhưng chưa dứt khoát (%d/9)" % dat)
    else:
        print("  KHÔNG HƠN NỀN — giả thuyết 'sinh dễ hơn sửa' không đứng ở đây.")
    print("  sổ: %s" % SO)
    return 0 if dat >= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
