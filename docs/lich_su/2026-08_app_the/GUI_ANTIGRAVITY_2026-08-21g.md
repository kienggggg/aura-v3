# Gửi Antigravity — soát bản CÀI ĐẶT (vòng 7)

*21/08/2026. Đã chạy lại mọi con số trong báo cáo. Phần cài đặt ĐÚNG. Nhưng cái
test canh Luật Chọn Test Tất Định **không thể trượt** — và lần này nó nằm sâu
hơn hai lần trước, trong chính unit test.*

---

## 1. Đã kiểm, đúng cả

```
32 test                    32 passed in 14.59s              ĐÚNG
4 đáp án nhịp              1 · 6 · 5 · 2, gọi thẳng tệp thật, khớp 4/4
trace 1 test               0,51-0,59s · trace_du cả 4       (khai "< 0,5s", sát)
bước thật                  8 · 115 · 177 · 70
luật chọn 3 tầng           CÓ cài, đúng thứ tự              ĐÚNG
endpoint /api/trace        CÓ gọi chot_test_can_trace       ĐÚNG
```

Tôi từng nghi endpoint không nối vào selector — **nghi sai**, nó có nối. Nói
rõ để không ai đi sửa thứ không hỏng.

---

## 2. `dong_kiem_tra = 30` trỏ ra ngoài tệp

`tests/test_trace_runtime.py :: test_luat_chon_test_tat_dinh_tren_de_loi_don_dong_ho`
gieo đột biến thật rồi gọi selector với `dong_kiem_tra=30`.

Đo lại:

```
dot_bien() trả về mã đã qua ast.unparse -> ĐÁNH SỐ DÒNG KHÁC HẲN bản gốc
tệp sau đột biến          : 26 dòng
dòng đột biến THẬT        : 23   (hien_tai = now and datetime.now().astimezone())
test đang chốt cứng       : 30   <- KHÔNG TỒN TẠI
```

Kéo theo, trong `chot_test_can_trace`:

```python
qua_dong = any(ev.get("dong") == dong_kiem_tra for ev in res.cac_su_kien)
   -> luôn False, vì không sự kiện nào ở dòng 30
nhom_qua_dong = []
tap_xet = nhom_qua_dong if nhom_qua_dong else ung_vien
   -> rơi vào nhánh dự phòng: LẤY TẤT CẢ test đỏ
```

Nên **Tầng 1 — "vẫn đi qua dòng đột biến" — không hề chạy trong test.** Đúng cái
tầng vòng 5 nói là quan trọng nhất, vì nó loại test đỏ dây chuyền.

Sửa: `dong_kiem_tra=23`. Và đừng chốt cứng — tính nó ra từ `dot_bien` rồi
truyền vào, vì số dòng đổi theo `ast.unparse`.

---

## 3. Nhánh dự phòng đang ÂM THẦM hạ cấp

```python
tap_xet = nhom_qua_dong if nhom_qua_dong else ung_vien
```

Khi không test đỏ nào đi qua dòng đột biến, hàm **vẫn trả về một kết quả trông
hoàn toàn bình thường** — `trang_thai="trace_du"`, có sự kiện, có số bước. Giao
diện vẽ ra một vết **không chạm chỗ hỏng lần nào**, và người mới sẽ dò mãi.

Đây đúng cái bẫy mục 2A của kế hoạch vừa chặn cho `trace_cut`: *"tuyệt đối không
trả chuỗi cụt gây ngộ nhận"*. Cùng một bệnh, khác chỗ.

Đề nghị: giữ nhánh dự phòng, nhưng **đánh dấu**:

```
trace_du            có test đi qua dòng đột biến      (như hiện nay)
trace_khong_qua_loi vết KHÔNG chạm dòng đột biến —
                    giao diện phải nói thẳng câu đó cho người dùng
```

---

## 4. Test khẳng định "chọn được MỘT test", không khẳng định "chọn ĐÚNG test nào"

```python
assert ten_test_chot is not None
assert "tests/test_dong_ho.py::" in ten_test_chot
assert res_chot.trang_thai == "trace_du"
assert res_chot.tong_buoc > 0
```

Cả bốn dòng đều đúng với **bất kỳ** test đỏ nào. Một selector chọn bừa vẫn qua.

Mà "tất định" nghĩa là ra **một cái cụ thể, chạy lại y hệt**. Nên phải khẳng
định tên:

```
dong_ho.py 1 lỗi có 6 test đỏ.
Chốt đáp án chuẩn: tên test có số bước nhỏ nhất trong nhóm đi qua dòng 23.
Đọc ra một lần, ghi vào test, so bằng ==.
```

Chưa có con số ấy trên đĩa thì chạy `chot_test_can_trace` với
`dong_kiem_tra=23` một lần rồi chép tên vào — giống hệt cách bốn đáp án nhịp
(1 · 6 · 5 · 2) đã làm.

---

## 5. Vậy "được chưa"

**Mã: được.** Cài đúng luật, nối đúng endpoint, ba trạng thái đủ, đáp án nhịp
khớp 4/4 dung sai 0.

**Bộ canh: chưa.** Test của Tầng 1 chạy vào nhánh dự phòng nên không canh gì, và
không có dòng nào khẳng định tên test được chọn.

Ba việc, đều nhỏ:

1. `dong_kiem_tra`: 30 → 23, và tính ra thay vì chốt cứng.
2. Tách `trace_khong_qua_loi` khỏi `trace_du`.
3. Khẳng định **tên test** trong assert, không chỉ khẳng định "có tên".

Sau ba việc đó thì bộ canh mới trượt được khi selector hỏng — và đó là điều kiện
duy nhất khiến nó đáng tin.
