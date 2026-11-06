"""Offline unit tests for the Claude-Red skills MCP.

All network access is monkeypatched at the module level (``_request_bytes``),
so the suite runs without connectivity.
"""

import asyncio
import json
import os
import shutil
import tempfile
import unittest

import mcp_redteam_skills as server


LOCAL_AD_SKILL = """---
name: active-directory-demo
description: >-
  Active Directory attack playbook. Use when assessing on-prem AD,
  Kerberoasting or ADCS deployments.
metadata:
  tags: [渗透测试, penetration-testing]
---

# Active Directory demo

Kerberoasting walkthrough.
"""

LOCAL_WEB_SKILL = """---
name: web-sqli-demo
description: SQL injection testing skill. Trigger on: SQLi, union select, blind sqli.
---

# SQLi demo

sqli payload notes.
"""

BROKEN_FRONTMATTER_SKILL = """---
name: broken-skill
description: "unterminated quote: with colon
  continuation: yes
---

body
"""

UPSTREAM_SKILL_MD = """---
name: offensive-sqli
description: "SQL injection methodology. Use when testing web application SQL injection."
---

# Offensive SQLi

upstream body
"""

UPSTREAM_CATALOG = {
    "name": "claude-red",
    "version": "0.3.0",
    "license": "MIT",
    "categories": {"web": ["offensive-sqli"]},
    "skills": [
        {
            "name": "offensive-sqli",
            "category": "web",
            "path": "Skills/web/offensive-sqli/SKILL.md",
            "description": "SQL injection methodology. Use when testing web application SQL injection.",
        }
    ],
    "skill_count": 1,
    "category_count": 1,
}


class RedTeamSkillsBase(unittest.TestCase):
    """共用測試環境：暫存 skills 根目錄 + 停用網路。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="redteam-skills-")
        self.skills_root = os.path.join(self.tmpdir, "skills")
        os.makedirs(self.skills_root)
        self._write_skill("active-directory-demo", LOCAL_AD_SKILL)
        self._write_skill("web-sqli-demo", LOCAL_WEB_SKILL)
        self._write_skill("broken-skill", BROKEN_FRONTMATTER_SKILL)
        # 沒有 SKILL.md 的目錄應該被忽略
        os.makedirs(os.path.join(self.skills_root, "not-a-skill"), exist_ok=True)

        self._original_request = server._request_bytes
        self._original_root = server._SKILLS_ROOT
        self._original_resolved = server._SKILLS_ROOT_RESOLVED

        server._request_bytes = self._offline_request
        server._set_skills_root(self.skills_root)
        server._cache_clear()

    def tearDown(self):
        server._request_bytes = self._original_request
        server._SKILLS_ROOT = self._original_root
        server._SKILLS_ROOT_RESOLVED = self._original_resolved
        server._cache_clear()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_skill(self, name, content):
        folder = os.path.join(self.skills_root, name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "SKILL.md"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    @staticmethod
    def _offline_request(url, max_bytes=server.MAX_CATALOG_BYTES):
        raise server.SourceError("network disabled in tests")

    @staticmethod
    def _fake_request(url, max_bytes=server.MAX_CATALOG_BYTES):
        if url.endswith("claude-skills.json"):
            return json.dumps(UPSTREAM_CATALOG).encode("utf-8")
        if url.endswith("SKILL.md"):
            return UPSTREAM_SKILL_MD.encode("utf-8")
        raise server.SourceError(f"unexpected url in tests: {url}")


class ToolRegistrationTests(RedTeamSkillsBase):
    def test_exactly_five_tools_are_exposed(self):
        tools = asyncio.run(server.app.list_tools())
        names = sorted(tool.name for tool in tools)
        self.assertEqual(names, [
            "redteam_get_skill",
            "redteam_list_skill_categories",
            "redteam_list_skills",
            "redteam_match_skills",
            "redteam_search_skills",
        ])
        for tool in tools:
            self.assertTrue(tool.description, f"{tool.name} is missing a description")

    def test_no_execution_helpers_are_defined(self):
        """伺服器必須保持純讀取：不得引入 subprocess / os.system。"""
        with open(server.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        for forbidden in ("import subprocess", "from subprocess", "os.system(",
                          "os.popen(", "subprocess.run", "subprocess.Popen", "shell=True"):
            self.assertNotIn(forbidden, source)


class LocalDiscoveryTests(RedTeamSkillsBase):
    def test_local_index_lists_skill_files_only(self):
        rows = server._local_index()
        names = sorted(row["name"] for row in rows)
        self.assertEqual(names, ["active-directory-demo", "broken-skill", "web-sqli-demo"])
        for row in rows:
            self.assertEqual(row["source"], "local")
            self.assertTrue(row["local_path"].endswith("SKILL.md"))

    def test_local_category_mapping(self):
        rows = {row["name"]: row for row in server._local_index()}
        self.assertEqual(rows["active-directory-demo"]["category"], "active-directory")
        self.assertEqual(rows["web-sqli-demo"]["category"], "web")
        self.assertEqual(rows["broken-skill"]["category"], server.LOCAL_FALLBACK_CATEGORY)

    def test_missing_local_root_returns_empty_list(self):
        server._set_skills_root(None)
        server._cache_clear()
        self.assertEqual(server._local_index(), [])
        result = server.redteam_list_skills()
        self.assertEqual(result["skills"], [])
        self.assertEqual(result["total"], 0)

    def test_list_skills_returns_local_rows(self):
        result = server.redteam_list_skills()
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["limit"], 50)
        self.assertEqual(result["category"], "")
        self.assertTrue(all(row["source"] == "local" for row in result["skills"]))

    def test_list_skills_filters_by_category(self):
        result = server.redteam_list_skills(category="web")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["skills"][0]["name"], "web-sqli-demo")
        self.assertEqual(result["category"], "web")

    def test_list_categories_counts_sources(self):
        result = server.redteam_list_skill_categories()
        self.assertEqual(result["sources"], {"local": 3, "upstream": 0})
        self.assertEqual(result["total"], 3)
        categories = {entry["name"]: entry for entry in result["categories"]}
        self.assertEqual(categories["web"]["skill_count"], 1)
        self.assertEqual(categories["web"]["sources"], ["local"])


class FrontMatterTests(RedTeamSkillsBase):
    def test_yaml_front_matter_is_parsed(self):
        meta = server._parse_front_matter(LOCAL_AD_SKILL)
        self.assertEqual(meta["name"], "active-directory-demo")
        self.assertIn("Kerberoasting", meta["description"])
        self.assertEqual(meta["metadata"]["tags"], ["渗透测试", "penetration-testing"])

    def test_folded_description_is_joined(self):
        meta = server._parse_front_matter(LOCAL_AD_SKILL)
        self.assertIn("Active Directory attack playbook", meta["description"])
        self.assertIn("ADCS deployments", meta["description"])

    def test_broken_yaml_falls_back_to_key_value_scan(self):
        meta = server._parse_front_matter(BROKEN_FRONTMATTER_SKILL)
        self.assertEqual(meta["name"], "broken-skill")
        self.assertIn("unterminated quote", meta["description"])

    def test_document_without_front_matter(self):
        self.assertEqual(server._parse_front_matter("# no front matter\n"), {})

    def test_tags_are_extracted(self):
        meta = server._parse_front_matter(LOCAL_AD_SKILL)
        tags = server._extract_tags(meta)
        self.assertIn("渗透测试", tags)
        self.assertIn("penetration-testing", tags)


class SearchTests(RedTeamSkillsBase):
    def test_search_matches_description_tokens(self):
        result = server.redteam_search_skills("kerberoasting")
        self.assertEqual(result["query"], "kerberoasting")
        self.assertGreaterEqual(result["total"], 1)
        self.assertEqual(result["results"][0]["name"], "active-directory-demo")
        self.assertGreater(result["results"][0]["score"], 0)

    def test_search_matches_name(self):
        result = server.redteam_search_skills("web-sqli-demo")
        self.assertGreaterEqual(result["total"], 1)
        self.assertEqual(result["results"][0]["name"], "web-sqli-demo")

    def test_search_rejects_control_characters(self):
        result = server.redteam_search_skills("bad\x00query")
        self.assertFalse(result["ok"])
        self.assertEqual(result["results"], [])
        self.assertIn("control characters", result["error"])

    def test_search_rejects_empty_query(self):
        result = server.redteam_search_skills("   ")
        self.assertFalse(result["ok"])
        self.assertEqual(result["total"], 0)

    def test_search_respects_limit(self):
        result = server.redteam_search_skills("attack", limit=1)
        self.assertEqual(len(result["results"]), 1)


class MatchTests(RedTeamSkillsBase):
    def test_trigger_matching_prefers_matching_skill(self):
        result = server.redteam_match_skills(
            "We need to assess an on-prem Active Directory domain with Kerberoasting."
        )
        self.assertGreaterEqual(result["total"], 1)
        best = result["matches"][0]
        self.assertEqual(best["name"], "active-directory-demo")
        self.assertEqual(best["source"], "local")
        self.assertGreater(best["score"], 0)
        self.assertTrue(best["reason"])

    def test_match_result_shape(self):
        result = server.redteam_match_skills("union select injection in a login form")
        self.assertTrue(result["text"].startswith("union select"))
        for match in result["matches"]:
            self.assertIn("name", match)
            self.assertIn("score", match)
            self.assertIn("reason", match)
            self.assertIn("source", match)

    def test_match_without_any_overlap_is_empty(self):
        result = server.redteam_match_skills("zzzunmatchabletoken qqqnothing")
        self.assertEqual(result["matches"], [])
        self.assertEqual(result["total"], 0)

    def test_match_rejects_control_characters(self):
        result = server.redteam_match_skills("bad\x07text")
        self.assertFalse(result["ok"])
        self.assertEqual(result["matches"], [])


class SecurityTests(RedTeamSkillsBase):
    def test_path_traversal_is_rejected(self):
        for bad in ("../../etc/passwd", "..", "../../secrets", "a/b"):
            result = server.redteam_get_skill(bad)
            self.assertFalse(result["ok"])
            self.assertIn("skill name", result["error"])
            self.assertIsNone(server._local_skill_path(bad))

    def test_local_path_stays_inside_skills_root(self):
        root = os.path.realpath(self.skills_root)
        path = server._local_skill_path("active-directory-demo")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.realpath(path).startswith(root + os.sep))

    def test_symlink_escape_is_rejected(self):
        outside = os.path.join(self.tmpdir, "outside")
        os.makedirs(outside, exist_ok=True)
        with open(os.path.join(outside, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nname: escaped\n---\n")
        link = os.path.join(self.skills_root, "escaped")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertIsNone(server._local_skill_path("escaped"))

    def test_control_characters_are_rejected(self):
        result = server.redteam_get_skill("skill\x00name")
        self.assertFalse(result["ok"])
        self.assertIn("control characters", result["error"])

    def test_limit_is_clamped(self):
        self.assertEqual(server._clamp_limit(100000, 50), server.MAX_LIMIT)
        self.assertEqual(server._clamp_limit(-5, 50), 1)
        self.assertEqual(server._clamp_limit(0, 50), 1)
        self.assertEqual(server._clamp_limit("not-a-number", 50), 50)
        self.assertEqual(server.redteam_list_skills(limit=100000)["limit"], server.MAX_LIMIT)
        search = server.redteam_search_skills("attack", limit=9999)
        self.assertLessEqual(len(search["results"]), server.MAX_LIMIT)

    def test_outbound_host_allowlist(self):
        with self.assertRaises(server.SourceError):
            self._original_request("https://example.com/evil")
        with self.assertRaises(server.SourceError):
            self._original_request("http://raw.githubusercontent.com/x")

    def test_upstream_path_allowlist(self):
        with self.assertRaises(server.SourceError):
            server._upstream_content("../../../etc/passwd")
        with self.assertRaises(server.SourceError):
            server._upstream_content("Skills/web/offensive-sqli/../../evil.md")


class OfflineFallbackTests(RedTeamSkillsBase):
    def test_local_skill_is_available_offline(self):
        result = server.redteam_get_skill("active-directory-demo")
        self.assertTrue(result["ok"])
        self.assertEqual(result["skill"]["source"], "local")
        self.assertIn("Kerberoasting walkthrough", result["skill"]["content"])
        self.assertEqual(result["skill"]["name"], "active-directory-demo")

    def test_unknown_skill_returns_structured_error(self):
        result = server.redteam_get_skill("no-such-skill-anywhere")
        self.assertFalse(result["ok"])
        self.assertIsInstance(result["error"], str)
        self.assertIn("not found", result["error"])

    def test_offline_upstream_only_skill_returns_structured_error(self):
        result = server.redteam_get_skill("offensive-sqli")
        self.assertFalse(result["ok"])
        self.assertIsInstance(result["error"], str)

    def test_categories_still_work_offline(self):
        result = server.redteam_list_skill_categories()
        self.assertEqual(result["sources"], {"local": 3, "upstream": 0})
        self.assertTrue(result["categories"])


class UpstreamMergeTests(RedTeamSkillsBase):
    def setUp(self):
        super().setUp()
        server._request_bytes = self._fake_request
        server._cache_clear()

    def test_upstream_catalog_is_parsed(self):
        rows = server._upstream_index()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["name"], "offensive-sqli")
        self.assertEqual(row["category"], "web")
        self.assertEqual(row["source"], "upstream")
        self.assertEqual(row["upstream_path"], "Skills/web/offensive-sqli/SKILL.md")

    def test_sources_are_merged_and_labelled(self):
        result = server.redteam_list_skills()
        self.assertEqual(result["total"], 4)
        self.assertEqual(sorted({row["source"] for row in result["skills"]}), ["local", "upstream"])

    def test_category_sources_merge_both(self):
        result = server.redteam_list_skill_categories()
        self.assertEqual(result["sources"], {"local": 3, "upstream": 1})
        categories = {entry["name"]: entry for entry in result["categories"]}
        self.assertEqual(categories["web"]["skill_count"], 2)
        self.assertEqual(categories["web"]["sources"], ["local", "upstream"])

    def test_upstream_content_is_fetched_on_demand(self):
        result = server.redteam_get_skill("offensive-sqli")
        self.assertTrue(result["ok"])
        self.assertEqual(result["skill"]["source"], "upstream")
        self.assertEqual(result["skill"]["category"], "web")
        self.assertIn("upstream body", result["skill"]["content"])
        self.assertIn("SQL injection methodology", result["skill"]["description"])

    def test_upstream_fetch_failure_falls_back_to_local(self):
        def failing(url, max_bytes=server.MAX_CATALOG_BYTES):
            if url.endswith("claude-skills.json"):
                return json.dumps(UPSTREAM_CATALOG).encode("utf-8")
            raise server.SourceError("upstream body unavailable")

        server._request_bytes = failing
        server._cache_clear()
        result = server.redteam_get_skill("offensive-sqli")
        self.assertFalse(result["ok"])
        self.assertIn("could not be retrieved from upstream", result["error"])


if __name__ == "__main__":
    unittest.main()
