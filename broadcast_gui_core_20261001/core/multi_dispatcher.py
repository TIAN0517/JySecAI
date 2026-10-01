import requests
import json
import os
import concurrent.futures
import time

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_routes.json")
FALLBACK_PROXY = os.environ.get(
    "TPE_BROADCAST_PROXY", "socks5h://202.160.76.156:11083"
)

def load_routes():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            routes = json.load(f)
            return routes if isinstance(routes, list) else []
    except Exception:
        return []

def enabled_routes():
    return [
        route for route in load_routes()
        if route.get("enabled", True) and route.get("token") and route.get("group_id")
    ]


def send_single(bot_token, chat_id, message, parse_mode="HTML", attempts=3):
    bot_token = bot_token.strip()
    chat_id = str(chat_id).strip()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    last_error = "unknown error"
    for attempt in range(1, attempts + 1):
        try:
            proxies = None
            if attempt > 1 and FALLBACK_PROXY:
                proxies = {"http": FALLBACK_PROXY, "https": FALLBACK_PROXY}
            r = requests.post(url, json=payload, timeout=10, proxies=proxies)
            data = r.json()
            if r.ok and data.get("ok", False):
                return True
            last_error = data.get("description", f"HTTP {r.status_code}")
        except Exception as e:
            last_error = str(e)
        if attempt < attempts:
            time.sleep(attempt)
    print(f"[!] 推播失敗到 {chat_id}（重試 {attempts} 次）: {last_error}", flush=True)
    return False


def broadcast_all_detailed(message, parse_mode="HTML"):
    routes = enabled_routes()
    if not routes:
        return []

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(routes))) as executor:
        futures = {
            executor.submit(
                send_single,
                route["token"],
                route["group_id"],
                message,
                parse_mode,
            ): route
            for route in routes
        }
        for future in concurrent.futures.as_completed(futures):
            route = futures[future]
            try:
                ok = bool(future.result())
            except Exception:
                ok = False
            results.append({
                "name": route.get("name", "unnamed"),
                "group_id": str(route["group_id"]),
                "token": route["token"],
                "ok": ok,
            })
    return results

def broadcast_all(message, parse_mode="HTML"):
    return sum(result["ok"] for result in broadcast_all_detailed(message, parse_mode))

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "🚨 測試多 Bot 多群組即時推播！"
    cnt = broadcast_all(msg)
    print(f"完成推播，成功發送至 {cnt} 個目標群組！")
