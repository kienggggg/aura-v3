# Nghiệm thu N3 + bốn cửa + một lỗi mới đào ra — 24/08/2026

*N3 đã đạt. Năm ngưỡng thẻ đạt cả năm. Bốn cửa cứng đạt cả bốn, khớp đúng báo
cáo của Antigravity. Nhưng lúc chạy mốc E1 để kiểm điều kiện bảo vệ, ra hai
thứ mới: một cửa test không hỏng được, và một phán quyết E1 sai vì chấm nhầm
bản vá.*

---

## 1. N3 — việc còn mở duy nhất, nay đóng

```
                        trước (23/08)   sau bản vá
khối có biến --cao-cot      0/50           50/50
lệch đáy cột so tâm nhánh   17px            0px
điều kiện                   KHÔNG đụng cửa sổ, đo ngay sau khi mở tệp
```

Mở `core/web_search.py` qua giao diện, không phát sự kiện `resize`, không gọi
tay. `yeuCauChinhCotDoc()` gọi ba lượt (ngay lập tức + hai khung hình lồng
nhau) bắt được lượt render cuối cùng.

## 2. Năm ngưỡng thẻ — `core/web_search.py`, 281 thẻ

```
N1  bề ngang bỏ trống       8%     <= 20%    ĐẠT
N2  cao trung vị           20px    <= 20px   ĐẠT
N3  cột dọc lệch tâm        0px    <=  2px   ĐẠT
N4  số màu nhánh rẽ          5     >=  3     ĐẠT
N5  lỗ lệch viền trái        0px   <=  1px   ĐẠT
```

## 3. Bốn cửa cứng — đối chiếu báo cáo Antigravity

Báo cáo ghi *"ĐẠT cả 4 cửa, exit 0, 86 tệp, 8219 thẻ"*. Lượt chạy của tôi:

```
Cửa 1  8219 thẻ · y byte 100% · ĐỔI NGHĨA ÂM THẦM 0 · VỠ CÚ PHÁP 0 · tệp dính 0/86
Cửa 2  33 dòng chú thích do thẻ thật quản, giữ 33, MẤT 0
Cửa 3  16/16 ca Origin đúng, kể cả evil.com@localhost và 127.0.0.1.evil.com
Cửa 4  5539 thẻ thật, tả sai 0 · phủ kho 67,8% · phủ dòng 64,5%
       dat_het = True trong data/the_v1/cua_cung_cst.json
```

Khớp. Con số `8219` là Cửa 1 (kể cả mảnh `ma_tho`); `5539` là Cửa 4 (chỉ thẻ
thật) — hai nhãn khác nhau, không mâu thuẫn.

## 4. Test

```
venv pytest tests            624 passed, 1 skipped   122,5s   (ngưỡng >= 620)
node test_e1_ui.js             6 pass, 0 fail
node test_the_parity.js       27/27 khớp
node test_the_connector_ui.js  6 pass, 0 fail  (sau khi tôi sửa, xem mục 5)
```

## 5. Cửa test mới KHÔNG HỎNG ĐƯỢC — đã sửa

`test_the_connector_ui.js` có test *"chinhCotDoc và yeuCauChinhCotDoc … gán
biến --cao-cot"*. Nó chỉ khẳng định `!== undefined`. Gieo lỗi thử:

```
gieo lỗi                                       trước sửa   sau sửa
công thức +4 -> +400 (lệch 396px)              xanh 5/5    ĐỎ
bỏ hoàn toàn double rAF (chính là lỗi N3)      xanh 5/5    ĐỎ
chỉ còn một lớp rAF                            —           ĐỎ
```

Hai nguyên nhân: `getBoundingClientRect()` giả trả **cùng một rect** cho mọi
phần tử, nên mọi công thức đều ra một số; và phép so `!== undefined` không nhìn
số ấy.

Đã sửa: rect đặt riêng từng phần tử (khối top 100, nhánh cuối top 300 h20 →
**đúng 214px**), và đếm độ lồng của `requestAnimationFrame` (**phải bằng 2**,
`chinhCotDoc` chạy **3 lần**). `app.js` khôi phục khớp SHA-256 sau khi gieo lỗi.

## 6. Bốn mốc E1 — không xê dịch, nhưng phán quyết thì lật

```
may_tinh.py      65 -> 15    tim_thay
web_search.py    87 -> 28    ung_vien_khong_qua_suite   <- 23/08 là tim_thay
dong_ho.py        1 ->  1    ung_vien_khong_qua_suite   <- 23/08 là tim_thay
loai_cau_hoi.py  10 ->  2    khong_tim_thay             (vẫn TRƯỢT, đúng sổ)
```

**Con số lọc không đổi một lần nào qua ~20 lượt chạy** — ngưỡng bảo vệ đạt.
Nhưng hai phán quyết lật, và lật SAI.

### Bản vá bị chấm không phải bản vá được công bố

E1 ghi vào bản sao tạm trường `ma`, tức `ast.unparse` **cả tệp**. Đo:

```
tệp            diff công bố   khác thật   chú thích     dòng      dòng ma thuật
dong_ho.py         2 dòng      24 dòng      1 -> 0     40 -> 26      MẤT
may_tinh.py        2 dòng     231 dòng     50 -> 0    321 -> 194     MẤT
web_search.py      2 dòng     409 dòng     94 -> 0    563 -> 350     MẤT
```

Người dùng đọc "sửa 2 dòng". Thứ đem đi chấm suite là tệp đã bị **xoá sạch chú
thích và mất dòng `# -*- coding: utf-8 -*-`**.

### Ba bản vá đều ĐÚNG

```
AST(ma)  ==  AST(tệp gốc)      cả 3/3 ca
```

Tức E1 tìm ra đúng chỗ sửa. Suite đỏ **chỉ vì chuẩn hoá**, không vì bản vá.

### Test nào bắt, và vì sao chỉ hai tệp bị

`tests/test_the_cst.py` (mới thêm vòng này) đọc thẳng tệp `core/*.py` từ đĩa:

```
test_chu_thich_the_in_web_search       đòi core/web_search.py >= 80 thẻ chu_thich
                                       -> chuẩn hoá còn 0 -> ĐỎ
test_dong_ma_thuat_khong_thanh_chu_thich đòi core/dong_ho.py giữ dòng ma thuật
                                       -> chuẩn hoá mất dòng 1 -> ĐỎ
core/may_tinh.py                       không test nào đọc -> tim_thay sống sót
```

Worker chạy pytest có cờ `-x`, nên dừng ở lỗi đầu tiên, rồi mọi ứng viên bị gán
`full_suite_status = ĐỎ`.

**Không mất dữ liệu:** giao diện E1 **không có nút áp dụng** — chỉ hiện
`unified_diff`. Trường `ma` không bao giờ ghi ra đĩa thật.

## 7. Hai chỗ nhỏ cùng lượt

```
tools/do_cua_cung_e1_app.py   sập UnicodeEncodeError cp1252 ngay dòng in đầu
                              (chạy được khi đặt PYTHONIOENCODING=utf-8)
cùng tệp                      cửa CDP quá 120s vì không mở được trình duyệt;
                              mã thoát 1 — nhưng bốn mốc E1 đã chạy xong trước đó
_worker_e1_exec.py:346        so_test_hong = max(1, count("FAILED") or 1)
                              -> suite không chạy được vẫn báo "1 test khác hỏng"
```

Dòng cuối cùng là họ hàng của luật *"phép đo không chạy phải NÓI LÀ KHÔNG
CHẠY"*: số 1 ấy không đo được từ đâu cả.

## 8. Còn mở

```
E1 ghi ast.unparse thay vì vá đúng một dòng          -> xin sửa
so_test_hong bịa số 1 khi không đọc được kết quả     -> xin sửa
do_cua_cung_e1_app.py sập cp1252                     -> xin sửa
data/evidence_sprint/e1_ngoai_ho.json bị .gitignore  -> Sếp quyết có theo dõi không
```
