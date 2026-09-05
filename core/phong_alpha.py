# -*- coding: utf-8 -*-
"""Phòng Alpha — dựng video dọc THẬT, 100% ngoại tuyến, rồi tự nộp bằng chứng.

VÌ SAO CÓ TỆP NÀY. Đến 02/09/2026 phòng Alpha trả về đoạn văn viết sẵn::

    "🎬 [Alpha Studio Output] Đã khởi tạo kịch bản video dọc 60 giây…"
    artifacts: storyboard.json (3.4 KB) · cards_preview.png (240 KB)

Hai tệp ấy **không tồn tại**; kích thước là chữ gõ tay. Đo cả bảy phòng qua
`POST /api/dispatch`: 8 tệp được khai, **0 tệp có thật**, mỗi lượt 2–9 ms.

Đặc tả thì đã có sẵn từ trước, ở `KY_LUAT_THUC_THI.md` Chương II mục 2, và nó
đo được — nên tệp này không phát minh tiêu chuẩn nào, chỉ đi làm cho đủ:

    đầu vào    STUDIO_FIXTURE.md đã đóng băng, kèm SHA-256
    TTS        giọng OneCore MSTTS_V110_viVN_An -> voice.wav thật
    thẻ hình   ≥3 ảnh 720×1280 bằng PIL, mỗi ảnh một SHA-256
    render     FFmpeg ghép thành MP4 dọc 720×1280, dài 55–65 giây
    verifier   ffprobe (kích thước + audio không im lặng)
               blackdetect (không có khung đen liên tục > 2s)

NĂM THỨ NÓ CẦN, ĐÃ CHẠY THỬ TRƯỚC KHI VIẾT DÒNG NÀO (mục 7 luật 2)::

    Pillow            CÓ · 12.3.0
    ffmpeg / ffprobe  CÓ · 7.1
    blackdetect       CÓ    astats CÓ    silencedetect CÓ
    MSTTS_V110_viVN_An  CÓ — nhưng chỉ ở nhánh registry Speech_OneCore.
                        `System.Speech` báo "không có giọng tiếng Việt", và
                        câu ấy SAI: nó chỉ nhìn nhánh cũ. Xem tools/tts_onecore.ps1.
    STUDIO_FIXTURE.md CÓ · 1403 byte · 235 từ · 15 câu khác nhau
                        sha256 a64eb0873ec065f48a8820cb3596383502d592a68b69d90f3be47cacf910fca9

CÂU ƯỚC LƯỢNG CŨ Ở ĐÂY ĐÃ SAI 40%, và đó là gốc của mọi chuyện sau. Nguyên văn:
*"13 từ đọc hết 4,875 s, nên 154 từ ≈ 58 s"*. Ngoại suy từ **một điểm duy nhất**,
ra 2,67 từ/s. Đo lại 03/09/2026 trên năm mẫu:

    80 từ (lặp)  22,38 s      179 từ (văn)  46,38 s
   154 từ (lặp)  42,05 s      266 từ (văn)  67,30 s
   240 từ (lặp)  65,93 s

Tức 3,58–3,95 từ/s, và đề 154 từ đọc hết **41,27 s**, không phải 58 s. Không ai
phát hiện suốt một tháng vì `_dai_ngan_lai()` đệm im lặng cho đủ cửa sổ —
**15,23 s / 56,50 s (27%) của video không có giọng nói**, và mọi cửa vẫn xanh.
Đề mới 235 từ tự nó lấp đầy cửa sổ, không cần đệm.

Cùng họ với luật *"ba điểm khớp một quy luật không chứng minh được điểm thứ
tư"* — ở đây còn tệ hơn: một điểm.

> Đoạn này đã bị MẤT một lần. Ngày 03/09 tôi sửa nó trong lúc `tools/gieo.py`
> đang gieo chính tệp này ở tiến trình nền; `gieo.py` cache nội dung gốc lúc
> khởi động rồi ghi đè trả lại ở `finally`, nên bản sửa biến mất không một tiếng
> động — và dòng *"1 tệp: giống hệt TỪNG BYTE"* chính là cơ chế ấy đang báo cáo
> thành công. Nay `gieo.py` phát hiện và kêu; xem `tests/test_gieo.py`.

BA TRẠNG THÁI, không gộp: `PASS` (dựng xong và qua verifier) · `FAIL` (dựng
xong nhưng verifier bác) · `KHONG_CHAY_DUOC` (thiếu công cụ, hết giờ, TTS gãy).
Trạng thái thứ ba là thứ hay bị nuốt nhất — nuốt nó thì "chưa làm được" đội lốt
"đã làm, không đạt".
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from core.paths import PROJECT_ROOT

FIXTURE = PROJECT_ROOT / "experiments" / "evidence_sprint" / "data_inputs" / "STUDIO_FIXTURE.md"
TTS_PS1 = PROJECT_ROOT / "tools" / "tts_onecore.ps1"
GIONG = "MSTTS_V110_viVN_An"

RONG, CAO = 720, 1280
SO_THE_TOI_THIEU = 3
DAI_MIN, DAI_MAX = 55.0, 65.0
TRAN_TTS_GIAY = 180
TRAN_RENDER_GIAY = 300
# Khung đen liên tục quá ngưỡng này là hỏng, theo đặc tả.
TRAN_DEN_GIAY = 2.0

# ---- CỬA CHẤT LƯỢNG, thêm 02/09/2026 ----
#
# Bốn cửa cũ (khung · thời lượng · có tiếng · không đen) chỉ đo ĐỊNH DẠNG. Bản
# Alpha đầu tiên đỗ cả bốn, rồi đo ra:
#
#     1.455 khung · 24 fps · bitrate video 30 kb/s
#     số lần đổi cảnh   2
#     đứng yên          14,08 s · 14,12 s · 14,12 s
#
# Bốn tấm ảnh tĩnh, mỗi tấm giữ 15 giây. Một slideshow chữ qua được cả bốn cửa
# cũ. Hai ngưỡng dưới đây chép từ `KY_LUAT_THUC_THI.md` Chương II mục 2, đặt
# TRƯỚC khi sửa dây chuyền — nên chúng làm video hiện tại RỚT, và rớt là đúng.
TRAN_TINH_GIAY = 5.0
SO_DOI_CANH_TOI_THIEU = 8

# Mỗi thẻ giữ bao nhiêu giây. 60s ÷ 4,5 ≈ 13 thẻ, tức 12 lần cắt — dư trên
# ngưỡng 8. Bản đầu để 4 thẻ / 15 giây mỗi thẻ, và đó chính là thứ làm nó rớt.
GIAY_MOI_THE = 4.5
# Bước xoay màu nền giữa hai thẻ liền nhau, tính theo vòng màu.
#
# 137,5° là góc vàng — chia vòng tròn đều nhất có thể với số bước bất kỳ, nên
# hai thẻ LIỀN NHAU không bao giờ gần màu. Cần thế thật: `scdet` chấm bốn thẻ
# cũ là **0** lần đổi cảnh, vì chúng cùng gradient và chỉ khác chữ — với bộ dò
# cảnh thì cả video là một cảnh.
BUOC_MAU_DO = 137.5

# ---- CỬA PHỤ ĐỀ & NHẠC NỀN, thêm 02/09/2026 tối ----
#
# Chép từ `KY_LUAT_THUC_THI.md` Chương II mục 2. Giọng đọc một mình đo được
# −17,04 LUFS; các nền phát hành thường quanh −14 (YouTube) đến −16 (TikTok),
# nên khoảng −18…−12 vừa chứa cả hai vừa đủ rộng.
LUFS_MIN, LUFS_MAX = -18.0, -12.0
# Nhạc phải thấp hơn giọng ít nhất chừng này, đo trên hai tệp RIÊNG. LUFS của
# bản đã trộn không nói được nhạc có át giọng hay không.
CHENH_NHAC_DB = 12.0
# Chữ nung vào hình: dải dưới phải đổi mạnh, dải trên gần như không đổi.
# Đo thật trên một video 13 thẻ: dải dưới 10,37 · dải trên 0,14. Đặt 3,0 và
# 1,0 là chừa biên rộng cả hai phía.
CHENH_DAI_DUOI_MIN = 3.0
CHENH_DAI_TREN_MAX = 1.0
# Hệ số âm lượng nhạc, NUNG THẲNG VÀO TỆP chứ không áp lúc trộn.
#
# Bản đầu áp hệ số bên trong `render`, nên `_lufs(nhac)` đo tệp CHƯA hạ — tức
# là phép "chênh giọng/nhạc" so sai cặp. Đo được lúc ấy: nhạc −26,89 LUFS,
# giọng −17,04, chênh 9,85 dB; nhưng mức thật đi vào bản trộn là −26,89 − 26 =
# −52,9 dB, nhỏ tới mức không ai nghe thấy. Một con số sai che một con số sai.
#
# Nay tệp trên đĩa CHÍNH LÀ mức được dùng, nên đo nó là đo đúng thứ.
# Hiệu chuẩn: nhạc gốc −26,89 LUFS, muốn chênh ~16 dB dưới giọng (−17,04) thì
# cần hạ khoảng 7 dB -> hệ số 0,45.
HE_SO_NHAC = 0.45

# CỬA NỘI DUNG (03/09/2026). Ba ngưỡng dưới đây chép tay từ `KY_LUAT_THUC_THI.md`
# — đăng ký ở đó TRƯỚC khi có mã này.
#
# Vì sao cần. Đề đã đóng băng là MỘT CÂU LẶP 22 LẦN, và video dựng từ nó qua
# sạch mọi cửa đang có: `scdet` vẫn đếm 12 lần đổi cảnh (nền thẻ xoay góc vàng
# nên đổi màu dù chữ y hệt), `silencedetect` trên bản trộn không thấy gì (nhạc
# phủ kín 15 giây câm), `loudnorm` vẫn trong khoảng (nhạc gánh phần im). Mỗi cửa
# đo đúng phần nó đo, và không cửa nào đo NỘI DUNG.
#
#   154 từ -> đọc hết 41,27s;  15,23s / 56,50s (27%) không có giọng
#   13 khối phụ đề · 1 khối khác nhau (tỉ lệ 0,077)
TI_LE_PHU_DE_KHAC_MIN = 0.80
TI_LE_KHOI_LAP_MAX = 0.25
# Hiệu chuẩn: văn bản 13 câu KHÁC NHAU, 179 từ, cùng giọng OneCore -> 16 khoảng
# nghỉ, dài nhất 0,77s, trung bình 0,59s. 2,0s là 2,6 lần khoảng dài nhất.
QUANG_CAM_TOI_DA_GIAY = 2.0
# Dò THẤP hơn ngưỡng chấm. Đặt bằng nhau thì mọi quãng ngắn hơn bị giấu — đúng
# lỗi đã mắc với `freezedetect` (probe d bằng ngưỡng thì không thấy gì).
DO_CAM_PROBE_GIAY = 0.5
DO_CAM_NGUONG_DB = -50

# Phông phải có dấu tiếng Việt. Segoe UI có; nếu máy không có thì thử lần lượt.
PHONG_UNG_VIEN = ("segoeui.ttf", "arial.ttf", "tahoma.ttf", "calibri.ttf")


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hien_vat(p: Path, loai: str, nhan: str) -> Dict[str, Any]:
    """Một hiện vật LUÔN mang đường dẫn thật + byte thật + SHA-256 thật.

    Đây là chỗ khác nhau giữa phòng này và bản cũ: bản cũ khai `{"name": ...,
    "size": "3.4 KB"}` với kích thước gõ tay và không có đường dẫn, nên không
    ai kiểm được.
    """
    # Đường dẫn tương đối cho gọn khi nằm trong kho; ngoài kho thì để nguyên
    # tuyệt đối. Bản đầu gọi thẳng `relative_to()` và NỔ `ValueError` khi thư
    # mục ra nằm ngoài `PROJECT_ROOT` — bài test dựng vào `tmp_path` bắt được.
    try:
        duong = p.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        duong = p.as_posix()
    return {"name": p.name, "path": duong,
            "size_bytes": p.stat().st_size, "sha256": _bam(p),
            "type": loai, "kind": nhan}


def _tim_phong():
    from PIL import ImageFont
    goc = Path(r"C:\Windows\Fonts")
    for ten in PHONG_UNG_VIEN:
        d = goc / ten
        if d.is_file():
            return ImageFont.truetype(str(d), 46), ten
    return ImageFont.load_default(), "(mặc định — có thể mất dấu)"


def tach_cau(van_ban: str) -> List[str]:
    """Tách câu — dùng chung cho cả khâu chia thẻ lẫn cửa phủ kín.

    Hai bên phải tách GIỐNG HỆT nhau, nếu không cửa sẽ báo mất câu chỉ vì hai
    phép tách khác nhau, chứ không vì thật sự mất.
    """
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+", van_ban.strip()) if c.strip()]


def so_the_can_dung(dai_giong: float, van_ban: str) -> int:
    """Số thẻ cho một lượt dựng. KHÔNG BAO GIỜ nhiều hơn số câu của kịch bản.

    HÀM THUẦN, cố ý — cùng lý do với `kiem_am_thanh`/`kiem_phu_kin`: để phép
    tính này nằm trong `_dung_video` thì cửa canh chỉ khẳng định được "một lượt
    thật ra 13 thẻ", không cách nào đưa cặp (thời lượng, số câu) xấu vào.

    VÌ SAO PHẢI CHẶN TRẦN THEO SỐ CÂU (04/09/2026). `_cat_doan` đệm cho đủ thẻ
    bằng cách LẶP LẠI câu: `cau = (cau * so_the)[:so_the]`. Thiếu câu thì mấy
    thẻ cuối chiếu lại câu đầu, trong khi giọng đã đọc xong — phụ đề sai so với
    tiếng, không phải một vết xước thẩm mỹ.

    Và nó VỚI TỚI ĐƯỢC, không phải giả định. Kịch bản đúng 13 câu (sàn của đặc
    tả) với giọng ≥ 60,7 s (giữa cửa sổ 55–65 s) ra 14 thẻ:

        giọng 55,0s -> 12 thẻ · 0 khối lặp
        giọng 60,7s -> 13 thẻ · 0 khối lặp
        giọng 61,0s -> 14 thẻ · 1 khối lặp   <- chiếu lại câu 1
        giọng 65,0s -> 14 thẻ · 1 khối lặp

    Không cửa nào kêu: `kiem_lap_phu_de` chấm tỉ lệ khác nhau, 13/14 = 0,93 ≫
    0,80; `kiem_phu_kin` hỏi "có câu nào bị bỏ sót không", không hỏi "có câu nào
    bị chiếu hai lần không". Hai cửa đo hai thứ, và cái lỗ nằm giữa chúng.

    `SO_THE_TOI_THIEU` vẫn là sàn cứng: dưới 3 thẻ thì không đủ lần đổi cảnh.
    Kịch bản ít hơn 3 câu vẫn bị lặp — nhưng ở đó cửa nội dung bác thật
    (2/3 = 0,67 < 0,80), nên nó hỏng TO chứ không hỏng lặng.
    """
    theo_thoi_luong = int(round(dai_giong / GIAY_MOI_THE))
    so_cau = len(tach_cau(van_ban))
    return max(SO_THE_TOI_THIEU, min(theo_thoi_luong, so_cau))


def _cat_doan(van_ban: str, so_the: int) -> List[str]:
    """Chia kịch bản thành `so_the` đoạn, KHÔNG BỎ SÓT CÂU NÀO.

    Bản trước 04/09/2026 tính `moi = len(cau) // so_the` rồi lấy `so_the` lát
    liên tiếp, nên phần dư ở ĐUÔI rơi ra ngoài. Đo trên hàm thuần:

        17 câu / 13 thẻ  -> 13 câu lên hình, MẤT 4
        20 câu / 13 thẻ  -> 13 câu lên hình, MẤT 7
        25 câu / 13 thẻ  -> 13 câu lên hình, MẤT 12
        13 câu / 13 thẻ  -> MẤT 0   (chỉ khi chia hết mới không mất)

    Chạy thật một lượt `aura` → `alpha`: kịch bản 17 câu, giọng đọc HẾT 17,
    màn hình chỉ có 14 — và ba câu mất là ba câu KẾT. Video vẫn PASS sạch hai
    chục cửa, vì mọi cửa cũ chỉ đo phụ đề với CHÍNH NÓ (đủ dòng, khác nhau,
    không chạy quá phim), không cửa nào đối chiếu ngược lại kịch bản.

    Nay chia theo mốc `i * n // so_the`: hai mốc liền nhau khít nhau nên phủ
    đúng `[0, n)`, không chồng, không hở.
    """
    cau = tach_cau(van_ban)
    if len(cau) < so_the:
        cau = (cau * so_the)[:so_the]
    n = len(cau)
    return [" ".join(cau[i * n // so_the:(i + 1) * n // so_the]) or cau[-1]
            for i in range(so_the)]


def sinh_the_hinh(van_ban: str, thu_muc: Path, so_the: int = 4) -> List[Path]:
    """Sinh ≥3 ảnh 720×1280. Nhãn `generated_template`, mỗi ảnh một SHA-256."""
    from PIL import Image, ImageDraw

    import colorsys

    phong, _ = _tim_phong()
    ra: List[Path] = []
    doan = _cat_doan(van_ban, so_the)
    for i, chu in enumerate(doan, 1):
        # Nền chuyển màu dọc, MỖI THẺ MỘT TÔNG KHÁC HẲN.
        #
        # Bản đầu chỉ nhích `i * 12` vào kênh đỏ — mắt thấy khác chút, nhưng
        # `scdet` chấm cả bốn thẻ là MỘT cảnh (0 lần đổi). Nay xoay hẳn vòng
        # màu theo góc vàng nên hai thẻ liền nhau luôn xa nhau.
        h = ((i - 1) * BUOC_MAU_DO / 360.0) % 1.0
        anh = Image.new("RGB", (RONG, CAO))
        ve = ImageDraw.Draw(anh)
        for y in range(CAO):
            t = y / CAO
            r, g, b = colorsys.hsv_to_rgb(h, 0.62, 0.20 + 0.30 * t)
            ve.line([(0, y), (RONG, y)],
                    fill=(int(r * 255), int(g * 255), int(b * 255)))
        ve.text((48, 90), f"THẺ {i}/{len(doan)}", font=phong, fill=(235, 245, 255))
        # Ngắt dòng thủ công: PIL không tự xuống dòng.
        dong, hien = [], ""
        for tu in chu.split():
            if len(hien) + len(tu) + 1 > 26:
                dong.append(hien)
                hien = tu
            else:
                hien = (hien + " " + tu).strip()
        dong.append(hien)
        for k, d in enumerate(dong[:14]):
            ve.text((48, 220 + k * 62), d, font=phong, fill=(238, 240, 248))
        p = thu_muc / f"card_{i:02d}.png"
        anh.save(p)
        ra.append(p)
    return ra


def doc_giong(van_ban: str, thu_muc: Path) -> tuple[Path | None, str]:
    """Gọi giọng OneCore. Trả `(None, lý do)` nếu không đọc được."""
    if not TTS_PS1.is_file():
        return None, f"thiếu {TTS_PS1.name}"
    loi = thu_muc / "loi.txt"
    loi.write_text(van_ban, encoding="utf-8")
    wav = thu_muc / "voice.wav"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(TTS_PS1), "-InFile", str(loi), "-OutFile", str(wav),
             "-VoiceId", GIONG],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TRAN_TTS_GIAY)
    except subprocess.TimeoutExpired:
        return None, f"TTS quá {TRAN_TTS_GIAY}s"
    if r.returncode != 0 or not wav.is_file() or wav.stat().st_size == 0:
        return None, f"TTS hỏng: {(r.stdout or r.stderr or '').strip()[:160]}"
    return wav, ""


def _giay(tep: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(tep)],
                       capture_output=True, text=True, timeout=60)
    try:
        return float((r.stdout or "0").strip())
    except ValueError:
        return 0.0


def _dai_ngan_lai(wav: Path, dich: float) -> None:
    """Đệm im lặng cho đủ 55–65s nếu giọng đọc ngắn hơn cửa sổ.

    Chỉ ĐỆM, không bao giờ tua nhanh: đổi tốc độ giọng để lọt cửa sổ là làm
    đẹp con số chứ không làm đúng việc.
    """
    dai = _giay(wav)
    if dai >= dich:
        return
    tam = wav.with_name("voice_padded.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav),
                    "-af", f"apad=whole_dur={dich:.2f}", str(tam)],
                   capture_output=True, timeout=TRAN_RENDER_GIAY)
    if tam.is_file() and tam.stat().st_size > 0:
        tam.replace(wav)


FPS = 24


def _mmss(giay: float) -> str:
    """Mốc thời gian kiểu SRT: HH:MM:SS,mmm."""
    ms = int(round(giay * 1000))
    g, ms = divmod(ms, 1000)
    p, g = divmod(g, 60)
    h, p = divmod(p, 60)
    return f"{h:02d}:{p:02d}:{g:02d},{ms:03d}"


def lam_phu_de(doan: List[str], moi_the: float, dich: Path) -> Path:
    """Một dòng phụ đề cho mỗi thẻ, khớp đúng khoảng thẻ ấy trên màn hình.

    Viết ra tệp `.srt` RIÊNG chứ không nung chữ vào khung hình: nung vào thì
    không ai kiểm được bằng máy, còn luồng phụ đề thì `ffprobe` đọc ra.
    """
    khoi = []
    for i, chu in enumerate(doan, 1):
        bd, kt = (i - 1) * moi_the, i * moi_the
        khoi.append(f"{i}\n{_mmss(bd)} --> {_mmss(kt)}\n{chu.strip()}\n")
    dich.write_text("\n".join(khoi), encoding="utf-8", newline="\n")
    return dich


def lam_nhac_nen(dai: float, dich: Path) -> tuple[Path | None, str]:
    """Sinh nền âm bằng ffmpeg — KHÔNG phải nhạc thật, và không được khai thế.

    Ba nốt ngân chồng nhau (A3–C#4–E4) cộng một lớp nhiễu rất nhỏ, vào/ra êm.
    Nhãn `generated_tone_bed`. Máy này không có tệp nhạc nào có bản quyền rõ
    ràng, nên tự sinh là lối duy nhất giữ được lời hứa "100% ngoại tuyến".
    """
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=220:duration={dai:.2f}",
         "-f", "lavfi", "-i", f"sine=frequency=277:duration={dai:.2f}",
         "-f", "lavfi", "-i", f"sine=frequency=330:duration={dai:.2f}",
         "-filter_complex",
         "[0:a][1:a][2:a]amix=inputs=3:duration=first,"
         f"afade=t=in:st=0:d=2,afade=t=out:st={max(0.0, dai - 2):.2f}:d=2,"
         f"volume={HE_SO_NHAC},"
         "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono[a]",
         "-map", "[a]", str(dich)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=TRAN_RENDER_GIAY)
    if r.returncode != 0 or not dich.is_file() or dich.stat().st_size == 0:
        return None, f"không sinh được nền nhạc: {(r.stderr or '').strip()[:160]}"
    return dich, ""


def chenh_dai_phu_de(a: Path, b: Path, giay: float = 20.0) -> Dict[str, float]:
    """So một khung của HAI video: dải dưới phải đổi, dải trên thì không.

    Cách duy nhất máy đọc được chữ đã nung vào hình mà không cần OCR: lấy cùng
    một mốc thời gian ở hai bản, rồi hỏi *chỗ nào đổi*. Chữ nằm ở đáy khung nên
    dải dưới đổi mạnh; nếu dải TRÊN cũng đổi thì thứ vừa thêm không phải phụ đề
    (mã hoá lại lệch màu, hay lọc nhầm cả khung).
    """
    from PIL import Image, ImageChops, ImageStat

    ra: Dict[str, float] = {}
    tam = a.parent / "_khung_so"
    tam.mkdir(exist_ok=True)
    khung = []
    for i, v in enumerate((a, b)):
        p = tam / f"k{i}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{giay:.2f}",
                        "-i", str(v), "-frames:v", "1", str(p)],
                       capture_output=True, timeout=180)
        if not p.is_file():
            return {"dai_duoi": -1.0, "dai_tren": -1.0}
        khung.append(Image.open(p).convert("L"))
    w, h = khung[0].size
    for nhan, hop in (("dai_duoi", (0, int(h * 0.7), w, h)),
                      ("dai_tren", (0, 0, w, int(h * 0.3)))):
        d = ImageChops.difference(khung[0].crop(hop), khung[1].crop(hop))
        ra[nhan] = round(ImageStat.Stat(d).mean[0], 2)
    for k in khung:
        k.close()
    shutil.rmtree(tam, ignore_errors=True)
    return ra


def kiem_nung(cd: Dict[str, float]) -> List[str]:
    """Chấm hai con số của phép nung. Trả về lý do BÁC; rỗng nghĩa là đạt.

    Tách ra thành hàm thuần vì cùng lý do với `kiem_am_thanh`: để nằm rải trong
    `dung_video` thì cửa canh chỉ khẳng định được "số đo nằm trong khoảng",
    không cách nào đưa số XẤU vào. Gieo lỗi bắt đúng chỗ ấy — bỏ hẳn hai nhánh
    chấm mà cửa vẫn xanh.
    """
    ra: List[str] = []
    if cd.get("dai_duoi", -1.0) < 0 or cd.get("dai_tren", -1.0) < 0:
        return ["không rút được khung để đối chiếu bản nung"]
    if cd["dai_duoi"] < CHENH_DAI_DUOI_MIN:
        ra.append(f"dải dưới chỉ chênh {cd['dai_duoi']}, cần ≥ "
                  f"{CHENH_DAI_DUOI_MIN} — chữ chưa nung vào hình")
    if cd["dai_tren"] > CHENH_DAI_TREN_MAX:
        ra.append(f"dải trên chênh {cd['dai_tren']}, cần ≤ "
                  f"{CHENH_DAI_TREN_MAX} — thứ vừa thêm không nằm ở chỗ phụ đề")
    return ra


def kiem_am_thanh(lufs_giong: float | None, lufs_nhac: float | None,
                  lufs_video: float | None) -> List[str]:
    """Chấm ba con số độ ồn. Trả về danh sách lý do BÁC; rỗng nghĩa là đạt.

    TÁCH RA THÀNH HÀM THUẦN LÀ CÓ CHỦ ĐÍCH. Bản đầu để ba phép này nằm rải
    trong `dung_video`, nên cửa canh chỉ khẳng định được "số đo nằm trong
    khoảng" — không cách nào đưa số XẤU vào để xem verifier có bác không. Gieo
    lỗi bắt đúng chỗ ấy: bỏ hẳn hai nhánh chấm mà cửa vẫn xanh, hai lần.
    """
    ra: List[str] = []
    if lufs_video is None:
        ra.append("không đo được độ ồn của video")
    elif not (LUFS_MIN <= lufs_video <= LUFS_MAX):
        ra.append(f"độ ồn {lufs_video:.1f} LUFS, cần {LUFS_MIN:.0f}…{LUFS_MAX:.0f}")
    if lufs_giong is None or lufs_nhac is None:
        ra.append("không đo được độ ồn giọng hoặc nhạc")
    else:
        chenh = lufs_giong - lufs_nhac
        if chenh < CHENH_NHAC_DB:
            ra.append(f"nhạc chỉ thấp hơn giọng {chenh:.1f} dB, "
                      f"cần ≥ {CHENH_NHAC_DB:.0f} — nhạc đang át lời")
    return ra


def _lufs(tep: Path) -> float | None:
    """Độ ồn tích hợp, theo `loudnorm`. `None` nếu không đo được."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(tep),
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    m = re.search(r'"input_i"\s*:\s*"(-?[\d.]+|-inf)"', r.stderr or "")
    if not m or m.group(1) == "-inf":
        return None
    return float(m.group(1))


def render(cards: List[Path], wav: Path, ra: Path,
           srt: Path | None = None, nhac: Path | None = None) -> tuple[bool, str]:
    """Ghép thẻ + giọng thành MP4, mỗi thẻ có chuyển động chậm (Ken Burns).

    VÌ SAO KHÔNG DÙNG `concat` ẢNH TĨNH NỮA. Bản đầu ghép thẳng ảnh, ra video
    đứng yên 14,1 giây mỗi thẻ và bitrate video **30 kb/s** — bốn tấm ảnh chứ
    không phải video. `freezedetect` bắt đúng.

    `zoompan` phóng rất chậm (1,00 -> 1,12 trong suốt một thẻ) nên KHÔNG khung
    nào trùng khung trước, mà mắt vẫn thấy tĩnh tại. Cắt giữa các thẻ vẫn là
    cắt cứng — đó là thứ `scdet` đếm được; `xfade` chuyển mượt thì nó lại không
    tính là đổi cảnh.
    """
    dai = _giay(wav)
    if dai <= 0:
        return False, "không đọc được thời lượng voice.wav"
    moi_the = dai / len(cards)
    khung_moi_the = max(2, int(round(moi_the * FPS)))

    lenh: List[str] = ["ffmpeg", "-v", "error", "-y"]
    for c in cards:
        # `-framerate FPS` để đầu vào TỰ sinh đủ khung; zoompan chỉ việc đi qua
        # từng khung một (`d=1`).
        lenh += ["-loop", "1", "-framerate", str(FPS),
                 "-t", f"{moi_the:.4f}", "-i", str(c)]
    lenh += ["-i", str(wav)]

    # `d=1`, KHÔNG phải `d=khung_moi_the`.
    #
    # Bản đầu để `d=khung_moi_the` cùng với `-loop 1`: mỗi khung VÀO sinh ra
    # `d` khung RA, mà `on` thì đếm dồn trên toàn bộ khung đã xuất — nên mức
    # phóng cộng dồn khủng khiếp. Đo được: ở giây 45 nhãn "THẺ i/13" đã trôi
    # hẳn khỏi khung, chênh lệch giữa các khung trong video chỉ còn 0,5–5,6
    # trong khi các thẻ gốc chênh nhau 5–17. Tức là video gần như chỉ có một
    # hai thẻ đầu, phóng to dần.
    #
    # `min(...)` chặn trần: dù tính sai vẫn không phóng quá 1,12.
    buoc = 0.12 / khung_moi_the
    doan = "".join(
        f"[{i}:v]zoompan=z='min(1+{buoc:.6f}*on,1.12)':d=1"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":s={RONG}x{CAO}:fps={FPS},setsar=1[v{i}];"
        for i in range(len(cards)))
    doan += "".join(f"[v{i}]" for i in range(len(cards)))
    doan += f"concat=n={len(cards)}:v=1:a=0[vout]"

    i_giong = len(cards)
    map_am = f"{i_giong}:a"
    if nhac is not None and nhac.is_file():
        # Hạ nhạc rồi mới trộn. `duration=first` để nền dài hơn cũng bị cắt theo
        # giọng, khỏi kéo dài video quá cửa sổ 55–65 giây.
        lenh += ["-i", str(nhac)]
        # `normalize=0` — BẮT BUỘC. Mặc định `amix` chia âm lượng cho số đầu
        # vào, nên trộn hai luồng là giọng tụt 6 dB. Đo được: bản trộn ra
        # −23,05 LUFS trong khi giọng gốc là −17,04, và cửa độ ồn bác đúng.
        doan += (f";[{i_giong}:a][{i_giong + 1}:a]amix=inputs=2:duration=first"
                 ":dropout_transition=0:normalize=0[aout]")
        map_am = "[aout]"

    lenh += ["-filter_complex", doan, "-map", "[vout]", "-map", map_am,
             "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "96k", "-shortest", str(ra)]
    r = subprocess.run(lenh, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=TRAN_RENDER_GIAY)
    if r.returncode != 0 or not ra.is_file():
        return False, f"ffmpeg: {(r.stderr or '').strip()[:200]}"

    # ---- NUNG CHỮ VÀO HÌNH ----
    #
    # Luồng phụ đề rời thì `ffprobe` đọc được — nên nó ĐO được — nhưng trên
    # Facebook/TikTok người ta lướt và xem TẮT TIẾNG, mà luồng rời thường không
    # tự bật. Chữ nung vào hình thì luôn thấy, nhưng máy không đọc ra được.
    # Giữ cả hai: luồng rời để KIỂM, chữ nung để XEM.
    #
    # `subtitles` cần đường dẫn KHÔNG có dấu `:` của ổ đĩa Windows, nên chạy
    # ffmpeg ngay trong thư mục chứa tệp và chỉ truyền TÊN.
    if srt is not None and srt.is_file():
        # GIỮ LẠI BẢN CHƯA NUNG. Không có nó thì không cách nào chứng minh chữ
        # đã vào hình — máy không đọc được chữ trên khung, chỉ so được hai
        # khung với nhau.
        shutil.copy(ra, ra.with_name("video_chua_nung.mp4"))
        nung = ra.with_name("_nung_" + ra.name)
        kieu = ("FontName=Segoe UI,FontSize=20,PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H90000000,BorderStyle=3,Outline=2,"
                "Alignment=2,MarginV=60")
        r3 = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", ra.name,
             "-vf", f"subtitles={srt.name}:force_style='{kieu}'",
             "-c:a", "copy", nung.name],
            cwd=str(ra.parent), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=TRAN_RENDER_GIAY)
        if r3.returncode != 0 or not nung.is_file():
            return False, f"nung phụ đề hỏng: {(r3.stderr or '').strip()[:200]}"
        nung.replace(ra)

    # Phụ đề ghép ở LƯỢT RIÊNG, `-c copy`, không mã hoá lại.
    #
    # Nhét thêm một đầu vào vào chính `filter_complex` ở trên thì phải tự đếm
    # chỉ số đầu vào — và bản đầu của tôi đếm sai, gọi một hàm không tồn tại.
    # Tách ra thì chỉ số hết ý nghĩa, và video không bị nén lại lần hai.
    if srt is not None and srt.is_file():
        tam = ra.with_name("_" + ra.name)
        r2 = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(ra), "-i", str(srt),
             "-c", "copy", "-c:s", "mov_text",
             "-metadata:s:s:0", "language=vie", str(tam)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TRAN_RENDER_GIAY)
        if r2.returncode != 0 or not tam.is_file():
            return False, f"ghép phụ đề hỏng: {(r2.stderr or '').strip()[:200]}"
        tam.replace(ra)
    return True, ""


def kiem_video(mp4: Path) -> Dict[str, Any]:
    """Verifier ĐỘC LẬP với bước dựng — nó chỉ nhìn tệp trên đĩa.

    `KY_LUAT_THUC_THI.md` Chương I: *"Worker không được tự chấm PASS."*
    """
    kq: Dict[str, Any] = {"dat": False, "vi_sao": [], "so": {}}
    if not mp4.is_file() or mp4.stat().st_size == 0:
        kq["vi_sao"].append("không có tệp mp4")
        return kq

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,width,height", "-show_entries", "format=duration",
         "-of", "json", str(mp4)], capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout or "{}")
    except ValueError:
        kq["vi_sao"].append("ffprobe không trả JSON đọc được")
        return kq

    luong = d.get("streams", [])
    v = next((s for s in luong if s.get("codec_type") == "video"), None)
    a = next((s for s in luong if s.get("codec_type") == "audio"), None)
    dai = float(d.get("format", {}).get("duration") or 0)
    kq["so"] = {"rong": (v or {}).get("width"), "cao": (v or {}).get("height"),
                "giay": round(dai, 2), "co_audio": a is not None}

    if not v:
        kq["vi_sao"].append("không có luồng video")
    elif (v.get("width"), v.get("height")) != (RONG, CAO):
        kq["vi_sao"].append(f"khung {v.get('width')}×{v.get('height')}, cần {RONG}×{CAO}")
    if not a:
        kq["vi_sao"].append("không có luồng audio")
    if not (DAI_MIN <= dai <= DAI_MAX):
        kq["vi_sao"].append(f"dài {dai:.1f}s, cần {DAI_MIN:.0f}–{DAI_MAX:.0f}s")

    # audio có tiếng thật không — không chấp nhận một luồng im lặng
    r2 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "astats",
                         "-f", "null", "-"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=120)
    m = re.search(r"Peak level dB:\s*(-?[\d.]+|-inf)", r2.stderr or "")
    dinh = m.group(1) if m else None
    kq["so"]["peak_db"] = dinh
    if dinh is None or dinh == "-inf" or float(dinh) < -60:
        kq["vi_sao"].append(f"audio im lặng (peak {dinh})")

    # khung đen liên tục
    r3 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4),
                         "-vf", f"blackdetect=d={TRAN_DEN_GIAY}:pic_th=0.98",
                         "-an", "-f", "null", "-"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=180)
    den = re.findall(r"black_duration:(\d+\.?\d*)", r3.stderr or "")
    kq["so"]["doan_den"] = len(den)
    if den:
        kq["vi_sao"].append(f"{len(den)} đoạn đen ≥ {TRAN_DEN_GIAY}s")

    # ---- cửa CHẤT LƯỢNG ----
    # Đứng yên quá lâu: `freezedetect` báo từng đoạn kèm thời lượng.
    # ĐẦU DÒ ĐẶT Ở 1 GIÂY, KHÔNG PHẢI Ở NGƯỠNG CHẤM 5 GIÂY.
    #
    # `freezedetect=d=X` chỉ báo những đoạn dài TỪ X trở lên. Đặt đầu dò đúng
    # bằng ngưỡng chấm thì mọi đoạn ngắn hơn biến mất khỏi phép đo — và gieo
    # lỗi bắt được đúng chuyện đó: bỏ hẳn `zoompan` (thẻ đứng im hoàn toàn) mà
    # cửa vẫn xanh, vì mỗi thẻ chỉ 4,33 s, dưới 5 s.
    #
    # Nay đo từ 1 s trở lên; luật chấm vẫn là `> TRAN_TINH_GIAY`. Nhờ vậy con số
    # phân biệt được "có chuyển động thật" (0,0 s) với "tĩnh nhưng cắt vụn"
    # (4,33 s) — hai thứ mà ngưỡng 5 giây một mình gộp làm một.
    DAU_DO_TINH_GIAY = 1.0
    r4 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4),
                         "-vf", f"freezedetect=n=-60dB:d={DAU_DO_TINH_GIAY}",
                         "-an", "-f", "null", "-"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=180)
    #
    # CHỖ NÀY TỪNG ĐỂ LỌT CA TỆ NHẤT. `freezedetect` chỉ in `freeze_duration`
    # khi một đoạn đứng yên KẾT THÚC. Video đứng yên suốt từ đầu tới cuối thì
    # đoạn ấy không bao giờ kết thúc — đo được: một video xanh trơn 60 s /
    # 1.500 khung cho **0** dòng `freeze_duration`, trong khi slideshow của
    # Alpha (có đổi thẻ) cho 3 dòng. Nên chỉ đếm `freeze_duration` là bỏ sót
    # đúng thứ tĩnh nhất.
    #
    # Sửa: đọc cả `freeze_start`; đoạn nào mở mà không đóng thì tính dài tới
    # hết video.
    tinh = [float(x) for x in
            re.findall(r"freeze_duration:\s*([\d.]+)", r4.stderr or "")]
    mo = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", r4.stderr or "")]
    dong_lai = re.findall(r"freeze_end:\s*([\d.]+)", r4.stderr or "")
    if len(mo) > len(dong_lai) and dai > 0:
        tinh.append(round(dai - mo[-1], 2))
    kq["so"]["dung_yen_lau_nhat"] = round(max(tinh), 2) if tinh else 0.0
    kq["so"]["so_doan_tinh"] = len(tinh)
    qua_tran = [x for x in tinh if x > TRAN_TINH_GIAY]
    if qua_tran:
        kq["vi_sao"].append(
            f"{len(qua_tran)} đoạn đứng yên > {TRAN_TINH_GIAY:.0f}s "
            f"(lâu nhất {max(qua_tran):.1f}s)")

    # Đổi cảnh: đếm bằng `scdet`, KHÔNG bằng `select='gt(scene,…)',showinfo`.
    #
    # Bản đầu dùng `select+showinfo` và luôn ra **0**, kể cả trên một video cắt
    # cảnh liên tục — `showinfo` chỉ in hai dòng cấu hình, không in dòng nào cho
    # khung được chọn. Đếm bằng `grep -c showinfo` thì ra 2, và tôi suýt nhận
    # con số ấy làm "2 lần đổi cảnh". Nó là 2 dòng cấu hình.
    #
    # Hiệu chuẩn bằng ca đối chứng — video 8 màu khác hẳn nhau, tức 7 lần cắt:
    #
    #     scdet threshold=3 · 6 · 10 · 14   ->  đếm được 6, ổn định
    #     slideshow 4 thẻ của Alpha         ->  đếm được 0
    #
    # Lệch 1 so với số cắt thật (khung đầu không tính là một lần đổi). Còn số 0
    # của Alpha thì đúng chứ không phải máy đo mù: bốn thẻ cùng gradient, cùng
    # bố cục, chỉ khác chữ — với bộ dò cảnh thì cả video là MỘT cảnh.
    # NGƯỠNG NHẠY CỦA MÁY ĐO, khác hẳn ngưỡng CHẤM (`SO_DOI_CANH_TOI_THIEU`).
    # Cái này nói "thế nào thì tính là một lần đổi cảnh"; cái kia nói "bao nhiêu
    # lần thì đủ". Lẫn hai thứ là chỉnh cân theo đáp án.
    #
    # Con số 10 ở bản đầu do tôi chọn mà KHÔNG đo. Hiệu chuẩn lại trên ba video
    # đã biết trước số cắt:
    #
    #     video                    th=1  th=2  th=3  th=5  th=10   cắt THẬT
    #     13 thẻ, có zoom            12    12    12    10     2       12
    #     8 màu cắt cứng              6     6     6     6     6        7
    #     xanh trơn 60s (tĩnh)        0     0     0     0     0        0
    #
    # Ngưỡng 1–3 cho kết quả y hệt nhau — một mặt bằng ổn định — và KHÔNG có
    # dương tính giả nào dù video đang zoom liên tục (nhiễu < 1). Cắt yếu nhất
    # đo được là 3,62. Chọn 3: giữa mặt bằng, trên sàn nhiễu, dưới cắt yếu nhất.
    r5 = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "debug",
                         "-i", str(mp4), "-vf", "scdet=threshold=3",
                         "-an", "-f", "null", "-"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=180)
    doi_canh = len(re.findall(r"lavfi\.scd\.time", r5.stderr or ""))
    kq["so"]["doi_canh"] = doi_canh
    if doi_canh < SO_DOI_CANH_TOI_THIEU:
        kq["vi_sao"].append(
            f"chỉ {doi_canh} lần đổi cảnh, cần ≥ {SO_DOI_CANH_TOI_THIEU} "
            "— video đang là slideshow")

    # ---- cửa PHỤ ĐỀ: có luồng hay không ----
    r6 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type",
         "-of", "json", str(mp4)], capture_output=True, text=True, timeout=60)
    try:
        luong6 = json.loads(r6.stdout or "{}").get("streams", [])
    except ValueError:
        luong6 = []
    co_phu_de = any(x.get("codec_type") == "subtitle" for x in luong6)
    kq["so"]["co_phu_de"] = co_phu_de
    if not co_phu_de:
        kq["vi_sao"].append("không có luồng phụ đề")

    kq["dat"] = not kq["vi_sao"]
    return kq


def khoi_phu_de(noi_dung: str) -> List[str]:
    """Rút phần CHỮ của từng khối .srt (bỏ số thứ tự và dòng mốc thời gian)."""
    ra: List[str] = []
    for khoi in re.split(r"\n\s*\n", noi_dung.strip()):
        dong = [d.strip() for d in khoi.strip().splitlines() if d.strip()]
        chu = [d for d in dong
               if not d.isdigit() and "-->" not in d]
        if chu:
            ra.append(" ".join(chu))
    return ra


def kiem_lap_phu_de(khoi: List[str]) -> List[str]:
    """Chấm độ lặp của phụ đề. Trả lý do BÁC; rỗng nghĩa là đạt.

    Hàm THUẦN, cùng lý do với `kiem_nung` và `kiem_am_thanh`: để phép chấm nằm
    rải trong dây chuyền thì cửa canh chỉ khẳng định được "số đo nằm trong
    khoảng" trên một lượt ĐẠT, không cách nào đưa số XẤU vào.
    """
    if not khoi:
        return ["không có khối phụ đề nào để chấm"]
    ti_le_khac = len(set(khoi)) / len(khoi)
    lap_nhieu_nhat = max(khoi.count(k) for k in set(khoi)) / len(khoi)
    ra: List[str] = []
    if ti_le_khac < TI_LE_PHU_DE_KHAC_MIN:
        ra.append(f"chỉ {len(set(khoi))}/{len(khoi)} khối phụ đề khác nhau "
                  f"(tỉ lệ {ti_le_khac:.3f}), cần ≥ {TI_LE_PHU_DE_KHAC_MIN}")
    if lap_nhieu_nhat > TI_LE_KHOI_LAP_MAX:
        ra.append(f"một khối chiếm {lap_nhieu_nhat:.3f} tổng số khối, cần ≤ "
                  f"{TI_LE_KHOI_LAP_MAX}")
    return ra


def kiem_phu_kin(van_ban: str, khoi: List[str]) -> List[str]:
    """Mọi câu của kịch bản phải có mặt trong phụ đề. Trả lý do BÁC; rỗng là đạt.

    KHÔNG có ngưỡng phần trăm: mất một câu là hỏng. Đặc tả ở
    `KY_LUAT_THUC_THI.md`, mục "Cửa PHỦ KÍN KỊCH BẢN".

    Hàm thuần, cùng lý do với `kiem_am_thanh`/`kiem_nung`: để phép chấm nằm rải
    trong `_dung_video` thì cửa canh không cách nào đưa ca XẤU vào — đã mắc bốn
    lần trong chính tệp này.

    So bằng `in` là CÓ CHỦ ĐÍCH ở đây, và an toàn theo một nghĩa hẹp: vế trái là
    NGUYÊN một câu đã tách (có dấu chấm), vế phải là toàn bộ chữ trên phụ đề nối
    lại. Đây không phải bệnh `x in y` của việc dò chuỗi con — chỗ ấy nguy vì `x`
    là mảnh vụn ("ai" lọt giữa "thứ hai"); ở đây `x` là một câu trọn vẹn, và cái
    ta hỏi đúng là "câu này có nằm trên màn hình không".
    """
    cau = tach_cau(van_ban)
    if not cau:
        return ["không tách được câu nào từ kịch bản"]
    tren_man = " ".join(khoi)
    mat = [c for c in cau if c not in tren_man]
    if mat:
        return [f"{len(mat)}/{len(cau)} câu của kịch bản KHÔNG lên màn hình — "
                f"giọng đọc hết mà phụ đề thiếu; câu đầu bị mất: {mat[0][:60]!r}"]
    return []


def _quang_cam_dai_nhat(wav: Path) -> float:
    """Quãng KHÔNG CÓ GIỌNG dài nhất trong tệp, tính bằng giây.

    Trả `-1.0` nếu không đo được — không gộp vào 0.0, vì 0.0 đọc ra thành
    "đo rồi, không có quãng nào".
    """
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(wav), "-af",
         f"silencedetect=noise={DO_CAM_NGUONG_DB}dB:d={DO_CAM_PROBE_GIAY}",
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=TRAN_RENDER_GIAY)
    if r.returncode != 0:
        return -1.0
    quang = [float(m) for m in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
    return max(quang) if quang else 0.0


def kiem_quang_cam(giay: float) -> List[str]:
    """Chấm quãng không có giọng. Trả lý do BÁC; rỗng nghĩa là đạt."""
    if giay < 0:
        return ["không đo được quãng câm trong giọng đọc"]
    if giay > QUANG_CAM_TOI_DA_GIAY:
        return [f"quãng không có giọng dài {giay:.2f}s, cần ≤ "
                f"{QUANG_CAM_TOI_DA_GIAY}s — kịch bản ngắn hơn cửa sổ video"]
    return []


def kiem_phu_de(srt: Path, so_the: int, dai_video: float) -> Dict[str, Any]:
    """Phụ đề phải đủ dòng và không chạy quá phim.

    Tách khỏi `kiem_video` vì nó cần biết SỐ THẺ và thời lượng, hai thứ chỉ dây
    chuyền mới có. `kiem_video` thì chỉ được nhìn tệp mp4, không hơn — verifier
    nhìn thêm thứ khác là verifier bớt độc lập đi.
    """
    kq: Dict[str, Any] = {"dat": False, "vi_sao": [], "so": {}}
    if not srt.is_file():
        kq["vi_sao"].append("không có tệp .srt")
        return kq
    moc = re.findall(
        r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)",
        srt.read_text(encoding="utf-8"))
    kq["so"]["so_dong"] = len(moc)
    if not moc:
        kq["vi_sao"].append("tệp .srt không có dòng nào")
        return kq
    h, ph, g, ms = moc[-1][4:]
    ket = int(h) * 3600 + int(ph) * 60 + int(g) + int(ms) / 1000
    kq["so"]["ket_dong_cuoi"] = round(ket, 3)
    if len(moc) < so_the:
        kq["vi_sao"].append(f"{len(moc)} dòng phụ đề, cần ≥ {so_the} (số thẻ)")
    if ket > dai_video + 0.25:
        kq["vi_sao"].append(
            f"dòng cuối kết ở {ket:.2f}s nhưng video chỉ dài {dai_video:.2f}s")
    kq["dat"] = not kq["vi_sao"]
    return kq


# Giữ lại bao nhiêu lượt dựng. Mỗi lượt để lại ~2,5 MB (voice.wav 1,8 MB +
# 4 thẻ + mp4), và `/api/dispatch` quét cả `data/` HAI LẦN mỗi lượt để đếm bằng
# chứng — nên thư mục này phình thì mọi phòng khác cùng chậm theo. Đo 02/09:
# 5 lượt = 13 MB.
SO_LUOT_GIU = 5


def _don_luot_cu(goc: Path) -> int:
    """Xoá bớt lượt cũ, giữ `SO_LUOT_GIU` lượt mới nhất. Trả số thư mục đã xoá."""
    if not goc.is_dir():
        return 0
    luot = sorted((d for d in goc.iterdir() if d.is_dir()),
                  key=lambda d: d.stat().st_mtime, reverse=True)
    xoa = 0
    for d in luot[SO_LUOT_GIU:]:
        shutil.rmtree(d, ignore_errors=True)
        xoa += not d.exists()
    return xoa


def dung_video(thu_muc_ra: Path, van_ban: str | None = None) -> Dict[str, Any]:
    """Chạy cả dây chuyền. Trả về `{trang_thai, artifacts, kiem, ms, vi_sao}`.

    HẾT GIỜ LÀ `KHONG_CHAY_DUOC`, KHÔNG PHẢI NGOẠI LỆ (thêm 04/09/2026).

    Tệp này có 16 lệnh con mang trần thời gian cứng (60–300 s) mà chỉ MỘT chỗ
    bắt `TimeoutExpired` — `doc_giong`. Mười lăm chỗ còn lại, dưới tải nặng, ném
    ngoại lệ thẳng ra ngoài: bài test đỏ với một traceback, đọc y hệt "dây chuyền
    hỏng" trong khi thật ra là "máy bận, chưa đo được".

    Đó chính là ba trạng thái bị gộp còn hai, ở chỗ khó thấy nhất.

    CHƯA CHỨNG MINH ĐƯỢC đây là nguyên nhân của mẫu chập chờn cả ngày 03/09::

        >= 15 phút  ->  ĐỎ    (30:37 · 19:17 · 16:49 · 15:14)
        <  12 phút  ->  XANH  (11:11 · 6:38 · 6:14 · 5:24 · 5:16 · 3:54 · 3:45)

    Không lượt nào phá mẫu, nhưng tôi chưa bắt được ngoại lệ tận tay — bốn lần
    thử tái hiện đều xanh. Bản vá này đúng bất kể nguyên nhân là gì, và nó làm
    lần sau TỰ KHAI: thay vì một traceback, sổ sẽ ghi rõ lệnh nào hết giờ.
    """
    t0 = time.monotonic()
    try:
        return _dung_video(thu_muc_ra, van_ban, t0)
    except subprocess.TimeoutExpired as e:
        lenh = e.cmd[0] if isinstance(e.cmd, (list, tuple)) and e.cmd else str(e.cmd)
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "kiem": {},
                "ms": round((time.monotonic() - t0) * 1000, 1),
                "vi_sao": f"hết giờ: `{lenh}` quá {e.timeout}s "
                          f"(máy bận — chưa đo được, không phải dây chuyền hỏng)"}


def _dung_video(thu_muc_ra: Path, van_ban: str | None, t0: float) -> Dict[str, Any]:
    _don_luot_cu(thu_muc_ra.parent)
    thieu = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    try:
        import PIL  # noqa: F401
    except ImportError:
        thieu.append("Pillow")
    if thieu:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "kiem": {},
                "ms": 0, "vi_sao": "thiếu công cụ: " + ", ".join(thieu)}

    if van_ban is None:
        if not FIXTURE.is_file():
            return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "kiem": {},
                    "ms": 0, "vi_sao": f"thiếu đề đã đóng băng {FIXTURE.name}"}
        van_ban = FIXTURE.read_text(encoding="utf-8").strip()

    thu_muc_ra.mkdir(parents=True, exist_ok=True)
    hien_vat: List[Dict[str, Any]] = []

    wav, ly_do = doc_giong(van_ban, thu_muc_ra)
    if wav is None:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": [], "kiem": {},
                "ms": round((time.monotonic() - t0) * 1000, 1), "vi_sao": ly_do}
    _dai_ngan_lai(wav, DAI_MIN + 1.5)
    hien_vat.append(_hien_vat(wav, "AUDIO", "tts_onecore"))

    # `max(SO_THE_TOI_THIEU, 4)` ở bản đầu làm hằng số này thành CHẾT: hạ nó
    # xuống 2 mà số thẻ vẫn là 4. Gieo lỗi phát hiện — cửa canh xanh vì phép
    # gieo không đổi được hành vi, chứ không phải vì cửa mù.
    # Số thẻ theo THỜI LƯỢNG, không phải một con số cố định: mỗi thẻ ~4,5 giây
    # thì 60 giây ra ~13 thẻ / 12 lần cắt, dư trên ngưỡng 8 lần đổi cảnh.
    # Và chặn trần theo SỐ CÂU — xem `so_the_can_dung`, thiếu câu thì thẻ cuối
    # chiếu lại câu đầu mà không cửa nào kêu.
    so_the = so_the_can_dung(_giay(wav), van_ban)
    cards = sinh_the_hinh(van_ban, thu_muc_ra, so_the=so_the)
    hien_vat += [_hien_vat(c, "IMAGE", "generated_template") for c in cards]

    # Phụ đề: một dòng cho mỗi thẻ, khớp đúng khoảng thẻ ấy trên màn hình.
    dai_giong = _giay(wav)
    srt = lam_phu_de(_cat_doan(van_ban, len(cards)),
                     dai_giong / len(cards), thu_muc_ra / "phu_de.srt")
    hien_vat.append(_hien_vat(srt, "SUBTITLE", "srt_theo_the"))

    # Nhạc nền SINH BẰNG MÁY, không phải nhạc thật.
    nhac, ly_do_nhac = lam_nhac_nen(dai_giong, thu_muc_ra / "nhac_nen.wav")
    if nhac is not None:
        hien_vat.append(_hien_vat(nhac, "AUDIO", "generated_tone_bed"))

    mp4 = thu_muc_ra / "video.mp4"
    ok, loi = render(cards, wav, mp4, srt=srt, nhac=nhac)
    if not ok:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hien_vat, "kiem": {},
                "ms": round((time.monotonic() - t0) * 1000, 1), "vi_sao": loi}
    hien_vat.append(_hien_vat(mp4, "VIDEO", "rendered"))

    # Chênh lệch giọng / nhạc phải đo trên HAI TỆP RIÊNG, trước khi trộn.
    # LUFS của bản đã trộn không nói được nhạc có át giọng hay không.
    lufs_giong, lufs_nhac = _lufs(wav), (_lufs(nhac) if nhac else None)
    kiem = kiem_video(mp4)
    kiem["so"]["lufs_giong"] = lufs_giong
    kiem["so"]["lufs_nhac"] = lufs_nhac

    kp = kiem_phu_de(srt, len(cards), _giay(mp4))
    kiem["so"].update(kp["so"])
    if not kp["dat"]:
        kiem["vi_sao"] += kp["vi_sao"]
        kiem["dat"] = False

    # Chữ đã nung vào hình chưa: so bản chưa nung với bản đã nung.
    chua_nung = mp4.with_name("video_chua_nung.mp4")
    if chua_nung.is_file():
        hien_vat.append(_hien_vat(chua_nung, "VIDEO", "chua_nung_phu_de"))
        cd = chenh_dai_phu_de(chua_nung, mp4)
        kiem["so"].update(cd)
        ly_do_nung = kiem_nung(cd)
        if ly_do_nung:
            kiem["vi_sao"] += ly_do_nung
            kiem["dat"] = False
    else:
        kiem["vi_sao"].append("không có bản chưa nung để đối chiếu")
        kiem["dat"] = False

    # Ba con số độ ồn, chấm bằng MỘT hàm thuần để cửa canh đưa số xấu vào được.
    lufs_ra = _lufs(mp4)
    kiem["so"]["lufs_video"] = lufs_ra
    if lufs_giong is not None and lufs_nhac is not None:
        kiem["so"]["chenh_giong_nhac_db"] = round(lufs_giong - lufs_nhac, 2)
    ly_do_am = kiem_am_thanh(lufs_giong, lufs_nhac, lufs_ra)
    if ly_do_am:
        kiem["vi_sao"] += ly_do_am
        kiem["dat"] = False

    # CỬA NỘI DUNG. Mọi phép trên chỉ đo HÌNH DẠNG, nên một kịch bản là một câu
    # lặp 22 lần vẫn qua sạch. Hai phép này đo thứ khán giả thật sự nhận được.
    khoi = khoi_phu_de(srt.read_text(encoding="utf-8")) if srt.is_file() else []
    kiem["so"]["so_khoi_phu_de"] = len(khoi)
    kiem["so"]["so_khoi_khac_nhau"] = len(set(khoi))
    ly_do_lap = kiem_lap_phu_de(khoi)
    if ly_do_lap:
        kiem["vi_sao"] += ly_do_lap
        kiem["dat"] = False

    # Phụ đề phải PHỦ KÍN kịch bản. Mọi cửa trên chỉ đối chiếu phụ đề với CHÍNH
    # NÓ; cửa này là cửa duy nhất nhìn ngược về kịch bản gốc.
    cau_kich_ban = tach_cau(van_ban)
    kiem["so"]["so_cau_kich_ban"] = len(cau_kich_ban)
    kiem["so"]["so_cau_len_man_hinh"] = sum(
        1 for c in cau_kich_ban if c in " ".join(khoi))
    ly_do_kin = kiem_phu_kin(van_ban, khoi)
    if ly_do_kin:
        kiem["vi_sao"] += ly_do_kin
        kiem["dat"] = False

    quang = _quang_cam_dai_nhat(wav)
    kiem["so"]["quang_cam_dai_nhat_s"] = round(quang, 2)
    ly_do_cam = kiem_quang_cam(quang)
    if ly_do_cam:
        kiem["vi_sao"] += ly_do_cam
        kiem["dat"] = False

    return {"trang_thai": "PASS" if kiem["dat"] else "FAIL",
            "artifacts": hien_vat, "kiem": kiem,
            "ms": round((time.monotonic() - t0) * 1000, 1),
            "vi_sao": "" if kiem["dat"] else "; ".join(kiem["vi_sao"])}
