#!/usr/bin/env python3
"""PUT each arsenal MCP into a running JySecAI via /api/external-mcp/:name."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:9898")
    p.add_argument("--token", required=True)
    p.add_argument("--json", default=str(Path(__file__).with_name("external-mcp.json")))
    p.add_argument("--start", action="store_true", help="POST /start after upsert")
    args = p.parse_args()

    servers = (json.loads(Path(args.json).read_text(encoding="utf-8")).get("servers") or {})
    ok, fail = [], []
    for name, spec in servers.items():
        body = json.dumps({"config": spec}).encode("utf-8")
        req = urllib.request.Request(
            f"{args.base.rstrip('/')}/api/external-mcp/{name}",
            data=body,
            method="PUT",
            headers={
                "Authorization": f"Bearer {args.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"PUT {name} -> {resp.status}")
            ok.append(name)
            if args.start:
                sreq = urllib.request.Request(
                    f"{args.base.rstrip('/')}/api/external-mcp/{name}/start",
                    data=b"{}",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {args.token}",
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(sreq, timeout=60) as resp:
                    print(f"START {name} -> {resp.status}")
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")[:300]
            print(f"FAIL {name} -> {e.code} {err}", file=sys.stderr)
            fail.append(name)
    print(f"ok={len(ok)} fail={len(fail)}")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
