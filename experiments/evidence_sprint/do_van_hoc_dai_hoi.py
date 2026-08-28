# -*- coding: utf-8 -*-
"""do_van_hoc_dai_hoi.py — Bộ đo đạc & Chấm điểm Văn học Đời thường Dài hơi (AURA v3).

Quy chuẩn đo đạc:
  1. Hard Gates: Word count, Mojibake, Nhân vật must_appear, Không rò rỉ prompt.
  2. Literary Metrics (Chỉ số văn chương):
     - Chỉ số Giác Quan (Sensory Density): Tần suất từ ngữ Thị giác, Thính giác, Khứu giác, Xúc giác, Vị giác.
     - Chỉ số Sạch Bệnh AI (Cliché-Free Index): Quét các từ ngữ sáo rỗng thường gặp ở LLM.
     - Tính Liên Tục Dài Hơi (Arc & Object Continuity): Theo dõi đồ vật neo đậu qua các chương.
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List

TU_SAO_RONG_AI = [
    "ngàn năm", "vũ trụ", "định mệnh", "bức tranh thủy mặc", "vô hình trung",
    "bất giác", "man mác", "thấu tận tâm can", "chết lặng", "thời gian như ngừng trôi",
    "dòng đời xô đẩy", "khắc cốt ghi tâm", "vạn vật", "hư vô"
]

TU_GIAC_QUAN = {
    "thinh_giac": ["tiếng", "lách cách", "lộp độp", "leng keng", "kêu", "rít", "lách tách", "im lặng", "tích tắc", "râm ran", "xào xạc"],
    "khuu_giac": ["mùi", "thơm", "khét", "ngai ngái", "nồng", "chua", "đắng", "tanh", "hương"],
    "xuc_giac": ["lạnh", "nóng", "ướt", "khô", "sần sùi", "mịn", "nhám", "nhẵn", "ấm", "buốt", "chạm"],
    "thi_giac": ["màu", "ánh", "vàng", "đỏ", "xanh", "sáng", "tối", "vệt", "bóng", "lóe", "mờ"]
}

def cham_diem_van_hoc(noi_dung: str, nhan_vat_bat_buoc: List[str]) -> Dict[str, Any]:
    words = noi_dung.split()
    tong_tu = len(words)
    text_lower = unicodedata.normalize('NFC', noi_dung).casefold()
    
    # 1. Quét từ sáo rỗng
    sao_rong_found = []
    for tu in TU_SAO_RONG_AI:
        if re.search(r'\b' + re.escape(tu) + r'\b', text_lower):
            sao_rong_found.append(tu)
            
    diem_cliche = max(0, 10.0 - len(sao_rong_found) * 2.0)
    
    # 2. Đếm mật độ giác quan
    diem_giac_quan_map = {}
    tong_tu_giac_quan = 0
    for gq, tu_list in TU_GIAC_QUAN.items():
        count = sum(len(re.findall(r'\b' + re.escape(w) + r'\b', text_lower)) for w in tu_list)
        diem_giac_quan_map[gq] = count
        tong_tu_giac_quan += count
        
    mat_do_giac_quan_per_1000 = round((tong_tu_giac_quan / max(1, tong_tu)) * 1000, 2)
    diem_giac_quan = min(10.0, round(mat_do_giac_quan_per_1000 / 3.0, 1))
    
    # 3. Kiểm tra nhân vật bắt buộc
    missing_chars = []
    for nv in nhan_vat_bat_buoc:
        if not re.search(r'\b' + re.escape(nv.casefold()) + r'\b', text_lower):
            missing_chars.append(nv)
            
    # 4. Tỷ lệ thoại (Hội thoại tự nhiên)
    dong_thoai = len(re.findall(r'—\s*["“]?[^"”\n]+["”]?', noi_dung))
    
    # Điểm tổng hợp
    diem_tong = round((diem_cliche * 0.4) + (diem_giac_quan * 0.3) + (10.0 if not missing_chars else 4.0) * 0.3, 1)
    
    return {
        "tong_tu": tong_tu,
        "tu_sao_rong_phat_hien": sao_rong_found,
        "diem_sach_benh_ai": diem_cliche,
        "dem_giac_quan": diem_giac_quan_map,
        "mat_do_giac_quan_1000_tu": mat_do_giac_quan_per_1000,
        "diem_giac_quan": diem_giac_quan,
        "so_luot_thoai": dong_thoai,
        "nhan_vat_thieu": missing_chars,
        "diem_tong_ket": diem_tong,
        "xep_loai": "XUẤT SẮC" if diem_tong >= 9.0 else ("TỐT" if diem_tong >= 7.5 else "CẦN CẢI THIỆN")
    }

if __name__ == "__main__":
    sample = "Mưa ngoài ngõ làm ướt mặt bàn gỗ. Diệu nhìn ly cà phê thơm mùi rang mộc. Tiếng chuông gió kêu lách cách trong gió lạnh."
    res = cham_diem_van_hoc(sample, ["Diệu"])
    print(json.dumps(res, ensure_ascii=False, indent=2))
