# -*- coding: utf-8 -*-
"""noi_bo_api.py — API Handlers cho App Nội Bộ Điều Hành 7 Đặc Nhiệm (AURA v3).

Quản lý 7 phòng ban chuyên trách:
  1. AURA  : Trung tâm điều phối & Sáng tác kịch bản (Writer & Orchestrator)
  2. Alpha : Studio sản xuất Video Dọc 60s & Visual Cards (Video & Multimedia)
  3. Beta  : Phòng thử nghiệm sáng tạo & Sandbox (Prompt Lab & Brainstorm)
  4. Delta : Phòng kỹ thuật & Bác sĩ mã nguồn (Code Doctor & Diagnostics)
  5. Gamma : Phòng giám sát & Phân tích dữ liệu (Metrics & Analytics)
  6. Omega : Phòng sổ cái nhiệm vụ & Âm nhạc Maestro (Task Ledger & Music Lab)
  7. Zeta  : Phòng Scout tra cứu & Kiểm chứng nguồn tin (Web Scout & Fact-Checker)
"""
from __future__ import annotations

import asyncio
from datetime import datetime
import hashlib
import hmac
import json
import re
import os
import secrets
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4

from aiohttp import web

from core.paths import DATA_DIR, PROJECT_ROOT
from core.polyglot import (
    DANH_SACH_NGON_NGU,
    chay_ma_da_ngon_ngu,
    chuyen_doi_ngon_ngu,
    kiem_tra_cu_phap_da_ngon_ngu,
    lay_danh_sach_ngon_ngu,
)

# Thư mục giao diện Web nội bộ
WEB_DIR = Path(__file__).resolve().parent / "web"
OMEGA_SO_CAI = DATA_DIR / "omega" / "so_cai.jsonl"
EVIDENCE_DIR = DATA_DIR / "evidence_sprint" / "runs"


# Trạng thái phòng KHÔNG nằm trong danh mục này nữa.
#
# 02/09/2026: bảy phòng khai sẵn `trang_thai`, sáu cái "ONLINE" — toàn bộ là
# chuỗi gõ tay, không dòng mã nào tính ra chúng. Đo lại bằng cách gọi đúng
# `POST /api/dispatch` rồi soi đĩa (`tools/do_trang_thai_phong.py`):
#
#     chạy thật 0 · chưa chạy thật 7 · không đo được 0
#     8 tệp được KHAI là đã tạo, 0 tệp có thật trên đĩa
#
# Ca đối chứng chứng minh máy đo không mù: gieo một lượt ghi tệp thật vào
# nhánh `beta` thì nó lật sang CHAY_THAT và gọi đúng tên tệp; trả mã về thì
# lật lại.
#
# Nay `api_danh_sach_phong` đọc trạng thái TỪ SỔ ĐO. Chưa đo thì hiện
# `CHUA_DO` — không phòng nào được tự khai ONLINE nữa.
SO_TRANG_THAI = DATA_DIR / "noi_bo" / "trang_thai_phong.json"


def doc_so_do() -> tuple[dict[str, str], str | None]:
    """Trả `(trạng thái từng phòng, ngày đo)`. Ngày `None` khi chưa đo được.

    NGÀY PHẢI ĐI CÙNG TRẠNG THÁI, KHÔNG TÁCH RỜI (10/09/2026).

    Đo được: tệp `trang_thai_phong.json` ghi `do_luc` là **2026-09-03T20:26:18**,
    và **34 commit** đã đụng vào mã của các phòng kể từ đó. `/api/rooms` trả
    `CHAY_THAT` cho cả bảy phòng mà **không trả ngày** — chỉ trả đường dẫn tệp.
    Người đọc thấy `CHAY_THAT` và hiểu là thì hiện tại.

    Đúng ca đã ghi sáng cùng ngày: *"nhãn đã đo không mang ngày thì đọc thành
    thì hiện tại"*. Lần ấy là kho công nghệ ngoài repo; lần này là chính sản
    phẩm. Nên hàm này trả CẢ HAI, và mọi chỗ dùng đều buộc phải cầm cái ngày.
    """
    try:
        d = json.loads(SO_TRANG_THAI.read_text(encoding="utf-8"))
        trang_thai = {p["phong_id"]: p["trang_thai"] for p in d.get("phong", [])}
        ngay = d.get("do_luc")
        return trang_thai, (ngay if isinstance(ngay, str) and ngay else None)
    except (OSError, ValueError, KeyError, TypeError):
        return {}, None


def _tuoi_phep_do(do_luc: str | None) -> int | None:
    """Phép đo già bao nhiêu ngày. `None` khi chưa đo được hoặc ngày hỏng."""
    if not do_luc:
        return None
    try:
        return max(0, (datetime.now() - datetime.fromisoformat(do_luc)).days)
    except (TypeError, ValueError):
        return None


def _duong_trong_kho(duong: Path) -> str:
    """Đường gọn cho HIỆN VẬT: tương đối nếu trong kho, tuyệt đối nếu ngoài.

    `relative_to(PROJECT_ROOT)` NÉM khi tệp nằm ngoài kho — bẫy ấy cắn BỐN lần
    trong ngày 10/09/2026, và lần thứ tư ở đây: `tests/conftest.py` chuyển
    `DATA_DIR` sang thư mục tạm cho bộ test khỏi ghi vào `data/` thật, thế là
    19 bài đỏ với `ValueError`. Mã sản phẩm đã ngầm giả định MỌI dữ liệu nằm
    dưới `PROJECT_ROOT` — giả định ấy chỉ đúng vì chưa ai từng chuyển nó đi.
    """
    try:
        return duong.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return duong.as_posix()


def _duong_de_hien(duong: Path) -> str:
    """Đường dẫn gọn để hiển thị. Không có tệp -> `CHUA_DO`; ngoài repo -> tuyệt đối."""
    if not duong.is_file():
        return "CHUA_DO"
    try:
        return str(duong.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(duong)


def _khoi_trang_thai_phong() -> dict:
    """Khối chung cho CẢ HAI cửa — một nguồn, không hai lời khai.

    Trước 10/09/2026 `/api/rooms` phủ trạng thái đo được còn `/api/status` trả
    `DANH_MUC_PHONG` THÔ kèm hằng số `"rooms_online": 7` gõ thẳng trong mã —
    hai trường cách nhau mười dòng trong cùng một tệp, một cái đã học bài, một
    cái chưa. Và giao diện không đọc `rooms_online` lần nào, nên không ai phát
    hiện nó sai.
    """
    da_do, do_luc = doc_so_do()
    phong = [{**p, "trang_thai": da_do.get(p["id"], "CHUA_DO")}
             for p in DANH_MUC_PHONG]
    return {
        "rooms": phong,
        # SUY RA, không gõ. Không có sổ đo thì 0 — fail-closed, chứ không phải
        # bảy phòng "online" vì con số 7 nằm sẵn trong mã.
        "so_phong_chay_that": sum(1 for p in phong
                                  if p["trang_thai"] == "CHAY_THAT"),
        "trang_thai_do_luc": do_luc,
        "trang_thai_so_ngay_truoc": _tuoi_phep_do(do_luc),
        # `relative_to` NÉM khi sổ đo nằm ngoài repo — bắt được 10/09/2026
        # bởi chính cửa canh vừa viết, lúc nó trỏ sổ vào thư mục tạm. Một
        # đường dẫn để HIỂN THỊ không đáng làm nổ cả cửa API.
        "nguon_trang_thai": _duong_de_hien(SO_TRANG_THAI),
    }


# ---------------------------------------------------------------- FAIL-CLOSED
#
# `KY_LUAT_THUC_THI.md` Chương I: *"Bằng chứng trên đĩa là chân lý duy nhất"*,
# và *"Lỗi là FAIL hoặc BLOCKED. Cấm nuốt lỗi."* Trước 02/09/2026 đường
# `/api/dispatch` làm ngược: nó trả `"status": "PASS"` cho MỌI lượt, kể cả lượt
# chỉ in ra một đoạn văn viết sẵn. Đo được: 7/7 phòng, 8 tệp được KHAI là đã
# tạo, **0 tệp có thật**.
#
# Nay phòng nào không để lại byte nào thì trả `KHONG_CHAY_DUOC`. Không phải
# `FAIL` — vì phòng ấy chưa hỏng, nó chưa CHẠY. Gộp hai thứ làm một thì "chưa
# làm gì" đội lốt "đã làm, không đạt".
#
# Hai chỗ trừ ra, giống hệt `tools/do_trang_thai_phong.py`:
#   * `so_cai.jsonl` — hàm này ghi cho MỌI phòng; tính vào thì phòng nào cũng đạt
#   * `__pycache__` — Python sinh ra khi nạp mô-đun
THU_MUC_BANG_CHUNG = ("data", "interface")


def _anh_chup_bang_chung() -> Dict[str, tuple]:
    ra: Dict[str, tuple] = {}
    for ten in THU_MUC_BANG_CHUNG:
        for f in (PROJECT_ROOT / ten).rglob("*"):
            if not f.is_file():
                continue
            d = f.as_posix()
            if "/__pycache__/" in d or f == OMEGA_SO_CAI:
                continue
            try:
                st = f.stat()
            except OSError:
                continue
            ra[d] = (st.st_size, st.st_mtime)
    return ra


def _bang_chung_moi(truoc: Dict[str, tuple], sau: Dict[str, tuple]) -> List[str]:
    return sorted([k for k in sau if k not in truoc]
                  + [k for k in sau if k in truoc and sau[k] != truoc[k]])


def _artifact_co_that(ten: str) -> bool:
    """Tệp phòng KHAI là đã tạo — có trên đĩa không?"""
    return any(f.is_file() for f in PROJECT_ROOT.rglob(ten))


# ---------------------------------------------------------- CỔNG VÀO CHẠY MÃ
#
# `/api/polyglot/run` chạy MÃ TUỲ Ý trong tiến trình con. Đo 04/09/2026 bằng một
# POST không mang gì cả::
#
#     HTTP 200 · status PASS
#     HOME = C:\Users\baloa      cwd = D:\AURA_v3
#     ghi được D:\AURA_v3\CHUNG_MINH_LO.txt — RA NGOÀI thư mục tạm
#
# Bốn lớp dưới đây chép từ `KY_LUAT_THUC_THI.md` Chương III — đăng ký ở đó TRƯỚC
# khi có mã này. Mọi lớp FAIL-CLOSED: thiếu là chặn.
#
# CHƯA CHẶN ĐƯỢC, và không được viết là đã chặn: bốn lớp này canh **ai gọi
# được**, KHÔNG canh **mã làm được gì**. Không có hộp cát — mã vẫn ghi ra ngoài
# thư mục tạm, đọc được HOME, gọi được mạng. `resource.setrlimit` là API Unix,
# đã thử 19/08 và `ModuleNotFoundError` trên Windows.
BIEN_BAT_CHAY_MA = "AURA_CHO_CHAY_MA"
HEADER_MA_THONG_HANH = "X-Aura-Token"

# Sinh một lần cho mỗi tiến trình. In ra console lúc khởi động (xem noi_bo_app).
MA_THONG_HANH = secrets.token_urlsafe(32)

# Máy chủ bind vào đâu. `noi_bo_app.main()` ghi vào đây trước khi chạy; còn None
# nghĩa là chưa ai khai — và chưa khai thì KHÔNG cho chạy mã.
DIA_CHI_BIND: Optional[str] = None

_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def dat_dia_chi_bind(host: str) -> None:
    """`noi_bo_app` gọi hàm này trước `web.run_app`."""
    global DIA_CHI_BIND
    DIA_CHI_BIND = host


def _la_loopback(host: Optional[str]) -> bool:
    return host is not None and host.strip().lower() in _LOOPBACK


def cua_chay_ma(headers: Mapping[str, str]) -> Optional[str]:
    """Trả lý do CHẶN, hoặc `None` nếu cho đi qua.

    Thứ tự cố ý: lớp 4 (loopback) đứng TRƯỚC lớp 1 (cờ bật), vì mở ra LAN và cho
    chạy mã là hai việc không được phép xảy ra cùng lúc — bật cờ cũng không cứu.
    """
    if not _la_loopback(DIA_CHI_BIND):
        return (f"máy chủ đang bind {DIA_CHI_BIND!r}, không phải loopback — "
                f"chạy mã bị TẮT vĩnh viễn ở chế độ này")
    if os.environ.get(BIEN_BAT_CHAY_MA) != "1":
        return (f"chạy mã đang TẮT. Đặt {BIEN_BAT_CHAY_MA}=1 để bật — "
                f"và đọc phần 'CHƯA CHẶN ĐƯỢC' trước khi bật")
    gui = headers.get(HEADER_MA_THONG_HANH, "")
    # So bằng BYTE, không bằng str.
    #
    # `hmac.compare_digest` ném `TypeError` khi chuỗi có ký tự ngoài ASCII —
    # nên một mã thông hành có dấu làm cổng NỔ 500 thay vì chặn 403. Sai chiều
    # fail-closed: lỗi phải dẫn tới chặn, không dẫn tới một trang lỗi. Bắt được
    # 04/09/2026 bởi chính bài test gửi "sai-be-bét".
    if not gui or not hmac.compare_digest(
            gui.encode("utf-8", "surrogatepass"),
            MA_THONG_HANH.encode("utf-8")):
        return f"thiếu hoặc sai {HEADER_MA_THONG_HANH}"
    # Origin chỉ có khi trình duyệt gọi. Không có Origin (curl, script) thì đã
    # qua được mã thông hành rồi, không cần chặn thêm.
    goc = headers.get("Origin", "")
    if goc:
        from urllib.parse import urlparse
        ten = (urlparse(goc).hostname or "").lower()
        if ten not in _LOOPBACK:
            return f"Origin {goc!r} không phải máy này"
    return None


# Danh mục 7 Đặc Nhiệm AURA v3
DANH_MUC_PHONG = [
    {
        "id": "aura",
        "code_name": "AURA",
        "ten": "Trung Tâm Điều Phối & Viết",
        "vai_tro": "Writer & Core Orchestrator",
        "bieu_tuong": "⚡",
        "mau_sac": "#3B82F6",
        "mo_ta": "Sáng tác chương truyện, bài viết, kịch bản bám sát bible và văn phong; phân loại luồng công việc.",
        "cong_cu": ["Soạn thảo chương", "Phân tích kịch bản", "Điều phối phòng ban", "Quản lý nhân vật"],
        "system_prompt": "Bạn là AURA — Trợ lý điều phối trung tâm và chuyên gia sáng tác nội dung trong hệ sinh thái AURA v3."
    },
    {
        "id": "alpha",
        "code_name": "Alpha",
        "ten": "Studio Video Dọc & Kịch Bản Thị Giác",
        "vai_tro": "Video Studio & Visual Cards",
        "bieu_tuong": "🎬",
        "mau_sac": "#EC4899",
        "mo_ta": "Sản xuất video dọc 720×1280 (55–65s) 100% offline; ghép ảnh PIL Cards, tổng hợp giọng đọc SAPI và render FFmpeg.",
        "cong_cu": ["Tạo Visual Cards (PIL)", "Tổng hợp TTS OneCore", "Ghép Video FFmpeg", "Kiểm định blackdetect"],
        "system_prompt": "Bạn là Alpha — Giám đốc Phòng Studio Video Dọc chuyên sản xuất video ngắn 60 giây đạt chuẩn kỹ thuật cao."
    },
    {
        "id": "beta",
        "code_name": "Beta",
        "ten": "Phòng Thử Nghiệm & Sandbox Sáng Tạo",
        "vai_tro": "Sandbox & Creative Lab",
        "bieu_tuong": "🧪",
        "mau_sac": "#F59E0B",
        "mo_ta": "Phòng thí nghiệm prompt, giả lập kịch bản tương tác, thử nghiệm tính năng mới trước khi đưa vào sản xuất.",
        "cong_cu": ["Thử nghiệm Prompt", "Mô phỏng phản hồi", "A/B Testing kịch bản", "Đo độ sáng tạo"],
        "system_prompt": "Bạn là Beta — Chuyên gia Nghiên cứu & Thử nghiệm sáng tạo, phụ trách sandbox và kiểm chứng ý tưởng mới."
    },
    {
        "id": "delta",
        "code_name": "Delta",
        "ten": "Phòng Kỹ Thuật & Bác Sĩ Sửa Mã",
        "vai_tro": "Code Doctor & Diagnostics",
        "bieu_tuong": "🔧",
        "mau_sac": "#10B981",
        "mo_ta": "Chẩn đoán lỗi logic, định vị nguyên nhân lỗi E1, phân tích AST và tự động sinh bản vá lỗi (Auto-Fix).",
        "cong_cu": ["Khám bệnh AST", "Tự động sửa lỗi Auto-Fix", "Định vị lỗi E1", "Tối ưu hiệu năng mã"],
        "system_prompt": "Bạn là Delta — Bác sĩ kỹ thuật chuyên chẩn đoán lỗi logic, sửa mã nguồn Python và bảo vệ tính toàn vẹn hệ thống."
    },
    {
        "id": "gamma",
        "code_name": "Gamma",
        "ten": "Phòng Giám Sát & Phân Tích Dữ Liệu",
        "vai_tro": "Metrics & Data Analytics",
        "bieu_tuong": "📊",
        "mau_sac": "#8B5CF6",
        "mo_ta": "Đo lường hiệu năng hệ thống: Tốc độ sinh chữ (token/s), mức tiêu thụ RAM thật, tỷ lệ đỗ Hard Gates của các phòng ban.",
        "cong_cu": ["Đo RAM & CPU", "Thống kê Hard Gates", "Phân tích tốc độ mô hình", "Báo cáo Evidence"],
        "system_prompt": "Bạn là Gamma — Chuyên gia phân tích số liệu và giám sát chất lượng hệ thống theo bằng chứng thật trên đĩa."
    },
    {
        "id": "omega",
        "code_name": "Omega",
        "ten": "Phòng Sổ Cái Nhiệm Vụ & Âm Nhạc Maestro",
        "vai_tro": "Task Ledger & Sound Lab",
        "bieu_tuong": "🎵",
        "mau_sac": "#06B6D4",
        "mo_ta": "Quản trị sổ cái nhiệm vụ chỉ-ghi-thêm (so_cai.jsonl), nhịp công việc và điều phối âm thanh/nhạc nền (LUFS, BPM, Stems).",
        "cong_cu": ["Ghi sổ cái chỉ-ghi-thêm", "Kiểm soát nhịp", "Phân tích chuẩn Loudness", "Tách bè âm thanh"],
        "system_prompt": "Bạn là Omega — Thủ thư quản trị sổ cái nhiệm vụ bất biến và phụ trách âm nhạc Maestro cho hệ sinh thái."
    },
    {
        "id": "zeta",
        "code_name": "Zeta",
        "ten": "Phòng Scout & Kiểm Chứng Nguồn Tin",
        "vai_tro": "Web Scout & Fact-Checker",
        "bieu_tuong": "🔍",
        "mau_sac": "#6366F1",
        "mo_ta": "Tra cứu mạng, trích xuất dữ liệu đa nguồn, tổng hợp bằng chứng kèm URL nguồn thật chống bịa đặt (Anti-hallucination).",
        "cong_cu": ["Tìm kiếm web DuckDuckGo", "Trích xuất bài viết", "Xác thực nguồn tin", "Lọc tin rác"],
        "system_prompt": "Bạn là Zeta — Trinh sát viên Scout chuyên thu thập dữ liệu từ Internet và kiểm chứng thông tin chính xác."
    }
]


# ==============================================================================
# 1. TRANG CHỦ & TÀI NGUYÊN GIAO DIỆN
# ==============================================================================
async def trang_chu(request: web.Request) -> web.Response:
    """Trả về trang Dashboard điều hành nội bộ `noi_bo.html`."""
    tep_html = WEB_DIR / "noi_bo.html"
    if not tep_html.is_file():
        return web.Response(text="Không tìm thấy noi_bo.html", status=404, content_type="text/plain; charset=utf-8")
    return web.FileResponse(tep_html)


async def file_tinh(request: web.Request) -> web.Response:
    """Phục vụ tài nguyên tĩnh (css, js, svg, hình ảnh)."""
    filename = request.match_info.get("filename", "")
    target = (WEB_DIR / filename).resolve()
    if not target.is_relative_to(WEB_DIR.resolve()) or not target.is_file():
        return web.Response(text="Không tìm thấy tài nguyên", status=404, content_type="text/plain; charset=utf-8")
    return web.FileResponse(target)


# ==============================================================================
# 2. API TRẠNG THÁI HỆ THỐNG & 7 PHÒNG BAN
# ==============================================================================
async def api_status(request: web.Request) -> web.Response:
    """Trả về thông số sinh tồn hệ thống (Vitals) và trạng thái 7 phòng ban."""
    import psutil # type: ignore
    
    # Đo RAM và CPU thật của máy
    try:
        mem = psutil.virtual_memory()
        ram_used_gb = round((mem.total - mem.available) / (1024 ** 3), 1)
        ram_total_gb = round(mem.total / (1024 ** 3), 1)
        ram_percent = mem.percent
        cpu_percent = psutil.cpu_percent(interval=None)
    except Exception:
        ram_used_gb = 4.2
        ram_total_gb = 16.0
        ram_percent = 26.5
        cpu_percent = 8.0

    # Đếm số nhiệm vụ trong sổ cái Omega
    so_nhiem_vu = 0
    if OMEGA_SO_CAI.is_file():
        try:
            with open(OMEGA_SO_CAI, "r", encoding="utf-8") as f:
                so_nhiem_vu = sum(1 for _ in f if _.strip())
        except Exception:
            pass

    # Đếm số run Evidence Sprint
    so_runs = 0
    if EVIDENCE_DIR.is_dir():
        try:
            so_runs = sum(1 for d in EVIDENCE_DIR.iterdir() if d.is_dir())
        except Exception:
            pass

    khoi = _khoi_trang_thai_phong()
    payload = {
        "status": "PASS",
        "service": "aura-noi-bo-v3",
        "timestamp": datetime.now().isoformat(),
        "vitals": {
            "ram_used_gb": ram_used_gb,
            "ram_total_gb": ram_total_gb,
            "ram_percent": ram_percent,
            "cpu_percent": cpu_percent,
            "tasks_count": so_nhiem_vu,
            "evidence_runs_count": so_runs,
            # Trường cũ ở đây là một hằng số bảy gõ thẳng, bỏ 10/09/2026.
            # Xoá một phòng khỏi DANH_MUC_PHONG hay để cả bảy phòng hỏng thì
            # nó vẫn trả bảy — và giao diện không đọc nó lần nào nên không ai
            # phát hiện. (Không chép lại tên trường cũ vào đây: cửa canh tìm
            # chuỗi ấy trong tệp, và chú thích cũng là tệp.)
            # Tên cũ cũng sai: chưa có gì đo "online", thứ đo được là "phòng
            # này có để lại byte nào trên đĩa không".
            "so_phong_chay_that": khoi["so_phong_chay_that"],
            "trang_thai_do_luc": khoi["trang_thai_do_luc"],
            "trang_thai_so_ngay_truoc": khoi["trang_thai_so_ngay_truoc"],
            "system_mode": "Local-First Active"
        },
        "rooms": khoi["rooms"]
    }
    return web.json_response(payload)


async def api_danh_sach_phong(request: web.Request) -> web.Response:
    """Trả về danh sách 7 phòng, kèm trạng thái ĐÃ ĐO (không phải tự khai)."""
    return web.json_response({"status": "PASS", **_khoi_trang_thai_phong()})


# ==============================================================================
# 3. API ĐIỀU PHỐI & THỰC THI NHIỆM VỤ TỪNG PHÒNG (DISPATCH)
# ==============================================================================
async def api_dieu_phoi_phong(request: web.Request) -> web.Response:
    """Tiếp nhận yêu cầu giao việc cho 1 trong 7 đặc nhiệm."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "FAIL", "error": "JSON không hợp lệ"}, status=400)

    phong_id = data.get("phong_id", "aura").lower()
    yeu_cau = (data.get("yeu_cau") or data.get("prompt") or "").strip()

    if not yeu_cau:
        return web.json_response({"status": "FAIL", "error": "Thiếu nội dung yêu cầu"}, status=400)

    # Tìm thông tin phòng
    phong = next((p for p in DANH_MUC_PHONG if p["id"] == phong_id), None)
    if not phong:
        return web.json_response({"status": "FAIL", "error": f"Không tìm thấy phòng: {phong_id}"}, status=404)

    task_id = f"task_{phong_id}_{int(time.time())}_{uuid4().hex[:6]}"
    bat_dau = time.monotonic()
    _truoc = _anh_chup_bang_chung()

    # Thực thi hành động theo từng phòng chuyên trách
    ket_qua = ""
    artifacts: List[Dict[str, Any]] = []
    _phong_tra_ve: Optional[str] = None   # phòng nào TỰ CHẤM thì điền vào đây

    if phong_id in ("zeta", "delta", "gamma", "omega", "beta"):
        # NĂM PHÒNG NÀY LÀM VIỆC THẬT (03/09/2026).
        #
        # Trước đó cả năm in một đoạn văn viết sẵn rồi khai một tệp không tồn
        # tại. Đo qua chính đường này: `chạy thật 2 · chưa chạy thật 5`.
        #
        # Chỗ chua nhất là `gamma` — phòng ĐO LƯỜNG — in "Số liệu đo đạc thời
        # gian thực" rồi báo bốn con số gõ tay, cả bốn đều sai:
        #
        #     RAM        4.2 GB / 16.0 GB    thật: 9,11 / 12,61 GB
        #     Hard Gates 714/714 tests       thật: 692 tests lúc ấy
        #     Tốc độ     38.4 tokens/giây    thật: 5,02–6,69 (thổi 5,7–7,6 lần)
        #     Latency    42 ms               chưa từng đo
        #
        # Cả năm nay ở `core/phong_noi_bo.py`, mỗi phòng để lại một hiện vật
        # thật kèm SHA-256 tính từ đĩa. Chúng gọi mạng và gọi model nên chậm —
        # `beta` tới ~170 giây — phải đẩy sang luồng khác kẻo chẹn máy chủ.
        from core.phong_noi_bo import PHONG

        _kq = await asyncio.to_thread(PHONG[phong_id], task_id, yeu_cau)
        _phong_tra_ve = _kq["trang_thai"]
        artifacts = _kq["artifacts"]
        _so = _kq["so"]
        _ten = {"zeta": "🔍 **[Zeta Scout]**", "delta": "🔧 **[Delta Code Doctor]**",
                "gamma": "📊 **[Gamma Analytics]**", "omega": "🎵 **[Omega Ledger]**",
                "beta": "🧪 **[Beta Sandbox]**"}[phong_id]

        # Mọi chỗ đọc `_so` đều dùng `.get()`: một phòng trả về hình dạng
        # khác thì đây phải in ra chỗ trống, KHÔNG được làm 500 cả
        # endpoint. Bắt được 03/09/2026 khi thay phòng bằng bản giả —
        # `_so["ket_qua"]` ném KeyError và `/api/dispatch` trả 500.
        def _dong(nhan: str, d: dict, chu: str) -> str:
            """Đo được thì in số; không đo được thì NÓI RA, đừng bỏ trống."""
            return (f"- **{nhan}**: {chu}\n" if d.get("do_duoc")
                    else f"- **{nhan}**: không đo được — {d.get('vi_sao')}\n")

        if phong_id == "gamma" and _kq["trang_thai"] != "KHONG_CHAY_DUOC":
            _r = _so.get("ram", {})
            _t = _so.get("test", {})
            _v = _so.get("toc_do", {})
            ket_qua = (
                f"{_ten} Số đo thật, không con số nào gõ tay.\n\n"
                + _dong("RAM", _r, f"{_r.get('dang_dung_gb')} / {_r.get('tong_gb')} GB "
                                   f"({_r.get('phan_tram')}%)")
                + _dong("Số bài test", _t, f"{_t.get('so_test')} (`pytest --collect-only`)")
                + _dong("Tốc độ sinh", _v, f"{_v.get('tok_moi_giay')} tok/s "
                                           f"({_v.get('model')}, {_v.get('so_token')} token)")
            )
        elif phong_id == "omega" and _kq["trang_thai"] == "PASS":
            ket_qua = (f"{_ten} Đã đọc sổ cái và viết báo cáo.\n\n"
                       f"- **{_so.get('so_dong', 0):,} dòng** · {_so.get('so_byte', 0):,} byte · "
                       f"{_so.get('dong_hong', 0)} dòng hỏng\n"
                       f"- **SHA-256 sổ cái**: `{str(_so.get('sha256_so_cai', ''))[:16]}…`\n"
                       f"- **Phòng có mặt trong sổ**: {len(_so.get('theo_phong', {}))}\n")
        elif phong_id == "zeta" and _kq["trang_thai"] == "PASS":
            ket_qua = (f"{_ten} Đã tra mạng thật và ghi biên nhận.\n\n"
                       f"- **Truy vấn**: {_so.get('truy_van', '')}\n"
                       f"- **Số nguồn**: {_so.get('so_nguon', 0)} — mỗi nguồn kèm URL và "
                       f"SHA-256 nội dung\n"
                       f"- **Lấy lúc**: {_so.get('lay_luc', '')}\n")
        elif phong_id == "delta" and _kq["trang_thai"] != "KHONG_CHAY_DUOC":
            ket_qua = (f"{_ten} Đã quét AST thật. **Không tự sửa gì cả.**\n\n"
                       f"- **{_so.get('so_tep', 0)} tệp** · {_so.get('tong_dong', 0):,} dòng · "
                       f"{_so.get('so_ham', 0)} hàm · {_so.get('so_lop', 0)} lớp\n"
                       f"- **Lỗi cú pháp**: {len(_so.get('loi_cu_phap', []))}\n")
        elif phong_id == "beta" and _kq["trang_thai"] == "PASS":
            _d = " · ".join(f"{k}: đạt {v.get('so_lan_dat')}/{v.get('so_lan_do_duoc')}"
                            for k, v in _so.get("ket_qua", {}).items())
            ket_qua = (f"{_ten} Đã chạy A/B hai biến thể lời nhắc.\n\n"
                       f"- **Chủ đề**: {_so.get('chu_de', '')}\n"
                       f"- {_d}\n"
                       f"- **Đủ để kết luận**: {_so.get('du_de_ket_luan', None)}"
                       + (f" — {_so.get('ghi_chu', '')}" if _so.get("ghi_chu", "") else "") + "\n")
        else:
            ket_qua = f"{_ten} {_kq['trang_thai']}: {_kq['vi_sao']}"

    elif phong_id == "alpha":
        # Phòng Studio: DỰNG VIDEO THẬT.
        #
        # Trước 02/09/2026 nhánh này in một storyboard viết sẵn rồi khai hai tệp
        # `storyboard.json` (3.4 KB) và `cards_preview.png` (240 KB) — không tệp
        # nào tồn tại, kích thước là chữ gõ tay.
        #
        # Nay nó chạy `core/phong_alpha.py`: giọng OneCore tiếng Việt -> 4 thẻ
        # PIL 720×1280 -> FFmpeg -> MP4, rồi để `ffprobe` + `blackdetect` chấm.
        # Mất khoảng 5 giây nên phải đẩy sang luồng khác, kẻo chẹn máy chủ.
        from core.phong_alpha import dung_video

        _kq = await asyncio.to_thread(
            dung_video, DATA_DIR / "alpha" / task_id)
        _phong_tra_ve = _kq["trang_thai"]
        artifacts = _kq["artifacts"]
        _so = _kq["kiem"].get("so", {})
        if _phong_tra_ve == "PASS":
            ket_qua = (
                "🎬 **[Alpha Studio]** Đã dựng xong video dọc; verifier độc lập đã chấm.\n\n"
                f"- **Khung**: {_so.get('rong')}×{_so.get('cao')} · **dài** {_so.get('giay')}s\n"
                f"- **Âm thanh**: có, đỉnh {_so.get('peak_db')} dB (không im lặng)\n"
                f"- **Đoạn đen ≥ 2s**: {_so.get('doan_den')}\n"
                f"- **Hiện vật**: {len(artifacts)} tệp thật, mỗi tệp một SHA-256\n\n"
                f"Dựng hết {_kq['ms'] / 1000:.1f}s."
            )
        else:
            ket_qua = (f"🎬 **[Alpha Studio]** {_phong_tra_ve}: {_kq['vi_sao']}\n\n"
                       f"Đã để lại {len(artifacts)} hiện vật để soi.")

    else:
        # AURA Writer: VIẾT KỊCH BẢN THẬT, ghi ra đĩa.
        #
        # Trước 03/09/2026 nhánh này in một đoạn văn viết sẵn — *"Nội dung đã
        # được biên soạn theo đúng bible và phong cách riêng"* — rồi khai
        # `draft_chapter.md` (5.6 KB). Tệp ấy KHÔNG TỒN TẠI; kích thước là chữ
        # gõ tay. Đo 02/09 qua `POST /api/dispatch`: 8 tệp được khai, 0 tệp có
        # thật, mỗi lượt 2–9 ms.
        #
        # Nay nó gọi `core/viet_truyen.py`: model viết, MÁY đếm, cắt giữa cho
        # lọt cửa sổ 215–250 từ / ≥13 câu khác nhau, trần 3 lần sinh. Chạy thật
        # 3 chủ đề: ĐẠT 3/3, mỗi lượt 85–234 giây — nên phải đẩy sang luồng
        # khác, kẻo chẹn máy chủ.
        #
        # Kịch bản này chính là đầu vào `van_ban` của phòng Alpha.
        from core.viet_truyen import viet_kich_ban

        _kq = await asyncio.to_thread(viet_kich_ban, yeu_cau)
        _phong_tra_ve = "PASS" if _kq["trang_thai"] == "DAT" else _kq["trang_thai"]
        _so = _kq["so"]

        if _kq["trang_thai"] == "DAT":
            _thu_muc = DATA_DIR / "aura" / task_id
            _thu_muc.mkdir(parents=True, exist_ok=True)
            _tep = _thu_muc / "kich_ban.md"
            _tep.write_text(_kq["van_ban"] + "\n", encoding="utf-8")
            artifacts.append({
                "name": _tep.name,
                "path": _duong_trong_kho(_tep),
                "size_bytes": _tep.stat().st_size,
                "sha256": hashlib.sha256(_tep.read_bytes()).hexdigest(),
                "type": "MARKDOWN", "kind": "kich_ban_cho_alpha",
            })
            ket_qua = (
                "⚡ **[AURA Writer]** Đã viết xong kịch bản cho Alpha.\n\n"
                f"- **Độ dài**: {_so.get('so_tu')} từ "
                f"(≈{_so.get('so_tu', 0) / 3.9:.0f}s đọc, cửa sổ 55–65s)\n"
                f"- **Câu khác nhau**: {_so.get('so_cau_khac')} · "
                f"{_so.get('tu_moi_cau')} từ/câu\n"
                f"- **Số lần sinh**: {_kq['so_lan_thu']}/3\n\n"
                f"Mất {_kq['ms'] / 1000:.1f}s."
            )
        else:
            # `lan` RỖNG là trạng thái thật, không phải ca hiếm: từ 04/09/2026
            # cửa nêu đề fail-closed TRƯỚC vòng lặp khi đề không còn từ nội dung
            # nào, nên không có lượt sinh nào để kể. Đọc `lan[-1]` ở đó thì nổ
            # IndexError — lý do bác biến thành sự cố 500.
            _vi = ("; ".join(str(l.get("vi_sao")) for l in _kq["lan"])
                   or "; ".join(_kq.get("vi_sao") or ["không rõ lý do"]))
            ket_qua = (f"⚡ **[AURA Writer]** {_kq['trang_thai']} sau "
                       f"{_kq['so_lan_thu']} lần sinh: {_vi}")

    # ---- FAIL-CLOSED: phòng có để lại byte nào không? ----
    bang_chung = [Path(d).name for d in _bang_chung_moi(_truoc, _anh_chup_bang_chung())]
    thieu = [a["name"] for a in artifacts if not _artifact_co_that(a["name"])]
    trang_thai = "PASS" if (bang_chung or (artifacts and not thieu)) else "KHONG_CHAY_DUOC"
    # Phòng nào tự chấm mình thì lời của NÓ đè lên phép đo bằng chứng — nhưng
    # chỉ theo chiều NGHIÊM HƠN. Có tệp trên đĩa không có nghĩa là đạt: Alpha
    # dựng ra được một video rồi `blackdetect` vẫn có thể bác nó.
    if _phong_tra_ve is not None and _phong_tra_ve != "PASS":
        trang_thai = _phong_tra_ve
    if trang_thai != "PASS":
        _thieu = (f", và {len(thieu)} tệp nó khai là đã tạo thì không có thật: "
                  + ", ".join(thieu)) if thieu else ""
        ket_qua = (
            "**KHÔNG CHẠY ĐƯỢC.** Phòng này trả lời xong mà không để lại byte "
            "nào trên đĩa" + _thieu + ".\n\n"
            "Đoạn dưới là văn bản viết sẵn, KHÔNG phải kết quả của một lượt "
            "chạy:\n\n---\n\n" + ket_qua
        )

    # Tự động ghi nhận vào Sổ cái Omega
    try:
        OMEGA_SO_CAI.parent.mkdir(parents=True, exist_ok=True)
        dong_so = {
            "task_id": task_id,
            "phong_id": phong_id,
            "yeu_cau": yeu_cau[:200],
            "timestamp": datetime.now().isoformat(),
            "status": trang_thai,
            "bang_chung": bang_chung,
            "artifacts_thieu": thieu,
            "latency_ms": round((time.monotonic() - bat_dau) * 1000, 1)
        }
        with open(OMEGA_SO_CAI, "a", encoding="utf-8") as f:
            f.write(json.dumps(dong_so, ensure_ascii=False) + "\n")
    except Exception:
        pass

    thoi_gian_ms = round((time.monotonic() - bat_dau) * 1000, 1)

    return web.json_response({
        "status": trang_thai,
        "task_id": task_id,
        "phong": phong,
        "tra_loi": ket_qua,
        "artifacts": artifacts,
        "bang_chung": bang_chung,
        "artifacts_thieu": thieu,
        "latency_ms": thoi_gian_ms
    })


# ==============================================================================
# 4. API QUY TRÌNH PHỐI HỢP LIÊN PHÒNG BAN (PIPELINE AUTOMATOR & PRESET CARDS)
# ==============================================================================

# CHẠY THẬT CẢ 8 THẺ NGÀY 06/09/2026, rồi đối chiếu `mo_ta` với hiện vật trên
# đĩa. Chuyển lời thẻ từ HTML sang màn hình mà không kiểm là dời một lời hứa
# chưa ai đo sang chỗ dễ tin hơn — nên đo trước, rồi mới chuyển.
#
#   thẻ                       chạy thật                       lời hứa
#   card_video_shorts         PASS 4/4 · 216s · 21 hiện vật   ĐÚNG
#   card_code_doctor          PASS 2/2 ·  48s ·  2            "sinh bản vá tự động" — không có
#   card_polyglot_transpiler  PASS 3/3 ·  39s ·  3            "dịch sang JS/Go/Rust…" — 0 dòng dịch
#   card_deep_scout           PASS 3/3 · 217s ·  3            "đối chiếu bằng chứng URL" — không đối chiếu
#   card_novel_writer         PASS 2/2 · 170s ·  2            "3 chương · TTR · giác quan" — 1 kịch bản 240 từ
#   card_fullstack_builder    FAIL 0/3 · 287s ·  0            "HTML5/CSS3 + API aiohttp" — 0 hiện vật
#                             -> sau khi đổi `bai_noi`: PASS 3/3 · 111s · 19 hiện vật
#   card_security_guard       PASS 3/3 ·  83s ·  3            "chống lộ API Key · Path · injection" — không cái nào
#   card_system_audit         PASS 2/2 ·  48s ·  2            "đo RAM/CPU" — không đo CPU
#
# Chỗ đắt nhất: `card_polyglot_transpiler` và `card_security_guard` hứa hai việc
# khác hẳn nhau mà chạy **y hệt nhau** — cùng chuỗi delta·gamma·omega, và
# `chan_doan.json` của cả hai đều 119 byte với đúng bốn con số đếm.
#
# `mo_ta` dưới đây đã sửa theo lượt chạy. Chỗ nào chưa làm được thì viết
# **CHƯA**, không viết cho đẹp — đúng luật Chương 7 mục 3.
#
# TÊN THẺ CŨNG SỬA THEO (06/09/2026, Sếp quyết "đổi tên cho khớp việc"). Lượt
# trước tôi chỉ đổi `card_code_doctor` và báo còn hai tên sai; đọc lại cả tám
# thì **năm** tên hứa việc không có, không phải hai:
#
#   Polyglot Cross-Compiler          -> Quét AST Toàn Kho (chưa dịch mã)
#   Trinh Sát & Kiểm Chứng Sự Thật   -> Trinh Sát Nguồn (chưa kiểm chứng)
#   Viết Truyện Đời Thường Dài Hơi   -> Viết Một Kịch Bản Truyện 215–250 Từ
#   Sinh App Fullstack Web           -> Viết → Quét AST → Dựng Video (đang gãy)
#   Kiểm Toán Bảo Mật & Secret Leak  -> Quét AST Toàn Kho (chưa quét khoá)
#
# Hai thẻ AST nay TRÙNG TÊN gần hết và TRÙNG biểu tượng — cố ý. Chúng chạy y
# hệt nhau; đặt hai cái tên nghe khác nhau cho một hành vi là giấu đúng thứ vừa
# đo ra.
#
# `ten` KHÔNG còn mang emoji: `bieu_tuong` là icon duy nhất trên thẻ, nên hai
# trường không được cãi nhau (trước đó 🩺 trong tên đứng cạnh 🔧 ở huy hiệu).
# Và vì `bieu_tuong` nay là icon duy nhất, nó cũng là một lời khai: 🔒 · 🛡️ ·
# 🌐 · 💻 đã đổi, chúng báo hiệu việc mà chuỗi không làm.
DANH_SACH_THE_QUY_TRINH = [
    {
        "id": "card_video_shorts",
        # RÚT `bai_noi` NGÀY 05/09/2026, sau khi chạy thật một lượt trên chính
        # đề mặc định của thẻ này ("Khám phá bí mật lịch sử phố cổ Hà Nội"):
        #
        #   bai_noi   KHONG_DAT · 3/3 lượt trượt cửa độ dài
        #             24,56 · 25,65 · 26,05 từ/câu   (trần 22,7)
        #             309 giây để nói "không viết được"
        #   truyen    DAT · 1/3 lượt · 70 giây · video PASS 59,46 s
        #
        # Bảng 2×2 nói `bai_noi` hơn hẳn trên đề GIẢI THÍCH (3/5 so 1/5). Nhưng
        # bảng ấy đo trên MỘT đề khác, ở đó bai_noi cho 19,0–21,6 từ/câu. Độ dài
        # câu của lời bài nói PHỤ THUỘC ĐỀ TÀI, và n=5 trên một đề không suy ra
        # được đề khác.
        #
        # Muốn dùng lại thì phải đo trên NHIỀU đề trước. Đừng nới trần 22,7 cho
        # vừa lời nhắc — ràng buộc thật có thể là trần, nhưng nới nó để một bản
        # vá trông đẹp là đúng cái bẫy `CLAUDE.md` cấm.
        "the_loai": "truyen",
        "ten": "Video Shorts 60s Tự Động",
        "bieu_tuong": "🎬",
        "mau_sac": "#EC4899",
        "mo_ta": "Nhập chủ đề ngắn, tự động cào tin tức, viết kịch bản và render video 60s kèm giọng đọc.",
        "cac_phong": ["zeta", "aura", "alpha", "omega"],
        "tham_so_mac_dinh": "Khám phá bí mật lịch sử phố cổ Hà Nội"
    },
    {
        "id": "card_code_doctor",
        # ĐỔI TÊN 06/09/2026: bỏ "Auto-Fix". Mục 5 Chương II của
        # `KY_LUAT_THUC_THI.md` ghi thẳng **`delta` KHÔNG tự sửa mã**, nên cái
        # tên đang hứa đúng thứ đặc tả cấm. Chạy thật: 2/2 · 48s · 2 hiện vật,
        # `chan_doan.json` đếm 27 tệp · 10.590 dòng · 293 hàm · 51 lớp · 0 lỗi
        # cú pháp. Không có bản vá nào.
        "ten": "Bác Sĩ Khám Mã (chỉ chẩn đoán)",
        "bieu_tuong": "🩺",
        "mau_sac": "#10B981",
        "mo_ta": "Quét AST toàn kho tìm lỗi cú pháp rồi đo RAM và số bài test. KHÔNG tự sửa mã — đặc tả cấm, và ở đây cũng sẽ không có.",
        "cac_phong": ["delta", "gamma"],
        "tham_so_mac_dinh": "def tinh_tong(n):\n    s = 0\n    for i in range(n):\n        s += i"
    },
    {
        "id": "card_polyglot_transpiler",
        "ten": "Dịch Mã & Để Trình Thật Chấm",
        "bieu_tuong": "🔤",
        "mau_sac": "#F59E0B",
        # 06/09 sáng: chuỗi là `delta·gamma·omega` — 3/3 · 39s và KHÔNG hiện vật
        # nào là mã đã dịch, nên thẻ phải viết "chưa dịch mã" trong khi bộ dịch
        # nằm ngay trong kho (`core/polyglot.py`, không phòng nào gọi).
        #
        # 06/09 chiều: `delta` → `epsilon`. Bỏ `delta` vì bước ấy quét
        # `core/*.py` và bỏ qua đề — nay `tham_so_mac_dinh` (một đoạn mã) lần
        # đầu được đọc thật.
        #
        # THẺ NÀY ĐỎ, VÀ ĐỎ LÀ ĐÚNG: `bash` sinh mã không parse nổi
        # (`echo fibonacci(n - 1) + fibonacci(n - 2)`), `javascript` qua
        # `node --check`. Sếp quyết lấy đủ ba ngôn ngữ kiểm được thay vì chỉ xin
        # `javascript` cho xanh — cái đỏ ấy chỉ đúng chỗ cần sửa tiếp.
        #
        # 07/09 sáng: nợ ấy đã trả. Chạy thật `epsilon` với đúng
        # `tham_so_mac_dinh` dưới đây: **PASS · 175ms · bash và javascript đều
        # qua trình thật**, và bản dịch bash chạy ra `55` bằng đúng bản Python.
        #
        # Nhưng KHÔNG được viết "dịch được Python sang Bash". Cùng lượt ấy đo
        # ra một chỗ tệ hơn cái vừa vá: `while`, `class`, `try`, `with` bị bộ
        # dịch **bỏ im lặng** — thân vòng lặp còn, vòng lặp mất, `bash -n` gật.
        # Nay chúng trả KHÔNG ĐO ĐƯỢC thay vì PASS, và lời thẻ phải nói ra.
        "mo_ta": "Dịch mã Python sang JavaScript và Bash, ghi bản dịch ra đĩa rồi để node/bash chấm chính tệp ấy. CHỈ dịch được def · if · for · gán · gọi hàm; gặp while · class · try · with thì trả KHÔNG ĐO ĐƯỢC chứ KHÔNG dịch. CHƯA kiểm được Go · Rust · C++ · TypeScript · SQL — máy này không có trình biên dịch cho chúng.",
        "cac_phong": ["epsilon", "gamma", "omega"],
        "tham_so_mac_dinh": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
    },
    {
        "id": "card_deep_scout",
        # RÚT `bai_noi` cùng ngày với `card_video_shorts` — xem chú thích ở đó.
        # Thẻ này CHƯA từng được chạy thật với `bai_noi`, nên rút vì cùng rủi
        # ro chứ không vì đã đo. Nói rõ ra để lần sau không ai đọc thành "đã đo
        # và hỏng".
        "the_loai": "truyen",
        "ten": "Trinh Sát Nguồn (chưa kiểm chứng)",
        "bieu_tuong": "🔍",
        "mau_sac": "#6366F1",
        # Chạy thật 06/09: 3/3 · 217s · 3 hiện vật. `zeta` lấy 5 nguồn kèm
        # SHA-256, `aura` viết kịch bản TỪ CHỦ ĐỀ — không đọc biên nhận, nên
        # không có bước đối chiếu nào. Chữ "chống bịa đặt" là lời hứa nặng nhất
        # của cả danh mục và nó chưa có gì đứng sau.
        "mo_ta": "Tra mạng thật rồi ghi biên nhận nguồn kèm SHA-256, viết kịch bản từ chủ đề và ghi sổ cái. CHƯA đối chiếu kịch bản với nguồn.",
        "cac_phong": ["zeta", "aura", "omega"],
        "tham_so_mac_dinh": "Xu hướng công nghệ AI Agent tự hành năm 2026"
    },
    {
        "id": "card_novel_writer",
        "the_loai": "truyen",  # sáng tác truyện đời thường
        "ten": "Viết Một Kịch Bản Truyện 215–250 Từ",
        "bieu_tuong": "📖",
        "mau_sac": "#3B82F6",
        # Chạy thật 06/09: 2/2 · 170s · 2 hiện vật. `aura` cho MỘT kịch bản 240
        # từ / 16 câu khác nhau — không phải 3 chương. `gamma` đo RAM · số bài
        # test · tốc độ sinh; không có TTR, không có mật độ giác quan ở đâu.
        "mo_ta": "Viết MỘT kịch bản truyện 215–250 từ rồi đo RAM, số bài test và tốc độ sinh. CHƯA có 3 chương, CHƯA đo TTR hay mật độ giác quan.",
        "cac_phong": ["aura", "gamma"],
        "tham_so_mac_dinh": "Quán Cà Phê Cuối Ngõ"
    },
    {
        "id": "card_fullstack_builder",
        # ĐỔI SANG `bai_noi` NGÀY 06/09/2026, sau khi ĐO — không phải sau khi
        # đoán. Chú thích 05/09 ở đây từ chối đổi với đúng lý do: *"gán `bai_noi`
        # cho nó là làm cho một thẻ hỏng trông đỡ hỏng hơn"*. Lý do ấy đứng
        # vững chừng nào lời thẻ còn sai; nay lời thẻ đã sửa theo lượt chạy, và
        # câu hỏi còn lại là một câu ĐO ĐƯỢC.
        #
        # Ghép đôi theo hạt giống, trên CHÍNH đề mặc định của thẻ ("Bảng điều
        # khiển tài chính cá nhân tương tác"), 5 hạt, mỗi bên 1 lượt model:
        #
        #   hạt  truyen                              bai_noi
        #   1    KHONG_DAT  466 từ · 25,89 từ/câu    DAT  245 từ · 20,42
        #   2    KHONG_DAT  câu mở không nêu đề      KHONG_DAT  22,75 (trần 22,73)
        #   3    KHONG_DAT  430 từ · 23,89 từ/câu    DAT  250 từ · 20,83
        #   4    KHONG_DAT  câu mở không nêu đề      DAT  243 từ · 22,09
        #   5    KHONG_DAT  câu mở không nêu đề      DAT  236 từ · 21,45
        #                   ĐẠT 0/5                       ĐẠT 4/5
        #
        # Trên đề GIẢI THÍCH, lời truyện trượt CẢ HAI cửa: 2/5 vì câu quá dài,
        # 3/5 vì câu mở dựng cảnh nên không nêu đề. Đúng thứ bảng 2×2 ngày 05/09
        # dự đoán — nay đo trên chính đề này, nên không còn phải suy từ đề khác.
        # Lượt `bai_noi` trượt duy nhất thua trần **0,02 từ/câu**.
        "the_loai": "bai_noi",
        "ten": "Viết Lời Thoại → Quét AST → Dựng Video",
        "bieu_tuong": "🎥",
        "mau_sac": "#06B6D4",
        # Chạy thật 06/09 trên chính đề mặc định của thẻ: **FAIL 0/3 · 287 giây
        # · 0 hiện vật**. `aura` trượt cửa độ dài (23,89 từ/câu, trần 22,7) nên
        # `delta` và `alpha` không chạy. Đây là thẻ DUY NHẤT trong 8 thẻ không
        # ra nổi một byte nào.
        #
        # KHÔNG đổi đề cho nó qua cửa. Đề "bảng điều khiển tài chính" là đề GIẢI
        # THÍCH, và lời nhắc truyện viết câu dài trên đề giải thích — đúng ca đã
        # đo 05/09. Đổi đề để thẻ trông chạy được là làm cho một thẻ hỏng trông
        # đỡ hỏng hơn, đúng thứ chú thích 05/09 ngay dưới đây từ chối làm.
        # Chạy lại sau khi đổi thể loại, cùng đề, cùng máy:
        #   trước  FAIL 0/3 · 287 s · 0 hiện vật
        #   sau    PASS 3/3 · 111 s · 19 hiện vật · video 58,87 s
        # Câu mở của lượt đạt: *"Ngày hôm nay tôi sẽ cùng bạn khám phá cách
        # hoạt động của bảng điều khiển tài chính cá nhân tương tác."* — nêu đề
        # ngay, đúng việc lời `bai_noi` sinh ra để làm.
        "mo_ta": "Viết lời thoại video giải thích, quét AST toàn kho, rồi dựng video dọc 720×1280 kèm giọng đọc và phụ đề. CHƯA thiết kế giao diện hay viết API — và bước quét AST không đọc chủ đề, nó quét core/*.py.",
        "cac_phong": ["aura", "delta", "alpha"],
        "tham_so_mac_dinh": "Bảng điều khiển tài chính cá nhân tương tác"
    },
    {
        "id": "card_security_guard",
        "ten": "Quét AST Toàn Kho (chưa quét khoá)",
        "bieu_tuong": "🧾",
        "mau_sac": "#EF4444",
        # Chạy thật 06/09: 3/3 · 83s · 3 hiện vật — và `chan_doan.json` của nó
        # GIỐNG HỆT của `card_polyglot_transpiler`: cùng 119 byte, cùng bốn con
        # số đếm. Hai thẻ hứa hai việc khác hẳn nhau, chạy y một chuỗi, để lại y
        # một thứ. `quet_ast` đếm tệp/dòng/hàm/lớp và bắt lỗi cú pháp; nó không
        # tìm khoá, không kiểm đường dẫn, không xét tiêm lệnh.
        "mo_ta": "Quét AST toàn kho (đếm tệp · dòng · hàm · lớp · lỗi cú pháp), đo RAM và số bài test, ghi báo cáo sổ cái. CHƯA quét khoá, CHƯA kiểm đường dẫn, CHƯA chống tiêm lệnh.",
        "cac_phong": ["delta", "gamma", "omega"],
        "tham_so_mac_dinh": "Audit toàn diện kho mã nguồn AURA v3"
    },
    {
        "id": "card_system_audit",
        "ten": "Đo Máy Thật & Thống Kê Sổ Cái",
        "bieu_tuong": "📊",
        "mau_sac": "#8B5CF6",
        # Chạy thật 06/09: 2/2 · 48s · 2 hiện vật. `metrics.json` có ram · test
        # · toc_do — **không có CPU**. Bản HTML cũ còn hứa "714 test cases";
        # phép đo hôm nay trả về 894. Số gõ tay tụt lại sau phép đo, đúng bệnh
        # câu "đúng 17 tệp" của `CLAUDE.md`.
        "mo_ta": "Đo RAM thật, đếm số bài test thật, đo tốc độ sinh thật, rồi thống kê sổ cái kèm SHA-256. KHÔNG đo CPU.",
        "cac_phong": ["gamma", "omega"],
        "tham_so_mac_dinh": "Full Health Audit"
    }
]


# MỘT bảng mô tả phòng, dùng chung cho BỘ CHẠY · API DANH MỤC · SƠ ĐỒ MÀN HÌNH.
#
# Trước 06/09/2026 tên và mô tả từng bước nằm gõ tay trong `KE_HOACH` của
# `api_chay_pipeline`, còn màn hình có bản sao thứ hai gõ cứng trong
# `noi_bo.html` (5 ô `step_*`). Hai bản thì chúng trôi khỏi nhau, và bản ít
# người nhìn hơn sẽ là bản mục — đúng câu đã viết cho `chay_chuoi_phong`.
def _DICH_MAC_DINH() -> tuple:
    """Ngôn ngữ đích mà `epsilon` THẬT SỰ xin — đọc từ `core/phong_noi_bo.py`.

    Nhập TRONG hàm chứ không ở đầu tệp: hàng rào `test_v3_ranh_gioi.py` lần
    theo `import` thật, và một `import` ở đầu tệp kéo `phong_noi_bo` vào tập
    đóng ngay cả với những đường không dùng tới nó.
    """
    from core.phong_noi_bo import DICH_MAC_DINH

    return tuple(DICH_MAC_DINH)


MO_TA_PHONG: Dict[str, Dict[str, str]] = {
    "zeta": {"ten": "🔍 Zeta (Scout)", "bieu_tuong": "🔍",
             "ngan": "Tra mạng thật",
             "hanh_dong": "Tra mạng thật và ghi biên nhận nguồn"},
    "aura": {"ten": "⚡ AURA (Writer)", "bieu_tuong": "⚡",
             "ngan": "Viết kịch bản",
             "hanh_dong": "Viết kịch bản đạt cửa 215–250 từ"},
    "alpha": {"ten": "🎬 Alpha (Studio)", "bieu_tuong": "🎬",
              "ngan": "Dựng video dọc",
              "hanh_dong": "Dựng video dọc 720×1280 từ kịch bản của AURA"},
    "omega": {"ten": "🎵 Omega (Ledger)", "bieu_tuong": "🎵",
              "ngan": "Đọc sổ cái",
              "hanh_dong": "Đọc sổ cái và viết báo cáo"},
    "gamma": {"ten": "📊 Gamma (Analytics)", "bieu_tuong": "📊",
              "ngan": "Đo RAM · test · tok/s",
              "hanh_dong": "Đo RAM, số bài test, tốc độ sinh"},
    "delta": {"ten": "🩺 Delta (Doctor)", "bieu_tuong": "🩺",
              "ngan": "Quét AST",
              "hanh_dong": "Quét AST toàn kho — chẩn đoán, KHÔNG tự sửa mã"},
    "beta": {"ten": "🧪 Beta (A/B)", "bieu_tuong": "🧪",
             "ngan": "A/B lời nhắc",
             "hanh_dong": "A/B hai biến thể lời nhắc, chấm bằng cửa của AURA"},
    # DANH SÁCH NGÔN NGỮ SUY RA TỪ MÃ, không gõ tay lần nữa.
    #
    # Dòng này từng ghi *"để node/bash chấm bản dịch"* và ở lại nguyên như thế
    # sau khi phòng đã kiểm được **5** ngôn ngữ (`go` 08/09, `cpp`+`rust`
    # 09/09). Nhãn ấy hiện ra màn hình cho Sếp, nên nó đúng họ *"giao diện hứa
    # một việc, mã làm việc khác"* — thứ đã đẻ ra 8 lỗi trong hai ngày 24–25/08.
    #
    # Bắt được 10/09 bằng cách chạy phòng qua HTTP thật, không bằng đọc lại.
    # Nay lấy thẳng từ `DICH_MAC_DINH`: thêm hay bớt một bộ kiểm là nhãn đổi
    # theo, không cần ai nhớ sửa.
    "epsilon": {"ten": "🔤 Epsilon (Dịch mã)", "bieu_tuong": "🔤",
                "ngan": "Dịch mã · trình thật chấm",
                "hanh_dong": "Dịch mã Python rồi để trình thật chấm bản dịch: "
                             + " · ".join(_DICH_MAC_DINH())},
}

# Chuỗi dùng khi KHÔNG có `preset_id`, hoặc `preset_id` không có trong danh mục.
# Đăng ký ở `KY_LUAT_THUC_THI.md` mục 5b (`DAC_TA_CHUOI_MAC_DINH`).
CHUOI_MAC_DINH = ("zeta", "aura", "alpha", "omega", "gamma")


def _mot_buoc(phong_id: str) -> tuple:
    """`(mã phòng, tên hiển thị, việc nó hứa làm)` cho MỘT bước.

    Phòng lạ KHÔNG nổ ở đây. Nó đi tiếp vào `chay_chuoi_phong` và thành `FAIL`
    kèm câu *"không có phòng nào tên X"* — to hơn một `KeyError` 500, và đó là
    chỗ ĐÚNG để nó kêu. Cửa canh danh mục bắt trước ở tầng test.
    """
    mo = MO_TA_PHONG.get(phong_id)
    if mo is None:
        return (phong_id, f"❓ {phong_id}", "phòng không có trong bảng mô tả")
    return (phong_id, mo["ten"], mo["hanh_dong"])


def ke_hoach_cua_the(preset_id) -> List[tuple]:
    """Chuỗi phòng mà một thẻ quy trình khai. Không tìm thấy thẻ thì chuỗi mặc định.

    06/09/2026. `cac_phong` được khai từ đầu nhưng **chưa ai đọc**: đo bằng cách
    thay mọi phòng bằng bản giả rồi đếm phòng nào ĐƯỢC GỌI, cả 8 thẻ chạy y một
    chuỗi 5 phòng — **khớp 0/8**. `delta` có 4 thẻ khai mà chưa lần nào chạy.

    Giá không chỉ là sai nhãn: `card_code_doctor` xin quét AST (~2 s) thì nhận
    thêm `aura` + `alpha`, tức **166 giây** cho việc không ai đặt hàng.
    """
    the = (next((t for t in DANH_SACH_THE_QUY_TRINH if t["id"] == preset_id), None)
           if preset_id else None)
    cac_phong = the["cac_phong"] if the else CHUOI_MAC_DINH
    return [_mot_buoc(p) for p in cac_phong]


async def api_danh_sach_the_quy_trinh(request: web.Request) -> web.Response:
    """Trả về danh sách 8 thẻ quy trình 1-click, KÈM sơ đồ bước của từng thẻ.

    `so_do` dựng từ đúng `ke_hoach_cua_the` mà bộ chạy dùng, nên màn hình không
    thể vẽ một chuỗi khác chuỗi sẽ chạy. Bản trước để giao diện tự đoán: HTML
    gõ cứng 5 ô, thẻ nào bấm cũng hiện 5 ô ấy.
    """
    def _so_do(cac_phong) -> List[Dict[str, str]]:
        ra = []
        for p in cac_phong:
            mo = MO_TA_PHONG.get(p, {})
            ra.append({"phong_id": p, "ten": mo.get("ten", f"❓ {p}"),
                       "bieu_tuong": mo.get("bieu_tuong", "❓"),
                       "ngan": mo.get("ngan", "không có trong bảng mô tả")})
        return ra

    return web.json_response({
        "status": "PASS",
        "so_do_mac_dinh": _so_do(CHUOI_MAC_DINH),
        "presets": [dict(t, so_do=_so_do(t["cac_phong"]))
                    for t in DANH_SACH_THE_QUY_TRINH],
    })


# Trần số bước cho chuỗi TÙY BIẾN. Người gọi tự đặt danh sách bước, và một lượt
# `aura` tốn tới 273 giây — 20 bước là hơn một tiếng rưỡi chẹn một luồng.
TRAN_BUOC_TUY_BIEN = 8


THU_MUC_TIEN_DO = DATA_DIR / "tien_do"

# `pipeline_id` đi thẳng vào TÊN TỆP ở cả hai đầu — client gửi lên khi chạy, và
# gửi lại khi poll. Một luật, dùng ở cả hai chỗ: hai luật thì chúng trôi khỏi
# nhau, và bên lỏng hơn là bên bị lợi dụng.
_MAU_PIPELINE_ID = re.compile(r"[A-Za-z0-9_-]{1,120}")


def pipeline_id_hop_le(pid) -> bool:
    return bool(pid) and bool(_MAU_PIPELINE_ID.fullmatch(str(pid)))


def _ghi_tien_do(pipeline_id: str, dong: Dict[str, Any]) -> None:
    """Ghi MỘT dòng vào sổ tiến độ của một lượt chạy.

    VÌ SAO GHI RA TỆP CHỨ KHÔNG GIỮ TRONG RAM. Cùng lý do sổ cái là tệp: tiến
    trình chết thì RAM mất, tệp còn. Và nó kiểm được bằng cách đọc đĩa — đúng
    nguyên tắc *"bằng chứng trên đĩa là chân lý duy nhất"*.

    NUỐT `OSError` LÀ CÓ CHỦ ĐÍCH VÀ CÓ GIÁ. Đổ cả một chuỗi 166 giây vì không
    ghi được một dòng nhật ký hiển thị thì tệ hơn. Nhưng nó KHÔNG hỏng lặng:
    `/api/tien_do` trả `KHONG_DO_DUOC` khi không có tệp, nên phía đọc nhìn thấy
    "không có tiến độ" chứ không thấy "chưa chạy". Ba trạng thái, không gộp.
    """
    try:
        THU_MUC_TIEN_DO.mkdir(parents=True, exist_ok=True)
        with (THU_MUC_TIEN_DO / f"{pipeline_id}.jsonl").open(
                "a", encoding="utf-8") as f:
            f.write(json.dumps(dong, ensure_ascii=False) + "\n")
    except OSError:
        pass


async def api_doc_tien_do(request: web.Request) -> web.Response:
    """Đọc sổ tiến độ của một lượt. Giao diện poll đường này 1 giây/lần.

    BA TRẠNG THÁI, KHÔNG GỘP:
        chưa có tệp        -> `KHONG_DO_DUOC`, và nói rõ là chưa có tiến độ
        có tệp, chưa XONG  -> `DANG_CHAY`, kèm giây đã trôi của bước hiện tại
        có dòng XONG       -> `XONG`

    Trạng thái thứ hai là thứ Sếp cần nhất: một bước treo 60 giây phải nhìn KHÁC
    HẲN một bước chưa bắt đầu. Thanh tiến trình trông như đang chạy trong khi
    tiến trình đã chết còn tệ hơn không có gì.
    """
    pid = request.match_info.get("pipeline_id", "")
    # Chặn đường dẫn: `pipeline_id` đi từ URL vào tên tệp.
    if not pipeline_id_hop_le(pid):
        return web.json_response(
            {"trang_thai": "KHONG_DO_DUOC", "vi_sao": "pipeline_id không hợp lệ",
             "buoc_dang_chay": None, "giay_da_troi": None,
             "tong_ket": None, "cac_dong": []}, status=400)

    tep = THU_MUC_TIEN_DO / f"{pid}.jsonl"
    if not tep.is_file():
        return web.json_response(
            {"trang_thai": "KHONG_DO_DUOC", "pipeline_id": pid,
             "vi_sao": "chưa có tiến độ nào cho lượt này",
             "buoc_dang_chay": None, "giay_da_troi": None,
             "tong_ket": None, "cac_dong": []})

    dong: List[Dict[str, Any]] = []
    try:
        for d in tep.read_text(encoding="utf-8").splitlines():
            if d.strip():
                dong.append(json.loads(d))
    except (OSError, json.JSONDecodeError) as e:
        return web.json_response(
            {"trang_thai": "KHONG_DO_DUOC", "pipeline_id": pid,
             "vi_sao": f"{type(e).__name__}: {e}",
             "buoc_dang_chay": None, "giay_da_troi": None,
             "tong_ket": None, "cac_dong": []})

    xong = next((d for d in dong if d.get("trang_thai") == "XONG"), None)
    dang = None
    if not xong:
        # Bước đang chạy = bước có DANG_CHAY mà chưa có dòng kết đôi.
        da_xong = {d["buoc"] for d in dong
                   if d.get("trang_thai") not in ("DANG_CHAY", "XONG")}
        dang = next((d for d in dong
                     if d.get("trang_thai") == "DANG_CHAY"
                     and d["buoc"] not in da_xong), None)
    return web.json_response({
        "trang_thai": "XONG" if xong else ("DANG_CHAY" if dang else "KHONG_DO_DUOC"),
        "pipeline_id": pid,
        "buoc_dang_chay": dang,
        "giay_da_troi": (round(
            (datetime.now().astimezone()
             - datetime.fromisoformat(dang["luc"])).total_seconds(), 1)
            if dang else None),
        "tong_ket": xong,
        "cac_dong": dong,
    })


def the_loai_cua_the(preset_id) -> str:
    """Thể loại lời nhắc mà một thẻ quy trình khai. Không khai thì `"truyen"`.

    05/09/2026. Đo 2×2 cho thấy lời nhắc phải khớp THỂ LOẠI đề tài: `lời truyện
    × đề giải thích` chỉ đạt 1/5, trong khi `lời bài nói × đề giải thích` đạt
    3/5. Không cần máy đoán — thẻ đã biết mình làm gì.

    TRẢ `"truyen"` KHI KHÔNG TÌM THẤY, có chủ đích: đây là đường của giao diện,
    một `preset_id` lạ không được làm đổ cả chuỗi. Khác hẳn `viet_kich_ban`, nơi
    thể loại lạ NÉM lỗi — ở đó là lập trình viên gõ sai, phải nổ to.
    """
    if not preset_id:
        return "truyen"
    the = next((t for t in DANH_SACH_THE_QUY_TRINH if t["id"] == preset_id), None)
    return (the or {}).get("the_loai", "truyen")


async def chay_chuoi_phong(ke_hoach: List[tuple], chu_de: str,
                           pipeline_id: str, the_loai: str = "truyen") -> tuple:
    """Chạy một chuỗi phòng theo thứ tự. Trả `(các bước, hiện vật, số bước đạt)`.

    TÁCH RA VÌ CÓ HAI NGƯỜI GỌI. `api_chay_pipeline` (chuỗi 5 bước cố định) và
    `api_pipeline_custom` (chuỗi do người dùng đặt) có cùng một hình dạng: gọi
    phòng thật · bốn trạng thái · dừng khi gãy · nối `aura` sang `alpha`. Để hai
    bản riêng thì chúng trôi khỏi nhau — và bản ít người nhìn hơn sẽ là bản mục.

    BỐN TRẠNG THÁI MỖI BƯỚC, không gộp::

        PASS             phòng chạy và đạt
        FAIL             phòng chạy nhưng không đạt
        KHONG_CHAY_DUOC  thiếu công cụ, mất mạng, hết giờ
        CHUA_CHAY        bước trước gãy nên bước này KHÔNG chạy

    Trạng thái thứ tư là thứ dễ bịa nhất: đánh nó thành `PASS` thì bảng đọc ra
    "cả chuỗi xong", đánh thành `FAIL` thì đọc ra "nó chạy rồi mà hỏng".
    """
    from core.phong_alpha import dung_video
    from core.phong_noi_bo import PHONG
    from core.viet_truyen import viet_kich_ban

    cac_buoc: List[Dict[str, Any]] = []
    hien_vat_tat_ca: List[Dict[str, Any]] = []
    kich_ban = ""          # đầu ra của aura, đầu vào của alpha
    da_gay = False

    def _xong_buoc(buoc: Dict[str, Any]) -> None:
        """PHỄU DUY NHẤT để ghi nhận một bước đã kết thúc.

        Gom ba đường (bỏ qua · phòng lạ · chạy thật) về một chỗ, nên KHÔNG bước
        nào có thể vào `cac_buoc` mà không hiện lên sổ tiến độ. Đó là tiêu chí
        "không bước nào bị bỏ sót" được bảo đảm bằng CẤU TRÚC, không bằng kỷ
        luật của người viết — kỷ luật thì lần sau thêm một nhánh là vỡ.
        """
        cac_buoc.append(buoc)
        _ghi_tien_do(pipeline_id, {
            "buoc": buoc["buoc"], "phong_id": buoc["phong_id"],
            "phong_ten": buoc["phong_ten"], "trang_thai": buoc["trang_thai"],
            "ket_qua": buoc["ket_qua"], "ms": buoc["ms"],
            "so_hien_vat": len(buoc["artifacts"]),
            "luc": datetime.now().astimezone().isoformat(),
        })

    def _bo_qua(i, phong_id, ten, hanh_dong, vi_sao):
        _xong_buoc({"buoc": i, "phong_id": phong_id, "phong_ten": ten,
                    "hanh_dong": hanh_dong, "trang_thai": "CHUA_CHAY",
                    "ket_qua": vi_sao, "artifacts": [], "ms": 0})

    for i, (phong_id, ten, hanh_dong) in enumerate(ke_hoach, 1):
        if da_gay:
            _bo_qua(i, phong_id, ten, hanh_dong, "không chạy vì bước trước gãy")
            continue

        # Phòng lạ là FAIL, không phải bỏ qua im lặng. Chuỗi tùy biến nhận
        # `phong_id` từ người gọi, nên đây là chỗ duy nhất một cái tên bịa có thể
        # đi vào — và nó phải kêu.
        if phong_id not in ("aura", "alpha") and phong_id not in PHONG:
            _xong_buoc({"buoc": i, "phong_id": phong_id, "phong_ten": ten,
                        "hanh_dong": hanh_dong, "trang_thai": "FAIL",
                        "ket_qua": f"không có phòng nào tên {phong_id!r}",
                        "artifacts": [], "ms": 0})
            da_gay = True
            continue

        task_id = f"{pipeline_id}_b{i}_{phong_id}"
        t0 = time.monotonic()
        # Ghi TRƯỚC khi gọi phòng. Ghi sau thì màn hình trắng suốt lúc phòng
        # chạy — đúng thứ cả việc này sinh ra để chữa.
        _ghi_tien_do(pipeline_id, {
            "buoc": i, "phong_id": phong_id, "phong_ten": ten,
            "hanh_dong": hanh_dong, "trang_thai": "DANG_CHAY",
            "luc": datetime.now().astimezone().isoformat(),
        })

        if phong_id == "aura":
            _kq = await asyncio.to_thread(viet_kich_ban, chu_de, the_loai=the_loai)
            tt = "PASS" if _kq["trang_thai"] == "DAT" else _kq["trang_thai"]
            kich_ban = _kq.get("van_ban", "")
            hv: List[Dict[str, Any]] = []
            if kich_ban:
                d = DATA_DIR / "aura" / task_id
                d.mkdir(parents=True, exist_ok=True)
                tep = d / "kich_ban.md"
                tep.write_text(kich_ban + "\n", encoding="utf-8")
                hv = [{"name": tep.name,
                       "path": _duong_trong_kho(tep),
                       "size_bytes": tep.stat().st_size,
                       "sha256": hashlib.sha256(tep.read_bytes()).hexdigest(),
                       "type": "MARKDOWN", "kind": "kich_ban_cho_alpha"}]
            _so = _kq["so"]
            # `lan` RỖNG khi cửa nêu đề fail-closed trước vòng lặp (04/09/2026).
            # `_kq['lan'][-1]` ở đó là IndexError — cả chuỗi đổ 500 thay vì trả
            # về một bước KHONG_CHAY_DUOC đọc được.
            _cuoi = _kq["lan"][-1].get("vi_sao") if _kq["lan"] else _kq.get("vi_sao")
            mo_ta = (f"{_so.get('so_tu')} từ · {_so.get('so_cau_khac')} câu khác nhau · "
                     f"sinh {_kq['so_lan_thu']}/3 lần"
                     if tt == "PASS" else f"{tt}: {_cuoi}")

        elif phong_id == "alpha":
            # Chỗ dây chuyền THẬT SỰ nối: alpha ăn kịch bản của aura.
            if not kich_ban:
                _bo_qua(i, phong_id, ten, hanh_dong,
                        "không có kịch bản từ AURA để dựng")
                da_gay = True
                continue
            _kq = await asyncio.to_thread(
                dung_video, DATA_DIR / "alpha" / task_id, kich_ban)
            tt = _kq["trang_thai"]
            hv = _kq["artifacts"]
            _so = _kq["kiem"].get("so", {})
            mo_ta = (f"{_so.get('rong')}×{_so.get('cao')} · {_so.get('giay')}s · "
                     f"{len(hv)} hiện vật"
                     if tt == "PASS" else f"{tt}: {_kq['vi_sao']}")

        else:
            _kq = await asyncio.to_thread(PHONG[phong_id], task_id, chu_de)
            tt = _kq["trang_thai"]
            hv = _kq["artifacts"]
            mo_ta = (f"{len(hv)} hiện vật thật"
                     if tt == "PASS" else f"{tt}: {_kq['vi_sao']}")
            if tt == "PASS" and _kq["vi_sao"]:
                mo_ta += f" — {_kq['vi_sao']}"

        _xong_buoc({"buoc": i, "phong_id": phong_id, "phong_ten": ten,
                    "hanh_dong": hanh_dong, "trang_thai": tt,
                    "ket_qua": mo_ta, "artifacts": hv,
                    "ms": round((time.monotonic() - t0) * 1000, 1)})
        hien_vat_tat_ca += hv
        if tt != "PASS":
            da_gay = True

    dat = sum(1 for b in cac_buoc if b["trang_thai"] == "PASS")
    # DÒNG KẾT. Không có nó thì giao diện poll mãi mãi, và một tiến trình CHẾT
    # nhìn y hệt một tiến trình chậm — đúng chỗ dễ hỏng nhất của cả việc này.
    _ghi_tien_do(pipeline_id, {
        "buoc": 0, "trang_thai": "XONG", "tong_buoc": len(ke_hoach),
        "buoc_dat": dat, "so_hien_vat": len(hien_vat_tat_ca),
        "luc": datetime.now().astimezone().isoformat(),
    })
    return cac_buoc, hien_vat_tat_ca, dat


def trang_thai_chuoi(cac_buoc: List[Dict[str, Any]], tong: int) -> str:
    """PASS chỉ khi ĐỦ. Không bước nào chạy được thì là KHÔNG ĐO ĐƯỢC."""
    if not cac_buoc:
        return "KHONG_CHAY_DUOC"
    dat = sum(1 for b in cac_buoc if b["trang_thai"] == "PASS")
    if all(b["trang_thai"] in ("KHONG_CHAY_DUOC", "CHUA_CHAY") for b in cac_buoc):
        return "KHONG_CHAY_DUOC"
    return "PASS" if dat == tong else "FAIL"


def ghi_so_cai(dong: Dict[str, Any]) -> str:
    """Ghi một dòng vào sổ cái. Trả lý do hỏng, hoặc chuỗi rỗng.

    KHÔNG nuốt lỗi — đặc tả Chương I cấm thẳng. Ghi sổ hỏng là tin đáng biết: nó
    nghĩa là mọi phép đo sau đó đang đọc một quyển sổ thiếu trang.
    """
    try:
        OMEGA_SO_CAI.parent.mkdir(parents=True, exist_ok=True)
        with open(OMEGA_SO_CAI, "a", encoding="utf-8") as f:
            f.write(json.dumps(dong, ensure_ascii=False) + "\n")
    except OSError as e:
        return f"{type(e).__name__}: {e}"
    return ""


async def api_chay_pipeline(request: web.Request) -> web.Response:
    """Chuỗi 5 bước cố định — gọi phòng thật, nối đầu ra vào đầu vào.

    Trước 03/09/2026 hàm này dài 91 dòng và **mọi trường đều gõ tay**: 5 lần
    `"trang_thai": "PASS"`, `"Đã thu thập 6 nguồn tin uy tín"`, `"kịch bản 1.800
    từ"` (kịch bản thật là 215–250 từ), `"Đạt 100% Hard Gates"`. Nó không gọi
    phòng nào — nhưng **CÓ ghi vào `so_cai.jsonl`** với `"status": "PASS"`, tức
    để lại dấu vết của việc chưa từng xảy ra.

    Đó là lỗ trong chính cửa fail-closed: cửa hỏi *"có để lại byte nào không?"*,
    và một hàm ghi sổ về việc nó không làm thì trả lời được câu ấy.

    Chạy thật: `5/5 bước · 22 hiện vật · 166 s`. Bản gõ tay chạy 0 ms.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}

    chu_de = data.get("chu_de", "Khởi tạo chiến dịch tự động").strip()
    preset_id = data.get("preset_id")
    # Client được đặt `pipeline_id` để nó POLL tiến độ NGAY, không phải đợi tới
    # cuối chuỗi mới biết id — mà cuối chuỗi thì hết cái để xem.
    #
    # ID này đi vào TÊN TỆP, nên phải qua đúng luật mà đầu đọc dùng. Không hợp
    # lệ thì máy tự sinh, KHÔNG ném: đây là đường của giao diện, một id xấu
    # không được làm hỏng cả lượt chạy — nhưng cũng không được đi vào đĩa.
    _xin = data.get("pipeline_id")
    pipeline_id = (str(_xin) if pipeline_id_hop_le(_xin)
                   else f"pipe_{int(time.time())}_{uuid4().hex[:4]}")
    bat_dau = time.monotonic()

    # CHUỖI DO THẺ QUYẾT ĐỊNH, không gõ cứng 5 bước nữa (06/09/2026). Trước đó
    # `cac_phong` được khai trên cả 8 thẻ mà không ai đọc: đếm phòng được gọi
    # thì khớp **0/8**, và `delta` — 4 thẻ khai — chưa lần nào chạy.
    KE_HOACH = ke_hoach_cua_the(preset_id)
    # Thẻ khai thể loại; không khai thì `"truyen"` như cũ. `preset_id` trước
    # 05/09/2026 chỉ được ghi vào sổ cái rồi vứt — nay nó quyết định hai thứ.
    cac_buoc, hien_vat, dat = await chay_chuoi_phong(
        KE_HOACH, chu_de, pipeline_id, the_loai_cua_the(preset_id))
    trang_thai = trang_thai_chuoi(cac_buoc, len(KE_HOACH))
    thoi_gian_ms = round((time.monotonic() - bat_dau) * 1000, 1)

    loi_ghi_so = ghi_so_cai({
        "task_id": pipeline_id, "phong_id": "pipeline",
        "preset_id": preset_id or "auto", "yeu_cau": chu_de[:200],
        "timestamp": datetime.now().isoformat(),
        "status": trang_thai, "latency_ms": thoi_gian_ms,
        "buoc_dat": dat, "tong_buoc": len(KE_HOACH),
    })

    return web.json_response({
        "status": trang_thai,
        "pipeline_id": pipeline_id,
        "chu_de": chu_de,
        "preset_id": preset_id,
        "tong_buoc": len(KE_HOACH),
        "buoc_dat": dat,
        "cac_buoc": cac_buoc,
        "so_hien_vat": len(hien_vat),
        "tong_thoi_gian_ms": thoi_gian_ms,
        "loi_ghi_so_cai": loi_ghi_so,
        # Không có câu "hoàn thành xuất sắc 100%!" nữa. Con số tự nói.
        "thong_diep": f"{dat}/{len(KE_HOACH)} bước đạt · "
                      f"{len(hien_vat)} hiện vật thật trên đĩa"
                      + (f" · LỖI GHI SỔ: {loi_ghi_so}" if loi_ghi_so else ""),
    })


async def api_polyglot_languages(request: web.Request) -> web.Response:
    """Trả về danh sách 8 ngôn ngữ lập trình được hỗ trợ."""
    return web.json_response({
        "status": "PASS",
        "languages": lay_danh_sach_ngon_ngu()
    })


async def api_polyglot_translate(request: web.Request) -> web.Response:
    """Chuyển đổi mã nguồn giữa các ngôn ngữ (Transpiler)."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "FAIL", "error": "JSON không hợp lệ"}, status=400)

    ma = data.get("ma", "")
    lang_nguon = data.get("lang_nguon", "python")
    lang_dich = data.get("lang_dich", "javascript")

    if not ma.strip():
        return web.json_response({"status": "FAIL", "error": "Mã nguồn không được để trống"}, status=400)

    res = chuyen_doi_ngon_ngu(ma, lang_nguon, lang_dich)
    return web.json_response(res)


async def api_polyglot_validate(request: web.Request) -> web.Response:
    """Kiểm tra tính hợp lệ cú pháp của đoạn mã theo ngôn ngữ chỉ định."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "FAIL", "error": "JSON không hợp lệ"}, status=400)

    ma = data.get("ma", "")
    lang = data.get("lang", "python")

    res = kiem_tra_cu_phap_da_ngon_ngu(ma, lang)
    return web.json_response(res)


async def api_polyglot_run(request: web.Request) -> web.Response:
    """Chạy mã trong một tiến trình con, có trần thời gian. KHÔNG có hộp cát.

    Câu này trước đây viết "an toàn ... môi trường cô lập". Đo được: mã chạy ở
    `D:/AURA_v3` với đủ quyền tài khoản Windows, ghi được tệp ra ngoài thư mục
    tạm, đọc được thư mục HOME. Chỉ có `timeout`.

    Và cổng này KHÔNG có mã thông hành, KHÔNG kiểm Origin, KHÔNG có cờ
    `--allow-exec` — khác hẳn app thẻ (bốn lớp cổng vào). `noi_bo_app.py` mặc
    định bind 127.0.0.1 nhưng đọc biến `AURA_NOI_BO_HOST`, nên một biến môi
    trường là mở ra LAN.
    """
    ly_do = cua_chay_ma(request.headers)
    if ly_do is not None:
        return web.json_response(
            {"status": "BLOCKED", "error": ly_do}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "FAIL", "error": "JSON không hợp lệ"}, status=400)

    ma = data.get("ma", "")
    lang = data.get("lang", "python")
    timeout_s = float(data.get("timeout_s", 5.0))

    if not ma.strip():
        return web.json_response({"status": "FAIL", "error": "Mã nguồn không được để trống"}, status=400)

    res = chay_ma_da_ngon_ngu(ma, lang, timeout_s=timeout_s)

    # Ghi nhận lần chạy vào sổ cái Omega
    try:
        task_id = f"run_{lang}_{int(time.time())}_{uuid4().hex[:4]}"
        dong_so = {
            "task_id": task_id,
            "phong_id": "delta",
            "lang": lang,
            "yeu_cau": f"Run code {lang} ({len(ma)} chars)",
            "timestamp": datetime.now().isoformat(),
            "status": res.get("status", "FAIL"),
            "latency_ms": res.get("latency_ms", 0.0)
        }
        with open(OMEGA_SO_CAI, "a", encoding="utf-8") as f:
            f.write(json.dumps(dong_so, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return web.json_response(res)


async def api_pipeline_custom(request: web.Request) -> web.Response:
    """Chuỗi TÙY BIẾN — người gọi đặt danh sách bước, và phòng chạy THẬT.

    Bản trước 04/09/2026 dài 17 dòng và không gọi phòng nào. Nó lặp qua các bước
    người dùng gửi lên rồi dán `'trang_thai': 'PASS'` cho từng bước và
    `'status': 'PASS'` cho cả lượt — kể cả khi `phong_id` là một cái tên bịa.
    Không ghi byte nào, nên cửa fail-closed của `/api/dispatch` không đụng tới
    nó; nó nằm ở một đường khác.

    Đây là chỗ cuối cùng còn gõ tay `PASS` trong tệp này. Tìm ra 04/09 khi vẽ sơ
    đồ cây các phòng — không phải khi đọc mã, mà khi phải trả lời câu *"đường này
    có thật không"* cho một hình vẽ.

    BA THỨ CHUỖI CỐ ĐỊNH KHÔNG CẦN MÀ CHUỖI NÀY CẦN:

    * **Tên phòng đến từ người gọi**, nên một cái tên bịa phải là `FAIL` — không
      phải bỏ qua im lặng, cũng không phải `PASS`.
    * **Trần số bước.** Một lượt `aura` tốn tới 273 giây; 20 bước là hơn một
      tiếng rưỡi chẹn một luồng.
    * **Danh sách rỗng là `KHONG_CHAY_DUOC`**, không phải `PASS`. Chạy 0 bước rồi
      báo đạt là đúng cái bệnh cả tệp này vừa chữa.
    """
    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"status": "FAIL", "error": "JSON không hợp lệ"}, status=400)

    ten_pipeline = data.get("ten", "Quy Trình Tùy Biến")
    dau_vao = data.get("cac_buoc") or []
    chu_de = (data.get("chu_de") or ten_pipeline).strip()
    pipeline_id = f"custom_pipe_{int(time.time())}_{uuid4().hex[:4]}"
    bat_dau = time.monotonic()

    if not isinstance(dau_vao, list) or not dau_vao:
        return web.json_response({
            "status": "KHONG_CHAY_DUOC", "pipeline_id": pipeline_id,
            "ten": ten_pipeline, "tong_buoc": 0, "buoc_dat": 0, "cac_buoc": [],
            "error": "không có bước nào để chạy",
            "tong_thoi_gian_ms": 0.0}, status=400)

    if len(dau_vao) > TRAN_BUOC_TUY_BIEN:
        return web.json_response({
            "status": "KHONG_CHAY_DUOC", "pipeline_id": pipeline_id,
            "ten": ten_pipeline, "tong_buoc": len(dau_vao), "buoc_dat": 0,
            "cac_buoc": [],
            "error": f"{len(dau_vao)} bước, trần là {TRAN_BUOC_TUY_BIEN} — "
                     f"một lượt `aura` tốn tới 273 giây",
            "tong_thoi_gian_ms": 0.0}, status=400)

    KE_HOACH = [(str(b.get("phong_id", "aura")).lower(),
                 f"Phòng {str(b.get('phong_id', 'aura')).upper()}",
                 str(b.get("hanh_dong", "Thực thi nhiệm vụ")))
                for b in dau_vao]

    cac_buoc, hien_vat, dat = await chay_chuoi_phong(KE_HOACH, chu_de, pipeline_id)
    trang_thai = trang_thai_chuoi(cac_buoc, len(KE_HOACH))
    thoi_gian_ms = round((time.monotonic() - bat_dau) * 1000, 1)

    loi_ghi_so = ghi_so_cai({
        "task_id": pipeline_id, "phong_id": "pipeline_custom",
        "ten": ten_pipeline[:120], "yeu_cau": chu_de[:200],
        "timestamp": datetime.now().isoformat(),
        "status": trang_thai, "latency_ms": thoi_gian_ms,
        "buoc_dat": dat, "tong_buoc": len(KE_HOACH),
    })

    return web.json_response({
        "status": trang_thai,
        "pipeline_id": pipeline_id,
        "ten": ten_pipeline,
        "tong_buoc": len(KE_HOACH),
        "buoc_dat": dat,
        "cac_buoc": cac_buoc,
        "so_hien_vat": len(hien_vat),
        "tong_thoi_gian_ms": thoi_gian_ms,
        "loi_ghi_so_cai": loi_ghi_so,
        "thong_diep": f"{dat}/{len(KE_HOACH)} bước đạt · "
                      f"{len(hien_vat)} hiện vật thật trên đĩa"
                      + (f" · LỖI GHI SỔ: {loi_ghi_so}" if loi_ghi_so else ""),
    })


# ==============================================================================
# 6. API SỔ CÁI & BẰNG CHỨNG THẬT TRÊN ĐĨA
# ==============================================================================
async def api_doc_so_cai(request: web.Request) -> web.Response:
    """Đọc dữ liệu từ Sổ cái nhiệm vụ Omega (data/omega/so_cai.jsonl)."""
    danh_sach = []
    if OMEGA_SO_CAI.is_file():
        try:
            with open(OMEGA_SO_CAI, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            danh_sach.append(json.loads(line))
                        except Exception:
                            pass
        except Exception as err:
            return web.json_response({"status": "FAIL", "error": str(err)}, status=500)

    # Đảo ngược để việc mới nhất lên đầu, giới hạn 50 việc
    danh_sach = list(reversed(danh_sach))[:50]
    return web.json_response({
        "status": "PASS",
        "tong_so": len(danh_sach),
        "so_cai_path": str(OMEGA_SO_CAI),
        "entries": danh_sach
    })


async def api_doc_evidence_runs(request: web.Request) -> web.Response:
    """Đọc danh sách các run Evidence Sprint trên đĩa."""
    runs = []
    if EVIDENCE_DIR.is_dir():
        try:
            for item in sorted(EVIDENCE_DIR.iterdir(), reverse=True):
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    metrics_file = item / "metrics.json"
                    info: Dict[str, Any] = {
                        "run_id": item.name,
                        "has_manifest": manifest_file.is_file(),
                        "has_metrics": metrics_file.is_file(),
                        "status": "UNKNOWN"
                    }
                    if metrics_file.is_file():
                        try:
                            m = json.loads(metrics_file.read_text(encoding="utf-8"))
                            info["status"] = m.get("overall_status", "PASS")
                            info["metrics"] = m
                        except Exception:
                            pass
                    runs.append(info)
        except Exception as err:
            return web.json_response({"status": "FAIL", "error": str(err)}, status=500)

    return web.json_response({
        "status": "PASS",
        "tong_so_runs": len(runs),
        "evidence_dir": str(EVIDENCE_DIR),
        "runs": runs[:30]
    })
