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
  - **≥ 11 câu khác nhau** *(13 → 11 ngày 04/09/2026, xem dưới)*.
  - Không câu nào lặp **quá 2 lần**.
  - Trần **3 lần sinh** cho một kịch bản, và **phải báo ra đã thử mấy lần**.

  > Ngưỡng lấy từ đâu. Tốc độ giọng OneCore đo trên 5 mẫu: 3,58–3,95 từ/giây,
  > văn xuôi ở cận trên. Lấy 3,9 → cửa sổ 55–65 s = 215–250 từ. Đã kiểm bằng
  > dây chuyền thật: **235 từ / 15 câu → PASS**; **266 từ → 67,3 s, FAIL**.
  > 13 câu là số thẻ ở 60 giây (`round(60 / 4,5)`) — **và đó là chỗ sai**,
  > sửa 04/09/2026 xuống 11. Xem mục *"Sàn 11 câu"* bên dưới.

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

* **HAI THỂ LOẠI LỜI NHẮC (thêm 05/09/2026):**
  - `viet_kich_ban(chu_de, the_loai="truyen")` — thêm `the_loai`, nhận đúng
    `"truyen"` hoặc `"bai_noi"`.
  - **Mặc định `"truyen"`**: người gọi cũ không đổi hành vi.
  - Thể loại lạ → **fail-closed**, ném lỗi. Không được âm thầm quay về mặc
    định: gõ nhầm `"bainoi"` mà chạy ra truyện thì hỏng LẶNG.

  > **Vì sao. Đo 2×2, biến là THỂ LOẠI của lời nhắc × LOẠI ĐỀ TÀI**, cùng 5 hạt
  > giống, cùng model, cùng tham số:
  >
  > ```
  > CẢ HAI cửa /5              đề GIẢI THÍCH   đề HƯ CẤU
  > lời TRUYỆN                      1/5             4/5
  > lời BÀI NÓI                     3/5             3/5
  >
  > riêng cửa ĐỀ, trên lượt thật sự được chấm:
  > lời TRUYỆN                      1/5             4/4
  > lời BÀI NÓI                     3/3             3/3
  > ```
  >
  > Ba ô đạt 100%. Ô duy nhất hỏng là `lời truyện × đề giải thích`. Nhìn được
  > cả cơ chế trong câu mở: *"Ánh nắng trưa chiếu xuống bàn học…"*, *"Đêm xuống
  > dần trong phòng thí nghiệm của cô gái tên Linh."* — model làm ĐÚNG thứ nó
  > được bảo. Truyện ngắn mở bằng dựng cảnh, mà dựng cảnh thì không nêu đề.
  >
  > Lời bài nói có giá của nó: nó viết câu dài hơn nên rụng 2/5 ở cửa độ dài
  > (đo được 3/5 so với 5/5). Vì thế **đường chéo là thật, không phải một bên
  > thắng tuốt**: đề giải thích `3/5 > 1/5` (gấp ba), đề hư cấu `4/5 > 3/5`.
  > Mỗi lời nhắc thắng trên thể loại của chính nó.

  > **KHÔNG có máy đoán thể loại — người gọi đã biết.** Dựng thêm một bộ đoán
  > là dựng thêm một chỗ đoán sai, cho một dữ kiện đã có sẵn.
  >
  > Thẻ nào khai gì (06/09/2026): `card_fullstack_builder` là **`bai_noi`** —
  > đề của nó là đề giải thích, đo được `truyen 0/5 · bai_noi 4/5`. Bốn thẻ
  > gọi `aura` còn lại khai `truyen`. `card_video_shorts` và `card_deep_scout`
  > **từng** được xếp là bài nói ở đoạn trên; chạy thật 05/09 trên đề của thẻ
  > video thì `bai_noi` trượt 3/3 vì câu quá dài, nên chúng đã rút về `truyen`.
  > Câu ấy trong bản 05/09 là **suy từ loại đề, không phải đo trên đề của
  > thẻ** — và đó chính là chỗ nó sai.

  > **PHÉP ĐO NÀY TỪNG KHÔNG KẾT LUẬN ĐƯỢC, và lý do đáng ghi.** Lần chạy
  > 04/09 cho `0/5 · 2/5 · 0/5 · 2/5` — không có đường chéo. Nguyên nhân là
  > **cái trần 19,2 làm nhiễu**: lời bài nói bị bác **9/10 lượt vì ĐỘ DÀI**
  > (21,0–25,4 từ/câu), tức phần lớn lượt chưa bao giờ đi tới được cửa đề. Hạ
  > sàn câu 13→11 hôm 04/09 đẩy trần lên 22,7, và chạy lại thì đường chéo hiện
  > ra ngay. **Một phép đo có thể không sai mà vẫn vô nghĩa, nếu một cửa khác
  > chặn mất phần lớn mẫu trước khi tới chỗ đang đo.**

  > **Giới hạn:** n=5 mỗi ô, và bốn ô có số lượt đo được khác nhau (5·4·3·3).
  > `1/5` so `3/5` là chênh gấp ba nhưng vẫn n=5 — đủ để đổi, chưa đủ để gọi
  > là chứng minh.

  > **ĐO LẠI TRÊN MỘT ĐỀ THỨ HAI (06/09/2026)** — đề mặc định của
  > `card_fullstack_builder`, *"Bảng điều khiển tài chính cá nhân tương tác"*,
  > cũng là một đề GIẢI THÍCH. Ghép đôi theo hạt giống, 5 hạt, mỗi bên 1 lượt:
  >
  > ```
  > hạt  truyen                              bai_noi
  > 1    KHONG_DAT  466 từ · 25,89 từ/câu    DAT  245 từ · 20,42
  > 2    KHONG_DAT  câu mở không nêu đề      KHONG_DAT  22,75 (trần 22,73)
  > 3    KHONG_DAT  430 từ · 23,89 từ/câu    DAT  250 từ · 20,83
  > 4    KHONG_DAT  câu mở không nêu đề      DAT  243 từ · 22,09
  > 5    KHONG_DAT  câu mở không nêu đề      DAT  236 từ · 21,45
  >                 ĐẠT 0/5                       ĐẠT 4/5
  > ```
  >
  > Đường chéo giữ nguyên, và rõ hơn lần đầu: `0/5` so `4/5`. Lời truyện trượt
  > **cả hai** cửa — 2/5 vì câu quá dài, 3/5 vì câu mở dựng cảnh nên không nêu
  > đề. Lượt `bai_noi` trượt duy nhất thua trần **0,02 từ/câu**.
  >
  > Điều này trả lời đúng câu mà chú thích của `card_video_shorts` để lại:
  > *"n=5 trên một đề không suy ra được đề khác"*. Cách trả lời không phải là
  > suy — là **đo trên đề thứ hai**.

* **Sàn 11 câu, trần 22,7 từ/câu (đổi 04/09/2026, trước đó 13 và 19,2):**
  - `SO_CAU_KHAC_MIN` **13 → 11**.
  - `TRAN_TU_MOI_CAU = 250 / 11 = 22,7` (vẫn là hệ quả, không phải phép đo).

  > **Con số 13 cũ suy từ một phép tính SAI HƯỚNG.** Nó lấy `round(60 / 4,5) = 13`
  > thẻ rồi giả định mỗi thẻ một câu, và giả định thêm rằng 13 thẻ cho 12 lần
  > đổi cảnh — vừa đủ trên ngưỡng 8. Dựng video THẬT ở từng mức, biến duy nhất
  > là số thẻ, cùng văn bản cùng giọng:
  >
  > ```
  >  thẻ  đổi cảnh  tĩnh lâu nhất   giây  s/thẻ  trạng thái
  >   13        20            0.0  59.34    4.6        PASS
  >   11        19            0.0  59.34    5.4        PASS
  >   10        16            0.0  59.34    5.9        PASS
  >    9        12            0.0  59.34    6.6        PASS
  >    8         9            0.0  59.34    7.4        PASS
  >    7        10            0.0  59.34    8.5        PASS
  >    6         9            0.0  59.34    9.9        PASS
  > ```
  >
  > `scdet` đếm **20** lần đổi cảnh ở 13 thẻ, không phải 12 — Ken Burns tạo
  > thêm. Phép tính `số thẻ − 1` sai hẳn hướng, và **mọi mức từ 6 đến 13 đều
  > PASS toàn bộ cửa**.

  > **Vì sao chọn 11 chứ không phải 6.** Máy đo cho PASS ở 6 thẻ không có nghĩa
  > 6 thẻ dùng được: ở đó mỗi thẻ đứng **9,9 giây** trên một video dọc 60 giây,
  > và **không cửa nào đo NHỊP**. Lấy sự cho phép của cửa làm bằng chứng về chất
  > lượng là đúng cái bẫy tệp này sinh ra để chống. Thêm nữa, gần sàn thì con số
  > nhiễu và không đơn điệu (8 thẻ → 9 lần cắt, 7 thẻ → 10, 6 thẻ → 9), biên chỉ
  > hơn ngưỡng 1 — nằm trong nhiễu.
  >
  > 11 thẻ giữ **19 lần đổi cảnh, biên gấp hơn 11 lần ngưỡng**, và nhịp 5,4 s/thẻ
  > sát nguyên bản 4,6.

  > **Nới này mua được gì — số đo từ lưới 2×2 ngày 04/09:**
  >
  > ```
  >                        lọt trần 19,2   lọt trần 22,7
  > lời TRUYỆN (đang dùng)      9/10           10/10
  > lời BÀI NÓI                 1/10            6/10
  > ```
  >
  > Lời truyện không mất gì; văn giải thích (đo được 22,0–22,4 từ/câu) từ 1/10
  > lên 6/10. Đó là toàn bộ lý do đổi — không có lý do nào khác.

  > **CHƯA ĐO — nhịp.** Không cửa nào biết video 11 thẻ xem có chán hơn 13 thẻ
  > không. Thứ đổi được đo là *lần đổi cảnh* và *tỉ lệ lọt cửa*, không phải
  > *người xem có ở lại không*.

* **Ba trạng thái, không gộp:** `DAT` · `KHONG_DAT` (đo được mà ngoài cửa sổ,
  kèm số) · `KHONG_DO_DUOC` (Ollama tắt, hết giờ, model không trả lời).

* **CHƯA CHẶN ĐƯỢC — không viết là đã chặn:** cửa này đếm từ, đếm câu, đếm lặp.
  Nó **không** biết truyện hay hay dở, có mạch lạc không. Mười lăm câu vô nghĩa
  nhưng khác nhau vẫn lọt sạch. Model cũng có thể viết 15 câu khác chuỗi mà cùng
  một ý — cửa mù chỗ đó.

* **Giá phải nói ra:** mỗi lượt sinh 64–96 giây. Trần 3 lần = tới ~4,8 phút cho
  một kịch bản, chưa tính 30 giây dựng video.

* **Cửa NÊU ĐỀ (thêm 04/09/2026):**
  - **Câu mở đầu** của kịch bản phải chứa **≥ 1** từ nội dung của đề tài.
  - So **nguyên từ**, không phân biệt hoa/thường, và **GIỮ DẤU**.
  - Đề tài không còn từ nội dung nào sau khi bỏ hư từ → `KHONG_DO_DUOC`,
    **fail-closed**: không đo được đề thì không dựng video nhận là về đề ấy.

  > Vì sao cần. Chạy thật 04/09/2026, đề *"Vì sao một bài test luôn xanh thì
  > chưa chứng minh được gì"*. AURA trả về một bài giảng về **gian lận thi cử
  > và điểm số** — và nó **ĐẠT**, vì cửa cũ chỉ đếm từ, đếm câu, đếm lặp:
  >
  > ```
  > chữ ký hàm: do_kich_ban(van_ban: str) -> ...
  >                         ^ không nhận `chu_de`
  > ```
  >
  > Cửa **về mặt cấu trúc** không thể kiểm đề tài — nó chưa bao giờ nhận đề.
  > Ca đối chứng cứng: một bài về **nấu phở** chấm cho đề trên ra `DAT`
  > (244 từ · 17 câu khác · lặp 1), trong khi một bài **đúng đề** ra
  > `KHONG_DAT` vì 273 từ. Cửa nhận bài lạc đề và bác bài đúng đề.

  > Ba thang đã CHẠY THỬ trước khi chọn — không thang nào dùng được:
  >
  > | thang | đo được gì |
  > |---|---|
  > | Embedding (cosine đề ↔ kịch bản) | `/api/embed` trả *"This server does not support embeddings"*. Máy chủ đang tắt. |
  > | Trùng từ nội dung, chấm theo tỉ lệ | **Không tách được.** Đề "nấu phở bò": đúng đề **0,33**, lạc đề **0,17**. Đề "bài test": đúng đề **0,67**, bài AURA lạc **0,33**. Cùng con số **0,33** vừa là đúng vừa là sai tuỳ đề — không tồn tại ngưỡng chung. |
  > | Hỏi model | Chính model vừa viết lại đi chấm bài mình. Đúng hình dạng đã ghi ở ca Hermes (*"asks itself"*, không có gì nói *không*) và DSPy. |
  >
  > Nên **đổi hợp đồng thay vì dựng cái cân**: không hỏi *"bài này có ĐÚNG đề
  > không"* — câu ấy không có thang đo được trên máy này — mà hỏi *"bài này có
  > NÊU đề ra không"*. Câu sau tất định, không có ngưỡng phải hiệu chuẩn, và
  > cũng là cách viết đúng cho video dọc: câu đầu là câu móc, phải nói ngay
  > video này về cái gì.

  > **GIỮ DẤU là có chủ đích.** Bỏ dấu thì `bò`, `bỏ`, `bó`, `bọ` cùng thành
  > `bo` — đúng họ bệnh `x in y` đã trả giá bảy lần trong `CLAUDE.md`, chỉ đổi
  > lớp áo. Tiếng Việt đơn âm nên bỏ dấu là tự tạo va chạm. So nguyên từ có dấu
  > thì `bò` chỉ khớp `bò`.

  > **LỜI NHẮC GIỮ NGUYÊN — quyết định có số.** Việc đầu tiên nghĩ tới là bảo
  > model nhắc đề ngay câu mở. Thử ba cách, mỗi cách 5 hạt giống cố định:
  >
  > ```
  > lời cũ                            dài 4/5  đề 2/5  CẢ HAI 2/5
  > "CÂU ĐẦU TIÊN phải nhắc tới ..."  dài 0/5  đề 0/5  CẢ HAI 0/5
  > chèn vào mệnh đề đề tài           dài 2/5  đề 3/5  CẢ HAI 2/5
  > mệnh đề ngắn ở cuối               dài 2/5  đề 3/5  CẢ HAI 2/5
  > ```
  >
  > Không bản nào mua được gì: cái gì giúp cửa đề thì lấy đi đúng chừng ấy ở
  > cửa dài. Bản viết hoa còn đẩy từ/câu từ ~19 lên **21,7–24,3**, quá trần
  > 19,2 cả năm lượt. n=5 mỗi nhánh — `2/5` so `2/5` KHÔNG chứng minh bằng
  > nhau, chỉ nói ở n=5 chưa thấy khác biệt. Đủ để KHÔNG đổi.

  > **GIÁ PHẢI NÓI RA.** Tỉ lệ lọt CẢ HAI cửa là **2/5 mỗi lượt sinh**, nên với
  > trần 3 lần: `1 − 0,6³ ≈ 78%`. Tức là **khoảng 1/5 yêu cầu nay trả về
  > `KHONG_DAT`** thay vì trả một kịch bản lạc đề — và mỗi lượt tốn 49–110 giây,
  > nên ca trượt tốn tới ~5,5 phút để nói "không viết được". Đó là giá của việc
  > hỏng TO thay vì đạt SAI.

* **CHƯA CHẶN ĐƯỢC — không viết là đã chặn.** Cửa nêu đề chỉ canh *có nêu đề
  ra không*, **không** canh *nội dung có đúng đề không*. Một bài mở bằng
  *"Bài test này nói về nấu phở"* rồi đi nói chuyện phở vẫn lọt. Trên máy này
  chưa có thang nào đo được điều thứ hai — đã thử ba thang, ghi ở trên.

  Và nó so **TỪ**, không so **NGHĨA** — bắt được ngay trong lượt đo lời nhắc
  04/09. Hạt 3 trả về câu mở *"Một lá **bài** được lật ra màu **xanh** lá
  cây."*: khớp hai từ khoá `bài` và `xanh`, cửa cho **ĐẠT**, trong khi `bài` ở
  đó là **lá bài** và `xanh` là màu lá cây. Tiếng Việt đơn âm nên đồng âm khác
  nghĩa là chuyện thường, không phải ca hiếm. (Lượt ấy vẫn bị bác — nhưng bởi
  cửa ĐỘ DÀI, 175 từ, chứ không phải bởi cửa đề. Một cửa khác bắt hộ không
  chứng minh được cửa này biết bắt.)

### 1c. CHẾ ĐỘ ĐỊNH TUYẾN CHO BÌNH LUẬN (04/09/2026)

Sếp soạn câu trả lời cho bình luận trong các nhóm AI/lập trình. Đo trên **10
bình luận THẬT do Sếp lấy về** (em không được thấy trước khi đo):

```
is_search_request định tuyến ra mạng   1/10
   — và câu duy nhất nổ (#9) nổ vì trong câu có chữ "google",
     tức trúng lệnh tra thẳng, KHÔNG phải định tuyến đúng. Thực chất 0/10.
```

**Luật cũ KHÔNG hỏng.** Nó được chỉnh cho chat riêng của Sếp, nơi cái đắt là
*tra thừa*: 23–43 giây, và một câu riêng tư bị đẩy ra máy chủ tìm kiếm. Nó làm
tốt đúng việc ấy — **0 sai dương** trên bộ đối chứng. Bình luận công khai có
hàm chi phí **ngược lại**: nói sai trước mặt người lạ đắt hơn nhiều so với một
lượt tra 4 giây. Cùng một luật, hai bài toán, hai hướng sai.

* **Ngưỡng, đặt TRƯỚC khi viết mã:**
  - `nen_tra_cho_binh_luan(text)` — **mặc định TRA**, chỉ không tra khi câu
    thuộc một trong bốn nhóm máy đã có sẵn đáp án:
    1. `la_viec_tu_lam` — bảo AURA làm một việc (viết hàm, sửa lỗi, dịch).
    2. `la_chuyen_rieng_cua_sep` — dữ kiện riêng, internet không đời nào biết,
       và tra là **đẩy chuyện riêng ra ngoài**.
    3. hỏi về chính AURA · chào hỏi · hỏi ngày giờ — `core/dong_ho.py` đã đưa
       giờ máy vào lời dặn mỗi lượt.
    4. phép tính số học — `core/may_tinh.py` lo, model không được đoán.

  - **Tiêu chí nghiệm thu, đăng ký trước khi chạy:**
    - 10 bình luận thật của Sếp → **10/10** ra mạng.
    - Bộ đối chứng (chào hỏi · "em là ai" · `1247 nhân 38` · "viết giúp tôi
      hàm sắp xếp" · chuyện riêng) → **0** ra mạng.

  > **MỘT NHÃN ĐỔI CÓ CHỦ Ý, nói ra trước khi đo.** Câu *"Giải thích cho tôi
  > decorator trong Python là gì"* ở chế độ chat gắn nhãn **không cần tra** —
  > model biết, tra là phí 4 giây. Ở chế độ bình luận em gắn nhãn **được phép
  > tra**: câu trả lời công khai kèm một đường dẫn tốt hơn câu không kèm, và
  > 4 giây là rẻ. Đây là **đổi hàm chi phí, không phải đổi sự thật** — và em
  > ghi ra đây trước khi chạy để nó không thành việc dán nhãn lại sau khi thấy
  > kết quả.

  > **Vì sao KHÔNG import `core/may_tinh.py` vào `core/web_search.py`.** Hàng
  > rào `tests/test_v3_ranh_gioi.py` cho chat và phòng dùng chung ĐÚNG hai tệp:
  > `paths.py` và `web_search.py`. Thêm cạnh ấy là kéo `may_tinh` sang phía
  > phòng. Nên phép dò số học ở đây là một phép dò TẠI CHỖ, cố ý hẹp, và nó
  > không thay `may_tinh` — nó chỉ trả lời "câu này có phải phép tính không".

* **ĐO ĐƯỢC TRƯỚC KHI DỰNG — tra mạng CÓ ăn thua trên loại câu này:**

  ```
  20 nguồn / 5 truy vấn · 2,3–15,1 s
  #3 "AG 2.0 có plugin auto accept không"
       -> github.com/nextcortex/antigravity-auto-accept
       -> github.com/zixfelw/ag-auto-click-scroll
  ```

  Và ca đối chứng đắt nhất: **nguyên văn bình luận tra ra TỐT NGANG HOẶC HƠN**
  truy vấn tự viết lại — kể cả tiếng lóng *"AG 2.0"*, *"anti IDE"*. Nên không
  cần khâu viết lại câu. Thiếu ca này thì đã ghi công cho tra mạng đúng cái
  việc người đo tự làm.

* **CHƯA CHẶN ĐƯỢC — không viết là đã chặn.** 4/10 bình luận (#2, #6, #8, #10)
  hỏi **kinh nghiệm cộng đồng**, không hỏi dữ kiện: *"mọi người vẫn để sol hay
  đổi sang luna"*, *"có tips nào cho nó nhớ lâu"*. Tra mạng ra bài viết chung,
  **không ra được câu "nhóm này đang làm thế nào"**. Định tuyến đúng cũng không
  đổi được điều đó.

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

* **Số thẻ KHÔNG được vượt số câu (thêm 04/09/2026):**
  - `so_the = max(SO_THE_TOI_THIEU, min(round(dài_giọng / 4,5), số_câu))`.
  - Không khối phụ đề nào được chiếu **hai lần**.

  > Vì sao thêm. Đi tìm xem trần **19,2 từ/câu** đo cái gì, thì ra nó **không đo
  > gì cả**: nó là `250 ÷ 13` viết lại — hệ quả số học của `SO_TU_MAX` và
  > `SO_CAU_KHAC_MIN`, không phải một phát hiện về video. Nó chưa bao giờ nói
  > "câu dài hơn 19,2 từ thì video xấu".
  >
  > Ràng buộc THẬT của video là `TI_LE_PHU_DE_KHAC_MIN = 0,80`. Với 13 thẻ nó
  > chỉ đòi **11 câu**, đo trên chính hàm sản phẩm:
  >
  > ```
  > số câu   từ/câu   khối   khác   tỉ lệ   cửa nội dung
  >     10     24,0     13     10    0,77   BÁC
  >     11     21,8     13     11    0,85   ĐẠT   <- sàn thật
  >     13     18,5     13     13    1,00   ĐẠT
  > ```
  >
  > Nhưng **không được nới trần theo đó**, vì `_cat_doan` đệm cho đủ thẻ bằng
  > cách LẶP LẠI câu. 11 câu / 13 thẻ ra:
  >
  > ```
  > thẻ 11 (44,6-49,1s): Ý thứ 11 ...
  > thẻ 12 (49,1-53,5s): Ý thứ 1  ...   <- CHIẾU LẠI
  > thẻ 13 (53,5-58,0s): Ý thứ 2  ...   <- CHIẾU LẠI
  > ```
  >
  > Chín giây cuối chiếu lại câu mở trong khi giọng đã đọc xong. **Cả hai cửa
  > nội dung đều cho ĐẠT**: `kiem_lap_phu_de` chấm tỉ lệ khác nhau (0,85 ≥
  > 0,80), còn `kiem_phu_kin` hỏi *"có câu nào bị bỏ sót không"*, không hỏi
  > *"có câu nào bị chiếu hai lần không"*. Lỗ nằm **GIỮA** hai cửa — mỗi cửa đo
  > đúng phần nó đo.

  > **Và lỗi ấy VỚI TỚI ĐƯỢC, không phải giả định.** Kịch bản đúng 13 câu (sàn
  > của đặc tả) với giọng ≥ 60,7 s (giữa cửa sổ 55–65 s) cho 14 thẻ:
  >
  > ```
  > giọng 55,0s -> 12 thẻ · 0 khối lặp
  > giọng 60,7s -> 13 thẻ · 0 khối lặp
  > giọng 61,0s -> 14 thẻ · 1 khối lặp   <- chiếu lại câu 1, mọi cửa ĐẠT
  > giọng 65,0s -> 14 thẻ · 1 khối lặp
  > ```
  >
  > Sửa: chặn trần số thẻ theo số câu. Sau vá, **0 ca lặp** trên lưới
  > 7 số câu × 4 thời lượng. Sàn cứng `SO_THE_TOI_THIEU = 3` vẫn thắng khi kịch
  > bản dưới 3 câu — ở đó cửa nội dung bác thật (một khối chiếm 1/3 > 0,25),
  > nên nó hỏng TO chứ không hỏng lặng.

  > **CHƯA LÀM — nới trần 19,2.** Sau khi hết lặp thì sàn thật là *số thẻ tối
  > thiểu để đủ lần đổi cảnh*, và số học cho 9 thẻ → 8 lần cắt → trần
  > `250 ÷ 9 = 27,8`, đủ chỗ cho văn giải thích (đo được **22,0–22,4 từ/câu**).
  > Nhưng phép tính `số thẻ − 1` chỉ là chặn dưới trên giấy: lượt render thật
  > 04/09 cho **19 lần đổi cảnh với 13 thẻ**, không phải 12, vì `scdet` đếm
  > thêm nhờ Ken Burns. Sàn thật rộng hơn hay hẹp hơn thì phải **dựng video ở
  > mức ấy mới biết**, không suy ra được. Chưa đo thì chưa đổi.

* **Cửa PHỦ KÍN KỊCH BẢN (thêm 04/09/2026):**
  - Mọi câu của kịch bản **phải** có mặt trong phụ đề. Số câu mất: **0**.
    Không có ngưỡng phần trăm — mất một câu là hỏng.

  > Vì sao thêm. Chạy thật một lượt `aura` → `alpha` ngày 04/09/2026, kịch bản
  > 245 từ / **17 câu**. Video ra **PASS**, sạch cả hai chục cửa trên:
  >
  > ```
  > 720×1280 · 61,32 s · 19 lần đổi cảnh · 0 đoạn tĩnh · 0 khung đen
  > lufs_giong −17,34 · lufs_nhac −33,82 · chênh 16,48 dB
  > 14 khối phụ đề · 14 khối khác nhau (tỉ lệ 1,00)
  > quãng câm dài nhất 0,76 s
  >
  > GIỌNG ĐỌC   17 câu (toàn bộ kịch bản)
  > LÊN MÀN HÌNH 14 câu
  > MẤT          3 câu   <- và là ba câu KẾT của kịch bản
  > ```
  >
  > Gốc ở `_cat_doan`: `moi = len(cau) // so_the` rồi lấy `so_the` lát liên
  > tiếp, nên phần dư ở ĐUÔI rơi ra ngoài. Bảng đo trên hàm thuần:
  >
  > ```
  > 17 câu / 13 thẻ  -> 13 câu lên hình, MẤT 4
  > 20 câu / 13 thẻ  -> 13 câu lên hình, MẤT 7
  > 25 câu / 13 thẻ  -> 13 câu lên hình, MẤT 12
  > 13 câu / 13 thẻ  -> đủ 13, MẤT 0        <- chỉ khi chia hết mới không mất
  > ```
  >
  > `viet_kich_ban` chỉ ép **≥ 13** câu, không có trần trên; `so_the` thì bằng
  > `round(dài_giọng / 4,5)`. Hai con số ấy không có lý do gì trùng nhau, nên
  > mất câu là trạng thái THƯỜNG, không phải ca hiếm.
  >
  > Không cửa nào cũ kêu được, vì mỗi cửa đo đúng phần nó đo: phụ đề vẫn đủ
  > dòng (14 ≥ số thẻ), vẫn khác nhau hết, vẫn không chạy quá phim. Cùng một
  > bài học với cửa nội dung hôm 03/09 — **cửa hình dạng không thay được cửa
  > nội dung** — chỉ khác là lần này thứ bị mất nằm ở khúc KẾT, tức là phần
  > khán giả cần nhất.

### 2b. MỐC PHỤ ĐỀ PHẢI ĐO, KHÔNG ĐƯỢC CHIA ĐỀU (06/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**.

`_dung_video` đặt mốc phụ đề bằng `dai_giong / len(cards)` — **chia đều**. Nó
không đo câu nào kết thúc ở giây nào; nó giả định mọi câu dài bằng nhau. Đo
trên kịch bản thật 245 từ / 13 đoạn:

```
lệch mốc lớn nhất 1,31 giây     đoạn ngắn nhất 4,17s · dài nhất 6,28s
                                chia đều cho    5,15s
```

Ở tốc độ 2–3 từ/giây, 1,31s là lệch 3–4 chữ. Nhìn thấy được.

**Đo bốn cách trên cùng một kịch bản:**

```
cách                            giây     cửa 55–65
A · đọc liền một lần           58,87s    LỌT     <- đang chạy, mốc lệch 1,31s
B · nối 13 đoạn, không cắt     66,94s    TRƯỢT   <- mỗi lượt SAPI đệm ~0,90s
C · cắt sạch im lặng           55,19s    LỌT nhưng sát sàn 0,19s
D · cắt + chèn khe             58,91s    LỌT
```

**Đặc tả:**

* **Đọc TỪNG ĐOẠN, cắt đệm SAPI, rồi chèn khe SUY RA TỪ ĐÍCH.** Mốc phụ đề
  tính từ độ dài thật của từng đoạn cộng khe — sai số 0, không còn phép chia.
* `DAI_DICH = 60,0s` (giữa cửa sổ 55–65). `khe = (DAI_DICH − tổng đã cắt) /
  (số đoạn − 1)`, kẹp trong `KHE_MIN 0,15s … KHE_MAX 1,20s`.
* **Ngưỡng cắt im lặng `-45dB`**, cắt hai đầu.
* **Số thẻ tính từ `DAI_DICH`, không từ độ dài đo được** — vì nay chính ta
  quyết định độ dài. `so_the_can_dung` giữ nguyên, kể cả trần theo số câu.

> **KHÔNG DÙNG MỘT HẰNG SỐ KHE.** Bản đầu của phép đo fit `khe = 0,31s` từ
> **chính kịch bản dùng để kiểm** — vòng tròn. Đo tiếp trên ba kịch bản:
>
> ```
>                  đọc liền   đã cắt   đệm/đoạn    KHE
> kb1 (245 từ)      58,87s    55,19s    0,90s     0,31s
> kb2 (239 từ)      59,46s    50,86s    0,89s     0,72s
> kb3 (240 từ)      59,88s    51,19s    0,90s     0,72s
>
> ĐỆM SAPI  0,89–0,90s  chênh 0,01s  -> hằng số thật, 39 đoạn
> KHE       0,31–0,72s  chênh 0,42s  -> KHÔNG phải hằng số
> ```
>
> `0,31s` hoá ra là ca lệch nhất. Áp nó cho kb2 thì `50,86 + 12×0,31 = 54,58s`
> — **dưới sàn 55s**. Suýt vá bằng một hằng số chỉ đúng cho đúng bài đã dùng để
> tìm ra nó. Suy khe từ đích thì cả ba đều ra đúng 60,00s.

> **CÁI NÀY KHÔNG MUA ĐƯỢC PHỤ ĐỀ SÁNG TỪNG CHỮ.** Nó cho mốc theo **CÂU**.
> Phụ đề karaoke đòi mốc theo **TỪ**, mà OneCore không trả. Nói ra để không ai
> đọc mục này rồi tưởng đã có.

> **Và nó thay `_dai_ngan_lai` trên đường chính.** Hàm ấy dồn im lặng vào CUỐI
> để đủ cửa sổ — đúng cái lỗi đã nằm một tháng không ai thấy (xem chú thích đầu
> `core/phong_alpha.py`). Nay im lặng nằm giữa các câu, chỗ nó vốn phải ở.

* **THỜI ĐIỂM ĐỔI THẺ DÙNG CHUNG `moc` VỚI PHỤ ĐỀ.** `render()` nhận `moc` và
  đặt `-t` riêng cho từng thẻ; bước phóng Ken Burns cũng tính riêng từng thẻ.

  > **VÁ MỘT NỬA CỦA MỘT CẶP THÌ PHÁ VỠ SỰ ĂN KHỚP.** `render()` để
  > `dai / len(cards)` — chia đều. Khi phụ đề CŨNG chia đều thì hai bên cùng
  > sai một kiểu nên **khớp nhau**. Vá phụ đề mà quên chỗ này:
  >
  > ```
  > thẻ đổi ở   phụ đề bắt đầu   lệch
  >   10,000       11,159       +1,159
  >   20,000       21,344       +1,344
  >   25,000       26,724       +1,724   <- NẶNG HƠN cái 1,31s vừa chữa
  > ```
  >
  > `scdet` xác nhận cắt cảnh ở 15,000 · 30,000 · 35,000 trong khi phụ đề ở
  > 15,812 · 30,839 · 35,621. Sau khi vá cả hai: **1,72s → 0,036s**, trong vòng
  > một khung hình (1/24 = 0,042s).

  > **BƯỚC PHÓNG PHẢI TÍNH RIÊNG TỪNG THẺ.** Một bước chung theo độ dài trung
  > bình thì thẻ dài hơn trung bình phóng hết cỡ sớm rồi ĐỨNG IM nốt phần còn
  > lại — `kiem_video` bắt đúng: *"1 đoạn đứng yên > 5s (lâu nhất 5,3s)"*. Lỗi
  > này chỉ **với tới được** sau khi thẻ có độ dài khác nhau.

  > **Thẻ cuối nhận phần dư.** Khe im lặng cuối cùng thuộc về nó; bỏ đi thì
  > video cụt trước khi giọng đọc xong.

### 2b-bis. MỘT THẺ MỘT CÂU, TRỪ KHI THẺ SẼ QUÁ NGẮN (07/09/2026)

Chạy thật một lượt Alpha để xem: **13 thẻ cho 15 câu**. Đọc kỹ hơn thì cái hỏng
không phải hai con số lệch nhau, mà là **độ lệch giữa các thẻ**:

```
thẻ ngắn nhất 2,04s · dài nhất 7,87s     (3,9 lần)
từ ít nhất 11        · nhiều nhất 32     (2,9 lần)

thẻ  7:  31 từ · 7,23s · 2 câu
thẻ 13:  32 từ · 7,87s · 2 câu
```

Hai thẻ ôm 2 câu, mỗi thẻ **32 từ trong 7,9 giây**, trong khi thẻ 1 có 11 từ.
Trên một video dọc 720×1280 thì đó là hai màn hình chữ dày gấp ba các thẻ khác.

**Nguyên nhân: ràng buộc đang đi SAI CHIỀU.**
`so_the_can_dung` lấy `min(round(dài/4,5), số_câu)` — tức **thời lượng quyết
định số thẻ**, còn câu chỉ là trần chống lặp. Với 60,0s thì `round(60/4,5) = 13`
chặn trước, và `_cat_doan` phải nhét 15 câu vào 13 ô bằng phép chia chỉ số
`i * n // so_the` — chọn thẻ nào ôm 2 câu **theo vị trí**, không theo độ dài.

Cân lại theo số từ cũng không cứu được: mọi câu ở lượt này dài 11–17 từ, nên
gộp bất kỳ cặp nào cũng ra 27–32 từ. Thứ sửa được là **đừng gộp**.

**Đặc tả mới — chép TAY vào cửa canh:**

```
so_the = max(SO_THE_TOI_THIEU, min(so_cau, int(dai_giong / GIAY_TOI_THIEU_MOI_THE)))
DAC_TA_GIAY_TOI_THIEU_MOI_THE = 2.5
```

Một thẻ một câu, **trừ khi** làm thế khiến thẻ ngắn hơn `GIAY_TOI_THIEU_MOI_THE`.
Với 60,0s thì trần là 24 thẻ; 15 câu ra đúng 15 thẻ.

**`2,5` LÀ MỘT CON SỐ CHỌN, KHÔNG PHẢI ĐO ĐƯỢC — nói ra chứ không giấu.**
`GIAY_MOI_THE = 4,5` trước nó cũng vậy. Thứ đo được ở đây chỉ là một điểm:
thẻ ngắn nhất của lượt vừa chạy dài **2,04s** và qua sạch mọi cửa, nên vùng
quanh 2 giây chưa phải chỗ hỏng. Trần này chỉ có việc khi kịch bản **>24 câu**;
`core/viet_truyen.py` có sàn `SO_CAU_KHAC_MIN = 11` nhưng **không có trần**, nên
để hở thì một kịch bản 40 câu ngắn sẽ ra 40 thẻ × 1,5s.

**Ràng buộc cũ đổi vai, không bị xoá.** `so_cau` từ chỗ là *trần chống lặp* trở
thành *đích*; thời lượng từ chỗ là *đích* trở thành *trần*. Lý do chống lặp
(`_cat_doan` đệm bằng cách lặp câu khi thiếu) vẫn còn nguyên vì `min(so_cau, …)`
vẫn giữ.

**Phải đo lại sau khi đổi, và đo ĐỘ LỆCH chứ không đo số thẻ:** tỷ lệ
từ-nhiều-nhất / từ-ít-nhất phải giảm. Chỉ đếm "13 → 15" thì một bản vá làm 15
thẻ lệch hơn nữa vẫn qua.

**ĐO SAU KHI ĐỔI — chạy thật lại cả dây chuyền:**

```
                  TRƯỚC (13 thẻ)     SAU (15 thẻ)
thẻ ngắn / dài    2,04s / 7,87s      2,04s / 3,70s     3,9× → 1,8×
từ ít / nhiều     11 / 32            11 / 17           2,9× → 1,5×
thẻ ôm 2 câu      2                  0
trạng thái        PASS 74,3s         PASS 63,8s
```

**VÀ CHỖ ĐÁNG GHI NHẤT: ĐỔI LUẬT XONG, 31 BÀI LIÊN QUAN VẪN XANH.**
Không cửa nào chốt công thức cũ, nên một quy tắc trung tâm của phòng Alpha
trôi đi **không tiếng động**. Hằng số `GIAY_MOI_THE = 4,5` có mặt trong mã, có
chú thích dài, nhưng chưa bao giờ có một dòng `assert` nào đối chiếu nó với đặc
tả — và `GIAY_TOI_THIEU_MOI_THE` mới cũng suýt vào kho theo cùng cách.

Nay ba cửa: hằng số chép tay · một thẻ một câu khi thời lượng còn chỗ · **độ
lệch** (thẻ dày chữ nhất không quá 2 lần thẻ mỏng nhất). Cửa thứ ba là cửa
quan trọng nhất — chỉ đếm "13 → 15" thì một bản vá làm 15 thẻ lệch hơn nữa vẫn
qua. Gieo 5 phép, cả 5 đỏ.

### 2b-ter. TRẦN SỐ CÂU — TRẢ NỢ MÀ CHÍNH §2b-bis SINH RA (07/09/2026)

§2b-bis phải đặt `GIAY_TOI_THIEU_MOI_THE = 2,5` làm **con số chọn** vì
`core/viet_truyen.py` có sàn `SO_CAU_KHAC_MIN = 11` nhưng **không có trần**.
Nợ ấy ghi ngay trong chú thích. Nay trả.

**LỖ CÓ THẬT, KHÔNG PHẢI GIẢ ĐỊNH.** Đo 5 lượt `viet_kich_ban` ngày 07/09:

```
lượt 3   233 từ · 12 câu · 19,4 từ/câu    -
lượt 4   238 từ · 36 câu ·  6,6 từ/câu    VƯỢT
```

`qwen3.5:4b` **thật sự** sinh 36 câu ngắn, và **mọi cửa cũ đều gật**: 238 từ
nằm trong 215–250, 36 câu khác nhau vượt sàn 11, và `TRAN_TU_MOI_CAU` chỉ chặn
câu **DÀI**. Không cửa nào hỏi *"quá nhiều câu ngắn"*. Với 36 câu thì Alpha
chặn ở 22 thẻ, 14 thẻ phải ôm 2 câu, và độ lệch quay về đúng cái vừa vá sáng
nay.

*(3/5 lượt còn lại không sinh được kịch bản đạt — con số riêng, chưa đụng tới.)*

**Đặc tả — SUY RA, không chọn:**

```
SO_CAU_TOI_DA = DAI_MIN / GIAY_TOI_THIEU_MOI_THE = 55,0 / 2,5 = 22
```

Khác `2,5` ở chỗ: `2,5` không suy ra từ đâu cả, còn `22` là hệ quả của hai hằng
số đã có. Ghi rõ cái nào là cái nào.

**HẰNG SỐ ĐỂ RỜI, KHÔNG `import` — VÀ CÓ CỬA GIỮ.** `viet_truyen` không lấy
`from core.phong_alpha import …`: cấu hình đi theo thứ cần nó. Nhưng để rời thì
hai bên trôi khỏi nhau được, nên `test_hai_phong_KHOP_tran_so_cau` giữ chính
phép suy ấy. Gieo hạ `GIAY_TOI_THIEU_MOI_THE` bên Alpha mà không đụng
`viet_truyen` → **bài ấy đỏ**, đúng việc của nó.

**Ca đối chứng bắt buộc:** kịch bản đúng 22 câu phải QUA. Không có nó thì một
bản vá bác *mọi* kịch bản cũng đi qua bài "36 câu bị bác".

**VÀ BẢN VÁ ĐẦU CHỈ ĐÚNG MỘT NỬA — bộ đủ bắt được, 7 bài đỏ.**

Bản đầu chỉ vá `do_kich_ban` (hàm **CHẤM**) mà quên `cat_cho_vua` (hàm **CẮT**).
Đúng bài *"vá một nửa của một cặp"*, lần thứ ba trong tuần. Hai chỗ hỏng, tìm
ra theo thứ tự:

1. **Hàm cắt chỉ đếm TỪ.** Model trả 40 câu × 9 từ = 360 từ; `cat_cho_vua` cắt
   còn **243 từ / 27 câu** — lọt cửa sổ từ nhưng vẫn vượt trần câu, nên vòng lặp
   trả về một văn bản mà **chính phép chấm của nó BÁC**. Vá: cắt theo cả hai.

2. **Cắt theo cả hai thì lộ ra một mặt đối xứng chưa ai đặt tên.** 40 câu × 9 từ
   cắt xuống 22 câu chỉ còn **198 từ**, dưới sàn 215 — *không cách cắt nào cứu
   được*. Đó đúng là câu đã viết cho `TRAN_TU_MOI_CAU`, chỉ ở chiều ngược:

```
TRAN_TU_MOI_CAU = SO_TU_MAX / SO_CAU_KHAC_MIN = 250 / 11 = 22,73   (câu DÀI)
SAN_TU_MOI_CAU  = SO_TU_MIN / SO_CAU_TOI_DA   = 215 / 22 =  9,77   (câu NGẮN)
```

   Dưới sàn thì **sinh lại ngay**, đừng đốt một lần cắt rồi mới trượt — y hệt
   nhánh đã có cho trần trên.

**Bảy bài đỏ đều dùng `_van_ban(26, 9)` làm kịch bản "hợp lệ" chuẩn.** Con số 26
chưa bao giờ là phép đo — nó là số dựng tay, chọn tuỳ ý trong cửa sổ 215–250 từ.
Nên chỗ phải sửa là **fixture**, không phải trần. Đặt tên `SO_CAU_DAT,
TU_MOI_CAU_DAT = 22, 10` để lần sau ai đổi ràng buộc thì sửa MỘT chỗ.

**Gieo 7 phép, và lượt đầu 2 cửa mù — một trong hai là phép gieo không tới nơi,
lần thứ năm:** dòng `SAN_TU_MOI_CAU = SO_TU_MIN / SO_CAU_TOI_DA` xuất hiện **hai
lần** — một trong chú thích, một trong mã. `Phep.so_lan` mặc định 1 nên nó sửa
**chú thích**, và công cụ in *"CỬA MÙ"* cho một cửa chưa hề bị đụng tới. Neo
thêm ký tự xuống dòng ở đầu thì khớp đúng dòng mã. Cửa mù thật là nhánh sàn —
chưa bài nào lái một kịch bản dưới sàn qua vòng lặp.

Lượt cuối: **7/7 đỏ**.


### 1c. SIẾT LỜI NHẮC `truyen` ĐỂ CÂU MỞ NÊU ĐỀ (08/09/2026)

Đăng ký **TRƯỚC KHI SỬA**.

**ĐO NỀN, 8 đề, ghi lý do TỪNG lượt thử** (mỗi đề tới `TRAN_SO_LAN = 3` lần):

```
5/8 đề ra kịch bản ĐẠT
11 lượt thử hỏng, lý do:
  10  "câu mở không nêu đề"     <- 91%
   1  "202 từ, cần 215–250"
```

Không phải cửa số từ, không phải trần số câu thêm 07/09. Là **cửa NÊU ĐỀ**.

```
TRƯỢT 3/3 lần thử              ĐẠT ngay lần 1
"bảng điều khiển tài chính"    "con hẻm nhỏ buổi sáng"
"một bài test luôn xanh"       "người thợ sửa khoá đầu ngõ"
"chuyến đi cuối năm"           "cơn mưa đầu mùa ở thành phố"
                               "chiếc la bàn gãy kim"
```

Model mở bài bằng **cảnh** — *"Buổi sáng đẹp…"*, *"Mưa đang rơi…"*, *"Mặt trời
bắt đầu…"*. Đề nào tự nó **là một vật trong cảnh** thì câu mở tình cờ chứa nó;
đề trừu tượng thì không. Đây là **lệch giữa cửa và lời nhắc**, không phải model
kém — cửa đòi một thứ lời nhắc chưa hề yêu cầu.

**CHỖ VÁ ĐÃ CÓ SẴN Ở THỂ LOẠI KIA.** `_loi_bai_noi` có câu *"Mở bằng một câu
nêu rõ đang nói về cái gì"*, và chú thích của nó ghi kết quả đo 03/09:

```
                    cửa ĐỀ    cửa ĐỘ DÀI
lời truyện           ?/3         5/5
lời bài nói          3/3         3/5      <- câu dài hơn, rụng 2/5
```

Nên **cái giá đã biết trước**: siết quá tay thì câu dài ra và rụng ở cửa độ dài.
Bản vá phải nói *"câu đầu tiên phải chứa từ của đề"* mà **không** đổi giọng kể
sang giọng giảng.

**Ngưỡng — chép TAY, đặt TRƯỚC khi đo lại:**

* **So sánh GHÉP CẶP: cùng 8 đề, trước và sau.** Đổi đề thì không tách được
  "lời nhắc tốt hơn" khỏi "đề dễ hơn".
* `lỗi NÊU ĐỀ` phải giảm còn **≤ 5** (nền 10).
* `số đề ĐẠT` **không được tụt** dưới nền **5/8**.
* `lỗi ĐỘ DÀI` không được vượt **nền + 2** (nền 1) — đây là cửa canh cái giá đã
  biết của `_loi_bai_noi`.

**ĐO SAU KHI SIẾT — cùng 8 đề, ghép cặp:**

```
                  nền        sau       ngưỡng đặt TRƯỚC
lỗi NÊU ĐỀ        10          0        ≤ 5        ĐẠT
số đề ĐẠT        5/8        8/8        ≥ 5/8      ĐẠT
lỗi ĐỘ DÀI         1          0        ≤ 3        ĐẠT
tổng lượt hỏng    11          1
```

**10 → 0.** Ba đề trước trượt 3/3 nay qua ngay lần đầu: *"bảng điều khiển tài
chính cá nhân"*, *"một bài test luôn xanh"*, *"chuyến đi cuối năm"*. Và thời
gian tụt theo: phần lớn đề chỉ còn **một** lượt thử (77–140s) thay vì ba.

**Câu thêm vào, cố ý hẹp:**

```
BẮT BUỘC: câu đầu tiên phải nhắc tới {chu_de} — dùng lại chính những
chữ đó trong câu mở, rồi mới kể tiếp bình thường.
```

Ràng buộc **đúng câu đầu**, và *"rồi mới kể tiếp bình thường"* để giữ giọng kể.

**VÀ CÁI GIÁ ĐÃ BIẾT TRƯỚC CŨNG HIỆN RA — đo được, phải nói:**

```
từ/câu trung vị    nền 16,9  →  sau 19,2     (+2,3)
1 lượt chạm trần   23,65 > 22,73 → "cắt kiểu gì cũng trượt", sinh lại thì qua
giá trị sát trần   22,18 · 22,73 · 21,73
```

Câu **dài ra thật**, đúng như chú thích `_loi_bai_noi` cảnh báo từ 03/09. Nó
nhỏ vì câu thêm vào chỉ ràng buộc câu đầu — nhưng ba lượt đã nằm sát trần
22,73. **Nếu trần ấy có ngày bị siết, chỗ này gãy trước.** Ghi ra để lần sau ai
động vào `TRAN_TU_MOI_CAU` thì biết nó không còn nhiều biên.

Gieo 4 phép, cả 4 đỏ.

**n = 8 LÀ NHỎ, nói ra chứ không giấu.** Model có nhiệt độ 0,8; hai lượt cùng
đề ra hai kết quả khác nhau. Ghép cặp cùng đề bù được phần lớn nhưng không hết.
Một thay đổi làm 10 → 6 chưa chắc là thật; 10 → 0 thì khó là nhiễu.

### 2c. BỘ DỰNG THỨ HAI: REMOTION (06/09/2026)

`sinh_the_hinh` vẽ ảnh **TĨNH** bằng PIL rồi ffmpeg chiếu mỗi ảnh một khoảng —
mỗi thẻ là một khung đứng yên, không có gì chuyển động được vì thứ duy nhất tồn
tại là một tệp PNG. Remotion dựng **lại từng khung** bằng React, nên chữ hiện
dần, nhích lên, và thanh tiến độ chạy theo đúng mốc đo được ở mục 2b.

**Đo trước khi dựng, trên chính máy này (không GPU rời):**

```
cài            2m06s · 215 MB · 13.471 tệp · 149 gói cấp 1
120 khung      76,0s   <- gần hết là chi phí MỘT LẦN: tải + bung Chromium
480 khung      18,8s
1440 khung     45,3s (scratchpad) · 47,7s (trong kho)
ra             60,05s · 720×1280 · h264 · 4,13 MB
```

Suýt ngoại suy từ con số đầu: 76 giây cho 5 giây video đọc ra thành "chậm gấp
30 lần, không dùng được". Đo tiếp thì 480 khung chỉ mất 18,8s — **gấp bốn số
khung trong một phần tư thời gian**. Một điểm không tách được chi phí cố định
khỏi chi phí biên.

**Giấy phép — kiểm trước tiên, theo Chương 7 mục 3.** Remotion **KHÔNG phải
MIT**: giấy phép riêng, miễn phí cho cá nhân và tổ chức **≤ 3 người**, được
dùng thương mại để làm video, **cấm bán lại hoặc cấp phép lại chính Remotion**.
OPC nằm trong diện miễn phí.

**Đặc tả:**

* `FPS 24 · RONG 720 · CAO 1280` khai trong `remotion/src/Root.tsx`, chép tay
  vào cửa canh — không đọc từ `core.phong_alpha`, kẻo hai vế cùng đổi.
* **Độ dài suy từ `moc`** qua `calculateMetadata`, không gõ `durationInFrames`.
  Đóng đinh nó là dựng lại đúng phép chia đều vừa gỡ ở mục 2b.
* **`Props` chỉ nhận `cau` và `moc`.** Không nhận đường dẫn `.srt`, và
  `render_remotion` chỉ nhận `(cau, moc, ra)`.

  > **PHỤ ĐỀ VẪN LÀ TỆP `.srt` RIÊNG.** Sức hút của Remotion là vẽ chữ thành
  > một phần khung hình, nhưng `core/phong_alpha.py` ghi thẳng: *"nung vào thì
  > không ai kiểm được bằng máy, còn luồng phụ đề thì `ffprobe` đọc ra"*.
  > Remotion không được nới luật ấy ra.

* **Không thêm một dòng nào vào `requirements.txt`.** Remotion là Node; hàng
  rào `V3_PHONG` lần theo `import` Python nên tệp `.tsx` không đụng trần.
* **`remotion/node_modules` phải bị git bỏ qua** — 215 MB, 13.471 tệp.

**CHẤM HAI BỘ, CÙNG ĐẦU VÀO, CÙNG BỘ CỬA (06/09/2026).** Cùng `van_ban`, cùng
`voice.wav`, cùng `moc`, cùng `phu_de.srt`, cùng nhạc nền. Khác đúng **một
biến**: ai vẽ khung hình.

```
                          A · PIL+ffmpeg    B · Remotion
lệch chữ–hình lớn nhất       0,293s           0,110s     <- B tốt hơn ~3 lần
đoạn đứng yên lâu nhất         0,0s           4,92s      <- B XẤU
số đoạn tĩnh                      0             15       <- B XẤU
số lần đổi cảnh                  31             20
kích thước tệp               3,91 MB        2,05 MB
thời gian dựng                  31s            45s
kiem_video · kiem_phu_de        ĐẠT            ĐẠT
```

**KẾT LUẬN: CHƯA ĐỔI MẶC ĐỊNH.** B thắng chỗ đồng bộ và dung lượng, nhưng
thành phần Remotion chỉ động **0,4 giây đầu mỗi thẻ**, sau đó chỉ còn thanh
tiến độ 6px — `freezedetect` đọc là đứng yên. Đó đúng kiểu hỏng đã ghi ở đầu
`core/phong_alpha.py`: *"bốn tấm ảnh chứ không phải video"*. B phải có chuyển
động liên tục rồi mới thay được A.

> **PHÉP CHẤM NÀY CHẶN ĐƯỢC MỘT LẦN ĐỔI SAI, VÀ BẮT ĐƯỢC MỘT LỖI ẨN.** Mọi cắt
> cảnh của bản Remotion lệch phụ đề đúng **0,735–0,769 giây** — một độ lệch
> HẰNG SỐ, bằng chính khe im lặng. Rút một khung trong khe ra nhìn thì thấy:
> màn hình hiện **"THẺ 13/13"**, trắng chữ, thanh tiến độ rỗng. `findIndex` trả
> `-1` trong khe và nhánh lui nhảy về thẻ cuối — **nháy 12 lần** trong một
> video 60 giây. `kiem_video` cho **ĐẠT**: nháy 0,76 giây thì không đen, không
> đứng yên, không cửa nào bắt.

> **HAI PHÉP ĐO ĐẦU CỦA TÔI ĐỀU KHÔNG DÙNG ĐƯỢC, và lý do đáng ghi.** Dò cắt
> cảnh trên bản ĐÃ NUNG chữ thì chữ phụ đề đổi cũng tính là đổi cảnh: 13 thẻ
> phải 12 cắt, đo ra 35 · 18 · 10 · 0 tuỳ ngưỡng. Chuyển sang bản **chưa nung**
> thì A ra đúng 12 — nhưng lẫn nhiễu do Ken Burns phóng, nên số 2,572s là rác.
> Thứ dùng được là hỏi **nhãn "THẺ i/N" đổi lúc nào**, tìm bằng chia đôi: 12/12
> ranh giới đo được ở cả hai bộ.

**CHƯA THAY BỘ DỰNG CŨ.**

### 2d. PHỤ ĐỀ THEO TỪNG TỪ — CĂN BẰNG TIẾN TRÌNH RIÊNG, KHÔNG KÉO 10 GÓI VÀO (07/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**. Trả món nợ ghi từ 06/09: *"phụ đề sang từng từ —
OneCore không trả timestamp theo từ"*.

**Đo trước khi nối**, `voice.wav` 60,00s · 12 đoạn · 245 từ, có sẵn lời gốc:

```
model   RTF    thời gian   WER      TỪ GỐC CÓ MỐC     phán quyết
base    0,23     13,7s     17,1%    205/245  83,7%    KHÔNG ĐẠT
small   0,63     38,1s      6,9%    228/245  93,1%    ĐẠT cả hai
                           ≤15%            ≥90%
```

**Ngưỡng WER ≤ 15% và KHỚP ≥ 90% viết ra TRƯỚC khi chạy vòng đo ấy**, không
phải sau. Chép tay xuống cửa canh.

**VÒNG ĐO ĐẦU CHẤM SAI, VÀ SAI THEO ĐÚNG BỆNH ĐÃ GHI.** Chỉ tiêu đầu đếm *số
từ*: `base` ra **247/245 = 100,8%** và được chấm ĐẠT, trong khi nó phiên
*"**Này** hôm nay"* cho *"**Ngày** hôm nay"*. Một bản phiên sai cả 245 từ vẫn
đếm ra 245 từ. Đổi sang WER + chuỗi con chung dài nhất thì thứ tự **lật ngược**:

```
đếm số từ      base 100,8%  >  small 100,0%
so khớp thật   base  83,7%  <  small  93,1%
```

Đúng bài *"đừng tự chấm điểm bằng dò chuỗi con"* đã ghi 12/08.

**CÂU HỎI CỦA AURA KHÔNG PHẢI "PHIÊN DỊCH ĐÚNG KHÔNG".** AURA **đã biết lời** —
chính nó sinh giọng từ lời ấy. Việc cần là **gắn mốc cho lời đã biết**. Nên
phép đo là: chuyển mốc từ bản phiên sang lời gốc qua chuỗi con chung dài nhất.
17/245 từ không khớp thì nội suy từ hai từ kề.

**KHÔNG ĐƯA `faster-whisper` VÀO `requirements.txt`.** Nó kéo theo
`ctranslate2` · `onnxruntime` · `av` · `numpy` · `tokenizers` · `huggingface-hub`
— đo được **273 MB và 10+ gói**, cộng 605 MB model. `CLAUDE.md` mục 1 lấy con số
**2 gói ngoài** làm lý do v3 tồn tại; đẩy nó lên 12 là tự tay dựng lại v2.

Nối theo **đúng khuôn đã dùng cho `node` và `bash`** ở phòng `epsilon`:

* **Tiến trình riêng, venv riêng, tìm bằng ĐƯỜNG DẪN TUYỆT ĐỐI.** Biến môi
  trường `AURA_STT_PYTHON` trước, rồi tới danh sách chỗ quen. Kho model đi
  cùng ổ với `F:\ollama-models` — ổ C chỉ còn 26,7 GB, F còn 61 GB.
* **Không có bộ căn thì `KHONG_DO_DUOC`**, và video vẫn dựng xong với phụ đề
  theo ĐOẠN như cũ. Không được rơi xuống `FAIL`, cũng tuyệt đối không `PASS`.
* **Worker chỉ sinh mốc, KHÔNG tự chấm.** `tools/can_tung_tu_worker.py` in ra
  JSON mốc từng từ; `core/can_chu.py` mới là chỗ tính WER · KHỚP và ra phán
  quyết. Đúng luật chương VIII: *"Runner chỉ sinh file; Verifier độc lập mới
  có quyền ghi trạng thái."*

**HAI LUỒNG PHỤ ĐỀ, HAI VIỆC KHÁC NHAU — KHÔNG ĐƯỢC GỘP:**

```
luồng RỜI (.srt, theo ĐOẠN)   -> để MÁY kiểm; `ffprobe` đọc ra; gates cũ dùng
chữ NUNG   (.ass, theo TỪ)    -> để NGƯỜI xem; karaoke `\kf` quét theo giọng
```

Chú thích sẵn có ở `render` viết: *"luồng rời để KIỂM, chữ nung để XEM"*. Bản
theo từ **chỉ thay phần NUNG**. `phu_de.srt` giữ nguyên, nên `kiem_phu_de` và
phép đo lệch chữ–hình **0,036 s** không bị đụng tới. Thay cả hai là đúng bài
*"vá một nửa của một cặp"* — chỉ khác là lần này phá cái đang chạy được.

**Đặc tả — chép TAY vào cửa canh:**

* `DAC_TA_CAN_WER_TRAN = 0,15` · `DAC_TA_CAN_KHOP_SAN = 0,90` · model `small`.
* **Mốc từ phải TĂNG DẦN** và nằm trong `[đoạn.đầu − 0,30 ; đoạn.cuối + 0,30]`.
* **Từ không khớp thì NỘI SUY giữa hai từ kề**, không bỏ trắng — bỏ trắng thì
  chữ biến mất giữa câu.
* **`.ass` phải làm chữ ĐỔI theo thời gian.** Hai khung trong CÙNG một đoạn,
  ở hai mốc từ khác nhau, phải KHÁC nhau ở dải phụ đề. Chỉ kiểm "có chữ" thì
  một bản karaoke đứng im vẫn qua — đúng lỗ đã để lọt bản Remotion nháy 0,76 s
  mà `kiem_video` vẫn cho ĐẠT.
* **Ca đối chứng:** gieo cho bộ căn biến mất → phòng phải vẫn dựng xong video
  và trả `KHONG_DO_DUOC` cho riêng phần căn chữ, **không** đỏ cả lượt.

**NGƯỠNG NÀY FIT TỪ ĐÚNG MỘT MẪU, VÀ ĐO THÊM THÌ 6/6 KỊCH BẢN KHÁC TRƯỢT.**

Đo 07/09 sau khi nối, trên sáu kịch bản chưa từng dùng để đặt ngưỡng:

```
                    WER            khớp          phán quyết
lặp khuôn   ×3   16,9–72,9%    27,1–83,2%     KHÔNG ĐẠT
văn tự nhiên ×3  10,2–16,3%    83,7–89,8%     KHÔNG ĐẠT  <- sát sàn
mẫu đặt ngưỡng        6,9%          93,1%     ĐẠT
```

Cái duy nhất đạt là **chính cái đã dùng để đặt ngưỡng**. Nghĩa là karaoke hiện
**rất ít khi bật** trên nội dung mới. Nói ra chỗ này chứ không giấu: tính năng
đã nối, đã đo, và **đang gần như không chạy**.

Lặp khuôn là một biến lớn (72,9% → 10,2%) — bộ nhận dạng hỏng nặng trên tiếng
lặp — nhưng kể cả văn tự nhiên vẫn dừng ở 83,7–89,8%.

**VÀ SÀN 90% CÓ THỂ ĐANG ĐO SAI THỨ.** Từ không khớp được nội suy giữa hai từ
neo, nên sai số của nó CÓ CHẶN. Đo bằng **phép giữ lại** — giấu 1 trong mỗi 7
từ đã khớp, bắt bộ nội suy đoán lại, so với mốc thật:

```
83 từ bị giấu:  trung vị 0,000s · p90 0,110s · tối đa 0,400s
                lệch quá 0,30s: 1/83 = 1,2%
```

Tức 14% từ được nội suy gần như **miễn phí về thời gian**. Thứ người xem thấy
là chữ sáng lệch bao nhiêu GIÂY, không phải bao nhiêu phần trăm từ khớp ASR.

**NHƯNG KHÔNG ĐỔI NGƯỠNG TRONG LƯỢT NÀY.** Ca đối chứng dựng để chứng minh cửa
mới biết đỏ — kịch bản lặp khuôn — lần chạy sau lại ra **81,4%** thay vì 27,1%,
và sai số nội suy của nó vẫn nhỏ (tối đa 0,258s). Cửa mới **chưa từng đỏ**, nên
theo đúng luật của chính tệp này, nó chưa chứng minh được gì. Đổi sang một cửa
chưa ai đi qua là thay một điểm tự thưởng bằng một điểm tự thưởng khác.

**Nợ để lại, ghi rõ:** dựng cho được một ca mà phép đo sai số nội suy PHẢI đỏ,
rồi mới bàn tới việc đổi ngưỡng. Chưa có ca ấy thì `KHOP_SAN = 0,90` ở lại, và
lời mô tả phải nói rằng karaoke hiếm khi bật.

### 2d-bis. ĐỔI NGƯỠNG: TỪ "BAO NHIÊU % TỪ KHỚP" SANG "LỆCH BAO NHIÊU GIÂY" (07/09/2026)

Sếp bảo sửa ngưỡng. Sửa được, nhưng phải sửa **phép đo trước** — vì phép giữ
lại của bản trước có một lỗ.

**LỖ: GIẤU RẢI RÁC LÀ ĐO CA DỄ.** Bản trước giấu 1 trong mỗi 7 từ, nên mọi từ
bị giấu đều nằm **giữa hai neo**. Nội suy một từ đơn giữa hai neo gần như không
thể sai — trung vị 0,000s — và tôi suýt kết luận cho cả bài từ con số ấy. Chỗ
hỏng thật không có hình dạng đó: từ trượt đi thành **chuỗi liền nhau**.

Đo lại, giấu theo chuỗi:

```
                      chuỗi trống THẬT      p90 sai số nội suy khi giấu chuỗi dài
                   số chuỗi · dài nhất       1        3        6       10
tài chính  89,8%      17    ·    3        0,050    0,140    0,200    0,229
văn xuôi   83,7%      22    ·    5        0,040    0,160    0,166    0,386
lặp khuôn  81,4%      29    ·    4        0,040    0,100    0,128    0,106
```

Hai điều đọc ra: **chuỗi trống thật rất ngắn** (trung vị 1, dài nhất 3–5), và
**phép đo có nhạy** — p90 đi từ 0,04s lên 0,386s theo độ dài chuỗi. Cửa mới
biết đỏ, khác hẳn lần trước khi tôi không dựng nổi một ca đỏ.

**NGƯỠNG MỚI, LẤY TỪ NGUYÊN TẮC CHỨ KHÔNG TỪ KẾT QUẢ:**

```
DAC_TA_CAN_TY_LE_NUA_TU = 0,5
ngưỡng = 0,5 × (độ dài TRUNG VỊ của một từ, đo từ chính lượt ấy)
```

Đo được: từ dài trung vị **0,200s** trên cả ba kịch bản → ngưỡng **0,100s**.
Lý lẽ: lệch quá **nửa từ** thì vệt sáng karaoke nằm sang từ bên cạnh, và người
xem thấy chữ sáng sai chỗ. Ngưỡng **tự hiệu chỉnh theo từng lượt** — đọc nhanh
thì từ ngắn, ngưỡng chặt lại theo.

**BỎ `KHOP_SAN = 0,90` LÀM CỬA, VÀ ĐÂY LÀ LÝ DO:**

Một từ chỉ trở thành neo khi nó **khớp đúng chữ** trong lời gốc, nên từ bị phiên
sai **không** thành neo — nó chỉ làm neo THƯA hơn. Neo thưa thì chuỗi trống dài
ra, và chuỗi trống dài thì sai số nội suy tăng. Tức `khop` và `WER` tác động lên
chất lượng **qua đúng một đường**, và đường ấy là thứ ngưỡng mới đo thẳng.

Giữ chúng làm **số ghi sổ**, không làm cửa. Một cửa đo hệ quả thì tốt hơn hai
cửa đo nguyên nhân — nhất là khi hai con số kia được đặt từ một mẫu duy nhất.

**GIỚI HẠN CỦA NGƯỠNG MỚI, NÓI RA:** phép giữ lại lấy chính các neo làm mốc
đúng, nên nó đo **chất lượng NỘI SUY**, không đo **chất lượng NEO**. Neo sai
chỗ do trùng chữ ngẫu nhiên thì nó không thấy — thứ chặn việc ấy là LCS giữ
đúng thứ tự, không phải bài này.

**Không đo được thì `KHONG_DO_DUOC`:** ít neo tới mức không giấu nổi một chuỗi
nào thì chưa kết luận được, và đó là nhánh thứ ba chứ không phải `KHONG_DAT`.

**ĐO SAU KHI ĐỔI — CỬA MỚI XẾP HẠNG KHÁC CỬA CŨ, VÀ KHÁC ĐÚNG CHỖ:**

```
             khớp     p90 / ngưỡng     cũ (khớp≥90%)   mới
tài chính   89,8%    0,087 / 0,100     KHÔNG ĐẠT      PASS
kỹ thuật    86,7%    0,210 / 0,100     KHÔNG ĐẠT      KHÔNG ĐẠT
văn xuôi    83,7%    0,067 / 0,100     KHÔNG ĐẠT      PASS
```

`văn xuôi` khớp **thấp nhất** mà đạt; `kỹ thuật` khớp cao hơn lại trượt. Hai
trục xếp hạng **ngược nhau** — đó là bằng chứng "% từ khớp" không phải thứ
quyết định chất lượng. Cửa cũ: **0/6 đạt**. Cửa mới: 2/3 đạt trên văn tự nhiên.

**Gieo 5 phép, và hai lần đầu KHÔNG đủ:**

```
lần 1   3/5 đỏ   2 cửa mù
lần 2   4/5 đỏ   1 cửa mù
lần 3   5/5 đỏ
```

Hai chỗ mù, cả hai đáng ghi:

* **Bài canh đọc nhầm trường.** Nó khẳng định `3 in dai_chuoi_trong` — nhưng
  trường ấy là chuỗi trống **ĐO ĐƯỢC**, không đổi khi bộ đo quay về giấu rải
  rác. Gieo `L = 1` thì cửa vẫn xanh. Thêm `dai_da_giau` — độ dài các chuỗi
  **ĐÃ GIẤU** — và hỏi vào đó.
* **Phép gieo không tới nơi, lần thứ tư.** Nhánh `KHONG_DO_DUOC` có bài canh
  hẳn hoi, nhưng tên bài không khớp bộ lọc `-k` của kịch bản gieo, nên nó
  không hề chạy. Công cụ in "VẪN XANH — CỬA MÙ" cho một cửa **chưa từng được
  gọi**. Trước khi ghi "cửa mù", kiểm xem bài định bắt có nằm trong lượt chạy
  không.

### 2d-ter. `ky thuat` TRƯỢT VÌ QUÃNG NGẮT, VÀ MỌI THỨ TRƯỚC ĐÓ CHƯA LÊN MÀN HÌNH (07/09/2026)

Sếp bảo sửa nốt kịch bản trượt (p90 0,210s). **Không nới ngưỡng** — mở bốn từ
lệch nhất ra:

```
0,370  đoạn 11  "đo"     nội suy 53,15  thật 53,52
0,360  đoạn  5  "thì"    nội suy 24,58  thật 24,94
0,360  đoạn  5  "hoặc"   nội suy 23,22  thật 23,58
0,347  đoạn 11  "và"     nội suy 54,49  thật 54,84
```

Cả bốn **sớm hơn thật**, và cả bốn đứng **ngay sau dấu phẩy hoặc hai chấm**.
Đo trên 336 cặp từ liền nhau đều có neo:

```
sau dấu phẩy/hai chấm    15 cặp   khe trung vị 0,360s
từ thường               321 cặp   khe trung vị 0,000s
```

Độ lệch bằng ĐÚNG khe ấy. *Một độ lệch hằng số không phải nhiễu.* `_noi_suy`
chia đều theo SỐ TỪ và không biết dấu câu tồn tại. Vá: trừ quãng ngắt ra trước,
rồi mới chia phần còn lại.

**Và quãng ngắt TỰ ĐO TỪNG LƯỢT, không gõ cứng.** `NGAT_GIAY = 0,36` đo trên
chính hai kịch bản đang chấm — để nó làm hằng số là lại rơi vào "hằng số fit từ
mẫu dùng để kiểm", đúng bẫy vừa mất một lượt để bỏ. Ba kịch bản tự đo ra
**0,38 · 0,36 · 0,34** giây.

```
             p90 TRƯỚC   →   SAU
tài chính      0,087        0,056
kỹ thuật       0,210        0,080
văn xuôi       0,067        0,067
```

**NHƯNG CHỖ ĐẮT NHẤT NẰM SAU ĐÓ, VÀ NÓ LÀM MỌI SỐ TRÊN THÀNH VÔ NGHĨA.**

Khi dựng cửa canh cho phần vừa vá, phát hiện `viet_ass` chỉ mã hoá **độ dài
từng từ**, không mã hoá **khe giữa hai từ**. libass chạy `\kf` NỐI TIẾP từ mốc
đầu Dialogue; nó không biết `moc_tu` tồn tại. Đo trên một đoạn dựng tay có khe
1,00s:

```
từ   mốc THẬT   libass vẽ ở   lệch
t3     1,60s        0,60s    -1,00s
t4     1,90s        0,90s    -1,00s
tổng kf 1,20s / đoạn dài 3,00s
```

Tức **mọi công nội suy chưa bao giờ lên tới màn hình** — kể cả quãng ngắt vừa
vá. Và cửa đếm điểm ảnh vàng vẫn xanh suốt: nó chứng minh chữ **CÓ quét**, chưa
từng chứng minh quét **ĐÚNG LÚC**. Cùng họ với cửa đo Ken Burns tưởng là đo chữ,
lần thứ hai trong một ngày.

Vá ba chỗ, mỗi chỗ một phép đo:
* **Khe đi vào một đơn vị karaoke riêng** mang đúng dấu cách giữa hai từ.
* **Kẹp mốc vào trong đoạn** — mốc từ theo thời gian TOÀN TỆP còn `moc_doan`
  theo phép ghép TTS, nên có từ chạy quá đoạn **0,26s**.
* **Bỏ sàn 1 phần trăm giây.** Từ bị phép kẹp bóp còn 0 giây mà vẫn được cấp
  1cs thì mỗi cái đẩy cả dòng đi 0,01s — đo được **0,02s** trên một đoạn 4 từ.
  `\kf0` hợp lệ và đúng nghĩa: từ ấy không có lúc nào để quét.

**Gieo 10 phép, và phải chạy BỐN LƯỢT mới đủ đỏ:**

```
lượt 1   3/5 đỏ    lượt 3   9/10 đỏ
lượt 2   4/5 đỏ    lượt 4  10/10 đỏ
```

Ba chỗ mù, và **hai trong ba là phép gieo không tới nơi**:

* Bài canh hỏi `dai_chuoi_trong` (chuỗi ĐO ĐƯỢC) trong khi cần hỏi chuỗi ĐÃ
  GIẤU. Gieo `L = 1` đi qua sạch.
* Nhánh `KHONG_DO_DUOC` **có** bài canh, nhưng tên nó không khớp bộ lọc `-k`
  của kịch bản gieo. Công cụ in "CỬA MÙ" cho một cửa **chưa từng được gọi**.
* Phép kẹp có **hai nửa** (trần `kt` và mốc `truoc`); gieo bỏ nửa sau thì cửa
  vẫn xanh vì dữ liệu thử không đi ngược thứ tự. Một cửa chỉ canh được nửa cặp
  thì nửa kia mục đi mà không ai biết.

**Và hai lần chốt bằng con số GÕ RA thay vì TÍNH RA**, cả hai đỏ ngay dù mã
đúng: `> 0,3` cho độ dời (đúng là `0,36 × (1 − 1/3) = 0,24`) và `> 10,3` cho mốc
`t9` (đúng là `6,8`). Ngưỡng trong cửa canh cũng phải suy ra được, y như ngưỡng
trong mã.

**Việc KHÔNG làm trong lượt này:** WhisperX (căn cưỡng bức thật, phủ 100%) kéo
theo `torch` ≈ 2–2,5 GB. Chưa chạy trên máy này nên mọi câu về nó là **đọc
thấy**, không phải **đo được**.

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

     <!-- CHOT:no-network -->
     **08/09/2026 — vá được MỘT PHẦN, xem mục hộp cát ở dưới.** Nay có
     `core/hop_cat.py`: cwd riêng · biến môi trường sạch (87 → 9) · trần RAM
     256 MB · giết cả cây tiến trình. Nhưng **ngắt mạng thì VẪN CHƯA CHẶN
     ĐƯỢC** — đo lại 08/09, `urlopen` vẫn trả mã 200. Dòng "no-network" ở trên
     vẫn là một lời hứa chưa giao.

     **Đã thử và thất bại, ghi lại để lần sau khỏi thử lại từ đầu:** máy không
     có Docker/WSL và tài khoản không phải Administrator, nên tường lửa loại.
     AppContainer tạo được profile nhưng **Python không khởi động nổi bên
     trong** (mã thoát 106 → 1 → không ghi nổi cả tệp lỗi). Cần quyền admin
     hoặc một môi trường container mới giao được.
     <!-- /CHOT:no-network -->
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

### 5b. THẺ PHẢI CHẠY ĐÚNG PHÒNG NÓ KHAI (06/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**, theo Chương 7 của `CLAUDE.md`.

Đo cái lỗ trước, bằng cách thay mọi phòng bằng bản giả rồi **đếm phòng nào được
gọi** — không dò chuỗi trong mã:

```
thẻ                        KHAI cac_phong              CHẠY THẬT
card_video_shorts          zeta,aura,alpha,omega       zeta,aura,alpha,omega,gamma
card_code_doctor           delta,gamma                 zeta,aura,alpha,omega,gamma
card_polyglot_transpiler   delta,gamma,omega           zeta,aura,alpha,omega,gamma
card_deep_scout            zeta,aura,omega             zeta,aura,alpha,omega,gamma
card_novel_writer          aura,gamma                  zeta,aura,alpha,omega,gamma
card_fullstack_builder     aura,delta,alpha            zeta,aura,alpha,omega,gamma
card_security_guard        delta,gamma,omega           zeta,aura,alpha,omega,gamma
card_system_audit          gamma,omega                 zeta,aura,alpha,omega,gamma
                                                       khớp 0/8
```

`delta` chưa từng được thẻ nào gọi tới, dù **bốn** thẻ khai nó. Và giá không chỉ
là sai nhãn: `card_code_doctor` xin một lượt quét AST (~2 giây) thì nhận cả
`aura` + `alpha` — **166 giây** cho một việc không ai đặt hàng.

Cùng họ với *"7 phòng tự khai ONLINE, 0 phòng phải chứng minh"* (02/09) và
*"33 cờ, 29 cái TẮT"* của v2: một trường được khai, không ai đọc.

**Đặc tả — chép TAY vào cửa canh, đừng tính lại bằng chính mã:**

* `DAC_TA_CHUOI_MAC_DINH = zeta · aura · alpha · omega · gamma` — dùng khi
  **không** gửi `preset_id`, hoặc gửi một `preset_id` không có trong danh mục.
  Đường của giao diện: id lạ **không được** làm đổ cả lượt chạy.
* `DAC_TA_SAN_PHONG = 1`, `DAC_TA_TRAN_PHONG = 8` cho `cac_phong` của mỗi thẻ.
  Trần dùng chung con số với chuỗi tùy biến, cùng một lý do: một lượt `aura`
  tốn tới 273 giây.
* **`alpha` chỉ hợp lệ khi có `aura` đứng TRƯỚC nó trong cùng thẻ.** `alpha` ăn
  kịch bản của `aura`; thiếu thì nó không có gì để dựng.
* **MỘT bảng mô tả phòng duy nhất** (`MO_TA_PHONG`), dùng chung cho bộ chạy, API
  danh mục, và sơ đồ trên màn hình. Ba bảng thì chúng trôi khỏi nhau — đúng bệnh
  `presetPrompts` gõ cứng trong `noi_bo.js` đang mắc (xem "còn nợ" dưới).
* **Sơ đồ trên màn hình phải dựng TỪ chuỗi của thẻ**, không phải 5 ô gõ cứng
  trong HTML. Chạy 2 phòng mà vẽ 5 ô thì ba ô đứng im mãi mãi — một lời nói dối
  mới đặt lên đúng cái vỏ vừa làm cho trong suốt.

**Còn nợ khi vá xong mục này — đã trả ở mục 5c ngay dưới.**

### 5c. MỘT THẺ, MỘT BẢN KHAI (06/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**.

Vá xong mục 5b thì máy chủ chạy đúng `cac_phong`. Nhưng thẻ được khai ở **ba
chỗ**: `DANH_SACH_THE_QUY_TRINH` (Python), 8 khối `.preset-card` gõ cứng trong
`noi_bo.html`, và bảng `presetPrompts` gõ cứng trong `noi_bo.js`. Đo độ lệch
giữa chúng:

```
tên thẻ            lệch 7/8
mô tả              lệch 8/8
biểu tượng phòng   lệch 6/8
đề mặc định        lệch 8/8
```

Không phải lệch câu chữ. Lệch **nội dung**:

* `card_code_doctor` hiện **ba** biểu tượng phòng cho chuỗi **hai** phòng, và
  🛡️ không phải phòng nào cả. `card_novel_writer` hiện 📜, `card_system_audit`
  hiện 🛡️ — cùng kiểu.
* `card_system_audit` hứa *"xác thực toàn bộ 714 test cases"*. Bộ test hôm nay
  **893**. Con số gõ tay tụt lại sau phép đo, đúng bệnh câu *"đúng 17 tệp"* của
  `CLAUDE.md`.
* `card_code_doctor` hứa *"Tự sinh bản vá & chạy kiểm thử"*, trong khi mục 5
  của chương này ghi thẳng: **`delta` KHÔNG tự sửa mã**. Màn hình hứa đúng cái
  thứ đặc tả cấm.

**Đặc tả:**

* **MỘT nguồn khai duy nhất là `DANH_SACH_THE_QUY_TRINH`.** `noi_bo.html` để
  trống lưới thẻ; `noi_bo.js` dựng thẻ từ `/api/pipeline/presets`; `presetPrompts`
  bị xoá, đề mặc định lấy từ `tham_so_mac_dinh`.
* **Dãy biểu tượng phòng SINH RA từ `so_do`**, không gõ tay — để nó đúng *bằng
  cấu trúc*, không bằng kỷ luật người sửa.
* **Lời thẻ hứa phải đối chiếu với một lượt CHẠY THẬT.** Chuyển prose từ HTML
  sang màn hình mà không kiểm là dời một lời hứa chưa ai đo sang chỗ dễ tin
  hơn. Câu nào lượt chạy bác thì sửa câu, kèm số.
* **Ô nhập chủ đề phải giữ được xuống dòng.** Hai thẻ mang cả đoạn mã trong
  `tham_so_mac_dinh`; `<input type="text">` **nuốt `\n` không báo**, nên thứ gửi
  đi khác thứ thẻ khai. Đổi sang `<textarea>`.
* **Bấm thẻ phải đi qua uỷ nhiệm sự kiện.** Thẻ nay dựng SAU khi gán trình nghe;
  gán lên từng thẻ lúc khởi động thì không thẻ nào nghe được.

**Chạy thật cả 8 thẻ trước khi đưa lời thẻ lên màn hình (06/09/2026):**

```
thẻ                       chạy thật                       lời hứa
card_video_shorts         PASS 4/4 · 216s · 21 hiện vật   ĐÚNG
card_code_doctor          PASS 2/2 ·  48s ·  2            "sinh bản vá tự động" — không có
card_polyglot_transpiler  PASS 3/3 ·  39s ·  3            "dịch sang JS/Go/Rust…" — 0 dòng dịch
card_deep_scout           PASS 3/3 · 217s ·  3            "đối chiếu bằng chứng URL" — không đối chiếu
card_novel_writer         PASS 2/2 · 170s ·  2            "3 chương · TTR · giác quan" — 1 kịch bản 240 từ
card_fullstack_builder    FAIL 0/3 · 287s ·  0            "HTML5/CSS3 + API aiohttp" — 0 hiện vật
card_security_guard       PASS 3/3 ·  83s ·  3            "chống lộ API Key · Path · injection" — không cái nào
card_system_audit         PASS 2/2 ·  48s ·  2            "đo RAM/CPU" — không đo CPU
```

`mo_ta` đã sửa theo lượt chạy, chỗ chưa làm được viết **CHƯA**. Hai điều ghi lại
để không phải đo lại:

* `card_polyglot_transpiler` và `card_security_guard` **chạy y hệt nhau** —
  cùng chuỗi `delta · gamma · omega`, và `chan_doan.json` của cả hai đều 119
  byte với đúng bốn con số đếm. Hai thẻ, hai lời hứa, một hành vi.
* `card_fullstack_builder` **gãy trên chính đề mặc định của nó**: `aura` cho
  23,89 từ/câu (trần 22,7) nên hai bước sau không chạy. **KHÔNG đổi đề cho nó
  qua cửa** — đề "bảng điều khiển tài chính" là đề GIẢI THÍCH, đúng ca đã đo
  05/09; đổi đề để thẻ trông chạy được là làm cho một thẻ hỏng trông đỡ hỏng.

**TÊN THẺ ĐÃ ĐỔI THEO (Sếp quyết cùng ngày).** Lượt trước tôi chỉ đổi
`card_code_doctor` và báo "còn hai tên sai". Đọc lại cả tám thì là **năm**:

```
Polyglot Cross-Compiler          -> Quét AST Toàn Kho (chưa dịch mã)
Trinh Sát & Kiểm Chứng Sự Thật   -> Trinh Sát Nguồn (chưa kiểm chứng)
Viết Truyện Đời Thường Dài Hơi   -> Viết Một Kịch Bản Truyện 215–250 Từ
Sinh App Fullstack Web           -> Viết → Quét AST → Dựng Video (đang gãy)
Kiểm Toán Bảo Mật & Secret Leak  -> Quét AST Toàn Kho (chưa quét khoá)
```

* **Hai thẻ AST nay trùng tên gần hết và trùng biểu tượng — cố ý.** Chúng chạy
  y hệt nhau; đặt hai cái tên nghe khác nhau cho một hành vi là giấu đúng thứ
  vừa đo ra.
* **`ten` không mang emoji nữa.** `bieu_tuong` là icon duy nhất trên thẻ, nên
  hai trường không được cãi nhau (trước đó 🩺 trong tên đứng cạnh 🔧 ở huy
  hiệu). Và vì nó là icon duy nhất, nó cũng là một lời khai: 🔒 · 🛡️ · 🌐 · 💻
  đã đổi, chúng báo hiệu việc mà chuỗi không làm.
* **Ba việc không phòng nào làm**, chốt trong `tests/`: *tự sửa mã* · *dịch mã*
  · *quét khoá*. Thẻ không được hứa, kể cả trong tên. Đây là **bộ chặn từ**,
  không phải phép chứng minh — nói tránh đi thì nó trượt; nó chỉ giữ cho những
  cụm đã từng nằm trên màn hình không quay lại y nguyên.
* **Và bộ chặn từ phải có ca đối chứng**, nếu không cách dễ nhất để qua nó là
  **bỏ hết chữ CHƯA** — tức cửa chống nói dối lại thưởng cho việc im lặng. Bảy
  thẻ có việc lượt chạy bác thì bảy `mo_ta` phải nói ra giới hạn, chốt theo
  từng thẻ.

### 5d. PHÒNG `epsilon` — DỊCH MÃ, VÀ CHỈ KHAI ĐẠT CHO THỨ KIỂM ĐƯỢC (06/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**.

`core/polyglot.py:574 chuyen_doi_ngon_ngu` dịch **thật** — đi bằng
`ast.NodeVisitor`, 5 nút, mỗi ngôn ngữ ra một dạng khác nhau. Nhưng **không
phòng nào gọi nó**, nên thẻ Polyglot phải viết *"chưa dịch mã"* trong khi bộ
dịch nằm ngay trong kho.

**Đo trước khi nối. Hỏi trình biên dịch THẬT, không hỏi `status`:**

```
             polyglot tự khai   HỎI TRÌNH BIÊN DỊCH   (04/09)
bash         PASS               FAIL                  <-- LỆCH
javascript   PASS               PASS
sql          FAIL               (không có bộ kiểm)
cpp go rust typescript  PASS    KHÔNG ĐO ĐƯỢC
```

*(Bảng trên là ĐO NGÀY 04/09 và giữ nguyên. `go` đã đổi — xem ngay dưới.)*

Máy này khi ấy chỉ có `node` và `bash`. Không có go · rustc · g++ · sqlite3.

Hai chỗ hỏng đọc thấy mà **không bộ kiểm nào trên máy này chứng minh được**:
`go` khai `func Fibonacci` rồi gọi `fibonacci` (hàm không tồn tại); `rust` sinh
`fn fibonacci(n)` không kiểu tham số, không kiểu trả về. Ghi lại là **đọc thấy**,
không phải **đo được** — hai câu khác nhau.

<!-- CHOT:epsilon-go -->
**08–09/09/2026 — `go` ĐÃ SANG ĐO ĐƯỢC, VÀ PHÒNG SUÝT KHÔNG BIẾT.**

Cài Go 1.27.1 (mục *"Bộ dịch `go`"*) thì `gofmt -e` vào được `TRINH_KIEM` và
kiểm Go **cả hai chiều**: tệp hợp lệ → `PASS`, tệp hỏng → `FAIL` kèm
`:2:15: expected '}', found 'EOF'`.

Nhưng `KIEM_DUOC` — danh sách phòng THẬT SỰ hỏi — **vẫn chỉ có ba chữ**
`javascript · bash · python`. Tức máy kiểm được Go từ 08/09 mà phòng vẫn trả
`KHONG_DO_DUOC`, đúng ca *"một khả năng có sẵn mà không ai gọi thì bằng
không"*. Bản vá hôm trước nối `TRINH_KIEM` mà quên `KIEM_DUOC` — **vá một nửa
của một cặp**, lần thứ hai.

**VÀ CỬA CANH KHÔNG BẮT ĐƯỢC, VÌ NÓ TAUTOLOGICAL.**
`test_epsilon_hang_so_khop_DAC_TA` so `set(KIEM_DUOC)` với
`DAC_TA_EPSILON_KIEM_DUOC` — **hai danh sách gõ tay, so với nhau**. Không vế
nào đối chiếu với thứ máy làm được, nên nó xanh vĩnh viễn dù thực tế đổi thế
nào. Cùng họ với `_co_ollama` và `_tim_trinh` bắt được hôm 08/09: máy dò và
thứ bị dò là một.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| `KIEM_DUOC` | `bash · go · javascript · python` — **4** |
| `DICH_MAC_DINH` (suy ra, bỏ nguồn `python`) | `bash · go · javascript` |
| phòng chạy `MA_TOT` với 3 đích | **PASS · 3 ngôn ngữ qua trình thật** |
| ràng buộc MỚI, KHÔNG tautological | mọi ngôn ngữ có trình kiểm **tìm thấy trên đĩa** phải nằm trong `KIEM_DUOC` |

Ràng buộc cuối là thứ đáng giá: nó nối **danh sách khai** với **năng lực đo
được**, chứ không nối hai danh sách khai với nhau. Cắm thêm một bộ kiểm mà quên
cho phòng dùng thì nó ĐỎ.

Chiều ngược lại **cố ý không có cửa**: `KIEM_DUOC` được phép kể tên một ngôn
ngữ mà máy này chưa có trình kiểm — khi ấy phòng trả `KHONG_DO_DUOC`, và đó là
đúng ba trạng thái. Bắt nó đỏ thì mọi máy thiếu công cụ đều đỏ, và cửa ấy chỉ
đo được máy chứ không đo được mã.
<!-- /CHOT:epsilon-go -->

**Đặc tả — chép TAY vào cửa canh:**

* `DAC_TA_EPSILON_KIEM_DUOC = javascript · bash · python · go` — đúng **bốn**
  ngôn ngữ có bộ kiểm trên máy này kể từ 09/09. Mọi ngôn ngữ khác trả
  `KHONG_DO_DUOC`, **không** trả `PASS`. `node --check` · `bash -n` ·
  `ast.parse` · `gofmt -e`.

  > Dòng này trước 09/09 ghi *"đúng ba ngôn ngữ"* và đúng lúc ấy. Cài Go xong
  > thì nó tụt lại sau phép đo suốt một ngày — cùng bệnh với câu *"đúng 17
  > tệp"* mà `CLAUDE.md` đã ghi. Nay có cửa canh nối thẳng danh sách này với
  > trình kiểm tìm được trên đĩa, nên nó không tụt lại lần nữa.
* `DAC_TA_EPSILON_DICH_MAC_DINH = bash · javascript` — **đích mặc định bỏ chính
  ngôn ngữ nguồn.** `python` ở lại danh sách KIỂM ĐƯỢC (nó là bộ kiểm), nhưng
  làm ĐÍCH thì nó là phép đồng nhất.

  > **PHÉP ĐỒNG NHẤT LÀ MỘT ĐIỂM TỰ THƯỞNG.** Bản đầu của phòng xin cả ba ngôn
  > ngữ, và `python` ra `PASS`: `chuyen_doi_ngon_ngu(ma, "python", "python")`
  > trả lại **y byte** mã vào, rồi `ast.parse` đạt — nhưng nó đạt vì MÃ VÀO hợp
  > lệ, thứ đã kiểm ở đầu hàm. Bắt được bằng cách mở `ban_dich.py` ra so với mã
  > vào, không bằng đọc mã. Cùng bẫy tautological đã dính 02/09 và 04/09.
  >
  > Và nó kéo theo cái thứ hai: `mo_ta` của thẻ nói *"sang JavaScript và Bash"*
  > trong khi mặc định xin **ba**. Đúng bệnh cả ngày hôm nay đi vá — thẻ khai
  > một đằng, máy chạy một nẻo — tự tạo ra ngay trong lượt vá.
* **Trạng thái phòng, ba nhánh không gộp:** `FAIL` khi có ít nhất một ngôn ngữ
  *kiểm được mà hỏng* · `KHONG_CHAY_DUOC` khi **bất kỳ ngôn ngữ nào được XIN mà
  chưa đo được** (kể cả khi mọi ngôn ngữ còn lại đều đạt), hoặc mã vào không
  phải Python hợp lệ · `PASS` chỉ khi **đo đủ mọi ngôn ngữ được xin và tất cả
  đều đạt**.

  > **PASS ĐÒI ĐO ĐỦ, KHÔNG CHỈ ĐÒI KHÔNG AI HỎNG.** Bản đầu trả `PASS` khi
  > `hong` rỗng và có ≥1 cái đạt, và nó đẻ ra **hai phán quyết cho cùng một
  > lượt**:
  >
  > ```
  > chạy từ Git Bash      bash có trên PATH  -> bản dịch bị bác  -> FAIL
  > chạy từ máy chủ       bash KHÔNG trên PATH -> KHÔNG ĐO ĐƯỢC -> PASS
  > ```
  >
  > Cùng mã, cùng đề, khác nhau ở **PATH của tiến trình gọi**. Một ngôn ngữ
  > được xin mà chưa từng đo thì cả lượt chưa kết luận được; gộp nó vào `PASS`
  > là đúng bệnh *"chưa đo được đội lốt đã đo, không sao"*.

* **Tìm trình kiểm bằng đường dẫn tuyệt đối, đừng dựa vào PATH.** `shutil.which`
  trước, rồi tới danh sách chỗ quen. `bash.exe` **có thật** trong thư mục cài
  Git trên máy này — chỉ là PATH của tiến trình máy chủ không thấy. Cùng bài với
  `System.Speech` báo máy không có giọng tiếng Việt trong khi registry có hai.
* **Hiện vật phải ghi TRÌNH NÀO đã chấm** (`trinh_kiem`). Hai máy có thể ra hai
  phán quyết cho cùng một bản dịch; bằng chứng phải nói ra ai là người chấm.
* **Mỗi ngôn ngữ để lại một tệp thật trên đĩa** kèm SHA-256 tính từ đĩa, cộng
  `ket_qua.json` ghi phán quyết từng ngôn ngữ.
* **`yeu_cau` là MÃ NGUỒN Python.** Đây là lần đầu tham số ấy được đọc thật:
  `card_polyglot_transpiler` truyền cả đoạn mã vào `chu_de` từ đầu, và `delta`
  thì bỏ qua nó.
* **Thẻ đổi `cac_phong`** `delta · gamma · omega` → `epsilon · gamma · omega`.
  Bỏ `delta` vì bước ấy quét `core/*.py`, không liên quan tới đề.

**THẺ NÀY SẼ ĐỎ, VÀ ĐỎ LÀ ĐÚNG.** `bash` sinh mã hỏng thật
(`if [ n <= 1 ]`, `echo fibonacci(n - 1)`), nên phòng sẽ trả `FAIL` ngay ngày
đầu. Sếp quyết lấy **đủ ba ngôn ngữ kiểm được** thay vì chỉ xin `javascript`
cho xanh: cái đỏ ấy chỉ đúng chỗ cần sửa tiếp, thay vì giấu đi bằng cách không
hỏi.

**KHÔNG sửa bộ dịch trong lượt này.** Trộn hai việc thì không biết con số nào
của việc nào.

**Chạy thật cả chuỗi thẻ sau khi nối:**

```
trước  PASS 3/3 · 39s · 3 hiện vật   (delta·gamma·omega — 0 dòng mã dịch)
sau    FAIL 0/3 ·  0s · 3 hiện vật   (epsilon·gamma·omega — 2 bản dịch thật)
       epsilon FAIL: bash — line 9: `    echo fibonacci(n - 1) + fibonacci(n - 2)'
       javascript qua `node --check`
```

Thẻ nhanh hơn ~200 lần và **đỏ**. Cái đỏ ấy là bản dịch bash thật sự không
parse nổi; cái xanh cũ là một phép quét AST không liên quan gì tới đề.

**Còn nợ (07/09/2026 đã trả một nửa — xem §5e):** `bash` đã vá, chạy ra đúng
số 3/3 đề. `go` **vẫn nợ** (`func Fibonacci` khai rồi gọi `fibonacci`), và chỗ
ấy là **đọc thấy**, không phải **đo được** — máy này không có trình biên dịch Go.

### 5e. BỘ DỊCH `bash` — TRẢ NỢ, VÀ ĐO BẰNG HAI CÂU HỎI TÁCH RỜI (07/09/2026)

Đăng ký **TRƯỚC KHI SỬA MÃ**. Đây là món nợ mục 5d ghi lại và cố ý không trả
trong lượt ấy (*"KHÔNG sửa bộ dịch trong lượt này. Trộn hai việc thì không biết
con số nào của việc nào"*).

**Đo trước khi vá.** Ba đề chọn xong trước khi biết kết quả — `fib` là **đúng
đoạn mã** `card_polyglot_transpiler` đang gửi vào phòng `epsilon`:

```
            polyglot khai   CÚ PHÁP        HÀNH VI
bash fib        PASS        FAIL           FAIL (chạy lỗi)
bash tong_vong  PASS        FAIL           FAIL (chạy lỗi)
bash if_else    PASS        FAIL           FAIL (chạy lỗi)
javascript ×3   PASS        PASS  3/3      PASS  3/3
go ×3           PASS        KHÔNG ĐO ĐƯỢC  KHÔNG ĐO ĐƯỢC
```

`javascript` **đạt cả hành vi**, không chỉ cú pháp — nên cái hỏng nằm ở nhánh
`bash` của bộ dịch, không nằm ở bộ khung.

**HAI CÂU HỎI, KHÔNG ĐƯỢC GỘP:**

1. **CÚ PHÁP** — `bash -n` có parse nổi không?
2. **HÀNH VI** — chạy thật, stdout có **bằng đúng** stdout của bản Python không?

Cửa `epsilon` hôm nay chỉ hỏi câu 1. Một bản dịch parse được mà tính sai vẫn
xanh — đúng họ bệnh `x in y` đã ghi **7 lần**. Sửa xong mà chỉ khoe `bash -n`
xanh là tự thưởng.

**Ngưỡng — chép TAY vào cửa canh, đặt theo NGUYÊN TẮC chứ không theo kết quả
chạy được:**

* `DAC_TA_BASH_DE = fib · tong_vong · if_else`, mã nguồn gõ thẳng trong tệp
  test, không đọc từ đâu về.
* Bản dịch bash phải đạt **3/3 cú pháp** VÀ **3/3 hành vi**. Không có mức
  "gần đạt". Không tới thì ghi số thật ra và để cửa ĐỎ.
* **So `stdout` từng byte** với `stdout` của chính đoạn Python ấy, chạy trong
  cùng một lượt — không gõ cứng `"55"` vào test. Gõ cứng thì đề đổi mà kỳ vọng
  không đổi.
* Không có `bash` trên máy → `KHONG_DO_DUOC`, **skip có tên**, không phải xanh.

**CỬA `epsilon` GIỮ NGUYÊN Ở MỨC CÚ PHÁP — CỐ Ý.**

Đầu vào của `epsilon` là **mã do người ngoài gửi** (`yeu_cau`). Dịch nó sang
bash rồi **chạy** tức là chạy mã của người ngoài — đúng cái rủi ro đã ghi cho
`/api/polyglot/run` ở dưới (*"đường chạy mã tuỳ ý"*). Nâng `epsilon` từ *kiểm cú
pháp* lên *chạy thật* sẽ biến một phòng dịch thành một phòng thực thi mà không
ai đăng ký điều đó.

Nên phép đo hành vi nằm ở **bộ test**, nơi ba đề do chính mình gõ ra và cố định;
`epsilon` vẫn chỉ `bash -n` · `node --check`. Hai chỗ, hai mức, nói rõ mức nào ở
đâu.

**ĐO SAU KHI VÁ (07/09/2026, cùng ba đề, cùng máy):**

```
            CÚ PHÁP        HÀNH VI
bash        3/3  PASS      3/3  PASS      (trước: 0/3 · 0/3)
javascript  3/3  PASS      3/3  PASS      (ca đối chứng, không đổi)
```

Phòng `epsilon` chạy thật với đúng `tham_so_mac_dinh` của thẻ:
**PASS · 83–175 ms · bash và javascript đều qua trình thật.** Cửa đỏ tự chuyển
xanh, không phải sửa cửa.

Ba chỗ nhánh bash cũ sai, cả ba cùng một gốc: **bash không phải "biểu thức lồng
biểu thức"**. Cùng tên `n` phải viết ba kiểu tuỳ chỗ đứng — `tong=5` (trần),
`echo "$tong"` (có `$`), `(( tong + 1 ))` (lại trần). Bản cũ dùng CHUNG một hàm
sinh chuỗi cho cả ba, nên ra `if [ n <= 1 ]` (so chuỗi `"n"` với `"1"`) và
`echo fibonacci(n - 1)` (bash bác dấu `(`).

**VÀ CÙNG LƯỢT ẤY ĐO RA MỘT CHỖ TỆ HƠN CÁI VỪA VÁ.**

`ast.NodeVisitor` không có `visit_While` thì gọi `generic_visit` — tức **đi
thẳng vào thân vòng lặp, sinh thân ra, còn vòng lặp thì biến mất**:

```
def dem(n):            ->   dem() {
    while n > 0:                local n="$1"
        n -= 1                  n=$(( n - 1 ))
    return n                    echo "$n"
                            }
```

`bash -n` GẬT. `node --check` GẬT. Phòng báo **PASS**. Bản dịch chạy đúng một
lần thay vì `n` lần. `class` · `try` · `with` · list comprehension cùng bệnh;
riêng bash còn im hơn nữa — biểu thức không dịch được ra `x=""`, parse sạch,
trong khi bốn ngôn ngữ kia ra `/* complex_expr */` và bị trình kiểm BÁC ngay.

Đây đúng là chỗ **một cửa chỉ hỏi cú pháp không bao giờ nhìn thấy**. Nó không
lộ ra vì đọc mã kỹ hơn — nó lộ ra vì đi tìm một ca hỏng THẬT để giữ bài
*"phòng biết nói FAIL"*, sau khi cái hỏng cũ đã được vá mất.

**Vá:** mọi chỗ bộ dịch bỏ cuộc đều phải **tự khai tên** (`bo_sot`), câu lệnh
lẫn biểu thức. `chuyen_doi_ngon_ngu` trả thêm trường ấy; `epsilon` thấy có bỏ
sót thì trả `KHONG_DO_DUOC` **trước khi** hỏi cú pháp. `status: "PASS"` của bộ
dịch từ nay chỉ có nghĩa *"bộ dịch chạy xong"*, không có nghĩa *"dịch đủ"*.

**Và một điểm tự thưởng nữa, bắt được do gọi phòng bằng sai khoá:** `yeu_cau=""`
thì `ast.parse` đạt, bộ dịch sinh mỗi dòng tiêu đề, hai trình kiểm đều gật, và
phòng trả **PASS · 2 ngôn ngữ qua trình thật** cho một tệp không có lấy một câu
lệnh. Nay `cay.body` rỗng là `KHONG_CHAY_DUOC`. Cùng bệnh đã cấm ở chuỗi tuỳ
biến (*"Danh sách rỗng là KHONG_CHAY_DUOC"*), chỉ khác tầng: ở đó 0 bước, ở đây
0 câu lệnh.

**Ba bài cũ phải sửa, và vì sao KHÔNG được xoá chúng.**
`test_epsilon_bat_duoc_ban_dich_HONG`, `..._MOT_ban_dich_hong_thi_ca_phong_
KHONG_duoc_PASS`, `..._KHONG_lo_duong_dan_tuyet_doi_ra_ly_do` đều mượn **cái
hỏng thật của bash** làm ca FAIL. Vá xong thì cả ba đỏ — đúng, nhưng xoá đi là
mất luôn khả năng chứng minh phòng nói được FAIL. Nay chúng bơm rác vào **đúng
một ngôn ngữ** (`_gia_bash_ra_rac`), ngôn ngữ còn lại chạy thật. Điều được canh
trở về đúng chỗ của nó: *phán quyết đi theo TRÌNH THẬT, không theo `status` bộ
dịch tự khai.* Một bài mượn cái hỏng thật là bài phụ thuộc vào việc nó **ở lại
hỏng**.

**`go` ĐÃ TRẢ NỢ 08/09/2026** — xem mục *"Bộ dịch `go`"* ở trên.

Câu ở đây trước 08/09 là: *"`go` KHÔNG ĐỘNG TỚI TRONG LƯỢT NÀY. Máy này không có
trình biên dịch Go, nên mọi câu nói về bản dịch Go chỉ là đọc thấy."* Giữ lại
nguyên văn vì nó đúng **vào lúc ấy**, và vì nó ghi đúng hai lỗi đọc-thấy-được:
`func Fibonacci` khai rồi gọi `fibonacci`, và câu lệnh mức module nằm ngoài
`func main`.

Cài Go 1.27.1 xong thì đo được, và đo ra **hai lỗi NỮA mà đọc không thấy**: `:=`
ở cấp gói, và số học trên `any`. Nền thật là **cú pháp 0/3 · hành vi 0/3**; sau
khi vá là **3/3 · 3/3**, chấm bằng `go build` + `go run` rồi so đầu ra với bản
Python chạy thật.

Đó là bài học riêng của lượt này: *"đọc thấy"* bắt được 2 trong 4 lỗi. Nửa còn
lại chỉ lộ ra khi có trình thật, và lỗi đầu tiên **che ba lỗi kia** — parser
dừng ở dòng 15 nên ba cái sau chưa từng được nhìn thấy.

## CHƯƠNG III: CƠ CHẾ BẢO MẬT & BỘ LỌC DỮ LIỆU NHẠY CẢM (REDACTION)
- Mọi file log lỗi (`raw/error.txt`) phải đi qua bộ lọc tập trung (Centralized Redactor).
- Tự động che giấu mọi dạng key/token: Bearer tokens, OpenAI/Gemini/Anthropic/OpenRouter API keys, Basic Auth credentials trong URL.
- Test bộ lọc bằng token giả; tuyệt đối không đưa key thật vào test fixture hoặc log commit.

### Chuỗi phòng TÙY BIẾN (`/api/pipeline/custom`, 04/09/2026)

Người gọi tự đặt danh sách bước, nên ba thứ chuỗi cố định không cần mà chuỗi này
cần:

* **Trần 8 bước.** Một lượt `aura` tốn tới 273 giây; 20 bước là hơn một tiếng
  rưỡi chẹn một luồng. Quá trần thì chặn **trước khi chạy**, trả
  `KHONG_CHAY_DUOC` + HTTP 400.
* **Tên phòng bịa là `FAIL`**, không phải bỏ qua im lặng và tuyệt đối không phải
  `PASS`. Đây là chỗ duy nhất một cái tên do người ngoài đặt đi vào hệ thống.
* **Danh sách rỗng là `KHONG_CHAY_DUOC`**, không phải `PASS`. Chạy 0 bước rồi
  báo đạt là đúng bệnh mà cả chương này sinh ra để chống.

Bốn trạng thái mỗi bước và phép chấm cả chuỗi dùng CHUNG với `/api/pipeline/run`
(`chay_chuoi_phong`, `trang_thai_chuoi`) — hai bản riêng thì chúng trôi khỏi
nhau, và bản ít người nhìn hơn sẽ là bản mục.

### HỘP CÁT cho `/api/polyglot/run` — TRẢ NỢ "CHƯA CHẶN ĐƯỢC" (08/09/2026)

Đăng ký **TRƯỚC KHI VIẾT MÃ**. Đây là **lời hứa an toàn**, nên luật mục 7 số 3
áp dụng nguyên văn: *kiểm được thì kiểm; kiểm không được thì viết "CHƯA chặn
được", đừng viết "đã chặn".*

**ĐO NỀN — 8 đơn chạy qua chính `chay_ma_da_ngon_ngu`:**

```
1. cwd                    D:\AURA_v3        <- gốc kho, không phải thư mục tạm
2. GHI tệp ngoài          ĐƯỢC
3. đọc `.env` của kho     đường đọc MỞ (kho hiện không có .env)
4. liệt kê HOME           87 mục
5. biến môi trường        87 biến, có tên nghi là bí mật (`CLAUDE_*`)
6. RA MẠNG                ĐƯỢC — mã 200
7. cấp phát 300 MB        ĐƯỢC
8. TIẾN TRÌNH MỒ CÔI      SỐNG SÓT qua timeout
```

**Mục 8 chưa ai ghi, và nó là chỗ nặng nhất:** `subprocess.run(timeout=)` chỉ
giết **con trực tiếp**. Một dòng `Popen` là cháu sống tiếp — tức **bảo vệ duy
nhất đang có bị vượt bằng một dòng**.

**THỬ TRƯỚC KHI VIẾT VÀO SẢN PHẨM** — bài 19/08 (`import resource` không tồn
tại trên Windows) bắt phải làm thế. Nguyên mẫu Job Object trên chính máy này:

```
KILL_ON_JOB_CLOSE     cha báo 'DA SINH chau' -> đóng job -> cháu KHÔNG sống sót
PROCESS_MEMORY        trần 128 MB, xin 300 MB -> mã thoát 1, CHẶN ĐƯỢC
```

*(Lượt thử đầu **vô nghĩa**: kịch bản cháu lỗi cú pháp vì đường dẫn Windows nằm
trong chuỗi lồng, nên cháu chưa từng sinh ra — mà kết quả đọc ra như "job giết
được cháu". Đúng bài phép đo không tới nơi. Tách cháu ra tệp riêng thì mới đo
thật.)*

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | sau khi vá | ghi chú |
|---|---|---|
| cwd | **thư mục tạm riêng**, không phải gốc kho | đo được |
| biến môi trường | **0 biến tên nghi bí mật**, tổng < 15 | đo được |
| cấp phát 300 MB | **BỊ CHẶN** (trần `RAM_MB = 256`) | đo được |
| tiến trình mồ côi | **KHÔNG sống sót** | đo được |
<!-- CHOT:hop-cat-con-lo -->
| **ghi tệp bằng đường dẫn tuyệt đối** | **VẪN ĐƯỢC** | **CHƯA CHẶN ĐƯỢC** |
| **đọc tệp bất kỳ / liệt kê HOME** | **VẪN ĐƯỢC** | **CHƯA CHẶN ĐƯỢC** |
| **ra mạng** | **VẪN ĐƯỢC** | **CHƯA CHẶN ĐƯỢC** |
<!-- /CHOT:hop-cat-con-lo -->

**`RAM_MB = 256` là con số CHỌN** — cùng con số kế hoạch 19/08 đã hứa mà không
giao được. Python rỗng tốn ~25 MB, nên 256 rộng rãi cho một đoạn mã ngắn.

**BA TRẠNG THÁI CHO CHÍNH HỘP CÁT, KHÔNG GỘP.** Kết quả trả về phải mang trường
`hop_cat` nói **thật sự đã áp được gì**: `"job"` (đủ) · `"khong"` (không tạo
được Job Object — chạy như cũ) · lý do. Không có trường ấy thì lời hứa "có hộp
cát" là một câu chữ không kiểm được — đúng thứ mục 7 cấm.

**ĐO SAU KHI VÁ — và một DƯƠNG TÍNH GIẢ suýt lọt:**

```
đơn                              nền             sau          phán quyết
1. cwd                           D:/AURA_v3      C:/../Temp   đổi mặc định
2. ghi tệp đường tuyệt đối       ĐƯỢC            VẪN ĐƯỢC     CHƯA CHẶN ĐƯỢC
3. đọc tệp bất kỳ trong kho      mở              25.583 byte  CHƯA CHẶN ĐƯỢC
4. liệt kê HOME (đường gõ cứng)  87 mục          87 mục       CHƯA CHẶN ĐƯỢC
5. biến môi trường               87, có bí mật   9, sạch      CHẶN ĐƯỢC
6. ra mạng                       ĐƯỢC            VẪN ĐƯỢC     CHƯA CHẶN ĐƯỢC
7. cấp phát 300 MB               ĐƯỢC            BỊ CHẶN      CHẶN ĐƯỢC
8. tiến trình mồ côi             SỐNG SÓT        KHÔNG        CHẶN ĐƯỢC
```

**MỤC 4 SUÝT BỊ CHẤM NHẦM LÀ ĐÃ CHẶN.** Lượt đo đầu sau khi vá cho nó `FAIL`,
đọc ra như *"hệ tệp đã kín"*. Thật ra `os.path.expanduser('~')` cần
`USERPROFILE` — biến vừa bị lọc — nên nó hỏng vì **thiếu biến**, không phải vì
bị chặn. Đường dẫn **gõ cứng** vẫn đọc được 87 mục, và `CLAUDE.md` vẫn đọc được
25.583 byte. **Một dương tính giả trong một lời hứa an toàn là thứ nguy hiểm
nhất ở đây** — nó biến "chưa chặn" thành "đã chặn" mà không ai nói dối.

**Chốt: 3 chặn được · 4 chưa chặn được · 1 chỉ đổi mặc định.** Ít hơn hẳn chữ
"sandbox".

**BỐN BÀI CANH KHẲNG ĐỊNH RẰNG VẪN CÒN LỖ.** `test_VAN_CHUA_chan_duoc_*` sẽ
**đỏ khi ai đó vá thêm** — và đó là lúc phải sửa tài liệu cùng lúc, chứ không
phải xoá bài. Không có chúng thì chữ "CHƯA chặn được" trôi dần thành "đã chặn"
mà không ai đo lại.

**NGẮT MẠNG — ĐÃ THỬ, VÀ VẪN CHƯA CHẶN ĐƯỢC (08/09/2026).**

Đo trước: máy này **không có Docker, không có WSL, và tài khoản KHÔNG phải
Administrator** — nên luật tường lửa (thứ duy nhất chặn mạng theo chương trình
trên Windows) **loại ngay từ đầu**.

Còn đúng một đường không cần quyền admin: **AppContainer** không cấp năng lực
`internetClient`. Thử theo đúng bài 19/08 — nguyên mẫu trước, sản phẩm sau:

```
1. CreateAppContainerProfile          OK, lấy được SID
2. icacls cấp RX cho temp + venv\Scripts   -> chạy python, mã thoát 106
3. cấp thêm base_prefix + prefix           -> mã thoát 1
4. cho cháu tự ghi traceback ra tệp        -> KHÔNG ghi nổi cả tệp lỗi
```

Bước 4 là chỗ kết luận: cháu hỏng **trước khi chạy dòng mã Python nào**, nên
không phải thiếu một thư mục nào nữa — trình thông dịch không khởi động nổi
trong AppContainer. Cấp thêm quyền là đoán, không phải đo.

**KẾT LUẬN: `no-network` VẪN CHƯA GIAO.** Muốn giao thì cần **một trong hai**:
quyền Administrator để đặt luật tường lửa theo chương trình, hoặc một môi
trường chạy dạng container. Cả hai đều là thay đổi lớn hơn hẳn phạm vi này.

**VÀ CỐ Ý KHÔNG GIAO MỘT BẢN NỬA VỜI.** Có thể chặn `socket` ở tầng Python
(gỡ `_socket` khỏi `sys.modules`, chặn `import`), và nó sẽ đổi dòng "ra mạng
ĐƯỢC" thành "bị chặn". Nhưng nó **vượt được bằng `ctypes` hoặc bằng một tiến
trình con**, mà người đọc tài liệu sẽ nhớ mỗi chữ "đã chặn". Một lời hứa an
toàn vượt được bằng một dòng thì **tệ hơn là không có** — nó làm người ta thôi
cẩn thận. Chỗ dựa thật vẫn là: `/api/polyglot/run` không đặt ra Internet.

**Dọn sạch sau khi thử — và LƯỢT DỌN ĐẦU KHÔNG TỚI NƠI.** ACL cấp cho
AppContainer SID đã gỡ khỏi thư mục Python và `venv`: đo lại bằng `icacls`,
**còn 0 mục**. Nhưng câu *"profile đã xoá (`HRESULT 0`)"* viết ban đầu là
**sai** — `HRESULT 0` là lời khai của API, không phải trạng thái của máy. Đo
thẳng vào máy thì:

```
TRƯỚC:  registry AppContainer\Mappings  CÒN 'aurapolyglotnonet'
        %LOCALAPPDATA%\Packages\...      CÒN thư mục (6 thư mục rỗng)
gọi lại DeleteAppContainerProfile      HRESULT 0x00000000
SAU:    registry hết  |  thư mục hết
```

Tức profile nằm lại trên máy **suốt từ lúc tài liệu này khẳng định nó đã bị
xoá**. Đúng ca [*"Trạng thái tự khai không phải trạng thái"*](SO_BENH_AN.md) —
lần này chính tôi là bên tự khai. Một nguyên mẫu để lại quyền trên máy là một
cái nợ không ai nhớ; một nguyên mẫu để lại quyền **kèm câu "đã dọn"** thì tệ
hơn, vì không ai đi kiểm nữa.

**Ba dòng CHƯA CHẶN ĐƯỢC ở trên phải ở lại tài liệu và ở lại `mo_ta`.** Chặn
được ba thứ không cho phép viết "đã cô lập". Chỗ dựa thật vẫn là
`/api/polyglot/run` không được đặt ra Internet.

Gieo 8 phép, cả 8 đỏ. Lượt đầu **1 cửa mù**: bài canh tài liệu hỏi
`cụm in spec` — mà cụm *"ra mạng"* còn nằm ở bảng đo nền, nên gieo xoá **hàng**
cảnh báo vẫn xanh. `x in y` lần thứ chín. Nay đòi cụm ấy nằm **cùng một dòng**
với `CHƯA CHẶN ĐƯỢC`.

<!-- CHOT:bo-can-tat-dinh -->
### Bộ căn chữ KHÔNG tất định — gốc của một bài mong manh (10/09/2026)

`test_ASS_va_MOC_TU_khop_nhau_tren_LUOT_THAT` đỏ một lượt trong bộ đủ 09/09,
lệch **0,050938s** so với trần 0,05 — quá **0,9 mili giây**. Dựng lại bằng mốc
gõ tay thì **không tái hiện được**, nên lúc ấy chỉ ghi lại là mong manh.

**Tách nguồn dao động 10/09:** sinh giọng **MỘT lần**, chạy bộ căn **8 lượt**
trên đúng tệp WAV ấy:

```
lượt 1,4,5,6,7   PASS  87/114 từ khớp   lệch lớn nhất 0,009062s
lượt 2           PASS  71/114 từ khớp   lệch lớn nhất 0,031375s
lượt 3, 8        KHONG_DAT — không ghi `.ass`
```

**Cùng một tệp âm thanh, cùng một lời, BA kết quả khác nhau.** Dao động nằm
trong **chính bộ nhận dạng**, không ở TTS và không ở phép ghi `.ass`.

**Vì sao:** `tools/can_tung_tu_worker.py` gọi
`m.transcribe(wav, language=..., word_timestamps=True)` mà **không ghim
`temperature`**. `faster-whisper` mặc định dùng **thang nhiệt độ dự phòng**
`[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]`: khi ngưỡng logprob hoặc tỉ lệ nén không đạt,
nó **lấy mẫu ngẫu nhiên** lại ở nhiệt độ cao hơn.

Đúng ca [*"cùng mã, cùng đề, hai phán quyết"*](SO_BENH_AN.md) — lần trước biến
thứ ba là `PATH`, lần này nó nằm **bên trong bộ đo**.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| `temperature` | **`0.0`** — một giá trị, KHÔNG phải thang dự phòng |
| `beam_size` | **`5`** — ghim rõ, không dựa vào mặc định của thư viện |
| `condition_on_previous_text` | **`False`** |
| chạy N lượt trên CÙNG một WAV | **kết quả giống hệt từng byte** |

`condition_on_previous_text=False`: bật thì mỗi đoạn phụ thuộc văn bản đoạn
trước, nên một chữ đổi ở đoạn 1 kéo lệch cả phần đuôi. Nó cũng là một đường
dẫn dao động vào kết quả.

**Ghi rõ cái KHÔNG đổi:** ghim nhiệt độ làm bộ căn **tất định**, không làm nó
**chính xác hơn**. Số từ khớp vẫn là 87/114 như cũ; thứ mất đi là những lượt
71/114 và `KHONG_DAT` ngẫu nhiên. Một bộ đo lúc nói thế này lúc nói thế khác
thì mọi con số nó sinh ra đều phải hỏi lại "lượt nào".
<!-- /CHOT:bo-can-tat-dinh -->

<!-- CHOT:can-cuong-buc -->
### Căn cưỡng bức (nợ "WhisperX") — ĐÓNG 10/09/2026, đo được mà KHÔNG ĐẠT

Kế hoạch: [`docs/KE_HOACH_CAN_CUONG_BUC_2026-09-09.md`](docs/KE_HOACH_CAN_CUONG_BUC_2026-09-09.md).
Sếp duyệt 09/09: *"dùng bản apache-2.0, đo thử xem có hơn không"*.

**KHÔNG cài gói `whisperx`.** Nó chặn `<3.14` (cả hai venv đều 3.14) và kéo
theo `pyannote-audio` — phân tách người nói, việc AURA không làm — cùng 21 gói
nữa. Thứ thật sự cần chỉ là `wav2vec2` + CTC: `torch` **124,1 MB bản CPU** +
`transformers` + `torchaudio`, trong venv riêng `F:\aura-align` (2,2 GB cả
model). **KHÔNG chen vào `F:\aura-stt`** đang chạy được và đang giữ bộ test
xanh.

Model: `dragonSwing/wav2vec2-base-vietnamese`, **apache-2.0**, 755,7 MB.
(Bản WhisperX chọn sẵn cho tiếng Việt là `cc-by-nc-4.0` — cấm dùng thương mại.)

**ĐO ĐƯỢC GÌ — cùng WAV, cùng lời, chỉ đổi bộ căn (ổn định qua 3 lượt):**

| | bộ hiện tại | căn cưỡng bức |
|---|---|---|
| từ có neo **đo được** | 87/114 = 76,3% | **114/114 = 100%** |
| thời gian | 68,6s | **13,6s** (nhanh 5×) |
| mốc không tăng dần / vượt biên | — | **0 / 0** |

**Nhưng phủ 100% mà đặt mốc SAI CHỖ thì không phải hơn.** Không có nhãn tay,
nên phải có **trọng tài độc lập với cả hai bộ**: ngưỡng "có tiếng" suy ra từ
chính tệp âm thanh (giữa log của phân vị 10 và 90), rồi chấm recall/precision.

| | recall | precision | **F1** |
|---|---|---|---|
| **bộ hiện tại** | 95,2% | 77,9% | **85,7%** |
| căn cưỡng bức — thô | 65,4% | 85,6% | 74,1% |
| căn cưỡng bức — kéo tới từ kế | 97,6% | 73,0% | 83,5% |

**KẾT LUẬN: KHÔNG ĐẠT ngưỡng đã đăng ký, nên KHÔNG GIAO.** Kế hoạch mục 5 chốt
trước: *"phải thấp hơn hẳn bản hiện tại"*. Nó không hơn — nó **kém 2,2 điểm F1**.

**Vì sao kém:** CTC phát ra **gai nhọn**, khoảng ký tự "hoạt động" hẹp hơn hẳn
độ dài âm học của từ. Đo được: bản thô khai **11,9 giây trong 30 giây là "giữa
các từ"** — với lời nói liên tục thì đó là sai. Kéo mỗi từ tới điểm khởi phát
của từ kế chữa được recall (65,4 → 97,6%) nhưng đánh đổi precision, và F1 vẫn
thấp hơn.

**HAI CHỖ SUÝT RA SỐ ĐẸP SAI:**

1. Bản CTC tôi **tự viết** bỏ blank giữa các nhãn cho gọn, và đo ra **5 mốc
   không tăng dần + 5 mốc vượt biên đoạn** trên 114 từ. Dùng
   `torchaudio.functional.forced_align` chuẩn thì cả hai về **0**. Một phép đo
   có lỗi thì không kết luận được gì.
2. Nếu dừng ở *"114/114 và nhanh 5×"* thì đã giao một thứ **tệ hơn**. Chỉ
   trọng tài độc lập mới thấy — và nó phải độc lập với **cả hai** bên, nếu
   không thì lại là bẫy tautological.

**CỠ MẪU: MỘT tệp 30 giây, 114 từ.** Đủ để nói *"chưa chứng minh được là hơn"*,
**không** đủ để nói *"chắc chắn kém"*. Ai muốn mở lại nợ này thì đo trên nhiều
mẫu hơn, và phải giữ nguyên trọng tài độc lập.
<!-- /CHOT:can-cuong-buc -->

<!-- CHOT:bo-dich-rust-cpp -->
### Bộ dịch `rust` và `cpp` — trả nợ 09/09/2026

Nợ mở từ 04/09 với một câu đúng: *"máy này không có `rustc`/`g++`, nên mọi câu
về bản dịch Rust/C++ chỉ là **đọc thấy**"*. Sếp duyệt cài 09/09.

**Cài gì, và vì sao chọn thế:**

| | tệp | cỡ | băm |
|---|---|---|---|
| C++ | `winlibs-x86_64-posix-seh-gcc-16.2.0-mingw-w64ucrt-14.0.0-r1.zip` | **274.029.684 byte** | SHA-256 `c1f52294…fcc4` **khớp** |
| Rust | `rustup-init.exe` → toolchain `x86_64-pc-windows-gnu` | ~9 MB + ~300 MB | SHA-256 `6f4bef66…db7e` **khớp** |

**KHÔNG dùng `w64devkit`** dù nó chỉ 61 MB: bản v2.9.1 chỉ còn phát hành
`.7z.exe` **tự bung** và **không công bố SHA-256**. Một tệp thực thi 61 MB
không đối chiếu được thì không tải — luật đã theo lúc cài Go. WinLibs công bố
`.sha256` kèm từng `.zip`, và `.zip` thì `zipfile` bung được.

**Rust dùng host `x86_64-pc-windows-gnu`, không phải `msvc`:** host msvc cần
Visual Studio Build Tools cho `link.exe`, tức thêm vài GB nữa. Toolchain gnu
mang trình liên kết riêng.

**Đặt trên `D:\sdk`, không phải `C:` như Go:** đo 09/09, C: còn **17,3 GB**
trong khi D: còn **62,7 GB**; hai bộ này bung ra ~2,5 GB.

**ĐO NỀN bằng trình thật, ba đề y hệt bộ `bash`/`node`/`go`:**

```
cpp   cú pháp 0/3 · hành vi 0/3
      main.cpp:14:6: error: 'cout' in namespace 'std' does not name a type
rust  cú pháp 0/3 · hành vi 0/3
```

**"ĐỌC THẤY" LẠI CHỈ BẮT ĐƯỢC MỘT PHẦN — y như Go 08/09:**

| | đọc thấy trước khi cài | chỉ lộ khi có trình thật |
|---|---|---|
| rust | `fn fibonacci(n)` thiếu kiểu · `let mut` ở cấp module | — |
| cpp | `std::cout` ở cấp tệp · `auto f(auto n)` đệ quy | — |
| **rust** | | **`return n` → `n` TRẦN: early-return biến mất** |

Lỗi cuối là **lỗi NGỮ NGHĨA, nặng hơn lỗi biên dịch**: trong Rust chỉ biểu
thức CUỐI hàm mới là giá trị trả về, nên `if n <= 1 { n }` thành một biểu thức
bị vứt đi và hàm **luôn** chạy xuống nhánh đệ quy. Đúng họ với `while` dịch
sang bash mà vòng lặp biến mất (06/09) — thứ `bash -n` gật đầu.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| cú pháp, 3 đề, mỗi ngôn ngữ | **3/3** |
| hành vi khớp bản Python chạy thật | **3/3** |
| `KIEM_DUOC` sau khi nối | `bash · cpp · go · javascript · python · rust` — **6** |
| `DICH_MAC_DINH` (bỏ nguồn `python`) | **5** ngôn ngữ |
| kiểu không suy được | **`bo_sot` khác rỗng** → phòng trả KHÔNG ĐO ĐƯỢC, không đưa cho trình biên dịch |

**Kiểu `any` của Rust CỐ Ý là một định danh KHÔNG tồn tại**
(`KIEU_KHONG_SUY_DUOC`). Go có `any` thật, C++ có `auto`, Rust không có gì
tương đương — mà đoán đại một kiểu thì bản dịch **biên dịch được và chạy sai**,
tệ hơn hẳn một lỗi biên dịch vì lỗi biên dịch thì ai cũng thấy.
<!-- /CHOT:bo-dich-rust-cpp -->

<!-- CHOT:bo-dich-go -->
### Bộ dịch `go` — trả nợ 08/09/2026

Nợ này mở từ 06/09 với đúng một câu: *"máy không có trình biên dịch Go"*. Sếp
duyệt cài thật 08/09, nên nó chuyển từ **KHÔNG ĐO ĐƯỢC** sang **đo được**.

**Cài gì:** `go1.27.1.windows-amd64.zip` · 78.931.360 byte · từ `dl.google.com`
· SHA-256 `a3911b5e…dd95d` **so khớp trước khi bung**. Bung vào
`~/go-sdk/go` — zip chứ không phải MSI, vì tài khoản này **không phải
Administrator**. `go version` chạy: `go1.27.1 windows/amd64`.

**ĐO NỀN bằng trình biên dịch THẬT, ba đề y hệt bộ `bash`/`node`:**

```
cú pháp (go build)  0/3      hành vi (go run)  0/3
main.go:15:1: syntax error: non-declaration statement outside function body
```

**Bốn lỗi, và lỗi đầu CHE ba lỗi kia** — parser dừng ở dòng 15 nên ba cái sau
chưa từng được trình biên dịch nhìn thấy:

| lỗi | vì sao chắc chắn hỏng |
|---|---|
| không có `func main()` | Go cấm câu lệnh ngoài thân hàm |
| tên khai báo ≠ tên gọi | khai `func Fibonacci`, gọi `fibonacci(…)` |
| `:=` ở cấp gói | `nums := []any{…}` ngoài hàm là lỗi cú pháp |
| số học trên `any` | `n <= 1`, `tong += x` — Go không có toán tử cho `any` |

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| cú pháp `go build`, 3 đề | **3/3** |
| hành vi `go run` khớp bản Python, 3 đề | **3/3** |
| kiểu suy được | `int` · `string` · `[]int` khi suy ra; **`any` + NÓI RA** khi không |
| không có `go` trên máy | **KHÔNG ĐO ĐƯỢC**, không phải PASS |

**Tìm `go` KHÔNG chỉ bằng PATH.** Sổ bệnh án có ca *"cùng mã, cùng đề, hai phán
quyết — biến thứ ba là PATH"*: cùng một bản dịch bị bác từ Git Bash và được
PASS từ máy chủ, chỉ vì `bash` có trên PATH ở nơi này mà không ở nơi kia.
`go.exe` nằm ở `~/go-sdk/go/bin` và **không** trên PATH, nên nó phải vào
`_CHO_TIM` — cùng khuôn `node` và `bash` đã dùng.

**PascalCase bị bỏ, có chủ ý.** Bản cũ khai `func Fibonacci` rồi gọi
`fibonacci(…)`. Trong `package main` không có gì cần xuất ra ngoài, mà Go cho
phép gạch dưới trong định danh — nên giữ nguyên tên Python là **xoá hẳn một
lớp lệch**, không phải tránh né nó. Đẹp theo lối Go mà không biên dịch được thì
không phải đẹp.
<!-- /CHOT:bo-dich-go -->

<!-- CHOT:tra-cuu -->
### Kho tra cứu cục bộ (08/09/2026)

Kế hoạch đầy đủ: [`docs/KE_HOACH_KHO_TRA_CUU_2026-09-08.md`](docs/KE_HOACH_KHO_TRA_CUU_2026-09-08.md).
Sếp duyệt 08/09: **tra cứu tường minh, chấp nhận ăn ô cuối của hàng rào.**

**Kho công nghệ chỉ sai đường và đó là phát hiện đầu.** Nó ghi Docling
`BENCHMARKED` 8,2s · MarkItDown `BENCHMARKED` 8,1s · MinerU `INSTALLED` là
"đường rẻ nhất, đã đo trên máy này". `find_spec` ở cả ba venv: **false, false,
false**. Và corpus **đã là Markdown sẵn**, nên hai bộ chuyển đổi ấy giải một
bài toán kho này không có. Thứ bắc được cầu từ vựng nằm sẵn trên máy 3 ngày mà
không ai gọi: **`bge-m3` 1,2 GB trong Ollama**.

**CHẤM BẰNG DẤU HIỆU, KHÔNG BẰNG TÊN TỆP.** Mỗi câu hỏi kèm một chuỗi phải có
mặt trong đoạn tìm được. Tên tệp là nhãn của tôi; chuỗi thì ai cũng kiểm lại
được.

**HAI BỘ CÂU HỎI, BỘ B VIẾT TRƯỚC KHI BIẾT THIẾT KẾ NÀO THẮNG:**

| | bộ A (dùng để CHỌN) | **bộ B (giữ riêng)** |
|---|---|---|
| RRF, bỏ `docs/lich_su/` — top-1 | **7/10** | **4/10** |
| RRF, bỏ `docs/lich_su/` — top-3 | 8/10 | **8/10** |

**top-1 tụt 7 → 4.** Đó là hình dạng của việc chỉnh theo 10 câu. `top-3 = 8/10`
là con số ổn định duy nhất, và nó QUYẾT ĐỊNH THIẾT KẾ: hiện **ba** đoạn, không
hiện một, và không gọi đoạn nào là "câu trả lời".

**CỔNG "KHÔNG TÌM THẤY": KHÔNG LÀM ĐƯỢC.** Khe giữa nhóm có đáp án
(8,55–22,60) và nhóm không có (7,59–8,54) là **0,01** trên thang rộng 15 điểm
— trùng hợp, không phải tách rời. Dựng cổng theo nó rồi chạy bộ B: **3/10 câu
đúng bị chặn nhầm** và **1/3 ca đối chứng vẫn lọt**. Bỏ cổng, hiện ba đoạn kèm
tên tệp, để Sếp tự chấm.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| top-3 trên bộ A | **≥ 8/10** |
| top-3 trên bộ B (giữ riêng) | **≥ 8/10** |
| top-1 | **KHÔNG đặt ngưỡng** — 8/10 và 4/10, không tin được |
| số đoạn hiện ra | **đúng 3**, mỗi đoạn kèm tên tệp + tiêu đề |
| nhúng một câu hỏi — GIỮA của 5 lượt trong MỘT vòng lặp | **< 300 ms** |
| gói Python ngoài | **vẫn đúng 2** |
| `V3` sau khi thêm `core/tra_cuu.py` | **20/20 — hết chỗ** |

**BA TRẠNG THÁI, KHÔNG GỘP THÀNH HAI:**

```
chưa dựng chỉ mục   -> NÓI RA, không được trả "không tìm thấy"
Ollama không gọi được -> NÓI RA, tụt về BM25 và BÁO là đã tụt
chạy đủ              -> RRF (BM25 + bge-m3)
```

Tụt về BM25 **im lặng** là thứ nguy hiểm nhất ở đây: kết quả vẫn ra, vẫn trông
như thường, chỉ kém đi — và không ai biết để đo lại.

**KHÔNG tự chèn vào mọi lượt chat.** top-1 đúng 4/10 trên bộ giữ riêng, nên tự
chèn đoạn hạng nhất là rót một đoạn sai vào 6/10 lượt. `CLAUDE.md` §4 đã đo
được rằng *"lời dặn không phải phép đo"* — nguồn nói sai thì model tin.

**Lượt tra kho KHÔNG gọi mạng.** `used_web` phải là `False` và `sources` rỗng:
trường ấy trả lời đúng câu *"lượt này AURA có gửi câu của tôi ra ngoài không?"*,
và câu trả lời ở đây là không.
<!-- /CHOT:tra-cuu -->

<!-- CHOT:path-noi-doi -->
### PATH nói có, chạy thì không (08/09/2026)

`opencode` nằm trên PATH, `command -v` **tìm thấy**, chạy thì báo thiếu tệp —
cả thư mục `node_modules/opencode-ai` đã biến mất, chỉ còn ba vỏ script npm
trỏ vào hư không. Đo cả thư mục npm toàn cục: **45 vỏ script / 15 lệnh, 1/15
trỏ vào hư không**.

Vì sao nó biến mất thì **KHÔNG ĐO ĐƯỢC**, và không được bịa: Defender có 0 mục
trong lịch sử phát hiện (bảo vệ thời gian thực đang bật); không có
`package.json` nào trong thư mục npm toàn cục nên không phải `npm i -g` prune
nhầm; npm chỉ giữ 11 log và cả 11 đều của sáng cùng ngày.

**Đây không phải chuyện của một công cụ ngoài lề.** Sổ bệnh án đã có ca [*"cùng
mã, cùng đề, hai phán quyết — biến thứ ba là PATH"*](SO_BENH_AN.md): cùng một
bản dịch bị bác từ Git Bash và được PASS từ máy chủ, chỉ vì `bash` có trên PATH
ở nơi này mà không có ở nơi kia. Một lệnh **có trên PATH mà chạy không nổi** là
đúng cái biến thứ ba ấy, ở dạng khó thấy hơn.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | ngưỡng |
|---|---|
| vỏ script npm trỏ vào hư không | **0** |
| số lệnh máy đo đọc được, ít hơn thì MÁY ĐO HỎNG chứ không phải sạch | **≥ 3** |
| lệnh bộ test dựa vào — tìm thấy trên PATH thì phải chạy được | `node` · `npx` · `ffmpeg` · `ffprobe` |

**CA ĐỐI CHỨNG LÀ BÀI CHỊU LỰC, không phải phép quét.** Phép quét chạy trên máy
thật nên hôm nay nó xanh, và một máy đo hỏng cũng cho ra đúng chữ "xanh" ấy —
regex hỏng thì đọc được 0 vỏ, và 0 vỏ hỏng đọc y hệt 0 vỏ chết. Nên cửa canh
phải có một thư mục tạm dựng sẵn **1 vỏ sống + 1 vỏ chết**, và máy đo phải báo
đúng **1**. Bài ấy kín, không phụ thuộc máy, và nó là thứ chứng minh phép quét
biết đỏ.

Ngưỡng "≥ 3 lệnh đọc được" là nửa còn lại của cùng một ý: thư mục có vỏ mà đọc
ra 0 lệnh thì phải **ĐỎ**, chứ không được đọc thành sạch. Thư mục không tồn tại
mới là KHÔNG ĐO ĐƯỢC.
<!-- /CHOT:path-noi-doi -->

<!-- CHOT:khe-dua -->
**KHE ĐUA `Popen` → job: ĐO TRƯỚC KHI VÁ (08/09/2026).**

Bản vá hôm qua tự ghi lại lỗ này rồi để đó, kèm một câu **sai**: *"muốn kín thì
phải bỏ `Popen` và gọi thẳng `CreateProcessW`"*. Không phải — `Popen` nhận
`creationflags`, và `CREATE_SUSPENDED` đi qua đó được. Thứ `Popen` không đưa ra
là **handle luồng**; mà luồng thì tìm lại được bằng `Toolhelp32`.

Đo bề rộng khe, **52 lượt**:

| | nhỏ nhất | giữa | lớn nhất | cháu sống sót |
|---|---|---|---|---|
| máy rảnh, 12 lượt | 0,077 ms | 0,103 ms | 0,232 ms | **0/12** |
| 8 tiến trình quay vòng trên 4 nhân, 40 lượt | 0,037 ms | 0,052 ms | **0,095 ms** | — |

Khe **không nở ra dưới tải** — nó hẹp lại. Cách đọc đầu tiên của tôi là *"luồng
cha đang giữ suất chạy của mình"*, và đó là một **lời giải thích đoán ra**. Đo
tiếp thì lộ biến thứ ba, và nó không phải tải:

| con Python **không treo** mất bao lâu mới ghi được mốc | nhỏ nhất | giữa | lớn nhất |
|---|---|---|---|
| máy rảnh, 30 lượt — **chạy trước, cache lạnh** | 290,3 ms | 465,2 ms | **837,9 ms** |
| 8 tiến trình quay vòng, 30 lượt — chạy sau, cache nóng | 5,9 ms | 25,9 ms | 299,9 ms |

Máy "bận" sinh tiến trình **nhanh hơn máy rảnh 28 lần**. Biến thứ ba là **cache
nóng** — lượt sau dùng lại DLL của Python đã nằm sẵn trong bộ nhớ, và ở lượt
rảnh thì CPU còn đang chạy xung thấp. Cùng bài *"cùng mã, cùng đề, hai phán
quyết"*: cái khác nhau không nằm trong hai thứ mình đang so.

Riêng `CreateProcess` của Python tốn 17–24 ms, nên tiến trình con là Python
**không thể** thắng cuộc đua này. Kết luận ấy không đổi; chỉ lý do đưa ra cho
việc khe hẹp lại là sai.

**Vẫn vá, và vá theo kiểu XOÁ HẲN KHE chứ không thu hẹp.** Một lời hứa "giết cả
cây tiến trình" không được phép dựa vào chuyện đối phương chậm hơn mình 200 lần
— con số ấy đúng hôm nay, trên máy này, với tiến trình con là Python. Đổi một
trong ba thứ đó thì lời hứa đổi theo mà không ai đo lại.

**ĐẶC TẢ — chép TAY vào cửa canh:**

| đơn | sau khi vá |
|---|---|
| tiến trình sinh ra ở trạng thái | **TREO** (`CREATE_SUSPENDED = 0x4`) |
| số lệnh con đã chạy lúc gắn vào job | **0** |
| `CHO_TREO_MS` — đợi bao lâu để chứng minh nó đang treo | **3000** ms |
| không thả được luồng | **giết con** + `hop_cat` nói ra — fail-closed |

**Không đo được "khe hở = 0 ms" bằng đồng hồ.** Đó chính là thứ phải chứng minh
bằng cách khác — cửa canh đo bằng **hành vi**, không đo bằng thời gian:

```
gắn xong, KHÔNG thả, đợi CHO_TREO_MS  ->  con phải CHƯA ghi gì
đối chứng: y hệt, bỏ CREATE_SUSPENDED ->  con PHẢI ghi trong CHO_TREO_MS
```

Ca đối chứng là chỗ bài này khác bài hôm qua: thiếu nó thì một tiến trình con
hỏng ngay từ đầu cũng "chưa ghi gì", và cửa vẫn xanh.

**`CHO_TREO_MS = 3000` là số SUY RA, không phải số gõ.** Bản đầu tôi gõ `500`
— và ca đối chứng đỏ ngay lượt chạy đầu, vì con Python cần tới 837,9 ms. Ngưỡng
lấy từ **lớn nhất đo được × 3,6**, và hai vế dùng CHUNG một hằng số vì chúng
ràng buộc lẫn nhau: khoảng đợi phải đủ dài để một con khoẻ đã kịp ghi, nếu
không thì "chưa ghi gì" chẳng chứng minh được là đang treo.
<!-- /CHOT:khe-dua -->

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
