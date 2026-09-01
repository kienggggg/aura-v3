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
    """Kiểm tra chuyển đổi từ Python sang Go."""
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "go")
    assert res["status"] == "PASS"
    ma_go = res["ma_dich"]
    assert "package main" in ma_go
    assert "func TinhTong(" in ma_go
    assert "for _, x := range nums" in ma_go


def test_chuyen_doi_ngon_ngu_python_sang_rust():
    """Kiểm tra chuyển đổi từ Python sang Rust."""
    ma_py = """def tinh_tong(nums):
    tong = 0
    for x in nums:
        tong += x
    return tong
"""
    res = chuyen_doi_ngon_ngu(ma_py, "python", "rust")
    assert res["status"] == "PASS"
    ma_rs = res["ma_dich"]
    assert "fn tinh_tong(nums)" in ma_rs
    assert "for x in nums" in ma_rs


def test_chuyen_doi_ngon_ngu_python_sang_cpp():
    """Kiểm tra chuyển đổi từ Python sang C++."""
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
    assert "auto tinh_tong(" in ma_cpp
    assert "for (const auto& x : nums)" in ma_cpp


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
