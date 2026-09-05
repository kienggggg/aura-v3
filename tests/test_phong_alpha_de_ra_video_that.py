# -*- coding: utf-8 -*-
"""Alpha phải đẻ ra video THẬT, và verifier phải biết nói KHÔNG.

VÌ SAO CÓ TỆP NÀY. Đến 02/09/2026 phòng Alpha trả về một storyboard viết sẵn và
khai hai tệp — `storyboard.json` (3.4 KB), `cards_preview.png` (240 KB) — **không
tệp nào tồn tại**, kích thước là chữ gõ tay. Đặc tả thì đã có sẵn và đo được từ
trước, ở `KY_LUAT_THUC_THI.md` Chương II mục 2; thiếu đúng phần mã.

NĂM THỨ ĐÃ CHẠY THỬ TRƯỚC KHI VIẾT DÒNG NÀO (`CLAUDE.md` mục 7 luật 2)::

    Pillow 12.3.0 · ffmpeg 7.1 · blackdetect · astats · silencedetect   CÓ
    STUDIO_FIXTURE.md   1403 byte · 235 từ · 15 câu khác nhau
                        (bản 924 byte / 154 từ / MỘT câu lặp 22 lần giữ ở
                         STUDIO_FIXTURE_LAP.md làm ca đối chứng âm)
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


# ---------------------------------------------------------------------------
# CỬA NỘI DUNG (03/09/2026)
#
# Ba con số dưới đây CHÉP TAY từ `KY_LUAT_THUC_THI.md`, không `import` từ
# `core.phong_alpha`. Lý do đã trả giá ngày 02/09: bài kiểm khung hình khẳng
# định `(width, height) == (RONG, CAO)` bằng CHÍNH hằng số mà mã dùng, nên gieo
# `RONG, CAO = 640, 1136` thì hai vế cùng đổi và cửa vẫn xanh.
DAC_TA_TI_LE_KHAC_MIN = 0.80
DAC_TA_TI_LE_LAP_MAX = 0.25
DAC_TA_QUANG_CAM_MAX = 2.0


def test_hang_so_cua_noi_dung_khop_dac_ta():
    import core.phong_alpha as pa

    assert pa.TI_LE_PHU_DE_KHAC_MIN == DAC_TA_TI_LE_KHAC_MIN
    assert pa.TI_LE_KHOI_LAP_MAX == DAC_TA_TI_LE_LAP_MAX
    assert pa.QUANG_CAM_TOI_DA_GIAY == DAC_TA_QUANG_CAM_MAX


def test_probe_do_cam_phai_THAP_hon_nguong_cham():
    """Đặt probe bằng ngưỡng chấm thì mọi quãng ngắn hơn bị GIẤU.

    Đã mắc đúng lỗi này với `freezedetect` ngày 02/09: probe `d` đặt bằng ngưỡng
    5,0 s nên không đoạn nào ngắn hơn lộ ra, và bảng đo đọc thành "sạch".
    """
    import core.phong_alpha as pa

    assert pa.DO_CAM_PROBE_GIAY < pa.QUANG_CAM_TOI_DA_GIAY, (
        f"probe {pa.DO_CAM_PROBE_GIAY}s không được ≥ ngưỡng chấm "
        f"{pa.QUANG_CAM_TOI_DA_GIAY}s"
    )


def test_khoi_phu_de_bo_so_thu_tu_va_moc_gio():
    from core.phong_alpha import khoi_phu_de

    srt = ("1\n00:00:00,000 --> 00:00:04,000\nCâu một.\n\n"
           "2\n00:00:04,000 --> 00:00:08,000\nCâu hai\ndòng tiếp.\n")
    assert khoi_phu_de(srt) == ["Câu một.", "Câu hai dòng tiếp."]
    assert khoi_phu_de("") == []


def test_cham_lap_phu_de_bac_kich_ban_mot_cau():
    """Đề đóng băng CŨ là một câu lặp 22 lần → 1/13 khối khác nhau."""
    from core.phong_alpha import kiem_lap_phu_de

    assert not kiem_lap_phu_de([f"Câu {i}." for i in range(13)]), (
        "13 khối khác nhau phải ĐẠT"
    )
    mot_cau = kiem_lap_phu_de(["Kael nhìn lên bầu trời đỏ rực."] * 13)
    assert any("khác nhau" in l for l in mot_cau), mot_cau
    assert any("một khối chiếm" in l for l in mot_cau), mot_cau

    # Điệp khúc lặp 2 lần trong 13 khối vẫn phải lọt — ngưỡng chừa chỗ cho nó.
    diep_khuc = [f"Câu {i}." for i in range(12)] + ["Câu 0."]
    assert not kiem_lap_phu_de(diep_khuc), diep_khuc

    # Nhưng lặp tới 4/13 (0,308 > 0,25) thì bác.
    lan_at = [f"Câu {i}." for i in range(10)] + ["Câu 0."] * 3
    assert kiem_lap_phu_de(lan_at), "một khối chiếm 4/13 phải BÁC"

    assert kiem_lap_phu_de([]), "không có khối nào thì phải BÁC, không phải ĐẠT"


def test_cham_quang_cam_tach_ba_trang_thai():
    from core.phong_alpha import kiem_quang_cam

    assert not kiem_quang_cam(0.77), "khoảng nghỉ tự nhiên dài nhất phải ĐẠT"
    assert not kiem_quang_cam(0.0)
    assert kiem_quang_cam(15.23), "15,23s đệm im lặng phải BÁC"
    assert kiem_quang_cam(DAC_TA_QUANG_CAM_MAX + 0.01), "quá ngưỡng phải BÁC"
    khong_do = kiem_quang_cam(-1.0)
    assert any("không đo được" in l for l in khong_do), (
        f"không đo được phải nói RA, không được gộp vào đạt: {khong_do}"
    )


def test_day_chuyen_NGHE_phan_quyet_cua_hai_cua_noi_dung(tmp_path):
    """Bơm phán quyết BÁC vào từng cửa nội dung rồi chạy CẢ dây chuyền.

    Không có bài này thì hai bài chấm ở trên vẫn xanh dù `dung_video` ngừng nghe
    chúng — đúng chỗ mù đã bắt được ngày 03/09 với `kiem_nung`: gieo
    `if ly_do_nung:` → `if False:` mà cả 30 bài vẫn xanh, vì mọi bài đều gọi
    thẳng hàm thuần.
    """
    import core.phong_alpha as pa

    for ten_ham, gia in (("kiem_lap_phu_de", ["gieo: phụ đề lặp"]),
                         ("kiem_quang_cam", ["gieo: quãng câm quá dài"])):
        goc = getattr(pa, ten_ham)
        try:
            setattr(pa, ten_ham, lambda *_a, **_k: list(gia))
            kq = pa.dung_video(tmp_path / f"bom_{ten_ham}")
        finally:
            setattr(pa, ten_ham, goc)

        if kq["trang_thai"] == "KHONG_CHAY_DUOC":
            pytest.skip(f"không đo được: {kq['vi_sao']}")
        assert kq["trang_thai"] == "FAIL", (
            f"{ten_ham} BÁC mà dây chuyền vẫn {kq['trang_thai']} — "
            f"phán quyết không đi tới `trang_thai`"
        )
        assert gia[0] in kq["vi_sao"], (
            f"lý do bác của {ten_ham} không lọt ra ngoài: {kq['vi_sao']!r}"
        )

    # Ca đối chứng: không bơm gì thì cùng đường ấy phải PASS.
    sach = pa.dung_video(tmp_path / "khong_bom")
    if sach["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"đối chứng không đo được: {sach['vi_sao']}")
    assert sach["trang_thai"] == "PASS", (
        f"đối chứng phải PASS mới chứng minh được bài trên: {sach['vi_sao']}"
    )


def test_de_dong_bang_du_dai_va_du_cau_khac_nhau():
    """Đề phải tự nó lấp đầy 55–65s, không nhờ đệm im lặng.

    Trước 03/09 đặc tả đòi đề 120–160 từ VÀ video 55–65 s cùng lúc. Ở tốc độ đo
    được (3,58–3,95 từ/s) thì đề 160 từ đọc hết nhiều nhất 41,5 s — hai con số
    chưa bao giờ giao nhau, và `_dai_ngan_lai()` âm thầm hoà giải chúng bằng
    15,23 s im lặng.
    """
    import re

    from core.phong_alpha import FIXTURE

    van = FIXTURE.read_text(encoding="utf-8").strip()
    so_tu = len(van.split())
    cau = [c.strip() for c in re.split(r"(?<=[.!?])\s+", van) if c.strip()]

    assert 215 <= so_tu <= 250, f"đề {so_tu} từ, đặc tả đòi 215–250"
    assert len(set(cau)) >= 13, (
        f"đề chỉ có {len(set(cau))} câu khác nhau trên {len(cau)}, cần ≥ 13"
    )
    # Ở 3,9 từ/s — cận dưới của cửa sổ video, không cần đệm.
    assert so_tu / 3.95 >= 55.0, f"đề đọc hết {so_tu / 3.95:.1f}s, dưới 55s"


def test_de_doi_chung_AM_van_con_tren_dia():
    """Đề cũ là vật chứng: kịch bản rác qua sạch mọi cửa HÌNH DẠNG.

    Giữ tệp lại để lần sau còn dựng lại được ca ấy mà không phải chế lại.
    """
    import re

    from core.phong_alpha import FIXTURE

    lap = FIXTURE.with_name("STUDIO_FIXTURE_LAP.md")
    assert lap.is_file(), "mất ca đối chứng âm"
    van = lap.read_text(encoding="utf-8").strip()
    cau = [c.strip() for c in re.split(r"(?<=[.!?])\s+", van) if c.strip()]
    assert len(set(cau)) == 1 and len(cau) >= 20, (
        f"đối chứng âm phải là MỘT câu lặp nhiều lần, đang là "
        f"{len(set(cau))} câu khác nhau trên {len(cau)}"
    )


def test_do_quang_cam_SINH_RA_khong_do_duoc_khi_ffmpeg_gay(tmp_path):
    """`_quang_cam_dai_nhat` phải TRẢ VỀ −1,0 khi không đo được, không phải 0,0.

    Gieo 03/09/2026 bắt được chỗ mù: đổi `return -1.0` thành `return 0.0` trong
    nhánh `r.returncode != 0` mà cả 39 bài vẫn xanh. Lý do là bài
    `test_cham_quang_cam_tach_ba_trang_thai` chấm hàm `kiem_quang_cam(-1.0)` —
    tức chấm NGƯỜI XỬ — trong khi không bài nào bắt NGƯỜI SINH RA số ấy phải
    sinh đúng. Trên một lượt chạy được thì ffmpeg không bao giờ gãy, nên nhánh
    ấy chưa từng chạy.

    Cùng họ với `kiem_nung`: chấm được một hàm không chứng minh giá trị vào nó
    từ đâu ra. Lần thứ tư trong tệp này.

    0,0 nguy hơn 0,0 nghe có vẻ: nó đọc thành "đo rồi, không có quãng câm nào"
    và `kiem_quang_cam(0.0)` cho ĐẠT — tức "chưa đo được" đội lốt "đã đo, không
    sao", đúng cái ba-trạng-thái sinh ra để chống.
    """
    from core.phong_alpha import _quang_cam_dai_nhat, kiem_quang_cam

    for ten, tep in (("tệp không tồn tại", tmp_path / "khong_co.wav"),
                     ("tệp không phải wav", tmp_path / "rac.wav")):
        if tep.name == "rac.wav":
            tep.write_bytes(b"day khong phai wav")
        do = _quang_cam_dai_nhat(tep)
        assert do < 0, (
            f"{ten}: trả {do}, phải là số ÂM. Trả 0.0 thì "
            f"`kiem_quang_cam` cho ĐẠT và 'không đo được' biến mất."
        )
        assert kiem_quang_cam(do), f"{ten}: {do} phải dẫn tới BÁC"

    # Ca đối chứng: một tệp wav THẬT thì phải đo ra số không âm.
    from core.phong_alpha import FIXTURE, doc_giong

    that, ly_do = doc_giong("Một câu ngắn để thử.", tmp_path)
    if that is None:
        pytest.skip(f"đối chứng không đo được: {ly_do}")
    assert _quang_cam_dai_nhat(that) >= 0, (
        "tệp wav thật phải đo ra số không âm — nếu không thì bài trên xanh "
        "chỉ vì hàm luôn trả số âm"
    )


# ---------------------------------------------------------------------------
# CỬA PHỦ KÍN KỊCH BẢN (04/09/2026)
#
# Mọi cửa phía trên đối chiếu phụ đề với CHÍNH NÓ — đủ dòng, khác nhau, không
# chạy quá phim. Không cửa nào nhìn ngược về kịch bản gốc, nên một lượt chạy
# thật ngày 04/09 ra PASS sạch trong khi giọng đọc 17 câu mà màn hình chỉ có 14,
# và ba câu mất là ba câu KẾT.
# ---------------------------------------------------------------------------

# Chép TAY từ KY_LUAT_THUC_THI.md, mục "Cửa PHỦ KÍN KỊCH BẢN": số câu được phép
# mất là 0. Không đọc hằng số từ mã — gieo `8 -> 999` hôm 04/09 cho thấy đọc từ
# mã thì hai vế cùng đổi và cửa không bao giờ mâu thuẫn được với mã.
DAC_TA_SO_CAU_DUOC_PHEP_MAT = 0


@pytest.mark.parametrize("so_cau,so_the", [
    (13, 13),   # chia hết — ca DUY NHẤT bản cũ không mất câu
    (17, 13),   # đúng ca đo được ngày 04/09: bản cũ mất 4
    (20, 13),   # bản cũ mất 7
    (25, 13),   # bản cũ mất 12
    (14, 12), (15, 14), (31, 12),
])
def test_cat_doan_KHONG_bo_sot_cau_nao(so_cau, so_the):
    """Chia thẻ phải phủ kín kịch bản với MỌI cặp (số câu, số thẻ).

    `viet_kich_ban` chỉ ép ≥13 câu, không có trần trên; `so_the` thì bằng
    `round(dài_giọng / 4,5)`. Hai con số ấy không có lý do gì trùng nhau, nên
    ca "không chia hết" là ca THƯỜNG.
    """
    from core.phong_alpha import _cat_doan

    cau = [f"Câu số {i} nói một chuyện riêng." for i in range(1, so_cau + 1)]
    doan = _cat_doan(" ".join(cau), so_the)
    assert len(doan) == so_the, f"{len(doan)} đoạn, cần đúng {so_the}"
    tren_man = " ".join(doan)
    mat = [c for c in cau if c not in tren_man]
    assert len(mat) == DAC_TA_SO_CAU_DUOC_PHEP_MAT, (
        f"{so_cau} câu / {so_the} thẻ: mất {len(mat)} câu — {mat[:3]}"
    )


def test_kiem_phu_kin_biet_noi_KHONG():
    """Cửa chưa từng nói không thì chưa chứng minh được gì.

    `return []` vô điều kiện cũng cho mọi ca hợp lệ đi qua.
    """
    from core.phong_alpha import kiem_phu_kin

    van = "Câu một nói chuyện này. Câu hai nói chuyện khác. Câu ba kết lại."
    du = ["Câu một nói chuyện này.", "Câu hai nói chuyện khác.", "Câu ba kết lại."]
    assert kiem_phu_kin(van, du) == [], "kịch bản phủ kín mà vẫn bị bác"

    thieu = du[:2]                      # bỏ đúng câu KẾT, như lỗi thật
    ly_do = kiem_phu_kin(van, thieu)
    assert ly_do, "mất câu kết mà cửa im lặng"
    assert "Câu ba kết lại." in ly_do[0], f"lý do không nói câu nào mất: {ly_do}"

    assert kiem_phu_kin("", du), "không có kịch bản thì phải là lý do bác"


@can_ffmpeg
@pytest.mark.slow
def test_day_chuyen_NGHE_phan_quyet_cua_cua_phu_kin(tmp_path):
    """Chấm được một hàm không chứng minh kết quả của nó đi tới đâu.

    Gieo `if ly_do_nung:` -> `if False:` hôm 03/09 mà cả 30 bài vẫn xanh, vì mọi
    bài đều gọi thẳng hàm thuần. Đây là lần thứ tư trong tệp này, nên bài viết
    theo đúng khuôn ấy ngay từ đầu: bơm một phán quyết BÁC rồi chạy CẢ dây
    chuyền, kèm ca đối chứng không bơm.
    """
    import core.phong_alpha as pa

    goc = pa.kiem_phu_kin
    try:
        pa.kiem_phu_kin = lambda van_ban, khoi: ["gieo: kịch bản chưa phủ kín"]
        kq = pa.dung_video(tmp_path / "bom_bac")
    finally:
        pa.kiem_phu_kin = goc

    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")
    assert kq["trang_thai"] == "FAIL", (
        f"cửa phủ kín BÁC mà dây chuyền vẫn {kq['trang_thai']} — "
        "phán quyết không đi tới `trang_thai`"
    )
    assert "gieo: kịch bản chưa phủ kín" in kq["vi_sao"], kq["vi_sao"]

    # Ca đối chứng: cùng đường ấy, không bơm gì thì phải PASS. Dùng ĐÚNG văn bản
    # mặc định chứ không dùng câu ngắn cho nhanh — đo 03/09 thì câu bốn mệnh đề
    # cho bản trộn −29,9 LUFS, nên đối chứng đỏ vì độ ồn chứ không vì chuyện
    # đang xét.
    sach = pa.dung_video(tmp_path / "khong_bom")
    if sach["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"đối chứng không đo được: {sach['vi_sao']}")
    assert sach["trang_thai"] == "PASS", (
        f"đối chứng phải PASS mới chứng minh được bài trên: {sach['vi_sao']}"
    )
    assert sach["kiem"]["so"]["so_cau_len_man_hinh"] == \
        sach["kiem"]["so"]["so_cau_kich_ban"], sach["kiem"]["so"]


# ---------------------------------------------------------------------------
# SỐ THẺ KHÔNG ĐƯỢC VƯỢT SỐ CÂU (04/09/2026)
#
# `_cat_doan` đệm cho đủ thẻ bằng cách LẶP LẠI câu. Thiếu câu thì thẻ cuối
# chiếu lại câu đầu trong khi giọng đã đọc xong — và không cửa nào kêu, vì
# `kiem_lap_phu_de` chấm TỈ LỆ khác nhau (13/14 = 0,93 ≫ 0,80) còn
# `kiem_phu_kin` hỏi "có câu nào bị bỏ sót không", không hỏi "có câu nào bị
# chiếu hai lần không". Lỗ nằm GIỮA hai cửa.
# ---------------------------------------------------------------------------

def _cau_khac_nhau(n: int) -> str:
    return " ".join(f"Ý thứ {i} nói một chuyện riêng." for i in range(1, n + 1))


@pytest.mark.parametrize("so_cau,giay", [
    (13, 61.0),   # CA THẬT đã đo: 13 câu là sàn đặc tả, 61s giữa cửa sổ 55–65s
    (13, 65.0),
    (13, 58.0),   # ca đối chứng: cùng số câu, giọng ngắn hơn -> chưa bao giờ lặp
    (11, 65.0), (9, 65.0), (3, 65.0), (17, 65.0), (22, 55.0),
    # 1 và 2 câu là ca DUY NHẤT chạm tới sàn `SO_THE_TOI_THIEU`. Lưới đầu của
    # tôi bắt đầu từ 3, nên gieo "bỏ sàn" vẫn XANH — cửa mù, bắt được bằng phép
    # gieo chứ không bằng đọc lại.
    (1, 65.0), (2, 55.0),
])
def test_so_the_KHONG_vuot_so_cau(so_cau, giay):
    """Sàn cứng `SO_THE_TOI_THIEU` vẫn thắng — dưới 3 thẻ thì không đủ đổi cảnh.

    Nhưng ở đó cửa nội dung bác THẬT (một khối chiếm 1/3 > 0,25), nên nó hỏng
    to chứ không hỏng lặng.
    """
    from core.phong_alpha import SO_THE_TOI_THIEU, so_the_can_dung

    the = so_the_can_dung(giay, _cau_khac_nhau(so_cau))
    assert the <= max(so_cau, SO_THE_TOI_THIEU), (
        f"{so_cau} câu / {giay}s -> {the} thẻ: nhiều thẻ hơn câu thì phải lặp")
    assert the >= SO_THE_TOI_THIEU


@pytest.mark.parametrize("so_cau", [3, 9, 11, 13, 14, 17, 22])
@pytest.mark.parametrize("giay", [55.0, 58.0, 61.0, 65.0])
def test_khong_khoi_phu_de_nao_bi_chieu_HAI_LAN(so_cau, giay):
    """Đi từ số câu + thời lượng ra ĐÚNG các khối sẽ lên màn hình, rồi đếm.

    Không khẳng định về `so_the_can_dung` — khẳng định về THỨ KHÁN GIẢ THẤY.
    """
    from core.phong_alpha import _cat_doan, so_the_can_dung

    van = _cau_khac_nhau(so_cau)
    doan = _cat_doan(van, so_the_can_dung(giay, van))
    lap = len(doan) - len(set(doan))
    if so_cau >= 3:
        assert lap == 0, (
            f"{so_cau} câu / {giay}s: {lap} khối bị chiếu lại — {doan}")


@can_ffmpeg
@pytest.mark.slow
def test_day_chuyen_THAT_SU_hoi_so_the_can_dung(tmp_path):
    """Chấm được một hàm không chứng minh kết quả của nó đi tới đâu.

    Lần thứ năm trong tệp này, nên viết theo khuôn ngay từ đầu: bơm một số thẻ
    KHÁC vào rồi đếm ẢNH THẬT trên đĩa. Soi văn bản hàm thì gieo `so_the_can_dung`
    thành `int(round(dai/GIAY_MOI_THE))` vẫn xanh — đó là cửa mù.
    """
    import core.phong_alpha as pa

    goc = pa.so_the_can_dung
    try:
        pa.so_the_can_dung = lambda dai, van: 7
        kq = pa.dung_video(tmp_path / "bom_so_the")
    finally:
        pa.so_the_can_dung = goc

    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"không đo được: {kq['vi_sao']}")
    anh = [a for a in kq["artifacts"] if a.get("type") == "IMAGE"]
    assert len(anh) == 7, (
        f"bơm 7 thẻ mà dây chuyền dựng {len(anh)} ảnh — "
        "`so_the_can_dung` không phải thứ quyết định số thẻ")
