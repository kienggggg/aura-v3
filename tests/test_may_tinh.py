# -*- coding: utf-8 -*-
"""Model đoán số, máy thì tính.

10/08/2026 đo trên máy thật: "Còn bao nhiêu ngày nữa tới ngày 1 tháng 9?" ->
AURA đáp **"khoảng 23 ngày"**.  Đúng ra là 22.  Đồng hồ đã đưa đúng mốc 10/08;
cái sai nằm ở phép trừ — model 4B sinh chữ theo xác suất, nó không trừ.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from core.chat_contract import ChatRequest
from core.may_tinh import tinh_bieu_thuc, tinh_giup

HOM_NAY = datetime(2026, 8, 10, 15, 30)     # Thứ Hai


# ------------------------------------------------------------ đếm ngày
def test_dung_con_so_lam_AURA_noi_sai():
    """Đúng câu đã sai: 10/08 -> 01/09 là 22 ngày, không phải 23."""
    câu = tinh_giup("Còn bao nhiêu ngày nữa tới ngày 1 tháng 9?", now=HOM_NAY)
    assert câu is not None
    assert "22 ngày" in câu
    assert "23" not in câu
    # Đưa CÂU MẪU chứ không đưa mệnh lệnh: bản đầu dặn "đừng nói 'khoảng'" và
    # model tuân lệnh vụng — "Chưa có 22 ngày nữa đến ngày 1 tháng 9."  Số đúng,
    # câu sai.  Cho sẵn câu để chép thì không còn chỗ nào đặt vụng.
    assert 'Còn 22 ngày nữa đến 01/09/2026.' in câu


@pytest.mark.parametrize("hoi,mong_doi", [
    ("còn bao nhiêu ngày nữa tới ngày 11 tháng 8", "1 ngày"),
    ("mấy ngày nữa thì tới 20/08?", "10 ngày"),
    ("bao nhiêu ngày nữa đến ngày 10 tháng 8", "0 ngày"),
    ("con bao nhieu ngay nua toi ngay 1 thang 9", "22 ngày"),  # gõ không dấu
])
def test_dem_ngay_nhieu_kieu_hoi(hoi, mong_doi):
    câu = tinh_giup(hoi, now=HOM_NAY)
    assert câu is not None and mong_doi in câu


def test_moc_da_qua_trong_nam_thi_hieu_la_NAM_SAU():
    """Hỏi ngày 1/3 vào tháng 8 thì Sếp đang nói 1/3 sang năm."""
    câu = tinh_giup("còn bao nhiêu ngày nữa tới ngày 1 tháng 3", now=HOM_NAY)
    assert câu is not None and "01/03/2027" in câu


def test_ngay_khong_ton_tai_thi_IM_chu_dung_bia():
    assert tinh_giup("còn bao nhiêu ngày nữa tới ngày 31 tháng 2", now=HOM_NAY) is None


# ------------------------------------------------------------ số học
@pytest.mark.parametrize("bieu_thuc,ket_qua", [
    ("2+2", 4), ("15*3", 45), ("100/8", 12.5),
    ("(2+3)*4", 20), ("2**10", 1024), ("17%5", 2),
])
def test_tinh_dung(bieu_thuc, ket_qua):
    assert tinh_bieu_thuc(bieu_thuc) == ket_qua


@pytest.mark.parametrize("khong_phai", [
    "", "xin chào", "Thủ đô Việt Nam", "123", "abc+def",
])
def test_khong_phai_phep_tinh_thi_tra_None(khong_phai):
    assert tinh_bieu_thuc(khong_phai) is None


@pytest.mark.parametrize("doc", [
    "__import__('os').system('dir')",
    "open('D:/bi_mat.txt').read()",
    "9**9**9",
    "1/0",
])
def test_chuoi_doc_hai_bi_tu_choi(doc):
    """Cố ý KHÔNG dùng `eval()`.

    Câu hỏi đến từ Sếp, nhưng lịch sử hội thoại có thể mang nguyên văn từ trang
    web lạ.  `eval` trên chuỗi như thế là cho người khác chạy mã trong tiến
    trình AURA.  `9**9**9` thì không nguy hiểm nhưng treo máy và ăn hết RAM.
    """
    assert tinh_bieu_thuc(doc) is None


@pytest.mark.parametrize("hoi,ket_qua", [
    ("Tính giúp tôi 1247 * 38 bằng bao nhiêu?", "47.386"),
    ("cho hỏi 1000 - 275 là mấy", "725"),
    ("em ơi 84 / 4 ra bao nhiêu vậy", "21"),
])
def test_phep_tinh_NAM_GIUA_cau_chu_van_bat_duoc(hoi, ket_qua):
    """AURA từng trả 46396 cho 1247*38 (đúng là 47.386).

    Máy tính bản đầu chỉ nhận CẢ CÂU là biểu thức thuần, nên có chữ tiếng Việt
    bao quanh là nó bỏ qua và model lại tự đoán số.
    """
    câu = tinh_giup(hoi, now=HOM_NAY)
    assert câu is not None and ket_qua in câu


@pytest.mark.parametrize("khong_phai_phep_tinh", [
    "Nói về COVID-19 đi",
    "Em ở phòng 3 tầng 5",
    "Chào AURA, hôm nay thế nào?",
])
def test_dung_bien_moi_con_so_trong_cau_thanh_phep_tinh(khong_phai_phep_tinh):
    """Rút biểu thức mà quét bừa thì câu nào có số cũng thành bài toán."""
    assert tinh_giup(khong_phai_phep_tinh, now=HOM_NAY) is None


def test_cau_hoi_thuong_thi_KHONG_chen_gi_vao_loi_dan():
    """Chen bừa vào mọi lượt là làm loãng lời dặn và tốn ngữ cảnh."""
    assert tinh_giup("Thủ đô Việt Nam là gì?", now=HOM_NAY) is None
    assert tinh_giup("Chào AURA", now=HOM_NAY) is None


# ------------------------------------------------------------ đã cắm chưa
def test_cong_local_gui_ket_qua_da_tinh_len_model():
    """Viết máy tính mà quên cắm vào lời dặn thì viết cho ai xem."""
    import asyncio

    from core.local_first_gateway import OllamaConfig, OllamaGateway

    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "22 ngày."}}

            return _Response()

    gate = OllamaGateway(OllamaConfig(), client=_Client())
    asyncio.run(gate.generate(ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web",
        text="Còn bao nhiêu ngày nữa tới ngày 1 tháng 9?",
    )))
    # Dữ kiện đi kèm CÂU HỎI (tin cuối), không nằm trong lời dặn hệ thống.
    # 10/08 chat thật: sổ 14 tin, máy tính đưa đúng "144 ngày" vào lời dặn mà
    # AURA vẫn đáp "khoảng 47 ngày" — dữ kiện bị lịch sử chen vào giữa.
    assert "ĐÃ TÍNH SẴN" not in sent["json"]["messages"][0]["content"]
    assert "ĐÃ TÍNH SẴN" in sent["json"]["messages"][-1]["content"]
    assert sent["json"]["messages"][-1]["role"] == "user"
