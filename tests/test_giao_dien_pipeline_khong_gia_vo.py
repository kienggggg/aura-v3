# -*- coding: utf-8 -*-
"""Giao diện pipeline không được GIẢ VỜ chạy.

Bản trước 05/09/2026 của `kichHoatPipeline` chạy một hoạt ảnh `setTimeout` 450ms
mỗi bước **TRƯỚC** khi gọi `/api/pipeline/run`::

    for (let i = 0; i < steps.length; i++) {
      el.textContent = 'ĐANG CHẠY...';
      await new Promise(r => setTimeout(r, 450));
      el.textContent = 'HOÀN TẤT ✓';
    }
    try { const resp = await fetch('/api/pipeline/run', ...) } catch (_) {}

Nên cả 5 bước báo **HOÀN TẤT ✓ sau 2,25 giây** — trước lúc dây chuyền bắt đầu —
rồi đứng im 166 giây. Hỏng thì `catch (_) {}` nuốt, màn hình không đổi gì.

Đó không phải màn hình trắng. Nó là màn hình NÓI DỐI, và tệ hơn màn hình trắng.
Cùng bệnh đã ghi trong `CLAUDE.md` ngày 24/08: *"panel Agent trả lời bằng chuỗi
cứng + setTimeout 350ms giả vờ suy nghĩ, 0 request"*.

Đo trên màn hình thật sau khi vá (05/09/2026, máy chủ ở cổng 8891)::

    t=8s    zeta HOÀN TẤT ✓ · aura ĐANG CHẠY 2.4s · alpha/omega/gamma ĐANG ĐỢI
    t=18s   zeta HOÀN TẤT ✓ · aura ĐANG CHẠY 8.4s
    lượt gãy: zeta KHÔNG CHẠY ĐƯỢC · bốn bước sau CHƯA CHẠY, kèm lý do
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import PROJECT_ROOT  # noqa: E402

JS = PROJECT_ROOT / "interface" / "web" / "noi_bo.js"


def _bo_chu_thich_js(chu: str) -> str:
    """Bỏ chú thích JS, giữ phần mã.

    CẦN THẬT. Bài `test_KHONG_con_hoat_anh_gia` đỏ ngay lần chạy đầu vì chú
    thích trong hàm nhắc lại chữ `setTimeout` để GIẢI THÍCH vì sao đã gỡ hoạt
    ảnh giả — đó là chỗ nó NÊN xuất hiện. Cửa hỏi *mã chứa chữ gì* thay vì *mã
    làm gì*: đúng bệnh `x in y`, và là lần thứ hai trong ngày.

    Bỏ khối `/* */`, và bỏ dòng có chú thích `//` — chỉ khi `//` không đứng sau
    dấu hai chấm, kẻo cắt nhầm `http://`.
    """
    chu = re.sub(r"/\*.*?\*/", " ", chu, flags=re.S)
    ra = []
    for d in chu.splitlines():
        i = d.find("//")
        while i != -1 and i > 0 and d[i - 1] == ":":
            i = d.find("//", i + 2)
        ra.append(d[:i] if i != -1 else d)
    return "\n".join(ra)


def _than_ham_js(ten: str) -> str:
    """Cắt lấy thân một hàm JS bằng cách đếm ngoặc nhọn, ĐÃ bỏ chú thích.

    Cắt thân hàm chứ không grep cả tệp: `setTimeout` xuất hiện hợp lệ ở chỗ
    khác trong `noi_bo.js`, nên soi cả tệp thì bài này hoặc đỏ oan, hoặc phải
    nới lỏng tới mức không còn canh được gì.
    """
    chu = _bo_chu_thich_js(JS.read_text(encoding="utf-8"))
    m = re.search(r"(?:async )?function " + re.escape(ten) + r"\s*\([^)]*\)\s*\{", chu)
    assert m, f"không tìm thấy hàm {ten}"
    i = m.end() - 1
    sau, j = 0, i
    while j < len(chu):
        if chu[j] == "{":
            sau += 1
        elif chu[j] == "}":
            sau -= 1
            if sau == 0:
                return chu[i:j + 1]
        j += 1
    raise AssertionError(f"{ten}: ngoặc không đóng")


def test_bo_cat_than_ham_that_su_cat_dung():
    """Ca đối chứng cho chính nhạc cụ đo — cắt sai thì mọi bài dưới vô nghĩa."""
    than = _than_ham_js("kichHoatPipeline")
    assert "/api/pipeline/run" in than, "bộ cắt nuốt mất phần gọi API"
    assert "taiLedgerVaEvidence" not in than, "bộ cắt lấn sang hàm khác"
    assert than.startswith("{") and than.endswith("}")


def test_bo_chu_thich_that_su_bo_duoc_va_KHONG_cat_nham_url():
    """Ca đối chứng cho bộ bỏ chú thích. Nó sai một lần rồi thì phải có cửa.

    Bỏ quá tay thì mọi bài dưới xanh oan; bỏ thiếu thì chúng đỏ oan.
    """
    assert _bo_chu_thich_js("// setTimeout(x, 450)\nlet a = 1;").strip() \
        == "let a = 1;"
    assert "setTimeout" not in _bo_chu_thich_js("/* setTimeout ở đây */ let b;")
    # KHÔNG được cắt nhầm dấu `//` trong URL.
    assert "http://a.b/c" in _bo_chu_thich_js("fetch('http://a.b/c');")
    # Và vẫn phải cắt được chú thích đứng SAU một URL trên cùng dòng.
    ra = _bo_chu_thich_js("fetch('http://a.b/c');  // setTimeout ghi chú")
    assert "http://a.b/c" in ra and "setTimeout" not in ra


def test_KHONG_con_hoat_anh_gia_truoc_khi_goi_may_chu():
    """Không được có `setTimeout` chờ suông trong hàm này.

    Chờ suông ở đây chỉ có một mục đích: làm ra vẻ đang chạy.
    """
    than = _than_ham_js("kichHoatPipeline")
    assert "setTimeout" not in than, (
        "còn `setTimeout` trong hàm chạy pipeline — hoạt ảnh giả đã quay lại")
    assert "HOÀN TẤT ✓" not in than, (
        "hàm tự gán 'HOÀN TẤT ✓'; nhãn phải đến TỪ máy chủ qua bảng NHAN")


def test_CO_poll_so_tien_do_va_KHONG_await_truoc_khi_poll():
    """Phải poll, và phải poll SONG SONG với lượt chạy.

    `await fetch(...)` trước khi dựng vòng poll thì poll chỉ bắt đầu sau khi
    chuỗi đã xong — lúc ấy không còn gì để xem.
    """
    than = _than_ham_js("kichHoatPipeline")
    assert "/api/tien_do/" in than, "không poll sổ tiến độ"
    assert "setInterval" in than, "không có vòng poll"

    i_fetch = than.index("'/api/pipeline/run'")
    i_poll = than.index("setInterval")
    assert i_poll > i_fetch, "dựng poll trước cả lượt gọi — sai thứ tự"
    # Lượt gọi chuỗi KHÔNG được `await` ngay tại chỗ.
    truoc = than[max(0, i_fetch - 80):i_fetch]
    assert "await fetch" not in truoc, (
        "`await` ngay lượt gọi chuỗi thì vòng poll không bao giờ chạy song song")


def test_gui_LEN_ca_pipeline_id_va_preset_id():
    """`pipeline_id` để poll được ngay; `preset_id` để thẻ quyết định thể loại.

    `preset_id` TỪNG BỊ VỨT: dòng gọi ở thẻ kịch bản truyền nó vào nhưng hàm
    không khai tham số, nên máy chủ chưa bao giờ nhận được.
    """
    than = _than_ham_js("kichHoatPipeline")
    assert "pipeline_id: pipelineId" in than, "không gửi pipeline_id"
    # Hỏi CẢ ĐIỀU KIỆN, không chỉ hỏi cái khoá. Gieo `...(false ? { preset_id:
    # presetId } : {})` thì chuỗi `preset_id: presetId` VẪN CÒN và bài này xanh
    # mà mù — bệnh `x in y`, bắt được bằng phép gieo chứ không bằng đọc lại.
    assert re.search(r"\.\.\.\(\s*presetId\s*\?\s*\{\s*preset_id:\s*presetId\s*\}",
                     than), "không gửi preset_id, hoặc điều kiện đã bị vô hiệu"

    chu = JS.read_text(encoding="utf-8")
    assert re.search(r"async function kichHoatPipeline\s*\(\s*presetId\s*\)", chu), (
        "hàm không khai tham số presetId — lời gọi ở thẻ sẽ rơi mất")


def test_KHONG_nuot_loi_va_ve_MOI_trang_thai():
    """Lượt FAIL phải nhìn khác lượt chưa bấm.

    Bản trước chỉ vẽ khi `status === 'PASS'`, và bọc tất cả trong
    `catch (_) {}` — một lượt hỏng trông y hệt một lượt chưa chạy.
    """
    than = _than_ham_js("kichHoatPipeline")
    assert "catch (_) {}" not in than, "còn nhánh nuốt lỗi trần"
    assert "data.status === 'PASS'" not in than, (
        "còn điều kiện chỉ vẽ khi PASS — lượt hỏng sẽ không hiện gì")
    for tt in ("FAIL", "KHONG_CHAY_DUOC", "CHUA_CHAY"):
        assert tt in than, f"không có nhãn cho trạng thái {tt}"


@pytest.mark.parametrize("tt", ["DANG_CHAY", "PASS", "FAIL",
                                "KHONG_CHAY_DUOC", "CHUA_CHAY"])
def test_moi_trang_thai_may_chu_deu_co_nhan_tren_man_hinh(tt):
    """Trạng thái nào máy chủ trả về cũng phải có chỗ hiện ra.

    Thiếu một nhãn thì bước ấy hiện ra mã thô — đọc được, nhưng nó là dấu hiệu
    hai bên đã trôi khỏi nhau.
    """
    chu = _bo_chu_thich_js(JS.read_text(encoding="utf-8"))
    m = re.search(r"const NHAN = \{(.*?)\n  \};", chu, re.S)
    assert m, "không tìm thấy bảng NHAN"
    # So theo KHOÁ, không so chuỗi con. Gieo đổi `FAIL:` thành `FAIL_CU:` thì
    # `"FAIL" in ...` vẫn đúng — bảng mất nhãn mà cửa vẫn xanh.
    khoa = set(re.findall(r"^\s*([A-Z_]+)\s*:", m.group(1), re.M))
    assert tt in khoa, f"bảng NHAN thiếu khoá {tt}; đang có {sorted(khoa)}"


# ---------------------------------------------------------------------------
# SƠ ĐỒ BƯỚC PHẢI LÀ CHUỖI CỦA THẺ (06/09/2026)
#
# Máy chủ từ 06/09 chạy đúng `cac_phong` của thẻ. Màn hình thì vẫn có 5 ô
# `step_*` GÕ CỨNG trong HTML, nên một thẻ 2 phòng hiện 5 ô và ba ô đứng im mãi
# mãi — một lời nói dối MỚI đặt lên đúng cái vỏ vừa làm cho trong suốt.
#
# BỐN BÀI DƯỚI LÀ CỬA CHỐNG HỒI QUY, KHÔNG PHẢI BẰNG CHỨNG. Chúng soi cấu
# trúc tệp; thứ chứng minh màn hình chạy đúng là lượt TỰ BẤM trên máy chủ thật
# (cổng 8893, 06/09/2026)::
#
#   card_system_audit   2 ô: gamma · omega        PASS 2/2 · 48 s
#   card_code_doctor    2 ô: delta · gamma        PASS 2/2 · 48 s
#   đồng hồ poll        10,0 -> 16,0 -> ... -> 47,0 s  (đúng 1 s mỗi nhịp)
#   gieo chặn danh mục  0 ô + câu "chưa nạp được", rồi ô hiện dần theo máy chủ
#
# `delta` trước lượt ấy CHƯA TỪNG chạy từ thẻ nào, dù bốn thẻ khai nó.

HTML = PROJECT_ROOT / "interface" / "web" / "noi_bo.html"
CSS = PROJECT_ROOT / "interface" / "web" / "noi_bo.css"


def test_HTML_KHONG_con_go_cung_o_buoc_nao():
    """Hàng sơ đồ phải RỖNG trong HTML — mọi ô do JS dựng từ chuỗi của thẻ."""
    chu = HTML.read_text(encoding="utf-8")
    m = re.search(r'<div class="pipeline-visual-flow" id="pipelineVisualFlow">'
                  r'(.*?)</div>', chu, re.S)
    assert m, "không tìm thấy hàng sơ đồ `pipelineVisualFlow`"
    assert not m.group(1).strip(), (
        f"hàng sơ đồ còn nội dung gõ cứng: {m.group(1)[:120]!r}")
    # Và không ô `step_*` nào sót lại ở chỗ khác trong tệp.
    assert not re.search(r'id="step_', chu), "còn id ô bước gõ cứng trong HTML"


def test_JS_NAP_danh_muc_the_tu_may_chu():
    """`/api/pipeline/presets` có sẵn từ lâu mà màn hình chưa bao giờ gọi."""
    than = _than_ham_js("taiTheQuyTrinh")
    assert "'/api/pipeline/presets'" in than, "không gọi danh mục thẻ"
    assert "so_do_mac_dinh" in than, "không lấy chuỗi mặc định từ máy chủ"

    khoi_dong = _than_ham_js("initCommandCenter")
    assert re.search(r"await\s+taiTheQuyTrinh\s*\(", khoi_dong), (
        "khởi tạo không CHỜ danh mục — bấm thẻ trước khi nạp xong thì vẽ nhầm")


def test_KHONG_con_bang_o_buoc_GO_CUNG_trong_JS():
    """`O_BUOC` cũ ánh xạ đúng 5 phòng; phòng thứ sáu thì không có chỗ hiện."""
    chu = _bo_chu_thich_js(JS.read_text(encoding="utf-8"))
    assert not re.search(r"\bconst\s+O_BUOC\b", chu), (
        "bảng ô bước gõ cứng đã quay lại")


def test_ve_so_do_CUA_THE_duoc_bam_TRUOC_khi_goi_chuoi():
    """Vẽ chuỗi của thẻ, và vẽ TRƯỚC lượt gọi — sau thì màn hình sai vài giây."""
    than = _than_ham_js("kichHoatPipeline")
    assert re.search(r"state\.theQuyTrinh\s*\[\s*presetId\s*\]", than), (
        "không tra thẻ được bấm trong danh mục đã nạp")
    # Hỏi THAM SỐ TRUYỀN VÀO, không chỉ hỏi cái tên hàm. Gieo
    # `veSoDoBuoc(state.soDoMacDinh)` thì dòng tra thẻ ở trên VẪN CÒN nguyên và
    # bài này xanh mà mù — bệnh `x in y`, bắt được bằng phép gieo.
    m = re.search(r"veSoDoBuoc\(([^;]*)\);", than)
    assert m, "không gọi `veSoDoBuoc` trong hàm chạy pipeline"
    assert "the.so_do" in m.group(1), (
        f"vẽ sơ đồ không lấy từ thẻ được bấm: veSoDoBuoc({m.group(1)})")
    i_ve = than.index("veSoDoBuoc")
    i_chay = than.index("'/api/pipeline/run'")
    assert i_ve < i_chay, "vẽ sơ đồ SAU khi gọi chuỗi — sai thứ tự"


def test_o_thieu_thi_DUNG_them_o_chu_khong_bo_qua_im_lang():
    """Bước máy chủ có chạy mà màn hình không có ô thì nó biến mất không dấu vết.

    Gieo thật trong trình duyệt 06/09: chặn `/api/pipeline/presets` thì hàng sơ
    đồ rỗng, rồi ô `gamma` hiện ra khi máy chủ báo, kèm chú *"không có trong sơ
    đồ ban đầu"*.
    """
    than = _than_ham_js("veMotBuoc")
    # Soi NHÁNH NGAY SAU lượt tra ô, không quét cả thân hàm: cuối nhánh dựng ô
    # vẫn còn một `if (!el) return;` hợp lệ (tra lại mà vẫn không thấy). Quét cả
    # thân thì bài này đỏ oan — nó đã đỏ oan đúng như thế ở lượt chạy đầu.
    m = re.search(r"document\.getElementById\(idO\(phongId\)\);\s*"
                  r"if\s*\(\s*!el\s*\)\s*(\{|return)", than)
    assert m, "không tìm thấy nhánh xử lý ô thiếu trong `veMotBuoc`"
    assert m.group(1) == "{", "còn nhánh bỏ qua im lặng khi thiếu ô"
    assert "insertAdjacentHTML" in than, "không dựng ô cho bước lạ"


def test_CSS_co_lop_cho_buoc_HONG():
    """Thiếu `.flow-step.fail` thì bước hỏng chỉ đổi CHỮ, viền không đổi.

    Nó thiếu thật từ 05/09 tới 06/09: `veMotBuoc` gán class `fail` cho cả FAIL
    lẫn KHONG_CHAY_DUOC, và CSS chưa bao giờ có lớp ấy.
    """
    chu = CSS.read_text(encoding="utf-8")
    assert re.search(r"\.flow-step\.fail\s*\{", chu), "CSS thiếu `.flow-step.fail`"
    assert re.search(r"\.flow-empty\s*\{", chu), "CSS thiếu `.flow-empty`"
