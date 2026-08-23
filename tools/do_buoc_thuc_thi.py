r"""Đếm số BƯỚC thực thi thật của một mô-đun khi chạy test của nó.

21/08/2026. Kế hoạch "Mạch Nước Ngầm" đặt trần `max_steps = 1000` trước khi có
dòng mã nào. Đo ra thì 3 trong 4 đề lỗi đơn vượt trần:

    web_search.py     15.298 bước   (vượt 15x)
    may_tinh.py        4.318 bước   (vượt  4x)
    loai_cau_hoi.py    2.273 bước   (vượt  2x)
    dong_ho.py            48 bước   lọt

Trần vỡ vì đang đếm CẢ TỆP test (40-49 test một tệp). Lúc gỡ lỗi chỉ có MỘT
test đỏ. Đếm theo từng test thì trung vị còn 36-123 bước, ca xấu nhất 3.974 —
nên trần 5.000 với phạm vi MỘT TEST là đủ, còn dư khoảng.

    venv\Scripts\python.exe -X utf8 tools\do_buoc_thuc_thi.py            # cả tệp
    venv\Scripts\python.exe -X utf8 tools\do_buoc_thuc_thi.py --moi-test  # từng test

CHỈ đếm dòng thuộc mô-đun đang xét. Trace cả stdlib + pytest thì số nở hàng
trăm lần và trần nào cũng vô nghĩa.
"""
from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
PY = str(GOC / "venv" / "Scripts" / "python.exe")
TRAN_KE_HOACH = 1000

# Chạy trong tiến trình con: settrace không sống qua pytest.main() gọi lồng.
KICH_CA_TEP = '''
import sys, time, pathlib
muc = str(pathlib.Path(sys.argv[1]).resolve())
dem = [0]
def theo(frame, ev, arg):
    if ev == "line" and frame.f_code.co_filename == muc:
        dem[0] += 1
    return theo
import pytest
t0 = time.monotonic()
sys.settrace(theo)
try:
    pytest.main(["-q", "-p", "no:cacheprovider", sys.argv[2]])
finally:
    sys.settrace(None)
print("KETQUA %d %.2f" % (dem[0], time.monotonic() - t0))
'''

KICH_MOI_TEST = '''
import sys, pathlib
muc = str(pathlib.Path(sys.argv[1]).resolve())
dem = [0]; ke = {}
def theo(frame, ev, arg):
    if ev == "line" and frame.f_code.co_filename == muc:
        dem[0] += 1
    return theo
class Ghi:
    def pytest_runtest_setup(self, item):
        dem[0] = 0
        sys.settrace(theo)
    def pytest_runtest_teardown(self, item):
        sys.settrace(None)
        ke[item.name] = dem[0]
import pytest
pytest.main(["-q", "-p", "no:cacheprovider", sys.argv[2]], plugins=[Ghi()])
v = sorted(ke.values())
if v:
    print("KETQUA %d %d %d %d" % (len(v), v[-1], v[int(len(v) * 0.9) - 1], v[len(v) // 2]))
'''


def cap_mo_dun() -> dict[str, str]:
    """Mô-đun -> tệp test, lấy từ chính bộ đề lỗi của evidence_sprint."""
    p = GOC / "experiments" / "evidence_sprint" / "de_loi.json"
    loi = json.loads(p.read_text(encoding="utf-8"))["loi"]
    cap: dict[str, str] = {}
    for x in loi:
        cap.setdefault(x["tep"], x["tep_test"])
    return cap


def chay(kich: str, mod: str, tt: str) -> list[str] | None:
    tam = GOC / "_do_buoc_tam.py"
    tam.write_text(kich, encoding="utf-8")
    try:
        r = subprocess.run([PY, "-X", "utf8", str(tam), mod, tt],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, cwd=str(GOC))
    except subprocess.TimeoutExpired:
        return None
    finally:
        tam.unlink(missing_ok=True)
    for d in (r.stdout or "").splitlines():
        if d.startswith("KETQUA"):
            return d.split()[1:]
    return None


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    moi_test = "--moi-test" in sys.argv
    cap = cap_mo_dun()

    if moi_test:
        print("SỐ BƯỚC THEO TỪNG TEST — phạm vi đúng của một lần gỡ lỗi")
        print()
        print("  %-20s %8s %8s %8s %9s" % ("mô-đun", "số test", "max", "p90", "trung vị"))
        tat_ca_max = 0
        for mod, tt in cap.items():
            k = chay(KICH_MOI_TEST, mod, tt)
            if not k:
                print("  %-20s  không đo được" % mod.split("/")[-1][:20])
                continue
            n, mx, p90, tv = (int(x) for x in k)
            tat_ca_max = max(tat_ca_max, mx)
            print("  %-20s %8d %8d %8d %9d"
                  % (mod.split("/")[-1][:20], n, mx, p90, tv))
        print()
        print("  ca xấu nhất cả kho: %d bước -> trần 5.000 là đủ" % tat_ca_max)
        return 0 if tat_ca_max <= 5000 else 1

    print("SỐ BƯỚC KHI CHẠY CẢ TỆP TEST — trần kế hoạch: %d" % TRAN_KE_HOACH)
    print()
    print("  %-20s %-26s %11s %8s" % ("mô-đun", "tệp test", "bước", "giây"))
    vuot = tong = 0
    for mod, tt in cap.items():
        k = chay(KICH_CA_TEP, mod, tt)
        if not k:
            print("  %-20s  không đo được" % mod.split("/")[-1][:20])
            continue
        b, g = int(k[0]), k[1]
        tong += 1
        if b > TRAN_KE_HOACH:
            vuot += 1
        print("  %-20s %-26s %11d %8s  %s"
              % (mod.split("/")[-1][:20], tt.split("/")[-1][:26], b, g,
                 "VƯỢT" if b > TRAN_KE_HOACH else ""))
    print()
    if not tong:
        print("  KHÔNG ĐO ĐƯỢC")
        return 2
    print("  vượt trần %d: %d/%d mô-đun" % (TRAN_KE_HOACH, vuot, tong))
    return 1 if vuot else 0


if __name__ == "__main__":
    raise SystemExit(main())
