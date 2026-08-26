# -*- coding: utf-8 -*-
"""kiem_ban_dong_bang.py — Cửa cứng kiểm tra tính toàn vẹn của bản đóng băng trước khi đo.

Tiêu chuẩn:
1. Số mục ở gốc bản chép >= 90% số mục ở gốc kho thật (đã trừ các mục rác/cache).
2. Các thư mục gói cốt lõi (core, interface, tests, experiments) phải tồn tại.
3. Import thử "import core, interface" thành công với mã thoát 0.
4. Đếm số test thu thập được (pytest --collect-only -q) trên các tệp test chỉ định
   khớp 100% giữa kho thật và bản đóng băng.

Nếu trượt bất kỳ điều kiện nào, hàm trả về (False, lý_do) và caller thoát mã 2 (KHÔNG ĐO ĐƯỢC).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

BO_QUA_GOC: Set[str] = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "venv",
    ".venv",
    ".venv314",
    "data",
    "_rac",
    "node_modules",
    "build",
    "dist",
    ".agents",
    ".claude",
    "scratch",
}

THU_MUC_BAT_BUOC: List[str] = ["core", "interface", "tests", "experiments"]


def _lay_muc_goc_hop_le(p: Path) -> Set[str]:
    """Lấy danh sách tên mục ở gốc không nằm trong danh sách bỏ qua."""
    if not p.is_dir():
        return set()
    return {
        item.name
        for item in p.iterdir()
        if item.name not in BO_QUA_GOC
        and not item.name.endswith(".pyc")
        and not item.name.endswith(".egg-info")
    }


def _dem_test_collect(tep_test: str, cwd: Path, py_exe: str) -> Tuple[int, int, str]:
    """Chạy pytest --collect-only -q và trả về (exit_code, so_test, stdout_stderr)."""
    cmd = [py_exe, "-X", "utf8", "-m", "pytest", tep_test, "--collect-only", "-q"]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd),
            timeout=30,
        )
        tests = [
            line.strip()
            for line in res.stdout.splitlines()
            if line.strip() and "::" in line.strip() and not line.strip().startswith("=")
        ]
        return res.returncode, len(tests), (res.stdout + "\n" + res.stderr).strip()
    except Exception as e:
        return 2, 0, str(e)


def kiem_tra_ban_dong_bang(
    tam: Path,
    goc: Path,
    danh_sach_tep_test: Optional[List[str]] = None,
    py_exe: Optional[str] = None,
    verbose: bool = True,
) -> Tuple[bool, str]:
    """Kiểm tra cửa cứng bản đóng băng.
    
    Trả về (True, "") nếu đạt.
    Trả về (False, lý_do_lỗi) nếu trượt bất kỳ tiêu chí nào.
    """
    py = py_exe or sys.executable or "python"

    # 1. Cửa kiểm tra số mục ở gốc >= 90%
    muc_goc_that = _lay_muc_goc_hop_le(goc)
    muc_goc_tam = _lay_muc_goc_hop_le(tam)

    if not muc_goc_that:
        msg = f"KHÔNG ĐO ĐƯỢC: Thư mục gốc {goc} không có mục hợp lệ nào để so sánh."
        if verbose:
            print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
        return False, msg

    ty_le = len(muc_goc_tam) / len(muc_goc_that)
    if ty_le < 0.90:
        thieu = muc_goc_that - muc_goc_tam
        thieu_str = ", ".join(sorted(list(thieu))[:10])
        msg = (
            f"KHÔNG ĐO ĐƯỢC: Số mục ở gốc bản chép không đạt ngưỡng 90% "
            f"({len(muc_goc_tam)}/{len(muc_goc_that)} = {ty_le:.1%}, thiếu: {thieu_str})"
        )
        if verbose:
            print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
        return False, msg

    # 2. Cửa kiểm tra mọi thư mục gói bắt buộc tồn tại
    for pkg in THU_MUC_BAT_BUOC:
        pkg_path = tam / pkg
        if not pkg_path.is_dir():
            msg = f"KHÔNG ĐO ĐƯỢC: Bản đóng băng thiếu thư mục gói bắt buộc '{pkg}' tại {pkg_path}"
            if verbose:
                print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
            return False, msg

    # 3. Cửa import thử thật trong bản chép
    try:
        res_import = subprocess.run(
            [py, "-X", "utf8", "-c", "import core, interface; print('OK_IMPORT')"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(tam),
            timeout=15,
        )
        if res_import.returncode != 0 or "OK_IMPORT" not in res_import.stdout:
            err_snip = (res_import.stderr or res_import.stdout).strip()[:300]
            msg = (
                f"KHÔNG ĐO ĐƯỢC: Thử nghiệm import core, interface thất bại "
                f"(mã thoát {res_import.returncode}): {err_snip}"
            )
            if verbose:
                print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
            return False, msg
    except Exception as e:
        msg = f"KHÔNG ĐO ĐƯỢC: Ngoại lệ khi thử nghiệm import trong bản chép: {e}"
        if verbose:
            print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
        return False, msg

    # 4. Cửa đếm test thu thập được (--collect-only)
    #
    # 26/08, THÊM `tests/test_the_app.py` VÀO DANH SÁCH MẶC ĐỊNH — vá một lỗ
    # đo được của ba cửa phía trên.
    #
    # Chạy thử sáu bản đóng băng cố ý làm hỏng: năm bản bị chặn đúng, nhưng
    # bản "`interface/` còn mà RUỘT RỖNG" thì ĐI QUA HẾT:
    #
    #   cửa 2 (đủ thư mục gói)  thư mục có mặt -> đạt
    #   cửa 3 (import thật)     `import interface` trên thư mục rỗng THÀNH
    #                           CÔNG, vì Python 3 coi nó là namespace package
    #                           (`_NamespacePath([...])`), không cần
    #                           `__init__.py`
    #   cửa 4 (collect)         ba tệp test mặc định — the_v1 · chat_service ·
    #                           the_cst — KHÔNG tệp nào `import interface`
    #   cửa 1 (90% mục ở gốc)   chỉ đếm mục CẤP MỘT, không nhìn vào ruột
    #
    # Đây đúng là kiểu hỏng đã đốt một lượt đo ngày 26/08 (bản chép thiếu
    # `interface/`, mọi test `import interface.*` gãy khi nạp nên bị tính là
    # ĐỎ, trace 0 bước, và phép đo cho ra 0,33 — một con số hoàn toàn giả).
    # Ở đó thư mục thiếu HẲN nên cửa 2 bắt được; nếu bản chép bị cắt ruột
    # (chép dở, hay bộ lọc loại `.py`) thì không cửa nào thấy.
    #
    # `tests/test_the_app.py` mở đầu bằng `from interface import the_api,
    # the_app`, nên `--collect-only` trên nó gãy ngay khi `interface` rỗng
    # hoặc thiếu tệp. Một dòng, dùng đúng cơ chế đã có.
    danh_sach_test = danh_sach_tep_test or [
        "tests/test_the_v1.py",
        "tests/test_chat_service.py",
        "tests/test_the_cst.py",
        "tests/test_the_app.py",
    ]
    for t_file in danh_sach_test:
        goc_t = goc / t_file
        tam_t = tam / t_file
        if not goc_t.is_file():
            continue
        if not tam_t.is_file():
            msg = f"KHÔNG ĐO ĐƯỢC: Bản đóng băng thiếu tệp test '{t_file}'"
            if verbose:
                print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
            return False, msg

        rc_goc, dem_goc, out_goc = _dem_test_collect(t_file, goc, py)
        rc_tam, dem_tam, out_tam = _dem_test_collect(t_file, tam, py)

        if rc_tam != 0 or dem_tam != dem_goc or dem_tam == 0:
            msg = (
                f"KHÔNG ĐO ĐƯỢC: Thu thập test trên '{t_file}' bị sai lệch hoặc lỗi nạp. "
                f"Kho thật: rc={rc_goc}, {dem_goc} tests. Bản chép: rc={rc_tam}, {dem_tam} tests."
            )
            if verbose:
                print(f"  [CỬA ĐÓNG BĂNG TRƯỢT] {msg}")
            return False, msg

    if verbose:
        print(f"  [CỬA ĐÓNG BĂNG XANH] Gốc: {len(muc_goc_tam)}/{len(muc_goc_that)} mục, đủ gói bắt buộc, import & collect 100% khớp.")
    return True, ""


if __name__ == "__main__":
    # Chạy thử trực tiếp
    goc_dir = Path(__file__).resolve().parent.parent.parent
    ok, err = kiem_tra_ban_dong_bang(goc_dir, goc_dir)
    sys.exit(0 if ok else 2)
