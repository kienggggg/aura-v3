# -*- coding: utf-8 -*-
"""Bộ che tha đường dẫn bài báo trong URL nguồn — `CHOT:url-nguon-slug` (13/09/2026).

Lượt chat thật đầu tiên sau khi bỏ dòng URL: "giá vàng SJC hôm nay" trả lời đúng
146 triệu, trích [4] — danh sách dưới câu trả lời chỉ có 3 nguồn. `core/redact.py`
coi mọi chuỗi `[A-Za-z0-9_-]{32,}` là khoá, nên đường dẫn bài báo tiếng Việt bị
che, URL đổi, nguồn rơi: 14/36 nguồn đông băng, 2/9 câu xuống `web_unavailable`.

Bộ che chỉ được trả HAI thứ cho URL nguồn: URL gốc nguyên vẹn, hoặc bản che như
cũ. 17 ca đối chứng đều ĐANG bị che trước khi sửa (kiểm 13/09) và phải VẪN bị che.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from core.chat_contract import (
    Channel,
    ChatRequest,
    ChatStatus,
    OutwardContent,
    SourceCitation,
)
from core.chat_service import ChatService, ModelReply
from core.paths import PROJECT_ROOT
from core.secret_guard import SecretContentGuard, scrub_for_log

# Chép TAY từ `CHOT:url-nguon-slug` — toàn bộ ô, so bằng `==`.
DAC_TA = {
    "nguồn bị bỏ, 36 nguồn đông băng": "0",
    "câu còn dưới 2 nguồn, 9 câu": "0",
    "ca đối chứng khoá trong URL": "17/17 vẫn bị che",
    "URL ra khác cả gốc lẫn bản che cũ": "0",
    "test cũ của bộ che": "xanh hết, không sửa bài nào",
}

# 14 URL THẬT từng rơi trên 36 nguồn đông băng 13/09 — lấy bằng máy từ tệp nguồn,
# không gõ tay. Nguồn công khai, không chứa gì của Sếp.
TUNG_ROI = [
    "https://baohatinh.vn/tv/gia-vang-hom-nay-13-9-2026-sjc-doji-pnj-btmc-btmh-phu-quy-va-vang-nhan-52959.html",
    "https://thuonghieucongluan.com.vn/gia-vang-hom-nay-13-9-vang-mieng-sjc-bat-tang-len-146-trieu-dong-luong-a334000.html",
    "https://doanhnghiephoinhap.vn/gia-vang-hom-nay-1392026-vang-trong-nuoc-khep-tuan-o-vung-gia-cao-148668.html",
    "https://doanhnghiephoinhap.vn/gia-xang-dau-hom-nay-1392026-dau-the-gioi-tuan-qua-tang-hon-8-vuot-100-usdthung-148565.html",
    "https://vov.vn/thi-truong/gia-xang-dau-hom-nay-139-gia-dau-the-gioi-giam-post1331974.vov",
    "https://vov.vn/xa-hoi/thoi-tiet-hom-nay-139-bac-bo-ngay-nang-trung-bo-va-nam-bo-mua-dong-post1332023.vov",
    "https://techmaster.vn/posts/36599/cau-hoi-phong-van-co-ban-ban-co-the-giai-thich-closures-la-gi-khong",
    "https://nhandan.vn/ong-donald-trump-chinh-thuc-tro-thanh-tong-thong-thu-47-cua-nuoc-my-post857026.html",
    "https://vov.vn/the-gioi/tong-thong-donald-trump-thoi-ky-hoang-kim-cua-nuoc-my-da-bat-dau-post1150095.vov",
    "https://cafef.vn/lai-suat-tiet-kiem-hom-nay-ngay-9-9-tai-agribank-bidv-vietcombank-sacombank-acb-vpbank-mb-188260909104210759.chn",
    "https://nhandan.vn/dan-so-trung-binh-cua-viet-nam-nam-2025-dat-1023-trieu-nguoi-post934760.html",
    "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/chinh-sach-moi/102597/dan-so-trung-binh-cua-viet-nam-nam-2025",
    "https://thanhnien.vn/dan-so-viet-nam-1023-trieu-nguoi-dung-thu-16-the-gioi-185260122194541201.htm",
    "https://baochinhphu.vn/dan-so-viet-nam-dung-3-dong-nam-a-thu-16-the-gioi-102260122233119324.htm",
]

# Khoá giả dựng lúc chạy: viết liền trong tệp thì máy soát khoá trước commit bắt.
_G = "giakhoa" * 4
_SLUG = "gia-vang-hom-nay-13-9-vang-mieng-sjc-bat-tang-len-146-trieu-dong-luong-a334000"
_HEX40 = "3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a"
DOI_CHUNG = {
    "sk- trong đường dẫn": "https://vi.du/tai-lieu/sk-" + _G,
    # Hình SLUG hợp lệ — chỉ luật cụ thể soi TRONG slug cứu được ca này.
    "sk- nằm GIỮA một slug": "https://vi.du/huong-dan-dung-sk-" + _G + "-cho-nguoi-moi.html",
    "ghp_ trong đường dẫn": "https://vi.du/repo/ghp_" + "GIAKHOA" * 4,
    "AIza trong ?key=": "https://vi.du/ban-do?key=AIza" + "GIAKHOA" * 4,
    "?access_token=": "https://vi.du/api/du-lieu?access_token=" + _G,
    "?token= 32 ký tự": "https://vi.du/tai-ve?token=" + "a1b2c3d4" * 4,
    "hex 40 ký tự không gạch": "https://vi.du/chia-se/" + _HEX40,
    "UUID": "https://vi.du/dat-lai/550e8400-e29b-41d4-a716-446655440000",
    # Hai phần toàn chữ (dead, beef): ngưỡng "≥ 3 phần" là thứ cứu ca này.
    "UUID có đúng 2 phần toàn chữ": "https://vi.du/dat-lai/1f2e3d4c-dead-beef-4a5b-6c7d8e9f0a1b",
    "chuỗi ngẫu nhiên nối gạch": "https://vi.du/ma/k3j4-h5g6-f7d8-s9a0-p1o2-i3u4-y5t6",
    "email trong đường dẫn": "https://vi.du/lien-he/ten.nguoi.that@gmail.com",
    # Hình SLUG hợp lệ — luật số điện thoại soi trong slug.
    "số điện thoại giữa slug": "https://vi.du/ban-nha-lien-he-0912345678-chinh-chu-gia-re.html",
    "slug hợp lệ + hex 40 ký tự bên cạnh": f"https://vi.du/{_SLUG}/{_HEX40}",
    "chữ HOA nối gạch": "https://vi.du/ma/ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ12",
    "tên:mật-khẩu@ trong tên miền": f"https://sep:matkhau123@vi.du/{_SLUG}.html",
    # Hình SLUG nhưng nằm ở `?…`: chỉ ĐƯỜNG DẪN được tha. Đường dẫn PHẢI có một
    # slug hợp lệ — bản đầu là `/chia-se?ma=…`, không slug nên bị chặn sớm, và
    # gieo bỏ bước soi phần ngoài slug thì ca này vẫn xanh (13/09).
    "chuỗi dạng slug nằm trong ?…": f"https://vi.du/{_SLUG}?ma=abcd-efgh-ijkl-mnop-qrst-uvwx-yzab",
    # Ca 17, thêm lúc bắt đầu viết mã: đuôi tệp dài tuỳ ý là một lối lọt.
    "slug có đuôi tệp là hex 40 ký tự": f"https://vi.du/gia-vang-hom-nay-13-9.{_HEX40}",
}
# Không phải khoá, nhưng lạ: phải rơi về bản che cũ, không được che một nửa.
URL_LA = {
    "tên miền IPv6 hỏng": f"http://[giakhoa/{_SLUG}",
    # Cùng bệnh với ca `?…` ở trên: bản đầu `/tin#…` không có slug trong đường dẫn.
    "slug nằm ở #…": f"https://vi.du/{_SLUG}#{_SLUG}",
    # Mã hoá % CHỮ THƯỜNG: bản `%C3%B4` chữ hoa đã bị luật "chữ thường" chặn, nên
    # gieo cho slug nhận `%` thì vẫn xanh — cửa mù (13/09).
    "slug mã hoá %": "https://vi.du/gia-vang-h%c3%b4m-nay-13-9-vang-mieng-sjc-bat-tang-len-146",
}


def _khoi() -> str:
    m = re.search(
        r"<!-- CHOT:url-nguon-slug -->(.*?)<!-- /CHOT:url-nguon-slug -->",
        (PROJECT_ROOT / "KY_LUAT_THUC_THI.md").read_text(encoding="utf-8"), re.S)
    assert m, "mất khối đặc tả CHOT:url-nguon-slug"
    return m.group(1)


def _url_ra(url: str) -> str:
    """Đi qua ĐÚNG cửa `chat_service` dùng: `scrub_output` trên cả gói."""
    nguon = SourceCitation(title="t", url=url, retrieved_at="2026-09-13T05:00:00+00:00",
                           supports="s")
    return SecretContentGuard().scrub_output(
        OutwardContent(text="x", sources=(nguon,))).sources[0].url


def test_NAM_NGUONG_dung_nhu_luc_dang_ky():
    hang = [h for h in re.findall(r"^\| (.+?) \| (.+?) \|$", _khoi(), re.M)
            if h != ("đơn", "ngưỡng")]
    assert len(hang) == len(dict(hang)), "hai hàng trùng tên — hàng sau đè ngưỡng hàng trước"
    assert dict(hang) == DAC_TA
    assert f"{len(DOI_CHUNG)}/{len(DOI_CHUNG)} vẫn bị che" == DAC_TA["ca đối chứng khoá trong URL"]


@pytest.mark.parametrize("url", TUNG_ROI)
def test_URL_BAI_BAO_tung_roi_nay_GIU_NGUYEN(url):
    assert scrub_for_log(url) != url, "ca này không còn bị luật chung che — nó thôi làm chứng"
    assert _url_ra(url) == url


@pytest.mark.parametrize("ten", DOI_CHUNG)
def test_CA_DOI_CHUNG_khoa_trong_URL_VAN_BI_CHE_nhu_cu(ten):
    url = DOI_CHUNG[ten]
    assert scrub_for_log(url) != url, f"{ten}: bộ che cũ không che — không đối chứng cho gì"
    assert _url_ra(url) == scrub_for_log(url), f"{ten}: lọt qua bộ che"


def test_KHONG_BAO_GIO_CHE_MOT_NUA():
    for url in [*TUNG_ROI, *DOI_CHUNG.values(), *URL_LA.values()]:
        assert _url_ra(url) in (url, scrub_for_log(url)), url
    for ten, url in URL_LA.items():
        assert scrub_for_log(url) != url, f"{ten}: bộ che cũ không che — không làm chứng"
        assert _url_ra(url) == scrub_for_log(url), ten


def test_LUOT_GIA_VANG_hien_DU_4_nguon_model_da_thay(monkeypatch):
    """Đúng ca bắt được 13/09: model trích [4], danh sách chỉ có 3."""
    monkeypatch.setattr("core.chat_service.mang_co_song", lambda *a, **k: True)
    urls = ["https://sjc.com.vn/", "https://baolamdong.vn/gia-vang",
            "https://www.24h.com.vn/gia-vang-hom-nay-c425.html", TUNG_ROI[1]]
    bay_gio = datetime.now(timezone.utc).isoformat()
    nguon = tuple(SourceCitation(title=f"Nguồn {i}", url=u, retrieved_at=bay_gio,
                                 supports=f"Dữ kiện {i}") for i, u in enumerate(urls, 1))

    class _Web:
        async def search(self, query):
            return nguon

    class _Model:
        async def generate(self, request, *, history, sources=()):
            return ModelReply("Giá bán ra 146 triệu đồng/lượng [4].")

    class _So:
        async def load(self, *, actor_id, session_id):
            return ()

        async def append_exchange(self, *, request, result):
            pass

    kq = asyncio.run(ChatService(model=_Model(), store=_So(), guard=SecretContentGuard(),
                                 web=_Web()).reply(
        ChatRequest(request_id=str(uuid4()), session_id=str(uuid4()),
                    actor_id="owner", channel=Channel.TEST, text="giá vàng SJC hôm nay")))
    assert kq.status is ChatStatus.OK
    assert [s.url for s in kq.sources] == urls, "danh sách dưới câu trả lời khác thứ model đã thấy"
