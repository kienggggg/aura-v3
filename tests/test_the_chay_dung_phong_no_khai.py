# -*- coding: utf-8 -*-
"""Thẻ quy trình phải CHẠY đúng những phòng nó KHAI.

Đo cái lỗ trước khi vá (06/09/2026), bằng cách thay mọi phòng bằng bản giả rồi
**đếm phòng nào được gọi** — không dò chuỗi trong mã::

    thẻ                        KHAI cac_phong              CHẠY THẬT
    card_video_shorts          zeta,aura,alpha,omega       zeta,aura,alpha,omega,gamma
    card_code_doctor           delta,gamma                 zeta,aura,alpha,omega,gamma
    card_polyglot_transpiler   delta,gamma,omega           zeta,aura,alpha,omega,gamma
    card_deep_scout            zeta,aura,omega             zeta,aura,alpha,omega,gamma
    card_novel_writer          aura,gamma                  zeta,aura,alpha,omega,gamma
    card_fullstack_builder     aura,delta,alpha            zeta,aura,alpha,omega,gamma
    card_security_guard        delta,gamma,omega           zeta,aura,alpha,omega,gamma
    card_system_audit          gamma,omega                 zeta,aura,alpha,omega,gamma
                                                           khớp 0/8

`delta` có **bốn** thẻ khai mà chưa lần nào được gọi. Và giá không chỉ là sai
nhãn: `card_code_doctor` xin một lượt quét AST (~2 giây) thì nhận thêm `aura` +
`alpha` — **166 giây** cho việc không ai đặt hàng.

Cùng họ với *"7 phòng tự khai ONLINE, 0 phòng phải chứng minh"* (02/09) và
*"33 cờ, 29 cái TẮT"* của AURA v2: một trường được khai, không ai đọc.
"""
from __future__ import annotations

import asyncio
import json as _json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.phong_alpha as _pa          # noqa: E402
import core.phong_noi_bo as _pnb        # noqa: E402
import core.viet_truyen as _vt          # noqa: E402
import interface.noi_bo_api as _api     # noqa: E402

# Chép TAY từ `KY_LUAT_THUC_THI.md` mục 5b. KHÔNG được viết
# `_api.CHUOI_MAC_DINH` ở đây: gieo đổi hằng số trong mã thì hai vế cùng đổi và
# cửa vẫn xanh — đúng bẫy tautological đã dính hai lần (02/09 và 04/09).
DAC_TA_CHUOI_MAC_DINH = ("zeta", "aura", "alpha", "omega", "gamma")
DAC_TA_SAN_PHONG = 1
DAC_TA_TRAN_PHONG = 8


class _Req:
    def __init__(self, d): self._d = d

    async def json(self): return self._d


@pytest.fixture
def phong_gia(monkeypatch):
    """Thay mọi phòng bằng bản giả, trả về danh sách phòng ĐƯỢC GỌI.

    Đếm lời gọi chứ không soi văn bản hàm. Bốn cửa canh đầu tiên cho
    `api_chay_pipeline` (03/09) mù đúng vì chúng đọc mã bằng `ast.unparse`.
    """
    da_goi: list = []

    def _aura(chu_de, *a, the_loai="truyen", **k):
        da_goi.append("aura")
        return {"trang_thai": "DAT", "van_ban": ("Cau mot. " * 30).strip(),
                "so": {"so_tu": 60, "so_cau_khac": 30}, "so_lan_thu": 1,
                "lan": [{"vi_sao": []}], "ms": 1.0}

    def _alpha(thu_muc, van_ban=None, *a, **k):
        da_goi.append("alpha")
        assert van_ban, "alpha phải nhận kịch bản từ aura"
        thu_muc.mkdir(parents=True, exist_ok=True)
        return {"trang_thai": "PASS", "artifacts": [], "kiem": {"so": {}},
                "ms": 1.0, "vi_sao": ""}

    def _mot_phong(ten):
        def _f(task_id, yeu_cau="", *a, **k):
            da_goi.append(ten)
            return {"trang_thai": "PASS", "artifacts": [], "so": {},
                    "vi_sao": "", "ms": 1.0}
        return _f

    monkeypatch.setattr(_vt, "viet_kich_ban", _aura)
    monkeypatch.setattr(_pa, "dung_video", _alpha)
    monkeypatch.setattr(_pnb, "PHONG",
                        {k: _mot_phong(k)
                         for k in ("zeta", "omega", "gamma", "delta", "beta")})
    return da_goi


def _chay(da_goi, **body):
    da_goi.clear()
    r = asyncio.run(_api.api_chay_pipeline(_Req(dict({"chu_de": "thử"}, **body))))
    return _json.loads(r.body.decode("utf-8")), list(da_goi)


# ---------------------------------------------------------------------------
# CHUỖI THẬT SỰ CHẠY

@pytest.mark.parametrize("the", _api.DANH_SACH_THE_QUY_TRINH,
                         ids=lambda t: t["id"])
def test_the_chay_DUNG_cac_phong_no_khai(phong_gia, the):
    """Khai gì chạy nấy — đúng thứ tự, không thừa không thiếu.

    Tám thẻ khai tám chuỗi KHÁC NHAU, nên một hằng số gõ cứng không thể qua nổi
    bài này: đó là ca đối chứng có sẵn trong chính phép đo.
    """
    _, goi = _chay(phong_gia, preset_id=the["id"])
    assert goi == list(the["cac_phong"]), (
        f"{the['id']} khai {the['cac_phong']} nhưng chạy {goi}")


def test_doc_DANH_MUC_SONG_chu_khong_phai_ban_chep_dong_bang(phong_gia):
    """Bơm một thẻ mới rồi chạy nó — hàm phải đọc danh mục lúc gọi.

    Không có ca này thì bài trên chỉ chứng minh tám thẻ hiện tại khớp, chứ chưa
    chứng minh cơ chế đọc `cac_phong` thật sự sống.
    """
    goc = _api.DANH_SACH_THE_QUY_TRINH
    try:
        _api.DANH_SACH_THE_QUY_TRINH = list(goc) + [
            {"id": "the_bom_vao", "cac_phong": ["beta", "delta", "omega"],
             "the_loai": "truyen"}]
        _, goi = _chay(phong_gia, preset_id="the_bom_vao")
        assert goi == ["beta", "delta", "omega"], goi
    finally:
        _api.DANH_SACH_THE_QUY_TRINH = goc


def test_KHONG_gui_preset_id_thi_giu_chuoi_MAC_DINH(phong_gia):
    """Đường cũ không đổi. Chép tay chuỗi mặc định từ đặc tả."""
    _, goi = _chay(phong_gia)
    assert goi == list(DAC_TA_CHUOI_MAC_DINH), goi


@pytest.mark.parametrize("pid", ["khong_co_that", "", None])
def test_preset_id_LA_thi_giu_chuoi_mac_dinh_va_KHONG_NO(phong_gia, pid):
    """Đường của giao diện: id lạ không được làm đổ cả lượt chạy.

    Khác hẳn `viet_kich_ban`, nơi thể loại lạ NÉM — ở đó là lập trình viên gõ
    sai nên phải nổ to; ở đây là dữ liệu từ ngoài vào.
    """
    d, goi = _chay(phong_gia, preset_id=pid)
    assert goi == list(DAC_TA_CHUOI_MAC_DINH), goi
    assert d["status"] == "PASS", d["thong_diep"]


def test_hang_so_trong_ma_KHOP_dac_ta():
    """Đối chiếu mã với ĐẶC TẢ, không phải với chính nó."""
    assert tuple(_api.CHUOI_MAC_DINH) == DAC_TA_CHUOI_MAC_DINH


# ---------------------------------------------------------------------------
# DANH MỤC THẺ PHẢI CHẠY ĐƯỢC

def test_moi_phong_moi_the_khai_deu_CHAY_DUOC_THAT():
    """Tên phòng trong thẻ phải là phòng có thật trong sổ đăng ký.

    Đối chiếu với `core.phong_noi_bo.PHONG` — sổ THẬT mà bộ chạy tra — chứ
    không đối chiếu với bảng mô tả của chính `noi_bo_api`.
    """
    that = set(_pnb.PHONG) | {"aura", "alpha"}
    for t in _api.DANH_SACH_THE_QUY_TRINH:
        la = [p for p in t["cac_phong"] if p not in that]
        assert not la, f"{t['id']} khai phòng không có thật: {la}"


def test_moi_phong_moi_the_khai_deu_CO_MO_TA():
    """Thiếu mô tả thì bước hiện ra `❓` — đọc được, nhưng là dấu hai bên đã trôi."""
    for t in _api.DANH_SACH_THE_QUY_TRINH:
        thieu = [p for p in t["cac_phong"] if p not in _api.MO_TA_PHONG]
        assert not thieu, f"{t['id']}: {thieu} không có trong MO_TA_PHONG"


def test_so_phong_moi_the_nam_trong_SAN_va_TRAN():
    """Sàn 1 · trần 8, chép tay từ đặc tả. Một lượt `aura` tốn tới 273 giây."""
    for t in _api.DANH_SACH_THE_QUY_TRINH:
        n = len(t["cac_phong"])
        assert DAC_TA_SAN_PHONG <= n <= DAC_TA_TRAN_PHONG, f"{t['id']}: {n} phòng"


def test_alpha_luon_co_aura_dung_TRUOC_trong_cung_the():
    """`alpha` ăn kịch bản của `aura`. Thiếu thì nó không có gì để dựng.

    Ràng buộc này TRƯỚC 06/09 không cần: chuỗi gõ cứng luôn có aura trước
    alpha. Từ lúc thẻ quyết định chuỗi, một lần sửa danh mục là mở được cửa ấy.
    """
    for t in _api.DANH_SACH_THE_QUY_TRINH:
        cp = list(t["cac_phong"])
        if "alpha" in cp:
            assert "aura" in cp[:cp.index("alpha")], (
                f"{t['id']} gọi alpha mà không có aura đứng trước: {cp}")


def test_the_thieu_aura_ma_goi_alpha_thi_KHONG_duoc_bao_PASS(phong_gia):
    """Ca đối chứng cho bài trên: nếu lọt lưới thì chuỗi phải GÃY, không PASS.

    Cửa danh mục bắt ở tầng test; đây kiểm cái lưới thứ hai — lúc chạy thật.
    """
    goc = _api.DANH_SACH_THE_QUY_TRINH
    try:
        _api.DANH_SACH_THE_QUY_TRINH = list(goc) + [
            {"id": "the_alpha_mo_coi", "cac_phong": ["alpha", "gamma"],
             "the_loai": "truyen"}]
        d, goi = _chay(phong_gia, preset_id="the_alpha_mo_coi")
        assert "alpha" not in goi, f"alpha chạy mà không có kịch bản: {goi}"
        assert d["status"] != "PASS", d["thong_diep"]
    finally:
        _api.DANH_SACH_THE_QUY_TRINH = goc


# ---------------------------------------------------------------------------
# DANH MỤC API PHẢI KHAI ĐÚNG CHUỖI SẼ CHẠY

def test_so_do_trong_API_danh_muc_KHOP_chuoi_CHAY_THAT(phong_gia):
    """So `so_do` với phòng ĐƯỢC GỌI THẬT, không so hai công thức với nhau.

    So `so_do` với `cac_phong` thì cả hai cùng suy ra từ một trường — hai vế
    cùng đổi, cửa mù. Vế bên kia phải là HÀNH VI.
    """
    r = asyncio.run(_api.api_danh_sach_the_quy_trinh(_Req({})))
    d = _json.loads(r.body.decode("utf-8"))
    so_do = {t["id"]: [b["phong_id"] for b in t["so_do"]] for t in d["presets"]}

    assert [b["phong_id"] for b in d["so_do_mac_dinh"]] \
        == list(DAC_TA_CHUOI_MAC_DINH)
    assert len(so_do) == len(_api.DANH_SACH_THE_QUY_TRINH)

    for the in _api.DANH_SACH_THE_QUY_TRINH:
        _, goi = _chay(phong_gia, preset_id=the["id"])
        assert so_do[the["id"]] == goi, (
            f"{the['id']}: màn hình sẽ vẽ {so_do[the['id']]} còn máy chạy {goi}")


def test_so_do_mang_du_chu_de_ve_MOT_o_tren_man_hinh():
    """Thiếu một trường thì ô hiện ra rỗng — im lặng, nên khó bắt hơn nổ."""
    r = asyncio.run(_api.api_danh_sach_the_quy_trinh(_Req({})))
    d = _json.loads(r.body.decode("utf-8"))
    for t in d["presets"]:
        for b in t["so_do"]:
            for truong in ("phong_id", "ten", "bieu_tuong", "ngan"):
                assert b.get(truong), f"{t['id']} · bước {b}: thiếu {truong!r}"
