# -*- coding: utf-8 -*-
"""PATH nói có, chạy thì không — cửa canh vỏ script trỏ vào hư không.

Đăng ký ở `KY_LUAT_THUC_THI.md` mục *"PATH nói có, chạy thì không"*
(08/09/2026), chép TAY xuống đây.

VÌ SAO CÓ TỆP NÀY. `opencode` nằm trên PATH, `command -v` tìm thấy, chạy thì
báo thiếu tệp: cả thư mục `node_modules/opencode-ai` biến mất, còn lại ba vỏ
script npm trỏ vào hư không. Quét cả thư mục npm toàn cục ngày 08/09: **45 vỏ
script / 15 lệnh, 1/15 trỏ vào hư không**.

Không phải chuyện của một công cụ ngoài lề. `SO_BENH_AN.md` đã có ca *"cùng
mã, cùng đề, hai phán quyết — biến thứ ba là PATH"*: cùng một bản dịch bị bác
từ Git Bash và được PASS từ máy chủ, chỉ vì `bash` có trên PATH ở nơi này mà
không có ở nơi kia. Một lệnh **có trên PATH mà chạy không nổi** là đúng biến
thứ ba ấy, ở dạng khó thấy hơn — vì nó không vắng mặt, nó có mặt và hỏng.

BÀI CHỊU LỰC Ở ĐÂY LÀ CA ĐỐI CHỨNG, KHÔNG PHẢI PHÉP QUÉT. Phép quét chạy trên
máy thật nên hôm nay nó xanh — mà một máy đo hỏng cũng cho ra đúng chữ "xanh"
ấy: regex hỏng thì đọc được 0 vỏ, và "0 vỏ đọc được" đọc y hệt "0 vỏ chết".
Nên `test_MAY_DO_bat_duoc_vo_chet...` dựng sẵn một thư mục tạm có **1 vỏ sống
+ 1 vỏ chết** và đòi máy đo báo đúng **1**. Bài ấy kín, không phụ thuộc máy,
và nó mới là thứ chứng minh phép quét biết đỏ.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Chép TAY từ đặc tả.
DAC_TA_VO_CHET_TOI_DA = 0
DAC_TA_SO_LENH_DOC_DUOC_TOI_THIEU = 3
# Cờ hỏi phiên bản KHÔNG giống nhau giữa các lệnh, và bản đầu bài này gõ
# `--version` cho cả bốn. `ffmpeg`/`ffprobe` nhận `-version` MỘT gạch: đưa hai
# gạch thì chúng in đủ banner phiên bản rồi vẫn báo *Missing argument for
# option '-version'* và trả **mã 1**. Cửa canh đỏ, và thông báo đọc ra như
# "máy Sếp có ffprobe hỏng" — một dương tính giả đổ lỗi cho máy, đúng thứ
# nguy hiểm nhất mà `test_hop_cat_polyglot.py` cũng đã dính một lần.
DAC_TA_LENH_BO_TEST_DUA_VAO = (("node", "--version"), ("npx", "--version"),
                               ("ffmpeg", "-version"), ("ffprobe", "-version"))

# Vỏ script npm trỏ vào gói bằng một đường đi qua `node_modules`. Ba dạng vỏ
# (`sh`, `.cmd`, `.ps1`) viết dấu gạch khác nhau nên nhận cả hai chiều.
_MAU_DICH = re.compile(r"node_modules[/\\]([^\"'\s]+?\.(?:exe|js|cjs|mjs))",
                       re.IGNORECASE)

la_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="KHÔNG ĐO ĐƯỢC: bố cục vỏ script npm này là của Windows")


def _quet_vo(thu_muc: Path) -> dict[str, tuple[int, int]]:
    """Trả `{tên lệnh: (số đích CÒN, tổng số vỏ)}` cho một thư mục bin npm.

    Hàm thuần trên một thư mục — nhờ thế ca đối chứng dựng được một thư mục
    tạm và chấm chính hàm này, thay vì chấm một phiên bản khác của nó.
    """
    nm = thu_muc / "node_modules"
    ra: dict[str, list[int]] = {}
    for p in sorted(thu_muc.iterdir()):
        if not p.is_file() or p.suffix.lower() not in ("", ".cmd", ".ps1"):
            continue
        try:
            noi_dung = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _MAU_DICH.search(noi_dung)
        if not m:
            continue
        dich = nm / m.group(1).replace("\\", "/")
        o = ra.setdefault(p.stem, [0, 0])
        o[1] += 1
        o[0] += int(dich.exists())
    return {k: (v[0], v[1]) for k, v in ra.items()}


def _dung_vo(d: Path, ten: str, goi: str) -> None:
    """Dựng một bộ vỏ script npm giả, đúng ba dạng như npm sinh ra thật."""
    (d / ten).write_text(
        f'exec "$basedir/node_modules/{goi}/bin/{ten}.exe"   "$@"\n',
        encoding="utf-8")
    (d / f"{ten}.cmd").write_text(
        f'"%~dp0\\node_modules\\{goi}\\bin\\{ten}.exe"   %*\n',
        encoding="utf-8")
    (d / f"{ten}.ps1").write_text(
        f'& "$basedir/node_modules/{goi}/bin/{ten}.exe"   $args\n',
        encoding="utf-8")


def test_MAY_DO_bat_duoc_vo_chet_va_KHONG_bao_nham_vo_song(tmp_path):
    """CA ĐỐI CHỨNG, kín hoàn toàn — bài chịu lực của tệp này.

    Hai chiều trong một bài, vì mỗi chiều một mình đều lừa được:

      - chỉ có vỏ chết  -> một máy đo "luôn báo hỏng" cũng xanh
      - chỉ có vỏ sống  -> một máy đo "luôn báo sạch" cũng xanh

    Dựng cả hai cạnh nhau thì không máy đo hằng số nào qua được.
    """
    nm = tmp_path / "node_modules"
    (nm / "goi-song" / "bin").mkdir(parents=True)
    (nm / "goi-song" / "bin" / "song.exe").write_bytes(b"MZ")
    _dung_vo(tmp_path, "song", "goi-song")
    _dung_vo(tmp_path, "chet", "goi-da-bien-mat")   # không tạo thư mục gói

    kq = _quet_vo(tmp_path)

    assert set(kq) == {"song", "chet"}, f"đọc ra {sorted(kq)}"
    assert kq["song"] == (3, 3), f"vỏ SỐNG bị báo nhầm là chết: {kq['song']}"
    assert kq["chet"] == (0, 3), f"vỏ CHẾT không bị bắt: {kq['chet']}"

    chet = [t for t, (con, _) in kq.items() if con == 0]
    assert chet == ["chet"], f"đếm sai số vỏ chết: {chet}"


@la_windows
def test_KHONG_con_vo_script_npm_nao_TRO_VAO_HU_KHONG():
    """Phép quét trên máy thật. Nền 08/09: 1/15 hỏng (`opencode`).

    Thư mục không tồn tại là KHÔNG ĐO ĐƯỢC. Thư mục CÓ vỏ mà đọc ra dưới 3
    lệnh thì **ĐỎ** — máy đo hỏng, không phải máy sạch. Gộp hai thứ ấy làm một
    là đúng cái `CLAUDE.md` cấm.
    """
    d = Path(os.environ.get("APPDATA", "")) / "npm"
    if not d.is_dir():
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: không có thư mục npm toàn cục ({d})")

    kq = _quet_vo(d)
    assert len(kq) >= DAC_TA_SO_LENH_DOC_DUOC_TOI_THIEU, (
        f"chỉ đọc được {len(kq)} lệnh trong {d} — MÁY ĐO HỎNG chứ không phải "
        f"máy sạch (nền 08/09 đọc được 15 lệnh / 45 vỏ script)")

    chet = sorted(t for t, (con, _) in kq.items() if con == 0)
    assert len(chet) <= DAC_TA_VO_CHET_TOI_DA, (
        f"{len(chet)}/{len(kq)} lệnh có trên PATH mà trỏ vào hư không: {chet}"
        f" — `command -v` sẽ tìm thấy chúng rồi chạy mới hỏng. Gỡ vỏ script "
        f"hoặc cài lại gói; đừng để PATH nói dối.")


@pytest.mark.parametrize("lenh,co", DAC_TA_LENH_BO_TEST_DUA_VAO)
def test_LENH_bo_test_dua_vao_TIM_THAY_thi_phai_CHAY_DUOC(lenh, co):
    """Không tìm thấy là KHÔNG ĐO ĐƯỢC. Tìm thấy mà chạy không nổi là ĐỎ.

    Bốn lệnh này là thứ bộ test thật sự gọi: `node`/`npx` cho Remotion,
    `ffmpeg`/`ffprobe` cho video. Bài này không đòi máy phải có chúng — nó chỉ
    cấm trạng thái *có mà hỏng*, vì đó là trạng thái duy nhất đi qua được mọi
    `shutil.which()` trong kho rồi mới gãy giữa chừng.
    """
    duong = shutil.which(lenh)
    if not duong:
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: máy này không có `{lenh}`")

    try:
        p = subprocess.run([duong, co], capture_output=True, timeout=60)
    except OSError as e:
        pytest.fail(f"`{lenh}` có trên PATH ({duong}) nhưng không chạy nổi: "
                    f"{type(e).__name__}: {e}")
    assert p.returncode == 0, (
        f"`{lenh}` có trên PATH ({duong}) nhưng `{co}` trả mã "
        f"{p.returncode}: {p.stderr[:200]!r}")


def test_DAC_TA_path_van_o_lai_tai_lieu():
    """Con số tạo ra luật phải ở lại cùng luật.

    Đọc đúng khối giữa hai neo có tên, không hỏi `cụm chữ có ở đâu đó trong
    tệp 100 KB không` — bài học `x in y` lần thứ mười và mười một sáng nay:
    một bảng ghi phép đo nằm chỗ khác cũng chứa cùng cụm chữ, và cửa xanh
    trong khi lời hứa đã bị xoá.
    """
    from core.paths import PROJECT_ROOT

    spec = (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8")
    m = re.search(r"<!-- CHOT:path-noi-doi -->(.*?)<!-- /CHOT:path-noi-doi -->",
                  spec, re.S)
    assert m, "mất neo CHOT:path-noi-doi trong đặc tả"
    khoi = m.group(1)
    for cum in ("45 vỏ script", "1/15",          # phép đo nền 08/09
                "KHÔNG ĐO ĐƯỢC",                 # vì sao nó mất: không được bịa
                "CA ĐỐI CHỨNG",                  # bài chịu lực
                str(DAC_TA_SO_LENH_DOC_DUOC_TOI_THIEU)):
        assert cum in khoi, f"khối path-noi-doi mất {cum!r}"
