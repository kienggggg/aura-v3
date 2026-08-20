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


def _muc(nut) -> int:
    """Mức thụt đầu dòng để truyền cho `sinh_dong_the_don`.

    ĐÃ SAI MỘT LẦN, 20/08: bản đầu đếm chiều sâu đệ quy. Sai hai đường —
    `TheNode.indent` lưu SỐ DẤU CÁCH chứ không phải số cấp, và chiều sâu đệ quy
    lệch hẳn vì thẻ `ma_tho` cũng lồng con (the_v1.py:684 thụt 4 dấu cách mà bộ
    đếm ra mức 11). Hậu quả: 3 thẻ `else:` hoàn toàn lành bị chấm là tả sai.

    Chấm bằng thứ máy ghi lại được, đừng chấm bằng thứ mình đếm lấy.
    """
    return (nut.indent or 0) // 4


def _tep_py():
    ra = []
    for d in THU_MUC:
        t = GOC / d
        if t.is_dir():
            ra += sorted(p for p in t.glob("*.py") if p.is_file())
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

    Đây là việc người dùng làm hằng ngày, và là phép thử mà đường tắt
    `raw_bytes` không đỡ được.
    """
    # Tách RIÊNG "y hệt byte" khỏi "cùng nghĩa". Gộp lại thì mất một tin: có
    # những chỗ khác byte mà chương trình không đổi (dòng gập lại, ngoặc thừa).
    # Số byte nghiêm hơn nhưng số nghĩa mới là số quyết định app có hại hay không.
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
            theo_tep.append({"tep": p.name, "the": 0, "hong": 0,
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
                    continue
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
        "dat": (n_doi + n_vo) == 0,
        "the": n_the, "nguyen": n_nguyen, "y_het_byte": n_y_byte,
        "doi_nghia": n_doi, "vo_cu_phap": n_vo,
        "tep_dinh": sum(1 for x in theo_tep if x.get("hong")),
        "tep_tong": len(theo_tep),
        "theo_tep": sorted(theo_tep, key=lambda x: -x.get("hong", 0)),
        "vi_du": vi_du,
    }


# ------------------------------------------------------------------- cửa 2
def cua_2_chu_thich(doc, sinh_dong):
    """Chú thích cuối dòng phải còn nguyên — thẻ LẺ và thẻ KHỐI như nhau.

    Bản v1: thẻ lẻ 21/21 giữ được, thẻ khối 0/4.
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
            continue

        def di(ns, muc):
            nonlocal co, mat
            for n in ns:
                if n.ma != "ma_tho" and n.line_start in ct:
                    o = theo_the.setdefault(n.ma, [0, 0])
                    o[0] += 1
                    try:
                        ra = sinh_dong(n, _muc(n))
                    except Exception:
                        ra = ""
                    if ct[n.line_start] in ra:
                        co += 1
                    else:
                        mat += 1
                        o[1] += 1
                        if len(vi_du) < 20:
                            vi_du.append({"tep": p.name, "the": n.ma,
                                          "dong": n.line_start,
                                          "chu_thich": ct[n.line_start][:70],
                                          "khoi": n.ma in KHOI})
                di(n.than, muc + 1)
        di(rec.tree, 0)
    return {
        "ten": "Cửa 2 — chú thích cuối dòng phải còn, kể cả trên thẻ khối",
        "dat": mat == 0, "co": co, "mat": mat,
        "theo_the": {k: {"co_ct": v[0], "mat": v[1], "khoi": k in KHOI}
                     for k, v in sorted(theo_the.items())},
        "vi_du": vi_du,
    }


# ------------------------------------------------------------------- cửa 3
def cua_3_origin(kiem):
    """Origin phải so BẰNG NHAU trên hostname, không dò chuỗi con.

    Bản v1 dùng `"127.0.0.1" in origin`, nên http://127.0.0.1.evil.com lọt —
    gõ vào máy chủ đang chạy ra mã 200. Ở đây gọi thẳng hàm, không cần dựng
    máy chủ, nên cửa này chạy được trong CI.
    """
    class _Gia:
        def __init__(self, o):
            self.headers = {"Origin": o} if o else {}

    thu = [
        ("http://127.0.0.1:8088", True, "trang that"),
        ("http://localhost:8088", True, "trang that"),
        ("", True, "cung nguon, khong co Origin"),
        ("https://evil.example", False, "trang la"),
        ("http://127.0.0.1.evil.com", False, "ten mien GIA chua 127.0.0.1"),
        ("http://localhost.evil.com", False, "ten mien GIA chua localhost"),
        ("http://evil.com/?x=127.0.0.1", False, "127.0.0.1 nam trong query"),
        ("http://not-localhost.tld", False, "localhost la hau to"),
    ]
    ra, sai = [], 0
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


# ------------------------------------------------------------------- cửa 4
def cua_4_tu_kiem(doc, sinh_dong):
    """Bộ đọc phải TỰ KIỂM: thẻ nào tả sai nguồn thì phải là ma_tho.

    Thà hiện ra mã thô còn hơn lặng lẽ xoá `-> bool`. Cửa này đo đúng một
    điều: còn thẻ nào KHÔNG PHẢI ma_tho mà sinh lại không khớp nguồn không.
    """
    tong = sai = tho = 0
    theo_the = {}
    vi_du = []
    for p in _tep_py():
        dong = p.read_text(encoding="utf-8").splitlines()
        try:
            rec = doc(p)
        except Exception:
            continue

        def di(ns, muc):
            nonlocal tong, sai, tho
            for n in ns:
                if n.ma == "ma_tho":
                    tho += 1
                    di(n.than, muc + 1)
                    continue
                tong += 1
                o = theo_the.setdefault(n.ma, [0, 0])
                o[0] += 1
                if n.line_start is None:
                    sai += 1
                    o[1] += 1
                    di(n.than, muc + 1)
                    continue
                try:
                    ra = sinh_dong(n, _muc(n))
                except Exception:
                    ra = "<<khong sinh duoc>>"
                # thẻ khối chỉ chịu trách nhiệm dòng ĐẦU, thân là thẻ con
                if n.ma in KHOI:
                    that = dong[n.line_start - 1]
                else:
                    that = "\n".join(
                        dong[n.line_start - 1:(n.line_end or n.line_start)])
                if ra != that:
                    sai += 1
                    o[1] += 1
                    if len(vi_du) < 30:
                        vi_du.append({"tep": p.name, "the": n.ma,
                                      "dong": n.line_start,
                                      "goc": that.strip()[:90],
                                      "sinh": ra.strip()[:90]})
                di(n.than, muc + 1)
        di(rec.tree, 0)
    return {
        "ten": "Cửa 4 — thẻ tả sai nguồn phải bị hạ xuống ma_tho",
        "dat": sai == 0, "the_that": tong, "tho": tho, "sai": sai,
        "phu_song": round(100 * (tong - sai) / max(tong + tho, 1), 1),
        "theo_the": {k: {"tong": v[0], "sai": v[1]}
                     for k, v in sorted(theo_the.items(),
                                        key=lambda x: -x[1][0])},
        "vi_du": vi_du,
    }


def chay():
    """Chạy cả bốn cửa, ghi MỘT tệp JSON khoá đã sắp."""
    try:
        sys.path.insert(0, str(GOC))
        from core.the_v1 import (doc_tep_py_sang_cay_the,
                                 luu_cay_the_ra_tep_py, sinh_dong_the_don)
        from interface.the_api import kiem_tra_origin_hop_le
    except Exception as e:
        return None, "khong nap duoc core.the_v1 / interface.the_api: %r" % (e,)

    if not _tep_py():
        return None, "khong tim thay tep .py nao trong %s" % (THU_MUC,)

    cua = [
        cua_1_go_lai_y_cu(doc_tep_py_sang_cay_the, luu_cay_the_ra_tep_py),
        cua_2_chu_thich(doc_tep_py_sang_cay_the, sinh_dong_the_don),
        cua_3_origin(kiem_tra_origin_hop_le),
        cua_4_tu_kiem(doc_tep_py_sang_cay_the, sinh_dong_the_don),
    ]
    so = {
        "luc": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "kho": str(GOC),
        "thu_muc_quet": list(THU_MUC),
        "so_tep": len(_tep_py()),
        "dat_het": all(c["dat"] for c in cua),
        "cua": cua,
    }
    RA.mkdir(parents=True, exist_ok=True)
    (RA / "cua_cung.json").write_text(
        json.dumps(so, ensure_ascii=False, sort_keys=True, indent=1),
        encoding="utf-8")
    return so, ""


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    so, loi = chay()
    if so is None:
        print("KHONG DO DUOC: " + loi)
        return 2                       # khong do duoc, KHAC voi truot
    from bao_cao_cua_cung import in_bang, dung_trang, TRANG
    # doc LAI tu dia, khong dung `so` trong RAM: bang nguoi doc phai dung tu
    # dung so JSON da ghi (luat CLAUDE.md muc 5)
    tu_so = json.loads((RA / "cua_cung.json").read_text(encoding="utf-8"))
    in_bang(tu_so)
    TRANG.write_text(dung_trang(tu_so), encoding="utf-8")
    print("\nso   : " + str(RA / "cua_cung.json"))
    print("trang: " + str(TRANG))
    return 0 if tu_so["dat_het"] else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
