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
    STUDIO_FIXTURE.md CÓ · 924 byte · 154 từ
                        sha256 33887b979f8c0be04b299281105b90740e01dbe1f8fc0eb725e29e61eeeb31b5

Đo thêm một nhịp để biết thời lượng có rơi vào cửa sổ không: 13 từ đọc hết
4,875 s, nên 154 từ ≈ 58 s — nằm giữa 55 và 65. Không phải may: nếu lệch thì
`_dai_ngan_lai()` cắt/đệm cho vừa, và verifier vẫn là thứ nói lời cuối.

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


def _cat_doan(van_ban: str, so_the: int) -> List[str]:
    cau = [c.strip() for c in re.split(r"(?<=[.!?])\s+", van_ban.strip()) if c.strip()]
    if len(cau) < so_the:
        cau = (cau * so_the)[:so_the]
    moi = max(1, len(cau) // so_the)
    return [" ".join(cau[i * moi:(i + 1) * moi]) or cau[-1] for i in range(so_the)]


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


def render(cards: List[Path], wav: Path, ra: Path) -> tuple[bool, str]:
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

    lenh += ["-filter_complex", doan, "-map", "[vout]", "-map", f"{len(cards)}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "96k", "-shortest", str(ra)]
    r = subprocess.run(lenh, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=TRAN_RENDER_GIAY)
    if r.returncode != 0 or not ra.is_file():
        return False, f"ffmpeg: {(r.stderr or '').strip()[:200]}"
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
    """Chạy cả dây chuyền. Trả về `{trang_thai, artifacts, kiem, ms, vi_sao}`."""
    t0 = time.monotonic()
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
    so_the = max(SO_THE_TOI_THIEU, int(round(_giay(wav) / GIAY_MOI_THE)))
    cards = sinh_the_hinh(van_ban, thu_muc_ra, so_the=so_the)
    hien_vat += [_hien_vat(c, "IMAGE", "generated_template") for c in cards]

    mp4 = thu_muc_ra / "video.mp4"
    ok, loi = render(cards, wav, mp4)
    if not ok:
        return {"trang_thai": "KHONG_CHAY_DUOC", "artifacts": hien_vat, "kiem": {},
                "ms": round((time.monotonic() - t0) * 1000, 1), "vi_sao": loi}
    hien_vat.append(_hien_vat(mp4, "VIDEO", "rendered"))

    kiem = kiem_video(mp4)
    return {"trang_thai": "PASS" if kiem["dat"] else "FAIL",
            "artifacts": hien_vat, "kiem": kiem,
            "ms": round((time.monotonic() - t0) * 1000, 1),
            "vi_sao": "" if kiem["dat"] else "; ".join(kiem["vi_sao"])}
