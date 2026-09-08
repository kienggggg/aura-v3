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


def test_TAI_LIEU_van_GIU_ba_dong_CHUA_CHAN_DUOC():
    """Chặn được ba thứ KHÔNG cho phép viết "đã cô lập".

    Bài này neo vào ĐẶC TẢ, không neo vào mã — chỗ dễ trôi là chỗ chữ. Cùng
    khuôn với bài canh `go` ở `tests/test_bo_dich_bash_chay_that.py`.
    """
    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    # HỎI THEO CẤU TRÚC, KHÔNG HỎI "CÓ CỤM CHỮ Ở ĐÂU ĐÓ KHÔNG".
    #
    # Bản đầu viết `cum in spec` và gieo xoá HÀNG cảnh báo vẫn xanh — vì cụm
    # "ra mạng" còn nằm ở bảng đo nền ("6. RA MẠNG ĐƯỢC — mã 200"). Cụm chữ
    # sống sót ở chỗ khác, còn lời hứa thì đã đổi. `x in y` lần thứ chín.
    #
    # Nay đòi cụm ấy nằm CÙNG MỘT DÒNG với "CHƯA CHẶN ĐƯỢC".
    dong_canh_bao = [d for d in spec.splitlines() if "CHƯA CHẶN ĐƯỢC" in d]
    gop = chr(10).join(dong_canh_bao)
    for cum in ("ghi tệp bằng đường dẫn tuyệt đối",
                "đọc tệp bất kỳ / liệt kê HOME",
                "ra mạng"):
        assert cum in gop, (
            f"đặc tả không còn dòng nào vừa nói {cum!r} vừa nói CHƯA CHẶN ĐƯỢC "
            f"— lời hứa đã trôi. Các dòng còn lại: {dong_canh_bao}")
    nguon = (PROJECT_ROOT / "core" / "hop_cat.py").read_text(encoding="utf-8")
    assert "CHƯA CHẶN ĐƯỢC" in nguon, "mã đã bỏ lời cảnh báo"
    assert "không" in nguon and "cô lập" in nguon, (
        "mất câu 'chặn được bốn thứ không cho phép viết đã cô lập'")
