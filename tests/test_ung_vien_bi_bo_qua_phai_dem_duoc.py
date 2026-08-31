# -*- coding: utf-8 -*-
"""Ứng viên bị bỏ qua trong vòng lật phải ĐẾM ĐƯỢC, không được biến mất im lặng.

30/08/2026. ``chay_e1_dinh_vi`` báo ra ``candidate_count_after`` — số ứng viên
còn lại **sau bộ lọc dòng chạy**, tức số phép nó ĐỊNH thử. Nhưng trong vòng lật
có hai chỗ ``except Exception: continue`` bỏ qua ứng viên mà không ai đếm:

* sinh mã sau khi lật nổ lỗi
* chạy test để kiểm phép lật nổ lỗi

Nên "sau lọc 4, tìm ra 0" đọc thành *"đã thử 4 phép, không phép nào xanh"* —
trong khi thật ra có thể thử 0 phép và 4 phép kia biến mất. Đo được, cùng một
đầu vào, chỉ khác việc gieo một lỗi vào chỗ sinh mã::

    chưa gieo   sau_loc=4  đã_thử=4  bỏ_qua=0  -> tìm ra 2
    gieo hỏng   sau_loc=4  đã_thử=0  bỏ_qua=4  -> tìm ra 0

Trước bản vá, cả hai dòng đều chỉ hiện ``sau_loc=4`` và "tìm ra 0".

Tệp ``core/lat_nguoc.py`` đã chữa đúng bệnh này một lần rồi — xem ``CHO_BO_QUA``
và chú thích *"bọc TỪNG chỗ, và ghi chỗ bị bỏ vào CHO_BO_QUA để đếm được"*. Hai
chỗ trong vòng lật bị sót. Cửa này canh để chúng không sót lại lần nữa.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.lat_nguoc as lat_nguoc  # noqa: E402

NGUON = (
    "def phan_loai(n):\n"
    "    if n > 10:\n"
    "        return 'lon'\n"
    "    if n >= 5:\n"
    "        return 'vua'\n"
    "    return 'nho'\n"
)

# Test ĐỎ thật: phan_loai(10) trả 'vua', test đòi 'lon'. Phải đỏ thì mới có vết,
# có vết thì bộ lọc dòng mới giữ lại ứng viên, và vòng lật mới thật sự chạy.
TEST_DO = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
    "from ma_t import phan_loai\n"
    "\n"
    "\n"
    "def test_bien():\n"
    "    assert phan_loai(10) == 'lon'\n"
)


@pytest.fixture()
def du_an():
    tam = Path(tempfile.mkdtemp(prefix="aura_bo_qua_"))
    (tam / "ma_t.py").write_text(NGUON, encoding="utf-8")
    (tam / "tests").mkdir()
    (tam / "tests" / "test_ma_t.py").write_text(TEST_DO, encoding="utf-8")
    yield tam
    shutil.rmtree(tam, ignore_errors=True)


def _chay(tam: Path) -> dict:
    return lat_nguoc.chay_e1_dinh_vi(
        tam, "ma_t.py", "tests/test_ma_t.py",
        timeout_s=150.0, filter_mutate_timeout_s=90.0)


def test_duong_binh_thuong_thi_da_thu_het_va_bo_qua_khong(du_an):
    kq = _chay(du_an)
    assert kq["candidate_count_after"] > 0, "bộ lọc dòng bỏ hết ứng viên — phép đo hỏng"
    assert kq["candidate_skipped_count"] == 0
    assert kq["candidate_tried_count"] == kq["candidate_count_after"]


def test_ung_vien_no_loi_thi_phai_hien_ra_trong_so_dem(du_an, monkeypatch):
    """Chỗ lỗi gốc: gieo lỗi vào sinh mã, các ứng viên phải được ĐẾM là bỏ qua."""
    monkeypatch.setattr(
        lat_nguoc, "_ma_sau_lat",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("gieo co y")))
    kq = _chay(du_an)
    sau_loc = kq["candidate_count_after"]
    assert sau_loc > 0, "bộ lọc dòng bỏ hết ứng viên — phép đo hỏng"
    assert kq["candidate_skipped_count"] == sau_loc, (
        "ứng viên nổ lỗi biến mất im lặng: sau_lọc=%s nhưng bỏ_qua=%s"
        % (sau_loc, kq["candidate_skipped_count"])
    )
    assert kq["candidate_tried_count"] == 0
    assert kq["candidate_skipped"], "không ghi lại lý do bỏ qua"
    assert all("RuntimeError" in x["reason"] for x in kq["candidate_skipped"])


def test_ba_so_luon_khop_nhau(du_an):
    """đã_thử + bỏ_qua phải bằng sau_lọc. Nếu không thì một trong ba là số bịa."""
    kq = _chay(du_an)
    assert (kq["candidate_tried_count"] + kq["candidate_skipped_count"]
            == kq["candidate_count_after"]), kq


def test_moi_DICT_TRA_VE_trong_ma_nguon_deu_khai_du_ba_so():
    """Đọc thẳng mã nguồn: MỌI dict trả về có `candidate_count_after` phải có đủ ba số.

    Vì sao cần khẳng định trên mã nguồn chứ không chỉ chạy thử: `chay_e1_dinh_vi`
    có BỐN đường trả về (hết giờ, không có test đỏ, không tìm thấy, tìm thấy), và
    bộ test hành vi ở trên chỉ chạm được hai. Gieo thử đo được đúng chỗ hổng đó —
    bỏ ba trường khỏi một đường không bị chạm thì cửa VẪN XANH.

    Đọc bằng AST, không dò chuỗi: dò chuỗi thì một chú thích có chữ
    `candidate_count_after` cũng khớp — đúng họ bệnh ở CLAUDE.md mục 4.

    GIỚI HẠN: đây là kiểm trên mã, không phải chạy thử. Nó biết trường CÓ MẶT,
    không biết giá trị có đúng không. Giá trị thì bốn khẳng định kia canh.
    """
    import ast

    nguon = Path(lat_nguoc.__file__).read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "chay_e1_dinh_vi")

    BA_SO = {"candidate_skipped_count", "candidate_skipped", "candidate_tried_count"}
    so_dict = 0
    for nut in ast.walk(ham):
        if not isinstance(nut, ast.Dict):
            continue
        khoa = {k.value for k in nut.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "candidate_count_after" not in khoa:
            continue
        so_dict += 1
        thieu = BA_SO - khoa
        assert not thieu, (
            f"dict trả về ở dòng {nut.lineno} khai candidate_count_after nhưng "
            f"thiếu {sorted(thieu)} — bên đọc sẽ nhận None và đọc None thành 0"
        )
    assert so_dict >= 4, (
        f"chỉ thấy {so_dict} dict trả về mang candidate_count_after; "
        "hàm này có bốn đường ra — nếu ít hơn thì phép quét đã hỏng"
    )


def test_moi_cho_tra_ve_deu_khai_du_ba_so(du_an, monkeypatch):
    """Hợp đồng phải đồng nhất — kể cả các đường trả về sớm.

    Bên đọc không được phải đoán xem trường có mặt hay không; thiếu trường thì
    ``.get()`` trả None và None lại bị đọc thành 0.
    """
    # đường trả về sớm: không có test đỏ nào -> chưa vào vòng lật
    (du_an / "tests" / "test_ma_t.py").write_text(
        TEST_DO.replace("== 'lon'", "== 'vua'"), encoding="utf-8")
    kq = _chay(du_an)
    for khoa in ("candidate_skipped_count", "candidate_skipped", "candidate_tried_count"):
        assert khoa in kq, f"đường trả về sớm thiếu trường {khoa}: {sorted(kq)}"
