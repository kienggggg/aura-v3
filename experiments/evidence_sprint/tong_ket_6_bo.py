# -*- coding: utf-8 -*-
import io
import json
import pathlib
import statistics
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

def phan_tich_tep(p_name):
    p = pathlib.Path('data/evidence_sprint') / p_name
    if not p.exists(): return None
    data = json.loads(p.read_text('utf-8'))['ket_qua']
    tong = len(data)
    do_duoc = [x for x in data if x.get('trang_thai') != 'khong_do_duoc']
    khong_do = tong - len(do_duoc)
    noi = [x for x in do_duoc if x.get('so_dong_chuoi', 0) > 1]
    im = [x for x in do_duoc if x.get('so_dong_chuoi', 0) <= 1]
    dung = sum(1 for x in noi if x.get('dong_loi_trong_chuoi'))
    sai = len(noi) - dung
    im_dung = sum(1 for x in im if x.get('dong_loi_trong_chuoi'))
    im_sai = len(im) - im_dung
    cx = (dung / len(noi)) if noi else 0.0
    dp = len(noi) / len(do_duoc) if do_duoc else 0.0
    th = [x['thu_hep'] for x in noi if x.get('thu_hep') is not None]
    mt = statistics.median(th) if th else 1.0
    dat_cx = cx >= 0.60
    dat_im = im_sai >= im_dung
    dat_dp = dp >= 0.25
    dat_th = mt <= 0.50
    dat_mc = all(x.get('model_calls', 0) == 0 for x in do_duoc)
    dat_ca_5 = dat_cx and dat_im and dat_dp and dat_th and dat_mc
    return {
        'tong': tong, 'do_duoc': len(do_duoc), 'khong_do': khong_do,
        'noi': len(noi), 'dung': dung, 'sai': sai,
        'im_sai': im_sai, 'im_dung': im_dung,
        'cx': cx, 'dp': dp, 'th': mt,
        'dat_ca_5': dat_ca_5, 'dat_cx': dat_cx, 'dat_th': dat_th
    }

print("=" * 86)
print(f"{'Bộ đề':<8} | {'Chính xác':<10} | {'Trả lời':<10} | {'Im lặng (Bỏ Sai / Bỏ Đúng)':<28} | {'Không đo':<10} | {'Đánh giá'}")
print("-" * 86)
bo_files = [
    (1, 'truy_nguoc_ngoai_ho.json'),
    (2, 'truy_nguoc_ngoai_ho_2.json'),
    (3, 'truy_nguoc_ngoai_ho_3.json'),
    (4, 'truy_nguoc_ngoai_ho_4.json'),
    (5, 'truy_nguoc_ngoai_ho_5.json'),
    (6, 'truy_nguoc_ngoai_ho_6.json')
]
for bo, fn in bo_files:
    r = phan_tich_tep(fn)
    cx_str = f"{r['cx']:.2f}"
    tl_str = f"{r['noi']}/{r['do_duoc']}"
    im_str = f"{r['im_sai']} sai / {r['im_dung']} đúng"
    kd_str = f"{r['khong_do']}"
    if r['dat_ca_5']:
        ng_str = "🎉 ĐẠT CẢ 5 NGƯỠNG"
    elif not r['dat_cx']:
        ng_str = "Trượt ngưỡng CX"
    elif not r['dat_th']:
        ng_str = "Trượt ngưỡng Thu hẹp"
    else:
        ng_str = "Trượt khác"
    print(f"Bộ {bo:<5} | {cx_str:<10} | {tl_str:<10} | {im_str:<28} | {kd_str:<10} | {ng_str}")
print("=" * 86)
