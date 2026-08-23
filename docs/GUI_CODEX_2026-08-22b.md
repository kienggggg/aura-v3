# Gửi Codex — RÚT việc cũ, giao việc mới

*22/08/2026. Hai phần: (1) rút lại việc giao sáng nay vì Antigravity đã làm
mất rồi, (2) việc mới — và nó xuất phát từ một chỗ khép kín tôi vừa tìm ra.*

---

## 1. RÚT việc giao sáng nay — Antigravity đã làm

Bản `docs/GUI_CODEX_2026-08-22.md` giao Codex ba việc trên
`experiments/evidence_sprint/do_lat_nguoc.py`:

```
1. _Lat ghi lineno cho từng chỗ
2. lọc theo dòng đã chạy
3. báo số trước/sau
```

Cả ba **đã xong**, nhưng ở chỗ khác: Antigravity tách hẳn thành
`core/lat_nguoc.py` (mã sản phẩm, không còn là mã thí nghiệm):

```
core/lat_nguoc.py:59    self.danh_sach.append((d, int(getattr(nut, "lineno", 0) or 0), ten))
core/lat_nguoc.py:109   def tao_cac_ung_vien(ma, dong_da_chay=None)
```

Số lọc đo được thật: `65→15` · `87→28` · `1→1` · `10→2`, và **chỗ đúng vẫn còn
trong tập sau lọc** trên cả ba đề giải được. Tôi đã đối chiếu độc lập.

**Xin Codex đừng làm việc đó nữa.** Lỗi ở khâu chuyển tin, thuộc về tôi.

Một chỗ nhỏ còn hở, ghi ra để biết chứ không giao: `core/lat_nguoc.py` **tự
dựng bộ truy vết riêng**, không dùng `TraceResult` của `core/trace_runtime.py`.
Nên kho đang có **hai bộ truy vết**; người dùng bấm cả hai nút thì chạy hai
lần. Việc gộp thuộc `core/`, mà Antigravity đang cầm.

---

## 2. VIỆC MỚI: bộ đề của E1 là một VÒNG KHÉP KÍN — đo hộ tôi cái đó

### Chỗ khép kín

`experiments/evidence_sprint/de_loi.json` có **29 lỗi**. Phân bố theo mô tả:

```
so sánh Lt          1        bỏ phủ định         8
logic Or            6        True/False          5
logic And           1        hằng số n -> n+1    8
```

Sinh ra bởi `DotBien` trong `dung_de_loi.py`, đúng **bốn bộ duyệt**:

```
visit_Compare · visit_BoolOp · visit_UnaryOp · visit_Constant
```

Còn `_Lat` trong `core/lat_nguoc.py` lật ngược đúng **bốn họ ấy**.

**Nên "E1 giải 3/4 đề lỗi đơn" đo trên một bộ đề chỉ chứa những lỗi E1 được
thiết kế để lật.** Con số ấy đúng, nhưng nó không nói gì về lỗi thật.

Điều này không làm E1 mất giá trị — năm họ ấy đúng là năm lỗi kinh điển của
người mới. Nhưng **chưa ai đo E1 trên lỗi NGOÀI họ của nó**, và app đang sắp
đưa nút "TÌM LỖI" ra cho người dùng thật.

### Việc

Dựng bộ đề **ngoài họ**, đo E1 trên đó.

```
[NEW] experiments/evidence_sprint/dung_de_ngoai_ho.py
      DotBienNgoai — các họ mà _Lat KHÔNG lật được:
         BinOp        a + b   ->  a - b        (Compare khác BinOp)
         doi bien     x       ->  y            (cùng phạm vi)
         bo return    return x  ->  x
         doi thu tu   f(a, b) ->  f(b, a)
         doi chi so   a[i]    ->  a[i + 1]
      Đủ 4-5 họ, mỗi họ vài ca, gieo vào cùng 4 tệp của de_loi.json.

[NEW] experiments/evidence_sprint/do_e1_ngoai_ho.py
      Gọi core.lat_nguoc.chay_e1_dinh_vi trên bộ đề mới.
```

### Ngưỡng đặt trước — và nhánh đáng sợ nhất không phải nhánh thấp

```
E1 giải được trên lỗi NGOÀI họ:

  = 0/N      ĐÚNG NHƯ THIẾT KẾ. Ghi con số ấy vào giao diện: "chỉ dò được
             5 họ; N lỗi ngoài họ thử qua đều KHÔNG dò ra."

  > 0/N      PHẢI MỞ RA XEM TỪNG CA. E1 làm test xanh trên một lỗi nó không
             hiểu nghĩa là nó tình cờ vá đè lên triệu chứng.
             Đó là "XANH nhưng SAI" — đúng cái bẫy cả tuần này đo được.
             Với mỗi ca như vậy, đối chiếu AST bản vá với bản gốc.
             KHỚP  -> may mắn, ghi lại
             LỆCH  -> LỖI NẶNG: app sẽ đề nghị người dùng một bản vá SAI
                      mà test xanh. Phải báo ngay, không chờ hết bộ.
```

Nhánh `> 0` mới là nhánh nguy hiểm, không phải nhánh `= 0`.

### Cách chấm — bắt buộc

```
dung_nghia = ast.dump(ast.parse(ban_va)) == ast.dump(ast.parse(ban_goc))
```

**Không chấm bằng "test có xanh không".** Cả tuần này đo được: nền `2/9 xanh`
nhưng `0/9 đúng nghĩa`. Xanh là điều kiện cần, không phải điều kiện đủ.

### Bẫy đã biết

```
a) dot_bien() trả mã đã qua ast.unparse -> SỐ DÒNG KHÁC HẲN tệp gốc.
   Tính dòng TỪ MÃ ĐÃ ĐỘT BIẾN. Antigravity đã vấp: đặt dòng 30 cho tệp
   26 dòng, dòng thật là 23.
b) Đừng chấm bằng dò chuỗi. Hôm nay tôi mắc lỗi này ba lần trong một phiên.
   So bằng AST.
c) Gieo lỗi xong phải kiểm test ĐỎ ỔN ĐỊNH (chạy hai lần). Lỗi gieo mà test
   vẫn xanh thì đề đó vô nghĩa — E1 đã có sẵn khâu này, chép lại.
d) chay_e1_dinh_vi() dựng bản sao tạm mỗi lần, tốn ~47 giây phụ cho mỗi lượt
   gọi. Bộ đề lớn thì nên gọi thẳng hàm trong tiến trình, đừng qua HTTP.
```

### Chạy thử

```
venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\do_e1_ngoai_ho.py
```

Sổ ghi ra `data/evidence_sprint/e1_ngoai_ho.json`. Giữ sổ cũ, đừng ghi đè.

---

## 3. Vì sao việc này đáng làm ngay

App sắp có nút "TÌM LỖI NHÂN QUẢ". Người mới bấm nút đó sẽ tin kết quả. Hiện
tại chúng ta biết:

```
E1 giải 3/4   trên bộ đề do CHÍNH họ phép của E1 sinh ra
E1 giải ?/?   trên lỗi ngoài họ            <- CHƯA AI BIẾT
```

Ô thứ hai trống mà nút đã sắp ra mắt. Đó là lý do việc này đứng trước mọi việc
mở rộng tính năng.
