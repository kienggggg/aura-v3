# Sổ lỗi phòng AURA

Sổ này ghi **lỗi thật** của phòng AURA viết truyện. `SO_BENH_AN.md` là sổ lỗi của em;
tệp này là sổ lỗi của AURA. Mỗi mục là một lỗi do Sếp hoặc em chỉ ra trên một bản
AURA đã viết, kèm ví dụ trích từ chính bản ấy. Kế hoạch:
[`docs/KE_HOACH_SO_LOI_PHONG_AURA_2026-09-14.md`](docs/KE_HOACH_SO_LOI_PHONG_AURA_2026-09-14.md).

Lý do có sổ: model không giỏi lên nhờ được huấn luyện cho thông minh hơn, mà nhờ nhớ
và tránh được lỗi mình đã làm (Sếp, 14/09/2026).

**Luật của sổ** — `tests/test_so_loi_phong_aura.py` canh những luật này:

- **Loại:**
  - **A**: do chính luật của máy ép ra, chữa bằng cách sửa máy.
  - **B**: máy đếm được, chữa bằng một cửa.
  - **C**: chỉ người đọc mới thấy, chữa bằng câu dặn trong lời nhắc.
- **Trạng thái:**
  - `chờ đo`: chưa qua phép đo nào.
  - `đang dặn`: đang nằm trong lời nhắc.
  - `đã thành cửa`, `đã sửa máy`, `bỏ`.
- **Chỉ mục loại C mới có câu dặn.** Mục A và B ghi `—`, vì chúng tốn 0 token.
- **Câu dặn viết XUÔI, không chép câu sai.** Bản đồ từng bị chép nguyên chữ vào
  2/15 truyện, nên đưa câu sai vào lời nhắc thì model có thể chép lại. Cửa canh
  bác mọi câu dặn trùng ví dụ từ **5 từ liền** trở lên.
- **Trần của khối câu dặn** (mọi mục C đang `chờ đo` hoặc `đang dặn` cộng lại):
  **480 ký tự**. Con số quy từ phép đo token ngày 14/09: bản đồ 388 ký tự = 118
  token, bộ luật 397 ký tự = 119 token, tức khoảng 3,3 ký tự mỗi token. Trần 150
  token lấy tròn xuống còn 480 ký tự.
- **Repo công khai:** chỉ trích bản của AURA, không trích tác phẩm của người khác.

## Các mục

### L-01
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản X
- loại: A
- lỗi: mở bằng nguyên văn đề, không dẫn dắt
- ví dụ: "Người thợ sửa khoá đầu ngõ ngồi trên chiếc xe ba bánh cũ kỹ."
- câu dặn: —
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: lời nhắc ép "dùng lại chính những chữ đó trong câu mở"; 53/60 bản gần nhất mở câu 1 bằng đúng nguyên văn đề. Đo 14/09 (CHOT:neu-de-hai-cau): nới cửa sang câu 1–2 KHÔNG chữa được — vẫn mở bằng nguyên văn đề 14/15, lọt cửa 4/15 so với 9/15. Nguyên nhân còn lại (lời dặn "dùng lại chính những chữ đó", hoặc thói quen của model) CHƯA đo.

### L-02
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản X
- loại: C
- lỗi: nói nhân vật muốn gì trước khi giới thiệu nhân vật
- ví dụ: "Ông muốn lấy lại thứ tiếng kim loại kêu lên khi chốt bật ra."
- câu dặn: Giới thiệu nhân vật là ai, đang ở đâu, trước khi kể nhân vật muốn gì.
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: xếp loại lại sau khi Sếp chấm xong và mở khoá — lỗi có thể do lời dặn của chính nhánh ấy ép ra.

### L-03
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản X
- loại: C
- lỗi: nhắc vật, việc mà không giải thích; nhân quả không rõ
- ví dụ: "Tiếng ấy đã vắng mất hai hôm nay vì một cái ổ đóng chặt."
- câu dặn: Vật hay việc nào nhắc tới lần đầu thì nói rõ nó là gì.
- số lần gặp: 1
- trạng thái: chờ đo

### L-04
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản X
- loại: C
- lỗi: chuyển ý đột ngột, không nối với câu trước
- ví dụ: "Khách hàng là chú thanh niên vừa ngã xuống đất và đau nhói ở vai trái."
- câu dặn: Mỗi câu phải nối với câu trước: nhắc lại người, vật hoặc việc vừa kể.
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: có thể lên loại B nếu thước máy khớp mắt Sếp (kế hoạch §7).

### L-05
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản X
- loại: C
- lỗi: nhân quả nhảy cóc
- ví dụ: "Chú thợ chỉ nhìn vào chiếc áo mưa bạc màu mà không hỏi nguyên nhân tai nạn."
- câu dặn: Kể nguyên nhân trước rồi mới kể kết quả, không bỏ bước ở giữa.
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: hai câu trước mới là "vừa ngã xuống đất"; cú ngã thành "tai nạn" mà không có câu nào nối hai việc.
