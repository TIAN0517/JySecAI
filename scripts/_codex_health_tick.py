#!/usr/bin/env python3
"""One health tick: codex-bridge + recent jysec-core error signals."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

TOKEN = "jysec-codex-bridge"
BRIDGE = "http://127.0.0.1:18787"


def sh(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=20)
    except subprocess.CalledProcessError as e:
        return e.output or str(e)
    except Exception as e:
        return f"ERR {e}"


def bridge_health() -> dict:
    out = {"ok": False}
    try:
        req = urllib.request.Request(
            f"{BRIDGE}/v1/health",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            body = json.loads(r.read().decode())
            out.update(ok=True, status=r.status, body=body)
    except Exception as e:
        out["error"] = str(e)
    return out


def systemd_status() -> dict:
    text = sh(["systemctl", "--user", "is-active", "codex-bridge.service"]).strip()
    return {"active": text}


def recent_core_hits(since: str = "75 seconds ago") -> list[str]:
    text = sh(
        [
            "journalctl",
            "-u",
            "jysec-core",
            "--since",
            since,
            "--no-pager",
            "-o",
            "short-iso",
        ]
    )
    needles = (
        "empty_model_output",
        "model output rejected by ShouldRetry",
        "Invalid schema for function",
        "codex subscription error",
        "cybersecurity risk",
        "Daybreak isn't available",
        "批量任務執行失敗",
        "批量任务执行失败",
        "eino stream recv error",
        "failover ChatModel",
        "agentic model failover",
        "502 Bad Gateway",
    )
    hits = []
    for line in text.splitlines():
        if any(n in line for n in needles):
            # Already-fixed broken-worker window (NameError residue).
            if "sanitize_tools" in line or "write_out" in line or "codex worker failed: r: name" in line:
                continue
            hits.append(line[:320])
    return hits[-12:]


def recent_bridge_hits(since: str = "75 seconds ago") -> list[str]:
    text = sh(
        [
            "journalctl",
            "--user-unit",
            "codex-bridge.service",
            "--since",
            since,
            "--no-pager",
            "-o",
            "short-iso",
        ]
    )
    needles = ("worker fail", "Traceback", "error", "Daybreak", "schema", "fail")
    # Ignore already-fixed broken-worker residue.
    ignore = ("sanitize_tools", "write_out", "NameError")
    hits = []
    for line in text.splitlines():
        low = line.lower()
        if any(n.lower() in low for n in needles) and not any(i in line for i in ignore):
            hits.append(line[:320])
    return hits[-8:]


def main() -> None:
    health = bridge_health()
    unit = systemd_status()
    core = recent_core_hits()
    bridge = recent_bridge_hits()
    severity = "ok"
    if not health.get("ok") or unit.get("active") != "active":
        severity = "critical"
    elif core or any("worker fail" in h or "Traceback" in h for h in bridge):
        severity = "warn"

    payload = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "severity": severity,
        "bridge": health,
        "systemd": unit,
        "core_hits": core,
        "bridge_hits": bridge,
    }
    # Only wake the agent on warn/critical; ok ticks stay quiet heartbeats.
    prefix = (
        "AGENT_LOOP_TICK_codex_watch"
        if severity != "ok"
        else "AGENT_LOOP_HEARTBEAT_codex_watch"
    )
    print(prefix + " " + json.dumps(payload, ensure_ascii=False), flush=True)
    print(
        f"summary severity={severity} systemd={unit.get('active')} "
        f"bridge_ok={health.get('ok')} core_hits={len(core)} bridge_hits={len(bridge)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
