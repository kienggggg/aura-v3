"""cli_hub.pyw — Bảng điều khiển & Trình khởi chạy AI CLI toàn năng cho Windows.

Một cú bấm là vào ngay CLI bạn cần, không cần nhớ lệnh, không gõ lặp lại.
Tự do đổi thư mục dự án trỏ tới (AURA v3, AURA OS v2, Robot Rover, hoặc thư mục bất kỳ).
Tự động nạp và tạo file trí nhớ AI (CLAUDE.md, AGENTS.md, MEMORY.md) cho từng dự án.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

GOC = Path(__file__).resolve().parent
CONFIG_FILE = GOC / "cli_hub_config.json"

# Bảng màu Huashu Cyber-Dark
BG_DARK = "#0a0c10"
BG_CARD = "#12161f"
BG_HOVER = "#1c2230"
BORDER_COLOR = "#252d3d"
BORDER_ACTIVE = "#f97316"
TEXT_MAIN = "#f1f5f9"
TEXT_MUTED = "#94a3b8"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#38bdf8"
ACCENT_GREEN = "#22c55e"
ACCENT_PURPLE = "#a855f7"
ACCENT_YELLOW = "#eab308"


CLI_REGISTRY = [
    {
        "id": "claude",
        "name": "Claude Code",
        "icon": "🟣",
        "color": ACCENT_PURPLE,
        "tag": "Anthropic Official",
        "desc": "Agent lập trình cao cấp, tự đọc CLAUDE.md trong thư mục dự án.",
        "cmd": "claude",
        "check": lambda: shutil.which("claude") is not None,
    },
    {
        "id": "codex",
        "name": "OpenAI Codex",
        "icon": "🟢",
        "color": ACCENT_GREEN,
        "tag": "OpenAI Official",
        "desc": "Agent lập trình GPT-4o, tự đọc AGENTS.md, kiểm định logic độc lập.",
        "cmd": "codex",
        "check": lambda: shutil.which("codex") is not None,
    },
    {
        "id": "supercode",
        "name": "SuperCode (Free SWE)",
        "icon": "🟡",
        "color": ACCENT_YELLOW,
        "tag": "Free GLM / DeepSeek",
        "desc": "SWE Agent mã nguồn mở, lập trình miễn phí qua API GLM-4/DeepSeek.",
        "cmd": "supercode",
        "check": lambda: shutil.which("supercode") is not None,
    },
    {
        "id": "9router",
        "name": "9Router Gateway",
        "icon": "🔵",
        "color": ACCENT_BLUE,
        "tag": "API Gateway (Port 20128)",
        "desc": "Cân bằng tải & gom 40+ provider AI miễn phí, chống cạn quota.",
        "cmd": "9router --tray",
        "is_service": True,
        "port": 20128,
        "check": lambda: shutil.which("9router") is not None,
    },
    {
        "id": "ollama",
        "name": "Ollama Local Engine",
        "icon": "🦙",
        "color": ACCENT_ORANGE,
        "tag": "Local LLM (F:\\ollama-models)",
        "desc": "Chạy model cục bộ qwen3.5:4b offline 100% không tốn API.",
        "cmd": "ollama run qwen3.5:4b",
        "is_service": True,
        "port": 11434,
        "check": lambda: shutil.which("ollama") is not None,
    },
    {
        "id": "rtk",
        "name": "RTK Shell (Token Compressor)",
        "icon": "⚡",
        "color": ACCENT_YELLOW,
        "tag": "Tiết kiệm 60-94% Token",
        "desc": "Terminal nén log git status, pytest trước khi đưa cho AI đọc.",
        "cmd": "D:\\AURA_OS_v2\\.rtk\\rtk.exe bash",
        "check": lambda: os.path.exists("D:\\AURA_OS_v2\\.rtk\\rtk.exe"),
    },
    {
        "id": "openclaw",
        "name": "OpenClaw Automation",
        "icon": "🟠",
        "color": ACCENT_ORANGE,
        "tag": "Multi-Agent OS",
        "desc": "Tự động hóa tác vụ màn hình, thao tác trình duyệt đa tác tử.",
        "cmd": "openclaw",
        "check": lambda: shutil.which("openclaw") is not None,
    },
    {
        "id": "aura_chat",
        "name": "AURA v3 Chat App",
        "icon": "🤖",
        "color": ACCENT_BLUE,
        "tag": "AURA Native UI",
        "desc": "Giao diện Chatbot AURA v3 (17 tệp ranh giới, localhost:8799).",
        "cmd": f'python "{GOC / "aura_app.pyw"}"',
        "check": lambda: (GOC / "aura_app.pyw").exists(),
    },
    {
        "id": "mcporter",
        "name": "MCPorter (MCP Manager)",
        "icon": "📦",
        "color": ACCENT_PURPLE,
        "tag": "Model Context Protocol",
        "desc": "Quản lý gói công cụ MCP servers cho các agent.",
        "cmd": "mcporter",
        "check": lambda: shutil.which("mcporter") is not None,
    },
    {
        "id": "gitnexus",
        "name": "GitNexus",
        "icon": "🐙",
        "color": ACCENT_GREEN,
        "tag": "Multi-Repo Manager",
        "desc": "Đồng bộ và quản lý nhiều git repository cùng lúc.",
        "cmd": "gitnexus",
        "check": lambda: shutil.which("gitnexus") is not None,
    },
]


def load_config() -> dict:
    default_cfg = {
        "active_project": str(GOC),
        "recent_projects": [str(GOC), "D:\\AURA_OS_v2"],
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_cfg.update(data)
        except Exception:
            pass
    return default_cfg


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def check_port(port: int) -> bool:
    """Kiểm tra cổng service có đang lắng nghe không."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def launch_cli(tool_dict: dict, work_dir: str) -> None:
    """Mở một cửa sổ Terminal/PowerShell mới chạy thẳng vào CLI tại thư mục dự án."""
    cmd = tool_dict["cmd"]
    name = tool_dict["name"]

    target_dir = Path(work_dir)
    if not target_dir.is_dir():
        target_dir = GOC

    # Đặt biến môi trường nếu cần
    env_str = "$env:OLLAMA_MODELS='F:\\ollama-models'; "

    if tool_dict.get("id") == "aura_chat":
        subprocess.Popen([sys.executable, str(GOC / "aura_app.pyw")], cwd=str(GOC))
        return

    # Lệnh bật PowerShell mới với tiêu đề đẹp, nạp môi trường và chạy lệnh
    ps_cmd = f"[Console]::Title = 'AURA CLI Hub — {name} [{target_dir.name}]'; {env_str} {cmd}"
    full_exec = f'start powershell -NoExit -ExecutionPolicy Bypass -Command "{ps_cmd}"'

    subprocess.Popen(full_exec, shell=True, cwd=str(target_dir))


def init_project_memory(project_dir: Path) -> str:
    """Tự động khởi tạo bộ nhớ AI (CLAUDE.md, AGENTS.md, MEMORY.md) cho dự án."""
    if not project_dir.is_dir():
        return "Thư mục không tồn tại."

    created = []

    # 1. CLAUDE.md
    claude_file = project_dir / "CLAUDE.md"
    if not claude_file.exists():
        claude_content = f"""# {project_dir.name} — BẢN ĐỒ BỐI CẢNH DỰ ÁN CHO AI

Tài liệu này được tự động tạo bởi AURA CLI Hub để các CLI Agent (Claude Code, Codex, Antigravity) hiểu ngay bối cảnh dự án khi khởi động.

## 1. MỤC TIÊU DỰ ÁN
- Tên dự án: `{project_dir.name}`
- Thư mục gốc: `{project_dir}`
- Mục tiêu chính: [Điền mục tiêu dự án tại đây]

## 2. QUY TẮC PHÁT TRIỂN & KỶ LUẬT
1. **Bằng chứng trên đĩa là chân lý duy nhất:** Code xong phải có test thật hoặc artifact kiểm chứng.
2. **Không phá vỡ cấu trúc:** Giữ nguyên các module hiện hữu, chỉ sửa đúng phạm vi được giao.
3. **Tiết kiệm token:** Giao việc theo từng mẩu nhỏ (atomic subtask), không sinh log rác.

## 3. CÔNG NGHỆ & LỆNH THƯỜNG DÙNG
- Ngôn ngữ chính: Python / Node.js / C++
- Lệnh chạy test: `pytest` hoặc `npm test`
"""
        claude_file.write_text(claude_content, encoding="utf-8")
        created.append("CLAUDE.md")

    # 2. AGENTS.md
    agents_file = project_dir / "AGENTS.md"
    if not agents_file.exists():
        agents_content = f"""# AGENTS.md — QUY TẮC BẮT BUỘC DÀNH CHO AGENT TẠI {project_dir.name}

1. **Tách biệt Worker và Verifier:** Runner không tự gán PASS, phải có test độc lập.
2. **Fail-Closed by Design:** Lỗi trả về exit code khác 0, không nuốt lỗi.
3. **Path Confinement:** Tuyệt đối không ghi file ngoài thư mục `{project_dir}`.
"""
        agents_file.write_text(agents_content, encoding="utf-8")
        created.append("AGENTS.md")

    # 3. MEMORY.md
    memory_file = project_dir / "MEMORY.md"
    if not memory_file.exists():
        memory_content = f"""# MEMORY.md — TRÍ NHỚ DÀI HẠN & TIẾN ĐỘ DỰ ÁN {project_dir.name}

## 📌 TRẠNG THÁI HIỆN TẠI
- Đang làm: [Ghi công việc hiện tại]
- Đã hoàn tất: Khởi tạo bối cảnh dự án qua AURA CLI Hub.

## 📝 NHẬT KÝ QUYẾT ĐỊNH & BÀI HỌC (Append-Only)
- 2026-08-16: Khởi tạo dự án và kết nối với AI CLI Hub.
"""
        memory_file.write_text(memory_content, encoding="utf-8")
        created.append("MEMORY.md")

    if created:
        return f"Đã tạo thành công {', '.join(created)} trong {project_dir.name}!"
    return f"Dự án {project_dir.name} đã có sẵn đầy đủ file trí nhớ (CLAUDE.md, AGENTS.md, MEMORY.md)."


class CLIHubApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AURA AI CLI Hub — Trình Khởi Chạy & Quản Lý CLI")
        self.geometry("900x740")
        self.minsize(820, 600)
        self.configure(bg=BG_DARK)

        self.cfg = load_config()
        self.active_project = tk.StringVar(value=self.cfg.get("active_project", str(GOC)))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_cards())

        self.setup_ui()
        self.render_cards()

    def setup_ui(self):
        # 1. Top Header
        header = tk.Frame(self, bg=BG_DARK, pady=12, padx=20)
        header.pack(fill=tk.X)

        title_box = tk.Frame(header, bg=BG_DARK)
        title_box.pack(side=tk.LEFT)

        title = tk.Label(
            title_box,
            text="⚡ AURA AI CLI HUB",
            font=("Segoe UI", 18, "bold"),
            fg=TEXT_MAIN,
            bg=BG_DARK,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            title_box,
            text="Trình Khởi Chạy AI Đa Tác Tử • Định Tuyến Dự Án & Nạp Trí Nhớ Tự Động",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=BG_DARK,
        )
        subtitle.pack(anchor="w")

        # Search box
        search_frame = tk.Frame(header, bg=BG_CARD, padx=10, pady=5, highlightthickness=1, highlightbackground=BORDER_COLOR)
        search_frame.pack(side=tk.RIGHT)

        tk.Label(search_frame, text="🔍", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 11)).pack(side=tk.LEFT)
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            font=("Segoe UI", 11),
            bd=0,
            width=20,
        )
        search_entry.pack(side=tk.LEFT, padx=5)

        # 2. Project Target Setting Bar
        proj_bar = tk.Frame(self, bg=BG_CARD, padx=15, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        proj_bar.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            proj_bar,
            text="📁 DỰ ÁN ĐANG TRỎ:",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.proj_combo = ttk.Combobox(
            proj_bar,
            textvariable=self.active_project,
            values=self.cfg.get("recent_projects", [str(GOC)]),
            font=("Consolas", 10),
            width=42,
        )
        self.proj_combo.pack(side=tk.LEFT, padx=5)
        self.proj_combo.bind("<<ComboboxSelected>>", self.on_project_changed)
        self.proj_combo.bind("<Return>", self.on_project_changed)

        # Browse Button
        browse_btn = tk.Button(
            proj_bar,
            text="📂 Chọn Thư Mục...",
            font=("Segoe UI", 9, "bold"),
            bg=BG_HOVER,
            fg=TEXT_MAIN,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.browse_directory,
        )
        browse_btn.pack(side=tk.LEFT, padx=6)

        # Memory Init Button
        mem_btn = tk.Button(
            proj_bar,
            text="🧠 Nạp Trí Nhớ AI (.md)",
            font=("Segoe UI", 9, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.inject_memory_files,
        )
        mem_btn.pack(side=tk.RIGHT)

        # 3. Body Scrollable Area
        self.canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG_DARK)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=880)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=5)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)

        # Mousewheel scroll
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def browse_directory(self):
        chosen = filedialog.askdirectory(initialdir=self.active_project.get(), title="Chọn Thư Mục Dự Án")
        if chosen:
            p = str(Path(chosen).resolve())
            self.active_project.set(p)
            self.save_project_selection(p)

    def on_project_changed(self, event=None):
        p = str(Path(self.active_project.get()).resolve())
        self.save_project_selection(p)

    def save_project_selection(self, p: str):
        recents = self.cfg.get("recent_projects", [])
        if p not in recents:
            recents.insert(0, p)
        else:
            recents.remove(p)
            recents.insert(0, p)
        self.cfg["active_project"] = p
        self.cfg["recent_projects"] = recents[:8]
        self.proj_combo["values"] = self.cfg["recent_projects"]
        save_config(self.cfg)

    def inject_memory_files(self):
        p = Path(self.active_project.get())
        msg = init_project_memory(p)
        messagebox.showinfo("Khởi Tạo Trí Nhớ AI", msg)

    def render_cards(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower()

        for tool in CLI_REGISTRY:
            if query and query not in tool["name"].lower() and query not in tool["desc"].lower() and query not in tool["cmd"].lower():
                continue

            installed = tool["check"]()
            is_service = tool.get("is_service", False)
            service_running = check_port(tool.get("port", 0)) if is_service else False

            # Card Container
            card = tk.Frame(
                self.scroll_frame,
                bg=BG_CARD,
                padx=15,
                pady=12,
                highlightthickness=1,
                highlightbackground=BORDER_ACTIVE if (is_service and service_running) else BORDER_COLOR,
            )
            card.pack(fill=tk.X, expand=True, pady=6, padx=5)

            # Left Col (Icon + Title + Desc)
            left = tk.Frame(card, bg=BG_CARD)
            left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            title_row = tk.Frame(left, bg=BG_CARD)
            title_row.pack(anchor="w")

            tk.Label(
                title_row,
                text=tool["icon"],
                font=("Segoe UI Emoji", 14),
                bg=BG_CARD,
            ).pack(side=tk.LEFT, padx=(0, 8))

            tk.Label(
                title_row,
                text=tool["name"],
                font=("Segoe UI", 13, "bold"),
                fg=TEXT_MAIN,
                bg=BG_CARD,
            ).pack(side=tk.LEFT)

            # Tag
            tag_label = tk.Label(
                title_row,
                text=f" {tool['tag']} ",
                font=("Segoe UI", 9, "bold"),
                fg=tool["color"],
                bg=BG_DARK,
                padx=6,
                pady=2,
            )
            tag_label.pack(side=tk.LEFT, padx=10)

            if is_service:
                status_text = "● ĐANG CHẠY" if service_running else "○ ĐANG DỪNG"
                status_color = ACCENT_GREEN if service_running else TEXT_MUTED
                tk.Label(
                    title_row,
                    text=status_text,
                    font=("Segoe UI", 9, "bold"),
                    fg=status_color,
                    bg=BG_CARD,
                ).pack(side=tk.LEFT, padx=5)

            # Desc
            tk.Label(
                left,
                text=tool["desc"],
                font=("Segoe UI", 10),
                fg=TEXT_MUTED,
                bg=BG_CARD,
                wraplength=540,
                justify=tk.LEFT,
            ).pack(anchor="w", pady=(4, 0))

            # Command hint
            cur_p = Path(self.active_project.get()).name
            cmd_hint = tk.Label(
                left,
                text=f"> [{cur_p}] {tool['cmd']}",
                font=("Consolas", 9),
                fg=ACCENT_ORANGE if installed else "#ef4444",
                bg=BG_CARD,
            )
            cmd_hint.pack(anchor="w", pady=(2, 0))

            # Right Col (Action Buttons)
            right = tk.Frame(card, bg=BG_CARD)
            right.pack(side=tk.RIGHT, padx=(10, 0))

            if installed:
                btn_text = "Khởi Chạy 🚀" if not (is_service and service_running) else "Vào Console ⚡"
                btn = tk.Button(
                    right,
                    text=btn_text,
                    font=("Segoe UI", 10, "bold"),
                    bg=tool["color"],
                    fg="#000000" if tool["color"] in (ACCENT_YELLOW, ACCENT_ORANGE) else "#ffffff",
                    activebackground=TEXT_MAIN,
                    bd=0,
                    padx=14,
                    pady=6,
                    cursor="hand2",
                    command=lambda t=tool: launch_cli(t, self.active_project.get()),
                )
                btn.pack(side=tk.RIGHT)
            else:
                tk.Label(
                    right,
                    text="Chưa có",
                    font=("Segoe UI", 10),
                    fg="#ef4444",
                    bg=BG_CARD,
                    padx=10,
                ).pack(side=tk.RIGHT)


if __name__ == "__main__":
    app = CLIHubApp()
    app.mainloop()
