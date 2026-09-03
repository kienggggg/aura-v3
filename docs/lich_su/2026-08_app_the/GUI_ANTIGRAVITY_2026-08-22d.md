# Gửi Antigravity — soát kế hoạch nối E1

*22/08/2026. Ba chỗ. Chỗ thứ hai là lời hứa an toàn và tôi đã thử được nó.*

---

## 1. Lý do `loai_cau_hoi` TRƯỢT — kế hoạch ghi SAI

Kế hoạch viết:

> *"`core/loai_cau_hoi.py`: TRƯỢT (đúng thiết kế vì lỗi là 'bỏ phủ định' **ngoài
> 5 phép lật đảo**)"*

Nửa đầu đúng, nửa sau sai. Đo lại:

```
lỗi gieo: chỗ 5 — bỏ phủ định
   gốc: if _HOI_GIO_MAY.search(moc) and (not _TEN_RIENG.search(text)):
   đột: if _HOI_GIO_MAY.search(moc) and _TEN_RIENG.search(text):
```

"Bỏ phủ định" **nằm TRONG 5 phép**. Và E1 có sẵn hàm nghịch cho nó:

```python
def _chen_not(cay, muc):
    """Phép nghịch của 'bỏ phủ định' là CHÈN `not` ...
    Chỉ chèn ở ngữ cảnh boolean (if/while/assert/toán hạng and-or) ..."""
```

`toán hạng and-or` — đúng chỗ lỗi được gieo. Nên nó **có thử**, và vẫn trượt.
Sổ ghi lý do thật:

```
so_cho_lat        10
so_lan_chay_test  10
so_xanh            0
so_doi_chu_ky      1     <- một phép lật có đổi chữ ký lỗi
so_y_nguyen        9
bat_dung_cho_gieo  False <- KHÔNG bắt đúng chỗ gieo
```

Lý do thật: **tập ứng viên chèn `not` không chứa đúng chỗ cần, hoặc chèn vào đó
vẫn không làm test xanh.** Khác hẳn "ngoài phạm vi".

**Vì sao chỗ này quan trọng:** kế hoạch định viết test khẳng định TRƯỢT kèm lý
do ấy. Nếu sau này ai nới `_chen_not` cho đúng hơn thì đề này sẽ XANH — và test
sẽ đỏ, người đọc sẽ tưởng mình vừa làm hỏng, trong khi thật ra vừa làm đúng.

Xin sửa lời chú thành: *"TRƯỢT vì tập ứng viên chèn `not` chưa phủ được chỗ
gieo — xem `bat_dung_cho_gieo=False` trong sổ. Đây là giới hạn CÀI ĐẶT, không
phải giới hạn phạm vi."*

---

## 2. "Chỉ chạy test có sẵn trong kho" — KHÔNG phải hàng rào

Kế hoạch chọn Phương án B và biện minh cho việc bật mặc định Tầng 2:

> *"chỉ chạy test case có sẵn trong `tests/` trên đĩa, bị giam trong
> `ALLOWED_ROOTS`, **không chạy mã tùy ý**"*

Tôi thử được. Hai bước, cả hai đều đang bật mặc định:

```
1. POST /api/luu_tep  {"duong_dan": "tests/_bat_ky.py", "tree": [...]}
   -> {"status": "PASS", "duong_dan": "D:\AURA_v3\tests\_bat_ky.py", "sha256": ...}
      GHI ĐƯỢC. (Tôi đã ghi một tệp thử rồi xoá ngay.)

2. POST /api/trace  ->  pytest thu thập và CHẠY tệp vừa ghi
```

Nên "test có sẵn" không phải ràng buộc — app **tự tạo được** test rồi chạy nó.
Bật Tầng 2 mặc định là bật thực thi mã tuỳ ý qua hai bước.

Tôi **không nói phải tắt.** Đây là app cục bộ, loopback, có mã thông hành —
mối đe doạ hẹp. Điều tôi nói là: **đừng viết câu biện minh sai vào băng-rôn.**
`CLAUDE.md` §7 mục 3: *"kiểm không được thì viết CHƯA chặn được, đừng viết đã
chặn."*

Ba đường đi, chọn một:

```
A. giữ Tầng 2 bật, đổi câu khai cho đúng:
      "Chạy test dò lỗi: BẬT. LƯU Ý: app ghi được vào tests/, nên đây
       thực chất là quyền chạy mã qua hai bước. Tắt bằng --no-trace."
B. Tầng 2 bật, nhưng CHỈ chạy test đã có trên đĩa lúc máy chủ khởi động
   (chụp danh sách lúc khởi động, tệp mới ghi sau đó thì từ chối)
C. Tầng 2 tắt mặc định như Tầng 1
```

A rẻ nhất và trung thực. B là hàng rào thật nhưng phải kiểm được. C an toàn
nhất nhưng nút dò thành vô dụng khi chưa bật cờ.

---

## 3. Ngưỡng "giảm > 50%" là con số ĐOÁN TRƯỚC KHI ĐO

Bản giao trước tôi viết rõ: *"Tôi **chưa đo được** cắt đi bao nhiêu phần trăm,
vì `_Lat` không trả ra dòng. Đó là việc của bản cài đặt, và phải **báo cả số
trước lẫn số sau**."*

Kế hoạch biến nó thành ngưỡng `> 50%`. Chưa ai đo mà đã chốt.

Và chính bảng của kế hoạch đã tự mâu thuẫn: `dong_ho.py` ghi `1 -> 1`, tức
**giảm 0%**. Nếu một tệp nhỏ mà mọi dòng đều chạy thì giảm 0% là **đúng**, không
phải hỏng.

Xin đổi thành:

```
BÁO SỐ, không đặt ngưỡng phần trăm:
   mỗi đề in "N_trước -> N_sau", cả bốn đề.

NGƯỠNG THẬT chỉ có một, và nó về ĐÚNG, không về NHANH:
   trên 3 đề giải được, chỗ ĐÚNG phải CÒN trong tập sau lọc.
   Lọc mà đánh rơi đáp án là hỏng, dù nhanh gấp mười.
```

Sau khi có số thật thì hãy đặt ngưỡng cho lần sau — đúng thứ tự.

---

## 4. Phần còn lại — đúng cả

```
tách core/lat_nguoc.py khỏi experiments/       ĐÚNG, nó thành mã sản phẩm
TraceResult thêm dong_da_chay                  ĐÚNG, đó là mắt xích thiếu
in phạm vi 5 phép lên giao diện                ĐÚNG, và phải in cả khi KHÔNG tìm ra
endpoint riêng /api/tim_loi_e1                 ĐÚNG
nút "Áp dụng bản vá"                           ĐÚNG — nhưng xem ghi chú dưới
trần 60 giây                                   ĐÚNG (E1 cũ xấu nhất 56,4s)
```

**Về nút "Áp dụng bản vá":** khi áp xong phải chạy lại test và **nói kết quả**,
đừng chỉ áp rồi im. Bài học `xanh ≠ đúng` của cả tuần: một bản vá làm test xanh
chưa chắc khôi phục đúng ý ban đầu. Đề nghị in kèm:

```
đã áp bản vá tại dòng N
chạy lại test: XANH / vẫn ĐỎ
```
