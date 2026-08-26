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

from core.trace_runtime import chot_test_can_trace, _chay_pytest_tim_test_do_phan_loai  # noqa: E402
from kiem_ban_dong_bang import kiem_tra_ban_dong_bang         # noqa: E402
from truy_nguoc_gia_tri import truy_nguoc                    # noqa: E402

_BO6 = "--bo6" in sys.argv
_BO5 = "--bo5" in sys.argv
_BO4 = "--bo4" in sys.argv
_BO3 = "--bo3" in sys.argv
_BO2 = "--bo2" in sys.argv
_CO_DONG_KIEM_TRA = "--dong-kiem-tra" in sys.argv
_SO_BO = 6 if _BO6 else (5 if _BO5 else (4 if _BO4 else (3 if _BO3 else (2 if _BO2 else 1))))
_HAU = "" if _SO_BO == 1 else "_%d" % _SO_BO
DE = GOC / "experiments" / "evidence_sprint" / ("de_ngoai_ho%s.json" % _HAU)
RA = GOC / "data" / "evidence_sprint" / ("truy_nguoc_ngoai_ho%s.json" % _HAU)

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

# ===========================================================================
# BỘ ĐỀ 4 — ngưỡng đăng ký 25/08/2026, TRƯỚC khi bộ đề 4 sinh xong
# ===========================================================================
# Giả thuyết đem ra thử: chuỗi truy ngược trượt vì nó KHÔNG BƯỚC QUA NỔI RANH
# GIỚI HÀM. Gộp bộ 1 + bộ 3 đo được:
#
#     lỗi CÙNG hàm với mốc bắt đầu   42/49 = 0,86
#     lỗi KHÁC hàm với mốc bắt đầu    1/31 = 0,03
#
# Giả thuyết ấy SINH RA TỪ bộ 1 và bộ 3, nên đo lại trên chính chúng là vòng
# tròn. Bộ 4 dùng bốn tệp chưa đụng tới: chat_runtime · local_first_gateway ·
# cua_hoc_vet · nhip_thuc_thi.
#
# CẢNH BÁO ĐĂNG KÝ TRƯỚC — bộ 4 có thể ra điểm cao mà KHÔNG nhờ bản sửa nào.
# Đo tỉ lệ "hàm được gọi từ một hàm khác trong cùng tệp", tức đúng hình dạng
# đẻ ra ca khác-hàm, TRƯỚC khi sinh đề:
#
#     bộ 1  19/30 = 63%      bộ 3  26/36 = 72%
#     bộ 2  11/22 = 50%      bộ 4  17/35 = 49%   <- THẤP NHẤT trong bốn bộ
#
# Nên con số TỔNG của bộ 4 không phải bằng chứng cho bản sửa: nó có thể lên
# chỉ vì bộ này ít ca khác-hàm hơn. Lần trước tôi đoán sai đúng kiểu này (đoán
# bộ 3 "dễ ăn" vì nhiều ca sập; đo ra 47% so 43%, chênh 4 điểm, vô nghĩa).
#
# Vì vậy CON SỐ DUY NHẤT được tính là bằng chứng: chính xác trên ca KHÁC HÀM.
#
#   A. chính xác trên ca KHÁC HÀM      >= 0,50   (hiện 1/31 = 0,03)
#   B. chính xác trên ca CÙNG HÀM      >= 0,80   (hiện 42/49 = 0,86 — bản sửa
#                                                 KHÔNG được làm hỏng chỗ đang chạy)
#   C. chính xác tổng khi nó nói       >= 0,60   (giữ nguyên ngưỡng cũ)
#   D. độ phủ                          >= 0,25   (giữ nguyên)
#   E. model_calls                     = 0       (giữ nguyên)
#
# Ngưỡng A đặt ở 0,50 chứ không phải 0,86: 0,86 là mức của ca cùng hàm, đem
# nó làm đích cho ca khác hàm là lấy hy vọng làm ngưỡng. 0,50 vẫn là gấp 16
# lần con số 0,03 hiện thời, đủ để không nhầm với nhiễu.
#
# NẾU BỘ 4 CÓ QUÁ ÍT CA KHÁC HÀM thì ngưỡng A KHÔNG ĐO ĐƯỢC — phải nói là
# không đo được, không được lấy ngưỡng C đạt mà bảo giả thuyết đúng.
NGUONG_KHAC_HAM = 0.50
NGUONG_CUNG_HAM = 0.80
# Dưới ngưỡng này thì mẫu quá nhỏ để kết luận A -> báo KHÔNG ĐO ĐƯỢC.
TOI_THIEU_CA_KHAC_HAM = 10

# ===========================================================================
# BỘ ĐỀ 6 — ngưỡng đăng ký 25/08/2026, TRƯỚC khi bộ đề 6 sinh xong
# ===========================================================================
# Bộ 6 là `core/lat_nguoc.py` — TỆP DUY NHẤT còn lại trong kho. 16 tệp kia
# đã dùng cho năm bộ trước; `redact`/`paths` không có test; `trace_runtime`
# là chính module đang được đo nên dùng là vòng tròn.
#
# Trước hôm nay `lat_nguoc.py` cũng không dùng được vì 0 test. Đó là lý do
# viết test cho nó. Nay: 70 test, 123 chỗ gieo được.
#
# HÌNH DẠNG — đo TRƯỚC khi sinh đề, như đã làm với bộ 4 và bộ 5:
#
#     579 dòng · 14 hàm · hàm nội bộ 7/14 = 50%
#
#     bộ 1  63%      bộ 3  72%      bộ 5  74–82%  (nhắm đích)
#     bộ 2  50%      bộ 4  49%      bộ 6  50%     <- TRUNG TÍNH
#
# Bộ 6 gần y hệt bộ 4 — tức KHÔNG nhắm đích. Đó chính là thứ cần: bộ 4 không
# trả lời nổi câu hỏi chính vì chỉ có 8 ca sâu (dưới mức tối thiểu 10), còn
# bộ 5 không trả lời được vì nó chọn tệp theo chính giả thuyết đang kiểm.
#
# CÂU BỘ 6 TRẢ LỜI: **cỗ máy truy ngược đã dùng được chưa, trên mã bình thường?**
# Con số hiện có cho câu ấy là bộ 4 sạch: 0,56 — dưới ngưỡng 0,60.
#
# CẢNH BÁO ĐĂNG KÝ TRƯỚC, vì nó dễ bị nuốt sau khi thấy kết quả:
#
# 1. Bộ 6 chỉ có MỘT tệp. Năm bộ trước có 3–4 tệp, và cả năm lần đều cho thấy
#    kết quả phân tán rất mạnh theo tệp (`khay_the` 9% so với `chat_contract`
#    91% trong cùng bộ 3). Một tệp nghĩa là KHÔNG có phương sai giữa tệp để
#    mà nhìn — con số ra sẽ là con số CỦA TỆP NÀY, không phải của "mã bình
#    thường" nói chung. Phải nói ra chứ không được im.
#
# 2. `lat_nguoc.py` nhập `core/trace_runtime.py` — chính mô-đun mà phép đo
#    dùng để lấy vết. Gieo lỗi vào `lat_nguoc` KHÔNG làm hỏng `trace_runtime`,
#    nên không vòng tròn. Nhưng nếu thấy tỉ lệ `khong_do_duoc` cao bất thường
#    thì phải kiểm chỗ này trước khi kết luận.
#
#   A. chính xác trên ca SÂU           >= 0,50   (giữ nguyên bộ 4 và bộ 5)
#   B. ca NÔNG máy MỚI >= máy CŨ trên CHÍNH bộ 6 — so cặp, cùng bộ đề
#   C. chính xác tổng khi nó nói       >= 0,60   (giữ nguyên)
#   D. độ phủ                          >= 0,25   (giữ nguyên)
#   E. model_calls                     = 0       (giữ nguyên)
#
# Không nới một con số nào của bộ 4 hay bộ 5. Nếu dưới 10 ca sâu thì ngưỡng A
# KHÔNG ĐO ĐƯỢC — báo là không đo được, y như bộ 4, không lấy C đắp vào.

# ===========================================================================
# BỘ ĐỀ 5 — ngưỡng đăng ký 25/08/2026, TRƯỚC khi bộ đề 5 sinh xong
# ===========================================================================
# BỘ ĐỀ NHẮM ĐÍCH. Bộ 4 chỉ ra 8 ca khác-hàm, dưới mức tối thiểu 10 đã đăng
# ký, nên ngưỡng A KHÔNG ĐO ĐƯỢC — đúng điều đã cảnh báo trước khi sinh đề
# (bộ 4 có tỉ lệ hàm nội bộ 49%, thấp nhất bốn bộ).
#
# Bộ 5 CỐ Ý chọn tệp có tỉ lệ hàm nội bộ cao, tức chọn theo chính giả thuyết
# đang kiểm. Điều đó KHÔNG làm phép đo vô giá trị, nhưng làm HẸP câu nó trả
# lời lại:
#
#     TRẢ LỜI ĐƯỢC : khi có nhiều ca khác-hàm thì bản sửa làm được gì
#     KHÔNG TRẢ LỜI: cỗ máy đã dùng được chưa, trên mã bình thường
#
# Ai đọc con số của bộ 5 mà bỏ dòng trên là đọc sai. Muốn biết "dùng được
# chưa" thì con số phải lấy từ bộ chọn KHÔNG theo giả thuyết — bộ 1 tới 4.
#
# SỬA THƯỚC ĐO — bắt được 25/08 khi chạy bộ 4 bằng CẢ HAI cỗ máy.
#
# Ngưỡng A và B của bộ 4 phân loại ca theo "dòng lỗi có cùng hàm với MỐC BẮT
# ĐẦU không". Mốc bắt đầu là thứ CỖ MÁY chọn, mà bản sửa `_moc_bat_dau` đã
# dời mốc — nên số ca mỗi loại đổi theo cỗ máy:
#
#     máy CŨ   khác hàm 14 ca · cùng hàm 22 ca
#     máy MỚI  khác hàm  8 ca · cùng hàm 28 ca
#
# "B tụt 0,82 -> 0,68" vì thế là so HAI TẬP CA KHÁC NHAU, không phải so hai
# cỗ máy. Hai ngưỡng ấy VÔ HIỆU — không phải trượt, không phải đạt, mà là
# hỏng thước. Cùng họ với §4 "đừng tự chấm điểm bằng dò chuỗi con": ở đó thước
# đo bắt nhầm chuỗi, ở đây thước đo phụ thuộc chính thứ nó đang chấm.
#
# Thay bằng thuộc tính CỦA CA, tất định, không đụng tới cỗ máy:
#
#     ca SÂU  = dòng lỗi nằm trong một hàm ĐƯỢC GỌI TỪ MỘT HÀM KHÁC cùng tệp
#     ca NÔNG = còn lại
#
# Chấm lại bộ 4 bằng thước này (cùng 8 ca, cùng 28 ca, chỉ cỗ máy đổi):
#
#     máy CŨ   ca sâu 1/8 = 0,12    ca nông 17/28 = 0,61    tổng 0,50
#     máy MỚI  ca sâu 3/8 = 0,38    ca nông 17/28 = 0,61    tổng 0,56
#
# Bản sửa giúp đúng chỗ dự đoán và không làm hỏng chỗ đang chạy. Nhưng 8 ca
# thì quá ít để kết luận — đó là lý do có bộ 5.
#
#   A. chính xác trên ca SÂU           >= 0,50   (bộ 4 máy mới: 0,38 trên 8 ca)
#   B. ca NÔNG máy MỚI không được THẤP HƠN ca NÔNG máy CŨ trên CHÍNH bộ 5
#      — so cặp, cùng bộ đề, chỉ cỗ máy đổi. Không đặt ngưỡng tuyệt đối nữa,
#      vì con số tuyệt đối của ca nông đổi theo bộ đề chứ không theo cỗ máy.
#   (giữ nguyên C, D, E bên dưới)
#
#   [VÔ HIỆU, giữ lại để thấy vết] A cũ. chính xác ca KHÁC HÀM  >= 0,50
#   B. chính xác trên ca CÙNG HÀM      >= 0,80   (giữ nguyên)
#   C. chính xác tổng khi nó nói       >= 0,60   (giữ nguyên)
#   D. độ phủ                          >= 0,25   (giữ nguyên)
#   E. model_calls                     = 0       (giữ nguyên)
#
# Không nới một con số nào của bộ 4. Bộ 5 dễ hơn cho giả thuyết ở chỗ nó cho
# ĐỦ CA để chấm, không phải ở chỗ hạ ngưỡng.
#
# ĐĂNG KÝ TRƯỚC MỘT ĐIỀU NỮA, vì nó dễ bị nuốt sau khi thấy kết quả: nếu
# ngưỡng A đạt mà ngưỡng B vẫn dưới 0,80 thì bản sửa ĐỔI CHỖ HỎNG chứ không
# sửa được gì — chữa ca khác-hàm bằng cách làm hỏng ca cùng-hàm. Phải báo là
# TRƯỢT, không được báo "A đạt".

# ===========================================================================
# BỘ ĐỀ 3 — ngưỡng đăng ký 25/08/2026, TRƯỚC khi bộ đề 3 sinh xong
# ===========================================================================
# Giả thuyết đang kiểm: `_moc_bat_dau` cũ chỉ nhận ra "chương trình chết" khi
# cú gỡ ngăn xếp nằm ở CUỐI vết. Bộ đề 2 bác bỏ giả định ấy — mã có lớp
# `try/except Exception` bọc ngoài thì cú chết nằm GIỮA vết:
#
#   bộ 2, chỉ nhóm "có trả lời"   doc_so_phien 6/10 · kiem_tien 8/9   (thuần)
#                                  secret_guard 2/9 · user_memory 3/11 (tích hợp)
#
# Bản mới quét MỌI dãy `tra_ve` liên tiếp, không chỉ dãy cuối.
#
# Bộ đề 3 dùng BỐN TỆP LẠI KHÁC HẲN cả bộ 1 lẫn bộ 2 (chat_contract ·
# khay_the · nho_lai · omega). Đây là bằng chứng độc lập THỨ HAI — luật rút
# ra từ bộ 2, nên chấm trên bộ 2 là vòng tròn.
#
#   1. chính xác khi nó NÓI          >= 0,60   (bộ 2 bản cũ: 0,49 — TRƯỢT)
#   2. im lặng bỏ câu SAI >= câu ĐÚNG
#   3. độ phủ                        >= 0,25
#   4. thu hẹp trung vị              <= 0,50
#   5. model_calls                    = 0
#
# Giữ NGUYÊN năm ngưỡng của bộ 2, không nới một con số nào. Nếu bản sửa thật
# sự đúng thì chính con số 0,49 kia phải tự vượt lên; nới ngưỡng để nó "đạt"
# là tự lừa mình.
#
# CẢNH BÁO nếu bộ 3 ĐẠT: mới là hai bộ độc lập liên tiếp, KHÔNG phải "đã
# giải quyết xong". `CLAUDE.md` §4 — ba điểm khớp không chứng minh được điểm
# thứ tư.


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


def chay_mot_de(d: dict, dung_dong: bool = False) -> dict:
    tam_goc = Path(tempfile.mkdtemp(prefix="slice_"))
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
            return {"trang_thai": "khong_do_duoc", "vi_sao": err_gate, "so_test_do_that": 0, "so_loi_nap": 0}

        # Phân loại test đỏ thật vs lỗi nạp
        ds_do_that, ds_loi_nap = _chay_pytest_tim_test_do_phan_loai(d["tep_test"], cwd=tam)
        if ds_loi_nap and not ds_do_that:
            return {
                "trang_thai": "khong_do_duoc",
                "vi_sao": f"lỗi nạp ({len(ds_loi_nap)} lỗi collection/import)",
                "so_test_do_that": 0,
                "so_loi_nap": len(ds_loi_nap),
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
            "so_dong_da_chay": len(da_chay),
            "so_dong_chuoi": len(dong_chuoi),
            "dai_chuoi": len(kq["chuoi"]),
            # 25/08: ghi them MOC BAT DAU va CAC DONG CHUOI. Khong co hai
            # truong nay thi khong doi chieu duoc "loi nam trong ham nao so
            # voi ham chuoi dang di" — da phai chay lai ca bo mot lan chi de
            # lay chung. Ban ghi truoc 25/08 khong co: rong nghia la CU.
            "dong_moc": (kq["chuoi"][0].get("dong") if kq.get("chuoi") else None),
            "cac_dong_chuoi": sorted(set(dong_chuoi)),
            "dong_trong_ma": dl,
            "trace_toi_dong_loi": toi_dong_loi,
            "dong_loi_trong_chuoi": any(x in dong_chuoi for x in dl),
            "thu_hep": round(len(dong_chuoi) / len(da_chay), 3) if da_chay else None,
            "model_calls": kq.get("model_calls", 0),
            "external_submit": kq.get("external_submit", False),
        }
    except Exception as e:                                   # noqa: BLE001
        return {"trang_thai": "khong_do_duoc", "vi_sao": str(e)[:120], "so_test_do_that": 0, "so_loi_nap": 0}
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

    if so and de:
        print("  ***  ĐO MỘT PHẦN — BẢNG DƯỚI TRỘN SỐ CŨ VỚI SỐ MỚI  ***")
        print("  %d mục đọc từ sổ CŨ (%s, ghi lúc %s)" % (
            len(so), RA.name,
            time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(RA.stat().st_mtime))))
        print("  %d mục đo MỚI trong lần chạy này." % len(de))
        print("  Muốn một phép đo thuần thì xoá sổ đi rồi chạy lại.")
        print()

    if so and not de:
        print("  ***  KHÔNG ĐO LẠI DÒNG NÀO  ***")
        print("  Toàn bộ %d mục đọc từ sổ CŨ: %s" % (len(so), RA.name))
        print("  Sổ ghi lúc: %s" % time.strftime(
            "%d/%m/%Y %H:%M:%S", time.localtime(RA.stat().st_mtime)))
        print("  Bảng dưới là số của LẦN ĐO ĐÓ, không phải của bản mã đang")
        print("  nằm trên đĩa lúc này. Muốn đo lại thì xoá sổ đi.\n")
    elif so:
        print("  %d mục đọc từ sổ cũ, %d mục đo mới\n" % (len(so), len(de)))
    print("  %d đề — truy ngược giá trị, không có model\n" % len(de))
    t0 = time.monotonic()

    for i, d in enumerate(de, 1):
        t1 = time.monotonic()
        r = chay_mot_de(d, dung_dong=_CO_DONG_KIEM_TRA)
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
          % (("BỘ ĐỀ %d, bốn tệp khác hẳn — bằng chứng độc lập" % _SO_BO) if _SO_BO >= 2
             else "CHÍNH bộ đề cũ — chỉ là kiểm bản cài đặt, KHÔNG phải bằng chứng"))
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
