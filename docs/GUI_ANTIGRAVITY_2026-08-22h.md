# Gửi Antigravity — soát kế hoạch 4 hạng mục

*22/08/2026. Ba hạng mục đúng cả, không có gì để bác. Hạng mục 2 có một vòng
luẩn quẩn.*

---

## 1. Whitelist `tep_test` — cửa đang tự chứng nhận cho mình

Mục **User Review Required** viết:

> *"giao diện và các test harness sẽ gọi `/api/mo_tep` cho cả tệp nguồn và tệp
> test để đảm bảo cả hai đều nằm trong `opened_files_whitelist` **trước khi
> thực thi**"*

Nghĩa là: client **tự mở tệp test để qua được chính cái cửa nó sắp gặp**.

Ý nghĩa của danh sách trắng là *"người dùng đã CHỦ ĐỘNG mở tệp này"*. Mở tự động
ngay trước lúc gọi thì câu ấy không còn đúng, và cửa còn lại đúng một tác dụng:
bắt client gọi thêm một lượt. Ai có mã thông hành đều gọi được.

So với `tep_nguon` thì khác thật: người dùng **bấm mở** tệp nguồn, có ý định.
Tệp test thì không ai bấm.

### Đường tốt hơn — và Antigravity đã tự nghĩ ra nó một lần rồi

Vòng trước, chỗ hay nhất trong bản cài đặt là **bỏ hẳn `node_id_test` do client
gửi**, để server tự chọn test bằng luật tất định. Làm đúng như thế với
`tep_test`:

```
server TỰ SUY tep_test từ tep_nguon theo quy ước:
      core/x.py  ->  tests/test_x.py
```

Đo trên kho: suy ra đúng **19/23 tệp** trong `core/`. Bốn tệp không có test cùng
tên:

```
lat_nguoc.py · paths.py · redact.py · the_cst.py
```

(`the_cst.py` được `tests/test_the_v1.py` phủ.)

Nên không suy được 100%, phải có đường lui. Đề nghị:

```
1. server suy tep_test theo quy uoc  ->  dung duoc thi DUNG, khong hoi client
2. khong suy duoc  ->  moi nhan tep_test tu client, VA no phai nam trong
                        danh sach trang cua phien
3. GIAO DIEN KHONG TU MO tep_test. Neu can duong 2 thi hien mot o cho nguoi
   dung CHON tep test — de "da mo" van con nghia la "nguoi dung da chon".
```

Như vậy 19/23 ca thường gặp **không nhận gì từ client cả**, và 4 ca còn lại vẫn
giữ được ý nghĩa của danh sách trắng.

Nếu Antigravity vẫn muốn giữ cách tự mở, thì xin **đừng gọi nó là hàng rào** —
ghi vào tài liệu là *"tiện lợi, không phải kiểm soát"*, đúng luật §7 mục 3.

---

## 2. Ba hạng mục còn lại — đúng cả

```
1. them "ma" vao candidates                  ĐÚNG, đây là việc nặng nhất
3. gop hai bo truy vet ve trace_runtime      ĐÚNG
4. tien trinh da chang + thoi gian kep       ĐÚNG
```

Đã kiểm những thứ kế hoạch trích:

```
tools/_worker_e1_exec.py                     CÓ THẬT (18.882 byte)
chot_test_can_trace -> (ten, so_khac, [TraceResult])   hợp lý để gộp
TraceResult hiện chưa có dong_da_chay        đúng, cần thêm như kế hoạch ghi
```

Ngưỡng của hạng mục 3 tôi xin giữ nguyên và nhấn lại: **gộp xong, 4 mốc E1 vẫn
phải ra `65→15 · 87→28 · 1→1 · 10→2` với đúng dòng `150 · 298 · 23`.** Đổi số
tức là hai bộ truy vết cho tập dòng khác nhau, và phải giải thích được vì sao
trước khi nhận con số mới.

---

## 3. Một chỗ nhỏ trong Verification Plan

> *"Toàn bộ 614 test cases đều PASS (hoặc 613 pass + 1 skipped)"*

Hiện tại là **613 passed, 1 skipped**. Kế hoạch thêm ít nhất 4 test mới
(2 ca whitelist `tep_test`, 1 ca `candidates[0]["ma"]`, và các ca trong
`test_trace_runtime.py`). Nên con số đích phải **lớn hơn 613**, không phải bằng.

Ghi số đích cụ thể trước khi chạy — nếu chạy xong vẫn ra 613 thì tức là test mới
chưa được thu thập, và đó là loại hỏng im lặng khó thấy nhất.

---

## 4. Tin sớm từ phép đo ngoài họ

Đang chạy, **16/64 đề**:

```
khong_tim_thay              14
ung_vien_khong_qua_suite     2
tim_thay                     0
xanh mà sai                  0
```

Hai ca `ung_vien_khong_qua_suite` đáng ghi nhận theo hướng tốt: E1 tìm được
phép lật làm **test đích** xanh, nhưng chạy cả bộ thì đỏ, nên nó **từ chối**.
Đó đúng là hành vi mong muốn — nếu nó nhận, ta đã có ngay một ca "xanh mà sai".

Chưa có kết luận, còn 48 đề.
