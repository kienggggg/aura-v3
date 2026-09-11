# Toàn văn bốn ghi chú lịch sử của `CLAUDE.md` mục 1

Tách ra 11/09/2026 khi `CLAUDE.md` lên **28.034/32.000 byte (88% trần)**. Bốn
khối dưới đây chiếm **3.094 byte** trong tệp nạp MỌI phiên, mà phần lớn là kể
chuyện — `CLAUDE.md` giữ lại phần cơ chế và con số, toàn văn nằm ở đây.

Cùng lối đã dùng 06/09/2026 khi tách `SO_BENH_AN.md`: **cắt phần kể, giữ phần
số.** Cắt mất con số thì luật thành lời răn suông — nên mỗi tóm tắt ở
`CLAUDE.md` đều còn mang số của nó.

---

## 1. `AURA-OS-V2` trên GitHub — thứ bị cấm là LỊCH SỬ, không phải MÃ

> Câu *"LỊCH SỬ của `D:\AURA_OS_v2` không được đẩy lên GitHub"* trước
> 02/09/2026 viết gọn là *"repo cũ không được đẩy lên GitHub"*, và đọc ra thành
> "v2 không có trên GitHub". Sai. Sếp nhắc, đo lại thì:
> `github.com/kienggggg/AURA-OS-V2` **đang công khai từ 13/08** — nhưng là một
> **ảnh chụp sạch**: 1 commit, 730 tệp, không mang lịch sử, email tác giả đã là
> `noreply`. Quét toàn bộ lịch sử kho ấy: **0 khoá thật**, 0 tệp `.env` bị theo
> dõi, 0 chỗ gán `api_key`/`token` giá trị dài; commit `88e8c07` **không có
> trong đó**.
>
> Thứ bị cấm là **lịch sử**, không phải **mã**. Viết gộp hai thứ làm một thì
> lần sau có người đọc luật này rồi tưởng mình vừa làm lộ khoá — hoặc tệ hơn,
> tưởng đẩy ảnh chụp sạch cũng là vi phạm rồi bỏ mất một việc làm được.

---

## 2. Bộ căn chữ cố ý nằm ngoài con số "19 tệp · 2 gói ngoài"

> **BỘ CĂN CHỮ KHÔNG NẰM TRONG CON SỐ ẤY, VÀ ĐÓ LÀ CỐ Ý** (07/09/2026).
> `core/can_chu.py` sinh phụ đề karaoke theo từng từ, nhưng nó gọi
> `faster-whisper` qua **tiến trình riêng, venv riêng ở `F:\aura-stt\venv`** —
> đúng khuôn `node --check` / `bash -n` của phòng `epsilon`.
>
> Đưa nó vào `requirements.txt` thì kéo theo `ctranslate2` · `onnxruntime` ·
> `av` · `numpy` · `tokenizers` · `huggingface-hub` — đo được **273 MB và 10+
> gói**, cộng 605 MB model. Tức **2 → 12**, cho một tính năng. Không có bộ căn
> thì `KHONG_DO_DUOC` và video vẫn dựng xong với phụ đề theo đoạn như cũ —
> thiếu một cái thước không phải là hỏng.

---

## 3. App Thẻ lớn lên ngoài tầm mắt suốt 14 ngày

> **App Thẻ đã tách sang kho riêng ngày 02/09/2026** —
> https://github.com/kienggggg/app-the — mang theo `libcst` (gói ngoài thứ ba
> cũ) và 8 tệp / 5.509 dòng. Hai bên không dùng chung tệp mã nào.
>
> Và đây là chỗ đắt: đến 02/09 hàng rào chỉ soi `aura_chat.py`, nên App Thẻ —
> **dài hơn phần được canh** — lớn lên ngoài tầm mắt suốt từ 19/08. Bắt được
> bằng cách chạy lại phép đo từ hai cửa vào, không bằng đọc lại.
>
> Trước 02/09 dòng đầu mục này còn ghi **"đúng 17 tệp mã · 4.248 dòng"** trong
> khi danh sách đóng đã lên 19. Câu tóm tắt tụt lại sau phép đo, và không ai
> sửa vì không ai chạy lại.

---

## 4. Luật từng mô tả một cấu trúc không còn tồn tại

> Mục này trước 03/09/2026 ghi **"hai danh sách đóng, hai trần riêng: `V3_CHAT`
> (trần 20) và `V3_THE` (trần 10)"**, kèm một đoạn giải thích vì sao không được
> gộp hai làm một. Đọc thì thuyết phục; đo thì sai: App Thẻ tách sang kho riêng
> ngày 02/09, `V3_THE` đi theo, và tệp này chỉ còn **một** danh sách. Luật mô tả
> một cấu trúc không còn tồn tại — cùng bệnh với câu "đúng 17 tệp" từng tụt lại
> sau phép đo.
>
> Đoạn về App Thẻ nằm ngoài tầm canh (8 tệp · 5.509 dòng) vẫn đúng **về mặt
> lịch sử** và là lý do sinh ra hàng rào thứ hai; nay nó thuộc kho `app-the`.
