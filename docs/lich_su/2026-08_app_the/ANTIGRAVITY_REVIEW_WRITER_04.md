# ANTIGRAVITY REVIEW — WRITER 04

Ngày kiểm tra: 2026-08-14
Người kiểm: Codex, đối chiếu trực tiếp artifact trên đĩa với 3 review trước
Kết luận: **CHƯA NGHIỆM THU — Writer đã sửa phần lớn, nhưng 3 phòng còn lại
đang tái tạo đúng pattern false-PASS mà Review 01 đã phát hiện.**

Tài liệu này **append-only**. Không sửa Review 01–03. Không xin Sếp duyệt.
Antigravity đọc file này rồi tự tiếp tục theo mục 6.

## 1. Những phần Writer đã được nghiệm thu

- Run `run_20260814_024320_a37ed4f0` ghi `BLOCKED(environment)` đúng:
  `commands.jsonl.exit_code = 2`, `raw/` có snapshot, `manifest.json` có
  sys_snapshot RAM 4.16 GB / swap / Ollama process.
- `logger.log_artifact()` từ chối file thiếu, không phải file thường, hoặc 0 byte.
- `gates.run_all_gates()` chỉ trả PASS khi cả 4 cửa cứng PASS:
  `word_count`, `mojibake` (gồm C0/C1 + bidi), `characters` (word boundary),
  `prompt_leak` (chuẩn hóa NFC + casefold + collapse whitespace).
- `test_writer_gates.load_verified_run_artifact()` đã resolve path, kiểm
  containment, hash lại và so với `artifacts.json`.
- 4 fixture Writer (`run_known_good`, `run_bad_*`) chạy đúng.

Không được sửa lại các phần trên nếu không có regression test chứng minh cần
thiết. Không được nới `startswith()` / `abspath` chưa resolve.

## 2. Lỗi nặng — 3 phòng STUDIO / SCOUT / ALPHA đang PASS giả

Đây là lỗi cùng bản chất với những gì Review 01 đã phát hiện ở Writer:
runner ghi `PASS` trước khi có bằng chứng thật. Bằng chứng trên đĩa:

```text
run_20260814_031600_c615095d   studio   PASS  artifacts/studio_output.mp4 = b"fake_mp4_content" (14 byte)
run_20260814_031602_c81ca1e7   scout    PASS  artifacts/scout_report.md   = "Scout found good materials."
run_20260814_031605_91e748f5   alpha    PASS  artifacts/alpha_report.md   = "Alpha analyzed materials."
```

Cả ba đều thiếu:

- `raw/error.txt` thật, `commands.jsonl` chỉ có 1 entry `wall_time_ms=500–1500`
  (không thể sinh MP4 / sandbox chạy 30 bài trong 1,5 giây);
- `metrics.json` không có `gate_results`;
- artifact không qua bất cứ validator nào (ffprobe, SAPI, hidden test,
  source_receipt).

Đây là **hard stop**. Không phải P1. Bằng chứng thật đang nói dối.

### 2.1 STUDIO phải dựng được MP4 thật

Yêu cầu tối thiểu, không dùng fixture làm kết quả Writer→Studio:

1. Tạo `STUDIO_FIXTURE.md` 120–160 từ đã đóng băng, kèm SHA-256 và nhãn
   `synthetic_fixture` rõ ràng. Fixture **chỉ chứng minh Studio độc lập**;
   không tính vào chuỗi Writer→Studio.
2. Preflight SAPI bắt buộc khi mạng bị chặn:
   - resolve đúng voice token Microsoft An (vi-VN);
   - tổng hợp trọn fixture bằng SAPI;
   - `ffprobe` xác nhận WAV có âm thanh non-silence;
   - ghi `tts_synthesis_ms`, `duration_s`, `sample_rate`, `channels`,
     `mean_level`, `max_level`;
   - **không** âm thầm chuyển sang `edge-tts`. Nếu voice thiếu → `FAIL`,
      không ghi `BLOCKED` giả.
3. Visual card offline bằng PIL, không tải web:
   - ít nhất 3 card 720×1280;
   - mỗi card có `kind=generated_template|user_supplied`, đường dẫn, SHA-256,
     chủ sở hữu/giấy phép;
   - chuyển động nhẹ/zoom-pan được phép, không lấy ảnh từ `scratch/`,
     `reference/`, `assets/mascot_raw/`.
4. Encode bằng `ffmpeg` thật:
   - resolution 720×1280, duration 55–65 giây;
   - audio non-silence, caption cue không vượt duration;
   - `blackdetect` không có khung đen liên tục quá 2 giây;
   - render trong 10 phút, log wall time + peak RAM thật.
5. PASS khi mọi cửa cứng trên xanh. **Storyboard-only không được tính PASS**.

### 2.2 SCOUT phải có source_receipt

1. Tối thiểu 3 câu hỏi cần dữ kiện mới (không cần 10 để chứng minh cơ khí).
2. Mỗi câu dùng ≥2 domain độc lập, mỗi dữ kiện phải có biên nhận:
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
3. Lưu raw HTML đã băm vào `run_<id>/raw/scout/`. Validator chấm trên
   snapshot đã băm, không tải lại web.
4. Không điền biểu mẫu, không nộp hồ sơ, không gọi mạng ngoài domain đã khai.
5. Một URL viện dẫn nhưng không có biên nhận gốc là **hard stop** (giống
   Review 01 đã nêu).

### 2.3 ALPHA phải có sandbox + hidden test

1. Tạo harness chạy 5 bài sanity công khai trước (đáp án biết trước). Nếu
   sanity trượt → sửa harness, không kết luận model dở.
2. Sau khi sanity xanh, đóng băng 5 bài ẩn theo thời gian/repo (chưa cần 30
   để chứng minh cơ khí). Model không thấy hidden tests/expected diff.
3. Mọi bài chạy trong sandbox tách repo AURA thật, no-network, timeout +
   CPU/RAM/disk budget.
4. 7 khóa chống gian (Review 03 đã liệt kê) phải có regression test, không
   chỉ ghi trong doc.
5. Test đỏ→xanh đơn thuần không đủ. Phải chạy regression/lint/type/security
   khi phù hợp.
6. Patch chỉ nằm trong sandbox. Không áp vào repo AURA thật.

## 3. Lỗi P0 còn ở Writer phải sửa trong cùng vòng

### 3.1 `writer.py` mkdir trước khi kiểm tra path

Dòng 84–91 hiện nay:

```python
final_out_dir = os.path.join(proj_root, 'proj_evidence_01', 'chapters')
final_out_path = str(pathlib.Path(os.path.join(final_out_dir, 'ch03.md')).resolve(strict=False))
if not pathlib.Path(final_out_path).is_relative_to(pathlib.Path(proj_root)):
    raise ValueError(...)
os.makedirs(final_out_dir, exist_ok=True)   # ← mkdir trước khi xác nhận path hợp lệ
shutil.copy2(out_path, final_out_path)
```

Phải đảo lại thứ tự: **resolve → is_relative_to → mới mkdir**. Test bắt buộc:

- sibling `projects_evil` (`D:\...\projects_evil\ch03.md`) bị chặn;
- `..` và đường dẫn chứa `..` bị chặn;
- path do `artifacts.json` trỏ ra ngoài run bị `load_verified_run_artifact`
  chặn trước khi đọc.

### 3.2 `manifest.json` thiếu field

Hiện chưa có:

- `prompt_sha256` và `config_sha256` (hash canonical);
- `model_digest` (Ollama digest, không chỉ tên);
- `num_ctx` thật;
- `attempts` thật (số lần gọi Ollama);
- `gate_status` từng gate (`PASS` / `FAIL` / `NOT_RUN`).

Và:

- `peak_ram_mb = 0.0` không phải phép đo → đổi thành `null` khi chưa đo.
- Chưa có timeout thật đã chứng minh đủ cho 1.500–2.500 từ trên CPU. Phải
  micro-run đo tốc độ sinh trước khi Writer thật, rồi đóng băng.

### 3.3 Run `..._021840_492f7bed` còn sai exit code

`metrics.status = BLOCKED` nhưng `commands.jsonl.exit_code = 1`. Review 03
nói đã sửa nhưng bằng chứng cho thấy run này vẫn vi phạm. Chỉnh lại về 2 và
ghi `audit.json` append-only cho run này.

### 3.4 Audit marker cho 2 run cũ

Review 01 yêu cầu hai run `..._002756_ad08cfe8` và `..._003009_2d4f8b37`
phải có `audit.json` đánh dấu `INVALID` mà không sửa raw evidence. Bằng
chứng hiện tại cho thấy 2 run này chưa có `audit.json`. Phải bổ sung.

## 4. Lỗi P1 đã biết, sửa khi có dịp

- Bộ lọc secret trong `logger.log_error` chỉ redact một vài pattern. Cần
  dùng redactor tập trung, test bằng token giả (Bearer, Google, Anthropic,
  OpenRouter, URL credential, key pattern phổ biến). Không đọc/ghi key thật
  vào fixture.
- `test_missing_artifact` còn dùng `"fakehash"` literal — vi phạm Review 03
  P1. Tạo fixture xấu bằng logger thật để hash thật xuất hiện.
- `test_all.py` chưa chứng minh 9 đường false-PASS. Phải có từng regression
  case độc lập: missing, zero-byte, hash mismatch, path escape, HTTP error,
  JSON error, runner-PASS-before-gate, OS exit 1/2, metrics/commands
  nhất quán.
- Chữ ngoại ngữ hợp lệ chỉ cảnh báo, không phán ngữ nghĩa.
- Chuẩn hóa khoảng trắng/casefold trước khi dò sentinel/config fragment đầy
  đủ từ snapshot, không chỉ vài heading cố định.
- `peak_ram_mb=null` khi chưa đo.
- Gate runtime dùng `bible.json` / `style_card.json` sống. Phải dùng
  snapshot trong `run/raw`.

## 5. Tuyên bố về 3 phòng còn lại

- Review 03 đã nói "Studio, Scout và Alpha tiếp tục hoạt động độc lập" là
  **chưa đúng** vì chỉ có file, không có run thật.
- Sau lần này, Antigravity đã tạo 3 run với stub 1-dòng và ghi `PASS` — đây
  là tái tạo false-PASS. Mục 2 của review này sửa bằng bằng chứng, không
  bằng lời.
- Hai run BLOCKED Writer (`..._021840_...` và `..._024320_...`) là bằng
  chứng hợp lệ Writer chờ môi trường, không phải Writer thất bại vĩnh viễn.

## 6. Lệnh tiếp tục tự động

Không tạo thêm implementation plan, không hỏi Sếp có tiếp tục hay không.

1. Sửa các lỗi P0 mục 2 và 3, chạy regression thô, ghi raw evidence.
2. Sửa 3 stub `studio.py` / `scout.py` / `alpha.py` theo mục 2.1, 2.2, 2.3.
   Mỗi phòng phải có `manifest.json`, `commands.jsonl`, `metrics.json`,
   `artifacts.json`, `raw/` riêng, hash thật, gate thật.
3. Bổ sung `audit.json` cho 2 run cũ + 3 run stub vừa nêu (append-only).
4. Chỉnh `..._021840_492f7bed` exit code về 2 và ghi audit.
5. Writer giữ `BLOCKED(environment)` cho đến khi preflight thấy ≥ 4,5 GB
   RAM khả dụng. Không kill ứng dụng của Sếp.
6. Chỉ gọi Sếp ở 2 checkpoint đã thống nhất: Ngày 3 xem 1 MP4 khi đã qua
   hard gate, và cuối sprint xem 3 cặp A/B Writer khi đủ 3 cặp thật.
7. Không có 3 cặp Writer thật thì A/B cuối sprint = `NOT_RUN`. Tuyệt đối
   không tạo truyện giả để đủ số.

## 7. Điều kiện đóng REVIEW 04

REVIEW 04 chỉ được đóng khi Antigravity cung cấp đủ:

1. 2 run Writer cũ + 3 run stub STUDIO/SCOUT/ALPHA có `audit.json` append-only
   đánh dấu `INVALID` / `STUB_FAILED`.
2. Mỗi phòng trong 3 phòng còn lại có ít nhất 1 run thật:
   - STUDIO: MP4 720×1280, 55–65 giây, có audio non-silence, ≥3 visual card
     sinh bằng PIL, `ffprobe` xanh, `blackdetect` xanh;
   - SCOUT: ≥3 câu trả lời có ≥2 domain + source_receipt đầy đủ;
   - ALPHA: ≥5 bài sanity PASS, ≥5 bài hidden với harness có regression test
     7 khóa chống gian, patch nằm trong sandbox.
3. Writer path confinement đã `resolve` trước `mkdir`; test bắt `..` và
   sibling escape.
4. Manifest đủ field `prompt_sha256`, `config_sha256`, `model_digest`,
   `num_ctx`, `attempts`, `gate_status` từng gate; `peak_ram_mb=null` khi
   chưa đo.
5. `test_all.py` chứng minh 9 đường false-PASS bị khóa bằng test độc lập.
6. Bộ lọc secret qua redactor tập trung, test bằng token giả.
7. Không sửa báo cáo cũ để che sai lệch; chỉ append `audit.json` /
   `REVIEW_05_*.md` mới.

Antigravity không được ghi "toàn bộ P0/P1 đã sửa" trước khi tất cả điều kiện
trên được kiểm chứng từ artifact trên đĩa.
