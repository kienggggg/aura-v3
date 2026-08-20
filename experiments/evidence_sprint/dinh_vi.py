# -*- coding: utf-8 -*-
"""Định vị hàm hỏng bằng MÁY, không hỏi model.

Ba AI (Antigravity, Qwen, GPT) đọc số 2/9 đều xếp hướng này hạng nhất, và họ
nói cùng một điều: đừng bắt model 7B vừa TÌM lỗi vừa SỬA lỗi. Máy tìm, model
sửa.

VÌ SAO TRACEBACK KHÔNG ĐỦ — đo 19/08 trên đề thật:

    tests/test_may_tinh.py:42: AssertionError

Traceback KHÔNG có khung nào của mã nguồn. Lỗi đột biến phần lớn là assertion
sai trên giá trị trả về, không phải ngoại lệ, nên ngăn xếp dừng ngay trong tệp
test. Nó chỉ cho biết HÀM CỬA VÀO (`tinh_giup`), còn lỗi thật nằm sâu hơn.

Nên phải theo dấu lúc CHẠY. Kho không có `coverage`, nhưng `sys.settrace` là
thư viện chuẩn — bộ dò dưới đây không cần cài gì.

CÁCH LÀM: chạy đúng test đỏ dưới bộ dò, ghi lại mọi hàm CỦA TỆP NGUỒN thực sự
được gọi. Đó là tập nghi ngờ. Hàm không hề chạy thì không thể gây đỏ.

CÁI NÓ KHÔNG LÀM ĐƯỢC: xếp hạng trong tập ấy. Muốn xếp hạng phải so với các
test XANH (hàm nào chỉ chạy ở test đỏ thì đáng ngờ hơn) — làm được, nhưng để
sau; bước này đo trước xem thu hẹp ngữ cảnh có ăn không.

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\dinh_vi.py
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

BO_DO = r'''
import json, sys
from pathlib import Path
import pytest

DICH = str(Path(sys.argv[1]).resolve())
BO = {"<module>", "<genexpr>", "<lambda>", "<listcomp>", "<dictcomp>", "<setcomp>"}
THAY = []
DONG = set()
_da = set()

# MỨC DÒNG, không chỉ mức hàm.
#
# Đo 19/08: xếp hạng theo hàm ra RIÊNG ĐỎ = 0 ở cả ba tệp — không hàm nào chỉ
# chạy khi đỏ. Đó không phải bộ xếp hạng hỏng, mà là tính chất của lớp lỗi:
# đổi `<` thành `<=`, lật True/False, đổi hằng số đều KHÔNG tạo đường đi mới.
# Cùng hàm, cùng luồng, chỉ khác GIÁ TRỊ ở một chỗ.
#
# Muốn tách thì phải xuống mức DÒNG: cùng một hàm, dòng nào chỉ test đỏ chạm
# tới. Muốn nhận sự kiện `line` thì hàm dò phải TRẢ VỀ CHÍNH NÓ cho khung
# thuộc tệp đích — trả `None` là Python thôi theo dõi bên trong khung ấy.
def _theo(frame, event, arg):
    f = frame.f_code
    if f.co_filename != DICH:
        return None
    if event == "call":
        if f.co_name not in _da and f.co_name not in BO:
            _da.add(f.co_name)
            THAY.append(f.co_name)
        return _theo          # theo dõi tiếp BÊN TRONG khung này
    if event == "line":
        DONG.add(frame.f_lineno)
    return _theo

sys.settrace(_theo)
try:
    cv = [sys.argv[2], "-q", "--no-header", "-p", "no:cacheprovider"]
    if len(sys.argv) > 4 and sys.argv[4]:
        cv += ["-k", sys.argv[4]]
    ma = pytest.main(cv)
finally:
    sys.settrace(None)
Path(sys.argv[3]).write_text(
    json.dumps({"ham": THAY, "dong": sorted(DONG), "ma_thoat": int(ma)}),
    encoding="utf-8")
'''


def test_do_nao(repo: Path, tep_test: str, py: str, tran: int = 240) -> list[str]:
    """Mã định danh của những test ĐANG ĐỎ (`tệp::tên[tham số]`)."""
    x = subprocess.run(
        [py, "-X", "utf8", "-m", "pytest", tep_test, "-q", "--no-header",
         "-rf", "--tb=no", "-p", "no:cacheprovider"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(repo), timeout=tran)
    ra = []
    for l in (x.stdout or "").splitlines():
        if not l.startswith("FAILED "):
            continue
        m = l.split(" ", 1)[1].strip()
        # CẮT TÓM TẮT LỖI. Cờ `-rf` in ra `FAILED <mã test> - AssertionEr...`,
        # và bản đầu lấy nguyên cả cụm làm mã test. pytest báo `no tests ran`,
        # mã thoát 4, bộ dò trả về 0 hàm — mà tôi đọc thành "test không gọi
        # hàm nào", rồi đi sửa nhầm chỗ khác (tưởng do tên tham số hoá).
        m = m.split(" - ", 1)[0].strip()
        # BỎ PHẦN [tham số]: pytest thoát mã Unicode trong tên tham số hoá
        # (`bao nhi\xeau ng\xe0y`) nên chuỗi ấy không khớp ngược lại được.
        # Bỏ ngoặc thì chạy cả nhóm tham số — rộng hơn chút, nhưng KHỚP ĐƯỢC.
        ra.append(m.split("[", 1)[0])
    # giữ thứ tự, bỏ trùng
    thay, kq = set(), []
    for m in ra:
        if m not in thay:
            thay.add(m)
            kq.append(m)
    return kq


def ham_da_chay(repo: Path, tep_nguon: str, muc_test: str,
                py: str, tran: int = 240, loc: str = "",
                lay_dong: bool = False):
    """Hàm nào của `tep_nguon` thực sự chạy khi chạy `muc_test`.

    `muc_test` phải là MỘT test đỏ cụ thể, không phải cả tệp. Bản đầu truyền
    cả tệp test nên các test chạy TRƯỚC test đỏ cũng bị tính, và tập nghi ngờ
    phình ra — thu hẹp chỉ còn 56-66%, gần như vô ích.
    """
    bo = repo / "_bo_do_tam.py"
    ra = repo / "_bo_do_ra.json"
    bo.write_text(BO_DO, encoding="utf-8")
    try:
        subprocess.run([py, "-X", "utf8", str(bo), str(repo / tep_nguon),
                        muc_test, str(ra), loc],
                       capture_output=True, cwd=str(repo), timeout=tran)
        if not ra.is_file():
            return ([], []) if lay_dong else []
        d = json.loads(ra.read_text(encoding="utf-8"))
        return (d.get("ham", []), d.get("dong", [])) if lay_dong else d.get("ham", [])
    except subprocess.TimeoutExpired:
        return ([], []) if lay_dong else []
    finally:
        bo.unlink(missing_ok=True)
        ra.unlink(missing_ok=True)


def xep_hang_ham(repo: Path, tep_nguon: str, tep_test: str,
                 py: str) -> tuple[list[str], list[str]]:
    """Xếp hạng hàm nghi ngờ bằng cách SO test đỏ với test XANH.

    Bản trước chỉ lấy "hàm nào test đỏ chạy qua". Đo 19/08: 2/9 -> 2/9, không
    nâng được gì. Lý do: `may_tinh` vẫn nhận 4 hàm và 66% mã — hàm nào cũng
    chạy nên "có chạy" không phân biệt được gì.

    Thứ phân biệt được là SO SÁNH: hàm chạy ở test đỏ mà KHÔNG hề chạy ở test
    xanh thì rất đáng ngờ — nếu nó đúng, test xanh đã phải chạm tới nó.

        RIÊNG ĐỎ  = chạy khi đỏ, không chạy khi xanh   <- nghi phạm chính
        CHUNG     = chạy ở cả hai                       <- hạng hai

    Chỉ tốn HAI lượt dò, không phải dò từng test: gom hết test đỏ vào một
    lượt, hết test xanh vào lượt kia.
    """
    do = test_do_nao(repo, tep_test, py)
    if not do:
        return [], []
    ten_do = sorted({m.rsplit("::", 1)[-1] for m in do})

    # lượt 1: chỉ chạy test ĐỎ
    bieu_do = " or ".join(ten_do)
    f_do = ham_da_chay(repo, tep_nguon, tep_test, py, loc=bieu_do)
    # lượt 2: chỉ chạy test XANH (loại hết test đỏ ra)
    bieu_xanh = " and ".join(f"not {t}" for t in ten_do)
    f_xanh = ham_da_chay(repo, tep_nguon, tep_test, py, loc=bieu_xanh)

    rieng = [h for h in f_do if h not in set(f_xanh)]
    chung = [h for h in f_do if h in set(f_xanh)]
    return rieng, chung


def cat_ham(nguon: str, ten: list[str]) -> str:
    """Cắt lấy đúng những hàm được nêu, kèm phần import/hằng ở đầu tệp.

    Giữ phần đầu vì hàm hay dùng hằng số và biểu thức chính quy khai ở cấp
    mô-đun; cắt trụi thì model không đọc nổi.
    """
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return nguon
    dong = nguon.splitlines()
    can = set(ten)

    dau = []
    for n in cay.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        dau.append("\n".join(dong[n.lineno - 1:(n.end_lineno or n.lineno)]))

    than = []
    for n in cay.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in can:
            d = n.lineno - 1
            # kéo cả decorator lên
            if n.decorator_list:
                d = min(d, n.decorator_list[0].lineno - 1)
            than.append("\n".join(dong[d:(n.end_lineno or n.lineno)]))
    if not than:
        return nguon
    return "\n".join(dau) + "\n\n" + "\n\n".join(than) + "\n"


def _thu() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    import shutil
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from dung_de_loi import dot_bien

    GOC = Path(__file__).resolve().parent.parent.parent
    py = str(GOC / "venv" / "Scripts" / "python.exe")
    loi = json.loads((Path(__file__).resolve().parent / "de_loi.json")
                     .read_text(encoding="utf-8"))["loi"]

    tg = Path(tempfile.mkdtemp())
    tam = tg / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".git", "__pycache__", "data", "_rac", "*.pyc"))
    try:
        for tep in ("core/may_tinh.py", "core/web_search.py", "core/dong_ho.py"):
            d = next((x for x in loi if x["tep"] == tep), None)
            if not d:
                continue
            f = tam / tep
            goc = f.read_text(encoding="utf-8")
            ma, mo_ta = dot_bien(goc, {d["cho"]})
            f.write_text(ma, encoding="utf-8")
            rieng, chung = xep_hang_ham(tam, tep, d["tep_test"], py)
            ham = rieng or chung
            cat = cat_ham(ma, ham)
            tong = len([n for n in ast.parse(ma).body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
            f.write_text(goc, encoding="utf-8")
            print(f"  {tep}")
            print(f"    tệp có {tong} hàm")
            print(f"    RIÊNG ĐỎ ({len(rieng)}): {rieng[:6]}")
            print(f"    chung   ({len(chung)}): {chung[:6]}")
            print(f"    mã đưa model: {len(ma)} -> {len(cat)} ký tự "
                  f"({100*len(cat)/len(ma):.0f}%)")
            print()
    finally:
        shutil.rmtree(tg, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(_thu())
