"""Focused HTTP handler tests for the thin AURA Chat v1 transport.

These tests call aiohttp handlers directly.  They are handler tests, not
browser/E2E evidence; the browser-facing source contract lives separately in
``test_chat_ui_static.py``.
"""
from __future__ import annotations

import asyncio
import inspect
import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from core.chat_contract import ChatResult, ChatStatus, SourceCitation
from core.chat_service import ChatMessage
from interface import chat_api


SID = str(uuid4())
RESULT_FIELDS = {
    "request_id",
    "session_id",
    "status",
    "text",
    "used_web",
    "sources",
    "latency_ms",
}


class _Request:
    def __init__(
        self,
        payload: object = None,
        *,
        query: dict[str, str] | None = None,
        method: str = "POST",
        content_type: str = "application/json",
        json_error: Exception | None = None,
    ) -> None:
        self.payload = {} if payload is None else payload
        self.query = query or {}
        self.method = method
        self.content_type = content_type
        self.json_error = json_error

    async def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload

    async def post(self):
        return self.payload if isinstance(self.payload, dict) else {}


def _run(handler, request: _Request):
    response = asyncio.run(handler(request))
    return response.status, json.loads(response.text)


def _result(request, *, status=ChatStatus.OK, text="Chào Sếp.", sources=()):
    return ChatResult(
        request_id=request.request_id,
        session_id=request.session_id,
        status=status,
        text=text,
        used_web=bool(sources),
        sources=tuple(sources),
        latency_ms=7,
    )


class _Service:
    def __init__(self, *, status=ChatStatus.OK, text="Chào Sếp.", sources=()):
        self.status = status
        self.text = text
        self.sources = tuple(sources)
        self.requests = []

    async def reply(self, request):
        self.requests.append(request)
        if request.validation_errors():
            return _result(
                request,
                status=ChatStatus.REJECTED,
                text="Yêu cầu không hợp lệ nên AURA chưa xử lý.",
            )
        return _result(
            request,
            status=self.status,
            text=self.text,
            sources=self.sources,
        )


class _Store:
    def __init__(self):
        self.by_identity = {}
        self.loads = []

    async def load(self, *, actor_id, session_id):
        self.loads.append((actor_id, session_id))
        return self.by_identity.get((actor_id, session_id), ())


class _Guard:
    def scrub_output(self, text):
        return text


@pytest.fixture
def runtime(monkeypatch):
    def install(*, service=None, store=None, guard=None):
        value = SimpleNamespace(
            service=service or _Service(),
            store=store or _Store(),
            guard=guard or _Guard(),
        )

        async def get_runtime(_request=None):
            return value

        monkeypatch.setattr(chat_api, "_get_runtime", get_runtime)
        return value

    return install


def test_transport_calls_one_service_and_returns_exact_chatresult(runtime):
    installed = runtime(service=_Service())
    status, body = _run(
        chat_api.api_chat,
        _Request({"text": "chào", "session_id": SID}),
    )

    assert status == 200
    assert set(body) == RESULT_FIELDS
    assert body["text"] == "Chào Sếp."
    assert body["status"] == "ok"
    assert body["session_id"] == SID
    assert len(installed.service.requests) == 1
    request = installed.service.requests[0]
    assert UUID(request.request_id).int != 0
    assert request.actor_id == "owner:web"
    assert request.channel_value.value == "web"


def test_source_schema_is_not_shrunk_or_aliased(runtime):
    citation = SourceCitation(
        title="Nguồn",
        url="https://example.com/article",
        retrieved_at="2026-08-09T10:00:00+07:00",
        supports="Dữ kiện đang trả lời.",
    )
    runtime(service=_Service(sources=(citation, citation)))
    _, body = _run(
        chat_api.api_chat,
        _Request({"text": "chào", "session_id": SID}),
    )
    assert set(body["sources"][0]) == {
        "title", "url", "retrieved_at", "supports"
    }
    assert "reply" not in body and "elapsed_s" not in body


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"text": "", "session_id": SID}, 400),
        ({"text": "x" * 12_001, "session_id": SID}, 400),
        ({"text": "chào", "session_id": "not-a-uuid"}, 400),
        ({"message": "schema cũ", "session_id": SID}, 400),
        (["not", "an", "object"], 400),
    ],
)
def test_invalid_or_old_payload_is_rejected_by_same_service(
    runtime, payload, expected_status
):
    installed = runtime(service=_Service())
    status, body = _run(chat_api.api_chat, _Request(payload))
    assert status == expected_status
    assert body["status"] == "rejected"
    assert set(body) == RESULT_FIELDS
    assert len(installed.service.requests) == 1


def test_malformed_json_becomes_visible_structured_rejection(runtime):
    runtime(service=_Service())
    status, body = _run(
        chat_api.api_chat,
        _Request(json_error=ValueError("bad json")),
    )
    assert status == 400
    assert body["status"] == "rejected"
    assert body["text"].strip()


@pytest.mark.parametrize(
    ("chat_status", "http_status"),
    [
        (ChatStatus.BACKEND_ERROR, 503),
        (ChatStatus.TIMEOUT, 504),
        (ChatStatus.CANCELLED, 503),
        (ChatStatus.WEB_UNAVAILABLE, 200),
        (ChatStatus.CANNOT_ANSWER, 200),
    ],
)
def test_http_status_preserves_visible_chatresult(runtime, chat_status, http_status):
    runtime(service=_Service(status=chat_status, text="Thông báo nhìn thấy được."))
    status, body = _run(
        chat_api.api_chat,
        _Request({"text": "hỏi", "session_id": SID}),
    )
    assert status == http_status
    assert body["status"] == chat_status.value
    assert body["text"] == "Thông báo nhìn thấy được."


def test_malformed_service_result_is_rejected_without_reflection(runtime):
    class MalformedService:
        async def reply(self, request):
            return {"text": "RAW_SECRET from broken adapter"}

    runtime(service=MalformedService())
    status, body = _run(
        chat_api.api_chat,
        _Request({"text": "hỏi", "session_id": SID}),
    )
    assert status == 503
    assert set(body) == RESULT_FIELDS
    assert body["status"] == "backend_error"
    assert "RAW_SECRET" not in body["text"]


def test_api_source_has_no_second_brain_or_timeout_bridge():
    source = inspect.getsource(chat_api)
    forbidden = (
        "orchestrator",
        "web_search",
        "OpenAICompatible",
        "secret_guard",
        "threading",
        "_within",
        "_run_sync",
    )
    for token in forbidden:
        assert token not in source
    assert source.count("runtime.service.reply(chat_request)") == 1


def test_history_loads_only_fixed_actor_and_requested_session(runtime):
    store = _Store()
    store.by_identity[("owner:web", SID)] = (
        ChatMessage("user", "marker-owner-this-tab"),
        ChatMessage("assistant", "answer-this-tab"),
    )
    runtime(store=store)
    status, body = _run(
        chat_api.api_history,
        _Request(query={"session_id": SID}, method="GET"),
    )
    assert status == 200
    assert store.loads == [("owner:web", SID)]
    assert body == {
        "messages": [
            {"role": "user", "content": "marker-owner-this-tab"},
            {"role": "assistant", "content": "answer-this-tab"},
        ]
    }


def test_history_rejects_bad_session_before_store(runtime):
    installed = runtime(store=_Store())
    status, _body = _run(
        chat_api.api_history,
        _Request(query={"session_id": "bad"}, method="GET"),
    )
    assert status == 400
    assert installed.store.loads == []


def test_history_scrubs_legacy_raw_secret_before_response(runtime):
    from core.secret_guard import SecretContentGuard

    store = _Store()
    raw = "password: legacy-secret-value"
    store.by_identity[("owner:web", SID)] = (
        ChatMessage("assistant", raw),
    )
    runtime(store=store, guard=SecretContentGuard())
    status, body = _run(
        chat_api.api_history,
        _Request(query={"session_id": SID}, method="GET"),
    )
    assert status == 200
    serialized = json.dumps(body, ensure_ascii=False)
    assert "legacy-secret-value" not in serialized
    assert "REDACTED" in serialized


def test_history_fails_closed_without_runtime_guard(runtime):
    installed = runtime(store=_Store())
    del installed.guard
    status, body = _run(
        chat_api.api_history,
        _Request(query={"session_id": SID}, method="GET"),
    )
    assert status == 503
    assert body == {"error": "Không thể đọc lịch sử một cách an toàn."}


# ---------------------------------------------------------------- memory UI
@pytest.fixture
def memory(tmp_path, monkeypatch):
    from core import user_memory

    monkeypatch.setattr(user_memory, "MEMORY_FILE", tmp_path / "nho.md")
    return user_memory


def _memory(method, payload=None):
    return _run(
        chat_api.api_memory,
        _Request(payload, method=method),
    )


def test_user_confirmed_memory_add_edit_delete(memory):
    status, body = _memory(
        "POST", {"text": "Sếp tốt nghiệp Đại học Bách khoa"}
    )
    assert status == 200
    fact_id = body["facts"][0]["id"]

    status, body = _memory(
        "PUT", {"id": fact_id, "text": "Sếp tốt nghiệp ĐH Bách khoa 2026"}
    )
    assert status == 200 and "2026" in body["facts"][0]["text"]

    status, body = _memory("DELETE", {"id": fact_id})
    assert status == 200 and body["facts"] == []


def test_secret_never_enters_user_memory(memory):
    _memory("POST", {"text": "khoá của tôi là sk-abc123def456ghi789jkl"})
    raw = memory.MEMORY_FILE.read_text(encoding="utf-8")
    assert "sk-abc123def456ghi789jkl" not in raw
