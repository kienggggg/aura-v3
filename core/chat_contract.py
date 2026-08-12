"""Pure data contract for the AURA Chat v1 front door.

This module deliberately has no dependency on the old orchestrator, daemon,
tools, configuration, environment variables, or any concrete provider.  It is
safe to import from HTTP, Telegram, tests, and future clients.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ipaddress import ip_address
import re
from typing import Iterable
from urllib.parse import urlparse
from uuid import UUID


MAX_TEXT_CODEPOINTS = 12_000
MAX_ACTOR_ID_CODEPOINTS = 128
_ENCODED_CONTROL_RE = re.compile(r"(?i)%(?:0[0-9a-f]|1[0-9a-f]|7f)")
_AMBIGUOUS_NUMERIC_HOST_RE = re.compile(
    r"(?i)^(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*$"
)


class Channel(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"
    TEST = "test"


class ChatStatus(str, Enum):
    OK = "ok"
    CANNOT_ANSWER = "cannot_answer"
    WEB_UNAVAILABLE = "web_unavailable"
    BACKEND_ERROR = "backend_error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ContentCheck:
    """A guard decision plus the only input text permitted in transcripts."""

    allowed: bool
    transcript_text: str
    rejection_text: str = ""

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(self.allowed, bool):
            errors.append("allowed must be bool")
        if not isinstance(self.transcript_text, str):
            errors.append("transcript_text must be a string")
        if self.allowed is False and (
            not isinstance(self.rejection_text, str)
            or not self.rejection_text.strip()
        ):
            errors.append("rejection_text is required when input is rejected")
        return tuple(errors)


def _valid_uuid(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.int != 0


def _contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """One request entering AURA Chat.

    Construction is intentionally non-throwing for ordinary bad client data.
    ``ChatService.reply`` validates it and returns ``status=rejected`` before
    touching any provider or transcript store.
    """

    request_id: str
    session_id: str
    actor_id: str
    channel: Channel | str
    text: str

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not _valid_uuid(self.request_id):
            errors.append("request_id must be a non-zero UUID")
        if not _valid_uuid(self.session_id):
            errors.append("session_id must be a non-zero UUID")
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            errors.append("actor_id is required")
        elif len(self.actor_id) > MAX_ACTOR_ID_CODEPOINTS:
            errors.append(
                f"actor_id exceeds {MAX_ACTOR_ID_CODEPOINTS} Unicode code points"
            )
        try:
            Channel(self.channel)
        except (ValueError, TypeError):
            errors.append("channel must be web, telegram, or test")
        if not isinstance(self.text, str) or not self.text.strip():
            errors.append("text is required")
        elif len(self.text) > MAX_TEXT_CODEPOINTS:
            errors.append(f"text exceeds {MAX_TEXT_CODEPOINTS} Unicode code points")
        return tuple(errors)

    @property
    def channel_value(self) -> Channel:
        return Channel(self.channel)


@dataclass(frozen=True, slots=True)
class SourceCitation:
    title: str
    url: str
    retrieved_at: str
    supports: str

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(self.title, str) or not self.title.strip():
            errors.append("citation title is required")
        elif _contains_control(self.title):
            errors.append("citation title cannot contain control characters")

        if not isinstance(self.url, str):
            errors.append("citation URL must be a string")
        else:
            try:
                parsed = urlparse(self.url)
                hostname = parsed.hostname
                parsed.port  # validate malformed and out-of-range ports
            except ValueError:
                parsed = None
                hostname = None
                errors.append("citation URL is malformed")
            if any(character.isspace() for character in self.url):
                errors.append("citation URL cannot contain raw whitespace")
            if _contains_control(self.url) or _ENCODED_CONTROL_RE.search(self.url):
                errors.append("citation URL cannot contain control characters")
            if (
                parsed is None
                or parsed.scheme.lower() not in {"http", "https"}
                or not parsed.netloc
                or not hostname
            ):
                errors.append("citation URL must be an absolute http/https URL")
            elif parsed.username is not None or parsed.password is not None:
                errors.append("citation URL cannot contain credentials")
            else:
                host = hostname.rstrip(".").lower()
                if host == "localhost" or host.endswith(".localhost"):
                    errors.append("citation URL cannot target localhost")
                elif host == "local" or host.endswith(".local"):
                    errors.append("citation URL cannot target a .local host")
                else:
                    try:
                        literal_ip = ip_address(host)
                    except ValueError:
                        # This is syntactic validation only. Deliberately do not
                        # resolve DNS here, so this is not an SSRF boundary.
                        if _AMBIGUOUS_NUMERIC_HOST_RE.fullmatch(host):
                            errors.append(
                                "citation URL cannot use an ambiguous numeric host"
                            )
                    else:
                        if not literal_ip.is_global:
                            errors.append(
                                "citation URL cannot target a non-global IP literal"
                            )

        if not isinstance(self.retrieved_at, str):
            errors.append("retrieved_at must be an ISO-8601 string")
        else:
            try:
                parsed_time = datetime.fromisoformat(
                    self.retrieved_at.replace("Z", "+00:00")
                )
            except ValueError:
                errors.append("retrieved_at must be valid ISO-8601")
            else:
                if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
                    errors.append("retrieved_at must include a timezone")

        if not isinstance(self.supports, str) or not self.supports.strip():
            errors.append("citation supports is required")
        elif _contains_control(self.supports):
            errors.append("citation supports cannot contain control characters")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class OutwardContent:
    """All user-visible text scrubbed by ContentGuard in one batch."""

    text: str
    sources: tuple[SourceCitation, ...] = ()
    fallback_text: str = ""


@dataclass(frozen=True, slots=True)
class ChatResult:
    request_id: str
    session_id: str
    status: ChatStatus | str
    text: str
    used_web: bool
    sources: tuple[SourceCitation, ...]
    latency_ms: int

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not _valid_uuid(self.request_id):
            errors.append("request_id must be a non-zero UUID")
        if not _valid_uuid(self.session_id):
            errors.append("session_id must be a non-zero UUID")
        try:
            status = ChatStatus(self.status)
        except (ValueError, TypeError):
            status = None
            errors.append("status is not a ChatStatus")
        if not isinstance(self.text, str) or not self.text.strip():
            errors.append("result text is required")
        if not isinstance(self.used_web, bool):
            errors.append("used_web must be bool")
        if not isinstance(self.sources, tuple) or not all(
            isinstance(item, SourceCitation) for item in self.sources
        ):
            errors.append("sources must be a tuple of SourceCitation")
        else:
            for index, source in enumerate(self.sources):
                errors.extend(
                    f"sources[{index}]: {error}"
                    for error in source.validation_errors()
                )
        if self.used_web is False and self.sources:
            errors.append("sources must be empty when used_web is false")
        if status is ChatStatus.OK and self.used_web and len(self.sources) < 2:
            errors.append("web-backed ok result requires at least two sources")
        if not isinstance(self.latency_ms, int) or isinstance(self.latency_ms, bool):
            errors.append("latency_ms must be an integer")
        elif self.latency_ms < 0:
            errors.append("latency_ms cannot be negative")
        return tuple(errors)


def valid_citations(
    citations: Iterable[SourceCitation],
) -> tuple[SourceCitation, ...]:
    """Return valid, URL-distinct citations without repairing bad evidence."""

    accepted: list[SourceCitation] = []
    seen_urls: set[str] = set()
    for item in citations:
        if not isinstance(item, SourceCitation) or item.validation_errors():
            continue
        parsed = urlparse(item.url)
        identity = (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
        )
        key = repr(identity)
        if key in seen_urls:
            continue
        seen_urls.add(key)
        accepted.append(item)
    return tuple(accepted)
