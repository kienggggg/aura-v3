"""Cổng tra mạng — luật số một: KHÔNG TRA ĐƯỢC THÌ NÓI, KHÔNG ĐOÁN.

Một câu bịa kèm giọng chắc chắn còn tệ hơn một câu từ chối, vì người đọc không
phân biệt được.  Các test dưới ép mọi đường hỏng đều phải fail-closed.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from core import web_search
from core.web_search import SearchResult, format_result, is_search_request, search

_EXA_OUTPUT = """Title: Kimi K3 chinh thuc ra mat
URL: https://example.com/kimi-k3
Published: N/A
Author: N/A
Highlights:
Kimi K3 la mo hinh 2.8T tham so.
...
Ho tro cua so 1 trieu token.

Title: Bai phan tich
URL: https://example.org/phan-tich
Highlights:
Danh gia doc lap ve hieu nang.
"""


class _Proc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture
def run(monkeypatch):
    def use(result):
        def fake(*args, **kwargs):
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(subprocess, "run", fake)

    return use


# --------------------------------------------------------------------- nhận biết
@pytest.mark.parametrize("text", [
    "tra mạng giúp tôi về Kimi K3",
    "tìm thông tin về Anthropic",
    "model AI mới nhất",
    "giá bitcoin bây giờ",
    "tin tức hôm nay",
])
def test_nhan_ra_cau_can_tra(text):
    assert is_search_request(text) is True


@pytest.mark.parametrize("text", [
    "mật khẩu wifi nhà mình là gì",
    "2 cộng 2 bằng mấy",
    "viết giúp tôi một hàm python",
])
def test_khong_tra_khi_khong_can(text):
    assert is_search_request(text) is False


# ------------------------------------------------------------------------ bóc tách
def test_boc_duoc_nguon_that(run):
    run(_Proc(stdout=_EXA_OUTPUT))
    res = search("kimi k3")
    assert res.ok is True
    assert [s.url for s in res.sources] == [
        "https://example.com/kimi-k3", "https://example.org/phan-tich",
    ]
    assert "2.8T" in res.sources[0].snippet
    assert res.fetched_at, "phải ghi thời điểm tra"


def test_chi_nhan_http_https_cong_khai_va_loai_trung(run):
    run(_Proc(stdout="""Title: hop le
URL: HTTPS://Example.COM/a#mot
Highlights:
nguon mot

Title: trung
URL: https://example.com/a#hai
Highlights:
nguon lap

Title: sai scheme
URL: javascript:alert(1)
Highlights:
khong duoc nhan

Title: sai url
URL: https://
Highlights:
khong duoc nhan

Title: noi bo
URL: http://127.0.0.1/admin
Highlights:
khong duoc nhan
"""))
    res = search("x")
    assert res.ok is True
    assert [source.url for source in res.sources] == ["https://example.com/a"]


@pytest.mark.parametrize("url", [
    "http://2130706433/admin",
    "http://0x7f000001/admin",
    "http://127.1/admin",
    "http://0177.0.0.1/admin",
    "https://example.com:99999/path",
    "https://example.com /path",
    "https://example.com/has space",
])
def test_loai_host_so_mo_ho_port_sai_va_khoang_trang_tho(run, url):
    run(_Proc(stdout=f"Title: poisoned\nURL: {url}\nHighlights:\nkhong duoc nhan\n"))
    res = search("x")
    assert res.ok is False
    assert res.sources == []


def test_bo_qua_khoi_khong_co_url(run):
    run(_Proc(stdout="Title: khong co lien ket\nHighlights:\nabc\n"))
    assert search("x").ok is False


# --------------------------------------------------------------------- fail-closed
def test_thieu_cong_cu_thi_bao_khong_tra_duoc(run):
    run(FileNotFoundError())
    res = search("x")
    assert res.ok is False
    assert res.sources == []
    assert "mcporter" in res.error


def test_qua_gio_thi_bao_khong_tra_duoc(run):
    run(subprocess.TimeoutExpired(cmd="mcporter", timeout=1))
    res = search("x")
    assert res.ok is False
    assert "quá" in res.error


def test_cong_cu_bao_loi_thi_khong_bia(run):
    run(_Proc(stdout="", stderr="network unreachable", returncode=1))
    res = search("x")
    assert res.ok is False
    assert res.sources == []


def test_cong_cu_nonzero_co_stdout_van_fail_closed(run):
    run(_Proc(stdout=_EXA_OUTPUT, stderr="partial failure", returncode=7))
    res = search("x")
    assert res.ok is False
    assert res.sources == []
    assert "partial failure" in res.error


def test_loi_la_van_fail_closed(run):
    run(RuntimeError("hỏng bất ngờ"))
    res = search("x")
    assert res.ok is False
    assert res.sources == []


def test_cau_rong():
    assert search("   ").ok is False


@pytest.mark.parametrize("query", [
    "python & whoami",
    "python | whoami",
    "python (whoami)",
    'python \"; whoami; \"',
])
def test_metachar_la_du_lieu_khong_phai_lenh(monkeypatch, query):
    captured = {}

    def fake(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _Proc(stdout=_EXA_OUTPUT)

    monkeypatch.setattr(subprocess, "run", fake)
    assert search(query).ok is True
    assert isinstance(captured["args"], list)
    assert captured["args"][-2] == "call"
    assert json.dumps(query, ensure_ascii=False) in captured["args"][-1]
    assert captured["kwargs"]["shell"] is False
    assert query not in captured["args"][:-1]


@pytest.mark.parametrize("query", ["dong mot\ndong hai", "\ndong hai", "nul\x00byte"])
def test_newline_va_nul_bi_tu_choi_truoc_khi_goi_cong_cu(monkeypatch, query):
    def forbidden(*args, **kwargs):
        pytest.fail("không được gọi subprocess với query chứa newline/NUL")

    monkeypatch.setattr(subprocess, "run", forbidden)
    res = search(query)
    assert res.ok is False
    assert res.sources == []


def test_query_qua_dai_bi_tu_choi(run):
    run(AssertionError("không được gọi công cụ"))
    res = search("x" * 501)
    assert res.ok is False


# ------------------------------------------------------------------------- trình bày
def test_that_bai_thi_noi_thang_khong_doan():
    res = SearchResult(query="x", ok=False, fetched_at="09/08/2026 10:00",
                       error="mạng chết")
    out = format_result(res)
    assert "Không tra được" in out
    assert "KHÔNG đoán" in out


def test_thanh_cong_thi_LUON_co_url_va_gio(run):
    run(_Proc(stdout=_EXA_OUTPUT))
    out = format_result(search("kimi k3"))
    assert "https://example.com/kimi-k3" in out
    assert "https://example.org/phan-tich" in out
    assert "Tra lúc" in out
    assert "chưa phải kết luận" in out, "phải tách dữ kiện nguồn khỏi suy luận"


def test_cong_khong_bao_gio_goi_model(run):
    """Cổng này chỉ lấy nguyên liệu. Có model chen vào là sai thiết kế."""
    import inspect

    src = inspect.getsource(web_search)
    for cam in ("openai", "gemini", "ollama", "complete(", "chat_completion"):
        assert cam not in src.lower(), f"cổng tra mạng không được gọi model ({cam})"
