# -*- coding: utf-8 -*-
"""Năm phòng nội bộ phải ĐO, không được GÕ TAY.

Bốn con số của `gamma` trước 03/09/2026, và số thật đo cùng ngày::

    RAM        4.2 GB / 16.0 GB    thật: 9,11 / 12,61 GB
    Hard Gates 714/714 tests       thật: 692 tests lúc ấy
    Tốc độ     38.4 tokens/giây    thật: 5,02–6,69 tok/s (thổi 5,7–7,6 lần)
    Latency    42 ms               chưa từng đo

Nên cửa quan trọng nhất ở đây không phải "hàm chạy được" mà là **số nó trả về
có khớp một phép đọc ĐỘC LẬP không**. Khẳng định `so_test == so_test` thì gõ tay
kiểu gì cũng lọt — đúng bẫy tautological đã trả giá 02/09.
"""
from __future__ import annotations

import ast
import ctypes
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402
from core.phong_noi_bo import (PHONG, dem_test, do_ram, phong_beta,  # noqa: E402
                               phong_delta, phong_gamma, phong_omega, phong_zeta,
                               quet_ast)

# Bốn chuỗi này KHÔNG được xuất hiện trong phần mã nữa.
SO_GO_TAY = ("4.2 GB", "16.0 GB", "714/714", "38.4 tokens", "42 ms",
             "9.4/10", "Perplexity", "120 BPM", "-14 LUFS")


def test_du_nam_phong():
    assert set(PHONG) == {"beta", "delta", "gamma", "omega", "zeta"}


def _ma_khong_chu_thich(p: Path) -> str:
    """Trả về phần MÃ CHẠY ĐƯỢC, bỏ chú thích và chuỗi tài liệu.

    Bản đầu của bài này lọc bằng cách bỏ dòng bắt đầu bằng `#`, và nó đỏ ngay —
    vì chuỗi tài liệu của `phong_noi_bo.py` CỐ Ý chép lại bốn con số giả cũ để
    ghi lại bằng chứng. Đó là chỗ chúng NÊN xuất hiện.

    `ast.unparse` bỏ chú thích giúp; docstring thì phải gỡ tay. Lọc bằng cấu
    trúc, không lọc bằng đoán chuỗi — đúng bài học `x in y`.
    """
    cay = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                          ast.AsyncFunctionDef)) and n.body:
            d = n.body[0]
            if (isinstance(d, ast.Expr) and isinstance(d.value, ast.Constant)
                    and isinstance(d.value.value, str)):
                n.body.pop(0)
                if not n.body:
                    n.body.append(ast.Pass())
    return ast.unparse(ast.fix_missing_locations(cay))


def test_khong_con_con_so_nao_go_tay_trong_NAM_PHONG():
    """Bốn con số giả của `gamma` và ba của `beta`/`omega` phải biến mất."""
    than = _ma_khong_chu_thich(PROJECT_ROOT / "core" / "phong_noi_bo.py")
    for s in SO_GO_TAY:
        assert s not in than, f"phong_noi_bo.py còn số gõ tay trong phần MÃ: {s!r}"


def test_duong_dispatch_khong_con_so_go_tay():
    """Chỉ soi hàm `api_dieu_phoi_phong` — đường mà bảy phòng đi qua."""
    cay = ast.parse((PROJECT_ROOT / "interface" / "noi_bo_api.py").read_text(encoding="utf-8"))
    ham = next((n for n in ast.walk(cay)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "api_dieu_phoi_phong"),
               None)
    assert ham is not None, "không tìm thấy api_dieu_phoi_phong"
    than = ast.unparse(ham)
    for s in SO_GO_TAY:
        assert s not in than, f"đường dispatch còn số gõ tay: {s!r}"


def test_ghi_nhan_api_chay_pipeline_VAN_CON_GIA():
    """`api_chay_pipeline` vẫn gõ tay `"trang_thai": "PASS"` — CHƯA sửa.

    Đo 03/09/2026: 91 dòng, **5 lần** gõ tay `PASS`, không gọi phòng nào, nhưng
    CÓ ghi vào `so_cai.jsonl` — tức nó để lại dấu vết của việc chưa từng xảy ra.

    Bài này không đòi nó phải thật. Nó ĐÓNG ĐINH con số 5, để lần sau ai sửa thì
    phải sửa cả đây — và để món nợ này không lặng lẽ trôi đi. Xoá bài này mà
    không sửa `api_chay_pipeline` là giấu nợ.
    """
    cay = ast.parse((PROJECT_ROOT / "interface" / "noi_bo_api.py").read_text(encoding="utf-8"))
    ham = next((n for n in ast.walk(cay)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "api_chay_pipeline"), None)
    assert ham is not None
    than = ast.unparse(ham)
    assert than.count("'trang_thai': 'PASS'") == 5, (
        "số lần gõ tay PASS trong api_chay_pipeline đã đổi — nếu vừa sửa nó "
        "thành thật thì xoá bài này đi, còn nếu chưa thì cập nhật con số")
    assert "PHONG[" not in than, "nếu nó đã gọi phòng thật thì bài này lỗi thời"


def test_bo_loc_chu_thich_that_su_bo_duoc():
    """Ca đối chứng cho chính bộ lọc — nếu nó bỏ nhầm cả mã thì bài trên vô nghĩa."""
    than = _ma_khong_chu_thich(PROJECT_ROOT / "core" / "phong_noi_bo.py")
    assert "GlobalMemoryStatusEx" in than, "bộ lọc nuốt mất cả phần mã"
    assert "tests collected" in than, "bộ lọc nuốt mất cả phần mã"
    assert "phòng ĐO LƯỜNG" not in than, "bộ lọc chưa bỏ được chuỗi tài liệu"


# ----------------------------------------------------------- GAMMA: đối chiếu

class _MEM(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def test_RAM_khop_phep_doc_DOC_LAP():
    """Đọc lại RAM bằng đường riêng của bài test, rồi so.

    Đây là chỗ chống tautological: không gọi `do_ram()` hai lần rồi so với chính
    nó. Bài test tự dựng struct và tự gọi Win32.
    """
    kq = do_ram()
    if not kq["do_duoc"]:
        pytest.skip(f"không đo được RAM: {kq.get('vi_sao')}")

    m = _MEM()
    m.dwLength = ctypes.sizeof(_MEM)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    tong_that = m.ullTotalPhys / 1e9

    assert abs(kq["tong_gb"] - tong_that) < 0.05, (
        f"RAM tổng báo {kq['tong_gb']} GB, đọc độc lập {tong_that:.2f} GB")
    assert 0 <= kq["phan_tram"] <= 100
    assert 0 < kq["dang_dung_gb"] <= kq["tong_gb"]


def test_dem_test_khop_pytest_collect_only():
    kq = dem_test()
    if not kq["do_duoc"]:
        pytest.skip(f"không đếm được: {kq.get('vi_sao')}")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--collect-only"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(PROJECT_ROOT), timeout=180)
    m = re.search(r"(\d+) tests? collected", r.stdout or "")
    assert m, "không đếm được độc lập"
    assert kq["so_test"] == int(m.group(1)), (
        f"phòng báo {kq['so_test']}, đếm độc lập {m.group(1)}")

    # BỎ `assert so_test != 714` ngày 03/09/2026, ngay sau khi viết nó.
    #
    # 714 là con số GIẢ mà mã cũ in ra. Nhưng tôi thêm chính bộ test này vào và
    # số THẬT lên đúng 714 — khẳng định ấy sập, `assert 714 != 714`. Nó chưa bao
    # giờ phân biệt được "trả hằng số giả" với "đo đúng ra 714"; phép so với
    # phép đếm độc lập ngay trên mới là cửa. Neo một bài test vào giá trị mà
    # mình muốn TRÁNH thì có ngày sự thật đi qua đúng chỗ ấy.


def test_gamma_do_duoc_mot_phan_van_PHAI_noi_phan_khong_do_duoc(tmp_path, monkeypatch):
    """Đo được 2/3 thì vẫn PASS, nhưng phần thiếu phải nói RA, không nuốt."""
    monkeypatch.setattr("core.phong_noi_bo.do_toc_do_model",
                        lambda: {"do_duoc": False, "vi_sao": "gieo: Ollama tắt"})
    kq = phong_gamma("thu_gamma_mot_phan")
    assert kq["trang_thai"] == "PASS"
    assert "không đo được" in kq["vi_sao"] and "toc_do" in kq["vi_sao"], kq["vi_sao"]


def test_gamma_khong_do_duoc_gi_thi_KHONG_CHAY_DUOC(monkeypatch):
    """Ba trạng thái: hỏng hết ≠ 'đã đo, không sao'."""
    for ten in ("do_ram", "dem_test", "do_toc_do_model"):
        monkeypatch.setattr(f"core.phong_noi_bo.{ten}",
                            lambda: {"do_duoc": False, "vi_sao": "gieo"})
    kq = phong_gamma("thu_gamma_hong_het")
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq["trang_thai"]


# ------------------------------------------------------------- DELTA: quét AST

def test_delta_BAT_duoc_loi_cu_phap_gieo_vao(tmp_path):
    """Quét AST phải chứng minh nó biết nói KHÔNG."""
    tot = tmp_path / "tot.py"
    tot.write_text("def a():\n    return 1\n", encoding="utf-8")
    hong = tmp_path / "hong.py"
    hong.write_text("def a(\n    return 1\n", encoding="utf-8")

    sach = quet_ast([tot])
    assert sach["loi_cu_phap"] == [] and sach["so_ham"] == 1, sach

    ban = quet_ast([tot, hong])
    assert len(ban["loi_cu_phap"]) == 1, ban["loi_cu_phap"]
    assert ban["loi_cu_phap"][0]["tep"] == "hong.py"
    assert ban["loi_cu_phap"][0]["dong"], "phải nói lỗi ở DÒNG nào"


def test_delta_dem_ham_va_lop_dung():
    """Ca đối chứng cho chính phép đếm — so với `ast` gọi tay."""
    p = PROJECT_ROOT / "core" / "phong_noi_bo.py"
    kq = quet_ast([p])
    cay = ast.parse(p.read_text(encoding="utf-8"))
    ham = sum(1 for n in ast.walk(cay)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    lop = sum(1 for n in ast.walk(cay) if isinstance(n, ast.ClassDef))
    assert (kq["so_ham"], kq["so_lop"]) == (ham, lop)


def test_delta_tep_khong_doc_duoc_khong_bi_gop_vao_loi_cu_phap(tmp_path):
    kq = quet_ast([tmp_path / "khong-co-that.py"])
    assert kq["loi_cu_phap"] == []
    assert len(kq["khong_doc_duoc"]) == 1, kq


def test_delta_chay_that_va_de_lai_hien_vat():
    kq = phong_delta("thu_delta")
    assert kq["trang_thai"] in ("PASS", "FAIL")
    assert len(kq["artifacts"]) == 1
    a = kq["artifacts"][0]
    p = PROJECT_ROOT / a["path"]
    assert p.is_file() and p.stat().st_size == a["size_bytes"]
    import hashlib
    assert hashlib.sha256(p.read_bytes()).hexdigest() == a["sha256"]
    assert kq["so"]["so_tep"] > 0 and kq["so"]["tong_dong"] > 0


# ------------------------------------------------------------- OMEGA: sổ cái

def test_omega_KHONG_lay_so_cai_lam_bang_chung_cua_minh():
    """Mọi phòng đều ghi vào `so_cai.jsonl`, nên nó không chứng minh được gì.

    `tools/do_trang_thai_phong.py` cố ý loại tệp ấy ra khỏi ảnh chụp bằng chứng.
    Omega lấy dòng sổ của mình làm bằng chứng thì phòng nào cũng "đạt".
    """
    kq = phong_omega("thu_omega")
    assert kq["trang_thai"] == "PASS", kq["vi_sao"]
    ten = [a["name"] for a in kq["artifacts"]]
    assert "so_cai.jsonl" not in ten, "lấy chính sổ cái làm hiện vật"
    assert ten == ["bao_cao_so_cai.md"], ten


def test_omega_dem_dong_khop_dem_tay():
    from core.phong_noi_bo import SO_CAI
    if not SO_CAI.is_file():
        pytest.skip("chưa có sổ cái")
    kq = phong_omega("thu_omega_dem")
    tay = len(SO_CAI.read_text(encoding="utf-8", errors="replace").splitlines())
    assert kq["so"]["so_dong"] == tay, f"phòng báo {kq['so']['so_dong']}, đếm tay {tay}"


def test_omega_khong_co_so_cai_thi_KHONG_CHAY_DUOC(monkeypatch, tmp_path):
    monkeypatch.setattr("core.phong_noi_bo.SO_CAI", tmp_path / "khong-co.jsonl")
    kq = phong_omega("thu_omega_thieu")
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq["trang_thai"]


# --------------------------------------------------------------- ZETA: biên nhận

def test_zeta_mat_mang_thi_KHONG_CHAY_DUOC(monkeypatch):
    monkeypatch.setattr("core.web_search.mang_co_song", lambda *a, **k: False)
    kq = phong_zeta("thu_zeta_mat_mang", "gì đó")
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC"
    assert kq["artifacts"] == []


def test_zeta_tra_duoc_ma_KHONG_co_nguon_la_FAIL_khong_phai_PASS(monkeypatch):
    """Chạy được mà kết quả rỗng thì phòng ĐÃ chạy — đó là FAIL, không phải
    KHÔNG CHẠY ĐƯỢC, và tuyệt đối không phải PASS."""
    class _Rong:
        sources: list = []

    monkeypatch.setattr("core.web_search.mang_co_song", lambda *a, **k: True)
    monkeypatch.setattr("core.web_search.search", lambda *a, **k: _Rong())
    kq = phong_zeta("thu_zeta_rong", "gì đó")
    assert kq["trang_thai"] == "FAIL", kq["trang_thai"]
    assert len(kq["artifacts"]) == 1, "vẫn phải để lại biên nhận để soi"


def test_zeta_bien_nhan_mang_URL_va_BAM_noi_dung(monkeypatch):
    class _Nguon:
        def __init__(self, u, t):
            self.url, self.title, self.text = u, t, "noi dung gia lap"

    class _Kq:
        sources = [_Nguon("https://vi.wikipedia.org/wiki/A", "A"),
                   _Nguon("https://vnexpress.net/b", "B")]

    monkeypatch.setattr("core.web_search.mang_co_song", lambda *a, **k: True)
    monkeypatch.setattr("core.web_search.search", lambda *a, **k: _Kq())
    kq = phong_zeta("thu_zeta_bien_nhan", "câu hỏi")
    assert kq["trang_thai"] == "PASS"
    d = json.loads((PROJECT_ROOT / kq["artifacts"][0]["path"]).read_text(encoding="utf-8"))
    assert d["so_nguon"] == 2 and d["truy_van"] == "câu hỏi"
    import hashlib
    for n in d["nguon"]:
        assert n["url"].startswith("http"), n
        assert n["sha256_noi_dung"] == hashlib.sha256(
            "noi dung gia lap".encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ BETA: A/B

def test_beta_NOI_RA_khi_N_qua_nho_de_ket_luan(monkeypatch):
    """N=1 mỗi biến thể không kết luận được gì — phòng phải tự nói, không im."""
    monkeypatch.setattr("core.viet_truyen._xin_model",
                        lambda loi, hat: ("Cau mot ngan. " * 30, 1.0))
    kq = phong_beta("thu_beta_n1", so_lan=1)
    assert kq["trang_thai"] == "PASS"
    assert kq["so"]["du_de_ket_luan"] is False
    assert "CHƯA đủ" in kq["so"]["ghi_chu"], kq["so"]["ghi_chu"]
    assert kq["vi_sao"], "ghi chú phải lọt ra tới `vi_sao`, không nằm im trong `so`"


def test_beta_N_du_thi_KHONG_con_canh_bao(monkeypatch):
    """Ca đối chứng: bài trên phải xanh vì N nhỏ, không phải vì luôn cảnh báo."""
    monkeypatch.setattr("core.viet_truyen._xin_model",
                        lambda loi, hat: ("Cau mot ngan. " * 30, 1.0))
    kq = phong_beta("thu_beta_n3", so_lan=3)
    assert kq["so"]["du_de_ket_luan"] is True
    assert kq["so"]["ghi_chu"] == ""


def test_beta_moi_luot_hong_thi_KHONG_CHAY_DUOC(monkeypatch):
    def _no(loi, hat):
        raise RuntimeError("gieo: Ollama tắt")

    monkeypatch.setattr("core.viet_truyen._xin_model", _no)
    kq = phong_beta("thu_beta_hong", so_lan=1)
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq["trang_thai"]


def test_beta_chay_dung_HAI_bien_the(monkeypatch):
    goi = []
    monkeypatch.setattr("core.viet_truyen._xin_model",
                        lambda loi, hat: (goi.append(loi), ("Cau mot ngan. " * 30, 1.0))[1])
    kq = phong_beta("thu_beta_hai", so_lan=2)
    assert len(goi) == 4, f"2 biến thể × 2 lượt = 4 lượt gọi, thực tế {len(goi)}"
    assert len(set(goi)) == 2, "hai biến thể phải KHÁC nhau"
    assert any("15 từ" in g for g in goi), "biến thể B phải có ràng buộc độ dài câu"
    assert any("15 từ" not in g for g in goi), "biến thể A phải KHÔNG có ràng buộc ấy"


def test_day_chuyen_delta_NGHE_phan_quyet_cua_quet_ast(monkeypatch):
    """Bơm một phán quyết BÁC vào `quet_ast` rồi chạy cả `phong_delta`.

    Gieo 03/09/2026 bắt được chỗ mù: đổi `if so["loi_cu_phap"]:` thành
    `if False:` mà cả 23 bài vẫn xanh. Lý do: bài chấm gọi thẳng hàm thuần
    `quet_ast(...)` — hàm ấy vẫn trả đúng lỗi — còn kho thì KHÔNG có tệp nào lỗi
    cú pháp, nên nhánh ấy trong `phong_delta` chưa từng chạy.

    Lần thứ SÁU cùng hình dạng trong ngày (âm thanh · phụ đề · nung · quãng câm ·
    bản-đã-cắt · và đây). Chấm được một hàm không chứng minh kết quả của nó đi
    tới đâu.
    """
    monkeypatch.setattr(
        "core.phong_noi_bo.quet_ast",
        lambda cac_tep: {"so_tep": 1, "tong_dong": 1, "so_ham": 0, "so_lop": 0,
                         "loi_cu_phap": [{"tep": "gieo.py", "dong": 1, "loi": "gieo"}],
                         "khong_doc_duoc": []})
    kq = phong_delta("thu_delta_bom_bac")
    assert kq["trang_thai"] == "FAIL", (
        f"quét AST BÁC mà dây chuyền vẫn {kq['trang_thai']} — phán quyết không "
        "đi tới `trang_thai`")
    assert "gieo.py" in kq["vi_sao"], f"tên tệp lỗi không lọt ra: {kq['vi_sao']!r}"


def test_doi_chung_delta_khong_bom_thi_PASS():
    """Không bơm gì thì cùng đường ấy phải PASS — thiếu ca này thì bài trên có
    thể xanh chỉ vì `phong_delta` luôn FAIL."""
    kq = phong_delta("thu_delta_khong_bom")
    assert kq["trang_thai"] == "PASS", kq["vi_sao"]
    assert kq["so"]["loi_cu_phap"] == []
