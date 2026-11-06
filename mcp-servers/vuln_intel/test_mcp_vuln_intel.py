import unittest

import mcp_vuln_intel as server


class VulnIntelTests(unittest.TestCase):
    def test_validate_cve(self):
        self.assertEqual(server._validate_cve_id("cve-2024-3400"), "CVE-2024-3400")
        with self.assertRaises(ValueError):
            server._validate_cve_id("3400")

    def test_safe_query(self):
        self.assertEqual(server._safe_query("  Apache   HTTPD  "), "Apache HTTPD")
        with self.assertRaises(ValueError):
            server._safe_query("--help")

    def test_compact_nvd(self):
        item = {
            "cve": {
                "id": "CVE-2024-0001",
                "vulnStatus": "Analyzed",
                "descriptions": [{"lang": "en", "value": "example"}],
                "metrics": {"cvssMetricV31": [{"source": "nvd", "cvssData": {"version": "3.1", "baseScore": 9.8, "baseSeverity": "CRITICAL", "vectorString": "CVSS:3.1/..."}}]},
                "weaknesses": [{"description": [{"lang": "en", "value": "CWE-78"}]}],
            }
        }
        compact = server._compact_nvd_cve(item)
        self.assertEqual(compact["id"], "CVE-2024-0001")
        self.assertEqual(compact["cvss"]["score"], 9.8)
        self.assertEqual(compact["weaknesses"], ["CWE-78"])

    def test_kev_overrides_priority(self):
        risk = server._risk_summary({"cvss": {"score": 4.0}}, {"score": 0.01}, {"cveID": "CVE-2024-0001"}, 0)
        self.assertEqual(risk["priority"], "critical")
        self.assertTrue(risk["known_exploited_in_the_wild"])


if __name__ == "__main__":
    unittest.main()
