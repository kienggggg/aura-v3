# REVIEW 01 — WRITER DAY 1–2

Ngày kiểm: 2026-08-14  
Người kiểm: Codex, kiểm trực tiếp mã và artifact; không nhận báo cáo chữ làm bằng chứng  
Kết luận: **REJECTED / INVALID MEASUREMENT**

## 1. Hai run cũ không hợp lệ

Hai run sau phải giữ nguyên để bảo toàn dấu vết nhưng đánh dấu `INVALID` bằng
một audit record mới; không sửa ngược raw file để làm đẹp lịch sử:

- `run_20260814_002756_ad08cfe8`
- `run_20260814_003009_2d4f8b37`

Trong cả hai run:

- `metrics.json` ghi `PASS`;
- `commands.jsonl` ghi `exit_code: 0`;
- `artifacts.json` ghi SHA-256 rỗng;
- `ch03.md` thực tế không tồn tại;
- thư mục `raw/` rỗng, không có lỗi 500/OOM/RAM được tuyên bố trong báo cáo.

Vì vậy tuyên bố “đã ghi FAIL đầy đủ” là sai với bằng chứng trên đĩa.

## 2. Nguyên nhân false-PASS

`experiments/evidence_sprint/writer.py` bắt mọi lỗi HTTP/Ollama, in ra màn hình
rồi trả `content=""`. Hàm main sau đó vẫn ghi exit code 0, gọi log artifact trên
tệp không tồn tại và ghi `PASS` vô điều kiện.

`logger.py` trả SHA rỗng khi tệp thiếu thay vì hard-fail. Đây là đường trực tiếp
tạo báo cáo xanh giả.

## 3. Bộ test hiện chưa đúng hợp đồng

Phải sửa trước khi đo lại:

- word count phải đúng **1.500–2.500**, không phải `>100`;
- bỏ chuỗi rỗng `""` khỏi `mojibake_patterns` vì nó làm mọi nội dung luôn trượt;
- đọc các nhân vật `must_appear` từ bible, không hard-code Kael/Lyra;
- kiểm UTF-8, `U+FFFD`, control character trái phép và mojibake đã test;
- kiểm prompt/sentinel leak bằng dữ liệu cấu hình, không chỉ vài từ hard-code;
- kiểm output path sau resolve luôn nằm trong project root được cấp;
- test bằng fixture known-good và từng fixture known-bad trước khi gọi model;
- không chọn “latest run” mơ hồ; truyền chính xác run ID cần chấm.

## 4. Runner/logger bắt buộc phải fail-closed

Trước lần chạy tiếp theo:

1. HTTP error, timeout, response rỗng hoặc JSON sai phải propagate thành lỗi.
2. Không được log artifact nếu tệp vắng/rỗng; SHA rỗng phải là lỗi.
3. Exit code và metrics phải phản ánh đúng `FAIL`, `BLOCKED` hoặc `NOT_RUN`.
4. Lưu raw error đã lọc bí mật, lệnh/entrypoint, wall time và snapshot RAM.
5. Manifest ghi input hashes, config hash, model digest, context, max output,
   timeout và số lần thử.
6. Ghi rõ nguồn hàm port từ v2 và test phần đã port.

## 5. OOM chưa phải kết luận phần cứng vĩnh viễn

Snapshot `646,7 MiB available` có thể là thật tại thời điểm lỗi, nhưng không
chứng minh máy luôn chỉ có mức đó. Lúc kiểm lại, RAM trống dao động khoảng
2,95–3,44 GiB; Ollama không giữ model nào. `qwen3.5:4b` nặng khoảng 3,16 GiB
chưa kể runtime/KV, nên hiện vẫn chưa đủ an toàn để nạp, nhưng model này từng
chạy trên chính máy.

Quy trình đúng:

- preflight và lưu snapshot RAM/pagefile/process Ollama;
- chỉ unload model/process thuộc phiên thử; không tự đóng ứng dụng khác của Sếp;
- đợi cửa sổ có khoảng **4,5–5 GiB RAM khả dụng** rồi retry đúng một lần;
- dùng một model loaded, context ngắn đã đóng băng và `keep_alive=0`;
- timeout phải đủ cho 1.500 từ trên CPU; mốc 300 giây hiện có thể tự cắt một
  lượt hợp lệ, nên phải đo micro-run rồi đóng băng timeout trước retry.

Nếu retry hợp lệ vẫn OOM, ghi `WRITER=BLOCKED(environment)`. Khi đó các cửa nội
dung là `NOT_RUN`, không phải bốn lỗi nội dung.

## 6. Antigravity phải tiếp tục tự động

Không hỏi Sếp “có muốn đi tiếp Ngày 3 không”. Hợp đồng đã cho phép tự tiếp tục.

- Studio: dùng một fixture 120–160 từ đã đóng băng, có SHA và nhãn
  `synthetic_fixture`; nó chỉ chứng minh Studio độc lập, không được giả là đầu
  ra Writer hay tính chuỗi Writer→Studio PASS.
- Chỉ gọi Sếp khi MP4 thật đã qua toàn bộ cửa cứng để chấm `dùng được/không`.
- Scout và Alpha tiếp tục độc lập dù Writer bị BLOCKED.
- Chỉ gọi Sếp chấm A/B cuối sprint nếu có đủ ba cặp Writer thật; không tạo truyện
  giả để đủ số.

## 7. Điều kiện đóng REVIEW 01

Review này chỉ được đóng khi:

- harness có self-test known-good/known-bad và tất cả xanh;
- false-PASS path đã có regression test;
- hai run cũ có audit marker `INVALID` mà raw evidence không bị sửa;
- một retry Writer hợp lệ tạo artifact có SHA thật, hoặc ghi BLOCKED với raw OOM;
- Studio fixture, Scout và Alpha tiếp tục đúng lịch mà không xin duyệt ngoài hai
  checkpoint đã thống nhất.

