# -*- coding: utf-8 -*-
"""Bộ dịch Python → Go: CHẠY THẬT rồi so số, không chỉ hỏi cú pháp.

Đăng ký ở `KY_LUAT_THUC_THI.md` mục *"Bộ dịch `go` — trả nợ 08/09/2026"*, chép
TAY xuống đây.

NỢ NÀY MỞ TỪ 06/09 với đúng một câu: *"máy không có trình biên dịch Go"*. Sếp
duyệt cài 08/09, nên nó chuyển từ **KHÔNG ĐO ĐƯỢC** sang **đo được** — và đo
xong thì ra 0/3, tức nó chưa từng chạy được lần nào.

    ĐO NỀN (go1.27.1 thật)     cú pháp 0/3   ·   hành vi 0/3
    main.go:15:1: syntax error: non-declaration statement outside function body

BỐN LỖI, VÀ LỖI ĐẦU CHE BA LỖI KIA. Parser dừng ở dòng 15 nên ba cái sau chưa
từng được trình biên dịch nhìn thấy:

    1. không có `func main()`      Go cấm câu lệnh ngoài thân hàm
    2. tên khai ≠ tên gọi          khai `func Fibonacci`, gọi `fibonacci(...)`
    3. `:=` ở cấp gói              `nums := []any{...}` ngoài hàm
    4. số học trên `any`           `n <= 1`, `tong += x` — Go không có toán tử

VÌ SAO PHẢI CHẠY, KHÔNG CHỈ HỎI CÚ PHÁP. Bài bash 06/09: `bash -n` gật đầu
trong khi bản dịch đã **đánh rơi cả vòng lặp**. `gofmt -e` cũng sẽ gật đúng
kiểu ấy. Chỉ có chạy rồi so đầu ra với bản Python mới bắt được.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from core.phong_noi_bo import _tim_trinh
from core.polyglot import chuyen_doi_ngon_ngu

# ĐỀ y hệt bộ `bash`/`node` — cùng đề thì mới so được giữa các ngôn ngữ.
DAC_TA_GO_DE = {
    "fib": textwrap.dedent('''\
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        print(fibonacci(10))
        '''),
    "tong_vong": textwrap.dedent('''\
        def tinh_tong(ds):
            tong = 0
            for x in ds:
                tong += x
            return tong

        nums = [1, 2, 3, 4, 5]
        print(tinh_tong(nums))
        '''),
    "if_else": textwrap.dedent('''\
        def phan_loai(diem):
            if diem >= 90:
                return "gioi"
            else:
                return "thuong"

        print(phan_loai(95))
        print(phan_loai(40))
        '''),
}

# Chép tay từ đặc tả. Không có mức "gần đạt" — nền là 0/3, nên 2/3 vẫn là hỏng.
DAC_TA_GO_CU_PHAP_TOI_THIEU = 3
DAC_TA_GO_HANH_VI_TOI_THIEU = 3
TRAN_GIAY = 180


def _go():
    trinh = _tim_trinh("go")
    if not trinh:
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này không có trình biên dịch Go")
    return trinh


def test_TIM_go_KHONG_duoc_phu_thuoc_MOI_PATH():
    """Máy CÓ Go mà `_tim_trinh` không thấy là lỗi của mình, không phải thiếu công cụ.

    BẪY TAUTOLOGICAL, bắt được bằng phép gieo (08/09). Gỡ `go` khỏi `_CHO_TIM`
    thì mọi bài trên **bỏ qua** và cả tệp xanh — vì `_tim_trinh` vừa là máy dò
    vừa là thứ bị dò. Một máy CÓ Go mà mã tìm hỏng đọc ra y hệt một máy KHÔNG
    có Go.

    Bài này hỏi ĐĨA trước, rồi mới hỏi `_tim_trinh`. Và nó là bài PATH của sổ
    bệnh án viết thành mã: `~/go-sdk/go/bin` KHÔNG nằm trên PATH, nên nếu
    `shutil.which` trượt mà `_tim_trinh` cũng trượt thì `_CHO_TIM` đang không
    làm việc gì cả.
    """
    import shutil

    tren_dia = Path.home() / "go-sdk" / "go" / "bin" / "go.exe"
    if not tren_dia.is_file():
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: máy này chưa cài Go vào {tren_dia}")
    if shutil.which("go"):
        pytest.skip("KHÔNG ĐO ĐƯỢC: `go` đã lên PATH nên bài này không còn "
                    "đo được `_CHO_TIM`")
    for ten in ("go", "gofmt"):
        assert _tim_trinh(ten), (
            f"`{ten}` CÓ trên đĩa nhưng `_tim_trinh` không thấy — nó không "
            f"nằm trên PATH, nên `_CHO_TIM` là thứ duy nhất tìm được nó. "
            f"Thiếu chỗ đó thì mọi bài Go tụt về KHÔNG ĐO ĐƯỢC và cả tệp "
            f"xanh trong khi chưa đo gì.")


def _dich(ma: str, thu_muc: Path) -> tuple:
    kq = chuyen_doi_ngon_ngu(ma, "python", "go")
    ban = kq.get("ma_dich", "")
    tep = thu_muc / "main.go"
    # `newline="\n"` — Windows sinh CRLF mặc định. Đây là biến thứ ba của bài
    # "cùng mã, hai phán quyết" mà bash đã trả giá.
    tep.write_text(ban, encoding="utf-8", newline="\n")
    return kq, ban, tep


def _python_noi_gi(ma: str) -> str:
    """Bản Python là CHUẨN ĐỐI CHIẾU, và nó phải CHẠY THẬT.

    Gõ tay kết quả mong đợi vào đây thì hai vế cùng do một người viết ra, và
    một bản dịch sai sẽ khớp với một kỳ vọng cũng sai.
    """
    r = subprocess.run([sys.executable, "-c", ma], capture_output=True,
                       text=True, timeout=TRAN_GIAY, encoding="utf-8",
                       errors="replace")
    assert r.returncode == 0, f"chính bản Python đã hỏng: {r.stderr[:300]}"
    return (r.stdout or "").strip()


@pytest.mark.parametrize("ten_de", sorted(DAC_TA_GO_DE))
def test_ban_dich_go_BIEN_DICH_va_chay_ra_dung_so(ten_de, tmp_path):
    """Nền: cú pháp 0/3, hành vi 0/3. Sau khi vá: 3/3 và 3/3."""
    go = _go()
    ma = DAC_TA_GO_DE[ten_de]
    mong = _python_noi_gi(ma)
    _, ban, tep = _dich(ma, tmp_path)

    ra = tmp_path / "ra.exe"
    b = subprocess.run([go, "build", "-o", str(ra), str(tep)],
                       capture_output=True, text=True, timeout=TRAN_GIAY,
                       cwd=str(tmp_path), encoding="utf-8", errors="replace")
    assert b.returncode == 0, (
        f"`go build` bác bản dịch {ten_de}:\n{(b.stderr or '')[:600]}\n"
        f"--- bản dịch ---\n{ban}")

    r = subprocess.run([str(ra)], capture_output=True, text=True,
                       timeout=TRAN_GIAY, encoding="utf-8", errors="replace")
    assert (r.stdout or "").strip() == mong, (
        f"Go chạy ra {r.stdout!r}, Python nói {mong!r}\n"
        f"--- bản dịch ---\n{ban}")


def test_dem_du_ba_de_dung_nguong_da_dang_ky(tmp_path):
    """Đếm lại tổng, để một `skip` lặng lẽ không đi qua thành "đạt".

    Ba bài trên chạy riêng từng đề. Nếu hai đề bị `skip` mà một đề xanh thì
    bảng kết quả đọc ra như "Go đã xong" — bài này bắt đúng chỗ ấy.
    """
    go = _go()
    cu_phap = hanh_vi = 0
    for ten, ma in sorted(DAC_TA_GO_DE.items()):
        d = tmp_path / ten
        d.mkdir()
        mong = _python_noi_gi(ma)
        _, _, tep = _dich(ma, d)
        ra = d / "ra.exe"
        if subprocess.run([go, "build", "-o", str(ra), str(tep)],
                          capture_output=True, timeout=TRAN_GIAY,
                          cwd=str(d)).returncode != 0:
            continue
        cu_phap += 1
        r = subprocess.run([str(ra)], capture_output=True, text=True,
                           timeout=TRAN_GIAY, encoding="utf-8",
                           errors="replace")
        hanh_vi += (r.stdout or "").strip() == mong

    assert cu_phap >= DAC_TA_GO_CU_PHAP_TOI_THIEU, (
        f"cú pháp {cu_phap}/3, đặc tả đòi {DAC_TA_GO_CU_PHAP_TOI_THIEU} (nền 0/3)")
    assert hanh_vi >= DAC_TA_GO_HANH_VI_TOI_THIEU, (
        f"hành vi {hanh_vi}/3, đặc tả đòi {DAC_TA_GO_HANH_VI_TOI_THIEU} (nền 0/3)")


def test_KIEU_khong_suy_duoc_thi_PHAI_NOI_RA(tmp_path):
    """Bộ suy kiểu HẸP, và chỗ nó bó tay phải tự khai.

    Ca đối chứng của bộ suy kiểu: một hàm mà kiểu KHÔNG suy được (tham số chỉ
    được truyền đi chứ không so sánh, không duyệt) thì phải ra `any` **và**
    ghi vào `bo_sot`. Im lặng để `any` là thứ làm một bản dịch hỏng trông như
    bản dịch xong — Go không có toán tử cho `any`, nên nó sẽ gãy ở chỗ khác.
    """
    kq = chuyen_doi_ngon_ngu(
        "def bao(x):\n    return x\n\nprint(bao(1))\n", "python", "go")
    ban = kq.get("ma_dich", "")
    assert "x any" in ban, f"kiểu suy ra từ đâu?\n{ban}"
    assert any("không suy được" in s for s in kq.get("bo_sot", [])), (
        f"để `any` mà không nói ra: bo_sot = {kq.get('bo_sot')}")


def test_KIEU_suy_duoc_thi_KHONG_duoc_de_any(tmp_path):
    """Ca đối chứng chiều ngược lại: suy được mà vẫn `any` là bộ suy kiểu chết.

    Thiếu bài này thì một bộ suy kiểu "luôn trả any" vẫn qua được bài trên.
    """
    kq = chuyen_doi_ngon_ngu(DAC_TA_GO_DE["tong_vong"], "python", "go")
    ban = kq.get("ma_dich", "")
    assert "ds []int" in ban, f"`for x in ds` mà không suy ra []int:\n{ban}"
    assert "[]int{1, 2, 3, 4, 5}" in ban, f"danh sách số vẫn là []any:\n{ban}"
    assert " any" not in ban.split("func main")[0], (
        f"còn `any` trong phần hàm dù suy được hết:\n{ban}")


def test_CAU_LENH_CAP_GOI_deu_nam_trong_func_main():
    """Lỗi nền số 1, và nó CHE ba lỗi kia nên phải có bài riêng.

    Không kiểm bằng `go build` — bài này phải đỏ được cả trên máy KHÔNG có Go,
    vì nó chấm một quy tắc ngữ pháp chứ không chấm một lượt chạy.
    """
    ban = chuyen_doi_ngon_ngu(DAC_TA_GO_DE["tong_vong"], "python", "go")["ma_dich"]
    dong = ban.splitlines()
    trong_ham = False
    for d in dong:
        if d.startswith("func "):
            trong_ham = True
        elif d == "}":
            trong_ham = False
        elif d.strip() and not trong_ham:
            assert (d.startswith(("//", "package ", "import ", "\t", ")"))
                    or d.startswith("var ") or d.startswith("const ")), (
                f"câu lệnh ở cấp gói — Go không cho: {d!r}\n{ban}")
    assert "func main() {" in ban, f"không có func main:\n{ban}"
