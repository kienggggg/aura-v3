# -*- coding: utf-8 -*-
"""Máy tính của AURA — model đoán số, máy thì tính.

10/08/2026 đo được: hỏi "Còn bao nhiêu ngày nữa tới ngày 1 tháng 9?", AURA đáp
**"khoảng 23 ngày"**.  Đúng ra là 22.  Đồng hồ đã đưa đúng mốc 10/08 rồi; cái
sai nằm ở phép trừ.  Model 4B sinh chữ theo xác suất, nó không trừ.

Cách chữa giống hệt `core/dong_ho.py`: **tính sẵn rồi đưa vào lời dặn**, chứ
không hy vọng model tự tính rồi đi kiểm bài nó.  Ranh giới: con số là dữ kiện
của MÁY, câu chữ mới là việc của model.

Cố ý KHÔNG dùng `eval()`.  Câu hỏi đến từ Sếp, nhưng lịch sử hội thoại có thể
mang theo nguyên văn từ trang web lạ, và `eval` trên chuỗi như thế là mở cửa
cho người khác chạy mã trong tiến trình AURA.
"""
from __future__ import annotations

import ast
import operator
import re
import unicodedata
from datetime import date, datetime

_PHEP = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_TRAN_LUY_THUA = 1_000_000


def _bo_dau(text: str) -> str:
    tach = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in tach if not unicodedata.combining(c)).replace("đ", "d")


def _tinh_cay(nut: ast.AST, an: tuple[str, float] | None = None) -> float:
    """Duyệt cây cú pháp: chỉ số và toán tử, không gọi hàm.

    `an` là cặp (tên ẩn, giá trị) — CHỈ một tên duy nhất được phép, và nó phải
    do chỗ gọi truyền vào. Không có `an` thì mọi tên đều bị từ chối, y như cũ:
    cấm tên là thứ ngăn `__import__` hay `os` lọt vào cây.
    """
    if isinstance(nut, ast.Constant):
        if isinstance(nut.value, bool) or not isinstance(nut.value, (int, float)):
            raise ValueError("chỉ nhận số")
        return nut.value
    if isinstance(nut, ast.Name):
        if an is not None and nut.id == an[0]:
            return an[1]
        raise ValueError("tên lạ trong biểu thức")
    if isinstance(nut, ast.BinOp) and type(nut.op) in _PHEP:
        trai, phai = _tinh_cay(nut.left, an), _tinh_cay(nut.right, an)
        if isinstance(nut.op, ast.Pow) and (
            abs(trai) > _TRAN_LUY_THUA or abs(phai) > 64
        ):
            # 9**9**9 treo máy vài phút và ăn hết RAM. Chặn ở cổng vào.
            raise ValueError("luỹ thừa quá lớn")
        return _PHEP[type(nut.op)](trai, phai)
    if isinstance(nut, ast.UnaryOp) and type(nut.op) in _PHEP:
        return _PHEP[type(nut.op)](_tinh_cay(nut.operand, an))
    raise ValueError("biểu thức không hợp lệ")


def tinh_bieu_thuc(bieu_thuc: str) -> float | None:
    """Tính một biểu thức số học thuần. Trả `None` nếu không phải phép tính."""
    sach = (bieu_thuc or "").strip().replace("×", "*").replace("÷", "/")
    sach = sach.replace("^", "**").replace(",", ".")
    if not sach or not re.fullmatch(r"[0-9\s+\-*/%().]+", sach):
        return None
    if not any(ch.isdigit() for ch in sach) or not any(
        ch in sach for ch in "+-*/%"
    ):
        return None
    try:
        return _tinh_cay(ast.parse(sach, mode="eval").body)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError,
            OverflowError, RecursionError):
        return None


# --------------------------------------------------------------------------- #
# PHƯƠNG TRÌNH BẬC NHẤT MỘT ẨN
#
# 13/08/2026, Sếp gõ "2x * 3 = 12, x bằng bao nhiêu":
#     lần chạy thứ nhất  ->  x = 2   (đúng)
#     lần chạy thứ hai   ->  x = 4   (sai)
# Cùng một câu, hai đáp án. `tinh_giup` trả `None` cho cả hai lần vì nó chỉ tính
# được biểu thức SỐ, nên không có máy nào kiểm lại model.
#
# Khác vụ bịa tiểu sử — chỗ đó chặn được bằng bắt buộc tra nguồn — ở đây KHÔNG
# CÓ NGUỒN NÀO ĐỂ TRA. Chỉ có cách để máy tự giải.
#
# Cách giải: KHÔNG dựng đại số ký hiệu. Một phương trình bậc nhất là hàm
# f(x) = a·x + b, nên đo f tại ba điểm là ra:
#     b = f(0)            a = f(1) − f(0)            x = −b / a
# Điểm thứ ba (x=2) dùng để KIỂM nó có thật sự bậc nhất không: f(2) phải bằng
# 2a + b. Không khớp thì đây là bậc hai trở lên, hoặc có ẩn dưới mẫu — trả
# `None` để model tự lo, đừng đưa một đáp án sai kèm giọng chắc chắn.
# --------------------------------------------------------------------------- #

# "2x" -> "2*x"; "3(x+1)" -> "3*(x+1)". Nhân ẩn phải viết ra thì AST mới hiểu.
_NHAN_NGAM = re.compile(r"(?<=[0-9)])\s*(?=[a-z(])")
_MOT_AN = re.compile(r"(?<![a-z])([a-z])(?![a-z])")
_SAI_SO = 1e-9


def _doi_ve(ve: str, ten_an: str, gia_tri: float) -> float:
    cay = ast.parse(ve.strip(), mode="eval").body
    return _tinh_cay(cay, (ten_an, gia_tri))


def giai_phuong_trinh(text: str) -> str | None:
    """Giải phương trình bậc nhất một ẩn, hoặc `None` nếu không phải.

    Fail-closed ở mọi chỗ nghi ngờ: nhiều ẩn, không bậc nhất, vô nghiệm, vô số
    nghiệm — tất cả trả `None`.
    """
    goc = (text or "").strip()
    if "=" not in goc:
        return None

    # Chỉ lấy phần có dạng phương trình, bỏ đuôi "x bằng bao nhiêu".
    khop = re.search(r"([0-9a-z\s+\-*/^().]+=[0-9a-z\s+\-*/^().]+)", _bo_dau(goc))
    if not khop:
        return None
    pt = khop.group(1).replace("^", "**")
    if pt.count("=") != 1:
        return None

    ten = sorted(set(_MOT_AN.findall(pt)))
    if len(ten) != 1:
        return None                      # không ẩn, hoặc nhiều hơn một ẩn
    an = ten[0]

    pt = _NHAN_NGAM.sub("*", pt)
    trai, phai = pt.split("=")
    if not trai.strip() or not phai.strip():
        return None

    try:
        f = [_doi_ve(trai, an, t) - _doi_ve(phai, an, t) for t in (0.0, 1.0, 2.0)]
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError,
            OverflowError, RecursionError):
        return None

    b = f[0]
    a = f[1] - f[0]
    # Bậc nhất thì f(2) − f(1) phải bằng f(1) − f(0).
    if abs((f[2] - f[1]) - a) > _SAI_SO * max(1.0, abs(a)):
        return None
    if abs(a) <= _SAI_SO:
        return None                      # vô nghiệm hoặc vô số nghiệm

    nghiem = -b / a
    if nghiem != nghiem or abs(nghiem) == float("inf"):   # NaN / vô cực
        return None
    return (
        f'MÁY ĐÃ GIẢI SẴN — Sếp chỉ HỎI, chưa đưa ra đáp án nào. '
        f'Nói lại thành câu cho Sếp: "{an} = {_goi_gon(nghiem)}." '
        f"Đây là đáp án MÁY giải ra, không phải model đoán — dùng đúng con số "
        f"này, đừng tính lại."
    )


# Biểu thức NẰM GIỮA câu chữ: phải có ít nhất hai số và một toán tử giữa chúng,
# nếu không thì "COVID-19" hay "phòng 3" cũng thành phép tính.
_BIEU_THUC_TRONG_CAU = re.compile(
    r"\d+(?:[.,]\d+)?(?:\s*[+\-*/%×÷^]\s*\d+(?:[.,]\d+)?)+"
)


# Sếp gõ TIẾNG VIỆT, không gõ ký hiệu.
#
# 13/08/2026: "1247 nhân 38 bằng bao nhiêu" -> AURA đáp 46.586. Đúng là 47.386.
# Đo ra thì `tinh_giup()` trả `None` — máy tính KHÔNG HỀ bắt câu đó, nên model
# tự đoán. Mẫu cũ chỉ nhận ký hiệu `+ - * / × ÷`, mà CLAUDE.md ghi tệp này sinh
# ra chính vì phép "1247*38". Nó đúng cho người gõ dấu sao; Sếp thì gõ "nhân".
#
# Sáng cùng ngày AURA từng trả 47.386 đúng — đó là MAY, không phải máy tính
# chạy. Một phép đo đúng nhờ may thì lần sau sai mà không ai hiểu vì sao.
#
# Chỉ đổi khi có DẠNG SỐ-CHỮ-SỐ: "trừ" còn nghĩa "ngoại trừ", "chia" còn nghĩa
# "chia sẻ" — kẹp giữa hai con số thì mới chắc là phép tính.
_CHU_THANH_KY_HIEU = (
    (re.compile(r"(?<=\d)\s*(?:nhan|x)\s*(?=\d)", re.IGNORECASE), " * "),
    (re.compile(r"(?<=\d)\s*(?:cong|them)\s*(?=\d)", re.IGNORECASE), " + "),
    (re.compile(r"(?<=\d)\s*(?:tru|bot)\s*(?=\d)", re.IGNORECASE), " - "),
    (re.compile(r"(?<=\d)\s*chia\s*(?=\d)", re.IGNORECASE), " / "),
    (re.compile(r"(?<=\d)\s*(?:mu|luy thua)\s*(?=\d)", re.IGNORECASE), " ^ "),
)


def _doi_chu_thanh_ky_hieu(khong_dau: str) -> str:
    for mau, ky_hieu in _CHU_THANH_KY_HIEU:
        khong_dau = mau.sub(ky_hieu, khong_dau)
    return khong_dau


def _rut_bieu_thuc(text: str) -> str | None:
    """Nhặt phép tính dài nhất nằm lẫn trong câu chữ, hoặc `None`."""
    text = _doi_chu_thanh_ky_hieu(_bo_dau(text or ""))
    khop = _BIEU_THUC_TRONG_CAU.findall(text or "")
    if not khop:
        return None
    return max(
        (m.group(0) for m in _BIEU_THUC_TRONG_CAU.finditer(text)), key=len
    )


def _goi_gon(so: float) -> str:
    """Số để đưa cho MODEL đọc — không phải để Sếp đọc.

    SỐ NGUYÊN RA CHỮ SỐ TRẦN, KHÔNG DẤU CHẤM HÀNG NGHÌN (10/09/2026). Bản cũ
    viết `83576` thành `83.576` theo lối Việt, và model đọc thành *tám mươi ba
    phẩy năm bảy sáu*. Trừ hai số nguyên mà ra số lẻ thì vô lý, nên nó BẮT LỖI
    MÁY rồi dựng ra một người đã ghi sai:

        "…kết quả là số âm (-83576), không phải 83.576 như bạn đã ghi."
        "Kết quả đúng là 83576, không phải 83.576."

    Đo, đối chứng một biến, xen kẽ từng lượt — cùng dạng câu, cùng số hạng đầu
    91234, chỉ đổi số hạng sau:

        "= 83.576."   bịa lỗi 5/20
        "= 123."      bịa lỗi 0/20

    Lượt N=5 trước đó cho 0/15 so với 0/15 và suýt được đọc thành "giả thuyết
    bị bác" — ô 5 lượt quá nhỏ cho một tỉ lệ ~25%.

    Số thập phân GIỮ NGUYÊN (`7,5000`): chưa đo được nó hỏng, và dấu phẩy thập
    phân là mặt đối xứng của cùng một bệnh — đổi mù là đổi lỗi lấy lỗi.
    """
    if isinstance(so, float) and so.is_integer():
        so = int(so)
    if isinstance(so, int):
        return str(so)
    return f"{so:,.4f}".replace(",", "_").replace(".", ",").replace("_", ".")


# Mẫu chạy trên chuỗi ĐÃ BỎ DẤU, nên viết "ngay/thang/nam" — như thế một mẫu
# lo được cả "ngày 1 tháng 9" lẫn "ngay 1 thang 9" mà không phải viết hai bản.
_NGAY_THANG = re.compile(
    r"ngay\s*(\d{1,2})\s*(?:/|-|\s+thang\s*)\s*(\d{1,2})"
    r"(?:\s*(?:/|-|\s+nam\s*)\s*(\d{4}))?"
    r"|(\d{1,2})\s*/\s*(\d{1,2})(?:\s*/\s*(\d{4}))?"
)
_HOI_CACH_NGAY = re.compile(
    r"(con\s*)?bao\s*nhieu\s*ngay|may\s*ngay|cach\s*day\s*bao\s*lau"
)


def _doc_ngay(text: str, hom_nay: date) -> date | None:
    khop = _NGAY_THANG.search(text)
    if not khop:
        return None
    ngay, thang, nam = (khop.group(1), khop.group(2), khop.group(3))
    if ngay is None:
        ngay, thang, nam = (khop.group(4), khop.group(5), khop.group(6))
    try:
        d, m = int(ngay), int(thang)
        y = int(nam) if nam else hom_nay.year
    except (TypeError, ValueError):
        return None
    try:
        moc = date(y, m, d)
    except ValueError:
        return None
    # "tới ngày 1 tháng 9" mà hôm nay đã qua 1/9 thì Sếp đang nói năm sau.
    if nam is None and moc < hom_nay:
        try:
            moc = date(y + 1, m, d)
        except ValueError:
            return None
    return moc


def tinh_giup(text: str, *, now: datetime | None = None) -> str | None:
    """Bắt câu hỏi có phép toán trong lời người dùng và tính sẵn con số đúng.

    Nhận cả phương trình, khoảng cách ngày, và dãy phép tính; không thấy gì thì
    trả `None`.

    Trả về CHUỖI chứ không phải số, vì thứ đi vào lời dặn là một câu khẳng định
    mà model chỉ việc chép lại — mọi cách khác đều là mời nó tính lại.

    Dòng đầu cũ tả GIÁ TRỊ TRẢ VỀ ("Một dòng đã tính sẵn để nhét vào lời dặn")
    chứ không tả VIỆC. Đo 20/08: thẻ này rơi khỏi cả khay 96 thẻ vì không chung
    chữ nào với việc "đáp lại một câu hỏi trong đó có phép toán". Dòng đầu
    docstring là thứ duy nhất khay đọc để xếp hạng — nó phải nói hàm LÀM GÌ.
    """
    goc = (text or "").strip()
    if not goc:
        return None
    hom_nay = (now or datetime.now()).date()
    khong_dau = _bo_dau(goc)

    # Phương trình xét TRƯỚC biểu thức số: "2x * 3 = 12" có cả dấu "=" lẫn phép
    # nhân, nên bộ rút biểu thức sẽ nhặt được "3 = 12" hoặc tương tự và trả một
    # con số vô nghĩa.
    pt = giai_phuong_trinh(goc)
    if pt is not None:
        return pt

    if _HOI_CACH_NGAY.search(khong_dau):
        moc = _doc_ngay(khong_dau, hom_nay)
        if moc is not None:
            cach = (moc - hom_nay).days
            # Đưa CÂU MẪU chứ không đưa mệnh lệnh.  Bản đầu dặn "dùng đúng con
            # số này, đừng nói 'khoảng'", và model tuân lệnh một cách vụng về:
            # "Chưa có 22 ngày nữa đến ngày 1 tháng 9."  Số đúng, câu sai.
            # Cho sẵn câu để chép thì không còn chỗ nào để đặt vụng.
            if cach >= 0:
                return (
                    f"MÁY ĐÃ TÍNH SẴN — Sếp chỉ HỎI, chưa đưa ra đáp án nào. "
                    f"Nói lại thành câu cho Sếp: "
                    f"\"Còn {cach} ngày nữa đến {moc:%d/%m/%Y}.\""
                )
            return (
                f"MÁY ĐÃ TÍNH SẴN — Sếp chỉ HỎI, chưa đưa ra đáp án nào. "
                f"Nói lại thành câu cho Sếp: "
                f"\"{moc:%d/%m/%Y} đã qua {-cach} ngày rồi.\""
            )

    bieu_thuc = goc.rstrip("=?. ")
    ket_qua = tinh_bieu_thuc(bieu_thuc)
    if ket_qua is None:
        # Câu hỏi thật hiếm khi là biểu thức trần. "Tính giúp tôi 1247 * 38 bằng
        # bao nhiêu?" từng lọt lưới và AURA trả 46396 thay vì 47.386.
        bieu_thuc = _rut_bieu_thuc(goc) or ""
        ket_qua = tinh_bieu_thuc(bieu_thuc)
    if ket_qua is not None:
        # "Trả lời đúng ý này" ĐỌC ĐƯỢC THÀNH "đáp án đúng là…", và model dựng
        # ra một người để đính chính (10/09/2026, chạy app thật):
        #
        #     hỏi   "1247 nhân 38 bằng bao nhiêu"
        #     đáp   "Lỗi tính toán trong câu trả lời bạn cung cấp là không
        #            chính xác. Kết quả đúng … là 47.386."
        #
        # Số đúng, mà Sếp không hề đưa ra câu trả lời nào để mà sai. Đo 3 bộ ×
        # 9 lượt: nền 7/27, và lỗi DỒN vào câu SAI KHIẾN — "tính giúp/hộ" 6/6,
        # câu hỏi có "bao nhiêu" chỉ 1/12. Câu sai khiến tự nó không phải một
        # câu hỏi, nên chuỗi dữ kiện chen vào đọc được thành lời của người dùng
        # đang chờ được chấm.
        #
        # Nói thẳng ra rằng KHÔNG có gì để chấm, và bỏ chữ "đúng". Vẫn giữ
        # khuôn CÂU MẪU đã trả giá ở nhánh ngày ngay trên: đưa câu để chép,
        # không đưa mệnh lệnh.
        return (
            f"MÁY ĐÃ TÍNH SẴN — Sếp chỉ HỎI, chưa đưa ra đáp án nào. "
            f"Nói lại thành câu cho Sếp: "
            f"\"{bieu_thuc.strip()} = {_goi_gon(ket_qua)}.\""
        )
    return None


__all__ = ["tinh_bieu_thuc", "tinh_giup"]
