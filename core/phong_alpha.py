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

    phong, _ = _tim_phong()
    ra: List[Path] = []
    doan = _cat_doan(van_ban, so_the)
    for i, chu in enumerate(doan, 1):
        # Nền chuyển màu dọc: mỗi thẻ một tông, để `blackdetect` không bắt
        # nhầm và để mắt người thấy thẻ đã đổi.
        anh = Image.new("RGB", (RONG, CAO))
        ve = ImageDraw.Draw(anh)
        for y in range(CAO):
            t = y / CAO
            ve.line([(0, y), (RONG, y)],
                    fill=(int(18 + 40 * t + i * 12), int(22 + 30 * t), int(46 + 70 * t)))
        ve.text((48, 90), f"THẺ {i}/{len(doan)}", font=phong, fill=(120, 200, 255))
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


def render(cards: List[Path], wav: Path, ra: Path) -> tuple[bool, str]:
    dai = _giay(wav)
    if dai <= 0:
        return False, "không đọc được thời lượng voice.wav"
    moi_the = dai / len(cards)
    ds = ra.with_name("cards.txt")
    ds.write_text(
        "".join(f"file '{c.as_posix()}'\nduration {moi_the:.4f}\n" for c in cards)
        + f"file '{cards[-1].as_posix()}'\n", encoding="utf-8")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(ds),
         "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-r", "24", "-vf", f"scale={RONG}:{CAO}", "-c:a", "aac", "-b:a", "96k",
         "-shortest", str(ra)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=TRAN_RENDER_GIAY)
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
    cards = sinh_the_hinh(van_ban, thu_muc_ra, so_the=SO_THE_TOI_THIEU + 1)
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
