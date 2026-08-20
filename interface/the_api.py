# -*- coding: utf-8 -*-
"""the_api.py — API Handlers cho App Lập trình bằng THẺ v1.

Triển khai 4 LỚP BẢO MẬT BẮT BUỘC theo Mục 13.2 & 14.2:
1. Chỉ nghe 127.0.0.1.
2. Mã thông hành ngẫu nhiên (Auth Token 32-hex) kiểm qua header X-Auth-Token (hoặc query param).
3. Kiểm tra Origin / Referer ngăn chặn CSRF từ website ngoài.
4. Path Confinement & Whitelist phiên: /api/luu_tep chỉ được ghi vào file đã mở hoặc trong workspace.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from aiohttp import web

from core.the_v1 import (
    BO_THE_V1,
    NHOM_THE,
    FileSourceRecord,
    TheNode,
    chay_ma_python_sandbox,
    doc_tep_py_sang_cay_the,
    kiem_tra_cay_the,
    luu_cay_the_ra_tep_py,
    sinh_ma_python,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "interface" / "web" / "the_v1"

# Session state: Sinh token 32 ký tự hex lúc khởi động máy chủ
AUTH_TOKEN = secrets.token_hex(16)

# Whitelist các tệp đã mở trong phiên làm việc hiện tại
OPENED_FILES_WHITELIST: Set[str] = set()

# Whitelist thư mục được phép thao tác (Workspace + Temp)
ALLOWED_ROOTS: List[Path] = [
    PROJECT_ROOT.resolve(),
]


# ==============================================================================
# BẢO MẬT: KIỂM TRA MÃ THÔNG HÀNH & NGUỒN GỐC REQUEST
# ==============================================================================

def xac_thuc_request(request: web.Request) -> bool:
    """Kiểm tra mã thông hành qua Header X-Auth-Token hoặc Query param ?token=."""
    token = request.headers.get("X-Auth-Token")
    if not token:
        token = request.query.get("token")
    if not token or token != AUTH_TOKEN:
        return False
    return True


def kiem_tra_origin_hop_le(request: web.Request) -> bool:
    """Kiểm tra Origin / Referer chỉ chấp nhận từ loopback."""
    origin = request.headers.get("Origin") or request.headers.get("Referer") or ""
    if not origin:
        # Request cùng nguồn (direct/same-origin)
        return True
    return "127.0.0.1" in origin or "localhost" in origin


def kiem_tra_duong_dan_an_toan(duong_dan_str: str) -> Optional[Path]:
    """Kiểm tra Path Confinement: Chặn .. và chỉ cho phép ghi vào vùng hợp lệ."""
    if not duong_dan_str or ".." in duong_dan_str:
        return None
    try:
        resolved = Path(duong_dan_str).resolve(strict=False)
    except Exception:
        return None

    # Phải nằm trong ALLOWED_ROOTS hoặc đã có trong OPENED_FILES_WHITELIST
    str_resolved = str(resolved).lower()
    in_whitelist = any(str_resolved == w.lower() for w in OPENED_FILES_WHITELIST)
    in_allowed_roots = any(resolved.is_relative_to(root) for root in ALLOWED_ROOTS)

    if in_whitelist or in_allowed_roots:
        return resolved
    return None


# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================

async def trang_chu(request: web.Request) -> web.Response:
    """Phục vụ trang chủ index.html."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.is_file():
        return web.Response(text="<h1>Không tìm thấy interface/web/the_v1/index.html</h1>", content_type="text/html", status=404)
    content = index_file.read_text(encoding="utf-8")
    return web.Response(text=content, content_type="text/html")


async def file_tinh(request: web.Request) -> web.Response:
    """Phục vụ các file tĩnh (CSS, JS, SVG, JSON)."""
    filename = request.match_info.get("filename", "")
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        return web.Response(text="403 Forbidden", status=403)
    target_path = (STATIC_DIR / filename).resolve()
    if not target_path.is_file() or not target_path.is_relative_to(STATIC_DIR.resolve()):
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
    return web.json_response({
        "app": "AURA_THE_v1",
        "status": "ready",
        "sandbox_info": "Sandbox: Trần 5s | Tiến trình riêng | CHƯA chặn được ghi tệp | Chưa có trần RAM",
        "security": {
            "loopback_only": True,
            "auth_token_required": True,
            "origin_check": True,
            "path_confinement": True
        }
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
    """POST /api/chay — Nhận mã Python hoặc cây thẻ, chạy qua sandbox."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        code = data.get("code")
        if code is None and "tree" in data:
            nodes = [TheNode.from_dict(item) for item in data["tree"]]
            code = sinh_ma_python(nodes)
        
        if not code:
            return web.json_response({"error": "Mã thực thi trống"}, status=400)

        # Chạy sandbox tiến trình riêng với trần 5s
        res = chay_ma_python_sandbox(code, timeout=5.0)
        return web.json_response({
            "status": res.status,
            "exit_code": res.exit_code,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "wall_time_ms": res.wall_time_ms,
            "timed_out": res.timed_out,
            "sandbox_notice": "Sandbox: Trần 5s | Tiến trình riêng | CHƯA chặn được ghi tệp | Chưa có trần RAM",
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi thực thi mã: {str(e)}"}, status=500)


async def api_mo_tep(request: web.Request) -> web.Response:
    """POST /api/mo_tep — Mở một tệp .py từ đĩa, chuyển thành cây thẻ."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        duong_dan_str = data.get("duong_dan", "")
        safe_path = kiem_tra_duong_dan_an_toan(duong_dan_str)
        if not safe_path or not safe_path.is_file():
            return web.json_response({"error": f"Đường dẫn tệp không hợp lệ hoặc không tồn tại: {duong_dan_str}"}, status=400)

        record = doc_tep_py_sang_cay_the(safe_path)
        # Thêm vào whitelist phiên
        OPENED_FILES_WHITELIST.add(str(safe_path))

        return web.json_response({
            "duong_dan": str(safe_path),
            "ten_tep": safe_path.name,
            "tree": [n.to_dict() for n in record.tree],
            "newline": "CRLF" if record.newline == "\r\n" else "LF",
            "so_dong": len(record.lines),
        })
    except Exception as e:
        return web.json_response({"error": f"Lỗi mở tệp .py: {str(e)}"}, status=500)


async def api_luu_tep(request: web.Request) -> web.Response:
    """POST /api/luu_tep — Lưu cây thẻ vào file .py (lossless) hoặc file .json."""
    if not xac_thuc_request(request):
        return web.json_response({"error": "403 Forbidden: Mã thông hành không hợp lệ"}, status=403)
    if not kiem_tra_origin_hop_le(request):
        return web.json_response({"error": "403 Forbidden: Origin không được phép"}, status=403)

    try:
        data = await request.json()
        duong_dan_str = data.get("duong_dan", "")
        safe_path = kiem_tra_duong_dan_an_toan(duong_dan_str)
        if not safe_path:
            return web.json_response({"error": "403 Forbidden: Đường dẫn không nằm trong danh sách được phép ghi"}, status=403)

        tree_data = data.get("tree", [])
        nodes = [TheNode.from_dict(item) for item in tree_data]
        kieu_luu = data.get("kieu_luu", "py")  # "py" hoặc "json"

        if kieu_luu == "json" or safe_path.suffix.lower() == ".json":
            json_text = json.dumps(tree_data, ensure_ascii=False, indent=2)
            safe_path.write_text(json_text, encoding="utf-8")
        else:
            # Lưu ngược vào file .py
            if safe_path.is_file():
                raw_bytes_goc = safe_path.read_bytes()
                record = doc_chuoi_py_sang_cay_the(raw_bytes_goc, str(safe_path))
                record.tree = nodes
                record.has_modifications = bool(data.get("has_modifications", True))
                out_bytes = luu_cay_the_ra_tep_py(record)
                safe_path.write_bytes(out_bytes)
            else:
                # Tạo file .py mới
                code_text = sinh_ma_python(nodes)
                safe_path.write_text(code_text, encoding="utf-8")

        OPENED_FILES_WHITELIST.add(str(safe_path))
        return web.json_response({"status": "PASS", "duong_dan": str(safe_path), "thong_diep": "Lưu tệp thành công"})
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
                { "id": "m4_1", "ma": "gan", "o": { "ten_bien": "", "gia_tri": "100" }, "than": [] },  # Đỏ: ô trống
                { "id": "m4_2", "ma": "nguoc_lai", "o": {}, "than": [] },  # Đỏ: mồ côi + thân rỗng
                { "id": "m4_3", "ma": "in_ra", "o": { "noi_dung": "chua_tung_gan" }, "than": [] },  # Đỏ: biến chưa gán
                { "id": "m4_4", "ma": "tra_ve", "o": { "gia_tri": "99" }, "than": [] },  # Đỏ: tra_ve ngoài hàm
                { "id": "m4_5", "ma": "gan", "o": { "ten_bien": "bien_khong_dung", "gia_tri": "1" }, "than": [] }  # Vàng: biến không dùng
            ]
        }
    ]
    return web.json_response({"mau": mau_list})
