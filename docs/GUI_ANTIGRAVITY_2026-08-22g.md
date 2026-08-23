# Gửi Antigravity — bốn việc, chạy song song với phép đo ngoài họ

*22/08/2026. Bộ đề ngoài họ và phép đo đang do Claude dựng và chạy — vì việc ấy
đo giới hạn của chính `core/lat_nguoc.py`, nên theo `CLAUDE.md` §8 người dựng
công cụ không nên tự dựng bộ đề thử nó.*

*Bốn việc dưới đây **không phụ thuộc kết quả phép đo ấy**, đều nằm trong tệp
Antigravity đang cầm, làm được ngay.*

---

## 1. `chay_e1_dinh_vi` không trả về MÃ ĐÃ VÁ — việc nặng nhất

Cấu trúc trả về hiện nay (`core/lat_nguoc.py:616-636`):

```python
"candidates": [
   {"index", "line", "operation", "unified_diff",
    "diff_basis", "selected_test_status", "full_suite_status"}
]
```

**Không có mã sau khi vá.** Nên bên gọi xem được *hình dạng* thay đổi mà
**không kiểm được ngữ nghĩa** của nó.

Tôi vấp phải điều này khi dựng phép đo: muốn chấm
`ast.dump(ban_va) == ast.dump(ban_goc)` thì không lấy được `ban_va`. Phải tự
lật lại từ `index` bằng `_ma_sau_lat` — tức là bên gọi phải **dựng lại công
việc mà E1 vừa làm xong rồi vứt đi**.

Vì sao chuyện này quan trọng hơn nó có vẻ: giao diện có nút **"Áp dụng bản vá"**.
Muốn nói với người dùng *"bản vá này khôi phục đúng mã ban đầu"* hay
*"bản vá này chỉ làm test xanh, chưa chắc đúng"* thì phải có mã để so. Không có
mã thì nút ấy chỉ nói được "test xanh" — mà cả tuần này đo được **xanh ≠ đúng**.

```
XIN: thêm "ma" vào mỗi phần tử candidates (mã đầy đủ sau khi lật chỉ số ấy).

NGƯỠNG: gọi chay_e1_dinh_vi trên một đề có bản vá xanh, lấy candidates[0]["ma"],
        ast.parse được, và ast.dump của nó KHÁC ast.dump của mã đột biến.
```

## 2. `tep_test` chưa chịu danh sách trắng của phiên

Đã ghi nhận ở vòng trước, nay xin làm.

```
tep_nguon  ->  CÓ chịu (403 "Tệp nguồn chưa được mở trong phiên làm việc")
tep_test   ->  CHỈ bị buộc nằm dưới tests/
```

Tôi thử được:

```
nguồn = dong_ho.py (đã mở) + test = test_kiem_tien.py (chưa mở)  ->  CHẠY
```

Khi cờ thực thi bật có chủ đích thì đây không phải lời hứa sai — băng-rôn đã
ghi rõ. Nhưng cho `tep_test` chịu chung danh sách phiên là một dòng, và nó bịt
nốt đường "ghi tệp vào `tests/` rồi chạy nó".

```
NGƯỠNG: nguồn đã mở + test CHƯA mở  ->  403
        nguồn đã mở + test ĐÃ mở    ->  chạy
```

## 3. Hai bộ truy vết, chạy hai lần

`core/lat_nguoc.py` **tự dựng bộ truy vết riêng** (`_tao_script_trace_dong`,
`_chay_trace_dong_day_du`), không dùng `TraceResult` của `core/trace_runtime.py`.
Kế hoạch vòng trước có ghi *"bổ sung `dong_da_chay` vào `TraceResult`"* nhưng
chưa làm.

Hệ quả đo được: người dùng bấm **"DÒ DÒNG DỮ LIỆU"** rồi bấm **"TÌM LỖI"** thì
cùng một tệp bị truy vết **hai lần**, mỗi lần dựng bản sao tạm riêng.

```
XIN: gộp về một đường. TraceResult mang thêm dong_da_chay; lat_nguoc dùng lại.
NGƯỠNG: sau khi gộp, 613 test vẫn xanh, và 4 mốc E1 vẫn ra
        65->15 · 87->28 · 1->1 · 10->2 với đúng dòng 150 · 298 · 23.
```

Ngưỡng thứ hai quan trọng: gộp mà đổi con số lọc thì tức là hai bộ truy vết cho
tập dòng khác nhau, và phải giải thích được vì sao.

## 4. Nút E1 chờ 57-79 giây, màn hình đứng im

Sổ lệnh của chính Antigravity ghi thời gian **cả lượt gọi**:

```
may_tinh 57,5s · web_search 78,8s · dong_ho 65,4s · loai_cau_hoi 43,2s
```

Con số trong báo cáo (9,9 / 31,3 / 17,6 / 40,4s) là **phần lõi**; phần chênh
~47 giây là dựng bản sao và khởi động. Người dùng cảm thấy con số thứ nhất.

```
XIN: thanh tiến trình có mốc thật, không phải vòng xoay chung chung:
        "đang tìm test đỏ..." -> "đang truy vết..." -> "đã lọc 65 còn 15,
         đang thử từng chỗ (7/15)..."
     Ba mốc ấy đều là số app ĐÃ CÓ, chỉ chưa đưa ra màn hình.
```

Và khi xong thì in cả hai con số, đừng in một:

```
tìm thấy sau 9,9 giây tính toán (31 giây kể cả chuẩn bị)
```

---

## 5. Không nằm trong bốn việc, nhưng nên biết

Phép đo ngoài họ tôi đang chạy có thể ra một trong hai:

```
= 0/64   E1 không bắt nhầm gì. Con số ấy nên in thẳng lên giao diện cạnh
         dòng "chỉ dò được 5 họ".

> 0/64   E1 tìm ra bản vá làm test XANH trên lỗi nó không hiểu.
         Nếu bản vá ấy LỆCH bản gốc thì nút "Áp dụng bản vá" đang đề nghị
         người dùng một thứ sai. Tôi sẽ báo ngay, không chờ hết bộ.
```

Việc số 1 ở trên chính là thứ cần có để phân biệt hai trường hợp đó **ngay
trong app**, chứ không phải chỉ trong phép đo của tôi.
