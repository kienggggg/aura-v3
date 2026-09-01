# -*- coding: utf-8 -*-
"""Bộ chạy đa ngôn ngữ không được hứa "cô lập", và không được báo đỗ khi chưa chạy.

VÌ SAO CÓ TỆP NÀY. 01/09/2026, đọc `core/polyglot.py` (972 dòng, do một AI khác
viết) thì thấy sáu chỗ hứa *"thực thi an toàn trong môi trường CÔ LẬP"* — hai
trong số đó hiện thẳng lên màn hình. Chạy thử qua chính hàm ấy:

    CWD                       D:/AURA_v3   (gốc kho, không phải thư mục tạm)
    USER                      baloa        (đủ quyền tài khoản Windows)
    liệt kê thư mục HOME      86 mục       (đọc được)
    GHI TỆP NGOÀI thư mục tạm              ĐƯỢC

Chỉ có một trần thời gian. `CLAUDE.md` mục 7 luật 3: *"Cô lập", "sandbox",
"không có quyền" — ba chữ ấy người đọc sẽ TIN, và tin sai thì mất tệp.*

Và chỗ đắt hơn: nhánh cho ngôn ngữ CHƯA CÀI TOOLCHAIN trả `status: "PASS"`,
`exit_code: 0`, in ra *"[AURA Polyglot Engine Sandbox] … đạt tiêu chuẩn biên
dịch"*. Đo thật với mã CỐ Ý HỎNG:

    go    fmt.Println(1/0)   -> PASS exit 0
    rust  panic!("no")       -> PASS exit 0
    cpp   return 1           -> PASS exit 0
    sql   SELECT 1/0         -> PASS exit 0
    bash  exit 3             -> PASS exit 0   (máy CÓ bash!)
    ts    (hợp lệ)           -> PASS exit 0

Sáu trên sáu báo đỗ trong khi không chương trình nào từng chạy, và giao diện vẽ
huy hiệu XANH "EXIT CODE 0" cho cả sáu. Đúng fake-PASS mà `KY_LUAT_THUC_THI.md`
cấm, và đúng ba-trạng-thái-gộp-thành-hai ở CLAUDE.md mục 4.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT
from core.polyglot import chay_ma_da_ngon_ngu

# Ngôn ngữ và một đoạn mã HỢP CÚ PHÁP nhưng SAI khi chạy — để phân biệt
# "chạy rồi thấy sai" với "chưa chạy bao giờ".
MA_HONG_KHI_CHAY = {
    "go": 'package main\nimport "fmt"\nfunc main(){ fmt.Println(1) }',
    "rust": 'fn main(){ panic!("no"); }',
    "cpp": "#include <iostream>\nint main(){ return 1; }",
    "sql": "SELECT 1;",
    "bash": "exit 3",
    "typescript": "const x: number = 1;",
}
TOOLCHAIN = {"go": "go", "rust": "rustc", "cpp": "g++", "sql": "sqlite3",
             "bash": "bash", "typescript": "node"}


@pytest.mark.parametrize("lang", sorted(MA_HONG_KHI_CHAY))
def test_chua_cai_toolchain_thi_KHONG_duoc_bao_dat(lang):
    """Chưa chạy thì phải nói là chưa chạy — không phải `PASS`."""
    r = chay_ma_da_ngon_ngu(MA_HONG_KHI_CHAY[lang], lang, timeout_s=8)
    if r.get("simulated") is not True:
        pytest.skip(f"máy này có toolchain cho {lang} nên đi đường chạy thật")
    assert r["status"] != "PASS", (
        f"`{lang}` chưa hề chạy mà báo PASS. Giao diện đọc `status === 'PASS'` "
        "rồi vẽ huy hiệu xanh — người dùng bấm CHẠY và nhận về màu xanh cho "
        "thứ chưa chạy."
    )
    assert r["status"] == "KHONG_CHAY_DUOC"
    assert r["exit_code"] is None, (
        "`exit_code: 0` cũng là một lời khai đỗ. Chưa chạy thì không có mã "
        "thoát nào cả."
    )
    assert not r["stdout"], "chưa chạy thì không có gì để in ra stdout"
    assert "KHÔNG CHẠY ĐƯỢC" in r["stderr"]
    assert "CHƯA HỀ CHẠY" in r["stderr"], (
        "câu giải thích phải nói RÕ là chương trình không chạy, không chỉ nói "
        "'thiếu công cụ' rồi để người dùng tự suy"
    )


def test_ba_trang_thai_TACH_ROI():
    """đạt · đo được mà không đạt · KHÔNG ĐO ĐƯỢC — gộp hai là mất một."""
    dat = chay_ma_da_ngon_ngu("print('ok')", "python", timeout_s=8)
    truot = chay_ma_da_ngon_ngu("raise SystemExit(3)", "python", timeout_s=8)
    chua = chay_ma_da_ngon_ngu("package main\nfunc main(){}", "go", timeout_s=8)
    if chua.get("simulated") is not True:
        pytest.skip("máy này có Go nên không dựng được trạng thái thứ ba")
    ba = {dat["status"], truot["status"], chua["status"]}
    assert len(ba) == 3, f"ba trạng thái chập lại còn {len(ba)}: {ba}"
    assert dat["status"] == "PASS" and dat["exit_code"] == 0
    assert truot["status"] == "FAIL" and truot["exit_code"] == 3


@pytest.mark.parametrize("lang, ma", [("python", "print('chay that')"),
                                      ("javascript", "console.log('chay that')")])
def test_hai_ngon_ngu_CO_duong_chay_that_van_chay(lang, ma):
    """Ca đối chứng: sửa nhãn không được làm hỏng hai đường chạy thật."""
    r = chay_ma_da_ngon_ngu(ma, lang, timeout_s=15)
    if lang == "javascript" and not shutil.which("node"):
        pytest.skip("máy này không có node")
    assert r["status"] == "PASS", f"{lang} không chạy được nữa: {r}"
    assert r["exit_code"] == 0
    assert "chay that" in r["stdout"], "phải là đầu ra THẬT của chương trình"
    assert r.get("simulated") is not True


# Những chỗ người đọc/người dùng gặp câu hứa. Không quét cả repo: chữ
# "Sandbox" còn là TÊN MỘT PHÒNG của Beta trong `noi_bo_api.py`, hợp lệ.
TEP_CAN_SACH = [
    "core/polyglot.py",
    "interface/noi_bo_api.py",
    "interface/web/noi_bo.html",
    "interface/web/noi_bo.js",
]


@pytest.mark.parametrize("ten", TEP_CAN_SACH)
def test_khong_con_cau_hua_CO_LAP_quanh_viec_chay_ma(ten):
    nguon = Path(PROJECT_ROOT, ten).read_text(encoding="utf-8")
    # MIỄN TRỪ HẸP NHẤT CÓ THỂ: chỉ bỏ dòng TRÍCH LẠI câu cũ (`trước đây`).
    #
    # Bản đầu miễn trừ rộng hơn — bỏ mọi dòng có "KHÔNG có hộp cát" hoặc
    # "CLAUDE.md". Gieo thử chứng minh nó MÙ: phụ đề trong `noi_bo.html` nằm
    # TRÊN CÙNG MỘT DÒNG với câu "KHÔNG có hộp cát", nên nhét lại "sandbox an
    # toàn" vào đầu dòng ấy thì cả dòng bị lọc đi và cửa không thấy gì.
    #
    # Miễn trừ theo DÒNG luôn có chỗ hở kiểu đó. Cách chắc hơn: viết lời cải
    # chính sao cho nó KHÔNG chứa nguyên văn cụm bị cấm — đã kiểm, mọi câu tôi
    # thêm đều thoả.
    dong = [d for d in nguon.split("\n")
            if "TRƯỚC ĐÂY" not in d and "trước đây" not in d]
    ma = "\n".join(dong)
    for cum in ("môi trường cô lập", "tiến trình cô lập", "sandbox an toàn",
                "Chạy Thử (Sandbox)", "THỰC THI SANDBOX"):
        assert cum not in ma, (
            f"`{ten}` còn hứa {cum!r}. Đo 01/09: mã chạy ở gốc kho với đủ "
            "quyền tài khoản Windows và ghi được tệp ra ngoài thư mục tạm — "
            "chỉ có một trần thời gian, không có cô lập nào."
        )
