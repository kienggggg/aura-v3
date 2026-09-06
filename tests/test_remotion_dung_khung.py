# -*- coding: utf-8 -*-
"""Bộ dựng Remotion — dựng khung THẬT, và độ dài SUY TỪ MỐC.

VÌ SAO CÓ BỘ DỰNG THỨ HAI (06/09/2026)

`sinh_the_hinh` vẽ ảnh TĨNH bằng PIL rồi ffmpeg chiếu mỗi ảnh một khoảng — mỗi
thẻ là một khung đứng yên, không có gì chuyển động được vì thứ duy nhất tồn tại
là một tệp PNG. Remotion dựng LẠI từng khung bằng React, nên chữ hiện dần và
thanh tiến độ chạy theo đúng mốc đo được.

ĐO TRÊN CHÍNH MÁY NÀY, không GPU rời::

    cài            2m06s · 215 MB · 13.471 tệp · 149 gói cấp 1
    120 khung      76,0s   <- gần hết là chi phí MỘT LẦN: tải + bung Chromium
    480 khung      18,8s
    1440 khung     45,3s   (scratchpad) · 47,7s (trong kho)
    ra             60,05s · 720×1280 · h264 · 4,13 MB

Giấy phép Remotion KHÔNG phải MIT — riêng, miễn phí cho cá nhân và tổ chức ≤ 3
người, được dùng thương mại để làm video, cấm bán lại chính Remotion.

CHƯA THAY BỘ DỰNG CŨ. Chạy song song, chấm bằng cùng bộ cửa, rồi mới quyết.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

RM = PROJECT_ROOT / "remotion"
NGUON = RM / "src"

# Chép TAY từ `KY_LUAT_THUC_THI.md` Chương II mục 2 — KHÔNG đọc từ
# `core.phong_alpha`: gieo đổi hằng số ở đó thì hai vế cùng đổi, cửa vẫn xanh.
DAC_TA_RONG, DAC_TA_CAO, DAC_TA_FPS = 720, 1280, 24


def _co_remotion() -> bool:
    return (RM / "node_modules").is_dir()


def _bo_chu_thich(chu: str) -> str:
    """Bỏ chú thích trước khi soi. CẦN THẬT.

    Bài `test_KHONG_nung_phu_de_thay_cho_srt` đỏ ngay lượt chạy đầu vì chú
    thích trong `TheAlpha.tsx` NHẮC LẠI luật ".srt riêng" để giải thích vì sao
    không nung chữ — đó là chỗ nó NÊN xuất hiện. Hỏi *văn bản chứa chữ gì* thay
    vì *mã làm gì*: đúng bệnh `x in y`, mắc lại lần nữa.
    """
    chu = re.sub(r"/\*.*?\*/", " ", chu, flags=re.S)
    ra = []
    for d in chu.splitlines():
        i = d.find("//")
        while i != -1 and i > 0 and d[i - 1] == ":":
            i = d.find("//", i + 2)
        ra.append(d[:i] if i != -1 else d)
    return "\n".join(ra)


def test_du_tep_nguon_va_KHONG_lot_node_modules_vao_git():
    """215 MB · 13.471 tệp. Một lần `git add -A` là kho phình gấp nhiều lần."""
    for t in ("package.json", "src/index.ts", "src/Root.tsx", "src/TheAlpha.tsx"):
        assert (RM / t).is_file(), f"thiếu {t}"
    bo_qua = (RM / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules" in bo_qua, "`.gitignore` của remotion/ không chặn node_modules"

    r = subprocess.run(["git", "check-ignore", "-q", "remotion/node_modules"],
                       cwd=str(PROJECT_ROOT), capture_output=True)
    assert r.returncode == 0, "git KHÔNG bỏ qua remotion/node_modules"


def test_hang_so_khung_hinh_khop_DAC_TA():
    """Đối chiếu mã với ĐẶC TẢ, không phải với chính nó."""
    chu = (NGUON / "Root.tsx").read_text(encoding="utf-8")
    for ten, gt in (("FPS", DAC_TA_FPS), ("RONG", DAC_TA_RONG), ("CAO", DAC_TA_CAO)):
        m = re.search(rf"export const {ten} = (\d+);", chu)
        assert m, f"không tìm thấy hằng số {ten}"
        assert int(m.group(1)) == gt, f"{ten} = {m.group(1)}, đặc tả {gt}"


def test_do_dai_SUY_TU_MOC_chu_khong_go_cung():
    """Đóng đinh `durationInFrames` là dựng lại đúng phép chia đều vừa gỡ bỏ.

    Cửa này soi CẤU TRÚC; thứ chứng minh là bài dựng thật ở dưới.
    """
    chu = _bo_chu_thich((NGUON / "Root.tsx").read_text(encoding="utf-8"))
    assert "calculateMetadata" in chu, "không suy độ dài từ props"
    # Lấy CẢ BIỂU THỨC tới hết dòng, không cắt ở dấu phẩy đầu tiên: bản đầu của
    # bài này khớp đúng `durationInFrames: Math.max(1` rồi báo là gõ cứng.
    m = re.search(r"durationInFrames: (.+)$", chu, re.M)
    assert m, "không thấy chỗ tính durationInFrames"
    assert "cuoi" in m.group(1) and "FPS" in m.group(1), (
        f"độ dài không tính từ mốc: {m.group(1)}")


def test_KHONG_nung_phu_de_thay_cho_srt():
    """`.srt` RIÊNG là luật của `core/phong_alpha.py`, Remotion không được nới.

    *"Nung vào thì không ai kiểm được bằng máy, còn luồng phụ đề thì `ffprobe`
    đọc ra."* Nên thành phần này chỉ nhận `cau` + `moc`, không nhận đường dẫn
    `.srt` và không tự gắn luồng phụ đề nào.
    """
    chu = _bo_chu_thich((NGUON / "TheAlpha.tsx").read_text(encoding="utf-8"))
    assert ".srt" not in chu, "thành phần đụng tới tệp .srt"

    # SO DANH SÁCH TRƯỜNG, không dò chuỗi `.srt`. Gieo thêm một trường
    # `duongSrt` thì bản đầu của bài này VẪN XANH — tên trường không có dấu
    # chấm nên chuỗi `.srt` không xuất hiện. Hỏi *kiểu này khai những gì* thay
    # vì *văn bản có chứa chữ gì*.
    m = re.search(r"export type Props = \{(.*?)\};", chu, re.S)
    assert m, "không tìm thấy kiểu Props"
    truong = set(re.findall(r"^\s*(\w+)\s*[?:]", m.group(1), re.M))
    assert truong == {"cau", "moc"}, (
        f"Props khai {sorted(truong)}; chỉ được nhận câu chữ và mốc")

    from core.phong_alpha import render_remotion
    import inspect
    ky = inspect.signature(render_remotion)
    assert set(ky.parameters) == {"cau", "moc", "ra"}, (
        f"chữ ký nhận thêm thứ nó không nên nhận: {list(ky.parameters)}")


@pytest.mark.skipif(not _co_remotion(),
                    reason="chưa `npm install` trong remotion/ — KHÔNG ĐO ĐƯỢC")
def test_dung_ra_MP4_THAT_va_so_khung_theo_MOC(tmp_path):
    """Dựng thật một đoạn ngắn rồi hỏi `ffprobe`, không tin mã trả về.

    Mốc cố ý LỆCH NHAU (0,5s và 1,0s) để số khung không thể ra đúng do trùng
    hợp với một phép chia đều nào đó.
    """
    from core.phong_alpha import render_remotion

    moc = [(0.0, 0.5), (0.6, 1.6)]
    ra = tmp_path / "ngan.mp4"
    xong, ly_do = render_remotion(["Câu một có dấu tiếng Việt.", "Câu hai."],
                                  moc, ra)
    assert xong, ly_do
    assert ra.is_file() and ra.stat().st_size > 0

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,nb_frames", "-of", "json", str(ra)],
        capture_output=True, text=True, timeout=120)
    s = json.loads(r.stdout)["streams"][0]
    assert (s["width"], s["height"]) == (DAC_TA_RONG, DAC_TA_CAO), s
    assert int(s["nb_frames"]) == round(moc[-1][1] * DAC_TA_FPS), (
        f"{s['nb_frames']} khung, mốc cuối {moc[-1][1]}s × {DAC_TA_FPS}fps "
        f"= {round(moc[-1][1] * DAC_TA_FPS)} — độ dài không theo mốc")


@pytest.mark.skipif(not _co_remotion(), reason="chưa cài Remotion — KHÔNG ĐO ĐƯỢC")
def test_MOC_DAI_HON_thi_video_DAI_HON(tmp_path):
    """Ca đối chứng: bài trên một mình chưa loại được một hằng số may mắn."""
    from core.phong_alpha import render_remotion

    ra1, ra2 = tmp_path / "a.mp4", tmp_path / "b.mp4"
    assert render_remotion(["Một."], [(0.0, 0.5)], ra1)[0]
    assert render_remotion(["Một."], [(0.0, 1.5)], ra2)[0]

    def _khung(p):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=nb_frames", "-of",
                            "default=nw=1:nk=1", str(p)],
                           capture_output=True, text=True, timeout=120)
        return int(r.stdout.strip())

    assert _khung(ra2) == _khung(ra1) * 3, (
        f"mốc gấp ba mà khung {_khung(ra1)} -> {_khung(ra2)}")


def test_KHONG_them_goi_PYTHON_nao():
    """Remotion là Node. Nó không được kéo theo một dòng nào vào requirements."""
    chu = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    dong = [d.split("#")[0].strip() for d in chu.splitlines()]
    goi = sorted(d for d in dong if d)
    assert all("remotion" not in g.lower() for g in goi), goi
    # TRẦN 2, không phải 3. `libcst==1.9.0` gỡ ngày 06/09/2026 — nó khai
    # `core/the_cst.py`, tệp đã theo App Thẻ sang kho riêng từ 02/09. Để trần 3
    # khi sự thật là 2 là chừa sẵn chỗ cho một lần phình im lặng.
    #
    # Chép TAY từ `CLAUDE.md` mục 1: **2 gói ngoài** (`aiohttp`, `httpx`).
    assert len(goi) <= 2, f"requirements phình lên {len(goi)} dòng: {goi}"
    assert {g.split()[0].split("=")[0] for g in goi} == {"aiohttp", "httpx"}, goi


@pytest.mark.skipif(not _co_remotion(), reason="chưa cài Remotion — KHÔNG ĐO ĐƯỢC")
def test_TRONG_KHE_giu_the_truoc_chu_khong_nhay_ve_THE_CUOI(tmp_path):
    """Mốc có KHE im lặng giữa hai câu. Khe không được làm màn hình nháy.

    Bản đầu để `i = giay < moc[0][0] ? 0 : moc.length - 1`, nên mỗi khe
    `findIndex` trả -1 và màn hình NHÁY SANG THẺ CUỐI — trắng chữ, thanh tiến
    độ rỗng, 12 lần trong một video 60 giây.

    KHÔNG CỬA NÀO CỦA ALPHA BẮT ĐƯỢC: `kiem_video` cho ĐẠT vì nháy 0,76 giây
    thì không đen, không đứng yên. Thấy nó vì mọi cắt cảnh lệch phụ đề đúng
    0,735–0,769s — một độ lệch HẰNG SỐ, bằng chính khe — rồi rút một khung
    trong khe ra NHÌN.

    Bài này đo bằng ẢNH: khung trong khe phải GIỐNG khung cuối câu trước, và
    KHÁC khung của thẻ cuối.
    """
    from core.phong_alpha import render_remotion

    # Ba thẻ, khe 0,5s giữa mỗi cặp. Thẻ cuối cố ý khác hẳn để so được.
    moc = [(0.0, 1.0), (1.5, 2.5), (3.0, 4.0)]
    ra = tmp_path / "khe.mp4"
    xong, ly_do = render_remotion(["Thẻ một.", "Thẻ hai.", "Thẻ ba."], moc, ra)
    assert xong, ly_do

    def _nhan(giay: float) -> bytes:
        """Cắt riêng vùng nhãn "THẺ i/N" ở góc trên trái rồi so BYTE.

        So cả khung thì quá chặt: trong khe thanh tiến độ đã chạy hết, còn ở
        0,9s nó mới 90% — khác vài byte dù thẻ vẫn là thẻ ấy. Bản đầu của bài
        này đỏ oan đúng vì thế. Vùng nhãn mới là thứ trả lời *đang chiếu thẻ
        mấy*.
        """
        p = tmp_path / f"k{giay}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ra), "-ss",
                        str(giay), "-frames:v", "1", "-vf", "crop=320:60:48:64",
                        str(p)], capture_output=True, timeout=180)
        assert p.is_file(), f"không rút được khung ở {giay}s"
        return p.read_bytes()

    trong_cau_1 = _nhan(0.9)      # cuối thẻ 1
    khe_1 = _nhan(1.25)           # giữa khe 1,0 -> 1,5
    trong_cau_2 = _nhan(2.4)      # cuối thẻ 2
    khe_2 = _nhan(2.75)           # giữa khe 2,5 -> 3,0
    the_cuoi = _nhan(3.5)         # giữa thẻ 3

    assert len({trong_cau_1, trong_cau_2, the_cuoi}) == 3, (
        "ba thẻ ra cùng một nhãn — phép đo không phân biệt được gì")
    assert khe_1 != the_cuoi, (
        "khung trong khe mang nhãn thẻ CUỐI — màn hình đang nháy về thẻ cuối")
    assert khe_1 == trong_cau_1, "khe 1 không giữ thẻ 1"

    # PHẢI KIỂM KHE THỨ HAI. Ở khe thứ nhất, "giữ thẻ trước" và "nhảy về thẻ
    # đầu" cho CÙNG kết quả — gieo `i = 0` vô điều kiện thì bản đầu của bài này
    # vẫn xanh. Chỉ từ khe thứ hai trở đi hai hành vi mới tách nhau.
    assert khe_2 == trong_cau_2, (
        "khe 2 không giữ thẻ 2 — nhánh lui đang nhảy về một thẻ cố định")
