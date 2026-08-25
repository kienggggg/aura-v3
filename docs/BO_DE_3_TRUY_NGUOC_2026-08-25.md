# Bộ đề 3 — truy ngược giá trị · 25/08/2026

Ngưỡng đăng ký **trước** khi thấy kết quả, giữ nguyên cả năm con số của bộ 2,
không nới một cái nào.

## Bảng ba bộ

| | trả lời | đúng | **chính xác** | ngưỡng | |
|---|---|---|---|---|---|
| bộ 1 bản cũ | 26/63 | 17 | 0,65 | 0,60 | đạt |
| bộ 1 **bản mới** | 21/63 | 16 | **0,76** | 0,60 | đạt |
| bộ 2 bản cũ | 39/72 | 19 | 0,49 | 0,60 | trượt |
| bộ 2 **bản mới** | 36/72 | 21 | **0,58** | 0,60 | trượt |
| bộ 3 **bản mới** | 59/76 | 27 | **0,46** | 0,60 | **trượt** |

Bản sửa `_moc_bat_dau` giúp cả hai bộ cũ: **0,65 → 0,76** và **0,49 → 0,58**.
Bộ 2 lên là chuyện phải xảy ra — nó chính là bộ đẻ ra bản sửa. Bộ 1 lên mới
là bằng chứng, vì bản sửa không sinh ra từ nó.

Bộ 3 vẫn **0,46**, dưới ngưỡng. Cỗ máy chưa dùng được.

## Vì sao — đo được, không đoán

Tách theo "dòng lỗi có nằm cùng hàm với mốc bắt đầu không". Gộp bộ 1 và bộ 3
(bộ 2 chạy trước khi ghi `dong_moc` nên không tính được):

```
lỗi CÙNG hàm với mốc   42/49 = 0,86
lỗi KHÁC hàm với mốc    1/31 = 0,03
```

Chia đôi rất sạch. Chi tiết từng tệp:

```
bộ 1   dong_ho.py         cùng hàm   6/6  = 1,00
       loai_cau_hoi.py    cùng hàm   4/4  = 1,00
       web_search.py      cùng hàm   3/3  = 1,00   khác hàm  0/1
       may_tinh.py        cùng hàm   2/4  = 0,50   khác hàm  1/3

bộ 3   chat_contract.py   cùng hàm  10/10 = 1,00   khác hàm  0/1
       nho_lai.py         cùng hàm   5/6  = 0,83
       omega.py           cùng hàm  10/12 = 0,83   khác hàm  0/8
       khay_the.py        cùng hàm   2/4  = 0,50   khác hàm  0/18
```

`khay_the.py` 2/22 = 9% được giải thích trọn vẹn: **18 trong 22 ca là khác hàm,
và cả 18 đều trượt.**

## Chỗ hỏng, tới tận dòng mã

Mở một ca ra chạy lại:

- lỗi gieo ở **dòng 43**, trong thân `bo_dau()` — `unicodedata.normalize('NFD', _)`
- test được chốt: `test_sinh_the_tu_ma_that_bo_ham_noi_bo`
- vết **có** đi qua dòng 43 (`trace_toi_dong_loi: True`), 30 dòng đã chạy
- chuỗi đi đủ 21 bước, **cả 21 nằm trong 162–183** — thân `sinh_khay`, quay
  vòng trong vòng `for`, không rời khỏi hàm ấy

Mốc bắt đầu là dòng 183: `return gan_phan_biet(list(ra.values()))`. Muốn tới
dòng 43 phải đi ba tầng `gan_phan_biet` → `_tu` → `bo_dau`.

`_viet_gan_nhat(su_kien, ten, buoc)` tìm **lần ghi gần nhất theo TÊN**, trên
một danh sách sự kiện **phẳng, không có phạm vi hàm**. Cái tên `gan_phan_biet`
ở dòng 183 là một `def`, không phải phép gán — không ai ghi nó trong vết, nên
nhánh ấy tắt ngay bước đầu. Chuỗi quay về thân vòng lặp và đốt hết ngân sách
21 bước tại đó.

**Lời gọi hàm là bức tường kín đối với cỗ máy này.** Cạnh còn thiếu: khi một
biến được gán từ giá trị trả về của hàm định nghĩa trong cùng tệp, phải nhảy
vào sự kiện `tra_ve` của hàm đó rồi truy tiếp từ trong ấy.

## Hai giả định bị chính dữ liệu bác

**Một.** Tôi ghi trước rằng bộ 3 nhiều ca sập hơn (47/76 = 62%, bộ 2 là 38%)
nên có thể "dễ ăn", và hứa tách ra để không nhận vơ. Tách ra đo: `co_ve_sap`
True **47%** so với False **43%**. Chênh 4 điểm — không giải thích nổi khoảng
cách 9% ↔ 91% giữa hai tệp. Giả định sai; cái giải thích được là hình dạng gọi
hàm ở trên.

**Hai.** Quy tắc im lặng ứng viên — "chuỗi chỉ thăm đúng một hàm thì nói không
biết" — tính được mà không cần biết đáp án, nên có vẻ hứa hẹn. Đo trên bộ 1 +
bộ 3: chính xác lên **0,80** nhưng nó **ném đi 31 câu ĐÚNG để giữ lại 12**, độ
phủ tụt còn **15/80 = 0,19**, dưới ngưỡng 0,25. Không đáng làm.

Và luật im lặng hiện hành cũng đã hết thời ở bộ 3: nó vứt **15 câu ĐÚNG** để
chặn **2 câu sai**. Ở bộ 1 tỉ lệ là 15 đúng / 27 sai — đáng. Ở bộ 3 thì có hại.

## Bộ chấm giấu việc nó không đo lại

`do_truy_nguoc_ngoai_ho.py` có cache tiếp-tục: mục nào đã có trong sổ thì bỏ
qua. Sổ đầy đủ thì không đo lại dòng nào — **nhưng vẫn in nguyên bảng năm
ngưỡng, trông y hệt một lần đo mới**. Dấu hiệu duy nhất là một dòng "0 đề" mờ
nhạt ở đầu.

Hôm nay tôi đọc lướt qua đúng cái bảng ấy và suýt báo **"bộ 1 bản MỚI = 0,65"**
— trong khi 0,65 là số đo hôm 24/08 bằng bản CŨ: sổ ghi **11:44:54** hôm trước,
lúc đọc là **07:00** hôm sau. Bắt được vì thấy lần chạy xong trong vài giây
thay vì 6 phút. Đo lại thật thì ra **0,76**, lệch 0,11 so với con số suýt báo.

Cùng họ với §4 *"phép đo không chạy phải NÓI LÀ KHÔNG CHẠY"*: ở đó là giấu
việc không chạy, ở đây là giấu **số này lấy từ hôm nào**. Đã vá: sổ đủ mà
không đo lại thì in `*** KHÔNG ĐO LẠI DÒNG NÀO ***` kèm giờ ghi sổ.

## Bước tiếp

Cho chuỗi bước qua ranh giới hàm. Kích thước phần thưởng: 31 ca khác hàm hiện
đúng **1**; nếu chúng đạt bằng mức cùng hàm (0,86) thì tổng lên khoảng 0,86.
Con số 0,86 ấy là **hy vọng, không phải phép đo** — phải đăng ký ngưỡng trước
rồi dựng **bộ đề 4** trên bốn tệp khác nữa mà đo, không được đo lại trên chính
bộ 1 và bộ 3 đã đẻ ra giả thuyết này.
