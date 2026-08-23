# Nghiệm thu — hiện ứng viên bị loại & giới hạn đọc động

*23/08/2026. Chạy lại bằng venv của kho, và thử chỗ đáng ngờ nhất bằng cách
ĐỔI SỔ xem con số có đổi theo không.*

---

## 1. Mọi lời khai — đúng cả

```
toàn kho                    620 passed, 1 skipped   (trước: 618)
node --test test_e1_ui.js   6 pass, 0 fail
/api/status                 trả e1_limitation, đọc sống từ sổ
app.js nhánh bị loại        KHÔNG sinh nút "Áp dụng"  (0 chỗ)
HTML/JS                     KHÔNG chép cứng số 64
```

## 2. "Đọc động" — thử bằng cách ĐỔI SỔ

Lời hứa *"không chép cứng, chạy lại ra số khác thì màn hình đổi theo"* chỉ kiểm
được bằng một cách: đưa cho nó một sổ khác.

```
sổ thật, 64 đề    ->  "Đã thử 64 lỗi NGOÀI 5 họ đó — không dò ra ca nào."
sổ giả,   7 đề    ->  "Đã thử 7 lỗi NGOÀI 5 họ đó — không dò ra ca nào."
KHÔNG có sổ       ->  "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có
                       nghĩa là mã không có lỗi."
```

Nhánh thứ ba là chỗ họ làm **hơn** yêu cầu: mất sổ thì không bịa số, mà lùi về
câu dè dặt. Đó đúng luật §7 mục 3 — kiểm không được thì đừng viết như đã kiểm.

## 3. Nút "Áp dụng" — khẳng định thật, không phải tên test suông

```js
const allButtons = container.querySelectorAll('button');
assert.strictEqual(allButtons.length, 0,
    'Tuyệt đối không có nút bấm Áp dụng cho ứng viên bị loại');
```

Không phải `assert.ok(true)` đội lốt. Và test **tự cấp** chuỗi `limitation`
trong đầu vào, nên nó kiểm **bộ dựng giao diện** chứ không phụ thuộc sổ trên
đĩa — đúng thiết kế, không giòn.

Bộ test còn khẳng định badge ghi rõ `Suite: ĐỎ (4 test khác hỏng)`, tức là
người dùng thấy **số test bị hỏng**, không chỉ thấy chữ "đỏ".

## 4. Bốn mốc E1 sau khi sửa — không xê dịch

```
may_tinh.py      65 -> 15   tim_thay          9,4s
web_search.py    87 -> 28   tim_thay         21,3s
dong_ho.py        1 ->  1   tim_thay          5,1s
loai_cau_hoi.py  10 ->  2   khong_tim_thay   18,7s
```

Ngưỡng tôi đặt từ vòng gộp tracer: **con số lọc không được đổi**. Giữ nguyên.
Và `loai_cau_hoi` vẫn TRƯỢT đúng như sổ E1 ghi — bản mới không "chữa" nó bằng
cách nới tay.

## 5. Việc còn mở: KHÔNG CÒN

```
84 lỗi đỏ giả                    XONG
sập khởi động console            XONG
bố cục 3 cột · thẻ một dòng      XONG
sinh_ma_python vỡ 20/22          XONG
mất chú kiểu 136/198             XONG
/api/trace chạy mã khi khai TẮT  XONG
E1 nối vào app, có cửa           XONG
"ma" trong candidates            XONG
tep_test tự suy + whitelist      XONG
gộp hai bộ truy vết              XONG
tiến trình đa chặng              XONG
hiện ứng viên bị loại            XONG
giới hạn ngoài họ đọc động       XONG
```

Không còn mục nào tôi đang giữ.

---

## 6. Điều đáng ghi lại của cả chặng này

Con số cuối cùng của app không phải `620 passed`. Là câu này, và nó đến từ một
phép đo chứ không từ một lời hứa:

> *"Chỉ dò được 5 họ lỗi so sánh/logic.
>  Đã thử 64 lỗi NGOÀI 5 họ đó — không dò ra ca nào."*

Và thứ đứng cạnh nó, cũng từ đo mà ra:

> *"Sửa một chỗ mà hỏng chỗ khác thì không phải sửa."*

Câu thứ hai sinh ra vì phép đo bắt gặp **10 ca** E1 tìm được phép lật làm test
đích xanh mà làm đỏ chỗ khác. Nếu không đo ngoài họ thì 10 ca ấy vẫn nằm im
dưới nhãn "không tìm thấy", và bài học đắt nhất của cả tuần — **xanh không phải
đúng** — sẽ không bao giờ tới được người học.
