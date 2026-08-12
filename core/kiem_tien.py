# -*- coding: utf-8 -*-
"""Soát đơn vị tiền — bắt con số lệch 1000 lần trước khi nó tới mắt Sếp.

10/08/2026, phiên thật của Sếp:

    HỎI : giá vàng ở miền bắc Việt Nam hôm nay là bao nhiêu
    ĐÁP : ...khoảng 137.500 đồng/lượng (mua vào) và 141.000 đồng/lượng (bán ra)

Sai đơn vị **1000 lần** — đúng ra là 137,5 TRIỆU đồng/lượng.  Con số lấy từ
nguồn thì đúng; báo chí Việt Nam ghi giá vàng theo *nghìn đồng*, và AURA chép
số mà gắn nhầm đơn vị.

Ở đây CỐ Ý KHÔNG tự nhân lên 1000 rồi tuyên bố con số mới.  Máy chắc chắn được
một chuyện duy nhất: **con số này vô lý**.  Nó không chắc con số đúng là bao
nhiêu — nguồn có thể ghi nghìn đồng, có thể là giá một chỉ, có thể là giá cũ.
Tự sửa là AURA bịa ra giá, và bịa một con số tiền thì tệ hơn nhiều so với nói
"em không chắc".

Ngưỡng dưới đây cố tình đặt RẤT THẤP so với giá thật, để chỉ bắt cái lệch hẳn
một bậc nghìn chứ không bắt nhầm dao động thị trường.
"""
from __future__ import annotations

import re

# (các cách viết đơn vị, mức sàn hợp lý tính bằng đồng)
_NGUONG: tuple[tuple[tuple[str, ...], int], ...] = (
    # Vàng: một lượng = một cây = 10 chỉ.  Giá đã trên 10 triệu/lượng từ 2009.
    (("đồng/lượng", "đồng một lượng", "đồng mỗi lượng",
      "đồng/cây", "đồng một cây"), 10_000_000),
    # Một chỉ vàng chưa bao giờ dưới 1 triệu trong thời gian AURA phục vụ.
    (("đồng/chỉ", "đồng một chỉ", "đồng mỗi chỉ"), 1_000_000),
    # Xăng: dưới 5.000 đồng/lít là chuyện của thế kỷ trước.
    (("đồng/lít", "đồng một lít", "đồng mỗi lít"), 5_000),
)

_CANH_BAO = (
    "\n\n⚠️ Em không chắc ĐƠN VỊ của con số trên. Báo chí Việt Nam hay ghi giá "
    "theo *nghìn đồng* rồi lược đi, nên em dễ đọc thiếu ba số 0.\n"
    "Sếp bấm vào nguồn bên dưới xem lại giúp em trước khi dùng con số này ạ."
)

# Số kiểu Việt: 137.500 hoặc 137,5 hoặc 137.500,25 — đứng ngay trước đơn vị.
_SO_TRUOC_DON_VI = r"([\d][\d.,]*)\s*(?:triệu\s*|nghìn\s*|ngàn\s*)?$"


def _doc_so(chuoi: str) -> float | None:
    """Đọc số kiểu Việt Nam: dấu chấm là phân cách nghìn, phẩy là thập phân."""
    sach = (chuoi or "").strip().rstrip(".,")
    if not sach or not sach[0].isdigit():
        return None
    if "," in sach:
        sach = sach.replace(".", "").replace(",", ".")
    else:
        # Chỉ coi dấu chấm là phân cách nghìn khi nó chia đúng nhóm 3 chữ số.
        phan = sach.split(".")
        if len(phan) > 1 and all(len(p) == 3 for p in phan[1:]):
            sach = "".join(phan)
        else:
            sach = sach.replace(".", "")
    try:
        return float(sach)
    except ValueError:
        return None


def _gia_tri_that(chuoi_so: str, duoi_cum: str) -> float | None:
    """Quy về ĐỒNG, có tính chữ "triệu"/"nghìn" nếu người viết ghi kèm."""
    so = _doc_so(chuoi_so)
    if so is None:
        return None
    duoi = duoi_cum.lower()
    if "triệu" in duoi:
        return so * 1_000_000
    if "nghìn" in duoi or "ngàn" in duoi:
        return so * 1_000
    return so


def don_vi_dang_ngo(text: str) -> bool:
    """True khi trong câu có một con số tiền lệch hẳn một bậc nghìn."""
    low = (text or "").lower()
    for cach_viet, san in _NGUONG:
        for don_vi in cach_viet:
            vi_tri = 0
            while True:
                found = low.find(don_vi, vi_tri)
                if found < 0:
                    break
                vi_tri = found + 1
                truoc = low[max(0, found - 24):found]
                khop = re.search(_SO_TRUOC_DON_VI, truoc)
                if not khop:
                    continue
                gia_tri = _gia_tri_that(khop.group(1), truoc)
                if gia_tri is not None and 0 < gia_tri < san:
                    return True
    return False


def gan_canh_bao(text: str) -> str:
    """Thêm một dòng cảnh báo nếu phát hiện đơn vị đáng ngờ; không sửa số."""
    if not text or not don_vi_dang_ngo(text):
        return text
    return text + _CANH_BAO


__all__ = ["don_vi_dang_ngo", "gan_canh_bao"]
