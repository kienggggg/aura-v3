# -*- coding: utf-8 -*-
"""Bộ test không được ghi vào `data/` thật — và mã sản phẩm phải chịu được việc ấy.

Đo 10/09/2026, chụp cây `data/` trước và sau MỘT lượt bộ đủ:

    tệp MỚI     71   (40 tiến độ · ~30 thư mục `task_*` của aura/alpha)
    tệp BỊ SỬA  57   (`epsilon/test_eps_*` ghi đè mỗi lượt, `beta/thu_beta_*`)
    sổ cái      +55 dòng mỗi lượt

Tích luỹ tới hôm ấy: sổ cái **12.119 dòng**, **9.170 dòng** có yêu cầu `"thử"`;
`data/tien_do/` **8.278 tệp**, chỉ **13 tệp** từ giao diện thật. `/api/status`
đếm sổ ấy ra `tasks_count` cho Sếp xem.

Cơ chế chính ở `tests/conftest.py` — cửa canh CẤP PHIÊN chụp `data/` thật lúc
bắt đầu và so lúc kết thúc. Tệp này canh ba thứ quanh nó.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

TEP_GHI_DU_LIEU = (
    PROJECT_ROOT / "core" / "phong_noi_bo.py",
    PROJECT_ROOT / "core" / "omega.py",
    PROJECT_ROOT / "interface" / "noi_bo_api.py",
)


def _cha(cay: ast.AST) -> dict[int, ast.AST]:
    ra: dict[int, ast.AST] = {}
    for nut in ast.walk(cay):
        for con in ast.iter_child_nodes(nut):
            ra[id(con)] = nut
    return ra


def _co_try_bat_ValueError(nut: ast.AST, cha: dict[int, ast.AST]) -> bool:
    while id(nut) in cha:
        nut = cha[id(nut)]
        if isinstance(nut, ast.Try):
            for h in nut.handlers:
                ten = h.type
                cac = ten.elts if isinstance(ten, ast.Tuple) else [ten]
                if any(isinstance(t, ast.Name) and t.id in ("ValueError", "Exception")
                       for t in cac):
                    return True
    return False


def test_KHONG_con_relative_to_PROJECT_ROOT_nao_tran_trui():
    """Bẫy `relative_to` cắn BỐN lần trong một ngày — sửa cả LOẠI, không từng chỗ.

    `Path.relative_to(PROJECT_ROOT)` NÉM `ValueError` khi tệp nằm ngoài kho.
    Mã sản phẩm đã ngầm giả định mọi dữ liệu nằm dưới `PROJECT_ROOT`; giả định
    ấy chỉ đúng vì chưa ai từng chuyển `DATA_DIR` đi. Lần thứ tư: chuyển nó sang
    thư mục tạm cho bộ test thì **19 bài đỏ** với cùng một `ValueError`.

    Bài này đọc `ast`: mọi lời gọi `.relative_to(PROJECT_ROOT)` trong `core/` và
    `interface/` phải nằm trong một khối `try` bắt `ValueError`.
    """
    tran: list[str] = []
    for tep in sorted((PROJECT_ROOT / "core").glob("*.py")) + sorted(
            (PROJECT_ROOT / "interface").glob("*.py")):
        cay = ast.parse(tep.read_text(encoding="utf-8"))
        cha = _cha(cay)
        for nut in ast.walk(cay):
            if (isinstance(nut, ast.Call)
                    and isinstance(nut.func, ast.Attribute)
                    and nut.func.attr == "relative_to"
                    and any(isinstance(a, ast.Name) and a.id == "PROJECT_ROOT"
                            for a in nut.args)
                    and not _co_try_bat_ValueError(nut, cha)):
                tran.append(f"{tep.relative_to(PROJECT_ROOT).as_posix()}:{nut.lineno}")
    assert not tran, (
        f"{len(tran)} chỗ gọi relative_to(PROJECT_ROOT) không bọc try — "
        f"nổ khi dữ liệu nằm ngoài kho: {tran}")


def test_MOT_goc_du_lieu_khong_con_PROJECT_ROOT_data():
    """Sổ cái từng được khai ở BA nơi, hai nơi tự tính `PROJECT_ROOT / "data"`.

    Tính lại gốc ngay trong mã thì bộ test không chuyển hướng được. Mọi đường
    dữ liệu trong ba tệp ghi phải đi từ `DATA_DIR` của `core/paths.py`. Hỏi
    `ast` (một phép chia `PROJECT_ROOT / "data"`), không dò chữ — chú thích kể
    lại chuyện này có chứa đúng chuỗi ấy.
    """
    con: list[str] = []
    for tep in TEP_GHI_DU_LIEU:
        cay = ast.parse(tep.read_text(encoding="utf-8"))
        for nut in ast.walk(cay):
            if (isinstance(nut, ast.BinOp) and isinstance(nut.op, ast.Div)
                    and isinstance(nut.left, ast.Name)
                    and nut.left.id == "PROJECT_ROOT"
                    and isinstance(nut.right, ast.Constant)
                    and nut.right.value == "data"):
                con.append(f"{tep.name}:{nut.lineno}")
    assert not con, f"còn tự tính PROJECT_ROOT / 'data': {con}"


def test_BA_cho_khai_so_cai_TRO_CUNG_MOT_tep_va_KHONG_phai_tep_that():
    """Kiểm `tests/conftest.py` làm việc thật, không phải tin rằng nó làm.

    Ba nơi khai sổ cái phải trỏ CÙNG một tệp — không thì bài ghi qua cửa này
    rồi đọc qua cửa kia thấy sổ rỗng. Và tệp ấy KHÔNG được là sổ thật: nếu cả
    ba cùng trỏ `data/omega/so_cai.jsonl` thì bài vẫn "khớp nhau" mà sổ thật
    vẫn bị ghi — một phép so bằng mà cả hai vế cùng sai.
    """
    from core import omega, phong_noi_bo
    from interface import noi_bo_api

    ba = {omega.SO_CAI.resolve(), phong_noi_bo.SO_CAI.resolve(),
          noi_bo_api.OMEGA_SO_CAI.resolve()}
    assert len(ba) == 1, f"ba nơi khai sổ cái trỏ {len(ba)} tệp khác nhau: {ba}"
    that = (PROJECT_ROOT / "data" / "omega" / "so_cai.jsonl").resolve()
    assert that not in ba, "bộ test đang trỏ vào SỔ CÁI THẬT"
    for mod in (phong_noi_bo, noi_bo_api):
        assert mod.DATA_DIR.resolve() != (PROJECT_ROOT / "data").resolve(), (
            f"{mod.__name__}.DATA_DIR vẫn là data/ thật")


def test_NGUONG_khop_khoi_dac_ta():
    khoi = re.search(
        r"<!-- CHOT:bo-test-khong-ban-data -->(.*?)"
        r"<!-- /CHOT:bo-test-khong-ban-data -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"),
        re.S)
    assert khoi, "mất khối đặc tả CHOT:bo-test-khong-ban-data"
    hang = dict(re.findall(r"^\| (.+?) \| (.+?) \|$", khoi.group(1), re.M))
    moi = hang.get("tệp mới trong data/ sau một lượt bộ đủ", "")
    sua = hang.get("tệp bị sửa trong data/", "")
    so = hang.get("dòng thêm vào sổ cái", "")
    assert "**0**" in moi and "nền 71" in moi, f"hàng tệp mới: {moi!r}"
    assert "**0**" in sua and "nền 57" in sua, f"hàng tệp sửa: {sua!r}"
    assert "**0**" in so and "nền +55" in so, f"hàng sổ cái: {so!r}"
