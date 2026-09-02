# -*- coding: utf-8 -*-
"""Không phòng nào được TỰ KHAI trạng thái. Trạng thái phải đến từ phép đo.

VÌ SAO CÓ TỆP NÀY. 02/09/2026, `interface/noi_bo_api.py` khai bảy phòng nội bộ,
mỗi phòng bốn công cụ, sáu phòng `trang_thai: "ONLINE"` — **toàn bộ là chuỗi gõ
tay**. Không một dòng mã nào tính ra chữ ấy. Cùng lúc `chat.html` khai ngược
lại: Delta và Omega ở đó là `san: false`. Hai sổ, hai câu trả lời khác nhau về
cùng một phòng.

Đo lại bằng cách đi từ cửa vào — gọi đúng `POST /api/dispatch` như giao diện
gọi — rồi hỏi một câu: **sau lượt ấy trên đĩa có gì mới không?**

    chạy thật 0 · chưa chạy thật 7 · không đo được 0
    8 tệp được KHAI là đã tạo · 0 tệp có thật trên đĩa
    mỗi lượt 2–9 ms

Cả bảy trả về đoạn văn viết sẵn. Vài ví dụ nguyên văn:

* `gamma` — phòng ĐO LƯỜNG — in *"Số liệu đo đạc thời gian thực"* rồi báo
  ``RAM 4.2 GB / 16.0 GB`` trên một máy có **11,7 GB**, và ``100% (714/714
  tests)``. Cả ba con số đều gõ tay.
* `alpha` khai hai tệp `storyboard.json` (3.4 KB) và `cards_preview.png`
  (240 KB) — không tệp nào tồn tại.
* `zeta` gọi `loc_menh_lenh()` thật rồi **vứt kết quả**, trả về một "báo cáo"
  nói đã đối chiếu Wikipedia, Dân Trí, VNExpress.

Và bộ điều phối ghi ``"status": "PASS"`` vào sổ cái cho **mọi** lượt, kể cả
lượt không làm gì.

Đây đúng hình dạng đã giết AURA v2 (`CLAUDE.md` mục 1: *339 tệp, 33 cờ mà 29
cái đang TẮT*), và cùng họ với lỗi 24/08 ở App Thẻ: *panel Agent trả lời bằng
chuỗi cứng + `setTimeout` 350ms giả vờ suy nghĩ, 0 request*.

CA ĐỐI CHỨNG chứng minh máy đo không mù: gieo một lượt ghi tệp thật vào nhánh
`beta` thì nó lật `CHUA_CHAY_THAT` -> `CHAY_THAT` và gọi đúng tên tệp; trả mã
về thì lật lại, sáu phòng kia không đổi.

CỬA NÀY KHÔNG BẮT CÁC PHÒNG PHẢI CHẠY THẬT. Nó chỉ cấm chúng **tự khai**. Sửa
cho phòng chạy thật là việc khác, dài hơn; nhưng chừng nào chưa sửa thì màn
hình phải nói đúng là chưa.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT

NGUON = Path(PROJECT_ROOT, "interface", "noi_bo_api.py").read_text(encoding="utf-8")

# Chuỗi tự khai bị cấm nằm trong danh mục. `CHUA_DO` và ba trạng thái đo được
# thì hợp lệ, vì chúng đến từ sổ đo chứ không phải từ danh mục.
TU_KHAI = ("ONLINE", "STANDBY", "OFFLINE")


def _danh_muc() -> list[dict]:
    for n in ast.walk(ast.parse(NGUON)):
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DANH_MUC_PHONG":
            return ast.literal_eval(n.value)
    pytest.fail("không tìm thấy DANH_MUC_PHONG")


def test_danh_muc_khong_con_truong_trang_thai():
    """Có trường là có chỗ để gõ tay. Bỏ hẳn trường đi thì không gõ vào đâu được."""
    xau = [p["id"] for p in _danh_muc() if "trang_thai" in p]
    assert not xau, (
        f"{xau} còn tự khai `trang_thai` trong danh mục. Trạng thái phải đến từ "
        "`tools/do_trang_thai_phong.py`, không phải từ bàn phím."
    )


@pytest.mark.parametrize("chuoi", TU_KHAI)
def test_khong_con_chuoi_tu_khai_trong_danh_muc(chuoi):
    """Soi trên CHÍNH danh mục đã phân giải, không dò chuỗi trên cả tệp.

    Dò cả tệp thì bắt nhầm câu giải thích trong chú thích — đúng bệnh `x in y`
    ở `CLAUDE.md` mục 4, đã cắn một lần sáng nay ở cửa gỡ-cài-đặt.
    """
    dinh = [f"{p['id']}.{k}" for p in _danh_muc() for k, v in p.items()
            if isinstance(v, str) and chuoi in v]
    assert not dinh, f"{dinh} còn mang chuỗi tự khai {chuoi!r}"


def test_api_doc_trang_thai_tu_so_do():
    from interface.noi_bo_api import SO_TRANG_THAI, doc_trang_thai_da_do
    assert SO_TRANG_THAI.name.endswith(".json")
    d = doc_trang_thai_da_do()
    assert isinstance(d, dict)
    for v in d.values():
        assert v in ("CHAY_THAT", "CHUA_CHAY_THAT", "KHONG_DO_DUOC"), v


def test_so_do_hong_thi_tra_ve_rong_chu_khong_no(tmp_path, monkeypatch):
    """Sổ hỏng phải thành `CHUA_DO`, không được làm sập trang danh sách phòng."""
    from interface import noi_bo_api

    for noi_dung in ("", "{khong phai json", '{"phong": "sai kieu"}', '{}'):
        gia = tmp_path / "so.json"
        gia.write_text(noi_dung, encoding="utf-8")
        monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI", gia)
        assert noi_bo_api.doc_trang_thai_da_do() == {}, noi_dung[:20]

    monkeypatch.setattr(noi_bo_api, "SO_TRANG_THAI", tmp_path / "khong-co.json")
    assert noi_bo_api.doc_trang_thai_da_do() == {}


def test_ba_trang_thai_TACH_ROI_trong_may_do():
    """đạt · đo được mà không đạt · KHÔNG ĐO ĐƯỢC — gộp hai là mất một.

    Bản đầu của phép này chỉ soi xem ba chuỗi CÓ MẶT trong mã máy đo. Gieo thử
    chứng minh nó MÙ: đổi nhánh HTTP-lỗi từ `KHONG_DO_DUOC` sang
    `CHUA_CHAY_THAT` thì chuỗi vẫn còn ở chỗ khác, cửa vẫn xanh. Bệnh `x in y`,
    lần thứ ba trong ngày, lần này nằm ngay trong cửa canh.

    Nay bắt máy đo CHẠY và xem nó TRẢ VỀ gì.
    """
    import tools.do_trang_thai_phong as md

    class _KhongNoi:
        def post(self, *a, **k):
            raise OSError("khong noi duoc")

    class _Loi500:
        def post(self, *a, **k):
            class R:
                status_code = 500
            return R()

    class _RongTuech:
        def post(self, *a, **k):
            class R:
                status_code = 200

                @staticmethod
                def json():
                    return {"artifacts": []}
            return R()

    a = md.do_mot_phong(_KhongNoi(), "http://x", "gamma")
    b = md.do_mot_phong(_Loi500(), "http://x", "gamma")
    c = md.do_mot_phong(_RongTuech(), "http://x", "gamma")
    assert a["trang_thai"] == "KHONG_DO_DUOC", a
    assert b["trang_thai"] == "KHONG_DO_DUOC", (
        f"HTTP 500 phải là KHÔNG ĐO ĐƯỢC, đang là {b['trang_thai']!r}. Gộp nó "
        "vào 'chưa chạy thật' là để 'chưa đo được' đội lốt 'đã đo, hỏng'."
    )
    assert c["trang_thai"] == "CHUA_CHAY_THAT", c
    assert len({a["trang_thai"], b["trang_thai"], c["trang_thai"]}) >= 2


def test_so_cai_khong_duoc_tinh_la_bang_chung_cua_phong():
    """Bộ điều phối ghi `so_cai.jsonl` cho MỌI phòng, kể cả phòng không làm gì.

    Tính nó vào thì cả bảy phòng đều "đạt" — phép đo mất hết ý nghĩa. Máy đo
    phải trừ nó ra.
    """
    nguon = Path(PROJECT_ROOT, "tools", "do_trang_thai_phong.py").read_text(encoding="utf-8")
    assert "SO_CAI" in nguon and "if p == SO_CAI:" in nguon, (
        "máy đo không còn trừ sổ cái ra khỏi bằng chứng"
    )


def test_so_do_hien_tai_khop_dinh_dang():
    """Sổ đo đang nằm trên đĩa phải đọc được và đủ bảy phòng."""
    so = Path(PROJECT_ROOT, "data", "noi_bo", "trang_thai_phong.json")
    if not so.is_file():
        pytest.skip("chưa chạy tools/do_trang_thai_phong.py trên máy này")
    d = json.loads(so.read_text(encoding="utf-8"))
    assert {p["id"] for p in _danh_muc()} == {p["phong_id"] for p in d["phong"]}
    for p in d["phong"]:
        assert p["trang_thai"] in ("CHAY_THAT", "CHUA_CHAY_THAT", "KHONG_DO_DUOC")


def test_API_lay_trang_thai_tu_so_do_chu_khong_tu_danh_muc(monkeypatch):
    """Đo HÀNH VI của đường `/api/rooms`, không đọc mã rồi suy.

    Gieo thử bắt được bản đầu: bỏ hẳn bước tra sổ đo, trả thẳng `DANH_MUC_PHONG`
    ra ngoài, mà cửa vẫn xanh — vì không phép nào GỌI hàm ấy.
    """
    import asyncio
    import json as _json

    from interface import noi_bo_api

    monkeypatch.setattr(noi_bo_api, "doc_trang_thai_da_do",
                        lambda: {"gamma": "CHAY_THAT"})
    r = asyncio.run(noi_bo_api.api_danh_sach_phong(None))
    d = _json.loads(r.body.decode("utf-8"))
    theo_id = {p["id"]: p["trang_thai"] for p in d["rooms"]}

    assert theo_id["gamma"] == "CHAY_THAT", (
        f"trạng thái của gamma phải lấy từ sổ đo, đang là {theo_id['gamma']!r}"
    )
    con_lai = {k: v for k, v in theo_id.items() if k != "gamma"}
    assert set(con_lai.values()) == {"CHUA_DO"}, (
        f"phòng chưa có trong sổ phải là CHUA_DO, đang là {sorted(set(con_lai.values()))}"
    )
    assert len(theo_id) == len(_danh_muc())
