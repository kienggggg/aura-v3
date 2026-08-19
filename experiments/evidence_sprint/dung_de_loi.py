# -*- coding: utf-8 -*-
"""Dựng đề bằng cách GÂY LỖI có kiểm soát — 1, 2, 3 lỗi mỗi đề.

Sếp chốt 19/08 bốn thứ cho vòng đo tới:
    1. có test đo được cột "LÀM ĐÚNG VIỆC", không chỉ "gọi đúng hàm"
    2. đọc suy luận model ở mỗi lần chọn
    3. không đòi đúng ngay lượt đầu — đo XONG SAU BAO NHIÊU LƯỢT
    4. phân cấp đề theo SỐ LỖI, và tăng dần cỡ khay, xem model xử ra sao
    5. có trần thử sai

Bốn thứ đó đòi một hình dạng đề khác hẳn "viết hàm dùng thẻ": phải là **mã
hỏng sẵn N lỗi, sửa cho test xanh**. Ở hình dạng này:
    - test của KHO làm cân, do người viết, không phải tôi bịa cho vừa ý
    - số lỗi đếm được -> phân cấp được
    - sửa rồi chạy test -> thử lại được, đếm được số lượt

GÂY LỖI BẰNG MÁY, KHÔNG BẰNG TAY. Tay thì tôi vô thức chọn lỗi dễ hoặc lỗi
hợp giả thuyết của mình. Máy đột biến theo luật cố định, đọc từ cây cú pháp:

    doi_so_sanh    <  ->  <=      ==  ->  !=
    doi_hang_so    n   ->  n+1    (số nguyên)
    doi_logic      and ->  or
    bo_phu_dinh    not X ->  X
    doi_true_false True -> False

CỬA XÁC MINH — một đột biến chỉ thành ĐỀ khi:
    a) trước khi sửa: test ĐỎ        (nếu xanh thì đột biến vô hại, bỏ)
    b) sau khi hoàn nguyên: test XANH (chứng minh đúng chỗ đó gây đỏ)
Không có hai cửa này thì sinh ra một đống đề không ai giải được — đúng lỗi
28/38 đề bất khả thi hồi 18/08.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\dung_de_loi.py
"""
from __future__ import annotations

import ast
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GOC = Path(__file__).resolve().parent.parent.parent
RA = Path(__file__).resolve().parent / "de_loi.json"
PY = str(GOC / "venv" / "Scripts" / "python.exe")

# mô-đun -> tệp test của nó. Chỉ lấy chỗ có test RIÊNG, chạy nhanh.
CAP = [
    ("core/may_tinh.py", "tests/test_may_tinh.py"),
    ("core/web_search.py", "tests/test_web_search.py"),
    ("core/dong_ho.py", "tests/test_dong_ho.py"),
    ("core/loai_cau_hoi.py", "tests/test_loai_cau_hoi.py"),
    ("core/kiem_tien.py", "tests/test_kiem_tien.py"),
    ("core/doc_so_phien.py", "tests/test_doc_so_phien.py"),
    ("core/secret_guard.py", "tests/test_secret_guard.py"),
    ("core/user_memory.py", "tests/test_user_memory.py"),
]


class DotBien(ast.NodeTransformer):
    """Đổi những chỗ có số thứ tự nằm trong `muc_tieu`, TRONG MỘT LƯỢT DUYỆT.

    NHẬN MỘT TẬP, KHÔNG PHẢI MỘT SỐ — và đó là bản vá 19/08.

    Bản đầu chỉ đổi được một chỗ, nên muốn gieo 3 lỗi thì tôi gọi nó ba lần
    liên tiếp trên mã đã đột biến. Mà mỗi lần đột biến là cây cú pháp đổi:
    `bỏ phủ định` xoá hẳn một nút, nên mọi chỗ phía sau tụt số. Chỉ số của lỗi
    thứ hai và thứ ba vì thế trỏ vào chỗ khác — hoặc trỏ ra ngoài và đề thành
    `khong_do_duoc`.

    Đo được: đề 3 lỗi đầu tiên hỏng đúng vì chuyện này. Mà "phân cấp theo số
    lỗi" chính là trục Sếp muốn đo, nên hỏng ở đây là hỏng cả phép đo.

    Một lượt duyệt, đếm trên MỘT cây, đổi mọi chỗ trúng tập — không có chỉ số
    nào tụt được.
    """

    def __init__(self, muc_tieu: int | set[int]):
        self.muc_tieu = ({muc_tieu} if isinstance(muc_tieu, int)
                         else set(muc_tieu))
        self.dem = 0
        self.da_doi = ""
        self.danh_sach: list[str] = []

    def _lay(self, mo_ta: str) -> bool:
        hit = self.dem in self.muc_tieu
        if hit:
            self.da_doi = mo_ta
            self.danh_sach.append(f"chỗ {self.dem}: {mo_ta}")
        self.dem += 1
        return hit

    def visit_Compare(self, n):
        self.generic_visit(n)
        DOI = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
               ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
        if len(n.ops) == 1 and type(n.ops[0]) in DOI:
            if self._lay(f"so sánh {type(n.ops[0]).__name__}"):
                n.ops = [DOI[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay(f"logic {type(n.op).__name__}"):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định"):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay(f"True/False -> {not n.value}"):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and 0 <= n.value < 10000:
            if self._lay(f"hằng số {n.value} -> {n.value + 1}"):
                return ast.Constant(value=n.value + 1)
        return n


def dot_bien(nguon: str, muc_tieu: int | set[int]) -> tuple[str, str]:
    """Gieo lỗi ở TẤT CẢ các chỗ trong `muc_tieu`, một lượt duyệt duy nhất."""
    cay = ast.parse(nguon)
    d = DotBien(muc_tieu)
    moi = ast.fix_missing_locations(d.visit(cay))
    can = len({muc_tieu} if isinstance(muc_tieu, int) else set(muc_tieu))
    if len(d.danh_sach) != can:
        # Gieo thiếu thì KHÔNG trả về mã dở dang. Đề 2 lỗi mà chỉ gieo được 1
        # sẽ vào sổ dưới nhãn "2 lỗi" và làm hỏng đúng trục đang đo.
        return "", ""
    return ast.unparse(moi), " · ".join(d.danh_sach)


def chay_test(tam: Path, tep_test: str, tran: int = 180) -> tuple[int, str]:
    x = subprocess.run(
        [PY, "-X", "utf8", "-m", "pytest", tep_test, "-q", "--no-header",
         "-x", "-p", "no:cacheprovider"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(tam), timeout=tran)
    return x.returncode, (x.stdout or "")[-1200:]


def main() -> int:
    rng = random.Random(19082026)
    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    print("  chép kho ra chỗ tạm…")
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))
    shutil.copytree(GOC / "venv", tam / "venv", symlinks=True) if False else None

    de = []
    try:
        for tep, tep_test in CAP:
            f = tam / tep
            if not f.is_file() or not (tam / tep_test).is_file():
                print(f"  bỏ {tep}: thiếu tệp")
                continue
            goc_nguon = f.read_text(encoding="utf-8")

            ma, bao = chay_test(tam, tep_test)
            if ma != 0:
                print(f"  bỏ {tep}: test đã ĐỎ sẵn khi chưa đột biến")
                continue

            n_cho = ast.parse(goc_nguon)
            tong = DotBien(-1)
            tong.visit(n_cho)
            cho = list(range(tong.dem))
            rng.shuffle(cho)
            dat = 0
            for i in cho:
                if dat >= 4:                 # tối đa 4 lỗi dùng được mỗi tệp
                    break
                moi, mo_ta = dot_bien(goc_nguon, i)
                if not moi:
                    continue
                f.write_text(moi, encoding="utf-8")
                ma_do, bao_do = chay_test(tam, tep_test)
                f.write_text(goc_nguon, encoding="utf-8")
                if ma_do == 0:
                    continue                  # đột biến vô hại, không thành đề
                de.append({"tep": tep, "tep_test": tep_test, "cho": i,
                           "mo_ta": mo_ta, "loi_test": bao_do[-400:]})
                dat += 1
                print(f"    {tep:<28}chỗ {i:<4}{mo_ta:<28}test ĐỎ  ✓")
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    RA.write_text(json.dumps({
        "_vi_sao": "Đột biến MÁY sinh, mỗi đề đã qua hai cửa: đột biến làm test "
                   "ĐỎ, hoàn nguyên làm test XANH. Không có hai cửa này thì đẻ "
                   "ra đề không ai giải được — lỗi 28/38 hồi 18/08.",
        "loi": de}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  {len(de)} lỗi dùng được, trên {len({d['tep'] for d in de})} tệp")
    print(f"  -> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
