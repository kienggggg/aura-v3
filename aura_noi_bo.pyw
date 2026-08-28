# -*- coding: utf-8 -*-
"""aura_noi_bo.pyw — AURA Command Center v3 như một ứng dụng desktop 1-click.

Chạy bằng `pythonw.exe` không cửa sổ console đen:
  1) Khởi động server nội bộ `noi_bo_app.py` trên cổng 8890 nếu chưa chạy.
  2) Chờ server sẵn sàng.
  3) Mở trình duyệt ở chế độ ứng dụng desktop (--app=http://127.0.0.1:8890/).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent
CONG = int(os.environ.get("AURA_NOI_BO_PORT", "8890"))
DIA_CHI = f"http://127.0.0.1:{CONG}"
CHO_TOI_DA = 15.0
_KHONG_CUA_SO = 0x08000000  # CREATE_NO_WINDOW


def _pythonw() -> str:
    exe = Path(sys.executable)
    ung_vien = exe.with_name("pythonw.exe")
    if ung_vien.exists():
        return str(ung_vien)
    trong_venv = GOC / "venv" / "Scripts" / "pythonw.exe"
    return str(trong_venv if trong_venv.exists() else exe)


def dang_chay() -> bool:
    """Kiểm tra server nội bộ đã phản hồi chưa."""
    try:
        with urllib.request.urlopen(f"{DIA_CHI}/api/status", timeout=2) as res:
            body = json.loads(res.read().decode("utf-8"))
        return str(body.get("service", "")).startswith("aura-noi-bo")
    except Exception:
        return False


def bat_server() -> None:
    """Bật server ngầm nếu chưa chạy."""
    lenh = [_pythonw(), "-m", "interface.noi_bo_app", "--port", str(CONG)]
    tuy_chon = {"cwd": str(GOC)}
    if sys.platform.startswith("win"):
        tuy_chon["creationflags"] = _KHONG_CUA_SO
    subprocess.Popen(lenh, **tuy_chon)


def cho_san_sang(han: float = CHO_TOI_DA) -> bool:
    """Chờ cho tới khi server sẵn sàng."""
    het_gio = time.monotonic() + han
    while time.monotonic() < het_gio:
        if dang_chay():
            return True
        time.sleep(0.4)
    return False


def mo_app() -> None:
    """Mở giao diện ở chế độ ứng dụng desktop (--app)."""
    trinh_duyet = [
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("brave"),
    ]
    for exe in trinh_duyet:
        if exe:
            try:
                subprocess.Popen([exe, f"--app={DIA_CHI}/"])
                return
            except Exception:
                pass
    import webbrowser
    webbrowser.open(DIA_CHI)


def main() -> None:
    if not dang_chay():
        bat_server()
    if cho_san_sang():
        mo_app()


if __name__ == "__main__":
    main()
