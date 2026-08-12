from __future__ import annotations

import asyncio

import httpx
import pytest

from core.chat_runtime import OpenAICompatibleModelGateway
from core.local_first_gateway import LocalFirstGateway, OllamaGateway
from interface import chat_adapters


class _Process:
    def __init__(self, stdout: bytes = b"", returncode: int | None = 0):
        self.stdout = stdout
        self.returncode = returncode
        self.killed = False
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def communicate(self):
        self.started.set()
        if self.returncode is None:
            await self.release.wait()
        return self.stdout, b""

    def kill(self):
        self.killed = True
        self.returncode = -9
        self.release.set()

    async def wait(self):
        return self.returncode


def test_search_adapter_is_shell_free_and_returns_typed_citations(monkeypatch):
    raw = (
        "Title: Nguồn một\nURL: https://example.com/one\n"
        "Highlights:\nDữ kiện một\n"
        "Title: Nguồn hai\nURL: https://example.org/two\n"
        "Highlights:\nDữ kiện hai\n"
    ).encode()
    process = _Process(raw)
    calls = []

    async def create(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    sources = asyncio.run(
        chat_adapters.ReadOnlySearchGateway().search("giá & echo harmless")
    )

    assert len(sources) == 2
    assert sources[0].url == "https://example.com/one"
    assert calls and "shell" not in calls[0][1]
    assert any("giá & echo harmless" in argument for argument in calls[0][0])


def test_search_process_is_killed_when_service_cancels(monkeypatch):
    process = _Process(returncode=None)

    async def create(*_args, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)

    async def scenario():
        task = asyncio.create_task(
            chat_adapters.ReadOnlySearchGateway().search("tin mới nhất")
        )
        await process.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert process.killed is True


def test_missing_cloud_key_builds_visible_failure_runtime(tmp_path):
    """Tắt local thì mất khoá cloud phải thành lỗi NHÌN THẤY, không phải im lặng."""
    config = chat_adapters.ChatRuntimeConfig(
        transcript_root=tmp_path, local_enabled=False
    )
    runtime = chat_adapters.build_chat_runtime(config=config)
    assert isinstance(runtime.model, chat_adapters.UnavailableModelGateway)
    assert runtime.model_configured is False


def test_mac_dinh_la_LOCAL_FIRST_khong_phai_cloud_first(tmp_path):
    """Nguyên tắc gốc của Sếp: local là trò, cloud là thầy.

    Chat v1 từng đảo ngược mà không ai nói ra.  Test này là chốt chặn để lần
    sau ai viết lại composition root thì máy kêu, chứ không đợi Sếp phát hiện.
    """
    config = chat_adapters.ChatRuntimeConfig(
        base_url="https://example.com/v1",
        model="cloud-model",
        api_key="k",
        transcript_root=tmp_path,
    )
    runtime = chat_adapters.build_chat_runtime(config=config)
    assert isinstance(runtime.model, LocalFirstGateway)
    assert isinstance(runtime.model._local, OllamaGateway)
    assert isinstance(runtime.model._cloud, OpenAICompatibleModelGateway)
    assert runtime.model_configured is True


def test_khong_co_cloud_van_chay_duoc_bang_local(tmp_path):
    """Mất khoá cloud KHÔNG còn là chết máy — trò vẫn làm việc một mình."""
    config = chat_adapters.ChatRuntimeConfig(transcript_root=tmp_path)
    runtime = chat_adapters.build_chat_runtime(config=config)
    assert isinstance(runtime.model, LocalFirstGateway)
    assert runtime.model._cloud is None
    assert runtime.model_configured is True


def test_dung_runtime_KHONG_duoc_cham_mang(tmp_path, monkeypatch):
    """Ollama đang tắt mà `build_chat_runtime` chạm mạng thì chết cửa trước."""
    def _no_network(*_args, **_kwargs):
        raise AssertionError("build_chat_runtime vừa gọi mạng")

    monkeypatch.setattr(httpx.Client, "request", _no_network, raising=False)
    monkeypatch.setattr(httpx.AsyncClient, "request", _no_network, raising=False)
    chat_adapters.build_chat_runtime(
        config=chat_adapters.ChatRuntimeConfig(transcript_root=tmp_path)
    )


def test_tat_local_bang_bien_moi_truong(tmp_path, monkeypatch):
    monkeypatch.setenv("AURA_CHAT_LOCAL_ENABLED", "0")
    config = chat_adapters.ChatRuntimeConfig.from_environment(
        transcript_root=tmp_path
    )
    assert config.local_enabled is False
    monkeypatch.setenv("AURA_CHAT_LOCAL_ENABLED", "1")
    assert (
        chat_adapters.ChatRuntimeConfig.from_environment(
            transcript_root=tmp_path
        ).local_enabled
        is True
    )


def test_runtime_config_repr_never_contains_api_key(tmp_path):
    config = chat_adapters.ChatRuntimeConfig(
        base_url="https://example.com/v1",
        model="model",
        api_key="super-secret-key",
        transcript_root=tmp_path,
    )
    assert "super-secret-key" not in repr(config)
