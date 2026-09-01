# -*- coding: utf-8 -*-
"""soi_model.py — cổng hỏi model LOCAL cho App Thẻ.

VÌ SAO CÓ TỆP NÀY. Bảng "Soi Chương Trình" đọc cây thẻ rồi trả lời theo luật,
và nó cố ý **không** có model nào (xem `docYDinhCauHoi` trong `app.js`). Nhưng
bốn việc theo luật không phủ hết: hỏi ngoài bốn việc thì nó nói thẳng "chưa
hiểu". Tệp này là chỗ để người dùng TỰ CHỌN có mượn một model local hay không.

CHỈ LOCAL. Không có đường ra cloud ở đây, không có chỗ dán khoá API. Ollama
chạy trên `127.0.0.1` là một tiến trình trên chính máy người dùng — nó không
phải "gửi ra ngoài" theo nghĩa của CLAUDE.md mục 2, và tệp này không mở thêm
đường nào khác.

BA CON SỐ ĐÃ ĐO trên máy này (i5, không GPU rời), chép từ
`core/local_first_gateway.py` — đó là lý do cho từng tham số dưới đây:

    bật "nghĩ thầm"     339 giây   <- qwen3.5 nghĩ 7.630 ký tự để đẻ 239 ký tự
    tắt "nghĩ thầm"      24,8 giây <- nhanh 13,7 lần, CHỈ đổi một cờ
    giữ model trong RAM  5-9 giây  <- khỏi nạp lại 3,4 GB mỗi câu

Nên: `think=False` mặc định, và `keep_alive` giữ model lại giữa các câu.

FAIL-CLOSED. Mọi hỏng hóc đều trả về "không dùng được" KÈM LÝ DO đọc được,
không ném ngoại lệ lên giao diện và không im lặng trả về rỗng. Người dùng phải
biết vì sao ô chọn model trống, nếu không họ tưởng app hỏng.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Tuple

import httpx

# `127.0.0.1` chứ không `localhost`: trên Windows `localhost` có thể phân giải
# ra `::1` trước, và Ollama bản cũ chỉ nghe IPv4 — khi đó phép dò trượt trong
# khi Ollama vẫn đang chạy. Đo 01/09/2026: cả hai đều trả HTTP 200 trên máy
# này, nhưng chọn dạng chắc chắn hơn.
HOST_MAC_DINH = "http://127.0.0.1:11434"

# Trần cho phép DÒ. Phải NGẮN: giao diện gọi lúc mở app, và người không cài
# Ollama là số đông. Chờ 30 giây để biết "không có" là chặn người ta 30 giây
# vì một thứ họ không dùng.
TRAN_DO_GIAY = 1.5

# Trần cho một câu hỏi thật. 5,9 tok/s nghĩa là 200 chữ mất khoảng 45 giây,
# nên 90 giây mới đủ chỗ cho một câu trả lời dài mà không cắt ngang.
TRAN_HOI_GIAY = 90.0

# Giữ model trong RAM bao lâu sau câu cuối. Đổi lại ~3,4 GB RAM bị giữ; trên
# máy 11,7 GB thì 5 phút là mức chịu được, và nó cắt 29 giây nạp lại xuống 5-9.
GIU_TRONG_RAM = "5m"


@dataclass
class TinhTrangModel:
    """Máy này có model local dùng được không, và nếu không thì vì sao."""

    co_ollama: bool
    host: str
    cac_model: List[str] = field(default_factory=list)
    ly_do: str = ""
    ms: int = 0


def do_ollama(host: str = HOST_MAC_DINH, tran_giay: float = TRAN_DO_GIAY) -> TinhTrangModel:
    """Ollama có đang chạy không, và có sẵn những model nào?

    KHÔNG ném ngoại lệ. Mọi ca hỏng đều thành `co_ollama=False` kèm `ly_do`
    viết cho người đọc, vì câu này đi thẳng lên giao diện.
    """
    t0 = time.perf_counter()
    try:
        r = httpx.get(f"{host}/api/tags", timeout=tran_giay)
    except httpx.ConnectError:
        return TinhTrangModel(
            False, host, ly_do=(
                "Không thấy Ollama trên máy. Nếu bạn có cài, mở nó lên (hoặc "
                "chạy `ollama serve`) rồi tải lại trang."),
            ms=int((time.perf_counter() - t0) * 1000))
    except httpx.TimeoutException:
        return TinhTrangModel(
            False, host, ly_do=(
                f"Ollama không trả lời trong {tran_giay:g} giây. Có thể nó "
                "đang bận nạp một model khác."),
            ms=int((time.perf_counter() - t0) * 1000))
    except Exception as loi:  # noqa: BLE001 — câu này đi lên màn hình, không được ném
        return TinhTrangModel(
            False, host, ly_do=f"Không dò được Ollama: {type(loi).__name__}",
            ms=int((time.perf_counter() - t0) * 1000))

    ms = int((time.perf_counter() - t0) * 1000)
    if r.status_code != 200:
        return TinhTrangModel(
            False, host, ly_do=f"Ollama trả HTTP {r.status_code}", ms=ms)

    try:
        cac = [m["name"] for m in r.json().get("models", []) if m.get("name")]
    except Exception:  # noqa: BLE001
        return TinhTrangModel(
            False, host, ly_do="Ollama trả về thứ không đọc được", ms=ms)

    if not cac:
        # PHÂN BIỆT với "không có Ollama". Hai câu khác nhau dẫn tới hai việc
        # khác nhau: một bên đi cài Ollama, một bên chỉ cần `ollama pull`.
        return TinhTrangModel(
            False, host, ly_do=(
                "Ollama có chạy nhưng CHƯA TẢI model nào. Chạy "
                "`ollama pull qwen3:1.7b` rồi tải lại trang."),
            ms=ms)

    return TinhTrangModel(True, host, cac_model=sorted(cac), ms=ms)


def dung_loi_dan(cau_hoi: str, ma_python: str) -> str:
    """Ghép câu hỏi với chương trình của người học.

    DỮ KIỆN NẰM CẠNH CÂU HỎI, không chôn trong lời dặn hệ thống — luật ở
    CLAUDE.md mục 3, đo được: nhét vào `system_prompt` thì model bỏ qua, gắn
    vào lượt của người dùng thì nó dùng.
    """
    ma = (ma_python or "").strip()
    if len(ma) > 4000:
        # Cắt để câu hỏi không nuốt hết cửa sổ ngữ cảnh của một model 4B. Nói
        # RÕ là đã cắt, không lặng lẽ đưa một chương trình cụt cho model rồi
        # nhận về lời bình về đoạn nó không thấy.
        ma = ma[:4000] + "\n# ... (đã cắt bớt, chương trình còn dài)"
    khoi = f"```python\n{ma}\n```" if ma else "(chưa có mã nào)"
    # CÂU DẶN CUỐI ĐÃ SUÝT BỊ BỎ. Đo 01/09/2026 cho thấy nó gây hại:
    #     có câu dặn   1/6 lần model nói "không đủ" cho một câu TRẢ LỜI ĐƯỢC
    #     bỏ câu dặn   0/6 lần nói sai như vậy
    # Nhưng ca đối chứng — hỏi thứ chương trình KHÔNG có — lật ngược lại:
    #     có câu dặn   4/4 từ chối đúng
    #     bỏ câu dặn   3/4 đúng, 1 ca BỊA: qwen3:1.7b dựng ra cả một hàm
    #                  `doc_tep()` không hề tồn tại rồi giải thích nó làm gì
    # Một lời từ chối nhầm thì người học hỏi lại. Một câu bịa thì họ đi sửa mã
    # theo thứ không có thật. Giữ câu dặn.
    return (
        "Đây là chương trình Python của một người mới học, dựng bằng cách kéo "
        "thả thẻ:\n\n"
        f"{khoi}\n\n"
        f"Câu hỏi của họ: {cau_hoi}\n\n"
        "Trả lời ngắn gọn bằng tiếng Việt. Nếu chương trình trên không đủ để "
        "trả lời, hãy nói thẳng là không đủ."
    )


def hoi_model(
    cau_hoi: str,
    model: str,
    ma_python: str = "",
    host: str = HOST_MAC_DINH,
    tran_giay: float = TRAN_HOI_GIAY,
) -> Tuple[bool, str, int, str]:
    """Hỏi một model local. Trả `(ok, tra_loi, ms, ly_do)`.

    `ok=False` thì `tra_loi` rỗng và `ly_do` là câu giải thích cho người dùng.
    Không bao giờ trả về một chuỗi rỗng mà bảo là thành công.
    """
    if not (cau_hoi or "").strip():
        return False, "", 0, "Câu hỏi rỗng."
    if not (model or "").strip():
        return False, "", 0, "Chưa chọn model nào."

    t0 = time.perf_counter()
    try:
        r = httpx.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": dung_loi_dan(cau_hoi, ma_python),
                "stream": False,
                # TẮT "nghĩ thầm". Đo 10/08: bật thì 339 giây, tắt còn 24,8 —
                # nhanh 13,7 lần chỉ bằng một cờ. Người học chờ 45 giây đã là
                # nhiều; 339 giây thì không ai dùng.
                "think": False,
                "keep_alive": GIU_TRONG_RAM,
            },
            timeout=tran_giay,
        )
    except httpx.TimeoutException:
        return False, "", int((time.perf_counter() - t0) * 1000), (
            f"Model không trả lời xong trong {tran_giay:g} giây. Máy không có "
            "GPU rời thì model sinh chữ khoảng 6 chữ/giây — câu dài sẽ quá giờ.")
    except httpx.ConnectError:
        return False, "", int((time.perf_counter() - t0) * 1000), (
            "Mất kết nối tới Ollama giữa chừng. Nó còn đang chạy chứ?")
    except Exception as loi:  # noqa: BLE001
        return False, "", int((time.perf_counter() - t0) * 1000), (
            f"Hỏi model không xong: {type(loi).__name__}")

    ms = int((time.perf_counter() - t0) * 1000)
    if r.status_code != 200:
        # Ollama trả câu lỗi có nghĩa (ví dụ model chưa tải) — đưa nguyên cho
        # người dùng thay vì nuốt thành "lỗi không rõ".
        chi_tiet = ""
        try:
            chi_tiet = str(r.json().get("error", ""))[:200]
        except Exception:  # noqa: BLE001
            chi_tiet = r.text[:200]
        return False, "", ms, f"Ollama trả HTTP {r.status_code}: {chi_tiet}"

    try:
        tra = str(r.json().get("response", "")).strip()
    except Exception:  # noqa: BLE001
        return False, "", ms, "Ollama trả về thứ không đọc được."

    if not tra:
        # RỖNG LÀ HỎNG, không phải "trả lời ngắn". Đây đúng chỗ dễ nuốt lỗi
        # nhất: đưa chuỗi rỗng lên màn hình thì trông như model đã trả lời.
        return False, "", ms, (
            "Model chạy xong nhưng không nói gì. Thử lại, hoặc chọn model khác.")

    return True, tra, ms, ""
