from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from core.chat_contract import (
    MAX_TEXT_CODEPOINTS,
    Channel,
    ChatRequest,
    ChatResult,
    ChatStatus,
    ContentCheck,
    SourceCitation,
)


def _request(**changes) -> ChatRequest:
    values = {
        "request_id": str(uuid4()),
        "session_id": str(uuid4()),
        "actor_id": "owner",
        "channel": Channel.TEST,
        "text": "xin chào",
    }
    values.update(changes)
    return ChatRequest(**values)


def _source(url: str = "https://example.com/article") -> SourceCitation:
    return SourceCitation(
        title="Nguồn thử",
        url=url,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        supports="Hỗ trợ dữ kiện đang trả lời.",
    )


def test_request_accepts_exact_unicode_limit_and_typed_channel():
    request = _request(text="ộ" * MAX_TEXT_CODEPOINTS, channel="web")
    assert request.validation_errors() == ()
    assert request.channel_value is Channel.WEB


def test_request_reports_empty_oversize_and_invalid_identity():
    empty = _request(text="  ")
    oversize = _request(text="a" * (MAX_TEXT_CODEPOINTS + 1))
    bad_id = _request(session_id="not-a-uuid")
    assert any("text is required" in item for item in empty.validation_errors())
    assert any("exceeds" in item for item in oversize.validation_errors())
    assert any("session_id" in item for item in bad_id.validation_errors())


def test_content_check_requires_safe_shape_and_rejection_message():
    assert ContentCheck(True, "safe text").validation_errors() == ()
    assert ContentCheck(False, "[REDACTED]", "blocked").validation_errors() == ()
    assert ContentCheck(False, "[REDACTED]").validation_errors()


def test_citation_requires_http_url_and_timezone():
    bad = SourceCitation(
        title="x",
        url="file:///C:/secret.txt",
        retrieved_at="2026-08-09T10:00:00",
        supports="x",
    )
    errors = bad.validation_errors()
    assert any("http/https" in item for item in errors)
    assert any("timezone" in item for item in errors)


def test_citation_rejects_local_hosts_non_global_ips_and_credentials():
    urls = (
        "http://localhost/admin",
        "https://printer.local/status",
        "http://127.0.0.1/private",
        "http://10.0.0.4/private",
        "http://[::1]/private",
        "https://user:password@example.com/article",
    )
    for url in urls:
        errors = _source(url).validation_errors()
        assert errors, f"dangerous citation URL was accepted: {url}"


def test_citation_rejects_ambiguous_numeric_hosts_and_invalid_ports():
    urls = (
        "http://2130706433/private",
        "http://0x7f000001/private",
        "http://127.1/private",
        "http://0177.0.0.1/private",
        "https://example.com:65536/article",
    )
    for url in urls:
        errors = _source(url).validation_errors()
        assert errors, f"ambiguous or invalid URL was accepted: {url}"


def test_citation_rejects_raw_whitespace_anywhere_in_url():
    for url in (
        "https://example.com/a path",
        " https://example.com/article",
        "https://example.com/article ",
        "https://example.com/\tarticle",
    ):
        errors = _source(url).validation_errors()
        assert any("whitespace" in item for item in errors), url


def test_citation_rejects_literal_and_percent_encoded_controls():
    for url in (
        "https://example.com/line\nbreak",
        "https://example.com/%0Aheader",
        "https://example.com/%7fdelete",
    ):
        errors = _source(url).validation_errors()
        assert any("control" in item for item in errors), url


def test_citation_syntax_check_does_not_claim_dns_resolution():
    # A normal hostname remains valid. Network-layer address pinning belongs in
    # the fetcher; this pure contract intentionally performs no DNS lookup.
    assert _source("https://example.com/article").validation_errors() == ()


def test_result_rejects_web_ok_without_two_valid_sources():
    request = _request()
    result = ChatResult(
        request_id=request.request_id,
        session_id=request.session_id,
        status=ChatStatus.OK,
        text="có nguồn",
        used_web=True,
        sources=(_source(),),
        latency_ms=1,
    )
    assert any("at least two" in item for item in result.validation_errors())


def test_valid_result_is_self_consistent():
    request = _request()
    result = ChatResult(
        request_id=request.request_id,
        session_id=request.session_id,
        status="ok",
        text="câu trả lời",
        used_web=False,
        sources=(),
        latency_ms=0,
    )
    assert result.validation_errors() == ()
