"""Trí nhớ Markdown — luật cứng: câu của AI KHÔNG tự thành sự thật.

Chốt ở lượt 003 của Codex.  Ở đây luật đó không nằm trong tài liệu mà nằm trong
chữ ký hàm: `remember()` đòi `confirmed_by_user=True`.

Bối cảnh: 06/08/2026 đo được 13% ký ức cũ của AURA là rác xã giao, và không ai
biết suốt nhiều tháng vì nó nằm trong kho vector không mở ra xem được.
"""
from __future__ import annotations

import pytest

from core import user_memory
from core.user_memory import (
    MemoryRefused, as_prompt_block, forget, list_facts, parse_remember, remember, update,
)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(user_memory, "MEMORY_FILE", tmp_path / "nho.md")


# ------------------------------------------------- luật cứng: AI không tự ghi
def test_khong_xac_nhan_thi_KHONG_ghi():
    with pytest.raises(MemoryRefused):
        remember("Sếp thích ăn phở")
    assert list_facts() == []


def test_cau_do_AI_sinh_ra_khong_the_tu_thanh_su_that():
    """Mô phỏng: AURA vừa nói một câu và cố tự nhớ nó."""
    cau_cua_ai = "Sếp là người rất giỏi và luôn đúng"
    with pytest.raises(MemoryRefused):
        remember(cau_cua_ai)                       # gọi như code thường sẽ gọi
    assert cau_cua_ai not in as_prompt_block()


def test_co_xac_nhan_thi_ghi_duoc():
    fact = remember("Sếp tên Phạm Xuân Kiên", confirmed_by_user=True)
    assert fact["id"].startswith("m-")
    assert [f["text"] for f in list_facts()] == ["Sếp tên Phạm Xuân Kiên"]


# --------------------------------------------------------- người đọc/sửa được
def test_tep_la_markdown_nguoi_doc_duoc():
    remember("Sếp học Đại học Thái Bình", confirmed_by_user=True)
    raw = user_memory.MEMORY_FILE.read_text(encoding="utf-8")
    assert raw.startswith("# AURA nhớ gì về Sếp")
    assert "Sếp học Đại học Thái Bình" in raw
    assert "SỬA TAY ĐƯỢC" in raw, "tệp phải tự nói cho Sếp biết là sửa được"


def test_sep_xoa_tay_trong_tep_thi_AURA_quen_that():
    remember("điều một", confirmed_by_user=True)
    remember("điều hai", confirmed_by_user=True)
    raw = user_memory.MEMORY_FILE.read_text(encoding="utf-8")
    con_lai = "\n".join(l for l in raw.splitlines() if "điều một" not in l)
    user_memory.MEMORY_FILE.write_text(con_lai, encoding="utf-8")
    assert [f["text"] for f in list_facts()] == ["điều hai"]


def test_quen_va_sua():
    a = remember("điều cũ", confirmed_by_user=True)
    assert update(a["id"], "điều đã sửa") is True
    assert list_facts()[0]["text"] == "điều đã sửa"
    assert forget(a["id"]) is True
    assert list_facts() == []
    assert forget("m-khongco1") is False


# --------------------------------------------------------------- bí mật & rác
def test_bi_mat_khong_vao_tri_nho_du_Sep_bao_nho():
    remember("khoá của tôi là sk-abc123def456ghi789jkl", confirmed_by_user=True)
    raw = user_memory.MEMORY_FILE.read_text(encoding="utf-8")
    assert "sk-abc123def456ghi789jkl" not in raw
    assert "REDACTED" in raw


def test_khong_nho_trung_lap():
    remember("Sếp ở Thái Bình", confirmed_by_user=True)
    with pytest.raises(MemoryRefused):
        remember("sếp ở thái bình", confirmed_by_user=True)
    assert len(list_facts()) == 1


def test_cau_rong_va_qua_dai():
    with pytest.raises(MemoryRefused):
        remember("   ", confirmed_by_user=True)
    with pytest.raises(MemoryRefused):
        remember("x" * 501, confirmed_by_user=True)


def test_tri_nho_khong_phinh_vo_han(monkeypatch):
    monkeypatch.setattr(user_memory, "_MAX_FACTS", 3)
    for i in range(3):
        remember(f"điều {i}", confirmed_by_user=True)
    with pytest.raises(MemoryRefused):
        remember("điều thừa", confirmed_by_user=True)


# ------------------------------------------------------- nhận biết lệnh nhớ
@pytest.mark.parametrize("cau,mong_doi", [
    ("ghi nhớ: tôi tốt nghiệp Đại học Thái Bình", "tôi tốt nghiệp Đại học Thái Bình"),
    ("nhớ giúp tôi là tôi thích cà phê đen", "tôi thích cà phê đen"),
    ("ghi nhớ tôi làm việc ban đêm", "tôi làm việc ban đêm"),
    ("AURA hãy ghi nhớ tôi làm việc ban đêm", "tôi làm việc ban đêm"),
    ("remember: I prefer short answers", "I prefer short answers"),
])
def test_nhan_ra_lenh_nho(cau, mong_doi):
    assert parse_remember(cau) == mong_doi


@pytest.mark.parametrize("cau", [
    "hôm nay trời đẹp",
    "bạn có nhớ hôm qua mình nói gì không",
    "tôi quên mất mật khẩu",
    "",
])
def test_khong_suy_dien_tu_hoi_thoai_thuong(cau):
    """Không tự rút ký ức từ chuyện phiếm — đó đúng là cách kho cũ đầy rác."""
    assert parse_remember(cau) is None


def test_khoi_prompt_rong_khi_chua_nho_gi():
    assert as_prompt_block() == ""


def test_khoi_prompt_co_du_moi_dieu():
    remember("điều A", confirmed_by_user=True)
    remember("điều B", confirmed_by_user=True)
    block = as_prompt_block()
    assert "điều A" in block and "điều B" in block
    assert "Sếp tự xác nhận" in block
