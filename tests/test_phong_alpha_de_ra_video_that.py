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
import re
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

def test_so_the_theo_THOI_LUONG_chu_khong_co_dinh():
    """4 thẻ / 60 s thì tối đa 3 lần cắt — không đời nào đạt ngưỡng 8.

    Số thẻ phải bám thời lượng, nếu không thì cửa `đổi cảnh ≥ 8` là bất khả thi
    chứ không phải nghiêm khắc.
    """
    from core.phong_alpha import GIAY_MOI_THE, SO_THE_TOI_THIEU

    for dai in (DAC_TA_DAI_MIN, 60.0, DAC_TA_DAI_MAX):
        n = max(SO_THE_TOI_THIEU, int(round(dai / GIAY_MOI_THE)))
        assert n - 1 >= DAC_TA_SO_DOI_CANH, (
            f"video {dai}s ra {n} thẻ = {n - 1} lần cắt, không đủ "
            f"{DAC_TA_SO_DOI_CANH}"
        )


def test_the_lien_nhau_phai_KHAC_MAU_du_de_may_dem_thay(tmp_path):
    """Bốn thẻ cũ cùng gradient chỉ khác chữ -> `scdet` chấm 0 lần đổi cảnh.

    Đo trên thang xám: thẻ liền nhau phải chênh đủ để không bị coi là một cảnh.
    """
    from PIL import Image, ImageChops, ImageStat

    cards = sinh_the_hinh(" ".join(f"Câu {i}." for i in range(1, 14)),
                          tmp_path, so_the=13)
    lech = []
    for a, b in zip(cards, cards[1:]):
        with Image.open(a) as x, Image.open(b) as y:
            d = ImageChops.difference(x.convert("L"), y.convert("L"))
            lech.append(ImageStat.Stat(d).mean[0])
    assert min(lech) >= 4.0, (
        f"hai thẻ liền nhau chỉ chênh {min(lech):.2f} trên thang xám — "
        "bộ dò cảnh sẽ coi cả video là một cảnh"
    )


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


@pytest.mark.slow
@can_ffmpeg
def test_chuyen_dong_phai_CO_THAT_khong_phai_nho_the_ngan(tmp_path):
    """Cửa 5 giây một mình KHÔNG bắt được việc thiếu chuyển động.

    Gieo thử bắt được: bỏ hẳn `zoompan` (thẻ đứng im hoàn toàn) mà cửa vẫn
    xanh — vì mỗi thẻ chỉ giữ 4,33 s, dưới ngưỡng 5 s. Tức là video có thể lại
    thành slideshow, chỉ cần cắt vụn hơn.

    Nên đòi thêm một tính chất mạnh hơn: giữa hai lần cắt KHÔNG được có đoạn
    đứng yên nào cả. Đo được trên dây chuyền thật: **0,0 s**.
    """
    from core.phong_alpha import dung_video

    kq = dung_video(tmp_path / "ra")
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")
    assert kq["kiem"]["so"]["dung_yen_lau_nhat"] == 0.0, (
        f"còn {kq['kiem']['so']['dung_yen_lau_nhat']}s đứng yên — thẻ đang tĩnh, "
        "chỉ là chưa đủ dài để cửa 5 giây bắt được"
    )


# ------------------------------------ cửa PHỤ ĐỀ & NHẠC NỀN, 02/09/2026 tối

DAC_TA_LUFS_MIN, DAC_TA_LUFS_MAX = -18.0, -12.0
DAC_TA_CHENH_NHAC_DB = 12.0


def test_hang_so_am_thanh_khop_DAC_TA():
    from core.phong_alpha import CHENH_NHAC_DB, LUFS_MAX, LUFS_MIN

    assert (LUFS_MIN, LUFS_MAX) == (DAC_TA_LUFS_MIN, DAC_TA_LUFS_MAX)
    assert CHENH_NHAC_DB == DAC_TA_CHENH_NHAC_DB


def test_phu_de_khop_so_the_va_khong_chay_qua_phim(tmp_path):
    """Ba ca: đủ dòng · thiếu dòng · chạy quá phim."""
    from core.phong_alpha import kiem_phu_de, lam_phu_de

    doan = [f"Câu {i}." for i in range(1, 14)]
    srt = lam_phu_de(doan, 4.0, tmp_path / "ok.srt")
    k = kiem_phu_de(srt, so_the=13, dai_video=52.0)
    assert k["dat"], k["vi_sao"]
    assert k["so"]["so_dong"] == 13
    assert k["so"]["ket_dong_cuoi"] == 52.0

    thieu = kiem_phu_de(srt, so_the=20, dai_video=52.0)
    assert not thieu["dat"]
    assert any("dòng phụ đề" in l for l in thieu["vi_sao"]), thieu["vi_sao"]

    qua = kiem_phu_de(srt, so_the=13, dai_video=30.0)
    assert not qua["dat"]
    assert any("dài" in l for l in qua["vi_sao"]), qua["vi_sao"]

    assert not kiem_phu_de(tmp_path / "khong-co.srt", 3, 60.0)["dat"]


def test_moc_thoi_gian_srt_dung_dinh_dang():
    """Sai định dạng mốc thì trình phát bỏ qua phụ đề, IM LẶNG."""
    from core.phong_alpha import _mmss

    assert _mmss(0) == "00:00:00,000"
    assert _mmss(4.346) == "00:00:04,346"
    assert _mmss(56.5) == "00:00:56,500"
    assert _mmss(3661.007) == "01:01:01,007"


@can_ffmpeg
def test_verifier_bac_video_KHONG_co_luong_phu_de(tmp_path):
    v = _lam_video(tmp_path / "khong_phude.mp4", DAC_TA_RONG, DAC_TA_CAO, 60,
                   "blue", "sine=f=440")
    k = kiem_video(v)
    assert k["so"]["co_phu_de"] is False
    assert any("phụ đề" in l for l in k["vi_sao"]), k["vi_sao"]


@can_ffmpeg
def test_nhac_nen_la_am_SINH_RA_va_du_nho(tmp_path):
    """Nhạc phải thấp hơn giọng ≥12 dB, và mức ấy phải NUNG VÀO TỆP.

    Bản đầu áp hệ số âm lượng lúc trộn, nên đo tệp nhạc là đo mức CHƯA hạ —
    phép "chênh giọng/nhạc" so sai cặp: báo 9,85 dB trong khi mức thật đi vào
    bản trộn là −52,9 dB, nhỏ tới mức không ai nghe thấy.
    """
    from core.phong_alpha import _lufs, lam_nhac_nen

    nhac, ly_do = lam_nhac_nen(8.0, tmp_path / "nhac.wav")
    assert nhac is not None, ly_do
    assert nhac.stat().st_size > 0
    muc = _lufs(nhac)
    assert muc is not None, "không đo được độ ồn nền nhạc"
    # Giọng đọc đo được −17,04 LUFS. Nền phải thấp hơn thế ít nhất 12 dB.
    assert muc <= -17.04 - DAC_TA_CHENH_NHAC_DB, (
        f"nền nhạc {muc:.1f} LUFS — chưa đủ thấp dưới giọng −17,04"
    )


@pytest.mark.slow
@can_ffmpeg
def test_day_chuyen_qua_CA_TAM_cua(tmp_path):
    """Tám cửa: bốn định dạng · hai chất lượng · phụ đề · độ ồn."""
    from core.phong_alpha import dung_video

    kq = dung_video(tmp_path / "ra")
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")
    assert kq["trang_thai"] == "PASS", kq["vi_sao"]

    so = kq["kiem"]["so"]
    assert so["co_phu_de"] is True
    assert so["so_dong"] >= DAC_TA_SO_DOI_CANH
    assert so["ket_dong_cuoi"] <= so["giay"] + 0.25, so
    assert DAC_TA_LUFS_MIN <= so["lufs_video"] <= DAC_TA_LUFS_MAX, so
    assert so["chenh_giong_nhac_db"] >= DAC_TA_CHENH_NHAC_DB, so

    # bốn cửa ĐỊNH DẠNG
    assert (so["rong"], so["cao"]) == (DAC_TA_RONG, DAC_TA_CAO)
    assert DAC_TA_DAI_MIN <= so["giay"] <= DAC_TA_DAI_MAX, so
    assert so["doan_den"] == 0
    assert so["peak_db"] not in (None, "-inf")
    # hai cửa CHẤT LƯỢNG
    assert so["dung_yen_lau_nhat"] <= DAC_TA_TRAN_TINH_GIAY, so
    assert so["doi_canh"] >= DAC_TA_SO_DOI_CANH, so

    nhan = {a["kind"] for a in kq["artifacts"]}
    assert "srt_theo_the" in nhan and "generated_tone_bed" in nhan, nhan
    assert "tts_onecore" in nhan, "giọng đọc phải là tệp riêng, đo được"

    loai = [a["type"] for a in kq["artifacts"]]
    # HAI video: bản đã nung chữ, và bản chưa nung giữ lại để đối chiếu. Không
    # giữ bản chưa nung thì không cách nào chứng minh chữ đã vào hình.
    assert loai.count("VIDEO") == 2, loai
    assert "chua_nung_phu_de" in {a["kind"] for a in kq["artifacts"]}
    assert so["dai_duoi"] >= DAC_TA_DAI_DUOI_MIN, so
    assert so["dai_tren"] <= DAC_TA_DAI_TREN_MAX, so
    assert loai.count("SUBTITLE") == 1
    # HAI tệp âm thanh: giọng và nhạc. Đo chênh lệch giữa chúng cần cả hai nằm
    # riêng trên đĩa — trộn rồi thì không tách ra được nữa.
    assert loai.count("AUDIO") == 2, loai
    assert loai.count("IMAGE") >= DAC_TA_SO_DOI_CANH, (
        "cần đủ thẻ để có ≥8 lần cắt — 4 thẻ thì tối đa 3 lần"
    )

    # Mọi hiện vật phải tự chứng minh: đường dẫn thật, byte thật, SHA-256 khớp.
    for a in kq["artifacts"]:
        f = Path(a["path"])
        d = f if f.is_absolute() and f.is_file() else (PROJECT_ROOT / a["path"])
        if not d.is_file():
            d = tmp_path / "ra" / a["name"]
        assert d.is_file(), a
        assert hashlib.sha256(d.read_bytes()).hexdigest() == a["sha256"], a["name"]


def test_cham_am_thanh_biet_BAC_khi_so_xau():
    """Đưa SỐ XẤU vào và xem verifier có bác không.

    Gieo lỗi bắt được bản đầu: ba phép chấm nằm rải trong `dung_video`, nên cửa
    canh chỉ khẳng định được "số đo nằm trong khoảng" — không cách nào đưa số
    xấu vào. Bỏ hẳn hai nhánh chấm mà cửa vẫn xanh, HAI LẦN.
    """
    from core.phong_alpha import kiem_am_thanh

    # đạt: giọng −17, nhạc −34 (chênh 17 dB), video −16,9
    assert kiem_am_thanh(-17.04, -33.82, -16.89) == []

    qua_to = kiem_am_thanh(-17.04, -33.82, -8.0)
    assert any("độ ồn" in l for l in qua_to), qua_to
    qua_nho = kiem_am_thanh(-17.04, -33.82, -30.0)
    assert any("độ ồn" in l for l in qua_nho), qua_nho

    at_loi = kiem_am_thanh(-17.04, -20.0, -16.89)
    assert any("át lời" in l for l in at_loi), at_loi
    # Đúng sát ngưỡng thì vẫn phải đạt — ngưỡng là ≥, không phải >.
    assert kiem_am_thanh(-17.04, -17.04 - DAC_TA_CHENH_NHAC_DB, -16.89) == []

    assert kiem_am_thanh(None, -33.82, -16.89), "thiếu số đo phải BÁC, không bỏ qua"
    assert kiem_am_thanh(-17.04, None, -16.89)
    assert kiem_am_thanh(-17.04, -33.82, None)


@can_ffmpeg
def test_render_THAT_SU_tron_nhac_vao_ban_ra(tmp_path):
    """Có tệp nhạc trên đĩa không có nghĩa nhạc đã vào video.

    Gieo lỗi bắt được: bỏ hẳn nhạc khỏi `render` mà cửa vẫn xanh — tệp nhạc vẫn
    được sinh ra và vẫn được đo, chỉ là nó không vào phim.

    HAI KỊCH BẢN ĐO TRƯỚC ĐÓ ĐỀU HỎNG, ghi lại kẻo lặp:

    * Dùng mức thật: nhạc thấp hơn giọng 16,8 dB nên chỉ nâng tổng ~0,09 dB —
      hai bản đọc RA CÙNG MỘT SỐ (−17,52), vì `loudnorm` chỉ trả hai chữ số.
    * Dùng giọng TTS thật với một câu ngắn: audio ra chỉ **2,325 giây**
      (`amix duration=first` + `-shortest`), mà `loudnorm` đo trên 2,3 giây thì
      không tin được. Sine "toàn thang" cũng chỉ đo ra −21,75 LUFS.

    Nên bỏ TTS hẳn: hai nguồn dựng sẵn, dài 10 giây, chênh nhau rõ rệt. Phép
    này chỉ cần trả lời một câu — ĐƯỜNG DÂY CÓ NỐI KHÔNG.
    """
    from core.phong_alpha import _lufs, render

    def tao(ten: str, tan: int, muc: float) -> Path:
        d = tmp_path / ten
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
             "-i", f"sine=frequency={tan}:duration=10",
             "-af", f"volume={muc},aformat=sample_fmts=s16:sample_rates=44100"
                    ":channel_layouts=mono", str(d)],
            capture_output=True, timeout=300)
        assert d.is_file(), ten
        return d

    khe = tao("khe.wav", 300, 0.02)     # đóng vai giọng, rất nhỏ
    to = tao("to.wav", 800, 1.0)        # đóng vai nhạc, rất to
    chenh_nguon = _lufs(to) - _lufs(khe)
    assert chenh_nguon > 20, f"hai nguồn chỉ chênh {chenh_nguon:.1f} dB, chưa đủ rõ"

    cards = sinh_the_hinh("Câu một. Câu hai. Câu ba.", tmp_path, so_the=3)
    ok1, l1 = render(cards, khe, tmp_path / "khong_nhac.mp4", srt=None, nhac=None)
    ok2, l2 = render(cards, khe, tmp_path / "co_nhac.mp4", srt=None, nhac=to)
    assert ok1 and ok2, (l1, l2)

    a, b = _lufs(tmp_path / "khong_nhac.mp4"), _lufs(tmp_path / "co_nhac.mp4")
    assert a is not None and b is not None
    assert b > a + 10.0, (
        f"trộn một nguồn to hơn {chenh_nguon:.0f} dB vào mà độ ồn chỉ đi từ "
        f"{a:.2f} sang {b:.2f} LUFS — nhạc chưa vào phim"
    )


# ---------------------------------------- nung chữ vào hình, 02/09/2026 tối

DAC_TA_DAI_DUOI_MIN = 3.0
DAC_TA_DAI_TREN_MAX = 1.0


def test_hang_so_nung_khop_DAC_TA():
    from core.phong_alpha import CHENH_DAI_DUOI_MIN, CHENH_DAI_TREN_MAX

    assert CHENH_DAI_DUOI_MIN == DAC_TA_DAI_DUOI_MIN
    assert CHENH_DAI_TREN_MAX == DAC_TA_DAI_TREN_MAX


@can_ffmpeg
def test_chenh_dai_phu_de_phan_biet_CO_NUNG_voi_KHONG(tmp_path):
    """Máy không đọc được chữ trên khung, chỉ so được hai khung với nhau.

    Ba ca: cùng một video (không đổi gì) · đổi ở DẢI DƯỚI (giống phụ đề) · đổi
    ở DẢI TRÊN (không phải phụ đề).
    """
    from core.phong_alpha import chenh_dai_phu_de

    goc = _lam_video(tmp_path / "goc.mp4", DAC_TA_RONG, DAC_TA_CAO, 6,
                     "blue", "sine=f=440")

    def ve_dai(ten: str, y: str) -> Path:
        """Vẽ một DẢI đặc, KHÔNG dùng `drawtext`.

        Hai bản trước đều hỏng, ghi lại kẻo lặp:

        * `drawtext` một dòng `fontsize=48`, hộp bó sát -> dải dưới chỉ chênh
          **1,85**, dưới ngưỡng 3,0. Ngưỡng ấy hiệu chuẩn theo phụ đề THẬT (đo
          được 10,37 và 10,63), nên ca đối chứng phải mạnh tương đương; hạ
          ngưỡng cho vừa một ca yếu là chỉnh cân theo đáp án.
        * Thêm `drawbox` vào trước `drawtext` -> ffmpeg gãy hẳn, tệp ra **0
          byte**: bản ffmpeg này KHÔNG có fontconfig
          (*"Cannot load default config file"*), nên `drawtext` không tìm được
          phông mặc định.

        Bộ đo chỉ hỏi *dải nào đổi*, không cần biết đó là chữ hay hộp — nên bỏ
        `drawtext` đi là bỏ một phụ thuộc mong manh, không mất gì.
        """
        d = tmp_path / ten
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(goc),
             "-vf", f"drawbox=x=0:y={y}:w=iw:h=200:color=white@0.85:t=fill",
             "-c:a", "copy", str(d)], capture_output=True, timeout=300)
        assert d.is_file() and d.stat().st_size > 0, ten
        return d

    duoi = ve_dai("duoi.mp4", "ih-260")
    tren = ve_dai("tren.mp4", "60")

    khong_doi = chenh_dai_phu_de(goc, goc, giay=3.0)
    assert khong_doi["dai_duoi"] < DAC_TA_DAI_DUOI_MIN, khong_doi
    assert khong_doi["dai_tren"] <= DAC_TA_DAI_TREN_MAX, khong_doi

    co_nung = chenh_dai_phu_de(goc, duoi, giay=3.0)
    assert co_nung["dai_duoi"] >= DAC_TA_DAI_DUOI_MIN, co_nung
    assert co_nung["dai_tren"] <= DAC_TA_DAI_TREN_MAX, co_nung

    sai_cho = chenh_dai_phu_de(goc, tren, giay=3.0)
    assert sai_cho["dai_tren"] > DAC_TA_DAI_TREN_MAX, (
        f"chữ vẽ ở ĐẦU khung mà dải trên chỉ chênh {sai_cho['dai_tren']} — "
        "phép đo không phân biệt được chỗ"
    )


@pytest.mark.slow
@can_ffmpeg
def test_dung_video_CO_dua_nhac_vao_ban_tron(tmp_path):
    """Chạy `dung_video` HAI lần, khác đúng một biến: có nền nhạc hay không.

    Gieo lỗi bắt được chỗ mù: bỏ hẳn nhạc khỏi lời gọi `render` bên trong
    `dung_video` mà cửa vẫn xanh, vì phép kiểm trước đó gọi thẳng `render`.

    Đo bằng RMS (`astats`, sáu chữ số) chứ không bằng LUFS (hai chữ số): nhạc
    thấp hơn giọng 16,8 dB nên chỉ dịch tổng ~0,2 dB — LUFS làm tròn mất, RMS
    thì thấy.
    """
    import core.phong_alpha as pa

    def rms(v: Path) -> float:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(v), "-af", "astats",
                            "-f", "null", "-"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        m = re.search(r"RMS level dB:\s*(-?[\d.]+)", r.stderr or "")
        assert m, "không đọc được RMS"
        return float(m.group(1))

    ngan = "Một hai ba. Bốn năm sáu. Bảy tám chín. Mười."
    co = pa.dung_video(tmp_path / "co", van_ban=ngan)
    if co["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {co['vi_sao']}")

    goc_lam_nhac = pa.lam_nhac_nen
    try:
        pa.lam_nhac_nen = lambda dai, dich: (None, "tắt cho phép đo")
        khong = pa.dung_video(tmp_path / "khong", van_ban=ngan)
    finally:
        pa.lam_nhac_nen = goc_lam_nhac

    a = rms(tmp_path / "khong" / "video.mp4")
    b = rms(tmp_path / "co" / "video.mp4")
    assert abs(b - a) > 0.05, (
        f"có nhạc và không nhạc cho cùng RMS ({a:.6f} vs {b:.6f} dB) — "
        "`dung_video` không đưa nhạc vào bản trộn"
    )


def test_cham_nung_biet_BAC_khi_so_xau():
    """Đưa SỐ XẤU vào và xem verifier có bác không.

    Gieo lỗi bắt được chỗ mù: bỏ hẳn hai nhánh chấm nung mà cửa vẫn xanh, vì
    bài chạy-thật chỉ khẳng định "số đo nằm trong khoảng" trên một lượt ĐẠT —
    không cách nào đưa số xấu vào. Cùng gốc với chỗ mù ở phần âm thanh.
    """
    from core.phong_alpha import kiem_nung

    assert kiem_nung({"dai_duoi": 10.63, "dai_tren": 0.25}) == []
    # Sát ngưỡng vẫn phải đạt — ngưỡng là ≥ và ≤, không phải > và <.
    assert kiem_nung({"dai_duoi": DAC_TA_DAI_DUOI_MIN,
                      "dai_tren": DAC_TA_DAI_TREN_MAX}) == []

    chua_nung = kiem_nung({"dai_duoi": 0.4, "dai_tren": 0.1})
    assert any("chưa nung" in l for l in chua_nung), chua_nung

    sai_cho = kiem_nung({"dai_duoi": 10.0, "dai_tren": 40.0})
    assert any("không nằm ở chỗ phụ đề" in l for l in sai_cho), sai_cho

    ca_hai = kiem_nung({"dai_duoi": 0.1, "dai_tren": 40.0})
    assert len(ca_hai) == 2, ca_hai

    assert kiem_nung({"dai_duoi": -1.0, "dai_tren": -1.0}), (
        "không rút được khung thì phải BÁC, không được coi là đạt"
    )
    assert kiem_nung({}), "thiếu số đo phải BÁC"


def test_day_chuyen_NGHE_phan_quyet_cua_cham_nung(tmp_path):
    """Bơm một phán quyết BÁC vào `kiem_nung` rồi chạy cả dây chuyền.

    Gieo 03/09/2026 bắt được chỗ mù: đổi `if ly_do_nung:` thành `if False:`
    trong `dung_video` mà cả 30 bài vẫn xanh. Lý do là mọi bài chấm nung đều
    gọi thẳng hàm thuần `kiem_nung(...)` — hàm ấy vẫn trả đúng lý do, nên
    không bài nào nhận ra dây chuyền đã ngừng NGHE nó.

    Cùng họ với hai chỗ mù đã sửa ở phần âm thanh và phần phụ đề: chấm được
    một hàm không có nghĩa là kết quả của hàm ấy đi tới đâu.
    """
    import core.phong_alpha as pa

    goc = pa.kiem_nung
    try:
        pa.kiem_nung = lambda cd: ["gieo: chữ chưa nung vào hình"]
        kq = pa.dung_video(tmp_path / "bom_bac")
    finally:
        pa.kiem_nung = goc

    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")

    assert kq["trang_thai"] == "FAIL", (
        f"chấm nung BÁC mà dây chuyền vẫn {kq['trang_thai']} — "
        "phán quyết của `kiem_nung` không đi tới `trang_thai`"
    )
    assert "gieo: chữ chưa nung vào hình" in kq["vi_sao"], (
        f"lý do bác không lọt ra ngoài: {kq['vi_sao']!r}"
    )

    # Ca đối chứng: KHÔNG bơm gì thì cùng đường ấy phải PASS. Thiếu ca này thì
    # bài trên có thể xanh chỉ vì `dung_video` luôn FAIL trong tmp_path.
    #
    # Cả hai lượt dùng VĂN BẢN MẶC ĐỊNH, không dùng câu ngắn cho nhanh: đo
    # 03/09/2026 thì câu bốn mệnh đề cho bản trộn −29,9 LUFS (trần là −18…−12),
    # nên đối chứng đỏ vì độ ồn chứ không vì chuyện đang xét. Rẻ hơn 2 phút,
    # nhưng đo sai biến.
    sach = pa.dung_video(tmp_path / "khong_bom")
    if sach["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"đối chứng không đo được: {sach['vi_sao']}")
    assert sach["trang_thai"] == "PASS", (
        f"đối chứng phải PASS mới chứng minh được bài trên: {sach['vi_sao']}"
    )
