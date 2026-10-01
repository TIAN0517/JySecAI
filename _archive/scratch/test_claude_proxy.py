import os
import requests

api_key = (
    "sk-376ca36fa6090758abb0634d61412c0fade52b0729b219ce3afc4ba3ec58b4a"
)
base_url = "https://czc.zh.kg/v1"
model = "claude-3-5-sonnet-20241022"

headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

payload = {
    "model": model,
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "ping"}],
}

print(f"[*] 正在測試 Claude 中轉站: {base_url} ...")
try:
    # 嘗試 Anthropic 原生 messages 端點
    url = f"{base_url.rstrip('/')}/messages"
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    print("HTTP 狀態碼:", r.status_code)
    print("返回內容:", r.text[:300])

    if r.status_code == 200:
        print("\n✔ Claude 中轉接口連通正常！")
    else:
        # 若失敗，嘗試常見的 OpenAI 相容路徑備援測試
        print("\n[-] Anthropic 端點異常，嘗試切換 OpenAI 相容格式測試...")
        openai_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        openai_payload = {
            "model": model,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "ping"}],
        }
        r2 = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=openai_headers,
            json=openai_payload,
            timeout=10,
        )
        print("OpenAI 格式狀態碼:", r2.status_code)
        print("OpenAI 格式返回內容:", r2.text[:300])
except Exception as e:
    print(f"[-] 連線發生異常: {e}")