# -*- coding: utf-8 -*-
"""Thin HTTP front door for the independent, read-only AURA Chat v1.

The transport creates ``ChatRequest``, calls ``ChatService.reply`` exactly
once, and renders the resulting ``ChatResult``.  Model choice, prompts, web
policy, secret filtering, timeouts, and transcript writes do not live here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from aiohttp import web

from core.chat_contract import ChatRequest, ChatResult, ChatStatus
from interface.chat_adapters import ChatRuntime, build_chat_runtime


_WEB_DIR = Path(__file__).resolve().parent / "web"
_WEB_ACTOR_ID = "owner:web"
CHAT_RUNTIME_KEY = web.AppKey("aura.chat.runtime", ChatRuntime)

_runtime: ChatRuntime | None = None


async def _get_runtime(request: web.Request | None = None) -> ChatRuntime:
    global _runtime
    if request is not None and CHAT_RUNTIME_KEY in request.app:
        return request.app[CHAT_RUNTIME_KEY]
    if _runtime is None:
        # Construction is synchronous and does no I/O, so no coroutine can
        # interleave here; avoiding a loop-bound global lock also keeps app
        # restart/test-loop teardown predictable.
        _runtime = build_chat_runtime()
    return _runtime


async def _close_runtime(_app: web.Application) -> None:
    global _runtime
    current, _runtime = _runtime, None
    if current is not None:
        await current.aclose()


def _result_payload(result: ChatResult) -> dict[str, Any]:
    """Serialize exactly the public ``ChatResult`` fields, without aliases."""

    return {
        "request_id": result.request_id,
        "session_id": result.session_id,
        "status": str(getattr(result.status, "value", result.status)),
        "text": result.text,
        "used_web": result.used_web,
        "sources": [
            {
                "title": source.title,
                "url": source.url,
                "retrieved_at": source.retrieved_at,
                "supports": source.supports,
            }
            for source in result.sources
        ],
        "latency_ms": result.latency_ms,
    }


def _http_status(result: ChatResult) -> int:
    try:
        status = ChatStatus(result.status)
    except (TypeError, ValueError):
        return 500
    return {
        ChatStatus.REJECTED: 400,
        ChatStatus.BACKEND_ERROR: 503,
        ChatStatus.TIMEOUT: 504,
        ChatStatus.CANCELLED: 503,
    }.get(status, 200)


def _service_result_is_valid(request: ChatRequest, result: object) -> bool:
    """Reject a broken adapter result without reflecting any of its content."""

    if not isinstance(result, ChatResult):
        return False
    if (
        result.request_id != request.request_id
        or result.session_id != request.session_id
    ):
        return False
    errors = list(result.validation_errors())
    try:
        status = ChatStatus(result.status)
    except (TypeError, ValueError):
        return False
    # A structurally rejected request intentionally echoes its invalid session
    # identity, so ChatResult's standalone UUID check cannot be satisfied.  All
    # other result invariants still apply and identity must match the request.
    if status is ChatStatus.REJECTED:
        errors = [
            error for error in errors
            if error != "session_id must be a non-zero UUID"
        ]
    return not errors


def _invalid_service_result(request: ChatRequest) -> ChatResult:
    return ChatResult(
        request_id=request.request_id,
        session_id=request.session_id,
        status=ChatStatus.BACKEND_ERROR,
        text="AURA nhận được kết quả nội bộ không hợp lệ. Vui lòng thử lại sau.",
        used_web=False,
        sources=(),
        latency_ms=0,
    )


async def _body_of(request: web.Request) -> dict[str, object]:
    """Return an object body; malformed/non-object input becomes rejection data."""

    try:
        if request.content_type == "application/json":
            body = await request.json()
        else:
            body = dict(await request.post())
    except Exception:  # malformed client data is handled by ChatService validation
        return {}
    return body if isinstance(body, dict) else {}


async def chat_page(_request: web.Request) -> web.Response:
    return web.FileResponse(_WEB_DIR / "chat.html")


def _history_probe(session_id: str) -> ChatRequest:
    return ChatRequest(
        request_id=str(uuid4()),
        session_id=session_id,
        actor_id=_WEB_ACTOR_ID,
        channel="web",
        text="history",
    )


async def api_history(request: web.Request) -> web.Response:
    raw_session = request.query.get("session_id", "")
    session_id = raw_session if isinstance(raw_session, str) else ""
    probe = _history_probe(session_id)
    if any(error.startswith("session_id") for error in probe.validation_errors()):
        return web.json_response({"error": "session_id không hợp lệ."}, status=400)

    runtime = await _get_runtime(request)
    messages = await runtime.store.load(
        actor_id=_WEB_ACTOR_ID,
        session_id=session_id,
    )
    guard = getattr(runtime, "guard", None)
    scrub = getattr(guard, "scrub_output", None)
    if not callable(scrub):
        return web.json_response(
            {"error": "Không thể đọc lịch sử một cách an toàn."}, status=503
        )

    safe_messages: list[dict[str, str]] = []
    try:
        for message in messages:
            safe_content = scrub(message.content)
            if not isinstance(safe_content, str) or not safe_content.strip():
                raise ValueError("content guard returned invalid history text")
            role = "user" if message.role == "user" else "assistant"
            safe_messages.append({"role": role, "content": safe_content})
    except Exception:
        # Do not partially return a transcript when its safety boundary failed.
        return web.json_response(
            {"error": "Không thể đọc lịch sử một cách an toàn."}, status=503
        )
    return web.json_response(
        {"messages": safe_messages}
    )


async def api_chat(request: web.Request) -> web.Response:
    body = await _body_of(request)
    raw_session = body.get("session_id", "")
    raw_text = body.get("text", "")
    chat_request = ChatRequest(
        request_id=str(uuid4()),
        session_id=raw_session if isinstance(raw_session, str) else "",
        actor_id=_WEB_ACTOR_ID,
        channel="web",
        text=raw_text if isinstance(raw_text, str) else "",
    )

    runtime = await _get_runtime(request)
    result = await runtime.service.reply(chat_request)
    if not _service_result_is_valid(chat_request, result):
        result = _invalid_service_result(chat_request)
    return web.json_response(_result_payload(result), status=_http_status(result))


# --------------------------------------------------------------------------- #
# User-confirmed Markdown memory.  It remains separate from chat transcripts:
# a model response never becomes a fact merely because it appeared in chat.
# --------------------------------------------------------------------------- #
async def memory_page(_request: web.Request) -> web.Response:
    return web.FileResponse(_WEB_DIR / "memory.html")


async def api_memory(request: web.Request) -> web.Response:
    from core import user_memory

    if request.method == "GET":
        return web.json_response({"facts": user_memory.list_facts()})

    body = await _body_of(request)
    try:
        if request.method == "POST":
            user_memory.remember(
                str(body.get("text") or ""), confirmed_by_user=True
            )
            message = "AURA đã nhớ."
        elif request.method == "PUT":
            ok = user_memory.update(
                str(body.get("id") or ""), str(body.get("text") or "")
            )
            if not ok:
                return web.json_response(
                    {"error": "Không tìm thấy điều cần sửa."}, status=404
                )
            message = "Đã sửa."
        elif request.method == "DELETE":
            if not user_memory.forget(str(body.get("id") or "")):
                return web.json_response(
                    {"error": "Không tìm thấy điều cần quên."}, status=404
                )
            message = "AURA đã quên."
        else:
            return web.json_response({"error": "Cách gọi không hỗ trợ."}, status=405)
    except user_memory.MemoryRefused as exc:
        return web.json_response({"error": str(exc)}, status=400)

    return web.json_response(
        {"message": message, "facts": user_memory.list_facts()}
    )


def attach_chat_routes(app: web.Application) -> None:
    """Attach the local Chat v1 front door to an aiohttp application."""

    app.router.add_get("/chat", chat_page)
    app.router.add_get("/api/chat/history", api_history)
    app.router.add_post("/api/chat", api_chat)
    app.router.add_get("/memory", memory_page)
    for method in ("GET", "POST", "PUT", "DELETE"):
        app.router.add_route(method, "/api/memory", api_memory)
    app.on_cleanup.append(_close_runtime)
