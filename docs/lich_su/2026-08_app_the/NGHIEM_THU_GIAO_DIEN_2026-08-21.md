# Nghiệm thu GIAO DIỆN app thẻ — 21/08/2026

*Claude mở app thật, thao tác thật. Bảy mục ngưỡng viết TRƯỚC khi mở. Ba trạng
thái: **đạt** · **đo được mà không đạt** · **không đo được** — không gộp.*

Máy chủ: `venv\Scripts\python.exe -X utf8 -u -m interface.the_app --port 8088`

---

## 1. Bảng bảy mục

| # | mục | kết quả |
|---|---|---|
| 1 | app nạp được, không lỗi console | **đạt** — 403 duy nhất là lần nạp trước khi có mã thông hành |
| 2 | `_public_http_url` ra 6 nhịp, bấm pill cuộn tới đúng thẻ | **đạt** *(kèm ghi chú, mục 3)* |
| 3 | ca biên nhịp rỗng hiện được | **đạt** — pill `X (Rỗng)` hiện đúng |
| 4 | ca khuyết B hiện được | **đạt** — nhãn `(Khuyết B)` hiện đúng |
| 5 | tab Mạch Nước Ngầm | **đạt một nửa** — đường "không có test đỏ" chạy đúng; đường có vết thật **không đo được bằng mắt** |
| 6 | cảnh báo `trace_khong_qua_loi` | **không đo được** — có trong mã (`app.js:711`) và backend đã đo, nhưng chưa dựng được ca thật để nhìn |
| 7 | tab Kịch Bản | **đo được mà KHÔNG đạt** — có câu phân định tĩnh/động, nhưng nội dung hỏng (mục 4) |

Mục 2 kiểm bằng số: mở `core/web_search.py`, dãy nhịp 13-18 ra đúng

```
KBX | BX | BX | KBX | BX | KKX
```

khớp tuyệt đối đáp án chuẩn 6 nhịp. Bấm từng pill tô đúng 3 · 2 · 2 · 3 · 2 · 3
thẻ, và Nhịp 18 `KKX` tô đúng Gán · Gán · Trả về — khuyết B thật.

---

## 2. VIỆC LỚN NHẤT: 84 lỗi đỏ đều là báo động giả

Mở `core/web_search.py` — mã sản xuất, nằm trong bộ **582 test đang xanh**:

```
84 Lỗi ĐỎ · 33 Cảnh báo VÀNG      trên 199 thẻ
109/199 thẻ mang huy hiệu ❌ LỖI
```

**Cả 84 lỗi đỏ đến từ ĐÚNG MỘT luật**: *"Biến X được sử dụng nhưng chưa từng
được gán giá trị"*. Luật ấy bỏ sót năm loại tên hợp lệ:

```
frozenset · getattr                        HÀM DỰNG SẴN của Python
logging · re · os · json · shutil · Path   IMPORT
   subprocess · datetime · unicodedata
text · value · query · limit · port        THAM SỐ của hàm
   address · char
bo_dau · _khop                             HÀM tự định nghĩa trong chính tệp
ch · tu · w · chu · dong · cum             BIẾN VÒNG LẶP / comprehension
```

Không phải riêng tệp này:

```
                        lỗi ĐỎ   cảnh báo VÀNG
core/dong_ho.py  26 dòng      2         3
core/kiem_tien.py            14        21
core/web_search.py           84        33
```

*(Sửa 21/08: bản đầu ghi "5 lỗi" và "35 lỗi" — đó là TỔNG đỏ+vàng, không phải
đỏ. Đã đối chiếu bộ kiểm Python với bộ kiểm JS: khớp tuyệt đối cả ba tệp, không
có lệch parity.)*

Đây là chỗ **giết mục tiêu của cả app**. Người mới mở một tệp chạy tốt ra và
thấy 84 dấu đỏ — thứ họ học được không phải lập trình, mà là **đừng tin cái
bảng đỏ này**. Còn tệ hơn không có bảng.

Và nó cùng một bệnh với `CLAUDE.md` §4: một phán quyết nghe rất chắc, sinh ra
từ một luật nông. Ở đây luật nông là *"tên này có từng nằm bên trái dấu `=`
không"*.

Một cảnh báo vàng còn ghi tên biến là `` '...]' `` — mảnh vụn phân tích, không
phải tên biến.

---

## 3. Thanh nhịp chạy theo TỆP, không theo HÀM

Kế hoạch gốc có *"🔥 Túi Mắc-ma: định nghĩa hàm là khối độc lập"*. Bản cài đặt
gộp hết vào một dãy:

```
core/web_search.py   ->  35 nhịp liền một dãy, không phân hàm
core/dong_ho.py      ->  "Nhịp 1 KKKX (Khuyết B)" + "Nhịp 2 K"
```

`dong_ho.py` chỉ có một hàm `cau_gio` (đáp án chuẩn: **1 nhịp KKX**). Nhưng
thanh nhịp gộp cả `_THU = (...)` ở cấp mô-đun vào thành `KKKX`, rồi `__all__`
thành `Nhịp 2 K` lửng lơ không có X đóng.

Nên **không đọc được đáp án chuẩn 1 · 6 · 5 · 2 từ giao diện** — chúng chỉ đúng
ở tầng hàm, mà giao diện không có tầng đó. Backend `chia_nhip_thuc_thi` thì
đúng cả 4/4, tôi đã gọi thẳng và đối chiếu.

Đề nghị: cắt dãy theo `def`, mỗi hàm một dải, và đánh dấu nhịp lửng (`Nhịp 2 K`)
là **chưa đóng** thay vì để trống.

---

## 4. Tab Kịch Bản hỏng vì 45/199 thẻ là "Mã thô"

Bảng khay đếm được: `Mã thô ×45` trên tổng 199 thẻ — **23%** mã thật không dựng
nổi thành thẻ.

Hệ quả đọc thấy ngay ở tab Kịch Bản:

```
Bước 1: Mã thô  Thực thi khối lệnh ma_tho.
Bước 2: Mã thô  Thực thi khối lệnh ma_tho.
Bước 3: Mã thô  Thực thi khối lệnh ma_tho.
...
```

Đoạn văn giải thích cho người mới trở thành một dãy lặp không mang tin. Câu
phân định tĩnh/động thì có và đúng chỗ — đó là phần đạt.

---

## 5. App SẬP khi khởi động nếu console không phải UTF-8

```
File "D:\AURA_v3\interface\the_app.py", line 58, in main
    print("  \U0001f680 AURA — APP LẬP TRÌNH BẰNG THẺ (BẢN v1)")
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'
[exited with code 1]
```

Sập **trước khi máy chủ mở cổng**. `start_the_app.bat` sống sót vì có
`chcp 65001`; mọi đường khác — CI, trình giám sát, `python -m ...` từ console
mặc định Windows — thì chết.

Cùng họ với luật `CLAUDE.md` §4 *"đo tiếng Việt bằng Python, đừng qua
PowerShell"*, chỉ khác chiều.

Sửa: bọc `sys.stdout` bằng `TextIOWrapper(..., encoding="utf-8", errors="replace")`
ngay đầu `main()`, hoặc bỏ biểu tượng khỏi băng-rôn.

Thêm một chỗ nhỏ cùng gốc: mã thông hành **chỉ in ra stdout**, mà stdout bị đệm
khi không phải cửa sổ thật — nên trình nào bọc app lại đều không lấy được mã.
Nên `flush=True` ở dòng in mã.

---

## 6. Xin bốn việc, theo thứ tự

1. **Sửa luật "biến chưa gán"** — nhận import, tham số hàm, hàm tự định nghĩa,
   biến vòng lặp, và hàm dựng sẵn. Ngưỡng nghiệm thu đặt trước:
   `core/web_search.py` phải ra **0 lỗi đỏ**; `core/dong_ho.py` **0**;
   `core/kiem_tien.py` **0**. Ba tệp đều đang xanh 582 test, nên 0 là con số
   đúng, không phải con số dễ.
2. **Chữa băng-rôn khởi động** — một dòng, chặn một lỗi sập.
3. **Cắt dải nhịp theo hàm**, đánh dấu nhịp chưa đóng.
4. **Giảm "Mã thô"** — 45/199 là quá nhiều; mỗi loại gỡ được sẽ chữa luôn tab
   Kịch Bản.

Việc 1 nặng hơn ba việc kia cộng lại, và nó là việc duy nhất đang chặn mục tiêu
của app.
