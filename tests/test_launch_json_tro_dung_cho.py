# -*- coding: utf-8 -*-
"""`.claude/launch.json` trỏ vào mã đã rời kho — chết 8 ngày không ai biết.

Đo 10/09/2026: cả **2/2** cấu hình chạy đều gọi `interface.the_app`, mà App Thẻ
đã tách sang kho `app-the` ngày **02/09/2026**. Bấm chạy thì
`ModuleNotFoundError`, và cửa vào thật của repo — `aura_chat.py`, cổng 8799 —
không có cấu hình nào cả.

Không cửa nào bắt được, vì `launch.json` không phải mã: bộ test không import
nó, hàng rào `V3` không lần tới nó, và nó chỉ hỏng lúc có người bấm.

Cùng họ với ca *"một khả năng có sẵn mà không ai gọi thì bằng không"*, chỉ
ngược chiều: đây là một lối gọi trỏ vào thứ không còn có.

Bài này KHÔNG chạy máy chủ. Nó chỉ hỏi: thứ mà cấu hình bảo chạy có nằm trên
đĩa không, và cổng khai có khớp cổng mặc định của chính mã ấy không.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

CAU_HINH = PROJECT_ROOT / ".claude" / "launch.json"

# Chép TAY từ mã, không import — hai vế phải cãi nhau được.
#   interface/chat_app.py:135    AURA_CHAT_PORT   mặc định 8799
#   interface/noi_bo_app.py:60   AURA_NOI_BO_PORT mặc định 8890
CONG_MAC_DINH = {"aura-chat": 8799, "noi-bo": 8890}


def _cau_hinh() -> list[dict]:
    return json.loads(CAU_HINH.read_text(encoding="utf-8"))["configurations"]


def test_CO_cau_hinh_de_ma_kiem():
    """Danh sách rỗng thì mọi bài dưới xanh vì rỗng — `KHÔNG ĐO ĐƯỢC` đội lốt."""
    assert CAU_HINH.is_file(), "mất .claude/launch.json"
    assert len(_cau_hinh()) >= 2, f"chỉ {len(_cau_hinh())} cấu hình"


@pytest.mark.parametrize("ch", _cau_hinh(), ids=lambda c: c["name"])
def test_moi_cau_hinh_tro_vao_thu_CO_TREN_DIA(ch: dict):
    """`-m goi.mo_dun` phải ra tệp thật; đường tệp thẳng cũng phải ra tệp thật."""
    args = list(ch["runtimeArgs"])
    assert (PROJECT_ROOT / ch["runtimeExecutable"]).is_file(), (
        f"{ch['name']}: không có {ch['runtimeExecutable']}")

    if args[0] == "-m":
        mo_dun = args[1]
        duong = PROJECT_ROOT / (mo_dun.replace(".", "/") + ".py")
        assert duong.is_file(), (
            f"{ch['name']}: `-m {mo_dun}` nhưng không có {duong.name} — "
            "mã đã rời kho mà cấu hình ở lại?")
    else:
        assert (PROJECT_ROOT / args[0]).is_file(), (
            f"{ch['name']}: không có {args[0]}")


@pytest.mark.parametrize("ch", _cau_hinh(), ids=lambda c: c["name"])
def test_cong_khai_KHOP_cong_mac_dinh_cua_ma(ch: dict):
    """Hai chỗ khai cổng thì hai chỗ trôi khỏi nhau được.

    Cấu hình mở trình duyệt ở cổng nó khai; máy chủ nghe ở cổng `--port` hoặc
    mặc định của chính nó. Lệch nhau thì trang trắng, và không ai đoán ra vì
    máy chủ **vẫn chạy đúng**.
    """
    ten = ch["name"]
    if ten not in CONG_MAC_DINH:
        pytest.skip(f"chưa chép tay cổng mặc định cho {ten}")
    args = ch["runtimeArgs"]
    assert ch["port"] == CONG_MAC_DINH[ten], (
        f"{ten}: launch.json khai {ch['port']}, mã mặc định "
        f"{CONG_MAC_DINH[ten]}")
    if "--port" in args:
        assert int(args[args.index("--port") + 1]) == ch["port"], (
            f"{ten}: --port {args[args.index('--port') + 1]} ≠ port "
            f"{ch['port']}")


def test_CONG_MAC_DINH_chep_tay_KHOP_ma_that():
    """Ca đối chứng cho bài trên: số chép tay phải là số mã thật dùng.

    Không có bài này thì `CONG_MAC_DINH` và `launch.json` có thể cùng sai một
    kiểu, và cửa trên vẫn xanh — đúng bẫy tautological đã ghi 02/09.
    """
    doc = {
        "aura-chat": (PROJECT_ROOT / "interface" / "chat_app.py", "AURA_CHAT_PORT"),
        "noi-bo": (PROJECT_ROOT / "interface" / "noi_bo_app.py", "AURA_NOI_BO_PORT"),
    }
    for ten, (tep, bien) in doc.items():
        m = re.search(rf'os\.environ\.get\("{bien}", "(\d+)"\)',
                      tep.read_text(encoding="utf-8"))
        assert m, f"{tep.name}: không tìm thấy mặc định của {bien}"
        assert int(m.group(1)) == CONG_MAC_DINH[ten], (
            f"{tep.name} mặc định {m.group(1)}, bài test chép tay "
            f"{CONG_MAC_DINH[ten]}")
