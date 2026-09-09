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
                               phong_delta, phong_epsilon, phong_gamma,
                               phong_omega, phong_zeta, quet_ast)

# Bốn chuỗi này KHÔNG được xuất hiện trong phần mã nữa.
SO_GO_TAY = ("4.2 GB", "16.0 GB", "714/714", "38.4 tokens", "42 ms",
             "9.4/10", "Perplexity", "120 BPM", "-14 LUFS")


def test_du_cac_phong_noi_bo():
    """Danh sách ĐÓNG. Thêm phòng thì phải sửa dòng này — tức phải cố ý.

    `epsilon` thêm 06/09/2026: dịch mã rồi để `node --check` / `bash -n` chấm
    bản dịch. Nó là phòng đầu tiên có VERIFIER NGOÀI TIẾN TRÌNH, và cũng là
    phòng đầu tiên đọc thật `yeu_cau`.
    """
    assert set(PHONG) == {"beta", "delta", "epsilon", "gamma", "omega", "zeta"}


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


def _than_ham(ten_ham: str, tep: str = "interface/noi_bo_api.py") -> str:
    """Phần MÃ của một hàm, đã gỡ chuỗi tài liệu của chính nó.

    Cần gỡ vì chuỗi tài liệu CỐ Ý chép lại các chuỗi giả cũ để ghi bằng chứng —
    đó là chỗ chúng NÊN xuất hiện. Bản đầu của mấy bài dưới đây đỏ đúng vì thế.
    """
    cay = ast.parse((PROJECT_ROOT / tep).read_text(encoding="utf-8"))
    ham = next((n for n in ast.walk(cay)
                if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef))
                and n.name == ten_ham), None)
    assert ham is not None, f"không tìm thấy {ten_ham}"
    d = ham.body[0]
    if (isinstance(d, ast.Expr) and isinstance(d.value, ast.Constant)
            and isinstance(d.value.value, str)):
        ham.body.pop(0)
    return ast.unparse(ast.fix_missing_locations(ham))


def test_than_ham_that_su_go_duoc_chuoi_tai_lieu():
    """Ca đối chứng cho chính bộ gỡ — gỡ nhầm cả mã thì mọi bài dưới vô nghĩa."""
    t = _than_ham("api_chay_pipeline")
    assert "chay_chuoi_phong" in t, "bộ gỡ nuốt mất cả phần mã"
    assert "6 nguồn tin uy tín" not in t, "bộ gỡ chưa bỏ được chuỗi tài liệu"


def test_khong_con_con_so_nao_go_tay_trong_NAM_PHONG():
    """Bốn con số giả của `gamma` và ba của `beta`/`omega` phải biến mất."""
    than = _ma_khong_chu_thich(PROJECT_ROOT / "core" / "phong_noi_bo.py")
    for s in SO_GO_TAY:
        assert s not in than, f"phong_noi_bo.py còn số gõ tay trong phần MÃ: {s!r}"


def test_duong_dispatch_khong_con_so_go_tay():
    """Chỉ soi hàm `api_dieu_phoi_phong` — đường mà bảy phòng đi qua."""
    than = _than_ham("api_dieu_phoi_phong")
    for s in SO_GO_TAY:
        assert s not in than, f"đường dispatch còn số gõ tay: {s!r}"


def test_api_chay_pipeline_GOI_PHONG_THAT_khong_go_tay():
    """Thay `test_ghi_nhan_api_chay_pipeline_VAN_CON_GIA` ngày 03/09/2026.

    Bài cũ đóng đinh con số 5 — số lần gõ tay `"trang_thai": "PASS"` — và nói
    thẳng: *"nếu vừa sửa nó thành thật thì xoá bài này đi"*. Nay đã sửa, nên nó
    lỗi thời đúng như đã dự. Món nợ được ghi ra, rồi được trả, chứ không trôi.

    Bản cũ: 91 dòng, 5 lần gõ tay PASS, không gọi phòng nào, nhưng CÓ ghi vào
    `so_cai.jsonl` — dấu vết của việc chưa từng xảy ra.
    """
    than = _than_ham("api_chay_pipeline")
    chung = _than_ham("chay_chuoi_phong")

    assert "'trang_thai': 'PASS'" not in than, "còn gõ tay trạng thái PASS"
    assert "chay_chuoi_phong" in than, "không gọi bộ chạy chuỗi"
    # Logic gọi phòng nằm ở bộ chạy chung từ 04/09/2026 — hai pipeline dùng
    # chung nó để khỏi trôi khỏi nhau.
    assert "PHONG[" in chung, "bộ chạy chuỗi không gọi phòng thật"
    assert "viet_kich_ban" in chung and "dung_video" in chung, (
        "không gọi hai phòng nặng nhất — aura và alpha")
    for s_gia in ("6 nguồn tin uy tín", "1.800 từ", "100% Hard Gates",
                  "xuất sắc 100%", "-14 LUFS", "58s"):
        assert s_gia not in than, f"còn chuỗi gõ tay: {s_gia!r}"


def test_pipeline_NOI_dau_ra_cua_aura_vao_alpha():
    """Nối thật, không diễu hành.

    Năm lượt gọi phòng độc lập thì không phải dây chuyền. Kịch bản `aura` viết
    ra phải đi vào tham số `van_ban` của `dung_video`.
    """
    cay = ast.parse((PROJECT_ROOT / "interface" / "noi_bo_api.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.AsyncFunctionDef) and n.name == "chay_chuoi_phong")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and any(
               isinstance(a, ast.Name) and a.id == "dung_video" for a in ast.walk(n))]
    assert goi, "không tìm thấy lượt gọi dung_video"
    tham_so = ast.unparse(goi[0])
    assert "kich_ban" in tham_so, (
        f"`dung_video` không nhận kịch bản của aura: {tham_so}")


def test_pipeline_co_trang_thai_CHUA_CHAY_cho_buoc_khong_chay():
    """Bước không chạy phải mang trạng thái RIÊNG, không phải PASS cũng không FAIL.

    Đánh nó thành PASS thì bảng đọc ra "cả năm bước xong"; đánh thành FAIL thì
    đọc ra "nó chạy rồi mà hỏng". Cả hai đều sai theo một cách khó bắt.
    """
    assert "CHUA_CHAY" in _than_ham("chay_chuoi_phong"), (
        "bộ chạy chuỗi thiếu trạng thái cho bước không chạy")
    assert "KHONG_CHAY_DUOC" in _than_ham("trang_thai_chuoi"), (
        "phép chấm cả chuỗi thiếu trạng thái không đo được")


def test_pipeline_KHONG_nuot_loi_ghi_so_cai():
    """`except Exception: pass` quanh lượt ghi sổ là điều đặc tả cấm thẳng.

    Ghi sổ hỏng là tin đáng biết: nó nghĩa là mọi phép đo sau đó đang đọc một
    quyển sổ thiếu trang.
    """
    cay = ast.parse((PROJECT_ROOT / "interface" / "noi_bo_api.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "ghi_so_cai")
    for n in ast.walk(ham):
        if isinstance(n, ast.ExceptHandler) and len(n.body) == 1 and isinstance(n.body[0], ast.Pass):
            raise AssertionError("còn một nhánh `except: pass` nuốt lỗi")
    for goi in ("api_chay_pipeline", "api_pipeline_custom"):
        assert "loi_ghi_so" in _than_ham(goi), (
            f"{goi}: lỗi ghi sổ phải lọt ra ngoài phản hồi")


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


# ---------------------------------------------------------------------------
# PIPELINE — ĐO HÀNH VI, không dò chuỗi
#
# Bốn bài trên chỉ soi VĂN BẢN của hàm bằng `ast.unparse`. Gieo 8 phép thì
# 4 XANH, và cả bốn đều là phép đổi HÀNH VI mà không đổi chuỗi:
#
#   trang_thai = "PASS" bất kể kết quả       -> vẫn xanh
#   bước gãy không làm dừng dây chuyền       -> vẫn xanh
#   ghi sổ cái luôn "PASS"                   -> vẫn xanh
#   bỏ nhánh gộp CHUA_CHAY/KHONG_CHAY_DUOC   -> vẫn xanh
#
# Đúng lỗi `CLAUDE.md` ghi ngày 02/09: *"cả hai đều vì tôi dò chuỗi trong mã
# thay vì gọi hàm rồi xem nó trả về gì"*. Lần thứ bảy cùng hình dạng.

class _ReqGia:
    def __init__(self, d): self._d = d

    async def json(self): return self._d


def _chay_pipeline(monkeypatch, aura="DAT", alpha="PASS", cac_phong=None, chu_de="thử"):
    """Chạy `api_chay_pipeline` với mọi phòng bị thay bằng bản giả, rồi ĐỌC kết quả.

    Đếm luôn phòng nào ĐƯỢC GỌI — để bắt được ca "bước gãy mà dây chuyền vẫn
    chạy tiếp", thứ mà dò chuỗi không bao giờ thấy.
    """
    import asyncio
    import json as _json

    import interface.noi_bo_api as api

    da_goi: list = []

    def _aura(chu_de_, *a, **k):
        da_goi.append("aura")
        return {"trang_thai": aura,
                "van_ban": ("Cau mot. " * 30).strip() if aura == "DAT" else "",
                "so": {"so_tu": 60, "so_cau_khac": 30}, "so_lan_thu": 1,
                "lan": [{"vi_sao": ["gieo"]}], "ms": 1.0}

    def _alpha(thu_muc, van_ban=None, *a, **k):
        da_goi.append("alpha")
        assert van_ban, "alpha phải nhận kịch bản từ aura"
        thu_muc.mkdir(parents=True, exist_ok=True)
        return {"trang_thai": alpha, "artifacts": [], "kiem": {"so": {}},
                "ms": 1.0, "vi_sao": "gieo"}

    def _mot_phong(ten, tt):
        def _f(task_id, yeu_cau="", *a, **k):
            da_goi.append(ten)
            return {"trang_thai": tt, "artifacts": [], "so": {}, "vi_sao": "", "ms": 1.0}
        return _f

    tt_phong = cac_phong or {"zeta": "PASS", "omega": "PASS", "gamma": "PASS"}
    monkeypatch.setattr("core.viet_truyen.viet_kich_ban", _aura)
    monkeypatch.setattr("core.phong_alpha.dung_video", _alpha)
    monkeypatch.setattr("core.phong_noi_bo.PHONG",
                        {k: _mot_phong(k, v) for k, v in tt_phong.items()})

    r = asyncio.run(api.api_chay_pipeline(_ReqGia({"chu_de": chu_de})))
    return _json.loads(r.body.decode("utf-8")), da_goi


def test_pipeline_moi_buoc_dat_thi_ca_chuoi_PASS(monkeypatch):
    """Ca đối chứng — máy đo phải chứng minh nó biết nói PASS."""
    d, da_goi = _chay_pipeline(monkeypatch)
    assert d["status"] == "PASS", d["thong_diep"]
    assert d["buoc_dat"] == 5 and d["tong_buoc"] == 5
    assert da_goi == ["zeta", "aura", "alpha", "omega", "gamma"], da_goi


def test_pipeline_MOT_buoc_gay_thi_ca_chuoi_KHONG_duoc_PASS(monkeypatch):
    d, _ = _chay_pipeline(monkeypatch, alpha="FAIL")
    assert d["status"] != "PASS", "một bước FAIL mà cả chuỗi vẫn PASS"
    assert d["buoc_dat"] < 5, d["buoc_dat"]


def test_pipeline_buoc_gay_thi_DUNG_LAI_va_KHONG_goi_phong_sau(monkeypatch):
    """Bước sau phụ thuộc bước trước — chạy tiếp là đo một thứ vô nghĩa.

    Dò chuỗi không bắt được ca này: bỏ `da_gay = True` thì văn bản hàm vẫn còn
    đủ mọi chữ mà bốn bài trên tìm.
    """
    d, da_goi = _chay_pipeline(monkeypatch, aura="KHONG_DAT")
    assert "alpha" not in da_goi, f"aura gãy mà alpha vẫn được gọi: {da_goi}"
    assert "gamma" not in da_goi, f"dây chuyền không dừng: {da_goi}"
    sau = [b for b in d["cac_buoc"] if b["buoc"] > 2]
    assert all(b["trang_thai"] == "CHUA_CHAY" for b in sau), (
        f"bước sau phải mang CHUA_CHAY: {[(b['buoc'], b['trang_thai']) for b in sau]}")


def test_pipeline_CHUA_CHAY_khong_bi_dem_thanh_dat(monkeypatch):
    d, _ = _chay_pipeline(monkeypatch, aura="KHONG_DAT")
    assert d["buoc_dat"] == 1, f"chỉ zeta đạt, mà đếm ra {d['buoc_dat']}"


def test_pipeline_ghi_SO_CAI_dung_trang_thai_that(monkeypatch):
    """Sổ cái phải mang trạng thái THẬT, không phải PASS cứng.

    Đây là chỗ đắt nhất: bản cũ ghi `"status": "PASS"` cho mọi lượt, nên sổ cái
    — thứ `omega` đọc để làm báo cáo — đầy những dòng PASS của việc chưa xảy ra.
    """
    import json as _json

    from core.phong_noi_bo import SO_CAI

    truoc = SO_CAI.read_text(encoding="utf-8").count("\n") if SO_CAI.is_file() else 0
    d, _ = _chay_pipeline(monkeypatch, alpha="FAIL")
    assert SO_CAI.is_file(), "không ghi sổ cái"
    cac_dong = SO_CAI.read_text(encoding="utf-8").strip().splitlines()
    assert len(cac_dong) > truoc, "không có dòng mới nào"
    moi = _json.loads(cac_dong[-1])
    assert moi["task_id"] == d["pipeline_id"], moi
    assert moi["status"] == d["status"] != "PASS", (
        f"sổ cái ghi {moi['status']!r} còn phản hồi là {d['status']!r}")
    assert moi["buoc_dat"] == d["buoc_dat"]


def test_pipeline_khong_buoc_nao_chay_duoc_thi_KHONG_CHAY_DUOC(monkeypatch):
    """Ba trạng thái ở tầng chuỗi: hỏng hết ≠ 'đã chạy, không đạt'."""
    d, _ = _chay_pipeline(monkeypatch,
                          cac_phong={"zeta": "KHONG_CHAY_DUOC", "omega": "PASS",
                                     "gamma": "PASS"})
    assert d["cac_buoc"][0]["trang_thai"] == "KHONG_CHAY_DUOC"
    assert d["status"] == "KHONG_CHAY_DUOC", (
        f"mọi bước đều KHONG_CHAY_DUOC/CHUA_CHAY mà cả chuỗi báo {d['status']!r}")


# ---------------------------------------------------------------------------
# PIPELINE TÙY BIẾN (04/09/2026)
#
# Bản trước dài 17 dòng, lặp qua các bước người dùng gửi lên rồi dán
# `'trang_thai': 'PASS'` cho từng bước và `'status': 'PASS'` cho cả lượt — kể cả
# khi `phong_id` là một cái tên bịa. Không gọi phòng nào, không ghi byte nào.
#
# Đây là chỗ CUỐI CÙNG còn gõ tay PASS trong `noi_bo_api.py`. Tìm ra khi vẽ sơ
# đồ cây — không phải khi đọc mã, mà khi phải trả lời *"đường này có thật
# không"* cho một hình vẽ.

def _chay_custom(monkeypatch, cac_buoc, ten="thử"):
    """Gọi `api_pipeline_custom` với mọi phòng bị thay bằng bản giả."""
    import asyncio
    import json as _json

    import core.phong_alpha as _pa
    import core.phong_noi_bo as _pnb
    import core.viet_truyen as _vt
    import interface.noi_bo_api as _api

    da_goi: list = []

    def _aura(chu_de, *a, **k):
        da_goi.append("aura")
        return {"trang_thai": "DAT", "van_ban": ("Cau mot. " * 30).strip(),
                "so": {"so_tu": 60, "so_cau_khac": 30}, "so_lan_thu": 1,
                "lan": [{"vi_sao": []}], "ms": 1.0}

    def _alpha(thu_muc, van_ban=None, *a, **k):
        da_goi.append("alpha")
        assert van_ban, "alpha phải nhận kịch bản từ aura"
        thu_muc.mkdir(parents=True, exist_ok=True)
        return {"trang_thai": "PASS", "artifacts": [], "kiem": {"so": {}},
                "ms": 1.0, "vi_sao": ""}

    def _phong(task_id, yeu_cau="", *a, **k):
        da_goi.append(task_id.rsplit("_", 1)[-1])
        return {"trang_thai": "PASS", "artifacts": [], "so": {}, "vi_sao": "", "ms": 1.0}

    monkeypatch.setattr(_vt, "viet_kich_ban", _aura)
    monkeypatch.setattr(_pa, "dung_video", _alpha)
    monkeypatch.setattr(_pnb, "PHONG",
                        {k: _phong for k in ("zeta", "omega", "gamma", "beta", "delta")})
    r = asyncio.run(_api.api_pipeline_custom(_ReqGia({"ten": ten, "cac_buoc": cac_buoc})))
    return r.status, _json.loads(r.body.decode("utf-8")), da_goi


def test_custom_khong_con_go_tay_PASS():
    than = _than_ham("api_pipeline_custom")
    assert "'trang_thai': 'PASS'" not in than, "còn gõ tay trạng thái PASS"
    assert "'status': 'PASS'" not in than, "còn gõ tay status PASS"
    assert "chay_chuoi_phong" in than, "không gọi bộ chạy chuỗi thật"


def test_custom_danh_sach_RONG_la_KHONG_CHAY_DUOC(monkeypatch):
    """Chạy 0 bước rồi báo đạt là đúng bệnh cả tệp này vừa chữa."""
    st, d, goi = _chay_custom(monkeypatch, [])
    assert st == 400 and d["status"] == "KHONG_CHAY_DUOC", (st, d["status"])
    assert goi == [], "không có bước nào mà vẫn gọi phòng"


# Chép TAY từ `KY_LUAT_THUC_THI.md` Chương III, KHÔNG đọc từ mã.
#
# Bản đầu của hai bài dưới dùng `_api.TRAN_BUOC_TUY_BIEN + 1`, nên gieo `8 -> 999`
# thì ngưỡng của bài test cũng nới theo và cửa VẪN XANH. Tautological: hai vế
# cùng đổi, phép kiểm không bao giờ cãi lại được mã. Đúng bẫy đã trả giá 02/09
# với `(RONG, CAO) == (RONG, CAO)`, mắc lại đúng một ngày sau khi ghi nó vào luật.
DAC_TA_TRAN_BUOC = 8


def test_tran_buoc_trong_ma_khop_DAC_TA():
    import interface.noi_bo_api as _api

    assert _api.TRAN_BUOC_TUY_BIEN == DAC_TA_TRAN_BUOC


def test_custom_qua_TRAN_thi_CHAN_truoc_khi_chay(monkeypatch):
    """Một lượt `aura` tốn tới 273 giây — 20 bước là hơn một tiếng rưỡi."""
    st, d, goi = _chay_custom(monkeypatch,
                              [{"phong_id": "omega"}] * (DAC_TA_TRAN_BUOC + 1))
    assert st == 400 and d["status"] == "KHONG_CHAY_DUOC"
    assert goi == [], "quá trần mà vẫn chạy"


def test_custom_dung_TRAN_thi_van_chay(monkeypatch):
    """Ca đối chứng: trần là trần, không phải chặn tất cả."""
    st, d, goi = _chay_custom(monkeypatch,
                              [{"phong_id": "omega"}] * DAC_TA_TRAN_BUOC)
    assert d["status"] == "PASS", d
    assert len(goi) == DAC_TA_TRAN_BUOC


def test_custom_phong_BIA_TEN_la_FAIL_va_lam_DUNG_day_chuyen(monkeypatch):
    """Tên phòng đến từ NGƯỜI GỌI — một cái tên bịa phải kêu, không im lặng.

    Bản cũ dán PASS cho mọi `phong_id`, kể cả `"khong_co_that"`.
    """
    st, d, goi = _chay_custom(monkeypatch, [
        {"phong_id": "omega"}, {"phong_id": "khong_co_that"}, {"phong_id": "gamma"}])
    tt = [b["trang_thai"] for b in d["cac_buoc"]]
    assert tt == ["PASS", "FAIL", "CHUA_CHAY"], tt
    assert d["status"] == "FAIL" and d["buoc_dat"] == 1, d
    assert "gamma" not in goi, f"dây chuyền không dừng: {goi}"


def test_custom_NOI_aura_sang_alpha(monkeypatch):
    st, d, goi = _chay_custom(monkeypatch,
                              [{"phong_id": "aura"}, {"phong_id": "alpha"}])
    assert d["status"] == "PASS" and d["buoc_dat"] == 2, d
    assert goi == ["aura", "alpha"], goi


def test_custom_alpha_mot_minh_thi_CHUA_CHAY(monkeypatch):
    """Không có kịch bản thì alpha KHÔNG chạy — và đó không phải FAIL của alpha."""
    st, d, goi = _chay_custom(monkeypatch, [{"phong_id": "alpha"}])
    assert d["cac_buoc"][0]["trang_thai"] == "CHUA_CHAY", d["cac_buoc"]
    assert d["status"] == "KHONG_CHAY_DUOC", d["status"]
    assert goi == [], "alpha bị gọi dù không có kịch bản"


def test_custom_ghi_SO_CAI_dung_trang_thai_that(monkeypatch):
    import json as _json

    from core.phong_noi_bo import SO_CAI

    truoc = SO_CAI.read_text(encoding="utf-8").count("\n") if SO_CAI.is_file() else 0
    st, d, _ = _chay_custom(monkeypatch, [{"phong_id": "omega"},
                                          {"phong_id": "khong_co_that"}])
    cac_dong = SO_CAI.read_text(encoding="utf-8").strip().splitlines()
    assert len(cac_dong) > truoc
    moi = _json.loads(cac_dong[-1])
    assert moi["task_id"] == d["pipeline_id"]
    assert moi["status"] == d["status"] != "PASS", moi
    assert moi["phong_id"] == "pipeline_custom", moi


def test_hai_pipeline_dung_CHUNG_bo_chay_chuoi():
    """Hai bản riêng thì chúng trôi khỏi nhau — bản ít người nhìn sẽ là bản mục."""
    for ten in ("api_chay_pipeline", "api_pipeline_custom"):
        assert "chay_chuoi_phong" in _than_ham(ten), ten
        assert "trang_thai_chuoi" in _than_ham(ten), ten


def test_aura_fail_closed_som_KHONG_lam_ca_chuoi_no_500(monkeypatch):
    """`lan` RỖNG là trạng thái THẬT, và hai chỗ gọi từng đọc `lan[-1]`.

    Từ 04/09/2026 cửa nêu đề fail-closed TRƯỚC vòng lặp khi đề tài không còn từ
    nội dung nào — nên `viet_kich_ban` trả về `"lan": []`, không có lượt sinh
    nào để kể. `_kq['lan'][-1]` ở đó là `IndexError`, và một lý do bác đọc được
    biến thành sự cố 500.

    Đây là cái giá của việc thêm một trạng thái mới: mọi chỗ đọc trạng thái cũ
    phải được đi lại. Bài này canh cho lần sau.
    """
    import asyncio
    import json as _json

    import core.phong_alpha as _pa
    import core.phong_noi_bo as _pnb
    import core.viet_truyen as _vt
    import interface.noi_bo_api as _api

    def _aura_khong_do_duoc(chu_de, *a, **k):
        return {"trang_thai": "KHONG_DO_DUOC", "van_ban": "",
                "so": {"so_tu_de": 0}, "so_lan_thu": 0, "lan": [],
                "vi_sao": [f"đề {chu_de!r} không còn từ nội dung nào"],
                "ms": 1.0}

    def _alpha(thu_muc, van_ban=None, *a, **k):
        raise AssertionError("alpha không được chạy khi aura không ra kịch bản")

    monkeypatch.setattr(_vt, "viet_kich_ban", _aura_khong_do_duoc)
    monkeypatch.setattr(_pa, "dung_video", _alpha)
    monkeypatch.setattr(_pnb, "PHONG", {})

    r = asyncio.run(_api.api_pipeline_custom(_ReqGia(
        {"ten": "thử", "chu_de": "vì sao thì mà là",
         "cac_buoc": [{"phong_id": "aura"}, {"phong_id": "alpha"}]})))
    d = _json.loads(r.body.decode("utf-8"))

    assert r.status == 200, f"nổ {r.status} thay vì trả lý do đọc được"
    assert d["status"] != "PASS", d["status"]
    assert d["cac_buoc"][0]["trang_thai"] == "KHONG_DO_DUOC", d["cac_buoc"][0]
    # Lý do phải LỌT RA NGOÀI, không được thành chuỗi rỗng hay `None`.
    mo_ta = str(d["cac_buoc"][0].get("ket_qua", ""))
    assert "không còn từ nội dung nào" in mo_ta, mo_ta
    assert "None" not in mo_ta, f"lý do bác rơi mất: {mo_ta!r}"


def test_dispatch_aura_lan_RONG_van_noi_ro_ly_do(monkeypatch):
    """Chỗ vá THỨ HAI. Vá một chỗ rồi tưởng xong là bệnh cũ.

    `viet_kich_ban` được gọi từ HAI đường: `chay_chuoi_phong` (bài ở trên) và
    `api_dieu_phoi_phong`. Cả hai đều đọc `lan` của nó. Đường thứ hai không
    `IndexError` — nó nối chuỗi rỗng — nên nó hỏng LẶNG HƠN: người dùng nhận
    một câu báo lỗi không có lý do nào trong đó.
    """
    import asyncio
    import json as _json

    import core.viet_truyen as _vt
    import interface.noi_bo_api as _api

    def _aura_khong_do_duoc(chu_de, *a, **k):
        return {"trang_thai": "KHONG_DO_DUOC", "van_ban": "",
                "so": {"so_tu_de": 0}, "so_lan_thu": 0, "lan": [],
                "vi_sao": [f"đề {chu_de!r} không còn từ nội dung nào"],
                "ms": 1.0}

    monkeypatch.setattr(_vt, "viet_kich_ban", _aura_khong_do_duoc)
    r = asyncio.run(_api.api_dieu_phoi_phong(_ReqGia(
        {"phong_id": "aura", "yeu_cau": "vì sao thì mà là"})))
    d = _json.loads(r.body.decode("utf-8"))

    assert r.status == 200, f"nổ {r.status} thay vì trả lý do đọc được"
    assert d["status"] != "PASS", d["status"]
    noi_dung = str(d)
    assert "không còn từ nội dung nào" in noi_dung, (
        f"lý do bác không lọt ra ngoài: {noi_dung[:300]}")


# ---------------------------------------------------------------------------
# THẺ KHAI THỂ LOẠI (05/09/2026)
#
# Đo 2×2: `lời truyện × đề giải thích` chỉ đạt 1/5, `lời bài nói × đề giải
# thích` đạt 3/5. Thẻ đã biết mình làm gì, nên nó khai — không cần máy đoán.
#
# `preset_id` TRƯỚC 05/09 chỉ được ghi vào sổ cái rồi vứt: đo bằng cách gọi
# `api_chay_pipeline` với cả 8 `preset_id` thì cả 8 chạy Y MỘT chuỗi 5 phòng.
# Khai thêm một trường mà không ai đọc là thêm trường trang trí thứ chín.
# ---------------------------------------------------------------------------

# Chép TAY từ KY_LUAT_THUC_THI.md mục 1b, "HAI THỂ LOẠI LỜI NHẮC".
DAC_TA_THE_LOAI_HOP_LE = ("bai_noi", "truyen")


def test_moi_the_goi_aura_deu_KHAI_the_loai():
    """Thẻ nào dùng `aura` mà không khai thì đang chạy mặc định trong im lặng."""
    import interface.noi_bo_api as _api

    thieu = [t["id"] for t in _api.DANH_SACH_THE_QUY_TRINH
             if "aura" in t["cac_phong"] and "the_loai" not in t]
    assert not thieu, f"thẻ gọi aura mà chưa khai thể loại: {thieu}"


def test_the_loai_khai_deu_NAM_TRONG_danh_sach_hop_le():
    """Gõ nhầm `"bainoi"` trong thẻ thì `viet_kich_ban` sẽ NÉM — bắt sớm ở đây."""
    import interface.noi_bo_api as _api

    for t in _api.DANH_SACH_THE_QUY_TRINH:
        if "the_loai" in t:
            assert t["the_loai"] in DAC_TA_THE_LOAI_HOP_LE, (
                f"{t['id']} khai {t['the_loai']!r}")


def test_tra_the_loai_KHONG_no_voi_preset_la():
    """Đường của giao diện: `preset_id` lạ không được làm đổ cả chuỗi.

    Khác hẳn `viet_kich_ban`, nơi thể loại lạ NÉM — ở đó là lập trình viên gõ
    sai nên phải nổ to; ở đây là dữ liệu từ ngoài vào.
    """
    from interface.noi_bo_api import the_loai_cua_the

    assert the_loai_cua_the(None) == "truyen"
    assert the_loai_cua_the("") == "truyen"
    assert the_loai_cua_the("khong_co_that") == "truyen"

    # Ca đối chứng: hàm phải ĐỌC ĐƯỢC thứ thẻ khai, không phải luôn trả mặc
    # định. Bơm một thẻ vào thay vì dựa vào thẻ thật — nếu không thì
    # `return "truyen"` vô điều kiện cũng qua bài này.
    #
    # `card_fullstack_builder` khai `bai_noi` từ 06/09/2026 (đo ghép đôi 5 hạt
    # trên chính đề của nó: truyen 0/5, bai_noi 4/5). Nhưng bài này vẫn bơm thẻ
    # giả: dựa vào một thẻ thật thì cửa chết theo lần sửa danh mục tiếp theo.
    import interface.noi_bo_api as _api

    goc = _api.DANH_SACH_THE_QUY_TRINH
    try:
        _api.DANH_SACH_THE_QUY_TRINH = list(goc) + [
            {"id": "the_thu_bai_noi", "cac_phong": ["aura"],
             "the_loai": "bai_noi"}]
        assert the_loai_cua_the("the_thu_bai_noi") == "bai_noi"
    finally:
        _api.DANH_SACH_THE_QUY_TRINH = goc


def test_the_loai_DI_TOI_viet_kich_ban_that_su(monkeypatch):
    """Chấm được một hàm không chứng minh kết quả của nó đi tới đâu.

    Bài này bắt THAM SỐ THẬT mà `viet_kich_ban` nhận được khi chạy cả chuỗi,
    chứ không gọi `the_loai_cua_the` rồi tự khen. Gieo bỏ khâu truyền tham số
    thì soi văn bản hàm vẫn xanh — đó là cửa mù.
    """
    import asyncio

    import core.phong_alpha as _pa
    import core.phong_noi_bo as _pnb
    import core.viet_truyen as _vt
    import interface.noi_bo_api as _api

    da_thay = []

    def _aura(chu_de, *a, the_loai="truyen", **k):
        da_thay.append(the_loai)
        return {"trang_thai": "DAT", "van_ban": ("Cau mot. " * 30).strip(),
                "so": {"so_tu": 60, "so_cau_khac": 30}, "so_lan_thu": 1,
                "lan": [{"vi_sao": []}], "ms": 1.0}

    def _alpha(thu_muc, van_ban=None, *a, **k):
        thu_muc.mkdir(parents=True, exist_ok=True)
        return {"trang_thai": "PASS", "artifacts": [], "kiem": {"so": {}},
                "ms": 1.0, "vi_sao": ""}

    def _phong(task_id, yeu_cau="", *a, **k):
        return {"trang_thai": "PASS", "artifacts": [], "so": {}, "vi_sao": "",
                "ms": 1.0}

    monkeypatch.setattr(_vt, "viet_kich_ban", _aura)
    monkeypatch.setattr(_pa, "dung_video", _alpha)
    monkeypatch.setattr(_pnb, "PHONG",
                        {k: _phong for k in ("zeta", "omega", "gamma", "beta", "delta")})

    # Bơm một thẻ khai `bai_noi` thay vì dùng thẻ thật: bộ máy phải chứng minh
    # nó truyền đúng giá trị, và cửa không được chết theo lần sửa danh mục kế
    # tiếp. (`card_fullstack_builder` khai `bai_noi` từ 06/09/2026; thẻ video
    # vẫn `truyen` — rút 05/09 sau khi đo 3/3 trượt cửa độ dài trên đề của nó.)
    monkeypatch.setattr(
        _api, "DANH_SACH_THE_QUY_TRINH",
        list(_api.DANH_SACH_THE_QUY_TRINH) + [
            {"id": "the_thu_bai_noi", "cac_phong": ["aura"],
             "the_loai": "bai_noi"}])

    asyncio.run(_api.api_chay_pipeline(
        _ReqGia({"chu_de": "thử", "preset_id": "the_thu_bai_noi"})))
    assert da_thay == ["bai_noi"], da_thay

    # Ca đối chứng: thẻ truyện phải ra "truyen", nếu không bài trên chỉ chứng
    # minh rằng một hằng số nào đó luôn là "bai_noi".
    da_thay.clear()
    asyncio.run(_api.api_chay_pipeline(
        _ReqGia({"chu_de": "thử", "preset_id": "card_novel_writer"})))
    assert da_thay == ["truyen"], da_thay

    # Không gửi preset_id thì giữ hành vi cũ.
    da_thay.clear()
    asyncio.run(_api.api_chay_pipeline(_ReqGia({"chu_de": "thử"})))
    assert da_thay == ["truyen"], da_thay


# ---------------------------------------------------------------------------
# SỔ TIẾN ĐỘ — VỎ TRONG SUỐT (05/09/2026)
#
# Trước hôm nay: bấm một thẻ thì màn hình trắng 166 giây, tới 330 giây nếu AURA
# phải sinh lại. Quét cả `interface/` cho SSE/WebSocket/stream: 0 kết quả.
#
# Ngưỡng đăng ký trước ở `KE_HOACH_VO_TRONG_SUOT_2026-09-05.md`.
# ---------------------------------------------------------------------------

def _tien_do(pid):
    import asyncio
    import json as _json

    import interface.noi_bo_api as _api

    class _R:
        match_info = {"pipeline_id": pid}

        async def json(self):
            return {}

    r = asyncio.run(_api.api_doc_tien_do(_R()))
    return _json.loads(r.body.decode("utf-8"))


def test_moi_buoc_deu_len_so_tien_do(monkeypatch, tmp_path):
    """Không bước nào được vào `cac_buoc` mà vắng mặt trên sổ tiến độ.

    Bảo đảm bằng CẤU TRÚC: ba đường ghi bước (bỏ qua · phòng lạ · chạy thật)
    đều đi qua phễu `_xong_buoc`. Kỷ luật thì lần sau thêm một nhánh là vỡ.
    """
    import asyncio
    import json as _json

    import interface.noi_bo_api as _api

    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", tmp_path)
    d, goi = _chay_pipeline(monkeypatch)
    td = _tien_do(d["pipeline_id"])

    dang = [x for x in td["cac_dong"] if x["trang_thai"] == "DANG_CHAY"]
    ket = [x for x in td["cac_dong"]
           if x["trang_thai"] not in ("DANG_CHAY", "XONG")]
    xong = [x for x in td["cac_dong"] if x["trang_thai"] == "XONG"]

    assert len(ket) == d["tong_buoc"], f"{len(ket)} dòng kết / {d['tong_buoc']} bước"
    assert len(dang) == d["tong_buoc"], "thiếu dòng DANG_CHAY"
    assert len(xong) == 1, "phải có ĐÚNG một dòng XONG"
    assert td["trang_thai"] == "XONG"


def test_buoc_TREO_nhin_khac_han_buoc_CHUA_BAT_DAU(monkeypatch, tmp_path):
    """CA ĐỐI CHỨNG QUAN TRỌNG NHẤT của cả việc này.

    Một thanh tiến trình trông như đang chạy trong khi tiến trình đã chết còn
    TỆ HƠN không có gì. Nên bơm một sổ có `DANG_CHAY` mà chưa có dòng kết, rồi
    đòi API nói rõ *bước nào* và *đã trôi bao lâu*.
    """
    import json as _json
    from datetime import datetime, timedelta

    import interface.noi_bo_api as _api

    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", tmp_path)
    luc = (datetime.now().astimezone() - timedelta(seconds=6)).isoformat()
    (tmp_path / "pipe_treo.jsonl").write_text(
        _json.dumps({"buoc": 1, "phong_id": "zeta", "phong_ten": "Zeta",
                     "trang_thai": "DANG_CHAY", "luc": luc},
                    ensure_ascii=False) + "\n", encoding="utf-8")

    td = _tien_do("pipe_treo")
    assert td["trang_thai"] == "DANG_CHAY", td["trang_thai"]
    assert td["buoc_dang_chay"]["phong_id"] == "zeta"
    assert td["giay_da_troi"] >= 5.0, td["giay_da_troi"]

    # Ca đối chứng: CHƯA có sổ nào thì phải là KHÔNG ĐO ĐƯỢC, không phải
    # "đang chạy". Ba trạng thái, không gộp.
    trong = _tien_do("pipe_chua_co")
    assert trong["trang_thai"] == "KHONG_DO_DUOC"
    assert trong["buoc_dang_chay"] is None
    assert trong["giay_da_troi"] is None


def test_buoc_da_XONG_thi_khong_con_bao_dang_chay(monkeypatch, tmp_path):
    """Có dòng kết đôi thì bước ấy phải thôi được tính là đang chạy."""
    import json as _json
    from datetime import datetime

    import interface.noi_bo_api as _api

    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", tmp_path)
    luc = datetime.now().astimezone().isoformat()
    (tmp_path / "pipe_xong.jsonl").write_text("\n".join(
        _json.dumps(x, ensure_ascii=False) for x in [
            {"buoc": 1, "phong_id": "zeta", "trang_thai": "DANG_CHAY", "luc": luc},
            {"buoc": 1, "phong_id": "zeta", "trang_thai": "PASS", "luc": luc,
             "ket_qua": "", "ms": 10, "so_hien_vat": 0},
        ]) + "\n", encoding="utf-8")

    td = _tien_do("pipe_xong")
    assert td["buoc_dang_chay"] is None, td["buoc_dang_chay"]


@pytest.mark.parametrize("xau", ["../../etc/passwd", "a/b", "", "x" * 200, "a b"])
def test_pipeline_id_la_bi_CHAN_truoc_khi_cham_dia(monkeypatch, tmp_path, xau):
    """`pipeline_id` đi từ URL thẳng vào tên tệp — phải chặn đường dẫn.

    BẢN ĐẦU CỦA BÀI NÀY MÙ. Nó chỉ đòi `KHONG_DO_DUOC`, mà bỏ hẳn hàng rào thì
    `../../etc/passwd.jsonl` VẪN không tồn tại nên VẪN trả `KHONG_DO_DUOC` —
    khẳng định được thoả bởi *tệp không có*, không phải bởi *hàng rào chặn*.
    Gieo `if False:` vào chỗ chặn mà bài vẫn xanh.

    Nay bài đòi thêm LÝ DO phải là "không hợp lệ", và có ca dưới đặt một tệp mà
    đường vòng thật sự với tới được.
    """
    import interface.noi_bo_api as _api

    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", tmp_path)
    td = _tien_do(xau)
    assert td["trang_thai"] == "KHONG_DO_DUOC", (xau, td)
    assert "không hợp lệ" in td["vi_sao"], (xau, td["vi_sao"])


def test_duong_vong_KHONG_doc_duoc_tep_ngoai_thu_muc(monkeypatch, tmp_path):
    """Ca đối chứng CÓ MỒI: đặt một tệp mà `..` sẽ với tới, rồi đòi KHÔNG đọc nó.

    Không có mồi thì bài trên chỉ chứng minh "tệp không tồn tại". Có mồi thì nó
    phân biệt được hàng rào với sự may mắn.
    """
    import json as _json

    import interface.noi_bo_api as _api

    ngoai = tmp_path / "ngoai"
    ngoai.mkdir()
    (ngoai / "bimat.jsonl").write_text(
        _json.dumps({"buoc": 1, "trang_thai": "XONG", "bi_mat": "KHONG_DUOC_LO"},
                    ensure_ascii=False) + "\n", encoding="utf-8")
    trong = tmp_path / "trong"
    trong.mkdir()
    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", trong)

    # Ca đối chứng THUẬN: mồi đọc được khi đặt ĐÚNG chỗ — nếu không thì bài này
    # xanh chỉ vì đường dẫn sai, không vì hàng rào.
    (trong / "that.jsonl").write_text(
        _json.dumps({"buoc": 1, "trang_thai": "XONG"}, ensure_ascii=False) + "\n",
        encoding="utf-8")
    assert _tien_do("that")["cac_dong"], "mồi đặt đúng chỗ mà vẫn không đọc được"

    td = _tien_do("../ngoai/bimat")
    assert td["cac_dong"] == [], "ĐỌC ĐƯỢC tệp ngoài thư mục qua đường vòng"
    assert "KHONG_DUOC_LO" not in _json.dumps(td, ensure_ascii=False)


def test_ghi_tien_do_HONG_thi_khong_lam_do_ca_chuoi(monkeypatch, tmp_path):
    """Nuốt `OSError` là có chủ đích — nhưng phải kiểm nó nuốt ĐÚNG chỗ.

    Đổ cả một chuỗi 166 giây vì không ghi được một dòng nhật ký hiển thị thì
    tệ hơn. Và nó không hỏng lặng: phía đọc trả `KHONG_DO_DUOC`.
    """
    import interface.noi_bo_api as _api

    # Trỏ thư mục tiến độ vào một chỗ KHÔNG mkdir được: con của một TỆP.
    # Bản đầu vá `Path.mkdir` toàn cục, nên nó làm hỏng luôn bước `aura` —
    # phép gieo rộng hơn thứ định gieo, và bài đỏ vì lý do khác hẳn.
    chan = tmp_path / "day.txt"
    chan.write_text("khong phai thu muc", encoding="utf-8")
    monkeypatch.setattr(_api, "THU_MUC_TIEN_DO", chan / "khong_the_tao")

    d, goi = _chay_pipeline(monkeypatch)
    assert d["status"] == "PASS", "chuỗi đổ chỉ vì không ghi được tiến độ"
    assert len(goi) == 5, f"chuỗi phải vẫn chạy đủ phòng: {goi}"

    # Và KHÔNG hỏng lặng: phía đọc phải nói KHÔNG ĐO ĐƯỢC.
    td = _tien_do(d["pipeline_id"])
    assert td["trang_thai"] == "KHONG_DO_DUOC", td["trang_thai"]


# ---------------------------------------------------------------------------
# PHÒNG EPSILON — DỊCH MÃ, VÀ TRÌNH THẬT CHẤM BẢN DỊCH (06/09/2026)
#
# `core/polyglot.py` dịch thật từ 02/09 nhưng KHÔNG phòng nào gọi, nên thẻ
# Polyglot phải viết "chưa dịch mã" trong khi bộ dịch nằm ngay trong kho.
#
# Đo trước khi nối — hỏi trình biên dịch THẬT, không hỏi `status` của bộ dịch::
#
#              polyglot tự khai   HỎI TRÌNH BIÊN DỊCH
#   bash       PASS               FAIL              <-- LỆCH
#   javascript PASS               PASS
#   cpp go rust typescript  PASS  KHÔNG ĐO ĐƯỢC (máy không có trình biên dịch)

MA_TOT = ("def fibonacci(n):\n"
          "    if n <= 1:\n"
          "        return n\n"
          "    return fibonacci(n-1) + fibonacci(n-2)")


def test_epsilon_biet_noi_PASS(tmp_path_factory):
    """Máy đo phải chứng minh nó nói được ĐẠT, nếu không thì mọi số 0 vô nghĩa."""
    kq = phong_epsilon("test_eps_pass", MA_TOT, cac_lang=("javascript",))
    assert kq["trang_thai"] == "PASS", kq["vi_sao"]
    assert kq["so"]["dat"] == ["javascript"], kq["so"]
    assert any(h["kind"] == "ban_dich_javascript" for h in kq["artifacts"])


def _gia_bash_ra_rac(monkeypatch):
    """Thay ĐÚNG MỘT ngôn ngữ bằng bản dịch rác, các ngôn ngữ khác chạy thật.

    Từ 07/09/2026 bản dịch bash THẬT đã qua được `bash -n`, nên ba bài dưới
    không còn mượn được cái hỏng thật để chứng minh phòng biết nói FAIL. Mượn
    cái hỏng thật thì bài phụ thuộc vào việc bộ dịch **ở lại hỏng** — sửa xong
    là bài đỏ, và người sửa sẽ tưởng mình làm hỏng cái gì.

    Bơm rác vào đúng một ngôn ngữ thì điều được canh trở lại đúng chỗ của nó:
    **phán quyết đi theo TRÌNH THẬT, không theo `status` bộ dịch tự khai.**
    """
    import core.polyglot as _pg

    that = _pg.chuyen_doi_ngon_ngu

    def _gia(ma, nguon, dich):
        if dich == "bash":
            return {"status": "PASS", "ma_dich": "f() { if [ ; then\n",
                    "nodes_translated": 9}
        return that(ma, nguon, dich)

    monkeypatch.setattr(_pg, "chuyen_doi_ngon_ngu", _gia)


def test_epsilon_bat_duoc_ban_dich_HONG(monkeypatch):
    """Bản dịch hỏng — phòng phải nói ra, không được theo `status` của bộ dịch."""
    _gia_bash_ra_rac(monkeypatch)
    kq = phong_epsilon("test_eps_fail", MA_TOT, cac_lang=("javascript", "bash"))
    assert kq["trang_thai"] == "FAIL", kq["so"]
    assert kq["so"]["hong"] == ["bash"], kq["so"]
    # Và chỗ đắt: bộ dịch TỰ KHAI PASS cho đúng bản dịch ấy.
    assert kq["so"]["theo_ngon_ngu"]["bash"]["polyglot_khai"] == "PASS"


def test_epsilon_MOT_ban_dich_hong_thi_ca_phong_KHONG_duoc_PASS(monkeypatch):
    """PASS đòi hai vế. Chỉ đòi 'có ít nhất một cái đạt' thì bản hỏng nấp được."""
    _gia_bash_ra_rac(monkeypatch)
    kq = phong_epsilon("test_eps_2ve", MA_TOT, cac_lang=("javascript", "bash"))
    assert kq["so"]["dat"] == ["javascript"] and kq["so"]["hong"] == ["bash"]
    assert kq["trang_thai"] != "PASS", "một bản dịch hỏng nấp sau một bản tốt"


def test_epsilon_bash_GIO_qua_duoc_trinh_that():
    """Món nợ 06/09 đã trả: bản dịch bash chạy THẬT, không phải chỉ parse được.

    Chạy không giả lập gì. `MA_TOT` là đúng đoạn `card_polyglot_transpiler`
    gửi vào, và đúng đề `fib` của `tests/test_bo_dich_bash_chay_that.py` —
    nơi đo tiếp câu hỏi thứ hai (chạy ra có bằng bản Python không).

        06/09  bash FAIL (`echo fibonacci(n - 1)` — bash bác dấu `(`)
        07/09  bash PASS
    """
    kq = phong_epsilon("test_eps_bash_da_sua", MA_TOT,
                       cac_lang=("javascript", "bash"))
    assert kq["so"]["hong"] == [], kq["so"]
    assert kq["so"]["dat"] == ["bash", "javascript"], kq["so"]
    assert kq["trang_thai"] == "PASS", kq["vi_sao"]


def test_epsilon_BO_SOT_cau_lenh_thi_KHONG_duoc_la_PASS():
    """Bản dịch thiếu câu lệnh không phải bản dịch đạt.

    `ast.NodeVisitor` không có `visit_While` thì đi thẳng vào thân vòng lặp và
    sinh thân ra — **vòng lặp biến mất**. Đo 07/09/2026: `while n > 0: n -= 1`
    sang bash ra đúng một dòng `n=$(( n - 1 ))`, và `bash -n` GẬT.

    Đây là chỗ một cửa chỉ hỏi cú pháp không bao giờ thấy được, nên nó phải
    được chặn TRƯỚC khi hỏi cú pháp.
    """
    ma = "def dem(n):\n    while n > 0:\n        n -= 1\n    return n\n"
    kq = phong_epsilon("test_eps_bosot", ma, cac_lang=("bash", "javascript"))
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq
    assert set(kq["so"]["khong_do_duoc"]) == {"bash", "javascript"}, kq["so"]
    assert "While" in kq["so"]["theo_ngon_ngu"]["bash"]["vi_sao"], kq["so"]


def test_epsilon_BO_SOT_o_muc_BIEU_THUC_cung_khong_duoc_la_PASS():
    """Bash im hơn bốn ngôn ngữ kia khi bỏ cuộc, nên phải canh riêng.

    `x = {'a': 1}`: bốn ngôn ngữ kia sinh `/* complex_expr */` và trình kiểm
    BÁC ngay — hỏng to tiếng. Bash sinh `x=""`, `bash -n` gật. Cùng một chỗ bỏ
    cuộc, một bên đỏ một bên xanh, chỉ vì cú pháp bên này rộng hơn.
    """
    ma = "def d():\n    x = {'a': 1}\n    return x\n"
    kq = phong_epsilon("test_eps_bosot_bt", ma, cac_lang=("bash",))
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq
    assert "Dict" in kq["so"]["theo_ngon_ngu"]["bash"]["vi_sao"], kq["so"]


def test_epsilon_ma_RONG_khong_duoc_la_PASS():
    """0 câu lệnh mà báo '2 ngôn ngữ qua trình thật' là một điểm tự thưởng.

    Bắt được 07/09/2026 khi gọi phòng bằng sai khoá: `yeu_cau=""` thì
    `ast.parse` đạt, bộ dịch sinh mỗi dòng tiêu đề, `bash -n` và `node --check`
    đều gật, và phòng trả **PASS**. Cùng bệnh đã cấm ở chuỗi tuỳ biến
    (*"Danh sách rỗng là KHONG_CHAY_DUOC"*), chỉ khác tầng: ở đó 0 bước, ở đây
    0 câu lệnh.
    """
    for rong in ("", "   \n\n  ", "# chỉ có chú thích\n"):
        kq = phong_epsilon("test_eps_rong", rong)
        assert kq["trang_thai"] == "KHONG_CHAY_DUOC", (rong, kq)
        assert kq["artifacts"] == [], rong


@pytest.mark.parametrize("cach", ["đường dẫn None", "không có mục nào"])
def test_epsilon_ngon_ngu_KHONG_kiem_duoc_thi_khong_phai_PASS(monkeypatch, cach):
    """Không đo được ≠ đã đo, không sao.

    THOÁT KHỎI CÁI VÒNG LUẨN QUẨN (09/09/2026). Hai bản trước của bài này mượn
    một công cụ CHƯA CÀI làm thước:

        06/09  mượn "máy không có go"      -> cài Go 08/09, bài đỏ
        08/09  đổi sang "không có rustc"   -> cài Rust thì lại đỏ

    Mỗi lần trả một món nợ là mất ca đối chứng và phải đi tìm ví dụ mới. Cái
    giá ấy không phải của điều được canh — nó là của **cách canh**: dùng trạng
    thái máy làm thước thì thước đổi theo máy.

    Nay TIÊM sự vắng mặt thay vì mượn nó. `go` có bộ dịch thật, có bộ kiểm
    thật; gỡ bộ kiểm đi bằng `monkeypatch` là dựng đúng tình huống cần đo, trên
    mọi máy, mãi mãi. Cùng họ với `tools/gieo.py`: gieo hỏng một thứ rồi xem
    cửa có đọc đúng không.

    HAI ĐƯỜNG KHÁC NHAU trong `kiem_ma_bang_trinh_that`, nên đo cả hai:
    `TRINH_KIEM` có mục mà đường dẫn `None`, và `TRINH_KIEM` không có mục nào.

    (Ghi để khỏi hiểu nhầm: máy này 09/09 vẫn không có `rustc`, `cargo`, `g++`,
    `gcc`, `clang++` — nhưng bài này KHÔNG còn dựa vào chuyện đó.)
    """
    import core.phong_noi_bo as _p

    moi = dict(_p.TRINH_KIEM)
    if cach == "đường dẫn None":
        moi["go"] = ("gofmt", ["-e"], None)
    else:
        moi.pop("go", None)
    monkeypatch.setattr(_p, "TRINH_KIEM", moi)

    kq = phong_epsilon("test_eps_chua_do", MA_TOT, cac_lang=("go",))
    assert kq["so"]["khong_do_duoc"] == ["go"], kq["so"]
    assert kq["so"]["dat"] == [], (
        f"không có bộ kiểm mà vẫn chấm ĐẠT — đó đúng là 'chưa đo được' đội lốt "
        f"'đã đo, không sao': {kq['so']}")
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq


def test_epsilon_go_NAY_DA_DO_DUOC_va_khong_duoc_tut_lai():
    """Nửa kia của cặp: `go` đã trả nợ, phòng phải ĐO được nó.

    Bài trên TIÊM sự vắng mặt của bộ kiểm `go` rồi đòi phòng nói KHÔNG ĐO
    ĐƯỢC. Một mình nó thì gỡ `go` khỏi `TRINH_KIEM` THẬT cũng chẳng ai thấy —
    phòng tụt về KHÔNG ĐO ĐƯỢC và cả hai bài vẫn xanh, đúng bẫy "tụt im lặng".
    Bài này là vế còn lại: KHÔNG vá gì cả, và đòi `go` phải đo được thật.
    """
    kq = phong_epsilon("test_eps_go_do_duoc", MA_TOT, cac_lang=("go",))
    assert "go" not in kq["so"]["khong_do_duoc"], (
        "`go` tụt lại thành KHÔNG ĐO ĐƯỢC — đã cài go1.27.1 và nối `gofmt -e` "
        "vào TRINH_KIEM ngày 08/09, xem `tests/test_bo_dich_go_chay_that.py`")


def test_epsilon_KHONG_tu_thuong_diem_cho_phep_DONG_NHAT():
    """`python -> python` trả lại y byte mã vào. Đó không phải một bản dịch.

    Bản đầu của phòng chấm đó là `python PASS`: `ast.parse` đạt vì MÃ VÀO hợp
    lệ — thứ đã kiểm ở đầu hàm. Một điểm tự thưởng, đúng bẫy tautological. Bắt
    được bằng cách mở `ban_dich.py` ra so với mã vào, không bằng đọc mã.
    """
    kq = phong_epsilon("test_eps_dongnhat", MA_TOT, cac_lang=("python",))
    assert kq["so"]["dat"] == [], "phép đồng nhất được tính là bản dịch đạt"
    assert kq["so"]["khong_do_duoc"] == ["python"]
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC"
    assert not any(h["kind"] == "ban_dich_python" for h in kq["artifacts"]), (
        "vẫn ghi ra một 'bản dịch' python — nó là bản sao mã vào")


def test_epsilon_ma_vao_hong_thi_KHONG_CHAY_DUOC():
    """Fail-closed trước khi tốn một lượt dịch nào."""
    kq = phong_epsilon("test_eps_mahong", "def f(:\n  pass")
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", kq
    assert kq["artifacts"] == []
    assert "Python hợp lệ" in kq["vi_sao"]


def test_epsilon_CHAM_TEP_TREN_DIA_chu_khong_cham_chuoi_trong_RAM(monkeypatch):
    """Ca đối chứng cho bộ kiểm: bơm rác vào thì nó phải ĐỎ.

    Không có ca này thì `node --check` xanh chỉ chứng minh nó chưa từng nói
    không. Thay bộ dịch bằng bản trả rác — hiện vật trên đĩa là rác, và phán
    quyết phải theo TỆP chứ không theo `status` bộ dịch khai.
    """
    import core.polyglot as _pg

    def _rac(ma, nguon, dich):
        return {"status": "PASS", "ma_dich": "function ( { { ]]] unbalanced",
                "nodes_translated": 99}

    monkeypatch.setattr(_pg, "chuyen_doi_ngon_ngu", _rac)
    kq = phong_epsilon("test_eps_rac", MA_TOT, cac_lang=("javascript",))
    assert kq["trang_thai"] == "FAIL", kq
    assert kq["so"]["hong"] == ["javascript"]
    tep = PROJECT_ROOT / kq["artifacts"][0]["path"]
    assert "unbalanced" in tep.read_text(encoding="utf-8")


def test_epsilon_hien_vat_co_SHA256_dung_voi_byte_tren_dia():
    """Bằng chứng trên đĩa là chân lý duy nhất — băm phải tính TỪ đĩa."""
    import hashlib

    kq = phong_epsilon("test_eps_bam", MA_TOT, cac_lang=("javascript",))
    for h in kq["artifacts"]:
        p = PROJECT_ROOT / h["path"]
        assert p.is_file(), h["path"]
        assert h["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
        assert h["size_bytes"] == p.stat().st_size > 0


def test_epsilon_KHONG_lo_duong_dan_tuyet_doi_ra_ly_do(monkeypatch):
    """Lý do đi vào sổ cái và lên màn hình; đường dẫn tuyệt đối chỉ là chỗ để tệp.

    Bản đầu để nguyên stderr của `bash`, nên lý do bắt đầu bằng cả đường dẫn ổ
    đĩa. Nó đi thẳng vào `so_cai.jsonl` và lên thẻ trên màn hình.
    """
    _gia_bash_ra_rac(monkeypatch)
    kq = phong_epsilon("test_eps_duongdan", MA_TOT, cac_lang=("bash",))
    assert kq["trang_thai"] == "FAIL"
    chu = kq["vi_sao"] + " " + kq["so"]["theo_ngon_ngu"]["bash"]["vi_sao"]
    assert str(PROJECT_ROOT) not in chu, chu
    assert "ban_dich.sh" not in chu, chu


# Chép TAY từ `KY_LUAT_THUC_THI.md` mục 5d. Không viết `phong_noi_bo.KIEM_DUOC`
# ở đây: gieo đổi hằng số trong mã thì hai vế cùng đổi và cửa vẫn xanh.
DAC_TA_EPSILON_KIEM_DUOC = {"javascript", "bash", "python", "go", "cpp", "rust"}
DAC_TA_EPSILON_DICH_MAC_DINH = ("bash", "cpp", "go", "javascript", "rust")

# Đuôi tệp CHÉP TAY, không đọc lại từ `KIEM_DUOC`. Bản đầu của
# `test_HIEN_VAT_phai_mang_dung_duoi_tep...` lấy đuôi từ chính `KIEM_DUOC` —
# tức so một thứ với chính nó, nên gieo `".go" -> ".txt"` thì HAI VẾ CÙNG ĐỔI
# và cửa vẫn xanh. Đúng bẫy tautological mà bài kế bên vừa sinh ra để chữa,
# mắc lại ngay trong bài chữa nó.
DAC_TA_DUOI_TEP = {"bash": ".sh", "go": ".go", "javascript": ".js",
                   "python": ".py", "cpp": ".cpp", "rust": ".rs"}


def test_epsilon_hang_so_khop_DAC_TA():
    """CHÉP TAY từ đặc tả — nhưng một mình bài này KHÔNG đủ, xem bài kế bên.

    Nó so hai danh sách GÕ TAY với nhau: `KIEM_DUOC` trong mã và hằng số ở
    đây. Không vế nào chạm tới máy, nên nó xanh vĩnh viễn dù thực tế đổi thế
    nào — và đó đúng là chuyện đã xảy ra 08/09: cài Go, nối `gofmt` vào
    `TRINH_KIEM`, đo được cả hai chiều, mà phòng vẫn trả `KHONG_DO_DUOC` suốt
    một ngày vì `KIEM_DUOC` không có `go`. Bài này xanh cả ngày hôm ấy.

    Nó vẫn đáng giữ: đổi `KIEM_DUOC` mà không đổi đặc tả thì nó đỏ. Nhưng thứ
    bắt được cái lỗi kia là `test_KIEM_DUOC_phai_theo_KIP_thu_may_THAT_SU...`.
    """
    import core.phong_noi_bo as _p

    assert set(_p.KIEM_DUOC) == DAC_TA_EPSILON_KIEM_DUOC
    assert tuple(_p.DICH_MAC_DINH) == DAC_TA_EPSILON_DICH_MAC_DINH


def test_KIEM_DUOC_phai_theo_KIP_thu_may_THAT_SU_kiem_duoc():
    """Cắm thêm một bộ kiểm mà quên cho phòng dùng thì phải ĐỎ.

    ĐÂY LÀ VẾ KHÔNG TAUTOLOGICAL. Nó không so hai lời khai với nhau — nó hỏi
    `TRINH_KIEM` xem trình kiểm nào THẬT SỰ tìm thấy trên đĩa, rồi đòi phòng
    phải chịu hỏi chúng.

    Đo 08–09/09: `gofmt -e` tìm thấy ở `~/go-sdk/go/bin`, kiểm Go cả hai chiều
    — mà `KIEM_DUOC` không có `go`, nên năng lực ấy bằng không suốt một ngày.

    CHIỀU NGƯỢC LẠI CỐ Ý KHÔNG CÓ CỬA. `KIEM_DUOC` được phép kể tên một ngôn
    ngữ mà máy này chưa có trình kiểm — khi ấy phòng trả `KHONG_DO_DUOC`, đúng
    ba trạng thái. Bắt nó đỏ thì mọi máy thiếu công cụ đều đỏ, và cửa ấy đo
    được cái MÁY chứ không đo được cái MÃ.
    """
    import core.phong_noi_bo as _p

    tim_duoc = {lang for lang, (_, _, duong) in _p.TRINH_KIEM.items() if duong}
    thieu = tim_duoc - set(_p.KIEM_DUOC)
    assert not thieu, (
        f"{sorted(thieu)} có trình kiểm TÌM THẤY TRÊN ĐĨA nhưng `KIEM_DUOC` "
        f"không kể tên, nên phòng không bao giờ hỏi và trả KHONG_DO_DUOC. "
        f"Một khả năng có sẵn mà không ai gọi thì bằng không.")
    assert tim_duoc, (
        "KHÔNG trình kiểm nào tìm thấy — bài này đang không đo gì cả. "
        "Nếu máy thật sự trống thì `TRINH_KIEM` phải rỗng, không phải đầy mà "
        "đường dẫn nào cũng None.")


def test_HIEN_VAT_phai_mang_dung_duoi_tep_cua_ngon_ngu():
    """Bản dịch Go để lại trên đĩa phải tên `.go`, không phải `.txt`.

    BẮT ĐƯỢC BẰNG PHÉP GIEO (09/09): đổi `"go": ".go"` thành `".txt"` mà cả 82
    bài **vẫn xanh** — vì `gofmt -e` phân tích tệp bất kể đuôi, nên phán quyết
    không đổi. Chỉ hiện vật đổi.

    Mà `.agents/rules/agent_discipline.md` nói *"bằng chứng trên đĩa là chân lý
    duy nhất"*. Một tệp mã Go tên `ban_dich.txt` là bằng chứng nói dối về
    chính nó: người mở thư mục bằng chứng sáu tháng sau không biết nó là gì,
    và không công cụ nào mở đúng nó.
    """
    import core.phong_noi_bo as _p

    kq = phong_epsilon("test_eps_duoi_tep", MA_TOT,
                       cac_lang=DAC_TA_EPSILON_DICH_MAC_DINH)
    ten_hv = {h["kind"]: h for h in kq["artifacts"]}
    for lang in DAC_TA_EPSILON_DICH_MAC_DINH:
        h = ten_hv.get(f"ban_dich_{lang}")
        assert h, f"không có hiện vật cho {lang}: {sorted(ten_hv)}"
        duoi = DAC_TA_DUOI_TEP[lang]
        assert h["path"].endswith(duoi), (
            f"bản dịch {lang} để lại tên {h['path']!r}, phải kết thúc bằng "
            f"{duoi!r} — trình kiểm không quan tâm đuôi tệp, nhưng người đọc "
            f"bằng chứng thì có")


def test_DAC_TA_epsilon_go_van_o_lai_tai_lieu():
    """Con số tạo ra luật phải ở lại cùng luật.

    Bài này sinh ra vì phép gieo: xoá neo `CHOT:epsilon-go` mà cả tệp vẫn
    xanh. Tôi viết khối đặc tả có neo rồi **quên viết cửa đọc nó** — một cái
    neo không ai kéo thì chỉ là chữ.
    """
    import re

    from core.paths import PROJECT_ROOT

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(r"<!-- CHOT:epsilon-go -->(.*?)<!-- /CHOT:epsilon-go -->",
                  spec, re.S)
    assert m, "mất neo CHOT:epsilon-go trong đặc tả"
    khoi = m.group(1)
    for cum in ("gofmt -e",
                "KHONG_DO_DUOC",           # thứ phòng trả suốt ngày 08/09
                "tautological",            # vì sao cửa cũ không bắt được
                str(len(DAC_TA_EPSILON_KIEM_DUOC))):   # 4
        assert cum in khoi, f"khối epsilon-go mất {cum!r}"


def test_epsilon_dich_MAC_DINH_khong_chua_ngon_ngu_NGUON():
    """Xin đích trùng nguồn là xin một phép đồng nhất — không phải bản dịch.

    Và nó làm lời thẻ lệch khỏi thứ chạy: `mo_ta` nói "sang JavaScript và Bash"
    trong khi mặc định xin ba, cái thứ ba luôn KHÔNG ĐO ĐƯỢC. Đúng bệnh cả ngày
    hôm nay đi vá, tự tạo ra trong lượt vá.
    """
    import core.phong_noi_bo as _p

    assert _p.NGUON_MAC_DINH not in _p.DICH_MAC_DINH


def test_epsilon_chay_MAC_DINH_dung_so_ngon_ngu_da_dang_ky():
    """Đo HÀNH VI, không đọc hằng số: gọi phòng rồi đếm ngôn ngữ nó thật sự xin.

    Tên cũ là `..._dung_hai_ngon_ngu` và dòng cuối gõ cứng `== 2`. Thêm `go`
    vào `KIEM_DUOC` (09/09) thì nó đỏ — **đỏ đúng**, vì hành vi đã đổi thật.
    Nhưng số `2` ấy là con số thứ HAI của cùng một sự thật, gõ lại bằng tay
    cạnh một dòng đã lấy từ đặc tả. Hai bản sao của một con số thì có ngày
    lệch nhau; nay chỉ còn một nguồn.
    """
    kq = phong_epsilon("test_eps_macdinh", MA_TOT)
    assert set(kq["so"]["theo_ngon_ngu"]) == set(DAC_TA_EPSILON_DICH_MAC_DINH)
    assert kq["so"]["so_ngon_ngu_xin"] == len(DAC_TA_EPSILON_DICH_MAC_DINH)


def test_epsilon_MOT_ngon_ngu_chua_do_duoc_thi_ca_phong_KHONG_duoc_PASS(monkeypatch):
    """Xin mà chưa đo được thì cả lượt chưa kết luận được — không phải PASS.

    Bản trước trả PASS khi `hong` rỗng và có ít nhất một cái đạt, và nó đẻ ra
    HAI phán quyết cho cùng một lượt: chạy từ Git Bash thì `bash` đo được và
    bản dịch bị bác (FAIL); chạy từ máy chủ aiohttp thì `bash` không trên PATH
    nên KHÔNG ĐO ĐƯỢC, `hong` rỗng, và phòng báo **PASS**. Cùng mã, cùng đề,
    khác nhau ở PATH của tiến trình gọi.
    """
    # TIÊM sự vắng mặt, không mượn một công cụ chưa cài. Bản 06/09 dùng `go`,
    # bản 08/09 đổi sang `rust` — mỗi lần trả một món nợ công cụ là bài này lại
    # đỏ và phải đi tìm ví dụ mới. Gỡ bộ kiểm của `go` bằng `monkeypatch` thì
    # tình huống dựng được trên mọi máy, và điều được canh không đổi một chữ.
    import core.phong_noi_bo as _p

    monkeypatch.setattr(_p, "TRINH_KIEM",
                        {**_p.TRINH_KIEM, "go": ("gofmt", ["-e"], None)})
    kq = phong_epsilon("test_eps_thieu", MA_TOT, cac_lang=("javascript", "go"))
    assert kq["so"]["dat"] == ["javascript"], kq["so"]
    assert kq["so"]["khong_do_duoc"] == ["go"], kq["so"]
    assert kq["trang_thai"] == "KHONG_CHAY_DUOC", (
        "một ngôn ngữ chưa đo được mà cả phòng vẫn báo " + kq["trang_thai"])
    assert "go" in kq["vi_sao"] and "javascript" in kq["vi_sao"], kq["vi_sao"]


def test_epsilon_GHI_RO_trinh_nao_da_cham():
    """Bằng chứng phải nói ai chấm — hai máy có thể ra hai phán quyết."""
    import core.phong_noi_bo as _p

    kq = phong_epsilon("test_eps_trinh", MA_TOT, cac_lang=("javascript",))
    duong = kq["so"]["theo_ngon_ngu"]["javascript"]["trinh_kiem"]
    assert duong and Path(duong).is_file(), f"trinh_kiem = {duong!r}"
    assert duong == _p.TRINH_KIEM["javascript"][2]


def test_epsilon_TIM_DUOC_bash_du_khong_co_tren_PATH(monkeypatch):
    """`shutil.which` trượt thì phải tìm tiếp ở chỗ quen, đừng báo 'không có'.

    `bash.exe` CÓ THẬT trong thư mục cài Git trên máy này; chỉ là PATH của tiến
    trình máy chủ không thấy. Cùng bài với `System.Speech` báo máy không có
    giọng tiếng Việt trong khi registry có hai giọng.
    """
    import core.phong_noi_bo as _p

    monkeypatch.setattr(_p.shutil, "which", lambda _t: None)
    assert _p._tim_trinh("bash"), "PATH trượt là chịu thua — chưa tìm chỗ quen"
    assert _p._tim_trinh("khong_co_trinh_nay_dau") is None, (
        "trả bừa một đường dẫn cho một cái tên không có thật")
