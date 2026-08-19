# -*- coding: utf-8 -*-
"""Soát TỪNG ĐỀ trong sổ nóng — hỏng ở đâu, và hỏng kiểu gì.

Sếp dặn 19/08: *tách ra kiểm từng đề để phát hiện lỗi và làm sai ở đâu để tinh
chỉnh kịp thời.* Một con số gộp `12/28` không nói được nên sửa cái gì. Sáu kiểu
hỏng dưới đây cần sáu cách chữa khác nhau:

    cu_phap_hong    mã không parse nổi        -> chữa ở bước bóc rào / lời dặn
    tu_viet_lay     tự `def` lại hàm của kho  -> khay chưa lọt vào mắt model
    khong_nhap      gọi đúng tên, KHÔNG import-> lời dặn thiếu, chữa bằng chữ
    goi_ham_khac    nhặt nhầm thẻ hàng xóm    -> thẻ chưa phân biệt được
    khong_goi_gi    không gọi hàm nào của kho -> bỏ khay đi tự làm
    dat             xong

Và một cột riêng: `nhat_ca_cum` — model gọi HAI hay nhiều thẻ cùng lúc. Đó là
đoán mò có che: không phân biệt được nên gọi cả hai cho chắc. Lượt 6 đề trước
tôi đã suýt tính một trường hợp như thế thành "đúng".

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\soat_khay.py
"""
from __future__ import annotations

import ast
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import sinh_khay                             # noqa: E402
from do_khay_loc import (                                       # noqa: E402
    dung_ham_kho, goi_ham_nao, nhap_tu_kho, tu_dinh_nghia,
)

GOC = Path(__file__).resolve().parent.parent.parent
SO = Path(__file__).resolve().parent / "so_nong_khay.json"


def phan_loai(ma: str, can: str, ten_kho: set[str]) -> str:
    if dung_ham_kho(ma, can):
        return "dat"
    try:
        ast.parse(ma)
    except SyntaxError:
        return "cu_phap_hong"
    if can in tu_dinh_nghia(ma):
        return "tu_viet_lay"
    goi = goi_ham_nao(ma)
    if can in goi and can not in nhap_tu_kho(ma):
        return "khong_nhap"
    khac = (goi & ten_kho) - {can} - tu_dinh_nghia(ma)
    if khac:
        return "goi_ham_khac"
    return "khong_goi_gi"


def main() -> int:
    if not SO.is_file():
        print(f"  chưa có {SO.name} — phép đo chưa chạy xong")
        return 2
    so = json.loads(SO.read_text(encoding="utf-8"))
    ten_kho = {t.ten for t in sinh_khay(GOC)}
    dk = sorted({x["dieu_kien"] for x in so}, key=lambda s: so.index(
        next(y for y in so if y["dieu_kien"] == s)))

    theo_de: dict[str, dict] = collections.OrderedDict()
    for x in so:
        theo_de.setdefault(x["de"], {})[x["dieu_kien"]] = x

    print(f"  {len(so)} lượt · {len(theo_de)} đề · {len(dk)} điều kiện\n")
    print(f"  {'đề':<26}{'hàm cần':<26}" + "".join(f"{d.split('·')[0].strip():<16}" for d in dk))
    print("  " + "-" * (52 + 16 * len(dk)))
    dem: dict[str, collections.Counter] = {d: collections.Counter() for d in dk}
    for de, hang in theo_de.items():
        o = f"  {de:<26}{next(iter(hang.values()))['can']:<26}"
        for d in dk:
            x = hang.get(d)
            if not x:
                o += f"{'(thiếu)':<16}"
                continue
            pl = phan_loai(x["ma"], x["can"], ten_kho)
            dem[d][pl] += 1
            o += f"{('ĐẠT' if pl == 'dat' else pl):<16}"
        print(o)

    print("\n  ===== VÌ SAO HỎNG, theo điều kiện =====")
    loai = sorted({k for c in dem.values() for k in c})
    print(f"  {'':<20}" + "".join(f"{k:<16}" for k in loai))
    for d in dk:
        print(f"  {d.split('·')[0].strip():<20}"
              + "".join(f"{dem[d].get(k, 0):<16}" for k in loai))

    # đoán mò có che: gọi từ hai thẻ trở lên
    print("\n  ===== GỌI NHIỀU THẺ CÙNG LÚC (đoán mò có che) =====")
    for d in dk:
        n = 0
        for x in (y for y in so if y["dieu_kien"] == d):
            if len((goi_ham_nao(x["ma"]) & ten_kho) - tu_dinh_nghia(x["ma"])) >= 2:
                n += 1
        print(f"    {d.split('·')[0].strip():<20}{n} đề")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
