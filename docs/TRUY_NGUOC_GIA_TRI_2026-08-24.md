# Truy ngược giá trị trên 64 đề ngoài họ — 24/08/2026

*Phép đo mà sổ 20/08 gọi là "đáng làm nhất, và không cần model". Đã làm. Cửa
đặt trước trả về **mã thoát 1 — đo được mà KHÔNG đạt**. Con số đáng giá nhất
không phải tỷ lệ trúng, mà là số ca nó chỉ sai một cách rất tự tin.*

---

## 1. Vì sao làm

```
E1 trong họ (5 phép so sánh/logic)     3/9
E1 NGOÀI họ                            0/64
   đổi biến   24 đề   \
   bỏ return  19 đề    >  43/64 = 67% là lỗi CẤU TRÚC
   đổi thứ tự 15 đề   /
   binop       6 đề
```

E1 liệt kê mọi phép lật rồi thử từng cái. Với `doi_bien` thì số ứng viên nổ
theo bình phương số biến trong tầm — không co giãn tới đó. Truy ngược đi hướng
khác: **không đề xuất bản vá nào**, chỉ thu hẹp từ "mọi dòng đã chạy" xuống
"những dòng thật sự sinh ra con số sai".

**Hai thước đo khác nhau, nói trước:** E1 trả lời *"vá thế này"*; truy ngược
trả lời *"nhìn mấy dòng này"*. Cột "vá đúng" của truy ngược **vĩnh viễn là 0**
vì nó không vá.

---

## 2. Cửa đặt trước — mã thoát 1

```
1. dòng lỗi trong chuỗi        32/64    >= 32      ĐẠT
2. dài chuỗi, trung vị            2     <= 8       ĐẠT
3. chuỗi rỗng mà vẫn báo         15     = 0        TRƯỢT
4. thu hẹp, trung vị           0,20     <= 0,50    ĐẠT
5. model_calls                    0     = 0        ĐẠT
```

Bốn trên năm. Nhưng cửa 3 là cửa gác đúng chỗ, và nó đỏ.

---

## 3. Con số thật — bổ đôi theo chiều dài chuỗi

```
chuỗi ĐÚNG 1 dòng, TRÚNG   15
chuỗi ĐÚNG 1 dòng, TRƯỢT   22   <- chỉ một dòng, và chỉ SAI
chuỗi  >1 dòng, TRÚNG      17
chuỗi  >1 dòng, TRƯỢT       9
```

**22/63 ca nó chỉ đúng một dòng, rất dứt khoát, và sai.** Trong 37 ca trả lời
một dòng thì chỉ 15 đúng — **41%**, tức tệ hơn tung đồng xu, mà lại trông chắc
chắn hơn hẳn. Với người mới học code thì một câu trả lời sai mà dứt khoát còn
tệ hơn không trả lời.

Ngược lại, khi nó **thật sự lùi được nhiều bước** thì khá:

```
chuỗi > 1 dòng    17 đúng / 26 ca = 65%
```

---

## 4. Vì sao chuỗi hay sập còn đúng một dòng

Trên lỗi làm chương trình **chết**, mốc bắt đầu là chỗ chết. Tên mà dòng ấy đọc
thường là biến chưa hề được gán (`a` trong `_bo_dau`), nên không có ai ghi để
lùi tiếp — chuỗi dừng ngay tại đó.

Nghĩa là: **trên lỗi gây chết, truy ngược không hơn gì cái traceback Python in
sẵn.** 15 ca "trúng bằng chuỗi một dòng" là 15 ca traceback đã chỉ đúng chỗ,
miễn phí. Đem chúng tính vào tỷ lệ trúng là tự cộng điểm cho việc mình không
làm.

Trừ 15 ca ấy ra, phần truy ngược **thật sự đóng góp** là **17/63**, không phải
32/63.

---

## 5. Theo họ lỗi

```
họ            tổng   trúng    chuỗi=1   chuỗi>1
doi_bien       24    22/24      15         7
doi_thu_tu     14     5/14       0         5
binop           6     2/6        0         2
bo_return      19     3/19       0         3
TỔNG           63    32/63      15        17
```

`bo_return` **3/19** — đúng như đoán trước khi chạy: bỏ `return` thì hàm trả
`None` một cách **hợp lệ**, không có cú chết nào để bám, và giá trị vẫn chảy
bình thường qua chỗ hỏng.

`doi_bien` 22/24 nhìn đẹp, nhưng 15 trong đó là ca traceback cho không.

```
                tổng    trúng
co_ve_sap=True    17    12/17
co_ve_sap=False   46    20/46
```

---

## 6. Thu hẹp và tốc độ — chỗ duy nhất đạt rõ

```
dòng đã chạy      trung vị 11   (ít nhất 1, nhiều nhất 57)
dòng trong chuỗi  trung vị  1   (ít nhất 1, nhiều nhất  7)
thu hẹp           trung vị 0,20
thời gian         trung vị 7,3 giây/đề
model_calls       0
```

Thu hẹp thật, nhanh thật, không gọi model lần nào. Nhưng thu hẹp mà chỉ sai thì
không dùng được — xem mục 3.

Một ca **KHÔNG ĐO ĐƯỢC**: `core/web_search.py` đề #44, không test đỏ nào trace
được.

---

## 7. Ba lỗi trong CHÍNH MÁY ĐO, sửa trước khi có con số nào

### 7.1 Bộ đề dùng `ast.unparse` — bệnh hôm qua, chỗ khác

```
core/may_tinh.py           321 dòng
`ma` trong de_ngoai_ho     194 dòng   (rụng hết chú thích)
trường `dong`               39        <- đếm theo TỆP GỐC
chỗ đổi thật trong `ma`     25        <- cùng câu lệnh, khác hệ toạ độ
```

Chấm bằng số 39 trên tệp 194 dòng thì mọi con số là rác — **mà bảng vẫn ra rất
gọn**. Nay tính lại bằng cách so `ast.unparse(gốc)` với `ma`.

### 7.2 Suýt để bộ chọn test nhìn trộm đáp án

`chot_test_can_trace` có tham số `dong_kiem_tra`: truyền dòng lỗi vào là nó ưu
tiên test đi qua đúng chỗ ấy. Đã để `None`, và đăng ký luật chọn không lộ:
*trong các test đỏ, chọn test chạy qua nhiều dòng nhất của tệp đích*.

### 7.3 `tra_ve` không chỉ phát khi hàm trả về

`sys.settrace` phát `return` **cả khi hàm ném lỗi ra ngoài** — mỗi tầng ngăn
xếp gỡ ra là một `tra_ve` với `arg = None`:

```
buoc=9   dong=25   <tra_ve>=None   tach = unicodedata.normalize('NFD', (a or ''))
buoc=11  dong=175  <tra_ve>=None   khong_dau = _bo_dau(goc)
```

Bản đầu lấy `tra_ve` **cuối cùng** nên luôn dừng ở tầng ngoài, không bao giờ
chạm chỗ hỏng. Sửa hai vòng mới đúng:

```
vòng 1   luật "dòng không phải `return`"
         -> trượt ngay đề #2, vì chỗ hỏng nằm ĐÚNG TRÊN một dòng `return`
vòng 2   nhìn SỰ KIỆN CUỐI CÙNG của cả vết
         -> dòng 175 không phải return  =>  cả đuôi ấy là một lượt gỡ
         -> lấy tầng sâu nhất
```

Sau vòng 2: 6 đề đầu từ 0/6 lên 5/6.

---

## 8. Cửa 3 đặt sai chữ nhưng gác đúng chỗ

Cửa 3 viết là *"chuỗi RỖNG mà vẫn báo tìm thấy"*. Đọc kỹ thì nó phạt cả câu trả
lời **lý tưởng** — một dòng, đúng dòng. Chữ đặt sai.

Nhưng nó vẫn đỏ đúng lúc cần đỏ, vì 15 ca ấy chính là 15 ca **traceback cho
không**. Cửa bắt đúng thứ cần bắt, dù vì lý do khác với lý do tôi viết ra.

**Không sửa lại chữ rồi tuyên bố ĐẠT.** Số đã đăng ký trước là 0, thực tế là
15, nên cửa TRƯỢT và mã thoát là 1. Nới ngưỡng sau khi thấy kết quả là đúng
động tác mà cả tệp `CLAUDE.md` sinh ra để chống.

---

## 9. Kết luận, và bước tiếp

**Phương pháp như đang có: KHÔNG DÙNG ĐƯỢC.** Không phải vì trúng ít, mà vì
**22 ca chỉ sai một dòng một cách dứt khoát**.

Có một hướng sửa rẻ và đo được ngay: **im lặng khi không lùi được bước nào.**
Chuỗi chỉ có một dòng thì đừng trả lời, hãy nói "không biết". Số hiện có cho
biết trước điều gì sẽ xảy ra:

```
                      nay        nếu chỉ trả lời khi chuỗi > 1 dòng
trả lời               63/63      26/63  (41% số ca)
trong đó đúng         32         17
trong đó SAI          31          9
tỷ lệ đúng khi nói    51%        65%
chỉ sai một dòng      22          0
```

Đổi 22 câu trả lời sai lấy 22 câu "không biết". Đúng luật *"tra không thấy thì
nói tôi không tìm thấy"*.

Nhưng đó là **suy từ số cũ, chưa phải phép đo**. Muốn kết luận thì phải đăng ký
ngưỡng mới rồi chạy lại — không được lấy chính bộ 64 này ra làm bằng chứng cho
một luật rút ra từ chính nó.

```
XIN Ý KIẾN SẾP — ba hướng:

a) Cài luật im lặng, đăng ký ngưỡng mới, chạy lại trên 64 đề.
   Rẻ nhất: ~10 phút chạy. Nhưng phải nói rõ nó không còn là phép đo
   độc lập nữa, vì luật rút ra từ chính bộ đề này.

b) Sinh bộ đề THỨ HAI (64 đề mới, hạt giống khác) rồi mới chấm luật im
   lặng trên đó. Đắt hơn, nhưng là bằng chứng thật.

c) Dừng hướng này. `bo_return` 3/19 và `doi_thu_tu` 5/14 cho thấy truy
   ngược giá trị không với tới hai họ ấy, mà chúng chiếm 33/64.
```

Tôi nghiêng về **(b)**. (a) sẽ ra một con số đẹp mà không chứng minh được gì —
đúng loại số mà mục 7 và 8 của tệp này vừa mất một buổi để dọn.
