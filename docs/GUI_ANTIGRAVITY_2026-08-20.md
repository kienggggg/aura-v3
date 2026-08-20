# Gửi Antigravity — dán nguyên phần dưới

*(Sếp dán từ dòng kẻ trở xuống. Bản đầy đủ nằm ở
`D:\AURA_v3\GIAO_LAI_ANTIGRAVITY_APP_THE_2026-08-20.md`, 5 việc, có mã mẫu.)*

---

Chào Antigravity. Đã nghiệm thu app lập trình bằng THẺ bản v1. **Chạy lại chứ
không đọc báo cáo** — đúng luật §7 của `CLAUDE.md` mà bạn đã theo khi gửi kế
hoạch trước lúc thực thi.

**Những gì bạn báo, tôi chạy lại và đúng cả:** pytest 19/19 · parity 22/22 ·
bind đúng `127.0.0.1` (netstat) · mã thông hành thiếu/sai đều 403, đúng thì 200 ·
chặn `..` và đường tuyệt đối ngoài kho · trần sandbox cắt đúng **5,0s** mã thoát
124. Riêng lời khai *"CHƯA chặn được ghi tệp"* — tôi thử, mã trong sandbox tạo
được tệp ở `C:\Users\baloa\` thật. **Khai đúng sự thật, chỗ đó làm rất đàng
hoàng.** `_trich_duoi_dong` xử lý `end_col_offset` là byte UTF-8 chứ không phải
ký tự cũng kỹ hơn tôi dặn.

**Chỗ chưa xong:** cửa cứng 1 không đo được gì. `the_v1.py:730` có đường tắt
`if not record.has_modifications: return record.raw_bytes`, mà test thì mở tệp
→ không sửa gì → lưu, nên đi thẳng vào nhánh đó. SHA khớp 100% với **mọi** tệp
kể cả tệp phân tích hỏng, vì bộ sinh mã chưa hề chạy.

Ép đi qua bộ sinh mã (gõ lại đúng giá trị cũ vào một thẻ rồi lưu — việc người
dùng làm hằng ngày), 66 tệp `.py`, 4.9xx thẻ:

```
50,0%  y hệt từng byte
72,6%  giữ đúng nghĩa
18,0%  ĐỔI NGHĨA ÂM THẦM   tệp vẫn dịch được, chương trình đã khác
 9,3%  VỠ CÚ PHÁP          tệp không chạy được nữa
55/66  tệp dính
```

**Đã dựng sẵn bộ đo để bạn tự bấm, không phải chờ tôi soát:**

```
venv\Scripts\python.exe -X utf8 tools\do_cua_cung_the.py
```

Ghi `data/the_v1/cua_cung.json`, dựng `data/the_v1/bao_cao.html` **từ chính tệp
JSON đó** (mở bằng trình duyệt, bấm vào mục chi tiết là ra đúng tệp:dòng nào
hỏng). Mã thoát `0` đạt · `1` đo được mà không đạt · `2` không đo được. Hiện
đang là `1`.

**Năm việc, thứ tự nên làm:**

1. **Bộ đọc phải TỰ KIỂM.** Dựng xong một thẻ thì sinh lại dòng từ chính thẻ đó,
   so với nguồn; lệch một byte thì **hạ xuống `ma_tho`**. Cửa cứng đặt ở lúc ĐỌC
   thay vì chỉ lúc LƯU. Khoảng mười dòng, gỡ được cả cửa 1 lẫn cửa 4. Gốc của
   vấn đề là bộ 11 thẻ **không biểu diễn nổi Python** — thẻ `ham` chỉ có
   `ten_ham` + `tham_so`, không có ô nào chứa `-> bool`, `: object`, hay
   `= None`, nên `def f(x: object = None) -> bool:` mất sạch phần thừa
   (178/460 thẻ `Định nghĩa hàm`). Đừng đuổi theo cho đủ thẻ; cứ hạ xuống mã
   thô, người dùng vẫn sửa được, chỉ là sửa dưới dạng mã thô.

2. **Sửa test cửa cứng 1 cùng lúc** — đánh dấu `da_sua = True` từng thẻ rồi mới
   so byte, và `rglob` thay `glob` (bản hiện tại quét 42 tệp trong khi bốn thư
   mục có 64). Test không trượt được trên mã hỏng thì không phải test.

3. **Chú thích cuối dòng trên thẻ KHỐI.** `the_v1.py:288` đặt `duoi_dong = ""`
   khi `l_start != l_end`, mà thẻ khối thì **luôn** khác — nên mất 4/4. Thẻ lẻ
   thì giữ được 22/22, chỗ đó bạn làm đúng. Đừng dò dấu `#` (đã đo: phá 2/5 dòng
   thử). Chạy `tokenize.generate_tokens` một lượt, dựng bảng
   `{số dòng → chú thích}`, tra bảng cho cả thẻ lẻ lẫn thẻ khối.

4. **`elif` — chỗ nguy hiểm nhất trong bản này.** 37 thẻ `Nếu` sinh ra `if` thay
   vì `elif`, và **28/40 thẻ `Ngược lại` sinh ra `else:` — mất luôn điều kiện**,
   nhánh chạy cả khi điều kiện sai. Trong cây cú pháp, `elif` là nút `If` nằm
   trong `orelse`; bộ đọc đang gắn cả cụm `orelse` vào thẻ `Ngược lại`.
   **19/28 chỗ nằm trong chính `core/the_v1.py`** — mở mã của app bằng app rồi
   lưu thì nó tự làm hỏng mình. Làm việc 1 trước thì cả 28 chỗ tự hạ xuống mã
   thô; xong hẵng quyết có thêm ô `noi_tiep` hay không.

5. **Origin so bằng hostname.** `the_api.py:65` dùng `"127.0.0.1" in origin`, nên
   `http://127.0.0.1.evil.com` và `http://localhost.evil.com` đều **lọt** (đo
   thật trên máy chủ đang chạy: mã 200). Dùng `urllib.parse.urlsplit` rồi so
   `hostname in {"127.0.0.1","localhost","::1"}`. Mức nguy hiểm **thấp** vì lớp
   mã thông hành vẫn đứng — nhưng câu *"Bảo mật: 4 lớp"* in lúc khởi động đang
   nói quá một lớp, sửa xong hẵng đếm lại.

**Một chuyện về bộ đo, nói trước cho sòng phẳng.** Nó đã tự sai một lần: bản đầu
chấm cửa 4 ra 444 thẻ tả sai. Tra ba thẻ `else:` bị chấm sai thì lộ ra lỗi của
tôi — tôi đếm chiều sâu đệ quy để suy mức thụt đầu dòng, trong khi
`TheNode.indent` lưu sẵn **số dấu cách**, và chiều sâu đệ quy lệch hẳn vì
`ma_tho` cũng lồng con. Sửa thành `nut.indent // 4` thì số tụt còn ~390, thẻ
`In ra` gần sạch, `Ngược lại` còn đúng 28 = số dòng `elif` thật. **68 thẻ bị tôi
vu oan.** Nếu thấy chỗ nào trong bốn cửa còn chấm bằng thứ tôi tự đếm thay vì
thứ máy ghi lại được thì cứ bắt — nói kèm dòng mã và số.

**Đừng sửa bộ đo để nó xanh.** Xong mỗi việc thì chạy lại và **dán số**, đừng
dán chữ "PASS". Bốn cửa ra `0` thì gửi lại, tôi soát bằng cách chạy.

Trong lúc chưa xong: **chưa dùng app này để sửa mã thật.** Chạy thử và học thì
được.

---

**BỔ SUNG — đọc trước khi bắt đầu VIỆC 1.**

Sau khi giao bản trên, tôi đã đo thử **LibCST** (Meta, MIT) xem có thay được bộ
đọc/sinh mã không. Đo chứ không đọc tài liệu:

```
.venv-cst\Scripts\python.exe -X utf8 tools\do_libcst.py     -> mã thoát 0

1. mở rồi lưu, không sửa gì        : khớp từng byte 67/67 (55 ms/tệp, 16 tệp CRLF)
2. CHẠM mọi câu lệnh qua with_changes: 3.888 nút, khớp từng byte 67/67
3. đổi thật một tên biến           : đúng 4 dòng đáng đổi, không dòng nào khác
   giữ chú kiểu · giá trị mặc định · kiểu trả về · elif · chú thích cuối dòng
   trên elif · dấu thăng trong chuỗi — CÓ hết
```

Đặt cạnh bản v1: **sửa một chỗ rồi lưu, v1 giữ nguyên byte 49,8%, LibCST 100%
trên 3.888 nút.** `elif` giữ nguyên thay vì thành `else:`.

Lý do gốc: `ast` **cố ý** vứt dấu cách, chú thích, và cả `elif` (nó chỉ là nút
`If` lồng trong `orelse`, không có cờ phân biệt). Bạn phải tự bù bằng
`line_start`/`duoi_dong`/`ma_tho` — và cả bốn lỗi đều sinh ra từ chỗ bù đó. Không
phải bạn làm ẩu; nền móng thiếu.

**Nếu đổi sang LibCST thì VIỆC 1, 2, 3 biến mất** chứ không phải được vá.
**VIỆC 4 (Origin) và VIỆC 5 (test) vẫn phải làm** — không liên quan.

Cái giá, nói cùng lúc:

- LibCST **chỉ có bên Python** — `validator.js` và 22 test parity không dùng
  được. Bên trình duyệt phải gọi máy chủ để mở/lưu; phần kiểm đỏ/vàng vẫn chạy
  tại chỗ vì nó soi cây thẻ, không soi mã. **Đây là chỗ phải quyết trước khi
  viết.**
- Chậm hơn `ast` khoảng 50 lần (55 ms so với ~1 ms mỗi tệp). Mở một tệp không ai
  thấy; quét cả kho mất 3,7 giây.
- 29 MB, có phần biên dịch sẵn bằng Rust, cài vào venv riêng `.venv-cst`.
- **Vẫn cần thẻ `ma_tho`** — LibCST lo chuyện *giữ nguyên*, không lo chuyện bộ 11
  thẻ tả được bao nhiêu. Khác biệt: nút thẻ không tả được thì hiện nguyên văn và
  không ai đụng, thay vì bị ép vào thẻ rồi mất dữ liệu.
- Phải viết lại `doc_tep_py_sang_cay_the` + `luu_cay_the_ra_tep_py`, khoảng 400
  dòng. **Giao diện, 5 đỏ, 4 vàng, sandbox, 4 lớp bảo mật giữ nguyên hết.**

**Đề nghị:** làm VIỆC 4 và VIỆC 5 trước (nhỏ, độc lập với mọi hướng), rồi thay bộ
đọc bằng LibCST thay cho VIỆC 1–3. Bốn cửa trong `tools\do_cua_cung_the.py`
**không đổi** — vẫn là cửa nghiệm thu. Nếu LibCST vướng gì mà **đo ra được** thì
nói, quay lại VIỆC 1–3 vẫn kịp.
