"""Static DOM/source-contract checks for AURA Chat v1.

These tests do not launch a real browser and must not be reported as browser
E2E evidence.  They catch regressions in the shipped HTML while a two-tab real
browser smoke test remains a separate acceptance item.
"""
from pathlib import Path


HTML_PATH = Path(__file__).resolve().parents[1] / "interface" / "web" / "chat.html"


def _html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def test_khong_moc_them_loi_tiem_ma_khac():
    """Bổ sung cho guard sẵn có, KHÔNG thay nó.

    `test_ui_handles_timeout_http_and_non_json_without_html_injection` đã chặn
    thuộc tính gán-mã-trang bằng cách tìm thẳng cái tên trong toàn tệp — thô
    nhưng chắc.  Bộ dịch Markdown (10/08/2026) phải sống chung được với luật
    đó, nên ngay cả chú thích trong `chat.html` cũng không viết tên nó ra.
    Ở đây chỉ khoá thêm mấy lối khác.
    """
    html = _html()
    for cam in ("insertAdjacentHTML", "document.write", "eval(", "new Function("):
        assert cam not in html, f"cửa chat vừa mọc lối tiêm mã: {cam}"


def test_dich_markdown_dung_nut_DOM():
    html = _html()
    assert "function dichMarkdown(" in html
    assert "function dichInline(" in html
    # Ba thứ model hay dùng nhất: đậm, khối mã, danh sách.
    assert "createElement('strong')" in html
    assert "createElement('pre')" in html
    assert "'ul' : 'ol'" in html, "danh sách phải dựng bằng thẻ thật"
    # Chữ Sếp gõ thì hiện y nguyên, không dịch.
    assert "role === 'user'" in html


def test_tab_session_uses_sessionstorage_and_uuid_shape():
    html = _html()
    assert "sessionStorage.getItem('aura_session_id')" in html
    assert "sessionStorage.setItem('aura_session_id', s)" in html
    assert "localStorage.getItem" not in html
    assert "crypto.randomUUID" in html
    assert "bytes[6]" in html and "bytes[8]" in html
    assert "function validSessionId(value)" in html
    assert "!validSessionId(s)" in html
    assert "sessionStorage.setItem('aura_session_id', s)" in html
    assert "!/^0{32}$/i.test(value.replaceAll('-', ''))" in html


def test_ui_uses_exact_chat_v1_fields_and_bounded_input():
    html = _html()
    assert 'maxlength="12000"' in html
    # 16/08/2026: thêm thanh chọn phòng, nên payload có thêm `phong` — nhưng
    # CHỈ khi Sếp chọn. Không chọn thì trường đó không tồn tại, và máy chủ cũ
    # chưa biết `phong` vẫn chạy y như trước. Test giữ cả HAI khẳng định:
    #   - đường không chọn phòng phải y hệt hợp đồng cũ
    #   - đường có chọn phòng chỉ được THÊM `phong`, không đổi hai trường kia
    assert "{text, session_id: SID}" in html
    assert "{text, session_id: SID, phong: phongDangChon}" in html
    assert "data.text" in html
    assert "data.latency_ms" in html
    assert "data.sources" in html
    assert "data.reply" not in html
    assert "elapsed_s" not in html


def test_ui_handles_timeout_http_and_non_json_without_html_injection():
    html = _html()
    assert "new AbortController()" in html
    assert "controller.abort()" in html
    assert "response.ok" in html
    assert "JSON.parse(raw)" in html
    assert ".textContent = text" in html
    assert "innerHTML" not in html
    assert "noopener noreferrer" in html


def test_chat_only_ui_has_no_link_to_unregistered_memory_route():
    assert 'href="/memory"' not in _html()
