# -*- coding: utf-8 -*-
"""Needle 2 (45M) so với qwen3.5:4b trên CÙNG một việc: chọn đúng hàm từ khay.

VÌ SAO ĐO KIỂU NÀY — 20/08/2026.

Bộ chấm cũ (`do_khay_loc.py`) bắt model VIẾT MÃ rồi kiểm mã ấy có gọi đúng hàm
kho không; qwen3.5:4b đạt 20/28. Needle 45M không viết mã — nó gọi tool. Đem
20/28 ra so với "chọn tool" là so hai việc khác nhau, đúng cái bẫy `CLAUDE.md`
mục 4 gọi tên: gắn theo thứ tự là giả định, không phải phép đo.

Nên ở đây đo CẢ HAI trên đúng một việc hẹp hơn: **cho mô tả việc, chọn đúng một
hàm trong khay 8 thẻ**. Số ra không so được với 20/28 cũ, và tệp này không giả
vờ là so được.

BA CON SỐ, không gộp:
    trần khay   hàm đúng có nằm trong khay 8 không (bộ lọc quyết định, không
                model nào vượt được trần này)
    Needle      chọn đúng / 28
    qwen        chọn đúng / 28

    .venv-needle\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_needle_khay.py --needle
    venv\\Scripts\\python.exe        -X utf8 experiments\\evidence_sprint\\do_needle_khay.py --qwen
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(GOC))

from core.khay_the import loc_khay, sinh_khay          # noqa: E402

DE = GOC / "experiments" / "evidence_sprint" / "de_khay.json"
SO = GOC / "data" / "evidence_sprint" / "needle_vs_qwen.json"
GIU = 8                        # cỡ khay đã chốt ở lượt trước
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:4b"


def _nap_de():
    d = json.loads(DE.read_text(encoding="utf-8"))
    return [(x[0], x[1], x[2]) for x in d["de"]]


def _khay_cho(khay, viec):
    return loc_khay(khay, viec, GIU)


def _tao_ham(ten: str, mo_ta: str):
    """Dựng một hàm thật mang tên và tài liệu của thẻ, để Needle đăng ký tool.

    Không dùng `lambda`: Needle đọc `__name__` và `__doc__` để dựng lược đồ, mà
    lambda thì tên là `<lambda>` hết.
    """
    def f() -> str:
        return ten
    f.__name__ = ten
    f.__qualname__ = ten
    f.__doc__ = mo_ta or ten
    return f


# ------------------------------------------------------------------ Needle
def chay_needle(de, khay):
    import needle
    ra = []
    t_nap = time.time()
    _ = needle.Needle(tools=[_tao_ham("thu", "thử")])   # nạp trọng số một lần
    t_nap = time.time() - t_nap
    for ma, viec, can in de:
        k = _khay_cho(khay, viec)
        ten_khay = [t.ten for t in k]
        cong_cu = [_tao_ham(t.ten, t.mo_ta or t.tai_lieu[:120]) for t in k]
        t0 = time.time()
        try:
            ag = needle.Needle(tools=cong_cu)
            kq = ag.run(viec)
            chon = (kq.get("results") or [None])[0] if isinstance(kq, dict) else None
            tin = kq.get("confidence") if isinstance(kq, dict) else None
            ram = kq.get("peak_ram_mb") if isinstance(kq, dict) else None
            loi = None
        except Exception as e:
            chon, tin, ram, loi = None, None, None, "%s: %s" % (type(e).__name__, e)
        ra.append({
            "de": ma, "can": can, "chon": chon, "dat": chon == can,
            "trong_khay": can in ten_khay, "tin_cay": tin, "ram_mb": ram,
            "giay": round(time.time() - t0, 2), "loi": loi,
            "khay": ten_khay,
        })
    return ra, round(t_nap, 1)


# -------------------------------------------------------------------- qwen
def chay_qwen(de, khay):
    ra = []
    for ma, viec, can in de:
        k = _khay_cho(khay, viec)
        ten_khay = [t.ten for t in k]
        # Cùng thông tin Needle nhận: tên hàm + dòng mô tả. Không thêm gợi ý.
        bang = "\n".join("- %s: %s" % (t.ten, (t.mo_ta or "")[:120]) for t in k)
        p = ("Dưới đây là các hàm có sẵn:\n%s\n\n"
             "VIỆC CẦN LÀM: %s\n\n"
             "Trả lời DUY NHẤT tên một hàm trong danh sách trên, không giải "
             "thích, không dấu ngoặc." % (bang, viec))
        b = {"model": MODEL, "prompt": p, "stream": False, "think": False,
             "keep_alive": "5m",
             "options": {"seed": 42, "temperature": 0.2, "num_predict": 24,
                         "num_ctx": 4096}}
        t0 = time.time()
        try:
            rq = urllib.request.Request(
                OLLAMA, data=json.dumps(b).encode(), method="POST",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(rq, timeout=300) as x:
                d = json.loads(x.read().decode())
            th = (d.get("response") or "").strip().strip("`'\"() \n")
            # Chấm bằng ĐỐI CHIẾU VỚI KHAY, không dò chuỗi con: `"ai"` từng khớp
            # bên trong `"thứ hai"` và làm hỏng năm phép đo trong một ngày.
            chon = th if th in ten_khay else next(
                (t for t in ten_khay if t == th.split()[0]), None) if th else None
            loi = None
        except Exception as e:
            chon, loi = None, "%s: %s" % (type(e).__name__, e)
        ra.append({
            "de": ma, "can": can, "chon": chon, "dat": chon == can,
            "trong_khay": can in ten_khay, "tin_cay": None, "ram_mb": None,
            "giay": round(time.time() - t0, 2), "loi": loi,
            "khay": ten_khay,
        })
    return ra, 0.0


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    bo = "needle" if "--needle" in sys.argv else (
        "qwen" if "--qwen" in sys.argv else "")
    if not bo:
        print("KHÔNG ĐO ĐƯỢC: thiếu cờ --needle hoặc --qwen")
        return 2
    de = _nap_de()
    khay = sinh_khay(GOC)
    if not de or not khay:
        print("KHÔNG ĐO ĐƯỢC: thiếu đề hoặc khay rỗng")
        return 2

    try:
        ra, t_nap = (chay_needle if bo == "needle" else chay_qwen)(de, khay)
    except ImportError as e:
        print("KHÔNG ĐO ĐƯỢC: %r" % (e,))
        return 2

    dat = sum(1 for x in ra if x["dat"])
    tran = sum(1 for x in ra if x["trong_khay"])
    hong = sum(1 for x in ra if x["loi"])
    tong_giay = round(sum(x["giay"] for x in ra), 1)

    SO.parent.mkdir(parents=True, exist_ok=True)
    cu = {}
    if SO.is_file():
        cu = json.loads(SO.read_text(encoding="utf-8"))
    cu[bo] = {"dat": dat, "tran_khay": tran, "tong": len(ra), "hong": hong,
              "giay_nap": t_nap, "tong_giay": tong_giay, "giu": GIU,
              "luc": time.strftime("%Y-%m-%dT%H:%M:%S"), "chi_tiet": ra}
    SO.write_text(json.dumps(cu, ensure_ascii=False, sort_keys=True, indent=1),
                  encoding="utf-8")

    print("=" * 62)
    print("  %s — chọn đúng hàm trong khay %d thẻ" % (bo.upper(), GIU))
    print("=" * 62)
    print("  TRẦN của khay (hàm đúng có mặt): %d/%d" % (tran, len(ra)))
    print("  chọn đúng                      : %d/%d" % (dat, len(ra)))
    if tran:
        print("  chọn đúng / khi CÓ mặt         : %d/%d"
              % (sum(1 for x in ra if x["dat"] and x["trong_khay"]), tran))
    print("  lỗi khi chạy                   : %d" % hong)
    print("  thời gian                      : nạp %.1fs + chạy %.1fs"
          % (t_nap, tong_giay))
    tc = [x["tin_cay"] for x in ra if x["tin_cay"] is not None]
    if tc:
        d2 = [x["tin_cay"] for x in ra if x["dat"] and x["tin_cay"] is not None]
        s2 = [x["tin_cay"] for x in ra if not x["dat"] and x["tin_cay"] is not None]
        print("  tin cậy trung bình             : %.3f" % (sum(tc) / len(tc)))
        if d2:
            print("    khi ĐÚNG                     : %.3f (n=%d)" % (sum(d2) / len(d2), len(d2)))
        if s2:
            print("    khi SAI                      : %.3f (n=%d)" % (sum(s2) / len(s2), len(s2)))
    print()
    print("  10 đề đầu:")
    for x in ra[:10]:
        print("    %-28s cần %-24s chọn %-24s %s%s"
              % (x["de"][:28], x["can"][:24], str(x["chon"])[:24],
                 "ĐÚNG" if x["dat"] else "sai",
                 "" if x["trong_khay"] else "  (KHÔNG có trong khay)"))
    print()
    print("  sổ: %s" % SO)
    return 0 if dat == len(ra) else 1


if __name__ == "__main__":
    raise SystemExit(main())
