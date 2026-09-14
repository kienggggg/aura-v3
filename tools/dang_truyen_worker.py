# -*- coding: utf-8 -*-
"""Đăng truyện tự động — vòng 0 (`CHOT:dang-vong-0`, 14/09/2026). Chạy ở TIẾN TRÌNH RIÊNG.

Chạy bằng Python của venv AURA v2, vì venv ấy đã có Playwright 1.60 và Chromium — vòng
này không tải gì. Không đưa Playwright vào `requirements.txt` của v3: cùng khuôn bộ căn
chữ, giữ con số "2 gói ngoài".

    D:\\AURA_OS_v2\\venv\\Scripts\\python.exe tools\\dang_truyen_worker.py mo  wattpad
    D:\\AURA_OS_v2\\venv\\Scripts\\python.exe tools\\dang_truyen_worker.py xem wattpad

HAI CHẾ ĐỘ, CẢ HAI KHÔNG BẤM GÌ — `tests/test_dang_truyen_worker.py` đọc AST để giữ điều ấy:
    mo   mở hồ sơ ở trang đăng nhập; SẾP tự gõ mật khẩu rồi đóng cửa sổ.
    xem  mở trang soạn truyện, ghi cây trợ năng + ảnh chụp, để viết kịch bản theo chữ
         hiển thị và vai trò — không theo class CSS, thứ đổi nhanh nhất.

Hồ sơ nằm dưới `F:\\aura-dang\\`, NGOÀI repo: ai lấy được thư mục ấy là vào được tài khoản
(`CLAUDE.md` §2, Sếp nới 14/09). CHƯA mã hoá — ghi rõ trong kế hoạch §5.
Trình duyệt thật, không giả vân tay, không giải CAPTCHA.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

GOC_HO_SO = Path(r"F:\aura-dang")
NEN_TANG = {
    "wattpad": {"dang_nhap": "https://www.wattpad.com/login",
                "soan": "https://www.wattpad.com/myworks"},
    "sangtacviet": {"dang_nhap": "https://sangtacviet.com/",
                    "soan": "https://sangtacviet.com/writer.php",
                    # Nút "Thêm Truyện" chỉ là onclick location.href tới trang này (đọc
                    # HTML 14/09) — mở thẳng trang không tạo ra gì.
                    "them_truyen": "https://sangtacviet.com/uploader/add-book/"},
}
TRAN_MO_GIAY = 900          # Sếp có 15 phút để đăng nhập; quá thì đóng, báo HET_GIO


def ho_so(nen_tang: str) -> Path:
    """Thư mục hồ sơ của một nền tảng. Tên lạ thì NỔ — không đoán sang nền tảng khác."""
    if nen_tang not in NEN_TANG:
        raise ValueError(f"nền tảng {nen_tang!r} không có; chỉ nhận {sorted(NEN_TANG)}")
    return GOC_HO_SO / nen_tang


def _mo_trinh_duyet(p, nen_tang: str):
    d = ho_so(nen_tang)
    d.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(str(d), headless=False, viewport=None)


def mo(nen_tang: str) -> dict:
    from playwright.sync_api import sync_playwright

    t0 = time.monotonic()
    with sync_playwright() as p:
        ctx = _mo_trinh_duyet(p, nen_tang)
        trang = ctx.pages[0] if ctx.pages else ctx.new_page()
        trang.goto(NEN_TANG[nen_tang]["dang_nhap"])
        # Chờ Sếp đóng MỌI tab — Sếp có thể mở thêm tab khi đăng nhập.
        while ctx.pages and time.monotonic() - t0 < TRAN_MO_GIAY:
            time.sleep(1)
        het_gio = bool(ctx.pages)
        # Sếp đóng tab cuối thì Chromium tự tắt, context đã đóng — gọi close() lúc ấy
        # ném TargetClosedError. Đo 14/09: CẢ HAI lượt `mo` đầu tiên chết đúng dòng này,
        # sau khi Sếp đã đăng nhập xong. Chỉ đóng khi còn tab, tức là lúc hết giờ.
        if het_gio:
            ctx.close()
    return {"che_do": "mo", "nen_tang": nen_tang,
            "trang_thai": "HET_GIO" if het_gio else "XONG",
            "giay": round(time.monotonic() - t0, 1)}


def xem(nen_tang: str, ten_trang: str = "soan") -> dict:
    from playwright.sync_api import sync_playwright

    if ten_trang not in NEN_TANG[nen_tang] or ten_trang == "dang_nhap":
        raise ValueError(f"trang {ten_trang!r} không có cho {nen_tang}")
    ra = GOC_HO_SO / "xem"
    ra.mkdir(parents=True, exist_ok=True)
    moc = time.strftime("%Y%m%d-%H%M%S")
    with sync_playwright() as p:
        ctx = _mo_trinh_duyet(p, nen_tang)
        trang = ctx.pages[0] if ctx.pages else ctx.new_page()
        trang.goto(NEN_TANG[nen_tang][ten_trang])
        trang.wait_for_load_state("networkidle", timeout=30000)
        cay = trang.locator("body").aria_snapshot()
        anh = ra / f"{nen_tang}-{moc}.png"
        chu = ra / f"{nen_tang}-{moc}.txt"
        trang.screenshot(path=str(anh), full_page=True)
        chu.write_text(cay, encoding="utf-8")
        # HTML nguyên trang: biểu mẫu dạng hộp thoại (Bootstrap) thường dựng SẴN rồi ẩn đi,
        # nên đọc được các ô của nó mà không cần bấm nút nào (14/09, nút "Thêm Truyện").
        html = ra / f"{nen_tang}-{moc}.html"
        html.write_text(trang.content(), encoding="utf-8")
        kq = {"che_do": "xem", "nen_tang": nen_tang, "url": trang.url, "tieu_de": trang.title(),
              "anh": str(anh), "cay": str(chu), "html": str(html), "so_ky_tu_cay": len(cay)}
        ctx.close()
    return kq


def main(argv: list[str]) -> int:
    # In JSON tiếng Việt qua đường ống: Windows mặc định cp1252 và chết ở "ẽ" (đã trả
    # giá ở bộ căn chữ) — ghim UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) not in (3, 4) or argv[1] not in ("mo", "xem") or (argv[1] == "mo" and len(argv) == 4):
        print(json.dumps({"loi": "cách gọi: dang_truyen_worker.py mo <nền tảng> | xem <nền tảng> [trang]"},
                         ensure_ascii=False))
        return 2
    kq = mo(argv[2]) if argv[1] == "mo" else xem(*argv[2:])
    print(json.dumps(kq, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
