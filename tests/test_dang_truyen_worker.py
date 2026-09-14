# -*- coding: utf-8 -*-
"""Công cụ đăng, vòng 0 — `tools/dang_truyen_worker.py` (`CHOT:dang-vong-0`, 14/09/2026).

Chạy trong venv v3, KHÔNG có Playwright: tệp được import mà không cần gói ấy, vì nó chỉ
import Playwright bên trong hàm. Canh ba điều mà một lần sửa vội sẽ phá lặng lẽ.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT
from tools import dang_truyen_worker as w

# Chép TAY: Sếp chỉ trang ngày 14/09; hồ sơ ngoài repo theo `CLAUDE.md` §2.
DAC_TA_GOC_HO_SO = Path(r"F:\aura-dang")
DAC_TA_NEN_TANG = {"wattpad": "www.wattpad.com", "sangtacviet": "sangtacviet.com"}
# Bất kỳ lời gọi nào làm thay đổi trang — vòng 0 bước 1–2 không được có.
LENH_THAO_TAC = {"click", "dblclick", "fill", "type", "press", "check", "uncheck",
                 "select_option", "set_input_files", "tap", "dispatch_event", "evaluate"}


def test_HO_SO_nam_NGOAI_repo_va_dung_goc():
    assert w.GOC_HO_SO == DAC_TA_GOC_HO_SO
    for nt in DAC_TA_NEN_TANG:
        d = w.ho_so(nt)
        assert d.parent == DAC_TA_GOC_HO_SO
        assert PROJECT_ROOT.resolve() not in d.resolve().parents, (
            f"hồ sơ {d} nằm TRONG repo — phiên đăng nhập sẽ bị git đụng tới")


def test_NEN_TANG_dung_hai_trang_Sep_chi():
    assert set(w.NEN_TANG) == set(DAC_TA_NEN_TANG)
    for nt, mien in DAC_TA_NEN_TANG.items():
        for url in w.NEN_TANG[nt].values():
            assert url.startswith(f"https://{mien}/"), (nt, url)


def test_NEN_TANG_LA_thi_NO_khong_doan():
    with pytest.raises(ValueError):
        w.ho_so("wattpad.com")


@pytest.mark.parametrize("ham", ["mo", "xem", "_mo_trinh_duyet"])
def test_VONG_0_KHONG_BAM_GI(ham):
    """Bước 1 là Sếp tự đăng nhập, bước 2 chỉ đọc. Có một lời gọi thao tác là đã vượt vòng 0."""
    cay = ast.parse((PROJECT_ROOT / "tools" / "dang_truyen_worker.py").read_text(encoding="utf-8"))
    than = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ham)
    goi = {n.func.attr for n in ast.walk(than)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not (goi & LENH_THAO_TAC), f"{ham} gọi {sorted(goi & LENH_THAO_TAC)}"


def test_TRINH_DUYET_THAT_khong_an_khong_gia():
    """Không chạy ẩn, không truyền cờ giả vân tay — `CLAUDE.md` §2: không né chặn bot."""
    nguon = (PROJECT_ROOT / "tools" / "dang_truyen_worker.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "launch_persistent_context"]
    assert len(goi) == 1
    kw = {k.arg: k.value for k in goi[0].keywords}
    assert isinstance(kw.get("headless"), ast.Constant) and kw["headless"].value is False
    assert not ({"args", "user_agent", "ignore_default_args"} & set(kw)), sorted(kw)
    assert "stealth" not in nguon.lower()
