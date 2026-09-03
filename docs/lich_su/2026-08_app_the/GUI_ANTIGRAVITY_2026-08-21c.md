# Gửi Antigravity — soát vòng 3

*21/08/2026. Kế hoạch v3 nhận hết vòng 2, và phần chia nhịp giờ đã chấm được.
Nhưng bảng nghiệm thu trích ba thứ trên đĩa — kiểm cả ba thì **hai chỗ không
khớp**, và **một chỗ là lỗi của tôi**, không phải của Antigravity.*

---

## 1. LỖI CỦA TÔI — con số 3/3 là sai, đúng là 3/4

Vòng 1 tôi viết:

> *"E1 giải được 3/3 các bài toán lỗi đơn"*

Antigravity chép lại thành **"3/3 (100%)"** và dựng ngưỡng #3 lên đó:

> *"Trích xuất thành công ... **100%** các bài toán lỗi đơn trong `de_loi.json`"*

Mở sổ E1 ra đếm:

```
DE LOI DON: 4 de, giai duoc 3
   may_tinh.py      1 loi   xanh   40,5s
   web_search.py    1 loi   xanh   56,4s
   dong_ho.py       1 loi   xanh    0,9s
   loai_cau_hoi.py  1 loi   TRUOT   6,3s   <- de thu tu, toi bo sot
```

Có **4** đề lỗi đơn, không phải 3. E1 giải được **3/4 = 75%**.

**Hệ quả trực tiếp:** ngưỡng #3 đòi 100% sẽ **trượt ngay từ đầu** trên
`loai_cau_hoi.py` — không phải vì bộ trace hỏng, mà vì cái mốc để so đã cao hơn
thứ có thật trên đĩa.

Đề nghị sửa ngưỡng #3 thành:

```
trace phải bắt được chuỗi giá trị của biến đích trên  4/4  đề lỗi đơn
   (TRACE là việc khác với GIẢI — E1 giải được 3/4, nhưng trace thì
    phải chạy được cả 4; loai_cau_hoi.py là ca kiểm tra bộ trace có
    trung thực khi câu trả lời KHÔNG tìm ra hay không)
đối chiếu 3 đề E1 giải được -> giá trị phải KHỚP sổ
đề loai_cau_hoi.py          -> trace vẫn phải ra chuỗi, dù không giải được
```

Tách **trace được** khỏi **giải được** là chỗ quan trọng nhất trong cả trang
này. Gộp hai thứ vào một ngưỡng là lại đúng bệnh "xanh ≠ đúng".

Tôi đã sửa con số trong `docs/NGUONG_CUA_NGUOI_MOI_HOC_CODE_2026-08-20.md` và
`docs/GUI_ANTIGRAVITY_2026-08-21.md`.

---

## 2. Đường dẫn sổ E1 sai

```
kế hoạch ghi : experiments/evidence_sprint/lat_nguoc.json     <- KHÔNG CÓ
trên đĩa     : data/evidence_sprint/lat_nguoc.json            <- 3792 byte, 9 mục
```

`do_lat_nguoc.py` dòng 86 ghi ra `data/`, không phải `experiments/`.

---

## 3. `test_the_v1.py :: ham_cong` không tồn tại

Nhóm 1 trong bảng trích hàm `ham_cong` ở `tests/test_the_v1.py`. Tệp đó không có
hàm nào tên vậy — nó chỉ có 23 hàm `test_*`.

Có **18 hàm thật** đủ điều kiện Nhóm 1 (1-5 thẻ, đúng một nhịp trọn vẹn):

```
tep                  ham                      mat cat  nhip
dong_ho.py           cau_gio                  KKX      1
khay_the.py          bo_dau                   KKX      1
may_tinh.py          _doi_chu_thanh_ky_hieu   BKX      1
```

Đề nghị **`core/dong_ho.py :: cau_gio`** — nó cũng là đề E1 giải nhanh nhất
(0,9 giây), nên dùng chung được cho cả Nhóm 1 lẫn ngưỡng #3.

Xin để ý mặt cắt là `KKX` chứ không phải `KBX`: hàm một nhịp thật trong kho phần
lớn **không có thẻ B**. Bảng đang giả định `KBX`; renderer phải vẽ được nhịp
thiếu B.

---

## 4. Chỗ ĐÚNG

```
_public_http_url tai core/web_search.py:293      DUNG
0/79 hàm >= 6 thẻ ra đúng ba tầng                DUNG (0/54 + 0/25)
tách core/nhip_thuc_thi.py khỏi the_cst.py       DUNG
chặn theo số bước thay vì đồng hồ                DUNG
so giá trị với giá trị, không dò chuỗi con       DUNG
```

Bốn đáp án nhịp ở mục 3 (6 · 5 · 2 và Nhóm 1) tôi đã đo lại, khớp.

---

## 5. Một cảnh báo về ngưỡng "trace ≤ 5 giây"

Ngưỡng #3 đòi mỗi ca trace ≤ 5 giây. Sổ E1 cho thấy **thời gian LẬT** là 40,5s ·
56,4s · 0,9s · 6,3s.

Hai con số ấy đo hai việc khác nhau — lật là chạy test hàng chục lần, trace là
chạy **một lần**. Nên ≤ 5 giây có thể vẫn đạt. Nhưng nếu Giai đoạn 1 định dựng
lại kết quả E1 (chứ không chỉ trace một lần), thì trần 5 giây sẽ trượt, và trượt
vì lý do không liên quan đến chất lượng mã.

Xin ghi rõ trong kế hoạch **trace một lần** hay **dựng lại E1** — hai việc, hai
trần thời gian.
