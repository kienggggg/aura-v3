# -*- coding: utf-8 -*-
"""Đo phòng Delta trên đề THẬT từ lịch sử git (do dung_de_alpha.py dựng).

Chấm bằng MÁY, không đọc mã bằng mắt:
    đạt = tệp test của đề chuyển ĐỎ -> XANH  VÀ  phần còn lại của bộ test vẫn XANH

Ba chỗ chống ăn gian, mỗi chỗ vì một cách gian cụ thể:
  1. CHỈ ghi đè tệp mã nguồn. Model trả về gì cho tệp test cũng vứt — cách gian
     dễ nhất là sửa/xoá test cho nó xanh.
  2. Cửa 3 chạy CẢ bộ test. Sửa liều một chỗ cho test này xanh mà làm hỏng chỗ
     khác thì trượt.
  3. Mỗi đề một bản clone riêng. Không có trạng thái nào rò từ đề trước sang.

Đề nào tệp nguồn dài hơn TRAN_CHU thì BỎ và ĐẾM RIÊNG — không nhét bừa vào ngữ
cảnh rồi coi là trượt. "Không đo được" phải khác "đo được mà không đạt"
(CLAUDE.md mục 4).

    venv\\Scripts\\python.exe experiments\\evidence_sprint\\do_delta.py [model...]
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# DELTA_BACKEND=llamacpp -> gọi llama-server (nhanh gấp 4 ở khâu nạp prompt).
# Không đặt -> Ollama, giữ nguyên đường cũ làm dự phòng.
BACKEND = os.environ.get("DELTA_BACKEND", "ollama")
LLAMA_URL = os.environ.get("DELTA_LLAMA_URL", "http://127.0.0.1:8088")

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # xem chú thích ở dung_de_alpha.py

# DELTA_DE / DELTA_KET_QUA: chay tren mot bo de khac va ghi ra tep khac.
# Can thiet vi ket qua truoc 18/08 do tren VUNG CAT HONG (28/38 de bat kha thi),
# khong duoc dung lai — nhung cung khong duoc xoa, no la bang chung cua loi.
DE = Path(os.environ.get("DELTA_DE") or "D:/alpha_bench/de_sach.json")
if not DE.exists():
    DE = Path("D:/alpha_bench/de.json")
SO = Path(os.environ.get("DELTA_KET_QUA") or "D:/alpha_bench/ket_qua.json")

_cv = sys.argv[1:]
# --lan=N: cho model xem test báo lỗi rồi sửa lại, tối đa N lần. --lan=1 là
# làm một phát. Chạy cả hai rồi so mới biết "thấy lỗi rồi sửa" có ăn thua không
# — đó là cách học DUY NHẤT chạy được trên máy không GPU, nên nó phải có số.
SO_LAN = next((int(a.split("=")[1]) for a in _cv if a.startswith("--lan=")), 1)
MODEL = [a for a in _cv if not a.startswith("--")] or ["qwen2.5-coder:7b"]

# ĐO ĐƯỢC 16/08 trên qwen2.5-coder:7b, num_ctx 16384:
#     nạp prompt 17,3 tok/s   ·   sinh ra 2,8 tok/s
# Nạp là chỗ nghẽn TÍNH TOÁN (không phải băng thông), nên cách duy nhất để
# nhanh hơn là ĐƯA ÍT CHỮ HƠN — không phải nới trần.
#
# Trần cũ 8.000 ký tự chỉ với tới 4/38 đề (trung vị 15.143). Nhưng nới trần mà
# vẫn bắt viết lại nguyên tệp thì tệp 22.402 ký tự = ~7.000 token đầu ra, ở
# 2,8 tok/s là 42 PHÚT cho một lần thử. Cả bộ 38 đề mất ~22 giờ.
#
# Nên đổi hai thứ cùng lúc:
#   vào  — chỉ VÙNG mà test chạm tới, không phải cả tệp
#   ra   — chỉ khối SEARCH/REPLACE, không phải cả tệp
# Còn ~2,7 giờ cho 38 đề.
TRAN_CHU = 40000           # chỉ để loại tệp khổng lồ; vùng mới là thứ giới hạn thật
TRAN_VUNG = 14000           # ký tự tối đa của phần mã đưa vào prompt
TRAN_TEST = 3000
TRAN_HOI = 900.0


def hoi(model: str, ten: str, ma: str, test: str, loi: str,
        lan_truoc: tuple[str, str] | None = None) -> tuple[float, str]:
    p = (
        "Bạn sửa lỗi trong mã Python. Test dưới đây đang ĐỎ.\n"
        f"Sửa MÃ NGUỒN ({ten}) cho test xanh. KHÔNG được sửa test.\n\n"
        "CÁCH TRẢ LỜI: viết lại TOÀN VĂN hàm cần sửa, từ dòng `def` tới hết "
        "thân hàm. Chỉ mã Python, không giải thích, không khối markdown.\n"
        "- Chỉ viết hàm nào bạn thực sự sửa, không chép lại cả tệp.\n"
        "- Hàm chưa có thì cứ viết mới, nó sẽ được thêm vào tệp.\n"
        "- Sửa được nhiều hàm thì viết lần lượt từng hàm.\n\n"
        f"=== MÃ NGUỒN ({ten}) ===\n{ma}\n"
        f"=== TỆP TEST ===\n{test}\n"
        f"=== TEST BÁO LỖI ===\n{loi}\n"
    )
    if lan_truoc:
        # Vòng thử lại: đưa BẢN SỬA HỎNG + lỗi THẬT của nó. Không tóm tắt lỗi,
        # không diễn giải — đưa nguyên văn pytest. Diễn giải là chỗ ta chen phán
        # đoán của mình vào rồi tưởng model tự nghĩ ra.
        p += (f"\n=== LẦN TRƯỚC BẠN TRẢ LỜI (KHÔNG ĂN) ===\n{lan_truoc[0]}\n"
              f"=== VÌ SAO KHÔNG ĂN ===\n{lan_truoc[1]}\n"
              "Đừng lặp lại cách đó. Sửa khác đi.\n")
    p += "=== TRẢ LỜI ===\n"
    # ĐO ĐƯỢC 17/08, cùng máy cùng model cùng lượng tử hoá, máy rảnh:
    #     nạp prompt   Ollama 18-19 t/s   ·   llama.cpp  76,0 t/s   (gấp 4,0x)
    #     sinh chữ     Ollama 4,4-4,6     ·   llama.cpp   4,0       (ngang nhau)
    # Nạp prompt là phần lớn chi phí ở đây (~3.500 token vào / ~300 ra), nên cả
    # lượt nhanh hơn ~2,1 lần. Chỗ nghẽn hoá ra là TRÌNH CHẠY, không phải phần
    # cứng — điều mà 11 giờ máy trước đó đã trả giá để biết.
    #
    # Đổi bằng biến môi trường chứ không đổi cứng: Ollama vẫn là đường dự phòng
    # khi llama-server không chạy.
    if BACKEND == "llamacpp":
        b = json.dumps({"model": model, "temperature": 0.2, "seed": 42,
                        "max_tokens": 3000,
                        "messages": [{"role": "user", "content": p}]}).encode()
        yc = urllib.request.Request(f"{LLAMA_URL}/v1/chat/completions", data=b,
                                    headers={"Content-Type": "application/json"},
                                    method="POST")
        t0 = time.monotonic()
        with urllib.request.urlopen(yc, timeout=TRAN_HOI) as r:
            kq = json.loads(r.read().decode())
        ra = (kq["choices"][0]["message"].get("content") or "").strip()
        return round(time.monotonic() - t0, 1), ra

    b = json.dumps({
        "model": model, "prompt": p, "stream": False,
        "think": False,          # thiếu dòng này là qwen3.5 trả về chuỗi rỗng
        "keep_alive": "10m",     # giữ model, tránh nạp lại 11-12s mỗi đề
        "options": {"seed": 42, "temperature": 0.2,
                    "num_predict": 3000, "num_ctx": 8192},
    }).encode()
    yc = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=b,
                                headers={"Content-Type": "application/json"},
                                method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(yc, timeout=TRAN_HOI) as r:
        kq = json.loads(r.read().decode())
    return round(time.monotonic() - t0, 1), (kq.get("response") or "").strip()


def cat_dong(s: str, tran: int) -> str:
    """Cắt theo ranh giới DÒNG, không cắt giữa ký tự."""
    if len(s) <= tran:
        return s
    return s[:tran].rsplit("\n", 1)[0] + "\n# … (cắt bớt) …\n"


def chon_vung(ma: str, test_text: str) -> str:
    """Chọn phần mã mà TEST chạm tới, thay vì đưa cả tệp.

    Nguyên tắc: chỉ đưa thứ model có quyền biết. Tên nào xuất hiện trong tệp
    test thì model được xem toàn văn hàm/lớp đó; phần đầu tệp (import, hằng)
    luôn giữ vì thiếu nó thì SEARCH/REPLACE không neo được.

    CỐ Ý KHÔNG dùng vị trí của lời giải thật để cắt vùng — làm thế là mách chỗ
    sửa, và con số đo ra sẽ đo nhầm sang "biết chỗ rồi thì sửa được không".
    """
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ma[:TRAN_VUNG]

    dong = ma.splitlines(keepends=True)
    # test_text phải là bản ĐẦY ĐỦ. Lần đầu em cắt nó ở 3.000 ký tự rồi mới
    # ast.parse — cắt mã Python giữa chừng thì đứt ngay giữa một chuỗi, và
    # 9/9 đề đầu chết bằng "unterminated string literal". Cắt là việc lúc đưa
    # vào lời nhắc, không phải lúc phân tích.
    ten_test: set[str] = set()
    try:
        cay_test = ast.parse(test_text) if test_text else None
    except SyntaxError:
        cay_test = None
    if cay_test is not None:
        for n in ast.walk(cay_test):
            if isinstance(n, ast.Name):
                ten_test.add(n.id)
            elif isinstance(n, ast.Attribute):
                ten_test.add(n.attr)

    dau = []          # phần module-level không phải def/class
    than: list[tuple[int, int, int]] = []   # (điểm ưu tiên, đầu, cuối)
    for nut in cay.body:
        d, c = nut.lineno - 1, (getattr(nut, "end_lineno", nut.lineno))
        if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            diem = 0 if nut.name in ten_test else 1
            if isinstance(nut, ast.ClassDef):     # lớp: xét cả tên phương thức
                if any(getattr(m, "name", None) in ten_test for m in nut.body):
                    diem = 0
            than.append((diem, d, c))
        else:
            dau.append((d, c))

    # THỨ TỰ QUAN TRỌNG — đây là chỗ đã hỏng suốt hai ngày (sửa 18/08/2026):
    # bản cũ đổ TOÀN BỘ mã cấp module vào trước rồi mới thêm hàm. Tệp thật
    # 15.000-25.000 ký tự, ngân sách cạn trước khi tới hàm đích, và hàm đích bị
    # bỏ IM LẶNG. Kết quả: 28/38 đề bất khả thi — hàm cần sửa không nằm trong
    # thứ model được xem. Mọi điểm 0 đo trước ngày này đều dính lỗi này.
    #
    # Giờ hàm mà TEST GỌI TỚI giành chỗ TRƯỚC và KHÔNG BAO GIỜ bị bỏ — thà
    # prompt dài hơn còn hơn ra một đề không có lời giải trong tầm nhìn.
    uu_tien = [(d, c) for diem, d, c in than if diem == 0]
    con_lai = [(d, c) for diem, d, c in than if diem != 0]

    phan = ["".join(dong[d:c]) for d, c in uu_tien]         # nhóm 0: LUÔN giữ
    da_dung = sum(len(x) for x in phan)

    for d, c in dau:                                        # rồi tới import/hằng
        khoi = "".join(dong[d:c])
        if da_dung + len(khoi) > TRAN_VUNG:
            continue
        phan.insert(0, khoi)
        da_dung += len(khoi)

    for d, c in con_lai:                                    # cuối: hàm không liên quan
        khoi = "".join(dong[d:c])
        if da_dung + len(khoi) > TRAN_VUNG:
            continue
        phan.append(khoi)
        da_dung += len(khoi)
    return chr(10).join(phan)


_SR = re.compile(
    r"<{5,}\s*SEARCH\s*\n(.*?)\n?={5,}\s*\n(.*?)\n?>{5,}\s*REPLACE", re.S)


def go_rao(s: str) -> str:
    """Model hay bọc markdown dù đã dặn không."""
    if "```" in s:
        khoi = s.split("```")
        than = max(khoi[1::2], key=len, default=s)
        d = than.splitlines()
        if d and d[0].strip().lower() in ("python", "py"):
            d = d[1:]
        return "\n".join(d).strip()
    return s.strip()


def _tim_nut(cay, ten: str):
    """Tìm def/class tên `ten` ở BẤT KỲ cấp nào (kể cả phương thức trong lớp)."""
    for nut in ast.walk(cay):
        if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and nut.name == ten:
            return nut
    return None


def ap_ham(ma_goc: str, tra_loi: str) -> tuple[str, str]:
    """Thay HÀM theo TÊN, thay vì bắt model chép lại mã cũ cho khớp.

    VÌ SAO ĐỔI: mẫu SEARCH/REPLACE trượt 5/5 lần thử qua hai lượt chạy, và
    trượt luôn cùng một kiểu — qwen2.5-coder:7b chép phần SEARCH từ TỆP TEST
    chứ không từ tệp nguồn ('from core.web_search import loc_menh_lenh',
    'gw._messages(...)'). Nới khớp thụt lề không cứu được, vì lỗi không nằm ở
    thụt lề mà ở chỗ model không phân biệt được hai mục trong lời nhắc.

    Cách này bỏ hẳn việc chép: model chỉ viết Python bình thường — toàn văn hàm
    đã sửa — còn việc tìm đúng chỗ mà thay là việc của MÁY, bằng AST. Đầu ra
    vẫn nhỏ (một hàm), nên vẫn giữ được lợi thế tốc độ.

    Hàm chưa có trong tệp thì NỐI VÀO CUỐI — đề loại `gay_import` cần đúng thế.
    """
    ma_moi = go_rao(tra_loi)
    if not ma_moi:
        return "", "câu trả lời rỗng"
    try:
        cay_moi = ast.parse(ma_moi)
    except SyntaxError as e:
        # Model hay viết một câu dẫn trước mã. Cắt từ dòng def/class/@ đầu tiên
        # rồi thử lại — đây là gỡ VĂN XUÔI, không phải sửa mã hộ. Nếu phần mã
        # thật sự sai cú pháp thì vẫn hỏng ở lần thử thứ hai này.
        dong = ma_moi.splitlines()
        d = next((i for i, l in enumerate(dong)
                  if l.startswith(("def ", "class ", "@", "async def "))), -1)
        if d < 0:
            return "", f"mã trả về sai cú pháp: {str(e)[:70]}"
        ma_moi = "\n".join(dong[d:])
        try:
            cay_moi = ast.parse(ma_moi)
        except SyntaxError as e2:
            return "", f"mã trả về sai cú pháp: {str(e2)[:70]}"
    dinh = [n for n in cay_moi.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if not dinh:
        return "", "câu trả lời không chứa def/class nào"

    dong_moi = ma_moi.splitlines(keepends=True)
    ra = ma_goc
    # IMPORT PHẢI ĐƯỢC NHẬN. Đo 18/08: 15/38 đề (39%) có bản vá THẬT thêm một
    # dòng import ở cấp module — `from core.web_search import loc_menh_lenh`
    # chẳng hạn. Bản cũ chỉ lấy def/class nên dòng đó rơi im lặng, và đề thành
    # BẤT KHẢ THI: model tra kho đúng, viết hàm đúng, gọi đúng tên, rồi chết vì
    # NameError. Không phép đo nào chỉ ra được — trạng thái vẫn là "truot",
    # đọc y hệt "model dốt". Chỉ lòi ra khi đọc sổ nóng từng lượt.
    ra = _them_import(ra, [n for n in cay_moi.body
                           if isinstance(n, (ast.Import, ast.ImportFrom))], dong_moi)
    for n in dinh:
        d = min([n.lineno] + [x.lineno for x in n.decorator_list]) - 1
        ra = _thay_ham(ra, n.name, "".join(dong_moi[d:n.end_lineno]))
    if ra == ma_goc:
        return "", "sửa xong mà tệp không đổi"
    try:
        ast.parse(ra)
    except SyntaxError as e:
        return "", f"vá xong tệp hỏng cú pháp: {str(e)[:60]}"
    return ra, ""


def _them_import(ma: str, nut: list, dong_moi: list[str]) -> str:
    """Chèn những import model viết thêm mà tệp chưa có.

    Chèn NGAY SAU khối import sẵn có, không chèn lên đầu tệp: `from __future__
    import annotations` bắt buộc phải là câu lệnh đầu tiên, và chuỗi tài liệu
    của module cũng phải đứng trước. Chèn bừa lên đầu là vá xong tệp hỏng cú
    pháp — đúng cái bẫy mà cửa `ast.parse(ra)` bên dưới sẽ bắt, nhưng bắt rồi
    thì đề vẫn hỏng.
    """
    if not nut:
        return ma
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ma
    da_co = {ast.unparse(n) for n in cay.body
             if isinstance(n, (ast.Import, ast.ImportFrom))}
    them = []
    for n in nut:
        txt = "".join(dong_moi[n.lineno - 1:n.end_lineno]).rstrip("\n")
        if ast.unparse(n) not in da_co and txt.strip():
            them.append(txt)
    if not them:
        return ma
    cuoi = 0
    for n in cay.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            cuoi = max(cuoi, n.end_lineno or n.lineno)
        elif isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
            cuoi = max(cuoi, n.end_lineno or n.lineno)      # chuỗi tài liệu
    dong = ma.splitlines(keepends=True)
    return "".join(dong[:cuoi]) + "\n".join(them) + "\n" + "".join(dong[cuoi:])


def _thay_ham(ma: str, ten: str, than: str) -> str:
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return ma
    nut = _tim_nut(cay, ten)
    dong = ma.splitlines(keepends=True)
    if nut is None:
        return ma.rstrip("\n") + "\n\n\n" + than.rstrip("\n") + "\n"
    d = min([nut.lineno] + [x.lineno for x in nut.decorator_list]) - 1
    # Phương thức trong lớp nằm thụt vào; model trả về ở cột 0. Không bù lại
    # thì vá xong ra IndentationError rồi bị chấm nhầm thành sửa sai.
    thut = _thut(dong[d])
    if thut:
        than = "".join((thut + l if l.strip() else l)
                       for l in than.splitlines(keepends=True))
    return ("".join(dong[:d]) + than.rstrip("\n") + "\n"
            + "".join(dong[nut.end_lineno:]))


def _thut(s: str) -> str:
    return s[:len(s) - len(s.lstrip())]


def _khop_mem(ma: str, tim: str) -> str:
    """Khớp bỏ qua khoảng trắng đầu/cuối MỖI DÒNG, giữ nguyên thụt lề của tệp.

    Đây KHÔNG phải đoán mò. Đoán mò là tự chọn chỗ sửa hộ model. Đây là khớp
    bỏ qua ĐỊNH DẠNG: dãy dòng phải trùng đúng thứ tự và đúng nội dung, chỉ
    tha thụt lề — thứ model 7B hay chép lệch nhất.

    Đo được: 3/3 đề đầu trượt ở khớp-tuyệt-đối, và cả ba đều trượt vì hình
    thức chứ không phải vì sửa sai.
    """
    dong_ma = ma.splitlines(keepends=True)
    can = [d.strip() for d in tim.strip().splitlines() if d.strip()]
    if not can:
        return ""
    goc = [d.strip() for d in dong_ma]
    for i in range(len(dong_ma) - len(can) + 1):
        if goc[i:i + len(can)] == can:
            return "".join(dong_ma[i:i + len(can)])
    return ""


def ap_sr(ma_goc: str, tra_loi: str) -> tuple[str, str]:
    """Áp khối SEARCH/REPLACE vào TOÀN BỘ tệp gốc.

    Trả (mã mới, lý do hỏng). Hai nấc khớp: đúng từng ký tự trước, rồi bỏ qua
    thụt lề. Không khớp được nấc nào thì BÁO HỎNG, không sửa hộ.
    """
    khoi = _SR.findall(tra_loi)
    if not khoi:
        return "", "không tìm thấy khối SEARCH/REPLACE nào"
    ra = ma_goc
    for tim, thay in khoi:
        if not tim.strip():
            return "", "khối SEARCH rỗng"
        if tim in ra:
            ra = ra.replace(tim, thay, 1)
            continue
        that = _khop_mem(ra, tim)
        if not that:
            gon = tim.strip().splitlines()[0][:60]
            return "", f"SEARCH không khớp tệp: {gon!r}"
        # Chỉnh lại thụt lề của phần thay theo đúng thụt lề tệp đang có, nếu
        # không thì vá xong ra IndentationError và bị chấm nhầm thành sửa sai.
        d_that, d_thay = _thut(that.splitlines()[0]), _thut(thay.splitlines()[0] if thay.strip() else "")
        if d_that != d_thay:
            bu = len(d_that) - len(d_thay)
            thay = "\n".join((d_that[:bu] + l) if bu > 0 else l[-bu:] if l[:-bu].strip() == "" else l
                             for l in thay.splitlines())
        ra = ra.replace(that, thay + ("\n" if that.endswith("\n") and not thay.endswith("\n") else ""), 1)
    if ra == ma_goc:
        return "", "sửa xong mà tệp không đổi"
    return ra, ""


def pytest_(py: str, tam: Path, muc: list[str], tran: int) -> tuple[int, str, set[str]]:
    # --ignore=tests/legacy: bắt buộc, trong đó có script gọi sys.exit() ở cấp
    # module. Thiếu nó thì cửa 3 treo tới hết trần rồi bị đọc nhầm thành "trượt".
    x = subprocess.run([py, "-X", "utf8", "-m", "pytest", *muc, "-q", "--no-header",
                        "-rf", "--ignore=tests/legacy", "-p", "no:cacheprovider"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(tam), timeout=tran)
    ra = x.stdout or ""
    do = {d.split()[1] for d in ra.splitlines()
          if d.startswith("FAILED ") and len(d.split()) > 1}
    return x.returncode, ra[-2500:], do


def mot_de(model: str, d: dict) -> dict:
    repo = Path(d["repo"])
    py = str(repo / "venv" / "Scripts" / "python.exe")
    goc = Path(tempfile.mkdtemp())
    tam = goc / "de"
    try:
        subprocess.run(["git", "clone", "-q", str(repo), str(tam)], check=True,
                       timeout=300)
        for a in (["checkout", "-q", d["sha"]],
                  ["checkout", "-q", f"{d['sha']}~1", "--", d["nguon"]]):
            subprocess.run(["git", "-C", str(tam), *a], capture_output=True,
                           timeout=120)

        f_nguon = tam / d["nguon"]
        ma = f_nguon.read_text(encoding="utf-8", errors="replace")
        if len(ma) > TRAN_CHU:
            return {"trang_thai": "khong_do_duoc", "vi_sao": f"nguồn {len(ma)} ký tự"}
        test_day = "\n\n".join((tam / t).read_text(encoding="utf-8", errors="replace")
                               for t in d["test"])
        vung = chon_vung(ma, test_day)          # phân tích trên bản ĐẦY ĐỦ
        test = cat_dong(test_day, TRAN_TEST)    # cắt theo DÒNG, chỉ để đưa vào prompt

        _, loi, _ = pytest_(py, tam, d["test"], 300)
        nen = set(d.get("do_nen") or ())      # test vốn đã đỏ ở lời giải thật
        tong_giay = 0.0
        truoc: tuple[str, str] | None = None
        sai_dd = ""
        for lan in range(1, SO_LAN + 1):
            giay, ra = hoi(model, d["nguon"], vung, test, loi, truoc)
            tong_giay += giay
            sua, hong = ap_ham(ma, ra)
            if hong:
                # Sai ĐỊNH DẠNG khác hẳn sai SUY LUẬN. Gộp hai thứ vào một chữ
                # "trượt" là làm hỏng chính con số muốn đo.
                sai_dd = hong
                truoc = (ra[:1500], f"Trả lời sai định dạng: {hong}")
                continue
            sai_dd = ""
            # CHỈ ghi tệp nguồn. Tệp test giữ nguyên bản của đề — cách gian dễ
            # nhất là sửa test cho nó xanh.
            f_nguon.write_text(sua, encoding="utf-8")
            try:
                m2, bao, _ = pytest_(py, tam, d["test"], 300)
                if m2 != 0:
                    them: set[str] = set()
                else:
                    _, ca_bo, do = pytest_(py, tam, ["tests"], 200)
                    # Cửa 3: KHÔNG đòi xanh tuyệt đối. Chỉ đòi không đỏ THÊM
                    # ngoài đỏ nền — repo này chưa bao giờ xanh tuyệt đối, đòi
                    # thế là loại oan cả commit tốt (đo được: 6/6 commit đầu).
                    them = do - nen
                    if them:
                        bao = ca_bo
            except subprocess.TimeoutExpired:
                return {"trang_thai": "khong_do_duoc", "vi_sao": "test treo",
                        "giay": round(tong_giay, 1)}
            if m2 == 0 and not them:
                return {"trang_thai": "dat", "lan_dat": lan,
                        "giay": round(tong_giay, 1)}
            truoc = (ra[:1500], bao[-1500:])
        if sai_dd:
            return {"trang_thai": "sai_dinh_dang", "giay": round(tong_giay, 1),
                    "vi_sao": sai_dd}
        return {"trang_thai": "truot", "lan_dat": 0, "giay": round(tong_giay, 1),
                "test_de": m2, "lam_do_them": sorted(them)[:5]}
    except Exception as e:                                       # noqa: BLE001
        return {"trang_thai": "khong_do_duoc",
                "vi_sao": f"{type(e).__name__}: {str(e)[:70]}"}
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    if not DE.exists():
        print(f"  chưa có {DE} — chạy dung_de_alpha.py trước")
        return 2
    de = json.loads(DE.read_text(encoding="utf-8"))
    print(f"  {len(de)} đề\n")

    so: dict = json.loads(SO.read_text(encoding="utf-8")) if SO.exists() else {}
    for model in MODEL:
        # Khoá kèm số lần thử VÀ trình chạy: kết quả 1 lần / 3 lần / Ollama /
        # llama.cpp KHÔNG được đè lên nhau, nếu không thì so sánh mất nghĩa.
        cot = f"{model}#lan{SO_LAN}" + ("#llamacpp" if BACKEND == "llamacpp" else "")
        print(f"=== {cot} ===")
        so.setdefault(cot, {})
        dat = truot = bo = sai = 0
        tong = 0.0
        dat_lan: dict[int, int] = {}
        for i, d in enumerate(de, start=1):
            # Khoá phải có CẢ tên tệp: một commit đẻ nhiều đề khác tệp (285472cd
            # có 3). Khoá bằng sha không thôi thì 16/38 đề đè mất nhau.
            khoa = f"{d['sha'][:8]}:{d['nguon']}"
            cu = so[cot].get(khoa)
            # KHÔNG dùng lại kết quả "không đo được" — đó là giàn giáo hỏng
            # (Ollama hết RAM, test treo), không phải phép đo. Dùng lại là đóng
            # băng lỗi của mình thành số liệu: đề 12 và 18 đã bị khoá đúng kiểu
            # đó, hết RAM một lần là vĩnh viễn không được chạy lại.
            if cu and cu.get("trang_thai") == "khong_do_duoc":
                cu = None
            r = cu or mot_de(model, d)
            so[cot][khoa] = r
            if r["trang_thai"] == "dat":
                dat_lan[r.get("lan_dat", 1)] = dat_lan.get(r.get("lan_dat", 1), 0) + 1
            SO.write_text(json.dumps(so, ensure_ascii=False, indent=2),
                          encoding="utf-8")     # ghi từng đề: cúp giữa chừng không mất
            t = r["trang_thai"]
            dat += t == "dat"
            truot += t == "truot"
            sai += t == "sai_dinh_dang"
            bo += t == "khong_do_duoc"
            tong += r.get("giay", 0.0)
            dau = {"dat": "✓", "truot": "✗", "sai_dinh_dang": "≠",
                   "khong_do_duoc": "·"}[t]
            print(f"  {dau} [{i:>2}/{len(de)}] {d['sha'][:8]} {d['nguon'][:30]:<30}"
                  f"{r.get('giay', 0):>6.1f}s  {r.get('vi_sao', '')}")
        # BỐN trạng thái tách rời, không gộp: "0/4" từng đọc y hệt "thua sạch"
        # trong khi cả 4 đều gãy ở chữ ký hàm (CLAUDE.md mục 4). "Sai định dạng"
        # cũng vậy — nó là model không theo được mẫu trả lời, KHÔNG phải model
        # không sửa được lỗi.
        do_duoc = dat + truot
        print(f"  -> ĐẠT {dat}/{do_duoc} đo được  ·  {sai} sai định dạng"
              f"  ·  {bo} không đo được  ·  tổng {tong:.0f}s")
        if SO_LAN > 1 and dat_lan:
            chi = "  ".join(f"lần {l}: {n}" for l, n in sorted(dat_lan.items()))
            print(f"     đạt ở  {chi}   (lần ≥2 = nhờ được xem test báo lỗi)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
