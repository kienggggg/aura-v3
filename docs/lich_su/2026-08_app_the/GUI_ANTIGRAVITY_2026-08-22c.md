# Gửi Antigravity — bước tiếp: nối E1 vào nút "DÒ DÒNG DỮ LIỆU"

*22/08/2026. Nhưng có một việc phải làm TRƯỚC, và nó là lời hứa an toàn.*

---

## 1. TRƯỚC TIÊN: app đang nói sai về chính nó

```
máy chủ tự khai      code_execution_enabled = False
băng-rôn khởi động   "Chay ma : TAT MAC DINH"

gọi POST /api/trace  ->  trang_thai "trace_du"
                         tong_buoc  8
                         cac_su_kien 4
```

Mã của người dùng **đã chạy thật** — `chay_trace_mot_test` gọi `pytest` qua
`subprocess`. Nhưng `api_trace` chỉ có hai cửa:

```python
if not xac_thuc_request(request):   ...403
if not kiem_tra_origin_hop_le(request): ...403
```

Thiếu đúng cái cửa mà `api_chay_ma` có:

```python
if not ALLOW_CODE_EXECUTION:  ...403
```

`CLAUDE.md` §7 mục 3: *"Lời hứa an toàn phải kiểm trước tiên. Kiểm được thì
kiểm; kiểm không được thì viết CHƯA chặn được, đừng viết đã chặn."*

Hai cách sửa, chọn một và **nói ra trong băng-rôn**:

```
A. /api/trace cũng chịu cửa ALLOW_CODE_EXECUTION
   -> nút "DÒ DÒNG DỮ LIỆU" tắt theo, và tính năng E1 dưới đây cũng tắt theo
B. tách thành hai mức quyền, ghi rõ trong băng-rôn:
      chạy mã do NGƯỜI DÙNG gõ          : TẮT
      chạy TEST CÓ SẴN của kho để dò lỗi: BẬT
   và giải thích vì sao mức thứ hai chấp nhận được
```

Tôi không chọn hộ. Nhưng **không được để nguyên** — một câu sai về quyền hạn
nằm trong băng-rôn là thứ người sau sẽ tin.

---

## 2. Bước tiếp: E1 vào nút dò

### Vì sao

```
model tìm lỗi    6 hướng đã đo    0-2/9 xanh · 0-1/9 đúng nghĩa
máy tìm lỗi      E1 lật ngược     3/4 đề lỗi đơn, KHÔNG gọi model
```

Sổ E1: `data/evidence_sprint/lat_nguoc.json`.

### Phạm vi — phải in ra màn hình, không giấu

E1 đạt 3/4 vì nó biết lỗi thuộc **đúng năm phép**, mỗi phép có **đúng một phép
nghịch**:

```
<  <->  <=          and  <->  or
not     (bỏ/thêm)   True <-> False        n  ->  n±1
```

Lỗi thật của người dùng **không hẹp như thế**. Nhưng năm phép ấy đúng là năm
lỗi kinh điển của người mới — nên phạm vi này chấp nhận được, **với điều kiện
giao diện nói thẳng**:

> *"Chỉ dò được 5 loại lỗi so sánh/logic. Không tìm được lỗi khác."*

Giấu phạm vi đi là lặp lại đúng bệnh 84-lỗi-đỏ: một tín hiệu nghe rất chắc mà
người dùng không biết nó chắc tới đâu.

### Việc phải làm

Phần lớn đã có sẵn, chỉ thiếu một mắt xích:

```
[có rồi] _chay_pytest_tim_test_do        tìm test đỏ
[có rồi] chot_test_can_trace             chọn test tất định (3 tầng)
[có rồi] chay_trace_mot_test             vết + dòng đã chạy, 0,5s
[THIẾU ] _Lat ghi lineno cho từng chỗ    hiện chỉ ĐẾM, không biết chỗ nào ở dòng nào
[THIẾU ] lọc chỗ lật theo dòng ĐÃ CHẠY
[có rồi] lật nhiều vòng tham lam         E1 đã làm
```

Mắt xích thiếu là chỗ đáng giá nhất: **lật một dòng mà test không hề chạy qua
thì không thể đổi kết quả.** Bỏ chúng đi là cắt thẳng không gian tìm.

Số chỗ lật đo được trên `core/`:

```
dong_ho 1 · loai_cau_hoi 10 · secret_guard 14 · nhip_thuc_thi 15
kiem_tien 34 · may_tinh 65 · web_search 87 · the_cst 104 · the_v1 265
                                                    tổng cả core/: 1.242
```

Tôi **chưa đo được** cắt đi bao nhiêu phần trăm, vì `_Lat` không trả ra dòng.
Đó là việc của bản cài đặt, và phải **báo cả số trước lẫn số sau**.

### Ngưỡng đặt trước

```
1. DỰNG LẠI ĐÚNG SỔ E1, không hơn không kém:
      may_tinh.py     1 lỗi  ->  XANH
      web_search.py   1 lỗi  ->  XANH
      dong_ho.py      1 lỗi  ->  XANH
      loai_cau_hoi.py 1 lỗi  ->  TRƯỢT     <- phải TRƯỢT
   Đề thứ tư trượt là một phần của ngưỡng. Nếu bản mới "giải được" nó thì
   phải giải thích bằng gì, đừng mừng.

2. LỌC KHÔNG ĐƯỢC ĐÁNH RƠI ĐÁP ÁN:
      trên 3 đề giải được, chỗ đúng phải CÒN trong tập sau khi lọc.
      Lọc mà mất đáp án thì lọc sai, dù nhanh hơn.

3. THỜI GIAN:  <= 60 giây mỗi tệp.  (E1 cũ: 40,5s · 56,4s · 0,9s · 6,3s)

4. BÁO SỐ TRƯỚC/SAU:  số chỗ lật trước lọc và sau lọc, từng đề.
```

Ngưỡng 2 là ngưỡng quan trọng nhất. Tối ưu tốc độ mà làm rơi câu trả lời là
đúng loại lỗi đã gặp ba lần trong loạt này.

---

## 3. Thứ tự tôi đề nghị

```
1. vá cửa ALLOW_CODE_EXECUTION cho /api/trace, sửa băng-rôn   <- trước hết
2. _Lat ghi lineno + lọc theo dòng đã chạy, báo số trước/sau
3. nối vào nút "DÒ DÒNG DỮ LIỆU", in phạm vi 5 phép lên màn hình
4. dựng lại sổ E1, đối chiếu 4 đề
```

Việc 1 không phụ thuộc ba việc sau và làm được ngay.
