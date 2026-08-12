"""Canh bộ đếm sổ phiên — thứ dùng để trả lời "AURA hỏng ở đâu" bằng ĐẾM.

Bộ đếm mà đếm sai thì tệ hơn không có: nó cho ra một con số trông như phép đo.
Ba chỗ dễ sai nhất, canh cả ba:
  1. trộn bản ghi cũ (không có số) vào phần đo được
  2. bỏ im lặng dòng hỏng
  3. bắt nhãn `timeout` đáng ngờ — chính thứ 12/08/2026 phải dựng lại bằng tay
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from dem_so_phien import doc, nhan_dang_ngo  # noqa: E402

_SCHEMA = "aura.chat.exchange.v1"


def _ghi(thu_muc: Path, ten: str, rows: list[dict]) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    (thu_muc / f"{ten}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


def _row(**thay) -> dict:
    row = {
        "schema": _SCHEMA,
        "at": "2026-08-12T10:00:00+00:00",
        "actor_id": "owner:web",
        "session_id": "s",
        "request_id": "r",
        "channel": "web",
        "status": "ok",
        "used_web": False,
        "user": "hỏi",
        "assistant": "đáp",
    }
    row.update(thay)
    return row


def test_doc_bao_ra_dong_hong_thay_vi_nuot(tmp_path):
    """Sổ bị cắt giữa chừng thì phải BÁO, không được im lặng trả số nhỏ hơn."""
    tep = tmp_path / "a.jsonl"
    tmp_path.mkdir(parents=True, exist_ok=True)
    tep.write_text(
        json.dumps(_row(), ensure_ascii=False) + "\n"
        + "khong-phai-json\n"
        + json.dumps({"schema": "sai", "user": "độc"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    ban_ghi, so_tep, bo = doc(tmp_path)
    assert len(ban_ghi) == 1
    assert so_tep == 1
    assert bo == 2, "dòng hỏng và dòng sai schema đều phải được đếm ra"


def test_ban_ghi_cu_khong_bi_tron_vao_phan_do_duoc(tmp_path):
    """Bản ghi cũ không có `latency_ms`. Trộn vào là ra con số nói dối."""
    _ghi(tmp_path, "a", [
        _row(status="timeout"),                                  # cũ
        _row(status="timeout", latency_ms=90_000, stage="model_call"),  # mới
    ])
    ban_ghi, _, _ = doc(tmp_path)
    cu = [d for d in ban_ghi if "latency_ms" not in d]
    moi = [d for d in ban_ghi if "latency_ms" in d]
    assert len(cu) == 1 and len(moi) == 1
    # Lượt CŨ không có số nên không được coi là sạch, cũng không được coi là ngờ.
    assert nhan_dang_ngo(cu, 90.0) == []


def test_bat_duoc_nhan_timeout_khong_cham_tran():
    """Đúng cảnh 10/08: ghi `timeout` nhưng lượt chỉ chạy 8 giây trên trần 90."""
    that = _row(status="timeout", latency_ms=90_400, stage="model_call")
    gia = _row(status="timeout", latency_ms=8_000, stage="model_call")
    ngo = nhan_dang_ngo([that, gia], 90.0)
    assert ngo == [gia], "chỉ lượt KHÔNG chạm trần mới là nhãn đáng ngờ"

    # Đúng trần và hơi quá trần đều là timeout thật.
    for ms in (81_000, 90_000, 95_000):
        assert nhan_dang_ngo([_row(status="timeout", latency_ms=ms)], 90.0) == []

    # Trần khác thì ngưỡng phải đi theo, không được ghim cứng 90 giây.
    assert nhan_dang_ngo([_row(status="timeout", latency_ms=8_000)], 5.0) == []


def test_chi_soi_luot_timeout_khong_dung_cham_luot_khac():
    """Một lượt `ok` nhanh không phải nhãn đáng ngờ — đừng bắt nhầm."""
    nhanh_ma_ok = _row(status="ok", latency_ms=12, stage="model_call")
    assert nhan_dang_ngo([nhanh_ma_ok], 90.0) == []
