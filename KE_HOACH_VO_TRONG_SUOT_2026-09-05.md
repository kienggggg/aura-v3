# KẾ HOẠCH — VỎ TRONG SUỐT

*Gửi Sếp duyệt trước khi viết dòng mã nào. Theo `CLAUDE.md` mục 7.*

Sếp yêu cầu: *"nhìn được từng công đoạn, giống cái vỏ trong suốt bên ngoài cỗ
máy — có thể nhìn không hiểu gì nhưng nhất định phải nhìn."*

---

## 1. Hiện trạng, đo được ngày 05/09/2026

```
giao dien goi     fetch('/api/pipeline/run')  -> MOT lan, dong bo
ghi so cai        dung 1 lan, o CUOI chuoi
streaming/SSE     0 ket qua khi quet ca thu muc interface/
"stream": False   4 cho: local_first_gateway · omega · phong_noi_bo · viet_truyen
"think": False    cung 4 cho — phan model nghi tham bi tat
```

Bấm một thẻ thì màn hình trắng **166 giây**, và tới **330 giây** nếu AURA phải
sinh lại. Xong mới có một cục JSON.

**Nhưng cỗ máy đã trong suốt sẵn.** Mỗi phòng ghi tệp vào
`data/<phòng>/<task_id>/` ngay khi xong, kèm SHA-256. Alpha để lại đúng thứ tự
nó làm: `voice.wav` → `card_01..13.png` → `phu_de.srt` → `nhac_nen.wav` →
`video.mp4`. **Thiếu cửa sổ, không thiếu dấu vết.**

---

## 2. Hai cơ chế, không cái nào thay cái nào

| | soi được gì | thời lượng nó chiếu |
|---|---|---|
| **Stream token** | chữ hiện dần lúc model viết | ~70–100 s của bước `aura` |
| **Mốc tiến độ** | bước nào đang chạy | ~90 s: TTS · thẻ · phụ đề · nhạc · render · chấm |

Khâu Alpha **không có token nào** — chỉ có `ffmpeg`. Stream không soi được nó.

---

## 3. Việc sẽ làm

### 3a. Mốc tiến độ (làm trước — nó phủ toàn chuỗi)

- Mỗi bước ghi **hai dòng** vào `data/tien_do/<task_id>.jsonl`:
  `{"buoc": i, "phong": "alpha", "trang_thai": "DANG_CHAY", "luc": ISO}`
  rồi `{"..., "trang_thai": "PASS", "ms": 35100, "hien_vat": 22}`.
- `GET /api/tien_do/<task_id>` đọc tệp ấy, trả về nguyên trạng.
- Giao diện poll 1 giây/lần, vẽ từng bước sáng lên.

**Vì sao `.jsonl` chứ không giữ trong RAM:** cùng lý do sổ cái là tệp — tiến
trình chết thì RAM mất, tệp còn. Và nó **kiểm được bằng cách đọc đĩa**, đúng
nguyên tắc *"bằng chứng trên đĩa là chân lý duy nhất"*.

**Vì sao poll chứ không SSE/WebSocket:** không thêm phụ thuộc, không thêm đường
mã bất đồng bộ mới. v3 hiện có đúng 2 gói ngoài; giữ nguyên con số ấy.

### 3b. Stream token cho bước `aura`

- `_xin_model` nhận `khi_co_chu=None`: có thì bật `"stream": True` và gọi lại
  cho từng mảnh; không thì giữ nguyên đường cũ.
- **Máy vẫn đếm trên văn bản ĐẦY ĐỦ.** Stream chỉ để nhìn; mọi cửa chấm không
  đổi một dòng.
- `think` để **Sếp bật/tắt được**, mặc định giữ `False` như hiện tại.

---

## 4. Ngưỡng nghiệm thu — ĐĂNG KÝ TRƯỚC KHI VIẾT

1. **Độ trễ hiển thị ≤ 2,0 giây.** Mỗi bước phải hiện trên màn hình trong vòng
   2 giây kể từ lúc nó THẬT SỰ bắt đầu — đo bằng đối chiếu `luc` trong
   `.jsonl` với thời điểm `/api/tien_do` trả về dòng ấy. Không đo bằng mắt.
2. **Không bước nào bị bỏ sót.** Số dòng `DANG_CHAY` phải bằng số bước trong
   `KE_HOACH`, và mỗi dòng phải có dòng kết đôi.
3. **Ca đối chứng — BƯỚC TREO.** Bơm một phòng cố ý ngủ 60 giây. Màn hình phải
   nói rõ *bước ấy đang chạy được N giây*, khác hẳn trạng thái *chưa bắt đầu*.
   **Đây là điểm dễ hỏng nhất:** một thanh tiến trình trông như đang chạy trong
   khi tiến trình đã chết còn tệ hơn không có gì.
4. **Ca đối chứng — BƯỚC GÃY.** Bơm một phòng ném lỗi. Màn hình phải chuyển
   sang trạng thái gãy, và các bước sau phải hiện `CHUA_CHAY`, không hiện
   "đang chạy" mãi mãi.
5. **Stream không đổi phán quyết.** Cùng một hạt giống, chạy có stream và không
   stream phải cho **cùng văn bản và cùng trạng thái**. Không có thì stream đã
   lén đổi thứ đang đo.

Mỗi ngưỡng phải có phép **gieo lỗi** làm nó đỏ trước khi tính là xong.

---

## 5. Việc sẽ KHÔNG làm, nói ra trước

- **Không bọc desktop app.** `noi_bo_app.py` đã phục vụ HTML ở `127.0.0.1`. Bọc
  `pywebview` là thêm **gói ngoài thứ ba** vào một repo đang có đúng hai. Cửa sổ
  trong suốt không cần khung cửa bằng Electron.
- **Không đụng phòng nào.** Bảy phòng giữ nguyên chữ ký và hành vi. Mốc tiến độ
  ghi ở `chay_chuoi_phong`, chỗ đã biết thứ tự các bước.
- **Không hứa "thấy được vì sao".** Màn hình sẽ cho thấy *đang làm gì* và *mất
  bao lâu*, **không** giải thích *vì sao model viết câu đó*. Sếp nói "nhìn không
  hiểu gì cũng được" — kế hoạch này làm đúng chừng ấy, không hơn.

---

## 6. Giá

```
3a moc tien do    ~120 dong ma + bai canh   ·  poll 1s
3b stream token   ~60 dong ma + bai canh    ·  chi soi buoc aura
do nghiem thu     2 luot chay that (~6 phut) + gieo loi
```

Chi phí lúc chạy: mỗi bước ghi thêm 2 dòng vào một tệp — không đáng kể so với
166 giây của chuỗi.

---

## 7. Thứ tự đề nghị

1. **3a trước.** Nó phủ toàn chuỗi và trả lời đúng câu Sếp hỏi.
2. Đo, gieo, chạy đủ bộ, commit.
3. **3b sau**, nếu Sếp vẫn muốn thấy chữ hiện dần — nó chỉ thêm cho một bước.

Sếp gật từng mục hay gật cả gói thì em bắt đầu.
