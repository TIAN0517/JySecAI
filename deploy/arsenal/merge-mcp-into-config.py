#!/usr/bin/env python3
"""Merge deploy/arsenal/external-mcp.json into a JySecAI config.yaml.

Round-trips with ruamel.yaml so comments, quoting, and enc:cfg values survive.
Existing server names are left untouched unless --force is passed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--json", required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    try:
        from ruamel.yaml import YAML
    except ImportError:
        print("need ruamel.yaml (do not use PyYAML dump on production config)", file=sys.stderr)
        return 2

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    cfg_path = Path(args.config)
    with cfg_path.open(encoding="utf-8") as f:
        data = yaml.load(f) or {}
    incoming = json.loads(Path(args.json).read_text(encoding="utf-8")).get("servers") or {}

    if "external_mcp" not in data or data["external_mcp"] is None:
        data["external_mcp"] = {}
    ext = data["external_mcp"]
    if "servers" not in ext or ext["servers"] is None:
        ext["servers"] = {}
    servers = ext["servers"]

    added, skipped, replaced = [], [], []
    for name, spec in incoming.items():
        if name in servers and not args.force:
            skipped.append(name)
            continue
        if name in servers:
            replaced.append(name)
        else:
            added.append(name)
        servers[name] = spec

    print(f"added={added}")
    print(f"replaced={replaced}")
    print(f"skipped_existing={skipped}")
    if args.dry_run or (not added and not replaced):
        return 0

    backup = cfg_path.with_name(cfg_path.name + ".bak-arsenal")
    backup.write_bytes(cfg_path.read_bytes())
    with cfg_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    print(f"wrote {cfg_path} (backup {backup})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
