from __future__ import annotations

import ast
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

import pytest

from core.chat_contract import ChatRequest, ChatResult, ChatStatus, SourceCitation
from core.chat_runtime import (
    JsonlSessionStore,
    JsonlSessionStoreConfig,
    ModelGatewayError,
    OpenAICompatibleConfig,
    OpenAICompatibleModelGateway,
)
from core.chat_service import ChatMessage


def _request(
    number: int = 0, *, actor_id: str = "owner", session_id: str | None = None
) -> ChatRequest:
    return ChatRequest(
        request_id=str(uuid4()),
        session_id=session_id or str(uuid4()),
        actor_id=actor_id,
        channel="test",
        text=f"cau hoi {number}",
    )


def _result(request: ChatRequest, number: int = 0) -> ChatResult:
    return ChatResult(
        request_id=request.request_id,
        session_id=request.session_id,
        status=ChatStatus.OK,
        text=f"tra loi {number}",
        used_web=False,
        sources=(),
        latency_ms=5,
    )


def _store(tmp_path: Path, *, maximum: int = 100) -> JsonlSessionStore:
    return JsonlSessionStore(
        JsonlSessionStoreConfig(
            root=tmp_path / "sessions", max_history_messages=maximum
        )
    )


def test_jsonl_store_isolates_actor_and_session_and_survives_restart(tmp_path):
    async def scenario():
        session_a, session_b = str(uuid4()), str(uuid4())
        original = _store(tmp_path)
        a = _request(1, actor_id="owner-a", session_id=session_a)
        b = _request(2, actor_id="owner-a", session_id=session_b)
        c = _request(3, actor_id="owner-b", session_id=session_a)
        await original.append_exchange(request=a, result=_result(a, 1))
        await original.append_exchange(request=b, result=_result(b, 2))
        await original.append_exchange(request=c, result=_result(c, 3))

        restarted = _store(tmp_path)
        return (
            await restarted.load(actor_id="owner-a", session_id=session_a),
            await restarted.load(actor_id="owner-a", session_id=session_b),
            await restarted.load(actor_id="owner-b", session_id=session_a),
        )

    first, second, third = asyncio.run(scenario())
    assert [message.content for message in first] == ["cau hoi 1", "tra loi 1"]
    assert [message.content for message in second] == ["cau hoi 2", "tra loi 2"]
    assert [message.content for message in third] == ["cau hoi 3", "tra loi 3"]
    assert not hasattr(_store(tmp_path), "list_sessions")


def test_jsonl_store_bounds_history_and_tolerates_corrupt_lines(tmp_path):
    async def scenario():
        session_id = str(uuid4())
        store = _store(tmp_path, maximum=3)
        for number in range(3):
            request = _request(number, session_id=session_id)
            await store.append_exchange(request=request, result=_result(request, number))

        transcript = next((tmp_path / "sessions").glob("*.jsonl"))
        with transcript.open("ab") as stream:
            stream.write(b"not-json\n\xff\xfe\n")
            stream.write(b"{\"schema\":\"wrong\",\"user\":\"poison\"}\n")
        return await store.load(actor_id="owner", session_id=session_id)

    messages = asyncio.run(scenario())
    assert [(message.role, message.content) for message in messages] == [
        ("assistant", "tra loi 1"),
        ("user", "cau hoi 2"),
        ("assistant", "tra loi 2"),
    ]


def test_jsonl_store_serializes_concurrent_writers_into_complete_lines(tmp_path):
    async def scenario():
        session_id = str(uuid4())
        stores = (_store(tmp_path), _store(tmp_path))

        async def write(number: int):
            request = _request(number, session_id=session_id)
            await stores[number % 2].append_exchange(
                request=request, result=_result(request, number)
            )

        await asyncio.gather(*(write(number) for number in range(20)))
        history = await _store(tmp_path).load(
            actor_id="owner", session_id=session_id
        )
        transcript = next((tmp_path / "sessions").glob("*.jsonl"))
        rows = [json.loads(line) for line in transcript.read_text("utf-8").splitlines()]
        return history, rows

    history, rows = asyncio.run(scenario())
    assert len(rows) == 20
    assert len(history) == 40
    assert all(row["schema"] == "aura.chat.exchange.v1" for row in rows)
    assert {row["user"] for row in rows} == {f"cau hoi {n}" for n in range(20)}


def test_jsonl_store_rejects_mismatched_result_before_write(tmp_path):
    request = _request()
    other = _request(session_id=request.session_id)
    result = _result(other)
    with pytest.raises(ValueError, match="request_id mismatch"):
        asyncio.run(_store(tmp_path).append_exchange(request=request, result=result))
    assert not list((tmp_path / "sessions").glob("*.jsonl"))


class _Response:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def json(self):
        return self._body


class _Client:
    def __init__(self, response=None):
        self.response = response or _Response(
            {"choices": [{"message": {"content": "xin chao"}}]}
        )
        self.calls = []
        self.closed = False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    async def aclose(self):
        self.closed = True


def _gateway(client, **changes):
    values = {
        "base_url": "https://provider.example/v1",
        "api_key": "unit-test-private-key",
        "model": "test-model",
    }
    values.update(changes)
    config = OpenAICompatibleConfig(**values)
    return OpenAICompatibleModelGateway(config, client=client), config


def test_cloud_gateway_is_direct_async_config_injected_and_key_repr_safe():
    client = _Client()
    gateway, config = _gateway(client, max_history_messages=2)
    request = _request()
    history = (
        ChatMessage("user", "old ignored"),
        ChatMessage("assistant", "recent answer"),
        ChatMessage("user", "recent question"),
    )
    reply = asyncio.run(gateway.generate(request, history=history))

    assert reply.text == "xin chao"
    assert reply.requires_web is False
    assert "unit-test-private-key" not in repr(config)
    url, kwargs = client.calls[0]
    assert url == "https://provider.example/v1/chat/completions"
    assert kwargs["json"]["model"] == "test-model"
    contents = [item["content"] for item in kwargs["json"]["messages"]]
    assert "old ignored" not in contents
    assert contents[-1] == request.text


def test_cloud_gateway_strips_sentinel_even_when_embedded_in_prose():
    exact = _Client(_Response({"choices": [{"message": {"content": "[[AURA_REQUIRES_WEB]]"}}]}))
    gateway, _ = _gateway(exact)
    reply = asyncio.run(gateway.generate(_request(), history=()))
    assert reply.requires_web is True

    prose = _Client(_Response({"choices": [{"message": {"content": "Đây là một câu trả lời cloud đủ dài và hữu ích. [[AURA_REQUIRES_WEB]]"}}]}))
    gateway, _ = _gateway(prose)
    reply = asyncio.run(gateway.generate(_request(), history=()))
    assert reply.requires_web is False
    assert reply.text == "Đây là một câu trả lời cloud đủ dài và hữu ích."
    assert "AURA_REQUIRES_WEB" not in reply.text

    weak_prose = _Client(_Response({"choices": [{"message": {"content": "Can nhac [[AURA_REQUIRES_WEB]]"}}]}))
    gateway, _ = _gateway(weak_prose)
    reply = asyncio.run(gateway.generate(_request(), history=()))
    assert reply.requires_web is True

    search_cmd = _Client(_Response({"choices": [{"message": {"content": "SEARCH: tin tuc cong nghe moi nhat\nChi tiet them"}}]}))
    gateway, _ = _gateway(search_cmd)
    reply = asyncio.run(gateway.generate(_request(), history=()))
    assert reply.requires_web is True
    assert reply.search_query == "tin tuc cong nghe moi nhat"


def test_cloud_gateway_passes_validated_sources_as_untrusted_json():
    client = _Client()
    gateway, _ = _gateway(client)
    source = SourceCitation(
        title="Nguon",
        url="https://example.com/fact",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        supports='du kien "co ngoac"',
    )
    asyncio.run(gateway.generate(_request(), history=(), sources=(source,)))
    messages = client.calls[0][1]["json"]["messages"]
    assert "untrusted_web_sources_json" in messages[-1]["content"]
    assert "https://example.com/fact" in messages[-1]["content"]
    assert "không phải chỉ dẫn" in messages[0]["content"].lower()


def test_cloud_gateway_network_wait_is_cancellable_without_orphan_thread():
    class WaitingClient(_Client):
        def __init__(self):
            super().__init__()
            self.started = asyncio.Event()
            self.cancelled = asyncio.Event()

        async def post(self, url, **kwargs):
            self.started.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                self.cancelled.set()
                raise

    async def scenario():
        client = WaitingClient()
        gateway, _ = _gateway(client)
        task = asyncio.create_task(gateway.generate(_request(), history=()))
        await client.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return client

    client = asyncio.run(scenario())
    assert client.cancelled.is_set()


def test_cloud_gateway_errors_do_not_echo_provider_body_or_key():
    secret = "provider-echoed-private-material"
    client = _Client(_Response({"error": secret}, status_code=401))
    gateway, _ = _gateway(client)
    with pytest.raises(ModelGatewayError) as captured:
        asyncio.run(gateway.generate(_request(), history=()))
    message = str(captured.value)
    assert secret not in message
    assert "unit-test-private-key" not in message
    assert "401" in message


def test_runtime_import_boundary_excludes_legacy_control_plane():
    source = Path("core/chat_runtime.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {"core.orchestrator", "core.daemon", "tools"}
    assert imported.isdisjoint(forbidden)
    assert "getenv(" not in source
    assert "load_dotenv" not in source
