# Gửi Antigravity — Sếp đổi thiết kế giao diện

*21/08/2026. Đây KHÔNG phải soát lỗi. Sếp nêu hai thay đổi về hình dạng app, và
một trong hai gỡ luôn được một lỗi tôi vừa báo ở bản nghiệm thu giao diện.*

---

## 1. Thẻ = MỘT DÒNG MÃ, không phải biểu mẫu

Sếp vẽ thẻ trong hình dung của Sếp:

```
|import json|        |print("chao")|
```

Đúng một dòng mã, có viền, có màu theo loại. **Không có ô nhãn.**

Hiện tại thẻ là biểu mẫu nhiều ô — `ĐỊNH NGHĨA HÀM` với ô `Hàm:` và ô `Tham số:`.

### Vì sao đổi: nó gỡ luôn lỗi "45/199 thẻ là Mã thô"

Bản nghiệm thu hôm nay ghi: mở `core/web_search.py` thì **45/199 thẻ (23%)** rơi
xuống `Mã thô` vì không vừa khuôn biểu mẫu nào.

Với thẻ-một-dòng thì **"Mã thô" không còn là hỏng** — nó chỉ là một thẻ như mọi
thẻ khác. Bốn việc tôi xin sửa hôm nay **còn ba**.

Nó cũng chữa luôn tab Kịch Bản, thứ đang in ra
`Bước 1: Mã thô. Bước 2: Mã thô. Bước 3: Mã thô...`

### Đo được, để đặt kích thước

Đo trên app đang chạy, tệp `core/kiem_tien.py`, 56 thẻ:

```
chiều cao thẻ hiện nay   trung vị 140px  (nhỏ nhất 87, lớn nhất 2.302)
tổng cao canvas          18.749px, khung nhìn 720px  ->  26 màn cuộn
thẻ-một-dòng ~28px       1.568px                     ->  2,2 màn cuộn
                                                         gọn hơn 12 lần
```

Bề ngang, đo 6.435 dòng thật trong `core/`:

```
trung vị     32 ký tự
p90          73
p99          82
dài nhất    167
<= 80 ký tự  98,8% số dòng
```

Nên: khung thẻ tính cho **80 ký tự**; 1,2% còn lại **cắt bớt kèm tooltip đầy
đủ**, đừng xuống dòng — xuống dòng là mất tính "một dòng một thẻ".

Độ sâu lồng nhau:

```
tầng 0  18,8%     tầng 3  14,3%
tầng 1  29,7%     tầng 4   7,4%
tầng 2  22,6%     tầng >=5 7,2%
```

Thụt 24px/tầng thì tầng 6 đã ăn 144px. Đề nghị **16px/tầng**, và tầng ≥5 thì
thu về 8px để không đẩy thẻ ra khỏi khung.

### Sửa thẻ thì sửa thế nào

Thẻ là một dòng, nên sửa là **sửa chính dòng đó**: bấm vào thẻ → nó thành ô nhập
một dòng, gõ xong Enter là xong. Cấu trúc do **màu viền + thụt đầu dòng** kể,
không do ô nhãn kể.

Chỗ này giữ nguyên hợp đồng cũ: `the_cst` vẫn bảo toàn từng byte, thẻ chỉ là
lớp kính. Sếp đã nói từ 20/08: *"bản chất cái chúng ta làm chỉ là cái khung
trực quan trên giao diện, không ảnh hưởng đến bản chất code"*.

---

## 2. Bố cục ba cột như IDE thường

```
┌──────────────┬────────────────────────────┬──────────────┐
│  TRÁI        │  GIỮA                      │  PHẢI        │
│              │                            │              │
│  cây thư mục │  tệp đang mở (canvas thẻ)  │  AI / Agent  │
│    ⇅ chuyển  │  ────────────────────────  │              │
│  khay thẻ    │  terminal                  │              │
│  (dạng lưới) │                            │              │
└──────────────┴────────────────────────────┴──────────────┘
```

- **Trái**: cây thư mục và khay thẻ **chuyển qua lại được** — cùng một chỗ, đổi
  bằng tab hoặc nút, không phải hai cột riêng.
- **Khay thẻ để dạng LƯỚI**, không phải danh sách dọc như hiện nay. Lưới cho
  thấy nhiều loại thẻ cùng lúc trong một tầm mắt.
- **Giữa**: tệp đang mở ở trên, terminal ở dưới — chia đôi kéo được.
- **Phải**: chừa cho AI/Agent. Chưa cần cắm gì vào, cứ để khung.

Hiện nay ba tab `Mã Python` · `Mạch Nước Ngầm` · `Chẩn đoán` · `Kịch Bản` đang
nằm bên phải. Chúng thuộc về **giữa** (chúng nói về tệp đang mở), còn bên phải
để trống cho Agent.

---

## 3. Ngưỡng nghiệm thu — đặt trước

```
1. mở core/web_search.py
      số thẻ "Mã thô" đặc biệt          = 0   (mọi dòng đều là thẻ bình thường)
      tổng chiều cao canvas             < 3.000px   (nay 18.749px cho 56 thẻ)
2. thẻ dài nhất trong core/ (167 ký tự) hiển thị KHÔNG vỡ khung, có tooltip đủ
3. hàm sâu nhất (tầng 6) vẫn nằm trong khung 1280px, không cuộn ngang
4. khay thẻ dạng lưới: thấy được >= 8 loại thẻ cùng lúc ở cao 720px
5. chuyển cây thư mục <-> khay thẻ: 1 lần bấm, không mất trạng thái canvas
6. bốn tab về tệp nằm ở CỘT GIỮA; cột phải trống dành cho Agent
```

Mục 1 là mục chính. Hai con số ấy đọc thẳng từ DOM, không cần ai chấm bằng mắt.

---

## 4. Ba việc cũ vẫn còn nguyên

Bản nghiệm thu `docs/NGHIEM_THU_GIAO_DIEN_2026-08-21.md` xin bốn việc; việc "giảm
Mã thô" nay được thiết kế mới gỡ hộ. Ba việc còn lại **không đổi**, và việc số 1
vẫn nặng hơn tất cả:

1. **Luật "biến chưa gán" báo 84 lỗi giả** trên `core/web_search.py` — bỏ sót
   import, tham số hàm, hàm tự định nghĩa, biến vòng lặp, và hàm dựng sẵn.
   Ngưỡng: ba tệp `web_search.py` · `dong_ho.py` · `kiem_tien.py` đều phải ra
   **0 lỗi đỏ**.
2. **Băng-rôn khởi động sập** với console không phải UTF-8 (dòng 58
   `interface/the_app.py`), sập TRƯỚC khi mở cổng.
3. **Dải nhịp cắt theo hàm**, và đánh dấu nhịp chưa đóng.

Đổi giao diện mà chưa sửa việc 1 thì người mới vẫn mở một tệp chạy tốt ra và
thấy 84 dấu đỏ — chỉ là thấy trong một bố cục đẹp hơn.
