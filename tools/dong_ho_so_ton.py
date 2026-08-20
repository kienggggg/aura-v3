# -*- coding: utf-8 -*-
"""Đóng hồ sơ 9 lượt hỏng còn tồn, mỗi lượt một lý do THẬT.

Omega 18/08 báo 17 việc. Soát tay từng lượt thì ra ba nhóm khác hẳn nhau, và
gộp chúng làm một là cách nhanh nhất để cái sổ mất giá trị:

  ĐÃ VÁ, lượt cũ là lịch sử   4 lượt — nguyên nhân không còn trong mã hiện tại
  MÔI TRƯỜNG, không phải mã   3 lượt — máy hết RAM lúc chạy
  CHƯA RÕ, cần đo lại         2 lượt — Writer hết giờ / đẻ ra tệp rỗng

Nhóm 3 KHÔNG đóng là "đã sửa". Đóng nó bằng lời hứa là đúng cái bệnh mà cả
tài liệu này cảnh báo: lời dặn không phải phép đo.

    venv\\Scripts\\python.exe tools\\dong_ho_so_ton.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import DATA_DIR                                  # noqa: E402

R = DATA_DIR / "evidence_sprint" / "runs"
XAC_MINH = "run_20260819_011133_6b0f135e"

DONG = {
    # --- nhom 1: nguyen nhan da het trong ma hien tai ----------------------
    "run_20260814_033852_7498bfa5": (
        "INVALID",
        "FAIL 'SAPI voice Microsoft An not found or failed'. Cau bao loi nay SAI: "
        "ma da co duong lui sang giong Microsoft bat ky (studio.py dong 20-22), va "
        "no in ra cho MOI ma thoat khac 0 chu khong rieng loi giong - tuc no khang "
        "dinh mot nguyen nhan no chua he kiem. Da va 19/08: bat lay loi PowerShell "
        "va bao dung ma thoat. Nguyen nhan that cua luot nay khong con truy duoc vi "
        "ban cu vut sach stderr. Xac minh duong TTS con chay: " + XAC_MINH + " PASS."),
    "run_20260814_033914_251a2d0a": (
        "INVALID",
        "Cung loi va cung cau bao loi sai nhu run_20260814_033852_7498bfa5. Da va "
        "19/08. Xac minh: " + XAC_MINH + " PASS."),
    "run_20260814_034034_ab06a7a3": (
        "INVALID",
        "FAIL 'stdout and stderr arguments may not be used with capture_output' - "
        "dung sai API subprocess. Soat 19/08 toan bo experiments/evidence_sprint: 0 "
        "cho con truyen ca hai. Nguyen nhan da het trong ma hien tai. Xac minh: "
        + XAC_MINH + " PASS."),
    "run_20260816_015207_fff695a0": (
        "INVALID",
        "Khong co metrics.json: luot Studio chet giua chung truoc khi ghi. Ba tep "
        "con lai deu co. Duong Studio hien tai chay het bai: " + XAC_MINH + " PASS."),

    # --- nhom 2: may het RAM, khong phai loi ma ---------------------------
    "run_20260814_024320_a37ed4f0": (
        "INVALID",
        "BLOCKED(environment): may con 4,16 GB trong, can 4,5 GB. Day la chan cua "
        "MOI TRUONG, khong phai loi ma - khong co gi de sua. Ghi lai de lan sau "
        "biet: mot ca chi mot agent chay, va Delta cuc bo chiem tron may 16 phut "
        "moi de."),
    "run_20260814_034528_c463ebd5": (
        "INVALID",
        "BLOCKED(environment): may con 2,51 GB trong, can 4,5 GB. Chan moi truong."),
    "run_20260816_010805_92232321": (
        "INVALID",
        "BLOCKED(environment): may con 0,74 GB trong, can 4,5 GB - nang nhat trong "
        "ba luot bi chan. Chan moi truong."),
}

# --- nhom 3: CHUA RO, co y KHONG dong -------------------------------------
# run_20260816_010908_dfc823eb  FAIL 'timed out'          (writer, qwen3.5:4b)
# run_20260816_011933_1774efb2  ch03.md rong 0 byte       (writer, qwen3.5:4b)
#
# Hai luot nay deu cua phong Writer, va nguyen nhan CHUA duoc do. Dong chung
# bang mot cau "chac da sua roi" la bien mot dieu chua biet thanh mot dieu da
# xu ly - dung benh ma tai lieu nay canh bao. De nguyen cho Omega keu tiep,
# den khi co ai chay lai Writer va do that.
CHUA_DONG = ("run_20260816_010908_dfc823eb", "run_20260816_011933_1774efb2")


def main() -> int:
    """Đóng các lượt còn treo trong sổ bằng cách ghi `audit.json` kèm lý do."""
    sys.stdout.reconfigure(encoding="utf-8")
    for ten, (tt, ly_do) in DONG.items():
        d = R / ten
        if not d.is_dir():
            print("  BO QUA " + ten + ": khong co thu muc")
            continue
        f = d / "audit.json"
        if f.is_file():
            print("  BO QUA " + ten + ": da co audit.json, khong ghi de")
            continue
        f.write_text(json.dumps({"audit_status": tt, "reason": ly_do},
                                ensure_ascii=False), encoding="utf-8")
        print("  dong " + ten)
    print("\n  CO Y de ngo " + str(len(CHUA_DONG)) + " luot Writer chua ro nguyen nhan:")
    for t in CHUA_DONG:
        print("    " + t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
