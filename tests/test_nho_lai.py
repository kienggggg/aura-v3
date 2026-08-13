"""Canh bộ nhớ lại — thứ quyết định AURA nhắc đúng hay bịa.

Một bộ tra SAI còn tệ hơn không có: nó nhét nhầm ngữ cảnh vào, và model nói sai
một cách TỰ TIN vì tưởng mình có căn cứ. Nên số test canh chỗ "phải im" nhiều
ngang chỗ "phải nhớ".
"""
from __future__ import annotations

from core.chat_service import ChatMessage
from core.nho_lai import nho_lai

TAM_NHIN = 4  # nhỏ cho dễ đọc; thật là 24


def _lich_su(*cap: tuple[str, str]) -> tuple[ChatMessage, ...]:
    ra: list[ChatMessage] = []
    for hoi, dap in cap:
        ra.append(ChatMessage("user", hoi))
        ra.append(ChatMessage("assistant", dap))
    return tuple(ra)


XE = "Xe đạp của em màu xanh lá, biển số 29AB-123.45. Nhớ giúp em nhé."


def _day_ra_ngoai_cua_so():
    """Lượt xe đạp ở đầu, rồi 3 lượt khác đẩy nó ra ngoài 4 tin."""
    return _lich_su(
        (XE, "Dạ em nhớ rồi ạ."),
        ("Python là gì", "Ngôn ngữ lập trình."),
        ("Còn Java thì sao", "Cũng là ngôn ngữ."),
        ("Vòng lặp for dùng khi nào", "Khi lặp qua dãy."),
    )


# --------------------------------------------------------------------------- #
# PHẢI NHỚ
# --------------------------------------------------------------------------- #

def test_loi_lai_du_kien_da_roi_khoi_cua_so():
    """Đúng cảnh đo được 13/08: lượt 1 ra ngoài, hỏi lại thì phải lôi về."""
    ra = nho_lai("Xe đạp của em màu gì, biển số bao nhiêu?",
                 _day_ra_ngoai_cua_so(), TAM_NHIN)
    assert ra is not None, "dữ kiện còn trong sổ mà không lôi ra được"
    # Con số phải về NGUYÊN VẸN — đây chính là chỗ AURA từng rút gọn thành "123".
    assert "29AB-123.45" in ra
    assert "xanh lá" in ra
    # Phải nói rõ là lời SẾP nói, không phải AURA tự nhớ.
    assert "SẾP" in ra


def test_lay_ban_MOI_NHAT_khi_du_kien_bi_sua():
    """Dữ kiện được sửa thì bản sau phải đè bản trước."""
    lich_su = _lich_su(
        ("Xe đạp của em màu xanh lá", "Dạ."),
        ("À không, xe đạp của em màu đỏ rồi", "Dạ em cập nhật."),
        ("Python là gì", "Ngôn ngữ."),
        ("Còn Java", "Cũng vậy."),
        ("Vòng lặp for", "Lặp qua dãy."),
    )
    ra = nho_lai("Xe đạp của em màu gì?", lich_su, TAM_NHIN)
    assert ra is not None
    assert "màu đỏ" in ra, "phải lấy bản mới nhất"


# --------------------------------------------------------------------------- #
# PHẢI IM — không chắc thì đừng nhét gì vào
# --------------------------------------------------------------------------- #

def test_im_khi_so_chua_vuot_cua_so():
    """Model còn nhìn thấy hết thì nhắc lại chỉ làm lời dặn dài thêm."""
    lich_su = _lich_su((XE, "Dạ em nhớ rồi ạ."))
    assert nho_lai("Xe đạp của em màu gì?", lich_su, TAM_NHIN) is None


def test_im_khi_cau_hoi_khong_lien_quan():
    """Hỏi chuyện khác thì tuyệt đối không kéo lượt cũ về."""
    assert nho_lai("Thủ đô nước Pháp là gì?",
                   _day_ra_ngoai_cua_so(), TAM_NHIN) is None
    assert nho_lai("Viết hàm Python đảo chuỗi",
                   _day_ra_ngoai_cua_so(), TAM_NHIN) is None


def test_im_khi_chi_trung_tu_rong():
    """"của em", "là gì" có ở mọi câu — trùng chúng không phải là liên quan."""
    assert nho_lai("của em là gì", _day_ra_ngoai_cua_so(), TAM_NHIN) is None


def test_khong_bao_gio_loi_lai_LOI_AURA_DAP():
    """Lời model là ý kiến hạng hai. Lôi lại câu AURA bịa = bịa hai lần."""
    lich_su = _lich_su(
        ("Xe của em thế nào", "Xe đạp của Sếp màu tím, biển 99XY-000.11."),
        ("Python là gì", "Ngôn ngữ."),
        ("Còn Java", "Cũng vậy."),
        ("Vòng lặp for", "Lặp qua dãy."),
    )
    ra = nho_lai("Xe đạp của em màu gì, biển số bao nhiêu?", lich_su, TAM_NHIN)
    if ra is not None:
        assert "màu tím" not in ra and "99XY" not in ra, \
            "đang lôi lại lời AURA đáp, không phải lời Sếp nói"


def test_im_khi_tam_nhin_khong_hop_le():
    assert nho_lai("gì cũng được", _day_ra_ngoai_cua_so(), 0) is None
    assert nho_lai("gì cũng được", _day_ra_ngoai_cua_so(), -5) is None


def test_khong_khop_theo_chuoi_con():
    """Bệnh đắt nhất của repo: "ai" khớp trong "thứ hai"."""
    lich_su = _lich_su(
        ("Mật khẩu wifi nhà em là Hoa2024", "Dạ em nhớ."),
        ("Python là gì", "Ngôn ngữ."),
        ("Còn Java", "Cũng vậy."),
        ("Vòng lặp for", "Lặp qua dãy."),
    )
    # "khau" nằm trong "mat khau", nhưng "khai" thì không được khớp vào đó.
    assert nho_lai("khai báo biến thế nào", lich_su, TAM_NHIN) is None
