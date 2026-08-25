# -*- coding: utf-8 -*-
"""do_test_lat_nguoc.py — cửa đo: bộ test `lat_nguoc` bắt được bao nhiêu lỗi gieo.

VÌ SAO CÓ TỆP NÀY, 25/08/2026:

`core/lat_nguoc.py` dài 547 dòng và có 0 test. Viết test cho nó là việc của hai
bên (xem hai bản giao cùng ngày). Nhưng "đã viết test" KHÔNG phải phép đo —
`tests/test_moi_nut_co_handler.js` sinh ra vì 624 test xanh suốt trong khi tám
lỗi đang tồn tại.

Thước ở đây: **gieo lỗi thật vào `core/lat_nguoc.py`, chạy bộ test, đếm xem
bao nhiêu lỗi làm test ĐỎ**. Test không làm đỏ được lỗi nào là test không hỏng
được, và cửa này in ra đúng con số ấy.

CÁCH DÙNG

    venv\\Scripts\\python.exe -X utf8 tools\\do_test_lat_nguoc.py            # toàn bộ
    venv\\Scripts\\python.exe -X utf8 tools\\do_test_lat_nguoc.py --thuan    # chỉ tầng thuần
    venv\\Scripts\\python.exe -X utf8 tools\\do_test_lat_nguoc.py --tich-hop # chỉ tầng tích hợp

MÃ THOÁT — theo luật ba trạng thái của kho:

    0   đạt ngưỡng
    1   ĐO ĐƯỢC mà KHÔNG đạt
    2   KHÔNG ĐO ĐƯỢC (thiếu tệp, gieo không ra đề nào)

Ngưỡng đăng ký TRƯỚC khi ai viết dòng test nào — xem `NGUONG` bên dưới.
"""
from __future__ import annotations

import argparse
import ast
import io
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.evidence_sprint.dung_de_loi import dot_bien  # noqa: E402

PY = str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe")
TEP_DICH = "core/lat_nguoc.py"
TEP_TEST = "tests/test_lat_nguoc.py"

# ==============================================================================
# NGƯỠNG — đăng ký 25/08/2026, TRƯỚC khi giao việc
# ==============================================================================
#
# ĐO NỀN (21 test neo do tôi viết, trước khi giao):
#
#     tầng thuần   : 19/30 trên chỗ 0–29
#     tầng tích hợp:  0/85 — chưa có test nào chạm tới
#
# Ngưỡng đặt theo TỈ LỆ chứ không theo số tuyệt đối, vì số chỗ gieo được đổi
# khi mã đổi. Đặt 0,85 cho tầng thuần: hàm thuần thì mọi nhánh đều gọi thẳng
# được, không viện cớ nào. Đặt 0,60 cho tầng tích hợp: mỗi test ở đó phải chép
# kho ra thư mục tạm và chạy pytest con, nên có những nhánh (hết trần giờ, xoá
# thư mục tạm hỏng) chỉ dựng lại được bằng cách giả lập — chấp nhận bỏ trống,
# nhưng phải NÓI RA chứ không lặng lẽ.
NGUONG = {"thuan": 0.85, "tich_hop": 0.60}

# Hàm nào thuộc tầng nào. Ranh giới là "có gọi tiến trình con không", không
# phải số dòng.
HAM_TICH_HOP = {"chay_e1_dinh_vi", "_chon_test_va_dong"}


def _ban_do_ham(ma: str) -> dict[int, str]:
    """{dòng (sau ast.unparse) -> tên hàm chứa nó}."""
    cay = ast.parse(ast.unparse(ast.parse(ma)))
    tam: dict[int, tuple[str, int]] = {}
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d2 = n.end_lineno or n.lineno
            rong = d2 - n.lineno
            for d in range(n.lineno, d2 + 1):
                if d not in tam or rong < tam[d][1]:
                    tam[d] = (n.name, rong)
    return {d: v[0] for d, v in tam.items()}


def _ham_cua_de(goc: str, moi: str, ban_do: dict[int, str]) -> str:
    """Lỗi gieo rơi vào hàm nào.

    KHÔNG tin trường `dong` của bộ gieo: nó đếm trên tệp GỐC, còn `ma` trả về
    đã qua `ast.unparse` nên số dòng lệch. Phải so hai bản unparse với nhau.
    """
    chuan = ast.unparse(ast.parse(goc)).splitlines()
    ml = ast.unparse(ast.parse(moi)).splitlines()
    for k, (a, b) in enumerate(zip(chuan, ml)):
        if a != b:
            return ban_do.get(k + 1, "(cấp module)")
    return "(không xác định)"


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thuan", action="store_true", help="chỉ đo tầng thuần")
    ap.add_argument("--tich-hop", action="store_true", help="chỉ đo tầng tích hợp")
    ap.add_argument("--toi-da", type=int, default=200, help="số chỗ gieo tối đa")
    tham_so = ap.parse_args()

    dich = PROJECT_ROOT / TEP_DICH
    tep_test = PROJECT_ROOT / TEP_TEST
    if not dich.is_file():
        print("KHÔNG ĐO ĐƯỢC: thiếu %s" % TEP_DICH)
        return 2
    if not tep_test.is_file():
        print("KHÔNG ĐO ĐƯỢC: thiếu %s — chưa ai viết test" % TEP_TEST)
        return 2

    goc = dich.read_text(encoding="utf-8")
    ban_do = _ban_do_ham(goc)

    chi_lay = None
    if tham_so.thuan and not tham_so.tich_hop:
        chi_lay = "thuan"
    elif tham_so.tich_hop and not tham_so.thuan:
        chi_lay = "tich_hop"

    de: list[tuple[int, str, str, str]] = []
    for i in range(tham_so.toi_da):
        moi, mo_ta = dot_bien(goc, i)
        if not moi:
            continue
        ham = _ham_cua_de(goc, moi, ban_do)
        tang = "tich_hop" if ham in HAM_TICH_HOP else "thuan"
        if chi_lay and tang != chi_lay:
            continue
        de.append((i, moi, mo_ta or "", ham))

    if not de:
        print("KHÔNG ĐO ĐƯỢC: không gieo được đề nào")
        return 2

    print("=" * 74)
    print("  CỬA: bộ test %s bắt được bao nhiêu lỗi gieo vào %s" % (TEP_TEST, TEP_DICH))
    print("  %d đề%s" % (len(de), "" if not chi_lay else " (chỉ tầng %s)" % chi_lay))
    print("=" * 74)

    t0 = time.monotonic()
    bat = 0
    lot: list[tuple[int, str, str]] = []
    for thu_tu, (i, moi, mo_ta, ham) in enumerate(de, 1):
        tam = Path(tempfile.mkdtemp(prefix="do_lat_"))
        try:
            for d in ("core", "tests", "experiments", "tools"):
                nguon_d = PROJECT_ROOT / d
                if nguon_d.is_dir():
                    shutil.copytree(nguon_d, tam / d)
            (tam / "pytest.ini").write_text("[pytest]\npythonpath = .\n", encoding="utf-8")
            (tam / TEP_DICH).write_text(moi, encoding="utf-8")
            r = subprocess.run(
                [PY, "-X", "utf8", "-m", "pytest", TEP_TEST, "-q", "--no-header", "-x"],
                cwd=tam, capture_output=True, text=True, timeout=300)
            do = r.returncode != 0
        except subprocess.TimeoutExpired:
            do = True                      # treo cũng là một dạng bị bắt
        finally:
            shutil.rmtree(tam, ignore_errors=True)
        bat += do
        if not do:
            lot.append((i, ham, mo_ta))
        print("  [%3d/%3d] %-26s %-30s %s"
              % (thu_tu, len(de), ham[:26], mo_ta[:30],
                 "ĐỎ" if do else "xanh — LỌT"))

    ty = bat / len(de)
    nguong = NGUONG[chi_lay] if chi_lay else min(NGUONG.values())
    print("-" * 74)
    print("  BẮT ĐƯỢC %d/%d = %.2f   ngưỡng >= %.2f   %s"
          % (bat, len(de), ty, nguong, "ĐẠT" if ty >= nguong else "TRƯỢT"))
    print("  %.1f giây" % (time.monotonic() - t0))
    if lot:
        print("-" * 74)
        print("  %d lỗi LỌT — đây là chỗ còn hở, không phải chỗ 'khó test':" % len(lot))
        for i, ham, mo_ta in lot:
            print("     mục %-3d %-26s %s" % (i, ham[:26], mo_ta[:34]))
    print("=" * 74)
    return 0 if ty >= nguong else 1


if __name__ == "__main__":
    sys.exit(main())
