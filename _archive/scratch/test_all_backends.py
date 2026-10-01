import json
import time
from openai import OpenAI
import requests

# 待驗證清單
TEST_TARGETS = [
    {
        "name": "Claude 3.5 Sonnet (CZC 中轉站)",
        "type": "anthropic_proxy",
        "url": "https://czc.zh.kg/v1",
        "key": (
            "sk-376ca36fa6090758abb0634d61412c0fade52b0729b219ce3afc4ba3ec58b4a"
        ),
        "model": "claude-3-5-sonnet-20241022",
    },
    {
        "name": "Claude 3.5 (OpenAI 相容協議回退測試)",
        "type": "openai",
        "url": "https://czc.zh.kg/v1",
        "key": (
            "sk-376ca36fa6090758abb0634d61412c0fade52b0729b219ce3afc4ba3ec58b4a"
        ),
        "model": "claude-3-5-sonnet-20241022",
    },
    {
        "name": "智譜/中轉 3a19f...",
        "type": "zhipu",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key": "3a19f2f0c4044bbf9bd8daa88cde4390.IGdXlv8cQonyTbDSGSWJX5qq",
        "model": "glm-4-flash",
    },
    {
        "name": "NVIDIA NIM (主控測試)",
        "type": "openai",
        "url": "https://integrate.api.nvidia.com/v1",
        "key": (
            "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"
        ),
        "model": "meta/llama-3.3-70b-instruct",
    },
]


def run_test(target):
    name = target["name"]
    t_type = target["type"]
    url = target["url"]
    key = target["key"]
    model = target["model"]

    print(f"\n[*] 正在測試: {name} ({model})")
    t0 = time.time()

    try:
        if t_type == "anthropic_proxy":
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 60,
                "messages": [
                    {
                        "role": "user",
                        "content": '輸出純JSON：{"status":"ready"}，不要額外文字。',
                    }
                ],
            }
            r = requests.post(
                f"{url.rstrip('/')}/messages",
                headers=headers,
                json=payload,
                timeout=12,
            )
            latency = round(time.time() - t0, 2)

            if r.status_code == 200:
                content = (
                    r.json()
                    .get("content", [{}])[0]
                    .get("text", "")
                    .strip()
                )
                print(f"    ✔ 連通成功 (HTTP 200, 耗時: {latency}s)")
                print(f"    響應內容: {content}")
            else:
                print(f"    ❌ 失敗 (HTTP {r.status_code}) - {r.text[:150]}")

        elif t_type == "openai":
            client = OpenAI(base_url=url, api_key=key, timeout=12.0)
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": '輸出純JSON：{"status":"ready"}，不要額外文字。',
                    }
                ],
                max_tokens=60,
            )
            latency = round(time.time() - t0, 2)
            content = res.choices[0].message.content.strip()
            print(f"    ✔ 連通成功 (OpenAI 相容, 耗時: {latency}s)")
            print(f"    響應內容: {content}")

        elif t_type == "zhipu":
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": '輸出純JSON：{"status":"ready"}，不要額外文字。',
                    }
                ],
                "max_tokens": 60,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=12)
            latency = round(time.time() - t0, 2)

            if r.status_code == 200:
                content = (
                    r.json()["choices"][0]["message"]["content"].strip()
                )
                print(f"    ✔ 連通成功 (HTTP 200, 耗時: {latency}s)")
                print(f"    響應內容: {content}")
            else:
                print(f"    ❌ 失敗 (HTTP {r.status_code}) - {r.text[:150]}")

    except Exception as err:
        print(f"    ❌ 連線例外: {err}")


for item in TEST_TARGETS:
    run_test(item)