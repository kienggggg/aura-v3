# AURA v3

Hai thứ chạy được trên máy không GPU rời:

- **AURA chat** — một con chatbot có màn hình chat.
- **App Thẻ** — dựng chương trình Python bằng cách kéo thả thẻ, kèm bộ tìm lỗi.

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ba gói ngoài, không hơn: `aiohttp`, `httpx`, `pytest`.

---

## AURA chat

```bash
venv\Scripts\python.exe aura_chat.py
```

→ http://127.0.0.1:8799

Không có `.env` vẫn chạy: cổng cloud trống thì `UnavailableModelGateway` giữ
cửa trước sống và trả lời "chưa cấu hình", thay vì đổ.

---

## App Thẻ

```bash
venv\Scripts\python.exe -m interface.the_app --port 8088
```

Địa chỉ kèm mã thông hành in ra ngay trên màn hình lúc khởi động. Trình duyệt
tự mở; thêm `--no-browser` nếu không muốn.

Bấm `start_the_app.bat` cũng ra kết quả ấy.

### Bật chạy mã

Nút **Chạy**, **Tìm lỗi** và **Dò dòng dữ liệu** **tắt mặc định**. Bật:

```bash
venv\Scripts\python.exe -m interface.the_app --port 8088 --allow-exec
```

Đọc mục an toàn bên dưới trước khi bật.

---

## An toàn — đọc trước khi bật `--allow-exec`

**App chạy mã của bạn với ĐÚNG QUYỀN tài khoản Windows của bạn. KHÔNG có
sandbox.**

Câu trên không phải lời cảnh báo cho có. Đo ngày 25/08/2026, chạy mã tuỳ ý qua
đúng đường app dùng (`core/the_v1.py: chay_ma_tien_trinh_rieng`):

| thử | kết quả |
|---|---|
| ghi tệp bằng đường dẫn tuyệt đối ngoài thư mục tạm | **ghi được** |
| gọi tiến trình con (`cmd /c`) | **chạy được** |
| mở socket và lắng nghe | **mở được** |
| đọc tệp bất kỳ trên đĩa | **đọc được** |
| đọc biến môi trường | **đọc được** |

Thứ duy nhất có: **tiến trình riêng** và **trần 5 giây**. Hai thứ ấy chống lặp
vô hạn và chống treo app. Chúng không chống mã phá hoại, và không có giới hạn
RAM, hệ tệp, mạng hay tiến trình nào cả.

Nghĩa là:

- **Dùng được** — bạn chạy mã của chính bạn trên máy của chính bạn. Đó đúng
  bằng quyền bạn vốn có khi mở `python` lên gõ.
- **KHÔNG dùng được** — chạy mã tải từ nơi khác, hoặc đặt app lên máy chủ cho
  nhiều người dùng. Với hiện trạng, đó là trao cho người lạ quyền ghi tệp và
  mở tiến trình trên máy chủ.

Một kế hoạch cũ (19/08) từng hứa "giới hạn 256 MB RAM" và "không cấp quyền ghi
ra ngoài". Chạy thử thì `import resource` là API Unix, Windows không có; còn
ghi bằng đường dẫn tuyệt đối thì ghi được. **Cả hai lời hứa ấy chưa bao giờ
tồn tại.**

### Ba cửa đang thật sự chặn

Kiểm bằng cách gọi API sống, không bằng đọc mã:

| cửa | thử | kết quả |
|---|---|---|
| chỉ bind loopback | `--host 0.0.0.0` | từ chối, thoát mã 1 |
| mã thông hành | `POST /api/chay` không token | `403` |
| mã thông hành | `POST /api/luu_tep` không token | `403` |
| chạy mã tắt mặc định | `POST /api/chay` có token, chưa `--allow-exec` | `403 bi_khoa` |

Mã thông hành sinh ngẫu nhiên 16 byte mỗi lần khởi động.

---

## Chạy test

```bash
venv\Scripts\python.exe -m pytest tests -q
```

624 xanh, 1 bỏ qua.

Một cửa nữa chạy bằng Node — mọi nút trên giao diện phải có người nghe sự kiện
thật:

```bash
node --test tests/test_moi_nut_co_handler.js
```

Cửa ấy sinh ra sau hai ngày bắt được tám lỗi cùng một họ: có nút mà bấm không
có gì xảy ra. **624 test xanh suốt trong khi cả tám đang tồn tại** — chúng chỉ
lộ ra khi tự bấm thử như người dùng. Cửa này chặn được đúng một loại trong họ
đó, loại rẻ nhất và máy kiểm được. Ba loại còn lại (nhãn nói sai việc, đọc sai
tên trường, trả lời giả) vẫn phải bắt bằng tay.

---

## Chỗ chưa có

Nói ra trước khi ai đó phải hỏi:

- **Không có sandbox** — mục trên.
- **Không có gói cài.** Chưa có `pyproject.toml`, chưa có installer. Cài bằng
  cách kể trên.
- **Bốn chức năng IDE còn thiếu**: tự động lưu, nhiều tab tệp, chép/dán thẻ,
  nhảy tới định nghĩa. Tự động lưu là cố ý chưa làm: app ghi tệp `.py` thật
  vào kho, tự lưu là sửa mã nguồn sau lưng người dùng.
- **Bộ truy ngược giá trị chưa đạt ngưỡng.** Đo trên năm bộ đề độc lập, chính
  xác cao nhất 0,76 và thấp nhất 0,46, ngưỡng đăng ký trước là 0,60. Nó đang
  là công cụ nghiên cứu, không phải tính năng đã chốt.

---

## Kho này không đẩy lên GitHub

Kho cũ `AURA_OS_v2` có ~20 khoá API thật trong lịch sử. Kho v3 tách ra ngày
12/08/2026, lịch sử sạch từ commit đầu, và **không cấu hình remote**. Khoá đi
vào `.env`, không vào tệp được git theo dõi.
