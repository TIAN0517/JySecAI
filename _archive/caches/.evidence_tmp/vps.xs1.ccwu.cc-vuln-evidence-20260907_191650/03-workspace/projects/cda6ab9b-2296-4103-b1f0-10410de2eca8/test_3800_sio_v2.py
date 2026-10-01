"""
V42 - 3800 socket.io 业务事件深探测 v2 (底层 polling 协议)
原因：python-socketio 客户端在 socket.io v3+ 上 OPEN packet 协议不兼容
方案：直接用 requests 模拟 EIO=4 polling：
  1. GET /socket.io/?EIO=4&transport=polling  → 拿 sid + EIO OPEN 包 (0{"sid":...,"upgrades":["websocket"],...})
  2. POST /socket.io/?EIO=4&transport=polling&sid=<sid>  → 发包 (42["eventName",{...}])
  3. GET /socket.io/?EIO=4&transport=polling&sid=<sid>  → 长轮询拿 server-pushed 包
"""
import requests
import json
import time
import sys
import re
import urllib.parse

base_url = "http://35.234.50.28:3800"
socketio_path = "/socket.io/"

# 业务事件候选集
candidate_events = [
    # EPCR 通用业务事件（与 8000/3400 一致）
    "case", "dispatch", "sync", "ambulance", "branch", "device",
    "mci", "hospital", "pcr", "stat",
    # mciServer 特有业务事件
    "ambulance-record", "mci-pcr", "mci-list", "hospital-list",
    "device-role", "hospital-detail", "mci-pcr-stat",
    # 业务事件通用模式
    "client.subscribe", "client.unsubscribe",
    "subscribe", "unsubscribe", "join", "leave",
    # 业务动作
    "new-case", "update-case", "delete-case",
    "new-ambulance-record", "update-ambulance-record",
    "new-mci", "update-mci", "delete-mci",
    # 心跳与握手
    "ping", "pong", "hello", "ready",
]

def parse_engineio_packet(data):
    """解析 EIO=4 包: 0{json}, 40, 42["event",{...}], 4<sid>msg"""
    if not data:
        return None, None, None
    if data.startswith("0"):
        # OPEN packet
        return "open", data, json.loads(data[1:]) if len(data) > 1 else None
    elif data.startswith("40"):
        # MESSAGE packet from server (engine.io message type 4)
        return "msg", data, None
    elif data.startswith("4"):
        # MESSAGE packet from server (4 + socket.io packet type)
        return "msg", data, None
    elif data.startswith("2"):
        # PING
        return "ping", data, None
    elif data.startswith("3"):
        # PONG
        return "pong", data, None
    else:
        return "unknown", data, None

def main():
    print(f"[V42-v2] 3800 socket.io 业务事件深探测 (底层 polling 协议)")
    print(f"[V42-v2] target: {base_url}{socketio_path}")
    print(f"[V42-v2] candidate_events: {len(candidate_events)}")
    print()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "python-requests/2.31.0",
        "Accept": "*/*",
        "Origin": "http://35.234.50.28:3800",
        "Referer": "http://35.234.50.28:3800/client/",
    })

    # Step 1: GET 拿到 sid + OPEN 包
    print(f"[*] Step 1: GET {socketio_path}?EIO=4&transport=polling ...")
    r = session.get(
        f"{base_url}{socketio_path}",
        params={"EIO": "4", "transport": "polling"},
        timeout=10,
    )
    print(f"    status: {r.status_code}")
    print(f"    body: {r.text[:300]}")
    print(f"    cookies: {dict(session.cookies)}")
    print()

    if r.status_code != 200:
        print(f"[FAIL] handshake failed: {r.status_code}")
        sys.exit(1)

    body = r.text
    ptype, pdata, popen = parse_engineio_packet(body)
    if ptype != "open":
        print(f"[FAIL] not OPEN packet: {body[:200]}")
        sys.exit(1)

    sid = popen.get("sid")
    ping_interval = popen.get("pingInterval", 25000) / 1000.0
    ping_timeout = popen.get("pingTimeout", 20000) / 1000.0
    upgrades = popen.get("upgrades", [])
    print(f"[+] OPEN packet received:")
    print(f"    sid: {sid}")
    print(f"    pingInterval: {ping_interval}s")
    print(f"    pingTimeout: {ping_timeout}s")
    print(f"    upgrades: {upgrades}")
    print()

    # Step 2: 发包（engine.io message type 4 = message, socket.io type 2 = event, ["eventName", payload]）
    print(f"[*] Step 2: emit {len(candidate_events)} candidate events ...")
    for ev in candidate_events:
        # 42["eventName",{...}]
        packet = f'42["{ev}",{{"probe":true,"ts":{int(time.time()*1000)}}}]'
        try:
            r = session.post(
                f"{base_url}{socketio_path}",
                params={"EIO": "4", "transport": "polling", "sid": sid},
                data=packet,
                timeout=5,
                headers={"Content-Type": "text/plain;charset=UTF-8"},
            )
            print(f"    [emit] {ev} → status={r.status_code} body={r.text[:80]}")
        except Exception as e:
            print(f"    [emit-fail] {ev} → {e}")
            break

    print()

    # Step 3: 长轮询拿 server-pushed 包（等待 6 秒）
    print(f"[*] Step 3: GET 长轮询 6s 等待 server-pushed events ...")
    received = []
    start = time.time()
    while time.time() - start < 6:
        try:
            r = session.get(
                f"{base_url}{socketio_path}",
                params={"EIO": "4", "transport": "polling", "sid": sid},
                timeout=3,
            )
            if r.status_code == 200 and r.text:
                # 多个 packet 可能在一个 response 里，EIO=4 包长度前缀
                print(f"    [recv] status={r.status_code} body={r.text[:200]}")
                # 解析 packet
                for raw in re.split(r'(?<=})\d+(?=\{)|(?<=\])', r.text):
                    if raw.strip():
                        ptype, pdata, popen = parse_engineio_packet(raw.strip())
                        if ptype in ("msg", "ping", "pong"):
                            received.append((ptype, pdata, popen))
            else:
                # 没有数据时（NOOP）等待
                time.sleep(0.5)
        except requests.exceptions.Timeout:
            # 长轮询超时正常
            continue
        except Exception as e:
            print(f"    [recv-err] {e}")
            break

    print()
    if received:
        print(f"[!] 收到 {len(received)} 个 server-pushed packets:")
        for ptype, pdata, popen in received:
            print(f"    {ptype}: {pdata[:200]}")
    else:
        print(f"[-] 0 server-pushed events（与 8000/3400 一致：服务端单向接收）")

    print(f"\n[V42-v2] done.")

if __name__ == "__main__":
    main()