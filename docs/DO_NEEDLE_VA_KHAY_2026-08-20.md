# Đo Needle 2 và sửa bộ lọc khay — 20/08/2026

*Sổ chạy nằm ở `data/evidence_sprint/needle_vs_qwen.json`, nhưng `data/` bị
`.gitignore` bỏ qua nên số phải chép vào đây mới sống được. Chạy lại:*

```
venv\Scripts\python.exe        -X utf8 experiments\evidence_sprint\do_needle_khay.py --qwen   --giu 8
.venv-needle\Scripts\python.exe -X utf8 experiments\evidence_sprint\do_needle_khay.py --needle --giu 8
```

---

## 1. Việc được đo

**Cho mô tả một việc, chọn đúng MỘT hàm trong khay.** 28 đề, mỗi đề nhắm đúng
một hàm có thật trong `core/`, mô tả cố ý không chứa tên hàm.

**Đây không phải việc mà con số 20/28 cũ đo.** Bộ chấm cũ (`do_khay_loc.py`)
bắt model **viết mã** rồi kiểm mã ấy có gọi đúng hàm kho không. Needle 45M không
viết mã — nó gọi tool. Đem 20/28 ra so với "chọn tool" là so hai việc khác nhau.
Nên ở đây đo **cả hai model trên cùng một việc hẹp hơn**, và số dưới đây không
so được với 20/28.

## 2. Ba lần đo

```
                     trần    chọn đúng   đúng/khi CÓ mặt   chết   giây
qwen3.5:4b  giữ 8    23/28   23/28       23/23 = 100%      0       271
qwen3.5:4b  giữ 15   25/28   22/28       22/25 =  88%      1      1008
Needle 2    giữ 8    23/28    7/28        7/23 =  30%      7       177
```

**Trần** = hàm đúng có nằm trong khay không. Không model nào vượt được trần —
đó là việc của bộ lọc, không phải của model.

## 3. Model chưa bao giờ là chỗ nghẽn

`qwen3.5:4b` chọn đúng **23/23 khi hàm đúng có mặt trong khay** — không sai lần
nào. Cả 5 đề nó trượt đều là **bộ lọc đánh rơi đáp án trước khi model kịp nhìn**.

Đó là kết quả lật ngược giả thuyết ban đầu. Đi tìm model tốt hơn là đi sai
hướng; chỗ phải sửa là `loc_khay`.

## 4. Đã sửa gì trong `core/khay_the.py`

**(a) Chấm thêm TOÀN VĂN tài liệu, trọng số 0,5** (`The.tu_tai_lieu()`).

`mo_ta` chỉ là **dòng đầu** docstring, mà dòng đầu hay tả *giá trị trả về* chứ
không tả việc — `tinh_giup` mở đầu bằng *"Một dòng 'đã tính sẵn' để nhét vào lời
dặn"*. Đo cả hai mức trọng số:

```
0,5  ->  trần khay 15 từ 24/28 lên 25/28
1,0  ->  TỤT xuống 24/28   (thân tài liệu dài, trọng số mạnh kéo cả thẻ nhiễu lên)
```

Cứu đúng `la_chuyen_rieng_cua_sep`: việc *"chặn không cho đẩy đời tư của chủ máy
ra ngoài"* chung `day`/`doi`/`may` với **thân** tài liệu mà không chung chữ nào
với dòng đầu.

**(b) Bỏ `if d > 0`** — thẻ điểm 0 chỉ bị xếp xuống cuối, không bị vứt hẳn.

Bản cũ vứt hẳn nên `giu` mất nghĩa: xin cả 96 thẻ vẫn chỉ nhận về 25/28 đáp án
đúng, và ba đề **không model nào thắng được**.

```
TRẦN KHAY        trước    sau
giữ 8            23/28    23/28
giữ 15           24/28    25/28
giữ 30           25/28    26/28
giữ 96           25/28    28/28   <- giờ bằng đúng cỡ khay
```

## 5. Khay to hơn thì TỆ hơn

Trần khay 15 cao hơn khay 8 hai đề, nhưng qwen tụt từ 23/23 xuống 22/25, **tổng
tụt 23 → 22**, và chậm gấp 3,7 lần.

Đúng **một** đề lật từ đúng sang sai (`gan_canh_bao` → `don_vi_dang_ngo`), và
**không đề nào lật ngược lại**. Bảy thẻ thêm vào chỉ gây nhiễu.

Quyết định *"giữ khay 8"* từ lượt trước giờ có số đỡ, không còn là cảm tính.

## 6. Needle 2 — đóng hồ sơ, ba lý do độc lập

`cactus-needle` 2.0.7, cài vào venv riêng `.venv-needle`. Ngưỡng đặt **trước**
khi đo: `>=10/28` đi tiếp, `<5/28` đóng.

1. **7/28 — dưới ngưỡng.** Nằm giữa hai mốc thì vẫn là dưới mốc đi tiếp.
2. **25% số lượt CHẾT.** 7/28 ném `UnicodeDecodeError` trên tiếng Việt. Một công
   cụ chết ở 1 trong 4 đầu vào tiếng Việt thì không dùng được trong kho này,
   **độc lập với chuyện nó chọn đúng bao nhiêu**.
3. **Điểm tin cậy mất sạch tín hiệu giữa hai lần chạy:**

   ```
   lần 1   đúng 0,281 / sai 0,136   (có tín hiệu)
   lần 2   đúng 0,091 / sai 0,094   (không còn gì)
   ```

   *"Confidence-gated"* là chỗ bán duy nhất đáng giá của nó với kho này, và nó
   không đứng vững.

**Sửa hai chỗ trong lời quảng cáo:** venv nặng **589 MB**, không phải 14 MB —
14 MB là *trọng số model*, thời gian chạy kéo theo cả flax/jax. Còn **đỉnh RAM
108 MB thì họ khai đúng**.

**Ghi nhận công bằng:** sửa `loc_khay` giúp Needle nhiều hơn giúp qwen
(2 → 7 so với 22 → 23). Model yếu hưởng lợi từ khay tốt nhiều hơn model mạnh —
hợp lý, vì qwen vốn đã không sai khi đáp án có mặt.

## 7. Chỗ CỐ Ý không sửa

Hai đề còn lại (`tinh_giup`, `search`) cần bắc cầu từ vựng. `search` có docstring
đúng **74 ký tự — "Tra mạng."** — không chung chữ nào với *"dịch vụ tìm kiếm"*.

**Không viết bảng từ đồng nghĩa cho 28 đề này.** Đó là học vẹt đúng nghĩa, chính
thứ `core/cua_hoc_vet.py` dựng ra để chặn. Chỗ ấy phải sửa **tài liệu của hàm**,
không phải sửa bộ lọc.

Vấn đề rộng hơn, đo được: **52% hàm trong kho không có docstring nào**; 90% có
chú kiểu. Muốn khay tốt hơn nữa thì viết tài liệu, không phải chỉnh trọng số.

## 8. Một nguồn nhiễu phải nói ra

Khay **sinh từ chính kho**, mà Antigravity đang sửa liên tục (`the_api.py`,
`the_app.py`, `app.js`, `pytest.ini`, `requirements.txt`). Tài liệu đổi thì tần
suất từ đổi, thứ hạng đổi theo.

Trần khay lúc đo Needle lần đầu là **22/28**, giờ **23/28** — chênh một đề là do
kho đổi, **không phải do bản sửa**. Muốn so hai bộ lọc cho chặt thì phải ghim
khay vào một tệp trước, chưa làm.
