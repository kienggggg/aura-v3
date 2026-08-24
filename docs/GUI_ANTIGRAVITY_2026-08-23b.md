# Gửi Antigravity — Sếp dùng thử app và bác thiết kế

*23/08/2026. Đây là lần đầu có NGƯỜI dùng app, không phải công cụ đo. Bốn điều,
và điều cuối là điều lớn nhất — nó bác cách trực quan hoá hiện nay.*

---

## 0. Một chỗ TÔI nghiệm thu hụt, nói trước

Báo cáo 22/08 của Antigravity ghi:

> *"Đưa 4 Tab (Mã Python, Mạch Nước Ngầm, Chẩn đoán, Kịch bản) vào khu vực trực
> quan ở cột giữa; cột phải dành trọn cho Agent"*

Kiểm lại `index.html`:

```
dòng 143   <aside class="sidebar-right" id="sidebarRight">
dòng 145   <div class="pane-tabs">  ->  4 tab VẪN Ở CỘT PHẢI
"agent" trong index.html            ->  0 lần
cây thư mục trong cột trái          ->  0 lần
```

Tôi đo `grid-template-columns` thấy `240px 1040px 0px` rồi kết luận bố cục đạt —
**mà không kiểm nội dung từng cột**. Đo cái khung, không đo cái nằm trong khung.
Lỗi nghiệm thu của tôi, không phải Antigravity khai gian ba mục kia.

---

## 1. Thẻ dài quá — 88% bề ngang bỏ trống

Đo trên app đang chạy, bài mẫu "Hàm cộng hai số":

```
vùng soạn thảo   1040px
thẻ def cong     rộng 820px, nội dung 106px
thẻ return       rộng 791px, nội dung  73px
thẻ print        rộng 820px, nội dung 112px
                 -> 88% bề ngang bị bỏ trống
```

Nguyên nhân ở CSS: `.card-block` có `display: flex` nhưng **không có ràng buộc
bề rộng**, nên nó kéo dài hết khung cha.

```
XIN: thẻ rộng theo NỘI DUNG (`width: fit-content` hoặc `align-self: flex-start`)
NGƯỠNG: trên bài mẫu, tổng bề rộng bỏ trống <= 20% (nay 88%)
```

## 2. Chưa có thẻ CHÚ THÍCH

Kho có 11 loại thẻ, **không có loại nào cho chú thích**:

```
gan · goi_ham · ham · in_ra · lap_khi · lap_moi · neu · nguoc_lai
pheptinh · ma_tho · tra_ve
```

Chú thích hiện chỉ tồn tại hai dạng: `duoi_dong` (bám đuôi một nút khác) và
`ma_tho` (dòng `#` đứng riêng thì rơi xuống mã thô). Cả hai đều **chìm**, trong
khi Sếp muốn nó **nổi lên**.

```
XIN: thêm loại thẻ `chu_thich`
     - dòng bắt đầu bằng `#` ở cấp câu lệnh -> thẻ chu_thich, màu riêng
     - `duoi_dong` vẫn giữ, nhưng hiện rõ chứ đừng ẩn
     - `the_cst` PHẢI giữ nguyên byte như cũ — đây chỉ là lớp trình bày

NGƯỠNG: mở core/dong_ho.py, số thẻ ma_tho GIẢM và số thẻ chu_thich > 0;
        cửa cứng 1 (lossless) vẫn khớp từng byte.
```

---

## 3. ĐIỀU LỚN NHẤT: "một tấm kính đặt trên quyển vở"

Nguyên văn Sếp:

> *"trực quan hóa mà tôi nói giống như đặt 1 tấm kính trên quyển vở vậy,
> chứ có phải như ảnh 2 đâu"*

### Đang làm gì

Mỗi dòng mã bị **đóng khung riêng**: viền, nền, đệm, bo góc. Cái khung là thứ
đập vào mắt trước; mã nằm **bên trong** khung. Tức là đã **sắp chữ lại** đoạn
mã thành một thứ khác.

Và người dùng thấy mã **hai lần**: một lần dạng thẻ ở giữa, một lần dạng văn
bản ở tab "Mã Python" bên phải.

### Ý Sếp

Quyển vở là **mã, để nguyên như mã**. Tấm kính đặt lên trên chỉ **thêm dấu**:
màu, nhóm, đường nối. Người ta vẫn **đọc trang vở**, không đọc tấm kính.

```
BÂY GIỜ                              Ý SẾP
┌────────────────────────────┐       │ def cong(a, b):
│ def cong ( a, b ) :        │       │     return a + b
└────────────────────────────┘       │
  ┌──────────────────────────┐       print(cong(5, 7))
  │ return a + b             │
  └──────────────────────────┘       ^ mã liền mạch, một dải màu bên trái
┌────────────────────────────┐         cho cả KHỐI, không cho từng dòng
│ print ( cong(5, 7) )       │
└────────────────────────────┘
```

### Cụ thể

```
1. Cột giữa hiện mã LIỀN MẠCH: phông đều, số dòng, giãn dòng tự nhiên.
   KHÔNG viền, KHÔNG nền, KHÔNG đệm cho từng dòng.

2. Tấm kính chỉ thêm:
      - một dải màu bên trái cho mỗi KHỐI (hàm, nếu, lặp) — không phải mỗi dòng
      - nền nhạt dần theo cấp lồng
      - đường nối cho cặp `nếu`/`ngược lại`
      - thanh nhịp neo vào khoảng dòng, không neo vào hộp

3. Bấm vào một dòng thì sửa TẠI CHỖ, không bung ra một hộp khác.

4. Bỏ tab "Mã Python" bên phải. Cột giữa ĐÃ LÀ mã rồi, không cần hiện hai lần.
```

### Vì sao đáng làm dù nó lớn

Cả tuần đo được: model **không** vướng ở chỗ "đây là lệnh gì" (25/28 khi cho
khay). Nó vướng ở **quãng giữa lúc chạy**. Người mới cũng vậy.

Đóng khung từng dòng là trả lời câu *"dòng này là loại gì"* — câu không ai hỏi.
Còn tấm kính giữ nguyên mã và **thêm cấu trúc lên trên** thì trả lời câu
*"những dòng này thuộc về nhau"* — câu có người hỏi.

---

## 4. Bố cục ba cột — làm nốt phần còn thiếu

```
TRÁI    cây thư mục  ⇅  khay thẻ    (đổi qua lại, 1 lần bấm)
                         endpoint /api/tep_tin ĐÃ CÓ, chỉ thiếu giao diện cây
GIỮA    mã liền mạch (tấm kính) ở trên
        terminal + Mạch Nước Ngầm + Chẩn đoán + Kịch Bản ở dưới, chia đôi kéo được
PHẢI    để trống cho Agent
```

---

## 5. Ngưỡng đặt trước

```
1. bề ngang bỏ trống trên bài mẫu   <= 20%      (nay 88%)
2. thẻ chu_thich                     > 0 trên core/dong_ho.py
   cửa cứng 1 lossless                vẫn khớp từng byte
3. mở core/web_search.py — 199 thẻ:
      số phần tử DOM có viền riêng cho TỪNG DÒNG  = 0
      số dải màu theo KHỐI                        > 0
4. cột phải: 0 tab về tệp; 4 tab nằm ở cột giữa
   cột trái: đổi được cây thư mục <-> khay thẻ bằng 1 lần bấm
5. 620 test vẫn xanh
```

Mục 3 là mục chấm được cái "tấm kính": nếu vẫn còn viền cho từng dòng thì chưa
phải kính, vẫn là hộp.

---

## 6. Xin gửi kế hoạch trước, đừng viết mã trước

`CLAUDE.md` §7. Đây là đổi cách vẽ toàn bộ vùng soạn thảo, không phải sửa một
lỗi. Và lần này tôi sẽ kiểm **nội dung từng cột**, không chỉ kiểm
`grid-template-columns` — đúng chỗ tôi vừa hụt.
