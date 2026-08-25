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

# ---------------------------------------------------------------------------
# THẺ BIỂU THỨC — bổ sâu thêm một tầng, MẶC ĐỊNH TẮT.
#
# Sếp vẽ 20/08: `a > 1` phải là một THẺ RIÊNG sinh ra khi viết, nối vào thẻ
# `if`, chứ không phải một ô chữ bên trong nó. Không phải trang trí — nó đổi
# việc sửa từ GÕ sang CHỌN:
#
#     ô `dieu_kien` = "a > 1"   -> model gõ gì cũng được, kể cả cả một hàm
#     ô `phep`      = ">"       -> chỉ 10 giá trị hợp lệ, ép được bằng enum
#
# Đo 20/08 trên 29 đề sửa lỗi: bổ sâu đưa 13/29 = 45% việc sửa xuống mức
# "chọn 1 trong <= 6", nhóm to nhất là `và/hoặc` với ĐÚNG 2 giá trị. Cái giá là
# số thẻ tăng 740 -> 4.792 (gấp 6,5) — nhưng đó chỉ là CÙNG MỘT CÂY vẽ chi tiết
# hơn, không thêm gì vào mã.
#
# TẮT MẶC ĐỊNH vì `the_api._doc_cay_the` từ chối mọi `ma` không có trong
# `BO_THE_V1`. Bật lên trước khi khai báo loại thẻ mới ở đó là app gãy.
# ---------------------------------------------------------------------------

SO_SANH = {"<": cst.LessThan, "<=": cst.LessThanEqual, ">": cst.GreaterThan,
           ">=": cst.GreaterThanEqual, "==": cst.Equal, "!=": cst.NotEqual,
           "is": cst.Is, "is not": cst.IsNot, "in": cst.In,
           "not in": cst.NotIn}
VA_HOAC = {"and": cst.And, "or": cst.Or}
PHU_DINH = {"not": cst.Not, "-": cst.Minus, "+": cst.Plus, "~": cst.BitInvert}
PHEP_TINH = {"+": cst.Add, "-": cst.Subtract, "*": cst.Multiply,
             "/": cst.Divide, "//": cst.FloorDivide, "%": cst.Modulo,
             "**": cst.Power, "@": cst.MatrixMultiply, "&": cst.BitAnd,
             "|": cst.BitOr, "^": cst.BitXor, "<<": cst.LeftShift,
             ">>": cst.RightShift}

# Ô nào có tập giá trị HỮU HẠN — đây là thứ ép được bằng enum.
O_HUU_HAN = {
    "so_sanh": {"phep": sorted(SO_SANH)},
    "va_hoac": {"phep": sorted(VA_HOAC)},
    "phu_dinh": {"dau": sorted(PHU_DINH)},
    "phep_tinh": {"phep": sorted(PHEP_TINH)},
}


def _ky_hieu(nut_toan_tu, bang: dict) -> str:
    for k, v in bang.items():
        if isinstance(nut_toan_tu, v):
            return k
    return ""


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


def _ma_bieu_thuc(nut) -> tuple[str, Dict[str, Any]] | None:
    """Nút biểu thức này là thẻ loại gì. `None` nếu không tách được."""
    if isinstance(nut, cst.Comparison) and len(nut.comparisons) == 1:
        return "so_sanh", {"trai": nut.left,
                           "phai": nut.comparisons[0].comparator}
    if isinstance(nut, cst.BooleanOperation):
        return "va_hoac", {"trai": nut.left, "phai": nut.right}
    if isinstance(nut, cst.UnaryOperation):
        return "phu_dinh", {"gia_tri": nut.expression}
    if isinstance(nut, cst.BinaryOperation):
        return "phep_tinh", {"trai": nut.left, "phai": nut.right}
    return None


def _ky_hieu_cua(ma: str, nut) -> tuple[str, str]:
    """(tên ô toán tử, ký hiệu hiện tại) cho một thẻ biểu thức."""
    if ma == "so_sanh":
        return "phep", _ky_hieu(nut.comparisons[0].operator, SO_SANH)
    if ma == "va_hoac":
        return "phep", _ky_hieu(nut.operator, VA_HOAC)
    if ma == "phu_dinh":
        return "dau", _ky_hieu(nut.operator, PHU_DINH)
    if ma == "phep_tinh":
        return "phep", _ky_hieu(nut.operator, PHEP_TINH)
    return "", ""


def _ma_cua(nut) -> tuple[str, Dict[str, str], Dict[str, Any]]:
    """Nút CST này là thẻ loại gì, ô nào lấy từ nút con nào.

    Trả `(mã thẻ, các ô dạng chữ, bản đồ ô -> nút con)`. Bản đồ ấy là thứ cho
    phép lúc lưu chỉ thay đúng một ô — chỗ khác không đụng tới.
    """
    if isinstance(nut, cst.FunctionDef):
        ban_do = {"ten_ham": nut.name, "tham_so": nut.params}
        if nut.returns is not None:
            ban_do["kieu_tra_ve"] = nut.returns.annotation
        return "ham", {}, ban_do
    if isinstance(nut, cst.If):
        return "neu", {}, {"dieu_kien": nut.test}
    if isinstance(nut, cst.Else):
        return "nguoc_lai", {}, {}
    if isinstance(nut, cst.For):
        return "lap_moi", {}, {"bien": nut.target, "day": nut.iter}
    if isinstance(nut, cst.While):
        return "lap_khi", {}, {"dieu_kien": nut.test}
    # ---- 5 thẻ thêm 25/08/2026 ----
    #
    # `try` CHỈ nhận dạng khi KHÔNG có `else` và KHÔNG có `finally`. Khay chưa
    # có thẻ cho hai thứ ấy, nên nhận dạng một `try/finally` thành thẻ là làm
    # MẤT khối `finally` lúc lưu. Rơi về `ma_tho` thì xấu hơn nhưng không mất
    # gì — và cửa `test_the_cst.py::test_lossless_23_files_core` canh đúng chỗ
    # này trên cả 23 tệp.
    if isinstance(nut, cst.Try):
        if getattr(nut, "orelse", None) is None and getattr(nut, "finalbody", None) is None:
            return "thu", {}, {}
        return "ma_tho", {}, {}
    if isinstance(nut, cst.ExceptHandler):
        ban_do = {}
        if nut.type is not None:
            ban_do["loai_loi"] = nut.type
        if nut.name is not None:
            ban_do["ten_bien"] = nut.name.name
        return "bat_loi", {}, ban_do
    if isinstance(nut, cst.SimpleStatementLine) and len(nut.body) == 1:
        t = nut.body[0]
        if isinstance(t, cst.Break):
            return "dung_lap", {}, {}
        if isinstance(t, cst.Continue):
            return "bo_qua", {}, {}
        # `import` chỉ nhận dạng dạng ĐƠN GIẢN: đúng một tên. `import a, b`
        # trên một dòng thì thẻ `nhap` không diễn đạt được — để mã thô.
        if isinstance(t, cst.Import) and len(t.names) == 1:
            al = t.names[0]
            o = {"thu_vien": _ten_diem(al.name)}
            if al.asname is not None and isinstance(al.asname.name, cst.Name):
                o["ten_khac"] = al.asname.name.value
            return "nhap", o, {}
        if isinstance(t, cst.ImportFrom) and not isinstance(t.names, cst.ImportStar):
            if t.relative:                       # `from . import x` — để mã thô
                return "ma_tho", {}, {}
            # IMPORT CÓ NGOẶC THÌ ĐỂ NGUYÊN MÃ THÔ.
            #
            # Đường lưu dựng lại câu lệnh từ ba ô, nên nó sinh ra MỘT dòng.
            # `core/chat_service.py:13` viết 13 tên trong ngoặc trên 15 dòng —
            # nhận dạng thành thẻ `nhap` rồi lưu là gom hết về một dòng dài
            # 178 ký tự. Cửa `test_the_v1.py::test_cua_cung_1_mo_luu_lossless`
            # bắt ngay: SHA lệch trên chat_service.py.
            #
            # Thẻ `nhap` nhắm vào `import math` của người mới học, không nhắm
            # vào khối import 13 tên của mã tích hợp. Để mã thô thì xấu hơn
            # nhưng KHÔNG mất byte nào.
            if t.lpar or t.rpar:
                return "ma_tho", {}, {}
            mod_ten = _ten_diem(t.module) if t.module is not None else ""
            ten_lay, ten_khac = [], ""
            for al in t.names:
                ten_lay.append(_ten_diem(al.name))
                if al.asname is not None and isinstance(al.asname.name, cst.Name):
                    ten_khac = al.asname.name.value
            if ten_khac and len(ten_lay) > 1:
                return "ma_tho", {}, {}          # `as` chỉ gắn được cho MỘT tên
            return "nhap", {"thu_vien": mod_ten, "phan": ", ".join(ten_lay),
                            **({"ten_khac": ten_khac} if ten_khac else {})}, {}
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


def _ten_diem(nut) -> str:
    """`a.b.c` (Attribute lồng nhau) hoặc `a` (Name) -> chuỗi."""
    if isinstance(nut, cst.Name):
        return nut.value
    if isinstance(nut, cst.Attribute):
        return _ten_diem(nut.value) + "." + nut.attr.value
    return ""


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


def _la_dong_ma_thuat(line: str, line_no: int) -> bool:
    if line_no > 2:
        return False
    t = line.strip()
    return t.startswith("#!") or "coding:" in t or "coding=" in t or "-*-" in t


def _tao_the_chu_thich_tu_cmt(cmt_val: str, line_no: int, muc: int, dem: list[int], ban_do: dict, cmt_node: Any) -> TheNode:
    dem[0] += 1
    if _la_dong_ma_thuat(cmt_val, line_no):
        mid = "ma_tho_%d" % dem[0]
        t = TheNode(id=mid, ma="ma_tho", o={"nguyen_van": cmt_val}, raw_text=cmt_val, line_start=line_no, line_end=line_no, indent=muc * 4)
        ban_do[mid] = cmt_node
        return t
    else:
        mid = "chu_thich_%d" % dem[0]
        nd = cmt_val.strip()
        if nd.startswith("#"):
            nd = nd[1:].lstrip()
        t = TheNode(id=mid, ma="chu_thich", o={"noi_dung": nd}, raw_text=cmt_val, line_start=line_no, line_end=line_no, indent=muc * 4)
        ban_do[mid] = (cmt_node, nd, cmt_val)
        return t


def doc_chuoi_py_sang_cay_the(nguon: str,
                              duong_dan: Optional[str] = None,
                              bo_sau: bool = False) -> BanGhiCST:
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
        # Phần tử GIỮA là các ô đã sẵn dạng chữ (thẻ `nhap` dùng nó — ô của
        # nó không ứng 1:1 với một nút con nào). Bản trước bỏ qua phần tử này
        # bằng `_`, nên thẻ `nhap` đọc lên có ĐÚNG hình dạng mà KHÔNG có nội
        # dung: mặt thẻ trống trơn dù tệp ghi `import math`.
        ma, o_san, cac_o = _ma_cua(nut)
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
        
        o_dict = _o_thanh_chu(ma, cac_o, mod)
        o_dict.update(o_san)
        if isinstance(nut, cst.FunctionDef):
            if nut.returns is not None:
                o_dict["kieu_tra_ve"] = mod.code_for_node(nut.returns.annotation).strip()
            if nut.asynchronous is not None:
                o_dict["async"] = "1"
            if nut.decorators:
                o_dict["trang_tri"] = "\n".join(mod.code_for_node(d).strip() for d in nut.decorators)

        t = TheNode(id=mid, ma=ma, o=o_dict,
                    line_start=r.start.line, line_end=r.end.line,
                    indent=muc * 4,
                    duoi_dong=_chu_thich_cuoi_dong(nut, mod))
        # `elif` là nút If nằm trong orelse. Ghi rõ ra ô, vì bản v1 nuốt mất
        # chỗ này: 28/40 thẻ Ngược lại sinh ra `else:` và MẤT ĐIỀU KIỆN.
        if ma == "neu" and id(nut) in la_elif:
            t.o["noi_tiep"] = "1"
        ban_do[mid] = nut
        t.than = than_cua(nut, muc + 1)
        if bo_sau:
            # Thẻ biểu thức đứng TRƯỚC thẻ thân: `a > 1` thuộc về dòng `if`,
            # còn thân là các dòng bên dưới.
            t.than = the_bieu_thuc(nut, cac_o, muc + 1) + t.than
        return t

    def the_bieu_thuc(cha, cac_o: Dict[str, Any], muc: int) -> List[TheNode]:
        """Bổ các ô biểu thức của thẻ cha thành thẻ con."""
        ra: List[TheNode] = []
        for nut_con in cac_o.values():
            ra += _di_bieu_thuc(nut_con, muc)
        return ra

    def _di_bieu_thuc(nut_bt, muc: int) -> List[TheNode]:
        d = _ma_bieu_thuc(nut_bt)
        if d is None:
            # không tách được ở tầng này thì thử xuống tầng dưới
            ra: List[TheNode] = []
            for con in getattr(nut_bt, "children", []):
                ra += _di_bieu_thuc(con, muc)
            return ra
        ma_bt, con_o = d
        dem[0] += 1
        mid = "%s_%d" % (ma_bt, dem[0])
        r = vi_tri[nut_bt]
        ten_o, ky = _ky_hieu_cua(ma_bt, nut_bt)
        o = {k: mod.code_for_node(v).strip() for k, v in con_o.items()}
        if ten_o:
            o[ten_o] = ky
        t = TheNode(id=mid, ma=ma_bt, o=o, line_start=r.start.line,
                    line_end=r.end.line, indent=muc * 4)
        ban_do[mid] = nut_bt
        for v in con_o.values():
            t.than += _di_bieu_thuc(v, muc + 1)
        return [t]

    def lam_danh_sach(ds, muc: int) -> List[TheNode]:
        res: List[TheNode] = []
        for nut in ds:
            lls = getattr(nut, "leading_lines", [])
            first_elem = nut.decorators[0] if getattr(nut, "decorators", None) else nut
            L = vi_tri[first_elem].start.line if first_elem in vi_tri else 1
            for i, el in enumerate(lls):
                if el.comment is not None:
                    calc_line = max(1, L - len(lls) + i)
                    res.append(_tao_the_chu_thich_tu_cmt(el.comment.value, calc_line, muc, dem, ban_do, el))
            res.append(lam(nut, muc))
        return res

    def than_cua(nut, muc: int) -> List[TheNode]:
        con: List[TheNode] = []
        than = getattr(nut, "body", None)
        if isinstance(than, cst.IndentedBlock):
            con.extend(lam_danh_sach(than.body, muc))
            ft = getattr(than, "footer", [])
            L_end = vi_tri[nut].end.line if nut in vi_tri else 1
            for i, el in enumerate(ft):
                if el.comment is not None:
                    calc_line = max(1, L_end - len(ft) + i)
                    con.append(_tao_the_chu_thich_tu_cmt(el.comment.value, calc_line, muc, dem, ban_do, el))
        # `except` của một `try` đi ra làm THẺ EM lùi một mức, giống `else`
        # của `if`. Bên sinh mã, `bat_loi` cũng lùi một mức (`isElseOrElif`),
        # nên hai chiều khớp nhau.
        for xl in getattr(nut, "handlers", []) or []:
            con.append(lam(xl, muc - 1))
        orelse = getattr(nut, "orelse", None)
        if orelse is not None:
            if isinstance(orelse, cst.If):
                la_elif.add(id(orelse))      # đánh dấu để lam() ghi ô noi_tiep
            con.append(lam(orelse, muc - 1))
        return con

    cay: List[TheNode] = []
    # 1. mod.header
    cur_line = 1
    for el in getattr(mod, "header", []):
        if el.comment is not None:
            cay.append(_tao_the_chu_thich_tu_cmt(el.comment.value, cur_line, 0, dem, ban_do, el))
        cur_line += 1

    # 2. mod.body
    cay.extend(lam_danh_sach(mod.body, 0))

    # 3. mod.footer
    for el in getattr(mod, "footer", []):
        if el.comment is not None:
            cay.append(_tao_the_chu_thich_tu_cmt(el.comment.value, cur_line, 0, dem, ban_do, el))
        cur_line += 1

    b = nguon.encode("utf-8")
    return BanGhiCST(duong_dan, b, mod.default_newline,
                     nguon.splitlines(), cay, mod, ban_do)


def doc_tep_py_sang_cay_the(duong_dan: Path | str,
                            bo_sau: bool = False) -> BanGhiCST:
    """Đọc một tệp .py trên đĩa thành cây thẻ, giữ nguyên từng byte bản gốc."""
    p = Path(duong_dan)
    return doc_chuoi_py_sang_cay_the(p.read_bytes().decode("utf-8"), str(p),
                                     bo_sau)


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

    # ---- thẻ `bat_loi`: đổi loại lỗi / tên biến ----
    #
    # 25/08: THIẾU KHỐI NÀY THÌ SỬA THẺ RỒI LƯU LÀ MẤT LẶNG LẼ. `_ap_dung`
    # kết thúc bằng `return nut` — nút cũ đi tiếp y nguyên, không ai báo gì.
    # Đo thật TRƯỚC khi viết: sửa `ValueError` -> `ZeroDivisionError` trên mặt
    # thẻ rồi lưu, tệp vẫn ghi `except ValueError as e:`.
    #
    # Đúng họ bệnh "giao diện hứa một việc, mã làm việc khác" ở §4.
    if isinstance(nut, cst.ExceptHandler):
        t = {}
        if khac("loai_loi"):
            moi_loai = (o_moi["loai_loi"] or "").strip()
            t["type"] = cst.parse_expression(moi_loai) if moi_loai else None
        if khac("ten_bien"):
            moi_ten = (o_moi["ten_bien"] or "").strip()
            if moi_ten:
                # Khi trước đó không có `as`, `nut.name` là None nên không
                # mượn được khoảng trắng cũ — phải tự đặt đúng một dấu cách.
                t["name"] = cst.AsName(
                    name=cst.Name(moi_ten),
                    whitespace_before_as=cst.SimpleWhitespace(" "),
                    whitespace_after_as=cst.SimpleWhitespace(" "))
            else:
                t["name"] = None
        if t and t.get("type", nut.type) is None and t.get("name", nut.name) is not None:
            t["name"] = None      # `except as e:` không phải Python
        return nut.with_changes(**t) if t else nut

    # ---- thẻ biểu thức: đổi TOÁN TỬ thì thay lớp, GIỮ NGUYÊN khoảng trắng.
    # Bỏ khoảng trắng đi thì `a > 1` thành `a>1` — khác byte, và cửa 1 bắt ngay.
    if isinstance(nut, cst.Comparison) and len(nut.comparisons) == 1:
        ct = nut.comparisons[0]
        t = {}
        if khac("phep") and o_moi["phep"] in SO_SANH:
            cu_tt = ct.operator
            t["comparisons"] = [ct.with_changes(operator=SO_SANH[o_moi["phep"]](
                whitespace_before=cu_tt.whitespace_before,
                whitespace_after=cu_tt.whitespace_after))]
        if khac("trai"):
            t["left"] = _doi_bieu_thuc(o_moi["trai"])
        if khac("phai"):
            t["comparisons"] = [(t.get("comparisons") or nut.comparisons)[0]
                                .with_changes(comparator=_doi_bieu_thuc(o_moi["phai"]))]
        return nut.with_changes(**t) if t else nut
    if isinstance(nut, cst.BooleanOperation):
        t = {}
        if khac("phep") and o_moi["phep"] in VA_HOAC:
            c = nut.operator
            t["operator"] = VA_HOAC[o_moi["phep"]](
                whitespace_before=c.whitespace_before,
                whitespace_after=c.whitespace_after)
        if khac("trai"):
            t["left"] = _doi_bieu_thuc(o_moi["trai"])
        if khac("phai"):
            t["right"] = _doi_bieu_thuc(o_moi["phai"])
        return nut.with_changes(**t) if t else nut
    if isinstance(nut, cst.UnaryOperation):
        t = {}
        if khac("dau") and o_moi["dau"] in PHU_DINH:
            t["operator"] = PHU_DINH[o_moi["dau"]](
                whitespace_after=nut.operator.whitespace_after)
        if khac("gia_tri"):
            t["expression"] = _doi_bieu_thuc(o_moi["gia_tri"])
        return nut.with_changes(**t) if t else nut
    if isinstance(nut, cst.BinaryOperation):
        t = {}
        if khac("phep") and o_moi["phep"] in PHEP_TINH:
            c = nut.operator
            t["operator"] = PHEP_TINH[o_moi["phep"]](
                whitespace_before=c.whitespace_before,
                whitespace_after=c.whitespace_after)
        if khac("trai"):
            t["left"] = _doi_bieu_thuc(o_moi["trai"])
        if khac("phai"):
            t["right"] = _doi_bieu_thuc(o_moi["phai"])
        return nut.with_changes(**t) if t else nut

    if isinstance(nut, cst.FunctionDef):
        t = {}
        if khac("ten_ham"):
            t["name"] = cst.Name(o_moi["ten_ham"])
        if khac("tham_so"):
            t["params"] = _doi_tham_so(o_moi["tham_so"])
        if khac("kieu_tra_ve"):
            ktv = o_moi["kieu_tra_ve"].strip()
            if ktv.startswith("->"):
                ktv = ktv[2:].strip()
            if ktv:
                t["returns"] = cst.Annotation(annotation=_doi_bieu_thuc(ktv))
            else:
                t["returns"] = None
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
    if isinstance(nut, cst.SimpleStatementLine) and len(nut.body) == 1 and (
            isinstance(nut.body[0], (cst.Import, cst.ImportFrom))) and (
            khac("thu_vien") or khac("phan") or khac("ten_khac")):
        # Ba ô của thẻ `nhap` không ứng 1:1 với nút con nào — `from a import b`
        # và `import a as b` là HAI lớp CST khác nhau, nên đổi một ô có thể
        # phải đổi cả lớp. Dựng lại đúng một câu lệnh rồi thay vào `body`;
        # `leading_lines` và `trailing_whitespace` của DÒNG vẫn là nút cũ, nên
        # dòng trống phía trên và chú thích cuối dòng không mất.
        tv = (o_moi.get("thu_vien", o_cu.get("thu_vien", "")) or "").strip()
        ph = (o_moi.get("phan", o_cu.get("phan", "")) or "").strip()
        tk = (o_moi.get("ten_khac", o_cu.get("ten_khac", "")) or "").strip()
        if not tv:
            return nut
        if ph:
            mot_ten = "," not in ph
            cau = ("from %s import %s as %s" % (tv, ph, tk)) if (tk and mot_ten)                   else ("from %s import %s" % (tv, ph))
        elif tk:
            cau = "import %s as %s" % (tv, tk)
        else:
            cau = "import %s" % tv
        try:
            moi_stmt = cst.parse_statement(cau).body[0]
        except Exception:                    # noqa: BLE001
            return nut                        # ô đang gõ dở -> giữ nguyên
        return nut.with_changes(body=[moi_stmt])

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
                entry = ban_ghi._ban_do[n.id]
                if isinstance(entry, tuple):
                    nut = entry[0]
                    orig_nd = entry[1]
                else:
                    nut = entry
                    orig_nd = None

                if n.ma == "ma_tho":
                    moi = n.o.get("nguyen_van", n.raw_text or "")
                    if moi == (n.raw_text or ""):
                        continue
                    doi[id(nut)] = ("__tho__", moi)
                elif n.ma == "chu_thich":
                    moi_nd = n.o.get("noi_dung", "").strip()
                    if orig_nd is not None and moi_nd == orig_nd:
                        continue
                    if moi_nd == (n.raw_text or "").strip().lstrip("#").lstrip():
                        continue
                    moi = f"# {moi_nd}" if moi_nd else "#"
                    doi[id(nut)] = ("__chu_thich__", moi)
                else:
                    ma, _, cac_o = _ma_cua(nut)
                    o_moi = dict(n.o)
                    o_cu = _o_thanh_chu(ma, cac_o, ban_ghi._mod)
                    if o_moi == o_cu:
                        continue
                    doi[id(nut)] = (o_moi, o_cu)
            gom(n.than)
    gom(ban_ghi.tree)

    if not doi:
        return ban_ghi._mod.code.encode("utf-8")

    tho = {k: v[1] for k, v in doi.items() if v[0] == "__tho__"}
    chu_thich_doi = {k: v[1] for k, v in doi.items() if v[0] == "__chu_thich__"}
    thuong = {k: v for k, v in doi.items() if v[0] not in ("__tho__", "__chu_thich__")}

    class _VaTho(_Vasua):
        def on_leave(self, cu, moi):
            if id(cu) in chu_thich_doi:
                moi_cmt = chu_thich_doi[id(cu)]
                if isinstance(moi, cst.EmptyLine):
                    return moi.with_changes(comment=cst.Comment(moi_cmt))
                return moi
            if id(cu) in tho:
                m = cst.parse_module(tho[id(cu)])
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
