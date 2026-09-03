# Gửi Antigravity — nghiệm thu ba bản vá E1 (không có việc phải làm)

*24/08/2026. Ba việc bản giao sáng nay: cài đúng cả ba, tôi chạy lại từng cái.
Bảy cửa cứng lần đầu thoát 0.*

**Bản giao này KHÔNG có việc phải làm.** Bên bạn hết lượt nên việc cuối tôi làm
luôn. Đây là báo lại số liệu và nói rõ tôi đã đổi những gì — để bên bạn khỏi
lùi về bản cũ khi có lượt trở lại.

---

## 0. Ba việc — ĐẠT cả ba, đừng làm lại

### Bản vá E1 giữ nguyên văn

```
                trước (23/08)                sau (24/08)
dong_ho.py      chú thích 1 -> 0             1 -> 1
                dòng 40 -> 26                40 -> 40
                dòng ma thuật MẤT            còn
may_tinh.py     50 -> 0 · 321 -> 194 · MẤT   50 -> 50 · 321 -> 321 · còn
web_search.py   94 -> 0 · 563 -> 350 · MẤT   94 -> 94 · 563 -> 563 · còn
```

`unified_diff` nay sinh từ `raw_goc`, nên **thứ hiện ra đúng bằng thứ đem đi
chấm**. Diff của `dong_ho` hiện đúng ngữ cảnh thật (dòng 27, chuỗi f nhiều dòng).

### Hết hai phán quyết oan

```
             23/08 đêm                     24/08
dong_ho      ung_vien_khong_qua_suite   -> tim_thay, suite XANH, so_test_hong=0
web_search   ung_vien_khong_qua_suite   -> tim_thay, suite XANH, so_test_hong=0
```

### `suite_khong_do_duoc` và cp1252

Cả hai xong. Dòng `print` từng sập cp1252 nay in được, mã thoát 0.

### Bảy cửa cứng — ba lượt trong ngày

```
lượt 1   sáu cửa ĐẠT rồi CHẾT vì TimeoutExpired không ai bắt   thoát 1
lượt 2   sáu cửa ĐẠT, cửa G khai KHÔNG ĐO ĐƯỢC                thoát 2
lượt 3   BẢY CỬA ĐẠT                                          thoát 0
```

Bốn mốc lượt cuối: `may_tinh 65->13 · web_search 87->28 · dong_ho 1->1 ·
loai_cau_hoi 10->2 khong_tim_thay`. Bản vá giữ nguyên văn 3/3.

---

## 1. Năm chỗ tôi sửa thêm — nói để bên bạn khỏi lùi lại

### 1.1 Worker GHI ĐƯỢC vào kho thật

`tools/_worker_e1_exec.py:489` là `tam_clone = Path(".").resolve()`. Chạy thẳng
worker từ gốc kho là nó ghi đè `core/<tệp>.py` để thử từng phép lật, chỉ ghi trả
lại ở cuối. Chết giữa chừng là để lại tệp **đang mang lỗi gieo**.

Đã xảy ra thật:

```
core/dong_ho.py trên đĩa   1762 byte
cùng tệp ở HEAD            1722 byte
chênh                      40 byte = đúng 40 dòng CRLF
```

Lần ấy lượt ghi trả lại có chạy nên không mất gì, nhưng nó chứng minh worker đã
đụng vào kho thật.

Bản sao do `e1_supervisor_bootstrap.py` dựng **không chép `.git`** (dòng 192);
kho thật thì có. Nên cửa chặn là hỏi `.git`:

```
chạy từ D:\AURA_v3          -> khong_do_duoc, mã thoát 2, không đụng tệp nào
chạy từ bản sao không .git  -> chạy bình thường, mã thoát 0
```

### 1.2 Bảy phép khẳng định RỖNG trong `tests/test_e1_ui.js`

```js
assert.ok(suiteBadge !== null, 'Phải có badge ghi rõ không đo được kèm lý do');
```

`suiteBadge` đến từ `Array.prototype.find`. **`find` trả `undefined`, không phải
`null`** — nên `undefined !== null` là `true` và cửa luôn xanh.

Gieo lỗi vào `app.js` rồi chạy:

```
gieo                                   trước sửa   sau sửa
'Suite: không đo được' -> 'XYZ HONG'   xanh 7/7    ĐỎ
'e1-notice-rejected'   -> 'XXX'        xanh 7/7    ĐỎ
'Danh Sách Ứng Viên Bị Loại' -> 'XXX'  xanh 7/7    ĐỎ
```

Sửa: bỏ `!== null`, để `assert.ok(x, ...)` — kiểm truthy thì bắt cả `undefined`
lẫn `null`.

### 1.3 Nhãn `diff_basis` trỏ sai

Diff nay so `raw_goc` với bản lật văn bản, nhưng nhãn vẫn ghi
`"ast_normalized_temp_copy"`. Đổi thành `"van_ban_goc_temp_copy"` ở cả hai tệp,
bỏ luôn biến chết `chuan_ast` ở `core/lat_nguoc.py`.

### 1.4 Bảng ngưỡng `MOC_E1` bị sửa sau khi đo

```
              cũ      mới
dong_ho       23  ->  30
web_search   298  ->  455
may_tinh     150  ->  242   và candidate_after 15 -> 13
```

Sửa một ngưỡng sau khi thấy kết quả là **đúng cái động tác làm cửa mất giá trị**.
Tôi kiểm từng con số bằng chính tệp trước khi kết luận:

```
                 chỉ số  văn bản gốc   bản chuẩn hoá   phép
dong_ho          #0        dòng 30       dòng 23      logic Or -> And
web_search       #78       dòng 455      dòng 298     bool False -> True
may_tinh (cũ)    #56       dòng 253      dòng 150     so sánh Lt -> LtE
may_tinh (mới)   #55       dòng 242      dòng 140     số 6 -> 5
```

Hai ca đầu là **cùng một chỗ**, chỉ đổi từ dòng-trên-bản-chuẩn-hoá sang dòng
thật — chính đáng, giữ. `may_tinh` thì **đổi hẳn chỗ**, và chỗ mới (#55) đúng
bằng chỉ số `DAU_VET_MOC` gieo lỗi vào; chỗ cũ (#56) là chỗ khác cũng làm xanh
test. Bản mới trả lời đúng chỗ hỏng — tốt hơn thật.

**Nhưng chuyện ấy đáng lẽ phải nêu ra, không nuốt vào bảng.** Nên tôi:

```
- ghi vì sao ngay trên MOC_E1, kèm cả bốn con số
- thêm cửa mới: chỉ số bản vá phải nằm trong `cho_gieo`
```

Cửa mới **không phải sửa** khi cách đánh số đổi, vì `cho_gieo` là chỗ chính tay
công cụ gieo vào. Đó mới là cửa thật; bảng `target_line` chỉ là số phụ.

**Luật rút ra:** một ngưỡng phải sửa mỗi lần đổi cách đánh số thì không canh
được gì. Nếu buộc phải sửa, ghi lý do vào ngay chỗ ấy — người sau đọc lịch sử
mà thấy ngưỡng bị đổi sau khi đo, không có lời giải thích, thì sẽ đọc thành nới
tay, và đọc thế là hợp lý.

### 1.5 Công cụ mới `tools/do_va_giu_nguyen_van.py`

Bốn mốc lọc `65->15 · 87->28 · 1->1 · 10->2` **không xê dịch một lần nào** suốt
20 lượt chạy trong khi bản vá đang rụng 409 dòng. Ngưỡng cũ mù hẳn với bệnh ấy.

```
chấm lại lượt 23/08 (đã biết hỏng)   0/3 giữ nguyên văn   mã thoát 1
chấm lượt 24/08                      3/3 giữ nguyên văn   mã thoát 0
```

Cửa hỏng được, đã thử. Chạy:

```bash
venv/Scripts/python.exe tools/do_va_giu_nguyen_van.py
```

---

## 2. Một lỗi NGƯỜI DÙNG GẶP THẬT, tìm ra từ chỗ không ngờ

Cửa CDP quá 120 giây, **không in ra một chữ nào**. Lần theo:

```
dò riêng luồng CDP (Chrome, /json/list, WebSocket, navigate, evaluate)
                                                   xong trong 2,1 giây
chạy cả tệp _cdp_browser_test.js                   317 giây vẫn chưa xong
chép ra ngoài, thêm trần 15s mỗi lượt CDP:
    [   111ms] ok  Page.navigate
    [ 16621ms] TREO >>> Runtime.evaluate :: ... openPyFile('core/dong_ho.py')
bắt Page.javascriptDialogOpening:
    HOP THOAI MO: type=alert
    "Lỗi kết nối khi mở tệp: Cannot set properties of null (setting 'textContent')"
bẫy document.getElementById xem cái nào trả null:
    id không tồn tại: pythonCodeOutput
```

`pythonCodeOutput` là phần tử của tab **"Mã Python" đã bỏ ở vòng ba cột 23/08**.
HTML gỡ rồi, `app.js:782` vẫn ghi `codeEl.textContent`.

**Đây là lỗi người dùng gặp, không phải lỗi của bộ đo.** Tái hiện trên trình
duyệt thường, trang mới tinh: mở tệp **đầu tiên** là hộp lỗi hiện lên, dù tệp
vẫn mở được (`state.activeFilePath` gán đúng). Mở tệp thứ hai trở đi thì không
thấy nữa — nên nó sống sót qua mọi lượt tôi thử tay từ hôm qua, vì tôi luôn đã
mở sẵn một tệp.

Và trong Chrome headless thì `alert` **chặn renderer**; không ai đóng nên mọi
`Runtime.evaluate` sau đó treo vĩnh viễn, mà `sendCDP` lại không có trần.

Đã sửa hai chỗ:

```
app.js:780             `if (!codeEl) return;`
_cdp_browser_test.js   tự đóng mọi hộp thoại + ghi lại + trần 30s mỗi lượt CDP
                       + cửa con mới `khong_hop_thoai`
```

Đo lại:

```
                        trước        sau
_cdp_browser_test.js    317s treo    19s, exit 0, PASS, 0 hộp thoại
gieo lại lỗi alert      317s treo    76s, exit 1, FAIL, soHopThoai=1
                                     kèm nguyên văn thông báo
```

**Luật rút ra:** gỡ một phần tử khỏi HTML thì phải tìm mọi chỗ ghi vào nó. Ở đây
chính tôi là người xin bỏ tab ấy, nên đây cũng là thiếu sót của tôi ở khâu
nghiệm thu — tôi kiểm "tab đã biến khỏi cột phải chưa", không kiểm "còn ai gọi
tới nó không".

---

## 3. Bài học lặp lại HAI NGÀY LIÊN TIẾP

```
23/08   assert.ok(khoi.style['--cao-cot'] !== undefined)
        FakeDOM trả CÙNG một rect cho mọi phần tử
        -> gieo lệch 396px: xanh · gieo bỏ double rAF: xanh

24/08   assert.ok(suiteBadge !== null)  với suiteBadge từ find()
        find trả undefined, không phải null
        -> gieo đổi chữ badge: xanh 7/7
```

Hai lần, hai chỗ, một bệnh: **cửa mới sinh ra không bắt được đúng cái lỗi nó
canh.**

Xin thêm đúng một bước vào quy trình, tốn ba giây:

```
Viết xong một bộ test mới -> GIEO một lỗi thật vào mã nó canh -> chạy lại.
Không đỏ thì cửa ấy chưa dùng được.
```

Không phải đọc lại kỹ hơn. Đọc kỹ không bắt được `find` trả `undefined` — tôi
đọc qua bảy dòng ấy hai lần vẫn không thấy. Gieo một lỗi thì thấy ngay.

---

## 4. VIỆC XIN — ĐÃ TỰ LÀM XONG, KHÔNG PHẢI LÀM LẠI

*Bên bạn hết lượt nên tôi làm luôn. Giữ mục này lại để bên bạn biết đã đổi gì
và vì sao, đừng lùi về bản cũ.*

### Hai bản sao của cùng một máy E1

`core/lat_nguoc.py` và `tools/_worker_e1_exec.py` dùng chung 14 tên hàm/lớp. Đo
bằng AST, bỏ docstring:

```
trùng tên                     14
GIỐNG HỆT TỪNG NÚT AST        13
còn khác thật                  1  -> _chon_test_va_dong
```

Danh sách 13 cái giống hệt:

```
_Lat · __init__ · _lay · _liet_ke_cho · _ma_sau_lat · _tao_unified_diff
doc_thong_tin_gioi_han · lat_tren_van_ban · tao_cac_ung_vien
visit_BoolOp · visit_Compare · visit_Constant · visit_UnaryOp
```

Hôm nay **cả hai đều phải nhận đúng một bản vá** (`lat_tren_van_ban`,
`suite_khong_do_duoc`, `diff_basis`). Bên bạn làm đủ cả hai — nhưng đó là nhờ
cẩn thận, không nhờ cấu trúc. Lần sau sửa một bên quên bên kia thì:

```
core/lat_nguoc.py  <- experiments/evidence_sprint/do_e1_ngoai_ho.py dùng
                      (chính là bộ sinh con số "0/64 ngoài họ")
tools/_worker_e1_exec.py  <- app thật dùng
```

Tức app đo một đằng, sổ bằng chứng đo một nẻo, mà **không ai báo**.

### Đã làm: XOÁ bản sao, không thêm test canh

Hai đường đi được:

```
a) giữ hai tệp, thêm test so AST 13 tên ấy, lệch là ĐỎ
b) xoá hẳn bản sao, hai bên dùng chung một định nghĩa
```

Chọn **(b)**. Test canh thì vẫn là một cửa phải bảo trì, và cửa nào cũng có thể
hỏng theo kiểu mục 3. Xoá bản sao thì lệch trở thành **không thể**, không còn gì
để canh.

```
tools/_worker_e1_exec.py   550 -> 389 dòng (bớt 161)
                           import 5 tên thật sự dùng từ core.lat_nguoc:
                           PHAM_VI_PHEP · _liet_ke_cho · _ma_sau_lat
                           _tao_unified_diff · doc_thong_tin_gioi_han
trùng tên còn lại          1 -> _chon_test_va_dong (cái khác thật, giữ nguyên)
```

Năm tên còn lại (`NGHICH_SS` · `OP_STR` · `_Lat` · `lat_tren_van_ban` ·
`tao_cac_ung_vien`) chỉ được dùng **bên trong** khối vừa xoá, nên không import.

### Nghiệm thu bằng đúng ngưỡng đã đặt

Gieo `tok.start[1]` thành `tok.start[1] + 1` ở **đúng một tệp**
(`core/lat_nguoc.py`):

```
đường app (tools/_worker_e1_exec)      VỠ CÚ PHÁP  now oanddatetime...
đường sổ bằng chứng (core.lat_nguoc)   VỠ CÚ PHÁP
```

Trước khi xoá bản sao thì gieo một bên, bên kia **im lặng**. `core/lat_nguoc.py`
khôi phục khớp SHA-256 sau khi gieo.

Chạy lại toàn bộ sau khi xoá:

```
bảy cửa cứng E1          ĐẠT cả bảy, exit 0
bốn mốc                  65->13 · 87->28 · 1->1 · 10->2 khong_tim_thay
giữ nguyên văn bản vá    3/3, exit 0
pytest                   624 passed, 1 skipped
node                     7/7 · 6/6 · 27/27
ba đường experiments     do_e1_ngoai_ho · dung_de_ngoai_ho · do_may_do_model_chot
                         vẫn import được
```

---

## 5. Lệnh nghiệm thu — đã chạy trước khi gửi

```bash
venv/Scripts/python.exe tools/do_cua_cung_e1_app.py
```
→ `TRẠNG THÁI CUỐI CÙNG: PASS (EXIT 0)`, bảy cửa ĐẠT.

```bash
venv/Scripts/python.exe tools/do_va_giu_nguyen_van.py
```
→ `3/3 giữ nguyên văn, ĐẠT, exit 0`.

```bash
venv/Scripts/python.exe -m pytest tests -q
```
→ `624 passed, 1 skipped`.

```bash
node tests/test_e1_ui.js
```
→ `pass 7, fail 0`. Cùng với `test_the_connector_ui.js` 6/6 và
`test_the_parity.js` 27/27.

Giao diện: mở `core/web_search.py`, không đụng cửa sổ → N3 `50/50` khối, lệch
`0px`, 281 thẻ, cao trung vị 20px, 5 màu nhánh rẽ. `app.js` đổi 97 dòng nhưng
không đụng `chinhCotDoc` / `yeuCauChinhCotDoc` / `ResizeObserver`.
