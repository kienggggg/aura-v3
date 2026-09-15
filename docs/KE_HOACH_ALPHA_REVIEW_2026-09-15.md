# Kế hoạch — Alpha làm video review công nghệ (15/09/2026)

<!-- KET_CUC:DANG_LAM · 15/09/2026 -->
**Trạng thái: ĐANG LÀM. Sếp duyệt ngày 15/09** (*"ok duyệt, bật sổ chụp sao đi"*).
- **Sổ chụp sao đã bật.** Máy chạy tools/so_sao.py mỗi ngày lúc 09:00 bằng tác vụ Windows
  "AURA so chup sao"; nếu lúc ấy máy tắt thì chạy khi máy bật lại. Lượt đầu 15/09 chụp 1.222 repo.
  Bảng tuần đầu tiên có vào ngày 22/09. Giới hạn: mỗi truy vấn chỉ lấy 300 kết quả đầu, xếp theo
  sao, trong khi truy vấn repo mới có 1.364 kết quả.
- **Đề đầu tiên, Sếp chọn:** phân tích loạt phim **Skibidi Toilet**. Ngưỡng đăng ký ở
  `CHOT:alpha-review-vong-0`. Không dùng clip, ảnh nhân vật hay nhạc của phim, vì chủ phim đang
  chủ động đòi bản quyền.
- 5 repo cho các video review sau: CHƯA chọn.
- **Video đầu tiên đã dựng ngày 15/09**, 63,48 s. 5/6 hàng của `CHOT:alpha-review-vong-0` ĐẠT; hàng
  "Sếp muốn xem hết" CHỜ SẾP.
  - Kịch bản mất 5 lượt viết và các đợt viết lại. Mỗi lỗi em đọc ra đều thành một cửa máy.
  - Dựng lần đầu dài 80,8 s, trượt khung; dựng lại với 10 ý thì vừa.
  - Lộ và sửa một lỗi của phòng Alpha: thẻ đổi sớm hơn lời, tới 10,5 s trong video truyện.

Sếp giao ngày 15/09: robot để sau Alpha. Alpha thử hướng *reaction/review*, vì có lẽ đơn giản
hơn tự tạo nội dung. `CLAUDE.md` §7 yêu cầu dựng hệ thống mới thì gửi kế hoạch trước. Chỗ nào
chưa chạy thử thì ghi **CHƯA ĐO**.

---

## 1. Đề xuất: làm REVIEW repo/công cụ, CHƯA làm REACTION video người khác

| | review repo / công cụ | reaction video người khác |
|---|---|---|
| nguyên liệu | số liệu GitHub, README, ảnh chụp trang công khai, phép đo trên máy mình | hình và tiếng của người khác |
| bản quyền | dữ kiện công khai cộng lời bình của mình | dùng lại hình/tiếng của người khác; video gốc có thể bị khiếu nại. **CHƯA** đọc luật từng nền tảng |
| việc khó nhất | kịch bản nói đúng sự thật | chọn đoạn, xin phép |
| AURA có sẵn | dò mạng, máy dựng video, phụ đề karaoke, Playwright | chưa có gì để cắt ghép video người khác |

Đây không phải lời khuyên pháp lý.

Vì sao review hợp với AURA:
- **Con số là dữ kiện của máy** (`CLAUDE.md` §3). Sao, commit, giấy phép lấy từ API lúc dựng
  video, không nhờ model nhớ.
- **Đỡ đúng chỗ phòng viết đang yếu.** Sếp chấm mù bộ 1 ngày 15/09 và bắt được: xưng hô đổi giữa
  chừng, câu tự mâu thuẫn ("gãy nhưng vẫn chắc chắn"), cụm cụt nghĩa, nhảy ý. Kịch bản review là
  văn trình bày; mỗi câu tựa vào một dữ kiện, nên máy đối chiếu được.
- **Khác các kênh đang có ở chỗ ĐO THẬT.** Mục 2 cho thấy số trong các video ấy đóng băng lúc quay
  rồi cũ dần, còn lời quảng cáo thì không ai kiểm.

## 2. Đo hôm nay: 8 ảnh Sếp gửi, so với số thật

Số thật lấy qua `gh api` lúc khoảng 15:00 ngày 15/09.

| trong ảnh | ảnh ghi | số thật |
|---|---|---|
| charlie947/social-media-skills | 3,4k ⭐ · 800 fork · MIT | 3.493 ⭐ · 816 fork · MIT — 17 skill viết nội dung cho Codex/Claude |
| Ashishps1/awesome-low-level-design | 26,8K ⭐ · 6,5K fork | 26.798 ⭐ · 6.497 fork · GPL-3.0 |
| zeroweight-ai/ZeroTTS | 155 ⭐ · 38 fork · MIT | 214 ⭐ · 51 fork · MIT · repo tạo 15/08, 7 commit trong 7 ngày |
| "Kokoro TTS" đọc tiếng Việt | hexgrad/Kokoro-82M · "chuẩn studio" · "0,2 s trên N100" | Danh sách giọng chính thức của Kokoro-82M: **9 ngôn ngữ, không có tiếng Việt**. Tiếng Việt là bản cộng đồng tinh chỉnh (`iamdinhthuan/Kokoro-Vietnamese` 107 ⭐; `contextboxai/Kokoro-Vietnamese` trên HF, 46.974 lượt tải). "0,2 s" **chưa ai kiểm** |
| cytostack/openwolf | chỉ có tên | 2.321 ⭐ · AGPL-3.0 · bộ nhớ dự án cho Claude Code, Codex, OpenCode |
| JustVugg/colibri | "30K+ ⭐ · 25GB RAM → 744B MoE" | 32.702 ⭐ · Apache-2.0. Kho công nghệ ghi ngày 10/08: **~0,1 token/s** (số cũ, chưa đo lại) |
| Home Assistant × Ollama | "điều khiển nhà bằng model 3B" | tích hợp chính thức của Home Assistant, không phải một repo riêng |
| livekit/agents | 12,6K ⭐ · 58 commit/7 ngày · 366 release | 14.199 ⭐ · **45** commit/7 ngày · **372** release · 496 người đóng góp |

**Trên máy, 15/09:**
- `gh api` trả đủ các số trên (sao, fork, giấy phép, commit 7 ngày, release, người đóng góp).
  Hạn mức 5.000 lượt/giờ.
- Chụp trang repo bằng Chromium sạch (không hồ sơ, không đăng nhập), khung 720×1280: 6,5–8,6 s mỗi
  trang. GitHub trả bố cục dọc, vừa khung 9:16.

## 2b. 12 video Sếp lưu trong `D:\` (tải 15/09, 14:26–14:40)

Chép lời ngay trên máy bằng faster-whisper `small`: 1.428 s âm thanh chép trong 15 phút, không
gửi gì ra ngoài. Mỗi video em xem 8 khung hình rải đều.

| kiểu | số video | ví dụ |
|---|---|---|
| soi một repo | 5 | VLX-Seek (`om-ai-lab`), Claude-Red, agent-device (callstack), bộ nhớ dùng chung cho tác tử |
| bảng xếp hạng tuần | 1 | "10 repo tăng sao nhiều nhất tuần này": +4.417 → +8.086 sao, 23 thẻ |
| so kè hai công cụ | 1 | Midjourney với Stable Diffusion |
| giảng giải bài báo | 2 | tự cải thiện đệ quy (RSI); tác tử nghiên cứu của Meta |
| hướng dẫn quy trình | 1 | 4 bước làm TVC bằng AI |
| quảng cáo sản phẩm | 2 | ghi biên bản họp; văn phòng AI |

**Khuôn kịch bản lặp lại ở nhiều video:**
1. mở bằng *"Thời đại … kết thúc rồi anh em ạ"*;
2. kể một cảnh hỏng quen thuộc;
3. lật lại: *"nhưng nghĩ lại xem, lỗi không phải tại …"*;
4. giới thiệu repo làm lời giải;
5. đưa số (sao, tuổi repo);
6. kêu gọi xem link.

Khuôn này cho model một chỗ đứng cố định, gần với cách bộ nêu đề đang làm ở phòng viết.

**Kiểu hợp với máy nhất là bảng xếp hạng.** Chỗ vướng, đo 15/09: GitHub không trả "số sao tăng
trong tuần". Máy phải tự chụp số sao **mỗi ngày** cho một danh sách repo rồi lấy hiệu. Mỗi repo
tốn 1 lượt gọi mỗi ngày, trong hạn mức 5.000 lượt/giờ. Chụp từ hôm nay thì 7 ngày nữa mới có
bảng đầu tiên.

## 3. Từ khoá Sếp đưa

"Đọc nguồn" nghĩa là em đọc README, trang chính thức hoặc số từ API ngày 15/09. **Không có mục nào
đã chạy trên máy này.**

| từ khoá | là gì | chạy trên máy này? | dùng cho Alpha? |
|---|---|---|---|
| OpenHuman (`tinyhumansai/openhuman` · 39.803 ⭐ · GPL-3.0 · beta) | khung tác tử: bộ nhớ cục bộ, điều phối, 100+ OAuth, tìm web qua Exa | CHƯA ĐO | Không. Nó là thứ để so với cả AURA, và là một đề review tốt |
| SubsVid.com | dịch vụ trả phí của Việt Nam: dịch phụ đề, lồng tiếng AI, xuất MP4/SRT, 50 credit miễn phí | web của họ | Hợp hướng reaction (dịch video tiếng Trung), nên mang theo rủi ro bản quyền của hướng ấy; video phải gửi lên máy của họ |
| Vane (`ItzCrazyKns/Vane` · 36.842 ⭐ · MIT) | máy trả lời kiểu Perplexity chạy tại nhà: SearxNG + Ollama, cài bằng Docker | CHƯA kiểm máy có Docker không | Có thể giúp khâu dò tin, nhưng AURA đã có dò mạng riêng. Chưa cần ở vòng đầu |
| OmniGet (`tonhowtf/omniget` · 12.356 ⭐ · GPL-3.0) | trình tải 1.800+ trang (yt-dlp + FFmpeg); khoá học qua phiên đăng nhập của chính mình; đọc PDF/EPUB; phụ đề; whisper.cpp | có bản Windows | Cho reaction, tải video người khác đúng là chỗ rủi ro. Máy đã có yt-dlp + ffmpeg. README ghi không bẻ DRM |
| ElevenLabs | TTS thương mại, trả phí, trả mốc thời gian từng từ | API của họ | Ứng viên giọng: tốn tiền, và kịch bản phải gửi ra ngoài. So với các TTS chạy tại máy ở vòng 1 |
| YuE2 (`multimodal-art-projection/YuE` · 8.695 ⭐ · Apache-2.0) | lời → bài hát có giọng, lập bản nhạc ký hiệu trước | **KHÔNG**: README đòi Linux và GPU NVIDIA 24 GB VRAM | Không chạy được trên máy này |
| m3e-canvas (`lnkiai/m3e-canvas` · 6.839 ⭐ · MIT · tạo 02/09) | phác màn hình Material 3 Expressive trong trình duyệt, xuất prompt vibe-coding | trang web tĩnh | Cho làm app, không cho Alpha. Là một đề review |
| Google Stitch (Google Labs) | lời hoặc ảnh phác → giao diện và mã frontend, dán sang Figma; bản mới dùng Gemini 3, có prototype | web của Google | Không cho Alpha. Là một đề review |
| chrome-devtools-mcp (`ChromeDevTools` · 52.010 ⭐ · Apache-2.0) | máy chủ MCP cho tác tử lập trình điều khiển DevTools của Chrome | có (Node) | Alpha chụp trang bằng Playwright là đủ. Hữu ích hơn cho em khi gỡ lỗi web |

**Từ các ảnh:**
- **Ứng viên giọng đọc cho vòng 1**:
  - ZeroTTS: README ghi RTF 0,5 trên CPU laptop và nhân bản giọng từ 3 s.
  - VieNeu-TTS: 2.571 ⭐. Bản v4 đóng mã; bản mở mới nhất là v3 Turbo, 48 kHz.
  - Kokoro-Vietnamese: bản cộng đồng.

  Mọi con số ở đây là của README, chưa đo trên máy này.
- **Để dành cho robot và giọng nói sau này:** LiveKit Agents, `luuquangvu/wyoming-vietnamese`
  (9 ⭐), VLX-Seek (`om-ai-lab`, 692 ⭐, mô hình thị giác chạy trên thiết bị), Home Assistant +
  Ollama.
- **Mẫu cho khâu kịch bản:** social-media-skills, trong đó `voice-builder` dựng giọng văn riêng
  từ 3–5 bài mẫu.
- **Không dùng:** `SnailSploit/Claude-Red`, bộ kỹ năng tấn công bảo mật.

## 4. Đường review đề xuất

**Máy làm, không hỏi model:**
1. **Chọn đề:** repo trong danh sách Sếp đưa (link GitHub, hoặc tên thấy trong video Sếp lưu).
2. **Dữ kiện:** qua `gh api` lấy sao, fork, giấy phép, ngôn ngữ, ngày tạo, lần đẩy mã gần nhất,
   commit 7 ngày, release, người đóng góp. Lấy lúc dựng video, và in giờ lấy lên video.
3. **Ảnh:** chụp trang repo 720×1280, cộng ảnh banner trong README.
4. **Đo thật (tuỳ đề):** chạy công cụ trên máy nếu nó nhẹ và Sếp duyệt tải, ví dụ đo RTF của một
   TTS. Không chạy được thì video nói thẳng *"chưa chạy thử"*.

**Model làm:**
5. **Kịch bản** 6–9 câu, viết từ README và dữ kiện. Cửa máy:
   - mọi con số trong kịch bản phải khớp dữ kiện;
   - mọi câu khẳng định tính năng phải tìm được chỗ tựa trong README;
   - không có câu khen hay chê nào không nguồn;
   - cửa chữ tiếng Anh và cửa nêu đề đang có vẫn áp dụng.

**Máy làm tiếp:**
6. **Thẻ hình**, theo kiểu trong ảnh: thẻ tiêu đề (tên repo, sao, giấy phép), ảnh chụp trang, 3 gạch
   đầu dòng, thẻ "đo thật", thẻ kết. Dựng bằng HTML rồi Playwright chụp lại, gần kiểu trong ảnh hơn
   là vẽ bằng PIL. **CHƯA ĐO** thời gian.
7. **Giọng:** vòng đầu dùng OneCore An, giọng đang có.
8. **Phụ đề karaoke và kiểm video:** dùng lại các cửa của phòng Alpha đang có
   (core/phong_alpha.py, core/can_chu.py).
9. **Đăng:** vòng đầu Sếp tự đăng. Đường tự đăng lên TikTok hoặc YouTube lập kế hoạch riêng, theo
   `CLAUDE.md` §2: mỗi nền tảng một đường.

## 5. Phép đo — ngưỡng đăng ký trong khối CHOT sau khi Sếp duyệt

**Vòng 0 — không tải gì.** 5 video review cho 5 repo khác nhau:
- con số trên video khớp API lúc dựng: 100%;
- câu khẳng định có chỗ tựa trong README: 100%;
- dựng xong dưới 10 phút mỗi video trên máy này;
- Sếp xem và chấm "muốn xem hết": ≥ 3/5.

**Vòng 1 — cần tải, Sếp duyệt riêng.** So giọng: OneCore An, ZeroTTS, VieNeu v3 Turbo,
Kokoro-Vietnamese. Đo ba thứ:
- RTF trên CPU máy này;
- lỗi đọc, đo bằng cách cho faster-whisper nghe lại;
- Sếp nghe mù rồi xếp hạng.

**Vòng 2:** bảng xếp hạng tuần (cần sổ chụp số sao đủ 7 ngày), thẻ động (Remotion), hàng chờ,
đường đăng.

## 6. CHƯA chặn được, và rủi ro

- **Bản quyền:** ảnh chụp trang GitHub, logo và banner trong README thuộc chủ repo. Review có bình
  luận là kiểu làm phổ biến, nhưng em **chưa kiểm** luật của từng nền tảng hay luật Việt Nam.
- **Kịch bản vẫn có thể sai nghĩa**, kiểu lỗi Sếp vừa bắt ở bộ 1 (logic, xưng hô, nhảy ý). Cửa
  máy chỉ bắt được con số và chỗ tựa, không bắt được câu viết vụng.
- **Giọng OneCore An nghe rõ là máy.** TTS tốt hơn phải tải và đo trước.
- **0 video đã đăng**, nên chưa biết người xem có thích kiểu này không.

## 7. Việc cần Sếp

1. Duyệt hướng review repo/công cụ, chưa làm reaction video người khác.
2. Chọn 5 repo cho vòng 0, hoặc để em lấy 5 trong 8 ảnh.
3. Chọn kênh đăng: TikTok hay YouTube Shorts. Vòng 0 Sếp tự đăng.
4. Duyệt tải giọng ở vòng 1. Em sẽ nêu tên, nguồn và cỡ trước.
5. Có bật sổ chụp số sao hằng ngày ngay từ bây giờ không, để 7 ngày nữa có bảng xếp hạng đầu
   tiên? Mỗi repo 1 lượt gọi API mỗi ngày, không tải gì.
