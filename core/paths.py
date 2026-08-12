# -*- coding: utf-8 -*-
"""Đường dẫn gốc của dự án.  Chỉ có thế.

Tệp này thay cho `core/config.py` cũ: **1.029 dòng, 33 cờ bật/tắt tính năng**,
mà toàn bộ xương sống chat dùng đúng MỘT thứ trong đó — `PROJECT_ROOT`.

Đó là bệnh của AURA v2 gói gọn trong một con số, nên nó cũng là luật đầu tiên
của v3: **cấu hình đi theo thứ cần nó, không gom vào một cái kho chung.**  Ai
cần một cờ mới thì đặt cờ đó cạnh mã dùng nó, đừng mang về đây.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

__all__ = ["PROJECT_ROOT", "DATA_DIR"]
