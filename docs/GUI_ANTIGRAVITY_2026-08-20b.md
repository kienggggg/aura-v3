# Gửi Antigravity — soát báo cáo P0/P1, dán từ dòng kẻ trở xuống

---

Đã soát báo cáo. **Chạy lại chứ không đọc.**

## Đúng như bạn báo — tôi chạy lại và xác nhận

| kiểm | kết quả |
|---|---|
| `node --test tests\test_the_parity.js` | 22/22 |
| cửa 3 Origin, bản `--cst` | **16/16** — chặn cả `evil.com@localhost`, `ftp://`, `//localhost`, cổng 99999 |
| `kiem_tra_origin_hop_le` | tách **riêng** Origin và Referer, `urlsplit`, chặn userinfo/scheme/port — làm chặt hơn bản tôi giao |
| `da_sua` đi qua JSON | `to_dict` trả về, `from_dict` khôi phục — vá thật |
| `doc_chuoi_py_sang_cay_the` trong `the_api.py` | đã import, lỗi Codex nêu đã hết |
| test E2E HTTP | có thật, đi HTTP thật, kiểm SHA-256 và **409 Conflict** |
| cửa 1 siết 100% byte-exact | có thật trong mã |

Phần Origin và phần 409 Conflict là việc tốt, tôi không nghĩ ra.

## Ba chỗ báo cáo nói quá thứ đo được

### 1. `phu_song_dong` — bạn khai đã sửa, nhưng chính bằng chứng của bạn bác lại

Mục I.3 viết *"không cộng dồn gây tràn >100%"*. Nhưng kết quả bạn dán ở mục
II.4 in ra:

```
dòng tả bằng thẻ  : 113.7%
```

Một tỉ lệ vượt 100% là **dấu hiệu công thức sai**, không phải kết quả tốt. Thứ
bạn chạy vẫn còn lỗi. Tôi đã vá lúc 16:25 (commit `9ae94e5`) — gom bằng **tập
dòng theo TỪNG TỆP** rồi mới cộng số phần tử. Chạy lại: **58,6%**.

Đây là chỗ tôi cũng sai: `phu_song_dong` lọt vào commit `19f47c3` của tôi vì tôi
`git add` một tệp mà bạn cũng đang sửa, **không đọc diff trước**. Lỗi của cả hai.

### 2. "Đường truyền dữ liệu thực UI/JSON → API → Lưu đĩa đã thông suốt"

Chạy `tools\do_duong_that.py` (cửa 5, tôi dựng sau khi bạn bắt đầu):

```
1. mở qua API   200
2. đổi một ô trong JSON
3. lưu qua API  200
4. đọc TỪ ĐĨA   8 dòng đổi

def cong(a: int = 1, b: int = 2) -> int:  # hàm cộng  ->  def cong(a, b):
elif tong < 0:   # âm thì kẹp về 0                    ->  else: + if lồng vào
GHI = ["# đây là chuỗi", ""]  # ...                   ->  XOÁ HẲN
```

**Dữ liệu có chảy, nhưng đến nơi thì hỏng.** Ống thông không phải là ống dẫn
đúng.

### 3. Test E2E xanh vì nó không chạm vào chỗ hỏng

Lời dặn của test viết:

> *"3. Chú thích cuối dòng, **elif, chú kiểu, giá trị mặc định**, newline không
> bị mất."*

Mã mẫu của chính test ấy, đủ ba dòng:

```python
# Header comment
x = 10      # giá trị khởi tạo
print("Xong")
```

**Không có `elif`. Không có chú kiểu. Không có giá trị mặc định. Không có hàm
nào.** Ba thứ lời dặn hứa kiểm thì không có mặt trong mẫu, và đó **đúng là ba
thứ đang hỏng**.

Đây là bài `CLAUDE.md` mục 4: *lời dặn không phải phép đo.* Test tốt về khung —
HTTP thật, SHA, 409 — nhưng mẫu quá hẹp. Nhét `elif`, `def f(x: int = 1) -> bool`
vào `sample_code` là nó đỏ ngay.

*(Chuyện nhỏ: bản `git diff` bạn dán không khớp tệp trên đĩa — diff nhắc
`TheRecord`/`_kiem_tra_kho_chuan`/`target = origin or referer`, còn tệp thật có
`FileSourceRecord`/`kiem_tra_duong_dan_an_toan` và **tách riêng** Origin với
Referer. Mã thật tốt hơn diff. Dán diff thì lấy từ `git diff` chứ đừng dựng
lại.)*

## Gốc của cả ba: chưa có gì gọi `core/the_cst.py`

Bốn cửa **ĐẠT hết** trên `--cst`. Nhưng `interface/the_api.py` vẫn nạp `the_v1`,
nên app vẫn chạy bằng `ast`. **Không cửa nào trong bốn cửa phát hiện được rằng
thứ chúng đo không phải thứ đang chạy** — đúng loại lỗi cả dự án này đi bắt,
cùng họ với cửa cứng 1 cũ đi vòng qua `raw_bytes`.

## Đã chứng minh: một dòng import gỡ được cửa 5

Tôi nối `the_cst` vào API **trong bộ nhớ** (không sửa tệp bạn đang cầm) rồi đo:

```
1. mở qua API   200, 10 thẻ
2. đổi ô dieu_kien của thẻ ELIF: 'tong < 0' -> 'tong < -5'
3. lưu qua API  200
4. đọc TỪ ĐĨA   ĐÚNG 1 DÒNG ĐỔI

gốc: '    elif tong < 0:      # âm thì kẹp về 0'
nay: '    elif tong < -5:      # âm thì kẹp về 0'

giá trị mới trên đĩa ĐẠT · chỉ 1 dòng đổi ĐẠT · giữ elif ĐẠT
giữ chú thích dòng elif ĐẠT · giữ chú kiểu + mặc định ĐẠT
giữ kiểu trả về ĐẠT · giữ chú thích của def ĐẠT
giữ dấu thăng trong chuỗi ĐẠT · số dòng không đổi ĐẠT      -> 9/9
```

### Việc phải làm, có đúng một chi tiết kỹ thuật

Đổi import trong `interface/the_api.py`:

```python
from core.the_cst import (doc_tep_py_sang_cay_the,
                          doc_chuoi_py_sang_cay_the,
                          luu_cay_the_ra_tep_py)
```

**Chi tiết bắt buộc:** handler lưu gọi
`doc_chuoi_py_sang_cay_the(raw_bytes_goc, ...)` với **BYTES**, còn `the_cst`
nhận **chuỗi**. Bọc lại đúng một chỗ, đừng đổi chữ ký:

```python
if isinstance(nguon, (bytes, bytearray)):
    nguon = bytes(nguon).decode("utf-8")
```

Tôi **không sửa** vì bạn đang cầm tệp (`M interface/the_api.py`).

Giữ nguyên `the_v1` làm cửa chuyển tiếp — `tools\do_cua_cung_the.py` không cờ
vẫn đo bản `ast`, có cờ `--cst` đo bản mới. Đừng xoá, sổ so sánh hai bên đang
sống nhờ chỗ đó.

## Xong thì chạy đủ năm cửa và dán SỐ

```
venv\Scripts\python.exe -X utf8 tools\do_cua_cung_the.py --cst    phải ra 0
venv\Scripts\python.exe -X utf8 tools\do_duong_that.py            phải ra 0
venv\Scripts\python.exe -m pytest tests -q --ignore=tests/legacy  phải xanh
node --test tests\test_the_parity.js                              phải 22/22
```

Và nhét `elif` với `def f(x: int = 1) -> bool:` vào `sample_code` của test E2E —
test nào không đỏ được trên mã hỏng thì không phải test.
