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
import shutil
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


# ------------------------------------------------------------------- EPSILON
#
# `core/polyglot.py` dịch THẬT từ 02/09 — `ast.NodeVisitor`, 5 nút, mỗi ngôn ngữ
# một dạng khác nhau — nhưng **không phòng nào gọi nó**, nên thẻ Polyglot phải
# viết "chưa dịch mã" trong khi bộ dịch nằm ngay trong kho.
#
# ĐO TRƯỚC KHI NỐI, hỏi trình biên dịch THẬT chứ không hỏi `status` của nó:
#
#              polyglot tự khai   HỎI TRÌNH BIÊN DỊCH
#   bash       PASS               FAIL              <-- LỆCH
#   javascript PASS               PASS
#   sql        FAIL               (không có bộ kiểm)
#   cpp go rust typescript  PASS  KHÔNG ĐO ĐƯỢC
#
# Nên phòng này KHÔNG lấy `status` của bộ dịch làm phán quyết. Nó dịch, ghi tệp
# ra đĩa, rồi đưa cho trình thật chấm.

# Đúng ba ngôn ngữ có bộ kiểm trên máy này. Đăng ký ở `KY_LUAT_THUC_THI.md` mục
# 5d. Thêm ngôn ngữ vào đây thì phải có bộ kiểm THẬT đi kèm — `KHONG_DO_DUOC`
# là câu trả lời đúng cho go · rust · cpp · typescript · sql, không phải `PASS`.
# DANH SÁCH PHÒNG THẬT SỰ HỎI. Không phải danh sách ngôn ngữ bộ dịch biết —
# đó là `polyglot.DANH_SACH_NGON_NGU`, và nó nói được 8 thứ tiếng mà không
# chứng minh được cái nào.
#
# `go` VÀO ĐÂY NGÀY 09/09/2026, MỘT NGÀY SAU KHI ĐÁNG LẼ PHẢI VÀO. Bản vá 08/09
# nối `gofmt -e` vào `TRINH_KIEM` và đo được cả hai chiều (tệp hợp lệ -> PASS,
# tệp hỏng -> FAIL kèm `:2:15: expected '}', found 'EOF'`) — nhưng quên dòng
# này, nên phòng vẫn trả `KHONG_DO_DUOC` cho Go suốt một ngày. Đúng ca "một khả
# năng có sẵn mà không ai gọi thì bằng không", và là "vá một nửa của một cặp"
# lần thứ hai.
#
# Cửa canh cũ không bắt được vì nó so DANH SÁCH NÀY với một danh sách gõ tay
# khác trong tệp test — hai lời khai đối chiếu nhau, không vế nào chạm tới máy.
# Nay `test_KIEM_DUOC_phai_theo_KIP_thu_may_THAT_SU_kiem_duoc` nối thẳng nó với
# trình kiểm tìm được trên đĩa.
KIEM_DUOC = {"javascript": ".js", "bash": ".sh", "python": ".py", "go": ".go"}
TRAN_KIEM_GIAY = 30

# ĐÍCH MẶC ĐỊNH BỎ CHÍNH NGÔN NGỮ NGUỒN. `python` ở lại `KIEM_DUOC` vì nó là bộ
# KIỂM được (dùng khi nguồn không phải Python), nhưng làm ĐÍCH thì nó là phép
# đồng nhất — xin nó chỉ đẻ thêm một dòng KHÔNG ĐO ĐƯỢC, và làm lời thẻ ("dịch
# sang JavaScript và Bash") lệch khỏi thứ thật sự chạy.
NGUON_MAC_DINH = "python"
DICH_MAC_DINH = tuple(l for l in sorted(KIEM_DUOC) if l != NGUON_MAC_DINH)

# TÌM TRÌNH KIỂM BẰNG ĐƯỜNG DẪN TUYỆT ĐỐI, KHÔNG DỰA VÀO PATH.
#
# Đo 06/09/2026: cùng mã, cùng đề, HAI PHÁN QUYẾT khác nhau. Chạy từ Git Bash
# thì `bash` có trên PATH → bản dịch bash bị bác → phòng FAIL. Chạy từ máy chủ
# aiohttp (khởi động qua PowerShell) thì `bash` KHÔNG trên PATH →
# `FileNotFoundError` → KHÔNG ĐO ĐƯỢC → phòng PASS.
#
# `bash.exe` **có thật** ở `C:\Program Files\Git\bin` và `...\Git\usr\bin` —
# chỉ là PATH của tiến trình kia không thấy. Cùng bài với `System.Speech` báo
# máy không có giọng tiếng Việt trong khi registry có: *một câu báo "không có"
# có thể sai*.
_CHO_TIM = {
    "node": (r"C:\Program Files\nodejs\node.exe",),
    "bash": (r"C:\Program Files\Git\bin\bash.exe",
             r"C:\Program Files\Git\usr\bin\bash.exe"),
    # Go 1.27.1 bung từ zip vào thư mục người dùng (08/09/2026) — tài khoản
    # này không phải Administrator nên không dùng MSI, và `~/go-sdk/go/bin`
    # KHÔNG nằm trên PATH.
    #
    # Đó chính là lý do nó phải có mặt ở đây. Sổ bệnh án có ca *"cùng mã, cùng
    # đề, hai phán quyết — biến thứ ba là PATH"*: một bản dịch bị bác từ Git
    # Bash và được PASS từ máy chủ, chỉ vì `bash` có trên PATH ở nơi này mà
    # không ở nơi kia. Dựa vào PATH là để phán quyết phụ thuộc chỗ gõ lệnh.
    "gofmt": (str(Path.home() / "go-sdk" / "go" / "bin" / "gofmt.exe"),),
    "go": (str(Path.home() / "go-sdk" / "go" / "bin" / "go.exe"),),
}


def _tim_trinh(ten: str):
    """`shutil.which` trước, rồi mới tới danh sách chỗ quen. Trả đường dẫn hoặc None."""
    duong = shutil.which(ten)
    if duong:
        return duong
    for p in _CHO_TIM.get(ten, ()):
        if Path(p).is_file():
            return p
    return None


# `(tên trình, cờ, đường dẫn giải ra)`. Giải MỘT LẦN lúc nạp mô-đun, và đường
# dẫn ấy được GHI VÀO HIỆN VẬT — bằng chứng phải nói rõ AI đã chấm.
TRINH_KIEM = {
    "javascript": ("node", ["--check"], _tim_trinh("node")),
    "bash": ("bash", ["-n"], _tim_trinh("bash")),
    # `gofmt -e` là bản đối ứng của `bash -n`: nó PHÂN TÍCH tệp và trả mã 2 khi
    # sai cú pháp, mã 0 khi hợp lệ — không cần dựng cả gói như `go build`.
    #
    # Và nó chỉ là NỬA phép đo, đúng như bash đã dạy 06/09: `bash -n` gật đầu
    # trong khi vòng lặp đã biến mất khỏi bản dịch. Nửa còn lại — chạy thật rồi
    # so đầu ra với bản Python — nằm ở `tests/test_bo_dich_go_chay_that.py`.
    "go": ("gofmt", ["-e"], _tim_trinh("gofmt")),
}


def kiem_ma_bang_trinh_that(lang: str, tep: Path) -> Dict[str, str]:
    """Hỏi trình thật xem tệp này có hợp lệ không. Trả `(trang_thai, vi_sao)`.

    KHÔNG có bộ kiểm thì `KHONG_DO_DUOC` — không phải `PASS`. Gộp hai cái này
    là đúng bệnh cả tệp này sinh ra để chống: "chưa đo được" đội lốt "đã đo,
    không sao".
    """
    if lang == "python":
        try:
            ast.parse(tep.read_text(encoding="utf-8"))
            return {"trang_thai": "PASS", "vi_sao": ""}
        except SyntaxError as e:
            return {"trang_thai": "FAIL", "vi_sao": f"{e.msg} (dòng {e.lineno})"}
    canh = TRINH_KIEM.get(lang)
    if canh is None:
        return {"trang_thai": "KHONG_DO_DUOC",
                "vi_sao": f"máy này không có bộ kiểm cho {lang}"}
    ten, co, duong = canh
    if duong is None:
        return {"trang_thai": "KHONG_DO_DUOC",
                "vi_sao": f"không tìm thấy {ten} trên máy này"}
    lenh = [duong] + co
    try:
        r = subprocess.run(lenh + [str(tep)], capture_output=True, text=True,
                           timeout=TRAN_KIEM_GIAY)
    except (OSError, subprocess.SubprocessError) as e:
        # Thiếu `node`/`bash` trên máy khác là KHÔNG ĐO ĐƯỢC, không phải hỏng mã.
        return {"trang_thai": "KHONG_DO_DUOC", "vi_sao": f"{type(e).__name__}: {e}"}
    if r.returncode == 0:
        return {"trang_thai": "PASS", "vi_sao": ""}
    dong = [d for d in (r.stderr or r.stdout).splitlines() if d.strip()]
    ly = dong[-1] if dong else ""
    # Bỏ đường dẫn tuyệt đối khỏi lý do: nó đi vào sổ cái và lên màn hình, mà
    # `D:\AURA_v3\data\...` chỉ là chỗ máy này để tệp, không phải tin về lỗi.
    for nhan in (str(tep), tep.name):
        ly = ly.replace(nhan + ": ", "").replace(nhan, "")
    return {"trang_thai": "FAIL", "vi_sao": ly.strip()[:200]}


def phong_epsilon(task_id: str, yeu_cau: str = "",
                  cac_lang: tuple = DICH_MAC_DINH) -> Dict[str, Any]:
    """Dịch mã Python sang nhiều ngôn ngữ, rồi để TRÌNH THẬT chấm bản dịch.

    `yeu_cau` là MÃ NGUỒN Python. Đây là lần đầu tham số ấy được đọc thật:
    `card_polyglot_transpiler` truyền cả đoạn mã vào từ đầu, còn `delta` — phòng
    nó từng gọi — quét `core/*.py` và bỏ qua nó.

    PASS đòi hai vế, không phải một: có ít nhất một ngôn ngữ kiểm được mà ĐẠT,
    **và** không ngôn ngữ kiểm được nào hỏng. Chỉ đòi vế đầu thì một bản dịch
    hỏng nấp được sau một bản dịch tốt.
    """
    from core.polyglot import chuyen_doi_ngon_ngu

    t0 = time.monotonic()
    ma = (yeu_cau or "").strip()
    try:
        cay = ast.parse(ma)
    except SyntaxError as e:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": f"mã vào không phải Python hợp lệ: {e.msg} (dòng {e.lineno})",
                "ms": round((time.monotonic() - t0) * 1000, 1)}

    # MÃ RỖNG KHÔNG PHẢI "ĐÃ DỊCH ĐƯỢC HẾT". Bắt được 07/09/2026 khi gọi phòng
    # bằng sai khoá: `yeu_cau=""` thì `ast.parse` đạt, bộ dịch sinh mỗi dòng
    # tiêu đề, `bash -n` và `node --check` đều gật, và phòng trả **PASS · 2
    # ngôn ngữ qua trình thật** cho một tệp không có lấy một câu lệnh.
    #
    # Đúng bệnh đã cấm ở chuỗi tuỳ biến (*"Danh sách rỗng là KHONG_CHAY_DUOC,
    # không phải PASS"*), chỉ khác tầng: ở đó là 0 bước, ở đây là 0 câu lệnh.
    if not cay.body:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "so": {},
                "vi_sao": "mã vào rỗng — không có câu lệnh nào để dịch",
                "ms": round((time.monotonic() - t0) * 1000, 1)}

    d = _thu_muc("epsilon", task_id)
    hv: List[Dict[str, Any]] = []
    theo_lang: Dict[str, Any] = {}
    for lang in cac_lang:
        # NGUỒN TRÙNG ĐÍCH LÀ PHÉP ĐỒNG NHẤT, KHÔNG PHẢI BẢN DỊCH.
        # `chuyen_doi_ngon_ngu(ma, "python", "python")` trả lại **y byte** mã
        # vào, rồi `ast.parse` đạt — nhưng nó đạt vì MÃ VÀO hợp lệ, thứ đã kiểm
        # ở đầu hàm này. Bản đầu của phòng chấm đó là `python PASS`: một điểm
        # tự thưởng, đúng bẫy tautological đã dính hai lần (02/09 và 04/09).
        # Bắt được bằng cách mở `ban_dich.py` ra so với mã vào, không bằng đọc.
        if lang == "python":
            theo_lang[lang] = {
                "trang_thai": "KHONG_DO_DUOC", "polyglot_khai": None,
                "vi_sao": "nguồn và đích trùng nhau — không có bản dịch nào để chấm"}
            continue
        kq = chuyen_doi_ngon_ngu(ma, "python", lang)
        ban_dich = kq.get("ma_dich", "")
        if kq.get("status") != "PASS" or not ban_dich.strip():
            theo_lang[lang] = {"trang_thai": "KHONG_CHAY_DUOC",
                               "vi_sao": kq.get("error", "bộ dịch trả về rỗng"),
                               "polyglot_khai": kq.get("status")}
            continue
        # BẢN DỊCH THIẾU CÂU LỆNH KHÔNG PHẢI BẢN DỊCH ĐẠT.
        #
        # Đo 07/09/2026: `while n > 0: n -= 1` sang bash ra đúng một dòng
        # `n=$(( n - 1 ))` — vòng lặp biến mất, `bash -n` GẬT, phòng báo PASS.
        # Cửa hỏi cú pháp không thể thấy chỗ này, nên phải chặn trước khi hỏi.
        if kq.get("bo_sot"):
            theo_lang[lang] = {
                "trang_thai": "KHONG_DO_DUOC", "polyglot_khai": kq.get("status"),
                "vi_sao": "bộ dịch bỏ sót " + ", ".join(kq["bo_sot"][:4])}
            continue
        tep = d / f"ban_dich{KIEM_DUOC.get(lang, '.txt')}"
        tep.write_text(ban_dich, encoding="utf-8")
        hv.append(_hien_vat(tep, lang.upper(), f"ban_dich_{lang}"))
        # CHẤM TỆP TRÊN ĐĨA, không chấm chuỗi trong RAM: thứ được kiểm phải là
        # đúng thứ để lại làm bằng chứng.
        chot = kiem_ma_bang_trinh_that(lang, tep)
        # GHI RÕ AI ĐÃ CHẤM. Cùng một bản dịch, hai máy có thể ra hai phán quyết
        # nếu một bên không tìm thấy trình kiểm — bằng chứng phải nói ra điều đó.
        theo_lang[lang] = {**chot, "polyglot_khai": kq.get("status"),
                           "so_nut": kq.get("nodes_translated"),
                           "trinh_kiem": (TRINH_KIEM.get(lang) or (None, None, None))[2]
                           or ("ast.parse" if lang == "python" else None)}

    so = {"so_ngon_ngu_xin": len(cac_lang), "theo_ngon_ngu": theo_lang,
          "dat": sorted(l for l, v in theo_lang.items() if v["trang_thai"] == "PASS"),
          "hong": sorted(l for l, v in theo_lang.items() if v["trang_thai"] == "FAIL"),
          "khong_do_duoc": sorted(l for l, v in theo_lang.items()
                                  if v["trang_thai"] == "KHONG_DO_DUOC")}
    tep = d / "ket_qua.json"
    tep.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    hv.append(_hien_vat(tep, "JSON", "phan_quyet_tung_ngon_ngu"))

    ms = round((time.monotonic() - t0) * 1000, 1)
    if so["hong"]:
        return {"trang_thai": "FAIL", "artifacts": hv, "so": so,
                "vi_sao": "bản dịch không qua được trình thật: "
                          + ", ".join(f"{l} ({theo_lang[l]['vi_sao'][:60]})"
                                      for l in so["hong"]),
                "ms": ms}
    # PASS ĐÒI ĐO ĐỦ, KHÔNG CHỈ ĐÒI KHÔNG AI HỎNG.
    #
    # Bản trước trả PASS khi `hong` rỗng và `dat` có ít nhất một cái — và nó đẻ
    # ra hai phán quyết cho cùng một lượt: từ Git Bash thì `bash` đo được và
    # bản dịch bị bác (FAIL); từ máy chủ aiohttp thì `bash` không có trên PATH
    # nên KHÔNG ĐO ĐƯỢC, `hong` rỗng, và phòng báo **PASS**.
    #
    # Một ngôn ngữ được XIN mà chưa từng đo thì cả lượt chưa kết luận được. Gộp
    # nó vào PASS là đúng cái bệnh "chưa đo được đội lốt đã đo, không sao".
    if so["khong_do_duoc"]:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hv, "so": so,
                "vi_sao": "chưa đo được " + ", ".join(so["khong_do_duoc"])
                          + (f" (đạt: {', '.join(so['dat'])})" if so["dat"] else ""),
                "ms": ms}
    if not so["dat"]:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hv, "so": so,
                "vi_sao": "không ngôn ngữ nào kiểm được trên máy này",
                "ms": ms}
    return {"trang_thai": "PASS", "artifacts": hv, "so": so,
            "vi_sao": f"{len(so['dat'])} ngôn ngữ qua trình thật: "
                      + ", ".join(so["dat"]), "ms": ms}


PHONG = {"gamma": phong_gamma, "omega": phong_omega, "zeta": phong_zeta,
         "delta": phong_delta, "beta": phong_beta, "epsilon": phong_epsilon}
