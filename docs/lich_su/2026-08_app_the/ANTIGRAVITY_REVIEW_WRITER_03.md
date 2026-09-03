# ANTIGRAVITY REVIEW — WRITER 03

Ngày kiểm tra: 2026-08-14  
Đối tượng: bản sửa sau `ANTIGRAVITY_REVIEW_WRITER_02.md`  
Kết luận: **PARTIAL — các lỗi P0 chính đã được sửa một phần, nhưng REVIEW 02 chưa đóng.**

## 1. Những sửa đổi được nghiệm thu

- Runner chỉ ghi `PASS` sau khi gọi hard gate.
- Artifact Writer được snapshot trong thư mục riêng của từng run, nên run mới không còn trỏ thẳng vào cùng một `projects/.../ch03.md` làm bằng chứng.
- Logger từ chối file thiếu, không phải file thường và file 0 byte.
- Mã thoát trong `writer.py` đã tách đúng: `0=PASS`, `1=FAIL`, `2=BLOCKED`.
- `max_retries=0` khớp với mã không retry.
- Run `run_20260814_024320_a37ed4f0` ghi `BLOCKED(environment)` và `commands.jsonl.exit_code=2`; input chính và source hiện có snapshot/hash.
- Fixture nội dung đã tách thành các trường hợp độ dài thấp/cao, mojibake, NUL, thiếu nhân vật và prompt leak.

Không được sửa lại các phần trên nếu không có regression test chứng minh cần thiết.

## 2. Các lỗi còn chặn đóng REVIEW 02

### P0 — Bộ test vẫn không kiểm tính toàn vẹn artifact

`tests/test_writer_gates.py` mở thẳng `artifacts.json[...].path` nhưng không:

- giới hạn path trong `runs/<run_id>/artifacts`;
- tính lại SHA-256 và so với `artifacts.json`;
- dùng snapshot `bible.json`/`style_card.json` của chính run;
- xác minh manifest, commands và mã thoát thật.

Vì vậy sửa nội dung sau khi hash, đổi path sang file khác, hoặc ghi SHA giả vẫn có thể lọt qua test.

**Phải sửa:** tạo một hàm `load_verified_run_artifact()` fail-closed: resolve path thật, kiểm containment, file thường/non-empty, tính lại hash, so manifest, rồi mới trả content. Gate phải đọc input snapshot đã hash trong `run/raw`, không đọc input sống ngoài run.

### P0 — Fixture generator vẫn có đường tự chế bằng chứng

`generate_fixtures_v2.py` bắt lỗi `logger.log_artifact()` rồi tự ghi `artifacts.json` ở nhánh exception. Đây chính là đường bypass logger mà REVIEW 02 cấm.

**Phải sửa:** xóa hoàn toàn nhánh tạo artifact giả. Với negative case `missing/zero/outside/hash-mismatch`, test phải khẳng định logger hoặc verifier từ chối và **không** tồn tại artifact record hợp lệ. Không được tạo JSON giả để giúp test chạy tiếp.

### P0 — Path confinement chưa đạt

- `writer.py` vẫn `mkdir` trước khi kiểm tra và vẫn dùng `startswith()` cho output cuối.
- `logger.py` dùng `abspath()` + lexical `is_relative_to()`, chưa `Path.resolve()`; junction/symlink vẫn có thể trỏ ra ngoài. Fallback vẫn dùng `startswith()`.

**Phải sửa:** resolve root và target trước mọi mkdir/write; dùng `Path.resolve(strict=False)` + `is_relative_to(resolved_root)`. Với file đã có, resolve cả liên kết. Test bắt buộc: `..`, sibling `projects_evil`, path ngoài run và junction/symlink khi Windows cho phép. Không tạo target trước khi validation PASS.

### P0 — `test_all.py` chưa chứng minh các đường false-PASS đã khóa

Nó chỉ kiểm status của fixture và mong `test_writer_gates` thất bại ở fixture xấu. Nó chưa kiểm:

- missing artifact;
- zero-byte artifact;
- SHA mismatch;
- artifact path escape;
- HTTP/JSON/timeout error;
- runner không thể PASS trước gate;
- OS exit code 1/2 thật;
- metrics/commands/artifact nhất quán.

Thêm từng regression case độc lập. Một case xấu chỉ được gọi “độc lập” khi các gate không liên quan vẫn PASS. Hiện `run_bad_missing_char` đồng thời rò từ `NHÂN VẬT`, nên chưa phải case độc lập.

### P1 — Gate vẫn thiếu phần đã chốt

- Chỉ bắt NUL, chưa bắt C0/C1 và bidi controls không được phép.
- Leak detector mới chuẩn hóa NFC + lowercase; chưa chuẩn hóa khoảng trắng/casefold và chưa dò sentinel/config fragment đầy đủ từ snapshot.
- Gate runtime dùng `bible.json` và `style_card.json` sống, không dùng bản snapshot của run.

Chữ ngoại ngữ hợp lệ chỉ cảnh báo; không biến regex thành bộ phán ngữ nghĩa.

### P1 — Manifest/evidence còn thiếu hoặc khai sai

Run mới vẫn thiếu:

- prompt hash và canonical config hash;
- model digest và `num_ctx`;
- số attempt thật;
- snapshot Ollama process/model;
- nguồn port cụ thể;
- gate status `NOT_RUN` khi BLOCKED.

`peak_ram_mb=0.0` không phải phép đo; phải là `null`/`unmeasured` nếu chưa đo. Timeout 300 giây chưa có micro-run chứng minh đủ cho 1.500–2.500 từ; phải đo và đóng băng trước lần Writer thật.

### P1 — Bộ lọc secret chưa đủ

`log_error()` chỉ thay đúng `OPENAI_API_KEY`. Nó chưa lọc Authorization/Bearer, Google/Gemini, Anthropic, OpenRouter, URL credential và key pattern thông dụng. Dùng bộ redactor tập trung, test bằng token giả; không đọc hoặc ghi key thật vào fixture.

## 3. Tuyên bố về ba phòng còn lại không có bằng chứng

Kiểm tra cây hiện tại của `D:\AURA_v3\experiments\evidence_sprint` chỉ thấy:

- `writer.py`, `logger.py`, `gates.py`;
- input Writer;
- test và fixture Writer.

Không có implementation, manifest, commands, metrics hoặc artifact của STUDIO, SCOUT hay ALPHA. Vì vậy câu “Studio, Scout và Alpha vẫn tiếp tục hoạt động độc lập” trong `REVIEW_02_CORRECTION.md` **chưa đúng**.

## 4. Lệnh tiếp tục tự động

Không tạo thêm implementation plan và không hỏi Sếp có tiếp tục hay không.

1. Sửa các lỗi P0 ở mục 2 và chạy regression thô.
2. Ghi một correction append-only; không sửa báo cáo cũ để che lời tuyên bố sai.
3. Writer giữ `BLOCKED(environment)` đến khi preflight đủ 4,5–5 GiB; không cố đóng ứng dụng của Sếp.
4. Đồng thời tạo STUDIO fixture đã đóng băng và triển khai preflight SAPI + visual-card offline theo bản giao Evidence Sprint.
5. Sau đó tiếp tục SCOUT và ALPHA độc lập; mỗi phòng phải có `manifest.json`, `commands.jsonl`, `metrics.json`, raw evidence và artifact/hash riêng.
6. Chỉ gọi Sếp khi MP4 Studio thật đã qua hard gate và cần checkpoint xem một lần.

## 5. Điều kiện nghiệm thu vòng sau

- Verifier bắt được file đổi sau hash, SHA giả, path ngoài run và input snapshot bị thay.
- Negative fixtures không bao giờ tự viết `artifacts.json` sau khi logger từ chối.
- Mỗi lỗi xấu có một test độc lập và đúng một nguyên nhân dự kiến.
- Path escape bị chặn trước mọi mkdir/write.
- BLOCKED có exit 2 thật, gate `NOT_RUN`, resource/Ollama snapshot và `peak_ram=null` nếu chưa đo.
- Có bằng chứng chạy thật của ít nhất STUDIO; không chỉ có câu tuyên bố trong report.

Antigravity không được ghi “toàn bộ P0/P1 đã sửa” trước khi tất cả điều kiện trên được kiểm chứng từ artifact trên đĩa.
