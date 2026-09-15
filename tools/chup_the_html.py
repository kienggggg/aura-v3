# -*- coding: utf-8 -*-
"""Chụp thẻ HTML thành ảnh 720×1280 — chạy bằng venv v2 (có Playwright); venv v3 không có Playwright
và không được thêm vào (`CLAUDE.md` §1: 2 gói ngoài).

    python tools/chup_the_html.py <thư mục chứa NN.html>   ->   NN.png cạnh mỗi tệp

Chromium sạch, không hồ sơ, không mạng: thẻ chỉ dùng phông của máy (Segoe UI).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

d = Path(sys.argv[1])
tep = sorted(d.glob("*.html"))
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 720, "height": 1280}, device_scale_factor=1)
    for t in tep:
        pg.goto(t.as_uri())
        pg.wait_for_timeout(150)
        pg.screenshot(path=str(t.with_suffix(".png")))
    b.close()
print(len(tep))
