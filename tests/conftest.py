# -*- coding: utf-8 -*-
"""Bộ test KHÔNG được ghi vào `data/` thật.

VÌ SAO CÓ TỆP NÀY (10/09/2026)

Đo bằng cách chụp cây `data/` trước và sau MỘT lượt bộ đủ. Trước tệp này, sổ
cái Omega — thứ `/api/status` đếm ra `tasks_count` và `/api/ledger` hiện cho
Sếp xem — có:

    12.119 dòng
     9.170 dòng yêu cầu là "thử"
       528 dòng "vì sao thì mà là"          <- ca đề không có từ nội dung
    ~1.300 dòng "Thực thi tác vụ kiểm thử cho phòng …"

và `data/tien_do/` có 8.278 tệp, trong đó chỉ 13 tệp mang tiền tố `pipe_ui` —
tức từ giao diện thật. Phần còn lại là test.

Sổ cái là **bằng chứng trên đĩa** — chương I của `KY_LUAT_THUC_THI.md` gọi nó
là *chân lý duy nhất*. Bộ test đã viết vào đó hàng nghìn dòng giả, và giao diện
đếm chúng như việc thật.

HAI LỚP, và lớp thứ hai mới là cơ chế:

1. `_du_lieu_tam` — mỗi bài ghi vào một thư mục tạm riêng. Đây là một DANH
   SÁCH vá tay, và danh sách thì sót được.
2. `pytest_sessionstart` / `pytest_sessionfinish` — chụp `data/` thật lúc bắt
   đầu, so lúc kết thúc. Có tệp mới hay tệp bị sửa là **cả phiên đỏ**, kèm tên
   tệp. Lớp 1 sót chỗ nào thì lớp 2 bắt, và bắt ngay lượt đầu tiên.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

_DATA_THAT = PROJECT_ROOT / "data"


def _chup(goc: Path) -> dict[str, tuple[int, int]]:
    """Tên tương đối -> (cỡ, mtime_ns). Không đọc nội dung — chụp thì phải rẻ."""
    ra: dict[str, tuple[int, int]] = {}
    if not goc.is_dir():
        return ra
    for thu_muc, _, cac_tep in os.walk(goc):
        for t in cac_tep:
            p = os.path.join(thu_muc, t)
            try:
                st = os.stat(p)
            except OSError:
                continue
            ra[os.path.relpath(p, goc)] = (st.st_size, st.st_mtime_ns)
    return ra


def pytest_sessionstart(session):
    session.config._aura_data_truoc = _chup(_DATA_THAT)


def pytest_sessionfinish(session, exitstatus):
    truoc = getattr(session.config, "_aura_data_truoc", None)
    if truoc is None:
        return
    sau = _chup(_DATA_THAT)
    moi = sorted(k for k in sau if k not in truoc)
    sua = sorted(k for k in sau if k in truoc and sau[k] != truoc[k])
    if not (moi or sua):
        return
    dong = [
        "",
        "=" * 72,
        "BỘ TEST VỪA GHI VÀO data/ THẬT — cả phiên này tính là ĐỎ.",
        f"  tệp mới: {len(moi)} · tệp bị sửa: {len(sua)}",
    ]
    dong += [f"    mới  {k}" for k in moi[:15]]
    dong += [f"    sửa  {k}" for k in sua[:15]]
    dong += [
        "  Vá bằng cách cho bài ấy ghi vào thư mục tạm (xem `_du_lieu_tam`).",
        "  Nếu app AURA đang chạy song song lúc chạy test thì đây có thể là",
        "  app ghi, không phải test — tắt app rồi chạy lại.",
        "=" * 72,
    ]
    session.config.get_terminal_writer().line("\n".join(dong), red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(autouse=True)
def _du_lieu_tam(tmp_path_factory, monkeypatch):
    """Mọi đích GHI đều trỏ vào một thư mục tạm của riêng bài này.

    SỔ CÁI BỊ KHAI Ở BA NƠI — `core/omega.py`, `core/phong_noi_bo.py`,
    `interface/noi_bo_api.py` — nên cả ba phải trỏ về CÙNG MỘT tệp tạm, không
    thì bài nào ghi qua cửa này rồi đọc qua cửa kia sẽ thấy sổ rỗng.

    Chỉ vá đích GHI. Thứ test ĐỌC từ đĩa thật — chỉ mục `tra_cuu`, sổ trạng
    thái phòng, các lượt evidence — là hiện vật do công cụ chạy tay sinh ra,
    và vài bài cố ý đọc chúng.
    """
    goc = tmp_path_factory.mktemp("data")
    so_cai = goc / "omega" / "so_cai.jsonl"

    from core import omega, phong_noi_bo
    from interface import noi_bo_api

    for mod in (phong_noi_bo, noi_bo_api):
        monkeypatch.setattr(mod, "DATA_DIR", goc)
    monkeypatch.setattr(phong_noi_bo, "SO_CAI", so_cai)
    monkeypatch.setattr(noi_bo_api, "OMEGA_SO_CAI", so_cai)
    monkeypatch.setattr(noi_bo_api, "THU_MUC_TIEN_DO", goc / "tien_do")
    monkeypatch.setattr(omega, "SO_CAI", so_cai)
    monkeypatch.setattr(omega, "NHA_OMEGA", goc / "omega")
    yield goc
