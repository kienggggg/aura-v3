# Nghiệm thu bản vá cửa thực thi — 22/08/2026

*Claude chạy lại bằng ĐÚNG venv của kho, và tự thử hàng rào. Hai việc xin sửa
đều xong. Họ còn siết chặt hơn cả mô tả.*

---

## 1. Chạy bằng venv của kho, không phải môi trường tạm

Antigravity chạy test bằng `uv run --with pytest-asyncio --with aiohttp ...` —
một môi trường dựng tạm, không phải `venv/` của kho. Nên tôi kiểm lại:

```
venv chính có pytest_asyncio ?   KHÔNG CÓ
venv chính có pytest_aiohttp ?   KHÔNG CÓ
```

Chạy bằng chính venv của kho:

```
613 passed, 1 skipped in 63.79s
```

**Đạt.** Test mới viết theo dạng lớp `AioHTTPTestCase` nên không cần gói thứ tư
— đúng thứ tôi xin ở bản giao 22/08. `CLAUDE.md` §1 chốt v3 chỉ có 3 gói ngoài,
và điều đó vẫn giữ.

Nhưng xin ghi nhớ cho lần sau: **chạy bằng venv của kho.** Một bộ test xanh
trong môi trường tạm không chứng minh nó xanh ở nơi nó sẽ sống.

## 2. Hai việc xin sửa — xong cả

### Băng-rôn

```
* Chay ma/Trace/E1: TAT MAC DINH (/api/chay, /api/trace, /api/dinh_vi_loi khoa;
                    mo/sua/kiem tra/luu van hoat dong)
```

Bật cờ thì đổi thành `DA BAT CO CHU DICH (...)`. Cả ba cổng được gọi tên.

### `/api/status`

```json
"code_execution_enabled": false,
"cac_cong_thuc_thi": ["/api/chay", "/api/trace", "/api/dinh_vi_loi"],
"security": { "execution_gate": true, ... }
```

### `/api/trace` — lỗ hổng hôm qua ĐÃ BỊT

```
hôm qua:  trace_du · tong_buoc 8 · 4 sự kiện   (chạy mã trong khi app khai TẮT)
hôm nay:  {"trang_thai": "bi_khoa", "error": "Chạy mã/test đang tắt mặc định"}
```

## 3. Siết chặt hơn cả mô tả — ba chỗ tôi thử được

```
node_id_test từ client          400 "Không nhận node_id_test từ client;
                                     chỉ dùng tep_test"
tep_test ngoài tests/           "Tệp test không hợp lệ (phải nằm dưới tests/)"
tệp nguồn CHƯA MỞ trong phiên   403 "Tệp nguồn chưa được mở trong phiên làm việc"
tệp nguồn ĐÃ MỞ                 chạy bình thường
```

Chặn `node_id_test` là chỗ hay nhất và **không có trong kế hoạch**: nó bỏ hẳn
đường mà client tự đặt tên một nút pytest bất kỳ. Server tự chọn test bằng luật
tất định.

## 4. Một ghi chú, không phải lỗi

`tep_nguon` chịu danh sách trắng của phiên; `tep_test` thì **chỉ** bị buộc nằm
dưới `tests/`, không bị soi theo phiên. Thử:

```
nguồn = dong_ho.py (đã mở) + test = test_kiem_tien.py (chưa mở)  ->  CHẠY
```

Nên khi cờ thực thi **bật có chủ đích**, đường tôi nêu hôm qua — ghi tệp vào
`tests/` rồi chạy nó — vẫn còn. Nhưng lúc ấy băng-rôn đã ghi rõ
`DA BAT CO CHU DICH`, nên **đây không phải lời hứa sai nữa**; đó chính là nghĩa
của việc bật cờ.

Nếu muốn siết thêm thì cho `tep_test` chịu chung danh sách phiên. Không gấp.

## 5. Danh sách việc — sạch

```
/api/trace chạy mã khi app khai TẮT      ĐÃ BỊT
băng-rôn nói sai về quyền                 ĐÃ SỬA
/api/status thiếu thông tin cổng          ĐÃ THÊM
613 test bằng venv của kho                XANH
```

Không còn mục nào đang mở.
