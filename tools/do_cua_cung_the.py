# -*- coding: utf-8 -*-
"""Bốn cửa nghiệm thu cho app lập trình bằng THẺ. Máy chấm, không ai tự khai.

VÌ SAO CÓ TỆP NÀY — đo 20/08/2026.

Bản v1 tự chấm "cửa cứng 1: 42/42 khớp SHA-256". Phép thử ấy mở tệp, KHÔNG SỬA
GÌ, rồi lưu — mà `luu_cay_the_ra_tep_py` có đường tắt:

    if not record.has_modifications:
        return record.raw_bytes

Nên nó trả lại đúng mảng byte đầu vào. SHA khớp 100% với MỌI tệp, kể cả tệp bộ
đọc phân tích hỏng hoàn toàn, vì bộ sinh mã chưa hề được gọi. Ép đi qua bộ sinh
mã thì ra 2.329/4.674 thẻ làm lệch tệp (50,2%), 60/64 tệp dính.

Bốn cửa dưới đây đo đúng việc người dùng làm, không đo ý định của mã.

BA TRẠNG THÁI, không gộp (luật CLAUDE.md mục 4):
    0  đạt
    1  đo được mà KHÔNG đạt
    2  KHÔNG đo được (thiếu core.the_v1, kho rỗng...)

    venv\\Scripts\\python.exe -X utf8 tools\\do_cua_cung_the.py
"""
from __future__ import annotations

import ast
import io
import json
import sys
import tokenize
from datetime import datetime
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
RA = GOC / "data" / "the_v1"
THU_MUC = ("core", "interface", "tools", "tests")

# Thẻ KHỐI trùm cả thân con nên line_end của nó không phải cuối dòng đầu.
# Bản v1 lấy `l_start == l_end` làm điều kiện trích chú thích, nên thẻ khối
# LUÔN mất chú thích — đo được 4/4 dòng, gồm user_memory.py:211.
KHOI = {"neu", "nguoc_lai", "ham", "lap_moi", "lap_khi"}


def _tep_py():
    ra = []
    for d in THU_MUC:
        t = GOC / d
        if t.is_dir():
            ra += sorted(p for p in t.rglob("*.py") if p.is_file())
    return ra


def _phang(nodes):
    """Duyệt phẳng cả cây, kể cả thẻ con — lỗi nằm nhiều ở thẻ lồng."""
    ra = []

    def di(ns):
        for n in ns:
            ra.append(n)
            di(n.than)
    di(nodes)
    return ra


def _chu_thich_that(nguon):
    """Dòng nào THẬT SỰ có chú thích cuối dòng, chấm bằng bộ tách token.

    Không dò dấu thăng: kho có 9 dòng chứa dấu ấy bên trong chuỗi, và
    user_memory.py:211 có CẢ HAI trên cùng một dòng.
    """
    dong = nguon.splitlines()
    ra = {}
    try:
        for t in tokenize.generate_tokens(io.StringIO(nguon).readline):
            if t.type != tokenize.COMMENT:
                continue
            truoc = dong[t.start[0] - 1][:t.start[1]]
            if truoc.strip():          # có mã đứng trước -> chú thích CUỐI DÒNG
                ra[t.start[0]] = dong[t.start[0] - 1][t.start[1]:]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return {}
    return ra


# ------------------------------------------------------------------- cửa 1
def cua_1_go_lai_y_cu(doc, luu):
    """Mở một thẻ, gõ lại ĐÚNG giá trị cũ, lưu -> tệp không được đổi byte nào.

    Hợp đồng P1: Yêu cầu 100% byte-exact (n_y_byte == n_the), không chấp nhận
    chỉ cùng AST nếu lệch byte. Lỗi mở/parser/writer làm cửa trượt ngay lập tức.
    """
    n_the = n_nguyen = n_doi = n_vo = n_y_byte = 0
    theo_tep = []
    vi_du = []
    for p in _tep_py():
        b = p.read_bytes()
        txt = b.decode("utf-8")
        try:
            cay_goc = ast.dump(ast.parse(txt))
        except SyntaxError:
            continue
        try:
            rec = doc(p)
        except Exception as e:
            n_vo += 1
            theo_tep.append({"tep": p.name, "the": 0, "hong": 1,
                             "loi_mo": type(e).__name__})
            continue
        ds = _phang(rec.tree)
        d0 = txt.splitlines()
        hong = 0
        for n in ds:
            for m in ds:
                m.da_sua = False
            n.da_sua = True
            rec.has_modifications = True
            n_the += 1
            try:
                ra = luu(rec).decode("utf-8")
            except Exception:
                n_vo += 1
                hong += 1
                continue
            if ra.encode("utf-8") == b:
                n_nguyen += 1
                n_y_byte += 1
                continue
            try:
                if ast.dump(ast.parse(ra)) == cay_goc:
                    n_nguyen += 1          # khác byte nhưng cùng nghĩa
                    n_doi += 1             # Hợp đồng P1: lệch byte là không đạt Cửa 1
                    loai = "lech_byte"
                else:
                    n_doi += 1
                    loai = "doi_nghia"
            except SyntaxError:
                n_vo += 1
                loai = "vo_cu_phap"
            hong += 1
            if len(vi_du) < 40:
                vi_du.append({
                    "tep": p.name, "the": n.ma, "dong": n.line_start,
                    "loai": loai,
                    "goc": (d0[n.line_start - 1].strip()[:96]
                            if n.line_start and n.line_start <= len(d0) else ""),
                })
        theo_tep.append({"tep": p.name, "the": len(ds), "hong": hong})
    return {
        "ten": "Cửa 1 — gõ lại y giá trị cũ, tệp phải không đổi byte",
        "dat": (n_the > 0) and (n_doi == 0) and (n_vo == 0) and (n_y_byte == n_the),
        "the": n_the, "nguyen": n_nguyen, "y_het_byte": n_y_byte,
        "doi_nghia": n_doi, "vo_cu_phap": n_vo,
        "tep_dinh": sum(1 for x in theo_tep if x.get("hong")),
        "tep_tong": len(theo_tep),
        "theo_tep": sorted(theo_tep, key=lambda x: -x.get("hong", 0)),
        "vi_du": vi_du,
    }


# ------------------------------------------------------------------- cửa 2
def cua_2_chu_thich(doc, luu):
    """Chú thích cuối dòng phải còn nguyên sau khi lưu — thẻ LẺ và thẻ KHỐI như nhau.

    Hợp đồng P1: Sửa một ô trên thẻ có chú thích rồi lưu ra đĩa/bytes, kiểm tra
    chú thích có thật sự xuất hiện ở tệp đầu ra không. Lỗi parser/writer làm cửa trượt.
    """
    co = mat = 0
    theo_the = {}
    vi_du = []
    for p in _tep_py():
        txt = p.read_text(encoding="utf-8")
        ct = _chu_thich_that(txt)
        if not ct:
            continue
        try:
            rec = doc(p)
        except Exception:
            mat += len(ct)
            continue

        ds = _phang(rec.tree)
        for n in ds:
            if n.ma != "ma_tho" and n.line_start in ct:
                o = theo_the.setdefault(n.ma, [0, 0])
                o[0] += 1
                # Đánh dấu đã sửa và lưu để kiểm tra thực tế sau ghi
                for m in ds:
                    m.da_sua = False
                n.da_sua = True
                rec.has_modifications = True
                try:
                    out_text = luu(rec).decode("utf-8")
                except Exception:
                    out_text = ""
                n.da_sua = False

                if ct[n.line_start] in out_text:
                    co += 1
                else:
                    mat += 1
                    o[1] += 1
                    if len(vi_du) < 20:
                        vi_du.append({"tep": p.name, "the": n.ma,
                                      "dong": n.line_start,
                                      "chu_thich": ct[n.line_start][:70],
                                      "khoi": n.ma in KHOI})
    return {
        "ten": "Cửa 2 — chú thích cuối dòng phải còn sau khi lưu, kể cả trên thẻ khối",
        "dat": (co > 0) and (mat == 0), "co": co, "mat": mat,
        "theo_the": {k: {"co_ct": v[0], "mat": v[1], "khoi": k in KHOI}
                     for k, v in sorted(theo_the.items())},
        "vi_du": vi_du,
    }


# ------------------------------------------------------------------- cửa 3
def cua_3_origin(kiem):
    """Origin phải so BẰNG NHAU trên hostname, chặn scheme lạ, userinfo, path, port sai.

    Hợp đồng P1: Kiểm tra toàn diện 14 phép thử HTTP Origin và Referer.
    """
    class _Gia:
        def __init__(self, o=None, r=None):
            self.headers = {}
            if o is not None:
                self.headers["Origin"] = o
            if r is not None:
                self.headers["Referer"] = r

    thu = [
        (_Gia("http://127.0.0.1:8088"), True, "trang that 127.0.0.1"),
        (_Gia("http://localhost:8088"), True, "trang that localhost"),
        (_Gia("http://[::1]:8088"), True, "trang that IPv6 loopback"),
        (_Gia(""), True, "cung nguon, khong co Origin"),
        (_Gia("https://evil.example"), False, "trang la"),
        (_Gia("http://127.0.0.1.evil.com"), False, "ten mien GIA chua 127.0.0.1"),
        (_Gia("http://localhost.evil.com"), False, "ten mien GIA chua localhost"),
        (_Gia("http://evil.com/?x=127.0.0.1"), False, "127.0.0.1 nam trong query"),
        (_Gia("http://not-localhost.tld"), False, "localhost la hau to"),
        (_Gia("http://evil.com@localhost"), False, "chua userinfo"),
        (_Gia("ftp://localhost"), False, "scheme khong hop le (ftp)"),
        (_Gia("//localhost"), False, "thieu scheme"),
        (_Gia("http://localhost/path"), False, "Origin khong duoc chua path"),
        (_Gia("http://localhost:99999"), False, "port ngoai pham vi"),
        (_Gia(None, "http://localhost:8088/app"), True, "Referer loopback hop le"),
        (_Gia(None, "http://evil.com/app"), False, "Referer trang la"),
    ]
    ra, sai = [], 0
    for req_obj, mong, ghi in thu:
        try:
            that = bool(kiem(req_obj))
        except Exception as e:
            that = None
            ghi = ghi + " [" + type(e).__name__ + "]"
        ok = that is mong
        if not ok:
            sai += 1
        ra.append({"origin": req_obj.headers.get("Origin") or req_obj.headers.get("Referer") or "(khong co)",
                   "mong": mong, "that": that, "dat": ok, "ghi": ghi})
    return {"ten": "Cửa 3 — Origin so bằng hostname, không dò chuỗi con",
            "dat": sai == 0, "sai": sai, "tong": len(thu), "thu": ra}
    for o, mong, ghi in thu:
        try:
            that = bool(kiem(_Gia(o)))
        except Exception as e:
            that = None
            ghi = ghi + " [" + type(e).__name__ + "]"
        ok = that is mong
        if not ok:
            sai += 1
        ra.append({"origin": o or "(khong co)", "mong": mong, "that": that,
                   "dat": ok, "ghi": ghi})
    return {"ten": "Cửa 3 — Origin so bằng hostname, không dò chuỗi con",
            "dat": sai == 0, "sai": sai, "tong": len(thu), "thu": ra}


# Ô là MỘT biểu thức -> bọc ngoặc là cách sửa hợp lệ với mọi hình dạng.
O_BIEU_THUC = ("gia_tri", "dieu_kien", "day")
# Ô là DANH SÁCH ĐỐI SỐ -> bọc ngoặc thì hỏng: `(parents=True, exist_ok=True)`
# không phải biểu thức. ĐÃ SAI MỘT LẦN 20/08, 59 thẻ Gọi hàm bị chấm trượt oan.
# Thêm một đối số vị trí ở ĐẦU thì hợp lệ với cả `*args` lẫn `**kwargs`.
O_DOI_SO = ("doi_so", "noi_dung")
O_TEN = ("ten_bien", "ten_ham", "bien")
O_DOI = O_BIEU_THUC + O_DOI_SO


def _dot_bien(o: str, kieu: str, cu: str) -> str:
    """Đổi ô sao cho VẪN HỢP CÚ PHÁP với mọi hình dạng đối số."""
    if kieu in ("ten", "chu_thich"):
        return cu + "_zz"
    thu = (["0, " + cu, "(" + cu + ")"] if o in O_DOI_SO
           else ["(" + cu + ")"])
    for x in thu:
        try:
            ast.parse("_(%s)" % x if o in O_DOI_SO else "_ = %s" % x)
            return x
        except SyntaxError:
            continue
    return cu + "_zz"


def cua_4_doi_that(doc, luu):
    """Đổi THẬT một ô: chỉ dòng của thẻ đó được đổi, không dòng nào khác.

    Bản CST không dựng lại dòng từ ô bao giờ, nên câu hỏi "thẻ tả đúng nguồn
    không" của cửa 4 cũ không còn nghĩa. Câu hỏi tương đương mà MẠNH HƠN: sửa
    một ô thì vết sửa có nằm gọn trong thẻ ấy không, hay lan sang chỗ khác.
    """
    tong = sai = tho = 0
    theo_the = {}
    vi_du = []
    tong_dong_vat_ly = 0
    dong_the_that = 0
    _dong_tep: set = set()

    for p in _tep_py():
        goc = p.read_text(encoding="utf-8").splitlines()
        tong_dong_vat_ly += len(goc)
        _dong_tep = set()
        try:
            rec = doc(p)
        except Exception:
            sai += 1
            continue
        ds = _phang(rec.tree)
        for n in ds:
            if n.ma == "ma_tho":
                tho += 1
                continue
            if n.ma == "chu_thich":
                o = "noi_dung"
                kieu = "chu_thich"
            else:
                o = next((k for k in O_DOI if k in n.o and n.o[k].strip()), None)
                kieu = "bieu_thuc"
                if o is None:
                    o = next((k for k in O_TEN if k in n.o and n.o[k].strip()), None)
                    kieu = "ten"
            if o is None:
                continue                       # thẻ không có ô nào sửa được
            tong += 1
            if n.line_start and n.line_end:
                _dong_tep.update(
                    range(n.line_start, (n.line_end or n.line_start) + 1))
            elif n.line_start:
                _dong_tep.add(n.line_start or 0)
            v = theo_the.setdefault(n.ma, [0, 0])
            v[0] += 1
            cu = n.o[o]
            n.o[o] = _dot_bien(o, kieu, cu)
            n.da_sua = True
            rec.has_modifications = True
            try:
                ra = luu(rec).decode("utf-8").splitlines()
            except Exception:
                ra = None
            n.o[o] = cu                        # trả lại nguyên trạng
            n.da_sua = False
            if ra is None:
                sai += 1
                v[1] += 1
                continue
            # SO ĐẦU VÀ ĐUÔI, không so theo chỉ số dòng tuyệt đối.
            d = n.line_start - 1
            c = (n.line_end or n.line_start)
            duoi = len(goc) - c
            gon = (goc[:d] == ra[:d]
                   and (duoi == 0 or goc[c:] == ra[len(ra) - duoi:]))
            if not gon or ra == goc:
                sai += 1
                v[1] += 1
                if len(vi_du) < 20:
                    vi_du.append({"tep": p.name, "the": n.ma,
                                  "dong": n.line_start, "o": o,
                                  "lan_ra": [] if gon else ["truoc/sau lech"],
                                  "goc": goc[n.line_start - 1].strip()[:70]})
        dong_the_that += len(_dong_tep)     # cộng SAU khi gom hết một tệp
    return {
        "ten": "Cửa 4 — đổi thật một ô, vết sửa nằm gọn trong thẻ ấy",
        "dat": (tong > 0) and (sai == 0), "the_that": tong, "tho": tho, "sai": sai,
        "phu_song": round(100 * tong / max(tong + tho, 1), 1),
        "phu_song_dong": round(100 * dong_the_that / max(tong_dong_vat_ly, 1), 1),
        "theo_the": {k: {"tong": v[0], "sai": v[1]}
                     for k, v in sorted(theo_the.items(),
                                        key=lambda x: -x[1][0])},
        "vi_du": vi_du,
    }


def chay():
    """Chạy cả bốn cửa nghiệm thu app thẻ, ghi MỘT tệp JSON khoá đã sắp.

    01/09/2026 — bỏ cờ `--v1`. Bộ đọc AST trong `core/the_v1.py` đã bị xoá vì
    KHÔNG AI GỌI: `interface/the_api.py` lấy hàm đọc từ `the_cst`. Giữ một
    nhánh chấm bộ đọc không ai dùng là chấm một thứ không tồn tại trên đường
    người dùng đi — và nó đã làm tôi báo sai một lần, xem `tests/test_the_cst.py`.
    """
    try:
        sys.path.insert(0, str(GOC))
        from core.the_cst import (doc_tep_py_sang_cay_the,
                                  luu_cay_the_ra_tep_py)
        from interface.the_api import kiem_tra_origin_hop_le
    except Exception as e:
        return None, "khong nap duoc bo doc / interface.the_api: %r" % (e,)

    if not _tep_py():
        return None, "khong tim thay tep .py nao trong %s" % (THU_MUC,)

    print(f"[*] Bộ đọc: the_cst (LibCST) — Quét {len(_tep_py())} tệp .py...", flush=True)
    
    print("[1/4] Đang đo Cửa 1 (gõ lại y giá trị cũ, bảo toàn byte)...", flush=True)
    c1 = cua_1_go_lai_y_cu(doc_tep_py_sang_cay_the, luu_cay_the_ra_tep_py)
    
    print("[2/4] Đang đo Cửa 2 (bảo toàn chú thích cuối dòng)...", flush=True)
    c2 = cua_2_chu_thich(doc_tep_py_sang_cay_the, luu_cay_the_ra_tep_py)
    
    print("[3/4] Đang đo Cửa 3 (bảo mật Origin / Referer)...", flush=True)
    c3 = cua_3_origin(kiem_tra_origin_hop_le)
    
    print("[4/4] Đang đo Cửa 4 (tỷ lệ phủ thẻ & độ chính xác miêu tả)...", flush=True)
    c4 = cua_4_doi_that(doc_tep_py_sang_cay_the, luu_cay_the_ra_tep_py)

    cua = [c1, c2, c3, c4]

    # Tên hiển thị lấy TỪ `BO_THE_V1`, không chép tay sang đây. Mã `gan` là
    # khoá trong máy (khoá JSON, tên biến JS/Python) nên buộc không dấu; chữ
    # người đọc thấy là `ten` = "Gán", và app đã làm đúng chỗ đó từ đầu — chỉ
    # bảng của tôi trước 20/08 in mã máy ra cho người đọc.
    try:
        from core.the_v1 import BO_THE_V1
        ten_the = {k: v.ten for k, v in BO_THE_V1.items()}
    except Exception:
        ten_the = {}

    so = {
        "bo_doc": "the_cst (LibCST)",
        "ten_the": ten_the,
        "luc": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "kho": str(GOC),
        "thu_muc_quet": list(THU_MUC),
        "so_tep": len(_tep_py()),
        "dat_het": all(c["dat"] for c in cua),
        "cua": cua,
    }
    RA.mkdir(parents=True, exist_ok=True)
    ten_so = "cua_cung_cst.json"
    (RA / ten_so).write_text(
        json.dumps(so, ensure_ascii=False, sort_keys=True, indent=1),
        encoding="utf-8")
    return so, ""


def main() -> int:
    """Chạy bốn cửa rồi in bảng, qua bộ đọc `the_cst` (LibCST).

    Mã thoát theo luật ba trạng thái: 0 đạt · 1 đo được mà không đạt ·
    2 không đo được. Gộp ba cái này làm hai là mở đường cho "0/4" đọc thành
    "thua sạch" trong khi thật ra phép đo chưa hề chạy.
    """
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    so, loi = chay()
    if so is None:
        print("KHONG DO DUOC: " + loi)
        return 2                       # khong do duoc, KHAC voi truot
    from bao_cao_cua_cung import in_bang, dung_trang, TRANG
    # doc LAI tu dia, khong dung `so` trong RAM: bang nguoi doc phai dung tu
    # dung so JSON da ghi (luat CLAUDE.md muc 5)
    ten_so = "cua_cung_cst.json"
    tu_so = json.loads((RA / ten_so).read_text(encoding="utf-8"))
    in_bang(tu_so)
    trang = TRANG.with_name("bao_cao_cst.html")
    trang.write_text(dung_trang(tu_so), encoding="utf-8")
    print("\nso   : " + str(RA / ten_so))
    print("trang: " + str(trang))
    return 0 if tu_so["dat_het"] else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
