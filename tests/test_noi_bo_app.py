# -*- coding: utf-8 -*-
"""test_noi_bo_app.py — Kiểm thử độc lập toàn diện cho App Nội Bộ 7 Đặc Nhiệm AURA v3."""
from __future__ import annotations

import json
import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from interface.noi_bo_app import build_noi_bo_app
from interface.noi_bo_api import DANH_MUC_PHONG


class TestNoiBoApp(AioHTTPTestCase):
    async def get_application(self) -> web.Application:
        return build_noi_bo_app()

    @unittest_run_loop
    async def test_trang_chu_html(self):
        """Trang chủ / phải trả về mã 200 và chứa tiêu đề AURA COMMAND CENTER."""
        resp = await self.client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "AURA COMMAND CENTER" in text
        assert "7 Đặc Nhiệm" in text

    @unittest_run_loop
    async def test_api_status_va_vitals(self):
        """API /api/status phải trả về 7 phòng và thông số vitals."""
        resp = await self.client.get("/api/status")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert len(data["rooms"]) == 7
        assert "vitals" in data
        assert "ram_used_gb" in data["vitals"]
        assert "cpu_percent" in data["vitals"]

    @unittest_run_loop
    async def test_api_danh_sach_phong(self):
        """API /api/rooms phải liệt kê đầy đủ 7 mã định danh: aura, alpha, beta, delta, gamma, omega, zeta."""
        resp = await self.client.get("/api/rooms")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        ids = {r["id"] for r in data["rooms"]}
        assert ids == {"aura", "alpha", "beta", "delta", "gamma", "omega", "zeta"}

    @unittest_run_loop
    async def test_api_dieu_phoi_nhiem_vu_tung_phong(self):
        """API /api/dispatch phải xử lý thành công yêu cầu cho từng phòng ban."""
        for phong_id in ["aura", "alpha", "beta", "delta", "gamma", "omega", "zeta"]:
            payload = {
                "phong_id": phong_id,
                "prompt": f"Thực thi tác vụ kiểm thử cho phòng {phong_id}"
            }
            resp = await self.client.post("/api/dispatch", json=payload)
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "PASS"
            assert "task_id" in data
            assert "tra_loi" in data
            assert len(data["tra_loi"]) > 0

    @unittest_run_loop
    async def test_api_chay_pipeline_lien_phong(self):
        """API /api/pipeline/run phải kích hoạt chuỗi 5 bước phối hợp liên phòng ban."""
        payload = {"chu_de": "Tạo kịch bản và video demo tự động"}
        resp = await self.client.post("/api/pipeline/run", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert data["tong_buoc"] == 5
        assert len(data["cac_buoc"]) == 5

    @unittest_run_loop
    async def test_api_doc_so_cai_va_evidence(self):
        """API /api/ledger và /api/evidence phải trả về dữ liệu danh sách hợp lệ."""
        resp_l = await self.client.get("/api/ledger")
        assert resp_l.status == 200
        data_l = await resp_l.json()
        assert data_l["status"] == "PASS"
        assert "entries" in data_l

        resp_e = await self.client.get("/api/evidence")
        assert resp_e.status == 200
        data_e = await resp_e.json()
        assert data_e["status"] == "PASS"
        assert "runs" in data_e

    @unittest_run_loop
    async def test_api_danh_sach_the_quy_trinh(self):
        """API /api/pipeline/presets phải trả về 4 thẻ quy trình thông minh."""
        resp = await self.client.get("/api/pipeline/presets")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert len(data["presets"]) == 4
        ids = {p["id"] for p in data["presets"]}
        assert ids == {"card_video_shorts", "card_code_doctor", "card_novel_writer", "card_system_audit"}
