# -*- coding: utf-8 -*-
"""Vòng HỎI CHUYÊN GIA cho Writer — và đo xem nó có thật sự làm văn hay hơn.

Ý của Sếp 19/08: hệ thống này là NGƯỜI THƯỜNG, gặp chỗ khó thì đi hỏi chuyên
gia. AURA viết truyện nhưng không biết hành văn của mình có giống người không
— nên đưa cho model mạnh xem, tiếp thu, sửa, rồi nộp lại hỏi đã tốt hơn chưa.

BỐN BƯỚC, và bước 4 là bước duy nhất đáng gọi là phép đo:

    1. lấy một đoạn văn AURA đã viết
    2. CLOUD đọc, chỉ ra 3 chỗ yếu           (chuyên gia)
    3. LOCAL sửa theo đúng ba chỗ đó         (người thường tiếp thu)
    4. CHẤM MÙ: cloud nhận HAI bản KHÔNG NHÃN, chọn bản hơn

CÁI BẪY BƯỚC 4 PHẢI TRÁNH: nếu đưa thẳng "đây là bản cũ, đây là bản tôi vừa
sửa, tốt hơn chưa?" thì câu trả lời gần như luôn là "tốt hơn" — model không có
mốc cố định và nó thiên vị bản mới nhất vừa nhìn. Nên giấu nhãn, và chấm MỖI
CẶP HAI LẦN với thứ tự đảo ngược: nếu nó chọn "bản đứng trước" cả hai lần thì
đó là thiên vị vị trí, không phải phán đoán về văn.

LUẬT CHẤM ĐẶT TRƯỚC KHI CHẠY (chép vào đây để không bẻ số sau khi thấy kết quả):

    bản SỬA thắng >= 7/10 lượt  ->  vòng này đáng giữ
    thắng 4-6/10                ->  ngang tung đồng xu, KHÔNG đáng giữ
    thắng <= 3/10               ->  vòng này làm văn TỆ ĐI
    hai lượt đảo thứ tự mà chọn cùng MỘT VỊ TRÍ  ->  lượt đó là thiên vị,
                                                     không tính vào tử số

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\vong_hoi_chuyen_gia.py
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GOC = Path(__file__).resolve().parent
RA = GOC.parent.parent / "data" / "evidence_sprint" / "hoi_chuyen_gia"
SO_TU_MAU = 400          # cắt đoạn cho vừa: sửa cả chương tốn 500 giây/lượt


def _env(tep: Path) -> dict:
    kv = {}
    for l in tep.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


E = _env(Path("D:/AURA_OS_v2/.env"))

# Đổi được nhà cung cấp bằng biến môi trường, không sửa cứng. Đo 19/08: tầng
# miễn phí Gemini chặn sau ĐÚNG 3 lượt gọi, và lùi 25/50/75 giây không gỡ —
# đó là trần THEO NGÀY, không phải theo phút. Một phép đo 15 lượt gọi vì thế
# phải chạy làm nhiều buổi, hoặc đổi sang cửa khác (ROUTER_* gom nhà cung cấp
# miễn phí, AURA_CHAT_* là cửa chat đang dùng).
_CUA = os.environ.get("HOI_CUA", "OPENAI").upper()
BASE = E[_CUA + "_BASE_URL"].rstrip("/")
KHOA = E[_CUA + "_API_KEY"]
CLOUD = os.environ.get("HOI_MODEL") or E.get(_CUA + "_MODEL", "gemini-2.5-flash")


def hoi_cloud(p: str, tran_token: int = 900) -> str:
    b = json.dumps({"model": CLOUD, "temperature": 0.2, "max_tokens": tran_token,
                    "messages": [{"role": "user", "content": p}]}).encode()
    for lan in range(4):
        try:
            r = urllib.request.Request(
                BASE + "/chat/completions", data=b, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + KHOA})
            with urllib.request.urlopen(r, timeout=300) as x:
                k = json.loads(x.read().decode())
            return (k["choices"][0]["message"].get("content") or "").strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and lan < 3:
                cho = 25 * (lan + 1)
                print(f"      HTTP {e.code}, chờ {cho}s", flush=True)
                time.sleep(cho)
                continue
            raise
    return ""


def hoi_local(p: str, tran: int = 1200) -> str:
    b = json.dumps({"model": "qwen3.5:4b", "prompt": p, "stream": False,
                    "think": False, "keep_alive": "10m",
                    "options": {"seed": 42, "temperature": 0.6,
                                "num_predict": tran, "num_ctx": 8192}}).encode()
    r = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                               method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=1800) as x:
        return (json.loads(x.read().decode()).get("response") or "").strip()


def lay_doan(f: Path) -> str:
    """Cắt ~400 từ, dừng ở cuối câu. Sửa cả chương 1.700 từ tốn ~500 giây/lượt
    trên máy này; đoạn 400 từ đủ để thấy hành văn mà rẻ hơn bốn lần."""
    chu = "\n".join(l for l in f.read_text(encoding="utf-8").splitlines()
                    if not l.startswith("#"))
    cau = [c for c in re.split(r"(?<=[.!?])\s+", chu) if c.strip()]
    gom, dem = [], 0
    for c in cau:
        n = len(c.split())
        if dem + n > SO_TU_MAU:
            break
        gom.append(c)
        dem += n
    return " ".join(gom)


def che_bai(doan: str) -> str:
    return hoi_cloud(
        "Bạn là biên tập viên văn học. Đọc đoạn văn tiếng Việt dưới đây và chỉ "
        "ra ĐÚNG BA chỗ yếu về HÀNH VĂN (không phải cốt truyện).\n"
        "Mỗi chỗ viết một dòng, bắt đầu bằng '- ', nói rõ yếu ở đâu và nên sửa "
        "theo hướng nào. Không viết lại đoạn văn.\n\n"
        "=== ĐOẠN VĂN ===\n" + doan)


def sua_theo(doan: str, che: str) -> str:
    ra = hoi_local(
        "Bạn là nhà văn. Biên tập viên đã chỉ ra ba chỗ yếu trong đoạn văn của "
        "bạn. Viết lại đoạn văn, sửa đúng ba chỗ đó.\n"
        "- Giữ nguyên nhân vật, bối cảnh và diễn biến.\n"
        "- Độ dài xấp xỉ bản cũ.\n"
        "- CHỈ trả về đoạn văn đã sửa, không giải thích, không tiêu đề.\n\n"
        "=== BA CHỖ YẾU ===\n" + che + "\n\n=== ĐOẠN VĂN CŨ ===\n" + doan)
    # Model hay dán thêm lời rào đầu/cuối. Bỏ dòng nào không phải văn xuôi.
    dong = [l for l in ra.splitlines()
            if l.strip() and not l.strip().startswith(("###", "**", "Đoạn văn",
                                                       "Bản sửa", "Dưới đây"))]
    return "\n".join(dong).strip()


def cham_mu(x: str, y: str) -> str:
    """Trả về 'A' hoặc 'B' — bản nào hành văn hơn. KHÔNG nói bản nào là bản sửa."""
    ra = hoi_cloud(
        "Bạn là giám khảo văn học. Dưới đây là hai đoạn văn tiếng Việt cùng nội "
        "dung, của hai người viết khác nhau. Đọc kỹ và chọn đoạn có HÀNH VĂN "
        "tốt hơn: tự nhiên hơn, ít sáo hơn, đọc cuốn hơn.\n"
        "Trả lời ĐÚNG MỘT chữ cái ở dòng đầu: A hoặc B. Dòng sau nói ngắn vì sao.\n\n"
        "=== ĐOẠN A ===\n" + x + "\n\n=== ĐOẠN B ===\n" + y, tran_token=300)
    m = re.search(r"\b([AB])\b", ra)
    return m.group(1) if m else "?"


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    nguon = [p for p in [
        GOC.parent.parent / "data/evidence_sprint/cham_mu/ban_A.md",
        GOC.parent.parent / "data/evidence_sprint/cham_mu/ban_B.md",
        GOC.parent.parent / "data/evidence_sprint/cham_mu/ban_C_chia_canh.md",
        GOC.parent.parent / "data/evidence_sprint/cham_mu/truyen_qwen35_4b.md",
        GOC.parent.parent / "data/evidence_sprint/runs/run_20260816_013302_412c0296/artifacts/ch03.md",
    ] if p.is_file()]
    print(f"  {len(nguon)} đoạn nguồn · chuyên gia={CLOUD} · thợ={'qwen3.5:4b'}\n")

    # NHỚ CHỖ ĐÃ LÀM. Trần hạn ngạch cắt ngang giữa chừng là chuyện thường ở
    # tầng miễn phí; không nhớ thì mỗi buổi lại đốt quota làm lại cặp cũ, và
    # phép đo 5 cặp không bao giờ xong.
    SO_TEP = RA / "ket_qua.json"
    so = json.loads(SO_TEP.read_text(encoding="utf-8")) if SO_TEP.is_file() else {
        "cap": [], "luat": "ban SUA phai thang >=7/10 luot moi dang giu"}
    da_lam = {c["nguon"] for c in so["cap"]}

    def _luu() -> None:
        tong = sum(1 for c in so["cap"] for k in ("lan1", "lan2")
                   if c[k] in ("moi", "cu") and not c["thien_vi"])
        so.update({
            "thang": sum(1 for c in so["cap"] for k in ("lan1", "lan2")
                         if c[k] == "moi" and not c["thien_vi"]),
            "thua": sum(1 for c in so["cap"] for k in ("lan1", "lan2")
                        if c[k] == "cu" and not c["thien_vi"]),
            "cap_thien_vi": sum(1 for c in so["cap"] if c["thien_vi"]),
            "tong_luot": tong})
        SO_TEP.write_text(json.dumps(so, ensure_ascii=False, indent=1),
                          encoding="utf-8")

    thang = thua = thien_vi = 0

    for i, f in enumerate(nguon, 1):
        if f.name in da_lam:
            print(f"  [{i}/{len(nguon)}] {f.name}  (đã đo buổi trước, bỏ qua)")
            continue
        doan = lay_doan(f)
        print(f"  [{i}/{len(nguon)}] {f.name}  ({len(doan.split())} từ)")
        t0 = time.monotonic()
        che = che_bai(doan)
        print(f"        chuyên gia chê xong ({time.monotonic()-t0:.0f}s)")
        t0 = time.monotonic()
        moi = sua_theo(doan, che)
        print(f"        thợ sửa xong {len(moi.split())} từ ({time.monotonic()-t0:.0f}s)")
        if len(moi.split()) < 60:
            print("        BỎ: bản sửa quá ngắn, không so được")
            continue

        (RA / f"{i}_cu.md").write_text(doan, encoding="utf-8")
        (RA / f"{i}_moi.md").write_text(moi, encoding="utf-8")
        (RA / f"{i}_che.md").write_text(che, encoding="utf-8")

        # Chấm HAI lần, đảo thứ tự. Cùng chọn một VỊ TRÍ = thiên vị vị trí.
        v1 = cham_mu(doan, moi)          # A=cũ  B=mới
        v2 = cham_mu(moi, doan)          # A=mới B=cũ
        chon1 = "moi" if v1 == "B" else ("cu" if v1 == "A" else "?")
        chon2 = "moi" if v2 == "A" else ("cu" if v2 == "B" else "?")
        if v1 == v2 and v1 in ("A", "B"):
            thien_vi += 1
            ket = f"THIEN VI VI TRI (cả hai lượt chọn {v1})"
        else:
            for c in (chon1, chon2):
                if c == "moi":
                    thang += 1
                elif c == "cu":
                    thua += 1
            ket = f"lượt 1 chọn {chon1}, lượt 2 chọn {chon2}"
        print(f"        chấm mù: {ket}\n")
        so["cap"].append({"nguon": f.name, "so_tu_cu": len(doan.split()),
                          "so_tu_moi": len(moi.split()),
                          "lan1": chon1, "lan2": chon2, "thien_vi": v1 == v2})
        _luu()          # lưu NGAY sau mỗi cặp, không đợi hết vòng

    _luu()
    thang, thua = so["thang"], so["thua"]
    thien_vi, tong = so["cap_thien_vi"], so["tong_luot"]
    print("  ===== KẾT QUẢ =====")
    print(f"    đã đo {len(so['cap'])}/{len(nguon)} cặp")
    print(f"    bản SỬA thắng : {thang}/{tong}")
    print(f"    bản CŨ  thắng : {thua}/{tong}")
    print(f"    cặp thiên vị  : {thien_vi} (không tính vào tử số)")
    if tong:
        tl = 100 * thang / tong
        print(f"\n    tỉ lệ {tl:.0f}%  ->  ", end="")
        print("ĐÁNG GIỮ" if tl >= 70 else
              ("NGANG TUNG ĐỒNG XU, không đáng giữ" if tl >= 40 else "LÀM VĂN TỆ ĐI"))
    if len(so["cap"]) < len(nguon):
        print(f"\n  CHƯA ĐỦ SỐ: mới {len(so['cap'])}/{len(nguon)} cặp. Kết luận ở "
              f"trên CHƯA đọc được — chạy lại khi hạn ngạch mở, nó tự đo tiếp.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
