# -*- coding: utf-8 -*-
"""Gắn mốc thời gian cho LỜI ĐÃ BIẾT, rồi sinh phụ đề karaoke `.ass`.

VÌ SAO KHÔNG PHẢI "PHIÊN DỊCH LẠI" (07/09/2026)
------------------------------------------------
AURA **đã biết lời** — chính nó sinh giọng từ lời ấy. Việc cần là gắn mốc cho
lời đã biết, không phải đoán lại lời từ tiếng. Nên bộ nhận dạng ở đây chỉ là
một cái thước: nó đọc ra chuỗi từ kèm mốc, còn mốc thì được **chuyển sang lời
gốc** qua chuỗi con chung dài nhất.

Đo 07/09/2026 trên `voice.wav` 60,00s · 12 đoạn · 245 từ:

    model   RTF    thời gian   WER      TỪ GỐC CÓ MỐC
    base    0,23     13,7s     17,1%    205/245  83,7%   KHÔNG ĐẠT
    small   0,63     38,1s      6,9%    228/245  93,1%   ĐẠT

VÒNG ĐO ĐẦU CHẤM SAI. Chỉ tiêu đầu đếm *số từ*: `base` ra 247/245 = **100,8%**
và được chấm ĐẠT, trong khi nó phiên *"Này hôm nay"* cho *"Ngày hôm nay"*. Một
bản sai cả 245 từ vẫn đếm ra 245 từ. Đổi sang WER + chuỗi con chung thì thứ tự
LẬT NGƯỢC: base 83,7% < small 93,1%. Đúng bài "đừng tự chấm điểm bằng dò chuỗi
con" đã ghi 12/08.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any, Dict, List, Tuple

from core.paths import PROJECT_ROOT

# Chép TAY từ `KY_LUAT_THUC_THI.md` §2d, và cả hai con số này được viết ra
# TRƯỚC khi chạy vòng đo cho ra 6,9% / 93,1% — không phải fit sau khi thấy kết
# quả. Đó là khác biệt giữa một ngưỡng và một lời mô tả.
WER_TRAN = 0.15
KHOP_SAN = 0.90
MODEL = "small"
BIEN_DOAN = 0.30
TRAN_GIAY = 900

# TÌM BỘ CĂN BẰNG ĐƯỜNG DẪN TUYỆT ĐỐI, KHÔNG DỰA VÀO PATH.
#
# Cùng bài đã trả giá 06/09 ở phòng `epsilon`: cùng mã, cùng đề, HAI phán quyết
# khác nhau chỉ vì PATH của tiến trình gọi. Kho model để cùng ổ với
# `F:\ollama-models` — ổ C còn 26,7 GB, F còn 61 GB.
_CHO_TIM = (
    r"F:\aura-stt\venv\Scripts\python.exe",
    r"D:\AURA_v3\.stt\venv\Scripts\python.exe",
)
_WORKER = PROJECT_ROOT / "tools" / "can_tung_tu_worker.py"


def tim_bo_can() -> str | None:
    """Đường dẫn tới python CÓ `faster-whisper`, hoặc `None`."""
    import os

    tay = os.environ.get("AURA_STT_PYTHON")
    if tay and Path(tay).is_file():
        return tay
    for p in _CHO_TIM:
        if Path(p).is_file():
            return p
    return None


def _chuan(t: str) -> str:
    return unicodedata.normalize("NFC", t.lower())


def tach_tu(t: str) -> List[str]:
    t = re.sub(r"[.,!?;:\"'()\[\]…–—-]", " ", _chuan(t))
    return [w for w in t.split() if w]


def _lcs_cap(a: List[str], b: List[str]) -> List[Tuple[int, int]]:
    """Cặp chỉ số của chuỗi con chung dài nhất giữa lời GỐC và lời NHẬN.

    Dùng LCS chứ không dùng `zip`: bộ nhận dạng thêm/bớt từ, nên ghép theo thứ
    tự sẽ lệch dần và mọi từ sau chỗ lệch đều nhận sai mốc. Đúng bài "gắn theo
    thứ tự là giả định, không phải phép đo" — 30 tóm tắt đúng nội dung nằm sai
    URL, ghi 12/08.
    """
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            dp[i][j] = (dp[i + 1][j + 1] + 1 if a[i] == b[j]
                        else max(dp[i + 1][j], dp[i][j + 1]))
    cap, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            cap.append((i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return cap


def _wer(goc: List[str], nhan: List[str]) -> float:
    truoc = list(range(len(nhan) + 1))
    for i, x in enumerate(goc, 1):
        nay = [i]
        for j, y in enumerate(nhan, 1):
            nay.append(min(truoc[j] + 1, nay[j - 1] + 1, truoc[j - 1] + (x != y)))
        truoc = nay
    return truoc[-1] / max(1, len(goc))


def _noi_suy(moc: Dict[int, Tuple[float, float]], so_tu: int,
             dau: float, cuoi: float) -> List[Tuple[float, float]]:
    """Từ không khớp thì chia đều giữa hai từ kề CÓ mốc.

    Bỏ trắng thì chữ biến mất giữa câu — người xem thấy một khoảng câm rồi chữ
    nhảy lại. Nội suy giữ được dòng chảy, và nói rõ ra rằng những từ ấy là
    SUY RA chứ không phải đo được.
    """
    ra: List[Tuple[float, float]] = []
    for i in range(so_tu):
        if i in moc:
            ra.append(moc[i])
            continue
        t = next((k for k in range(i - 1, -1, -1) if k in moc), None)
        s = next((k for k in range(i + 1, so_tu) if k in moc), None)
        a = moc[t][1] if t is not None else dau
        b = moc[s][0] if s is not None else cuoi
        n = (s if s is not None else so_tu) - (t + 1 if t is not None else 0)
        k = i - (t + 1 if t is not None else 0)
        buoc = (b - a) / max(1, n)
        ra.append((a + k * buoc, a + (k + 1) * buoc))
    return ra


def _ass_giay(g: float) -> str:
    g = max(0.0, g)
    h, r = divmod(g, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def viet_ass(doan: List[str], moc_doan: List[tuple],
             moc_tu: List[List[Tuple[float, float]]], dich: Path) -> Path:
    """Phụ đề karaoke `.ass` — `\\kf` quét chữ theo đúng giọng.

    `\\kf` (quét mượt) chứ không phải `\\k` (đổi màu đứt đoạn): đây là thứ
    người xem nhìn thấy, và cái đáng xem là chữ chạy THEO tiếng.

    Đơn vị của `\\kf` là **phần trăm giây**, không phải mili giây. Nhầm đơn vị
    thì karaoke chạy nhanh gấp 10 và vẫn hợp lệ — libass không kêu.
    """
    dau = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 720", "PlayResY: 1280",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        # PrimaryColour = chữ ĐÃ đọc tới (vàng), SecondaryColour = chữ CHƯA tới
        # (trắng). libass quét từ Secondary sang Primary theo `\kf`.
        "Style: Kar,Segoe UI,54,&H0000D7FF,&H00FFFFFF,&H90000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,3,3,0,2,40,40,120,1", "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text",
    ]
    for i, chu in enumerate(doan):
        if i >= len(moc_doan) or i >= len(moc_tu):
            break
        bd, kt = moc_doan[i]
        tu = chu.split()
        mt = moc_tu[i]
        phan = []
        for j, w in enumerate(tu):
            if j < len(mt):
                cs = max(1, int(round((mt[j][1] - mt[j][0]) * 100)))
            else:
                cs = 1
            phan.append(r"{\kf%d}%s " % (cs, w))
        dau.append(f"Dialogue: 0,{_ass_giay(bd)},{_ass_giay(kt)},Kar,,0,0,0,,"
                   + "".join(phan).rstrip())
    dich.write_text("\n".join(dau) + "\n", encoding="utf-8", newline="\n")
    return dich


def can_tung_tu(wav: Path, doan: List[str], moc_doan: List[tuple],
                dich_ass: Path) -> Dict[str, Any]:
    """Chạy bộ căn, chấm, và sinh `.ass` nếu đạt.

    BA TRẠNG THÁI, KHÔNG GỘP THÀNH HAI:
      `PASS`           đo đủ và qua cả WER lẫn độ phủ
      `KHONG_DAT`      đo được mà dưới ngưỡng — có số, và số ấy nói không
      `KHONG_DO_DUOC`  không có bộ căn / worker gãy — CHƯA đo, không phải hỏng
    """
    bo_can = tim_bo_can()
    if not bo_can:
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": "máy này chưa có bộ căn chữ (đặt AURA_STT_PYTHON "
                          f"hoặc cài vào {_CHO_TIM[0]})"}
    if not _WORKER.is_file():
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": f"thiếu {_WORKER.name}"}

    try:
        r = subprocess.run([bo_can, str(_WORKER), str(wav), "--model", MODEL],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TRAN_GIAY)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": f"bộ căn không chạy được: {type(e).__name__}"}
    if r.returncode != 0 or not (r.stdout or "").strip():
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": f"bộ căn trả mã {r.returncode}: "
                          f"{(r.stderr or '')[:160]}"}
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": "bộ căn trả về không phải JSON"}
    nhan_tho = d.get("tu") or []
    if not nhan_tho:
        return {"trang_thai": "KHONG_DO_DUOC", "ass": None,
                "vi_sao": d.get("loi") or "bộ căn không trả mốc từ nào"}

    goc_tu = [tach_tu(c) for c in doan]
    phang = [w for c in goc_tu for w in c]
    nhan = [tach_tu(x["chu"]) for x in nhan_tho]
    nhan_phang, ban_do = [], []
    for k, ws in enumerate(nhan):
        for w in ws:
            nhan_phang.append(w)
            ban_do.append(k)

    wer = _wer(phang, nhan_phang)
    cap = _lcs_cap(phang, nhan_phang)
    khop = len(cap) / max(1, len(phang))
    so = {"wer": round(wer, 4), "khop": round(khop, 4),
          "tu_goc": len(phang), "tu_co_moc": len(cap),
          "model": d.get("model"), "giay_nap": d.get("giay_nap"),
          "giay_dich": d.get("giay_dich")}

    if wer > WER_TRAN or khop < KHOP_SAN:
        return {"trang_thai": "KHONG_DAT", "ass": None, "so": so,
                "vi_sao": f"WER {wer:.1%} (trần {WER_TRAN:.0%}) · "
                          f"khớp {khop:.1%} (sàn {KHOP_SAN:.0%})"}

    moc_phang = {i: (nhan_tho[ban_do[j]]["bd"], nhan_tho[ban_do[j]]["kt"])
                 for i, j in cap}
    moc_tu: List[List[Tuple[float, float]]] = []
    o = 0
    for i, ws in enumerate(goc_tu):
        bd, kt = (moc_doan[i] if i < len(moc_doan) else (0.0, 0.0))
        rieng = {k - o: moc_phang[k] for k in range(o, o + len(ws))
                 if k in moc_phang}
        moc_tu.append(_noi_suy(rieng, len(ws), bd, kt))
        o += len(ws)

    viet_ass(doan, moc_doan, moc_tu, dich_ass)
    return {"trang_thai": "PASS", "ass": dich_ass, "so": so,
            "vi_sao": f"{len(cap)}/{len(phang)} từ có mốc đo được, "
                      f"WER {wer:.1%}"}
