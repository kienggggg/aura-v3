# -*- coding: utf-8 -*-
"""the_v1.py — Bộ lõi hệ thống Lập trình bằng THẺ (bản v1).

Thiết kế theo chuẩn AURA v3 và chỉ đạo của Sếp (19/08/2026):
1. 11 thẻ: 10 thẻ ngôn ngữ cố định + 1 thẻ Mã Thô (`ma_tho`, màu xám #6B7280).
2. CỬA CỨNG 1: Mở tệp .py bất kỳ -> Lưu -> Giữ nguyên 100% byte gốc (SHA-256 khớp).
3. CỬA CỨNG 2: Sửa 1 ô -> Giữ nguyên chú thích cuối dòng (cắt bằng end_col_offset) và
   không đổi các dòng còn lại.
4. Kiểm tra tĩnh: 5 lỗi ĐỎ (lỗi cứng) và 4 cảnh báo VÀNG (rủi ro).
5. Thực thi: Tiến trình riêng + trần giờ 5.0s.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Whitelist các tên hàm / hằng số dựng sẵn phổ biến của Python (tránh báo lỗi biến chưa gán)
BUILTIN_SYMBOLS: Set[str] = {
    "True", "False", "None", "range", "len", "int", "str", "float", "list",
    "dict", "set", "tuple", "sum", "min", "max", "abs", "round", "bool",
    "print", "input", "enumerate", "zip", "sorted", "reversed", "map", "filter",
    "open", "type", "isinstance", "issubclass", "iter", "next", "all", "any",
    "chr", "ord", "hex", "bin", "oct", "pow", "divmod", "format", "repr",
}

# 5 Nhóm thẻ với màu sắc chuẩn (Tuyệt đối không dùng Đỏ #EF4444 và Vàng #EAB308)
NHOM_THE: Dict[str, Dict[str, str]] = {
    "dieu_khien": {"ten": "Điều khiển", "mau": "#3B82F6"},  # Xanh dương
    "du_lieu": {"ten": "Dữ liệu", "mau": "#10B981"},        # Xanh lá
    "vao_ra": {"ten": "Vào / Ra", "mau": "#8B5CF6"},        # Tím
    "ham": {"ten": "Hàm", "mau": "#F59E0B"},               # Cam / Amber
    "ma_tho": {"ten": "Mã thô", "mau": "#6B7280"},          # Xám
}


@dataclass(frozen=True)
class ODefinition:
    ten: str
    kieu: str
    bat_buoc: bool = True
    goi_y: str = ""


@dataclass(frozen=True)
class TheDefinition:
    ma: str
    ten: str
    nhom: str
    o: List[ODefinition]
    co_than: bool
    mau: str


# 11 Thẻ chuẩn của v1
BO_THE_V1: Dict[str, TheDefinition] = {
    "gan": TheDefinition(
        ma="gan",
        ten="Gán",
        nhom="du_lieu",
        o=[
            ODefinition(ten="ten_bien", kieu="chu", bat_buoc=True, goi_y="x"),
            ODefinition(ten="gia_tri", kieu="bieu_thuc", bat_buoc=True, goi_y="10"),
        ],
        co_than=False,
        mau=NHOM_THE["du_lieu"]["mau"],
    ),
    "in_ra": TheDefinition(
        ma="in_ra",
        ten="In ra",
        nhom="vao_ra",
        o=[
            ODefinition(ten="noi_dung", kieu="bieu_thuc", bat_buoc=True, goi_y='"Xin chào"'),
        ],
        co_than=False,
        mau=NHOM_THE["vao_ra"]["mau"],
    ),
    "neu": TheDefinition(
        ma="neu",
        ten="Nếu",
        nhom="dieu_khien",
        o=[
            ODefinition(ten="dieu_kien", kieu="bieu_thuc", bat_buoc=True, goi_y="x > 0"),
        ],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "nguoc_lai": TheDefinition(
        ma="nguoc_lai",
        ten="Ngược lại",
        nhom="dieu_khien",
        o=[],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "lap_moi": TheDefinition(
        ma="lap_moi",
        ten="Lặp mỗi",
        nhom="dieu_khien",
        o=[
            ODefinition(ten="bien", kieu="chu", bat_buoc=True, goi_y="i"),
            ODefinition(ten="day", kieu="bieu_thuc", bat_buoc=True, goi_y="range(10)"),
        ],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "lap_khi": TheDefinition(
        ma="lap_khi",
        ten="Lặp khi",
        nhom="dieu_khien",
        o=[
            ODefinition(ten="dieu_kien", kieu="bieu_thuc", bat_buoc=True, goi_y="x > 0"),
        ],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "tra_ve": TheDefinition(
        ma="tra_ve",
        ten="Trả về",
        nhom="ham",
        o=[
            ODefinition(ten="gia_tri", kieu="bieu_thuc", bat_buoc=True, goi_y="x + 1"),
        ],
        co_than=False,
        mau=NHOM_THE["ham"]["mau"],
    ),
    "ham": TheDefinition(
        ma="ham",
        ten="Định nghĩa hàm",
        nhom="ham",
        o=[
            ODefinition(ten="ten_ham", kieu="chu", bat_buoc=True, goi_y="tinh_tong"),
            ODefinition(ten="tham_so", kieu="chu", bat_buoc=False, goi_y="a, b"),
        ],
        co_than=True,
        mau=NHOM_THE["ham"]["mau"],
    ),
    "goi_ham": TheDefinition(
        ma="goi_ham",
        ten="Gọi hàm",
        nhom="ham",
        o=[
            ODefinition(ten="ten_ham", kieu="chu", bat_buoc=True, goi_y="tinh_tong"),
            ODefinition(ten="doi_so", kieu="chu", bat_buoc=False, goi_y="1, 2"),
        ],
        co_than=False,
        mau=NHOM_THE["ham"]["mau"],
    ),
    "pheptinh": TheDefinition(
        ma="pheptinh",
        ten="Phép tính",
        nhom="du_lieu",
        o=[
            ODefinition(ten="trai", kieu="bieu_thuc", bat_buoc=True, goi_y="a"),
            ODefinition(ten="phep", kieu="chu", bat_buoc=True, goi_y="+"),
            ODefinition(ten="phai", kieu="bieu_thuc", bat_buoc=True, goi_y="b"),
        ],
        co_than=False,
        mau=NHOM_THE["du_lieu"]["mau"],
    ),
    "ma_tho": TheDefinition(
        ma="ma_tho",
        ten="Mã thô",
        nhom="ma_tho",
        o=[
            ODefinition(ten="nguyen_van", kieu="chu_nhieu_dong", bat_buoc=True, goi_y=""),
        ],
        co_than=False,
        mau=NHOM_THE["ma_tho"]["mau"],
    ),
}


@dataclass
class TheNode:
    id: str
    ma: str
    o: Dict[str, str] = field(default_factory=dict)
    than: List[TheNode] = field(default_factory=list)
    # Metadata vị trí trong file nguồn (cho lossless round-trip & span splicing)
    line_start: Optional[int] = None  # 1-indexed
    line_end: Optional[int] = None    # 1-indexed, inclusive
    indent: int = 0
    duoi_dong: str = ""               # Đoạn text từ sau câu lệnh đến hết dòng (kể cả comment)
    raw_text: Optional[str] = None    # Lưu nguyên văn text nếu là ma_tho hoặc file gốc
    da_sua: bool = False              # Đánh dấu thẻ này có bị người dùng sửa hay không

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "id": self.id,
            "ma": self.ma,
            "o": dict(self.o),
            "than": [child.to_dict() for child in self.than],
            "da_sua": self.da_sua,
        }
        if self.line_start is not None:
            res["vi_tri"] = {
                "line_start": self.line_start,
                "line_end": self.line_end,
                "indent": self.indent,
                "duoi_dong": self.duoi_dong,
            }
        if self.raw_text is not None and self.ma == "ma_tho":
            res["raw_text"] = self.raw_text
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TheNode:
        vi_tri = data.get("vi_tri", {})
        da_sua = bool(data.get("da_sua", False) or vi_tri.get("da_sua", False))
        return cls(
            id=str(data.get("id", "")),
            ma=str(data.get("ma", "")),
            o={k: str(v) for k, v in data.get("o", {}).items()},
            than=[cls.from_dict(item) for item in data.get("than", [])],
            line_start=vi_tri.get("line_start"),
            line_end=vi_tri.get("line_end"),
            indent=vi_tri.get("indent", 0),
            duoi_dong=vi_tri.get("duoi_dong", ""),
            raw_text=data.get("raw_text"),
            da_sua=da_sua,
        )


@dataclass
class FileSourceRecord:
    duong_dan: Optional[str]
    raw_bytes: bytes
    newline: str                       # "\n" hoặc "\r\n"
    lines: List[str]                   # Danh sách dòng không chứa newline
    tree: List[TheNode]
    has_modifications: bool = False


# ==============================================================================
# 1. BỘ PHÂN TÍCH AST & MỞ TỆP .PY SANG CÂY THẺ (LOSSLESS SPAN TRACKING)
# ==============================================================================

def _tach_dong_va_newline(raw_bytes: bytes) -> Tuple[List[str], str]:
    """Tách bytes thành danh sách dòng và phát hiện kiểu xuống dòng gốc."""
    text = raw_bytes.decode("utf-8", errors="replace")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    return lines, newline


def _trich_duoi_dong(line: str, end_col: Optional[int]) -> str:
    """Trích xuất duoi_dong bằng end_col_offset của AST.
    
    Cực kỳ quan trọng (Mục 15):
    Trong CPython AST, col_offset và end_col_offset là UTF-8 BYTE OFFSET tính từ
    đầu dòng (chứ không phải character offset). Nếu dòng chứa ký tự Unicode đa byte
    (như tiếng Việt, em-dash), phải cắt trên chuỗi bytes UTF-8 rồi mới decode lại.
    """
    if end_col is None or end_col < 0:
        return ""
    line_bytes = line.encode("utf-8")
    if end_col >= len(line_bytes):
        return ""
    duoi_bytes = line_bytes[end_col:]
    return duoi_bytes.decode("utf-8", errors="replace")


def _tao_id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx}_{int(time.time() * 1000) % 1000000}"


def _phan_tich_ast_statement(
    node: ast.AST,
    lines: List[str],
    full_source: str,
    counter: List[int],
) -> Optional[TheNode]:
    """Cố gắng chuyển một AST statement sang 1 trong 10 thẻ chuẩn.
    Nếu không khớp, trả về None để caller chuyển thành thẻ `ma_tho`.
    """
    counter[0] += 1
    node_id = _tao_id("the", counter[0])
    l_start = getattr(node, "lineno", 1)
    l_end = getattr(node, "end_lineno", l_start)
    col_offset = getattr(node, "col_offset", 0)
    end_col = getattr(node, "end_col_offset", None)
    
    line_text = lines[l_start - 1] if 0 <= l_start - 1 < len(lines) else ""
    duoi_dong = _trich_duoi_dong(line_text, end_col) if l_start == l_end else ""
    indent = col_offset

    # 1. Gán: x = 10
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        target_name = node.targets[0].id
        val_seg = ast.get_source_segment(full_source, node.value) or ""
        return TheNode(
            id=node_id,
            ma="gan",
            o={"ten_bien": target_name, "gia_tri": val_seg},
            than=[],
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 2. In ra: print(...)
    if (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "print"
    ):
        call_node = node.value
        args_text = ""
        if call_node.args:
            seg = ast.get_source_segment(full_source, call_node)
            if seg and "(" in seg and seg.endswith(")"):
                args_text = seg[seg.find("(") + 1 : -1].strip()
        return TheNode(
            id=node_id,
            ma="in_ra",
            o={"noi_dung": args_text},
            than=[],
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 3. Trả về: return x
    if isinstance(node, ast.Return):
        val_seg = ""
        if node.value is not None:
            val_seg = ast.get_source_segment(full_source, node.value) or ""
        return TheNode(
            id=node_id,
            ma="tra_ve",
            o={"gia_tri": val_seg},
            than=[],
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 4. Gọi hàm: func(a, b) (dưới dạng statement biểu thức)
    if (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id != "print"
    ):
        fn_name = node.value.func.id
        call_seg = ast.get_source_segment(full_source, node.value) or ""
        args_text = ""
        if "(" in call_seg and call_seg.endswith(")"):
            args_text = call_seg[call_seg.find("(") + 1 : -1].strip()
        return TheNode(
            id=node_id,
            ma="goi_ham",
            o={"ten_ham": fn_name, "doi_so": args_text},
            than=[],
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 5. Phép tính dạng biểu thức đứng một mình (BinOp)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.BinOp):
        bin_op = node.value
        trai = ast.get_source_segment(full_source, bin_op.left) or ""
        phai = ast.get_source_segment(full_source, bin_op.right) or ""
        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
        }
        phep = op_map.get(type(bin_op.op), "+")
        return TheNode(
            id=node_id,
            ma="pheptinh",
            o={"trai": trai, "phep": phep, "phai": phai},
            than=[],
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 6. Định nghĩa hàm: def fn(a, b):
    if isinstance(node, ast.FunctionDef) and not node.decorator_list:
        fn_name = node.name
        params = [arg.arg for arg in node.args.args]
        body_nodes = _chuyen_danh_sach_ast_sang_the(node.body, lines, full_source, counter)
        return TheNode(
            id=node_id,
            ma="ham",
            o={"ten_ham": fn_name, "tham_so": ", ".join(params)},
            than=body_nodes,
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 7. Lặp mỗi: for i in range(10):
    if isinstance(node, ast.For) and not node.orelse:
        target_str = ast.get_source_segment(full_source, node.target) or ""
        iter_str = ast.get_source_segment(full_source, node.iter) or ""
        body_nodes = _chuyen_danh_sach_ast_sang_the(node.body, lines, full_source, counter)
        return TheNode(
            id=node_id,
            ma="lap_moi",
            o={"bien": target_str, "day": iter_str},
            than=body_nodes,
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 8. Lặp khi: while cond:
    if isinstance(node, ast.While) and not node.orelse:
        cond_str = ast.get_source_segment(full_source, node.test) or ""
        body_nodes = _chuyen_danh_sach_ast_sang_the(node.body, lines, full_source, counter)
        return TheNode(
            id=node_id,
            ma="lap_khi",
            o={"dieu_kien": cond_str},
            than=body_nodes,
            line_start=l_start,
            line_end=l_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )

    # 9 & 10. Nếu và Ngược lại: if cond: ... else: ...
    if isinstance(node, ast.If):
        cond_str = ast.get_source_segment(full_source, node.test) or ""
        body_nodes = _chuyen_danh_sach_ast_sang_the(node.body, lines, full_source, counter)
        
        if_end = getattr(node.body[-1], "end_lineno", l_end) if node.body else l_end
        if_node = TheNode(
            id=node_id,
            ma="neu",
            o={"dieu_kien": cond_str},
            than=body_nodes,
            line_start=l_start,
            line_end=if_end,
            indent=indent,
            duoi_dong=duoi_dong,
        )
        
        if node.orelse:
            counter[0] += 1
            else_id = _tao_id("the", counter[0])
            else_body = _chuyen_danh_sach_ast_sang_the(node.orelse, lines, full_source, counter)
            else_start = getattr(node.orelse[0], "lineno", if_end + 1)
            actual_else_start = else_start
            for check_l in range(if_end + 1, else_start + 1):
                if check_l <= len(lines) and "else:" in lines[check_l - 1]:
                    actual_else_start = check_l
                    break
            else_end = getattr(node.orelse[-1], "end_lineno", l_end)
            else_node = TheNode(
                id=else_id,
                ma="nguoc_lai",
                o={},
                than=else_body,
                line_start=actual_else_start,
                line_end=else_end,
                indent=indent,
                duoi_dong="",
            )
            return [if_node, else_node]  # type: ignore
            
        return if_node

    return None


def _chuyen_danh_sach_ast_sang_the(
    statements: List[ast.stmt],
    lines: List[str],
    full_source: str,
    counter: List[int],
) -> List[TheNode]:
    """Chuyển danh sách statement AST sang danh sách TheNode."""
    res: List[TheNode] = []
    for stmt in statements:
        matched = _phan_tich_ast_statement(stmt, lines, full_source, counter)
        if matched is None:
            counter[0] += 1
            st_l = getattr(stmt, "lineno", 1)
            en_l = getattr(stmt, "end_lineno", st_l)
            stmt_lines = lines[st_l - 1 : en_l]
            text = "\n".join(stmt_lines)
            res.append(
                TheNode(
                    id=_tao_id("matho", counter[0]),
                    ma="ma_tho",
                    o={"nguyen_van": text},
                    than=[],
                    line_start=st_l,
                    line_end=en_l,
                    indent=getattr(stmt, "col_offset", 0),
                    duoi_dong="",
                    raw_text=text,
                )
            )
        elif isinstance(matched, list):
            res.extend(matched)
        else:
            res.append(matched)
    return res


def doc_tep_py_sang_cay_the(duong_dan: Path | str) -> FileSourceRecord:
    """Đọc tệp .py từ đĩa và phân tích thành FileSourceRecord & danh sách TheNode."""
    path = Path(duong_dan).resolve(strict=False)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp .py: {path}")
    raw_bytes = path.read_bytes()
    return doc_chuoi_py_sang_cay_the(raw_bytes, str(path))


def doc_chuoi_py_sang_cay_the(
    raw_bytes: bytes,
    duong_dan: Optional[str] = None
) -> FileSourceRecord:
    """Phân tích chuỗi bytes của file .py thành cây thẻ với bảo toàn span dòng."""
    lines, newline = _tach_dong_va_newline(raw_bytes)
    full_source = raw_bytes.decode("utf-8", errors="replace")

    counter = [0]
    tree_nodes: List[TheNode] = []

    try:
        parsed_ast = ast.parse(full_source)
        current_line = 1
        for stmt in parsed_ast.body:
            st_l = getattr(stmt, "lineno", current_line)
            en_l = getattr(stmt, "end_lineno", st_l)

            # Khoảng trống / chú thích trước stmt
            if st_l > current_line:
                gap_lines = lines[current_line - 1 : st_l - 1]
                gap_text = "\n".join(gap_lines)
                if gap_text.strip() or any(l.strip().startswith("#") for l in gap_lines):
                    counter[0] += 1
                    tree_nodes.append(
                        TheNode(
                            id=_tao_id("matho", counter[0]),
                            ma="ma_tho",
                            o={"nguyen_van": gap_text},
                            than=[],
                            line_start=current_line,
                            line_end=st_l - 1,
                            indent=0,
                            duoi_dong="",
                            raw_text=gap_text,
                        )
                    )

            matched = _phan_tich_ast_statement(stmt, lines, full_source, counter)
            if matched is None:
                counter[0] += 1
                stmt_lines = lines[st_l - 1 : en_l]
                text = "\n".join(stmt_lines)
                tree_nodes.append(
                    TheNode(
                        id=_tao_id("matho", counter[0]),
                        ma="ma_tho",
                        o={"nguyen_van": text},
                        than=[],
                        line_start=st_l,
                        line_end=en_l,
                        indent=getattr(stmt, "col_offset", 0),
                        duoi_dong="",
                        raw_text=text,
                    )
                )
            elif isinstance(matched, list):
                tree_nodes.extend(matched)
            else:
                tree_nodes.append(matched)

            current_line = en_l + 1

        # Chú thích / dòng trống cuối file
        if current_line <= len(lines):
            trailing_lines = lines[current_line - 1 :]
            trailing_text = "\n".join(trailing_lines)
            if trailing_text:
                counter[0] += 1
                tree_nodes.append(
                    TheNode(
                        id=_tao_id("matho", counter[0]),
                        ma="ma_tho",
                        o={"nguyen_van": trailing_text},
                        than=[],
                        line_start=current_line,
                        line_end=len(lines),
                        indent=0,
                        duoi_dong="",
                        raw_text=trailing_text,
                    )
                )

    except SyntaxError:
        counter[0] += 1
        full_text = "\n".join(lines)
        tree_nodes = [
            TheNode(
                id=_tao_id("matho", counter[0]),
                ma="ma_tho",
                o={"nguyen_van": full_text},
                than=[],
                line_start=1,
                line_end=len(lines),
                indent=0,
                duoi_dong="",
                raw_text=full_text,
            )
        ]

    return FileSourceRecord(
        duong_dan=duong_dan,
        raw_bytes=raw_bytes,
        newline=newline,
        lines=lines,
        tree=tree_nodes,
        has_modifications=False,
    )


# ==============================================================================
# 2. BỘ SINH MÃ PYTHON & LƯU TỆP LOSSLESS (SPAN SPLICER + DUOI_DONG)
# ==============================================================================

def sinh_dong_the_don(node: TheNode, indent_level: int = 0) -> str:
    """Sinh chuỗi mã Python cho 1 thẻ đơn (chưa kèm thân con)."""
    spaces = " " * (indent_level * 4)
    ma = node.ma

    if ma == "gan":
        ten_bien = node.o.get("ten_bien", "x")
        gia_tri = node.o.get("gia_tri", "None")
        base = f"{spaces}{ten_bien} = {gia_tri}"
    elif ma == "in_ra":
        noi_dung = node.o.get("noi_dung", "")
        base = f"{spaces}print({noi_dung})"
    elif ma == "neu":
        dieu_kien = node.o.get("dieu_kien", "True")
        base = f"{spaces}if {dieu_kien}:"
    elif ma == "nguoc_lai":
        base = f"{spaces}else:"
    elif ma == "lap_moi":
        bien = node.o.get("bien", "item")
        day = node.o.get("day", "[]")
        base = f"{spaces}for {bien} in {day}:"
    elif ma == "lap_khi":
        dieu_kien = node.o.get("dieu_kien", "True")
        base = f"{spaces}while {dieu_kien}:"
    elif ma == "tra_ve":
        gia_tri = node.o.get("gia_tri", "")
        base = f"{spaces}return {gia_tri}".rstrip()
    elif ma == "ham":
        ten_ham = node.o.get("ten_ham", "ham")
        tham_so = node.o.get("tham_so", "")
        base = f"{spaces}def {ten_ham}({tham_so}):"
    elif ma == "goi_ham":
        ten_ham = node.o.get("ten_ham", "ham")
        doi_so = node.o.get("doi_so", "")
        base = f"{spaces}{ten_ham}({doi_so})"
    elif ma == "pheptinh":
        trai = node.o.get("trai", "a")
        phep = node.o.get("phep", "+")
        phai = node.o.get("phai", "b")
        base = f"{spaces}{trai} {phep} {phai}"
    elif ma == "ma_tho":
        raw = node.o.get("nguyen_van", node.raw_text or "")
        return raw
    else:
        base = f"{spaces}pass"

    # Nối duoi_dong (chú thích cuối dòng) nếu có (Mục 14.1)
    if node.duoi_dong:
        dd = node.duoi_dong
        if dd.lstrip().startswith("#") and not dd.startswith(" "):
            dd = " " + dd
        return f"{base}{dd}"
    return base


def sinh_ma_python(nodes: List[TheNode], indent_level: int = 0) -> str:
    """Sinh toàn bộ mã Python từ danh sách TheNode (chuẩn 4 dấu cách)."""
    res_lines: List[str] = []
    for node in nodes:
        if node.ma == "ma_tho":
            raw = node.o.get("nguyen_van", node.raw_text or "")
            if raw:
                res_lines.append(raw)
            continue

        head_line = sinh_dong_the_don(node, indent_level)
        res_lines.append(head_line)

        if BO_THE_V1.get(node.ma, TheDefinition("", "", "", [], False, "")).co_than:
            if node.than:
                child_code = sinh_ma_python(node.than, indent_level + 1)
                res_lines.append(child_code)
            else:
                spaces = " " * ((indent_level + 1) * 4)
                res_lines.append(f"{spaces}pass")

    return "\n".join(res_lines)


def luu_cay_the_ra_tep_py(record: FileSourceRecord) -> bytes:
    """Lưu cây thẻ ngược lại byte file .py.
    
    CỬA CỨNG 1: Nếu chưa sửa gì (has_modifications == False), trả về CHÍNH XÁC
    raw_bytes ban đầu (100% SHA-256 match, 0 byte thay đổi).
    
    CỬA CỨNG 2: Nếu có sửa, thực hiện thay thế trên các span dòng [line_start:line_end]
    của đúng các thẻ bị sửa (da_sua == True), giữ nguyên toàn bộ các dòng chú thích,
    import và duoi_dong (Mục 14.1).
    """
    if not record.has_modifications:
        return record.raw_bytes

    working_lines = list(record.lines)

    def _apply_node(n: TheNode, ind: int):
        # Nếu node này hoặc bất kỳ node con nào có da_sua == True
        node_or_child_modified = n.da_sua or any(c.da_sua for c in n.than)
        if node_or_child_modified:
            if n.line_start is not None and n.line_end is not None:
                new_code = sinh_ma_python([n], indent_level=ind)
                new_lines = new_code.split("\n")
                idx_s = n.line_start - 1
                idx_e = n.line_end
                working_lines[idx_s:idx_e] = new_lines
        else:
            for child in n.than:
                _apply_node(child, ind + 1)

    for node in record.tree:
        _apply_node(node, 0)

    result_text = record.newline.join(working_lines)
    return result_text.encode("utf-8")


# ==============================================================================
# 3. BỘ KIỂM TRA TĨNH (STATIC ANALYZER: 5 ĐỎ & 4 VÀNG)
# ==============================================================================

@dataclass
class DiagnosticItem:
    muc_do: str       # "do" (Lỗi cứng) | "vang" (Cảnh báo)
    ma_loi: str       # Mã lỗi / định danh quy tắc
    thong_diep: str   # Thông báo tiếng Việt dễ hiểu
    node_id: str      # ID của thẻ vi phạm
    line: Optional[int] = None


@dataclass
class DiagnosticResult:
    hop_le: bool                       # True nếu không có lỗi ĐỎ
    so_loi_do: int
    so_canh_bao_vang: int
    danh_sach: List[DiagnosticItem]
    so_lan_dung_the: Dict[str, int]    # Bộ đếm ×N


def _trich_xuat_bien_trong_bieu_thuc(bieu_thuc: str) -> Set[str]:
    """Phân tích AST biểu thức để lấy danh sách tên biến được đọc."""
    if not bieu_thuc or not bieu_thuc.strip():
        return set()
    try:
        parsed = ast.parse(bieu_thuc, mode="eval")
        names: Set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in BUILTIN_SYMBOLS:
                    names.add(node.id)
        return names
    except Exception:
        tokens = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", bieu_thuc))
        return {t for t in tokens if t not in BUILTIN_SYMBOLS}


def _dem_so_lan_dung_the(nodes: List[TheNode], counter: Dict[str, int]) -> None:
    """Duyệt đệ quy cây thẻ để đếm chính xác số lần dùng từng thẻ (×N)."""
    for n in nodes:
        counter[n.ma] = counter.get(n.ma, 0) + 1
        if n.than:
            _dem_so_lan_dung_the(n.than, counter)


def kiem_tra_cay_the(nodes: List[TheNode]) -> DiagnosticResult:
    """Chạy toàn bộ 5 quy tắc ĐỎ và 4 quy tắc VÀNG trên cây thẻ."""
    diagnostics: List[DiagnosticItem] = []
    
    so_lan_dung: Dict[str, int] = {k: 0 for k in BO_THE_V1.keys()}
    _dem_so_lan_dung_the(nodes, so_lan_dung)

    cac_bien_da_gan: Set[str] = set()
    cac_bien_da_doc: Set[str] = set()

    def _kiem_tra_danh_sach(
        node_list: List[TheNode],
        depth: int,
        inside_function: bool,
        scope_vars: Set[str],
    ):
        prev_node: Optional[TheNode] = None
        da_gap_tra_ve = False

        for idx, node in enumerate(node_list):
            ma = node.ma
            defn = BO_THE_V1.get(ma)

            # CẢNH BÁO VÀNG 4: Lồng sâu quá 4 tầng
            if depth > 4:
                diagnostics.append(
                    DiagnosticItem(
                        muc_do="vang",
                        ma_loi="excessive_nesting",
                        thong_diep=f"Khối lệnh lồng quá sâu ({depth} tầng, tối đa 4)",
                        node_id=node.id,
                        line=node.line_start,
                    )
                )

            # CẢNH BÁO VÀNG 3: Thẻ nằm sau tra_ve trong cùng một thân (unreachable)
            if da_gap_tra_ve:
                diagnostics.append(
                    DiagnosticItem(
                        muc_do="vang",
                        ma_loi="unreachable_code",
                        thong_diep="Thẻ nằm sau lệnh 'Trả về', sẽ không bao giờ được chạy tới",
                        node_id=node.id,
                        line=node.line_start,
                    )
                )
            if ma == "tra_ve":
                da_gap_tra_ve = True

            # LỖI ĐỎ 1: Ô bắt buộc còn trống
            if defn:
                for o_def in defn.o:
                    if o_def.bat_buoc:
                        val = node.o.get(o_def.ten, "")
                        if not val or not val.strip():
                            diagnostics.append(
                                DiagnosticItem(
                                    muc_do="do",
                                    ma_loi="empty_required_field",
                                    thong_diep=f"Ô bắt buộc '{o_def.ten}' của thẻ '{defn.ten}' còn trống",
                                    node_id=node.id,
                                    line=node.line_start,
                                )
                            )

            # LỖI ĐỎ 2: nguoc_lai không đứng ngay sau neu
            if ma == "nguoc_lai":
                if prev_node is None or prev_node.ma != "neu":
                    diagnostics.append(
                        DiagnosticItem(
                            muc_do="do",
                            ma_loi="orphan_else",
                            thong_diep="Thẻ 'Ngược lại' phải đứng ngay sau một thẻ 'Nếu'",
                            node_id=node.id,
                            line=node.line_start,
                        )
                    )

            # LỖI ĐỎ 3: tra_ve nằm ngoài mọi ham
            if ma == "tra_ve" and not inside_function:
                diagnostics.append(
                    DiagnosticItem(
                        muc_do="do",
                        ma_loi="return_outside_function",
                        thong_diep="Lệnh 'Trả về' chỉ được dùng bên trong một thẻ 'Hàm'",
                        node_id=node.id,
                        line=node.line_start,
                    )
                )

            # LỖI ĐỎ 5: Chuỗi thẻ rỗng bên trong thẻ có thân
            if defn and defn.co_than and not node.than:
                diagnostics.append(
                    DiagnosticItem(
                        muc_do="do",
                        ma_loi="empty_body",
                        thong_diep=f"Thẻ '{defn.ten}' có thân nhưng chưa chứa lệnh nào bên trong",
                        node_id=node.id,
                        line=node.line_start,
                    )
                )

            current_scope = set(scope_vars)

            if ma == "gan":
                ten_bien = node.o.get("ten_bien", "").strip()
                gia_tri = node.o.get("gia_tri", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(gia_tri)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' được sử dụng nhưng chưa từng được gán giá trị",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )
                if ten_bien and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", ten_bien):
                    cac_bien_da_gan.add(ten_bien)
                    scope_vars.add(ten_bien)

            elif ma == "in_ra":
                noi_dung = node.o.get("noi_dung", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(noi_dung)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' được sử dụng nhưng chưa từng được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            elif ma == "neu":
                dk = node.o.get("dieu_kien", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(dk)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' trong điều kiện 'Nếu' chưa được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            elif ma == "lap_khi":
                dk = node.o.get("dieu_kien", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(dk)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' trong điều kiện 'Lặp khi' chưa được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )
                # CẢNH BÁO VÀNG 2: lap_khi điều kiện không đổi trong thân
                if read_vars and node.than:
                    assigned_in_body: Set[str] = set()
                    for child in node.than:
                        if child.ma == "gan":
                            assigned_in_body.add(child.o.get("ten_bien", "").strip())
                    if not (read_vars & assigned_in_body):
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="vang",
                                ma_loi="potential_infinite_loop",
                                thong_diep="Vòng lặp có thể lặp vô tận: không có biến điều kiện nào được thay đổi giá trị trong thân",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            elif ma == "lap_moi":
                bien_lap = node.o.get("bien", "").strip()
                day_lap = node.o.get("day", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(day_lap)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến dãy '{v}' trong 'Lặp mỗi' chưa được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            elif ma == "tra_ve":
                gt = node.o.get("gia_tri", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(gt)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' trong giá trị 'Trả về' chưa được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            elif ma == "pheptinh":
                t = node.o.get("trai", "")
                p = node.o.get("phai", "")
                read_vars = _trich_xuat_bien_trong_bieu_thuc(t) | _trich_xuat_bien_trong_bieu_thuc(p)
                cac_bien_da_doc.update(read_vars)
                for v in read_vars:
                    if v not in current_scope:
                        diagnostics.append(
                            DiagnosticItem(
                                muc_do="do",
                                ma_loi="undefined_variable",
                                thong_diep=f"Biến '{v}' trong phép tính chưa được gán",
                                node_id=node.id,
                                line=node.line_start,
                            )
                        )

            if node.than:
                child_scope = set(scope_vars)
                is_fn = inside_function or (ma == "ham")
                if ma == "ham":
                    ten_h = node.o.get("ten_ham", "").strip()
                    if ten_h:
                        scope_vars.add(ten_h)
                        cac_bien_da_gan.add(ten_h)
                    params = [p.strip() for p in node.o.get("tham_so", "").split(",") if p.strip()]
                    child_scope.update(params)
                    cac_bien_da_gan.update(params)
                elif ma == "lap_moi":
                    b = node.o.get("bien", "").strip()
                    if b:
                        child_scope.add(b)
                        cac_bien_da_gan.add(b)

                _kiem_tra_danh_sach(
                    node.than,
                    depth=depth + 1,
                    inside_function=is_fn,
                    scope_vars=child_scope,
                )

            prev_node = node

    _kiem_tra_danh_sach(nodes, depth=1, inside_function=False, scope_vars=set())

    # CẢNH BÁO VÀNG 1: Biến gán rồi không dùng lần nào
    chua_dung = cac_bien_da_gan - cac_bien_da_doc
    for var in sorted(chua_dung):
        diagnostics.append(
            DiagnosticItem(
                muc_do="vang",
                ma_loi="unused_variable",
                thong_diep=f"Biến '{var}' đã được khai báo nhưng chưa được sử dụng lần nào",
                node_id="global",
            )
        )

    so_do = sum(1 for d in diagnostics if d.muc_do == "do")
    so_vang = sum(1 for d in diagnostics if d.muc_do == "vang")

    return DiagnosticResult(
        hop_le=(so_do == 0),
        so_loi_do=so_do,
        so_canh_bao_vang=so_vang,
        danh_sach=diagnostics,
        so_lan_dung_the=so_lan_dung,
    )


# ==============================================================================
# 4. SANDBOX CHẠY THỬ TIẾN TRÌNH CON (TRẦN 5.0S - MINH BẠCH GIỚI HẠN)
# ==============================================================================

@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    wall_time_ms: int
    timed_out: bool
    status: str       # "PASS" | "ERROR" | "TIMEOUT"


def chay_ma_python_sandbox(code: str, timeout: float = 5.0) -> ExecutionResult:
    """Chạy mã Python người dùng trong một tiến trình con độc lập.
    
    CHÚ THÍCH BẮT BUỘC THEO MỤC 13.1:
    Đây KHÔNG PHẢI hộp cát. Mã người dùng có mọi quyền của tài khoản đang chạy app.
    v1 chỉ có trần giờ 5 giây và tiến trình riêng — hai thứ ấy chống lặp vô hạn và chống
    treo app, KHÔNG chống được mã phá hoại.
    """
    t_start = time.perf_counter()
    timed_out = False
    
    with tempfile.TemporaryDirectory(prefix="aura_the_run_") as tmpdir:
        script_file = Path(tmpdir) / "run_script.py"
        script_file.write_text(code, encoding="utf-8")
        
        try:
            proc = subprocess.Popen(
                [sys.executable, str(script_file)],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
            exit_code = 124
            stderr += f"\n[TIMEOUT]: Quá giới hạn thời gian thực thi {timeout:.1f} giây. Tiến trình đã bị dừng."

    t_end = time.perf_counter()
    wall_time_ms = int((t_end - t_start) * 1000)

    if timed_out:
        status = "TIMEOUT"
    elif exit_code == 0:
        status = "PASS"
    else:
        status = "ERROR"

    return ExecutionResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        wall_time_ms=wall_time_ms,
        timed_out=timed_out,
        status=status,
    )
