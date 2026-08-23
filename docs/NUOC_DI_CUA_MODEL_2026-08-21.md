# Model nghĩ gì khi nó sửa sai — đo bằng nước đi, không hỏi

*21/08/2026. Câu của Sếp: "phải đo xem model nghĩ gì thì mới biết chỗ sửa được,
giống người mới học code — phải biết họ nghĩ gì mới giải quyết triệt để."*

---

## 1. Cái bẫy phải né trước

Hỏi model *"vì sao mày làm thế"* thì nó **kể một câu chuyện**, không đưa nguyên
nhân. Đã bắt được đúng ca ấy hôm 20/08: model sửa `now or ...` thành
`now if now else ...`, nêu một lý lẽ **sai hẳn**, mà test vẫn xanh.

Nên phép đo này không hỏi. Nó đọc **nước đi đã đánh** trong sổ E2 và xếp loại
bằng máy.

```
venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\soi_nuoc_di.py
```

---

## 2. Bảng cả ngày, sau khi mọi phép đo đã sạch

```
                              xanh   đúng nghĩa   bán kính phá
nền   vá hàm đã hỏng           2/9      0/9           22x
C     đổi một ô thẻ            1/9      1/9            1x
C2    đổi ô + ép khuôn         0/9        —            1x
C3    đổi ô enum               0/9        —            1x
E3    viết lại hàm có khay     0/9      0/9           22x
E2    điền chỗ trống           1/9      0/9            1x
```

Không cách trình bày nào lay chuyển được. **Cột đáng chấm cao nhất là 1/9.**

---

## 3. NƯỚC ĐI — 57 lần điền của E2

```
nước đi                    lần      %
chép dòng có sẵn            34    60%
sai kiểu câu lệnh           16    28%
đúng kiểu, sai nội dung      6    11%
giữ nguyên đột biến          1     2%
```

### "Chép dòng có sẵn" là chép THẬT, đã kiểm

Một dòng trùng có thể chỉ là câu quen tay. Nên đo khoảng cách từ dòng bị chép
tới ô trống:

```
trung vị        3 dòng
cách 1 dòng    12 lần   <- chép đúng dòng NGAY CẠNH
<=3 dòng       22/34
>15 dòng        7/34    <- xa, có thể chỉ trùng; không tính là chép
```

Đếm dè: **27/34 nằm trong 8 dòng.**

### Bốn cách hiểu sai, mỗi cách một kiểu

```
chép dòng bên cạnh    không hiểu ô trống là chỗ RIÊNG — tưởng là chép lại
sai kiểu câu lệnh     không thấy dòng DƯỚI đang phụ thuộc dòng này mở khối
                      (điền `raise ...` vào chỗ đáng lẽ là `if ...:`)
giữ nguyên đột biến   đọc mà không đối chiếu — đề nghị đúng cái đang sai
đúng kiểu sai nội dung viết đúng KHUÔN `return SearchResult(...)`, sai giá trị
```

Ba cách đầu là **lỗi cấu trúc**. Cách thứ tư mới là lỗi hiểu chương trình.

---

## 4. Chỗ này là ĐO, chỗ kia là SUY — không trộn

**Đo được:** bảng ở mục 3. Máy đếm, chạy lại ra y hệt.

**Suy, chưa đo:** rằng giao diện chặn được ba loại đầu (89%). Đó là **phán đoán
của người**, và có lý do cụ thể để không tin sẵn:

> C2 ép khuôn JSON Schema, C3 ép enum — đúng kiểu "chặn bằng ràng buộc" — và cả
> hai ra **0/9**.

Khác biệt: C2/C3 ép **giá trị** của một toán tử. Ba loại lỗi ở đây là về **thứ
gì được phép nằm trong ô**. Hai chuyện khác nhau, nên C2/C3 không bác được suy
đoán này — nhưng cũng không chứng minh được nó.

---

## 5. Phép đo tiếp theo, viết ngưỡng trước

Chặn đúng ba thứ, đo lại trên chính 9 đề ấy:

```
1. cấm điền một dòng đã có nguyên văn trong mã đang xem
2. khoá KIỂU câu lệnh của ô trống (máy biết: đáp án là If thì chỉ nhận If)
3. cấm điền lại chính dòng đang đỏ
```

Cả ba máy đều tự kiểm được, **không cần model hợp tác**.

```
NGƯỠNG ĐẶT TRƯỚC
  >=4/9 đúng nghĩa  -> chặn cấu trúc là đòn bẩy thật, dựng vào app
  2-3/9             -> có tác dụng, chưa đủ để đổi thiết kế
  <=1/9             -> lỗi cấu trúc chỉ là VỎ; bức tường vẫn là hiểu lúc chạy,
                       và ba loại đầu chỉ là cách model lấp chỗ khi nó bí
```

Nhánh cuối là nhánh đáng sợ nhất và cũng dễ xảy ra nhất: model chép dòng bên
cạnh **vì nó không biết điền gì**, chứ không phải vì nó tưởng phải chép. Chặn
đường chép thì nó đổi sang bịa. Nếu vậy thì 60% kia không phải bệnh — chỉ là
triệu chứng.
