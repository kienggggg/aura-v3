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


def dong_trong_except(nguon: str) -> Set[int]:
    """Những dòng nằm TRONG thân một `except`."""
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return set()
    ra: Set[int] = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.ExceptHandler):
            for than in n.body:
                d1 = getattr(than, "lineno", 0)
                d2 = getattr(than, "end_lineno", d1) or d1
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
    trong_except = dong_trong_except(nguon)

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

    # ---- BỘ ĐỀ 2 BÁC BỎ GIẢ ĐỊNH "CHẾT LUÔN Ở CUỐI VẾT" ----
    #
    # Luật trên chỉ nhìn ĐUÔI vết. Đo 24/08 trên bộ đề 2, mã TÍCH HỢP có lớp
    # `try/except Exception` bọc ngoài (`core/chat_service.py:371,583,612,675`)
    # thì cú chết nằm GIỮA vết, còn cuối vết là một tính toán khác, hợp lệ:
    #
    #   buoc=6   dong=45   <tra_ve>=None                 <- CHẾT ở đây
    #   buoc=8   dong=74   <tra_ve>=None                 <- lan lên hàm gọi
    #   ... 10 bước sau, một nhánh KHÁC của cùng test ...
    #   buoc=40  dong=111  <tra_ve>=OutwardContent(...)  <- giá trị HỢP LỆ
    #
    # ChatService nuốt lặng lẽ NameError, rẽ sang nhánh dự phòng, rồi trả về
    # một giá trị đúng. Luật cũ lấy `tra_ve` cuối (bước 40) — không bao giờ
    # chạm chỗ hỏng. Kết quả: `secret_guard` 2/9 đúng, `user_memory` 3/11,
    # trong khi hai tệp thuần logic cùng bộ được 60% và 89%.
    #
    # Sửa: quét MỌI dãy `tra_ve` liên tiếp trong vết, không chỉ dãy cuối. Dãy
    # nào kết thúc ở dòng KHÔNG phải `return` là một lượt gỡ ngăn xếp; lấy
    # phần tử đầu của lượt gỡ SỚM NHẤT — chỗ chết đầu tiên.
    i = 0
    n = len(su_kien)
    while i < n:
        if su_kien[i].get("su_kien") != "tra_ve":
            i += 1
            continue
        j = i
        while j + 1 < n and su_kien[j + 1].get("su_kien") == "tra_ve":
            j += 1
        # Dãy su_kien[i..j] là các tầng bật ra liên tiếp.
        #
        # ---- BỘ ĐỀ 3 BÁC BỎ "KHÔNG PHẢI RETURN THÌ LÀ CHẾT" ----
        #
        # Luật trên một mình BÁO ĐỘNG GIẢ. Đo 25/08 trên `core/khay_the.py`,
        # đề `doi_bien` gieo vào dòng 43:
        #
        #   buoc=27  dong=182  <tra_ve>=None   ra[n.name] = The(ten=..., ...)
        #
        # Dòng 182 dựng một đối tượng. `sys.settrace` phát `tra_ve` khi
        # `The.__init__` xong, và dòng 182 KHÔNG phải câu lệnh `return` — nên
        # luật cũ kêu "chết ở đây" ngay bước 27, trong khi chương trình còn
        # chạy tiếp tới bước 95. Chuỗi vì thế chỉ thấy sự kiện trước bước 27,
        # quay vòng trong thân `sinh_khay` và không bao giờ gặp lời gọi
        # `gan_phan_biet` ở dòng 183 — nơi dẫn xuống chỗ hỏng thật.
        #
        # Trả về ngầm (hàm hết thân, không có `return`) và lời gọi hàm dựng
        # đối tượng đều rơi vào bẫy này.
        #
        # Phân biệt được mà KHÔNG cần biết đáp án: một cú chết BỊ NUỐT thì
        # phải có kẻ nuốt. Sau lượt gỡ, luồng chạy nhảy vào thân một `except`.
        # Không có bằng chứng ấy thì đây chỉ là một lần trả về bình thường.
        #
        # Luật §4 của kho này: "phán quyết phải đi kèm phép đo tạo ra nó".
        # Ở đây phán quyết là "chết", còn phép đo là "bước kế tiếp có ở trong
        # except không".
        ke_tiep = su_kien[j + 1] if j + 1 < n else None
        bi_nuot = ke_tiep is not None and (ke_tiep.get("dong") in trong_except)
        if su_kien[j].get("dong") not in co_ret and bi_nuot:
            return su_kien[i], "chỗ chương trình chết (lỗi bị nuốt giữa chừng)"
        i = j + 1

    return tra_ve[-1], "giá trị test nhìn thấy"


def map_ham_theo_dong(nguon: str) -> Dict[int, str]:
    """{số dòng -> tên hàm chứa nó}. Hàm lồng nhau thì hàm TRONG CÙNG thắng."""
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return {}
    tam: Dict[int, Tuple[str, int]] = {}
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d2 = n.end_lineno or n.lineno
            rong = d2 - n.lineno
            for d in range(n.lineno, d2 + 1):
                if d not in tam or rong < tam[d][1]:
                    tam[d] = (n.name, rong)
    return {d: v[0] for d, v in tam.items()}


def map_dong_goi(nguon: str) -> Dict[int, Set[str]]:
    """{số dòng -> tên các hàm ĐỊNH NGHĨA TRONG CHÍNH TỆP mà dòng ấy gọi}.

    Chỉ lấy hàm của tệp này. Gọi `unicodedata.normalize` thì không có vết để
    mà đi vào, đem vào chỉ tổ nạp rác cho hàng đợi.
    """
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return {}
    co_that = {n.name for n in ast.walk(cay)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    ra: Dict[int, Set[str]] = {}
    for n in ast.walk(cay):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        ten = getattr(f, "id", None) or getattr(f, "attr", None)
        if ten not in co_that:
            continue
        d = getattr(n, "lineno", 0)
        if d:
            ra.setdefault(d, set()).add(ten)
    return ra


def _ra_khoi_ham_gan_nhat(
    su_kien: List[dict], ham: str, nguon: str, truoc_buoc: int
) -> Optional[dict]:
    """Lượt chạy GẦN NHẤT của `ham` trước `truoc_buoc` kết thúc ở sự kiện nào.

    VÌ SAO CÓ HÀM NÀY — đo 25/08/2026, bộ đề 1 + bộ đề 3 gộp lại:

        lỗi CÙNG hàm với mốc bắt đầu   42/49 = 0,86
        lỗi KHÁC hàm với mốc bắt đầu    1/31 = 0,03

    `_viet_gan_nhat` tìm lần ghi gần nhất theo TÊN, trên một danh sách sự kiện
    PHẲNG, không có phạm vi hàm. Một lời gọi hàm vì thế là bức tường kín: ở
    `core/khay_the.py`, mốc bắt đầu là dòng 183 `return gan_phan_biet(...)`,
    còn lỗi nằm ở dòng 43 trong `bo_dau()`, cách ba tầng gọi. Cái tên
    `gan_phan_biet` là một `def` chứ không phải phép gán nên không ai "ghi"
    nó — nhánh ấy tắt ngay bước đầu, chuỗi quay về thân vòng `for` và đốt hết
    ngân sách 21 bước tại đó. Kết quả: khay_the.py trúng 2/22, mà 18 trong 22
    ca là khác-hàm và cả 18 đều trượt.

    Cạnh còn thiếu chính là cái này: dòng đang xét GỌI một hàm của cùng tệp
    thì phải nhảy vào lượt chạy của hàm ấy rồi truy tiếp từ trong đó.

    Trả về sự kiện CUỐI CÙNG bên trong hàm trước `truoc_buoc` — là `tra_ve`
    nếu hàm trả về bình thường, là chỗ chết nếu nó ném lỗi ra ngoài. Cả hai
    đều đúng chỗ cần đi tiếp.
    """
    hd = map_ham_theo_dong(nguon)
    tot = None
    for e in su_kien:
        b = e.get("buoc", 0)
        if b >= truoc_buoc:
            continue
        if hd.get(e.get("dong") or 0) != ham:
            continue
        if tot is None or b > tot.get("buoc", 0):
            tot = e
    return tot


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


def _rut_gon_chuoi_theo_dong(chuoi: List[dict]) -> List[dict]:
    """Giữ một mục đại diện đầu tiên cho mỗi dòng nguồn, đúng thứ tự đã tìm.

    Đo bộ 5 ngày 25/08/2026: máy có cạnh qua hàm trả trung vị 18,5 mục nhưng
    chỉ 7,0 dòng riêng. Các mục lặp cùng dòng không thêm vị trí nào để người
    dùng kiểm tra; bộ chấm cũng xác định đúng/sai bằng tập dòng riêng.

    Phải gọi hàm này SAU khi hàng đợi đã duyệt xong. Gộp ngay lúc duyệt sẽ làm
    `len(chuoi) < sau_toi_da` đổi nghĩa, tức âm thầm cấp thêm ngân sách cho một
    cỗ máy khác và không còn bảo đảm giữ nguyên độ chính xác 0,77 đã đo.
    """
    ra: List[dict] = []
    dong_da_co: Set[int] = set()
    for muc in chuoi:
        dong = muc.get("dong")
        if isinstance(dong, int):
            if dong in dong_da_co:
                continue
            dong_da_co.add(dong)
        # Không gộp các mục thiếu số dòng: chưa có bằng chứng chúng cùng một
        # vị trí, nên gom tất cả vào khoá None sẽ làm mất dữ liệu thật.
        ra.append(muc)
    return ra


def truy_nguoc(
    su_kien: List[dict],
    nguon: str,
    sau_toi_da: int = 40,
    im_lang_khi_khong_lui: bool = False,
) -> Dict[str, Any]:
    """Đi ngược từ giá trị trả về sai về các dòng đã sinh ra nó.

    `im_lang_khi_khong_lui` — luật rút ra từ bộ đề 1 ngày 24/08:

        chuỗi ĐÚNG 1 dòng, TRÚNG   15
        chuỗi ĐÚNG 1 dòng, TRƯỢT   22   <- chỉ một dòng, và chỉ SAI
        chuỗi  >1 dòng, TRÚNG      17
        chuỗi  >1 dòng, TRƯỢT       9

    Trong 37 ca trả lời đúng một dòng thì chỉ 15 đúng — 41%, tệ hơn tung đồng
    xu mà trông chắc chắn hơn hẳn. Chuỗi một dòng nghĩa là **không lùi được
    bước nào**: tên mà dòng ấy đọc không có ai ghi trong vết, nên máy chỉ đang
    đọc lại chỗ chương trình chết — đúng thứ traceback Python in sẵn miễn phí.

    Bật cờ này thì những ca ấy trả `khong_biet` thay vì chỉ vào một dòng.

    CẢNH BÁO: luật này rút ra TỪ bộ đề 1. Chấm nó trên bộ đề 1 là lấy kết quả
    chứng minh cho giả thiết sinh ra từ chính kết quả ấy. Muốn có bằng chứng
    thì phải chạy trên bộ đề 2 — mã nguồn khác hẳn.
    """
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

    mg = map_dong_goi(nguon)

    chuoi: List[dict] = []
    da_xet: Set[Tuple[int, str]] = set()
    # hàng đợi: (bước hiện tại, tên cần truy, vì sao, kiểu)
    #   kiểu "ten" — truy biến, như cũ
    #   kiểu "goi" — dòng ấy GỌI một hàm của cùng tệp, nhảy vào trong hàm đó
    hang: List[Tuple[int, str, str, str]] = []

    def nap(buoc: int, dong: int, vi_sao: str) -> None:
        for ten in sorted(md.get(dong, set())):
            if (buoc, ten) not in da_xet:
                hang.append((buoc, ten, vi_sao, "ten"))
        # Cạnh QUA RANH GIỚI HÀM. Nạp SAU các tên, nên bề rộng vẫn ưu tiên
        # truy trong cùng hàm trước — chỉ đi sâu khi trong hàm đã cạn.
        for ham in sorted(mg.get(dong, set())):
            if (buoc, "()" + ham) not in da_xet:
                hang.append((buoc, ham, vi_sao, "goi"))

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
        buoc, ten, vi_sao, kieu = hang.pop(0)
        khoa = ("()" + ten) if kieu == "goi" else ten
        if (buoc, khoa) in da_xet:
            continue
        da_xet.add((buoc, khoa))

        if kieu == "goi":
            e = _ra_khoi_ham_gan_nhat(su_kien, ten, nguon, buoc)
            if e is None:
                # Hàm có trong mã nhưng không chạy trong vết này.
                continue
            chuoi.append({
                "dong": e.get("dong"),
                "ten_bien": e.get("ten_bien"),
                "gia_tri": e.get("gia_tri_moi"),
                "dong_ma": e.get("dong_ma", ""),
                "vi_sao": "%s vào trong %s()" % (vi_sao, ten),
                "sau": sau,
            })
            nap(e.get("buoc", 0), e.get("dong", 0), ten + "()")
            continue

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

    # Giữ nguyên phán quyết "có lùi được hay không" của chuỗi đầy đủ; phép
    # rút gọn chỉ thay phần trình bày, không được đổi trạng thái nghiệp vụ.
    khong_lui = len(chuoi) <= 1

    # Rút phần người dùng phải đọc, không đổi bất kỳ bước duyệt nào ở trên.
    chuoi = _rut_gon_chuoi_theo_dong(chuoi)

    dong = []
    for m in chuoi:
        d = m.get("dong")
        if isinstance(d, int) and d not in dong:
            dong.append(d)

    if im_lang_khi_khong_lui and khong_lui:
        return {
            "trang_thai": "khong_biet",
            "vi_sao": "không lùi được bước nào — tên mà dòng ấy đọc không có "
                      "ai ghi trong vết. Traceback Python đã chỉ đúng chỗ này.",
            "chuoi": chuoi,
            "dong": [],
            "khong_lui": True,
            "model_calls": 0,
            "external_submit": False,
        }

    return {
        "trang_thai": "chuoi_rong" if khong_lui else "co_chuoi",
        "vi_sao": "",
        "chuoi": chuoi,
        "dong": dong,
        "khong_lui": khong_lui,
        "model_calls": 0,
        "external_submit": False,
    }
