# -*- coding: utf-8 -*-
"""``tools/gieo.py`` là một máy đo, nên chính nó phải được đo.

Nó in ra "ĐỎ (đạt)" / "CỬA MÙ" — đó là phán quyết. Một máy đo phát phán quyết mà
không ai kiểm thì y hệt Auto-Grader hôm 30/08: chạy trơn tru, nói rất tự tin, và
không đọc gì cả.

Bốn thứ nó hứa, bốn thứ ở đây kiểm bằng cách CHẠY THẬT:

* giữ nguyên kiểu xuống dòng (CRLF không bị đổi thành LF, và ngược lại)
* trả mã về đúng TỪNG BYTE, kể cả khi lệnh nổ giữa chừng
* phép gieo không khớp phải báo to, không được im
* cửa mù (gieo vào rồi mà lệnh vẫn xanh) phải bị bắt
"""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.gieo import Phep, chay_gieo, doc  # noqa: E402

PY_EXE = sys.executable


def _du_an(tmp_path: Path, kieu_xuong_dong: str) -> Path:
    """Một dự án tí hon: ma.py có hằng số, test kiểm hằng số đó."""
    ma = "GIA_TRI = 42\n"
    test = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent))\nfrom ma import GIA_TRI\n\n\ndef test_x():\n    assert GIA_TRI == 42\n"
    (tmp_path / "ma.py").write_bytes(ma.replace("\n", kieu_xuong_dong).encode("utf-8"))
    (tmp_path / "test_ma.py").write_bytes(test.replace("\n", kieu_xuong_dong).encode("utf-8"))
    return tmp_path


LENH = [PY_EXE, "-m", "pytest", "test_ma.py", "-q", "-p", "no:cacheprovider"]


@pytest.mark.parametrize("kieu", ["\r\n", "\n"])
def test_gieo_vao_duoc_va_tra_ma_ve_dung_tung_byte(tmp_path, kieu):
    """Phép gieo viết bằng ``\\n`` phải khớp cả tệp CRLF — đúng cái bẫy đã vấp."""
    goc = _du_an(tmp_path, kieu)
    truoc = hashlib.sha256((goc / "ma.py").read_bytes()).hexdigest()

    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("đổi hằng số", "ma.py", "GIA_TRI = 42", "GIA_TRI = 99")],
    )
    assert kq.nen_xanh, kq.dong_nen
    assert kq.cua_mu == [], "gieo vào rồi mà lệnh vẫn xanh — phải bị bắt"
    assert kq.khong_vao == [], f"phép gieo viết bằng \\n không khớp tệp {kieu!r}"
    assert kq.ma_thoat == 0

    sau_raw = (goc / "ma.py").read_bytes()
    assert hashlib.sha256(sau_raw).hexdigest() == truoc, "không trả mã về nguyên byte"
    assert kieu.encode() in sau_raw, f"kiểu xuống dòng {kieu!r} bị đổi"
    if kieu == "\n":
        assert b"\r\n" not in sau_raw, "tệp LF bị biến thành CRLF"


def test_gieo_giu_nguyen_do_dai_van_phai_vao_toi_may(tmp_path):
    """Bẫy ``.pyc``: Python dùng lại bản biên dịch cũ theo **mtime + KÍCH THƯỚC**.

    ``GIA_TRI = 42`` -> ``GIA_TRI = 99`` là cùng số byte. Nếu mtime chưa nhích qua
    độ phân giải hệ tệp, tiến trình con nạp lại bản CŨ: hạt giống không tới máy,
    lệnh vẫn xanh, và công cụ kết luận "CỬA MÙ" — vu oan cho cửa.

    Bắt được 30/08/2026 bởi chính bộ test này: cùng một phép gieo, ca CRLF đỏ còn
    ca LF xanh, khác nhau chỉ vì may rủi thời điểm ghi. Chạy nền TRƯỚC để chắc
    chắn đã có ``.pyc`` cũ, rồi mới gieo.

    ĐỪNG đổi phép gieo này sang một cặp khác độ dài — làm thế là gỡ mất cái bẫy.
    """
    goc = _du_an(tmp_path, "\n")
    import subprocess
    subprocess.run(LENH, cwd=str(goc), capture_output=True)      # sinh .pyc cũ
    assert list((goc / "__pycache__").glob("ma.*.pyc")), "chưa sinh được .pyc để thử bẫy"

    cu = (goc / "ma.py").read_bytes()
    moi = cu.replace(b"42", b"99")
    assert len(moi) == len(cu), "phép gieo phải GIỮ NGUYÊN độ dài mới thử được bẫy"

    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("đổi hằng số, cùng độ dài", "ma.py", "GIA_TRI = 42", "GIA_TRI = 99")],
    )
    assert kq.cua_mu == [], "bản biên dịch cũ nuốt mất hạt giống, rồi đổ cho cửa"
    assert kq.ma_thoat == 0


def test_phep_khong_khop_phai_bao_to_chu_khong_im(tmp_path):
    """Im lặng ở đây đọc y hệt 'cửa bắt được' — đó là chỗ nguy hiểm nhất."""
    goc = _du_an(tmp_path, "\r\n")
    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("chuỗi không tồn tại", "ma.py", "KHONG_CO_CHUOI_NAY", "x")],
    )
    assert kq.khong_vao == ["chuỗi không tồn tại"]
    assert kq.ma_thoat == 2, "gieo không vào là KHÔNG ĐO ĐƯỢC, không phải đạt"


def test_cua_mu_phai_bi_bat(tmp_path):
    """Gieo vào thật mà lệnh vẫn xanh: cửa không canh chỗ đó."""
    goc = _du_an(tmp_path, "\r\n")
    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        # đổi một chỗ mà test không hề kiểm -> lệnh vẫn xanh
        cac_phep=[Phep("thêm dòng test không đụng tới", "ma.py",
                       "GIA_TRI = 42", "GIA_TRI = 42\nKHONG_AI_KIEM = 1")],
    )
    assert kq.cua_mu == ["thêm dòng test không đụng tới"]
    assert kq.ma_thoat == 1, "cửa mù phải là 1, không được coi là đạt"
    assert hashlib.sha256((goc / "ma.py").read_bytes()).hexdigest() == \
        hashlib.sha256(b"GIA_TRI = 42\r\n").hexdigest()


def test_nen_do_san_thi_dung_lai_chu_dung_gieo(tmp_path):
    """Nền đỏ thì gieo không nói lên điều gì — mọi phép đều 'đỏ', vô nghĩa."""
    goc = _du_an(tmp_path, "\n")
    (goc / "ma.py").write_text("GIA_TRI = 7\n", encoding="utf-8")   # test sẽ đỏ
    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("bất kỳ", "ma.py", "GIA_TRI = 7", "GIA_TRI = 8")],
    )
    assert kq.nen_xanh is False
    assert kq.hang == [], "nền đỏ mà vẫn gieo tiếp — kết quả sẽ bị đọc nhầm"
    assert kq.ma_thoat == 1


def test_van_tra_ma_ve_khi_lenh_khong_chay_noi(tmp_path):
    """Lệnh hỏng thì vẫn phải trả mã về — mất mã của người dùng là giá đắt nhất."""
    goc = _du_an(tmp_path, "\r\n")
    truoc = (goc / "ma.py").read_bytes()
    kq = chay_gieo(
        lenh=["mot_lenh_khong_ton_tai_tren_doi"], goc=goc, im_lang=True,
        cac_phep=[Phep("đổi hằng số", "ma.py", "42", "99")],
    )
    assert kq.nen_xanh is False
    assert (goc / "ma.py").read_bytes() == truoc, "lệnh hỏng làm mất mã gốc"
    assert kq.khong_tra_duoc == []


def test_doc_nhan_dung_kieu_xuong_dong(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
    chu, kieu, _ = doc(tmp_path / "a.py")
    assert kieu == "\r\n"
    assert chu == "x = 1\ny = 2\n", "nội dung phải được chuẩn hoá về \\n để phép gieo khớp"

    (tmp_path / "b.py").write_bytes(b"x = 1\ny = 2\n")
    chu, kieu, _ = doc(tmp_path / "b.py")
    assert kieu == "\n"


def test_ham_gieo_tuy_y_cung_dung_duoc(tmp_path):
    """Đổi phức tạp thì truyền hàm, không phải cắt thành nhiều phép thay chuỗi."""
    goc = _du_an(tmp_path, "\r\n")
    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("bằng hàm", "ma.py", ham=lambda s: s.replace("42", "0"))],
    )
    assert kq.khong_vao == []
    assert kq.cua_mu == []
    assert kq.ma_thoat == 0
