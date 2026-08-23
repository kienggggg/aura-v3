# -*- coding: utf-8 -*-
"""nhip_thuc_thi.py — Phân tích Dải Nhịp Thực Thi (Execution Rhythms) cho AURA v3.

Độc lập hoàn toàn với `core/the_cst.py` (giữ sạch hợp đồng Cửa Cứng 1).

Luật chia nhịp (Machine-verifiable, Sai lệch cho phép = 0 nhịp):
- Phân loại thẻ:
  + K = Khởi tạo / Chuẩn bị: 'gan'
  + B = Biến đổi / Xử lý: 'pheptinh', 'neu', 'nguoc_lai', 'lap_moi', 'lap_khi'
  + X = Kết xuất / Chuyển giao: 'in_ra', 'tra_ve'
- Quy tắc đóng nhịp:
  + Mỗi nhịp ĐÓNG LẠI KHI GẶP THẺ 'X'.
  + Mỗi nhịp chứa đúng một thẻ 'X' và toàn bộ các thẻ 'K'/'B' đứng trước nó thuộc chu kỳ đó.
  + Hỗ trợ đầy đủ:
    * Nhịp khuyết B (dạng 'KKX', ví dụ `dong_ho.py :: cau_gio`).
    * Nhịp rỗng / chỉ có X (dạng 'X', ví dụ `kiem_tien.py :: don_vi_dang_ngo`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from core.the_cst import TheNode, doc_tep_py_sang_cay_the, doc_chuoi_py_sang_cay_the

TANG_THE = {
    "gan": "K",
    "pheptinh": "B",
    "neu": "B",
    "nguoc_lai": "B",
    "lap_moi": "B",
    "lap_khi": "B",
    "in_ra": "X",
    "tra_ve": "X",
}


@dataclass
class NhipThucThi:
    so_thu_tu: int
    cac_the: list[dict] = field(default_factory=list)
    mat_cat: str = ""
    mo_ta_nhip: str = ""
    co_khuyet_b: bool = False
    co_rong: bool = False  # Chỉ có X, không có K và B

    def to_dict(self) -> dict:
        return asdict(self)


def _phang_cay_the(nodes: list[TheNode]) -> list[TheNode]:
    """Làm phẳng danh sách thẻ theo thứ tự duyệt sâu (pre-order)."""
    ra = []
    for n in nodes:
        ra.append(n)
        ra.extend(_phang_cay_the(n.than))
    return ra


def chia_nhip_thuc_thi(cac_the_trong_ham: list[TheNode]) -> list[NhipThucThi]:
    """Chia danh sách các thẻ trong một hàm thành các dải nhịp thực thi.
    
    Quy tắc: Nhịp đóng lại khi gặp thẻ 'X' (in_ra, tra_ve).
    Mỗi nhịp chứa đúng 1 thẻ X và toàn bộ thẻ K/B trước đó.
    """
    danh_sach_the = _phang_cay_the(cac_the_trong_ham)
    the_phan_tang = [t for t in danh_sach_the if t.ma in TANG_THE]

    if not the_phan_tang:
        return []

    danh_sach_nhip: list[NhipThucThi] = []
    current_nodes: list[TheNode] = []
    current_str = []
    so_thu_tu = 1

    for the in the_phan_tang:
        ky_hieu = TANG_THE[the.ma]
        current_nodes.append(the)
        current_str.append(ky_hieu)

        if ky_hieu == "X":
            # Đóng nhịp khi gặp X
            mat_cat = "".join(current_str)
            co_khuyet_b = ("B" not in mat_cat) and ("K" in mat_cat)
            co_rong = ("B" not in mat_cat) and ("K" not in mat_cat)  # Chỉ có X

            mo_ta = (
                f"Nhịp {so_thu_tu}: Chu kỳ hoàn tất"
                if not co_rong else
                f"Nhịp {so_thu_tu}: Kết xuất rỗng / chuyển tiếp"
            )

            nhip = NhipThucThi(
                so_thu_tu=so_thu_tu,
                cac_the=[t.to_dict() for t in current_nodes],
                mat_cat=mat_cat,
                mo_ta_nhip=mo_ta,
                co_khuyet_b=co_khuyet_b,
                co_rong=co_rong,
            )
            danh_sach_nhip.append(nhip)

            # Reset cho nhịp tiếp theo
            current_nodes = []
            current_str = []
            so_thu_tu += 1

    # Nếu còn các thẻ K/B ở cuối mà chưa có X đóng nhịp (nhịp mở)
    if current_nodes:
        mat_cat = "".join(current_str)
        nhip = NhipThucThi(
            so_thu_tu=so_thu_tu,
            cac_the=[t.to_dict() for t in current_nodes],
            mat_cat=mat_cat,
            mo_ta_nhip=f"Nhịp {so_thu_tu}: Nhịp mở (chưa có kết xuất)",
            co_khuyet_b=False,
            co_rong=False,
        )
        danh_sach_nhip.append(nhip)

    return danh_sach_nhip


def phan_tich_nhip_cho_ham(tep_py: str | Path, ten_ham: str) -> list[NhipThucThi]:
    """Đọc tệp .py và phân tích dải nhịp cho một hàm cụ thể."""
    rec = doc_tep_py_sang_cay_the(tep_py)
    tat_ca_the = _phang_cay_the(rec.tree)
    
    ham_node = None
    for n in tat_ca_the:
        if n.ma == "ham" and n.o.get("ten_ham") == ten_ham:
            ham_node = n
            break

    if not ham_node:
        raise ValueError(f"Không tìm thấy hàm '{ten_ham}' trong {tep_py}")

    return chia_nhip_thuc_thi(ham_node.than)
