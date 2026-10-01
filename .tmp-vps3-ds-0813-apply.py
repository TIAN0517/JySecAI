#!/usr/bin/env python3
"""Wire DeepSeek 0813 alias on vps3 WSL Hermes + OpenClaw. Never print secrets."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path("/home/bossjy/.hermes")
OPENCLAW = Path("/home/bossjy/.openclaw")
KEY_FILE = Path("/tmp/ds-0813.key")
KEY_FILE_WIN = Path("/mnt/c/Users/Administrator/Desktop/JySecAI/_ds.key")
PROXY_SRC = Path("/mnt/c/Users/Administrator/Desktop/JySecAI/_ds_alias_proxy.py")
PROXY_DST = HERMES / "ds-alias-proxy.py"
CFG = HERMES / "config.yaml"
AUTH = HERMES / "auth.json"
ENV = HERMES / ".env"
OC = OPENCLAW / "openclaw.json"
PROXY_HOST = "127.0.0.1"
PROXY_PORT = "18790"
PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}/v1"


def upsert_env(path: Path, pairs: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for ln in lines:
        if "=" in ln and not ln.strip().startswith("#"):
            name = ln.split("=", 1)[0]
            if name in pairs:
                out.append(f"{name}={pairs[name]}")
                seen.add(name)
                continue
        out.append(ln)
    for name, val in pairs.items():
        if name not in seen:
            if out and out[-1].strip():
                out.append("")
            out.append(f"{name}={val}")
    body = "\n".join(out)
    if not body.endswith("\n"):
        body += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def patch_yaml_text(text: str) -> str:
    aliases = (
        "model_aliases:\n"
        "  deepseek/deepseek-v4-pro-0813:\n"
        "    model: deepseek-v4-pro\n"
        "    provider: deepseek\n"
        "    key_env: DEEPSEEK_API_KEY\n"
        "  deepseek-v4-pro-0813:\n"
        "    model: deepseek-v4-pro\n"
        "    provider: deepseek\n"
        "    key_env: DEEPSEEK_API_KEY\n"
        "  deepseek/deepseek-v4-pro:\n"
        "    model: deepseek-v4-pro\n"
        "    provider: deepseek\n"
        "    key_env: DEEPSEEK_API_KEY\n"
    )
    if "deepseek/deepseek-v4-pro-0813:" not in text:
        if "model_aliases:" in text:
            text = text.replace("model_aliases:\n", aliases, 1)
        elif "custom_providers:" in text:
            text = text.replace("custom_providers:", aliases + "custom_providers:", 1)
        else:
            text = aliases + text
    if "providers:" in text and "  deepseek:" not in text.split("providers:", 1)[1][:800]:
        block = (
            "  deepseek:\n"
            "    name: DeepSeek\n"
            f"    base_url: {PROXY_URL}\n"
            "    key_env: DEEPSEEK_API_KEY\n"
            "    model: deepseek-v4-pro\n"
            "    models:\n"
            "      deepseek-v4-pro:\n"
            "        context_length: 1000000\n"
            "      deepseek-v4-pro-0813:\n"
            "        context_length: 1000000\n"
            "      deepseek/deepseek-v4-pro-0813:\n"
            "        context_length: 1000000\n"
            "      deepseek-flash:\n"
            "        context_length: 1000000\n"
        )
        # insert after providers:\n
        text = text.replace("providers:\n", "providers:\n" + block, 1)
    return text


def ensure_proxy() -> None:
    if not PROXY_SRC.exists():
        raise SystemExit("missing proxy source")
    HERMES.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROXY_SRC, PROXY_DST)
    print("proxy-copied", PROXY_DST.exists())
    probe = subprocess.run(
        ["ss", "-ltn"], capture_output=True, text=True, check=False
    )
    listening = f":{PROXY_PORT}" in (probe.stdout or "")
    print("proxy-listening-before", listening)
    if not listening:
        log = HERMES / "ds-alias-proxy.log"
        with log.open("ab") as fh:
            subprocess.Popen(
                [sys.executable, str(PROXY_DST)],
                stdout=fh,
                stderr=fh,
                start_new_session=True,
            )
        print("proxy-started")


def patch_auth() -> None:
    if not AUTH.exists():
        print("no-auth")
        return
    bak = AUTH.with_suffix(".json.bak-before-leave-nous-20260914")
    if not bak.exists():
        shutil.copy2(AUTH, bak)
    data = json.loads(AUTH.read_text(encoding="utf-8"))
    before = data.get("active_provider")
    data["active_provider"] = "custom"
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    AUTH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("auth-active", before, "->", data["active_provider"])


def patch_openclaw() -> None:
    if not OC.exists():
        print("no-openclaw")
        return
    bak = OC.with_name("openclaw.json.bak-ds-0813-20260914")
    if not bak.exists():
        shutil.copy2(OC, bak)
    data = json.loads(OC.read_text(encoding="utf-8"))
    models = data.setdefault("models", {})
    providers = models.setdefault("providers", {})
    ds = providers.setdefault("deepseek", {})
    ds["baseUrl"] = f"http://{PROXY_HOST}:{PROXY_PORT}"
    ds["api"] = "openai-completions"
    existing = ds.get("models")
    wanted = [
        {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro"},
        {"id": "deepseek-v4-pro-0813", "name": "DeepSeek V4 Pro 0813"},
        {"id": "deepseek-flash", "name": "DeepSeek Flash"},
    ]
    if not isinstance(existing, list) or not existing:
        ds["models"] = wanted
    else:
        ids = {item.get("id") for item in existing if isinstance(item, dict)}
        for item in wanted:
            if item["id"] not in ids:
                existing.append(item)
        ds["models"] = existing
    OC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("openclaw-baseUrl", ds.get("baseUrl"))
    print("openclaw-model-ids", [m.get("id") for m in ds.get("models") if isinstance(m, dict)])


def main() -> None:
    src = KEY_FILE if KEY_FILE.exists() else KEY_FILE_WIN
    if not src.exists():
        raise SystemExit("missing key file")
    key = src.read_text(encoding="utf-8").strip()
    if len(key) < 12 or not key.startswith("sk-"):
        raise SystemExit("bad key shape")
    print("key-len", len(key), "last4", key[-4:])
    upsert_env(
        ENV,
        {
            "DEEPSEEK_API": key,
            "DEEPSEEK_API_KEY": key,
            "DEEPSEEK_BASE_URL": PROXY_URL,
        },
    )
    print("hermes-env-names", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL")
    if CFG.exists():
        bak = CFG.with_suffix(".yaml.bak-ds-0813-20260914")
        if not bak.exists():
            shutil.copy2(CFG, bak)
        CFG.write_text(patch_yaml_text(CFG.read_text(encoding="utf-8")), encoding="utf-8")
        print("hermes-config-patched", "0813" in CFG.read_text(encoding="utf-8"))
    else:
        print("no-hermes-config")
    patch_auth()
    patch_openclaw()
    ensure_proxy()
    for p in (KEY_FILE, KEY_FILE_WIN):
        try:
            p.unlink()
        except OSError:
            pass
    print("done")


if __name__ == "__main__":
    main()
