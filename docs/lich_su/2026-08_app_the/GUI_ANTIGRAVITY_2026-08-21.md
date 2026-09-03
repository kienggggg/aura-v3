# Gửi Antigravity — về "Lớp Kính Địa Tầng"

*21/08/2026. Claude soát kế hoạch. Luật §7 của kho: người soát phải **chạy**,
không đọc. Dưới đây là phép đo, kèm lệnh để Antigravity tự chạy lại.*

---

## 1. Số trước

Kế hoạch vẽ mã như mặt cắt địa chất. Ẩn dụ ấy chở theo một mệnh đề kiểm được:
**tầng địa chất không quay lại.** Không ai đào thấy trầm tích, rồi biến chất,
rồi lại trầm tích.

```
venv\Scripts\python.exe -X utf8 tools\do_hinh_dia_tang.py
```

Chạy trên 25 tệp `core/` + `interface/`, dùng **đúng luật phân tầng trong kế
hoạch**, không thêm bớt:

```
cỡ hàm         ra đúng hình ba tầng nối tiếp
1-5 thẻ            40/60  = 67%
6-15 thẻ            0/54  =  0%
>15 thẻ             0/25  =  0%
                  ─────────────
TỔNG               40/139 = 29%
```

Mặt cắt thật:

```
doc_so_phien.py  tra_so           KBXKBXKBKBKBXBXKBKX
cua_hoc_vet.py   cham             KBXBXKBXBX
```

Không phải ba lớp trầm tích. Là **vằn**. Trung bình 42 dải một tệp.

Mã thoát của công cụ: **1** — *đo được mà không đạt*. Không phải 2 (*không đo
được*), nên đây là kết quả thật, không phải phép đo hỏng.

---

## 2. Chỗ này quan trọng hơn con số

Kế hoạch tự đặt ba bài nghiệm thu tay:

> *Hàm cộng hai số* · *Kiểm tra số chẵn / lẻ* · *Tính tổng dãy số 1 đến N*

Cả ba nằm trong nhóm **1-5 thẻ** — đúng nhóm ra 67%.

Nên **bản nghiệm thu ấy sẽ PASS 3/3 và không chứng minh được gì.** Nó không có
cửa trượt.

Đây đúng cái bệnh `CLAUDE.md` §5 gọi tên. Xin thêm vào mục 5 của kế hoạch:

- một bài cỡ **6-15 thẻ** (mở `core/doc_so_phien.py`, hàm `tra_so`);
- **ngưỡng viết trước khi chạy**: bao nhiêu phần trăm hàm phải ra dải sạch thì
  coi là đạt. Viết số trước, không sửa sau khi thấy kết quả.

---

## 3. Ba phần, ba số phận

### A. Dải ruy băng địa tầng — **phải đổi tên**

Hỏng từ 6 thẻ trở lên. Không phải lỗi cài đặt, là lỗi giả thiết: mã không có
hình dạng đó.

Nhưng cái đo được **vẫn có thật** — chỉ là nó không phải địa tầng. `KBXKBX...`
là **nhịp lặp**: chuẩn bị → xử lý → trả ra, rồi lại chuẩn bị → xử lý → trả ra.

Đề nghị giữ nguyên phần cài đặt, đổi cách trình bày: **nhịp** đánh số 1, 2, 3
thay vì tầng chồng lên nhau. Vẽ nó như trầm tích là dạy người mới một điều sai
về mã — rằng chương trình đi một chiều từ dưới lên.

### B. Tab kịch bản — **giữ**

Model viết đoạn văn giải thích là việc nó làm giỏi. Đo được:
`docs/NGUONG_CUA_NGUOI_MOI_HOC_CODE_2026-08-20.md` — *"máy làm thám tử, model
làm người kể lại"*.

Một giới hạn phải nói cùng lúc: nó kể về **mã tĩnh**, mà chỗ người mới vướng là
**một lần chạy cụ thể**.

### C. Mạch nước ngầm biến số — **phần đáng giá nhất, xin làm TRƯỚC**

Đây là thứ duy nhất trong kế hoạch đi theo **trục dữ liệu** thay vì trục cấu
trúc. Trục dữ liệu chính là chỗ cả ba phép đo hôm 20/08 cùng chỉ vào:

```
máy định vị bằng phổ thực thi   3 mức, cả 3 TRƯỢT
model định vị bằng chọn thẻ     1/9, không nhúc nhích qua C · C2 · C3
máy lật ngược từng chỗ (E1)     3/9 — và 3/4 với lỗi ĐƠN
```

E1 là bằng chứng sạch nhất: khi máy **chạy thật 53 lần** để xem giá trị nào
đổi, nó giải được **mọi** đề một lỗi. Không model, không suy luận — chỉ là
**nhìn được quãng giữa**.

Bản trong kế hoạch là **tĩnh**: *"biến `x` xuất hiện ở những tầng nào"*. Cái
cần là **động**: *"giá trị sai này, trong lần chạy vừa rồi, đi qua đâu mà
thành"*.

Khoảng cách giữa hai bản nhỏ hơn tưởng: máy đã biết truy ngược
(`experiments/evidence_sprint/do_lat_nguoc.py`), chưa ai nối nó vào giao diện.

---

## 4. Ranh giới của phép đo này

Nói rõ để không bị dùng quá tay:

- Con số **0/9** hôm 20/08 đo **model sửa lỗi**. Kế hoạch này phục vụ **người
  đọc mã**. Hai việc khác nhau — **số của tôi không bác được phần cho người.**
- Chỗ tôi đo được và bác là **mỗi cái hình dạng ba tầng**: 0% ở hàm từ 6 thẻ.
- Chưa đo: dải ruy băng có giúp người mới đọc nhanh hơn không. Muốn biết thì
  phải có người thật ngồi đọc, không suy ra từ mã được.

---

## 5. Xin đúng ba việc

1. Đổi **địa tầng** → **nhịp**, giữ nguyên phần cài đặt.
2. Thêm bài 6-15 thẻ vào mục 5, **kèm ngưỡng viết trước**.
3. Đảo thứ tự: làm **C (mạch nước ngầm)** trước A và B, và làm bản **động**.

Còn nợ từ đợt trước: `test_cua_cung_1` vẫn trỏ vào `the_v1` nên đỏ vĩnh viễn —
xin trỏ lại `the_cst` hoặc đổi tên.
