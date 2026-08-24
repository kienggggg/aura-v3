# Gửi Antigravity — bản giao gộp 24/08/2026

*Vòng thẻ nối thẳng đã xong: N3 đạt, năm ngưỡng đạt, bốn cửa cứng đạt, 624
test xanh. Bản giao này chỉ còn ba việc, và cả ba nằm ở bộ E1 — không nằm ở
giao diện. Mọi lệnh dưới đây tôi đã chạy trước khi gửi.*

---

## 0. Đã đạt — đừng đụng vào

```
N3 cột dọc      0/50 -> 50/50 khối có --cao-cot, lệch 17px -> 0px
                đo ngay sau khi mở core/web_search.py, KHÔNG phát resize
N1 N2 N4 N5     8% bỏ trống · cao trung vị 20px · 5 màu nhánh rẽ · lỗ lệch 0px
bốn cửa cứng    ĐẠT cả bốn · 86 tệp · 8219 thẻ · đổi nghĩa âm thầm 0
                vỡ cú pháp 0 · tệp dính 0/86 · dat_het=True
pytest          624 passed, 1 skipped
node            e1_ui 6/6 · parity 27/27 · connector 6/6
```

`yeuCauChinhCotDoc()` gọi ba lượt (ngay lập tức + hai khung hình lồng nhau) là
cách đúng. Giữ nguyên.

Tôi cũng đã thêm ngoại lệ `.gitignore` cho
`data/evidence_sprint/e1_ngoai_ho.json`. Trước đó, bản sao chỉ gồm tệp git theo
dõi cho **2 failed, 622 passed**; nay **624 passed, mã thoát 0**. Không phải
việc của bên bạn, chỉ báo để biết.

---

## 1. VIỆC NẶNG NHẤT — E1 chấm nhầm bản vá

### Đo được

Bốn mốc lọc **không xê dịch** (`65->15 · 87->28 · 1->1 · 10->2`). Nhưng phán
quyết hai ca lật từ `tim_thay` sang `ung_vien_khong_qua_suite`, và lật SAI.

`tools/_worker_e1_exec.py:129`

```python
moi = ast.unparse(ast.fix_missing_locations(bd.visit(ast.parse(nguon))))
```

`ast.unparse` dựng lại **cả tệp** từ cây, nên rụng hết chú thích và dòng ma
thuật. Dòng 260 ghi thẳng chuỗi ấy vào bản sao tạm, rồi dòng 322 đem **chính
tệp đã rụng** đi chạy suite.

```
tệp            diff công bố   khác thật   chú thích     dòng      dòng ma thuật
dong_ho.py         2 dòng      24 dòng      1 -> 0     40 -> 26      MẤT
may_tinh.py        2 dòng     231 dòng     50 -> 0    321 -> 194     MẤT
web_search.py      2 dòng     409 dòng     94 -> 0    563 -> 350     MẤT
```

`unified_diff` thì đúng, vì nó so **hai bản đã chuẩn hoá** với nhau
(dòng 273: `_tao_unified_diff(chuan_ast_goc, ma_moi, ...)`). Người đọc thấy
"sửa 2 dòng"; thứ đem đi chấm là tệp khác 409 dòng.

### Ba bản vá đều ĐÚNG

```
AST(ma) == AST(tệp gốc)      3/3 ca
```

Suite đỏ **chỉ vì chuẩn hoá**, không vì bản vá.

### Vì sao chỉ hai tệp bị, còn may_tinh thoát

`tests/test_the_cst.py` là bộ test đầu tiên đọc `core/*.py` **như văn bản**:

```
test_chu_thich_the_in_web_search         đòi web_search.py >= 80 thẻ chu_thich
                                         chuẩn hoá còn 0        -> ĐỎ
test_dong_ma_thuat_khong_thanh_chu_thich đòi dong_ho.py giữ dòng ma thuật
                                         chuẩn hoá mất dòng 1   -> ĐỎ
core/may_tinh.py                         không test nào đọc     -> sống sót
```

Worker chạy pytest có cờ `-x` nên dừng ở lỗi đầu, và **mọi** ứng viên trên hai
tệp ấy bị gán `full_suite_status = ĐỎ`.

Đây đúng là dòng ma thuật tôi xin bảo vệ ở bản giao 23/08 mục 2. Luật đã cài
đúng cho **bộ đọc thẻ**; E1 vẫn xoá nó ở đường khác.

### Lệnh xem tận mắt — 3 giây

```bash
venv/Scripts/python.exe -X utf8 -c "import sys; sys.path.insert(0,'tools'); from _worker_e1_exec import _ma_sau_lat, _liet_ke_cho; goc=open('core/dong_ho.py',encoding='utf-8').read(); ma,da=_ma_sau_lat(goc,_liet_ke_cho(goc)[0][0]); d=lambda s:sum(1 for l in s.splitlines() if l.strip().startswith('#')); print('chu thich',d(goc),'->',d(ma),'| dong',len(goc.splitlines()),'->',len(ma.splitlines()),'| con dong ma thuat:',ma.splitlines()[0].startswith('#'))"
```

Ra: `chu thich 1 -> 0 | dong 40 -> 26 | con dong ma thuat: False`

Chỉ hai chạm: `-X utf8` và in ra chữ không dấu. Bản đầu tiên tôi viết
không có hai thứ đó thì **sập ngay `UnicodeEncodeError` cp1252** — đúng bệnh
mục 3 dưới đây, chứng minh luôn là nó gặp thật chứ không phải lý thuyết.

### XIN: lật trên VĂN BẢN, đừng dựng lại cả tệp

Bản mẫu dưới đây tôi đã chạy trên `core/dong_ho.py`, ra **chú thích 1→1, dòng
40→40, dòng ma thuật còn nguyên, đúng 2 dòng khác, AST đổi thật**:

```python
def lat_tren_van_ban(nguon: str, node, tu: str, sang: str) -> str:
    """Đổi ĐÚNG một token toán tử trong vùng của node, giữ nguyên mọi byte khác."""
    dong = nguon.splitlines(keepends=True)
    bat_dau = sum(len(d) for d in dong[:node.lineno - 1]) + node.col_offset
    ket = sum(len(d) for d in dong[:node.end_lineno - 1]) + node.end_col_offset
    vung = nguon[bat_dau:ket]
    for tok in tokenize.generate_tokens(io.StringIO(vung).readline):
        if tok.string == tu and tok.type in (tokenize.NAME, tokenize.OP):
            r0 = sum(len(l) for l in vung.splitlines(keepends=True)[:tok.start[0] - 1]) + tok.start[1]
            return nguon[:bat_dau + r0] + sang + nguon[bat_dau + r0 + len(tu):]
    raise ValueError("khong thay token")
```

`tools/_worker_e1_exec.py` hiện **chưa import** `io` và `tokenize` — nhớ thêm.

Năm họ phép của E1 đều hợp: `so_sanh` · `logic` · `bo_phu_dinh` ·
`bool_constant` · `int_constant` — tất cả đều là **đổi một token**. Với
`bool_constant` và `int_constant` thì còn rẻ hơn: node `Constant` đã có sẵn
`col_offset`/`end_col_offset`, cắt thẳng.

`unified_diff` khi ấy nên so `raw_goc` với bản đã lật văn bản, để **thứ hiện ra
đúng bằng thứ đem đi chấm**.

### NGƯỠNG ĐẶT TRƯỚC

```
1. bốn mốc E1 chạy lại, KHÔNG đụng gì khác:
      may_tinh      65 -> 15   tim_thay
      web_search    87 -> 28   tim_thay
      dong_ho        1 ->  1   tim_thay
      loai_cau_hoi  10 ->  2   khong_tim_thay
2. với MỖI ứng viên, tệp trong bản sao tạm phải:
      số chú thích BẰNG tệp gốc   (dong_ho 1 · may_tinh 50 · web_search 94)
      dòng 1 vẫn là `# -*- coding: utf-8 -*-`
      số dòng khác so tệp gốc = 2   (một `-`, một `+`)
```

**Ngưỡng 2 mới là ngưỡng thật.** Ngưỡng 1 một mình thì bỏ cờ `-x` cũng qua
được, mà bệnh vẫn còn nguyên.

---

## 2. `so_test_hong` bịa ra số 1

`tools/_worker_e1_exec.py:346`

```python
so_test_hong = max(1, out_text.count("FAILED") or 1)
```

Suite lỗi thu thập, quá giờ, hay chết vì bất cứ lý do gì cũng ra **1**. Giao
diện in `Suite: ĐỎ (1 test khác hỏng)` — đọc như một phép đo, mà không có phép
đo nào. Cùng họ với `except Exception: so_test_hong = 1` ở dòng 349.

`CLAUDE.md` §4: *phép đo không chạy phải NÓI LÀ KHÔNG CHẠY.*

```
XIN: thêm trạng thái thứ ba `suite_khong_do_duoc`, giao diện hiện đúng chữ ấy
     kèm lý do (quá giờ / lỗi thu thập), đừng mượn nhãn ĐỎ và đừng bịa số.

NGƯỠNG: đặt full_suite_timeout_s = 1 rồi chạy E1 trên core/dong_ho.py
        -> phải ra `suite_khong_do_duoc`, KHÔNG ra "ĐỎ (1 test khác hỏng)"
```

---

## 3. `tools/do_cua_cung_e1_app.py` sập ngay dòng in đầu

```
dòng 339   print(f"[*] BẮT ĐẦU NGHIỆM THU CỬA CỨNG E1 ...")
->  UnicodeEncodeError: 'charmap' codec can't encode character 'Ắ'
```

Trên console mặc định của Windows là sập. Phải đặt `PYTHONIOENCODING=utf-8` mới
chạy được — tệp không có `TextIOWrapper` nào. Cùng bệnh với cú sập khởi động đã
sửa hôm 22/08, và đúng luật `CLAUDE.md` §4 *"đo tiếng Việt bằng Python"*.

```
XIN: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
     ngay đầu tệp.

NGƯỠNG: chạy KHÔNG đặt biến môi trường nào -> không sập ở dòng in đầu.
```

Kèm theo: cửa CDP trong tệp ấy quá 120 giây vì không mở được trình duyệt, làm
mã thoát 1. Bốn mốc E1 đã chạy xong trước đó nên số vẫn dùng được, nhưng một
công cụ luôn thoát 1 thì sớm muộn cũng bị bỏ qua — y như `do_cua_cung_the.py`
đỏ vĩnh viễn hồi 23/08.

---

## 4. Test canh N3 không hỏng được — tôi đã sửa, chỉ báo để biết

`tests/test_the_connector_ui.js` test số 5 chỉ khẳng định
`--cao-cot !== undefined`. Gieo lỗi:

```
công thức +4 -> +400 (lệch 396px)              vẫn xanh 5/5
bỏ hoàn toàn double rAF (CHÍNH LÀ LỖI N3)      vẫn xanh 5/5
```

Cửa không phát hiện được đúng cái lỗi nó sinh ra để canh. Bệnh ở FakeDOM chứ
không ở `app.js`: `getBoundingClientRect()` trả **cùng một rect** cho mọi phần
tử, nên tử số và mẫu số bằng nhau, mọi công thức ra cùng một số.

Đã sửa: thêm `this._rect` đặt riêng từng phần tử (khối top 100, nhánh cuối top
300 cao 20 → phải ra **đúng `214px`**), và đếm độ lồng `requestAnimationFrame`
(**phải bằng 2**, `chinhCotDoc` chạy **3 lần**). Gieo lại ba lỗi: **3/3 đều
ĐỎ**. `app.js` khôi phục khớp SHA-256, không đụng.

Nhắc lại vì nó lặp lại nhiều vòng rồi: **một cửa chỉ có giá trị bằng đúng cái
lỗi nó bắt được.** Trước khi gửi một bộ test mới, gieo thử một lỗi thật vào và
xem nó có đỏ không — mất ba giây.

---

## 5. Tóm tắt việc

```
1. E1 lật trên văn bản thay vì ast.unparse cả tệp        <- nặng nhất
2. so_test_hong: thêm trạng thái `suite_khong_do_duoc`
3. do_cua_cung_e1_app.py: bọc stdout UTF-8
```

Việc 1 chưa gây mất tệp vì giao diện E1 **không có nút áp dụng**. Nhưng ngày
nào thêm nút ấy mà chưa sửa thì bấm một cái là bay sạch chú thích của tệp — và
`unified_diff` trên màn hình vẫn sẽ nói "sửa 2 dòng".
