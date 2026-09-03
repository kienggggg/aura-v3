# Kế hoạch — `core/viet_truyen.py`: AURA viết kịch bản, Alpha dựng video

**Trạng thái: CHỜ DUYỆT. Chưa viết dòng mã nào.**

Theo `CLAUDE.md` mục 7: dựng mới một hệ thống thì gửi kế hoạch trước. Và người
duyệt phải **chạy thử** mọi con số, không đọc kỹ. Mọi số dưới đây em đã chạy;
chỗ nào chưa chạy được em ghi rõ là **CHƯA ĐO**.

---

## 1. Số đã đo — đây là thứ quyết định thiết kế, không phải ý thích

### Model không giữ nổi ngân sách chữ

Yêu cầu 232 từ, `qwen3.5:4b`, 5 lượt, hạt giống 1–5:

```
lan    tu   lech   cau khac   giay doc   sinh
  1   214    -18         16      54,9s     81s
  2   346   +114         14      88,7s     84s
  3   273    +41         13      70,0s     68s
  4   190    -42         13      48,7s     59s
  5   134    -98         12      34,4s     56s

dung so tu 0/5   ·   du cau khac nhau 4/5
```

Lệch −42% đến +49%. Nhưng ràng buộc **số câu** thì giữ được 4/5.

### Số câu cũng KHÔNG quyết định được độ dài

Từ chính năm lượt trên: 214/16 = 13,4 · 346/14 = 24,7 · 273/13 = 21,0 ·
190/13 = 14,6 · 134/12 = 11,2 từ mỗi câu.

**11,2 đến 24,7** — hơn gấp đôi. Nên không có núm nào của model điều khiển được
độ dài. Máy phải đo và tự xử lý.

### Tốc độ đọc, 5 mẫu

```
 80 tu (lap)  22,38 s   3,58 tu/s      179 tu (van)  46,38 s   3,86
154 tu (lap)  42,05 s   3,66           266 tu (van)  67,30 s   3,95
240 tu (lap)  65,93 s   3,64
```

Văn xuôi đọc nhanh hơn văn lặp ~7%. Lấy 3,9 → cửa sổ 55–65 s = **215–250 từ**.
Đã kiểm bằng dây chuyền thật: **235 từ/15 câu → PASS**; **266 từ → 67,3 s, FAIL
vì quá dài**.

### Mối nối đã có sẵn

`dung_video(thu_muc_ra: Path, van_ban: str | None = None)` — Alpha nhận văn bản
từ ngoài từ đầu. Không phải sửa Alpha để nối vào.

### Hai cái bẫy đã đo được

**Đừng cho truyện đi qua cửa chat.**

```
"Viết cho tôi một truyện ngắn về người thợ săn..."   tra mang = False   dung
"Kể một câu chuyện HIỆN NAY về thành phố ngập..."    tra mang = True    SAI
```

Một yêu cầu sáng tác có chữ chỉ thời gian bị đem ra máy chủ tìm kiếm: 23–43
giây, và đề bài đi ra ngoài.

**Cấu hình chat dùng lại không được.** `OllamaConfig.num_predict = 768` — 220 từ
tiếng Việt sát trần đó; `temperature = 0.3` chỉnh cho câu trả lời dữ kiện, không
phải văn xuôi.

---

## 2. Phát hiện làm ĐỔI kế hoạch: hệ thống Phòng đang nằm ngoài hàng rào

```
hang rao V3 dang canh   19 tep · 5.116 dong · tran 20
phan KHONG duoc canh     3 tep · 2.723 dong · KHONG CO TRAN

    908  core/phong_alpha.py
  1.009  core/polyglot.py
    806  interface/noi_bo_api.py
```

`tests/test_v3_ranh_gioi.py` đi từ **một** cửa vào là `aura_chat.py`. Cả hệ
thống Phòng không với tới được từ đó, nên không có gì đếm nó.

Đây đúng bệnh `CLAUDE.md` đã ghi về App Thẻ: *"8 tệp, 5.509 dòng, dài hơn phần
được canh — nằm ngoài, không có gì giữ nó khỏi phình. Đúng bệnh v3 sinh ra để
chống, mọc ở phía không ai nhìn."*

Và `core/viet_truyen.py` sẽ rơi **vào đúng vùng ấy**.

Bắt được không phải bằng đọc mã, mà vì phải trả lời câu *"tệp mới nằm ở đâu so
với hàng rào"* — cùng cách đã bắt được App Thẻ hồi 02/09.

---

## 3. Thiết kế

### Phần A — `core/viet_truyen.py`

Mối nối RIÊNG. Không `import core.web_search`, không dùng `OllamaConfig` của
chat.

```
xin_truyen(chu_de, hat)      -> (van_ban, giay)      gọi model, KHÔNG đếm gì
do_kich_ban(van_ban)         -> (trang_thai, ly_do, so)   HÀM THUẦN, ba trạng thái
cat_cho_vua(van_ban)         -> (van_ban_moi, da_cat)     MÁY cắt, model không đếm
viet_kich_ban(chu_de, tran)  -> dict                  vòng có trần, báo số lần thử
```

`do_kich_ban` là hàm **thuần** — để cửa canh đưa được văn bản XẤU vào. Đây là
lỗi đã mắc bốn lần trong `phong_alpha.py`: phép chấm nằm rải trong dây chuyền
thì cửa chỉ khẳng định được "số đo nằm trong khoảng" trên một lượt đạt.

Ba trạng thái, không gộp:

```
DAT             lọt cửa sổ
KHONG_DAT       đo được mà ngoài cửa sổ  (kèm lý do + số)
KHONG_DO_DUOC   model không trả lời, Ollama tắt, hết giờ
```

`viet_kich_ban` **phải trả về số lần đã thử**. Một kịch bản đạt sau 1 lần và
sau 5 lần là hai chuyện khác nhau, và giấu con số ấy là giấu giá.

### Phần B — hàng rào thứ hai, KHÔNG được bỏ

`tests/test_v3_ranh_gioi.py` thêm danh sách đóng thứ hai:

```
V3_CHAT   cửa vào aura_chat.py              trần 20   (đang 19)
V3_PHONG  cửa vào interface/noi_bo_api.py   trần  8   (đang 5, sẽ thành 6)
```

Đúng cấu trúc `CLAUDE.md` từng mô tả và em vừa sửa đi hôm nay vì nó không còn
đúng. Nó đúng khi viết, mất đi khi App Thẻ tách kho, và **cần lại vì lý do
khác**: giờ phần không được canh là hệ thống Phòng.

Gộp một danh sách thì trần mất nghĩa — "25 tệp" không nói được bên nào phình.

---

## 4. Ngưỡng — đăng ký vào `KY_LUAT_THUC_THI.md` TRƯỚC khi viết mã

| ngưỡng | giá trị | lấy từ đâu |
|---|---|---|
| số từ | **215–250** | 3,9 từ/s × 55–65 s; đã kiểm 235 PASS, 266 FAIL |
| câu khác nhau | **≥ 13** | số thẻ = round(60/4,5) = 13 |
| một câu lặp tối đa | **2 lần** | cùng ngưỡng 0,25 của cửa nội dung Alpha |
| trần số lần thử | **3** | xem mục 5 — CHƯA ĐO, có thể phải đổi |

Chép tay vào cửa canh, **không** `import` từ mã — bài học tautological ngày
02/09: khẳng định `(RONG, CAO) == (RONG, CAO)` thì gieo `640, 1136` vẫn xanh.

---

## 5. Lời hứa chịu lực, và cách kiểm từng cái

| lời hứa | kiểm bằng | trạng thái |
|---|---|---|
| model không giữ được ngân sách chữ | 5 lượt, đếm thật | **ĐÃ ĐO** — 0/5 |
| model giữ được ràng buộc số câu | cùng 5 lượt | **ĐÃ ĐO** — 4/5 |
| 215–250 từ lọt cửa sổ video | chạy `dung_video` thật | **ĐÃ ĐO** — 235 PASS |
| cắt bằng máy thì lọt cửa | 5 lượt, ba cách cắt | **ĐANG CHẠY** |
| cắt xong truyện còn ra truyện | đọc câu cuối của mỗi cách | **ĐANG CHẠY** |
| trần 3 lần là đủ | phụ thuộc kết quả trên | **CHƯA ĐO** |
| không đi qua `web_search` | gọi hàm, xem có request nào không | chưa làm |
| hàng rào thứ hai bắt được | gieo ≥6 lỗi vào chính nó | chưa làm |

**Ba dòng cuối chưa có số. Em không viết mã trước khi ba dòng ấy có số.**

### Ba cách cắt đang đo

```
A  cat DUOI   bo cau cuoi dan  -> lot cua, nhung MAT KET TRUYEN
B  cat GIUA   giu cau dau + cac cau cuoi, bo cau giua -> giu mo va ket
C  khong cat  de xem ban goc co lot khong
```

Nếu B đạt ≥4/5 thì lấy B. Nếu cả ba đều dưới 3/5 thì thiết kế này **sai**, và
phải quay lại — không nới ngưỡng cho vừa.

---

## 6. Chỗ CHƯA chặn được — nói thẳng, không viết "đã chặn"

- **Chất lượng văn.** Cửa canh đếm từ, đếm câu, đếm lặp. Nó **không** biết
  truyện hay hay dở, có mạch lạc không, có mở-thân-kết không. Một chuỗi 15 câu
  vô nghĩa nhưng khác nhau vẫn lọt sạch. Đây là giới hạn thật, không vá được
  bằng thêm ngưỡng.
- **Model tự lặp ý.** Nó có thể viết 15 câu khác nhau về mặt chuỗi mà cùng một
  ý. Cửa hiện tại mù chỗ này.
- **Thời gian.** Mỗi lượt sinh 56–88 giây. Trần 3 lần = tới 4,5 phút cho một
  kịch bản, chưa tính dựng video 30 giây. Đây là giá phải nói ra.

---

## 7. Việc KHÔNG làm trong vòng này

- Không sửa `OllamaConfig` của chat. Cấu hình đi theo thứ cần nó (mục 5 luật).
- Không vá `is_search_request`. Bẫy ấy chỉ hại nếu truyện đi qua cửa chat, mà
  thiết kế này không đi qua. Ghi lại thành việc riêng.
- Không nối AURA→Alpha tự động. Vòng này chỉ sinh ra kịch bản đạt chuẩn; ai gọi
  nó và khi nào là chuyện của vòng sau.
- Không làm giao diện.

---

## 8. Em cần Sếp quyết ba chuyện

1. **Hàng rào thứ hai có làm cùng vòng này không?** Em nghĩ có — thêm tệp vào
   vùng không ai đếm rồi hẹn "để sau" là đúng cách 2.723 dòng kia đã sinh ra.
2. **Trần thời gian.** 4,5 phút cho một kịch bản có chấp nhận được không, hay
   phải hạ trần số lần thử xuống 2?
3. **Nếu cả ba cách cắt đều trượt** thì dừng lại bàn tiếp, hay Sếp muốn em thử
   hướng khác luôn (ví dụ: sinh 3 bản song song rồi chọn bản gần cửa sổ nhất)?
