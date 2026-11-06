#!/usr/bin/env python3
"""
test_multi_session.py - 反向 Shell 多 session 逻辑测试

不依赖 mcp/yaml 第三方包：若本机缺失则注入最小 stub 后再导入被测模块，
只验证真实的 socket/session 管理逻辑：
  - 握手 token（正确 token 建 session、错误 token 被拒并记录）
  - 多客户端同时进入 session 表
  - send_command 的 session 选择（指定 id / 单 session 自动选用 / 多 session 报错列出 id）
  - 1MB 输出上限
  - 来源 IP 白名单
  - stop_listener 清理

运行：python3 test_multi_session.py
"""

from __future__ import annotations

import re
import socket
import sys
import threading
import time
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _stub_missing_deps() -> None:
    """WSL python3 可能没有 mcp/yaml：注入最小 stub 以便导入被测模块。"""
    try:
        import mcp  # noqa: F401
    except ImportError:
        mcp_mod = ModuleType("mcp")
        server_mod = ModuleType("mcp.server")
        fastmcp_mod = ModuleType("mcp.server.fastmcp")

        class _StubFastMCP:
            def __init__(self, name: str | None = None, instructions: str | None = None):
                self.name = name
                self.instructions = instructions

            def tool(self, description: str | None = None):
                def deco(fn):
                    fn._tool_description = description
                    return fn

                return deco

            def run(self, *args, **kwargs):  # pragma: no cover
                raise RuntimeError("stub FastMCP 不能在测试中 run")

        fastmcp_mod.FastMCP = _StubFastMCP
        mcp_mod.server = server_mod
        server_mod.fastmcp = fastmcp_mod
        sys.modules.setdefault("mcp", mcp_mod)
        sys.modules.setdefault("mcp.server", server_mod)
        sys.modules.setdefault("mcp.server.fastmcp", fastmcp_mod)

    try:
        import yaml  # noqa: F401
    except ImportError:
        sys.modules.setdefault("yaml", ModuleType("yaml"))


_stub_missing_deps()
import mcp_reverse_shell as rs  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_sessions(n: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with rs._LOCK:
            if len(rs._SESSIONS) >= n:
                return True
        time.sleep(0.05)
    return False


def _wait_eof(sock: socket.socket, timeout: float = 5.0) -> bool:
    """等待服务端关闭连接（recv 返回空或报错）。"""
    sock.settimeout(0.2)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if sock.recv(4096) == b"":
                return True
        except socket.timeout:
            continue
        except OSError:
            return True
    return False


def _responder(sock: socket.socket, tag: str, stop: threading.Event) -> None:
    """模拟反弹 shell：收到结束标记后回一段输出 + 标记；tag=BIG 时回 >1MB 数据。"""
    marker = rs._END_MARKER.encode()
    sock.settimeout(0.2)
    while not stop.is_set():
        try:
            data = sock.recv(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        if not data:
            break
        if marker in data:
            payload = b"BIGOUT" * 200000 if tag == "BIG" else f"PONG-{tag}".encode()
            try:
                sock.sendall(payload + b"\n" + marker + b"\n")
            except OSError:
                break
    try:
        sock.close()
    except OSError:
        pass


def main() -> int:
    global PASS, FAIL

    # -- 启动监听，token 应返回给调用者 -----------------------------------
    port = _free_port()
    msg = rs._start_listener(port)
    check("start_listener 成功", rs._LISTENER is not None, msg)
    m = re.search(r"\b[0-9a-f]{32}\b", msg)
    check("start_listener 返回一次性 token", bool(m), msg)
    token = m.group(0) if m else ""
    check("消息中的 token 与内部状态一致", bool(token) and token == rs._AUTH_TOKEN)

    # -- 1. 错误 token 被拒 ------------------------------------------------
    bad = socket.create_connection(("127.0.0.1", port), timeout=5)
    bad.sendall(b"WRONG-TOKEN")
    check("错误 token 连接被断开", _wait_eof(bad))
    bad.close()
    time.sleep(0.2)
    check("错误 token 未进入 session 表", len(rs._SESSIONS) == 0, str(dict(rs._SESSIONS)))
    check("拒绝已记录到事件日志", any("token 不匹配" in e for e in rs._EVENTS))

    # -- 2. 正确 token 建立 session A --------------------------------------
    a = socket.create_connection(("127.0.0.1", port), timeout=5)
    a.sendall(token.encode())
    check("正确 token 建立了 1 个 session", _wait_sessions(1))
    sid_a = next(iter(rs._SESSIONS))
    check("session 记录来源地址", rs._SESSIONS[sid_a]["addr"][0] == "127.0.0.1")

    # -- 3. 第二个客户端 B 同时在表 ----------------------------------------
    b = socket.create_connection(("127.0.0.1", port), timeout=5)
    b.sendall(token.encode())
    check("两个客户端同时在 session 表", _wait_sessions(2))
    sids = sorted(rs._SESSIONS)
    sid_a, sid_b = sids[0], sids[1]
    check("两个 session_id 互不相同", sid_a != sid_b)

    stop_a = threading.Event()
    threading.Thread(target=_responder, args=(a, "A", stop_a), daemon=True).start()
    stop_b = threading.Event()
    threading.Thread(target=_responder, args=(b, "BIG", stop_b), daemon=True).start()

    # -- 4. 多个 session 且未指定 session_id → 报错并列出可选 id ------------
    out = rs._send_command_blocking("id")
    check(
        "多 session 未指定 id 时报错并列出可选 id",
        "错误" in out and sid_a in out and sid_b in out,
        out,
    )

    # -- 5. 指定 session_id 下发命令 ---------------------------------------
    out = rs._send_command_blocking("id", session_id=sid_a)
    check("指定 session_id 收到该 session 输出", "PONG-A" in out, out)

    # -- 6. >1MB 输出被截断到上限 ------------------------------------------
    out = rs._send_command_blocking("id", session_id=sid_b)
    check(
        "超大输出被截断到 1MB 上限",
        "已截断" in out and len(out.encode()) < rs._RECV_MAX_BYTES + 256,
        f"len={len(out.encode())}",
    )

    # -- 7. 断开 B 后，唯一 session 自动选用 --------------------------------
    out = rs._disconnect_session(sid_b)
    check("disconnect 指定 session", sid_b in out, out)
    stop_b.set()
    time.sleep(0.1)
    check("断开后 session 表只剩 A", list(rs._SESSIONS) == [sid_a], str(list(rs._SESSIONS)))
    out = rs._send_command_blocking("id")
    check("单 session 时未传 session_id 自动选用", "PONG-A" in out, out)

    # -- 8. 无效 session_id 报错并列出可用 id -------------------------------
    out = rs._send_command_blocking("id", session_id="sess-9999")
    check("无效 session_id 报错并列出可用", "错误" in out and sid_a in out, out)

    # -- 9. stop_listener 清理 ---------------------------------------------
    out = rs._stop_listener()
    stop_a.set()
    check("stop 后 session 表清空", len(rs._SESSIONS) == 0, out)
    check("stop 后 token 清空", rs._AUTH_TOKEN is None)

    # -- 10. 来源 IP 白名单：127.0.0.1 不在名单 → 直接拒绝（即使 token 正确） -
    port2 = _free_port()
    msg2 = rs._start_listener(port2, allowed_ips=["192.0.2.99"])
    m2 = re.search(r"\b[0-9a-f]{32}\b", msg2)
    check("白名单监听启动并返回 token", bool(m2), msg2)
    c = socket.create_connection(("127.0.0.1", port2), timeout=5)
    if m2:
        c.sendall(m2.group(0).encode())
    check("白名单外来源被拒绝", _wait_eof(c))
    c.close()
    check("白名单拒绝已记录", any("不在白名单" in e for e in rs._EVENTS))
    rs._stop_listener()

    print()
    print(f"结果: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
