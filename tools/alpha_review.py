# -*- coding: utf-8 -*-
"""Alpha review — video phân tích dựng từ NGUỒN GHIM (`CHOT:alpha-review-vong-0`, 15/09/2026).

    python tools/alpha_review.py nguon      # lấy + làm sạch nguồn ghim, lưu kèm SHA-256
    python tools/alpha_review.py kich_ban   # model viết từng câu KÈM đoạn trích nguyên văn; máy dò
    python tools/alpha_review.py dung       # thẻ HTML -> ảnh, giọng, phụ đề, ghép, kiểm
    python tools/alpha_review.py tat_ca

Đề đầu tiên Sếp chọn: loạt phim Skibidi Toilet. KHÔNG dùng gì của phim (clip, ảnh nhân vật,
nhạc) — chủ phim đang đòi quyền (khiếu nại DMCA nhắm Garry's Mod, kiện một công ty ở Dubai 01/2025).

CHỐNG BỊA: mỗi câu kịch bản phải kèm một đoạn trích NGUYÊN VĂN ≥ 8 từ từ nguồn ghim, và máy tìm
đoạn ấy trong nguồn. Đoạn 8 từ trở lên thì không khớp nhầm vào giữa một từ khác — khác loại dò
chuỗi con đã ghi 8 lần trong SO_BENH_AN.md. Câu tiếng Việt có NÓI ĐÚNG như đoạn trích hay không
thì người đọc lại, không phải máy.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

DE = "skibidi_toilet"
THU_MUC = GOC / "data" / "alpha_review" / DE
NGUON = {
    "en": {"trang": "Skibidi_Toilet", "revid": 1374917295, "ngay": "14/09/2026",
           "api": "https://en.wikipedia.org/w/api.php"},
    "vi": {"trang": "Skibidi_Toilet", "revid": 74669391, "ngay": "12/01/2026",
           "api": "https://vi.wikipedia.org/w/api.php"},
}
# Luật robot của Wikimedia đòi User-Agent có LIÊN HỆ dạng URL. Đo 15/09/2026 bằng httpx: không đặt
# UA -> 403; UA có chữ nhưng không URL -> 403 "respect our robot policy"; UA mang URL repo -> 200.
# Dùng URL repo công khai, không dùng email của Sếp.
UA = {"User-Agent": "AURA-v3-alpha-review/0.1 (https://github.com/kienggggg/aura-v3)"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def lam_sach(html_trang: str) -> str:
    """HTML của một bản sửa Wikipedia -> văn bản thuần, mỗi đoạn một dòng.

    Giữ: các đoạn <p>, mục danh sách <li> trong thân bài, và các hàng hộp thông tin (Nhãn: Giá trị).
    Bỏ: chú thích [12], bảng khác, danh mục tham khảo. Đoạn trích của model so trên CHÍNH văn bản
    này, nên nó phải ổn định: cùng HTML vào thì cùng chữ ra.
    """
    h = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html_trang, flags=re.S)
    h = re.sub(r'<sup[^>]*class="[^"]*reference[^"]*"[^>]*>.*?</sup>', "", h, flags=re.S)
    h = re.sub(r'<ol class="references".*?</ol>', " ", h, flags=re.S)
    dong: list[str] = []
    for nhan, gia in re.findall(r'<th[^>]*class="infobox-label"[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>', h, re.S):
        dong.append(f"{_chu(nhan)}: {_chu(gia)}")
    than = re.sub(r"<table.*?</table>", " ", h, flags=re.S)
    for the, noi in re.findall(r"<(p|li)[^>]*>(.*?)</\1>", than, re.S):
        c = _chu(noi)
        if len(c.split()) >= 6:
            dong.append(c)
    return "\n".join(dong) + "\n"


def _chu(x: str) -> str:
    x = re.sub(r"<br\s*/?>", " ", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = html.unescape(x).replace("\xa0", " ")
    x = re.sub(r"\[\d+\]|\[[a-z]\]|\[citation needed\]", "", x)
    return re.sub(r"\s+", " ", x).strip()


def lay_nguon() -> dict:
    import httpx
    THU_MUC.mkdir(parents=True, exist_ok=True)
    kq = {}
    for ma, n in NGUON.items():
        r = httpx.get(n["api"], params={"action": "parse", "oldid": n["revid"], "prop": "text|revid",
                                        "format": "json", "formatversion": 2}, headers=UA, timeout=60)
        r.raise_for_status()
        d = r.json()["parse"]
        if d.get("revid") != n["revid"]:
            raise RuntimeError(f"{ma}: API trả bản {d.get('revid')}, cần {n['revid']}")
        tep = THU_MUC / f"nguon_{ma}.txt"
        tep.write_text(lam_sach(d["text"]), encoding="utf-8")
        kq[ma] = {"revid": n["revid"], "ngay": n["ngay"], "tep": tep.name, "sha256": _sha(tep),
                  "so_dong": len(tep.read_text(encoding="utf-8").splitlines()),
                  "url": f"https://{ma}.wikipedia.org/w/index.php?oldid={n['revid']}",
                  "giay_phep": "CC BY-SA 4.0"}
    (THU_MUC / "nguon.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


# ---- KỊCH BẢN ----------------------------------------------------------------------------------
# Dàn ý do MÁY đặt: mỗi ý một câu, một thẻ. Mỗi ý gắn với dòng nguồn chứa dữ kiện, chọn bằng từ
# khoá (không bằng số dòng — làm sạch đổi thì số dòng trôi). 12 ý -> 12 thẻ -> 11 lần đổi cảnh, trên
# sàn 8 của `kiem_video`. Model chỉ viết CÂU; nó không chọn ý, nên không nhảy ý (lỗi Sếp bắt ở bộ 1).
DAN_Y = [
    ("mo", "Mở đầu: con số lượt xem khổng lồ, nói kèm mốc thời gian nguồn ghi", "65 billion views", "Hiện tượng"),
    ("la_gi", "Loạt phim kể chuyện gì: bồn cầu có đầu người đánh nhau với người đầu camera, loa, tivi", "The series depicts a conflict", "Loạt phim là gì"),
    ("ai_lam", "Ai làm ra loạt phim", "is produced by Alexey Gerasimov", "Ai làm ra nó"),
    ("tap_dau", "Tập đầu tiên: ngày đăng và độ dài", "11-second runtime", "Tập đầu tiên"),
    ("bai_hat", "Bài hát trong phim: bản trộn không giấy phép, và chuyện khiếu nại năm 2024", "unlicensed mashup", "Bài hát"),
    ("nhip_dang", "Nhịp đăng dày lúc đầu, và vì sao nó giúp phim lan nhanh", "at least two videos weekly", "Nhịp đăng"),
    ("xep_hang", "Kênh lọt nhóm kênh YouTube xem nhiều nhất ở Mỹ", "50 most viewed YouTube channels", "Bảng xếp hạng"),
    ("khan_gia", "Khán giả chủ yếu là thế hệ Alpha", "audience is predominantly Generation Alpha", "Ai đang xem"),
    ("ke_chuyen", "Điểm lạ: kể cả một câu chuyện chỉ bằng video ngắn", "narrative entirely out of short-form videos", "Kể chuyện kiểu mới"),
    ("doc_sau", "Một cách đọc sâu hơn: nỗi sợ bị giám sát", "fear of surveillance", "Đọc sâu hơn"),
    ("tranh_chap", "Tranh chấp quyền và nhóm làm phim mới năm 2026", "new four-person creative team", "Ai giữ loạt phim"),
    ("ket", "Kết: dự án phim điện ảnh, hỏi người xem nghĩ gì", "in talks", "Chuyện sắp tới"),
]
SCHEMA = {"type": "object", "properties": {"cau": {"type": "string"}, "trich": {"type": "string"},
                                           "chu_lon": {"type": "string"}},
          "required": ["cau", "trich", "chu_lon"]}
THANG = {m: i for i, m in enumerate(("january february march april may june july august september "
                                     "october november december").split(), 1)}
TEN_RIENG = ("Skibidi Toilet YouTube TikTok Twitter Gerasimov Alexey DaFuq Boom Blugray Invisible Narratives "
             "Timbaland Universal Music Group UMG Tubefilter Washington Post Civilians Wired Insider Michael Bay "
             "Adam Goodman Virlance Strider FScript Achi Garry Mod Alpha Gen Slender Man G-Toilet CCTV Kids").split()
SO_LAN_THU = 3


def _chuan(s: str) -> str:
    s = (s or "").replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip()


def _so(s: str) -> set[str]:
    return {re.sub(r"[.,]", "", x) for x in re.findall(r"\d+(?:[.,]\d+)*", s or "")}


def kiem_cau(cau: str, trich: str, chu_lon: str, nguon: str) -> list[str]:
    """Lý do bác một câu; rỗng là đạt. HÀM THUẦN để cửa canh đưa câu xấu vào được."""
    from core.viet_truyen import chu_khong_phai_tieng_viet
    loi = []
    t = _chuan(trich).strip(" .\"'")
    if len(t.split()) < 8:
        loi.append(f"đoạn trích {len(t.split())} từ, cần ≥ 8")
    elif t not in _chuan(nguon):
        loi.append("đoạn trích KHÔNG có nguyên văn trong nguồn ghim")
    duoc = _so(trich) | {str(THANG[w]) for w in re.findall(r"[a-z]+", trich.lower()) if w in THANG}
    la = (_so(cau) | _so(chu_lon)) - duoc
    if la:
        loi.append(f"con số không có trong đoạn trích: {sorted(la)}")
    mien = set(re.findall(r"[A-Za-z]+", trich)) | set(TEN_RIENG)
    chu_anh = chu_khong_phai_tieng_viet(cau + " " + chu_lon, mien=mien)
    if chu_anh:
        loi.append(f"chữ không phải tiếng Việt: {' '.join(sorted(set(chu_anh)))[:60]}")
    n = len(cau.split())
    if not 10 <= n <= 30:
        loi.append(f"câu {n} từ, cần 10–30")
    if len(chu_lon.split()) > 6:
        loi.append(f"chữ lớn {len(chu_lon.split())} từ, cần ≤ 6")
    return loi


def _goi_model(loi_nhac: str, seed: int) -> dict:
    import httpx
    from core.viet_truyen import HOST, MODEL
    r = httpx.post(f"{HOST}/api/generate", json={
        "model": MODEL, "prompt": loi_nhac, "stream": False, "think": False, "format": SCHEMA,
        "options": {"temperature": 0.3, "seed": seed, "num_ctx": 4096}}, timeout=600)
    r.raise_for_status()
    return json.loads(r.json()["response"])


def viet_kich_ban() -> dict:
    nguon = (THU_MUC / "nguon_en.txt").read_text(encoding="utf-8")
    dong = nguon.splitlines()
    t0 = time.monotonic()
    ra, cau_truoc = [], ""
    for ma, y, khoa, nhan in DAN_Y:
        doan = [d for d in dong if khoa.lower() in d.lower()]
        if not doan:
            raise RuntimeError(f"ý {ma}: không thấy dòng nguồn chứa {khoa!r}")
        loi_nhac = (
            "Bạn viết MỘT câu tiếng Việt, 14–24 từ, cho video phân tích về loạt phim hoạt hình Skibidi Toilet.\n"
            f"Ý của câu này: {y}.\n"
            + (f"Câu ngay trước trong video: \"{cau_truoc}\" — câu của bạn phải nối tiếp tự nhiên, không lặp ý.\n"
               if cau_truoc else "Đây là câu mở đầu video.\n")
            + "CHỈ dùng thông tin có trong ĐOẠN NGUỒN tiếng Anh dưới đây. Không thêm con số hay chi tiết nào khác.\n"
            "Tên riêng giữ nguyên. Không dùng từ tiếng Anh nào khác.\n\n"
            f"ĐOẠN NGUỒN:\n{doan[0]}\n\n"
            "Trả về JSON:\n"
            "- \"cau\": câu tiếng Việt;\n"
            "- \"trich\": một đoạn CHÉP NGUYÊN VĂN từ ĐOẠN NGUỒN, 8–30 từ tiếng Anh, chứa đúng thông tin câu của bạn dùng;\n"
            "- \"chu_lon\": cụm tiếng Việt ngắn tối đa 5 từ để in to trên thẻ, ví dụ con số chính.")
        lan = []
        for k in range(SO_LAN_THU):
            t1 = time.monotonic()
            try:
                d = _goi_model(loi_nhac, seed=15 + k)
                loi = kiem_cau(d.get("cau", ""), d.get("trich", ""), d.get("chu_lon", ""), nguon)
            except Exception as e:  # noqa: BLE001 — model trả rác cũng là một lượt hỏng, không phải sập
                d, loi = {}, [f"{type(e).__name__}: {str(e)[:120]}"]
            lan.append({**d, "loi": loi, "giay": round(time.monotonic() - t1, 1)})
            if not loi:
                break
        dat = not lan[-1]["loi"]
        ra.append({"ma": ma, "nhan": nhan, "dat": dat, "lan": lan, **({k: lan[-1][k] for k in ("cau", "trich", "chu_lon")} if dat else {})})
        print(f"{ma:11} {'DAT' if dat else 'KHONG DAT'} sau {len(lan)} lan · {lan[-1].get('cau', '')[:90]}", flush=True)
        if dat:
            cau_truoc = lan[-1]["cau"]
    kq = {"trang_thai": "DAT" if all(x["dat"] for x in ra) else "KHONG_DAT", "y": ra,
          "giay": round(time.monotonic() - t0, 1)}
    (THU_MUC / "kich_ban.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


if __name__ == "__main__":
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:] or ["nguon"]
    if a[0] == "nguon":
        print(json.dumps(lay_nguon(), ensure_ascii=False, indent=1))
    elif a[0] == "kich_ban":
        kq = viet_kich_ban()
        print(json.dumps({"trang_thai": kq["trang_thai"], "giay": kq["giay"]}, ensure_ascii=False))
    else:
        sys.exit(__doc__)
