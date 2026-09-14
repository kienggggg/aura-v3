# -*- coding: utf-8 -*-
"""Hàng chờ đăng — `CHOT:dang-vong-2` (14/09/2026).

App ghi `kich_ban.md` + `meta.json` qua MỘT hàm cho cả hai đường; công cụ đăng đọc hàng chờ
và sổ đăng. Chạy trong venv v3, không Playwright, không đụng `data/` thật.
"""
from __future__ import annotations

import ast
import hashlib
import json

import pytest

from core.paths import PROJECT_ROOT
from interface import noi_bo_api as api
from tools import dang_truyen_worker as w


def test_GHI_KICH_BAN_kem_meta_va_SHA_cua_chinh_tep(tmp_path):
    hv = api._ghi_kich_ban(tmp_path / "t1", "Câu một. Câu hai.", "người gác chắn tàu", "truyen")
    kb = (tmp_path / "t1" / "kich_ban.md").read_bytes()
    meta = json.loads((tmp_path / "t1" / "meta.json").read_text(encoding="utf-8"))
    # Windows: `write_text` đổi "\n" thành "\r\n" (đo 14/09 — bản đầu bài này kỳ vọng LF và
    # đỏ). SHA là của BYTE TRÊN ĐĨA, nên dù xuống dòng kiểu nào, meta vẫn khớp tệp.
    assert kb.decode("utf-8").replace("\r\n", "\n") == "Câu một. Câu hai.\n"
    assert meta["sha256"] == hashlib.sha256(kb).hexdigest() == hv["sha256"]
    assert meta["chu_de"] == "người gác chắn tàu" and meta["the_loai"] == "truyen" and meta["luc"]
    assert hv["name"] == "kich_ban.md" and hv["kind"] == "kich_ban_cho_alpha"


def test_HAI_DUONG_cua_app_deu_ghi_qua_MOT_ham():
    """`/api/dispatch` và `/api/pipeline/run` đều ghi kịch bản. Một đường ghi thẳng tệp là
    một đường không có `meta.json` — và hàng chờ sẽ lặng lẽ bỏ sót mọi kịch bản từ đó."""
    nguon = (PROJECT_ROOT / "interface" / "noi_bo_api.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "_ghi_kich_ban")
    trong = {id(n) for n in ast.walk(ham)}
    ngoai = [n.lineno for n in ast.walk(cay) if isinstance(n, ast.Constant)
             and n.value == "kich_ban.md" and id(n) not in trong]
    assert not ngoai, f"'kich_ban.md' được ghi ngoài _ghi_kich_ban ở dòng {ngoai}"
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name) and n.func.id == "_ghi_kich_ban"]
    assert len(goi) == 2, f"mong đúng 2 chỗ gọi (dispatch + pipeline), thấy {len(goi)}"


@pytest.fixture
def kho(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DATA_AURA", tmp_path / "aura")
    monkeypatch.setattr(w, "SO_DANG", tmp_path / "dang" / "so_dang.jsonl")

    def them(ten, van, luc, meta=True, sua_sau=False):
        d = tmp_path / "aura" / ten
        api._ghi_kich_ban(d, van, f"đề {ten}", "truyen")
        m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        m["luc"] = luc
        (d / "meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        if not meta:
            (d / "meta.json").unlink()
        if sua_sau:
            (d / "kich_ban.md").write_text(van + " sửa tay.\n", encoding="utf-8")
        return m["sha256"]
    return them


def test_HANG_CHO_bo_ban_da_dang_ban_khong_meta_ban_bi_sua_va_ban_trung(kho):
    da = kho("a", "Truyện A.", "2026-09-14T10:00")
    kho("b", "Truyện B.", "2026-09-14T12:00")
    kho("c", "Truyện C.", "2026-09-14T09:00", meta=False)      # kịch bản cũ, trước vòng 2
    kho("d", "Truyện D.", "2026-09-14T08:00", sua_sau=True)    # sửa sau khi app ghi
    kho("e", "Truyện B.", "2026-09-14T13:00")                  # trùng nội dung với b
    kho("f", "Truyện F.", "2026-09-14T11:00")
    w._ghi_so_dang({"nen_tang": "wattpad", "sha256": da, "trang_thai": "DAT"})
    hang = w._hang_cho("wattpad")
    assert [m["van_ban"] for m in hang] == ["Truyện F.", "Truyện B."], hang
    assert all(m["url_do_dang"] is None for m in hang)
    # Hai bản "Truyện B.": giữ bản CŨ NHẤT (b, 12:00), không phải bản sau (e, 13:00).
    assert hang[1]["thu_muc"].endswith("b") and hang[1]["chu_de"] == "đề b", hang[1]


def test_LAN_HONG_da_mo_chuong_thi_GHI_TIEP_khong_mo_chuong_moi(kho):
    sha = kho("g", "Truyện G.", "2026-09-14T10:00")
    w._ghi_so_dang({"nen_tang": "wattpad", "sha256": sha, "trang_thai": "KHONG_DAT",
                    "url_chuong": "https://www.wattpad.com/myworks/1/write/2"})
    hang = w._hang_cho("wattpad")
    assert len(hang) == 1 and hang[0]["url_do_dang"] == "https://www.wattpad.com/myworks/1/write/2"
    # Nền tảng khác không được mượn sổ của Wattpad.
    assert w._hang_cho("sangtacviet")[0]["url_do_dang"] is None


def test_CHUAN_HOA_chi_gop_khoang_trang_khong_doi_chu():
    assert w._chuan_hoa(" Câu  một.\n\nCâu hai. ") == "Câu một. Câu hai."
    assert w._chuan_hoa("Câu một.") != w._chuan_hoa("Câu mot.")
