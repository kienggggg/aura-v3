# -*- coding: utf-8 -*-
"""Đo xem 7 phòng nội bộ có thật sự LÀM gì không, thay vì tin chuỗi tự khai.

VÌ SAO CÓ TỆP NÀY. 02/09/2026, `interface/noi_bo_api.py` khai bảy phòng, sáu
phòng `trang_thai: "ONLINE"`, mỗi phòng bốn công cụ — **tất cả đều là chuỗi gõ
tay**. Không một dòng mã nào tính ra chữ "ONLINE" ấy. Cùng lúc, `chat.html`
khai ngược lại: Delta và Omega ở đó là `san: false`.

Đó là hình dạng đã giết AURA v2, ghi ở đầu `CLAUDE.md`: *339 tệp, 33 cờ bật-tắt
mà 29 cái đang TẮT*. Ở đây là 7 phòng, 6 cái tự khai ONLINE, 0 cái phải chứng
minh.

CÁCH ĐO. Không đọc mã rồi suy — đi từ **cửa vào**, gọi đúng đường mà giao diện
gọi (`POST /api/dispatch`), rồi hỏi một câu duy nhất:

    **Sau lượt gọi ấy, trên đĩa có gì mới không?**

Đó là luật Chương I của `KY_LUAT_THUC_THI.md`: *"Bằng chứng trên đĩa là chân lý
duy nhất."* Một phòng trả về đoạn văn đẹp mà không để lại byte nào thì nó chưa
làm gì cả.

HAI CHỖ PHẢI TRỪ RA, kẻo đo nhầm thành công:

1. `data/omega/so_cai.jsonl` — bộ điều phối ghi một dòng cho **mọi** phòng, kể
   cả phòng không làm gì. Tính nó vào thì cả bảy phòng đều "đạt".
2. `__pycache__` — Python sinh ra khi nạp mô-đun, không phải sản phẩm của phòng.

BA TRẠNG THÁI, tách rời, không được gộp thành hai:

    CHAY_THAT       gọi được, và để lại bằng chứng trên đĩa
    CHUA_CHAY_THAT  gọi được, trả về 200, nhưng 0 byte mới
    KHONG_DO_DUOC   không gọi được (máy chủ không lên, đường lỗi, hết giờ)

Trạng thái thứ ba là trạng thái hay bị nuốt nhất. Gộp nó vào "không đạt" thì
"chưa đo được" đội lốt "đã đo, hỏng".

CHẠY:

    venv\\Scripts\\python.exe tools/do_trang_thai_phong.py

Nó ghi kết quả ra `data/noi_bo/trang_thai_phong.json`. `api_danh_sach_phong`
đọc tệp ấy; không có tệp thì mọi phòng hiện `CHUA_DO` — chứ không hiện ONLINE.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
# Chạy được cả khi gọi thẳng `python tools/do_trang_thai_phong.py` — lúc ấy
# thư mục của TỆP nằm trên sys.path, không phải gốc kho.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SO_CAI = ROOT / "data" / "omega" / "so_cai.jsonl"
RA = ROOT / "data" / "noi_bo" / "trang_thai_phong.json"
CONG = 8791
TRAN_LEN_GIAY = 40.0
# Trần cho MỘT phòng. Nới 30 -> 360 ngày 03/09/2026.
#
# Phòng `aura` nay gọi model thật (`core/viet_truyen.py`) và đo được 85–273
# giây, tuỳ nó phải sinh lại mấy lần. Để nguyên 30 giây thì máy đo báo
# `KHONG_DO_DUOC` cho một phòng THẬT SỰ CHẠY — tức trần của nhạc cụ làm sai kết
# luận về thứ được đo, không phải phòng ấy hỏng.
#
# 360 = 273 (lượt chậm nhất đo được) + biên. Không đặt bằng trần lý thuyết của
# `viet_kich_ban` (3 × 300 = 900 s) vì chờ 15 phút cho một lượt đo thì máy đo
# không dùng được nữa — nếu chạm 360 s thì đó là tin đáng biết, không phải tin
# nên nuốt.
TRAN_MOT_PHONG_GIAY = 360.0

# Câu yêu cầu dùng cho mọi phòng. Cố ý VÔ HẠI và giống nhau, để khác biệt giữa
# các phòng là do PHÒNG, không do đề bài.
YEU_CAU = "kiem tra tinh trang phong"


def _anh_chup(goc: Path) -> dict[str, tuple[int, float]]:
    """Ảnh chụp cây tệp: đường dẫn -> (kích thước, mtime).

    Bỏ những chỗ đổi vì lý do không liên quan tới phòng.
    """
    ra: dict[str, tuple[int, float]] = {}
    for p in goc.rglob("*"):
        if not p.is_file():
            continue
        s = p.as_posix()
        if "/__pycache__/" in s or "/.git/" in s or "/venv/" in s:
            continue
        if p == SO_CAI:
            continue  # bộ điều phối ghi cho MỌI phòng — không phải công của phòng
        try:
            st = p.stat()
        except OSError:
            continue
        ra[s] = (st.st_size, st.st_mtime)
    return ra


def _khac(truoc: dict, sau: dict) -> list[str]:
    moi = [k for k in sau if k not in truoc]
    doi = [k for k in sau if k in truoc and sau[k] != truoc[k]]
    return sorted(moi + doi)


def do_mot_phong(client: httpx.Client, goc: str, phong_id: str) -> dict:
    truoc = _anh_chup(ROOT / "data")
    truoc_goc = _anh_chup(ROOT / "interface")
    t0 = time.perf_counter()
    try:
        r = client.post(f"{goc}/api/dispatch",
                        json={"phong_id": phong_id, "yeu_cau": YEU_CAU},
                        timeout=TRAN_MOT_PHONG_GIAY)
    except Exception as loi:  # noqa: BLE001 — câu này đi thẳng vào sổ
        return {"phong_id": phong_id, "trang_thai": "KHONG_DO_DUOC",
                "vi_sao": f"{type(loi).__name__}: {loi}", "ms": None,
                "tep_moi": [], "artifacts_khai": [], "artifacts_co_that": []}
    ms = round((time.perf_counter() - t0) * 1000, 1)
    if r.status_code != 200:
        return {"phong_id": phong_id, "trang_thai": "KHONG_DO_DUOC",
                "vi_sao": f"HTTP {r.status_code}", "ms": ms,
                "tep_moi": [], "artifacts_khai": [], "artifacts_co_that": []}

    j = r.json()
    khai = [a.get("name", "?") for a in j.get("artifacts", [])]
    # Ngủ một nhịp: tệp có thể được ghi xong sau khi phản hồi đã trả về.
    time.sleep(0.4)
    tep_moi = _khac(truoc, _anh_chup(ROOT / "data")) + \
        _khac(truoc_goc, _anh_chup(ROOT / "interface"))

    # Tệp mà phòng KHAI là đã tạo — có thật trên đĩa ở đâu đó không?
    co_that = []
    for ten in khai:
        if any(p.name == ten for p in ROOT.rglob(ten) if p.is_file()):
            co_that.append(ten)

    dat = bool(tep_moi) or (khai and len(co_that) == len(khai))
    return {"phong_id": phong_id,
            "trang_thai": "CHAY_THAT" if dat else "CHUA_CHAY_THAT",
            "vi_sao": "" if dat else "trả 200 nhưng không để lại byte nào trên đĩa",
            "ms": ms, "tep_moi": tep_moi,
            "artifacts_khai": khai, "artifacts_co_that": co_that}


def _in(chu: str = "") -> None:
    """In an toàn — console Windows nuốt dấu thì ghi thẳng bytes UTF-8."""
    try:
        print(chu)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(chu.encode("utf-8") + b"\n")
        sys.stdout.flush()


def main() -> int:
    from interface.noi_bo_api import DANH_MUC_PHONG

    tien_trinh = subprocess.Popen(
        [sys.executable, "-m", "interface.noi_bo_app", "--port", str(CONG)],
        cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace")
    goc = f"http://127.0.0.1:{CONG}"
    try:
        han = time.time() + TRAN_LEN_GIAY
        len_duoc = False
        with httpx.Client() as c:
            while time.time() < han:
                try:
                    if c.get(f"{goc}/api/rooms", timeout=2).status_code == 200:
                        len_duoc = True
                        break
                except Exception:
                    time.sleep(0.15)
            if not len_duoc:
                _in(f"  KHÔNG ĐO ĐƯỢC: máy chủ nội bộ không lên trong {TRAN_LEN_GIAY:.0f}s")
                return 2

            ket = [do_mot_phong(c, goc, p["id"]) for p in DANH_MUC_PHONG]
    finally:
        tien_trinh.kill()
        try:
            tien_trinh.wait(timeout=10)
        except Exception:
            pass

    _in(f"  {'phòng':<8}{'trạng thái':<17}{'ms':>7}  bằng chứng trên đĩa")
    _in("  " + "-" * 68)
    for k in ket:
        bc = ", ".join(k["tep_moi"][:2]) if k["tep_moi"] else "(không có)"
        if k["artifacts_khai"]:
            bc += f"  · khai {len(k['artifacts_khai'])} tệp, có thật {len(k['artifacts_co_that'])}"
        ms = f"{k['ms']:.0f}" if k["ms"] is not None else "-"
        _in(f"  {k['phong_id']:<8}{k['trang_thai']:<17}{ms:>7}  {bc}")

    dem = {t: sum(1 for k in ket if k["trang_thai"] == t)
           for t in ("CHAY_THAT", "CHUA_CHAY_THAT", "KHONG_DO_DUOC")}
    _in("")
    _in(f"  chạy thật {dem['CHAY_THAT']} · chưa chạy thật {dem['CHUA_CHAY_THAT']}"
        f" · không đo được {dem['KHONG_DO_DUOC']}   (tổng {len(ket)})")

    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps(
        {"_vi_sao": "Đo bằng cách gọi POST /api/dispatch rồi soi đĩa. "
                    "Xem tools/do_trang_thai_phong.py.",
         "do_luc": datetime.now().isoformat(timespec="seconds"),
         "phong": ket}, ensure_ascii=False, indent=1), encoding="utf-8")
    _in(f"  sổ: {RA}")
    return 0 if dem["KHONG_DO_DUOC"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
