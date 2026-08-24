# -*- coding: utf-8 -*-
"""do_truy_nguoc_ngoai_ho.py — chấm truy ngược giá trị trên đúng 64 đề ngoài họ.

Bảng điểm đã có sẵn từ 23/08 nên không tự chấm mình được:

    E1 trên 64 đề này    tim_thay 0/64 · dung_nghia 0/64

HAI THƯỚC KHÁC NHAU — nói trước:

    E1        trả lời "vá thế này"      -> chấm bằng `dung_nghia` (AST khớp gốc)
    truy ngược trả lời "nhìn mấy dòng"  -> chấm bằng "dòng lỗi có trong chuỗi"

Cột `dung_nghia` của tệp này VĨNH VIỄN là 0 vì nó không sinh bản vá nào. Ai đem
số của hai bên đặt cạnh nhau mà không nói rõ là đã đổi thước giữa chừng.

LUẬT CHỌN TEST — đăng ký trước khi chạy, và KHÔNG lộ đáp án:

    Trong các test ĐỎ, chọn test chạy qua NHIỀU DÒNG NHẤT của tệp đích.
    KHÔNG truyền `dong_kiem_tra` cho `chot_test_can_trace` — truyền vào là
    mách nó dòng lỗi, và mọi con số sau đó thành vô nghĩa.

NGƯỠNG ĐẶT TRƯỚC:

    1. dòng lỗi nằm trong chuỗi truy ngược          >= 32/64
    2. chiều dài chuỗi, trung vị                    <= 8 dòng
    3. ca có chuỗi RỖNG mà vẫn báo tìm thấy         = 0
    4. thu hẹp so với "mọi dòng đã chạy", trung vị  <= 0,50
       (24/08: bản kế hoạch đầu tiên viết ngưỡng này là "phải dưới 13 ứng viên
        của E1" — SAI, vì 13 là số ỨNG VIÊN còn đây đếm số DÒNG. Hai đơn vị
        khác nhau. Sửa thành phép so cùng đơn vị, trên đúng cùng một vết.)
    5. model_calls = 0, external_submit = false

    Ngưỡng 4 là ngưỡng thật. Ba cái đầu một mình thì "trả về cả hàm" cũng qua.

Mã thoát: 0 đạt · 1 đo được mà không đạt · 2 không đo được.
"""
from __future__ import annotations

import ast
import io
import json
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.trace_runtime import chot_test_can_trace          # noqa: E402
from truy_nguoc_gia_tri import truy_nguoc                    # noqa: E402

_BO2 = "--bo2" in sys.argv
DE = GOC / "experiments" / "evidence_sprint" / (
    "de_ngoai_ho_2.json" if _BO2 else "de_ngoai_ho.json")
RA = GOC / "data" / "evidence_sprint" / (
    "truy_nguoc_ngoai_ho_2.json" if _BO2 else "truy_nguoc_ngoai_ho.json")

NGUONG_TRONG_CHUOI = 32
NGUONG_DAI_CHUOI = 8
NGUONG_THU_HEP = 0.50

# ===========================================================================
# NGƯỠNG CHO LUẬT IM LẶNG — đăng ký 24/08/2026, TRƯỚC khi bộ đề 2 chạy xong
# ===========================================================================
# Luật: chuỗi chỉ có mốc bắt đầu (không lùi được bước nào) thì trả "không
# biết", đừng chỉ vào một dòng.
#
# Luật này rút ra TỪ bộ đề 1, nên chấm nó trên bộ đề 1 là vòng tròn. Bộ đề 2
# dùng BỐN TỆP KHÁC HẲN (secret_guard · user_memory · doc_so_phien ·
# kiem_tien), không trùng tệp nào với bộ 1.
#
# Bộ 1 dự đoán, nếu luật im lặng đã bật: trả lời 26/63 ca, đúng 17 sai 9,
# tức chính xác 0,65 và 0 ca chỉ sai một dòng.
#
#   1. chính xác khi nó NÓI (đúng/số ca trả lời)   >= 0,60
#   2. số ca chỉ sai ĐÚNG MỘT dòng                 = 0
#   3. độ phủ (số ca trả lời / tổng)               >= 0,25
#   4. thu hẹp trung vị, trên ca có trả lời         <= 0,50
#   5. model_calls                                  = 0
#
# Ngưỡng 1 và 3 KÉO NGƯỢC NHAU: im lặng nhiều hơn thì chính xác lên mà độ phủ
# xuống. Phải đạt cả hai, nếu không thì "im lặng" chỉ là cách trốn phép đo.
# Ngưỡng 2 không phải phát hiện gì — nó chỉ kiểm bản cài đặt làm đúng điều nó
# hứa.
NGUONG_CHINH_XAC = 0.60
NGUONG_DO_PHU = 0.25


def dong_loi_trong_ma(d: dict) -> List[int]:
    """Dòng bị gieo lỗi, tính theo TOẠ ĐỘ CỦA `ma` — không tin trường `dong`.

    24/08: trường `dong` trong `de_ngoai_ho.json` đếm theo TỆP GỐC, còn `ma` là
    bản `ast.unparse` đã rụng hết chú thích. Đo đề #0 (`core/may_tinh.py`):

        tệp gốc      321 dòng   `dong` = 39
        `ma`         194 dòng   chỗ đổi thật ở dòng 25

    Cùng một câu lệnh `tach = unicodedata.normalize(...)`, hai hệ toạ độ. Chấm
    bằng số 39 trên tệp 194 dòng thì mọi con số sau đó là rác — mà nó vẫn ra
    một bảng trông rất gọn.

    Nên tính lại bằng cách so `ast.unparse(gốc)` với `ma`: cùng một bộ chuẩn
    hoá, nên lệch ở đâu là chỗ gieo ở đó.
    """
    try:
        goc = (GOC / d["tep"]).read_text(encoding="utf-8")
        chuan = ast.unparse(ast.parse(goc)).splitlines()
    except Exception:                                        # noqa: BLE001
        return []
    moi = d["ma"].splitlines()
    khac = [i + 1 for i, (a, b) in enumerate(zip(chuan, moi)) if a != b]
    if len(chuan) != len(moi):
        # Lệch số dòng: lấy thêm phần đuôi thừa/thiếu
        khac += list(range(min(len(chuan), len(moi)) + 1, len(moi) + 1))
    return khac


def chay_mot_de(d: dict) -> dict:
    tam_goc = Path(tempfile.mkdtemp(prefix="slice_"))
    tam = tam_goc / "kho"
    try:
        shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
            "venv", ".venv*", ".git", "__pycache__", ".pytest_cache",
            "data", "_rac", "*.pyc", "node_modules"))
        (tam / "data").mkdir(exist_ok=True)
        (tam / d["tep"]).write_text(d["ma"], encoding="utf-8")

        ten, so_do, ds = chot_test_can_trace(
            d["tep"], d["tep_test"], dong_kiem_tra=None, cwd=tam)
        if not ten or not ds:
            return {"trang_thai": "khong_do_duoc",
                    "vi_sao": "không có test đỏ nào trace được"}

        # Luật chọn đã đăng ký: nhiều dòng nhất của tệp đích.
        tr = max(ds, key=lambda r: len(r.dong_da_chay or []))
        da_chay = list(tr.dong_da_chay or [])
        dl = dong_loi_trong_ma(d)
        toi_dong_loi = any(x in da_chay for x in dl)

        kq = truy_nguoc(tr.cac_su_kien, d["ma"])
        dong_chuoi = kq["dong"]
        return {
            "trang_thai": kq["trang_thai"],
            "ten_test": tr.ten_test,
            "so_test_do_khac": so_do,
            "so_dong_da_chay": len(da_chay),
            "so_dong_chuoi": len(dong_chuoi),
            "dai_chuoi": len(kq["chuoi"]),
            "dong_trong_ma": dl,
            "trace_toi_dong_loi": toi_dong_loi,
            "dong_loi_trong_chuoi": any(x in dong_chuoi for x in dl),
            "thu_hep": round(len(dong_chuoi) / len(da_chay), 3) if da_chay else None,
            "model_calls": kq.get("model_calls", 0),
            "external_submit": kq.get("external_submit", False),
        }
    except Exception as e:                                   # noqa: BLE001
        return {"trang_thai": "khong_do_duoc", "vi_sao": str(e)[:120]}
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if not DE.is_file():
        print("KHÔNG ĐO ĐƯỢC: chưa có %s" % DE.name)
        return 2
    de = json.loads(DE.read_text(encoding="utf-8"))["de"]
    # `--bo2` cũng là một argv, nên không được lấy argv[1] làm số đề.
    so_arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(so_arg[0]) if so_arg else len(de)
    de = de[:n]

    so = []
    if RA.is_file():
        so = json.loads(RA.read_text(encoding="utf-8")).get("ket_qua", [])
        xong = {(x["tep"], x["muc"]) for x in so}
        de = [x for x in de if (x["tep"], x["muc"]) not in xong]

    RA.parent.mkdir(parents=True, exist_ok=True)
    print("  %d đề — truy ngược giá trị, không có model\n" % len(de))
    t0 = time.monotonic()

    for i, d in enumerate(de, 1):
        t1 = time.monotonic()
        r = chay_mot_de(d)
        r.update({"tep": d["tep"], "muc": d["muc"], "ho": d["ho"],
                  "mo_ta": d["mo_ta"], "dong": d["dong"],
                  "giay": round(time.monotonic() - t1, 1)})
        so.append(r)
        RA.write_text(json.dumps(
            {"_vi_sao": "Truy nguoc gia tri tren 64 de NGOAI ho cua _Lat",
             "_thuoc_do": "cham bang 'dong loi co trong chuoi', KHONG phai 'va dung'",
             "ket_qua": so}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  [%2d/%2d] %-18s %-11s dòng %-8s | tới=%-5s trong chuỗi=%-5s "
              "| %3s→%-3s | %.1fs"
              % (i, len(de), Path(d["tep"]).name, d["ho"],
                 ",".join(map(str, r.get("dong_trong_ma") or [])) or "?",
                 r.get("trace_toi_dong_loi"), r.get("dong_loi_trong_chuoi"),
                 r.get("so_dong_da_chay"), r.get("so_dong_chuoi"), r["giay"]))

    print("\n  tổng %.1f phút" % ((time.monotonic() - t0) / 60))
    return cham(so)


def cham(so: list) -> int:
    do_duoc = [x for x in so if x["trang_thai"] != "khong_do_duoc"]
    khong_do = len(so) - len(do_duoc)
    trong_chuoi = sum(1 for x in do_duoc if x.get("dong_loi_trong_chuoi"))
    toi_noi = [x for x in do_duoc if x.get("trace_toi_dong_loi")]
    trong_chuoi_khi_toi = sum(1 for x in toi_noi if x.get("dong_loi_trong_chuoi"))
    dai = [x["dai_chuoi"] for x in do_duoc if x.get("dai_chuoi")]
    th = [x["thu_hep"] for x in do_duoc if x.get("thu_hep") is not None]
    rong_ma_bao = sum(1 for x in do_duoc
                      if x.get("so_dong_chuoi", 0) <= 1 and x.get("dong_loi_trong_chuoi"))

    print("\n" + "=" * 68)
    print("  TRUY NGƯỢC GIÁ TRỊ trên %d đề NGOÀI họ" % len(so))
    print("=" * 68)
    print("  thước đo: DÒNG LỖI CÓ TRONG CHUỖI — không phải 'vá đúng'")
    print("  E1 trên đúng bộ đề này: tìm thấy 0/64 · vá đúng 0/64")
    print("  truy ngược: vá đúng 0/%d — nó KHÔNG sinh bản vá nào" % len(so))
    print("-" * 68)
    md = statistics.median(dai) if dai else 0
    mt = statistics.median(th) if th else 1.0
    hang = [
        ("1. dòng lỗi trong chuỗi", "%d/%d" % (trong_chuoi, len(so)),
         ">= %d" % NGUONG_TRONG_CHUOI, trong_chuoi >= NGUONG_TRONG_CHUOI),
        ("2. dài chuỗi, trung vị", "%.0f" % md,
         "<= %d" % NGUONG_DAI_CHUOI, md <= NGUONG_DAI_CHUOI),
        ("3. chuỗi rỗng mà vẫn báo", "%d" % rong_ma_bao, "= 0", rong_ma_bao == 0),
        ("4. thu hẹp, trung vị", "%.2f" % mt,
         "<= %.2f" % NGUONG_THU_HEP, mt <= NGUONG_THU_HEP),
        ("5. model_calls", "%d" % sum(x.get("model_calls", 0) for x in do_duoc),
         "= 0", all(x.get("model_calls", 0) == 0 for x in do_duoc)),
    ]
    for ten, thuc, nguong, ok in hang:
        print("  %-28s %-8s %-10s %s" % (ten, thuc, nguong, "ĐẠT" if ok else "TRƯỢT"))
    print("-" * 68)
    print("  trace KHÔNG tới dòng lỗi : %d/%d  (phần này không phải lỗi của"
          % (len(do_duoc) - len(toi_noi), len(do_duoc)))
    print("                              phép truy ngược, mà của khâu chọn test)")
    if toi_noi:
        print("  khi trace CÓ tới dòng lỗi: %d/%d nằm trong chuỗi"
              % (trong_chuoi_khi_toi, len(toi_noi)))
    if khong_do:
        print("  KHÔNG ĐO ĐƯỢC           : %d" % khong_do)
    print("  sổ: %s" % RA)
    print("=" * 68)

    ok_cu = all(h[3] for h in hang)
    ok_im = cham_im_lang(do_duoc)

    if khong_do == len(so):
        print("  KHÔNG ĐO ĐƯỢC")
        return 2
    return 0 if (ok_cu and ok_im) else 1


def cham_im_lang(do_duoc: list) -> bool:
    """Chấm chế độ IM LẶNG trên cùng dữ liệu — không cần chạy lại vết."""
    # "không lùi được bước nào" = chuỗi chỉ có mốc bắt đầu
    noi = [x for x in do_duoc if x.get("so_dong_chuoi", 0) > 1]
    im = [x for x in do_duoc if x.get("so_dong_chuoi", 0) <= 1]
    dung = sum(1 for x in noi if x.get("dong_loi_trong_chuoi"))
    sai = len(noi) - dung
    # GIÁ CỦA VIỆC IM LẶNG. Bản đầu tôi đặt ngưỡng 2 là "số ca chỉ sai đúng một
    # dòng = 0" — vô nghĩa, vì chế độ im lặng KHÔNG trả lời một dòng nữa, nên
    # nó bằng 0 theo cấu trúc. (Và bản mã đầu còn viết `and False` nên nó bằng
    # 0 kể cả khi cấu trúc không bảo đảm. Cửa không hỏng được, đúng bệnh của cả
    # tuần này.)
    #
    # Đo cái đáng đo: im lặng NÉM ĐI những gì. Mỗi ca bị im lặng đáng lẽ là một
    # câu trả lời — đúng hoặc sai. Im lặng chỉ đáng nếu nó bỏ nhiều câu SAI hơn
    # câu ĐÚNG.
    im_dung = sum(1 for x in im if x.get("dong_loi_trong_chuoi"))
    im_sai = len(im) - im_dung
    th = [x["thu_hep"] for x in noi if x.get("thu_hep") is not None]
    cx = (dung / len(noi)) if noi else 0.0
    dp = len(noi) / len(do_duoc) if do_duoc else 0.0
    mt = statistics.median(th) if th else 1.0

    print()
    print("=" * 68)
    print("  CHẾ ĐỘ IM LẶNG — không lùi được bước nào thì nói KHÔNG BIẾT")
    print("=" * 68)
    print("  luật này rút ra TỪ bộ đề 1; đây là %s"
          % ("BỘ ĐỀ 2, bốn tệp khác hẳn — bằng chứng độc lập" if _BO2
             else "CHÍNH bộ đề 1 — chỉ là kiểm bản cài đặt, KHÔNG phải bằng chứng"))
    print("-" * 68)
    print("  trả lời          : %d/%d ca" % (len(noi), len(do_duoc)))
    print("  im lặng          : %d/%d ca" % (len(im), len(do_duoc)))
    print("  trong số trả lời : đúng %d · SAI %d" % (dung, sai))
    print("  giá của im lặng  : ném đi %d câu ĐÚNG và %d câu SAI"
          % (im_dung, im_sai))
    print("-" * 68)
    hang = [
        ("1. chính xác khi nó nói", "%.2f" % cx,
         ">= %.2f" % NGUONG_CHINH_XAC, cx >= NGUONG_CHINH_XAC),
        ("2. im lặng bỏ SAI >= bỏ ĐÚNG", "%d/%d" % (im_sai, im_dung),
         "sai >= đúng", im_sai >= im_dung),
        ("3. độ phủ", "%.2f" % dp, ">= %.2f" % NGUONG_DO_PHU, dp >= NGUONG_DO_PHU),
        ("4. thu hẹp, trung vị", "%.2f" % mt,
         "<= %.2f" % NGUONG_THU_HEP, mt <= NGUONG_THU_HEP),
        ("5. model_calls", "%d" % sum(x.get("model_calls", 0) for x in do_duoc),
         "= 0", all(x.get("model_calls", 0) == 0 for x in do_duoc)),
    ]
    for ten, thuc, ng, ok in hang:
        print("  %-28s %-8s %-10s %s" % (ten, thuc, ng, "ĐẠT" if ok else "TRƯỢT"))
    print("=" * 68)
    return all(h[3] for h in hang)


if __name__ == "__main__":
    sys.exit(main())
