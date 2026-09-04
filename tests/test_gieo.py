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
    import os
    import subprocess

    # Lượt hâm nóng PHẢI được phép ghi .pyc, nên dọn `PYTHONDONTWRITEBYTECODE`
    # khỏi môi trường thay vì thừa hưởng của cha.
    #
    # 03/09/2026: bài này đỏ khi chạy DƯỚI `gieo.py` và xanh khi chạy thẳng —
    # vì `chay_gieo` đặt đúng biến ấy cho tiến trình con, và `subprocess.run`
    # ở đây thừa hưởng nó. Không sinh được .pyc thì khẳng định ngay dưới gãy.
    # Bắt được nhờ chính bản sửa hôm nay: nền đỏ nay in ra TÊN BÀI.
    mt = dict(os.environ)
    mt.pop("PYTHONDONTWRITEBYTECODE", None)
    subprocess.run(LENH, cwd=str(goc), capture_output=True, env=mt)   # sinh .pyc cũ
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


# ---------------------------------------------------------------------------
# TÊN BÀI ĐỎ (thêm 03/09/2026)
#
# Trước đó bảng chỉ ghi "-> ĐỎ (đạt)" và "1 failed, 39 passed". Hai chuyện quan
# trọng đều không nói ra được:
#
#   nền đỏ  -> không biết bài nào. Gặp đúng ca ấy hai lần liên tiếp ngày 03/09;
#              phải chạy lại tay mới biết, rồi lần chạy lại nó XANH nên mất dấu.
#   gieo đỏ -> một phép gieo làm đỏ một bài CHẲNG LIÊN QUAN trông y hệt một phép
#              gieo bắt trúng.

def test_boc_ten_bai_do_tu_dau_ra_pytest():
    """Đo 03/09 chứ không đoán: `pytest -q` CÓ SẴN khối `short test summary`."""
    from tools.gieo import ten_bai_do

    ra = ten_bai_do(
        "..F.F\n"
        "=========================== short test summary info ====================\n"
        "FAILED tests/test_a.py::test_mot - assert 1 == 2\n"
        "FAILED tests/test_b.py::test_hai - ValueError: hong\n"
        "ERROR tests/test_c.py\n"
        "2 failed, 3 passed in 0.07s\n"
    )
    assert ra == ["tests/test_a.py::test_mot", "tests/test_b.py::test_hai",
                  "tests/test_c.py"], ra


def test_boc_ten_bai_do_tu_dau_ra_node_tap():
    from tools.gieo import ten_bai_do

    assert ten_bai_do("ok 1 - chay duoc\nnot ok 2 - nut khong co handler\n") == [
        "nut khong co handler"]


def test_boc_ten_khong_bia_khi_khong_co_gi():
    """Rỗng phải là RỖNG — không được bịa ra một tên nghe hợp lý."""
    from tools.gieo import ten_bai_do

    assert ten_bai_do("") == []
    assert ten_bai_do("3 passed in 0.02s\n") == []
    # "FAILED" nằm giữa dòng thì KHÔNG phải dòng tổng kết của pytest.
    assert ten_bai_do("day la mot cau co chu FAILED o giua\n") == []


def test_nen_do_thi_NOI_RA_bai_nao_do(tmp_path, capsys):
    """Nền đỏ là lúc CẦN tên bài nhất — gieo dừng ngay, dấu vết mất luôn."""
    du_an = _du_an(tmp_path, "\n")
    (du_an / "test_do_san.py").write_text(
        "def test_da_do_san():\n    assert False\n", encoding="utf-8")

    kq = chay_gieo(
        lenh=[PY_EXE, "-m", "pytest", ".", "-q", "-p", "no:cacheprovider"],
        cac_phep=[Phep("doi hang so", "ma.py", "42", "41")],
        goc=du_an,
    )
    assert not kq.nen_xanh
    assert any("test_da_do_san" in t for t in kq.bai_do_nen), kq.bai_do_nen
    assert "test_da_do_san" in capsys.readouterr().out, (
        "tên bài đỏ phải được IN RA, không chỉ nằm trong KetQua"
    )


def test_gieo_do_thi_noi_ra_do_o_BAI_NAO(tmp_path, capsys):
    """"ĐỎ" chưa đủ — phải đỏ VÌ ĐÚNG LÝ DO.

    Ca đối chứng nằm ngay trong bài: hai phép gieo, một phép nhắm trúng làm đỏ
    ĐÚNG MỘT bài, một phép cùn (hỏng import) kéo đổ CẢ HAI. Trước 03/09 hai
    phép ấy in ra y hệt nhau.
    """
    du_an = _du_an(tmp_path, "\n")
    (du_an / "test_ma.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
        "from ma import GIA_TRI\n\n\n"
        "def test_dung_gia_tri():\n    assert GIA_TRI == 42\n\n\n"
        "def test_la_so_nguyen():\n    assert isinstance(GIA_TRI, int)\n",
        encoding="utf-8")

    kq = chay_gieo(
        lenh=[PY_EXE, "-m", "pytest", "test_ma.py", "-q", "-p", "no:cacheprovider"],
        cac_phep=[
            Phep("nham trung: doi gia tri", "ma.py", "GIA_TRI = 42", "GIA_TRI = 41"),
            Phep("cun: doi sang chuoi", "ma.py", "GIA_TRI = 42", 'GIA_TRI = "42"'),
        ],
        goc=du_an,
    )
    assert kq.cua_mu == [], kq.cua_mu
    trung = kq.bai_do["nham trung: doi gia tri"]
    cun = kq.bai_do["cun: doi sang chuoi"]
    assert len(trung) == 1 and "test_dung_gia_tri" in trung[0], trung
    assert len(cun) == 2, f"phép cùn phải làm đỏ cả hai bài: {cun}"
    ra = capsys.readouterr().out
    assert "test_dung_gia_tri" in ra and "test_la_so_nguyen" in ra, (
        "hai phép gieo phải PHÂN BIỆT được trên màn hình"
    )


def test_khong_boc_duoc_ten_thi_NOI_LA_khong_boc_duoc(tmp_path, capsys):
    """Ba trạng thái, không gộp: có tên · không có bài đỏ · KHÔNG BÓC ĐƯỢC.

    Nếu chỗ in lặng lẽ bỏ qua khi danh sách rỗng thì "không bóc được tên" đọc y
    hệt "gieo này sạch" — đúng cái ba-trạng-thái sinh ra để chống.
    """
    from tools.gieo import _in_bai_do

    dong: list[str] = []
    _in_bai_do(dong.append, [])
    assert dong and "không bóc được" in dong[0], dong


def test_boc_ten_bo_trung_lap():
    """Một bài đỏ phải đếm MỘT lần, dù đầu ra nhắc nó nhiều lần.

    Gieo 03/09 bắt được chỗ mù: bỏ `dict.fromkeys` mà cả bộ vẫn xanh — không
    bài nào đưa vào đầu ra có tên lặp. `pytest -rA` in cả `ERROR` lẫn `FAILED`
    cho cùng một bài, nên đây không phải ca tưởng tượng.
    """
    from tools.gieo import ten_bai_do

    ra = ten_bai_do(
        "FAILED tests/test_a.py::test_mot - loi lan mot\n"
        "FAILED tests/test_b.py::test_hai - loi khac\n"
        "FAILED tests/test_a.py::test_mot - van loi ay\n"
    )
    assert ra == ["tests/test_a.py::test_mot", "tests/test_b.py::test_hai"], ra


def test_tep_bi_SUA_TRONG_LUC_GIEO_thi_KHONG_ghi_de(tmp_path, capsys):
    """Ngày 03/09/2026 tôi sửa chú thích `core/phong_alpha.py` trong lúc một lượt
    gieo đang chạy nền trên chính tệp ấy. `chay_gieo` cache nội dung gốc lúc khởi
    động, rồi ở `finally` ghi cache đè lên — **bản sửa biến mất không một tiếng
    động**, và commit đi mất luôn. Phát hiện một ngày sau, tình cờ.

    Chua nhất: dòng *"1 tệp: giống hệt TỪNG BYTE trước khi gieo"* chính là cơ chế
    ấy đang báo cáo THÀNH CÔNG. Một máy đo nói thật về việc nó làm, mà việc nó
    làm là xoá công của người khác.

    BÀN TAY THỨ HAI PHẢI GHI TRONG LÚC LỆNH CHẠY. Bản đầu của bài này bơm qua
    `Phep(ham=...)` — chạy TRƯỚC lúc `chay_gieo` ghi bản gieo, nên bản "người
    khác" bị đè ngay và không có gì để phát hiện. Sai chỗ bơm thì phép đo đo một
    thứ khác.
    """
    goc = _du_an(tmp_path, "\n")
    ma = goc / "ma.py"
    NGUOI_KHAC = "GIA_TRI = 42\n# dong nguoi khac vua them\n"

    # Lệnh này ĐÓNG VAI bàn tay thứ hai: nó ghi đè ma.py rồi thoát khác 0.
    lenh_sua = [PY_EXE, "-c",
                "import pathlib,sys;"
                f"pathlib.Path({str(ma)!r}).write_text({NGUOI_KHAC!r}, encoding='utf-8');"
                "sys.exit(1)"]

    kq = chay_gieo(
        lenh=lenh_sua, goc=goc,
        cac_phep=[Phep("gieo rồi bị sửa chen ngang", "ma.py",
                       "GIA_TRI = 42", "GIA_TRI = 99")],
    )
    assert kq.bi_sua_giua_chung == ["ma.py"], kq.bi_sua_giua_chung
    assert ma.read_text(encoding="utf-8") == NGUOI_KHAC, (
        "gieo.py đã GHI ĐÈ lên bản sửa của người khác")
    assert kq.ma_thoat == 2, "bị sửa chen ngang là KHÔNG ĐO ĐƯỢC, không phải đạt"
    assert "BỊ SỬA TRONG LÚC GIEO" in capsys.readouterr().out
    # Bản gốc phải được giữ lại ở đâu đó, không được mất.
    giu = goc / "ma.py.truoc_khi_gieo"
    assert giu.is_file() and "GIA_TRI = 42" in giu.read_text(encoding="utf-8")


def test_khong_bi_sua_thi_VAN_tra_ma_ve_binh_thuong(tmp_path):
    """Ca đối chứng: bài trên phải xanh vì có bàn tay thứ hai, không phải vì
    `gieo.py` từ nay không bao giờ trả mã về nữa."""
    goc = _du_an(tmp_path, "\n")
    truoc = hashlib.sha256((goc / "ma.py").read_bytes()).hexdigest()
    kq = chay_gieo(
        lenh=LENH, goc=goc, im_lang=True,
        cac_phep=[Phep("đổi hằng số", "ma.py", "GIA_TRI = 42", "GIA_TRI = 99")],
    )
    assert kq.bi_sua_giua_chung == []
    assert kq.ma_thoat == 0
    assert hashlib.sha256((goc / "ma.py").read_bytes()).hexdigest() == truoc
    assert not (goc / "ma.py.truoc_khi_gieo").exists(), "không có ai sửa thì đừng đẻ tệp thừa"
