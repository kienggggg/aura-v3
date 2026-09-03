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
    async def test_api_dieu_phoi_khong_duoc_bao_PASS_khi_khong_lam_gi(self):
        """`/api/dispatch` phải fail-closed.

        BÀI NÀY TRƯỚC 02/09/2026 LÀM NGƯỢC LẠI. Nó khẳng định
        ``data["status"] == "PASS"`` cho cả bảy phòng — tức là một bài test
        **bắt buộc** đường ấy phải báo đỗ, trong khi đo được là cả bảy chỉ in ra
        một đoạn văn viết sẵn và để lại **0 byte** trên đĩa, 8 tệp được khai là
        đã tạo thì **0 tệp có thật**.

        Test xanh không có nghĩa app dùng được; ở đây nó còn tệ hơn — test xanh
        đang KHOÁ CHẶT cái giả, nên mọi lần sửa cho thật đều làm nó đỏ.
        """
        for phong_id in ["aura", "alpha", "beta", "delta", "gamma", "omega", "zeta"]:
            payload = {
                "phong_id": phong_id,
                "prompt": f"Thực thi tác vụ kiểm thử cho phòng {phong_id}"
            }
            resp = await self.client.post("/api/dispatch", json=payload)
            assert resp.status == 200
            data = await resp.json()
            assert "task_id" in data
            assert data["tra_loi"]
            # BA trạng thái, không phải hai. `FAIL` xuất hiện từ 02/09 chiều khi
            # Alpha bắt đầu tự chấm bằng verifier riêng: nó CHẠY được, để lại 6
            # hiện vật thật, nhưng video ra là slideshow nên verifier bác.
            #
            #   PASS             để lại byte, và không phòng nào tự bác
            #   FAIL             chạy được, có hiện vật, nhưng verifier bác
            #   KHONG_CHAY_DUOC  không để lại byte nào
            #
            # Gộp `FAIL` vào `KHONG_CHAY_DUOC` là mất phân biệt giữa "chưa làm"
            # và "làm rồi nhưng chưa đủ hay" — đúng lỗi mà cả tệp này sinh ra
            # để chống.
            assert data["status"] in ("PASS", "FAIL", "KHONG_CHAY_DUOC"), data["status"]
            # Hai trường này phải có LUÔN LUÔN, không chỉ ở nhánh đỗ. Gieo thử
            # bắt được bản đầu: bỏ hẳn chúng khỏi phản hồi mà cửa vẫn xanh, vì
            # phép kiểm nằm bên trong `if status == "PASS"` — nhánh không chạy.
            assert "bang_chung" in data and "artifacts_thieu" in data, data
            if data["status"] == "PASS":
                # Đỗ thì phải chỉ ra được BẰNG CHỨNG, không được đỗ suông.
                assert data["bang_chung"] or not data["artifacts_thieu"], data
            elif data["status"] == "FAIL":
                # Rớt thì phải có hiện vật để soi, và phải nói RỚT VÌ SAO.
                assert data["artifacts"], "FAIL mà không để lại gì để soi"
                assert data["bang_chung"], "FAIL mà không có byte nào trên đĩa"
                assert not data["artifacts_thieu"], data["artifacts_thieu"]
            else:
                # Chưa chạy thì câu trả lời phải NÓI RA, không để người đọc tự suy.
                assert "KHÔNG CHẠY ĐƯỢC" in data["tra_loi"], data["tra_loi"][:120]

    @unittest_run_loop
    async def test_so_cai_KHONG_duoc_tinh_la_bang_chung(self):
        """Hàm dispatch ghi `so_cai.jsonl` cho MỌI phòng, kể cả phòng không làm
        gì. Tính nó vào bằng chứng thì phòng nào cũng đỗ — phép đo mất sạch
        nghĩa.

        Đo bằng HÀNH VI: chạm vào sổ cái rồi chụp lại, hiệu phải RỖNG. Bản đầu
        của cửa này chỉ dò chuỗi trong mã và bị gieo lỗi qua mặt.
        """
        from interface.noi_bo_api import (OMEGA_SO_CAI, _anh_chup_bang_chung,
                                          _bang_chung_moi)

        truoc = _anh_chup_bang_chung()
        OMEGA_SO_CAI.parent.mkdir(parents=True, exist_ok=True)
        with open(OMEGA_SO_CAI, "a", encoding="utf-8") as f:
            f.write('{"cham_vao_so_cai": true}\n')
        assert _bang_chung_moi(truoc, _anh_chup_bang_chung()) == [], (
            "sổ cái đang được tính là bằng chứng — mọi phòng sẽ đỗ suông"
        )

    @unittest_run_loop
    async def test_so_cai_ghi_DUNG_trang_thai_cua_luot_ay(self):
        """Sổ phải chép lại trạng thái THẬT của lượt, không phải một chữ cố định."""
        import json

        from interface.noi_bo_api import OMEGA_SO_CAI

        resp = await self.client.post(
            "/api/dispatch", json={"phong_id": "delta", "prompt": "doi chieu so cai"})
        data = await resp.json()
        dong = [json.loads(d) for d in
                OMEGA_SO_CAI.read_text(encoding="utf-8").strip().split("\n")
                if d.strip().startswith("{")]
        khop = [d for d in dong if d.get("task_id") == data["task_id"]]
        assert khop, "lượt vừa chạy không vào sổ"
        assert khop[-1]["status"] == data["status"], (
            f"sổ ghi {khop[-1]['status']!r} nhưng lượt ấy trả về "
            f"{data['status']!r} — sổ đang chép một chữ cố định"
        )

    @unittest_run_loop
    async def test_so_cai_ghi_dung_trang_thai_that(self):
        """Sổ cái từng ghi ``"status": "PASS"`` cho MỌI lượt, kể cả lượt không
        làm gì. Sổ mà chỉ biết một chữ thì đọc lại không nói được điều gì."""
        import json

        from interface.noi_bo_api import OMEGA_SO_CAI

        await self.client.post("/api/dispatch",
                               json={"phong_id": "gamma", "prompt": "kiem tra so cai"})
        dong = [json.loads(d) for d in
                OMEGA_SO_CAI.read_text(encoding="utf-8").strip().split("\n") if d.strip()]
        cuoi = dong[-1]
        assert cuoi["phong_id"] == "gamma"
        assert cuoi["status"] in ("PASS", "KHONG_CHAY_DUOC")
        assert "bang_chung" in cuoi and "artifacts_thieu" in cuoi

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
        """API /api/pipeline/presets phải trả về 8 thẻ quy trình thông minh."""
        resp = await self.client.get("/api/pipeline/presets")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "PASS"
        assert len(data["presets"]) == 8
        ids = {p["id"] for p in data["presets"]}
        ky_vong = {
            "card_video_shorts", "card_code_doctor", "card_polyglot_transpiler",
            "card_deep_scout", "card_novel_writer", "card_fullstack_builder",
            "card_security_guard", "card_system_audit"
        }
        assert ids == ky_vong
