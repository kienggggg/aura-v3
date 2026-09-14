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

import hashlib
import json
import re
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
    """Có hộp kiểm người-hay-máy trên trang không (Cloudflare, reCAPTCHA, hCaptcha). Có thì
    dừng — không giải (`CLAUDE.md` §2)."""
    return any(f.url.startswith("https://challenges.cloudflare.com") or "recaptcha" in f.url
               or "hcaptcha" in f.url for f in trang.frames)


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


# Wattpad: hai ô bắt buộc, tên theo cây trợ năng đọc 14/09. Ô thứ ba bắt buộc là nút
# "Hư cấu" của mục "Loại hình văn bản".
TRUYEN_THU_WATTPAD = {"Tiêu đề *": "AURA bản thử",
                      "Mô tả * Mô tả": "Bản thử của máy đăng tự động AURA. Không phát hành."}
# Truyện tuyển tập của vòng 2 (`CHOT:dang-vong-2`) — Sếp chọn "dạng tuyển tập" 14/09. Lời
# giới thiệu nói thẳng truyện do AI viết; Sếp đổi tên hay lời giới thiệu được trên Wattpad.
TUYEN_TAP_WATTPAD = {"Tiêu đề *": "Truyện ngắn AURA",
                     "Mô tả * Mô tả": "Tuyển tập truyện ngắn do AURA — một trí tuệ nhân tạo — "
                                      "viết. Mỗi chương là một truyện riêng."}
# Mã truyện thử vừa tạo — để KHÔNG tạo lại, và để kịch bản ghi chỉ mở ĐÚNG truyện ấy,
# không bao giờ mở hai truyện đã đăng của Sếp.
TEP_TRUYEN_THU = GOC_HO_SO / "truyen_thu.json"
# Hàng chờ và sổ đăng: kịch bản ĐẠT do app ghi (`kich_ban.md` + `meta.json`), sổ ghi mỗi lượt.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_AURA = PROJECT_ROOT / "data" / "aura"
SO_DANG = PROJECT_ROOT / "data" / "dang" / "so_dang.jsonl"


def _doc_truyen_thu() -> dict:
    try:
        return json.loads(TEP_TRUYEN_THU.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _ghi_truyen_thu(nen_tang: str, gia_tri: dict) -> None:
    d = _doc_truyen_thu()
    d[nen_tang] = gia_tri
    TEP_TRUYEN_THU.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _tao_stv(trang, kq: dict) -> None:
    """Sáng Tác Việt: chỉ bấm đúng "Tạo truyện". Nút phát hành là nút RIÊNG của từng truyện
    (đọc mã trang 14/09), và tệp này không có dòng nào chạm tới nó."""
    trang.goto(NEN_TANG["sangtacviet"]["soan"])
    trang.wait_for_load_state("networkidle", timeout=30000)
    ten = TRUYEN_THU["Tên truyện"]
    if _co_cloudflare(trang):
        kq["trang_thai"] = "KHONG_DO_DUOC"
        return
    if trang.get_by_text(ten, exact=True).count():
        kq["trang_thai"] = "DA_CO"
        return
    trang.goto(NEN_TANG["sangtacviet"]["them_truyen"])
    trang.wait_for_load_state("networkidle", timeout=30000)
    if _co_cloudflare(trang):
        kq["trang_thai"] = "KHONG_DO_DUOC"
        return
    for nhan, gia_tri in TRUYEN_THU.items():
        trang.get_by_label(nhan, exact=True).fill(gia_tri)
    trang.get_by_role("button", name="Tạo truyện", exact=True).click()
    trang.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)
    # Tin trang ĐỌC LẠI, không tin cú bấm.
    trang.goto(NEN_TANG["sangtacviet"]["soan"])
    trang.wait_for_load_state("networkidle", timeout=30000)
    kq["trang_thai"] = "DA_TAO" if trang.get_by_text(ten, exact=True).count() else "KHONG_THAY"


def _tao_wattpad(trang, kq: dict, khoa: str = "wattpad") -> None:
    """Wattpad: điền hai ô, bấm "Hư cấu" rồi "Lưu & Tiếp tục". Truyện chưa có chương nào
    được đăng thì không ai đọc được. Tạo xong thì ghi mã truyện vào `TEP_TRUYEN_THU` dưới
    `khoa`: "wattpad" là truyện thử, "wattpad_tuyen_tap" là truyện tuyển tập."""
    o = TRUYEN_THU_WATTPAD if khoa == "wattpad" else TUYEN_TAP_WATTPAD
    if khoa in _doc_truyen_thu():
        kq["trang_thai"] = "DA_CO"
        return
    trang.goto(NEN_TANG["wattpad"]["truyen_moi"])
    trang.wait_for_load_state("load", timeout=30000)
    time.sleep(3)
    if _co_cloudflare(trang):
        kq["trang_thai"] = "KHONG_DO_DUOC"
        return
    for nhan, gia_tri in o.items():
        trang.get_by_role("textbox", name=nhan, exact=True).fill(gia_tri)
    trang.get_by_role("button", name="Hư cấu", exact=True).click()
    time.sleep(1)
    trang.get_by_role("button", name="Lưu & Tiếp tục", exact=True).click()
    # Đo 14/09: chờ 33 s là THIẾU — Wattpad chuyển trang muộn hơn, máy báo "KHONG_TAO"
    # trong khi truyện đã có (URL cuối /myworks/416096235/write/…). Chờ tới 90 s.
    for _ in range(90):
        if re.search(r"/myworks/\d+", trang.url):
            break
        time.sleep(1)
    time.sleep(3)
    m = re.search(r"/myworks/(\d+)", trang.url)
    moc = time.strftime("%Y-%m-%d %H:%M:%S")
    # Không chắc thì KHONG_RO — KHÔNG BAO GIỜ nói "không tạo" khi chưa đọc lại. Và vẫn ghi
    # dấu vào tệp, để lần chạy sau thấy "DA_CO" mà không tạo thêm truyện thứ hai.
    if not m:
        _ghi_truyen_thu(khoa, {"id": None, "url": None, "trang_thai": "KHONG_RO", "moc": moc})
        kq["trang_thai"] = "KHONG_RO"
        return
    _ghi_truyen_thu(khoa, {"id": m.group(1), "url": trang.url, "tieu_de": o["Tiêu đề *"], "moc": moc})
    # Tin trang ĐỌC LẠI: mở lại chính trang ấy, tiêu đề truyện phải hiện đúng.
    trang.goto(trang.url)
    trang.wait_for_load_state("load", timeout=30000)
    time.sleep(3)
    kq["trang_thai"] = "DA_TAO" if _dung_truyen(trang, o["Tiêu đề *"]) else "KHONG_RO"


def _dung_truyen(trang, tieu_de: str) -> bool:
    """Trang đang mở có đúng truyện mang tiêu đề này không — đọc tiêu đề hiện trên trang.
    Mọi lần ghi phải qua câu hỏi này TRƯỚC khi chạm vào ô viết (cửa canh kiểm thứ tự)."""
    return trang.get_by_text(tieu_de, exact=True).count() > 0


def _dung_truyen_thu(trang) -> bool:
    return _dung_truyen(trang, TRUYEN_THU_WATTPAD["Tiêu đề *"])


def _chuan_hoa(s: str) -> str:
    """Gộp mọi khoảng trắng liền nhau thành một dấu cách — ô soạn được đổi xuống dòng,
    không được đổi chữ (`CHOT:dang-vong-2`, "đọc lại khớp")."""
    return " ".join((s or "").split())


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _doc_so_dang() -> list:
    try:
        return [json.loads(x) for x in SO_DANG.read_text(encoding="utf-8").splitlines() if x.strip()]
    except OSError:
        return []


def _ghi_so_dang(muc: dict) -> None:
    SO_DANG.parent.mkdir(parents=True, exist_ok=True)
    with SO_DANG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(muc, ensure_ascii=False) + "\n")


def _hang_cho(nen_tang: str) -> list:
    """Kịch bản ĐẠT chưa đăng, cũ nhất trước. Nguồn là thứ app ghi: `kich_ban.md` + `meta.json`.

    Bỏ: thư mục không có `meta.json` (kịch bản cũ, trước vòng 2 — không tự đăng bù); tệp
    kịch bản bị sửa sau khi ghi (SHA không còn khớp meta); SHA đã ĐẠT trong sổ. Một lần
    hỏng trước đó đã mở chương thì trả `url_do_dang`, để lần sau GHI TIẾP vào chương ấy
    thay vì mở chương mới — không để lại chương rỗng.
    """
    so = [m for m in _doc_so_dang() if m.get("nen_tang") == nen_tang]
    da_xong = {m.get("sha256") for m in so if m.get("trang_thai") == "DAT"}
    do_dang = {m.get("sha256"): m["url_chuong"] for m in so
               if m.get("trang_thai") != "DAT" and m.get("url_chuong")}
    ra: dict = {}
    for tep_meta in sorted(DATA_AURA.glob("*/meta.json")):
        try:
            meta = json.loads(tep_meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        kb = tep_meta.parent / "kich_ban.md"
        if not kb.is_file() or hashlib.sha256(kb.read_bytes()).hexdigest() != meta.get("sha256"):
            continue
        # Cùng nội dung ở hai thư mục: giữ bản CŨ NHẤT theo giờ app ghi. Gieo 14/09: bản đầu
        # viết `in ra` — dict đằng nào cũng gộp trùng, nên điều kiện ấy chỉ quyết định giữ
        # bản nào, và không bài nào hỏi điều ấy (cửa mù).
        cu = ra.get(meta["sha256"])
        if meta["sha256"] in da_xong or (cu and cu["luc"] <= meta.get("luc", "")):
            continue
        ra[meta["sha256"]] = {"thu_muc": str(tep_meta.parent), "sha256": meta["sha256"],
                              "chu_de": meta.get("chu_de") or tep_meta.parent.name,
                              "van_ban": kb.read_text(encoding="utf-8").strip(),
                              "luc": meta.get("luc", ""), "url_do_dang": do_dang.get(meta["sha256"])}
    return sorted(ra.values(), key=lambda m: m["luc"])


def _luu_chuong(trang, tuyen_tap: dict, muc: dict) -> dict:
    """MỘT kịch bản thành MỘT chương nháp trong truyện tuyển tập, rồi ĐỌC LẠI.

    Mở trang của truyện tuyển tập, hỏi "đúng truyện chưa", bấm "+ Chương Mới", hỏi lại
    trong trình soạn, điền tên chương (đề) và nội dung, bấm "Lưu", tải lại, đọc lại tên,
    nội dung và chữ "Bản thảo". Lần hỏng trước đã mở chương thì ghi tiếp vào chương ấy.
    """
    t0 = time.monotonic()
    tieu_de = TUYEN_TAP_WATTPAD["Tiêu đề *"]
    kq = {"nen_tang": "wattpad", "sha256": muc["sha256"], "chu_de": muc["chu_de"],
          "thu_muc": muc["thu_muc"]}
    if muc.get("url_do_dang"):
        trang.goto(muc["url_do_dang"])
    else:
        trang.goto(f"https://www.wattpad.com/myworks/{tuyen_tap['id']}")
        trang.wait_for_load_state("load", timeout=30000)
        time.sleep(3)
        if _co_cloudflare(trang) or not _dung_truyen(trang, tieu_de):
            kq["trang_thai"] = "KHONG_DO_DUOC" if _co_cloudflare(trang) else "SAI_TRUYEN"
            return kq
        trang.get_by_role("button", name="+ Chương Mới", exact=True).click()
        for _ in range(60):
            if re.search(r"/write/\d+", trang.url):
                break
            time.sleep(1)
    trang.wait_for_load_state("load", timeout=30000)
    time.sleep(3)
    if not re.search(rf"/myworks/{tuyen_tap['id']}/write/\d+", trang.url):
        kq["trang_thai"] = "KHONG_RO"
        return kq
    kq["url_chuong"] = trang.url
    if _co_cloudflare(trang) or not _dung_truyen(trang, tieu_de):
        kq["trang_thai"] = "KHONG_DO_DUOC" if _co_cloudflare(trang) else "SAI_TRUYEN"
        return kq
    trang.locator("#story-title").fill(muc["chu_de"])
    trang.get_by_role("textbox", name="Viết truyện của bạn", exact=True).fill(muc["van_ban"])
    trang.get_by_role("button", name="Lưu", exact=True).click()
    time.sleep(5)
    trang.reload()
    trang.wait_for_load_state("load", timeout=30000)
    time.sleep(3)
    doc = trang.get_by_role("textbox", name="Viết truyện của bạn", exact=True).inner_text()
    ten = trang.locator("#story-title").inner_text()
    kq.update({"khop": _sha(_chuan_hoa(doc)) == _sha(_chuan_hoa(muc["van_ban"])),
               "ten_khop": _chuan_hoa(ten) == _chuan_hoa(muc["chu_de"]),
               "con_la_nhap": trang.get_by_text("Bản thảo", exact=False).count() > 0,
               "dung_truyen_sau": _dung_truyen(trang, tieu_de)})
    kq["trang_thai"] = ("DAT" if kq["khop"] and kq["ten_khop"] and kq["con_la_nhap"]
                        and kq["dung_truyen_sau"] else "KHONG_DAT")
    kq["giay"] = round(time.monotonic() - t0, 1)
    return kq


def dang_hang_cho(nen_tang: str, toi_da: str = "5") -> dict:
    """Vòng 2: đưa tối đa `toi_da` kịch bản trong hàng chờ thành chương nháp, ghi sổ MỖI
    lượt — kể cả lượt hỏng. Gặp hộp kiểm hay sai truyện thì dừng cả lượt chạy."""
    if nen_tang != "wattpad":
        raise ValueError("vòng 2 mới dựng cho wattpad")
    tuyen_tap = _doc_truyen_thu().get("wattpad_tuyen_tap") or {}
    if not tuyen_tap.get("id"):
        raise ValueError("chưa có truyện tuyển tập — chạy: tao_thu wattpad tuyen_tap")
    viec = _hang_cho(nen_tang)[: int(toi_da)]
    ket: list = []
    if viec:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            ctx = _mo_trinh_duyet(p, nen_tang)
            trang = ctx.pages[0] if ctx.pages else ctx.new_page()
            for muc in viec:
                try:
                    kq = _luu_chuong(trang, tuyen_tap, muc)
                except Exception as e:  # noqa: BLE001 — lượt hỏng cũng phải vào sổ
                    kq = {"nen_tang": nen_tang, "sha256": muc["sha256"], "chu_de": muc["chu_de"],
                          "thu_muc": muc["thu_muc"], "trang_thai": "LOI", "loi": str(e)[:300]}
                    if re.search(rf"/myworks/{tuyen_tap['id']}/write/\d+", trang.url):
                        kq["url_chuong"] = trang.url
                kq["luc"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _ghi_so_dang(kq)
                ket.append(kq)
                if kq["trang_thai"] != "DAT":
                    break
            ctx.close()
    return {"che_do": "dang_hang_cho", "nen_tang": nen_tang, "so_viec": len(viec), "ket": ket}


def ghi_nhap(nen_tang: str, lan: str) -> dict:
    """Vòng 0 bước 3 (`CHOT:dang-vong-0`): ghi MỘT đoạn thử vào chương nháp của truyện thử,
    bấm "Lưu", tải lại trang, ĐỌC LẠI ô viết và trạng thái "Bản thảo".

    Chỉ mở đúng URL trong `TEP_TRUYEN_THU`; tiêu đề trên trang khác truyện thử thì dừng —
    không bao giờ gõ vào hai truyện đã đăng của Sếp. Ba trạng thái như đặc tả: DAT ·
    KHONG_DAT · KHONG_DO_DUOC (gặp hộp kiểm người-hay-máy), thêm SAI_TRUYEN.
    """
    if nen_tang != "wattpad":
        raise ValueError("vòng 0 mới dựng phần ghi cho wattpad")
    url = (_doc_truyen_thu().get("wattpad") or {}).get("url")
    if not url:
        raise ValueError("chưa có truyện thử wattpad — chạy tao_thu trước")
    from playwright.sync_api import sync_playwright

    ra = GOC_HO_SO / "xem"
    ra.mkdir(parents=True, exist_ok=True)
    doan = f"AURA thử ghi nháp, lần {lan}, lúc {time.strftime('%Y-%m-%d %H:%M:%S')}."
    kq = {"che_do": "ghi_nhap", "nen_tang": nen_tang, "lan": lan, "doan": doan}
    t0 = time.monotonic()
    with sync_playwright() as p:
        ctx = _mo_trinh_duyet(p, nen_tang)
        trang = ctx.pages[0] if ctx.pages else ctx.new_page()
        trang.goto(url)
        trang.wait_for_load_state("load", timeout=30000)
        time.sleep(3)
        if _co_cloudflare(trang):
            kq["trang_thai"] = "KHONG_DO_DUOC"
        elif not _dung_truyen_thu(trang):
            kq["trang_thai"] = "SAI_TRUYEN"
        else:
            trang.get_by_role("textbox", name="Viết truyện của bạn", exact=True).fill(doan)
            trang.get_by_role("button", name="Lưu", exact=True).click()
            time.sleep(5)
            trang.reload()
            trang.wait_for_load_state("load", timeout=30000)
            time.sleep(3)
            doc = trang.get_by_role("textbox", name="Viết truyện của bạn", exact=True).inner_text().strip()
            con_nhap = trang.get_by_text("Bản thảo", exact=False).count() > 0
            kq.update({"doc_lai": doc, "khop": doc == doan, "con_la_nhap": con_nhap,
                       "dung_truyen_sau": _dung_truyen_thu(trang)})
            kq["trang_thai"] = "DAT" if (doc == doan and con_nhap) else "KHONG_DAT"
        kq["giay"] = round(time.monotonic() - t0, 1)
        anh = ra / f"{nen_tang}-ghi_nhap-{lan}-{time.strftime('%H%M%S')}.png"
        trang.screenshot(path=str(anh), full_page=True)
        kq["anh"] = str(anh)
        ctx.close()
    return kq


def tao_thu(nen_tang: str, loai: str = "thu") -> dict:
    """Tạo truyện thử (vòng 0) hoặc truyện tuyển tập (vòng 2, `loai="tuyen_tap"`, chỉ
    Wattpad) nếu CHƯA có, rồi chụp lại trang. Không tự bấm gì ở đây — phần bấm nằm ở
    `_tao_stv` / `_tao_wattpad`, mỗi hàm một danh sách nút được phép."""
    buoc = {("sangtacviet", "thu"): _tao_stv,
            ("wattpad", "thu"): lambda t, k: _tao_wattpad(t, k, "wattpad"),
            ("wattpad", "tuyen_tap"): lambda t, k: _tao_wattpad(t, k, "wattpad_tuyen_tap")}
    if (nen_tang, loai) not in buoc:
        raise ValueError(f"không có phần tạo {loai!r} cho {nen_tang!r}")
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
        buoc[(nen_tang, loai)](trang, kq)
        anh = ra / f"{nen_tang}-tao_thu-{moc}.png"
        trang.screenshot(path=str(anh), full_page=True)
        (ra / f"{nen_tang}-tao_thu-{moc}.txt").write_text(
            trang.locator("body").aria_snapshot(), encoding="utf-8")
        kq.update({"url": trang.url, "anh": str(anh), "hop_thoai": hop_thoai})
        ctx.close()
    return kq


def xem(nen_tang: str, ten_trang: str = "soan") -> dict:
    from playwright.sync_api import sync_playwright

    if ten_trang == "truyen_thu":
        url = _doc_truyen_thu().get(nen_tang, {}).get("url")
        if not url:
            raise ValueError(f"chưa có truyện thử cho {nen_tang} — chạy tao_thu trước")
    elif ten_trang not in NEN_TANG[nen_tang] or ten_trang == "dang_nhap":
        raise ValueError(f"trang {ten_trang!r} không có cho {nen_tang}")
    else:
        url = NEN_TANG[nen_tang][ten_trang]
    ra = GOC_HO_SO / "xem"
    ra.mkdir(parents=True, exist_ok=True)
    moc = time.strftime("%Y%m%d-%H%M%S")
    with sync_playwright() as p:
        ctx = _mo_trinh_duyet(p, nen_tang)
        trang = ctx.pages[0] if ctx.pages else ctx.new_page()
        trang.goto(url)
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
    che_do = {"mo": mo, "mo_chrome": mo_chrome, "tao_thu": tao_thu, "xem": xem,
              "ghi_nhap": ghi_nhap, "dang_hang_cho": dang_hang_cho}
    bon_doi_so = {"xem", "ghi_nhap", "tao_thu", "dang_hang_cho"}
    if (len(argv) not in (3, 4) or argv[1] not in che_do
            or (argv[1] not in bon_doi_so and len(argv) == 4)
            or (argv[1] == "ghi_nhap" and len(argv) != 4)):
        print(json.dumps({"loi": "cách gọi: dang_truyen_worker.py mo|mo_chrome|tao_thu <nền tảng>"
                                 " | xem <nền tảng> [trang] | ghi_nhap <nền tảng> <lần>"},
                         ensure_ascii=False))
        return 2
    kq = che_do[argv[1]](*argv[2:])
    print(json.dumps(kq, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
