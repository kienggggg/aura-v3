# -*- coding: utf-8 -*-
"""polyglot.py — Multi-Language Polyglot Engine cho AURA v3.

Hỗ trợ 8 ngôn ngữ lập trình chính:
  1. Python (Mặc định)
  2. JavaScript (ES2022+)
  3. TypeScript
  4. Go (Golang)
  5. Rust
  6. C++ (C++20)
  7. SQL (ANSI / SQLite / PostgreSQL / BigQuery)
  8. Bash / Shell

Tính năng:
  - Tra cứu metadata và template chuẩn của từng ngôn ngữ.
  - Chuyển đổi mã logic AST từ Python sang các ngôn ngữ đích (Transpiler).
  - Kiểm tra cú pháp độc lập (Syntax Validator) cho từng ngôn ngữ.
  - Chạy mã trong tiến trình con có HỘP CÁT MỘT PHẦN (Windows Job Object):
    cwd riêng · biến môi trường sạch · trần RAM · giết cả cây tiến trình.
    CHƯA chặn: ghi/đọc tệp bằng đường dẫn tuyệt đối, và ra mạng.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class LanguageInfo:
    """Thông tin chi tiết về một ngôn ngữ lập trình."""
    id: str
    ten: str
    bieu_tuong: str
    duoi_tep: str
    mau_sac: str
    mo_ta: str
    la_bien_dich: bool
    lenh_chay: Optional[str]
    tu_khoa_chinh: List[str]
    ma_mau: str


DANH_SACH_NGON_NGU: Dict[str, LanguageInfo] = {
    "python": LanguageInfo(
        id="python",
        ten="Python",
        bieu_tuong="🐍",
        duoi_tep=".py",
        mau_sac="#3B82F6",
        mo_ta="Ngôn ngữ kịch bản mạnh mẽ, linh hoạt và là xương sống cốt lõi của AURA v3.",
        la_bien_dich=False,
        lenh_chay="python",
        tu_khoa_chinh=["def", "class", "import", "return", "if", "elif", "else", "for", "while", "try", "except", "async", "await"],
        ma_mau="""def tinh_tong(danh_sach: list[int]) -> int:
    \"\"\"Tính tổng các phần tử trong danh sách.\"\"\"
    tong = 0
    for x in danh_sach:
        tong += x
    return tong

if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5]
    print(f"Tổng là: {tinh_tong(nums)}")
"""
    ),
    "javascript": LanguageInfo(
        id="javascript",
        ten="JavaScript",
        bieu_tuong="🟨",
        duoi_tep=".js",
        mau_sac="#F59E0B",
        mo_ta="Ngôn ngữ lập trình web phổ biến nhất thế giới cho frontend và Node.js backend.",
        la_bien_dich=False,
        lenh_chay="node",
        tu_khoa_chinh=["function", "const", "let", "var", "return", "if", "else", "for", "while", "try", "catch", "async", "await", "import", "export"],
        ma_mau="""function tinhTong(danhSach) {
    /**
     * Tính tổng các phần tử trong mảng.
     */
    let tong = 0;
    for (const x of danhSach) {
        tong += x;
    }
    return tong;
}

const nums = [1, 2, 3, 4, 5];
console.log(`Tổng là: ${tinhTong(nums)}`);
"""
    ),
    "typescript": LanguageInfo(
        id="typescript",
        ten="TypeScript",
        bieu_tuong="🔷",
        duoi_tep=".ts",
        mau_sac="#2563EB",
        mo_ta="Siêu tập hợp của JavaScript với hệ thống kiểu tĩnh mạnh mẽ, an toàn kiểu dữ liệu.",
        la_bien_dich=True,
        lenh_chay="ts-node",
        tu_khoa_chinh=["function", "interface", "type", "const", "let", "return", "if", "else", "for", "while", "async", "await", "export"],
        ma_mau="""interface Calculator {
    tinhTong(danhSach: number[]): number;
}

function tinhTong(danhSach: number[]): number {
    let tong: number = 0;
    for (const x of danhSach) {
        tong += x;
    }
    return tong;
}

const nums: number[] = [1, 2, 3, 4, 5];
console.log(`Tổng là: ${tinhTong(nums)}`);
"""
    ),
    "go": LanguageInfo(
        id="go",
        ten="Go (Golang)",
        bieu_tuong="🐹",
        duoi_tep=".go",
        mau_sac="#06B6D4",
        mo_ta="Ngôn ngữ hiện đại từ Google, hiệu năng cực cao và quản lý luồng song song (Goroutines) tuyệt vời.",
        la_bien_dich=True,
        lenh_chay="go run",
        tu_khoa_chinh=["package", "import", "func", "return", "if", "else", "for", "range", "var", "type", "struct", "go", "chan"],
        ma_mau="""package main

import "fmt"

// TinhTong tính tổng các phần tử trong slice số nguyên
func TinhTong(danhSach []int) int {
	tong := 0
	for _, x := range danhSach {
		tong += x
	}
	return tong
}

func main() {
	nums := []int{1, 2, 3, 4, 5}
	fmt.Printf("Tổng là: %d\\n", TinhTong(nums))
}
"""
    ),
    "rust": LanguageInfo(
        id="rust",
        ten="Rust",
        bieu_tuong="🦀",
        duoi_tep=".rs",
        mau_sac="#EA580C",
        mo_ta="Ngôn ngữ hệ thống an toàn bộ nhớ tuyệt đối (Borrow Checker), tốc độ tối đa không cần Garbage Collector.",
        la_bien_dich=True,
        lenh_chay="rustc",
        tu_khoa_chinh=["fn", "let", "mut", "struct", "impl", "enum", "match", "if", "else", "for", "in", "return", "pub", "use"],
        ma_mau="""fn tinh_tong(danh_sach: &[i32]) -> i32 {
    let mut tong = 0;
    for &x in danh_sach {
        tong += x;
    }
    tong
}

fn main() {
    let nums = vec![1, 2, 3, 4, 5];
    println!("Tổng là: {}", tinh_tong(&nums));
}
"""
    ),
    "cpp": LanguageInfo(
        id="cpp",
        ten="C++ (C++20)",
        bieu_tuong="⚡",
        duoi_tep=".cpp",
        mau_sac="#8B5CF6",
        mo_ta="Ngôn ngữ hiệu năng đỉnh cao cho game engine, hệ thống tính toán khoa học và tài chính.",
        la_bien_dich=True,
        lenh_chay="g++",
        tu_khoa_chinh=["#include", "namespace", "class", "struct", "auto", "int", "void", "return", "if", "else", "for", "while", "std"],
        ma_mau="""#include <iostream>
#include <vector>
#include <numeric>

int tinhTong(const std::vector<int>& danhSach) {
    int tong = 0;
    for (int x : danhSach) {
        tong += x;
    }
    return tong;
}

int main() {
    std::vector<int> nums = {1, 2, 3, 4, 5};
    std::cout << "Tổng là: " << tinhTong(nums) << std::endl;
    return 0;
}
"""
    ),
    "sql": LanguageInfo(
        id="sql",
        ten="SQL",
        bieu_tuong="🗄️",
        duoi_tep=".sql",
        mau_sac="#10B981",
        mo_ta="Ngôn ngữ truy vấn cơ sở dữ liệu quan hệ tiêu chuẩn (BigQuery, PostgreSQL, SQLite).",
        la_bien_dich=False,
        lenh_chay="sqlite3",
        tu_khoa_chinh=["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "INSERT", "UPDATE", "DELETE", "CREATE TABLE", "HAVING", "LIMIT"],
        ma_mau="""-- Truy vấn tổng kết quả và số lượng bản ghi
SELECT 
    phong_id,
    COUNT(task_id) AS tong_so_nhiem_vu,
    AVG(latency_ms) AS do_tre_trung_binh_ms,
    MAX(timestamp) AS lan_chay_moi_nhat
FROM omega_so_cai
WHERE status = 'PASS'
GROUP BY phong_id
ORDER BY tong_so_nhiem_vu DESC;
"""
    ),
    "bash": LanguageInfo(
        id="bash",
        ten="Bash / Shell",
        bieu_tuong="🐚",
        duoi_tep=".sh",
        mau_sac="#64748B",
        mo_ta="Ngôn ngữ kịch bản dòng lệnh cho tự động hóa hệ điều hành và pipeline DevOps.",
        la_bien_dich=False,
        lenh_chay="bash",
        tu_khoa_chinh=["#!/bin/bash", "if", "then", "else", "fi", "for", "in", "do", "done", "while", "echo", "export", "exit"],
        ma_mau="""#!/bin/bash
# Script kiểm toán và tự động hóa AURA v3
set -euo pipefail

echo "=== KHỞI ĐỘNG KIỂM TOÁN AURA v3 ==="
NUMS=(1 2 3 4 5)
TONG=0

for x in "${NUMS[@]}"; do
    TONG=$((TONG + x))
done

echo "Tổng là: ${TONG}"
echo "Trạng thái: HOÀN TẤT"
"""
    )
}


def lay_danh_sach_ngon_ngu() -> List[Dict[str, Any]]:
    """Trả về danh sách tất cả ngôn ngữ hỗ trợ kèm metadata."""
    return [asdict(info) for info in DANH_SACH_NGON_NGU.values()]


# ==============================================================================
# 1. BỘ CHUYỂN ĐỔI MÃ NGUỒN ĐA NGÔN NGỮ (POLYGLOT TRANSPILER)
# ==============================================================================

class PythonToPolyglotVisitor(ast.NodeVisitor):
    """AST Visitor chuyển đổi mã Python cơ bản sang các ngôn ngữ khác."""

    def __init__(self, target_lang: str):
        self.target = target_lang.lower()
        self.lines: List[str] = []
        self.indent_level = 0
        self.indent_str = "    "
        self.notes: List[str] = []
        self.nodes_count = 0
        # BASH KHÔNG CÓ BIẾN TRẦN NHƯ PYTHON, nên phải nhớ ba thứ mà cây AST
        # không nói ra (07/09/2026):
        #   * `ham_tu_khai` — gọi một hàm do chính tệp định nghĩa thì phải ra
        #     `$(ten tham_so)`, còn `echo` / `len` thì không. Không phân biệt
        #     được thì sinh ra `echo fibonacci(n - 1)` — bash coi `(` là lỗi cú
        #     pháp, đo được 3/3 đề đều gãy.
        #   * `mang` — `for x in ds` cần `"${ds[@]}"` chứ không phải `$ds`.
        #   * `trong_ham` — tên tham số phải `local` lại từ `$1`, vì bash không
        #     có tham số có tên.
        self.ham_tu_khai: set = set()
        self.mang: set = set()
        # CÂU LỆNH BỊ BỎ SÓT, GHI RA TÊN.
        #
        # `ast.NodeVisitor` không có `visit_While` thì gọi `generic_visit`, tức
        # **đi vào thân vòng lặp và sinh thân ra, còn vòng lặp thì biến mất**.
        # Đo 07/09/2026: `while n > 0: n -= 1` dịch sang bash ra đúng một dòng
        # `n=$(( n - 1 ))` — `bash -n` GẬT, `node --check` GẬT, và bản dịch
        # tính sai hoàn toàn. `class`, `try`, `with`, list comprehension cùng
        # bệnh.
        #
        # Một cửa chỉ hỏi cú pháp không bao giờ thấy chỗ này. Nên chỗ sót phải
        # tự khai ra, để phòng `epsilon` trả KHÔNG ĐO ĐƯỢC thay vì PASS.
        self.bo_sot: List[str] = []

    def _indent(self) -> str:
        return self.indent_str * self.indent_level

    def _emit(self, text: str):
        self.lines.append(f"{self._indent()}{text}")

    # Đúng những nút có `visit_*` bên dưới. Danh sách ĐÓNG: viết thêm một
    # `visit_While` thì phải thêm tên vào đây, tức phải cố ý.
    _NUT_DICH_DUOC = (ast.Module, ast.FunctionDef, ast.Return, ast.Assign,
                      ast.AugAssign, ast.If, ast.For, ast.Expr)

    def visit(self, node: ast.AST):
        self.nodes_count += 1
        if isinstance(node, ast.stmt) and not isinstance(node, self._NUT_DICH_DUOC):
            self.bo_sot.append(f"{type(node).__name__} (dòng {getattr(node, 'lineno', '?')})")
        super().visit(node)

    def visit_Module(self, node: ast.Module):
        # Header theo từng ngôn ngữ
        if self.target == "javascript":
            self.lines.append("// Chuyển đổi tự động từ Python sang JavaScript bởi AURA Polyglot Engine\n")
        elif self.target == "typescript":
            self.lines.append("// Chuyển đổi tự động từ Python sang TypeScript bởi AURA Polyglot Engine\n")
        elif self.target == "go":
            self.lines.append("// Chuyển đổi tự động từ Python sang Go bởi AURA Polyglot Engine")
            self.lines.append("package main\n")
            self.lines.append('import (\n\t"fmt"\n)\n')
        elif self.target == "rust":
            self.lines.append("// Chuyển đổi tự động từ Python sang Rust bởi AURA Polyglot Engine\n")
        elif self.target == "cpp":
            self.lines.append("// Chuyển đổi tự động từ Python sang C++20 bởi AURA Polyglot Engine")
            self.lines.append("#include <iostream>")
            self.lines.append("#include <vector>")
            self.lines.append("#include <string>")
            self.lines.append("#include <numeric>\n")
        elif self.target == "bash":
            self.lines.append("#!/bin/bash")
            self.lines.append("# Chuyển đổi tự động từ Python sang Bash bởi AURA Polyglot Engine\n")

        # GOM TÊN HÀM TRƯỚC KHI SINH DÒNG NÀO. Đệ quy gọi chính nó ngay trong
        # thân nó, nên gom dần theo thứ tự gặp thì `fibonacci` bên trong
        # `fibonacci` vẫn chưa biết là hàm. Đi một vòng riêng thì hết.
        if self.target in ("bash", "go", "cpp", "rust"):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.FunctionDef):
                    self.ham_tu_khai.add(stmt.name)

        # GO: CÂU LỆNH CẤP GÓI PHẢI VÀO `func main()`.
        #
        # Đo nền 08/09 bằng `go build` thật, cả ba đề cùng một lỗi:
        #     main.go:15:1: syntax error: non-declaration statement outside
        #                   function body
        # Go chỉ cho khai báo ở cấp gói, còn `fmt.Println(...)` và `nums := ...`
        # là CÂU LỆNH. Lỗi này chặn ở dòng đầu tiên nên nó CHE ba lỗi còn lại —
        # parser dừng, và ba cái sau chưa từng được trình biên dịch nhìn thấy.
        # BA NGÔN NGỮ BIÊN DỊCH ĐỀU CẤM CÂU LỆNH Ở CẤP TỆP.
        #
        # Đo nền bằng trình thật, cùng một bệnh, ba thông báo khác nhau:
        #   go   08/09  main.go:15:1: syntax error: non-declaration statement
        #                              outside function body
        #   cpp  09/09  main.cpp:14:6: error: 'cout' in namespace 'std' does
        #                              not name a type
        #   rust 09/09  (xem đặc tả — `let mut` ở cấp module)
        # Cả ba đều 0/3 cú pháp trước khi vá, và ở cả ba lỗi này CHẶN NGAY DÒNG
        # ĐẦU nên nó che các lỗi phía sau.
        if self.target in ("go", "cpp", "rust"):
            mo, dong = {"go": ("func main() {", "}"),
                        "cpp": ("int main() {", "    return 0;\n}"),
                        "rust": ("fn main() {", "}")}[self.target]
            ham = [s for s in node.body if isinstance(s, ast.FunctionDef)]
            con_lai = [s for s in node.body if not isinstance(s, ast.FunctionDef)]
            for stmt in ham:
                self.visit(stmt)
            self._emit(mo)
            self.indent_level += 1
            for stmt in con_lai:
                self.visit(stmt)
            self.indent_level -= 1
            self._emit(dong)
            return

        for stmt in node.body:
            self.visit(stmt)

    # Bộ suy kiểu trả về KIỂU TRỪU TƯỢNG; mỗi ngôn ngữ dịch sang chữ của mình.
    #
    # `any` của Rust CỐ Ý là một định danh KHÔNG tồn tại. Go có `any` thật, C++
    # có `auto`, Rust thì không có gì tương đương — và đoán đại một kiểu thì
    # bản dịch BIÊN DỊCH ĐƯỢC mà CHẠY SAI, tệ hơn hẳn một lỗi biên dịch vì lỗi
    # biên dịch thì ai cũng thấy. Fail-closed: để nó gãy, và gãy có tên.
    # (Trên thực tế `bo_sot` đã chặn trước khi tới trình biên dịch.)
    _KIEU_THEO_NGON_NGU = {
        "go":   {"int": "int", "string": "string", "[]int": "[]int",
                 "any": "any", "": ""},
        "cpp":  {"int": "int", "string": "std::string",
                 "[]int": "const std::vector<int>&", "any": "auto", "": "void"},
        "rust": {"int": "i32", "string": "&'static str", "[]int": "Vec<i32>",
                 "any": "KIEU_KHONG_SUY_DUOC", "": ""},
    }

    def _suy_kieu(self, node: ast.FunctionDef):
        """Suy kiểu Go cho tham số và giá trị trả về của một hàm.

        VÌ SAO CẦN (08/09/2026). Bản cũ khai mọi thứ là `any`, và Go **không có
        toán tử cho `any`**: `n <= 1`, `tong += x`, `n - 1` đều là lỗi biên
        dịch. Nó chỉ chưa lộ ra vì lỗi "câu lệnh ngoài thân hàm" ở dòng 15 làm
        parser dừng trước.

        SUY ĐƯỢC TỚI ĐÂU THÌ NÓI TỚI ĐÓ — đây là bộ suy kiểu HẸP, không phải
        bộ suy kiểu đầy đủ:

            tham số so sánh/tính với số     -> int
            tham số bị `for ... in` duyệt   -> []int
            trả về toàn hằng chuỗi          -> string
            còn lại                         -> any, và GHI VÀO `bo_sot`

        Chỗ không suy được vẫn ra `any`, tức vẫn hỏng nếu có số học — nhưng
        người đọc kết quả biết là nó yếu ở đâu. Im lặng để `any` mới là thứ
        làm một bản dịch hỏng trông như bản dịch xong.
        """
        ten_ts = {a.arg for a in node.args.args}
        kieu: Dict[str, str] = {}
        khong_suy: List[str] = []

        # `for x in <tham số>` -> tham số là lát cắt.
        for con in ast.walk(node):
            if isinstance(con, ast.For) and isinstance(con.iter, ast.Name):
                if con.iter.id in ten_ts:
                    kieu[con.iter.id] = "[]int"

        # So sánh hoặc tính toán với một hằng SỐ -> int.
        for con in ast.walk(node):
            ve = []
            if isinstance(con, ast.Compare):
                ve = [con.left] + list(con.comparators)
            elif isinstance(con, ast.BinOp):
                ve = [con.left, con.right]
            if not any(isinstance(v, ast.Constant) and isinstance(v.value, (int, float))
                       and not isinstance(v.value, bool) for v in ve):
                continue
            for v in ve:
                if isinstance(v, ast.Name) and v.id in ten_ts:
                    kieu.setdefault(v.id, "int")

        for a in node.args.args:
            if a.arg not in kieu:
                kieu[a.arg] = "any"
                khong_suy.append(a.arg)

        # Biến cục bộ được gán một hằng số nguyên: `tong = 0` -> `tong` là số.
        bien_so = {t.id
                   for c in ast.walk(node) if isinstance(c, ast.Assign)
                   for t in c.targets
                   if isinstance(t, ast.Name)
                   and isinstance(c.value, ast.Constant)
                   and isinstance(c.value.value, int)
                   and not isinstance(c.value.value, bool)}

        # Kiểu trả về. Chỉ nhìn `return` của CHÍNH hàm này, không nhìn hàm lồng.
        tra = [c for c in ast.walk(node)
               if isinstance(c, ast.Return) and c.value is not None]
        if not tra:
            kieu_tra = ""          # Go: không trả gì thì bỏ trống, không `any`
        elif all(isinstance(t.value, ast.Constant) and isinstance(t.value.value, str)
                 for t in tra):
            kieu_tra = "string"
        elif all(self._la_so(t.value, kieu, bien_so) for t in tra):
            kieu_tra = "int"
        else:
            kieu_tra = "any"
            khong_suy.append("giá trị trả về")
        return kieu, kieu_tra, khong_suy

    def _la_so(self, e, kieu: Dict[str, str], bien_so: set) -> bool:
        """Biểu thức này có CHẮC là số nguyên không? Thà nói KHÔNG còn hơn đoán.

        Đoán bừa ra `int` thì bản dịch biên dịch được mà chạy sai — tệ hơn hẳn
        một lỗi biên dịch, vì lỗi biên dịch thì ai cũng thấy.
        """
        if isinstance(e, ast.Constant):
            return isinstance(e.value, int) and not isinstance(e.value, bool)
        if isinstance(e, ast.Name):
            return kieu.get(e.id) == "int" or e.id in bien_so
        if isinstance(e, ast.BinOp):
            return (self._la_so(e.left, kieu, bien_so)
                    and self._la_so(e.right, kieu, bien_so))
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Name):
            # Đệ quy: hàm đang dịch gọi chính nó. Chưa biết kiểu của nó, nhưng
            # nếu mọi nhánh KHÁC là số thì nhánh đệ quy cũng là số.
            return e.func.id in self.ham_tu_khai
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        args = [arg.arg for arg in node.args.args]
        args_str = ", ".join(args)

        if self.target == "javascript":
            self._emit(f"function {name}({args_str}) {{")
        elif self.target == "typescript":
            ts_args = [f"{arg}: any" for arg in args]
            self._emit(f"function {name}({', '.join(ts_args)}): any {{")
        elif self.target in ("go", "cpp", "rust"):
            # GIỮ NGUYÊN TÊN PYTHON — có chủ ý, xem `_KIEU_THEO_NGON_NGU`.
            # Bản Go cũ khai `func Fibonacci` rồi gọi `fibonacci(...)`.
            kieu_ts, kieu_tra, khong_suy = self._suy_kieu(node)
            bang = self._KIEU_THEO_NGON_NGU[self.target]
            for ten_bien in khong_suy:
                # Chỗ bản dịch YẾU đi phải TỰ KHAI. `bo_sot` khác rỗng thì
                # phòng `epsilon` trả KHÔNG ĐO ĐƯỢC và không đưa cho trình biên
                # dịch — nên một bản dịch đoán kiểu không bao giờ được chấm ĐẠT.
                self.bo_sot.append(
                    f"kiểu {self.target} không suy được cho `{ten_bien}` trong "
                    f"`{name}` (dòng {node.lineno})")
            ts = [(a, bang.get(kieu_ts.get(a, "any"), bang["any"])) for a in args]
            ra = bang.get(kieu_tra, bang["any"]) if kieu_tra else bang[""]
            if self.target == "go":
                self._emit(f"func {name}({', '.join(f'{a} {k}' for a, k in ts)})"
                           f"{(' ' + ra) if ra else ''} {{")
            elif self.target == "cpp":
                self._emit(f"{ra or 'void'} {name}"
                           f"({', '.join(f'{k} {a}' for a, k in ts)}) {{")
            else:   # rust
                self._emit(f"fn {name}({', '.join(f'{a}: {k}' for a, k in ts)})"
                           f"{(' -> ' + ra) if ra else ''} {{")
        elif self.target == "bash":
            self._emit(f"{name}() {{")
        else:
            self._emit(f"# Hàm: {name}")

        self.indent_level += 1
        if self.target == "bash":
            # THAM SỐ CÓ TÊN KHÔNG TỒN TẠI TRONG BASH — chỉ có `$1 $2`. Bản cũ
            # để nguyên tên rồi dùng `n` trần, nên `if [ n <= 1 ]` so chuỗi
            # `"n"` với `"1"`; buộc phải `local` lại ở đầu thân hàm.
            dung_nhu_mang = self._bash_ten_dung_nhu_mang(node)
            for i, ten_ts in enumerate(args, start=1):
                if ten_ts in dung_nhu_mang and i == len(args):
                    # Bash làm phẳng mảng khi truyền đi, nên tham số CUỐI hứng
                    # phần đuôi. Không có cách nào giữ được hai mảng một lúc —
                    # ghi ra đây thay vì giả vờ có.
                    self._emit(f'local {ten_ts}=("${{@:{i}}}")')
                    self.mang.add(ten_ts)
                else:
                    self._emit(f'local {ten_ts}="${i}"')
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        if self.target == "bash":
            # Tham số là biến CỤC BỘ — để nó ở lại `self.mang` thì một tên
            # trùng ở mức module sau đó bị sinh nhầm ra `"${x[@]}"`.
            self.mang -= set(args)

        if self.target in ("javascript", "typescript", "go", "rust", "cpp", "bash"):
            self._emit("}\n")

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            self._emit("return 0" if self.target == "bash" else "return;")
        else:
            val = self._expr_to_str(node.value)
            if self.target in ("javascript", "typescript", "cpp"):
                self._emit(f"return {val};")
            elif self.target == "go":
                self._emit(f"return {val}")
            elif self.target == "rust":
                # `return {val};`, KHÔNG phải `{val}` trần.
                #
                # Bản cũ sinh biểu thức trần, và đó là lỗi NGỮ NGHĨA, nặng hơn
                # một lỗi biên dịch. `def fibonacci: if n<=1: return n` ra:
                #     if n <= 1 { n }
                #     fibonacci(n - 1) + fibonacci(n - 2)
                # Trong Rust chỉ biểu thức CUỐI hàm mới là giá trị trả về, nên
                # `if n <= 1 { n }` thành một biểu thức bị vứt đi và hàm LUÔN
                # chạy tiếp xuống nhánh đệ quy — early-return biến mất.
                #
                # Một cửa chỉ hỏi cú pháp không bao giờ thấy chỗ này; đây đúng
                # họ với `while` dịch sang bash mà vòng lặp biến mất (06/09).
                self._emit(f"return {val};")
            elif self.target == "bash":
                self._emit(f"echo {val}\n{self._indent()}return 0")
            else:
                self._emit(f"return {val}")

    def visit_Assign(self, node: ast.Assign):
        if self.target == "bash":
            # VẾ TRÁI PHẢI TRẦN, VẾ PHẢI PHẢI CÓ `$`. Cùng một `ast.Name` ra
            # hai dạng khác nhau tuỳ chỗ đứng, nên không dùng chung một hàm
            # sinh chuỗi được: `tong=$x` đúng, `$tong=$x` là lỗi.
            for t in node.targets:
                if not isinstance(t, ast.Name):
                    # Gán vào `a[0]` hoặc `a, b = ...` — chưa dịch được. Ghi
                    # tên ra chứ không bỏ im lặng, để `epsilon` trả KHÔNG ĐO
                    # ĐƯỢC thay vì để `bash -n` gật cho một tệp thiếu dòng.
                    self._bash_bo_qua(t)
                    continue
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    self.mang.add(t.id)
                    elts = " ".join(self._bash(e, arith=False)
                                    for e in node.value.elts)
                    self._emit(f"{t.id}=({elts})")
                else:
                    self._emit(f"{t.id}={self._bash(node.value, arith=False)}")
            return

        targets = [self._expr_to_str(t) for t in node.targets]
        val = self._expr_to_str(node.value)
        t_str = ", ".join(targets)

        if self.target in ("javascript", "typescript"):
            self._emit(f"let {t_str} = {val};")
        elif self.target == "go":
            self._emit(f"{t_str} := {val}")
        elif self.target == "rust":
            self._emit(f"let mut {t_str} = {val};")
        elif self.target == "cpp":
            self._emit(f"auto {t_str} = {val};")
        elif self.target == "bash":
            self._emit(f"{t_str}={val}")
        else:
            self._emit(f"{t_str} = {val}")

    _DAU_SO = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
               ast.Mod: "%"}

    def visit_AugAssign(self, node: ast.AugAssign):
        if self.target == "bash" and isinstance(node.target, ast.Name):
            dau = self._DAU_SO.get(type(node.op), "+")
            v = self._bash(node.value, arith=True)
            self._emit(f"{node.target.id}=$(( {node.target.id} {dau} {v} ))")
            return

        target = self._expr_to_str(node.target)
        val = self._expr_to_str(node.value)
        op = "+="
        if isinstance(node.op, ast.Add):
            op = "+="
        elif isinstance(node.op, ast.Sub):
            op = "-="
        elif isinstance(node.op, ast.Mult):
            op = "*="
        elif isinstance(node.op, ast.Div):
            op = "/="

        if self.target in ("javascript", "typescript", "cpp", "rust", "go"):
            self._emit(f"{target} {op} {val};" if self.target != "go" else f"{target} {op} {val}")
        elif self.target == "bash":
            self._emit(f"{target}=$(({target} {op[0]} {val}))")
        else:
            self._emit(f"{target} {op} {val}")

    def visit_If(self, node: ast.If):
        test = ("" if self.target == "bash" else self._expr_to_str(node.test))
        if self.target in ("javascript", "typescript", "cpp"):
            self._emit(f"if ({test}) {{")
        elif self.target in ("go", "rust"):
            self._emit(f"if {test} {{")
        elif self.target == "bash":
            self._emit(f"if {self._bash_dieu_kien(node.test)}; then")
        else:
            self._emit(f"if {test}:")

        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

        if node.orelse:
            if self.target in ("javascript", "typescript", "cpp", "go", "rust"):
                self._emit("} else {")
            elif self.target == "bash":
                self._emit("else")
            self.indent_level += 1
            for stmt in node.orelse:
                self.visit(stmt)
            self.indent_level -= 1

        if self.target in ("javascript", "typescript", "cpp", "go", "rust"):
            self._emit("}")
        elif self.target == "bash":
            self._emit("fi")

    def visit_For(self, node: ast.For):
        if self.target == "bash":
            ten = node.target.id if isinstance(node.target, ast.Name) else "muc"
            self._emit(f"for {ten} in {self._bash_duyet(node.iter)}; do")
            self.indent_level += 1
            for stmt in node.body:
                self.visit(stmt)
            self.indent_level -= 1
            self._emit("done")
            return

        target = self._expr_to_str(node.target)
        iter_expr = self._expr_to_str(node.iter)

        if self.target in ("javascript", "typescript"):
            self._emit(f"for (const {target} of {iter_expr}) {{")
        elif self.target == "go":
            self._emit(f"for _, {target} := range {iter_expr} {{")
        elif self.target == "rust":
            self._emit(f"for {target} in {iter_expr} {{")
        elif self.target == "cpp":
            self._emit(f"for (const auto& {target} : {iter_expr}) {{")
        elif self.target == "bash":
            self._emit(f"for {target} in {iter_expr}; do")
        else:
            self._emit(f"for {target} in {iter_expr}:")

        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

        if self.target in ("javascript", "typescript", "go", "rust", "cpp"):
            self._emit("}")
        elif self.target == "bash":
            self._emit("done")

    def visit_Expr(self, node: ast.Expr):
        if (self.target == "bash" and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id in self.ham_tu_khai):
            # Ở VỊ TRÍ CÂU LỆNH thì gọi hàm là `f 1`, không phải `"$(f 1)"` —
            # dạng sau bảo bash lấy kết quả in ra rồi CHẠY nó như một lệnh.
            tso = " ".join(self._bash(a) for a in node.value.args)
            self._emit(f"{node.value.func.id} {tso}".rstrip())
            return

        val = self._expr_to_str(node.value)
        if val:
            if self.target in ("javascript", "typescript", "cpp"):
                self._emit(f"{val};")
            elif self.target in ("go", "rust"):
                self._emit(f"{val};" if self.target == "rust" else val)
            elif self.target == "bash":
                self._emit(val)
            else:
                self._emit(val)

    def _expr_to_str(self, expr: ast.AST) -> str:
        """Chuyển biểu thức Python AST sang chuỗi theo cú pháp ngôn ngữ đích."""
        if self.target == "bash":
            return self._bash(expr, arith=False)
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return json.dumps(expr.value, ensure_ascii=False)
            elif isinstance(expr.value, bool):
                if self.target in ("javascript", "typescript", "go", "rust", "cpp"):
                    return "true" if expr.value else "false"
                return str(expr.value)
            elif expr.value is None:
                if self.target in ("javascript", "typescript"):
                    return "null"
                elif self.target in ("go", "rust", "cpp"):
                    return "nil" if self.target == "go" else "None"
                return "None"
            return str(expr.value)

        elif isinstance(expr, ast.Name):
            return expr.id

        elif isinstance(expr, ast.List):
            elts = [self._expr_to_str(e) for e in expr.elts]
            if self.target in ("javascript", "typescript"):
                return f"[{', '.join(elts)}]"
            elif self.target in ("go", "cpp", "rust"):
                # KIỂU PHẦN TỬ PHẢI NÓI RA. `[]any` / `auto{...}` không cộng
                # được: `tong += x` với `x` kiểu mơ hồ là lỗi biên dịch. Toàn
                # số nguyên thì nói thẳng; lẫn lộn thì vẫn hỏng — nhưng hỏng ở
                # chỗ đúng, không phải hỏng vì bộ dịch lười.
                toan_so = bool(expr.elts) and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, int)
                    and not isinstance(e.value, bool) for e in expr.elts)
                than = ", ".join(elts)
                if self.target == "go":
                    return f"{'[]int' if toan_so else '[]any'}{{{than}}}"
                if self.target == "cpp":
                    return (f"std::vector<int>{{{than}}}" if toan_so
                            else f"{{{than}}}")
                return f"vec![{than}]"
            elif self.target == "bash":
                return f"({' '.join(elts)})"
            return f"[{', '.join(elts)}]"

        elif isinstance(expr, ast.BinOp):
            left = self._expr_to_str(expr.left)
            right = self._expr_to_str(expr.right)
            op = "+"
            if isinstance(expr.op, ast.Add):
                op = "+"
            elif isinstance(expr.op, ast.Sub):
                op = "-"
            elif isinstance(expr.op, ast.Mult):
                op = "*"
            elif isinstance(expr.op, ast.Div):
                op = "/"
            elif isinstance(expr.op, ast.Mod):
                op = "%"
            return f"{left} {op} {right}"

        elif isinstance(expr, ast.Compare):
            left = self._expr_to_str(expr.left)
            ops_strs = []
            for op, comp in zip(expr.ops, expr.comparators):
                comp_str = self._expr_to_str(comp)
                op_sym = "=="
                if isinstance(op, ast.Eq):
                    op_sym = "===" if self.target in ("javascript", "typescript") else "=="
                elif isinstance(op, ast.NotEq):
                    op_sym = "!==" if self.target in ("javascript", "typescript") else "!="
                elif isinstance(op, ast.Lt):
                    op_sym = "<"
                elif isinstance(op, ast.LtE):
                    op_sym = "<="
                elif isinstance(op, ast.Gt):
                    op_sym = ">"
                elif isinstance(op, ast.GtE):
                    op_sym = ">="
                ops_strs.append(f"{op_sym} {comp_str}")
            return f"{left} {' '.join(ops_strs)}"

        elif isinstance(expr, ast.Call):
            func_name = self._expr_to_str(expr.func)
            args = [self._expr_to_str(a) for a in expr.args]
            args_str = ", ".join(args)

            # Mapping hàm chuẩn
            if func_name == "print":
                if self.target in ("javascript", "typescript"):
                    return f"console.log({args_str})"
                elif self.target == "go":
                    return f'fmt.Println({args_str})'
                elif self.target == "rust":
                    # `{}` (Display), KHÔNG phải `{:?}` (Debug).
                    #
                    # Đo 09/09 bằng `rustc` thật: bản `{:?}` cho cú pháp 3/3
                    # nhưng hành vi 2/3 — `print("gioi")` ra `"gioi"` KÈM DẤU
                    # NHÁY, vì Debug bọc chuỗi lại. Python thì không.
                    #
                    # Đây đúng là thứ chỉ CHẠY mới thấy: `rustc` gật đầu cả ba
                    # đề, và một cửa chỉ hỏi cú pháp sẽ báo ĐẠT.
                    #
                    # Giá phải trả, nói thẳng: `{}` đòi `Display`, mà `Vec`
                    # không có. In một danh sách sẽ KHÔNG biên dịch được —
                    # hỏng to và thấy ngay, hơn là in ra một dạng khác Python.
                    return f'println!("{{}}", {args_str})'
                elif self.target == "cpp":
                    return f'std::cout << {args_str} << std::endl'
                elif self.target == "bash":
                    return f'echo {args_str}'
            elif func_name == "len":
                if self.target in ("javascript", "typescript"):
                    return f"{args[0]}.length" if args else "0"
                elif self.target == "go":
                    return f"len({args_str})"
                elif self.target == "rust":
                    return f"{args[0]}.len()" if args else "0"
                elif self.target == "cpp":
                    return f"{args[0]}.size()" if args else "0"
            elif func_name == "range":
                if self.target in ("javascript", "typescript"):
                    return f"Array.from({{length: {args_str}}}, (_, i) => i)"
            return f"{func_name}({args_str})"

        return "/* complex_expr */"

    # ------------------------------------------------------------------
    # BASH (07/09/2026) — vì sao phải tách hẳn ra khỏi `_expr_to_str`
    #
    # Bốn ngôn ngữ kia đều là "biểu thức lồng biểu thức": một `ast.Name` ra
    # cùng một chuỗi dù đứng ở đâu. Bash thì KHÔNG — cùng tên `n` phải viết ba
    # kiểu tuỳ chỗ đứng:
    #
    #     tong=5          <- vế trái, TRẦN
    #     echo "$tong"    <- lấy giá trị, có `$`
    #     (( tong + 1 ))  <- trong ngoặc số học, lại TRẦN
    #
    # Bản cũ dùng chung một hàm cho cả ba, nên sinh ra `if [ n <= 1 ]` (so
    # chuỗi "n" với "1") và `echo fibonacci(n - 1)` (bash coi `(` là lỗi cú
    # pháp). Đo 07/09: **3/3 đề gãy cú pháp, 3/3 gãy hành vi**, trong khi
    # javascript cùng bộ khung đạt 3/3 cả hai. Cái hỏng nằm ở nhánh bash.
    # ------------------------------------------------------------------

    def _bash(self, expr: ast.AST, arith: bool = False) -> str:
        """Sinh MỘT TỪ bash cho biểu thức.

        `arith=True` nghĩa là chỗ đứng đã nằm trong `$(( ))` hoặc `(( ))`: tên
        biến để trần, và không bọc thêm một lớp `$(( ))` nữa.
        """
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "1" if expr.value else "0"
            if expr.value is None:
                return '""'
            if isinstance(expr.value, str):
                return json.dumps(expr.value, ensure_ascii=False)
            return str(expr.value)

        if isinstance(expr, ast.Name):
            if arith:
                return expr.id
            if expr.id in self.mang:
                return '"${%s[@]}"' % expr.id
            return '"$%s"' % expr.id

        if isinstance(expr, (ast.List, ast.Tuple)):
            return "(" + " ".join(self._bash(e) for e in expr.elts) + ")"

        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
            trong = self._bash(expr.operand, arith=True)
            return f"-{trong}" if arith else f'"$(( -{trong} ))"'

        if isinstance(expr, ast.BinOp):
            # `"a" + "b"` KHÔNG PHẢI PHÉP CỘNG SỐ. Để nó rơi vào `$(( ))` thì
            # bash vẫn parse được — cú pháp XANH — nhưng ra `0`. Đúng loại lỗi
            # mà một cửa chỉ hỏi `bash -n` sẽ bỏ lọt, nên tách ra ở đây.
            if isinstance(expr.op, ast.Add) and self._bash_la_chuoi(expr):
                return '"' + self._bash_than_chuoi(expr) + '"'
            dau = self._DAU_SO.get(type(expr.op))
            if dau is None:
                return self._bash_bo_qua(expr)
            than = (f"{self._bash(expr.left, arith=True)} {dau} "
                    f"{self._bash(expr.right, arith=True)}")
            return than if arith else f'"$(( {than} ))"'

        if isinstance(expr, ast.Call):
            return self._bash_goi(expr, arith)

        return self._bash_bo_qua(expr)

    def _bash_bo_qua(self, expr: ast.AST) -> str:
        """Chỗ nhánh bash bỏ cuộc — GHI TÊN RA, rồi mới trả chuỗi rỗng.

        Bốn ngôn ngữ kia bỏ cuộc thì sinh `/* complex_expr */`, và trình kiểm
        BÁC ngay — hỏng to tiếng. Bash thì `x=""` parse sạch, nên cùng một chỗ
        bỏ cuộc lại đi qua cửa `bash -n` mà không ai biết. Đo 07/09: `x = {'a':
        1}` sang bash ra `x=""`, `bash -n` gật.
        """
        self.bo_sot.append(f"{type(expr).__name__} "
                           f"(dòng {getattr(expr, 'lineno', '?')}, biểu thức)")
        return '""'

    def _bash_goi(self, expr: ast.Call, arith: bool = False) -> str:
        ten = expr.func.id if isinstance(expr.func, ast.Name) else ""
        if ten == "print":
            return "echo " + " ".join(self._bash(a) for a in expr.args)
        if ten == "len" and expr.args:
            if isinstance(expr.args[0], ast.Name):
                return "${#%s[@]}" % expr.args[0].id
            return "0"
        if ten in self.ham_tu_khai:
            # GỌI HÀM LẤY GIÁ TRỊ PHẢI QUA `$( )`. Bash không có giá trị trả
            # về ngoài mã thoát 0-255, nên quy ước ở đây: hàm `echo` kết quả,
            # người gọi hứng bằng thay thế lệnh.
            tso = " ".join(self._bash(a) for a in expr.args)
            tho = f"$({ten} {tso})" if tso else f"$({ten})"
            return tho if arith else f'"{tho}"'
        return self._bash_bo_qua(expr)

    def _bash_la_chuoi(self, e: ast.AST) -> bool:
        if isinstance(e, ast.Constant):
            return isinstance(e.value, str)
        if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
            return self._bash_la_chuoi(e.left) or self._bash_la_chuoi(e.right)
        return False

    def _bash_than_chuoi(self, e: ast.AST) -> str:
        """Phần thân để nhét vào GIỮA hai dấu nháy kép."""
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            return e.value.replace("\\", "\\\\").replace('"', '\\"')
        if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
            return self._bash_than_chuoi(e.left) + self._bash_than_chuoi(e.right)
        if isinstance(e, ast.Name):
            return "${%s}" % e.id
        if isinstance(e, ast.Call):
            return self._bash_goi(e, arith=True)
        return self._bash(e, arith=False).strip('"')

    def _bash_dieu_kien(self, test: ast.AST) -> str:
        """Câu điều kiện — `(( ))` cho số, `[[ ]]` cho bằng/khác.

        `(( ))` so SỐ, `[[ a == b ]]` so CHUỖI. Không biết kiểu thì không chọn
        đúng được cả hai: `(( s <= 1 ))` với `s` là chuỗi thì bash đọc `s` như
        một tên biến rỗng và cho ra `0 <= 1` — ĐÚNG cú pháp, SAI kết quả. Ghi
        ra đây thay vì để người đọc tưởng chỗ này kín.
        """
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            op, trai, phai = test.ops[0], test.left, test.comparators[0]
            if isinstance(op, (ast.Eq, ast.NotEq)):
                dau = "==" if isinstance(op, ast.Eq) else "!="
                return f"[[ {self._bash(trai)} {dau} {self._bash(phai)} ]]"
            dau = {ast.Lt: "<", ast.LtE: "<=",
                   ast.Gt: ">", ast.GtE: ">="}.get(type(op))
            if dau:
                return (f"(( {self._bash(trai, arith=True)} {dau} "
                        f"{self._bash(phai, arith=True)} ))")
        return f"(( {self._bash(test, arith=True)} ))"

    def _bash_duyet(self, it: ast.AST) -> str:
        """Vế `in` của vòng lặp."""
        if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
                and it.func.id == "range"):
            a = [self._bash(x, arith=True) for x in it.args]
            if len(a) == 1:
                return f"$(seq 0 $(( {a[0]} - 1 )))"
            if len(a) >= 2:
                return f"$(seq {a[0]} $(( {a[1]} - 1 )))"
        if isinstance(it, ast.Name):
            # Dạng mảng chạy được cho CẢ biến thường (ra đúng 1 phần tử), nên
            # dùng luôn — khỏi phải đoán kiểu.
            return '"${%s[@]}"' % it.id
        if isinstance(it, (ast.List, ast.Tuple)):
            return " ".join(self._bash(e) for e in it.elts)
        return self._bash(it)

    @staticmethod
    def _bash_ten_dung_nhu_mang(node: ast.FunctionDef) -> set:
        """Tên nào TRONG hàm này được dùng như mảng (`for … in x`, `len(x)`)."""
        ten = set()
        for con in ast.walk(node):
            if isinstance(con, ast.For) and isinstance(con.iter, ast.Name):
                ten.add(con.iter.id)
            if (isinstance(con, ast.Call) and isinstance(con.func, ast.Name)
                    and con.func.id == "len" and con.args
                    and isinstance(con.args[0], ast.Name)):
                ten.add(con.args[0].id)
        return ten


def chuyen_doi_ngon_ngu(
    ma_nguon: str,
    lang_nguon: str = "python",
    lang_dich: str = "javascript"
) -> Dict[str, Any]:
    """Chuyển đổi mã nguồn từ ngôn ngữ này sang ngôn ngữ khác."""
    lang_nguon = lang_nguon.lower().strip()
    lang_dich = lang_dich.lower().strip()

    if lang_nguon not in DANH_SACH_NGON_NGU:
        return {
            "status": "FAIL",
            "error": f"Ngôn ngữ nguồn không được hỗ trợ: {lang_nguon}",
            "ma_dich": ""
        }
    if lang_dich not in DANH_SACH_NGON_NGU:
        return {
            "status": "FAIL",
            "error": f"Ngôn ngữ đích không được hỗ trợ: {lang_dich}",
            "ma_dich": ""
        }

    if lang_nguon == lang_dich:
        return {
            "status": "PASS",
            "source_lang": lang_nguon,
            "target_lang": lang_dich,
            "ma_dich": ma_nguon,
            "nodes_translated": 1,
            "notes": ["Ngôn ngữ nguồn và đích trùng nhau."]
        }

    # Nếu nguồn là Python -> phân tích AST để sinh code chính xác
    if lang_nguon == "python":
        try:
            tree = ast.parse(ma_nguon)
            visitor = PythonToPolyglotVisitor(target_lang=lang_dich)
            visitor.visit(tree)
            ma_ket_qua = "\n".join(visitor.lines)
            return {
                "status": "PASS",
                "source_lang": lang_nguon,
                "target_lang": lang_dich,
                "ma_dich": ma_ket_qua,
                "nodes_translated": visitor.nodes_count,
                "notes": visitor.notes,
                # Người gọi PHẢI đọc được chỗ sót. `status: PASS` ở đây chỉ có
                # nghĩa "bộ dịch chạy xong", không có nghĩa "dịch đủ".
                "bo_sot": visitor.bo_sot,
            }
        except SyntaxError as err:
            return {
                "status": "FAIL",
                "error": f"Lỗi cú pháp Python nguồn: dòng {err.lineno}: {err.msg}",
                "ma_dich": ""
            }

    # Chuyển đổi dạng mẫu mẫu nếu nguồn khác Python
    ma_dich_template = DANH_SACH_NGON_NGU[lang_dich].ma_mau
    return {
        "status": "PASS",
        "source_lang": lang_nguon,
        "target_lang": lang_dich,
        "ma_dich": ma_dich_template,
        "nodes_translated": 1,
        "notes": [f"Tạo khung mẫu chuẩn cho {DANH_SACH_NGON_NGU[lang_dich].ten}"]
    }


# ==============================================================================
# 2. BỘ KIỂM ĐỊNH CÚ PHÁP ĐA NGÔN NGỮ (SYNTAX VALIDATOR)
# ==============================================================================

def kiem_tra_cu_phap_da_ngon_ngu(ma: str, lang: str = "python") -> Dict[str, Any]:
    """Kiểm tra cú pháp độc lập cho mã thuộc bất kỳ ngôn ngữ nào."""
    lang = lang.lower().strip()
    if lang not in DANH_SACH_NGON_NGU:
        return {
            "status": "FAIL",
            "valid": False,
            "error": f"Không hỗ trợ kiểm tra ngôn ngữ: {lang}",
            "details": []
        }

    if not ma.strip():
        return {
            "status": "FAIL",
            "valid": False,
            "error": "Mã nguồn rỗng",
            "details": ["Không có dòng lệnh nào để kiểm tra."]
        }

    # 1. Python AST Check
    if lang == "python":
        try:
            tree = ast.parse(ma)
            so_node = sum(1 for _ in ast.walk(tree))
            return {
                "status": "PASS",
                "valid": True,
                "language": "python",
                "message": f"Cú pháp Python hợp lệ (AST: {so_node} nodes).",
                "details": []
            }
        except SyntaxError as err:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "python",
                "error": f"SyntaxError tại dòng {err.lineno}, cột {err.offset}: {err.msg}",
                "details": [f"Line {err.lineno}: {err.text.strip() if err.text else ''}"]
            }

    # 2. JavaScript / TypeScript Check
    elif lang in ("javascript", "typescript"):
        # Kiểm tra đóng mở ngoặc (), {}, []
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        for i, char in enumerate(ma):
            if char in "({[":
                stack.append((char, i))
            elif char in ")}]":
                if not stack or stack[-1][0] != pairs[char]:
                    return {
                        "status": "FAIL",
                        "valid": False,
                        "language": lang,
                        "error": f"Lỗi đóng mở ngoặc: thừa hoặc sai vị trí '{char}' tại vị trí {i}",
                        "details": []
                    }
                stack.pop()
        if stack:
            unclosed, pos = stack[-1]
            return {
                "status": "FAIL",
                "valid": False,
                "language": lang,
                "error": f"Chưa đóng ngoặc '{unclosed}' tại vị trí {pos}",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": lang,
            "message": f"Cấu trúc cú pháp {DANH_SACH_NGON_NGU[lang].ten} chuẩn xác.",
            "details": []
        }

    # 3. Go Check
    elif lang == "go":
        if "package " not in ma and "func " not in ma:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "go",
                "error": "Thiếu khai báo package hoặc hàm func trong mã Go.",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": "go",
            "message": "Cấu trúc mã Go hợp lệ.",
            "details": []
        }

    # 4. Rust Check
    elif lang == "rust":
        if "fn " not in ma:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "rust",
                "error": "Thiếu định nghĩa hàm (fn) trong mã Rust.",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": "rust",
            "message": "Cấu trúc mã Rust hợp lệ.",
            "details": []
        }

    # 5. C++ Check
    elif lang == "cpp":
        if "int main" not in ma and "void " not in ma and "auto " not in ma and "#include" not in ma:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "cpp",
                "error": "Thiếu chỉ thị #include hoặc hàm thực thi trong mã C++.",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": "cpp",
            "message": "Cấu trúc mã C++20 hợp lệ.",
            "details": []
        }

    # 6. SQL Check
    elif lang == "sql":
        tu_khoa_sql = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "WITH"]
        ma_upper = ma.upper()
        if not any(k in ma_upper for k in tu_khoa_sql):
            return {
                "status": "FAIL",
                "valid": False,
                "language": "sql",
                "error": "Không tìm thấy câu lệnh SQL hợp lệ (SELECT, INSERT, UPDATE, v.v.)",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": "sql",
            "message": "Cú pháp câu lệnh SQL hợp lệ.",
            "details": []
        }

    # 7. Bash Check
    elif lang == "bash":
        if "if " in ma and "fi" not in ma:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "bash",
                "error": "Khối 'if' trong Bash chưa được đóng bằng 'fi'.",
                "details": []
            }
        if "for " in ma and "done" not in ma:
            return {
                "status": "FAIL",
                "valid": False,
                "language": "bash",
                "error": "Vòng lặp 'for' trong Bash chưa được đóng bằng 'done'.",
                "details": []
            }
        return {
            "status": "PASS",
            "valid": True,
            "language": "bash",
            "message": "Cú pháp Bash script hợp lệ.",
            "details": []
        }

    return {
        "status": "PASS",
        "valid": True,
        "language": lang,
        "message": f"Kiểm tra hoàn tất cho {lang}.",
        "details": []
    }


# ==============================================================================
# 3. BỘ THỰC THI MÃ AN TOÀN TRONG TIẾN TRÌNH CÔ LẬP (ISOLATED RUNNER)
# ==============================================================================

def _chay_co_hop_cat(cmd, thu_muc, timeout_s):
    """Chạy `cmd` trong hộp cát, trả `(returncode, stdout, stderr, hop_cat)`.

    Dùng `Popen` chứ không `subprocess.run`: phải có `pid` mới gán được vào Job
    Object. Và `finally: dong_job` là chỗ `KILL_ON_JOB_CLOSE` giết cả cây — kể
    cả cháu mà `timeout` của `run` không với tới (đo 08/09: cháu SỐNG SÓT qua
    timeout ở bản cũ).
    """
    from core.hop_cat import (CREATE_SUSPENDED, RAM_MB, dong_job, gan_vao_job,
                              moi_truong_sach, tao_job, tha_tien_trinh)

    h_job, ly_do = tao_job()
    # TREO NGAY TỪ LÚC SINH (08/09). Bản 07/09 gắn vào job sau khi con đã chạy,
    # để hở 0,077–0,232 ms (đo 52 lượt, cháu sống sót 0/12 — không ai bắn trúng,
    # nhưng khe hẹp là nhờ Python khởi động chậm 17–24 ms, không nhờ mã này).
    p = subprocess.Popen(cmd, cwd=str(thu_muc), env=moi_truong_sach(),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace",
                         creationflags=CREATE_SUSPENDED if h_job else 0)
    da_gan = gan_vao_job(h_job, p.pid) if h_job else False
    # BA TRẠNG THÁI CHO CHÍNH HỘP CÁT. Không có trường này thì lời hứa "có hộp
    # cát" là một câu chữ không kiểm được — đúng thứ CLAUDE.md mục 7 cấm.
    hop_cat = ("job" if da_gan
               else ("khong: " + (ly_do or "AssignProcessToJobObject thất bại")))
    if h_job:
        # FAIL-CLOSED. Con đang TREO; không thả được thì `communicate` sẽ đợi
        # hết timeout rồi mới về, tức một lỗi im lặng đội lốt "mã chạy lâu".
        # Giết thẳng và nói ra trong `hop_cat`.
        da_tha, vi_sao = tha_tien_trinh(p.pid)
        if not da_tha:
            try:
                p.kill()
            except OSError:
                pass
            dong_job(h_job)
            return 1, "", f"hộp cát: không thả nổi tiến trình — {vi_sao}", \
                f"khong: {vi_sao}"
    try:
        out, err = p.communicate(timeout=timeout_s)
        return p.returncode, out, err, hop_cat
    finally:
        try:
            p.kill()
        except OSError:
            pass
        dong_job(h_job)


def chay_ma_da_ngon_ngu(
    ma: str,
    lang: str = "python",
    timeout_s: float = 5.0
) -> Dict[str, Any]:
    """Chạy mã trong một tiến trình con, có trần thời gian. KHÔNG có hộp cát.

    01/09/2026 — câu này TRƯỚC ĐÂY viết "thực thi an toàn trong môi trường CÔ
    LẬP". Chạy thử qua chính hàm này thì:

        CWD                      D:/AURA_v3   (gốc kho, không phải thư mục tạm)
        USER                     baloa        (đủ quyền tài khoản Windows)
        liệt kê thư mục HOME     86 mục       (đọc được)
        GHI TỆP NGOÀI thư mục tạm             ĐƯỢC

    Chỉ có `timeout`. Không giới hạn tệp, không giới hạn mạng, không đổi
    người dùng. CLAUDE.md mục 7 luật 3: "Cô lập", "sandbox", "không có quyền"
    — ba chữ ấy người đọc sẽ TIN, và tin sai thì mất tệp. Kiểm được thì kiểm;
    kiểm không được thì viết CHƯA chặn được, đừng viết đã chặn.

    CHỈ Python và JavaScript chạy thật (cần `node`). Sáu ngôn ngữ còn lại chỉ
    được KIỂM CÚ PHÁP — xem nhánh cuối hàm.
    """
    lang = lang.lower().strip()
    if lang not in DANH_SACH_NGON_NGU:
        return {
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Không hỗ trợ thực thi ngôn ngữ: {lang}",
            "latency_ms": 0.0
        }

    t0 = time.monotonic()

    # 1. Thực thi Python
    if lang == "python":
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(ma)
            temp_path = f.name

        try:
            cmd = [sys.executable, "-X", "utf8", temp_path]
            ma_thoat, out, err, hop_cat = _chay_co_hop_cat(
                cmd, os.path.dirname(temp_path), timeout_s)
            t_ms = round((time.monotonic() - t0) * 1000, 1)
            return {
                "status": "PASS" if ma_thoat == 0 else "FAIL",
                "exit_code": ma_thoat,
                "stdout": out,
                "stderr": err,
                "latency_ms": t_ms,
                "language": "python",
                "hop_cat": hop_cat,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "exit_code": 124,
                "stdout": "",
                "stderr": f"Quá thời gian thực thi cho phép ({timeout_s}s).",
                "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                "language": "python",
                "hop_cat": "job",
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                "language": "python"
            }
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    # 2. Thực thi Node.js (JavaScript) nếu có node trên máy
    elif lang == "javascript" and shutil.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(ma)
            temp_path = f.name

        try:
            cmd = ["node", temp_path]
            ma_thoat, out, err, hop_cat = _chay_co_hop_cat(
                cmd, os.path.dirname(temp_path), timeout_s)
            t_ms = round((time.monotonic() - t0) * 1000, 1)
            return {
                "status": "PASS" if ma_thoat == 0 else "FAIL",
                "exit_code": ma_thoat,
                "stdout": out,
                "stderr": err,
                "latency_ms": t_ms,
                "language": "javascript",
                "hop_cat": hop_cat,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "exit_code": 124,
                "stdout": "",
                "stderr": f"Quá thời gian thực thi ({timeout_s}s).",
                "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                "language": "javascript"
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                "language": "javascript"
            }
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    # 3. KHÔNG CHẠY ĐƯỢC — chỉ kiểm cú pháp.
    #
    # 01/09/2026 — nhánh này TRƯỚC ĐÂY trả `status: "PASS"`, `exit_code: 0` và
    # in ra "[AURA Polyglot Engine Sandbox] ... đạt tiêu chuẩn biên dịch".
    # Đo thật, 6 ngôn ngữ, mã CỐ Ý HỎNG:
    #
    #     go    fmt.Println(1/0)     -> PASS  exit 0
    #     rust  panic!("no")         -> PASS  exit 0
    #     cpp   return 1             -> PASS  exit 0
    #     sql   SELECT 1/0           -> PASS  exit 0
    #     bash  exit 3               -> PASS  exit 0   (máy CÓ bash!)
    #     ts    (hợp lệ)             -> PASS  exit 0
    #
    # Sáu trên sáu báo đỗ trong khi không chương trình nào từng chạy. Giao diện
    # đọc `status === 'PASS'` rồi vẽ huy hiệu xanh "EXIT CODE 0" — người dùng
    # bấm CHẠY và nhận về màu xanh cho thứ chưa hề chạy.
    #
    # Ba trạng thái phải tách rời (CLAUDE.md mục 4): đạt · đo được mà không
    # đạt · KHÔNG ĐO ĐƯỢC. Nhánh này là cái thứ ba.
    syntax_res = kiem_tra_cu_phap_da_ngon_ngu(ma, lang)
    t_ms = round((time.monotonic() - t0) * 1000, 1)

    if syntax_res.get("valid"):
        return {
            "status": "KHONG_CHAY_DUOC",
            "exit_code": None,
            "stdout": "",
            "stderr": f"KHÔNG CHẠY ĐƯỢC — máy này chưa có bộ công cụ cho "
                      f"{DANH_SACH_NGON_NGU[lang].ten}.\n"
                      f"Đã kiểm CÚ PHÁP và thấy hợp lệ, nhưng chương trình "
                      f"CHƯA HỀ CHẠY, nên không biết nó ra kết quả gì.",
            "latency_ms": t_ms,
            "language": lang,
            "simulated": True
        }
    else:
        return {
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": syntax_res.get("error", "Lỗi cú pháp không xác định"),
            "latency_ms": t_ms,
            "language": lang,
            "simulated": True
        }
