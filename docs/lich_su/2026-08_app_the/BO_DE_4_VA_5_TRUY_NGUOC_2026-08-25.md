# Bộ đề 4 và 5 — truy ngược giá trị · 25/08/2026

## Hai bản sửa đem ra thử

**1. Cạnh qua ranh giới hàm** (`_ra_khoi_ham_gan_nhat`). Gộp bộ 1 + bộ 3 đo
được: lỗi CÙNG hàm với mốc 42/49 = 0,86; lỗi KHÁC hàm 1/31 = 0,03.
`_viet_gan_nhat` tìm theo TÊN trên danh sách sự kiện PHẲNG, không có phạm vi
hàm — nên một lời gọi hàm là bức tường kín.

**2. Siết luật "lỗi bị nuốt giữa chừng".** Luật cũ rút từ bộ 2 báo động giả:
`core/khay_the.py:182` là `ra[n.name] = The(...)` — dựng đối tượng;
`sys.settrace` phát `tra_ve` khi `The.__init__` xong, mà dòng 182 không phải
`return`, nên luật cũ kêu "chết ở đây" ngay bước 27 trong khi chương trình
chạy tới bước 95. Sửa: đòi bằng chứng — một cú chết bị nuốt thì phải có kẻ
nuốt, bước kế tiếp phải nằm trong thân một `except`.

## Bộ 5 — phép đo sạch, cùng 64 đề, CHỈ cỗ máy đổi

| | ca SÂU (lỗi trong hàm nội bộ) | ca NÔNG | tổng | dài chuỗi (dòng riêng) |
|---|---|---|---|---|
| máy CŨ (`14b4666`) | 8/14 = 0,57 | 6/11 = 0,55 | **0,56** | trung vị 4 |
| máy MỚI | 12/15 = **0,80** | 8/11 = **0,73** | **0,77** | trung vị 7 |

Năm ngưỡng đăng ký TRƯỚC khi bộ 5 sinh xong, không nới con số nào của bộ 4:

```
A. chính xác ca SÂU              0,80   >= 0,50   ĐẠT   (n = 15, trên mức tối thiểu 10)
B. ca NÔNG máy MỚI >= máy CŨ     0,73 so 0,55     ĐẠT
C. chính xác tổng                0,77   >= 0,60   ĐẠT
D. độ phủ                        1,00   >= 0,25   ĐẠT
E. model_calls                   0      = 0       ĐẠT
```

**Lần đầu trong cả chiến dịch có một bộ đạt đủ năm ngưỡng.**

Nhưng ba điều phải nói cùng lúc, không được để Sếp phải hỏi:

**Một — bộ 5 chọn theo chính giả thuyết đang kiểm.** Ba tệp được chọn vì tỉ lệ
hàm nội bộ cao (`chat_service` 82% · `the_cst` 77% · `the_v1` 74%). Nó trả lời
được "khi có nhiều ca sâu thì bản sửa làm được gì"; nó KHÔNG trả lời "cỗ máy
đã dùng được chưa". Điều này đã đăng ký trước khi thấy kết quả.

**Hai — 38/64 đề KHÔNG ĐO ĐƯỢC**, lý do "không có test đỏ nào trace được".
Riêng `core/the_v1.py` là **24/24 không đo được** — tệp ấy góp đúng 0 ca. Nên
26 ca đo được thật ra chỉ đến từ hai tệp: `chat_service` 11 và `the_cst` 15.

**Ba — chuỗi dài ra gấp bốn.** Ngưỡng "dài chuỗi trung vị <= 8" đo theo số mục
chuỗi: máy cũ 4, máy mới **18** — TRƯỢT. Đếm theo dòng riêng thì 4 lên 7. Cạnh
qua ranh giới hàm mua độ chính xác bằng cách nạp thêm rất nhiều dòng vào chuỗi.
Chuỗi 18 mục chỉ đúng chỗ vẫn kém hơn chuỗi 4 mục chỉ đúng chỗ.

## Bộ 4 — phép đo sạch, cùng 58 đề

| | ca SÂU | ca NÔNG | tổng |
|---|---|---|---|
| máy CŨ | 1/8 = 0,12 | 17/28 = 0,61 | **0,50** |
| máy MỚI | 3/8 = 0,38 | 17/28 = 0,61 | **0,56** |

Bản sửa giúp đúng chỗ dự đoán, không làm hỏng chỗ đang chạy. Nhưng ngưỡng
chính của bộ 4 **KHÔNG ĐO ĐƯỢC**: chỉ 8 ca sâu, dưới mức tối thiểu 10 đã đăng
ký. Nguyên nhân đã cảnh báo TRƯỚC khi sinh đề — bộ 4 có tỉ lệ hàm nội bộ 49%,
thấp nhất bốn bộ.

## Hai lỗi phương pháp của chính tôi, cả hai bắt được bằng cách chạy

**Thước đo phụ thuộc thứ nó đang chấm.** Ngưỡng A và B của bộ 4 phân loại ca
theo "dòng lỗi có cùng hàm với MỐC BẮT ĐẦU không". Mốc là thứ CỖ MÁY chọn, mà
bản sửa đã dời mốc — nên số ca mỗi loại đổi theo cỗ máy (khác hàm 14 ca thành
8 ca). "B tụt 0,82 xuống 0,68" vì thế là so HAI TẬP CA KHÁC NHAU. Hai ngưỡng
ấy VÔ HIỆU — không phải trượt, không phải đạt, mà là hỏng thước. Thay bằng
thuộc tính CỦA CA: ca SÂU = dòng lỗi nằm trong hàm được gọi từ hàm khác cùng
tệp.

**Đo trên mã đang sửa.** Lần đo bộ 5 đầu tiên ra `0,78` so `0,30` và tôi suýt
báo là "bản sửa làm hỏng nặng". Kiểm lại: hai lượt chạy dùng CÙNG MỘT cỗ máy
(`HEAD` lúc ấy đã chứa cả hai bản sửa), còn thứ khác nhau là **mã nguồn** — bộ
5 gieo lỗi vào `core/the_v1.py` và `core/the_cst.py`, đúng hai tệp tôi đang
sửa để thêm thẻ. Phép đo chép kho hiện tại vào thư mục tạm rồi chạy pytest,
nên hai lượt đã đo hai bản mã khác nhau. Cả hai con số đều vứt.

Đo lại với cây mã đứng yên: **0,56 lên 0,77** — ngược hẳn.

Cùng họ với §4 *"phép đo lấy giờ thật là phép đo xanh theo lịch"*: ở đó phép
đo phụ thuộc ngày chạy, ở đây phụ thuộc **cây mã tại thời điểm chạy**.

## Chỗ đứng sau năm bộ đề

Con số lấy từ bộ chọn KHÔNG theo giả thuyết (bộ 1 đến 4) vẫn là thứ trả lời
"dùng được chưa", và nó chưa đạt: bộ 4 sạch được **0,56**, dưới ngưỡng 0,60.
Bộ 5 đạt 0,77 nhưng là bộ nhắm đích.

Và kho đã **hết tệp độc lập**: 16 tệp đã dùng cho năm bộ; `lat_nguoc` (547
dòng), `redact`, `paths` không có test; `trace_runtime` là chính module đang
được đo nên dùng là vòng tròn. Muốn có bằng chứng độc lập tiếp thì phải viết
test cho `lat_nguoc` hoặc lấy mã ngoài kho.
