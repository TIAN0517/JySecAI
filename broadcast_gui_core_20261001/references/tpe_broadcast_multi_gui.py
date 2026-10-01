import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import signal
import json
import threading
import time
import requests
from gui_branding import apply_window_icon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "bot_routes.json")

class MultiRouteGUI:
    def __init__(self, root):
        self.root = root
        apply_window_icon(self.root)
        self.root.title("TPE 119 派遣系統 — 多 Bot 多群組推播路由控制台")
        self.root.geometry("880x680")
        self.daemon_proc = None
        self.routes = self._load_routes()

        self._build_ui()
        self._refresh_table()

    def _load_routes(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_routes(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.routes, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        title_frame = tk.Frame(self.root, bg="#1b2a4a", pady=10)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="TPE 119 多 Bot ✕ 多群組分流發送控制台", 
                 fg="white", bg="#1b2a4a", font=("Noto Sans CJK TC", 13, "bold")).pack()

        main_box = ttk.Frame(self.root, padding=10)
        main_box.pack(fill=tk.BOTH, expand=True)

        # 頂部：新增 Bot 與 群組通道
        input_frame = ttk.LabelFrame(main_box, text=" 新增 / 自動綁定推播分流通道 ", padding=8)
        input_frame.pack(fill=tk.X, pady=5)

        # Row 0: 通道名稱 & Token
        ttk.Label(input_frame, text="通道備註:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.entry_name = ttk.Entry(input_frame, width=16)
        self.entry_name.insert(0, "分流 Bot")
        self.entry_name.grid(row=0, column=1, padx=4, pady=3)

        ttk.Label(input_frame, text="Bot Token:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        self.entry_token = ttk.Entry(input_frame, width=32)
        self.entry_token.grid(row=0, column=3, padx=4, pady=3)

        # Row 1: 群組 ID & 自動綁定按鈕
        ttk.Label(input_frame, text="目標群組 ID:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        self.entry_group = ttk.Entry(input_frame, width=16)
        self.entry_group.grid(row=1, column=1, padx=4, pady=3)

        btn_auto_detect = ttk.Button(input_frame, text="🔍 自動偵測並綁定群組 ID", command=self.auto_bind_single_bot)
        btn_auto_detect.grid(row=1, column=2, columnspan=2, sticky=tk.EW, padx=4, pady=3)

        # Row 2: 新增 & 測試廣播按鈕
        btn_add = ttk.Button(input_frame, text="➕ 新增至分流池", command=self.add_route)
        btn_add.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=5)

        btn_test_all = ttk.Button(input_frame, text="⚡ 測試全部群組推播", command=self.test_broadcast_all)
        btn_test_all.grid(row=2, column=2, columnspan=2, sticky=tk.EW, padx=4, pady=5)

        # 中部：現有通道列表
        list_frame = ttk.LabelFrame(main_box, text=" 目前已啟用的多 Bot 分流列表 ", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ("name", "token", "group_id", "status")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=5)
        self.tree.heading("name", text="名稱 / 備註")
        self.tree.heading("token", text="Bot Token (前段隱藏)")
        self.tree.heading("group_id", text="目標群組 ID")
        self.tree.heading("status", text="狀態")

        self.tree.column("name", width=130)
        self.tree.column("token", width=230)
        self.tree.column("group_id", width=140)
        self.tree.column("status", width=90)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        btn_del = ttk.Button(list_frame, text="❌ 刪除\n選取通道", width=10, command=self.del_route)
        btn_del.pack(side=tk.RIGHT, padx=5, fill=tk.Y)

        # 底部控制區
        ctrl_frame = ttk.Frame(main_box, padding=4)
        ctrl_frame.pack(fill=tk.X, pady=4)

        self.lbl_status = tk.Label(ctrl_frame, text="Daemon 狀態: ● 未運行", fg="gray", font=("Noto Sans CJK TC", 10, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(ctrl_frame, text="🚀 啟動分流推播 Daemon", bg="#27ae60", fg="white",
                                   font=("Noto Sans CJK TC", 10, "bold"), command=self.start_daemon)
        self.btn_start.pack(side=tk.RIGHT, padx=5)

        self.btn_stop = tk.Button(ctrl_frame, text="🛑 停止 Daemon", bg="#c0392b", fg="white",
                                  font=("Noto Sans CJK TC", 10, "bold"), command=self.stop_daemon)
        self.btn_stop.pack(side=tk.RIGHT, padx=5)

        # 日誌區
        log_frame = ttk.LabelFrame(main_box, text=" 廣播即時日誌 ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=4)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, bg="#111", fg="#00ff66", font=("Consolas", 8))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log(self, text):
        now = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{now}] {text}\n")
        self.log_area.see(tk.END)

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, r in enumerate(self.routes):
            tok_mask = r["token"][:12] + "..." + r["token"][-6:] if len(r["token"]) > 18 else r["token"]
            self.tree.insert("", tk.END, iid=str(idx), values=(r["name"], tok_mask, r["group_id"], "🟢 啟用中"))

    def auto_bind_single_bot(self):
        token = self.entry_token.get().replace("\r", "").replace("\n", "").strip()
        if not token:
            messagebox.showwarning("提示", "請先填寫上方 Bot Token！")
            return

        self.log(f"正在偵測 Token: {token[:12]}... 所在的最新群組...")

        def _worker():
            try:
                # 1. 驗證 Bot 身分
                me_res = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=6).json()
                if not me_res.get("ok"):
                    self.root.after(0, lambda: self.log(f"❌ Token 驗證失敗: {me_res.get('description')}"))
                    return

                bot_name = me_res["result"].get("username", "Bot")

                # 2. 獲取 Update 中的 Chat ID
                upd_res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=6).json()
                if upd_res.get("ok") and upd_res.get("result"):
                    for item in reversed(upd_res["result"]):
                        msg = item.get("message") or item.get("my_chat_member") or item.get("channel_post")
                        if msg and "chat" in msg:
                            chat_id = str(msg["chat"]["id"])
                            chat_title = msg["chat"].get("title", "未命名群組")
                            self.root.after(0, lambda cid=chat_id, bname=bot_name, ctitle=chat_title: self._apply_auto_bind(cid, bname, ctitle))
                            return

                self.root.after(0, lambda: self.log("⚠️ 未在 Updates 中偵測到群組。請先將該 Bot 加進群組，並在群組隨意發一則文字訊息後再按一次！"))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.log(f"❌ 自動綁定失敗: {err}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_auto_bind(self, chat_id, bot_name, chat_title):
        self.entry_group.delete(0, tk.END)
        self.entry_group.insert(0, chat_id)
        if self.entry_name.get().strip() in ["", "分流 Bot"]:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, f"@{bot_name} ({chat_title[:8]})")
        self.log(f"✅ 自動綁定成功！偵測到群組: {chat_title} (ID: {chat_id})")

    def add_route(self):
        name = self.entry_name.get().strip() or "未命名通道"
        token = self.entry_token.get().replace("\r", "").replace("\n", "").strip()
        gid = self.entry_group.get().replace("\r", "").replace("\n", "").strip()
        if not token or not gid:
            messagebox.showwarning("警告", "請填寫 Token 並確認群組 ID 已綁定！")
            return
        self.routes.append({"name": name, "token": token, "group_id": gid, "enabled": True})
        self._save_routes()
        self._refresh_table()
        self.entry_token.delete(0, tk.END)
        self.entry_group.delete(0, tk.END)
        self.log(f"➕ 已成功加入分流清單: {name} ➔ {gid}")

    def del_route(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        del self.routes[idx]
        self._save_routes()
        self._refresh_table()
        self.log("已移除該分流通道。")

    def test_broadcast_all(self):
        self.log(f"正在對清單中的 {len(self.routes)} 個目標發送測試廣播...")
        def _worker():
            from multi_dispatcher import broadcast_all
            cnt = broadcast_all("🚨 <b>[TPE 119 系統通知]</b>\n多 Bot 多群組分流推播連線測試成功！")
            self.root.after(0, lambda: self.log(f"✅ 測試完成：已成功同時推送到 {cnt} 個群組！"))
        threading.Thread(target=_worker, daemon=True).start()

    def start_daemon(self):
        if not self.routes:
            messagebox.showwarning("警告", "分流列表為空，請至少新增一組！")
            return
        self.stop_daemon()

        main_token = self.routes[0]["token"]
        main_group = self.routes[0]["group_id"]

        cmd = [
            "/usr/bin/python", "-u",
            "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/broadcast_daemon.py",
            "--interval", "10",
            "--city", "01",
            "--tg-bot-token", main_token,
            "--dispatch-group-id", main_group
        ]
        self.log(f"啟動廣播 Daemon... (共掛載 {len(self.routes)} 組分流目標)")
        self.daemon_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lbl_status.config(text=f"Daemon 狀態: ● 運行中 (PID {self.daemon_proc.pid})", fg="green")

        def _reader():
            for line in self.daemon_proc.stdout:
                line = line.strip()
                if line:
                    self.root.after(0, lambda l=line: self.log(l))

        threading.Thread(target=_reader, daemon=True).start()

    def stop_daemon(self):
        if self.daemon_proc and self.daemon_proc.poll() is None:
            self.log(f"停止 Daemon (PID {self.daemon_proc.pid})...")
            try:
                os.kill(self.daemon_proc.pid, signal.SIGTERM)
            except Exception:
                pass
            self.daemon_proc = None
        subprocess.run(["pkill", "-9", "-f", "broadcast_daemon.py"], stderr=subprocess.DEVNULL)
        if os.path.exists("/tmp/broadcast_daemon.lock"):
            try:
                os.remove("/tmp/broadcast_daemon.lock")
            except Exception:
                pass
        self.lbl_status.config(text="Daemon 狀態: ● 已停止", fg="gray")

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiRouteGUI(root)
    root.mainloop()
