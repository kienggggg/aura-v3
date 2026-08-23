# -*- coding: utf-8 -*-
r"""Soi NƯỚC ĐI của model, không hỏi nó nghĩ gì.

21/08/2026. Sếp nêu: *"phải đo xem model nghĩ gì thì mới biết chỗ sửa được,
giống người mới học code — phải biết họ nghĩ gì mới giải quyết triệt để"*.

Ý đúng, nhưng có một cái bẫy ngay ở cửa: **hỏi model "vì sao mày làm thế" thì
nó kể một câu chuyện, không phải nguyên nhân**. Luật §4 của kho: lời nói không
phải hành vi. Hôm 20/08 đã bắt được đúng ca ấy — model sửa `now or ...` thành
`now if now else ...` rồi nêu một lý lẽ SAI hẳn, mà test vẫn xanh.

Nên tệp này không hỏi. Nó đọc **nước đi đã đánh** trong sổ E2 và xếp loại bằng
máy. Mỗi loại là một CÁCH HIỂU SAI khác nhau, và mỗi cách hiểu sai cần một cách
chữa khác nhau — hệt như dạy người mới:

    chép dòng bên cạnh   -> không hiểu ô trống là chỗ RIÊNG, tưởng là chép lại
    giữ nguyên đột biến  -> không thấy dòng đang sai; đọc mà không đối chiếu
    sai loại khối        -> không thấy dòng dưới đang phụ thuộc mình
    đúng loại sai nội dung -> hiểu KIỂU câu lệnh, không hiểu ĐIỀU KIỆN nào đúng

Ba loại đầu chữa bằng giao diện (chỉ ra chỗ, khoá loại thẻ). Loại thứ tư thì
không — nó đòi hiểu chương trình chạy ra sao, đúng bức tường đã đo cả ngày.

    venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\soi_nuoc_di.py
"""
from __future__ import annotations

import ast
import collections
import io
import json
import random
import sys
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(NHA))

from dung_de_loi import dot_bien                                # noqa: E402

SO = NHA / "so_dien_cho_trong.json"
CHO_TRONG = "____"


def _chuan(s: str) -> str:
    """So bằng AST, không so chuỗi — `a>1` và `a > 1` là MỘT nước đi."""
    try:
        return ast.dump(ast.parse(s.strip()))
    except SyntaxError:
        return "!" + " ".join(s.split())


def _kieu(s: str) -> str:
    """Kiểu câu lệnh theo AST: If · Return · Assign · Raise · Expr ..."""
    try:
        cay = ast.parse(s.strip())
    except SyntaxError:
        # Dòng mở khối đứng một mình không parse được -> vá thân giả rồi thử lại.
        try:
            cay = ast.parse(s.strip() + chr(10) + "    pass")
        except SyntaxError:
            return "?"
    return type(cay.body[0]).__name__ if cay.body else "?"


def _khoet(chuan: str, ma: str) -> tuple[str, list[tuple[int, str]]]:
    a, b = chuan.splitlines(), ma.splitlines()
    ra, dap = [], []
    for i in range(len(b)):
        if i < len(a) and a[i] != b[i]:
            thut = len(b[i]) - len(b[i].lstrip())
            ra.append(b[i][:thut] + CHO_TRONG)
            dap.append((i + 1, a[i]))
        else:
            ra.append(b[i])
    return "\n".join(ra), dap


def dung_lai_de() -> list[dict]:
    """Y HỆT do_dien_cho_trong.py — cùng gieo, cùng 9 đề."""
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo: dict[str, list] = {}
    for x in loi:
        theo.setdefault(x["tep"], []).append(x)
    rng = random.Random(19082026)
    de = []
    for tep, ds in theo.items():
        for n in (1, 2, 3):
            if len(ds) >= n:
                de.append({"tep": tep, "cho": [x["cho"] for x in rng.sample(ds, n)],
                           "so_loi": n})
    return de[:9]


def xep_loai(dap: str, tra: str, ma_khoet: str, dong_dot_bien: set[str]) -> str:
    if _chuan(dap) == _chuan(tra):
        return "dung"
    if tra.strip() in dong_dot_bien:
        return "giu_nguyen_dot_bien"
    # dòng model trả về có nằm sẵn đâu đó trong mã nó ĐƯỢC XEM không
    co_san = {l.strip() for l in ma_khoet.splitlines()
              if l.strip() and l.strip() != CHO_TRONG}
    if tra.strip() in co_san:
        return "chep_dong_co_san"
    # 21/08: bản đầu xếp loại bằng "có kết thúc bằng dấu hai chấm không".
    # Nó gọi `return SearchResult(...)` và `f"[{host}]"` là CÙNG loại — sai.
    # Luật §4 cấm chấm bằng dò chuỗi; so KIỂU NÚT AST mới là so cấu trúc.
    if _kieu(dap) != _kieu(tra):
        return "sai_kieu_cau_lenh"
    return "dung_kieu_sai_noi_dung"


CHUA = {
 "dung":                   "—",
 "giu_nguyen_dot_bien":    "giao diện: tô đỏ đúng dòng đang sai",
 "chep_dong_co_san":       "giao diện: khoá không cho lặp dòng đã có",
 "sai_kieu_cau_lenh":      "giao diện: khoá KIỂU thẻ cho ô trống",
 "dung_kieu_sai_noi_dung": "KHÔNG chữa được bằng giao diện — đòi hiểu lúc chạy",
}


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if not SO.is_file():
        print("KHÔNG ĐO ĐƯỢC — chưa có sổ %s" % SO.name)
        return 2
    so = json.loads(SO.read_text(encoding="utf-8"))
    theo_de = {(x["tep"], x["so_loi"]): x for x in so}

    dem: collections.Counter[str] = collections.Counter()
    vi_du: dict[str, tuple[str, str, str]] = {}

    for d in dung_lai_de():
        x = theo_de.get((d["tep"], d["so_loi"]))
        if not x:
            continue
        goc = (GOC / d["tep"]).read_text(encoding="utf-8")
        ma, _ = dot_bien(goc, set(d["cho"]))
        chuan = ast.unparse(ast.parse(goc))
        ma_khoet, dap_cap = _khoet(chuan, ma)
        dot = {ma.splitlines()[n - 1].strip() for n, _ in dap_cap
               if n - 1 < len(ma.splitlines())}
        dap = [l for _, l in dap_cap]

        for g in x.get("ghi", []):
            tra = g.get("tra_ve") or []
            for i, t in enumerate(tra[:len(dap)]):
                loai = xep_loai(dap[i], t, ma_khoet, dot)
                dem[loai] += 1
                vi_du.setdefault(loai, (d["tep"].split("/")[-1], dap[i].strip(), t.strip()))

    tong = sum(dem.values())
    print("NƯỚC ĐI CỦA MODEL — %d lần điền, xếp loại bằng máy" % tong)
    print("(không hỏi model nghĩ gì; hỏi thì nó kể chuyện, xem docstring)")
    print()
    print("  %-24s %5s %6s   %s" % ("nước đi", "lần", "%", "chữa bằng gì"))
    for loai, n in dem.most_common():
        print("  %-24s %5d %5.0f%%   %s" % (loai, n, 100 * n / tong, CHUA.get(loai, "?")))
    print()
    print("  ví dụ từng loại:")
    for loai, (tep, d_, t_) in vi_du.items():
        print("     [%s] %s" % (loai, tep))
        print("        đúng : %s" % d_[:66])
        print("        model: %s" % t_[:66])
    print()
    chua_duoc = dem["giu_nguyen_dot_bien"] + dem["chep_dong_co_san"] + dem["sai_kieu_cau_lenh"]
    print("  ---- DƯỚI ĐÂY LÀ SUY, KHÔNG PHẢI ĐO ----")
    print("  Bảng trên là phép đo: máy đếm nước đi. Hai dòng dưới là PHÁN ĐOÁN")
    print("  của người về việc loại nào chặn được bằng giao diện — chưa ai đo.")
    print("  C2 và C3 đã một lần hứa hẹn kiểu này rồi ra 0/9, nên đừng tin sẵn.")
    print()
    print("  đoán chặn được bằng giao diện : %d/%d = %.0f%%"
          % (chua_duoc, tong, 100 * chua_duoc / max(tong, 1)))
    print("  đoán đòi hiểu lúc chạy        : %d/%d = %.0f%%"
          % (dem["dung_kieu_sai_noi_dung"], tong,
             100 * dem["dung_kieu_sai_noi_dung"] / max(tong, 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
