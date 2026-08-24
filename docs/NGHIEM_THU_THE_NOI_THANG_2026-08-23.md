# Nghiệm thu thẻ nối thẳng + chú thích + ba cột — 23/08/2026

*Claude chạy lại mọi thứ và đo bằng DOM. Bốn trong năm ngưỡng về thẻ ĐẠT.
Một ngưỡng trượt, và nó trượt đúng chỗ tôi cảnh báo trước — nhưng nguyên nhân
khác điều tôi đoán.*

---

## 1. Đã kiểm, đúng cả

```
pytest test_the_cst + test_the_v1      27 passed
node test_the_connector_ui + e1_ui     10 pass, 0 fail
node test_the_parity.js                27/27
lossless core/*.py                     23/23 khớp từng byte
```

### Thẻ chú thích — làm đúng, kể cả chỗ khó

```
core/web_search.py    chu_thich = 81      (ngưỡng >= 80)
core/dong_ho.py       thẻ đầu tiên = ma_tho, nội dung '# -*- coding: utf-8 -*-'
```

**Dòng ma thuật an toàn.** Luật tôi xin ở vòng trước được cài đúng cách rẻ nhất:
giữ nguyên trong `ma_tho`, không cho nó thành thẻ kéo được.

### Bốn cửa cứng — mặc định đã đảo

```
dòng 566   dung_cst = "--v1" not in sys.argv        <- mặc định là CST
dòng 581   print("so   : " + str(RA / ten_so))      <- cái bẫy đã bịt
chạy thử   [1/4] ... [2/4] ... [3/4] ... [4/4]      <- đã in tiến trình
```

Cả ba việc tôi xin ở mục 4 vòng trước đều xong.

### Bố cục ba cột — lần này tôi kiểm NỘI DUNG từng cột

```
cột trái    "Khay Thẻ / Cây Thư Mục" — có nút đổi
cột phải    "🤖 Agent AURA" — 0 tab về tệp
cột giữa    4 tab: Mạch Nước Ngầm · Chẩn đoán · Kịch Bản · Terminal
tab "Mã Python"                                     đã bỏ
```

Vòng trước tôi đo `grid-template-columns` rồi kết luận đạt, mà không mở ra xem
trong cột có gì. Lần này mở.

---

## 2. Năm ngưỡng về thẻ — đo trên `core/web_search.py`, 281 thẻ

```
N1  bề ngang bỏ trống      8%     <= 20%    ĐẠT   (trước: 88%)
N2  cao trung vị          20px    <= 20px   ĐẠT   (trước: 28px)
N4  số màu nhánh rẽ         5     >= 3      ĐẠT
N5  lỗ lệch viền trái       0     <= 1px    ĐẠT
N3  cột dọc lệch tâm      17px    <= 2px    TRƯỢT  trên 50 khối
```

Thẻ trung thành với trang mẫu: `.lo` là `position:absolute` nên không ăn bề
ngang, đệm `1px 12px`, tâm lỗ nằm **đúng trên viền**.

---

## 3. N3 TRƯỢT — nhưng hàm KHÔNG sai

Tôi tưởng họ tính bằng phần trăm như tôi từng làm hỏng. **Không phải.** Hàm
`chinhCotDoc()` ở `app.js:276` viết **y hệt** bản tôi đưa, và được gọi ở bốn
chỗ (715 · 1899 · 1908 · 2154).

Đo thẳng:

```
vừa mở tệp xong        0/50 khối có biến --cao-cot     lệch 17px
phát sự kiện resize   50/50 khối có biến               lệch  0px
```

**Hàm đúng. Nối vào `resize` đúng. Chỉ đường MỞ TỆP là hụt.**

Ở `renderCanvas()` nó gọi qua `requestAnimationFrame(chinhCotDoc)` — một khung
hình sau. Trên đường mở tệp, có một lượt render nữa xảy ra **sau** khung hình
ấy, dựng lại toàn bộ `.khoi` mới, nên biến vừa đặt bị xoá cùng DOM cũ.

Bằng chứng: tôi đặt tay cả 50 khối, vài giây sau đo lại còn **0/50** — có thứ
đã thay DOM.

```
XIN: gọi chinhCotDoc() SAU khi lượt render cuối cùng xong.
     Rẻ nhất: cuối `onTreeChanged`, hoặc double rAF:
        requestAnimationFrame(() => requestAnimationFrame(chinhCotDoc));

NGƯỠNG: mở core/web_search.py, KHÔNG đụng cửa sổ,
        đếm khối có --cao-cot  =  50/50
        lệch lớn nhất          <= 2px
```

Chỗ này đáng nói vì **mắt thường không bắt được**. Lệch 17px trên một khối 200px
trông vẫn "gần đúng". Chỉ có `getBoundingClientRect()` mới thấy.

---

## 4. Một ngưỡng CỦA TÔI đặt sai — sửa lại

Bản giao ghi: *"`core/the_v1.py`, ngưỡng >= 20 `duoi_dong` hiện rõ"*.

Đo thật: `the_v1.py` có 16 chú thích cuối dòng, nhưng **chỉ 1 nằm trên thẻ
thật**; 15 nằm trong vùng `ma_tho`, nơi chúng được giữ **nguyên văn** và không
cần cơ chế `duoi_dong`.

Tương tự `web_search.py`: 6 chú thích cuối dòng, cả 6 nằm **giữa khối nhiều
dòng** (dòng thứ 2/5, thứ 13/43, thứ 42/55...) — thuộc nội dung khối, không
phải cuối câu lệnh.

Tôi đếm bằng `tokenize` trên cả tệp, trộn **ba loại chú thích khác nhau** rồi
đặt ngưỡng lên con số trộn ấy. Ngưỡng sai, không phải bản cài đặt sai.

Cửa 2 của công cụ đo đúng thứ cần đo: *"dòng có chú thích do thẻ thật quản: 33,
giữ được 33, MẤT 0"*.

---

## 5. Còn lại

Bốn cửa cứng đang chạy (8 phút/lượt). Báo cáo của Antigravity ghi **ĐẠT cả bốn,
exit 0, 86 tệp, 8219 thẻ**. Tôi sẽ đối chiếu khi lượt chạy của tôi xong.

Việc còn mở: **đúng một** — N3, một lần gọi hàm.
