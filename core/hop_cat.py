# -*- coding: utf-8 -*-
"""Hộp cát cho tiến trình chạy mã người ngoài gửi — Windows Job Object.

VÌ SAO CÓ TỆP NÀY (08/09/2026)

`/api/polyglot/run` chạy **mã tuỳ ý** và cho tới hôm nay chỉ có `timeout`.
Đo nền bằng 8 đơn chạy qua chính `chay_ma_da_ngon_ngu`:

    1. cwd                    D:\\AURA_v3   <- gốc kho, không phải thư mục tạm
    2. GHI tệp ngoài          ĐƯỢC
    3. đọc `.env` của kho     đường đọc MỞ
    4. liệt kê HOME           87 mục
    5. biến môi trường        87 biến, có tên nghi là bí mật (`CLAUDE_*`)
    6. RA MẠNG                ĐƯỢC — mã 200
    7. cấp phát 300 MB        ĐƯỢC
    8. TIẾN TRÌNH MỒ CÔI      SỐNG SÓT qua timeout

Mục 8 chưa ai ghi và là chỗ nặng nhất: `subprocess.run(timeout=)` chỉ giết
**con trực tiếp**. Một dòng `Popen` là cháu sống tiếp — **bảo vệ duy nhất đang
có bị vượt bằng một dòng**.

THỬ TRƯỚC KHI VIẾT VÀO SẢN PHẨM. Bài 19/08: một kế hoạch hứa "giới hạn 256 MB
RAM" bằng `import resource` — API Unix, Windows không có, và nó suýt đi vào tài
liệu thành *"đã có sandbox 256 MB"*. Nên nguyên mẫu chạy trước, trên chính máy
này:

    KILL_ON_JOB_CLOSE   cha báo 'DA SINH chau' -> đóng job -> cháu KHÔNG sống sót
    PROCESS_MEMORY      trần 128 MB, xin 300 MB -> mã thoát 1, CHẶN ĐƯỢC

BỐN THỨ CHẶN ĐƯỢC, BA THỨ KHÔNG — và ba thứ ấy phải ở lại trong lời mô tả:

    chặn được       cwd riêng · biến môi trường sạch · trần RAM · giết cả cây
    CHƯA CHẶN ĐƯỢC  ghi tệp bằng đường dẫn tuyệt đối
                    đọc tệp bất kỳ / liệt kê HOME
                    ra mạng

Chặn được bốn thứ **không** cho phép viết "đã cô lập". Chỗ dựa thật vẫn là
`/api/polyglot/run` không được đặt ra Internet.
"""
from __future__ import annotations

import ctypes
import os
import sys
from typing import Any, Dict, Tuple

# CON SỐ CHỌN — cùng con số kế hoạch 19/08 đã hứa mà không giao được. Python
# rỗng tốn ~25 MB nên 256 rộng rãi cho một đoạn mã ngắn.
RAM_MB = 256

# Giữ đúng những biến một tiến trình cần để chạy. Mọi thứ khác bị bỏ, vì khoá
# API sống trong biến môi trường (`CLAUDE.md` mục 2).
BIEN_GIU = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE", "TEMP", "TMP", "PATH")

_JobObjectExtendedLimitInformation = 9
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001

_LA_WINDOWS = sys.platform == "win32"

if _LA_WINDOWS:
    import ctypes.wintypes as _wt

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                    ("WriteOperationCount", ctypes.c_ulonglong),
                    ("OtherOperationCount", ctypes.c_ulonglong),
                    ("ReadTransferCount", ctypes.c_ulonglong),
                    ("WriteTransferCount", ctypes.c_ulonglong),
                    ("OtherTransferCount", ctypes.c_ulonglong)]

    class _BASIC(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", _wt.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", _wt.DWORD),
                    ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
                    ("PriorityClass", _wt.DWORD),
                    ("SchedulingClass", _wt.DWORD)]

    class _EXTENDED(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BASIC),
                    ("IoInfo", _IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]


def moi_truong_sach() -> Dict[str, str]:
    """Biến môi trường tối thiểu. Khoá API sống ở đây nên mặc định là BỎ HẾT."""
    return {k: os.environ[k] for k in BIEN_GIU if k in os.environ}


def tao_job(ram_mb: int = RAM_MB) -> Tuple[Any, str]:
    """Tạo Job Object. Trả `(handle, lý do nếu không tạo được)`.

    KHÔNG ném ngoại lệ: không tạo được thì chạy như cũ và **nói ra**. Nuốt lỗi
    ở đây sẽ thành một lời hứa an toàn không kiểm được.
    """
    if not _LA_WINDOWS:
        return None, f"không phải Windows ({sys.platform}) — chưa có bản cho nền này"
    try:
        h = _k32.CreateJobObjectW(None, None)
        if not h:
            return None, f"CreateJobObject lỗi {ctypes.get_last_error()}"
        info = _EXTENDED()
        info.BasicLimitInformation.LimitFlags = (
            _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | _JOB_OBJECT_LIMIT_PROCESS_MEMORY)
        info.ProcessMemoryLimit = ram_mb * 1024 * 1024
        if not _k32.SetInformationJobObject(
                _wt.HANDLE(h), _JobObjectExtendedLimitInformation,
                ctypes.byref(info), ctypes.sizeof(info)):
            ma = ctypes.get_last_error()
            _k32.CloseHandle(_wt.HANDLE(h))
            return None, f"SetInformationJobObject lỗi {ma}"
        return h, ""
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"


def gan_vao_job(h_job: Any, pid: int) -> bool:
    """Gán tiến trình vào job.

    CÓ MỘT KHE ĐUA, nói ra chứ không giấu: tiến trình được `Popen` khởi động
    RỒI mới gán, nên giữa hai bước ấy nó chạy tự do vài mili giây. Muốn kín thì
    phải `CREATE_SUSPENDED` — mà `subprocess.Popen` không đưa handle luồng ra,
    nên phải bỏ `Popen` và gọi thẳng `CreateProcessW`. Chưa làm; ghi lại.
    """
    if not _LA_WINDOWS or not h_job:
        return False
    h_p = _k32.OpenProcess(_PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, pid)
    if not h_p:
        return False
    ok = _k32.AssignProcessToJobObject(_wt.HANDLE(h_job), _wt.HANDLE(h_p))
    _k32.CloseHandle(_wt.HANDLE(h_p))
    return bool(ok)


def dong_job(h_job: Any) -> None:
    """Đóng job — `KILL_ON_JOB_CLOSE` giết CẢ CÂY tiến trình."""
    if _LA_WINDOWS and h_job:
        _k32.CloseHandle(_wt.HANDLE(h_job))
