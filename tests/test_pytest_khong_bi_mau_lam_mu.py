# -*- coding: utf-8 -*-
"""Bộ dò vết đọc đầu ra pytest — mã màu ANSI KHÔNG được làm nó mù.

30/08/2026. Tiến trình app chạy dưới một môi trường có ``FORCE_COLOR=1`` (thừa
kế từ nơi khởi chạy). pytest thấy cờ đó thì tô màu KỂ CẢ khi ghi ra pipe, nên
dòng tóm tắt không còn bắt đầu bằng ``FAILED `` mà bằng ``\\x1b[31mFAILED\\x1b[0m``.
``line.startswith("FAILED ")`` trượt sạch, danh sách test đỏ rỗng, và
``/api/trace`` trả về **"Không có test nào bị đỏ trong tệp test này"**.

Ba kết quả khác nhau cho cùng một sự thật, đo cùng ngày cùng máy:

    pytest gọi thẳng             "1 failed"              đúng
    /api/trace                   "không có test đỏ"      SAI, trả lời trong 0,5s
    gọi hàm từ script riêng      tìm thấy 1 test đỏ      đúng

Thứ khác nhau giữa ba lần là **biến môi trường**, không phải mã của người dùng.
Và câu "Không có test nào bị đỏ" là một phán quyết tự tin về bài của họ, phát ra
trong khi phép đo đã hỏng — đúng thứ CLAUDE.md mục 4 cấm.

Cửa này ÉP ``FORCE_COLOR=1`` chứ không dựa vào môi trường máy đang chạy: nếu
không ép thì nó xanh trên máy này và đỏ trên máy khác, tức là một phép đo "xanh
theo lịch" như bộ test đồng hồ hôm 25/08.

GIỚI HẠN, nói luôn. Bản vá có hai lớp: cờ ``--color=no`` trên lệnh pytest, và
hàm ``_bo_mau`` bóc ANSI khi phân tích. Gieo thử đo được:

    gỡ riêng ``--color=no``   -> ĐỎ   (khẳng định tách lớp bên dưới bắt được)
    gỡ riêng ``_bo_mau``      -> xanh (lớp cờ đỡ hết)
    gỡ cả hai                 -> ĐỎ

Tức là **lớp dự phòng ``_bo_mau`` không được canh riêng bằng hành vi**, vì không
có cách nào bắt pytest tô màu trong khi ``--color=no`` vẫn còn. Nó chỉ được kiểm
như một hàm thuần ở cuối tệp. Đừng đọc "8 passed" thành "cả hai lớp đều đã chứng
minh".
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.trace_runtime as trace_runtime  # noqa: E402
from core.trace_runtime import (  # noqa: E402
    _bo_mau,
    _chay_pytest_lay_danh_sach_test,
    _chay_pytest_tim_test_do,
)

KHO = Path(__file__).resolve().parent.parent


@pytest.fixture()
def cap_nguon_test(tmp_path, monkeypatch):
    """Một cặp nguồn + test ĐỎ, đặt trong thư mục tạm riêng."""
    (tmp_path / "ma_thu.py").write_text(
        "def cong_don(day):\n"
        "    tong = 0\n"
        "    for phan_tu in day:\n"
        "        tong = tong + phan_tu\n"
        "    return tong\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ma_thu.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
        "from ma_thu import cong_don\n"
        "\n"
        "\n"
        "def test_co_y_do():\n"
        "    assert cong_don([1, 2, 3]) == 999\n",
        encoding="utf-8",
    )
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.mark.parametrize("bien", ["FORCE_COLOR", "PY_COLORS", "CLICOLOR_FORCE"])
def test_tim_duoc_test_do_du_moi_truong_ep_mau(cap_nguon_test, monkeypatch, bien):
    monkeypatch.setenv(bien, "1")
    ds = _chay_pytest_tim_test_do("tests/test_ma_thu.py", cwd=cap_nguon_test)
    assert ds == ["tests/test_ma_thu.py::test_co_y_do"], (
        f"{bien}=1 làm bộ phân tích mù: không thấy test đỏ nào"
    )


def test_thu_thap_duoc_danh_sach_test_du_moi_truong_ep_mau(cap_nguon_test, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    ds = _chay_pytest_lay_danh_sach_test("tests/test_ma_thu.py", cwd=cap_nguon_test)
    assert ds == ["tests/test_ma_thu.py::test_co_y_do"]


def test_khong_ep_mau_thi_van_phai_dung(cap_nguon_test, monkeypatch):
    """Chiều ngược lại: bản vá không được làm hỏng đường bình thường."""
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("PY_COLORS", raising=False)
    ds = _chay_pytest_tim_test_do("tests/test_ma_thu.py", cwd=cap_nguon_test)
    assert ds == ["tests/test_ma_thu.py::test_co_y_do"]


def test_tep_test_toan_xanh_thi_phai_ra_rong(tmp_path, monkeypatch):
    """Và không được ngược lại: xanh hết thì đừng bịa ra test đỏ."""
    monkeypatch.setenv("FORCE_COLOR", "1")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_xanh.py").write_text(
        "def test_xanh():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    assert _chay_pytest_tim_test_do("tests/test_xanh.py", cwd=tmp_path) == []


def test_co_moi_co_color_no_thoi_cung_phai_du(cap_nguon_test, monkeypatch):
    """Đo RIÊNG lớp cờ ``--color=no``, bằng cách tắt lớp bóc ANSI đi.

    Gieo thử cho thấy gỡ một lớp thôi thì cửa vẫn xanh vì lớp kia đỡ — đúng ý
    đồ, nhưng nghĩa là không khẳng định nào canh riêng cờ ``--color=no``. Mà
    ``core/lat_nguoc.py`` (tính năng "Định vị bằng test") CHỈ có lớp cờ ấy,
    không có ``_bo_mau``. Nên lớp cờ phải tự đứng được một mình.
    """
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setattr(trace_runtime, "_bo_mau", lambda chuoi: chuoi or "")
    ds = _chay_pytest_tim_test_do("tests/test_ma_thu.py", cwd=cap_nguon_test)
    assert ds == ["tests/test_ma_thu.py::test_co_y_do"], (
        "bỏ lớp bóc ANSI đi thì cờ --color=no không tự đỡ nổi"
    )


def test_bo_mau_giu_nguyen_chu_va_bo_dung_ma_mau():
    esc = "\x1b"
    assert _bo_mau(f"{esc}[31mFAILED{esc}[0m tests/a.py::b") == "FAILED tests/a.py::b"
    assert _bo_mau("FAILED tests/a.py::b") == "FAILED tests/a.py::b"
    # Không được ăn mất chữ tiếng Việt có dấu.
    assert _bo_mau(f"{esc}[1mTổng{esc}[0m: 6") == "Tổng: 6"
    assert _bo_mau("") == ""
    assert _bo_mau(None) == ""
