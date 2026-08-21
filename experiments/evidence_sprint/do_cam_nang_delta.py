# -*- coding: utf-8 -*-
"""CẨM NANG DELTA — lỗi pytest có nói ra được LOẠI THẺ cần sửa không.

VÌ SAO — 20/08/2026, ý của Sếp.

Ba lượt đo C · C2 · C3 đều gãy ở cùng một chỗ: `chọn đúng thẻ` đứng yên 1/9 dù
đổi cách trình bày, ép khuôn, và bổ thẻ sâu. Vấn đề của Delta **không nằm ở chỗ
sửa, nó nằm ở chỗ tìm**.

Sếp đề: thẻ đã phân theo chức năng rồi, khay lại ít thẻ — vậy viết một cuốn cẩm
nang *"gặp lỗi kiểu này thì soi loại thẻ nào"*.

Ý ấy khác ba lượt trước ở chỗ nó nhắm vào TÌM, và nó đo được **không cần model**.

BỘ ĐỘT BIẾN CÓ ĐÚNG NĂM LOẠI (`dung_de_loi.DotBien`), mỗi loại ứng thẳng vào
một loại thẻ:

    visit_Compare   <↔<=  >↔>=  ==↔!=    ->  so_sanh    ô `phep`
    visit_BoolOp    and↔or                ->  va_hoac    ô `phep`
    visit_UnaryOp   bỏ `not`              ->  phu_dinh   (nút bị XOÁ hẳn)
    visit_Constant  True↔False            ->  hằng bool
    visit_Constant  số -> số+1            ->  hằng số

TỆP NÀY CHỈ THU DỮ LIỆU, CHƯA VIẾT LUẬT. Viết luật sau khi đã nhìn 29 đáp án là
fit vào bộ đề — đúng thứ `cua_hoc_vet.py` dựng ra để chặn. Thu xong mới xem cái
gì trong lỗi mang tín hiệu, rồi luật viết từ TAXONOMY chứ không từ đáp án.

    venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_cam_nang_delta.py
"""
from __future__ import annotations

import collections
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(NHA))

from dung_de_loi import chay_test, dot_bien            # noqa: E402

RA = GOC / "data" / "evidence_sprint" / "cam_nang_delta.json"

# Loại đột biến -> loại thẻ. Bảng này đọc THẲNG từ `DotBien`, không suy từ đáp án.
LOAI_THE = {
    "so sánh": "so_sanh",
    "logic": "va_hoac",
    "bỏ phủ định": "phu_dinh",
    "True/False": "hang_bool",
    "hằng số": "hang_so",
}


def _loai(mo_ta: str) -> str:
    t = mo_ta.split(":", 1)[-1].strip()
    for k, v in LOAI_THE.items():
        if t.startswith(k):
            return v
    return "?"


def _boc_loi(loi: str) -> dict:
    """Rút những thứ MÁY đọc được từ lỗi pytest. Chưa phán đoán gì."""
    d: dict = {}
    m = re.search(r"\b(\w*Error|\w*Exception)\b", loi)
    d["ngoai_le"] = m.group(1) if m else ""
    d["co_assert"] = "assert" in loi.lower()
    # assert so sánh hai giá trị: `assert X == Y`, `assert X is Y`
    m = re.search(r"assert\s+(.{0,60}?)\s*(==|!=|is not|is|<=|>=|<|>|in)\s*(.{0,60})",
                  loi)
    if m:
        d["ve_trai"], d["phep"], d["ve_phai"] = (m.group(1).strip(),
                                                 m.group(2), m.group(3).strip())
    d["co_True_False"] = bool(re.search(r"\b(True|False)\b", loi))
    # hai số khác nhau xuất hiện trong lỗi -> mùi hằng số / phép tính
    so = re.findall(r"(?<![\w.])(\d{1,9})(?![\w.])", loi)
    d["so_trong_loi"] = sorted(set(so))[:6]
    d["hai_so_lech_1"] = any(abs(int(a) - int(b)) == 1
                             for i, a in enumerate(so) for b in so[i + 1:]
                             if a.isdigit() and b.isdigit())
    d["dai"] = len(loi)
    return d


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    de = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    ra = []
    try:
        for i, d in enumerate(de, 1):
            f = tam / d["tep"]
            goc = f.read_text(encoding="utf-8")
            ma, mo = dot_bien(goc, {int(d["cho"])})
            if not ma:
                continue
            f.write_text(ma, encoding="utf-8")
            try:
                _, loi = chay_test(tam, d["tep_test"])
            finally:
                f.write_text(goc, encoding="utf-8")
            r = {"tep": d["tep"], "cho": d["cho"], "loai_the": _loai(mo),
                 "mo_ta": mo.split(":", 1)[-1].strip(), "loi": loi[-900:]}
            r.update(_boc_loi(loi))
            ra.append(r)
            print("  %2d/%d  %-22s %-12s %-18s %s"
                  % (i, len(de), d["tep"].split("/")[-1][:22], r["loai_the"],
                     r["ngoai_le"] or "(assert)",
                     "lệch 1" if r["hai_so_lech_1"] else ""))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps(ra, ensure_ascii=False, indent=1),
                  encoding="utf-8")

    print("\n" + "=" * 64)
    print("  TÍN HIỆU TRONG LỖI, theo LOẠI THẺ")
    print("=" * 64)
    theo = collections.defaultdict(list)
    for r in ra:
        theo[r["loai_the"]].append(r)
    print("  %-12s %4s | %-16s %-9s %-9s %s"
          % ("loại thẻ", "n", "ngoại lệ hay gặp", "có assert", "có T/F", "2 số lệch 1"))
    for k, ds in sorted(theo.items(), key=lambda x: -len(x[1])):
        nl = collections.Counter(r["ngoai_le"] or "(assert)" for r in ds)
        print("  %-12s %4d | %-16s %-9s %-9s %s"
              % (k, len(ds), "%s %d" % nl.most_common(1)[0],
                 sum(r["co_assert"] for r in ds),
                 sum(r["co_True_False"] for r in ds),
                 sum(r["hai_so_lech_1"] for r in ds)))
    print("\n  sổ: %s" % RA)
    print("  CHƯA viết luật. Nhìn bảng trên rồi mới quyết luật viết được hay không.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
