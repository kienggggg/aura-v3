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

TRẦN CỨNG TỪ/CÂU — 19,2 cho tới 04/09/2026, nay 22,7

Lượt trượt duy nhất không hỏng vì dài: sau khi cắt nó đúng 237 từ, nhưng chỉ còn
**11 câu**. Nó viết 442 từ trong 21 câu = 21 từ/câu, mà trần khi ấy là
``250 / 13 = 19,2``. Câu dài hơn trần thì hai ràng buộc KHÔNG THỂ cùng đúng, và
không cách cắt nào cứu được. Nên đo từ/câu TRƯỚC khi cắt rồi sinh lại luôn.

Ngày 04/09/2026 sàn số câu hạ 13 → 11, nên trần thành ``250 / 11 = 22,7``. Lý
do và bảng đo nằm ngay trên hằng số ``SO_CAU_KHAC_MIN``.

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
# 13 -> 11 ngày 04/09/2026. Con số 13 cũ suy từ `round(60 / 4,5) = 13` thẻ rồi
# giả định mỗi thẻ một câu, và giả định thêm 13 thẻ cho 12 lần đổi cảnh. Dựng
# video THẬT ở từng mức, biến duy nhất là số thẻ:
#
#    thẻ  đổi cảnh  s/thẻ  trạng thái        thẻ  đổi cảnh  s/thẻ  trạng thái
#     13        20    4,6        PASS          8         9    7,4        PASS
#     11        19    5,4        PASS          7        10    8,5        PASS
#     10        16    5,9        PASS          6         9    9,9        PASS
#      9        12    6,6        PASS
#
# `scdet` đếm 20 ở 13 thẻ, không phải 12 — Ken Burns tạo thêm. Phép tính
# `số thẻ − 1` sai hẳn hướng, và MỌI mức 6–13 đều PASS.
#
# Chọn 11 chứ không phải 6, dù 6 cũng PASS: ở 6 thẻ mỗi thẻ đứng 9,9 giây trên
# một video dọc 60 giây, và KHÔNG CỬA NÀO ĐO NHỊP. Lấy sự cho phép của cửa làm
# bằng chứng về chất lượng là đúng cái bẫy `CLAUDE.md` sinh ra để chống. Gần
# sàn thì số còn nhiễu và không đơn điệu (8 thẻ → 9, 7 → 10, 6 → 9), biên chỉ
# hơn ngưỡng 1. 11 thẻ giữ 19 lần đổi cảnh — biên gấp hơn 11 lần ngưỡng.
SO_CAU_KHAC_MIN = 11
LAP_TOI_DA = 2
TRAN_SO_LAN = 3

# 250 / 11 = 22,73. VẪN LÀ HỆ QUẢ, không phải phép đo — nó chưa bao giờ nói
# "câu dài hơn thế thì video xấu". Nó chỉ nói: viết dài hơn thì hai ràng buộc
# (số từ, số câu khác nhau) không thể cùng đúng, và không cách cắt nào cứu được.
#
# Nới này mua được gì, đo trên lưới 2×2 ngày 04/09:
#                            lọt trần 19,2   lọt trần 22,7
#     lời TRUYỆN (đang dùng)      9/10           10/10
#     lời BÀI NÓI                 1/10            6/10
# Lời truyện không mất gì; văn giải thích (22,0–22,4 từ/câu) từ 1/10 lên 6/10.
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


# Ngưỡng chép tay từ `KY_LUAT_THUC_THI.md` mục 1b, "Cửa NÊU ĐỀ".
SO_TU_DE_TRONG_CAU_MO_MIN = 1

# Hư từ tiếng Việt — bỏ ra khỏi đề tài vì chúng có mặt trong MỌI văn bản, nên
# giữ lại thì câu mở nào cũng "nêu đề". Danh sách ĐÓNG, có dấu: bỏ dấu thì `bò`,
# `bỏ`, `bó`, `bọ` cùng thành `bo` — đúng họ bệnh `x in y` đã trả giá bảy lần.
HU_TU = frozenset("""
là và của có không được một những này đó ấy thì mà nên cho đến từ với về
trong ngoài trên dưới khi nếu vì bởi như sẽ đã đang cũng còn chỉ rất quá
mình chúng ta họ tôi bạn ai gì sao thế nào mọi tất cả đều hay hơn nhất
cái người việc làm ra vào lên xuống ở tại bằng theo sau trước giữa nửa
phải cần nhiều ít hoặc càng đầu luôn chưa các để bị nó lại đi
""".split())


def _tu(van_ban: str) -> List[str]:
    """Tách từ (âm tiết) — giữ nguyên dấu, hạ về chữ thường."""
    return re.findall(r"\w+", van_ban.lower(), re.UNICODE)


def tu_khoa_de(chu_de: str) -> List[str]:
    """Từ nội dung của đề tài: bỏ hư từ, bỏ từ một ký tự. Giữ thứ tự, không lặp."""
    ra: List[str] = []
    for t in _tu(chu_de):
        if len(t) > 1 and t not in HU_TU and t not in ra:
            ra.append(t)
    return ra


def kiem_neu_de(chu_de: str, van_ban: str) -> Tuple[str, List[str], Dict[str, Any]]:
    """Câu mở đầu có NÊU đề tài ra không. Trả `(trạng thái, lý do bác, số đo)`.

    HÀM THUẦN, cùng lý do với `do_kich_ban`: để phép chấm nằm rải trong
    `viet_kich_ban` thì cửa canh không cách nào đưa ca XẤU vào.

    NÓ ĐO GÌ — VÀ KHÔNG ĐO GÌ. Nó hỏi *"bài này có nêu đề ra không"*, không hỏi
    *"bài này có đúng đề không"*. Câu thứ hai không có thang đo được trên máy
    này: embedding tắt (`/api/embed` trả *"This server does not support
    embeddings"*), trùng-từ-theo-tỉ-lệ không tách nổi (đề "nấu phở bò" cho đúng
    đề 0,33 / lạc đề 0,17; đề "bài test" cho đúng đề 0,67 / bài lạc 0,33 — cùng
    con số 0,33 vừa đúng vừa sai tuỳ đề), còn hỏi model là để model vừa viết
    chấm chính bài mình.

    Ba trạng thái, không gộp:
        DAT             câu mở có ≥1 từ nội dung của đề
        KHONG_DAT       đo được mà câu mở không nêu đề
        KHONG_DO_DUOC   đề không còn từ nội dung nào -> FAIL-CLOSED

    Fail-closed ở nhánh thứ ba là có chủ đích: không đo được đề thì không dựng
    một video nhận là về đề ấy.
    """
    tu_de = tu_khoa_de(chu_de)
    if not tu_de:
        return ("KHONG_DO_DUOC",
                [f"đề {chu_de!r} không còn từ nội dung nào sau khi bỏ hư từ — "
                 "không có gì để đối chiếu, hãy đặt đề cụ thể hơn"],
                {"so_tu_de": 0})

    cau = _tach_cau(van_ban)
    if not cau:
        return "KHONG_DO_DUOC", ["không tách được câu nào để đọc câu mở"], \
               {"so_tu_de": len(tu_de)}

    tu_cau_mo = set(_tu(cau[0]))
    trung = [t for t in tu_de if t in tu_cau_mo]
    so = {"so_tu_de": len(tu_de), "so_tu_de_trong_cau_mo": len(trung),
          "tu_de_trung": trung}
    if len(trung) < SO_TU_DE_TRONG_CAU_MO_MIN:
        return ("KHONG_DAT",
                [f"câu mở không nêu đề: cần ≥{SO_TU_DE_TRONG_CAU_MO_MIN} từ "
                 f"trong {tu_de}, thấy {len(trung)} — {cau[0][:70]!r}"], so)
    return "DAT", [], so


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


def _loi_nhac(chu_de: str, the_loai: str = "truyen") -> str:
    """Lời nhắc này ĐÃ ĐƯỢC ĐO. Sửa một chữ là phải đo lại.

    Bản đầu của tôi thêm *"mỗi câu KHÔNG quá 15 từ"* để chữa trần 19,2 từ/câu.
    Nó chữa được thật — từ/câu tụt xuống 8,1–10,1 — nhưng kéo luôn tổng độ dài
    xuống: chạy thật 3 lượt ra **171 · 163 · 187 từ**, trượt cả ba vì QUÁ NGẮN.

    Phép đo cho 4/5 lọt cửa dùng lời nhắc KHÔNG có câu ấy. Tôi sửa lời nhắc rồi
    không đo lại — đúng tội "tiện tay" mà `CLAUDE.md` mục 5 cấm. Trần từ/câu đã
    có máy canh ở `viet_kich_ban`; không cần nhờ model giữ hộ.

    04/09/2026 — LỜI NHẮC NÀY GIỮ NGUYÊN, và đó là một QUYẾT ĐỊNH CÓ SỐ.

    Thêm cửa NÊU ĐỀ thì việc đầu tiên nghĩ tới là bảo model nhắc đề ngay câu mở.
    Đã thử ba cách, mỗi cách 5 hạt giống CỐ ĐỊNH, cùng model, cùng tham số:

        lời cũ                            dài 4/5  đề 2/5  CẢ HAI 2/5
        "CÂU ĐẦU TIÊN phải nhắc tới ..."  dài 0/5  đề 0/5  CẢ HAI 0/5
        chèn vào mệnh đề đề tài           dài 2/5  đề 3/5  CẢ HAI 2/5
        mệnh đề ngắn ở cuối               dài 2/5  đề 3/5  CẢ HAI 2/5

    **Không bản nào mua được gì.** Cái gì giúp cửa đề (2/5 → 3/5) lấy đi đúng
    chừng ấy ở cửa dài (4/5 → 2/5). Bản mệnh lệnh viết hoa còn tệ hơn hẳn: nó
    đẩy từ/câu từ ~19 lên **21,7–24,3**, quá trần 19,2 cả năm lượt, nên không
    lượt nào đi tới nổi cửa đề.

    Đây đúng là hình dạng đã trả giá 03/09 ở ngay trên: thêm một ràng buộc vào
    lời nhắc thì model đổi cách viết theo kiểu mình không điều khiển được. Máy
    canh vẫn là máy canh; lời nhắc không phải chỗ để vá.

    Nói rõ giới hạn của phép đo: n=5 mỗi nhánh. `2/5` so với `2/5` KHÔNG chứng
    minh hai bản bằng nhau — nó chỉ nói ở n=5 chưa thấy khác biệt nào. Đủ để
    KHÔNG đổi; chưa đủ để nói đổi thì vô ích.

    05/09/2026 — THÊM `the_loai`, và lần này lời nhắc thứ hai MUA ĐƯỢC thật. Đo
    2×2, biến là thể loại lời nhắc × loại đề tài, cùng 5 hạt giống:

        CẢ HAI cửa /5              đề GIẢI THÍCH   đề HƯ CẤU
        lời TRUYỆN                      1/5             4/5
        lời BÀI NÓI                     3/5             3/5

    Khác hẳn ba bản vá hỏng ở trên: chúng sửa CÂU CHỮ trong cùng một thể loại,
    nên cái gì được ở cửa này mất ở cửa kia. Cái này đổi THỂ LOẠI, và mỗi lời
    thắng trên thể loại của chính nó — đường chéo, không phải một bên thắng
    tuốt.

    Phép đo ấy từng KHÔNG kết luận được, hôm 04/09 cho `0/5 · 2/5 · 0/5 · 2/5`.
    Nguyên nhân là trần 19,2 chặn mất 9/10 lượt bài nói TRƯỚC khi tới cửa đề.
    Hạ sàn câu 13→11 đẩy trần lên 22,7, chạy lại thì đường chéo hiện ngay.

    Giới hạn: n=5 mỗi ô, bốn ô có số lượt đo được khác nhau (5·4·3·3). `1/5` so
    `3/5` là chênh gấp ba nhưng vẫn n=5 — đủ để đổi, chưa đủ để gọi là chứng
    minh.
    """
    if the_loai not in _LOI_THEO_THE_LOAI:
        # FAIL-CLOSED. Gõ nhầm `"bainoi"` mà âm thầm chạy ra truyện thì hỏng
        # LẶNG: kịch bản vẫn ra, vẫn lọt cửa dài, chỉ lạc đề — và không ai biết
        # vì sao. Thà nổ to ngay tại chỗ gọi.
        raise ValueError(
            f"thể loại {the_loai!r} không có; chỉ nhận "
            f"{sorted(_LOI_THEO_THE_LOAI)}")
    return _LOI_THEO_THE_LOAI[the_loai](chu_de)


def _loi_truyen(chu_de: str) -> str:
    """Văn kể chuyện — mở bằng dựng cảnh. Bản chạy từ 03/09/2026."""
    return (f"Viết một truyện ngắn tiếng Việt hoàn chỉnh về: {chu_de}. "
            f"Có mở đầu và kết thúc rõ ràng, dài khoảng {SO_TU_XIN} từ, "
            f"chia thành ít nhất 18 câu. "
            f"Chỉ trả về truyện, không giải thích, không tiêu đề.")


def _loi_bai_noi(chu_de: str) -> str:
    """Lời thoại video giải thích — nói thẳng vào đề, không dựng nhân vật.

    Câu mở đo được: *"Chúng ta đang nói về việc tại sao một bài kiểm tra luôn
    hiển màu xanh lá…"* — so với lời truyện: *"Đêm xuống dần trong phòng thí
    nghiệm nhỏ hẹp của cô gái tên Linh."*

    GIÁ CỦA NÓ, nói ra cùng lúc: nó viết câu DÀI hơn, nên rụng 2/5 ở cửa độ dài
    (đo được 3/5 so với 5/5 của lời truyện). Đổi lại cửa đề lên 3/3.
    """
    return (f"Viết kịch bản lời thoại tiếng Việt cho một video ngắn giải thích: "
            f"{chu_de}. Nói thẳng vào chủ đề, không dựng nhân vật, không kể "
            f"chuyện. Mở bằng một câu nêu rõ đang nói về cái gì, dài khoảng "
            f"{SO_TU_XIN} từ, chia thành ít nhất 18 câu. "
            f"Chỉ trả về nội dung, không giải thích thêm, không tiêu đề.")


# Danh sách ĐÓNG. Thêm thể loại thì phải đo lại 2×2, không được đoán.
_LOI_THEO_THE_LOAI = {"truyen": _loi_truyen, "bai_noi": _loi_bai_noi}
THE_LOAI_MAC_DINH = "truyen"


def viet_kich_ban(chu_de: str, tran: int = TRAN_SO_LAN, hat_dau: int = 1,
                  the_loai: str = THE_LOAI_MAC_DINH) -> Dict[str, Any]:
    """Sinh một kịch bản đạt chuẩn cho Alpha.

    Luôn trả về `so_lan_thu` — một kịch bản đạt sau 1 lần và sau 3 lần là hai
    chuyện khác nhau, và giấu con số ấy là giấu giá. Cùng lý do sổ phiên phải
    mang `latency_ms`: đừng in ra phán quyết mà không kèm con số tạo ra nó.

    HAI CỬA, KHÔNG PHẢI MỘT (từ 04/09/2026): `do_kich_ban` chấm HÌNH DẠNG (đủ
    từ, đủ câu khác nhau, không lặp quá), `kiem_neu_de` chấm câu mở có NÊU đề
    ra không. Trước đó chỉ có cửa thứ nhất, và nó không thể có cửa thứ hai — chữ
    ký `do_kich_ban(van_ban)` không bao giờ nhận `chu_de`. Chạy thật 04/09: đề
    về "bài test luôn xanh" cho ra một bài giảng về gian lận thi cử, ĐẠT sạch.

    `"lan": []` LÀ TRẠNG THÁI THẬT, không phải ca hiếm: đề không còn từ nội dung
    nào thì fail-closed ngay, chưa tốn lượt model nào. Chỗ nào đọc `lan[-1]`
    phải rà lại — hai chỗ trong `interface/noi_bo_api.py` từng nổ IndexError vì
    nó.
    """
    t0 = time.monotonic()

    # Thể loại lạ thì NỔ NGAY, không đợi vào vòng lặp. `_loi_nhac` cũng ném, và
    # ném đúng — nhưng chỉ khi vòng lặp chạy. Gọi với `tran=0` thì thể loại sai
    # lọt qua im lặng. Kiểm ở đây bịt đúng khe ấy.
    if the_loai not in _LOI_THEO_THE_LOAI:
        raise ValueError(
            f"thể loại {the_loai!r} không có; chỉ nhận "
            f"{sorted(_LOI_THEO_THE_LOAI)}")

    # FAIL-CLOSED TRƯỚC KHI TỐN MỘT LƯỢT MODEL. Đề không còn từ nội dung nào thì
    # không có gì để đối chiếu — và mỗi lượt sinh tốn 64–96 giây, nên hỏi câu
    # này sau ba lượt là đốt tới 4,8 phút để nói ra thứ biết ngay từ đầu.
    tt_de, ly_do_de, so_de = kiem_neu_de(chu_de, "câu giả để đọc đề.")
    if tt_de == "KHONG_DO_DUOC" and not so_de.get("so_tu_de"):
        return {"trang_thai": "KHONG_DO_DUOC", "van_ban": "", "so": so_de,
                "so_lan_thu": 0, "lan": [], "vi_sao": ly_do_de,
                "ms": round((time.monotonic() - t0) * 1000, 1)}

    lan: List[Dict[str, Any]] = []
    for i in range(tran):
        try:
            tho, giay = _xin_model(_loi_nhac(chu_de, the_loai), hat_dau + i)
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

        # Cửa NÊU ĐỀ, chấm SAU khi cắt: `cat_cho_vua` bỏ câu ở GIỮA nên câu mở
        # luôn còn nguyên — chấm trước khi cắt thì đo đúng cùng một câu, nhưng
        # chấm sau mới là chấm đúng thứ sẽ đi vào video.
        tt_de, ly_do_de, so_de = kiem_neu_de(chu_de, van)
        so = {**so, **so_de}
        if tt_de != "DAT":
            trang_thai = "KHONG_DAT" if trang_thai == "DAT" else trang_thai
            ly_do = list(ly_do) + ly_do_de

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
