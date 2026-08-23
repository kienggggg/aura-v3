# -*- coding: utf-8 -*-
"""tools/e1_supervisor_bootstrap.py — Stdlib-only Supervisor Bootstrap cho E1.

Nhiệm vụ:
1. Tự tạo Windows Job Object (hoặc POSIX Process Group), bật KILL_ON_JOB_CLOSE và tự gán PID.
2. Nếu gắn Job Object thất bại trên Windows, fail-closed ngay lập tức (không phát READY).
3. In frame handshake `===E1_SUPERVISOR_READY===` kèm JSON `job_attached: true`.
4. Tạo snapshot clone sạch và cài đặt `sitecustomize.py` chặn mạng ngoại vi ở cấp child process.
5. Preflight xác minh SHA snapshot và pytest collection trong `clean_env`.
6. Chạy worker `_worker_e1_exec.py` trong temp clone với môi trường sạch.
7. Thu thập kết quả, in JSON ra stdout và dọn sạch temp clone trong khối finally.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any, Dict, Optional

_GLOBAL_JOB_HANDLE = None


def _setup_job_object() -> bool:
    """Thiết lập Windows Job Object với cờ tự hủy toàn bộ tiến trình khi đóng."""
    global _GLOBAL_JOB_HANDLE
    if sys.platform != "win32":
        try:
            os.setpgid(0, 0)
            return True
        except Exception:
            return False

    try:
        kernel32 = ctypes.windll.kernel32

        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]

        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []

        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]

        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

        h_job = kernel32.CreateJobObjectW(None, None)
        if not h_job:
            return False

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryLimit", ctypes.c_size_t),
                ("PeakJobMemoryLimit", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        set_info_res = kernel32.SetInformationJobObject(
            h_job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not set_info_res:
            return False

        cur_proc = kernel32.GetCurrentProcess()
        assign_res = kernel32.AssignProcessToJobObject(h_job, cur_proc)
        if not assign_res:
            return False

        _GLOBAL_JOB_HANDLE = h_job
        return True
    except Exception:
        return False


def _install_child_canary(dst_root: Path) -> None:
    """Tạo sitecustomize.py để tự động chặn mạng ngoại vi trong mọi sub-process Python."""
    canary_code = textwrap.dedent("""
        # -*- coding: utf-8 -*-
        import json
        import os
        import socket
        import sys
        from pathlib import Path

        _CANARY_LOG = os.environ.get("AURA_CHILD_CANARY_LOG", "")
        _orig_connect = socket.socket.connect

        def _guarded_connect(self, address):
            host = ""
            port = 0
            if isinstance(address, (tuple, list)) and len(address) > 0:
                host = str(address[0])
                if len(address) > 1:
                    port = address[1]
            else:
                host = str(address)

            is_loopback = host in ("127.0.0.1", "::1", "localhost", "0.0.0.0")

            record = {
                "pid": os.getpid(),
                "executable": sys.executable,
                "target": f"{host}:{port}",
                "is_loopback": is_loopback,
                "blocked": not is_loopback,
            }

            if _CANARY_LOG:
                try:
                    with open(_CANARY_LOG, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\\n")
                except Exception:
                    pass

            if not is_loopback:
                raise PermissionError(f"AURA_CHILD_CANARY_BLOCKED: External network connection ({host}:{port}) forbidden in E1 child process")

            return _orig_connect(self, address)

        socket.socket.connect = _guarded_connect
    """)
    (dst_root / "sitecustomize.py").write_text(canary_code.strip(), encoding="utf-8")


def _copy_manifest(src_root: Path, dst_root: Path) -> None:
    """Sao chép manifest đầy đủ sang temp clone."""
    dst_root.mkdir(parents=True, exist_ok=True)

    # 1. Các tệp gốc
    for fname in ["aura_chat.py", "pytest.ini", "CLAUDE.md", "AGENTS.md"]:
        f_src = src_root / fname
        if f_src.is_file():
            shutil.copy2(f_src, dst_root / fname)

    # 2. Các thư mục chính
    ignore_pat = shutil.ignore_patterns(
        "venv", ".venv*", ".git", "__pycache__", ".pytest_cache", "*.pyc", "_rac", "runs"
    )
    for dname in ["core", "interface", "tests", "tools", "experiments"]:
        d_src = src_root / dname
        if d_src.is_dir():
            shutil.copytree(d_src, dst_root / dname, dirs_exist_ok=True, ignore=ignore_pat)

    # 3. Thư mục data rỗng
    (dst_root / "data").mkdir(exist_ok=True)

    # 4. Cài đặt guard sitecustomize.py
    _install_child_canary(dst_root)


def main():
    # 1. Thiết lập Job Object
    job_ok = _setup_job_object()

    # Fail-closed nếu trên Windows không thể thiết lập Job Object
    if sys.platform == "win32" and not job_ok:
        print(json.dumps({
            "trang_thai": "khong_do_duoc",
            "reason": "Fail-closed: Thiết lập Windows Job Object thất bại",
            "job_attached": False,
        }))
        sys.exit(1)

    # 2. Bắn frame READY
    sys.stdout.write("===E1_SUPERVISOR_READY===\n")
    sys.stdout.write(json.dumps({
        "ready": True,
        "supervisor_pid": os.getpid(),
        "job_attached": job_ok,
        "platform": sys.platform,
    }) + "\n")
    sys.stdout.flush()

    # 3. Đọc cấu hình từ stdin hoặc file arg
    if len(sys.argv) > 1 and Path(sys.argv[1]).is_file():
        cfg_text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        cfg_text = sys.stdin.read()

    try:
        cfg = json.loads(cfg_text)
    except Exception as exc:
        print(json.dumps({"trang_thai": "khong_do_duoc", "reason": f"Không đọc được JSON cấu hình: {exc}"}))
        sys.exit(1)

    project_root = Path(cfg["project_root"]).resolve(strict=False)
    temp_clone_dir = Path(cfg["temp_clone_dir"]).resolve(strict=False)
    tep_nguon_rel = cfg["tep_nguon_rel"].replace("\\", "/")
    tep_test_rel = cfg["tep_test_rel"].replace("\\", "/")
    expected_source_sha = cfg.get("source_sha", "").lower()
    expected_test_sha = cfg.get("test_sha", "").lower()
    deadline_s = float(cfg.get("deadline_s", 300.0))

    try:
        # 4. Sao chép manifest vào temp_clone
        _copy_manifest(project_root, temp_clone_dir)

        # 5. Xác minh SHA snapshot (Barrier 2)
        snap_src = temp_clone_dir / tep_nguon_rel
        snap_test = temp_clone_dir / tep_test_rel

        if not snap_src.is_file() or not snap_test.is_file():
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": "Tệp nguồn hoặc test không tồn tại trong snapshot clone",
            }))
            sys.exit(1)

        src_hash = hashlib.sha256(snap_src.read_bytes()).hexdigest().lower()
        test_hash = hashlib.sha256(snap_test.read_bytes()).hexdigest().lower()

        if expected_source_sha and src_hash != expected_source_sha:
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": f"Snapshot nguồn sai lệch SHA: {src_hash} != {expected_source_sha}",
            }))
            sys.exit(1)

        if expected_test_sha and test_hash != expected_test_sha:
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": f"Snapshot test sai lệch SHA: {test_hash} != {expected_test_sha}",
            }))
            sys.exit(1)

        canary_log_path = temp_clone_dir / ".aura_child_canary.jsonl"
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "TEMP": str(temp_clone_dir),
            "TMP": str(temp_clone_dir),
            "PYTHONPATH": str(temp_clone_dir),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "AURA_CHILD_CANARY_LOG": str(canary_log_path),
            "AURA_CHILD_CANARY": "1",
        }

        # 6. Preflight: kiểm tra collection trên temp clone với clean_env
        pre_proc = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-m", "pytest", "tests", "-m", "not e1_control", "--collect-only", "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(temp_clone_dir),
            env=clean_env,
            timeout=20.0,
        )
        if pre_proc.returncode != 0:
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": f"Preflight pytest collection trên clone thất bại: {pre_proc.stderr[-500:]}",
            }))
            sys.exit(1)

        # 7. Chạy worker bên trong clone
        worker_script = temp_clone_dir / "tools" / "_worker_e1_exec.py"
        if not worker_script.is_file():
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": "Không tìm thấy tools/_worker_e1_exec.py trong clone",
            }))
            sys.exit(1)

        t0 = time.monotonic()
        w_proc = subprocess.Popen(
            [
                sys.executable, "-B", "-X", "utf8", str(worker_script),
                tep_nguon_rel, tep_test_rel, expected_source_sha, expected_test_sha
            ],
            cwd=str(temp_clone_dir),
            env=clean_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        try:
            w_out, w_err = w_proc.communicate(timeout=deadline_s)
            if w_proc.returncode != 0:
                print(json.dumps({
                    "trang_thai": "khong_do_duoc",
                    "reason": f"Worker exit {w_proc.returncode}: {w_err[-500:]}",
                }))
            else:
                # Bổ sung thông tin canary log nếu có
                try:
                    res_dict = json.loads(w_out)
                    if canary_log_path.is_file():
                        records = []
                        for line in canary_log_path.read_text(encoding="utf-8").splitlines():
                            if line.strip():
                                try:
                                    records.append(json.loads(line))
                                except Exception:
                                    pass
                        res_dict["child_canary_records"] = len(records)
                        res_dict["child_canary_violations"] = sum(1 for r in records if r.get("blocked"))
                    sys.stdout.write(json.dumps(res_dict, ensure_ascii=False, indent=2))
                    sys.stdout.flush()
                except Exception:
                    sys.stdout.write(w_out)
                    sys.stdout.flush()
        except subprocess.TimeoutExpired:
            w_proc.kill()
            w_proc.wait(timeout=5.0)
            print(json.dumps({
                "trang_thai": "khong_do_duoc",
                "reason": f"Worker vượt trần thời gian deadline {deadline_s}s",
                "timeout_triggered": True,
            }))
    finally:
        shutil.rmtree(temp_clone_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
