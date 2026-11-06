"""Unit tests for the kali_gpt reasoning MCP.

全部測試皆離線：不連網、不執行任何外部指令。記憶體測試使用
`KALI_GPT_MEMORY_DB` 指向暫存目錄，避免碰到使用者實際的 memory.db。
"""

import asyncio
import inspect
import os
import shutil
import tempfile
import unittest

import mcp_kali_gpt as server


EXPECTED_TOOLS = {
    "kali_map_to_mitre",
    "kali_suggest_toolchain",
    "kali_plan_phase",
    "kali_record_memory",
    "kali_recall_memory",
    "kali_gpt_status",
}

PHASES = [
    "recon",
    "scan",
    "enumeration",
    "vulnerability-analysis",
    "exploitation",
    "reporting",
]

PLACEHOLDERS = ("{target}", "{port}", "{wordlist}", "{url}")


class ToolRegistrationTests(unittest.TestCase):
    def test_exactly_six_tools_are_exposed(self):
        tools = asyncio.run(server.app.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(names, EXPECTED_TOOLS)
        self.assertEqual(len(tools), 6)

    def test_module_has_no_process_or_network_capability(self):
        source = inspect.getsource(server)
        for forbidden in (
            "import subprocess",
            "import socket",
            "import urllib",
            "import requests",
            "os.system(",
            "urlopen(",
            "popen(",
            "eval(",
            "exec(",
        ):
            self.assertNotIn(forbidden, source, f"module must not contain {forbidden}")


class MapToMitreTests(unittest.TestCase):
    def test_known_tool_maps_to_attack(self):
        result = server.kali_map_to_mitre("nmap", "")
        self.assertEqual(result["technique_id"], "T1046")
        self.assertEqual(result["technique_name"], "Network Service Discovery")
        self.assertEqual(result["tactic"], "discovery")
        self.assertTrue(result["mapped"])
        self.assertEqual(result["technique_source"], "curated-offline")
        self.assertTrue(result["related_techniques"])
        for entry in result["related_techniques"]:
            self.assertIn("technique_id", entry)
            self.assertIn("technique_name", entry)
            self.assertIn("tactic", entry)

    def test_unknown_tool_returns_structured_fallback(self):
        result = server.kali_map_to_mitre("totally-unknown-tool", "")
        self.assertIn(result["tactic"], ("unknown", "execution"))
        self.assertFalse(result["mapped"])
        self.assertEqual(result["related_techniques"], [])
        self.assertIn("unmapped", result["technique_source"])
        self.assertTrue(result["tactic_rationale"])

    def test_empty_tool_returns_structured_fallback(self):
        result = server.kali_map_to_mitre("", "")
        self.assertFalse(result["mapped"])
        self.assertEqual(result["tactic"], "unknown")

    def test_aliases_and_punctuation_resolve(self):
        cases = {
            "impacket-psexec": "T1021.002",
            "impacket-secretsdump": "T1003",
            "GetUserSPNs": "T1558.003",
            "testssl.sh": "T1592",
            "jwt_tool": "T1550.001",
            "wireshark/tshark": "T1040",
            "msfconsole": "T1190",
            "kerberoast": "T1558.003",
        }
        for tool, technique_id in cases.items():
            with self.subTest(tool=tool):
                result = server.kali_map_to_mitre(tool, "")
                self.assertTrue(result["mapped"], f"{tool} should be mapped")
                self.assertEqual(result["technique_id"], technique_id)

    def test_args_hint_is_included_in_rationale(self):
        result = server.kali_map_to_mitre("nmap", "-sV -p-")
        self.assertIn("-sV -p-", result["tactic_rationale"])

    def test_curated_table_covers_required_tools(self):
        required = [
            "nmap", "masscan", "rustscan", "whatweb", "nikto", "gobuster", "ffuf",
            "dirb", "wfuzz", "arjun", "searchsploit", "sqlmap", "hydra", "medusa",
            "metasploit", "msfconsole", "nuclei", "curl", "wget", "ssh", "scp", "nc",
            "ncat", "socat", "chisel", "bloodhound", "sharphound", "ldapsearch",
            "ldapwhoami", "kerbrute", "kerberoast", "crackmapexec", "netexec",
            "impacket-psexec", "impacket-wmiexec", "impacket-secretsdump",
            "GetUserSPNs", "rubeus", "certipy", "mimikatz", "lsadump", "cobaltstrike",
            "beacon", "sliver", "burpsuite", "zap", "xsser", "commix", "tplmap",
            "dalfox", "webshock", "ansible", "terraform", "kubectl", "docker",
            "openssl", "jwt_tool", "responder", "bettercap", "ettercap", "tcpdump",
            "wireshark/tshark", "volatility", "foremost", "testssl.sh",
            "nuclei-templates",
        ]
        for tool in required:
            with self.subTest(tool=tool):
                result = server.kali_map_to_mitre(tool, "")
                self.assertTrue(result["mapped"], f"{tool} missing from curated table")
                self.assertRegex(result["technique_id"], r"^T\d{4}(\.\d{3})?$")


class SuggestToolchainTests(unittest.TestCase):
    def _tools(self, findings):
        result = server.kali_suggest_toolchain(findings, 20)
        self.assertEqual(result["findings"], len(findings) if isinstance(findings, list) else 1)
        return result, [step["tool"] for step in result["chain"]]

    def test_http_port_drives_web_chain(self):
        result, tools = self._tools([{"type": "open_port", "port": 80}])
        self.assertIn("whatweb", tools)
        self.assertIn("nikto", tools)
        self.assertIn("ffuf", tools)
        self.assertIn("nuclei", tools)
        self.assertEqual(result["chain"][0]["step"], 1)
        self.assertIn("execution_policy", result)
        for step in result["chain"]:
            self.assertIsInstance(step["requires_authorization"], bool)
            self.assertTrue(any(marker in step["command_template"] for marker in PLACEHOLDERS))

    def test_wordpress_adds_wpscan(self):
        _, tools = self._tools([
            {"type": "open_port", "port": 80},
            {"type": "web_tech", "value": "wordpress"},
        ])
        self.assertIn("wpscan", tools)

    def test_smb_chain(self):
        _, tools = self._tools([{"type": "service", "service": "smb"}])
        self.assertIn("enum4linux", tools)
        self.assertIn("netexec", tools)

    def test_ldap_chain(self):
        _, tools = self._tools([{"type": "open_port", "port": 389}])
        self.assertIn("ldapsearch", tools)
        self.assertIn("bloodhound", tools)
        self.assertIn("kerbrute", tools)

    def test_ssh_chain_includes_credential_audit(self):
        _, tools = self._tools([{"type": "open_port", "port": 22}])
        self.assertIn("ssh-audit", tools)
        self.assertIn("hydra", tools)

    def test_mysql_without_web_has_no_sqlmap(self):
        _, tools = self._tools([{"type": "open_port", "port": 3306}])
        self.assertNotIn("sqlmap", tools)

    def test_mysql_with_web_adds_non_destructive_sqlmap(self):
        result, tools = self._tools([
            {"type": "open_port", "port": 3306},
            {"type": "open_port", "port": 80},
        ])
        self.assertIn("sqlmap", tools)
        sqlmap_steps = [s for s in result["chain"] if s["tool"] == "sqlmap"]
        for step in sqlmap_steps:
            self.assertIn("--batch", step["command_template"])
            self.assertIn("space2comment", step["command_template"])
            self.assertNotIn("--dump", step["command_template"])

    def test_sqli_finding_adds_sqlmap(self):
        _, tools = self._tools([{"type": "sql_injection", "value": "id=1' OR 1=1--"}])
        self.assertIn("sqlmap", tools)

    def test_container_findings_add_kubectl_and_docker(self):
        _, tools = self._tools([{"type": "kubernetes", "value": "k8s cluster"}])
        self.assertIn("kubectl", tools)
        self.assertIn("docker", tools)

    def test_free_form_string_findings(self):
        result, tools = self._tools("open port 80, wordpress detected")
        self.assertIn("whatweb", tools)
        self.assertIn("wpscan", tools)
        self.assertEqual(result["findings"], 1)

    def test_limit_is_respected(self):
        result = server.kali_suggest_toolchain([{"type": "open_port", "port": 80}], 2)
        self.assertEqual(len(result["chain"]), 2)

    def test_empty_findings_still_returns_a_chain(self):
        result = server.kali_suggest_toolchain([], 8)
        self.assertEqual(result["findings"], 0)
        self.assertTrue(result["chain"])
        self.assertTrue(result["notes"])

    def test_output_is_deterministic(self):
        findings = [{"type": "open_port", "port": 445}, {"type": "web_tech", "value": "wordpress"}]
        self.assertEqual(
            server.kali_suggest_toolchain(findings, 8),
            server.kali_suggest_toolchain(findings, 8),
        )


class PlanPhaseTests(unittest.TestCase):
    def test_all_six_phases(self):
        for phase in PHASES:
            with self.subTest(phase=phase):
                result = server.kali_plan_phase(phase, "10.0.0.5")
                self.assertTrue(result["ok"])
                self.assertEqual(result["phase"], phase)
                self.assertEqual(result["target"], "10.0.0.5")
                self.assertTrue(result["steps"])
                self.assertIn("execution_policy", result)
                self.assertTrue(result["mitre_coverage"])
                for order, step in enumerate(result["steps"], start=1):
                    self.assertEqual(step["order"], order)
                    self.assertIsInstance(step["requires_authorization"], bool)
                    self.assertTrue(step["title"])
                    self.assertTrue(step["description"])
                    self.assertTrue(step["expected_output"])
                    self.assertIsInstance(step["tools"], list)
                    self.assertIsInstance(step["mitre_tactics"], list)

    def test_phase_aliases(self):
        cases = {
            "information-gathering": "recon",
            "vuln-analysis": "vulnerability-analysis",
            "vulnerability-analysis": "vulnerability-analysis",
            "report": "reporting",
            "attack": "exploitation",
        }
        for alias, expected in cases.items():
            with self.subTest(alias=alias):
                result = server.kali_plan_phase(alias, "10.0.0.5")
                self.assertTrue(result["ok"])
                self.assertEqual(result["phase"], expected)

    def test_invalid_phase_returns_structured_error(self):
        result = server.kali_plan_phase("not-a-phase", "10.0.0.5")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_empty_target_returns_structured_error(self):
        result = server.kali_plan_phase("recon", "  ")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_plan_is_deterministic(self):
        self.assertEqual(
            server.kali_plan_phase("exploitation", "10.0.0.5"),
            server.kali_plan_phase("exploitation", "10.0.0.5"),
        )


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="kali_gpt_test_")
        self.previous = os.environ.get(server.MEMORY_DB_ENV)
        os.environ[server.MEMORY_DB_ENV] = os.path.join(self.tmpdir, "nested", "memory.db")

    def tearDown(self):
        if self.previous is None:
            os.environ.pop(server.MEMORY_DB_ENV, None)
        else:
            os.environ[server.MEMORY_DB_ENV] = self.previous
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_round_trip_and_ranking(self):
        first = server.kali_record_memory({
            "target_fingerprint": "acme-corp:443",
            "tool": "nuclei",
            "technique_id": "T1190",
            "outcome": "success",
            "notes": "wordpress template confirmed outdated plugin",
            "tags": ["wordpress", "web"],
        })
        self.assertTrue(first["ok"])
        self.assertGreater(first["id"], 0)
        self.assertTrue(first["memory_db"].endswith("memory.db"))

        second = server.kali_record_memory({
            "target_fingerprint": "other-host:80",
            "tool": "nmap",
            "technique_id": "T1046",
            "outcome": "failure",
            "notes": "filtered scan missed 8080",
            "tags": ["recon"],
        })
        self.assertTrue(second["ok"])
        self.assertNotEqual(first["id"], second["id"])

        recalled = server.kali_recall_memory("acme-corp:443", "", 10)
        self.assertEqual(recalled["total"], 2)
        self.assertEqual(recalled["entries"][0]["target_fingerprint"], "acme-corp:443")
        self.assertGreater(recalled["entries"][0]["score"], recalled["entries"][1]["score"])
        self.assertEqual(recalled["entries"][0]["tags"], ["wordpress", "web"])
        self.assertEqual(recalled["entries"][0]["outcome"], "success")
        self.assertTrue(recalled["entries"][0]["updated_at"].endswith("Z"))

        by_tool = server.kali_recall_memory("", "nmap", 10)
        self.assertEqual(by_tool["entries"][0]["tool"], "nmap")

        by_tag = server.kali_recall_memory("", "wordpress", 10)
        self.assertEqual(by_tag["entries"][0]["tool"], "nuclei")

    def test_empty_fingerprint_returns_most_recent(self):
        server.kali_record_memory({"target_fingerprint": "a:1", "tool": "nmap"})
        server.kali_record_memory({"target_fingerprint": "b:2", "tool": "nikto"})
        recalled = server.kali_recall_memory("", "", 10)
        self.assertEqual(recalled["total"], 2)
        self.assertEqual(recalled["entries"][0]["tool"], "nikto")

    def test_notes_and_tag_caps(self):
        server.kali_record_memory({
            "target_fingerprint": "cap:1",
            "tool": "nmap",
            "notes": "x" * 5000,
            "tags": [f"tag{i}" for i in range(50)],
        })
        recalled = server.kali_recall_memory("cap:1", "", 1)
        entry = recalled["entries"][0]
        self.assertLessEqual(len(entry["notes"]), 2000)
        self.assertLessEqual(len(entry["tags"]), 16)

    def test_invalid_outcome_is_defaulted(self):
        result = server.kali_record_memory({
            "target_fingerprint": "x:1", "tool": "nmap", "outcome": "weird"})
        self.assertTrue(result["ok"])
        recalled = server.kali_recall_memory("x:1", "", 1)
        self.assertEqual(recalled["entries"][0]["outcome"], "partial")

    def test_missing_fields_are_rejected(self):
        self.assertFalse(server.kali_record_memory({"tool": "nmap"})["ok"])
        self.assertFalse(server.kali_record_memory({"target_fingerprint": "a:1"})["ok"])
        self.assertFalse(server.kali_record_memory("not-a-dict")["ok"])

    def test_missing_db_read_returns_empty_list(self):
        os.environ[server.MEMORY_DB_ENV] = os.path.join(self.tmpdir, "absent", "memory.db")
        recalled = server.kali_recall_memory("anything", "nmap", 10)
        self.assertEqual(recalled["entries"], [])
        self.assertEqual(recalled["total"], 0)

    def test_status_reports_entry_count(self):
        server.kali_record_memory({"target_fingerprint": "a:1", "tool": "nmap"})
        status = server.kali_gpt_status()
        self.assertTrue(status["ok"])
        self.assertEqual(status["tool_count"], 6)
        self.assertEqual(status["memory_entries"], 1)
        self.assertEqual(status["provider"], "curated-offline-rule-engine")
        self.assertTrue(status["memory_db"].endswith("memory.db"))


if __name__ == "__main__":
    unittest.main()
