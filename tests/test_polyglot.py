# -*- coding: utf-8 -*-
"""test_polyglot.py — Kiểm thử đơn vị cho module Polyglot Engine (core/polyglot.py)."""
from __future__ import annotations

import pytest

from core.polyglot import (
    DANH_SACH_NGON_NGU,
    chay_ma_da_ngon_ngu,
    chuyen_doi_ngon_ngu,
    kiem_tra_cu_phap_da_ngon_ngu,
    lay_danh_sach_ngon_ngu,
)


def test_danh_sach_ngon_ngu_du_8_ngon_ngu():
    """Kiểm tra đủ 8 ngôn ngữ lập trình được khai báo và có metadata chuẩn."""
    ds = lay_danh_sach_ngon_ngu()
    assert len(ds) == 8
    cac_id = {item["id"] for item in ds}
    ky_vong = {"python", "javascript", "typescript", "go", "rust", "cpp", "sql", "bash"}
    assert cac_id == ky_vong

    for lang in ds:
        assert lang["ten"]
        assert lang["bieu_tuong"]
        assert lang["duoi_tep"].startswith(".")
        assert lang["mau_sac"].startswith("#")
        assert len(lang["ma_mau"]) > 10


def test_chuyen_doi_ngon_ngu_python_sang_javascript():
    """Kiểm tra chuyển đổi hàm và vòng lặp từ Python sang JavaScript."""
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "javascript")
    assert res["status"] == "PASS"
    ma_js = res["ma_dich"]
    assert "function tinh_tong(nums)" in ma_js
    assert "let tong = 0;" in ma_js
    assert "for (const x of nums)" in ma_js
    assert "tong += x;" in ma_js
    assert "return tong;" in ma_js


def test_chuyen_doi_ngon_ngu_python_sang_go():
    """Chuyển đổi Python sang Go.

    BÀI NÀY TỪNG KHOÁ CHÍNH CÁI LỖI (sửa 08/09/2026). Nó khẳng định
    `"func TinhTong(" in ma_go` — PascalCase — và xanh suốt, trong khi bản dịch
    Go **chưa từng biên dịch được lần nào**: khai `func TinhTong` rồi gọi
    `tinh_tong(...)` là định danh không tồn tại.

    Một bài chỉ dò CHUỖI trong đầu ra, chưa bao giờ đưa đầu ra ấy cho trình
    biên dịch, thì nó giữ nguyên cái hỏng thay vì bắt. Đo bằng `go build` thật
    ngày 08/09: **cú pháp 0/3, hành vi 0/3**.

    Nay bài này đòi tên khai TRÙNG tên gọi, và phần chạy thật nằm ở
    `tests/test_bo_dich_go_chay_that.py` — nơi có `go build` + `go run`.
    """
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong

print(tinh_tong([1, 2, 3]))
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "go")
    assert res["status"] == "PASS"
    ma_go = res["ma_dich"]
    assert "package main" in ma_go
    assert "func tinh_tong(" in ma_go, (
        "tên khai báo phải TRÙNG tên gọi — PascalCase làm định danh biến mất")
    assert "tinh_tong(" in ma_go.split("func main")[1], "chỗ gọi mất hàm"
    assert "for _, x := range nums" in ma_go
    assert "func main() {" in ma_go, "câu lệnh cấp gói phải nằm trong main"


def test_chuyen_doi_ngon_ngu_python_sang_rust():
    """CHỤP LẠI DẠNG ĐẦU RA HIỆN NAY — **không** chứng minh Rust chạy được.

    Máy này không có `rustc`/`cargo` (đo 09/09), nên chưa trình biên dịch nào
    từng nhìn thấy đầu ra này. `status == "PASS"` dưới đây là **bộ dịch tự
    khai**, không phải phán quyết của ai.

    VÀ NÓ ĐANG KHOÁ MỘT CÁI HỎNG. `fn tinh_tong(nums)` thiếu kiểu tham số và
    kiểu trả về — Rust không nhận. Đặc tả §5e đã ghi đúng chỗ ấy từ 04/09.

    ĐỌC KỸ TRƯỚC KHI SỬA BỘ DỊCH: vá cho đúng Rust thì bài này ĐỎ, và đỏ là
    ĐÚNG. Đừng revert bản vá để bài xanh lại — đó chính là cái bẫy đã giữ bộ
    dịch Go hỏng: `test_chuyen_doi_ngon_ngu_python_sang_go` khẳng định
    `"func TinhTong(" in ma_go` và xanh suốt trong khi bản dịch chưa từng biên
    dịch được lần nào. Sửa bài này CÙNG LÚC với bản vá, và thêm một bài chạy
    thật như `tests/test_bo_dich_go_chay_that.py`.
    """
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "rust")
    assert res["status"] == "PASS"
    ma_rs = res["ma_dich"]
    # SỬA 09/09 CÙNG LÚC VỚI BẢN VÁ — bản cũ đòi `fn tinh_tong(nums)`, tức
    # KHOÁ CHÍNH CÁI HỎNG (thiếu kiểu tham số và kiểu trả về). Nay Rust có
    # trình biên dịch trên máy, và `tests/test_bo_dich_rust_cpp_chay_that.py`
    # chấm bằng `rustc` chứ không bằng dò chuỗi.
    assert "fn tinh_tong(nums: Vec<i32>) -> i32" in ma_rs, ma_rs
    assert "for x in nums" in ma_rs
    assert "return tong;" in ma_rs, "early-return trần lại quay về"
    assert "fn main() {" in ma_rs, "câu lệnh cấp module không có chỗ đứng"


def test_chuyen_doi_ngon_ngu_python_sang_cpp():
    """CHỤP LẠI DẠNG ĐẦU RA HIỆN NAY — **không** chứng minh C++ biên dịch được.

    Máy này không có `g++`/`gcc`/`clang++` (đo 09/09). `status == "PASS"` là
    bộ dịch tự khai. Cùng cảnh báo như bài Rust ngay trên: vá bộ dịch cho đúng
    thì bài này đỏ, và đỏ là ĐÚNG — sửa nó cùng lúc với bản vá, đừng revert.
    """
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "cpp")
    assert res["status"] == "PASS"
    ma_cpp = res["ma_dich"]
    assert "#include <iostream>" in ma_cpp
    # SỬA 09/09 CÙNG LÚC VỚI BẢN VÁ. `auto tinh_tong(auto n)` là mẫu hàm rút
    # gọn C++20, và ĐỆ QUY với kiểu trả về suy diễn thì g++ bác: *"use of
    # `fibonacci` before deduction of `auto`"*. Kiểu nói thẳng thì hết.
    assert "int tinh_tong(const std::vector<int>& nums)" in ma_cpp, ma_cpp
    assert "for (const auto& x : nums)" in ma_cpp
    assert "int main() {" in ma_cpp, "câu lệnh ở cấp tệp — g++ bác ngay dòng đầu"


def test_chuyen_doi_loi_cu_phap_python_nguon():
    """Kiểm tra xử lý fail-closed khi mã Python nguồn bị sai cú pháp."""
    ma_py = "def ham_loi(: return 123"
    res = chuyen_doi_ngon_ngu(ma_py, "python", "javascript")
    assert res["status"] == "FAIL"
    assert "Lỗi cú pháp Python" in res["error"]


def test_kiem_tra_cu_phap_python():
    """Kiểm định cú pháp Python hợp lệ và không hợp lệ."""
    hop_le = kiem_tra_cu_phap_da_ngon_ngu("def hello(): return 'world'", "python")
    assert hop_le["valid"] is True
    assert hop_le["status"] == "PASS"

    sai = kiem_tra_cu_phap_da_ngon_ngu("def hello( return 'world'", "python")
    assert sai["valid"] is False
    assert sai["status"] == "FAIL"


def test_kiem_tra_cu_phap_javascript_ngoac():
    """Kiểm định lỗi thiếu ngoặc trong JavaScript."""
    hop_le = kiem_tra_cu_phap_da_ngon_ngu("function foo() { return [1, 2, 3]; }", "javascript")
    assert hop_le["valid"] is True

    sai = kiem_tra_cu_phap_da_ngon_ngu("function foo() { return [1, 2, 3; }", "javascript")
    assert sai["valid"] is False
    assert "Lỗi đóng mở ngoặc" in sai["error"]


def test_kiem_tra_cu_phap_sql():
    """Kiểm định câu lệnh SQL hợp lệ và không hợp lệ."""
    hop_le = kiem_tra_cu_phap_da_ngon_ngu("SELECT id, ten FROM users WHERE active = 1;", "sql")
    assert hop_le["valid"] is True

    sai = kiem_tra_cu_phap_da_ngon_ngu("HELLO WORLD THIS IS NOT SQL", "sql")
    assert sai["valid"] is False


def test_kiem_tra_cu_phap_bash():
    """Kiểm định script Bash hợp lệ và không hợp lệ."""
    hop_le = kiem_tra_cu_phap_da_ngon_ngu("#!/bin/bash\nif [ $x -gt 0 ]; then echo 'yes'; fi", "bash")
    assert hop_le["valid"] is True

    sai = kiem_tra_cu_phap_da_ngon_ngu("#!/bin/bash\nif [ $x -gt 0 ]; then echo 'yes'", "bash")
    assert sai["valid"] is False


def test_chay_ma_python_an_toan():
    """Kiểm tra chạy mã Python thực tế trong tiến trình riêng."""
    ma = "print('AURA POLYGLOT PASS')"
    res = chay_ma_da_ngon_ngu(ma, "python", timeout_s=3.0)
    assert res["status"] == "PASS"
    assert res["exit_code"] == 0
    assert "AURA POLYGLOT PASS" in res["stdout"]


def test_chay_ma_python_timeout():
    """Kiểm tra bảo vệ timeout khi mã Python lặp vô tận."""
    ma = "import time\nwhile True: time.sleep(0.1)"
    res = chay_ma_da_ngon_ngu(ma, "python", timeout_s=0.5)
    assert res["status"] == "FAIL"
    assert res["exit_code"] == 124
    assert "Quá thời gian" in res["stderr"]
