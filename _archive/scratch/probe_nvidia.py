import time
import requests

API_KEY = (
    "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"
)
BASE_URL = "https://integrate.api.nvidia.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

print("[*] 正在從 NVIDIA NIM 獲取所有在線模型註冊清單...")
try:
    resp = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10)
    all_models = [m["id"] for m in resp.json().get("data", [])]
except Exception as e:
    print(f"[-] 獲取模型清單失敗: {e}")
    exit()

print(f"[*] 獲取到 {len(all_models)} 個註冊端點，開始自動探測真實可用的 2 款模型...\n")

working_models = []

for model_id in all_models:
    # 快速排除非文本生成端點
    if any(
        x in model_id.lower()
        for x in ["embed", "rerank", "whisper", "audio", "vision", "reward"]
    ):
        continue

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": '{"test":"ok"}'}],
        "max_tokens": 10,
        "temperature": 0.0,
    }

    t0 = time.time()
    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=4.0,  # 4 秒快速超時，不卡頓
        )
        latency = round(time.time() - t0, 2)

        if r.status_code == 200:
            print(f"✔ 找到可用模型: {model_id} (延遲: {latency}s)")
            working_models.append(model_id)
            if len(working_models) >= 2:
                break
        else:
            print(f"[-] 跳過 {model_id} (HTTP {r.status_code})")
    except requests.exceptions.Timeout:
        print(f"[-] 超時跳過: {model_id}")
    except Exception as e:
        print(f"[-] 異常跳過: {model_id} ({e})")

print("\n" + "=" * 50)
if len(working_models) >= 2:
    print(f"[+] 成功鎖定 2 款當前可用模型：")
    print(f"    1. 主力決策: {working_models[0]}")
    print(f"    2. 審計過濾: {working_models[1]}")
else:
    print("[-] 未能探測到 2 款可用模型，請檢查返回狀態碼。")
print("=" * 50)