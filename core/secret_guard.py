# -*- coding: utf-8 -*-
"""Cổng BÍ MẬT — AURA Chat không phải kho mật khẩu.

Vì sao tệp này ra đời (09/08/2026, phiên aura-chat-reboot):
Tôi dựng màn hình chat, thử bằng câu "mật khẩu wifi nhà mình là gì", AURA trả
thẳng mật khẩu ra màn hình — và tôi **chụp lại làm bằng chứng thành công**.
Codex xem xong nói đúng một câu:

    "Đây là lỗi nghiêm trọng hơn việc không trả lời được."

Anh ấy đúng. Một trợ lý câm thì vô dụng; một trợ lý đọc to mật khẩu trên bất kỳ
bề mặt chat nào thì nguy hiểm — và nguy hiểm không có báo động.

Hai lớp, tách bạch:
  * `is_secret_request()` — chặn Ở ĐẦU VÀO, trước khi gọi model hay tra mạng.
    Không tìm, không đọc, không kèm gợi ý "chỗ đó nằm ở đâu".
  * `core.redact.redact()` — che Ở ĐẦU RA và trước khi ghi nhật ký, phòng khi
    bí mật lọt vào qua đường khác.

Ranh giới cố ý: đây là cổng cho BỀ MẶT CHAT. Công cụ cục bộ như `wifi_manager`
vẫn giữ nguyên cho các đường dùng riêng có chủ đích — cổng này chỉ bảo đảm
đường chat không trở thành cái loa.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Sequence, overload

from core.chat_contract import (
    ChatRequest,
    ContentCheck,
    OutwardContent,
    SourceCitation,
)

if TYPE_CHECKING:
    from core.chat_service import ChatMessage

# Thứ cần bảo vệ. Đặt tên rộng: thà từ chối nhầm còn hơn đọc to nhầm.
_SECRET_NOUNS = (
    r"m[aậ]t\s*kh[aẩ]u", r"password", r"passwd", r"\bpwd\b",
    r"api[\s_-]*key", r"\bapikey\b", r"\btoken\b", r"secret",
    r"credential", r"\bcookie\b", r"private\s*key",
    # Dấu tiếng Việt rơi vào ĐÚNG chỗ dễ sót: "khoá" khác "khoa", nên phải cho
    # cả hai. Bản đầu viết `kh[oó]a` và câu "in ra các khoá bí mật" lọt thẳng.
    r"kh[oó][aá]\s*b[ií]\s*m[aậ]t", r"b[ií]\s*m[aậ]t",
    r"m[aã]\s*pin", r"\botp\b", r"m[aã]\s*x[aá]c\s*nh[aậ]n",
    r"\.env\b", r"env\s*file", r"chu[oỗ]i\s*k[eế]t\s*n[oố]i",
    r"connection\s*string", r"s[oố]\s*th[eẻ]", r"cvv",
)
# Động từ moi tin. Tách riêng để "cách đổi mật khẩu" KHÔNG bị chặn oan.
_ASK_VERBS = (
    r"l[aà]\s*g[iì]", r"bao\s*nhi[eê]u", r"cho\s*(?:t[oô]i|xem|bi[eế]t)",
    r"n[oó]i\s*(?:cho|t[oô]i)", r"nh[aắ]c\s*l[aạ]i", r"đ[oọ]c\s*(?:l[eê]n|cho)",
    r"in\s*ra", r"li[eệ]t\s*k[eê]", r"xem\s*(?:gi[uú]p|h[oộ])?",
    r"what(?:\s+is|'s)", r"show(?:\s*me)?", r"display", r"tell\s*me",
    r"print", r"reveal", r"list", r"copy", r"send(?:\s*me)?",
    r"give(?:\s*me)?", r"provide", r"output", r"expose",
    r"g[uử]i\s*(?:cho|qua)?", r"d[aá]n\s*(?:ra|v[aà]o)",
    r"đ[uư]a(?:\s+cho\s+t[oô]i|\s+.*?\s+đ[aâ]y)?", r"hi[eể]n\s*th[iị]",
    r"l[aấ]y\s*ra", r"xu[aấ]t\s*ra",
)

_NOUN_RE = re.compile("|".join(_SECRET_NOUNS), re.IGNORECASE)
_VERB_RE = re.compile("|".join(_ASK_VERBS), re.IGNORECASE)
# Câu hỏi cách làm thì cho qua: người ta hỏi CÁCH, không đòi GIÁ TRỊ.
_HOWTO_RE = re.compile(
    r"(?i)\b(c[aá]ch|l[aà]m\s*sao|how(?:\s+do\s+i)?\s+to|"
    r"h[uư][oớ]ng\s*d[aẫ]n)\b.{0,80}"
    r"\b(đ[oổ]i|thay|đ[aặ]t|t[aạ]o|reset|c[aấ]u\s*h[iì]nh|b[aả]o\s*m[aậ]t|"
    r"qu[eê]n|change|rotate|set|create|configure|secure|recover)\b"
)
_RECOVERY_HOWTO_RE = re.compile(
    r"(?i)\b(?:qu[eê]n|forgot|lost)\b.{0,80}"
    r"\b(?:reset|kh[oô]i\s*ph[uụ]c|l[aấ]y\s*l[aạ]i|recover)\b"
)

# Một số cách nói lịch sự dùng động từ giống yêu cầu tiết lộ, nhưng thực chất
# chỉ mở đầu cho câu hỏi hướng dẫn. Loại đúng phần mở đầu này rồi mới tìm động
# từ moi tin; nếu phía sau còn "... rồi hiển thị key hiện tại" thì vẫn bị chặn.
_HOWTO_LEADIN_RE = re.compile(
    r"(?i)\b(?:show|tell)\s+me\s+how(?:\s+do\s+i)?\s+to\b|"
    r"\bcho\s+t[oô]i\s+(?:bi[eế]t|xem)\s+c[aá]ch\b"
)


# Bổ sung cục bộ cho đường chat/log. `core.redact` vẫn là lớp che dùng chung;
# các mẫu này xử lý các cách trình bày tự nhiên mà bộ lọc chung chưa nhận ra.
_CHAT_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?ix)(\b(?:m[aậ]t\s*kh[aẩ]u|password)\b"
            r"(?:\s+(?:wi-?fi|network|m[aạ]ng))?"
            r"(?:\s+(?:c[uủ]a\s+)?(?:\"[^\"\r\n]{1,80}\"|"
            r"'[^'\r\n]{1,80}'|“[^”\r\n]{1,80}”))?"
            r"\s*(?:l[aà]\s*)?[:=]\s*)"
            r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
        ),
        r"\1[REDACTED_SECRET]",
    ),
    (
        re.compile(
            r"(?ix)(\b(?:[a-z0-9]+_)*(?:api_key|access_token|refresh_token|"
            r"bot_token|token|secret|password|passwd|pwd)\s*=\s*)"
            r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
        ),
        r"\1[REDACTED_SECRET]",
    ),
    (
        re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=\-]{6,}"),
        r"\1[REDACTED_BEARER_TOKEN]",
    ),
)

REFUSAL = (
    "🔒 Em không đọc mật khẩu, khoá hay token ra màn hình chat — kể cả khi em "
    "tra được.\n"
    "Cửa chat này có thể mở trên nhiều nơi, nên một dòng bí mật lọt ra là lọt "
    "hẳn, và không có báo động nào cả.\n"
    "Sếp lấy trực tiếp từ máy nhé; em không nhắc lại và cũng không ghi nó vào "
    "nhật ký hội thoại."
)


def is_secret_request(text: str) -> bool:
    """True khi câu hỏi đang ĐÒI GIÁ TRỊ của một bí mật.

    Hỏi *cách* đổi mật khẩu thì không chặn — người ta cần trợ giúp thật, và chặn
    oan cũng là một kiểu hỏng.
    """
    raw = (text or "").strip()
    if not raw:
        return False
    if not _NOUN_RE.search(raw):
        return False

    # Đừng để "cách/how to" vô hiệu hóa cả câu. Chỉ bỏ qua đúng lời dẫn
    # lịch sự ("show me how to...") rồi tìm xem phần còn lại có đòi giá trị
    # hay không. Nhờ vậy câu hỗn hợp vẫn fail-closed.
    without_safe_leadin = _HOWTO_LEADIN_RE.sub("how to", raw)
    if _VERB_RE.search(without_safe_leadin):
        return True
    if _HOWTO_RE.search(raw) or _RECOVERY_HOWTO_RE.search(raw):
        return False

    # Trên bề mặt chat, chỉ riêng cụm "mật khẩu wifi" hay "wifi password
    # please" đã là một yêu cầu tự nhiên. Mọi nhắc tới bí mật không được nhận
    # diện rõ là hướng dẫn an toàn đều bị chặn, thay vì đoán ý tốt của người hỏi.
    return True


def scrub_for_log(text: str) -> str:
    """Che bí mật TRƯỚC khi ghi nhật ký. Không bao giờ lưu bản rõ."""
    from core.redact import redact

    cleaned = text or ""
    for pattern, replacement in _CHAT_REDACT_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return redact(cleaned)


class SecretContentGuard:
    """Adapter nhỏ, không I/O, dùng trực tiếp với ``ChatService``.

    Input hợp lệ vẫn được che trước khi ghi transcript; output luôn đi qua cùng
    một đường che. Yêu cầu moi bí mật bị chặn trước model và không lưu nguyên
    văn câu hỏi vào ``ContentCheck``.
    """

    def check_input(self, request: ChatRequest) -> ContentCheck:
        if is_secret_request(request.text):
            return ContentCheck(
                allowed=False,
                transcript_text="[REDACTED_SECRET_REQUEST]",
                rejection_text=REFUSAL,
            )
        return ContentCheck(
            allowed=True,
            transcript_text=scrub_for_log(request.text),
        )

    def scrub_history(
        self, history: Sequence[ChatMessage]
    ) -> tuple[ChatMessage, ...]:
        """Trả bản sao lịch sử chỉ gồm role/content đã được che.

        Import cục bộ tránh vòng phụ thuộc lúc nạp module; ở thời điểm phương
        thức được gọi, ``ChatService`` đã được nạp xong. Không tái sử dụng hoặc
        sửa tại chỗ message đầu vào, và không mang theo metadata lạ.
        """
        from core.chat_service import ChatMessage

        cleaned: list[ChatMessage] = []
        for item in history:
            if not isinstance(item, ChatMessage):
                raise TypeError("history must contain ChatMessage")
            cleaned.append(
                ChatMessage(
                    role=item.role,
                    content=scrub_for_log(item.content),
                )
            )
        return tuple(cleaned)

    @overload
    def scrub_output(self, content: str) -> str: ...

    @overload
    def scrub_output(self, content: OutwardContent) -> OutwardContent: ...

    def scrub_output(
        self, content: str | OutwardContent
    ) -> str | OutwardContent:
        """Che chuỗi API cũ hoặc toàn bộ gói nội dung của ``ChatService``.

        Kiểu vào nào thì trả đúng kiểu đó. Với ``OutwardContent``, dựng mới cả
        object và từng citation để không giữ tham chiếu/metadata thô.
        """
        if isinstance(content, str):
            return scrub_for_log(content)
        if not isinstance(content, OutwardContent):
            raise TypeError("content must be str or OutwardContent")

        return OutwardContent(
            text=scrub_for_log(content.text),
            sources=tuple(
                SourceCitation(
                    title=scrub_for_log(source.title),
                    url=scrub_for_log(source.url),
                    retrieved_at=scrub_for_log(source.retrieved_at),
                    supports=scrub_for_log(source.supports),
                )
                for source in content.sources
            ),
            fallback_text=scrub_for_log(content.fallback_text),
        )


__all__ = [
    "REFUSAL",
    "SecretContentGuard",
    "is_secret_request",
    "scrub_for_log",
]
