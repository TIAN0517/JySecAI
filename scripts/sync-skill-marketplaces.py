#!/usr/bin/env python3
"""Sync skills from public offensive-security / audit skill marketplaces into skills_dir.

Supported marketplaces:
  - specterops   -> https://github.com/SpecterOps/skills
  - trailofbits  -> https://github.com/trailofbits/skills

Skill shape: a directory containing a SKILL.md with YAML frontmatter
(name / description / metadata). This matches JySecAI's `skills_dir` loader
(internal/multiagent/eino_skills.go -> Eino skill filesystem backend).

Workflow:
  1. clone (or re-clone with --update) the marketplace repo into a cache dir;
  2. copy the requested skill directories into skills_dir;
  3. normalize frontmatter: ensure dir name == `name`, tag provenance
     (metadata.marketplace, metadata.source);
  4. record every import in <skills_dir>/.marketplace-manifest.json.

Usage:
  python scripts/sync-skill-marketplaces.py --source specterops --preset starter
  python scripts/sync-skill-marketplaces.py --source specterops --import \
      plugins/c2-cobaltstrike/skills skills/cwe-code-review
  python scripts/sync-skill-marketplaces.py --source trailofbits --import plugins/yara-authoring/skills
  python scripts/sync-skill-marketplaces.py --dry-run --source specterops --preset recon --skills-dir skills

Notes:
  - Skills that depend on an external MCP server (BloodHound, Ghostwriter,
    Binary Ninja, Ghidra, ...) are imported as-is; you must deploy the matching
    MCP server yourself and add it to `external_mcp.servers` in config.
  - Review every SKILL.md and bundled script before enabling it (supply-chain:
    same trust bar as evaluating any third-party tool).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPOS = {
    "specterops": "https://github.com/SpecterOps/skills.git",
    "trailofbits": "https://github.com/trailofbits/skills.git",
}

PRESETS = {
    "c2": ("specterops", ["plugins/c2-cobaltstrike/skills"]),
    "recon": ("specterops", ["plugins/ops-reconnaissance/skills"]),
    "bloodhound": ("specterops", ["plugins/bloodhound/skills"]),
    "timeline": (
        "specterops",
        [
            "plugins/report-timeline/skills/timeline-consolidator",
            "plugins/report-timeline/skills/timeline-workflow",
        ],
    ),
    "code-review": ("specterops", ["skills"]),
    "audit": (
        "trailofbits",
        ["plugins/burpsuite-project-parser/skills", "plugins/yara-authoring/skills"],
    ),
    "starter": (
        "specterops",
        [
            "skills",
            "plugins/c2-cobaltstrike/skills",
            "plugins/ops-reconnaissance/skills",
            "plugins/bloodhound/skills",
            "plugins/report-timeline/skills/timeline-consolidator",
            "plugins/report-timeline/skills/timeline-workflow",
        ],
    ),
}

SKILL_MD = "SKILL.md"
MANIFEST = ".marketplace-manifest.json"


@dataclass
class ImportRecord:
    name: str
    source: str          # marketplace alias
    repo: str            # git url
    commit: str          # cloned commit
    relpath: str         # path of the skill inside the marketplace repo
    imported_at: str     # ISO date
    deps_mcp: list = field(default_factory=list)  # referenced MCP servers (best-effort)


def log(msg: str) -> None:
    print(msg, flush=True)


def run_git(args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def clone_or_update(url: str, cache: Path, update: bool) -> str:
    # Windows path-length limits break checkout of repos with very long
    # filenames (e.g. SpecterOps bloodhound query snapshots). Always enable
    # core.longpaths before materialising the working tree.
    if cache.exists() and not update:
        r = run_git(["-C", str(cache), "rev-parse", "HEAD"])
        if r.returncode == 0:
            return r.stdout.strip()
        shutil.rmtree(cache, ignore_errors=True)
    if cache.exists():
        r = run_git(["-C", str(cache), "pull", "--depth", "1", "origin", "HEAD"])
        if r.returncode != 0:
            shutil.rmtree(cache, ignore_errors=True)
    if not cache.exists():
        r = run_git(["clone", "--depth", "1", "--no-checkout", url, str(cache)])
        if r.returncode != 0:
            shutil.rmtree(cache, ignore_errors=True)
            sys.exit(f"git clone failed for {url}:\n{r.stderr}")
    run_git(["-C", str(cache), "config", "core.longpaths", "true"])
    r = run_git(["-C", str(cache), "checkout", "--force", "HEAD"])
    if r.returncode != 0:
        shutil.rmtree(cache, ignore_errors=True)
        sys.exit(f"git checkout failed for {url}:\n{r.stderr}")
    r = run_git(["-C", str(cache), "rev-parse", "HEAD"])
    return r.stdout.strip() if r.returncode == 0 else "unknown"


_FRONT_DELIM = re.compile(r"^---[ \t]*$")


def split_frontmatter(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    if not lines:
        return None, lines
    start_idx = 0
    while start_idx < len(lines) and not lines[start_idx].strip():
        start_idx += 1
    if start_idx >= len(lines) or not _FRONT_DELIM.match(lines[start_idx]):
        return None, lines
    while start_idx < len(lines) and _FRONT_DELIM.match(lines[start_idx]):
        start_idx += 1
    body_start = None
    for i in range(start_idx, len(lines)):
        if _FRONT_DELIM.match(lines[i]):
            body_start = i
            break
    if body_start is None:
        return None, lines
    return lines[start_idx:body_start], lines[body_start + 1:]


def frontmatter_get(fm: list, key: str):
    for ln in fm:
        m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", ln)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


def frontmatter_has_metadata(fm: list) -> bool:
    return any(re.match(r"^metadata\s*:[ \t]*(\S.*)?$", ln) for ln in fm)


def inject_provenance(skill_md: Path, marketplace: str, relpath: str) -> None:
    raw = skill_md.read_text(encoding="utf-8")
    if not raw.endswith("\n"):
        raw += "\n"
    fm, body = split_frontmatter(raw)
    if fm is None:
        return  # not a SKILL.md — leave untouched
    if any("marketplace:" in ln for ln in fm):
        return  # already injected
    marker = f"  marketplace: {marketplace}\n  source: {relpath}\n"
    new_lines = list(fm)
    md_idx = next(
        (i for i, ln in enumerate(new_lines) if re.match(r"^metadata\s*:[ \t]*(\S.*)?$", ln)),
        None,
    )
    if md_idx is not None:
        entry = new_lines[md_idx]
        # map `metadata: { ... }` flow form -> block form
        if ":" in entry and entry.split(":", 1)[1].strip():
            head = entry.split(":", 1)[0]
            new_lines[md_idx] = f"{head}:\n{marker}" + "  " + entry.split(":", 1)[1].strip() + "\n"
        else:
            new_lines.insert(md_idx + 1, marker.rstrip("\n"))
    else:
        new_lines.append("metadata:")
        new_lines.append(marker.rstrip("\n"))
    out = ["---", *new_lines, "---", *body]
    skill_md.write_text("\n".join(out) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")


def normalize_name(skill_dir: Path, marketplace: str, relpath: str, dry_run: bool):
    md = skill_dir / SKILL_MD
    raw = md.read_text(encoding="utf-8")
    fm, _ = split_frontmatter(raw)
    declared = frontmatter_get(fm, "name") if fm else None
    current = skill_dir.name
    if declared and declared != current:
        target = skill_dir.with_name(sanitize_name(declared))
        if not dry_run:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
                skill_dir.rename(target)
            else:
                skill_dir.rename(target)
        log(f"  renamed  {current} -> {declared}")
        return target.name
    return current


def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-") or "unnamed"


KNOWN_MCP_SERVERS = {
    "bloodhound",
    "reverse-shell",
    "vuln-intel",
    "redteam-knowledge",
    "dragon-v",
    "pent-claude-agent",
    "ghostwriter",
    "binary-ninja",
    "ghidra",
    "shodan",
    "nmap",
}


def skill_mcp_deps(skill_dir: Path) -> list:
    """Best-effort scan for the MCP servers a skill mentions."""
    names = set()
    for f in skill_dir.glob("**/*"):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for server in KNOWN_MCP_SERVERS:
            if server in text:
                names.add(server)
    return sorted(names)[:8]


def import_skill(src_skill: Path, skills_dir: Path, marketplace: str, relpath: str,
                 repo_url: str, commit: str, dry_run: bool, manifest: dict) -> None:
    md_src = src_skill / SKILL_MD
    if not md_src.is_file():
        log(f"  skip {relpath} (no {SKILL_MD})")
        return
    raw = md_src.read_text(encoding="utf-8")
    fm, _ = split_frontmatter(raw)
    declared = frontmatter_get(fm, "name") if fm else sanitize_name(src_skill.name)
    name = declared or sanitize_name(src_skill.name)
    target = skills_dir / name
    if target.exists():
        # overwrite-import keeps upstream up to date; provenance preserved below
        if not dry_run:
            shutil.rmtree(target, ignore_errors=True)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for item in src_skill.iterdir():
            dst = target / item.name
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)
        inject_provenance(target / SKILL_MD, marketplace, relpath)
    deps = skill_mcp_deps(src_skill)
    rec = {
        "name": name,
        "marketplace": marketplace,
        "repo": repo_url,
        "commit": commit,
        "source": relpath,
        "imported_at": _dt.date.today().isoformat(),
        "deps_mcp": deps,
    }
    manifest[name] = rec
    log(f"  import  {name}  <- {marketplace}:{relpath}" + (f"  [mcp: {', '.join(deps)}]" if deps else ""))


def resolve_skill_dirs(base: Path, rel: str) -> list:
    """rel is either a single skill dir or a container (each child w/ SKILL.md)."""
    path = base / rel
    if not path.exists():
        log(f"  !! missing path in marketplace: {rel}")
        return []
    if (path / SKILL_MD).is_file():
        return [(path, rel)]
    out = []
    for child in sorted(path.iterdir()):
        if child.is_dir() and (child / SKILL_MD).is_file():
            out.append((child, f"{rel}/{child.name}"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync skills from public marketplaces into skills_dir.")
    ap.add_argument("--source", choices=list(REPOS), help="marketplace alias (overridden by --preset)")
    ap.add_argument("--preset", choices=list(PRESETS), help="named import set")
    ap.add_argument("--import", dest="imports", nargs="+", metavar="PATH",
                    help="paths inside the marketplace to import (skill dir or container)")
    ap.add_argument("--skills-dir", default="skills", help="target skills directory")
    ap.add_argument("--cache-dir", default=None, help="clone cache dir (default: scripts/.marketplace-cache)")
    ap.add_argument("--update", action="store_true", help="force re-clone/pull the marketplace")
    ap.add_argument("--dry-run", action="store_true", help="print what would be imported without writing")
    args = ap.parse_args()

    if args.preset:
        source, imports = PRESETS[args.preset]
    elif args.source and args.imports:
        source, imports = args.source, args.imports
    else:
        sys.exit("provide --preset NAME or --source NAME --import PATH [...]")

    base_dir = Path(__file__).resolve().parent.parent
    skills_dir = Path(args.skills_dir)
    if not skills_dir.is_absolute():
        skills_dir = base_dir / skills_dir
    skills_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else base_dir / "scripts" / ".marketplace-cache"
    cache = cache_dir / source

    log(f"[{source}] cloning/updating {REPOS[source]} -> {cache}")
    commit = clone_or_update(REPOS[source], cache, args.update)
    log(f"[{source}] commit {commit}")

    manifest_path = skills_dir / MANIFEST
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    repo_root = cache
    for rel in imports:
        for skill_dir, relpath in resolve_skill_dirs(repo_root, rel):
            if args.dry_run:
                log(f"  would import {skill_dir.relative_to(repo_root)}")
                continue
            import_skill(skill_dir, skills_dir, source, relpath, REPOS[source], commit, False, manifest)

    if not args.dry_run:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        log(f"manifest -> {manifest_path} ({len(manifest)} skills)")

    diffs = {
        name: rec
        for name, rec in manifest.items()
        if rec.get("marketplace") != source
    }
    if diffs:
        log(f"note: manifest also tracks {len(diffs)} skill(s) from other marketplaces")


if __name__ == "__main__":
    main()