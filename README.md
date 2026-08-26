# AURA v3

Hai ứng dụng chạy được trên máy không cần GPU rời:

- **App Thẻ (`aura-the`)** — Dựng chương trình Python bằng cách kéo thả thẻ, kèm bộ kiểm tra và tìm lỗi.
- **AURA Chat (`aura-chat`)** — Trợ lý lập trình giao tiếp trực tiếp trên trình duyệt.

---

## 1. Cài đặt

Yêu cầu máy đã cài **Python >= 3.11**.

Cài đặt từ gói phát hành:

```bash
pip install aura_v3-0.1.0-py3-none-any.whl
```

*(Hoặc cài trực tiếp từ thư mục mã nguồn bằng lệnh `pip install .`)*

Sau khi cài đặt thành công, hệ thống sẽ có hai lệnh chạy: `aura-the` và `aura-chat`.

---

## 2. Cách dùng App Thẻ (`aura-the`)

`aura-the` mở và lưu các tệp `.py` trong **thư mục làm việc hiện tại** (tương tự như `git` hoặc `code .`).

### Khởi động cơ bản
Chuyển tới thư mục chứa bài tập hoặc dự án của bạn và gõ:

```bash
cd D:\bai_tap_cua_toi
aura-the --port 8088
```

App sẽ tự động mở giao diện trên trình duyệt web tại địa chỉ `http://127.0.0.1:8088/?token=...`.

### Các tuỳ chọn thường dùng
- `--du-an <đường_dẫn>`: Trỏ thẳng tới thư mục làm việc khác mà không cần `cd`.
  ```bash
  aura-the --du-an D:\du_an_khac
  ```
- `--port <cổng>`: Chọn cổng mạng mong muốn (mặc định: `8088`).
- `--no-browser`: Không tự động bật cửa sổ trình duyệt khi khởi động.
- `--allow-exec`: Bật tính năng thực thi mã Python (nút **Chạy**, **Tìm lỗi**). Mặc định tính năng chạy mã bị tắt để đảm bảo an toàn.

```bash
aura-the --port 8088 --allow-exec
```

---

## 3. Cách dùng AURA Chat (`aura-chat`)

Khởi động giao diện chatbot:

```bash
aura-chat --port 8799
```

Mở trình duyệt truy cập: `http://127.0.0.1:8799`

Nếu chưa cấu hình khoá API trong tệp `.env`, cổng giao tiếp cục bộ vẫn duy trì hoạt động và phản hồi hướng dẫn thay vì báo lỗi ứng dụng.

---

## 4. An toàn — Đọc kỹ trước khi bật `--allow-exec`

**Ứng dụng chạy mã Python với ĐÚNG QUYỀN tài khoản Windows của bạn. KHÔNG có sandbox (hộp cát).**

Đo đạc thực tế khi chạy mã qua hệ thống:

| Hành động của mã | Kết quả thực tế |
|---|---|
| Ghi tệp bằng đường dẫn tuyệt đối ngoài thư mục tạm | **Ghi được** |
| Gọi tiến trình con của hệ điều hành (`cmd /c`) | **Chạy được** |
| Mở cổng socket và lắng nghe mạng | **Mở được** |
| Đọc tệp bất kỳ trên ổ đĩa | **Đọc được** |
| Đọc các biến môi trường | **Đọc được** |

Cơ chế bảo vệ khi chạy mã hiện tại: **chạy trong tiến trình con độc lập** và **giới hạn thời gian 5 giây** (nhằm chống lặp vô hạn và tránh treo giao diện). Hệ thống **chưa có cơ chế cách ly** hệ thống tệp, mạng hay bộ nhớ RAM.

**Khuyến nghị sử dụng:**
- **Nên dùng:** Chạy mã do chính bạn viết trên máy tính cá nhân của bạn.
- **KHÔNG dùng:** Chạy các đoạn mã tải từ nguồn lạ chưa kiểm chứng, hoặc đặt ứng dụng lên máy chủ công cộng cho nhiều người truy cập.

### Bốn lớp bảo vệ cổng vào (Gateway)
Hệ thống bảo vệ quyền truy cập API bằng 4 lớp kiểm soát nghiêm ngặt:
1. **Loopback Only:** Chỉ lắng nghe trên `127.0.0.1`, từ chối bind `0.0.0.0`.
2. **Mã thông hành (Auth Token):** Sinh ngẫu nhiên 16-byte mỗi lần mở máy chủ, từ chối mọi yêu cầu thiếu token (`403 Forbidden`).
3. **Kiểm soát Origin:** Chặn các cuộc gọi từ trang web lạ chống CSRF (`403 Forbidden`).
4. **Khoá đường dẫn (Path Confinement):** Không cho phép mở hoặc lưu các tệp nằm ngoài thư mục dự án đã chọn (`400 Bad Request`).

---

## 5. Dành cho người phát triển

Chi tiết về thiết lập môi trường phát triển, chạy bộ kiểm thử tự động, kiểm tra giao diện và cấu trúc mã nguồn, vui lòng xem tại [docs/PHAT_TRIEN.md](docs/PHAT_TRIEN.md).

---

## 6. Bản quyền & Giấy phép

© 2026 Phạm Xuân Kiên. Bảo lưu mọi quyền. Xem [LICENSE](LICENSE).

Giấy phép độc quyền (`LicenseRef-Proprietary`): **Không được sao chép, sửa đổi hoặc phân phối lại** khi chưa có văn bản cho phép.
