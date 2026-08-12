# AURA v3

Một con chatbot có màn hình chat. Chạy được trên máy không GPU rời.

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
venv\Scripts\python.exe aura_chat.py
```

→ http://127.0.0.1:8799

Không có `.env` vẫn chạy: cổng cloud trống thì `UnavailableModelGateway` giữ cửa
trước sống và trả lời "chưa cấu hình", thay vì đổ.

```bash
venv\Scripts\python.exe -m pytest tests -q
```

## Nó gồm những gì

| | |
|---|---|
| mã | **17 tệp · 4.248 dòng** |
| test | 28 tệp |
| gói ngoài | **3** — `aiohttp`, `httpx`, `pytest` |

Danh sách 17 tệp là **danh sách đóng**, giữ trong `tests/test_v3_ranh_gioi.py`.
Test đó đi từ cửa vào `aura_chat.py`, lần theo `import` thật — kể cả import giấu
trong hàm — nên không kéo lén tệp thứ 18 vào được. Thêm tệp thì phải sửa danh
sách, tức là phải cố ý và có người thấy.

## Vì sao con số nhỏ là điểm chính

Repo này tách ra từ AURA v2 ngày 12/08/2026. v2 có **339 tệp .py / 47.566
dòng** và **33 cờ bật-tắt tính năng, 29 cái đang TẮT**. Bệnh không phải "mã dở"
— bệnh là mọi thứ được xây rồi cắm vào, không thứ nào phải chứng minh mình
chạy, và không thứ nào bị gỡ ra. `core/config.py` của v2 dài 1.029 dòng trong
khi xương sống chat dùng đúng một hằng số của nó; ở đây nó là `core/paths.py`,
19 dòng.

v2 vẫn còn nguyên làm kho phụ tùng — Telegram, rover BLE, xưởng truyện/video,
mascot, crew 4 công nhân, SkillOpt, Wattpad/Payhip. Muốn mang một mảnh sang thì
**đo nó chạy trước**.

## Vài thứ trong đây có lý do cụ thể

- `core/dong_ho.py`, `core/may_tinh.py` — ngày giờ và số học **không hỏi model**.
  Model từng nói 21/07 khi là 10/08, và `1247*38` ra 46396 thay vì 47.386.
- `core/secret_guard.py` — AURA không đọc mật khẩu ra màn hình. Ngày 09/08/2026
  nhật ký hội thoại chứa mật khẩu wifi thật vì chưa có cổng này.
- `core/local_first_gateway.py` — trò làm trước, mượn thầy khi bí. Nguồn lấy về
  là **dữ liệu**, không phải chỉ dẫn; nhưng chỗ dựa thật không phải câu dặn đó,
  mà là AURA không có quyền gì để một trang web cướp.
- `core/doc_so_phien.py` — "câu thứ 2 là gì" thì **đếm trong sổ**, không đoán.

Luật đầy đủ ở `CLAUDE.md`.
