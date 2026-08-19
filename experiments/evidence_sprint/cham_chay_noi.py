# -*- coding: utf-8 -*-
"""Tầng chấm thứ hai: mã có CHẠY NỔI không, không chỉ có gọi đúng hàm.

VÌ SAO THÊM. Soi tay đề đầu của lượt hai-bước 19/08:

    from core.dong_ho import cau_gio
    def noi_bay_gio_may_gio():
        now = datetime.datetime.now()    <- datetime KHÔNG HỀ được import
        cau_gio(now)                     <- gọi xong vứt kết quả, không return

Bộ chấm cũ ghi `dat=True` vì có import và có gọi `cau_gio`. Mã đó chạy là nổ
`NameError`. Nghĩa là mọi con số hôm nay — 0/28, 22/28 — chỉ đo được ĐÚNG MỘT
cột: có gọi hàm của kho hay không.

    gọi đúng hàm   <-  đo được, và đã đo
    mã chạy nổi    <-  tệp này thêm vào
    làm đúng việc  <-  vẫn KHÔNG đo được, phải có test cho từng đề

Chấm lại trên mã ĐÃ LƯU, không gọi model lần nào — đó là lý do phải giữ nguyên
văn đầu ra ngay từ đầu.

BA LỖI TỆP NÀY BẮT, đều đọc từ cây cú pháp:
    ten_chua_dinh_nghia   dùng tên chưa import và chưa gán (như `datetime`)
    khong_tra_ve          hàm chính không có `return` nào
    goi_sai_so_tham_so    gọi hàm của kho sai số tham số so với chữ ký thật

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\cham_chay_noi.py <so_nong.json>
"""
from __future__ import annotations

import ast
import builtins
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from core.khay_the import sinh_khay                             # noqa: E402

GOC = Path(__file__).resolve().parent.parent.parent
SAN_CO = set(dir(builtins))


def ten_chua_dinh_nghia(ma: str) -> list[str]:
    """Tên được DÙNG mà chưa import, chưa gán, chưa là tham số, chưa sẵn có."""
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ["<cú pháp hỏng>"]
    co = set(SAN_CO)
    for n in ast.walk(cay):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                co.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            co.add(n.name)
            for a in n.args.args + n.args.kwonlyargs:
                co.add(a.arg)
            if n.args.vararg:
                co.add(n.args.vararg.arg)
            if n.args.kwarg:
                co.add(n.args.kwarg.arg)
        elif isinstance(n, ast.ClassDef):
            co.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            co.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            co.add(n.name)
        elif isinstance(n, (ast.comprehension,)):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name):
                    co.add(t.id)
    thieu = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in co:
            if n.id not in thieu:
                thieu.append(n.id)
    return thieu


def khong_tra_ve(ma: str, ten_ham: str) -> bool:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return True
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == ten_ham:
            return not any(isinstance(x, ast.Return) and x.value is not None
                           for x in ast.walk(n))
    return True


def sai_so_tham_so(ma: str, can: str, so_tham_so: int) -> str:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ""
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            ten = (n.func.id if isinstance(n.func, ast.Name)
                   else n.func.attr if isinstance(n.func, ast.Attribute) else "")
            if ten == can:
                dua = len(n.args) + len(n.keywords)
                if dua > so_tham_so:
                    return f"đưa {dua} tham số, chữ ký có {so_tham_so}"
    return ""


def main() -> int:
    tep = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent / "so_hai_buoc.json")
    if not tep.is_file():
        print(f"  không có {tep}")
        return 2
    so = json.loads(tep.read_text(encoding="utf-8"))
    chu_ky = {t.ten: len(t.chu_ky.split("(")[1].rstrip(")").split(","))
              if t.chu_ky.split("(")[1].rstrip(")").strip() else 0
              for t in sinh_khay(GOC)}

    print(f"  chấm lại {len(so)} lượt trên mã ĐÃ LƯU, không gọi model\n")
    print(f"  {'đề':<26}{'gọi đúng':<10}{'chạy nổi':<10}vì sao không chạy nổi")
    print("  " + "-" * 78)
    n_goi = n_chay = 0
    for x in so:
        ma, can, ten = x.get("ma") or "", x["can"], x["de"]
        goi_ok = bool(x.get("dat"))
        n_goi += goi_ok
        ly_do = []
        if not ma:
            ly_do.append("không có mã")
        else:
            t = ten_chua_dinh_nghia(ma)
            if t:
                ly_do.append("tên chưa định nghĩa: " + ", ".join(t[:3]))
            if khong_tra_ve(ma, ten):
                ly_do.append("hàm không return gì")
            s = sai_so_tham_so(ma, can, chu_ky.get(can, 99))
            if s:
                ly_do.append(s)
        chay_ok = not ly_do
        n_chay += chay_ok
        print(f"  {ten:<26}{'ĐÚNG' if goi_ok else 'sai':<10}"
              f"{'ok' if chay_ok else 'KHÔNG':<10}{'; '.join(ly_do)[:60]}")

    n = len(so)
    print(f"\n  gọi đúng hàm : {n_goi}/{n}")
    print(f"  chạy nổi     : {n_chay}/{n}")
    print(f"  CẢ HAI       : {sum(1 for x in so if x.get('dat') and not ten_chua_dinh_nghia(x.get('ma') or '') and not khong_tra_ve(x.get('ma') or '', x['de']))}/{n}")
    print("\n  (làm ĐÚNG VIỆC thì vẫn chưa đo được — cần test riêng cho từng đề)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
