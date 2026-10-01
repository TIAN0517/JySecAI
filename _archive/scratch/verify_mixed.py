from concurrent.futures import ThreadPoolExecutor
import json
import time
import requests
from tabulate import tabulate

LLM_KEYS = [
    "a24b3819a36c4cdfa14a032fad0caf33.yTB5oTq8OGaotKXyqlcXxuJs",
    "c6e2fa46a9bd4205a9da3526aa578553.4zVydL3mNyL9dXLuzmd4KdZY",
    "3a19f2f0c4044bbf9bd8daa88cde4390.IGdXlv8cQonyTbDSGSWJX5qq",
]

TG_TOKENS = [
    "8572662914:AAEOzm86LBTUCPSoyOSEr57PHW9Rn3Vey3g",
    "8442777602:AAEkTcc6rRLVlp-OOHUTkP52X50D9voh_40",
    "8047936135:AAEDGcFPvyZZtlaBK5v7FkN-qw6t-LgLGaY",
    "7442421291:AAEAKoQxxMnhZ3-pd8UQdwRFaA_c01yYdxo",
    "8431805678:AAFuGbGA5wmSlJtogDVVvApxaVw5rJRWWu8",
    "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
]


def test_tg_bot(token):
    url = f"https://api.telegram.org/bot{token}/getMe"
    t0 = time.time()
    try:
        r = requests.get(url, timeout=6.0)
        latency = round(time.time() - t0, 2)
        if r.status_code == 200 and r.json().get("ok"):
            bot_name = r.json()["result"].get("username", "Unknown")
            return [
                token[:12] + "...",
                "Telegram Bot",
                "✔ 正常可用",
                f"@{bot_name}",
                f"{latency}s",
            ]
        return [
            token[:12] + "...",
            "Telegram Bot",
            f"❌ 失效 ({r.status_code})",
            "-",
            "-",
        ]
    except Exception as e:
        return [token[:12] + "...", "Telegram Bot", "❌ 連線超時/受阻", "-", "-"]


def test_llm_key(key):
    # 測試智譜官方端點
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=6.0)
        latency = round(time.time() - t0, 2)
        if r.status_code == 200:
            return [
                key[:12] + "...",
                "LLM API (GLM)",
                "✔ 正常可用",
                "glm-4-flash",
                f"{latency}s",
            ]
        elif r.status_code == 401:
            return [
                key[:12] + "...",
                "LLM API (GLM)",
                "❌ 密鑰無效/非官方",
                "-",
                "-",
            ]
        else:
            return [
                key[:12] + "...",
                "LLM API (GLM)",
                f"❌ 異常 ({r.status_code})",
                "-",
                "-",
            ]
    except Exception as e:
        return [key[:12] + "...", "LLM API (GLM)", "❌ 連線超時", "-", "-"]


print("[*] 正在並行驗證混合金鑰...\n")
results = []

with ThreadPoolExecutor(max_workers=9) as executor:
    tg_res = list(executor.map(test_tg_bot, TG_TOKENS))
    llm_res = list(executor.map(test_llm_key, LLM_KEYS))

results.extend(tg_res)
results.extend(llm_res)

headers = ["金鑰簡稱", "類型判斷", "連通狀態", "對象 / 詳情", "延遲"]
print(tabulate(results, headers=headers, tablefmt="github"))