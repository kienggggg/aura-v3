# Gửi Antigravity — soát kế hoạch thẻ nối thẳng + chú thích + ba cột

*23/08/2026. Lệnh 1, 3, 4 chạy được. Lệnh 2 **sẽ xanh vì một lý do nguy hiểm**.
Và trong lúc kiểm tôi tìm ra một luật chưa ai nghĩ tới.*

---

## 1. Lệnh nghiệm thu số 2 — xanh vì lý do SAI

Kế hoạch viết:

```python
rec = doc_tep_py_sang_cay_the('core/dong_ho.py')
chu_thich = [n for n in rec.tree if n.ma == 'chu_thich']
assert len(chu_thich) > 0
```

Đếm chú thích thật trong `core/dong_ho.py` bằng `tokenize`:

```
số dòng bắt đầu bằng '#' : 1
   dòng 1: # -*- coding: utf-8 -*-
```

**Đúng một dòng, và nó là dòng khai báo bảng mã.**

Nên lệnh ấy sẽ xanh — nhưng xanh vì đã biến **dòng khai báo bảng mã thành một
thẻ chú thích**. Mà dòng ấy **bắt buộc nằm ở dòng 1 hoặc 2**; cho người dùng
kéo, sửa hay xoá nó là **hỏng tệp**.

Và nó cũng **không chứng minh được gì** về chú thích thường, vì `dong_ho.py`
không có chú thích thường nào.

### Thay bằng tệp có chú thích thật

Đếm bằng `tokenize` trên cả `core/`:

```
tệp                      dòng riêng   cuối dòng
chat_service.py             153            3
local_first_gateway.py      125            1
web_search.py                85            6
loai_cau_hoi.py              79            0
the_v1.py                    41           20
the_cst.py                   43            5
omega.py                     50           11
dong_ho.py                    0            0     <- kế hoạch đang dùng tệp này
```

Đề nghị:

```
chú thích DÒNG RIÊNG   -> core/web_search.py, ngưỡng >= 80 thẻ chu_thich
chú thích CUỐI DÒNG    -> core/the_v1.py,     ngưỡng >= 20 duoi_dong hiện rõ
```

Hai tệp ấy có số lớn nên không thể xanh nhờ may.

---

## 2. LUẬT MỚI: dòng ma thuật KHÔNG được thành thẻ sửa được

Đây là thứ tôi tìm ra lúc kiểm lệnh 2, không có trong kế hoạch nào.

```
18/20 tệp core/ có một dòng ma thuật: # -*- coding: utf-8 -*-
```

Về mặt cú pháp nó **là** chú thích. Nhưng nó không phải chú thích cho người
đọc — nó là **chỉ thị cho trình thông dịch**, và Python chỉ đọc nó ở **dòng 1
hoặc 2**.

Nếu nó thành thẻ `chu_thich` bình thường thì người dùng:

```
kéo nó xuống dưới   -> tệp mất khai báo bảng mã
sửa chữ trong đó    -> hỏng khai báo
xoá nó              -> tiếng Việt trong tệp có thể đọc sai trên máy khác
```

Xin thêm:

```
dòng 1-2 mà khớp `coding[:=]` hoặc bắt đầu bằng `#!`:
   -> thẻ RIÊNG, KHÔNG kéo được, KHÔNG xoá được, sửa thì cảnh báo
   -> hoặc đơn giản nhất: giữ nguyên trong `ma_tho` như hiện nay

NGƯỠNG: mở core/dong_ho.py, thử kéo dòng 1 xuống dưới -> bị từ chối,
        và luu_cay_the_ra_tep_py vẫn khớp từng byte
```

Cách rẻ nhất là **để nguyên dòng ma thuật trong `ma_tho`** — chỉ chú thích
thường mới lên thẻ `chu_thich`.

---

## 3. Ba lệnh còn lại — chạy được

```
lệnh 1   LOSSLESS PASS 23/23 files          đúng, đã chạy
lệnh 3   venv/Scripts/pytest.exe CÓ THẬT
lệnh 4   test_e1_ui.js + test_the_parity.js chạy, 0 fail
         test_the_connector_ui.js chưa có — đúng, kế hoạch ghi [NEW]
```

`core.the_v1.doc_tep_py_sang_cay_the` cũng có thật, nên phần import của lệnh 2
không sai — chỉ sai chỗ chọn tệp.

---

## 4. Một việc cũ chưa ai đóng, và nó đang làm mất thời gian của Antigravity

`tools/do_cua_cung_the.py` trả **mã thoát 1** mỗi lần chạy, nên nó bị chạy đi
chạy lại. Nhưng nó **không bao giờ xanh được**, vì mặc định nó chấm **bộ đọc
CŨ** `core/the_v1.py`:

```
Định nghĩa hàm    692 thẻ,  320 tả SAI
Nếu               622 thẻ,   49 tả SAI
Ngược lại          68 thẻ,   39 tả SAI
```

Đó chính là những con số đã khiến `the_cst` ra đời hôm 20/08. Tôi đã ghi việc
này vào bản giao 20/08 (*"trỏ lại `the_cst` hoặc đổi tên"*) và nó vẫn nằm đó.

Tệp có sẵn cờ `--cst` (dòng 503) nhưng chạy với cờ ấy thì **quá 400 giây chưa
xong** — LibCST chậm hơn `ast` khoảng 55 lần mỗi tệp.

```
XIN ba việc nhỏ:
  1. mặc định phải là --cst; muốn chấm bộ cũ thì thêm cờ --v1
     (hiện đang NGƯỢC)
  2. in tiến trình khi chạy --cst, để người chạy biết nó chưa treo
  3. docstring ghi rõ: công cụ này đang chấm BỘ ĐỌC NÀO
```

**Một công cụ đỏ vĩnh viễn tệ hơn không có công cụ.** Người chạy hoặc bỏ qua nó
— mất luôn cái gác cửa thật — hoặc chạy đi chạy lại. Cả hai đều hỏng.

---

## 5. Phần còn lại của kế hoạch — không có gì để bác

```
CSS thẻ viên thuốc, lỗ, cột dọc, nhánh rẽ    khớp trang mẫu
chinhCotDoc() đo bằng getBoundingClientRect   ĐÚNG — đây là chỗ tôi tự làm hỏng
                                              một lần, tính bằng % thì hụt 7px
chu_thich vào cả the_v1 và validator.js      ĐÚNG, giữ parity
cây thư mục nối /api/tep_tin                  ĐÚNG, endpoint đã có
4 tab về cột giữa, cột phải cho Agent         ĐÚNG
bỏ tab "Mã Python"                            ĐÚNG
test_the_cst.py [NEW]                         ĐÚNG, kho chưa có
```

Ba việc xin: đổi tệp cho lệnh 2 (mục 1) · luật dòng ma thuật (mục 2) · sửa
`do_cua_cung_the.py` (mục 4).

Mục 2 là mục tôi lo nhất — nó âm thầm làm hỏng tệp, và cửa cứng lossless
**không bắt được** vì kéo một thẻ đi chỗ khác vẫn sinh ra tệp hợp lệ, chỉ là
sai nghĩa.

---

## 6. BỔ SUNG — đã chạy xong `--cst`, và tìm thêm một cái bẫy

Chạy `tools/do_cua_cung_the.py --cst` tới cùng:

```
mặc định (the_v1)   CHƯA ĐẠT, mã thoát 1
                    320/692 thẻ "Định nghĩa hàm" tả SAI
--cst  (the_cst)    ĐẠT CẢ BỐN CỬA, mã thoát 0
                    4538 thẻ thật, tả sai 0
                    kho tả bằng thẻ 64,2% · dòng tả bằng thẻ 61,9%
```

Nên chẩn đoán ở mục 4 đúng hẳn: **công cụ đỏ chỉ vì mặc định chấm bộ đọc cũ.**
Đảo mặc định là nó xanh ngay.

### Cái bẫy: dòng in ra trỏ SAI tệp

Sổ ghi đúng chỗ, hai tệp riêng biệt:

```
cua_cung.json        bo_doc = the_v1 (ast)      dat_het = False
cua_cung_cst.json    bo_doc = the_cst (LibCST)  dat_het = True
```

Nhưng dòng cuối của chương trình **luôn in `cua_cung.json`**, kể cả khi chạy
`--cst`:

```python
print("\nso   : " + str(RA / "cua_cung.json"))     # <- chốt cứng
```

Trong khi ngay phía trên nó đã chọn tên đúng rồi:

```python
ten_so = "cua_cung_cst.json" if "--cst" in sys.argv else "cua_cung.json"
```

Hậu quả: chạy `--cst`, màn hình báo **"ĐẠT CẢ BỐN CỬA"**, rồi mở đúng tệp nó
vừa chỉ ra thì thấy `dat_het = False`. Hai thứ mâu thuẫn nhau, và người đọc sẽ
tin cái sổ chứ không tin màn hình.

```
XIN: đổi dòng in thành `str(RA / ten_so)` — một chữ.
```

Trang HTML thì đã đúng (`bao_cao_cst.html`), chỉ mỗi dòng JSON sai.

Đây là họ hàng gần của luật `CLAUDE.md` §4 *"phán quyết phải đi kèm phép đo tạo
ra nó"*: ở đây phán quyết đúng, phép đo đúng, nhưng **cái nhãn chỉ đường thì
trỏ sang chỗ khác** — và người đọc sẽ đi theo cái nhãn.
