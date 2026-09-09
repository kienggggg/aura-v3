# -*- coding: utf-8 -*-
"""Bộ dịch Python → Rust và C++: BIÊN DỊCH THẬT rồi so số.

Đăng ký ở `KY_LUAT_THUC_THI.md` mục *"Bộ dịch `rust` và `cpp`"* (09/09/2026),
chép TAY xuống đây.

NỢ NÀY MỞ TỪ 04/09 với một câu đúng: *"máy này không có rustc/g++, nên mọi câu
về bản dịch Rust/C++ chỉ là ĐỌC THẤY"*. Sếp duyệt cài 09/09.

    ĐO NỀN (g++ 16.2.0 · rustc thật)   cpp 0/3 · 0/3      rust 0/3 · 0/3

VÀ "ĐỌC THẤY" LẠI CHỈ BẮT ĐƯỢC MỘT PHẦN — y như Go 08/09:

    đọc thấy trước khi cài:
        rust  `fn fibonacci(n)` thiếu kiểu tham số và kiểu trả về
        rust  câu lệnh `let mut nums = ...` ở cấp module
        cpp   `std::cout << ...` ở cấp tệp
        cpp   `auto fibonacci(auto n)` đệ quy với kiểu trả về suy diễn
    CHỈ LỘ KHI CÓ TRÌNH THẬT:
        rust  `return n` bị dịch thành `n` TRẦN — early-return biến mất, hàm
              luôn chạy xuống nhánh đệ quy. LỖI NGỮ NGHĨA, nặng hơn lỗi biên
              dịch, và một cửa chỉ hỏi cú pháp không bao giờ thấy.

VÌ SAO PHẢI CHẠY, KHÔNG CHỈ HỎI CÚ PHÁP: bài bash 06/09 — `bash -n` gật đầu
trong khi bản dịch đã đánh rơi cả vòng lặp. `g++ -fsyntax-only` cũng sẽ gật
đúng kiểu ấy.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from core.phong_noi_bo import _tim_trinh
from core.polyglot import chuyen_doi_ngon_ngu

# ĐỀ y hệt bộ `bash`/`node`/`go` — cùng đề thì mới so được giữa các ngôn ngữ.
DAC_TA_DE = {
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

# Chép tay từ đặc tả. Nền là 0/3 cho cả hai, nên 2/3 vẫn là hỏng.
DAC_TA_CU_PHAP_TOI_THIEU = 3
DAC_TA_HANH_VI_TOI_THIEU = 3
TRAN_GIAY = 300

# `(ngôn ngữ, đuôi tệp, tên trình, cờ dựng ra tệp chạy được)`
BO_DICH = {
    "cpp": (".cpp", "g++", ["-std=c++20", "-o"]),
    "rust": (".rs", "rustc", ["-o"]),
}


def _trinh(lang: str) -> str:
    duoi, ten, _ = BO_DICH[lang]
    duong = _tim_trinh(ten)
    if not duong:
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: máy này không có `{ten}`")
    return duong


@pytest.mark.parametrize("lang", sorted(BO_DICH))
def test_TIM_trinh_KHONG_duoc_phu_thuoc_MOI_PATH(lang):
    """Máy CÓ trình biên dịch mà `_tim_trinh` không thấy là lỗi của mình.

    BẪY TAUTOLOGICAL, bắt được bằng phép gieo (09/09). Gỡ `g++` khỏi
    `_CHO_TIM` thì các bài trên **bỏ qua** và cả tệp xanh — vì `_tim_trinh`
    vừa là máy dò vừa là thứ bị dò. Một máy CÓ g++ mà mã tìm hỏng đọc ra y hệt
    một máy KHÔNG có g++. Cùng họ với `_co_ollama` (08/09) và `test_TIM_go...`.

    Bài này hỏi ĐĨA trước, rồi mới hỏi `_tim_trinh`. Và nó là bài PATH của sổ
    bệnh án viết thành mã: `D:\\sdk\\...` KHÔNG nằm trên PATH, nên `_CHO_TIM`
    là thứ duy nhất tìm được.
    """
    import shutil

    _, ten, _ = BO_DICH[lang]
    tren_dia = {
        "g++": Path(r"D:\sdk\winlibs\mingw64\bin\g++.exe"),
        "rustc": Path(r"D:\sdk\rustup\toolchains"
                      r"\stable-x86_64-pc-windows-gnu\bin\rustc.exe"),
    }[ten]
    if not tren_dia.is_file():
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: máy này chưa cài {ten} vào {tren_dia}")
    if shutil.which(ten):
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: `{ten}` đã lên PATH nên bài này không "
                    f"còn đo được `_CHO_TIM`")
    assert _tim_trinh(ten), (
        f"`{ten}` CÓ trên đĩa nhưng `_tim_trinh` không thấy — nó không nằm "
        f"trên PATH, nên `_CHO_TIM` là thứ duy nhất tìm được. Thiếu chỗ đó thì "
        f"mọi bài {lang} tụt về KHÔNG ĐO ĐƯỢC và cả tệp xanh trong khi chưa "
        f"đo gì.")


def test_DAC_TA_rust_cpp_van_o_lai_tai_lieu():
    """Con số tạo ra luật phải ở lại cùng luật.

    Bài này sinh ra vì phép gieo: xoá neo `CHOT:bo-dich-rust-cpp` mà cả tệp
    vẫn xanh. Tôi viết khối đặc tả có neo rồi **quên viết cửa đọc nó** — lần
    thứ hai trong hai ngày. Một cái neo không ai kéo thì chỉ là chữ.
    """
    import re

    from core.paths import PROJECT_ROOT

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(r"<!-- CHOT:bo-dich-rust-cpp -->(.*?)"
                  r"<!-- /CHOT:bo-dich-rust-cpp -->", spec, re.S)
    assert m, "mất neo CHOT:bo-dich-rust-cpp trong đặc tả"
    khoi = m.group(1)
    for cum in ("0/3",                    # nền: chưa từng biên dịch được
                "3/3",                    # sau khi vá
                "c1f52294",               # SHA-256 WinLibs đã so
                "6f4bef66",               # SHA-256 rustup đã so
                "w64devkit",              # vì sao KHÔNG chọn nó
                "KIEU_KHONG_SUY_DUOC"):   # `any` của Rust cố ý không tồn tại
        assert cum in khoi, f"khối bo-dich-rust-cpp mất {cum!r}"


def _python_noi_gi(ma: str) -> str:
    """Bản Python là CHUẨN ĐỐI CHIẾU và nó phải CHẠY THẬT.

    Gõ tay kết quả mong đợi thì hai vế cùng do một người viết, và một bản dịch
    sai sẽ khớp với một kỳ vọng cũng sai.
    """
    r = subprocess.run([sys.executable, "-c", ma], capture_output=True,
                       text=True, timeout=TRAN_GIAY, encoding="utf-8",
                       errors="replace")
    assert r.returncode == 0, f"chính bản Python đã hỏng: {r.stderr[:300]}"
    return (r.stdout or "").strip()


def _dich_bien_dich_chay(lang: str, ma: str, thu_muc: Path):
    """Trả `(mã thoát biên dịch, stderr, đầu ra khi chạy, bản dịch)`."""
    duoi, _, co = BO_DICH[lang]
    trinh = _trinh(lang)
    ban = chuyen_doi_ngon_ngu(ma, "python", lang).get("ma_dich", "")
    tep = thu_muc / ("main" + duoi)
    # `newline="\n"`: Windows sinh CRLF mặc định — biến thứ ba của bài "cùng
    # mã, hai phán quyết" mà bash đã trả giá.
    tep.write_text(ban, encoding="utf-8", newline="\n")
    ra = thu_muc / "ra.exe"
    b = subprocess.run([trinh, *co, str(ra), str(tep)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=TRAN_GIAY, cwd=str(thu_muc))
    if b.returncode != 0:
        return b.returncode, (b.stderr or ""), None, ban
    r = subprocess.run([str(ra)], capture_output=True, text=True,
                       timeout=TRAN_GIAY, encoding="utf-8", errors="replace")
    return 0, "", (r.stdout or "").strip(), ban


@pytest.mark.parametrize("lang", sorted(BO_DICH))
@pytest.mark.parametrize("ten_de", sorted(DAC_TA_DE))
def test_ban_dich_BIEN_DICH_va_chay_ra_dung_so(lang, ten_de, tmp_path):
    """Nền: cú pháp 0/3, hành vi 0/3 cho cả hai. Sau khi vá: 3/3 và 3/3."""
    ma = DAC_TA_DE[ten_de]
    mong = _python_noi_gi(ma)
    ma_thoat, loi, that, ban = _dich_bien_dich_chay(lang, ma, tmp_path)
    assert ma_thoat == 0, (
        f"trình biên dịch bác bản dịch {lang}/{ten_de}:\n{loi[:700]}\n"
        f"--- bản dịch ---\n{ban}")
    assert that == mong, (
        f"{lang} chạy ra {that!r}, Python nói {mong!r}\n"
        f"--- bản dịch ---\n{ban}")


@pytest.mark.parametrize("lang", sorted(BO_DICH))
def test_dem_du_ba_de_dung_nguong_da_dang_ky(lang, tmp_path):
    """Đếm lại tổng, để một `skip` lặng lẽ không đi qua thành "đạt".

    Ba bài trên chạy riêng từng đề. Hai đề bị `skip` mà một đề xanh thì bảng
    kết quả đọc ra như "Rust đã xong" — bài này bắt đúng chỗ ấy.
    """
    _trinh(lang)
    cu_phap = hanh_vi = 0
    for ten, ma in sorted(DAC_TA_DE.items()):
        d = tmp_path / f"{lang}_{ten}"
        d.mkdir()
        mong = _python_noi_gi(ma)
        ma_thoat, _, that, _ = _dich_bien_dich_chay(lang, ma, d)
        if ma_thoat != 0:
            continue
        cu_phap += 1
        hanh_vi += that == mong
    assert cu_phap >= DAC_TA_CU_PHAP_TOI_THIEU, (
        f"{lang}: cú pháp {cu_phap}/3, đặc tả đòi "
        f"{DAC_TA_CU_PHAP_TOI_THIEU} (nền 0/3)")
    assert hanh_vi >= DAC_TA_HANH_VI_TOI_THIEU, (
        f"{lang}: hành vi {hanh_vi}/3, đặc tả đòi "
        f"{DAC_TA_HANH_VI_TOI_THIEU} (nền 0/3)")


def test_RUST_early_return_khong_duoc_thanh_bieu_thuc_TRAN():
    """Lỗi NGỮ NGHĨA, và nó chỉ lộ ra khi chạy — không lộ khi hỏi cú pháp.

    Bản cũ dịch `return n` thành `n` trần, nên:

        if n <= 1 { n }                              <- biểu thức bị VỨT ĐI
        fibonacci(n - 1) + fibonacci(n - 2)          <- LUÔN chạy tới đây

    Trong Rust chỉ biểu thức CUỐI hàm mới là giá trị trả về. Đây đúng họ với
    `while` dịch sang bash mà vòng lặp biến mất (06/09) — thứ mà `bash -n` gật.

    Bài này KHÔNG cần `rustc`: nó chấm dạng bản dịch, nên đỏ được cả trên máy
    chưa cài Rust.
    """
    ban = chuyen_doi_ngon_ngu(DAC_TA_DE["fib"], "python", "rust")["ma_dich"]
    assert "return n;" in ban, (
        f"early-return của Rust lại thành biểu thức trần:\n{ban}")
    # Ca đối chứng: đừng "sửa" bằng cách nhét `return` vào mọi chỗ.
    assert ban.count("return ") == 2, (
        f"đề `fib` có đúng 2 câu `return` trong Python, bản dịch có "
        f"{ban.count('return ')}:\n{ban}")


@pytest.mark.parametrize("lang", sorted(BO_DICH))
def test_CAU_LENH_CAP_TEP_deu_nam_trong_ham_main(lang):
    """Lỗi nền chung của cả ba ngôn ngữ biên dịch, và nó CHẶN NGAY DÒNG ĐẦU.

    Không kiểm bằng trình biên dịch — bài này chấm một quy tắc ngữ pháp nên nó
    phải đỏ được cả trên máy chưa cài gì.
    """
    ban = chuyen_doi_ngon_ngu(DAC_TA_DE["tong_vong"], "python", lang)["ma_dich"]
    mo = {"cpp": "int main() {", "rust": "fn main() {"}[lang]
    assert mo in ban, f"không có hàm main:\n{ban}"
    dau = ban.index(mo)
    for d in ban[:dau].splitlines():
        d = d.rstrip()
        if not d or d.startswith(("//", "#include", "    ", "\t", "}")):
            continue
        assert d.startswith(("int ", "fn ", "auto ", "void ", "std::", "use ")), (
            f"câu lệnh ở cấp tệp, trước `main` — {lang} không cho: {d!r}\n{ban}")


@pytest.mark.parametrize("lang", sorted(BO_DICH))
def test_KIEU_khong_suy_duoc_thi_PHAI_NOI_RA(lang):
    """Bộ suy kiểu HẸP, và chỗ nó bó tay phải tự khai.

    `bo_sot` khác rỗng thì phòng `epsilon` trả KHÔNG ĐO ĐƯỢC và **không đưa
    cho trình biên dịch** — nên một bản dịch đoán kiểu không bao giờ được chấm
    ĐẠT. Im lặng để kiểu mơ hồ là thứ làm một bản dịch hỏng trông như xong.
    """
    kq = chuyen_doi_ngon_ngu(
        "def bao(x):\n    return x\n\nprint(bao(1))\n", "python", lang)
    assert any("không suy được" in s for s in kq.get("bo_sot", [])), (
        f"để kiểu mơ hồ mà không nói ra: bo_sot = {kq.get('bo_sot')}")
