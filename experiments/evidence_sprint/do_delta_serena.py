# -*- coding: utf-8 -*-
"""M2 — đo lại 15 đề, GIỮ NGUYÊN model, chỉ đổi giàn giáo: cho model CÔNG CỤ.

M0 (một lần bắn) ra 0/34. Nhưng ở M0 model bị BỊT MẮT: chỉ thấy một vùng đã cắt
của một tệp, không đọc được tệp khác, không tự chạy được test. Nên cái 0 đó
chứng minh "không vá mù được mã lạ", chưa chứng minh "không sửa được lỗi".

Ở đây model được đi theo KÝ HIỆU qua language server của serena — tìm hàm, xem
thân hàm, thay đúng hàm — thay vì đọc cả tệp. Đúng chỗ M0 hỏng: tệp trung vị
15.143 ký tự bị em cắt còn ~3.500 token rồi cầu cho chỗ hỏng nằm trong đó.

BA CHỖ CHỐNG ĂN GIAN, giữ nguyên như do_delta.py:
  1. Công cụ ghi CHỈ ghi được vào tệp nguồn của đề. Model đòi ghi tệp khác
     (nhất là tệp test) thì bị từ chối và bị ghi vào sổ.
  2. KHÔNG cấp execute_shell_command. Serena có tool đó; cấp là mở cửa cho
     model sửa test, xoá test, hoặc làm bất cứ gì. `chay_test` chỉ chạy đúng
     tệp test của đề.
  3. Chấm bằng ba cửa cũ, trên bản clone riêng từng đề.

ĐÃ ĐO 17/08 và phải nhớ khi đọc kết quả: qwen2.5-coder:7b CHỌN ĐÚNG công cụ và
đúng tham số, nhưng viết ra dưới dạng văn bản thường thay vì bọc thẻ giao thức,
nên Ollama trả `tool_calls` rỗng. Giàn giáo này tự đọc JSON trong nội dung —
cùng loại với gỡ rào markdown ở M0. Số lần phải đọc hộ được ĐẾM RIÊNG và in ra;
không in là báo cáo một năng lực model không có.

    .venv_serena\\Scripts\\python.exe experiments\\evidence_sprint\\do_delta_serena.py
"""
from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MODEL = "qwen2.5-coder:7b"
HAT = 17082026
SO_DE = 15
TRAN_BUOC = 4          # 252s/bước đo được -> 4 bước ~17 phút/đề, 15 đề ~4,3 giờ
DE = Path("D:/alpha_bench/de_sach.json")
RA = Path("D:/alpha_bench/ket_qua_serena.json")

CONG_CU = [
    {"type": "function", "function": {
        "name": "xem_ky_hieu",
        "description": "Liệt kê các hàm/lớp cấp cao nhất trong một tệp mã nguồn.",
        "parameters": {"type": "object", "properties": {
            "duong_dan": {"type": "string", "description": "đường dẫn tệp"}},
            "required": ["duong_dan"]}}},
    {"type": "function", "function": {
        "name": "doc_ham",
        "description": "Đọc TOÀN VĂN một hàm hoặc lớp theo tên.",
        "parameters": {"type": "object", "properties": {
            "ten": {"type": "string", "description": "tên hàm/lớp, ví dụ 'loc_menh_lenh' hoặc 'Lop/phuong_thuc'"},
            "duong_dan": {"type": "string", "description": "đường dẫn tệp"}},
            "required": ["ten", "duong_dan"]}}},
    {"type": "function", "function": {
        "name": "thay_ham",
        "description": "Thay toàn văn một hàm/lớp bằng mã mới. Chỉ ghi được vào tệp mã nguồn của đề.",
        "parameters": {"type": "object", "properties": {
            "ten": {"type": "string"}, "duong_dan": {"type": "string"},
            "than": {"type": "string", "description": "mã mới, gồm cả dòng def"}},
            "required": ["ten", "duong_dan", "than"]}}},
    {"type": "function", "function": {
        "name": "chay_test",
        "description": "Chạy test của đề và trả về nguyên văn kết quả pytest.",
        "parameters": {"type": "object", "properties": {}}}},
]

_JSON = re.compile(r"\{[^{}]*\"name\"\s*:\s*\"(\w+)\"[^{}]*\"arguments\"\s*:\s*(\{.*?\})\s*\}", re.S)


def doc_goi_tu_van_ban(noi_dung: str) -> list[dict]:
    """Model chọn đúng công cụ nhưng không bọc thẻ giao thức — đọc hộ JSON.

    KHÔNG phải nới cửa: ta chỉ đọc thứ model đã tự viết ra, không tự chọn công
    cụ hộ nó. Nhưng mỗi lần dùng đường này đều bị ĐẾM, vì "model gọi được công
    cụ" và "model gần gọi được, giàn giáo đọc hộ" là hai năng lực khác nhau.
    """
    ra = []
    for m in _JSON.finditer(noi_dung or ""):
        try:
            ra.append({"name": m.group(1), "arguments": json.loads(m.group(2))})
        except json.JSONDecodeError:
            pass
    return ra


def hoi(msg: list[dict]) -> tuple[float, dict]:
    b = json.dumps({"model": MODEL, "messages": msg, "tools": CONG_CU,
                    "stream": False, "think": False, "keep_alive": "15m",
                    "options": {"seed": 42, "temperature": 0.2,
                                "num_predict": 700, "num_ctx": 16384}}).encode()
    r = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=b,
                               headers={"Content-Type": "application/json"},
                               method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(r, timeout=1200) as x:
        k = json.loads(x.read().decode())
    return time.monotonic() - t0, (k.get("message") or {})


def mot_de(d: dict, so: dict) -> dict:
    from serena.agent import SerenaAgent                       # noqa: PLC0415
    from serena.tools.symbol_tools import (                    # noqa: PLC0415
        FindSymbolTool, GetSymbolsOverviewTool, ReplaceSymbolBodyTool)

    import do_delta as D                                       # noqa: PLC0415

    repo = Path(d["repo"])
    py = str(repo / "venv" / "Scripts" / "python.exe")
    goc = Path(tempfile.mkdtemp())
    tam = goc / "de"
    dem_doc_ho = 0
    try:
        subprocess.run(["git", "clone", "-q", str(repo), str(tam)], check=True, timeout=300)
        for a in (["checkout", "-q", d["sha"]],
                  ["checkout", "-q", f"{d['sha']}~1", "--", d["nguon"]]):
            subprocess.run(["git", "-C", str(tam), *a], capture_output=True, timeout=120)

        t_ls = time.monotonic()
        agent = SerenaAgent(project=str(tam))
        giay_ls = time.monotonic() - t_ls        # language server tốn bao lâu: phải biết
        t_xem = agent.get_tool(GetSymbolsOverviewTool)
        t_doc = agent.get_tool(FindSymbolTool)
        t_thay = agent.get_tool(ReplaceSymbolBodyTool)

        def chay(muc: list[str], tran: int = 300):
            return D.pytest_(py, tam, muc, tran)

        def lam(ten: str, arg: dict) -> str:
            try:
                if ten == "xem_ky_hieu":
                    return t_xem.apply(arg.get("duong_dan") or d["nguon"])[:2500]
                if ten == "doc_ham":
                    return t_doc.apply(arg.get("ten", ""),
                                       relative_path=arg.get("duong_dan") or d["nguon"],
                                       include_body=True)[:4000]
                if ten == "thay_ham":
                    dd = (arg.get("duong_dan") or "").replace("\\", "/")
                    # CỬA CHỐNG GIAN: chỉ tệp nguồn của đề. Model đòi ghi tệp
                    # test là cách gian dễ nhất và cũng là cách rõ nhất.
                    if dd != d["nguon"]:
                        return (f"TỪ CHỐI: chỉ được sửa {d['nguon']}, "
                                f"không được sửa {dd or '(trống)'}.")
                    return t_thay.apply(arg.get("ten", ""), d["nguon"], arg.get("than", ""))[:1200]
                if ten == "chay_test":
                    _, bao, _ = chay(d["test"])
                    return bao[-2000:]
                return f"Không có công cụ tên {ten}."
            except Exception as e:                             # noqa: BLE001
                return f"LỖI công cụ: {type(e).__name__}: {str(e)[:200]}"

        _, loi, _ = chay(d["test"])
        msg = [
            {"role": "system", "content":
             "Bạn sửa lỗi Python. Dùng công cụ để TÌM HIỂU trước, rồi mới sửa. "
             f"Chỉ được sửa tệp {d['nguon']}. KHÔNG được sửa tệp test. "
             "Sửa xong thì gọi chay_test để tự kiểm."},
            {"role": "user", "content":
             f"Test {', '.join(d['test'])} đang ĐỎ. Chỉ sửa {d['nguon']} cho test xanh.\n\n"
             f"=== PYTEST BÁO LỖI ===\n{loi[-2000:]}"},
        ]

        tong = 0.0
        for buoc in range(1, TRAN_BUOC + 1):
            giay, m = hoi(msg)
            tong += giay
            goi = m.get("tool_calls") or []
            if goi:
                goi = [{"name": c["function"]["name"],
                        "arguments": c["function"].get("arguments") or {}} for c in goi]
            else:
                goi = doc_goi_tu_van_ban(m.get("content") or "")
                if goi:
                    dem_doc_ho += 1
            msg.append({"role": "assistant", "content": m.get("content") or ""})
            if not goi:
                msg.append({"role": "user", "content":
                            "Hãy GỌI CÔNG CỤ, đừng viết lời giải thích."})
                continue
            for g in goi:
                kq = lam(g["name"], g.get("arguments") or {})
                msg.append({"role": "tool", "content": kq[:2500]})

        # Chấm bằng ĐÚNG ba cửa cũ, không tin lời model tự báo
        nen = set(d.get("do_nen") or ())
        try:
            m2, _, _ = chay(d["test"])
            them = (chay(["tests"], 200)[2] - nen) if m2 == 0 else set()
        except subprocess.TimeoutExpired:
            return {"trang_thai": "khong_do_duoc", "vi_sao": "test treo",
                    "giay": round(tong, 1)}
        return {"trang_thai": "dat" if (m2 == 0 and not them) else "truot",
                "giay": round(tong, 1), "giay_language_server": round(giay_ls, 1),
                "lan_phai_doc_ho": dem_doc_ho, "lam_do_them": sorted(them)[:4]}
    except Exception as e:                                     # noqa: BLE001
        return {"trang_thai": "khong_do_duoc",
                "vi_sao": f"{type(e).__name__}: {str(e)[:110]}"}
    finally:
        shutil.rmtree(goc, ignore_errors=True)


def main() -> int:
    de = json.loads(DE.read_text(encoding="utf-8"))
    chon = random.Random(HAT).sample(de, min(SO_DE, len(de)))
    so = json.loads(RA.read_text(encoding="utf-8")) if RA.exists() else {}
    print(f"  hạt {HAT} · {len(chon)}/{len(de)} đề · {MODEL} · trần {TRAN_BUOC} bước\n")

    dat = truot = bo = doc_ho = 0
    for i, d in enumerate(chon, start=1):
        khoa = f"{d['sha'][:8]}:{d['nguon']}"
        r = so.get(khoa)
        if r and r.get("trang_thai") == "khong_do_duoc":
            r = None                    # lỗi giàn giáo không được đóng băng thành số liệu
        r = r or mot_de(d, so)
        so[khoa] = r
        RA.write_text(json.dumps({"hat": HAT, **so}, ensure_ascii=False, indent=2),
                      encoding="utf-8")
        t = r["trang_thai"]
        dat += t == "dat"; truot += t == "truot"; bo += t == "khong_do_duoc"
        doc_ho += r.get("lan_phai_doc_ho", 0)
        dau = {"dat": "✓", "truot": "✗", "khong_do_duoc": "·"}[t]
        print(f"  {dau} [{i:>2}/{len(chon)}] {d['sha'][:8]} {d['nguon'][:30]:<30}"
              f"{r.get('giay', 0):>7.1f}s  {r.get('vi_sao', '')}")

    print(f"\n  ĐẠT {dat}/{dat + truot} đo được  ·  {bo} không đo được")
    print(f"  giàn giáo phải đọc hộ lời gọi công cụ: {doc_ho} lần "
          f"(model chọn đúng nhưng sai khuôn giao thức)")
    print(f"  -> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
