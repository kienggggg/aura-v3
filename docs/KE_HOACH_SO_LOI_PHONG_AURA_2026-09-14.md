# Kế hoạch — Sổ lỗi phòng AURA (14/09/2026)

<!-- KET_CUC:CHUA_DUYET · 14/09/2026 -->
**Trạng thái: CHỜ DUYỆT. Chưa viết dòng mã nào.**

Sếp giao ngày 14/09, với một nguyên tắc: *model không giỏi lên nhờ được huấn luyện
cho thông minh hơn, mà nhờ nhớ và tránh được lỗi mình đã làm*. `CLAUDE.md` §7
yêu cầu dựng hệ thống mới thì gửi kế hoạch trước. Mọi con số dưới đây **đã chạy
trên máy này** ngày 14/09. Chỗ nào chưa chạy thì ghi **CHƯA ĐO**.

---

## 1. Việc này là gì, và KHÔNG là gì

**Là:** một cuốn sổ ghi **lỗi thật** của phòng AURA viết truyện. Mỗi lỗi do Sếp
(hoặc em) chỉ ra trên một bản AURA đã viết, và đi kèm một ví dụ trích từ chính
bản ấy. Sổ cũng ghi cách để những lần sinh sau không mắc lại lỗi đó.

**Không là:**
- Không huấn luyện model. Máy không có GPU rời, model là `qwen3.5:4b`.
- Không phải một bộ luật viết sẵn từ đầu. Bộ luật và bản đồ đang chờ Sếp chấm mù.
- Không nối NotebookLM. Kế hoạch kho tham chiếu §3 đã kiểm ngày 13/09: bản thường
  không có API công khai, còn đường không chính thức đòi phiên đăng nhập Google
  của Sếp — thứ AURA không được giữ.

## 2. Mỗi lỗi đi về chỗ RẺ NHẤT còn giữ được nó

| loại | lỗi thuộc kiểu | chữa ở đâu | tốn ngữ cảnh | độ chắc |
|---|---|---|---|---|
| **A** | do chính luật của máy ép ra | sửa luật của máy | 0 | chắc |
| **B** | máy đếm được | thành một cửa, kiểm SAU khi sinh | 0 | chắc |
| **C** | chỉ người đọc mới thấy | câu dặn trong lời nhắc | có | yếu: model có lúc quên, có lúc chép |

Cửa chữ Hán và cửa chữ Anh tuần này là loại B: nhớ một lỗi rồi không bao giờ cho
nó lọt nữa, mà không tốn một token nào. Mỗi lỗi chuyển được từ C sang B là một
lỗi không còn phải trông vào trí nhớ của model.

## 3. Ngữ cảnh: trần là THỜI GIAN, không phải số token

Đo ngày 14/09 bằng `prompt_eval_count` thật của Ollama, cùng `num_ctx` và
`num_thread` với phòng viết:

```
ngữ cảnh tối đa (num_ctx)                 4096 token
lời nhắc truyện hiện nay                   118
  + bộ luật HOẶC bản đồ (bản chưng cất)   +~120
một truyện 242 từ                         ~280
tốc độ model đọc lời nhắc                 ~37 token/s  (243 token: 6,5 s · 1.534 token: 40,5 s)
```

Phép đo tốc độ chạy lúc máy đang bận gieo lỗi, nên máy rảnh có thể nhanh hơn một
chút. Quy ra: **mỗi 100 token nhớ thêm làm mỗi lần sinh chậm khoảng 2,7 giây**.
Một lần sinh hiện mất khoảng 59 giây, và phòng có thể sinh tới 3 lần. Ngữ cảnh còn
chỗ cho khoảng 3.000 token, nhưng thời gian cạn trước ngữ cảnh rất xa.

**Đề xuất trần cho khối câu dặn: 150 token**, tức khoảng +4 giây mỗi lần sinh (~7%).

**Sửa lại một câu em đã nói với Sếp.** Em nói máy có sẵn bộ tra cứu cục bộ để
chọn mục phù hợp. Bộ ấy có thật, nhưng **phòng viết không được import nó**: hàng
rào chỉ cho hai hệ dùng chung đúng hai tệp. Nó cũng mới được đo trên tài liệu kỹ
thuật, chưa đo trên văn học. Với vài chục mục thì cũng không cần tra cứu: chọn theo
thứ tự ưu tiên, trong trần token. Khi nào sổ vượt trần và lỗi bắt đầu phụ thuộc
vào tình huống thì làm một kế hoạch riêng.

## 4. Năm lỗi đầu tiên — Sếp chấm ngày 14/09 (bộ luật, cặp 1, bản X)

| mã | lỗi | ví dụ trích từ bản X | loại |
|---|---|---|---|
| L-01 | mở bằng nguyên văn đề, không dẫn dắt | "Người thợ sửa khoá đầu ngõ ngồi trên chiếc xe ba bánh cũ kỹ." | **A** (§5) |
| L-02 | nói nhân vật muốn gì trước khi giới thiệu nhân vật | "Ông muốn lấy lại thứ tiếng kim loại kêu lên khi chốt bật ra." | C |
| L-03 | nhắc vật, việc mà không giải thích; nhân quả không rõ | "Tiếng ấy đã vắng mất hai hôm nay vì một cái ổ đóng chặt." | C |
| L-04 | chuyển ý đột ngột, không nối với câu trước | "Khách hàng là chú thanh niên…" ngay sau câu về tiếng kim loại | C, có thể lên B (§7) |
| L-05 | nhân quả nhảy cóc | câu trước "vừa ngã xuống đất", câu sau đã là "tai nạn" | C |

Loại của từng lỗi phải **xét lại sau khi Sếp chấm xong và mở khoá**. Một lỗi có
thể do chính lời dặn của nhánh ấy ép ra, và khi đó nó thuộc loại A chứ không phải C.

## 5. L-01 là lỗi của MÁY — sửa ở máy, không đưa vào sổ

Đếm trên 60 bản gần nhất, gộp mọi nhánh:

```
câu 1 BẮT ĐẦU bằng đúng nguyên văn đề   53/60
câu 1 CÓ nguyên văn đề ở đâu đó         56/60
```

Lời nhắc hiện nay viết: *"BẮT BUỘC: câu đầu tiên phải nhắc tới {đề} — dùng lại
chính những chữ đó trong câu mở"*. Lời ấy được thêm ngày 08/09, vì trước đó cửa
nêu đề bác 10/11 lượt, toàn ở các đề trừu tượng. Bỏ lời ấy đi thì cửa nêu đề lại
bác nhiều như cũ.

**Đề xuất đo, chưa sửa:** nới cửa nêu đề từ "câu 1" thành "câu 1 hoặc câu 2", và
đổi lời nhắc thành "nhắc tới đề trong hai câu đầu". Như vậy model có một câu để
dẫn dắt.

Nguy cơ: cửa này sinh ra ngày 04/09 vì một truyện lạc đề vẫn ĐẠT. Nới ra hai câu
vẫn giữ việc bắt lạc đề, nhưng điều ấy **CHƯA ĐO**.

Đo trên 3 đề mới × 5 hạt, hai số:
- tỉ lệ lọt cửa nêu đề — không được tụt quá 2/15;
- tỉ lệ câu 1 mở bằng nguyên văn đề — phải giảm.

## 6. Sổ để ở đâu, viết thế nào

**Chỗ để, đề xuất:** tệp `SO_LOI_PHONG_AURA.md` ở gốc repo, nằm cạnh
`SO_BENH_AN.md` (sổ lỗi của em). Git theo dõi tệp này, và Sếp mở ra sửa trực tiếp
được. Repo là **công khai**, nên sổ chỉ trích bản của AURA, không trích tác phẩm
của người khác.

**Mỗi mục có đủ các trường:**
- mã · ngày · ai thấy · loại (A/B/C);
- lỗi, viết trong một câu;
- ví dụ thật, dài tối đa một câu;
- câu dặn;
- số lần gặp;
- trạng thái: *đang dặn* · *đã thành cửa* · *đã sửa máy* · *bỏ*.

**Chỉ mục loại C đang ở trạng thái *đang dặn* mới vào lời nhắc.** Hai loại kia
tốn 0 token.

**Câu dặn viết XUÔI, không kèm câu sai.** Bản đồ đã bị chép nguyên chữ vào 2/15
truyện. Đưa câu sai vào lời nhắc thì model có thể chép lại chính câu sai ấy. Ví
dụ chỉ nằm trong sổ, cho người đọc.

**Trần 150 token cho khối câu dặn.** Vượt trần thì chọn theo số lần gặp, rồi theo
ngày; cách chọn tất định. Không thêm tệp mã mới: danh sách đóng của hệ phòng đã
dùng 7/8 chỗ. Phòng viết (module core.viet_truyen) đọc thẳng tệp sổ.

**Cửa canh:**
- Sổ đúng định dạng: đủ trường, không trùng mã.
- Khối câu dặn nằm trong trần. Trần ký tự quy đổi từ phép đo token, và phải ghi
  rõ con số quy đổi.
- Mỗi lượt chạy thật ghi `prompt_eval_count` vào sổ lượt.

## 7. Đường từ C lên B — biến một câu dặn thành một cửa

L-04 (chuyển ý đột ngột) có một thước thô mà máy đếm được: một câu không có từ nội
dung nào chung với câu trước, và cũng không có đại từ nối lại. Chưa biết thước ấy
có khớp với mắt Sếp hay không.

**Cách kiểm:**
1. Trên các bản Sếp đã chấm, đánh dấu những chỗ Sếp gọi là "chuyển đột ngột".
2. So những chỗ ấy với chỗ thước máy chỉ ra.
3. Khớp đủ ngưỡng đăng ký trước — đề xuất: bắt được ≥ 4/5 chỗ Sếp chỉ, và báo
   nhầm ≤ 1/10 chỗ Sếp không chỉ — thì lời dặn thành cửa: 0 token, model không
   cần nhớ nữa.
4. Không khớp thì lỗi ở lại loại C.

Phép kiểm này cần thêm lời chấm của Sếp. **CHƯA ĐO.**

## 8. Phép thử — ngưỡng đăng ký trước khi chạy

Sau khi Sếp duyệt, ngưỡng sẽ chép vào một khối `CHOT` trong đặc tả, rồi mới chạy
lượt model đầu tiên.

**Hai nhánh:**
- nhánh **0**: lời nhắc hiện nay;
- nhánh **S**: khối câu dặn (L-02…L-05) đặt trước lời nhắc hiện nay.

**3 đề MỚI × 5 hạt × 2 nhánh = 30 lượt.** Không dùng lại ba đề cũ: sổ lấy ví dụ từ
đề "người thợ sửa khoá đầu ngõ", nên chấm trên chính đề ấy là chỉnh theo bộ dùng
để chấm.

| đơn | ngưỡng đề xuất |
|---|---|
| lọt cửa phòng viết, 15 lượt mỗi nhánh | S ≥ 0 − 2 |
| truyện chép nguyên chữ khối câu dặn (≥ 5 từ liền trùng) | S ≤ 1/15 |
| thời gian thêm mỗi lần sinh | ≤ 10% |
| em chấm mù theo danh sách lỗi L-02…L-05, đếm tổng số lỗi | S ≤ 2/3 của nhánh 0 |
| Sếp chấm lại mù, 3 cặp | S hơn ở ≥ 2/3 |

**Luật quyết định:** đạt cả năm hàng thì khối câu dặn vào lời nhắc. Hỏng hàng 1,
2 hoặc 3 thì dừng, ghi số, không cần Sếp chấm.

**Giới hạn, nói trước.** Em chấm theo đúng danh sách lỗi mà nhánh S được dặn
tránh. Như vậy hàng 4 đo độ **tuân lệnh**, chưa chắc đo độ **hay**, đúng cái bẫy
đã ghi ở bộ luật và bản đồ. Vì thế hàng 5 do Sếp chấm mới là chốt. Lỗi MỚI, không
có trong sổ, em ghi riêng và báo, không tính vào hàng 4.

## 9. Nối với bộ luật và bản đồ đang chờ chấm

- Nếu Sếp chấm bộ luật hoặc bản đồ thắng, chúng vào lời nhắc trước, và nhánh 0 của
  phép thử này dùng lời nhắc mới ấy.
- Nếu chúng thua, phép thử dùng lời nhắc hiện nay.

Nên chạy phép thử **sau** khi Sếp chấm xong hai tệp. Mỗi lỗi Sếp ghi trong lúc
chấm sẽ thành một mục mới trong sổ.

## 10. Việc cần Sếp

1. Duyệt hoặc sửa kế hoạch này.
2. Chọn chỗ để sổ (em đề xuất gốc repo, §6).
3. Chấm mù hai tệp trong `data/cham_mu/`.
4. Chọn 3 đề mới cho phép thử, hoặc để em chọn.
5. Nhánh sửa cửa nêu đề (§5) đo riêng hay gộp chung vào phép thử này.

## 11. CHƯA chặn được

- Model 4B có thể **nhớ mà vẫn không làm được** điều được dặn. Lỗi mạch lạc là
  giới hạn năng lực của model, không chỉ là chuyện quên.
- Mỗi mục hiện nay dựa trên **một** ví dụ trong **một** truyện: n = 1.
- L-02, L-03, L-05 chưa có thước máy nào.
- Câu dặn dù viết xuôi vẫn có thể bị chép nguyên chữ. Hàng 2 đo đúng điều ấy.
