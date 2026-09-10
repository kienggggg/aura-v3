# -*- coding: utf-8 -*-
"""Câu hỏi về dữ liệu RIÊNG của Sếp không ra máy chủ tìm kiếm.

Đo trên app thật 10/09/2026, phiên 18 lượt, ba dữ kiện gắn ở lượt 1-3 rồi đẩy
ra ngoài cửa sổ 24 tin:

    "biển số xe tôi là gì"       web_unavailable · 52,7 giây · dữ kiện bị vứt
    "mã đơn hàng của tôi là gì"  đúng, NHƯNG kèm "[1]"
                                 2/3

Trả lời được hay không phụ thuộc một phép tra mạng KHÔNG LIÊN QUAN có trúng
nguồn nào không. Và cái `[1]` trỏ vào một trang web **không hề chứa** con số
ấy — nguồn không đỡ được điều nó đang đỡ.

Sau vá: **3/3** đúng nguyên văn, `status=ok`, **0 nguồn**, `used_web=False`,
không còn `[1]`.

BA ĐIỀU KIỆN. Cách nói *"mỗi ca được cứu bởi đúng một điều kiện"* là SAI
HÌNH — một câu bị nhiều điều kiện cùng chặn. Cái đo được là chiều ngược: bỏ
một điều kiện thì có ca đối chứng nào LỌT không. Ngưỡng chép TAY từ khối
`CHOT:cau-hoi-rieng-khong-ra-mang`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.nho_lai import hoi_ve_minh, so_phien_co_dap_an  # noqa: E402
from core.paths import PROJECT_ROOT  # noqa: E402
from core.web_search import is_search_request  # noqa: E402

DAC_TA_RIENG = 3
DAC_TA_DOI_CHUNG = 7
DAC_TA_SO_DIEU_KIEN = 3


class _Tin:
    def __init__(self, role: str, content: str) -> None:
        self.role, self.content = role, content


# Lượt "theo dõi giá vàng SJC" là BẪY cố ý: nó làm `so_phien_co_dap_an` trả
# `True` cho câu hỏi về giá vàng.
SO_PHIEN = [
    _Tin("user", "Xe của tôi biển số 29AB-123.45, nhớ giúp tôi nhé"),
    _Tin("assistant", "Đã ghi nhớ"),
    _Tin("user", "Mã đơn hàng của tôi là DH-2026-XK7734"),
    _Tin("assistant", "Đã lưu"),
    _Tin("user", "Con gái tôi tên là Phạm Nhã Uyên, sinh năm 2019"),
    _Tin("assistant", "Đã ghi nhớ"),
    _Tin("user", "tôi đang theo dõi giá vàng SJC dạo này"),
    _Tin("assistant", "Vâng"),
]

RIENG = (
    "biển số xe tôi là gì",
    "mã đơn hàng của tôi là gì",
    "con gái tôi tên là gì",
)

# Bảy câu PHẢI vẫn ra mạng. Một câu có thể được nhiều điều kiện cùng chặn —
# nhãn "điều kiện nào cứu nó" là SAI HÌNH, và bản đầu của bài này khai như thế
# rồi tự đỏ. Cái đo được là chiều ngược: BỎ một điều kiện thì có ca nào lọt
# không.
DOI_CHUNG = (
    "giá vàng SJC hôm nay là gì",
    "thủ đô nước Pháp là gì",
    "mức độ lạm phát năm ngoái là gì",
    "số căn cước của tôi là gì",
    "mã số thuế của tôi là gì",
    # BẪY 1: thoả CẢ `minh` lẫn `sổ`, chỉ `lex` chặn được.
    "giá vàng SJC tôi đang theo dõi hôm nay là gì",
    # BẪY 2, THÊM SAU KHI CỬA CANH BẮT ĐƯỢC BỘ NÀY THIẾU:
    # `lex=False`, không nhắc Sếp, nhưng trùng 2 từ với lượt cũ
    # "tôi đang theo dõi giá vàng SJC" -> `sổ` nói CÓ. Không có điều kiện
    # `minh` thì câu này bị chặn nhầm, mà nó là dữ kiện ngoài đời cần nguồn.
    #
    # Sáu ca đầu KHÔNG ca nào chứng minh được `minh` là cần thiết: hai điều
    # kiện kia đã chặn hết. Đúng bài học cùng ngày — ca đối chứng chỉ đối
    # chứng được thứ nó PHÂN BIỆT NỔI, và phải kiểm chứ không suy ra.
    "vàng SJC là gì",
)


def _chan(cau: str) -> bool:
    """Ba điều kiện, chép tay từ `chat_service.reply`."""
    return (not is_search_request(cau)
            and hoi_ve_minh(cau)
            and so_phien_co_dap_an(cau, SO_PHIEN))


def test_DEM_du_hai_bo():
    assert len(RIENG) == DAC_TA_RIENG
    assert len(DOI_CHUNG) == DAC_TA_DOI_CHUNG


@pytest.mark.parametrize("cau", RIENG)
def test_cau_hoi_RIENG_khong_ra_mang(cau: str):
    """Sổ phiên trả lời được thì đừng đẩy chuyện riêng của Sếp ra ngoài."""
    assert _chan(cau), f"vẫn bị đẩy ra máy chủ tìm kiếm: {cau!r}"


@pytest.mark.parametrize("cau", DOI_CHUNG)
def test_DOI_CHUNG_van_ra_mang(cau: str):
    """Bảy câu này PHẢI vẫn ra mạng. Đây là nhóm quan trọng nhất."""
    assert not _chan(cau), f"chặn nhầm, câu này cần nguồn: {cau!r}"


def test_MOI_dieu_kien_deu_CAN_THIET():
    """Bỏ một điều kiện thì phải có ca đối chứng LỌT — nếu không nó thừa.

    Ba điều kiện mà chỉ hai cái làm việc thì cái thứ ba là trang trí, và trang
    trí thì sẽ bị ai đó dọn đi.

    BẢN ĐẦU CỦA BÀI NÀY KHAI SAI HÌNH: nó gán cho mỗi ca *"điều kiện duy nhất
    cứu nó"*, trong khi một câu có thể bị nhiều điều kiện cùng chặn. Chạy thì
    đỏ 3 bài, và cái đỏ ấy lộ ra **bộ đối chứng thiếu**: không ca nào trong sáu
    ca đầu chứng minh được `minh` là cần thiết. Thêm *"vàng SJC là gì"* thì mới
    đủ ba.
    """
    thieu = {
        "lex": lambda c: hoi_ve_minh(c) and so_phien_co_dap_an(c, SO_PHIEN),
        "minh": lambda c: (not is_search_request(c)
                           and so_phien_co_dap_an(c, SO_PHIEN)),
        "so": lambda c: not is_search_request(c) and hoi_ve_minh(c),
    }
    for ten, chan_khi_thieu in thieu.items():
        lot = [c for c in DOI_CHUNG if chan_khi_thieu(c)]
        assert lot, (
            f"bỏ điều kiện {ten!r} mà KHÔNG ca đối chứng nào lọt — "
            "hoặc điều kiện ấy thừa, hoặc bộ đối chứng còn thiếu ca")


def test_BA_dieu_kien_DEU_co_mat_trong_ma():
    """Hỏi CẤU TRÚC: cả ba phải nằm trong CÙNG một câu `if` ở `chat_service`.

    Dò chữ thì trúng chính đoạn chú thích kể lại ba điều kiện — `x in y` đã
    cắn ba lần trong ngày hôm nay.
    """
    import ast as _ast

    cay = _ast.parse((PROJECT_ROOT / "core" / "chat_service.py")
                     .read_text(encoding="utf-8"))
    thay = False
    for nut in _ast.walk(cay):
        if not isinstance(nut, _ast.If):
            continue
        goi = {n.func.id for n in _ast.walk(nut.test)
               if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)}
        if {"is_search_request", "hoi_ve_minh", "so_phien_co_dap_an"} <= goi:
            thay = True
            break
    assert thay, (
        "không còn câu `if` nào gọi đủ CẢ BA điều kiện — "
        "bỏ một cái là chặn nhầm hoặc bỏ sót")


def test_NGUONG_khop_khoi_dac_ta():
    khoi = re.search(
        r"<!-- CHOT:cau-hoi-rieng-khong-ra-mang -->(.*?)"
        r"<!-- /CHOT:cau-hoi-rieng-khong-ra-mang -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:cau-hoi-rieng-khong-ra-mang"
    van = khoi.group(1)
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", van, re.M))
    r = hang.get("riêng + sổ trả lời được, KHÔNG ra mạng", "")
    assert f"{DAC_TA_RIENG}/3" in r and "nền 0/3" in r, f"hàng ngưỡng: {r!r}"
    dc = hang.get("đối chứng vẫn ra mạng", "")
    assert f"{DAC_TA_DOI_CHUNG}/7" in dc, f"hàng đối chứng: {dc!r}"
    sdk = hang.get("số điều kiện", "")
    assert f"**{DAC_TA_SO_DIEU_KIEN}**" in sdk, f"hàng số điều kiện: {sdk!r}"
    # Bằng chứng phải ở lại: cắt nó đi thì ba điều kiện thành sở thích.
    phang = re.sub(r"\s+", " ", van)
    assert "52,7 giây" in phang, "cắt mất số đo lượt chết ở web_unavailable"
    assert "DH-2026-XK7734 [1]" in phang, "cắt mất bằng chứng trích dẫn sai"
