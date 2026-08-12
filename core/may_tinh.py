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


def _tinh_cay(nut: ast.AST) -> float:
    """Duyệt cây cú pháp, chỉ cho phép số và toán tử — không tên, không gọi hàm."""
    if isinstance(nut, ast.Constant):
        if isinstance(nut.value, bool) or not isinstance(nut.value, (int, float)):
            raise ValueError("chỉ nhận số")
        return nut.value
    if isinstance(nut, ast.BinOp) and type(nut.op) in _PHEP:
        trai, phai = _tinh_cay(nut.left), _tinh_cay(nut.right)
        if isinstance(nut.op, ast.Pow) and (
            abs(trai) > _TRAN_LUY_THUA or abs(phai) > 64
        ):
            # 9**9**9 treo máy vài phút và ăn hết RAM. Chặn ở cổng vào.
            raise ValueError("luỹ thừa quá lớn")
        return _PHEP[type(nut.op)](trai, phai)
    if isinstance(nut, ast.UnaryOp) and type(nut.op) in _PHEP:
        return _PHEP[type(nut.op)](_tinh_cay(nut.operand))
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


# Biểu thức NẰM GIỮA câu chữ: phải có ít nhất hai số và một toán tử giữa chúng,
# nếu không thì "COVID-19" hay "phòng 3" cũng thành phép tính.
_BIEU_THUC_TRONG_CAU = re.compile(
    r"\d+(?:[.,]\d+)?(?:\s*[+\-*/%×÷^]\s*\d+(?:[.,]\d+)?)+"
)


def _rut_bieu_thuc(text: str) -> str | None:
    """Nhặt phép tính dài nhất nằm lẫn trong câu chữ, hoặc `None`."""
    khop = _BIEU_THUC_TRONG_CAU.findall(text or "")
    if not khop:
        return None
    return max(
        (m.group(0) for m in _BIEU_THUC_TRONG_CAU.finditer(text)), key=len
    )


def _goi_gon(so: float) -> str:
    if isinstance(so, float) and so.is_integer():
        so = int(so)
    if isinstance(so, int):
        return f"{so:,}".replace(",", ".")
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
    """Một dòng "đã tính sẵn" để nhét vào lời dặn, hoặc `None` nếu không có gì.

    Trả về CHUỖI chứ không phải số, vì thứ đi vào lời dặn là một câu khẳng định
    mà model chỉ việc chép lại — mọi cách khác đều là mời nó tính lại.
    """
    goc = (text or "").strip()
    if not goc:
        return None
    hom_nay = (now or datetime.now()).date()
    khong_dau = _bo_dau(goc)

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
                    f"ĐÃ TÍNH SẴN. Trả lời đúng ý này: "
                    f"\"Còn {cach} ngày nữa đến {moc:%d/%m/%Y}.\""
                )
            return (
                f"ĐÃ TÍNH SẴN. Trả lời đúng ý này: "
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
        return (
            f"ĐÃ TÍNH SẴN. Trả lời đúng ý này: "
            f"\"{bieu_thuc.strip()} = {_goi_gon(ket_qua)}.\""
        )
    return None


__all__ = ["tinh_bieu_thuc", "tinh_giup"]
