from concurrent.futures import ThreadPoolExecutor
import json
import time
import requests
from tabulate import tabulate

API_KEYS = [
    # 最新這組
    "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",
    # 之前提供的 7 組
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
]

ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
# 使用你在 curl 驗證成功的現役在線模型
MODEL_NAME = "moonshotai/kimi-k3"


def test_key(key):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 針對自動化入庫進行 JSON 格式驗證
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": (
                    '嚴格輸出純 JSON：{"status":"ok"}，不得輸出任何其他字元。'
                ),
            }
        ],
        "max_tokens": 50,
        "temperature": 0.0,
        "stream": False,
    }

    t0 = time.time()
    try:
        r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=12.0)
        latency = round(time.time() - t0, 2)

        if r.status_code == 200:
            content = (
                r.json()["choices"][0]["message"]["content"]
                .strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            data = json.loads(content)
            if data.get("status") == "ok":
                return [
                    key[:12] + "...",
                    "✔ 正常可用",
                    f"{latency}s",
                    "通過 (全自動入庫)",
                ]
            return [key[:12] + "...", "✔ 連通", f"{latency}s", "回傳非純JSON"]
        elif r.status_code == 401:
            return [key[:12] + "...", "❌ 密鑰無效 (401)", "-", "無法使用"]
        elif r.status_code == 402 or "quota" in r.text.lower():
            return [key[:12] + "...", "❌ 點數耗盡 (402)", "-", "無法使用"]
        elif r.status_code == 403:
            return [key[:12] + "...", "❌ 無權限訪問此模型 (403)", "-", "無法使用"]
        elif r.status_code == 429:
            return [key[:12] + "...", "❌ 觸發限流 (429)", "-", "無法使用"]
        else:
            return [
                key[:12] + "...",
                f"❌ 異常 ({r.status_code})",
                "-",
                "無法使用",
            ]
    except json.JSONDecodeError:
        return [
            key[:12] + "...",
            "✔ 連通",
            f"{round(time.time() - t0, 2)}s",
            "需字串清洗",
        ]
    except Exception as e:
        return [key[:12] + "...", f"❌ 連線超時/出錯", "-", "無法使用"]


print(f"[*] 正在並行驗證 8 組 Key 在 [{MODEL_NAME}] 上的可用性...\n")
with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(test_key, API_KEYS))

headers = ["API Key 簡稱", "通訊狀態", "延遲", "自動化能力"]
print(tabulate(results, headers=headers, tablefmt="github"))