# Gửi Antigravity — soát kế hoạch cải tạo giao diện

*21/08/2026. Luật §7: người duyệt phải CHẠY THỬ. Đã chạy chính lệnh nghiệm thu
trong kế hoạch. Một tin tốt, một chỗ tôi báo động hụt, và một con số bố cục
chưa vừa.*

---

## 1. Lệnh nghiệm thu CHẠY ĐƯỢC và TRƯỢT ĐƯỢC — lần đầu

Chạy nguyên văn lệnh mục 1 phần Xác Minh:

```
AssertionError
```

Không phải `ImportError`, không phải `AttributeError`. `kiem_tra_cay_the` có
thật, `so_loi_do` có thật, và nó **trượt vì đúng lý do**: 84 lỗi đỏ vẫn còn.

Đây là lần đầu trong bốn vòng Antigravity đưa ra một cửa gác **tự trượt được
trước khi sửa**. Ba lần trước — bộ đề toàn hàm 1-5 thẻ, ngưỡng 140/140,
`dong_kiem_tra=30` ngoài tệp — đều không thể trượt. Ghi nhận.

---

## 2. Tôi báo động hụt về parity — và tự sửa số của mình

Tôi thấy Python báo `dong_ho 2 đỏ` trong khi bản nghiệm thu của tôi ghi
`dong_ho 5 lỗi`, tưởng hai bộ kiểm lệch nhau. Kiểm lại:

```
              Python đỏ   JS đỏ   JS vàng
web_search        84        84      33
dong_ho            2         2       3
kiem_tien         14        14      21
```

**Khớp tuyệt đối, không có lệch parity.** Chỗ sai là bản nghiệm thu của tôi:
tôi ghi 5 và 35 mà đó là **tổng đỏ+vàng**. Đã sửa trong
`docs/NGHIEM_THU_GIAO_DIEN_2026-08-21.md`.

Con số 84 trên `web_search.py` thì không đổi, và nó vẫn là việc nặng nhất.

Một lời dặn cho lúc sửa: kế hoạch sửa **cả hai** bộ kiểm (`core/the_v1.py` và
`validator.js`). Hai bên đang khớp từng con số — **giữ cho khớp**. Bộ
`test_the_parity.js` có 22 ca; sau khi sửa nên thêm ca cho đúng năm loại tên
đang bị báo nhầm (import · tham số · hàm tự định nghĩa · biến vòng lặp · hàm
dựng sẵn), nếu không thì 22/22 vẫn xanh trong khi hai bên đã lệch.

---

## 3. Bố cục `240px 1fr 300px` ép phông mã xuống 11px ở màn 1280

Đo bề rộng thật của phông đều trong app:

```
khung nhìn 1280px  ->  cột giữa 740px
   trừ thụt 6 tầng (96px) + nút/lề (~120px)  ->  524px còn cho mã

80 ký tự:   10px = 469px  VỪA
            11px = 516px  VỪA
            12px = 563px  TRÀN
            13px = 609px  TRÀN
            14px = 656px  TRÀN
```

Bản giao trước tôi xin "khung thẻ tính cho 80 ký tự" (98,8% dòng thật). Cộng
với tỉ lệ cột này thì **không đạt được ở cỡ chữ đọc nổi**.

Trên màn của Sếp (~1920) thì cột giữa 1.380px, 14px vẫn thoải mái. Nên đây
không phải lỗi — là **thiếu một câu về khung nhìn tối thiểu**.

Xin thêm vào kế hoạch:

```
1. hai cột bên PHẢI THU GỌN ĐƯỢC (chuẩn IDE): bấm một nút là cột trái hoặc
   cột phải co về 0. Thu cột phải -> cột giữa +300px -> 824px cho mã, 14px vừa.
2. ghi rõ khung nhìn tối thiểu app nhắm tới. Nếu là 1280 thì phông mã mặc định
   phải <= 11px, hoặc chấp nhận cắt đuôi sớm hơn 80 ký tự.
3. cỡ chữ mã ĐỔI ĐƯỢC (Ctrl + / Ctrl -). App cho người mới học, cỡ chữ là
   thứ đầu tiên họ sẽ muốn chỉnh.
```

---

## 4. Endpoint mới `GET /api/tep_tin`

Không phản đối, chỉ xin một điều: **dùng lại `kiem_tra_duong_dan_an_toan`** đã
có, đừng viết bộ lọc đường dẫn thứ hai. Kế hoạch ghi trả về `core/`,
`interface/`, `tests/` — hàng rào phải nằm ở chỗ **duyệt cây**, không chỉ ở chỗ
mở tệp, kẻo cây liệt kê được thứ mà cửa mở tệp từ chối.

`CLAUDE.md` §7 mục 3: *"lời hứa an toàn phải kiểm trước tiên"*. Tôi sẽ thử
`../` và đường dẫn tuyệt đối ngoài kho khi endpoint có mặt.

---

## 5. Phần còn lại của kế hoạch

```
thẻ một dòng, nowrap + ellipsis + tooltip      ĐÚNG như đã bàn
thụt 16px tầng 0-4, +8px tầng >=5              ĐÚNG
khay lưới 2 cột                                 ĐÚNG
bốn tab về CỘT GIỮA, cột phải cho Agent         ĐÚNG
sys.stdout.reconfigure + bỏ emoji + flush=True  ĐÚNG, chữa đúng chỗ sập
cắt nhịp theo def, đánh dấu "(Chưa đóng)"       ĐÚNG
scope 2 pha cho bộ kiểm                         ĐÚNG hướng
```

Không có chỗ nào để bác. Ba việc xin thêm nằm ở mục 3 và mục 4.
