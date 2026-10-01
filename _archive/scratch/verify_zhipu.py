from concurrent.futures import ThreadPoolExecutor
import json
import time
from openai import OpenAI
from tabulate import tabulate

ZHIPU_KEYS = [
    "a24b3819a36c4cdfa14a032fad0caf33.yTB5oTq8OGaotKXyqlcXxuJs",
    "b43525624d584b5d88029a2af9b0063c.xi2HQtJ4PawRz166uq7Oe0E2",
    "c8eb531e54344ca48f818d28be56f103.hVlSyJjeqmtEMMqvq_eEaboG",
    "524b29f428ca40d590a30665c3598a70.mImRcr9A5cEro1273-I5WCba",
    "c8fb31e823694b73aee31c29a5645f81.LB_buTidW6cVxsCBeWoKWTAW",
    "c8677bc08b7e470599d235257d91d1e4.EQD9u6vVOlg49XR0gpJZ6hHF",
    "5895c95063434ee098b44a7def9e35bc.dSPzr1AamB2bJkhL4g0A6al1",
    "dea3fd002c9f414886915c686973b723.RjhXiZvg2UcQ4Hhgrcw4Wd4y",
    "9180dde083604c8cb1815205a09be4bd.R8Xi87W5_koaR7xryouuvLP4",
    "2b1c7c08d2be457ba84034140e42216f.QBC-fizrzRcXlGF-4E2EO21n",
    "5c45f8226ab946d792b0f1dfa7c45c2d.9auVGGcg3M6Sujp7pqISjiNN",
    "55f3c9790137451d93027c317835cabf.4HlSvNQ4nZsqHqsmXQ3k9z7y",
    "80d5957ca32d400a8afc2437785d7bd6.loAKw1CXEl1L0LJyMrNx0xsc",
    "de85c748146f4ac2af589cc0e4919d19.ydsmi6gWDvu7rWlqZTEKEjAe",
    "acf02bf0a00c437e901f6ca9a35f96d6.hsf5uoTKI6DlvJ16-J62upOa",
]

# 智譜官方 OpenAI 相容接口
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
# 官方免費主力模型
MODEL_NAME = "glm-4-flash"


def check_key(key):
    client = OpenAI(base_url=BASE_URL, api_key=key, timeout=8.0)
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": (
                        '嚴格只輸出一段純JSON：{"status":"ok"}，禁止任何其他文字。'
                    ),
                }
            ],
            temperature=0.01,
            max_tokens=20,
        )
        latency = round(time.time() - t0, 2)
        raw_text = resp.choices[0].message.content.strip()
        clean = (
            raw_text.replace("```json", "")
            .replace("```", "")
            .strip()
            .split("\n")[-1]
        )

        data = json.loads(clean)
        if data.get("status") == "ok":
            return [
                key[:10] + "..." + key[-6:],
                "✔ 正常可用",
                f"{latency}s",
                "通過 (全自動入庫)",
            ]
        return [
            key[:10] + "..." + key[-6:],
            "✔ 連通",
            f"{latency}s",
            "格式需正則清洗",
        ]

    except json.JSONDecodeError:
        return [
            key[:10] + "..." + key[-6:],
            "✔ 連通",
            f"{round(time.time() - t0, 2)}s",
            "非純JSON",
        ]
    except Exception as e:
        err = str(e)
        if "401" in err or "1000" in err:
            status = "❌ 密鑰無效/未開通"
        elif "1002" in err or "quota" in err.lower() or "402" in err:
            status = "❌ 額度耗盡/欠費"
        elif "429" in err:
            status = "❌ 請求限流"
        else:
            status = f"❌ 異常({err[:20]}...)"
        return [key[:10] + "..." + key[-6:], status, "-", "無法使用"]


print(f"[*] 正在驗證 15 組智譜 API Key 連通性與 {MODEL_NAME} 推論能力...\n")
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_key, ZHIPU_KEYS))

headers = ["API Key 摘要", "通訊狀態", "延遲", "自動化能力"]
print(tabulate(results, headers=headers, tablefmt="github"))