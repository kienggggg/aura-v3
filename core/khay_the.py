# -*- coding: utf-8 -*-
"""Khay thẻ: sinh thẻ từ kho mã THẬT, rồi lọc còn vài thẻ liên quan.

TRẢ LỜI CÂU CỦA SẾP 19/08 — "tên hàm không phải lệnh cố định, có tính là thẻ
được không": ĐƯỢC, nhưng nó là LOẠI THẺ KHÁC, và khác ở chỗ quyết định thiết kế.

    thẻ CỐ ĐỊNH   if, for, return, +   thuộc về ngôn ngữ, không bao giờ đổi,
                                       ghi cứng vào công cụ được
    thẻ SINH RA   cau_gio, bo_dau      thuộc về kho mã, đổi khi mã đổi

Hệ quả cứng: thẻ sinh ra **phải sinh lại từ mã nguồn mỗi lần**, không được ai
chép tay thành danh sách. Danh sách chép tay sẽ cũ đi, rồi model gọi một hàm đã
bị xoá — và cái đó TỆ HƠN không có thẻ, vì model gọi nó một cách tự tin.

Nên mọi thẻ ở đây đọc thẳng từ cây cú pháp, kèm băm mã nguồn để biết thẻ đã cũ.

VÌ SAO CẦN LỌC — đo 19/08, cùng 6 đề, chỉ đổi cỡ khay:

    khay  6 thẻ  ->  gọi đúng 5/6
    khay 20 thẻ  ->  gọi đúng 5/6
    khay 60 thẻ  ->  gọi đúng 4/6      và chậm gấp 2,5 lần

Hai lượt hỏng ở cỡ 60 tôi ĐÃ CHẨN ĐOÁN SAI là "thẻ trùng nghĩa". Tra mã thật
thì `la_chuyen_rieng_cua_sep` (hỏi chuyện riêng) và `is_secret_request` (đòi
giá trị bí mật) là hai việc khác hẳn. Model chọn ĐÚNG VÙNG, SAI TẦNG — nên gộp
thẻ không chữa được. Thứ chữa được là **đưa ít thẻ hơn**, đúng cái Sếp nói từ
đầu: trước khi code thì nhặt nhóm thẻ cần dùng.

Lọc bằng MÁY, không hỏi model: đối chiếu từ trong mô tả việc với tên thẻ và
dòng đầu tài liệu của nó, bỏ dấu tiếng Việt trước khi so. Lọc mà phải gọi model
thì đã tự chuốc lại đúng cái chậm mình đang tránh.
"""
from __future__ import annotations

import ast
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# Từ quá phổ biến, có mặt ở mọi mô tả nên không phân biệt được gì.
BO_QUA = {
    "cua", "va", "cho", "khi", "neu", "thi", "la", "co", "khong", "mot", "cac",
    "nay", "do", "de", "voi", "tu", "ra", "vao", "hay", "duoc", "bang", "theo",
    "tra", "loi", "cau", "text", "str", "bool", "none", "true", "false", "int",
    "hoac", "sep", "aura", "ham", "viet", "python", "gia", "tri",
}


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt. Không so được 'hỏi' với 'hoi' thì lọc trượt hết."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", s).replace("đ", "d").replace("Đ", "D")


def _tu(s: str) -> set[str]:
    t = bo_dau((s or "").lower())
    t = re.sub(r"[_\W]+", " ", t)
    return {w for w in t.split() if len(w) > 2 and w not in BO_QUA}


@dataclass(frozen=True)
class The:
    ten: str
    mo_dun: str
    chu_ky: str
    mo_ta: str
    bam: str          # băm mã nguồn của hàm — thẻ cũ thì băm lệch
    goi: frozenset[str] = frozenset()      # hàm cùng mô-đun mà nó gọi
    tai_lieu: str = ""                     # TOÀN VĂN tài liệu, để rút dòng phân biệt
    phan_biet: str = ""                    # điền sau, khi đã biết cả nhóm

    @property
    def nhom(self) -> str:
        """Nhóm = mô-đun. Máy chia, không ai chép tay.

        Và nhóm hoá ra đúng chỗ cần: hai cặp model chọn nhầm 19/08 đều NẰM
        CÙNG mô-đun (`tinh_giup`/`tinh_bieu_thuc` ở may_tinh,
        `la_chuyen_rieng_cua_sep`/`is_search_request` ở web_search). Thẻ dễ lẫn
        thì ở cạnh nhau — nên nhóm là chỗ phải chứa cái phân biệt.
        """
        return self.mo_dun

    def tu_khoa(self) -> set[str]:
        return _tu(self.ten) | _tu(self.mo_ta)

    def tu_tai_lieu(self) -> set[str]:
        """Từ chỉ có trong TOÀN VĂN tài liệu, không có ở tên hay dòng đầu.

        `mo_ta` là DÒNG ĐẦU docstring, mà dòng đầu hay tả GIÁ TRỊ TRẢ VỀ chứ
        không tả việc: `tinh_giup` mở đầu bằng *"Một dòng 'đã tính sẵn' để nhét
        vào lời dặn"*. Đo 20/08: chấm thêm toàn văn kéo trần khay 15 thẻ từ
        24/28 lên 25/28, và cứu đúng `la_chuyen_rieng_cua_sep` — việc "chặn
        không cho đẩy đời tư của chủ máy ra ngoài" chung `day`/`doi`/`may` với
        thân tài liệu mà không chung chữ nào với dòng đầu.
        """
        return _tu(self.tai_lieu) - self.tu_khoa()

    def dong_khay(self) -> str:
        d = f"  {self.chu_ky}   (từ {self.mo_dun})"
        if self.mo_ta:
            d += f"\n      {self.mo_ta}"
        if self.phan_biet:
            d += f"\n      -> {self.phan_biet}"
        return d


def _cau(s: str) -> list[str]:
    """Tách tài liệu thành CÂU, không thành dòng.

    Bản đầu tách theo cả `\\n` nên câu bị chặt giữa chừng — tài liệu gói dòng ở
    79 ký tự, xuống dòng trong câu chỉ là chỗ gói. Kết quả là dòng phân biệt in
    ra những mẩu cụt: "mà model chỉ việc chép lại", "riêng của Sếp ra máy tìm
    kiếm." Nối dòng trong cùng đoạn lại trước, rồi mới tách theo dấu kết câu.
    """
    doan = re.split(r"\n\s*\n", (s or "").strip())
    cau = []
    for d in doan:
        lien = re.sub(r"\s*\n\s*", " ", d).strip()
        cau += [c.strip() for c in re.split(r"(?<=[.!?])\s+", lien)]
    return [c for c in cau if len(c) > 20]


def gan_phan_biet(khay: list[The]) -> list[The]:
    """Điền `phan_biet` cho mỗi thẻ — thứ tách nó khỏi ANH EM CÙNG NHÓM.

    Đo 19/08: lọc khay từ 65 xuống 12 thẻ KHÔNG cải thiện gì (4/6 -> 4/6), và
    hỏng đúng hai đề ở cả hai điều kiện. Thẻ đúng NẰM TRONG khay, model vẫn lấy
    nhầm thẻ hàng xóm. Nên nút thắt không phải cỡ khay mà là **thẻ na ná nhau**.

    Khay chỉ in dòng đầu tài liệu, mà dòng đầu của hai thẻ hàng xóm nghe giống
    nhau. Thứ phân biệt nằm ở phần sau — hoặc ở quan hệ gọi nhau.

    Hai tín hiệu, đều do MÁY rút, không ai viết tay (viết tay thì cũ đi, và thẻ
    cũ tệ hơn không có thẻ):

    1. TẦNG — A gọi B trong cùng mô-đun thì A là tầng ngoài. Chắc chắn, đọc từ
       cây cú pháp. Đúng cặp model hỏng: `tinh_giup` GỌI `tinh_bieu_thuc`, và
       model chọn nhầm cái tầng trong.
    2. CÂU HIẾM TRONG NHÓM — câu nào trong tài liệu chứa từ mà anh em cùng nhóm
       không có. Dùng cho cặp ngang hàng không gọi nhau.
    """
    theo_nhom: dict[str, list[The]] = {}
    for t in khay:
        theo_nhom.setdefault(t.nhom, []).append(t)

    ra: list[The] = []
    for nhom, ds in theo_nhom.items():
        ten_trong_nhom = {t.ten for t in ds}
        # từ nào phổ biến trong chính nhóm này thì không phân biệt được gì
        dem: dict[str, int] = {}
        for t in ds:
            for w in _tu(t.tai_lieu):
                dem[w] = dem.get(w, 0) + 1

        for t in ds:
            manh = []
            goi_trong_nhom = sorted(t.goi & ten_trong_nhom)
            if goi_trong_nhom:
                manh.append("TẦNG NGOÀI, bên trong nó gọi "
                            + ", ".join(goi_trong_nhom[:3]))
            if len(ds) > 1:
                tot, diem_tot = "", 0.0
                for c in _cau(t.tai_lieu)[1:]:      # bỏ dòng 1, đã in ở mo_ta
                    tu = _tu(c)
                    if not tu:
                        continue
                    d = sum(1.0 / dem.get(w, 1) for w in tu) / (len(tu) ** 0.5)
                    if d > diem_tot:
                        tot, diem_tot = c, d
                if tot:
                    manh.append(tot[:110])
            ra.append(The(t.ten, t.mo_dun, t.chu_ky, t.mo_ta, t.bam, t.goi,
                          t.tai_lieu, "  ·  ".join(manh)))
    return ra


def sinh_khay(goc: Path, thu_muc: tuple[str, ...] = ("core", "interface", "tools")) -> list[The]:
    """Đọc cây cú pháp, sinh thẻ từ hàm CÔNG KHAI có thật. Không chép tay."""
    ra: dict[str, The] = {}
    for tm in thu_muc:
        d = goc / tm
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            try:
                nguon = f.read_text(encoding="utf-8")
                cay = ast.parse(nguon)
            except (OSError, SyntaxError):
                continue
            for n in cay.body:
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if n.name.startswith("_") or n.name in ra:
                    continue
                tai_lieu = (ast.get_docstring(n) or "").strip()
                doc = tai_lieu.splitlines()
                than = ast.get_source_segment(nguon, n) or n.name
                goi = {c.func.id for c in ast.walk(n)
                       if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
                ra[n.name] = The(
                    ten=n.name,
                    mo_dun=f"{tm}.{f.stem}",
                    chu_ky=f"{n.name}({', '.join(a.arg for a in n.args.args)})",
                    mo_ta=(doc[0] if doc else "")[:90],
                    bam=hashlib.sha256(than.encode("utf-8")).hexdigest()[:12],
                    goi=frozenset(goi - {n.name}),
                    tai_lieu=tai_lieu,
                )
    return gan_phan_biet(list(ra.values()))


def loc_khay(khay: list[The], viec: str, giu: int = 24) -> list[The]:
    """Giữ `giu` thẻ liên quan nhất tới mô tả việc. Thuần máy, không gọi model.

    MẶC ĐỊNH 24, chốt 20/08 sau khi đo đủ lưới trên 28 đề với qwen3.5:4b:

        khay  trần    chọn đúng   đúng/khi có mặt   giây
          8   23/28   22/28       22/23 =  96%       322
         15   26/28   24/28       24/26 =  92%       505
         24   28/28   25/28       25/28 =  89%       579   <- chốt
         30   28/28   25/28       25/28 =  89%       875

    Hai xu hướng kéo ngược nhau: khay to thì TRẦN cao hơn (23 -> 28/28) nhưng
    model CHÍNH XÁC KÉM đi (96% -> 89%). Tích của chúng đạt đỉnh ở khay to, và
    trần bão hoà đúng ở 24 — 30 hoà điểm mà chậm hơn 34%, nên lấy 24.

    Mặc định cũ là 8, đúng với khay CHƯA CÓ docstring. Sau khi viết docstring
    cho 25 hàm thì nền đổi dưới chân nó: thẻ phân biệt được nhau nên khay to
    hết loãng. Không phải quyết định cũ sai, mà là điều kiện đã đổi.

    BẢN ĐẦU CHỈ ĐƯỢC 3/6 — mất thẻ đúng nửa số lần. Hai lỗi:

    1. Đếm từ chung trần trụi. Một từ phổ biến như "hoi" hay "tra" khớp với
       nửa cái khay, nên thẻ nào cũng được 1 điểm và thứ tự thành ngẫu nhiên.
    2. Câu phá hoà viết ngược hẳn ý định: chú thích ghi "giữ mô tả ngắn hơn",
       mã lại sắp `-x[1]` với `x[1] = -len(mo_ta)`, tức ƯU TIÊN MÔ TẢ DÀI —
       đúng loại thẻ khớp nhờ nhiễu.

    Bản này chấm theo ĐỘ HIẾM: một từ có mặt ở 40/65 thẻ gần như vô nghĩa, từ
    chỉ có ở 2 thẻ thì đáng giá. Đó cũng là lý do bỏ luôn danh sách từ-bỏ-qua
    chép tay — tự đếm thì đúng hơn, và không bỏ nhầm từ có nghĩa trong nghề
    như "tra" hay "gio".

    TÊN thẻ nặng gấp ba MÔ TẢ: tên là thứ người viết đặt để gọi đúng việc, còn
    mô tả là văn xuôi và dễ trùng ngẫu nhiên.
    """
    if not khay:
        return []
    # độ hiếm: từ càng ít thẻ chứa thì càng đáng tin
    dem: dict[str, int] = {}
    for t in khay:
        for w in t.tu_khoa() | t.tu_tai_lieu():
            dem[w] = dem.get(w, 0) + 1
    n = len(khay)

    tu_viec = _tu(viec)
    cham = []
    for t in khay:
        tu_ten, tu_mo, tu_tl = _tu(t.ten), _tu(t.mo_ta), t.tu_tai_lieu()
        d = 0.0
        for w in tu_viec:
            if w not in dem:
                continue
            hiem = (n / dem[w]) ** 0.5        # có ở ít thẻ -> điểm cao
            if w in tu_ten:
                d += 3.0 * hiem
            elif w in tu_mo:
                d += 1.0 * hiem
            elif w in tu_tl:
                # NỬA ĐIỂM cho thân tài liệu. Đo 20/08 cả hai mức: 0,5 kéo trần
                # khay 15 từ 24/28 lên 25/28, còn 1,0 thì TỤT xuống 24/28 — thân
                # tài liệu dài nên trọng số đủ mạnh là kéo cả thẻ nhiễu lên.
                d += 0.5 * hiem
        # hoà thì mô tả NGẮN thắng — dài là dễ trùng nhờ nhiễu
        cham.append((d, -len(t.mo_ta), t))
    cham.sort(key=lambda x: (x[0], x[1]), reverse=True)
    # KHÔNG loại thẻ điểm 0 nữa, chỉ xếp chúng xuống cuối.
    #
    # Bản cũ có `if d > 0` nên thẻ không khớp từ nào bị vứt HẲN, và `giu` mất
    # nghĩa: đo 20/08, xin cả 96 thẻ vẫn chỉ nhận về 25/28 đáp án đúng, ba đề
    # KHÔNG MODEL NÀO thắng được. Nay xin 96 thì nhận đủ 28/28 — trần khay bằng
    # đúng cỡ khay, còn thắng hay không là việc của model.
    return [t for _, _, t in cham[:giu]]


def bang_khay(khay: list[The], theo_nhom: bool = True) -> str:
    """In khay. Mặc định GOM THEO NHÓM — thẻ dễ lẫn nằm cạnh nhau thì người
    (và model) mới so được chúng với nhau, thay vì gặp từng cái rời rạc."""
    if not theo_nhom:
        return "\n".join(t.dong_khay() for t in khay)
    nhom: dict[str, list[The]] = {}
    for t in khay:
        nhom.setdefault(t.nhom, []).append(t)
    d = []
    for ten, ds in nhom.items():
        d.append(f"[nhóm {ten}]")
        d += [t.dong_khay() for t in ds]
    return "\n".join(d)


def the_da_cu(khay: list[The], goc: Path) -> list[The]:
    """Thẻ nào không còn khớp mã nguồn hiện tại.

    Đây là lý do thẻ sinh-ra phải sinh lại: hàm bị sửa hay bị xoá thì thẻ cũ
    vẫn nằm đó, và model sẽ gọi nó một cách tự tin.
    """
    moi = {t.ten: t.bam for t in sinh_khay(goc)}
    return [t for t in khay if moi.get(t.ten) != t.bam]


# ---------------------------------------------------------------------------
# THẺ TỪ THƯ VIỆN CÀI NGOÀI
#
# Sếp hỏi 20/08: thư viện mới tải về và hàm người dùng tự viết thì app lấy đâu
# ra mô tả để phân loại. Đo trên chính máy này:
#
#     hàm kho tự viết (280 hàm)   48% có docstring · 90% CÓ CHÚ KIỂU
#     libcst   222 hàm   100% có tài liệu      pathlib  100%
#     re        94%      json 88%   aiohttp 89%   yaml 33%  <- kém nhất
#
# Nên KHÔNG cần hỏi model để biết một hàm làm gì: `inspect` đọc thẳng được chữ
# ký và tài liệu mà người viết thư viện đã để sẵn. Máy đọc cái có thật; model
# chỉ được đụng vào chỗ máy đọc không ra, và khi đó vẫn phải vào sổ kèm băm.
#
# `sinh_khay` ở trên đọc MÃ NGUỒN của kho bằng AST. Hàm dưới đây đọc GÓI ĐÃ CÀI
# bằng introspect — nhiều gói không phát hành mã nguồn, nhưng chữ ký và tài liệu
# thì luôn có trong đối tượng đang chạy.
# ---------------------------------------------------------------------------

def sinh_khay_thu_vien(goi_ten: tuple[str, ...],
                       toi_da_moi_goi: int = 40) -> list[The]:
    """Sinh thẻ từ gói đã cài, bằng `inspect`, không đọc tệp mã nguồn.

    Băm dựng từ PHIÊN BẢN GÓI + chữ ký + dòng tài liệu đầu, nên nâng cấp gói là
    băm lệch và `the_da_cu` bắt được — cùng cơ chế đã dùng cho mã của kho.
    Không có băm thì thẻ sẽ âm thầm mô tả sai sau mỗi lần `pip install -U`.
    """
    import importlib
    import importlib.metadata as md
    import inspect

    ra: list[The] = []
    for ten_goi in goi_ten:
        try:
            m = importlib.import_module(ten_goi)
        except Exception:
            continue                       # gói chưa cài thì bỏ qua, không nổ
        try:
            ban = md.version(ten_goi)
        except Exception:
            ban = getattr(m, "__version__", "?")
        # `__all__` là danh sách tác giả gói CÔNG BỐ; `dir()` là tất cả những gì
        # lọt ra ngoài. Ưu tiên cái tác giả công bố.
        ten_ds = list(getattr(m, "__all__", None) or
                      [x for x in dir(m) if not x.startswith("_")])
        dem = 0
        for nm in ten_ds:
            if dem >= toi_da_moi_goi:
                break
            o = getattr(m, nm, None)
            if o is None or not (inspect.isfunction(o) or inspect.isclass(o)
                                 or inspect.isbuiltin(o)):
                continue
            try:
                ck = "%s%s" % (nm, inspect.signature(o))
            except (TypeError, ValueError):
                ck = "%s(...)" % nm         # gói C không luôn có chữ ký
            tai_lieu = (inspect.getdoc(o) or "").strip()
            d = tai_lieu.splitlines()
            ra.append(The(
                ten="%s.%s" % (ten_goi, nm),
                mo_dun="%s %s" % (ten_goi, ban),
                chu_ky=ck if len(ck) <= 120 else ck[:117] + "...",
                mo_ta=(d[0] if d else "")[:90],
                bam=hashlib.sha256(
                    ("%s|%s|%s" % (ban, ck, d[0] if d else ""))
                    .encode("utf-8")).hexdigest()[:12],
                tai_lieu=tai_lieu,
            ))
            dem += 1
    return gan_phan_biet(ra)


def khay_day_du(goc: Path, goi_ten: tuple[str, ...] = ()) -> list[The]:
    """Khay gộp: hàm của kho (đọc mã) + hàm của gói đã cài (introspect).

    Hai nguồn KHÁC NHAU nên giữ riêng hai hàm sinh, chỉ gộp ở đây — thẻ kho có
    băm theo mã nguồn, thẻ gói có băm theo phiên bản, và trộn hai cách băm vào
    một hàm là mở đường cho một loại thẻ cũ đi mà không ai bắt được.
    """
    return sinh_khay(goc) + sinh_khay_thu_vien(goi_ten)
