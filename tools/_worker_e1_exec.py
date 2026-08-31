# -*- coding: utf-8 -*-
"""tools/_worker_e1_exec.py — E1 Worker thực thi phân tích định vị lỗi bên trong temp clone.

Chạy hoàn toàn bên trong temp clone, không truy cập kho gốc hay mạng bên ngoài.
Thực hiện 4 bước:
1. Thu vết dòng chạy trên test chọn (Trace).
2. Liệt kê 5 họ phép nghịch AST và lọc ứng viên theo dòng chạy.
3. Lật thử trên test chọn (chỉ giữ ứng viên làm test chọn XANH).
4. Kiểm thử hồi quy toàn bộ suite bằng selector:
   `python -B -X utf8 -m pytest tests -m "not e1_control" -q --no-header -p no:cacheprovider`
"""
from __future__ import annotations

import ast
import difflib
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.trace_runtime import chot_test_can_trace

PY = sys.executable

# 24/08/2026: tệp này từng chép nguyên 3 hằng số + 13 hàm/lớp từ
# `core/lat_nguoc.py`. Đo bằng AST, bỏ docstring: 13/14 tên trùng GIỐNG HỆT
# TỪNG NÚT; chỉ `_chon_test_va_dong` là khác thật nên giữ lại bên dưới.
#
# Cùng ngày, CẢ HAI bản đều phải nhận đúng một bản vá (`lat_tren_van_ban`,
# `suite_khong_do_duoc`, `diff_basis`). Lần ấy làm đủ cả hai, nhưng nhờ cẩn
# thận chứ không nhờ cấu trúc — mà hai bên phục vụ hai đường khác nhau:
#
#     core/lat_nguoc.py         <- experiments/evidence_sprint/do_e1_ngoai_ho.py
#                                  (bộ sinh con số "0/64 lỗi ngoài họ")
#     tools/_worker_e1_exec.py  <- app thật, qua e1_supervisor_bootstrap
#
# Quên một bên thì app đo một đằng, sổ bằng chứng đo một nẻo, KHÔNG AI BÁO.
# Thêm một test canh lệch cũng được, nhưng xoá hẳn bản sao thì lệch trở thành
# KHÔNG THỂ — rẻ hơn và không có cửa nào phải bảo trì.
from core.lat_nguoc import (  # noqa: E402
    PHAM_VI_PHEP,
    _liet_ke_cho,
    _ma_sau_lat,
    _tao_unified_diff,
    doc_thong_tin_gioi_han,
)


def _chon_test_va_dong(
    tam: Path,
    tep_nguon_rel: str,
    tep_test_rel: str,
    deadline: float,
) -> dict:
    con_lai = deadline - time.monotonic()
    if con_lai <= 0:
        return {"trang_thai": "khong_chay", "vi_sao": "Hết trần thời gian trước khi trace", "test": "", "so_test_do_khac": 0, "dong_da_chay": []}

    ten_chot, so_khac, danh_sach = chot_test_can_trace(
        tep_nguon=tep_nguon_rel,
        tep_test=tep_test_rel,
        cwd=tam,
    )
    if not ten_chot or not danh_sach:
        # Xem chú thích cùng ngày ở core/trace_runtime.py: "không có test đỏ" và
        # "chưa đo được" là hai chuyện, không được nói bằng cùng một câu.
        vi_sao = (danh_sach[0].thong_diep
                  if danh_sach and danh_sach[0].trang_thai == "khong_chay"
                  else "Đã chạy tệp test: không có test nào bị đỏ")
        return {"trang_thai": "khong_chay", "vi_sao": vi_sao, "test": "", "so_test_do": 0, "so_test_do_khac": 0, "dong_da_chay": []}

    chot_res = danh_sach[0]
    return {
        "trang_thai": chot_res.trang_thai,
        "vi_sao": chot_res.thong_diep,
        "test": ten_chot,
        "so_test_do": so_khac + 1,
        "so_test_do_khac": so_khac,
        "dong_da_chay": chot_res.dong_da_chay,
        "so_buoc": chot_res.tong_buoc,
    }


def chay_worker(
    tam_clone: Path,
    tep_nguon_rel: str,
    tep_test_rel: str,
    source_sha256: str = "",
    test_sha256: str = "",
    filter_mutate_timeout_s: float = 60.0,
    full_suite_timeout_s: float = 180.0,
) -> dict:
    t0_tong = time.monotonic()
    tep_nguon_rel = tep_nguon_rel.replace("\\", "/")
    tep_test_rel = tep_test_rel.replace("\\", "/")

    target_file = tam_clone / tep_nguon_rel
    test_file = tam_clone / tep_test_rel

    if not target_file.is_file() or not test_file.is_file():
        return {
            "trang_thai": "khong_do_duoc",
            "reason": "Tệp nguồn hoặc tệp test không tồn tại trong clone",
        }

    raw_goc = target_file.read_text(encoding="utf-8")
    try:
        ast.parse(raw_goc)
    except Exception as exc:
        return {
            "trang_thai": "khong_do_duoc",
            "reason": f"Không thể parse AST tệp nguồn: {exc}",
        }

    cac_cho_all = _liet_ke_cho(raw_goc)
    n_before = len(cac_cho_all)

    # Bước 1: Trace dòng chạy trên test đỏ
    t0_loc = time.monotonic()
    deadline_loc = t0_loc + filter_mutate_timeout_s
    trace = _chon_test_va_dong(tam_clone, tep_nguon_rel, tep_test_rel, deadline_loc)

    if trace.get("trang_thai") != "trace_du":
        return {
            "trang_thai": "khong_tim_thay" if trace.get("so_test_do") == 0 else "khong_do_duoc",
            "source_path": tep_nguon_rel,
            "source_sha256": source_sha256,
            "test_file": tep_test_rel,
            "test_sha256": test_sha256,
            "selected_test": trace.get("test", ""),
            "other_red_test_count": trace.get("so_test_do_khac", 0),
            "executed_lines": trace.get("dong_da_chay", []),
            "candidate_count_before": n_before,
            "candidate_count_after": 0,
            "scope_operations": PHAM_VI_PHEP,
            "elapsed_filter_mutate_s": round(time.monotonic() - t0_loc, 1),
            "elapsed_full_suite_s": 0.0,
            "analysis_on_temp_copy": True,
            "model_calls": 0,
            "external_submit": False,
            "candidates": [],
            "reason": trace.get("vi_sao", "Không có vết dòng đầy đủ"),
            "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
        }

    selected_test = trace["test"]
    dong_da_chay = set(trace["dong_da_chay"])

    # Bước 2: Lọc các chỗ nằm trên dòng đã chạy
    cac_cho_loc = [c for c in cac_cho_all if c[1] in dong_da_chay]
    n_after = len(cac_cho_loc)

    # Bước 3: Lật thử trên test chọn
    xanh_selected: list[dict] = []
    for chi_so, dong, mo_ta in cac_cho_loc:
        if time.monotonic() > deadline_loc:
            break
        ma_moi, da = _ma_sau_lat(raw_goc, chi_so)
        target_file.write_text(ma_moi, encoding="utf-8")
        try:
            r = subprocess.run(
                [PY, "-B", "-X", "utf8", "-m", "pytest", tep_test_rel, "-q", "--no-header", "-x", "-p", "no:cacheprovider"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tam_clone),
                timeout=10.0,
            )
            if r.returncode == 0:
                diff_text = _tao_unified_diff(raw_goc, ma_moi, tep_nguon_rel)
                xanh_selected.append({
                    "index": chi_so,
                    "line": dong,
                    "operation": mo_ta,
                    "ma": ma_moi,
                    "unified_diff": diff_text,
                })
        except Exception:
            continue

    # Khôi phục file về nguyên trạng sau bước lọc + lật
    target_file.write_text(raw_goc, encoding="utf-8")
    t_lat_end = time.monotonic()
    elapsed_filter_mutate = round(t_lat_end - t0_loc, 1)

    if elapsed_filter_mutate > filter_mutate_timeout_s:
        return {
            "trang_thai": "khong_do_duoc",
            "source_path": tep_nguon_rel,
            "source_sha256": source_sha256,
            "test_file": tep_test_rel,
            "test_sha256": test_sha256,
            "selected_test": selected_test,
            "other_red_test_count": trace.get("so_test_do_khac", 0),
            "executed_lines": sorted(dong_da_chay),
            "candidate_count_before": n_before,
            "candidate_count_after": n_after,
            "scope_operations": PHAM_VI_PHEP,
            "elapsed_filter_mutate_s": elapsed_filter_mutate,
            "elapsed_full_suite_s": 0.0,
            "analysis_on_temp_copy": True,
            "model_calls": 0,
            "external_submit": False,
            "candidates": [],
            "reason": "Lọc + lật vượt trần thời gian quy định",
            "limitation": "Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.",
        }

    # Bước 4: Full suite regression cho các ứng viên làm test chọn XANH
    t0_suite = time.monotonic()
    candidates_out: list[dict] = []
    co_ban_va_xanh_suite = False

    for cand in xanh_selected:
        target_file.write_text(cand["ma"], encoding="utf-8")
        full_suite_status = "ĐỎ"
        so_test_hong = 0
        ly_do_khong_do = ""
        try:
            r_suite = subprocess.run(
                [
                    PY, "-B", "-X", "utf8", "-m", "pytest", "tests",
                    "-m", "not e1_control",
                    "-q", "--no-header", "-p", "no:cacheprovider",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(tam_clone),
                timeout=full_suite_timeout_s,
            )
            out_text = (r_suite.stdout or "") + "\n" + (r_suite.stderr or "")
            if r_suite.returncode == 0:
                full_suite_status = "XANH"
                co_ban_va_xanh_suite = True
                so_test_hong = 0
            else:
                if "ERROR collecting" in out_text or "errors during collection" in out_text or r_suite.returncode not in (0, 1):
                    full_suite_status = "suite_khong_do_duoc"
                    ly_do_khong_do = "Lỗi thu thập test suite"
                    so_test_hong = 0
                else:
                    found_failed = False
                    for line in out_text.splitlines():
                        if "failed" in line:
                            m = re.search(r"(\d+)\s+failed", line)
                            if m:
                                so_test_hong = int(m.group(1))
                                found_failed = True
                                break
                    if not found_failed:
                        count_f = out_text.count("FAILED")
                        if count_f > 0:
                            so_test_hong = count_f
                            found_failed = True
                    if found_failed and so_test_hong > 0:
                        full_suite_status = "ĐỎ"
                    else:
                        full_suite_status = "suite_khong_do_duoc"
                        ly_do_khong_do = "Không đo được kết quả suite"
                        so_test_hong = 0
        except subprocess.TimeoutExpired:
            full_suite_status = "suite_khong_do_duoc"
            ly_do_khong_do = f"Quá giờ ({full_suite_timeout_s}s)"
            so_test_hong = 0
        except Exception as exc:
            full_suite_status = "suite_khong_do_duoc"
            ly_do_khong_do = f"Ngoại lệ: {exc}"
            so_test_hong = 0

        cand_entry = {
            "index": cand["index"],
            "line": cand["line"],
            "operation": cand["operation"],
            "unified_diff": cand["unified_diff"],
            # 24/08: diff nay sinh tu _tao_unified_diff(raw_goc, ma_moi) — van ban
            # goc, KHONG con di qua ast.unparse. Nhan cu doc nguoc voi thuc te.
            "diff_basis": "van_ban_goc_temp_copy",
            "selected_test_status": "XANH",
            "full_suite_status": full_suite_status,
            "so_test_hong": so_test_hong if full_suite_status == "ĐỎ" else 0,
            "ma": cand["ma"],
        }
        if ly_do_khong_do:
            cand_entry["ly_do_suite"] = ly_do_khong_do
        candidates_out.append(cand_entry)

    # Khôi phục lại file gốc
    target_file.write_text(raw_goc, encoding="utf-8")
    elapsed_suite = round(time.monotonic() - t0_suite, 1)

    if co_ban_va_xanh_suite:
        trang_thai = "tim_thay"
        reason = f"Đã tìm thấy {sum(1 for c in candidates_out if c['full_suite_status'] == 'XANH')} bản vá xanh toàn bộ suite."
    elif any(c["full_suite_status"] == "suite_khong_do_duoc" for c in candidates_out) and not any(c["full_suite_status"] == "XANH" for c in candidates_out):
        trang_thai = "suite_khong_do_duoc"
        reasons_list = [c["ly_do_suite"] for c in candidates_out if c.get("ly_do_suite")]
        reasons_str = f" ({', '.join(reasons_list)})" if reasons_list else ""
        reason = f"Ứng viên làm xanh test chọn nhưng suite không đo được{reasons_str}."
    elif candidates_out:
        trang_thai = "ung_vien_khong_qua_suite"
        reason = f"Có {len(candidates_out)} ứng viên làm xanh test chọn nhưng không vượt qua toàn bộ test suite."
    else:
        trang_thai = "khong_tim_thay"
        reason = "Không có ứng viên nào trong phạm vi 5 phép làm xanh test chọn."

    return {
        "trang_thai": trang_thai,
        "source_path": tep_nguon_rel,
        "source_sha256": source_sha256,
        "test_file": tep_test_rel,
        "test_sha256": test_sha256,
        "selected_test": selected_test,
        "other_red_test_count": trace.get("so_test_do_khac", 0),
        "executed_lines": sorted(dong_da_chay),
        "candidate_count_before": n_before,
        "candidate_count_after": n_after,
        "scope_operations": PHAM_VI_PHEP,
        "regression_suite_selector": "not e1_control",
        "elapsed_filter_mutate_s": elapsed_filter_mutate,
        "elapsed_full_suite_s": elapsed_suite,
        "analysis_on_temp_copy": True,
        "model_calls": 0,
        "external_submit": False,
        "candidates": candidates_out,
        "reason": reason,
        "limitation": doc_thong_tin_gioi_han(tam_clone),
    }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"trang_thai": "khong_do_duoc", "reason": "Thiếu tham số chạy worker"}))
        sys.exit(1)

    tep_nguon = sys.argv[1]
    tep_test = sys.argv[2]
    source_sha = sys.argv[3] if len(sys.argv) > 3 else ""
    test_sha = sys.argv[4] if len(sys.argv) > 4 else ""

    tam_clone = Path(".").resolve()

    # Worker GHI ĐÈ tệp nguồn để thử từng phép lật (dòng 245 + vòng lặp bên dưới),
    # và chỉ ghi trả lại ở cuối. Chạy nhầm ở kho thật thì mỗi lần nó chết giữa
    # chừng là để lại tệp ĐANG MANG LỖI GIEO trên đĩa.
    #
    # Đã xảy ra 24/08/2026: `core/dong_ho.py` trên đĩa lệch HEAD 1762/1722 byte.
    # Lần ấy chỉ là 40 dòng CRLF vì lượt ghi trả lại có chạy — nhưng nó chứng minh
    # worker đã đụng vào kho thật, và lần sau chết sớm hơn thì mất nội dung.
    #
    # Bản sao do e1_supervisor_bootstrap.py dựng KHÔNG chép `.git` (dòng 192).
    # Kho thật thì có. Đó là dấu hiệu rẻ nhất và không đoán được nhầm.
    if (tam_clone / ".git").exists():
        print(json.dumps({
            "trang_thai": "khong_do_duoc",
            "reason": (
                "Từ chối chạy: thư mục hiện tại có .git nên đây là kho thật, "
                "không phải bản sao tạm. Worker ghi đè tệp nguồn khi thử phép lật. "
                "Hãy gọi qua tools/e1_supervisor_bootstrap.py, hoặc cd sang bản sao."
            ),
            "cwd": str(tam_clone),
        }, ensure_ascii=False, indent=2))
        sys.exit(2)

    res = chay_worker(
        tam_clone=tam_clone,
        tep_nguon_rel=tep_nguon,
        tep_test_rel=tep_test,
        source_sha256=source_sha,
        test_sha256=test_sha,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
