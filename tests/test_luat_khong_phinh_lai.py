# -*- coding: utf-8 -*-
"""`CLAUDE.md` là tệp nạp vào MỌI phiên — nó phải ở lại nhỏ.

VÌ SAO CÓ TỆP NÀY (06/09/2026)

    CLAUDE.md            83.047 byte · 1.352 dòng
       30 ngày trước      8.497 byte     -> gấp ~10 lần trong một tháng
    KY_LUAT_THUC_THI.md  76.048 byte
                        ~159 KB · ~40k token, nạp MỌI phiên

Và một phiên đã phải **nén ngữ cảnh hai lần**. Cứ đà ấy tháng sau là 800 KB.

Mục 4 chiếm 1.149/1.352 dòng, nên nó tách sang `SO_BENH_AN.md` — tệp KHÔNG tự
nạp. `CLAUDE.md` giữ luật, mỗi luật một dòng **kèm con số tạo ra nó**.

RỦI RO PHẢI CANH, không chỉ canh kích thước: chính các ca bệnh làm luật DÍNH
được. Cắt mất con số thì luật đọc ra như lời răn suông — và lời răn suông là
thứ bị phá bốn lần trong một ngày (29 bài học đã ghi, `x in y` ghi lại 7 lần,
chữ "lần thứ ba" xuất hiện 4 lần). Nên có cả cửa đòi **con số**, không chỉ cửa
đòi **ngắn**.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

LUAT = PROJECT_ROOT / "CLAUDE.md"
SO = PROJECT_ROOT / "SO_BENH_AN.md"

# Chép TAY. Đo được lúc tách: 20.906 byte. Trần 32.000 cho chỗ viết thêm, nhưng
# không rộng tới mức nuốt lại được cả sổ bệnh án (70 KB).
TRAN_BYTE_CLAUDE = 32_000
SO_CA_TOI_THIEU = 30


def _muc4(chu: str) -> str:
    i4, i5 = chu.index("## 4. Luật đã trả giá"), chu.index("## 5. Viết mã ở đây")
    return chu[i4:i5]


def test_CLAUDE_md_khong_phinh_qua_tran():
    """Tệp nạp mọi phiên. 83.047 byte là chỗ nó đã tới trước khi tách."""
    n = len(LUAT.read_bytes())
    assert n <= TRAN_BYTE_CLAUDE, (
        f"CLAUDE.md {n:,} byte, quá trần {TRAN_BYTE_CLAUDE:,} — "
        "đẩy phần kể chuyện sang SO_BENH_AN.md")


def test_so_benh_an_giu_DU_ca():
    """Tách không được làm mất ca nào."""
    assert SO.is_file(), "không có SO_BENH_AN.md"
    ca = re.findall(r"^### (.+)$", SO.read_text(encoding="utf-8"), re.M)
    assert len(ca) >= SO_CA_TOI_THIEU, f"chỉ còn {len(ca)} ca, cần ≥ {SO_CA_TOI_THIEU}"
    assert len(set(ca)) == len(ca), "có ca trùng tên"


def _neo(ten: str) -> str:
    ra = []
    for c in ten.lower():
        if c.isalnum() or c in "-_":
            ra.append(c)
        elif c.isspace():
            ra.append("-")
        elif unicodedata.category(c).startswith("M"):
            ra.append(c)
    return re.sub(r"-+", "-", "".join(ra)).strip("-")


def test_moi_luat_TRO_DUNG_mot_ca_co_that():
    """Link chết thì con trỏ vô dụng, và cả thiết kế này sụp.

    Bản đầu của bộ tách bằm chữ tiếng Việt thành gạch ngang
    (`#l-i-d-n-kh-ng-ph-i-ph-p-o`) nên **mọi link đều chết**. Chữ có dấu là CHỮ
    CÁI; GitHub giữ nguyên chúng.
    """
    co = {_neo(t) for t in re.findall(r"^### (.+)$", SO.read_text(encoding="utf-8"), re.M)}
    tro = re.findall(r"\(SO_BENH_AN\.md#([^)]+)\)", _muc4(LUAT.read_text(encoding="utf-8")))
    assert tro, "mục 4 không trỏ tới ca nào"
    chet = sorted(set(tro) - co)
    assert not chet, f"{len(chet)} link chết: {chet[:5]}"


def test_moi_luat_GIU_CON_SO_tao_ra_no():
    """Cửa chống cắt-mất-số. Ngắn mà rỗng thì tệ hơn dài mà có bằng chứng.

    *"Đừng in ra một phán quyết mà không kèm con số tạo ra nó"* — luật của
    chính tệp này. Áp cho luật thì nó cũng phải mang số.
    """
    dong = [d for d in _muc4(LUAT.read_text(encoding="utf-8")).splitlines()
            if d.startswith("- **[")]
    assert len(dong) >= SO_CA_TOI_THIEU, f"chỉ {len(dong)} luật"
    khong_so = [d.split("]")[0][5:] for d in dong if not re.search(r"\d", d.split("<br>", 1)[-1])]
    assert not khong_so, f"{len(khong_so)} luật không mang con số nào: {khong_so}"


@pytest.mark.parametrize("cum", ["x in y", "gieo", "đối chứng"])
def test_luat_van_GIU_ba_cot_song(cum):
    """Ba thứ không được rơi mất khi cắt: bệnh `x in y`, phép gieo, ca đối chứng.

    Chúng là cơ chế, không phải giai thoại. `tools/gieo.py` mới là thứ bắt được
    lỗi hôm nay — tài liệu thì tôi đã đọc rồi vẫn phá.
    """
    assert cum.lower() in LUAT.read_text(encoding="utf-8").lower(), (
        f"cắt mất {cum!r} khỏi CLAUDE.md")


def test_KY_LUAT_khong_bi_keo_vao_CLAUDE():
    """Hai tệp, hai việc. Gộp lại là dựng lại đúng cái vừa tháo ra."""
    chu = LUAT.read_text(encoding="utf-8")
    assert "KY_LUAT_THUC_THI.md" in chu, "CLAUDE.md không còn trỏ tới đặc tả"
    assert len(chu.encode("utf-8")) < len(
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_bytes()), (
        "CLAUDE.md đã to hơn cả đặc tả — nó là tệp TÓM TẮT")
