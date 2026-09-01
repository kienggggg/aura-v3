# -*- coding: utf-8 -*-
"""trace_runtime.py — Thu thập vết thực thi dòng chảy dữ liệu (Runtime Data Flow).

Phục vụ Mạch Nước Ngầm Biến Số (Ưu tiên #1 của AURA v3):
1. Chọn test tất định 3 tầng khi có nhiều test đỏ:
   - Tầng 1: Trong tập test ĐỎ, chọn test có số bước nhỏ nhất đi qua dòng đột biến.
   - Tầng 2: Phân xử hoà theo thứ tự thu thập (collection order) của pytest.
   - Tầng 3: Báo rõ số test đỏ khác trên giao diện.
2. Đo bước lọc theo mô-đun:
   - Chỉ đếm dòng lệnh thuộc file nguồn đang xét (loại bỏ stdlib, pytest, harness).
   - Trần số bước: max_steps = 5000.
3. Ba trạng thái Fail-Closed chuẩn (Luật §5):
   - 'trace_du': Trích xuất đầy đủ chuỗi giá trị biến đổi.
   - 'trace_cut': 'KHÔNG ĐO ĐƯỢC: Chạm trần ở bước 5000' (tuyệt đối không trả chuỗi cụt).
   - 'khong_chay': 'KHÔNG ĐO ĐƯỢC: <lý do>'.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable or str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe")


@dataclass
class TraceEvent:
    buoc: int
    dong: int
    ten_bien: str
    gia_tri_cu: str
    gia_tri_moi: str
    su_kien: str  # 'gan', 'thay_doi', 'tra_ve', 'dong_chay'
    dong_ma: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TraceResult:
    trang_thai: str  # 'trace_du', 'trace_cut', 'khong_chay'
    thong_diep: str
    tong_buoc: int
    ten_test: str
    so_test_do_khac: int
    cac_su_kien: list[dict] = field(default_factory=list)
    tep_nguon: str = ""
    thoi_gian_giay: float = 0.0
    dong_da_chay: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Bóc mã màu ANSI trước khi so chuỗi trên đầu ra pytest.
#
# 30/08/2026. Tiến trình app chạy dưới một môi trường có FORCE_COLOR=1 (thừa kế
# từ nơi khởi chạy). pytest thấy cờ đó thì tô màu KỂ CẢ khi ghi ra pipe, nên dòng
# tóm tắt không còn bắt đầu bằng "FAILED " nữa mà bằng "\x1b[31mFAILED\x1b[0m".
# `line.startswith("FAILED ")` trượt sạch -> danh sách test đỏ RỖNG -> /api/trace
# trả về "Không có test nào bị đỏ trong tệp test này".
#
# Đo thật 30/08, cùng một tệp test, cùng một máy:
#     pytest gọi thẳng            -> "1 failed"          (đúng)
#     /api/trace                  -> "không có test đỏ"  (SAI), 0,5 giây
#     gọi hàm này từ script riêng -> tìm thấy 1 test đỏ  (đúng)
# Ba kết quả khác nhau cho cùng một sự thật; cái khác nhau là biến môi trường.
#
# Câu "Không có test nào bị đỏ" là một PHÁN QUYẾT tự tin về mã của người dùng,
# phát ra trong khi phép đo đã hỏng — đúng thứ CLAUDE.md mục 4 cấm.
#
# Hai lớp: `--color=no` trên mọi lệnh pytest (gốc), và hàm này (phòng khi có
# công cụ khác tô màu, hoặc cờ ấy bị bỏ qua).
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _bo_mau(chuoi: str) -> str:
    return _ANSI.sub("", chuoi or "")


def _chay_pytest_lay_danh_sach_test(tep_test: str, cwd: Optional[Path] = None) -> list[str]:
    """Thu thập danh sách tất cả các test case theo thứ tự pytest collection."""
    root = cwd or PROJECT_ROOT
    cmd = [PY, "-X", "utf8", "-m", "pytest", tep_test, "--collect-only", "-q", "--color=no"]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(root),
            timeout=30,
        )
        tests = []
        for line in _bo_mau(res.stdout).splitlines():
            line = line.strip()
            if line and "::" in line and not line.startswith("="):
                # VD: tests/test_may_tinh.py::test_dem_ngay
                tests.append(line)
        return tests
    except Exception:
        return []


def _chay_pytest_tim_test_do_phan_loai(tep_test: str, cwd: Optional[Path] = None) -> Tuple[List[str], List[str]]:
    """Chạy toàn bộ tệp test và trả về (danh_sach_test_do_that, danh_sach_loi_nap)."""
    root = cwd or PROJECT_ROOT
    cmd = [
        PY, "-X", "utf8", "-m", "pytest", tep_test,
        "-q", "--no-header", "--tb=line", "-p", "no:cacheprovider", "--color=no",
    ]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(root),
            timeout=60,
        )
        failing_tests = []
        import_errors = []
        chi_tiet_loi: list[str] = []
        for line in _bo_mau(res.stdout).splitlines():
            line = line.strip()
            if line.startswith("FAILED "):
                part = line[len("FAILED "):].split(" - ")[0].split(" : ")[0].strip()
                failing_tests.append(part)
            elif line.startswith("ERROR "):
                part = line[len("ERROR "):].split(" - ")[0].split(" : ")[0].strip()
                if "::" in part:
                    failing_tests.append(part)
                else:
                    # Với lỗi NẠP thì giữ nguyên cả dòng: phần sau dấu " - " chính
                    # là lý do (ModuleNotFoundError, SyntaxError…). Cắt nó đi thì
                    # thông điệp chỉ còn tên tệp, người đọc vẫn phải tự đoán —
                    # mà đoán là thứ cả tệp luật này sinh ra để chống.
                    import_errors.append(line[len("ERROR "):].strip())
            elif line.startswith("INTERNALERROR"):
                import_errors.append(line)
            elif line.startswith("E   ") and len(chi_tiet_loi) < 2:
                # Dòng tóm tắt của pytest chỉ ghi "ERROR tests/x.py" — không kèm
                # lý do. Lý do thật nằm trong THÂN, ở dòng bắt đầu bằng "E   ":
                #     E   ModuleNotFoundError: No module named 'abc'
                # Không gom dòng này thì thông điệp gửi lên màn hình chỉ có tên
                # tệp, và người dùng vẫn phải tự đoán hỏng ở đâu.
                chi_tiet_loi.append(line[len("E   "):].strip())

        if import_errors and chi_tiet_loi:
            import_errors = [f"{import_errors[0]} ({'; '.join(chi_tiet_loi)})"] + import_errors[1:]

        if res.returncode == 2 and not failing_tests and not import_errors:
            # 31/08/2026 — bản đóng gói `.exe` rơi vào đúng nhánh này, và câu
            # nó nói ra là câu KHÔNG AI ĐỌC ĐƯỢC. Đo trên bản dựng bằng
            # PyInstaller, bấm TÌM LỖI:
            #     "KHÔNG ĐO ĐƯỢC: chạy tệp test không xong — Lỗi thu thập/nạp
            #      module (mã thoát 2): usage: AURA_The.exe [-h] [--host HOST]
            #      ... unrecognized arguments: -X utf8 -m pytest ..."
            # Trạng thái thì ĐÚNG (`khong_chay`, không giả vờ "không có test
            # nào đỏ"), nhưng người thử đọc xong vẫn không biết phải làm gì.
            #
            # Nguyên nhân thật, nói thẳng: bản đóng gói không kèm `pytest`, và
            # trong bản đóng băng `sys.executable` là chính cái .exe nên
            # `-m pytest` rơi vào argparse của app.
            if getattr(sys, "frozen", False):
                import_errors.append(
                    "Bản đóng gói (.exe) KHÔNG kèm pytest, nên TÌM LỖI và DÒ "
                    "DÒNG DỮ LIỆU không chạy được ở đây. Hai nút này dành cho "
                    "bản chạy từ mã nguồn. Nút CHẠY THỬ thì vẫn dùng bình thường."
                )
            else:
                import_errors.append(
                    f"Lỗi thu thập/nạp module (mã thoát 2): {res.stderr.strip()[:200]}")

        return failing_tests, import_errors
    except Exception as e:
        return [], [str(e)]


def _chay_pytest_tim_test_do(tep_test: str, cwd: Optional[Path] = None) -> list[str]:
    """Chạy toàn bộ tệp test và trả về danh sách các test case bị FAILED/ERROR theo thứ tự."""
    ds_do, _ = _chay_pytest_tim_test_do_phan_loai(tep_test, cwd=cwd)
    return ds_do



def tao_script_tracer(
    tep_nguon_abs: str,
    node_id_test: str,
    dong_kiem_tra: Optional[int] = None,
    max_steps: int = 5000,
) -> str:
    """Tạo mã Python thực thi 1 test đơn lẻ với sys.settrace lọc chính xác mô-đun đích."""
    tep_json = json.dumps(str(tep_nguon_abs))
    node_json = json.dumps(str(node_id_test))
    max_steps_int = int(max_steps)
    dong_kiem_tra_int = int(dong_kiem_tra) if dong_kiem_tra is not None and not isinstance(dong_kiem_tra, bool) and dong_kiem_tra > 0 else -1

    script = f'''# -*- coding: utf-8 -*-
import sys
import os
import json
import traceback

TEP_NGUON_ABS = os.path.abspath({tep_json})
MAX_STEPS = {max_steps_int}
DONG_KIEM_TRA = {dong_kiem_tra_int}

events = []
dong_da_chay = set()
step_count = 0
hit_ceiling = False
qua_dong_kiem_tra = False
last_locals = {{}}

# Đọc các dòng mã nguồn
source_lines = []
try:
    with open(TEP_NGUON_ABS, "r", encoding="utf-8", errors="replace") as f:
        source_lines = f.readlines()
except Exception:
    pass

def safe_repr(val, max_len=150):
    try:
        s = repr(val)
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s
    except Exception:
        return "<unprintable>"

def tracer(frame, event, arg):
    global step_count, hit_ceiling, qua_dong_kiem_tra, last_locals, dong_da_chay
    filename = frame.f_code.co_filename
    if not filename:
        return tracer
    try:
        abs_fn = os.path.abspath(filename)
    except Exception:
        return tracer
    
    # Chỉ đếm và thu thập vết thuộc mô-đun đang xét
    if abs_fn.lower() != TEP_NGUON_ABS.lower():
        return tracer

    line_no = frame.f_lineno
    if event == "line":
        dong_da_chay.add(int(line_no))

    if DONG_KIEM_TRA > 0 and line_no == DONG_KIEM_TRA:
        qua_dong_kiem_tra = True

    if step_count >= MAX_STEPS:
        hit_ceiling = True
        return None  # Dừng trace

    step_count += 1
    code_text = ""
    if 1 <= line_no <= len(source_lines):
        code_text = source_lines[line_no - 1].strip()

    curr_locals = dict(frame.f_locals)
    if event == "line":
        # So sánh biến thay đổi so với bước trước trong cùng scope
        for k, v in curr_locals.items():
            if k.startswith("__"):
                continue
            if k not in last_locals:
                events.append({{
                    "buoc": step_count,
                    "dong": line_no,
                    "ten_bien": k,
                    "gia_tri_cu": "<chưa gán>",
                    "gia_tri_moi": safe_repr(v),
                    "su_kien": "gan",
                    "dong_ma": code_text
                }})
            elif last_locals[k] != safe_repr(v):
                events.append({{
                    "buoc": step_count,
                    "dong": line_no,
                    "ten_bien": k,
                    "gia_tri_cu": last_locals[k],
                    "gia_tri_moi": safe_repr(v),
                    "su_kien": "thay_doi",
                    "dong_ma": code_text
                }})
        last_locals = {{k: safe_repr(v) for k, v in curr_locals.items() if not k.startswith("__")}}

    elif event == "return":
        events.append({{
            "buoc": step_count,
            "dong": line_no,
            "ten_bien": "<tra_ve>",
            "gia_tri_cu": "",
            "gia_tri_moi": safe_repr(arg),
            "su_kien": "tra_ve",
            "dong_ma": code_text
        }})

    return tracer

# Chạy pytest với Plugin Hookwrapper: sys.settrace chỉ kích hoạt ĐÚNG trong lúc thực thi test call
import pytest

class TracePlugin:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        sys.settrace(tracer)
        try:
            yield
        finally:
            sys.settrace(None)

plugin = TracePlugin()
exit_code = pytest.main(
    ["-q", "--no-header", "--tb=short", "-p", "no:cacheprovider", {node_json}],
    plugins=[plugin]
)

result = {{
    "step_count": step_count,
    "hit_ceiling": hit_ceiling,
    "qua_dong_kiem_tra": qua_dong_kiem_tra,
    "exit_code": exit_code,
    "dong_da_chay": sorted(dong_da_chay),
    "events": events
}}

print("===JSON_START===")
print(json.dumps(result, ensure_ascii=False))
print("===JSON_END===")
'''
    return script


# TRẦN THỜI GIAN CHO MỘT LƯỢT TRACE — nới 15 -> 90 giây, 27/08/2026.
#
# Trần cũ là 15 giây, đóng đinh trong thân hàm. Đo trên máy RẢNH, ba ca của
# `core/the_cst.py` mà báo cáo vòng 4 nêu:
#
#     mục 89    15,0 giây  ->  khong_chay   (đụng trần)
#     mục 97    12,0 giây  ->  trace_du
#     mục 108   14,4 giây  ->  trace_du
#
# Tức vết CST chạy dưới `sys.settrace` mất 12–15 giây — NẰM SÁT MÉP TRẦN. Nới
# lên 120 thì mục 89 chạy xong trong 15,1 giây và ra `trace_du`. Nhãn cũ của
# nó được quyết bởi MỘT PHẦN MƯỜI GIÂY.
#
# Hậu quả đo được, không phải suy đoán: bộ 5 đo 26/08 trên máy rảnh ra 18 ca
# không đo được; đo lại 27/08 trong khi tôi chạy `pytest tests -q` song song
# thì ra 30. Cùng bộ đề, cùng cây mã, khác mỗi tải máy. Phép đo đang cân trên
# lưỡi dao, nên mọi con số của đợt này đều mang một sai số không ai đo.
#
# VÌ SAO 90 CHỨ KHÔNG PHẢI 120 HAY 300: ba test cancellation của
# `tests/test_chat_service.py` treo VĨNH VIỄN — `await web.started.wait()`
# không có timeout nội tại, và đột biến làm `ChatService.reply()` chết trước
# khi chạm hook `set()`. Trần càng cao thì mỗi ca treo càng đốt thêm chừng ấy
# giây cho không. 90 là sáu lần mức đo rải (15 giây), đủ chỗ cho máy bận, mà
# vẫn cắt được ca treo.
#
# Đây KHÔNG phải nới ngưỡng chấm điểm. Trần này là tham số của phép đo, và
# giá trị cũ đang làm phép đo nói SAI về cỗ máy (xem `chot_test_can_trace`).
TRAN_TRACE_GIAY = 90


def chay_trace_mot_test(
    tep_nguon: str,
    node_id_test: str,
    dong_kiem_tra: Optional[int] = None,
    max_steps: int = 5000,
    cwd: Optional[Path] = None,
    so_test_do_khac: int = 0,
) -> TraceResult:
    """Thực thi trace trên đúng 1 test case và trả về TraceResult 3 trạng thái chuẩn."""
    start_time = time.perf_counter()
    root = cwd or PROJECT_ROOT
    tep_nguon_path = (root / tep_nguon).resolve() if not Path(tep_nguon).is_absolute() else Path(tep_nguon)

    if not tep_nguon_path.is_file():
        return TraceResult(
            trang_thai="khong_chay",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Tệp nguồn không tồn tại: {tep_nguon}",
            tong_buoc=0,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=[],
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=round(time.perf_counter() - start_time, 3),
        )

    runner_code = tao_script_tracer(
        tep_nguon_abs=str(tep_nguon_path),
        node_id_test=node_id_test,
        dong_kiem_tra=dong_kiem_tra,
        max_steps=max_steps,
    )

    try:
        res = subprocess.run(
            [PY, "-X", "utf8", "-c", runner_code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(root),
            timeout=TRAN_TRACE_GIAY,
        )
    except subprocess.TimeoutExpired:
        return TraceResult(
            trang_thai="khong_chay",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Timeout thực thi quá {TRAN_TRACE_GIAY} giây",
            tong_buoc=0,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=[],
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=round(time.perf_counter() - start_time, 3),
        )
    except Exception as e:
        return TraceResult(
            trang_thai="khong_chay",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Lỗi tiến trình con: {e}",
            tong_buoc=0,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=[],
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=round(time.perf_counter() - start_time, 3),
        )

    elapsed = round(time.perf_counter() - start_time, 3)

    if "===JSON_START===" not in res.stdout:
        return TraceResult(
            trang_thai="khong_chay",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Không thu được output JSON. Stderr: {res.stderr[:200]}",
            tong_buoc=0,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=[],
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=elapsed,
        )

    try:
        raw_json = res.stdout.split("===JSON_START===")[1].split("===JSON_END===")[0].strip()
        data = json.loads(raw_json)
    except Exception as e:
        return TraceResult(
            trang_thai="khong_chay",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Lỗi giải mã JSON vết: {e}",
            tong_buoc=0,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=[],
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=elapsed,
        )

    hit_ceiling = data.get("hit_ceiling", False)
    step_count = data.get("step_count", 0)
    events = data.get("events", [])
    dong_da_chay = data.get("dong_da_chay", [])

    if hit_ceiling or step_count >= max_steps:
        return TraceResult(
            trang_thai="trace_cut",
            thong_diep=f"KHÔNG ĐO ĐƯỢC: Chạm trần ở bước {max_steps}",
            tong_buoc=step_count,
            ten_test=node_id_test,
            so_test_do_khac=so_test_do_khac,
            cac_su_kien=events,
            tep_nguon=str(tep_nguon_path),
            thoi_gian_giay=elapsed,
            dong_da_chay=dong_da_chay,
        )

    return TraceResult(
        trang_thai="trace_du",
        thong_diep=f"Trace thành công ({step_count} bước)",
        tong_buoc=step_count,
        ten_test=node_id_test,
        so_test_do_khac=so_test_do_khac,
        cac_su_kien=events,
        tep_nguon=str(tep_nguon_path),
        thoi_gian_giay=elapsed,
        dong_da_chay=dong_da_chay,
    )


def chot_test_can_trace(
    tep_nguon: str,
    tep_test: str,
    dong_kiem_tra: Optional[int] = None,
    cwd: Optional[Path] = None,
    max_steps: int = 5000,
) -> Tuple[Optional[str], int, List[TraceResult]]:
    """Thực hiện Luật Chọn Test Tất Định 3 Tầng:
    1. Tìm tất cả các test ĐỎ.
    2. Trace từng test đỏ để tìm test có SỐ BƯỚC NHỎ NHẤT mà VẪN ĐI QUA DÒNG ĐỘT BIẾN.
    3. Phân xử hoà theo thứ tự thu thập của pytest.
    
    Trả về: (ten_test_chot, so_test_do_khac, danh_sach_ket_qua_trace_ung_vien)
    """
    root = cwd or PROJECT_ROOT
    # 30/08/2026 — TRUOC ĐÂY gọi `_chay_pytest_tim_test_do`, tức là bản đã VỨT
    # `import_errors` đi ngay dòng sau khi tính ra nó. Hậu quả: tệp test không
    # import nổi, pytest sập, hay quá giờ — cả ba đều ra `[]`, và cả ba nơi gọi
    # hàm này đều dịch `[]` thành cùng một câu: "không có test nào bị đỏ".
    #
    # Đó là một PHÁN QUYẾT về mã của người dùng, phát ra trong khi chưa đo được
    # gì. Người đọc nó sẽ tin là mã mình xanh. CLAUDE.md mục 4: phép đo không
    # chạy phải NÓI LÀ KHÔNG CHẠY — ba trạng thái, không được gộp thành hai.
    #
    # Người viết trước đã dựng sẵn `import_errors` để phân biệt; nó chỉ bị đánh
    # rơi một tầng. Nay giữ lại và trả về thành một TraceResult `khong_chay`.
    ds_test_do, loi_nap = _chay_pytest_tim_test_do_phan_loai(tep_test, cwd=root)
    if not ds_test_do:
        if loi_nap:
            return None, 0, [TraceResult(
                trang_thai="khong_chay",
                thong_diep="KHÔNG ĐO ĐƯỢC: chạy tệp test không xong — "
                           + "; ".join(str(x) for x in loi_nap)[:300],
                tong_buoc=0,
                ten_test="",
                so_test_do_khac=0,
                cac_su_kien=[],
                tep_nguon=str(tep_nguon),
                thoi_gian_giay=0.0,
            )]
        return None, 0, []

    tong_so_do = len(ds_test_do)
    ung_vien: list[Tuple[int, bool, int, str, TraceResult]] = []
    # (so_buoc, qua_dong, thu_tu_pytest, ten_test, trace_result)

    for idx, test_id in enumerate(ds_test_do):
        res = chay_trace_mot_test(
            tep_nguon=tep_nguon,
            node_id_test=test_id,
            dong_kiem_tra=dong_kiem_tra,
            max_steps=max_steps,
            cwd=root,
            so_test_do_khac=tong_so_do - 1,
        )
        qua_dong = False
        if dong_kiem_tra is not None and dong_kiem_tra > 0:
            qua_dong = any(ev.get("dong") == dong_kiem_tra for ev in res.cac_su_kien)
        else:
            qua_dong = True  # Không yêu cầu dòng cụ thể

        ung_vien.append((res.tong_buoc, qua_dong, idx, test_id, res))

    # Lọc các test đi qua dòng đột biến (nếu có yêu cầu)
    nhom_qua_dong = [u for u in ung_vien if u[1]]
    if nhom_qua_dong:
        tap_xet = nhom_qua_dong
    else:
        # Nhánh dự phòng: không test đỏ nào đi qua dòng đột biến.
        #
        # 27/08/2026: PHẢI PHÂN BIỆT "CHẠY XONG MÀ KHÔNG QUA" VỚI "HẾT GIỜ".
        #
        # Trước đây nhánh này dán một nhãn duy nhất cho mọi ứng viên:
        # "Vết thực thi không đi qua dòng đột biến". Nhưng một vết HẾT GIỜ thì
        # `chay_trace_mot_test` trả `trang_thai = "khong_chay"` và rơi vào đây
        # — nên câu ấy nói một điều về HÀNH VI của cỗ máy trong khi sự thật
        # chỉ là phép đo chưa chạy xong.
        #
        # Đo 27/08 trên ba ca `the_cst.py` mà báo cáo vòng 4 nêu:
        #
        #     mục 89    trace 15,0 giây  -> khong_chay   (đụng trần 15)
        #     mục 97    trace 12,0 giây  -> trace_du
        #     mục 108   trace 14,4 giây  -> trace_du
        #
        # Nới trần lên 120 giây thì mục 89 chạy xong trong 15,1 giây và ra
        # `trace_du`. Tức nhãn "vết không đi qua dòng đột biến" của nó được
        # quyết bởi MỘT PHẦN MƯỜI GIÂY.
        #
        # Đúng luật CLAUDE.md §4: "phép đo không chạy phải NÓI LÀ KHÔNG CHẠY".
        # Ở đây còn tệ hơn giấu việc không chạy — nó thay việc không chạy bằng
        # một phán quyết về cỗ máy.
        tap_xet = ung_vien
        for u in tap_xet:
            if u[4].trang_thai == "khong_chay":
                # Giữ nguyên `khong_chay` và thông điệp gốc (đã ghi rõ hết giờ
                # bao nhiêu giây). Đừng đổi nó thành một câu về hành vi.
                continue
            u[4].trang_thai = "trace_khong_qua_loi"
            u[4].thong_diep = "KHÔNG ĐO ĐƯỢC: Vết thực thi không đi qua dòng đột biến"

    # Sắp xếp: ít bước nhất -> thứ tự pytest trước
    tap_xet.sort(key=lambda x: (x[0] if x[0] > 0 else 999999, x[2]))

    chot = tap_xet[0]
    ten_test_chot = chot[3]
    ket_qua_chot = chot[4]
    ket_qua_chot.so_test_do_khac = tong_so_do - 1

    return ten_test_chot, tong_so_do - 1, [u[4] for u in tap_xet]

