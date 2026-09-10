# -*- coding: utf-8 -*-
"""Kho tra cứu cục bộ — `tra kho: <câu hỏi>`.

Đăng ký ở `KY_LUAT_THUC_THI.md` mục *"Kho tra cứu cục bộ"* (08/09/2026), chép
TAY xuống đây. Kế hoạch: `docs/KE_HOACH_KHO_TRA_CUU_2026-09-08.md`.

HAI BỘ CÂU HỎI, VÀ BỘ B LÀ THƯỚC — KHÔNG ĐƯỢC SỬA CHO ĐẸP SỐ.
Bộ A dùng để CHỌN thiết kế (bỏ `docs/lich_su/`, trộn RRF). Bộ B viết ngày
08/09/2026 **trước khi biết thiết kế nào thắng**, và chưa từng dùng để chọn gì.
Đo được:

    RRF, bỏ docs/lich_su/    bộ A      bộ B
      top-1                  7/10      4/10     <- tụt gần một nửa
      top-3                  8/10      8/10     <- con số ổn định duy nhất

Đo trên CHỈ MỤC SẢN PHẨM (437 đoạn). Nguyên mẫu 435 đoạn cho bộ A top-1 8/10;
kế hoạch còn ghi con số ấy. Chênh một câu, và tài liệu phải theo phép đo.

Sửa một câu trong bộ B để cho số đẹp hơn là **sửa thước**. Nếu một câu trong đó
sai (dấu hiệu gõ nhầm, tài liệu đổi), thì sửa kèm ghi lý do ngay tại dòng ấy.
"""
from __future__ import annotations

import asyncio
import json
import re
import time

import pytest

from core import tra_cuu
from core.paths import PROJECT_ROOT

# ---- chép TAY từ đặc tả ----------------------------------------------------
DAC_TA_TOP3_A = 8
DAC_TA_TOP3_B = 8
DAC_TA_SO_DOAN_HIEN = 3
# Đo trên GIỮA của 5 lượt trong CÙNG một vòng lặp sự kiện — vì app thật chạy
# một vòng lặp suốt đời, còn `asyncio.run` mỗi lượt là hiện vật của bộ test.
#
#   asyncio.run mỗi lượt   giữa 341,7 ms   <- bản đầu của bài này đo cái này
#   MỘT vòng lặp (app thật) giữa 103,8 ms
#
# Trần 300 ms trên giữa: biên ~3 lần. Không đặt trên LỚN NHẤT vì một lượt lẻ
# 369 ms đã xuất hiện khi máy bận, và một cửa đỏ vì máy bận là cửa mong manh.
DAC_TA_NHUNG_MS = 300
DAC_TA_GOI_NGOAI = 2

# top-1 CỐ Ý KHÔNG CÓ NGƯỠNG: 7/10 trên bộ A và 4/10 trên bộ B. Đặt ngưỡng cho
# một con số gần như giảm nửa giữa hai mẫu là fit hằng số vào mẫu.

BO_A = (
    ("hộp cát giới hạn bao nhiêu bộ nhớ", "256"),
    ("vì sao không đưa bộ căn chữ vào kho chính", "273 MB"),
    ("máy này có card đồ hoạ rời không", "không GPU rời"),
    ("lỗi x in y đã mắc bao nhiêu lần", "x in y"),
    ("cái gì làm bộ test v3 treo vô hạn", "treo"),
    ("ngắt mạng cho polyglot làm được chưa", "CHƯA CHẶN ĐƯỢC"),
    ("được phép dùng bao nhiêu gói ngoài", "gói ngoài"),
    ("firecrawl dùng giấy phép gì", "AGPL"),
    ("vì sao không được đẩy lịch sử kho cũ lên GitHub", "88e8c07"),
    ("công cụ nào dùng để gieo lỗi", "gieo.py"),
)

BO_B = (
    ("model local tên gì", "qwen3.5:4b"),
    ("kho model để ở ổ nào", "ollama-models"),
    ("cổng của app chat là bao nhiêu", "8799"),
    ("trần số câu của viết truyện", "22"),
    ("ai không được tự chấm PASS", "Verifier"),
    ("máy có bao nhiêu RAM", "11,7 GB"),
    ("v3 tách khỏi kho cũ ngày nào", "12/08/2026"),
    ("app thẻ chuyển sang kho nào", "app-the"),
    ("lỗi sai ngày của đồng hồ là bao nhiêu", "20 ngày"),
    ("bao nhiêu ca trong sổ bệnh án", "31"),
)

# Ba câu KHÔNG có đáp án trong kho. Vì đã bỏ cổng, bài đối chứng không đòi
# chúng bị chặn — nó đòi kết quả HIỆN ĐÚNG TÊN TỆP để Sếp thấy ngay là lệch.
# Dòng kết quả bắt đầu ở CỘT 0; thân đoạn thụt 3 dấu cách. Đừng `strip()`
# trước khi khớp — bản đầu của các cửa dưới làm thế và đếm nhầm **thân đoạn**
# bắt đầu bằng "1. Hidden tests." thành một kết quả thứ tư. Cửa đỏ vì đếm phải
# thứ khác đang chuyển động, không phải vì mã sai.
_LA_DONG_DOAN = re.compile(r"^\d+\. \S")

DOI_CHUNG = ("giá vàng hôm nay bao nhiêu",
             "thời tiết Hà Nội ngày mai",
             "tỷ số trận Real Madrid tối qua")


def _khoi_dac_ta(ten: str) -> str:
    """Đọc đúng khối giữa `<!-- CHOT:ten -->` và `<!-- /CHOT:ten -->`."""
    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(rf"<!-- CHOT:{ten} -->(.*?)<!-- /CHOT:{ten} -->", spec, re.S)
    assert m, f"mất neo CHOT:{ten} trong đặc tả"
    return m.group(1)


def _kho():
    k = tra_cuu.doc_chi_muc()
    if k is None:
        pytest.skip("KHÔNG ĐO ĐƯỢC: chưa dựng chỉ mục — "
                    "`venv\\Scripts\\python.exe tools/dung_chi_muc.py`")
    return k


def _co_ollama() -> bool:
    """Hỏi Ollama TRỰC TIẾP, không đi qua `_nhung_cau`.

    BẪY TAUTOLOGICAL, bắt được bằng phép gieo (08/09). Bản đầu viết
    `return asyncio.run(tra_cuu._nhung_cau("thử")) is not None` — tức **máy dò
    và thứ bị dò là cùng một hàm**. Gieo cho `_nhung_cau` luôn trả `None` thì
    cả 4 bài phụ thuộc Ollama đều **bỏ qua**, và cửa mù: một máy CÓ Ollama mà
    mã gọi Ollama hỏng sẽ đọc ra y hệt một máy KHÔNG có Ollama.

    Nay: `/api/tags` trả về `bge-m3` thì Ollama CÓ. Từ đó, `_nhung_cau` trả
    `None` là **lỗi của mã mình** và phải ĐỎ, không được bỏ qua.
    """
    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5.0)
        r.raise_for_status()
        return any(tra_cuu.MODEL_NHUNG in m.get("name", "")
                   for m in r.json().get("models", []))
    except Exception:
        return False


def test_NHUNG_hong_khi_CO_Ollama_thi_phai_DO_chu_khong_bo_qua():
    """Máy có Ollama mà `_nhung_cau` trả `None` là LỖI CỦA MÃ MÌNH.

    Đây là bài đóng cái lỗ mà bản đầu của `_co_ollama` để hở: khi máy dò và
    thứ bị dò là một, mọi hỏng hóc đều đội lốt "máy không có Ollama".
    """
    if not _co_ollama():
        pytest.skip("KHÔNG ĐO ĐƯỢC: Ollama/bge-m3 không có trên máy này")
    v = asyncio.run(tra_cuu._nhung_cau("hộp cát"))
    assert v is not None, (
        "Ollama ĐANG chạy và có bge-m3, nhưng `_nhung_cau` trả None — "
        "đường gọi của mình hỏng, không phải máy thiếu công cụ")
    assert len(v) == 1024, f"bge-m3 phải cho 1024 chiều, thấy {len(v)}"


def _cham(kho, bo, dung_vector: bool):
    t1 = t3 = 0
    for cau, dau in bo:
        v = asyncio.run(tra_cuu._nhung_cau(cau)) if dung_vector else None
        ix = kho.tron(cau, v, DAC_TA_SO_DOAN_HIEN)
        co = [dau.lower() in (kho.doan[i]["tieu_de"] + " "
                              + kho.doan[i]["noi_dung"]).lower() for i in ix]
        t1 += bool(co and co[0])
        t3 += any(co)
    return t1, t3


# ---------------------------------------------------------------------------
# LỆNH
# ---------------------------------------------------------------------------

def test_la_lenh_chi_bat_dung_tien_to():
    assert tra_cuu.la_lenh("tra kho: hộp cát")
    assert tra_cuu.la_lenh("  TRA KHO:  hộp cát  ")
    assert not tra_cuu.la_lenh("tra cứu giúp tôi giá vàng")
    assert not tra_cuu.la_lenh("Chào Sếp")
    assert tra_cuu.boc_cau_hoi("tra kho:  hộp cát  ") == "hộp cát"


def test_bo_dau_lam_viec_ca_hai_chieu():
    """Sếp gõ lúc có dấu lúc không — BM25 phải cho cùng một kết quả.

    Đo 08/09: bge-m3 mất một nửa độ chính xác khi câu hỏi không dấu (top-1
    4/10 -> 2/10); BM25 thì giống hệt vì cả hai vế đi qua `bo_dau`. Đó là lý
    do nửa từ khoá vẫn đáng giữ dù nó yếu hơn.
    """
    assert tra_cuu.tach_tu("Trần RAM 256 MB") == tra_cuu.tach_tu("Tran RAM 256 MB")
    assert "duong" in tra_cuu.tach_tu("đường dẫn")


# ---------------------------------------------------------------------------
# BA TRẠNG THÁI — không được gộp thành hai
# ---------------------------------------------------------------------------

def test_CHUA_DUNG_CHI_MUC_khong_duoc_doc_thanh_khong_tim_thay(tmp_path, monkeypatch):
    """Thiếu chỉ mục là KHÔNG ĐO ĐƯỢC, không phải "kho không có gì".

    `x in y` LẦN THỨ MƯỜI HAI, và lần này ngay trong cửa canh việc tách ba
    trạng thái. Bản đầu bài này viết `"không tìm thấy" not in ra.lower()` —
    đỏ ngay, vì câu trả lời của máy nói *"đây KHÔNG phải 'không tìm thấy'"*
    và cửa thấy đúng cụm chữ ấy.

    Nay đối chiếu **chuỗi THẬT mà `_dinh_dang` dùng** khi không có kết quả,
    và đòi không có dòng đoạn nào. Đối chiếu một cách diễn đạt thì lần sau
    đổi câu chữ là cửa lại sai.
    """
    # Vá `CHI_MUC`, KHÔNG truyền `kho=doc_chi_muc(...)`: hàm ấy trả `None` khi
    # thiếu tệp, mà `tra_giup(kho=None)` không phân biệt được "không truyền"
    # với "truyền None" nên nó rơi về chỉ mục THẬT — bản đầu bài này đỏ đúng
    # kiểu ấy, và nó đỏ vì đo nhầm trạng thái chứ không vì mã sai.
    monkeypatch.setattr(tra_cuu, "CHI_MUC", tmp_path / "khong_co.json")
    ra = asyncio.run(tra_cuu.tra_giup("tra kho: hộp cát"))
    assert "CHƯA DỰNG CHỈ MỤC" in ra, ra
    assert "Không có đoạn nào khớp" not in ra, (
        "thiếu chỉ mục bị trả về bằng câu của trạng thái 'kho không có gì' — "
        "hai trạng thái khác nhau, gộp lại thì 'chưa đo được' đội lốt 'đã đo'")
    assert not [d for d in ra.splitlines() if _LA_DONG_DOAN.match(d)], (
        f"thiếu chỉ mục mà vẫn hiện đoạn:\n{ra}")
    assert "dung_chi_muc.py" in ra, "không chỉ ra cách dựng"


def test_TUT_VE_TU_KHOA_phai_NOI_RA_chu_khong_tut_im_lang(monkeypatch):
    """Ollama chết thì kết quả vẫn ra, vẫn trông như thường, chỉ KÉM ĐI.

    Đó là thứ nguy hiểm nhất ở đây: không ai biết để đo lại. Nên lượt tụt phải
    tự khai ngay trên dòng đầu.
    """
    kho = _kho()

    async def hong(_):
        return None

    monkeypatch.setattr(tra_cuu, "_nhung_cau", hong)
    ra = asyncio.run(tra_cuu.tra_giup("tra kho: hộp cát", kho=kho))
    assert "CHỈ TÌM THEO TỪ KHOÁ" in ra, f"tụt im lặng: {ra[:200]}"
    assert "bge-m3" in ra, "không nói ra thứ nào hỏng"


def test_CHAY_DU_thi_KHONG_duoc_tu_khai_la_dang_tut():
    """Ca đối chứng của bài trên: chạy đủ mà vẫn báo tụt cũng là nói dối."""
    kho = _kho()
    if not _co_ollama():
        pytest.skip("KHÔNG ĐO ĐƯỢC: Ollama/bge-m3 không gọi được")
    ra = asyncio.run(tra_cuu.tra_giup("tra kho: hộp cát", kho=kho))
    assert "CHỈ TÌM THEO TỪ KHOÁ" not in ra, ra[:200]


# ---------------------------------------------------------------------------
# ĐỘ CHÍNH XÁC — hai bộ, và bộ B là thước
# ---------------------------------------------------------------------------

def test_TOP3_bo_A_dat_nguong():
    kho = _kho()
    if not _co_ollama():
        pytest.skip("KHÔNG ĐO ĐƯỢC: Ollama/bge-m3 không gọi được")
    t1, t3 = _cham(kho, BO_A, True)
    assert t3 >= DAC_TA_TOP3_A, f"bộ A top-3 {t3}/10 (top-1 {t1}/10)"


def test_TOP3_bo_B_GIU_RIENG_dat_nguong():
    """Bộ B chưa từng dùng để chọn gì. Đây là con số thật.

    Nếu bài này đỏ thì KHÔNG được sửa câu hỏi cho vừa — phải sửa máy tìm, hoặc
    hạ ngưỡng trong đặc tả và nói ra vì sao.
    """
    kho = _kho()
    if not _co_ollama():
        pytest.skip("KHÔNG ĐO ĐƯỢC: Ollama/bge-m3 không gọi được")
    t1, t3 = _cham(kho, BO_B, True)
    assert t3 >= DAC_TA_TOP3_B, f"bộ B top-3 {t3}/10 (top-1 {t1}/10)"


def test_CHI_TU_KHOA_van_tim_duoc_it_nhieu():
    """Nửa từ khoá chạy KHÔNG CẦN Ollama — nên bài này luôn đo được.

    Nền đo 08/09: BM25 một mình trên chỉ mục đã lọc cho top-3 4/10 ở bộ B.
    Ngưỡng đặt ở 3 để bài không mong manh, nhưng vẫn đỏ nếu máy tìm hỏng hẳn.
    """
    kho = _kho()
    _, t3 = _cham(kho, BO_B, False)
    assert t3 >= 3, f"chỉ từ khoá: bộ B top-3 {t3}/10 — máy tìm hỏng?"


# ---------------------------------------------------------------------------
# DẠNG TRẢ LỜI
# ---------------------------------------------------------------------------

def test_hien_DUNG_BA_doan_va_moi_doan_co_NGUON():
    kho = _kho()
    ra = asyncio.run(tra_cuu.tra_giup("tra kho: hộp cát giới hạn bộ nhớ",
                                      kho=kho))
    dong = [d for d in ra.splitlines() if _LA_DONG_DOAN.match(d)]
    assert len(dong) == DAC_TA_SO_DOAN_HIEN, f"{len(dong)} đoạn:\n{ra}"
    for d in dong:
        assert "›" in d, f"đoạn không kèm tệp › tiêu đề: {d}"
    assert "KHÔNG chắc" in ra, (
        "mất câu tự nhận không chắc — top-1 chỉ đúng 4/10 trên bộ giữ riêng, "
        "không được trình bày như thể đoạn đầu là câu trả lời")


def test_DOI_CHUNG_cau_khong_co_dap_an_van_hien_TEN_TEP(monkeypatch):
    """Không có cổng, nên máy VẪN trả 3 đoạn — và đó là lựa chọn có chủ ý.

    Đo 08/09: khe giữa hai nhóm điểm là **0,01** trên thang rộng 15 điểm. Dựng
    cổng theo đó thì 3/10 câu ĐÚNG bị chặn nhầm mà *"thời tiết Hà Nội ngày
    mai"* **vẫn lọt**. Nên chỗ dựa không phải cổng, mà là TÊN TỆP hiện ra để
    Sếp thấy ngay `NGHIEM_THU_GIAO_DIEN.md` không trả lời được giá vàng.
    """
    kho = _kho()

    async def khong_nhung(_):
        return None

    monkeypatch.setattr(tra_cuu, "_nhung_cau", khong_nhung)
    for cau in DOI_CHUNG:
        ra = asyncio.run(tra_cuu.tra_giup(f"tra kho: {cau}", kho=kho))
        dong = [d for d in ra.splitlines() if _LA_DONG_DOAN.match(d)]
        assert dong, f"{cau!r} không ra gì"
        for d in dong:
            assert ".md ›" in d, f"{cau!r}: đoạn không nói rõ tệp nào: {d}"


def test_NHUNG_mot_cau_du_nhanh():
    """Đo lượt chat THẬT: nhiều lượt trong CÙNG một vòng lặp sự kiện.

    Bản đầu bài này gọi `asyncio.run` mỗi lượt và đo 497 ms — đỏ so với trần
    400 ms — rồi đọc ra như "bge-m3 chậm". Thật ra nó đo **hiện vật của bộ
    test**: mỗi `asyncio.run` là một vòng lặp mới, nên client được dựng lại,
    và dựng client tốn ~194 ms. App thật chạy một vòng lặp suốt đời.

    Bản vá đi kèm: dùng lại `AsyncClient` theo vòng lặp — giữa 396 -> 104 ms.
    """
    if not _co_ollama():
        pytest.skip("KHÔNG ĐO ĐƯỢC: Ollama/bge-m3 không gọi được")

    async def do_nam_luot():
        await tra_cuu._nhung_cau("hâm nóng")   # dựng client + nạp model
        xs = []
        for cau, _ in BO_A[:5]:
            t0 = time.perf_counter()
            await tra_cuu._nhung_cau(cau)
            xs.append((time.perf_counter() - t0) * 1000)
        return xs

    xs = sorted(asyncio.run(do_nam_luot()))
    giua = xs[len(xs) // 2]
    assert giua < DAC_TA_NHUNG_MS, (
        f"giữa {giua:.0f} ms, trần {DAC_TA_NHUNG_MS} ms — 5 lượt: "
        f"{[round(x) for x in xs]}")


# ---------------------------------------------------------------------------
# ĐƯỜNG THẬT — chấm được một hàm không nói kết quả của nó đi tới đâu
# ---------------------------------------------------------------------------

def test_DUONG_THAT_qua_ChatService_khong_goi_mang():
    """Bài học 05/09: *"vá xong một trường không nói gì về trường bên cạnh"*.

    Mọi bài trên gọi thẳng `tra_giup`. Chúng vẫn xanh kể cả khi `chat_service`
    không hề nối vào. Bài này đi qua `ChatService.reply()` thật, và nó cũng là
    chỗ duy nhất chứng minh được `used_web=False` — lượt tra kho KHÔNG gửi câu
    của Sếp ra ngoài.
    """
    from tests.test_chat_service import FakeGuard, FakeModel, FakeStore, _request
    from core.chat_service import ChatService
    from core.chat_contract import ChatStatus

    _kho()  # thiếu chỉ mục thì bỏ qua, không chấm nhầm
    store, model = FakeStore(), FakeModel([])
    kq = asyncio.run(ChatService(model=model, store=store, guard=FakeGuard())
                     .reply(_request(text="tra kho: hộp cát giới hạn bộ nhớ")))

    assert kq.status is ChatStatus.OK, kq
    assert kq.used_web is False, "lượt tra kho KHÔNG được đánh dấu là gọi mạng"
    assert kq.sources == (), f"lượt cục bộ mà có nguồn web: {kq.sources}"
    assert "›" in kq.text, f"không thấy nguồn trong câu trả lời:\n{kq.text[:300]}"
    assert not model.calls, (
        f"MODEL BỊ GỌI {len(model.calls)} lần — lượt tra kho phải do MÁY trả "
        f"lời thẳng, để đoạn văn tới tay Sếp nguyên văn kèm tên tệp")
    assert store.appended, "lượt tra kho không vào sổ phiên (CLAUDE.md §5)"


# ---------------------------------------------------------------------------
# ĐẶC TẢ
# ---------------------------------------------------------------------------

def test_DAC_TA_tra_cuu_van_o_lai_tai_lieu():
    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(r"<!-- CHOT:tra-cuu -->(.*?)<!-- /CHOT:tra-cuu -->", spec, re.S)
    assert m, "mất neo CHOT:tra-cuu"
    khoi = m.group(1)
    for cum in ("8/10", "4/10",          # hai bộ, và chỗ top-1 tụt
                "0,01",                   # khe giả của cổng đã bỏ
                "1,2 GB",                 # bge-m3 nằm sẵn trên máy
                "20/20",                  # hàng rào hết chỗ
                str(DAC_TA_NHUNG_MS)):
        assert cum in khoi, f"khối tra-cuu mất {cum!r}"


def test_van_dung_HAI_goi_ngoai():
    """Kho tra cứu KHÔNG được kéo thêm gói nào — đó là điều kiện của kế hoạch."""
    dong = [d.strip() for d in
            (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
            .splitlines() if d.strip() and not d.strip().startswith("#")]
    assert len(dong) == DAC_TA_GOI_NGOAI, f"{len(dong)} gói: {dong}"


def test_DAC_TA_nhan_kho_cong_nghe_van_o_lai_tai_lieu():
    """Kho công nghệ NẰM TRONG chỉ mục này, nên nhãn sai của nó là lỗi của đây.

    Đo 10/09: 13 mục kho khai `BENCHMARKED`/`SMOKE_TESTED`/`INSTALLED` — tức
    *"đã chạy thật trên máy này"* — thì **8/13 không còn thấy trên máy**. Nhãn
    không mang ngày và không mang môi trường, nên người đọc hiểu là thì hiện
    tại; mà `core/tra_cuu.py` đưa đúng những dòng ấy lại cho Sếp.

    46 mục `DISCOVERED` thì KHÔNG phải nợ — chúng không khai gì. Bài này giữ
    đúng chỗ phân biệt ấy khỏi trôi.
    """
    khoi = _khoi_dac_ta("nhan-kho-cong-nghe")
    phang = " ".join(khoi.split())
    for cum in ("5/13", "8/13",          # còn / mất
                "Docling",               # ca đã trả giá thật
                "NGÀY",                  # luật mới
                "MÔI TRƯỜNG"):
        assert cum in phang, f"khối nhan-kho-cong-nghe mất {cum!r}"
    assert "46 mục `DISCOVERED` KHÔNG phải nợ" in phang, (
        "mất câu phân biệt: mục DISCOVERED không khai gì nên không thể sai — "
        "gộp chúng vào 'nợ chưa kiểm' là đi ngược chính luật của kho")
