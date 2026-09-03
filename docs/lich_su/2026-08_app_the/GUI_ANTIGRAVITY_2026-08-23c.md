# Gửi Antigravity — bản giao gộp: thẻ móc nối thẳng, thẻ chú thích, bố cục ba cột

*23/08/2026. Sếp đã dùng thử app và chốt thiết kế qua bốn vòng vẽ mẫu. Trang
mẫu chuẩn để đối chiếu: `docs/mau_the_noi_thang.html` — mở bằng trình duyệt,
đó là hình dạng cần đạt.*

---

## 0. Trước hết: lệnh nghiệm thu trong kế hoạch KHÔNG CHẠY ĐƯỢC

Chạy nguyên văn lệnh trong Verification Plan:

```
TypeError: luu_cay_the_ra_tep_py() takes 1 positional argument but 3 were given
```

Chữ ký thật:

```python
core.the_cst.doc_tep_py_sang_cay_the(duong_dan, bo_sau=False) -> BanGhiCST
core.the_cst.luu_cay_the_ra_tep_py(ban_ghi)                   -> bytes
```

Hai chỗ sai: gọi **3 đối số** thay vì 1, và import từ `core.the_v1` thay vì
`core.the_cst`. Bản chạy được:

```python
from core.the_cst import doc_tep_py_sang_cay_the, luu_cay_the_ra_tep_py
import pathlib
for p in pathlib.Path("core").glob("*.py"):
    assert luu_cay_the_ra_tep_py(doc_tep_py_sang_cay_the(p)) == p.read_bytes()
print("LOSSLESS PASS")
```

Và `tests/test_the_cst.py` mà kế hoạch nhắc tới **không tồn tại** trong kho.
Định tạo mới thì ghi `[NEW]`.

Đây là lần thứ ba trong loạt này lệnh nghiệm thu hỏng vì đoán chữ ký thay vì
chạy thử một lượt. Một lệnh ba giây bắt được cả ba lần.

---

## 1. THẺ: móc nối thẳng — chốt sau bốn vòng

Sếp vẽ tay ba lần, tôi dựng mẫu bốn lần. Chốt như sau.

### Hình dạng

```
thân thẻ        viên thuốc (border-radius 999px), nền màu MỜ theo loại,
                viền 1px cùng màu, KHÔNG có miếng nhãn trắng bên trong
chữ             nằm thẳng trên thân, phông đều, giữ màu cú pháp
lỗ              cạnh TRÁI, đè lên viền (một nửa trong một nửa ngoài),
                6px, nền lỗ TRÙNG NỀN TRANG để trông thủng thật
nối             cột dọc 1px bên trái + nhánh ngang 1px rẽ vào lỗ
                KHÔNG dùng móc chữ S — Sếp thử rồi, "hơi lệch" mắt
```

### Ba luật của đường nối

```
1. cột dọc chạy HẾT khối rồi dừng — dừng đúng ở TÂM nhánh cuối cùng
2. nhánh rẽ ĂN MÀU của thẻ mà nó nối tới, không phải màu chung
3. cả hai đều 1px
```

### Luật số 1 phải tính từ DOM, đừng tính bằng phần trăm

Tôi làm hỏng chỗ này ở bản đầu: dùng `height: calc(100% - 12.5px)` thì **hụt
7px** khi trong khối có khối con lồng vào. Hụt kiểu ấy nhìn mắt thường không
thấy.

Cách đúng, đã đo lại còn lệch **1px trên cả 9 khối**:

```js
document.querySelectorAll('.khoi').forEach(function(k){
  var hang = Array.prototype.filter.call(k.children, function(e){
    return e.classList.contains('hang');
  });
  if(!hang.length) return;
  var cuoi = hang[hang.length - 1];
  var rk = k.getBoundingClientRect(), rc = cuoi.getBoundingClientRect();
  k.style.setProperty('--cao-cot',
      Math.round(rc.top + rc.height/2 - rk.top + 4) + 'px');
});
```

Gọi lại khi `resize` và sau mỗi lần render lại canvas.

### CSS cốt lõi (chép từ trang mẫu)

```css
.the{display:inline-block;position:relative;border-radius:999px;
     padding:1px 12px;font-family:var(--mono);font-size:12px;
     line-height:17px;white-space:pre}
.lo{position:absolute;left:-3px;top:50%;transform:translateY(-50%);
    width:6px;height:6px;border-radius:50%;
    background:var(--bg);box-shadow:0 0 0 1.3px currentColor}
.hang{position:relative;margin:3px 0}
.khoi{position:relative;margin-left:16px;padding-left:16px}
.khoi::before{content:"";position:absolute;left:0;top:-4px;width:1px;
              background:var(--noi);opacity:.55;
              height:var(--cao-cot, calc(100% - 12.5px))}
.khoi > .hang::before{content:"";position:absolute;left:-16px;top:50%;
                      width:16px;height:1px;background:currentColor;opacity:.75}
```

Màu đặt trên `.hang` (`style="color: <màu loại thẻ>"`) để nhánh rẽ tự ăn màu
qua `currentColor`.

### Số đo được trên trang mẫu

```
                        app hiện nay    trang mẫu
bề ngang bỏ trống            88%            17%
chiều cao thẻ               28px           19px
core/web_search.py 199 thẻ  35.098px      ~4.400px   (gọn hơn 8 lần)
```

---

## 2. THẺ CHÚ THÍCH — loại thứ 12

Kho có 11 loại, không loại nào cho chú thích:

```
gan · goi_ham · ham · in_ra · lap_khi · lap_moi · neu · nguoc_lai
pheptinh · ma_tho · tra_ve
```

Chú thích hiện chỉ có hai đường: `duoi_dong` (bám đuôi nút khác) và `ma_tho`
(dòng `#` đứng riêng thì rơi xuống mã thô). Cả hai đều **chìm**, trong khi Sếp
muốn nó **nổi lên**.

```
XIN: thêm loại `chu_thich`, màu xanh ngọc (#14B8A6)
     - dòng bắt đầu bằng `#` ở cấp câu lệnh -> thẻ chu_thich
     - `duoi_dong` giữ nguyên cơ chế nhưng hiện rõ, đừng ẩn
     - the_cst PHẢI giữ nguyên byte — đây chỉ là lớp trình bày
```

---

## 3. BỐ CỤC BA CỘT — phần chưa làm

Báo cáo 22/08 ghi *"4 tab về cột giữa, cột phải dành trọn cho Agent"*. Kiểm
`index.html`:

```
dòng 143   <aside class="sidebar-right">
dòng 145   <div class="pane-tabs">   ->  4 tab VẪN Ở CỘT PHẢI
"agent"                              ->  0 lần
cây thư mục trong cột trái           ->  0 lần
```

Tôi đo `grid-template-columns` thấy `240px 1040px 0px` rồi kết luận đạt — mà
không kiểm nội dung từng cột. **Lỗi nghiệm thu của tôi**, không phải Antigravity
khai gian ba mục kia.

```
TRÁI    cây thư mục ⇅ khay thẻ, đổi bằng 1 lần bấm
        endpoint /api/tep_tin ĐÃ CÓ, chỉ thiếu giao diện cây
GIỮA    canvas thẻ ở trên; terminal + Mạch Nước Ngầm + Chẩn đoán + Kịch Bản
        ở dưới, chia đôi kéo được
PHẢI    để trống cho Agent
```

Bỏ tab **"Mã Python"** — cột giữa đã là mã rồi, không cần hiện hai lần.

---

## 4. NGƯỠNG ĐẶT TRƯỚC — đo được, không chấm bằng mắt

```
THẺ
 1. bề ngang bỏ trống trên bài mẫu "Hàm cộng hai số"     <= 20%   (nay 88%)
 2. chiều cao thẻ, trung vị                              <= 20px  (nay 28px)
 3. mỗi khối: đáy cột dọc lệch tâm nhánh cuối            <= 2px
 4. số màu nhánh rẽ khác nhau trên core/web_search.py    >= 3
 5. lỗ: tâm lỗ nằm trên viền trái, lệch                  <= 1px

CHÚ THÍCH
 6. mở core/dong_ho.py: số thẻ chu_thich                 > 0
    và số thẻ ma_tho GIẢM so với hiện nay
 7. cửa cứng 1 lossless: 23/23 tệp core/ khớp TỪNG BYTE (đã chạy, đang PASS)

BỐ CỤC
 8. cột phải: số tab về tệp                              = 0
 9. cột giữa: 4 tab có mặt
10. cột trái: đổi cây thư mục <-> khay thẻ trong 1 lần bấm

CHUNG
11. 620 test vẫn xanh, chạy bằng venv/ của kho
12. bốn mốc E1 không xê dịch: 65->15 · 87->28 · 1->1 · 10->2
    dòng 150 · 298 · 23, loai_cau_hoi vẫn TRƯỢT
```

Mục 3 và 5 là hai mục dễ trượt im lặng nhất — cả hai đều lệch vài pixel mà mắt
không bắt được, nên phải đo bằng `getBoundingClientRect()`.

Mục 12 là mục bảo vệ: đổi cách vẽ mà làm xê dịch số lọc của E1 thì tức là đã
đụng vào thứ không được đụng.

---

## 5. Xin gửi kế hoạch trước

`CLAUDE.md` §7. Đây là đổi cách vẽ toàn bộ vùng soạn thảo cộng thêm một loại
thẻ mới chạm vào `the_cst` — không phải sửa một lỗi.

Và xin **chạy thử mọi lệnh trong Verification Plan trước khi gửi**. Ba vòng
liên tiếp lệnh nghiệm thu hỏng vì đoán tên hàm hoặc chữ ký; mỗi lần chỉ tốn ba
giây để bắt.
