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
SO_CA_TOI_THIEU = 31


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


def test_MOI_NEO_CHOT_trong_dac_ta_deu_co_CUA_DOC():
    """Một cái neo không ai kéo thì chỉ là chữ.

    BA LẦN TRONG BA NGÀY tôi viết một khối đặc tả có `<!-- CHOT:ten -->` rồi
    QUÊN viết cửa đọc nó, và cả ba lần phép gieo báo "VẪN XANH — CỬA MÙ":

        08/09  CHOT:epsilon-go
        09/09  CHOT:bo-dich-rust-cpp
        10/09  CHOT:bo-can-tat-dinh

    Sửa từng ca thì lần thứ tư vẫn tới. Bài này sửa cả LOẠI BỆNH: mọi neo
    trong đặc tả phải được ít nhất một tệp test nhắc tới. Neo sinh ra để cửa
    canh đọc **đúng một chỗ** thay vì hỏi "cụm chữ có ở đâu đó trong tệp
    100 KB không" — nên một neo không có cửa là một neo chưa làm việc gì.
    """
    import ast as _ast
    import re as _re

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    neo = sorted(set(_re.findall(r"<!-- CHOT:([a-z0-9-]+) -->", spec)))
    assert neo, "không còn neo CHOT nào trong đặc tả — chúng đi đâu?"

    # CHỈ ĐỌC CHUỖI THẬT TRONG MÃ, bỏ docstring.
    #
    # `x in y` LẦN THỨ MƯỜI BA, và lần này trong CHÍNH bài viết ra để chữa loại
    # bệnh ấy. Bản đầu nối cả tệp lại rồi tìm — nên docstring ngay trên kia,
    # chỗ liệt kê ba neo tôi từng quên, đã tự làm cho chúng "có cửa". Cửa canh
    # thấy tên neo trong một đoạn KỂ CHUYỆN và tưởng đó là một chỗ dùng.
    manh: list[str] = []
    for tep in (PROJECT_ROOT / "tests").glob("test_*.py"):
        cay = _ast.parse(tep.read_text(encoding="utf-8"))
        la_docstring = set()
        for nut in _ast.walk(cay):
            than = getattr(nut, "body", None)
            if isinstance(nut, (_ast.Module, _ast.ClassDef, _ast.FunctionDef,
                                _ast.AsyncFunctionDef)) and than:
                d = than[0]
                if (isinstance(d, _ast.Expr)
                        and isinstance(d.value, _ast.Constant)
                        and isinstance(d.value.value, str)):
                    la_docstring.add(id(d.value))
        manh += [n.value for n in _ast.walk(cay)
                 if isinstance(n, _ast.Constant) and isinstance(n.value, str)
                 and id(n) not in la_docstring]
    nguon = "\n".join(manh)
    # Nhắc tới neo bằng HAI cách, và cả hai đều tính:
    #   `re.search(r"<!-- CHOT:khe-dua -->…")`  — dán thẳng tên vào biểu thức
    #   `_khoi_chot("no-network")`              — truyền tên làm đối số
    # Bản đầu của bài này chỉ tìm `CHOT:<tên>`, nên nó báo `khe-dua` và
    # `no-network` là mù trong khi cả hai ĐANG có cửa. Suýt đi "sửa" hai thứ
    # không hỏng — một cửa canh quá chặt cũng là một cửa sai.
    # `manh` là GIÁ TRỊ các chuỗi, không phải mã nguồn — nên tìm tên trần,
    # đừng tìm tên kèm dấu nháy. (Bản trước tìm `'"no-network"'` trong một danh
    # sách chỉ chứa `no-network`, và báo mù cho hai neo đang có cửa.)
    dung_truc_tiep = set(manh)
    thieu = [n for n in neo
             if n not in dung_truc_tiep and f"CHOT:{n}" not in nguon]
    assert not thieu, (
        f"{len(thieu)}/{len(neo)} neo KHÔNG có cửa nào đọc: {thieu}. "
        f"Viết một bài đọc khối giữa hai neo và đòi các con số ở lại — hoặc "
        f"bỏ neo đi nếu nó không canh gì.")


def test_MOI_NEO_CHOT_deu_DONG_lai_dung_cach():
    """Neo mở mà không có neo đóng thì `re.search` nuốt tới cuối tệp.

    Ca đối chứng của bài trên: một cửa vẫn "đọc được khối" khi khối ấy thật ra
    là toàn bộ phần còn lại của đặc tả — và khi ấy nó bắt trúng mọi cụm chữ,
    tức trở lại đúng bệnh `x in y` mà neo sinh ra để chữa.
    """
    import re as _re

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    mo = _re.findall(r"<!-- CHOT:([a-z0-9-]+) -->", spec)
    dong = _re.findall(r"<!-- /CHOT:([a-z0-9-]+) -->", spec)
    assert sorted(mo) == sorted(dong), (
        f"neo mở và neo đóng không khớp:\n  chỉ có neo MỞ : "
        f"{sorted(set(mo) - set(dong))}\n  chỉ có neo ĐÓNG: "
        f"{sorted(set(dong) - set(mo))}")
    assert len(mo) == len(set(mo)), f"neo trùng tên: {mo}"
