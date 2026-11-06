#!/usr/bin/env python3
"""Read-only Claude-Red skills MCP for JySecAI.

Merges the upstream open-source Claude-Red methodology library (MIT License,
SnailSploit / Kai Aizen, https://github.com/SnailSploit/Claude-Red) with
JySecAI's own local ``skills/`` directory and exposes the union as five
read-only MCP tools.

Safety posture: this server only retrieves *text*. It never spawns a
subprocess, never runs a shell command, never downloads a payload and never
contacts a target. Every outbound request is HTTPS to an allowlisted host, and
every failure degrades into a structured error object instead of an exception
escaping to the caller.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import yaml

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP as _MCPServer


# ---------------------------------------------------------------------------
# 常數
# ---------------------------------------------------------------------------

UPSTREAM_REPO = "SnailSploit/Claude-Red"
UPSTREAM_BRANCH = "main"
UPSTREAM_CATALOG_URL = (
    f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_BRANCH}/claude-skills.json"
)
UPSTREAM_TREE_URL = (
    f"https://api.github.com/repos/{UPSTREAM_REPO}/git/trees/{UPSTREAM_BRANCH}?recursive=1"
)
UPSTREAM_RAW_TEMPLATE = (
    f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_BRANCH}/{{path}}"
)
# 本地镜像：微信文 / GitHub Claude-Red 的 claude-skills.json。
# 有文件时目录与内容走本地，GitHub 只作缺包时的回退。
_LOCAL_UPSTREAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upstream")
_LOCAL_CATALOG_PATH = os.path.join(_LOCAL_UPSTREAM_DIR, "claude-skills.json")
UPSTREAM_LICENSE = "MIT"
UPSTREAM_ATTRIBUTION = "Claude-Red (MIT) by SnailSploit / Kai Aizen"

USER_AGENT = "JySecAI-RedTeamSkills/1.0"
HTTP_TIMEOUT = max(5, min(int(os.getenv("REDTEAM_SKILLS_HTTP_TIMEOUT", "20")), 60))

MAX_SKILL_BYTES = 4 * 1024 * 1024          # 單一 SKILL.md 上限
MAX_CATALOG_BYTES = 8 * 1024 * 1024        # claude-skills.json / git tree 上限
MAX_LOCAL_FILE_BYTES = 4 * 1024 * 1024     # 本地 SKILL.md 讀取上限
MAX_LIMIT = 200                            # limit 參數硬上限
MAX_QUERY_LEN = 200
MAX_TEXT_LEN = 2000
MAX_CATEGORY_LEN = 80
MAX_NAME_LEN = 128
MAX_DESCRIPTION_LEN = 1200

_ALLOWED_HOSTS = {"raw.githubusercontent.com", "api.github.com"}
_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_UPSTREAM_PATH_RE = re.compile(r"^Skills/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+/SKILL\.md$")
_ASCII_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")

# 本地 skill 沒有分類目錄；用上游分類詞表做最長前綴比對，
# 讓本地與上游的同名分類可以合併呈現。命中的本地 skill 進對應分類，
# 其餘進 "jysecai-local" 桶。
_LOCAL_CATEGORY_HINTS = (
    "active-directory", "social-engineering", "post-exploitation", "supply-chain",
    "exploit-dev", "infrastructure", "forensics", "fuzzing", "container", "crypto",
    "privesc", "recon", "utility", "wireless", "mobile", "network", "cicd", "cloud",
    "web", "api", "auth", "ai", "iot",
)
LOCAL_FALLBACK_CATEGORY = "jysecai-local"

# 觸發詞抽取：從 "Use when ..." / "Trigger on: ..." / "使用場景 ..." 等句型取片段
_TRIGGER_MARKERS = (
    "use this skill when", "use skill when", "use when", "activate when",
    "triggered by", "triggers on", "trigger on", "use cases",
    "使用场景", "使用場景", "适用场景", "適用場景", "使用时机", "使用時機", "适用", "適用",
)
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "by", "can", "for", "from",
    "how", "in", "into", "is", "it", "its", "not", "of", "on", "or", "per", "that",
    "the", "this", "to", "use", "used", "using", "via", "was", "what", "when",
    "where", "which", "why", "will", "with", "you", "your",
}

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK = threading.Lock()


class SourceError(RuntimeError):
    """外部來源不可用或回應不合法。"""


# ---------------------------------------------------------------------------
# TTL 快取
# ---------------------------------------------------------------------------

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


def _cache_clear() -> None:
    """清空 TTL 快取（測試用）。"""
    with _CACHE_LOCK:
        _CACHE.clear()


# ---------------------------------------------------------------------------
# 對外請求（HTTPS + host 白名單 + 大小上限 + 逾時）
# ---------------------------------------------------------------------------

def _request_bytes(url: str, max_bytes: int = MAX_CATALOG_BYTES) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise SourceError("outbound host is not allowlisted")
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            request = Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json, application/json, text/plain, */*",
                    "User-Agent": USER_AGENT,
                },
            )
            with urlopen(request, timeout=HTTP_TIMEOUT) as response:
                raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
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


def _fetch_json(url: str, *, max_bytes: int = MAX_CATALOG_BYTES, cache_ttl: int = 6 * 3600) -> Any:
    key = f"json:{url}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        data = json.loads(_request_bytes(url, max_bytes).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"invalid JSON: {exc}") from exc
    return _cache_set(key, data, cache_ttl)


# ---------------------------------------------------------------------------
# 輸入驗證 / 正規化
# ---------------------------------------------------------------------------

def _safe_text(value: Any, max_len: int, field: str) -> str:
    if value is None:
        raise ValueError(f"{field} is required")
    text = str(value)
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError(f"{field} contains control characters")
    text = " ".join(text.split())
    if not text:
        raise ValueError(f"{field} must not be empty")
    if len(text) > max_len:
        raise ValueError(f"{field} must not exceed {max_len} characters")
    return text


def _normalize_skill_name(value: Any) -> str:
    """技能名只允許 ``^[a-z0-9][a-z0-9._-]*$``；擋掉路徑分隔符與控制字元。"""
    if value is None:
        raise ValueError("skill name is required")
    text = str(value)
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError("skill name contains control characters")
    text = text.strip().lower()
    if not text:
        raise ValueError("skill name must not be empty")
    if len(text) > MAX_NAME_LEN:
        raise ValueError(f"skill name must not exceed {MAX_NAME_LEN} characters")
    if not _SKILL_NAME_RE.match(text):
        raise ValueError("skill name must match ^[a-z0-9][a-z0-9._-]*$")
    return text


def _clamp_limit(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(number, MAX_LIMIT))


def _clip(value: Any, size: int = MAX_DESCRIPTION_LEN) -> str:
    text = str(value or "").strip()
    return text if len(text) <= size else f"{text[:size]}..."


def _tokenize(text: str) -> list[str]:
    """英文以單字切、連字號也切；中文以 bigram 切，讓本地中文描述可被檢索。"""
    lowered = str(text or "").lower()
    tokens = [
        token for token in _ASCII_TOKEN_RE.findall(lowered)
        if len(token) > 1 and token not in _STOPWORDS
    ]
    for run in _CJK_RE.findall(lowered):
        if len(run) == 1:
            if run not in _STOPWORDS:
                tokens.append(run)
            continue
        for index in range(len(run) - 1):
            bigram = run[index:index + 2]
            if bigram not in _STOPWORDS:
                tokens.append(bigram)
    return tokens


# ---------------------------------------------------------------------------
# 本地 skill 根目錄解析
# ---------------------------------------------------------------------------

_SKILLS_ROOT: str | None = None
_SKILLS_ROOT_RESOLVED = False


def _discover_skills_root() -> str | None:
    """先看 ``JY_TECH_SKILLS_DIR``；否則從本檔所在目錄一路往上找 ``skills/``。

    部署版面是 ``/opt/jysecai/core/current/mcp-servers/redteam_skills/``，
    因此往上兩層就會命中 ``/opt/jysecai/core/current/skills/``。
    """
    env = (os.getenv("JY_TECH_SKILLS_DIR") or "").strip()
    if env:
        try:
            resolved = os.path.abspath(env)
        except (OSError, ValueError):
            resolved = ""
        if resolved and os.path.isdir(resolved):
            return resolved
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        candidate = os.path.join(current, "skills")
        if os.path.isdir(candidate):
            return os.path.abspath(candidate)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _skills_root() -> str | None:
    global _SKILLS_ROOT, _SKILLS_ROOT_RESOLVED
    if not _SKILLS_ROOT_RESOLVED:
        _SKILLS_ROOT = _discover_skills_root()
        _SKILLS_ROOT_RESOLVED = True
    return _SKILLS_ROOT


def _set_skills_root(path: str | None) -> None:
    """測試用：直接指定（或清空）本地 skills 根目錄。"""
    global _SKILLS_ROOT, _SKILLS_ROOT_RESOLVED
    _SKILLS_ROOT = os.path.abspath(path) if path else None
    _SKILLS_ROOT_RESOLVED = True


def _local_skill_path(name: str) -> str | None:
    """組出本地 SKILL.md 路徑，並確認解析後仍在 skills 根目錄之內。"""
    if not _SKILL_NAME_RE.match(name):
        return None
    root = _skills_root()
    if not root:
        return None
    candidate = os.path.join(root, name, "SKILL.md")
    try:
        root_real = os.path.realpath(root)
        target_real = os.path.realpath(candidate)
    except OSError:
        return None
    if not target_real.startswith(root_real + os.sep):
        return None
    if not os.path.isfile(target_real):
        return None
    return target_real


# ---------------------------------------------------------------------------
# YAML front matter 解析（容錯）
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"\A\ufeff?[ \t]*---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_FOLD_MARKERS = {">", ">-", ">+", "|", "|-", "|+"}


def _join_folded(values: list[str]) -> str:
    parts: list[str] = []
    for index, value in enumerate(values):
        text = str(value).strip()
        if index == 0 and text in _FOLD_MARKERS:
            continue
        parts.append(text)
    text = " ".join(part for part in parts if part).strip()
    if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    return text


def _scan_front_matter(block: str) -> dict[str, Any]:
    """YAML 壞掉時的後備掃描器：抓 ``key: value`` 與縮排續行。"""
    result: dict[str, Any] = {}
    key: str | None = None
    buffer: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line[:1].isspace() and key:
            buffer.append(line.strip())
            continue
        if key is not None:
            result[key] = _join_folded(buffer)
        key = None
        buffer = []
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1)
            inline = match.group(2).strip()
            buffer = [inline] if inline else []
    if key is not None:
        result[key] = _join_folded(buffer)
    return result


def _parse_front_matter(text: str) -> dict[str, Any]:
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return _scan_front_matter(block)
    if isinstance(data, dict):
        return data
    return _scan_front_matter(block)


def _extract_tags(meta: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    candidates: list[Any] = []
    metadata = meta.get("metadata")
    if isinstance(metadata, dict):
        candidates.append(metadata.get("tags"))
    candidates.append(meta.get("tags"))
    for value in candidates:
        if isinstance(value, str):
            items: list[str] = [part for part in re.split(r"[,;|]", value)]
        elif isinstance(value, (list, tuple)):
            items = [str(part) for part in value]
        else:
            continue
        for item in items:
            tag = str(item).strip().strip("\"'").lower()
            if tag and tag not in tags:
                tags.append(tag)
    return tags[:16]


def _derive_triggers(description: str, tags: list[str]) -> list[str]:
    """從「Use when / Trigger on / 使用場景」句型抽出觸發短語。"""
    triggers: list[str] = []
    lowered = str(description or "").lower()
    for marker in _TRIGGER_MARKERS:
        start = 0
        while True:
            index = lowered.find(marker, start)
            if index < 0:
                break
            tail = lowered[index + len(marker):]
            tail = tail.lstrip(":-–— ")
            cut = len(tail)
            for stop in (". ", ".", "; ", "\n"):
                position = tail.find(stop)
                if position != -1:
                    cut = min(cut, position)
            segment = tail[:cut]
            for piece in re.split(r"[,;|、，/]|\band\b|\bor\b", segment):
                phrase = re.sub(r"\s+", " ", piece).strip(" .:-–—")
                phrase = re.sub(r"^(when|while|if|to|for)\s+", "", phrase).strip()
                if 2 < len(phrase) <= 80 and phrase not in triggers:
                    triggers.append(phrase)
            start = index + len(marker)
    for tag in tags:
        if tag not in triggers:
            triggers.append(tag)
    return triggers[:24]


def _derive_local_category(name: str) -> str:
    lowered = str(name or "").lower()
    for category in sorted(_LOCAL_CATEGORY_HINTS, key=len, reverse=True):
        if lowered == category or lowered.startswith(f"{category}-"):
            return category
    return LOCAL_FALLBACK_CATEGORY


# ---------------------------------------------------------------------------
# 本地索引
# ---------------------------------------------------------------------------

def _read_local_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(MAX_LOCAL_FILE_BYTES)
    except OSError as exc:
        raise SourceError(f"cannot read local skill file: {exc}") from exc


def _parse_local_skill(path: str, fallback_name: str) -> dict[str, Any]:
    content = _read_local_file(path)
    meta = _parse_front_matter(content)
    name = str(meta.get("name") or fallback_name).strip() or fallback_name
    description = str(meta.get("description") or "").strip()
    return {
        "name": name,
        "description": description,
        "tags": _extract_tags(meta),
        "content": content,
    }


def _local_index() -> list[dict[str, Any]]:
    cached = _cache_get("local-index")
    if cached is not None:
        return cached
    rows: list[dict[str, Any]] = []
    root = _skills_root()
    cat_map = {r["name"]: str(r.get("category") or "") for r in _load_local_catalog()}
    if root:
        try:
            entries = sorted(os.scandir(root), key=lambda item: item.name)
        except OSError:
            entries = []
        for entry in entries:
            try:
                if not entry.is_dir():
                    continue
            except OSError:
                continue
            skill_file = os.path.join(entry.path, "SKILL.md")
            if not os.path.isfile(skill_file):
                continue
            try:
                parsed = _parse_local_skill(skill_file, entry.name)
            except SourceError:
                continue
            name = parsed["name"] or entry.name
            description = parsed["description"]
            category = cat_map.get(name) or _derive_local_category(name)
            rows.append({
                "name": name,
                "dir_name": entry.name,
                "description": _clip(description),
                "category": category,
                "source": "local",
                "triggers": _derive_triggers(description, parsed["tags"]),
                "local_path": skill_file,
                "upstream_path": "",
            })
    return _cache_set("local-index", rows, 60)


# ---------------------------------------------------------------------------
# 上游索引（claude-skills.json，失敗退回 git tree）
# ---------------------------------------------------------------------------

def _rows_from_catalog(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    entries = data.get("skills")
    if not isinstance(entries, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        path = str(item.get("path") or "").strip()
        if not name or not path:
            continue
        category = str(item.get("category") or "").strip().lower()
        if not category and path.startswith("Skills/"):
            parts = path.split("/")
            if len(parts) > 2:
                category = parts[1].lower()
        description = str(item.get("description") or "").strip()
        rows.append({
            "name": name,
            "dir_name": name,
            "description": _clip(description),
            "category": category or "upstream",
            "source": "upstream",
            "triggers": _derive_triggers(description, []),
            "local_path": "",
            "upstream_path": path,
        })
    return rows


def _rows_from_tree(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    tree = data.get("tree")
    if not isinstance(tree, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in tree:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if item.get("type") != "blob" or not _UPSTREAM_PATH_RE.match(path):
            continue
        parts = path.split("/")
        rows.append({
            "name": parts[2].lower(),
            "dir_name": parts[2].lower(),
            "description": "",
            "category": parts[1].lower(),
            "source": "upstream",
            "triggers": [],
            "local_path": "",
            "upstream_path": path,
        })
    return rows


def _load_local_catalog() -> list[dict[str, Any]]:
    if not os.path.isfile(_LOCAL_CATALOG_PATH):
        return []
    try:
        with open(_LOCAL_CATALOG_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return []
    return _rows_from_catalog(data)


def _upstream_index() -> list[dict[str, Any]]:
    cached = _cache_get("upstream-index")
    if cached is not None:
        return cached
    rows = _load_local_catalog()
    if not rows:
        try:
            rows = _rows_from_catalog(_fetch_json(UPSTREAM_CATALOG_URL, max_bytes=MAX_CATALOG_BYTES))
        except SourceError:
            rows = []
    if not rows:
        try:
            rows = _rows_from_tree(_fetch_json(UPSTREAM_TREE_URL, max_bytes=MAX_CATALOG_BYTES))
        except SourceError:
            rows = []
    return _cache_set("upstream-index", rows, 6 * 3600 if rows else 60)


def _upstream_content(path: str) -> str:
    if not _UPSTREAM_PATH_RE.match(path or ""):
        raise SourceError("upstream path is not allowlisted")
    parts = path.split("/")
    if len(parts) >= 3:
        local = _local_skill_path(parts[2].lower())
        if local:
            return _read_local_file(local)
    url = UPSTREAM_RAW_TEMPLATE.format(path=quote(path))
    raw = _request_bytes(url, MAX_SKILL_BYTES)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceError(f"invalid UTF-8 content: {exc}") from exc


def _merged_rows() -> list[dict[str, Any]]:
    rows = list(_local_index())
    seen = {str(row.get("name") or "") for row in rows}
    for row in _upstream_index():
        name = str(row.get("name") or "")
        if name and name in seen:
            continue
        rows.append(row)
        if name:
            seen.add(name)
    return rows


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row["name"],
        "description": row.get("description", ""),
        "category": row.get("category", ""),
        "source": row.get("source", ""),
        "triggers": list(row.get("triggers") or []),
        "local_path": row.get("local_path", ""),
        "upstream_path": row.get("upstream_path", ""),
    }


# ---------------------------------------------------------------------------
# 評分
# ---------------------------------------------------------------------------

def _score_skill(row: dict[str, Any], tokens: list[str], lowered_text: str) -> tuple[float, str]:
    """以觸發詞 / 名稱 / 描述的 token 重疊評分。"""
    score = 0.0
    reasons: list[str] = []
    token_set = set(tokens)

    for trigger in row.get("triggers") or []:
        phrase = str(trigger).strip().lower()
        if not phrase:
            continue
        if phrase in lowered_text:
            score += 3.0
            reasons.append(f"trigger '{trigger}' matched")
            continue
        overlap = set(_tokenize(phrase)) & token_set
        if overlap:
            score += min(1.5, 0.75 * len(overlap))
            reasons.append(f"trigger '{trigger}' partially matched")

    for token in sorted(set(_tokenize(row.get("name", ""))) & token_set):
        score += 2.0
        reasons.append(f"name token '{token}' matched")

    overlap = set(_tokenize(row.get("description", ""))) & token_set
    if overlap:
        score += min(3.0, 0.5 * len(overlap))
        reasons.append("description mentions " + ", ".join(sorted(overlap)[:4]))

    return score, "; ".join(reasons[:4])


def _find_row(name: str, source: str) -> dict[str, Any] | None:
    for row in _merged_rows():
        if row.get("source") != source:
            continue
        if row.get("name") == name or row.get("dir_name") == name:
            return row
    return None


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

app = _MCPServer(
    name="redteam-skills",
    instructions=(
        "Read-only access to the merged red-team methodology skill library: the upstream "
        "Claude-Red library (MIT, SnailSploit / Kai Aizen) plus JySecAI's own local skills. "
        "Every row is labelled with its source (local or upstream). The server returns text "
        "only: it never executes commands, never downloads payloads, and never contacts a target."
    ),
)


@app.tool(description="List merged red-team skill categories with per-category skill counts and the sources that contribute to each category.")
def redteam_list_skill_categories() -> dict[str, Any]:
    try:
        rows = _merged_rows()
    except Exception as exc:  # pragma: no cover - 防禦性：不讓例外逃出去
        return {
            "ok": False, "error": str(exc), "categories": [], "total": 0,
            "sources": {"local": 0, "upstream": 0},
        }
    grouped: dict[str, dict[str, Any]] = {}
    counts = {"local": 0, "upstream": 0}
    for row in rows:
        source = str(row.get("source") or "")
        counts[source] = counts.get(source, 0) + 1
        category = str(row.get("category") or "unknown")
        entry = grouped.setdefault(category, {"name": category, "skill_count": 0, "sources": []})
        entry["skill_count"] += 1
        if source not in entry["sources"]:
            entry["sources"].append(source)
    categories = sorted(grouped.values(), key=lambda item: (-item["skill_count"], item["name"]))
    for entry in categories:
        entry["sources"] = sorted(entry["sources"])
    return {"categories": categories, "total": len(categories), "sources": counts}


@app.tool(description="List merged red-team skills (upstream Claude-Red + JySecAI local library) with descriptions, trigger phrases, category and source label.")
def redteam_list_skills(category: str = "", limit: int = 50) -> dict[str, Any]:
    count = _clamp_limit(limit, 50)
    wanted = ""
    if category:
        try:
            wanted = _safe_text(category, MAX_CATEGORY_LEN, "category").lower()
        except ValueError as exc:
            return {"ok": False, "error": str(exc), "skills": [], "total": 0, "category": str(category), "limit": count}
    rows = _merged_rows()
    if wanted:
        rows = [row for row in rows if str(row.get("category") or "").lower() == wanted]
    skills = [_public_row(row) for row in rows[:count]]
    return {"skills": skills, "total": len(rows), "category": wanted, "limit": count}


@app.tool(description="Get the full methodology text of one merged red-team skill by name. Upstream content is fetched on demand and cached; the local skill file is used as fallback. Read-only text retrieval.")
def redteam_get_skill(name: str) -> dict[str, Any]:
    try:
        skill_name = _normalize_skill_name(name)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    upstream_error = ""
    row = _find_row(skill_name, "upstream")
    if row is not None and row.get("upstream_path"):
        try:
            content = _upstream_content(row["upstream_path"])
        except SourceError as exc:
            content = ""
            upstream_error = str(exc)
        if content:
            meta = _parse_front_matter(content)
            description = str(meta.get("description") or row.get("description") or "").strip()
            return {
                "ok": True,
                "skill": {
                    "name": row["name"],
                    "category": row.get("category", ""),
                    "source": "upstream",
                    "content": content,
                    "description": description,
                },
            }

    local_row = _find_row(skill_name, "local")
    local_path = None
    if local_row and local_row.get("local_path"):
        local_path = str(local_row["local_path"])
    if local_path is None:
        local_path = _local_skill_path(skill_name)
    if local_path:
        try:
            content = _read_local_file(local_path)
        except SourceError as exc:
            return {"ok": False, "error": str(exc)}
        meta = _parse_front_matter(content)
        description = str(meta.get("description") or "").strip()
        return {
            "ok": True,
            "skill": {
                "name": str(meta.get("name") or skill_name),
                "category": str(local_row.get("category")) if local_row else _derive_local_category(skill_name),
                "source": "local",
                "content": content,
                "description": description,
            },
        }

    if upstream_error:
        return {"ok": False, "error": f"skill '{skill_name}' could not be retrieved from upstream: {upstream_error}"}
    return {"ok": False, "error": f"skill '{skill_name}' was not found in the upstream or the local skill library"}


@app.tool(description="Keyword-search the merged red-team skill library across skill name, description and trigger phrases.")
def redteam_search_skills(query: str, limit: int = 10) -> dict[str, Any]:
    count = _clamp_limit(limit, 10)
    try:
        needle = _safe_text(query, MAX_QUERY_LEN, "query")
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "query": str(query), "results": [], "total": 0}
    tokens = _tokenize(needle)
    if not tokens:
        return {
            "ok": False, "error": "query must contain at least one searchable token",
            "query": needle, "results": [], "total": 0,
        }
    results: list[dict[str, Any]] = []
    for row in _merged_rows():
        score, reason = _score_skill(row, tokens, needle.lower())
        if score <= 0:
            continue
        entry = _public_row(row)
        entry["score"] = round(score, 2)
        entry["reason"] = reason
        results.append(entry)
    results.sort(key=lambda item: (-item["score"], item["name"]))
    return {"query": needle, "results": results[:count], "total": len(results)}


@app.tool(description="Match a free-form task or target description against the merged skill triggers to decide which red-team skills should be auto-loaded for this engagement.")
def redteam_match_skills(text: str, limit: int = 10) -> dict[str, Any]:
    count = _clamp_limit(limit, 10)
    try:
        raw = _safe_text(text, MAX_TEXT_LEN, "text")
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "text": str(text), "matches": [], "total": 0}
    tokens = _tokenize(raw)
    if not tokens:
        return {
            "ok": False, "error": "text must contain at least one searchable token",
            "text": raw, "matches": [], "total": 0,
        }
    matches: list[dict[str, Any]] = []
    for row in _merged_rows():
        score, reason = _score_skill(row, tokens, raw.lower())
        if score <= 0:
            continue
        matches.append({
            "name": row["name"],
            "score": round(score, 2),
            "reason": reason,
            "source": row.get("source", ""),
            "category": row.get("category", ""),
        })
    matches.sort(key=lambda item: (-item["score"], item["name"]))
    return {"text": raw, "matches": matches[:count], "total": len(matches)}


if __name__ == "__main__":
    app.run(transport="stdio")
