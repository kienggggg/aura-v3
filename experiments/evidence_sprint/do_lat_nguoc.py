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
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

NHA = Path(__file__).resolve().parent
GOC = NHA.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(NHA))

from dung_de_loi import chay_test, dot_bien            # noqa: E402

PY = str(GOC / "venv" / "Scripts" / "python.exe")
RA = GOC / "data" / "evidence_sprint" / "lat_nguoc.json"

# Khóa trước khi chạy ngày 22/08/2026: dựng đúng bốn đề lỗi đơn của sổ E1 cũ.
# True = phải có bản vá xanh cả bộ và khôi phục đúng mã; False = phải trượt.
MOC_E1_MOT_LOI = {
    "core/may_tinh.py": True,
    "core/web_search.py": True,
    "core/dong_ho.py": True,
    "core/loai_cau_hoi.py": False,
}

# Không chỉ khóa tên tệp/verdict: khóa cả đúng đột biến đã tạo sổ 21/08.
# Nếu mã nguồn hoặc de_loi.json trôi, phép đo phải dừng thay vì lặng lẽ đổi đề.
DAU_VET_E1_MOT_LOI = {
    "core/may_tinh.py": {
        "tep_test": "tests/test_may_tinh.py", "cho": [55],
        "sha256": "5af334da017929928c4883e83c0e3a0fb94e64f66abd1949d7a7a1be21ac4db5",
    },
    "core/web_search.py": {
        "tep_test": "tests/test_web_search.py", "cho": [78],
        "sha256": "cbf424d3acdf418e89aeb12037dd034468af1eadc77bb787a0cbdc0b3ebe528e",
    },
    "core/dong_ho.py": {
        "tep_test": "tests/test_dong_ho.py", "cho": [0],
        "sha256": "c104b5c2cda397caf7bb53db0f1486e53037bc4bf24e5d24c5f8cd75a2a76857",
    },
    "core/loai_cau_hoi.py": {
        "tep_test": "tests/test_loai_cau_hoi.py", "cho": [3],
        "sha256": "07166b72ee344d1f381c163534358e56d057f7aaafbf1d500ea7cc32c9b7c5f7",
    },
}

# Phép NGHỊCH của đúng 5 phép gieo. Mỗi chỗ có ĐÚNG MỘT phép nghịch.
NGHICH_SS = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
             ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


class _Lat(ast.NodeTransformer):
    """Lật ĐÚNG MỘT chỗ, chỉ số `muc`. Đếm theo cùng thứ tự với `DotBien`."""

    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.da = ""
        self.danh_sach: list[tuple[int, int, str]] = []

    def _lay(self, ten: str, nut: ast.AST) -> bool:
        d = self.dem
        # Dòng thuộc CHÍNH cây đang duyệt. `dot_bien()` dùng ast.unparse nên
        # dòng của tệp gốc không còn giá trị sau khi gieo lỗi.
        self.danh_sach.append((d, int(getattr(nut, "lineno", 0) or 0), ten))
        self.dem += 1
        if d == self.muc:
            self.da = ten
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            if self._lay("so sánh %s" % type(n.ops[0]).__name__, n):
                n.ops = [NGHICH_SS[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay("logic %s" % type(n.op).__name__, n):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay("bool %s" % n.value, n):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            # gieo là n -> n+1, nên NGHỊCH là n -> n-1
            if self._lay("số %d" % n.value, n):
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
    return len(_liet_ke_cho(ma))


def _liet_ke_cho(ma: str) -> list[tuple[int, int]]:
    """Liệt kê ``(chỉ số, dòng)`` theo đúng thứ tự hậu duyệt của `_Lat`.

    Không dùng ``ast.walk``: nó duyệt breadth-first, còn cả `DotBien` lẫn `_Lat`
    đều đếm sau khi đã thăm cây con. Đổi thứ tự là lật nhầm chỗ.
    """
    d = _Lat(-1)
    d.visit(ast.parse(ma))
    return [(chi_so, dong) for chi_so, dong, _ in d.danh_sach]


def _ma_sau_lat(nguon: str, chi_so: int) -> tuple[str, str]:
    """Lật đúng chỉ số trên một cây mới; không tái dùng cây đã bị biến đổi."""
    bd = _Lat(chi_so)
    moi = ast.unparse(ast.fix_missing_locations(bd.visit(ast.parse(nguon))))
    return moi, bd.da


def _chi_so_khoi_phuc(nguon: str, chuan: str) -> list[int]:
    """Tìm đáp án bằng byte mã chuẩn hóa, KHÔNG dùng test hay dò chuỗi."""
    ra: list[int] = []
    for chi_so, _ in _liet_ke_cho(nguon):
        try:
            moi, _ = _ma_sau_lat(nguon, chi_so)
        except Exception:
            continue
        if moi == chuan:
            ra.append(chi_so)
    return ra


def _tao_script_trace_dong(tep_nguon: Path, node_id_test: str,
                           max_steps: int = 5000) -> str:
    """Tracer cục bộ của E1: ghi MỌI dòng chạy và gọi test đúng một lần.

    `TraceResult.cac_su_kien` hiện chỉ ghi khi local đổi hoặc return, nên không
    phải line coverage. Không sửa `core/trace_runtime.py` vì Antigravity đang
    dùng nó cho `/api/trace`; E1 chỉ bổ sung phép đo còn thiếu trong kho tạm.
    """
    return textwrap.dedent(f"""
        # -*- coding: utf-8 -*-
        import json
        import os
        import sys
        import pytest

        TEP = os.path.normcase(os.path.realpath({json.dumps(str(tep_nguon))}))
        NODE = {json.dumps(node_id_test)}
        MAX_STEPS = {int(max_steps)}
        dong_da_chay = set()
        so_buoc = 0
        cham_tran = False

        def tracer(frame, event, arg):
            global so_buoc, cham_tran
            if event != "line":
                return tracer
            try:
                hien_tai = os.path.normcase(os.path.realpath(frame.f_code.co_filename))
            except Exception:
                return tracer
            if hien_tai != TEP:
                return tracer
            if so_buoc >= MAX_STEPS:
                cham_tran = True
                return None
            so_buoc += 1
            dong_da_chay.add(int(frame.f_lineno))
            return tracer

        class Plugin:
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_call(self, item):
                sys.settrace(tracer)
                try:
                    yield
                finally:
                    sys.settrace(None)

        ma_thoat = pytest.main(
            ["-q", "--no-header", "--tb=short", "-p", "no:cacheprovider", NODE],
            plugins=[Plugin()],
        )
        print("===E1_TRACE_START===")
        print(json.dumps({{
            "ma_thoat": int(ma_thoat),
            "so_buoc": so_buoc,
            "cham_tran": cham_tran,
            "dong_da_chay": sorted(dong_da_chay),
        }}, ensure_ascii=False))
        print("===E1_TRACE_END===")
    """)


def _chay_trace_dong_day_du(tam: Path, tep_nguon: str, node_id_test: str,
                            max_steps: int = 5000,
                            timeout_s: float = 20.0) -> dict:
    """Chạy tracer line-coverage trong tiến trình con, fail-closed ba trạng thái."""
    tep_abs = (tam / tep_nguon).resolve()
    script = _tao_script_trace_dong(tep_abs, node_id_test, max_steps=max_steps)
    t0 = time.monotonic()
    try:
        x = subprocess.run(
            [PY, "-X", "utf8", "-c", script], capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=str(tam),
            timeout=max(0.1, min(20.0, timeout_s)),
        )
    except subprocess.TimeoutExpired:
        return {"trang_thai": "khong_chay", "vi_sao": "trace dòng quá 20 giây",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}
    except Exception as exc:
        return {"trang_thai": "khong_chay", "vi_sao": f"lỗi tiến trình trace: {exc}",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}

    marker_a, marker_b = "===E1_TRACE_START===", "===E1_TRACE_END==="
    if x.returncode != 0 or marker_a not in x.stdout or marker_b not in x.stdout:
        return {"trang_thai": "khong_chay",
                "vi_sao": f"trace không trả JSON (exit {x.returncode})",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}
    try:
        raw = x.stdout.split(marker_a, 1)[1].split(marker_b, 1)[0].strip()
        data = json.loads(raw)
    except Exception as exc:
        return {"trang_thai": "khong_chay", "vi_sao": f"JSON trace hỏng: {exc}",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}

    # Đây là test ĐỎ đã chọn, nên pytest phải trả đúng 1. Mọi mã khác là harness
    # hỏng/collection error/test bỗng xanh và không được dùng để lọc.
    if data.get("ma_thoat") != 1:
        return {"trang_thai": "khong_chay",
                "vi_sao": f"test được chọn trả mã {data.get('ma_thoat')}, cần 1",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}
    if data.get("cham_tran"):
        return {"trang_thai": "trace_cut", "vi_sao": f"chạm trần {max_steps} bước",
                "dong_da_chay": data.get("dong_da_chay", []),
                "giay": round(time.monotonic() - t0, 3)}
    dong = sorted({int(v) for v in data.get("dong_da_chay", []) if int(v) > 0})
    if not dong:
        return {"trang_thai": "khong_chay", "vi_sao": "trace không có dòng nguồn",
                "dong_da_chay": [], "giay": round(time.monotonic() - t0, 3)}
    return {"trang_thai": "trace_du", "vi_sao": "", "dong_da_chay": dong,
            "so_buoc": int(data.get("so_buoc", 0)),
            "giay": round(time.monotonic() - t0, 3)}


def _chon_test_va_dong(tam: Path, tep_nguon: str, tep_test: str,
                       deadline: float) -> dict:
    """Chốt test đỏ ít bước nhất; mỗi lượt TRACE chỉ chạy test đúng một lần.

    Không gọi `core.trace_runtime.chot_test_can_trace`: đo 22/08/2026 bắt được
    plugin của nó tự gọi `item.runtest()`; nếu lượt đó không raise thì hook mặc
    định gọi lại. E1 dùng một tiến trình thường để nhận diện test đỏ, rồi mỗi
    test đỏ chạy đúng một lần trong tiến trình trace riêng. Mọi subprocess cùng
    chia sẻ một deadline tuyệt đối 60 giây.
    """
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {"trang_thai": "khong_chay", "vi_sao": "hết trần 60 giây trước trace",
                "test": "", "so_test_do_khac": 0, "dong_da_chay": []}
    try:
        x = subprocess.run(
            [PY, "-X", "utf8", "-m", "pytest", tep_test, "-q", "--no-header",
             "--tb=line", "-p", "no:cacheprovider"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(tam), timeout=max(0.1, min(60.0, con_lai)),
        )
    except subprocess.TimeoutExpired:
        return {"trang_thai": "khong_chay", "vi_sao": "liệt kê test đỏ quá hạn",
                "test": "", "so_test_do_khac": 0, "dong_da_chay": []}
    except Exception as exc:
        return {"trang_thai": "khong_chay", "vi_sao": f"lỗi liệt kê test đỏ: {exc}",
                "test": "", "so_test_do_khac": 0, "dong_da_chay": []}
    if x.returncode not in (0, 1):
        return {"trang_thai": "khong_chay",
                "vi_sao": f"không liệt kê được test đỏ (exit {x.returncode})",
                "test": "", "so_test_do_khac": 0, "dong_da_chay": []}
    test_do: list[str] = []
    for line in x.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAILED "):
            node_id = line[len("FAILED "):].split(" - ", 1)[0].split(" : ", 1)[0].strip()
            if node_id and node_id not in test_do:
                test_do.append(node_id)
    if not test_do:
        return {"trang_thai": "khong_chay", "vi_sao": "không chốt được test đỏ",
                "test": "", "so_test_do_khac": 0, "dong_da_chay": []}

    ung_vien: list[tuple[int, int, str, dict]] = []
    for thu_tu, ten_test in enumerate(test_do):
        con_lai = deadline - time.monotonic()
        if con_lai <= 0:
            return {"trang_thai": "khong_chay", "vi_sao": "hết trần khi trace test đỏ",
                    "test": "", "so_test_do_khac": len(test_do) - 1,
                    "dong_da_chay": []}
        trace = _chay_trace_dong_day_du(
            tam, tep_nguon, ten_test, timeout_s=min(20.0, con_lai)
        )
        if trace.get("trang_thai") == "trace_du":
            ung_vien.append((int(trace.get("so_buoc", 0)), thu_tu, ten_test, trace))
    if not ung_vien:
        return {"trang_thai": "khong_chay",
                "vi_sao": "không test đỏ nào có trace dòng đầy đủ",
                "test": "", "so_test_do_khac": max(0, len(test_do) - 1),
                "dong_da_chay": []}
    _, _, ten_test, ra = min(ung_vien, key=lambda item: (item[0], item[1]))
    ra.update({"test": ten_test, "so_test_do_khac": len(test_do) - 1,
               "so_test_do": len(test_do)})
    return ra


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
        try:
            m1, loi1 = chay_test(tam, tep_test)
            m2, _ = chay_test(tam, tep_test)
        except subprocess.TimeoutExpired:
            return {"trang_thai": "khong_do_duoc",
                    "vi_sao": "kiểm nhiễu test đỏ quá thời gian"}
        if m1 == 0 or m2 == 0:
            return {"trang_thai": "khong_do_duoc", "vi_sao": "test không đỏ ổn định"}
        goc_ky = _chu_ky(loi1)

        # BẢN GỐC là đáp án: lật đúng chỗ gieo phải khôi phục nguyên văn.
        chuan = ast.unparse(ast.parse(goc))
        cac_cho = _liet_ke_cho(ma)
        n_cho = len(cac_cho)
        chi_so_dap_an = _chi_so_khoi_phuc(ma, chuan)

        # Chốt test đỏ trước, rồi lấy MỌI dòng mà đúng test ấy chạy trên mã đã
        # đột biến. Không dùng dòng tệp gốc và không dùng `cac_su_kien` thưa.
        t0_loc = time.monotonic()
        deadline = t0_loc + 60.0
        trace = _chon_test_va_dong(tam, tep, tep_test, deadline)
        if trace.get("trang_thai") != "trace_du":
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": f"không có vết dòng đầy đủ: {trace.get('vi_sao', '')}",
                "mo_ta_gieo": mo.split(":", 1)[-1].strip(),
                "so_cho_truoc_loc": n_cho,
                "so_cho_sau_loc": 0,
                "chi_so_dap_an_truoc_loc": chi_so_dap_an,
                "trace": trace,
            }
        dong_da_chay = set(trace["dong_da_chay"])
        cho_sau_loc = [(chi_so, dong) for chi_so, dong in cac_cho
                       if dong in dong_da_chay]
        chi_so_sau_loc = {chi_so for chi_so, _ in cho_sau_loc}
        dong_dap_an = [dong for chi_so, dong in cac_cho if chi_so in chi_so_dap_an]
        dap_an_con_sau_loc = all(i in chi_so_sau_loc for i in chi_so_dap_an)
        giay_loc = time.monotonic() - t0_loc
        if giay_loc >= 60.0:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": "riêng bước trace đã vượt trần 60 giây",
                "mo_ta_gieo": mo.split(":", 1)[-1].strip(),
                "so_cho_truoc_loc": n_cho,
                "so_cho_sau_loc": len(cho_sau_loc),
                "chi_so_sau_loc": sorted(chi_so_sau_loc),
                "chi_so_dap_an_truoc_loc": chi_so_dap_an,
                "dap_an_con_sau_loc": (dap_an_con_sau_loc if chi_so_dap_an else None),
                "trace": trace,
                "giay_loc_va_lat": round(giay_loc, 1),
            }

        t0_lat = time.monotonic()
        n_chay = [0]
        qua_gio = [False]

        def mot_vong(nguon: str, ky_nen: str,
                     chi_so_duoc_thu: list[int]):
            """Lật từng chỗ một lượt. Trả (danh sách xanh, danh sách đổi chữ ký)."""
            xanh_, doi_ = [], []
            for i in chi_so_duoc_thu:
                con_lai = deadline - time.monotonic()
                if con_lai <= 0:
                    qua_gio[0] = True
                    break
                try:
                    moi, phep = _ma_sau_lat(nguon, i)
                except Exception:
                    continue
                if moi == nguon:
                    continue
                f.write_text(moi, encoding="utf-8")
                n_chay[0] += 1
                try:
                    mt, lt = chay_test(tam, tep_test, tran=max(0.1, con_lai))
                except subprocess.TimeoutExpired:
                    qua_gio[0] = True
                    break
                if mt == 0:
                    xanh_.append({"chi_so": i, "phep": phep, "ma": moi})
                elif _chu_ky(lt) != ky_nen:
                    doi_.append({"chi_so": i, "phep": phep, "ma": moi,
                                 "ky": _chu_ky(lt)})
            return xanh_, doi_

        # Phép đo mới cố ý dựng lại ĐÚNG bốn đề một lỗi của sổ E1. Không nối
        # `_chen_not`: làm vậy sẽ đổi thuật toán và biến đề thứ tư từ TRƯỢT sang
        # XANH, trái ngưỡng đã khóa trước khi chạy.
        xanh, doi_ky = mot_vong(ma, goc_ky,
                                [chi_so for chi_so, _ in cho_sau_loc])
        y_nguyen = len(cho_sau_loc) - len(xanh) - len(doi_ky)
        loi_ap = 0
        vong = 1
        giay_lat = time.monotonic() - t0_lat
        giay_loc_va_lat = time.monotonic() - t0_loc
        if qua_gio[0]:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": "lọc + lật vượt trần 60 giây",
                "mo_ta_gieo": mo.split(":", 1)[-1].strip(),
                "so_cho_truoc_loc": n_cho,
                "so_cho_sau_loc": len(cho_sau_loc),
                "chi_so_sau_loc": sorted(chi_so_sau_loc),
                "chi_so_dap_an_truoc_loc": chi_so_dap_an,
                "dap_an_con_sau_loc": (dap_an_con_sau_loc if chi_so_dap_an else None),
                "test_do_duoc_chon": trace.get("test", ""),
                "trang_thai_trace": trace.get("trang_thai"),
                "so_lan_chay_test": n_chay[0],
                "giay_loc": round(giay_loc, 1),
                "giay_lat": round(giay_lat, 1),
                "giay_loc_va_lat": round(giay_loc_va_lat, 1),
            }
        for x in xanh:
            x["khoi_phuc_goc"] = x.get("ma") == chuan

        # chỉ những bản vá làm test đỏ xanh mới đáng chạy CẢ BỘ
        ca_bo = []
        ca_bo_kiem_tra = []
        for x in xanh:
            f.write_text(x["ma"], encoding="utf-8")
            try:
                r = subprocess.run(
                    [PY, "-X", "utf8", "-m", "pytest", "tests", "-q",
                     "--no-header", "-p", "no:cacheprovider"],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", cwd=str(tam), timeout=900,
                )
                ca_bo_kiem_tra.append({"chi_so": x["chi_so"],
                                       "trang_thai": "xanh" if r.returncode == 0 else "do",
                                       "ma_thoat": r.returncode,
                                       "duoi_loi": "" if r.returncode == 0 else
                                       ((r.stdout or "") + (r.stderr or ""))[-1500:]})
                if r.returncode == 0:
                    ca_bo.append(x)
            except subprocess.TimeoutExpired:
                ca_bo_kiem_tra.append({"chi_so": x["chi_so"],
                                       "trang_thai": "khong_do_duoc_timeout",
                                       "ma_thoat": None})
        return {
            "trang_thai": "do_duoc", "mo_ta_gieo": mo.split(":", 1)[-1].strip(),
            "so_cho_lat": n_cho,
            "so_cho_truoc_loc": n_cho,
            "so_cho_sau_loc": len(cho_sau_loc),
            "chi_so_sau_loc": sorted(chi_so_sau_loc),
            "chi_so_dap_an_truoc_loc": chi_so_dap_an,
            "dong_dap_an_trong_ma_dot_bien": dong_dap_an,
            "dap_an_con_sau_loc": (dap_an_con_sau_loc if chi_so_dap_an else None),
            "sha256_ma_dot_bien": hashlib.sha256(ma.encode("utf-8")).hexdigest(),
            "test_do_duoc_chon": trace.get("test", ""),
            "so_test_do_khac": trace.get("so_test_do_khac", 0),
            "trang_thai_trace": trace.get("trang_thai"),
            "so_buoc_trace": trace.get("so_buoc", 0),
            "dong_da_chay": trace.get("dong_da_chay", []),
            "so_xanh": len(xanh),
            "so_doi_chu_ky": len(doi_ky), "so_y_nguyen": y_nguyen,
            "loi_ap": loi_ap, "so_xanh_ca_bo": len(ca_bo),
            "kiem_tra_ca_bo": ca_bo_kiem_tra,
            "so_vong": vong, "so_lan_chay_test": n_chay[0],
            "bat_dung_cho_gieo": any(x["khoi_phuc_goc"] for x in xanh),
            "giay_loc": round(giay_loc, 1),
            "giay_lat": round(giay_lat, 1),
            "giay_loc_va_lat": round(giay_loc_va_lat, 1),
            "xanh": [{k: v for k, v in x.items() if k != "ma"} for x in xanh[:8]],
        }
    finally:
        f.write_text(goc, encoding="utf-8")


def _ghi_so_nguyen_tu(path: Path, data: list[dict]) -> None:
    """Không để một lần dừng giữa chừng biến sổ JSON thành tệp nửa dòng."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tam = path.with_suffix(path.suffix + ".tmp")
    tam.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tam.replace(path)


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if RA.exists():
        print("  BLOCKED: lat_nguoc.json đã tồn tại. Đổi tên sổ cũ trước; không ghi đè.")
        return 2
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
    # Sinh đủ theo thứ tự cũ TRƯỚC rồi mới lọc; lọc sớm sẽ làm RNG chọn đề khác.
    de = [d for d in de if d["so_loi"] == 1 and d["tep"] in MOC_E1_MOT_LOI]
    if [d["tep"] for d in de] != list(MOC_E1_MOT_LOI):
        print("  KHÔNG ĐO ĐƯỢC: bốn đề E1 lỗi đơn đã trôi thứ tự/nội dung")
        return 2
    for d in de:
        moc = DAU_VET_E1_MOT_LOI[d["tep"]]
        goc = (GOC / d["tep"]).read_text(encoding="utf-8")
        ma, _ = dot_bien(goc, set(d["cho"]))
        dau_vet = hashlib.sha256(ma.encode("utf-8")).hexdigest() if ma else ""
        if (d["tep_test"] != moc["tep_test"] or d["cho"] != moc["cho"]
                or dau_vet != moc["sha256"]):
            print("  KHÔNG ĐO ĐƯỢC: đề E1 đã trôi:", d["tep"])
            return 2
    if len(sys.argv) > 1 and int(sys.argv[1]) != 4:
        print("  KHÔNG ĐO ĐƯỢC: phép đối chứng này khóa đúng 4 đề; chỉ nhận đối số 4")
        return 2

    tam_goc = Path(tempfile.mkdtemp())
    tam = tam_goc / "kho"
    shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
        "venv", ".venv-cst", ".venv-needle", ".git", "__pycache__", "data",
        "_rac", "*.pyc"))
    # Không chép kho dữ liệu lớn, nhưng phải giữ hình dạng thư mục. Test hàng
    # rào `/api/tep_tin?thu_muc=data` phân biệt "không tồn tại" (400) với
    # "tồn tại nhưng ngoài whitelist" (403); thiếu thư mục làm suite đỏ giả.
    (tam / "data").mkdir()
    ra = []
    print("  %d đề · KHÔNG GỌI MODEL · máy lật từng chỗ, test phán quyết\n" % len(de))
    try:
        try:
            nen = subprocess.run(
                [PY, "-X", "utf8", "-m", "pytest", "tests", "-q", "--no-header",
                 "-p", "no:cacheprovider"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(tam), timeout=900,
            )
        except subprocess.TimeoutExpired:
            print("  KHÔNG ĐO ĐƯỢC: suite nền quá 900 giây")
            return 2
        if nen.returncode != 0:
            print("  KHÔNG ĐO ĐƯỢC: bản sao tạm đã đỏ trước khi gieo lỗi")
            print(((nen.stdout or "") + (nen.stderr or ""))[-2000:])
            return 2
        for d in de:
            t0 = time.monotonic()
            r = mot_de(tam, d)
            r.update({"tep": d["tep"], "so_loi": d["so_loi"],
                      "giay": round(time.monotonic() - t0, 1)})
            ra.append(r)
            _ghi_so_nguyen_tu(RA, ra)
            print("  %-22s %d lỗi  %3s -> %3s chỗ  %2s xanh  %s cả bộ  "
                  "giữ đáp án: %-5s  lọc+lật %4ss"
                  % (d["tep"].split("/")[-1][:22], d["so_loi"],
                     r.get("so_cho_truoc_loc", "-"), r.get("so_cho_sau_loc", "-"),
                     r.get("so_xanh", "-"), r.get("so_xanh_ca_bo", "-"),
                     r.get("dap_an_con_sau_loc"), r.get("giay_loc_va_lat", "-")))
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)

    ok = [x for x in ra if x["trang_thai"] == "do_duoc"]
    theo_ket_qua = {x["tep"]: x for x in ra}
    dung_bon_de = len(ok) == 4 and set(theo_ket_qua) == set(MOC_E1_MOT_LOI)
    dung_verdict = dung_bon_de and all(
        (
            bool(theo_ket_qua[tep].get("bat_dung_cho_gieo"))
            and theo_ket_qua[tep].get("so_xanh_ca_bo", 0) > 0
        ) == phai_xanh
        for tep, phai_xanh in MOC_E1_MOT_LOI.items()
    )
    giu_dap_an = dung_bon_de and all(
        bool(theo_ket_qua[tep].get("chi_so_dap_an_truoc_loc"))
        and theo_ket_qua[tep].get("dap_an_con_sau_loc") is True
        for tep, phai_xanh in MOC_E1_MOT_LOI.items() if phai_xanh
    )
    dung_thoi_gian = dung_bon_de and all(
        float(x.get("giay_loc_va_lat", 10**9)) <= 60.0 for x in ok
    )
    print("\n" + "=" * 64)
    print("  E1 — LẬT NGƯỢC + LỌC VẾT THỰC THI, KHÔNG MODEL")
    print("=" * 64)
    for tep, phai_xanh in MOC_E1_MOT_LOI.items():
        x = theo_ket_qua.get(tep, {})
        thuc_te = bool(x.get("bat_dung_cho_gieo") and x.get("so_xanh_ca_bo", 0))
        print("  %-25s trước/sau %3s/%3s · %-5s (mốc %-5s) · %5ss"
              % (Path(tep).name, x.get("so_cho_truoc_loc", "-"),
                 x.get("so_cho_sau_loc", "-"),
                 "XANH" if thuc_te else "TRƯỢT",
                 "XANH" if phai_xanh else "TRƯỢT",
                 x.get("giay_loc_va_lat", "-")))
    print("  dựng đúng sổ 3 xanh + 1 trượt : %s" % dung_verdict)
    print("  không đánh rơi 3 đáp án       : %s" % giu_dap_an)
    print("  lọc + lật <= 60s từng tệp     : %s" % dung_thoi_gian)
    print("  sổ: %s" % RA)
    return 0 if dung_verdict and giu_dap_an and dung_thoi_gian else 1


if __name__ == "__main__":
    raise SystemExit(main())
