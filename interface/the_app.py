# -*- coding: utf-8 -*-
"""the_app.py — Entrypoint máy chủ Web App Lập trình bằng THẺ v1.

Chạy máy chủ aiohttp trên loopback (127.0.0.1) và tự động mở giao diện trình duyệt.
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from aiohttp import web

from interface import the_api


def tao_app() -> web.Application:
    """Khởi tạo aiohttp Application với các route API và static files."""
    app = web.Application(client_max_size=10 * 1024 * 1024)  # 10 MB

    # Routes
    app.router.add_get("/", the_api.trang_chu)
    app.router.add_get("/static/{filename:.*}", the_api.file_tinh)
    
    # API endpoints
    app.router.add_get("/api/status", the_api.api_status)
    app.router.add_get("/api/mau", the_api.api_mau_chuong_trinh)
    app.router.add_post("/api/kiem", the_api.api_kiem_tra)
    app.router.add_post("/api/chay", the_api.api_chay_ma)
    app.router.add_post("/api/mo_tep", the_api.api_mo_tep)
    app.router.add_post("/api/luu_tep", the_api.api_luu_tep)

    return app


def main():
    parser = argparse.ArgumentParser(description="AURA App Lập trình bằng THẺ (v1)")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ bind (chỉ loopback)")
    parser.add_argument("--port", type=int, default=8088, help="Cổng chạy máy chủ")
    parser.add_argument("--no-browser", action="store_true", help="Không tự động mở trình duyệt")
    args = parser.parse_args()

    # CỬA BẢO MẬT: Chỉ cho phép bind vào loopback / 127.0.0.1
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"[BẢO MẬT]: Từ chối bind vào địa chỉ ngoài loopback: {args.host}")
        sys.exit(1)

    app = tao_app()
    token = the_api.AUTH_TOKEN
    app_url = f"http://{args.host}:{args.port}/?token={token}"

    print("=" * 70)
    print("  🚀 AURA — APP LẬP TRÌNH BẰNG THẺ (BẢN v1)")
    print("=" * 70)
    print(f"  * Địa chỉ web : {app_url}")
    print(f"  * Mã thông hành: {token}")
    print("  * Bảo mật     : 4 lớp (Loopback + Auth Token + Origin + Whitelist)")
    print("  * Thực thi    : Trần 5s | Tiến trình riêng | CHƯA chặn ghi tệp | Chưa có trần RAM")
    print("=" * 70)
    print("  Bấm Ctrl+C để dừng máy chủ.\n")

    if not args.no_browser:
        webbrowser.open(app_url)

    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
