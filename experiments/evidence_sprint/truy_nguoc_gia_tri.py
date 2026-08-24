# -*- coding: utf-8 -*-
"""truy_nguoc_gia_tri.py — từ giá trị SAI đi ngược về những dòng đã sinh ra nó.

Vì sao làm cái này, ngày 24/08/2026:

    E1 trong họ (5 phép so sánh/logic)     3/9
    E1 NGOÀI họ                            0/64
       đổi biến   24 đề   \\
       bỏ return  19 đề    >  43/64 = 67% là lỗi CẤU TRÚC
       đổi thứ tự 15 đề   /
       binop       6 đề

E1 liệt kê mọi phép lật rồi thử từng cái. Với `doi_bien` thì số ứng viên nổ
theo bình phương số biến trong tầm — cách ấy không co giãn tới đó. Truy ngược
đi hướng khác: **không đề xuất bản vá nào cả**, chỉ thu hẹp từ "mọi dòng đã
chạy" xuống "những dòng thật sự sinh ra con số sai".

Một nửa máy đã có sẵn từ trước: `core/trace_runtime.py:193` ghi từng dòng
`dong · ten_bien · gia_tri_cu -> gia_tri_moi · su_kien`. Đó là vế **AI GHI**.
Vế còn thiếu là **AI ĐỌC**, và cái đó lấy từ AST của chính dòng ấy, không cần
chạy thêm gì.

CẢNH BÁO VỀ THƯỚC ĐO — đọc trước khi so số:

    E1 trả lời "vá thế này".   Truy ngược trả lời "nhìn mấy dòng này".
    HAI THƯỚC KHÁC NHAU. Cột "vá đúng" của tệp này VĨNH VIỄN là 0, vì nó
    không vá. Đem 40/64 của truy ngược đặt cạnh 0/64 của E1 mà không nói rõ
    thì đó là đổi thước giữa chừng.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Set, Tuple

# Thân của các câu lệnh ghép: dòng trong thân có câu lệnh riêng của nó, nên khi
# tính "dòng này đọc biến nào" thì phải bỏ các trường này ra, kẻo `if x > 3:`
# nuốt luôn mọi biến trong cả khối.
TRUONG_THAN = ("body", "orelse", "finalbody", "handlers")


def _ten_doc(nut: ast.AST) -> Set[str]:
    """Mọi tên được ĐỌC trong một nút, không đi vào thân câu lệnh ghép."""
    ra: Set[str] = set()

    def di(n: ast.AST) -> None:
        for truong, gia_tri in ast.iter_fields(n):
            if truong in TRUONG_THAN:
                continue
            if isinstance(gia_tri, list):
                for x in gia_tri:
                    if isinstance(x, ast.AST):
                        di(x)
            elif isinstance(gia_tri, ast.AST):
                di(gia_tri)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            ra.add(n.id)

    di(nut)
    return ra


def map_dong_doc(nguon: str) -> Dict[int, Set[str]]:
    """{số dòng -> tập tên mà dòng ấy ĐỌC}.

    Câu lệnh nhỏ hơn ghi đè câu lệnh lớn hơn: `if x > 3:` phủ cả khối, nhưng
    từng dòng trong thân có câu lệnh riêng và phải thắng.
    """
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return {}

    cac_lenh: List[Tuple[int, int, int, ast.stmt]] = []
    for n in ast.walk(cay):
        if isinstance(n, ast.stmt):
            d1 = getattr(n, "lineno", 0)
            d2 = getattr(n, "end_lineno", d1) or d1
            if d1:
                cac_lenh.append((d2 - d1, d1, d2, n))

    ra: Dict[int, Set[str]] = {}
    # rộng trước, hẹp sau -> hẹp ghi đè
    for _, d1, d2, n in sorted(cac_lenh, key=lambda x: -x[0]):
        doc = _ten_doc(n)
        for d in range(d1, d2 + 1):
            ra[d] = set(doc)
    return ra


def dong_co_return(nguon: str) -> Set[int]:
    """Những dòng THẬT SỰ có câu lệnh `return`."""
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return set()
    ra: Set[int] = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Return):
            d1 = getattr(n, "lineno", 0)
            d2 = getattr(n, "end_lineno", d1) or d1
            for d in range(d1, d2 + 1):
                ra.add(d)
    return ra


def _moc_bat_dau(su_kien: List[dict], nguon: str) -> Tuple[Optional[dict], str]:
    """Bắt đầu truy ngược từ đâu — và đây là chỗ dễ sai nhất.

    `sys.settrace` phát sự kiện `return` CẢ KHI hàm ném lỗi ra ngoài: mỗi tầng
    ngăn xếp gỡ ra là một `tra_ve` với `arg = None`. Đo trên đề #0 ngày
    24/08 (`_bo_dau` dùng biến `a` chưa gán -> NameError):

        buoc=9   dong=25   <tra_ve> = None   tach = unicodedata.normalize(...)
        buoc=11  dong=175  <tra_ve> = None   khong_dau = _bo_dau(goc)

    Hai dòng đó là HAI TẦNG GỠ, không phải hai lần trả về. Lấy cái cuối là dừng
    ở tầng ngoài cùng và không bao giờ chạm tới chỗ hỏng.

    Phân biệt được mà không cần biết đáp án: dòng 25 **không phải câu lệnh
    `return`**. Một lần trả về thật thì luôn đứng trên `return`.

        có `tra_ve` ở dòng KHÔNG phải return  ->  chương trình CHẾT ở đó,
                                                  lấy tầng sâu nhất (sớm nhất)
        mọi `tra_ve` đều đứng trên return     ->  chạy trót lọt mà ra số sai,
                                                  lấy giá trị cuối cùng
    """
    tra_ve = [e for e in su_kien if e.get("su_kien") == "tra_ve"]
    if not tra_ve:
        return (su_kien[-1] if su_kien else None), "sự kiện cuối cùng"
    co_ret = dong_co_return(nguon)

    # Đuôi gỡ ngăn xếp: dãy `tra_ve` liên tiếp ở CUỐI vết. Một lượt gỡ thì các
    # tầng bật ra liên tiếp, không xen sự kiện gán nào — vì không có gì được gán.
    duoi: List[dict] = []
    for e in reversed(su_kien):
        if e.get("su_kien") != "tra_ve":
            break
        duoi.append(e)
    duoi.reverse()

    # Sự kiện CUỐI CÙNG đứng trên dòng không phải `return` -> cả đuôi ấy là gỡ.
    # Đo 24/08 đề #2: chỗ hỏng nằm ĐÚNG TRÊN một dòng `return`, nên luật "dòng
    # không phải return" một mình không phân biệt được; phải nhìn sự kiện cuối.
    #
    #   buoc=12 dong=26  <tra_ve>=None   return ''.join((a for c in tach ...
    #   buoc=14 dong=26  <tra_ve>=None   (khung genexp)
    #   buoc=16 dong=175 <tra_ve>=None   khong_dau = _bo_dau(goc)   <- không return
    #
    # `khong_dau` KHÔNG hề được gán -> hàm không trả về gì cả, nó chết.
    if duoi and su_kien[-1].get("dong") not in co_ret:
        return duoi[0], "chỗ chương trình chết (gỡ ngăn xếp)"
    return tra_ve[-1], "giá trị test nhìn thấy"


def _viet_gan_nhat(
    su_kien: List[dict], ten: str, truoc_buoc: int
) -> Optional[dict]:
    """Sự kiện GHI vào `ten` gần nhất trước bước đã cho."""
    tot = None
    for e in su_kien:
        b = e.get("buoc", 0)
        if b >= truoc_buoc:
            continue
        if e.get("ten_bien") != ten:
            continue
        if e.get("su_kien") not in ("gan", "thay_doi"):
            continue
        if tot is None or b > tot.get("buoc", 0):
            tot = e
    return tot


def truy_nguoc(
    su_kien: List[dict],
    nguon: str,
    sau_toi_da: int = 40,
) -> Dict[str, Any]:
    """Đi ngược từ giá trị trả về sai về các dòng đã sinh ra nó."""
    if not su_kien:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "không có sự kiện vết chạy",
                "chuoi": [], "dong": []}

    md = map_dong_doc(nguon)
    if not md:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "mã nguồn không phân tích được",
                "chuoi": [], "dong": []}

    goc, vi_sao_goc = _moc_bat_dau(su_kien, nguon)
    if goc is None:
        return {"trang_thai": "khong_do_duoc", "vi_sao": "không có mốc bắt đầu",
                "chuoi": [], "dong": []}

    chuoi: List[dict] = []
    da_xet: Set[Tuple[int, str]] = set()
    # hàng đợi: (bước hiện tại, tên cần truy, vì sao)
    hang: List[Tuple[int, str, str]] = []

    def nap(buoc: int, dong: int, vi_sao: str) -> None:
        for ten in sorted(md.get(dong, set())):
            if (buoc, ten) not in da_xet:
                hang.append((buoc, ten, vi_sao))

    chuoi.append({
        "dong": goc.get("dong"),
        "ten_bien": goc.get("ten_bien"),
        "gia_tri": goc.get("gia_tri_moi"),
        "dong_ma": goc.get("dong_ma", ""),
        "vi_sao": vi_sao_goc,
        "sau": 0,
    })
    nap(goc.get("buoc", 10**9), goc.get("dong", 0), str(goc.get("ten_bien")))

    sau = 0
    while hang and len(chuoi) < sau_toi_da:
        sau += 1
        if sau > sau_toi_da:
            break
        buoc, ten, vi_sao = hang.pop(0)
        if (buoc, ten) in da_xet:
            continue
        da_xet.add((buoc, ten))
        e = _viet_gan_nhat(su_kien, ten, buoc)
        if e is None:
            # Không ai ghi -> tham số hàm hoặc biến toàn cục. Hết đường lùi.
            continue
        chuoi.append({
            "dong": e.get("dong"),
            "ten_bien": ten,
            "gia_tri": e.get("gia_tri_moi"),
            "dong_ma": e.get("dong_ma", ""),
            "vi_sao": "%s cần %s" % (vi_sao, ten),
            "sau": sau,
        })
        nap(e.get("buoc", 0), e.get("dong", 0), ten)

    dong = []
    for m in chuoi:
        d = m.get("dong")
        if isinstance(d, int) and d not in dong:
            dong.append(d)

    return {
        "trang_thai": "co_chuoi" if len(chuoi) > 1 else "chuoi_rong",
        "vi_sao": "",
        "chuoi": chuoi,
        "dong": dong,
        "model_calls": 0,
        "external_submit": False,
    }
