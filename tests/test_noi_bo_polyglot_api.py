# -*- coding: utf-8 -*-
"""test_noi_bo_polyglot_api.py — Kiểm thử API Polyglot và Custom Pipeline cho App Nội Bộ."""
from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from interface.noi_bo_app import build_noi_bo_app


class TestNoiBoPolyglotAPI(AioHTTPTestCase):
    async def get_application(self) -> web.Application:
        return build_noi_bo_app()

    async def test_api_polyglot_languages(self):
        """API /api/polyglot/languages phải trả về 8 ngôn ngữ."""
        resp = await self.client.get("/api/polyglot/languages")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert len(data["languages"]) == 8

    async def test_api_polyglot_translate(self):
        """API /api/polyglot/translate dịch code Python sang JS."""
        payload = {
            "ma": "def foo(): return 42",
            "lang_nguon": "python",
            "lang_dich": "javascript"
        }
        resp = await self.client.post("/api/polyglot/translate", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert "function foo()" in data["ma_dich"]

    async def test_api_polyglot_validate(self):
        """API /api/polyglot/validate kiểm tra cú pháp."""
        payload = {
            "ma": "def valid_func(): pass",
            "lang": "python"
        }
        resp = await self.client.post("/api/polyglot/validate", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["valid"] is True

    async def test_api_polyglot_run_CHAN_khi_khong_co_ma_thong_hanh(self):
        """Không mã thông hành thì 403, và mã KHÔNG chạy.

        Bản trước 04/09/2026 của bài này tên là `test_api_polyglot_run` và chú
        thích ghi *"thực thi mã trong sandbox"*. Không có hộp cát nào cả — đo
        được cùng ngày: một POST không mang gì cả ghi được tệp ra ngoài thư mục
        tạm và đọc được `HOME`. Đúng ba chữ `CLAUDE.md` mục 7 luật 3 cảnh báo:
        *"'Cô lập', 'sandbox', 'không có quyền' — người đọc sẽ TIN"*.
        """
        import interface.noi_bo_api as api

        goc = api.DIA_CHI_BIND
        api.DIA_CHI_BIND = "127.0.0.1"
        try:
            resp = await self.client.post("/api/polyglot/run", json={
                "ma": "print('KHONG_DUOC_CHAY')", "lang": "python", "timeout_s": 3.0})
            assert resp.status == 403, resp.status
            data = await resp.json()
            assert data["status"] == "BLOCKED", data
            assert "KHONG_DUOC_CHAY" not in str(data), "mã đã chạy dù bị chặn"
        finally:
            api.DIA_CHI_BIND = goc

    async def test_api_polyglot_run_CHAY_khi_du_bon_lop(self):
        """Ca đối chứng: đủ bốn lớp thì mã THẬT SỰ chạy.

        Thiếu bài này thì bài trên xanh được bằng cách chặn tất cả — và một cổng
        chặn tất cả thì chưa chứng minh được nó chặn đúng người.
        """
        import os

        import interface.noi_bo_api as api

        goc_bind, goc_co = api.DIA_CHI_BIND, os.environ.get(api.BIEN_BAT_CHAY_MA)
        api.DIA_CHI_BIND = "127.0.0.1"
        os.environ[api.BIEN_BAT_CHAY_MA] = "1"
        try:
            resp = await self.client.post(
                "/api/polyglot/run",
                json={"ma": "print('TEST_PASS_123')", "lang": "python", "timeout_s": 3.0},
                headers={api.HEADER_MA_THONG_HANH: api.MA_THONG_HANH})
            assert resp.status == 200, resp.status
            data = await resp.json()
            assert data["status"] == "PASS", data
            assert "TEST_PASS_123" in data["stdout"]
        finally:
            api.DIA_CHI_BIND = goc_bind
            if goc_co is None:
                os.environ.pop(api.BIEN_BAT_CHAY_MA, None)
            else:
                os.environ[api.BIEN_BAT_CHAY_MA] = goc_co

    async def test_api_pipeline_presets_du_8_cards(self):
        """API /api/pipeline/presets phải trả về 8 presets."""
        resp = await self.client.get("/api/pipeline/presets")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert len(data["presets"]) == 8

    async def test_api_pipeline_custom(self):
        """API /api/pipeline/custom thực thi pipeline tùy biến."""
        payload = {
            "ten": "Pipeline Tùy Biến Thử Nghiệm",
            "cac_buoc": [
                {"phong_id": "zeta", "hanh_dong": "Thu thập dữ liệu"},
                {"phong_id": "delta", "hanh_dong": "Khám mã nguồn"}
            ]
        }
        resp = await self.client.post("/api/pipeline/custom", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert data["tong_buoc"] == 2
