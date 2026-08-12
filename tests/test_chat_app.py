"""Server/app-factory tests; these do not launch a browser or external network."""
from __future__ import annotations

import asyncio
import ast
import inspect
import json
from pathlib import Path
from time import monotonic

import pytest
from aiohttp.test_utils import make_mocked_request

from interface import chat_api, chat_app


class FakeRuntime:
    model_configured = True

    def __init__(self):
        self.closed = 0

    async def aclose(self):
        self.closed += 1


def test_chat_only_route_set_is_exact():
    """Bộ đường của cửa trước phải ĐẾM ĐƯỢC BẰNG TAY — luật Codex đặt ở lượt 003.

    10/08: mở khoá thêm `/memory` + `/api/memory`, CÓ CHỦ Ý.  Trang "AURA nhớ gì
    về tôi" đã xây xong từ 09/08 mà cửa trước không nối route nên trả 404; test
    này chính là thứ bắt tôi phải dừng lại và sửa danh sách thay vì lẳng lặng
    thêm đường.  Nó làm đúng việc của nó, nên tôi mở chứ không gỡ.
    """
    app = chat_app.create_chat_app(runtime=FakeRuntime())
    paths = {resource.canonical for resource in app.router.resources()}
    assert paths == {
        "/", "/api/status", "/api/chat", "/api/chat/history",
        "/memory", "/api/memory",
    }
    assert "/dashboard" not in paths, "cửa trước v3 không được mọc lại dashboard cũ"


def test_chat_app_imports_no_legacy_runtime():
    tree = ast.parse(inspect.getsource(chat_app))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "interface.dashboard",
        "core.orchestrator",
        "core.daemon",
        "factory",
    }
    assert imported.isdisjoint(forbidden)


@pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.2", "::1", "localhost"])
def test_loopback_bind_is_accepted(host):
    assert chat_app.require_loopback(host)


@pytest.mark.parametrize(
    "host", ["0.0.0.0", "::", "192.168.1.20", "8.8.8.8", "aura.local"]
)
def test_non_loopback_bind_is_refused(host):
    with pytest.raises(ValueError):
        chat_app.require_loopback(host)


def test_root_serves_chat_html_and_status_is_immediate():
    runtime = FakeRuntime()
    app = chat_app.create_chat_app(runtime=runtime)

    root_response = asyncio.run(chat_api.chat_page(None))
    html = Path(root_response._path).read_text(encoding="utf-8")
    assert "<title>AURA · Trò chuyện</title>" in html
    assert "Nhắn cho AURA" in html

    request = make_mocked_request("GET", "/api/status", app=app)
    started = monotonic()
    response = asyncio.run(chat_app.api_status(request))
    elapsed = monotonic() - started
    body = json.loads(response.text)
    assert response.status == 200
    assert body["service"] == "aura-chat-v3"
    assert body["status"] == "ready"
    assert body["read_only"] is True
    assert body["model_configured"] is True
    # Cửa phải TỰ KHAI mã của nó cũ hay mới.  10/08/2026 một tab mở từ trước
    # vẫn hiện lịch sử do bản chưa vá sinh ra, và cả Sếp lẫn tôi đều tưởng bản
    # vá không chạy — mất một vòng chẩn đoán sai chỉ vì thiếu dòng này.
    assert body["code_updated_at"] and body["code_updated_at"] != "không rõ"
    assert elapsed < 1.0


def test_moi_trang_da_xay_deu_co_route_that():
    """Mã sống + test xanh + sản phẩm 404 = đúng bệnh của v2.

    Trang "AURA nhớ gì về tôi" xây ngày 09/08, có `memory.html`, có
    `core/user_memory.py`, có test riêng — mà `/memory` trả 404 suốt vì cửa
    trước độc lập không nối route.  Test này đếm ĐƯỜNG THẬT trong app, không
    đếm hàm đã viết.
    """
    app = chat_app.create_chat_app(runtime=FakeRuntime())
    duong = {
        (route.method, route.resource.canonical)
        for route in app.router.routes()
    }
    for can_co in (
        ("GET", "/"),
        ("GET", "/api/status"),
        ("POST", "/api/chat"),
        ("GET", "/api/chat/history"),
        ("GET", "/memory"),
        ("GET", "/api/memory"),
        ("POST", "/api/memory"),
        ("PUT", "/api/memory"),
        ("DELETE", "/api/memory"),
    ):
        assert can_co in duong, f"thiếu route thật: {can_co[0]} {can_co[1]}"


def test_app_cleanup_closes_async_gateway_once():
    runtime = FakeRuntime()
    app = chat_app.create_chat_app(runtime=runtime)

    async def lifecycle():
        app.freeze()
        await app.startup()
        await app.cleanup()

    asyncio.run(lifecycle())
    assert runtime.closed == 1


def test_cli_has_no_raw_secret_flag():
    destinations = {action.dest for action in chat_app.build_parser()._actions}
    assert "api_key" not in destinations
    assert "key" not in destinations
    assert "secret" not in destinations

