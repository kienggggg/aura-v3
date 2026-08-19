# AGENTS.md — QUY TẮC BẮT BUỘC DÀNH CHO AGENT TRÊN AURA v3

Tài liệu này là quy tắc hành vi cốt lõi của Agent khi thao tác trên repo `D:\AURA_v3`.

## 1. NGUYÊN TẮC TỐI THƯỢNG
1. **BẰNG CHỨNG TRÊN ĐĨA LÀ CHÂN LÝ DUY NHẤT (HARD EVIDENCE ON DISK):**
   - Chỉ công nhận kết quả khi có file thật trên đĩa, byte thật, hash SHA-256 thật tính từ đĩa, exit code OS thật, và validator độc lập xác thực.
   - Báo cáo bằng chữ, lời hứa hẹn hoặc mô tả không có giá trị bằng chứng.
2. **TÁCH BIỆT WORKER VÀ VERIFIER:**
   - Mã sinh nội dung / runner KHÔNG CÓ QUYỀN tự gán `status = PASS`.
   - Chỉ có Verifier / Hard Gates độc lập mới có quyền đọc file, tính hash và ghi nhận kết quả.
3. **FAIL-CLOSED BY DESIGN:**
   - Mọi lỗi (file rỗng, thiếu hash, timeout, ngoại lệ mạng, OOM) phải trả về `FAIL` (exit code 1) hoặc `BLOCKED(environment)` (exit code 2).
   - Nghiêm cấm bắt ngoại lệ rồi im lặng trả về chuỗi rỗng `""` hoặc SHA rỗng.
4. **CẤM FAKE-PASS & STUB RÁC:**
   - Tuyệt đối không tạo file giả lập (như 14-byte mp4, chuỗi mock 1 dòng) rồi tự tuyên bố thành công.
   - Không khai man tiến độ các phòng ban khi chưa có code và artifact thực tế trên đĩa.
5. **AN TOÀN ĐƯỜNG DẪN (PATH CONFINEMENT):**
   - Luôn sử dụng `Path.resolve(strict=False)` và kiểm tra `is_relative_to()` trước khi `mkdir` hoặc ghi file. Cấm dùng `startswith()` lỏng lẻo.

## 2. QUY CHUẨN EVIDENCE SPRINT
* Mọi run phải lưu trong `data/evidence_sprint/runs/<run_id>/` với 5 tệp: `manifest.json`, `commands.jsonl`, `metrics.json`, `artifacts.json`, `raw/`.
* Chi tiết tiêu chuẩn kỹ thuật 4 phòng (Writer, Studio, Scout, Alpha) xem tại [KY_LUAT_THUC_THI.md](file:///d:/AURA_v3/KY_LUAT_THUC_THI.md).
