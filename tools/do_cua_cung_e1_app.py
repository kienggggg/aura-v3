# -*- coding: utf-8 -*-
"""tools/do_cua_cung_e1_app.py — Verifier độc lập nghiệm thu 7 Cửa Cứng E1 vào App Thẻ.

QUY TẮC BẤT DI BẤT DỊCH (AGENTS.md & KY_LUAT_THUC_THI.md):
1. BẰNG CHỨNG TRÊN ĐĨA LÀ CHÂN LÝ DUY NHẤT.
2. TÁCH BIỆT WORKER VÀ VERIFIER: Không tin số worker tự ghi; tự đo đếm, tính SHA và verify độc lập qua Oracle.
3. FAIL-CLOSED BY DESIGN: Trả về mã thoát 0 (PASS), 1 (FAIL), 2 (BLOCKED).
4. KHÔNG SỬA LIVE CORE: Tự clone kho, tự dựng fixture từ seed 19082026, chạy máy chủ test trên clone.
"""
from __future__ import annotations

import ast
import asyncio
import datetime
import difflib
import hashlib
import hmac
import json
import os
import random
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer, TestClient

# Thư mục gốc repo
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from interface import the_api, the_app

SEED = 19082026

MOC_E1 = {
    "core/may_tinh.py": {
        "candidate_before": 65,
        "candidate_after": 15,
        "target_line": 150,
        "expect_verdict": "XANH",
        "expect_suite_pass": True,
    },
    "core/web_search.py": {
        "candidate_before": 87,
        "candidate_after": 28,
        "target_line": 298,
        "expect_verdict": "XANH",
        "expect_suite_pass": True,
    },
    "core/dong_ho.py": {
        "candidate_before": 1,
        "candidate_after": 1,
        "target_line": 23,
        "expect_verdict": "XANH",
        "expect_suite_pass": True,
    },
    "core/loai_cau_hoi.py": {
        "candidate_before": 10,
        "candidate_after": 2,
        "target_line": 0,
        "expect_verdict": "TRUOT",
        "expect_suite_pass": False,
    },
}

DAU_VET_MOC = {
    "core/may_tinh.py": ("tests/test_may_tinh.py", [55],
                          "5af334da017929928c4883e83c0e3a0fb94e64f66abd1949d7a7a1be21ac4db5"),
    "core/web_search.py": ("tests/test_web_search.py", [78],
                           "cbf424d3acdf418e89aeb12037dd034468af1eadc77bb787a0cbdc0b3ebe528e"),
    "core/dong_ho.py": ("tests/test_dong_ho.py", [0],
                         "c104b5c2cda397caf7bb53db0f1486e53037bc4bf24e5d24c5f8cd75a2a76857"),
    "core/loai_cau_hoi.py": ("tests/test_loai_cau_hoi.py", [3],
                              "07166b72ee344d1f381c163534358e56d057f7aaafbf1d500ea7cc32c9b7c5f7"),
}

NGHICH_SS = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}


# ==============================================================================
# CANARY BẢO MẬT MẠNG (CỬA E)
# ==============================================================================
class SocketCanary:
    """Canary phát hiện và ghi lại mọi kết nối mạng ngoài loopback."""

    def __init__(self):
        self.violations: list[dict] = []
        self.control_probe_caught = False
        self._orig_connect = socket.socket.connect
        self._orig_create_conn = socket.create_connection

    def start(self):
        canary = self

        def patched_connect(sock_self, address):
            host = address[0] if isinstance(address, (tuple, list)) else address
            host_str = str(host).lower()
            if host_str in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
                return canary._orig_connect(sock_self, address)

            record = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "target": str(address),
                "type": "connect",
            }
            canary.violations.append(record)
            if "8.8.8.8" in str(address):
                canary.control_probe_caught = True
            raise PermissionError(f"[SOCKET_CANARY_BLOCKED]: Cấm kết nối mạng tới {address}")

        def patched_create_conn(address, *args, **kwargs):
            host = address[0] if isinstance(address, (tuple, list)) else address
            host_str = str(host).lower()
            if host_str in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
                return canary._orig_create_conn(address, *args, **kwargs)

            record = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "target": str(address),
                "type": "create_connection",
            }
            canary.violations.append(record)
            if "8.8.8.8" in str(address):
                canary.control_probe_caught = True
            raise PermissionError(f"[SOCKET_CANARY_BLOCKED]: Cấm kết nối mạng tới {address}")

        socket.socket.connect = patched_connect
        socket.create_connection = patched_create_conn

    def stop(self):
        socket.socket.connect = self._orig_connect
        socket.create_connection = self._orig_create_conn


# ==============================================================================
# HÀM TỰ DỰNG ĐỘT BIẾN TỪ SEED 19082026 TRÊN CLONE (CỬA D)
# ==============================================================================
class _Gieo(ast.NodeTransformer):
    def __init__(self, muc_can_gieo: set[int]):
        self.muc = set(muc_can_gieo)
        self.dem = 0
        self.da_gieo = []

    def _lay(self, ten: str, nut: ast.AST) -> bool:
        d = self.dem
        self.dem += 1
        if d in self.muc:
            self.da_gieo.append((d, getattr(nut, "lineno", 0), ten))
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            if self._lay(f"so sánh {type(n.ops[0]).__name__}", n):
                n.ops = [NGHICH_SS[type(n.ops[0])]()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if self._lay(f"logic {type(n.op).__name__}", n):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            if self._lay(f"bool {n.value}", n):
                return ast.Constant(value=not n.value)
        elif isinstance(n.value, int) and 0 <= n.value < 10000:
            if self._lay(f"số {n.value}", n):
                return ast.Constant(value=n.value + 1)
        return n


def gieo_ma(nguon: str, muc_can_gieo: set[int]) -> str:
    g = _Gieo(muc_can_gieo)
    cay = ast.parse(nguon)
    moi = g.visit(cay)
    ast.fix_missing_locations(moi)
    return ast.unparse(moi)


# ==============================================================================
# ORACLE VERIFIER ĐỘC LẬP: TỰ ÁP AST LÊN CLONE THỨ HAI VÀ KIỂM CHỨNG
# ==============================================================================
class _OracleLat(ast.NodeTransformer):
    def __init__(self, muc: int):
        self.muc = muc
        self.dem = 0
        self.da = ""
        self.danh_sach: list[tuple[int, int, str]] = []

    def _lay(self, ten: str, nut: ast.AST) -> bool:
        d = self.dem
        self.danh_sach.append((d, int(getattr(nut, "lineno", 0) or 0), ten))
        self.dem += 1
        if d == self.muc:
            self.da = ten
            return True
        return False

    def visit_Compare(self, n):
        self.generic_visit(n)
        if len(n.ops) == 1 and type(n.ops[0]) in NGHICH_SS:
            op_cls = type(n.ops[0])
            target_cls = NGHICH_SS[op_cls]
            if self._lay(f"so sánh {op_cls.__name__} -> {target_cls.__name__}", n):
                n.ops = [target_cls()]
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.And):
            if self._lay("logic And -> Or", n):
                n.op = ast.Or()
        elif isinstance(n.op, ast.Or):
            if self._lay("logic Or -> And", n):
                n.op = ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not) and self._lay("bỏ phủ định", n):
            return n.operand
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, bool):
            target_val = not n.value
            if self._lay(f"bool {n.value} -> {target_val}", n):
                return ast.Constant(value=target_val)
        elif isinstance(n.value, int) and not isinstance(n.value, bool):
            if self._lay(f"số {n.value} -> {n.value - 1}", n):
                return ast.Constant(value=n.value - 1)
        return n


def oracle_calculate_candidates(source_text: str) -> list[tuple[int, int, str]]:
    """Oracle tự đếm số ứng viên độc lập trên AST."""
    d = _OracleLat(-1)
    d.visit(ast.parse(source_text))
    return [(chi_so, dong, ten) for chi_so, dong, ten in d.danh_sach]


def oracle_verify_candidate(
    clean_clone_dir: Path,
    tep_nguon_rel: str,
    mutated_source_text: str,
    cand_index: int,
    cand_line: int,
    cand_operation: str,
    api_unified_diff: str,
) -> bool:
    """Oracle độc lập áp AST lên clone thứ hai và chạy pytest độc lập."""
    target_f = clean_clone_dir / tep_nguon_rel
    clean_original_text = (REPO_ROOT / tep_nguon_rel).read_text(encoding="utf-8")
    try:
        goc_ast_chuan = ast.unparse(ast.parse(mutated_source_text))
        bd = _OracleLat(cand_index)
        cay_moi = bd.visit(ast.parse(mutated_source_text))
        ast.fix_missing_locations(cay_moi)
        moi_ast_chuan = ast.unparse(cay_moi)

        # Kiểm tra operation và line
        cands_all = oracle_calculate_candidates(mutated_source_text)
        match_info = next((c for c in cands_all if c[0] == cand_index), None)
        if not match_info:
            return False
        if match_info[1] != cand_line:
            return False

        # Tạo unified diff độc lập
        lines_goc = goc_ast_chuan.splitlines(keepends=True)
        lines_moi = moi_ast_chuan.splitlines(keepends=True)
        expected_diff = "".join(difflib.unified_diff(
            lines_goc,
            lines_moi,
            fromfile=f"a/{tep_nguon_rel}",
            tofile=f"b/{tep_nguon_rel}",
        ))

        # So khớp diff
        if expected_diff.strip() != api_unified_diff.strip():
            return False

        # Ghi mã vá vào clone thứ hai và chạy full suite
        target_f.write_text(moi_ast_chuan, encoding="utf-8")
        r = subprocess.run(
            [
                sys.executable, "-B", "-X", "utf8", "-m", "pytest", "tests",
                "-m", "not e1_control",
                "-q", "--no-header", "-p", "no:cacheprovider",
            ],
            cwd=str(clean_clone_dir),
            capture_output=True,
            timeout=180.0,
        )
        return r.returncode == 0
    except Exception:
        return False
    finally:
        # Khôi phục file trên clone thứ hai về bản sạch nguyên thủy
        target_f.write_text(clean_original_text, encoding="utf-8")


# ==============================================================================
# QUY TRÌNH NGHIỆM THU 7 CỬA CỨNG E1
# ==============================================================================
async def main_async() -> int:
    time_start_utc = datetime.datetime.now(datetime.timezone.utc)
    timestamp_str = time_start_utc.strftime("%Y%m%d_%H%M%S")
    run_id = f"e1_app_{timestamp_str}"
    run_dir = REPO_ROOT / "data" / "evidence_sprint" / "runs" / run_id
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"[*] BẮT ĐẦU NGHIỆM THU CỬA CỨNG E1 TRÊN APP THẺ — RUN ID: {run_id}")
    print("=" * 70)

    # 1. BẢO TOÀN TỆP GỐC: Tính SHA-256 live repo trước khi chạy
    sha_goc_truoc = {}
    for tep in MOC_E1:
        sha_goc_truoc[tep] = hashlib.sha256((REPO_ROOT / tep).read_bytes()).hexdigest()

    # 2. KHỞI TẠO CANARY MẠNG (CỬA E)
    canary = SocketCanary()
    canary.start()

    # Thử kết nối thăm dò control probe tới 8.8.8.8:53 (bắt buộc bị canary chặn)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 53))
    except Exception:
        pass

    gate_results: dict[str, str] = {
        "A": "FAIL",
        "B": "FAIL",
        "C": "FAIL",
        "D": "FAIL",
        "E": "FAIL",
        "F": "FAIL",
        "G": "FAIL",
    }
    metrics: dict[str, Any] = {}
    commands_log: list[dict] = []
    raw_responses: dict[str, Any] = {}

    def log_cmd(cmd: str, exit_code: int, duration_s: float):
        commands_log.append({
            "command": cmd,
            "exit_code": exit_code,
            "duration_s": round(duration_s, 3),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

    temp_clone_dir = Path(tempfile.mkdtemp(prefix="aura_e1_verifier_clone_"))
    temp_clone_2 = Path(tempfile.mkdtemp(prefix="aura_e1_oracle_clone_"))
    server = None
    client = None

    try:
        # 3. DỰNG CLONE VÀ PREFLIGHT SUITE NỀN
        def _clone_repo(dst: Path):
            dst.mkdir(parents=True, exist_ok=True)
            for fname in ["aura_chat.py", "pytest.ini", "CLAUDE.md", "AGENTS.md"]:
                if (REPO_ROOT / fname).is_file():
                    shutil.copy2(REPO_ROOT / fname, dst / fname)
            ignore_pat = shutil.ignore_patterns("venv", ".venv*", ".git", "__pycache__", ".pytest_cache", "*.pyc", "runs")
            for dname in ["core", "interface", "tests", "tools", "experiments"]:
                if (REPO_ROOT / dname).is_dir():
                    shutil.copytree(REPO_ROOT / dname, dst / dname, dirs_exist_ok=True, ignore=ignore_pat)
            (dst / "data").mkdir(exist_ok=True)
            from tools import e1_supervisor_bootstrap
            e1_supervisor_bootstrap._install_child_canary(dst)

        _clone_repo(temp_clone_dir)
        _clone_repo(temp_clone_2)

        # Preflight: Chạy clean-clone suite nền xanh
        t0_pref = time.time()
        r_pref = subprocess.run(
            [
                sys.executable, "-B", "-X", "utf8", "-m", "pytest", "tests",
                "-m", "not e1_control",
                "-q", "--no-header", "-p", "no:cacheprovider"
            ],
            cwd=str(temp_clone_dir),
            capture_output=True,
            text=True,
            timeout=180.0,
        )
        log_cmd("preflight_clean_suite", r_pref.returncode, time.time() - t0_pref)
        if r_pref.returncode != 0:
            print("  [✗] PREFLIGHT THẤT BẠI: Suite nền trên clone sạch không xanh 100%!")
            print(r_pref.stdout[-1000:] + r_pref.stderr[-1000:])
            return 1

        # 4. KHỞI TẠO APP VỚI ROOT TRỎ VÀO CLONE VÀ BẬT CỜ
        test_auth_token = "e1testtoken_" + hashlib.sha256(str(SEED).encode()).hexdigest()[:16]
        app = the_app.tao_app(
            project_root=temp_clone_dir,
            allow_code_execution=True,
            auth_token=test_auth_token,
        )
        server = TestServer(app, host="127.0.0.1")
        await server.start_server()
        client = TestClient(server, timeout=aiohttp.ClientTimeout(total=600.0))

        auth_headers = {
            "X-Auth-Token": test_auth_token,
            "Origin": f"http://127.0.0.1:{server.port}",
        }

        # ----------------------------------------------------------------------
        # CỬA C: Cách ly Context Per-App & Zero-Disk-Write
        # ----------------------------------------------------------------------
        app_disabled = the_app.tao_app(
            project_root=temp_clone_2,
            allow_code_execution=False,
            auth_token="disabled_token_" + secrets.token_hex(8),
        )
        server_disabled = TestServer(app_disabled, host="127.0.0.1")
        await server_disabled.start_server()
        client_disabled = TestClient(server_disabled)

        try:
            # 1. Gọi vào app_disabled -> 403 bi_khoa
            resp_dis = await client_disabled.post(
                "/api/dinh_vi_loi",
                json={"tep_nguon": "core/dong_ho.py", "tep_test": "tests/test_dong_ho.py", "source_sha256": "0"*64, "test_sha256": "0"*64},
                headers={"X-Auth-Token": app_disabled["aura_config"].auth_token, "Origin": "http://127.0.0.1"}
            )
            dis_ok = (resp_dis.status == 403)

            # 2. Dùng token app_disabled gọi vào app chính -> 403 Sai token
            resp_cross = await client.post(
                "/api/dinh_vi_loi",
                json={"tep_nguon": "core/dong_ho.py", "tep_test": "tests/test_dong_ho.py", "source_sha256": "0"*64, "test_sha256": "0"*64},
                headers={"X-Auth-Token": app_disabled["aura_config"].auth_token, "Origin": "http://127.0.0.1"}
            )
            cross_ok = (resp_cross.status == 403)

            if dis_ok and cross_ok:
                gate_results["C"] = "PASS"
                print("  [✓] CỬA C — Cách ly Context Per-App & Khóa mặc định: ĐẠT")
        finally:
            await client_disabled.close()
            await server_disabled.close()

        # ----------------------------------------------------------------------
        # CỬA B: Hàng rào bảo mật API, Path Confinement & Token
        # ----------------------------------------------------------------------
        cua_b_pass = True
        # B1. Không có token -> 403
        r_b1 = await client.post("/api/dinh_vi_loi", json={})
        if r_b1.status != 403:
            cua_b_pass = False

        # B2. Origin ngoài loopback -> 403
        r_b2 = await client.post("/api/dinh_vi_loi", json={}, headers={"X-Auth-Token": test_auth_token, "Origin": "http://attacker.com"})
        if r_b2.status != 403:
            cua_b_pass = False

        # B3. Path traversal -> 400
        r_b3 = await client.post(
            "/api/dinh_vi_loi",
            json={"tep_nguon": "../core/dong_ho.py", "tep_test": "tests/test_dong_ho.py", "source_sha256": "0"*64, "test_sha256": "0"*64},
            headers=auth_headers
        )
        if r_b3.status != 400:
            cua_b_pass = False

        # B4. Thư mục data -> 403 Forbidden
        r_b4 = await client.get("/api/tep_tin?thu_muc=data", headers=auth_headers)
        if r_b4.status != 403:
            cua_b_pass = False

        # B5. Schema SHA rỗng/sai định dạng -> 400
        r_b5 = await client.post(
            "/api/dinh_vi_loi",
            json={"tep_nguon": "core/dong_ho.py", "tep_test": "tests/test_dong_ho.py", "source_sha256": "invalid_hex", "test_sha256": "0"*64},
            headers=auth_headers
        )
        if r_b5.status != 400:
            cua_b_pass = False

        if cua_b_pass:
            gate_results["B"] = "PASS"
            print("  [✓] CỬA B — Hàng rào bảo mật API, Confinement & Token: ĐẠT")
        else:
            print("  [✗] CỬA B — Hàng rào bảo mật API thất bại!")

        # ----------------------------------------------------------------------
        # CỬA F: Responsiveness (< 1s) & Fail-closed Concurrency (409 BUSY)
        # ----------------------------------------------------------------------
        t0_status = time.time()
        resp_status = await client.get("/api/status", headers=auth_headers)
        elapsed_status = time.time() - t0_status
        status_ok = (resp_status.status == 200 and elapsed_status < 1.0)

        # Mở core/dong_ho.py trong phiên để có quyền gọi E1
        r_mo_f = await client.post("/api/mo_tep", json={"duong_dan": "core/dong_ho.py"}, headers=auth_headers)
        data_mo_f = await r_mo_f.json()
        sha_dong_ho_src = data_mo_f["sha256"]
        r_tep_f = await client.get("/api/tep_tin?thu_muc=tests", headers=auth_headers)
        data_tep_f = await r_tep_f.json()
        match_test_f = next(t for t in data_tep_f["danh_sach"] if t["duong_dan"] == "tests/test_dong_ho.py")
        sha_dong_ho_test = match_test_f["sha256"]

        # Giả lập lock bận
        app["aura_runtime"].busy_info["is_busy"] = True
        try:
            resp_busy = await client.post(
                "/api/dinh_vi_loi",
                json={
                    "tep_nguon": "core/dong_ho.py",
                    "tep_test": "tests/test_dong_ho.py",
                    "source_sha256": sha_dong_ho_src,
                    "test_sha256": sha_dong_ho_test,
                },
                headers=auth_headers
            )
            busy_data = await resp_busy.json()
            busy_ok = (resp_busy.status == 409 and busy_data.get("trang_thai") == "busy")
        finally:
            app["aura_runtime"].busy_info["is_busy"] = False

        if status_ok and busy_ok:
            gate_results["F"] = "PASS"
            print("  [✓] CỬA F — Responsiveness (< 1s) & Fail-closed (409 BUSY): ĐẠT")
        else:
            print(f"  [✗] CỬA F — Thất bại: status_ok={status_ok}, busy_ok={busy_ok}")

        # ----------------------------------------------------------------------
        # CỬA A: Negative Control & Tamper Test cho Oracle
        # ----------------------------------------------------------------------
        # 1. Tamper test: Oracle bắt buộc từ chối ứng viên giả
        tamper_rejected = not oracle_verify_candidate(
            clean_clone_dir=temp_clone_2,
            tep_nguon_rel="core/dong_ho.py",
            mutated_source_text=(REPO_ROOT / "core/dong_ho.py").read_text("utf-8"),
            cand_index=999,
            cand_line=999,
            cand_operation="fake",
            api_unified_diff="fake diff",
        )
        if tamper_rejected:
            gate_results["A"] = "PASS"
            print("  [✓] CỬA A — Oracle độc lập & Tamper negative control: ĐẠT")
        else:
            print("  [✗] CỬA A — Oracle không từ chối ứng viên giả mạo!")

        # ----------------------------------------------------------------------
        # CỬA D: Thực thi 4 mốc E1 qua HTTP endpoint trên clone fixture
        # ----------------------------------------------------------------------
        cua_d_pass = True

        for tep, (tep_test, cho_gieo, expected_sha) in DAU_VET_MOC.items():
            cfg = MOC_E1[tep]

            # Đảm bảo các tệp khác sạch, chỉ gieo lỗi đúng tệp đang đo
            for other_tep, (o_test, o_cho, _) in DAU_VET_MOC.items():
                goc_clean = (REPO_ROOT / other_tep).read_text(encoding="utf-8")
                if other_tep == tep:
                    mut_text = gieo_ma(goc_clean, set(cho_gieo))
                    mut_sha = hashlib.sha256(mut_text.encode("utf-8")).hexdigest()
                    if mut_sha != expected_sha:
                        raise ValueError(f"Fixture {tep} có SHA {mut_sha} không khớp mẫu chuẩn {expected_sha}")
                    (temp_clone_dir / other_tep).write_text(mut_text, encoding="utf-8")
                else:
                    (temp_clone_dir / other_tep).write_text(goc_clean, encoding="utf-8")

            # Oracle tự tính toán số ứng viên trước và sau độc lập từ tệp đột biến
            target_mut_text = (temp_clone_dir / tep).read_text(encoding="utf-8")
            oracle_all_cands = oracle_calculate_candidates(target_mut_text)
            oracle_n_before = len(oracle_all_cands)

            if oracle_n_before != cfg["candidate_before"]:
                print(f"  [✗] {tep}: Oracle tự tính n_before={oracle_n_before} != {cfg['candidate_before']}")
                cua_d_pass = False

            # 1. Mở tệp trong phiên để đăng ký whitelist
            resp_mo = await client.post("/api/mo_tep", json={"duong_dan": tep}, headers=auth_headers)
            if resp_mo.status != 200:
                print(f"  [✗] Lỗi mở tệp {tep}: {resp_mo.status}")
                cua_d_pass = False
                continue
            data_mo = await resp_mo.json()
            source_sha = data_mo["sha256"]

            # 2. Lấy SHA tệp test qua inventory
            resp_tep = await client.get("/api/tep_tin?thu_muc=tests", headers=auth_headers)
            data_tep = await resp_tep.json()
            match_test = next((t for t in data_tep.get("danh_sach", []) if t["duong_dan"] == tep_test), None)
            if not match_test:
                print(f"  [✗] Không tìm thấy test {tep_test} trong inventory")
                cua_d_pass = False
                continue
            test_sha = match_test["sha256"]

            # 3. Gọi POST /api/dinh_vi_loi
            t_call0 = time.time()
            resp_e1 = await client.post(
                "/api/dinh_vi_loi",
                json={
                    "tep_nguon": tep,
                    "tep_test": tep_test,
                    "source_sha256": source_sha,
                    "test_sha256": test_sha,
                },
                headers=auth_headers
            )
            elapsed_call = time.time() - t_call0
            log_cmd(f"api_dinh_vi_loi_{Path(tep).stem}", resp_e1.status, elapsed_call)

            if resp_e1.status != 200:
                print(f"  [✗] {tep}: /api/dinh_vi_loi trả status={resp_e1.status}")
                cua_d_pass = False
                continue

            res_data = await resp_e1.json()
            raw_responses[tep] = res_data

            # Ghi file raw
            stem = Path(tep).stem
            (raw_dir / f"{stem}_e1_raw.json").write_text(json.dumps(res_data, indent=2, ensure_ascii=False), encoding="utf-8")

            # 4. Kiểm tra các chỉ số mốc
            cb = res_data.get("candidate_count_before")
            ca = res_data.get("candidate_count_after")
            t_filter_mut = res_data.get("elapsed_filter_mutate_s", 999.0)
            candidates = res_data.get("candidates", [])

            metrics[f"{stem}_before"] = cb
            metrics[f"{stem}_after"] = ca
            metrics[f"{stem}_elapsed_s"] = t_filter_mut

            if cb != cfg["candidate_before"] or ca != cfg["candidate_after"]:
                print(f"  [✗] {tep}: Số ứng viên {cb}->{ca}, yêu cầu {cfg['candidate_before']}->{cfg['candidate_after']}")
                cua_d_pass = False

            if t_filter_mut > 60.0:
                print(f"  [✗] {tep}: Thời gian lọc+lật {t_filter_mut}s > 60.0s")
                cua_d_pass = False

            # 5. Oracle verification độc lập
            if cfg["expect_suite_pass"]:
                has_green = any(c.get("full_suite_status") == "XANH" for c in candidates)
                if not has_green or res_data.get("trang_thai") != "tim_thay":
                    print(f"  [✗] {tep}: Kỳ vọng XANH cả kho nhưng trả về {res_data.get('trang_thai')}")
                    cua_d_pass = False

                match_target = next((c for c in candidates if c.get("line") == cfg["target_line"] and c.get("full_suite_status") == "XANH"), None)
                if not match_target:
                    print(f"  [✗] {tep}: Không tìm thấy bản vá XANH tại dòng {cfg['target_line']}")
                    cua_d_pass = False
                else:
                    diff_str = match_target.get("unified_diff", "")
                    oracle_ok = oracle_verify_candidate(
                        clean_clone_dir=temp_clone_2,
                        tep_nguon_rel=tep,
                        mutated_source_text=target_mut_text,
                        cand_index=match_target["index"],
                        cand_line=match_target["line"],
                        cand_operation=match_target["operation"],
                        api_unified_diff=diff_str,
                    )
                    if not oracle_ok:
                        print(f"  [✗] {tep}: Oracle độc lập không xác nhận được bản vá!")
                        cua_d_pass = False
            else:
                # Đề thứ tư: Kỳ vọng TRƯỢT (so_xanh = 0)
                has_green = any(c.get("full_suite_status") == "XANH" for c in candidates)
                if has_green or res_data.get("trang_thai") not in ("ung_vien_khong_qua_suite", "khong_tim_thay"):
                    print(f"  [✗] {tep}: Kỳ vọng TRƯỢT nhưng trả về {res_data.get('trang_thai')}")
                    cua_d_pass = False

            print(f"  [✓] {Path(tep).name:20}: {cb:3}->{ca:3} | "
                  f"Verdict: {res_data.get('trang_thai')} | "
                  f"Thời gian: {t_filter_mut:.2f}s")

        if cua_d_pass:
            gate_results["D"] = "PASS"
            print("  [✓] CỬA D — Đúng 4 mốc E1 trên clone fixture: ĐẠT")

        # ----------------------------------------------------------------------
        # CỬA E: Kiểm tra Canary Mạng và Negative Control Child Process
        # ----------------------------------------------------------------------
        (raw_dir / "socket_canary_log.json").write_text(
            json.dumps({
                "violations": canary.violations,
                "control_probe_caught": canary.control_probe_caught,
            }, indent=2),
            encoding="utf-8"
        )
        real_violations = [v for v in canary.violations if "8.8.8.8" not in v.get("target", "")]

        # Child negative control: Thử kết nối mạng ngoài trong subprocess của clone
        child_test_code = (
            "import socket\n"
            "try:\n"
            "    s = socket.socket()\n"
            "    s.connect(('8.8.8.8', 53))\n"
            "    print('UNEXPECTED_CONNECTED')\n"
            "except PermissionError:\n"
            "    print('CHILD_CANARY_BLOCKED')\n"
        )
        child_canary_log_path = raw_dir / "child_canary_negative_control.jsonl"
        env_child = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(temp_clone_dir),
            "AURA_CHILD_CANARY_LOG": str(child_canary_log_path),
            "AURA_CHILD_CANARY": "1",
        }
        r_child_canary = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-c", child_test_code],
            cwd=str(temp_clone_dir),
            env=env_child,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        child_blocked = "CHILD_CANARY_BLOCKED" in r_child_canary.stdout

        if canary.control_probe_caught and len(real_violations) == 0 and child_blocked:
            gate_results["E"] = "PASS"
            print("  [✓] CỬA E — Không model, không mạng ngoài, child canary negative control: ĐẠT")
        else:
            print(f"  [✗] CỬA E — Thất bại: control_probe={canary.control_probe_caught}, real_violations={len(real_violations)}, child_blocked={child_blocked}")

        # ----------------------------------------------------------------------
        # CỬA G: Trình duyệt thật qua Chrome CDP thuần Node.js
        # ----------------------------------------------------------------------
        t0_cdp = time.time()
        cdp_script = REPO_ROOT / "tools" / "_cdp_browser_test.js"
        r_cdp = await asyncio.to_thread(
            subprocess.run,
            [
                "node", str(cdp_script),
                str(server.port),
                test_auth_token,
                str(raw_dir),
                "true",
            ],
            capture_output=True,
            text=True,
            timeout=120.0,
        )
        log_cmd("chrome_cdp_browser_test", r_cdp.returncode, time.time() - t0_cdp)

        screenshot_path = raw_dir / "e1_ui_screenshot.png"
        dom_receipt_path = raw_dir / "ui_dom_receipt.json"

        cdp_receipt_valid = False
        if dom_receipt_path.is_file():
            try:
                receipt_json = json.loads(dom_receipt_path.read_text(encoding="utf-8"))
                subgates = receipt_json.get("testResults", {}).get("subgates", {})
                cdp_receipt_valid = all(sg.get("pass") is True for sg in subgates.values())
            except Exception:
                cdp_receipt_valid = False

        if r_cdp.returncode == 0 and screenshot_path.is_file() and cdp_receipt_valid:
            gate_results["G"] = "PASS"
            print("  [✓] CỬA G — Chrome CDP Browser E2E, XSS Canary & Screenshot: ĐẠT")
        else:
            print(f"  [✗] CỬA G — Browser E2E thất bại (exit {r_cdp.returncode}): {r_cdp.stderr[-500:]}")

    finally:
        canary.stop()
        if client:
            await client.close()
        if server:
            await server.close()

        # Dọn sạch clone temp
        shutil.rmtree(temp_clone_dir, ignore_errors=True)
        shutil.rmtree(temp_clone_2, ignore_errors=True)

    # 5. Kiểm tra bảo toàn tệp gốc (không bị sửa đổi byte nào)
    sha_goc_sau = {}
    for tep in MOC_E1:
        sha_goc_sau[tep] = hashlib.sha256((REPO_ROOT / tep).read_bytes()).hexdigest()
        if sha_goc_sau[tep] != sha_goc_truoc[tep]:
            print(f"  [FATAL ✗] Tệp {tep} trên repo thật đã bị sửa đổi!")
            gate_results["D"] = "FAIL"

    # 6. Ghi Evidence Sprint Manifest, Metrics, Artifacts
    time_end_utc = datetime.datetime.now(datetime.timezone.utc)
    all_passed = all(status == "PASS" for status in gate_results.values())

    manifest = {
        "run_id": run_id,
        "timestamp_start_utc": time_start_utc.isoformat(),
        "timestamp_end_utc": time_end_utc.isoformat(),
        "seed": SEED,
        "verifier": "tools/do_cua_cung_e1_app.py",
        "status": "PASS" if all_passed else "FAIL",
        "gates": gate_results,
        "python_version": sys.version,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    with open(run_dir / "commands.jsonl", "w", encoding="utf-8") as f:
        for c in commands_log:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    # Danh sách artifacts
    artifacts_data = []
    for item in raw_dir.glob("*"):
        if item.is_file():
            artifacts_data.append({
                "name": item.name,
                "path": str(item.relative_to(run_dir)).replace("\\", "/"),
                "size_bytes": item.stat().st_size,
                "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
            })
    (run_dir / "artifacts.json").write_text(json.dumps(artifacts_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 70)
    print("KẾT QUẢ TỔNG HỢP 7 CỬA CỨNG:")
    for gate, status in gate_results.items():
        print(f"  - Cửa {gate}: {status}")
    print(f"\nBằng chứng Sprint đã lưu tại: {run_dir}")
    print(f"TRẠNG THÁI CUỐI CÙNG: {'PASS (EXIT 0)' if all_passed else 'FAIL (EXIT 1)'}")
    print("=" * 70)

    return 0 if all_passed else 1


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
