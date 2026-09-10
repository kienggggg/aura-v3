# -*- coding: utf-8 -*-
"""Một kế hoạch không mang KẾT CỤC thì đọc thành thì hiện tại.

VÌ SAO CÓ TỆP NÀY (10/09/2026)

`KE_HOACH_VIET_TRUYEN_2026-09-03.md` để nguyên dòng đầu:

    **Trạng thái: CHỜ DUYỆT. Chưa viết dòng mã nào.**

suốt **bảy ngày** sau khi `core/viet_truyen.py` đã chạy với 44 bài test. Ai mở
tệp ấy ra đọc sẽ tin rằng chưa có gì được dựng.

Và `KE_HOACH_VO_TRONG_SUOT_2026-09-05.md` không có dòng trạng thái NÀO, trong
khi nó giao đúng một nửa: mốc tiến độ có (`/api/tien_do`), stream token không
(`"stream": False` còn ở cả bốn chỗ). Không có nửa nào trong tệp nói ra điều
ấy — nên nó đọc được thành "cả hai đang chờ" hoặc "cả hai đã xong", và cả hai
cách đọc đều sai.

Cùng họ với ca *"nhãn đã đo không mang ngày thì đọc thành thì hiện tại"* ghi
sáng nay: một câu trạng thái đứng yên trong khi cái nó mô tả đi tiếp.

CƠ CHẾ, KHÔNG PHẢI LỜI RĂN: một cái neo máy đọc được, và một phép so với ĐĨA.
Trạng thái tự khai không phải trạng thái — nên bài `test_CHUA_DUYET_phai_khop
_DIA` không tin cái neo, nó đi xem tệp mã có tồn tại không.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

# Chép TAY từ khối `CHOT:ket-cuc-ke-hoach` trong `KY_LUAT_THUC_THI.md`.
# Đóng, không mở rộng bằng cách đoán: thêm một trạng thái là phải sửa CẢ HAI
# chỗ, và `test_TRANG_THAI_khop_dac_ta` bắt nếu chỉ sửa một.
TRANG_THAI_HOP_LE = {
    "CHUA_DUYET",     # gửi đi rồi, chưa ai đụng vào mã
    "DANG_LAM",       # đang dựng, chưa xong
    "DA_GIAO",        # giao đủ
    "GIAO_MOT_NUA",   # giao một phần, phần còn lại PHẢI kể ra
    "KHONG_GIAO",     # đo xong, quyết định không giao
}
NEO = re.compile(r"<!-- KET_CUC:([A-Z_]+) · (\d{2}/\d{2}/\d{4}) -->")
# Chỉ bắt đường dẫn mã sản phẩm. `tests/` không tính — kế hoạch nào cũng nhắc.
MA_SP = re.compile(r"`((?:core|tools|interface)/[a-z_0-9]+\.py)`")


def _ke_hoach() -> list[Path]:
    ra = sorted(PROJECT_ROOT.glob("KE_HOACH_*.md"))
    ra += sorted((PROJECT_ROOT / "docs").glob("KE_HOACH_*.md"))
    return ra


def test_CO_ke_hoach_de_ma_kiem():
    """Không tìm thấy tệp nào thì mọi bài dưới đây xanh vì rỗng.

    Đây là ca `KHÔNG ĐO ĐƯỢC` đội lốt `đạt` — bệnh đã ghi trong `CLAUDE.md`.
    Đo 10/09/2026: **4** kế hoạch.
    """
    assert len(_ke_hoach()) >= 4, f"chỉ thấy {len(_ke_hoach())} kế hoạch"


@pytest.mark.parametrize("tep", _ke_hoach(), ids=lambda p: p.name)
def test_MOI_ke_hoach_mang_dung_MOT_neo_KET_CUC(tep: Path):
    """Một chỗ cố định, máy đọc được. Ba tệp đang viết ba kiểu câu khác nhau
    và tệp thứ tư không viết gì — nên đọc bằng mắt là không đọc được."""
    tim = NEO.findall(tep.read_text(encoding="utf-8"))
    assert len(tim) == 1, (
        f"{tep.name}: có {len(tim)} neo KET_CUC, cần đúng 1 — "
        "dạng `<!-- KET_CUC:DA_GIAO · 10/09/2026 -->`")
    assert tim[0][0] in TRANG_THAI_HOP_LE, (
        f"{tep.name}: trạng thái {tim[0][0]!r} không có trong "
        f"{sorted(TRANG_THAI_HOP_LE)}")


@pytest.mark.parametrize("tep", _ke_hoach(), ids=lambda p: p.name)
def test_CHUA_DUYET_phai_khop_DIA(tep: Path):
    """KHÔNG tin cái neo — đi xem đĩa.

    *"Trạng thái tự khai không phải trạng thái"* (02/09: bảy phòng tự khai
    `ONLINE`). Neo ghi `CHUA_DUYET` mà tệp mã kế hoạch nhắc tới đã nằm trên
    đĩa thì neo ấy sai, và đó đúng là cách `KE_HOACH_VIET_TRUYEN` tụt lại.
    """
    van = tep.read_text(encoding="utf-8")
    tim = NEO.findall(van)
    if not tim:
        pytest.skip("bài trên đã bắt việc thiếu neo")
    co_that = sorted({m for m in MA_SP.findall(van)
                      if (PROJECT_ROOT / m).is_file()})
    if tim[0][0] == "CHUA_DUYET":
        assert not co_that, (
            f"{tep.name} khai CHUA_DUYET nhưng mã đã có trên đĩa: {co_that}")
    else:
        # Chiều ngược cũng phải đúng, nếu không thì nhánh trên không bao giờ
        # chạy và cửa này là cửa mù: khai ĐÃ GIAO thì phải có gì đó để chỉ.
        if tim[0][0] in ("DA_GIAO", "GIAO_MOT_NUA"):
            assert co_that or "ĐÃ CÓ" in van, (
                f"{tep.name} khai {tim[0][0]} nhưng không chỉ ra được tệp mã "
                "nào trên đĩa")


def test_TRANG_THAI_khop_dac_ta():
    """Danh sách đóng phải khớp `KY_LUAT_THUC_THI.md` — hai chỗ, cãi nhau được."""
    khoi = re.search(
        r"<!-- CHOT:ket-cuc-ke-hoach -->(.*?)<!-- /CHOT:ket-cuc-ke-hoach -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:ket-cuc-ke-hoach"
    trong_dac_ta = set(re.findall(r"^\| `([A-Z_]+)` \|", khoi.group(1), re.M))
    assert trong_dac_ta == TRANG_THAI_HOP_LE, (
        f"đặc tả {sorted(trong_dac_ta)} ≠ mã {sorted(TRANG_THAI_HOP_LE)}")
