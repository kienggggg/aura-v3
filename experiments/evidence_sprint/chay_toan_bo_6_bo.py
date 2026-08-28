# -*- coding: utf-8 -*-
"""chay_toan_bo_6_bo.py — Chạy đo tuần tự cả 6 bộ đề truy ngược ngoài họ trên máy rảnh."""
import io
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Đảm bảo stdout / stderr luôn là UTF-8 trên Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

GOC = Path(__file__).resolve().parent.parent.parent
PY = sys.executable

BO_DE = [
    (1, []),
    (2, ["--bo2"]),
    (3, ["--bo3"]),
    (4, ["--bo4"]),
    (5, ["--bo5"]),
    (6, ["--bo6"]),
]

def sao_luu_va_xoa_so_cu(so_bo: int):
    hau = "" if so_bo == 1 else f"_{so_bo}"
    tep_so = GOC / "data" / "evidence_sprint" / f"truy_nguoc_ngoai_ho{hau}.json"
    if tep_so.exists():
        backup_name = GOC / "data" / "evidence_sprint" / f"_backup_truoc_90s_bo_{so_bo}.json"
        if not backup_name.exists():
            shutil.copy2(tep_so, backup_name)
            print(f"[Sao lưu] Đã sao lưu {tep_so.name} -> {backup_name.name}", flush=True)
        tep_so.unlink()
        print(f"[Làm sạch] Đã xoá {tep_so.name} để đo sạch 100%", flush=True)

def doc_ket_qua_so(so_bo: int):
    hau = "" if so_bo == 1 else f"_{so_bo}"
    tep_so = GOC / "data" / "evidence_sprint" / f"truy_nguoc_ngoai_ho{hau}.json"
    if not tep_so.exists():
        return None
    try:
        raw = json.loads(tep_so.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return raw.get("ket_qua", [])
        elif isinstance(raw, list):
            return raw
        return []
    except Exception as e:
        print(f"Lỗi đọc {tep_so}: {e}", flush=True)
        return None

def tong_hop_so(data: list):
    if not data:
        return {}
    tong = len(data)
    do_duoc = [x for x in data if x.get("trang_thai") == "do_duoc"]
    khong_do = tong - len(do_duoc)
    
    noi = [x for x in do_duoc if x.get("so_dong_chuoi", 0) > 1]
    im = [x for x in do_duoc if x.get("so_dong_chuoi", 0) <= 1]
    dung = sum(1 for x in noi if x.get("dong_loi_trong_chuoi"))
    sai = len(noi) - dung
    
    im_dung = sum(1 for x in im if x.get("dong_loi_trong_chuoi"))
    im_sai = len(im) - im_dung
    
    cx = (dung / len(noi)) if noi else 0.0
    dp = len(noi) / len(do_duoc) if do_duoc else 0.0
    
    # 5 ngưỡng
    dat_cx = cx >= 0.60
    dat_im = im_sai >= im_dung
    dat_dp = dp >= 0.25
    
    import statistics
    th = [x["thu_hep"] for x in noi if x.get("thu_hep") is not None]
    mt = statistics.median(th) if th else 1.0
    dat_th = mt <= 0.50
    dat_mc = all(x.get("model_calls", 0) == 0 for x in do_duoc)
    
    dat_ca_5 = dat_cx and dat_im and dat_dp and dat_th and dat_mc
    
    return {
        "tong": tong,
        "do_duoc": len(do_duoc),
        "khong_do": khong_do,
        "tra_loi": len(noi),
        "dung": dung,
        "sai": sai,
        "im_lang": len(im),
        "im_dung": im_dung,
        "im_sai": im_sai,
        "chinh_xac": cx,
        "do_phu": dp,
        "thu_hep_median": mt,
        "dat_ca_5": dat_ca_5,
        "dat_cx": dat_cx,
        "dat_im": dat_im,
        "dat_dp": dat_dp,
        "dat_th": dat_th,
        "dat_mc": dat_mc,
    }

def main():
    t_start_all = time.time()
    print("=" * 78, flush=True)
    print("BẮT ĐẦU CHẠY ĐO TUẦN TỰ CẢ 6 BỘ ĐỀ TRUY NGƯỢC NGOÀI HỌ (TRAN_TRACE_GIAY=90)", flush=True)
    print(f"Python: {PY}", flush=True)
    print(f"Bắt đầu lúc: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 78, flush=True)
    
    ket_qua = {}
    
    for so_bo, args in BO_DE:
        t0 = time.time()
        sao_luu_va_xoa_so_cu(so_bo)
        print(f"\n[{time.strftime('%H:%M:%S')}] >>> BẮT ĐẦU BỘ ĐỀ {so_bo} (args: {args})...", flush=True)
        cmd = [PY, "-X", "utf8", str(GOC / "experiments" / "evidence_sprint" / "do_truy_nguoc_ngoai_ho.py")] + args
        
        proc = subprocess.run(cmd, cwd=str(GOC), capture_output=False)
        dt = time.time() - t0
        print(f"[{time.strftime('%H:%M:%S')}] <<< BỘ ĐỀ {so_bo} HOÀN TẤT sau {dt/60:.1f} phút (exit code: {proc.returncode})", flush=True)
        
        data = doc_ket_qua_so(so_bo)
        if data:
            thong_ke = tong_hop_so(data)
            thong_ke["thoi_gian_giay"] = dt
            ket_qua[so_bo] = thong_ke
        else:
            print(f"CẢNH BÁO: Không đọc được dữ liệu sổ bộ {so_bo}", flush=True)
    
    dt_all = time.time() - t_start_all
    print("\n" + "=" * 82, flush=True)
    print(f"TỔNG HỢP KẾT QUẢ CẢ 6 BỘ ĐỀ VỚI TRẦN 90S (Tổng thời gian: {dt_all/3600:.2f} giờ)", flush=True)
    print("=" * 82, flush=True)
    print(f"{'Bộ':<6} | {'Chính xác':<10} | {'Trả lời':<10} | {'Im lặng (Sai/Đúng)':<20} | {'Không đo':<10} | {'5 Ngưỡng':<12}")
    print("-" * 82, flush=True)
    for so_bo in sorted(ket_qua.keys()):
        r = ket_qua[so_bo]
        cx_str = f"{r['chinh_xac']:.2f}"
        tl_str = f"{r['tra_loi']}/{r['do_duoc']}"
        im_str = f"{r['im_sai']} sai / {r['im_dung']} đúng"
        kd_str = f"{r['khong_do']}"
        ng_str = "ĐẠT CẢ NĂM" if r['dat_ca_5'] else ("Trượt CX" if not r['dat_cx'] else "Trượt khác")
        print(f"Bộ {so_bo:<3} | {cx_str:<10} | {tl_str:<10} | {im_str:<20} | {kd_str:<10} | {ng_str:<12}", flush=True)
    print("=" * 82, flush=True)

if __name__ == "__main__":
    main()
