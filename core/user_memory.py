# -*- coding: utf-8 -*-
"""TRÍ NHỚ về Sếp — Markdown, Sếp đọc và sửa được bằng tay.

Mảnh thứ tư của nhân lõi AURA Chat (phiên aura-chat-reboot-20260809).

Vì sao là Markdown chứ không phải kho vector: hôm 06/08 tôi đo được **13% ký ức
cũ của AURA là rác xã giao** ("xin chào", "duyệt", "y") — và không ai biết suốt
nhiều tháng, vì nó nằm trong kho vector không mở ra xem được.  Một trí nhớ không
đọc được là một trí nhớ không sửa được, và một trí nhớ không sửa được thì càng
chạy càng bẩn.

LUẬT CỨNG, chốt ở lượt 003 của Codex:

    Câu trả lời của AI TUYỆT ĐỐI không được tự phong thành sự thật.

Ở đây luật đó không phải lời hứa trong tài liệu — nó là chữ ký hàm: `remember()`
đòi `confirmed_by_user=True`, và có test nộp thẳng một câu do AI sinh ra để chứng
minh nó bị từ chối.  Chưa có cơ chế xác nhận thì chưa tự rút ký ức.
"""
from __future__ import annotations

import logging
import re
import threading
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

from core.paths import PROJECT_ROOT

logger = logging.getLogger("aura.user_memory")

MEMORY_FILE = PROJECT_ROOT / "data" / "aura_nho_gi_ve_sep.md"
_MAX_FACT_CHARS = 500
_MAX_FACTS = 200
_LOCK = threading.Lock()

_HEADER = """# AURA nhớ gì về Sếp

<!-- Tệp này Sếp ĐỌC VÀ SỬA TAY ĐƯỢC. Xoá một dòng là AURA quên hẳn.
     AURA chỉ ghi vào đây khi Sếp xác nhận — câu do AURA tự nói KHÔNG bao giờ
     tự biến thành sự thật ở đây. -->

"""

# - [m-a1b2c3d4] nội dung  <!-- 09/08/2026 · Sếp xác nhận -->
_LINE_RE = re.compile(
    r"^-\s*\[(?P<id>m-[0-9a-f]{8})\]\s*(?P<text>.*?)\s*(?:<!--\s*(?P<meta>.*?)\s*-->)?\s*$"
)


class MemoryRefused(ValueError):
    """Từ chối ghi — thường vì chưa có xác nhận của Sếp."""


def _read_lines() -> list[str]:
    if not MEMORY_FILE.exists():
        return []
    try:
        return MEMORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        logger.warning("Không đọc được trí nhớ: %s", exc)
        return []


def list_facts() -> list[dict]:
    """Mọi điều AURA đang nhớ, theo đúng thứ tự trong tệp."""
    facts: list[dict] = []
    for line in _read_lines():
        hit = _LINE_RE.match(line.strip())
        if hit and hit.group("text").strip():
            facts.append({
                "id": hit.group("id"),
                "text": hit.group("text").strip(),
                "meta": (hit.group("meta") or "").strip(),
            })
    return facts


def _write(facts: list[dict]) -> None:
    body = "".join(
        f"- [{f['id']}] {f['text']}"
        + (f"  <!-- {f['meta']} -->" if f.get("meta") else "")
        + "\n"
        for f in facts
    )
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(_HEADER + body, encoding="utf-8", newline="\n")


def remember(text: str, *, confirmed_by_user: bool = False) -> dict:
    """Ghi một điều vào trí nhớ.  CHỈ khi Sếp xác nhận.

    `confirmed_by_user` cố ý là tham số bắt buộc-nêu-tên và mặc định False: muốn
    ghi thì phải viết ra chữ đó, không thể ghi nhầm bằng cách gọi qua loa.
    """
    if not confirmed_by_user:
        raise MemoryRefused(
            "AURA chỉ nhớ điều Sếp đã xác nhận. Câu do AURA tự nói không tự "
            "thành sự thật."
        )
    from core.secret_guard import scrub_for_log

    clean = " ".join((text or "").split())
    if not clean:
        raise MemoryRefused("Chưa có nội dung để nhớ.")
    if len(clean) > _MAX_FACT_CHARS:
        raise MemoryRefused(f"Điều cần nhớ dài quá {_MAX_FACT_CHARS} ký tự.")
    # Bí mật KHÔNG bao giờ vào trí nhớ dài hạn, kể cả khi Sếp bảo nhớ.
    clean = scrub_for_log(clean)

    with _LOCK:
        facts = list_facts()
        if any(f["text"].casefold() == clean.casefold() for f in facts):
            raise MemoryRefused("Điều này AURA đã nhớ rồi.")
        if len(facts) >= _MAX_FACTS:
            raise MemoryRefused(
                f"Trí nhớ đã đầy ({_MAX_FACTS} điều). Sếp xoá bớt rồi thêm nhé."
            )
        fact = {
            "id": f"m-{uuid.uuid4().hex[:8]}",
            "text": clean,
            "meta": f"{datetime.now().strftime('%d/%m/%Y')} · Sếp xác nhận",
        }
        facts.append(fact)
        _write(facts)
    return fact


def forget(fact_id: str) -> bool:
    """Quên một điều.  True nếu có thứ để quên."""
    with _LOCK:
        facts = list_facts()
        kept = [f for f in facts if f["id"] != fact_id]
        if len(kept) == len(facts):
            return False
        _write(kept)
    return True


def update(fact_id: str, text: str) -> bool:
    """Sửa một điều đã nhớ.  Sếp sửa thẳng trong tệp cũng có tác dụng y hệt."""
    from core.secret_guard import scrub_for_log

    clean = scrub_for_log(" ".join((text or "").split()))
    if not clean:
        raise MemoryRefused("Nội dung mới rỗng — muốn xoá thì dùng chức năng quên.")
    if len(clean) > _MAX_FACT_CHARS:
        raise MemoryRefused(f"Điều cần nhớ dài quá {_MAX_FACT_CHARS} ký tự.")
    with _LOCK:
        facts = list_facts()
        found = False
        for fact in facts:
            if fact["id"] == fact_id:
                fact["text"] = clean
                fact["meta"] = f"{datetime.now().strftime('%d/%m/%Y')} · Sếp sửa"
                found = True
        if found:
            _write(facts)
    return found


# --------------------------------------------------------------------------- #
# Nhận biết câu "nhớ giúp tôi ..." — bằng LUẬT, không hỏi model.
# --------------------------------------------------------------------------- #
# Viết bằng các BƯỚC thay vì một biểu thức chính quy dài: bản regex mất ba vòng
# dò mà vẫn nuốt nhầm chữ, còn cách này đọc là biết nó làm gì.
_PREFIXES = ("aura", "hãy", "hay")
_VERBS = ("ghi nhớ", "ghi nho", "nhớ", "nho", "remember")
_HELPERS = ("giúp", "giup", "hộ", "ho")
_SUBJECTS = ("tôi", "toi", "mình", "minh", "me")
_LINKERS = ("là", "la", "rằng", "rang", "that")


def _strip_word(text: str, words: tuple[str, ...]) -> str | None:
    """Bỏ một từ ở đầu câu nếu có, trả phần còn lại.  None nếu không khớp."""
    low = text.lower()
    for word in words:
        if low.startswith(word):
            rest = text[len(word):]
            if not rest or rest[0].isspace() or rest[0] in ":-":
                return rest.lstrip()
    return None


def parse_remember(text: str) -> str | None:
    """Trả nội dung cần nhớ nếu Sếp đang RA LỆNH nhớ, ngược lại None.

    Chỉ câu mệnh lệnh rõ ràng mới tính là xác nhận.  Không suy diễn từ hội thoại
    thường — đó đúng là cách kho ký ức cũ đầy rác.

    Chuẩn hoá NFC trước vì "là" có thể là ký tự dựng sẵn hoặc "a" + dấu huyền
    rời — hôm nay tôi dính đúng lỗi dấu tiếng Việt này ở ba tệp khác nhau.
    """
    rest = unicodedata.normalize("NFC", text or "").strip()
    if not rest:
        return None

    for _ in range(2):                      # bỏ tối đa "aura hãy"
        stripped = _strip_word(rest, _PREFIXES)
        if stripped is None:
            break
        rest = stripped

    after_verb = _strip_word(rest, _VERBS)
    if after_verb is None:
        return None                          # không phải câu ra lệnh nhớ
    rest = after_verb

    if rest[:1] in (":", "-"):               # "ghi nhớ: ..." -> lấy hết phần sau
        return rest[1:].strip() or None

    helped = _strip_word(rest, _HELPERS)     # "nhớ giúp ..."
    if helped is not None:
        rest = helped

    # "tôi/mình" chỉ bị bỏ khi có "là/rằng" ngay sau — nếu không, nó là CHỦ NGỮ
    # của điều cần nhớ ("nhớ tôi làm việc ban đêm").
    without_subject = _strip_word(rest, _SUBJECTS)
    if without_subject is not None:
        without_linker = _strip_word(without_subject, _LINKERS)
        if without_linker is not None:
            rest = without_linker

    return rest.strip() or None


def as_prompt_block() -> str:
    """Khối ngắn để nhét vào prompt.  Rỗng nếu chưa nhớ gì."""
    facts = list_facts()
    if not facts:
        return ""
    lines = "\n".join(f"- {f['text']}" for f in facts)
    return f"AURA đang nhớ những điều sau về Sếp (do Sếp tự xác nhận):\n{lines}"
