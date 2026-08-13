# -*- coding: utf-8 -*-
"""Đọc sổ phiên — hỏi "câu thứ mấy" là việc ĐẾM, không phải việc đoán.

10/08/2026, phiên thật của Sếp:

    1. Viết hàm Python đảo ngược chuỗi...
    2. giá vàng hôm nay là bao nhiêu
    3. vậy AI là gì
    4. "câu hỏi thứ 2 tôi hỏi bạn trong phiên chat này là hỏi về cái gì"

AURA đáp: "Câu hỏi thứ hai của bạn yêu cầu định nghĩa AI..."  Đó là câu THỨ BA.

Model 4B không đếm được các lượt trong ngữ cảnh của chính nó — nó nhìn thấy một
khối chữ, không thấy một danh sách đánh số.  Nhưng `ChatService` thì có sổ hẳn
hoi.  Cùng một lối chữa với `core/dong_ho.py` và `core/may_tinh.py`: **tra sổ
rồi đưa câu trả lời sẵn vào lời dặn.**

Cố ý đếm trên TOÀN BỘ sổ chứ không trên phần model nhìn thấy — cửa sổ chỉ giữ
24 tin, nên đếm trên phần bị cắt sẽ ra "câu thứ 2" là một câu khác hẳn.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Sequence

_SO_CHU = {
    "nhất": 1, "nhat": 1, "đầu": 1, "dau": 1, "một": 1, "mot": 1,
    "hai": 2, "nhì": 2, "nhi": 2, "ba": 3, "tư": 4, "tu": 4, "bốn": 4,
    "bon": 4, "năm": 5, "nam": 5, "sáu": 6, "sau": 6, "bảy": 7, "bay": 7,
    "tám": 8, "tam": 8, "chín": 9, "chin": 9, "mười": 10, "muoi": 10,
}
# "câu hỏi thứ 2", "câu thứ hai", "câu đầu tiên", "câu hỏi đầu"
_HOI_THU_MAY = re.compile(
    r"cau(?:\s*hoi)?\s*(?:thu\s*)?(\d{1,2}|" + "|".join(_SO_CHU) + r")\b"
)
_HOI_DAU_TIEN = re.compile(r"cau(?:\s*hoi)?\s*(?:dau\s*tien|dau)\b")
_DAU_HIEU = re.compile(r"cau\s*hoi|cau\s*thu|toi\s*(?:da\s*)?hoi|hoi\s*gi")


def _bo_dau(text: str) -> str:
    tach = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in tach if not unicodedata.combining(c)).replace("đ", "d")


def _cau_hoi_cua_sep(history: Sequence[object]) -> list[str]:
    ra: list[str] = []
    for tin in history:
        vai = str(getattr(tin, "role", "") or "")
        if vai in ("user", "owner", "sep", "sếp"):
            noi_dung = str(getattr(tin, "content", "") or "").strip()
            if noi_dung:
                ra.append(noi_dung)
    return ra


def tra_so(text: str, history: Sequence[object]) -> str | None:
    """Sếp hỏi về một lượt cũ -> trả câu đó ra sẵn, hoặc `None` nếu không hỏi.

    Trả `None` cũng khi sổ không đủ dài: thà im để model nói "em không rõ" còn
    hơn đưa nhầm một câu rồi nó khẳng định chắc nịch.
    """
    khong_dau = _bo_dau(text)
    if not _DAU_HIEU.search(khong_dau):
        return None

    danh_sach = _cau_hoi_cua_sep(history)
    if not danh_sach:
        return None

    thu_tu: int | None = None
    khop = _HOI_THU_MAY.search(khong_dau)
    if khop:
        gia_tri = khop.group(1)
        thu_tu = int(gia_tri) if gia_tri.isdigit() else _SO_CHU.get(gia_tri)
    elif _HOI_DAU_TIEN.search(khong_dau):
        thu_tu = 1

    if thu_tu is None or thu_tu < 1:
        return None
    if thu_tu > len(danh_sach):
        return (
            f"ĐÃ TRA SỔ: trong phiên này Sếp mới hỏi {len(danh_sach)} câu, "
            f"chưa có câu thứ {thu_tu}. Nói thẳng điều đó, đừng bịa."
        )

    cau = " ".join(danh_sach[thu_tu - 1].split())
    if len(cau) > 300:
        cau = cau[:300].rstrip() + "…"
    # Lời dặn phải nói rõ là NHẮC LẠI, không phải TRẢ LỜI LẠI.
    #
    # 10/08/2026, phiên thật của Sếp: câu số 2 là "bạn là 1 AI hay 1 Agent".
    # Sếp hỏi "câu hỏi thứ 2 tôi hỏi bạn là gì", AURA đáp "Tôi là một mô hình
    # ngôn ngữ lớn (AI)..." — nó TRẢ LỜI LẠI câu đó.  Dữ kiện đưa đúng, nhưng
    # câu dặn cũ ("Dựa đúng vào câu này") đọc kiểu nào cũng ra "hãy trả lời câu
    # này".  Sai ở lời tôi viết, không ở model.
    return (
        f'ĐÃ TRA SỔ. Sếp đang hỏi XEM LẠI một lượt cũ, không hỏi lại nội dung '
        f'của nó. Hãy NHẮC LẠI cho Sếp: câu hỏi thứ {thu_tu} của Sếp trong '
        f'phiên này, nguyên văn, là "{cau}". Chỉ nói lại câu đó — TUYỆT ĐỐI '
        f'không trả lời nội dung của nó, và đừng đếm lại.'
    )


def tra_loi_thang(text: str, history: Sequence[object]) -> str | None:
    """Câu trả lời HOÀN CHỈNH cho Sếp, hoặc `None` nếu đây không phải câu hỏi ấy.

    Vì sao có hàm này bên cạnh `tra_so`: `tra_so` đưa model một LỜI DẶN ("nhắc
    lại câu này, đừng trả lời nó") rồi trông vào model nghe lời. Đo 13/08/2026,
    chạy 5 lần cùng một phiên có sẵn hai lượt đầy ngày tháng:

        ĐÚNG 1/5 — bốn lần AURA đáp "Hôm nay là ngày 13 tháng 8 năm 2026"

    Tức nó TRẢ LỜI LẠI câu cũ thay vì nhắc lại, đúng lỗi mà lời dặn dài dòng ở
    `tra_so` sinh ra để chặn. Lời dặn viết kỹ tới đâu cũng thua khi đáp án của
    câu cũ đang nằm ngay trong lịch sử và trong `cau_gio()` ở lời dặn hệ thống —
    model 1.7B bị kéo về phía đó.

    Chỗ chữa không phải viết lời dặn chặt hơn. "Câu thứ N là gì" có đáp án
    ĐƯỢC XÁC ĐỊNH HOÀN TOÀN bởi sổ: một chuỗi chép nguyên văn. Không có việc gì
    cho model làm ngoài chép lại — mà hỏi model là mời nó đoán (CLAUDE.md §3).
    Nên máy trả lời thẳng, bỏ qua model.

    Đổi lại: câu trả lời cụt và máy móc hơn. Chấp nhận — đúng còn hơn mượt.
    """
    khong_dau = _bo_dau(text)
    if not _DAU_HIEU.search(khong_dau):
        return None

    danh_sach = _cau_hoi_cua_sep(history)
    if not danh_sach:
        return None

    thu_tu: int | None = None
    khop = _HOI_THU_MAY.search(khong_dau)
    if khop:
        gia_tri = khop.group(1)
        thu_tu = int(gia_tri) if gia_tri.isdigit() else _SO_CHU.get(gia_tri)
    elif _HOI_DAU_TIEN.search(khong_dau):
        thu_tu = 1

    if thu_tu is None or thu_tu < 1:
        return None
    if thu_tu > len(danh_sach):
        return (
            f"Trong phiên này Sếp mới hỏi {len(danh_sach)} câu, chưa có câu "
            f"thứ {thu_tu} ạ."
        )

    cau = " ".join(danh_sach[thu_tu - 1].split())
    if len(cau) > 300:
        cau = cau[:300].rstrip() + "…"
    return f'Câu hỏi thứ {thu_tu} của Sếp trong phiên này, nguyên văn, là: "{cau}"'


__all__ = ["tra_so", "tra_loi_thang"]
