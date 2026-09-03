# Nghiệm thu thẻ một dòng — 22/08/2026

*Claude đo lại bằng DOM trên app đang chạy. Hai ngưỡng ĐẠT. Nhưng lúc dò cây có
còn nguyên không thì đụng phải một lỗi CŨ, nặng, chưa ai bắt.*

---

## 1. Hai ngưỡng — ĐẠT

Đo trên `core/web_search.py`, 199 thẻ:

```
                        trước   ngưỡng      nay
chiều cao trung vị       63px   <= 32px     28px    ĐẠT
số thẻ cao > 40px      199/199  <= 5%       0/199   ĐẠT
```

Mọi thẻ đúng 28px. Bốn cửa gác chạy lại vẫn xanh (0·0·0 · 27/27 · 8 · 33).

Cây vẫn đọc được: 199 thẻ nằm phẳng trong DOM nhưng thụt lề vẽ bằng lề trái,
**5 mốc** — nhìn ra bậc. Cửa cứng 1 (lossless) vẫn xanh, nên **đường LƯU không
việc gì**.

---

## 2. LỖI CŨ, NẶNG: tab "Mã Python" sinh ra mã KHÔNG CHẠY ĐƯỢC

Đường **xem trước** (`sinh_ma_python`) khác đường **lưu** (`luu_cay_the_ra_tep_py`).
Đường lưu bảo toàn từng byte; đường xem trước thì:

```
sinh_ma_python() trên 22 tệp core/
   VỠ CÚ PHÁP: 20/22 tệp
```

Cùng một lỗi ở cả 20 tệp. Mở `dong_ho.py` ra xem:

```
23 | def cau_gio(now: datetime | None = None):
24 | """Một dòng tiếng Việt nói rõ bây giờ là lúc nào...
     ^ docstring nằm ở CỘT 0, lẽ ra thụt 4 dấu cách
```

Thẻ `ma_tho` giữ docstring **không được thụt vào thân hàm**. Mà `CLAUDE.md` §5
bắt buộc hàm nào cũng có chú thích, nên gần như tệp nào cũng vỡ.

Và dòng 23 còn thiếu `-> str`:

```
hàm có chú kiểu trả về      : 198
bị mất "-> ..." khi sinh    : 136  (69%)
```

**Vì sao chưa ai bắt được:**

```
cửa cứng 1        canh `the_cst` — đường LƯU. Không đụng `sinh_ma_python`.
test_the_parity   27 ca, cây tự dựng, hàm không có docstring -> không chạm lỗi.
test_the_v1       có ca `sinh_ma_python` nhưng là cây mẫu 10 thẻ, cũng không có
                  docstring trong thân hàm.
```

Lại đúng một bệnh: cửa gác canh **một đường**, còn đường kia hỏng suốt.

Đây **không phải lỗi của đợt cải tạo này** — nó có từ trước. Nhưng nó đáng sợ
vì cạnh tab ấy có nút **"Sao chép mã Python"**: người mới bấm copy rồi dán ra,
20/22 lần sẽ được một tệp không chạy.

### Xin hai việc, kèm ngưỡng đặt trước

```
1. thẻ ma_tho trong thân hàm phải THỤT theo cấp lồng
2. giữ "-> <kiểu>" khi sinh lại chữ ký hàm

NGƯỠNG:  sinh_ma_python() trên 22 tệp core/ phải PARSE ĐƯỢC 22/22
         số hàm mất "-> ..."  =  0/198
```

Lệnh chạy lại, không cần giao diện:

```python
from core.the_cst import doc_tep_py_sang_cay_the
from core.the_v1 import sinh_ma_python
import ast
from pathlib import Path
for p in sorted(Path("core").glob("*.py")):
    ast.parse(sinh_ma_python(doc_tep_py_sang_cay_the(p).tree))   # phải không nổ
```

---

## 3. Tóm lại

```
thẻ một dòng 28px          ĐẠT
2 ngưỡng đặt trước         ĐẠT cả hai
4 cửa gác                  xanh
đường LƯU (lossless)       nguyên vẹn
đường XEM TRƯỚC            VỠ 20/22 tệp  <- lỗi cũ, mới lộ ra
```

Toàn bộ danh sách việc từ bản nghiệm thu giao diện 21/08 nay đã xong. Việc mới
này không nằm trong danh sách ấy — nó lộ ra vì lần này tôi dò sang đường thứ
hai, đường mà chưa cửa gác nào canh.
