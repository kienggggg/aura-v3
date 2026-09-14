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
import subprocess
import sys
import time
from pathlib import Path

GOC_HO_SO = Path(r"F:\aura-dang")
# Wattpad chạy Chrome THẬT: Google từ chối đăng nhập trên Chromium do Playwright điều
# khiển — "Couldn't sign you in · This browser or app may not be secure" (ảnh Sếp gửi
# 14/09). Sếp đăng nhập bằng Chrome mở như chương trình thường (`mo_chrome`); về sau
# Playwright chỉ mượn phiên của WATTPAD, không đụng tới Google nữa.
TRINH_DUYET = {"wattpad": "chrome", "sangtacviet": "chromium"}
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
NEN_TANG = {
    "wattpad": {"dang_nhap": "https://www.wattpad.com/login",
                "soan": "https://www.wattpad.com/myworks",
                # "+ Truyện Mới" là <a href="/write/story/new"> (đọc HTML 14/09).
                "truyen_moi": "https://www.wattpad.com/write/story/new"},
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
    # Hồ sơ Chrome và hồ sơ Chromium là hai thư mục khác nhau — không trộn định dạng.
    return GOC_HO_SO / (nen_tang if TRINH_DUYET[nen_tang] == "chromium" else f"{nen_tang}-chrome")


def _mo_trinh_duyet(p, nen_tang: str):
    d = ho_so(nen_tang)
    d.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(
        str(d), headless=False, viewport=None,
        channel="chrome" if TRINH_DUYET[nen_tang] == "chrome" else None)


def _co_cloudflare(trang) -> bool:
    """Có hộp kiểm Cloudflare trên trang không. Có thì dừng — không giải (`CLAUDE.md` §2)."""
    return any(f.url.startswith("https://challenges.cloudflare.com") for f in trang.frames)


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


def mo_chrome(nen_tang: str) -> dict:
    """Mở Chrome THẬT như chương trình thường — không Playwright, không cổng gỡ lỗi — ở
    trang đăng nhập, cho SẾP tự đăng nhập. Chờ Sếp đóng Chrome; quá giờ thì để nguyên
    cửa sổ (Sếp có thể đang dở tay) và báo HET_GIO."""
    if TRINH_DUYET.get(nen_tang) != "chrome":
        raise ValueError(f"{nen_tang!r} không dùng Chrome thật")
    d = ho_so(nen_tang)
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    tien_trinh = subprocess.Popen([str(CHROME), f"--user-data-dir={d}", "--no-first-run",
                                   NEN_TANG[nen_tang]["dang_nhap"]])
    try:
        tien_trinh.wait(timeout=TRAN_MO_GIAY)
        het_gio = False
    except subprocess.TimeoutExpired:
        het_gio = True
    return {"che_do": "mo_chrome", "nen_tang": nen_tang,
            "trang_thai": "HET_GIO" if het_gio else "XONG",
            "giay": round(time.monotonic() - t0, 1)}


# Truyện thử của vòng 0 — tạo MỘT lần, không bao giờ xuất bản. Bút danh "AURA": ghi đúng
# người viết; Sếp chưa chọn bút danh cho truyện thật (14/09).
TRUYEN_THU = {"Tên truyện": "AURA bản thử", "Tác giả/Bút danh": "AURA",
              "Thể loại": "Thử nghiệm",
              "Giới thiệu": "Bản thử của máy đăng tự động AURA. Không phát hành."}


def _dong_hop_thoai(h, ghi: list) -> None:
    """Ghi lời hộp thoại rồi đóng. Đo 14/09: STV bật alert rồi trang đi tiếp, gọi accept()
    lúc hộp đã tắt thì ném "No dialog is showing" — lời nhắn đã ghi được, nên bỏ qua lỗi ấy."""
    ghi.append(f"{h.type}: {h.message}")
    try:
        h.accept() if h.type == "alert" else h.dismiss()
    except Exception as e:  # noqa: BLE001 — chỉ nuốt đúng ca hộp đã tắt
        if "No dialog is showing" not in str(e):
            raise


def tao_thu(nen_tang: str) -> dict:
    """Tạo truyện thử trên Sáng Tác Việt nếu CHƯA có, rồi đọc lại danh sách để xác nhận.

    Chỉ bấm đúng nút "Tạo truyện". Nút phát hành là nút RIÊNG của từng truyện (đọc mã
    trang 14/09), và tệp này không có dòng nào chạm tới nó — cửa canh đọc AST giữ điều ấy.
    """
    if nen_tang != "sangtacviet":
        raise ValueError("vòng 0 mới dựng phần tạo truyện cho sangtacviet")
    from playwright.sync_api import sync_playwright

    ra = GOC_HO_SO / "xem"
    ra.mkdir(parents=True, exist_ok=True)
    moc = time.strftime("%Y%m%d-%H%M%S")
    hop_thoai: list = []
    kq = {"che_do": "tao_thu", "nen_tang": nen_tang}
    with sync_playwright() as p:
        ctx = _mo_trinh_duyet(p, nen_tang)
        trang = ctx.pages[0] if ctx.pages else ctx.new_page()
        # alert thì bấm OK để trang chạy tiếp; confirm thì TỪ CHỐI — không đồng ý gì hộ Sếp.
        trang.on("dialog", lambda h: _dong_hop_thoai(h, hop_thoai))
        trang.goto(NEN_TANG[nen_tang]["soan"])
        trang.wait_for_load_state("networkidle", timeout=30000)
        ten = TRUYEN_THU["Tên truyện"]
        if _co_cloudflare(trang):
            kq["trang_thai"] = "KHONG_DO_DUOC"
        elif trang.get_by_text(ten, exact=True).count():
            kq["trang_thai"] = "DA_CO"
        else:
            trang.goto(NEN_TANG[nen_tang]["them_truyen"])
            trang.wait_for_load_state("networkidle", timeout=30000)
            if _co_cloudflare(trang):
                kq["trang_thai"] = "KHONG_DO_DUOC"
            else:
                for nhan, gia_tri in TRUYEN_THU.items():
                    trang.get_by_label(nhan, exact=True).fill(gia_tri)
                trang.get_by_role("button", name="Tạo truyện", exact=True).click()
                trang.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(2)
                # Tin trang ĐỌC LẠI, không tin cú bấm.
                trang.goto(NEN_TANG[nen_tang]["soan"])
                trang.wait_for_load_state("networkidle", timeout=30000)
                kq["trang_thai"] = "DA_TAO" if trang.get_by_text(ten, exact=True).count() else "KHONG_THAY"
        anh = ra / f"{nen_tang}-tao_thu-{moc}.png"
        trang.screenshot(path=str(anh), full_page=True)
        (ra / f"{nen_tang}-tao_thu-{moc}.txt").write_text(
            trang.locator("body").aria_snapshot(), encoding="utf-8")
        kq.update({"url": trang.url, "anh": str(anh), "hop_thoai": hop_thoai})
        ctx.close()
    return kq


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
        # KHÔNG chờ "networkidle": Wattpad gọi mạng liên tục (quảng cáo, đo lường) nên
        # không bao giờ yên — đo 14/09 hết giờ 30 s, còn STV thì yên được. Chờ "load" + 3 s.
        trang.wait_for_load_state("load", timeout=30000)
        time.sleep(3)
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
    che_do = {"mo": mo, "mo_chrome": mo_chrome, "tao_thu": tao_thu, "xem": xem}
    if len(argv) not in (3, 4) or argv[1] not in che_do or (argv[1] != "xem" and len(argv) == 4):
        print(json.dumps({"loi": "cách gọi: dang_truyen_worker.py mo|mo_chrome|tao_thu <nền tảng>"
                                 " | xem <nền tảng> [trang]"}, ensure_ascii=False))
        return 2
    kq = che_do[argv[1]](*argv[2:])
    print(json.dumps(kq, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
