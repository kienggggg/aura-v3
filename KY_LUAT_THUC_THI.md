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

### 1b. KỊCH BẢN CHO STUDIO (`core/viet_truyen.py`, 03/09/2026)

AURA viết kịch bản, Alpha dựng video. Mối nối là tham số `van_ban` đã có sẵn của
`dung_video()`.

* **Ngưỡng, đặt TRƯỚC khi viết mã:**
  - Số từ **215–250**.
  - **≥ 13 câu khác nhau**.
  - Không câu nào lặp **quá 2 lần**.
  - Trần **3 lần sinh** cho một kịch bản, và **phải báo ra đã thử mấy lần**.

  > Ngưỡng lấy từ đâu. Tốc độ giọng OneCore đo trên 5 mẫu: 3,58–3,95 từ/giây,
  > văn xuôi ở cận trên. Lấy 3,9 → cửa sổ 55–65 s = 215–250 từ. Đã kiểm bằng
  > dây chuyền thật: **235 từ / 15 câu → PASS**; **266 từ → 67,3 s, FAIL**.
  > 13 câu là số thẻ ở 60 giây (`round(60 / 4,5)`).

* **MÁY đếm, model không đếm.** Đo 5 lượt, yêu cầu 232 từ:
  `214 · 346 · 273 · 190 · 134` — **0/5 đúng số từ**, lệch −42% đến +49%.
  Ràng buộc *số câu* thì model giữ được **4/5**. Nhưng từ/câu dao động
  **11,2–24,7**, nên số câu cũng không điều khiển được độ dài. Không núm nào của
  model làm được việc này.

* **Cách xử lý: xin dài dư rồi CẮT GIỮA.** Xin ~320 từ, giữ câu mở và các câu
  cuối, bỏ dần câu ở giữa. Đo 5 lượt:

  ```
  không cắt      1/5 lọt cửa
  cắt từ DƯỚI    4/5 lọt cửa   — nhưng MẤT KẾT TRUYỆN
  cắt từ GIỮA    4/5 lọt cửa   — giữ được mở và kết
  ```

  Cùng tỉ lệ, nhưng câu kết khác hẳn: cắt dưới cho *"Sự im lặng giữa hai người
  không nặng nề mà đầy chất thơ"* (cắt ngang), cắt giữa cho *"Mỗi giọt mưa rơi
  xuống đất đều là một lời cầu nguyện"* (kết thật).

* **Trần cứng 19,2 từ/câu.** Lượt trượt duy nhất không hỏng vì dài — sau khi cắt
  nó đúng 237 từ — mà vì chỉ còn **11 câu**. Nó viết 442 từ trong 21 câu, tức
  21 từ/câu, trong khi `250 ÷ 13 = 19,2` là trần. Viết câu dài hơn thế thì hai
  ràng buộc **không thể cùng đúng**, và không cách cắt nào cứu được. Máy phải đo
  từ/câu **trước khi cắt** và sinh lại ngay, khỏi phí công.

* **Ba trạng thái, không gộp:** `DAT` · `KHONG_DAT` (đo được mà ngoài cửa sổ,
  kèm số) · `KHONG_DO_DUOC` (Ollama tắt, hết giờ, model không trả lời).

* **CHƯA CHẶN ĐƯỢC — không viết là đã chặn:** cửa này đếm từ, đếm câu, đếm lặp.
  Nó **không** biết truyện hay hay dở, có mạch lạc không. Mười lăm câu vô nghĩa
  nhưng khác nhau vẫn lọt sạch. Model cũng có thể viết 15 câu khác chuỗi mà cùng
  một ý — cửa mù chỗ đó.

* **Giá phải nói ra:** mỗi lượt sinh 64–96 giây. Trần 3 lần = tới ~4,8 phút cho
  một kịch bản, chưa tính 30 giây dựng video.

### 2. PHÒNG STUDIO (Sản xuất Video Dọc Offline)
* **Đầu vào:** `STUDIO_FIXTURE.md` (**215–250 từ**, **≥13 câu khác nhau**) đã
  đóng băng kèm SHA-256 (nhãn `synthetic_fixture`).

  > Trước 03/09/2026 dòng này ghi **120–160 từ**, và nó MÂU THUẪN với chính yêu
  > cầu video 55–65 s ngay bên dưới. Đo tốc độ giọng OneCore trên năm mẫu:
  >
  > ```
  >  80 từ (lặp)   22,38 s   3,58 từ/s
  > 154 từ (lặp)   42,05 s   3,66
  > 240 từ (lặp)   65,93 s   3,64
  > 179 từ (văn)   46,38 s   3,86
  > 266 từ (văn)   67,30 s   3,95
  > ```
  >
  > Ở mọi tốc độ ấy, một đề 160 từ đọc hết **nhiều nhất 41,5 s** — không cách nào
  > chạm 55 s. Hai con số chưa bao giờ giao nhau; thứ âm thầm hoà giải chúng là
  > `_dai_ngan_lai()` đệm im lặng, và **15,23 giây câm chính là chỗ chúng va
  > nhau**. Cửa nội dung bên dưới làm chỗ va ấy kêu thành tiếng.
  >
  > Văn xuôi đọc nhanh hơn văn lặp ~7%, nên ngân sách lấy 3,9 từ/s: 55 s → 215
  > từ, 65 s → 254 từ. Đã kiểm: **235 từ / 15 câu → PASS**; **266 từ → 67,3 s,
  > FAIL vì quá dài**.
  >
  > Đề cũ giữ lại nguyên vẹn ở `STUDIO_FIXTURE_LAP.md` làm **ca đối chứng âm** —
  > nó là bằng chứng đã kiểm rằng một kịch bản rác vẫn qua sạch mọi cửa hình
  > dạng. Xoá nó đi là mất vật chứng.
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
* **Cửa PHỤ ĐỀ & NHẠC NỀN (thêm 02/09/2026, tối):**
  - MP4 phải có **luồng phụ đề** (`ffprobe` thấy `codec_type=subtitle`), và tệp
    `.srt` là một hiện vật riêng kèm SHA-256.
  - Chữ phải **NUNG THẲNG VÀO HÌNH**, không chỉ nằm ở luồng rời. Đo bằng cách so
    khung của bản chưa nung với bản đã nung: **dải dưới 30% chênh ≥ 3,0** trên
    thang xám, **dải trên 30% chênh ≤ 1,0**.

    > Vì sao cần cả hai. Luồng phụ đề rời thì `ffprobe` đọc được — nên nó đo
    > được — nhưng trên Facebook/TikTok người ta lướt và xem TẮT TIẾNG, mà
    > luồng rời thường không tự bật. Chữ nung vào hình thì luôn thấy, nhưng máy
    > không đọc ra được. Giữ cả hai: luồng rời để KIỂM, chữ nung để XEM.
    >
    > Ngưỡng lấy từ đâu: đo trên video thật, nung bằng `subtitles` + libass ra
    > **dải dưới 10,37 · dải trên 0,14**. Đặt 3,0 và 1,0 là chừa biên rộng cho
    > cả hai phía, và hai con số ấy phân biệt được "có nung" với "không nung"
    > mà không bị màu nền thẻ đánh lừa.
  - Số dòng phụ đề **≥ số thẻ**, và mốc kết thúc của dòng cuối **≤ thời lượng
    video** — phụ đề chạy quá phim là phụ đề sai.
  - Âm thanh cuối phải là **hỗn hợp giọng + nhạc**, độ ồn tích hợp trong khoảng
    **−18 đến −12 LUFS** (`loudnorm`).
  - Nền nhạc phải **thấp hơn giọng ≥ 12 dB**, đo trên hai tệp RIÊNG trước khi
    trộn. Nhạc át giọng thì video vô dụng, mà LUFS của bản trộn không nói được
    điều đó.

  > Ngưỡng lấy từ đâu. Giọng đọc một mình đo được **−17,04 LUFS**; các nền phát
  > hành thường quanh −14 (YouTube) đến −16 (TikTok), nên khoảng −18…−12 vừa
  > chứa cả hai vừa đủ rộng để không phải chỉnh mỗi lần đổi giọng. Còn 12 dB là
  > mức chênh tối thiểu quen dùng khi lồng nhạc dưới lời đọc.
  >
  > Nhạc ở đây là **âm sinh bằng ffmpeg**, nhãn `generated_tone_bed` — không
  > phải nhạc thật, và không được khai là nhạc thật.

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

* **Cửa NỘI DUNG (thêm 03/09/2026 — mọi cửa trên chỉ đo HÌNH DẠNG):**
  - Tỉ lệ khối phụ đề **khác nhau ≥ 0,80** trên tổng số khối.
  - Không khối phụ đề nào chiếm **quá 0,25** tổng số khối.
  - Quãng **không có giọng nói** dài nhất trong luồng giọng (đo TRƯỚC khi trộn
    nhạc) **≤ 2,0 giây**.

  > Vì sao thêm. Đề đã đóng băng `STUDIO_FIXTURE.md` là **một câu lặp 22 lần** —
  > `"Kael nhìn lên bầu trời đỏ rực."` ×22 — và video dựng từ nó **qua sạch sẽ
  > mọi cửa trên**. Đo ngày 03/09/2026:
  >
  > ```
  > 154 từ  ->  đọc hết 41,27 s
  > 15,23 s / 56,50 s  (27%)  KHÔNG CÓ GIỌNG NÓI
  > 13 khối phụ đề · 1 khối có nội dung khác nhau  (tỉ lệ 0,077)
  > ```
  >
  > Không cửa nào kêu, vì mỗi cửa đo đúng phần nó đo: nền thẻ xoay theo góc vàng
  > nên `scdet` vẫn đếm đủ 12 lần đổi cảnh dù chữ y hệt; nhạc nền phủ kín 15 giây
  > câm nên `silencedetect` trên bản trộn không thấy gì; `loudnorm` vẫn trong
  > khoảng vì nhạc gánh phần im. **Cửa hình dạng không thay được cửa nội dung.**
  >
  > Ngưỡng lấy từ đâu. Cho một văn bản 13 câu KHÁC NHAU, 179 từ, đọc bằng đúng
  > giọng OneCore ấy: **16 khoảng nghỉ**, dài nhất **0,77 s**, trung bình 0,59 s.
  > Đặt 2,0 s là 2,6 lần khoảng nghỉ tự nhiên dài nhất — đủ rộng để không bắt oan
  > nhịp thở giữa câu, mà vẫn cách 15,23 s của bản đệm rất xa. Còn 0,80 và 0,25:
  > đề hiện tại cho 0,077 và 1,00; văn bản 13 câu khác nhau cho 1,00 và 0,077.
  > Hai ngưỡng nằm giữa, chừa chỗ cho một câu điệp khúc lặp vài lần.
  >
  > `silencedetect` phải dò ở `d=0,5` — THẤP hơn ngưỡng chấm 2,0. Đặt bằng nhau
  > thì mọi quãng ngắn hơn bị giấu, đúng lỗi đã mắc với `freezedetect`.
  >
  > Ba ngưỡng này đặt **TRƯỚC** khi sửa mã, và chúng làm đề đóng băng hiện tại
  > **RỚT**. Rớt là đúng.

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

### 5. NĂM PHÒNG NỘI BỘ CÒN LẠI (`core/phong_noi_bo.py`, 03/09/2026)

Đo qua `POST /api/dispatch` sáng 03/09: **chạy thật 2 · chưa chạy thật 5**. Năm
phòng `beta` · `delta` · `gamma` · `omega` · `zeta` đều trả một đoạn văn viết
sẵn rồi khai một tệp không tồn tại.

Chỗ chua nhất là `gamma` — **phòng đo lường**. Nó in *"Số liệu đo đạc thời gian
thực"* rồi báo bốn con số gõ tay, và cả bốn đều sai:

```
RAM        4.2 GB / 16.0 GB    thật: 9,11 / 12,61 GB
Hard Gates 714/714 tests       thật: 692 tests lúc ấy
Tốc độ     38.4 tokens/giây    thật: 5,02–6,69 tok/s (thổi 5,7–7,6 lần)
Latency    42 ms               chưa từng đo
```

* **Mỗi phòng để lại MỘT hiện vật thật** kèm SHA-256 tính từ đĩa:

  | phòng | việc thật | hiện vật | ai kiểm chéo được |
  |---|---|---|---|
  | `gamma` | RAM · số bài test · tốc độ sinh | `metrics.json` | `ctypes` gọi thẳng Win32 · `pytest --collect-only` |
  | `omega` | đọc sổ cái, tính thống kê | `bao_cao_so_cai.md` | đếm lại dòng bằng tay |
  | `zeta` | tra mạng thật | `bien_nhan.json` | mở URL ra đối chiếu, kèm SHA-256 nội dung |
  | `delta` | quét AST thật | `chan_doan.json` | gọi `ast` tay rồi so số hàm/lớp |
  | `beta` | A/B hai biến thể lời nhắc | `ab_test.json` | chấm bằng chính `do_kich_ban` |

* **KHÔNG dùng `psutil`.** Nó không có trong `requirements.txt`, và chính nhánh
  `except` khi thiếu nó đã đẻ ra con số giả `4.2/16.0`. `ctypes` gọi thẳng
  `GlobalMemoryStatusEx` — đọc được, không thêm gói ngoài nào.

* **`omega` KHÔNG được lấy `so_cai.jsonl` làm bằng chứng của mình.** Mọi phòng
  đều ghi vào đó, nên `tools/do_trang_thai_phong.py` cố ý loại nó ra khỏi ảnh
  chụp. Phòng nào lấy dòng sổ của mình làm bằng chứng thì phòng nào cũng "đạt".

* **`zeta` tra được mà không ra nguồn nào là `FAIL`, không phải `KHONG_CHAY_DUOC`
  và tuyệt đối không phải `PASS`.** Nó đã CHẠY, chỉ là kết quả rỗng.

* **`delta` KHÔNG tự sửa mã.** Bản cũ khai có `Auto-Fix` — không có, và sẽ không
  có: sửa mã hộ người khác mà không ai duyệt là chuyện khác hẳn với đọc mã.

* **`beta` phải tự nói ra khi N quá nhỏ.** Mỗi biến thể tốn một lượt gọi model
  64–96 giây, nên mặc định `so_lan=1` để lọt trần 360 s của máy đo phòng. Một
  lượt mỗi bên **không kết luận được gì**, và trường `du_de_ket_luan` nói thẳng
  điều đó thay vì đưa ra một tỉ lệ trông như bằng chứng. Đủ để kết luận: **≥ 3**.

  > Việc này CÓ THẬT. Ngày 03/09 tôi thêm *"mỗi câu KHÔNG quá 15 từ"* vào lời
  > nhắc của `core/viet_truyen.py` để chữa trần 19,2 từ/câu. Nó chữa được, nhưng
  > kéo tụt tổng độ dài — chạy thật ra 171 · 163 · 187 từ, trượt cả ba vì quá
  > ngắn. Không ai phát hiện bằng đọc lời nhắc. Chạy `beta` lần đầu thì nó dựng
  > lại đúng ca ấy: biến thể A cho 304 từ → ĐẠT, biến thể B cho 197 từ → trượt.

* **MỘT tệp cho cả năm phòng, không phải năm tệp.** `V3_PHONG` trần 8, đang 4;
  năm mô-đun riêng là 9 — vượt trần. Hàng rào ấy dựng cùng ngày và nó đang làm
  đúng việc: bắt người viết phải cố ý.

* **`api_chay_pipeline` — ĐÃ SỬA cùng ngày.** Bản cũ 91 dòng, gõ tay
  `"trang_thai": "PASS"` **5 lần**, không gọi phòng nào, nhưng CÓ ghi vào
  `so_cai.jsonl` với `"status": "PASS"` — dấu vết của việc chưa từng xảy ra. Đó
  là lỗ trong chính cửa fail-closed: cửa hỏi *"có để lại byte nào không?"*, và
  một hàm ghi sổ về việc nó không làm thì trả lời được câu ấy.

  Bản mới gọi phòng thật và **nối đầu ra vào đầu vào**: kịch bản `aura` viết ra
  đi thẳng vào `van_ban` của `alpha`. Năm lượt gọi phòng độc lập thì không phải
  dây chuyền. Chạy thật:

  ```
  status PASS · 5/5 bước đạt · 22 hiện vật · 166 s
  1 zeta   PASS    8.165 ms   1 hiện vật thật
  2 aura   PASS  106.406 ms   244 từ · 13 câu khác nhau · sinh 1/3 lần
  3 alpha  PASS   28.484 ms   720×1280 · 58,55 s · 18 hiện vật
  4 omega  PASS       23 ms   1 hiện vật thật
  5 gamma  PASS   23.234 ms   1 hiện vật thật
  ```

  **BỐN trạng thái cho mỗi bước, không gộp:** `PASS` · `FAIL` · `KHONG_CHAY_DUOC`
  · **`CHUA_CHAY`** (bước trước gãy nên bước này không chạy). Trạng thái thứ tư
  là thứ dễ bịa nhất: đánh nó thành `PASS` thì bảng đọc ra "cả năm bước xong",
  đánh thành `FAIL` thì đọc ra "nó chạy rồi mà hỏng" — cả hai sai theo một cách
  khó bắt.

  Lượt ghi sổ **không được nuốt lỗi**. Bản cũ bọc trong `except Exception: pass`;
  ghi sổ hỏng là tin đáng biết, vì nó nghĩa là mọi phép đo sau đó đang đọc một
  quyển sổ thiếu trang.

  > Giá đo được: bản gõ tay **0 ms**, bản thật **166 s**.
  >
  > Và bốn cửa canh đầu tiên của tôi cho bản này **MÙ**: gieo 8 phép thì 4 xanh,
  > cả bốn đều là phép đổi HÀNH VI mà không đổi chuỗi — vì bốn bài ấy soi văn
  > bản hàm bằng `ast.unparse` thay vì gọi hàm rồi đọc kết quả. Đúng lỗi đã ghi
  > ngày 02/09. Viết lại thành phép đo hành vi (thay mọi phòng bằng bản giả, rồi
  > đếm cả *phòng nào ĐƯỢC GỌI*) thì **8/8 đỏ**.

## CHƯƠNG III: CƠ CHẾ BẢO MẬT & BỘ LỌC DỮ LIỆU NHẠY CẢM (REDACTION)
- Mọi file log lỗi (`raw/error.txt`) phải đi qua bộ lọc tập trung (Centralized Redactor).
- Tự động che giấu mọi dạng key/token: Bearer tokens, OpenAI/Gemini/Anthropic/OpenRouter API keys, Basic Auth credentials trong URL.
- Test bộ lọc bằng token giả; tuyệt đối không đưa key thật vào test fixture hoặc log commit.

### Cổng vào của `/api/polyglot/run` (04/09/2026)

Đường này **chạy mã tuỳ ý** trong tiến trình con. Đo trước khi vá, bằng một
`POST` không mang gì cả:

```
HTTP 200 · status PASS
HOME = C:\Users\baloa      cwd = D:\AURA_v3
ghi được D:\AURA_v3\CHUNG_MINH_LO.txt — RA NGOÀI thư mục tạm
```

Không mã thông hành, không kiểm Origin, không cờ bật. `noi_bo_app.py` mặc định
bind `127.0.0.1` nhưng đọc `AURA_NOI_BO_HOST`, nên **một biến môi trường là mở
ra LAN**.

**Bốn lớp, đăng ký TRƯỚC khi viết mã. Mọi lớp fail-closed — thiếu là chặn.**

1. **Tắt mặc định.** Không có `AURA_CHO_CHAY_MA=1` thì trả **403**. Chạy mã là
   việc phải bật có ý thức, không phải mặc định của một máy chủ nội bộ.
2. **Mã thông hành.** Sinh ngẫu nhiên 32 byte lúc tiến trình khởi động, in ra
   console một lần. Client phải gửi đúng ở `X-Aura-Token`, so bằng
   `hmac.compare_digest`. Sai hoặc thiếu -> **403**.
3. **Kiểm Origin.** Có `Origin` mà khác gốc của chính máy chủ -> **403**. Đây là
   lớp chặn trang web bất kỳ trong trình duyệt của Sếp gọi sang localhost.
4. **Chỉ loopback.** Máy chủ bind địa chỉ KHÔNG phải loopback thì lớp 1 bị vô
   hiệu hoá vĩnh viễn — bật cờ cũng không chạy được mã. Mở ra LAN và cho chạy mã
   là hai việc không được phép xảy ra cùng lúc.

**CHƯA CHẶN ĐƯỢC — không viết là đã chặn:**

- **Không có hộp cát.** Mã vẫn chạy với đủ quyền tài khoản Windows: ghi được ra
  ngoài thư mục tạm, đọc được `HOME`, gọi được mạng. Bốn lớp trên chặn *ai gọi
  được*, không chặn *mã làm được gì*. `resource.setrlimit` là API Unix — đã thử
  ngày 19/08, `ModuleNotFoundError` trên Windows.
- Chỉ có `timeout`, không có trần RAM, không có trần ghi đĩa.

**Phép đo phải chứng minh cả hai chiều.** Mỗi lớp một ca CHẶN và một ca ĐI QUA
— một cổng chưa từng cho ai đi qua thì không chứng minh được nó đang chặn đúng
người, mà chỉ chứng minh nó chặn tất cả.
