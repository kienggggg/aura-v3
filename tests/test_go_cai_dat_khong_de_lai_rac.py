# -*- coding: utf-8 -*-
"""Gỡ cài đặt phải xoá HẾT thứ trình cài tạo ra — và chỉ thứ nó tạo ra.

VÌ SAO CÓ TỆP NÀY. 01/09/2026, thêm mục "AURA Thẻ" vào Settings > Apps. Mục ấy
là một khoá registry, tức là thứ ĐẦU TIÊN trình cài để lại NGOÀI thư mục của
chính nó. Ba câu hỏi phải có cửa canh, không được để cho trí nhớ:

1. **Chỉ `HKCU`.** Bậc kia cần quyền quản trị và đụng vào mọi tài khoản trên máy.
2. **Gỡ được.** Ghi một khoá mà không xoá ra thì Settings sẽ mãi hiện một mục
   trỏ vào thư mục đã biến mất.
3. **Không đụng bài tập của người dùng.**

Và một lỗi ĐO ĐƯỢC ngay hôm ấy, vốn có từ trước lúc thêm registry.
`GO_CAI_DAT.bat` nằm TRONG thư mục nó sắp xoá, nên chạy tại chỗ thì::

    rmdir /S /Q "<thư mục cài>"   -> xoá luôn chính tệp .bat đang chạy
    dòng kế tiếp                  -> "The system cannot find the path specified"
    mã thoát                      -> 1
    người dùng thấy               -> KHÔNG có "Xong", KHÔNG có `pause`

Cửa sổ tắt giữa chừng, và từ Settings > Apps thì mã 1 ấy đọc ra là *"gỡ cài đặt
hỏng"*. Sửa: tệp tự chép sang `%TEMP%` rồi `start` bản chép, bản gốc `exit` ngay
để nhả tệp. Đo lại sau khi sửa::

    nhánh 1 (bấm .bat)     thoát 0 · chép sang %TEMP% đúng byte · sinh 1 cửa sổ
    nhánh 2 (--tu-temp)    thoát 0 · stderr rỗng · CÓ dòng "Xong."
                           khoá False · thư mục False · lnk False,False · BÀI True
    ca đối chứng (bấm N)   thoát 0 · khoá True · thư mục True · lnk True,True

Một cái bẫy của MÁY ĐO gặp trên đường, ghi lại kẻo mắc lại: chạy dòng
``reg delete "HKCU\\..." /f`` qua ``subprocess.run(["cmd", "/c", <chuỗi>])`` thì
báo *"unable to find the specified registry key"* trong khi khoá CÓ THẬT — vì
``subprocess`` bọc lại dấu nháy thành ``\\"`` nên ``reg`` nhận tên khoá kèm dấu
nháy. Gọi thẳng ``reg.exe`` thì thoát 0. Nên các cửa dưới đây đọc dòng lệnh RA
TỪ chuỗi ``.bat`` thật, không gõ lại bằng tay.
"""
from __future__ import annotations

import io
import tokenize
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT
from tools.trinh_cai_dat import KHOA_APP, KHOA_UNINSTALL, NOI_DUNG_GO_CAI

NGUON = Path(PROJECT_ROOT, "tools", "trinh_cai_dat.py").read_text(encoding="utf-8")

CAI = r"C:\gia\Programs\AURA The"
BAI = r"C:\gia\Documents\AURA The"
LNK_D = r"C:\gia\Desktop\AURA The.lnk"
LNK_M = r"C:\gia\Start Menu\AURA The.lnk"


def bat_that() -> str:
    """Chuỗi .bat ĐÚNG NHƯ nó được ghi ra đĩa, không phải bản gõ lại."""
    return NOI_DUNG_GO_CAI.format(thu_muc_cai=CAI, thu_muc_bai=BAI,
                                  lnk_desktop=LNK_D, lnk_menu=LNK_M,
                                  khoa_uninstall=KHOA_UNINSTALL,
                                  khoa_app=KHOA_APP)


def bat_khong_chu_thich() -> str:
    """Bỏ các dòng `rem` của .bat trước khi đi tìm VỊ TRÍ của lệnh.

    Cửa này bắt được chính nó lúc mới viết: ``bat.index("rmdir")`` trả về 103,
    nhưng vị trí 103 nằm trong câu GIẢI THÍCH *"rem rmdir xoá luôn chính tệp
    đang chạy"* chứ không phải lệnh ``rmdir`` ở cuối. So thứ tự trên chuỗi thô
    thì ra ``658 < 103`` — đúng bệnh ``x in y`` ở CLAUDE.md mục 4, lần này nằm
    ngay trong cửa canh sinh ra để chống nó.
    """
    bo = ("rem ", "rem\t", "::")
    return "\n".join(d for d in bat_that().split("\n")
                     if not d.strip().lower().startswith(bo))


def ma_khong_chu_thich() -> str:
    """Bỏ chú thích VÀ chuỗi, chỉ còn mã thật.

    Cần thiết vì cả tệp này lẫn ``trinh_cai_dat.py`` đều VIẾT tên bậc registry
    kia ra trong lời giải thích. Dò chuỗi trên nguyên tệp thì bắt nhầm câu giải
    thích và báo đỏ oan — đúng bệnh ``x in y`` mà CLAUDE.md mục 4 nói.
    """
    ra = []
    for tok in tokenize.generate_tokens(io.StringIO(NGUON).readline):
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            ra.append(tok.string)
    return " ".join(ra)


# ---------------------------------------------------------------- chỉ HKCU

def test_ma_chi_dung_HKEY_CURRENT_USER():
    ma = ma_khong_chu_thich()
    assert "HKEY_CURRENT_USER" in ma, "không thấy nhánh ghi registry nào"
    assert "HKEY_LOCAL_MACHINE" not in ma, (
        "bậc máy cần quyền quản trị và đụng vào MỌI tài khoản trên máy. Trình "
        "cài này cài cho một người, phải ghi vào chỗ của một người."
    )


def test_bat_cung_chi_ghi_vao_bac_nguoi_dung():
    """Chuỗi .bat không đi qua ``tokenize``, nên phải soi riêng."""
    bat = bat_that()
    assert "HKLM" not in bat and "HKEY_LOCAL_MACHINE" not in bat, (
        "gỡ cài đặt đụng vào bậc máy — trình cài chưa từng ghi vào đó"
    )


def test_khoa_nam_dung_cho_Settings_doc():
    assert KHOA_UNINSTALL.endswith("CurrentVersion\\Uninstall"), KHOA_UNINSTALL
    assert KHOA_APP and "\\" not in KHOA_APP, (
        "tên khoá app phải là MỘT bậc, không được lồng thêm đường dẫn"
    )


# -------------------------------------------------- .bat xoá đúng khoá ấy

def dong_reg_delete() -> str:
    dong = [d.strip() for d in bat_that().split("\n")
            if d.strip().lower().startswith("reg delete")]
    assert len(dong) == 1, f"phải có ĐÚNG một dòng `reg delete`, đang có {len(dong)}"
    return dong[0]


def test_bat_xoa_dung_khoa_ma_ham_ghi_da_tao():
    """Ghi một chỗ, xoá một chỗ khác thì Settings giữ lại mục chết."""
    d = dong_reg_delete()
    can = '"HKCU\\' + KHOA_UNINSTALL + "\\" + KHOA_APP + '"'
    assert can in d, f"dòng xoá không trỏ vào khoá đã ghi.\n  có : {d}\n  cần: {can}"
    assert "/f" in d.split(), "thiếu /f — `reg delete` sẽ dừng lại hỏi Y/N"


def test_xoa_khoa_TRUOC_khi_xoa_thu_muc():
    """rmdir có thể hỏng (app đang chạy). Khoá phải đi trước, kẻo Settings còn
    một mục trỏ vào ``UninstallString`` đã chết."""
    bat = bat_khong_chu_thich()
    assert bat.index("reg delete") < bat.index("rmdir"), (
        "xoá thư mục trước rồi mới xoá khoá — rmdir hỏng thì mục ở Settings ở lại"
    )


# ------------------------- không tự xoá mình giữa chừng (lỗi mã thoát 1)

def test_bat_tu_chep_sang_TEMP_truoc_khi_xoa_thu_muc_chua_no():
    bat = bat_khong_chu_thich()
    assert "--tu-temp" in bat, (
        "thiếu rào tự-chép: chạy tại chỗ thì `rmdir` xoá luôn tệp .bat đang "
        "chạy -> mã thoát 1, người dùng không thấy 'Xong' lẫn `pause`"
    )
    i_rao = bat.index('if "%~1"=="--tu-temp"')
    i_start = bat.index("start ")
    i_lam = bat.index(":lam")
    i_rmdir = bat.index("rmdir")
    assert i_rao < i_start < i_lam < i_rmdir, (
        f"thứ tự sai: rào={i_rao} start={i_start} :lam={i_lam} rmdir={i_rmdir}"
    )


def test_ban_goc_thoat_han_de_nha_tep():
    """``exit /b`` chỉ thoát tệp .bat; tiến trình cmd còn sống và còn GIỮ tệp.

    Phải ``exit`` trần thì tiến trình chết hẳn, ``rmdir`` của cửa sổ kia mới xoá
    được thư mục.
    """
    bat = bat_khong_chu_thich()
    dau = bat[:bat.index(":lam")]
    dong_thoat = [d.strip() for d in dau.split("\n") if d.strip().startswith("exit")]
    assert dong_thoat == ["exit"], (
        f"nhánh trước `:lam` phải thoát bằng `exit` trần, đang là {dong_thoat}"
    )


def test_start_chay_ban_trong_TEMP_chu_khong_phai_ban_goc():
    bat = bat_that()
    dong = [d.strip() for d in bat.split("\n") if d.strip().startswith("start ")]
    assert len(dong) == 1, dong
    assert "%TEMP%" in dong[0], (
        "`start` phải gọi bản trong %TEMP%, không phải bản nằm trong thư mục "
        f"sắp bị xoá: {dong[0]}"
    )
    assert "--tu-temp" in dong[0], "quên truyền cờ -> bản chép lại đi chép tiếp"


# ------------------------------- UninstallString phải trỏ vào một .exe có thật

def test_uninstall_string_tro_vao_mot_exe_CO_THAT(tmp_path):
    """Không trỏ thẳng vào `.bat`.

    CỬA NÀY KHÔNG SINH RA TỪ MỘT LỖI ĐÃ XẢY RA. Nói rõ để người sau không đọc
    ngược. 02/09/2026, nút Uninstall trong Settings bấm ba lần không có gì xảy
    ra; đổi chuỗi sang `cmd.exe /c ""bat""` thì lần thứ tư chạy. Nhưng hai biến
    cùng đổi — dạng chuỗi, và Settings được đóng rồi mở lại. Ca đối chứng, ghi
    đè NGƯỢC đúng một giá trị về dạng cũ và giữ Settings mở mới::

        chuỗi mới + Settings mở mới   -> CHẠY
        chuỗi CŨ  + Settings mở mới   -> CHẠY

    Dạng chuỗi vô can. Thủ phạm là danh sách cũ: Settings mở lúc 06:41:37, khoá
    ghi lần cuối 06:48:19, giữa hai mốc khoá bị xoá và tạo lại hai lần.

    Lý do VẪN đóng đinh dạng `.exe` là chuyện khác, đo được cơ chế::

        .bat -> batfile -> "%1" %*                  HKCR, bậc máy
        HKCU\\...\\FileExts\\.bat\\UserChoice          không có trên máy này

    `ShellExecute` mở `.bat` bằng cách tra bảng liên kết mà người dùng đè lên
    được; máy nào gán `.bat` cho một trình soạn thảo thì nút Uninstall mở trình
    soạn thảo, im lặng. `cmd.exe` không đi qua bảng đó. CHƯA ĐO ĐƯỢC trên một
    máy bị đè liên kết — đây là suy luận từ cơ chế, không phải từ số.
    """
    from tools.trinh_cai_dat import CMD_EXE, dang_ky_apps_features

    winreg = pytest.importorskip("winreg")
    duong = KHOA_UNINSTALL + "\\" + KHOA_APP
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, duong))
        pytest.skip("máy này đã cài AURA Thẻ thật — không đụng vào khoá của nó")
    except FileNotFoundError:
        pass
    cha_co_san = True
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, KHOA_UNINSTALL))
    except FileNotFoundError:
        cha_co_san = False

    assert CMD_EXE.is_file(), f"không có {CMD_EXE}"
    assert CMD_EXE.suffix.lower() == ".exe"

    go = tmp_path / "GO_CAI_DAT.bat"
    go.write_text("rem gia", encoding="utf-8")
    try:
        assert dang_ky_apps_features(tmp_path, go) is True
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, duong) as k:
            chuoi = winreg.QueryValueEx(k, "UninstallString")[0]
    finally:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, duong)
        except FileNotFoundError:
            pass
        if not cha_co_san:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KHOA_UNINSTALL)
            except OSError:
                pass

    # Windows tách chuỗi này thành (tệp để chạy) + (đối số): tệp là phần nằm
    # trong cặp nháy đầu tiên.
    assert chuoi.startswith('"'), chuoi
    tep = Path(chuoi[1:chuoi.index('"', 1)])
    assert tep.is_file(), f"thứ Windows sẽ chạy không có trên đĩa: {tep}"
    assert tep.suffix.lower() == ".exe", (
        f"UninstallString trỏ vào {tep.suffix!r}, không phải .exe — đúng cấu "
        "hình đã đo được là nút Uninstall trong Settings bấm không có tác dụng"
    )
    # `.bat` vẫn phải nằm trong chuỗi, ở vế đối số.
    assert str(go) in chuoi, chuoi
    assert " /c " in chuoi, "thiếu /c thì cmd mở cửa sổ tương tác rồi ngồi đó"


# -------------------------------------------------------- không đụng bài tập

def test_khong_dong_lenh_XOA_nao_cham_vao_thu_muc_bai_tap():
    """Bài tập chỉ được xuất hiện trong dòng ``echo``, không trong dòng xoá."""
    pham = []
    for d in bat_that().split("\n"):
        t = d.strip().lower()
        if t.startswith(("del ", "rmdir ", "rd ", "erase ")) and BAI.lower() in t:
            pham.append(d.strip())
    assert not pham, f"lệnh xoá chạm vào bài tập của người dùng: {pham}"


def test_co_noi_ro_bai_tap_duoc_giu():
    bat = bat_that()
    assert "GIỮ NGUYÊN" in bat and BAI in bat, (
        "phải nói rõ cái gì được giữ TRƯỚC khi hỏi Y/N — người dùng đang sắp "
        "bấm Y cho một câu hỏi có chữ 'Xoá'"
    )


# --------------------------------------------- vòng tròn thật trên registry

def test_ghi_doc_xoa_that_tren_registry(tmp_path):
    """Ca duy nhất đụng vào registry thật.

    Bỏ qua nếu máy ĐÃ cài AURA Thẻ — không được xoá mục của bản cài thật chỉ vì
    đang chạy test.
    """
    winreg = pytest.importorskip("winreg")
    from tools.trinh_cai_dat import TEN_HIEN, dang_ky_apps_features

    duong = KHOA_UNINSTALL + "\\" + KHOA_APP
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, duong))
        pytest.skip("máy này đã cài AURA Thẻ thật — không đụng vào khoá của nó")
    except FileNotFoundError:
        pass

    # Bậc cha có sẵn không? Nếu không thì test này tạo ra nó, và phải xoá đi.
    #
    # Bắt được 01/09/2026 bằng cách đếm: gieo lỗi đổi `KHOA_UNINSTALL` thành
    # `...\Uninstall\Apps` làm test dựng thêm một bậc `Apps`; xoá xong khoá con
    # thì `Apps` RỖNG ở lại trong registry thật của máy. Số mục dưới Uninstall
    # đi từ 18 lên 19 và không tự về. Một cửa canh dọn sạch registry của app
    # mà lại bẩn registry của người chạy nó thì tự mâu thuẫn.
    cha_co_san = True
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, KHOA_UNINSTALL))
    except FileNotFoundError:
        cha_co_san = False

    (tmp_path / "AURA_The.exe").write_bytes(b"x" * 2048)
    go = tmp_path / "GO_CAI_DAT.bat"
    go.write_text("rem gia", encoding="utf-8")
    try:
        assert dang_ky_apps_features(tmp_path, go) is True
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, duong) as k:
            n = winreg.QueryInfoKey(k)[1]
            gia_tri = dict(winreg.EnumValue(k, i)[:2] for i in range(n))
        # Dấu tiếng Việt phải còn nguyên. `WScript.Shell` ghi qua trang mã ANSI
        # nên "AURA Thẻ" thành "AURA Th?"; `winreg` ghi REG_SZ UTF-16 thì không.
        assert gia_tri["DisplayName"] == TEN_HIEN == "AURA Thẻ"
        assert gia_tri["InstallLocation"] == str(tmp_path)
        assert gia_tri["EstimatedSize"] == 2, "Settings đọc trường này theo KB"
        assert gia_tri["NoModify"] == 1 and gia_tri["NoRepair"] == 1
    finally:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, duong)
        except FileNotFoundError:
            pass
        if not cha_co_san:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KHOA_UNINSTALL)
            except OSError:
                pass
    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, duong)
