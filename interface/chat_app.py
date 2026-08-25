# -*- coding: utf-8 -*-
"""Standalone loopback-only aiohttp application for AURA Chat v1.

This module deliberately does not import the legacy dashboard, orchestrator,
jobs, revenue operators, desktop control, or daemon.  Its route set is small
enough to enumerate in a release test.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from ipaddress import ip_address
import os
from pathlib import Path
import sys
from typing import Sequence

from aiohttp import web

from interface import chat_api
from interface.chat_adapters import (
    ChatRuntime,
    ChatRuntimeConfig,
    build_chat_runtime,
)


def require_loopback(host: str) -> str:
    """Accept localhost/loopback literals and reject every LAN/public bind."""

    candidate = (host or "").strip()
    if candidate.casefold() == "localhost":
        return "localhost"
    try:
        address = ip_address(candidate)
    except ValueError as error:
        raise ValueError(
            "AURA Chat v1 chỉ được bind vào localhost/địa chỉ loopback."
        ) from error
    if not address.is_loopback:
        raise ValueError(
            "AURA Chat v1 chưa có xác thực nên từ chối địa chỉ ngoài loopback."
        )
    return candidate


def _ma_chay_luc_nao() -> str:
    """Mã đang chạy được sửa lần cuối lúc nào — theo mtime của chính xương sống.

    Không hỏi git: git có thể không có lúc chạy, và câu hỏi thật của Sếp không
    phải "commit nào" mà là "cái cửa tôi đang gõ có mới không".
    """
    from core.paths import PROJECT_ROOT

    moi_nhat = 0.0
    for ten in ("core/chat_service.py", "core/local_first_gateway.py",
                "core/web_search.py", "core/dong_ho.py",
                "interface/chat_adapters.py", "interface/chat_app.py"):
        duong_dan = PROJECT_ROOT / ten
        if duong_dan.is_file():
            moi_nhat = max(moi_nhat, duong_dan.stat().st_mtime)
    if not moi_nhat:
        return "không rõ"
    return datetime.fromtimestamp(moi_nhat).strftime("%d/%m %H:%M")


async def api_status(request: web.Request) -> web.Response:
    """Khai máy chủ này là bản nào và đang chạy model gì.

    Có vì 10/08/2026 Sếp báo AURA trả sai ngày trong khi bản đã vá trả đúng
    3/3 — hoá ra Sếp đang gõ vào bảng điều khiển v2 cũ ở cổng khác, và không
    có cách nào nhìn ra điều đó.
    """
    runtime = request.app[chat_api.CHAT_RUNTIME_KEY]
    return web.json_response(
        {
            # "v3" là thứ màn hình dùng để tự khai mình là ai.  10/08/2026 Sếp
            # báo AURA trả sai ngày trong khi bản đã vá trả đúng 3/3 — hoá ra
            # Sếp đang gõ vào bảng điều khiển v2 cũ ở cổng khác, và không có
            # cách nào nhìn ra điều đó.
            "service": "aura-chat-v3",
            "status": "ready",
            "read_only": True,
            "model_configured": bool(
                getattr(runtime, "model_configured", False)
            ),
            "code_updated_at": _ma_chay_luc_nao(),
        }
    )


async def _close_runtime(app: web.Application) -> None:
    runtime = app[chat_api.CHAT_RUNTIME_KEY]
    await runtime.aclose()


def create_chat_app(
    *,
    runtime_config: ChatRuntimeConfig | None = None,
    runtime: ChatRuntime | None = None,
) -> web.Application:
    """Create the four-route Chat-only app without contacting any provider."""

    selected = runtime or build_chat_runtime(config=runtime_config)
    app = web.Application(client_max_size=64 * 1024)
    app[chat_api.CHAT_RUNTIME_KEY] = selected
    app.router.add_get("/", chat_api.chat_page)
    app.router.add_get("/api/status", api_status)
    app.router.add_post("/api/chat", chat_api.api_chat)
    app.router.add_get("/api/chat/history", chat_api.api_history)
    # Trang "AURA nhớ gì về tôi".  Đã xây từ 09/08 (memory.html + user_memory.py
    # + test riêng) nhưng CHƯA BAO GIỜ được nối vào cửa trước độc lập này —
    # `attach_chat_routes()` chỉ nối cho dashboard cũ, còn ở đây thì `/memory`
    # trả 404.  Mã sống, test xanh, sản phẩm chết: đúng bệnh của v2.
    app.router.add_get("/memory", chat_api.memory_page)
    for method in ("GET", "POST", "PUT", "DELETE"):
        app.router.add_route(method, "/api/memory", chat_api.api_memory)
    app.on_cleanup.append(_close_runtime)
    return app


def build_parser() -> argparse.ArgumentParser:
    """Dựng bộ đọc tham số dòng lệnh cho máy chủ chat (host, cổng, model)."""
    parser = argparse.ArgumentParser(
        description="Chạy AURA Chat v1 độc lập trên loopback."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("AURA_CHAT_HOST", "127.0.0.1"),
        help="Chỉ localhost/địa chỉ loopback; mặc định 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AURA_CHAT_PORT", "8799")),
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL; hoặc AURA_CHAT_BASE_URL.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Tên model; hoặc AURA_CHAT_MODEL.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Trần một lượt; hoặc AURA_CHAT_TIMEOUT_S.",
    )
    parser.add_argument(
        "--transcript-root",
        type=Path,
        default=None,
        help="Thư mục transcript; hoặc AURA_CHAT_TRANSCRIPT_ROOT.",
    )
    # Intentionally no --api-key: secrets belong only in AURA_CHAT_API_KEY.
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Khởi động máy chủ chat AURA trên loopback. Mã thoát 0 nếu dừng sạch."""
    # 25/08: THIẾU HAI DÒNG NÀY THÌ `aura-chat --help` GÃY NGAY.
    #
    # Bắt được lúc kiểm bản đã cài: chạy `aura-chat.exe --help` từ một venv
    # sạch thì nổ `UnicodeEncodeError: 'charmap' codec can't encode character
    # 'ạ'` — cp1252 không mã hoá nổi chữ "ạ" trong phần trợ giúp. Người
    # dùng gõ `--help` lần đầu là gặp traceback.
    #
    # Trong kho thì không thấy, vì ở đây luôn chạy qua `python -X utf8`. Chỉ
    # bản CÀI mới lộ ra — đó là lý do phải cài thật rồi chạy thật, chứ không
    # đọc mã mà tin.
    #
    # `interface/the_app.py:121` đã có đúng hai dòng này từ trước; chỗ ấy
    # thoát nạn còn chỗ này thì không.
    # Chỉnh CẢ HAI: `stdout` và `stderr`.
    #
    # 25/08: bản đầu chỉ chỉnh `stdout`. Chạy bản đã cài thì `--help` ra đúng,
    # nhưng câu từ chối bind — thứ đi ra `stderr` — vẫn hỏng:
    #   "AURA Chat v1 chưa c? x?c thực n?n từ chối..."
    # Người dùng gặp lỗi chính là lúc cần đọc được câu tiếng Việt nhất.
    for _luong in (sys.stdout, sys.stderr):
        if hasattr(_luong, "reconfigure"):
            _luong.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        host = require_loopback(args.host)
        config = ChatRuntimeConfig.from_environment(
            base_url=args.base_url,
            model=args.model,
            timeout_s=args.timeout,
            transcript_root=args.transcript_root,
        )
        app = create_chat_app(runtime_config=config)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    web.run_app(app, host=host, port=args.port, print=None)
    return 0


__all__ = [
    "api_status",
    "build_parser",
    "create_chat_app",
    "main",
    "require_loopback",
]

