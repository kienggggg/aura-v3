# -*- coding: utf-8 -*-
"""Năm phòng nội bộ còn lại — làm việc THẬT, để lại bằng chứng THẬT.

VÌ SAO CÓ TỆP NÀY

Đo 03/09/2026 qua `POST /api/dispatch`: `chạy thật 2 · chưa chạy thật 5`. Năm
phòng `beta` · `delta` · `gamma` · `omega` · `zeta` đều trả một đoạn văn viết
sẵn rồi khai một tệp không tồn tại.

Chỗ chua nhất là `gamma` — **phòng đo lường**. Nó in *"Số liệu đo đạc thời gian
thực"* rồi báo::

    RAM tiêu thụ  4.2 GB / 16.0 GB      máy thật: 8,85 / 12,61 GB
    Hard Gates    100% (714/714 tests)  đếm thật: 692 tests lúc ấy
    Tốc độ sinh   38.4 tokens/giây      thật: 5,02–6,69 tok/s (thổi 5,7–7,6 lần)

Ba con số, ba lần gõ tay, trong đúng cái phòng có nghề là đo.

MỘT TỆP CHO CẢ NĂM PHÒNG, KHÔNG PHẢI NĂM TỆP

`tests/test_v3_ranh_gioi.py` giữ `V3_PHONG` trần **8**, đang 4. Năm mô-đun riêng
là 9 — vượt trần. Hàng rào ấy dựng cùng ngày, và nó đang làm đúng việc: bắt
người viết phải cố ý. Năm phòng này đều là việc đo nhỏ, cùng một hình dạng
(*làm → ghi bằng chứng → trả ba trạng thái*), nên một tệp là đúng chỗ.

BA TRẠNG THÁI, KHÔNG GỘP

    PASS             làm xong, có bằng chứng trên đĩa
    FAIL             làm được nhưng kết quả không đạt
    KHONG_CHAY_DUOC  thiếu công cụ, mất mạng, hết giờ

KHÔNG DÙNG `psutil`. Nó không có trong `requirements.txt`, và chính nhánh
`except` khi thiếu nó đã đẻ ra con số giả `4.2/16.0`. `ctypes` gọi thẳng
`GlobalMemoryStatusEx` của Windows — đọc được, không thêm gói ngoài nào.
"""
from __future__ import annotations

import ast
import ctypes
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from core.paths import PROJECT_ROOT

TRAN_DEM_TEST_GIAY = 180
TRAN_TOK_GIAY = 120

# `beta` chạy A/B thì mỗi biến thể tốn một lượt gọi model 64–96 giây. Mặc định 1
# lượt để lọt trần 360s của máy đo phòng — và phòng PHẢI tự nói ra rằng N=1
# không kết luận được gì, thay vì im lặng đưa ra một tỉ lệ.
BETA_SO_LAN_MAC_DINH = 1
BETA_N_DU_DE_KET_LUAN = 3


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hien_vat(p: Path, loai: str, nhan: str) -> Dict[str, Any]:
    """Đường dẫn thật + byte thật + SHA-256 thật, giống `core/phong_alpha.py`."""
    try:
        duong = p.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        duong = p.as_posix()
    return {"name": p.name, "path": duong, "size_bytes": p.stat().st_size,
            "sha256": _bam(p), "type": loai, "kind": nhan}


def _thu_muc(phong: str, task_id: str) -> Path:
    d = PROJECT_ROOT / "data" / phong / task_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------- GAMMA

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def do_ram() -> Dict[str, Any]:
    """RAM THẬT qua `GlobalMemoryStatusEx`. Không đọc được thì nói là không đọc được."""
    try:
        m = _MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return {"do_duoc": False, "vi_sao": "GlobalMemoryStatusEx trả 0"}
        return {"do_duoc": True,
                "tong_gb": round(m.ullTotalPhys / 1e9, 2),
                "dang_dung_gb": round((m.ullTotalPhys - m.ullAvailPhys) / 1e9, 2),
                "phan_tram": m.dwMemoryLoad}
    except (AttributeError, OSError) as e:
        return {"do_duoc": False, "vi_sao": f"{type(e).__name__}: {e}"}


def dem_test() -> Dict[str, Any]:
    """Đếm test THẬT bằng `pytest --collect-only`, không gõ tay."""
    try:
        r = subprocess.run(
            [str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe"), "-m", "pytest",
             "tests", "-q", "--collect-only"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(PROJECT_ROOT), timeout=TRAN_DEM_TEST_GIAY)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"do_duoc": False, "vi_sao": f"{type(e).__name__}: {e}"}
    m = re.search(r"(\d+) tests? collected", r.stdout or "")
    if not m:
        return {"do_duoc": False, "vi_sao": "không thấy dòng 'tests collected'"}
    return {"do_duoc": True, "so_test": int(m.group(1))}


def do_toc_do_model() -> Dict[str, Any]:
    """Tốc độ sinh THẬT, lấy từ `eval_count / eval_duration` mà Ollama trả về.

    Không ước lượng bằng đồng hồ ngoài: con số ấy dính cả thời gian nạp model và
    thời gian mạng nội bộ, nên nó nhỏ hơn tốc độ sinh thật và người đọc không
    biết mình đang đọc cái nào.
    """
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps({"model": "qwen3.5:4b", "prompt": "Đếm từ 1 đến 20.",
                             "stream": False, "think": False,
                             "options": {"num_predict": 120, "temperature": 0}}
                            ).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TRAN_TOK_GIAY) as r:
            d = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"do_duoc": False, "vi_sao": f"{type(e).__name__}: {e}"}
    dem, ns = d.get("eval_count"), d.get("eval_duration")
    if not dem or not ns:
        return {"do_duoc": False, "vi_sao": "Ollama không trả eval_count/eval_duration"}
    return {"do_duoc": True, "model": "qwen3.5:4b", "so_token": dem,
            "tok_moi_giay": round(dem / (ns / 1e9), 2)}


def phong_gamma(task_id: str, yeu_cau: str = "") -> Dict[str, Any]:
    t0 = time.monotonic()
    so = {"ram": do_ram(), "test": dem_test(), "toc_do": do_toc_do_model()}
    khong_do = [k for k, v in so.items() if not v.get("do_duoc")]
    d = _thu_muc("gamma", task_id)
    tep = d / "metrics.json"
    tep.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    hv = [_hien_vat(tep, "JSON", "so_do_that")]

    if len(khong_do) == len(so):
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hv, "so": so,
                "vi_sao": "không đo được thứ nào: " + ", ".join(khong_do),
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    # Đo được một phần vẫn là PASS, nhưng phải NÓI RA phần không đo được — gộp
    # nó vào "đã đo" là đúng bệnh mà cả tệp này sinh ra để chống.
    return {"trang_thai": "PASS", "artifacts": hv, "so": so,
            "vi_sao": ("không đo được: " + ", ".join(khong_do)) if khong_do else "",
            "ms": round((time.monotonic() - t0) * 1000, 1)}


# --------------------------------------------------------------------- OMEGA

SO_CAI = PROJECT_ROOT / "data" / "omega" / "so_cai.jsonl"


def phong_omega(task_id: str, yeu_cau: str = "") -> Dict[str, Any]:
    """Đọc sổ cái rồi VIẾT BÁO CÁO — không phải ghi thêm một dòng vào sổ.

    Ghi vào `so_cai.jsonl` không tính là bằng chứng của phòng này: mọi phòng đều
    ghi vào đó, nên `tools/do_trang_thai_phong.py` cố ý loại nó ra. Phòng nào lấy
    dòng sổ của mình làm bằng chứng thì phòng nào cũng "đạt".
    """
    t0 = time.monotonic()
    if not SO_CAI.is_file():
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": f"không có {SO_CAI.name}",
                "ms": round((time.monotonic() - t0) * 1000, 1)}

    tho = SO_CAI.read_text(encoding="utf-8", errors="replace").splitlines()
    hong, theo_phong, theo_trang_thai = 0, {}, {}
    for d in tho:
        if not d.strip():
            continue
        try:
            j = json.loads(d)
        except ValueError:
            hong += 1
            continue
        theo_phong[j.get("phong_id", "(không ghi)")] = \
            theo_phong.get(j.get("phong_id", "(không ghi)"), 0) + 1
        theo_trang_thai[j.get("status", "(không ghi)")] = \
            theo_trang_thai.get(j.get("status", "(không ghi)"), 0) + 1

    so = {"so_dong": len(tho), "dong_hong": hong,
          "so_byte": SO_CAI.stat().st_size,
          "sha256_so_cai": _bam(SO_CAI),
          "theo_phong": dict(sorted(theo_phong.items(), key=lambda x: -x[1])),
          "theo_trang_thai": dict(sorted(theo_trang_thai.items(), key=lambda x: -x[1]))}

    d = _thu_muc("omega", task_id)
    bc = d / "bao_cao_so_cai.md"
    dong = [f"# Báo cáo sổ cái — {task_id}", "",
            f"Nguồn: `{SO_CAI.relative_to(PROJECT_ROOT).as_posix()}`",
            f"SHA-256: `{so['sha256_so_cai']}`", "",
            f"- **{so['so_dong']:,} dòng** · {so['so_byte']:,} byte",
            f"- dòng hỏng (không đọc được JSON): **{hong}**", "", "## Theo phòng", ""]
    dong += [f"| {k} | {v} |" for k, v in so["theo_phong"].items()]
    dong += ["", "## Theo trạng thái", ""]
    dong += [f"| {k} | {v} |" for k, v in so["theo_trang_thai"].items()]
    bc.write_text("\n".join(dong) + "\n", encoding="utf-8")

    return {"trang_thai": "PASS", "artifacts": [_hien_vat(bc, "MARKDOWN", "bao_cao_so_cai")],
            "so": so, "vi_sao": "", "ms": round((time.monotonic() - t0) * 1000, 1)}


# ---------------------------------------------------------------------- ZETA

def phong_zeta(task_id: str, yeu_cau: str) -> Dict[str, Any]:
    """Tra mạng THẬT rồi ghi biên nhận: URL · giờ lấy · SHA-256 nội dung.

    Bản cũ in *"Nguồn kiểm chứng: Wikipedia, Dân Trí, VNExpress, Báo Chính Phủ"*
    — bốn cái tên gõ tay, không lượt tra nào xảy ra, không URL nào kiểm được.
    """
    t0 = time.monotonic()
    from core.web_search import mang_co_song, search

    if not mang_co_song():
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": "không có mạng",
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    try:
        kq = search(yeu_cau or "tin tức hôm nay", limit=5)
    except Exception as e:                                   # noqa: BLE001
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": f"{type(e).__name__}: {str(e)[:120]}",
                "ms": round((time.monotonic() - t0) * 1000, 1)}

    nguon = []
    for s in (getattr(kq, "sources", None) or []):
        noi_dung = (getattr(s, "text", None) or getattr(s, "snippet", None) or "")
        nguon.append({
            "url": getattr(s, "url", ""),
            "tieu_de": getattr(s, "title", ""),
            "so_ky_tu": len(noi_dung),
            # Băm nội dung để lần sau còn đối chiếu được là nguồn có đổi không.
            "sha256_noi_dung": hashlib.sha256(noi_dung.encode("utf-8")).hexdigest(),
        })
    so = {"truy_van": yeu_cau, "so_nguon": len(nguon),
          "lay_luc": time.strftime("%Y-%m-%dT%H:%M:%S")}

    d = _thu_muc("zeta", task_id)
    bn = d / "bien_nhan.json"
    bn.write_text(json.dumps({**so, "nguon": nguon}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    hv = [_hien_vat(bn, "JSON", "bien_nhan_nguon")]

    # Không có nguồn nào là FAIL, không phải PASS: tra được mà không ra gì thì
    # phòng đã CHẠY, chỉ là kết quả rỗng.
    if not nguon:
        return {"trang_thai": "FAIL", "artifacts": hv, "so": so,
                "vi_sao": "tra xong nhưng không có nguồn nào",
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    return {"trang_thai": "PASS", "artifacts": hv, "so": so, "vi_sao": "",
            "ms": round((time.monotonic() - t0) * 1000, 1)}


# --------------------------------------------------------------------- DELTA

def quet_ast(cac_tep: List[Path]) -> Dict[str, Any]:
    """Quét AST THẬT. Hàm thuần trên danh sách tệp, để cửa canh đưa tệp xấu vào."""
    loi_cu_phap, khong_doc_duoc = [], []
    tong_dong = tong_ham = tong_lop = 0
    for p in cac_tep:
        try:
            nguon = p.read_text(encoding="utf-8")
        except OSError as e:
            khong_doc_duoc.append({"tep": p.name, "vi_sao": f"{type(e).__name__}"})
            continue
        tong_dong += len(nguon.splitlines())
        try:
            cay = ast.parse(nguon)
        except SyntaxError as e:
            loi_cu_phap.append({"tep": p.name, "dong": e.lineno, "loi": str(e.msg)})
            continue
        for n in ast.walk(cay):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tong_ham += 1
            elif isinstance(n, ast.ClassDef):
                tong_lop += 1
    return {"so_tep": len(cac_tep), "tong_dong": tong_dong,
            "so_ham": tong_ham, "so_lop": tong_lop,
            "loi_cu_phap": loi_cu_phap, "khong_doc_duoc": khong_doc_duoc}


def phong_delta(task_id: str, yeu_cau: str = "") -> Dict[str, Any]:
    """Chẩn đoán AST. KHÔNG tự động sửa gì cả.

    Bản cũ in *"✅ AST Status: PASS"* và *"✨ Khuyến nghị: Đoạn mã đạt chuẩn tối
    ưu"* mà chưa parse dòng nào. Nó còn khai có `Auto-Fix` — không có, và ở đây
    cũng sẽ không có: sửa mã hộ người khác mà không ai duyệt là chuyện khác hẳn
    với đọc mã.
    """
    t0 = time.monotonic()
    cac_tep = sorted((PROJECT_ROOT / "core").glob("*.py")) + \
        sorted((PROJECT_ROOT / "interface").glob("*.py"))
    if not cac_tep:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": "không tìm thấy tệp .py nào để quét",
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    so = quet_ast(cac_tep)
    d = _thu_muc("delta", task_id)
    tep = d / "chan_doan.json"
    tep.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    hv = [_hien_vat(tep, "JSON", "chan_doan_ast")]

    if so["loi_cu_phap"]:
        return {"trang_thai": "FAIL", "artifacts": hv, "so": so,
                "vi_sao": f"{len(so['loi_cu_phap'])} tệp lỗi cú pháp: "
                          + ", ".join(l["tep"] for l in so["loi_cu_phap"][:5]),
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    return {"trang_thai": "PASS", "artifacts": hv, "so": so,
            "vi_sao": (f"{len(so['khong_doc_duoc'])} tệp không đọc được"
                       if so["khong_doc_duoc"] else ""),
            "ms": round((time.monotonic() - t0) * 1000, 1)}


# ---------------------------------------------------------------------- BETA

def phong_beta(task_id: str, yeu_cau: str = "", so_lan: int = BETA_SO_LAN_MAC_DINH
               ) -> Dict[str, Any]:
    """A/B hai biến thể lời nhắc, chấm bằng chính cửa `do_kich_ban`.

    Việc này CÓ THẬT và tôi vừa làm nó bằng tay ngày 03/09: thêm *"mỗi câu KHÔNG
    quá 15 từ"* vào lời nhắc của `core/viet_truyen.py` để chữa trần 19,2 từ/câu.
    Nó chữa được (từ/câu tụt còn 8,1–10,1) nhưng kéo tụt luôn tổng độ dài — chạy
    thật 3 lượt ra 171 · 163 · 187 từ, trượt cả ba vì quá ngắn. Không ai phát
    hiện bằng đọc lời nhắc; chỉ chạy hai bản cạnh nhau mới thấy.

    N NHỎ THÌ PHÒNG PHẢI TỰ NÓI RA. Mỗi biến thể tốn một lượt gọi model 64–96
    giây, nên mặc định `so_lan=1` để lọt trần 360 s của máy đo phòng. Một lượt
    mỗi bên KHÔNG kết luận được gì, và trường `du_de_ket_luan` nói thẳng điều đó
    thay vì đưa ra một tỉ lệ trông như bằng chứng.
    """
    t0 = time.monotonic()
    from core.viet_truyen import _tach_cau, _xin_model, cat_cho_vua, do_kich_ban

    chu_de = yeu_cau or "người gác đèn biển và con tàu cuối mùa bão"
    BIEN_THE = {
        "A_khong_gioi_han_do_dai_cau": (
            f"Viết một truyện ngắn tiếng Việt hoàn chỉnh về: {chu_de}. "
            f"Có mở đầu và kết thúc rõ ràng, dài khoảng 320 từ, "
            f"chia thành ít nhất 18 câu. "
            f"Chỉ trả về truyện, không giải thích, không tiêu đề."),
        "B_moi_cau_toi_da_15_tu": (
            f"Viết một truyện ngắn tiếng Việt hoàn chỉnh về: {chu_de}. "
            f"Có mở đầu và kết thúc rõ ràng, dài khoảng 320 từ, "
            f"chia thành ít nhất 18 câu, mỗi câu KHÔNG quá 15 từ. "
            f"Chỉ trả về truyện, không giải thích, không tiêu đề."),
    }

    ket: Dict[str, Any] = {}
    hong = 0
    for ten, loi in BIEN_THE.items():
        cac_luot = []
        for i in range(so_lan):
            try:
                tho, giay = _xin_model(loi, hat=1000 + i)
            except RuntimeError as e:
                hong += 1
                cac_luot.append({"trang_thai": "KHONG_DO_DUOC", "vi_sao": str(e)})
                continue
            van, da_bo = cat_cho_vua(tho)
            tt, ly, so = do_kich_ban(van)
            cac_luot.append({"trang_thai": tt, "so": so, "vi_sao": ly,
                             "giay": round(giay, 1), "cau_da_bo": da_bo,
                             "tu_tho": len(tho.split()),
                             "cau_tho": len(_tach_cau(tho))})
        do_duoc = [l for l in cac_luot if l["trang_thai"] != "KHONG_DO_DUOC"]
        ket[ten] = {
            "so_lan": so_lan,
            "so_lan_do_duoc": len(do_duoc),
            "so_lan_dat": sum(1 for l in do_duoc if l["trang_thai"] == "DAT"),
            "luot": cac_luot,
        }

    so = {"chu_de": chu_de, "so_lan_moi_bien_the": so_lan,
          "du_de_ket_luan": so_lan >= BETA_N_DU_DE_KET_LUAN,
          "ghi_chu": (f"N={so_lan} mỗi biến thể — CHƯA đủ để kết luận. "
                      f"Cần ≥ {BETA_N_DU_DE_KET_LUAN}."
                      if so_lan < BETA_N_DU_DE_KET_LUAN else ""),
          "ket_qua": ket}

    d = _thu_muc("beta", task_id)
    tep = d / "ab_test.json"
    tep.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    hv = [_hien_vat(tep, "JSON", "ab_test_loi_nhac")]

    if hong == so_lan * len(BIEN_THE):
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hv, "so": so,
                "vi_sao": "mọi lượt gọi model đều hỏng",
                "ms": round((time.monotonic() - t0) * 1000, 1)}
    return {"trang_thai": "PASS", "artifacts": hv, "so": so,
            "vi_sao": so["ghi_chu"], "ms": round((time.monotonic() - t0) * 1000, 1)}


PHONG = {"gamma": phong_gamma, "omega": phong_omega, "zeta": phong_zeta,
         "delta": phong_delta, "beta": phong_beta}
