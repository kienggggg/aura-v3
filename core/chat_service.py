"""Provider-neutral AURA Chat v1 service.

Only injected dependencies can talk to a model, the web, or storage.  Importing
this module performs no I/O and starts no background task.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from time import monotonic
from typing import Awaitable, Protocol, Sequence, TypeVar

from core.chat_contract import (
    CHAT_STAGE_HISTORY,
    CHAT_STAGE_INPUT,
    CHAT_STAGE_MODEL,
    CHAT_STAGE_PERSIST,
    CHAT_STAGE_WEB,
    ChatRequest,
    ChatResult,
    ChatStatus,
    ContentCheck,
    OutwardContent,
    SourceCitation,
    valid_citations,
)
from core.kiem_tien import gan_canh_bao
from core.web_search import (
    mang_co_song,
    is_search_request,
    la_chuyen_rieng_cua_sep,
    la_viec_tu_lam,
)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ModelReply:
    text: str
    requires_web: bool = False
    search_query: str = ""


class ModelGateway(Protocol):
    """An async, cancellation-aware model adapter."""

    async def generate(
        self,
        request: ChatRequest,
        *,
        history: Sequence[ChatMessage],
        sources: Sequence[SourceCitation] = (),
    ) -> ModelReply: ...


class WebSearchGateway(Protocol):
    async def search(self, query: str) -> Sequence[SourceCitation]: ...


class SessionStore(Protocol):
    """Cancellation-aware storage; append should be atomic in its adapter."""

    async def load(
        self, *, actor_id: str, session_id: str
    ) -> Sequence[ChatMessage]: ...

    async def append_exchange(
        self, *, request: ChatRequest, result: ChatResult
    ) -> None: ...


class FreshnessPolicy(Protocol):
    def requires_web(self, request: ChatRequest) -> bool: ...


class ContentGuard(Protocol):
    """Local safety boundary; concrete legacy guards are wired by adapters."""

    def check_input(self, request: ChatRequest) -> ContentCheck: ...

    def scrub_history(
        self, history: Sequence[ChatMessage]
    ) -> Sequence[ChatMessage]: ...

    def scrub_output(self, content: OutwardContent) -> OutwardContent: ...


class DeterministicFreshnessPolicy:
    """Shared deterministic web policy plus inherently live domains.

    ``core.web_search.is_search_request`` is the authoritative lexical policy
    used by the existing read-only search boundary. Calling it performs no
    network or filesystem I/O. Weather is inherently live even when the user
    omits words such as "today", so it is the one domain-level addition here.
    """

    # Narrow additions missing from the shared v1 classifier: direct commands
    # without "giúp/hộ", plus an inherently live domain. Kept as auditable
    # phrases rather than a second competing regular-expression policy.
    _EXPLICIT_COMMANDS = (
        "tra ",
        "tìm ",
        "kiểm tra",
        "search ",
        "lookup ",
        "check ",
        "verify ",
    )
    _INHERENTLY_LIVE_DOMAINS = ("thời tiết", "weather")

    def requires_web(self, request: ChatRequest) -> bool:
        normalized = request.text.casefold()
        # "kiểm tra" nằm trong `_EXPLICIT_COMMANDS`, nên câu "Viết giúp tôi hàm
        # Python KIỂM TRA một tên miền có hợp lệ không" bị đẩy đi tra mạng —
        # 71,7 giây và 3 nguồn chẳng liên quan cho một hàm 10 dòng.
        #
        # Việc phải TỰ LÀM thì thắng, kể cả khi câu có chữ gợi tra cứu.  Trừ
        # khi Sếp bảo tra thẳng ("tra mạng", "google") — lúc đó Sếp nói gì thì
        # làm nấy, và `is_search_request` giữ nguyên quyền đó.
        if la_viec_tu_lam(request.text) and not is_search_request(request.text):
            return False
        return (
            is_search_request(request.text)
            or any(command in normalized for command in self._EXPLICIT_COMMANDS)
            or any(
                domain in normalized for domain in self._INHERENTLY_LIVE_DOMAINS
            )
        )


class _NullWebSearch:
    async def search(self, query: str) -> Sequence[SourceCitation]:
        return ()


# "Quên" và "không biết" là HAI chuyện khác nhau, và Sếp cần phân biệt được.
# 10/08/2026 đo: đặt dữ kiện ở lượt 1, lấp đầy 7 lượt, hỏi lại ở lượt 9 —
# AURA đáp "chưa thể trả lời một cách đáng tin cậy".  Đúng là nó không trả lời
# được, nhưng câu đó khiến Sếp tưởng AURA dốt, trong khi sự thật là đoạn ấy đã
# rơi khỏi cửa sổ trí nhớ.  Hai chuyện ấy dẫn tới hai hành động khác nhau: một
# bên đi hỏi chỗ khác, một bên chỉ cần NHẮC LẠI một câu.
# Ân hạn CHỈ để ghi lại một lượt đã quá giờ.  Đủ cho một lần ghi đĩa, và có
# trần nên một cái sổ treo cũng không giữ Sếp lại thêm được bao lâu.
_AN_HAN_GHI_SO = 2.0

# Mất mạng KHÁC nguồn xấu.  Câu này nói đúng chuyện gì đang xảy ra và Sếp phải
# làm gì — chứ không đổ cho chất lượng nguồn khi cáp mạng mới là thứ đứt.
_MAT_MANG = (
    "📡 Máy đang KHÔNG có mạng nên em không tra được — chứ không phải nguồn "
    "kém.\nSếp kiểm lại wifi giúp em rồi hỏi lại. Những câu không cần dữ liệu "
    "mới thì em vẫn trả lời được bình thường ngay lúc này."
)

# Cờ điều phối chỉ có nghĩa bên trong lõi.  Adapter hiện tại có thể đã gỡ nó,
# nhưng ChatService là cửa ra chung nên vẫn phải tự bảo vệ trước adapter cũ,
# adapter thử nghiệm, hoặc một bộ che vô tình trả nó lại.
_WEB_SENTINEL = "[[AURA_REQUIRES_WEB]]"


def _bo_co_noi_bo(value: object) -> str:
    """Remove the web-routing sentinel from any user-visible text."""

    if not isinstance(value, str):
        return ""
    return value.replace(_WEB_SENTINEL, "").strip()

_QUEN_DAU_CHUYEN = (
    "😅 Em không trả lời được câu này — và nhiều khả năng là do em QUÊN chứ "
    "không phải không biết: cuộc trò chuyện đã dài hơn phần em còn giữ trong "
    "đầu.\nSếp nhắc lại giúp em dữ kiện đó một câu thôi, em trả lời được ngay."
)

# Tra được nguồn mà model không rút nổi đáp án ra thì đừng vứt nguồn đi — Sếp
# đọc bốn cái link đó còn nhanh hơn hỏi lại.  Nói thẳng là "em chưa dám chốt"
# chứ không giả vờ như chẳng có gì.
_CO_NGUON_MA_CHUA_DAM_CHOT = (
    "🔎 Em tra được {so} nguồn nhưng chưa dám chốt một con số từ chúng — các "
    "nguồn nói lệch nhau hoặc em đọc chưa chắc.\n"
    "Em để nguyên nguồn bên dưới, Sếp xem trực tiếp cho chắc ạ."
)

_MESSAGES = {
    ChatStatus.REJECTED: "Yêu cầu không hợp lệ nên AURA chưa xử lý.",
    ChatStatus.CANNOT_ANSWER: "AURA chưa thể trả lời câu này một cách đáng tin cậy.",
    ChatStatus.WEB_UNAVAILABLE: (
        "Câu này cần tra nguồn mới, nhưng AURA chưa lấy đủ nguồn đáng tin cậy."
    ),
    ChatStatus.BACKEND_ERROR: "AURA đang gặp lỗi ở bộ não. Vui lòng thử lại sau.",
    ChatStatus.TIMEOUT: "AURA đã dừng vì quá thời gian trả lời.",
    ChatStatus.CANCELLED: "Yêu cầu đã được hủy.",
}
def _safe_user_message(error: BaseException) -> str | None:
    """Câu an toàn do tầng dưới gửi lên, nếu có.

    Cố ý đọc bằng `getattr` chứ không import lớp lỗi của nhà cung cấp: tầng
    service phải trung lập với backend.  Chỉ nhận chuỗi khác rỗng, và vẫn để
    `_finalize` cho nó đi qua bộ che.
    """
    message = getattr(error, "user_message", None)
    if isinstance(message, str) and message.strip():
        return message
    return None


_PERSISTENCE_ERROR_MESSAGE = (
    "AURA đã tạo câu trả lời nhưng không xác nhận được việc lưu lịch sử. "
    "Vui lòng thử lại."
)


class _DeadlineExceeded(Exception):
    pass


class _WebUnavailable(Exception):
    pass


_T = TypeVar("_T")


def _consume_background_result(task: asyncio.Task[object]) -> None:
    """Retrieve a late task result so it cannot emit an unhandled warning."""

    try:
        task.result()
    except (BaseException,):
        pass


async def _before_deadline(awaitable: Awaitable[_T], deadline: float) -> _T:
    """Race one awaitable against a service-owned monotonic deadline.

    Unlike ``wait_for``, this function does not accept a value returned after
    cancellation as an on-time result.  Cancellation is cooperative: adapters
    must stop promptly when cancelled.  An adapter around a non-cancellable
    SDK belongs behind a separately terminable process boundary; arbitrary
    Python coroutines cannot be forcibly killed here.
    """

    remaining = deadline - monotonic()
    if remaining <= 0:
        close = getattr(awaitable, "close", None)
        if close is not None:
            close()
        raise _DeadlineExceeded

    task: asyncio.Task[_T] = asyncio.create_task(awaitable)
    try:
        done, _ = await asyncio.wait((task,), timeout=remaining)
    except asyncio.CancelledError:
        task.cancel()
        task.add_done_callback(_consume_background_result)
        raise
    if task not in done:
        task.cancel()
        task.add_done_callback(_consume_background_result)
        raise _DeadlineExceeded
    return task.result()


class ChatService:
    """One deterministic front door shared by every chat channel."""

    def __init__(
        self,
        *,
        model: ModelGateway,
        store: SessionStore,
        guard: ContentGuard,
        web: WebSearchGateway | None = None,
        freshness_policy: FreshnessPolicy | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self._model = model
        self._store = store
        self._guard = guard
        self._web = web if web is not None else _NullWebSearch()
        self._freshness = (
            freshness_policy
            if freshness_policy is not None
            else DeterministicFreshnessPolicy()
        )
        self._timeout_s = float(timeout_s)

    async def reply(self, request: ChatRequest) -> ChatResult:
        started = monotonic()
        deadline = started + self._timeout_s

        # Lượt đang đứng ở bước nào. Gán lại NGAY TRƯỚC mỗi chỗ chờ, để nhánh
        # `except` nào cũng đọc được bước cuối cùng thật sự chạm tới. Không có
        # nó thì `timeout` chỉ nói "quá giờ" mà không nói quá ở đâu — 12/08 mở
        # sổ ra mới thấy 90 giây bị đốt trước cả bước tra mạng.
        stage = CHAT_STAGE_INPUT

        if request.validation_errors():
            return await self._finalize(
                request,
                ChatStatus.REJECTED,
                started=started,
                deadline=deadline,
                stage=stage,
            )

        # `used_web` phải trả lời được đúng câu hỏi Sếp thật sự quan tâm: "lượt
        # này AURA có gửi câu của tôi ra ngoài không?".  Trước đây nó tính bằng
        # `bool(sources)`, nên hai trường hợp bị báo SAI: tra mạng xong mà model
        # không dùng được nguồn -> `used_web=False`; và tra mạng ra 0 nguồn ->
        # cũng `False`.  Cả hai đều đã gọi ra ngoài rồi.
        #
        # Đặt ngoài `try` để nhánh `except` nào cũng đọc được.
        da_goi_mang = False

        # Dùng lại được trong mọi nhánh `except`, kể cả khi hỏng trước lúc bộ
        # che kịp chạy — sổ phiên phải ghi được lượt hỏng, xem `_ghi_so()`.
        safe_request = request

        try:
            content_check = self._guard.check_input(request)
            if (
                not isinstance(content_check, ContentCheck)
                or content_check.validation_errors()
            ):
                raise TypeError("ContentGuard returned an invalid ContentCheck")
            if not content_check.allowed:
                return await self._finalize(
                    request,
                    ChatStatus.REJECTED,
                    text=content_check.rejection_text,
                    started=started,
                    deadline=deadline,
                    stage=stage,
                )

            # From this point on, raw request.text is out of scope. The guard's
            # transcript_text is the only text model, web, and store may see.
            safe_request = replace(request, text=content_check.transcript_text)

            stage = CHAT_STAGE_HISTORY
            raw_history = tuple(
                await _before_deadline(
                    self._store.load(
                        actor_id=safe_request.actor_id,
                        session_id=safe_request.session_id,
                    ),
                    deadline,
                )
            )
            history = tuple(self._guard.scrub_history(raw_history))
            if not all(isinstance(item, ChatMessage) for item in history):
                raise TypeError("ContentGuard returned invalid history")

            policy_requires_web = self._freshness.requires_web(safe_request)
            sources: tuple[SourceCitation, ...] = ()
            if policy_requires_web:
                da_goi_mang = True
                stage = CHAT_STAGE_WEB
                sources = await self._search_with_evidence(safe_request, deadline)
                stage = CHAT_STAGE_MODEL
                final_reply = await _before_deadline(
                    self._model.generate(
                        safe_request,
                        history=history,
                        sources=sources,
                    ),
                    deadline,
                )
            else:
                stage = CHAT_STAGE_MODEL
                initial = await _before_deadline(
                    self._model.generate(safe_request, history=history), deadline
                )
                final_reply = initial
                if initial.requires_web and (
                    la_chuyen_rieng_cua_sep(safe_request.text)
                    or la_viec_tu_lam(safe_request.text)
                ):
                    # Model đòi tra mạng cho một câu về đồ đạc/chuyện riêng của
                    # Sếp.  Đi tra là mất 55,4 giây để rồi vẫn phải nói "em
                    # quên" — Google không biết xe đạp của Sếp màu gì.  Tệ hơn
                    # nữa, tra tức là ĐẨY câu hỏi riêng tư ra máy chủ bên ngoài.
                    #
                    # Luật (`is_search_request`) đã bảo câu này không cần mạng.
                    # Lời của model là ý kiến hạng hai, không được lật luật.
                    return await self._finalize(
                        request,
                        ChatStatus.CANNOT_ANSWER,
                        text=self._loi_bo_tay(history),
                        started=started,
                        deadline=deadline,
                        stage=stage,
                    )
                if initial.requires_web:
                    da_goi_mang = True
                    stage = CHAT_STAGE_WEB
                    sources = await self._search_with_evidence(
                        safe_request,
                        deadline,
                        search_query=initial.search_query,
                    )
                    stage = CHAT_STAGE_MODEL
                    final_reply = await _before_deadline(
                        self._model.generate(
                            safe_request,
                            history=history,
                            sources=sources,
                        ),
                        deadline,
                    )

            # Model đã được đưa nguồn mà VẪN đòi tra mạng nghĩa là nó bó tay,
            # không phải nó có đáp án.  10/08 đo được: câu "Tỷ giá USD sang VND
            # hiện nay?" trả về đúng chuỗi `[[AURA_REQUIRES_WEB]]` cho Sếp đọc,
            # kèm status `ok`.  Máy móc trong bụng lọt ra mặt tiền.
            if final_reply.requires_web and sources:
                return await self._finalize(
                    request,
                    ChatStatus.CANNOT_ANSWER,
                    text=self._loi_bo_tay(history, sources),
                    used_web=da_goi_mang,
                    sources=sources,
                    started=started,
                    deadline=deadline,
                    persist=True,
                    transcript_request=safe_request,
                    stage=stage,
                )

            # Không tin adapter là lớp chặn cuối.  Cổng cloud cũ từng trả prose
            # kèm cờ, và adapter giả trong test/extension có thể làm điều tương
            # tự.  Cờ nội bộ không được đi vào bộ che, sổ phiên hay giao diện.
            text = _bo_co_noi_bo(final_reply.text)
            # Con số tiền lệch một bậc nghìn thì gắn cảnh báo, KHÔNG tự sửa —
            # xem `core/kiem_tien.py`.  Máy chắc được là "số này vô lý"; nó
            # không chắc số đúng là bao nhiêu, và bịa một con số tiền còn tệ
            # hơn nhiều so với nói "em không chắc".
            text = gan_canh_bao(text)
            if not text:
                return await self._finalize(
                    request,
                    ChatStatus.CANNOT_ANSWER,
                    text=self._loi_bo_tay(history, sources),
                    used_web=da_goi_mang,
                    sources=sources,
                    started=started,
                    deadline=deadline,
                    persist=True,
                    transcript_request=safe_request,
                    stage=stage,
                )

            return await self._finalize(
                request,
                ChatStatus.OK,
                text=text,
                used_web=da_goi_mang,
                sources=sources,
                started=started,
                deadline=deadline,
                persist=True,
                transcript_request=safe_request,
                stage=stage,
            )
        except _DeadlineExceeded:
            # Quá giờ VẪN phải vào sổ: Sếp nhìn thấy lượt đó trên màn hình, nên
            # trí nhớ của AURA cũng phải có nó.
            #
            # Nhưng chỗ ghi sổ dùng chính `deadline` — mà `deadline` vừa hết,
            # nên ghi thẳng ở đây sẽ nổ `_DeadlineExceeded` ngay trong tay
            # `except`. Cấp một khoản ÂN HẠN riêng, có trần, chỉ để ghi lại thứ
            # Sếp đã thấy.
            #
            # Không mở lại lỗi "ghi mồ côi": lượt gọi model đã bị huỷ ở trên và
            # thân `try` đã bỏ dở, nên bản nháp về muộn không có đường nào tới
            # đây.  Test timeout canh đúng chuyện đó và vẫn canh được.
            return await self._finalize(
                request,
                ChatStatus.TIMEOUT,
                used_web=da_goi_mang,
                started=started,
                deadline=deadline,
                persist=True,
                transcript_request=safe_request,
                persist_deadline=monotonic() + _AN_HAN_GHI_SO,
                stage=stage,
            )
        except _WebUnavailable:
            # Tra hụt VẪN là đã tra: câu của Sếp đi ra ngoài rồi, dù không mang
            # về được nguồn nào.  Báo `used_web=False` ở đây là giấu đúng cái
            # đáng nói nhất.
            #
            # 11/08/2026: Sếp mất mạng và AURA đáp "chưa lấy đủ nguồn đáng tin
            # cậy" — nghe như NGUỒN XẤU, trong khi sự thật là KHÔNG CÓ MẠNG.
            # Hai chuyện dẫn tới hai hành động khác nhau: một cái chờ được, một
            # cái phải đi cắm lại wifi.  Chỉ hỏi khi đã tra hụt, nên không tốn
            # gì ở đường bình thường.
            return await self._finalize(
                request,
                ChatStatus.WEB_UNAVAILABLE,
                text=None if mang_co_song() else _MAT_MANG,
                used_web=da_goi_mang,
                started=started,
                deadline=deadline,
                persist=True,
                transcript_request=safe_request,
                stage=stage,
            )
        except asyncio.CancelledError:
            return await self._finalize(
                request,
                ChatStatus.CANCELLED,
                used_web=da_goi_mang,
                started=started,
                deadline=deadline,
                stage=stage,
            )
        except Exception as error:
            # Cổng model được phép kèm MỘT câu an toàn cho người dùng (ví dụ:
            # hết hạn mức). Service không cần biết nhà cung cấp nào — chỉ nhận
            # nếu có, và vẫn cho đi qua bộ che như mọi câu chữ khác.
            return await self._finalize(
                request,
                ChatStatus.BACKEND_ERROR,
                started=started,
                deadline=deadline,
                text=_safe_user_message(error),
                used_web=da_goi_mang,
                # Cũng KHÔNG ghi sổ, cùng lý do: lỗi bộ não là máy hỏng giữa
                # chừng, không phải AURA đã trả lời Sếp một điều gì.
                stage=stage,
            )

    async def _search_with_evidence(
        self,
        request: ChatRequest,
        deadline: float,
        *,
        search_query: str = "",
    ) -> tuple[SourceCitation, ...]:
        query = (search_query or "").strip() or request.text
        try:
            found = await _before_deadline(
                self._web.search(query), deadline
            )
            sources = valid_citations(found)
        except (_DeadlineExceeded, asyncio.CancelledError):
            raise
        except Exception as error:
            raise _WebUnavailable from error
        if len(sources) < 2:
            raise _WebUnavailable
        return sources

    def _loi_bo_tay(
        self,
        history: Sequence[ChatMessage],
        sources: Sequence[SourceCitation] = (),
    ) -> str | None:
        """Bó tay vì QUÊN, hay bó tay vì KHÔNG BIẾT — nói đúng cái nào đang xảy ra.

        Không hỏi model "bạn có quên không" (nó không tự biết, và hỏi thêm một
        lượt nữa thì vừa chậm vừa không kiểm lại được).  Chỉ so hai con số đã
        có sẵn: sổ phiên giữ được bao nhiêu tin, và cổng model nhìn thấy được
        bao nhiêu.  Sổ dài hơn tầm nhìn nghĩa là CÓ đoạn đã rơi ra ngoài.

        Trả `None` khi không có gì rơi — để `_finalize` dùng câu mặc định.
        """
        # TRA ĐƯỢC NGUỒN mà vẫn bó tay thì KHÔNG phải chuyện quên.  10/08 nhìn
        # trên màn hình: hỏi "Tỷ giá USD sang VND hiện nay?", AURA mang về 4
        # nguồn Techcombank/Investing đúng ngày, rồi lại bảo "em quên đầu cuộc
        # trò chuyện".  Đổ oan cho trí nhớ, và bỏ phí 4 nguồn đang nằm ngay đó.
        if sources:
            return _CO_NGUON_MA_CHUA_DAM_CHOT.format(so=len(sources))
        tam_nhin = getattr(self._model, "history_window", 0)
        if not isinstance(tam_nhin, int) or tam_nhin <= 0:
            return None
        return _QUEN_DAU_CHUYEN if len(history) > tam_nhin else None

    async def _finalize(
        self,
        request: ChatRequest,
        status: ChatStatus,
        *,
        started: float,
        deadline: float,
        text: str | None = None,
        used_web: bool = False,
        sources: tuple[SourceCitation, ...] = (),
        persist: bool = False,
        transcript_request: ChatRequest | None = None,
        persist_deadline: float | None = None,
        stage: str = "",
    ) -> ChatResult:
        """Scrub exactly once, then optionally expose only scrubbed data to storage."""

        raw_text = _bo_co_noi_bo(text) if text is not None else ""
        if status is ChatStatus.OK and text is not None and not raw_text:
            # Một adapter đánh dấu sai `requires_web=False` nhưng chỉ trả cờ
            # không được phép biến thành kết quả OK rỗng sau khi làm sạch.
            status = ChatStatus.CANNOT_ANSWER
        raw_text = raw_text or _MESSAGES[status]
        raw_outward = OutwardContent(
            text=raw_text,
            sources=sources,
            fallback_text=_MESSAGES[ChatStatus.WEB_UNAVAILABLE],
        )
        try:
            safe_outward = self._guard.scrub_output(raw_outward)
        except Exception:
            # A broken guard must fail closed without recursively asking that
            # same broken guard to scrub an error about itself.
            safe_outward = OutwardContent(
                text="AURA không thể xuất câu trả lời an toàn."
            )
        if not isinstance(safe_outward, OutwardContent):
            safe_outward = OutwardContent(
                text="AURA không thể xuất câu trả lời an toàn."
            )
        # Chặn lần cuối SAU bộ che: đây là ranh giới chung cho mọi output, kể
        # cả một ContentGuard tuỳ biến vô tình chèn lại cờ vào prefix/fallback.
        safe_text = _bo_co_noi_bo(safe_outward.text)
        if not safe_text:
            safe_text = "AURA không thể xuất câu trả lời an toàn."

        safe_sources: tuple[SourceCitation, ...] = ()
        if len(safe_outward.sources) == len(sources):
            candidates: list[SourceCitation] = []
            for original, candidate in zip(sources, safe_outward.sources):
                if not isinstance(candidate, SourceCitation):
                    continue
                # A redacted/changed URL no longer identifies the evidence that
                # was fetched. Drop it instead of presenting a fabricated link.
                if candidate.url != original.url:
                    continue
                candidates.append(candidate)
            safe_sources = valid_citations(candidates)

        if status is ChatStatus.OK and used_web and len(safe_sources) < 2:
            status = ChatStatus.WEB_UNAVAILABLE
            # Nguồn bị bộ che loại không làm cuộc gọi mạng biến mất.  Cờ này
            # khai việc câu hỏi đã đi ra ngoài; `sources` mới khai bằng chứng
            # nào còn đủ an toàn để hiện.
            safe_sources = ()
            fallback = _bo_co_noi_bo(safe_outward.fallback_text)
            safe_text = (
                fallback
                if fallback
                else "AURA không thể xuất câu trả lời an toàn."
            )
            persist = False

        # Lượt bị TỪ CHỐI thì tuyệt đối không ghi sổ.  Cổng bí mật đã hứa với
        # Sếp: "em không nhắc lại và cũng không ghi nó vào nhật ký hội thoại".
        # Một lời hứa về bí mật thì phải chặn ở nơi thật sự ghi, không phải chỉ
        # ở nơi gọi — người sau thêm một nhánh mới là lời hứa vỡ.
        if status is ChatStatus.REJECTED:
            persist = False

        latency_ms = max(0, round((monotonic() - started) * 1000))
        result = ChatResult(
            request_id=request.request_id,
            session_id=request.session_id,
            status=status,
            text=safe_text,
            used_web=used_web,
            sources=safe_sources,
            latency_ms=latency_ms,
            stage=stage,
        )
        if persist:
            if transcript_request is None:
                raise ValueError("transcript_request is required when persist=True")
            try:
                # Storage sees neither raw model output nor raw input. A model
                # that returns after timeout never reaches this method at all.
                await _before_deadline(
                    self._store.append_exchange(
                        request=transcript_request,
                        result=result,
                    ),
                    deadline if persist_deadline is None else persist_deadline,
                )
            except (_DeadlineExceeded, asyncio.CancelledError):
                # Propagate so reply() returns structured TIMEOUT/CANCELLED.
                # An adapter must make append cancellable and atomic; this layer
                # cannot claim rollback of a write that already partially ran.
                raise
            except Exception:
                # Do not report OK when durability is unknown. The first scrub
                # happened before storage (so the store never saw raw output);
                # this newly determined final status requires its own scrub.
                try:
                    failure_outward = self._guard.scrub_output(
                        OutwardContent(text=_PERSISTENCE_ERROR_MESSAGE)
                    )
                except Exception:
                    failure_outward = OutwardContent(
                        text="AURA không thể xuất câu trả lời an toàn."
                    )
                failure_text = _bo_co_noi_bo(
                    failure_outward.text
                    if isinstance(failure_outward, OutwardContent)
                    else ""
                )
                failure_text = failure_text or "AURA không thể xuất câu trả lời an toàn."
                # Câu trả lời đã dựng xong, chỗ gãy là lúc GHI SỔ. Ghi đúng bước
                # đó chứ không giữ bước cũ — nếu không, sổ sẽ đổ lỗi cho model
                # trong khi model đã làm xong việc của nó.
                return ChatResult(
                    request_id=request.request_id,
                    session_id=request.session_id,
                    status=ChatStatus.BACKEND_ERROR,
                    text=failure_text,
                    used_web=used_web,
                    sources=(),
                    stage=CHAT_STAGE_PERSIST,
                    latency_ms=max(
                        0, round((monotonic() - started) * 1000)
                    ),
                )
        return result
