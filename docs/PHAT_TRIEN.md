# Hướng Dẫn Phát Triển AURA v3

Tài liệu dành cho lập trình viên và người bảo trì hệ thống.

---

## 1. Thiết lập môi trường phát triển

Yêu cầu: **Python >= 3.11** (khuyến nghị Python 3.11 hoặc 3.14).

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Ba gói ngoài duy nhất dùng trong runtime:
- `aiohttp`: Web framework & HTTP server
- `httpx`: HTTP client cho các API adapter
- `libcst==1.9.0`: Xử lý CST/AST giữ nguyên định dạng và chú thích khi mở/sửa/lưu file Python

Gói `pytest` là công cụ kiểm thử dành riêng cho môi trường dev.

---

## 2. Chạy ứng dụng trực tiếp từ mã nguồn

### App Thẻ (The App)
```bash
venv\Scripts\python.exe -m interface.the_app --port 8088
```
Bật chạy mã:
```bash
venv\Scripts\python.exe -m interface.the_app --port 8088 --allow-exec
```

### AURA Chat
```bash
venv\Scripts\python.exe aura_chat.py --port 8799
```

---

## 3. Chạy kiểm thử & Các cửa cứng

### Bộ kiểm thử chính (pytest)
```bash
venv\Scripts\python.exe -m pytest tests -q
```
*Hiện trạng: 702 passed, 1 skipped.*

### Cửa kiểm tra giao diện (Node.js)
Mọi nút bấm trên giao diện web phải có event handler thật để chống lỗi nút bấm liệt:
```bash
node --test tests/test_moi_nut_co_handler.js
```

---

## 4. Đóng gói phân phối (Wheel)

Cấu hình đóng gói được định nghĩa trong `pyproject.toml`.

```bash
venv\Scripts\python.exe -m build --wheel
```

Tệp wheel sinh ra tại `dist/aura_v3-0.1.0-py3-none-any.whl` (~233 KB) bao gồm:
- 23 tệp `core/`
- 9 tệp `interface/`
- 4 tệp giao diện web tĩnh trong `interface/web/the_v1/` (`index.html`, `app.js`, `style.css`, `validator.js`)
- Tệp giấy phép `LICENSE` trong metadata (`dist-info/licenses/LICENSE`)
