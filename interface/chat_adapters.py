# -*- coding: utf-8 -*-
"""Composition root for the small, read-only AURA Chat v1 runtime.

The HTTP layer must not choose a model, build prompts, search the web, or own
transcript persistence.  This module wires the provider-neutral ``ChatService``
to the concrete async model/store adapters in ``core.chat_runtime`` and to one
read-only, cancellable search adapter.

Importing this module performs no network I/O and starts no worker.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Sequence

from core.chat_contract import ChatRequest, SourceCitation
from core.chat_runtime import (
    JsonlSessionStore,
    JsonlSessionStoreConfig,
    ModelGatewayError,
    OpenAICompatibleConfig,
    OpenAICompatibleModelGateway,
)
from core.chat_service import ChatMessage, ChatService, ModelReply
from core.paths import PROJECT_ROOT
from core.local_first_gateway import (
    LocalFirstGateway,
    OllamaConfig,
    OllamaGateway,
)
from core.secret_guard import SecretContentGuard


_MAX_SEARCH_QUERY_CODEPOINTS = 500
_MAX_SEARCH_SOURCES = 4


@dataclass(frozen=True, slots=True)
class ChatRuntimeConfig:
    """Explicit Chat-only configuration; the API key is never represented."""

    base_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    timeout_s: float = 90.0
    transcript_root: Path = PROJECT_ROOT / "data" / "chat_sessions"
    # Trần số lượt đang xử lý cùng lúc.  Codex yêu cầu ở lượt 009: timeout liên
    # tiếp có thể đẻ việc nghẽn vô hạn và đốt RAM/hạn mức.  Bản viết lại giữa
    # chừng đã gỡ mất; đây là lần cắm lại, đặt ở LÕI để mọi kênh (web, Telegram)
    # đều được che chứ không riêng cửa web.
    max_concurrent_replies: int = 4
    # LOCAL-FIRST: trò làm trước, cloud chỉ là thầy.  Đây là nguyên tắc gốc ghi
    # trong `core/brain_router.py`; Chat v1 từng đảo thành cloud-only mà không
    # ai nói ra.  Đặt `AURA_CHAT_LOCAL_ENABLED=0` để quay lại cloud-only.
    local_enabled: bool = True
    local_host: str = "http://localhost:11434"
    local_model: str = "qwen3.5:4b"

    @classmethod
    def from_environment(
        cls,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float | None = None,
        transcript_root: Path | None = None,
    ) -> "ChatRuntimeConfig":
        """Read only ``AURA_CHAT_*`` variables; never legacy router settings."""

        env_timeout = os.environ.get("AURA_CHAT_TIMEOUT_S", "").strip()
        if timeout_s is None:
            try:
                timeout_s = float(env_timeout) if env_timeout else 90.0
            except ValueError:
                timeout_s = 90.0
        local_flag = os.environ.get("AURA_CHAT_LOCAL_ENABLED", "1").strip().lower()
        return cls(
            local_enabled=local_flag not in ("0", "false", "no", "off"),
            local_host=(
                os.environ.get("AURA_CHAT_LOCAL_HOST", "").strip()
                or "http://localhost:11434"
            ),
            local_model=(
                os.environ.get("AURA_CHAT_LOCAL_MODEL", "").strip()
                or "qwen3.5:4b"
            ),
            base_url=(
                base_url
                if base_url is not None
                else os.environ.get("AURA_CHAT_BASE_URL", "")
            ).strip(),
            model=(
                model
                if model is not None
                else os.environ.get("AURA_CHAT_MODEL", "")
            ).strip(),
            api_key=os.environ.get("AURA_CHAT_API_KEY", ""),
            timeout_s=float(timeout_s),
            transcript_root=(
                Path(transcript_root)
                if transcript_root is not None
                else Path(
                    os.environ.get(
                        "AURA_CHAT_TRANSCRIPT_ROOT",
                        str(PROJECT_ROOT / "data" / "chat_sessions"),
                    )
                )
            ),
        )


class UnavailableModelGateway:
    """Keep the front door alive when no Chat-v1 cloud key is configured."""

    async def generate(
        self,
        request: ChatRequest,
        *,
        history: Sequence[ChatMessage],
        sources: Sequence[SourceCitation] = (),
    ) -> ModelReply:
        raise ModelGatewayError(
            "AURA Chat v1 cloud model is not configured"
        )


class ReadOnlySearchGateway:
    """Async/cancellable adapter for the existing read-only search command.

    ``core.web_search.search`` is synchronous.  Wrapping it in ``to_thread``
    would recreate the orphan-worker bug from the prototype: timing out would
    stop waiting but not stop the subprocess.  This adapter launches the same
    shell-free argv asynchronously and kills that exact process on cancellation.
    """

    async def search(self, query: str) -> Sequence[SourceCitation]:
        from core import web_search as backend

        if not isinstance(query, str):
            return ()
        query = query.strip()
        if (
            not query
            or len(query) > _MAX_SEARCH_QUERY_CODEPOINTS
            or any(character in query for character in ("\x00", "\r", "\n"))
        ):
            return ()

        encoded_query = json.dumps(query, ensure_ascii=False)
        call = (
            "exa.web_search_exa("
            f"query: {encoded_query}, numResults: {_MAX_SEARCH_SOURCES})"
        )
        argv = backend._mcporter_argv(call)
        process: asyncio.subprocess.Process | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await process.communicate()
        except asyncio.CancelledError:
            if process is not None and process.returncode is None:
                process.kill()
                try:
                    await process.wait()
                except (ProcessLookupError, OSError):
                    pass
            raise
        except (FileNotFoundError, OSError):
            return ()
        except Exception:
            # FAIL-CLOSED cho MỌI lỗi, không chỉ lỗi tiến trình.
            #
            # 10/08/2026 đo được: câu "tỷ giá USD/VND hiện nay" trả về
            # `backend_error` mà KHÔNG có một lời gọi HTTP nào — model chưa từng
            # được chạm tới.  Ngoại lệ lạ ở khâu tra chui qua đây, lên tới
            # `ChatService` và bị gán nhãn "lỗi ở bộ não".  Sai hai lần: sai
            # status (hợp đồng lượt 003 buộc `web_unavailable`) và sai lời báo
            # cho Sếp (đổ tội cho bộ não trong khi bộ não vô can).
            #
            # `core.web_search.search()` vốn đã bắt rộng đúng vì lẽ này; bản
            # async viết lại thu hẹp lại và làm bài học cũ tái phát.
            return ()

        if process.returncode != 0:
            return ()
        try:
            raw = stdout.decode("utf-8", errors="replace").strip()
            found = backend._parse_exa(raw)
        except Exception:
            return ()
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return tuple(
            SourceCitation(
                title=item.title,
                url=item.url,
                retrieved_at=retrieved_at,
                supports=item.snippet or item.title,
            )
            for item in found[:_MAX_SEARCH_SOURCES]
        )


class BoundedChatService:
    """Chặn quá tải: quá trần thì TỪ CHỐI SỚM, không xếp hàng vô hạn.

    Xếp hàng vô hạn nhìn thì "lịch sự" nhưng thực ra là im lặng có trì hoãn —
    người dùng vẫn ngồi chờ, còn máy vẫn nuốt RAM và hạn mức.  Nói thẳng "đang
    bận" là câu trả lời trung thực hơn.

    Đếm bằng số nguyên chứ không dùng `Semaphore`: vòng lặp sự kiện chạy một
    luồng nên phép tăng/giảm giữa hai lần `await` là nguyên tử, và cách này cho
    biết CHÍNH XÁC lúc nào đã đầy (Semaphore không có `acquire` không chờ).
    """

    _BUSY_TEXT = (
        "🚦 AURA đang xử lý {limit} câu cùng lúc rồi nên chưa nhận thêm.\n"
        "Sếp đợi một chút rồi hỏi lại nhé — em từ chối sớm để máy khỏi nghẽn."
    )

    def __init__(self, inner: ChatService, limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("max_concurrent_replies must be a positive int")
        self._inner = inner
        self._limit = limit
        self._active = 0

    @property
    def active(self) -> int:
        return self._active

    async def reply(self, request: ChatRequest):
        from core.chat_contract import ChatResult, ChatStatus

        if self._active >= self._limit:
            return ChatResult(
                request_id=request.request_id,
                session_id=request.session_id,
                status=ChatStatus.BACKEND_ERROR,
                text=self._BUSY_TEXT.format(limit=self._limit),
                used_web=False,
                sources=(),
                latency_ms=0,
            )
        self._active += 1
        try:
            return await self._inner.reply(request)
        finally:
            self._active -= 1


@dataclass(frozen=True, slots=True)
class ChatRuntime:
    service: ChatService
    store: JsonlSessionStore
    guard: SecretContentGuard
    model: object
    model_configured: bool

    async def aclose(self) -> None:
        closer = getattr(self.model, "aclose", None)
        if closer is not None:
            await closer()


def build_chat_runtime(
    *,
    config: ChatRuntimeConfig | None = None,
    transcript_root: Path | None = None,
) -> ChatRuntime:
    """Build one Chat v1 runtime without importing the old orchestrator."""

    runtime_config = config or ChatRuntimeConfig.from_environment(
        transcript_root=transcript_root
    )
    if runtime_config.timeout_s <= 0:
        raise ValueError("Chat timeout must be positive")
    root = transcript_root or runtime_config.transcript_root
    store = JsonlSessionStore(
        JsonlSessionStoreConfig(root=root, max_history_messages=60)
    )

    cloud: object | None = None
    cloud_configured = bool(
        runtime_config.base_url
        and runtime_config.model
        and runtime_config.api_key
    )
    if cloud_configured:
        try:
            cloud = OpenAICompatibleModelGateway(
                OpenAICompatibleConfig(
                    base_url=runtime_config.base_url,
                    api_key=runtime_config.api_key,
                    model=runtime_config.model,
                    timeout_s=min(60.0, runtime_config.timeout_s),
                    max_history_messages=24,
                )
            )
        except ValueError:
            # Bad provider configuration must become a visible backend_error
            # through ChatService, never an import/startup crash or leaked URL.
            cloud = None
            cloud_configured = False

    # BẬC THANG: local trước, cloud làm thầy.  Không dò Ollama ở đây — dựng
    # runtime mà chạm mạng thì một cái máy chủ đang tắt sẽ làm chết cửa trước.
    # Ollama tắt sẽ thành `ModelGatewayError` lúc trả lời, và bậc thang mượn
    # thầy; hết cả hai thì Sếp nhận một câu nói rõ máy nào chưa chạy.
    if runtime_config.local_enabled:
        model: object = LocalFirstGateway(
            local=OllamaGateway(
                OllamaConfig(
                    host=runtime_config.local_host,
                    model=runtime_config.local_model,
                    timeout_s=runtime_config.timeout_s,
                )
            ),
            cloud=cloud,
        )
        model_configured = True
    else:
        model = cloud if cloud is not None else UnavailableModelGateway()
        model_configured = cloud_configured

    guard = SecretContentGuard()
    service = BoundedChatService(
        ChatService(
            model=model,
            store=store,
            guard=guard,
            web=ReadOnlySearchGateway(),
            timeout_s=runtime_config.timeout_s,
        ),
        runtime_config.max_concurrent_replies,
    )
    return ChatRuntime(
        service=service,
        store=store,
        guard=guard,
        model=model,
        model_configured=model_configured,
    )


__all__ = [
    "ChatRuntime",
    "ChatRuntimeConfig",
    "ReadOnlySearchGateway",
    "UnavailableModelGateway",
    "build_chat_runtime",
]
