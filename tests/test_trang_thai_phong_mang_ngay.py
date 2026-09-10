# -*- coding: utf-8 -*-
"""Trạng thái phòng phải mang NGÀY ra tới cửa, và số phòng phải SUY RA.

Bắt được 10/09/2026 bằng cách chạy app nội bộ thật.

    tệp trạng thái đo lúc                2026-09-03T20:26:18
    commit đụng vào mã phòng kể từ đó    34
    API trả ra ngày ấy                   KHÔNG — chỉ trả đường dẫn tệp

Người đọc thấy `CHAY_THAT` và hiểu là thì hiện tại. Đúng ca ghi sáng cùng
ngày — *"nhãn đã đo không mang ngày thì đọc thành thì hiện tại"* — lần ấy là
kho công nghệ ngoài repo, lần này là chính sản phẩm.

VÀ HAI CỬA CẠNH NHAU KHÔNG KHỚP. `/api/rooms` phủ trạng thái đo được;
`/api/status` cách đó mười dòng trả `DANH_MUC_PHONG` THÔ kèm `"rooms_online":
7` — một hằng số gõ thẳng, không tính ra từ đâu. Giao diện không đọc trường ấy
lần nào, nên không ai phát hiện nó sai.

Ngưỡng chép TAY từ khối `CHOT:trang-thai-phong-mang-ngay`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

DAC_TA_SO_PHONG = 7
DAC_TA_TRUONG_BAT_BUOC = (
    "trang_thai_do_luc", "trang_thai_so_ngay_truoc", "so_phong_chay_that")


def _khoi():
    from interface import noi_bo_api

    return noi_bo_api._khoi_trang_thai_phong()


def test_khoi_chung_mang_DU_ba_truong():
    """Ngày, tuổi, và số phòng — thiếu một cái là mất một nửa nghĩa."""
    k = _khoi()
    for ten in DAC_TA_TRUONG_BAT_BUOC:
        assert ten in k, f"khối trạng thái thiếu {ten!r}"
    assert len(k["rooms"]) == DAC_TA_SO_PHONG


def test_SO_PHONG_CHAY_THAT_suy_ra_chu_khong_go_tay(monkeypatch, tmp_path):
    """Gieo một sổ đo CHỈ có 3 phòng chạy thật -> phải ra 3, không phải 7.

    Đây là ca đối chứng cho hằng số `"rooms_online": 7` đã bỏ: nó đứng yên ở 7
    bất kể sổ đo nói gì, kể cả khi không có sổ nào.
    """
    from interface import noi_bo_api

    so = tmp_path / "trang_thai_phong.json"
    so.write_text(json.dumps({
        "do_luc": "2026-01-02T03:04:05",
        "phong": [{"phong_id": "aura", "trang_thai": "CHAY_THAT"},
                  {"phong_id": "alpha", "trang_thai": "CHAY_THAT"},
                  {"phong_id": "beta", "trang_thai": "CHUA_CHAY_THAT"},
                  {"phong_id": "delta", "trang_thai": "CHAY_THAT"}]},
        ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI", so)

    k = noi_bo_api._khoi_trang_thai_phong()
    assert k["so_phong_chay_that"] == 3, k["so_phong_chay_that"]
    assert k["trang_thai_do_luc"] == "2026-01-02T03:04:05"
    tt = {p["id"]: p["trang_thai"] for p in k["rooms"]}
    assert tt["beta"] == "CHUA_CHAY_THAT"
    assert tt["gamma"] == "CHUA_DO", "phòng thiếu trong sổ phải là CHUA_DO"
    assert tt["omega"] == "CHUA_DO"
    assert tt["zeta"] == "CHUA_DO"


def test_KHONG_CO_SO_DO_thi_fail_closed(monkeypatch, tmp_path):
    """Không có sổ đo -> mọi phòng `CHUA_DO`, số phòng chạy thật **0**.

    Không phải bảy phòng "online" vì con số 7 nằm sẵn trong mã. *"Lỗi là FAIL
    hoặc BLOCKED. Cấm nuốt lỗi."*
    """
    from interface import noi_bo_api

    monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI",
                        tmp_path / "khong-co-that.json")
    k = noi_bo_api._khoi_trang_thai_phong()
    assert k["so_phong_chay_that"] == 0
    assert k["trang_thai_do_luc"] is None
    assert k["trang_thai_so_ngay_truoc"] is None
    assert k["nguon_trang_thai"] == "CHUA_DO"
    assert all(p["trang_thai"] == "CHUA_DO" for p in k["rooms"])


def test_TUOI_phep_do_tinh_dung(monkeypatch, tmp_path):
    """Tuổi phải là số ngày thật, không phải một chuỗi trang trí."""
    from datetime import datetime, timedelta

    from interface import noi_bo_api

    truoc = (datetime.now() - timedelta(days=9, hours=1)).isoformat()
    so = tmp_path / "s.json"
    so.write_text(json.dumps({"do_luc": truoc, "phong": []}), encoding="utf-8")
    monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI", so)
    assert noi_bo_api._khoi_trang_thai_phong()["trang_thai_so_ngay_truoc"] == 9


def test_NGAY_HONG_khong_lam_no_va_khong_noi_doi(monkeypatch, tmp_path):
    """Sổ có `do_luc` rác -> tuổi `None`, không nổ, không bịa ra một con số."""
    from interface import noi_bo_api

    so = tmp_path / "s.json"
    so.write_text(json.dumps({"do_luc": "hôm kia", "phong": []}), encoding="utf-8")
    monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI", so)
    k = noi_bo_api._khoi_trang_thai_phong()
    assert k["trang_thai_so_ngay_truoc"] is None
    assert k["trang_thai_do_luc"] == "hôm kia"


def test_HAI_CUA_dung_CHUNG_mot_nguon():
    """Hai lời khai cạnh nhau sẽ trôi khỏi nhau — đã trôi một lần rồi.

    HỎI CẤU TRÚC MÃ, KHÔNG DÒ CHỮ. `x in y` LẦN THỨ MƯỜI BẢY, hai lượt liên
    tiếp trong cùng một bài:

        lượt 1   dò cả tệp  -> bắt phải CHÚ THÍCH giải thích hằng số vừa bỏ
        lượt 2   bỏ COMMENT -> bắt phải DOCSTRING kể lại đúng chuyện ấy

    Docstring là STRING chứ không phải COMMENT, nên `tokenize` không lọc nó.
    Cứ vá từng lớp thì còn lớp thứ ba. Chữa cả LOẠI: hỏi `ast` xem trong mã có
    một `dict` nào mang khoá ấy không — chữ trong văn xuôi không dựng nổi một
    nút `ast.Dict`.
    """
    import ast as _ast

    tep = PROJECT_ROOT / "interface" / "noi_bo_api.py"
    cay = _ast.parse(tep.read_text(encoding="utf-8"))

    assert tep.read_text(encoding="utf-8").count("_khoi_trang_thai_phong()") >= 2, (
        "một trong hai cửa không còn dùng khối chung")

    go_tay = [n for n in _ast.walk(cay) if isinstance(n, _ast.Dict)
              and any(isinstance(k, _ast.Constant) and k.value == "rooms_online"
                      for k in n.keys if k is not None)]
    assert not go_tay, (
        'hằng số "rooms_online" gõ thẳng đã quay lại trong MÃ '
        f"(dòng {[n.lineno for n in go_tay]})")

    # Và `rooms` không được trỏ thẳng vào danh mục THÔ ở bất kỳ dict nào —
    # danh mục thô là danh mục KHÔNG mang trạng thái đo được.
    tho = []
    for n in _ast.walk(cay):
        if not isinstance(n, _ast.Dict):
            continue
        for k, val in zip(n.keys, n.values):
            if (isinstance(k, _ast.Constant) and k.value == "rooms"
                    and isinstance(val, _ast.Name)
                    and val.id == "DANH_MUC_PHONG"):
                tho.append(n.lineno)
    assert not tho, (
        f"một cửa trả DANH_MUC_PHONG THÔ, không phủ trạng thái đo (dòng {tho})")


def test_NGUONG_khop_khoi_dac_ta():
    """Ngưỡng phải có chỗ đứng ngoài mã."""
    khoi = re.search(
        r"<!-- CHOT:trang-thai-phong-mang-ngay -->(.*?)"
        r"<!-- /CHOT:trang-thai-phong-mang-ngay -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:trang-thai-phong-mang-ngay"
    van = khoi.group(1)
    phang = re.sub(r"\s+", " ", van)
    # Cái NỀN phải ở lại: "đã sửa" mà không có số cũ thì không đọc được nó
    # hơn cái gì.
    assert "2026-09-03T20:26:18" in phang, "cắt mất ngày của phép đo cũ"
    assert "34" in phang, "cắt mất số commit đã đụng vào mã phòng"
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", van, re.M))
    assert "SUY RA" in hang.get("`rooms_online`", ""), hang
