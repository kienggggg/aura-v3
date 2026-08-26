# -*- coding: utf-8 -*-
"""test_kiem_ban_dong_bang.py — Kiểm thử cửa cứng kiểm tra bản đóng băng và phân loại lỗi nạp."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
import pytest

from experiments.evidence_sprint.kiem_ban_dong_bang import kiem_tra_ban_dong_bang
from core.trace_runtime import _chay_pytest_tim_test_do_phan_loai

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_kiem_ban_dong_bang_kho_that():
    """Kiểm tra trên chính kho thật phải vượt qua 100% các tiêu chí."""
    ok, err = kiem_tra_ban_dong_bang(PROJECT_ROOT, PROJECT_ROOT, ["tests/test_dong_ho.py"])
    assert ok is True
    assert err == ""


def test_kiem_ban_dong_bang_thieu_goc(tmp_path: Path):
    """Kiểm tra khi bản chép chỉ có vài thư mục (dưới 90% mục ở gốc) phải bị chặn với mã Fail-closed."""
    for d in ("core", "tests", "experiments", "tools"):
        shutil.copytree(PROJECT_ROOT / d, tmp_path / d)

    ok, err = kiem_tra_ban_dong_bang(tmp_path, PROJECT_ROOT, ["tests/test_dong_ho.py"])
    assert ok is False
    assert "KHÔNG ĐO ĐƯỢC" in err
    assert "không đạt ngưỡng 90%" in err


def test_kiem_ban_dong_bang_thieu_interface(tmp_path: Path):
    """Kiểm tra khi bản chép thiếu thư mục interface/ thì phải bị chặn ngay."""
    tam = tmp_path / "kho"
    shutil.copytree(
        PROJECT_ROOT,
        tam,
        ignore=shutil.ignore_patterns(
            "venv", ".venv*", ".git", "__pycache__", ".pytest_cache",
            "data", "_rac", "*.pyc", "node_modules"
        ),
    )
    shutil.rmtree(tam / "interface")

    ok, err = kiem_tra_ban_dong_bang(tam, PROJECT_ROOT, ["tests/test_dong_ho.py"])
    assert ok is False
    assert "KHÔNG ĐO ĐƯỢC" in err
    assert "interface" in err


def test_phan_loai_test_do_that_vs_loi_nap(tmp_path: Path):
    """Kiểm tra _chay_pytest_tim_test_do_phan_loai phân biệt chính xác test đỏ thật vs lỗi nạp module."""
    # 1. Test trên file test hợp lệ (không lỗi nạp)
    failing, import_errors = _chay_pytest_tim_test_do_phan_loai("tests/test_dong_ho.py", cwd=PROJECT_ROOT)
    assert isinstance(failing, list)
    assert len(import_errors) == 0

    # 2. Tạo một file test bị lỗi cú pháp / lỗi import ở module level
    test_hong = tmp_path / "test_hong_nap.py"
    test_hong.write_text("import khong_ton_tai_module_xyz_12345\ndef test_a(): pass\n", encoding="utf-8")
    
    failing_hong, import_errors_hong = _chay_pytest_tim_test_do_phan_loai(str(test_hong), cwd=PROJECT_ROOT)
    assert len(failing_hong) == 0
    assert len(import_errors_hong) > 0
    assert any("khong_ton_tai_module_xyz_12345" in e or "ERROR" in e or "Lỗi thu thập" in e for e in import_errors_hong)
