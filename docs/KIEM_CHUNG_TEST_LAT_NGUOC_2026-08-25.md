# Kiểm chứng bài nộp — test cho `core/lat_nguoc.py` · 25/08/2026

Codex và Antigravity đều báo đạt. Tệp này ghi lại **kết quả chạy lại độc lập**,
không phải lời khai.

---

## Cả hai con số đều đúng

| tầng | bên làm báo | chạy lại độc lập | ngưỡng | |
|---|---|---|---|---|
| thuần | 36/37 = 0,97 | **36/37 = 0,97** (37,7 giây) | ≥ 0,85 | **đạt**, exit 0 |
| tích hợp | 75/85 = 0,88 | **75/85 = 0,88** (99,8 giây) | ≥ 0,60 | **đạt**, exit 0 |

Suite đầy đủ: **697 xanh, 1 bỏ qua, 71,4 giây** — khớp lời khai.
`tests/test_lat_nguoc.py`: **68 test, 0,54 giây**.

Ba điều kiện biên đều giữ:

- `core/lat_nguoc.py` **không bị đụng** — `git diff` rỗng, SHA-256
  `565209E20434BF76512EF52181EC1E9D2715E314CB57547D55CAD63D6C90DF54`.
- `NGUONG` trong `tools/do_test_lat_nguoc.py` **không bị nới** —
  `{"thuan": 0.85, "tich_hop": 0.60}`, `git diff` rỗng.
- Soi bẫy fake-PASS: không có `assert True`, không có khẳng định rỗng, không
  `pytest.skip` che chỗ khó.

Đường đi từ đầu: **0 test → 68 test**; tầng thuần **0,62 → 0,97**, tầng tích
hợp **0,00 → 0,88**.

---

## Ba chỗ không có trong hai bản báo cáo

### 1. Bằng chứng "chạy trên bản sao tạm" phủ nhầm đường

`test_..._loi_hua_1_2_3` băm SHA-256 tệp nguồn **thật từ đĩa** trước và sau —
phép đo đúng. Nhưng nó mock `_chon_test_va_dong` trả `khong_chay`, và
`core/lat_nguoc.py:313` có:

```python
if trace.get("trang_thai") != "trace_du":
    ...
    return { ... }          # thoát ngay, chưa sinh ứng viên, chưa chạy suite
```

Nên phép đo ấy chứng minh **đường thoát sớm không ghi gì** — đường gần như
không làm gì cả.

Đếm trên tệp test: **23 test đi qua đường `trace_du`** — đường thật sự lật mã
và chạy suite con — và **không test nào trong 23 kiểm tệp nguồn sau khi chạy**.

Lời hứa "chạy hoàn toàn trên bản sao tạm" có giá trị đúng ở chỗ nó CÓ ghi, chứ
không phải chỗ nó thoát sớm. Báo cáo ghi *"SHA-256 tệp nguồn thật trước/sau"*
mà không nói phủ nhánh nào — câu ấy đọc mạnh hơn thứ đã đo.

Đây **không phải** lỗi bịa số: phép đo có thật, chỉ là phủ nhầm chỗ.

### 2. Một lỗi thật trong `core/lat_nguoc.py`, cả hai bên đều báo "không phát hiện"

`core/lat_nguoc.py:316`:

```python
trang_thai_ra = "khong_tim_thay" if "không có test nào bị đỏ" in vi_sao else "khong_do_duoc"
```

Một **quyết định luồng điều khiển dò chuỗi con trên câu tiếng Việt dành cho
người đọc**. Câu gốc nằm ở dòng 223 của chính tệp ấy. Chạy thử:

```
"không có test nào bị đỏ trong tệp test"  ->  khong_tim_thay
"không có test nào ĐỎ trong tệp test"     ->  khong_do_duoc
```

Hai cách viết cùng nghĩa, kết quả ngược nhau. Mà `khong_tim_thay` và
`khong_do_duoc` là **hai điều ngược nhau** trong kỷ luật của kho: "đo được mà
không thấy" so với "không đo được". Sửa lại một câu thông báo cho dễ đọc là đủ
làm sổ bằng chứng ghi sai loại.

Đúng họ bệnh §4 *"đừng tự chấm điểm bằng dò chuỗi con"* — kho này đã trả giá
năm lần trong một ngày cho nó.

Hôm nay chưa hỏng, vì hai chuỗi còn khớp. Đó là lý do không test nào bắt được,
và cũng là lý do phải ghi ra.

### 3. Một hash trong báo cáo Codex không giải thích được

Khối kết xuất ghi `HASH_BEFORE=CADE6738…` và `HASH_AFTER=CADE6738…`. Băm ba
tệp liên quan:

```
565209E20434BF76  core/lat_nguoc.py
36988DCC710E4C0E  tests/test_lat_nguoc.py
26FC229A30FF8A84  tools/do_test_lat_nguoc.py
```

Không tệp nào ra `CADE6738`. Câu trong văn xuôi (`565209E2…C90DF54`) thì đúng.

Kết luận không đổi — "nguồn không bị đụng" đã kiểm bằng `git diff` — nhưng
**một con số không giải thích được thì không nên nằm trong phần bằng chứng.**

---

## Một lỗi của chính tôi

Commit `0c21f6d` mang thông điệp *"0 → 49 test; cửa đo nói 28/37 và 50/85, CẢ
HAI TRƯỢT"*. Nhưng chính commit ấy ghi `tests/test_lat_nguoc.py | 1450` dòng —
tức lúc commit, cả hai bên **đã viết xong**, và trạng thái thật là **68 test,
36/37 và 75/85, cả hai ĐẠT**.

Tôi đo lúc tệp còn 1.047 dòng rồi commit sau khi nó đã thành 1.450, mà mang
theo con số cũ. **Lần thứ hai trong một ngày tôi đo một thứ đang đổi dưới tay**
— lần trước là chạy bộ đề 5 trong khi đang sửa chính hai tệp nó gieo lỗi vào.

Luật rút ra, cùng họ với §4 *"phép đo lấy giờ thật là phép đo xanh theo lịch"*:

> **Con số trong thông điệp commit phải đo trên đúng thứ đang được commit.**
> Đo xong mà chưa commit ngay thì phải đo lại, hoặc ghi rõ số ấy đo lúc nào.
