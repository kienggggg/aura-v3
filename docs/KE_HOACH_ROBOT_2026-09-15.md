# Kế hoạch — hoàn thành AURA Rover (15/09/2026)

<!-- KET_CUC:DANG_LAM · 15/09/2026 -->
**Trạng thái: ĐANG LÀM. Sếp chọn hướng A ngày 15/09** (*"robot làm hướng A"*): nghiệm thu lại
trên xe thật với bản vá. Ngưỡng đăng ký trước khi đo ở `CHOT:robot-nghiem-thu` trong
`KY_LUAT_THUC_THI.md`. Hướng B, C và câu hỏi ghép đôi BLE vẫn để ngỏ.

**TẠM DỪNG 15/09, chiều**, theo lời Sếp: *"vẫn là để robot sau khi làm sau Alpha"*. Đã chuẩn bị xong:
- firmware có số phiên bản đã dịch (v2 `9b844a4`), CHƯA nạp;
- APK versionCode 3 đã dựng, CHƯA cài;
- máy đo và máy chấm đã kiểm: 12 ca gieo lỗi, 0 ca mù.

Chưa đo hàng nào của `CHOT:robot-nghiem-thu`.

Rover nằm ở repo cũ `D:\AURA_OS_v2`, cùng ba đường ra lệnh:
- firmware ESP32 trong `robot\`;
- chat AURA v2, qua `v2: core/rover.py` và `bleak`;
- app Vivo trong `android\aura-avatar`.

AURA v3 **chưa có** đường nào tới xe.

---

## 1. Đo được hôm nay, không cần xe

| thứ | đo bằng | kết quả |
|---|---|---|
| firmware dịch được | `arduino-cli compile`, core `esp32@1.0.6`, ra thư mục nháp | **ĐẠT**: 977.214 byte (74% bộ nhớ chương trình), 100 s |
| firmware trên chip là bản nào | so tệp `.bin` trong repo với bản vừa dịch | **CHƯA BIẾT**: `.bin` trong repo ghi ngày 02/08, còn mã nguồn đổi ngày 08/08 (bù lệch bánh, hạ tốc 145→120). Hai tệp lệch 48 byte, không đủ để kết luận. Firmware không in số phiên bản nào |
| test rover của v2 | `pytest tests/test_rover.py` | xanh 29/29, **trong khi bộ đọc lệnh sai 7/12 câu** (mục 2) |
| app Vivo | tệp `app-debug.apk` | dựng ngày 02/08. Không có `gradlew` trong thư mục, nên hôm nay **không dựng lại** |

## 2. Lỗi tìm ra, đã sửa trong mã (v2, commit `e172eb7`, chỉ trong máy)

Cả ba đường ra lệnh cùng mắc một bệnh: **dò chuỗi con** thay vì đọc theo từ.

| đường | đo | ví dụ | sau sửa |
|---|---|---|---|
| chat v2 | 12 câu có chữ "xe/robot": **sai 7/12, cả 7 thành TIẾN** | "robot hết điện chưa" → tiến 1,5 s ("đi" nằm trong "điện"); "xe đi lùi 2 giây" → **tiến** 2 s | 12/12 |
| nút dừng `chay_xe.py dung` | câu gửi đi là "xe dung 3 giay" | → **TIẾN 3 giây** | dừng |
| app Vivo | 18 câu, đo bằng **chính hàm Java** (trích từ tệp, dịch bằng javac) | "robot nói tiếng Việt được không" → tiến; "robot phải làm gì" → rẽ phải; "aura tự chạy lại bài test đi" → **bật tự tuần tra**. **Sai 8/18, cả 8 làm xe chuyển động** | 0/18 |

Vì sao test vẫn xanh: mọi câu *"không được cướp"* trong `test_rover.py` đều **không có** chữ
"xe/robot", nên bộ lọc chặn chúng từ vòng ngoài. Chưa ca nào thử một câu chat thường **có
nhắc tới xe**.

**Cách sửa:**
- Đọc hướng theo từ, trên chữ còn dấu.
- Bỏ "đi" khỏi bảng lệnh.
- "trái/phải" phải đi cùng một động từ rẽ (rẽ, xoay, quay, sang).
- Câu có từ hai hướng trở lên, hoặc không rõ hướng, thì xe đứng yên.
- "tự chạy" chỉ bật tự tuần tra khi câu gọi đích danh robot.

**Kiểm bằng gieo lại lỗi:**
- rover.py 5/5 phép đỏ.
- App 5/5 phép đỏ, không phép nào đỏ vì lỗi dịch.
- Trả mã về khớp SHA-256.

Một phép gieo của rover.py lúc đầu **vẫn xanh**, vì `handle_rover_command` nuốt mọi
Exception, kể cả `AssertionError` do test cài vào. Em đã sửa test sang đếm số lần gọi.

**Hành vi đổi:** "xe đi 2 giây" và "robot trái" (không có động từ rẽ) không còn làm xe
chạy nữa.

**CHƯA xong:**
- App Vivo mới sửa trong mã. **Chưa dựng APK, chưa cài**, nên điện thoại vẫn chạy bản cũ,
  bản sai 8/18.
- Chưa thử bằng giọng nói thật trên xe thật.

## 3. CHƯA chặn được

- **BLE không có ghép đôi hay xác thực.** Ai ở gần có một app BLE (ví dụ nRF Connect) cũng
  gửi được `F:255`. Chỗ dựa hiện có là firmware tự dừng khi mất nhịp sống quá 1,1 s và khi
  vật cản trong vòng 150 mm. Nhưng lớp chặn vật cản chỉ áp cho lệnh tiến.
- Không biết firmware trên chip là bản nào (mục 1).

## 4. "Hoàn thành" là hướng nào — cần Sếp chọn

**A. Nghiệm thu lại trên xe thật với bản vá** (em đề xuất làm trước):
1. Thêm số phiên bản vào firmware, in ra lúc khởi động và trong telemetry, để AURA đọc được
   chip đang chạy bản nào.
2. Dựng APK mới rồi cài lên Vivo.
3. Chạy lại 10 bước ở mục 4 của `robot\README.md`, cộng 18 câu ở mục 2 đọc bằng giọng nói.

Cần Sếp có mặt: kê bánh, bật nguồn, cắm Vivo. Em không nạp firmware khi không ai nhìn xe.

**B. Nối rover vào AURA v3**, con chatbot đang dùng:
- Chạy tiến trình riêng bằng venv v2 (đã có `bleak` 3.0.2), cùng khuôn với bộ căn chữ, để
  v3 giữ con số "2 gói ngoài".
- Danh sách đóng của v3 có trần 20 tệp, nên thêm một tệp cũng phải cố ý.
- Cần một khối CHOT với ngưỡng đăng ký trước.

**C. Tự lái bằng camera, vòng kín** (Sếp nhắc ngày 08/08: *"sau này camera tự lái sẽ bù
bằng vòng kín"*):
- Lớn nhất, cần kế hoạch riêng.
- Máy không có GPU. Model thị giác chạy trên CPU hay trên Vivo đều **CHƯA ĐO**.

## 5. Việc cần Sếp

1. Chọn hướng: A, B, C, hoặc một thứ khác.
2. Theo A: báo lúc nào xe và Vivo sẵn sàng.
3. Có muốn thêm ghép đôi BLE (mục 3) không? Core `esp32@1.0.6` đã cài trên máy có sẵn
   `BLESecurity.h`, nhưng ghép đôi với Vivo và với `bleak` thì **CHƯA ĐO**.
