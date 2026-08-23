# -*- coding: utf-8 -*-
"""test_the_app.py — Kiểm thử bảo mật và API máy chủ Web App Thẻ.

Sử dụng aiohttp.test_utils.AioHTTPTestCase (không cần plugin pytest-aiohttp).
"""
import hashlib
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from interface import the_api, the_app


class TestTheAppAPI(AioHTTPTestCase):
    async def get_application(self) -> web.Application:
        return the_app.tao_app()

    def get_auth_headers(self) -> dict:
        return {
            "X-Auth-Token": self.app["aura_config"].auth_token,
            "Origin": "http://127.0.0.1:8088",
        }

    async def test_status_endpoint(self):
        resp = await self.client.request("GET", "/api/status")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data.get("app"), "AURA_THE_v1")
        self.assertEqual(data.get("status"), "ready")

    async def test_danh_sach_tep_tu_choi_khi_thieu_token(self):
        resp = await self.client.request("GET", "/api/tep_tin")
        self.assertEqual(resp.status, 403)

    async def test_danh_sach_tep_tu_choi_origin_la(self):
        headers = {
            "X-Auth-Token": self.app["aura_config"].auth_token,
            "Origin": "http://evil-site.com",
        }
        resp = await self.client.request("GET", "/api/tep_tin", headers=headers)
        self.assertEqual(resp.status, 403)

    async def test_danh_sach_tep_thanh_cong_voi_token(self):
        resp = await self.client.request("GET", "/api/tep_tin", headers=self.get_auth_headers())
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn("danh_sach", data)
        self.assertGreater(data.get("tong_so", 0), 0)
        danh_sach = data["danh_sach"]
        # Kiểm tra mọi tệp đều thuộc core, interface hoặc tests
        for item in danh_sach:
            duong_dan = item["duong_dan"]
            self.assertTrue(
                duong_dan.startswith("core/")
                or duong_dan.startswith("interface/")
                or duong_dan.startswith("tests/"),
                f"Tệp không thuộc danh mục whitelist: {duong_dan}"
            )
            self.assertTrue(item["duoi_tep"] in (".py", ".json"))

    async def test_danh_sach_tep_chan_traversal_va_ngoai_kho(self):
        # 1. Chặn ..
        resp = await self.client.request(
            "GET", "/api/tep_tin?thu_muc=../", headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 400)

        # 2. Chặn đường dẫn tuyệt đối
        resp = await self.client.request(
            "GET", "/api/tep_tin?thu_muc=C:/Windows", headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 400)

        # 3. Chặn thư mục ngoài whitelist ALLOWED_SCAN_DIRS (ví dụ data/)
        resp = await self.client.request(
            "GET", "/api/tep_tin?thu_muc=data", headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 403)

    async def test_danh_sach_tep_loc_theo_thu_muc_hop_le(self):
        resp = await self.client.request(
            "GET", "/api/tep_tin?thu_muc=core", headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        for item in data["danh_sach"]:
            self.assertTrue(item["duong_dan"].startswith("core/"))

    async def test_mo_tep_chan_traversal(self):
        payload = {"duong_dan": "../CLAUDE.md"}
        resp = await self.client.request(
            "POST", "/api/mo_tep", json=payload, headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 400)

    async def test_mo_tep_py_hop_le(self):
        payload = {"duong_dan": "core/dong_ho.py"}
        resp = await self.client.request(
            "POST", "/api/mo_tep", json=payload, headers=self.get_auth_headers()
        )
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data.get("ten_tep"), "dong_ho.py")
        self.assertIn("tree", data)
        self.assertIn("sha256", data)
        self.assertEqual(len(data["sha256"]), 64)
