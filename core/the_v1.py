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
from typing import Any, Dict, List, Optional, Set

# Whitelist các tên hàm / hằng số / từ khóa dựng sẵn của Python (tránh báo lỗi biến chưa gán)
BUILTIN_SYMBOLS: Set[str] = {
    "True", "False", "None", "range", "len", "int", "str", "float", "list",
    "dict", "set", "tuple", "sum", "min", "max", "abs", "round", "bool",
    "print", "input", "enumerate", "zip", "sorted", "reversed", "map", "filter",
    "open", "type", "isinstance", "issubclass", "iter", "next", "all", "any",
    "chr", "ord", "hex", "bin", "oct", "pow", "divmod", "format", "repr",
    "getattr", "hasattr", "setattr", "delattr", "frozenset", "callable", "id",
    "hash", "staticmethod", "classmethod", "property", "super", "vars", "dir",
    "bytes", "bytearray", "slice", "complex", "memoryview", "ascii", "help",
    "globals", "locals", "Exception", "ValueError", "TypeError", "KeyError",
    "IndexError", "AttributeError", "RuntimeError", "StopIteration",
    "FileNotFoundError", "AssertionError", "ImportError", "IOError", "OSError",
    # Từ khóa Python
    "if", "else", "elif", "for", "while", "in", "is", "not", "and", "or",
    "as", "with", "try", "except", "finally", "def", "class"
}

# 6 Nhóm thẻ với màu sắc chuẩn (Tuyệt đối không dùng Đỏ #EF4444 và Vàng #EAB308)
NHOM_THE: Dict[str, Dict[str, str]] = {
    "dieu_khien": {"ten": "Điều khiển", "mau": "#3B82F6"},  # Xanh dương
    "du_lieu": {"ten": "Dữ liệu", "mau": "#10B981"},        # Xanh lá
    "vao_ra": {"ten": "Vào / Ra", "mau": "#8B5CF6"},        # Tím
    "ham": {"ten": "Hàm", "mau": "#F59E0B"},               # Cam / Amber
    "chu_thich": {"ten": "Chú thích", "mau": "#14B8A6"},   # Xanh ngọc
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


# 17 Thẻ chuẩn của v1 (12 gốc + 5 thêm ngày 25/08/2026)
#
# BẢN NÀY PHẢI KHỚP 1:1 VỚI interface/web/the_v1/validator.js.
# Hai bản sinh mã song song là bệnh trùng lặp logic, nhưng JS và Python
# không dùng chung mã được. Thứ giữ chúng khỏi trôi là cửa
# `tests/test_the_parity.js` — 27 cây thẻ chạy qua CẢ HAI bản rồi so.
# Hôm 25/08 thêm 5 thẻ vào JS mà chưa thêm vào đây: cửa ấy đỏ ngay.
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
    "chu_thich": TheDefinition(
        ma="chu_thich",
        ten="Chú thích",
        nhom="chu_thich",
        o=[
            ODefinition(ten="noi_dung", kieu="chu", bat_buoc=True, goi_y="# Chú thích"),
        ],
        co_than=False,
        mau=NHOM_THE["chu_thich"]["mau"],
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
    # ---- 5 thẻ thêm 25/08/2026, xem chú thích cùng ngày ở validator.js ----
    "nhap": TheDefinition(
        ma="nhap",
        ten="Nhập thư viện",
        nhom="vao_ra",
        o=[
            ODefinition(ten="thu_vien", kieu="chu", bat_buoc=True, goi_y="math"),
            ODefinition(ten="phan", kieu="chu", bat_buoc=False, goi_y="sqrt, pi"),
            ODefinition(ten="ten_khac", kieu="chu", bat_buoc=False, goi_y=""),
        ],
        co_than=False,
        mau=NHOM_THE["vao_ra"]["mau"],
    ),
    "dung_lap": TheDefinition(
        ma="dung_lap",
        ten="Dừng lặp",
        nhom="dieu_khien",
        o=[],
        co_than=False,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "bo_qua": TheDefinition(
        ma="bo_qua",
        ten="Bỏ qua vòng này",
        nhom="dieu_khien",
        o=[],
        co_than=False,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "thu": TheDefinition(
        ma="thu",
        ten="Thử",
        nhom="dieu_khien",
        o=[],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
    "bat_loi": TheDefinition(
        ma="bat_loi",
        ten="Bắt lỗi",
        nhom="dieu_khien",
        o=[
            ODefinition(ten="loai_loi", kieu="chu", bat_buoc=False, goi_y="Exception"),
            ODefinition(ten="ten_bien", kieu="chu", bat_buoc=False, goi_y="e"),
        ],
        co_than=True,
        mau=NHOM_THE["dieu_khien"]["mau"],
    ),
}


@dataclass
class TheNode:
    id: str
    ma: str
    o: Dict[str, str] = field(default_factory=dict)
    than: List[TheNode] = field(default_factory=list)
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    indent: int = 0
    duoi_dong: str = ""
    raw_text: Optional[str] = None
    da_sua: bool = False

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "id": self.id,
            "ma": self.ma,
            "o": dict(self.o),
            "than": [child.to_dict() for child in self.than],
            "line_start": self.line_start,
            "line_end": self.line_end,
            "indent": self.indent,
            "duoi_dong": self.duoi_dong,
            "raw_text": self.raw_text,
            "da_sua": self.da_sua,
        }
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TheNode:
        than_list = [cls.from_dict(child) for child in data.get("than", [])]
        return cls(
            id=data.get("id", ""),
            ma=data.get("ma", "ma_tho"),
            o=dict(data.get("o", {})),
            than=than_list,
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
            indent=data.get("indent", 0),
            duoi_dong=data.get("duoi_dong", ""),
            raw_text=data.get("raw_text"),
            da_sua=data.get("da_sua", False),
        )


# ==============================================================================
# 1. BỘ PHÂN TÍCH AST & MỞ TỆP .PY SANG CÂY THẺ (LOSSLESS SPAN TRACKING)
# ==============================================================================


# Cờ để chạy MỘT TỆP .py bằng chính cái .exe đã đóng băng.
#
# 31/08/2026 — đo trên bản `.exe` dựng bằng PyInstaller: bấm CHẠY THỬ thì máy
# chủ gọi `[sys.executable, "-X", "utf8", run_script.py]`, mà trong bản đóng
# băng `sys.executable` LÀ CHÍNH CÁI EXE, không phải `python.exe`. Kết quả đo
# được, không đoán:
#
#     AURA_The.exe: error: unrecognized arguments: -X utf8 ...\run_script.py
#     exit_code 2 · nhãn trên màn hình: "LỖI RUNTIME"
#
# Tức là bản gửi cho người thử có nút chính CHẾT, và nhãn còn đổ lỗi cho mã của
# người học. Cách chữa: cho cái exe biết đóng vai thông dịch khi thấy cờ này.
# Xem `interface/the_app.py` — nhánh nhận cờ nằm ở dòng ĐẦU của `main()`, trước
# argparse, vì argparse chính là thứ đã từ chối.
CO_CHAY_TEP = "--chay-tep-python"


def lenh_chay_tep_python(script: Path | str) -> List[str]:
    """Câu lệnh chạy một tệp .py — đúng cả khi app đã bị đóng băng thành .exe.

    Bản thường  ->  [python.exe, -X, utf8, script]
    Bản .exe    ->  [AURA_The.exe, --chay-tep-python, script]

    `-X utf8` không truyền được cho bản đóng băng (bootloader không nhận cờ của
    CPython), nên nhánh kia tự ép UTF-8 trong `main()` thay vì qua dòng lệnh.
    """
    if getattr(sys, "frozen", False):
        return [sys.executable, CO_CHAY_TEP, str(script)]
    return [sys.executable, "-X", "utf8", str(script)]


# ==============================================================================
# 2. BỘ SINH MÃ PYTHON & LƯU TỆP LOSSLESS (SPAN SPLICER + DUOI_DONG)
# ==============================================================================

def sinh_dong_the_don(node: TheNode, indent_level: int = 0) -> str:
    """Sinh chuỗi mã 1 dòng cho một TheNode duy nhất kèm duoi_dong."""
    spaces = " " * (indent_level * 4)
    ma = node.ma

    if ma == "gan":
        ten_b = node.o.get("ten_bien", "x")
        gia_t = node.o.get("gia_tri", "10")
        base = f"{spaces}{ten_b} = {gia_t}"
    elif ma == "in_ra":
        noi_d = node.o.get("noi_dung", "")
        base = f'{spaces}print({noi_d})'
    elif ma == "neu":
        dieu_k = node.o.get("dieu_kien", "True")
        prefix = "elif" if node.o.get("noi_tiep") == "1" else "if"
        base = f"{spaces}{prefix} {dieu_k}:"
    elif ma == "nguoc_lai":
        base = f"{spaces}else:"
    elif ma == "nhap":
        tv = node.o.get("thu_vien", "").strip()
        ph = node.o.get("phan", "").strip()
        tk = node.o.get("ten_khac", "").strip()
        if ph:
            # `from X import a, b` — `as` chỉ gắn được khi lấy ĐÚNG MỘT tên.
            mot_ten = "," not in ph
            if tk and mot_ten:
                base = f"{spaces}from {tv} import {ph} as {tk}"
            else:
                base = f"{spaces}from {tv} import {ph}"
        elif tk:
            base = f"{spaces}import {tv} as {tk}"
        else:
            base = f"{spaces}import {tv}"
    elif ma == "dung_lap":
        base = f"{spaces}break"
    elif ma == "bo_qua":
        base = f"{spaces}continue"
    elif ma == "thu":
        base = f"{spaces}try:"
    elif ma == "bat_loi":
        # Bỏ trống thì `except Exception:`, KHÔNG phải `except:` trần — xem
        # chú thích cùng ngày ở validator.js.
        loai = node.o.get("loai_loi", "").strip() or "Exception"
        tb = node.o.get("ten_bien", "").strip()
        base = f"{spaces}except {loai} as {tb}:" if tb else f"{spaces}except {loai}:"
    elif ma == "lap_moi":
        bien = node.o.get("bien", "i")
        day = node.o.get("day", "range(10)")
        base = f"{spaces}for {bien} in {day}:"
    elif ma == "lap_khi":
        dieu_k = node.o.get("dieu_kien", "True")
        base = f"{spaces}while {dieu_k}:"
    elif ma == "tra_ve":
        gia_t = node.o.get("gia_tri", "")
        base = f"{spaces}return {gia_t}".rstrip()
    elif ma == "ham":
        ten_ham = node.o.get("ten_ham", "ham")
        tham_so = node.o.get("tham_so", "")
        kieu_tra_ve = node.o.get("kieu_tra_ve", "")
        prefix = "async def" if node.o.get("async") == "1" else "def"
        
        lines = []
        if node.o.get("trang_tri"):
            for dec in node.o["trang_tri"].split("\n"):
                if dec.strip():
                    lines.append(f"{spaces}{dec.strip()}")
                    
        if kieu_tra_ve:
            if not kieu_tra_ve.startswith("->"):
                kieu_tra_ve = f"-> {kieu_tra_ve}"
            sig = f"{spaces}{prefix} {ten_ham}({tham_so}) {kieu_tra_ve}:"
        else:
            sig = f"{spaces}{prefix} {ten_ham}({tham_so}):"
        lines.append(sig)
        base = "\n".join(lines)
    elif ma == "goi_ham":
        ten_ham = node.o.get("ten_ham", "ham")
        doi_so = node.o.get("doi_so", "")
        base = f"{spaces}{ten_ham}({doi_so})"
    elif ma == "pheptinh":
        trai = node.o.get("trai", "a")
        phep = node.o.get("phep", "+")
        phai = node.o.get("phai", "b")
        base = f"{spaces}{trai} {phep} {phai}"
    elif ma == "chu_thich":
        nd = node.o.get("noi_dung", "").strip()
        if not nd.startswith("#"):
            nd = f"# {nd}"
        base = f"{spaces}{nd}"
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


def _so_dong_trong_truoc(truoc: Optional[TheNode], nay: TheNode) -> int:
    """Số dòng trống nằm giữa hai thẻ anh em trong TỆP GỐC.

    26/08/2026. `sinh_ma_python` trước đây nối các thẻ bằng đúng một `\n`, nên
    mọi dòng trống giữa các câu lệnh biến mất. Đo vòng tròn trên 33 tệp thật
    (đọc tệp -> cây thẻ -> sinh lại -> so với bản gốc):

        tệp kiểu người mới học   5/5 khác bản gốc, và khác ĐÚNG ở dòng trống
        mã nguồn AURA           28/28 khác bản gốc

    Một tệp `def chao(...)` rồi hai dòng trống rồi `chao("A")` sinh lại thành
    ba dòng dính liền. Với người mới học thì đó là bài của họ bị bóp lại.

    Không cần thêm trường nào: `line_start` và `line_end` ĐÃ có sẵn trên mỗi
    thẻ khi đọc bằng CST. Khoảng hở giữa `line_end` của thẻ trước và
    `line_start` của thẻ sau chính là số dòng trống.

    Trả 0 khi thiếu thông tin dòng — thẻ do người dùng vừa kéo vào không có
    `line_start`, và đoán bừa một dòng trống cho nó thì tệ hơn là không đoán.
    """
    if truoc is None or nay is None:
        return 0
    if not truoc.line_end or not nay.line_start:
        return 0
    hieu = nay.line_start - truoc.line_end - 1
    return hieu if hieu > 0 else 0


def sinh_ma_python(nodes: List[TheNode], indent_level: int = 0) -> str:
    """Sinh toàn bộ mã Python từ danh sách TheNode (chuẩn 4 dấu cách)."""
    res_lines: List[str] = []
    the_truoc: Optional[TheNode] = None
    for node in nodes:
        # Trả lại đúng số dòng trống của tệp gốc. Xem `_so_dong_trong_truoc`.
        for _ in range(_so_dong_trong_truoc(the_truoc, node)):
            res_lines.append("")
        the_truoc = node
        if node.ma == "ma_tho":
            raw = node.o.get("nguyen_van", node.raw_text or "")
            if raw:
                spaces = " " * (indent_level * 4)
                for rl in raw.split("\n"):
                    if rl.strip():
                        res_lines.append(f"{spaces}{rl}")
                    else:
                        res_lines.append("")
            continue

        is_else_or_elif = (node.ma in ("nguoc_lai", "bat_loi")) or (
            node.ma == "neu" and node.o.get("noi_tiep") == "1")
        cur_indent = max(0, indent_level - 1) if is_else_or_elif else indent_level

        head_line = sinh_dong_the_don(node, cur_indent)
        res_lines.append(head_line)

        if BO_THE_V1.get(node.ma, TheDefinition("", "", "", [], False, "")).co_than:
            if node.than:
                child_indent = cur_indent + 1
                child_code = sinh_ma_python(node.than, child_indent)
                res_lines.append(child_code)
            else:
                spaces = " " * ((cur_indent + 1) * 4)
                res_lines.append(f"{spaces}pass")

    return "\n".join(res_lines)


def sinh_ma_python_ca_tep(nodes: List[TheNode], xuong_dong: str = "\n") -> str:
    """Sinh mã cho MỘT TỆP HOÀN CHỈNH — có ký tự xuống dòng cuối.

    `xuong_dong` GIỮ ĐÚNG QUY ƯỚC CỦA TỆP GỐC. Thêm 26/08/2026 sau khi phép
    thử đầu tiên trượt vì đúng chuyện này: `sinh_ma_python` luôn nối bằng LF,
    còn tệp trên Windows — Notepad, `Path.write_text`, git checkout — hầu hết
    là CRLF. Đo trên cùng một nội dung:

        tệp LF    sinh lại giống hệt  -> True
        tệp CRLF  sinh lại khác       -> False

    Nên nếu bỏ tham số này thì luật "sinh lại đúng bản gốc thì cho thêm thẻ"
    KHÔNG BAO GIỜ MỞ trên máy Windows — mà đó chính là máy app chạy. Và ghi
    một tệp CRLF thành LF thì git báo cả tệp đã đổi.

    Bản ghi của bộ đọc (`the_cst.BanGhiCST.newline`) đã ghi sẵn quy ước ấy
    lúc đọc; chỉ việc truyền vào.

    01/09/2026: câu trên trước ghi `FileSourceRecord.newline` — lớp ấy thuộc
    bộ đọc AST trong chính tệp này, và bộ đọc ấy vừa bị xoá vì KHÔNG AI GỌI.
    Chú thích trỏ vào một cái tên không còn tồn tại thì người sau đi tìm mãi.

    26/08/2026. `sinh_ma_python` nối các dòng bằng `"\\n".join()` nên chuỗi
    trả về KHÔNG kết thúc bằng xuống dòng. Điều đó đúng cho lời gọi đệ quy
    (thân thẻ nối vào giữa tệp), nhưng sai cho một TỆP: git, các công cụ dòng
    lệnh và POSIX đều coi tệp văn bản là kết thúc bằng xuống dòng.

    Đo vòng tròn sau khi vá dòng trống: tệp kiểu người mới học sinh lại giống
    bản gốc TỪNG BYTE, trừ đúng ký tự cuối này.

    KHÔNG thêm vào chính `sinh_ma_python` vì nó tự gọi mình cho thân thẻ; thêm
    ở đó thì mỗi tầng lồng nhau chèn dư một dòng trống.
    """
    ma = sinh_ma_python(nodes)
    if not ma:
        return ma
    if not ma.endswith("\n"):
        ma += "\n"
    # `sinh_ma_python` luôn nối bằng LF; đổi sang quy ước của tệp gốc ở BƯỚC
    # CUỐI, một lần, thay vì rải vào mọi chỗ nối chuỗi bên trong.
    if xuong_dong and xuong_dong != "\n":
        ma = ma.replace("\n", xuong_dong)
    return ma


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


# Định danh Python 3 CHO PHÉP chữ Unicode: `tổng`, `lời_chào`, `cộng`, `số` đều
# là tên biến hợp lệ. Mẫu cũ `[^\W\d]\w*` chỉ nhận ASCII, nên tên
# tiếng Việt không bao giờ được ghi vào `cac_bien_da_gan` (dòng ~1499), và rồi
# chính nó bị báo là "chưa từng được gán".
#
# Đo thật 30/08/2026 qua /api/kiem, hai cây thẻ y hệt nhau, chỉ khác cái tên:
#     ten_bien "loi_chao"  -> hop_le true,  0 lỗi
#     ten_bien "lời_chào"  -> hop_le false, 1 lỗi ĐỎ "chưa từng được gán"
# Lỗi ĐỎ chặn cứng nút CHẠY (xem runProgram trong app.js), nên người học đặt tên
# biến bằng tiếng Việt vừa bị vu oan vừa không chạy nổi chương trình.
#
# `\w` trong `re` của Python đã hiểu Unicode sẵn cho chuỗi str, nên `[^\W\d]\w*`
# đọc là "ký tự từ nhưng không phải chữ số, rồi ký tự từ" — xấp xỉ XID_Start /
# XID_Continue. Nó RỘNG hơn luật thật của Python một chút, và rộng là hướng sai
# an toàn ở đây: rộng thì bỏ sót một lỗi thật, hẹp thì VU OAN rồi chặn người dùng.
def _trich_xuat_bien_trong_bieu_thuc(bieu_thuc: str) -> Set[str]:
    """Phân tích AST biểu thức để lấy danh sách tên biến được đọc từ phạm vi ngoài."""
    if not bieu_thuc or not bieu_thuc.strip():
        return set()
    try:
        parsed = ast.parse(bieu_thuc, mode="eval")
        # Thu thập các biến cục bộ sinh từ comprehension hoặc walrus operator
        local_comp_vars: Set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for gen in node.generators:
                    for t_node in ast.walk(gen.target):
                        if isinstance(t_node, ast.Name):
                            local_comp_vars.add(t_node.id)
            elif isinstance(node, ast.NamedExpr):
                if isinstance(node.target, ast.Name):
                    local_comp_vars.add(node.target.id)

        names: Set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in BUILTIN_SYMBOLS and node.id not in local_comp_vars:
                    names.add(node.id)
        return names
    except Exception:
        clean = re.sub(r'"(?:[^"\\]|\\.)*"', ' ', bieu_thuc)
        clean = re.sub(r"'(?:[^'\\]|\\.)*'", ' ', clean)
        clean = re.sub(r'\.[^\W\d]\w*', ' ', clean)
        tokens = set(re.findall(r"\b[^\W\d]\w*\b", clean))
        return {t for t in tokens if t not in BUILTIN_SYMBOLS}


def _trich_xuat_bieu_tuong_import(code: str) -> Set[str]:
    """Trích xuất tất cả các tên được import từ khối mã thô."""
    symbols: Set[str] = set()
    if not code:
        return symbols
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        symbols.add(alias.asname or alias.name)
    except Exception:
        for line in code.splitlines():
            line = line.strip()
            if line.startswith("import "):
                parts = line[7:].split(",")
                for p in parts:
                    p = p.strip().split(" as ")[-1].strip().split(".")[0]
                    if p:
                        symbols.add(p)
            elif line.startswith("from ") and " import " in line:
                _, imp = line.split(" import ", 1)
                for p in imp.split(","):
                    p = p.strip().replace("(", "").replace(")", "").split(" as ")[-1].strip()
                    if p and p != "*":
                        symbols.add(p)
    return symbols


def _trich_xuat_bien_gan_trong_ma_tho(code: str) -> Set[str]:
    """Trích xuất các biến/hàm/lớp được định nghĩa trong khối mã thô."""
    names: Set[str] = set()
    if not code:
        return names
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
    except Exception:
        for m in re.finditer(r"^\s*([^\W\d]\w*)\s*=", code, re.MULTILINE):
            names.add(m.group(1))
        for m in re.finditer(r"^\s*(?:def|class)\s+([^\W\d]\w*)", code, re.MULTILINE):
            names.add(m.group(1))
    return names


def _trich_xuat_ten_tham_so(tham_so_str: str) -> List[str]:
    """Trích xuất danh sách tên tham số từ chuỗi định nghĩa hàm."""
    if not tham_so_str or not tham_so_str.strip():
        return []
    try:
        mod = ast.parse(f"def _({tham_so_str}): pass")
        fn = mod.body[0]
        assert isinstance(fn, ast.FunctionDef)
        params = []
        for arg in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs:
            params.append(arg.arg)
        if fn.args.vararg:
            params.append(fn.args.vararg.arg)
        if fn.args.kwarg:
            params.append(fn.args.kwarg.arg)
        return params
    except Exception:
        clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', tham_so_str)
        clean = re.sub(r"'(?:[^'\\]|\\.)*'", "''", clean)
        depth = 0
        cur = []
        chunks = []
        for ch in clean:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                chunks.append("".join(cur).strip())
                cur = []
                continue
            cur.append(ch)
        if cur:
            chunks.append("".join(cur).strip())
        res = []
        for chunk in chunks:
            if chunk == "*":
                continue
            part = re.split(r"[:=]", chunk)[0].strip().lstrip("*")
            if part and re.match(r"^[^\W\d]\w*$", part):
                res.append(part)
        return res


def _dem_so_lan_dung_the(nodes: List[TheNode], counter: Dict[str, int]) -> None:
    """Duyệt đệ quy cây thẻ để đếm chính xác số lần dùng từng thẻ (×N)."""
    for n in nodes:
        counter[n.ma] = counter.get(n.ma, 0) + 1
        if n.than:
            _dem_so_lan_dung_the(n.than, counter)


def _thu_thap_bieu_tuong_toan_cuc(nodes: List[TheNode], global_symbols: Set[str]) -> None:
    """Pha 1: Thu thập biểu tượng toàn cục (hàm, import, gán trong mã thô)."""
    for node in nodes:
        if node.ma == "ham":
            ten_h = node.o.get("ten_ham", "").strip()
            if ten_h:
                global_symbols.add(ten_h)
        elif node.ma == "ma_tho":
            code = node.o.get("nguyen_van", node.raw_text or "")
            global_symbols.update(_trich_xuat_bieu_tuong_import(code))
            global_symbols.update(_trich_xuat_bien_gan_trong_ma_tho(code))
        elif node.ma == "nhap":
            # Không gom thì mỗi lần dùng `sqrt` đều báo "biến chưa được gán" —
            # thẻ `nhap` sẽ thành thẻ DUY NHẤT sinh ra lỗi giả cho chính nó.
            tv = node.o.get("thu_vien", "").strip()
            ph = node.o.get("phan", "").strip()
            tk = node.o.get("ten_khac", "").strip()
            if ph:
                mot_ten = "," not in ph
                if tk and mot_ten:
                    global_symbols.add(tk)
                else:
                    for x in ph.split(","):
                        t = x.strip()
                        if re.fullmatch(r"[^\W\d]\w*", t):
                            global_symbols.add(t)
            elif tk:
                global_symbols.add(tk)
            elif tv:
                # `import a.b.c` chỉ đưa tên `a` vào tầm nhìn.
                goc = tv.split(".")[0].strip()
                if re.fullmatch(r"[^\W\d]\w*", goc):
                    global_symbols.add(goc)
        if node.than:
            _thu_thap_bieu_tuong_toan_cuc(node.than, global_symbols)


def kiem_tra_cay_the(nodes: List[TheNode]) -> DiagnosticResult:
    """Chạy toàn bộ 5 quy tắc ĐỎ và 4 quy tắc VÀNG trên cây thẻ với Scope 2 pha."""
    diagnostics: List[DiagnosticItem] = []
    
    so_lan_dung: Dict[str, int] = {k: 0 for k in BO_THE_V1.keys()}
    _dem_so_lan_dung_the(nodes, so_lan_dung)

    # PHA 1: Thu thập biểu tượng toàn cục
    global_symbols: Set[str] = set(BUILTIN_SYMBOLS)
    _thu_thap_bieu_tuong_toan_cuc(nodes, global_symbols)

    cac_bien_da_gan: Set[str] = set()
    cac_bien_da_doc: Set[str] = set()

    # PHA 2: Duyệt kiểm tra phạm vi và cú pháp
    def _kiem_tra_danh_sach(
        node_list: List[TheNode],
        depth: int,
        inside_function: bool,
        scope_vars: Set[str],
        parent_ma: Optional[str] = None,
        inside_loop: bool = False,
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

            # LỖI ĐỎ 2: nguoc_lai không đứng sau neu (kể cả dạng con trong CST hay anh em)
            if ma == "nguoc_lai":
                hop_le_else = (parent_ma == "neu") or (prev_node is not None and prev_node.ma == "neu")
                if not hop_le_else:
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

            # LỖI ĐỎ 3b: 'Dừng lặp' / 'Bỏ qua vòng này' nằm ngoài mọi vòng lặp
            if ma in ("dung_lap", "bo_qua") and not inside_loop:
                diagnostics.append(
                    DiagnosticItem(
                        muc_do="do",
                        ma_loi="loop_control_outside_loop",
                        thong_diep=(
                            f"Thẻ '{defn.ten if defn else ma}' chỉ được dùng "
                            f"bên trong 'Lặp mỗi' hoặc 'Lặp khi'"
                        ),
                        node_id=node.id,
                        line=node.line_start,
                    )
                )

            # LỖI ĐỎ 3c: 'Bắt lỗi' không gắn với 'Thử' nào
            if ma == "bat_loi":
                hop_le = (parent_ma == "thu") or (prev_node is not None and prev_node.ma == "thu")
                if not hop_le:
                    diagnostics.append(
                        DiagnosticItem(
                            muc_do="do",
                            ma_loi="orphan_except",
                            thong_diep="Thẻ 'Bắt lỗi' phải đứng ngay sau một thẻ 'Thử'",
                            node_id=node.id,
                            line=node.line_start,
                        )
                    )

            # LỖI ĐỎ 3d: 'Thử' không có 'Bắt lỗi' đi kèm
            #
            # Python KHÔNG cho `try:` đứng một mình — thiếu `except` là lỗi cú
            # pháp thật, không phải chuyện phong cách.
            if ma == "thu":
                sau = node_list[idx + 1] if idx + 1 < len(node_list) else None
                co_em = sau is not None and sau.ma == "bat_loi"
                co_con = any(c is not None and c.ma == "bat_loi" for c in (node.than or []))
                if not co_em and not co_con:
                    diagnostics.append(
                        DiagnosticItem(
                            muc_do="do",
                            ma_loi="try_without_except",
                            thong_diep="Thẻ 'Thử' phải đi kèm một thẻ 'Bắt lỗi' ngay sau nó",
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
                if ten_bien and re.match(r"^[^\W\d]\w*$", ten_bien):
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
                    params = _trich_xuat_ten_tham_so(node.o.get("tham_so", ""))
                    child_scope.update(params)
                    cac_bien_da_gan.update(params)
                elif ma == "lap_moi":
                    b_str = node.o.get("bien", "").strip()
                    loop_vars = re.findall(r"\b[^\W\d]\w*\b", b_str)
                    for b in loop_vars:
                        child_scope.add(b)
                        cac_bien_da_gan.add(b)
                elif ma == "bat_loi":
                    # `except ValueError as e:` GÁN biến `e` cho thân khối.
                    # Xem chú thích cùng ngày ở validator.js.
                    tb = node.o.get("ten_bien", "").strip()
                    if re.fullmatch(r"[^\W\d]\w*", tb):
                        child_scope.add(tb)
                        cac_bien_da_gan.add(tb)

                # `dung_lap`/`bo_qua` còn hiệu lực khi lồng trong `neu` hay
                # `thu` bên trong vòng lặp, nên cờ mang xuống; nhưng KHÔNG
                # vượt qua ranh giới một `ham` — `break` trong hàm lồng trong
                # vòng lặp là lỗi cú pháp thật của Python.
                if ma in ("lap_moi", "lap_khi"):
                    trong_lap = True
                elif ma == "ham":
                    trong_lap = False
                else:
                    trong_lap = inside_loop

                _kiem_tra_danh_sach(
                    node.than,
                    depth=depth + 1,
                    inside_function=is_fn,
                    scope_vars=child_scope,
                    parent_ma=ma,
                    inside_loop=trong_lap,
                )

            prev_node = node

    _kiem_tra_danh_sach(nodes, depth=1, inside_function=False,
                        scope_vars=set(global_symbols), inside_loop=False)

    # CẢNH BÁO VÀNG 1: Biến gán rồi không dùng lần nào
    chua_dung = cac_bien_da_gan - cac_bien_da_doc - global_symbols
    for var in sorted(chua_dung):
        if not var.startswith("_"):
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


def chay_ma_tien_trinh_rieng(code: str, timeout: float = 5.0) -> ExecutionResult:
    """Chạy mã Python người dùng trong một tiến trình con riêng, trần 5 giây.

    TÊN CŨ LÀ `chay_ma_python_sandbox` — ĐỔI NGÀY 25/08/2026.

    Chú thích cũ đã nói đúng ("đây KHÔNG PHẢI hộp cát"), nhưng cái TÊN nói
    ngược lại, và cái tên là thứ người sau đọc. Ai gọi `..._sandbox` sẽ tin
    là đã cô lập, rồi dựa vào đó mà quyết định.

    ĐO THẬT 25/08/2026, chạy qua đúng hàm này, không đọc mã mà suy:

        ghi tệp bằng đường dẫn TUYỆT ĐỐI ngoài cwd   GHI ĐƯỢC
        gọi tiến trình con (`cmd /c echo`)           CHẠY ĐƯỢC
        mở socket, lắng nghe                         MỞ ĐƯỢC (cổng 57658)
        đọc tệp bất kỳ trên đĩa                      ĐỌC ĐƯỢC
        đọc biến môi trường                          ĐỌC ĐƯỢC

    Thứ duy nhất hàm này có: tiến trình riêng + trần 5 giây. Hai thứ ấy chống
    lặp vô hạn và chống treo app. Chúng KHÔNG chống mã phá hoại, và không có
    giới hạn RAM, hệ tệp, mạng hay tiến trình nào cả.

    Kế hoạch 19/08 từng hứa "giới hạn 256 MB RAM" (`import resource` — API
    Unix, Windows không có) và "cwd ở thư mục tạm, không cấp quyền ghi ra
    ngoài" (chạy thử: ghi được). Cả hai lời hứa ấy chưa bao giờ tồn tại.

    Dùng được cho: người dùng chạy mã CỦA CHÍNH HỌ trên máy CỦA CHÍNH HỌ —
    đúng quyền họ vốn có khi mở `python` lên gõ.
    Không dùng được cho: máy chủ nhiều người, hoặc chạy mã tải từ nơi khác.
    """
    t_start = time.perf_counter()
    timed_out = False
    
    with tempfile.TemporaryDirectory(prefix="aura_the_run_") as tmpdir:
        script_file = Path(tmpdir) / "run_script.py"
        script_file.write_text(code, encoding="utf-8")
        
        try:
            # -X utf8 — 30/08/2026. Cha giai ma bang encoding="utf-8" (duoi day)
            # nhung CON van ghi bang codec mac dinh cua Windows. Do that qua dung
            # ham nay:
            #     print("Chuot")  -> status=PASS   stdout 'Chuot'
            #     print("Chuột")  -> status=ERROR  UnicodeEncodeError: 'charmap'
            #                        codec can't encode character '\u1ed9'
            # Tuc la moi nguoi hoc Viet Nam in ra mot chu co dau deu nhan loi —
            # ca o nut CHAY lan o bo cham thu thach. Bai 4 "Loc San Pham" in ra
            # ['Chuot'] co dau nen 0/2 truong hop do duoc, trong khi bai 3 in
            # "Nguyen Van A" thuan ASCII thi 3/3.
            # Cung ho voi luat o CLAUDE.md muc 4 (do tieng Viet bang Python, dung
            # qua PowerShell): duong ong nao khong ep UTF-8 thi duong ong do nuot dau.
            proc = subprocess.Popen(
                lenh_chay_tep_python(script_file),
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
