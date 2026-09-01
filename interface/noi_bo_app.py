# -*- coding: utf-8 -*-
"""noi_bo_app.py — Máy chủ độc lập cho App Nội Bộ Điều Hành 7 Đặc Nhiệm (AURA v3).

Chạy trên Loopback (127.0.0.1) an toàn, kết nối trực tiếp với các phân hệ
AURA, Alpha, Beta, Delta, Gamma, Omega, Zeta.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from aiohttp import web

from interface import noi_bo_api
from core.paths import PROJECT_ROOT


def build_noi_bo_app() -> web.Application:
    """Tạo ứng dụng aiohttp cho App Nội Bộ AURA v3."""
    app = web.Application()

    # Trang chủ Dashboard
    app.router.add_get("/", noi_bo_api.trang_chu)
    app.router.add_get("/static/{filename:.*}", noi_bo_api.file_tinh)

    # API endpoints
    app.router.add_get("/api/status", noi_bo_api.api_status)
    app.router.add_get("/api/rooms", noi_bo_api.api_danh_sach_phong)
    app.router.add_post("/api/dispatch", noi_bo_api.api_dieu_phoi_phong)
    app.router.add_get("/api/pipeline/presets", noi_bo_api.api_danh_sach_the_quy_trinh)
    app.router.add_post("/api/pipeline/run", noi_bo_api.api_chay_pipeline)
    app.router.add_post("/api/pipeline/custom", noi_bo_api.api_pipeline_custom)
    app.router.add_get("/api/polyglot/languages", noi_bo_api.api_polyglot_languages)
    app.router.add_post("/api/polyglot/translate", noi_bo_api.api_polyglot_translate)
    app.router.add_post("/api/polyglot/validate", noi_bo_api.api_polyglot_validate)
    app.router.add_post("/api/polyglot/run", noi_bo_api.api_polyglot_run)
    app.router.add_get("/api/ledger", noi_bo_api.api_doc_so_cai)
    app.router.add_get("/api/evidence", noi_bo_api.api_doc_evidence_runs)

    return app


def build_parser() -> argparse.ArgumentParser:
    """Dựng bộ đọc tham số dòng lệnh."""
    parser = argparse.ArgumentParser(
        description="Khởi động App Nội Bộ Điều Hành 7 Đặc Nhiệm AURA v3."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("AURA_NOI_BO_HOST", "127.0.0.1"),
        help="Địa chỉ Loopback (mặc định 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AURA_NOI_BO_PORT", "8890")),
        help="Cổng phục vụ giao diện (mặc định 8890).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Khởi động máy chủ App Nội Bộ."""
    # Đảm bảo UTF-8 trên Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args(argv)

    print("=" * 60)
    print("  🏛️  AURA COMMAND CENTER — APP ĐIỀU HÀNH 7 ĐẶC NHIỆM v3")
    print(f"  ⚡ Máy chủ đang chạy tại: http://{args.host}:{args.port}/")
    print("  🛡️ 7 Phòng ban sẵn sàng: AURA, Alpha, Beta, Delta, Gamma, Omega, Zeta")
    print("=" * 60)

    app = build_noi_bo_app()
    try:
        web.run_app(app, host=args.host, port=args.port, print=None)
        return 0
    except OSError as err:
        print(f"Lỗi khởi động máy chủ: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
