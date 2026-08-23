# -*- coding: utf-8 -*-
"""Cửa độc lập cho ánh xạ chỉ số→dòng và tracer exactly-once của E1."""
from __future__ import annotations

import subprocess
from pathlib import Path

import experiments.evidence_sprint.do_lat_nguoc as worker
from experiments.evidence_sprint.do_lat_nguoc import (
    _chay_trace_dong_day_du,
    _chi_so_khoi_phuc,
    _liet_ke_cho,
    mot_de,
)


def test_liet_ke_dung_thu_tu_hau_duyet_va_dong_ma_dot_bien():
    nguon = "def f(x):\n    return x < 3 and not False\n"
    # Constant 3, Compare, Constant False, Not, And — cùng thứ tự `_Lat` lật.
    assert _liet_ke_cho(nguon) == [
        (0, 2), (1, 2), (2, 2), (3, 2), (4, 2)
    ]


def test_dap_an_tinh_tu_ast_khong_do_chuoi():
    ma_dot_bien = "x = 1 <= 2"
    ma_chuan = "x = 1 < 2"
    assert _chi_so_khoi_phuc(ma_dot_bien, ma_chuan) == [2]


def test_trace_dong_bat_ca_dong_khong_doi_local_va_chay_test_mot_lan(tmp_path: Path):
    (tmp_path / "core").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "core" / "__init__.py").write_text("", encoding="utf-8")
    source = tmp_path / "core" / "demo.py"
    source.write_text(
        "from pathlib import Path\n"
        "def f(x):\n"
        "    with Path(__file__).with_name('count.txt').open('a', encoding='utf-8') as h:\n"
        "        h.write('x')\n"
        "    if x > 0:\n"          # không tạo/đổi local, vẫn phải nằm trong vết
        "        return 1\n"
        "    return 0\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_demo.py").write_text(
        "from core.demo import f\n"
        "def test_red():\n"
        "    assert f(1) == 2\n",
        encoding="utf-8",
    )

    trace = _chay_trace_dong_day_du(
        tmp_path, "core/demo.py", "tests/test_demo.py::test_red"
    )

    assert trace["trang_thai"] == "trace_du"
    assert 5 in trace["dong_da_chay"]
    assert (tmp_path / "core" / "count.txt").read_text(encoding="utf-8") == "x"


def _de_nho(tmp_path: Path) -> dict:
    (tmp_path / "core").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "core" / "a.py").write_text("x = 2\n", encoding="utf-8")
    return {"tep": "core/a.py", "tep_test": "tests/test_a.py", "cho": [0]}


def test_timeout_kiem_nhieu_tra_khong_do_duoc(monkeypatch, tmp_path: Path):
    de = _de_nho(tmp_path)

    def qua_gio(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("pytest", 1)

    monkeypatch.setattr(worker, "chay_test", qua_gio)
    assert mot_de(tmp_path, de) == {
        "trang_thai": "khong_do_duoc",
        "vi_sao": "kiểm nhiễu test đỏ quá thời gian",
    }


def test_timeout_luc_lat_fail_closed_va_khoi_phuc_tep(monkeypatch, tmp_path: Path):
    de = _de_nho(tmp_path)
    goc = (tmp_path / "core" / "a.py").read_text(encoding="utf-8")
    so_lan = 0

    def do_hai_lan_roi_qua_gio(*_args, **_kwargs):
        nonlocal so_lan
        so_lan += 1
        if so_lan <= 2:
            return 1, "E assert giả"
        raise subprocess.TimeoutExpired("pytest", 1)

    monkeypatch.setattr(worker, "chay_test", do_hai_lan_roi_qua_gio)
    monkeypatch.setattr(worker, "_chon_test_va_dong", lambda *_args, **_kwargs: {
        "trang_thai": "trace_du",
        "dong_da_chay": [1],
        "test": "tests/test_a.py::test_a",
        "so_test_do_khac": 0,
        "so_buoc": 1,
    })

    ket_qua = mot_de(tmp_path, de)

    assert ket_qua["trang_thai"] == "khong_do_duoc"
    assert ket_qua["vi_sao"] == "lọc + lật vượt trần 60 giây"
    assert (tmp_path / "core" / "a.py").read_text(encoding="utf-8") == goc
