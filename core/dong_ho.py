# -*- coding: utf-8 -*-
"""Đồng hồ của AURA — model không có, nên phải đưa.

10/08/2026 hỏi "Hôm nay là thứ mấy?", AURA đi tra mạng rồi trả về **"Thứ Ba
ngày 21 tháng Bảy năm 2026"**.  Sai 20 ngày, mà vẫn nói chắc nịch, có cả trích
nguồn.  Model không có đồng hồ: nó chỉ biết ngày tháng lờ mờ từ lúc huấn luyện,
và tra mạng không cứu được vì trang web nào cũng nói "hôm nay" theo ngày của
trang đó.

Sửa đúng chỗ: **đưa giờ máy vào lời dặn**.  Rẻ, chắc, không tốn một lần gọi
mạng nào.  Đây cũng là ranh giới đúng — giờ là dữ kiện của MÁY, không phải kiến
thức của model.
"""
from __future__ import annotations

from datetime import datetime

_THU = (
    "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
    "Thứ Sáu", "Thứ Bảy", "Chủ Nhật",
)


def cau_gio(now: datetime | None = None) -> str:
    """Một dòng tiếng Việt nói rõ bây giờ là lúc nào, theo giờ máy của Sếp.

    Nhận `now` để test đóng đinh được thời gian — một hàm đọc thẳng
    `datetime.now()` bên trong thì không có cách nào kiểm.
    """
    hien_tai = now or datetime.now().astimezone()
    thu = _THU[hien_tai.weekday()]
    return (
        f"BÂY GIỜ là {hien_tai:%H:%M} {thu}, ngày {hien_tai.day} tháng "
        f"{hien_tai.month} năm {hien_tai.year} (giờ máy của Sếp). "
        "Dùng mốc này cho mọi câu hỏi về hôm nay, hôm qua, tuần này, tuổi tác "
        "hay khoảng cách thời gian — đừng đoán và đừng tra mạng để biết ngày."
    )


__all__ = ["cau_gio"]
