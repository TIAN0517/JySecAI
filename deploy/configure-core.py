#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import yaml


def mapping(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("runtime_root", type=Path)
    parser.add_argument("--new-install", action="store_true")
    args = parser.parse_args()

    with args.config.open("r", encoding="utf-8") as source:
        data = yaml.safe_load(source) or {}
    if not isinstance(data, dict):
        raise ValueError("Core configuration root must be a mapping")

    runtime = str(args.runtime_root)
    state = "/var/lib/jysecai/core"
    server = mapping(data, "server")
    server.update({"host": "127.0.0.1", "port": 8080, "tls_enabled": False})
    server["tls_auto_self_sign"] = False

    database = mapping(data, "database")
    database["path"] = f"{state}/conversations.db"
    database["knowledge_db_path"] = f"{state}/knowledge.db"
    mapping(data, "security")["tools_dir"] = f"{runtime}/tools"
    mapping(data, "knowledge")["base_path"] = f"{runtime}/knowledge_base"
    data["skills_dir"] = f"{runtime}/skills"
    data["agents_dir"] = f"{runtime}/agents"
    data["roles_dir"] = f"{runtime}/roles"

    agent = mapping(data, "agent")
    agent["workspace_root_dir"] = f"{state}/workspace"

    # PyYAML follows YAML 1.1 and parses an unquoted `off` as boolean false.
    # The Go application expects the explicit HITL mode string.
    hitl = mapping(data, "hitl")
    if hitl.get("default_mode") is False:
        hitl["default_mode"] = "off"

    # Seed the SOCKS5 pool only once. Later edits made through the JySecAI
    # settings page are preserved by subsequent deployments.
    if not isinstance(data.get("proxy_pool"), dict):
        data["proxy_pool"] = {
            "enabled": True,
            "strategy": "round_robin",
            "health_check_url": "https://api.ipify.org",
            "connect_timeout_seconds": 8,
            "request_timeout_seconds": 15,
            "failure_threshold": 2,
            "cooldown_seconds": 60,
            "proxies": [
                {"name": "s5-154", "url": "socks5://202.160.76.154:11085", "enabled": True},
                {"name": "s5-155", "url": "socks5://202.160.76.155:11084", "enabled": True},
                {"name": "s5-156", "url": "socks5://202.160.76.156:11083", "enabled": True},
                {"name": "s5-157", "url": "socks5://202.160.76.157:11082", "enabled": True},
                {"name": "s5-165", "url": "socks5://202.160.76.165:11081", "enabled": True},
                {"name": "s5-166", "url": "socks5://202.160.76.166:11086", "enabled": True},
                {"name": "s5-167", "url": "socks5://202.160.76.167:1080", "enabled": True},
                {"name": "s5-168", "url": "socks5://202.160.76.168:1080", "enabled": True},
                {"name": "s5-169", "url": "socks5://202.160.76.169:1080", "enabled": True},
                {"name": "s5-173", "url": "socks5://202.160.76.173:1080", "enabled": True},
                {"name": "s5-221", "url": "socks5://202.160.76.221:1080", "enabled": True},
                {"name": "s5-223", "url": "socks5://202.160.76.223:1080", "enabled": True},
            ],
        }
    multi_agent = mapping(data, "multi_agent")
    middleware = mapping(multi_agent, "eino_middleware")
    middleware["reduction_root_dir"] = f"{state}/workspace/.jysec/reduction"

    if args.new_install:
        mapping(data, "c2")["enabled"] = False

    servers = mapping(mapping(data, "external_mcp"), "servers")
    servers["hexstrike-ai"] = {
        "type": "stdio",
        "command": "/opt/jysecai/hexstrike-ai/hexstrike-env/bin/python",
        "args": [
            "/opt/jysecai/hexstrike-ai/hexstrike_mcp.py",
            "--server",
            "http://127.0.0.1:8888",
        ],
        "description": "HexStrike AI security tools through the local JySec backend",
        "timeout": 300,
        "terminate_duration": 10,
        "external_mcp_enable": True,
        "autoApprove": [],
    }
    servers["kali-mcp"] = {
        "type": "stdio",
        "command": "/opt/jysecai/MCP-Kali-Server/mcp-env/bin/python",
        "args": [
            "/opt/jysecai/MCP-Kali-Server/mcp-server/mcp_server.py",
            "--server",
            "http://127.0.0.1:5000",
        ],
        "env": {"KALI_SERVER_URL": "http://127.0.0.1:5000"},
        "description": "Kali security tools through the local JySec backend",
        "timeout": 300,
        "terminate_duration": 10,
        "external_mcp_enable": True,
        "autoApprove": [],
    }
    existing_vuln_intel = servers.get("vuln-intel")
    vuln_intel_env = {}
    if isinstance(existing_vuln_intel, dict) and isinstance(existing_vuln_intel.get("env"), dict):
        # Preserve optional operator-supplied NVD/GitHub credentials on upgrade.
        vuln_intel_env = existing_vuln_intel["env"]
    servers["vuln-intel"] = {
        "type": "stdio",
        "command": "/opt/jysecai/core/venv/bin/python",
        "args": [
            "/opt/jysecai/core/current/mcp-servers/vuln_intel/mcp_vuln_intel.py",
        ],
        "env": vuln_intel_env,
        "description": "Read-only NVD, CISA KEV, EPSS, OSV, ExploitDB and public POC intelligence",
        "timeout": 90,
        "terminate_duration": 10,
        "external_mcp_enable": True,
        "autoApprove": [],
    }
    servers["redteam-knowledge"] = {
        "type": "stdio",
        "command": "/opt/jysecai/core/venv/bin/python",
        "args": [
            "/opt/jysecai/core/current/mcp-servers/redteam_knowledge/mcp_redteam_knowledge.py",
        ],
        "description": "Read-only MITRE ATT&CK, LOLBAS, GTFOBins and Atomic Red Team knowledge",
        "timeout": 120,
        "terminate_duration": 10,
        "external_mcp_enable": True,
        "autoApprove": [],
    }

    fd, temporary = tempfile.mkstemp(prefix="core-config-", suffix=".yaml", dir=args.config.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            yaml.safe_dump(data, output, allow_unicode=True, sort_keys=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, args.config)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == "__main__":
    main()
