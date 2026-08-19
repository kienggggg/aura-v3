# KỶ LUẬT THỰC THI VÀ CHỐNG GIAN LẬN CHO AGENT (AURA v3)

Tài liệu này là luật bất biến dành riêng cho Agent khi thực thi công việc trong workspace `D:\AURA_v3`. Mọi hành động của Agent đều phải tuân thủ nghiêm ngặt các nguyên tắc dưới đây.

---

## 1. NGUYÊN TẮC BẤT DI BẤT DỊCH
* **Bằng chứng trên đĩa là chân lý duy nhất:** Chỉ công nhận kết quả khi có file vật lý thật, byte thật, SHA-256 thật tính từ đĩa, exit code thật và validator độc lập xác thực.
* **Tách rời Worker và Verifier:** Runner/Generator chỉ sinh file, TUYỆT ĐỐI không tự ghi `status = PASS`. Chỉ có bộ Gate/Verifier độc lập mới có quyền đọc file và ghi nhận kết quả.
* **Fail-Closed:** Bất kỳ lỗi nào (empty file, timeout, OOM, hash mismatch, path escape) mặc định là `FAIL` (exit code 1) hoặc `BLOCKED` (exit code 2). Không nuốt lỗi, không fallback sang PASS.
* **Cấm Fake-PASS & Stub rác:** Tuyệt đối không tạo file giả lập 14 bytes hay chuỗi mock rồi tự xưng thành công.

---

## 2. QUY CHUẨN 4 PHÒNG TRONG EVIDENCE SPRINT
* **WRITER:**
  - Độ dài 1.500–2.500 từ.
  - Khớp nhân vật bắt buộc bằng boundary regex `\b`.
  - Chuẩn hóa Unicode `NFC` + `casefold` + dọn khoảng trắng trước khi dò leak/sentinel.
  - Cấm control character trái phép (C0/C1, bidi không hợp lệ).
* **STUDIO:**
  - Voice Việt thật qua SAPI OneCore token `MSTTS_V110_viVN_An`.
  - Ít nhất 3 thẻ visual card 720×1280 sinh bằng PIL.
  - Video dọc 720×1280, thời lượng 55–65s, render bằng FFmpeg thật.
  - Phải qua `ffprobe` (xác nhận audio non-silence) và `blackdetect` (không có khung đen > 2s).
* **SCOUT:**
  - Tối thiểu 3 câu hỏi cần dữ kiện mới; ≥2 domain độc lập.
  - Mọi dữ kiện phải có `source_receipt` (canonical URL, fetched_at, status 200, content_sha256).
  - Lưu raw HTML snapshot vào `run_<id>/raw/scout/`.
* **ALPHA:**
  - Sandbox cô lập hoàn toàn, no-network, timeout + resource budget.
  - 7 khóa chống gian (chặn mock pytest, chặn đọc file test, chặn import bừa bãi...).
  - Chạy qua 5 bài sanity + 5 bài hidden. Patch chỉ nằm trong sandbox, không áp vào repo AURA thật.

---

## 3. BẢO VỆ VÙNG ĐỆM ĐƯỜNG DẪN (PATH CONFINEMENT)
* Bắt buộc `Path.resolve(strict=False)` và `is_relative_to()` trước mọi lệnh `mkdir` hoặc ghi tệp.
* Cấm dùng `startswith()` trên chuỗi chưa resolve.
* Chặn mọi đường dẫn chứa `..`, sibling ngoài run (`projects_evil`), symlink/junction trái phép.

---

## 4. KỶ LUẬT THẢO LUẬN ĐA TÁC TỬ (MULTI-AGENT PROTOCOL)
* **Cấm mạo danh:** Tuyệt đối không tự bịa lời, không giả lập phiên chat, không viết hộ lượt của Claude, Codex hay bất kỳ Agent nào.
* **Kỷ luật phân lượt (Turn-Taking Barrier):** Phải chờ đến đúng lượt của mình mới được ghi file. Khi chưa tới lượt, chỉ đọc, cắm watcher theo dõi ngầm và chuẩn bị trước nội dung phân tích.
* **Ước lượng thời gian & Heartbeat:** Phải nêu rõ thời gian dự kiến thực thi (ETA) để các bên không bị treo chờ đợi.

---

## 5. TỰ ĐỘNG KHÔI PHỤC BỐI CẢNH ĐẦU PHIÊN (ZERO-MANUAL CONTEXT)
* **Chủ động đọc trạng thái:** Mỗi khi bắt đầu một phiên làm việc mới, Agent PHẢI TỰ ĐỘNG đọc các file trạng thái cốt lõi (`thaoluan.md`, `CLAUDE.md`, `AGENTS.md`, báo cáo review gần nhất) để nắm ngay bối cảnh mà KHÔNG ĐƯỢC CHỜ SẾP NHẮC.
* **Cấm phiền nhiễu:** Tuyệt đối không bắt Sếp phải giải thích lại lịch sử, nhắc đọc phiên cũ hay thực hiện thao tác mồi thủ công.
