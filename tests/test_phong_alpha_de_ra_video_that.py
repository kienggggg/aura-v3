# -*- coding: utf-8 -*-
"""Alpha phải đẻ ra video THẬT, và verifier phải biết nói KHÔNG.

VÌ SAO CÓ TỆP NÀY. Đến 02/09/2026 phòng Alpha trả về một storyboard viết sẵn và
khai hai tệp — `storyboard.json` (3.4 KB), `cards_preview.png` (240 KB) — **không
tệp nào tồn tại**, kích thước là chữ gõ tay. Đặc tả thì đã có sẵn và đo được từ
trước, ở `KY_LUAT_THUC_THI.md` Chương II mục 2; thiếu đúng phần mã.

NĂM THỨ ĐÃ CHẠY THỬ TRƯỚC KHI VIẾT DÒNG NÀO (`CLAUDE.md` mục 7 luật 2)::

    Pillow 12.3.0 · ffmpeg 7.1 · blackdetect · astats · silencedetect   CÓ
    STUDIO_FIXTURE.md   924 byte · 154 từ
    MSTTS_V110_viVN_An  CÓ — nhưng `System.Speech` báo KHÔNG, và câu ấy SAI:

        HKLM\\...\\Speech\\Voices\\Tokens            2 giọng, cả hai en-US
        HKLM\\...\\Speech_OneCore\\Voices\\Tokens    4 giọng, CÓ viVN_An

    Giọng có thật, chỉ nằm ở nhánh OneCore mà `System.Speech` không nhìn tới.
    Nếu tin câu báo ấy thì đã kết luận "máy không có giọng tiếng Việt" và đi
    làm một đường vòng không cần thiết.

Lượt chạy thật đầu tiên::

    PASS · 5,2 s · 720×1280 · 60,62 s · peak −3,47 dB · 0 đoạn đen
    6 hiện vật, mỗi tệp một SHA-256 tính từ đĩa

HAI CA ĐỐI CHỨNG, vì "PASS ngay lần đầu" là lúc đáng ngờ nhất:

1. **Verifier có biết nói KHÔNG không.** Dựng bốn video CỐ Ý HỎNG, mỗi cái vi
   phạm đúng một điều kiện. Cả bốn bị bác, mỗi cái đúng lý do của nó.
2. **Chữ trên thẻ có dấu thật không.** Vẽ "nhìn" và "nhin" rồi so bitmap: giống
   hệt nhau nghĩa là phông rụng dấu âm thầm. Đo được: KHÁC nhau, phông
   `segoeui.ttf`. Và soi một khung rút từ video thật: chữ đủ dấu, không ô vuông.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from core.paths import PROJECT_ROOT
from core.phong_alpha import (CAO, DAI_MAX, DAI_MIN, RONG, SO_DOI_CANH_TOI_THIEU,
                              SO_THE_TOI_THIEU, TRAN_TINH_GIAY, _tim_phong,
                              kiem_video, sinh_the_hinh)

# NGUỒN SỰ THẬT ĐỘC LẬP — chép tay từ `KY_LUAT_THUC_THI.md` Chương II mục 2,
# KHÔNG import từ mã đang bị kiểm.
#
# Bản đầu của tệp này khẳng định `(width, height) == (RONG, CAO)` bằng chính
# hằng số mà mã dùng. Gieo `RONG, CAO = 640, 1136` thì cả hai vế cùng đổi và
# cửa VẪN XANH. Đó đúng là "tautological" — phép kiểm đỗ do cấu tạo, không bao
# giờ cãi lại được mã.
DAC_TA_RONG, DAC_TA_CAO = 720, 1280
DAC_TA_DAI_MIN, DAC_TA_DAI_MAX = 55.0, 65.0
DAC_TA_SO_THE_TOI_THIEU = 3
DAC_TA_TRAN_TINH_GIAY = 5.0
DAC_TA_SO_DOI_CANH = 8

CO_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
can_ffmpeg = pytest.mark.skipif(not CO_FFMPEG, reason="máy này không có ffmpeg/ffprobe")


def _lam_video(dich: Path, rong: int, cao: int, giay: int, mau: str, am: str) -> Path:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"color=c={mau}:s={rong}x{cao}:d={giay}",
         "-f", "lavfi", "-i", f"{am}:d={giay}",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(dich)],
        capture_output=True, timeout=300)
    return dich


# ------------------------------------------------- verifier phải biết nói KHÔNG

@can_ffmpeg
def test_verifier_bac_video_sai_kich_thuoc(tmp_path):
    """Ngang thay vì dọc. Video dọc là điều kiện đầu tiên của cả phòng."""
    v = _lam_video(tmp_path / "ngang.mp4", CAO, RONG, 60, "blue", "sine=f=440")
    k = kiem_video(v)
    assert not k["dat"]
    assert any(f"{CAO}×{RONG}" in l for l in k["vi_sao"]), k["vi_sao"]


@can_ffmpeg
def test_verifier_bac_video_qua_ngan(tmp_path):
    v = _lam_video(tmp_path / "ngan.mp4", DAC_TA_RONG, DAC_TA_CAO, 10, "blue", "sine=f=440")
    k = kiem_video(v)
    assert not k["dat"]
    assert any("dài" in l for l in k["vi_sao"]), k["vi_sao"]


def test_hang_so_trong_ma_khop_DAC_TA():
    """Đối chiếu mã với đặc tả, không đối chiếu mã với chính nó."""
    assert (RONG, CAO) == (DAC_TA_RONG, DAC_TA_CAO)
    assert (DAI_MIN, DAI_MAX) == (DAC_TA_DAI_MIN, DAC_TA_DAI_MAX)
    assert SO_THE_TOI_THIEU >= DAC_TA_SO_THE_TOI_THIEU
    assert TRAN_TINH_GIAY == DAC_TA_TRAN_TINH_GIAY
    assert SO_DOI_CANH_TOI_THIEU == DAC_TA_SO_DOI_CANH


@can_ffmpeg
def test_verifier_bac_audio_im_lang(tmp_path):
    """Một luồng audio TỒN TẠI mà im lặng vẫn là hỏng.

    Đây là chỗ dễ lọt nhất: `ffprobe` thấy có luồng audio và báo đủ; chỉ
    `astats` mới biết nó câm.
    """
    v = _lam_video(tmp_path / "im.mp4", RONG, CAO, 60, "blue",
                   "anullsrc=r=44100:cl=mono")
    k = kiem_video(v)
    assert not k["dat"]
    assert any("im lặng" in l for l in k["vi_sao"]), k["vi_sao"]
    assert k["so"]["co_audio"] is True, "có luồng audio thật — chỉ là nó câm"


@can_ffmpeg
def test_verifier_bac_man_hinh_den(tmp_path):
    v = _lam_video(tmp_path / "den.mp4", RONG, CAO, 60, "black", "sine=f=440")
    k = kiem_video(v)
    assert not k["dat"]
    assert any("đen" in l for l in k["vi_sao"]), k["vi_sao"]


def test_verifier_bac_khi_khong_co_tep(tmp_path):
    k = kiem_video(tmp_path / "khong-co-that.mp4")
    assert not k["dat"] and k["vi_sao"]


# ----------------------------------------------------- thẻ hình và dấu tiếng Việt

def test_the_hinh_co_dau_tieng_viet_that():
    """Phông rụng dấu thì hỏng ÂM THẦM — ảnh vẫn ra, chữ vẫn có, chỉ mất dấu.

    Ca đối chứng: vẽ cùng một câu, một bản có dấu một bản không. Bitmap giống
    hệt nhau nghĩa là dấu không tới được mặt ảnh.
    """
    from PIL import Image, ImageDraw

    phong, _ = _tim_phong()

    def ve(chu: str) -> bytes:
        a = Image.new("RGB", (600, 90), (0, 0, 0))
        ImageDraw.Draw(a).text((10, 10), chu, font=phong, fill=(255, 255, 255))
        return a.tobytes()

    assert ve("Kael nhìn lên bầu trời đỏ rực") != ve("Kael nhin len bau troi do ruc"), (
        "phông đang rụng dấu tiếng Việt — thẻ hình sẽ ra chữ không dấu hoặc ô vuông"
    )


def test_sinh_du_the_va_dung_kich_thuoc(tmp_path):
    from PIL import Image

    cards = sinh_the_hinh("Câu một. Câu hai. Câu ba. Câu bốn.", tmp_path, so_the=4)
    assert len(cards) >= DAC_TA_SO_THE_TOI_THIEU, "đặc tả đòi tối thiểu 3 thẻ"
    for c in cards:
        assert c.stat().st_size > 0
        with Image.open(c) as a:
            assert a.size == (DAC_TA_RONG, DAC_TA_CAO), f"{c.name} là {a.size}"


# ------------------------------------------------------------- hiện vật thật

def test_hien_vat_mang_sha256_TINH_TU_DIA(tmp_path):
    """Bản cũ khai `{"name": ..., "size": "3.4 KB"}` — chữ gõ tay, không đường
    dẫn, không băm, không ai kiểm được. Nay mỗi hiện vật phải tự chứng minh."""
    from core.phong_alpha import _hien_vat

    p = tmp_path / "thu.bin"
    p.write_bytes(b"x" * 1234)
    # `_hien_vat` lấy đường dẫn tương đối so với gốc kho -> phải nằm trong kho.
    trong_kho = PROJECT_ROOT / "data" / "alpha" / "_thu_hien_vat"
    trong_kho.mkdir(parents=True, exist_ok=True)
    q = trong_kho / "thu.bin"
    try:
        q.write_bytes(b"x" * 1234)
        hv = _hien_vat(q, "BIN", "thu")
        assert hv["size_bytes"] == 1234
        assert hv["sha256"] == hashlib.sha256(q.read_bytes()).hexdigest()
        assert (PROJECT_ROOT / hv["path"]).is_file(), "đường dẫn phải trỏ vào tệp có thật"
    finally:
        shutil.rmtree(trong_kho, ignore_errors=True)


# --------------------------------------------------- cả dây chuyền, chạy thật

@pytest.mark.slow
@can_ffmpeg
def test_day_chuyen_chay_that_nhung_CHUA_QUA_cua_chat_luong(tmp_path):
    """Trạng thái THẬT hôm nay: dựng được, nhưng chưa đủ hay.

    Bài này TRƯỚC 02/09 chiều khẳng định `trang_thai == "PASS"`. Rồi hai cửa
    chất lượng được thắt vào (`KY_LUAT_THUC_THI.md` Chương II mục 2) và dây
    chuyền RỚT — đúng như dự tính, vì nó đẻ ra bốn ảnh tĩnh mỗi ảnh giữ 15 giây.

    Giữ bài này ở trạng thái `FAIL` là cố ý. Nó nói ra CHÍNH XÁC chặng nào còn
    thiếu, thay vì để một slideshow đội lốt "video đạt chuẩn". Ngày nào dây
    chuyền có chuyển động thật thì bài này phải được sửa cùng lúc — và lúc ấy
    con số ở đây là bằng chứng cho biết nó đã tiến bao xa.
    """
    from core.phong_alpha import dung_video

    kq = dung_video(tmp_path / "ra")
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được trên máy này: {kq['vi_sao']}")

    # 1. Dây chuyền CHẠY được — không phải "chưa chạy".
    assert kq["trang_thai"] == "FAIL", kq["vi_sao"]
    loai = [a["type"] for a in kq["artifacts"]]
    assert loai.count("VIDEO") == 1 and loai.count("AUDIO") == 1
    assert loai.count("IMAGE") >= DAC_TA_SO_THE_TOI_THIEU
    for a in kq["artifacts"]:
        f = Path(a["path"])
        d = f if f.is_absolute() and f.is_file() else (PROJECT_ROOT / a["path"])
        if not d.is_file():
            d = tmp_path / "ra" / a["name"]
        assert d.is_file(), a
        assert hashlib.sha256(d.read_bytes()).hexdigest() == a["sha256"], a["name"]

    # 2. Bốn cửa ĐỊNH DẠNG vẫn đỗ.
    so = kq["kiem"]["so"]
    assert (so["rong"], so["cao"]) == (DAC_TA_RONG, DAC_TA_CAO)
    assert DAC_TA_DAI_MIN <= so["giay"] <= DAC_TA_DAI_MAX, so
    assert so["doan_den"] == 0
    assert so["peak_db"] not in (None, "-inf")

    # 3. Cửa CHẤT LƯỢNG là thứ làm nó rớt, và rớt vì đúng lý do.
    assert so["dung_yen_lau_nhat"] > DAC_TA_TRAN_TINH_GIAY, so
    assert so["doi_canh"] < DAC_TA_SO_DOI_CANH, so
    assert any("đứng yên" in l for l in kq["kiem"]["vi_sao"])
    assert any("slideshow" in l for l in kq["kiem"]["vi_sao"])


def test_don_luot_cu_giu_dung_so_luot(tmp_path):
    """Mỗi lượt dựng để lại ~2,5 MB, và `/api/dispatch` quét cả `data/` HAI LẦN
    mỗi lượt để đếm bằng chứng. Không dọn thì mọi phòng khác chậm dần theo."""
    import time as _t

    from core.phong_alpha import SO_LUOT_GIU, _don_luot_cu

    for i in range(SO_LUOT_GIU + 3):
        d = tmp_path / f"task_{i:02d}"
        d.mkdir()
        (d / "video.mp4").write_bytes(b"x" * 100)
        _t.sleep(0.01)   # để mtime tách nhau, kẻo thứ tự do may rủi

    assert len(list(tmp_path.iterdir())) == SO_LUOT_GIU + 3
    _don_luot_cu(tmp_path)
    con = sorted(d.name for d in tmp_path.iterdir())
    assert len(con) == SO_LUOT_GIU, con
    # Phải giữ lượt MỚI NHẤT, không phải lượt bất kỳ.
    assert con[-1] == f"task_{SO_LUOT_GIU + 2:02d}", con
    assert "task_00" not in con


def test_don_luot_cu_khong_no_khi_chua_co_thu_muc(tmp_path):
    from core.phong_alpha import _don_luot_cu

    assert _don_luot_cu(tmp_path / "chua-ton-tai") == 0


@pytest.mark.slow
@can_ffmpeg
def test_dung_video_CO_GOI_don_luot_cu(tmp_path):
    """Đo cả ĐƯỜNG, không chỉ đo hàm.

    Gieo thử bắt được bản đầu: bỏ hẳn lời gọi `_don_luot_cu` khỏi `dung_video`
    mà cửa vẫn xanh, vì phép kiểm gọi thẳng vào hàm chứ không đi qua dây chuyền.
    """
    import time as _t

    from core.phong_alpha import SO_LUOT_GIU, dung_video

    for i in range(SO_LUOT_GIU + 2):
        d = tmp_path / f"cu_{i:02d}"
        d.mkdir()
        (d / "rac.bin").write_bytes(b"x" * 10)
        _t.sleep(0.01)

    kq = dung_video(tmp_path / "moi")
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")
    assert len(list(tmp_path.iterdir())) <= SO_LUOT_GIU + 1, (
        "dây chuyền không dọn lượt cũ — data/alpha sẽ phình mãi, và "
        "/api/dispatch quét thư mục ấy hai lần mỗi lượt"
    )


# ---------------------------------------------------- cửa CHẤT LƯỢNG, 02/09/2026

@can_ffmpeg
def test_verifier_bac_slideshow_dung_yen_qua_lau(tmp_path):
    """Một ảnh tĩnh giữ nguyên 60 giây qua được CẢ BỐN cửa định dạng.

    Đó chính là thứ Alpha đẻ ra ở bản đầu: 720×1280, 60,62 s, có tiếng, 0 khung
    đen — mà đo ra 3 đoạn đứng yên 14,1 s và bitrate video 30 kb/s.
    """
    v = _lam_video(tmp_path / "tinh.mp4", DAC_TA_RONG, DAC_TA_CAO, 60,
                   "blue", "sine=f=440")
    k = kiem_video(v)
    assert not k["dat"]
    assert any("đứng yên" in l for l in k["vi_sao"]), k["vi_sao"]
    assert k["so"]["dung_yen_lau_nhat"] > DAC_TA_TRAN_TINH_GIAY, k["so"]
    # Bốn cửa ĐỊNH DẠNG vẫn đỗ — đó là lý do phải có cửa chất lượng.
    assert (k["so"]["rong"], k["so"]["cao"]) == (DAC_TA_RONG, DAC_TA_CAO)
    assert k["so"]["doan_den"] == 0
    assert k["so"]["peak_db"] not in (None, "-inf")


@can_ffmpeg
def test_may_dem_doi_canh_KHONG_MU(tmp_path):
    """Ca đối chứng bắt buộc: máy đếm phải phân biệt được tĩnh với động.

    Bản đầu đếm bằng `select='gt(scene,…)',showinfo` và luôn ra **0**, kể cả
    trên video cắt cảnh liên tục — nên "0 lần đổi cảnh" của Alpha có thể chỉ là
    máy đo mù. Ở đây dựng một video 8 màu khác hẳn nhau (7 lần cắt thật) và bắt
    máy đếm phải thấy.
    """
    doan = []
    for i, mau in enumerate(("red", "green", "blue", "yellow",
                             "magenta", "cyan", "white", "orange"), 1):
        p = tmp_path / f"p{i}.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
             "-i", f"color=c={mau}:s={DAC_TA_RONG}x{DAC_TA_CAO}:d=1.5",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             str(p)], capture_output=True, timeout=120)
        assert p.is_file(), f"không dựng được {p.name}"
        doan.append(p)

    ds = tmp_path / "l.txt"
    ds.write_text("\n".join(f"file '{d.name}'" for d in doan) + "\n",
                  encoding="utf-8")
    dong = tmp_path / "dong.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(ds),
         "-f", "lavfi", "-i", "sine=f=440:d=12", "-c:v", "libx264",
         "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac",
         "-shortest", str(dong)],
        cwd=str(tmp_path), capture_output=True, timeout=300)
    assert dong.is_file()

    tinh = _lam_video(tmp_path / "tinh.mp4", DAC_TA_RONG, DAC_TA_CAO, 12,
                      "blue", "sine=f=440")

    n_dong = kiem_video(dong)["so"]["doi_canh"]
    n_tinh = kiem_video(tinh)["so"]["doi_canh"]
    assert n_dong >= 5, (
        f"video 7 lần cắt thật mà máy chỉ đếm {n_dong} — máy đếm đang mù, "
        "nên con số 0 của slideshow không nói lên điều gì"
    )
    assert n_tinh == 0, f"video một màu tĩnh mà đếm ra {n_tinh} lần đổi cảnh"
    assert n_dong > n_tinh


@can_ffmpeg
def test_video_dung_yen_SUOT_khong_duoc_lot(tmp_path):
    """Ca tệ nhất từng LỌT qua cửa.

    `freezedetect` chỉ in `freeze_duration` khi một đoạn đứng yên KẾT THÚC. Video
    đứng yên suốt từ đầu tới cuối thì đoạn ấy không bao giờ kết thúc — đo được:
    video xanh trơn 60 s / 1.500 khung cho **0** dòng `freeze_duration`, còn
    slideshow của Alpha (có đổi thẻ) cho 3 dòng. Chỉ đếm `freeze_duration` là
    bỏ sót đúng thứ tĩnh nhất.
    """
    v = _lam_video(tmp_path / "xanh.mp4", DAC_TA_RONG, DAC_TA_CAO, 60,
                   "blue", "sine=f=440")
    k = kiem_video(v)
    assert not k["dat"]
    assert k["so"]["dung_yen_lau_nhat"] >= 55, (
        f"video tĩnh HOÀN TOÀN mà chỉ đo được {k['so']['dung_yen_lau_nhat']}s "
        "đứng yên — đang bỏ sót đoạn không có điểm kết thúc"
    )
    assert any("đứng yên" in l for l in k["vi_sao"]), k["vi_sao"]
