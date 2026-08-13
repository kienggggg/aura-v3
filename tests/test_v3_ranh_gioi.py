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
CUA_VAO = ("aura_chat.py",)

# Toàn bộ AURA v3.  18 file.  Mọi thứ khác trong repo là KHO PHỤ TÙNG của v2:
# vẫn nằm đó, vẫn đọc được, nhưng v3 không được phép với tay sang.
V3 = frozenset({
    "aura_chat.py",
    "core/chat_contract.py",       # hợp đồng Codex chốt ở lượt 003
    "core/chat_runtime.py",        # cổng cloud + sổ phiên JSONL
    "core/chat_service.py",        # một hàm reply(), mọi kênh dùng chung
    "core/doc_so_phien.py",        # "câu thứ 2" — đếm, chứ không đoán
    "core/dong_ho.py",             # AURA từng trả sai ngày 20 hôm, nói chắc nịch
    "core/kiem_tien.py",           # "137.500 đồng/lượng" — sai tiền 1000 lần
    "core/local_first_gateway.py",  # trò làm trước, mượn thầy khi bí
    "core/may_tinh.py",      # AURA nói "khoảng 23 ngày" khi đúng là 22
    "core/nho_lai.py",       # 13/08: hỏi lại dữ kiện lượt 1 ở lượt 15 -> bịa
                             # "biển số 123" trong khi sổ ghi "29AB-123.45"
    "core/paths.py",               # thay core/config.py 1.029 dòng
    "core/redact.py",
    "core/secret_guard.py",        # AURA không đọc mật khẩu ra màn hình
    "core/user_memory.py",         # trí nhớ Markdown Sếp sửa tay được
    "core/web_search.py",          # tra mạng CÓ NGUỒN, fail-closed
    "interface/chat_adapters.py",  # composition root
    "interface/chat_api.py",
    "interface/chat_app.py",
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


def _dong_bao_dong() -> set[str]:
    """Tập đóng của các file v3 thật sự với tới, đi từ cửa vào."""
    tham: set[Path] = set()
    hang_doi = [ROOT / c for c in CUA_VAO]
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
    """Con số này là lời hứa. v2 có 339 file; v3 vượt 20 thì phải hỏi vì sao."""
    assert len(V3) <= 20, f"v3 đã phình lên {len(V3)} file — dừng lại xem lại đi"


def test_config_1029_dong_cua_v2_KHONG_con_trong_v3():
    """Cấu hình đi theo thứ cần nó, không gom vào kho chung.

    `core/config.py` vẫn nằm đó cho v2 dùng, nhưng v3 chạm vào là hỏng luật.
    """
    assert "core/config.py" not in V3
    for ten in sorted(V3):
        nguon = (ROOT / ten).read_text(encoding="utf-8")
        assert "core.config" not in nguon, f"{ten} còn dính core/config.py"
