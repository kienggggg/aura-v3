# -*- coding: utf-8 -*-
"""Sổ chụp số sao hằng ngày — `tools/so_sao.py` (Sếp duyệt 15/09/2026). Không gọi mạng: `_gh` giả.

Ba điều phải giữ:
1. Hiệu tuần chỉ tính cho repo có mặt ở CẢ hai ngày, và bảng nói ra số repo bị bỏ.
2. Thiếu một trong hai ngày thì KHONG_DO_DUOC — không phải bảng rỗng đội lốt "không ai tăng".
3. Mọi lượt chạy vào sổ lịch, kể cả lượt đã có tệp và lượt lỗi; tệp ngày không bao giờ dở dang.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from tools import so_sao


@pytest.fixture
def kho(tmp_path, monkeypatch):
    monkeypatch.setattr(so_sao, "THU_MUC", tmp_path)
    monkeypatch.setattr(so_sao, "THEO_DOI", tmp_path / "theo_doi.txt")
    monkeypatch.setattr(so_sao, "SO_LICH", tmp_path / "lich.jsonl")
    monkeypatch.setattr(so_sao, "NGHI_GIUA_TIM", 0)
    return tmp_path


def _ghi_ngay(kho, ngay: str, sao: dict) -> None:
    dong = [json.dumps({"meta": {"ngay": ngay}})] + [json.dumps({"repo": r, "sao": s}) for r, s in sao.items()]
    (kho / f"{ngay}.jsonl").write_text("\n".join(dong) + "\n", encoding="utf-8")


def _repo(ten: str, sao: int) -> dict:
    return {"full_name": ten, "stargazers_count": sao, "forks_count": 1, "created_at": "2026-09-01T00:00:00Z",
            "pushed_at": "2026-09-15T00:00:00Z", "license": {"spdx_id": "MIT"}, "language": "Python",
            "description": "x"}


def test_hieu_tuan_chi_tinh_repo_co_ca_hai_ngay(kho):
    _ghi_ngay(kho, "2026-09-08", {"a/a": 100, "b/b": 50, "c/c": 10})
    _ghi_ngay(kho, "2026-09-15", {"a/a": 130, "b/b": 250, "d/d": 999})
    b = so_sao.bang(date(2026, 9, 15))
    assert b["trang_thai"] == "XONG"
    assert [(d["repo"], d["tang"]) for d in b["top"]] == [("b/b", 200), ("a/a", 30)]
    assert b["so_repo_chung"] == 2 and b["bo_vi_moi_vao"] == 1   # d/d mới vào: nói ra, không lặng lẽ


def test_thieu_mot_ngay_la_KHONG_DO_DUOC(kho):
    _ghi_ngay(kho, "2026-09-15", {"a/a": 130})
    b = so_sao.bang(date(2026, 9, 15))
    assert b["trang_thai"] == "KHONG_DO_DUOC" and "2026-09-08" in b["vi_sao"]


def test_chup_ghi_tep_roi_lan_hai_bo_qua_va_lich_du_hai_dong(kho, monkeypatch):
    goi = []

    def gia(duong):
        goi.append(duong)
        if duong.startswith("repos/"):
            return _repo(duong[6:], 7)
        return {"total_count": 2, "incomplete_results": False, "items": [_repo("x/moi", 120), _repo("y/moi", 101)]}

    monkeypatch.setattr(so_sao, "_gh", gia)
    kq = so_sao.chup(date(2026, 9, 15))
    assert kq["trang_thai"] == "XONG"
    dong = (kho / "2026-09-15.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(dong[0])["meta"]["so_repo"] == len(dong) - 1
    assert {"x/moi", "y/moi"} <= {json.loads(x)["repo"] for x in dong[1:]}
    so_goi = len(goi)
    assert so_sao.chup(date(2026, 9, 15))["trang_thai"] == "DA_CO"
    assert len(goi) == so_goi, "lượt thứ hai không được gọi mạng lại"
    lich = [json.loads(x)["trang_thai"] for x in (kho / "lich.jsonl").read_text(encoding="utf-8").splitlines()]
    assert lich == ["XONG", "DA_CO"]


def test_chup_loi_van_vao_lich_va_khong_de_tep_do_dang(kho, monkeypatch):
    def hong(duong):
        if duong.startswith("search/"):
            raise RuntimeError("mat mang")
        return _repo(duong[6:], 7)

    monkeypatch.setattr(so_sao, "_gh", hong)
    assert so_sao.chup(date(2026, 9, 15))["trang_thai"] == "LOI"
    assert not (kho / "2026-09-15.jsonl").exists(), "lượt lỗi không được để lại tệp mang tên ngày"
    assert json.loads((kho / "lich.jsonl").read_text(encoding="utf-8"))["trang_thai"] == "LOI"
