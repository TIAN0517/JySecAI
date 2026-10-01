"""
V42 - 3800 mciServer socket.io 业务事件深探测
复用 8000/3400 测试模式：仅 / namespace 探测 + 候选业务事件名批量 emit + 长轮询等待
目标：35.234.50.28:3800/socket.io/?EIO=4&transport=polling
"""
import socketio
import time
import sys

# 业务事件候选集（基于 V40 lazy chunk 暴露的 component 名反推）
candidate_events = [
    # EPCR 通用业务事件（与 8000/3400 一致）
    "case", "dispatch", "sync", "ambulance", "branch", "device",
    "mci", "hospital", "pcr", "stat",
    # mciServer 特有业务事件（基于 8 个业务模块）
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

base_url = "http://35.234.50.28:3800"
sid_received = []

def main():
    print(f"[V42] 3800 socket.io 业务事件深探测")
    print(f"[V42] target: {base_url}/socket.io/")
    print(f"[V42] candidate_events: {len(candidate_events)}")
    print()

    try:
        sio = socketio.Client(logger=False, engineio_logger=False)
    except Exception as e:
        print(f"[FAIL] socketio init: {e}")
        sys.exit(1)

    @sio.event
    def connect():
        print(f"[+] CONNECTED sid={sio.sid}")

    @sio.event
    def disconnect():
        print(f"[-] DISCONNECTED")

    @sio.on("*")
    def catch_all(event, *args):
        print(f"[!] catch_all event={event} args={args}")
        sid_received.append((event, args))

    try:
        # EIO=4 polling
        sio.connect(
            f"{base_url}/socket.io/",
            transports=["polling"],
            wait_timeout=10,
            socketio_path="/socket.io/",
        )
        print(f"[+] connected, sid={sio.sid}")

        # 探测每个候选事件
        for ev in candidate_events:
            try:
                sio.emit(ev, {"probe": True, "ts": time.time()})
                print(f"[emit] {ev} → ack pending")
            except Exception as e:
                print(f"[emit-fail] {ev} → {e}")
                break

        # 等待 6 秒观察 server-pushed events
        print(f"\n[*] 等待 6s 观察 server-pushed events ...")
        time.sleep(6)

        if sid_received:
            print(f"\n[!] 收到 {len(sid_received)} 个 server-pushed events")
            for ev, args in sid_received:
                print(f"    event={ev} args={args}")
        else:
            print(f"\n[-] 0 server-pushed events（与 8000/3400 一致：服务端单向接收）")

        sio.disconnect()

    except Exception as e:
        print(f"[FAIL] socket.io error: {e}")
        sys.exit(1)

    print(f"\n[V42] done.")

if __name__ == "__main__":
    main()
