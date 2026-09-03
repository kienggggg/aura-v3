# Gửi Antigravity — việc tiếp: đo GIỚI HẠN của chính E1

*22/08/2026. Việc này ban đầu giao Codex, nhưng Codex hết token nên chuyển sang
Antigravity. Có một điều phải nói trước khi bắt đầu.*

---

## 0. Điều phải nói trước

Việc này **đo giới hạn của chính công cụ Antigravity vừa dựng**. `CLAUDE.md` §8:

> *"Worker không được tự chấm PASS: Runner chỉ sinh file; Verifier độc lập mới
> có quyền ghi trạng thái."*

Nên chia như cả tuần nay đã làm và nó chạy tốt:

```
Antigravity   dựng bộ đề ngoài họ + kịch bản chạy, SINH RA SỐ
Claude        đối chiếu độc lập, ghi trạng thái ĐẠT / KHÔNG ĐẠT
```

Tôi sẽ tự dựng lại bộ đề bằng seed để kiểm nó có đúng "ngoài họ" không, và tự
chấm `dung_nghia` bằng AST. Không đọc kết quả của Antigravity thay cho việc
chạy.

Nói thẳng vì sao tôi cẩn thận chỗ này: qua 7 vòng, **4 lần cửa gác của
Antigravity không thể trượt** (bộ đề toàn hàm dễ · ngưỡng 140/140 ·
`dong_kiem_tra=30` ngoài tệp · ca parity `x, y, z`). Đây là việc mà một bộ đề
"vô tình dễ" sẽ cho ra con số đẹp và sai.

---

## 1. Chỗ khép kín tôi tìm ra

`experiments/evidence_sprint/de_loi.json` có **29 lỗi**:

```
so sánh Lt          1        bỏ phủ định         8
logic Or            6        True/False          5
logic And           1        hằng số n -> n+1    8
```

Sinh bởi `DotBien` trong `dung_de_loi.py`, đúng **bốn bộ duyệt**:

```
visit_Compare · visit_BoolOp · visit_UnaryOp · visit_Constant
```

Còn `_Lat` trong `core/lat_nguoc.py` lật ngược **đúng bốn họ ấy**.

**Nên "E1 giải 3/4 đề lỗi đơn" đo trên bộ đề chỉ chứa lỗi mà E1 được thiết kế
để lật.** Con số đúng, nhưng nó không nói gì về lỗi thật.

Điều này không làm E1 mất giá trị — bốn họ ấy đúng là lỗi kinh điển của người
mới. Nhưng **chưa ai đo E1 trên lỗi NGOÀI họ**, mà nút "TÌM LỖI NHÂN QUẢ" sắp
ra mắt cho người dùng thật. Người mới bấm nút đó sẽ tin kết quả.

```
E1 giải 3/4   trên bộ đề do CHÍNH họ phép của E1 sinh ra
E1 giải ?/?   trên lỗi ngoài họ            <- CHƯA AI BIẾT
```

Ô thứ hai trống mà nút đã sắp ra mắt. Đó là lý do việc này đứng trước mọi việc
mở rộng tính năng.

---

## 2. Việc

```
[NEW] experiments/evidence_sprint/dung_de_ngoai_ho.py
      DotBienNgoai — các họ mà _Lat KHÔNG lật được:
         BinOp          a + b     ->  a - b
         đổi biến       x         ->  y          (cùng phạm vi, cùng kiểu)
         bỏ return      return x  ->  x
         đổi thứ tự     f(a, b)   ->  f(b, a)
         đổi chỉ số     a[i]      ->  a[i + 1]
      Gieo vào ĐÚNG 4 tệp của de_loi.json, mỗi họ vài ca.

[NEW] experiments/evidence_sprint/do_e1_ngoai_ho.py
      Gọi core.lat_nguoc.chay_e1_dinh_vi trên bộ đề mới.
      Sổ ra data/evidence_sprint/e1_ngoai_ho.json — GIỮ sổ cũ, đừng ghi đè.
```

### Bắt buộc: chứng minh bộ đề THẬT SỰ ngoài họ

Trước khi đo E1, phải chạy khâu này và in kết quả:

```python
from core.lat_nguoc import tao_cac_ung_vien
# voi moi de: bo goc `chuan`, ban dot bien `ma`
uv = tao_cac_ung_vien(ma)             # khong loc
assert not any(mm == chuan for _, _, mm in uv), "de nay VAN NAM TRONG ho"
```

Nếu một phép lật của `_Lat` khôi phục được bản gốc thì đề đó **vẫn trong họ**,
phải loại khỏi bộ. Không có khâu này thì cả phép đo vô nghĩa — và đây chính là
chỗ một bộ đề "vô tình dễ" sẽ lọt.

---

## 3. Ngưỡng đặt trước — nhánh đáng sợ KHÔNG phải nhánh thấp

```
E1 giải được trên lỗi NGOÀI họ:

  = 0/N    ĐÚNG NHƯ THIẾT KẾ. In con số ấy lên giao diện:
           "Chỉ dò được 5 họ. Đã thử N lỗi ngoài họ, không dò ra ca nào."

  > 0/N    PHẢI MỞ RA XEM TỪNG CA.
           E1 làm test xanh trên một lỗi nó không hiểu = vá đè lên triệu chứng.
           Với mỗi ca, đối chiếu AST bản vá với bản gốc:
              KHỚP  -> may mắn, ghi lại
              LỆCH  -> LỖI NẶNG. App sẽ đề nghị người dùng một bản vá SAI mà
                       test xanh. BÁO NGAY, đừng chờ hết bộ.
```

Nhánh `> 0` mới nguy hiểm, không phải nhánh `= 0`.

### Cách chấm — bắt buộc

```python
dung_nghia = ast.dump(ast.parse(ban_va)) == ast.dump(ast.parse(ban_goc))
```

**Không chấm bằng "test có xanh không".** Cả tuần này đo được: nền `2/9 xanh`
nhưng `0/9 đúng nghĩa`. Xanh là điều kiện cần, không phải điều kiện đủ.

---

## 4. Bốn bẫy đã biết — ba trong số đó tôi tự vấp hôm nay

```
a) dot_bien() trả mã đã qua ast.unparse -> SỐ DÒNG KHÁC HẲN tệp gốc.
   Tính dòng TỪ MÃ ĐÃ ĐỘT BIẾN. (Antigravity đã vấp: đặt dòng 30 cho tệp
   26 dòng, dòng thật là 23.)

b) Đừng chấm bằng dò chuỗi. Tôi mắc lỗi này BA lần trong một phiên hôm nay:
   đếm hàm mất "-> ..." bằng chuỗi ra 29, AST cho 0. So bằng AST.

c) Gieo lỗi xong phải kiểm test ĐỎ ỔN ĐỊNH (chạy hai lần). Lỗi gieo mà test
   vẫn xanh thì đề đó vô nghĩa. E1 đã có sẵn khâu này, chép lại.

d) MỘT PHÉP LẬT CÓ THỂ LÀM TEST TREO. Tôi vấp thật hôm nay:
      subprocess.TimeoutExpired: pytest tests/test_web_search.py
      timed out after 180 seconds
   `core/lat_nguoc.py` đã bắt TimeoutExpired ở ba chỗ (dòng 215, 307, 533) nên
   app không việc gì — nhưng kịch bản đo mới phải bắt lại. Treo = TRƯỢT, không
   phải sự cố.
```

---

## 5. Một chỗ nhỏ, ghi ra chứ không giao

`core/lat_nguoc.py` **tự dựng bộ truy vết riêng**, không dùng `TraceResult` của
`core/trace_runtime.py` (kế hoạch có ghi thêm `dong_da_chay` vào `TraceResult`
nhưng chưa làm). Nên kho đang có **hai bộ truy vết**; người dùng bấm cả hai nút
thì chạy hai lần. Không gấp, gộp lúc rảnh.
