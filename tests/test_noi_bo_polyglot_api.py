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

    async def test_api_polyglot_run(self):
        """API /api/polyglot/run thực thi mã trong sandbox."""
        payload = {
            "ma": "print('TEST_PASS_123')",
            "lang": "python",
            "timeout_s": 3.0
        }
        resp = await self.client.post("/api/polyglot/run", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert "TEST_PASS_123" in data["stdout"]

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
