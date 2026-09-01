# -*- coding: utf-8 -*-
"""Gieo lỗi vào mã rồi xem cửa có đỏ không — một cửa chưa từng đỏ thì chưa chứng minh gì.

VÌ SAO CÓ TỆP NÀY
-----------------
30/08/2026. Trong một ngày, tôi viết tay mười mấy script gieo. **Ba trong số đó
tự hỏng**, và mỗi lần hỏng lại làm tôi đọc sai kết quả một lúc:

* neo bằng ``\\n`` trên tệp CRLF thuần  -> "GIEO KHÔNG VÀO", tưởng cửa mù
* cửa sổ 260 ký tự đặt tay quá ngắn     -> tưởng nhánh quá giờ dẫn sai trạng thái
* ``print("ℹ")`` qua stdout cp1252      -> ``UnicodeEncodeError``, mất cả lượt đo

Cả ba đều là bẫy CỦA MÔI TRƯỜNG, không phải của phép đo. Viết lại bằng tay mỗi
lần thì lần nào cũng có thể vấp lại. Tệp này gom chúng vào một chỗ, đã trả giá
một lần thì thôi.

BỐN THỨ NÓ TỰ LO
----------------
1. **Xuống dòng.** Đọc bằng ``newline=""`` để giữ nguyên, và ghi lại đúng kiểu
   tệp vốn có. Phép gieo viết bằng ``\\n`` vẫn khớp được tệp CRLF.
2. **UTF-8.** In qua ``_in()`` — nổ ``UnicodeEncodeError`` thì tự ghi thẳng
   bytes UTF-8. KHÔNG tráo ``sys.stdout`` toàn cục (xem chú thích ở ``_in``).
3. **Trả về nguyên byte.** So SHA-256 trước và sau, ở ``finally``. Gieo mà không
   trả được thì đó là chuyện nghiêm trọng hơn cả kết quả gieo.
4. **Gieo không vào.** Nếu phép thay không đổi được gì thì báo to, KHÔNG lẳng
   lặng bỏ qua — im lặng ở đây đọc y hệt "cửa bắt được".

MÃ THOÁT
--------
``0`` mọi phép gieo đều làm cửa ĐỎ, và nền thì XANH · ``1`` có phép gieo mà cửa
vẫn xanh (cửa mù), hoặc nền đã đỏ sẵn · ``2`` không đo được (gieo không vào, trả
mã về không nguyên byte, không chạy nổi lệnh).

DÙNG NHƯ THƯ VIỆN
-----------------
::

    from tools.gieo import Phep, chay_gieo
    chay_gieo(
        lenh=["venv/Scripts/python.exe", "-m", "pytest", "tests/test_x.py", "-q"],
        cac_phep=[
            Phep("bỏ rào chắn", "core/x.py", "if datHet:", "if True:"),
            Phep("đếm sai", "core/x.py", "len(bo_qua)", "0"),
        ],
    )
"""
from __future__ import annotations

import hashlib
import io
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

GOC_MAC_DINH = Path(__file__).resolve().parent.parent

def _in(*phan) -> None:
    """In an toàn, KHÔNG đụng vào ``sys.stdout`` toàn cục.

    Bản đầu bọc lại ``sys.stdout`` ngay lúc import cho khỏi nổ ``UnicodeEncodeError``
    trên console cp1252. Chính bộ test của tệp này bắt được: pytest bắt đầu ra
    bằng cách tráo ``sys.stdout``, nên bọc lúc import làm vỡ máy bắt của nó —
    "ValueError: I/O operation on closed file", 0 test chạy được.
    Sửa biến toàn cục lúc import là việc một thư viện không được phép làm.
    Nay chỉ bọc TẠI CHỖ IN, và chỉ khi lần in thẳng nổ.
    """
    chu = " ".join(str(x) for x in phan)
    try:
        print(chu)
    except UnicodeEncodeError:
        dem = getattr(sys.stdout, "buffer", None)
        if dem is None:
            print(chu.encode("ascii", "replace").decode("ascii"))
        else:
            dem.write((chu + "\n").encode("utf-8", "replace"))
            dem.flush()


# ---------------------------------------------------------------------------
# Đọc/ghi giữ nguyên kiểu xuống dòng
# ---------------------------------------------------------------------------
def _kieu_xuong_dong(raw: bytes) -> str:
    """CRLF hay LF? Quyết theo cái nào NHIỀU hơn, không theo cái gặp trước.

    Tệp lẫn lộn thì đa số thắng; ghi lại một kiểu duy nhất là đúng ý muốn.
    """
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return "\r\n" if crlf >= lf and crlf > 0 else "\n"


def doc(duong: Path) -> tuple[str, str, bytes]:
    """Trả về (nội dung đã chuẩn hoá về ``\\n``, kiểu xuống dòng gốc, byte gốc)."""
    raw = duong.read_bytes()
    kieu = _kieu_xuong_dong(raw)
    chu = raw.decode("utf-8").replace("\r\n", "\n")
    return chu, kieu, raw


def ghi(duong: Path, chu: str, kieu: str) -> None:
    duong.write_bytes(chu.replace("\n", kieu).encode("utf-8"))


# ---------------------------------------------------------------------------
@dataclass
class Phep:
    """Một phép gieo.

    ``cu``/``moi``: thay chuỗi. Viết bằng ``\\n``; tệp CRLF vẫn khớp.
    ``ham``: nếu cần đổi phức tạp hơn thì truyền hàm ``(chu) -> chu``, và khi ấy
    ``cu``/``moi`` bị bỏ qua.
    ``so_lan``: mặc định 1. Truyền ``0`` để thay tất cả.
    """

    ten: str
    tep: str
    cu: str = ""
    moi: str = ""
    ham: Optional[Callable[[str], str]] = None
    so_lan: int = 1

    def ap_dung(self, chu: str) -> str:
        if self.ham is not None:
            return self.ham(chu)
        if self.so_lan <= 0:
            return chu.replace(self.cu, self.moi)
        return chu.replace(self.cu, self.moi, self.so_lan)


@dataclass
class KetQua:
    nen_xanh: bool = False
    dong_nen: str = ""
    hang: list[tuple[str, str, str]] = field(default_factory=list)  # (tên, kết luận, dòng tóm tắt)
    khong_vao: list[str] = field(default_factory=list)
    cua_mu: list[str] = field(default_factory=list)
    khong_tra_duoc: list[str] = field(default_factory=list)

    @property
    def ma_thoat(self) -> int:
        if self.khong_vao or self.khong_tra_duoc:
            return 2
        if not self.nen_xanh or self.cua_mu:
            return 1
        return 0


# ---------------------------------------------------------------------------
def _don_pycache(cac_tep: Sequence[Path]) -> None:
    """Xoá bản biên dịch cũ cạnh các tệp bị gieo.

    Python quyết định dùng lại ``.pyc`` bằng **mtime + KÍCH THƯỚC**. Một phép gieo
    rất hay giữ nguyên độ dài — ``GIA_TRI = 42`` -> ``GIA_TRI = 99`` là cùng số
    byte — và nếu mtime chưa nhích qua độ phân giải của hệ tệp thì tiến trình con
    nạp lại BẢN CŨ. Hạt giống không vào tới máy, nhưng công cụ lại thấy lệnh vẫn
    xanh và kết luận "CỬA MÙ" — vu oan cho cửa.

    Bắt được ngày 30/08/2026 bởi chính bộ test của tệp này: cùng một phép gieo,
    ca CRLF đỏ (đúng) còn ca LF xanh (sai), khác nhau chỉ vì may rủi thời điểm ghi.
    """
    for t in {p.parent / "__pycache__" for p in cac_tep}:
        if not t.is_dir():
            continue
        for f in t.glob("*.pyc"):
            try:
                f.unlink()
            except OSError:
                pass


def _chay(lenh: Sequence[str], goc: Path, tom_tat) -> tuple[int, str]:
    import os

    moi_truong = dict(os.environ)
    # Đừng sinh .pyc mới trong lúc gieo, và đừng để màu ANSI làm hỏng dòng tóm tắt
    # (xem core/trace_runtime.py cùng ngày: FORCE_COLOR làm bộ phân tích mù).
    moi_truong["PYTHONDONTWRITEBYTECODE"] = "1"
    moi_truong.pop("FORCE_COLOR", None)
    moi_truong.pop("PY_COLORS", None)
    moi_truong["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(
            list(lenh), capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=str(goc), env=moi_truong,
        )
    except Exception as e:                                   # noqa: BLE001
        return -1, f"KHÔNG CHẠY ĐƯỢC LỆNH: {type(e).__name__}: {e}"
    return r.returncode, tom_tat((r.stdout or "") + "\n" + (r.stderr or ""))


def _tom_tat_mac_dinh(dau_ra: str) -> str:
    """Lấy dòng tổng kết của pytest hoặc node --test; không thấy thì lấy dòng cuối."""
    dong = [d.strip() for d in dau_ra.splitlines() if d.strip()]
    for d in reversed(dong):
        if ("passed" in d or "failed" in d) and " in " in d:
            return d[:78]
    for d in dong:
        if d.startswith("ℹ fail") or d.startswith("# fail"):
            return d[:78]
    return (dong[-1][:78] if dong else "(không có đầu ra)")


def chay_gieo(
    lenh: Sequence[str],
    cac_phep: Sequence[Phep],
    goc: Path = GOC_MAC_DINH,
    tom_tat: Callable[[str], str] = _tom_tat_mac_dinh,
    im_lang: bool = False,
) -> KetQua:
    """Chạy nền, gieo từng phép, trả mã về, in bảng. Xem mã thoát ở đầu tệp."""
    kq = KetQua()
    duong = {p: (goc / p) for p in {ph.tep for ph in cac_phep}}
    goc_chu: dict[str, str] = {}
    goc_kieu: dict[str, str] = {}
    goc_bam: dict[str, str] = {}

    for ten, d in duong.items():
        if not d.is_file():
            kq.khong_tra_duoc.append(f"{ten}: không có tệp này")
            return kq
        chu, kieu, raw = doc(d)
        goc_chu[ten], goc_kieu[ten], goc_bam[ten] = chu, kieu, hashlib.sha256(raw).hexdigest()

    def noi(*a):
        if not im_lang:
            _in(*a)

    try:
        ma, tt = _chay(lenh, goc, tom_tat)
        kq.nen_xanh = (ma == 0)
        kq.dong_nen = tt
        noi(f"  {'chưa gieo gì':<52} mã thoát {ma}  {tt}")
        if not kq.nen_xanh:
            noi("\n  *** NỀN ĐÃ ĐỎ SẴN — gieo lúc này không nói lên điều gì. Dừng. ***")
            return kq
        noi("")

        for ph in cac_phep:
            d = duong[ph.tep]
            cu = goc_chu[ph.tep]
            moi = ph.ap_dung(cu)
            if moi == cu:
                kq.khong_vao.append(ph.ten)
                kq.hang.append((ph.ten, "KHÔNG VÀO", ""))
                noi(f"  {ph.ten:<52} *** GIEO KHÔNG VÀO — phép thay không khớp gì ***")
                continue
            ghi(d, moi, goc_kieu[ph.tep])
            _don_pycache([d])
            try:
                ma, tt = _chay(lenh, goc, tom_tat)
            finally:
                ghi(d, cu, goc_kieu[ph.tep])
                _don_pycache([d])
            if ma == 0:
                kq.cua_mu.append(ph.ten)
                ket = "*** VẪN XANH — CỬA MÙ ***"
            else:
                ket = "ĐỎ (đạt)"
            kq.hang.append((ph.ten, ket, tt))
            noi(f"  {ph.ten:<52} mã thoát {ma}  {tt}  -> {ket}")

        noi("")
        ma, tt = _chay(lenh, goc, tom_tat)
        noi(f"  {'trả mã về nguyên trạng':<52} mã thoát {ma}  {tt}")
    finally:
        # Trả về, rồi CHỨNG MINH là đã trả về — so băm, không tin vào việc mình vừa ghi.
        for ten, d in duong.items():
            try:
                ghi(d, goc_chu[ten], goc_kieu[ten])
            except Exception as e:                           # noqa: BLE001
                kq.khong_tra_duoc.append(f"{ten}: ghi lại hỏng: {e}")
                continue
            bam = hashlib.sha256(d.read_bytes()).hexdigest()
            if bam != goc_bam[ten]:
                kq.khong_tra_duoc.append(f"{ten}: băm lệch {bam[:12]}… ≠ {goc_bam[ten][:12]}…")
        if not im_lang:
            if kq.khong_tra_duoc:
                for x in kq.khong_tra_duoc:
                    _in(f"\n  *** KHÔNG TRẢ MÃ VỀ ĐƯỢC: {x}")
            else:
                _in(f"\n  {len(duong)} tệp: giống hệt TỪNG BYTE trước khi gieo")

    return kq


# ---------------------------------------------------------------------------
def _cli() -> int:
    import json

    if len(sys.argv) < 2:
        _in(__doc__)
        _in("  Dùng: python tools/gieo.py <tệp_mô_tả.json>")
        _in('  {"lenh": [...], "cac_phep": [{"ten":..., "tep":..., "cu":..., "moi":...}]}')
        return 2
    mo_ta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    kq = chay_gieo(
        lenh=mo_ta["lenh"],
        cac_phep=[Phep(**p) for p in mo_ta["cac_phep"]],
        goc=Path(mo_ta.get("goc", GOC_MAC_DINH)),
    )
    return kq.ma_thoat


if __name__ == "__main__":
    raise SystemExit(_cli())
