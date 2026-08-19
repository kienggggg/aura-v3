# ANTIGRAVITY — AURA FOUR-ROOM EVIDENCE SPRINT

Trạng thái: **được phép thực thi**  
Nguồn quyết định: `thaoluan.md`, lượt 007–011  
Kho đích: `D:\AURA_v3`  
Kho `D:\AURA_OS_v2`: chỉ đọc để tham khảo; không nối runtime v2 vào v3  
Thời lượng: **10 ngày làm việc**, sau đó mới xét Phase B và Model Lab

## 1. Mục tiêu thật

Chứng minh bằng sản phẩm và phép đo rằng bốn phòng sau có đáng được tích hợp
vào AURA v3 hay không:

1. **WRITER** — viết một chương truyện từ bible và một style card duy nhất.
2. **STUDIO** — biến chương đó thành video dọc 55–65 giây, có giọng Việt và
   phụ đề; baseline phải chạy được khi mất mạng.
3. **SCOUT** — trả lời câu hỏi cần dữ kiện mới với biên nhận nguồn kiểm chứng
   được.
4. **ALPHA** — sửa lỗi Python trong bản sao sandbox, có test ẩn và khóa chống
   gian.

Đây là **Evidence Sprint**, chưa phải hệ điều hành bốn phòng hoàn chỉnh. Không
xây dispatcher, bộ nhớ tách phòng, capability registry, khay duyệt hay publisher
trong sprint này. Chỉ những phòng PASS mới được xét cho Phase B.

## 2. Chế độ vận hành tự động

Antigravity tự đọc, sửa, chạy test, sửa lỗi và ghi bằng chứng trong workspace;
không hỏi Sếp duyệt từng thao tác thường lệ. Chỉ dừng để Sếp làm đúng hai việc:

- **Cổng Ngày 3:** xem một video và trả lời `dùng được` hoặc `không`.
- **Cuối sprint:** đọc ba cặp truyện A/B đã xáo nhãn và trả lời cho từng cặp:
  `muốn đọc tiếp không?` và `A hay B hơn?`.

Mọi việc khác phải tự tiếp tục hoặc tự dừng theo điều kiện trong tài liệu này.

Các giới hạn không được vượt:

- Không đọc hoặc in `.env`, token, cookie hay dữ liệu đăng nhập.
- Không gửi dữ liệu riêng ra ngoài ngoài nội dung Scout đã được xác định là cần
  web; log phải che dữ liệu nhạy cảm.
- Không `external_submit`: không đăng bài, nộp đơn, mua hàng, gửi biểu mẫu hay
  công khai nội dung.
- Không áp patch Alpha vào repo AURA thật.
- Không tự đổi tiêu chí nghiệm thu sau khi thấy kết quả.
- Không báo PASS bằng mô tả. PASS phải trỏ tới lệnh chạy, exit code, thời gian,
  artifact và SHA-256.

## 3. Bố trí công việc và bằng chứng

Tạo một gói thử nghiệm cô lập trong `D:\AURA_v3\experiments\evidence_sprint\`.
Không import runtime từ v2. Nếu tái dùng ý tưởng/hàm v2, port phần nhỏ cần thiết,
ghi nguồn trong code và viết test mới ở v3.

Tạo dữ liệu chạy ở thư mục local/ignored:

```text
data/evidence_sprint/
├─ runs/<run_id>/
│  ├─ manifest.json
│  ├─ commands.jsonl
│  ├─ metrics.json
│  ├─ artifacts.json
│  └─ raw/
├─ frozen/
└─ reports/
```

Mỗi lần chạy phải ghi:

- `run_id`, thời gian có múi giờ, git commit và config hash;
- model, seed, sampling, context, max output, số lần thử;
- lệnh/entrypoint, exit code, wall time, peak RAM nếu đo được;
- SHA-256 của đầu vào, đầu ra và fixture;
- trạng thái `PASS`, `FAIL`, `BLOCKED` hoặc `NOT_RUN` cùng lý do máy-chấm được.

Không đưa raw prompt/truyện riêng vào commit công khai. Báo cáo có thể dùng hash,
metric và fixture tổng hợp.

## 4. Lịch cố định

```text
Ngày 1–2  WRITER + hợp đồng chapter → shorts_script → shot_list
Ngày 3    STUDIO dựng MP4 offline tối thiểu; CỔNG SẾP XEM
Ngày 4–6  SCOUT + source_receipt
Ngày 7    ALPHA: harness + 5 bài sanity
Ngày 8    Đóng băng 30 bài ẩn + đo baseline
Ngày 9    Đo Alpha candidate
Ngày 10   Chạy lại phép đo, bảng PASS/FAIL, A/B Writer cho Sếp
Sau Ngày 10  Model Lab Dynamic 1-bit, tách khỏi đường sống còn
```

Cổng Ngày 3 chỉ quyết định có tiếp tục sợi Writer→Studio hay thu nó về một
phòng. Scout và Alpha vẫn được đo độc lập.

## 5. WRITER

### Việc thật

- Đầu vào: `bible.json`, số chương và đúng **một** `style_card`.
- Đầu ra: `writer/projects/<project_id>/chapters/ch03.md`, 1.500–2.500 từ.
- Không nạp nhiều style card trong cùng lượt.

Có thể tham khảo/port tối thiểu từ v2 `story_factory`: `_build_bible`,
`_write_chapter`, `_polish_chapter`, `_bible_context`, `_update_truth`. Không
được coi tên hàm là bằng chứng đã chạy.

### Cửa cứng

Tất cả phải PASS:

- số từ trong khoảng;
- nhân vật bắt buộc trong bible có mặt;
- UTF-8 hợp lệ, không `U+FFFD`, không control character trái phép;
- không có mẫu mojibake đã khóa bằng test;
- không rò nguyên văn prompt, sentinel hay luật nội bộ;
- chỉ ghi trong thư mục dự án được cấp.

Từ lóng hiện đại, ngoặc kép đáng ngờ, lặp từ, độ dài câu và chữ ngoại ngữ
ngoài danh sách tên chỉ là **cảnh báo**, không được tự động kết luận văn dở.

### Cửa chất lượng

Chuẩn bị ba đề cố định với ít nhất hai style card khác nhau. Với mỗi đề:

- sinh một bản baseline bằng đường Writer trước sprint;
- sinh một bản candidate;
- xáo nhãn A/B trước khi đưa Sếp;
- cùng model, seed, sampling, max tokens và tối đa hai lần sinh;
- lưu commit/config hash của baseline.

PASS khi 3/3 qua cửa cứng, ít nhất 2/3 được Sếp chọn `muốn đọc tiếp`, và
candidate thắng baseline ít nhất 2/3. Hòa là chưa chứng minh cải thiện.

Dừng Writer nếu 2/3 trượt cửa cứng sau một vòng sửa, hoặc Sếp không muốn đọc
tiếp ít nhất hai candidate.

## 6. STUDIO

### Hợp đồng bàn giao

```text
chapter.md
  → shorts_script.md (120–160 từ)
  → shot_list.json + caption_timing.json
  → voice.wav + visual assets + asset_manifest.json
  → video.mp4
```

Đầu ra: MP4 dọc **720×1280**, dài 55–65 giây. Không đăng.

### Preflight TTS offline bắt buộc

SAPI Microsoft An (vi-VN) hiện chỉ có bằng chứng tổng hợp một đoạn ngắn; nhãn
ban đầu là `offline candidate — synthesis measured`.

Antigravity phải chạy preflight khi mạng bị chặn:

- resolve đúng voice token Microsoft An;
- tổng hợp trọn script 120–160 từ;
- ffprobe được WAV và xác nhận có âm thanh không im lặng;
- ghi thời gian tổng hợp, duration, sample rate, channels, mean/max level;
- tuyệt đối không âm thầm chuyển sang `edge-tts`.

Nếu voice thiếu hoặc preflight thất bại, Studio-offline FAIL. `edge-tts` chỉ là
fallback **connected** được báo rõ, không dùng để cứu điểm offline.

Nếu audio lệch 55–65 giây, chỉ cho một lần chỉnh tốc độ đọc hoặc độ dài script
trong biên 120–160 từ. Cấm kéo giãn audio hoặc lặp cảnh để lách cửa.

### Hình ảnh offline tối thiểu

Kho hiện không có bộ sinh ảnh minh họa offline: `story_video` gọi Pollinations
rồi Gemini; `video_shorts` tải Pixabay. Vì vậy baseline được khóa:

1. Dùng ảnh dự án chỉ khi Sếp cung cấp và xác nhận quyền sử dụng; hoặc
2. PIL sinh ít nhất ba visual card 720×1280 gồm nền gradient/màu, chữ, hình học
   và chuyển động nhẹ/zoom-pan.

Không tải ảnh web. Không lấy ảnh từ `scratch/`, `reference/` hoặc
`assets/mascot_raw/`. Mỗi asset phải có `kind=generated_template|user_supplied`,
đường dẫn, SHA-256, chủ sở hữu/giấy phép.

Visual card chỉ chứng minh **video offline tối thiểu**, không được gọi là ảnh
minh họa ngữ nghĩa do AI sinh.

### Cửa cứng và cửa chất lượng

Cửa cứng:

- giải mã end-to-end thành công;
- duration 55–65 giây;
- 720×1280;
- có audio, non-silence;
- caption cue không vượt duration audio/video;
- `blackdetect` không có khung đen liên tục quá 2 giây;
- ít nhất ba visual card;
- render hoàn tất trong 10 phút.

Cửa chất lượng: Sếp xem đúng một lần ở Ngày 3. PASS khi mọi cửa cứng xanh và
Sếp nói `dùng được`. Storyboard-only không được tính PASS.

Dừng sợi Writer→Studio nếu sau hai lần dựng vẫn quá 10 phút, không decode hoặc
Sếp nói `không dùng được`.

## 7. SCOUT

### Việc thật

Trả lời mười câu cần dữ kiện mới. Mỗi câu trả lời phải dùng ít nhất **hai domain
độc lập** và mỗi câu dữ kiện phải trỏ tới ít nhất một biên nhận.

`source_receipt` được tạo ngay lúc lấy dữ liệu:

```json
{
  "canonical_url": "https://...",
  "fetched_at": "timestamp-with-timezone",
  "status": 200,
  "content_sha256": "...",
  "normalized_support_span": "...",
  "claim_ids": ["claim-..."]
}
```

Validator chấm trên snapshot đã băm, không tải lại trang để quyết định PASS.
Mất mạng/403 về sau là `unverified`, không phải bằng chứng bịa.

PASS khi 10/10 câu có integrity biên nhận đầy đủ và ít nhất 9/10 hữu ích khi
Sếp/kiểm toán soi mẫu. Một URL hoặc đoạn trích được viện dẫn nhưng không có
biên nhận gốc là bịa nguồn và hard stop Scout.

Scout chỉ đọc web; không điền biểu mẫu, không nộp hồ sơ và không thực hiện hành
động bên ngoài. Khi mất mạng chỉ được dùng cache và phải hiện ngày lấy.

## 8. ALPHA

### Việc thật

Tạo bài sửa lỗi Python từ lịch sử commit đã chọn, nhưng mọi bài chạy trong bản
sao sandbox. Đầu ra chỉ là patch + báo cáo; không áp vào repo AURA thật.

Ngày 7 phải dựng harness và chạy năm bài sanity công khai, có đáp án biết trước.
Nếu sanity trượt thì sửa harness; chưa được kết luận model dở.

Sau khi sanity xanh:

- đóng băng 30 bài ẩn theo thời gian/repo;
- model không thấy hidden tests hoặc expected diff;
- đo baseline trước, candidate sau;
- hai bên dùng cùng đề, prompt/context, timeout, token/attempt budget.

### Bảy khóa chống gian

1. Hidden tests.
2. Test và fixture bất biến.
3. Diff chỉ trong allowlist.
4. No-network.
5. Sandbox tách repo thật.
6. Timeout và giới hạn CPU/RAM/đĩa.
7. Không chạm repo AURA thật.

Khi phù hợp, chạy regression, lint, type và security checks. Test đỏ→xanh đơn
thuần không đủ vì model có thể hard-code hoặc sửa test.

PASS khi candidate giải đúng nhiều hơn baseline ít nhất **5/30 bài** và không
vi phạm khóa nào. Nếu harness hợp lệ mà baseline 0/30 thì dừng nhánh thay vì
tuyên bố một cải thiện từ nền bằng không. Một lần sửa test/fixture, vượt sandbox,
gọi mạng hoặc chạm ngoài allowlist là hard stop.

## 9. Báo cáo Ngày 10 và nghiệm thu độc lập

Báo cáo cuối phải có:

- bảng PASS/FAIL/BLOCKED cho từng phòng;
- liên kết local tới raw evidence, command, exit code và hash;
- số lần thử và mọi lần thất bại, không chỉ lần đẹp nhất;
- latency, peak RAM và thời gian sửa tay;
- điểm cửa cứng tách khỏi đánh giá chất lượng;
- danh sách điều không được chứng minh;
- quyết định phòng nào được sang Phase B.

Không tự phong `chuyên gia`. Một phòng chỉ đủ điều kiện Phase B khi đạt đúng
cổng hẹp trong tài liệu này.

Sau khi Antigravity hoàn tất, Codex và Claude nghiệm thu bằng cách chạy lại mã:

- chọn mẫu ngẫu nhiên và tái chạy từ đầu;
- đối chiếu SHA-256 với nguồn;
- xác nhận không sửa tiêu chí sau kết quả;
- kiểm `git status` sạch và không có file riêng/bí mật bị stage;
- không chỉ đọc báo cáo do Antigravity viết.

## 10. Phase B — chỉ sau Ngày 10

Chỉ tích hợp những phòng PASS. Phase B mới xây dispatcher deterministic, memory
isolation, capability handoff và approval/receipt; không nằm trong sprint.

Phase B vẫn không `external_submit`. Nó chỉ tạo artifact, mục chờ xử lý và
receipt. Wattpad/Payhip bàn giao thủ công. Rookies/YouTube chỉ được thử adapter
thật sau một ủy quyền riêng trong tương lai.

## 11. Model Lab Dynamic 1-bit — sau Ngày 10

Ứng viên duy nhất:

```text
Model: Qwen3-30B-A3B-Instruct-2507
GGUF:  Qwen3-30B-A3B-Instruct-2507-UD-IQ1_S.gguf
Repo:  unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF
Size:  9.05 GB decimal (~8.43 GiB)
Arch:  30.5B total, ~3.3B active/token; 128 experts, choose 8
License: Apache-2.0
```

Dynamic 1-bit là mixed precision, không phải mọi weight đúng một bit. Đây là
thử nghiệm `bộ não lớn nằm trong tủ`, không thay qwen3.5:4b làm model thường
trực.

Không tải trước khi báo cáo Ngày 10 hoàn tất. Trước khi tải, xác minh revision,
tên tệp, SHA nếu nguồn cung cấp, ít nhất 20 GB đĩa trống và runtime llama.cpp có
hỗ trợ Qwen3-MoE/IQ1.

Preflight:

- dừng các model khác;
- CPU-only, bốn luồng, context 2.048, mmap bật, KV Q8/Q4;
- đầu ra 32–64 token;
- ghi RAM/pagefile trước, trong và sau;
- dừng nếu 15 phút chưa có token đầu, máy gần treo/pagefile tăng mất kiểm soát,
  hoặc tốc độ warm <0,05 tok/s.

Benchmark gồm 12 microtask cố định ở bốn nhóm viết, code, dữ kiện và tuân thủ
cấu trúc; max output **300 token**, cùng prompt/config với qwen3.5:4b. Tổng
wall time mỗi bài, kể cả load/prefill/generation, phải ≤600 giây.

Chỉ giữ model như deep fallback nếu thắng qwen3.5:4b ít nhất 8/12 cặp mù và
không có lỗi/lặp vô nghĩa quá 25%. Mốc 0,05 tok/s chỉ chứng minh model sống;
không chứng minh nó dùng được.

## 12. Điều kiện hoàn tất toàn bộ nhiệm vụ

Nhiệm vụ Antigravity hoàn tất khi:

- Evidence Sprint có báo cáo Ngày 10 cùng raw evidence tái lập được;
- hai checkpoint duy nhất của Sếp đã được ghi nhận;
- mọi phòng có quyết định PASS/FAIL/BLOCKED đúng tiêu chí đóng băng;
- repo đích sạch sau khi các thay đổi cần giữ đã được commit có chủ đích;
- không có external action, secret leak hoặc dữ liệu riêng bị đưa vào commit;
- Model Lab được chạy sau Ngày 10 hoặc được ghi `BLOCKED/NOT_RUN` với bằng chứng
  chính xác theo điều kiện dừng, tuyệt đối không giả PASS.

