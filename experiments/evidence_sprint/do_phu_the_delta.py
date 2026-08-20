# -*- coding: utf-8 -*-
"""CHẶNG B — thẻ có tả nổi chỗ Delta phải sửa không. Cửa chặn, không qua thì dừng.

VÌ SAO — 20/08/2026.

Kế hoạch nối app THẺ vào Delta đứng trên một giả định chưa đo: rằng chỗ cần sửa
nằm trong **thẻ thật**. Nếu nó rơi vào `ma_tho` thì "sửa qua thẻ" chỉ là "sửa
chữ" — model vẫn gõ văn bản tự do, và cả hướng đi mất nghĩa.

MỘT CHI TIẾT ĐỔI CẢ PHÉP ĐO: `dung_de_loi.dot_bien` trả về `ast.unparse(...)`,
và `do_sua_loi.py:130` ghi thẳng bản ấy ra đĩa. Nên tệp model nhìn thấy **không
phải tệp gốc** — nó đã bị chuẩn hoá, sạch chú thích, biểu thức duỗi thẳng. Đo
độ phủ trên tệp gốc là đo nhầm tệp.

Nên đo cả hai, để thấy chênh:
    GỐC       tệp trong kho, còn chú thích và biểu thức nhiều dòng
    ĐÃ GIEO   tệp `ast.unparse` + đột biến, đúng thứ Delta mở ra

NGƯỠNG ĐẶT TRƯỚC (kế hoạch mục 3, chặng B):
    >= 60% dòng nằm trong thẻ THẬT      -> đi tiếp sang chặng C
    40..59%                             -> đo được mà không đạt, ghi sổ rồi cân
    <  40%                              -> DỪNG, Delta sẽ chỉ sửa mã thô

Và một con số sắc hơn tỉ lệ trung bình: **chỗ đột biến có nằm trong thẻ thật
không**, tính trên từng đề. Trung bình cao mà đúng chỗ cần sửa lại là `ma_tho`
thì vẫn hỏng.

    venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_phu_the_delta.py
"""
from __future__ import annotations

import ast
import collections
import io
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.the_cst import doc_chuoi_py_sang_cay_the        # noqa: E402
from dung_de_loi import dot_bien                          # noqa: E402

DE = GOC / "experiments" / "evidence_sprint" / "de_loi.json"
RA = GOC / "data" / "evidence_sprint" / "phu_the_delta.json"

# Ngưỡng viết ở đây, TRƯỚC khi chạy. Đổi ngưỡng sau khi thấy số là gian lận.
NGUONG_DI_TIEP = 60.0
NGUONG_DUNG = 40.0


def _phang(ns):
    ra = []
    for n in ns:
        ra.append(n)
        ra += _phang(n.than)
    return ra


def _phu(nguon: str):
    """Trả (số dòng, tập dòng nằm trong thẻ THẬT, bản đồ dòng -> mã thẻ)."""
    rec = doc_chuoi_py_sang_cay_the(nguon)
    that: set[int] = set()
    ban_do: dict[int, str] = {}
    for n in _phang(rec.tree):
        if n.line_start is None:
            continue
        vung = range(n.line_start, (n.line_end or n.line_start) + 1)
        if n.ma == "ma_tho":
            for d in vung:
                ban_do.setdefault(d, "ma_tho")
            continue
        # Thẻ KHỐI chỉ "sở hữu" dòng đầu; thân là của thẻ con.
        vung_that = ([n.line_start] if n.than else list(vung))
        for d in vung_that:
            that.add(d)
            ban_do[d] = n.ma
    return len(nguon.splitlines()), that, ban_do


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    de = json.loads(DE.read_text(encoding="utf-8"))["loi"]

    # Gộp theo tệp: nhiều đề dùng chung một tệp, chỉ cần đo tệp một lần.
    tep_de = collections.defaultdict(list)
    for d in de:
        tep_de[d["tep"]].append(d)

    dong_goc = that_goc = 0
    dong_gieo = that_gieo = 0
    theo_tep = []
    trong_the = ngoai_the = khong_do = 0
    loai_the = collections.Counter()
    vi_du = []

    for tep, ds in sorted(tep_de.items()):
        p = GOC / tep
        if not p.is_file():
            khong_do += len(ds)
            continue
        goc = p.read_text(encoding="utf-8")
        n_g, that_g, _ = _phu(goc)
        dong_goc += n_g
        that_goc += len(that_g)

        # Bản CHUẨN HOÁ, chưa gieo lỗi — mốc để tìm dòng đột biến.
        chuan = ast.unparse(ast.parse(goc))
        n_c, that_c, ban_do_c = _phu(chuan)
        dong_gieo += n_c
        that_gieo += len(that_c)
        theo_tep.append({"tep": tep, "dong_goc": n_g,
                         "phu_goc": round(100 * len(that_g) / max(n_g, 1), 1),
                         "dong_chuan": n_c,
                         "phu_chuan": round(100 * len(that_c) / max(n_c, 1), 1)})

        for d in ds:
            cho = d["cho"]
            muc = set(cho) if isinstance(cho, list) else {int(cho)}
            ma, _mo = dot_bien(goc, muc)
            if not ma:
                khong_do += 1
                continue
            a, b = chuan.splitlines(), ma.splitlines()
            lech = [i + 1 for i in range(min(len(a), len(b))) if a[i] != b[i]]
            if not lech:
                khong_do += 1
                continue
            # Chỗ đột biến nằm trong thẻ thật khi MỌI dòng lệch đều thuộc thẻ thật
            nhan = [ban_do_c.get(x, "?") for x in lech]
            if all(x in that_c for x in lech):
                trong_the += 1
                for x in nhan:
                    loai_the[x] += 1
            else:
                ngoai_the += 1
                for x in nhan:
                    loai_the[x] += 1
                if len(vi_du) < 8:
                    vi_du.append({"tep": tep, "cho": cho, "dong": lech[:3],
                                  "the": nhan[:3],
                                  "ma": (b[lech[0] - 1].strip()[:74]
                                         if lech[0] <= len(b) else "")})

    n_de = trong_the + ngoai_the + khong_do
    phu_goc = 100 * that_goc / max(dong_goc, 1)
    phu_gieo = 100 * that_gieo / max(dong_gieo, 1)

    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps({
        "phu_goc": round(phu_goc, 1), "phu_chuan_hoa": round(phu_gieo, 1),
        "de_trong_the": trong_the, "de_ngoai_the": ngoai_the,
        "de_khong_do_duoc": khong_do, "tong_de": n_de,
        "nguong_di_tiep": NGUONG_DI_TIEP, "nguong_dung": NGUONG_DUNG,
        "theo_tep": theo_tep, "loai_the": dict(loai_the), "vi_du": vi_du,
    }, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")

    print("=" * 66)
    print("  CHẶNG B — thẻ có tả nổi chỗ Delta phải sửa không")
    print("=" * 66)
    print("  ĐỘ PHỦ DÒNG bằng thẻ THẬT, trên %d tệp của bộ đề:" % len(theo_tep))
    print("    tệp GỐC trong kho          : %.1f%%  (%d/%d dòng)"
          % (phu_goc, that_goc, dong_goc))
    print("    tệp ĐÃ CHUẨN HOÁ (ast.unparse, thứ Delta thật sự mở):")
    print("                               : %.1f%%  (%d/%d dòng)"
          % (phu_gieo, that_gieo, dong_gieo))
    print()
    print("  CHỖ ĐỘT BIẾN nằm ở đâu (%d đề):" % n_de)
    print("    trong THẺ THẬT             : %d" % trong_the)
    print("    rơi vào MÃ THÔ             : %d" % ngoai_the)
    print("    không đo được              : %d" % khong_do)
    if trong_the + ngoai_the:
        print("    tỉ lệ sửa được bằng thẻ    : %.0f%%"
              % (100 * trong_the / (trong_the + ngoai_the)))
    print()
    print("  loại thẻ mà đột biến rơi vào:")
    for k, v in loai_the.most_common(10):
        print("    %-12s %d" % (k, v))
    if vi_du:
        print()
        print("  ví dụ rơi vào mã thô:")
        for v in vi_du[:5]:
            print("    %s dòng %s -> %s" % (v["tep"], v["dong"], v["the"]))
            print("       %s" % v["ma"])
    print()
    print("  theo tệp (phủ gốc -> phủ sau chuẩn hoá):")
    for t in theo_tep:
        print("    %-26s %5.1f%% -> %5.1f%%   (%d -> %d dòng)"
              % (t["tep"][:26], t["phu_goc"], t["phu_chuan"],
                 t["dong_goc"], t["dong_chuan"]))

    print()
    print("=" * 66)
    if phu_gieo >= NGUONG_DI_TIEP:
        print("  ĐẠT (>= %.0f%%) — đi tiếp sang chặng C" % NGUONG_DI_TIEP)
        ma_thoat = 0
    elif phu_gieo >= NGUONG_DUNG:
        print("  ĐO ĐƯỢC MÀ KHÔNG ĐẠT (%.1f%%, ngưỡng %.0f%%) — ghi sổ rồi cân"
              % (phu_gieo, NGUONG_DI_TIEP))
        ma_thoat = 1
    else:
        print("  DƯỚI NGƯỠNG DỪNG (%.1f%% < %.0f%%) — Delta sẽ chỉ sửa mã thô"
              % (phu_gieo, NGUONG_DUNG))
        ma_thoat = 1
    print("=" * 66)
    print("  sổ: %s" % RA)
    return ma_thoat


if __name__ == "__main__":
    raise SystemExit(main())
