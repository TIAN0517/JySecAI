#!/usr/bin/env python3
"""Authoritative, read-only red-team knowledge MCP for JySecAI.

The server retrieves technique and test metadata but never launches commands,
downloads payloads, or changes a target. Command examples are opt-in output.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP as _MCPServer


ATTACK_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/{domain}-attack/{domain}-attack.json"
LOLBAS_URL = "https://lolbas-project.github.io/api/lolbas.json"
GTFOBINS_URL = "https://gtfobins.org/api.json"
ATOMIC_URL = "https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/{technique}/{technique}.yaml"
USER_AGENT = "JySecAI-RedTeamKnowledge/1.0"
HTTP_TIMEOUT = max(5, min(int(os.getenv("REDTEAM_KNOWLEDGE_HTTP_TIMEOUT", "30")), 90))
MAX_RESPONSE_BYTES = 64 * 1024 * 1024

_ALLOWED_HOSTS = {"raw.githubusercontent.com", "lolbas-project.github.io", "gtfobins.org"}
_DOMAINS = {"enterprise", "mobile", "ics"}
_TECHNIQUE_RE = re.compile(r"^T\d{4}(?:\.\d{3})?$", re.IGNORECASE)
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK = threading.Lock()


class SourceError(RuntimeError):
    pass


def _cache_get(key: str) -> Any | None:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        expires, value = item
        if expires <= time.time():
            _CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: Any, ttl: int) -> Any:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time() + ttl, value)
    return value


def _request_bytes(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise SourceError("outbound host is not allowlisted")
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            request = Request(url, headers={"Accept": "application/json, text/yaml", "User-Agent": USER_AGENT})
            with urlopen(request, timeout=HTTP_TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise SourceError("response exceeded size limit")
            return raw
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt:
                break
            time.sleep(1.0)
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt:
                break
            time.sleep(0.5)
    raise SourceError(str(last_error or "request failed"))


def _request_json(url: str, *, cache_ttl: int = 3600) -> Any:
    key = f"json:{url}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        data = json.loads(_request_bytes(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"invalid JSON: {exc}") from exc
    return _cache_set(key, data, cache_ttl)


def _safe_query(query: str) -> str:
    value = " ".join(query.strip().split())
    if not value or len(value) > 160:
        raise ValueError("query must contain 1-160 characters")
    if any(ord(char) < 32 for char in value):
        raise ValueError("query contains control characters")
    return value


def _technique_id(value: str) -> str:
    technique = value.strip().upper()
    if not _TECHNIQUE_RE.fullmatch(technique):
        raise ValueError("technique_id must look like T1059 or T1059.001")
    return technique


def _domain(value: str) -> str:
    domain = value.strip().lower()
    if domain not in _DOMAINS:
        raise ValueError("domain must be enterprise, mobile, or ics")
    return domain


def _clip(value: Any, size: int = 4000) -> str:
    text = str(value or "").strip()
    return text if len(text) <= size else f"{text[:size]}..."


def _external_id(item: dict[str, Any]) -> str | None:
    for reference in item.get("external_references") or []:
        value = str(reference.get("external_id") or "")
        if _TECHNIQUE_RE.fullmatch(value):
            return value.upper()
    return None


def _external_url(item: dict[str, Any]) -> str | None:
    for reference in item.get("external_references") or []:
        if reference.get("source_name") in {"mitre-attack", "mitre-mobile-attack", "mitre-ics-attack"} and reference.get("url"):
            return str(reference["url"])
    return None


def _attack_dataset(domain: str) -> dict[str, Any]:
    cache_key = f"attack-index:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    url = ATTACK_URL.format(domain=domain)
    try:
        bundle = json.loads(_request_bytes(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"invalid ATT&CK STIX JSON: {exc}") from exc
    kept_types = {
        "attack-pattern", "course-of-action", "intrusion-set", "malware", "tool",
        "x-mitre-detection-strategy", "x-mitre-data-component",
    }
    nodes: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, Any]] = []
    techniques: list[dict[str, Any]] = []
    by_external: dict[str, dict[str, Any]] = {}
    for item in bundle.get("objects") or []:
        item_type = item.get("type")
        if item_type in kept_types and item.get("id"):
            nodes[str(item["id"])] = item
        if item_type == "relationship":
            relationships.append(item)
        elif item_type == "attack-pattern" and not item.get("revoked") and not item.get("x_mitre_deprecated"):
            external = _external_id(item)
            if external:
                techniques.append(item)
                by_external[external] = item
    return _cache_set(cache_key, {
        "nodes": nodes, "relationships": relationships, "techniques": techniques,
        "by_external": by_external, "source": url,
    }, 6 * 3600)


def _compact_technique(item: dict[str, Any]) -> dict[str, Any]:
    tactics = sorted({str(phase.get("phase_name")) for phase in item.get("kill_chain_phases") or [] if phase.get("phase_name")})
    return {
        "technique_id": _external_id(item),
        "name": item.get("name"),
        "description": _clip(item.get("description")),
        "tactics": tactics,
        "platforms": item.get("x_mitre_platforms") or [],
        "data_sources": item.get("x_mitre_data_sources") or [],
        "detection": _clip(item.get("x_mitre_detection")),
        "permissions_required": item.get("x_mitre_permissions_required") or [],
        "version": item.get("x_mitre_version"),
        "modified": item.get("modified"),
        "url": _external_url(item),
    }


def _compact_node(item: dict[str, Any]) -> dict[str, Any]:
    external = None
    url = None
    for reference in item.get("external_references") or []:
        external = external or reference.get("external_id")
        url = url or reference.get("url")
    return {
        "type": item.get("type"), "id": external, "name": item.get("name"),
        "description": _clip(item.get("description"), 1200), "url": url,
    }


def _attack_detail(technique_id: str, domain: str) -> dict[str, Any]:
    dataset = _attack_dataset(domain)
    technique = dataset["by_external"].get(technique_id)
    if not technique:
        raise SourceError(f"{technique_id} was not found in {domain} ATT&CK")
    stix_id = technique["id"]
    mitigations: list[dict[str, Any]] = []
    used_by: list[dict[str, Any]] = []
    detections: list[dict[str, Any]] = []
    for relationship in dataset["relationships"]:
        source = dataset["nodes"].get(str(relationship.get("source_ref")))
        relation = relationship.get("relationship_type")
        if relation == "mitigates" and relationship.get("target_ref") == stix_id and source:
            mitigations.append(_compact_node(source))
        elif relation == "uses" and relationship.get("target_ref") == stix_id and source:
            used_by.append(_compact_node(source))
        elif relation == "detects" and relationship.get("target_ref") == stix_id and source:
            detections.append(_compact_node(source))
    return {
        **_compact_technique(technique),
        "mitigations": mitigations[:30],
        "observed_groups_or_software": used_by[:20],
        "detection_strategies": detections[:20],
        "source": dataset["source"],
    }


def _lolbas_rows() -> list[dict[str, Any]]:
    data = _request_json(LOLBAS_URL, cache_ttl=3 * 3600)
    if not isinstance(data, list):
        raise SourceError("unexpected LOLBAS schema")
    return data


def _compact_lolbas(item: dict[str, Any], include_examples: bool) -> dict[str, Any]:
    commands = item.get("Commands") or []
    result = {
        "name": item.get("Name"), "description": item.get("Description"),
        "full_paths": item.get("Full_Path") or [],
        "categories": sorted({str(command.get("Category")) for command in commands if command.get("Category")}),
        "mitre_ids": sorted({str(command.get("MitreID")) for command in commands if command.get("MitreID")}),
        "detection": _clip(item.get("Detection"), 1600),
        "resources": item.get("Resources") or [], "url": item.get("url"),
        "example_count": len(commands),
    }
    if include_examples:
        result["examples"] = [{
            "command": _clip(command.get("Command"), 1200), "use_case": command.get("Usecase"),
            "category": command.get("Category"), "privileges": command.get("Privileges"),
            "mitre_id": command.get("MitreID"), "operating_system": command.get("OperatingSystem"),
        } for command in commands[:8]]
    return result


def _gtfobins_data() -> dict[str, Any]:
    data = _request_json(GTFOBINS_URL, cache_ttl=3 * 3600)
    if not isinstance(data, dict) or not isinstance(data.get("executables"), dict):
        raise SourceError("unexpected GTFOBins schema")
    return data


def _compact_gtfobin(name: str, item: dict[str, Any], definitions: dict[str, Any], include_examples: bool) -> dict[str, Any]:
    functions = item.get("functions") or {}
    capabilities = sorted(functions)
    result: dict[str, Any] = {
        "name": name, "comment": item.get("comment"), "capabilities": capabilities,
        "mitre_ids": sorted({str(value) for capability in capabilities for value in (definitions.get(capability, {}).get("mitre") or [])}),
        "url": f"https://gtfobins.org/gtfobins/{name.lower()}/",
    }
    if include_examples:
        examples = []
        for capability in capabilities:
            for example in (functions.get(capability) or [])[:2]:
                examples.append({
                    "capability": capability, "code": _clip(example.get("code"), 1200),
                    "contexts": sorted((example.get("contexts") or {}).keys()),
                    "comment": _clip(example.get("comment"), 600),
                })
        result["examples"] = examples[:12]
    return result


def _atomic_tests(technique_id: str, include_commands: bool, limit: int) -> dict[str, Any]:
    url = ATOMIC_URL.format(technique=technique_id)
    key = f"yaml:{url}"
    data = _cache_get(key)
    if data is None:
        try:
            data = yaml.safe_load(_request_bytes(url).decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            raise SourceError(f"invalid Atomic Red Team YAML: {exc}") from exc
        _cache_set(key, data, 3 * 3600)
    if not isinstance(data, dict):
        raise SourceError("unexpected Atomic Red Team schema")
    rows = []
    for test in (data.get("atomic_tests") or [])[:limit]:
        executor = test.get("executor") or {}
        row: dict[str, Any] = {
            "name": test.get("name"), "auto_generated_guid": test.get("auto_generated_guid"),
            "description": _clip(test.get("description"), 1600),
            "supported_platforms": test.get("supported_platforms") or [],
            "executor": executor.get("name"), "elevation_required": bool(executor.get("elevation_required")),
            "input_arguments": sorted((test.get("input_arguments") or {}).keys()),
            "dependency_count": len(test.get("dependencies") or []),
        }
        if include_commands:
            row["command"] = _clip(executor.get("command"), 3000)
            row["cleanup_command"] = _clip(executor.get("cleanup_command"), 1600)
            row["dependencies"] = [{
                "description": _clip(dependency.get("description"), 600),
                "prereq_command": _clip(dependency.get("prereq_command"), 1200),
                "get_prereq_command": _clip(dependency.get("get_prereq_command"), 1200),
            } for dependency in (test.get("dependencies") or [])[:8]]
        rows.append(row)
    return {
        "technique_id": technique_id, "display_name": data.get("display_name"), "tests": rows,
        "total_tests": len(data.get("atomic_tests") or []), "source": url,
        "execution_policy": "Reference only. Explicit authorization, isolation, prerequisites, and cleanup review are required before running a test.",
    }


def _source_call(name: str, function: Callable[[], Any]) -> tuple[str, dict[str, Any]]:
    try:
        return name, {"ok": True, "data": function()}
    except (SourceError, ValueError, OSError) as exc:
        return name, {"ok": False, "error": str(exc)}


app = _MCPServer(
    name="redteam-knowledge",
    instructions=("Read-only MITRE ATT&CK, LOLBAS, GTFOBins, and Atomic Red Team knowledge. "
                  "It never executes techniques or downloads payloads. Command examples require an explicit opt-in argument."),
)


@app.tool(description="Search official MITRE ATT&CK techniques by ID, name, description, tactic, or platform.")
def redteam_search_attack(query: str, domain: str = "enterprise", platform: str = "", tactic: str = "", limit: int = 10) -> dict[str, Any]:
    value = _safe_query(query).lower()
    selected_domain = _domain(domain)
    platform_filter = platform.strip().lower()
    tactic_filter = tactic.strip().lower().replace(" ", "-")
    count = max(1, min(limit, 30))
    dataset = _attack_dataset(selected_domain)
    matches = []
    for item in dataset["techniques"]:
        compact = _compact_technique(item)
        searchable = " ".join([str(compact.get("technique_id") or ""), str(compact.get("name") or ""), str(compact.get("description") or "")]).lower()
        if value not in searchable:
            continue
        if platform_filter and not any(platform_filter in str(entry).lower() for entry in compact["platforms"]):
            continue
        if tactic_filter and tactic_filter not in compact["tactics"]:
            continue
        matches.append(compact)
    matches.sort(key=lambda row: (0 if str(row.get("technique_id", "")).lower() == value else 1, str(row.get("technique_id"))))
    return {"query": query, "domain": selected_domain, "results": matches[:count], "source": dataset["source"]}


@app.tool(description="Get one official MITRE ATT&CK technique with mitigations, detection strategies, and observed groups/software.")
def redteam_get_attack(technique_id: str, domain: str = "enterprise") -> dict[str, Any]:
    return _attack_detail(_technique_id(technique_id), _domain(domain))


@app.tool(description="Search official LOLBAS Windows living-off-the-land entries. Command examples are omitted unless include_examples is true; nothing is executed.")
def redteam_search_lolbas(query: str, category: str = "", mitre_id: str = "", include_examples: bool = False, limit: int = 10) -> dict[str, Any]:
    value = _safe_query(query).lower()
    category_filter = category.strip().lower()
    mitre_filter = mitre_id.strip().upper()
    count = max(1, min(limit, 30))
    matches = []
    for item in _lolbas_rows():
        commands = item.get("Commands") or []
        searchable = " ".join([str(item.get("Name") or ""), str(item.get("Description") or "")] + [
            " ".join(str(command.get(key) or "") for key in ("Usecase", "Category", "MitreID", "Description")) for command in commands
        ]).lower()
        if value not in searchable:
            continue
        if category_filter and not any(category_filter in str(command.get("Category") or "").lower() for command in commands):
            continue
        if mitre_filter and not any(mitre_filter == str(command.get("MitreID") or "").upper() for command in commands):
            continue
        matches.append(_compact_lolbas(item, include_examples))
    return {"query": query, "results": matches[:count], "source": LOLBAS_URL, "read_only": True}


@app.tool(description="Search official GTFOBins Unix living-off-the-land entries by executable or capability. Examples are opt-in and never executed.")
def redteam_search_gtfobins(query: str, capability: str = "", include_examples: bool = False, limit: int = 10) -> dict[str, Any]:
    value = _safe_query(query).lower()
    capability_filter = capability.strip().lower().replace(" ", "-")
    count = max(1, min(limit, 30))
    data = _gtfobins_data()
    definitions = data.get("functions") or {}
    matches = []
    for name, item in data["executables"].items():
        functions = item.get("functions") or {}
        searchable = " ".join([str(name), str(item.get("comment") or ""), *functions.keys()]).lower()
        if value not in searchable:
            continue
        if capability_filter and capability_filter not in functions:
            continue
        matches.append(_compact_gtfobin(str(name), item, definitions, include_examples))
    matches.sort(key=lambda row: (0 if str(row["name"]).lower() == value else 1, str(row["name"]).lower()))
    return {"query": query, "results": matches[:count], "source": GTFOBINS_URL, "read_only": True}


@app.tool(description="Get official Atomic Red Team test metadata for one ATT&CK technique. Commands are omitted by default and are never executed.")
def redteam_get_atomic_tests(technique_id: str, include_commands: bool = False, limit: int = 20) -> dict[str, Any]:
    return _atomic_tests(_technique_id(technique_id), include_commands, max(1, min(limit, 50)))


@app.tool(description="Check authoritative red-team knowledge sources without executing any technique or test.")
def redteam_knowledge_health() -> dict[str, Any]:
    checks: dict[str, Callable[[], Any]] = {
        "mitre_attack": lambda: _attack_detail("T1059", "enterprise").get("name"),
        "lolbas": lambda: len(_lolbas_rows()),
        "gtfobins": lambda: len(_gtfobins_data().get("executables") or {}),
        "atomic_red_team": lambda: _atomic_tests("T1059", False, 1).get("total_tests"),
    }
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(checks)) as pool:
        futures = [pool.submit(_source_call, name, function) for name, function in checks.items()]
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result
    return {"sources": results, "cache_entries": len(_CACHE), "read_only": True, "executes_commands": False}


if __name__ == "__main__":
    app.run(transport="stdio")
