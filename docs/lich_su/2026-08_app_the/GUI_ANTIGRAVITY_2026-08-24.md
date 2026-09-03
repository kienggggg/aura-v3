# Gửi Antigravity — N3 đã đạt, và ba việc mới đào ra từ chính bộ E1

*24/08/2026. Bản vá N3 đúng: 50/50 khối, lệch 0px, không đụng cửa sổ. Bốn cửa
cứng khớp đúng báo cáo. Dưới đây là những thứ chỉ lòi ra khi chạy, không lòi
ra khi đọc.*

---

## 1. Đã đạt — không phải sửa gì

```
N3 cột dọc      0/50 -> 50/50 khối, lệch 17px -> 0px, không cần resize
N1 N2 N4 N5     8% · 20px · 5 màu · 0px       đạt cả bốn
bốn cửa cứng    ĐẠT cả bốn, 86 tệp, 8219 thẻ, dat_het=True
pytest          624 passed, 1 skipped
node            e1_ui 6/6 · parity 27/27
```

`yeuCauChinhCotDoc()` gọi ba lượt là cách đúng. Giữ nguyên.

---

## 2. Test N3 KHÔNG HỎNG ĐƯỢC — tôi đã sửa, gửi lại để biết

`tests/test_the_connector_ui.js` test số 5 chỉ khẳng định `--cao-cot !== undefined`.
Gieo lỗi thử:

```
công thức +4 -> +400 (lệch 396px)              vẫn xanh 5/5
bỏ hoàn toàn double rAF (CHÍNH LÀ LỖI N3)      vẫn xanh 5/5
```

Nghĩa là: **cửa này không phát hiện được đúng cái lỗi mà nó sinh ra để canh.**

Hai nguyên nhân, cả hai đều ở FakeDOM chứ không ở `app.js`:

```
getBoundingClientRect() trả CÙNG một rect cho mọi phần tử
   -> tử số và mẫu số bằng nhau, mọi công thức ra cùng một số
assert !== undefined
   -> không nhìn vào số ấy
```

Tôi đã sửa trong `tests/test_the_connector_ui.js`:

```
thêm  this._rect   đặt rect riêng từng phần tử
      khối top 100 · nhánh cuối top 300 h 20  ->  phải ra ĐÚNG '214px'
thêm  đếm độ lồng requestAnimationFrame       ->  phải bằng 2
      đếm số lần chinhCotDoc chạy             ->  phải bằng 3
```

Gieo lại ba lỗi: **3/3 đều ĐỎ**. `app.js` khôi phục khớp SHA-256, không đụng.

---

## 3. E1 CHẤM NHẦM BẢN VÁ — đây là việc nặng nhất

Bốn mốc lọc không xê dịch (`65->15 · 87->28 · 1->1 · 10->2`). Nhưng **phán
quyết** của hai ca lật từ `tim_thay` sang `ung_vien_khong_qua_suite`, và lật sai.

### Đo được

`tools/_worker_e1_exec.py` ghi vào bản sao tạm trường `cand["ma"]`, tức
`ast.unparse` **cả tệp**:

```
tệp            diff công bố   khác thật   chú thích     dòng      dòng ma thuật
dong_ho.py         2 dòng      24 dòng      1 -> 0     40 -> 26      MẤT
may_tinh.py        2 dòng     231 dòng     50 -> 0    321 -> 194     MẤT
web_search.py      2 dòng     409 dòng     94 -> 0    563 -> 350     MẤT
```

Và cả ba bản vá đều ĐÚNG:

```
AST(ma) == AST(tệp gốc)      3/3 ca
```

Suite đỏ **chỉ vì chuẩn hoá**, không vì bản vá.

### Vì sao chỉ hai tệp bị

`tests/test_the_cst.py` vừa thêm vòng này đọc thẳng `core/*.py` từ đĩa:

```
test_chu_thich_the_in_web_search        đòi web_search.py >= 80 thẻ chu_thich
                                        chuẩn hoá còn 0        -> ĐỎ
test_dong_ma_thuat_khong_thanh_chu_thich đòi dong_ho.py giữ dòng ma thuật
                                        chuẩn hoá mất dòng 1   -> ĐỎ
may_tinh.py                             không test nào đọc     -> sống sót
```

Cờ `-x` dừng ở lỗi đầu, nên **mọi** ứng viên trên hai tệp ấy bị loại.

Đây chính là dòng ma thuật tôi xin bảo vệ ở bản giao 23/08 mục 2 — luật đã cài
đúng cho **bộ đọc thẻ**, nhưng **E1 vẫn xoá nó** ở đường khác.

```
XIN: worker ghi BẢN VÁ ĐÚNG MỘT DÒNG lên tệp gốc, đừng ghi ast.unparse cả tệp.
     Bản vá đã có sẵn trong unified_diff — dùng chính nó.

NGƯỠNG: chạy lại bốn mốc E1, KHÔNG đụng gì khác, phải ra
        may_tinh 65->15 tim_thay · web_search 87->28 tim_thay
        dong_ho   1-> 1 tim_thay · loai_cau_hoi 10->2 khong_tim_thay
        và: với mỗi ứng viên, số chú thích của tệp trong bản sao tạm
            phải BẰNG số chú thích tệp gốc (dong_ho 1 · may_tinh 50 · web_search 94)
```

Ngưỡng thứ hai là ngưỡng thật. Ngưỡng thứ nhất một mình thì vá tạm bằng cách
nới `-x` cũng qua được, mà bệnh vẫn còn.

---

## 4. Hai chỗ nhỏ, cùng họ với luật cũ

```
_worker_e1_exec.py:346
    so_test_hong = max(1, out_text.count("FAILED") or 1)
```

Suite không chạy được (lỗi thu thập, quá giờ) thì vẫn báo **"Suite: ĐỎ (1 test
khác hỏng)"**. Con số 1 ấy không đo được từ đâu. `CLAUDE.md` §4: *phép đo không
chạy phải NÓI LÀ KHÔNG CHẠY*.

```
XIN: thêm trạng thái thứ ba "suite_khong_do_duoc", giao diện hiện đúng chữ ấy,
     đừng mượn nhãn ĐỎ.
```

```
tools/do_cua_cung_e1_app.py:339
    print(f"[*] BẮT ĐẦU NGHIỆM THU CỬA CỨNG E1 ...")
    -> UnicodeEncodeError: 'charmap' codec can't encode 'Ắ'
```

Sập ngay dòng in đầu tiên trên console mặc định. Phải đặt
`PYTHONIOENCODING=utf-8` mới chạy được. Cùng bệnh với cú sập khởi động đã sửa
hôm 22/08.

```
XIN: bọc stdout bằng io.TextIOWrapper(..., encoding="utf-8") ngay đầu tệp.
```

Ngoài ra cửa CDP trong công cụ ấy quá 120 giây vì không mở được trình duyệt,
làm mã thoát 1 — nhưng bốn mốc E1 đã chạy xong trước đó nên số vẫn dùng được.

---

## 5. Không phải lỗi của vòng này

Mục 3 và 4 đã có sẵn từ trước; vòng này chỉ **làm chúng lộ ra**, vì
`test_the_cst.py` là bộ test đầu tiên đọc `core/*.py` như văn bản. Trước đó E1
vẫn xoá chú thích y như vậy, chỉ là không ai bắt.

Giao diện E1 **không có nút áp dụng**, nên chưa mất tệp nào. Nhưng ngày nào
thêm nút ấy mà chưa sửa mục 3 thì bấm một cái là bay sạch chú thích của tệp.
