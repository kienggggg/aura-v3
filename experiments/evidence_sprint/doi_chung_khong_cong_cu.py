# -*- coding: utf-8 -*-
"""Nhóm ĐỐI CHỨNG: đúng 10 đề đó, đúng model đó, CÓ vá import, KHÔNG công cụ.

VÌ SAO CẦN: lượt 18/08 có công cụ ra 2/10, so với nền cũ 0/10. Nhưng giữa hai
lần đó tôi đổi HAI thứ — thêm công cụ tra kho, VÀ vá lỗi `ap_ham` nuốt dòng
import. Đề `2d4131cc` lật từ truot sang dat là do BẢN VÁ IMPORT, đọc sổ nóng
thì thấy rõ: model tra kho ra hàm, viết `from core.web_search import
loc_menh_lenh`, và bản cũ vứt dòng đó đi.

Hai biến đổi cùng lúc thì 2/10 không quy được cho biến nào. Lượt này khoá công
cụ lại, giữ nguyên bản vá import — chênh lệch với 2/10 chính là phần công cụ
đóng góp, không lẫn gì khác.

    set DELTA_DE=D:/alpha_bench/de_doi_chung.json
    venv\\Scripts\\python.exe experiments\\evidence_sprint\\doi_chung_khong_cong_cu.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# DELTA_DE phải đặt TRƯỚC khi nạp do_delta: hằng DE đọc biến môi trường ở cấp
# module, đặt sau thì nó đã chốt vào bộ 38 đề đầy đủ rồi.
os.environ.setdefault("DELTA_DE", "D:/alpha_bench/de_doi_chung.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import do_delta_cloud                                            # noqa: E402,F401
import do_delta as D                                            # noqa: E402

# do_delta_cloud ghi đè D.SO vào sổ mây chung. Đổi sang sổ riêng, nếu không
# lượt đối chứng đè lên 38 kết quả cũ và mất luôn cái nền để so.
D.SO = Path("D:/alpha_bench/ket_qua_doi_chung.json")

if __name__ == "__main__":
    print("  ĐỐI CHỨNG · " + str(D.DE))
    print("  cùng 10 đề · cùng gemini · CÓ vá import · KHÔNG công cụ\n")
    raise SystemExit(D.main())
