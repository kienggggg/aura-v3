# -*- coding: utf-8 -*-
"""the_api.py — API Handlers cho App Lập trình bằng THẺ v1.

Triển khai 4 LỚP BẢO MẬT BẮT BUỘC theo Mục 13.2 & 14.2:
1. Chỉ nghe 127.0.0.1 (Loopback).
2. Mã thông hành ngẫu nhiên (Auth Token 32-hex) per-app qua header X-Auth-Token (hoặc query param ?token=).
3. Kiểm tra Origin / Referer ngăn chặn CSRF từ website ngoài.
4. Path Confinement & Whitelist phiên per-app: /api/luu_tep chỉ được ghi vào file đã mở hoặc trong workspace.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
import secrets
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlsplit

from aiohttp import web

from core.the_v1 import (
    BO_THE_V1,
    NHOM_THE,
    TheNode,
    chay_ma_tien_trinh_rieng,
    kiem_tra_cay_the,
    sinh_ma_python,
)
from core.the_cst import (
    doc_chuoi_py_sang_cay_the as _doc_chuoi_cst,
    luu_cay_the_ra_tep_py,
)
from core.trace_runtime import (
    chay_trace_mot_test,
    chot_test_can_trace,
)
from core.lat_nguoc import doc_thong_tin_gioi_han
from core.nhip_thuc_thi import (
    chia_nhip_thuc_thi,
    phan_tich_nhip_cho_ham,
)


def doc_chuoi_py_sang_cay_the(nguon, duong_dan=None):
    """Bọc lại đúng một chỗ: handler lưu truyền BYTES, `the_cst` nhận CHUỖI."""
    if isinstance(nguon, (bytes, bytearray)):
        nguon = bytes(nguon).decode("utf-8")
    return _doc_chuoi_cst(nguon, duong_dan)


DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# TÀI NGUYÊN WEB NEO VÀO CHÍNH GÓI, KHÔNG SUY TỪ THƯ MỤC DỰ ÁN.
#
# 25/08: trước đây `static_dir` suy từ `project_root`. Chạy thử trỏ
# `project_root` sang một dự án khác: `static_dir` đi theo, và `index.html`
# KHÔNG tồn tại ở đó — app không phục vụ nổi giao diện.
#
# Đó là chỗ chặn chính của việc đóng gói: cài xong thì mã app nằm ở
# `site-packages`, còn mã người dùng nằm chỗ khác hẳn. Hai thứ ấy phải rời
# nhau ra. `__file__` của chính tệp này là cái neo đúng — nó luôn nằm cạnh
# thư mục `web/`, dù chạy từ kho hay từ gói đã cài.
STATIC_DIR_GOI = (Path(__file__).resolve().parent / "web" / "the_v1")
DEFAULT_STATIC_DIR = STATIC_DIR_GOI
ALLOWED_SCAN_DIRS: Tuple[str, ...] = ("core", "interface", "tests")
LOOPBACK: Set[str] = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class AppConfig:
    """Cấu hình bất biến theo từng app instance."""
    project_root: Path
    static_dir: Path
    allowed_scan_dirs: Tuple[str, ...] = ("core", "interface", "tests")
    auth_token: str = field(default_factory=lambda: secrets.token_hex(16))
    allow_code_execution: bool = False


@dataclass
class AppRuntimeState:
    """Trạng thái runtime có thể thay đổi theo từng app instance."""
    opened_files_whitelist: Set[str] = field(default_factory=set)
    busy_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    busy_info: Dict[str, Any] = field(default_factory=lambda: {"is_busy": False, "job_id": None, "start_time": None})
    active_job_process: Optional[Any] = None
    cleanup_task: Optional[asyncio.Task] = None


# Module-level defaults for backward compatibility
AUTH_TOKEN = secrets.token_hex(16)
ALLOW_CODE_EXECUTION = os.environ.get("AURA_THE_ALLOW_CODE_EXECUTION", "").strip() == "1"
ALLOWED_ROOTS: List[Path] = [DEFAULT_PROJECT_ROOT]
OPENED_FILES_WHITELIST: Set[str] = set()
E1_LOCK = asyncio.Lock()


def lay_config(request: Optional[web.Request] = None) -> AppConfig:
    """Lấy AppConfig từ request.app hoặc trả về cấu hình mặc định."""
    if request is not None and "aura_config" in request.app:
        return request.app["aura_config"]
    if request is not None and "project_root" in request.app:
        root = Path(request.app["project_root"]).resolve(strict=False)
        allow_exec = bool(request.app.get("allow_code_execution", ALLOW_CODE_EXECUTION))
        token = str(request.app.get("auth_token", AUTH_TOKEN))
        return AppConfig(
            project_root=root,
            static_dir=STATIC_DIR_GOI.resolve(strict=False),
            allowed_scan_dirs=ALLOWED_SCAN_DIRS,
            auth_token=token,
            allow_code_execution=allow_exec,
        )
    return AppConfig(
        project_root=DEFAULT_PROJECT_ROOT.resolve(strict=False),
        static_dir=DEFAULT_STATIC_DIR.resolve(strict=False),
        allowed_scan_dirs=ALLOWED_SCAN_DIRS,
        auth_token=AUTH_TOKEN,
        allow_code_execution=ALLOW_CODE_EXECUTION,
    )


def lay_runtime(request: Optional[web.Request] = None) -> AppRuntimeState:
    """Lấy AppRuntimeState từ request.app hoặc trả về state dự phòng."""
    if request is not None and "aura_runtime" in request.app:
        return request.app["aura_runtime"]
    return AppRuntimeState(
        opened_files_whitelist=OPENED_FILES_WHITELIST,
        busy_lock=E1_LOCK,
        busy_info={"is_busy": False, "job_id": None, "start_time": None},
    )


def lay_project_root(request: Optional[web.Request] = None) -> Path:
    return lay_config(request).project_root


def lay_allow_code_execution(request: Optional[web.Request] = None) -> bool:
    return lay_config(request).allow_code_execution


# ==============================================================================
# BẢO MẬT: KIỂM TRA MÃ THÔNG HÀNH & NGUỒN GỐC REQUEST
# ==============================================================================

def xac_thuc_request(request: web.Request) -> bool:
    """Kiểm tra mã thông hành qua Header X-Auth-Token hoặc Query param ?token=."""
    token = request.headers.get("X-Auth-Token")
    if not token:
        token = request.query.get("token")
    if not token:
        return False
    expected = lay_config(request).auth_token
    return hmac.compare_digest(token, expected)


def kiem_tra_origin_hop_le(request: web.Request) -> bool:
    """Kiểm tra chặt chẽ Origin / Referer ngăn chặn CSRF và Hostname giả."""
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")

    if origin is not None:
        origin = origin.strip()
        if not origin:
            return True
        try:
            u = urlsplit(origin)
        except Exception:
            return False
        if u.scheme.lower() not in ("http", "https"):
            return False
        if u.username or u.password:
            return False
        if u.path not in ("", "/") or u.query or u.fragment:
            return False
        if (u.hostname or "").lower() not in LOOPBACK:
            return False
        try:
            if u.port is not None and not (1 <= u.port <= 65535):
                return False
        except ValueError:
            return False
        return True

    if referer is not None:
        referer = referer.strip()
        if not referer:
            return True
        try:
            u = urlsplit(referer)
        except Exception:
            return False
        if u.scheme.lower() not in ("http", "https"):
            return False
        if u.username or u.password:
            return False
        if (u.hostname or "").lower() not in LOOPBACK:
            return False
        try:
            if u.port is not None and not (1 <= u.port <= 65535):
                return False
        except ValueError:
            return False
        return True

    return True


def _co_the_da_sua(nodes: List[TheNode]) -> bool:
    for n in nodes:
        if n.da_sua or _co_the_da_sua(n.than):
            return True
    return False


def _doc_cay_the(data: Any, *, depth: int = 0, counter: Optional[List[int]] = None) -> List[TheNode]:
    if counter is None:
        counter = [0]
    if depth > 100 or not isinstance(data, list):
        raise ValueError("Cây thẻ phải là danh sách và không sâu quá 100 cấp")
    result: List[TheNode] = []
    for item in data:
        counter[0] += 1
        if counter[0] > 10_000:
            raise ValueError("Cây thẻ vượt quá 10.000 nút")
        if not isinstance(item, dict):
            raise ValueError("Mỗi thẻ phải là một object JSON")
        if not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("Mỗi thẻ phải có id chuỗi không rỗng")
        if item.get("ma") not in BO_THE_V1:
            raise ValueError(f"Mã thẻ không được hỗ trợ: {item.get('ma')!r}")
        if not isinstance(item.get("o", {}), dict) or not isinstance(item.get("than", []), list):
            raise ValueError("Trường o phải là object và than phải là danh sách")
        node = TheNode.from_dict(item)
        node.than = _doc_cay_the(item.get("than", []), depth=depth + 1, counter=counter)
        result.append(node)
    return result


def _xoa_co_da_sua(nodes: List[TheNode]) -> None:
    for node in nodes:
        node.da_sua = False
        _xoa_co_da_sua(node.than)


def _rang_buoc_cau_truc_va_danh_dau(
    current: List[TheNode], submitted: List[TheNode], path: str = "root"
) -> Optional[str]:
    if len(current) != len(submitted):
        return f"{path}: số thẻ đã thay đổi"
    for index, (old, new) in enumerate(zip(current, submitted)):
        here = f"{path}[{index}]"
        if old.id != new.id:
            return f"{here}: id hoặc thứ tự thẻ đã thay đổi"
        if old.ma != new.ma:
            return f"{here}: loại thẻ đã thay đổi"
        new.da_sua = new.o != old.o or (
            new.ma == "ma_tho"
            and new.o.get("nguyen_van", new.raw_text or "")
            != old.o.get("nguyen_van", old.raw_text or "")
        )
        problem = _rang_buoc_cau_truc_va_danh_dau(old.than, new.than, f"{here}.than")
        if problem:
            return problem
    return None


def _xac_nhan_o_da_duoc_ap_dung(
    submitted: List[TheNode], reparsed: List[TheNode], path: str = "root"
) -> Optional[str]:
    if len(submitted) != len(reparsed):
        return f"{path}: cấu trúc sau lưu không còn khớp"
    for index, (wanted, actual) in enumerate(zip(submitted, reparsed)):
        here = f"{path}[{index}]"
        if wanted.id != actual.id or wanted.ma != actual.ma:
            return f"{here}: định danh sau lưu không còn khớp"
        if wanted.da_sua and wanted.o != actual.o:
            return f"{here}: giá trị ô sửa không được backend áp dụng đầy đủ"
        problem = _xac_nhan_o_da_duoc_ap_dung(wanted.than, actual.than, f"{here}.than")
        if problem:
            return problem
    return None


def _ghi_nguyen_tu(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            tmp_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        tmp_name = None
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)


def kiem_tra_duong_dan_an_toan(duong_dan_str: str, request: Optional[web.Request] = None) -> Optional[Path]:
    """Kiểm tra Path Confinement: Chặn .. và chỉ cho phép thao tác trong project_root."""
    if not duong_dan_str or ".." in duong_dan_str:
        return None
    project_root = lay_project_root(request)
    runtime = lay_runtime(request)
    try:
        p = Path(duong_dan_str)
        if not p.is_absolute():
            resolved = (project_root / p).resolve(strict=False)
        else:
            resolved = p.resolve(strict=False)
    except Exception:
        return None

    # Phải nằm trong project_root, ALLOWED_ROOTS, hoặc trong whitelist phiên
    str_resolved = str(resolved).lower()
    in_whitelist = any(str_resolved == w.lower() for w in runtime.opened_files_whitelist)
    in_root = resolved.is_relative_to(project_root) or any(
        resolved.is_relative_to(r.resolve(strict=False)) for r in ALLOWED_ROOTS
    )

    if in_whitelist or in_root:
        return resolved
    return None


# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================

async def trang_chu(request: web.Request) -> web.Response:
    """Phục vụ trang chủ index.html."""
    config = lay_config(request)
    index_file = config.static_dir / "index.html"
    if not index_file.is_file():
        return web.Response(text="<h1>Không tìm thấy interface/web/the_v1/index.html</h1>", content_type="text/html", status=404)
    content = index_file.read_text(encoding="utf-8")
    return web.Response(text=content, content_type="text/html")


async def file_tinh(request: web.Request) -> web.Response:
    """Phục vụ các file tĩnh (CSS, JS, SVG, JSON)."""
    config = lay_config(request)
    filename = request.match_info.get("filename", "")
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        return web.Response(text="403 Forbidden", status=403)
    target_path = (config.static_dir / filename).resolve(strict=False)
    if not target_path.is_file() or not target_path.is_relative_to(config.static_dir.resolve(strict=False)):
        return web.Response(text="404 Not Found", status=404)

    content_type = "text/plain"
    if target_path.suffix == ".html":
        content_type = "text/html"
    elif target_path.suffix == ".css":
        content_type = "text/css"
    elif target_path.suffix == ".js":
        content_type = "application/javascript"
    elif target_path.suffix == ".json":
        content_type = "application/json"
    elif target_path.suffix == ".svg":
        content_type = "image/svg+xml"

    return web.Response(body=target_path.read_bytes(), content_type=content_type)


async def api_status(request: web.Request) -> web.Response:
    """Trả về trạng thái máy chủ."""
    config = lay_config(request)
    allow_exec = config.allow_code_execution
    return web.json_response({
        "app": "AURA_THE_v1",
        "status": "ready",
        "code_execution_enabled": allow_exec,
        "cac_cong_thuc_thi": ["/api/chay", "/api/trace", "/api/dinh_vi_loi"],
        "e1_limitation": doc_thong_tin_gioi_han(config.project_root),
        "execution_info": (
            "Đã bật có chủ đích: cho phép /api/chay, /api/trace, /api/dinh_vi_loi; chưa cô lập toàn diện tệp/mạng/RAM"
            if allow_exec else
            "Tắt mặc định: các cổng thực thi (/api/chay, /api/trace, /api/dinh_vi_loi) đều bị khóa"
        ),
        "security": {
            "loopback_only": True,
            "auth_token_required": True,
            "origin_check": True,
            "path_confinement": True,
            "execution_gate": True,
        }
    })


async def api_danh_sach_tep(request: web.Request) -> web.Response:
    """GET /api/tep_tin — Liệt kê danh sách tệp .py và .json an toàn trong kho."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ hoặc bị thiếu"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    config = lay_config(request)
    project_root = config.project_root
    thu_muc_query = request.query.get("thu_muc", "").strip()

    if thu_muc_query:
        if ".." in thu_muc_query or Path(thu_muc_query).is_absolute():
            return web.json_response({"error": "400 Bad Request: Đường dẫn thư mục không hợp lệ"}, status=400)
        
        # Hàng rào fail-closed: Phải thuộc đúng config.allowed_scan_dirs (không có data)
        parts = Path(thu_muc_query).parts
        if not parts or parts[0] not in config.allowed_scan_dirs:
            return web.json_response({"error": "403 Forbidden: Thư mục ngoài danh mục cho phép"}, status=403)

        target_dir = (project_root / thu_muc_query).resolve(strict=False)
        if not target_dir.is_dir() or not target_dir.is_relative_to(project_root):
            return web.json_response({"error": "400 Bad Request: Thư mục không tồn tại hoặc ngoài phạm vi"}, status=400)
        scan_targets = [target_dir]
    else:
        scan_targets = [
            (project_root / d).resolve(strict=False)
            for d in config.allowed_scan_dirs
            if (project_root / d).is_dir()
        ]

    ket_qua = []
    for d in scan_targets:
        if not d.is_dir() or not d.is_relative_to(project_root):
            continue
        for root, dirs, files in os.walk(d):
            dirs[:] = [sub for sub in dirs if not sub.startswith(".") and sub != "__pycache__" and sub != "venv"]
            for fname in sorted(files):
                if fname.startswith("."):
                    continue
                ext = Path(fname).suffix.lower()
                if ext in (".py", ".json"):
                    full_p = (Path(root) / fname).resolve(strict=False)
                    if full_p.is_file() and full_p.is_relative_to(project_root):
                        rel = str(full_p.relative_to(project_root)).replace("\\", "/")
                        file_bytes = full_p.read_bytes()
                        sha256_hex = hashlib.sha256(file_bytes).hexdigest()
                        ket_qua.append({
                            "duong_dan": rel,
                            "ten_tep": full_p.name,
                            "kich_thuoc": full_p.stat().st_size,
                            "duoi_tep": ext,
                            "sha256": sha256_hex,
                        })

    ket_qua.sort(key=lambda x: x["duong_dan"])
    return web.json_response({
        "thu_muc": thu_muc_query or "all",
        "danh_sach": ket_qua,
        "tong_so": len(ket_qua),
    })


async def api_kiem_tra(request: web.Request) -> web.Response:
    """POST /api/kiem — Nhận cây thẻ, trả danh sách lỗi Đỏ và cảnh báo Vàng."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ hoặc bị thiếu"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        tree_data = data.get("tree", [])
        nodes = [TheNode.from_dict(item) for item in tree_data]
        res = kiem_tra_cay_the(nodes)
        
        return web.json_response({
            "hop_le": res.hop_le,
            "so_loi_do": res.so_loi_do,
            "so_canh_bao_vang": res.so_canh_bao_vang,
            "danh_sach": [
                {
                    "muc_do": d.muc_do,
                    "ma_loi": d.ma_loi,
                    "thong_diep": d.thong_diep,
                    "node_id": d.node_id,
                    "line": d.line,
                }
                for d in res.danh_sach
            ],
            "so_lan_dung_the": res.so_lan_dung_the,
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi kiểm tra cây thẻ: {str(e)}"}, status=400)


async def api_chay_ma(request: web.Request) -> web.Response:
    """POST /api/chay — Chạy mã chỉ khi người vận hành bật rõ cờ allow_code_execution."""
    # 1. Hàng rào xác thực & Origin
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    # 2. Hàng rào thực thi (trước khi parse JSON)
    if not lay_allow_code_execution(request):
        return web.json_response({
            "trang_thai": "bi_khoa",
            "error": "Chạy mã/test đang tắt mặc định"
        }, status=403)

    try:
        data = await request.json()
        code = data.get("code")
        if code is None and "tree" in data:
            nodes = [TheNode.from_dict(item) for item in data["tree"]]
            code = sinh_ma_python(nodes)
        
        if not code:
            return web.json_response({"error": "Mã thực thi trống"}, status=400)

        res = await asyncio.to_thread(chay_ma_tien_trinh_rieng, code, timeout=5.0)
        return web.json_response({
            "status": res.status,
            "exit_code": res.exit_code,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "wall_time_ms": res.wall_time_ms,
            "timed_out": res.timed_out,
            "execution_notice": "Tiến trình riêng, trần 5s; vẫn có quyền ghi tệp của tài khoản Windows",
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi thực thi mã: {str(e)}"}, status=500)


async def api_mo_tep(request: web.Request) -> web.Response:
    """POST /api/mo_tep — Mở một tệp .py từ đĩa, chuyển thành cây thẻ kèm SHA-256."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        duong_dan_str = data.get("duong_dan", "")
        safe_path = kiem_tra_duong_dan_an_toan(duong_dan_str, request)
        if not safe_path or not safe_path.is_file():
            return web.json_response({"error": f"Đường dẫn tệp không hợp lệ hoặc không tồn tại: {duong_dan_str}"}, status=400)

        if safe_path.suffix.lower() not in (".py", ".json"):
            return web.json_response({"error": "Chỉ mở tệp .py hoặc .json"}, status=400)

        config = lay_config(request)
        runtime = lay_runtime(request)

        raw_bytes = safe_path.read_bytes()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        if safe_path.suffix.lower() == ".json":
            tree_data = json.loads(raw_bytes.decode("utf-8"))
            nodes = _doc_cay_the(tree_data)
            _xoa_co_da_sua(nodes)
            tree_payload = [n.to_dict() for n in nodes]
            newline = "CRLF" if b"\r\n" in raw_bytes else "LF"
            so_dong = len(raw_bytes.decode("utf-8").splitlines())
        else:
            record = doc_chuoi_py_sang_cay_the(raw_bytes, str(safe_path))
            tree_payload = [n.to_dict() for n in record.tree]
            newline = "CRLF" if record.newline == "\r\n" else "LF"
            so_dong = len(record.lines)

        try:
            rel_path = str(safe_path.relative_to(config.project_root)).replace("\\", "/")
        except ValueError:
            rel_path = str(safe_path).replace("\\", "/")
        runtime.opened_files_whitelist.add(str(safe_path))
        runtime.opened_files_whitelist.add(rel_path)

        return web.json_response({
            "duong_dan": str(safe_path),
            "duong_dan_rel": rel_path,
            "ten_tep": safe_path.name,
            "tree": tree_payload,
            "newline": newline,
            "so_dong": so_dong,
            "sha256": sha256_hash,
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi mở tệp: {str(e)}"}, status=500)


async def api_luu_tep(request: web.Request) -> web.Response:
    """POST /api/luu_tep — Lưu cây thẻ vào file .py (lossless) hoặc file .json."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        duong_dan_str = data.get("duong_dan", "")
        safe_path = kiem_tra_duong_dan_an_toan(duong_dan_str, request)
        if not safe_path:
            return web.json_response({"error": "403 Forbidden: Đường dẫn không nằm trong danh sách được phép ghi"}, status=403)

        tree_data = data.get("tree")
        try:
            nodes = _doc_cay_the(tree_data)
        except (TypeError, ValueError) as exc:
            return web.json_response({"error": f"Payload cây thẻ không hợp lệ: {exc}"}, status=400)
        kieu_luu = data.get("kieu_luu", "py")
        if kieu_luu not in ("py", "json"):
            return web.json_response({"error": "kieu_luu phải là py hoặc json"}, status=400)
        expected_suffix = ".json" if kieu_luu == "json" else ".py"
        if safe_path.suffix.lower() != expected_suffix:
            return web.json_response({
                "error": f"Kiểu lưu {kieu_luu} chỉ được ghi vào tệp {expected_suffix}"
            }, status=400)

        expected_sha = data.get("expected_sha256")
        raw_bytes_goc: Optional[bytes] = None
        if safe_path.is_file():
            if not isinstance(expected_sha, str) or len(expected_sha) != 64:
                return web.json_response({
                    "error": "428 Precondition Required: Phải mở tệp trước khi ghi đè để lấy SHA-256"
                }, status=428)
            try:
                bytes.fromhex(expected_sha)
            except ValueError:
                return web.json_response({"error": "expected_sha256 không hợp lệ"}, status=400)
            raw_bytes_goc = safe_path.read_bytes()
            current_sha = hashlib.sha256(raw_bytes_goc).hexdigest()
            if not hmac.compare_digest(current_sha, expected_sha.lower()):
                return web.json_response({
                    "error": "409 Conflict: Tệp trên đĩa đã bị thay đổi bên ngoài",
                    "status": 409,
                    "current_sha256": current_sha,
                    "expected_sha256": expected_sha,
                }, status=409)

        source_bytes = raw_bytes_goc
        source_path = safe_path if raw_bytes_goc is not None else None
        if kieu_luu == "py" and source_bytes is None and data.get("source_path"):
            candidate = kiem_tra_duong_dan_an_toan(str(data.get("source_path", "")), request)
            source_sha = data.get("source_sha256")
            if not candidate or not candidate.is_file() or candidate.suffix.lower() != ".py":
                return web.json_response({"error": "Tệp nguồn Save As không hợp lệ"}, status=400)
            if not isinstance(source_sha, str) or len(source_sha) != 64:
                return web.json_response({
                    "error": "428 Precondition Required: Save As cần SHA-256 của tệp nguồn đã mở"
                }, status=428)
            try:
                bytes.fromhex(source_sha)
            except ValueError:
                return web.json_response({"error": "source_sha256 không hợp lệ"}, status=400)
            candidate_bytes = candidate.read_bytes()
            candidate_current_sha = hashlib.sha256(candidate_bytes).hexdigest()
            if not hmac.compare_digest(candidate_current_sha, source_sha.lower()):
                return web.json_response({
                    "error": "409 Conflict: Tệp nguồn của Save As đã thay đổi bên ngoài",
                    "status": 409,
                    "current_sha256": candidate_current_sha,
                    "expected_sha256": source_sha,
                }, status=409)
            source_bytes = candidate_bytes
            source_path = candidate

        if kieu_luu == "json" or safe_path.suffix.lower() == ".json":
            _xoa_co_da_sua(nodes)
            json_text = json.dumps([n.to_dict() for n in nodes], ensure_ascii=False, indent=2)
            new_bytes = json_text.encode("utf-8")
            _ghi_nguyen_tu(safe_path, new_bytes)
            new_sha = hashlib.sha256(new_bytes).hexdigest()
        else:
            if source_bytes is not None:
                record = doc_chuoi_py_sang_cay_the(source_bytes, str(source_path))
                structural_problem = _rang_buoc_cau_truc_va_danh_dau(record.tree, nodes)
                if structural_problem:
                    return web.json_response({
                        "error": (
                            "422 Unprocessable Entity: Bản public v1 chỉ hỗ trợ sửa ô của thẻ đã có; "
                            f"thêm/xóa/đổi thứ tự/đổi loại chưa được phép ({structural_problem})"
                        )
                    }, status=422)
                record.tree = nodes
                record.has_modifications = _co_the_da_sua(nodes)
                out_bytes = luu_cay_the_ra_tep_py(record)
                reparsed = doc_chuoi_py_sang_cay_the(out_bytes, str(safe_path))
                apply_problem = _xac_nhan_o_da_duoc_ap_dung(nodes, reparsed.tree)
                if apply_problem:
                    return web.json_response({
                        "error": f"422 Unprocessable Entity: {apply_problem}"
                    }, status=422)
                _ghi_nguyen_tu(safe_path, out_bytes)
                new_sha = hashlib.sha256(out_bytes).hexdigest()
            else:
                code_text = sinh_ma_python(nodes)
                out_bytes = code_text.encode("utf-8")
                _ghi_nguyen_tu(safe_path, out_bytes)
                new_sha = hashlib.sha256(out_bytes).hexdigest()

        config = lay_config(request)
        runtime = lay_runtime(request)
        try:
            rel_path = str(safe_path.relative_to(config.project_root)).replace("\\", "/")
        except ValueError:
            rel_path = str(safe_path).replace("\\", "/")
        runtime.opened_files_whitelist.add(str(safe_path))
        runtime.opened_files_whitelist.add(rel_path)

        return web.json_response({
            "status": "PASS",
            "duong_dan": str(safe_path),
            "duong_dan_rel": rel_path,
            "thong_diep": "Lưu tệp thành công",
            "sha256": new_sha,
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi lưu tệp: {str(e)}"}, status=500)


async def api_mau_chuong_trinh(request: web.Request) -> web.Response:
    """GET /api/mau — Cung cấp danh sách các chương trình mẫu tích hợp sẵn."""
    mau_list = [
        {
            "id": "mau_cong_hai_so",
            "ten": "1. Hàm cộng hai số",
            "mo_ta": "Mẫu nhập môn: Định nghĩa hàm cộng 2 số và in kết quả ra màn hình",
            "tree": [
                { "id": "m1_1", "ma": "ham", "o": { "ten_ham": "cong", "tham_so": "a, b" }, "than": [
                    { "id": "m1_2", "ma": "tra_ve", "o": { "gia_tri": "a + b" }, "than": [] }
                ]},
                { "id": "m1_3", "ma": "in_ra", "o": { "noi_dung": "cong(5, 7)" }, "than": [] }
            ]
        },
        {
            "id": "mau_chan_le",
            "ten": "2. Kiểm tra số chẵn / lẻ",
            "mo_ta": "Cấu trúc điều khiển: Lệnh Nếu và Ngược lại phân loại số",
            "tree": [
                { "id": "m2_1", "ma": "gan", "o": { "ten_bien": "n", "gia_tri": "42" }, "than": [] },
                { "id": "m2_2", "ma": "neu", "o": { "dieu_kien": "n % 2 == 0" }, "than": [
                    { "id": "m2_3", "ma": "in_ra", "o": { "noi_dung": '"Số chẵn"' }, "than": [] }
                ]},
                { "id": "m2_4", "ma": "nguoc_lai", "o": {}, "than": [
                    { "id": "m2_5", "ma": "in_ra", "o": { "noi_dung": '"Số lẻ"' }, "than": [] }
                ]}
            ]
        },
        {
            "id": "mau_tinh_tong_day_so",
            "ten": "3. Tính tổng dãy số 1 đến N",
            "mo_ta": "Vòng lặp: Lặp mỗi phần tử và tính tổng tích luỹ",
            "tree": [
                { "id": "m3_1", "ma": "gan", "o": { "ten_bien": "tong", "gia_tri": "0" }, "than": [] },
                { "id": "m3_2", "ma": "lap_moi", "o": { "bien": "i", "day": "range(1, 11)" }, "than": [
                    { "id": "m3_3", "ma": "gan", "o": { "ten_bien": "tong", "gia_tri": "tong + i" }, "than": [] }
                ]},
                { "id": "m3_4", "ma": "in_ra", "o": { "noi_dung": '"Tổng từ 1 đến 10 là: " + str(tong)' }, "than": [] }
            ]
        },
        {
            "id": "mau_phong_thi_nghiem_loi",
            "ten": "4. Phòng thử nghiệm Lỗi Đỏ & Cảnh báo Vàng",
            "mo_ta": "Mẫu vi phạm để quan sát phản hồi trực quan Đỏ/Vàng tức thì",
            "tree": [
                { "id": "m4_1", "ma": "gan", "o": { "ten_bien": "", "gia_tri": "100" }, "than": [] },
                { "id": "m4_2", "ma": "nguoc_lai", "o": {}, "than": [] },
                { "id": "m4_3", "ma": "in_ra", "o": { "noi_dung": "chua_tung_gan" }, "than": [] },
                { "id": "m4_4", "ma": "tra_ve", "o": { "gia_tri": "99" }, "than": [] },
                { "id": "m4_5", "ma": "gan", "o": { "ten_bien": "bien_khong_dung", "gia_tri": "1" }, "than": [] }
            ]
        }
    ]
    return web.json_response({"mau": mau_list})


async def api_trace(request: web.Request) -> web.Response:
    """POST /api/trace — Thu thập vết dòng chảy dữ liệu thực thi (Mạch Nước Ngầm Biến Số)."""
    # 1. Hàng rào xác thực & Origin
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    # 2. Hàng rào thực thi (trước khi parse JSON)
    if not lay_allow_code_execution(request):
        return web.json_response({
            "trang_thai": "bi_khoa",
            "error": "Chạy mã/test đang tắt mặc định"
        }, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "400 Bad Request: JSON không hợp lệ"}, status=400)

    if not isinstance(data, dict):
        return web.json_response({"error": "400 Bad Request: Body phải là object JSON"}, status=400)

    # Từ chối client đưa node_id_test trực tiếp (khóa injection)
    if "node_id_test" in data:
        return web.json_response({"error": "400 Bad Request: Không nhận node_id_test từ client; chỉ dùng tep_test"}, status=400)

    # Kiểm tra dong_kiem_tra
    dong_kiem_tra = data.get("dong_kiem_tra")
    if dong_kiem_tra is not None:
        if isinstance(dong_kiem_tra, bool) or not isinstance(dong_kiem_tra, int) or dong_kiem_tra <= 0:
            return web.json_response({"error": "400 Bad Request: dong_kiem_tra phải là số nguyên dương hoặc null"}, status=400)

    # Kiểm tra max_steps
    max_steps_raw = data.get("max_steps", 5000)
    if isinstance(max_steps_raw, bool) or not isinstance(max_steps_raw, int) or not (1 <= max_steps_raw <= 5000):
        return web.json_response({"error": "400 Bad Request: max_steps phải là số nguyên từ 1 đến 5000"}, status=400)
    max_steps = int(max_steps_raw)

    tep_nguon_str = data.get("tep_nguon") or data.get("duong_dan", "")
    if not isinstance(tep_nguon_str, str) or not tep_nguon_str.strip():
        return web.json_response({"error": "400 Bad Request: Thiếu tệp nguồn"}, status=400)

    safe_nguon = kiem_tra_duong_dan_an_toan(tep_nguon_str, request)
    if not safe_nguon or not safe_nguon.is_file():
        return web.json_response({"error": f"Tệp nguồn không hợp lệ hoặc không tồn tại: {tep_nguon_str}"}, status=400)

    config = lay_config(request)
    runtime = lay_runtime(request)
    project_root = config.project_root

    # Whitelist phiên per-app (tệp đã mở)
    str_source_resolved = str(safe_nguon).lower()
    rel_source_str = str(safe_nguon.relative_to(project_root)).replace("\\", "/").lower()
    if not any(str_source_resolved == w.lower() or rel_source_str == w.lower() for w in runtime.opened_files_whitelist):
        return web.json_response({"error": "403 Forbidden: Tệp nguồn chưa được mở trong phiên làm việc"}, status=403)

    tep_test_str = data.get("tep_test")
    safe_test = None
    tests_dir = (project_root / "tests").resolve(strict=False)

    # Tự suy tệp test theo quy ước: core/x.py -> tests/test_x.py
    tep_test_suy_ra = (project_root / "tests" / f"test_{safe_nguon.name}").resolve(strict=False)

    if tep_test_str and isinstance(tep_test_str, str) and tep_test_str.strip():
        safe_test = kiem_tra_duong_dan_an_toan(tep_test_str, request)
        if not safe_test or not safe_test.is_file() or not safe_test.is_relative_to(tests_dir):
            return web.json_response({"error": f"Tệp test không hợp lệ (phải nằm dưới tests/): {tep_test_str}"}, status=400)
        # Nếu tệp test khác với tệp tự suy hoặc tệp tự suy không tồn tại, kiểm tra whitelist phiên
        if not (tep_test_suy_ra.is_file() and safe_test.samefile(tep_test_suy_ra)):
            str_test_resolved = str(safe_test).lower()
            rel_test_str = str(safe_test.relative_to(project_root)).replace("\\", "/").lower()
            if not any(str_test_resolved == w.lower() or rel_test_str == w.lower() for w in runtime.opened_files_whitelist):
                return web.json_response({"error": "403 Forbidden: Tệp test chưa được mở trong phiên làm việc"}, status=403)
    else:
        if tep_test_suy_ra.is_file():
            safe_test = tep_test_suy_ra
        else:
            return web.json_response({"error": "400 Bad Request: Không thể tự suy tệp test, cần chỉ định tep_test đã mở trong phiên"}, status=400)

    try:
        ten_chot, so_khac, danh_sach = await asyncio.to_thread(
            chot_test_can_trace,
            tep_nguon=str(safe_nguon),
            tep_test=str(safe_test),
            dong_kiem_tra=dong_kiem_tra,
            max_steps=max_steps,
            cwd=project_root,
        )
        if not ten_chot or not danh_sach:
            return web.json_response({
                "trang_thai": "khong_chay",
                "thong_diep": "Không có test nào bị đỏ trong tệp test này",
                "tong_buoc": 0,
                "ten_test": "",
                "so_test_do_khac": 0,
                "cac_su_kien": [],
                "tep_nguon": str(safe_nguon),
                "thoi_gian_giay": 0.0,
            })
        res_chot = danh_sach[0]
        return web.json_response(res_chot.to_dict())
    except Exception as e:
        return web.json_response({"error": f"Lỗi truy vết thực thi: {str(e)}"}, status=500)


async def api_nhip(request: web.Request) -> web.Response:
    """POST /api/nhip — Phân tích Dải Nhịp Thực Thi từ cây thẻ hoặc từ hàm trên đĩa."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        if "tree" in data:
            nodes = [TheNode.from_dict(item) for item in data["tree"]]
            nhip_list = chia_nhip_thuc_thi(nodes)
            return web.json_response({
                "status": "PASS",
                "so_nhip": len(nhip_list),
                "nhip": [n.to_dict() for n in nhip_list],
            })
        elif "duong_dan" in data and "ten_ham" in data:
            safe_path = kiem_tra_duong_dan_an_toan(data["duong_dan"], request)
            if not safe_path or not safe_path.is_file():
                return web.json_response({"error": "Tệp không tồn tại hoặc ngoài vùng an toàn"}, status=400)
            nhip_list = phan_tich_nhip_cho_ham(safe_path, data["ten_ham"])
            return web.json_response({
                "status": "PASS",
                "ten_ham": data["ten_ham"],
                "so_nhip": len(nhip_list),
                "nhip": [n.to_dict() for n in nhip_list],
            })
        else:
            return web.json_response({"error": "Cần cung cấp 'tree' hoặc 'duong_dan' + 'ten_ham'"}, status=400)
    except Exception as e:
        return web.json_response({"error": f"Lỗi phân tích dải nhịp: {str(e)}"}, status=500)


async def api_dinh_vi_loi(request: web.Request) -> web.Response:
    """POST /api/dinh_vi_loi — Định vị lỗi E1 trên bản sao tạm (phân tích chỉ-đọc)."""
    # 1. Hàng rào xác thực & Origin
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ hoặc bị thiếu"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    # 2. Hàng rào thực thi (trước khi parse JSON)
    if not lay_allow_code_execution(request):
        return web.json_response({
            "trang_thai": "bi_khoa",
            "error": "Chạy mã/test đang tắt mặc định"
        }, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "400 Bad Request: JSON không hợp lệ"}, status=400)

    if not isinstance(data, dict):
        return web.json_response({"error": "400 Bad Request: Body phải là object JSON"}, status=400)

    REQUIRED_KEYS = {"tep_nguon", "tep_test", "source_sha256", "test_sha256"}
    if set(data.keys()) != REQUIRED_KEYS:
        return web.json_response({
            "error": "400 Bad Request: Schema yêu cầu đúng 4 trường (tep_nguon, tep_test, source_sha256, test_sha256)"
        }, status=400)

    for k in REQUIRED_KEYS:
        if not isinstance(data[k], str) or not data[k].strip():
            return web.json_response({"error": f"400 Bad Request: Trường {k} phải là chuỗi không rỗng"}, status=400)

    source_sha = data["source_sha256"].strip().lower()
    test_sha = data["test_sha256"].strip().lower()
    if len(source_sha) != 64 or len(test_sha) != 64:
        return web.json_response({"error": "400 Bad Request: SHA-256 phải là chuỗi hex 64 ký tự"}, status=400)
    try:
        bytes.fromhex(source_sha)
        bytes.fromhex(test_sha)
    except ValueError:
        return web.json_response({"error": "400 Bad Request: SHA-256 không hợp lệ"}, status=400)

    config = lay_config(request)
    runtime = lay_runtime(request)
    project_root = config.project_root

    # Confinement tep_nguon
    tep_nguon_str = data["tep_nguon"].strip()
    if ".." in tep_nguon_str or not tep_nguon_str.endswith(".py"):
        return web.json_response({"error": "400 Bad Request: Đường dẫn nguồn không hợp lệ"}, status=400)
    safe_source = (project_root / tep_nguon_str).resolve(strict=False)
    if not safe_source.is_file() or not safe_source.is_relative_to(project_root):
        return web.json_response({"error": "400 Bad Request: Tệp nguồn ngoài vùng root hoặc không tồn tại"}, status=400)

    # Confinement tep_test
    tep_test_str = data["tep_test"].strip()
    if ".." in tep_test_str or not tep_test_str.endswith(".py"):
        return web.json_response({"error": "400 Bad Request: Đường dẫn test không hợp lệ"}, status=400)
    safe_test = (project_root / tep_test_str).resolve(strict=False)
    tests_dir = (project_root / "tests").resolve(strict=False)
    if not safe_test.is_file() or not safe_test.is_relative_to(tests_dir):
        return web.json_response({"error": "400 Bad Request: Tệp test phải nằm dưới tests/"}, status=400)

    # Whitelist phiên per-app (tệp đã mở)
    str_source_resolved = str(safe_source).lower()
    rel_source_str = str(safe_source.relative_to(project_root)).replace("\\", "/").lower()
    if not any(str_source_resolved == w.lower() or rel_source_str == w.lower() for w in runtime.opened_files_whitelist):
        return web.json_response({"error": "403 Forbidden: Tệp nguồn chưa được mở trong phiên làm việc"}, status=403)

    # Whitelist phiên per-app (tệp test):
    # Nếu khớp quy ước tests/test_<nguon>.py thì tự suy từ tệp nguồn đã mở hợp lệ (không cần mở riêng)
    # Nếu khác quy ước (hoặc quy ước không có), tệp test bắt buộc phải nằm trong opened_files_whitelist
    tep_test_suy_ra = (project_root / "tests" / f"test_{safe_source.name}").resolve(strict=False)
    if not (tep_test_suy_ra.is_file() and safe_test.samefile(tep_test_suy_ra)):
        str_test_resolved = str(safe_test).lower()
        rel_test_str = str(safe_test.relative_to(project_root)).replace("\\", "/").lower()
        if not any(str_test_resolved == w.lower() or rel_test_str == w.lower() for w in runtime.opened_files_whitelist):
            return web.json_response({"error": "403 Forbidden: Tệp test chưa được mở trong phiên làm việc"}, status=403)

    # Kiểm tra SHA đĩa thật (Barrier 1)
    source_bytes = safe_source.read_bytes()
    actual_source_sha = hashlib.sha256(source_bytes).hexdigest()
    if not hmac.compare_digest(actual_source_sha, source_sha):
        return web.json_response({
            "error": "409 Conflict: SHA-256 tệp nguồn trên đĩa đã bị trôi",
            "status": 409,
            "current_sha256": actual_source_sha,
            "expected_sha256": source_sha,
        }, status=409)

    test_bytes = safe_test.read_bytes()
    actual_test_sha = hashlib.sha256(test_bytes).hexdigest()
    if not hmac.compare_digest(actual_test_sha, test_sha):
        return web.json_response({
            "error": "409 Conflict: SHA-256 tệp test trên đĩa đã bị trôi",
            "status": 409,
            "current_sha256": actual_test_sha,
            "expected_sha256": test_sha,
        }, status=409)

    # Atomic Check+Set Busy slot (không yield/await ở giữa)
    if runtime.busy_info["is_busy"]:
        return web.json_response({
            "error": "BUSY: Đang có tiến trình E1 khác đang phân tích",
            "trang_thai": "busy",
        }, status=409)

    job_id = secrets.token_hex(8)
    runtime.busy_info["is_busy"] = True
    runtime.busy_info["job_id"] = job_id
    runtime.busy_info["start_time"] = asyncio.get_event_loop().time()

    temp_clone_dir = Path(tempfile.mkdtemp(prefix="aura_e1_snap_"))
    supervisor_script = (Path(__file__).resolve().parent.parent / "tools" / "e1_supervisor_bootstrap.py").resolve(strict=False)

    cfg_payload = {
        "project_root": str(project_root),
        "temp_clone_dir": str(temp_clone_dir),
        "tep_nguon_rel": str(safe_source.relative_to(project_root)).replace("\\", "/"),
        "tep_test_rel": str(safe_test.relative_to(project_root)).replace("\\", "/"),
        "source_sha": source_sha,
        "test_sha": test_sha,
        "deadline_s": 300.0,
    }

    supervisor_proc: Optional[asyncio.subprocess.Process] = None
    supervisor_pid: Optional[int] = None

    async def _cleanup_supervisor():
        nonlocal supervisor_proc, supervisor_pid
        if supervisor_pid is not None:
            if sys.platform == "win32":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(supervisor_pid)],
                        capture_output=True,
                        timeout=5.0,
                    )
                except Exception:
                    pass
            else:
                try:
                    os.killpg(os.getpgid(supervisor_pid), 9)
                except Exception:
                    pass
        if supervisor_proc is not None:
            try:
                if supervisor_proc.returncode is None:
                    supervisor_proc.kill()
                    await supervisor_proc.wait()
            except Exception:
                pass
        shutil.rmtree(temp_clone_dir, ignore_errors=True)
        runtime.active_job_process = None
        runtime.busy_info["is_busy"] = False
        runtime.busy_info["job_id"] = None
        runtime.busy_info["start_time"] = None

    try:
        # Re-check live SHA before spawning supervisor (Barrier 3)
        actual_live_src = hashlib.sha256(safe_source.read_bytes()).hexdigest()
        actual_live_test = hashlib.sha256(safe_test.read_bytes()).hexdigest()
        if not hmac.compare_digest(actual_live_src, source_sha) or not hmac.compare_digest(actual_live_test, test_sha):
            return web.json_response({
                "error": "409 Conflict: SHA-256 tệp nguồn hoặc test trên đĩa đã bị trôi trước khi chạy",
                "status": 409,
            }, status=409)

        # Spawn supervisor process
        supervisor_proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-B",
            "-X",
            "utf8",
            str(supervisor_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        runtime.active_job_process = supervisor_proc

        # Read READY frame with timeout 5.0s
        try:
            line1 = await asyncio.wait_for(supervisor_proc.stdout.readline(), timeout=5.0)
            if b"===E1_SUPERVISOR_READY===" not in line1:
                return web.json_response({
                    "trang_thai": "khong_do_duoc",
                    "reason": "Supervisor không phát frame READY hợp lệ",
                }, status=500)
            line2 = await asyncio.wait_for(supervisor_proc.stdout.readline(), timeout=5.0)
            ready_info = json.loads(line2.decode("utf-8"))
            if not ready_info.get("ready") or not ready_info.get("job_attached"):
                return web.json_response({
                    "trang_thai": "khong_do_duoc",
                    "reason": "Supervisor không đính kèm được Job Object an toàn (job_attached is false)",
                }, status=500)
            supervisor_pid = ready_info.get("supervisor_pid", supervisor_proc.pid)
        except Exception as exc:
            return web.json_response({
                "trang_thai": "khong_do_duoc",
                "reason": f"Handshake READY thất bại: {exc}",
            }, status=500)

        # Write config JSON to supervisor stdin and close stdin
        supervisor_proc.stdin.write(json.dumps(cfg_payload).encode("utf-8"))
        await supervisor_proc.stdin.drain()
        supervisor_proc.stdin.close()
        await supervisor_proc.stdin.wait_closed()

        # Wait for supervisor completion (deadline 300s)
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            supervisor_proc.communicate(),
            timeout=300.0,
        )

        # Re-check live SHA after job (Barrier 4)
        post_live_src = hashlib.sha256(safe_source.read_bytes()).hexdigest()
        post_live_test = hashlib.sha256(safe_test.read_bytes()).hexdigest()
        if not hmac.compare_digest(post_live_src, source_sha) or not hmac.compare_digest(post_live_test, test_sha):
            return web.json_response({
                "error": "409 Conflict: SHA-256 tệp nguồn hoặc test trên đĩa đã bị trôi trong quá trình chạy",
                "status": 409,
            }, status=409)

        out_text = stdout_bytes.decode("utf-8", errors="replace").strip()
        try:
            res_json = json.loads(out_text)
        except Exception:
            return web.json_response({
                "trang_thai": "khong_do_duoc",
                "reason": f"Supervisor trả về output không phải JSON: {out_text[-500:]}",
            }, status=500)

        if res_json.get("trang_thai") == "khong_do_duoc" and res_json.get("timeout_triggered"):
            return web.json_response(res_json, status=504)

        return web.json_response(res_json, status=200)

    except asyncio.TimeoutError:
        return web.json_response({
            "trang_thai": "khong_do_duoc",
            "reason": "Supervisor timeout vượt trần 180s",
            "timeout_triggered": True,
        }, status=504)
    except asyncio.CancelledError:
        raise
    finally:
        await asyncio.shield(_cleanup_supervisor())

