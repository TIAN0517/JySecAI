import requests, urllib3, json, urllib.parse
urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw"

# Get JWT
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Try PHP API with form data and JWT auth
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Try the resent action with form data
post_data = "doctor=femet&patient=test_patient"
r = requests.post(f"{base}/rtc/api/index.php?action=resent",
    data=post_data, headers=headers, verify=False, timeout=10, allow_redirects=False)
print(f"POST action=resent with doctor/patient: {r.status_code}")
print(f"  Body: {r.text[:300]}")

# Try with different field names
for field_combo in [
    ("user", "pass"),
    ("account", "password"),
    ("account_name", "password"),
    ("username", "password"),
    ("acc", "pw"),
    ("doctor", "patient"),
    ("name", "password"),
    ("id", "token"),
]:
    data = f"{field_combo[0]}=femet&{field_combo[1]}=femet123"
    r = requests.post(f"{base}/rtc/api/index.php?action=login",
        data=data, headers=headers, verify=False, timeout=10, allow_redirects=False)
    print(f"POST action=login with {field_combo[0]}/{field_combo[1]}: {r.status_code}")
    if r.status_code != 200 or "default" not in r.text:
        print(f"  *** Body: {r.text[:300]}")

# Try with JWT in cookie
cookies = {"cool-jwt": token, "login-user": "femet", "display-name": "admin"}
r = requests.post(f"{base}/rtc/api/index.php?action=list",
    data="doctor=femet&patient=test", cookies=cookies, verify=False, timeout=10)
print(f"\nPOST action=list with JWT cookie: {r.status_code}")
print(f"  Body: {r.text[:300]}")

# Try the get_token action with proper params
r = requests.post(f"{base}/rtc/api/index.php?action=get_token",
    data="account_name=femet&password=femet123", headers=headers, verify=False, timeout=10)
print(f"\nPOST action=get_token: {r.status_code}")
print(f"  Body: {r.text[:300]}")

# Try action=user_list, patient_list
for action in ["user_list", "patient_list", "doctor_list", "get_users", "online", "online_users"]:
    r = requests.get(f"{base}/rtc/api/index.php?action={action}", headers=headers, verify=False, timeout=8)
    print(f"GET action={action}: {r.status_code} '{r.text[:100]}'")

print("\nDone")
