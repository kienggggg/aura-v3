# Kế hoạch — AURA tự đăng truyện lên Wattpad và Sáng Tác Việt (14/09/2026)

<!-- KET_CUC:DANG_LAM · 14/09/2026 -->
**Trạng thái: ĐANG LÀM. Sếp duyệt ngày 14/09.** Chưa viết dòng mã nào, chưa tải gói
nào.
- Chế độ đầu lấy đúng đề xuất: `nháp`.
- Dạng đăng chưa chọn; tới vòng 2 mới cần.
- **Vòng 0 xong ngày 14/09** (`CHOT:dang-vong-0`):
  - Wattpad **ĐẠT** cả bốn hàng: 10/10 lần, tối đa 18,8 s, 0 lần đăng công khai, hai
    truyện đã đăng của Sếp không bị đụng tới.
  - Sáng Tác Việt **KHÔNG ĐO ĐƯỢC**: tài khoản cần tham gia STV hơn 1000 phút mới được
    tạo truyện.
- **Vòng 2 xong ngày 14/09** (`CHOT:dang-vong-2`), dạng tuyển tập Sếp chọn:
  - 5/5 kịch bản thật của phòng viết thành chương nháp trong *"Truyện ngắn AURA"*.
  - 0 chương trùng, 0 lần đăng công khai, mỗi chương ≤ 19,2 s, truyện đã đăng của Sếp giống
    hệt trước và sau.
  - Còn hở: chưa có lịch tự chạy hàng chờ.
- Vòng 1 (tải browser-use) chờ Sếp duyệt riêng.

Sếp giao ngày 14/09: *việc gì tự động được thì tự động hoàn toàn*, dù mỗi nền tảng
có một quy trình đăng khác nhau. Cùng ngày Sếp cấp quyền đăng và nới cho AURA giữ
phiên đăng nhập của **một hồ sơ trình duyệt riêng** chỉ dùng để đăng (`CLAUDE.md`
§2). `CLAUDE.md` §7 yêu cầu dựng hệ thống mới thì gửi kế hoạch trước. Chỗ nào chưa
chạy được thì ghi **CHƯA ĐO**.

---

## 1. Đã kiểm gì, ngày 14/09

| điều | kiểm bằng | kết quả |
|---|---|---|
| Wattpad có API chính thức để đăng | tìm kiếm | **KHÔNG thấy** — chỉ có thư viện không chính thức, và chúng dùng để ĐỌC. Muốn đăng thì phải qua trình duyệt |
| Điều khoản Wattpad về tự động hoá | đọc trang Policies bằng trình duyệt | cấm cào nội dung (*"crawl", "spider"*) và cấm gây tải bất hợp lý; **không thấy** câu nào về việc tự đăng truyện của chính mình |
| Wattpad về truyện do AI viết | trang Content Guidelines chính thức | chỉ cấm deepfake AI về người thật khi họ không đồng ý. **Không thấy** luật bắt dán nhãn truyện AI. Mấy trang tổng hợp nói "phải dán nhãn", nhưng không khớp nguồn gốc nên em không dùng |
| Sáng Tác Việt nhận truyện sáng tác | kết quả tìm kiếm: có trang tác giả `writer.php` | **CHƯA mở trực tiếp**. Tên miền đổi nhiều (.com / .pro / .vip), cần Sếp chỉ đúng trang |
| công cụ trên máy | `pip list`, PATH | Playwright 1.60 + Chromium và easyocr 1.7.2: **chỉ có trong venv của v2**. Browser-use, Camoufox, PaddleOCR, dots.ocr: **chưa cài** |

**Kho công nghệ ≠ máy.** Trong kho, browser-use chỉ có tên trong một danh sách, còn
Camoufox ở bậc `DISCOVERED`. Đúng bài *"nhãn đã đo không mang ngày"* ghi ngày 10/09:
có trong kho không có nghĩa là đang chạy được.

## 2. Thiết kế

**Tiến trình riêng, venv riêng** — cùng khuôn với bộ căn chữ. Không đưa Playwright
vào `requirements.txt` của v3, để giữ con số "2 gói ngoài". Vòng đầu dùng lại
Playwright và Chromium đã có ở venv v2, nên **không phải tải gì**.

**Mỗi nền tảng một hồ sơ trình duyệt riêng**, để ngoài git và ngoài thư mục dự án
(ví dụ `F:\aura-dang\wattpad`). Sếp mở hồ sơ ấy và tự đăng nhập một lần. AURA dùng
lại phiên đăng nhập ấy, không bao giờ thấy mật khẩu.

**Đường đăng có hai lớp:**
1. **Kịch bản cố định cho từng nền tảng.**
   - Tìm nút theo chữ hiển thị và vai trò trợ năng, không theo tên class CSS (thứ
     dễ đổi nhất).
   - Sau mỗi bước, kiểm xem đã tới đúng trang chưa.
   - Không thấy thứ phải thấy thì FAIL-CLOSED: chụp màn hình, dừng lại, báo Sếp.
     Không đoán.
2. **Lớp thích nghi**, dùng khi kịch bản gãy vì giao diện đổi. Có hai cách: browser-use
   (model đọc trang rồi tự tìm nút), hoặc OCR (tìm nút theo chữ trên ảnh chụp màn
   hình). **CHƯA ĐO** với model trên máy. Nếu model 4B không làm nổi thì lớp này
   không dùng, và máy báo gãy để sửa kịch bản.

**Không né chặn bot:**
- dùng trình duyệt thật, không giả vân tay, không giải CAPTCHA;
- đăng theo nhịp của người, không dồn dập, vì điều khoản Wattpad cấm gây tải bất hợp lý;
- gặp CAPTCHA hay bị đòi xác minh thì dừng, chụp màn hình, báo Sếp.

**Sổ đăng.** Mỗi lượt ghi: nền tảng, đường link, giờ, SHA-256 của văn bản, và ảnh chụp
trang sau khi đăng. Lượt hỏng cũng vào sổ, theo luật mọi lượt đều vào sổ.

**Chỉ đăng bản đã qua mọi cửa** của phòng viết.

**Hai chế độ:** `nháp` (AURA lưu bản nháp trên nền tảng, Sếp bấm đăng) và `đăng thẳng`.
Đổi bằng một cờ. Đề xuất bắt đầu ở `nháp` tới khi truyện đạt mức 4/5 truyện Sếp
muốn đọc tiếp; hiện mới 0/2.

**Dạng đăng — cần Sếp chọn.** Một truyện của phòng viết dài khoảng 230 từ (13 câu),
ngắn hơn nhiều so với một chương thường gặp trên Wattpad (con số này em **ước**,
CHƯA ĐO). Có hai cách:
- mỗi truyện một "story" riêng;
- gom thành một tuyển tập: một story, mỗi truyện là một chương.

## 3. Phép đo — đăng ký ngưỡng TRƯỚC khi viết mã (sau khi Sếp duyệt)

**Vòng 0 — không tải gì.**
- Mở Chromium của Playwright (venv v2) với hồ sơ riêng; Sếp tự đăng nhập.
- Kịch bản ghi nội dung thử vào **MỘT bản nháp cố định** trên mỗi nền tảng, lặp 10
  lần. Không tạo rồi xoá: xoá dữ liệu trên tài khoản của Sếp là việc em không làm.
- Ngưỡng đề xuất:
  - kịch bản thành công ≥ 9/10 lần;
  - mỗi lần < 60 giây;
  - gặp CAPTCHA thì ghi lại và báo — đó là chuyện của nền tảng, không phải lỗi mã.

**Vòng 1 — lớp thích nghi, phải tải thêm gói nên cần Sếp duyệt riêng** (em sẽ nêu
tên gói, nguồn, cỡ).
- Chạy browser-use với `qwen3.5:4b`: 10 lượt, cùng một nhiệm vụ, trên trang nháp.
  Ngưỡng ≥ 7/10 thì mới được dùng.
- Song song, đo easyocr (đã có trên máy): tìm đúng nút theo chữ trên ảnh chụp.

**Vòng 2 — nối vào phòng viết:** bản đã qua mọi cửa thì đăng theo chế độ đang đặt,
rồi ghi sổ.

## 4. Việc cần Sếp

1. Duyệt kế hoạch.
2. Chỉ đúng trang Sáng Tác Việt đang dùng, và cho biết đã có tài khoản tác giả trên
   Sáng Tác Việt và tài khoản Wattpad chưa.
3. Chọn dạng đăng: mỗi truyện một story, hay gom thành tuyển tập.
4. Chọn chế độ đầu: `nháp` hay `đăng thẳng`.
5. Đến vòng 0: Sếp tự đăng nhập vào hồ sơ trình duyệt. Em không gõ mật khẩu.

## 5. CHƯA chặn được, và rủi ro

- **Giao diện đổi:** kịch bản gãy thì FAIL-CLOSED, không đăng sai chỗ. Nhưng lớp tự
  thích nghi thì **CHƯA ĐO**, nên chưa thể nói là "ứng phó được".
- **Phiên đăng nhập nằm trên đĩa:** ai lấy được thư mục hồ sơ là vào được tài khoản.
  Hồ sơ để ngoài git và ngoài dự án, nhưng **CHƯA mã hoá**.
- **Nền tảng vẫn có thể khoá tài khoản vì tự động hoá**, dù điều khoản không cấm rõ.
  Điều khoản chỉ nói tới việc cào nội dung và gây tải; không có gì đảm bảo ngoài đó.
- **Chất lượng:** mới 0/2 truyện Sếp đọc là đăng được. Đăng thẳng lúc này tức là đưa
  những truyện ấy lên dưới tên của Sếp.
