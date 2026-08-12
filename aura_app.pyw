"""aura_app.pyw — AURA v3 như một ứng dụng máy tính, một cú bấm.

Đuôi `.pyw` để Windows chạy bằng `pythonw.exe`: không cửa sổ console đen.

Việc của tệp này đúng ba bước:
  1) bật `aura_chat.py` nếu nó chưa chạy (chạy rồi thì DÙNG LẠI, không đẻ thêm)
  2) CHỜ TỚI KHI server thật sự trả lời — không ngủ đại vài giây
  3) mở Edge/Chrome ở chế độ `--app`: cửa sổ riêng, không thanh địa chỉ

Vì sao không ngủ đại: bản `.bat` cũ `timeout /t 1` rồi mở luôn. Ollama nạp model
mất 20-40 giây, nên cửa sổ hiện ra trước khi server sẵn sàng và Sếp thấy trang
lỗi. Ở đây hỏi `/api/status` cho tới khi nó trả lời, tối đa 40 giây.

Bản `.bat` cũ còn trỏ nhầm `localhost:8765/chat.html` — 8765 là cổng của daemon
v2, và v3 phục vụ màn hình chat ở `/` chứ không có đường `/chat.html`. Bấm vào
là ra 404.

KHÔNG bật mascot. KHÔNG bật health guard.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent
CONG = int(os.environ.get("AURA_CHAT_PORT", "8799"))
DIA_CHI = f"http://127.0.0.1:{CONG}"
CHO_TOI_DA = 40.0
_KHONG_CUA_SO = 0x08000000  # CREATE_NO_WINDOW


def _pythonw() -> str:
    exe = Path(sys.executable)
    ung_vien = exe.with_name("pythonw.exe")
    if ung_vien.exists():
        return str(ung_vien)
    trong_venv = GOC / "venv" / "Scripts" / "pythonw.exe"
    return str(trong_venv if trong_venv.exists() else exe)


def dang_chay() -> bool:
    """Server đã sẵn sàng chưa — hỏi thẳng nó, không đoán qua cổng."""
    try:
        with urllib.request.urlopen(f"{DIA_CHI}/api/status", timeout=2) as tra_loi:
            body = json.loads(tra_loi.read().decode("utf-8"))
        return str(body.get("service", "")).startswith("aura-chat")
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return False


def bat_server() -> None:
    lenh = [_pythonw(), str(GOC / "aura_chat.py"), "--port", str(CONG)]
    tuy_chon = {"cwd": str(GOC)}
    if sys.platform.startswith("win"):
        tuy_chon["creationflags"] = _KHONG_CUA_SO
    subprocess.Popen(lenh, **tuy_chon)  # noqa: S603 — lệnh dựng từ hằng số


def cho_san_sang(han: float = CHO_TOI_DA) -> bool:
    """Chờ lặng lẽ — dùng khi không dựng nổi cửa sổ báo."""
    het_gio = time.monotonic() + han
    while time.monotonic() < het_gio:
        if dang_chay():
            return True
        time.sleep(0.6)
    return False


def cho_co_cua_so_bao(han: float = CHO_TOI_DA) -> bool:
    """Chờ, nhưng CÓ nói cho Sếp biết là đang chờ cái gì.

    Lần bấm đầu sau khi bật máy mất 20-40 giây vì Ollama phải nạp 3,1 GB. Không
    có cửa sổ này thì Sếp bấm xong thấy màn hình đứng im, tưởng lối tắt hỏng.

    Đồng hồ đếm giây là cố ý, cùng lý do với đồng hồ trong khung chat: đứng im
    thì không phân biệt được "đang chạy" với "đã chết".

    Dùng Tkinter vì nó nằm sẵn trong Python trên Windows — thêm một thư viện
    nữa chỉ để hiện một dòng chữ thì không đáng.
    """
    try:
        import tkinter as tk
    except ImportError:
        return cho_san_sang(han)

    NEN, CHU, MO, VIEN = "#151E1B", "#E4E8E5", "#949B96", "#E39A3C"
    ket_qua = {"xong": False}
    bat_dau = time.monotonic()

    cua_so = tk.Tk()
    cua_so.overrideredirect(True)          # bỏ khung, trông như hộp thoại chờ
    cua_so.configure(bg=VIEN)
    cua_so.attributes("-topmost", True)
    rong, cao = 340, 132
    x = (cua_so.winfo_screenwidth() - rong) // 2
    y = (cua_so.winfo_screenheight() - cao) // 2
    cua_so.geometry(f"{rong}x{cao}+{x}+{y}")

    ruot = tk.Frame(cua_so, bg=NEN)
    ruot.place(x=1, y=1, width=rong - 2, height=cao - 2)
    # MỘT nhãn mang cả chữ lẫn đồng hồ. Bản đầu tách làm hai và cái nhãn đếm
    # giây khởi tạo rỗng nên nó co lại bằng không — chụp màn hình ra một khoảng
    # trắng, không đọc được gì.
    nhan_chinh = tk.Label(ruot, text="Đang đánh thức AURA…", bg=NEN, fg=CHU,
                          font=("Segoe UI", 13, "bold"), height=2)
    nhan_chinh.pack(pady=(24, 2))
    # Câu này từng ghi "nạp bộ não local", và SAI: `aura_chat.py` chỉ mở cổng,
    # model Ollama nạp ở CÂU HỎI ĐẦU TIÊN chứ không phải lúc khởi động. Chờ ở
    # đây là chờ Python khởi động, khoảng 10 giây.
    tk.Label(ruot, text="mở cửa trò chuyện ở 127.0.0.1:%d" % CONG,
             bg=NEN, fg=MO, font=("Segoe UI", 8)).pack(side="bottom", pady=(0, 14))

    def kiem() -> None:
        troi = time.monotonic() - bat_dau
        if dang_chay():
            ket_qua["xong"] = True
            cua_so.destroy()
            return
        if troi >= han:
            nhan_chinh.config(
                text="AURA chưa lên sau %.0f giây.\nSếp thử bấm lại giúp em." % han,
                fg=VIEN, font=("Segoe UI", 11, "bold"),
            )
            cua_so.after(2600, cua_so.destroy)
            return
        nhan_chinh.config(text=f"Đang đánh thức AURA…\n{troi:.0f} giây")
        cua_so.after(500, kiem)

    cua_so.after(120, kiem)
    cua_so.mainloop()
    return ket_qua["xong"]


def tim_trinh_duyet() -> str | None:
    """Tìm Edge/Chrome thật — KHÔNG tin mỗi `shutil.which`.

    Đo 10/08/2026: `shutil.which("msedge")` trả `None` trên máy Sếp, vì Windows
    không đặt Edge lên PATH mà đăng ký nó ở registry `App Paths`. Mã cũ rơi
    xuống `webbrowser.open()` và mở một TAB THƯỜNG trong cửa sổ Edge đang mở —
    đúng thứ nó cố tránh.
    """
    if sys.platform.startswith("win"):
        import winreg

        # Vòng ngoài là TRÌNH DUYỆT, vòng trong mới là hive — lồng ngược lại
        # thì hive người dùng thắng và máy Sếp vớ phải Brave dù có sẵn Edge.
        for ten in ("msedge.exe", "chrome.exe", "brave.exe"):
            for goc in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(
                        goc,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion"
                        rf"\App Paths\{ten}",
                    ) as khoa:
                        duong = winreg.QueryValue(khoa, None)
                    if duong and Path(duong).is_file():
                        return duong
                except OSError:
                    continue

        for thu_muc in (
            os.environ.get("ProgramFiles(x86)", ""),
            os.environ.get("ProgramFiles", ""),
            os.environ.get("LOCALAPPDATA", ""),
        ):
            if not thu_muc:
                continue
            for duoi in (
                r"Microsoft\Edge\Application\msedge.exe",
                r"Google\Chrome\Application\chrome.exe",
            ):
                ung_vien = Path(thu_muc) / duoi
                if ung_vien.is_file():
                    return str(ung_vien)

    for ten in ("msedge", "chrome", "brave", "chromium"):
        duong = shutil.which(ten)
        if duong:
            return duong
    return None


def mo_cua_so() -> bool:
    """Cửa sổ riêng, có mặt trên thanh tác vụ như một ứng dụng thật.

    `--user-data-dir` riêng là thứ khiến Windows coi đây là một ứng dụng độc
    lập, chứ không phải một tab nữa của trình duyệt Sếp đang mở.

    Trả về `False` khi phải mở bằng trình duyệt thường — để `main()` nói thật
    thay vì im lặng đưa Sếp một cái tab.
    """
    duong = tim_trinh_duyet()
    if duong is None:
        import webbrowser

        webbrowser.open(f"{DIA_CHI}/")
        return False

    ho_so = GOC / "data" / "app_window"
    ho_so.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(  # noqa: S603 — đường dẫn lấy từ registry của Windows
        [
            duong,
            f"--app={DIA_CHI}/",
            f"--user-data-dir={ho_so}",
            "--window-size=880,900",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        cwd=str(GOC),
    )
    return True


def main() -> int:
    if not dang_chay():
        bat_server()
        # Không mở cửa sổ trỏ vào một server chưa sống — Sếp sẽ thấy trang lỗi
        # và tưởng AURA hỏng, trong khi nó chỉ đang nạp model.
        if not cho_co_cua_so_bao():
            return 1
    mo_cua_so()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
