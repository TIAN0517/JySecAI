"""Mirror 0813 alias + DeepSeek key onto vps3 Windows Hermes. No secret prints."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"C:\Users\Administrator\AppData\Local\hermes")
CFG = HOME / "config.yaml"
AUTH = HOME / "auth.json"
ENV = HOME / ".env"
WSL_ENV = Path(r"\\wsl$\Ubuntu\home\bossjy\.hermes\.env")
# fallback: read from leftover desktop key if present
KEY_CANDIDATES = [
    Path(r"C:\Users\Administrator\Desktop\JySecAI\_ds.key"),
    Path(r"C:\Users\Administrator\Desktop\JySecAI\.tmp-ds.key"),
]
OFFICIAL = "https://api.deepseek.com/v1"


def read_key() -> str:
    for p in KEY_CANDIDATES:
        if p.exists():
            k = p.read_text(encoding="utf-8").strip()
            if k.startswith("sk-"):
                return k
    # WSL env via UNC may fail; try wsl path through a copied file we already wrote
    wsl_copy = Path(r"C:\Users\Administrator\Desktop\JySecAI\_ds_from_wsl.env")
    if wsl_copy.exists():
        for ln in wsl_copy.read_text(encoding="utf-8").splitlines():
            if ln.startswith("DEEPSEEK_API_KEY="):
                return ln.split("=", 1)[1].strip()
    raise SystemExit("no key")


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
    path.write_text(body, encoding="utf-8")


def patch_yaml(text: str) -> str:
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
        if "custom_providers:" in text:
            text = text.replace("custom_providers:", aliases + "custom_providers:", 1)
        else:
            text = aliases + text
    block = (
        "  deepseek:\n"
        "    name: DeepSeek\n"
        f"    base_url: {OFFICIAL}\n"
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
    if "\n  deepseek:\n" not in text and "providers:\n" in text:
        text = text.replace("providers:\n", "providers:\n" + block, 1)
    return text


def main() -> None:
    if not HOME.exists():
        print("no-win-hermes")
        return
    key = read_key()
    print("key-len", len(key), "last4", key[-4:])
    upsert_env(ENV, {"DEEPSEEK_API": key, "DEEPSEEK_API_KEY": key, "DEEPSEEK_BASE_URL": OFFICIAL})
    if CFG.exists():
        bak = CFG.with_suffix(".yaml.bak-ds-0813-20260914")
        if not bak.exists():
            shutil.copy2(CFG, bak)
        CFG.write_text(patch_yaml(CFG.read_text(encoding="utf-8")), encoding="utf-8")
        print("cfg-patched", "deepseek/deepseek-v4-pro-0813:" in CFG.read_text(encoding="utf-8"))
    if AUTH.exists():
        bak = AUTH.with_name("auth.json.bak-before-leave-nous-20260914")
        if not bak.exists():
            shutil.copy2(AUTH, bak)
        data = json.loads(AUTH.read_text(encoding="utf-8"))
        before = data.get("active_provider")
        data["active_provider"] = "custom"
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        AUTH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("auth", before, "->", data["active_provider"])
    print("done-win")


if __name__ == "__main__":
    main()
