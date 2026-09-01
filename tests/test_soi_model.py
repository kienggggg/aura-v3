# -*- coding: utf-8 -*-
"""Cổng hỏi model local: chỉ local, fail-closed, và không bao giờ nuốt lỗi.

VÌ SAO CÓ TỆP NÀY. `core/soi_model.py` là đường DUY NHẤT App Thẻ nói chuyện với
một model. Ba điều nó phải giữ, và mỗi điều đều có một cách hỏng đã thấy ở repo
này:

  1. CHỈ LOCAL. Không có đường ra cloud, không có chỗ dán khoá API.
     CLAUDE.md mục 2: AURA không được tự gửi ra ngoài.

  2. FAIL-CLOSED KÈM LÝ DO. Mọi ca hỏng phải thành "không dùng được" + một câu
     người đọc hiểu, không ném ngoại lệ lên giao diện và không im lặng trả rỗng.
     Ô chọn model trống mà không nói vì sao thì người dùng tưởng app hỏng.

  3. RỖNG LÀ HỎNG. Model chạy xong mà không nói gì thì phải là `ok=False` —
     đưa chuỗi rỗng lên màn hình trông y hệt như nó đã trả lời.

Hầu hết các test ở đây KHÔNG cần Ollama: chúng bơm một máy chủ giả qua
`monkeypatch` để dựng đúng những ca hỏng khó tạo thật. Ca cần Ollama thật thì
tự bỏ qua khi không có, và NÓI RÕ là bỏ qua — không giả vờ đã đo.
"""
from __future__ import annotations

import httpx
import pytest

from core import soi_model
from core.soi_model import do_ollama, dung_loi_dan, hoi_model


class _PhanHoiGia:
    def __init__(self, ma: int = 200, du_lieu=None, chu: str = ""):
        self.status_code = ma
        self._du_lieu = du_lieu
        self.text = chu

    def json(self):
        if self._du_lieu is None:
            raise ValueError("khong phai JSON")
        return self._du_lieu


# ---------------------------------------------------------------- chỉ local
def test_chi_biet_duong_localhost():
    """Không có host nào khác ngoài loopback trong tệp này."""
    assert soi_model.HOST_MAC_DINH.startswith("http://127.0.0.1")
    nguon = (soi_model.__file__ and open(soi_model.__file__, encoding="utf-8").read()) or ""
    # Bỏ chú thích khỏi phép dò: chú thích đầu tệp có chữ "cloud" khi giải
    # thích rằng KHÔNG có đường cloud — dò thô sẽ tự bắt chính lời giải thích.
    ma = "\n".join(d for d in nguon.splitlines() if not d.lstrip().startswith("#"))
    for cam in ("https://", "api.openai", "anthropic", "api_key", "Authorization"):
        assert cam not in ma, f"`{cam}` xuất hiện — tệp này chỉ được nói với máy local"


# ------------------------------------------------------- fail-closed khi dò
@pytest.mark.parametrize(
    "loi, chu_phai_co",
    [
        (httpx.ConnectError("refused"), "Không thấy Ollama"),
        (httpx.TimeoutException("cham"), "không trả lời"),
        (RuntimeError("gi do la"), "Không dò được"),
    ],
)
def test_do_ollama_hong_thi_noi_ly_do_chu_khong_nem(monkeypatch, loi, chu_phai_co):
    def _nem(*a, **k):
        raise loi

    monkeypatch.setattr(httpx, "get", _nem)
    t = do_ollama()
    assert t.co_ollama is False
    assert chu_phai_co in t.ly_do, f"lý do đọc không ra việc: {t.ly_do!r}"
    assert t.cac_model == []


def test_do_ollama_phan_biet_KHONG_CO_VOI_CHUA_TAI_MODEL(monkeypatch):
    """Hai câu khác nhau dẫn tới hai việc khác nhau.

    Không có Ollama -> đi cài Ollama.
    Có Ollama nhưng chưa tải model -> chỉ cần `ollama pull`.
    Gộp chúng thành một câu là bắt người dùng đoán.
    """
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _PhanHoiGia(200, {"models": []}))
    t = do_ollama()
    assert t.co_ollama is False
    assert "ollama pull" in t.ly_do.lower()
    assert "CHƯA TẢI" in t.ly_do


def test_do_ollama_doc_duoc_danh_sach(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _PhanHoiGia(
        200, {"models": [{"name": "b:1b"}, {"name": "a:2b"}, {"name": ""}]}))
    t = do_ollama()
    assert t.co_ollama is True
    assert t.cac_model == ["a:2b", "b:1b"], "phải sắp xếp, và bỏ tên rỗng"
    assert t.ly_do == ""


def test_do_ollama_http_khac_200_la_hong(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _PhanHoiGia(500, {"models": [{"name": "x"}]}))
    t = do_ollama()
    assert t.co_ollama is False and "500" in t.ly_do


# ------------------------------------------------------ fail-closed khi hỏi
def test_cau_hoi_rong_va_model_rong_bi_chan_truoc_khi_goi_mang(monkeypatch):
    def _khong_duoc_goi(*a, **k):
        raise AssertionError("đã gọi mạng cho một yêu cầu rỗng")

    monkeypatch.setattr(httpx, "post", _khong_duoc_goi)
    ok, tra, ms, ly = hoi_model("", "qwen3:1.7b")
    assert ok is False and "rỗng" in ly.lower()
    ok, tra, ms, ly = hoi_model("có gì", "")
    assert ok is False and "model" in ly.lower()


def test_MODEL_TRA_VE_RONG_LA_HONG(monkeypatch):
    """Đây là chỗ dễ nuốt lỗi nhất trong cả tệp.

    `response: ""` mà báo `ok=True` thì giao diện vẽ một khung trống trơn, đọc
    y hệt như model đã trả lời rồi.
    """
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _PhanHoiGia(200, {"response": "   "}))
    ok, tra, ms, ly = hoi_model("hỏi gì đó", "m:1b")
    assert ok is False, "chuỗi rỗng bị báo là thành công"
    assert tra == ""
    assert "không nói gì" in ly


def test_ollama_bao_loi_thi_dua_NGUYEN_VAN_cho_nguoi_dung(monkeypatch):
    """"model not found" là câu hữu ích — nuốt nó thành "lỗi không rõ" là phí."""
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _PhanHoiGia(
        404, {"error": "model 'khong_co:9b' not found"}))
    ok, tra, ms, ly = hoi_model("hỏi", "khong_co:9b")
    assert ok is False
    assert "404" in ly and "not found" in ly


@pytest.mark.parametrize("loi, chu", [
    (httpx.TimeoutException("cham"), "quá giờ"),
    (httpx.ConnectError("mat"), "Mất kết nối"),
])
def test_hoi_model_hong_thi_noi_ly_do(monkeypatch, loi, chu):
    def _nem(*a, **k):
        raise loi

    monkeypatch.setattr(httpx, "post", _nem)
    ok, tra, ms, ly = hoi_model("hỏi", "m:1b")
    assert ok is False and tra == ""
    if chu == "quá giờ":
        assert "giây" in ly and "6 chữ/giây" in ly, (
            "câu quá giờ phải nói RÕ vì sao chậm — máy không GPU thì 6 chữ/giây, "
            "người dùng cần biết để chọn model nhỏ hơn")
    else:
        assert chu in ly


def test_duong_thanh_cong(monkeypatch):
    ghi = {}

    def _post(url, json=None, timeout=None, **k):
        ghi["url"] = url
        ghi["json"] = json
        return _PhanHoiGia(200, {"response": "  Nó in ra 12.  "})

    monkeypatch.setattr(httpx, "post", _post)
    ok, tra, ms, ly = hoi_model("in ra gì?", "m:1b", "print(12)")
    assert ok is True and tra == "Nó in ra 12." and ly == ""
    assert ghi["url"].startswith("http://127.0.0.1:11434")
    # Hai tham số này là lý do tệp tồn tại được trên máy không GPU:
    #   think=False        339 giây -> 24,8 giây (nhanh 13,7 lần)
    #   keep_alive         nạp lại 29 giây -> 5-9 giây; đo lại 01/09 trên
    #                      qwen3:1.7b: 4,0s nguội -> 1,3s / 1,2s ấm
    assert ghi["json"]["think"] is False, "bật nghĩ thầm là 339 giây một câu"
    assert ghi["json"]["keep_alive"], "không giữ RAM thì mỗi câu nạp lại 3,4 GB"
    assert ghi["json"]["stream"] is False


# ------------------------------------------------------------- lời dẫn
def test_ma_nam_CANH_CAU_HOI_khong_chon_trong_loi_dan_he_thong():
    """CLAUDE.md mục 3, đo được: nhét vào `system_prompt` thì model bỏ qua."""
    p = dung_loi_dan("in ra gì?", "print(12)")
    assert "print(12)" in p
    assert p.index("print(12)") < p.index("in ra gì?"), "mã phải đứng TRƯỚC câu hỏi"
    assert "```python" in p


def test_ma_qua_dai_thi_cat_va_NOI_LA_DA_CAT():
    """Đưa một chương trình cụt cho model mà không nói là đã cắt thì nó bình
    luận về đoạn nó không hề thấy."""
    p = dung_loi_dan("hỏi", "x = 1\n" * 5000)
    assert len(p) < 6000
    assert "đã cắt bớt" in p


def test_khong_co_ma_thi_noi_ro_la_chua_co():
    p = dung_loi_dan("hỏi", "")
    assert "chưa có mã nào" in p


def test_cau_dan_TU_CHOI_phai_con_nguyen():
    """Ca đối chứng 01/09 lật ngược ý định bỏ nó.

        giữ câu dặn   4/4 từ chối đúng khi chương trình không đủ
        bỏ câu dặn    3/4 đúng, 1 ca BỊA ra hàm `doc_tep()` không tồn tại

    Đổi lại 1/6 lần nói "không đủ" nhầm cho câu trả lời được. Một lời từ chối
    nhầm thì người học hỏi lại; một câu bịa thì họ đi sửa mã theo thứ không có.
    """
    p = dung_loi_dan("hỏi", "print(1)")
    assert "không đủ" in p


# ------------------------------------- ca cần Ollama THẬT (tự bỏ qua nếu không có)
def test_duong_that_toi_ollama_neu_may_nay_co():
    t = do_ollama()
    if not t.co_ollama:
        pytest.skip(f"KHÔNG ĐO ĐƯỢC — máy này không có Ollama đang chạy: {t.ly_do}")
    assert t.cac_model, "báo có Ollama mà danh sách model rỗng"
    assert t.ms >= 0
