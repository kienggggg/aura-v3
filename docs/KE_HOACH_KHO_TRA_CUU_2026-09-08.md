# Kế hoạch — Kho tra cứu cục bộ cho AURA (08/09/2026)

**Trạng thái: SẾP DUYỆT 08/09/2026 — "tra cứu tường minh, ăn ô cuối cũng
được". Đã giao; xem mục 9 cho những con số đổi sau khi chạy thật.**

*(Câu này lúc gửi đi là "CHỜ SẾP DUYỆT. Chưa viết một dòng mã sản phẩm nào."
Giữ lại nguyên văn ở đây vì nó là điều kiện của luật §7 — kế hoạch phải ra đời
trước mã, và dòng này là bằng chứng nó đã thế.)*

`CLAUDE.md` §7 luật 1: *"Dựng mới một hệ thống thì gửi kế hoạch trước, không
viết mã trước."* Luật 2: *"Người duyệt phải CHẠY THỬ mọi con số và mọi lời hứa
kỹ thuật."* Nên mọi con số dưới đây **đã chạy trên chính máy này hôm nay**, và
tệp nguyên mẫu còn ở scratchpad để Sếp chạy lại.

---

## 1. Kho công nghệ chỉ sai đường, và đó là phát hiện đầu tiên

`D:\KHO_CONG_NGHE.md` dòng 592 ghi nợ này kèm lời khuyên:

> **Docling** `BENCHMARKED` · **MarkItDown** `BENCHMARKED` · **MinerU`INSTALLED`
> — *"Docling và MarkItDown đã đo so sánh được trên máy này — đó là đường rẻ
> nhất, không phải hai mục mới."*

Chạy `importlib.util.find_spec` ở cả ba venv trên máy:

| gói | nhãn trong kho | đo được |
|---|---|---|
| `docling` | `BENCHMARKED` 8,2s | **false** ở venv v3, python hệ thống, venv STT |
| `markitdown` | `BENCHMARKED` 8,1s | **false** |
| `mineru` | `INSTALLED` | **false** |

Ba nhãn ấy là số của một máy khác — đúng ca *"Đo cái app KHÔNG chạy thì mọi
con số đều là số của người khác"*.

Và kể cả nếu có cài: chúng chuyển PDF/DOCX sang Markdown, trong khi **corpus ở
đây đã là Markdown sẵn**. Chúng giải một bài toán kho này không có.

## 2. Corpus thật nhỏ hơn tưởng 56 lần

Phép đo đầu của tôi ra **4.259 tệp `.md`** — và con số ấy sai. 4.160 tệp nằm
trong `data/`: nhật ký chạy, không phải tài liệu. Đếm đúng bằng `git ls-files`:

| | |
|---|---|
| tệp `.md` git theo dõi trong kho v3 | **73 tệp · 711.187 byte** |
| `D:\KHO_CONG_NGHE.md` + `D:\CONG_NGHE_TONG_HOP.md` | 2 tệp · 80.979 byte |
| **tổng corpus** | **75 tệp · ~792 KB · 946 đoạn** |

792 KB nằm gọn trong RAM. Không cần cơ sở dữ liệu vector, không cần gói mới.

## 3. Thứ cần là bắc cầu từ vựng, và nó đã nằm sẵn trên máy

Các ca trượt của tìm kiếm từ khoá thuần đều cùng một bệnh: tài liệu ghi *"trần
RAM 256 MB"*, Sếp hỏi *"giới hạn bộ nhớ"*; tài liệu ghi *"không GPU rời"*, Sếp
hỏi *"card đồ hoạ"*. BM25 không bắc được cầu ấy.

`ollama list`: **`bge-m3:latest` 1,2 GB, tải 3 ngày trước, chưa ai gọi.** Model
nhúng đa ngữ mạnh tiếng Việt. Vì là model của Ollama nên **0 gói Python mới** —
`httpx` đã nói chuyện với Ollama từ `core/local_first_gateway.py`.

Đúng bài *"một khả năng có sẵn mà không ai gọi thì bằng không"*.

## 4. Phép đo

**Cách chấm:** mỗi câu hỏi kèm một `dấu hiệu` — chuỗi PHẢI có mặt trong đoạn
tìm được thì mới tính đúng. Không chấm theo tên tệp, vì tên tệp là **nhãn của
tôi**; chuỗi thì ai cũng kiểm lại được.

**Hai bộ câu hỏi, và bộ B viết TRƯỚC khi biết thiết kế nào thắng.** Chỉnh thiết
kế bằng bộ A rồi khoe số trên bộ A là vô nghĩa — ca *"một hằng số fit từ chính
mẫu dùng để kiểm"*.

### 4.1 Chọn thiết kế trên bộ A

| máy tìm | top-1 | top-3 | tách được "không tìm thấy"? |
|---|---|---|---|
| BM25, chỉ mục đầy đủ | 6/10 | 6/10 | không |
| BM25, bỏ `docs/lich_su/` | 6/10 | 6/10 | "có" — **nhưng khe chỉ 0,01** |
| bge-m3, chỉ mục đầy đủ | 4/10 | 6/10 | không |
| bge-m3, bỏ `docs/lich_su/` | 5/10 | 6/10 | không |
| RRF (trộn thứ hạng), chỉ mục đầy đủ | 6/10 | 8/10 | không |
| **RRF, bỏ `docs/lich_su/`** | **8/10** | **8/10** | không |

`docs/lich_su/` là 511/946 đoạn — 60+ tệp bàn giao đã bị thay thế, chúng chen
chỗ của `CLAUDE.md`. Bỏ chúng đi là **curation**, không phải mẹo.

### 4.2 Kiểm trên bộ B — 10 câu giữ riêng

| | bộ A | **bộ B (giữ riêng)** |
|---|---|---|
| RRF, bỏ `lich_su` — top-1 | 8/10 | **4/10** |
| RRF, bỏ `lich_su` — top-3 | 8/10 | **8/10** |

**top-1 tụt 8 → 4. top-3 giữ nguyên 8/10 ở cả hai bộ.**

Đó là con số ổn định duy nhất trong toàn bộ phép đo, và nó quyết định thiết kế:
**phải hiện BA đoạn, không được hiện một, và không được gọi đoạn nào là "câu
trả lời".**

### 4.3 Cổng "không tìm thấy": KHÔNG LÀM ĐƯỢC

Khe giữa nhóm có đáp án (8,55–22,60) và nhóm không có (7,59–8,54) là **0,01**
trên một thang rộng 15 điểm. Đó không phải tách rời, đó là trùng hợp. Dựng cổng
theo ngưỡng ấy rồi chạy bộ B: **3/10 câu có đáp án bị chặn nhầm**, và **1/3 ca
đối chứng vẫn lọt** (*"thời tiết Hà Nội ngày mai"* → `SO_BENH_AN.md`).

Cổng đổi 2 lượt trúng lấy 2/3 lượt chặn. **Bỏ cổng.**

### 4.4 Giá

| | đo được |
|---|---|
| nhúng một câu hỏi (bge-m3, model đã nạp) | **107–129 ms**, giữa **115 ms** |
| dựng chỉ mục 946 đoạn | **1.058 giây** (17,6 phút), một lần |
| tệp chỉ mục trên đĩa | 13.050.301 byte |
| gói Python mới | **0** |

> Con số *"4,2 giây mỗi câu hỏi"* tôi báo ở lượt đo đầu là **sai**: tôi lấy một
> đoạn văn 330 ký tự làm que đo thay vì một câu hỏi thật. Que đo sai thì con số
> đo thứ khác.

---

## 5. Thiết kế đề xuất

**Một lệnh tra cứu tường minh. KHÔNG tự chèn vào mọi lượt chat.**

```
Sếp: tra kho: ngắt mạng cho polyglot làm được chưa

AURA: 3 đoạn gần nhất trên đĩa — em KHÔNG chắc đoạn nào đúng,
      Sếp đọc rồi tự chấm:

  1. KY_LUAT_THUC_THI.md › "PATH nói có, chạy thì không"
     …CHƯA CHẶN ĐƯỢC — đo lại 08/09, urlopen vẫn trả mã 200…
  2. …
  3. …
```

Vì sao **không** tự chèn: `CLAUDE.md` §4 đã đo được rằng *"Lời dặn không phải
phép đo"* — một nguồn nói sai thì model tin. top-1 chỉ đúng 4/10 trên bộ giữ
riêng, nên tự chèn đoạn hạng nhất vào mọi lượt là **rót một đoạn sai vào 6/10
lượt**. Hiện ba đoạn kèm tên tệp và tiêu đề thì Sếp thấy ngay nó lệch.

**Đường đi:** `interface/noi_bo_api.py` → `core/tra_cuu.py` → Ollama `bge-m3`
qua `httpx`. Chỉ mục lưu ở `data/`, không vào git.

---

## 6. Giá phải trả — HÀNG RÀO HẾT CHỖ

Đây là chỗ đắt nhất và phải quyết trước khi viết mã:

| danh sách | đang có | trần | sau khi thêm `core/tra_cuu.py` |
|---|---|---|---|
| `V3` (đi từ `aura_chat.py`) | 19 | 20 | **20/20 — hết chỗ** |
| `V3_PHONG` (phòng nội bộ) | 7 | 8 | **8/8 — hết chỗ** |

Tệp mới ăn **ô cuối cùng** của một trong hai bên, dù đặt ở đâu. Không có lựa
chọn "để dành". Nếu Sếp thấy kho tra cứu không đáng một ô cuối, thì câu trả lời
đúng cho nợ này là **đóng nó lại kèm phép đo**, chứ không phải nới trần.

> Ghi thêm: chú thích ở `tests/test_v3_ranh_gioi.py` dòng 83 viết *"Đang 3"*
> trong khi `V3_PHONG` có **7** mục. Tài liệu tụt lại sau phép đo — đúng bệnh
> `CLAUDE.md` mô tả về câu *"đúng 17 tệp"*. Chưa sửa vì ngoài phạm vi.

---

## 7. Cách chấm — đăng ký TRƯỚC, chép tay xuống cửa canh

| đơn | ngưỡng |
|---|---|
| top-3 trên bộ B (giữ riêng) | **≥ 8/10** |
| top-3 trên bộ A | **≥ 8/10** |
| nhúng một câu hỏi | **< 400 ms** (đo được 115 ms, biên 3,5 lần) |
| gói Python ngoài | **vẫn đúng 2** |
| Ollama không chạy | **KHÔNG ĐO ĐƯỢC**, không phải "không tìm thấy" |

**Ba thứ bắt buộc:**

1. **Ca đối chứng:** ba câu không có đáp án trong kho. Vì cổng đã bỏ, bài này
   không đòi chúng bị chặn — nó đòi kết quả **hiện đúng tên tệp**, để Sếp thấy
   ngay là lệch. Và nó ghi lại rằng 1/3 ca đối chứng từng lọt qua cổng.
2. **Gieo lại lỗi:** bỏ `docs/lich_su/` khỏi bộ lọc → top-1 phải tụt; hỏng
   đường gọi Ollama → phải ra `KHÔNG ĐO ĐƯỢC` chứ không ra "không tìm thấy".
3. **Bộ B không được sửa để cho đẹp số.** Nó nằm trong tệp test, có chú thích
   ghi ngày viết. Sửa nó là sửa thước.

---

## 8. Ba câu cần Sếp quyết

1. **Có đáng một ô cuối của hàng rào không?** top-3 8/10 nghĩa là cứ 5 câu thì
   1 câu không có đáp án trong ba đoạn hiện ra.
2. **Tra cứu tường minh (`tra kho: ...`) — đúng ý Sếp chưa,** hay Sếp muốn nó
   tự chạy mỗi lượt? Nếu tự chạy thì em phải nói trước: 6/10 lượt sẽ rót một
   đoạn không liên quan vào ngữ cảnh.
3. **Corpus lấy tới đâu?** Đề xuất: 73 tệp git theo dõi (bỏ `docs/lich_su/`) +
   2 tệp kho công nghệ trên `D:\`. Có muốn thêm gì không.

---

## 9. ĐO LẠI SAU KHI GIAO (08/09/2026, cùng ngày)

Sếp duyệt lúc kế hoạch còn mang số của **nguyên mẫu**. Bản chạy thật khác ở bốn
chỗ, và kế hoạch giữ nguyên câu chữ cũ ở trên để thấy được chỗ lệch:

| | kế hoạch (nguyên mẫu) | **bản chạy thật** |
|---|---|---|
| số đoạn trong chỉ mục | 946 (chưa lọc) / 435 (đã lọc) | **437** |
| dựng chỉ mục | 1.058 giây · 13.050.301 byte | **649,8 giây · 6.659.925 byte** |
| bộ A — top-1 | 8/10 | **7/10** |
| nhúng một câu hỏi | 115 ms | **104 ms** (giữa, trong một vòng lặp) |

**Con số 115 ms trong kế hoạch đo bằng QUE KHÁC** — `urllib` thô trong một vòng
lặp chặt. Đường sản phẩm dựng `httpx.AsyncClient` mỗi lượt, và cửa canh đầu tiên
đo được **497 ms**, đỏ so với trần 400 ms. Đọc ra thì như *"bge-m3 chậm"*; thật
ra **194 ms trong đó là phí dựng client** (httpx dựng ngữ cảnh SSL dù đây là
`http://` tới localhost). Vá bằng cách dùng lại client theo vòng lặp sự kiện:
giữa 396 -> 104 ms. Trần trong đặc tả hạ xuống **300 ms trên GIỮA của 5 lượt**,
và đo trong MỘT vòng lặp — vì `asyncio.run` mỗi lượt là hiện vật của bộ test,
không phải hình dạng của lượt chat thật.

`top-3 = 8/10` trên **cả hai bộ** — đúng như kế hoạch hứa, và là cơ sở của việc
hiện ba đoạn thay vì một.
