# ANTIGRAVITY REVIEW — WRITER 02

Ngày kiểm tra: 2026-08-14  
Phạm vi: `D:\AURA_v3\experiments\evidence_sprint` và các run Writer hiện có  
Kết luận: **CHƯA NGHIỆM THU — sửa đúng một phần, nhưng vẫn còn đường PASS giả và bằng chứng chưa bất biến.**

## 1. Những phần đã được xác nhận là đúng

- Hai run xanh giả cũ đã có `audit.json` đánh dấu `INVALID`; các tệp bằng chứng gốc không bị sửa.
- Lỗi HTTP, timeout và JSON từ Ollama không còn bị biến thành nội dung rỗng rồi tiếp tục như thành công.
- Run mới có thể ghi `BLOCKED(environment)` cùng `raw/error.txt` khi RAM khả dụng dưới ngưỡng.
- `TARGET_RUN_ID` đã bắt buộc.
- Cửa độ dài đã trở về đúng 1.500–2.500 từ.
- Chuỗi rỗng trong danh sách mojibake đã được loại bỏ; U+FFFD đã được kiểm.
- Chạy lại độc lập cho kết quả:
  - `run_known_good`: 4/4 cửa hiện có PASS, 2.300 từ.
  - `run_known_bad`: 4/4 cửa hiện có FAIL.

Các kết quả trên chỉ xác nhận một phần cơ khí của harness, chưa đủ đóng REVIEW 01.

## 2. Lỗi chặn nghiệm thu

### P0 — Runner ghi PASS trước khi chạy cửa cứng

`writer.py` đang ghi `metrics.status = PASS` ngay sau khi tạo artifact, nhưng không chạy bộ gate trước khi quyết định trạng thái. Một chương 10 từ, thiếu nhân vật hoặc rò prompt vẫn có thể được runner ghi PASS.

Yêu cầu:

1. Runner phải gọi cùng một hàm gate mà pytest dùng, hoặc một thư viện gate dùng chung.
2. Chỉ ghi PASS khi tất cả hard gate PASS.
3. Gate fail phải ghi FAIL cùng kết quả từng gate; không được để pytest sau đó là nơi duy nhất phát hiện.
4. Gate chưa chạy do môi trường phải ghi `NOT_RUN`, không được ghi FAIL nội dung.

### P0 — Bằng chứng run cũ có thể bị run mới ghi đè

Mọi run hiện trỏ tới cùng `projects\proj_evidence_01\chapters\ch03.md`. Run sau có thể thay nội dung mà `artifacts.json` của run trước vẫn trỏ vào đường dẫn đó. Test hiện đọc file mới nhất và không đối chiếu SHA.

Yêu cầu:

- Mỗi run phải snapshot artifact bất biến vào chính thư mục run, ví dụ `runs\<run_id>\artifacts\ch03.md`.
- `artifacts.json` chỉ trỏ tới snapshot thuộc run đó.
- Tính lại SHA-256 khi nghiệm thu và so với manifest; sai hash hoặc mất file là FAIL-INTEGRITY.
- Snapshot `bible.json`, `style_card.json` và cấu hình dùng cho run, kèm SHA-256.

### P0 — Tệp 0 byte vẫn được logger nhận

SHA-256 của tệp rỗng là một chuỗi hợp lệ (`e3b0...`), nên `if not sha256` không bắt được.

Yêu cầu trước khi hash:

- đường dẫn tồn tại;
- là file thường;
- kích thước lớn hơn 0;
- nằm trong thư mục artifact được cấp cho run.

Thiếu một điều kiện phải làm lệnh thất bại và tiến trình thoát khác 0.

### P0 — Exit code thật vẫn là 0

Nhánh `BLOCKED`/`FAIL` bắt exception, tự ghi `commands.jsonl.exit_code = 1`, rồi kết thúc bình thường. Vì không `raise`/`SystemExit`, mã thoát thật của tiến trình vẫn là 0.

Yêu cầu:

- PASS: OS exit 0.
- FAIL: OS exit 1.
- BLOCKED(environment): OS exit 2.
- Giá trị trong `commands.jsonl` phải lấy từ kết quả thật hoặc khớp chính xác với exit code thật; không tự khai một mã khác.

### P0 — Kiểm tra đường dẫn có thể bị vượt qua

Runner tạo thư mục trước khi kiểm tra, rồi dùng `startswith()`. Đường như `...\projects_evil` vẫn có thể lọt.

Yêu cầu:

- Resolve/normalize đường dẫn trước mọi `mkdir` hoặc ghi file.
- Dùng `Path.resolve()` cùng `is_relative_to()` hoặc `os.path.commonpath`, không dùng so tiền tố chuỗi.
- Test bắt buộc cho sibling `projects_evil`, `..`, symlink/junction nếu môi trường cho phép, và artifact path do JSON trỏ ra ngoài.

## 3. Các thiếu sót P1 phải sửa trong cùng vòng

### Integrity và khả năng tái lập

Manifest mỗi run phải có:

- SHA-256 của `bible.json`, `style_card.json`, prompt/config và mã runner/gate;
- model name + model digest, `num_ctx`, `num_predict`, temperature, seed;
- timeout thật, số attempt thật;
- snapshot RAM khả dụng, pagefile/swap, Ollama process/model state trước khi chạy;
- nguồn/commit của logic được port;
- trạng thái từng gate: PASS/FAIL/NOT_RUN.

Không ghi `max_retries: 1` nếu mã không retry. Hoặc triển khai đúng một retry có log riêng, hoặc ghi `max_retries: 0`. `peak_ram_mb = 0` phải đổi thành `null/unmeasured` nếu chưa đo, không được giả là phép đo bằng 0.

### Timeout

Mốc 300 giây chưa được chứng minh đủ để sinh 1.500–2.500 từ trên CPU. Trước lần chạy thật:

1. Chạy một micro-run có giới hạn output cố định.
2. Ghi tốc độ sinh, load time và total wall time.
3. Từ đó đóng băng timeout cho bài Writer; không tự đổi giữa baseline và candidate.

### Gate và self-test

- Chỉ bắt các nhân vật có `must_appear: true`; dùng so khớp token/word boundary, không để `Kaelly` làm `Kael` PASS.
- Bắt NUL, C0/C1 control và bidi control không được phép; chữ ngoại ngữ hợp lệ chỉ cảnh báo, không tự phán ngữ nghĩa.
- Chuẩn hóa Unicode, khoảng trắng và chữ hoa/thường trước khi dò sentinel/prompt leak.
- Leak gate phải lấy sentinel/config fragment từ snapshot đầu vào, không chỉ vài heading cố định hoặc 20 ký tự đầu.
- Test phải giới hạn artifact path trong run và tự tính lại SHA.
- Tạo từng fixture xấu độc lập: missing file, zero-byte, hash mismatch, word-count low/high, mojibake/control, missing required character, prompt leak, path escape, HTTP error và runner PASS-before-gate.
- Fixture phải được tạo bằng logger thật với hash thật; xóa literal `fakehash`.
- Test cả `metrics.json`, `commands.jsonl` và exit code thật, không chỉ bốn assert nội dung.
- `raw/error.txt` phải qua bộ lọc secret/credential trước khi ghi.

## 4. Trạng thái Writer và cách tiếp tục Sprint

- Hai run đầu: `INVALID`.
- Run mới ở 1,77 GiB RAM khả dụng: `BLOCKED(environment)` hợp lệ ở mức snapshot hiện tại, **không phải bằng chứng Writer bị chặn vĩnh viễn bởi phần cứng**.
- Sau khi sửa harness, chỉ retry Writer khi preflight thấy tối thiểu 4,5–5 GiB RAM khả dụng. Chỉ dọn model/process do Sprint sở hữu; không đóng ứng dụng của Sếp và không kill rộng theo tên process.
- Nếu retry vẫn OOM, giữ Writer `BLOCKED(environment)` và không tạo A/B giả.

Không được dừng toàn Sprint để hỏi Sếp. Trong lúc Writer chờ RAM:

- STUDIO tiếp tục bằng fixture 120–160 từ đã đóng băng, có hash và nhãn rõ `STUDIO_FIXTURE`; không tuyên bố đó là đầu ra Writer và không tính là Writer→Studio end-to-end.
- SCOUT và ALPHA tiếp tục độc lập theo kế hoạch đã giao.
- Chỉ gọi Sếp ở checkpoint Ngày 3 khi đã có MP4 thật qua hard gate để xem một lần.
- Không có 3 cặp Writer thật thì checkpoint A/B cuối Sprint là `NOT_RUN`; tuyệt đối không tạo dữ liệu giả để hỏi Sếp.

## 5. Điều kiện đóng REVIEW 02

REVIEW 02 chỉ được đóng khi Antigravity cung cấp toàn bộ:

1. Các test regression P0/P1 ở trên chạy lại xanh với bằng chứng thô.
2. Một fixture tốt PASS và từng fixture xấu độc lập FAIL đúng một lý do dự kiến.
3. Một run BLOCKED/FAIL có exit code OS khác 0 và log khớp.
4. Một artifact 0 byte, hash sai, đường dẫn ngoài run và output rò prompt đều không thể được ghi PASS.
5. Run artifact và input snapshot bất biến, hash được tái kiểm độc lập.
6. Sprint tự tiếp tục STUDIO/SCOUT/ALPHA mà không hỏi quyền đi tiếp.

## 6. Chỉ thị thực thi

Antigravity đọc tệp này và tiếp tục tự động. Không tạo thêm implementation plan để xin xác nhận; không đánh dấu task hoàn tất trước khi các điều kiện đóng ở mục 5 có bằng chứng chạy thật. Không sửa báo cáo cũ để che sai lệch; chỉ append audit/correction mới.
