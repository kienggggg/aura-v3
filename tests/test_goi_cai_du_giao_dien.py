# -*- coding: utf-8 -*-
"""Mọi tệp giao diện trong `interface/web/` phải được `package-data` khai.

26/08/2026 — bắt được một lỗi hỏng lặng lẽ đúng loại `pyproject.toml` đã tự
cảnh báo ngay phía trên dòng gây lỗi.

`package-data` khai `interface = ["web/the_v1/*"]`. Nhưng `interface/web/` còn
hai tệp NGOÀI `the_v1/`:

    interface/web/chat.html
    interface/web/memory.html

Cả hai không vào wheel. Đo trên bản cài trong venv sạch:

    aura-chat --port 8799     khởi động bình thường, KHÔNG in một dòng lỗi nào
    GET http://127.0.0.1:8799/        -> 404, 0 byte
    GET http://127.0.0.1:8799/memory  -> 404, 0 byte

Đúng lệnh README bảo người dùng gõ. `web.FileResponse` trên tệp không có thì
aiohttp trả 404 — không ngoại lệ, không nhật ký, không gì cả.

Vì sao lượt kiểm trước không thấy: nó liệt kê tệp trong
`site-packages/interface/web/the_v1/` — tức ĐÚNG thư mục vừa được khai. Kiểm
trong chỗ mình vừa khai thì bao giờ cũng đủ. Phải đối chiếu với NGUỒN.

Test này so hai bên: tệp có thật dưới `interface/web/` và các mẫu trong
`package-data`. Thêm một thư mục giao diện mới mà quên khai thì đỏ ngay, thay
vì im lặng cho tới khi có người cài gói ra rồi thấy trang trắng.
"""
from __future__ import annotations

import fnmatch
import sys
import unittest
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - máy này chạy 3.11+
    import tomli as tomllib

GOC = Path(__file__).resolve().parent.parent


class TestGoiCaiDuGiaoDien(unittest.TestCase):
    def test_moi_tep_web_deu_duoc_package_data_khai(self):
        with open(GOC / "pyproject.toml", "rb") as f:
            cau_hinh = tomllib.load(f)
        mau = cau_hinh["tool"]["setuptools"]["package-data"]["interface"]

        thu_muc_web = GOC / "interface" / "web"
        thieu = []
        for tep in sorted(thu_muc_web.rglob("*")):
            if not tep.is_file():
                continue
            # đường dẫn tương đối so với gói `interface`, dùng dấu `/`
            tuong_doi = tep.relative_to(GOC / "interface").as_posix()
            if not any(fnmatch.fnmatch(tuong_doi, m) for m in mau):
                thieu.append(tuong_doi)

        self.assertEqual(
            thieu, [],
            "Tệp giao diện KHÔNG được `package-data` khai — cài gói ra sẽ 404 "
            f"lặng lẽ: {thieu}. Sửa `[tool.setuptools.package-data]` trong "
            "pyproject.toml.")

    def test_hai_trang_chat_van_con(self):
        """Chốt hai tệp cụ thể đã gây ra lỗi 26/08, phòng khi ai đổi tên."""
        for ten in ("chat.html", "memory.html"):
            self.assertTrue(
                (GOC / "interface" / "web" / ten).is_file(),
                f"interface/web/{ten} biến mất — `aura-chat` sẽ trả 404")


if __name__ == "__main__":
    unittest.main()
