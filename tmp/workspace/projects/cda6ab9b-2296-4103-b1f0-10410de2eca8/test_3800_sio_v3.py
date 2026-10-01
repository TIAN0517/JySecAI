"""
V42 - 3800 socket.io 业务事件深探测 v3 (修复版)
关键修复：EIO=4 polling 响应是 socket.io 复合包格式：
  97:0{"sid":"...","upgrades":["websocket"],...}2:40
其中：
  "97:" 是 socket.io packet 长度前缀（97 字符）
  "0" 是 socket.io packet type 0=CONNECT
  紧跟 "{\"sid\":\"...\",...}" CONNECT payload
  紧跟 "2:40" 下一个包：长度 2 + 内容 "40"（engine.io 4=MESSAGE + socket.io 0=CONNECT-ACK 嵌套）
正确解析逻辑：
  1. 剥离长度前缀 (数字:)
  2. 第一个字符是 socket.io packet type
  3. 之后按 socket.io packet type 解析：
     - 0=CONNECT: 后跟 JSON payload (含 sid/pingInterval/pingTimeout)
     - 1=DISCONNECT: 后跟 reason
     - 2=EVENT: 后跟 JSON array ["eventName", payload, ...]
     - 3=ACK: 后跟 JSON [ackId, data]
     - 4=ERROR: 后跟 error info
     - 5=BINARY_EVENT: 同 2 但有 binary placeholders
     - 6=BINARY_ACK: 同 3 但有 binary placeholders
  4. engine.io 类型嵌入在 socket.io 内层 packet type 之后（"40"=4=MESSAGE+0=CONNECT-ACK）
  5. 客户端需要立即回复 CONNECT-ACK: 4{"sid":<sid>}
"""
import requests
import json
import time
import sys
import re

base_url = "http://35.234.50.28:3800"
socketio_path = "/socket.io/"

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

# socket.io packet type 映射
SIO_PACKET_TYPES = {
    "0": "CONNECT",
    "1": "DISCONNECT",
    "2": "EVENT",
    "3": "ACK",
    "4": "ERROR",
    "5": "BINARY_EVENT",
    "6": "BINARY_ACK",
}

# engine.io packet type 映射 (在 socket.io packet type 后)
EIO_PACKET_TYPES = {
    "0": "OPEN",
    "1": "CLOSE",
    "2": "PING",
    "3": "PONG",
    "4": "MESSAGE",
    "5": "UPGRADE",
    "6": "NOOP",
}

def parse_socketio_packets(body):
    """
    解析 socket.io v3+ 复合包格式:
      <length>:<packet><next_length>:<next_packet>...
    例子: "97:0{...}2:40"
    """
    packets = []
    i = 0
    while i < len(body):
        # 找到冒号
        colon = body.find(":", i)
        if colon == -1:
            break
        # 长度前缀
        try:
            plen = int(body[i:colon])
        except ValueError:
            packets.append(("RAW", body[i:]))
            break
        # 包内容
        start = colon + 1
        end = start + plen
        if end > len(body):
            packets.append(("INCOMPLETE", body[i:]))
            break
        pkt = body[start:end]
        packets.append(("OK", pkt))
        i = end
    return packets

def parse_sio_packet(pkt):
    """解析单个 socket.io packet"""
    if not pkt:
        return ("EMPTY", None)
    sio_type = pkt[0]
    rest = pkt[1:]
    sio_name = SIO_PACKET_TYPES.get(sio_type, f"UNKNOWN({sio_type})")

    # CONNECT (0) / DISCONNECT (1) / ACK (3) / ERROR (4) / BINARY_ACK (6) 后续都是 JSON
    # EVENT (2) / BINARY_EVENT (5) 后续是 JSON array
    try:
        if sio_type in ("0", "1", "3", "4"):
            payload = json.loads(rest) if rest else None
            return (sio_name, payload)
        elif sio_type in ("2", "5"):
            payload = json.loads(rest) if rest else None
            return (sio_name, payload)
        else:
            return (sio_name, rest)
    except (json.JSONDecodeError, ValueError) as e:
        return (sio_name + "_PARSE_ERR", (rest, str(e)))

def main():
    print(f"[V42-v3] 3800 socket.io 业务事件深探测 (修复版)")
    print(f"[V42-v3] target: {base_url}{socketio_path}")
    print(f"[V42-v3] candidate_events: {len(candidate_events)}")
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
    packets = parse_socketio_packets(body)
    print(f"[*] Parsed {len(packets)} packets from handshake:")
    sid = None
    for status, pkt in packets:
        name, payload = parse_sio_packet(pkt)
        print(f"    [{status}] packet={pkt[:100]} type={name} payload={payload}")
        if name == "CONNECT" and isinstance(payload, dict):
            sid = payload.get("sid")
    print()

    if not sid:
        print(f"[FAIL] no sid received from CONNECT packet")
        sys.exit(1)

    print(f"[+] sid = {sid}")
    print()

    # Step 2: 发送 CONNECT-ACK (engine.io 4=MESSAGE + socket.io 0=CONNECT)
    # 这是 EIO=4 polling 的要求
    print(f"[*] Step 2: send CONNECT-ACK (4{{\"sid\":\"{sid}\"}}) ...")
    ack = f'4{{"sid":"{sid}"}}'
    r = session.post(
        f"{base_url}{socketio_path}",
        params={"EIO": "4", "transport": "polling", "sid": sid},
        data=f"{len(ack)}:{ack}",
        timeout=5,
        headers={"Content-Type": "text/plain;charset=UTF-8"},
    )
    print(f"    CONNECT-ACK status: {r.status_code} body: {r.text[:100]}")
    print()

    # Step 3: emit 35 个候选事件
    print(f"[*] Step 3: emit {len(candidate_events)} candidate events ...")
    for ev in candidate_events:
        # 42["eventName", payload]  (engine.io 4=MESSAGE + socket.io 2=EVENT)
        packet_data = json.dumps([ev, {"probe": True, "ts": int(time.time()*1000)}])
        # socket.io packet: 2<packet_data>  → engine.io wrap: 4<sio_packet>
        sio_packet = "2" + packet_data
        eio_packet = "4" + sio_packet
        prefixed = f"{len(eio_packet)}:{eio_packet}"
        try:
            r = session.post(
                f"{base_url}{socketio_path}",
                params={"EIO": "4", "transport": "polling", "sid": sid},
                data=prefixed,
                timeout=5,
                headers={"Content-Type": "text/plain;charset=UTF-8"},
            )
            ok = (r.status_code == 200)
            print(f"    [emit] {ev} → status={r.status_code} ok={ok} body={r.text[:60]}")
        except Exception as e:
            print(f"    [emit-fail] {ev} → {e}")
            break

    print()

    # Step 4: 长轮询 6s 等待 server-pushed events
    print(f"[*] Step 4: 长轮询 6s 等待 server-pushed events ...")
    received_packets = []
    start = time.time()
    while time.time() - start < 6:
        try:
            r = session.get(
                f"{base_url}{socketio_path}",
                params={"EIO": "4", "transport": "polling", "sid": sid},
                timeout=4,
            )
            if r.status_code == 200 and r.text and r.text != "":
                pkts = parse_socketio_packets(r.text)
                for status, pkt in pkts:
                    name, payload = parse_sio_packet(pkt)
                    if name in ("EVENT", "BINARY_EVENT"):
                        # 解析 event name
                        try:
                            arr = payload
                            ev_name = arr[0] if isinstance(arr, list) and len(arr) > 0 else None
                            print(f"    [recv-event] {ev_name} payload={arr[1:]}")
                        except:
                            print(f"    [recv-event] payload={payload}")
                    received_packets.append((name, payload, pkt))
                if not pkts:
                    print(f"    [recv] status={r.status_code} body={r.text[:200]}")
            else:
                time.sleep(0.3)
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"    [recv-err] {e}")
            break

    print()
    if received_packets:
        print(f"[!] 收到 {len(received_packets)} 个 server-pushed packets:")
        for name, payload, pkt in received_packets:
            print(f"    type={name} payload={payload}")
    else:
        print(f"[-] 0 server-pushed events（与 8000/3400 一致：服务端单向接收）")

    print(f"\n[V42-v3] done.")

if __name__ == "__main__":
    main()