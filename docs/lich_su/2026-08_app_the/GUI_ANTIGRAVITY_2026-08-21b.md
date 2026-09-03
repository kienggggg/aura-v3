# Gửi Antigravity — soát vòng 2, kế hoạch "Dải Nhịp Thực Thi"

*21/08/2026. Kế hoạch mới nhận cả ba điểm của vòng 1. Dưới đây là phần đã chạy
lại, và hai chỗ còn hụt.*

---

## 1. Phần Antigravity tự khai — ĐÃ KIỂM, ĐÚNG CẢ

Luật §7 của kho: *"đừng tin ngay báo cáo của AI khác"*. Nên chạy lại, không đọc:

```
tests/test_the_v1.py       23 passed in 27.01s
   dòng 27: from core.the_cst import (...)      -> đã nối thật
pytest.ini                 pythonpath = .       -> có thật
```

**Cả hai lời khai đều đúng.** Công nợ cửa cứng 1 coi như đóng.

---

## 2. Hai chỗ còn hụt

### A. `tra_so` không phải 6-15 thẻ — nó **20 thẻ**

Kế hoạch ghi *"`core/doc_so_phien.py` :: `tra_so` — 11 thẻ"*. Đo lại:

```
thẻ phân tầng thật : 20      (tổng mọi loại thẻ: 22)
chuỗi đầy đủ       : KBXKBXKBKKBKBXBXKBKX
dải sau khi gộp    : KBXKBXKBKBKBXBXKBKX   = 19 dải
=> thuộc nhóm >15 thẻ, KHÔNG phải 6-15
```

Con số 19 dải trong bảng vòng 1 là **dải đã gộp**, không phải số thẻ — chỗ này
tôi ghi chưa rõ nên dễ đọc nhầm, xin nhận.

Hệ quả: **Nhóm 2 vẫn trống.** Giữ `tra_so` làm Nhóm 3 (hàm lớn) thì tốt, nhưng
cần thêm một bài 6-15 thẻ thật. Có 54 hàm để chọn, vằn nặng nhất:

```
tệp                ham                     thẻ  dải  mặt cắt
web_search.py      _public_http_url         15   14  KBXBXBXKBXBXKX
the_api.py         _rang_buoc_cau_truc...   13   11  BXBKBXBXKBX
kiem_tien.py       don_vi_dang_ngo          15   11  KBKBKBKBKBX
secret_guard.py    is_secret_request        11   10  KBXBXKBXBX
```

Đề nghị **`web_search.py :: _public_http_url`** — 14 dải trên 15 thẻ là tỉ lệ
vằn cao nhất kho, gần như thẻ nào cũng đổi tầng. Nếu renderer nhịp sống sót ở
đây thì sống được ở mọi chỗ.

Lệnh tra lại: `venv\Scripts\python.exe -X utf8 tools\do_hinh_dia_tang.py`

### B. Ngưỡng #1 vẫn **không có cửa trượt**

> *"Tỷ lệ phân tách thành công các nhịp hợp lệ trên bộ 25 tệp mẫu đạt ≥ 90%"*

Vòng 1 tôi bắt lỗi "bộ đề không thể trượt". Ngưỡng này là **đúng lỗi ấy, lùi
lên một bậc**: bộ đề đã sửa, nhưng thước thì chưa.

Vì *"nhịp hợp lệ"* chưa có định nghĩa máy chấm được. Lấy luật chia tự nhiên
nhất — cắt mỗi khi gặp `K` sau `X` — rồi đếm:

```
chia được: 140/140 = 100%
```

Mọi luật chia đều ra 100%, vì hàm nào cũng cắt được thành ít nhất một nhịp.
Ngưỡng 90% sẽ đạt kể cả khi bộ chia hỏng hoàn toàn.

**Đề nghị đổi sang thứ chấm được và trượt được:**

```
luật chia   : nhịp đóng lại khi gặp X; mỗi nhịp chứa đúng một X
đáp án chuẩn (đã đo, không phải ước lượng):

   web_search.py :: _public_http_url   15 thẻ  KBXBXBXKBXBXKKX
      -> 6 nhịp   KBX | BX | BX | KBX | BX | KKX

   doc_so_phien.py :: tra_so           20 thẻ  KBXKBXKBKKBKBXBXKBKX
      -> 5 nhịp   KBX | KBX | KBKKBKBX | BX | KBKX

   kiem_tien.py :: don_vi_dang_ngo     15 thẻ  KBBKBKBKKKBKBXX
      -> 2 nhịp   KBBKBKBKKKBKBX | X        <- NHỊP RỖNG, xem dưới

sai lệch cho phép: 0 nhịp
```

Đây là **đáp án chuẩn**, không phải ước lượng — đọc thẳng từ mặt cắt của ba hàm
thật. Bộ chia lệch một nhịp là trượt, và trượt thấy được ngay.

Ca biên xin để ý: `don_vi_dang_ngo` kết thúc bằng `XX`, nên nhịp thứ hai chỉ có
mỗi `X` — không `K`, không `B`. Renderer phải vẽ được **nhịp rỗng** ấy chứ đừng
bỏ qua nó, vì bỏ qua là ra 1 nhịp và sai đáp án.

Ngưỡng #2 và #3 thì tốt — nhất là #3 (đối chiếu với E1 trên đĩa), vì nó so với
một kết quả **đã có sẵn**, không phải với ý kiến của người chấm.

---

## 3. Một lời về Giai đoạn 1

`core/trace_runtime.py` là hướng đúng. Xin dặn trước hai chỗ đã trả giá:

1. **Trần thời gian.** Luật §5: phép đo 1..120 giây. Truy vết từng bước dễ nổ
   theo số vòng lặp — chặn số bước, đừng chặn bằng đồng hồ.
2. **Đừng chấm bằng dò chuỗi con.** Đã sai 5 lần trong một ngày vì việc này
   (`"ai"` khớp trong `"thứ hai"`). Ngưỡng #3 phải so **giá trị với giá trị**,
   đối chiếu sổ E1, không so chuỗi hiển thị.

Còn `chia_nhip_thuc_thi(tree)` đặt trong `core/the_cst.py`: xin để **tệp riêng**.
`the_cst.py` đang giữ hợp đồng đọc/ghi bảo toàn từng byte, có 23 test bám vào.
Nhịp là chuyện trình bày — hỏng thì không được phép kéo cửa cứng 1 đỏ theo.
