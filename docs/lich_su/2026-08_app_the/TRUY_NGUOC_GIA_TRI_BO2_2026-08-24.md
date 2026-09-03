# Bộ đề thứ hai — luật im lặng KHÔNG đứng vững ngoài bộ đề sinh ra nó

*24/08/2026, tiếp theo `TRUY_NGUOC_GIA_TRI_2026-08-24.md`. Bộ 1 gợi ý một luật
sửa: im lặng khi chuỗi chỉ có một dòng. Bộ 2 — bốn tệp hoàn toàn khác, sinh
bằng cùng máy — dùng để kiểm luật ấy có phải ngẫu nhiên hợp với riêng bộ 1 hay
không. **Không đứng vững.** Và lý do tìm ra được không phải may rủi thống kê,
mà là một hình dạng mã cụ thể mà bộ 1 không có.*

---

## 1. Bộ đề 2 — độc lập bằng cách nào

Máy sinh đề (`dung_de_ngoai_ho.py`) không có hạt giống ngẫu nhiên nào — nó liệt
kê tuần tự và lấy N đề đầu mỗi họ mỗi tệp. Nên "sinh lại với hạt giống khác"
không tồn tại. Độc lập thật phải đổi **mã nguồn**:

```
bộ 1   may_tinh · web_search · dong_ho · loai_cau_hoi        64 đề
bộ 2   secret_guard · user_memory · doc_so_phien · kiem_tien 76 đề
       (không trùng một tệp nào với bộ 1)
```

Thêm cờ `--bo2` vào chính generator, không chép tệp.

4/76 đề vỡ ngay lúc thu thập (`ERROR collecting` — mô-đun không import được)
— tách riêng, không tính vào tử/mẫu số của phần trăm.

---

## 2. Cửa cũ (nói mọi lúc) — vẫn không đạt, cùng kiểu

```
                              bộ 1         bộ 2
1. dòng lỗi trong chuỗi     32/64 ĐẠT    31/76 TRƯỢT (ngưỡng >=32)
2. dài chuỗi, trung vị          2 ĐẠT        2 ĐẠT
3. chuỗi rỗng mà vẫn báo       15 TRƯỢT     12 TRƯỢT
4. thu hẹp, trung vị        0,20 ĐẠT     0,12 ĐẠT
5. model_calls                  0 ĐẠT        0 ĐẠT
```

Nhất quán: cửa 3 đỏ ở cả hai bộ, đúng lý do đã biết — chuỗi một dòng là
traceback cho không, không phải phát hiện thật.

---

## 3. Luật im lặng — dự đoán từ bộ 1 SAI trên bộ 2

Bộ 1 (tính lại): trả lời 26/63, đúng 17 sai 9 → **chính xác 65%**.

Bộ 2, cùng luật, chạy trên dữ liệu chưa từng thấy:

```
                          bộ 1 dự đoán    bộ 2 thực đo
trả lời                  26/63 (41%)     39/72 (54%)
trong đó đúng            17              19
trong đó SAI              9              20
chính xác khi trả lời    65%             49%   <- gần bằng tung đồng xu
```

```
NGƯỠNG                          bộ 2 THỰC ĐO
1. chính xác khi nó nói  >=0,60   0,49   TRƯỢT
2. im lặng bỏ SAI>=ĐÚNG           21/12  ĐẠT
3. độ phủ               >=0,25   0,54   ĐẠT
4. thu hẹp trung vị      <=0,50   0,14   ĐẠT
5. model_calls            =0     0      ĐẠT
```

**Trượt đúng ngưỡng quan trọng nhất.** Luật "im lặng khi chuỗi một dòng" đúng
là *loại bớt được* câu sai (mục 2 vẫn đạt: bỏ 21 sai so với 12 đúng), nhưng khi
nó **đã chịu trả lời** thì độ tin cậy rơi từ 65% xuống 49% — không hơn tung
đồng xu là bao.

---

## 4. Vì sao — không phải ngẫu nhiên, mà là một hình dạng mã cụ thể

Theo tệp, chỉ tính nhóm "có trả lời" (chuỗi > 1 dòng):

```
tệp                 số ca    đúng
doc_so_phien.py       10     6  (60%)
kiem_tien.py           9     8  (89%)
secret_guard.py        9     2  (22%)
user_memory.py        11     3  (27%)
```

Hai nhóm tách bạch rõ. `doc_so_phien` và `kiem_tien` là tiện ích thuần —
tương tự bộ 1. `secret_guard` và `user_memory` là **mã tích hợp**, gọi qua
`ChatService` với lớp `try/except Exception` bọc bên ngoài.

### Một ca cụ thể, lần theo tận gốc

Đề: `core/secret_guard.py`, họ `doi_bien`, dòng 45 —
`raw = (text or "").strip()` bị đổi thành `raw = (cleaned or "").strip()`.
`cleaned` không hề tồn tại trong hàm `is_secret_request` (nó là biến cục bộ
của một hàm **khác**, `scrub_for_log`) — đột biến này là NameError chắc chắn.

Vết chạy thật:

```
buoc=4   dong=45   is_secret_request bắt đầu chạy
buoc=6   dong=45   <tra_ve>=None      <- NameError, hàm CHẾT ngay
buoc=8   dong=74   <tra_ve>=None      <- lan lên hàm gọi, CŨNG chết
        ... (10 bước sau, một nhánh KHÁC của cùng một test) ...
buoc=40  dong=111  <tra_ve>=OutwardContent(...)   <- giá trị HỢP LỆ
```

`core/chat_service.py:371` gọi `self._guard.check_input(request)` bên trong
một khối có `except Exception` bọc quanh (dòng 583, 612, 675...). NameError bị
**nuốt lặng lẽ**, pipeline rẽ sang nhánh dự phòng, rồi tính tiếp qua
`scrub_output` — một đường hoàn toàn không dính đột biến — và trả về một giá
trị **hợp lệ, không sai**.

`_moc_bat_dau` của tôi chỉ nhận ra "chương trình chết" khi cú gỡ ngăn xếp nằm
**ở cuối vết**. Ở đây cú chết nằm ở **giữa** vết (bước 6-8), còn cuối vết là
một tính toán khác, đúng, không liên quan. Máy lấy nhầm mốc — không phải vì
thuật toán sai logic, mà vì **giả định "crash luôn ở cuối" chỉ đúng với mã
đơn giản, không đúng với mã có lớp exception-handling phòng thủ.**

Bộ 1 toàn hàm thuần (`may_tinh`, `dong_ho`...), không có lớp bọc nào — nên giả
định ấy chưa từng bị lộ. Bộ 2 có `secret_guard`/`user_memory` nằm sau
`ChatService` — lộ ngay.

---

## 5. Kết luận

**Luật im lặng rút từ bộ 1 không tổng quát hoá.** Không phải vì bộ 2 khó hơn
ngẫu nhiên, mà vì nó chứa một **hình dạng mã cụ thể** (crash bị nuốt bởi lớp
xử lý ngoại lệ ở tầng trên) mà thuật toán truy ngược chưa xử lý.

Sửa được không phải bằng cách nới ngưỡng, mà bằng cách sửa **giả định**: mốc
bắt đầu phải quét toàn vết tìm bước `<tra_ve>=None` **sớm nhất** có nằm ngay
sau khi tham số hàm được đọc mà chưa từng ghi (dấu hiệu NameError/AttributeError
giữa hàm), không chỉ nhìn đuôi vết. Đó là việc mới, chưa làm, và phải đăng ký
ngưỡng rồi kiểm trên **bộ đề thứ ba** trước khi tin.

**Không cài luật im lặng vào app.** Nó chưa qua nổi bài kiểm tra độc lập đầu
tiên.

---

## 6. Số liệu đầy đủ

```
bộ 2: 76 đề, 4 không đo được (vỡ lúc thu thập), 72 đo được
dòng đã chạy, trung vị    18
thu hẹp, trung vị       0,12
giây/đề, trung vị        8,8
model_calls                0
```
