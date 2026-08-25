# -*- coding: utf-8 -*-
"""the_app.py — Entrypoint máy chủ Web App Lập trình bằng THẺ v1.

Chạy máy chủ aiohttp trên loopback (127.0.0.1) và tự động mở giao diện trình duyệt.
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys
import webbrowser
from pathlib import Path
from typing import Optional

from aiohttp import web

from interface import the_api


# Thư mục cấp một mà hộp "Mở tệp" được phép liệt kê.
#
# ĐÂY LÀ HÀNG RÀO AN TOÀN THẬT, không phải tiện nghi. `tests/test_the_app.py`
# đóng đinh: `?thu_muc=data` phải trả 403. Nới bừa là mở rào mà không ai biết.
#
# 25/08, lúc đóng gói: bộ ba `("core","interface","tests")` đóng cứng theo bố
# cục CỦA KHO NÀY. Chạy thử trên một dự án khác thì chỉ `core` tồn tại — hai
# thư mục kia không có, và một dự án của người dùng thì chẳng có lý do gì phải
# đặt tên như vậy.
#
# Sửa: chạy trên chính kho này thì giữ NGUYÊN bộ ba cũ (test 403 không đổi);
# chạy với `--du-an` trỏ chỗ khác thì suy từ thư mục cấp một CÓ THẬT của dự
# án, loại thư mục ẩn và mấy thứ không ai muốn duyệt.
#
# Hàng rào thứ hai vẫn còn nguyên bên trong `api_danh_sach_tep`:
# `is_relative_to(project_root)`. Cái ở đây chỉ là hàng rào ngoài.
BO_QUA_KHI_QUET = {"venv", ".venv", "__pycache__", "node_modules", "site-packages"}


def thu_muc_duoc_quet(root: Path) -> tuple[str, ...]:
    """Danh mục thư mục cấp một cho phép liệt kê, suy từ `root`."""
    if root.resolve(strict=False) == the_api.DEFAULT_PROJECT_ROOT.resolve(strict=False):
        # Chạy ngay trên kho AURA — giữ đúng hàng rào cũ, kể cả việc CHẶN `data`.
        return the_api.ALLOWED_SCAN_DIRS
    try:
        ten = sorted(
            d.name for d in root.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name not in BO_QUA_KHI_QUET
        )
    except OSError:
        return ()
    return tuple(ten)


def tao_app(
    project_root: Optional[Path | str] = None,
    allow_code_execution: Optional[bool] = None,
    auth_token: Optional[str] = None,
) -> web.Application:
    """Khởi tạo aiohttp Application với các route API và static files per-app context."""
    app = web.Application(client_max_size=10 * 1024 * 1024)  # 10 MB

    root = Path(project_root).resolve(strict=False) if project_root is not None else the_api.DEFAULT_PROJECT_ROOT.resolve(strict=False)
    if allow_code_execution is None:
        allow_code_execution = os.environ.get("AURA_THE_ALLOW_CODE_EXECUTION", "").strip() == "1"
    token = str(auth_token) if auth_token is not None else secrets.token_hex(16)

    config = the_api.AppConfig(
        project_root=root,
        static_dir=the_api.STATIC_DIR_GOI.resolve(strict=False),
        allowed_scan_dirs=thu_muc_duoc_quet(root),
        auth_token=token,
        allow_code_execution=bool(allow_code_execution),
    )
    runtime = the_api.AppRuntimeState()

    app["aura_config"] = config
    app["aura_runtime"] = runtime

    # Backward compatibility
    app["project_root"] = config.project_root
    app["allow_code_execution"] = config.allow_code_execution
    app["auth_token"] = config.auth_token

    # Cleanup lifecycle hook
    async def _on_app_cleanup(app_instance: web.Application) -> None:
        runtime_state = app_instance.get("aura_runtime")
        if runtime_state and runtime_state.active_job_process is not None:
            proc = runtime_state.active_job_process
            try:
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
            except Exception:
                pass
            runtime_state.active_job_process = None
            runtime_state.busy_info["is_busy"] = False

    app.on_cleanup.append(_on_app_cleanup)

    # Routes
    app.router.add_get("/", the_api.trang_chu)
    app.router.add_get("/static/{filename:.*}", the_api.file_tinh)
    
    # API endpoints
    app.router.add_get("/api/status", the_api.api_status)
    app.router.add_get("/api/mau", the_api.api_mau_chuong_trinh)
    app.router.add_get("/api/tep_tin", the_api.api_danh_sach_tep)
    app.router.add_post("/api/kiem", the_api.api_kiem_tra)
    app.router.add_post("/api/chay", the_api.api_chay_ma)
    app.router.add_post("/api/trace", the_api.api_trace)
    app.router.add_post("/api/nhip", the_api.api_nhip)
    app.router.add_post("/api/mo_tep", the_api.api_mo_tep)
    app.router.add_post("/api/luu_tep", the_api.api_luu_tep)
    app.router.add_post("/api/dinh_vi_loi", the_api.api_dinh_vi_loi)

    return app


def main():
    # Chỉnh CẢ HAI: `stdout` và `stderr`.
    #
    # 25/08: bản đầu chỉ chỉnh `stdout`. Chạy bản đã cài thì `--help` ra đúng,
    # nhưng câu từ chối bind — thứ đi ra `stderr` — vẫn hỏng:
    #   "AURA Chat v1 chưa c? x?c thực n?n từ chối..."
    # Người dùng gặp lỗi chính là lúc cần đọc được câu tiếng Việt nhất.
    for _luong in (sys.stdout, sys.stderr):
        if hasattr(_luong, "reconfigure"):
            _luong.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="AURA App Lập trình bằng THẺ (v1)")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ bind (chỉ loopback)")
    parser.add_argument("--port", type=int, default=8088, help="Cổng chạy máy chủ")
    parser.add_argument("--no-browser", action="store_true", help="Không tự động mở trình duyệt")
    # 23/08: trước đây chỉ bật được bằng biến môi trường
    # AURA_THE_ALLOW_CODE_EXECUTION=1. Nên bấm start_the_app.bat thì app mở
    # được nhưng nút "TÌM LỖI" và "DÒ DÒNG DỮ LIỆU" đều khoá, và KHÔNG CÓ CÁCH
    # NÀO bật từ dòng lệnh — hai tính năng chính thành không dùng được.
    parser.add_argument(
        "--allow-exec", action="store_true",
        help="Bật chạy mã/test (/api/chay, /api/trace, /api/dinh_vi_loi). "
             "Tắt mặc định vì tiến trình chưa được cách ly khỏi tệp/mạng/RAM")
    parser.add_argument(
        "--du-an", default=None, metavar="ĐƯỜNG_DẪN",
        help="Thư mục dự án — nơi mở và lưu tệp .py. Mặc định: thư mục hiện "
             "tại, theo lối `git` hay `code .`")
    args = parser.parse_args()
    if args.allow_exec:
        os.environ["AURA_THE_ALLOW_CODE_EXECUTION"] = "1"

    # CỬA BẢO MẬT: Chỉ cho phép bind vào loopback / 127.0.0.1
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"[BẢO MẬT]: Từ chối bind vào địa chỉ ngoài loopback: {args.host}", flush=True)
        sys.exit(1)

    # 25/08: mặc định là THƯ MỤC HIỆN TẠI, không phải thư mục chứa mã app.
    #
    # Cài bằng `pip` thì mã app nằm ở `site-packages` — không ai muốn mở/lưu
    # tệp .py của mình ở đó. Chạy `aura-the` ngay trong thư mục dự án là lối
    # quen thuộc của `git`, `code .`, `jupyter notebook`.
    #
    # Chạy từ trong kho AURA thì thư mục hiện tại CHÍNH LÀ gốc kho, nên hành
    # vi cũ không đổi.
    du_an = Path(args.du_an).resolve(strict=False) if args.du_an else Path.cwd()
    if not du_an.is_dir():
        print("[LỖI]: Thư mục dự án không tồn tại: %s" % du_an, flush=True)
        sys.exit(1)

    app = tao_app(project_root=du_an)
    token = app["aura_config"].auth_token
    app_url = f"http://{args.host}:{args.port}/?token={token}"

    print("=" * 70, flush=True)
    print("  [*] AURA -- APP LAP TRINH BANG THE (BAN v1)", flush=True)
    print("=" * 70, flush=True)
    print(f"  * Dia chi web  : {app_url}", flush=True)
    print(f"  * Ma thong hanh: {token}", flush=True)
    print("  * Bao mat      : 4 lop (Loopback + Auth Token + Origin + Whitelist)", flush=True)
    print(
        "  * Chay ma/Trace/E1: "
        + ("DA BAT CO CHU DICH (/api/chay, /api/trace, /api/dinh_vi_loi)" if app["aura_config"].allow_code_execution
           else "TAT MAC DINH (/api/chay, /api/trace, /api/dinh_vi_loi khoa; mo/sua/kiem tra/luu van hoat dong)"),
        flush=True,
    )
    print("=" * 70, flush=True)
    print("  Bam Ctrl+C de dung may chu.\n", flush=True)

    if not args.no_browser:
        webbrowser.open(app_url)

    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
