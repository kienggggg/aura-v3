# -*- coding: utf-8 -*-
r"""Dung bo de NGOAI HO cua E1. 22/08/2026.

VI SAO. `de_loi.json` co 29 loi, sinh boi `DotBien` qua dung bon bo duyet:

    visit_Compare · visit_BoolOp · visit_UnaryOp · visit_Constant

Ma `_Lat` trong `core/lat_nguoc.py` lat nguoc DUNG BON HO AY. Nen con so
"E1 giai 3/4 de loi don" do tren mot bo de CHI CHUA nhung loi E1 duoc thiet ke
de lat. Vong khep kin.

Tep nay sinh bo de NGOAI ho, de tra loi cau chua ai biet: E1 lam gi khi gap
loi no khong hieu.

NGHIENG VE LOI KHONG SAP - va day la cho quan trong nhat cua thiet ke.

Nhanh dang so cua phep do khong phai `0/N` ma la `>0/N`: E1 lam test XANH tren
mot loi no khong hieu, tuc va de len trieu chung. Muon cham duoc nhanh ay thi
loi phai la loai mot phep lat toan tu CO THE che lap.

Doi bien bua bai cho ra NameError - chuong trinh SAP, va khong phep lat
`<`<->`<=` nao cuu duoc mot NameError. Nhung ca ay chac chan ra 0, nen chung
KHONG kiem tra duoc dieu ta can kiem.

Nen o day:
    - uu tien BinOp · bo return · doi chi so · doi thu tu doi so
      (deu doi GIA TRI ma chuong trinh van chay tron lot)
    - `doi bien` chi hoan doi giua nhung ten CHAC CHAN DA DUOC GAN trong cung
      ham (thu tap Name o ngu canh Store), nen gan nhu khong sinh NameError
    - BO HAN `|` <-> `&`: trong 4 tep muc tieu co 12/25 BinOp la bitwise, dao
      chung tren co thuong khong doi hanh vi quan sat duoc -> test van xanh ->
      bi loai o khau "do on dinh", ton thi gian ma khong duoc ca nao

BAT `n.slice` LA Constant, KHONG PHAI `ast.Index`. Do tren Python 3.14.5 cua
kho: `ast.Index` VAN CON lop nhung parser KHONG sinh ra nut kieu ay tu 3.9 -
`ast.parse("a[0]").slice` cho ra `Constant`. Ma do `isinstance(x, ast.Index)`
se chay em va khong bat duoc gi.

    venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\dung_de_ngoai_ho.py
"""
from __future__ import annotations

import ast
import io
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(NHA))
sys.path.insert(0, str(GOC))

from dung_de_loi import chay_test                         # noqa: E402
from core.lat_nguoc import tao_cac_ung_vien               # noqa: E402

# Bo 1 (mac dinh). Bo 2 mo bang co `--bo2`: TEP KHAC HAN, khong trung mot
# tep nao voi bo 1.
#
# 24/08/2026: bo sinh de nay KHONG co hat giong ngau nhien nao — no liet ke
# tuan tu `for muc in range(tong_cho)` roi lay 6 de dau moi ho moi tep. Nen
# "sinh lai voi hat giong khac" la chuyen khong ton tai. Muon mot bo doc lap
# that thi phai doi MA NGUON, khong phai doi so ngau nhien.
#
# Vi sao can bo 2: luat "im lang khi khong lui duoc buoc nao" cua truy nguoc
# gia tri duoc rut ra TU CHINH bo 1. Cham no tren bo 1 la lay ket qua chung
# minh cho gia thiet sinh ra tu chinh ket qua ay.
BO_DE = {
    1: (("core/may_tinh.py", "core/web_search.py",
         "core/dong_ho.py", "core/loai_cau_hoi.py"), "de_ngoai_ho.json"),
    2: (("core/secret_guard.py", "core/user_memory.py",
         "core/doc_so_phien.py", "core/kiem_tien.py"), "de_ngoai_ho_2.json"),
    # Bo 3, 25/08: lai KHAC HAN bo 1 va bo 2. Tranh core/trace_runtime.py du
    # no co test — do chinh la module dang duoc DO, dung no la vong tron.
    3: (("core/chat_contract.py", "core/khay_the.py",
         "core/nho_lai.py", "core/omega.py"), "de_ngoai_ho_3.json"),
    # Bo 4, 25/08: luat chon noi TRUOC khi tinh hinh dang — chua dung o bo
    # 1-3, co test, khong phai trace_runtime.py (module dang duoc do, dung
    # no la vong tron), tong dong xap xi cac bo truoc. 1270 dong / 46 test
    # (bo 3 = 1258 dong). Giu nguyen luat sau khi thay ti le ham noi bo cua
    # bo nay chi 49% — thap nhat bon bo — vi doi luat luc do chinh la thu
    # tinh chinh theo gia thuyet ma bo de nay sinh ra de kiem.
    4: (("core/chat_runtime.py", "core/local_first_gateway.py",
         "core/cua_hoc_vet.py", "core/nhip_thuc_thi.py"), "de_ngoai_ho_4.json"),
    # Bo 5, 25/08 — BO DE NHAM DICH, khong phai bo ngau nhien.
    #
    # Bo 4 chi ra 8 ca khac-ham, duoi muc toi thieu 10 da dang ky, nen nguong
    # A KHONG DO DUOC. Nguyen nhan da canh bao truoc khi sinh de: bo 4 co ti
    # le ham noi bo 49%, thap nhat bon bo.
    #
    # Bo 5 CO Y chon tep co ti le ham noi bo cao — tuc chon theo chinh gia
    # thuyet dang kiem. Phai noi ro: con so cua bo nay CHI tra loi "khi co
    # nhieu ca khac-ham thi ban sua lam duoc gi", KHONG tra loi "co may dung
    # duoc chua". Ba tep cuoi cung con lai co test:
    #
    #     chat_service  82% (sau 3)   the_cst  77% (sau 9)   the_v1  74% (sau 5)
    #
    # Het ba tep nay thi kho khong con tep doc lap nao nua.
    5: (("core/chat_service.py", "core/the_cst.py",
         "core/the_v1.py"), "de_ngoai_ho_5.json"),
}
_BO = (5 if "--bo5" in sys.argv else
       4 if "--bo4" in sys.argv else
       3 if "--bo3" in sys.argv else
       2 if "--bo2" in sys.argv else 1)
TEP = BO_DE[_BO][0]
TEP_TEST = {t: "tests/test_" + Path(t).name for t in TEP}
RA = NHA / BO_DE[_BO][1]
TRAN_MOI_HO_MOI_TEP = 6      # du de co so, khong lam phep do dai vo ich


def _ten_da_gan(cay: ast.AST) -> dict[int, set[str]]:
    """Ten CHAC CHAN da duoc gan, theo tung ham (id(ham) -> tap ten).

    Chi lay Name o ngu canh Store va tham so ham. Hoan doi trong tap nay thi
    ca hai ten deu ton tai luc chay -> khong sinh NameError.
    """
    ra: dict[int, set[str]] = {}
    for h in ast.walk(cay):
        if not isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        t: set[str] = set()
        for a in h.args.args + h.args.kwonlyargs:
            t.add(a.arg)
        for n in ast.walk(h):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                t.add(n.id)
        ra[id(h)] = t
    return ra


class DotBienNgoai(ast.NodeTransformer):
    """Doi DUNG MOT cho co so thu tu `muc_tieu`. Cung khuon voi `DotBien`."""

    DOI_BINOP = {ast.Add: ast.Sub, ast.Sub: ast.Add,
                 ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult}

    def __init__(self, muc_tieu: int, ten_gan: set[str] | None = None):
        self.muc_tieu = muc_tieu
        self.dem = 0
        self.mo_ta = ""
        self.ho = ""
        self.dong = 0
        self.ten_gan = ten_gan or set()

    def _lay(self, ho: str, mo_ta: str, nut) -> bool:
        hit = self.dem == self.muc_tieu
        if hit:
            self.ho = ho
            self.mo_ta = mo_ta
            self.dong = int(getattr(nut, "lineno", 0) or 0)
        self.dem += 1
        return hit

    def visit_BinOp(self, n):
        self.generic_visit(n)
        k = type(n.op)
        if k in self.DOI_BINOP:
            moi = self.DOI_BINOP[k]
            if self._lay("binop", "%s -> %s" % (k.__name__, moi.__name__), n):
                n.op = moi()
        return n

    def visit_Return(self, n):
        self.generic_visit(n)
        if n.value is not None:
            if self._lay("bo_return", "bo return, ham tra None", n):
                return ast.Expr(value=n.value)
        return n

    def visit_Call(self, n):
        self.generic_visit(n)
        kh = [a for a in n.args if not isinstance(a, ast.Starred)]
        if len(kh) >= 2 and len(kh) == len(n.args):
            if self._lay("doi_thu_tu", "doi cho hai doi so dau", n):
                n.args[0], n.args[1] = n.args[1], n.args[0]
        return n

    def visit_Subscript(self, n):
        self.generic_visit(n)
        s = n.slice
        if isinstance(s, ast.Constant) and isinstance(s.value, int) \
                and not isinstance(s.value, bool):
            if self._lay("doi_chi_so", "a[%d] -> a[%d]" % (s.value, s.value + 1), n):
                n.slice = ast.Constant(value=s.value + 1)
        return n

    def visit_Name(self, n):
        if isinstance(n.ctx, ast.Load) and n.id in self.ten_gan:
            khac = sorted(x for x in self.ten_gan if x != n.id)
            if khac:
                if self._lay("doi_bien", "%s -> %s" % (n.id, khac[0]), n):
                    return ast.Name(id=khac[0], ctx=ast.Load())
        return n


def _dem_cho(nguon: str, ten_gan: set[str]) -> int:
    d = DotBienNgoai(-1, ten_gan)
    d.visit(ast.parse(nguon))
    return d.dem


def dot_bien_ngoai(nguon: str, muc: int, ten_gan: set[str]):
    """Tra (ma_moi, ho, mo_ta, dong) hoac (None, ...) neu khong gieo duoc."""
    d = DotBienNgoai(muc, ten_gan)
    try:
        moi = ast.unparse(ast.fix_missing_locations(d.visit(ast.parse(nguon))))
    except Exception:                                        # noqa: BLE001
        return None, "", "", 0
    if not d.ho:
        return None, "", "", 0
    try:
        ast.parse(moi)
    except SyntaxError:
        return None, "", "", 0
    return moi, d.ho, d.mo_ta, d.dong


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))

    de = []
    thong_ke: dict[str, dict[str, int]] = {}
    t0 = time.monotonic()
    try:
        for tep in TEP:
            f = tam / tep
            goc = f.read_text(encoding="utf-8")
            chuan = ast.unparse(ast.parse(goc))
            cay = ast.parse(goc)
            gom = _ten_da_gan(cay)
            ten_gan: set[str] = set()
            for v in gom.values():
                ten_gan |= v
            tong_cho = _dem_cho(goc, ten_gan)
            dem_ho: dict[str, int] = {}
            thong_ke[tep] = {}
            print("  %-22s %d cho co the gieo" % (tep.split("/")[-1], tong_cho))

            HO = ("binop", "bo_return", "doi_thu_tu", "doi_chi_so", "doi_bien")
            for muc in range(tong_cho):
                # Du ho roi thi dung han. Khong co dong nay thi vong lap van
                # chay test cho hang tram cho con lai - phan lon la nhung dot
                # bien lam test VAN XANH, tuc ton 2 lan chay test de vut di.
                if all(dem_ho.get(h, 0) >= TRAN_MOI_HO_MOI_TEP for h in HO):
                    break
                ma, ho, mo_ta, dong = dot_bien_ngoai(goc, muc, ten_gan)
                if ma is None:
                    continue
                if dem_ho.get(ho, 0) >= TRAN_MOI_HO_MOI_TEP:
                    continue
                # ---- CHUNG MINH NGOAI HO ----
                # Chi chung minh: khong phep lat DON nao cua _Lat khoi phuc
                # duoc ban goc. E1 lat nhieu vong tham lam, nen day KHONG phai
                # cau "E1 khong the giai" - chinh phep do se tra loi cau ay.
                try:
                    uv = tao_cac_ung_vien(ma)
                except Exception:                            # noqa: BLE001
                    continue
                if any(mm == chuan for _, _, mm in uv):
                    continue
                # ---- TEST PHAI DO ON DINH ----
                f.write_text(ma, encoding="utf-8")
                try:
                    m1, loi1 = chay_test(tam, TEP_TEST[tep])
                    m2, _ = chay_test(tam, TEP_TEST[tep])
                except Exception:                            # noqa: BLE001
                    f.write_text(goc, encoding="utf-8")
                    continue
                f.write_text(goc, encoding="utf-8")
                if m1 == 0 or m2 == 0:
                    continue
                sap = ("Error" in loi1 and "assert" not in loi1.lower())
                dem_ho[ho] = dem_ho.get(ho, 0) + 1
                de.append({"tep": tep, "tep_test": TEP_TEST[tep], "muc": muc,
                           "ho": ho, "mo_ta": mo_ta, "dong": dong,
                           "co_ve_sap": sap, "ma": ma})
                print("     [%s] muc %-4d dong %-4d %s%s"
                      % (ho, muc, dong, mo_ta, "  (co ve SAP)" if sap else ""))
            for h in ("binop", "bo_return", "doi_thu_tu", "doi_chi_so", "doi_bien"):
                thong_ke[tep][h] = dem_ho.get(h, 0)
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    RA.write_text(json.dumps(
        {"_vi_sao": "Bo de NGOAI HO cua _Lat. Xem docstring dung_de_ngoai_ho.py",
         "de": de, "thong_ke": thong_ke}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print()
    print("  %-22s %7s %10s %11s %11s %10s" % ("tep", "binop", "bo_return",
                                               "doi_thu_tu", "doi_chi_so", "doi_bien"))
    for tep in TEP:
        t = thong_ke.get(tep, {})
        print("  %-22s %7d %10d %11d %11d %10d"
              % (tep.split("/")[-1][:22], t.get("binop", 0), t.get("bo_return", 0),
                 t.get("doi_thu_tu", 0), t.get("doi_chi_so", 0), t.get("doi_bien", 0)))
    print()
    n_sap = sum(1 for x in de if x["co_ve_sap"])
    print("  TONG: %d de  (co ve SAP: %d, doi gia tri ma chay tron lot: %d)"
          % (len(de), n_sap, len(de) - n_sap))
    print("  %.0f giay" % (time.monotonic() - t0))
    return 0 if de else 2


if __name__ == "__main__":
    raise SystemExit(main())
