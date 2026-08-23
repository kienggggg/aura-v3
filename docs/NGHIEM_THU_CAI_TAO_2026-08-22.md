# Nghiệm thu bản cải tạo — 22/08/2026

*Claude chạy lại cả bốn cửa gác, thử hàng rào bảo mật bằng tay, và mở app đo
bằng DOM. Ba trạng thái: **đạt** · **đo được mà không đạt** · **không đo được**.*

---

## 1. Bốn cửa gác — ĐÚNG CẢ, chạy lại được

```
cửa 1  core/web_search.py 0 · dong_ho.py 0 · kiem_tien.py 0   mã thoát 0
cửa 2  node tests/test_the_parity.js        27/27 khớp 100%
cửa 3  pytest tests/test_the_app.py          8 passed in 0.78s
cửa 4  pytest 3 tệp cốt lõi                 33 passed in 18.77s
```

Trước khi sửa: **84 · 2 · 14**. Sau: **0 · 0 · 0**.

## 2. Luật được SỬA THẬT, không phải xoá

`84 → 0` có hai cách đạt: sửa luật, hoặc gỡ luật. Dựng bảy ca thử để tách:

```
SẠCH  len() dựng sẵn                              0 lỗi   OK
SẠCH  import re rồi dùng re.compile               0 lỗi   OK
SẠCH  tham số 'text: str, *, now: int | None'     0 lỗi   OK
LỖI   biến bịa hoàn toàn                          bắt     OK
LỖI   gõ nhầm tên module đã import (rre)          bắt     OK
LỖI   gõ nhầm tên hàm tự định nghĩa (bo_ddau)     bắt     OK
LỖI   tham số của hàm KHÁC dùng lọt sang hàm này  bắt     OK
                                                    7/7
```

Ca cuối là ca đáng giá nhất: nó chứng minh có **phạm vi thật**, không phải ném
hết vào một danh sách cho qua.

Đo lại trên giao diện: `web_search.py` còn **0 đỏ · 6 vàng** (trước là 84 · 33).

## 3. Hàng rào `/api/tep_tin` — tôi tự thử, giữ được

```
không token · token sai                        403
../ · ../../ · core/../../                     400
%2e%2e%2f (mã hoá URL) · ..%5c (backslash)     400
C:/Windows · D:/AURA_OS_v2 · //D:/...          400
venv (ngoài whitelist)                         403
core · CORE · core/. · chuỗi rỗng              200
```

Danh sách trả về: **66 tệp**, gốc chỉ có `core` 22 · `interface` 5 · `tests` 39.
**Không tệp nào ngoài whitelist.**

Ba ca trả 200 (`CORE` chữ hoa · `core/.` · chuỗi rỗng) đều quy về trong
whitelist, không rò.

## 4. Sập khởi động — đã hết

Chạy **không** `-X utf8`, console mặc định Windows:

```
  [*] AURA -- APP LAP TRINH BANG THE (BAN v1)
  * Ma thong hanh: 4f0a6e0f...        <- ra ngay, flush=True có tác dụng
```

Trước đây chết ở dòng 58 trước khi mở cổng. Nay không.

## 5. Bố cục — đúng như kế hoạch

```
grid 3 cột       "240px 1040px 0px"   <- cột phải TỰ thu gọn ở 1280
--code-font-size 14px
khay thẻ         "106.5px 106.5px"    <- lưới 2 cột
nút thu gọn      có cả trái lẫn phải
```

---

## 6. CHƯA ĐẠT: thẻ vẫn chưa phải MỘT DÒNG

Mổ một thẻ ra:

```
card-header-bar    26px   "Gán  ↑ ↓ 📋 ✕"          <- hàng nhãn loại + nút
card-body-content  35px   "Biến: [__] = [__]"      <- hàng biểu mẫu
                   ────
                    63px
```

Thẻ **thấp hơn** trước (140px → 63px, giảm 55%) nhưng vẫn là **biểu mẫu hai
hàng**. Thiết kế Sếp vẽ là **một hàng**: chính dòng mã, loại kể bằng **màu
viền** chứ không bằng hàng nhãn riêng.

Phân bố trên `core/web_search.py`, 199 thẻ:

```
trung vị  63px      p75 154px      p90 306px      lớn nhất 2.422px
số thẻ <= 32px:  0/199
số thẻ <= 40px:  0/199
```

Xin đúng hai việc:

1. **Gộp `card-header-bar` vào cùng hàng với nội dung.** Nhãn loại bỏ đi, thay
   bằng màu viền trái. Nút `↑↓📋✕` chỉ hiện khi rê chuột.
2. **Hàng nội dung hiện DÒNG MÃ**, không hiện `Biến: [__] = [__]`. Bấm vào mới
   thành ô sửa.

---

## 7. NGƯỠNG CỦA TÔI ĐẶT SAI — nhận và sửa

Bản giao `GUI_ANTIGRAVITY_2026-08-21h.md` mục 3 tôi viết:

```
mở core/web_search.py
   tổng chiều cao canvas  < 3.000px
   số thẻ "Mã thô" đặc biệt = 0
```

**Cả hai đều hỏng, và đều là lỗi của tôi.**

*Ngưỡng 3.000px là bất khả thi.* `web_search.py` có **199 thẻ**. Dù mỗi thẻ chỉ
30px — đúng một dòng — thì tổng đã là **5.970px**. Tôi viết một con số mà không
nhân thử. Cùng loại lỗi với ngưỡng `≥8/9` hôm 20/08 khi trần lý thuyết chỉ 3/9.

*Ngưỡng "Mã thô = 0" thì sai về khái niệm.* Chính tôi đã viết ở mục 1 của bản
giao ấy rằng với thẻ-một-dòng thì **"Mã thô" không còn là hỏng nữa**. Vậy mà
vẫn đặt ngưỡng đếm nó bằng 0. Hiện đang là 67 — nhưng con số ấy **không nói lên
điều gì** nếu mọi thẻ đều là một dòng.

Ngưỡng đúng, viết lại:

```
trên core/web_search.py (199 thẻ)
   chiều cao TRUNG VỊ của thẻ  <= 32px      (nay 63px)
   số thẻ cao > 40px            <= 5% (10 thẻ)   (nay 199/199 đều > 40px)
   thẻ nào cũng hiện đúng MỘT dòng mã, kể cả thẻ nội bộ gọi là ma_tho
```

Đo chiều cao **từng thẻ** thì đúng; đo **tổng canvas** thì lẫn với số lượng thẻ,
mà số lượng thẻ là do tệp dài chứ không do thiết kế.

---

## 8. Tóm lại

```
84 lỗi đỏ giả          ĐÃ CHỮA, và chữa đúng cách (7/7 ca thử)
hàng rào endpoint      GIỮ ĐƯỢC (tôi tự thử 13 đường vòng)
sập khởi động          ĐÃ CHỮA
bố cục 3 cột, 14px     ĐẠT
thẻ một dòng           CHƯA — còn hai hàng, 63px
```

Việc nặng nhất của đợt trước đã xong. Còn đúng một việc, và nó là việc **thuần
trình bày** — không đụng tới `the_cst`, không đụng tới bộ kiểm.
