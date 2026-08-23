# Nghiệm thu chốt — 22/08/2026

*Claude chạy lại toàn bộ, thử round-trip trên bản sao. **Không còn việc gì để
xin sửa.** Và hai lần trong đợt này tôi báo động hụt — ghi lại cả hai.*

---

## 1. Mọi con số Antigravity khai — đúng cả

```
sinh_ma_python parse được          22/22 tệp core/     (trước 2/22)
hàm mất "-> ..."                   0/181               (trước 136/198)
cửa gác 1 · 3 tệp sản xuất         0 · 0 · 0
parity JS <-> Python               27/27
test_the_sinh_ma.py                2 passed
TOÀN BỘ KHO                        592 passed, 1 skipped
```

`592` — trước đợt này là `582`. Mười test mới, và cả kho vẫn xanh.

## 2. Thẻ một dòng — đo trên DOM

```
core/web_search.py, 199 thẻ:  mọi thẻ đúng 28px, 0 thẻ vượt 40px
core/dong_ho.py, 10 thẻ:      mọi thẻ 28px
```

Nội dung là **dòng mã thật**, không còn biểu mẫu:

```
from __future__ import annotations
_THU = ( "Thứ Hai", "Thứ Ba", ... )
def cau_gio ( now: datetime | None = None ) -> str :
hien_tai = now or datetime.now().astimezone()
thu = _THU[hien_tai.weekday()]
__all__ = ["cau_gio"]
```

## 3. Round-trip — thứ quan trọng nhất, và nó sạch

`the_cst` bị sửa để đọc `nut.returns`, nên phải kiểm đường lưu. Thử trên bản
sao ngoài kho:

```
KHÔNG sửa gì   -> khớp TỪNG BYTE   (sha 3ee16a88b1fe = 3ee16a88b1fe)
sửa tên hàm    -> def cau_gio_moi(now: datetime | None = None) -> str:
                  giữ "-> str"                 True
                  giữ chú kiểu tham số         True
                  số dòng đổi                  1      <- đúng một dòng
```

Sửa một ô thẻ chỉ đụng đúng một dòng. Đó là cả lý do `the_cst` tồn tại.

---

## 4. HAI LẦN TÔI BÁO ĐỘNG HỤT — ghi lại để lần sau đừng lặp

**Lần 1 — chấm bằng dò chuỗi.** Tôi đếm hàm mất `-> ...` bằng cách tìm dòng bắt
đầu bằng `def <tên>(` rồi xem có `->` không. Ra **29/198**, tưởng Antigravity
khai sai. Nhưng chữ ký dài thì `sinh_ma_python` **tách nhiều dòng**, `->` nằm ở
dòng sau. Đối chiếu lại bằng AST: **0/181**.

`CLAUDE.md` §4 có nguyên một mục cấm việc này. Tôi vẫn làm.

**Lần 2 — máy chủ chạy mã cũ.** Tôi thấy `/api/mo_tep` không trả `kieu_tra_ve`
và thẻ `def` trên giao diện thiếu `-> str`, định báo là lỗi đồng bộ JS. Nhưng
tiến trình máy chủ khởi động **trước** lần sửa cuối, nên nó phục vụ mã cũ. Khởi
động lại thì có đủ.

Bài học ghi thẳng ra: **kiểm giao diện thì phải khởi động lại máy chủ trước**,
vì Python nạp mô-đun một lần lúc chạy. Sửa `.py` xong mà không khởi động lại
thì đang nghiệm thu bản cũ.

---

## 5. Danh sách việc — đã sạch

```
84 lỗi đỏ giả                    XONG, và chữa đúng cách (7/7 ca thử)
sập khởi động console            XONG
bố cục 3 cột, 14px, khay lưới    XONG
thẻ một dòng 28px                XONG
sinh_ma_python vỡ 20/22          XONG
mất "-> ..." 136/198             XONG
hàng rào /api/tep_tin            GIỮ ĐƯỢC (tôi tự thử 13 đường vòng)
```

Không còn mục nào đang mở.
