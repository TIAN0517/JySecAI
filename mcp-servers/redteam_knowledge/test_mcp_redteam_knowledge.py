import unittest

import mcp_redteam_knowledge as server


class RedTeamKnowledgeTests(unittest.TestCase):
    def test_technique_validation(self):
        self.assertEqual(server._technique_id("t1059.001"), "T1059.001")
        with self.assertRaises(ValueError):
            server._technique_id("CVE-2024-1234")

    def test_compact_attack_technique(self):
        item = {
            "type": "attack-pattern",
            "name": "PowerShell",
            "description": "Example",
            "external_references": [{
                "source_name": "mitre-attack",
                "external_id": "T1059.001",
                "url": "https://attack.mitre.org/techniques/T1059/001/",
            }],
            "kill_chain_phases": [{"phase_name": "execution"}],
            "x_mitre_platforms": ["Windows"],
        }
        compact = server._compact_technique(item)
        self.assertEqual(compact["technique_id"], "T1059.001")
        self.assertEqual(compact["tactics"], ["execution"])

    def test_gtfobin_examples_are_opt_in(self):
        item = {"functions": {"shell": [{"code": "sh", "contexts": {"sudo": None}}]}}
        definitions = {"shell": {"mitre": ["T1059"]}}
        compact = server._compact_gtfobin("demo", item, definitions, False)
        self.assertNotIn("examples", compact)
        self.assertEqual(compact["mitre_ids"], ["T1059"])

    def test_atomic_commands_are_opt_in(self):
        original_bytes = server._request_bytes
        original_get = server._cache_get
        original_set = server._cache_set
        try:
            server._cache_get = lambda key: None
            server._cache_set = lambda key, value, ttl: value
            server._request_bytes = lambda url: b"""attack_technique: T1059
display_name: Command and Scripting Interpreter
atomic_tests:
  - name: demo
    description: demo test
    supported_platforms: [linux]
    executor:
      name: sh
      command: echo demo
"""
            result = server._atomic_tests("T1059", False, 5)
            self.assertNotIn("command", result["tests"][0])
            result = server._atomic_tests("T1059", True, 5)
            self.assertEqual(result["tests"][0]["command"], "echo demo")
        finally:
            server._request_bytes = original_bytes
            server._cache_get = original_get
            server._cache_set = original_set


if __name__ == "__main__":
    unittest.main()
