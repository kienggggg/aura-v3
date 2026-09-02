# -*- coding: utf-8 -*-
"""trinh_cai_dat.py — trình cài đặt AURA Thẻ, đóng thành MỘT tệp .exe.

VÌ SAO CÓ TỆP NÀY. Bản gửi người thử trước đây là một tệp `.zip`: tải về, bấm
chuột phải, Extract All, tìm `.bat`, bấm đúp. Bốn bước, và bước thứ hai là chỗ
người không quen máy tính bỏ cuộc.

Đo được ngày 01/09/2026, cùng một mã nguồn, hai kiểu đóng gói:

    onedir (thư mục)   gửi 15,4 MB (zip)   khởi động 0,71 s
    onefile (một exe)  gửi 15,6 MB          khởi động 1,94 s   (chậm 2,7 lần)

Nên trình cài này lấy CẢ HAI: người dùng nhận **một tệp**, còn thứ được cài vào
máy là bản **onedir** chạy nhanh. Cái giá là trình cài phải mang theo bản onedir
đã nén bên trong.

BỐN CHỖ NÓ ĐỂ LẠI TRÊN MÁY — không có chỗ thứ năm:

  * `%LOCALAPPDATA%\\Programs\\AURA The`  — chương trình, 71 tệp / 30,2 MB
  * `Documents\\AURA The`                 — bài tập của người dùng
  * Lối tắt trên Desktop và trong Start Menu
  * MỘT khoá registry ở bậc tài khoản (`HKCU`), để "AURA Thẻ" hiện trong
    Settings > Apps. Không cần quyền quản trị, không đụng tài khoản khác.
    Cài đè lần thứ hai vẫn chỉ một mục — đo được: nền 18 -> 19 -> 19.

HAI ĐIỀU NÓ KHÔNG LÀM, và không giả vờ làm:

  * KHÔNG ký số. Windows vẫn hiện bảng xanh SmartScreen ở lần chạy đầu.
  * KHÔNG đụng vào thư mục bài của người dùng khi gỡ. Bài nằm ở
    `Documents\\AURA The` và ở lại đó — đo bằng cách sửa bài rồi cài đè rồi gỡ.

NÚT "Uninstall" TRONG SETTINGS: đã bấm thật, hai lần, cả hai dạng
`UninstallString`. Cả hai lần gỡ đúng bốn thứ và giữ nguyên bài tập, registry
về đúng nền 18 mục.

Cái bẫy trên đường tới đó đáng nhớ hơn kết quả: ba lần bấm đầu **không có gì
xảy ra**, và nguyên nhân không nằm trong tệp này. `SystemSettings.exe` mở lúc
06:41:37, khoá ghi lần cuối 06:48:19, và trong 7 phút giữa hai mốc tôi xoá rồi
tạo lại khoá HAI lần. Sếp bấm một mục trong danh sách chụp trước đó. **Đóng hẳn
Settings rồi mở lại thì nút chạy ngay** — kể cả với dạng chuỗi cũ.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

TEN_APP = "AURA The"
TEN_HIEN = "AURA Thẻ"
TEN_GOI = "goi_app.zip"          # nằm trong exe, do PyInstaller nhét vào


def _in(chu: str = "") -> None:
    """In an toàn — console Windows mặc định là cp1252, nuốt dấu tiếng Việt.

    CLAUDE.md mục 4: mọi phép đo/thông báo có tiếng Việt phải qua UTF-8, không
    thì "Thủ đô" thành "Thu do" và người đọc tưởng app hỏng font.
    """
    try:
        print(chu, flush=True)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((chu + "\n").encode("utf-8", "replace"))
        sys.stdout.flush()


def thu_muc_goc_du_lieu() -> Path:
    """Chỗ PyInstaller bung dữ liệu kèm theo, hoặc thư mục tệp này khi chạy thô."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def tao_loi_tat(duong_lnk: Path, dich: Path, doi_so: str, thu_muc_lam_viec: Path,
                mo_ta: str) -> bool:
    """Tạo một `.lnk` bằng PowerShell, rồi ĐỔI TÊN bằng Python.

    Không dùng `win32com` — thêm một gói ngoài chỉ để tạo hai lối tắt là trả
    giá sai chỗ. PowerShell có sẵn trên mọi máy Windows.

    VÌ SAO PHẢI ĐỔI TÊN. Tên lối tắt là "AURA Thẻ.lnk". Gọi thẳng
    `WScript.Shell.CreateShortcut` với tên ấy thì hỏng:

        Unable to save shortcut "...\\AURA Th?.lnk"

    Chữ `ẻ` thành `?`. Thử `-EncodedCommand` (base64 của UTF-16LE, không đi qua
    trang mã của console) — VẪN HỎNG y hệt. Tức thứ nuốt dấu không phải cách
    PowerShell nhận lệnh, mà là chính COM `WScript.Shell`: nó dựng đường dẫn
    theo trang mã ANSI của máy.

    Nên: tạo bằng tên ASCII, rồi `Path.rename` trong Python — Python không nuốt
    dấu. Đo 01/09/2026: ra đúng `AURA Thẻ.lnk`, 2.376 byte.

    Đây đúng luật ở CLAUDE.md mục 4 — *"Đo tiếng Việt bằng Python, đừng qua
    PowerShell"* — chỉ khác chỗ hỏng: không phải khi ĐỌC kết quả, mà khi
    PowerShell GHI một tệp có dấu.
    """
    tam = duong_lnk.with_name("_aura_loi_tat_tam.lnk")
    ps = (
        "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
        "try { $w = New-Object -ComObject WScript.Shell; "
        f"$s = $w.CreateShortcut('{tam}'); "
        f"$s.TargetPath = '{dich}'; "
        f"$s.Arguments = '{doi_so}'; "
        f"$s.WorkingDirectory = '{thu_muc_lam_viec}'; "
        f"$s.Description = '{mo_ta}'; "
        "$s.Save(); 'OK' } catch { 'LOI: ' + $_.Exception.Message }"
    )
    import base64

    b64 = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive",
                        "-EncodedCommand", b64],
                       capture_output=True, text=True, timeout=60)
    except Exception:  # noqa: BLE001 — không tạo được lối tắt thì báo, không ném
        return False
    if not tam.is_file():
        return False
    try:
        if duong_lnk.exists():
            duong_lnk.unlink()
        tam.rename(duong_lnk)
    except OSError:
        # Đổi tên hỏng thì vẫn còn tệp tạm — dọn đi, đừng để lại rác trên
        # Desktop của người dùng với một cái tên khó hiểu.
        try:
            tam.unlink()
        except OSError:
            pass
        return False
    return duong_lnk.is_file()


# Khoá đăng ký ứng dụng. CHỈ `HKEY_CURRENT_USER` — không bao giờ `HKLM`.
#
# HKCU thuộc về một tài khoản, không cần quyền quản trị, và không đụng tới
# người dùng khác trên cùng máy. HKLM thì ngược lại cả ba, nên trình cài này
# không biết đường tới đó.
#
# Đây là đăng ký ỨNG DỤNG (cùng loại việc với tạo lối tắt), không phải sửa cài
# đặt hệ thống hay bảo mật: không đụng chính sách, không đụng khởi động cùng
# Windows, không đụng gì ngoài đúng một khoá mang tên app.
KHOA_UNINSTALL = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
KHOA_APP = "AURA_The"

# Lấy từ %SystemRoot%, không đóng đinh "C:\Windows": máy cài Windows ở ổ khác
# thì đường dẫn cứng trỏ vào chỗ không có gì.
CMD_EXE = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "cmd.exe"


def dang_ky_apps_features(thu_muc_cai: Path, go_cai: Path) -> bool:
    """Tạo mục "AURA Thẻ" trong Settings > Apps > Installed apps.

    Dùng `winreg` của Python, KHÔNG dùng `reg.exe` hay PowerShell. Lý do đo
    được ngay trong tệp này: `WScript.Shell` ghi chuỗi qua trang mã ANSI nên
    "AURA Thẻ" thành "AURA Th?". `winreg` ghi `REG_SZ` bằng UTF-16 nên tên
    hiện đúng dấu trong Settings.

    Kiểm bằng một bộ đọc KHÁC, không tự đọc lại bằng `winreg` rồi tự chấm —
    `Get-Package -ProviderName Programs` là kho phần mềm của chính Windows::

        winreg đọc thẳng registry            'AURA Thẻ'
        Get-Package, console mặc định        'AURA Th?'
        Get-Package, OutputEncoding UTF-8    'AURA Thẻ'

    Ca đối chứng ở dòng ba nói rõ dấu hỏi ở dòng hai là do console PowerShell
    nuốt dấu lúc IN RA, không phải byte trong registry sai. Không có dòng ba
    thì dòng hai đọc y hệt "tên bị hỏng".
    """
    try:
        import winreg
    except ImportError:
        return False

    co = 0
    for f in thu_muc_cai.rglob("*"):
        if f.is_file():
            co += f.stat().st_size

    muc = {
        "DisplayName": TEN_HIEN,
        "DisplayVersion": "1.0",
        "Publisher": "AURA",
        "InstallLocation": str(thu_muc_cai),
        # Trỏ vào `cmd.exe` — một tệp `.exe` có thật — rồi đưa `.bat` làm đối
        # số, thay vì trỏ thẳng vào `.bat`.
        #
        # DẠNG NÀY KHÔNG SỬA LỖI NÀO CẢ. Nói rõ vì suýt nữa nó được ghi vào đây
        # như một bản vá. 02/09/2026, Sếp bấm nút Uninstall trong Settings ba
        # lần, cả ba lần không có gì xảy ra; tôi đổi chuỗi sang dạng này, lần
        # thứ tư chạy được, và tôi định kết luận là đã vá xong.
        #
        # Nhưng giữa lần hỏng và lần chạy có HAI biến cùng đổi: dạng chuỗi, và
        # cửa sổ Settings được đóng rồi mở lại. Ca đối chứng — cài bình thường
        # rồi ghi đè NGƯỢC đúng một giá trị về dạng cũ, giữ nguyên Settings mở
        # mới — cho kết quả:
        #
        #     chuỗi mới + Settings mở mới   -> CHẠY
        #     chuỗi CŨ  + Settings mở mới   -> CHẠY   <- dạng chuỗi vô can
        #
        # Thủ phạm thật là danh sách cũ: `SystemSettings.exe` mở lúc 06:41:37,
        # khoá ghi lần cuối 06:48:19, và trong 7 phút giữa hai mốc tôi xoá rồi
        # tạo lại khoá HAI lần. Sếp bấm một mục trong ảnh chụp trước đó. Lỗi
        # nằm ở cách tôi bố trí phép thử, không ở mã.
        #
        # VẪN GIỮ dạng `cmd.exe`, vì một lý do khác, đo được cơ chế:
        #
        #     .bat -> batfile -> "%1" %*   (HKCR, bậc máy)
        #     HKCU\...\FileExts\.bat\UserChoice   không có trên máy này
        #
        # `ShellExecute` mở `.bat` bằng cách tra bảng liên kết phần mở rộng, mà
        # bảng ấy người dùng đè lên được. Máy này sạch nên cả hai dạng chạy;
        # máy nào lỡ gán `.bat` cho một trình soạn thảo thì nút Uninstall mở
        # trình soạn thảo — im lặng, đúng kiểu hỏng vừa tốn một tiếng để tìm.
        # `cmd.exe` không đi qua bảng đó. CHƯA ĐO ĐƯỢC trên một máy bị đè liên
        # kết như vậy; đây là suy luận từ cơ chế, không phải từ số.
        #
        # Dấu nháy đôi quanh `.bat`: cmd bóc một lớp nháy ngoài cùng, đường dẫn
        # có khoảng trắng ("AURA The") cần lớp còn lại.
        "UninstallString": f'"{CMD_EXE}" /c ""{go_cai}""',
        "DisplayIcon": str(thu_muc_cai / "AURA_The.exe"),
        # NoModify/NoRepair: Settings sẽ chỉ hiện nút "Uninstall", không hiện
        # hai nút kia — bấm vào chúng thì chẳng có gì chạy.
        "NoModify": 1,
        "NoRepair": 1,
    }
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                f"{KHOA_UNINSTALL}\\{KHOA_APP}", 0,
                                winreg.KEY_WRITE) as k:
            for ten, gt in muc.items():
                if isinstance(gt, int):
                    winreg.SetValueEx(k, ten, 0, winreg.REG_DWORD, gt)
                else:
                    winreg.SetValueEx(k, ten, 0, winreg.REG_SZ, gt)
            # Settings đọc trường này theo KB, không phải byte.
            winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, co // 1024)
        return True
    except OSError:
        return False


NOI_DUNG_GO_CAI = """@echo off
chcp 65001 > nul
rem Tệp này nằm TRONG thư mục nó sắp xoá. Đo 01/09/2026, chạy tại chỗ:
rem `rmdir` xoá luôn chính tệp đang chạy, cmd đọc dòng kế thì không còn tệp ->
rem in "The system cannot find the path specified", THOÁT MÃ 1, và người dùng
rem KHÔNG thấy dòng "Xong" lẫn `pause` — cửa sổ tắt giữa chừng. Từ Settings >
rem Apps thì mã 1 ấy đọc ra là "gỡ cài đặt hỏng".
rem Nên: tự chép sang %TEMP% rồi chạy bản chép; bản gốc `exit` NGAY (không
rem `exit /b`) để tiến trình chết hẳn và nhả tệp ra cho `rmdir`.
if "%~1"=="--tu-temp" goto lam
copy /Y "%~f0" "%TEMP%\\AURA_The_go_cai.bat" > nul
start "" "%TEMP%\\AURA_The_go_cai.bat" --tu-temp
exit

:lam
title Gỡ cài đặt AURA Thẻ
echo.
echo   Gỡ cài đặt AURA Thẻ
echo   ------------------------------------------------------------
echo   Sẽ xoá:      {thu_muc_cai}
echo   GIỮ NGUYÊN:  {thu_muc_bai}
echo.
choice /C YN /M "Xoá chương trình (bài tập của bạn vẫn còn)"
if errorlevel 2 goto thoi
del "{lnk_desktop}" 2>nul
del "{lnk_menu}" 2>nul
rem Xoá mục trong Settings > Apps. CHỈ HKCU, chỉ đúng khoá của app này.
rem Xoá TRƯỚC khi xoá thư mục: nếu rmdir hỏng (app đang chạy) thì ít nhất
rem Settings không còn trỏ vào một UninstallString đã chết.
reg delete "HKCU\\{khoa_uninstall}\\{khoa_app}" /f >nul 2>&1
echo   Đang xoá...
cd /d "%TEMP%"
rmdir /S /Q "{thu_muc_cai}"
echo.
echo   Xong. Bài tập của bạn vẫn ở: {thu_muc_bai}
echo.
pause
exit /b 0
:thoi
echo   Đã huỷ, không xoá gì.
pause
exit /b 0
"""


def cai_dat() -> int:
    goi = thu_muc_goc_du_lieu() / TEN_GOI
    if not goi.is_file():
        _in(f"HỎNG: không thấy gói `{TEN_GOI}` bên trong trình cài.")
        _in("Trình cài này bị dựng thiếu — tải lại bản mới giúp mình.")
        return 2

    mac_dinh = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / TEN_APP
    thu_muc_bai = Path.home() / "Documents" / TEN_APP

    _in("=" * 66)
    _in(f"  Cài đặt {TEN_HIEN} — lập trình Python bằng cách kéo thả thẻ")
    _in("=" * 66)
    _in(f"  Chương trình sẽ vào : {mac_dinh}")
    _in(f"  Bài tập của bạn vào : {thu_muc_bai}")
    _in("  Lối tắt             : Desktop và Start Menu")
    _in("  Gỡ ra bằng          : Settings > Apps > AURA Thẻ > Uninstall")
    _in("")
    _in("  Máy này KHÔNG cần cài Python. Không có gì gửi lên mạng.")
    _in("  Lưu ý: mã bạn bấm CHẠY THỬ có đủ quyền của tài khoản Windows")
    _in("  đang dùng — KHÔNG có hộp cát. Chỉ chạy mã do chính bạn viết.")
    _in("=" * 66)

    if "--im-lang" not in sys.argv:
        try:
            tra_loi = input("  Cài vào đó? [Enter = đồng ý, gõ 'k' = thôi]: ").strip().lower()
        except EOFError:
            tra_loi = ""
        if tra_loi in ("k", "n", "khong", "không"):
            _in("  Đã huỷ, không thay đổi gì trên máy.")
            return 0

    dich = mac_dinh
    # Cài đè: xoá bản cũ TRƯỚC, không bung chồng lên. Bung chồng thì tệp của
    # bản cũ mà bản mới đã bỏ vẫn nằm lại và app nạp nhầm.
    if dich.exists():
        _in(f"  Thấy bản cũ ở đó, đang xoá trước khi cài lại...")
        try:
            shutil.rmtree(dich)
        except OSError as loi:
            _in(f"  KHÔNG XOÁ ĐƯỢC bản cũ: {loi}")
            _in("  App có đang chạy không? Đóng nó rồi cài lại giúp mình.")
            return 2

    _in("  Đang bung tệp...")
    try:
        dich.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(goi) as z:
            z.extractall(dich)
    except Exception as loi:  # noqa: BLE001 — câu này đi thẳng lên màn hình
        _in(f"  HỎNG khi bung: {type(loi).__name__}: {loi}")
        return 2

    # Gói được nén với thư mục gốc `AURA_The/` — kéo nội dung lên một bậc để
    # đường dẫn lối tắt không phụ thuộc vào tên ấy.
    trong = dich / "AURA_The"
    if trong.is_dir():
        for m in list(trong.iterdir()):
            shutil.move(str(m), str(dich / m.name))
        trong.rmdir()

    exe = dich / "AURA_The.exe"
    if not exe.is_file():
        _in("  HỎNG: bung xong mà không thấy AURA_The.exe.")
        return 2

    thu_muc_bai.mkdir(parents=True, exist_ok=True)
    # Bài mẫu: chỉ chép khi CHƯA có, không đè bài người dùng đã sửa.
    mau = dich / "bai_cua_toi" / "vi_du.py"
    if mau.is_file() and not (thu_muc_bai / "vi_du.py").exists():
        shutil.copy(mau, thu_muc_bai / "vi_du.py")

    doi_so = f'--allow-exec --du-an "{thu_muc_bai}"'
    desktop = Path.home() / "Desktop" / f"{TEN_HIEN}.lnk"
    menu_thu_muc = (Path(os.environ.get("APPDATA", Path.home())) / "Microsoft"
                    / "Windows" / "Start Menu" / "Programs")
    menu_thu_muc.mkdir(parents=True, exist_ok=True)
    menu = menu_thu_muc / f"{TEN_HIEN}.lnk"

    # Mô tả KHÔNG DẤU, có chủ đích. Đo 01/09: `WScript.Shell` ghi trường này
    # qua trang mã ANSI, nên "Lập trình bằng thẻ" nằm trong tệp `.lnk` thành
    # "L?p tr?nh b?ng th?" — người dùng rê chuột vào thấy một dòng dấu hỏi.
    # TÊN lối tắt thì vẫn có dấu đầy đủ, vì nó do Python đổi tên (xem
    # `tao_loi_tat`); chỉ trường mô tả bên trong tệp là không cứu được.
    MO_TA = "AURA The - lap trinh Python bang cach keo tha the"
    ok_desktop = tao_loi_tat(desktop, exe, doi_so, dich, MO_TA)
    ok_menu = tao_loi_tat(menu, exe, doi_so, dich, MO_TA)

    (dich / "GO_CAI_DAT.bat").write_text(
        NOI_DUNG_GO_CAI.format(thu_muc_cai=dich, thu_muc_bai=thu_muc_bai,
                               lnk_desktop=desktop, lnk_menu=menu,
                               khoa_uninstall=KHOA_UNINSTALL, khoa_app=KHOA_APP),
        encoding="utf-8")

    ok_reg = dang_ky_apps_features(dich, dich / "GO_CAI_DAT.bat")

    _in("")
    _in("  XONG.")
    _in(f"    Lối tắt Desktop    : {'có' if ok_desktop else 'KHÔNG TẠO ĐƯỢC'}")
    _in(f"    Lối tắt Start Menu : {'có' if ok_menu else 'KHÔNG TẠO ĐƯỢC'}")
    _in(f"    Trong Settings/Apps: {'có' if ok_reg else 'KHÔNG ĐĂNG KÝ ĐƯỢC'}")
    if not (ok_desktop or ok_menu):
        # Không có lối tắt nào thì phải chỉ đường khác, không để người dùng
        # cài xong rồi không biết mở bằng gì.
        _in(f"    Mở trực tiếp bằng  : {exe}")
    _in(f"    Bài tập của bạn ở  : {thu_muc_bai}")
    _in(f"    Gỡ cài đặt         : {dich / 'GO_CAI_DAT.bat'}")
    _in("")

    if "--im-lang" not in sys.argv:
        try:
            if input("  Mở AURA Thẻ luôn? [Enter = mở, 'k' = thôi]: ").strip().lower() not in ("k", "n"):
                subprocess.Popen([str(exe), "--allow-exec", "--du-an", str(thu_muc_bai)],
                                 cwd=str(dich))
        except EOFError:
            pass
    return 0


if __name__ == "__main__":
    for _l in (sys.stdout, sys.stderr):
        if hasattr(_l, "reconfigure"):
            _l.reconfigure(encoding="utf-8", errors="replace")
    ma = cai_dat()
    if "--im-lang" not in sys.argv:
        try:
            input("  Bấm Enter để đóng cửa sổ này.")
        except EOFError:
            pass
    raise SystemExit(ma)
