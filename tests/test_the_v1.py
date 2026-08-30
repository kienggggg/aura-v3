# -*- coding: utf-8 -*-
"""test_the_v1.py — Bộ kiểm thử nghiêm ngặt theo đúng kỷ luật AURA v3.

Bao gồm:
1. CỬA CỨNG 1: Mở - Lưu không đổi 1 byte trên toàn bộ ~40 file .py của kho (SHA-256 match 100%).
2. CỬA CỨNG 2: Sửa 1 ô -> Giữ nguyên chú thích cuối dòng (cắt bằng end_col_offset, không bị lừa bởi # trong chuỗi) và giữ nguyên các dòng khác.
3. Test thẻ `ma_tho` cho các cấu trúc phức tạp.
4. Test sinh mã Python chuẩn cho 10 thẻ.
5. Test 5 LỖI ĐỎ và 4 CẢNH BÁO VÀNG.
6. Test Sandbox thực thi (timeout 5s, bắt stdout/stderr, tiến trình con).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from core.the_v1 import (
    BO_THE_V1,
    TheNode,
    chay_ma_tien_trinh_rieng,
    kiem_tra_cay_the,
    sinh_dong_the_don,
    sinh_ma_python,
)
from core.the_cst import (
    doc_chuoi_py_sang_cay_the,
    doc_tep_py_sang_cay_the,
    luu_cay_the_ra_tep_py,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# CỬA CỨNG 1: MỞ — LƯU — KHÔNG ĐỔI MỘT BYTE (SHA-256 TRÊN TOÀN BỘ FILE .PY)
# ==============================================================================

def test_cua_cung_1_mo_luu_lossless_toan_bo_kho_ma():
    """Mở mọi tệp .py trong core/, interface/, tools/, tests/, ép đi qua bộ sinh mã -> Lưu lại.
    Tệp lưu ra phải GIỐNG HỆT TỪNG BYTE (SHA-256 khớp 100%).
    """
    py_files: list[Path] = []
    for d in ("core", "interface", "tools", "tests"):
        target_dir = PROJECT_ROOT / d
        if target_dir.is_dir():
            py_files.extend(sorted([p for p in target_dir.rglob("*.py") if p.is_file()]))

    assert len(py_files) >= 50, f"Phải tìm thấy ít nhất 50 tệp .py trong kho (tìm thấy {len(py_files)})"

    def _phang(nodes):
        ra = []
        def di(ns):
            for n in ns:
                ra.append(n)
                di(n.than)
        di(nodes)
        return ra

    so_tep_pass = 0
    for p in py_files:
        raw_bytes_original = p.read_bytes()
        sha_original = hashlib.sha256(raw_bytes_original).hexdigest()

        # Mở -> Cây thẻ
        record = doc_tep_py_sang_cay_the(p)
        ds = _phang(record.tree)

        # Ép TẤT CẢ thẻ đi qua bộ ghi trong một lượt. Bản cũ ghi từng thẻ rồi
        # dựng lại cả module hơn 5.000 lần, khiến cùng một phép chứng minh mất >6 phút.
        for node in ds:
            node.da_sua = True
        record.has_modifications = True
        output_bytes = luu_cay_the_ra_tep_py(record)
        sha_output = hashlib.sha256(output_bytes).hexdigest()

        assert sha_output == sha_original, (
            f"Thất bại cửa cứng 1 tại file {p.relative_to(PROJECT_ROOT)}: "
            f"SHA ban đầu={sha_original}, SHA sau lưu={sha_output}"
        )
        so_tep_pass += 1

    assert so_tep_pass == len(py_files)


# ==============================================================================
# CỬA CỨNG 2: SỬA 1 Ô — GIỮ NGUYÊN CHÚ THÍCH CUỐI DÒNG VÀ 0 BYTE LỆCH DÒNG KHÁC
# ==============================================================================

def test_cua_cung_2_sua_o_giu_nguyen_chu_thich_cuoi_dong():
    """Kiểm tra trường duoi_dong trích xuất bằng end_col_offset.
    Khi sửa 1 ô, chú thích cuối dòng còn nguyên, và các dòng khác không đổi byte nào.
    """
    sample_code = (
        '# Header docstring\n'
        'CHAT_STAGE_INPUT = "input_check"      # kiểm dữ liệu vào + cổng nội dung\n'
        'x = 10  # biến đếm\n'
        'd = ["# Omega — báo cáo " + "gio", ""]  # có # trong chuỗi và có cả comment\n'
        'print("Xong")\n'
    )
    raw_bytes = sample_code.encode("utf-8")
    record = doc_chuoi_py_sang_cay_the(sample_code)

    # Tìm thẻ gán CHAT_STAGE_INPUT
    target_node = None
    for node in record.tree:
        if node.ma == "gan" and node.o.get("ten_bien") == "CHAT_STAGE_INPUT":
            target_node = node
            break

    assert target_node is not None, "Phải tìm thấy thẻ gán CHAT_STAGE_INPUT"
    assert "# kiểm dữ liệu vào + cổng nội dung" in target_node.duoi_dong

    # Sửa giá trị của ô gia_tri
    target_node.o["gia_tri"] = '"input_check_v2"'
    target_node.da_sua = True
    record.has_modifications = True

    # Lưu lại
    saved_bytes = luu_cay_the_ra_tep_py(record)
    saved_text = saved_bytes.decode("utf-8")

    # Kiểm tra: dòng CHAT_STAGE_INPUT được cập nhật giá trị mới VÀ giữ nguyên chú thích
    assert 'CHAT_STAGE_INPUT = "input_check_v2"      # kiểm dữ liệu vào + cổng nội dung' in saved_text
    # Kiểm tra: dòng chú thích header và các dòng khác vẫn nguyên vẹn
    assert "# Header docstring" in saved_text
    assert 'x = 10  # biến đếm' in saved_text
    assert 'd = ["# Omega — báo cáo " + "gio", ""]  # có # trong chuỗi và có cả comment' in saved_text


def test_trich_duoi_dong_khong_bi_lua_boi_hash_trong_chuoi():
    """Kiểm tra trường hợp có dấu # nằm trong chuỗi (Mục 15).
    Dùng end_col_offset đảm bảo không bao giờ cắt nhầm chuỗi có chứa #.
    """
    sample_code = 'd = ["# Omega — báo cáo " + gio, ""]\n'
    record = doc_chuoi_py_sang_cay_the(sample_code)
    
    node = record.tree[0]
    assert node.ma == "gan"
    assert node.o["ten_bien"] == "d"
    assert node.o["gia_tri"] == '["# Omega — báo cáo " + gio, ""]'
    assert node.duoi_dong == ""  # Không có chú thích thật sau dấu ngoặc vuông


# ==============================================================================
# TEST THẺ MÃ THÔ & BỘ 10 THẺ LỆNH CHUẨN
# ==============================================================================

def test_the_ma_tho_chua_cau_truc_phuc_tap():
    """Cấu trúc chưa hỗ trợ thành mã thô; async def vẫn là thẻ hàm giữ nguyên async."""
    code = (
        'import os\n'
        'from dataclasses import dataclass\n'
        '\n'
        '@dataclass\n'
        'class Config:\n'
        '    host: str = "127.0.0.1"\n'
        '\n'
        'async def chay():\n'
        '    async with lock:\n'
        '        pass\n'
    )
    record = doc_chuoi_py_sang_cay_the(code)
    assert len(record.tree) >= 1

    # 25/08: con số cũ là `>= 3` — nó đếm CẢ HAI dòng `import` là "cấu trúc
    # chưa hỗ trợ". Từ hôm nay khay có thẻ `nhap`, nên hai dòng ấy thành thẻ
    # thật và số mã thô ở cấp ngoài tụt còn 1 (`class Config`).
    #
    # KHÔNG hạ `>= 3` xuống `>= 1` — như thế là nới ngưỡng cho vừa kết quả.
    # Thay bằng phép kiểm CHẶT HƠN: nêu đích danh cấu trúc nào phải là mã thô
    # và cấu trúc nào phải thành thẻ. Sai theo chiều nào cũng đỏ.
    ma_cap_ngoai = [n.ma for n in record.tree]
    assert ma_cap_ngoai.count("nhap") == 2, (
        f"Hai dòng import phải thành thẻ `nhap`, nhận được {ma_cap_ngoai}")
    assert ma_cap_ngoai.count("ma_tho") == 1, (
        f"`class Config` (chưa có thẻ) phải là mã thô, nhận được {ma_cap_ngoai}")
    nhap1 = next(n for n in record.tree if n.ma == "nhap")
    assert nhap1.o.get("thu_vien") == "os"
    nhap2 = [n for n in record.tree if n.ma == "nhap"][1]
    assert nhap2.o.get("thu_vien") == "dataclasses"
    assert nhap2.o.get("phan") == "dataclass"

    async_function = next(node for node in record.tree if node.ma == "ham")
    assert any(child.ma == "ma_tho" for child in async_function.than)
    for node in record.tree:
        node.da_sua = True
    assert luu_cay_the_ra_tep_py(record) == code.encode("utf-8")


def test_sinh_ma_python_10_the_chuan():
    """Kiểm tra sinh mã Python chuẩn thụt lề 4 spaces cho 10 thẻ cố định."""
    nodes = [
        TheNode(id="1", ma="ham", o={"ten_ham": "cong", "tham_so": "a, b"}, than=[
            TheNode(id="2", ma="tra_ve", o={"gia_tri": "a + b"}),
        ]),
        TheNode(id="3", ma="gan", o={"ten_bien": "ket_qua", "gia_tri": "cong(5, 7)"}),
        TheNode(id="4", ma="neu", o={"dieu_kien": "ket_qua > 10"}, than=[
            TheNode(id="5", ma="in_ra", o={"noi_dung": '"Lớn hơn 10"'}),
        ]),
        TheNode(id="6", ma="nguoc_lai", o={}, than=[
            TheNode(id="7", ma="in_ra", o={"noi_dung": '"Nhỏ hơn hoặc bằng 10"'}),
        ]),
        TheNode(id="8", ma="lap_moi", o={"bien": "i", "day": "range(3)"}, than=[
            TheNode(id="9", ma="in_ra", o={"noi_dung": "i"}),
        ]),
        TheNode(id="10", ma="lap_khi", o={"dieu_kien": "ket_qua > 0"}, than=[
            TheNode(id="11", ma="gan", o={"ten_bien": "ket_qua", "gia_tri": "ket_qua - 1"}),
        ]),
        TheNode(id="12", ma="goi_ham", o={"ten_ham": "cong", "doi_so": "1, 2"}),
        TheNode(id="13", ma="pheptinh", o={"trai": "x", "phep": "+", "phai": "y"}),
    ]

    generated_code = sinh_ma_python(nodes)
    expected_snippets = [
        "def cong(a, b):",
        "    return a + b",
        "ket_qua = cong(5, 7)",
        "if ket_qua > 10:",
        '    print("Lớn hơn 10")',
        "else:",
        '    print("Nhỏ hơn hoặc bằng 10")',
        "for i in range(3):",
        "    print(i)",
        "while ket_qua > 0:",
        "    ket_qua = ket_qua - 1",
        "cong(1, 2)",
        "x + y",
    ]
    for snippet in expected_snippets:
        assert snippet in generated_code, f"Thiếu đoạn mã sinh: {snippet}\nToàn bộ mã:\n{generated_code}"


# ==============================================================================
# TEST 5 LỖI ĐỎ & 4 CẢNH BÁO VÀNG
# ==============================================================================

def test_loi_do_1_o_bat_buoc_trong():
    """Lỗi ĐỎ 1: Ô bắt buộc còn trống."""
    nodes = [
        TheNode(id="1", ma="gan", o={"ten_bien": "", "gia_tri": "10"}),  # thiếu ten_bien
    ]
    res = kiem_tra_cay_the(nodes)
    assert not res.hop_le
    assert res.so_loi_do >= 1
    assert any(d.ma_loi == "empty_required_field" for d in res.danh_sach)


def test_loi_do_2_nguoc_lai_khong_sau_neu():
    """Lỗi ĐỎ 2: nguoc_lai không đứng ngay sau neu."""
    nodes = [
        TheNode(id="1", ma="in_ra", o={"noi_dung": '"A"'}),
        TheNode(id="2", ma="nguoc_lai", o={}, than=[
            TheNode(id="3", ma="in_ra", o={"noi_dung": '"B"'}),
        ]),
    ]
    res = kiem_tra_cay_the(nodes)
    assert not res.hop_le
    assert any(d.ma_loi == "orphan_else" for d in res.danh_sach)


def test_loi_do_3_tra_ve_ngoai_ham():
    """Lỗi ĐỎ 3: tra_ve nằm ngoài mọi ham."""
    nodes = [
        TheNode(id="1", ma="tra_ve", o={"gia_tri": "42"}),
    ]
    res = kiem_tra_cay_the(nodes)
    assert not res.hop_le
    assert any(d.ma_loi == "return_outside_function" for d in res.danh_sach)


def test_loi_do_4_bien_dung_chua_gan():
    """Lỗi ĐỎ 4: Tên biến dùng mà chưa từng gán."""
    nodes = [
        TheNode(id="1", ma="in_ra", o={"noi_dung": "chua_tung_gan + 5"}),
    ]
    res = kiem_tra_cay_the(nodes)
    assert not res.hop_le
    assert any(d.ma_loi == "undefined_variable" for d in res.danh_sach)


def test_loi_do_5_than_rong_trong_the_co_than():
    """Lỗi ĐỎ 5: Chuỗi thẻ rỗng bên trong thẻ có thân."""
    nodes = [
        TheNode(id="1", ma="neu", o={"dieu_kien": "True"}, than=[]),  # than rỗng
    ]
    res = kiem_tra_cay_the(nodes)
    assert not res.hop_le
    assert any(d.ma_loi == "empty_body" for d in res.danh_sach)


def test_canh_bao_vang_1_bien_gan_khong_dung():
    """Cảnh báo VÀNG 1: Biến gán rồi không dùng lần nào."""
    nodes = [
        TheNode(id="1", ma="gan", o={"ten_bien": "bien_thua", "gia_tri": "100"}),
        TheNode(id="2", ma="in_ra", o={"noi_dung": '"Xin chao"'}),
    ]
    res = kiem_tra_cay_the(nodes)
    assert res.hop_le  # Vẫn hợp lệ (không có lỗi Đỏ)
    assert res.so_canh_bao_vang >= 1
    assert any(d.ma_loi == "unused_variable" for d in res.danh_sach)


def test_canh_bao_vang_2_lap_khi_khong_doi_bien_dieu_kien():
    """Cảnh báo VÀNG 2: lap_khi điều kiện không đổi trong thân (nguy cơ lặp vô tận)."""
    nodes = [
        TheNode(id="1", ma="gan", o={"ten_bien": "x", "gia_tri": "10"}),
        TheNode(id="2", ma="lap_khi", o={"dieu_kien": "x > 0"}, than=[
            TheNode(id="3", ma="in_ra", o={"noi_dung": "x"}),  # không gán lại x
        ]),
    ]
    res = kiem_tra_cay_the(nodes)
    assert res.hop_le
    assert any(d.ma_loi == "potential_infinite_loop" for d in res.danh_sach)


def test_canh_bao_vang_3_the_sau_tra_ve():
    """Cảnh báo VÀNG 3: Thẻ nằm sau tra_ve trong cùng một thân (dead code)."""
    nodes = [
        TheNode(id="1", ma="ham", o={"ten_ham": "f", "tham_so": ""}, than=[
            TheNode(id="2", ma="tra_ve", o={"gia_tri": "1"}),
            TheNode(id="3", ma="in_ra", o={"noi_dung": '"Khong bao gio chay"'}),
        ]),
    ]
    res = kiem_tra_cay_the(nodes)
    assert res.hop_le
    assert any(d.ma_loi == "unreachable_code" for d in res.danh_sach)


def test_canh_bao_vang_4_long_sau_qua_4_tang():
    """Cảnh báo VÀNG 4: Lồng sâu quá 4 tầng."""
    n5 = TheNode(id="5", ma="in_ra", o={"noi_dung": '"Sau 5 tầng"'})
    n4 = TheNode(id="4", ma="neu", o={"dieu_kien": "True"}, than=[n5])
    n3 = TheNode(id="3", ma="neu", o={"dieu_kien": "True"}, than=[n4])
    n2 = TheNode(id="2", ma="neu", o={"dieu_kien": "True"}, than=[n3])
    n1 = TheNode(id="1", ma="neu", o={"dieu_kien": "True"}, than=[n2])
    root = [TheNode(id="0", ma="neu", o={"dieu_kien": "True"}, than=[n1])]

    res = kiem_tra_cay_the(root)
    assert any(d.ma_loi == "excessive_nesting" for d in res.danh_sach)


def test_dem_so_lan_dung_the_xN():
    """Kiểm tra bộ đếm ×N đếm chính xác số lần dùng từng thẻ."""
    nodes = [
        TheNode(id="1", ma="gan", o={"ten_bien": "a", "gia_tri": "1"}),
        TheNode(id="2", ma="gan", o={"ten_bien": "b", "gia_tri": "2"}),
        TheNode(id="3", ma="in_ra", o={"noi_dung": "a + b"}),
    ]
    res = kiem_tra_cay_the(nodes)
    assert res.so_lan_dung_the["gan"] == 2
    assert res.so_lan_dung_the["in_ra"] == 1
    assert res.so_lan_dung_the["neu"] == 0


# ==============================================================================
# TEST 4 LỚP BẢO MẬT API MÁY CHỦ (MỤC 13.2 & 14.2)
# ==============================================================================

def test_api_bao_mat_4_lop():
    """Kiểm tra 4 lớp bảo mật của API máy chủ bao gồm kiểm tra Origin / Referer toàn diện."""
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    from interface import the_api
    from interface.the_app import tao_app

    async def _run_checks():
        app = tao_app()
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            valid_token = app["auth_token"]

            # 1. Gọi thiếu Auth token -> Phải trả về 403
            resp_no_token = await client.post("/api/kiem", json={"tree": []})
            assert resp_no_token.status == 403

            # 2. Gọi sai Auth token -> Phải trả về 403
            resp_wrong_token = await client.post(
                "/api/kiem",
                json={"tree": []},
                headers={"X-Auth-Token": "wrong_token_12345"}
            )
            assert resp_wrong_token.status == 403

            # 3. Gọi đúng Auth token qua header X-Auth-Token -> 200 OK
            resp_valid = await client.post(
                "/api/kiem",
                json={"tree": []},
                headers={"X-Auth-Token": valid_token, "Origin": "http://127.0.0.1:8099"}
            )
            assert resp_valid.status == 200
            data = await resp_valid.json()
            assert "hop_le" in data

            # 4. Ghi file chứa '..' (Path traversal) -> Phải trả về 403
            resp_traversal = await client.post(
                "/api/luu_tep",
                json={"duong_dan": "../../evil.py", "tree": []},
                headers={"X-Auth-Token": valid_token, "Origin": "http://127.0.0.1:8099"}
            )
            assert resp_traversal.status == 403

            # 5. Các trường hợp Origin không hợp lệ -> Phải trả về 403
            invalid_origins = [
                "http://malicious-site.com",
                "http://127.0.0.1.evil.com",
                "http://localhost.evil.com",
                "http://evil.com/?x=127.0.0.1",
                "http://not-localhost.tld",
                "http://evil.com@localhost",
                "ftp://localhost",
                "//localhost",
                "http://localhost/path",
                "http://localhost:99999",
            ]
            for bad_origin in invalid_origins:
                resp_bad_origin = await client.post(
                    "/api/kiem",
                    json={"tree": []},
                    headers={"X-Auth-Token": valid_token, "Origin": bad_origin}
                )
                assert resp_bad_origin.status == 403, f"Origin {bad_origin} phải bị chặn 403"

            # 6. Origin hợp lệ (loopback chuẩn) -> 200 OK
            valid_origins = [
                "http://127.0.0.1:8099",
                "http://localhost:8099",
                "https://127.0.0.1",
                "http://127.0.0.1",
            ]
            for ok_origin in valid_origins:
                resp_ok = await client.post(
                    "/api/kiem",
                    json={"tree": []},
                    headers={"X-Auth-Token": valid_token, "Origin": ok_origin}
                )
                assert resp_ok.status == 200, f"Origin {ok_origin} phải được chấp nhận 200"

        finally:
            await client.close()

    asyncio.run(_run_checks())


def test_api_e2e_mo_sua_luu_tep_http(tmp_path):
    """Test E2E thực tế qua HTTP: POST /api/mo_tep -> Sửa JSON -> POST /api/luu_tep -> Đọc lại đĩa.
    
    Chứng minh:
    1. Giá trị mới thật sự được ghi xuống đĩa qua API.
    2. Chỉ span dự kiến đổi, các dòng khác giữ nguyên byte.
    3. Chú thích cuối dòng, elif, chú kiểu, giá trị mặc định, newline không bị mất.
    4. Trả về SHA-256 mới và kiểm tra xung đột 409 Conflict nếu tệp trên đĩa bị thay đổi ngoài ý muốn.
    5. Không gán da_sua trực tiếp lên object Python mà truyền qua JSON API.
    """
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    from interface import the_api
    from interface.the_app import tao_app

    import copy

    test_file = tmp_path / "sample_e2e.py"
    sample_code = (
        '# Header comment\r\n'
        'def chon(x: int = 1) -> bool:\r\n'
        '    if x == 1:  # nhánh đầu\r\n'
        '        return True\r\n'
        '    elif x == 2:  # nhánh cần sửa\r\n'
        '        return False\r\n'
        '    else:\r\n'
        '        return True\r\n'
    )
    raw_sample = sample_code.encode("utf-8")
    test_file.write_bytes(raw_sample)
    the_api.ALLOWED_ROOTS.append(tmp_path.resolve())

    async def _run():
        app = tao_app()
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            token = app["auth_token"]
            headers = {
                "X-Auth-Token": token,
                "Origin": "http://127.0.0.1:8099",
            }

            # 1. Mở tệp qua API
            resp_open = await client.post(
                "/api/mo_tep",
                json={"duong_dan": str(test_file)},
                headers=headers
            )
            assert resp_open.status == 200
            data_open = await resp_open.json()
            assert "tree" in data_open
            assert "sha256" in data_open
            original_sha = data_open["sha256"]
            assert original_sha == hashlib.sha256(sample_code.encode("utf-8")).hexdigest()

            assert data_open["newline"] == "CRLF"
            tree = data_open["tree"]

            def walk(nodes):
                for node in nodes:
                    yield node
                    yield from walk(node.get("than", []))

            # 2. Tìm đúng thẻ elif và sửa điều kiện qua JSON thuần túy.
            target = next(
                node for node in walk(tree)
                if node.get("ma") == "neu" and node.get("o", {}).get("noi_tiep") == "1"
            )
            target["o"]["dieu_kien"] = "x == 3"
            # Cố tình không gửi da_sua=True: server phải tự suy ra thay đổi.
            target["da_sua"] = False

            # Tệp đã có mà thiếu version token phải bị chặn trước khi ghi.
            resp_missing_sha = await client.post(
                "/api/luu_tep",
                json={"duong_dan": str(test_file), "tree": tree, "kieu_luu": "py"},
                headers=headers,
            )
            assert resp_missing_sha.status == 428
            assert test_file.read_bytes() == raw_sample

            # THÊM THẺ: 26/08/2026 CHUYỂN TỪ "LUÔN 422" SANG "TUỲ TỆP".
            #
            # Trước đây mọi thao tác cấu trúc đều 422 vì bộ ghi sửa TẠI CHỖ
            # trên CST, thẻ mới không có chỗ ghi vào. Nay có đường thứ hai:
            # sinh lại CẢ TỆP từ cây thẻ — nhưng chỉ khi tệp biểu diễn TRỌN
            # VẸN bằng thẻ, đo tại chỗ bằng `_sinh_lai_duoc_tron_ven`.
            #
            # ĐÂY KHÔNG PHẢI NỚI TAY. Mẫu `sample_e2e.py` này sinh lại ra
            # ĐÚNG BẢN GỐC TỪNG BYTE — đã đo, kể cả chú thích cuối dòng
            # (`# nhánh đầu`), chú kiểu (`x: int = 1) -> bool`), `elif`, và
            # CRLF. Cây thẻ mang trọn tệp, nên sinh lại không đánh rơi gì.
            #
            # Còn `core/chat_contract.py` thì sinh lại KHÁC bản gốc (chữ ký
            # hàm nhiều dòng bị gộp), nên vẫn 422 — kiểm ngay dưới.
            assert data_open.get("them_bot_the_duoc") is True, (
                "/api/mo_tep phải nói ngay lúc mở là tệp này cho thêm/bớt thẻ; "
                "thiếu thì giao diện sẽ báo bừa 'chỉ sửa được nội dung ô'")

            structural_tree = copy.deepcopy(tree)
            structural_tree.append({
                "id": "the_moi", "ma": "in_ra", "o": {"noi_dung": '"mới"'},
                "than": [], "da_sua": True,
            })
            resp_structural = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(test_file), "tree": structural_tree,
                    "kieu_luu": "py", "expected_sha256": original_sha,
                },
                headers=headers,
            )
            assert resp_structural.status == 200, (
                "tệp biểu diễn trọn vẹn bằng thẻ thì thêm thẻ phải LƯU ĐƯỢC")
            sau_them = test_file.read_bytes()
            # Thẻ mới phải có mặt, và MỌI thứ cũ phải còn nguyên — đây mới là
            # điều test này bảo vệ, không phải con số 422.
            assert b'print("m\xe1\xbb\x9bi")' in sau_them, "thẻ mới không được ghi"
            assert b"# nh\xc3\xa1nh \xc4\x91\xe1\xba\xa7u" in sau_them, "mất chú thích cuối dòng"
            assert b"x: int = 1" in sau_them, "mất chú kiểu tham số"
            assert b"-> bool" in sau_them, "mất chú kiểu trả về"
            # Chỉ chốt `elif`, KHÔNG chốt điều kiện: `tree` đã bị bước Save As
            # phía trên sửa `x == 2` thành `x == 3`, nên chốt số cụ thể là
            # chốt nhầm — test sai chứ không phải mã sai.
            assert b"elif x == " in sau_them, "mất nhánh elif"
            assert b"# Header comment" in sau_them, "mất chú thích đầu tệp"
            assert b"\r\n" in sau_them and b"\n\n" not in sau_them.replace(b"\r\n", b"\n"), (
                "phải giữ quy ước xuống dòng CRLF của tệp gốc")

            # TỆP KHÔNG BIỂU DIỄN TRỌN VẸN THÌ VẪN CHẶN — nửa còn lại của luật.
            phuc_tap = tmp_path / "phuc_tap.py"
            phuc_tap.write_bytes(
                (Path(__file__).resolve().parent.parent / "core" / "chat_contract.py")
                .read_bytes())
            resp_mo_pt = await client.post(
                "/api/mo_tep", json={"duong_dan": str(phuc_tap)}, headers=headers)
            data_pt = await resp_mo_pt.json()
            assert data_pt.get("them_bot_the_duoc") is False, (
                "tệp sinh lại KHÁC bản gốc mà lại báo cho thêm thẻ")
            raw_pt = phuc_tap.read_bytes()
            cay_pt = copy.deepcopy(data_pt["tree"])
            cay_pt.append({"id": "x", "ma": "in_ra", "o": {"noi_dung": '"x"'},
                           "than": [], "da_sua": True})
            resp_pt = await client.post(
                "/api/luu_tep",
                json={"duong_dan": str(phuc_tap), "tree": cay_pt,
                      "kieu_luu": "py", "expected_sha256": data_pt["sha256"]},
                headers=headers,
            )
            assert resp_pt.status == 422, "tệp phức tạp vẫn phải bị chặn"
            assert phuc_tap.read_bytes() == raw_pt, "bị chặn mà tệp vẫn đổi"

            # Trả tệp mẫu về nguyên trạng cho các bước sau của test.
            test_file.write_bytes(raw_sample)

            # Save As sang tệp mới phải giữ toàn bộ cú pháp ẩn nhờ byte+SHA nguồn,
            # không được dựng lại từ các ô thẻ rồi làm mất annotation/comment/elif.
            save_as_file = tmp_path / "sample_e2e_copy.py"
            resp_save_as = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(save_as_file), "tree": tree, "kieu_luu": "py",
                    "source_path": str(test_file), "source_sha256": original_sha,
                },
                headers=headers,
            )
            assert resp_save_as.status == 200
            assert save_as_file.read_bytes() == raw_sample.replace(b"x == 2", b"x == 3")
            assert test_file.read_bytes() == raw_sample

            # 3. Lưu tệp qua API với expected_sha256
            resp_save = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(test_file),
                    "tree": tree,
                    "kieu_luu": "py",
                    "expected_sha256": original_sha,
                    "has_modifications": True
                },
                headers=headers
            )
            assert resp_save.status == 200
            data_save = await resp_save.json()
            assert data_save.get("status") == "PASS"
            new_sha = data_save.get("sha256")

            # 4. Đọc lại từ đĩa để xác thực
            saved_bytes = test_file.read_bytes()
            assert hashlib.sha256(saved_bytes).hexdigest() == new_sha
            expected_bytes = raw_sample.replace(b"x == 2", b"x == 3")
            assert saved_bytes == expected_bytes
            assert b"def chon(x: int = 1) -> bool:\r\n" in saved_bytes
            assert b"elif x == 3:  # nh" in saved_bytes

            # Lưu lần hai bằng SHA mới phải thành công.
            target["o"]["dieu_kien"] = "x == 4"
            resp_save_2 = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(test_file), "tree": tree, "kieu_luu": "py",
                    "expected_sha256": new_sha,
                },
                headers=headers,
            )
            assert resp_save_2.status == 200
            data_save_2 = await resp_save_2.json()
            new_sha_2 = data_save_2["sha256"]
            assert test_file.read_bytes() == raw_sample.replace(b"x == 2", b"x == 4")

            # 5. Sửa ngoài luồng rồi gửi đúng SHA của lần lưu gần nhất: phải 409.
            external_bytes = test_file.read_bytes() + b"# Sua ben ngoai\r\n"
            test_file.write_bytes(external_bytes)
            resp_conflict = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(test_file),
                    "tree": tree,
                    "kieu_luu": "py",
                    "expected_sha256": new_sha_2,
                },
                headers=headers
            )
            assert resp_conflict.status == 409
            data_conflict = await resp_conflict.json()
            assert "409 Conflict" in data_conflict.get("error", "")
            assert test_file.read_bytes() == external_bytes

        finally:
            await client.close()

    asyncio.run(_run())


def test_api_json_version_token_bat_buoc_va_mo_lai_duoc(tmp_path):
    """JSON dùng cùng optimistic-lock như Python và thật sự mở lại được trên app."""
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    from interface import the_api
    from interface.the_app import tao_app

    target = tmp_path / "cards.json"
    the_api.ALLOWED_ROOTS.append(tmp_path.resolve())
    tree = [{
        "id": "n1", "ma": "gan", "o": {"ten_bien": "x", "gia_tri": "1"},
        "than": [], "da_sua": True,
    }]

    async def _run():
        app = tao_app()
        client = TestClient(TestServer(app))
        await client.start_server()
        headers = {
            "X-Auth-Token": app["auth_token"],
            "Origin": "http://127.0.0.1:8099",
        }
        try:
            create = await client.post(
                "/api/luu_tep",
                json={"duong_dan": str(target), "tree": tree, "kieu_luu": "json"},
                headers=headers,
            )
            assert create.status == 200
            created = await create.json()
            first_sha = created["sha256"]
            first_bytes = target.read_bytes()

            opened = await client.post(
                "/api/mo_tep", json={"duong_dan": str(target)}, headers=headers
            )
            assert opened.status == 200
            opened_data = await opened.json()
            assert opened_data["sha256"] == first_sha
            assert opened_data["tree"][0]["o"]["gia_tri"] == "1"
            opened_data["tree"][0]["o"]["gia_tri"] = "2"

            missing = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(target), "tree": opened_data["tree"],
                    "kieu_luu": "json",
                },
                headers=headers,
            )
            assert missing.status == 428
            assert target.read_bytes() == first_bytes

            conflict = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(target), "tree": opened_data["tree"],
                    "kieu_luu": "json", "expected_sha256": "0" * 64,
                },
                headers=headers,
            )
            assert conflict.status == 409
            assert target.read_bytes() == first_bytes

            saved = await client.post(
                "/api/luu_tep",
                json={
                    "duong_dan": str(target), "tree": opened_data["tree"],
                    "kieu_luu": "json", "expected_sha256": first_sha,
                },
                headers=headers,
            )
            assert saved.status == 200
            assert json.loads(target.read_text(encoding="utf-8"))[0]["o"]["gia_tri"] == "2"
        finally:
            await client.close()

    asyncio.run(_run())


def test_ui_giu_sha_va_khong_danh_dau_ban_khi_vua_mo():
    """Khóa tĩnh tối thiểu cho contract JS; HTTP byte-level được đo ở hai test trên."""
    js = (PROJECT_ROOT / "interface" / "web" / "the_v1" / "app.js").read_text(encoding="utf-8")
    assert "activeFileSha256: null" in js
    assert "state.activeFileSha256 = data.sha256" in js
    assert "payload.expected_sha256 = state.activeFileSha256" in js
    assert "payload.source_path = state.activeFilePath" in js
    assert "payload.source_sha256 = state.activeFileSha256" in js
    assert "onTreeChanged(false, false)" in js
    assert "resp.status === 409" in js


def test_api_chay_ma_tat_mac_dinh(monkeypatch):
    """Bản public không được gọi tiến trình Python nếu chưa bật rõ opt-in."""
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    from interface import the_api
    from interface.the_app import tao_app

    monkeypatch.setattr(the_api, "ALLOW_CODE_EXECUTION", False)

    async def _run():
        app = tao_app()
        client = TestClient(TestServer(app))
        await client.start_server()
        headers = {
            "X-Auth-Token": app["auth_token"],
            "Origin": "http://127.0.0.1:8099",
        }
        try:
            status = await client.get("/api/status", headers=headers)
            assert status.status == 200
            assert (await status.json())["code_execution_enabled"] is False
            run = await client.post("/api/chay", json={"code": "print(1)"}, headers=headers)
            assert run.status == 403
        finally:
            await client.close()

    asyncio.run(_run())


def test_sandbox_chay_ma_thanh_cong():
    """Chạy mã in kết quả -> Status PASS, bắt đúng stdout."""
    code = (
        'def cong(a, b):\n'
        '    return a + b\n'
        'print(cong(5, 7))\n'
    )
    res = chay_ma_tien_trinh_rieng(code, timeout=5.0)
    assert res.status == "PASS"
    assert res.exit_code == 0
    assert res.stdout.strip() == "12"
    assert not res.timed_out


def test_sandbox_chay_ma_loi_cu_phap_hoac_runtime():
    """Chạy mã lỗi runtime -> Status ERROR, bắt đúng stderr và exit_code != 0."""
    code = 'print(1 / 0)\n'
    res = chay_ma_tien_trinh_rieng(code, timeout=5.0)
    assert res.status == "ERROR"
    assert res.exit_code != 0
    assert "ZeroDivisionError" in res.stderr


def test_chay_ma_in_duoc_tieng_viet_co_dau():
    """In chữ có dấu phải CHẠY ĐƯỢC, không nổ UnicodeEncodeError.

    Đo thật 30/08/2026, qua đúng hàm này, TRƯỚC khi vá:

        print("Chuot")  -> PASS,  stdout 'Chuot'
        print("Chuột")  -> ERROR, UnicodeEncodeError: 'charmap' codec can't
                           encode character '\u1ed9'

    Cha giải mã bằng encoding="utf-8" nhưng CON vẫn ghi bằng codec mặc định
    của Windows (cp1252). Nghĩa là mọi người học Việt Nam in một chữ có dấu
    đều nhận lỗi — ở nút CHẠY lẫn ở bộ chấm thử thách. Lộ ra khi bấm tay bài
    4 "Lọc Sản Phẩm": nó in ['Chuột'] nên 0/2 trường hợp đo được, trong khi
    bài 3 in "Nguyen Van A" thuần ASCII thì 3/3.

    Cửa này CHẠY THẬT chứ không dò chuỗi `-X utf8` trong mã: gỡ cờ ấy ra thì
    nó phải đỏ vì hành vi, không vì thiếu một chuỗi.
    """
    res = chay_ma_tien_trinh_rieng('print("Chuột")\n', timeout=5.0)
    assert res.status == "PASS", f"stderr: {res.stderr[-300:]}"
    assert res.exit_code == 0
    assert res.stdout.strip() == "Chuột"
    assert "UnicodeEncodeError" not in res.stderr


def test_chay_ma_in_duoc_ca_danh_sach_chuoi_co_dau():
    """Đúng ca đã làm bài 4 gãy: in một list chứa chữ có dấu."""
    code = 'ds = ["Chuột", "Bàn phím"]\nprint(ds)\n'
    res = chay_ma_tien_trinh_rieng(code, timeout=5.0)
    assert res.status == "PASS", f"stderr: {res.stderr[-300:]}"
    assert "Chuột" in res.stdout
    assert "Bàn phím" in res.stdout


def test_sandbox_chong_lap_vo_han_timeout_5s():
    """Chạy vòng lặp vô hạn -> Kill sau timeout (thử với timeout=1.0s trong test để chạy nhanh)."""
    code = 'while True:\n    pass\n'
    res = chay_ma_tien_trinh_rieng(code, timeout=1.0)
    assert res.status == "TIMEOUT"
    assert res.timed_out
    assert res.exit_code == 124
    assert "[TIMEOUT]" in res.stderr


# ==============================================================================
# TEST ĐƠN VỊ CẤU TRÚC DỮ LIỆU THENODE & FILESOURCERECORD
# ==============================================================================

def test_the_node_to_dict_va_from_dict():
    """Kiểm tra tuần tự hóa hai chiều của TheNode to_dict và from_dict."""
    con = TheNode(id="sub1", ma="in_ra", o={"noi_dung": '"hello"'})
    node = TheNode(
        id="root1",
        ma="neu",
        o={"dieu_kien": "x > 0"},
        than=[con],
        line_start=1,
        line_end=2,
        indent=0,
        duoi_dong="# check x",
        da_sua=True
    )

    d = node.to_dict()
    assert d["id"] == "root1"
    assert d["ma"] == "neu"
    assert d["o"]["dieu_kien"] == "x > 0"
    assert len(d["than"]) == 1
    assert d["than"][0]["ma"] == "in_ra"
    assert d["duoi_dong"] == "# check x"
    assert d["da_sua"] is True

    phuc_hoi = TheNode.from_dict(d)
    assert phuc_hoi.id == "root1"
    assert phuc_hoi.ma == "neu"
    assert len(phuc_hoi.than) == 1
    assert phuc_hoi.than[0].o["noi_dung"] == '"hello"'
    assert phuc_hoi.da_sua is True

