#!/usr/bin/env python3
"""Kali GPT - offline autonomous-pentest REASONING MCP for JySecAI.

Re-implements the OBSERVE -> THINK -> ACT -> LEARN loop of the upstream
`kali-gpt` project (https://github.com/alishahid74/kali-gpt) as MCP tools:

* ATT&CK mapping of every planned tool invocation (curated offline table).
* Dynamic tool-chain selection driven by discovered findings.
* Persistent engagement memory (target fingerprints + tool success rates).
* PTES-phased methodology planning.

安全契約（safety contract）
---------------------------
本模組是 **planner only**：

* 不會啟動任何子行程、不做 socket 連線、沒有任何網路 I/O。
* 不會對任何目標做掃描、列舉或利用。
* `command_template` 只是一串含 `{target}` / `{port}` 之類佔位符的**範本**，
  伺服器永遠不會代入真實目標，也永遠不會執行它。
* 真正的執行權歸 JySecAI：必須同時通過 HITL 人工審批卡與 scope registry
  授權（scope_targets + action_class）才會真正落地。
* 所有輸出皆為確定性（deterministic）結果，方便測試與重現。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP as _MCPServer


PROVIDER = "curated-offline-rule-engine"
TECHNIQUE_SOURCE = "curated-offline"
UNKNOWN_TACTIC = "unknown"
MEMORY_DB_ENV = "KALI_GPT_MEMORY_DB"
MAX_NOTES_CHARS = 2000
MAX_FINGERPRINT_CHARS = 256
MAX_TOOL_CHARS = 128
MAX_TECHNIQUE_CHARS = 32
MAX_TAGS = 16
MAX_TAG_CHARS = 64
MAX_ROWS = 100
VALID_OUTCOMES = ("success", "failure", "partial")
DEFAULT_OUTCOME = "partial"

EXECUTION_POLICY = (
    "Planning only. This MCP never executes commands, never contacts a target and performs no network I/O. "
    "Every command_template is a non-executed placeholder string. Running one requires the JySecAI tool path: "
    "(1) the HITL approval gate must approve the call, and (2) the scope registry must authorize the target and "
    "the action class (credential_enum / bulk_scan / arbitrary are never implicit). "
    "Templates are conservative defaults only and must be reviewed against the engagement rules of engagement."
)


def _entry(
    tactic: str,
    technique_id: str,
    technique_name: str,
    rationale: str,
    related: tuple[tuple[str, str, str], ...] = (),
) -> dict[str, Any]:
    """組出單筆 curated ATT&CK 條目。"""
    return {
        "tactic": tactic,
        "technique_id": technique_id,
        "technique_name": technique_name,
        "rationale": rationale,
        "related": [
            {"technique_id": rid, "technique_name": rname, "tactic": rtactic}
            for rid, rname, rtactic in related
        ],
    }


# ---------------------------------------------------------------------------
# Curated MITRE ATT&CK enterprise mapping (離線、唯讀、無網路)
# ---------------------------------------------------------------------------
_MITRE_TABLE: dict[str, dict[str, Any]] = {
    # ---- 網路掃描 / 主動偵測 ---------------------------------------------
    "nmap": _entry(
        "discovery", "T1046", "Network Service Discovery",
        "nmap 對目標做主動連線探測並列舉開放埠與服務版本，屬於 Discovery 戰術的服務發現。",
        (("T1595", "Active Scanning", "reconnaissance"),
         ("T1018", "Remote System Discovery", "discovery"),
         ("T1082", "System Information Discovery", "discovery")),
    ),
    "masscan": _entry(
        "reconnaissance", "T1595", "Active Scanning",
        "masscan 以大量 SYN 探測大範圍位址，屬於針對目標的主動掃描。",
        (("T1046", "Network Service Discovery", "discovery"),
         ("T1595.002", "Vulnerability Scanning", "reconnaissance")),
    ),
    "rustscan": _entry(
        "discovery", "T1046", "Network Service Discovery",
        "rustscan 先做快速連線埠過濾再交給 nmap 深掃，本質是服務發現。",
        (("T1595", "Active Scanning", "reconnaissance"),),
    ),
    "testssl-sh": _entry(
        "reconnaissance", "T1592", "Gather Victim Host Information",
        "testssl.sh 蒐集目標的 TLS 憑證、協定版本與組態弱點，屬於蒐集受害者主機資訊。",
        (("T1040", "Network Sniffing", "credential-access"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    "openssl": _entry(
        "reconnaissance", "T1592", "Gather Victim Host Information",
        "openssl s_client 用於取得憑證鏈與協定協商細節，是被動式資訊蒐集。",
        (("T1040", "Network Sniffing", "credential-access"),),
    ),
    # ---- Web 蒐集 / 指紋 -------------------------------------------------
    "whatweb": _entry(
        "reconnaissance", "T1592", "Gather Victim Host Information",
        "whatweb 辨識 Web 技術棧、伺服器版本與前端框架，是典型的受害者資訊蒐集。",
        (("T1591", "Gather Victim Org Information", "reconnaissance"),
         ("T1518", "Software Discovery", "discovery"),
         ("T1580", "Cloud Infrastructure Discovery", "reconnaissance")),
    ),
    "nikto": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "nikto 對公開 Web 服務做組態與已知弱點檢查，位在初始存取階段的弱點驗證。",
        (("T1595.002", "Vulnerability Scanning", "reconnaissance"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "gobuster": _entry(
        "reconnaissance", "T1595.003", "Wordlist Scanning",
        "gobuster 以字典檔枚舉 Web 路徑，屬於字典掃描式蒐集。",
        (("T1595", "Active Scanning", "reconnaissance"),
         ("T1087", "Account Discovery", "discovery")),
    ),
    "ffuf": _entry(
        "reconnaissance", "T1595.003", "Wordlist Scanning",
        "ffuf 以字典檔 fuzz 目錄與參數，同屬字典掃描。",
        (("T1595", "Active Scanning", "reconnaissance"),),
    ),
    "dirb": _entry(
        "reconnaissance", "T1595.003", "Wordlist Scanning",
        "dirb 為字典式 Web 目錄枚舉工具，映射到 Wordlist Scanning。",
        (("T1595", "Active Scanning", "reconnaissance"),),
    ),
    "wfuzz": _entry(
        "reconnaissance", "T1595.003", "Wordlist Scanning",
        "wfuzz 對 Web 參數做字典 fuzz，映射到 Wordlist Scanning。",
        (("T1595", "Active Scanning", "reconnaissance"),),
    ),
    "arjun": _entry(
        "reconnaissance", "T1595.003", "Wordlist Scanning",
        "arjun 猜測隱藏的 GET/POST 參數，本質是字典式參數枚舉。",
        (("T1595", "Active Scanning", "reconnaissance"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    "wpscan": _entry(
        "reconnaissance", "T1595.002", "Vulnerability Scanning",
        "wpscan 針對 WordPress 做版本、外掛與佈景主題弱點掃描。",
        (("T1592", "Gather Victim Host Information", "reconnaissance"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    "nuclei": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "nuclei 以模板驗證已知弱點，屬於公開服務弱點利用前的驗證行為。",
        (("T1595.002", "Vulnerability Scanning", "reconnaissance"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "nuclei-templates": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "nuclei 模板集是弱點驗證的規則來源，用來確認公開服務是否可被利用。",
        (("T1595.002", "Vulnerability Scanning", "reconnaissance"),),
    ),
    "searchsploit": _entry(
        "resource-development", "T1608.006", "Stage Capabilities: Exploits",
        "searchsploit 查詢 exploit-db 取得可用的公開 exploit，屬於準備攻擊資源。",
        (("T1588.006", "Exploit Public-Facing Application", "resource-development"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    # ---- 弱點利用 / 注入 -------------------------------------------------
    "sqlmap": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "sqlmap 驗證並（若允許）利用 SQL 注入，屬於對公開 Web 應用的弱點利用。",
        (("T1210", "Exploitation of Remote Services", "lateral-movement"),
         ("T1005", "Data from Local System", "collection")),
    ),
    "xsser": _entry(
        "execution", "T1059.007", "Command and Scripting Interpreter: JavaScript",
        "xsser 驗證 XSS 注入點，payload 最終以 JavaScript 進入瀏覽器執行環境。",
        (("T1189", "Drive-by Compromise", "initial-access"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    "dalfox": _entry(
        "execution", "T1059.007", "Command and Scripting Interpreter: JavaScript",
        "dalfox 主要掃描 DOM-based XSS，注入腳本在瀏覽器端執行。",
        (("T1190", "Exploit Public-Facing Application", "initial-access"),),
    ),
    "commix": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "commix 針對命令注入弱點做自動化驗證與利用。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    "tplmap": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "tplmap 驗證伺服器端模板注入（SSTI），可導向遠端程式碼執行。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    "burpsuite": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "burpsuite 做手動 Web 弱點分析與利用，位在初始存取階段。",
        (("T1210", "Exploitation of Remote Services", "lateral-movement"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "zap": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "OWASP ZAP 自動掃描並驗證 Web 應用弱點。",
        (("T1595.002", "Vulnerability Scanning", "reconnaissance"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "metasploit": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "metasploit 以公開 exploit 模組對目標服務進行初始存取驗證。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    "msfconsole": _entry(
        "initial-access", "T1190", "Exploit Public-Facing Application",
        "msfconsole 為 metasploit 的互動介面，用途與 metasploit 相同。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    # ---- 憑證存取 / 密碼稽核 ---------------------------------------------
    "hydra": _entry(
        "credential-access", "T1110.001", "Brute Force: Password Guessing",
        "hydra 進行密碼猜測，屬於憑證存取階段的暴力破解分支。",
        (("T1110", "Brute Force", "credential-access"),
         ("T1078", "Valid Accounts", "defense-evasion")),
    ),
    "medusa": _entry(
        "credential-access", "T1110.001", "Brute Force: Password Guessing",
        "medusa 為多協定密碼猜測工具，映射到 Password Guessing。",
        (("T1110", "Brute Force", "credential-access"),
         ("T1078", "Valid Accounts", "defense-evasion")),
    ),
    "kerbrute": _entry(
        "credential-access", "T1110.001", "Brute Force: Password Guessing",
        "kerbrute 以字典檔列舉/猜測網域帳號，屬於密碼猜測。",
        (("T1110", "Brute Force", "credential-access"),
         ("T1087.002", "Account Discovery: Domain Account", "discovery")),
    ),
    "responder": _entry(
        "credential-access", "T1557.001",
        "Adversary-in-the-Middle: LLMNR/NBT-NS Poisoning and SMB Relay",
        "responder 架設 LLMNR/NBT-NS 毒化與 SMB relay 以擷取網域憑證。",
        (("T1557", "Adversary-in-the-Middle", "credential-access"),
         ("T1187", "Forced Authentication", "credential-access")),
    ),
    "bettercap": _entry(
        "credential-access", "T1557", "Adversary-in-the-Middle",
        "bettercap 執行 ARP/DNS/NTP spoof 等中間人攻擊以擷取或篡改流量。",
        (("T1040", "Network Sniffing", "credential-access"),
         ("T1187", "Forced Authentication", "credential-access")),
    ),
    "ettercap": _entry(
        "credential-access", "T1557", "Adversary-in-the-Middle",
        "ettercap 進行中間人嗅探與流量篡改。",
        (("T1040", "Network Sniffing", "credential-access"),
         ("T1187", "Forced Authentication", "credential-access")),
    ),
    "mimikatz": _entry(
        "credential-access", "T1003.001", "OS Credential Dumping: LSASS Memory",
        "mimikatz 從 LSASS 記憶體與 Kerberos 票證中擷取憑證。",
        (("T1003", "OS Credential Dumping", "credential-access"),
         ("T1555", "Credentials from Password Stores", "credential-access"),
         ("T1134.001", "Access Token Manipulation: Token Impersonation/Theft", "defense-evasion")),
    ),
    "lsadump": _entry(
        "credential-access", "T1003.001", "OS Credential Dumping: LSASS Memory",
        "lsadump 直接傾印 LSASS 內容取得雜湊與明文。",
        (("T1003", "OS Credential Dumping", "credential-access"),
         ("T1552.001", "Unsecured Credentials: Credentials In Files", "credential-access")),
    ),
    "secretsdump": _entry(
        "credential-access", "T1003", "OS Credential Dumping",
        "impacket-secretsdump 傾印 SAM/ntds.dit/LSASS 等本機憑證存放區。",
        (("T1003.002", "OS Credential Dumping: Security Account Manager", "credential-access"),
         ("T1003.003", "OS Credential Dumping: NTDS", "credential-access")),
    ),
    "impacket-secretsdump": _entry(
        "credential-access", "T1003", "OS Credential Dumping",
        "impacket-secretsdump 傾印遠端網域的 SAM/ntds.dit 雜湊。",
        (("T1003.002", "OS Credential Dumping: Security Account Manager", "credential-access"),
         ("T1003.003", "OS Credential Dumping: NTDS", "credential-access")),
    ),
    "kerberoast": _entry(
        "credential-access", "T1558.003", "Steal or Forge Kerberos Tickets: Kerberoasting",
        "kerberoast 離線破解服務主體票證（TGS）雜湊。",
        (("T1558", "Steal or Forge Kerberos Tickets", "credential-access"),
         ("T1003", "OS Credential Dumping", "credential-access")),
    ),
    "getuserspns": _entry(
        "credential-access", "T1558.003", "Steal or Forge Kerberos Tickets: Kerberoasting",
        "GetUserSPNs 列舉可被 Kerberoast 的服務主體。",
        (("T1087.002", "Account Discovery: Domain Account", "discovery"),
         ("T1558", "Steal or Forge Kerberos Tickets", "credential-access")),
    ),
    "rubeus": _entry(
        "credential-access", "T1558", "Steal or Forge Kerberos Tickets",
        "rubeus 執行 Kerberoast / Pass-the-Ticket / 票證竄改等多種 Kerberos 攻擊。",
        (("T1550.003", "Use Alternate Authentication Material: Pass the Ticket", "defense-evasion"),
         ("T1134.001", "Access Token Manipulation: Token Impersonation/Theft", "defense-evasion")),
    ),
    "certipy": _entry(
        "credential-access", "T1649", "Steal or Forge Authentication Certificates",
        "certipy 枚舉、取得或偽造 AD CS 憑證以取得票證或提權。",
        (("T1552.004", "Unsecured Credentials: Private Keys", "credential-access"),
         ("T1649", "Steal or Forge Authentication Certificates", "credential-access")),
    ),
    "jwt-tool": _entry(
        "credential-access", "T1550.001", "Use Alternate Authentication Material: Application Access Token",
        "jwt_tool 檢查/竄改 JWT 簽章與演算法，即以替代認證material繞過存取控制。",
        (("T1134.001", "Access Token Manipulation: Token Impersonation/Theft", "defense-evasion"),
         ("T1190", "Exploit Public-Facing Application", "initial-access")),
    ),
    # ---- 帳號列舉 / 發現 -------------------------------------------------
    "enum4linux": _entry(
        "discovery", "T1087.002", "Account Discovery: Domain Account",
        "enum4linux 列舉 SMB 匿名可見的網域帳號與群組。",
        (("T1135", "Network Share Discovery", "discovery"),
         ("T1069.002", "Permission Groups Discovery: Domain Groups", "discovery")),
    ),
    "smbmap": _entry(
        "discovery", "T1135", "Network Share Discovery",
        "smbmap 列舉 SMB 共用與存取權限。",
        (("T1046", "Network Service Discovery", "discovery"),
         ("T1021.002", "Remote Services: SMB/Windows Admin Shares", "lateral-movement")),
    ),
    "smbclient": _entry(
        "lateral-movement", "T1021.002", "Remote Services: SMB/Windows Admin Shares",
        "smbclient 以既有憑證掛載或存取 Windows 管理共用。",
        (("T1078", "Valid Accounts", "defense-evasion"),
         ("T1135", "Network Share Discovery", "discovery")),
    ),
    "ldapsearch": _entry(
        "discovery", "T1087.002", "Account Discovery: Domain Account",
        "ldapsearch 直接查詢目錄物件以列舉帳號與結構。",
        (("T1069.002", "Permission Groups Discovery: Domain Groups", "discovery"),
         ("T1018", "Remote System Discovery", "discovery")),
    ),
    "ldapwhoami": _entry(
        "discovery", "T1033", "System Owner/User Discovery",
        "ldapwhoami 回傳目前綁定身分，用於確認自身在目標上的權限位置。",
        (("T1087.002", "Account Discovery: Domain Account", "discovery"),
         ("T1069.002", "Permission Groups Discovery: Domain Groups", "discovery")),
    ),
    "bloodhound": _entry(
        "discovery", "T1087.002", "Account Discovery: Domain Account",
        "bloodhound 收集 Active Directory 關係，找出最短提權路徑。",
        (("T1069.002", "Permission Groups Discovery: Domain Groups", "discovery"),
         ("T1482", "Domain Trust Discovery", "discovery")),
    ),
    "sharphound": _entry(
        "discovery", "T1087.002", "Account Discovery: Domain Account",
        "SharpHound 為 bloodhound 的 C# 收集器，用途相同。",
        (("T1069.002", "Permission Groups Discovery: Domain Groups", "discovery"),
         ("T1482", "Domain Trust Discovery", "discovery")),
    ),
    # ---- 橫向移動 / 遠端服務 ---------------------------------------------
    "crackmapexec": _entry(
        "lateral-movement", "T1021.002", "Remote Services: SMB/Windows Admin Shares",
        "crackmapexec 以既有或猜測的帳密嘗試 SMB/Windows 管理共用驗證。",
        (("T1550.002", "Use Alternate Authentication Material: Pass the Hash", "defense-evasion"),
         ("T1078", "Valid Accounts", "defense-evasion"),
         ("T1018", "Remote System Discovery", "discovery")),
    ),
    "netexec": _entry(
        "lateral-movement", "T1021.002", "Remote Services: SMB/Windows Admin Shares",
        "netexec 為 crackmapexec 的後继工具，同樣用於 SMB 橫向驗證。",
        (("T1550.002", "Use Alternate Authentication Material: Pass the Hash", "defense-evasion"),
         ("T1078", "Valid Accounts", "defense-evasion")),
    ),
    "impacket-psexec": _entry(
        "lateral-movement", "T1021.002", "Remote Services: SMB/Windows Admin Shares",
        "impacket-psexec 經由 SMB 管理共用建立遠端服務執行指令。",
        (("T1569.002", "System Services: Service Execution", "execution"),
         ("T1570", "Lateral Tool Transfer", "lateral-movement")),
    ),
    "impacket-wmiexec": _entry(
        "execution", "T1047", "Windows Management Instrumentation",
        "impacket-wmiexec 透過 WMI 在遠端執行指令。",
        (("T1021.002", "Remote Services: SMB/Windows Admin Shares", "lateral-movement"),
         ("T1569.002", "System Services: Service Execution", "execution")),
    ),
    "ssh": _entry(
        "lateral-movement", "T1021.004", "Remote Services: SSH",
        "ssh 用既有帳號登入遠端主機，屬於遠端服務的橫向移動。",
        (("T1078", "Valid Accounts", "defense-evasion"),
         ("T1098", "Account Manipulation", "privilege-escalation")),
    ),
    "ssh-audit": _entry(
        "reconnaissance", "T1592", "Gather Victim Host Information",
        "ssh-audit 檢查 SSH 伺服器主機金鑰與演算法組態弱點。",
        (("T1040", "Network Sniffing", "credential-access"),),
    ),
    "scp": _entry(
        "lateral-movement", "T1570", "Lateral Tool Transfer",
        "scp 在主機之間搬移檔案，是典型的橫向工具傳輸。",
        (("T1105", "Ingress Tool Transfer", "command-and-control"),
         ("T1021.004", "Remote Services: SSH", "lateral-movement")),
    ),
    "curl": _entry(
        "reconnaissance", "T1595", "Active Scanning",
        "curl 對目標發出 HTTP 請求做服務與路徑探測，屬主動掃描行為。",
        (("T1046", "Network Service Discovery", "discovery"),
         ("T1071.001", "Application Layer Protocol: Web Protocols", "command-and-control")),
    ),
    "wget": _entry(
        "reconnaissance", "T1595", "Active Scanning",
        "wget 用於 HTTP(S) 探測或取回檔案，探測部分屬主動掃描。",
        (("T1105", "Ingress Tool Transfer", "command-and-control"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "nc": _entry(
        "command-and-control", "T1095", "Non-Application Layer Protocol",
        "nc 建立非 HTTP 的原始連線，常作為反向連線或服務探測。",
        (("T1571", "Non-Standard Port", "command-and-control"),
         ("T1046", "Network Service Discovery", "discovery")),
    ),
    "ncat": _entry(
        "command-and-control", "T1095", "Non-Application Layer Protocol",
        "ncat 為 netcat 的衍生版，用於原始 TCP/UDP 連線。",
        (("T1571", "Non-Standard Port", "command-and-control"),),
    ),
    "socat": _entry(
        "command-and-control", "T1095", "Non-Application Layer Protocol",
        "socat 進行通訊協定轉接與代理，常用於隧道與橫向。",
        (("T1090", "Proxy", "command-and-control"),
         ("T1570", "Lateral Tool Transfer", "lateral-movement")),
    ),
    "chisel": _entry(
        "command-and-control", "T1090.003", "Proxy: Multi-hop Proxy",
        "chisel 建立多層 HTTP/TCP 隧道，讓內網服務可被外部存取。",
        (("T1090", "Proxy", "command-and-control"),
         ("T1572", "Protocol Tunneling", "command-and-control")),
    ),
    # ---- 容器 / 雲端 -----------------------------------------------------
    "kubectl": _entry(
        "execution", "T1609", "Container Administration Command",
        "kubectl 直接對容器工作負載下達指令，屬於容器管理指令。",
        (("T1610", "Deploy Container", "persistence"),
         ("T1611", "Escape to Host", "privilege-escalation"),
         ("T1078", "Valid Accounts", "defense-evasion")),
    ),
    "docker": _entry(
        "privilege-escalation", "T1611", "Escape to Host",
        "docker 以高權限掛載主機資源（-v /:/host、--privileged）是典型的容器逃逸路徑。",
        (("T1610", "Deploy Container", "persistence"),
         ("T1609", "Container Administration Command", "execution")),
    ),
    "ansible": _entry(
        "execution", "T1059.006", "Command and Scripting Interpreter: Python",
        "ansible 以 Python 為執行引擎批次執行 playbook。",
        (("T1021.004", "Remote Services: SSH", "lateral-movement"),
         ("T1098", "Account Manipulation", "privilege-escalation")),
    ),
    "terraform": _entry(
        "resource-development", "T1588.003", "Develop Capabilities: Infrastructure",
        "terraform 以程式碼佈建基礎設施，可被用來準備攻擊用資源或建立非法權限。",
        (("T1098.001", "Account Manipulation: Additional Cloud Credentials", "privilege-escalation"),
         ("T1588.001", "Develop Capabilities: Obtain Infrastructure", "resource-development")),
    ),
    # ---- C2 / 持久化 / 取證 ----------------------------------------------
    "cobaltstrike": _entry(
        "lateral-movement", "T1210", "Exploitation of Remote Services",
        "Cobalt Strike 常用於對已入侵服務做橫向利用與長期控制。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1105", "Ingress Tool Transfer", "command-and-control"),
         ("T1071.001", "Application Layer Protocol: Web Protocols", "command-and-control")),
    ),
    "beacon": _entry(
        "execution", "T1059", "Command and Scripting Interpreter",
        "Beacon 週期性執行指令並回傳結果，是典型的命令與腳本解譯器行為。",
        (("T1071.001", "Application Layer Protocol: Web Protocols", "command-and-control"),
         ("T1105", "Ingress Tool Transfer", "command-and-control"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    "sliver": _entry(
        "execution", "T1059", "Command and Scripting Interpreter",
        "Sliver 的 implant 執行遠端指令，屬命令與腳本解譯器。",
        (("T1071.001", "Application Layer Protocol: Web Protocols", "command-and-control"),
         ("T1105", "Ingress Tool Transfer", "command-and-control")),
    ),
    "webshock": _entry(
        "persistence", "T1505.003", "Server Software Component: Web Shell",
        "webshock 植入 Web shell，建立長期持久化入口。",
        (("T1059", "Command and Scripting Interpreter", "execution"),
         ("T1210", "Exploitation of Remote Services", "lateral-movement")),
    ),
    "tcpdump": _entry(
        "credential-access", "T1040", "Network Sniffing",
        "tcpdump 擷取網路流量以蒐集明文協定與憑證。",
        (("T1557", "Adversary-in-the-Middle", "credential-access"),
         ("T1592", "Gather Victim Host Information", "reconnaissance")),
    ),
    "tshark": _entry(
        "credential-access", "T1040", "Network Sniffing",
        "tshark 深入解析擷取封包以找憑證與敏感資料。",
        (("T1557", "Adversary-in-the-Middle", "credential-access"),
         ("T1592", "Gather Victim Host Information", "reconnaissance")),
    ),
    "volatility": _entry(
        "credential-access", "T1003", "OS Credential Dumping",
        "volatility 對記憶體映像做取证，常用來萃取憑證與程序資訊。",
        (("T1003.001", "OS Credential Dumping: LSASS Memory", "credential-access"),
         ("T1070", "Indicator Removal", "defense-evasion")),
    ),
    "foremost": _entry(
        "collection", "T1005", "Data from Local System",
        "foremost 從磁碟或影像中切出檔案，屬本機資料收集。",
        (("T1074.001", "Data Staged: Local Data Staging", "collection"),
         ("T1531", "Account Access Removal", "impact")),
    ),
}

# 別名對應（正規化後的 key -> curated key）
_TOOL_ALIASES: dict[str, str] = {
    "msf": "metasploit",
    "msfconsole": "metasploit",
    "psexec": "impacket-psexec",
    "psexec-py": "impacket-psexec",
    "wmiexec": "impacket-wmiexec",
    "wmiexec-py": "impacket-wmiexec",
    "secretsdump": "impacket-secretsdump",
    "secretsdump-py": "impacket-secretsdump",
    "wireshark": "tshark",
    "wireshark-tshark": "tshark",
    "cobalt-strike": "cobaltstrike",
    "cobaltstrike-beacon": "beacon",
    "jwttool": "jwt-tool",
    "jwt-tool-py": "jwt-tool",
    "testssl": "testssl-sh",
    "testsslsh": "testssl-sh",
    "responder-py": "responder",
    "bloodhound-python": "bloodhound",
    "bloodhoundpy": "bloodhound",
    "sharphound-py": "sharphound",
    "kerberoast-py": "kerberoast",
    "getuserspns-py": "getuserspns",
    "rubeus-net": "rubeus",
    "certipy-ad": "certipy",
    "volatility3": "volatility",
    "metasploit-framework": "metasploit",
    "nuclei-templates-wordpress": "nuclei-templates",
    "enum4linux-ng": "enum4linux",
    "netexec-smb": "netexec",
}

# 埠號 -> 服務名（用於由開放埠推斷後續工具鏈）
_PORT_SERVICE: dict[int, str] = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns", 80: "http",
    88: "kerberos", 110: "pop3", 111: "rpcbind", 135: "msrpc", 139: "netbios",
    143: "imap", 389: "ldap", 445: "smb", 464: "kerberos", 465: "smtps",
    514: "syslog", 587: "smtp", 636: "ldaps", 873: "rsync", 993: "imaps",
    995: "pop3s", 1080: "socks", 1433: "mssql", 1521: "oracle", 2049: "nfs",
    2181: "zookeeper", 2375: "docker", 2376: "docker", 3000: "http",
    3306: "mysql", 3389: "rdp", 4443: "https", 5000: "http", 5432: "postgres",
    5601: "kibana", 5672: "amqp", 5900: "vnc", 5984: "couchdb", 6379: "redis",
    6443: "kubernetes", 7001: "weblogic", 8000: "http", 8008: "http", 8080: "http",
    8081: "http", 8088: "http", 8443: "https", 8888: "http", 9000: "http",
    9042: "cassandra", 9090: "http", 9200: "elasticsearch", 9300: "elasticsearch",
    10250: "kubelet", 10255: "kubelet", 11211: "memcached", 27017: "mongodb",
    27018: "mongodb", 28017: "mongodb",
}

# 自由文字 -> 正規化服務/技術關鍵字
_TEXT_KEYWORDS: dict[str, str] = {
    "wordpress": "wordpress", "wp-": "wordpress", "joomla": "joomla",
    "drupal": "drupal", "magento": "magento", "laravel": "laravel",
    "apache": "http", "nginx": "http", "iis": "http", "tomcat": "http",
    "http": "http", "https": "http", "web": "http",
    "ssh": "ssh", "smb": "smb", "cifs": "smb", "ldap": "ldap", "ldaps": "ldap",
    "kerberos": "kerberos", "mysql": "mysql", "mariadb": "mysql",
    "postgres": "postgres", "mssql": "mssql", "oracle": "oracle",
    "redis": "redis", "mongodb": "mongodb", "memcached": "memcached",
    "ftp": "ftp", "smtp": "smtp", "rdp": "rdp", "dns": "dns", "smb445": "smb",
    "docker": "docker", "container": "container", "kubernetes": "kubernetes",
    "k8s": "kubernetes", "kubectl": "kubernetes",
    "sqli": "sql_injection", "sql injection": "sql_injection",
    "sql-injection": "sql_injection", "注入": "sql_injection",
}

_TECHNICAL_RE = re.compile(r"\bt\d{4}(?:\.\d{3})?\b", re.IGNORECASE)
_PORT_RE = re.compile(r"(?<![\w.])(\d{2,5})(?![\w.])")


def _normalize_tool(name: str) -> str:
    """把工具名正規化為查找用的 key。"""
    value = str(name or "").strip().lower()
    value = value.replace("_", "-").replace(" ", "-").replace("/", "-")
    value = value.replace(".", "-")
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def _resolve_tool_key(name: str) -> str | None:
    key = _normalize_tool(name)
    if not key:
        return None
    if key in _MITRE_TABLE:
        return key
    alias = _TOOL_ALIASES.get(key)
    if alias and alias in _MITRE_TABLE:
        return alias
    # 前綴式比對（例：impacket-secretsdump-xxx / nmap-syn）
    for candidate in sorted(_MITRE_TABLE):
        if key.startswith(candidate + "-") or key.startswith(candidate + "."):
            return candidate
    return None


def _technique_for(tool: str) -> tuple[str, str, str]:
    """回傳 (tactic, technique_id, technique_name)；找不到時回傳 unknown。"""
    key = _resolve_tool_key(tool)
    if key is None:
        return (UNKNOWN_TACTIC, "", "Unmapped Tool")
    item = _MITRE_TABLE[key]
    return (item["tactic"], item["technique_id"], item["technique_name"])


# ---------------------------------------------------------------------------
# Tool 1: kali_map_to_mitre
# ---------------------------------------------------------------------------
app = _MCPServer(
    name="kali-gpt",
    instructions=(
        "Offline autonomous-pentest reasoning: ATT&CK mapping of tool invocations, dynamic tool-chain "
        "selection from findings, PTES phase planning, and persistent engagement memory. "
        "Planning only - it never executes commands and never touches a target."
    ),
)


@app.tool(description="Map a red-team tool invocation to MITRE ATT&CK (curated offline table). Never executes anything.")
def kali_map_to_mitre(tool: str, args_hint: str = "") -> dict[str, Any]:
    try:
        name = str(tool or "").strip()
        hint = str(args_hint or "").strip()
        if not name:
            return {
                "tool": "", "tactic": UNKNOWN_TACTIC, "technique_id": "",
                "technique_name": "Unmapped Tool",
                "tactic_rationale": "tool 參數為空，無法對應到 curated ATT&CK 條目。",
                "related_techniques": [],
                "technique_source": f"{TECHNIQUE_SOURCE}:unmapped",
                "mapped": False,
            }
        key = _resolve_tool_key(name)
        if key is None:
            return {
                "tool": name, "tactic": UNKNOWN_TACTIC, "technique_id": "",
                "technique_name": "Unmapped Tool",
                "tactic_rationale": (
                    f"curated 離線表沒有 '{_normalize_tool(name)}' 這個工具的條目；請改用兄弟服務 redteam-knowledge "
                    "查官方 ATT&CK，或先對工具功能做人工判讀。"
                ),
                "related_techniques": [],
                "technique_source": f"{TECHNIQUE_SOURCE}:unmapped",
                "mapped": False,
            }
        item = _MITRE_TABLE[key]
        rationale = item["rationale"]
        if hint:
            rationale = f"{rationale}（本次呼叫參數摘要：{hint[:200]}）"
        return {
            "tool": name,
            "tactic": item["tactic"],
            "technique_id": item["technique_id"],
            "technique_name": item["technique_name"],
            "tactic_rationale": rationale,
            "related_techniques": [dict(entry) for entry in item["related"]],
            "technique_source": TECHNIQUE_SOURCE,
            "mapped": True,
        }
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_map_to_mitre failed: {exc}"}


# ---------------------------------------------------------------------------
# Tool 2: kali_suggest_toolchain
# ---------------------------------------------------------------------------
def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _normalize_findings(findings: Any) -> list[dict[str, Any]]:
    """把 findings（dict list / 自由字串 / 混合）正規化為 dict list。"""
    if findings is None:
        return []
    if isinstance(findings, str):
        raw: list[Any] = [findings]
    elif isinstance(findings, dict):
        raw = [findings]
    elif isinstance(findings, (list, tuple, set)):
        raw = list(findings)
    else:
        raw = [findings]
    normalized: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            entry: dict[str, Any] = {}
            for key, value in item.items():
                entry[str(key).strip().lower()] = value
            normalized.append(entry)
        else:
            text = _as_text(item).strip()
            if text:
                normalized.append({"type": "text", "value": text})
    return normalized


def _collect_signals(findings: list[dict[str, Any]], context: str = "") -> dict[str, Any]:
    """由 findings 與 context 抽出可用的判斷訊號。"""
    signals: dict[str, Any] = {
        "ports": set(),
        "services": set(),
        "techs": set(),
        "has_sqli": False,
        "has_container": False,
        "has_k8s": False,
        "has_web": False,
    }

    def scan_text(text: str) -> None:
        if not text:
            return
        cleaned = _TECHNICAL_RE.sub(" ", text.lower())
        for token in _PORT_RE.findall(cleaned):
            value = int(token)
            if 1 <= value <= 65535:
                signals["ports"].add(value)
                service = _PORT_SERVICE.get(value)
                if service:
                    signals["services"].add(service)
        for keyword, canonical in _TEXT_KEYWORDS.items():
            if keyword in cleaned:
                if canonical in ("wordpress", "joomla", "drupal", "magento", "laravel"):
                    signals["techs"].add(canonical)
                elif canonical == "sql_injection":
                    signals["has_sqli"] = True
                elif canonical == "container":
                    signals["has_container"] = True
                elif canonical == "kubernetes":
                    signals["has_k8s"] = True
                    signals["has_container"] = True
                elif canonical == "http":
                    signals["has_web"] = True
                signals["services"].add(canonical)

    for finding in findings:
        kind = str(finding.get("type") or "").strip().lower()
        port = finding.get("port")
        try:
            if port is not None and str(port).strip() != "":
                value = int(port)
                if 1 <= value <= 65535:
                    signals["ports"].add(value)
                    service = _PORT_SERVICE.get(value)
                    if service:
                        signals["services"].add(service)
        except (TypeError, ValueError):
            pass
        if kind in ("service", "proto", "protocol"):
            signals["services"].add(str(finding.get("value") or finding.get("service") or "").strip().lower())
        if kind in ("web_tech", "tech", "technology", "webtech"):
            signals["techs"].add(str(finding.get("value") or finding.get("tech") or "").strip().lower())
        if kind in ("sql_injection", "sqli", "injection"):
            signals["has_sqli"] = True
        if kind in ("container", "docker"):
            signals["has_container"] = True
        if kind in ("kubernetes", "k8s"):
            signals["has_k8s"] = True
            signals["has_container"] = True
        scan_text(_as_text(finding.get("value") or ""))
        scan_text(_as_text(finding.get("service") or ""))
        scan_text(_as_text(finding.get("tech") or ""))
        if kind == "text":
            scan_text(str(finding.get("value") or ""))

    scan_text(context)

    if signals["services"] & {"http", "wordpress", "joomla", "drupal", "magento", "laravel"}:
        signals["has_web"] = True
    if signals["ports"] & {80, 443, 8000, 8080, 8443, 8888, 3000, 5000, 9000, 9090}:
        signals["has_web"] = True
    return signals


def _step(
    tool: str,
    purpose: str,
    command_template: str,
    depends_on: list[str] | None = None,
    requires_authorization: bool = True,
) -> dict[str, Any]:
    tactic, technique_id, _ = _technique_for(tool)
    return {
        "tool": tool,
        "purpose": purpose,
        "mitre_tactic": tactic,
        "technique_id": technique_id,
        "depends_on": list(depends_on or []),
        "command_template": command_template,
        "requires_authorization": requires_authorization,
    }


def _build_chain(signals: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """依訊號組出確定性的工具鏈與提醒筆記。"""
    chain: list[dict[str, Any]] = []
    notes: list[str] = []
    ports = signals["ports"]
    services = signals["services"]
    techs = signals["techs"]

    if signals["has_web"] or ports & {80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 9000, 9090}:
        chain.append(_step(
            "whatweb",
            "確認 Web 技術棧、伺服器版本與前端框架，決定後續模板與字典",
            "whatweb -a 3 http://{target}:{port}",
        ))
        chain.append(_step(
            "nikto",
            "檢查公開 Web 服務的常見組態缺失與已知弱點",
            "nikto -h http://{target}:{port} -nointeractive",
            ["whatweb"],
        ))
        chain.append(_step(
            "ffuf",
            "以字典檔枚舉隱藏路徑與參數",
            "ffuf -u http://{target}:{port}/FUZZ -w {wordlist} -mc all",
            ["whatweb"],
        ))
        chain.append(_step(
            "nuclei",
            "以模板驗證已知弱點（限 medium 以上並降低 rate）",
            "nuclei -u http://{target}:{port} -severity medium,high,critical -rate-limit 50 -timeout 10",
            ["nikto"],
        ))
        notes.append("Web 鏈以 whatweb 的指紋結果決定後續字典與模板；建議以 -rate-limit 避免影響線上服務。")
    elif ports or services:
        chain.append(_step(
            "nmap",
            "先做 TCP 服務與版本識別，作為後續所有工具鏈的基礎事實",
            "nmap -sV -sC -p- --min-rate 1000 {target}",
        ))
    else:
        chain.append(_step(
            "nmap",
            "尚未解析出任何服務訊號，先以完整 TCP 掃描建立服務清單",
            "nmap -sV -sC -p- --min-rate 1000 {target}",
        ))
        notes.append("未從 findings 解析出明確訊號；建議先產出 TCP 服務清單後重新呼叫本工具。")

    if techs & {"wordpress"}:
        chain.append(_step(
            "wpscan",
            "枚舉 WordPress 版本、外掛與佈景主題弱點",
            "wpscan --url http://{target}:{port} --enumerate vp,vt --plugins-detection mixed",
            ["whatweb"],
        ))
        chain.append(_step(
            "nuclei",
            "只跑 WordPress 相關模板，避免對全站重複掃描",
            "nuclei -u http://{target}:{port} -tags wordpress -severity medium,high,critical -rate-limit 20",
            ["wpscan"],
        ))
        notes.append("偵測到 WordPress：wpscan 需對外連線取得版本清單，執行前請確認 engagement 允許對外請求。")
    elif techs & {"joomla", "drupal", "magento", "laravel"}:
        chain.append(_step(
            "nikto",
            "針對特定 CMS 做組態與弱點檢查",
            "nikto -h http://{target}:{port} -nointeractive -Tuning 123bde",
            ["whatweb"],
        ))
        notes.append(f"偵測到 CMS：{', '.join(sorted(techs))}，請補上對應的專屬掃描工具。")

    if "smb" in services or 445 in ports or 139 in ports:
        chain.append(_step(
            "enum4linux",
            "列舉 SMB 共用、匿名可讀內容與網域帳號",
            "enum4linux -S -u '' -p '' -a {target}",
        ))
        chain.append(_step(
            "smbmap",
            "列出 SMB 共用與存取權限",
            "smbmap -H {target} -u '' -P ''",
            ["enum4linux"],
        ))
        chain.append(_step(
            "netexec",
            "以既有帳號驗證 SMB 並評估橫向面",
            "netexec smb {target} -u {user} -p {pass} --shares",
            ["smbmap"],
        ))
        notes.append("SMB 鏈後段需要有效憑證；請確認帳號來源合法，且不得把 hash 帶出目標範圍。")

    if "ldap" in services or 389 in ports or 636 in ports:
        chain.append(_step(
            "ldapsearch",
            "列舉 LDAP 目錄物件、群組與 OU 結構",
            "ldapsearch -x -H ldap://{target}:389 -b {base_dn} -s sub '(objectClass=*)'",
        ))
        chain.append(_step(
            "bloodhound",
            "收集 AD 關係圖，找出最短提權路徑",
            "bloodhound-python -d {domain} -u {user} -p {pass} -dc {target} --collection All",
            ["ldapsearch"],
        ))
        chain.append(_step(
            "kerbrute",
            "以字典檔列舉網域使用者名稱（密碼猜測，務必先取得授權）",
            "kerbrute userenum -d {domain} --dc {target} -t {wordlist}",
            ["ldapsearch"],
        ))
        notes.append("kerbrute 屬於 credential_enum 類別，必須在 scope registry 中明確授權後才可執行。")

    if "kerberos" in services or 88 in ports:
        chain.append(_step(
            "GetUserSPNs",
            "列出可被 Kerberoast 的服務主體",
            "GetUserSPNs.py -dc {domain} -target {target}",
        ))
        chain.append(_step(
            "rubeus",
            "評估 Kerberoast / Pass-the-Ticket 的可行路徑",
            "rubeus kerberoast /domain:{domain} /user:{user}",
            ["GetUserSPNs"],
        ))
        notes.append("Kerberos 攻擊可能觸發帳號鎖定；建議先在測試網域驗證。")

    if "ssh" in services or 22 in ports:
        chain.append(_step(
            "ssh-audit",
            "檢查 SSH 主機金鑰、演算法與組態弱點",
            "ssh-audit -p {port} {target}",
        ))
        chain.append(_step(
            "hydra",
            "密碼稽核（弱密碼測試，必須有明確授權並限制速率與帳號範圍）",
            "hydra -l {user} -P {wordlist} -t 4 -s {port} ssh://{target}",
            ["ssh-audit"],
        ))
        notes.append("hydra/medusa 屬於憑證爆破：需 engagement 明確授權，且必須設定 -t 與 -f 避免鎖定。")

    if "mysql" in services or 3306 in ports:
        chain.append(_step(
            "mysql-enum",
            "列舉 MySQL 版本、資料庫與帳號權限",
            "mysql -h {target} -P {port} -u {user} -p{pass} -e 'SHOW DATABASES;'",
        ))
        if signals["has_web"]:
            chain.append(_step(
                "sqlmap",
                "僅在存在 Web 前端時，對疑似注入點做非破壞性驗證",
                "sqlmap -u {url} --batch --level=3 --risk=1 --technique=BEU --threads=2 --tamper=space2comment",
                ["mysql-enum"],
            ))
            notes.append("sqlmap 使用 --batch / --level / --risk 與 tamper=space2comment 的非破壞性 profile，禁止 --dump。")
        else:
            notes.append("偵測到 MySQL 但沒有 Web 前端：未加入 sqlmap，避免對資料庫做破壞性驗證。")

    if "postgres" in services or 5432 in ports:
        chain.append(_step("psql", "列舉 PostgreSQL 版本與資料庫清單",
                           "psql -h {target} -p {port} -U {user} -l"))
    if "mssql" in services or 1433 in ports:
        chain.append(_step("sqlcmd", "列舉 MSSQL 版本與資料庫",
                           "sqlcmd -S {target} -p {port} -U {user} -P {pass} -Q 'SELECT @@VERSION'"))
    if "redis" in services or 6379 in ports:
        chain.append(_step("redis-cli", "檢查 Redis 未授權存取與設定",
                           "redis-cli -h {target} -p {port} INFO"))
    if "mongodb" in services or 27017 in ports:
        chain.append(_step("mongosh", "檢查 MongoDB 未授權存取與資料庫",
                           "mongosh --host {target} --port {port} --eval 'db.adminCommand({listDatabases:1})'"))

    if signals["has_sqli"]:
        chain.append(_step(
            "sqlmap",
            "針對既有 SQLi 發現做非破壞性驗證與資料型別確認",
            "sqlmap -u {url} --batch --level=2 --risk=1 --technique=BEU --dbms={dbms} --threads=2 --tamper=space2comment",
        ))
        notes.append("已存在 SQLi 發現：sqlmap 僅做驗證，禁止 --dump/--os-shell，需匯出資料請另行授權。")

    if signals["has_k8s"] or signals["has_container"]:
        chain.append(_step(
            "docker",
            "稽核容器設定與掛載，確認是否存在主機路徑掛載",
            "docker inspect --format '{{json .Config}}' {container}",
        ))
        chain.append(_step(
            "kubectl",
            "盤點 Pod、ServiceAccount 與 RBAC 權限過寬情況",
            "kubectl get pods,sa -A -o wide",
            ["docker"],
        ))
        notes.append("容器鏈：先確認 kubelet/Docker API 是否暴露，再談逃逸；逃逸嘗試需獨立授權。")

    notes.append("所有 command_template 皆為含佔位符的範本，本伺服器不會代入真實目標、也不會執行。")
    notes.append("執行前建議先用 kali_recall_memory 查詢同一 target_fingerprint 的過往經驗。")
    return chain, notes


@app.tool(description="Suggest a dynamic, finding-driven red-team tool chain with MITRE mapping. Planning only; never runs anything.")
def kali_suggest_toolchain(findings: list, limit: int = 8) -> dict[str, Any]:
    try:
        normalized = _normalize_findings(findings)
        signals = _collect_signals(normalized)
        chain, notes = _build_chain(signals)
        try:
            max_steps = int(limit)
        except (TypeError, ValueError):
            max_steps = 8
        max_steps = max(1, min(max_steps, 30))
        selected = chain[:max_steps]
        result_chain = []
        for index, item in enumerate(selected, start=1):
            entry = dict(item)
            entry["step"] = index
            result_chain.append(entry)
        return {
            "findings": len(normalized),
            "chain": result_chain,
            "notes": notes,
            "execution_policy": EXECUTION_POLICY,
        }
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_suggest_toolchain failed: {exc}"}


# ---------------------------------------------------------------------------
# Tool 3: kali_plan_phase
# ---------------------------------------------------------------------------
_PHASE_ALIASES: dict[str, str] = {
    "recon": "recon",
    "reconnaissance": "recon",
    "information-gathering": "recon",
    "info-gathering": "recon",
    "scan": "scan",
    "scanning": "scan",
    "vulnerability-scan": "scan",
    "enumeration": "enumeration",
    "enum": "enumeration",
    "vulnerability-analysis": "vulnerability-analysis",
    "vuln-analysis": "vulnerability-analysis",
    "exploitation": "exploitation",
    "exploit": "exploitation",
    "attack": "exploitation",
    "reporting": "reporting",
    "report": "reporting",
}

_PHASE_TITLES: dict[str, str] = {
    "recon": "Information Gathering / 資訊蒐集",
    "scan": "Vulnerability Scanning / 弱點掃描",
    "enumeration": "Enumeration / 深度列舉",
    "vulnerability-analysis": "Vulnerability Analysis / 弱點分析",
    "exploitation": "Exploitation / 弱點利用",
    "reporting": "Reporting / 結案報告",
}

# 每個 phase 的步驟模板：(title, description, tools, mitre_tactics, expected_output, requires_authorization)
_PHASE_STEPS: dict[str, list[tuple[str, str, list[str], list[str], str, bool]]] = {
    "recon": [
        ("被動資訊蒐集",
         "以 WHOIS / 公開 CT / 搜尋引擎建立目標輪廓，不直接碰目標主機。",
         ["whois", "amass", "subfinder", "theHarvester"],
         ["reconnaissance", "resource-development"],
         "子域名清單、註冊資訊與公開暴露的資產清單。",
         False),
        ("主動存活性與埠別確認",
         "對已授權範圍做 TCP/UDP 埠掃描，確認哪些服務真的對外開放。",
         ["nmap", "masscan", "rustscan"],
         ["reconnaissance", "discovery"],
         "開放埠與服務版本清單（後續所有工具鏈的輸入）。",
         True),
        ("Web 技術棧指紋",
         "辨識 Web 伺服器版本、CMS、框架與前端資源。",
         ["whatweb"],
         ["reconnaissance"],
         "技術棧清單，決定後續字典、模板與 CVE 關注面。",
         True),
        ("TLS 與憑證盤點",
         "檢查憑證有效期、主機名稱、協定版本與弱點。",
         ["testssl.sh", "openssl"],
         ["reconnaissance"],
         "TLS 組態弱點與憑證資訊。",
         True),
    ],
    "scan": [
        ("服務與弱點掃描",
         "以已確認的服務清單進行版本導向的弱點掃描。",
         ["nmap", "nikto", "nuclei"],
         ["reconnaissance", "discovery", "initial-access"],
         "弱點候選清單（含模板 ID 與可信度）。",
         True),
        ("模板化驗證",
         "用 nuclei 模板與 searchsploit 交叉比對，確認弱點是否真的可利用。",
         ["nuclei-templates", "searchsploit"],
         ["reconnaissance", "resource-development"],
         "已驗證弱點清單與對應 exploit 來源。",
         True),
        ("內容與路徑枚舉",
         "以字典檔找出隱藏端點、備份檔與管理介面。",
         ["gobuster", "ffuf", "dirb", "wfuzz"],
         ["reconnaissance"],
         "隱藏路徑清單與敏感檔案（備份、設定檔）。",
         True),
        ("參數面探索",
         "找出未在文件中出現的參數，作為後續注入測試的輸入。",
         ["arjun"],
         ["reconnaissance"],
         "參數清單與其推斷來源。",
         True),
    ],
    "enumeration": [
        ("帳號與群組列舉",
         "列舉目錄中的帳號、群組與特權成員，畫出權限輪廓。",
         ["enum4linux", "ldapsearch", "ldapwhoami", "netexec"],
         ["discovery", "credential-access"],
         "帳號/群組/特權成員清單。",
         True),
        ("網站與應用面列舉",
         "針對 CMS、外掛與參數做深入列舉。",
         ["wpscan", "ffuf", "arjun"],
         ["discovery", "reconnaissance"],
         "外掛版本、主題與可利用參數清單。",
         True),
        ("密碼與票證面評估",
         "評估弱密碼與 Kerberos 票證可利用性（授權後才執行爆破類工具）。",
         ["kerbrute", "GetUserSPNs", "kerberoast"],
         ["credential-access"],
         "弱密碼帳號清單與可 Kerberoast 的服務主體清單。",
         True),
        ("本機憑證與中間人面",
         "盤點可被傾印或攔截的憑證來源。",
         ["responder", "mimikatz", "lsadump", "impacket-secretsdump"],
         ["credential-access"],
         "可取得的憑證類型與取得前提條件。",
         True),
    ],
    "vulnerability-analysis": [
        ("弱點複核與風險排序",
         "把掃描結果與實際設定比對，去除誤報並排序真實風險。",
         ["nuclei", "nikto", "searchsploit"],
         ["reconnaissance", "initial-access"],
         "去誤報後的風險排序清單（附複核證據）。",
         True),
        ("注入點分析",
         "對疑似注入點做非破壞性驗證（禁止 dump / shell）。",
         ["sqlmap", "commix", "tplmap", "dalfox", "xsser"],
         ["initial-access", "execution"],
         "已驗證的注入點清單與其資料庫/執行語意。",
         True),
        ("弱密碼與預設憑證稽核",
         "在明確授權範圍內評估弱密碼風險。",
         ["hydra", "medusa"],
         ["credential-access"],
         "弱密碼帳號清單與風險等級。",
         True),
        ("應用層手動驗證",
         "以專業工具做業務邏輯與授權繞過的手動驗證。",
         ["burpsuite", "zap"],
         ["initial-access", "defense-evasion"],
         "業務邏輯缺陷與授權繞過證據（request/response 紀錄）。",
         True),
    ],
    "exploitation": [
        ("初始存取驗證",
         "以最小侵入的方式驗證初始存取是否成立（優先無害 payload）。",
         ["metasploit", "msfconsole", "burpsuite"],
         ["initial-access", "execution"],
         "初始存取證據與可重現步驟。",
         True),
        ("橫向移動評估",
         "沿著已確認的信任邊界評估橫向移動路徑。",
         ["crackmapexec", "netexec", "impacket-psexec", "impacket-wmiexec", "ssh", "scp"],
         ["lateral-movement"],
         "可用的橫向路徑清單與其所需憑證/前提。",
         True),
        ("提權路徑評估",
         "評估網域與主機層級的提權路徑（ADCS、票證、組態）。",
         ["mimikatz", "certipy", "rubeus"],
         ["privilege-escalation", "credential-access"],
         "提權路徑清單與最短步驟數。",
         True),
        ("持久化與通道盤點",
         "評估可用的持久化位置與回連通道（僅記錄，不建立）。",
         ["webshock", "chisel", "socat", "ansible", "terraform", "kubectl", "docker"],
         ["persistence", "privilege-escalation"],
         "持久化選項與其落地前提（僅評估，不實際建立）。",
         True),
    ],
    "reporting": [
        ("證據與觀測彙整",
         "把各階段證據與工具輸出整理成可追溯的案例條目（僅分析已取得的 artifact，不重新碰目標）。",
         ["volatility", "foremost", "kali_record_memory"],
         ["collection", "credential-access"],
         "目標指紋、工具執行結果與成敗率（寫入 engagement memory）。",
         False),
        ("ATT&CK 對映",
         "把每個已驗證步驟對應到 ATT&CK 技術，形成覆蓋率視圖。",
         ["kali_map_to_mitre"],
         ["reconnaissance", "initial-access", "credential-access", "lateral-movement"],
         "技術對映表與涵蓋的戰術。",
         False),
        ("覆蓋率與缺口檢核",
         "檢查哪些 PTES 階段與技術尚未覆蓋，決定是否需要補測。",
         ["kali_plan_phase", "kali_gpt_status"],
         ["collection"],
         "覆蓋率缺口清單與建議補測項目。",
         False),
        ("報告撰寫與風險敘述",
         "產出風險敘述、影響、證據與修復建議。",
         ["kali_recall_memory"],
         ["collection"],
         "可交付的結案報告草稿（含證據索引）。",
         False),
    ],
}


@app.tool(description="Build a PTES phase plan (recon/scan/enumeration/vulnerability-analysis/exploitation/reporting). Planning only; never executes.")
def kali_plan_phase(phase: str, target: str, context: str = "") -> dict[str, Any]:
    try:
        raw_phase = str(phase or "").strip().lower()
        key = _normalize_tool(raw_phase)
        resolved = _PHASE_ALIASES.get(key)
        if resolved is None:
            return {
                "ok": False,
                "error": (
                    f"unsupported phase '{raw_phase}'; supported: recon, scan, enumeration, "
                    "vulnerability-analysis, exploitation, reporting"
                ),
            }
        target_value = str(target or "").strip()
        if not target_value:
            return {"ok": False, "error": "target must not be empty"}
        context_value = str(context or "").strip()
        steps: list[dict[str, Any]] = []
        coverage: list[dict[str, Any]] = []
        seen_coverage: set[str] = set()
        for order, (title, description, tools, tactics, expected, requires_auth) in enumerate(
            _PHASE_STEPS[resolved], start=1
        ):
            steps.append({
                "order": order,
                "title": title,
                "description": description,
                "tools": list(tools),
                "mitre_tactics": list(tactics),
                "expected_output": expected,
                "requires_authorization": bool(requires_auth),
            })
            for tool in tools:
                tactic, technique_id, technique_name = _technique_for(tool)
                if technique_id and technique_id not in seen_coverage:
                    seen_coverage.add(technique_id)
                    coverage.append({
                        "technique_id": technique_id,
                        "technique_name": technique_name,
                        "tactic": tactic,
                    })
        return {
            "ok": True,
            "phase": resolved,
            "phase_title": _PHASE_TITLES[resolved],
            "target": target_value,
            "steps": steps,
            "mitre_coverage": coverage,
            "execution_policy": EXECUTION_POLICY,
        }
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_plan_phase failed: {exc}"}


# ---------------------------------------------------------------------------
# Tool 4/5/6: engagement memory
# ---------------------------------------------------------------------------
def _memory_db_path() -> str:
    raw = os.environ.get(MEMORY_DB_ENV, "").strip()
    if raw:
        return os.path.abspath(os.path.expanduser(raw))
    return os.path.join(os.path.expanduser("~"), ".jysecai", "kali_gpt", "memory.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS engagement_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_fingerprint TEXT,
            tool TEXT,
            technique_id TEXT,
            outcome TEXT,
            notes TEXT,
            tags TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_engagement_memory_fingerprint "
        "ON engagement_memory(target_fingerprint)"
    )


def _clean(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    text = text.strip()
    if len(text) > limit:
        text = text[:limit]
    return text


def _clean_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [part for part in re.split(r"[,\s]+", value) if part]
    elif isinstance(value, (list, tuple, set)):
        raw_items = [str(item) for item in value]
    else:
        raw_items = [str(value)]
    cleaned: list[str] = []
    for item in raw_items:
        tag = _clean(item, MAX_TAG_CHARS)
        if tag and tag not in cleaned:
            cleaned.append(tag)
        if len(cleaned) >= MAX_TAGS:
            break
    return cleaned


def _parse_tags(raw: Any) -> list[str]:
    if not raw:
        return []
    return [part for part in str(raw).split(",") if part]


def _like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@app.tool(description="Record an engagement lesson (target fingerprint, tool, outcome) into the local SQLite memory. No network, no target access.")
def kali_record_memory(entry: dict) -> dict[str, Any]:
    try:
        db_path = _memory_db_path()
        if not isinstance(entry, dict):
            return {"ok": False, "error": "entry must be an object"}
        fingerprint = _clean(entry.get("target_fingerprint"), MAX_FINGERPRINT_CHARS)
        tool = _clean(entry.get("tool"), MAX_TOOL_CHARS)
        if not fingerprint:
            return {"ok": False, "error": "target_fingerprint must not be empty"}
        if not tool:
            return {"ok": False, "error": "tool must not be empty"}
        technique_id = _clean(entry.get("technique_id"), MAX_TECHNIQUE_CHARS)
        outcome = _clean(entry.get("outcome"), 32).lower()
        if outcome not in VALID_OUTCOMES:
            outcome = DEFAULT_OUTCOME
        notes = _clean(entry.get("notes"), MAX_NOTES_CHARS)
        tags = _clean_tags(entry.get("tags"))
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = _connect(db_path)
        try:
            _init_schema(conn)
            cursor = conn.execute(
                "INSERT INTO engagement_memory "
                "(target_fingerprint, tool, technique_id, outcome, notes, tags, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fingerprint, tool, technique_id, outcome, notes, ",".join(tags), _utc_now()),
            )
            conn.commit()
            row_id = int(cursor.lastrowid or 0)
        finally:
            conn.close()
        return {"ok": True, "id": row_id, "memory_db": db_path}
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_record_memory failed: {exc}"}


@app.tool(description="Recall past engagement lessons ranked by fingerprint match, then tool/tag overlap. Read-only; missing DB returns an empty list.")
def kali_recall_memory(target_fingerprint: str = "", tool: str = "", limit: int = 10) -> dict[str, Any]:
    try:
        db_path = _memory_db_path()
        fingerprint = _clean(target_fingerprint, MAX_FINGERPRINT_CHARS)
        tool_name = _clean(tool, MAX_TOOL_CHARS)
        try:
            max_rows = int(limit)
        except (TypeError, ValueError):
            max_rows = 10
        max_rows = max(1, min(max_rows, MAX_ROWS))
        if not os.path.exists(db_path):
            return {"entries": [], "total": 0, "matched_total": 0, "memory_db": db_path}
        conn = _connect(db_path)
        try:
            conn.execute("SELECT 1 FROM engagement_memory LIMIT 1")
        except sqlite3.Error:
            conn.close()
            return {"entries": [], "total": 0, "matched_total": 0, "memory_db": db_path}
        rows: dict[int, sqlite3.Row] = {}

        def collect(sql: str, params: tuple[Any, ...]) -> None:
            try:
                for row in conn.execute(sql, params):
                    rows[int(row["id"])] = row
            except sqlite3.Error:
                return

        if fingerprint:
            collect(
                "SELECT * FROM engagement_memory WHERE lower(target_fingerprint) = lower(?) "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (fingerprint, MAX_ROWS),
            )
            collect(
                "SELECT * FROM engagement_memory WHERE lower(target_fingerprint) LIKE ? ESCAPE '\\' "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (f"%{_like_escape(fingerprint.lower())}%", MAX_ROWS),
            )
        if tool_name:
            collect(
                "SELECT * FROM engagement_memory WHERE lower(tool) = lower(?) "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (tool_name, MAX_ROWS),
            )
            collect(
                "SELECT * FROM engagement_memory WHERE lower(tool) LIKE ? ESCAPE '\\' "
                "OR lower(tags) LIKE ? ESCAPE '\\' "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (
                    f"%{_like_escape(tool_name.lower())}%",
                    f"%{_like_escape(tool_name.lower())}%",
                    MAX_ROWS,
                ),
            )
        collect(
            "SELECT * FROM engagement_memory ORDER BY updated_at DESC, id DESC LIMIT ?",
            (MAX_ROWS,),
        )
        conn.close()

        scored: list[tuple[float, str, int, dict[str, Any]]] = []
        for row in rows.values():
            row_fp = str(row["target_fingerprint"] or "")
            row_tool = str(row["tool"] or "")
            tags = _parse_tags(row["tags"])
            score = 0.0
            if fingerprint:
                query_fp = fingerprint.lower()
                target_fp = row_fp.lower()
                if target_fp == query_fp:
                    score += 100.0
                elif target_fp and (target_fp in query_fp or query_fp in target_fp):
                    score += 50.0
            if tool_name:
                query_tool = tool_name.lower()
                target_tool = row_tool.lower()
                lowered_tags = [tag.lower() for tag in tags]
                if target_tool == query_tool:
                    score += 40.0
                elif query_tool and query_tool in target_tool:
                    score += 15.0
                elif query_tool in lowered_tags:
                    score += 20.0
                elif any(query_tool in tag for tag in lowered_tags):
                    score += 10.0
            entry = {
                "id": int(row["id"]),
                "target_fingerprint": row_fp,
                "tool": row_tool,
                "technique_id": str(row["technique_id"] or ""),
                "outcome": str(row["outcome"] or ""),
                "notes": str(row["notes"] or ""),
                "tags": tags,
                "updated_at": str(row["updated_at"] or ""),
                "score": score,
            }
            scored.append((score, entry["updated_at"], entry["id"], entry))
        # 穩定排序：先 id desc，再 updated_at desc，最後以 score desc 為主要鍵。
        scored.sort(key=lambda item: -item[2])
        scored.sort(key=lambda item: item[1], reverse=True)
        scored.sort(key=lambda item: -item[0])
        ordered = [item[3] for item in scored]
        return {
            "entries": ordered[:max_rows],
            "total": len(ordered[:max_rows]),
            "matched_total": len(ordered),
            "memory_db": db_path,
        }
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_recall_memory failed: {exc}"}


@app.tool(description="Report kali-gpt status: tool count, memory database path and entry count. Offline, read-only.")
def kali_gpt_status() -> dict[str, Any]:
    try:
        db_path = _memory_db_path()
        entries = 0
        if os.path.exists(db_path):
            conn = _connect(db_path)
            try:
                row = conn.execute("SELECT COUNT(*) AS c FROM engagement_memory").fetchone()
                entries = int(row["c"]) if row is not None else 0
            except sqlite3.Error:
                entries = 0
            finally:
                conn.close()
        return {
            "ok": True,
            "tool_count": 6,
            "memory_db": db_path,
            "memory_entries": entries,
            "provider": PROVIDER,
            "note": (
                "Curated offline rule engine: ATT&CK mappings are a hand-maintained table, not the official "
                "MITRE dataset. Cross-check technique IDs with the sibling redteam-knowledge MCP. "
                "This server plans only - it never executes commands and never contacts a target."
            ),
        }
    except Exception as exc:  # pragma: no cover - 防禦性兜底
        return {"ok": False, "error": f"kali_gpt_status failed: {exc}"}


if __name__ == "__main__":
    app.run(transport="stdio")
