# -*- coding: utf-8 -*-
"""test_cua_a_guard.py — Kiểm thử độc lập Cửa A: Khóa chạy mã mặc định & Route Shell.

Yêu cầu Cửa A:
- Khi allow_code_execution=False:
  - /api/chay        -> trả 403 {"trang_thai": "bi_khoa"}, runner count = 0
  - /api/trace       -> trả 403 {"trang_thai": "bi_khoa"}, runner count = 0
  - /api/dinh_vi_loi -> trả 403 {"trang_thai": "bi_khoa"}, runner count = 0
- Không được trả 404.
- Thứ tự kiểm tra: Auth/Origin & Cờ thực thi trước khi parse JSON hay chạm đĩa.
"""
from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch

from interface.the_app import tao_app


@pytest.mark.e1_control
class TestCuaAGuard(AioHTTPTestCase):
    async def get_application(self) -> web.Application:
        # Khởi tạo app với allow_code_execution=False
        return tao_app(allow_code_execution=False, auth_token="a" * 32)

    def get_headers(self) -> dict[str, str]:
        return {
            "X-Auth-Token": "a" * 32,
            "Origin": "http://127.0.0.1:8088",
        }

    @unittest_run_loop
    async def test_cua_a_chay_ma_bi_khoa(self):
        with patch("interface.the_api.chay_ma_python_sandbox", side_effect=RuntimeError("SPY_CHAY_CALLED")) as mock_chay:
            resp = await self.client.post(
                "/api/chay",
                headers=self.get_headers(),
                json={"code": "print('hello')"},
            )
            self.assertEqual(resp.status, 403)
            data = await resp.json()
            self.assertEqual(data.get("trang_thai"), "bi_khoa")
            self.assertEqual(mock_chay.call_count, 0)

    @unittest_run_loop
    async def test_cua_a_trace_bi_khoa(self):
        with patch("interface.the_api.chot_test_can_trace", side_effect=RuntimeError("SPY_TRACE_CALLED")) as mock_trace:
            resp = await self.client.post(
                "/api/trace",
                headers=self.get_headers(),
                json={"tep_nguon": "core/may_tinh.py", "tep_test": "tests/test_may_tinh.py"},
            )
            self.assertEqual(resp.status, 403)
            data = await resp.json()
            self.assertEqual(data.get("trang_thai"), "bi_khoa")
            self.assertEqual(mock_trace.call_count, 0)

    @unittest_run_loop
    async def test_cua_a_dinh_vi_loi_bi_khoa_va_khong_404(self):
        with patch("core.lat_nguoc.chay_e1_dinh_vi", side_effect=RuntimeError("SPY_E1_CALLED")) as mock_e1:
            resp = await self.client.post(
                "/api/dinh_vi_loi",
                headers=self.get_headers(),
                json={
                    "tep_nguon": "core/may_tinh.py",
                    "tep_test": "tests/test_may_tinh.py",
                    "source_sha256": "0" * 64,
                    "test_sha256": "0" * 64,
                },
            )
            self.assertNotEqual(resp.status, 404, "Route /api/dinh_vi_loi phải được đăng ký và không được trả 404")
            self.assertEqual(resp.status, 403)
            data = await resp.json()
            self.assertEqual(data.get("trang_thai"), "bi_khoa")
            self.assertEqual(mock_e1.call_count, 0)

    @unittest_run_loop
    async def test_cua_a_chan_truoc_khi_parse_json(self):
        # Gửi payload hỏng / non-JSON khi cờ tắt -> vẫn phải trả 403 bi_khoa
        resp = await self.client.post(
            "/api/dinh_vi_loi",
            headers=self.get_headers(),
            data=b"INVALID_MALFORMED_JSON",
        )
        self.assertEqual(resp.status, 403)
        data = await resp.json()
        self.assertEqual(data.get("trang_thai"), "bi_khoa")

    @unittest_run_loop
    async def test_status_khai_bao_dung_tat_ca_cong_thuc_thi(self):
        resp = await self.client.get("/api/status")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data.get("code_execution_enabled"), False)
        self.assertEqual(
            data.get("cac_cong_thuc_thi"),
            ["/api/chay", "/api/trace", "/api/dinh_vi_loi"]
        )


@pytest.mark.e1_control
class TestCuaAEnabledWhitelist(AioHTTPTestCase):
    async def get_application(self) -> web.Application:
        return tao_app(allow_code_execution=True, auth_token="b" * 32)

    def get_headers(self) -> dict[str, str]:
        return {
            "X-Auth-Token": "b" * 32,
            "Origin": "http://127.0.0.1:8088",
        }

    @unittest_run_loop
    async def test_trace_tu_choi_tep_chua_mo_trong_phien(self):
        # Khi allow_code_execution=True nhưng tệp chưa mở qua /api/mo_tep
        resp = await self.client.post(
            "/api/trace",
            headers=self.get_headers(),
            json={"tep_nguon": "core/may_tinh.py", "tep_test": "tests/test_may_tinh.py"},
        )
        self.assertEqual(resp.status, 403)
        data = await resp.json()
        self.assertIn("chưa được mở trong phiên", data.get("error", ""))

    @unittest_run_loop
    async def test_tep_test_tu_suy_khi_tep_nguon_da_mo(self):
        # Mở core/dong_ho.py
        await self.client.post(
            "/api/mo_tep",
            headers=self.get_headers(),
            json={"duong_dan": "core/dong_ho.py"},
        )
        # Gọi /api/trace không truyền tep_test -> server tự suy tests/test_dong_ho.py
        resp = await self.client.post(
            "/api/trace",
            headers=self.get_headers(),
            json={"tep_nguon": "core/dong_ho.py"},
        )
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn("trang_thai", data)

    @unittest_run_loop
    async def test_tep_test_ngoai_le_chua_mo_bi_403(self):
        # Mở core/dong_ho.py nhưng truyền tep_test khác quy ước (tests/test_may_tinh.py) chưa mở
        await self.client.post(
            "/api/mo_tep",
            headers=self.get_headers(),
            json={"duong_dan": "core/dong_ho.py"},
        )
        resp = await self.client.post(
            "/api/trace",
            headers=self.get_headers(),
            json={"tep_nguon": "core/dong_ho.py", "tep_test": "tests/test_may_tinh.py"},
        )
        self.assertEqual(resp.status, 403)
        data = await resp.json()
        self.assertIn("Tệp test chưa được mở trong phiên làm việc", data.get("error", ""))

    @unittest_run_loop
    async def test_tep_test_ngoai_le_da_mo_thi_qua_duoc(self):
        # Mở cả core/dong_ho.py và tests/test_may_tinh.py
        await self.client.post(
            "/api/mo_tep",
            headers=self.get_headers(),
            json={"duong_dan": "core/dong_ho.py"},
        )
        await self.client.post(
            "/api/mo_tep",
            headers=self.get_headers(),
            json={"duong_dan": "tests/test_may_tinh.py"},
        )
        resp = await self.client.post(
            "/api/trace",
            headers=self.get_headers(),
            json={"tep_nguon": "core/dong_ho.py", "tep_test": "tests/test_may_tinh.py"},
        )
        self.assertNotEqual(resp.status, 403)

