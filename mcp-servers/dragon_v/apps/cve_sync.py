#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dragon-V CVE 自動同步管線：NVD API 2.0 -> 離線 YAML 武器庫。

補上離線武器庫（data/cve/{zh,en}，原 414+414 條）的資料真空：
依 AI/LLM 應用關鍵字呼叫 NVD CVE API 2.0（keywordSearch）增量拉取，
轉換為 exploit_database.py 可載入的 YAML（data/cve/<lang>/<app>/CVE-*.yaml）。

特性：
- 限速：無 NVD_API_KEY 時 5 req/30s（官方上限）；有 key 時 45 req/30s
  （官方上限 50，留餘裕），滾動視窗 + sleep 實作。
- 指數退避重試：429/403/5xx/網路逾時，尊重 Retry-After，上限 5 次。
- 增量：data/cve/.sync_state.json 記錄 last_synced、各關鍵字 last_fetch、
  累計新增數；last_fetch 在 120 天內時改用 lastModStart/EndDate 視窗查詢。
- 去重：掃描 data/cve/{zh,en}/*/*.yaml 檔名（CVE id），已存在即跳過。
- zh 鏡像：同步寫入 zh 目錄，內容暫以英文值填入（待後續翻譯），
  檔名與 id 與 en 完全一致。

用法（在 mcp-servers/dragon_v 目錄下執行）：
  python -m apps.cve_sync --list-keywords
  python -m apps.cve_sync --keywords comfyui --max-per-keyword 5 --dry-run
  python -m apps.cve_sync --keywords comfyui,ollama --max-per-keyword 20
  python -m apps.cve_sync                # 全量關鍵字（fingerprints + 內建清單）

僅供 JySecAI 授權資安作業平台離線使用；資料來源為 NVD 公開 API。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:  # 以套件方式（python -m apps.cve_sync）或 MCP server 匯入
    from apps.exploit_database import default_data_dir
except ImportError:  # 直接以 python apps/cve_sync.py 執行
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from apps.exploit_database import default_data_dir

_NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_RESULTS_PER_PAGE = 200
_REQUEST_TIMEOUT = 30
_MAX_RETRIES = 5
_BACKOFF_BASE = 2.0
_BACKOFF_MAX = 60.0
_NVD_WINDOW_DAYS = 119  # NVD 日期視窗上限 120 天，留一天餘裕
_USER_AGENT = "dragon-v-cve-sync/1.0 (JySecAI authorized security platform)"

_SYNC_STATE_FILENAME = ".sync_state.json"

_KEYWORD_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,59}$")
_CVE_ID_RE = re.compile(r"^CVE-\d{4}-\d{1,}$", re.IGNORECASE)

# 內建兜底關鍵字清單（常見 AI/LLM 應用；與 fingerprints 提取結果合併）
_BUILTIN_KEYWORDS: List[str] = [
    "anythingllm",
    "comfyui",
    "dify",
    "ollama",
    "vllm",
    "langflow",
    "flowise",
    "litellm",
    "open-webui",
    "gradio",
    "fastchat",
    "localai",
    "huggingface",
    "pyload",
    "n8n",
    "langchain",
    "lollms",
    "gpt4all",
    "privategpt",
    "ragflow",
    "xinference",
    "llama-factory",
    "text-generation-webui",
    "openllm",
    "chatgpt-next-web",
    "one-api",
    "mlflow",
    "kubeflow",
    "tensorboard",
    "marimo",
    "langfuse",
    "qanything",
    "triton-inference-server",
]


# ---------------------------------------------------------------------------
# YAML 輸出（與 data/cve/{zh,en} 現有格式對齐：info / rule / references）
# ---------------------------------------------------------------------------


class _BlockStyleDumper(yaml.SafeDumper):
    """多行字串輸出為 | 區塊純量，貼近現有 en 檔案的 details 寫法。"""


def _str_representer(dumper: yaml.SafeDumper, data: str) -> Any:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_BlockStyleDumper.add_representer(str, _str_representer)


def _dump_record(record: Dict[str, Any]) -> str:
    return yaml.dump(
        record,
        Dumper=_BlockStyleDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    )


def _write_yaml(path: Path, record: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(_dump_record(record))
    return path


# ---------------------------------------------------------------------------
# 關鍵字來源：data/fingerprints YAML 應用名 + 內建兜底清單
# ---------------------------------------------------------------------------


def extract_fingerprint_keywords(data_dir: Path | str | None = None) -> List[str]:
    """從 data/fingerprints 的 YAML 提取應用名（info.name / metadata.product 等）。"""
    base = Path(data_dir) if data_dir else default_data_dir()
    fp_dir = base / "fingerprints"
    names: set[str] = set()
    if fp_dir.is_dir():
        for yaml_file in sorted(fp_dir.rglob("*.yaml")):
            try:
                with yaml_file.open("r", encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
            except Exception:
                doc = None
            info = doc.get("info") or {} if isinstance(doc, dict) else {}
            meta = info.get("metadata") or {} if isinstance(info, dict) else {}
            for candidate in (
                info.get("name") if isinstance(info, dict) else None,
                meta.get("product") if isinstance(meta, dict) else None,
                meta.get("vendor") if isinstance(meta, dict) else None,
                yaml_file.stem,
            ):
                if isinstance(candidate, str):
                    names.add(candidate.strip().lower())
    return sorted(n for n in names if _KEYWORD_RE.fullmatch(n))


def default_keywords(data_dir: Path | str | None = None) -> List[str]:
    """自動關鍵字 = fingerprints 提取 + 內建兜底清單（合併去重）。"""
    extracted = extract_fingerprint_keywords(data_dir)
    return sorted(set(extracted) | set(_BUILTIN_KEYWORDS))


def normalize_keywords(keywords: Any) -> List[str]:
    """接受 list 或逗號分隔字串，正規化並過濾不合法關鍵字。"""
    if keywords is None:
        return []
    if isinstance(keywords, str):
        raw = keywords.split(",")
    else:
        raw = list(keywords)
    result: List[str] = []
    for token in raw:
        value = (token or "").strip().lower()
        if value and _KEYWORD_RE.fullmatch(value) and value not in result:
            result.append(value)
    return result


# ---------------------------------------------------------------------------
# 限速與 NVD API 呼叫（滾動視窗 + 指數退避）
# ---------------------------------------------------------------------------


class _RateLimiter:
    """滾動視窗限速器：window_seconds 內最多 max_requests 次請求。"""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = float(window_seconds)
        self._hits: deque[float] = deque()

    def wait(self) -> None:
        now = time.monotonic()
        while self._hits and now - self._hits[0] >= self.window_seconds:
            self._hits.popleft()
        if len(self._hits) >= self.max_requests:
            sleep_for = self.window_seconds - (now - self._hits[0]) + 0.25
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._hits.append(time.monotonic())


def _make_limiter(api_key: str) -> _RateLimiter:
    # NVD 官方限制：無 key 5 req/30s；有 key 50 req/30s（留餘裕用 45）
    return _RateLimiter(45 if api_key else 5, 30.5)


def _nvd_get(params: Dict[str, str], api_key: str, limiter: _RateLimiter) -> Dict[str, Any]:
    """呼叫 NVD CVE API 2.0，含指數退避重試；失敗時拋出 RuntimeError。"""
    query = urllib.parse.urlencode(params)
    url = f"{_NVD_API_URL}?{query}"
    last_error = "unknown error"
    for attempt in range(_MAX_RETRIES):
        limiter.wait()
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        if api_key:
            headers["apiKey"] = api_key
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            if exc.code in (403, 429) or 500 <= exc.code < 600:
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.0
                delay = max(delay, min(_BACKOFF_BASE**attempt, _BACKOFF_MAX))
                time.sleep(delay)
                continue
            raise RuntimeError(f"NVD API {last_error}（url={url}）") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = str(exc) or exc.__class__.__name__
            time.sleep(min(_BACKOFF_BASE**attempt, _BACKOFF_MAX))
    raise RuntimeError(f"NVD API 重試 {_MAX_RETRIES} 次仍失敗：{last_error}")


# ---------------------------------------------------------------------------
# NVD JSON -> 現有 YAML 格式轉換
# ---------------------------------------------------------------------------


def _extract_cvss(cve: Dict[str, Any]) -> Tuple[str, str, float]:
    """優先 CVSS v3.1 Primary，其次 v3.0、v2；回傳 (vector, severity, score)。"""
    metrics = cve.get("metrics") or {}
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if not entries:
            continue
        entry = next((e for e in entries if e.get("type") == "Primary"), entries[0])
        data = entry.get("cvssData") or {}
        vector = str(data.get("vectorString") or "")
        severity = str(data.get("baseSeverity") or entry.get("baseSeverity") or "").upper()
        try:
            score = float(data.get("baseScore") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        if vector or severity:
            return vector, severity or "UNKNOWN", score
    return "", "UNKNOWN", 0.0


def _extract_affected(cve: Dict[str, Any]) -> List[Dict[str, Any]]:
    """從 NVD configurations (CPE) 取受影響產品與版本界線。"""
    affected: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for config in cve.get("configurations") or []:
        for node in config.get("nodes") or []:
            for match in node.get("cpeMatch") or []:
                if not match.get("vulnerable"):
                    continue
                criteria = str(match.get("criteria") or "")
                parts = criteria.split(":")
                if len(parts) < 5 or parts[0] != "cpe":
                    continue
                vendor, product = parts[2], parts[3]
                if (vendor, product) in seen:
                    continue
                seen.add((vendor, product))
                affected.append(
                    {
                        "vendor": vendor,
                        "product": product,
                        "version": parts[4] if len(parts) > 4 else "",
                        "version_end_excluding": match.get("versionEndExcluding"),
                        "version_end_including": match.get("versionEndIncluding"),
                    }
                )
    return affected


def _build_rule(affected: List[Dict[str, Any]]) -> str:
    """依 CPE 版本界線組 rule 字串（格式同現有檔案：version > "0" && ...）。"""
    for entry in affected:
        end_excluding = entry.get("version_end_excluding")
        if end_excluding:
            return f'version > "0" && version < "{end_excluding}"'
        end_including = entry.get("version_end_including")
        if end_including:
            return f'version > "0" && version <= "{end_including}"'
    return 'version > "0"'


def _build_advise(app_name: str, severity: str, affected: List[Dict[str, Any]]) -> str:
    """產生修護建議（暫以英文填入，zh 後續翻譯）。"""
    lines = [
        f"1. Track the official advisory of {app_name} and upgrade to a fixed version as soon as it is released.",
    ]
    for entry in affected[:3]:
        label = f"{entry['vendor']} {entry['product']}".strip()
        if entry.get("version_end_excluding"):
            lines.append(
                f"2. NVD CPE marks {label} vulnerable below version {entry['version_end_excluding']}; upgrade to that version or later."
            )
        elif entry.get("version_end_including"):
            lines.append(
                f"2. NVD CPE marks {label} vulnerable up to version {entry['version_end_including']}; upgrade beyond that version."
            )
        else:
            lines.append(f"2. NVD CPE marks {label} as affected; verify the deployed version and apply vendor patches.")
    if len(lines) == 1:
        lines.append(f"2. Verify the deployed {app_name} version against the NVD entry and apply vendor patches.")
    lines.extend(
        [
            f"3. Limit exposure of {app_name} (bind to trusted interfaces, enforce authentication) as a mitigation for {severity} risk.",
            "4. Re-check the NVD entry for updated remediation information.",
        ]
    )
    return "\n".join(lines)


def _build_summary(description: str) -> str:
    text = " ".join((description or "").split())
    parts = text.split(". ")
    summary = parts[0].rstrip(".") if parts and parts[0] else text
    if len(summary) > 240:
        summary = summary[:237].rstrip() + "..."
    return summary


def nvd_item_to_record(item: Dict[str, Any], app_name: str) -> Optional[Dict[str, Any]]:
    """將 NVD vulnerability item 轉為現有 YAML 格式（info / rule / references）。"""
    cve = (item or {}).get("cve") or {}
    cve_id = str(cve.get("id") or "").upper()
    if not _CVE_ID_RE.fullmatch(cve_id):
        return None
    if str(cve.get("vulnStatus") or "").lower() == "rejected":
        return None
    descriptions = cve.get("descriptions") or []
    description = next(
        (d.get("value", "") for d in descriptions if d.get("lang") == "en"),
        "",
    )
    if not description or description.startswith("** REJECT"):
        return None
    vector, severity, _score = _extract_cvss(cve)
    affected = _extract_affected(cve)
    references: List[str] = [f"https://nvd.nist.gov/vuln/detail/{cve_id}"]
    for ref in cve.get("references") or []:
        url = str(ref.get("url") or "")
        if url and url not in references:
            references.append(url)
    return {
        "info": {
            "name": app_name,
            "cve": cve_id,
            "summary": _build_summary(description),
            "details": textwrap.fill(" ".join(description.split()), width=100),
            "cvss": vector,
            "severity": severity,
            "security_advise": _build_advise(app_name, severity, affected),
        },
        "rule": _build_rule(affected),
        "references": references[:10],
    }


# ---------------------------------------------------------------------------
# 狀態檔（last_synced / 各關鍵字 last_fetch / 累計新增數）
# ---------------------------------------------------------------------------


def sync_state_path(data_dir: Path | str | None = None) -> Path:
    base = Path(data_dir) if data_dir else default_data_dir()
    return base / "cve" / _SYNC_STATE_FILENAME


def read_sync_state(data_dir: Path | str | None = None) -> Dict[str, Any]:
    path = sync_state_path(data_dir)
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            state = json.load(fh)
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def _save_sync_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_iso(value: str) -> Optional[datetime]:
    text = (value or "").strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _mod_window(last_fetch: str) -> Optional[Tuple[str, str]]:
    """last_fetch 在 120 天內時回傳 NVD lastMod 視窗，否則 None（全量查詢）。"""
    start = _parse_iso(last_fetch)
    if start is None:
        return None
    now = datetime.now(timezone.utc)
    if now - start > timedelta(days=_NVD_WINDOW_DAYS):
        return None
    start = max(start, now - timedelta(days=_NVD_WINDOW_DAYS))
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    return start.astimezone(timezone.utc).strftime(fmt)[:-3], now.strftime(fmt)[:-3]


# ---------------------------------------------------------------------------
# 去重與 app 目錄對應
# ---------------------------------------------------------------------------


def existing_cve_ids(data_dir: Path | str | None = None) -> set[str]:
    """掃描 data/cve/{zh,en}/*/*.yaml 檔名，回傳已存在的 CVE id 集合。"""
    base = Path(data_dir) if data_dir else default_data_dir()
    ids: set[str] = set()
    for lang in ("zh", "en"):
        lang_dir = base / "cve" / lang
        if not lang_dir.is_dir():
            continue
        for app_dir in lang_dir.iterdir():
            if not app_dir.is_dir():
                continue
            for yaml_file in app_dir.glob("*.yaml"):
                candidate = yaml_file.stem.upper()
                if _CVE_ID_RE.fullmatch(candidate):
                    ids.add(candidate)
    return ids


def resolve_app_dir(en_dir: Path, keyword: str) -> str:
    """關鍵字 -> app 子目錄名：優先既有目錄（不分大小寫），其次包含關係。"""
    if not en_dir.is_dir():
        return keyword
    dirs = [d.name for d in en_dir.iterdir() if d.is_dir()]
    lowered = keyword.lower()
    for name in dirs:
        if name.lower() == lowered:
            return name
    for name in dirs:
        if lowered in name.lower() or name.lower() in lowered:
            return name
    return lowered


# ---------------------------------------------------------------------------
# 同步主流程
# ---------------------------------------------------------------------------


def _fetch_keyword_items(
    keyword: str,
    *,
    api_key: str,
    limiter: _RateLimiter,
    last_fetch: str,
    max_new: int,
    known_ids: set[str],
) -> Tuple[List[Dict[str, Any]], int]:
    """拉取單一關鍵字的 NVD 結果，回傳 (新增 items, NVD totalResults)。"""
    params: Dict[str, str] = {
        "keywordSearch": keyword,
        "resultsPerPage": str(min(_RESULTS_PER_PAGE, max(1, max_new * 2))),
        "startIndex": "0",
        # 註：不加 noRejected 參數（NVD 對此參數回 HTTP 404，已實測），
        # Rejected CVE 改在 nvd_item_to_record 本地過濾。
    }
    window = _mod_window(last_fetch)
    if window:
        params["lastModStartDate"], params["lastModEndDate"] = window
    new_items: List[Dict[str, Any]] = []
    total = 0
    start_index = 0
    while True:
        params["startIndex"] = str(start_index)
        payload = _nvd_get(params, api_key, limiter)
        total = int(payload.get("totalResults") or 0)
        vulnerabilities = payload.get("vulnerabilities") or []
        for item in vulnerabilities:
            cve_id = str(((item or {}).get("cve") or {}).get("id") or "").upper()
            if not cve_id or cve_id in known_ids:
                continue
            known_ids.add(cve_id)
            new_items.append(item)
            if len(new_items) >= max_new:
                break
        if len(new_items) >= max_new:
            break
        start_index += len(vulnerabilities)
        if not vulnerabilities or total <= 0 or start_index >= total:
            break
    return new_items, total


def sync_cves(
    keywords: Any = None,
    *,
    max_per_keyword: int = 20,
    dry_run: bool = False,
    data_dir: Path | str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """同步 CVE：NVD API 2.0 -> data/cve/{en,zh}/<app>/CVE-*.yaml。

    - keywords：list 或逗號分隔字串；None/空字串時使用 fingerprints + 內建清單。
    - max_per_keyword：每個關鍵字最多新增的 CVE 數。
    - dry_run：只統計不寫檔、不更新狀態。
    回傳 dict：total_new / keywords 明細 / errors /（非 dry-run）added_files。
    """
    base = Path(data_dir) if data_dir else default_data_dir()
    cve_dir = base / "cve"
    en_dir = cve_dir / "en"
    zh_dir = cve_dir / "zh"
    state_path = sync_state_path(base)
    state = read_sync_state(base)

    keyword_list = normalize_keywords(keywords) or default_keywords(base)
    keyword_source = "explicit" if normalize_keywords(keywords) else "auto(fingerprints+builtin)"
    max_new = max(1, min(int(max_per_keyword), 200))

    key = (api_key if api_key is not None else os.getenv("NVD_API_KEY", "")).strip()
    limiter = _make_limiter(key)
    known_ids = existing_cve_ids(base)

    per_keyword: Dict[str, Dict[str, Any]] = {}
    errors: List[Dict[str, str]] = []
    added_files: List[str] = []

    for keyword in keyword_list:
        last_state = (state.get("keywords") or {}).get(keyword) or {}
        try:
            items, total = _fetch_keyword_items(
                keyword,
                api_key=key,
                limiter=limiter,
                last_fetch=str(last_state.get("last_fetch") or ""),
                max_new=max_new,
                known_ids=set(known_ids),
            )
        except Exception as exc:  # 單一關鍵字失敗不中斷整批
            errors.append({"keyword": keyword, "error": str(exc)})
            per_keyword[keyword] = {"new": 0, "error": str(exc)}
            continue

        records: List[Dict[str, Any]] = []
        for item in items:
            record = nvd_item_to_record(item, keyword)
            if record and record["info"]["cve"] not in known_ids:
                records.append(record)
        new_ids = [r["info"]["cve"] for r in records]
        per_keyword[keyword] = {
            "new": len(records),
            "total_on_nvd": total,
            "ids": new_ids,
            "mode": "incremental" if _mod_window(str(last_state.get("last_fetch") or "")) else "full",
        }

        if not dry_run and records:
            app_dir_name = resolve_app_dir(en_dir, keyword)
            for record in records:
                filename = f"{record['info']['cve']}.yaml"
                path_en = _write_yaml(en_dir / app_dir_name / filename, record)
                # zh 鏡像：檔名與 id 一致，內容暫以英文值填入待翻譯
                _write_yaml(zh_dir / app_dir_name / filename, record)
                added_files.append(str(path_en.relative_to(base)))
                known_ids.add(record["info"]["cve"])
            state.setdefault("keywords", {})[keyword] = {
                "last_fetch": _now_iso(),
                "cumulative_new": int(last_state.get("cumulative_new") or 0) + len(records),
                "last_new_ids": new_ids,
            }

    summary: Dict[str, Any] = {
        "dry_run": dry_run,
        "api_key_used": bool(key),
        "keyword_source": keyword_source,
        "total_new": sum(v.get("new", 0) for v in per_keyword.values()),
        "keywords": per_keyword,
        "errors": errors,
    }
    if not dry_run:
        state["last_synced"] = _now_iso()
        state["cumulative_new"] = int(state.get("cumulative_new") or 0) + summary["total_new"]
        _save_sync_state(state_path, state)
        summary["added_files"] = added_files
        summary["state_file"] = str(state_path)
    return summary


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m apps.cve_sync",
        description="Dragon-V CVE 自動同步管線（NVD API 2.0 -> 離線 YAML 武器庫）",
    )
    parser.add_argument(
        "--keywords",
        default="",
        help="逗號分隔關鍵字（例如 comfyui,ollama）；省略時使用 fingerprints 提取 + 內建清單",
    )
    parser.add_argument("--max-per-keyword", type=int, default=20, help="每個關鍵字最多新增的 CVE 數（預設 20）")
    parser.add_argument("--dry-run", action="store_true", help="只統計不寫檔、不更新狀態")
    parser.add_argument("--data-dir", default="", help="覆寫資料目錄（預設 dragon_v/data）")
    parser.add_argument("--list-keywords", action="store_true", help="列出自動提取的關鍵字後離開")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir) if args.data_dir else None
    if args.list_keywords:
        for keyword in default_keywords(data_dir):
            print(keyword)
        return 0

    result = sync_cves(
        args.keywords or None,
        max_per_keyword=args.max_per_keyword,
        dry_run=args.dry_run,
        data_dir=data_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
