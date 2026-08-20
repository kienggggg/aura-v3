# -*- coding: utf-8 -*-
"""Bộ đọc/ghi thẻ dựng trên LibCST thay cho `ast`. Cùng giao diện với `the_v1`.

VÌ SAO CÓ TỆP RIÊNG — 20/08/2026.

`ast` của Python CỐ Ý vứt dấu cách, chú thích, và cả `elif` (nó chỉ là nút `If`
lồng trong `orelse`, không cờ nào phân biệt với `else`). Bản v1 phải tự bù bằng
`line_start`/`duoi_dong`/`ma_tho`, và cả bốn lỗi đo được đều sinh ra từ chỗ bù:

    gõ lại y giá trị cũ rồi lưu   49,8% giữ nguyên byte
    chú thích cuối dòng thẻ khối  mất 4/4
    `elif X:` -> `else:`          28/40, MẤT LUÔN ĐIỀU KIỆN
    thẻ tả sai nguồn              390/2.539

LibCST giữ nguyên từng byte theo thiết kế. Đo 20/08 trên 67 tệp của kho:
parse -> code khớp 67/67, chạm 3.888 nút qua `with_changes` vẫn 67/67.

VIẾT THÀNH TỆP RIÊNG, không sửa `the_v1.py`, vì Antigravity đang cầm tệp đó theo
kế hoạch v1.1 (luật CLAUDE.md mục 7: đọc trước khi viết đè). Hai bộ chạy song
song, đo được cạnh nhau bằng `tools/do_cua_cung_the.py --cst`.

KHÁC BIỆT CỐT LÕI so với bản v1:

    v1   : thẻ giữ CÁC Ô, lưu thì DỰNG LẠI dòng từ ô -> mất thứ ô không chứa
    ở đây: thẻ giữ THAM CHIẾU tới nút cây, lưu thì chỉ thay ĐÚNG ô bị đổi
           -> thứ người dùng không chạm vào thì không thể xê dịch

Nên thẻ `Định nghĩa hàm` không cần ô cho `-> bool` mới giữ được `-> bool`.
"""
from __future__ import annotations

import io
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

from core.the_v1 import TheNode

# Thẻ khối: dòng đầu là của thẻ, thân là các thẻ con.
KHOI = {"neu", "nguoc_lai", "ham", "lap_moi", "lap_khi"}


class BanGhiCST:
    """Cùng vai với `FileSourceRecord`, thêm cây CST và bản đồ thẻ -> nút.

    `the_api.py` chỉ đụng `tree` / `has_modifications` / `duong_dan` nên thay
    một đổi một được.
    """

    def __init__(self, duong_dan, raw_bytes, newline, lines, tree,
                 mod, ban_do):
        self.duong_dan = duong_dan
        self.raw_bytes = raw_bytes
        self.newline = newline
        self.lines = lines
        self.tree: List[TheNode] = tree
        self.has_modifications = False
        self._mod = mod                      # cst.Module gốc
        self._ban_do: Dict[str, Any] = ban_do  # id thẻ -> nút CST


# ---------------------------------------------------------------- đọc

def _chu_thich_cuoi_dong(nut, mod) -> str:
    """Chú thích cuối dòng, lấy TỪ CÂY chứ không dò chuỗi.

    Câu lệnh đơn giữ nó ở `trailing_whitespace`; thẻ khối giữ ở
    `body.header` (phần sau dấu hai chấm). Cả hai đều là nút thật, nên
    `d = ["# Omega"]` không lọt — bộ tách của LibCST biết đâu là chuỗi.
    """
    tw = None
    if isinstance(nut, cst.SimpleStatementLine):
        tw = nut.trailing_whitespace
    elif hasattr(nut, "body") and isinstance(getattr(nut, "body", None),
                                             cst.IndentedBlock):
        tw = nut.body.header
    if tw is None or tw.comment is None:
        return ""
    return mod.code_for_node(tw).rstrip("\r\n")


def _ma_cua(nut) -> tuple[str, Dict[str, str], Dict[str, Any]]:
    """Nút CST này là thẻ loại gì, ô nào lấy từ nút con nào.

    Trả `(mã thẻ, các ô dạng chữ, bản đồ ô -> nút con)`. Bản đồ ấy là thứ cho
    phép lúc lưu chỉ thay đúng một ô — chỗ khác không đụng tới.
    """
    if isinstance(nut, cst.FunctionDef):
        return "ham", {}, {"ten_ham": nut.name, "tham_so": nut.params}
    if isinstance(nut, cst.If):
        return "neu", {}, {"dieu_kien": nut.test}
    if isinstance(nut, cst.Else):
        return "nguoc_lai", {}, {}
    if isinstance(nut, cst.For):
        return "lap_moi", {}, {"bien": nut.target, "day": nut.iter}
    if isinstance(nut, cst.While):
        return "lap_khi", {}, {"dieu_kien": nut.test}
    if isinstance(nut, cst.SimpleStatementLine) and len(nut.body) == 1:
        t = nut.body[0]
        if isinstance(t, cst.Assign) and len(t.targets) == 1:
            return "gan", {}, {"ten_bien": t.targets[0].target,
                               "gia_tri": t.value}
        if isinstance(t, cst.Return):
            return "tra_ve", {}, ({"gia_tri": t.value} if t.value is not None
                                  else {})
        if isinstance(t, cst.Expr) and isinstance(t.value, cst.Call):
            g = t.value
            if isinstance(g.func, cst.Name) and g.func.value == "print":
                return "in_ra", {}, {"noi_dung": g}      # ô = danh sách đối số
            return "goi_ham", {}, {"ten_ham": g.func, "doi_so": g}
    return "ma_tho", {}, {}


def _o_thanh_chu(ma: str, ban_do: Dict[str, Any], mod) -> Dict[str, str]:
    """Đổi nút con thành chữ cho người dùng sửa."""
    o: Dict[str, str] = {}
    for ten, nut_con in ban_do.items():
        if ma in ("in_ra", "goi_ham") and ten in ("noi_dung", "doi_so"):
            # ô là DANH SÁCH đối số, không phải cả lệnh gọi
            o[ten] = ", ".join(mod.code_for_node(a.with_changes(comma=cst.MaybeSentinel.DEFAULT)).strip()
                               for a in nut_con.args)
        else:
            o[ten] = mod.code_for_node(nut_con).strip()
    if ma == "tra_ve" and "gia_tri" not in o:
        o["gia_tri"] = ""
    return o


def doc_chuoi_py_sang_cay_the(nguon: str,
                              duong_dan: Optional[str] = None) -> BanGhiCST:
    """Đọc mã nguồn thành cây thẻ. Không mất gì: cây CST giữ nguyên bản gốc."""
    mod = cst.parse_module(nguon)
    # `unsafe_skip_copy` giữ NGUYÊN danh tính nút — lưu về sau khớp nút bằng
    # `is`, nên không cần đường dẫn hay số thứ tự nào để tìm lại.
    boc = MetadataWrapper(mod, unsafe_skip_copy=True)
    vi_tri = boc.resolve(PositionProvider)

    ban_do: Dict[str, Any] = {}
    dem = [0]
    # Nút CST đông cứng, không gắn được thuộc tính -> ghi danh tính vào tập.
    la_elif: set[int] = set()

    def lam(nut, muc: int) -> TheNode:
        ma, _, cac_o = _ma_cua(nut)
        dem[0] += 1
        mid = "%s_%d" % (ma, dem[0])
        r = vi_tri[nut]
        if ma == "ma_tho":
            tho = mod.code_for_node(nut)
            t = TheNode(id=mid, ma="ma_tho", o={"nguyen_van": tho},
                        raw_text=tho, line_start=r.start.line,
                        line_end=r.end.line, indent=muc * 4)
            ban_do[mid] = nut
            return t
        t = TheNode(id=mid, ma=ma, o=_o_thanh_chu(ma, cac_o, mod),
                    line_start=r.start.line, line_end=r.end.line,
                    indent=muc * 4,
                    duoi_dong=_chu_thich_cuoi_dong(nut, mod))
        # `elif` là nút If nằm trong orelse. Ghi rõ ra ô, vì bản v1 nuốt mất
        # chỗ này: 28/40 thẻ Ngược lại sinh ra `else:` và MẤT ĐIỀU KIỆN.
        if ma == "neu" and id(nut) in la_elif:
            t.o["noi_tiep"] = "1"
        ban_do[mid] = nut
        t.than = than_cua(nut, muc + 1)
        return t

    def than_cua(nut, muc: int) -> List[TheNode]:
        con: List[TheNode] = []
        than = getattr(nut, "body", None)
        if isinstance(than, cst.IndentedBlock):
            for c in than.body:
                con.append(lam(c, muc))
        orelse = getattr(nut, "orelse", None)
        if orelse is not None:
            if isinstance(orelse, cst.If):
                la_elif.add(id(orelse))      # đánh dấu để lam() ghi ô noi_tiep
            con.append(lam(orelse, muc - 1))
        return con

    cay = [lam(c, 0) for c in mod.body]
    b = nguon.encode("utf-8")
    return BanGhiCST(duong_dan, b, mod.default_newline,
                     nguon.splitlines(), cay, mod, ban_do)


def doc_tep_py_sang_cay_the(duong_dan: Path | str) -> BanGhiCST:
    """Đọc một tệp .py trên đĩa thành cây thẻ, giữ nguyên từng byte bản gốc."""
    p = Path(duong_dan)
    return doc_chuoi_py_sang_cay_the(p.read_bytes().decode("utf-8"), str(p))


# ---------------------------------------------------------------- ghi

def _doi_bieu_thuc(chu: str):
    return cst.parse_expression(chu)


def _doi_tham_so(chu: str):
    m = cst.parse_statement("def _(%s): pass" % chu)
    return m.params


def _doi_doi_so(chu: str):
    g = cst.parse_expression("_(%s)" % chu)
    return list(g.args)


def _ap_dung(nut, o_moi: Dict[str, str], o_cu: Dict[str, str]):
    """Thay ĐÚNG những ô đã đổi. Ô không đổi thì không đụng tới nút con của nó.

    Đây là chỗ khác hẳn bản v1: bản v1 dựng lại cả dòng từ các ô, nên thứ ô
    không chứa (`-> bool`, `= None`, chú thích) biến mất. Ở đây nút cũ đi tiếp,
    chỉ nhánh bị sửa mới được thay.
    """
    def khac(ten):
        return ten in o_moi and o_moi[ten] != o_cu.get(ten)

    if isinstance(nut, cst.FunctionDef):
        t = {}
        if khac("ten_ham"):
            t["name"] = cst.Name(o_moi["ten_ham"])
        if khac("tham_so"):
            t["params"] = _doi_tham_so(o_moi["tham_so"])
        return nut.with_changes(**t) if t else nut
    if isinstance(nut, cst.If):
        return (nut.with_changes(test=_doi_bieu_thuc(o_moi["dieu_kien"]))
                if khac("dieu_kien") else nut)
    if isinstance(nut, cst.While):
        return (nut.with_changes(test=_doi_bieu_thuc(o_moi["dieu_kien"]))
                if khac("dieu_kien") else nut)
    if isinstance(nut, cst.For):
        t = {}
        if khac("bien"):
            t["target"] = _doi_bieu_thuc(o_moi["bien"])
        if khac("day"):
            t["iter"] = _doi_bieu_thuc(o_moi["day"])
        return nut.with_changes(**t) if t else nut
    if isinstance(nut, cst.SimpleStatementLine) and len(nut.body) == 1:
        t = nut.body[0]
        if isinstance(t, cst.Assign):
            th = {}
            if khac("ten_bien"):
                th["targets"] = [t.targets[0].with_changes(
                    target=_doi_bieu_thuc(o_moi["ten_bien"]))]
            if khac("gia_tri"):
                th["value"] = _doi_bieu_thuc(o_moi["gia_tri"])
            return (nut.with_changes(body=[t.with_changes(**th)])
                    if th else nut)
        if isinstance(t, cst.Return) and khac("gia_tri"):
            v = (_doi_bieu_thuc(o_moi["gia_tri"])
                 if o_moi["gia_tri"].strip() else None)
            return nut.with_changes(body=[t.with_changes(value=v)])
        if isinstance(t, cst.Expr) and isinstance(t.value, cst.Call):
            g = t.value
            th = {}
            if khac("ten_ham"):
                th["func"] = _doi_bieu_thuc(o_moi["ten_ham"])
            if khac("doi_so"):
                th["args"] = _doi_doi_so(o_moi["doi_so"])
            if khac("noi_dung"):
                th["args"] = _doi_doi_so(o_moi["noi_dung"])
            return (nut.with_changes(body=[t.with_changes(
                value=g.with_changes(**th))]) if th else nut)
    return nut


class _Vasua(cst.CSTTransformer):
    """Thay đúng những nút được đánh dấu, khớp bằng DANH TÍNH nút (`is`)."""

    def __init__(self, doi):
        super().__init__()
        self.doi = doi           # id(nút CST) -> (ô mới, ô cũ)
        self.da_thay = 0

    def on_leave(self, cu, moi):
        t = self.doi.get(id(cu))
        if t is None:
            return moi
        self.da_thay += 1
        if isinstance(moi, cst.SimpleStatementLine) or True:
            ra = _ap_dung(moi, t[0], t[1])
            return ra
        return moi


def luu_cay_the_ra_tep_py(ban_ghi: BanGhiCST) -> bytes:
    """Ghi cây thẻ về byte.

    KHÔNG có đường tắt `return raw_bytes`: kể cả khi không sửa gì, mã vẫn đi
    qua bộ ghi của LibCST. Bản v1 có đường tắt ấy nên test cửa cứng 1 khớp
    SHA 100% với MỌI tệp mà bộ sinh mã chưa hề chạy.
    """
    doi = {}

    def gom(ns):
        for n in ns:
            if n.da_sua and n.id in ban_ghi._ban_do:
                nut = ban_ghi._ban_do[n.id]
                if n.ma == "ma_tho":
                    moi = n.o.get("nguyen_van", n.raw_text or "")
                    # KHÔNG ĐỔI THÌ KHÔNG ĐỤNG — giống hệt luật `khac()` của
                    # thẻ thường. Phân tích lại rồi cắm vào khối thụt sẽ khiến
                    # LibCST thụt lại các dòng TRỐNG bên trong, thêm khoảng
                    # trắng cuối dòng: đo 20/08, the_v1.py:538 và
                    # test_the_v1.py:351 đổi '' thành '    '.
                    if moi == (n.raw_text or ""):
                        continue
                    doi[id(nut)] = ("__tho__", moi)
                else:
                    ma, _, cac_o = _ma_cua(nut)
                    doi[id(nut)] = (dict(n.o),
                                    _o_thanh_chu(ma, cac_o, ban_ghi._mod))
            gom(n.than)
    gom(ban_ghi.tree)

    if not doi:
        return ban_ghi._mod.code.encode("utf-8")

    tho = {k: v[1] for k, v in doi.items() if v[0] == "__tho__"}
    thuong = {k: v for k, v in doi.items() if v[0] != "__tho__"}

    class _VaTho(_Vasua):
        def on_leave(self, cu, moi):
            if id(cu) in tho:
                m = cst.parse_module(tho[id(cu)])
                # GIỮ LẠI DÒNG TRỐNG ĐỨNG TRƯỚC. `leading_lines` không nằm
                # trong đoạn văn bản người dùng cầm, nên nút mới sinh ra không
                # có chúng — bản đầu làm 141 thẻ `Mã thô` nuốt mất dòng trống
                # phía trên (chat_contract.py:8 và 5 chỗ khác).
                dau = getattr(cu, "leading_lines", None)
                if len(m.body) == 1:
                    n0 = m.body[0]
                    return (n0.with_changes(leading_lines=dau)
                            if dau is not None and hasattr(n0, "leading_lines")
                            else n0)
                ds = list(m.body)
                if dau is not None and ds and hasattr(ds[0], "leading_lines"):
                    ds[0] = ds[0].with_changes(leading_lines=dau)
                return cst.FlattenSentinel(ds)
            return super().on_leave(cu, moi)

    return ban_ghi._mod.visit(_VaTho(thuong)).code.encode("utf-8")


# ------------------------------------------------- cho bộ đo dùng chung

def sinh_dong_the_don(nut_the: TheNode, indent_level: int = 0) -> str:
    """Dòng mà thẻ này TẢ LẠI được từ nguồn.

    Ở đây thẻ không dựng lại dòng để lưu (lưu đi qua cây), nên hàm này chỉ
    phục vụ bộ đo: nó trả về đúng đoạn nguồn mà thẻ đang cầm. Cửa 4 vì thế đo
    được cùng một câu hỏi trên cả hai bộ: "thẻ có tả đúng nguồn không".
    """
    if nut_the.ma == "ma_tho":
        return nut_the.o.get("nguyen_van", nut_the.raw_text or "")
    return nut_the.o.get("__nguon__", "")


def _bang_chu_thich(nguon: str) -> Dict[int, str]:
    """Bảng {số dòng -> chú thích cuối dòng}, dùng cho bộ đo đối chiếu."""
    dong = nguon.splitlines()
    ra: Dict[int, str] = {}
    try:
        for t in tokenize.generate_tokens(io.StringIO(nguon).readline):
            if t.type == tokenize.COMMENT and dong[t.start[0] - 1][:t.start[1]].strip():
                ra[t.start[0]] = dong[t.start[0] - 1][t.start[1]:]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return {}
    return ra
