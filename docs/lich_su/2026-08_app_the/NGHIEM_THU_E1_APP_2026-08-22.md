# Nghiệm thu E1 vào app — 22/08/2026

*Claude chạy lại, tự thử hàng rào, đối chiếu sổ với mã. Phần lõi ĐÚNG. Nhưng
một hạng mục trong kế hoạch KHÔNG được cài mà báo cáo không nói.*

---

## 1. Đã kiểm, đúng cả

```
toàn kho                        611 passed, 1 skipped
thư mục bằng chứng              có thật: artifacts · commands.jsonl · manifest
                                · metrics.json · raw/
sáu tệp mới                     core/lat_nguoc.py 23 KB · do_cua_cung_e1_app.py 35 KB
                                · test_e1_app.py · test_cua_a_guard.py
                                · test_e1_ui.js · _cdp_browser_test.js
```

### Bốn mốc dùng ĐÚNG đề của E1

Đối chiếu chỗ gieo chốt cứng trong `do_cua_cung_e1_app.py` với chỗ E1 gieo
(dựng lại bằng `random.Random(19082026)`):

```
may_tinh.py      E1 gieo chỗ 55   họ dùng [55]   KHỚP
web_search.py    E1 gieo chỗ 78   họ dùng [78]   KHỚP
dong_ho.py       E1 gieo chỗ  0   họ dùng  [0]   KHỚP
loai_cau_hoi.py  E1 gieo chỗ  3   họ dùng  [3]   KHỚP
```

### NGƯỠNG #2 CỦA TÔI ĐẠT — lọc không đánh rơi đáp án

Đây là ngưỡng tôi nói là quan trọng nhất. Đối chiếu dòng họ tìm ra với dòng đột
biến thật:

```
                báo cáo   dòng thật
may_tinh.py       150        150      KHỚP   if nam is None and moc <= hom_nay:
web_search.py     298        298      KHỚP   return SearchResult(query, True, ...)
dong_ho.py         23         23      KHỚP   hien_tai = now and datetime.now()...
```

Lọc cắt `65→15`, `87→28`, `1→1`, `10→2` mà **chỗ đúng vẫn còn** trong cả ba đề
giải được.

### Hàng rào `/api/dinh_vi_loi` — tôi tự thử 7 đường

```
không token · token sai                     403
../ trong tep_nguon                         403
đường dẫn tuyệt đối (C:/Windows/win.ini)    403
ra ngoài kho (D:/AURA_OS_v2/...)            403
thư mục data/ ngoài whitelist               403
tep_test ra ngoài                           403
```

Và gọi hợp lệ khi chưa bật cờ:

```json
{"trang_thai": "bi_khoa", "error": "Chạy mã/test đang tắt mặc định"}
```

**Endpoint E1 fail-closed đúng.**

---

## 2. HẠNG MỤC KHÔNG ĐƯỢC CÀI — báo cáo không nói

Kế hoạch để ở đầu, mục **User Review Required số 1**, chọn **Phương án B**:

> *Tầng 2 (`/api/trace`, `/api/tim_loi_e1`): **BẬT MẶC ĐỊNH**... Có thể tắt
> bằng `AURA_THE_ALLOW_TRACE=0`. Băng-rôn & `/api/status`: khai báo trung thực,
> tách bạch rõ ràng cả 2 quyền.*

Kiểm trên đĩa:

```
ALLOW_TRACE_EXECUTION trong mã           KHÔNG CÓ
/api/status có trace_execution_enabled   KHÔNG — chỉ có code_execution_enabled
băng-rôn khởi động                       vẫn MỘT dòng:
    "* Chay ma : TAT MAC DINH; mo/sua/kiem tra/luu van hoat dong"
/api/trace có cửa thực thi               VẪN CHƯA CÓ
```

Thực tế đã cài là **Phương án C cho E1** (endpoint mới chịu chung
`ALLOW_CODE_EXECUTION`) **cộng với KHÔNG LÀM GÌ cho `/api/trace`**.

Nên **lỗi tôi báo hôm qua vẫn còn nguyên**: `/api/trace` chạy mã người dùng
trong khi app khai `code_execution_enabled: False`. Endpoint mới thì an toàn;
endpoint cũ thì không.

Đây không phải cài sai — cài **an toàn hơn** kế hoạch. Vấn đề là **báo cáo ghi
PASS 7/7 mà không nói mình đã đổi phương án**, và cái hố cũ vẫn mở.

Xin hai việc, đều một dòng:

```
1. /api/trace chịu cùng cửa như /api/dinh_vi_loi
2. băng-rôn + /api/status nói đúng những gì đang bật
```

---

## 3. Bảng thời gian trong báo cáo KHÁC sổ lệnh của chính nó

```
                báo cáo (metrics)   commands.jsonl   chênh
may_tinh.py          9,9s               57,5s        +47,6
web_search.py       31,3s               78,8s        +47,5   <- vượt trần 60s
dong_ho.py          17,6s               65,4s        +47,8   <- vượt trần 60s
loai_cau_hoi.py     40,4s               43,2s         +2,8
```

Không phải khai man: đầu bảng ghi rõ *"Thời gian Lọc + Lật"*, tức đo **phần
lõi**. Sổ lệnh đo **cả lượt gọi HTTP** — gồm dựng bản sao và khởi động máy chủ.

Nhưng con số người dùng **cảm thấy** khi bấm nút là con số thứ hai: **57–79
giây**. Trần 60 giây tôi đặt là cho phần lõi, nên chưa vi phạm. Xin ghi **cả
hai** vào báo cáo lần sau, và nếu nút bấm mất 79 giây thì giao diện phải có
thanh tiến trình, không để người dùng ngồi nhìn màn hình đứng im.

---

## 4. Không đo được

`tools/do_cua_cung_e1_app.py` chạy quá **10 phút** trên máy tôi mà chưa xong,
tôi phải cắt. Sổ lệnh của họ ghi tổng **327 giây (5,5 phút)**.

Chênh này tôi **chưa giải thích được** — có thể phần Chrome CDP chờ trình duyệt
mà máy tôi không có sẵn. Ghi là **KHÔNG ĐO ĐƯỢC**, không ghi là hỏng.

---

## 5. Năm lần tôi dò sai trong đợt này

Ghi ra vì nó là số liệu về chính tôi:

```
1. tưởng web_search báo sai dòng   -> tôi lấy sai ĐỀ (dùng mục [0] thay vì
                                      rng.sample có seed). Thật ra KHỚP.
2. tưởng họ dùng sai chỗ gieo [3]  -> cũng lỗi trên. Cả bốn đều KHỚP.
3. tưởng lệch parity Python/JS     -> tôi so ĐỎ với TỔNG đỏ+vàng.
4. tưởng mất 29/198 chú kiểu       -> chấm bằng dò chuỗi; AST cho 0.
5. tưởng thiếu kieu_tra_ve trong API -> máy chủ đang chạy mã CŨ.
```

Ba trong năm là dò chuỗi hoặc lấy sai mẫu — đúng thứ `CLAUDE.md` §4 cấm. Bài
học chung: **trước khi báo người khác sai, chạy lại probe của chính mình trên
một ca đã biết đáp án.**
