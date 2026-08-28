# -*- coding: utf-8 -*-
"""tao_loi_tat_desktop.py — Tạo các lối tắt (shortcuts) ra ngoài màn hình Desktop trên Windows."""
import os
from pathlib import Path
import subprocess
import sys

def tao_loi_tat():
    goc = Path(__file__).resolve().parent.parent
    
    # Tìm đường dẫn Desktop
    desktop_env = os.environ.get("USERPROFILE", "")
    desktop_onedrive = Path(desktop_env) / "OneDrive" / "Desktop"
    desktop_local = Path(desktop_env) / "Desktop"
    
    desktop = desktop_onedrive if desktop_onedrive.is_dir() else desktop_local
    if not desktop.is_dir():
        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        
    ds_loi_tat = [
        {
            "ten": "AURA The v1 IDE.lnk",
            "dich": str(goc / "start_the_app_day_du.bat"),
            "thu_muc": str(goc),
            "mo_ta": "AURA Thẻ v1 — Trình lập trình bằng thẻ trực quan"
        },
        {
            "ten": "AURA Command Center (Noi Bo).lnk",
            "dich": str(goc / "start_app_noi_bo.bat"),
            "thu_muc": str(goc),
            "mo_ta": "AURA Command Center — App điều hành 7 Đặc Nhiệm"
        },
        {
            "ten": "Lo Trinh Hoc AI va Tieng Anh.lnk",
            "dich": str(goc / "docs" / "LO_TRINH_HOC_AI_VA_TIENG_ANH.md"),
            "thu_muc": str(goc / "docs"),
            "mo_ta": "Lộ trình học AI từ gốc rễ và Tiếng Anh thực chiến"
        }
    ]
    
    ps_commands = ["$wsh = New-Object -ComObject WScript.Shell;"]
    for lt in ds_loi_tat:
        duong_dan_lnk = str(desktop / lt["ten"])
        ps_commands.append(
            f'$s = $wsh.CreateShortcut(\'{duong_dan_lnk}\'); '
            f'$s.TargetPath = \'{lt["dich"]}\'; '
            f'$s.WorkingDirectory = \'{lt["thu_muc"]}\'; '
            f'$s.Description = \'{lt["mo_ta"]}\'; '
            f'$s.Save();'
        )
        
    lenh_ps = " ".join(ps_commands)
    subprocess.run(["powershell", "-NoProfile", "-Command", lenh_ps], check=True)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"[OK] Da tao 3 loi tat thanh cong tai Desktop: {desktop}")

if __name__ == "__main__":
    tao_loi_tat()
