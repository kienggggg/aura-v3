# -*- coding: utf-8 -*-
"""Hộp cát cho `/api/polyglot/run` — CHẶN ĐƯỢC BA THỨ, KHÔNG CHẶN ĐƯỢC BỐN.

Đăng ký ở `KY_LUAT_THUC_THI.md` (08/09/2026), chép TAY xuống đây.

Đây là **lời hứa an toàn**, nên `CLAUDE.md` mục 7 luật 3 áp dụng nguyên văn:
*kiểm được thì kiểm; kiểm không được thì viết "CHƯA chặn được", đừng viết "đã
chặn".* Nửa số bài trong tệp này canh đúng chiều ấy — chúng khẳng định rằng
**vẫn còn lỗ**, và sẽ đỏ nếu ai đó viết một lời hứa quá tay.

ĐO NỀN → SAU KHI VÁ, 8 đơn chạy qua chính `chay_ma_da_ngon_ngu`:

    đơn                              nền             sau          phán quyết
    1. cwd                           D:/AURA_v3      C:/../Temp   đổi mặc định
    2. ghi tệp đường tuyệt đối       ĐƯỢC            VẪN ĐƯỢC     CHƯA CHẶN
    3. đọc tệp bất kỳ trong kho      mở              25.583 byte  CHƯA CHẶN
    4. liệt kê HOME (đường gõ cứng)  87 mục          87 mục       CHƯA CHẶN
    5. biến môi trường               87, có bí mật   9, sạch      CHẶN ĐƯỢC
    6. ra mạng                       ĐƯỢC            VẪN ĐƯỢC     CHƯA CHẶN
    7. cấp phát 300 MB               ĐƯỢC            BỊ CHẶN      CHẶN ĐƯỢC
    8. tiến trình mồ côi             SỐNG SÓT        KHÔNG        CHẶN ĐƯỢC

MỤC 4 SUÝT BỊ CHẤM NHẦM LÀ ĐÃ CHẶN. Lượt đo đầu sau khi vá cho nó FAIL, và đọc
ra như "hệ tệp đã kín". Thật ra `os.path.expanduser('~')` cần `USERPROFILE` —
biến vừa bị lọc — nên nó hỏng vì THIẾU BIẾN, không phải vì bị chặn. Đường dẫn
gõ cứng vẫn đọc được 87 mục. Một dương tính giả trong một lời hứa an toàn là
thứ nguy hiểm nhất tệp này canh.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import pytest

from core import hop_cat
from core.paths import PROJECT_ROOT
from core.polyglot import chay_ma_da_ngon_ngu

# Chép TAY từ đặc tả. `256` là con số CHỌN — cùng con số kế hoạch 19/08 đã hứa
# mà không giao được (`import resource`, API Unix, Windows không có).
DAC_TA_RAM_MB = 256
DAC_TA_SO_BIEN_TOI_DA = 15

# Chép TAY từ đặc tả khe đua (08/09). `0x4` là `CREATE_SUSPENDED` của Windows.
#
# `3000` là số SUY RA, và bản đầu tôi gõ `500` rồi ca đối chứng đỏ ngay lượt
# đầu. Đo 30 lượt: con Python KHÔNG treo mất tới **837,9 ms** mới ghi được mốc
# khi máy rảnh (cache lạnh, CPU xung thấp) — nhanh hơn 28 lần khi máy đang bận
# vì lúc ấy DLL đã nóng. Ngưỡng = lớn nhất đo được × 3,6.
DAC_TA_CREATE_SUSPENDED = 0x00000004
DAC_TA_CHO_TREO_MS = 3000

la_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="KHÔNG ĐO ĐƯỢC: Job Object chỉ có trên Windows")


def _chay(ma: str, giay: float = 15.0):
    return chay_ma_da_ngon_ngu(ma, "python", giay)


def test_hang_so_khop_DAC_TA():
    assert hop_cat.RAM_MB == DAC_TA_RAM_MB


def test_MOI_ket_qua_deu_MANG_truong_hop_cat():
    """Không có trường này thì "có hộp cát" là một câu chữ không kiểm được.

    Ba trạng thái cho chính hộp cát, không gộp: `job` (đủ) · `khong: <lý do>`.
    Người đọc kết quả phải biết lượt ấy **thật sự** được bọc hay không — chứ
    không suy ra từ việc mã có tệp `hop_cat.py`.
    """
    kq = _chay("print('xin chao')")
    assert "hop_cat" in kq, kq
    assert kq["hop_cat"] == "job" or kq["hop_cat"].startswith("khong: "), kq


@la_windows
def test_BIEN_MOI_TRUONG_bi_loc_sach():
    """Khoá API sống trong biến môi trường — `CLAUDE.md` mục 2.

    Nền: 87 biến, có tên nghi là bí mật (`CLAUDE_*`). Sau: 9 biến, không cái
    nào có tên nghi bí mật.
    """
    kq = _chay(
        "import os\n"
        "nghi = [x for x in os.environ if any(t in x.upper() for t in "
        "('KEY','TOKEN','SECRET','PASS'))]\n"
        "print(len(os.environ), nghi)\n")
    assert kq["status"] == "PASS", kq
    so, nghi = kq["stdout"].strip().split(" ", 1)
    assert int(so) <= DAC_TA_SO_BIEN_TOI_DA, f"{so} biến, nền là 87"
    assert nghi.strip() == "[]", f"còn biến tên nghi bí mật: {nghi}"


@la_windows
def test_TRAN_RAM_chan_that():
    """Nền: cấp phát 300 MB ĐƯỢC. Sau: bị chặn bởi trần 256 MB."""
    kq = _chay("x = bytearray(300*1024*1024)\nprint('cap phat duoc')")
    assert kq["status"] == "FAIL", f"cấp phát 300 MB vẫn qua được: {kq}"
    assert "cap phat duoc" not in (kq["stdout"] or "")


@la_windows
def test_TIEN_TRINH_MO_COI_khong_song_sot(tmp_path):
    """Chỗ nặng nhất, và chưa ai ghi trước 08/09.

    `subprocess.run(timeout=)` chỉ giết CON TRỰC TIẾP. Một dòng `Popen` là cháu
    sống tiếp — tức bảo vệ duy nhất đang có bị vượt bằng một dòng. Đo nền: cháu
    **SỐNG SÓT**. `KILL_ON_JOB_CLOSE` giết cả cây.
    """
    moc = tmp_path / "chau_song_sot.txt"
    chau = tmp_path / "chau.py"
    # TÁCH CHÁU RA TỆP RIÊNG. Nhét đường dẫn Windows vào chuỗi lồng thì cháu
    # chết vì SyntaxError và kết quả đọc ra như "job giết được cháu" — trong
    # khi cháu CHƯA TỪNG SINH RA. Nguyên mẫu 08/09 dính đúng thế.
    chau.write_text("import time, pathlib, sys\n"
                    "time.sleep(6)\n"
                    "pathlib.Path(sys.argv[1]).write_text('song sot')\n",
                    encoding="utf-8")
    ma = (f"import subprocess, sys, time\n"
          f"subprocess.Popen([sys.executable, {str(chau)!r}, {str(moc)!r}])\n"
          f"print('DA SINH chau', flush=True)\n"
          f"time.sleep(30)\n")
    _chay(ma, 3.0)
    time.sleep(9)
    assert not moc.is_file(), (
        "cháu SỐNG SÓT qua timeout — job không giết được cả cây")


@la_windows
def test_cwd_KHONG_phai_goc_kho():
    """Nền: `cwd` là `D:/AURA_v3`. Đây chỉ ĐỔI MẶC ĐỊNH, không phải chặn —
    xem `test_VAN_CHUA_chan_duoc_ghi_tep`."""
    kq = _chay("import os; print(os.getcwd())")
    assert kq["status"] == "PASS", kq
    assert Path(kq["stdout"].strip()).resolve() != PROJECT_ROOT.resolve()


# ---------------------------------------------------------------------------
# BỐN BÀI DƯỚI KHẲNG ĐỊNH RẰNG VẪN CÒN LỖ.
#
# Chúng đỏ khi ai đó vá thêm — và đó là lúc phải sửa TÀI LIỆU cùng lúc, chứ
# không phải xoá bài. Không có chúng thì lời "CHƯA chặn được" trong tài liệu
# trôi dần thành "đã chặn" mà không ai đo lại.
# ---------------------------------------------------------------------------

@la_windows
def test_VAN_CHUA_chan_duoc_GHI_TEP_duong_tuyet_doi(tmp_path):
    ra = tmp_path / "ghi_duoc.txt"
    kq = _chay(f"open({str(ra)!r}, 'w').write('x')\nprint('DA GHI')")
    assert kq["status"] == "PASS" and ra.is_file(), (
        "ghi tệp bằng đường tuyệt đối đã bị chặn — MỪNG, nhưng phải sửa "
        "`KY_LUAT_THUC_THI.md` và `core/hop_cat.py` cùng lúc")


@la_windows
def test_VAN_CHUA_chan_duoc_DOC_TEP_bat_ky():
    kq = _chay("import pathlib\n"
               "print(len(pathlib.Path(r'D:/AURA_v3/CLAUDE.md').read_bytes()))")
    assert kq["status"] == "PASS" and int(kq["stdout"].strip()) > 1000, (
        "đọc tệp trong kho đã bị chặn — sửa tài liệu cùng lúc")


@la_windows
def test_VAN_CHUA_chan_duoc_RA_MANG():
    kq = _chay("import urllib.request\n"
               "r = urllib.request.urlopen('http://127.0.0.1:11434/api/tags',"
               " timeout=5)\n"
               "print(r.status)")
    if kq["status"] != "PASS":
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: Ollama không chạy — {kq['stderr'][:60]}")
    assert kq["stdout"].strip() == "200", (
        "ra mạng đã bị chặn — sửa tài liệu cùng lúc")


def _khoi_chot(ten: str) -> str:
    """Đọc đúng khối nằm giữa `<!-- CHOT:ten -->` và `<!-- /CHOT:ten -->`.

    VÌ SAO PHẢI CÓ NEO CÓ TÊN — `x in y` lần thứ MƯỜI và MƯỜI MỘT (08/09/2026).

    Hai bản trước của các bài dưới hỏi *"cụm chữ có ở đâu đó trong tệp 100 KB
    không"*. Gieo xoá đúng dòng lời hứa mà cửa vẫn xanh, vì **chính tôi vừa
    thêm một bảng ghi phép đo** cũng chứa cụm ấy:

        gieo xoá hàng "ra mạng | VẪN ĐƯỢC | CHƯA CHẶN ĐƯỢC"
          -> vẫn xanh, vì bảng ĐO SAU KHI VÁ có dòng
             "6. ra mạng ... CHƯA CHẶN ĐƯỢC"
        gieo xoá đoạn ghi AppContainer
          -> vẫn xanh, vì chữ "AppContainer" còn ở mục hộp cát

    Sửa cả LOẠI BỆNH, không sửa một ca: neo có tên chỉ đúng MỘT chỗ, và bảng
    ghi phép đo nằm ngoài neo nên không cứu được lời hứa nữa.
    """
    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(rf"<!-- CHOT:{ten} -->(.*?)<!-- /CHOT:{ten} -->", spec, re.S)
    assert m, f"mất neo CHOT:{ten} trong đặc tả"
    return m.group(1)


def test_TAI_LIEU_van_GIU_ba_dong_CHUA_CHAN_DUOC():
    """Chặn được ba thứ KHÔNG cho phép viết "đã cô lập"."""
    khoi = _khoi_chot("hop-cat-con-lo")
    for cum in ("ghi tệp bằng đường dẫn tuyệt đối",
                "đọc tệp bất kỳ / liệt kê HOME",
                "ra mạng"):
        assert cum in khoi and "CHƯA CHẶN ĐƯỢC" in khoi, (
            f"khối CHOT:hop-cat-con-lo không còn nói {cum!r} là CHƯA CHẶN "
            f"ĐƯỢC — khối đang là: {khoi!r}")
    assert khoi.count("CHƯA CHẶN ĐƯỢC") == 3, (
        f"khối phải có đúng 3 dòng CHƯA CHẶN ĐƯỢC, thấy "
        f"{khoi.count('CHƯA CHẶN ĐƯỢC')} — khối đang là: {khoi!r}")
    nguon = (PROJECT_ROOT / "core" / "hop_cat.py").read_text(encoding="utf-8")
    assert "CHƯA CHẶN ĐƯỢC" in nguon, "mã đã bỏ lời cảnh báo"
    assert "cô lập" in nguon, (
        "mất câu 'chặn được bốn thứ không cho phép viết đã cô lập'")


def test_LOI_HUA_no_network_van_duoc_danh_dau_CHUA_GIAO():
    """`no-network` là khoá số 1 trong "7 Khoá Chống Gian Lận" của đặc tả.

    Nó **chưa giao**, và đã thử thật ngày 08/09:

        không Docker · không WSL · KHÔNG Administrator  -> tường lửa loại
        AppContainer: profile OK, SID OK
          + icacls temp/venv        -> mã thoát 106
          + icacls base_prefix      -> mã thoát 1
          + cho cháu ghi traceback  -> KHÔNG ghi nổi cả tệp lỗi

    Cháu hỏng **trước khi chạy dòng Python nào**, nên cấp thêm quyền là đoán
    chứ không phải đo.
    """
    khoi = _khoi_chot("no-network")
    assert "vẫn là một lời hứa chưa giao" in khoi, (
        "dòng no-network đã mất nhãn CHƯA GIAO — nếu thật sự giao được thì "
        "phải có phép đo cho thấy `urlopen` bị chặn, và sửa cả "
        "`test_VAN_CHUA_chan_duoc_RA_MANG` cùng lúc")
    # Lý do THẤT BẠI phải ở lại — không có nó thì lần sau thử lại từ đầu.
    for cum in ("AppContainer", "Administrator", "không khởi động nổi"):
        assert cum in khoi, (
            f"khối no-network mất phần ghi {cum!r} — khối đang là: {khoi!r}")


# ---------------------------------------------------------------------------
# KHE ĐUA `Popen` → job (08/09/2026)
# ---------------------------------------------------------------------------


def _con_ghi_ngay(d: Path) -> tuple[list, Path]:
    """Tiến trình con ghi mốc ở dòng ĐẦU TIÊN, không làm gì khác."""
    moc = d / "moc.txt"
    kb = d / "con.py"
    kb.write_text("import sys, pathlib\n"
                  "pathlib.Path(sys.argv[1]).write_text('DA CHAY')\n",
                  encoding="utf-8")
    return [sys.executable, str(kb), str(moc)], moc


def test_hang_so_khe_dua_khop_DAC_TA():
    assert hop_cat.CREATE_SUSPENDED == DAC_TA_CREATE_SUSPENDED


@la_windows
def test_KHE_DUA_con_sinh_ra_o_trang_thai_TREO(tmp_path):
    """Con sinh với `CREATE_SUSPENDED` phải CHƯA chạy lệnh nào sau 500 ms.

    ĐÂY LÀ NỬA ĐẦU CỦA MỘT CẶP. Một mình nó chứng minh được rất ít: một tiến
    trình con hỏng ngay từ đầu cũng "chưa ghi gì". Nên bài này còn phải chứng
    minh con VẪN SỐNG — thả ra thì nó ghi. Và bài kế bên là ca đối chứng.

    VÌ SAO CÓ CẢ CHUYỆN NÀY: khe đua đo được 0,077–0,232 ms (52 lượt, cháu
    sống sót 0/12). Không ai bắn trúng — nhưng khe hẹp là nhờ `CreateProcess`
    của Python tốn 17–24 ms, tức nhờ ĐỐI PHƯƠNG CHẬM, không nhờ mã của mình.
    """
    import subprocess

    cmd, moc = _con_ghi_ngay(tmp_path)
    p = subprocess.Popen(cmd, cwd=str(tmp_path),
                         env=hop_cat.moi_truong_sach(),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=hop_cat.CREATE_SUSPENDED)
    try:
        time.sleep(DAC_TA_CHO_TREO_MS / 1000)
        assert not moc.is_file(), (
            "con ĐÃ CHẠY dù sinh ra với CREATE_SUSPENDED — khe đua vẫn hở")

        # Nửa sau: nó treo, KHÔNG phải nó chết. Thiếu đoạn này thì bài trên
        # xanh cả khi tiến trình con không bao giờ khởi động nổi.
        da_tha, vi_sao = hop_cat.tha_tien_trinh(p.pid)
        assert da_tha, f"không thả được: {vi_sao}"
        for _ in range(100):
            if moc.is_file():
                break
            time.sleep(0.05)
        assert moc.is_file(), (
            "thả rồi mà con vẫn không ghi — nó chết chứ không phải treo, "
            "và bài trên vừa xanh vì lý do sai")
    finally:
        try:
            p.kill()
        except OSError:
            pass


@la_windows
def test_KHE_DUA_doi_chung_khong_treo_thi_con_GHI_DUOC_ngay(tmp_path):
    """CA ĐỐI CHỨNG — khác đúng một biến: bỏ `CREATE_SUSPENDED`.

    Không có bài này thì bài trên là một phép đo rỗng: mọi lý do khiến con
    không ghi được đều đọc ra thành "treo thành công".
    """
    import subprocess

    cmd, moc = _con_ghi_ngay(tmp_path)
    p = subprocess.Popen(cmd, cwd=str(tmp_path),
                         env=hop_cat.moi_truong_sach(),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # Chờ CÓ MỐC thì dừng ngay, không ngủ trọn khoảng: bài này chỉ cần
        # chứng minh con ghi được trong khoảng ấy, không cần đo nó nhanh cỡ nào.
        han = time.monotonic() + DAC_TA_CHO_TREO_MS / 1000
        while not moc.is_file() and time.monotonic() < han:
            time.sleep(0.02)
        assert moc.is_file(), (
            "ĐỐI CHỨNG HỎNG: con không treo mà cũng không ghi nổi trong "
            f"{DAC_TA_CHO_TREO_MS} ms — bài treo bên cạnh đang đo cái khác")
    finally:
        try:
            p.kill()
        except OSError:
            pass


@la_windows
def test_tha_tien_trinh_FAIL_CLOSED_khi_khong_co_luong_nao():
    """Không tìm thấy luồng nào thì phải trả `False` + lý do, không trả True.

    Nhánh fail-closed trong `_chay_co_hop_cat` chỉ chạy khi hàm này trả
    `False`. Một hàm luôn trả `True` sẽ làm nhánh ấy thành mã chết mà mọi bài
    khác vẫn xanh.
    """
    da_tha, vi_sao = hop_cat.tha_tien_trinh(0x7FFFFFF0)
    assert da_tha is False, "pid không tồn tại mà vẫn báo thả được"
    assert vi_sao, "trả False mà không nói lý do"


@la_windows
def test_HOP_CAT_van_chay_duoc_ma_that_sau_khi_them_treo(tmp_path):
    """Sinh treo rồi thả — mã người ngoài gửi vẫn phải chạy ra kết quả đúng.

    Bài dễ quên nhất: vá xong cái khe mà quên thả thì mọi lượt chạy đều hết
    `timeout` rồi mới về, và đọc ra như "mã chạy lâu".
    """
    kq = _chay("print(6 * 7)")
    assert kq["status"] == "PASS", f"{kq['stderr'][:200]}"
    assert kq["stdout"].strip() == "42"
    assert kq["hop_cat"] == "job", f"hộp cát không dựng được: {kq['hop_cat']}"
    assert kq["latency_ms"] < 10000, (
        f"chạy mất {kq['latency_ms']} ms — nghi là con bị treo rồi đợi timeout")


def test_DAC_TA_khe_dua_van_o_lai_tai_lieu():
    """Các con số của khe đua phải ở lại, không thì luật thành lời răn suông.

    Bản đầu bài này đòi chuỗi `"500"` — và nó **vẫn xanh sau khi ngưỡng đổi
    thành 3000**, vì `500` còn nằm trong chính câu kể lại con số đã bị bỏ.
    Một cửa bắt trúng chữ trong đoạn kể chuyện thì không canh gì cả; nay đòi
    đúng những số ĐANG CÓ HIỆU LỰC, và đòi chúng khớp với hằng số chép tay.
    """
    khoi = _khoi_chot("khe-dua")
    for cum in ("0,077", "0,232", "0,095",     # bề rộng khe, 52 lượt
                "837,9",                        # con khoẻ chậm nhất — gốc ngưỡng
                "3,6",                          # biên
                "CREATE_SUSPENDED",
                str(DAC_TA_CHO_TREO_MS)):       # 3000, không gõ rời
        assert cum in khoi, f"khối khe-dua mất {cum!r} — khối: {khoi[:400]!r}"


def _dem_treo(pid: int) -> int:
    """Đếm số lần một tiến trình đang bị treo, KHÔNG làm nó đổi trạng thái.

    `SuspendThread` trả về **số đếm treo trước đó**, `ResumeThread` gỡ lại đúng
    một nấc. Cặp ấy đọc được trạng thái mà không để lại dấu vết: con đang treo
    (đếm 1) thì đọc xong vẫn treo; con đang chạy (đếm 0) thì đọc xong vẫn chạy.
    """
    import ctypes
    import ctypes.wintypes as wt

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    snap = k32.CreateToolhelp32Snapshot(hop_cat._TH32CS_SNAPTHREAD, 0)
    if snap == -1 or not snap:
        return -1
    try:
        te = hop_cat._THREADENTRY32()
        te.dwSize = ctypes.sizeof(hop_cat._THREADENTRY32)
        if not k32.Thread32First(wt.HANDLE(snap), ctypes.byref(te)):
            return -1
        while True:
            if te.th32OwnerProcessID == pid:
                h = k32.OpenThread(hop_cat._THREAD_SUSPEND_RESUME, False,
                                   te.th32ThreadID)
                if h:
                    truoc = k32.SuspendThread(wt.HANDLE(h))
                    k32.ResumeThread(wt.HANDLE(h))
                    k32.CloseHandle(wt.HANDLE(h))
                    return truoc
            if not k32.Thread32Next(wt.HANDLE(snap), ctypes.byref(te)):
                return -1
    finally:
        k32.CloseHandle(wt.HANDLE(snap))


@la_windows
def test_DUONG_THAT_sinh_con_o_trang_thai_TREO(monkeypatch):
    """Đo đường THẬT, không đo một `Popen` do bài test tự dựng.

    VÌ SAO PHẢI CÓ BÀI NÀY: hai bài treo ở trên chứng minh `CREATE_SUSPENDED`
    và `tha_tien_trinh` chạy đúng — nhưng chúng tự gọi `Popen` của riêng mình.
    Chúng vẫn xanh **kể cả khi `_chay_co_hop_cat` không hề dùng cờ ấy**. Đúng
    bài *"một khả năng có sẵn mà không ai gọi thì bằng không"* (`SO_BENH_AN`).

    Cách bắt: `_chay_co_hop_cat` gọi `gan_vao_job` ở đúng khoảnh khắc cần đo,
    và nó `import` bên trong hàm nên vá vào `hop_cat` là bắt được. Đọc số đếm
    treo NGAY tại khoảnh khắc ấy.
    """
    that = hop_cat.gan_vao_job
    ghi = {}

    def do_roi_goi(h_job, pid):
        ghi["dem_treo"] = _dem_treo(pid)
        return that(h_job, pid)

    monkeypatch.setattr(hop_cat, "gan_vao_job", do_roi_goi)
    kq = _chay("print('xong')")

    assert "dem_treo" in ghi, "`gan_vao_job` không được gọi — hộp cát chưa dựng"
    assert ghi["dem_treo"] >= 1, (
        f"lúc gắn vào job, con KHÔNG treo (đếm treo = {ghi['dem_treo']}) — "
        f"`_chay_co_hop_cat` chưa dùng CREATE_SUSPENDED, khe đua vẫn hở")
    # Và thả xong nó vẫn phải chạy ra kết quả — nửa kia của cặp.
    assert kq["status"] == "PASS" and kq["stdout"].strip() == "xong", kq


@la_windows
def test_FAIL_CLOSED_tha_hong_thi_BAO_LOI_chu_khong_treo(monkeypatch):
    """Thả luồng hỏng thì phải giết con và nói ra — không được đợi hết giờ.

    VÌ SAO CÓ BÀI NÀY: gieo "bỏ nhánh fail-closed" ở `_chay_co_hop_cat`
    **vẫn xanh** — 8 phép gieo khác đỏ, riêng phép này mù. Không phải phép
    gieo trượt: nhánh ấy chỉ chạy khi `tha_tien_trinh` trả `False`, nên gieo
    MỘT biến không bao giờ chạm tới nó. Phải gieo đúng điều kiện vào.

    Hỏng im lặng ở đây đọc ra như "mã người dùng chạy lâu": con nằm treo, và
    `communicate` đợi đủ `timeout` rồi mới về.
    """
    monkeypatch.setattr(hop_cat, "tha_tien_trinh",
                        lambda pid: (False, "gieo: thả hỏng"))
    t0 = time.monotonic()
    kq = _chay("print('khong bao gio in ra')", 6.0)
    mat = time.monotonic() - t0

    assert mat < 3.0, (
        f"mất {mat:.1f}s — con bị bỏ treo rồi đợi hết giờ, tức nhánh "
        f"fail-closed không chạy")
    assert kq["status"] != "PASS", kq
    assert kq["hop_cat"].startswith("khong: "), (
        f"thả hỏng mà `hop_cat` vẫn báo {kq['hop_cat']!r}")
    assert "thả hỏng" in kq["hop_cat"], (
        f"nuốt mất lý do thật: {kq['hop_cat']!r}")
    assert "khong bao gio in ra" not in (kq["stdout"] or ""), (
        "con vẫn chạy được dù đã báo là không thả nổi")
