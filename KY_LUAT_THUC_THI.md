# BỘ LUẬT THỰC THI DỰ ÁN & QUY CHUẨN EVIDENCE SPRINT (AURA v3)

Tài liệu này xác lập bộ quy chuẩn kỹ thuật chính thức cho toàn bộ các quy trình thử nghiệm, đánh giá và tích hợp phòng ban vào AURA v3.

---

## CHƯƠNG I: NGUYÊN TẮC QUẢN TRỊ BẰNG CHỨNG (EVIDENCE INTEGRITY)

### 1. Cấu trúc Bằng chứng Bắt buộc cho Mọi Lần Chạy
Mọi lần chạy thử nghiệm phải được lưu cô lập trong `data/evidence_sprint/runs/<run_id>/` và bắt buộc chứa đủ 5 tệp:
1. `manifest.json`:
   - `run_id`, timestamp có timezone (ISO 8601), git commit hash.
   - `prompt_sha256`, `config_sha256` (canonical hash).
   - `model_name`, `model_digest` (Ollama digest hoặc provider token), `num_ctx`, `attempts`.
   - Snapshot tài nguyên: RAM khả dụng, swap/pagefile, tiến trình Ollama.
   - `peak_ram_mb`: `null` khi chưa đo, không được ghi `0.0`.
   - Trạng thái từng gate: `PASS` / `FAIL` / `NOT_RUN`.
2. `commands.jsonl`:
   - Ghi nhận lệnh/entrypoint thực thi, timestamp bắt đầu/kết thúc.
   - `exit_code` thật từ hệ điều hành (`0=PASS`, `1=FAIL`, `2=BLOCKED`).
   - `wall_time_ms` thực tế.
3. `metrics.json`:
   - Trạng thái chung: `PASS`, `FAIL`, hoặc `BLOCKED(environment)`.
   - Chi tiết kết quả từng gate do Verifier chấm độc lập.
4. `artifacts.json`:
   - Danh sách file đầu ra nằm trong thư mục `artifacts/` của run.
   - Kích thước `size_bytes` (> 0).
   - Mã băm `sha256` tính toán độc lập từ file vật lý trên đĩa.
5. Thư mục `raw/`:
   - `error.txt` (nếu có lỗi, đã lọc sạch credentials/API keys).
   - Snapshot đầu vào bất biến (`bible.json`, `style_card.json`, prompt config...).
   - Bằng chứng thô (HTML raw, wav audio thô, stdout/stderr log).

### 2. Tính Bất Biến và Lịch Sử Append-Only
- Nghiêm cấm sửa ngược file raw hoặc artifacts của các run cũ để làm đẹp báo cáo.
- Các run lỗi thời hoặc không hợp lệ phải được đánh dấu bằng `audit.json` (append-only), chỉ rõ lý do `INVALID` hoặc `STUB_FAILED`.

---

## CHƯƠNG II: TIÊU CHUẨN KỸ THUẬT CỨNG CHO 4 PHÒNG

> **BẢNG TÊN — đọc trước, kẻo tra nhầm phòng.**
>
> Chương này gọi phòng bằng **tên chức năng**; mã và giao diện gọi bằng **mã
> danh**. Trước 02/09/2026 hai hệ thống tên ấy đụng nhau: mục 4 dưới đây tên là
> *"PHÒNG ALPHA"* và giao vai **sửa lỗi tự động**, trong khi
> `interface/noi_bo_api.py` và `interface/web/chat.html` đều giao vai ấy cho
> **Delta**, còn **Alpha** ở đó là phòng **dựng video**. Một cái tên, hai phòng.
>
> | chương này | mã danh | vai trong mã |
> |---|---|---|
> | 1. WRITER | `aura` | Writer & Core Orchestrator |
> | 2. STUDIO | `alpha` | Video Studio & Visual Cards |
> | 3. SCOUT | `zeta` | Web Scout & Fact-Checker |
> | 4. **DELTA** *(trước 02/09 ghi nhầm là "ALPHA")* | `delta` | Code Doctor & Diagnostics |
>
> Ba phòng còn lại trong mã (`beta`, `gamma`, `omega`) chưa có chương nào ở đây.
>
> **VÀ ĐÂY LÀ ĐIỀU PHẢI ĐỌC TRƯỚC MỌI TIÊU CHUẨN BÊN DƯỚI.** Đo 02/09/2026 bằng
> cách gọi `POST /api/dispatch` rồi soi đĩa (`tools/do_trang_thai_phong.py`):
>
> ```
> 02/09 sáng   chạy thật 0 · chưa chạy thật 7 · không đo được 0
>              8 tệp được KHAI là đã tạo · 0 tệp có thật · mỗi lượt 2–9 ms
> 02/09 chiều  chạy thật 1 · chưa chạy thật 6 · không đo được 0
> ```
>
> Phòng chạy thật đầu tiên là **Alpha** (mục 2 ngay dưới): nó dựng video dọc
> 720×1280 dài 60,6 s, giọng OneCore tiếng Việt, 6 hiện vật mỗi tệp một
> SHA-256, và để `ffprobe` + `blackdetect` chấm — hết 6,4 s. Xem
> `core/phong_alpha.py`.
>
> Sáu phòng còn lại vẫn trả về **đoạn văn viết sẵn**. Nên những tiêu chuẩn dưới
> đây là thứ các phòng **phải đạt**, không phải thứ chúng **đang đạt** — trừ
> mục 2. Đọc ngược lại là đúng cái bẫy mà chính Chương I cấm.


### 1. PHÒNG WRITER (Sáng tác Chương truyện)
* **Đầu vào:** `bible.json`, `style_card.json` (duy nhất 1 card) được snapshot trong `raw/`.
* **Đầu ra:** Chương truyện Markdown (1.500–2.500 từ).
* **Hard Gates bắt buộc (Tất cả phải PASS):**
  1. `word_count`: Nằm trong khoảng 1.500–2.500 từ.
  2. `characters`: Nhân vật bắt buộc (`must_appear: true`) phải xuất hiện, so khớp theo boundary từ `\b`.
  3. `mojibake`: Không chứa `U+FFFD`, không chứa ký tự điều khiển C0/C1, không chứa bidi control trái phép.
  4. `prompt_leak`: Chuẩn hóa Unicode `NFC` + `casefold` + dọn khoảng trắng, quét sạch mọi mảnh cấu hình/sentinel/heading của prompt.
  5. `path_confinement`: File đầu ra chỉ nằm trong thư mục được cấp phép (`Path.resolve` + `is_relative_to`).

### 2. PHÒNG STUDIO (Sản xuất Video Dọc Offline)
* **Đầu vào:** `STUDIO_FIXTURE.md` (120–160 từ) đã đóng băng kèm SHA-256 (nhãn `synthetic_fixture`).
* **Quy trình Thực thi 100% Offline trên Máy:**
  1. **Tổng hợp Giọng đọc (TTS):** Sử dụng Windows SAPI OneCore token `MSTTS_V110_viVN_An` xuất ra `voice.wav` thật.
  2. **Visual Cards:** Sinh tối thiểu 3 ảnh 720×1280 bằng thư viện PIL (Pillow), có nhãn `kind=generated_template` và SHA-256 riêng.
  3. **Render Video:** Dùng FFmpeg ghép audio và visual cards thành video dọc MP4 (720×1280), thời lượng 55–65 giây.
* **Cửa Kiểm định Verifier (ffprobe & filters):**
  - `ffprobe` xác nhận có luồng video 720×1280 và luồng audio non-silence (`mean_level`, `max_level` hợp lệ).
  - Filter `blackdetect` xác nhận không có khung hình đen liên tục vượt quá 2 giây.
  - Video mở xem được bình thường trên các trình phát media.
* **Cửa CHẤT LƯỢNG (thêm 02/09/2026 — bốn cửa trên chỉ đo ĐỊNH DẠNG):**
  - `freezedetect` xác nhận **không đoạn nào đứng yên quá 5 giây**.
  - Số lần **đổi cảnh ≥ 8** trên toàn video (`select='gt(scene,0.3)'`).

  > Vì sao thêm. Bản Alpha đầu tiên ĐỖ cả bốn cửa định dạng — 720×1280,
  > 60,62 s, có tiếng, 0 khung đen — nhưng đo ra:
  >
  > ```
  > 1.455 khung · 24 fps · bitrate video 30 kb/s
  > số lần đổi cảnh   2
  > đứng yên          14,08 s · 14,12 s · 14,12 s
  > ```
  >
  > Tức là bốn tấm ảnh tĩnh, mỗi tấm giữ 15 giây. Một slideshow chữ vẫn qua
  > được cả bốn cửa cũ. Hai ngưỡng này đặt **TRƯỚC** khi sửa mã, và chúng làm
  > video hiện tại **RỚT** — rớt là đúng, vì nó nói ra chặng nào còn thiếu.
  >
  > Ngưỡng lấy từ đâu: 60 s ÷ 8 = 7,5 s một lần đổi cảnh, là mức tối thiểu để
  > một video dọc không đọc ra thành slideshow. Còn 5 giây là ngưỡng riêng cho
  > TỪNG đoạn — 8 lần đổi vẫn có thể giấu một quãng đứng yên 20 giây.

### 3. PHÒNG SCOUT (Tra cứu Dữ kiện Mới & Source Receipt)
* **Đầu vào:** Tối thiểu 3 câu hỏi cần dữ kiện mới.
* **Quy trình Tra cứu & Biên nhận Nguồn:**
  1. Sử dụng tối thiểu 2 domain độc lập cho mỗi câu hỏi.
  2. Mỗi dữ kiện trích dẫn bắt buộc phải có `source_receipt` kèm theo:
     ```json
     {
       "canonical_url": "https://...",
       "fetched_at": "ISO-8601-timestamp",
       "status": 200,
       "content_sha256": "hash-sha256-cua-raw-html",
       "normalized_support_span": "doan-text-trich-dan-chinh-xac",
       "claim_ids": ["claim-01"]
     }
     ```
  3. Lưu toàn bộ file raw HTML đã crawl vào `runs/<run_id>/raw/scout/`.
  4. Verifier chấm điểm trực tiếp trên snapshot HTML đã lưu, không cào lại mạng. Cấm mọi hành vi gửi biểu mẫu hoặc external submit.

### 4. PHÒNG DELTA (Harness Sửa Lỗi Tự động & Sandbox Chống Gian)
* **Quy trình Thử nghiệm:**
  1. **Sanity Phase:** Chạy qua 5 bài test công khai (sanity tests).
  2. **Hidden Phase:** Chạy qua 5 bài test ẩn được đóng băng (model không thấy test code và expected diff).
* **7 Khóa Chống Gian Lận (Anti-Cheat Locks):**
  1. Sandbox cô lập, ngắt hoàn toàn kết nối mạng (`no-network`).
     **CHƯA CHẶN ĐƯỢC.** Đo 01/09/2026 trên `core/polyglot.py`: mã chạy ở
     gốc kho với đủ quyền tài khoản Windows và GHI ĐƯỢC tệp ra ngoài thư
     mục tạm; chỉ có một trần thời gian. Và `alpha.py::verify_anti_cheat_keys()`
     trả về bảy chuỗi `"PASS"` gõ cứng — không đo gì cả.
  2. Giới hạn ngân sách tài nguyên nghiêm ngặt (timeout, CPU/RAM/disk budget).
  3. Chặn mã sửa đổi bộ test hoặc import mock thư viện kiểm thử.
  4. Kiểm tra cú pháp và tính an toàn bằng AST parser trước khi thực thi.
  5. Chạy đầy đủ regression suite sau khi patch.
  6. Patch chỉ nằm trong sandbox, tuyệt đối không áp ngược vào repo AURA thật.

---

## CHƯƠNG III: CƠ CHẾ BẢO MẬT & BỘ LỌC DỮ LIỆU NHẠY CẢM (REDACTION)
- Mọi file log lỗi (`raw/error.txt`) phải đi qua bộ lọc tập trung (Centralized Redactor).
- Tự động che giấu mọi dạng key/token: Bearer tokens, OpenAI/Gemini/Anthropic/OpenRouter API keys, Basic Auth credentials trong URL.
- Test bộ lọc bằng token giả; tuyệt đối không đưa key thật vào test fixture hoặc log commit.
