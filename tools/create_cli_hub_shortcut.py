# -*- coding: utf-8 -*-
"""Tạo lối tắt AURA CLI Hub ra màn hình Desktop thật (tự động nhận diện OneDrive Desktop).

Chạy trực tiếp bằng pythonw.exe: 0 giây giật màn hình đen, mở thẳng bảng điều khiển.
"""
import io
import os
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_PYW = PROJECT_ROOT / "cli_hub.pyw"
PYTHONW_EXE = PROJECT_ROOT / "venv" / "Scripts" / "pythonw.exe"

if not PYTHONW_EXE.exists():
    PYTHONW_EXE = Path(sys.executable).with_name("pythonw.exe")


def get_real_desktop() -> Path:
    """Lấy đúng đường dẫn Desktop thực tế của Windows (kể cả khi dùng OneDrive)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        desktop_val, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        expanded = os.path.expandvars(desktop_val)
        if Path(expanded).is_dir():
            return Path(expanded)
    except Exception:
        pass
    
    # Fallback
    user_profile = Path(os.environ.get("USERPROFILE", ""))
    onedrive_desktop = user_profile / "OneDrive" / "Desktop"
    if onedrive_desktop.is_dir():
        return onedrive_desktop
    return user_profile / "Desktop"


def create_shortcuts():
    """Tạo lối tắt CLI Hub trên màn hình nền và trong kho, kèm biểu tượng."""
    real_desktop = get_real_desktop()
    destinations = [real_desktop / "AURA CLI Hub.lnk", PROJECT_ROOT / "AURA CLI Hub.lnk"]

    # Biểu tượng tia sét / terminal từ imageres.dll
    icon_loc = r"C:\Windows\System32\imageres.dll,109"

    vbs_lines = ['Set WshShell = WScript.CreateObject("WScript.Shell")']
    for dst in destinations:
        vbs_lines.extend([
            f'Set Shortcut = WshShell.CreateShortcut("{dst}")',
            f'Shortcut.TargetPath = "{PYTHONW_EXE}"',
            f'Shortcut.Arguments = """{TARGET_PYW}"""',
            f'Shortcut.WorkingDirectory = "{PROJECT_ROOT}"',
            'Shortcut.Description = "AURA AI CLI Hub — Trình Quản Lý & Khởi Chạy CLI"',
            'Shortcut.WindowStyle = 7',
            f'Shortcut.IconLocation = "{icon_loc}"',
            'Shortcut.Save',
        ])

    vbs_content = "\r\n".join(vbs_lines)
    tmp_vbs = PROJECT_ROOT / ".tmp_create_cli_shortcut.vbs"

    try:
        tmp_vbs.write_bytes(vbs_content.encode("utf-16"))
        subprocess.run(["cscript", "//Nologo", str(tmp_vbs)], check=True)
        print("Đã tạo thành công lối tắt tại:")
        for dst in destinations:
            print(f"  -> {dst}")
        return True
    finally:
        if tmp_vbs.exists():
            tmp_vbs.unlink()


if __name__ == "__main__":
    create_shortcuts()
