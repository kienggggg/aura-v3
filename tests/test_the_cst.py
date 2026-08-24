# -*- coding: utf-8 -*-
"""Kiểm thử bộ phân tích và lưu tệp LibCST (the_cst.py) và the_v1.py."""
import pathlib
import pytest

from core.the_cst import (
    doc_tep_py_sang_cay_the as cst_doc_tep,
    luu_cay_the_ra_tep_py as cst_luu_tep,
    doc_chuoi_py_sang_cay_the as cst_doc_chuoi,
)
from core.the_v1 import (
    doc_tep_py_sang_cay_the as v1_doc_tep,
    luu_cay_the_ra_tep_py as v1_luu_tep,
    BO_THE_V1,
    NHOM_THE,
)


def _phang(nodes):
    ra = []
    for n in nodes:
        ra.append(n)
        if n.than:
            ra.extend(_phang(n.than))
    return ra


def test_lossless_23_files_core():
    """CST phải đảm bảo 100% byte-for-byte lossless trên toàn bộ 23 tệp core/*.py."""
    files = list(pathlib.Path("core").glob("*.py"))
    assert len(files) == 23, f"Kỳ vọng 23 tệp core/*.py, thấy {len(files)}"
    for p in files:
        raw = p.read_bytes()
        rec = cst_doc_tep(p)
        out = cst_luu_tep(rec)
        assert out == raw, f"Lệch byte tại {p.name}"


def test_chu_thich_the_in_web_search():
    """core/web_search.py có nhiều chú thích dòng riêng (>= 80 thẻ chu_thich)."""
    # 1. Kiểm tra trên the_v1
    rec_ws_v1 = v1_doc_tep("core/web_search.py")
    all_nodes_v1 = _phang(rec_ws_v1.tree)
    chu_thich_v1 = [n for n in all_nodes_v1 if n.ma == "chu_thich"]
    assert len(chu_thich_v1) >= 80, f"the_v1 web_search.py chỉ có {len(chu_thich_v1)} thẻ chu_thich, kỳ vọng >= 80"

    # 2. Kiểm tra trên the_cst
    rec_ws_cst = cst_doc_tep("core/web_search.py")
    all_nodes_cst = _phang(rec_ws_cst.tree)
    chu_thich_cst = [n for n in all_nodes_cst if n.ma == "chu_thich"]
    assert len(chu_thich_cst) >= 80, f"the_cst web_search.py chỉ có {len(chu_thich_cst)} thẻ chu_thich, kỳ vọng >= 80"


def test_dong_ma_thuat_khong_thanh_chu_thich():
    """Dòng 1-2 chứa coding hoặc shebang (#!) KHÔNG được thành thẻ chu_thich (phải giữ trong ma_tho)."""
    # 1. the_v1
    rec_dh_v1 = v1_doc_tep("core/dong_ho.py")
    all_nodes_v1 = _phang(rec_dh_v1.tree)
    assert not any(n.ma == "chu_thich" and "coding" in n.o.get("noi_dung", "") for n in all_nodes_v1)
    dong_1_v1 = next((n for n in all_nodes_v1 if n.line_start == 1), None)
    assert dong_1_v1 is not None and dong_1_v1.ma == "ma_tho"

    # 2. the_cst
    rec_dh_cst = cst_doc_tep("core/dong_ho.py")
    all_nodes_cst = _phang(rec_dh_cst.tree)
    assert not any(n.ma == "chu_thich" and "coding" in n.o.get("noi_dung", "") for n in all_nodes_cst)
    assert all_nodes_cst[0].ma == "ma_tho"
    assert "coding" in all_nodes_cst[0].o.get("nguyen_van", "")


def test_bo_the_v1_co_chu_thich():
    """BO_THE_V1 và NHOM_THE phải có thẻ chu_thich với màu xanh ngọc."""
    assert "chu_thich" in BO_THE_V1
    assert "chu_thich" in NHOM_THE
    assert BO_THE_V1["chu_thich"].nhom == "chu_thich"
    assert NHOM_THE["chu_thich"]["mau"] == "#14B8A6"
    assert BO_THE_V1["chu_thich"].co_than is False
