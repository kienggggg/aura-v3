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
- lỗi: câu mở không giới thiệu nhân vật là ai, nhảy thẳng vào việc — không dẫn dắt
- ví dụ: "Người thợ sửa khoá đầu ngõ ngồi trên chiếc xe ba bánh cũ kỹ."
- câu dặn: —
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: lời nhắc chỉ đòi câu 1 "nhắc tới" đề và "dùng lại chính những chữ đó"; 53/60 bản gần nhất mở câu 1 bằng đúng nguyên văn đề. Đo 14/09 (CHOT:neu-de-hai-cau): nới cửa sang câu 1–2 KHÔNG chữa được — vẫn mở bằng nguyên văn đề 14/15. SỬA TÊN LỖI 14/09 chiều: bản Y cùng cặp CŨNG mở bằng nguyên văn đề ("Người thợ sửa khoá đầu ngõ là người đàn ông…") mà Sếp khen câu ấy — nên lỗi không nằm ở việc lặp đề, mà ở việc không giới thiệu. Đo 14/09 (CHOT:mo-truyen-gioi-thieu): nhánh G ("giới thiệu {đề} là ai hoặc là gì") qua hàng máy, lọt cửa 8/15 so với 9/15; 11/15 câu mở có dạng giới thiệu. Nhánh D bị loại, lọt 4/15. CHỜ Sếp chấm 3 bộ ba.

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
- số lần gặp: 3
- trạng thái: chờ đo
- ghi chú: có thể lên loại B nếu thước máy khớp mắt Sếp (kế hoạch §7). Gặp lại hai lần ở bản Y cùng cặp (14/09 chiều): câu tả thói quen làm việc buổi sáng nhảy sang "Cái chìa khóa lớn nặng trĩu…"; "Không ai biết rõ tuổi tác thực sự của anh…" rồi "Chỉ những người rất thân thiết mới hiểu…" — Sếp: hai câu không liên quan gì nhau.

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

### L-06
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản Y
- loại: C
- lỗi: tả một thói quen mà không nói mức độ — luôn, thường, thỉnh thoảng, hay chỉ khi nào
- ví dụ: "Người thợ sửa khoá đầu ngõ là người đàn ông đeo kính râm mà mọi gia đình trong hẻm đều quen thuộc."
- câu dặn: Tả thói quen của nhân vật thì nói rõ mức độ: luôn, thường, thỉnh thoảng, hay chỉ khi nào.
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: Sếp khen câu này "khá tốt" — nó giới thiệu được người thợ là ai — chỉ thiếu mức độ của chuyện đeo kính.

### L-07
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản Y
- loại: B
- lỗi: chữ Hán lẫn vào câu tiếng Việt
- ví dụ: "Cái chìa khóa lớn nặng trĩu trong tay anh được mài rất光亮, phát ra ánh kim khi bị chạm vào mặt trời."
- câu dặn: —
- số lần gặp: 2
- trạng thái: đã thành cửa
- ghi chú: cùng bản còn "遇到过" ở câu 17. Bản này sinh 13/09 TRƯỚC khi có cửa chữ Hán (CHOT:chu-han-kich-ban, commit 7b2945b); từ đó cửa bác mọi bản mang chữ Hán — lỗi đã được máy nhớ, không tốn token nào.

### L-08
- ngày: 14/09/2026
- ai thấy: Sếp, chấm mù bộ luật, cặp 1, bản Y
- loại: C
- lỗi: tả thái quá, phóng đại việc nhân vật làm
- ví dụ: "Những năm qua, anh đã cứu trợ biết bao ngôi nhà khỏi những kẻ trộm lén lút."
- câu dặn: Tả vừa đủ và đúng mức, không phóng đại việc nhân vật làm.
- số lần gặp: 1
- trạng thái: chờ đo
- ghi chú: Sếp chỉ cả đoạn từ câu này tới "…một lần sửa chữa đơn giản" (câu 5–9 của bản Y).
