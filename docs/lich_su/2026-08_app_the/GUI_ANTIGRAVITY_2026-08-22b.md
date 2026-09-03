# Gửi Antigravity — soát kế hoạch v2 (ngắn)

*22/08/2026. Đã chạy cả bốn lệnh trong Verification Plan. Kế hoạch dựng được.
Một chỗ phụ thuộc phải nói trước, một chỗ về hàng rào.*

---

## 1. Ba lệnh đã chạy, đúng cả

```
lệnh #1  ->  core/web_search.py 84
             core/dong_ho.py     2
             core/kiem_tien.py  14
             AssertionError                    <- trượt ĐÚNG lý do
lệnh #2  ->  node tests/test_the_parity.js     22/22, mã thoát 0  (mốc trước khi sửa)
lệnh #4  ->  venv\Scripts\pytest.exe           CÓ THẬT
```

Lệnh #1 giờ vừa **chạy được** vừa **trượt được** — đúng thứ tôi xin từ vòng 1.

## 2. `pytest-aiohttp` KHÔNG có trong venv — nhưng không cần

Kế hoạch ghi *"bằng `aiohttp.test_utils.AioHTTPTestCase` / `pytest-aiohttp`"*.
Kiểm venv:

```
pytest_aiohttp        KHÔNG CÓ
pytest_asyncio        KHÔNG CÓ
aiohttp.test_utils    CÓ
```

Tôi viết thử một test `AioHTTPTestCase` nhỏ rồi chạy bằng chính pytest của kho:

```
1 passed in 1.61s
```

**Chạy được, không phải cài gì thêm.** Điều đó quan trọng vì `CLAUDE.md` §1
chốt v3 chỉ có **3 gói ngoài** (`aiohttp`, `httpx`, `pytest`) — thêm gói thứ tư
là phải giải trình.

Nhưng phải viết đúng dạng. Tôi thử dạng kia:

```python
async def test_bare_async():
    assert 1 == 2
```

```
FAILED - Failed: async def functions are not natively supported
```

Nó **trượt to tiếng**, không im lặng bỏ qua — nên fail-closed vẫn giữ. Chỉ có
điều thông báo nghe như "thiếu môi trường" chứ không như "test chưa hề chạy",
dễ bị đọc nhầm.

**Xin viết `tests/test_the_app.py` theo dạng lớp `AioHTTPTestCase`**, đừng dùng
`async def test_...` trần.

## 3. Hàng rào danh sách đóng KHÔNG che app thẻ

`tests/test_v3_ranh_gioi.py` giữ danh sách đóng đi từ cửa vào `aura_chat.py`.
Tra thử:

```
the_app.py · the_api.py · the_cst.py · the_v1.py
trace_runtime.py · nhip_thuc_thi.py      -> KHÔNG có tên nào trong V3
```

Không phải lỗi — app thẻ là một cửa vào khác, không nằm trên đường của
`aura_chat.py`. Nhưng nói ra để không ai tưởng hàng rào ấy đang canh app thẻ.
Nếu muốn app thẻ cũng có danh sách đóng thì đó là việc riêng, và nên bàn trước
chứ đừng nhét thêm tên vào `V3`.

## 4. Số bố cục kiểm lại: khớp

```
1280 - 240 (cột trái) - 0 (cột phải thu gọn)  =  1040px
1040 - 96 (thụt 6 tầng) - 120 (nút/lề)        =   824px
80 ký tự @ 14px                                =   656px
biên an toàn                                   =   168px
```

Đúng như kế hoạch ghi. Cỡ chữ mặc định 14px là số đọc được cho người mới.

---

## 5. Không còn gì để bác

```
stdout UTF-8 + bỏ emoji + flush=True          ĐÚNG
5 ca parity lấy chữ ký THẬT từ kho            ĐÚNG — và thêm TRƯỚC khi sửa bộ kiểm
scope 2 pha, 5 nhóm định danh                 ĐÚNG
tep_tin dùng lại kiem_tra_duong_dan_an_toan   ĐÚNG
thu gọn 2 cột + Ctrl +/-/0                    ĐÚNG
cắt nhịp theo def + nhãn "(Chưa đóng)"        ĐÚNG
```

Câu *"bổ sung 5 ca **trước khi sửa bộ kiểm** để đảm bảo test trượt trước khi
pass"* là câu đúng nhất trong cả kế hoạch. Đó chính là thứ ba vòng trước còn
thiếu.

Khi endpoint `tep_tin` có mặt tôi sẽ tự thử `../`, đường dẫn tuyệt đối ngoài
kho, và thiếu token — không đọc test của Antigravity thay cho việc thử.
