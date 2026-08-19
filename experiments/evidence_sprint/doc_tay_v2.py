# -*- coding: utf-8 -*-
"""Bản 2 — luật chặt. Bản 1 đếm nhầm: 'replace'/'format'/'compile' là hàm sẵn
có của Python, còn 'sạch'/'Luật' là chữ tiếng Việt lọt qua regex bắt tên hàm.
Đọc tay 21 mục mới thấy. Đây đúng là bệnh "chấm bằng dò chuỗi con" lần thứ sáu.

Luật mới KHÔNG đoán từ chuỗi. Với mỗi tên mà bản vá thật dùng và tệp-được-xem
không có, đi TRA THẲNG cả kho ở bản sha xem nó được định nghĩa ở đâu:

  can_tra_kho     tên đó định nghĩa ở TỆP KHÁC trong repo
                  -> không model nào biết được; phải TRA KHO mới ra
  can_kien_thuc   tên đó của thư viện chuẩn / bên thứ ba (import mới)
                  -> hỏi model lớn hoặc tra tài liệu thì cứu được
  trong_vung      mọi thứ cần đều nằm trước mắt -> trượt vì HIỂU SAI
  ngoai_vung      hàm phải sửa không có trong vùng -> đề hỏng, bỏ
"""
from __future__ import annotations

import io, json, os, re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["doc_tay", "--lan=1"]
import do_delta as D                                            # noqa: E402
from doc_tay_that_bai import git, ham_bao, dong_da_doi          # noqa: E402

# doc_tay_that_bai bọc lại sys.stdout khi nạp -> bọc chồng, bản cũ bị đóng.
# Đặt lại SAU khi nạp xong, nếu không mọi print đều ném "closed file".
sys.stdout.reconfigure(encoding="utf-8")

DE = Path("D:/alpha_bench/de_sach.json")
KQ = Path("D:/alpha_bench/ket_qua_cloud.json")
RA = Path("D:/alpha_bench/doc_tay_v2.json")


def dinh_nghia_o_dau(repo: str, sha: str, ten: str, tru_tep: str) -> str:
    """Tên này được `def`/`class` ở tệp nào khác trong kho, tại bản sha?"""
    k = subprocess.run(
        ["git", "-C", repo, "grep", "-l", "-E", rf"^\s*(def|class)\s+{re.escape(ten)}\b",
         sha, "--", "*.py"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    for l in k.stdout.splitlines():
        tep = l.split(":", 1)[-1]
        if tep != tru_tep and "/tests/" not in tep and not tep.startswith("tests/"):
            return tep
    return ""


def main() -> int:
    de = {f"{d['sha'][:8]}:{d['nguon']}": d for d in json.loads(DE.read_text("utf-8"))}
    kq = next(iter(json.loads(KQ.read_text("utf-8")).values()))
    ra, dem = [], {"ngoai_vung": 0, "can_tra_kho": 0, "can_kien_thuc": 0, "trong_vung": 0}

    for khoa, r in kq.items():
        if r.get("trang_thai") != "truot" or khoa not in de:
            continue
        d = de[khoa]; repo, sha, ng = d["repo"], d["sha"], d["nguon"]
        diff = git(repo, "diff", f"{sha}~1..{sha}", "--", ng)
        ma_hong = git(repo, "show", f"{sha}~1:{ng}")
        if not diff or not ma_hong:
            continue
        can = ham_bao(ma_hong, dong_da_doi(diff))
        test_day = "\n\n".join(git(repo, "show", f"{sha}:{t}") for t in d["test"])
        vung = D.chon_vung(ma_hong, test_day)
        thieu = {h for h in can if h != "<cap_module>"
                 and not re.search(rf"\b(def|class)\s+{re.escape(h)}\b", vung)}
        if thieu:
            dem["ngoai_vung"] += 1
            ra.append({"de": khoa, "nhan": "ngoai_vung", "ham_thieu": sorted(thieu)})
            continue

        them = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        ma_them = "\n".join(them)
        nhap_du_an = [l.strip() for l in them
                      if re.match(r"\s*from\s+(core|interface|tools|skills|brains|agents)\b", l)]
        nhap_ngoai = [l.strip() for l in them
                      if re.match(r"\s*(import\s+\w|from\s+(?!core|interface|tools|skills|brains|agents)\w)", l)]
        # tên gọi trong phần thêm, bỏ tên do CHÍNH bản vá định nghĩa
        tu_dn = set(re.findall(r"^\s*(?:def|class)\s+(\w+)", ma_them, re.M))
        goi = {m for m in re.findall(r"\b([a-zA-Z_]\w{2,})\s*\(", ma_them)
               if m not in ma_hong and m not in tu_dn and m.isascii()}
        o_tep_khac = {g: t for g in sorted(goi) if (t := dinh_nghia_o_dau(repo, sha, g, ng))}

        if nhap_du_an or o_tep_khac:
            nhan = "can_tra_kho"
        elif nhap_ngoai:
            nhan = "can_kien_thuc"
        else:
            nhan = "trong_vung"
        dem[nhan] += 1
        ra.append({"de": khoa, "nhan": nhan, "tieu_de": d["tieu_de"],
                   "so_dong_sua": len(dong_da_doi(diff)),
                   "import_du_an": nhap_du_an[:3], "import_ngoai": nhap_ngoai[:3],
                   "ten_o_tep_khac": o_tep_khac})

    tong = sum(dem.values())
    print(f"\n  ===== {tong} luot TRUOT — vi sao =====\n")
    for k, v in dem.items():
        print(f"    {k:<16}{v:>3}   {100*v/max(tong,1):>3.0f}%")
    hl = tong - dem["ngoai_vung"]
    print(f"\n  De hop le: {hl}")
    print(f"    can TRA KHO (tep khac)    {dem['can_tra_kho']:>3}/{hl} = {100*dem['can_tra_kho']/max(hl,1):.0f}%")
    print(f"    can KIEN THUC chung       {dem['can_kien_thuc']:>3}/{hl} = {100*dem['can_kien_thuc']/max(hl,1):.0f}%")
    print(f"    HIEU SAI (du du kien)     {dem['trong_vung']:>3}/{hl} = {100*dem['trong_vung']/max(hl,1):.0f}%")
    RA.write_text(json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
