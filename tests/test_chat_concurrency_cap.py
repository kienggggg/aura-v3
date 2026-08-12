"""Trần đồng thời — quá tải thì TỪ CHỐI SỚM, không xếp hàng vô hạn.

Codex yêu cầu ở lượt 009: timeout liên tiếp có thể đẻ việc nghẽn vô hạn và đốt
RAM/hạn mức.  Tôi cắm ở commit d3a4ce8, rồi một bản viết lại giữa chừng gỡ mất.
Đây là lần cắm lại, kèm test để lần sau ai gỡ thì bộ test kêu.

Đặt ở LÕI chứ không ở cửa web: Telegram sau này dùng chung một lõi, nên trần phải
nằm nơi mọi kênh đều đi qua.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, ChatResult, ChatStatus
from interface.chat_adapters import BoundedChatService


def _request() -> ChatRequest:
    return ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text="chào AURA",
    )


class _Slow:
    """Lõi giả: giữ chỗ cho tới khi được thả."""

    def __init__(self) -> None:
        self.gate = asyncio.Event()
        self.started = 0

    async def reply(self, request):
        self.started += 1
        await self.gate.wait()
        return ChatResult(
            request_id=request.request_id, session_id=request.session_id,
            status=ChatStatus.OK, text="xong", used_web=False,
            sources=(), latency_ms=1,
        )


def test_qua_tran_thi_tu_choi_som_chu_khong_cho_mai():
    async def go():
        inner = _Slow()
        service = BoundedChatService(inner, limit=2)
        held = [asyncio.create_task(service.reply(_request())) for _ in range(2)]
        await asyncio.sleep(0)          # cho hai lượt kia chiếm chỗ

        # Lượt thứ ba phải trả về NGAY, không treo.
        third = await asyncio.wait_for(service.reply(_request()), timeout=2.0)
        assert third.status == ChatStatus.BACKEND_ERROR
        assert third.text.strip()
        assert inner.started == 2, "lượt bị từ chối không được chạm vào lõi"

        inner.gate.set()
        done = await asyncio.gather(*held)
        assert all(r.status == ChatStatus.OK for r in done)

    asyncio.run(go())


def test_tha_cho_roi_thi_nhan_lai_duoc():
    async def go():
        inner = _Slow()
        service = BoundedChatService(inner, limit=1)
        first = asyncio.create_task(service.reply(_request()))
        await asyncio.sleep(0)
        assert (await service.reply(_request())).status == ChatStatus.BACKEND_ERROR

        inner.gate.set()
        await first
        assert service.active == 0, "chỗ phải được trả lại sau khi xong"
        assert (await service.reply(_request())).status == ChatStatus.OK

    asyncio.run(go())


def test_loi_trong_loi_van_tra_lai_cho():
    """Lõi ném lỗi mà không trả chỗ thì vài lần là kẹt cứng vĩnh viễn."""
    class _No:
        async def reply(self, request):
            raise RuntimeError("hỏng")

    async def go():
        service = BoundedChatService(_No(), limit=1)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await service.reply(_request())
        assert service.active == 0

    asyncio.run(go())


def test_ket_qua_tu_choi_van_dung_hop_dong():
    async def go():
        inner = _Slow()
        service = BoundedChatService(inner, limit=1)
        held = asyncio.create_task(service.reply(_request()))
        await asyncio.sleep(0)
        request = _request()
        busy = await service.reply(request)
        assert busy.validation_errors() == (), busy.validation_errors()
        assert busy.request_id == request.request_id
        assert busy.session_id == request.session_id
        inner.gate.set()
        await held

    asyncio.run(go())


@pytest.mark.parametrize("bad", [0, -1, True, "4", None])
def test_tran_phai_la_so_nguyen_duong(bad):
    class _Any:
        async def reply(self, request):
            return None

    with pytest.raises(ValueError):
        BoundedChatService(_Any(), bad)


def test_runtime_that_su_boc_loi_bang_tran(tmp_path):
    """Cắm trần vào cấu hình mà quên bọc thì trần vô nghĩa."""
    from interface.chat_adapters import ChatRuntimeConfig, build_chat_runtime

    runtime = build_chat_runtime(
        config=ChatRuntimeConfig(transcript_root=tmp_path, max_concurrent_replies=3)
    )
    assert isinstance(runtime.service, BoundedChatService)
    assert runtime.service._limit == 3
