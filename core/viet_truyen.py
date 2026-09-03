# -*- coding: utf-8 -*-
"""AURA viết kịch bản cho Alpha — MÁY đếm, model viết.

VÌ SAO TÁCH RA MỘT TỆP RIÊNG, KHÔNG DÙNG LẠI CỬA CHAT

Đo 03/09/2026, `core.web_search.is_search_request`::

    "Viết cho tôi một truyện ngắn về người thợ săn..."   tra mạng = False   đúng
    "Kể một câu chuyện HIỆN NAY về thành phố ngập..."    tra mạng = True    SAI

Một yêu cầu sáng tác có chữ chỉ thời gian bị đem ra máy chủ tìm kiếm: 23–43 giây
đốt vô ích, và đề bài đi ra ngoài. Cùng họ với ca `"phiên này"` trong CLAUDE.md.

Và cấu hình chat dùng lại không được: `OllamaConfig.num_predict = 768` — 220 từ
tiếng Việt sát trần đó — còn `temperature = 0.3` chỉnh cho câu trả lời dữ kiện,
không phải văn xuôi.

MODEL KHÔNG ĐẾM ĐƯỢC, VÀ ĐÂY LÀ SỐ

Yêu cầu 232 từ, `qwen3.5:4b`, 5 lượt::

    lần    từ   lệch   câu khác
      1   214    -18         16
      2   346   +114         14
      3   273    +41         13
      4   190    -42         13
      5   134    -98         12
    đúng số từ 0/5 · đủ câu khác nhau 4/5

Ràng buộc *số câu* thì nó giữ được. Nhưng từ/câu dao động **11,2–24,7**, nên số
câu cũng không điều khiển được độ dài. Không núm nào của model làm được việc
này — đúng `CLAUDE.md` mục 3: con số là dữ kiện của MÁY.

CÁCH XỬ LÝ: XIN DÀI DƯ RỒI CẮT GIỮA

Đo 5 lượt, xin 320 từ::

    không cắt      1/5 lọt cửa
    cắt từ DƯỚI    4/5 — nhưng MẤT KẾT TRUYỆN
    cắt từ GIỮA    4/5 — giữ được câu mở và câu kết

Cùng tỉ lệ, khác hẳn kết quả. Cắt dưới cho câu cuối *"Sự im lặng giữa hai người
không nặng nề mà đầy chất thơ"* — cắt ngang. Cắt giữa cho *"Mỗi giọt mưa rơi
xuống đất đều là một lời cầu nguyện"* — kết thật.

TRẦN CỨNG 19,2 TỪ/CÂU

Lượt trượt duy nhất không hỏng vì dài: sau khi cắt nó đúng 237 từ, nhưng chỉ còn
**11 câu**. Nó viết 442 từ trong 21 câu = 21 từ/câu, mà ``250 / 13 = 19,2`` là
trần. Câu dài hơn thế thì hai ràng buộc KHÔNG THỂ cùng đúng, và không cách cắt
nào cứu được. Nên đo từ/câu TRƯỚC khi cắt rồi sinh lại luôn.

CHƯA CHẶN ĐƯỢC — đừng đọc thành đã chặn

Cửa này đếm từ, đếm câu, đếm lặp. Nó **không** biết truyện hay hay dở, có mạch
lạc không, có mở-thân-kết không. Mười lăm câu vô nghĩa nhưng khác nhau vẫn lọt
sạch. Đây là trần thật của thiết kế, không vá được bằng thêm ngưỡng.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple

# Ngưỡng chép tay từ `KY_LUAT_THUC_THI.md` Chương II mục 1b — đăng ký ở đó
# TRƯỚC khi có tệp này.
SO_TU_MIN, SO_TU_MAX = 215, 250
SO_CAU_KHAC_MIN = 13
LAP_TOI_DA = 2
TRAN_SO_LAN = 3

# 250 / 13 = 19,23. Viết câu dài hơn thế thì không cách cắt nào làm cho vừa cả
# hai ràng buộc — đo được ở lượt 442 từ / 21 câu.
TRAN_TU_MOI_CAU = SO_TU_MAX / SO_CAU_KHAC_MIN

# Xin dài dư để còn chỗ mà cắt. 320 cho 4/5 lọt cửa sau khi cắt giữa.
SO_TU_XIN = 320

MODEL = "qwen3.5:4b"
HOST = "http://127.0.0.1:11434"
# `num_predict` của chat là 768 — không đủ cho 320 từ tiếng Việt.
NUM_PREDICT = 1400
NUM_CTX = 4096
# Chat để 0.3 vì nó trả lời dữ kiện. Văn xuôi cần cao hơn.
NHIET_DO = 0.8
TRAN_GIAY = 300


def _tach_cau(van_ban: str) -> List[str]:
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+", van_ban.strip()) if c.strip()]


def _dem(cau: List[str]) -> Dict[str, Any]:
    tu = len(" ".join(cau).split())
    return {
        "so_tu": tu,
        "so_cau": len(cau),
        "so_cau_khac": len(set(cau)),
        "lap_nhieu_nhat": max((cau.count(c) for c in set(cau)), default=0),
        "tu_moi_cau": round(tu / len(cau), 2) if cau else 0.0,
    }


def do_kich_ban(van_ban: str) -> Tuple[str, List[str], Dict[str, Any]]:
    """Chấm một kịch bản. Trả `(trạng thái, lý do bác, số đo)`.

    HÀM THUẦN, cố ý. Để phép chấm nằm rải trong `viet_kich_ban` thì cửa canh chỉ
    khẳng định được "số đo nằm trong khoảng" trên một lượt ĐẠT, không cách nào
    đưa văn bản XẤU vào. Đây là lỗi đã mắc BỐN lần trong `core/phong_alpha.py`
    (âm thanh · phụ đề · nung · quãng câm), lần nào cũng phải tách hàm ra mới vá
    được.

    Ba trạng thái, không gộp:
        DAT             lọt cửa sổ
        KHONG_DAT       đo được mà ngoài cửa sổ
        KHONG_DO_DUOC   không có gì để đo
    """
    if not van_ban or not van_ban.strip():
        return "KHONG_DO_DUOC", ["không có văn bản để chấm"], {}
    cau = _tach_cau(van_ban)
    if not cau:
        return "KHONG_DO_DUOC", ["không tách được câu nào"], {}
    so = _dem(cau)

    ly_do: List[str] = []
    if not (SO_TU_MIN <= so["so_tu"] <= SO_TU_MAX):
        ly_do.append(f"{so['so_tu']} từ, cần {SO_TU_MIN}–{SO_TU_MAX}")
    if so["so_cau_khac"] < SO_CAU_KHAC_MIN:
        ly_do.append(f"{so['so_cau_khac']} câu khác nhau, cần ≥ {SO_CAU_KHAC_MIN}")
    if so["lap_nhieu_nhat"] > LAP_TOI_DA:
        ly_do.append(f"một câu lặp {so['lap_nhieu_nhat']} lần, cho tối đa {LAP_TOI_DA}")
    return ("DAT" if not ly_do else "KHONG_DAT"), ly_do, so


def cat_cho_vua(van_ban: str) -> Tuple[str, int]:
    """Cắt từ GIỮA cho lọt cửa sổ. Trả `(văn bản mới, số câu đã bỏ)`.

    Giữ câu MỞ và câu KẾT, bỏ dần câu ở giữa. Cắt từ dưới lên cũng lọt cửa 4/5
    y hệt, nhưng câu cuối thành một câu giữa truyện — video kết thúc lửng.
    """
    cau = _tach_cau(van_ban)
    if len(cau) <= 2:
        return van_ban, 0
    giu = list(cau)
    bo = 0
    i = 1                              # không bao giờ đụng câu đầu
    while len(" ".join(giu).split()) > SO_TU_MAX and len(giu) > 2:
        if i >= len(giu) - 1:          # cũng không bao giờ đụng câu cuối
            i = 1
        giu.pop(i)
        bo += 1
        i += 1
    return " ".join(giu), bo


def _xin_model(loi: str, hat: int) -> Tuple[str, float]:
    """Gọi model. Ném `RuntimeError` nếu không gọi được — chỗ gọi tự phân loại."""
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps({
            "model": MODEL, "prompt": loi, "stream": False, "think": False,
            "options": {"seed": hat, "temperature": NHIET_DO,
                        "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TRAN_GIAY) as r:
            d = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError) as e:
        raise RuntimeError(f"{type(e).__name__}: {e}") from e
    txt = d.get("response", "")
    # `think: False` vẫn có bản để lại khối nghĩ thầm; cắt nếu có.
    if "</think>" in txt:
        txt = txt.split("</think>")[-1]
    return txt.strip(), time.monotonic() - t0


def _loi_nhac(chu_de: str) -> str:
    """Lời nhắc này ĐÃ ĐƯỢC ĐO. Sửa một chữ là phải đo lại.

    Bản đầu của tôi thêm *"mỗi câu KHÔNG quá 15 từ"* để chữa trần 19,2 từ/câu.
    Nó chữa được thật — từ/câu tụt xuống 8,1–10,1 — nhưng kéo luôn tổng độ dài
    xuống: chạy thật 3 lượt ra **171 · 163 · 187 từ**, trượt cả ba vì QUÁ NGẮN.

    Phép đo cho 4/5 lọt cửa dùng lời nhắc KHÔNG có câu ấy. Tôi sửa lời nhắc rồi
    không đo lại — đúng tội "tiện tay" mà `CLAUDE.md` mục 5 cấm. Trần từ/câu đã
    có máy canh ở `viet_kich_ban`; không cần nhờ model giữ hộ.
    """
    return (f"Viết một truyện ngắn tiếng Việt hoàn chỉnh về: {chu_de}. "
            f"Có mở đầu và kết thúc rõ ràng, dài khoảng {SO_TU_XIN} từ, "
            f"chia thành ít nhất 18 câu. "
            f"Chỉ trả về truyện, không giải thích, không tiêu đề.")


def viet_kich_ban(chu_de: str, tran: int = TRAN_SO_LAN, hat_dau: int = 1) -> Dict[str, Any]:
    """Sinh một kịch bản đạt chuẩn cho Alpha.

    Luôn trả về `so_lan_thu` — một kịch bản đạt sau 1 lần và sau 3 lần là hai
    chuyện khác nhau, và giấu con số ấy là giấu giá. Cùng lý do sổ phiên phải
    mang `latency_ms`: đừng in ra phán quyết mà không kèm con số tạo ra nó.
    """
    t0 = time.monotonic()
    lan: List[Dict[str, Any]] = []
    for i in range(tran):
        try:
            tho, giay = _xin_model(_loi_nhac(chu_de), hat_dau + i)
        except RuntimeError as e:
            lan.append({"hat": hat_dau + i, "trang_thai": "KHONG_DO_DUOC", "vi_sao": str(e)})
            continue

        cau = _tach_cau(tho)
        truoc = _dem(cau)
        # Đo từ/câu TRƯỚC khi cắt: quá trần thì không cách cắt nào cứu được,
        # cắt xong vẫn trượt — sinh lại luôn cho đỡ phí.
        if truoc["tu_moi_cau"] > TRAN_TU_MOI_CAU:
            lan.append({"hat": hat_dau + i, "trang_thai": "KHONG_DAT", "so": truoc,
                        "vi_sao": [f"{truoc['tu_moi_cau']} từ/câu, quá trần "
                                   f"{TRAN_TU_MOI_CAU:.1f} — cắt kiểu gì cũng trượt"],
                        "giay": round(giay, 1)})
            continue

        van, da_bo = cat_cho_vua(tho)
        trang_thai, ly_do, so = do_kich_ban(van)
        lan.append({"hat": hat_dau + i, "trang_thai": trang_thai, "so": so,
                    "vi_sao": ly_do, "giay": round(giay, 1), "cau_da_bo": da_bo})
        if trang_thai == "DAT":
            return {"trang_thai": "DAT", "van_ban": van, "so": so,
                    "so_lan_thu": i + 1, "lan": lan,
                    "ms": round((time.monotonic() - t0) * 1000, 1)}

    cuoi = lan[-1] if lan else {}
    return {
        # Mọi lượt đều không gọi được model thì đó là KHÔNG ĐO ĐƯỢC, không phải
        # "đã đo, không đạt". Gộp hai cái này là bệnh cũ.
        "trang_thai": ("KHONG_DO_DUOC"
                       if lan and all(l["trang_thai"] == "KHONG_DO_DUOC" for l in lan)
                       else "KHONG_DAT"),
        "van_ban": "", "so": cuoi.get("so", {}), "so_lan_thu": len(lan), "lan": lan,
        "ms": round((time.monotonic() - t0) * 1000, 1),
    }
