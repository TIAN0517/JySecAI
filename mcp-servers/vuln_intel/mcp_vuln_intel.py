#!/usr/bin/env python3
"""Curated, read-only vulnerability intelligence MCP for JySecAI.

Sources are deliberately limited to authoritative feeds plus clearly-labelled
public PoC discovery. This server never downloads or executes PoC code.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP as _MCPServer


NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_API = "https://api.first.org/data/v1/epss"
CISA_KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OSV_API = "https://api.osv.dev/v1"
GITHUB_API = "https://api.github.com"
USER_AGENT = "JySecAI-VulnIntel/1.0"
HTTP_TIMEOUT = max(5, min(int(os.getenv("VULN_INTEL_HTTP_TIMEOUT", "20")), 60))
MAX_RESPONSE_BYTES = 12 * 1024 * 1024

_ALLOWED_HOSTS = {
    "services.nvd.nist.gov",
    "api.first.org",
    "www.cisa.gov",
    "api.osv.dev",
    "api.github.com",
}
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
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


def _request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    cache_ttl: int = 300,
) -> Any:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise SourceError("outbound host is not allowlisted")

    body = None
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    cache_key = f"{url}|{body!r}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    request_headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            request = Request(url, data=body, headers=request_headers, method="POST" if body else "GET")
            with urlopen(request, timeout=HTTP_TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise SourceError("response exceeded size limit")
            return _cache_set(cache_key, json.loads(raw.decode("utf-8")), cache_ttl)
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt:
                break
            time.sleep(1.0)
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = exc
            if attempt:
                break
            time.sleep(0.5)
    raise SourceError(str(last_error or "request failed"))


def _validate_cve_id(cve_id: str) -> str:
    value = cve_id.strip().upper()
    if not _CVE_RE.fullmatch(value):
        raise ValueError("cve_id must look like CVE-2024-12345")
    return value


def _safe_query(query: str) -> str:
    value = " ".join(query.strip().split())
    if not value or len(value) > 180 or value.startswith("-"):
        raise ValueError("query must contain 1-180 characters and cannot start with '-'")
    if any(ord(char) < 32 for char in value):
        raise ValueError("query contains control characters")
    return value


def _english(items: list[dict[str, Any]] | None) -> str:
    for item in items or []:
        if item.get("lang") == "en":
            return str(item.get("value", ""))
    return str((items or [{}])[0].get("value", "")) if items else ""


def _cvss(cve: dict[str, Any]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for entries in (cve.get("metrics") or {}).values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            data = entry.get("cvssData") or {}
            if data.get("baseScore") is not None:
                candidates.append(
                    {
                        "version": data.get("version"),
                        "score": data.get("baseScore"),
                        "severity": data.get("baseSeverity") or entry.get("baseSeverity"),
                        "vector": data.get("vectorString"),
                        "source": entry.get("source"),
                    }
                )
    return max(candidates, key=lambda item: float(item.get("score") or 0), default=None)


def _compact_nvd_cve(record: dict[str, Any]) -> dict[str, Any]:
    cve = record.get("cve", record)
    weaknesses = sorted(
        {
            str(desc.get("value"))
            for weakness in cve.get("weaknesses") or []
            for desc in weakness.get("description") or []
            if desc.get("value")
        }
    )
    cpes: list[str] = []
    for configuration in cve.get("configurations") or []:
        for node in configuration.get("nodes") or []:
            for match in node.get("cpeMatch") or []:
                if match.get("vulnerable") and match.get("criteria"):
                    cpes.append(str(match["criteria"]))
    references = [
        {
            "url": item.get("url"),
            "tags": item.get("tags") or [],
            "source": item.get("source"),
        }
        for item in (cve.get("references") or [])[:15]
    ]
    return {
        "id": cve.get("id"),
        "status": cve.get("vulnStatus"),
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "description": _english(cve.get("descriptions")),
        "cvss": _cvss(cve),
        "weaknesses": weaknesses,
        "vulnerable_cpes": list(dict.fromkeys(cpes))[:20],
        "references": references,
        "nvd_cisa": {
            "known_exploited_added": cve.get("cisaExploitAdd"),
            "action_due": cve.get("cisaActionDue"),
            "required_action": cve.get("cisaRequiredAction"),
            "name": cve.get("cisaVulnerabilityName"),
        },
    }


def _nvd_lookup(cve_id: str) -> dict[str, Any]:
    headers = {}
    if os.getenv("NVD_API_KEY"):
        headers["apiKey"] = os.environ["NVD_API_KEY"]
    data = _request_json(f"{NVD_API}?{urlencode({'cveId': cve_id})}", headers=headers)
    records = data.get("vulnerabilities") or []
    if not records:
        raise SourceError("CVE not found in NVD")
    return _compact_nvd_cve(records[0])


def _nvd_search(params: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    headers = {}
    if os.getenv("NVD_API_KEY"):
        headers["apiKey"] = os.environ["NVD_API_KEY"]
    query = dict(params)
    query["resultsPerPage"] = max(1, min(limit, 100))
    data = _request_json(f"{NVD_API}?{urlencode(query)}", headers=headers, cache_ttl=180)
    return [_compact_nvd_cve(item) for item in data.get("vulnerabilities") or []]


def _epss_lookup(cve_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not cve_ids:
        return {}
    joined = ",".join(cve_ids[:100])
    data = _request_json(f"{EPSS_API}?{urlencode({'cve': joined})}", cache_ttl=900)
    return {
        str(item.get("cve", "")).upper(): {
            "score": float(item.get("epss", 0)),
            "percentile": float(item.get("percentile", 0)),
            "date": item.get("date"),
        }
        for item in data.get("data") or []
        if item.get("cve")
    }


def _kev_catalog() -> dict[str, Any]:
    return _request_json(CISA_KEV, cache_ttl=1800)


def _kev_lookup(cve_id: str) -> dict[str, Any] | None:
    for item in _kev_catalog().get("vulnerabilities") or []:
        if str(item.get("cveID", "")).upper() == cve_id:
            return item
    return None


def _searchsploit(query: str, limit: int) -> dict[str, Any]:
    executable = shutil.which("searchsploit")
    if not executable:
        return {"available": False, "results": [], "error": "searchsploit is not installed"}
    try:
        result = subprocess.run(
            [executable, "--json", query],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": True, "results": [], "error": str(exc)}
    if result.returncode not in {0, 2}:
        return {"available": True, "results": [], "error": result.stderr.strip()[:500]}
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {"available": True, "results": [], "error": "invalid searchsploit JSON"}
    rows = (parsed.get("RESULTS_EXPLOIT") or []) + (parsed.get("RESULTS_SHELLCODE") or [])
    compact = [
        {
            "edb_id": row.get("EDB-ID"),
            "title": row.get("Title"),
            "date": row.get("Date"),
            "type": row.get("Type"),
            "platform": row.get("Platform"),
            "author": row.get("Author"),
            "path": row.get("Path"),
            "url": f"https://www.exploit-db.com/exploits/{row.get('EDB-ID')}" if row.get("EDB-ID") else None,
            "verification": "catalogued_public_exploit_not_executed",
        }
        for row in rows[:limit]
    ]
    return {"available": True, "results": compact, "error": None}


def _github_pocs(query: str, limit: int) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    search = f'"{query}" (poc OR exploit)'
    try:
        data = _request_json(
            f"{GITHUB_API}/search/repositories?{urlencode({'q': search, 'sort': 'updated', 'order': 'desc', 'per_page': min(limit, 20)})}",
            headers=headers,
            cache_ttl=600,
        )
    except SourceError as exc:
        return {"available": False, "results": [], "error": str(exc)}
    rows = []
    for item in data.get("items") or []:
        rows.append(
            {
                "repository": item.get("full_name"),
                "url": item.get("html_url"),
                "description": item.get("description"),
                "stars": item.get("stargazers_count"),
                "forks": item.get("forks_count"),
                "updated_at": item.get("updated_at"),
                "archived": item.get("archived"),
                "is_fork": item.get("fork"),
                "verification": "unverified_public_repository_do_not_execute_without_review",
            }
        )
    return {"available": True, "results": rows, "error": None}


def _source_call(name: str, function: Callable[[], Any]) -> tuple[str, dict[str, Any]]:
    try:
        return name, {"ok": True, "data": function()}
    except (SourceError, ValueError, OSError) as exc:
        return name, {"ok": False, "error": str(exc)}


def _risk_summary(nvd: dict[str, Any] | None, epss: dict[str, Any] | None, kev: dict[str, Any] | None, poc_count: int) -> dict[str, Any]:
    score = float((((nvd or {}).get("cvss") or {}).get("score") or 0))
    epss_score = float((epss or {}).get("score") or 0)
    if kev:
        priority = "critical"
    elif score >= 9 or epss_score >= 0.5:
        priority = "high"
    elif score >= 7 or epss_score >= 0.1 or poc_count:
        priority = "medium"
    else:
        priority = "normal"
    return {
        "priority": priority,
        "known_exploited_in_the_wild": bool(kev),
        "public_poc_candidates": poc_count,
        "cvss": score or None,
        "epss_probability": epss_score if epss else None,
        "interpretation": "Public PoC links are discovery leads, not proof that the assessed target is vulnerable.",
    }


app = _MCPServer(
    name="vuln-intel",
    instructions=(
        "Read-only CVE, KEV, EPSS, OSV and public PoC intelligence. "
        "Never treats a public repository as verified and never executes PoC code."
    ),
)


@app.tool(description="Cross-check one CVE across NVD, CISA KEV, FIRST EPSS, local ExploitDB/SearchSploit, and GitHub public PoC candidates. Read-only; no PoC is executed.")
def vuln_triage_cve(cve_id: str, include_public_poc: bool = True, poc_limit: int = 8) -> dict[str, Any]:
    cve = _validate_cve_id(cve_id)
    limit = max(1, min(poc_limit, 20))
    jobs: dict[str, Callable[[], Any]] = {
        "nvd": lambda: _nvd_lookup(cve),
        "epss": lambda: _epss_lookup([cve]).get(cve),
        "cisa_kev": lambda: _kev_lookup(cve),
    }
    if include_public_poc:
        jobs["exploitdb"] = lambda: _searchsploit(cve, limit)
        jobs["github_poc"] = lambda: _github_pocs(cve, limit)
    sources: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(_source_call, name, function) for name, function in jobs.items()]
        for future in as_completed(futures):
            name, result = future.result()
            sources[name] = result
    nvd = sources.get("nvd", {}).get("data")
    epss = sources.get("epss", {}).get("data")
    kev = sources.get("cisa_kev", {}).get("data")
    exploitdb = ((sources.get("exploitdb", {}).get("data") or {}).get("results") or [])
    github = ((sources.get("github_poc", {}).get("data") or {}).get("results") or [])
    return {
        "cve_id": cve,
        "risk": _risk_summary(nvd, epss, kev, len(exploitdb) + len(github)),
        "sources": sources,
        "evidence_policy": "Confirm affected version/configuration and reproduce safely before recording a vulnerability as confirmed.",
    }


@app.tool(description="Search NVD CVEs by product, component, vendor, or vulnerability keyword. Optionally restrict results to recent publication days.")
def vuln_search_cves(keyword: str, limit: int = 10, published_within_days: int = 0) -> dict[str, Any]:
    query = _safe_query(keyword)
    params: dict[str, Any] = {"keywordSearch": query}
    if published_within_days:
        days = max(1, min(published_within_days, 120))
        now = datetime.now(timezone.utc)
        params["pubStartDate"] = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000")
        params["pubEndDate"] = now.strftime("%Y-%m-%dT%H:%M:%S.000")
    return {"query": query, "results": _nvd_search(params, limit), "source": "NIST NVD"}


@app.tool(description="Find public PoC/EXP leads in local ExploitDB/SearchSploit and GitHub. Results are explicitly unverified and are never downloaded or executed.")
def vuln_search_public_pocs(query: str, limit: int = 10) -> dict[str, Any]:
    value = _safe_query(query)
    count = max(1, min(limit, 20))
    with ThreadPoolExecutor(max_workers=2) as pool:
        local_future = pool.submit(_searchsploit, value, count)
        github_future = pool.submit(_github_pocs, value, count)
        return {
            "query": value,
            "exploitdb": local_future.result(),
            "github": github_future.result(),
            "warning": "Discovery only. Review provenance and code, then validate in an isolated authorized target before use.",
        }


@app.tool(description="Watch newly disclosed high-risk CVEs and newly added CISA KEV entries. This is an emerging-threat watch, not proof of an undisclosed zero-day.")
def vuln_emerging_threat_watch(days: int = 7, limit: int = 20, minimum_cvss: float = 7.0) -> dict[str, Any]:
    window = max(1, min(days, 120))
    count = max(1, min(limit, 50))
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window)
    params = {
        "pubStartDate": cutoff.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
    }
    recent = _nvd_search(params, min(count * 3, 100))
    recent = [item for item in recent if float(((item.get("cvss") or {}).get("score") or 0)) >= minimum_cvss][:count]
    kev_rows = []
    for item in _kev_catalog().get("vulnerabilities") or []:
        try:
            added = datetime.strptime(str(item.get("dateAdded")), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if added >= cutoff:
            kev_rows.append(item)
    kev_rows.sort(key=lambda item: str(item.get("dateAdded", "")), reverse=True)
    ids = list(dict.fromkeys([str(item.get("id")) for item in recent if item.get("id")] + [str(item.get("cveID")) for item in kev_rows]))
    epss = _epss_lookup(ids)
    return {
        "window_days": window,
        "new_high_severity_cves": [{**item, "epss": epss.get(str(item.get("id")))} for item in recent],
        "new_known_exploited": [{**item, "epss": epss.get(str(item.get("cveID")))} for item in kev_rows[:count]],
        "zero_day_policy": "A recent CVE or public PoC is not labelled zero-day unless an authoritative source documents exploitation before disclosure or patch availability.",
    }


@app.tool(description="Query OSV for vulnerabilities affecting an exact open-source package and version. Useful for npm, PyPI, Maven, Go, crates.io, NuGet, Packagist, and other OSV ecosystems.")
def vuln_query_package(ecosystem: str, package: str, version: str) -> dict[str, Any]:
    eco = _safe_query(ecosystem)
    name = _safe_query(package)
    ver = _safe_query(version)
    data = _request_json(
        f"{OSV_API}/query",
        payload={"version": ver, "package": {"name": name, "ecosystem": eco}},
        cache_ttl=600,
    )
    return {"ecosystem": eco, "package": name, "version": ver, "vulnerabilities": data.get("vulns") or [], "source": "OSV.dev"}


@app.tool(description="Retrieve one OSV/GHSA/CVE advisory record by identifier without executing or downloading exploit code.")
def vuln_get_advisory(advisory_id: str) -> dict[str, Any]:
    value = _safe_query(advisory_id)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError("advisory_id contains unsupported characters")
    return _request_json(f"{OSV_API}/vulns/{quote(value, safe='')}", cache_ttl=600)


@app.tool(description="Check availability of authoritative vulnerability sources and local ExploitDB/SearchSploit integration.")
def vuln_intel_source_health() -> dict[str, Any]:
    checks: dict[str, Callable[[], Any]] = {
        "nvd": lambda: _nvd_lookup("CVE-2021-44228").get("id"),
        "epss": lambda: bool(_epss_lookup(["CVE-2021-44228"])),
        "cisa_kev": lambda: bool(_kev_catalog().get("vulnerabilities")),
        "osv": lambda: bool(_request_json(f"{OSV_API}/vulns/CVE-2021-44228", cache_ttl=600)),
        "searchsploit": lambda: bool(shutil.which("searchsploit")),
    }
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(checks)) as pool:
        futures = [pool.submit(_source_call, name, function) for name, function in checks.items()]
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result
    results["github"] = {"ok": True, "authenticated": bool(os.getenv("GITHUB_TOKEN")), "note": "unauthenticated search has a lower rate limit"}
    return {"sources": results, "cache_entries": len(_CACHE), "read_only": True}


if __name__ == "__main__":
    app.run(transport="stdio")
