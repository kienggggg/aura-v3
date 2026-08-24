# -*- coding: utf-8 -*-
"""test_trace_runtime.py — Kiểm thử nghiêm ngặt module trace_runtime (Mạch Nước Ngầm Động).

Kiểm chứng các tiêu chuẩn kỹ thuật:
1. Khả năng trace 1 test đơn lẻ (trạng thái trace_du, bắt đúng biến và giá trị).
2. Xử lý chạm trần max_steps (trạng thái trace_cut: 'KHÔNG ĐO ĐƯỢC: Chạm trần ở bước N', Fail-closed).
3. Xử lý lỗi tệp/môi trường (trạng thái khong_chay).
4. Luật chọn test tất định 3 tầng khi có test đỏ.
5. Đối chiếu thời gian thực thi (hoàn tất < 5s cho 1 test).
6. Kiểm chứng trích xuất vết trên 4 đề lỗi đơn trong sổ E1 (lat_nguoc.json).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import pytest

from core.trace_runtime import (
    TraceEvent,
    TraceResult,
    chay_trace_mot_test,
    chot_test_can_trace,
    tao_script_tracer,
)
from experiments.evidence_sprint.dung_de_loi import dot_bien

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_trace_don_dong_ho_thanh_cong():
    """Test trace thành công 1 test của core/dong_ho.py, ra đúng trace_du và số bước thực tế < 50."""
    res = chay_trace_mot_test(
        tep_nguon="core/dong_ho.py",
        node_id_test="tests/test_dong_ho.py::test_cau_gio_noi_dung_thu_va_ngay",
        max_steps=5000,
    )
    assert res.trang_thai == "trace_du"
    assert res.tong_buoc > 0
    assert res.tong_buoc < 50, f"Số bước của dong_ho.py phải nhỏ, nhận được {res.tong_buoc}"
    assert res.thoi_gian_giay < 5.0, f"Thời gian trace phải < 5s, nhận được {res.thoi_gian_giay}s"
    assert len(res.cac_su_kien) > 0

    ten_cac_bien = {ev["ten_bien"] for ev in res.cac_su_kien}
    assert ("hien_tai" in ten_cac_bien or "thu" in ten_cac_bien or "<tra_ve>" in ten_cac_bien)


def test_trace_cham_tran_fail_closed():
    """Test khi chạm trần max_steps (đặt = 2), phải trả về trace_cut kèm thông điệp chuẩn xác."""
    res = chay_trace_mot_test(
        tep_nguon="core/dong_ho.py",
        node_id_test="tests/test_dong_ho.py::test_cau_gio_noi_dung_thu_va_ngay",
        max_steps=2,
    )
    assert res.trang_thai == "trace_cut"
    assert "KHÔNG ĐO ĐƯỢC: Chạm trần ở bước 2" in res.thong_diep
    assert res.tong_buoc >= 2


def test_trace_tep_khong_ton_tai():
    """Test khi tệp nguồn không tồn tại, phải trả về khong_chay Fail-Closed."""
    res = chay_trace_mot_test(
        tep_nguon="core/khong_he_co_tep_nay_12345.py",
        node_id_test="tests/test_dong_ho.py::test_cau_gio_noi_dung_thu_va_ngay",
    )
    assert res.trang_thai == "khong_chay"
    assert "KHÔNG ĐO ĐƯỢC" in res.thong_diep


def test_tao_script_tracer_chuan_xac():
    """Kiểm tra mã script sinh ra chứa đầy đủ các hook sys.settrace và trần bước."""
    script = tao_script_tracer(
        tep_nguon_abs=r"D:\AURA_v3\core\dong_ho.py",
        node_id_test="tests/test_dong_ho.py::test_cau_gio",
        dong_kiem_tra=25,
        max_steps=5000,
    )
    assert "TracePlugin" in script
    assert "MAX_STEPS = 5000" in script
    assert "DONG_KIEM_TRA = 25" in script
    assert "===JSON_START===" in script


def test_luat_chon_test_tat_dinh_tren_de_loi_don_dong_ho(tmp_path: Path):
    """Kiểm tra luật chọn test tất định khi gieo 1 lỗi đơn vào core/dong_ho.py (Tầng 1 thực thi thật)."""
    # Sao chép kho tối thiểu sang tmp_path
    for d in ("core", "tests"):
        shutil.copytree(PROJECT_ROOT / d, tmp_path / d)
    (tmp_path / "pytest.ini").write_text("[pytest]\npythonpath = .\n", encoding="utf-8")

    # ĐÓNG ĐINH ĐỒNG HỒ — nếu không, phép đo này XANH 3/7 NGÀY TRONG TUẦN.
    #
    # Đo 25/08/2026: lỗi gieo ở đây là `now or ...` -> `now and ...`, làm
    # `cau_gio()` bỏ qua mốc thời gian test truyền vào mà dùng `datetime.now()`
    # THẬT. Ba test tham số hoá trong test_dong_ho.py so thứ với 10/08 (Thứ
    # Hai), 15/08 (Thứ Bảy), 16/08 (Chủ Nhật) — chạy đúng một trong ba thứ ấy
    # thì một test TÌNH CỜ xanh, số test đỏ tụt từ 6 xuống 5.
    #
    #     Thứ Hai / Thứ Bảy / Chủ Nhật  -> 5 đỏ -> so_test_khac = 4
    #     bốn thứ còn lại                -> 6 đỏ -> so_test_khac = 5
    #
    # Hôm 24/08 (Thứ Hai) suite xanh 624; hôm sau 25/08 (Thứ Ba) đỏ, không ai
    # đụng vào mã. Đúng bệnh mà chính `core/dong_ho.py` sinh ra để chống: lấy
    # thời gian thật vào chỗ cần một mốc cố định.
    #
    # Sửa ở GỐC — làm phép đo tất định — chứ KHÔNG nới con số kỳ vọng.
    (tmp_path / "conftest.py").write_text(
        "import datetime as _dt\n"
        "import pytest\n"
        "\n"
        "# Thứ Tư — cố ý KHÔNG trùng ba thứ mà test_dong_ho.py tham số hoá,\n"
        "# để số test đỏ không đổi theo ngày chạy.\n"
        "_MOC = _dt.datetime(2026, 8, 26, 9, 30)\n"
        "\n"
        "\n"
        "class _DongHoDongDinh(_dt.datetime):\n"
        "    @classmethod\n"
        "    def now(cls, tz=None):\n"
        "        return _MOC if tz is None else _MOC.replace(tzinfo=tz)\n"
        "\n"
        "\n"
        "@pytest.fixture(autouse=True)\n"
        "def _dong_dinh_dong_ho(monkeypatch):\n"
        "    import core.dong_ho\n"
        "    monkeypatch.setattr(core.dong_ho, 'datetime', _DongHoDongDinh)\n",
        encoding="utf-8",
    )

    goc_tep = tmp_path / "core" / "dong_ho.py"
    goc_code = goc_tep.read_text(encoding="utf-8")
    
    # Gieo lỗi chỗ 0 (logic Or) như sổ E1
    moi_code, mo_ta = dot_bien(goc_code, 0)
    assert moi_code != "", "Phải gieo được đột biến vào dong_ho.py"
    goc_tep.write_text(moi_code, encoding="utf-8")

    # Tính dòng đột biến thực tế sau khi ast.unparse
    dong_dot_bien = None
    for idx_dong, dong_text in enumerate(moi_code.splitlines(), start=1):
        if "datetime.now()" in dong_text and "and" in dong_text:
            dong_dot_bien = idx_dong
            break
    assert dong_dot_bien is not None, "Phải xác định được dòng đột biến thật sự"
    assert dong_dot_bien == 23, f"Dòng đột biến trong dong_ho.py unparsed phải là 23, nhận được {dong_dot_bien}"

    ten_test_chot, so_test_khac, danh_sach = chot_test_can_trace(
        tep_nguon="core/dong_ho.py",
        tep_test="tests/test_dong_ho.py",
        dong_kiem_tra=dong_dot_bien,
        cwd=tmp_path,
        max_steps=5000,
    )

    # 1. Khẳng định ĐÚNG tên test được chọn theo luật tất định (ít bước nhất -> thứ tự pytest)
    assert ten_test_chot == "tests/test_dong_ho.py::test_cau_gio_noi_dung_thu_va_ngay"
    # 5 (không phải 4 như bản cũ): với đồng hồ đóng đinh vào Thứ Tư, cả BA test
    # tham số hoá theo thứ đều đỏ. Con số 4 của bản cũ là con số của những ngày
    # Thứ Hai / Thứ Bảy / Chủ Nhật, khi một trong ba test tình cờ xanh. Đây
    # KHÔNG phải nới ngưỡng: phép đo nay tất định, nên con số cũng đổi theo.
    assert so_test_khac == 5, f"dong_ho.py lỗi đơn có 6 test đỏ (1 chốt + 5 khác), nhận được {so_test_khac}"

    # 2. Khẳng định trace_result của test được chọn đi qua dòng đột biến (Tầng 1 thực thi thật)
    res_chot = next(r for r in danh_sach if r.ten_test == ten_test_chot)
    assert res_chot.trang_thai == "trace_du"
    assert res_chot.tong_buoc == 5
    assert len(res_chot.cac_su_kien) > 0
    assert any(ev.get("dong") == dong_dot_bien for ev in res_chot.cac_su_kien), "Test được chọn phải đi qua dòng đột biến 23"


def test_fallback_trace_khong_qua_loi(tmp_path: Path):
    """Kiểm tra khi không có test đỏ nào đi qua dòng kiểm tra, selector rơi vào nhánh dự phòng và trả về trace_khong_qua_loi."""
    for d in ("core", "tests"):
        shutil.copytree(PROJECT_ROOT / d, tmp_path / d)
    (tmp_path / "pytest.ini").write_text("[pytest]\npythonpath = .\n", encoding="utf-8")

    goc_tep = tmp_path / "core" / "dong_ho.py"
    moi_code, _ = dot_bien(goc_tep.read_text(encoding="utf-8"), 0)
    goc_tep.write_text(moi_code, encoding="utf-8")

    # Truyền dòng kiểm tra 9999 (không test nào đi qua dòng này)
    ten_test_chot, so_test_khac, danh_sach = chot_test_can_trace(
        tep_nguon="core/dong_ho.py",
        tep_test="tests/test_dong_ho.py",
        dong_kiem_tra=9999,
        cwd=tmp_path,
        max_steps=5000,
    )

    assert ten_test_chot is not None
    res_chot = next(r for r in danh_sach if r.ten_test == ten_test_chot)
    assert res_chot.trang_thai == "trace_khong_qua_loi"
    assert "KHÔNG ĐO ĐƯỢC: Vết thực thi không đi qua dòng đột biến" in res_chot.thong_diep


def test_trace_result_dong_da_chay_truc_tiep():
    """Kiểm tra TraceResult chứa danh sách dòng đã chạy chính xác khi trace trực tiếp."""
    res = chay_trace_mot_test(
        tep_nguon="core/dong_ho.py",
        node_id_test="tests/test_dong_ho.py::test_cau_gio_noi_dung_thu_va_ngay",
        max_steps=5000,
    )
    assert res.trang_thai == "trace_du"
    assert isinstance(res.dong_da_chay, list)
    assert len(res.dong_da_chay) > 0
    # Phải chứa các dòng định nghĩa / thực thi trong dong_ho.py
    assert all(isinstance(d, int) and d > 0 for d in res.dong_da_chay)

