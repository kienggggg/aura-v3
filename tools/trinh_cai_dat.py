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

BA ĐIỀU TRÌNH CÀI NÀY KHÔNG LÀM, và không giả vờ làm:

  * KHÔNG ghi Registry. Không có mục trong "Apps & features". Gỡ cài bằng
    `GO_CAI_DAT.bat` trong thư mục cài, hoặc xoá thư mục.
  * KHÔNG ký số. Windows vẫn hiện bảng xanh SmartScreen ở lần chạy đầu.
  * KHÔNG đụng vào thư mục bài của người dùng khi gỡ. Bài nằm ở
    `Documents\\AURA The` và ở lại đó.
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


NOI_DUNG_GO_CAI = """@echo off
chcp 65001 > nul
title Gỡ cài đặt AURA Thẻ
echo.
echo   Gỡ cài đặt AURA Thẻ
echo   ------------------------------------------------------------
echo   Sẽ xoá:      %~dp0
echo   GIỮ NGUYÊN:  {thu_muc_bai}
echo.
choice /C YN /M "Xoá chương trình (bài tập của bạn vẫn còn)"
if errorlevel 2 goto thoi
del "{lnk_desktop}" 2>nul
del "{lnk_menu}" 2>nul
echo   Đang xoá...
cd /d "%TEMP%"
rmdir /S /Q "{thu_muc_cai}"
echo   Xong. Bài tập của bạn vẫn ở: {thu_muc_bai}
pause
exit /b 0
:thoi
echo   Đã huỷ, không xoá gì.
pause
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
                               lnk_desktop=desktop, lnk_menu=menu),
        encoding="utf-8")

    _in("")
    _in("  XONG.")
    _in(f"    Lối tắt Desktop    : {'có' if ok_desktop else 'KHÔNG TẠO ĐƯỢC'}")
    _in(f"    Lối tắt Start Menu : {'có' if ok_menu else 'KHÔNG TẠO ĐƯỢC'}")
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
