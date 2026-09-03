# Gửi Antigravity — soát kế hoạch cải tạo, vòng 2

*22/08/2026. Đã chạy lệnh nghiệm thu trong kế hoạch. Ba chỗ.*

---

## 1. Lệnh nghiệm thu vòng này KHÔNG CHẠY ĐƯỢC

Chạy nguyên văn lệnh mục 1 phần Verification Plan:

```
File "D:\AURA_v3\core\the_cst.py", line 292, in doc_chuoi_py_sang_cay_the
    b = nguon.encode("utf-8")
AttributeError: 'bytes' object has no attribute 'encode'
```

`core.the_cst.doc_chuoi_py_sang_cay_the` nhận **CHUỖI**. Chỗ bọc bytes→chuỗi
nằm ở `interface/the_api.py`, không nằm ở `core/the_cst`.

Điều đáng nói: **vòng trước lệnh của Antigravity CHẠY ĐƯỢC** — nó dùng
`doc_tep_py_sang_cay_the` và trượt bằng `AssertionError`, đúng lý do. Vòng này
đổi sang `doc_chuoi_py_sang_cay_the(Path(p).read_bytes(), p)` và hỏng.

Đây là chỗ nguy hiểm hơn một cửa gác lỏng: một cửa gác **luôn nổ** thì người
chạy không bao giờ biết con số thật là bao nhiêu.

Hai bản sửa, tôi đã chạy cả hai:

```
# A — ngắn nhất, đúng như vòng trước
from core.the_cst import doc_tep_py_sang_cay_the
kiem_tra_cay_the(doc_tep_py_sang_cay_the(p).tree).so_loi_do

# B — nếu muốn giữ doc_chuoi thì phải read_text, không read_bytes
doc_chuoi_py_sang_cay_the(Path(p).read_text(encoding="utf-8"), p)
```

Cả hai cho cùng số, và đây là **mốc trước khi sửa**:

```
core/web_search.py   84
core/dong_ho.py       2
core/kiem_tien.py    14
```

## 2. `tests/test_the_app.py` không tồn tại

Verification Plan mục 3 ghi *"Chạy test suite `tests/test_the_app.py`"*. Trong
kho không có tệp đó. Nếu định viết mới thì ghi là **tạo mới**; nếu định kiểm
bằng script HTTP thì bỏ tên tệp đi.

Khi endpoint có mặt tôi sẽ tự thử `../`, đường dẫn tuyệt đối ngoài kho, và
thiếu token.

## 3. Bộ parity 22/22 xanh vì ca kiểm thử QUÁ DỄ

Đây là chỗ đáng giá nhất trong trang này.

`node tests/test_the_parity.js` → **22/22 PASS, mã thoát 0**. Nhưng mã thật có
84 lỗi đỏ. Vì sao cả hai cùng đúng? Mở ca số 20 ra:

```js
name: "20_ham_nhieu_tham_so",
  { ma: "ham", o: { ten_ham: "tinh_tong_3", tham_so: "x, y, z" } ... }
```

`"x, y, z"` — tên trần. Không chú kiểu, không giá trị mặc định, không `*`.
Nên bộ trích tham số hiện nay xử lý được, và ca này xanh.

Chữ ký THẬT trong kho thì thế này:

```
may_tinh.py    _tinh_cay    nut: ast.AST, an: tuple[str, float] | None = None
may_tinh.py    tinh_giup    text: str, *, now: datetime | None = None
khay_the.py    sinh_khay    goc: Path, thu_muc: tuple[str, ...] = ("core", "interface", "tools")
user_memory.py remember     text: str, *, confirmed_by_user: bool = False
the_v1.py      sinh_ma...   nodes: List[TheNode], indent_level: int = 0
```

**Xin lấy đúng năm chuỗi này làm ca `tham_so_ham_da_dang`**, đừng đặt thêm một
`x, y, z` nữa. Bốn ca còn lại cũng vậy: lấy dòng import thật
(`from urllib.parse import urlsplit, urlunsplit`), tên hàm thật, biến vòng lặp
thật — không phải mẫu tự nghĩ ra.

Vì bộ 22 ca hiện nay **không thể trượt** trên chính lỗi đang cần chữa. Đó là
lần thứ tư cùng một bệnh trong loạt này, chỉ khác tầng: vòng 1 ở bộ đề, vòng 5
ở ngưỡng, vòng 7 ở unit test, giờ ở dữ liệu của bộ parity.

Cách kiểm nhanh cho chính Antigravity: **thêm ca mới TRƯỚC khi sửa bộ kiểm**.
Nếu ca mới xanh ngay thì ca ấy chưa chạm vào lỗi.

---

## 4. Phông 11px: 8px dư là quá sát

Kế hoạch chốt mặc định 11px cho màn 1280 với lý do `516px < 524px`. Số ấy đúng,
tôi đo ra. Nhưng `524` là **tôi ước lượng**: 96px thụt sáu tầng + ~120px nút và
lề. Nếu nút/lề thật là 140px thì còn 504px, và 11px **tràn**.

Dư 8px trên 524 là **1,5%**. Đừng chỉnh phông cho vừa khít một con số ước
lượng.

Đề nghị đổi cách: **màn < 1400px thì cột phải (Agent) mặc định THU GỌN.**

```
1280, thu cot phai  ->  giua 1040px
                        tru thut 96 + nut/le 120  ->  824px
                        14px can 656px  ->  du 168px, khong sat
```

Người dùng bung cột Agent ra khi cần; lúc ấy hoặc chấp nhận 11px, hoặc cắt đuôi
sớm hơn. Như vậy cỡ chữ mặc định là **14px đọc được**, không phải 11px.

---

## 5. Phần còn lại

```
sys.stdout.reconfigure + bỏ emoji + flush=True   ĐÚNG, chữa đúng dòng 58
thu gọn 2 cột, Ctrl +/-/0, lưu localStorage      ĐÚNG
scope 2 pha, 5 nhóm định danh                     ĐÚNG hướng
cắt nhịp theo def + nhãn "(Chưa đóng)"            ĐÚNG
tep_tin dùng lại kiem_tra_duong_dan_an_toan       ĐÚNG
```

Ba việc xin: sửa lệnh nghiệm thu (mục 1) · lấy chữ ký thật làm ca parity
(mục 3) · thu gọn cột phải thay vì ép phông xuống 11px (mục 4).
