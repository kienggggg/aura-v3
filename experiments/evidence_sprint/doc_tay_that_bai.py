# -*- coding: utf-8 -*-
"""Bước 2: mở từng đề TRƯỢT ra đọc, phân loại vì sao trượt.

VÌ SAO CẦN: Sếp hỏi "hỏi đúng rồi có áp dụng được không". Muốn trả lời thì phải
biết 29 lượt trượt của Gemini hỏng vì THIẾU DỮ KIỆN hay vì HIỂU SAI BÀI — hai
bệnh này chữa bằng hai thứ khác hẳn nhau, và chỉ một trong hai cần "cho AI hỏi".

Cách làm KHÔNG gọi model lần nào: đề dựng bằng `checkout sha` rồi lùi một tệp
về `sha~1`, nên ĐÁP ÁN THẬT nằm sẵn trong `git diff sha~1..sha -- nguon`. Đọc
đáp án thật rồi đối chiếu với vùng mã đã đưa cho model.

Đây cũng chính là CỬA 4 đang thiếu: nếu hàm phải sửa không nằm trong vùng đưa
cho model thì đề đó KHÔNG AI LÀM ĐƯỢC — trượt không nói gì về model cả. Ghi lỗi
này vào cột model là đúng cái sai đã cho ra "Gemini 9%" trong khi thật là 33%.

NHÃN:
  ngoai_vung   hàm phải sửa không có trong vùng -> ĐỀ HỎNG, bỏ khỏi mọi tỉ lệ
  can_du_kien  bản vá thật thêm import / dùng tên không có sẵn trong tệp
               -> model có thể trượt vì KHÔNG BIẾT, hỏi thì cứu được
  trong_vung   mọi thứ cần đều nằm trước mắt -> trượt là do HIỂU SAI, hỏi vô ích
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["doc_tay", "--lan=1"]
import do_delta as D                                            # noqa: E402

DE = Path("D:/alpha_bench/de_sach.json")
KQ = Path("D:/alpha_bench/ket_qua_cloud.json")
RA = Path("D:/alpha_bench/doc_tay_that_bai.json")


def git(repo: str, *a: str) -> str:
    k = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return k.stdout


def ham_bao(ma: str, dong: set[int]) -> set[str]:
    """Tên hàm/lớp BAO các dòng đã đổi. Lấy nút TRONG CÙNG, không lấy lớp bao
    ngoài — lấy lớp thì một sửa đổi bất kỳ trong lớp 400 dòng cũng tính là
    'đúng chỗ', và cái sổ tự chấm điểm cho mình."""
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return set()
    ten: set[str] = set()
    for d in dong:
        trong = None
        for n in ast.walk(cay):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if n.lineno <= d <= (n.end_lineno or n.lineno):
                    if trong is None or n.lineno > trong.lineno:
                        trong = n
        ten.add(trong.name if trong else "<cap_module>")
    return ten


def dong_da_doi(diff: str) -> set[int]:
    """Dòng ở phía BẢN HỎNG (sha~1) mà bản vá chạm vào."""
    ra: set[int] = set()
    cur = 0
    for l in diff.splitlines():
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+", l)
        if m:
            cur = int(m.group(1))
            continue
        if l.startswith("-") and not l.startswith("---"):
            ra.add(cur); cur += 1
        elif l.startswith("+"):
            ra.add(max(cur - 1, 1))          # dòng thêm: gán vào chỗ chèn
        elif l.startswith(" "):
            cur += 1
    return ra


def main() -> int:
    de = {f"{d['sha'][:8]}:{d['nguon']}": d for d in json.loads(DE.read_text("utf-8"))}
    kq = json.loads(KQ.read_text("utf-8"))
    kq = next(iter(kq.values()))
    ra, dem = [], {"ngoai_vung": 0, "can_du_kien": 0, "trong_vung": 0, "khong_doc_duoc": 0}

    for khoa, r in kq.items():
        if r.get("trang_thai") != "truot":
            continue
        d = de.get(khoa)
        if not d:
            dem["khong_doc_duoc"] += 1
            continue
        repo, sha, ng = d["repo"], d["sha"], d["nguon"]
        diff = git(repo, "diff", f"{sha}~1..{sha}", "--", ng)
        ma_hong = git(repo, "show", f"{sha}~1:{ng}")
        if not diff or not ma_hong:
            dem["khong_doc_duoc"] += 1
            continue

        can = ham_bao(ma_hong, dong_da_doi(diff))
        # vùng mã ĐÚNG như đã đưa cho model
        test_day = "\n\n".join(git(repo, "show", f"{sha}:{t}") for t in d["test"])
        vung = D.chon_vung(ma_hong, test_day)
        thieu = {h for h in can
                 if h != "<cap_module>" and not re.search(rf"\b(def|class)\s+{re.escape(h)}\b", vung)}

        them = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        nhap_moi = [l.strip() for l in them if re.match(r"\s*(import |from )", l)]
        # tên gọi trong phần thêm mà tệp hỏng KHÔNG hề có -> phải biết từ ngoài
        goi = {m for l in them for m in re.findall(r"\b([A-Za-z_]\w{2,})\s*\(", l)}
        ngoai = sorted(g for g in goi if g not in ma_hong)

        if thieu:
            nhan = "ngoai_vung"
        elif nhap_moi or ngoai:
            nhan = "can_du_kien"
        else:
            nhan = "trong_vung"
        dem[nhan] += 1
        ra.append({"de": khoa, "nhan": nhan, "ham_phai_sua": sorted(can),
                   "ham_KHONG_co_trong_vung": sorted(thieu),
                   "so_dong_sua": len(dong_da_doi(diff)),
                   "import_moi": nhap_moi[:3], "ten_ngoai_tep": ngoai[:5],
                   "tieu_de": d["tieu_de"]})

    tong = sum(dem.values())
    print(f"\n  ===== {tong} luot TRUOT cua gemini-2.5-flash =====\n")
    for k, v in dem.items():
        print(f"    {k:<16}{v:>3}   {100*v/max(tong,1):>3.0f}%")
    kha = dem["can_du_kien"] + dem["trong_vung"]
    print(f"\n  De HOP LE (bo {dem['ngoai_vung']} de khong ai lam duoc): {kha}")
    if kha:
        print(f"    hoi nguoi khac CO THE cuu : {dem['can_du_kien']}/{kha} = "
              f"{100*dem['can_du_kien']/kha:.0f}%")
        print(f"    hoi VO ICH (hieu sai bai) : {dem['trong_vung']}/{kha} = "
              f"{100*dem['trong_vung']/kha:.0f}%")
    RA.write_text(json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  chi tiet tung de -> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
