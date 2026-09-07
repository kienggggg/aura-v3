# -*- coding: utf-8 -*-
"""Phụ đề theo TỪNG TỪ — mốc phải đo được, và chữ phải THẬT SỰ quét.

Đăng ký ở `KY_LUAT_THUC_THI.md` §2d (07/09/2026), chép TAY xuống đây.

CỬA ĐẦU CỦA CHÍNH BÀI NÀY ĐÃ MÙ, VÀ ĐÂY LÀ CHỖ ĐẮT NHẤT.
Bản đầu chứng minh "chữ có đổi theo thời gian" bằng cách băm dải phụ đề ở ba
mốc rồi thấy ba khung khác nhau. Nhưng nền có Ken Burns phóng chậm
(1,00 → 1,12 suốt một thẻ), nên **ba khung khác nhau kể cả khi chữ đứng im** —
cửa ấy đo chuyển động của NỀN, không đo chuyển động của CHỮ.

Đo lại bằng thứ chỉ karaoke mới làm được: đếm điểm ảnh VÀNG. `\\kf` quét chữ
từ trắng sang vàng theo thời gian, nên trong một đoạn số điểm vàng phải TĂNG.
Chạy thật 07/09 trên `video_chua_nung.mp4` có sẵn:

    t (s)    KARAOKE .ass    ĐỐI CHỨNG .srt
     0,44               0                 0
     1,55           1.965                 0
     2,66           7.613                 0
     3,77          12.591                 0

Ca đối chứng khác đúng MỘT biến: cùng video nền, cùng ba mốc, nung bằng `.srt`
theo đoạn thay vì `.ass` karaoke. Nó phẳng 0 — nên con số bên trái đúng là do
karaoke, không do cái gì khác.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from core import can_chu

# Chép TAY từ §2d-bis. Không viết `can_chu.TY_LE_NUA_TU` ở vế phải: gieo đổi
# hằng số trong mã thì hai vế cùng đổi và cửa vẫn xanh — bẫy tautological 02/09.
#
# `WER` và `khớp` KHÔNG còn là cửa (07/09 chiều). Chúng đặt từ đúng một kịch
# bản và 6/6 kịch bản khác trượt — tức karaoke gần như không bật. Nay cửa hỏi
# thẳng thứ người xem thấy: vệt sáng lệch bao nhiêu giây.
DAC_TA_CAN_TY_LE_NUA_TU = 0.5
DAC_TA_CAN_MODEL = "small"


def test_hang_so_khop_DAC_TA():
    assert can_chu.TY_LE_NUA_TU == DAC_TA_CAN_TY_LE_NUA_TU
    assert can_chu.MODEL == DAC_TA_CAN_MODEL


def test_KHOP_khong_con_la_cua_va_TRUC_da_doi():
    """Đo được 07/09 chiều, ba kịch bản tự nhiên:

        kịch bản     khớp     p90 / ngưỡng      phán quyết
        tài chính   89,8%   0,087 / 0,100      PASS
        kỹ thuật    86,7%   0,210 / 0,100      KHÔNG ĐẠT
        văn xuôi    83,7%   0,067 / 0,100      PASS

    `văn xuôi` khớp THẤP NHẤT mà đạt, `kỹ thuật` khớp cao hơn lại trượt. Hai
    trục xếp hạng NGƯỢC nhau — đó là bằng chứng "% từ khớp" không phải thứ
    quyết định chất lượng. Bài này chốt rằng cửa không quay về trục cũ.
    """
    import inspect

    nguon = inspect.getsource(can_chu.can_tung_tu)
    assert "KHOP_SAN" not in nguon, (
        "`can_tung_tu` lại chấm bằng `KHOP_SAN` — trục cũ đã quay lại")
    assert "WER_TRAN" not in nguon, (
        "`can_tung_tu` lại chấm bằng `WER_TRAN` — trục cũ đã quay lại")
    assert "sai_so_noi_suy" in nguon, "không còn gọi phép giữ lại"


def test_giu_lai_giau_theo_CHUOI_chu_khong_rai_rac():
    """Giấu rải rác là đo ca dễ, và bản đầu của chính bài này mắc đúng thế.

    Mỗi từ giấu rải rác đều nằm GIỮA hai neo, nội suy gần như không thể sai
    (trung vị 0,000s). Chỗ hỏng thật là CHUỖI liền nhau. Đo 07/09 trên cùng
    một kịch bản: giấu chuỗi dài 1 ra p90 0,040s; dài 10 ra p90 0,386s.

    Ở đây dựng một lượt có chuỗi trống dài 3, và đòi phép giữ lại cũng phải
    giấu được một cụm dài 3 — nếu nó chỉ giấu lẻ từng từ thì bài đỏ.
    """
    # 12 từ; neo ở mọi chỗ TRỪ chỉ số 4,5,6 -> chuỗi trống thật dài 3.
    neo = {i: (i * 0.2, i * 0.2 + 0.2) for i in range(12) if i not in (4, 5, 6)}
    ss = can_chu.sai_so_noi_suy(neo, [[f"t{i}" for i in range(12)]],
                                [(0.0, 2.4)])
    assert ss["do_duoc"], ss
    assert 3 in ss["dai_chuoi_trong"], ss
    # HỎI ĐỘ DÀI ĐÃ GIẤU, KHÔNG HỎI ĐỘ DÀI ĐO ĐƯỢC. Bản đầu của bài này khẳng
    # định `3 in dai_chuoi_trong` — nhưng trường ấy là chuỗi trống THẬT, không
    # đổi khi bộ đo quay về giấu rải rác. Gieo `L = 1` thì cửa VẪN XANH.
    assert 3 in ss["dai_da_giau"], (
        f"phép giữ lại không giấu nổi một cụm dài 3 — nó đang giấu rải rác, "
        f"tức đo ca dễ: {ss}")
    # Neo đều tăm tắp thì nội suy đúng tuyệt đối — đó là ca đối chứng: phép đo
    # KHÔNG được tự sinh ra sai số từ hư không.
    assert ss["p90"] == 0.0, ss


def test_giu_lai_BAT_duoc_khi_tieng_noi_KHONG_deu():
    """Ca đối chứng chiều ngược: mốc lệch nhau thì phép đo phải kêu.

    Bài trên dùng neo đều và đòi sai số bằng 0. Chỉ có một chiều thì chưa
    chứng minh được gì — phép đo luôn trả 0 cũng qua bài ấy.
    """
    # Từ 0-5 rất ngắn, từ 6-11 rất dài: nội suy đều sẽ trượt nặng.
    moc = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    neo = {i: (t, t + 0.1) for i, t in enumerate(moc)}
    ss = can_chu.sai_so_noi_suy(neo, [[f"t{i}" for i in range(12)]],
                                [(0.0, 6.6)])
    assert ss["do_duoc"], ss
    assert ss["p90"] > ss["nguong"], (
        f"tiếng nói rất không đều mà phép đo vẫn báo khớp: {ss}")


def test_ghep_moc_bang_LCS_chu_khong_bang_thu_tu():
    """Bộ nhận dạng thêm/bớt từ, nên ghép theo thứ tự sẽ lệch dần.

    Ở đây bản nhận **thiếu** một từ ở giữa. Ghép theo `zip` thì từ thứ 3 trở đi
    nhận mốc của từ đứng sau nó — sai hết phần đuôi mà không chỗ nào kêu. Đúng
    bài "gắn theo thứ tự là giả định, không phải phép đo".
    """
    goc = ["một", "hai", "ba", "bốn", "năm"]
    nhan = ["một", "hai", "bốn", "năm"]
    cap = can_chu._lcs_cap(goc, nhan)
    assert cap == [(0, 0), (1, 1), (3, 2), (4, 3)], cap
    # "ba" (chỉ số 2) KHÔNG được gán cho bất kỳ từ nhận nào.
    assert 2 not in {i for i, _ in cap}


def test_noi_suy_lap_cho_trong_va_van_TANG_DAN():
    """Từ không khớp thì nội suy, không bỏ trắng — bỏ trắng thì chữ mất giữa câu."""
    moc = {0: (0.0, 1.0), 3: (3.0, 4.0)}
    ra = can_chu._noi_suy(moc, 4, 0.0, 4.0)
    assert len(ra) == 4
    assert ra[0] == (0.0, 1.0) and ra[3] == (3.0, 4.0)
    for i in range(1, 4):
        assert ra[i][0] >= ra[i - 1][0] - 1e-9, ra
    # Hai từ giữa phải nằm HẲN trong khe 1,0 -> 3,0, không đè lên hai đầu.
    assert 1.0 <= ra[1][0] < ra[2][0] <= 3.0, ra


def test_ass_ghi_kf_bang_PHAN_TRAM_GIAY_chu_khong_phai_mili_giay():
    """Nhầm đơn vị thì karaoke chạy nhanh gấp 10 và libass KHÔNG kêu.

    Một từ dài đúng 1,00 giây phải ra `\\kf100`. Ra `\\kf1000` thì tệp vẫn hợp
    lệ, vẫn nung được, vẫn có chữ — chỉ là chữ quét sai hoàn toàn. Không cửa
    nào hỏi "có phụ đề không" thấy được chỗ này.
    """
    p = can_chu.viet_ass(["alpha beta"], [(0.0, 2.0)],
                         [[(0.0, 1.0), (1.0, 2.0)]],
                         pytest.importorskip("pathlib").Path(
                             __import__("tempfile").mkdtemp()) / "x.ass")
    chu = p.read_text(encoding="utf-8")
    assert r"{\kf100}alpha" in chu, chu
    assert r"{\kf100}beta" in chu, chu


def test_KHONG_co_bo_can_thi_KHONG_DO_DUOC_chu_khong_phai_FAIL(monkeypatch, tmp_path):
    """Thiếu một cái thước không phải là hỏng.

    Ba trạng thái không được gộp thành hai. Trả `FAIL` ở đây thì mọi máy chưa
    cài bộ căn đều thấy Alpha đỏ và sẽ đi sửa nhầm chỗ; trả `PASS` thì tệ hơn
    nhiều — "chưa đo được" đội lốt "đã đo, không sao".
    """
    monkeypatch.setattr(can_chu, "tim_bo_can", lambda: None)
    kq = can_chu.can_tung_tu(tmp_path / "khong_co.wav", ["a b"], [(0.0, 1.0)],
                             tmp_path / "x.ass")
    assert kq["trang_thai"] == "KHONG_DO_DUOC", kq
    assert kq["ass"] is None
    assert not (tmp_path / "x.ass").exists()


def test_do_duoc_ma_DUOI_NGUONG_thi_KHONG_DAT_chu_khong_phai_KHONG_DO_DUOC(
        monkeypatch, tmp_path):
    """Có số, và số ấy nói không — đó là nhánh thứ ba, phải đứng riêng."""
    monkeypatch.setattr(can_chu, "tim_bo_can", lambda: "python")

    # Mọi từ đều khớp, nhưng TIẾNG NÓI RẤT KHÔNG ĐỀU: sáu từ đầu dồn trong
    # nửa giây, sáu từ sau kéo mỗi từ một giây. Nội suy đều sẽ trượt nặng, nên
    # phép giữ lại phải bắt được — dù `khớp` là 100%.
    tu = ["một", "hai", "ba", "bốn", "năm", "sáu",
          "bảy", "tám", "chín", "mười", "mười một", "mười hai"]
    moc = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]

    class _R:
        returncode = 0
        stderr = ""
        stdout = json.dumps({"tu": [{"bd": t, "kt": t + 0.1, "chu": w}
                                    for w, t in zip(tu, moc)],
                             "model": "small"}, ensure_ascii=False)

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _R())
    kq = can_chu.can_tung_tu(tmp_path / "a.wav", [" ".join(tu)],
                             [(0.0, 6.6)], tmp_path / "x.ass")
    assert kq["trang_thai"] == "KHONG_DAT", kq
    assert kq["ass"] is None
    assert kq["so"]["khop"] == 1.0, (
        f"khớp 100% mà vẫn phải trượt — đó là cả điểm của việc đổi trục: "
        f"{kq['so']}")
    assert kq["so"]["sai_so"]["p90"] > kq["so"]["sai_so"]["nguong"], kq["so"]


def test_KHONG_giau_noi_chuoi_nao_thi_KHONG_DO_DUOC_chu_khong_phai_dat(
        monkeypatch, tmp_path):
    """Neo thưa tới mức không giấu nổi cụm nào thì CHƯA kết luận được.

    Phép gieo 07/09 bắt được chỗ mù: đổi `if not ss["do_duoc"]:` thành
    `if False:` mà cả bộ vẫn xanh — không bài nào canh nhánh thứ ba này. Gộp
    nó vào `PASS` là đúng bệnh "chưa đo được đội lốt đã đo, không sao".
    """
    monkeypatch.setattr(can_chu, "tim_bo_can", lambda: "python")

    class _R:
        returncode = 0
        stderr = ""
        stdout = json.dumps({"tu": [{"bd": 0.0, "kt": 0.2, "chu": "một"}],
                             "model": "small"}, ensure_ascii=False)

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _R())
    kq = can_chu.can_tung_tu(tmp_path / "a.wav",
                             ["một hai ba bốn năm sáu bảy tám chín mười"],
                             [(0.0, 5.0)], tmp_path / "x.ass")
    assert kq["trang_thai"] == "KHONG_DO_DUOC", kq
    assert kq["ass"] is None
    assert not (tmp_path / "x.ass").exists()
    assert kq["so"]["sai_so"]["do_duoc"] is False, kq["so"]


def _dung_video_thu(d, ass_hay_srt, ten_ra):
    """Video 4 giây một màu + nung phụ đề. Nhỏ và nhanh, chạy được trong bộ test."""
    nen = d / "nen.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=0x101828:s=720x1280:d=4:r=12", "-pix_fmt",
                    "yuv420p", str(nen)], check=True, timeout=180)
    ra = d / ten_ra
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", nen.name,
                    "-vf", f"subtitles={ass_hay_srt.name}", str(ra.name)],
                   cwd=str(d), check=True, timeout=300)
    return ra


def _dem_vang(mp4, giay) -> int:
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{giay:.2f}", "-i", str(mp4),
         "-frames:v", "1", "-vf", "crop=720:220:0:1000", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=120)
    b, n = r.stdout, 0
    for i in range(0, len(b) - 2, 3):
        if b[i] > 200 and 150 < b[i + 1] < 245 and b[i + 2] < 90:
            n += 1
    return n


def test_chu_THAT_SU_quet_theo_thoi_gian_va_ca_doi_chung_thi_KHONG(tmp_path):
    """Đếm điểm ảnh VÀNG, không băm khung.

    Băm khung thì Ken Burns làm mọi khung khác nhau và cửa xanh dù chữ đứng
    im. Ca đối chứng ở đây khác đúng MỘT biến: cùng nền, cùng ba mốc, nung
    bằng `.srt` chữ tĩnh — số điểm vàng của nó phải đúng 0.
    """
    if not __import__("shutil").which("ffmpeg"):
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này không có ffmpeg")

    ass = can_chu.viet_ass(["một hai ba bốn"], [(0.0, 4.0)],
                           [[(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]],
                           tmp_path / "kar.ass")
    srt = tmp_path / "doan.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:04,000\nmột hai ba bốn\n",
                   encoding="utf-8", newline="\n")

    v_kar = _dung_video_thu(tmp_path, ass, "kar.mp4")
    v_doan = _dung_video_thu(tmp_path, srt, "doan.mp4")

    diem = [0.2, 1.4, 2.6, 3.8]
    kar = [_dem_vang(v_kar, g) for g in diem]
    doi = [_dem_vang(v_doan, g) for g in diem]

    assert sum(doi) == 0, (
        f"ca đối chứng (chữ tĩnh) cũng ra điểm vàng {doi} — phép đo đang bắt "
        "nhầm thứ khác, không phải quét karaoke")
    assert all(kar[i] >= kar[i - 1] for i in range(1, len(kar))), (
        f"điểm vàng không tăng dần: {kar}")
    assert kar[-1] > kar[0] > 0 or kar[-1] > 0, (
        f"chữ không quét: {kar}")


def test_chay_THAT_bo_can_TU_DUNG_LAY_TIENG(tmp_path):
    """Phép đo thật, và bài này TỰ SINH tiếng thay vì bám vào đĩa.

    Bản đầu đọc `data/alpha/sau_va2_163047/` — một lượt Alpha cũ. Nó bốc hơi
    giữa chừng: `_dung_video` gọi `_don_luot_cu(thu_muc_ra.parent)`, giữ đúng
    `SO_LUOT_GIU = 5` thư mục mới nhất dưới `data/alpha/` và xoá phần còn lại.
    Chỉ cần một lượt chạy thử trỏ vào `data/alpha/` là thư mục kia đi. Bài test
    bám vào đĩa thì màu của nó phụ thuộc việc ai vừa chạy cái gì — cùng họ với
    "test đổi màu theo mạng".
    """
    if not can_chu.tim_bo_can():
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này chưa có bộ căn chữ")
    import core.phong_alpha as pa

    # SÁU CÂU, KHÔNG PHẢI MƯỜI BA. Bài này đo BỘ CĂN, không dựng video, nên
    # không cần đủ 55–65 giây. Đo 07/09: 13 câu tốn 200 giây, 6 câu tốn một
    # nửa, và WER/khớp vẫn tính trên hơn trăm từ. Một bộ test dài tới mức
    # người ta ngừng chạy thì bằng không.
    doan = [c.strip() + "." for c in _kich_ban_du_dai().split(".")
            if c.strip()][:6]
    wav, moc, ly_do = pa.doc_giong_theo_doan(doan, tmp_path)
    if wav is None or not moc:
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: không sinh được giọng — {ly_do}")

    kq = can_chu.can_tung_tu(wav, doan[:len(moc)], moc, tmp_path / "t.ass")
    assert kq["trang_thai"] in ("PASS", "KHONG_DAT"), kq
    assert "wer" in kq["so"] and "khop" in kq["so"], kq
    ss = kq["so"]["sai_so"]
    assert ss["do_duoc"], kq["so"]
    assert ss["nguong"] == round(ss["tu_dai_trung_vi"]
                                 * DAC_TA_CAN_TY_LE_NUA_TU, 3), ss
    if kq["trang_thai"] == "PASS":
        assert ss["p90"] <= ss["nguong"], ss
        assert (tmp_path / "t.ass").is_file()
        assert r"\kf" in (tmp_path / "t.ass").read_text(encoding="utf-8")
    else:
        assert not (tmp_path / "t.ass").exists(), (
            "dưới ngưỡng mà vẫn ghi .ass — bản karaoke sai mốc đi vào video")


def test_phong_alpha_THAT_SU_truyen_ket_qua_can_vao_render():
    """Hỏi ĐỐI SỐ tại điểm gọi, không hỏi tên hàm có mặt trong tệp.

    Bài học 06/09: một cửa kiểm `state.theQuyTrinh[presetId]` "có mặt trong
    hàm" vẫn xanh sau khi gieo bỏ đúng đối số cần canh — vì dòng ấy còn nguyên
    ở chỗ khác. Ở đây đọc bằng AST: lời gọi `render(...)` phải có `nung=` và
    giá trị của nó phải là biến hứng kết quả bộ căn.
    """
    import ast

    cay = ast.parse((can_chu.PROJECT_ROOT / "core" / "phong_alpha.py")
                    .read_text(encoding="utf-8"))
    # Tên biến hứng `.ass` từ `can_tung_tu`
    goi_can = [n for n in ast.walk(cay)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "can_tung_tu"]
    assert goi_can, "`_dung_video` không gọi `can_tung_tu` nữa"

    goi_render = [n for n in ast.walk(cay)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "render"]
    assert goi_render, "không tìm thấy lời gọi `render(...)`"
    co_nung = [k for g in goi_render for k in g.keywords if k.arg == "nung"]
    assert co_nung, "`render(...)` được gọi mà KHÔNG truyền `nung=` — bản .ass "
    for k in co_nung:
        assert isinstance(k.value, ast.Name), ast.dump(k.value)
        assert k.value.id == "ass", (
            f"`nung=` nhận {ast.unparse(k.value)}, không phải kết quả bộ căn")


def test_render_co_tham_so_nung_va_KHONG_ep_kieu_len_file_ass():
    """`force_style` đè lên `.ass` thì màu quét bị mất và chữ đứng im.

    Vẫn có chữ, vẫn qua mọi cửa "có phụ đề không" — nên chỗ này phải canh
    riêng bằng cấu trúc, không bằng mắt.
    """
    import ast
    import inspect

    from core import phong_alpha

    ts = inspect.signature(phong_alpha.render).parameters
    assert "nung" in ts, "render() không còn nhận `nung`"

    nguon = inspect.getsource(phong_alpha.render)
    cay = ast.parse(nguon.lstrip())
    # Mọi chuỗi có `force_style` phải nằm trong một nhánh CÓ điều kiện về `.ass`
    ba = [n for n in ast.walk(cay)
          if isinstance(n, ast.IfExp) and "force_style" in ast.unparse(n)]
    assert ba, ("`force_style` không nằm trong biểu thức điều kiện nào — "
                "tức nó áp cho cả `.ass` lẫn `.srt`")
    assert any(".ass" in ast.unparse(n.test) for n in ba), (
        "điều kiện quanh `force_style` không nhắc tới `.ass`")


# ---------------------------------------------------------------------------
# Hai bài dưới CHẠY CẢ DÂY CHUYỀN. Chúng đắt (~50–90 giây mỗi bài) và cố ý nằm
# ở đây chứ không nằm trong `test_phong_alpha_de_ra_video_that.py`: tệp ấy gọi
# `dung_video` 12 lượt, mỗi lượt cõng thêm bộ căn thì bộ đủ đi từ 13:36 lên
# 31:17. Một bộ test dài tới mức người ta ngừng chạy thì bằng không.
#
# Nhưng tắt bộ căn ở đó mà KHÔNG có hai bài này thì việc nối chỉ được chứng
# minh bằng AST — tức bằng chữ, không bằng hành vi. Đúng bài "một khả năng có
# sẵn mà không ai gọi thì bằng không".
# ---------------------------------------------------------------------------


def _kich_ban_du_dai() -> str:
    """~247 từ / 13 câu — cùng cỡ với kịch bản đã đo 60,00s ngày 06/09.

    Bản đầu của hai bài dưới dùng 13 câu ngắn (~9 từ) và cả hai đỏ với
    *"quãng không có giọng dài 16,50s, cần ≤ 2,0s"* — một cửa CÓ SẴN từ trước,
    không liên quan gì tới bộ căn. Kịch bản ngắn hơn cửa sổ video thì phần đuôi
    im lặng, và cửa ấy bắt đúng. Mỗi câu ở đây 19 từ, đúng trần
    `core/viet_truyen.py` đo được.
    """
    y = ["bảng điều khiển", "dòng tiền vào", "biểu đồ cột", "khoản chi lớn",
         "nguồn thu chính", "hạn mức tháng", "thẻ tín dụng", "ngân sách năm",
         "báo cáo tuần", "cảnh báo sớm", "mục tiêu dài", "sổ tiết kiệm",
         "hoá đơn điện"]
    return " ".join(
        f"Phần thứ {i} nói về {t}, khác hẳn phần trước ở cách dữ liệu "
        f"được trình bày."
        for i, t in enumerate(y, 1))


def test_CA_DAY_CHUYEN_that_su_ra_ass_va_nung_duoc(tmp_path):
    """Chạy `dung_video` THẬT, có bộ căn. Đo 07/09: PASS · 84,1s."""
    if not can_chu.tim_bo_can():
        pytest.skip("KHÔNG ĐO ĐƯỢC: máy này chưa có bộ căn chữ")
    import core.phong_alpha as pa

    kq = pa.dung_video(tmp_path / "ra", _kich_ban_du_dai())
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: {kq['vi_sao']}")

    so = kq["kiem"]["so"]
    assert so["can_chu"] in ("PASS", "KHONG_DAT"), so
    assert "can_wer" in so and "can_khop" in so, (
        "chạy được mà không ghi số ra sổ — không ai đọc lại được")

    ten = {h.get("kind") for h in kq["artifacts"]}
    if so["can_chu"] == "PASS":
        assert "ass_karaoke_tung_tu" in ten, ten
        ass = next(h for h in kq["artifacts"]
                   if h["kind"] == "ass_karaoke_tung_tu")
        p = can_chu.PROJECT_ROOT / ass["path"] if not str(
            ass["path"]).startswith(str(tmp_path)) else __import__(
            "pathlib").Path(ass["path"])
        assert r"\kf" in p.read_text(encoding="utf-8")
    else:
        assert "ass_karaoke_tung_tu" not in ten, (
            "dưới ngưỡng mà vẫn ghi ra .ass — bản karaoke sai mốc đi vào video")


def test_DUOI_NGUONG_thi_LUI_ve_srt_chu_KHONG_lam_hong_ca_video(tmp_path,
                                                                monkeypatch):
    """Đo được mà dưới ngưỡng → video vẫn dựng xong, chỉ mất phần karaoke.

    Bản đầu 07/09 để `KHONG_DAT` kéo cả lượt xuống đỏ. Chạy bộ đủ thì **6 bài
    đỏ**, vì WER phụ thuộc TIẾNG và LỜI chứ không phụ thuộc mã:

        đề 245 từ / 60s     WER  6,9%   khớp 93,1%
        đề ngắn trong test  WER 17,9%   khớp 82,1%

    Màu của một lượt dựng khi ấy đổi theo NỘI DUNG chứ không theo đúng/sai —
    đúng bài "test đổi màu theo mạng" đã chữa 06/09, chỉ khác biến. Bài này
    chốt hành vi mới, và chốt luôn rằng đường lui THẬT SỰ chạy.
    """
    import core.phong_alpha as pa

    monkeypatch.setattr(pa, "can_tung_tu", lambda *a, **k: {
        "trang_thai": "KHONG_DAT", "ass": None,
        "so": {"wer": 0.179, "khop": 0.821},
        "vi_sao": "gieo: WER 17.9% · khớp 82.1%"})
    kq = pa.dung_video(tmp_path / "ra", _kich_ban_du_dai())
    if kq["trang_thai"] == "KHONG_CHAY_DUOC":
        pytest.skip(f"KHÔNG ĐO ĐƯỢC: {kq['vi_sao']}")

    so = kq["kiem"]["so"]
    assert so["can_chu"] == "KHONG_DAT", so
    assert so["can_wer"] == 0.179, "số đo được không đi vào sổ"
    assert kq["trang_thai"] == "PASS", (
        f"bộ căn dưới ngưỡng kéo cả video xuống {kq['trang_thai']} — "
        f"màu của lượt dựng đang đổi theo nội dung: {kq['kiem']['vi_sao']}")

    ten = {h.get("kind") for h in kq["artifacts"]}
    assert "ass_karaoke_tung_tu" not in ten, ten
    # ĐƯỜNG LUI PHẢI CHẠY THẬT, không chỉ là "không nổ". Có bản chưa nung tức
    # bước nung `.srt` đã chạy — đúng hành vi từ 06/09.
    assert "chua_nung_phu_de" in ten, (
        f"không lui về nung .srt — video có thể đang KHÔNG có chữ: {ten}")
