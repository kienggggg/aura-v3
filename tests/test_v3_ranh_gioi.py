# -*- coding: utf-8 -*-
"""HÀNG RÀO AURA v3 — thứ duy nhất ngăn v3 phình lại thành v2.

Ngày 10/08/2026 đếm được: AURA v2 có **339 file .py / 47.566 dòng**, với **33
cờ bật-tắt tính năng mà 29 cái đang TẮT**.  Bệnh không phải "code dở" — bệnh là
mọi thứ được xây rồi cắm vào, không thứ nào phải chứng minh mình chạy, và không
thứ nào bị gỡ ra.  `core/config.py` dài **1.029 dòng** trong khi xương sống chat
dùng đúng **một** hằng số của nó.

Nên v3 không bắt đầu bằng việc xoá (Sếp giữ v2 làm kho phụ tùng).  v3 bắt đầu
bằng một DANH SÁCH ĐÓNG và bài test này.  Muốn thêm file vào v3 thì phải sửa
`V3` bên dưới — tức là phải cố ý, phải có người thấy, phải giải thích được.

Cách kiểm cố tình đi từ CỬA VÀO và lần theo `import` thật, không đọc tên thư
mục.  Ai lén `import core.daemon` trong một hàm sâu 5 tầng thì test này vẫn kêu.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Cửa vào của AURA v3.  Chỉ có một.
#
# Từ 19/08 đến 02/09/2026 kho này còn mang cả App Thẻ, và hàng rào KHÔNG canh
# nó: `CUA_VAO` chỉ có `aura_chat.py`, nên 8 tệp / 5.509 dòng của App Thẻ —
# **dài hơn phần được canh** — lớn lên ngoài tầm mắt. Đo được ngày 02/09 bằng
# cách chạy lại phép đo từ hai cửa vào: hai bên không dùng chung tệp mã nào.
#
# App Thẻ nay ở kho riêng: https://github.com/kienggggg/app-the
# Hàng rào của nó là `tests/test_ranh_gioi.py` bên ấy, danh sách đóng 8 tệp,
# trần 10.
CUA_VAO = ("aura_chat.py",)

# Cửa vào THỨ HAI: hệ thống Phòng nội bộ.
#
# Đo 03/09/2026, và bắt được vì phải trả lời câu "tệp mới sẽ nằm ở đâu so với
# hàng rào" — không phải vì đọc lại mã:
#
#     hàng rào đang canh    19 tệp · 5.116 dòng · trần 20
#     KHÔNG được canh        3 tệp · 2.723 dòng · KHÔNG CÓ TRẦN
#         908  core/phong_alpha.py
#       1.009  core/polyglot.py
#         806  interface/noi_bo_api.py
#
# Đúng bệnh đã ghi về App Thẻ: *"dài hơn phần được canh, nằm ngoài, không có gì
# giữ nó khỏi phình"*. Lần đó bắt được bằng cách chạy phép đo từ hai cửa vào;
# lần này cũng thế.
#
# Gộp một danh sách thì trần mất nghĩa: "25 tệp" không nói được bên nào đang
# phình.
CUA_VAO_PHONG = ("interface/noi_bo_api.py",)

# Toàn bộ AURA v3.  19 tệp.  Mọi thứ khác trong repo là KHO PHỤ TÙNG của v2:
# vẫn nằm đó, vẫn đọc được, nhưng v3 không được phép với tay sang.
V3 = frozenset({
    "aura_chat.py",
    "core/chat_contract.py",       # hợp đồng Codex chốt ở lượt 003
    "core/chat_runtime.py",        # cổng cloud + sổ phiên JSONL
    "core/chat_service.py",        # một hàm reply(), mọi kênh dùng chung
    "core/doc_so_phien.py",        # "câu thứ 2" — đếm, chứ không đoán
    "core/dong_ho.py",             # AURA từng trả sai ngày 20 hôm, nói chắc nịch
    "core/kiem_tien.py",     # "137.500 đồng/lượng" — sai tiền 1000 lần
    "core/loai_cau_hoi.py",  # 13/08: "Phạm Xuân Kiên là ai" -> bịa nguyên một
    "core/local_first_gateway.py",  # trò làm trước, mượn thầy khi bí
    "core/may_tinh.py",      # AURA nói "khoảng 23 ngày" khi đúng là 22
    "core/nho_lai.py",       # 13/08: hỏi lại dữ kiện lượt 1 ở lượt 15 -> bịa
    "core/paths.py",               # thay core/config.py 1.029 dòng
    "core/redact.py",
    "core/secret_guard.py",        # AURA không đọc mật khẩu ra màn hình
    "core/user_memory.py",         # trí nhớ Markdown Sếp sửa tay được
    "core/web_search.py",          # tra mạng CÓ NGUỒN, fail-closed
    "interface/chat_adapters.py",  # composition root
    "interface/chat_api.py",
    "interface/chat_app.py",
})

# Hệ thống Phòng nội bộ — chỉ những tệp KHÔNG có trong V3.
#
# Trần 8, không phải 20: phần này nhỏ hơn hẳn và phải giữ cho nó nhỏ. Đang 3.
V3_PHONG = frozenset({
    "core/phong_alpha.py",    # dựng video dọc thật, verifier độc lập
    "core/polyglot.py",
    "core/viet_truyen.py",    # MÁY đếm, model viết — kịch bản cho Alpha
    "interface/noi_bo_api.py",  # /api/dispatch, fail-closed
})

# Hai bên được phép dùng chung ĐÚNG hai tệp này, không hơn.
#
# Đóng đinh danh sách chứ không đếm, vì con số không nói được bên nào lấn: nếu
# `noi_bo_api` bắt đầu `import core.chat_service` thì số vẫn có thể là 2 nếu một
# tệp khác rụng đi. Cùng lý do CLAUDE.md đòi danh sách đóng thay vì trần đơn.
DUNG_CHUNG = frozenset({
    "core/paths.py",       # 19 dòng, gốc đường dẫn
    "core/web_search.py",  # polyglot cần tra mạng
})

# Gói nhà trồng được — `import httpx` thì kệ, `import core.daemon` thì không.
GOI_NHA = {"core", "interface", "factory", "brains", "evolution", "robot",
           "ui", "arena", "skills", "tools", "portfolio", "android"}


def _duong_dan(module: str) -> Path | None:
    ung_vien = (
        ROOT / (module.replace(".", "/") + ".py"),
        ROOT / module.replace(".", "/") / "__init__.py",
    )
    return next((p for p in ung_vien if p.is_file()), None)


def _import_cua(path: Path) -> set[str]:
    cay = ast.parse(path.read_text(encoding="utf-8"))
    ra: set[str] = set()
    for node in ast.walk(cay):
        if isinstance(node, ast.Import):
            ra.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            ra.add(node.module)
            # `from core import user_memory`: tên module nằm ở ALIAS chứ không
            # ở `node.module`.  Bản dò đầu tiên của tôi bỏ sót đúng kiểu này và
            # suýt xoá nhầm trang "AURA nhớ gì về tôi".
            ra.update(f"{node.module}.{alias.name}" for alias in node.names)
    return {m for m in ra if m.split(".")[0] in GOI_NHA}


def _dong_bao_dong(cua_vao: tuple[str, ...] = CUA_VAO) -> set[str]:
    """Tập đóng của các file thật sự với tới, đi từ cửa vào."""
    tham: set[Path] = set()
    hang_doi = [ROOT / c for c in cua_vao]
    while hang_doi:
        hien_tai = hang_doi.pop()
        if hien_tai in tham:
            continue
        tham.add(hien_tai)
        for module in _import_cua(hien_tai):
            tim_thay = _duong_dan(module)
            if tim_thay is not None and tim_thay not in tham:
                hang_doi.append(tim_thay)
    return {p.relative_to(ROOT).as_posix() for p in tham}


def test_v3_khong_voi_tay_sang_kho_phu_tung_v2():
    lan_ra = _dong_bao_dong() - V3
    assert not lan_ra, (
        "AURA v3 vừa với tay sang kho phụ tùng v2: "
        + ", ".join(sorted(lan_ra))
        + ". Muốn mang một mảnh v2 sang thì phải ĐO nó chạy trước, rồi thêm "
        "tên vào V3 trong chính tệp này — không kéo lén qua đường import."
    )


def test_danh_sach_v3_khong_co_ten_chet():
    """Tên trong V3 mà không ai với tới = rác đang tích lại. Đúng bệnh của v2."""
    chet = V3 - _dong_bao_dong()
    assert not chet, (
        "Có tên trong V3 nhưng không cửa nào với tới: " + ", ".join(sorted(chet))
    )


@pytest.mark.parametrize("ten", sorted(V3))
def test_moi_file_v3_deu_ton_tai(ten):
    assert (ROOT / ten).is_file(), f"V3 khai có {ten} nhưng trên đĩa không có"


def test_v3_van_con_nho():
    """Con số này là lời hứa. v2 có 339 tệp; v3 vượt 20 thì phải hỏi vì sao."""
    assert len(V3) <= 20, f"v3 đã phình lên {len(V3)} tệp — dừng lại xem lại đi"


def test_config_1029_dong_cua_v2_KHONG_con_trong_v3():
    """Cấu hình đi theo thứ cần nó, không gom vào kho chung.

    `core/config.py` vẫn nằm đó cho v2 dùng, nhưng v3 chạm vào là hỏng luật.
    """
    assert "core/config.py" not in V3
    for ten in sorted(V3):
        nguon = (ROOT / ten).read_text(encoding="utf-8")
        assert "core.config" not in nguon, f"{ten} còn dính core/config.py"


# ---------------------------------------------------------------------------
# HÀNG RÀO THỨ HAI — hệ thống Phòng nội bộ (03/09/2026)
#
# Vì sao có. Hàng rào trên đi từ MỘT cửa vào là `aura_chat.py`, nên cả hệ thống
# Phòng — 3 tệp, 2.723 dòng — không với tới được từ đó và không ai đếm nó. Cùng
# hình dạng với App Thẻ hồi 19/08–02/09: phần không được canh DÀI HƠN phần được
# canh, và lớn lên ngoài tầm mắt.

def test_he_thong_phong_khong_voi_tay_ra_ngoai():
    lan_ra = _dong_bao_dong(CUA_VAO_PHONG) - V3 - V3_PHONG
    assert not lan_ra, (
        "Hệ thống Phòng vừa với tay sang tệp không ai khai: "
        + ", ".join(sorted(lan_ra))
        + ". Thêm tên vào V3_PHONG trong chính tệp này, đừng kéo lén qua import."
    )


def test_danh_sach_phong_khong_co_ten_chet():
    chet = V3_PHONG - _dong_bao_dong(CUA_VAO_PHONG)
    assert not chet, (
        "Có tên trong V3_PHONG nhưng không cửa nào với tới: " + ", ".join(sorted(chet))
    )


@pytest.mark.parametrize("ten", sorted(V3_PHONG))
def test_moi_file_phong_deu_ton_tai(ten):
    assert (ROOT / ten).is_file(), f"V3_PHONG khai có {ten} nhưng trên đĩa không có"


def test_he_thong_phong_van_con_nho():
    """Trần riêng, 8. Gộp vào trần 20 của chat thì không biết bên nào phình."""
    assert len(V3_PHONG) <= 8, (
        f"hệ thống Phòng đã phình lên {len(V3_PHONG)} tệp — dừng lại xem lại đi"
    )


def test_hai_ben_dung_chung_DUNG_HAI_TEP():
    """Chat và Phòng chỉ được chung `paths.py` và `web_search.py`.

    Đây là cửa quan trọng nhất của cả nhóm này. Hai hệ thống dùng chung càng
    nhiều thì tách ra càng khó, và cái giá ấy không hiện lên ở bất kỳ con số
    tổng nào. Ca đã trả giá: hàng rào App Thẻ 02/09 có đúng một phép gieo là
    "App Thẻ bắt đầu dùng chung tệp với chat", và nó là phép đắt nhất.
    """
    chung = _dong_bao_dong(CUA_VAO) & _dong_bao_dong(CUA_VAO_PHONG)
    assert chung == set(DUNG_CHUNG), (
        f"phần dùng chung đổi: đang là {sorted(chung)}, khai là {sorted(DUNG_CHUNG)}. "
        "Thêm một tệp dùng chung là buộc hai hệ thống chặt hơn — phải cố ý."
    )


def test_phong_KHONG_dung_ruot_cua_chat():
    """Phòng không được với vào xương sống chat.

    `paths.py` (19 dòng) và `web_search.py` là hạ tầng dùng chung được. Nhưng
    `chat_service`, `chat_runtime`, `user_memory`, `nho_lai` là RUỘT của chat —
    Phòng chạm vào là hai hệ thống dính vào nhau.
    """
    RUOT = {"core/chat_service.py", "core/chat_runtime.py", "core/chat_contract.py",
            "core/user_memory.py", "core/nho_lai.py", "core/doc_so_phien.py",
            "interface/chat_api.py", "interface/chat_app.py",
            "interface/chat_adapters.py", "aura_chat.py"}
    cham = _dong_bao_dong(CUA_VAO_PHONG) & RUOT
    assert not cham, (
        "Hệ thống Phòng vừa với vào ruột của chat: " + ", ".join(sorted(cham))
    )


def test_hai_danh_sach_khong_de_ten_lot_khe():
    """Mỗi tệp Phòng với tới phải nằm ở ĐÚNG MỘT danh sách, không phải cả hai."""
    trung = V3 & V3_PHONG
    assert not trung, (
        f"tên nằm ở CẢ HAI danh sách: {sorted(trung)}. V3_PHONG chỉ khai tệp "
        "riêng của Phòng; phần dùng chung khai ở DUNG_CHUNG."
    )
