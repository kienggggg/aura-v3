# Gửi Antigravity — việc tiếp, và nó đến từ số liệu

*23/08/2026. Bốn hạng mục vòng trước tôi đã kiểm tĩnh: đúng cả bốn. Việc dưới
đây không có trong kế hoạch nào — nó lộ ra từ phép đo ngoài họ đang chạy.*

---

## 1. E1 ĐANG GIẤU thứ đáng nói nhất với người học

Phép đo trên 64 lỗi **ngoài năm họ** của E1, tới đề thứ 60:

```
khong_tim_thay              48
ung_vien_khong_qua_suite     8      <- chỗ này
khong_do_duoc                4
tim_thay                     0
```

Tám ca `ung_vien_khong_qua_suite` nghĩa là: **E1 tìm được một phép lật làm TEST
ĐÍCH xanh, nhưng chạy cả bộ thì đỏ, nên nó từ chối.**

Không có cửa chạy-cả-bộ ấy thì đó đã là **tám bản vá SAI được đề nghị cho người
dùng**. Cửa đang làm việc thật.

Nhưng giao diện hiện chỉ nói được hai câu: *"tìm thấy"* hoặc *"không tìm thấy"*.
Với tám ca này, người dùng thấy **"không tìm thấy"** — trong khi sự thật là:

> *"Tôi tìm được 1 chỗ làm test bạn đang nhìn xanh lên, nhưng sửa chỗ đó thì
> hỏng 3 test khác. Nên tôi KHÔNG đề nghị nó."*

Câu thứ hai dạy người mới đúng bài học đắt nhất của cả tuần này: **xanh không
phải đúng.** Câu thứ nhất không dạy gì.

### Xin

```
Trong candidates ĐÃ CÓ SẴN full_suite_status = "ĐỎ" cho những ca ấy.
Chỉ cần đưa ra màn hình, đừng lọc bỏ.

Giao diện, khi trang_thai == "ung_vien_khong_qua_suite":
    hiện danh sách ứng viên bị loại, mỗi dòng có:
        dòng số mấy · phép gì · vì sao bị loại (mấy test khác hỏng)
    và MỘT CÂU giải thích, đúng chữ này hoặc tương đương:
        "Những chỗ dưới đây làm test bạn đang xem XANH, nhưng làm ĐỎ chỗ khác.
         Sửa một chỗ mà hỏng chỗ khác thì không phải sửa."

    KHÔNG có nút "Áp dụng" cho nhóm này.
```

### Ngưỡng đặt trước

```
1. dựng một ca ung_vien_khong_qua_suite (bộ đề de_ngoai_ho.json có 8 ca),
   gọi /api/dinh_vi_loi, giao diện phải hiện >= 1 ứng viên bị loại
   kèm số test khác bị hỏng.
2. nhóm bị loại KHÔNG có nút "Áp dụng bản vá".
3. 618 test vẫn xanh.
```

---

## 2. Việc thứ hai — SỐ ĐÃ CHỐT, làm được ngay

Phép đo xong. **0/64.**

```
họ              số đề  tìm ra  không tìm  ứng viên bị loại  không đo được
binop               6       0          6                 0              0
bo_return          19       0         12                 5              2
doi_bien           24       0         23                 1              0
doi_thu_tu         15       0          9                 4              2
──────────────────────────────────────────────────────────────────────────
TỔNG               64       0         50                10              4
```

Đã thử lại 8 đề trên bản `lat_nguoc.py` MỚI (sau khi gộp tracer): cùng kết
luận, `0/8`, và thời gian mỗi đề giảm **39s → 23s**.

Xin in câu này lên giao diện, cạnh dòng phạm vi hiện có:

```
"Chỉ dò được 5 họ lỗi so sánh/logic.
 Đã thử 64 lỗi NGOÀI 5 họ đó — không dò ra ca nào."
```

Câu thứ hai biến một lời hứa thành một con số tra lại được. Sổ ở
`data/evidence_sprint/e1_ngoai_ho.json`, bộ đề ở
`experiments/evidence_sprint/de_ngoai_ho.json`, chạy lại bằng:

```
venv\Scripts\python.exe -X utf8 experiments\evidence_sprint\do_e1_ngoai_ho.py
```

**Ngưỡng:** con số trên màn hình phải đọc từ sổ, đừng chép cứng vào HTML — chạy
lại phép đo mà ra số khác thì màn hình phải đổi theo.

### Một ghi chú về cách chạy, đắt hơn nó có vẻ

Phép đo khởi động **09:39:06**, Antigravity sửa `core/lat_nguoc.py` lúc
**09:54:38**. Python nạp mô-đun một lần lúc chạy, nên cả lượt đo dùng bản CŨ —
không nhiễu giữa chừng, nhưng mô tả bản trước 09:54. Vì thế mới phải chạy lại
8 đề bằng tiến trình mới.

Cùng bài học tôi đã vấp hôm qua lúc nghiệm thu giao diện: **sửa `.py` xong mà
không khởi động lại thì đang nghiệm thu bản cũ.**

---

## 3. Bốn hạng mục vòng trước — đã kiểm tĩnh, đúng cả

```
"ma" trong candidates          lat_nguoc.py:396 · _worker_e1_exec.py:259
TraceResult.dong_da_chay       có
tracer tự chế trong lat_nguoc  còn 0 chỗ, đã dùng chot_test_can_trace
the_api tự suy tep_test        dòng 823 tests/test_{tên}.py
                               dòng 830 lệch quy ước mới đòi whitelist
```

Mục cuối làm **đúng đường tôi đề nghị**, không phải cách tự-mở-để-qua-cửa mà
kế hoạch ban đầu định làm. Đó là chỗ Antigravity tự sửa hướng sau khi nghe, lần
thứ hai trong loạt này.

Tôi sẽ chạy `pytest` và bộ 7 cửa cứng sau khi phép đo xong, để hai thứ không
giành CPU, rồi báo cả hai một lượt.
