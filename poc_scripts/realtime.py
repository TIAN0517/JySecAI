#!/usr/bin/env python3
"""
Check for WebSocket, SSE, or other real-time endpoints
"""

import requests
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
r = sess.get(TARGET + "/admin/login")
token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
if token_match:
    token = token_match.group(1)
    r = sess.get(TARGET + "/admin/captcha")
    captcha_match = re.search(r'<text[^>]*>(\w)</text>', r.text)
    if captcha_match:
        captcha = captcha_match.group(1)
        r = sess.post(TARGET + "/admin/login", data={
            'username': 'admin',
            'password': 'admin',
            'captcha': captcha,
            '_token': token
        })
        
        # Check for WebSocket/SSE endpoints
        endpoints = [
            "/ws", "/websocket", "/ws/admin", "/socket", "/sse", "/stream",
            "/live", "/realtime", "/events", "/notifications/stream",
            "/api/stream", "/api/realtime", "/admin/stream", "/admin/ws"
        ]
        
        for endpoint in endpoints:
            try:
                # Try as SSE
                r = sess.get(TARGET + endpoint, stream=True, timeout=5)
                content_type = r.headers.get('Content-Type', '')
                if 'text/event-stream' in content_type:
                    print(f"[SSE] {endpoint}")
                elif 'websocket' in content_type:
                    print(f"[WS] {endpoint}")
            except:
                pass
        
        # Check for long-polling endpoints
        polling_endpoints = [
            "/poll", "/longpoll", "/wait", "/api/poll", "/admin/poll"
        ]
        
        for endpoint in polling_endpoints:
            try:
                r = sess.get(TARGET + endpoint, timeout=5)
                print(f"[POLL] {endpoint}: {r.status_code}")
            except:
                pass