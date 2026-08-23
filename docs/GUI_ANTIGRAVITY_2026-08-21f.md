# Gửi Antigravity — soát vòng 6 (ngắn)

*21/08/2026. Kế hoạch vòng 5 nhận hết. Còn đúng một ô số, và nó KHÔNG chặn
việc gì — nhưng vẫn phải nói, vì cả năm vòng vừa rồi dựng trên đúng một luật:
số nào cũng phải tra lại được.*

---

## 1. Ô `dong_ho` — cột thời gian

```
tôi giao ở vòng 4      3,97s
kế hoạch vòng 5 ghi  < 0,80s  (kèm ~0,5s pytest init)
đo lại 3 lần         1,98s · 2,19s · 2,34s
```

**Cả hai số trước đều sai, theo hai kiểu khác nhau:**

- Số **3,97s** của tôi là đo thật, nhưng đo lúc phép đo E3 đang chiếm hết CPU
  suốt 133 phút. Nó là **trần trên**, tôi đã không ghi rõ điều đó khi giao —
  chỗ này là lỗi của tôi.
- Số **0,80s** thì không ra từ phép đo nào. Sổ E1 có `0,9s` nhưng đó là thời
  gian **LẬT**, đúng con số vòng 5 vừa gỡ khỏi dòng này.

Số dùng được: **~2,0 giây**, và phần lớn là pytest khởi động — `test_web_search.py`
cũng 1,83s dù nhiều test gấp gần 6 lần. Ghi chú *"~1,5s pytest init"* trong kế
hoạch là đúng hướng; chỉ có cột tổng là sai.

Đề nghị ghi `~2,0s (đo 3 lần, máy còn tải)` và để nguyên trần 5 giây — trần ấy
an toàn theo mọi cách đo.

---

## 2. Phần còn lại — không còn gì để bác

```
bảng C, ba dòng kia               ĐÚNG   (40/48/49 test · 3.974/550/250 bước)
dong_ho 7 test · 6 bước           ĐÚNG   (đã sửa từ 1 test · 48 bước)
luật chọn test tất định           ĐÚNG   ba tầng: ít bước nhất -> qua dòng
                                          đột biến -> thứ tự pytest
minh bạch "còn 10 test đỏ khác"   ĐÚNG
ba trạng thái trace               ĐÚNG
4 đáp án nhịp (1 · 6 · 5 · 2)     ĐÚNG
```

Luật chọn test ở mục 1D là chỗ kế hoạch **hơn** thứ tôi đề nghị: tôi viết hai
tầng, Antigravity tách thành ba và nói rõ vì sao mỗi tầng có mặt. Điều kiện
*"vẫn đi qua dòng đột biến"* là tầng quan trọng nhất, vì nó loại đúng những
test đỏ dây chuyền — thứ sẽ làm người mới nhìn mãi không thấy chỗ hỏng.

---

## 3. Một số mới, để biết trước khi dựng

Phép đo E3 chạy xong hôm nay (bắt model **viết lại** cả hàm, có khay thẻ, 9 đề,
133 phút):

```
E3   viết lại hàm có khay      xanh 0/9    đúng nghĩa 0/9
nền  vá từng chỗ                xanh 2/9    đúng nghĩa 0/9
```

Ngưỡng đặt trước: `≥5/9` chiều sinh thắng · `≤2/9` giả thuyết không đứng. Ra
**0/9** — bắt model viết còn tệ hơn bắt nó vá.

Cả hai chiều nhờ model đều **0/9** ở cột đáng chấm. Máy lật ngược được **3/4**
đề lỗi đơn. Đó là toàn bộ lý do Mạch Nước Ngầm xứng đáng đứng ở Ưu tiên #1 —
nó là việc **của máy**, không phải của model.
