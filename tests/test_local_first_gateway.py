"""Cổng local-first — trò làm trước, mượn thầy khi bí.

Khôi phục nguyên tắc gốc trong `brain_router.py`: System 1 = Ollama local,
System 2 = cloud "thầy".  Chat v1 từng đảo thành cloud-only mà không ai nói ra.

Các test giữ hai thứ: bậc thang đúng chiều, và KHÔNG mọc thêm tầng router nào.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from core.chat_contract import ChatRequest, SourceCitation
from core.chat_runtime import ModelGatewayError, ModelGatewayTimeout
from core.chat_service import ChatMessage, ModelReply
from core.local_first_gateway import (
    LocalFirstGateway, OllamaConfig, OllamaGateway, looks_weak,
)


def _request(text: str = "chào AURA") -> ChatRequest:
    return ChatRequest(
        request_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        actor_id="owner:web", channel="web", text=text,
    )


class _Gateway:
    def __init__(self, text="", raises=None, requires_web=False):
        self._text = text
        self._raises = raises
        self._requires_web = requires_web
        self.calls = 0

    async def generate(self, request, *, history=(), sources=()):
        self.calls += 1
        if self._raises:
            raise self._raises
        return ModelReply(text=self._text, requires_web=self._requires_web)


def _run(gateway, text="chào AURA"):
    return asyncio.run(gateway.generate(_request(text)))


# ------------------------------------------------------------ bậc thang
def test_local_tra_loi_tot_thi_KHONG_goi_cloud():
    local = _Gateway(text="Chào Sếp, em nghe đây ạ. Hôm nay cần gì em làm luôn.")
    cloud = _Gateway(text="(thầy)")
    gate = LocalFirstGateway(local=local, cloud=cloud)
    assert "Chào Sếp" in _run(gate).text
    assert cloud.calls == 0, "trò làm được thì không được gọi thầy"
    assert gate.last_escalation.used_cloud is False


def test_local_guc_thi_muon_thay():
    local = _Gateway(raises=ModelGatewayError("ollama chết"))
    cloud = _Gateway(text="Thầy trả lời thay.")
    gate = LocalFirstGateway(local=local, cloud=cloud)
    assert _run(gate).text == "Thầy trả lời thay."
    assert cloud.calls == 1
    assert gate.last_escalation.used_cloud is True
    assert gate.last_escalation.reason, "phải ghi VÌ SAO mượn thầy"


def test_local_tra_YEU_thi_muon_thay():
    local = _Gateway(text="Tôi không biết.")
    cloud = _Gateway(text="Thầy giải thích cặn kẽ hơn nhiều cho Sếp đây ạ.")
    gate = LocalFirstGateway(local=local, cloud=cloud)
    assert "Thầy giải thích" in _run(gate).text
    assert gate.last_escalation.reason == "đáp án local yếu"


def test_khong_co_thay_thi_giu_nguyen_loi_goc():
    local = _Gateway(raises=ModelGatewayTimeout("local quá giờ"))
    gate = LocalFirstGateway(local=local, cloud=None)
    with pytest.raises(ModelGatewayTimeout):
        _run(gate)


def test_thay_ban_thi_van_tra_bai_cua_tro():
    """Câu yếu còn hơn im lặng — đúng luật đã chốt ở phiên chat."""
    local = _Gateway(text="Ừm.")
    cloud = _Gateway(raises=ModelGatewayError("hết hạn mức"))
    gate = LocalFirstGateway(local=local, cloud=cloud)
    assert _run(gate).text == "Ừm."
    assert gate.last_escalation.used_cloud is False


def test_can_tra_mang_thi_de_ChatService_lo():
    local = _Gateway(text="[[AURA_REQUIRES_WEB]]", requires_web=True)
    cloud = _Gateway(text="(thầy)")
    gate = LocalFirstGateway(local=local, cloud=cloud)
    assert _run(gate).requires_web is True
    assert cloud.calls == 0, "tra mạng là việc của ChatService, không phải của thầy"


def test_tat_co_che_muon_thay():
    local = _Gateway(text="Ừm.")
    cloud = _Gateway(text="(thầy)")
    gate = LocalFirstGateway(local=local, cloud=cloud, escalate_when_weak=False)
    assert _run(gate).text == "Ừm."
    assert cloud.calls == 0


# ------------------------------------------------------------ nhận biết yếu
@pytest.mark.parametrize("text", [
    "", "   ", "Ừm.", "ok", "không", "Tôi không biết.",
    "Xin lỗi, tôi không có thông tin về việc đó.",
    "I don't know", "As an AI language model, I cannot help with that",
])
def test_nhan_ra_dap_an_yeu(text):
    assert looks_weak(text) is True


@pytest.mark.parametrize("text", [
    "Chào Sếp, hôm nay em thấy máy còn 3,4 GB RAM trống ạ.",
    "2 cộng 2 bằng 4, và đây là cách kiểm lại bằng máy tính.",
    # NGẮN KHÔNG PHẢI YẾU: bản đầu đẩy mấy câu này lên thầy, tốn 13,4 giây
    # cho việc trò đã làm xong trong 5 giây.
    "2 cộng 2 bằng 4.",
    "Là 42.",
    "Chào buổi sáng! Có gì cần hỗ trợ không?",
])
def test_khong_cho_la_yeu_khi_da_tra_loi_tu_te(text):
    assert looks_weak(text) is False


# ------------------------------------------------------------ cấu hình đo được
def test_mac_dinh_bam_dung_so_da_do():
    """Ba tham số này là kết quả đo 10/08, không phải sở thích."""
    config = OllamaConfig()
    assert config.think is False, "bật nghĩ thầm: 339 giây thay vì 24,8"
    assert config.keep_alive != "0", "không giữ RAM: 29 giây thay vì 5-9"
    assert config.num_ctx <= 8192, "ngữ cảnh dài ăn RAM y như tham số"


@pytest.mark.parametrize("bad", [
    {"model": "   "}, {"num_ctx": 128}, {"timeout_s": 0},
])
def test_cau_hinh_sai_bi_tu_choi_som(bad):
    with pytest.raises(ValueError):
        OllamaConfig(**bad)


def test_khong_moc_them_tang_router():
    """Ba tầng router chồng nhau là nơi con số 512 nằm im mấy tháng."""
    import inspect

    from core import local_first_gateway

    source = inspect.getsource(local_first_gateway)
    for banned in ("BrainRouter", "litellm", "Router(", "route_intent"):
        assert banned not in source, f"đang dựng lại mê cung cũ: {banned}"


def test_cong_local_gui_dung_ba_tham_so_len_ollama():
    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["url"] = url
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "Chào Sếp, em nghe rõ ạ."}}

            return _Response()

    gate = OllamaGateway(OllamaConfig(model="qwen3.5:4b"), client=_Client())
    reply = asyncio.run(gate.generate(_request()))
    assert reply.text.startswith("Chào Sếp")
    assert sent["json"]["think"] is False
    assert sent["json"]["keep_alive"] == "5m"
    assert sent["json"]["options"]["num_ctx"] == 4096
    assert sent["url"].endswith("/api/chat")


def test_cua_so_tri_nho_du_dai_cho_mot_mach_chuyen():
    """12 tin = 6 lượt, quá ngắn cho một mạch chuyện bình thường.

    Đo 10/08: đặt dữ kiện ở lượt 1, lấp đầy 7 lượt, hỏi lại ở lượt 9.
        12 tin -> quên sạch, mất 54,5 giây đi TRA MẠNG tìm màu xe đạp của Sếp
        24 tin -> "Màu cam." trong 2,1 giây
    Nhanh hơn CHÍNH VÌ không phải tra mạng cho thứ nằm sẵn trong cuộc trò chuyện.
    """
    config = OllamaConfig()
    assert config.max_history_messages >= 24, (
        "hạ xuống dưới 24 là AURA quên giữa mạch chuyện — đã đo, đừng đoán"
    )
    # Nhưng đừng nới vô hạn: lịch sử dài ăn `num_ctx`, mà `num_ctx` ăn RAM.
    assert config.max_history_messages * 200 < config.num_ctx * 4


def test_cong_local_gui_DU_lich_su_len_ollama():
    """Nới `max_history_messages` mà quên cắm vào payload thì nới cho ai xem."""
    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "rõ ạ"}}

            return _Response()

    lich_su = [
        ChatMessage(role="user" if i % 2 == 0 else "aura", content=f"tin {i}")
        for i in range(40)
    ]
    gate = OllamaGateway(OllamaConfig(), client=_Client())
    asyncio.run(gate.generate(_request(), history=lich_su))
    # 1 lời dặn hệ thống + 24 tin cũ + 1 câu đang hỏi
    assert len(sent["json"]["messages"]) == 26
    assert sent["json"]["messages"][1]["content"] == "tin 16", "phải giữ 24 tin CUỐI"


def test_cau_cam_nhac_lai_luat_luon_o_CUOI_CUNG():
    """Kể cả đường CÓ NGUỒN — đó là chỗ nó rò trở lại.

    10/08: câu cấm nằm cuối `system_prompt` và tôi tưởng thế là xong. Đường có
    nguồn nối thêm luật trích dẫn SAU nó, nên nó hết ở cuối, và mảnh luật rò ra
    ngay: "...đây là sự kiện bên ngoài thay đổi theo thời gian" trong câu trả
    lời về giá xăng.
    """
    from core.local_first_gateway import _CAM_NHAC_LAI_LUAT

    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "rõ ạ"}}

            return _Response()

    nguon = (SourceCitation(
        title="Giá vàng", url="https://vi.du/gia",
        retrieved_at="2026-08-10T12:00:00+00:00", supports="140 triệu",
    ),)
    gate = OllamaGateway(OllamaConfig(), client=_Client())

    for bo_nguon in ((), nguon):
        asyncio.run(gate.generate(_request("giá vàng hôm nay"), sources=bo_nguon))
        he_thong = sent["json"]["messages"][0]["content"]
        assert he_thong.rstrip().endswith(_CAM_NHAC_LAI_LUAT.rstrip()), (
            "câu cấm nhắc lại luật không còn nằm cuối "
            + ("(đường CÓ NGUỒN)" if bo_nguon else "(đường thường)")
        )


def test_luot_CO_NGUON_thi_cat_bot_lich_su():
    """10/08 chat thật: "Giá vàng hôm nay?" ở lượt 9 (sổ 16 tin) QUÁ 90 GIÂY.

    Cùng câu đó ở phiên mới chỉ mất 33 giây.  Khi đã có nguồn thì đáp án phải
    rút từ nguồn; 24 tin cũ chỉ làm dày lời nhắc, mà máy này sinh chữ ở
    5,9 tok/s nên mỗi tin thừa là thời gian Sếp ngồi chờ.
    """
    sent = {}

    class _Client:
        async def post(self, url, json=None):
            sent["json"] = json

            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "Giá vàng khoảng X [1]."}}

            return _Response()

    lich_su = [
        ChatMessage(role="user" if i % 2 == 0 else "aura", content=f"tin {i}")
        for i in range(40)
    ]
    nguon = (SourceCitation(
        title="Giá vàng", url="https://vi.du/gia-vang",
        retrieved_at="2026-08-10T12:00:00+00:00", supports="X đồng",
    ),)

    gate = OllamaGateway(OllamaConfig(), client=_Client())
    asyncio.run(gate.generate(_request("giá vàng hôm nay"),
                              history=lich_su, sources=nguon))
    co_nguon = len(sent["json"]["messages"])

    asyncio.run(gate.generate(_request("giá vàng hôm nay"), history=lich_su))
    khong_nguon = len(sent["json"]["messages"])

    assert co_nguon == 1 + 6 + 1, "lượt có nguồn phải chỉ giữ 6 tin lịch sử"
    assert khong_nguon == 1 + 24 + 1
    assert co_nguon < khong_nguon


def test_loi_dan_khoanh_HEP_cua_tra_mang():
    """10/08: "Chào AURA, hôm nay em làm được gì cho Sếp?" bị đẩy đi tra mạng.

    AURA tra Google chữ "Aura", vớ phải một app App Store không liên quan rồi
    báo cáo về app đó — 51 giây cho một câu tự giới thiệu.  Lời dặn cũ chỉ nói
    "cần dữ liệu mới thì tra", nên chữ "hôm nay" đủ để mở cửa.
    """
    prompt = OllamaConfig().system_prompt
    # ĐẢO CHIỀU 11/08/2026. Bản trước đòi lời dặn PHẢI liệt kê khi nào không
    # tra mạng. Chính danh sách đó làm hỏng việc: Sếp gõ "AI là gì", model khớp
    # chữ "AI" vào mục "câu hỏi về chính bạn" rồi chép nguyên danh sách ra làm
    # câu trả lời — 3/3 lần.
    #
    # Luật tra mạng KHÔNG thuộc về lời dặn: `DeterministicFreshnessPolicy` và
    # `web_search.is_search_request` quyết xong trước khi model được hỏi. Đưa
    # nó vào prompt vừa thừa vừa cho model một đoạn văn để đọc thuộc.
    for cam in ("TỰ TRẢ LỜI", "chính bạn", "giá cả", "thời tiết", "tin tức",
                "SỰ KIỆN BÊN NGOÀI"):
        assert cam not in prompt, f"luật định tuyến quay lại lời dặn: {cam!r}"
    assert "TRẢ LỜI ĐÚNG CÂU SẾP HỎI" in prompt
    assert "đừng nói về bản thân bạn" in prompt


def test_loi_dan_co_luat_DINH_DANG():
    """Sếp xin "một khối mã + danh sách 2 ý", AURA trả một đoạn văn xuôi.

    Bỏ qua 2 trong 3 yêu cầu.  Model 4B không tự suy ra luật định dạng nên phải
    dặn thẳng — đây là chỗ duy nhất dặn được mà không tốn thêm lượt gọi nào.
    """
    prompt = OllamaConfig().system_prompt
    assert "ĐỊNH DẠNG" in prompt
    assert "Mã nguồn LUÔN đặt trong khối" in prompt
    assert "mỗi ý MỘT DÒNG" in prompt
    assert "đúng thứ tự đã nêu" in prompt


def _gate_tra(noi_dung: str) -> ModelReply:
    class _Client:
        async def post(self, url, json=None):
            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": noi_dung}}

            return _Response()

    return asyncio.run(OllamaGateway(OllamaConfig(), client=_Client()).generate(
        _request()
    ))


@pytest.mark.parametrize("noi_dung", [
    "Hôm nay là ngày 10 tháng 8 năm 2026.\n[[AURA_REQUIRES_WEB]]",
    "[[AURA_REQUIRES_WEB]]\nCòn 144 ngày nữa đến 01/01/2027.",
    "Giá vàng hôm nay tại SJC là 139.700 đồng. [[AURA_REQUIRES_WEB]]",
])
def test_co_noi_bo_DAN_THEM_vao_cau_tra_loi_thi_phai_go_ra(noi_dung):
    """10/08/2026, đo `qwen3:1.7b`: gần như lượt nào nó cũng dán cờ vào cuối một
    câu trả lời bình thường, và cả cụm đi thẳng ra mặt Sếp.

    Bản chặn cũ chỉ bắt khi TOÀN BỘ câu trả lời đúng bằng chuỗi cờ.
    """
    reply = _gate_tra(noi_dung)
    assert "AURA_REQUIRES_WEB" not in reply.text
    assert reply.requires_web is False, "còn chữ tử tế thì đó là câu trả lời"
    assert reply.text.strip()


@pytest.mark.parametrize("noi_dung", [
    "[[AURA_REQUIRES_WEB]]",
    "  [[AURA_REQUIRES_WEB]]  ",
    "[[AURA_REQUIRES_WEB]] ok",       # còn lại quá ngắn để là câu trả lời
])
def test_chi_co_moi_cai_co_thi_dung_la_doi_tra_mang(noi_dung):
    reply = _gate_tra(noi_dung)
    assert reply.requires_web is True


def test_local_tra_rong_bi_coi_la_guc():
    """Rỗng = trò bí, không phải 'đã trả lời'. Đúng bài học con số 512."""
    class _Client:
        async def post(self, url, json=None):
            class _Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"message": {"content": "   ", "thinking": "nghĩ rất nhiều"}}

            return _Response()

    gate = OllamaGateway(OllamaConfig(), client=_Client())
    with pytest.raises(ModelGatewayError):
        asyncio.run(gate.generate(_request()))
