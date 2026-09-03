# Bảng tổng kết — model có sửa được lỗi trong mã không

*22/08/2026. Tám phép đo, cùng 9 đề, cùng model `qwen2.5-coder:7b`, cùng trần
4 lượt, cùng gieo `random.Random(19082026)`.*

---

## 1. Bảng

```
                                          xanh   ĐÚNG NGHĨA   ai làm phần TÌM
nền   vá từng chỗ                          2/9      0/9        model
C     đổi một ô thẻ                        1/9      1/9        model
C2    đổi ô + ép khuôn JSON Schema         0/9        —        model
C3    đổi ô + ép enum                      0/9        —        model
E3    viết lại cả hàm, có khay thẻ         0/9      0/9        model
E2    khoét đúng chỗ, chỉ hỏi điền gì      1/9      0/9        MÁY (cho không)
E4    E2 + chặn ba nước đi sai             1/9      0/9        MÁY + chặn
E5    máy lọc ứng viên, model chọn số      1/9      1/9        MÁY
─────────────────────────────────────────────────────────────────────────────
E1    máy lật ngược, KHÔNG gọi model       3/9      3/9        MÁY, và máy chốt
```

**Máy một mình hơn mọi cách có model.** Gấp ba lần con số cao nhất ở cột đáng
chấm.

## 2. E5 — phép đo cuối, và nó dứt điểm

E5 dựng để thử đúng câu kết luận cả tuần: *"máy làm thám tử, model làm người kể
lại."* Máy làm hết phần khó — tìm test đỏ, truy vết, sinh ứng viên, lọc theo
dòng đã chạy. Model chỉ phải trả lời **một con số**.

```
tệp                lỗi   lọc        kết quả
may_tinh.py         1    65 -> 15   hết lượt
may_tinh.py         2    64 ->  9   hết lượt
may_tinh.py         3    64 ->  3   hết lượt      <- 3 ứng viên, đoán mò 33%
web_search.py       1    87 -> 28   hết lượt
web_search.py       2    86 ->  4   hết lượt
web_search.py       3    86 -> 14   hết lượt
dong_ho.py          1     1 ->  1   ĐẠT · đúng nghĩa
loai_cau_hoi.py     1    10 ->  2   hết lượt      <- 2 ứng viên, đoán mò 50%
loai_cau_hoi.py     2    10 ->  9   hết lượt
```

**Đề duy nhất đạt là đề máy lọc còn ĐÚNG MỘT ứng viên** — model không phải chọn
gì. Tám đề còn lại, nơi thật sự phải chọn: **0/8**.

Hai đề đáng nhìn kỹ: `may_tinh 3 lỗi` còn **3 ứng viên** và `loai_cau_hoi 1 lỗi`
còn **2 ứng viên**. Đoán mò ngẫu nhiên cho 33% và 50%. Model trượt cả hai.

Nước đi, 34 lượt:

```
chọn "1"   18 lần   chọn "3"  5   chọn "5"  4   chọn "17"  4   khác  3
```

Nó **lấy số đầu danh sách**, không đọc danh sách. Cùng nết với E2 (60% nước đi
là chép dòng ngay cạnh) và E4 (lặp một câu trả lời mười lần dù bị nói thẳng là
sai).

Ngưỡng đặt trước ngày 22/08: `>=5/9` phối hợp thắng · `3-4/9` ngang E1 · `<=2/9`
model làm hỏng thông tin máy đưa. Ra **1/9** — nhánh cuối.

## 3. Câu kết luận phải sửa lại

Cả tuần tôi viết: *"máy làm thám tử, model làm người kể lại."*

Nửa đầu đúng và giờ có ba con số chống lưng: E1 giải 3/9 không cần model, lọc
`65→15` mà **không đánh rơi đáp án**, và app đã dựng xong ba trong bốn câu mà
người mới cần.

Nửa sau **chưa được chứng minh, và E5 vừa bác nó ở dạng mạnh nhất**: cho model
một danh sách 2-3 ứng viên đã lọc sạch, nó vẫn không chọn được.

Câu đúng hơn theo số liệu hiện có:

> **Máy làm thám tử. Còn model làm gì thì CHƯA ĐO ĐƯỢC —
> tám cách bắt nó tham gia vào việc sửa đều không hơn máy làm một mình.**

Việc "kể lại" — viết đoạn văn giải thích cho người đọc — **chưa từng được đo**.
Tab Kịch Bản đang làm việc ấy nhưng chưa ai chấm nó đúng hay sai, hay hay dở.
Đó là ô trống lớn nhất còn lại.

## 4. Ba lần tôi phải sửa giàn đo của chính mình trong E5

Ghi ra vì nếu không sửa thì cả ba đều cho ra `0/9` và tôi đã báo một con số sai:

```
1. chọn sai vẫn GIỮ phép lật sai  -> trạng thái trôi, 15 ứng viên còn 4
2. lời nhắc lượt sau Y HỆT lượt trước -> model tất nhiên trả lời y hệt;
   đo tính tất định của giải mã, không đo năng lực
3. một phép lật làm pytest TREO 180 giây -> cả phép đo chết ở đề thứ tư
```

Sau khi sửa, tôi kiểm lại điều kiện cần: **đáp án có nằm trong danh sách không**
— `may_tinh` vị trí 8/15. Có. Nên đề giải được; model chỉ không chọn đúng.

Bài học chung của cả tuần, đắt nhất: **trước khi báo một con số 0, hãy chứng
minh bài toán ấy GIẢI ĐƯỢC.**
