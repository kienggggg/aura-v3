# Kế hoạch — Căn cưỡng bức thật (nợ "WhisperX"), 09/09/2026

**Trạng thái: SẾP DUYỆT 09/09 — "dùng bản apache-2.0, đo thử xem có hơn
không". ĐO XONG 10/09: KHÔNG ĐẠT, KHÔNG GIAO — xem mục 6.**

*(Câu này lúc gửi đi là "CHỜ SẾP DUYỆT. Chưa cài gì, chưa viết một dòng
mã sản phẩm nào." Giữ nguyên văn vì nó là bằng chứng kế hoạch ra đời
trước phép đo — luật §7.)*

`CLAUDE.md` §7 luật 1: *"Dựng mới một hệ thống thì gửi kế hoạch trước, không
viết mã trước."* Luật 2: *"Người duyệt phải CHẠY THỬ mọi con số."* Mọi con số
dưới đây **đã chạy trên chính máy này hôm nay**.

---

## 1. Nợ này là gì

`SO_BENH_AN.md` dòng 1295 ghi:

> Đây là **nhận dạng rồi ghép mốc**, chưa phải **căn cưỡng bức** lời đã biết.
> 17/245 từ không khớp được nội suy giữa hai từ kề — chúng là **suy ra**, không
> phải **đo được**. WhisperX làm đúng việc thứ hai và sẽ phủ 100%, nhưng kéo
> theo `torch` ≈ 2–2,5 GB và **chưa chạy trên máy này**.

Hai con số trong câu ấy đều **sai so với đo lại**.

## 2. Phía lợi ích — TỆ HƠN sổ ghi

Chạy `can_tung_tu` thật hôm nay, cùng đường sản phẩm:

| | sổ ghi 07/09 | **đo 09/09** |
|---|---|---|
| từ có neo đo được | 228/245 | **87/114** |
| từ là **nội suy** (đoán) | 17/245 = 6,9% | **27/114 = 23,7%** |
| p90 lệch vệt sáng | — | **0,090s** |
| ngưỡng (nửa từ) | — | **0,090s** |
| WER | — | 23,7% |

**Gần một phần tư số từ đang là đoán, và sai số nằm ĐÚNG TRÊN VẠCH.** `p90 ==
ngưỡng` là lý do `test_ASS_va_MOC_TU_khop_nhau_tren_LUOT_THAT` mong manh: nó
ngồi ngay ranh giới, nên nội dung đổi một chút là đổi phán quyết.

Đây là lợi ích thật, không phải "cho đẹp".

## 3. Phía chi phí — RẺ HƠN sổ ghi, nhưng có ba chướng ngại

### 3.1 `whisperx` KHÔNG CÀI ĐƯỢC trên máy này

```
whisperx 3.8.6    requires_python: <3.14,>=3.10
venv v3           Python 3.14.x
venv STT (F:)     Python 3.14.5
```

Cả hai môi trường đều 3.14. Muốn dùng gói `whisperx` thì phải dựng thêm **một
bản Python thứ ba** — một biến nữa vào bài toán.

### 3.2 Và nó kéo theo thứ AURA không dùng

`whisperx` phụ thuộc `pyannote-audio>=4.0.0` — **phân tách người nói**, việc
AURA không làm. Riêng gói ấy kéo thêm 21 gói: `lightning`, `matplotlib`, ba gói
`opentelemetry-*`, `pytorch-metric-learning`, `torch-audiomentations`…

**Nhưng căn cưỡng bức của WhisperX chỉ là `wav2vec2` + CTC.** Không cần gói
`whisperx`. Thứ thật sự cần:

| | cỡ đo được |
|---|---|
| `torch` bản **CPU**, wheel `cp314-win_amd64` | **124,1 MB** |
| `transformers` + `torchaudio` | ~60 MB |
| model căn tiếng Việt | 385 MB – 1,26 GB (mục 3.3) |

> **Con số "torch ≈ 2–2,5 GB" trong sổ là bản CUDA.** Máy này **không có GPU
> rời** (`CLAUDE.md` mục 1), nên bản ấy không bao giờ cần tới. Đúng ca *"đo cái
> app KHÔNG chạy thì mọi con số đều là số của người khác"* — con số ấy đọc từ
> tài liệu, không đo trên máy này.

### 3.3 Giấy phép — CHỖ SẾP PHẢI QUYẾT

Model mà WhisperX chọn sẵn cho tiếng Việt là **phi thương mại**:

| model | cỡ (trọng số) | giấy phép | lượt tải |
|---|---|---|---|
| `nguyenvulebinh/wav2vec2-base-vi-vlsp2020` *(WhisperX chọn sẵn)* | **385,0 MB** | **`cc-by-nc-4.0`** | — |
| `dragonSwing/wav2vec2-base-vietnamese` | 755,7 MB | **`apache-2.0`** | 2.188 |
| `not-tanh/wav2vec2-large-xlsr-53-vietnamese` | 1.262,4 MB | **`apache-2.0`** | 454 |
| `Nhut/wav2vec2-large-xlsr-vietnamese` | 1.262,5 MB | **`apache-2.0`** | 569 |

Bản `cc-by-nc-4.0` nhỏ nhất và được dùng nhiều nhất, nhưng **cấm dùng thương
mại**. Ba bản `apache-2.0` thoáng hơn, nặng gấp 2–3 lần, và **chưa ai đo chất
lượng của chúng trên máy này**.

> Kho công nghệ đã có tiền lệ ghi giấy phép làm điều kiện dùng lại: `firecrawl`
> bị đánh dấu `AGPL-3.0`. Đây là cùng loại quyết định.

### 3.4 RAM — chướng ngại thật sự

```
RAM tổng 12,61 GB · còn trống 1,03 GB · đang dùng 91%
```

`wav2vec2-base` ở fp32 chiếm ~1,4 GB chỉ riêng trọng số, chưa kể runtime của
`torch`. **Với 1,03 GB trống thì nó sẽ tráo đĩa.** Bản `large` (1,26 GB trọng
số) còn nặng hơn.

Đĩa thì đủ: `F:` còn 65,2 GB, venv STT hiện tại chỉ 283 MB.

---

## 4. Thiết kế đề xuất

**Không cài `whisperx`. Viết thẳng phần căn cưỡng bức bằng `torch` +
`transformers`, trong venv riêng — đúng khuôn `faster-whisper` đang dùng.**

```
F:\aura-stt\venv          (đã có, Python 3.14.5, 283 MB)
   + torch (CPU) + transformers + torchaudio        ~600 MB
   + model wav2vec2 tiếng Việt                      385 MB – 1,26 GB
core/can_chu.py           gọi qua TIẾN TRÌNH RIÊNG, y như bây giờ
requirements.txt          KHÔNG đổi — vẫn đúng 2 gói ngoài
```

`CLAUDE.md` mục 1 đã chốt khuôn này cho `faster-whisper`: *"273 MB và 10+ gói,
cộng 605 MB model. Tức 2 → 12, cho một tính năng"* — nên nó ở venv riêng, gọi
qua tiến trình con. Căn cưỡng bức đi đúng đường ấy.

**Ba trạng thái giữ nguyên:** không có bộ căn cưỡng bức thì tụt về bộ hiện tại
(nhận dạng + nội suy) và **NÓI RA**, không tụt im lặng — đúng bài đã học ở
`core/tra_cuu.py` hôm qua.

---

## 5. Cách chấm — đăng ký TRƯỚC

| đơn | ngưỡng |
|---|---|
| từ có neo **đo được** | **114/114 = 100%** (nay 87/114) |
| p90 lệch vệt sáng | **< 0,090s** và phải **thấp hơn hẳn** bản hiện tại 0,090s |
| ca đối chứng | cùng đoạn âm thanh, cùng lời — chỉ đổi bộ căn |
| không có venv/model | **KHÔNG ĐO ĐƯỢC**, tụt về bộ cũ và **nói ra** |
| `requirements.txt` | **vẫn đúng 2 dòng** |

**Bước 1 của việc làm là MỘT PHÉP ĐO, không phải mã sản phẩm:** cài vào venv
riêng, chạy căn cưỡng bức trên **đúng tệp WAV** mà phép đo mục 2 vừa dùng, rồi
so hai cột. Nếu p90 **không** thấp hơn 0,090s thì dừng lại và ghi
"KHÔNG ĐÁNG" — 600 MB + 385 MB không đổi lấy một con số không nhúc nhích.

> Chưa ai chạy `wav2vec2` trên máy này. Mọi câu về việc nó sẽ tốt hơn bao nhiêu
> **đều là đọc thấy**, kể cả câu của tôi ở mục 2.

---

## 6. Ba câu cần Sếp quyết

1. **Giấy phép.** Dùng bản `cc-by-nc-4.0` 385 MB (nhỏ, phổ biến, **cấm thương
   mại**) hay bản `apache-2.0` 756 MB / 1,26 GB (thoáng, nặng hơn, chưa ai đo)?
2. **RAM còn 1,03 GB.** Có chấp nhận việc lượt căn chữ sẽ tráo đĩa, hoặc phải
   đóng bớt thứ khác trước khi dựng video không?
3. **Có đáng không?** 27/114 từ đang là đoán và p90 nằm đúng trên vạch — nhưng
   video vẫn dựng xong, phụ đề vẫn quét. Đây là **làm cho đúng**, không phải
   **sửa cho chạy**.

---

## 6. KẾT QUẢ — ĐO XONG 10/09/2026: **KHÔNG ĐẠT, KHÔNG GIAO**

Sếp duyệt 09/09: *"dùng bản apache-2.0, đo thử xem có hơn không"*.
Đã cài, đã đo, và câu trả lời là **chưa hơn**.

### 6.1 Cài gì

| | |
|---|---|
| venv | `F:\aura-align` **riêng**, KHÔNG chen vào `F:\aura-stt` đang chạy được |
| `torch` | **2.14.0+cpu**, wheel 124,1 MB — đúng con số kế hoạch, không phải 2–2,5 GB |
| model | `dragonSwing/wav2vec2-base-vietnamese`, **apache-2.0**, 755,7 MB |
| tổng trên đĩa | ~2,2 GB |

### 6.2 Phía được — thật, và đáng kể

| | bộ hiện tại | căn cưỡng bức |
|---|---|---|
| từ có neo **đo được** | 87/114 = 76,3% | **114/114 = 100%** |
| thời gian | 68,6s | **13,6s** — nhanh 5× |
| mốc không tăng dần / vượt biên | — | **0 / 0** |

### 6.3 Phía mất — và nó thắng

Không có nhãn tay, nên phải dựng **trọng tài độc lập với cả hai bộ**: ngưỡng
"có tiếng" suy ra từ chính tệp âm thanh (giữa log của phân vị 10 và 90), rồi
chấm recall/precision trên khung 10 ms.

| | recall | precision | **F1** |
|---|---|---|---|
| **bộ hiện tại** | 95,2% | 77,9% | **85,7%** |
| căn cưỡng bức — thô | 65,4% | 85,6% | 74,1% |
| căn cưỡng bức — kéo tới từ kế | 97,6% | 73,0% | 83,5% |

**Kém 2,2 điểm F1.** Mục 5 chốt trước: *"phải thấp hơn hẳn bản hiện tại"* —
không đạt, nên dừng.

**Vì sao:** CTC phát ra **gai nhọn**. Bản thô khai **11,9 giây trong 30 giây là
"giữa các từ"** — với lời nói liên tục thì đó là sai. Kéo mỗi từ tới điểm khởi
phát của từ kế chữa được recall (65,4 → 97,6%) nhưng đánh đổi precision.

### 6.4 Hai chỗ suýt ra số đẹp sai

1. Bản CTC **tôi tự viết** bỏ blank giữa các nhãn cho gọn → **5 mốc không tăng
   dần + 5 mốc vượt biên** trên 114 từ. Dùng `torchaudio.functional.forced_align`
   chuẩn thì cả hai về **0**. Một phép đo có lỗi thì không kết luận được gì.
2. Nếu dừng ở *"114/114 và nhanh 5×"* thì đã giao một thứ **tệ hơn**. Chỉ trọng
   tài độc lập mới thấy — và nó phải độc lập với **cả hai** bên.

### 6.5 Còn để lại gì

- `F:\aura-align` (2,2 GB) **giữ nguyên** — ai mở lại nợ này thì đo tiếp được ngay.
- Cỡ mẫu: **MỘT tệp 30 giây, 114 từ**. Đủ để nói *"chưa chứng minh được là hơn"*,
  **không** đủ để nói *"chắc chắn kém"*.
- Cửa canh `test_DAC_TA_can_cuong_buc_van_o_lai_tai_lieu` giữ kết luận này khỏi
  trôi — vì *"114/114, nhanh 5×"* đọc rất giống một thắng lợi.
