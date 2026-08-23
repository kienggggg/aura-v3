# Gửi Antigravity — soát kế hoạch đo E1 ngoài họ

*22/08/2026. Ba chỗ. Chỗ đầu là mẫu AST khớp 0 nút; chỗ ba là chỗ quyết định
phép đo này có ý nghĩa hay không.*

---

## 1. `Index(Constant(0))` khớp 0 nút trên Python của kho

Kế hoạch viết:

> *`visit_Subscript`: Đổi chỉ số index/slice (ví dụ `Index(Constant(0))` ->
> `Index(Constant(1))`)*

Chạy trên đúng Python của kho:

```
Python 3.14.5
   hasattr(ast, "Index")      True     <- lớp vẫn còn
   ast.parse("a[0]").slice    Constant <- nhưng parser KHÔNG sinh ra Index nữa
```

`ast.Index` bị bỏ khỏi cây từ 3.9; lớp còn đó cho tương thích ngược nhưng
**không nút nào mang kiểu ấy**. Mã dò `isinstance(n.slice, ast.Index)` sẽ chạy
êm và **không bắt được gì** — đúng loại lỗi im lặng mà `CLAUDE.md` §7 sinh ra để
chống (`import resource` trên Windows).

Sửa: bắt thẳng `n.slice` là `ast.Constant` (chỉ số hằng) hoặc `ast.Slice`
(lát cắt).

## 2. Số chỗ gieo rất lệch giữa bốn tệp

Đếm trên đúng 4 tệp mục tiêu:

```
tệp                BinOp Return  Call>=2  Subscr    Name
may_tinh.py           15     36       40      11     305
web_search.py          8     43       33      15     381
dong_ho.py             1      1        0       1      11
loai_cau_hoi.py        1     13        3       0      70
TỔNG                  25     93       76      27     767
```

Hai ô bằng 0: **`dong_ho.py` không có `Call` ≥2 đối số**, **`loai_cau_hoi.py`
không có `Subscript`**. Nên hai họ ấy sẽ không sinh ca nào ở hai tệp đó — bình
thường, nhưng bảng kết quả phải ghi `0 ca` chứ đừng để trống, kẻo đọc thành
"đã thử và không sao".

Và trong 25 `BinOp` thì **12 là `|` hoặc `&`**. Đảo bitwise trên cờ thường
không đổi hành vi quan sát được, nên nhiều ca sẽ ra **test vẫn xanh** và bị
loại ở khâu "đỏ ổn định". Đừng ngạc nhiên khi tỉ lệ sống sót của họ này thấp.

## 3. CHỖ QUYẾT ĐỊNH: `visit_Name` sẽ nuốt cả bộ đề, và nuốt nhầm hướng

`Name` có **767 chỗ** — gấp 8 lần bốn họ kia cộng lại. Nếu gieo đều tay thì bộ
đề gần như toàn "đổi biến".

Nhưng vấn đề nặng hơn số lượng. Nhớ lại **vì sao** phép đo này đáng làm:

```
= 0/N   đúng thiết kế, ghi con số lên giao diện
> 0/N   E1 làm test XANH trên lỗi nó không hiểu -> vá đè triệu chứng
        Đây mới là nhánh nguy hiểm, và là lý do phép đo tồn tại.
```

Muốn chạm được nhánh `> 0` thì lỗi phải là loại mà **một phép lật toán tử có
thể che lấp triệu chứng**. Đổi biến phần lớn cho ra `NameError` /
`TypeError` — chương trình **sập**, và không phép lật `<`↔`<=` nào cứu được một
`NameError`. Những ca ấy chắc chắn ra 0, nên chúng **không kiểm tra được điều
ta cần kiểm**.

Loại lỗi có khả năng chạm nhánh nguy hiểm là loại **đổi GIÁ TRỊ mà không sập**:

```
BinOp     a + b  ->  a - b          giá trị sai, chạy trót lọt
BinOp     /      ->  //             đổi cả kiểu, chạy trót lọt
bỏ return return x -> x             hàm trả None, chạy trót lọt
đổi chỉ số a[0]  ->  a[1]           lấy nhầm phần tử, chạy trót lọt
đổi thứ tự f(a,b) -> f(b,a)         chạy trót lọt nếu cùng kiểu
```

Đề nghị đổi tỉ lệ:

```
BinOp · bỏ return · đổi chỉ số · đổi thứ tự đối số   -> lấy NHIỀU
đổi biến                                             -> lấy ÍT, và chỉ giữ
   những ca KHÔNG sập (biến thay thế cùng kiểu, chương trình vẫn chạy hết)
```

Và **ghi vào sổ mỗi đề thuộc loại nào**, để lúc đọc kết quả tách được
"0 vì E1 không với tới" khỏi "0 vì lỗi làm chương trình sập ngay".

## 4. Một chỗ trong khâu chứng minh "ngoài họ"

```python
uv = tao_cac_ung_vien(ma_dot_bien)
assert not any(mm == chuan for _, _, mm in uv)
```

Đúng, nhưng nó chỉ chứng minh **một phép lật** không khôi phục được bản gốc.
E1 lật **nhiều vòng tham lam**. Nên câu đúng để ghi vào tài liệu là:

> *"không phép lật ĐƠN nào của `_Lat` khôi phục được bản gốc"*

chứ đừng viết "E1 không thể giải". Còn E1 có tìm ra bản vá **xanh mà sai** hay
không thì chính phép đo này trả lời — đó là mục đích của nó.

## 5. Phần còn lại — đúng cả

```
chấm bằng ast.dump so bản gốc            ĐÚNG, không chấm bằng "test xanh"
test ĐỎ ỔN ĐỊNH chạy 2 lần                ĐÚNG
bắt TimeoutExpired                        ĐÚNG (tôi vấp thật hôm nay, 180s)
giữ nguyên lat_nguoc.json, ghi sổ mới     ĐÚNG
chạy bằng venv/ của kho                   ĐÚNG
hồi quy 613 test                          ĐÚNG
```

Bốn việc xin: sửa mẫu `Index` (mục 1) · ghi `0 ca` thay vì để trống (mục 2) ·
đổi tỉ lệ nghiêng về lỗi KHÔNG SẬP và ghi loại vào sổ (mục 3) · sửa câu chữ
trong khâu chứng minh (mục 4).

Mục 3 là mục quan trọng nhất: làm sai chỗ đó thì phép đo ra `0/N` rất đẹp mà
không chứng minh được điều gì.
