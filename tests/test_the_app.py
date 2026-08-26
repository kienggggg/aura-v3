# -*- coding: utf-8 -*-
"""test_the_app.py — Kiểm thử bảo mật và API máy chủ Web App Thẻ.

Sử dụng aiohttp.test_utils.AioHTTPTestCase (không cần plugin pytest-aiohttp).
"""
import hashlib
import tempfile
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


class TestLietKeTepDuAnNguoiDung(AioHTTPTestCase):
    """Tệp để NGAY GỐC thư mục dự án phải hiện ra trong hộp "Mở tệp".

    26/08/2026. Trước bản sửa hôm nay, `api_danh_sach_tep` chỉ quét các THƯ MỤC
    CON suy từ `thu_muc_duoc_quet()`. Thư mục bài tập của người mới học thường
    là một nắm tệp `.py` để thẳng ở gốc, không thư mục con nào — nên danh mục
    rỗng và API trả `200` với `tong_so: 0`. Hộp "Mở tệp" trống trơn, không một
    dòng báo lỗi: người dùng tưởng app không đọc được tệp của mình.

    Đo trên bản CÀI trong venv sạch, không phải trong kho: `cd bai_tap_cua_toi`
    rồi `aura-the` -> `tong_so = 0` với 3 tệp nằm sờ sờ ở đó.

    Vì sao 702 test cũ không bắt: tất cả chạy trên CHÍNH kho AURA, nơi danh mục
    là `core`/`interface`/`tests` — ba thư mục có thật và đầy tệp. Đúng họ bệnh
    "test xanh không có nghĩa là app dùng được" (CLAUDE.md §4).
    """

    async def get_application(self) -> web.Application:
        self._tam = tempfile.TemporaryDirectory(prefix="du_an_nguoi_dung_")
        goc = Path(self._tam.name)
        (goc / "bai1.py").write_text("x = 1\n", encoding="utf-8")
        (goc / "ghi_chu.json").write_text("{}\n", encoding="utf-8")
        (goc / "khong_phai_ma.txt").write_text("bo qua\n", encoding="utf-8")
        (goc / "chuong2").mkdir()
        (goc / "chuong2" / "bai3.py").write_text("y = 2\n", encoding="utf-8")
        return the_app.tao_app(project_root=goc)

    async def tearDownAsync(self) -> None:
        self._tam.cleanup()
        await super().tearDownAsync()

    def _headers(self) -> dict:
        return {
            "X-Auth-Token": self.app["aura_config"].auth_token,
            "Origin": "http://127.0.0.1:8088",
        }

    async def test_tep_o_goc_du_an_duoc_liet_ke(self):
        resp = await self.client.request(
            "GET", "/api/tep_tin", headers=self._headers())
        self.assertEqual(resp.status, 200)
        duong_dan = {x["duong_dan"] for x in (await resp.json())["danh_sach"]}
        self.assertIn("bai1.py", duong_dan)
        self.assertIn("ghi_chu.json", duong_dan)
        self.assertIn("chuong2/bai3.py", duong_dan)
        # `.txt` không phải mã — vẫn phải bị bỏ, quét gốc không nới đuôi tệp.
        self.assertNotIn("khong_phai_ma.txt", duong_dan)

    async def test_khong_liet_ke_trung(self):
        """Quét gốc bằng `os.walk` thì `chuong2/bai3.py` hiện HAI lần.

        Bản sửa đầu tiên của em đúng lỗi ấy: gốc đệ quy nuốt lại mọi thư mục
        con. Nay gốc chỉ quét ĐỘ SÂU 0.
        """
        resp = await self.client.request(
            "GET", "/api/tep_tin", headers=self._headers())
        ds = [x["duong_dan"] for x in (await resp.json())["danh_sach"]]
        self.assertEqual(len(ds), len(set(ds)), f"có tệp lặp: {ds}")


class TestKhoAuraKhongDoiHangRao(AioHTTPTestCase):
    """Chạy trên CHÍNH kho AURA thì hàng rào cũ giữ nguyên — `data` vẫn bị chặn.

    Bản sửa 26/08 quét thêm tệp ở gốc dự án. Nếu áp cả cho kho AURA thì
    `apply_audit.py`, `aura_chat.py`, `test_all.py` hiện thêm, và
    `test_danh_sach_tep_thanh_cong_voi_token` đỏ — nó đã đỏ thật một lần. Test
    này chốt rằng phạm vi bản sửa dừng đúng ở dự án của người dùng.
    """

    async def get_application(self) -> web.Application:
        return the_app.tao_app()

    async def test_khong_liet_ke_tep_goc_kho(self):
        resp = await self.client.request("GET", "/api/tep_tin", headers={
            "X-Auth-Token": self.app["aura_config"].auth_token,
            "Origin": "http://127.0.0.1:8088",
        })
        duong_dan = {x["duong_dan"] for x in (await resp.json())["danh_sach"]}
        self.assertNotIn("aura_chat.py", duong_dan)
        self.assertNotIn("apply_audit.py", duong_dan)
        self.assertTrue(all(
            d.startswith(("core/", "interface/", "tests/")) for d in duong_dan))
