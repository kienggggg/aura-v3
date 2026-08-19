# -*- coding: utf-8 -*-
"""Cho model quyền TRA KHO MÃ, rồi đo lại — và ghi lại NGUYÊN VĂN nó nghĩ gì.

VÌ SAO: đọc tay 29 lượt trượt của gemini (doc_tay_v2.py, 18/08) ra ba nhóm —

    cần TRA KHO (tên nằm ở tệp khác)   10/27 = 37%
    cần KIẾN THỨC chung (thư viện)      2/27 =  7%
    ĐỦ dữ kiện mà vẫn trượt            15/27 = 56%

Nhóm 37% không model nào giải được, dù to đến đâu: bản vá thật đòi
`from core.web_search import loc_menh_lenh`, hàm đó có thật ở dòng 482 của
web_search.py, nhưng máy đo cũ chỉ đưa MỘT tệp và không cho mở gì thêm.

THAY ĐỔI DUY NHẤT so với do_delta.py: thêm ba lệnh cho model gọi. Vùng mã đầu
vào, test, lỗi, cách chấm — giữ y hệt. Đổi hai thứ cùng lúc thì chênh lệch
không quy được cho thứ nào.

LUẬT ĐẶT TRƯỚC KHI CHẠY (viết ở đây để không bẻ số sau khi thấy kết quả):

  Trên đề nhóm can_tra_kho, bản KHÔNG công cụ được 0/10.
    -> đoán: có công cụ thì >= 3/10. Dưới 3 nghĩa là thiếu-tên KHÔNG phải
       nguyên nhân thật, và bảng phân loại của tôi sai.
  Trên đề nhóm trong_vung (đủ dữ kiện sẵn), công cụ ĐÁNG LẼ không giúp gì.
    -> đoán: vẫn ~0. Nếu công cụ giúp cả ở đây thì phân loại cũng sai.

Hai nhóm chạy cùng máy đo, cùng model. Đó là nhóm ĐỐI CHỨNG.

SỔ NÓNG: mỗi đề ghi một tệp .log — nguyên văn lời nhắc, nguyên văn model trả
lời, nguyên văn kết quả công cụ, từng lượt một. Không tóm tắt. Tóm tắt là chỗ
mình chen phán đoán vào rồi tưởng model tự nghĩ ra.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_delta_tra_kho.py --nhom=can_tra_kho
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_cv = sys.argv[1:]
sys.argv = ["tra_kho", "--lan=1"]
import do_delta as D                                            # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

NHOM = next((a.split("=")[1] for a in _cv if a.startswith("--nhom=")), "can_tra_kho")
SO_DE = int(next((a.split("=")[1] for a in _cv if a.startswith("--so=")), "10"))
MODEL = next((a.split("=")[1] for a in _cv if a.startswith("--model=")), "qwen2.5-coder:7b")
TRAN_CONG_CU = 3           # gọi công cụ quá số này thì buộc phải nộp bài
BACKEND = os.environ.get("DELTA_BACKEND", "ollama")
LLAMA = os.environ.get("DELTA_LLAMA_URL", "http://127.0.0.1:8088")
SO = Path("D:/alpha_bench/ket_qua_tra_kho.json")
SO_NONG = Path("D:/alpha_bench/so_nong")

HUONG_DAN = """Bạn sửa lỗi trong mã Python. Test dưới đây đang ĐỎ.
Sửa MÃ NGUỒN ({ten}) cho test xanh. KHÔNG được sửa test.

BẠN ĐƯỢC TRA KHO MÃ. Mỗi lượt viết ĐÚNG MỘT lệnh ở dòng đầu:

  TIM <chữ cần tìm>          -> tìm chữ đó trong cả kho, trả về tệp:dòng
  MO <tệp> <tên hàm>         -> xem toàn văn một hàm ở tệp khác
  VA                         -> nộp bài, xuống dòng rồi viết mã

Khi nộp bài (VA): viết lại TOÀN VĂN hàm cần sửa, từ dòng `def` tới hết thân
hàm. Chỉ mã Python, không giải thích, không khối markdown.
- Chỉ viết hàm nào bạn thực sự sửa, không chép lại cả tệp.
- Hàm chưa có thì cứ viết mới, nó sẽ được thêm vào tệp.
"""

# "Còn N lượt" phải nằm CUỐI lời nhắc, không phải đầu. Vòng công cụ gửi lại cả
# lời nhắc mỗi lượt; llama.cpp chỉ nhớ được phần ĐẦU giống hệt lượt trước. Đặt
# con số đổi-mỗi-lượt lên đầu là phá sạch bộ nhớ đệm — mỗi lượt lại nạp lại
# 6.000 token từ số không, và cái vòng công cụ đắt gấp bảy lần vòng một phát.
DUOI = "\nBạn còn {con} lượt tra. Hết lượt thì buộc phải VA.\n=== TRẢ LỜI ===\n"


def _env(tep: Path) -> dict:
    kv = {}
    for l in tep.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


def goi_model(model: str, p: str) -> str:
    if BACKEND == "cloud":
        # Bảng phân loại 37% dựng từ 29 lượt TRƯỢT CỦA GEMINI, nên phép đo
        # "có công cụ thì khác gì" phải chạy trên CHÍNH GEMINI. Đo model khác
        # là trả lời một câu khác. Đo 18/08: 22,4 giây/lượt và không chiếm
        # byte RAM nào của máy — cục bộ là 973,5 giây và chiếm trọn máy.
        e = _env(Path("D:/AURA_OS_v2/.env"))
        b = json.dumps({"model": e.get("OPENAI_MODEL", "gemini-2.5-flash"),
                        "messages": [{"role": "user", "content": p}],
                        "temperature": 0.2}).encode()
        for lan in range(4):
            try:
                r = urllib.request.Request(
                    e["OPENAI_BASE_URL"].rstrip("/") + "/chat/completions",
                    data=b, method="POST",
                    headers={"Content-Type": "application/json",
                             "Authorization": "Bearer " + e["OPENAI_API_KEY"]})
                with urllib.request.urlopen(r, timeout=300) as x:
                    k = json.loads(x.read().decode())
                return (k["choices"][0]["message"].get("content") or "").strip()
            except urllib.error.HTTPError as ex:
                if ex.code in (429, 500, 502, 503) and lan < 3:
                    cho = 20 * (lan + 1)          # tầng miễn phí có hạn mức phút
                    print(" [HTTP " + str(ex.code) + ", cho " + str(cho) + "s]",
                          end="", flush=True)
                    time.sleep(cho)
                    continue
                raise
        return ""

    if BACKEND == "llamacpp":
        # cache_prompt: giữ lại phần đầu giống lượt trước, chỉ nạp phần đuôi mới.
        # Đo 17/08 trên cùng máy: nạp prompt Ollama 18-19 t/s, llama.cpp 76,0 t/s.
        # Vòng công cụ nạp ~6.000 token MỖI LƯỢT, nên đây là khác biệt giữa
        # 5,5 phút và 1,3 phút cho mỗi lượt — trước cả phần bộ nhớ đệm tiết kiệm.
        b = json.dumps({"prompt": p, "n_predict": 1200, "temperature": 0.2,
                        "seed": 42, "cache_prompt": True}).encode()
        r = urllib.request.Request(LLAMA + "/completion", data=b,
                                   headers={"Content-Type": "application/json"},
                                   method="POST")
        with urllib.request.urlopen(r, timeout=1800) as x:
            return (json.loads(x.read().decode()).get("content") or "").strip()

    b = json.dumps({"model": model, "prompt": p, "stream": False, "think": False,
                    "options": {"seed": 42, "temperature": 0.2, "num_predict": 1200,
                                "num_ctx": 16384}}).encode()
    r = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                               headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=1800) as x:
        return (json.loads(x.read().decode()).get("response") or "").strip()


def cong_cu_tim(tam: Path, mau: str) -> str:
    k = subprocess.run(["git", "-C", str(tam), "grep", "-n", "-F", mau, "--", "*.py"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = [l for l in k.stdout.splitlines() if not l.startswith("tests/")][:25]
    return "\n".join(d) if d else "(khong tim thay '" + mau + "' trong kho)"


def cong_cu_mo(tam: Path, tep: str, ten: str) -> str:
    f = tam / tep
    if not f.is_file():
        return "(khong co tep " + tep + ")"
    ma = f.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^(\s*)(?:async\s+)?(?:def|class)\s+" + re.escape(ten) + r"\b", ma, re.M)
    if not m:
        return "(tep " + tep + " khong co '" + ten + "')"
    dong = ma.splitlines()
    d0 = ma[:m.start()].count("\n")
    thut = len(m.group(1))
    het = len(dong)
    for i in range(d0 + 1, len(dong)):
        l = dong[i]
        if l.strip() and (len(l) - len(l.lstrip())) <= thut:
            het = i
            break
    return "\n".join(dong[d0:het])[:4000]


def mot_de(d: dict, nhat_ky: Path) -> dict:
    goc = Path(tempfile.mkdtemp())
    ghi = nhat_ky.open("w", encoding="utf-8")

    def ghi_lai(nhan: str, noi_dung: str) -> None:
        ghi.write("\n" + "=" * 70 + "\n" + nhan + "\n" + "=" * 70 + "\n" + noi_dung + "\n")
        ghi.flush()

    try:
        tam = goc / "de"
        subprocess.run(["git", "clone", "-q", d["repo"], str(tam)], check=True,
                       capture_output=True)
        for a in (["checkout", "-q", d["sha"]],
                  ["checkout", "-q", d["sha"] + "~1", "--", d["nguon"]]):
            subprocess.run(["git", "-C", str(tam), *a], capture_output=True, check=True)

        # venv CỦA CHÍNH REPO ĐỀ, không phải venv đang chạy máy đo. Đề lấy từ
        # D:\AURA_OS_v2 nên phải chạy pytest bằng python của v2 — dùng nhầm
        # venv v3 thì mọi đề đỏ vì thiếu gói, và đọc thành "model trượt".
        py = str(Path(d["repo"]) / "venv" / "Scripts" / "python.exe")
        f_nguon = tam / d["nguon"]
        ma = f_nguon.read_text(encoding="utf-8", errors="replace")
        test_day = "\n\n".join((tam / t).read_text(encoding="utf-8", errors="replace")
                               for t in d["test"])
        vung = D.chon_vung(ma, test_day)
        test = D.cat_dong(test_day, D.TRAN_TEST)
        _, loi, _ = D.pytest_(py, tam, d["test"], 300)
        nen = set(d.get("do_nen") or ())

        # Phần TĨNH — giống hệt mọi lượt, để llama.cpp nhớ được và khỏi nạp lại.
        dau_bai = (HUONG_DAN.format(ten=d["nguon"])
                   + "\n=== MÃ NGUỒN (" + d["nguon"] + ") ===\n" + vung + "\n"
                   + "=== TỆP TEST ===\n" + test + "\n=== TEST BÁO LỖI ===\n" + loi + "\n")

        lich_su, so_goi, tong_giay = "", 0, 0.0
        while True:
            con = TRAN_CONG_CU - so_goi
            p = dau_bai + lich_su + DUOI.format(con=max(con, 0))
            if so_goi == 0:
                ghi_lai("LOI NHAC BAN DAU", p)
            t0 = time.monotonic()
            ra = goi_model(MODEL, p)
            tong_giay += time.monotonic() - t0
            ghi_lai("MODEL TRA LOI (luot " + str(so_goi + 1) + ")", ra)

            dau = ra.strip().splitlines()[0].strip() if ra.strip() else ""
            if con > 0 and dau.upper().startswith("TIM "):
                mau = dau[4:].strip()
                kq = cong_cu_tim(tam, mau)
                ghi_lai("CONG CU TIM '" + mau + "' TRA VE", kq)
                lich_su += "\n=== BẠN ĐÃ TÌM: " + mau + " ===\n" + kq + "\n"
                so_goi += 1
                continue
            if con > 0 and dau.upper().startswith("MO "):
                pt = dau[3:].split(None, 1)
                kq = cong_cu_mo(tam, pt[0], pt[1].strip()) if len(pt) == 2 else "(thieu ten ham)"
                ghi_lai("CONG CU MO " + dau[3:] + " TRA VE", kq)
                lich_su += "\n=== BẠN ĐÃ MỞ: " + dau[3:] + " ===\n" + kq + "\n"
                so_goi += 1
                continue

            # Không phải lệnh tra -> coi là nộp bài. Bỏ dòng VA nếu có.
            bai = re.sub(r"^\s*VA\s*\n", "", ra, count=1, flags=re.I)
            sua, hong = D.ap_ham(ma, bai)
            if hong:
                ghi_lai("KET QUA", "SAI DINH DANG: " + hong)
                return {"trang_thai": "sai_dinh_dang", "vi_sao": hong,
                        "so_goi_cong_cu": so_goi, "giay": round(tong_giay, 1)}
            f_nguon.write_text(sua, encoding="utf-8")
            m2, bao, _ = D.pytest_(py, tam, d["test"], 300)
            them: set[str] = set()
            if m2 == 0:
                _, ca_bo, do = D.pytest_(py, tam, ["tests"], 200)
                them = do - nen
                if them:
                    bao = ca_bo
            ok = (m2 == 0 and not them)
            ghi_lai("KET QUA", ("DAT" if ok else "TRUOT") + "\nma_thoat=" + str(m2)
                    + "\nlam_do_them=" + str(sorted(them)[:5]) + "\n\n" + bao[-2000:])
            return {"trang_thai": "dat" if ok else "truot", "so_goi_cong_cu": so_goi,
                    "giay": round(tong_giay, 1), "lam_do_them": sorted(them)[:5]}
    except Exception as e:                                       # noqa: BLE001
        ghi_lai("KET QUA", "KHONG DO DUOC: " + type(e).__name__ + ": " + str(e))
        return {"trang_thai": "khong_do_duoc", "vi_sao": type(e).__name__ + ": " + str(e)[:80]}
    finally:
        ghi.close()
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    phan = {r["de"]: r["nhan"] for r in
            json.loads(Path("D:/alpha_bench/doc_tay_v2.json").read_text("utf-8"))}
    de = {d["sha"][:8] + ":" + d["nguon"]: d
          for d in json.loads(Path("D:/alpha_bench/de_sach.json").read_text("utf-8"))}
    chon = [k for k, n in phan.items() if n == NHOM][:SO_DE]
    SO_NONG.mkdir(parents=True, exist_ok=True)
    cu = json.loads(SO.read_text("utf-8")) if SO.is_file() else {}
    cot = (MODEL if BACKEND != "cloud" else "gemini-2.5-flash") + "#tra_kho#" + NHOM
    cu.setdefault(cot, {})

    print("\n  nhom=" + NHOM + "  model=" + MODEL + "  " + str(len(chon))
          + " de  tran cong cu=" + str(TRAN_CONG_CU) + "\n")
    for i, k in enumerate(chon, 1):
        # khong_do_duoc KHONG duoc cache: hong may do ma dong bang thanh du lieu.
        if cu[cot].get(k, {}).get("trang_thai") in ("dat", "truot", "sai_dinh_dang"):
            print("  [" + str(i) + "/" + str(len(chon)) + "] " + k + "  (da co, bo qua)")
            continue
        lg = SO_NONG / (k.replace(":", "__").replace("/", "_") + ".log")
        print("  [" + str(i) + "/" + str(len(chon)) + "] " + k + " ...", end="", flush=True)
        r = mot_de(de[k], lg)
        cu[cot][k] = r
        SO.write_text(json.dumps(cu, ensure_ascii=False, indent=1), encoding="utf-8")
        print(" " + r["trang_thai"] + "  (tra " + str(r.get("so_goi_cong_cu", "?"))
              + " lan, " + str(r.get("giay", "?")) + "s)")

    xong = cu[cot]
    dat = sum(1 for v in xong.values() if v.get("trang_thai") == "dat")
    print("\n  ===== " + NHOM + ": " + str(dat) + "/" + str(len(xong)) + " dat =====")
    print("  " + str(dict(collections.Counter(v.get("trang_thai") for v in xong.values()))))
    tra = [v.get("so_goi_cong_cu", 0) for v in xong.values() if "so_goi_cong_cu" in v]
    if tra:
        print("  so lan tra kho: trung binh " + format(sum(tra) / len(tra), ".1f")
              + ", khong tra lan nao: " + str(sum(1 for t in tra if t == 0)) + "/" + str(len(tra)))
    print("\n  so nong tung de -> " + str(SO_NONG))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
