# -*- coding: utf-8 -*-
"""Công cụ đăng, vòng 0 — `tools/dang_truyen_worker.py` (`CHOT:dang-vong-0`, 14/09/2026).

Chạy trong venv v3, KHÔNG có Playwright: tệp được import mà không cần gói ấy, vì nó chỉ
import Playwright bên trong hàm. Canh ba điều mà một lần sửa vội sẽ phá lặng lẽ.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT
from tools import dang_truyen_worker as w

# Chép TAY: Sếp chỉ trang ngày 14/09; hồ sơ ngoài repo theo `CLAUDE.md` §2.
DAC_TA_GOC_HO_SO = Path(r"F:\aura-dang")
DAC_TA_NEN_TANG = {"wattpad": "www.wattpad.com", "sangtacviet": "sangtacviet.com"}
# Bất kỳ lời gọi nào làm thay đổi trang — vòng 0 bước 1–2 không được có.
LENH_THAO_TAC = {"click", "dblclick", "fill", "type", "press", "check", "uncheck",
                 "select_option", "set_input_files", "tap", "dispatch_event", "evaluate"}


def test_HO_SO_nam_NGOAI_repo_va_dung_goc():
    assert w.GOC_HO_SO == DAC_TA_GOC_HO_SO
    for nt in DAC_TA_NEN_TANG:
        d = w.ho_so(nt)
        assert d.parent == DAC_TA_GOC_HO_SO
        assert PROJECT_ROOT.resolve() not in d.resolve().parents, (
            f"hồ sơ {d} nằm TRONG repo — phiên đăng nhập sẽ bị git đụng tới")


def test_NEN_TANG_dung_hai_trang_Sep_chi():
    assert set(w.NEN_TANG) == set(DAC_TA_NEN_TANG)
    for nt, mien in DAC_TA_NEN_TANG.items():
        for url in w.NEN_TANG[nt].values():
            assert url.startswith(f"https://{mien}/"), (nt, url)


def test_NEN_TANG_LA_thi_NO_khong_doan():
    with pytest.raises(ValueError):
        w.ho_so("wattpad.com")


def _nguon() -> str:
    return (PROJECT_ROOT / "tools" / "dang_truyen_worker.py").read_text(encoding="utf-8")


def _ham(ten: str) -> ast.FunctionDef:
    return next(n for n in ast.walk(ast.parse(_nguon()))
                if isinstance(n, ast.FunctionDef) and n.name == ten)


@pytest.mark.parametrize("ham", ["mo", "mo_chrome", "xem", "_mo_trinh_duyet", "_co_cloudflare",
                                 "tao_thu", "_doc_truyen_thu", "_ghi_truyen_thu", "_dung_truyen_thu"])
def test_VONG_0_KHONG_BAM_GI(ham):
    """Bước 1 là Sếp tự đăng nhập, bước 2 chỉ đọc. Có một lời gọi thao tác là đã vượt vòng 0."""
    goi = {n.func.attr for n in ast.walk(_ham(ham))
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not (goi & LENH_THAO_TAC), f"{ham} gọi {sorted(goi & LENH_THAO_TAC)}"


# Chép TAY từ hai biểu mẫu tạo truyện đọc ngày 14/09.
DAC_TA_O_TAO_THU = {"Tên truyện", "Tác giả/Bút danh", "Thể loại", "Giới thiệu"}      # STV
DAC_TA_O_TAO_THU_WATTPAD = {"Tiêu đề *", "Mô tả * Mô tả"}
# Mỗi hàm tạo truyện: ĐÚNG những nút này, không hơn.
DAC_TA_NUT = {"_tao_stv": ["Tạo truyện"], "_tao_wattpad": ["Hư cấu", "Lưu & Tiếp tục"],
              "ghi_nhap": ["Lưu"]}


@pytest.mark.parametrize("ham,nut", sorted(DAC_TA_NUT.items()))
def test_TAO_THU_chi_bam_dung_nut_duoc_phep(ham, nut):
    than = _ham(ham)
    nguon = _nguon()
    bam = [ast.get_source_segment(nguon, n) for n in ast.walk(than) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "click"]
    assert len(bam) == len(nut), f"{ham} bấm {len(bam)} chỗ, được {len(nut)}: {bam}"
    for chu in nut:
        assert sum(f'"{chu}"' in b for b in bam) == 1, f"{ham}: nút {chu!r} phải bấm đúng một lần — {bam}"
    khac = {n.func.attr for n in ast.walk(than) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)} & (LENH_THAO_TAC - {"click", "fill"})
    assert not khac, f"{ham} gọi {sorted(khac)}"
    assert set(w.TRUYEN_THU) == DAC_TA_O_TAO_THU
    assert set(w.TRUYEN_THU_WATTPAD) == DAC_TA_O_TAO_THU_WATTPAD


def test_GHI_NHAP_hoi_DUNG_TRUYEN_truoc_khi_cham_o_viet():
    """Tài khoản có hai truyện ĐÃ ĐĂNG của Sếp. Gõ nhầm vào đó là sửa truyện thật trước mặt
    người đọc — nên ô viết chỉ được chạm SAU câu hỏi "đây có phải truyện thử không"."""
    than = _ham("ghi_nhap")
    nguon = _nguon()
    hoi = [n.lineno for n in ast.walk(than) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name) and n.func.id == "_dung_truyen_thu"]
    dien = [n for n in ast.walk(than) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == "fill"]
    assert len(dien) == 1, f"ghi_nhap điền {len(dien)} chỗ"
    assert '"Viết truyện của bạn"' in ast.get_source_segment(nguon, dien[0])
    assert hoi and min(hoi) < dien[0].lineno, "ô viết bị chạm trước khi hỏi đúng truyện thử"


def test_KHONG_CO_nhan_KHONG_TAO():
    """Đo 14/09: máy báo "KHONG_TAO" trong khi truyện đã có — chờ chuyển trang 33 s là
    thiếu, và nhãn ấy khẳng định một điều chưa đọc lại. Không chắc thì là KHONG_RO."""
    chuoi = {n.value for n in ast.walk(ast.parse(_nguon()))
             if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "KHONG_TAO" not in chuoi
    assert "KHONG_RO" in chuoi


def test_KHONG_BO_TIM_NUT_nao_mang_chu_Dang_hay_Xuat_ban():
    """Nút phát hành của Wattpad là "Đăng". Chữ ấy trong NỘI DUNG truyện thử là dữ liệu;
    trong đối số của một bộ tìm nút thì là một cú bấm sắp xảy ra."""
    nguon = _nguon()
    tim = [n for n in ast.walk(ast.parse(nguon)) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute)
           and n.func.attr in ("get_by_role", "get_by_text", "get_by_label", "locator", "get_by_title")]
    assert tim, "không thấy bộ tìm nút nào — cửa này dò sai chỗ"
    for n in tim:
        doan = ast.get_source_segment(nguon, n).lower()
        for cam in ("đăng", "xuất bản", "publish"):
            assert cam not in doan, f"bộ tìm nút mang {cam!r}: {doan}"


def test_KHONG_DONG_TOI_NUT_PHAT_HANH():
    """Trên STV "Tạo truyện" và nút phát hành là HAI nút (đọc mã trang 14/09). Vòng 0
    không được có một chữ nào dẫn tới nút thứ hai — kể cả tên hàm JS của nó.

    Dò trong MÃ (chuỗi và tên của cây AST), bỏ chú thích và docstring. Bản đầu dò cả tệp
    và đỏ vì chú thích "không bao giờ xuất bản" — `x in y` lần nữa: chữ nằm trong lời kể,
    không nằm trong lệnh.
    """
    cay = ast.parse(_nguon())
    doc = {id(n.body[0].value) for n in ast.walk(cay)
           if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
           and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    ma = [n.value for n in ast.walk(cay)
          if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc]
    ma += [n.id for n in ast.walk(cay) if isinstance(n, ast.Name)]
    ma += [n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)]
    chu = " ".join(ma).lower()
    assert "tạo truyện" in chu, "máy dò không thấy cả chữ nó phải thấy — dò sai chỗ"
    for cam in ("xuất bản", "xuat ban", "exportbook", "extractbook", "isexport", "publish"):
        assert cam not in chu, f"mã của công cụ có {cam!r}"


def test_MO_CHROME_la_Chrome_thuong_khong_co_co_dieu_khien():
    """Google chỉ cho đăng nhập trên trình duyệt KHÔNG bị điều khiển. Lén thêm cổng gỡ lỗi
    thì vừa hỏng đúng việc ấy, vừa thành trình duyệt bị điều khiển đội lốt Chrome thường."""
    assert w.CHROME == Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    assert set(w.TRINH_DUYET) == set(w.NEN_TANG)
    popen = [n for n in ast.walk(_ham("mo_chrome")) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "Popen"]
    assert len(popen) == 1
    co = [s.value for s in ast.walk(popen[0].args[0])
          if isinstance(s, ast.Constant) and isinstance(s.value, str) and s.value.startswith("--")]
    assert set(co) <= {"--user-data-dir=", "--no-first-run"}, co


def test_TRINH_DUYET_THAT_khong_an_khong_gia():
    """Không chạy ẩn, không truyền cờ giả vân tay — `CLAUDE.md` §2: không né chặn bot."""
    nguon = (PROJECT_ROOT / "tools" / "dang_truyen_worker.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "launch_persistent_context"]
    assert len(goi) == 1
    kw = {k.arg: k.value for k in goi[0].keywords}
    assert isinstance(kw.get("headless"), ast.Constant) and kw["headless"].value is False
    assert not ({"args", "user_agent", "ignore_default_args"} & set(kw)), sorted(kw)
    assert "stealth" not in nguon.lower()
