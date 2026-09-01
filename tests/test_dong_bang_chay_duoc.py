# -*- coding: utf-8 -*-
"""Bản đóng gói `.exe` bấm CHẠY THỬ phải chạy được mã của người học.

VÌ SAO CÓ TỆP NÀY. Ngày 31/08/2026, dựng bản `.exe` đầu tiên bằng PyInstaller
để gửi người thử. Suite 778 test XANH, app chạy từ mã nguồn tốt, `.exe` khởi
động in đủ banner. Rồi bấm CHẠY THỬ trên chính bản `.exe` ấy:

    AURA_The.exe: error: unrecognized arguments: -X utf8 ...\\run_script.py
    exit_code 2 · nhãn trên màn hình: "LỖI RUNTIME"

Nguyên nhân: `core/the_v1.py` chạy mã người học bằng `sys.executable`, mà trong
bản đóng băng `sys.executable` LÀ CHÍNH CÁI EXE. Nó tự gọi lại mình, argparse
thấy `-X utf8` và từ chối.

Không test nào cũ bắt được, vì cả 778 test đều chạy TỪ MÃ NGUỒN — nơi
`sys.frozen` không tồn tại và `sys.executable` đúng là `python.exe`. Đây đúng
họ với luật ở CLAUDE.md mục 4: *test xanh không có nghĩa là app dùng được* —
lần này thêm một tầng, "app chạy được" cũng không có nghĩa là "BẢN ĐÓNG GÓI
chạy được".

Và nhãn còn tệ hơn lỗi: người học đọc "LỖI RUNTIME" rồi đi sửa mã của mình,
trong khi mã của họ không có gì sai.
"""
from __future__ import annotations

import sys

import pytest

from core.the_v1 import CO_CHAY_TEP, lenh_chay_tep_python


def test_ban_thuong_van_goi_python_that():
    lenh = lenh_chay_tep_python(r"C:\tam\run_script.py")
    assert lenh[0] == sys.executable
    assert lenh[1:3] == ["-X", "utf8"], (
        "bản chạy từ mã nguồn phải giữ nguyên `-X utf8` — bỏ nó là mọi "
        "print() có dấu tiếng Việt lại nổ UnicodeEncodeError trên Windows"
    )
    assert lenh[-1].endswith("run_script.py")
    assert CO_CHAY_TEP not in lenh, (
        "bản chạy từ mã nguồn KHÔNG được đi qua cờ đóng vai thông dịch — "
        "mở thêm một đường chạy tệp tuỳ ý là tự thêm một cửa không ai canh"
    )


def test_ban_dong_bang_khong_tu_goi_lai_minh_bang_co_cua_cpython(monkeypatch):
    # Giả lập đúng thứ PyInstaller đặt vào: `sys.frozen = True`.
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    lenh = lenh_chay_tep_python(r"C:\tam\run_script.py")

    assert "-X" not in lenh and "utf8" not in lenh, (
        "đây là câu đã đo được trên bản .exe 31/08: bootloader của PyInstaller "
        "không nhận cờ của CPython, nên `-X utf8` rơi thẳng vào argparse của "
        "chính app và nó trả `unrecognized arguments`, exit code 2"
    )
    assert lenh[1] == CO_CHAY_TEP, (
        f"bản đóng băng phải gọi lại mình kèm {CO_CHAY_TEP!r} để đóng vai "
        "thông dịch, chứ không đưa thẳng đường dẫn tệp"
    )
    assert lenh[2].endswith("run_script.py")
    assert len(lenh) == 3


def test_nhanh_dong_vai_thong_dich_ton_tai_trong_entrypoint():
    """Cờ phải được NGHE ở `main()`, và phải nghe TRƯỚC argparse.

    Chỉ khẳng định `CO_CHAY_TEP` xuất hiện thì chưa đủ: nếu nhánh nằm SAU
    `parse_args()` thì argparse vẫn nổ trước khi tới nó — đúng lỗi gốc.
    """
    from pathlib import Path

    from core.paths import PROJECT_ROOT

    nguon = Path(PROJECT_ROOT, "interface", "the_app.py").read_text(encoding="utf-8")
    vi_tri_def_main = nguon.index("def main():")
    vi_tri_co = nguon.index(CO_CHAY_TEP, vi_tri_def_main)
    vi_tri_parse = nguon.index("parse_args()", vi_tri_def_main)

    assert vi_tri_co < vi_tri_parse, (
        "nhánh nghe cờ nằm SAU parse_args() — argparse sẽ từ chối trước khi "
        "tới nó, y hệt lỗi gốc mà tệp này sinh ra để chống"
    )
    assert 'getattr(sys, "frozen", False)' in nguon[vi_tri_def_main:vi_tri_co], (
        "nhánh phải bị khoá sau `sys.frozen`: bản chạy từ mã nguồn không được "
        "có đường chạy một tệp .py tuỳ ý"
    )


@pytest.mark.parametrize("so_doi_so", [1, 2])
def test_ban_dong_bang_thieu_doi_so_thi_khong_vao_nhanh_thong_dich(so_doi_so):
    """`--chay-tep-python` mà không kèm đường dẫn thì phải rơi xuống argparse.

    Không có khẳng định này thì `sys.argv[2]` ném IndexError và app chết câm.
    """
    from pathlib import Path

    from core.paths import PROJECT_ROOT

    nguon = Path(PROJECT_ROOT, "interface", "the_app.py").read_text(encoding="utf-8")
    assert "len(sys.argv) >= 3" in nguon, (
        "phải kiểm đủ 3 đối số trước khi đọc sys.argv[2]"
    )
    assert so_doi_so < 3


def test_ban_dong_bang_noi_ro_vi_sao_tim_loi_khong_chay(monkeypatch, tmp_path):
    """TÌM LỖI trong bản .exe phải nói bằng tiếng người, không dán stderr thô.

    31/08/2026, đo trên bản .exe: trạng thái trả về ĐÚNG (`khong_chay`, không
    giả vờ "không có test nào đỏ"), nhưng câu kèm theo là:

        Lỗi thu thập/nạp module (mã thoát 2): usage: AURA_The.exe [-h]
        [--host HOST] ... unrecognized arguments: -X utf8 -m pytest ...

    Người thử đọc xong vẫn không biết phải làm gì. Ba trạng thái tách đúng rồi
    thì bước tiếp theo là: trạng thái "KHÔNG ĐO ĐƯỢC" phải kèm LÝ DO dùng được.
    """
    import subprocess

    from core import trace_runtime

    class _KetQuaGia:
        returncode = 2
        stdout = ""
        stderr = (
            "usage: AURA_The.exe [-h] [--host HOST] [--port PORT]\n"
            "AURA_The.exe: error: unrecognized arguments: -X utf8 -m pytest x"
        )

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _KetQuaGia())

    do, loi_nap = trace_runtime._chay_pytest_tim_test_do_phan_loai(
        str(tmp_path / "test_x.py"), cwd=tmp_path)

    assert do == []
    assert len(loi_nap) == 1
    cau = loi_nap[0]
    assert "pytest" in cau and "mã nguồn" in cau, (
        f"câu phải nói RÕ nguyên nhân và lối ra, đang là: {cau!r}"
    )
    assert "CHẠY THỬ" in cau, (
        "phải nói luôn thứ VẪN dùng được, không thì người thử tưởng cả app hỏng"
    )
    assert "unrecognized arguments" not in cau, (
        "không được dán stderr thô của bootloader vào mặt người dùng"
    )


def test_ban_chay_tu_ma_nguon_van_giu_nguyen_stderr_ky_thuat(monkeypatch, tmp_path):
    """Ca đối chứng: khác đúng một biến (`sys.frozen`), câu phải khác hẳn.

    Không có ca này thì khẳng định trên có thể xanh vì câu mới ĐÈ LÊN CẢ HAI
    nhánh — và bản chạy từ mã nguồn mất luôn thông tin gỡ lỗi thật.
    """
    import subprocess

    from core import trace_runtime

    class _KetQuaGia:
        returncode = 2
        stdout = ""
        stderr = "ModuleNotFoundError: No module named 'khong_co_dau'"

    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _KetQuaGia())

    _, loi_nap = trace_runtime._chay_pytest_tim_test_do_phan_loai(
        str(tmp_path / "test_x.py"), cwd=tmp_path)

    assert len(loi_nap) == 1
    assert "khong_co_dau" in loi_nap[0], (
        "bản chạy từ mã nguồn phải giữ stderr thật — đó là thứ duy nhất chỉ ra "
        "module nào thiếu"
    )
    assert "Bản đóng gói" not in loi_nap[0]
