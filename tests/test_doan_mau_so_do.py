# -*- coding: utf-8 -*-
"""Nhánh ĐOẠN MẪU với Số Đỏ — `CHOT:doan-mau-so-do` (14/09/2026).

Kho mẫu Sếp duyệt 13/09 (`docs/KE_HOACH_KHO_THAM_CHIEU_2026-09-13.md`). Bài này
giữ ngưỡng như lúc đăng ký, và giữ lời hứa của kế hoạch: tác phẩm không bao giờ
nằm trong tệp git theo dõi — repo PUBLIC.
"""
from __future__ import annotations

import re
import subprocess

from core.paths import PROJECT_ROOT

# Chép TAY từ `CHOT:doan-mau-so-do` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "lọt cửa phòng viết, 15 lượt": "có mẫu ≥ không mẫu − 2",
    "chuỗi từ liền nhau chung với đoạn mẫu, dài nhất":
        "≤ mức tình cờ của nhánh đối chứng, và tuyệt đối ≤ 8 từ",
    "em chấm mù, 3 cặp": "có mẫu thắng ≥ 2/3",
    "Sếp chấm lại mù, 3 cặp": "có mẫu thắng ≥ 2/3",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:doan-mau-so-do -->(.*?)<!-- /CHOT:doan-mau-so-do -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:doan-mau-so-do"
    return m.group(1)


def test_BON_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA


def test_TAC_PHAM_KHONG_BAO_GIO_nam_trong_tep_git_theo_doi():
    """Repo PUBLIC. `data/*` đang bị bỏ qua — nhưng một lần `git add -f` là lọt."""
    ra = subprocess.run(["git", "ls-files", "data/tham_chieu"], cwd=PROJECT_ROOT,
                        capture_output=True, text=True, check=True)
    assert ra.stdout.strip() == "", f"tác phẩm đã vào git: {ra.stdout[:200]}"
    kiem = subprocess.run(["git", "check-ignore", "-q", "data/tham_chieu/x/y.txt"],
                          cwd=PROJECT_ROOT)
    assert kiem.returncode == 0, "data/tham_chieu/ không còn bị .gitignore bỏ qua"
