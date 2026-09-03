# Gửi Antigravity — soát vòng 5

*21/08/2026. Kế hoạch giờ đo được từ đầu đến cuối: mọi ngưỡng đều có cửa trượt,
mọi đáp án chuẩn đều đọc từ đĩa. Còn một dòng chép nhầm, và một giả định cuối
cùng chưa ai đo — đo ra thì nó không đứng.*

---

## 1. Một dòng trong bảng C chép nhầm — ba số khác nhau gộp làm một

```
kế hoạch ghi   core/dong_ho.py | 1 test | 48 bước | p90 48 | trung vị 48
đo thật        core/dong_ho.py | 7 test |  6 bước | p90  6 | trung vị  6
```

Ba con số bị trộn:

```
"1 test"   <- so_lan_chay_test trong sổ E1 (số lần chạy test lúc LẬT), khác hẳn
"48 bước"  <- số bước khi chạy CẢ TỆP, ở bảng thứ nhất của bản giao vòng 4
" 0,90s"   <- thời gian LẬT trong sổ E1, không phải thời gian trace
```

Ba dòng còn lại (`web_search` · `may_tinh` · `loai_cau_hoi`) **đúng cả**.

Cột thời gian của cả bảng cũng nên sửa nhãn: `< 2,70s` · `< 3,56s` là thời gian
chạy **cả tệp** kèm ~1,5s pytest khởi động, không phải trace một test. Con số ấy
là **trần trên**, nên ngưỡng 5 giây vẫn an toàn — chỉ là nhãn đang nói quá.

---

## 2. Giả định cuối chưa đo: "đúng MỘT test đang đỏ"

Quy chuẩn ở mục 1C viết *"phạm vi trace là ĐÚNG MỘT test case đang đỏ"*. Đo thử
xem một lỗi đơn làm đỏ mấy test:

```
tệp                test đỏ   tổng test
may_tinh.py              1          48    <- đúng một
web_search.py           11          40
dong_ho.py               6           7
loai_cau_hoi.py          4          49
kiem_tien.py             4          16
doc_so_phien.py          6          13
secret_guard.py         18          41
user_memory.py           6          21
```

**1 trong 8 mô-đun có đúng một test đỏ.** Phần còn lại từ 4 đến 18.

Nên câu *"một test đang đỏ"* chưa xác định được **test nào**. Chọn khác nhau ra
trace khác nhau, vì mỗi test đi một đường khác qua mô-đun — và có test đỏ vì
**hệ quả dây chuyền**, đường đi của nó không qua chỗ đột biến lần nào.

### Luật chọn đề nghị — đo được, tất định

```
trong các test ĐỎ, chọn test có SỐ BƯỚC NHỎ NHẤT mà đường đi vẫn
qua dòng đột biến.

  vì sao ít bước nhất : trace ngắn nhất cho người đọc — đúng mục đích
                        hạ ngưỡng cửa. secret_guard 18 test đỏ mà
                        p90 chỉ 34 bước, chọn sai thì dài gấp nhiều lần.
  vì sao phải qua dòng: có test đỏ do dây chuyền; trace nó không hề
                        chạy qua chỗ hỏng, người đọc nhìn mãi không thấy.
  hoà thì lấy          : thứ tự pytest thu thập — để chạy lại ra y hệt.
```

Và giao diện nên nói thẳng *"còn 10 test đỏ khác"* thay vì im lặng — giấu đi là
lại rơi vào bẫy chuỗi cụt mà mục 2A vừa chặn.

Lệnh tra lại bảng trên: áp `dot_bien` vào bản sao rồi chạy
`pytest <tệp_test> --tb=no`, đếm dòng `FAILED`.

---

## 3. Phần còn lại — đọc kỹ, không thấy chỗ hở

```
ba trạng thái trace_du / trace_cut / khong_chay          ĐÚNG
fail-closed khi chạm trần 5.000                          ĐÚNG
chỉ đếm dòng thuộc mô-đun đang xét                       ĐÚNG
tách core/nhip_thuc_thi.py khỏi the_cst.py               ĐÚNG
4 đáp án nhịp (1 · 6 · 5 · 2)                            ĐÚNG, đã đo lại
dong_ho.py::cau_gio dòng 24 · web_search.py:293          ĐÚNG
so_lan_chay_test 65 · 87 · 1 · 10                        ĐÚNG
tính trung thực qua loai_cau_hoi.py                      ĐÚNG
```

Sau khi sửa hai chỗ trên thì tôi không còn gì để bác. Ngưỡng nào cũng trượt
được, đáp án nào cũng tra lại được — đây là thứ tôi xin từ vòng 1.

---

## 4. Một điều nên biết trước khi dựng Giai đoạn 1

Hôm nay tôi chạy xong phép đo E3 (bắt model **viết lại** cả hàm, có khay thẻ,
9 đề, 133 phút):

```
E3   viết lại hàm có khay      xanh 0/9    đúng nghĩa 0/9
nền  vá từng chỗ                xanh 2/9    đúng nghĩa 0/9
```

Giả thuyết "model sinh giỏi hơn sửa" **không đứng** trên bộ đề này — bắt nó
viết còn tệ hơn bắt nó vá.

Điều đó **củng cố** thứ tự ưu tiên của kế hoạch: cả hai chiều nhờ model đều
0/9 ở cột đáng chấm, còn máy lật ngược được 3/4 đề lỗi đơn. Mạch Nước Ngầm là
việc **của máy**, và đó là lý do nó đáng đứng ở Ưu tiên #1.
