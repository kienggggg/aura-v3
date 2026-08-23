"""Đo xem mã THẬT có hình dạng ba tầng nối tiếp như "Lớp Kính Địa Tầng" giả định.

21/08/2026. Kế hoạch của Antigravity vẽ mã như mặt cắt địa chất: một tầng KHỞI
TẠO nằm dưới, tầng BIẾN ĐỔI ở giữa, tầng KẾT XUẤT trên cùng. Ẩn dụ ấy chở theo
một mệnh đề kiểm được: tầng địa chất KHÔNG quay lại — không ai đào thấy trầm
tích, rồi biến chất, rồi lại trầm tích.

Chạy trên 25 tệp `core/` + `interface/`:

    hàm 1-5 thẻ    40/61 = 66% ra đúng hình
    hàm 6-15 thẻ    0/54 =  0%
    hàm >15 thẻ     0/25 =  0%

Mặt cắt thật của `doc_so_phien.py`: KBXKBXKBKBKBXBXKBKX — vằn, không phải lớp.

Ba bài nghiệm thu tay trong kế hoạch (cộng hai số · chẵn lẻ · tổng 1..N) đều
nằm trong nhóm 1-5 thẻ, nên bản nghiệm thu ấy KHÔNG THỂ TRƯỢT. Thêm bài cỡ
6-15 thẻ trước khi chấm.
"""
from __future__ import annotations

import collections
import io
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

from core.the_cst import doc_tep_py_sang_cay_the       # noqa: E402

# Đúng luật phân tầng trong kế hoạch, không thêm bớt.
TANG = {"gan": "K", "pheptinh": "B", "neu": "B", "nguoc_lai": "B",
        "lap_moi": "B", "lap_khi": "B", "in_ra": "X", "tra_ve": "X"}

# Hình được coi là "ba tầng nối tiếp": đi một chiều K -> B -> X, không quay lại.
HINH_DAT = {"KB", "KX", "BX", "KBX"}


def phang(ns):
    r = []
    for n in ns:
        r.append(n)
        r += phang(n.than)
    return r


def mat_cat(the_trong_ham) -> str:
    """Chuỗi dải theo thứ tự xuất hiện, đã gộp các thẻ liền nhau cùng tầng."""
    chuoi = [TANG[c.ma] for c in the_trong_ham if c.ma in TANG]
    if not chuoi:
        return ""
    dai = [chuoi[0]]
    for t in chuoi[1:]:
        if t != dai[-1]:
            dai.append(t)
    return "".join(dai)


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    theo_co: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    vi_du: list[tuple[str, str, str]] = []
    dat = tong = 0

    for thu_muc in ("core", "interface"):
        for p in sorted((GOC / thu_muc).glob("*.py")):
            try:
                rec = doc_tep_py_sang_cay_the(p)
            except Exception:                                # noqa: BLE001
                continue
            for n in phang(rec.tree):
                if n.ma != "ham":
                    continue
                trong = phang(n.than)
                s = mat_cat(trong)
                if len(s) < 2:
                    continue
                n_the = sum(1 for c in trong if c.ma in TANG)
                co = ("1-5 thẻ" if n_the <= 5
                      else "6-15 thẻ" if n_the <= 15 else ">15 thẻ")
                ok = s in HINH_DAT
                tong += 1
                theo_co[co][1] += 1
                if ok:
                    dat += 1
                    theo_co[co][0] += 1
                elif len(s) >= 6 and len(vi_du) < 5:
                    vi_du.append((p.name, n.o.get("ten_ham", "?"), s))

    print("HÌNH DẠNG ĐỊA TẦNG CỦA MÃ THẬT")
    print("  luật phân tầng: K=khởi tạo (gán) · B=biến đổi (nếu/lặp/phép tính)"
          " · X=kết xuất (in ra/trả về)")
    print('  "đạt" = đi một chiều K→B→X, không quay lại')
    print()
    print("  %-12s %14s" % ("cỡ hàm", "ra đúng hình"))
    for co in ("1-5 thẻ", "6-15 thẻ", ">15 thẻ"):
        d, t = theo_co[co]
        if t:
            print("  %-12s %6d/%-4d %3.0f%%" % (co, d, t, 100 * d / t))
    print("  %-12s %6d/%-4d %3.0f%%" % ("TỔNG", dat, tong,
                                        100 * dat / max(tong, 1)))
    print()
    print("  mặt cắt THẬT của vài hàm:")
    for ten_tep, ten_ham, s in vi_du:
        print("     %-20s %-22s %s" % (ten_tep[:20], ten_ham[:22], s[:44]))
    print()
    # Cửa cứng: 0 = hình ba tầng đứng vững, 1 = đo được mà không đạt.
    if tong == 0:
        print("  KHÔNG ĐO ĐƯỢC — không đọc được hàm nào")
        return 2
    if 100 * dat / tong >= 80:
        print("  ĐẠT — mã thật đúng là ba tầng nối tiếp")
        return 0
    print("  ĐO ĐƯỢC MÀ KHÔNG ĐẠT — %.0f%% hàm ra đúng hình, phần còn lại là VẰN"
          % (100 * dat / tong))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
