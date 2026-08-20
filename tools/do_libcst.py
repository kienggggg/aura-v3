# -*- coding: utf-8 -*-
"""LibCST có thay được bộ đọc/sinh mã tự đẽo của app thẻ không. Đo, không đọc.

VÌ SAO — 20/08/2026.

App thẻ bản v1 dựng cây trên `ast`, mà `ast` CỐ Ý vứt dấu cách, chú thích, và cả
`elif` (nó là nút `If` lồng trong `orelse`, không có cờ nào phân biệt). Nên
Antigravity phải tự bù bằng `line_start`/`duoi_dong`/`ma_tho`, và cả bốn lỗi đo
được đều sinh ra từ chỗ bù ấy:

    cửa 1  gõ lại y giá trị cũ  ->  49,8% giữ nguyên byte
    cửa 2  chú thích thẻ khối   ->  mất 4/4
    cửa 4  thẻ tả sai nguồn     ->  390/2.539
    riêng `elif` -> `else:`     ->  28/40 thẻ Ngược lại, MẤT LUÔN ĐIỀU KIỆN

LibCST giữ nguyên từng byte theo thiết kế. Tài liệu nói vậy — nhưng kho đã trả
giá vì tin tài liệu một lần rồi (OpenClaw "context tối thiểu 16K", mã chặn ở 4K),
nên tệp này ĐO trên đúng 66 tệp của kho.

    .venv-cst\\Scripts\\python.exe -X utf8 tools\\do_libcst.py

Cài riêng, không đụng venv chính (luật gói giả của kho):

    venv\\Scripts\\python.exe -m venv .venv-cst
    .venv-cst\\Scripts\\python.exe -m pip install libcst
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
THU_MUC = ("core", "interface", "tools", "tests")

MAU = (
    'import os\n'
    '\n'
    '\n'
    'def cong(a: int = 1, b: int = 2) -> int:   # hàm cộng\n'
    '    tong = a + b        # cộng lại\n'
    '    if tong > 10:\n'
    '        return 10\n'
    '    elif tong < 0:      # âm thì kẹp về 0\n'
    '        return 0\n'
    '    else:\n'
    '        return tong\n'
    '\n'
    '\n'
    'GHI = ["# đây là chuỗi", ""]    # đây mới là chú thích\n'
)


def _tep():
    ra = []
    for d in THU_MUC:
        t = GOC / d
        if t.is_dir():
            ra += sorted(p for p in t.glob("*.py") if p.is_file())
    return ra


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        import libcst as cst
    except ImportError:
        print("KHÔNG ĐO ĐƯỢC: chưa cài libcst. Xem lời dặn đầu tệp.")
        return 2                       # không đo được, KHÁC với trượt

    tep = _tep()
    if not tep:
        print("KHÔNG ĐO ĐƯỢC: không tìm thấy tệp .py nào")
        return 2

    # ---- phép 1: mở rồi lưu, không sửa gì -------------------------------
    khop = hong = 0
    crlf = 0
    t0 = time.perf_counter()
    for p in tep:
        b = p.read_bytes()
        if b"\r\n" in b:
            crlf += 1
        try:
            if cst.parse_module(b.decode("utf-8")).code.encode("utf-8") == b:
                khop += 1
        except Exception:
            hong += 1
    t_mo = time.perf_counter() - t0

    # ---- phép 2: CHẠM vào mọi câu lệnh rồi lưu --------------------------
    # Phép 1 không đủ: chính lỗi đã bắt ở app thẻ là test mở-rồi-lưu đi vòng
    # qua bộ sinh mã. Ở đây ép mọi nút đi qua `with_changes` — đúng đường mà
    # app sẽ đi khi người dùng sửa một ô.
    class GoLaiYCu(cst.CSTTransformer):
        def __init__(self):
            self.cham = 0

        def leave_Assign(self, cu, moi):
            self.cham += 1
            return moi.with_changes(targets=moi.targets, value=moi.value)

        def leave_FunctionDef(self, cu, moi):
            self.cham += 1
            return moi.with_changes(name=moi.name, params=moi.params)

        def leave_If(self, cu, moi):
            self.cham += 1
            return moi.with_changes(test=moi.test)

        def leave_Return(self, cu, moi):
            self.cham += 1
            return moi.with_changes(value=moi.value)

        def leave_For(self, cu, moi):
            self.cham += 1
            return moi.with_changes(target=moi.target, iter=moi.iter)

    khop2 = cham = 0
    lech2 = []
    t0 = time.perf_counter()
    for p in tep:
        b = p.read_bytes()
        try:
            bd = GoLaiYCu()
            ra = cst.parse_module(b.decode("utf-8")).visit(bd).code
            cham += bd.cham
        except Exception:
            lech2.append(p.name)
            continue
        if ra.encode("utf-8") == b:
            khop2 += 1
        else:
            lech2.append(p.name)
    t_sua = time.perf_counter() - t0

    # ---- phép 3: đổi thật một tên biến ----------------------------------
    class DoiTen(cst.CSTTransformer):
        def leave_Name(self, cu, moi):
            return (moi.with_changes(value="tong_moi")
                    if moi.value == "tong" else moi)

    ra3 = cst.parse_module(MAU).visit(DoiTen()).code
    g, r = MAU.splitlines(), ra3.splitlines()
    doi = [i + 1 for i in range(len(g)) if g[i] != r[i]]
    can_doi = [i + 1 for i in range(len(g)) if "tong" in g[i]]
    giu = [
        ("chú kiểu + giá trị mặc định", "a: int = 1, b: int = 2"),
        ("kiểu trả về", "-> int"),
        ("elif (không thành else)", "    elif tong_moi < 0:"),
        ("chú thích cuối dòng trên elif", "# âm thì kẹp về 0"),
        ("dấu thăng bên trong chuỗi", '"# đây là chuỗi"'),
        ("chú thích cuối dòng trên def", "# hàm cộng"),
    ]
    thieu = [n for n, m in giu if m not in ra3]

    dat = (khop == len(tep) and khop2 == len(tep)
           and doi == can_doi and not thieu)

    print("=" * 64)
    print("  LIBCST trên %d tệp .py của kho (%d tệp CRLF)" % (len(tep), crlf))
    print("=" * 64)
    print("  1. mở rồi lưu, không sửa gì")
    print("     khớp từng byte : %d/%d   (%.2fs, %.0f ms/tệp)"
          % (khop, len(tep), t_mo, 1000 * t_mo / len(tep)))
    print("     không đọc được : %d" % hong)
    print("  2. CHẠM vào mọi câu lệnh rồi lưu")
    print("     nút đã chạm    : %d" % cham)
    print("     khớp từng byte : %d/%d   (%.2fs)" % (khop2, len(tep), t_sua))
    if lech2:
        print("     tệp lệch       : %s" % lech2[:5])
    print("  3. đổi thật một tên biến trên mẫu 14 dòng")
    print("     dòng bị đổi    : %s" % doi)
    print("     dòng đáng đổi  : %s   %s"
          % (can_doi, "khớp" if doi == can_doi else "*** LỆCH ***"))
    for n, m in giu:
        print("     giữ %-32s: %s" % (n, "CÓ" if m in ra3 else "KHÔNG"))
    print("=" * 64)
    print("  %s" % ("ĐẠT — LibCST thay được bộ đọc/sinh mã tự đẽo"
                    if dat else "KHÔNG ĐẠT — xem dòng có dấu sao ở trên"))
    print("=" * 64)
    return 0 if dat else 1


if __name__ == "__main__":
    raise SystemExit(main())
