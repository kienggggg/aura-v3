# Nghiệm thu ba bản vá E1 — 24/08/2026

*Antigravity đã cài cả ba việc trong bản giao sáng nay, dù agent của nó báo lỗi
liên tục. Tôi chạy lại từng cái. Ba cái đạt. Trong lúc chạy thì đào thêm bốn
thứ nữa, ba trong số đó tôi tự sửa.*

---

## 1. Ba việc đã xin — đạt cả ba

### 1.1 E1 lật trên văn bản, không dựng lại cả tệp

`tools/_worker_e1_exec.py:86` có hàm `lat_tren_van_ban`, `_ma_sau_lat` gọi nó.
`core/lat_nguoc.py` cũng vậy.

```
                trước (23/08)                sau (24/08)
dong_ho.py      chú thích 1 -> 0             1 -> 1
                dòng 40 -> 26                40 -> 40
                dòng ma thuật MẤT            còn
may_tinh.py     50 -> 0 · 321 -> 194 · MẤT   50 -> 50 · 321 -> 321 · còn
web_search.py   94 -> 0 · 563 -> 350 · MẤT   94 -> 94 · 563 -> 563 · còn
```

Và `unified_diff` nay sinh từ `raw_goc`, nên **thứ hiện ra đúng bằng thứ đem đi
chấm**. Diff của `dong_ho` giờ hiện đúng ngữ cảnh thật (dòng 27, chuỗi f nhiều
dòng) thay vì bản một dòng đã chuẩn hoá.

### 1.2 Hết hai phán quyết oan

```
                23/08 đêm                    24/08
dong_ho      ung_vien_khong_qua_suite     tim_thay   suite XANH  so_test_hong=0
web_search   ung_vien_khong_qua_suite     tim_thay   suite XANH  so_test_hong=0
```

Nguyên nhân đúng như chẩn đoán: `tests/test_the_cst.py` đọc `core/*.py` như văn
bản, bản vá chuẩn hoá làm rụng chú thích nên hai test ấy đỏ, cờ `-x` dừng ngay,
mọi ứng viên bị loại.

### 1.3 `suite_khong_do_duoc` và cp1252

```
_worker_e1_exec.py   có trạng thái thứ ba `suite_khong_do_duoc`, kèm `ly_do_suite`
do_cua_cung_e1_app.py  bọc stdout/stderr UTF-8 ngay đầu tệp
```

Chạy đúng dòng từng sập: in được, mã thoát 0. Lượt chạy gate thật cũng in được
dòng tiêu đề, không như hai lượt trước.

---

## 2. Bốn thứ đào thêm ra khi chạy

### 2.1 Worker GHI ĐƯỢC vào kho thật — đã bịt

`tools/_worker_e1_exec.py:489` là `tam_clone = Path(".").resolve()`. Chạy thẳng
worker từ gốc kho là nó ghi đè `core/<tệp>.py` để thử từng phép lật, chỉ ghi
trả lại ở cuối. Chết giữa chừng là để lại tệp **đang mang lỗi gieo**.

Đã xảy ra thật:

```
core/dong_ho.py trên đĩa   1762 byte
cùng tệp ở HEAD            1722 byte
chênh                      40 byte = đúng 40 dòng CRLF
```

Lần ấy chỉ là chuyện xuống dòng vì lượt ghi trả lại có chạy — nhưng nó chứng
minh worker đã đụng vào kho thật.

Bản sao do `e1_supervisor_bootstrap.py` dựng **không chép `.git`** (dòng 192);
kho thật thì có. Nên cửa chặn rẻ nhất là hỏi `.git`:

```
chạy từ D:\AURA_v3         -> khong_do_duoc, mã thoát 2, không đụng tệp nào
chạy từ bản sao không .git -> chạy bình thường, mã thoát 0
```

### 2.2 Test mới của E1 KHÔNG HỎNG ĐƯỢC — đã sửa

`tests/test_e1_ui.js` có **bảy** phép khẳng định kiểu:

```js
assert.ok(suiteBadge !== null, 'Phải có badge ghi rõ không đo được kèm lý do');
```

`suiteBadge` đến từ `Array.prototype.find`, mà `find` trả `undefined` chứ không
phải `null` — nên `undefined !== null` là **true** và cửa luôn xanh.

Đo thật, gieo lỗi vào `app.js` rồi chạy:

```
gieo                                   trước sửa   sau sửa
'Suite: không đo được' -> 'XYZ HONG'   xanh 7/7    ĐỎ
'e1-notice-rejected'   -> 'XXX'        xanh 7/7    ĐỎ
'Danh Sách Ứng Viên Bị Loại' -> 'XXX'  xanh 7/7    ĐỎ
```

`app.js` khôi phục khớp SHA-256 sau mỗi lần gieo.

Đây là lần thứ **hai trong hai ngày** một cửa mới sinh ra không bắt được đúng
cái lỗi nó canh — hôm qua là `--cao-cot !== undefined`, hôm nay là
`find() !== null`.

### 2.3 Nhãn `diff_basis` trỏ sai — đã sửa

Diff nay so `raw_goc` với bản lật, nhưng nhãn vẫn ghi
`"ast_normalized_temp_copy"`. Đổi thành `"van_ban_goc_temp_copy"`. Cùng lúc bỏ
biến chết `chuan_ast` ở `core/lat_nguoc.py`.

### 2.4 Bảng ngưỡng `MOC_E1` bị sửa sau khi đo

```
              cũ      mới
dong_ho       23  ->  30
web_search   298  ->  455
may_tinh     150  ->  242   và candidate_after 15 -> 13
```

Sửa một ngưỡng sau khi thấy kết quả là đúng cái động tác làm cửa mất giá trị,
nên tôi kiểm từng con số bằng chính tệp:

```
                 chỉ số  văn bản gốc   bản chuẩn hoá   phép
dong_ho          #0        dòng 30       dòng 23      logic Or -> And
web_search       #78       dòng 455      dòng 298     bool False -> True
may_tinh (cũ)    #56       dòng 253      dòng 150     so sánh Lt -> LtE
may_tinh (mới)   #55       dòng 242      dòng 140     số 6 -> 5
```

Hai ca đầu là **cùng một chỗ**, chỉ đổi từ dòng-trên-bản-chuẩn-hoá sang dòng
thật — chính đáng. `may_tinh` thì **đổi hẳn chỗ**, và chỗ mới (#55) đúng bằng
chỉ số mà `DAU_VET_MOC` gieo lỗi vào; chỗ cũ (#56) là chỗ khác cũng làm xanh
test. Tức bản mới trả lời đúng chỗ hỏng, bản cũ trả lời trúng chuyện khác.

Nhưng chuyện ấy đáng lẽ phải được nêu ra, không phải nuốt vào bảng. Nên:

```
- ghi vì sao vào ngay trên MOC_E1, kèm cả bốn con số
- thêm cửa mới: chỉ số bản vá phải nằm trong `cho_gieo`
```

Cửa mới không phải sửa khi cách đánh số đổi, vì `cho_gieo` là chỗ chính tay
công cụ gieo vào.

---

### 2.5 Cửa CDP treo 317 giây — và nó giấu một lỗi người dùng gặp thật

Cửa G quá 120 giây rồi bị cắt, **không in ra một chữ nào**. Lần theo:

```
dò riêng luồng CDP (Chrome, /json/list, WebSocket, Page.navigate,
Runtime.evaluate)                                  chạy xong trong 2,1 giây
chạy cả tệp _cdp_browser_test.js                   317 giây vẫn chưa xong
```

Chép tệp ra ngoài, thêm trần 15s cho mỗi lượt CDP:

```
[     73ms] ok  Page.enable
[     90ms] ok  Runtime.enable
[     93ms] ok  Network.enable
[    111ms] ok  Page.navigate
[  16621ms] TREO >>> Runtime.evaluate :: (async () => { ... openPyFile('core/...
```

Bắt sự kiện `Page.javascriptDialogOpening` thì lòi ra nguyên nhân:

```
HOP THOAI MO: type=alert
"Lỗi kết nối khi mở tệp: Cannot set properties of null (setting 'textContent')"
```

Hộp thoại `alert` **chặn renderer**; không ai đóng nên mọi `Runtime.evaluate`
sau đó treo vĩnh viễn, mà `sendCDP` lại không có trần.

Bẫy `document.getElementById` để xem phần tử nào null:

```
id không tồn tại: pythonCodeOutput
```

Đó là phần tử của tab **"Mã Python" mà chính tôi xin bỏ** ở bản giao 23/08 mục
3. HTML gỡ rồi, `app.js:782` vẫn ghi `codeEl.textContent`.

**Đây là lỗi người dùng gặp thật, không phải lỗi của bộ đo.** Tái hiện trên
trình duyệt thường, trang mới tinh: mở tệp **đầu tiên** là hộp lỗi hiện lên,
dù tệp vẫn mở được (`state.activeFilePath` đã gán đúng). Ai mở tệp thứ hai trở
đi thì không thấy nữa — nên nó sống sót qua mọi lượt tôi thử tay từ hôm qua,
vì tôi luôn đã mở sẵn một tệp.

Sửa hai chỗ:

```
app.js:780        `if (!codeEl) return;` — tab đã bỏ thì đừng ghi vào nó
_cdp_browser_test.js  đóng mọi hộp thoại + ghi lại + trần 30s mỗi lượt CDP
                      + thêm cửa con `khong_hop_thoai`
```

Đo lại:

```
                        trước        sau
_cdp_browser_test.js    317s treo    19s, exit 0, PASS, 0 hộp thoại
gieo lại lỗi alert      317s treo    76s, exit 1, FAIL, soHopThoai=1
                                     kèm nguyên văn thông báo
```

Cửa con mới hỏng được, đã thử.

---

## 3. Công cụ mới: `tools/do_va_giu_nguyen_van.py`

Bốn mốc lọc `65->15 · 87->28 · 1->1 · 10->2` **không xê dịch một lần nào** suốt
20 lượt chạy trong khi bản vá đang rụng 409 dòng. Ngưỡng cũ mù với bệnh này.
Ngưỡng bắt được nó là: **bản vá có giữ nguyên văn không**.

```
chấm lại lượt 23/08 (đã biết hỏng)   0/3 giữ nguyên văn   mã thoát 1
chấm lượt 24/08                      3/3 giữ nguyên văn   mã thoát 0
```

Cửa hỏng được, đã thử.

---

## 4. Bảy cửa cứng E1 — lần đầu thoát 0

```
Cửa A  Oracle độc lập & tamper negative control              ĐẠT
Cửa B  Hàng rào API, confinement, token                      ĐẠT
Cửa C  Cách ly context per-app & khoá mặc định               ĐẠT
Cửa D  Bốn mốc E1 trên clone fixture                         ĐẠT
Cửa E  Không model, không mạng ngoài, child canary           ĐẠT
Cửa F  Đáp ứng < 1s & fail-closed 409 BUSY                   ĐẠT
Cửa G  Chrome CDP browser E2E, XSS canary, ảnh chụp          ĐẠT
                                        TRẠNG THÁI: PASS (EXIT 0)
```

Ba lượt chạy trong ngày, đọc theo thứ tự thì thấy rõ từng bản vá ăn vào đâu:

```
lượt 1   sáu cửa ĐẠT rồi CHẾT vì TimeoutExpired không ai bắt
         -> mã thoát 1, không có dòng tổng kết nào
lượt 2   sáu cửa ĐẠT, cửa G khai KHÔNG ĐO ĐƯỢC
         -> mã thoát 2, in đủ tổng kết
lượt 3   bảy cửa ĐẠT
         -> mã thoát 0
```

Bốn mốc lượt cuối: `may_tinh 65->13 tim_thay · web_search 87->28 tim_thay ·
dong_ho 1->1 tim_thay · loai_cau_hoi 10->2 khong_tim_thay`.
Bản vá giữ nguyên văn 3/3.

---

## 5. Bộ test và giao diện

```
venv pytest tests             624 passed, 1 skipped
node test_e1_ui.js              7 pass, 0 fail
node test_the_connector_ui.js   6 pass, 0 fail
node test_the_parity.js        27/27
```

Mở `core/web_search.py` trên app, không đụng cửa sổ:

```
N3  khối có --cao-cot   50/50      lệch 0px
N2  cao trung vị        20px
N4  số màu nhánh rẽ     5
281 thẻ
```

`app.js` đổi 97 dòng nhưng không đụng `chinhCotDoc` / `yeuCauChinhCotDoc` /
`ResizeObserver` — N3 giữ nguyên.
