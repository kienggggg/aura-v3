# -*- coding: utf-8 -*-
"""Nhớ lại — tra NỘI DUNG đã rơi khỏi cửa sổ, thay vì để model bịa.

13/08/2026, đo trên phiên thật 15 lượt:

    lượt 1   Sếp: "Xe đạp của em màu xanh lá, biển số 29AB-123.45"
    ...      13 lượt hỏi chuyện khác, đẩy lượt 1 ra khỏi 24 tin model nhìn thấy
    lượt 15  Sếp: "Xe đạp của em màu gì, biển số bao nhiêu?"
             AURA: "màu xanh, biển số 123."          <-- BỊA

Dữ kiện vẫn nằm trong sổ phiên, ĐÚNG TỪNG KÝ TỰ. Chỉ là không ai đọc lại. Trí
nhớ tình tiết của AURA là loại CHỈ-GHI: chép mọi thứ xuống rồi không bao giờ
mở ra.

Tệ hơn "quên": hàng rào `_QUEN_DAU_CHUYEN` ("em quên chứ không phải không
biết") KHÔNG bắn, vì nó chỉ bắn khi model chịu nói mình bó tay. Model bịa một
câu tự tin thì đi vòng qua cửa đó.

Cùng khuôn với ba mảnh đã có — `dong_ho` (ngày giờ), `may_tinh` (phép tính),
`doc_so_phien` (đếm lượt): **máy tra sổ rồi đưa đáp án sẵn vào lời dặn, không
hỏi model.** Khác một chỗ: ba cái kia tính ra dữ kiện MỚI, cái này lôi lại lời
CHÍNH SẾP đã nói.

NỚI CỬA SỔ KHÔNG PHẢI CÁCH CHỮA. `max_history_messages` từ 24 lên 48 chỉ dời
cái mép ra xa và ăn thêm RAM trên máy 11,7 GB — quá mép vẫn bịa y như cũ.

BA LUẬT CỦA TỆP NÀY:

1. **Chỉ đọc lời SẾP nói, không đọc lời AURA đáp.** Lời model là ý kiến hạng
   hai (CLAUDE.md §7). Lôi lại một câu AURA từng bịa thì thành bịa hai lần, và
   lần sau nó có "bằng chứng" là chính nó.

2. **Khớp theo TỪ, không theo chuỗi con.** Bệnh đắt nhất của repo này: `"ai"`
   khớp trong `"thứ hai"`, `"hiện nay"` khớp trong `"p·hiên này"` (12/08, làm
   câu hỏi riêng tư bị đẩy ra Google).

3. **Không chắc thì im.** Trả `None` để đường cũ chạy, và AURA nói "em quên".
   Một bộ tra sai còn tệ hơn không có: nó nhét nhầm ngữ cảnh vào, và model sẽ
   nói sai MỘT CÁCH TỰ TIN vì tưởng có căn cứ.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Sequence

# Từ chức năng — có mặt ở mọi câu nên không phân biệt được gì.
# Bỏ chúng đi rồi mới đếm chồng lấp, không thì "của em" khớp với mọi lượt.
_TU_RONG = frozenset("""
a ai ay ban bao bay bi boi ca cac cai cang chi cho chua chuyen co con cua cung
da dang de den deu di do doi dung duoc em gi gia giup hay hoi khi khong la lai
lam len luc ma mai minh moi mot na nao nay nen nhe nhi nho nhu nhung no noi nua
o phai qua quen ra rang roi sao se sep the thi tho toi tren tu tuy va vao ve voi
vi vua xem y
""".split())

# Chỉ giữ chữ và số; dấu câu và gạch nối thành khoảng trắng để "29AB-123.45"
# tách ra thành các mẩu đối chiếu được.
_TACH = re.compile(r"[^0-9a-z]+")

# Ngưỡng: phải trùng ÍT NHẤT ngần này từ có nghĩa mới dám lôi lại.
# 2 là đủ chặt để "Python là gì" (0 từ trùng) không kéo nhầm lượt xe đạp về,
# và đủ lỏng để "xe đạp ... màu ... biển số" (5 từ trùng) bắt được.
_TOI_THIEU = 2

# Trần chữ nhét vào lời dặn. Một lượt cũ dài lê thê đẩy chính câu hỏi ra xa,
# đúng lỗi đã ghi ở `_messages`: dữ kiện bị lịch sử chen vào thì model bỏ qua.
_TRAN_CHU = 400


def _tu(text: str) -> set[str]:
    """Câu -> tập TỪ có nghĩa, đã bỏ dấu."""
    tach = unicodedata.normalize("NFD", (text or "").lower())
    khong_dau = "".join(c for c in tach if not unicodedata.combining(c))
    khong_dau = khong_dau.replace("đ", "d")
    return {t for t in _TACH.split(khong_dau) if len(t) > 1 and t not in _TU_RONG}


def nho_lai(
    text: str, history: Sequence[object], tam_nhin: int
) -> str | None:
    """Sếp hỏi về thứ đã rơi khỏi cửa sổ -> lôi nguyên văn lượt cũ ra.

    `tam_nhin` = số tin model sắp được nhìn. Chỉ tra phần NẰM NGOÀI đó — thứ
    model còn thấy thì không cần nhắc, nhắc lại chỉ làm lời dặn dài thêm.

    Trả `None` khi: sổ chưa vượt cửa sổ · không lượt nào đủ trùng · hoặc câu
    hỏi rỗng nghĩa.
    """
    if tam_nhin <= 0 or len(history) <= tam_nhin:
        return None

    tu_hoi = _tu(text)
    if len(tu_hoi) < _TOI_THIEU:
        return None

    # Phần model KHÔNG được nhìn. Đếm theo tin, giống hệt chỗ cắt ở `_messages`.
    ngoai_tam = list(history)[: len(history) - tam_nhin]

    tot_nhat: tuple[int, str] | None = None
    for tin in ngoai_tam:
        vai = str(getattr(tin, "role", "") or "")
        # LUẬT 1: chỉ lời Sếp. Lôi lại lời AURA là nhân đôi cái bịa cũ.
        if vai not in ("user", "owner", "sep", "sếp"):
            continue
        noi_dung = str(getattr(tin, "content", "") or "").strip()
        if not noi_dung:
            continue
        trung = len(tu_hoi & _tu(noi_dung))
        if trung < _TOI_THIEU:
            continue
        # `>=` chứ không `>`: cùng điểm thì lấy lượt MỚI HƠN. Dữ kiện được sửa
        # thì bản sau đè bản trước — "xe đạp giờ màu đỏ" phải thắng "màu xanh".
        if tot_nhat is None or trung >= tot_nhat[0]:
            tot_nhat = (trung, noi_dung)

    if tot_nhat is None:
        return None

    cau = " ".join(tot_nhat[1].split())
    if len(cau) > _TRAN_CHU:
        cau = cau[:_TRAN_CHU].rstrip() + "…"

    # Nói rõ ba điều, vì mỗi điều đã có lần sai:
    #   - đây là lời SẾP nói, không phải AURA nghĩ ra
    #   - nó nằm NGOÀI phần đang thấy (nếu không model tưởng mình tự nhớ được)
    #   - dữ kiện không có trong đó thì phải nói KHÔNG BIẾT, đừng suy ra
    return (
        f'ĐÃ TRA SỔ PHIÊN — đoạn này nằm NGOÀI phần đang hiển thị, chính SẾP đã '
        f'nói ở một lượt trước: "{cau}". Dùng đúng dữ kiện trong đó để trả lời. '
        f'Chi tiết nào KHÔNG có trong câu đó thì nói thẳng là không có trong '
        f'sổ — TUYỆT ĐỐI không suy đoán, không làm tròn, không rút gọn con số.'
    )


__all__ = ["nho_lai"]
