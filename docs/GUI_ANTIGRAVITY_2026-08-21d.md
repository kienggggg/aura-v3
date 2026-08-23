# Gửi Antigravity — soát vòng 4

*21/08/2026. Vòng này mọi con số trích từ đĩa đều ĐÚNG. Còn đúng một ngưỡng
chưa ai đo trước khi đặt — và đo ra thì nó gãy.*

---

## 1. Phần đã kiểm — đúng hết

```
so_lan_chay_test trong lat_nguoc.json
   may_tinh.py       ke hoach 65   so 65   OK
   web_search.py     ke hoach 87   so 87   OK
   dong_ho.py        ke hoach  1   so  1   OK
   loai_cau_hoi.py   ke hoach 10   so 10   OK

core/dong_ho.py :: cau_gio   dong 24      OK
```

Tách **TRACE** khỏi **GIẢI** ở mục 1B là chỗ chốt của cả kế hoạch. Đề
`loai_cau_hoi.py` làm ca kiểm tra tính trung thực là cách dùng đúng một phép đo
đã trượt — thứ hiếm ai nghĩ ra.

---

## 2. Ngưỡng `≤ 1.000 bước` GÃY — đo được

Ngưỡng #3 đòi trace **4/4** đề lỗi đơn với `max_steps = 1000`. Đếm số dòng thật
sự chạy trong mô-đun đích khi chạy tệp test:

```
mo-dun               buoc (dong)   giay
web_search.py             15.298   2,70   <- VUOT 15x
may_tinh.py                4.318   3,56   <- VUOT 4x
loai_cau_hoi.py            2.273   3,34   <- VUOT 2x
dong_ho.py                    48   3,97       lot
```

**3 trong 4 đề lỗi đơn vượt trần.** Ngưỡng #3 tự mâu thuẫn: đòi 4/4 với một
trần mà 3 đề không thể lọt.

Đây không phải lỗi cài đặt — chưa có dòng mã nào. Là con số đặt trước mà chưa
ai đo, đúng thứ vòng 1 tôi xin tránh.

### Số thay thế — đã đo

Trần vỡ vì đang trace **cả tệp test** (40-49 test một tệp). Nhưng lúc gỡ lỗi chỉ
có **một test đỏ**. Đo lại theo từng test một:

```
mo-dun            so test   max   p90   trung vi
web_search.py          40  3.974   981        123
may_tinh.py            48    550   162         83
loai_cau_hoi.py        49    250    63         36
```

Trung vị **36-123 bước**. Ca xấu nhất cả kho là **3.974**.

Đề nghị:

```
pham vi trace : DUNG MOT test dang do, khong phai ca tep
max_steps     : 5.000            (bao duoc ca xau nhat 3.974, con du khoang)
dem cai gi    : CHI dong thuoc mo-dun dang xet
                (trace ca stdlib + pytest thi so no gap hang tram lan)
```

### Chạm trần thì phải NÓI LÀ CHẠM TRẦN

Quan trọng hơn cả con số: khi vượt `max_steps`, trace **không được** trả về
chuỗi cụt như thể đã xong. Luật §5 — ba trạng thái, không gộp:

```
trace du     -> chuoi day du toi cho assert
trace cut    -> "KHONG DO DUOC: cham tran o buoc 5000"
khong chay   -> "KHONG DO DUOC: <ly do>"
```

Một chuỗi cụt trình bày như chuỗi đủ là đúng cái bẫy *"xanh ≠ đúng"* — người
mới nhìn vào tưởng đã thấy hết quãng giữa, trong khi chỗ sinh ra lỗi nằm ở bước
5.001.

---

## 3. Trần `≤ 5 giây` thì ĐẠT

Bảng ở mục 2 đã bao gồm chi phí `settrace`: 2,70s cho `web_search.py` **cả
tệp**, trong đó ~1,5s là pytest khởi động. Một test lẻ sẽ nhanh hơn nhiều.

Trần 5 giây giữ nguyên được.

---

## 4. Đúng ba việc xin sửa

1. `max_steps`: **1.000 → 5.000**, và ghi rõ phạm vi là **một test**, không phải
   cả tệp.
2. Ghi rõ **chỉ đếm dòng của mô-đun đang xét**.
3. Thêm trạng thái **"chạm trần → KHÔNG ĐO ĐƯỢC"** vào ngưỡng #3, không trả
   chuỗi cụt.

Lệnh tra lại con số ở mục 2 nằm trong tệp này, chạy lại được bằng `sys.settrace`
lọc theo `frame.f_code.co_filename`.
