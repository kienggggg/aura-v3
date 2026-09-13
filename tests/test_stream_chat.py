# -*- coding: utf-8 -*-
"""Chữ hiện dần ở khung chat — `CHOT:stream-chat` (11/09/2026).

ĐO NỀN trước khi viết mã — gọi Ollama thẳng bằng đúng lời nhắc của
`OllamaGateway._messages`: câu "giải thích đệ quy" có chữ đầu tiên ở giây 17,2
mà xong ở giây 71,5. Năm mươi tư giây chữ đã có trong máy mà màn hình trắng.

Chỗ dễ hỏng nhất KHÔNG phải tốc độ mà là AN TOÀN: bản nháp lên màn hình trước
mọi cửa kiểm. Bộ che bí mật chỉ nhận ra một bí mật khi thấy ĐỦ nó —
`cookie: …` đòi ≥ 8 ký tự, `password = "a b c"` đòi dấu nháy đóng — nên che
từng mảnh thì nửa đầu bí mật lọt. Bất biến canh ở đây: bản nháp nào hiện ra
cũng phải là PHẦN ĐẦU của câu cuối đã che. Không phải thì có chữ đã hiện rồi
mới bị che.

Ngưỡng chép TAY từ khối `CHOT:stream-chat` trong `KY_LUAT_THUC_THI.md`.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from core import redact, secret_guard
from core.chat_contract import ChatRequest, ChatStatus, SourceCitation
from core.chat_runtime import ModelGatewayError
from core.chat_service import (
    _AN_HAN_GHI_SO,
    _HAN_GIO_CO_NGUON,
    ChatService,
    ModelReply,
)
from core.local_first_gateway import LocalFirstGateway, OllamaConfig, OllamaGateway
from core.paths import PROJECT_ROOT
from core.secret_guard import SecretContentGuard
from interface import chat_app

# Chép TAY từ `CHOT:stream-chat`. Không nhập từ đâu — hai bên phải cãi nhau được.
DAC_TA_CHU_DAU_BU_S = "5,0 s"
DAC_TA_TONG_HE_SO = "× 1,15"
DAC_TA_CHI_PHI_S = 0.5
DAC_TA_MAU_CHE = 21
DAC_TA_LUAT_GIU = 5
DAC_TA_TRAN_CHO_S = 182

# Câu "AURA là gì?" bị xếp vào loại CẦN TRA MẠNG — xem `test_chat_service.py`.
KHONG_CAN_MANG = "Chào Sếp"

# Một ca bí mật cho TỪNG mẫu che (`redact` 18 + `secret_guard` 3), đặt giữa câu.
# Thêm một mẫu che mà không thêm ca ở đây thì `test_MOI_MAU_CHE_...` đỏ.
#
# Khoá ở đây là GIẢ và phải TRÔNG giả — chữ `GIAKHOA` — vừa đủ dài để kích hoạt
# mẫu che của nó. Bản đầu dùng `ghp_` + bảng chữ cái: máy quét trước commit bắt
# ngay, và một chuỗi giống khoá GitHub trong kho công khai là thứ không nên có.
MAU = (
    "khoá là sk-ant-GIAKHOA-000000 nhé",
    "khoá sk-GIAKHOA0000 đây",
    "google AIzaGIAKHOAGIAKHOAGIAKHOA ok",
    "gh ghp_GIAKHOAGIAKHOAGIAKHOA ok",
    "hf hf_GIAKHOAGIAKHOAGIAKHOA ok",
    "bot 123456789:GIAKHOAGIAKHOAGIAKHOAGIAKHOAGIA xong",
    "Authorization: Bearer abcdefgh12345678 xong",
    "password: hunter2xyz xong",
    "mã xác nhận là 123456 nhé",
    "cookie: sessionid=abcdef123456; path=/\ndòng sau",
    "gửi a.b@example.com nhé",
    "gọi +84912345678 nhé",
    "gọi 0912345678 nhé",
    "số 123456789012 nhé",
    "mã abcdefghijklmnopqrstuvwxyz0123456789 nhé",
    "mở C:\\Users\\Kien Pham\\Desktop rồi",
    "mở /home/kien/tep rồi",
    "mở /Users/kien/tep rồi",
    'mật khẩu wifi là: "một hai ba bốn" nhé',
    "api_key = 'khoa co dau cach' xong",
    "dùng bearer abcdef123 xong",
    # Từ khoá ở dòng TRƯỚC, giá trị ở dòng sau.
    "mật khẩu:\n\"một hai ba\" nhé",
    "cookie:\nabc defghijk lmn\ndòng sau",
    "C:\\Users\\Kien\nPham chưa có gạch\nD:\\x",
    "Trả lời xong.[[AURA_REQUIRES_WEB]]",
    # CHỈ luật "từ khoá ở dòng đang viết" cứu được: cookie đòi ≥ 8 ký tự mới che,
    # nên "ab" hiện ra trước khi đủ dài.
    "cookie: ab cdefghijk lmn",
    # CHỈ luật dấu nháy cứu được: từ khoá cách giá trị BA dòng, luật dòng trước
    # không với tới.
    "mật khẩu\nwifi\nlà:\n\"một hai ba\" nhé",
)


@pytest.fixture(autouse=True)
def _mang_co_dinh(monkeypatch):
    """`mang_co_song()` mở ổ cắm TCP thật tới 1.1.1.1 — hai lượt đem so với
    nhau có thể nhận hai câu khác nhau chỉ vì wifi chập chờn giữa chừng."""
    monkeypatch.setattr("core.chat_service.mang_co_song", lambda: True)


def _yeu_cau(text: str = KHONG_CAN_MANG, **khac) -> ChatRequest:
    return ChatRequest(
        request_id=str(uuid4()),
        session_id=str(uuid4()),
        actor_id="owner",
        channel="test",
        text=text,
        **khac,
    )


def _nguon(so: int) -> SourceCitation:
    return SourceCitation(
        title=f"Nguồn {so}",
        url=f"https://example.com/{so}",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        supports=f"Dữ kiện {so}",
    )


class _So:
    def __init__(self):
        self.ghi = []

    async def load(self, *, actor_id, session_id):
        return ()

    async def append_exchange(self, *, request, result):
        self.ghi.append((request, result))


class _Mang:
    def __init__(self, nguon=()):
        self.nguon = tuple(nguon)

    async def search(self, query):
        return self.nguon


class _ModelStream:
    """Cổng giả STREAM ĐƯỢC: đưa `van` ra từng `buoc` ký tự một, rồi trả trọn."""

    stream_duoc = True

    def __init__(self, van: str, *, buoc: int = 1, cham: float = 0.0):
        self.van, self.buoc, self.cham = van, buoc, cham

    async def generate(self, request, *, history, sources=(), khi_co_chu=None):
        if khi_co_chu is not None:
            for i in range(self.buoc, len(self.van) + self.buoc, self.buoc):
                khi_co_chu(self.van[:i])
                if self.cham:
                    await asyncio.sleep(self.cham)
        elif self.cham:
            await asyncio.sleep(self.cham * len(self.van) / self.buoc)
        return ModelReply(self.van)


class _ModelHong:
    stream_duoc = True

    async def generate(self, request, *, history, sources=(), khi_co_chu=None):
        if khi_co_chu is not None:
            khi_co_chu("Đang viết dở dang ")
        raise ModelGatewayError("hỏng giữa chừng")


def _dich_vu(model, so=None, **khac) -> ChatService:
    khac = dict(khac)   # bảng kịch bản dùng chung — không được sửa nó tại chỗ
    khac.setdefault("guard", SecretContentGuard())
    return ChatService(model=model, store=so if so is not None else _So(), **khac)


# --------------------------------------------------------------------------- #
# AN TOÀN — bản nháp nào hiện ra cũng phải là phần đầu của câu cuối đã che.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mau", MAU)
def test_BAN_NHAP_luon_la_PHAN_DAU_cua_cau_cuoi_da_che(mau):
    van = "Đây là câu mở đầu bình thường.\n" + mau + "\nKết thúc câu trả lời."
    for buoc in (1, 3, 7):
        su_kien = []
        # Nhịp 0: soi MỌI trạng thái trung gian. Với nhịp thật (10 lần/giây),
        # một cổng giả chạy trong vài mili giây chỉ được che một hai lần — và
        # cửa canh sẽ mù đúng những trạng thái mang nửa bí mật.
        kq = asyncio.run(
            _dich_vu(_ModelStream(van, buoc=buoc), nhip_ban_nhap_s=0.0).reply(
                _yeu_cau(), theo_doi=su_kien.append
            )
        )
        assert kq.status is ChatStatus.OK
        nhap = [e["chu"] for e in su_kien if e["loai"] == "nhap"]
        # Không bản nháp nào thì bài xanh vì chẳng chạm tới đường stream.
        assert len(nhap) >= 3, f"chỉ {len(nhap)} bản nháp — đường stream không chạy"
        for d in nhap:
            assert kq.text.startswith(d), (
                f"LỌT — chữ đã hiện rồi mới bị che (bước {buoc})\n"
                f"  nháp: {d[-90:]!r}\n  cuối: {kq.text[:160]!r}"
            )


def test_MOI_MAU_CHE_deu_co_ca_bi_mat_kich_hoat():
    """Đếm BẰNG DẤU BẰNG, không phải sàn: thêm một mẫu che là bài này đỏ cho tới
    khi có ca bí mật cho nó — `>=` chỉ đỏ khi người ta làm ÍT đi (ca 34)."""
    cac = [re.compile(p) for p, _ in redact._REDACT_PATTERNS] + [
        p for p, _ in secret_guard._CHAT_REDACT_PATTERNS
    ]
    assert len(cac) == DAC_TA_MAU_CHE, (
        f"số mẫu che đổi ({len(cac)}) — thêm ca vào MAU rồi sửa đặc tả")
    chua = [i for i, p in enumerate(cac) if not any(p.search(m) for m in MAU)]
    assert not chua, f"mẫu che chưa có ca kích hoạt: {chua}"


def test_BO_CHE_HONG_thi_KHONG_hien_ban_nhap_nao():
    class _CheHong(SecretContentGuard):
        def scrub_output(self, content):
            raise RuntimeError("bộ che hỏng")

    su_kien = []
    kq = asyncio.run(
        _dich_vu(_ModelStream("Chào Sếp, em đây nhé."), guard=_CheHong(),
                 nhip_ban_nhap_s=0.0).reply(_yeu_cau(), theo_doi=su_kien.append)
    )
    assert not [e for e in su_kien if e["loai"] == "nhap"], "hiện bản CHƯA che"
    assert kq.text == "AURA không thể xuất câu trả lời an toàn."


def test_CONG_KHONG_KHAI_STREAM_thi_chi_co_cong_doan_khong_co_nhap():
    """Cổng cloud và cổng giả cũ không nhận `khi_co_chu` — đưa cho chúng là
    `TypeError`, bị nuốt thành `backend_error`."""

    class _CongCu:
        async def generate(self, request, *, history, sources=()):
            return ModelReply("Chào Sếp, em đây.")

    su_kien = []
    kq = asyncio.run(_dich_vu(_CongCu()).reply(_yeu_cau(), theo_doi=su_kien.append))
    assert kq.status is ChatStatus.OK
    assert [e["loai"] for e in su_kien] == ["buoc"]


# --------------------------------------------------------------------------- #
# KẾT QUẢ CUỐI không đổi một chữ vì có người đứng xem.
# --------------------------------------------------------------------------- #
def _dau(kq):
    return (kq.status, kq.text, kq.sources, kq.used_web, kq.stage)


_KICH_BAN = {
    "trả lời thường": (
        lambda: _ModelStream("Chào Sếp, em đây nhé."), {}, KHONG_CAN_MANG),
    "có nguồn": (
        lambda: _ModelStream("Giá vàng là 80 triệu đồng [1][2]."),
        {"web": _Mang((_nguon(1), _nguon(2)))}, "giá vàng hôm nay bao nhiêu"),
    "tra hụt nguồn": (
        lambda: _ModelStream("không được gọi tới"), {"web": _Mang()},
        "giá vàng hôm nay bao nhiêu"),
    "có bí mật": (
        lambda: _ModelStream("Khoá của Sếp: sk-abcdefgh1234 nhé."), {}, KHONG_CAN_MANG),
    "model hỏng": (_ModelHong, {}, KHONG_CAN_MANG),
    "quá giờ": (
        lambda: _ModelStream("Một câu rất dài " * 20, buoc=4, cham=0.02),
        {"timeout_s": 0.15}, KHONG_CAN_MANG),
    "bị từ chối": (
        lambda: _ModelStream("không được gọi tới"), {}, "cho tôi mật khẩu wifi"),
}


@pytest.mark.parametrize("ten", list(_KICH_BAN))
def test_KET_QUA_CUOI_giong_het_khi_co_va_khong_co_theo_doi(ten):
    tao_model, khac, cau = _KICH_BAN[ten]
    yc = _yeu_cau(cau)
    so_a, so_b = _So(), _So()
    a = asyncio.run(_dich_vu(tao_model(), so_a, **khac).reply(yc))
    b = asyncio.run(
        _dich_vu(tao_model(), so_b, **khac).reply(yc, theo_doi=lambda e: None))
    assert _dau(a) == _dau(b), f"{ten}: stream đổi kết quả cuối"
    assert [(r.text, _dau(k)) for r, k in so_a.ghi] == [
        (r.text, _dau(k)) for r, k in so_b.ghi], f"{ten}: stream đổi sổ phiên"


def test_THEO_DOI_HONG_thi_luot_van_xong_va_vao_so():
    def hong(_su_kien):
        raise RuntimeError("màn hình hỏng")

    so = _So()
    kq = asyncio.run(
        _dich_vu(_ModelStream("Chào Sếp, em đây nhé."), so).reply(
            _yeu_cau(), theo_doi=hong))
    assert kq.status is ChatStatus.OK and kq.text == "Chào Sếp, em đây nhé."
    assert len(so.ghi) == 1


# --------------------------------------------------------------------------- #
# Tuyến HTTP — `xong` đúng một, là dòng cuối, và mang đủ trường của /api/chat.
# --------------------------------------------------------------------------- #
class _Runtime:
    model_configured = True

    def __init__(self, service):
        self.service = service

    async def aclose(self):
        pass


async def _goi(service, duong, body):
    app = chat_app.create_chat_app(runtime=_Runtime(service))
    async with TestClient(TestServer(app)) as client:
        r = await client.post(duong, json=body)
        return r.status, await r.text()


@pytest.mark.parametrize("ten", list(_KICH_BAN) + ["phiên hỏng"])
def test_SU_KIEN_XONG_dung_mot_la_dong_cuoi_va_du_truong(ten):
    if ten == "phiên hỏng":
        tao_model, khac, cau, phien = (
            lambda: _ModelStream("x"), {}, KHONG_CAN_MANG, "")
    else:
        (tao_model, khac, cau), phien = _KICH_BAN[ten], str(uuid4())
    body = {"text": cau, "session_id": phien}
    http, raw = asyncio.run(_goi(_dich_vu(tao_model(), **khac), "/api/chat", body))
    _, raw_stream = asyncio.run(
        _goi(_dich_vu(tao_model(), **khac), "/api/chat/stream", body))
    thuong = json.loads(raw)
    dong = [json.loads(x) for x in raw_stream.splitlines() if x.strip()]
    xong = [d for d in dong if d.get("loai") == "xong"]
    assert len(xong) == 1, f"{ten}: {len(xong)} sự kiện xong"
    assert dong[-1] is xong[0], f"{ten}: xong không phải dòng cuối"
    assert set(xong[0]) == set(thuong) | {"loai", "http"}
    assert xong[0]["http"] == http
    for truong in set(thuong) - {"request_id", "latency_ms"}:
        assert xong[0][truong] == thuong[truong], f"{ten}: lệch {truong}"


def test_TRINH_DUYET_DONG_giua_chung_thi_luot_van_vao_so(monkeypatch):
    goc = web.StreamResponse.write
    da_ghi = {"lan": 0}

    async def write(self, data):
        da_ghi["lan"] += 1
        if da_ghi["lan"] > 1:
            raise ConnectionResetError("trình duyệt đã đóng")
        return await goc(self, data)

    monkeypatch.setattr(web.StreamResponse, "write", write)
    so = _So()
    dv = _dich_vu(
        _ModelStream("Chào Sếp, em đang trả lời từng chữ một nhé.", buoc=3,
                     cham=0.02), so)
    asyncio.run(_goi(dv, "/api/chat/stream",
                     {"text": KHONG_CAN_MANG, "session_id": str(uuid4())}))
    assert da_ghi["lan"] >= 2, "phép gieo không tới: chưa lần ghi nào hỏng"
    assert len(so.ghi) == 1 and so.ghi[0][1].status is ChatStatus.OK


def test_TRAN_CHO_TRINH_DUYET_dai_hon_tran_may_chu():
    """Đọc cả hai số TỪ MÃ. Trước 11/09 giao diện bỏ chờ ở 105 s trong khi
    đường có nguồn được 180 s: màn hình nói quá giờ, sổ ghi thành công."""
    html = (PROJECT_ROOT / "interface" / "web" / "chat.html").read_text(encoding="utf-8")
    so = re.findall(r"^const CLIENT_TIMEOUT_MS = (\d+);$", html, re.M)
    assert len(so) == 1, f"tìm thấy {len(so)} khai báo CLIENT_TIMEOUT_MS"
    tran_may_chu = _HAN_GIO_CO_NGUON + _AN_HAN_GHI_SO
    assert tran_may_chu == DAC_TA_TRAN_CHO_S, (
        "trần máy chủ đổi — sửa đặc tả và trần trình duyệt cùng lúc")
    assert int(so[0]) / 1000 >= tran_may_chu


# --------------------------------------------------------------------------- #
# Cổng Ollama — đường từng mảnh trả về Y HỆT đường một lần.
# --------------------------------------------------------------------------- #
def _cong_ollama(xu_ly) -> OllamaGateway:
    return OllamaGateway(
        OllamaConfig(),
        client=httpx.AsyncClient(transport=httpx.MockTransport(xu_ly)))


def _ndjson(*goi) -> str:
    return "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in goi)


def _ollama_gia(van: str):
    def xu_ly(request: httpx.Request) -> httpx.Response:
        if json.loads(request.content)["stream"]:
            manh = [van[i:i + 3] for i in range(0, len(van), 3)]
            goi = [{"message": {"role": "assistant", "content": m}, "done": False}
                   for m in manh]
            goi.append({"message": {"role": "assistant", "content": ""},
                        "done": True})
            return httpx.Response(200, text=_ndjson(*goi))
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": van}, "done": True})
    return xu_ly


@pytest.mark.parametrize("van", [
    "Chào Sếp, em đây.",
    "   Có khoảng trắng hai đầu   ",
    "Trả lời xong. [[AURA_REQUIRES_WEB]]",
    "[[AURA_REQUIRES_WEB]]",
    "SEARCH: giá vàng hôm nay",
])
def test_OLLAMA_tung_manh_tra_ve_Y_HET_mot_lan(van):
    thay = []
    mot_lan = asyncio.run(_cong_ollama(_ollama_gia(van)).generate(_yeu_cau()))
    tung_manh = asyncio.run(_cong_ollama(_ollama_gia(van)).generate(
        _yeu_cau(), khi_co_chu=thay.append))
    assert tung_manh == mot_lan
    assert thay and thay[-1] == van, "khi_co_chu không nhận bản thô đã gom"
    assert all(b.startswith(a) for a, b in zip(thay, thay[1:]))


@pytest.mark.parametrize("ten, tra_ve", [
    ("cụt giữa chừng", lambda: httpx.Response(200, text=_ndjson(
        {"message": {"content": "Nửa câu"}, "done": False}))),
    ("dòng báo lỗi", lambda: httpx.Response(200, text=_ndjson(
        {"error": "model not found"}))),
    ("dòng không phải JSON", lambda: httpx.Response(200, text="không phải json\n")),
    ("HTTP 500", lambda: httpx.Response(500, text="lỗi")),
])
def test_OLLAMA_tung_manh_hong_thi_LOI_khong_phai_nua_cau(ten, tra_ve):
    with pytest.raises(ModelGatewayError):
        asyncio.run(_cong_ollama(lambda _r: tra_ve()).generate(
            _yeu_cau(), khi_co_chu=lambda _t: None))


def test_OLLAMA_khi_co_chu_HONG_thi_cau_tra_loi_van_du():
    def hong(_t):
        raise RuntimeError("màn hình hỏng")

    van = "Chào Sếp, em trả lời đủ câu."
    kq = asyncio.run(_cong_ollama(_ollama_gia(van)).generate(
        _yeu_cau(), khi_co_chu=hong))
    assert kq.text == van


def test_BAC_THANG_khong_bao_gio_dua_khi_co_chu_cho_THAY():
    class _TroYeu:
        stream_duoc = True

        async def generate(self, request, *, history=(), sources=(),
                           khi_co_chu=None):
            if khi_co_chu is not None:
                khi_co_chu("ừm ")
            return ModelReply("ừm")

    class _Thay:
        async def generate(self, request, *, history=(), sources=()):
            return ModelReply("Câu của thầy, đủ ý và dài hơn hẳn câu của trò.")

    cong = LocalFirstGateway(local=_TroYeu(), cloud=_Thay())
    assert cong.stream_duoc
    kq = asyncio.run(cong.generate(_yeu_cau(), khi_co_chu=lambda _t: None))
    assert kq.text.startswith("Câu của thầy")
    assert not LocalFirstGateway(local=_Thay()).stream_duoc


# --------------------------------------------------------------------------- #
# Chi phí và đặc tả.
# --------------------------------------------------------------------------- #
def test_CHI_PHI_DUNG_BAN_NHAP_3000_ky_tu_tung_ky_tu():
    cau = ("Đệ quy là khi một hàm tự gọi chính nó để giải bài toán nhỏ hơn. "
           "Ví dụ tính giai thừa: n! = n × (n-1)!, dừng ở 0! = 1.\n")
    van = (cau * 40)[:3000]

    def luot(theo_doi):
        t = time.perf_counter()
        asyncio.run(_dich_vu(_ModelStream(van)).reply(_yeu_cau(), theo_doi=theo_doi))
        return time.perf_counter() - t

    co = min(luot(lambda _e: None) for _ in range(3))
    khong = min(luot(None) for _ in range(3))
    assert co - khong <= DAC_TA_CHI_PHI_S, f"dựng bản nháp tốn {co - khong:.3f} s"


def test_NGUONG_khop_khoi_dac_ta():
    khoi = re.search(
        r"<!-- CHOT:stream-chat -->(.*?)<!-- /CHOT:stream-chat -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:stream-chat"
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", khoi.group(1), re.M))
    chu_dau = hang.get("chữ đầu tiên, tính từ lúc gọi model", "")
    assert f"+ {DAC_TA_CHU_DAU_BU_S}" in chu_dau and "5/5 câu" in chu_dau, chu_dau
    assert DAC_TA_TONG_HE_SO in hang.get(
        "tổng thời gian, stream so với không stream", "")
    assert f"≤ {DAC_TA_CHI_PHI_S}".replace(".", ",") + " s" in hang.get(
        "chi phí dựng bản nháp, 3.000 ký tự từng ký tự một", "")
    assert "100 %" in hang.get("bản nháp là phần đầu của câu cuối đã che", "")
    assert f"{DAC_TA_MAU_CHE}/{DAC_TA_MAU_CHE}" in hang.get(
        "mẫu che có ca bí mật kích hoạt", "")
    assert f"{DAC_TA_LUAT_GIU}/{DAC_TA_LUAT_GIU}" in hang.get(
        "luật giữ lại gỡ ra thì có ca lọt", "")
    assert f"≥ {DAC_TA_TRAN_CHO_S} s" in hang.get("trần chờ phía trình duyệt", "")
