#!/usr/bin/env python3
"""
:3100 socket.io v3 protocol probe - test if server can detect & reject v3 client
socket.io v3 uses EIO=3 + different handshake format
"""
import socket
import time
import urllib.request

TARGET = "35.234.50.28"
PORT = 3100

def test_v3():
    print("=" * 70)
    print(f"[:3100] socket.io v3 protocol probe (EIO=3)")
    print("=" * 70)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((TARGET, PORT))

    # v3 polling handshake
    req = (
        f"GET /socket.io/?EIO=3&transport=polling HTTP/1.1\r\n"
        f"Host: {TARGET}:{PORT}\r\n"
        f"User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36\r\n"
        f"Accept: */*\r\n"
        f"Origin: http://127.0.0.1:18080\r\n"
        f"Referer: http://127.0.0.1:18080/csws_poc.html\r\n"
        f"Sec-Fetch-Dest: empty\r\n"
        f"Sec-Fetch-Mode: cors\r\n"
        f"Sec-Fetch-Site: cross-site\r\n"
        f"Sec-Ch-Ua: \"Chromium\";v=\"151\", \"Not_A Brand\";v=\"99\"\r\n"
        f"Sec-Ch-Ua-Mobile: ?0\r\n"
        f"Sec-Ch-Ua-Platform: \"Linux\"\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )

    print(f"[*] Sending v3 handshake...")
    s.sendall(req.encode())

    response = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response and b"0" in response[-100:]:
                # Get body up to the packet boundary
                pass
            if len(response) > 4096:
                break
    except socket.timeout:
        pass

    print(f"[*] Response ({len(response)} bytes):")
    print(response.decode('latin-1')[:1500])
    print("---")
    s.close()

def test_v4_with_post():
    print("=" * 70)
    print(f"[:3100] v4 polling - second GET after handshake")
    print("=" * 70)

    # Step 1: handshake to get sid
    import re
    url = f"http://{TARGET}:{PORT}/socket.io/?EIO=4&transport=polling"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Origin": "http://127.0.0.1:18080",
        "Referer": "http://127.0.0.1:18080/csws_poc.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Ch-Ua": '"Chromium";v="151", "Not_A Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode('utf-8')
        cookies = r.headers.get_all('Set-Cookie')
        print(f"[*] Handshake status={r.status} body={body[:200]}")
        print(f"[*] Set-Cookie: {cookies}")

    # extract sid
    m = re.search(r'"sid":"([^"]+)"', body)
    if not m:
        print("[-] no sid")
        return
    sid = m.group(1)
    print(f"[+] sid: {sid}")

    # Step 2: send '40' (engine.io OPEN message) via POST
    # v4 polling client first POSTs '0' for engine.io handshake
    # server expects '40' (engine.io OPEN ack) on second POST
    print(f"\n[*] Step 2: POST second poll with engine.io OPEN frame")
    url2 = f"http://{TARGET}:{PORT}/socket.io/?EIO=4&transport=polling&sid={sid}"
    headers2 = dict(headers)
    headers2["Content-Type"] = "text/plain;charset=UTF-8"
    data = b"40"  # engine.io OPEN message
    req2 = urllib.request.Request(url2, data=data, headers=headers2, method='POST')
    try:
        with urllib.request.urlopen(req2, timeout=10) as r2:
            print(f"[+] POST status={r2.status}")
            print(f"[+] POST headers: {dict(r2.headers)}")
            print(f"[+] POST body: {r2.read()[:500]}")
    except Exception as e:
        print(f"[-] POST error: {e}")

    # Step 3: GET the response from the second poll
    print(f"\n[*] Step 3: GET second poll to see server's response")
    try:
        with urllib.request.urlopen(req, timeout=10) as r3:
            print(f"[+] GET status={r3.status}")
            print(f"[+] GET body: {r3.read()[:500]}")
    except Exception as e:
        print(f"[-] GET error: {e}")


if __name__ == "__main__":
    test_v3()
    print()
    test_v4_with_post()