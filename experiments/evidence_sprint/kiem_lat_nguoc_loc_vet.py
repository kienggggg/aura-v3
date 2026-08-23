# -*- coding: utf-8 -*-
"""Nghiệm thu độc lập E1 lọc theo vết thực thi.

Không import ``do_lat_nguoc`` hay tin các số worker tự ghi. Verifier tự dựng
lại bốn đề, tự liệt kê/lật AST, rồi đối chiếu sổ trước và sau.

Mã thoát: 0 = đạt, 1 = đo được mà không đạt, 2 = không đo được.
"""
from __future__ import annotations

import ast
import hashlib
import json
import random
import sys
from pathlib import Path


NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
SO_CU = GOC / "data" / "evidence_sprint" / "lat_nguoc_baseline_20260821.json"
SO_MOI = GOC / "data" / "evidence_sprint" / "lat_nguoc.json"
SHA_SO_CU = "6f716387cf37ced0849c8102809c7611ecc4f3176097f5c6aba8730d9aa04ad3"
MOC = {
    "core/may_tinh.py": True,
    "core/web_search.py": True,
    "core/dong_ho.py": True,
    "core/loai_cau_hoi.py": False,
}
DAU_VET = {
    "core/may_tinh.py": ("tests/test_may_tinh.py", [55],
                          "5af334da017929928c4883e83c0e3a0fb94e64f66abd1949d7a7a1be21ac4db5"),
    "core/web_search.py": ("tests/test_web_search.py", [78],
                           "cbf424d3acdf418e89aeb12037dd034468af1eadc77bb787a0cbdc0b3ebe528e"),
    "core/dong_ho.py": ("tests/test_dong_ho.py", [0],
                         "c104b5c2cda397caf7bb53db0f1486e53037bc4bf24e5d24c5f8cd75a2a76857"),
    "core/loai_cau_hoi.py": ("tests/test_loai_cau_hoi.py", [3],
                              "07166b72ee344d1f381c163534358e56d057f7aaafbf1d500ea7cc32c9b7c5f7"),
}
NGHICH = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
          ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


class _GieoDocLap(ast.NodeTransformer):
    """Bản nhỏ độc lập của đúng năm phép gieo trong bộ đề đóng băng."""

    def __init__(self, muc: set[int]):
        self.muc = muc
        self.dem = 0
        self.trung = 0

    def _lay(self) -> bool:
        hit = self.dem in self.muc
        self.dem += 1
        self.trung += int(hit)
        return hit

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH and self._lay():
            n.ops = [NGHICH[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay():
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay():
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay():
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and 0 <= n.value < 10000:
            if self._lay():
                return ast.Constant(value=n.value + 1)
        return n


class _LatDocLap(ast.NodeTransformer):
    """Dựng lại miền ứng viên legacy của E1, kể cả số nguyên ngoài miền gieo."""

    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.cho: list[tuple[int, int]] = []

    def _lay(self, n: ast.AST) -> bool:
        i = self.dem
        self.cho.append((i, int(getattr(n, "lineno", 0) or 0)))
        self.dem += 1
        return i == self.muc

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH and self._lay(n):
            n.ops = [NGHICH[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay(n):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay(n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay(n):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            if self._lay(n):
                return ast.Constant(value=n.value - 1)
        return n


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gieo(nguon: str, cho: set[int]) -> str:
    d = _GieoDocLap(cho)
    cay = d.visit(ast.parse(nguon))
    if d.trung != len(cho):
        raise ValueError("gieo thiếu chỗ")
    return ast.unparse(ast.fix_missing_locations(cay))


def _liet_ke(ma: str) -> list[tuple[int, int]]:
    d = _LatDocLap(-1)
    d.visit(ast.parse(ma))
    return d.cho


def _lat(ma: str, muc: int) -> str:
    d = _LatDocLap(muc)
    return ast.unparse(ast.fix_missing_locations(d.visit(ast.parse(ma))))


def _dung_bon_de() -> list[dict]:
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo_tep: dict[str, list[dict]] = {}
    for x in loi:
        theo_tep.setdefault(x["tep"], []).append(x)
    rng = random.Random(19082026)
    tat_ca: list[dict] = []
    for tep, ds in theo_tep.items():
        for so_loi in (1, 2, 3):
            if len(ds) >= so_loi:
                tat_ca.append({"tep": tep,
                               "tep_test": ds[0]["tep_test"],
                               "cho": [x["cho"] for x in rng.sample(ds, so_loi)],
                               "so_loi": so_loi})
    return [x for x in tat_ca if x["so_loi"] == 1 and x["tep"] in MOC]


def main() -> int:
    try:
        if not SO_CU.is_file() or not SO_MOI.is_file():
            print("KHÔNG ĐO ĐƯỢC: thiếu sổ cũ hoặc sổ mới")
            return 2
        if _sha(SO_CU) != SHA_SO_CU:
            print("KHÔNG ĐO ĐƯỢC: sổ cũ không còn nguyên byte")
            return 2
        moi = json.loads(SO_MOI.read_text(encoding="utf-8"))
        de = _dung_bon_de()
    except Exception as exc:
        print(f"KHÔNG ĐO ĐƯỢC: {exc}")
        return 2

    loi: list[str] = []
    if [x.get("tep") for x in moi] != list(MOC):
        loi.append("sổ mới không chứa đúng bốn đề theo thứ tự khóa")
    if [x["tep"] for x in de] != list(MOC):
        loi.append("bộ sinh không dựng đúng bốn đề khóa")
    theo_tep = {x.get("tep"): x for x in moi}

    for d in de:
        tep = d["tep"]
        r = theo_tep.get(tep)
        if not r:
            continue
        try:
            goc = (GOC / tep).read_text(encoding="utf-8")
            ma = _gieo(goc, set(d["cho"]))
            tep_test_moc, cho_moc, sha_moc = DAU_VET[tep]
            if (d["tep_test"] != tep_test_moc or d["cho"] != cho_moc
                    or hashlib.sha256(ma.encode("utf-8")).hexdigest() != sha_moc):
                loi.append(f"{tep}: danh tính đột biến đã trôi")
            chuan = ast.unparse(ast.parse(goc))
            cac_cho = _liet_ke(ma)
            dap_an = [i for i, _ in cac_cho if _lat(ma, i) == chuan]
            dong_trace = {int(x) for x in r.get("dong_da_chay", [])}
            sau = [i for i, dong in cac_cho if dong in dong_trace]
        except Exception as exc:
            loi.append(f"{tep}: không tái dựng được: {exc}")
            continue

        doi_chieu = {
            "sha256_ma_dot_bien": hashlib.sha256(ma.encode("utf-8")).hexdigest(),
            "so_cho_truoc_loc": len(cac_cho),
            "so_cho_sau_loc": len(sau),
            "chi_so_sau_loc": sau,
            "chi_so_dap_an_truoc_loc": dap_an,
        }
        for truong, dung in doi_chieu.items():
            if r.get(truong) != dung:
                loi.append(f"{tep}: {truong} ghi {r.get(truong)!r}, dựng lại {dung!r}")

        con_dap_an = (all(i in sau for i in dap_an) if dap_an else None)
        if r.get("dap_an_con_sau_loc") is not con_dap_an:
            loi.append(f"{tep}: nhãn giữ đáp án sai")
        thuc_te = bool(r.get("bat_dung_cho_gieo") and r.get("so_xanh_ca_bo", 0) > 0)
        if thuc_te != MOC[tep]:
            loi.append(f"{tep}: verdict {'XANH' if thuc_te else 'TRƯỢT'} sai mốc")
        if MOC[tep] and not con_dap_an:
            loi.append(f"{tep}: lọc làm rơi đáp án")
        if r.get("trang_thai") != "do_duoc":
            loi.append(f"{tep}: trạng thái {r.get('trang_thai')!r}")
        try:
            if float(r.get("giay_loc_va_lat")) > 60.0:
                loi.append(f"{tep}: lọc+lật quá 60 giây")
        except (TypeError, ValueError):
            loi.append(f"{tep}: thiếu thời gian lọc+lật")

        print(f"{Path(tep).name:22} {len(cac_cho):3}->{len(sau):3}  "
              f"đáp án={dap_an or None}  "
              f"{'XANH' if thuc_te else 'TRƯỢT'}  "
              f"{r.get('giay_loc_va_lat')}s")

    if loi:
        print("\nKHÔNG ĐẠT")
        for x in loi:
            print("-", x)
        return 1
    print("\nĐẠT: sổ cũ nguyên byte; số trước/sau, đáp án, verdict và thời gian đều khớp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
