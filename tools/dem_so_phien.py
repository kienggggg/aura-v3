# -*- coding: utf-8 -*-
"""Đếm sổ phiên: lượt nào hỏng, hỏng ở BƯỚC nào, và mất bao lâu.

VÌ SAO CÓ TỆP NÀY — 12/08/2026: hỏi "AURA hỏng ở đâu" thì phải dựng lại bằng
tay từ 71 tệp .jsonl, và câu trả lời rút ra được chỉ là "8 lượt timeout" — không
nói được timeout ở bước nào, cũng không kiểm được nhãn đó có đúng không.

HAI LOẠI BẢN GHI, KHÔNG ĐƯỢC TRỘN:
    cũ   trước 12/08/2026 — không có `latency_ms`/`stage`
    mới  có cả hai
Đếm gộp là ra một con số nói dối: mọi lượt cũ sẽ thành "không rõ bước", đọc y
hệt "hỏng ở chỗ không xác định". Đó đúng là bệnh đã trả giá ("phép đo không
chạy phải NÓI LÀ KHÔNG CHẠY"), nên ở đây tách hẳn và in riêng.

NHÃN ĐÁNG NGỜ: một lượt `timeout` mà thời lượng KHÔNG chạm trần thì nhãn sai —
nó gãy vì chuyện khác rồi bị gọi là quá giờ. Đây chính là thứ bắt được 6/8 lượt
`timeout` hôm 10/08 (ghi sổ cách nhau 8–25 giây trong khi trần là 90 giây).

    venv\\Scripts\\python.exe tools\\dem_so_phien.py [--tran GIÂY] [--so THƯ_MỤC]

Mã thoát: 0 không có nhãn đáng ngờ · 1 có.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
_SCHEMA = "aura.chat.exchange.v1"


def _so_mac_dinh() -> Path:
    tu_moi_truong = os.environ.get("AURA_CHAT_TRANSCRIPT_ROOT", "").strip()
    return Path(tu_moi_truong) if tu_moi_truong else GOC / "data" / "chat_sessions"


def doc(thu_muc: Path) -> tuple[list[dict], int, int]:
    """-> (bản ghi hợp lệ, số tệp, số dòng bỏ vì hỏng).

    Dòng hỏng KHÔNG im lặng: sổ có thể bị cắt giữa chừng khi máy tắt đột ngột,
    và một con số "0 lượt" vì đọc trượt thì tệ hơn nhiều so với báo ra.
    """
    ban_ghi: list[dict] = []
    so_tep = bo = 0
    for tep in sorted(thu_muc.glob("*.jsonl")):
        so_tep += 1
        for dong in tep.read_text(encoding="utf-8", errors="replace").splitlines():
            dong = dong.strip()
            if not dong:
                continue
            try:
                d = json.loads(dong)
            except ValueError:
                bo += 1
                continue
            if not isinstance(d, dict) or d.get("schema") != _SCHEMA:
                bo += 1
                continue
            d["_tep"] = tep.stem[:12]
            ban_ghi.append(d)
    return ban_ghi, so_tep, bo


def nhan_dang_ngo(ban_ghi: list[dict], tran_giay: float) -> list[dict]:
    """Lượt ghi `timeout` mà thời lượng KHÔNG chạm trần -> nhãn sai.

    Ngưỡng 90% trần chứ không phải đúng bằng trần: một lượt quá giờ thật thì
    dừng ở khoảng trần cộng chút xíu, không bao giờ dừng ở nửa trần.

    Chỉ soi được bản ghi có `latency_ms`. Bản ghi cũ không có số thì KHÔNG được
    coi là sạch — hàm này bỏ qua chúng, và chỗ gọi phải nói ra là đã bỏ qua.
    """
    nguong = tran_giay * 1000 * 0.9
    return [
        d for d in ban_ghi
        if d.get("status") == "timeout"
        and isinstance(d.get("latency_ms"), int)
        and not isinstance(d.get("latency_ms"), bool)
        and d["latency_ms"] < nguong
    ]


def _bach_phan(so: list[int], p: float) -> int:
    if not so:
        return 0
    xep = sorted(so)
    return xep[min(len(xep) - 1, int(round((len(xep) - 1) * p)))]


def _bang(tieu_de: str, dem: Counter, tong: int) -> None:
    print(f"  {tieu_de}")
    if not dem:
        print("      (không có)")
        return
    for ten, n in dem.most_common():
        pct = f"{n * 100 / tong:4.1f}%" if tong else "    -"
        print(f"      {ten:<16} {n:>5}  {pct}")


def main() -> int:
    """Đếm số lượt đã vào sổ phiên và in ra cho người đọc."""
    # Ép UTF-8 Ở ĐÂY, không phải lúc import: đổi `sys.stdout` ở cấp module thì
    # chỉ cần `import dem_so_phien` là bộ bắt output của pytest gãy
    # ("I/O operation on closed file"), và cả tệp thành không test được.
    # Nhập một module phải không có tác dụng phụ.
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    p = argparse.ArgumentParser()
    p.add_argument("--so", type=Path, default=None, help="thư mục sổ phiên")
    p.add_argument("--tran", type=float, default=None,
                   help="trần một lượt, giây (mặc định đọc AURA_CHAT_TIMEOUT_S, "
                        "không có thì 90)")
    args = p.parse_args()

    thu_muc = args.so or _so_mac_dinh()
    if not thu_muc.is_dir():
        print(f"  không thấy sổ: {thu_muc}")
        return 2
    tran = args.tran
    if tran is None:
        try:
            tran = float(os.environ.get("AURA_CHAT_TIMEOUT_S", "") or 90.0)
        except ValueError:
            tran = 90.0

    ban_ghi, so_tep, bo = doc(thu_muc)
    if not ban_ghi:
        print(f"  {thu_muc}\n  sổ rỗng — chưa có lượt nào")
        return 0

    cu = [d for d in ban_ghi if "latency_ms" not in d]
    moi = [d for d in ban_ghi if "latency_ms" in d]
    print(f"  {thu_muc}")
    print(f"  {so_tep} phiên · {len(ban_ghi)} lượt"
          + (f" · BỎ {bo} dòng hỏng" if bo else ""))
    print()
    print(f"  bản ghi CŨ  (không có latency_ms/stage): {len(cu):>5}")
    print(f"  bản ghi MỚI (đo được)                 : {len(moi):>5}")
    print()

    _bang("theo trạng thái — TẤT CẢ lượt:",
          Counter(str(d.get("status")) for d in ban_ghi), len(ban_ghi))
    print()

    if not moi:
        print("  Chưa có bản ghi mới nào nên KHÔNG đếm được theo bước và thời")
        print("  lượng. Đây là 'chưa đo', không phải 'không có vấn đề'.")
    else:
        _bang("theo bước kết thúc — chỉ bản ghi MỚI:",
              Counter(str(d.get("stage") or "(trống)") for d in moi), len(moi))
        print()
        ms = [int(d["latency_ms"]) for d in moi
              if isinstance(d.get("latency_ms"), int)]
        print(f"  thời lượng (ms) — {len(ms)} lượt đo được:")
        print(f"      p50 {_bach_phan(ms,0.5):>7}   p90 {_bach_phan(ms,0.9):>7}"
              f"   max {max(ms) if ms else 0:>7}")
        print()
        cham = sorted(moi, key=lambda d: -int(d.get("latency_ms") or 0))[:5]
        print("  5 lượt LÂU NHẤT:")
        for d in cham:
            print(f"      {int(d['latency_ms']):>7}ms  {str(d.get('status')):<14}"
                  f" {str(d.get('stage') or '-'):<13} {str(d.get('user',''))[:44]}")
        print()

    hong = [d for d in ban_ghi if d.get("status") != "ok"]
    print(f"  LƯỢT HỎNG: {len(hong)}")
    for d in sorted(hong, key=lambda x: str(x.get("at", ""))):
        ms = d.get("latency_ms")
        so_ms = f"{int(ms):>7}ms" if isinstance(ms, int) else "      —"
        print(f"      {str(d.get('at',''))[:19]}  {so_ms}  "
              f"{str(d.get('status')):<15} {str(d.get('stage') or '-'):<13}"
              f" {str(d.get('user',''))[:40]}")

    # Nhãn timeout mà chưa chạm trần = nhãn sai. Chỉ soi được ở bản ghi MỚI;
    # bản ghi cũ thì đành chịu, và phải nói ra chứ không lờ đi.
    nguong = tran * 1000 * 0.9
    ngo = nhan_dang_ngo(moi, tran)
    to_cu = sum(1 for d in cu if d.get("status") == "timeout")
    print()
    print(f"  NHÃN ĐÁNG NGỜ (trần {tran:g}s → ngưỡng {nguong:.0f}ms): {len(ngo)}")
    for d in ngo:
        print(f"      {str(d.get('at',''))[:19]}  {d['latency_ms']}ms  "
              f"< ngưỡng mà vẫn ghi 'timeout' — {str(d.get('user',''))[:40]}")
    if to_cu:
        print(f"  ({to_cu} lượt timeout nằm ở bản ghi CŨ — không có số để soi.)")
    return 1 if ngo else 0


if __name__ == "__main__":
    raise SystemExit(main())
