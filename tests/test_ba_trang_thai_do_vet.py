# -*- coding: utf-8 -*-
"""Ba trạng thái của việc dò vết phải TÁCH RỜI, không được gộp thành hai.

30/08/2026. ``_chay_pytest_tim_test_do_phan_loai`` tính ra ``import_errors`` rất
cẩn thận — lỗi nạp module, ``INTERNALERROR``, mã thoát 2 — rồi
``_chay_pytest_tim_test_do`` **vứt nó đi ngay dòng sau**::

    ds_do, _ = _chay_pytest_tim_test_do_phan_loai(tep_test, cwd=cwd)

Hậu quả: tệp test không import nổi, sai cú pháp, pytest sập, hay quá giờ — cả
bốn đều ra ``[]``. Và cả **ba** nơi gọi (``interface/the_api.py``,
``core/lat_nguoc.py``, ``tools/_worker_e1_exec.py``) đều dịch ``[]`` thành cùng
một câu:

    "Không có test nào bị đỏ trong tệp test này"

Đó là một phán quyết về mã của người dùng, phát ra trong khi chưa đo được gì.
Người đọc sẽ tin là mã mình xanh. CLAUDE.md mục 4: *phép đo không chạy phải NÓI
LÀ KHÔNG CHẠY* — ba trạng thái, không được gộp thành hai.

Cùng ngày, cùng hàm này, đã có một lỗi họ hàng: ``FORCE_COLOR`` làm bộ phân tích
mù nên trả về ``[]``, và người dùng cũng đọc được đúng câu ấy. Sửa cái đó mới chỉ
bỏ MỘT nguyên nhân; câu nói dối vẫn còn cho mọi nguyên nhân khác. Đây là chỗ sửa
gốc.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.trace_runtime import chot_test_can_trace  # noqa: E402

NGUON = "def cong_don(day):\n    return sum(day)\n"


def _dung(tmp_path: Path, ma_test: str) -> Path:
    (tmp_path / "ma_t.py").write_text(NGUON, encoding="utf-8")
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests" / "test_ma_t.py").write_text(ma_test, encoding="utf-8")
    return tmp_path


def _chot(tmp_path: Path):
    return chot_test_can_trace(
        tep_nguon="ma_t.py", tep_test="tests/test_ma_t.py",
        cwd=tmp_path, max_steps=500)


DAU = ("import sys\nfrom pathlib import Path\n"
       "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
       "from ma_t import cong_don\n\n\n")


def test_do_duoc_va_khong_co_test_do_thi_KHONG_bao_khong_do_duoc(tmp_path):
    """Trạng thái 1: đo xong, tệp test xanh hết. Không được coi là hỏng."""
    thu = _dung(tmp_path, DAU + "def test_xanh():\n    assert cong_don([1, 2]) == 3\n")
    chot, _, ds = _chot(thu)
    assert chot is None
    assert ds == [], "tệp test xanh hết mà lại sinh ra kết quả 'không đo được'"
    shutil.rmtree(thu, ignore_errors=True)


def test_do_duoc_va_co_test_do_thi_chot_duoc(tmp_path):
    """Trạng thái 2: đo xong, có test đỏ."""
    thu = _dung(tmp_path, DAU + "def test_do():\n    assert cong_don([1, 2]) == 999\n")
    chot, _, ds = _chot(thu)
    assert chot == "tests/test_ma_t.py::test_do"
    assert ds and ds[0].trang_thai != "khong_chay"
    shutil.rmtree(thu, ignore_errors=True)


@pytest.mark.parametrize("nhan,ma_test,dau_hieu", [
    ("khong import noi",
     "from mot_module_khong_ton_tai import gi_do\n\n\ndef test_x():\n    assert gi_do() == 1\n",
     "ModuleNotFoundError"),
    ("sai cu phap",
     "def test_x(:\n    assert 1 == 1\n",
     "test_ma_t.py"),
])
def test_chua_do_duoc_thi_phai_noi_la_chua_do_duoc(tmp_path, nhan, ma_test, dau_hieu):
    """Trạng thái 3 — chỗ từng bị gộp mất.

    Phải trả về một kết quả ``khong_chay`` MANG THEO LÝ DO. Không được trả về
    danh sách rỗng, vì rỗng sẽ bị ba nơi gọi dịch thành "không có test nào đỏ".
    """
    thu = _dung(tmp_path, ma_test)
    chot, _, ds = _chot(thu)
    assert chot is None
    assert ds, f"[{nhan}] trả về rỗng — sẽ bị đọc nhầm thành 'không có test nào đỏ'"
    assert ds[0].trang_thai == "khong_chay", f"[{nhan}] {ds[0].trang_thai}"
    assert "KHÔNG ĐO ĐƯỢC" in ds[0].thong_diep
    assert dau_hieu in ds[0].thong_diep, (
        f"[{nhan}] thông điệp không nói ra hỏng ở đâu: {ds[0].thong_diep!r}"
    )
    shutil.rmtree(thu, ignore_errors=True)


def test_ba_trang_thai_cho_ba_cau_khac_nhau(tmp_path):
    """Ba tình huống KHÔNG được cho ra cùng một câu — đó chính là lỗi gốc."""
    cau = []
    for ma_test in [
        DAU + "def test_xanh():\n    assert cong_don([1, 2]) == 3\n",
        DAU + "def test_do():\n    assert cong_don([1, 2]) == 999\n",
        "from khong_ton_tai import x\n\n\ndef test_x():\n    assert x() == 1\n",
    ]:
        thu = tmp_path / f"ca_{len(cau)}"
        thu.mkdir()
        _dung(thu, ma_test)
        chot, _, ds = _chot(thu)
        cau.append((chot is not None, ds[0].trang_thai if ds else "(rỗng)"))
    assert len(set(cau)) == 3, f"ba tình huống chỉ cho {len(set(cau))} kết quả khác nhau: {cau}"
