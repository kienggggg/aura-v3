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

# HAI cửa vào, hai danh sách, hai trần RIÊNG.
#
# Trước 02/09/2026 tệp này chỉ canh `aura_chat.py`. Đo hôm ấy, đi từ hai cửa
# vào theo `import` thật:
#
#     chat  (aura_chat.py)        19 tệp   5.135 dòng
#     App Thẻ (the_app.py)         8 tệp   5.509 dòng
#     DÙNG CHUNG                   0 tệp       0 dòng
#
# Không một tệp nào chung — hai chương trình riêng ở nhờ chung một kho. Và
# phần KHÔNG được canh đã dài hơn phần được canh. Đúng bệnh v3 sinh ra để
# chống, chỉ khác là nó mọc ở phía không ai nhìn.
#
# Gộp hai danh sách làm một thì trần mất nghĩa: 27 tệp không nói được chương
# trình nào đang phình. Nên tách đôi, mỗi bên một trần.
CUA_VAO_CHAT = ("aura_chat.py",)
CUA_VAO_THE = ("interface/the_app.py",)

# Xương sống chat.  19 file.  Mọi thứ khác trong repo là KHO PHỤ TÙNG của v2:
# vẫn nằm đó, vẫn đọc được, nhưng v3 không được phép với tay sang.
V3_CHAT = frozenset({
    "aura_chat.py",
    "core/chat_contract.py",       # hợp đồng Codex chốt ở lượt 003
    "core/chat_runtime.py",        # cổng cloud + sổ phiên JSONL
    "core/chat_service.py",        # một hàm reply(), mọi kênh dùng chung
    "core/doc_so_phien.py",        # "câu thứ 2" — đếm, chứ không đoán
    "core/dong_ho.py",             # AURA từng trả sai ngày 20 hôm, nói chắc nịch
    "core/kiem_tien.py",     # "137.500 đồng/lượng" — sai tiền 1000 lần
    "core/loai_cau_hoi.py",  # 13/08: "Phạm Xuân Kiên là ai" -> bịa nguyên một
                             # tiểu sử. Tự nghĩ / tra cứu / sáng tác.
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

# App Thẻ.  8 file.  Cửa vào `interface/the_app.py`, KHÔNG dùng chung tệp nào
# với chat — kể cả `core/paths.py`.
V3_THE = frozenset({
    "interface/the_app.py",        # cửa vào; có nhánh thông dịch cho bản .exe
    "interface/the_api.py",        # 1.513 dòng — phần dài nhất của App Thẻ
    "core/the_cst.py",             # bộ đọc Python -> thẻ mà app THẬT SỰ gọi
    "core/the_v1.py",              # dựng lệnh chạy, biết mình có bị đóng băng
    "core/lat_nguoc.py",           # gieo lỗi rồi xem test có đỏ không
    "core/trace_runtime.py",       # dò dòng dữ liệu
    "core/soi_model.py",           # cổng Ollama; không có Ollama thì nói thẳng
    "core/nhip_thuc_thi.py",
})

# Giữ tên cũ cho chỗ khác đọc tới.
V3 = V3_CHAT | V3_THE
CUA_VAO = CUA_VAO_CHAT + CUA_VAO_THE

# (tên, cửa vào, danh sách đóng, trần) — trần là LỜI HỨA, vượt thì phải hỏi
# vì sao, không phải nới ra cho xanh.
CHUONG_TRINH = (
    ("chat", CUA_VAO_CHAT, V3_CHAT, 20),
    ("App Thẻ", CUA_VAO_THE, V3_THE, 10),
)

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


def _dong_bao_dong(cua_vao=CUA_VAO) -> set[str]:
    """Tập đóng của các file v3 thật sự với tới, đi từ cửa vào."""
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


@pytest.mark.parametrize("ten, cua_vao, danh_sach", [(a, b, c) for a, b, c, _ in CHUONG_TRINH])
def test_khong_voi_tay_sang_kho_phu_tung_v2(ten, cua_vao, danh_sach):
    lan_ra = _dong_bao_dong(cua_vao) - danh_sach
    assert not lan_ra, (
        f"{ten} vừa với tay sang kho phụ tùng v2: "
        + ", ".join(sorted(lan_ra))
        + ". Muốn mang một mảnh v2 sang thì phải ĐO nó chạy trước, rồi thêm "
        "tên vào danh sách trong chính tệp này — không kéo lén qua import."
    )


@pytest.mark.parametrize("ten, cua_vao, danh_sach", [(a, b, c) for a, b, c, _ in CHUONG_TRINH])
def test_danh_sach_khong_co_ten_chet(ten, cua_vao, danh_sach):
    """Tên khai mà không ai với tới = rác đang tích lại. Đúng bệnh của v2."""
    chet = danh_sach - _dong_bao_dong(cua_vao)
    assert not chet, (
        f"Có tên trong danh sách {ten} nhưng không cửa nào với tới: "
        + ", ".join(sorted(chet))
    )


def test_hai_chuong_trinh_van_la_hai():
    """Đo 02/09/2026: 0 tệp dùng chung. Không cấm dùng chung — nhưng ngày nào
    hai bên bắt đầu chia nhau một tệp thì phải có người THẤY, vì lúc ấy hai
    trần riêng không còn nói đúng nữa."""
    chung = _dong_bao_dong(CUA_VAO_CHAT) & _dong_bao_dong(CUA_VAO_THE)
    assert not chung, (
        "chat và App Thẻ bắt đầu dùng chung: " + ", ".join(sorted(chung))
        + ". Không sai, nhưng phải cố ý: sửa lời hứa trong tệp này trước."
    )


@pytest.mark.parametrize("ten", sorted(V3))
def test_moi_file_v3_deu_ton_tai(ten):
    assert (ROOT / ten).is_file(), f"V3 khai có {ten} nhưng trên đĩa không có"


@pytest.mark.parametrize("ten, danh_sach, tran", [(a, c, d) for a, _, c, d in CHUONG_TRINH])
def test_van_con_nho(ten, danh_sach, tran):
    """Con số này là lời hứa. v2 có 339 file; vượt trần thì phải hỏi vì sao,
    không phải nới trần cho xanh."""
    assert len(danh_sach) <= tran, (
        f"{ten} đã phình lên {len(danh_sach)} file (trần {tran}) — dừng lại xem lại đi"
    )


def test_config_1029_dong_cua_v2_KHONG_con_trong_v3():
    """Cấu hình đi theo thứ cần nó, không gom vào kho chung.

    `core/config.py` vẫn nằm đó cho v2 dùng, nhưng v3 chạm vào là hỏng luật.
    """
    assert "core/config.py" not in V3
    for ten in sorted(V3):
        nguon = (ROOT / ten).read_text(encoding="utf-8")
        assert "core.config" not in nguon, f"{ten} còn dính core/config.py"
