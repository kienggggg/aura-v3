# Người mới học code vướng gì — và LLM vướng đúng chỗ nào

*20/08/2026. Câu của Sếp: "nếu ví LLM là một người mới bắt đầu code thì gặp
những khó khăn gì". Dưới đây đối chiếu từng khó khăn với một phép đo có thật
trên máy này. Ô nào chưa đo thì ghi rõ là chưa đo.*

---

## 1. Bảng đối chiếu

| khó khăn của người mới | LLM có vướng không | bằng chứng |
|---|---|---|
| **không hiểu lệnh này làm gì** | **KHÔNG** | khay thẻ: chọn đúng hàm **25/28** khi hàm ấy có trong khay |
| **không biết dùng lệnh nào cho việc này** | **KHÔNG** | 25/28 — cả 3 lần trượt là do bộ lọc đánh rơi, không phải model chọn sai |
| **biết chỗ rồi nhưng không biết sửa ra sao** | **KHÔNG** | C·C2·C3: **0 trường hợp** chọn đúng thẻ mà sửa sai giá trị |
| **không viết nổi đúng khuôn** | **KHÔNG, sau khi ép** | ép JSON Schema: lỗi cú pháp **9 → 0**, bịa id **4 → 0** |
| **không biết chuỗi lệnh chạy ra sao** | *chưa đo riêng* | — |
| **không hiểu tại sao code viết như thế** | *chưa đo* | — |
| **không biết CHẠY THẾ NÀO mà ra kết quả đó** | **CÓ — và đây là bức tường** | định vị **1/9**, đứng yên qua cả ba lượt C·C2·C3 |

## 2. Bốn ô đầu: LLM KHÔNG phải người mới

Điều gây bất ngờ nhất trong cả ngày: bốn khó khăn kinh điển của người mới thì
model **không vướng**.

- Cho nó một mô tả việc và một khay hàm, nó chọn đúng **25/28**.
- Cho nó đúng chỗ cần sửa, nó sửa đúng — **không một lần nào** chọn đúng thẻ rồi
  đổi sai giá trị.
- Cho nó một lược đồ, nó xuất đúng khuôn.

Nên toàn bộ nỗ lực "dạy model biết lệnh", "cho khay thẻ đẹp hơn", "mô tả kỹ hơn"
là **chữa bệnh nó không có**. Ba lượt đo C · C2 · C3 đổi cách trình bày, cách ép
khuôn, độ sâu phân rã — con số định vị **đứng yên 1/9** cả ba lần.

## 3. Ô cuối: chỗ người mới và LLM vướng GIỐNG HỆT nhau

> *"không hiểu chạy thế nào mà ra được kết quả đó"*

Đây là chỗ duy nhất trong bảng model thật sự thua, và nó thua đúng kiểu người
mới thua:

```
test báo:  assert False is True
người mới hỏi:  ủa, False này ở đâu ra?
model làm:      chọn bừa một thẻ, đề nghị đúng giá trị cũ (61% số lượt)
```

Cả hai đều nhìn thấy **đầu vào** và **đầu ra sai**, mà không thấy **quãng giữa**.

Ba phép đo độc lập cùng chỉ vào đó:

```
máy định vị bằng phổ thực thi   3 mức, cả 3 TRƯỢT
   vì đột biến `<`->`<=` không tạo đường đi mới — cùng luồng, khác GIÁ TRỊ
model định vị bằng chọn thẻ     1/9, không nhúc nhích qua C·C2·C3
máy lật ngược từng chỗ (E1)     3/9 — và 3/3 với lỗi ĐƠN, 0/6 với lỗi kép
```

E1 là bằng chứng sạch nhất: khi máy **chạy thật 53 lần** để xem giá trị nào đổi
thì nó giải được **mọi** đề một lỗi. Không suy luận, không model — chỉ là **nhìn
được quãng giữa**.

## 4. Vì sao THẺ không lay chuyển được con số

Thẻ tả **cấu trúc**: cái này là `if`, cái kia là `gán`, ô này là `dieu_kien`.

Nhưng câu hỏi đang gãy không phải *"đây là loại lệnh gì"* — model đã trả lời
được câu ấy 25/28. Câu đang gãy là *"giá trị sai này đi qua đâu mà thành"*.

**Thẻ tả cấu trúc. Bức tường nằm ở thực thi. Hai thứ khác nhau.**

Đó là lý do bổ thẻ sâu 6,5 lần vẫn ra 0/9: vẽ chi tiết hơn một tấm bản đồ tĩnh
không giúp gì cho người đang hỏi *"tôi đi đường nào tới đây"*.

## 5. Hệ quả cho ý "app tự động phân tầng code"

Ý của Sếp đúng hướng, nhưng số liệu nói rõ **phân tầng theo trục nào**:

```
phân tầng CẤU TRÚC   hàm > khối > câu lệnh > biểu thức > lá
                     <- đã làm rồi (the_cst, bổ sâu). Không lay chuyển 0/9.

phân tầng THỰC THI   kết quả sai <- biểu thức nào sinh ra
                                 <- đầu vào của nó là gì
                                 <- những đầu vào ấy đến từ đâu
                     <- CHƯA LÀM. Đây mới là trục đang thiếu.
```

Một app hạ ngưỡng cửa cho người mới phải trả lời được đúng bốn câu, và cả bốn
đều là câu về **một lần chạy cụ thể**, không phải về mã tĩnh:

1. **Giá trị này ở đâu ra?** — bấm vào `False` trong thông báo lỗi, app chỉ
   thẳng biểu thức đã sinh ra nó.
2. **Nó đi qua những đâu?** — chuỗi từ hằng/đầu vào tới chỗ assert, chỉ gồm
   những bước THẬT SỰ chạy trong lần đó.
3. **Đổi chỗ này thì gì đổi theo?** — đúng thứ E1 làm bằng máy: lật thử, xem
   kết quả đổi ra sao. Người mới học được nhân quả, không phải học thuộc.
4. **Vì sao lại viết thế?** — chỗ duy nhất cần chữ của người. Kho này đã có sẵn
   thói quen ấy: chú thích ghi **vì sao, kèm số**.

Ba câu đầu **máy trả lời được hết**, không cần model. Câu thứ tư mới cần người.

## 6. Điều này cũng nói lại vai của model

```
việc máy làm giỏi     duyệt hết · chạy thử · so byte · truy ngược giá trị
việc model làm giỏi   đọc mô tả việc -> chọn đúng hàm (25/28)
                      biết chỗ -> sửa đúng (0 lần sai)
                      viết câu giải thích cho người đọc
```

Cả ngày hôm nay giao nhầm việc: bắt model **tìm** — thứ nó dở nhất — trong khi
máy có thể chạy chương trình 53 lần trong 40 giây.

Nói gọn: **đừng bắt model làm thám tử. Cho máy làm thám tử, model làm người kể
lại.**

## 7. Chưa đo — ghi ra để không lẫn với kết luận

- *"không hiểu chuỗi lệnh hoạt động"* — chưa tách riêng khỏi ô định vị.
- *"không hiểu tại sao code viết như thế"* — chưa đo lần nào.
- **Truy ngược giá trị (backward value slice)** — ba trong năm AI đều đề nghị,
  và mục 5 nói nó là trục đúng. **Vẫn chưa đo.** Đây là phép đo tiếp theo đáng
  làm nhất, và nó không cần model.
