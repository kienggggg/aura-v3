# -*- coding: utf-8 -*-
"""Kiểm thử bộ phân tích và lưu tệp LibCST (`core/the_cst.py`).

01/09/2026 — tệp này TỪNG chạy mỗi khẳng định HAI LẦN: một lần qua bộ đọc
LibCST, một lần qua một bộ đọc AST thứ hai nằm trong `core/the_v1.py`. Nó
không so hai bộ với nhau, chỉ đòi cả hai cùng thoả một tính chất.

Bộ đọc AST ấy KHÔNG AI GỌI: `interface/the_api.py` lấy hàm đọc từ
`the_cst`, chỉ lấy `BO_THE_V1 · NHOM_THE · TheNode · sinh_ma_python · …`
từ `the_v1`. Phân tích khả đạt: 10/30 mục cấp module của `the_v1.py` không
ai với tới — 588 dòng. Đã xoá.

Nó không chỉ là mã chết. Ngày 01/09 tôi đo nhầm nó rồi báo với Sếp rằng app
không dựng nổi thẻ `nhap` · `thu` · `bat_loi` · `bo_qua` · `dung_lap`. Số
thật của bộ đọc app dùng: 46 · 19 · 26 · 7 · 1, và `ma_tho` chỉ 7,3% chứ
không phải 22,1%. Hai bộ trông giống hệt nhau từ bên ngoài — đó là chỗ đắt.
"""
import pathlib
import pytest

from core.the_cst import (
    doc_tep_py_sang_cay_the as cst_doc_tep,
    luu_cay_the_ra_tep_py as cst_luu_tep,
    doc_chuoi_py_sang_cay_the as cst_doc_chuoi,
)
from core.the_v1 import BO_THE_V1, NHOM_THE


def _phang(nodes):
    ra = []
    for n in nodes:
        ra.append(n)
        if n.than:
            ra.extend(_phang(n.than))
    return ra


def test_lossless_core_files():
    """CST phải đảm bảo 100% byte-for-byte lossless trên toàn bộ các tệp core/*.py."""
    files = list(pathlib.Path("core").glob("*.py"))
    assert len(files) >= 23, f"Kỳ vọng ít nhất 23 tệp core/*.py, thấy {len(files)}"
    for p in files:
        raw = p.read_bytes()
        rec = cst_doc_tep(p)
        out = cst_luu_tep(rec)
        assert out == raw, f"Lệch byte tại {p.name}"


def test_chu_thich_the_in_web_search():
    """core/web_search.py có nhiều chú thích dòng riêng (>= 80 thẻ chu_thich)."""
    rec_ws_cst = cst_doc_tep("core/web_search.py")
    all_nodes_cst = _phang(rec_ws_cst.tree)
    chu_thich_cst = [n for n in all_nodes_cst if n.ma == "chu_thich"]
    assert len(chu_thich_cst) >= 80, f"the_cst web_search.py chỉ có {len(chu_thich_cst)} thẻ chu_thich, kỳ vọng >= 80"


def test_dong_ma_thuat_khong_thanh_chu_thich():
    """Dòng 1-2 chứa coding hoặc shebang (#!) KHÔNG được thành thẻ chu_thich (phải giữ trong ma_tho)."""
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


# ==============================================================================
# 5 THẺ THÊM 25/08/2026 — nhap · dung_lap · bo_qua · thu · bat_loi
# ==============================================================================

MAU_NAM_THE = '''from math import sqrt
import json as js


def kiem(day):
    for i in day:
        if i == 1:
            continue
        if i == 4:
            break
        print(i, sqrt(i))
    try:
        print(sqrt(-1))
    except ValueError as e:
        print("bat duoc:", e)
    return js.dumps(list(day))
'''


def _dem_ma(cay):
    dem = {}

    def di(ns):
        for n in ns:
            dem[n.ma] = dem.get(n.ma, 0) + 1
            di(n.than)

    di(cay)
    return dem


def _cay_cua(r):
    return r.cay if hasattr(r, "cay") else r.tree


def _tim(ns, ma):
    for n in ns:
        if n.ma == ma:
            return n
        t = _tim(n.than, ma)
        if t:
            return t
    return None


def test_nam_the_moi_doc_len_dung_loai():
    """Năm cấu trúc ấy trước 25/08 đều rơi vào `ma_tho`. Nay phải thành thẻ."""
    dem = _dem_ma(_cay_cua(cst_doc_chuoi(MAU_NAM_THE)))
    assert dem.get("nhap") == 2, dem
    assert dem.get("bo_qua") == 1, dem
    assert dem.get("dung_lap") == 1, dem
    assert dem.get("thu") == 1, dem
    assert dem.get("bat_loi") == 1, dem
    assert "ma_tho" not in dem, "Không được còn mã thô nào: %s" % dem


def test_nam_the_moi_mo_roi_luu_y_nguyen_byte():
    """Mở rồi lưu, KHÔNG sửa gì — phải trùng từng byte."""
    r = cst_doc_chuoi(MAU_NAM_THE)
    assert cst_luu_tep(r) == MAU_NAM_THE.encode("utf-8")


def test_sua_the_nhap_va_bat_loi_thi_GHI_DUOC_RA_TEP():
    """Sửa ô rồi lưu thì tệp phải ĐỔI THEO.

    VÌ SAO CÓ TEST NÀY: `_ap_dung` kết thúc bằng `return nut`, nên thẻ nào nó
    chưa biết thì sửa xong LƯU LÀ MẤT LẶNG LẼ — mặt thẻ hiện giá trị mới, tệp
    giữ giá trị cũ, không ai báo gì. Đo thật ngày 25/08 TRƯỚC khi viết đường
    lưu: đổi `ValueError` -> `ZeroDivisionError` rồi lưu, tệp vẫn ghi
    `except ValueError as e:`.

    Đúng họ bệnh "giao diện hứa một việc, mã làm việc khác" ở CLAUDE.md §4.
    """
    # 1. `from math import sqrt` -> `from statistics import mean`
    r = cst_doc_chuoi(MAU_NAM_THE)
    c = _cay_cua(r)
    c[0].o["thu_vien"] = "statistics"
    c[0].o["phan"] = "mean"
    c[0].da_sua = True
    ra = cst_luu_tep(r).decode("utf-8")
    assert "from statistics import mean" in ra
    assert "from math import sqrt" not in ra

    # 2. `import json as js` -> `import csv` (bỏ luôn phần `as`)
    r = cst_doc_chuoi(MAU_NAM_THE)
    c = _cay_cua(r)
    c[1].o["thu_vien"] = "csv"
    c[1].o["ten_khac"] = ""
    c[1].da_sua = True
    ra = cst_luu_tep(r).decode("utf-8")
    assert "import csv" in ra
    assert "import json as js" not in ra

    # 3. `except ValueError as e:` -> `except ZeroDivisionError as loi:`
    r = cst_doc_chuoi(MAU_NAM_THE)
    b = _tim(_cay_cua(r), "bat_loi")
    b.o["loai_loi"] = "ZeroDivisionError"
    b.o["ten_bien"] = "loi"
    b.da_sua = True
    ra = cst_luu_tep(r).decode("utf-8")
    assert "except ZeroDivisionError as loi:" in ra

    # 4. Bỏ tên biến -> `except ValueError:`, KHÔNG được sinh `except as ...`
    r = cst_doc_chuoi(MAU_NAM_THE)
    b = _tim(_cay_cua(r), "bat_loi")
    b.o["ten_bien"] = ""
    b.da_sua = True
    ra = cst_luu_tep(r).decode("utf-8")
    assert "except ValueError:" in ra
    dong_except = [d for d in ra.splitlines() if "except" in d]
    assert all(" as " not in d for d in dong_except), dong_except


def test_import_nhieu_dong_trong_ngoac_van_la_ma_tho():
    """Import có ngoặc PHẢI ở lại mã thô.

    Đường lưu dựng lại câu lệnh từ ba ô nên nó sinh MỘT dòng. Nhận dạng khối
    13 tên trong ngoặc ở `core/chat_service.py:13` thành thẻ `nhap` rồi lưu là
    gom hết về một dòng dài — cửa lossless bắt ngay bằng SHA lệch. Test này
    giữ cho ai đó về sau đừng gỡ hàng rào ấy ra.
    """
    ma = "from core.chat_contract import (\n    ChatRequest,\n    ChatResult,\n)\n"
    r = cst_doc_chuoi(ma)
    assert _cay_cua(r)[0].ma == "ma_tho", _cay_cua(r)[0].ma
    assert cst_luu_tep(r) == ma.encode("utf-8")


def test_try_co_finally_van_la_ma_tho():
    """`try/finally` PHẢI ở lại mã thô — khay chưa có thẻ cho `finally`.

    Nhận dạng nó thành thẻ `thu` là LÀM MẤT khối `finally` lúc lưu.
    """
    ma = "try:\n    x = 1\nfinally:\n    x = 2\n"
    r = cst_doc_chuoi(ma)
    assert _cay_cua(r)[0].ma == "ma_tho", _cay_cua(r)[0].ma
    assert cst_luu_tep(r) == ma.encode("utf-8")


def test_cst_ten_diem_va_nested_call_attributes():
    """Kiểm tra nhận dạng tên hàm phân cấp a.b.c qua _ten_diem trong the_cst."""
    import libcst as cst
    from core.the_cst import _ten_diem

    nut_ten = cst.Name("func")
    assert _ten_diem(nut_ten) == "func"

    nut_attr1 = cst.Attribute(value=cst.Name("os"), attr=cst.Name("path"))
    assert _ten_diem(nut_attr1) == "os.path"

    nut_attr2 = cst.Attribute(value=nut_attr1, attr=cst.Name("join"))
    assert _ten_diem(nut_attr2) == "os.path.join"

    # Test qua chuỗi mã nguồn
    ma = "os.path.join('a', 'b')\n"
    r = cst_doc_chuoi(ma)
    cay = _cay_cua(r)
    assert len(cay) >= 1
    assert cay[0].ma == "goi_ham"
    assert cay[0].o["ten_ham"] == "os.path.join"

