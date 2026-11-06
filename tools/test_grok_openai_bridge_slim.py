"""Unit tests for the Grok device-code login helper. No network."""
import base64
import json
import tempfile
import time
import unittest
from pathlib import Path

import grok_openai_bridge_slim as bridge


def _jwt(exp: int, tier: int | None = None) -> str:
    payload = {"exp": exp}
    if tier is not None:
        payload["tier"] = tier
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"h.{body}.s"


class GrokLoginTests(unittest.TestCase):
    def test_rejects_non_xai_endpoint(self):
        bridge.assert_xai_https("https://auth.x.ai/oauth2/token")
        bridge.assert_xai_https("https://api.x.ai/v1")
        with self.assertRaises(RuntimeError):
            bridge.assert_xai_https("http://auth.x.ai/oauth2/token")
        with self.assertRaises(RuntimeError):
            bridge.assert_xai_https("https://evil.example/oauth2/token")

    def test_pick_bundle_prefers_tier_over_expiry(self):
        older_tiered = bridge._bundle(_jwt(1_700_000_000, tier=5), "r1", source="grok-cli")
        newer_notier = bridge._bundle(_jwt(1_800_000_000, tier=None), "r2", source="hermes")
        picked = bridge.pick_bundle([newer_notier, older_tiered])
        self.assertEqual(picked["refresh_token"], "r1")
        self.assertEqual(picked["tier"], 5)

    def test_pick_bundle_prefers_later_expiry_when_tier_equal(self):
        older = bridge._bundle(_jwt(1_700_000_000, tier=5), "r1")
        newer = bridge._bundle(_jwt(1_800_000_000, tier=5), "r2")
        picked = bridge.pick_bundle([older, newer])
        self.assertEqual(picked["refresh_token"], "r2")

    def test_merge_keeps_other_providers(self):
        store = {
            "version": 1,
            "providers": {"openai": {"tokens": {"access_token": "keep-me"}}},
            "credential_pool": {"openai": [{"access_token": "keep-me"}]},
        }
        bundle = bridge._bundle("access-new", "refresh-new", "https://auth.x.ai/oauth2/token")
        merged = bridge.merge_hermes_store(store, bundle, {"token_endpoint": "https://auth.x.ai/oauth2/token"})
        self.assertEqual(merged["providers"]["openai"]["tokens"]["access_token"], "keep-me")
        self.assertEqual(merged["providers"]["xai-oauth"]["auth_mode"], "oauth_device_code")
        self.assertEqual(merged["providers"]["xai-oauth"]["tokens"]["access_token"], "access-new")
        self.assertEqual(merged["credential_pool"]["xai-oauth"][0]["refresh_token"], "refresh-new")
        self.assertNotIn("device_code", merged["providers"]["xai-oauth"])

    def test_bundle_from_grok_cli(self):
        store = {
            f"{bridge.XAI_OAUTH_ISSUER}::{bridge.XAI_OAUTH_CLIENT_ID}": {
                "key": _jwt(1_900_000_000, tier=5),
                "refresh_token": "rt",
                "auth_mode": "oidc",
            }
        }
        bundle = bridge.bundle_from_grok_cli(store)
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle["tier"], 5)
        self.assertEqual(bundle["source"], "grok-cli")
        self.assertEqual(bundle["refresh_token"], "rt")

    def test_hard_quota_detection(self):
        msg = {
            "error": (
                "Too many requests ... Requests per Minute (actual/limit): 0/0. "
                "Your rate limit tier is determined based on your historical API spend."
            )
        }
        self.assertTrue(bridge.is_hard_quota_error(429, msg))
        self.assertFalse(bridge.is_soft_rate_limit(429, msg))
        soft = {"error": "You are sending requests too quickly. Please slow down"}
        self.assertTrue(bridge.is_soft_rate_limit(429, soft))
        self.assertFalse(bridge.is_hard_quota_error(429, soft))

    def test_status_hides_device_code_and_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge.OAUTH_PATH = Path(tmp) / "missing.json"
            bridge.AUTH_PATH = Path(tmp) / "missing-hermes.json"
            bridge.GROK_CLI_AUTH_PATH = Path(tmp) / "missing-grok.json"
            bridge.invalidate_caches()
            with bridge._state_lock:
                bridge._pending.update({
                    "device_code": "secret-device-code",
                    "user_code": "ABCD-1234",
                    "verification_uri": "https://auth.x.ai/device",
                    "verification_uri_complete": "https://auth.x.ai/device?user_code=ABCD-1234",
                    "interval": 5,
                    "expires_at": time.time() + 60,
                    "status": "pending",
                    "error": "",
                })
            view = bridge.public_login_view(use_cache=False)
        self.assertEqual(view["status"], "pending")
        self.assertEqual(view["user_code"], "ABCD-1234")
        self.assertNotIn("device_code", view)
        self.assertNotIn("access_token", view)
        blob = json.dumps(view)
        self.assertNotIn("secret-device-code", blob)

    def test_oauth_scope_includes_conversations(self):
        self.assertIn("conversations:read", bridge.XAI_OAUTH_SCOPE)
        self.assertIn("workspaces:write", bridge.XAI_OAUTH_SCOPE)

    def test_login_reuses_tiered_token_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            grok_path = Path(tmp) / "auth.json"
            tok = _jwt(int(time.time()) + 3600, tier=5)
            grok_path.write_text(
                json.dumps({
                    f"{bridge.XAI_OAUTH_ISSUER}::{bridge.XAI_OAUTH_CLIENT_ID}": {
                        "key": tok,
                        "refresh_token": "rt",
                    }
                }),
                encoding="utf-8",
            )
            bridge.GROK_CLI_AUTH_PATH = grok_path
            bridge.OAUTH_PATH = Path(tmp) / "local.json"
            bridge.AUTH_PATH = Path(tmp) / "hermes.json"
            bridge.invalidate_caches()
            with bridge._state_lock:
                bridge._pending.update({
                    "device_code": "",
                    "user_code": "",
                    "verification_uri": "",
                    "verification_uri_complete": "",
                    "interval": 5,
                    "expires_at": 0.0,
                    "status": "idle",
                    "error": "",
                })
            view = bridge.start_device_login(force=False)
            self.assertEqual(view["status"], "ok")
            self.assertTrue(view.get("reused"))
            self.assertEqual(view.get("tier"), 5)
            self.assertEqual(bridge._pending["status"], "idle")


if __name__ == "__main__":
    unittest.main()
