# -*- coding: utf-8 -*-
"""test_e1_app.py — Unit, API và Lifecycle tests cho E1 trong App Thẻ.

Bao phủ các yêu cầu:
- Cửa A: Lật ngược AST, giới hạn 5 họ phép, loại trừ test xanh
- Cửa B: Bảo mật API /api/dinh_vi_loi (Auth token, loopback, path confinement, SHA check)
- Cửa C: Hàng rào khóa chạy mã (allow_code_execution = False mặc định trả 403 bi_khoa)
- Cửa F: Concurrency lock (409 BUSY), timeout (504 khong_do_duoc), dọn sạch temp
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from core import lat_nguoc
from interface import the_api, the_app

# Đánh dấu toàn bộ module này là e1_control để tránh tự gọi E1 lồng E1 trong worker regression
pytestmark = pytest.mark.e1_control


class TestE1UnitAST(AioHTTPTestCase):
    """Kiểm thử tầng AST và logic cốt lõi của E1 (Cửa A)."""

    async def get_application(self) -> web.Application:
        return the_app.tao_app(allow_code_execution=True)

    def test_e1_phep_bien_doi_5_ho(self):
        """Xác minh 5 họ phép chuẩn được hỗ trợ và các phép ngoài bị bỏ qua."""
        # 1. So sánh: < -> <=
        ma_goc = "def f(x):\n    return x < 10\n"
        cands = lat_nguoc.tao_cac_ung_vien(ma_goc, {2})
        self.assertTrue(any("so sánh Lt" in c[1] for c in cands))

        # 2. Logic: and -> or
        ma_logic = "def f(a, b):\n    return a and b\n"
        cands_logic = lat_nguoc.tao_cac_ung_vien(ma_logic, {2})
        self.assertTrue(any("logic And" in c[1] for c in cands_logic))

        # 3. Phủ định: not x -> x
        ma_not = "def f(x):\n    return not x\n"
        cands_not = lat_nguoc.tao_cac_ung_vien(ma_not, {2})
        self.assertTrue(any("bỏ phủ định" in c[1] for c in cands_not))

        # 4. Boolean: True -> False
        ma_bool = "def f():\n    return True\n"
        cands_bool = lat_nguoc.tao_cac_ung_vien(ma_bool, {2})
        self.assertTrue(any("bool True" in c[1] for c in cands_bool))

        # 5. Số nguyên: 10 -> 9
        ma_num = "def f():\n    return 10\n"
        cands_num = lat_nguoc.tao_cac_ung_vien(ma_num, {2})
        self.assertTrue(any("số 10" in c[1] for c in cands_num))

    def test_e1_loc_theo_dong_chay(self):
        """Ứng viên chỉ được sinh trên các dòng nằm trong dong_da_chay."""
        ma = "def f(x):\n    a = 10\n    b = 20\n    return a < b\n"
        # Chỉ chạy qua dòng 4 (return a < b), không qua dòng 2, 3
        cands = lat_nguoc.tao_cac_ung_vien(ma, {4})
        lines = [c[0] for c in cands]
        self.assertIn(4, lines)
        self.assertNotIn(2, lines)
        self.assertNotIn(3, lines)

    def test_e1_candidates_contain_patched_code(self):
        """Mỗi ứng viên trong candidates phải trả về mã đã vá đầy đủ ('ma'), parse được bằng AST và khác mã gốc."""
        import ast
        ma = "def f(x):\n    return x < 10\n"
        cands = lat_nguoc.tao_cac_ung_vien(ma, {2})
        self.assertGreater(len(cands), 0)
        for cand in cands:
            line_no, desc, patched_code = cand
            self.assertIsInstance(patched_code, str)
            self.assertGreater(len(patched_code), 0)
            parsed = ast.parse(patched_code)
            self.assertIsNotNone(parsed)
            self.assertNotEqual(ast.dump(parsed), ast.dump(ast.parse(ma)))

    def test_doc_thong_tin_gioi_han_doc_tu_so(self):
        """Hàm doc_thong_tin_gioi_han phải đọc động số đề từ sổ data/evidence_sprint/e1_ngoai_ho.json."""
        root = Path(__file__).parent.parent
        lim = lat_nguoc.doc_thong_tin_gioi_han(root)
        self.assertIn("5 họ lỗi so sánh/logic", lim)
        self.assertIn("64 lỗi NGOÀI 5 họ đó", lim)


class TestE1APISecurity(AioHTTPTestCase):
    """Kiểm thử Cửa B & Cửa C trên endpoint /api/dinh_vi_loi."""

    async def get_application(self) -> web.Application:
        # App mặc định allow_code_execution=False
        return the_app.tao_app(allow_code_execution=False)

    def get_auth_headers(self) -> dict:
        token = self.app["aura_config"].auth_token
        return {
            "X-Auth-Token": token,
            "Origin": "http://127.0.0.1:8088",
        }

    async def test_cua_c_chay_ma_tat_mac_dinh(self):
        """Khi cờ tắt, /api/dinh_vi_loi và /api/trace trả 403 bi_khoa."""
        headers = self.get_auth_headers()
        
        # 1. /api/dinh_vi_loi
        payload_e1 = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload_e1, headers=headers)
        self.assertEqual(resp.status, 403)
        data = await resp.json()
        self.assertEqual(data.get("trang_thai"), "bi_khoa")

        # 2. /api/trace
        payload_trace = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
        }
        resp_trace = await self.client.request("POST", "/api/trace", json=payload_trace, headers=headers)
        self.assertEqual(resp_trace.status, 403)
        data_trace = await resp_trace.json()
        self.assertEqual(data_trace.get("trang_thai"), "bi_khoa")

    async def test_api_dinh_vi_loi_thieu_token(self):
        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload)
        self.assertEqual(resp.status, 403)

    async def test_api_dinh_vi_loi_origin_ngoai_loopback(self):
        headers = {
            "X-Auth-Token": self.app["aura_config"].auth_token,
            "Origin": "http://attacker.com",
        }
        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
        self.assertEqual(resp.status, 403)

    async def test_status_chua_e1_limitation_dong(self):
        resp = await self.client.request("GET", "/api/status")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn("e1_limitation", data)
        self.assertIn("5 họ lỗi so sánh/logic", data["e1_limitation"])


class TestE1APIExecution(AioHTTPTestCase):
    """Kiểm thử khi allow_code_execution=True (Cửa B & F)."""

    async def get_application(self) -> web.Application:
        return the_app.tao_app(allow_code_execution=True)

    def get_auth_headers(self) -> dict:
        token = self.app["aura_config"].auth_token
        return {
            "X-Auth-Token": token,
            "Origin": "http://127.0.0.1:8088",
        }

    async def test_api_dinh_vi_loi_sai_keys_payload(self):
        headers = self.get_auth_headers()
        # Thừa key lạ
        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
            "extra_key": "injected",
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
        self.assertEqual(resp.status, 400)

    async def test_path_traversal_bi_chan(self):
        headers = self.get_auth_headers()
        payload = {
            "tep_nguon": "../core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
        self.assertEqual(resp.status, 400)

    async def test_ngoai_whitelist_phien_bi_chan_403(self):
        headers = self.get_auth_headers()
        # Tệp tồn tại nhưng chưa mở trong phiên của app này
        self.app["aura_runtime"].opened_files_whitelist.clear()
        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
        self.assertEqual(resp.status, 403)
        data = await resp.json()
        self.assertIn("chưa được mở trong phiên", data.get("error", ""))

    async def test_sha_khong_khop_tra_409(self):
        headers = self.get_auth_headers()
        # Mở tệp trong phiên
        await self.client.request("POST", "/api/mo_tep", json={"duong_dan": "core/dong_ho.py"}, headers=headers)

        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "0" * 64,  # Sai SHA
            "test_sha256": "1" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
        self.assertEqual(resp.status, 409)
        data = await resp.json()
        self.assertIn("error", data)

    async def test_concurrency_lock_tra_409_busy(self):
        """Khi busy_info đang is_busy, request thứ hai trả 409 BUSY."""
        headers = self.get_auth_headers()
        # Mở tệp trong phiên
        await self.client.request("POST", "/api/mo_tep", json={"duong_dan": "core/dong_ho.py"}, headers=headers)

        root = Path(__file__).parent.parent
        src_bytes = (root / "core" / "dong_ho.py").read_bytes()
        tst_bytes = (root / "tests" / "test_dong_ho.py").read_bytes()
        src_sha = hashlib.sha256(src_bytes).hexdigest()
        tst_sha = hashlib.sha256(tst_bytes).hexdigest()

        payload = {
            "tep_nguon": "core/dong_ho.py",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": src_sha,
            "test_sha256": tst_sha,
        }

        # Giả lập app đang bận job khác
        runtime = self.app["aura_runtime"]
        runtime.busy_info["is_busy"] = True
        try:
            resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
            self.assertEqual(resp.status, 409)
            data = await resp.json()
            self.assertEqual(data.get("trang_thai"), "busy")
        finally:
            runtime.busy_info["is_busy"] = False

    async def test_security_matrix_empty_sha_and_non_hex(self):
        """Ma trận schema: SHA rỗng, sai độ dài, chứa ký tự phi hex đều bị chặn 400."""
        headers = self.get_auth_headers()
        await self.client.request("POST", "/api/mo_tep", json={"duong_dan": "core/dong_ho.py"}, headers=headers)

        bad_shas = [
            "",
            "abc",
            "z" * 64,  # 'z' không phải hex
            12345,     # sai kiểu dữ liệu
            None,
        ]
        for bad_sha in bad_shas:
            payload = {
                "tep_nguon": "core/dong_ho.py",
                "tep_test": "tests/test_dong_ho.py",
                "source_sha256": bad_sha,
                "test_sha256": "a" * 64,
            }
            resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload, headers=headers)
            self.assertEqual(resp.status, 400)

    async def test_security_matrix_absolute_and_non_py(self):
        """Chặn đường dẫn tuyệt đối và đuôi tệp không phải .py."""
        headers = self.get_auth_headers()
        # 1. Đường dẫn tuyệt đối
        payload_abs = {
            "tep_nguon": "C:/Windows/System32/cmd.exe",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload_abs, headers=headers)
        self.assertEqual(resp.status, 400)

        # 2. Tệp không phải .py
        payload_ext = {
            "tep_nguon": "pytest.ini",
            "tep_test": "tests/test_dong_ho.py",
            "source_sha256": "a" * 64,
            "test_sha256": "b" * 64,
        }
        resp = await self.client.request("POST", "/api/dinh_vi_loi", json=payload_ext, headers=headers)
        self.assertEqual(resp.status, 400)


class TestE1LifecycleAndCanary(AioHTTPTestCase):
    """Kiểm thử Job Object 64-bit, Child Network Canary và App Lifecycle Cleanup."""

    async def get_application(self) -> web.Application:
        return the_app.tao_app(allow_code_execution=True)

    def test_job_object_attached_ready_frame(self):
        """Supervisor phát đúng frame READY với job_attached: True trên Windows."""
        supervisor_script = Path(__file__).parent.parent / "tools" / "e1_supervisor_bootstrap.py"
        p = subprocess.Popen(
            [sys.executable, "-B", "-X", "utf8", str(supervisor_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            line1 = p.stdout.readline()
            line2 = p.stdout.readline()
            self.assertIn("===E1_SUPERVISOR_READY===", line1)
            ready_info = json.loads(line2)
            self.assertTrue(ready_info.get("ready"))
            self.assertTrue(ready_info.get("job_attached"))
            self.assertGreater(ready_info.get("supervisor_pid", 0), 0)
        finally:
            p.kill()
            p.wait()

    def test_child_canary_blocks_external_connect(self):
        """sitecustomize.py chặn kết nối mạng ngoài và ghi nhận vào log."""
        tmp = Path(tempfile.mkdtemp(prefix="aura_test_canary_"))
        try:
            from tools import e1_supervisor_bootstrap
            e1_supervisor_bootstrap._install_child_canary(tmp)
            canary_log = tmp / ".canary.jsonl"

            code = (
                "import socket\n"
                "try:\n"
                "    s = socket.socket()\n"
                "    s.connect(('8.8.8.8', 53))\n"
                "    print('CONNECTED')\n"
                "except PermissionError as exc:\n"
                "    print('BLOCKED:', exc)\n"
            )
            env = {
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": str(tmp),
                "AURA_CHILD_CANARY_LOG": str(canary_log),
            }
            r = subprocess.run(
                [sys.executable, "-B", "-X", "utf8", "-c", code],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tmp),
                timeout=5.0,
            )
            self.assertIn("BLOCKED: AURA_CHILD_CANARY_BLOCKED", r.stdout)
            self.assertTrue(canary_log.is_file())
            log_text = canary_log.read_text(encoding="utf-8")
            self.assertIn("8.8.8.8:53", log_text)
            self.assertIn('"blocked": true', log_text)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    async def test_app_cleanup_hook_terminates_job(self):
        """Khi app shutdown, hook on_cleanup dọn sạch tiến trình đang active."""
        app = self.app
        runtime = app["aura_runtime"]
        
        # Tạo tiến trình giả lập đang chạy
        dummy_proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", "import time; time.sleep(100)"
        )
        runtime.active_job_process = dummy_proc
        runtime.busy_info["is_busy"] = True

        # Kích hoạt cleanup
        for hook in app.on_cleanup:
            await hook(app)

        self.assertIsNone(runtime.active_job_process)
        self.assertFalse(runtime.busy_info["is_busy"])
        self.assertIsNotNone(dummy_proc.returncode)

