# -*- coding: utf-8 -*-
"""do_so_sanh_dong_kiem_tra_bo5.py — Chạy đo đối chiếu Bộ đề 5 giữa dong_kiem_tra=None vs dong_kiem_tra=de.dong.

Phục vụ Giao Antigravity Vòng 3 (26/08/2026):
1. Chạy trên bản đóng băng chuẩn (đầy đủ mọi thư mục, vượt qua cửa cứng kiem_tra_ban_dong_bang).
2. Tách bạch test đỏ thật vs lỗi nạp.
3. Đo so sánh 2 cột:
   - Cột A: dong_kiem_tra = None
   - Cột B: dong_kiem_tra = d["dong"]
4. Thu thập và phân tích chi tiết các ca "không có test đỏ nào trace được" (11 ca nghi vấn).
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

from core.trace_runtime import chot_test_can_trace, _chay_pytest_tim_test_do_phan_loai
from kiem_ban_dong_bang import kiem_tra_ban_dong_bang
from truy_nguoc_gia_tri import truy_nguoc
from do_truy_nguoc_ngoai_ho import dong_loi_trong_ma

DE_PATH = GOC / "experiments" / "evidence_sprint" / "de_ngoai_ho_5.json"


def chay_mot_de_che_do(d: dict, dung_dong: bool) -> dict:
    tam_goc = Path(tempfile.mkdtemp(prefix="slice_bo5_"))
    tam = tam_goc / "kho"
    try:
        shutil.copytree(GOC, tam, ignore=shutil.ignore_patterns(
            "venv", ".venv*", ".git", "__pycache__", ".pytest_cache",
            "data", "_rac", "*.pyc", "node_modules"))
        (tam / "data").mkdir(exist_ok=True)
        (tam / d["tep"]).write_text(d["ma"], encoding="utf-8")

        # Cửa cứng kiểm tra bản đóng băng trước khi đo
        ok_gate, err_gate = kiem_tra_ban_dong_bang(tam, GOC, [d["tep_test"]], verbose=False)
        if not ok_gate:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": err_gate,
                "so_test_do_that": 0,
                "so_loi_nap": 0,
                "loi_nap_chitiet": [],
            }

        # Phân loại test đỏ thật vs lỗi nạp
        ds_do_that, ds_loi_nap = _chay_pytest_tim_test_do_phan_loai(d["tep_test"], cwd=tam)
        if ds_loi_nap and not ds_do_that:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": f"lỗi nạp ({len(ds_loi_nap)} lỗi collection/import)",
                "so_test_do_that": 0,
                "so_loi_nap": len(ds_loi_nap),
                "loi_nap_chitiet": ds_loi_nap,
            }

        dk = d.get("dong") if dung_dong else None
        ten, so_do, ds = chot_test_can_trace(
            d["tep"], d["tep_test"], dong_kiem_tra=dk, cwd=tam)
        if not ten or not ds:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": "không có test đỏ nào trace được",
                "so_test_do_that": len(ds_do_that),
                "so_loi_nap": len(ds_loi_nap),
                "loi_nap_chitiet": ds_loi_nap,
            }

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
            "so_test_do_that": len(ds_do_that),
            "so_loi_nap": len(ds_loi_nap),
            "loi_nap_chitiet": ds_loi_nap,
            "so_dong_da_chay": len(da_chay),
            "so_dong_chuoi": len(dong_chuoi),
            "dai_chuoi": len(kq["chuoi"]),
            "dong_moc": (kq["chuoi"][0].get("dong") if kq.get("chuoi") else None),
            "cac_dong_chuoi": sorted(set(dong_chuoi)),
            "dong_trong_ma": dl,
            "trace_toi_dong_loi": toi_dong_loi,
            "dong_loi_trong_chuoi": any(x in dong_chuoi for x in dl),
            "thu_hep": round(len(dong_chuoi) / len(da_chay), 3) if da_chay else None,
            "model_calls": kq.get("model_calls", 0),
            "external_submit": kq.get("external_submit", False),
        }
    except Exception as e:
        return {
            "trang_thai": "khong_do_duoc",
            "vi_sao": str(e)[:120],
            "so_test_do_that": 0,
            "so_loi_nap": 0,
            "loi_nap_chitiet": [],
        }
    finally:
        shutil.rmtree(tam_goc, ignore_errors=True)


def tinh_chi_so(so: list) -> dict:
    do_duoc = [x for x in so if x["trang_thai"] != "khong_do_duoc"]
    khong_do = len(so) - len(do_duoc)
    noi = [x for x in do_duoc if x.get("so_dong_chuoi", 0) > 1]
    im = [x for x in do_duoc if x.get("so_dong_chuoi", 0) <= 1]
    dung = sum(1 for x in noi if x.get("dong_loi_trong_chuoi"))
    sai = len(noi) - dung
    cx = (dung / len(noi)) if noi else 0.0
    dp = len(noi) / len(do_duoc) if do_duoc else 0.0
    th = [x["thu_hep"] for x in noi if x.get("thu_hep") is not None]
    mt = statistics.median(th) if th else 1.0

    return {
        "tong_so": len(so),
        "do_duoc": len(do_duoc),
        "khong_do_duoc": khong_do,
        "ti_le_khong_do_duoc": round(khong_do / len(so), 3) if so else 0.0,
        "tra_loi": len(noi),
        "im_lang": len(im),
        "dung": dung,
        "sai": sai,
        "chinh_xac": round(cx, 3),
        "do_phu": round(dp, 3),
        "thu_hep_trung_vi": round(mt, 3),
    }


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if not DE_PATH.is_file():
        print(f"Lỗi: Không tìm thấy {DE_PATH}")
        return 2

    raw = json.loads(DE_PATH.read_text(encoding="utf-8"))
    de = raw["de"]
    print(f"=== BẮT ĐẦU ĐO ĐỐI CHIẾU BỘ ĐỀ 5 ({len(de)} ĐỀ) ===")
    print("Môi trường: Bản đóng băng chuẩn đầy đủ (có interface/, conftest.py, pytest.ini)\n")

    kq_none = []
    kq_dong = []

    t0 = time.monotonic()
    for idx, d in enumerate(de, 1):
        t_start = time.monotonic()
        # Chạy bản dong_kiem_tra = None
        r_none = chay_mot_de_che_do(d, dung_dong=False)
        r_none.update({"tep": d["tep"], "muc": d["muc"], "ho": d["ho"], "mo_ta": d["mo_ta"], "dong": d["dong"]})
        kq_none.append(r_none)

        # Chạy bản dong_kiem_tra = d["dong"]
        r_dong = chay_mot_de_che_do(d, dung_dong=True)
        r_dong.update({"tep": d["tep"], "muc": d["muc"], "ho": d["ho"], "mo_ta": d["mo_ta"], "dong": d["dong"]})
        kq_dong.append(r_dong)

        t_elapsed = round(time.monotonic() - t_start, 1)
        tt_none = r_none["trang_thai"]
        tt_dong = r_dong["trang_thai"]
        print(
            f"[{idx:2d}/{len(de):2d}] {Path(d['tep']).name:<16} {d['ho']:<11} d.{d['dong']:<4} | "
            f"None: {tt_none:<13} (do_that={r_none.get('so_test_do_that', 0)}, nap={r_none.get('so_loi_nap', 0)}) | "
            f"Dong: {tt_dong:<13} | {t_elapsed}s"
        )

    t_total = round((time.monotonic() - t0) / 60, 2)
    print(f"\nHoàn tất 66 đề trong {t_total} phút.\n")

    # Lưu kết quả
    out_dir = GOC / "data" / "evidence_sprint"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "so_sanh_bo5_none.json").write_text(
        json.dumps({"ket_qua": kq_none}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out_dir / "so_sanh_bo5_dong.json").write_text(
        json.dumps({"ket_qua": kq_dong}, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # Tính toán chỉ số
    cs_none = tinh_chi_so(kq_none)
    cs_dong = tinh_chi_so(kq_dong)

    print("=" * 75)
    print("  BẢNG SO SÁNH BỘ ĐỀ 5: dong_kiem_tra = None  vs  dong_kiem_tra = de.dong")
    print("=" * 75)
    print(f"  {'Chỉ số':<30} | {'dong_kiem_tra=None':<20} | {'dong_kiem_tra=de.dong':<20}")
    print("-" * 75)
    print(f"  {'Tổng số ca':<30} | {cs_none['tong_so']:<20} | {cs_dong['tong_so']:<20}")
    print(f"  {'Đo được':<30} | {cs_none['do_duoc']:<20} | {cs_dong['do_duoc']:<20}")
    print(f"  {'Không đo được':<30} | {cs_none['khong_do_duoc']:<20} | {cs_dong['khong_do_duoc']:<20}")
    print(f"  {'Tỉ lệ không đo được':<30} | {cs_none['ti_le_khong_do_duoc']:.1%} ({cs_none['khong_do_duoc']}/{cs_none['tong_so']}){'':<7} | {cs_dong['ti_le_khong_do_duoc']:.1%} ({cs_dong['khong_do_duoc']}/{cs_dong['tong_so']})")
    print(f"  {'Số ca trả lời':<30} | {cs_none['tra_loi']:<20} | {cs_dong['tra_loi']:<20}")
    print(f"  {'  - Trả lời ĐÚNG':<30} | {cs_none['dung']:<20} | {cs_dong['dung']:<20}")
    print(f"  {'  - Trả lời SAI':<30} | {cs_none['sai']:<20} | {cs_dong['sai']:<20}")
    print(f"  {'Chính xác khi nó nói':<30} | {cs_none['chinh_xac']:<20} | {cs_dong['chinh_xac']:<20}")
    print(f"  {'Độ phủ':<30} | {cs_none['do_phu']:<20} | {cs_dong['do_phu']:<20}")
    print(f"  {'Thu hẹp (trung vị)':<30} | {cs_none['thu_hep_trung_vi']:<20} | {cs_dong['thu_hep_trung_vi']:<20}")
    print("=" * 75)

    # Phân tích 11 ca nghi vấn (không có test đỏ nào trace được)
    print("\n" + "=" * 75)
    print("  MỔ XẺ TỪNG CA 'KHÔNG ĐO ĐƯỢC' TRÊN BẢN ĐÓNG BĂNG ĐẦY ĐỦ")
    print("=" * 75)
    ca_kdd = [x for x in kq_none if x["trang_thai"] == "khong_do_duoc"]
    print(f"  Tổng số ca không đo được thực tế: {len(ca_kdd)}/{len(de)}\n")

    for i, c in enumerate(ca_kdd, 1):
        print(f"  [{i}] Tệp: {c['tep']} | mục: {c['muc']} | họ: {c['ho']} | dòng: {c['dong']}")
        print(f"      Mô tả: {c['mo_ta']}")
        print(f"      Vì sao: {c.get('vi_sao')}")
        print(f"      Test đỏ thật: {c.get('so_test_do_that', 0)}, Lỗi nạp: {c.get('so_loi_nap', 0)}")
        if c.get("loi_nap_chitiet"):
            print(f"      Chi tiết lỗi nạp: {c['loi_nap_chitiet']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
