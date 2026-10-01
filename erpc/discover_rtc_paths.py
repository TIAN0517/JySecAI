import requests, urllib3, json, time, concurrent.futures
urllib3.disable_warnings()

# Load our JWT token
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
jwt_headers = {"Authorization": f"Bearer {token}"}

# All known hosts and ports
hosts = {
    "epcr_4000": "https://epcr.tpf.gov.tw:4000",
    "epcr_4001": "https://epcr.tpf.gov.tw:4001",
    "epcr_4004": "https://epcr.tpf.gov.tw:4004",
    "epcr_4005": "https://epcr.tpf.gov.tw:4005",
    "rtc_443": "https://tpertc.tfd.gov.tw",
    "rtc_8787": "https://tpertc.tfd.gov.tw:8787",
}

# All paths we've discovered
paths = [
    # EPCR 4000
    "/version/", "/config", "/socket.io/?EIO=4&transport=polling",
    "/DispatchRecords", 
    # EPCR 4001
    "/events", "/events/567246",
    # EPCR 4004
    "/login", "/refreshToken", "/config", "/socket.io/?EIO=4&transport=polling",
    # EPCR 4005
    "/config",
    # RTC 443
    "/", "/rtc/", "/rtc/account.php?action=login", "/rtc/api/index.php",
    "/rtc/api/file.php?action=list", "/client/", "/doctor/", "/patient/",
    # RTC 8787
    "/", "/socket.io/?EIO=4&transport=polling", "/getToken", "/getUser",
    "/auth", "/rtc/", "/deactivate",
]

def check_url(url):
    try:
        r = requests.get(url, headers=jwt_headers, verify=False, timeout=10, allow_redirects=False)
        return {
            "url": url,
            "status": r.status_code,
            "preview": r.text[:200].replace('\n', ' ').strip()
        }
    except requests.exceptions.Timeout:
        return {"url": url, "status": "TIMEOUT", "preview": ""}
    except Exception as e:
        return {"url": url, "status": "ERROR", "preview": str(e)[:150]}

# Build all URLs
all_urls = []
for host_name, host_url in hosts.items():
    for path in paths:
        all_urls.append((host_name, f"{host_url}{path}"))

# Use thread pool for parallel testing
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    future_to_info = {executor.submit(check_url, url): (host, url) for host, url in all_urls}
    for future in concurrent.futures.as_completed(future_to_info):
        host, url = future_to_info[future]
        try:
            result = future.result()
            result["host"] = host
            results.append(result)
        except Exception as e:
            results.append({"url": url, "host": host, "status": "ERROR", "preview": str(e)[:150]})

# Sort and print
interesting = [r for r in results if r["status"] not in [404, 400, "TIMEOUT", "ERROR"]]
print("=== 非 404/400/ERROR 結果 ===\n")
for r in sorted(interesting, key=lambda x: x["status"] if isinstance(x["status"], int) else 999):
    print(f"[{r['host']}] {r['url']}")
    print(f"  → Status: {r['status']} | {r['preview'][:300]}")
    print()

print(f"\n=== 計算: {len(interesting)} 個有效路徑, {len(results)} 個總請求 ===")

# Show all timeouts and errors
errors = [r for r in results if r["status"] in ["TIMEOUT", "ERROR"]]
if errors:
    print(f"\n=== 逾時/錯誤 ({len(errors)} 個) ===")
    for r in errors[:10]:
        print(f"[{r['host']}] {r['url']} -> {r['status']}")
