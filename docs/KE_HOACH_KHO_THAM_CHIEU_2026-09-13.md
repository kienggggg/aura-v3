# Kế hoạch — Kho đoạn văn mẫu cho phòng AURA (13/09/2026)

<!-- KET_CUC:DANG_LAM · 13/09/2026 -->
**Trạng thái: ĐANG LÀM — Sếp duyệt 13/09. Mã sản phẩm CHƯA đổi; đang đo nhánh bộ luật (§11).**

Sếp chọn việc này ngày 13/09. `CLAUDE.md` §7: dựng mới một hệ thống thì gửi kế
hoạch trước. Mọi con số dưới đây **đã chạy trên máy này**; chỗ nào chưa chạy
được thì ghi **CHƯA ĐO**.

---

## 1. Việc này là gì — và KHÔNG là gì

**Là:** một thư mục đoạn văn mẫu Sếp tự bỏ vào. Khi phòng AURA viết kịch bản,
máy lấy **một** đoạn mẫu trong thư mục **giọng** Sếp chọn, đặt cạnh lời nhắc để
model học GIỌNG VĂN.

**Không là:** kho dữ kiện để trả lời câu hỏi; không nối NotebookLM; AURA không
tự tải sách từ mạng.

## 2. Vì sao là ĐOẠN MẪU chứ không phải LUẬT — và vì sao đó vẫn là giả thuyết

```
chấm mù 16/08, Sếp chấm   bản CÓ 13 luật văn phong  THUA  bản không luật
                          cả hai: "không tạo cảm giác muốn đọc"
phòng viết hôm nay        cửa chỉ đếm từ / câu / lặp và kiểm câu mở nêu đề —
                          chính module core.viet_truyen ghi "không biết truyện
                          hay hay dở"
```

Đoạn mẫu là **cho xem** thay vì **dặn**. Chưa ai đo trên máy này, và nó có thể
thua y như bộ luật đã thua. Nên §6 đặt luật quyết định **trước** khi chạy.

## 3. NotebookLM — đã kiểm, đề xuất KHÔNG nối vòng này

| điều | kiểm bằng | kết quả |
|---|---|---|
| bản thường có API công khai | tài liệu Google + nguồn tổng hợp, 13/09 | **KHÔNG** |
| bản Enterprise có API | tài liệu Google Cloud | **CÓ** — bản xem trước, qua Google Cloud, tài khoản doanh nghiệp |
| thư viện không chính thức (`notebooklm-py`…) | README | điều khiển bản thường bằng chính **phiên đăng nhập Google** của người dùng |
| mục 15 kho công nghệ: endpoint `notebooklm.google.com/mcp/v1` | tìm tài liệu chính thức | **không thấy** — coi là CHƯA KIỂM, đừng dùng |

Đường không chính thức bị loại vì AURA **không được giữ mật khẩu hay phiên đăng
nhập** của Sếp, và nó vỡ mỗi khi Google đổi giao diện.

**Đề xuất:** Sếp cứ dùng NotebookLM để tự đọc, tự nghiên cứu. Cùng những tệp
ấy, bỏ thêm một bản vào `data/tham_chieu/` cho AURA — một thư mục trên máy,
không gửi đi đâu.

## 4. Thiết kế

**Chỗ để:** `data/tham_chieu/<giong>/<tac_pham>.txt`, UTF-8. `<giong>` là tên
thư mục Sếp tự đặt (`co_tich`, `tien_hiep`, `do_thi`…).

**Không để lọt lên GitHub — đã kiểm 13/09:**

```
repo kienggggg/aura-v3              PUBLIC
git check-ignore data/tham_chieu/…  khớp `.gitignore:11: data/*`
```

Thêm cửa canh: không tệp nào dưới `data/tham_chieu/` được git theo dõi, và
không câu nào của đoạn mẫu được chép vào đặc tả, sổ bệnh án hay commit.

**Cắt đoạn:** theo đoạn văn của tác phẩm, gộp lại cho tới 120–250 từ. Số đoạn
trên mỗi tác phẩm: **CHƯA ĐO** — cần tệp thật của Sếp.

**Chọn đoạn:** đúng **1** đoạn, trong thư mục giọng Sếp chọn, theo hạt giống.
Kết quả tất định và lặp lại được. **Không** chọn theo độ gần với đề, vì ba lý
do:
- Đề giống nhau thì dễ chép luôn tình tiết.
- BM25 và bge-m3 mới chỉ đo trên tài liệu kỹ thuật, chưa đo trên văn học.
- Phòng viết không được import chỉ mục `tra kho:`, vì hai hệ chỉ được dùng chung
  đúng hai tệp.

Không dựng chỉ mục nhúng: bge-m3 tốn 1,49 s mỗi đoạn (649,8 s cho 437 đoạn, đo
08/09). Một bộ tiểu thuyết 100.000 từ ≈ 500 đoạn ≈ 12 phút (**ước**, CHƯA ĐO).

**Đặt vào lời nhắc:** TRƯỚC lời dặn đã đo, không sửa chữ nào của lời dặn:

```
ĐOẠN VĂN MẪU — chỉ để học giọng văn. KHÔNG chép câu chữ, tên nhân vật, tình tiết:
«…một đoạn 120–250 từ…»

<lời dặn phòng viết, giữ nguyên từng chữ>
```

Mặc định **TẮT**. Chỉ bật cho từng việc khi Sếp chọn giọng.

**Tệp mã:** không thêm tệp nào. Phần đọc thư mục, cắt và chọn (ước ~60 dòng)
nằm trong chính module core.viet_truyen. Danh sách đóng của phòng nội bộ có trần
8 và đang dùng 7, nên một tệp mới sẽ ăn ô cuối cùng — không đáng cho ~60 dòng.

## 5. Giá — đã đo 13/09

```
tiếng Việt văn xuôi      1,17 token / từ      (đoạn 235 từ -> 274 token)
đọc thêm một đoạn mẫu    274 token -> 6,0 s   (đọc 48 tk/s lúc đo; hôm nay dao
                                               động 25–51 tk/s, tức 5–11 s)
ngân sách ngữ cảnh       4.096 = lời nhắc ~100 + đoạn mẫu ~290 + viết tới 1.400
                         -> còn dư ~2.300, vừa cả 2 đoạn nếu cần
```

## 6. Đo — thước và luật quyết định viết TRƯỚC khi chạy

**Vòng 1 — máy chấm, không cần Sếp.** Chọn 3 đề trong bộ 8 đề đã dùng ngày
08/09. Mỗi đề 5 hạt giống × 2 nhánh (không mẫu / có 1 đoạn mẫu), chạy xen kẽ.

| đơn | ngưỡng |
|---|---|
| lọt cửa phòng viết, 15 lượt | có mẫu ≥ không mẫu − 2 |
| chuỗi từ liền nhau chung với đoạn mẫu, dài nhất | ≤ mức tình cờ của nhánh đối chứng, và tuyệt đối ≤ 8 từ |
| tên riêng của đoạn mẫu xuất hiện trong bài | đếm và báo, không làm ngưỡng |
| thời gian mỗi lần viết | báo, không làm ngưỡng |

*Mức tình cờ* = so bài của nhánh **không** mẫu với chính đoạn mẫu mà nhánh kia
nhận. Bài ấy chưa từng thấy đoạn mẫu, nên mọi chỗ trùng đều là trùng tình cờ
(những cụm như "một ngày nọ", "trong khi đó").

**Vòng 2 — Sếp chấm mù, như ngày 16/08.** Mỗi đề một cặp (hạt giống 1, cả hai
bản đã lọt cửa), nhãn xáo, đáp án khoá trong tệp riêng. Mỗi cặp Sếp trả lời:
*bản nào hay hơn*; mỗi bản: *có muốn đọc tiếp không*.

**Luật quyết định, viết trước:** chỉ cho phép bật kho mẫu khi cả ba điều sau
cùng đúng:
- bản có mẫu thắng **≥ 2/3 cặp**;
- cửa chép **0 vi phạm**;
- tỉ lệ lọt cửa không tụt quá ngưỡng.

Hỏng một điều thì **không** bật, và ghi số lại. Đây là cùng hình dạng với cổng
đã làm bộ luật văn phong trượt ngày 16/08.

**Giới hạn nói trước:** n = 3 cặp. Thắng 2/3 là đủ để **bật**, chưa đủ để gọi
là **chứng minh**.

## 7. Rủi ro — và chỗ dựa thật

| rủi ro | chỗ dựa | trạng thái |
|---|---|---|
| model chép nguyên câu của tác phẩm có bản quyền vào kịch bản, rồi kịch bản lên video | cửa chép của máy, không phải lời dặn "không chép" | **CHƯA ĐO** — vòng 1 đo |
| câu văn chương dài làm hỏng cửa từ/câu (trần 22,7 từ/câu) | tỉ lệ lọt cửa ở vòng 1 | **CHƯA ĐO** |
| tác phẩm lọt lên repo PUBLIC | `.gitignore` + cửa canh | `.gitignore` **ĐÃ KIỂM**; cửa canh viết khi làm |
| đoạn mẫu có câu mệnh lệnh trá hình | giọng văn chứ không phải lệnh; vẫn cho đi qua bộ lọc mệnh lệnh của web | **CHƯA ĐO** |

## 8. Việc KHÔNG làm vòng này

- Không nối NotebookLM, dù bản chính thức hay không chính thức.
- Không tự tải tác phẩm nào: Sếp bỏ tệp vào thư mục.
- Không dựng chỉ mục nhúng, không chọn đoạn theo độ gần đề.
- Không đổi lời dặn đã đo của phòng viết.

## 9. Phòng Alpha — ngoài phạm vi, ghi để khỏi quên

Sếp nói đúng: phòng Alpha không có vật tham chiếu. Hướng đã nêu 13/09: Sếp chọn
vài video dọc mẫu (Sếp tự tải), máy đo những gì đo được bằng ffprobe/ffmpeg —
nhịp cắt cảnh, tốc độ đọc, độ ồn, khoảng im, mật độ chữ trên hình. Video Alpha
dựng ra được so với dải số ấy. Dây chuyền Remotion Sếp gửi ngày 06/09 là một mẫu
có sẵn. Chờ Sếp chọn sau.

## 10. Ba câu cần Sếp quyết

1. **Duyệt thiết kế §4?** Thư mục trên máy, 1 đoạn chọn theo hạt giống, mặc
   định tắt, không thêm tệp mã.
2. **Vòng thử dùng giọng nào?** Cần một thư mục có 2–3 tác phẩm, tổng ≥ 20 đoạn.
   Sếp bỏ tệp vào, em không tải.
3. **Sếp chấm mù 3 cặp ở vòng 2 được không?** Máy không chấm được "hay".

Nguồn cho §3:
[NotebookLM Enterprise — Google Cloud](https://cloud.google.com/agentspace/notebooklm-enterprise/docs/overview) ·
[Does NotebookLM Have an API? 2026](https://autocontentapi.com/blog/does-notebooklm-have-an-api) ·
[notebooklm-py](https://github.com/teng-lin/notebooklm-py)

## 11. Sửa 13/09 — Sếp duyệt, và thêm hai việc

Sếp trả lời: *"có duyệt, phòng Alpha để sau, bạn chấm trước đi, vậy làm 1 bộ luật
phòng AURA…"*.

- **§4 duyệt.** Câu 2 (giọng nào, tác phẩm nào) chưa có — vòng đoạn mẫu chờ tệp
  của Sếp trong `data/tham_chieu/<giong>/`.
- **Bộ luật phòng AURA:** `docs/BO_LUAT_PHONG_AURA_2026-09-13.md`. Dùng làm thước
  chấm của em; bản gọn sáu dòng là một nhánh thử riêng (`CHOT:bo-luat-aura`) —
  ngày 16/08 luật trong lời nhắc đã thua, nên phải đo.
- **Vòng 2 đổi:** em chấm mù TRƯỚC — điểm ghi và băm SHA-256 trước khi mở khoá
  nhãn; Sếp chấm lại mới là chốt. Độ khớp giữa hai người được ghi lại.
- **Phát hiện khi dựng bản nền, ngoài phạm vi nhưng chặn đường:** bộ cắt giữa của
  phòng viết bỏ 39–48 % số câu (10/23 · 7/18 · 11/23), cách một câu bỏ một câu, và xoá đúng mạch truyện
  (xem `CHOT:bo-luat-aura`). Đoạn mẫu hay bộ luật có giúp viết ra truyện thì bộ cắt
  cũng xoá đi trước khi tới video — nên sửa bộ cắt là việc phải làm trước khi bật
  bất cứ thứ gì ở kế hoạch này.
