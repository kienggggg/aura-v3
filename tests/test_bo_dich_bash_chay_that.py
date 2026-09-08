# -*- coding: utf-8 -*-
"""Bản dịch bash phải CHẠY RA ĐÚNG SỐ, không chỉ parse được.

Đăng ký ở `KY_LUAT_THUC_THI.md` §5e (07/09/2026), chép TAY xuống đây.

VÌ SAO CÓ TỆP NÀY
-----------------
Phòng `epsilon` hỏi `bash -n` — tức chỉ hỏi **cú pháp**. Một bản dịch parse
được mà tính sai vẫn xanh, đúng họ bệnh `x in y` đã ghi 7 lần trong
`SO_BENH_AN.md`. Đo 07/09 trước khi vá:

    bash  3/3 đề GÃY cú pháp, 3/3 GÃY hành vi
    js    3/3 đạt cú pháp,    3/3 đạt hành vi   <- ca đối chứng

`javascript` đi qua **cùng bộ khung** `PythonToPolyglotVisitor` mà đạt cả hai,
nên cái hỏng nằm ở nhánh `bash`, không nằm ở bộ khung. Ca đối chứng ấy giữ
nguyên trong tệp này: nếu một ngày cả hai cùng đỏ thì lỗi ở máy đo, không phải
ở bộ dịch.

VÌ SAO PHÉP ĐO HÀNH VI Ở ĐÂY MÀ KHÔNG Ở TRONG PHÒNG `epsilon`
-------------------------------------------------------------
Đầu vào của `epsilon` là **mã do người ngoài gửi**. Dịch nó sang bash rồi CHẠY
tức là chạy mã người ngoài — đúng rủi ro đã ghi cho `/api/polyglot/run`. Nâng
`epsilon` từ *kiểm cú pháp* lên *chạy thật* sẽ biến một phòng dịch thành một
phòng thực thi mà không ai đăng ký điều đó.

Nên ba đề dưới đây do chính mình gõ ra và cố định; `epsilon` vẫn chỉ `bash -n`.
Hai chỗ, hai mức, nói rõ mức nào ở đâu.
"""
from __future__ import annotations

import re
import subprocess
import sys
import textwrap

import pytest

from core.phong_noi_bo import _tim_trinh
from core.polyglot import chuyen_doi_ngon_ngu

# ĐỀ CHỌN XONG TRƯỚC KHI BIẾT KẾT QUẢ, gõ thẳng vào đây chứ không đọc từ đâu về.
# `fib` là ĐÚNG đoạn mã `card_polyglot_transpiler` đang gửi vào phòng `epsilon`.
DAC_TA_BASH_DE = {
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

# Chép tay từ §5e. Không có mức "gần đạt".
DAC_TA_BASH_CU_PHAP_TOI_THIEU = 3
DAC_TA_BASH_HANH_VI_TOI_THIEU = 3

TRAN_GIAY = 30


def _chay(lenh, cwd, tep) -> tuple:
    r = subprocess.run(lenh + [tep.name], capture_output=True, text=True,
                       timeout=TRAN_GIAY, encoding="utf-8", errors="replace",
                       cwd=str(cwd))
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def _dich_va_ghi(ma: str, lang: str, duoi: str, thu_muc):
    kq = chuyen_doi_ngon_ngu(ma, "python", lang)
    ban = kq.get("ma_dich", "")
    tep = thu_muc / f"ban_dich{duoi}"
    # `newline="\n"` — bash bác tệp CRLF với lỗi `$'\r': command not found`,
    # và trên Windows `write_text` mặc định sinh CRLF. Đây là biến thứ ba của
    # bài "cùng mã, hai phán quyết".
    tep.write_text(ban, encoding="utf-8", newline="\n")
    return kq, ban, tep


@pytest.mark.parametrize("ten_de", sorted(DAC_TA_BASH_DE))
@pytest.mark.parametrize("lang,duoi,co_kiem", [("bash", ".sh", "bash"),
                                               ("javascript", ".js", "node")])
def test_ban_dich_chay_ra_dung_so_nhu_ban_python(ten_de, lang, duoi, co_kiem,
                                                 tmp_path):
    """Chạy THẬT bản dịch, so `stdout` từng byte với bản Python cùng lượt.

    KHÔNG gõ cứng `"55"` vào đây. Gõ cứng thì đề đổi mà kỳ vọng không đổi, và
    bài trở thành một câu khẳng định về quá khứ.
    """
    trinh = _tim_trinh(co_kiem)
    if not trinh:
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: máy này không có `{co_kiem}`")

    ma = DAC_TA_BASH_DE[ten_de]
    tep_py = tmp_path / "goc.py"
    tep_py.write_text(ma, encoding="utf-8")
    rc_py, mong_doi, loi_py = _chay([sys.executable], tmp_path, tep_py)
    assert rc_py == 0, f"chính bản Python chạy lỗi: {loi_py}"
    assert mong_doi, "bản Python không in ra gì — đề này không đo được hành vi"

    _, ban, tep = _dich_va_ghi(ma, lang, duoi, tmp_path)
    assert ban.strip(), f"{lang}: bộ dịch trả về rỗng"

    # BẢN DỊCH KHÔNG ĐƯỢC GỌI NGƯỢC LẠI PYTHON. Một "bản dịch" chỉ gồm
    # `python goc.py` sẽ ra đúng số và qua sạch bài này — đúng bẫy tautological
    # đã dính ba lần (02/09, 04/09, 06/09).
    #
    # BỎ CHÚ THÍCH TRƯỚC KHI DÒ. Bản đầu viết `"python" not in ban.lower()` và
    # ĐỎ CẢ 6 LƯỢT, vì dòng đầu bản dịch là *"Chuyển đổi tự động từ Python sang
    # Bash"* — chữ "python" nằm trong lời kể, không phải trong lệnh. Đúng bệnh
    # `x in y` mà chính bài này sinh ra để chống, mắc ngay trong lượt viết nó.
    ma_song = "\n".join(d.split("//")[0].split("#")[0] for d in ban.splitlines())
    assert not re.search(r"\bpython[\d.]*\b", ma_song, re.I), (
        f"{lang}: bản dịch gọi lại python — {ma_song[:120]}")

    rc, ra, loi = _chay([trinh], tmp_path, tep)
    assert rc == 0, f"{lang}/{ten_de}: chạy lỗi — {loi.splitlines()[0][:160] if loi else rc}"
    assert ra == mong_doi, (
        f"{lang}/{ten_de}: bản dịch ra {ra!r}, bản Python ra {mong_doi!r}")


@pytest.mark.parametrize("ten_de", sorted(DAC_TA_BASH_DE))
def test_ban_dich_bash_qua_duoc_bash_n(ten_de, tmp_path):
    """Câu hỏi CÚ PHÁP, tách hẳn khỏi câu hỏi hành vi.

    Hai câu này không được gộp: đây là đúng phép mà phòng `epsilon` chạy, nên
    nó phải đứng riêng để một ngày hành vi hỏng còn đọc ra được là hỏng ở đâu.
    """
    trinh = _tim_trinh("bash")
    if not trinh:
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này không có `bash`")
    _, ban, tep = _dich_va_ghi(DAC_TA_BASH_DE[ten_de], "bash", ".sh", tmp_path)
    rc, _, loi = _chay([trinh, "-n"], tmp_path, tep)
    assert rc == 0, f"bash -n bác {ten_de}: {loi.splitlines()[0][:160] if loi else rc}"


def test_dem_du_ba_de_dung_nguong_da_dang_ky(tmp_path):
    """Đếm lại tổng, để một `skip` lặng lẽ không đi qua thành 'đạt'.

    Ba bài trên chạy riêng từng đề. Nếu hai đề bị `skip` mà một đề xanh thì
    bảng kết quả vẫn toàn dấu chấm — bài này là chỗ con số phải khớp ngưỡng
    đã chép tay: 3 cú pháp và 3 hành vi, không có mức giữa.
    """
    trinh = _tim_trinh("bash")
    if not trinh:
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này không có `bash`")

    cu_phap = hanh_vi = 0
    hong = []
    for ten_de, ma in sorted(DAC_TA_BASH_DE.items()):
        d = tmp_path / ten_de
        d.mkdir()
        tep_py = d / "goc.py"
        tep_py.write_text(ma, encoding="utf-8")
        _, mong_doi, _ = _chay([sys.executable], d, tep_py)
        _, _, tep = _dich_va_ghi(ma, "bash", ".sh", d)
        if _chay([trinh, "-n"], d, tep)[0] == 0:
            cu_phap += 1
        rc, ra, _ = _chay([trinh], d, tep)
        if rc == 0 and ra == mong_doi:
            hanh_vi += 1
        else:
            hong.append(f"{ten_de} (ra {ra!r}, cần {mong_doi!r})")

    assert cu_phap >= DAC_TA_BASH_CU_PHAP_TOI_THIEU, f"cú pháp {cu_phap}/3"
    assert hanh_vi >= DAC_TA_BASH_HANH_VI_TOI_THIEU, (
        f"hành vi {hanh_vi}/3 — còn hỏng: {'; '.join(hong)}")


def test_go_DA_TRA_NO_va_dac_ta_phai_mang_phep_do():
    """`go` đã trả nợ 08/09/2026 — và bài này đổi chiều cùng lúc với đặc tả.

    Bản trước của bài này đòi §5e còn câu *"`go` KHÔNG ĐỘNG TỚI TRONG LƯỢT
    NÀY"*, để lượt sau đừng đọc rồi tưởng `go` đã xong. Nay `go` xong thật —
    có trình biên dịch trên máy, có phép đo — nên **câu ấy phải đi, và bài này
    phải đi theo cùng lúc**. Vá một nửa của một cặp thì phá vỡ sự ăn khớp của
    chúng (bài học 06/09 chiều).

    Điều được canh vẫn y nguyên, chỉ đổi chiều: **đừng khai `go` đã xong nếu
    không có phép đo kèm theo.** Nên bài này đòi đặc tả mang đúng con số nền
    và con số sau khi vá — xoá câu khai thì dễ, xoá con số thì lộ.
    """
    from core.paths import PROJECT_ROOT

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(r"<!-- CHOT:bo-dich-go -->(.*?)<!-- /CHOT:bo-dich-go -->",
                  spec, re.S)
    assert m, "mất neo CHOT:bo-dich-go — `go` không được khai là xong mà không có đặc tả"
    khoi = m.group(1)
    for cum in ("0/3",                 # nền: chưa từng biên dịch được
                "3/3",                 # sau khi vá
                "go1.27.1",            # bản trình biên dịch đã dùng
                "a3911b5e",            # SHA-256 đã so trước khi bung
                "non-declaration statement outside function body"):
        assert cum in khoi, f"khối bo-dich-go mất {cum!r}"
