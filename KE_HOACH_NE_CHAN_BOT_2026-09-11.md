# Kế hoạch — AURA tự lấy trang và xử lý chặn bot (11/09/2026)

<!-- KET_CUC:CHUA_DUYET · 11/09/2026 -->
**Trạng thái: CHỜ DUYỆT. Chưa viết dòng mã sản phẩm nào.**

Sếp quyết 11/09: *"AURA nên né chặn bot"*. Theo `CLAUDE.md` mục 7, dựng mới một
hệ thống thì gửi kế hoạch trước. Mọi số dưới đây **đã chạy trên máy này**; chỗ
nào chưa chạy được em ghi rõ **CHƯA ĐO**.

---

## 1. Hiện trạng — AURA KHÔNG tự lấy trang

`interface/chat_adapters.py:ReadOnlySearchGateway` gọi
`exa.web_search_exa(...)` qua `mcporter`. **Exa lo việc crawl.** Nên hôm nay
AURA **không có chỗ nào chạm vào Cloudflare**, và câu hỏi *"có nên né chặn
bot"* chỉ có nghĩa nếu đổi sang **tự lấy trang**.

Đổi sang tự lấy trang mua được hai thứ **không** liên quan tới chặn bot:

* **Riêng tư.** Hiện mọi câu cần tra mạng của Sếp đều đi qua Exa — một bên thứ
  ba. `CLAUDE.md` gọi tên đúng cái hại này ở ca *"câu hỏi riêng tư bị đẩy ra
  Google"*, và bản vá 10/09 (`CHOT:cau-hoi-rieng-khong-ra-mang`) mới chỉ chặn
  được phần sổ phiên trả lời được.
* **Không phụ thuộc hạn mức/khoá của một dịch vụ ngoài.**

---

## 2. Số đã đo — 10 trang, ba nấc, 11/09/2026

Cùng danh sách trang, cùng `httpx`, **đổi đúng một biến mỗi nấc**:

```
nấc 1  httpx mặc định (bot thô)              qua 7/10
nấc 2  chỉ đổi User-Agent thành Chrome giả   qua 7/10
nấc 3  bộ header trình duyệt ĐẦY ĐỦ          0/3 trên ba trang đã chặn
nấc 4  User-Agent TRUNG THỰC có liên hệ      wikipedia 403 -> 200 (2,3 MB)
```

**Đổi User-Agent giả không mua được gì: 7/10 → 7/10.** Ba trang chặn vẫn chặn.

## 3. "Chặn" hoá ra là BA LOẠI, không phải một

Đọc thân phản hồi và header trả về mới tách được:

| trang | ai trả lời | nội dung | loại |
|---|---|---|---|
| `sjc.com.vn` | `server: cloudflare`, `cf-mitigated: challenge` | *"Just a moment…"* | **challenge thật** |
| `stackoverflow.com` | `server: cloudflare`, `cf-mitigated: challenge` | *"Just a moment…"* | **challenge thật** |
| `vi.wikipedia.org` | `server: HAProxy`, `text/plain` 141 byte | *"Please set a user-agent and respect our robot policy"* | **đòi khai báo trung thực** |

**Ca Wikipedia đi NGƯỢC hướng né bot.** Nó không chặn bot — nó đòi biết bot là
ai. UA Chrome giả bị từ chối; UA trung thực
`AURA-v3/1.0 (…; github.com/kienggggg/aura-v3)` **qua ngay, 200, 2,3 MB**.
Camoufox giả vân tay Firefox sẽ **làm hỏng đúng ca này**.

```
7/10  không chặn gì
1/10  đòi UA trung thực   -> một dòng header
2/10  Cloudflare challenge -> mới thật sự cần trình duyệt thật
```

---

## 4. Đề xuất — làm theo NẤC, không nhảy thẳng vào Camoufox

**Nấc A — bộ lấy trang trung thực (rẻ, không cần gói mới).**
`httpx` sẵn có trong 2 gói ngoài của v3. Thêm một hàm lấy trang với UA trung
thực + `robots.txt` + giới hạn nhịp. Đo được: phủ **8/10** trang.

**Nấc B — chỉ cho phần Cloudflare challenge.** Lúc ấy mới hỏi: Camoufox, hay
bỏ qua trang ấy, hay dùng nguồn thay thế (RSS, API chính thức của SJC/Stack
Exchange — Stack Exchange **có API công khai miễn phí**, không cần né gì).

**Nấc B là chỗ Sếp cần quyết lại**, vì nó khác hẳn nấc A về bản chất: nấc A là
*khai báo mình là ai*, nấc B là *giả làm người khác*.

---

## 5. Ngưỡng — đăng ký TRƯỚC khi viết mã

| ngưỡng | giá trị | lấy từ đâu |
|---|---|---|
| trang lấy được bằng nấc A | **≥ 8/10** | đo 11/09, nền 7/10 |
| UA phải nhận dạng được + có URL liên hệ | **bắt buộc** | chính sách Wikimedia, đo được 403 → 200 |
| tôn trọng `robots.txt` | **bắt buộc** | CHƯA ĐO — phải kiểm bằng một trang có `Disallow` |
| nhịp tối đa mỗi tên miền | **CHƯA ĐO** | phải đo, đừng gõ tay một con số |
| RAM thêm khi chạy Camoufox | **CHƯA ĐO** | máy 11,7 GB, lúc chạy app nội bộ đã 9,7 GB (82%) |
| gói ngoài thêm vào | nấc A: **0** · nấc B: **CHƯA ĐO** | v3 đang có đúng 2 gói |

## 6. Lời hứa chịu lực và cách kiểm từng cái

| lời hứa | kiểm bằng | trạng thái |
|---|---|---|
| đổi UA giả không giúp gì | 10 trang, hai nấc | **ĐÃ ĐO** — 7/10 so với 7/10 |
| UA trung thực cứu được Wikipedia | cùng trang, đổi một biến | **ĐÃ ĐO** — 403 → 200 |
| Cloudflare challenge cần trình duyệt thật | chưa thử trình duyệt nào | **CHƯA ĐO** |
| Camoufox chạy được trên Windows | chưa tải | **CHƯA ĐO** |
| *"chạy nhẹ trên VPS 5 đô"* | lời của người bán VPS | **KHÔNG ĐO ĐƯỢC** — nguồn có xung đột lợi ích |
| tự lấy trang giữ câu hỏi ở lại máy | cần một bộ tìm kiếm local | **CHƯA ĐO** — vẫn phải hỏi ai đó "trang nào" |

**Ba dòng cuối chưa có số. Em không viết mã trước khi ba dòng ấy có số.**

## 7. Việc KHÔNG làm vòng này

* **Không tự tải Camoufox.** Tải gói phải có Sếp duyệt kèm tên tệp, nguồn, cỡ,
  SHA-256 — và đây là một bản Firefox vá, không phải thư viện nhỏ.
* **Không tự viết mã vượt challenge**, không tự giải CAPTCHA.
* Không bỏ Exa trong vòng này. Nấc A chạy **song song**, không thay thế.

## 8. Giới hạn phải nói cùng lúc với đề xuất

Vượt Cloudflare challenge là **qua mặt một biện pháp trang dựng lên có chủ
đích**. Điều khoản của nhiều trang cấm việc ấy, và nó không phải một câu hỏi kỹ
thuật. Phép đo trên cho thấy **8/10 nhu cầu đạt được mà không cần né gì**, nên
em đề nghị tách bạch: làm nấc A trước, để nấc B lại thành một quyết định riêng
có số liệu của chính nó.

Và với hai trang ấy còn đường khác chưa thử: **Stack Exchange có API công khai
miễn phí**; SJC có trang giá dạng khác. Chưa đo — nhưng nếu đi được thì rẻ hơn
và không đụng tới ToS.

## 9. Ba câu cần Sếp quyết

1. **Nấc A có làm không?** Nó không né gì, không thêm gói, phủ 8/10.
2. **Nấc B** — giả vân tay trình duyệt để vượt challenge: làm, hay thử API
   chính thức trước?
3. **Tự lấy trang có THAY Exa không**, hay chạy song song? Thay thì được riêng
   tư, mất chất lượng tìm kiếm; song song thì vẫn gửi câu hỏi ra ngoài.
