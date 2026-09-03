# -*- coding: utf-8 -*-
"""`core/viet_truyen.py` — MÁY đếm, model viết.

Ba thứ tệp này canh:

* ngưỡng trong mã khớp ĐẶC TẢ, không khớp chính nó
* phép chấm là hàm THUẦN, đưa văn bản xấu vào được
* ba trạng thái không bị gộp, và số lần thử không bị giấu

Ngưỡng dưới đây CHÉP TAY từ `KY_LUAT_THUC_THI.md` Chương II mục 1b. Không
`import` từ `core.viet_truyen` — bài học tautological 02/09: khẳng định
`(RONG, CAO) == (RONG, CAO)` thì gieo `640, 1136` vẫn xanh, vì hai vế cùng đổi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.viet_truyen import (cat_cho_vua, do_kich_ban, viet_kich_ban,  # noqa: E402
                              _dem, _tach_cau)

# ---- NGUỒN SỰ THẬT ĐỘC LẬP, chép tay từ đặc tả ----
DAC_TA_TU_MIN, DAC_TA_TU_MAX = 215, 250
DAC_TA_CAU_KHAC_MIN = 13
DAC_TA_LAP_TOI_DA = 2
DAC_TA_TRAN_SO_LAN = 3


def _van_ban(so_cau: int, tu_moi_cau: int = 8) -> str:
    """Sinh văn bản có ĐÚNG số câu và ĐÚNG số từ mỗi câu.

    Bản đầu đếm sai phần cố định: `"Cau so 1"` là 3 từ và `"o day."` là 2, tức
    5 từ khung, nhưng tôi trừ 4. Mỗi câu dôi một từ, và `_van_ban(26, 9)` ra 260
    từ thay vì 234 — nằm ngoài cửa sổ 215–250, nên bài "phải ĐẠT" đỏ oan.

    Nhạc cụ đo sai trước khi thứ được đo sai. Có `test_ham_phu_dem_dung_so_tu`
    bên dưới canh đúng chỗ này.
    """
    assert tu_moi_cau >= 6, "cần ít nhất 6 từ để đủ khung câu"
    khung = 5                                  # "Cau so N" (3) + "o day." (2)
    return " ".join(
        f"Cau so {i} " + " ".join("chu" for _ in range(tu_moi_cau - khung)) + " o day."
        for i in range(1, so_cau + 1)
    )


def test_ham_phu_dem_dung_so_tu():
    """Ca đối chứng cho chính nhạc cụ đo — nó sai một lần rồi."""
    for so_cau, tu in ((3, 8), (26, 9), (21, 21)):
        van = _van_ban(so_cau, tu)
        cau = _tach_cau(van)
        assert len(cau) == so_cau, f"muốn {so_cau} câu, ra {len(cau)}"
        assert len(van.split()) == so_cau * tu, (
            f"muốn {so_cau * tu} từ, ra {len(van.split())}")


def test_hang_so_trong_ma_khop_DAC_TA():
    import core.viet_truyen as vt

    assert (vt.SO_TU_MIN, vt.SO_TU_MAX) == (DAC_TA_TU_MIN, DAC_TA_TU_MAX)
    assert vt.SO_CAU_KHAC_MIN == DAC_TA_CAU_KHAC_MIN
    assert vt.LAP_TOI_DA == DAC_TA_LAP_TOI_DA
    assert vt.TRAN_SO_LAN == DAC_TA_TRAN_SO_LAN


def test_tran_tu_moi_cau_la_he_qua_cua_hai_nguong_kia():
    """19,2 không phải số đặt tay — nó là `250 / 13`.

    Lượt trượt duy nhất trong 5 lượt đo 03/09 chết vì đúng chỗ này: 442 từ trong
    21 câu (21 từ/câu). Cắt xuống 237 từ thì chỉ còn 11 câu, dưới ngưỡng 13. Hai
    ràng buộc không thể cùng đúng, và không cách cắt nào cứu được.
    """
    import core.viet_truyen as vt

    assert vt.TRAN_TU_MOI_CAU == DAC_TA_TU_MAX / DAC_TA_CAU_KHAC_MIN
    assert 19.0 < vt.TRAN_TU_MOI_CAU < 19.5


def test_khong_dung_lai_cua_chat():
    """Truyện KHÔNG được đi qua luật tra mạng của chat.

    Đo 03/09: `is_search_request("Kể một câu chuyện HIỆN NAY về...")` trả True —
    một yêu cầu sáng tác bị đem ra máy chủ tìm kiếm, 23–43 giây và đề bài đi ra
    ngoài. Cùng họ với ca `"phiên này"` trong CLAUDE.md.
    """
    nguon = (Path(__file__).resolve().parent.parent / "core" / "viet_truyen.py"
             ).read_text(encoding="utf-8")
    # Bỏ phần chú thích ở đầu tệp — ở đó có nhắc tên để giải thích vì sao tránh.
    than = nguon.split('"""', 2)[-1]
    for cam in ("web_search", "is_search_request", "local_first_gateway",
                "OllamaConfig"):
        assert cam not in than, f"`{cam}` không được xuất hiện trong phần mã"


# ------------------------------------------------------------ phép chấm thuần

def test_cham_bac_so_tu_ngoai_cua_so():
    for so_cau, tu_moi_cau, vi_sao in [(13, 8, "quá ngắn"), (40, 10, "quá dài")]:
        tt, ly, so = do_kich_ban(_van_ban(so_cau, tu_moi_cau))
        assert tt == "KHONG_DAT", f"{vi_sao}: {so}"
        assert any("từ, cần" in l for l in ly), ly


def test_cham_bac_it_cau_khac_nhau():
    """Đề đóng băng cũ của Alpha là MỘT câu lặp 22 lần — đúng ca này."""
    mot_cau = "Kael nhin len bau troi do ruc mot cach rat cham rai va lang le. " * 20
    tt, ly, so = do_kich_ban(mot_cau)
    assert tt == "KHONG_DAT"
    assert any("câu khác nhau" in l or "lặp" in l for l in ly), ly


def test_cham_bac_cau_lap_qua_hai_lan():
    cau = [f"Cau so {i} co dung bay chu o day." for i in range(1, 26)]
    cau[5] = cau[10] = cau[15] = cau[0]           # một câu xuất hiện 4 lần
    tt, ly, so = do_kich_ban(" ".join(cau))
    assert so["lap_nhieu_nhat"] == 4, so
    assert tt == "KHONG_DAT"
    assert any("lặp" in l for l in ly), ly


def test_cham_cho_DAT_khi_dung_chuan():
    """Máy chấm phải chứng minh nó biết nói ĐẠT — không thì mọi 'KHÔNG ĐẠT' vô nghĩa."""
    tt, ly, so = do_kich_ban(_van_ban(26, 9))
    assert tt == "DAT", (ly, so)
    assert DAC_TA_TU_MIN <= so["so_tu"] <= DAC_TA_TU_MAX
    assert so["so_cau_khac"] >= DAC_TA_CAU_KHAC_MIN


def test_khong_do_duoc_KHONG_bi_gop_vao_khong_dat():
    """Ba trạng thái, không gộp thành hai."""
    for van in ("", "   ", "\n\n"):
        tt, ly, so = do_kich_ban(van)
        assert tt == "KHONG_DO_DUOC", f"{van!r} -> {tt}"
        assert ly, "không đo được thì phải NÓI RA lý do"


# ------------------------------------------------------------------- cắt giữa

def test_cat_giu_cau_MO_va_cau_KET():
    """Cắt từ dưới cũng lọt cửa 4/5 y hệt, nhưng video kết thúc lửng.

    Đo 03/09, câu cuối sau khi cắt:
        dưới  "…Sự im lặng giữa hai người không nặng nề mà đầy chất thơ"  (cắt ngang)
        giữa  "…Mỗi giọt mưa rơi xuống đất đều là một lời cầu nguyện"      (kết thật)
    """
    goc = _van_ban(60, 9)
    cau_goc = _tach_cau(goc)
    van, bo = cat_cho_vua(goc)
    cau_moi = _tach_cau(van)

    assert bo > 0, "văn bản 60 câu phải bị cắt bớt"
    assert cau_moi[0] == cau_goc[0], "câu MỞ bị đụng"
    assert cau_moi[-1] == cau_goc[-1], "câu KẾT bị đụng — đây là chỗ cắt-từ-dưới hỏng"
    assert len(" ".join(cau_moi).split()) <= DAC_TA_TU_MAX


def test_cat_khong_dung_toi_van_ban_da_vua():
    van = _van_ban(26, 9)
    ra, bo = cat_cho_vua(van)
    assert bo == 0 and ra == van, "đã vừa rồi thì đừng cắt"


def test_cat_khong_no_tren_van_ban_qua_ngan():
    for van in ("", "Mot cau thoi.", "Cau mot. Cau hai."):
        ra, bo = cat_cho_vua(van)
        assert bo == 0
        assert _tach_cau(ra) == _tach_cau(van)


def test_cat_xong_van_phai_QUA_phep_cham():
    """Cắt cho vừa số từ mà làm rụng mất câu thì vẫn phải bị BÁC.

    Đây đúng lượt trượt 03/09: sau khi cắt nó 237 từ (lọt), nhưng còn 11 câu
    (trượt). Cắt không được phép tự phong là đạt.
    """
    dai_cau = _van_ban(21, 21)                    # 21 từ/câu, quá trần 19,2
    van, _ = cat_cho_vua(dai_cau)
    tt, ly, so = do_kich_ban(van)
    assert tt == "KHONG_DAT", f"cắt xong vẫn phải bác: {so}"
    assert any("câu khác nhau" in l for l in ly), ly


# --------------------------------------------------------------- vòng có trần

class _GiaModel:
    """Thay `_xin_model` để đo vòng lặp mà không phải chờ model 90 giây/lượt."""

    def __init__(self, cac_ban):
        self.cac_ban = list(cac_ban)
        self.so_lan = 0

    def __call__(self, loi, hat):
        self.so_lan += 1
        ban = self.cac_ban[min(self.so_lan - 1, len(self.cac_ban) - 1)]
        if isinstance(ban, Exception):
            raise ban
        return ban, 1.0


def test_dat_ngay_lan_dau_thi_KHONG_thu_them(monkeypatch):
    gia = _GiaModel([_van_ban(26, 9)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "DAT"
    assert kq["so_lan_thu"] == 1, "đạt rồi mà vẫn gọi model tiếp"
    assert gia.so_lan == 1


def test_SO_LAN_THU_khong_bi_giau(monkeypatch):
    """Đạt sau 1 lần và sau 3 lần là hai chuyện khác nhau.

    Cùng luật với sổ phiên phải mang `latency_ms`: đừng in ra một phán quyết mà
    không kèm con số tạo ra nó.
    """
    gia = _GiaModel([_van_ban(5, 8), _van_ban(5, 8), _van_ban(26, 9)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "DAT"
    assert kq["so_lan_thu"] == 3, kq["so_lan_thu"]
    assert len(kq["lan"]) == 3, "phải ghi lại CẢ ba lượt, kể cả hai lượt trượt"
    assert kq["lan"][0]["trang_thai"] == "KHONG_DAT"


def test_khong_qua_TRAN_SO_LAN(monkeypatch):
    gia = _GiaModel([_van_ban(5, 8)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "KHONG_DAT"
    assert gia.so_lan == DAC_TA_TRAN_SO_LAN, f"gọi model {gia.so_lan} lần"
    assert kq["van_ban"] == "", "không đạt thì không được trả văn bản ra"


def test_moi_luot_deu_hong_thi_la_KHONG_DO_DUOC(monkeypatch):
    """Ollama tắt ≠ 'đã đo, không đạt'. Gộp hai cái này là bệnh cũ."""
    gia = _GiaModel([RuntimeError("URLError: connection refused")])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "KHONG_DO_DUOC", kq["trang_thai"]
    assert kq["so_lan_thu"] == DAC_TA_TRAN_SO_LAN


def test_mot_luot_hong_mot_luot_do_duoc_thi_KHONG_phai_khong_do_duoc(monkeypatch):
    """Ca đối chứng: chỉ TẤT CẢ lượt hỏng mới là không đo được."""
    gia = _GiaModel([RuntimeError("mat mang"), _van_ban(5, 8), _van_ban(5, 8)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "KHONG_DAT", kq["trang_thai"]


def test_cau_qua_dai_thi_SINH_LAI_ngay_khong_phi_cong_cat(monkeypatch):
    """21 từ/câu thì cắt kiểu gì cũng trượt — đo trước, đừng cắt rồi mới biết."""
    gia = _GiaModel([_van_ban(21, 21), _van_ban(26, 9)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "DAT"
    assert kq["so_lan_thu"] == 2
    assert any("từ/câu" in l for l in kq["lan"][0]["vi_sao"]), kq["lan"][0]


def test_van_ban_tra_ve_PHAI_qua_duoc_phep_cham(monkeypatch):
    """Vòng lặp không được tự phong ĐẠT cho thứ mà `do_kich_ban` sẽ bác.

    Cùng hình dạng với chỗ mù đã bắt bốn lần ở `phong_alpha.py`: chấm được một
    hàm không chứng minh kết quả của nó đi tới đâu.
    """
    gia = _GiaModel([_van_ban(26, 9)])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")
    assert kq["trang_thai"] == "DAT"
    tt, ly, so = do_kich_ban(kq["van_ban"])
    assert tt == "DAT", f"vòng lặp trả về văn bản mà phép chấm BÁC: {ly}"


def test_tra_ve_ban_DA_CAT_chu_khong_phai_ban_tho(monkeypatch):
    """Bài trên KHÔNG bắt được chuyện này, và gieo lỗi chỉ ra đúng chỗ.

    Gieo `van_ban: van` → `van_ban: tho` mà cả 21 bài vẫn xanh. Lý do: model giả
    ở bài trên trả văn bản ĐÃ VỪA SẴN (234 từ), nên `cat_cho_vua` không đổi gì
    và `van == tho` — phép thay vô hình.

    Lần thứ năm trong ngày cùng một hình dạng: khẳng định trên một đường ĐẠT thì
    không đưa được giá trị xấu vào nhánh cần kiểm. Ở đây phải cho model giả trả
    văn bản QUÁ DÀI, để bản cắt và bản thô khác nhau thật.
    """
    tho = _van_ban(40, 9)                       # 360 từ — quá cửa sổ
    assert len(tho.split()) > DAC_TA_TU_MAX, "văn bản thử phải QUÁ DÀI mới đo được"
    gia = _GiaModel([tho])
    monkeypatch.setattr("core.viet_truyen._xin_model", gia)
    kq = viet_kich_ban("thu")

    assert kq["trang_thai"] == "DAT", kq["lan"]
    assert kq["van_ban"] != tho, "trả về bản THÔ, chưa cắt"
    assert len(kq["van_ban"].split()) <= DAC_TA_TU_MAX
    assert kq["lan"][0]["cau_da_bo"] > 0, "phải ghi lại đã bỏ mấy câu"
    tt, _, _ = do_kich_ban(kq["van_ban"])
    assert tt == "DAT"


def test_dem_dung_tu_moi_cau():
    so = _dem(["Mot hai ba bon.", "Nam sau bay tam chin muoi."])
    assert so["so_tu"] == 10 and so["so_cau"] == 2
    assert so["tu_moi_cau"] == 5.0
