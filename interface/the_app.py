# -*- coding: utf-8 -*-
"""the_app.py — Entrypoint máy chủ Web App Lập trình bằng THẺ v1.

Chạy máy chủ aiohttp trên loopback (127.0.0.1) và tự động mở giao diện trình duyệt.
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys
import webbrowser
from pathlib import Path
from typing import Optional

from aiohttp import web

from interface import the_api


# Thư mục cấp một mà hộp "Mở tệp" được phép liệt kê.
#
# ĐÂY LÀ HÀNG RÀO AN TOÀN THẬT, không phải tiện nghi. `tests/test_the_app.py`
# đóng đinh: `?thu_muc=data` phải trả 403. Nới bừa là mở rào mà không ai biết.
#
# 25/08, lúc đóng gói: bộ ba `("core","interface","tests")` đóng cứng theo bố
# cục CỦA KHO NÀY. Chạy thử trên một dự án khác thì chỉ `core` tồn tại — hai
# thư mục kia không có, và một dự án của người dùng thì chẳng có lý do gì phải
# đặt tên như vậy.
#
# Sửa: chạy trên chính kho này thì giữ NGUYÊN bộ ba cũ (test 403 không đổi);
# chạy với `--du-an` trỏ chỗ khác thì suy từ thư mục cấp một CÓ THẬT của dự
# án, loại thư mục ẩn và mấy thứ không ai muốn duyệt.
#
# Hàng rào thứ hai vẫn còn nguyên bên trong `api_danh_sach_tep`:
# `is_relative_to(project_root)`. Cái ở đây chỉ là hàng rào ngoài.
BO_QUA_KHI_QUET = {"venv", ".venv", "__pycache__", "node_modules", "site-packages"}


def thu_muc_duoc_quet(root: Path) -> tuple[str, ...]:
    """Danh mục thư mục cấp một cho phép liệt kê, suy từ `root`."""
    if root.resolve(strict=False) == the_api.DEFAULT_PROJECT_ROOT.resolve(strict=False):
        # Chạy ngay trên kho AURA — giữ đúng hàng rào cũ, kể cả việc CHẶN `data`.
        return the_api.ALLOWED_SCAN_DIRS
    try:
        ten = sorted(
            d.name for d in root.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name not in BO_QUA_KHI_QUET
        )
    except OSError:
        return ()
    return tuple(ten)


def tao_app(
    project_root: Optional[Path | str] = None,
    allow_code_execution: Optional[bool] = None,
    auth_token: Optional[str] = None,
) -> web.Application:
    """Khởi tạo aiohttp Application với các route API và static files per-app context."""
    app = web.Application(client_max_size=10 * 1024 * 1024)  # 10 MB

    root = Path(project_root).resolve(strict=False) if project_root is not None else the_api.DEFAULT_PROJECT_ROOT.resolve(strict=False)
    if allow_code_execution is None:
        allow_code_execution = os.environ.get("AURA_THE_ALLOW_CODE_EXECUTION", "").strip() == "1"
    token = str(auth_token) if auth_token is not None else secrets.token_hex(16)

    config = the_api.AppConfig(
        project_root=root,
        static_dir=the_api.STATIC_DIR_GOI.resolve(strict=False),
        allowed_scan_dirs=thu_muc_duoc_quet(root),
        auth_token=token,
        allow_code_execution=bool(allow_code_execution),
    )
    runtime = the_api.AppRuntimeState()

    app["aura_config"] = config
    app["aura_runtime"] = runtime

    # Backward compatibility
    app["project_root"] = config.project_root
    app["allow_code_execution"] = config.allow_code_execution
    app["auth_token"] = config.auth_token

    # Cleanup lifecycle hook
    async def _on_app_cleanup(app_instance: web.Application) -> None:
        runtime_state = app_instance.get("aura_runtime")
        if runtime_state and runtime_state.active_job_process is not None:
            proc = runtime_state.active_job_process
            try:
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
            except Exception:
                pass
            runtime_state.active_job_process = None
            runtime_state.busy_info["is_busy"] = False

    app.on_cleanup.append(_on_app_cleanup)

    # Routes
    app.router.add_get("/", the_api.trang_chu)
    app.router.add_get("/static/{filename:.*}", the_api.file_tinh)
    
    # API endpoints
    app.router.add_get("/api/status", the_api.api_status)
    app.router.add_get("/api/model", the_api.api_model)
    app.router.add_post("/api/hoi_model", the_api.api_hoi_model)
    app.router.add_get("/api/mau", the_api.api_mau_chuong_trinh)
    app.router.add_get("/api/tep_tin", the_api.api_danh_sach_tep)
    app.router.add_post("/api/kiem", the_api.api_kiem_tra)
    app.router.add_post("/api/chay", the_api.api_chay_ma)
    app.router.add_post("/api/trace", the_api.api_trace)
    app.router.add_post("/api/nhip", the_api.api_nhip)
    app.router.add_post("/api/mo_tep", the_api.api_mo_tep)
    app.router.add_post("/api/luu_tep", the_api.api_luu_tep)
    app.router.add_post("/api/dinh_vi_loi", the_api.api_dinh_vi_loi)

    return app


def _cong_dung_duoc(host: str, port: int) -> bool:
    """Cổng này còn trống không — hỏi hệ điều hành, không đoán.

    Thử buộc một socket rồi thả ra ngay. Đây là một CỬA SỔ HẸP: giữa lúc thả
    và lúc `web.run_app` buộc thật, một tiến trình khác có thể chen vào. Nên
    lời gọi này KHÔNG thay cho việc bắt `OSError` ở dưới — nó chỉ để câu báo
    hiện ra TRƯỚC banner trong ca thường gặp (app đã chạy sẵn).

    KHÔNG dùng `SO_REUSEADDR`: trên Windows cờ ấy cho phép buộc chồng lên một
    cổng đang dùng, tức phép thử sẽ luôn nói "còn trống" và cửa này thành lệnh
    rỗng.
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False


def main():
    # NHÁNH ĐÓNG VAI THÔNG DỊCH — phải nằm TRƯỚC argparse.
    #
    # 31/08/2026: bản `.exe` bấm CHẠY THỬ ra `unrecognized arguments: -X utf8`,
    # vì argparse ở dưới thấy đối số nó không biết. Nên nhánh này chặn ở trên,
    # không đi qua parser.
    #
    # Chỉ mở khi ĐÃ đóng băng. Bản chạy từ mã nguồn không cần — ở đó
    # `sys.executable` vốn đã là `python.exe` thật, và mở thêm một đường chạy
    # tệp tuỳ ý là tự thêm một cửa không ai canh.
    if getattr(sys, "frozen", False) and len(sys.argv) >= 3 and sys.argv[1] == "--chay-tep-python":
        import runpy

        for _l in (sys.stdout, sys.stderr):
            if hasattr(_l, "reconfigure"):
                _l.reconfigure(encoding="utf-8", errors="replace")
        _tep = sys.argv[2]
        sys.argv = [_tep] + sys.argv[3:]
        try:
            runpy.run_path(_tep, run_name="__main__")
        except SystemExit:
            raise
        except BaseException as _loi:  # noqa: BLE001 — mã người học, mọi thứ đều có thể
            # CẮT KHUNG NỘI BỘ khỏi traceback.
            #
            # 31/08/2026, đo trên bản .exe vừa vá: `print(chia(1, 0))` trả về
            # đúng ZeroDivisionError, nhưng phía trên nó có NĂM dòng người học
            # không viết và không hiểu:
            #     File "the_app.py", line 333, in <module>
            #     File "the_app.py", line 160, in main
            #     File "<frozen runpy>", line 294, in run_path
            #     File "<frozen runpy>", line 98,  in _run_module_code
            #     File "<frozen runpy>", line 88,  in _run_code
            # và ở CUỐI một dòng còn tệ hơn:
            #     [PYI-...:ERROR] Failed to execute script 'the_app' due to
            #     unhandled exception!
            # Dòng ấy đọc như AURA vừa sập, trong khi thứ hỏng là phép chia của
            # người học. Cùng họ với lỗi 30/08 (máy chủ hỏng bị dán nhãn "LỖI
            # RUNTIME"): đừng để người học đi sửa thứ họ không gây ra, và cũng
            # đừng bắt họ đọc ruột của app.
            #
            # Bản chạy bằng `python.exe` không có hai thứ này, nên đây là giá
            # phải trả riêng của bản đóng băng — trả ở đây, một chỗ.
            import traceback

            _tb = _loi.__traceback__
            while _tb is not None and _tb.tb_frame.f_code.co_filename != _tep:
                _tb = _tb.tb_next
            traceback.print_exception(type(_loi), _loi, _tb, file=sys.stderr)
            sys.stderr.flush()
            sys.stdout.flush()
            # `sys.exit` chứ không để lỗi bay lên: bay lên là bootloader của
            # PyInstaller in dòng "Failed to execute script" nói trên.
            sys.exit(1)
        return

    # Chỉnh CẢ HAI: `stdout` và `stderr`.
    #
    # 25/08: bản đầu chỉ chỉnh `stdout`. Chạy bản đã cài thì `--help` ra đúng,
    # nhưng câu từ chối bind — thứ đi ra `stderr` — vẫn hỏng:
    #   "AURA Chat v1 chưa c? x?c thực n?n từ chối..."
    # Người dùng gặp lỗi chính là lúc cần đọc được câu tiếng Việt nhất.
    for _luong in (sys.stdout, sys.stderr):
        if hasattr(_luong, "reconfigure"):
            _luong.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="AURA App Lập trình bằng THẺ (v1)")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ bind (chỉ loopback)")
    parser.add_argument("--port", type=int, default=8088, help="Cổng chạy máy chủ")
    parser.add_argument("--no-browser", action="store_true", help="Không tự động mở trình duyệt")
    # 23/08: trước đây chỉ bật được bằng biến môi trường
    # AURA_THE_ALLOW_CODE_EXECUTION=1. Nên bấm start_the_app.bat thì app mở
    # được nhưng nút "TÌM LỖI" và "DÒ DÒNG DỮ LIỆU" đều khoá, và KHÔNG CÓ CÁCH
    # NÀO bật từ dòng lệnh — hai tính năng chính thành không dùng được.
    parser.add_argument(
        "--allow-exec", action="store_true",
        help="Bật chạy mã/test (/api/chay, /api/trace, /api/dinh_vi_loi). "
             "Tắt mặc định vì tiến trình chưa được cách ly khỏi tệp/mạng/RAM")
    parser.add_argument(
        "--du-an", default=None, metavar="ĐƯỜNG_DẪN",
        help="Thư mục dự án — nơi mở và lưu tệp .py. Mặc định: thư mục hiện "
             "tại, theo lối `git` hay `code .`")
    args = parser.parse_args()
    if args.allow_exec:
        os.environ["AURA_THE_ALLOW_CODE_EXECUTION"] = "1"

    # CỬA BẢO MẬT: Chỉ cho phép bind vào loopback / 127.0.0.1
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"[BẢO MẬT]: Từ chối bind vào địa chỉ ngoài loopback: {args.host}", flush=True)
        sys.exit(1)

    # 25/08: mặc định là THƯ MỤC HIỆN TẠI, không phải thư mục chứa mã app.
    #
    # Cài bằng `pip` thì mã app nằm ở `site-packages` — không ai muốn mở/lưu
    # tệp .py của mình ở đó. Chạy `aura-the` ngay trong thư mục dự án là lối
    # quen thuộc của `git`, `code .`, `jupyter notebook`.
    #
    # Chạy từ trong kho AURA thì thư mục hiện tại CHÍNH LÀ gốc kho, nên hành
    # vi cũ không đổi.
    du_an = Path(args.du_an).resolve(strict=False) if args.du_an else Path.cwd()
    if not du_an.is_dir():
        print("[LỖI]: Thư mục dự án không tồn tại: %s" % du_an, flush=True)
        sys.exit(1)

    # KIỂM CỔNG TRƯỚC KHI IN BANNER.
    #
    # 27/08/2026. Bản sửa đầu của tôi bắt `OSError` quanh `web.run_app`, và
    # câu báo hiện ra ĐÚNG nhưng SAU banner — tức người dùng đọc:
    #
    #     Địa chỉ web   : http://127.0.0.1:8088/?token=...
    #     Bấm Ctrl+C để dừng máy chủ.
    #     KHÔNG MỞ ĐƯỢC: cổng 8088 đang có thứ khác dùng.
    #
    # Banner nói app đang chạy, rồi ba dòng sau nói không mở được. Bắt được
    # bằng cách tự chạy hai lần và ĐỌC kết xuất, không phải bằng đọc mã.
    #
    # Nên thử buộc cổng TRƯỚC, khi chưa in gì. Bận thì báo và dừng, banner
    # không bao giờ xuất hiện.
    if not _cong_dung_duoc(args.host, args.port):
        print("=" * 70, flush=True)
        print(f"  KHÔNG MỞ ĐƯỢC: cổng {args.port} đang có thứ khác dùng.",
              flush=True)
        print("=" * 70, flush=True)
        print("  Thường là do AURA đã chạy sẵn rồi. Thử mở địa chỉ này trước:",
              flush=True)
        print(f"      http://{args.host}:{args.port}", flush=True)
        print("", flush=True)
        print("  Nếu không phải, dùng cổng khác:", flush=True)
        print(f"      aura-the --port {args.port + 1}", flush=True)
        print("=" * 70, flush=True)
        sys.exit(1)

    app = tao_app(project_root=du_an)
    token = app["aura_config"].auth_token
    app_url = f"http://{args.host}:{args.port}/?token={token}"

    # BANNER VIẾT CÓ DẤU, VÀ NÓI CẢ GIỚI HẠN — sửa 26/08/2026.
    #
    # Bản cũ viết không dấu ("APP LAP TRINH BANG THE", "Dia chi web") vì hồi
    # ấy bảng mã còn hỏng. Nay `main()` đã chỉnh cả `stdout` lẫn `stderr` sang
    # UTF-8 (commit 5c6ce52) nên hiện dấu được.
    #
    # Bản cũ in "Bao mat: 4 lop" và DỪNG Ở ĐÓ. Bốn lớp ấy CÓ THẬT — đã kiểm
    # từng lớp bằng cách gọi API sống: `--host 0.0.0.0` thoát 1 · không token
    # 403 · Origin lạ 403 (Origin đúng 200) · đường dẫn ra ngoài dự án 400.
    #
    # Nhưng câu ấy đứng một mình thì người đọc hiểu là "chạy mã ở đây an toàn".
    # KHÔNG PHẢI. Bốn lớp bảo vệ CỔNG VÀO — ai gọi được API. Chúng không bảo
    # vệ gì khi mã đã chạy. Đo 25/08 qua đúng đường app dùng: ghi tệp bằng
    # đường dẫn tuyệt đối ngoài thư mục tạm GHI ĐƯỢC · gọi tiến trình con
    # CHẠY ĐƯỢC · mở socket MỞ ĐƯỢC · đọc tệp bất kỳ ĐỌC ĐƯỢC.
    #
    # README và chân giao diện đã nói thật chỗ này; banner thì chưa — mà banner
    # là thứ người dùng nhìn thấy ĐẦU TIÊN.
    #
    # Thêm dòng THƯ MỤC DỰ ÁN: bản cũ không in nó, nên người dùng không biết
    # app sẽ đọc/ghi tệp ở đâu. Với `aura-the` cài bằng pip thì đó là thư mục
    # hiện tại, và người dùng rất dễ chạy nhầm chỗ.
    bat_chay_ma = app["aura_config"].allow_code_execution

    print("=" * 70, flush=True)
    print("  AURA — APP LẬP TRÌNH BẰNG THẺ (bản v1)", flush=True)
    print("=" * 70, flush=True)
    print(f"  Địa chỉ web   : {app_url}", flush=True)
    print(f"  Mã thông hành : {token}", flush=True)
    print(f"  Thư mục dự án : {du_an}", flush=True)
    print("  Cổng vào      : 4 lớp — chỉ loopback · mã thông hành · Origin · "
          "khoá đường dẫn", flush=True)
    if bat_chay_ma:
        print("  Chạy mã       : ĐÃ BẬT (--allow-exec)", flush=True)
        print("=" * 70, flush=True)
        print("  ⚠  Mã bạn chạy ở đây có ĐỦ QUYỀN của tài khoản Windows đang", flush=True)
        print("     dùng. KHÔNG có hộp cát. Bốn lớp trên chỉ giữ CỔNG VÀO,", flush=True)
        print("     chúng không giữ được gì khi mã đã chạy.", flush=True)
        print("     Chỉ chạy mã do CHÍNH BẠN viết. Xem mục an toàn trong README.", flush=True)
    else:
        print("  Chạy mã       : TẮT mặc định — mở, sửa, kiểm tra, lưu vẫn dùng "
              "được", flush=True)
        print("                  (bật bằng --allow-exec; đọc mục an toàn trong "
              "README trước)", flush=True)
    print("=" * 70, flush=True)
    print("  Bấm Ctrl+C để dừng máy chủ.\n", flush=True)

    if not args.no_browser:
        webbrowser.open(app_url)

    try:
        web.run_app(app, host=args.host, port=args.port, print=None)
    except OSError as loi:
        # CỔNG ĐANG BẬN THÌ NÓI TIẾNG NGƯỜI, ĐỪNG ĐỔ VẾT NGĂN XẾP.
        #
        # 27/08/2026. Mở app lần thứ hai trên cùng cổng thì người dùng nhận
        # ĐÚNG 12 dòng: `aiohttp/web_runner.py` · `asyncio/base_events.py` ·
        # `OSError: [Errno 10048] ... only one usage of each socket address`.
        # Đã đo bằng cách chạy `aura-the --port 8088` hai lần.
        #
        # Cổng mặc định là 8088 và README cũng bảo gõ `--port 8088`, nên đây
        # KHÔNG phải ca hiếm: mở app lần hai, hoặc quên rằng lần trước chưa
        # tắt, là gặp. Mà người app nhắm tới là "người chưa viết nổi Python
        # trôi chảy" — vết ngăn xếp với họ chỉ là màn hình dọa người, và nó
        # không nói phải làm gì.
        #
        # 10048 là mã Windows (WSAEADDRINUSE); 98 là Linux (EADDRINUSE). Bắt
        # cả hai chứ không chỉ Windows — đọc `errno` chứ không dò chuỗi tiếng
        # Anh trong lời lỗi, vì lời ấy đổi theo ngôn ngữ hệ điều hành.
        if loi.errno not in (10048, 98):
            raise
        print("=" * 70, flush=True)
        print(f"  KHÔNG MỞ ĐƯỢC: cổng {args.port} đang có thứ khác dùng.",
              flush=True)
        print("=" * 70, flush=True)
        print("  Thường là do AURA đã chạy sẵn rồi. Thử mở địa chỉ này trước:",
              flush=True)
        print(f"      http://{args.host}:{args.port}", flush=True)
        print("", flush=True)
        print("  Nếu không phải, dùng cổng khác:", flush=True)
        print(f"      aura-the --port {args.port + 1}", flush=True)
        print("=" * 70, flush=True)
        # `sys.exit` chứ không `return 1`: `python -m interface.the_app` gọi
        # `main()` rồi bỏ qua giá trị trả về, nên `return` không đặt được mã
        # thoát. Hai chỗ báo lỗi khác trong tệp này (dòng 154, 167) cũng dùng
        # `sys.exit(1)`.
        sys.exit(1)


if __name__ == "__main__":
    main()
