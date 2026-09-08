# -*- coding: utf-8 -*-
"""JySecAI 桌面控制面板(繁體中文版)

架構:
  - 後端引擎: desktop_runtime.DesktopRuntime
    (34 個單元測試保護: 日誌密鑰遮蔽、事件佇列上限、僅迴環探測、執行緒安全)
  - 前端介面: Tkinter 深色主題 + 繁體中文, 事件驅動(無忙等輪詢)

用法:
  python gui_control_panel.py            # 開啟圖形介面
  python gui_control_panel.py --selftest # 無頭自檢(建 UI 後即退出, 供 CI/驗證)
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox

import desktop_runtime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

C_BG = "#0f1420"
C_CARD = "#171e2e"
C_BORDER = "#232c42"
C_TEXT = "#e6ebf5"
C_DIM = "#8b96ad"
C_ACCENT = "#4f8cff"
C_GREEN = "#2ecc71"
C_RED = "#e74c3c"
C_ORANGE = "#f39c12"
C_LOG_BG = "#0b0f18"
C_LOG_FG = "#c9d4e8"

F_UI = ("Microsoft JhengHei UI", 10)
F_BOLD = ("Microsoft JhengHei UI", 10, "bold")
F_TITLE = ("Microsoft JhengHei UI", 15, "bold")
F_SMALL = ("Microsoft JhengHei UI", 8)
F_LOG = ("Consolas", 9)

STATE_TEXT = {
    "stopped": ("已停止", C_DIM),
    "starting": ("啟動中…", C_ORANGE),
    "running": ("執行中", C_GREEN),
    "stopping": ("停止中…", C_ORANGE),
    "unresponsive": ("無回應", C_ORANGE),
    "external": ("既有執行個體", C_ORANGE),
    "conflict": ("埠被占用", C_RED),
    "error": ("錯誤", C_RED),
}
LOG_TAG = {"success": "ok", "error": "err", "warning": "warn"}


def _build_runtime(root_dir):
    return desktop_runtime.DesktopRuntime(root_dir)


class Panel:
    """繁中介面; 所有狀態皆由 runtime 事件佇列驅動, UI 執行緒零忙等。"""

    def __init__(self, root, root_dir=BASE_DIR):
        self.root = root
        self.rt = _build_runtime(root_dir)
        root.title("JySecAI 控制面板")
        root.geometry("680x760")
        root.minsize(600, 680)
        root.configure(bg=C_BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._btn_style = {}
        self._build()
        self.rt.begin_monitoring()
        self._pump()
        self._refresh(self.rt.snapshot())

    # ── 元件工廠 ─────────────────────────────────────────────
    def _card(self, parent, text):
        return tk.LabelFrame(parent, text=" " + text + " ", bg=C_CARD, fg=C_DIM,
                             font=F_BOLD, relief=tk.FLAT, bd=0,
                             highlightbackground=C_BORDER, highlightthickness=1)

    def _button(self, parent, text, cmd, bg, hover):
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#ffffff",
                      font=F_BOLD, relief=tk.FLAT, bd=0, cursor="hand2",
                      activebackground=hover, activeforeground="#ffffff",
                      padx=16, pady=8)
        b.bind("<Enter>", lambda e: b["state"] != "disabled" and b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        self._btn_style[b] = (bg, hover)
        return b

    def _set_enabled(self, btn, enabled):
        btn.config(state=tk.NORMAL if enabled else tk.DISABLED,
                   bg=self._btn_style[btn][0] if enabled else "#2a3550",
                   fg="#ffffff" if enabled else "#5c688a")

    # ── 版面 ─────────────────────────────────────────────────
    def _build(self):
        wrap = tk.Frame(self.root, bg=C_BG, padx=18, pady=14)
        wrap.pack(fill=tk.BOTH, expand=True)

        head = tk.Frame(wrap, bg=C_BG)
        head.pack(fill=tk.X, pady=(0, 10))
        tk.Label(head, text="JySecAI 控制面板", bg=C_BG, fg=C_TEXT,
                 font=F_TITLE).pack(side=tk.LEFT)
        tk.Label(head, text="JySecAI 桌面版", bg=C_BG, fg=C_DIM,
                 font=F_SMALL).pack(side=tk.LEFT, padx=(10, 0), pady=(6, 0))

        sc = self._card(wrap, "服務狀態")
        sc.pack(fill=tk.X, pady=(0, 10))
        row = tk.Frame(sc, bg=C_CARD)
        row.pack(fill=tk.X, padx=14, pady=12)
        self.dot = tk.Canvas(row, width=12, height=12, bg=C_CARD, highlightthickness=0)
        self.dot.pack(side=tk.LEFT)
        self.lbl_state = tk.Label(row, text="已停止", bg=C_CARD, fg=C_DIM, font=F_BOLD)
        self.lbl_state.pack(side=tk.LEFT, padx=8)
        self.lbl_detail = tk.Label(row, text="—", bg=C_CARD, fg=C_DIM, font=F_SMALL,
                                   anchor="w", wraplength=430, justify="left")
        self.lbl_detail.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        ic = self._card(wrap, "服務資訊")
        ic.pack(fill=tk.X, pady=(0, 10))
        grid = tk.Frame(ic, bg=C_CARD)
        grid.pack(fill=tk.X, padx=14, pady=10)
        self.info = {}
        for i, key in enumerate(("url", "port", "host", "tls", "version", "pid")):
            label = {"url": "網址", "port": "埠", "host": "主機",
                     "tls": "加密", "version": "版本", "pid": "行程"}[key]
            tk.Label(grid, text=label, bg=C_CARD, fg=C_DIM, font=F_UI).grid(
                row=i, column=0, sticky="w", pady=2)
            self.info[key] = tk.Label(grid, text="—", bg=C_CARD, fg=C_TEXT, font=F_UI)
            self.info[key].grid(row=i, column=1, sticky="w", padx=14, pady=2)
        grid.columnconfigure(1, weight=1)

        cc = self._card(wrap, "控制")
        cc.pack(fill=tk.X, pady=(0, 10))
        btns = tk.Frame(cc, bg=C_CARD)
        btns.pack(fill=tk.X, padx=14, pady=12)
        self.btn_start = self._button(btns, "▶  啟動服務", self._start, C_ACCENT, "#3d78e0")
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_stop = self._button(btns, "■  停止", self._stop, C_RED, "#c0392b")
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_restart = self._button(btns, "⟳  重新啟動", self._restart, C_ORANGE, "#d68910")
        self.btn_restart.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_open = self._button(btns, "🌐  開啟主控台", self._open, "#27ae60", "#1f8b4d")
        self.btn_open.pack(side=tk.LEFT)

        lc = self._card(wrap, "服務日誌")
        lc.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.log = tk.Text(lc, height=12, font=F_LOG, bg=C_LOG_BG, fg=C_LOG_FG,
                           relief=tk.FLAT, bd=0, wrap="word", state=tk.DISABLED,
                           insertbackground=C_LOG_FG)
        sb = tk.Scrollbar(lc, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        sb.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        self.log.tag_config("ok", foreground="#2ecc71")
        self.log.tag_config("err", foreground="#e74c3c")
        self.log.tag_config("warn", foreground="#f39c12")

        self._append_log("info", "控制面板已就緒。")

    # ── 事件驅動: 100ms 幫浦排空事件佇列(有界, 零忙等) ──────
    def _pump(self):
        try:
            for _ in range(200):
                level, message = self.rt.events.get_nowait()
                self._append_log(level, message)
        except Exception:
            pass
        self._refresh(self.rt.snapshot())
        if self.root.winfo_exists():
            self.root.after(100, self._pump)

    def _refresh(self, snap):
        state = snap.get("state", "stopped")
        text, color = STATE_TEXT.get(state, (state, C_DIM))
        if str(self.lbl_state["text"]) != text:
            self.lbl_state.config(text=text, fg=color)
            self.dot.delete("all")
            self.dot.create_oval(1, 1, 11, 11, fill=color, outline="")
        if self.lbl_detail["text"] != snap.get("detail", "—"):
            self.lbl_detail.config(text=snap.get("detail", "—"))

        s = self.rt.settings
        url = s.url if s else "—"
        self.info["url"].config(text=url)
        self.info["port"].config(text=str(s.port) if s else "—")
        self.info["host"].config(text=s.host if s else "—")
        self.info["tls"].config(text="HTTPS" if (s and s.tls) else "HTTP")
        self.info["version"].config(text=s.version or "—" if s else "—")
        pid = snap.get("pid")
        self.info["pid"].config(text=str(pid) if pid else "—")

        owned = bool(snap.get("owned"))
        busy = bool(snap.get("busy"))
        self._set_enabled(self.btn_start, not owned and not busy)
        self._set_enabled(self.btn_stop, owned and not busy)
        self._set_enabled(self.btn_restart, owned and not busy)
        self._set_enabled(self.btn_open, bool(s))

    # ── 動作 ─────────────────────────────────────────────────
    def _append_log(self, level, message):
        tag = LOG_TAG.get(level, "")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n", tag)
        if float(self.log.index("end-1c").split(".")[0]) > 2000:
            self.log.delete("1.0", "200.0")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _start(self):
        if not self.rt.start():
            return
        self._append_log("info", "啟動指令已送出…")

    def _stop(self):
        if not self.rt.stop():
            return
        self._append_log("info", "停止指令已送出…")

    def _restart(self):
        if not self.rt.restart():
            return
        self._append_log("info", "重新啟動指令已送出…")

    def _open(self):
        s = self.rt.settings
        if not s:
            return
        import webbrowser
        webbrowser.open(s.url)

    def _on_close(self):
        snap = self.rt.snapshot()
        if snap.get("owned"):
            if not messagebox.askyesno("確認", "服務仍在執行，要一併停止並結束面板嗎？"):
                return
            self.rt.stop()
        self.rt.close()
        self.root.destroy()


def main():
    if "--selftest" in sys.argv:
        root = tk.Tk()
        root.withdraw()
        panel = Panel(root, BASE_DIR)
        snap = panel.rt.snapshot()
        print("SELFTEST_OK state=%s config_error=%r url=%s" % (
            snap.get("state"), snap.get("config_error"),
            panel.rt.settings.url if panel.rt.settings else "—"))
        root.destroy()
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("JySecAI.ControlPanel")
    except Exception:
        pass
    root = tk.Tk()
    Panel(root)
    root.mainloop()


if __name__ == "__main__":
    main()
