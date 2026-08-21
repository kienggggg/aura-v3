# -*- coding: utf-8 -*-
"""E1 — LẬT NGƯỢC: máy thử từng chỗ, test phán quyết. KHÔNG GỌI MODEL.

VÌ SAO — 20/08/2026. Năm AI (Antigravity · DeepSeek · ChatGPT · Qwen ×2 · GLM)
được hỏi cùng một câu và **hội tụ vào cùng một câu trả lời**:

    Đừng đọc assertion một cách thụ động. Hãy chủ động lật ngược từng chỗ
    rồi để chính test đỏ làm oracle nhân quả.

Chỗ tôi bỏ sót: assertion đỏ là tín hiệu **quan sát**. Nhưng hệ thống này có
quyền **chạy chương trình nhiều lần** — mà tôi chưa dùng quyền ấy để định vị.

Ba tính chất làm bài toán này gần như may đo cho cách ấy:

    biết có ĐÚNG MỘT lỗi
    biết lỗi thuộc ĐÚNG 5 phép
    mỗi phép có ĐÚNG MỘT phép nghịch      <- hệ số phân nhánh = 1

Nên "64,8 hằng số ứng viên" KHÔNG có nghĩa model phải chọn 1 trong 64,8. Máy thử
tuần tự 64,8 phép lật, mỗi phép một lần chạy test. Ngu ngốc nhưng chắc chắn.

ĐIỂM META PHẢI GHI TRƯỚC (GLM nêu, và nó đúng):

    Nếu phép đo này đạt 8-9/9 thì bộ đề `de_loi.json` KHÔNG CÒN ĐO NĂNG LỰC
    MODEL với lớp lỗi này — một script vài trăm dòng chạm trần. Câu hỏi đổi
    từ "model có vượt nền 2/9 không" thành "model có hơn script không".

    Đó là một kết quả, không phải một thất bại. Ghi ra trước để sau không ai
    đọc con số cao rồi tưởng model giỏi lên.

NGƯỠNG TÔI ĐẶT LẦN ĐẦU LÀ SAI, ghi lại để không ai lặp:

    Tôi đặt ">= 8/9 bắt đúng chỗ gieo" cho phép lật MỘT chỗ. Bất khả thi ngay
    từ đầu: bộ 9 đề có 1 · 2 · 3 lỗi mỗi đề, mà lật một chỗ thì đề 2-3 lỗi
    không bao giờ xanh được. Trần của lật-một-chỗ là 3/9.
    Năm AI đều giả định "đúng một đột biến" — đúng với mô tả tôi gửi họ, nhưng
    tôi gửi thiếu chi tiết đề gộp 1/2/3 lỗi. Lỗi mô tả của tôi.

    Sửa: lật NHIỀU VÒNG THAM LAM — đúng cách lỗi được gieo (độc lập từng chỗ).
    Vòng 1 lật một chỗ; chỗ nào làm lỗi ĐỔI CHỮ KÝ thì giữ lại rồi lật tiếp.

NGƯỠNG ĐẶT TRƯỚC (gộp từ đề nghị của năm AI, chọn mức nghiêm nhất):

    kiểm nhiễu   test đỏ chạy 2 lần trên bản đã gieo phải ĐỎ cả 2, 9/9
                 lệch thì sửa harness trước, chưa đo gì cả

    ĐẠT     chỗ gieo thật nằm trong tập lật-thành-XANH  >= 8/9
            và có ít nhất một bản vá xanh CẢ BỘ          >= 7/9
    XÁM     chỗ gieo thật bắt được 6..7/9
    ĐÓNG    chỗ gieo thật bắt được <= 5/9

    riêng nhóm HẰNG (13/29 đề, chỗ cẩm nang thua nhất):
    ĐẠT >= 11/13 · ĐÓNG <= 8/13

Ghi thêm ba trạng thái cho mỗi phép lật, không gộp (ChatGPT nêu):

    2  test đỏ -> XANH            (sửa được nhân quả)
    1  lỗi ĐỔI chữ ký             (có tác động, chưa sửa hết)
    0  lỗi y nguyên               (không tác động)
   -1  làm test đang XANH -> đỏ   (phạt)

    .venv... venv\\Scripts\\python.exe -X utf8 experiments\\evidence_sprint\\do_lat_nguoc.py [so_de]
"""
from __future__ import annotations

import ast
import collections
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(NHA))

from dung_de_loi import chay_test, dot_bien            # noqa: E402

PY = str(GOC / "venv" / "Scripts" / "python.exe")
RA = GOC / "data" / "evidence_sprint" / "lat_nguoc.json"

# Phép NGHỊCH của đúng 5 phép gieo. Mỗi chỗ có ĐÚNG MỘT phép nghịch.
NGHICH_SS = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
             ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


class _Lat(ast.NodeTransformer):
    """Lật ĐÚNG MỘT chỗ, chỉ số `muc`. Đếm theo cùng thứ tự với `DotBien`."""

    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.da = ""

    def _lay(self, ten: str) -> bool:
        d = self.dem
        self.dem += 1
        if d == self.muc:
            self.da = ten
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            if self._lay("so sánh %s" % type(n.ops[0]).__name__):
                n.ops = [NGHICH_SS[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay("logic %s" % type(n.op).__name__):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định"):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay("bool %s" % n.value):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            # gieo là n -> n+1, nên NGHỊCH là n -> n-1
            if self._lay("số %d" % n.value):
                return ast.Constant(value=n.value - 1)
        return n


def _chen_not(cay: ast.AST, muc: int) -> tuple[str, str]:
    """Phép nghịch của 'bỏ phủ định' là CHÈN `not` — chỗ gieo đã mất dấu vết.

    Chỉ chèn ở ngữ cảnh boolean (`if`/`while`/`assert`/toán hạng and-or), không
    bọc mọi biểu thức: bọc bừa thì tập ứng viên nổ mà phần lớn không hợp nghĩa.
    """
    cho = []

    class _Tim(ast.NodeVisitor):
        def visit_If(self, n):
            cho.append(("test", n))
            self.generic_visit(n)

        def visit_While(self, n):
            cho.append(("test", n))
            self.generic_visit(n)

        def visit_BoolOp(self, n):
            for i, v in enumerate(n.values):
                cho.append(("values%d" % i, n))
            self.generic_visit(n)

    _Tim().visit(cay)
    if muc >= len(cho):
        return "", ""
    truong, nut = cho[muc]
    if truong == "test":
        nut.test = ast.UnaryOp(op=ast.Not(), operand=nut.test)
    else:
        i = int(truong[6:])
        nut.values[i] = ast.UnaryOp(op=ast.Not(), operand=nut.values[i])
    return ast.unparse(ast.fix_missing_locations(cay)), "chèn not #%d" % muc


def _chu_ky(loi: str) -> str:
    """Chữ ký lỗi — để phân biệt 'lỗi ĐỔI' với 'lỗi y nguyên'."""
    e = [l.strip() for l in loi.splitlines() if l.strip().startswith("E ")]
    return re.sub(r"\s+", " ", e[0])[:160] if e else re.sub(r"\s+", " ", loi)[-160:]


def _so_cho(ma: str) -> int:
    """Bao nhiêu chỗ lật được — đếm bằng chính bộ duyệt sẽ dùng để lật."""
    d = _Lat(-1)
    d.visit(ast.parse(ma))
    return d.dem


def mot_de(tam: Path, d: dict) -> dict:
    tep, tep_test = d["tep"], d["tep_test"]
    f = tam / tep
    goc = f.read_text(encoding="utf-8")
    ma, mo = dot_bien(goc, set(d["cho"]))
    if not ma:
        return {"trang_thai": "khong_do_duoc"}
    f.write_text(ma, encoding="utf-8")
    try:
        # KIỂM NHIỄU: đỏ hai lần thì mới tin là đỏ
        m1, loi1 = chay_test(tam, tep_test)
        m2, _ = chay_test(tam, tep_test)
        if m1 == 0 or m2 == 0:
            return {"trang_thai": "khong_do_duoc", "vi_sao": "test không đỏ ổn định"}
        goc_ky = _chu_ky(loi1)

        # BẢN GỐC là đáp án: lật đúng chỗ gieo phải khôi phục nguyên văn.
        chuan = ast.unparse(ast.parse(goc))

        n_cho = _so_cho(ma)
        t0 = time.monotonic()
        n_chay = [0]

        def mot_vong(nguon: str, ky_nen: str):
            """Lật từng chỗ một lượt. Trả (danh sách xanh, danh sách đổi chữ ký)."""
            xanh_, doi_ = [], []
            n = _so_cho(nguon)
            for i in range(n):
                try:
                    bd = _Lat(i)
                    moi = ast.unparse(ast.fix_missing_locations(
                        bd.visit(ast.parse(nguon))))
                except Exception:
                    continue
                if moi == nguon:
                    continue
                f.write_text(moi, encoding="utf-8")
                n_chay[0] += 1
                mt, lt = chay_test(tam, tep_test)
                if mt == 0:
                    xanh_.append({"chi_so": i, "phep": bd.da, "ma": moi})
                elif _chu_ky(lt) != ky_nen:
                    doi_.append({"chi_so": i, "phep": bd.da, "ma": moi,
                                 "ky": _chu_ky(lt)})
            return xanh_, doi_

        # THAM LAM NHIỀU VÒNG: vòng 1 lật một chỗ; chưa xanh thì giữ lại những
        # chỗ làm lỗi ĐỔI CHỮ KÝ (có tác động nhân quả) rồi lật tiếp trên đó.
        # Chặn trần TRAN_CHAY để không nổ chi phí trên đề 3 lỗi.
        TRAN_CHAY = 700
        RONG = 4                       # giữ tối đa 4 nhánh mỗi vòng
        xanh, doi_ky = mot_vong(ma, goc_ky)
        y_nguyen = n_cho - len(xanh) - len(doi_ky)
        loi_ap = 0
        vong = 1
        bien = [(ma, goc_ky)]
        while not xanh and vong < d["so_loi"] and n_chay[0] < TRAN_CHAY:
            vong += 1
            bien_moi = []
            for nh in doi_ky[:RONG]:
                if n_chay[0] >= TRAN_CHAY:
                    break
                x2, d2 = mot_vong(nh["ma"], nh["ky"])
                if x2:
                    xanh = x2
                    break
                bien_moi += d2[:RONG]
            if xanh:
                break
            doi_ky = bien_moi
        giay_lat = time.monotonic() - t0
        for x in xanh:
            x["khoi_phuc_goc"] = x.get("ma") == chuan

        # chỉ những bản vá làm test đỏ xanh mới đáng chạy CẢ BỘ
        ca_bo = []
        for x in xanh:
            f.write_text(x["ma"], encoding="utf-8")
            r = subprocess.run([PY, "-X", "utf8", "-m", "pytest", "tests", "-q",
                                "--no-header", "-p", "no:cacheprovider"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=str(tam), timeout=900)
            if r.returncode == 0:
                ca_bo.append(x)
        return {
            "trang_thai": "do_duoc", "mo_ta_gieo": mo.split(":", 1)[-1].strip(),
            "so_cho_lat": n_cho, "so_xanh": len(xanh),
            "so_doi_chu_ky": len(doi_ky), "so_y_nguyen": y_nguyen,
            "loi_ap": loi_ap, "so_xanh_ca_bo": len(ca_bo),
            "so_vong": vong, "so_lan_chay_test": n_chay[0],
            "bat_dung_cho_gieo": any(x["khoi_phuc_goc"] for x in xanh),
            "giay_lat": round(giay_lat, 1),
            "xanh": [{k: v for k, v in x.items() if k != "ma"} for x in xanh[:8]],
        }
    finally:
        f.write_text(goc, encoding="utf-8")


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    loi = json.loads((NHA / "de_loi.json").read_text(encoding="utf-8"))["loi"]
    theo_tep: dict[str, list] = {}
    for x in loi:
        theo_tep.setdefault(x["tep"], []).append(x)
    import random
    rng = random.Random(19082026)      # Y HỆT do_sua_loi.py, để cùng 9 đề
    de = []
    for tep, ds in theo_tep.items():
        for so_loi in (1, 2, 3):
            if len(ds) >= so_loi:
                de.append({"tep": tep, "tep_test": ds[0]["tep_test"],
                           "cho": [x["cho"] for x in rng.sample(ds, so_loi)],
                           "so_loi": so_loi})
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    de = de[:n]

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    ra = []
    print("  %d đề · KHÔNG GỌI MODEL · máy lật từng chỗ, test phán quyết\n" % len(de))
    try:
        for d in de:
            t0 = time.monotonic()
            r = mot_de(tam, d)
            r.update({"tep": d["tep"], "so_loi": d["so_loi"],
                      "giay": round(time.monotonic() - t0, 1)})
            ra.append(r)
            RA.parent.mkdir(parents=True, exist_ok=True)
            RA.write_text(json.dumps(ra, ensure_ascii=False, indent=1),
                          encoding="utf-8")
            print("  %-22s %d lỗi  %3s chỗ  %2s xanh  %2s đổi chữ ký  "
                  "%s cả bộ  bắt đúng chỗ: %-5s %4.0fs"
                  % (d["tep"].split("/")[-1][:22], d["so_loi"],
                     r.get("so_cho_lat", "-"), r.get("so_xanh", "-"),
                     r.get("so_doi_chu_ky", "-"), r.get("so_xanh_ca_bo", "-"),
                     r.get("bat_dung_cho_gieo"), r["giay"]))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    ok = [x for x in ra if x["trang_thai"] == "do_duoc"]
    bat = sum(1 for x in ok if x["bat_dung_cho_gieo"])
    ca_bo = sum(1 for x in ok if x.get("so_xanh_ca_bo", 0) > 0)
    print("\n" + "=" * 64)
    print("  E1 — LẬT NGƯỢC, KHÔNG MODEL")
    print("=" * 64)
    print("  nền: model viết lại cả hàm 2/9 · model chọn đúng thẻ 1/9")
    print("  bắt đúng chỗ gieo         : %d/%d" % (bat, len(ok)))
    print("  có bản vá xanh CẢ BỘ      : %d/%d" % (ca_bo, len(ok)))
    if ok:
        print("  chỗ lật trung bình        : %.0f" % (sum(x["so_cho_lat"] for x in ok) / len(ok)))
        print("  bản vá làm test đỏ xanh   : %.1f trung bình" % (sum(x["so_xanh"] for x in ok) / len(ok)))
        print("  bản vá làm lỗi ĐỔI chữ ký : %.1f trung bình" % (sum(x["so_doi_chu_ky"] for x in ok) / len(ok)))
        print("  thời gian                 : %.0f phút cả %d đề"
              % (sum(x["giay"] for x in ra) / 60, len(ra)))
    print()
    if bat >= 8:
        print("  ĐẠT (>= 8/9). VÀ: bộ đề này không còn đo năng lực model với lớp")
        print("  lỗi này — một script chạm trần. Phải ghi vào sổ.")
    elif bat >= 6:
        print("  XÁM (6..7/9) — xem phép `chèn not`, tập chèn có thể còn hở")
    else:
        print("  ĐÓNG (<= 5/9)")
    print("  sổ: %s" % RA)
    return 0 if bat >= 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
