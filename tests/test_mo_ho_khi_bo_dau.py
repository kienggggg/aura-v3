# -*- coding: utf-8 -*-
r"""Bỏ dấu gộp `đô` · `độ` · `đo` thành `do`, mà `do` là từ TRỎ NGỮ CẢNH.

`_TRO_VE_NGU_CANH` khớp trên bản BỎ DẤU, nên `do` bắt luôn `đô` (thủ đô), `độ`
(chế độ, nhiệt độ, mức độ), `đo` (đo lường); `duoi` bắt luôn `đuôi`. Câu chứa
chúng không trỏ vào ngữ cảnh nào cả, nhưng vẫn được miễn khỏi đường bắt buộc
có nguồn.

ĐO NỀN 10/09/2026: **15/15** câu cần nguồn LỌT, 6/6 ca đối chứng đúng.

TÁC HẠI ĐO TRÊN APP THẬT, không phải suy luận:

    hỏi  "mức độ lạm phát Việt Nam năm ngoái là gì"
    đáp  status=ok · nguồn=0
         "Theo số liệu chính thức từ Tổng cục Thống kê, mức giá trung bình
          tại Việt Nam tăng khoảng 2,91% trong năm 2024..."

Dẫn tên một cơ quan nhà nước kèm con số cụ thể, **0 nguồn**, và sai cả năm
(từ 2026, *"năm ngoái"* là 2025). Đúng cách bịa của 13/08/2026.

Sau vá, cùng câu ấy: `web_unavailable` — từ chối thật thà. Và *"thủ đô nước
Pháp là gì"* ra `ok` kèm **4 nguồn**.

Ngưỡng chép TAY từ khối `CHOT:mo-ho-khi-bo-dau-loai-cau-hoi`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.loai_cau_hoi import TRA_CUU, loai  # noqa: E402
from core.paths import PROJECT_ROOT  # noqa: E402

DAC_TA_CAN_NGUON = 15
DAC_TA_DOI_CHUNG = 6
# Chép TAY. Ba từ này bỏ dấu thì trùng từ khác hẳn -> chỉ khớp bản CÓ DẤU.
DAC_TA_TU_MO = ("này", "đó", "dưới")

CAN_NGUON = (
    "thủ đô nước Pháp là gì",
    "chế độ ăn keto là gì",
    "nhiệt độ sôi của nước là gì",
    "tốc độ ánh sáng là gì",
    "độ cao của đỉnh Everest là gì",
    "đơn vị đo áp suất là gì",
    "kinh độ và vĩ độ là gì",
    "đô la Mỹ là gì",
    "mức độ lạm phát năm ngoái là gì",
    "chế độ quân chủ lập hiến là gì",
    "đuôi tệp .rs là gì",
    "đô thị loại 1 là gì",
    "độ ẩm trung bình Hà Nội là gì",
    "đơn vị đo nhiệt độ là gì",
    "mức độ ô nhiễm không khí là gì",
)

# Thật sự trỏ vào ngữ cảnh. Vá xong mà nhóm này đổi thì đã phá đúng thứ luật
# ấy sinh ra để giữ — đẩy chuyện riêng của Sếp ra máy chủ tìm kiếm.
DOI_CHUNG = (
    "lỗi này là gì",
    "hàm vừa rồi là gì",
    "cái đó là gì",
    "dòng ở trên là gì",
    "đoạn vừa nói là gì",
    "biến kia là gì",
)


def test_DEM_du_hai_bo():
    """`parametrize` trên bộ thiếu thì xanh vì rỗng."""
    assert len(CAN_NGUON) == DAC_TA_CAN_NGUON
    assert len(DOI_CHUNG) == DAC_TA_DOI_CHUNG


@pytest.mark.parametrize("cau", CAN_NGUON)
def test_cau_can_nguon_KHONG_duoc_mien_vi_bo_dau(cau: str):
    """Chứa `đô`/`độ`/`đo`/`đuôi` không làm câu ấy trỏ vào ngữ cảnh."""
    assert loai(cau) == TRA_CUU, f"lọt khỏi đường bắt buộc có nguồn: {cau!r}"


@pytest.mark.parametrize("cau", DOI_CHUNG)
def test_DOI_CHUNG_van_duoc_mien(cau: str):
    """Câu trỏ ngữ cảnh vẫn phải được miễn — đáp án nằm trong cuộc trò chuyện."""
    assert loai(cau) != TRA_CUU, f"đẩy chuyện riêng ra máy chủ tìm kiếm: {cau!r}"


@pytest.mark.parametrize("tu", DAC_TA_TU_MO)
def test_TU_MO_chi_khop_ban_CO_DAU(tu: str):
    """Không có dấu thì không được nhận — đó là cả bản vá.

    Ca đối chứng gắn liền: cùng một câu, có dấu thì miễn, không dấu thì không.
    Nếu cả hai cùng miễn thì mẫu vẫn đang khớp trên bản bỏ dấu.
    """
    import unicodedata

    from core.loai_cau_hoi import _tro_ve_ngu_canh, _bo_dau

    co_dau = f"cái {tu} là gì"
    khong_dau = "".join(
        c for c in unicodedata.normalize("NFD", co_dau)
        if not unicodedata.combining(c)).replace("đ", "d").replace("Đ", "D")

    assert _tro_ve_ngu_canh(co_dau, _bo_dau(co_dau)), f"mất nhận diện {tu!r}"
    assert not _tro_ve_ngu_canh(khong_dau, _bo_dau(khong_dau)), (
        f"{tu!r} vẫn khớp khi bỏ dấu — đúng khe đã cho `đô`/`độ` lọt qua")


def test_KHONG_con_mau_cu_khop_tren_ban_BO_DAU():
    """Mẫu cũ không được quay lại — hỏi CẤU TRÚC, không dò chữ.

    Bài này đọc `ast`: trong mã không được còn một biến nào tên
    `_TRO_VE_NGU_CANH`. Dò chữ thì trúng chính chú thích kể lại chuyện này —
    `x in y` đã cắn ba lần trong ngày hôm nay.
    """
    import ast as _ast

    cay = _ast.parse((PROJECT_ROOT / "core" / "loai_cau_hoi.py")
                     .read_text(encoding="utf-8"))
    ten = {n.id for n in _ast.walk(cay) if isinstance(n, _ast.Name)}
    ten |= {t.id for n in _ast.walk(cay) if isinstance(n, _ast.Assign)
            for t in n.targets if isinstance(t, _ast.Name)}
    assert "_TRO_VE_NGU_CANH" not in ten, (
        "mẫu cũ khớp trên bản bỏ dấu đã quay lại")


def test_NGUONG_khop_khoi_dac_ta():
    """Ngưỡng phải có chỗ đứng ngoài mã."""
    khoi = re.search(
        r"<!-- CHOT:mo-ho-khi-bo-dau-loai-cau-hoi -->(.*?)"
        r"<!-- /CHOT:mo-ho-khi-bo-dau-loai-cau-hoi -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:mo-ho-khi-bo-dau-loai-cau-hoi"
    van = khoi.group(1)
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", van, re.M))
    can = hang.get("15 câu cần nguồn", "")
    assert "0/15" in can and "nền 15/15" in can, f"hàng ngưỡng: {can!r}"
    mo = hang.get("từ MỜ khi bỏ dấu", "")
    for tu in DAC_TA_TU_MO:
        assert f"`{tu}`" in mo, f"đặc tả thiếu từ mờ {tu!r}: {mo!r}"
    # Bằng chứng tác hại phải ở lại: cắt nó đi thì bản vá thành sở thích.
    phang = re.sub(r"\s+", " ", van)
    assert "Tổng cục Thống kê" in phang, "cắt mất bằng chứng tác hại đo được"
    assert "2,91%" in phang, "cắt mất con số AURA đã bịa"
