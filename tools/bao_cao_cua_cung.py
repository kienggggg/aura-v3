# -*- coding: utf-8 -*-
"""Dựng bảng người đọc TỪ tệp JSON của `do_cua_cung_the.py`, không dựng từ RAM.

Luật CLAUDE.md mục 5: bảng phải dựng lại từ chính JSON đã ghi. In riêng là mở
đường cho bảng nói một đằng sổ ghi một nẻo — đúng lỗi đã bắt được ở sổ soát
link 11/08, nơi 30 tóm tắt đúng nội dung mà gắn sai URL.

    venv\\Scripts\\python.exe -X utf8 tools\\bao_cao_cua_cung.py
"""
from __future__ import annotations

import html
import io
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO = GOC / "data" / "the_v1" / "cua_cung.json"
TRANG = GOC / "data" / "the_v1" / "bao_cao.html"


def _e(x) -> str:
    return html.escape(str(x), quote=True)


# Tên hiển thị nạp từ sổ JSON (sổ lấy từ BO_THE_V1). Mã `gan` là khoá trong
# máy nên buộc không dấu; chữ người đọc thấy phải là "Gán".
TEN_THE: dict = {}


def _ten(ma: str) -> str:
    t = TEN_THE.get(ma)
    return ("%s (%s)" % (t, ma)) if t else str(ma)


def in_bang(so: dict) -> None:
    """Bảng cho người đọc trên terminal."""
    TEN_THE.update(so.get("ten_the") or {})
    print("=" * 68)
    print("  BỐN CỬA NGHIỆM THU — APP LẬP TRÌNH BẰNG THẺ")
    print("  %s · %d tệp .py · %s" % (so["luc"], so["so_tep"],
                                      "/".join(so["thu_muc_quet"])))
    print("=" * 68)
    for c in so["cua"]:
        dau = "ĐẠT " if c["dat"] else "TRƯỢT"
        print("\n[%s] %s" % (dau, c["ten"]))
        if "the" in c:
            t = c["the"] or 1
            print("    thẻ thử           : %d" % c["the"])
            print("    y hệt từng byte   : %5d  (%.1f%%)"
                  % (c["y_het_byte"], 100 * c["y_het_byte"] / t))
            print("    giữ đúng nghĩa    : %5d  (%.1f%%)"
                  % (c["nguyen"], 100 * c["nguyen"] / t))
            print("    ĐỔI NGHĨA ÂM THẦM : %5d  (%.1f%%)"
                  % (c["doi_nghia"], 100 * c["doi_nghia"] / t))
            print("    VỠ CÚ PHÁP        : %5d  (%.1f%%)"
                  % (c["vo_cu_phap"], 100 * c["vo_cu_phap"] / t))
            print("    tệp dính          : %d/%d" % (c["tep_dinh"], c["tep_tong"]))
        elif "mat" in c:
            print("    dòng có chú thích do thẻ thật quản: %d" % (c["co"] + c["mat"]))
            print("    giữ được: %d   MẤT: %d" % (c["co"], c["mat"]))
            for k, v in c["theo_the"].items():
                if v["co_ct"]:
                    print("      %-22s %2d có, %2d mất %s"
                          % (_ten(k), v["co_ct"], v["mat"],
                             "(thẻ khối)" if v["khoi"] else ""))
        elif "thu" in c:
            for t in c["thu"]:
                print("      %-32s mong %-5s thật %-5s  %s"
                      % (t["origin"][:32], t["mong"], t["that"],
                         "đạt" if t["dat"] else "*** LỌT ***"))
        elif "the_that" in c:
            print("    thẻ thật          : %d  (tả sai %d)" % (c["the_that"], c["sai"]))
            print("    mảnh ma_tho       : %d" % c["tho"])
            print("    kho tả bằng thẻ   : %.1f%%" % c["phu_song"])
            if "phu_song_dong" in c:
                print("    dòng tả bằng thẻ  : %.1f%%" % c["phu_song_dong"])
            for k, v in c["theo_the"].items():
                if v["sai"]:
                    print("      %-22s %4d thẻ, %4d tả SAI" % (_ten(k), v["tong"], v["sai"]))
    print("\n" + "=" * 68)
    # 01/09/2026 — câu này TỪNG đóng cứng "bao_cao.html", nhưng `do_cua_cung_the`
    # ghi ra `bao_cao_cst.html`. Người đọc mở đúng tệp được chỉ thì thấy một bản
    # báo cáo từ 23/08 và tưởng đó là kết quả vừa chạy. Suy tên từ `bo_doc` đang
    # có trong sổ, không chép tay.
    ten_trang = ("bao_cao_cst.html" if "the_cst" in str(so.get("bo_doc", ""))
                 else "bao_cao.html")
    print("  TỔNG: %s" % ("ĐẠT CẢ BỐN CỬA" if so["dat_het"]
                          else f"CHƯA ĐẠT — xem data/the_v1/{ten_trang}"))
    print("=" * 68)


_CSS = """
:root{--nen:#f7f7f5;--the:#fff;--chu:#1a1a18;--mo:#6b6b63;--vien:#e3e3dd;
--dat:#166534;--dat-n:#dcfce7;--truot:#9f1239;--truot-n:#ffe4e6;--vang:#854d0e;
--vang-n:#fef3c7;--ma:#f4f4f0;--xanh:#1d4ed8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--nen:#16161a;--the:#1f1f25;--chu:#eceef2;--mo:#9a9aa4;--vien:#33333c;
--dat:#86efac;--dat-n:#14311f;--truot:#fda4af;--truot-n:#3d1220;--vang:#fcd34d;
--vang-n:#3a2c07;--ma:#26262e;--xanh:#93b4fd}}
:root[data-theme="dark"]{--nen:#16161a;--the:#1f1f25;--chu:#eceef2;--mo:#9a9aa4;
--vien:#33333c;--dat:#86efac;--dat-n:#14311f;--truot:#fda4af;--truot-n:#3d1220;
--vang:#fcd34d;--vang-n:#3a2c07;--ma:#26262e;--xanh:#93b4fd}
*{box-sizing:border-box}
body{margin:0;background:var(--nen);color:var(--chu);
font:15px/1.6 "Segoe UI",system-ui,-apple-system,sans-serif}
.bao{max-width:1080px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}
.duoi{color:var(--mo);font-size:13px;margin-bottom:26px}
.tong{padding:16px 20px;border-radius:10px;font-weight:600;margin-bottom:28px;
border:1px solid var(--vien)}
.tong.ok{background:var(--dat-n);color:var(--dat)}
.tong.no{background:var(--truot-n);color:var(--truot)}
.cua{background:var(--the);border:1px solid var(--vien);border-radius:10px;
padding:18px 20px;margin-bottom:18px}
.cua h2{font-size:16px;margin:0 0 12px;display:flex;gap:10px;align-items:center}
.nhan{font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;
letter-spacing:.04em;flex:none}
.nhan.ok{background:var(--dat-n);color:var(--dat)}
.nhan.no{background:var(--truot-n);color:var(--truot)}
.o{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.so{background:var(--ma);border-radius:8px;padding:10px 14px;min-width:118px}
.so b{display:block;font-size:20px;line-height:1.2}
.so span{font-size:11px;color:var(--mo);text-transform:uppercase;
letter-spacing:.05em}
.so.xau b{color:var(--truot)}
.so.tot b{color:var(--dat)}
.cuon{overflow-x:auto;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--vien);
vertical-align:top}
th{font-size:11px;color:var(--mo);text-transform:uppercase;letter-spacing:.05em}
code{font:12.5px/1.5 "Cascadia Mono",Consolas,monospace;background:var(--ma);
padding:1px 5px;border-radius:4px;white-space:pre-wrap;word-break:break-word}
.x{color:var(--truot);font-weight:600}
.v{color:var(--dat);font-weight:600}
.mo{color:var(--mo)}
details{margin-top:12px}
summary{cursor:pointer;font-size:13px;color:var(--xanh);padding:4px 0}
.mui{border-left:3px solid var(--truot);padding-left:12px;margin:10px 0}
.mui .g{color:var(--mo)}
"""


def _cua_1(c) -> str:
    t = c["the"] or 1
    o = ('<div class="o">'
         '<div class="so"><b>%d</b><span>thẻ thử</span></div>'
         '<div class="so tot"><b>%d</b><span>y hệt từng byte</span></div>'
         '<div class="so tot"><b>%d</b><span>giữ đúng nghĩa</span></div>'
         '<div class="so xau"><b>%d</b><span>đổi nghĩa âm thầm</span></div>'
         '<div class="so xau"><b>%d</b><span>vỡ cú pháp</span></div>'
         '<div class="so"><b>%d/%d</b><span>tệp dính</span></div></div>'
         % (c["the"], c["y_het_byte"], c["nguyen"], c["doi_nghia"],
            c["vo_cu_phap"], c["tep_dinh"], c["tep_tong"]))
    o += ('<p class="mo">Y hệt byte %.1f%% · giữ đúng nghĩa %.1f%% · '
          'đổi nghĩa %.1f%% · vỡ cú pháp %.1f%%. Phần chênh giữa hai cột đầu là '
          'những chỗ khác byte mà chương trình không đổi.</p>'
          % (100 * c["y_het_byte"] / t, 100 * c["nguyen"] / t,
             100 * c["doi_nghia"] / t, 100 * c["vo_cu_phap"] / t))
    h = ['<details><summary>Tệp nào dính nặng nhất</summary><div class="cuon">'
         '<table><tr><th>tệp</th><th>thẻ</th><th>làm lệch</th></tr>']
    for x in c["theo_tep"][:20]:
        if not x.get("hong"):
            break
        h.append('<tr><td><code>%s</code></td><td>%d</td>'
                 '<td class="x">%d</td></tr>'
                 % (_e(x["tep"]), x["the"], x["hong"]))
    h.append("</table></div></details>")
    if c["vi_du"]:
        h.append('<details><summary>Dòng cụ thể bị hỏng</summary>'
                 '<div class="cuon"><table>'
                 '<tr><th>tệp:dòng</th><th>thẻ</th><th>kiểu</th>'
                 '<th>dòng gốc</th></tr>')
        for v in c["vi_du"][:25]:
            h.append('<tr><td><code>%s:%s</code></td><td>%s</td>'
                     '<td class="x">%s</td><td><code>%s</code></td></tr>'
                     % (_e(v["tep"]), _e(v["dong"]), _e(_ten(v["the"])),
                        _e(v["loai"]), _e(v["goc"])))
        h.append("</table></div></details>")
    return o + "".join(h)


def _cua_2(c) -> str:
    o = ('<div class="o">'
         '<div class="so tot"><b>%d</b><span>giữ được</span></div>'
         '<div class="so xau"><b>%d</b><span>MẤT chú thích</span></div></div>'
         % (c["co"], c["mat"]))
    h = ['<div class="cuon"><table><tr><th>loại thẻ</th><th>có chú thích</th>'
         '<th>mất</th><th></th></tr>']
    for k, v in c["theo_the"].items():
        if not v["co_ct"]:
            continue
        h.append('<tr><td><code>%s</code></td><td>%d</td>'
                 '<td class="%s">%d</td><td class="mo">%s</td></tr>'
                 % (_e(_ten(k)), v["co_ct"], "x" if v["mat"] else "v", v["mat"],
                    "thẻ khối" if v["khoi"] else "thẻ lẻ"))
    h.append("</table></div>")
    for v in c["vi_du"][:8]:
        h.append('<div class="mui"><code>%s:%s</code> · thẻ <code>%s</code>%s'
                 '<br><span class="g">mất:</span> <code>%s</code></div>'
                 % (_e(v["tep"]), _e(v["dong"]), _e(_ten(v["the"])),
                    " (thẻ khối)" if v["khoi"] else "", _e(v["chu_thich"])))
    return o + "".join(h)


def _cua_3(c) -> str:
    h = ['<div class="cuon"><table><tr><th>Origin gửi lên</th><th>phải</th>'
         '<th>thật</th><th>kết</th><th></th></tr>']
    for t in c["thu"]:
        h.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td>'
                 '<td class="%s">%s</td><td class="mo">%s</td></tr>'
                 % (_e(t["origin"]),
                    "cho" if t["mong"] else "chặn",
                    "cho" if t["that"] else "chặn",
                    "v" if t["dat"] else "x",
                    "đạt" if t["dat"] else "LỌT",
                    _e(t["ghi"])))
    h.append("</table></div>")
    return "".join(h)


def _cua_4(c) -> str:
    o = ('<div class="o">'
         '<div class="so"><b>%d</b><span>thẻ thật</span></div>'
         '<div class="so xau"><b>%d</b><span>tả SAI nguồn</span></div>'
         '<div class="so"><b>%d</b><span>mảnh ma_tho</span></div>'
         '<div class="so"><b>%.0f%%</b><span>kho tả bằng thẻ</span></div></div>'
         % (c["the_that"], c["sai"], c["tho"], c["phu_song"]))
    h = ['<div class="cuon"><table><tr><th>loại thẻ</th><th>tổng</th>'
         '<th>tả sai</th><th>tả đúng</th></tr>']
    for k, v in c["theo_the"].items():
        h.append('<tr><td><code>%s</code></td><td>%d</td>'
                 '<td class="%s">%d</td><td>%.0f%%</td></tr>'
                 % (_e(_ten(k)), v["tong"], "x" if v["sai"] else "v", v["sai"],
                    100 * (v["tong"] - v["sai"]) / max(v["tong"], 1)))
    h.append("</table></div>")
    if c["vi_du"]:
        h.append('<details><summary>Gốc so với thứ thẻ sinh ra</summary>')
        for v in c["vi_du"][:14]:
            h.append('<div class="mui"><code>%s:%s</code> · <code>%s</code>'
                     '<br><span class="g">gốc :</span> <code>%s</code>'
                     '<br><span class="g">%s:</span> <code>%s</code></div>'
                     % (_e(v["tep"]), _e(v["dong"]), _e(_ten(v["the"])),
                        _e(v["goc"]),
                        "sinh" if "sinh" in v else "ô sửa",
                        _e(v.get("sinh", v.get("o", "")))))
        h.append("</details>")
    return o + "".join(h)


def dung_trang(so: dict) -> str:
    """Dựng HTML TỪ sổ JSON — không nhận dữ liệu nào khác."""
    TEN_THE.update(so.get("ten_the") or {})
    than = []
    ve = (_cua_1, _cua_2, _cua_3, _cua_4)
    for i, c in enumerate(so["cua"]):
        than.append(
            '<section class="cua"><h2><span class="nhan %s">%s</span>%s</h2>%s'
            '</section>'
            % ("ok" if c["dat"] else "no",
               "ĐẠT" if c["dat"] else "TRƯỢT",
               _e(c["ten"]), ve[i](c) if i < len(ve) else ""))
    return (
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Bốn cửa nghiệm thu — app thẻ</title>'
        '<style>%s</style><div class="bao">'
        '<h1>Bốn cửa nghiệm thu — app lập trình bằng THẺ</h1>'
        '<p class="duoi">%s · %d tệp <code>.py</code> trong %s · '
        'bảng này dựng từ <code>data/the_v1/cua_cung.json</code></p>'
        '<div class="tong %s">%s</div>%s'
        '<p class="duoi">Chạy lại: '
        '<code>venv\\Scripts\\python.exe -X utf8 tools\\do_cua_cung_the.py</code>'
        '</p></div>'
        % (_CSS, _e(so["luc"]), so["so_tep"],
           _e("/".join(so["thu_muc_quet"])),
           "ok" if so["dat_het"] else "no",
           "ĐẠT CẢ BỐN CỬA — app dùng được trên mã thật"
           if so["dat_het"] else
           "CHƯA ĐẠT — chưa dùng app này để sửa mã thật",
           "".join(than)))


def main() -> int:
    """In bảng và dựng trang HTML từ sổ bốn cửa. Mã thoát 0 đạt / 1 trượt / 2 chưa có sổ."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if not SO.is_file():
        print("KHÔNG ĐO ĐƯỢC: chưa có %s" % SO)
        return 2
    so = json.loads(SO.read_text(encoding="utf-8"))
    in_bang(so)
    TRANG.parent.mkdir(parents=True, exist_ok=True)
    TRANG.write_text(dung_trang(so), encoding="utf-8")
    print("\ntrang xem: %s" % TRANG)
    return 0 if so["dat_het"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
