# -*- coding: utf-8 -*-
"""Kho tra cứu cục bộ — `tra kho: <câu hỏi>` trả về BA đoạn kèm nguồn.

Đăng ký ở `KY_LUAT_THUC_THI.md` mục *"Kho tra cứu cục bộ"*; kế hoạch đầy đủ ở
`docs/KE_HOACH_KHO_TRA_CUU_2026-09-08.md`. Sếp duyệt 08/09/2026.

VÌ SAO HIỆN **BA** ĐOẠN, KHÔNG HIỆN MỘT — và đây là con số quyết định thiết kế.
Hai bộ câu hỏi, bộ B viết TRƯỚC khi biết thiết kế nào thắng:

    RRF, bỏ docs/lich_su/   bộ A (dùng để chọn)   bộ B (giữ riêng)
      top-1                       7/10                 4/10
      top-3                       8/10                 8/10

top-1 tụt gần một nửa giữa hai bộ — đúng hình dạng của việc chỉnh theo 10 câu.
`top-3 = 8/10` là con số ổn định duy nhất. Nên máy này KHÔNG được phép nói
"đây là câu trả lời"; nó đưa ba đoạn kèm tên tệp và để Sếp tự chấm.

VÌ SAO KHÔNG CÓ CỔNG "KHÔNG TÌM THẤY". Khe giữa nhóm câu có đáp án
(BM25 8,55–22,60) và nhóm không có (7,59–8,54) là **0,01** trên thang rộng 15
điểm — trùng hợp chứ không phải tách rời. Dựng cổng theo ngưỡng ấy rồi chạy bộ
B thì **3/10 câu đúng bị chặn nhầm** mà *"thời tiết Hà Nội ngày mai"* **vẫn
lọt**. Cổng đổi 2 lượt trúng lấy 2/3 lượt chặn: không đáng.

VÌ SAO KHÔNG TỰ CHÈN VÀO MỌI LƯỢT. top-1 đúng 4/10, nên tự chèn đoạn hạng nhất
là rót một đoạn không liên quan vào 6/10 lượt. `CLAUDE.md` §4 đã đo được rằng
một nguồn nói sai thì model tin theo.

BA TRẠNG THÁI, KHÔNG GỘP THÀNH HAI. Tụt về BM25 **im lặng** là thứ nguy hiểm
nhất ở đây — kết quả vẫn ra, vẫn trông như thường, chỉ kém đi, và không ai biết
để đo lại. Nên mỗi lượt nói rõ nó chạy ở chế độ nào.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
import weakref
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

from core.paths import PROJECT_ROOT

# Tiền tố lệnh. Tường minh, không đoán ý — Sếp gõ thì mới tra.
LENH = "tra kho:"

SO_DOAN_HIEN = 3

# `k1=1.5`, `b=0.75`, `hang=60` là hằng số CHUẨN của BM25 và RRF trong bài gốc,
# không phải số tôi chọn rồi fit vào mẫu. Ghi ra để lần sau khỏi đi dò lại.
_BM25_K1, _BM25_B, _RRF_HANG = 1.5, 0.75, 60

MODEL_NHUNG = "bge-m3"
_URL_NHUNG = "http://127.0.0.1:11434/api/embed"
_GIU_MODEL = "30m"

CHI_MUC = PROJECT_ROOT / "data" / "tra_cuu" / "chi_muc.json"

# Ba chế độ, và lượt nào cũng phải nói ra mình chạy chế độ nào.
CHUA_DUNG = "CHUA_DUNG_CHI_MUC"
CHI_TU_KHOA = "CHI_TU_KHOA"          # Ollama không gọi được -> tụt, và BÁO
DAY_DU = "DAY_DU"


def bo_dau(s: str) -> str:
    """Sếp gõ tiếng Việt lúc có dấu lúc không — chỉ mục phải chịu được cả hai.

    Đo được: bge-m3 mất một nửa độ chính xác khi câu hỏi không dấu (top-1
    4/10 -> 2/10), còn BM25 cho kết quả **giống hệt** vì cả hai vế đều đi qua
    hàm này. Đó là lý do nửa từ khoá vẫn đáng giữ dù nó yếu hơn.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def tach_tu(s: str) -> List[str]:
    return re.findall(r"[a-z0-9_]+", bo_dau(s).lower())


def la_lenh(van_ban: str) -> bool:
    return isinstance(van_ban, str) and van_ban.strip().lower().startswith(LENH)


def boc_cau_hoi(van_ban: str) -> str:
    return van_ban.strip()[len(LENH):].strip()


class KhoTraCuu:
    """Chỉ mục đọc từ đĩa. KHÔNG tự dựng — dựng là việc của `tools/dung_chi_muc.py`.

    Dựng mất 649,8 giây cho 437 đoạn (đo 08/09); nhét vào đường chat thì
    lượt đầu tiên của mỗi ngày treo 11 phút.
    """

    def __init__(self, doan: Sequence[Dict[str, Any]],
                 vector: Sequence[Sequence[float]] | None = None) -> None:
        self.doan = list(doan)
        self.vector = [_chuan(v) for v in vector] if vector else None
        self._tui = [Counter(tach_tu(d["tieu_de"] + " " + d["noi_dung"]))
                     for d in self.doan]
        n = max(len(self.doan), 1)
        df: Counter = Counter()
        for t in self._tui:
            df.update(t.keys())
        self._idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5))
                     for w, c in df.items()}
        self._dai = [sum(t.values()) for t in self._tui]
        self._dai_tb = (sum(self._dai) / n) or 1.0

    def bm25(self, cau: str) -> List[Tuple[float, int]]:
        q = tach_tu(cau)
        ra: List[Tuple[float, int]] = []
        for i, tui in enumerate(self._tui):
            s = 0.0
            for w in q:
                f = tui.get(w, 0)
                if f:
                    s += self._idf.get(w, 0.0) * f * (_BM25_K1 + 1) / (
                        f + _BM25_K1 * (1 - _BM25_B
                                        + _BM25_B * self._dai[i] / self._dai_tb))
            if s > 0:
                ra.append((s, i))
        ra.sort(reverse=True)
        return ra

    def theo_vector(self, v_cau: Sequence[float]) -> List[Tuple[float, int]]:
        if not self.vector:
            return []
        q = _chuan(v_cau)
        return sorted(((sum(a * b for a, b in zip(q, v)), i)
                       for i, v in enumerate(self.vector)), reverse=True)

    def tron(self, cau: str, v_cau: Sequence[float] | None,
             k: int = SO_DOAN_HIEN) -> List[int]:
        """Reciprocal Rank Fusion — trộn THỨ HẠNG, không trộn điểm.

        Trộn điểm thì phải chuẩn hoá hai thang khác nhau (BM25 mở, cosine nằm
        trong [-1,1]), và mọi cách chuẩn hoá đều là một hằng số tôi chọn rồi
        fit vào mẫu. Trộn thứ hạng thì không có hằng số nào của tôi.
        """
        bang = [self.bm25(cau)]
        if v_cau is not None:
            bang.append(self.theo_vector(v_cau))
        diem: Dict[int, float] = {}
        for ds in bang:
            for hang, (_, i) in enumerate(ds[:50]):
                diem[i] = diem.get(i, 0.0) + 1.0 / (_RRF_HANG + hang + 1)
        return [i for i, _ in sorted(diem.items(), key=lambda x: -x[1])[:k]]


def _chuan(v: Sequence[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def doc_chi_muc(duong=None) -> KhoTraCuu | None:
    """Trả `None` khi chưa dựng — bên gọi phải NÓI RA, không được im.

    `duong=None` rồi mới lấy `CHI_MUC` bên trong, KHÔNG đặt `duong=CHI_MUC` ở
    chữ ký: giá trị mặc định bị đóng băng lúc định nghĩa hàm, nên vá
    `tra_cuu.CHI_MUC` sang một đường khác không có tác dụng — và cửa canh
    "chưa dựng chỉ mục" không dựng nổi trạng thái nó cần đo.
    """
    duong = duong or CHI_MUC
    if not duong.is_file():
        return None
    d = json.loads(duong.read_text(encoding="utf-8"))
    return KhoTraCuu(d["doan"], d.get("vector"))


# Một `AsyncClient` cho mỗi vòng lặp sự kiện, dùng lại.
#
# ĐO 08/09, 15 lượt mỗi cách, cùng câu hỏi, cùng model đã nạp:
#     dựng client mỗi lượt   giữa 396 ms · lớn nhất 476 ms
#     dùng lại một client    giữa 187 ms · lớn nhất 424 ms
#     -> phí dựng client ≈ 194 ms, tức MỘT NỬA thời gian một lượt tra
# `httpx.AsyncClient` dựng ngữ cảnh SSL dù đây là `http://` tới localhost.
#
# Khoá theo vòng lặp chứ không phải một biến toàn cục: pool kết nối gắn với
# vòng lặp tạo ra nó, mà bộ test gọi `asyncio.run` nên mỗi bài một vòng lặp
# mới. `WeakKeyDictionary` để vòng lặp chết thì mục tự rụng — khoá theo `id()`
# thì một `id` được cấp lại sẽ trả về client của vòng lặp đã đóng.
_khach: "weakref.WeakKeyDictionary[Any, Any]" = weakref.WeakKeyDictionary()


def _lay_khach():
    import asyncio

    import httpx
    vong = asyncio.get_running_loop()
    k = _khach.get(vong)
    if k is None or k.is_closed:
        k = httpx.AsyncClient(timeout=20.0)
        _khach[vong] = k
    return k


async def _nhung_cau(cau: str) -> List[float] | None:
    """Nhúng câu hỏi. Hỏng thì trả `None` để bên gọi TỤT CÓ BÁO.

    Đo 08/09 trên chính đường này: giữa **187 ms**, lớn nhất 424 ms. Lượt đầu
    sau khi Ollama nhả model tốn ~6,5 giây, nên xin giữ model 30 phút.

    Con số *"115 ms"* ghi ở kế hoạch là của một que đo KHÁC — `urllib` thô
    trong một vòng lặp chặt, không dựng client, không qua `asyncio`. Nó đo
    được Ollama nhanh cỡ nào, không đo được lượt tra tốn bao lâu.
    """
    try:
        r = await _lay_khach().post(_URL_NHUNG, json={"model": MODEL_NHUNG,
                                                      "input": cau,
                                                      "keep_alive": _GIU_MODEL})
        r.raise_for_status()
        return r.json()["embeddings"][0]
    except Exception:
        # Nuốt LỖI thì được, nuốt TRẠNG THÁI thì không: bên gọi nhận `None` và
        # bắt buộc phải in ra rằng lượt này chỉ chạy nửa từ khoá.
        return None


def _dinh_dang(cau: str, kho: KhoTraCuu, chi_so: Sequence[int],
               che_do: str) -> str:
    dau = {
        DAY_DU: "3 đoạn gần nhất trên đĩa",
        CHI_TU_KHOA: ("3 đoạn gần nhất trên đĩa — CHỈ TÌM THEO TỪ KHOÁ, "
                      "không gọi được `bge-m3`, nên kết quả kém hơn bình thường"),
    }[che_do]
    dong = [f"{dau}. Em KHÔNG chắc đoạn nào đúng — Sếp đọc rồi tự chấm:", ""]
    for thu, i in enumerate(chi_so, 1):
        d = kho.doan[i]
        than = " ".join(d["noi_dung"].split())
        dong.append(f"{thu}. {d['tep']} › {d['tieu_de']}")
        dong.append(f"   {than[:400]}")
        dong.append("")
    if not chi_so:
        dong = [f"Không có đoạn nào khớp `{cau}` trong kho trên đĩa."]
    return "\n".join(dong).rstrip()


async def tra_giup(van_ban: str, kho: KhoTraCuu | None = None) -> str | None:
    """Trả câu trả lời của MÁY, hoặc `None` nếu đây không phải lệnh tra kho.

    Máy trả lời thẳng, không qua model: top-1 chỉ đúng 4/10 nên đoạn văn phải
    đến tay Sếp NGUYÊN VĂN kèm tên tệp. Để model diễn đạt lại thì nó bỏ mất
    nguồn, và một đoạn sai được viết thành câu trôi chảy là thứ khó cãi nhất.
    """
    if not la_lenh(van_ban):
        return None
    cau = boc_cau_hoi(van_ban)
    if not cau:
        return f"Cú pháp: `{LENH} <câu hỏi>`."

    if kho is None:
        kho = doc_chi_muc()
    if kho is None:
        return ("CHƯA DỰNG CHỈ MỤC nên em chưa tra được — đây KHÔNG phải "
                "'không tìm thấy'. Dựng bằng: "
                "`venv\\Scripts\\python.exe tools/dung_chi_muc.py` "
                "(một lần, đo 08/09 mất 649,8 giây cho 437 đoạn).")

    v = await _nhung_cau(cau)
    che_do = DAY_DU if v is not None else CHI_TU_KHOA
    return _dinh_dang(cau, kho, kho.tron(cau, v), che_do)
