# -*- coding: utf-8 -*-
"""Đo model SỬA LỖI: phân cấp theo số lỗi × cỡ khay, có trần thử sai.

Sếp chốt 19/08 năm thứ, tệp này làm đủ cả năm:

    1. TEST làm cân — đo cột "LÀM ĐÚNG VIỆC", không chỉ "gọi đúng hàm".
       Test của KHO, do người viết, không phải tôi bịa cho vừa ý.
    2. ĐỌC SUY LUẬN mỗi lần chọn — model phải nói nó sửa chỗ nào và vì sao,
       trước khi đưa bản vá.
    3. KHÔNG đòi đúng ngay lượt đầu — đếm XONG SAU BAO NHIÊU LƯỢT.
    4. PHÂN CẤP theo số lỗi (1, 2, 3) và tăng dần cỡ khay (0, 8, 30 thẻ).
    5. TRẦN THỬ SAI — hết lượt thì thôi, ghi là chưa xong.

VÌ SAO ĐỔI SANG ĐỀ SỬA LỖI. Mấy vòng trước đo "viết hàm dùng thẻ trong khay",
và cột duy nhất đo được là *có gọi đúng hàm không*. Soi tay 19/08 thì thấy có
đề gọi đúng hàm mà mã chạy là nổ `NameError` — bộ chấm vẫn ghi ĐẠT. Muốn đo
"làm đúng việc" thì phải có cân, và cân sẵn có là bộ test của kho.

Đề sinh bởi `dung_de_loi.py`: đột biến MÁY, mỗi lỗi đã chứng minh làm test đỏ.

CÁCH ĐẾM LƯỢT: mỗi lượt model nhận lại NGUYÊN VĂN lỗi pytest của lượt trước.
Không tóm tắt hộ — tóm tắt là chỗ mình chen phán đoán vào rồi tưởng model tự
nghĩ ra.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_sua_loi.py [so_de]
"""
from __future__ import annotations

import ast
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import bang_khay, loc_khay, sinh_khay        # noqa: E402
from dung_de_loi import DotBien, chay_test, dot_bien            # noqa: E402
from dinh_vi import cat_ham, ham_da_chay, test_do_nao          # noqa: E402

GOC = Path(__file__).resolve().parent.parent.parent
NHA = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
TRAN_LUOT = 4              # trần thử sai
PY = str(GOC / "venv" / "Scripts" / "python.exe")
# Tắt được để đo lại bản cũ mà không sửa mã — cùng tệp, cùng đề, một biến.
DUNG_DINH_VI = os.environ.get("SUA_LOI_DINH_VI", "1") != "0"
TRAN_MA = 9000             # ký tự mã đưa cho model


def hoi(p: str, tran: int = 700) -> tuple[str, float]:
    b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
         "keep_alive": "10m",
         "options": {"seed": 42, "temperature": 0.2, "num_predict": tran,
                     "num_ctx": 16384}}
    r = urllib.request.Request(OLLAMA, data=json.dumps(b).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=1800) as x:
        k = json.loads(x.read().decode())
    return (k.get("response") or "").strip(), time.monotonic() - t0


def _boc(ra: str) -> str:
    t = ra.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def tach(ra: str) -> tuple[str, str]:
    """Tách phần SUY LUẬN khỏi phần MÃ. Cả hai đều phải giữ."""
    m = re.search(r"^\s*SUYLUAN\s*:?\s*(.+?)^\s*MA\s*:?\s*$", ra,
                  re.M | re.S | re.I)
    if m:
        return m.group(1).strip(), _boc(ra[m.end():])
    # model không theo khuôn -> coi cả khối là mã, ghi suy luận rỗng
    return "", _boc(ra)


def ap_ham(nguon: str, va: str) -> tuple[str, str]:
    """Thay hàm cùng tên trong `nguon` bằng hàm trong `va`."""
    try:
        cay_moi = ast.parse(va)
    except SyntaxError as e:
        return "", f"bản vá hỏng cú pháp: {str(e)[:60]}"
    ham_moi = {n.name: n for n in cay_moi.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not ham_moi:
        return "", "bản vá không có hàm nào"
    try:
        cay = ast.parse(nguon)
    except SyntaxError as e:
        return "", f"nguồn hỏng: {str(e)[:60]}"
    thay = 0
    for i, n in enumerate(cay.body):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in ham_moi:
            cay.body[i] = ham_moi.pop(n.name)
            thay += 1
    if not thay:
        return "", f"không tìm thấy hàm {sorted(ham_moi)[:2]} trong tệp"
    return ast.unparse(ast.fix_missing_locations(cay)), ""


def mot_de(tam: Path, d: dict, khay_day: list, co_the: int) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")

    # Gieo cả N lỗi trong MỘT lượt duyệt.
    #
    # Bản đầu gọi `dot_bien` N lần liên tiếp trên mã đã đột biến. Mỗi lần đột
    # biến là cây cú pháp đổi — `bỏ phủ định` xoá hẳn một nút — nên chỉ số của
    # lỗi thứ hai, thứ ba tụt đi và trỏ vào chỗ khác. Đề 3 lỗi đầu tiên hỏng
    # đúng vì thế. Mà số lỗi chính là trục đang đo.
    ma, mo_ta = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc",
                "vi_sao": f"không gieo đủ {len(d['cho'])} lỗi ở {d['cho']}"}
    f.write_text(ma, encoding="utf-8")

    _, loi = chay_test(tam, tep_test)

    # ĐỊNH VỊ BẰNG MÁY, rồi chỉ đưa hàm nghi ngờ thay vì cả tệp.
    #
    # Ba AI đọc số 2/9 đều xếp hướng này hạng nhất, và cùng nói một điều: đừng
    # bắt model 7B vừa TÌM lỗi vừa SỬA lỗi. Máy chạy test đỏ dưới `sys.settrace`,
    # ghi lại hàm nào của tệp nguồn thực sự chạy — hàm không chạy thì không thể
    # gây đỏ.
    #
    # Đo được 19/08 trên ba tệp: web_search cắt còn 40% (tệp rối nhất, và cũng
    # là tệp trước giờ 0/3), may_tinh còn 66%, dong_ho giữ 100% (chỉ có 1 hàm).
    #
    # ĐỔI ĐÚNG MỘT BIẾN so với lượt 2/9: vẫn model ấy, đề ấy, cách chấm ấy,
    # trần 4 lượt ấy. Chỉ khác chỗ mã đưa vào.
    ma_dua = ma
    ham_nghi: list[str] = []
    if DUNG_DINH_VI:
        do = test_do_nao(tam, tep_test, PY)
        if do:
            ham_nghi = ham_da_chay(tam, tep, do[0], PY)
            if ham_nghi:
                ma_dua = cat_ham(ma, ham_nghi)
    lich_su = ""
    ghi = []
    try:
        for luot in range(1, TRAN_LUOT + 1):
            khay = ""
            if co_the:
                k = loc_khay(khay_day, d.get("goi_y", tep), co_the)
                khay = f"\nKHAY HÀM CÓ SẴN trong kho (dùng nếu cần):\n{bang_khay(k)}\n"
            nhan = (f", chỉ các hàm test đỏ chạy qua: {', '.join(ham_nghi)}"
                    if ham_nghi and len(ma_dua) < len(ma) else "")
            p = (f"Bạn sửa lỗi mã Python. Test đang ĐỎ.\n"
                 f"{khay}\n=== MÃ NGUỒN ({tep}{nhan}) ===\n{ma_dua[:TRAN_MA]}\n"
                 f"=== PYTEST BÁO ===\n{loi[-1000:]}\n{lich_su}"
                 f"\nTrả lời ĐÚNG khuôn hai phần:\n"
                 f"SUYLUAN:\n<bạn nghĩ lỗi nằm ở đâu, vì sao, và vì sao chọn cách "
                 f"sửa đó thay vì cách khác — tối đa 4 câu>\n"
                 f"MA:\n<viết lại TOÀN VĂN hàm cần sửa, chỉ mã Python>\n")
            ra, g = hoi(p)
            suy, va = tach(ra)
            sua, hong = ap_ham(ma, va)
            ghi.append({"luot": luot, "suy_luan": suy, "giay": round(g, 1),
                        "hong": hong, "va": va[:600]})
            if hong:
                lich_su = (f"\n=== LƯỢT {luot} CỦA BẠN KHÔNG ÁP ĐƯỢC ===\n{hong}\n")
                continue
            f.write_text(sua, encoding="utf-8")
            m2, bao = chay_test(tam, tep_test)
            if m2 == 0:
                return {"trang_thai": "dat", "luot": luot, "ghi": ghi,
                        "ham_nghi": ham_nghi}
            # `ma` là TOÀN VĂN tệp (để vá tiếp), `ma_dua` là phần cắt cho model.
            # Trộn hai cái là đưa cả tệp trở lại từ lượt 2 và mất luôn phép đo.
            ma, loi = sua, bao
            ma_dua = cat_ham(sua, ham_nghi) if ham_nghi else sua
            lich_su = (f"\n=== LƯỢT {luot} VẪN ĐỎ ===\n{bao[-500:]}\n"
                       f"Đừng lặp lại cách đó.\n")
        return {"trang_thai": "het_luot", "luot": TRAN_LUOT, "ghi": ghi,
                "ham_nghi": ham_nghi}
    finally:
        f.write_text(goc, encoding="utf-8")


def main() -> int:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10)
    except Exception:                                            # noqa: BLE001
        print("  Ollama chưa chạy — KHÔNG ĐO ĐƯỢC")
        return 2
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo_tep: dict[str, list] = {}
    for x in loi:
        theo_tep.setdefault(x["tep"], []).append(x)

    rng = random.Random(19082026)
    de = []
    for tep, ds in theo_tep.items():
        for so_loi in (1, 2, 3):
            if len(ds) >= so_loi:
                cho = [x["cho"] for x in rng.sample(ds, so_loi)]
                de.append({"tep": tep, "tep_test": ds[0]["tep_test"],
                           "cho": cho, "so_loi": so_loi})
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(de)
    de = de[:n]

    khay_day = sinh_khay(GOC)
    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))

    # NHỚ CHỖ ĐÃ LÀM. Đo được 19/08: ~20 phút một đề (RAM tụt còn 677 MB nên
    # máy giã đĩa). Không nhớ thì mỗi lần cắt bớt lại đốt lại từ đầu.
    so = []
    if (NHA / "so_sua_loi.json").is_file():
        so = json.loads((NHA / "so_sua_loi.json").read_text(encoding="utf-8"))
        xong = {(x["tep"], x["so_loi"]) for x in so}
        de = [d for d in de if (d["tep"], d["so_loi"]) not in xong]
        print(f"  đã có {len(so)} đề trong sổ, còn {len(de)} đề\n")
    print(f"  {len(de)} đề · trần thử sai {TRAN_LUOT} lượt · khay 8 thẻ\n")
    try:
        # BỎ TRỤC KHAY, giữ đúng khay 8 thẻ (Sếp chốt 19/08).
        #
        # Ba lượt đầu — cùng một đề, khay 0 / 8 / 30 — đều `het_luot` y hệt.
        # Đúng như trông đợi: khay cho biết KHO CÓ GÌ, không giúp TÌM LỖI Ở ĐÂU.
        # Ở loại đề sửa-lỗi thì trục khay không mang thông tin, mà nó nhân ba
        # thời gian: đủ lưới 24 đề × 3 khay là ~17 tiếng máy, mà máy thì ngủ.
        for d in de:
            for co_the in (8,):
                r = mot_de(tam, d, khay_day, co_the)
                r.update({"tep": d["tep"], "so_loi": d["so_loi"], "co_the": co_the})
                so.append(r)
                (NHA / "so_sua_loi.json").write_text(
                    json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
                tt = r["trang_thai"]
                print(f"  {d['tep']:<26}{d['so_loi']} lỗi  khay {co_the:>2}  "
                      f"{tt:<12}{('lượt ' + str(r.get('luot'))) if tt == 'dat' else ''}")
                if r.get("ghi"):
                    s1 = r["ghi"][0].get("suy_luan", "")
                    if s1:
                        print(f"      lượt 1 nghĩ: {s1[:110]}")
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    print("\n  ===== XONG SAU BAO NHIÊU LƯỢT =====")
    print(f"  {'số lỗi':<8}{'khay':<7}{'đạt':<8}{'lượt trung bình':<18}")
    for sl in sorted({x["so_loi"] for x in so}):
        for ct in sorted({x["co_the"] for x in so}):
            g = [x for x in so if x["so_loi"] == sl and x["co_the"] == ct]
            if not g:
                continue
            dat = [x for x in g if x["trang_thai"] == "dat"]
            tb = sum(x["luot"] for x in dat) / len(dat) if dat else 0
            print(f"  {sl:<8}{ct:<7}{len(dat)}/{len(g):<6}"
                  f"{(f'{tb:.1f}' if dat else '-'):<18}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
