# Kế hoạch: từ app THẺ tới tích hợp Delta

**Dựng 20/08/2026** · mọi con số dưới đây đo được trên máy này, có lệnh chạy lại.

---

## 0. Sợi chỉ xuyên suốt

Cả buổi hôm nay đo ra đúng một câu chuyện, và nó không phải câu chuyện ban đầu
tưởng:

```
Delta (model sửa lỗi mã)        2/9      model viết lại TOÀN VĂN hàm rồi ghi đè
Khay thẻ (model tìm hàm)        0/28 -> 24/28
App thẻ (máy sửa mã)            5 cửa ĐẠT, đường thật 9/9
```

Ba mảnh này **chưa nối vào nhau**. Delta vẫn bắt model viết lại cả hàm bằng chữ,
trong khi đã có một bộ máy sửa mã giữ nguyên từng byte và một cái khay biết
hàm nào có sẵn.

**Giả thuyết của kế hoạch này:** Delta trượt không phải vì model dốt, mà vì
**bề mặt sửa quá rộng**. Bắt viết lại cả hàm thì mỗi lượt là một cơ hội làm hỏng
dòng không liên quan. Thu bề mặt lại còn "chọn một thẻ, đổi một ô" thì cái sai
tệ nhất chỉ còn là *giá trị sai trong một ô*, không phải *tệp vỡ*.

Giả thuyết này **chưa được đo**. Cả kế hoạch là để đo nó.

---

## 1. Đang đứng ở đâu — số, không phải cảm giác

### App thẻ: xong phần nền

```
Cửa 1  gõ lại y giá trị cũ    ĐẠT   5.672 thẻ, 100% y hệt byte, 0/68 tệp dính
Cửa 2  chú thích cuối dòng    ĐẠT   31 giữ, 0 mất, kể cả thẻ khối
Cửa 3  Origin                 ĐẠT   16/16 ca tấn công
Cửa 4  đổi thật một ô         ĐẠT   3.544 thẻ, 0 tả sai, phủ 62,8%
Cửa 5  đường THẬT qua HTTP    ĐẠT   9/9, đúng 1 dòng đổi
```

```
venv\Scripts\python.exe -X utf8 tools\do_cua_cung_the.py --cst
venv\Scripts\python.exe -X utf8 tools\do_duong_that.py
```

### Khay thẻ: điểm vận hành vừa dịch chuyển

```
                        trần    chọn đúng   đúng/khi có mặt   giây
docstring cũ, giữ 8     23/28   23/28       23/23 = 100%       271
docstring cũ, giữ 15    25/28   22/28       22/25 =  88%      1008
docstring mới, giữ 8    23/28   22/28       22/23 =  96%       322
docstring mới, giữ 15   26/28   24/28       24/26 =  92%       505   <- tốt nhất
```

Viết docstring **hại ở khay 8, giúp mạnh ở khay 15** — thẻ giờ phân biệt được
nhau thay vì trống trơn. Điểm vận hành chuyển từ 8 sang 15.

### Delta: chưa chạy lại được

`do_delta.py` đọc bộ đề từ `D:\alpha_bench` — **thư mục ấy không có trên máy**.
Bộ đề chạy được là `de_loi.json`: **29 đề đột biến** trên 8 tệp `core/`, chấm
bằng `do_sua_loi.py`, kết quả gần nhất **2/9**.

Kế hoạch này dùng **29 đề của `de_loi.json`**, không dùng `alpha_bench`. Đề nào
không có thì không đếm — "không đo được" khác "trượt".

---

## 2. Chỗ nghẽn ĐÃ ĐO, đừng đi tìm lại

Ba thứ đã đóng hồ sơ trong ngày, ghi ra đây để không ai làm lại:

| đã thử | kết quả | đừng làm lại |
|---|---|---|
| định vị lỗi bằng phổ thực thi | 3 mức, cả 3 TRƯỢT | đột biến `<`→`<=` không tạo đường đi mới, phổ không tách được |
| Needle 2 (45M, tool calling) | 7/28, 25% lượt chết vì tiếng Việt | dưới ngưỡng, và điểm tin cậy mất tín hiệu giữa hai lần chạy |
| đi tìm model tốt hơn cho khay | qwen 24/26 khi đáp án có mặt | model không phải chỗ nghẽn ở bước chọn hàm |

---

## 3. Bốn chặng, mỗi chặng một cửa đặt TRƯỚC

Luật chung: **mỗi chặng viết ngưỡng trước khi đo.** Không đạt thì nói không đạt,
không nới ngưỡng. Ba trạng thái không gộp: *đạt · đo được mà không đạt · không
đo được.*

### CHẶNG A — chốt điểm vận hành khay *(đang chạy)*

Còn thiếu một số: khay 30 (trần 28/28). Nếu 30 > 24/28 thì điểm vận hành lại
dịch, nếu không thì chốt **giữ 15**.

- **Ngưỡng:** chọn cỡ khay có `chọn đúng/28` cao nhất; hoà thì lấy cỡ nhỏ hơn
  (nhanh hơn, ít nhiễu hơn).
- **Xong khi:** ghi cỡ đã chốt vào `khay_the.loc_khay` làm mặc định, kèm bảng số.
- **Ước:** một lượt đo ~8 phút. Còn đúng một lượt.

### CHẶNG B — app thẻ mở được tệp Delta sẽ sửa

App hiện phủ **62,8%** thẻ thật, và `_rang_buoc_cau_truc_va_danh_dau` chỉ cho
**sửa ô của thẻ đã có** — không thêm, không xoá thẻ. Delta cần cả ba.

- **Việc:** mở 8 tệp `core/` mà `de_loi.json` nhắm tới, đo tỉ lệ thẻ thật trên
  đúng 8 tệp ấy (không phải trung bình cả kho — đề chỉ đụng 8 tệp này).
- **Ngưỡng đặt trước:** ≥60% dòng của 8 tệp ấy nằm trong thẻ **thật** (không
  phải `ma_tho`). Dưới 40% thì dừng, vì Delta sẽ chỉ sửa mã thô — tức là quay
  về viết chữ, không được gì.
- **Cửa:** thêm chế độ `--tep core/may_tinh.py ...` cho `do_cua_cung_the.py`.
- **Ước:** nửa ngày máy.

### CHẶNG C — Delta sửa QUA THẺ, không viết lại hàm

Đây là chặng chính. Đổi lời nhắc của `do_delta`/`do_sua_loi` từ *"viết lại toàn
văn hàm"* thành:

```
1. máy đưa: cây thẻ của tệp (đã lọc quanh vùng test báo lỗi) + lỗi pytest
2. model trả: {"id_the": "...", "o": {"dieu_kien": "..."}}    <- MỘT ô
3. máy áp qua API /api/luu_tep, rồi chạy pytest
```

Ba thứ chặn ăn gian giữ nguyên từ `do_delta`: chỉ ghi tệp nguồn, chạy **cả** bộ
test, mỗi đề một bản clone riêng.

- **Ngưỡng đặt trước, trên 29 đề của `de_loi.json`:**

  ```
  nền hiện tại (viết lại hàm)          2/9  =  22%
  >= 8/29  (28%)   -> đi tiếp, hướng đúng
  4..7/29          -> đo được mà không đạt, ghi sổ rồi dừng
  <  4/29          -> đóng hồ sơ, quay về viết lại hàm
  ```

- **Phải đo RIÊNG hai thứ, đừng gộp:**
  - *sửa đúng chỗ* — model chọn đúng thẻ chưa (so với `cho` trong `de_loi.json`)
  - *sửa đúng giá trị* — ô mới có làm test xanh không

  Gộp lại thì không biết nên chữa khay hay chữa model.

- **Ước:** một ngày máy dựng + ~2 giờ mỗi lượt đo 29 đề.

### CHẶNG D — nối khay vào Delta

Chỉ làm **sau khi** C có số. Khay trả lời câu *"hàm nào"*; Delta cần câu
*"sửa ô nào"*. Hai câu khác nhau, và chưa có bằng chứng khay giúp được câu thứ
hai.

- **Việc:** dùng `loc_khay` để chọn thẻ đưa vào ngữ cảnh, thay vì đưa cả cây.
- **Ngưỡng:** phải hơn chặng C **ít nhất 3/29**. Dưới mức đó thì khay chỉ là
  thêm một tầng phức tạp không trả tiền.
- **Cạm bẫy đã biết:** hiệu ứng chen lấn. Ở khay 8, viết thêm 23 docstring làm
  bộ đề **tệ đi 1**. Khay nhỏ mà nhiều thẻ tra được thì thẻ đúng bị đẩy ra.

---

## 4. Cái có thể làm cả kế hoạch này vô nghĩa

Nói trước, không giấu:

1. **Thẻ có thể không tả nổi chỗ cần sửa.** 29 đề là đột biến kiểu `<`→`<=`,
   lật `True/False`, đổi hằng số. Những chỗ ấy nằm trong biểu thức — mà biểu
   thức nhiều dòng đang là `ma_tho`. Nếu phần lớn đề rơi vào `ma_tho` thì
   "sửa qua thẻ" thành "sửa chữ", và chặng C hết nghĩa. **Chặng B đo đúng
   chuyện này, và nó là cửa chặn — không qua thì không sang C.**

2. **Bề mặt hẹp có thể không phải là thứ giúp.** Giả thuyết là model trượt vì
   bề mặt rộng. Cũng có thể nó trượt vì không hiểu lỗi. Nếu chặng C đo ra
   *chọn đúng thẻ nhưng sai giá trị* chiếm phần lớn, thì bề mặt không phải
   vấn đề, và phải đổi hướng.

3. **App thẻ chưa cho thêm/xoá thẻ.** Sửa lỗi thật đôi khi cần thêm một dòng
   `if`. Bản v1 cấm đổi cấu trúc. Nếu chặng C vấp nhiều ở chỗ này thì phải mở
   `_rang_buoc_cau_truc_va_danh_dau`, và mở là mở luôn một lớp rủi ro mới —
   phải có cửa đo riêng trước khi mở.

---

## 5. Thứ tự và ai làm

```
A  chốt cỡ khay          Claude, đang chạy, còn 1 lượt đo
B  phủ thẻ trên 8 tệp    Claude, nửa ngày máy      <- CỬA CHẶN
C  Delta sửa qua thẻ     Claude dựng, ~1 ngày + 2h/lượt đo
D  nối khay vào Delta    chỉ sau khi C có số
```

Song song, **không đụng nhau**:

- Antigravity: đang giữ `the_api.py`, `the_app.py`, `app.js`, `test_the_v1.py`,
  `do_duong_that.py`. Việc còn của họ: trỏ `test_cua_cung_1` sang `the_cst`
  (ở đó nó xanh) hoặc đổi tên cho rõ đây là hồ sơ vì sao bỏ `ast` — để một test
  đỏ vĩnh viễn là dạy người ta bỏ qua màu đỏ.
- Codex: bắt được chỗ bốn cửa không đo app. Việc hợp với Codex tiếp theo là
  **soát chặng C khi có số** — đọc mã và bắt chỗ phép đo tự tin.

---

## 6. Nguồn nhiễu phải xử trước khi tin số nào

**Khay sinh từ chính kho, mà kho đang bị ba AI sửa liên tục.** Trần khay lúc đo
Needle lần đầu là 22/28, một giờ sau là 23/28 — chênh một đề chỉ vì `the_api.py`
đổi docstring.

**Phải ghim khay vào một tệp trước khi so hai bộ lọc.** Chưa làm, và nó là việc
đầu tiên của chặng B. Không có nó thì mọi số so sánh trong kế hoạch này đều
lung lay một đề.

---

## 7. KẾT QUẢ CHẶNG B — và ngưỡng tôi đặt trước đã đo nhầm thứ

```
venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\do_phu_the_delta.py
```

### 7.1 Hai con số, và chúng không nói cùng một điều

```
độ phủ dòng trung bình, tệp đã chuẩn hoá  : 45,7%   -> DƯỚI ngưỡng 60%
chỗ đột biến nằm trong thẻ THẬT           : 28/29 = 97%
mỗi đột biến chạm mấy dòng                : 29/29 đúng MỘT dòng
mỗi đột biến chạm mấy thẻ                 : 29/29 đúng MỘT thẻ
```

**Ngưỡng tôi viết ở mục 3 — "≥60% dòng nằm trong thẻ thật" — đo nhầm thứ.**

Độ phủ trung bình trả lời câu *"bao nhiêu phần của tệp sửa được bằng thẻ"*.
Nhưng câu quyết định là *"chỗ CẦN sửa có nằm trong thẻ không"*, và hai câu ấy
tách nhau rất xa: phủ 45,7% mà 97% chỗ cần sửa vẫn nằm trong thẻ.

Tôi có ghi con số sắc hơn ấy vào lời dặn của bộ đo **trước khi chạy** — *"trung
bình cao mà đúng chỗ cần sửa lại là `ma_tho` thì vẫn hỏng"* — nhưng **không gắn
ngưỡng cho nó**, và để mã thoát dựa vào con số trung bình. Đó là lỗi đặt ngưỡng
của tôi, không phải kết quả xấu của phép đo.

Nên **không tự đổi cửa sau khi thấy số**. Ghi cả hai, và để Sếp quyết.

### 7.2 Đột biến rơi vào loại thẻ nào

```
neu       15      <- điều kiện `if`, đúng thẻ có ô `dieu_kien`
gan        7
tra_ve     5
goi_ham    1
ma_tho     1      <- chỗ duy nhất thẻ không tả nổi
```

15/29 là đổi điều kiện `if` — `<` thành `<=`, lật `not`. Sửa nó qua thẻ là **đổi
đúng một ô `dieu_kien`**. Đây là hình dạng thuận nhất có thể cho hướng thẻ.

Chỗ duy nhất rơi vào mã thô, `user_memory.py:83`:

```python
fact = {'id': f'm-{uuid.uuid4().hex[:9]}', 'text': clean, 'meta': f"{datet...
```

Một `gan` với biểu thức từ điển lồng f-string — bộ đọc hạ xuống mã thô.

### 7.3 Một phát hiện đổi cách hiểu bài toán

`dung_de_loi.dot_bien` trả `ast.unparse(...)`, và `do_sua_loi.py:130` ghi thẳng
bản ấy ra đĩa. **Tệp Delta mở ra không phải tệp trong kho** — nó đã bị chuẩn
hoá, sạch chú thích, biểu thức duỗi thẳng.

Điều đó cắt cả hai chiều:

- Thế mạnh lớn nhất của app thẻ (giữ chú thích, `elif`, chú kiểu) **phần lớn vô
  dụng ở đây** — không còn chú thích nào để giữ.
- Nhưng chuẩn hoá lại **nâng độ phủ**: 40,0% → 45,7%, vì biểu thức nhiều dòng bị
  duỗi thành một dòng. Sáu trên tám tệp tăng; riêng `dong_ho.py` (35,0 → 23,1)
  và `secret_guard.py` (28,7 → 24,1) thì giảm.

### 7.4 Đề nghị

Ba con số `28/29`, `29/29 một dòng`, `29/29 một thẻ` nói rằng **bề mặt sửa thu
được đúng như giả thuyết chặng C cần**. Ngưỡng trung bình 45,7% nói ngược lại,
nhưng nó đo cái khác.

Đề nghị **sang chặng C**, và đổi cửa chặn của chặng B thành:

```
chỗ đột biến nằm trong thẻ thật  >= 80%   -> sang C     (đo được: 97%)
                                  50..79%  -> cân lại
                                  <  50%   -> dừng
```

Ghi rõ đây là **cửa đổi sau khi thấy số**, để người sau biết mà nghi. Lý do đổi
nằm ở 7.1 và có thể tra lại; nếu Sếp thấy không thuyết phục thì giữ nguyên cửa
cũ và dừng ở đây.
