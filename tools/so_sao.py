# -*- coding: utf-8 -*-
"""Sổ chụp số sao GitHub hằng ngày — cho bảng "repo tăng sao nhiều nhất tuần" của Alpha.

Sếp duyệt 15/09/2026 (`docs/KE_HOACH_ALPHA_REVIEW_2026-09-15.md` mục 2b, việc 5). Đo cùng ngày:
GitHub KHÔNG trả "số sao tăng trong tuần"; API chỉ có số sao HIỆN TẠI. Muốn có hiệu tuần thì
phải tự chụp mỗi ngày rồi trừ — chụp từ hôm nay thì 7 ngày nữa mới có bảng đầu tiên.

    python tools/so_sao.py chup            # chụp hôm nay (đã có tệp đủ thì bỏ qua)
    python tools/so_sao.py bang [YYYY-MM-DD]   # bảng tăng sao 7 ngày tính tới ngày ấy

Ba nguồn mỗi ngày, gọi qua `gh api` (khoá nằm trong keyring của gh, không đi qua tệp nào):
1. danh sách theo dõi — `data/so_sao/theo_doi.txt`, mỗi dòng `chu/repo`;
2. repo tạo trong 30 ngày, ≥ 100 sao, xếp theo sao — bắt repo mới lên nhanh;
3. vài chủ đề AI, ≥ 500 sao, có đẩy mã trong 7 ngày.

Hiệu tuần chỉ tính cho repo có mặt ở CẢ hai ngày. Repo mới vào danh sách thì chưa có số tuần
trước — bảng ghi rõ số repo bị bỏ vì lý do ấy, không lặng lẽ bỏ.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
THU_MUC = GOC / "data" / "so_sao"
THEO_DOI = THU_MUC / "theo_doi.txt"
SO_LICH = THU_MUC / "lich.jsonl"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
CHU_DE = ("llm", "ai-agents", "mcp", "generative-ai", "text-to-speech", "rag")
TRANG_MOI_TIM = 3          # 3 trang × 100 = 300 kết quả mỗi truy vấn
NGHI_GIUA_TIM = 2.2        # hạn mức tìm kiếm có xác thực: 30 lượt/phút
MAC_DINH_THEO_DOI = (
    "charlie947/social-media-skills", "ashishps1/awesome-low-level-design", "zeroweight-ai/ZeroTTS",
    "hexgrad/kokoro", "luuquangvu/wyoming-vietnamese", "cytostack/openwolf", "JustVugg/colibri",
    "livekit/agents", "ItzCrazyKns/Vane", "ChromeDevTools/chrome-devtools-mcp", "lnkiai/m3e-canvas",
    "multimodal-art-projection/YuE", "tinyhumansai/openhuman", "tonhowtf/omniget", "pnnbao97/VieNeu-TTS",
    "om-ai-lab/VLX-Seek", "iamdinhthuan/Kokoro-Vietnamese",
)


def _gh(duong: str) -> dict | list:
    r = subprocess.run([GH, "api", duong], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {duong[:80]}: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)


def _dong(r: dict) -> dict:
    return {"repo": r["full_name"], "sao": r["stargazers_count"], "fork": r["forks_count"],
            "tao": (r.get("created_at") or "")[:10], "day": (r.get("pushed_at") or "")[:10],
            "gp": (r.get("license") or {}).get("spdx_id"), "ngon_ngu": r.get("language"),
            "mo_ta": (r.get("description") or "")[:140]}


def _tim(q: str, hom_nay: date) -> tuple[list[dict], dict]:
    ra, meta = [], {"q": q, "trang": 0, "tong": None, "thieu": False}
    for trang in range(1, TRANG_MOI_TIM + 1):
        time.sleep(NGHI_GIUA_TIM)
        d = _gh(f"search/repositories?q={q}&sort=stars&order=desc&per_page=100&page={trang}")
        meta["trang"], meta["tong"] = trang, d.get("total_count")
        meta["thieu"] = meta["thieu"] or bool(d.get("incomplete_results"))
        ra += [_dong(r) for r in d.get("items", [])]
        if len(d.get("items", [])) < 100:
            break
    return ra, meta


def _ghi_lich(**kv) -> None:
    THU_MUC.mkdir(parents=True, exist_ok=True)
    with SO_LICH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **kv}, ensure_ascii=False) + "\n")


def tep_ngay(ngay: date) -> Path:
    return THU_MUC / f"{ngay.isoformat()}.jsonl"


def doc_ngay(ngay: date) -> dict[str, dict]:
    """{repo: dòng} của một ngày; dòng đầu tệp là meta nên bỏ qua."""
    tep = tep_ngay(ngay)
    if not tep.exists():
        return {}
    ra = {}
    for x in tep.read_text(encoding="utf-8").splitlines():
        d = json.loads(x)
        if "repo" in d:
            ra[d["repo"].lower()] = d
    return ra


def chup(hom_nay: date | None = None) -> dict:
    hom_nay = hom_nay or date.today()
    tep = tep_ngay(hom_nay)
    t0 = time.monotonic()
    if tep.exists() and tep.read_text(encoding="utf-8").startswith('{"meta"'):
        kq = {"trang_thai": "DA_CO", "tep": tep.name}
        _ghi_lich(**kq)
        return kq
    try:
        THU_MUC.mkdir(parents=True, exist_ok=True)
        if not THEO_DOI.exists():
            THEO_DOI.write_text("\n".join(MAC_DINH_THEO_DOI) + "\n", encoding="utf-8")
        gop: dict[str, dict] = {}
        metas, loi_theo_doi = [], []
        for r in [x.strip() for x in THEO_DOI.read_text(encoding="utf-8").splitlines() if x.strip()]:
            try:
                d = _dong(_gh(f"repos/{r}"))
                gop[d["repo"].lower()] = {**d, "nguon": "theo_doi"}
            except RuntimeError as e:
                loi_theo_doi.append(f"{r}: {e}"[:160])
        truoc30 = (hom_nay - timedelta(days=30)).isoformat()
        truoc7 = (hom_nay - timedelta(days=7)).isoformat()
        cau = [(f"created:>={truoc30}+stars:>=100", "moi_30_ngay")]
        cau += [(f"topic:{c}+stars:>=500+pushed:>={truoc7}", f"chu_de:{c}") for c in CHU_DE]
        for q, nguon in cau:
            ds, meta = _tim(q, hom_nay)
            metas.append({**meta, "nguon": nguon, "lay": len(ds)})
            for d in ds:
                gop.setdefault(d["repo"].lower(), {**d, "nguon": nguon})
        tam = tep.with_suffix(".tam")
        with tam.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"meta": {"ngay": hom_nay.isoformat(), "so_repo": len(gop), "truy_van": metas,
                                         "loi_theo_doi": loi_theo_doi,
                                         "giay": round(time.monotonic() - t0, 1)}}, ensure_ascii=False) + "\n")
            for d in gop.values():
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        tam.replace(tep)  # ghi xong mới đổi tên: tệp dở dang không bao giờ mang tên ngày
        kq = {"trang_thai": "XONG", "tep": tep.name, "so_repo": len(gop), "loi_theo_doi": len(loi_theo_doi),
              "giay": round(time.monotonic() - t0, 1)}
    except Exception as e:  # noqa: BLE001 — lượt lỗi cũng phải có dòng trong sổ lịch
        kq = {"trang_thai": "LOI", "loi": str(e)[:300], "giay": round(time.monotonic() - t0, 1)}
    _ghi_lich(**kq)
    return kq


def bang(ngay: date, top: int = 10) -> dict:
    """Bảng tăng sao 7 ngày tính tới `ngay`. KHONG_DO_DUOC khi thiếu một trong hai tệp."""
    moi, cu = doc_ngay(ngay), doc_ngay(ngay - timedelta(days=7))
    if not moi or not cu:
        return {"trang_thai": "KHONG_DO_DUOC", "vi_sao": "thiếu tệp ngày " +
                (ngay if not moi else ngay - timedelta(days=7)).isoformat()}
    chung = [k for k in moi if k in cu]
    hang = sorted(({**moi[k], "tang": moi[k]["sao"] - cu[k]["sao"]} for k in chung), key=lambda d: -d["tang"])
    return {"trang_thai": "XONG", "ngay": ngay.isoformat(), "so_repo_chung": len(chung),
            "bo_vi_moi_vao": len(moi) - len(chung), "top": hang[:top]}


def _in(x: dict) -> None:
    # Lịch chạy bằng pythonw: sys.stdout là None — reconfigure/print mà không chặn thì chết TRƯỚC khi
    # chụp, và sổ lịch không có dòng nào (dang_truyen_worker vấp đúng chỗ này ngày 14/09).
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(x, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:] or ["chup"]
    if a[0] == "chup":
        _in(chup())
    elif a[0] == "bang":
        _in(bang(date.fromisoformat(a[1]) if len(a) > 1 else date.today()))
    else:
        sys.exit(__doc__)
