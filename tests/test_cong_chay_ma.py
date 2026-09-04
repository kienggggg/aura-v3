# -*- coding: utf-8 -*-
"""`/api/polyglot/run` chạy MÃ TUỲ Ý — bốn lớp cổng vào, đo cả hai chiều.

LỖ ĐO ĐƯỢC TRƯỚC KHI VÁ, ngày 04/09/2026, bằng một `POST` không mang gì cả::

    HTTP 200 · status PASS
    HOME = C:\\Users\\baloa      cwd = D:\\AURA_v3
    ghi được D:\\AURA_v3\\CHUNG_MINH_LO.txt — RA NGOÀI thư mục tạm

MỖI LỚP MỘT CA CHẶN VÀ MỘT CA ĐI QUA. Một cổng chưa từng cho ai đi qua thì
không chứng minh được nó chặn đúng người — nó chỉ chứng minh nó chặn tất cả, và
`return "chặn"` vô điều kiện cũng làm được thế.

Ngưỡng chép tay từ `KY_LUAT_THUC_THI.md` Chương III, không `import` từ mã.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import interface.noi_bo_api as api  # noqa: E402

# ---- NGUỒN SỰ THẬT ĐỘC LẬP ----
DAC_TA_BIEN = "AURA_CHO_CHAY_MA"
DAC_TA_HEADER = "X-Aura-Token"


@pytest.fixture
def cong_mo(monkeypatch):
    """Dựng trạng thái ĐI QUA ĐƯỢC, để mỗi bài chỉ phá đúng một lớp."""
    monkeypatch.setattr(api, "DIA_CHI_BIND", "127.0.0.1")
    monkeypatch.setenv(DAC_TA_BIEN, "1")
    return {DAC_TA_HEADER: api.MA_THONG_HANH}


def test_hang_so_khop_DAC_TA():
    assert api.BIEN_BAT_CHAY_MA == DAC_TA_BIEN
    assert api.HEADER_MA_THONG_HANH == DAC_TA_HEADER


def test_du_bon_lop_thi_DI_QUA(cong_mo):
    """Ca đối chứng của CẢ TỆP. Thiếu bài này thì mọi bài dưới vô nghĩa."""
    assert api.cua_chay_ma(cong_mo) is None


# ---------------------------------------------------- lớp 1: tắt mặc định

def test_khong_co_co_bat_thi_CHAN(cong_mo, monkeypatch):
    monkeypatch.delenv(DAC_TA_BIEN, raising=False)
    ly_do = api.cua_chay_ma(cong_mo)
    assert ly_do and DAC_TA_BIEN in ly_do, ly_do


def test_co_bat_sai_gia_tri_thi_CHAN(cong_mo, monkeypatch):
    """`=1` chứ không phải "có đặt là được" — `0`, `false`, rỗng đều phải chặn."""
    for gia in ("0", "false", "", "true", "yes"):
        monkeypatch.setenv(DAC_TA_BIEN, gia)
        assert api.cua_chay_ma(cong_mo) is not None, f"{gia!r} lọt qua"


# --------------------------------------------------- lớp 2: mã thông hành

def test_thieu_ma_thong_hanh_thi_CHAN(cong_mo):
    assert api.cua_chay_ma({}) is not None


def test_sai_ma_thong_hanh_thi_CHAN(cong_mo):
    assert api.cua_chay_ma({DAC_TA_HEADER: "sai-be-bét"}) is not None


def test_ma_thong_hanh_gan_dung_van_CHAN(cong_mo):
    """Thiếu một ký tự cũng phải chặn — so bằng `compare_digest`, không `startswith`."""
    assert api.cua_chay_ma({DAC_TA_HEADER: api.MA_THONG_HANH[:-1]}) is not None
    assert api.cua_chay_ma({DAC_TA_HEADER: api.MA_THONG_HANH + "x"}) is not None


def test_ma_thong_hanh_du_dai_va_ngau_nhien():
    """32 byte urlsafe ≈ 43 ký tự. Ngắn hơn thì đoán được."""
    assert len(api.MA_THONG_HANH) >= 40, len(api.MA_THONG_HANH)


# ---------------------------------------------------------- lớp 3: Origin

def test_origin_la_trang_web_ngoai_thi_CHAN(cong_mo):
    """Lớp này chặn một trang bất kỳ trong trình duyệt của Sếp gọi sang localhost."""
    for goc in ("https://ke-xau.example.com", "http://192.168.1.50:8000",
                "https://localhost.ke-xau.com"):
        ly_do = api.cua_chay_ma({**cong_mo, "Origin": goc})
        assert ly_do and "Origin" in ly_do, f"{goc} lọt qua: {ly_do}"


def test_origin_cua_chinh_may_thi_DI_QUA(cong_mo):
    for goc in ("http://127.0.0.1:8791", "http://localhost:8791"):
        assert api.cua_chay_ma({**cong_mo, "Origin": goc}) is None, goc


def test_khong_co_Origin_thi_DI_QUA(cong_mo):
    """curl/script không gửi Origin — đã qua mã thông hành rồi thì cho đi."""
    assert api.cua_chay_ma(cong_mo) is None


# -------------------------------------------------------- lớp 4: loopback

def test_bind_ra_LAN_thi_CHAN_du_co_du_moi_thu(cong_mo, monkeypatch):
    """Mở ra LAN và cho chạy mã là hai việc không được xảy ra cùng lúc.

    Lớp này đứng TRƯỚC cờ bật: bật cờ cũng không cứu được.
    """
    for host in ("0.0.0.0", "192.168.1.10", "::"):
        monkeypatch.setattr(api, "DIA_CHI_BIND", host)
        ly_do = api.cua_chay_ma(cong_mo)
        assert ly_do and "loopback" in ly_do, f"{host} lọt qua: {ly_do}"


def test_chua_khai_bind_thi_CHAN(cong_mo, monkeypatch):
    """Quên gọi `dat_dia_chi_bind` thì TẮT, không phải MỞ.

    Fail-closed đặt đúng chiều: lỗi của người viết mã dẫn tới an toàn hơn.
    """
    monkeypatch.setattr(api, "DIA_CHI_BIND", None)
    assert api.cua_chay_ma(cong_mo) is not None


# ------------------------------------------------- nối vào handler thật

async def _goi(headers):
    class _Req:
        def __init__(self, h):
            self.headers = h

        async def json(self):
            return {"ma": "print(1)", "lang": "python"}

    return await api.api_polyglot_run(_Req(headers))


def test_handler_CHAN_that_chu_khong_chi_ham_thuan(monkeypatch):
    """Chấm được `cua_chay_ma` không chứng minh handler NGHE nó.

    Đây là chỗ mù đã mắc BẢY lần trong ngày 03/09. Bài này gọi thẳng handler.
    """
    import asyncio
    import json as _json

    monkeypatch.setattr(api, "DIA_CHI_BIND", "127.0.0.1")
    monkeypatch.delenv(DAC_TA_BIEN, raising=False)
    r = asyncio.run(_goi({}))
    assert r.status == 403, r.status
    d = _json.loads(r.body.decode("utf-8"))
    assert d["status"] == "BLOCKED", d
    assert DAC_TA_BIEN in d["error"], d


def test_handler_CHO_DI_QUA_khi_du_dieu_kien(monkeypatch):
    """Ca đối chứng ở tầng handler: đủ bốn lớp thì mã THẬT SỰ chạy.

    Không có bài này thì bài trên xanh được bằng cách chặn tất cả.
    """
    import asyncio
    import json as _json

    monkeypatch.setattr(api, "DIA_CHI_BIND", "127.0.0.1")
    monkeypatch.setenv(DAC_TA_BIEN, "1")
    r = asyncio.run(_goi({DAC_TA_HEADER: api.MA_THONG_HANH}))
    assert r.status != 403, "đủ điều kiện mà vẫn chặn"
    d = _json.loads(r.body.decode("utf-8"))
    assert d.get("status") != "BLOCKED", d


def test_chu_thich_KHONG_duoc_hua_co_hop_cat():
    """Bốn lớp này canh AI GỌI ĐƯỢC, không canh MÃ LÀM ĐƯỢC GÌ.

    `CLAUDE.md` mục 7 luật 3: *"'Cô lập', 'sandbox', 'không có quyền' — ba chữ ấy
    người đọc sẽ TIN, và tin sai thì mất tệp."* Ngày 19/08 một kế hoạch từng hứa
    "sandbox 256 MB" bằng `resource.setrlimit` — API Unix, `ModuleNotFoundError`
    trên máy này.
    """
    nguon = (Path(__file__).resolve().parent.parent
             / "interface" / "noi_bo_api.py").read_text(encoding="utf-8")
    i = nguon.index("CỔNG VÀO CHẠY MÃ")
    j = nguon.index("Danh mục 7 Đặc Nhiệm", i)
    # CHỈ soi dòng CHÚ THÍCH. Bản đầu soi cả khối và đỗ nhờ một chuỗi trong câu
    # thông báo lúc chạy (`"và đọc phần 'CHƯA CHẶN ĐƯỢC' trước khi bật"`) — gieo
    # lỗi bỏ hẳn đoạn giải thích mà bài vẫn xanh. Cụm ấy xuất hiện HAI lần, và
    # tôi chỉ kiểm "có mặt".
    khoi = "\n".join(d for d in nguon[i:j].splitlines()
                     if d.lstrip().startswith("#"))
    assert "CHƯA CHẶN ĐƯỢC" in khoi, "chú thích phải nói rõ chỗ chưa chặn được"
    assert "Không có hộp cát" in khoi
    assert "resource.setrlimit" in khoi, (
        "phải ghi VÌ SAO không có hộp cát, không chỉ ghi là không có")
    for hua in ("đã cô lập", "sandbox an toàn", "đã chặn hoàn toàn"):
        assert hua not in khoi, f"hứa quá tay: {hua!r}"
