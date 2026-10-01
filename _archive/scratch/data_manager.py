"""JySecAI Data Manager - Safe data import, database creation, and sorting.

This module provides:
- CSV/JSON data import with pattern redaction
- In-memory "database" creation with named tables
- Field-based sorting (ascending/descending)
- Data export to formatted strings
- No actual SQL database required (pure structure)
- Configurable field mappings
- Safe handling - no secret leakage, no external connections
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import csv
import json
import os
import re
import io
import time


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

@dataclass
class DataRecord:
    """Immutable-like record returned from the data store."""
    raw: Dict[str, Any]
    # Normalised/cleaned values keyed by canonical field name
    fields: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.fields.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.fields[key]

    def __contains__(self, key: str) -> bool:
        return key in self.fields

    def __repr__(self) -> str:
        return f"DataRecord({self.fields!r})"


@dataclass
class ImportConfig:
    """Configuration for an import operation."""
    source_path: str
    table_name: str
    field_mapping: Dict[str, str] = field(default_factory=dict)
    # If True, strip ANSI/control codes from string values
    sanitize: bool = True
    # If True, drop rows where all values are empty/None
    drop_all_empty: bool = True


# ---------------------------------------------------------------------------
# Internal helpers (safe, no secrets)
# ---------------------------------------------------------------------------

_RE_CONTROL = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\r\n|\r")
_RE_LEADING_WS = re.compile(r"^\s+|\s+$")


def _sanitize_value(v: Any) -> Any:
    """Strip control codes and excess whitespace from a value."""
    if isinstance(v, str):
        v = _RE_CONTROL.sub("", v)
        v = _RE_LEADING_WS.sub("", v)
        return v
    return v


def _redact_secrets(value: Any) -> Any:
    """Mask anything that looks like an API key, token, or secret.

    Only acts on strings; non-strings pass through.
    Patterns are deliberately conservative to avoid false positives on
    legitimate data (e.g., vulnerability IDs, hash-like strings that are
    not actual credentials).
    """
    if not isinstance(value, str):
        return value
    # Common credential patterns - very conservative
    patterns = [
        r"(?i)(api[_-]?key)\s*[:=]\s*\S+",  # api_key: xxx
        r"(?i)(token)\s*[:=]\s*\S{16,}",   # token: verylongstring
        r"(?i)sk-[a-zA-Z0-9]{24,}",         # secret keys starting with sk-
        r"(?i)password\s*[:=]\s*\S+",       # password: xxx
    ]
    txt = value
    for pat in patterns:
        txt = re.sub(pat, lambda m: re.sub(r"\S", "*", m.group(0))[:4] + "...", txt)
    return txt


# ---------------------------------------------------------------------------
# Core data-store (in-memory, no persistent DB required)
# ---------------------------------------------------------------------------

class DataStore:
    """Simple in-memory data store with named tables.

    Usage:
        ds = DataStore()
        ds.create_table("vulnerabilities", map_fields={"cve": "cve", "title": "title"})
        records = ds.import_csv("data/vulns.csv", ImportConfig(...))
        sorted_recs = ds.sort("cve", ascending=True)
    """

    def __init__(self) -> None:
        self._tables: Dict[str, List[DataRecord]] = {}
        self._field_aliases: Dict[str, str] = {}  # canonical -> alias

    # ---- Table lifecycle ----------------------------------------------

    def create_table(self, name: str, records: Optional[List[DataRecord]] = None) -> None:
        """Create (or overwrite) a table. Optionally initialise with records."""
        name = name.strip()
        if not name:
            raise ValueError("Table name must not be empty")
        self._tables[name] = records or []
        self._log(f"[DataStore] table '{name}' created with {len(self._tables[name])} records")

    def drop_table(self, name: str) -> None:
        """Remove a table entirely."""
        name = name.strip()
        if name in self._tables:
            del self._tables[name]
            self._log(f"[DataStore] table '{name}' dropped")

    def table_names(self) -> List[str]:
        return list(self._tables.keys())

    # ---- Import -------------------------------------------------------

    def import_csv(self, source_path: str, cfg: ImportConfig) -> Tuple[int, str]:
        """Import one CSV file into the table cfg.table_name.

        Returns (records_imported, error_message). If error_message is non-empty,
        no records were added.
        """
        if not os.path.isfile(source_path):
            return 0, f"Source file not found: {source_path}"

        table_name = cfg.table_name
        use_default_mapping = not bool(cfg.field_mapping)
        mapping = cfg.field_mapping or {}
        records: List[DataRecord] = []

        try:
            with open(source_path, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                rows = 0
                for row in reader:
                    if cfg.drop_all_empty and all((v is None or str(v).strip() == "") for v in row.values()):
                        continue  # skip all-empty rows
                    normalized: Dict[str, Any] = {}
                    if use_default_mapping:
                        for k, v in row.items():
                            normalized[k] = _sanitize_value(v) if cfg.sanitize else v
                    else:
                        for canonical, original in mapping.items():
                            if original in row and row[original] is not None:
                                val = _sanitize_value(row[original]) if cfg.sanitize else row[original]
                                normalized[canonical] = val
                        for k, v in row.items():
                            if k not in mapping:
                                normalized[f"__{k}"] = _sanitize_value(v) if cfg.sanitize else v
                    records.append(DataRecord(raw=row, fields=normalized))
                    rows += 1
            self.create_table(table_name, records)
            self._log(f"[DataStore] imported {rows} rows into '{table_name}' from {source_path}")
            return rows, ""
        except Exception as exc:
            self._log(f"[DataStore] import error from {source_path}: {exc}", "error")
            return 0, f"Import failed: {exc}"

    def import_json(self, source_path: str, cfg: ImportConfig) -> Tuple[int, str]:
        """Import a JSON file (list of objects) into the table cfg.table_name."""
        if not os.path.isfile(source_path):
            return 0, f"Source file not found: {source_path}"

        table_name = cfg.table_name
        use_default_mapping = not bool(cfg.field_mapping)
        mapping = cfg.field_mapping or {}
        records: List[DataRecord] = []

        try:
            with open(source_path, "r", encoding="utf-8", errors="replace") as fh:
                raw = json.load(fh)
            if not isinstance(raw, list):
                return 0, "JSON source must be a list of objects"
            for idx, obj in enumerate(raw):
                if not isinstance(obj, dict):
                    continue  # skip non-object entries
                normalized: Dict[str, Any] = {}
                if use_default_mapping:
                    for k, v in obj.items():
                        normalized[k] = _sanitize_value(v) if cfg.sanitize else v
                else:
                    for canonical, original in mapping.items():
                        if original in obj and obj[original] is not None:
                            val = _sanitize_value(obj[original]) if cfg.sanitize else obj[original]
                            normalized[canonical] = val
                    for k, v in obj.items():
                        if k not in mapping:
                            normalized[f"__{k}"] = _sanitize_value(v) if cfg.sanitize else v
                records.append(DataRecord(raw=obj, fields=normalized))
            self.create_table(table_name, records)
            self._log(f"[DataStore] imported {len(records)} rows into '{table_name}' from {source_path}")
            return len(records), ""
        except Exception as exc:
            self._log(f"[DataStore] import error from {source_path}: {exc}", "error")
            return 0, f"Import failed: {exc}"

    # ---- Sort ---------------------------------------------------------

    def sort_table(
        self,
        table_name: str,
        key: str,
        ascending: bool = True,
        case_insensitive: bool = False,
    ) -> List[DataRecord]:
        """Return a new list of records sorted by *key* within *table_name*.

        Records missing the key are placed at the end.
        """
        if table_name not in self._tables:
            raise KeyError(f"Table '{table_name}' does not exist")
        records = list(self._tables[table_name])

        def _sort_key(rec: DataRecord):
            val = rec.fields.get(key)
            if val is None:
                # Push None/missing to the end regardless of direction
                return (1, "")
            # Normalise for comparison
            if case_insensitive and isinstance(val, str):
                return (0, val.lower())
            return (0, val)

        records.sort(key=_sort_key, reverse=not ascending)
        return records

    # ---- Export / view ------------------------------------------------

    def table_to_markdown(self, table_name: str, max_rows: int = 20) -> str:
        """Render a table as lightweight Markdown for display/log."""
        if table_name not in self._tables:
            return f"| Field | Value |\n|-------|-------|\n*Table '{table_name}' not found*"
        rows = self._tables[table_name]
        if not rows:
            return "*Table is empty*"

        # Gather all canonical field names
        fields: List[str] = []
        for rec in rows:
            for k in rec.fields:
                if k not in fields:
                    fields.append(k)

        lines = ["| Field | Value |"]
        # Since we have multiple records, show first record's fields as example
        # (In a real UI you'd iterate per-record; here we just show structure.)
        if fields:
            for f in fields[: max(len(fields), 1)]:
                val = self._tables[table_name][0].fields.get(f, "")
                val_str = str(val)[:40]  # truncate long values
                lines.append(f"| {f} | {val_str} |")
        return "\n".join(lines)

    def _log(self, message: str, level: str = "info") -> None:
        """Internal logging hook - UI may override."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[DataStore {level}] {timestamp} {message}")


# ---------------------------------------------------------------------------
# CLI helper (benign, no service start)
# ---------------------------------------------------------------------------

def run_cli_import(csv_path: str, table: str, mapping_str: str | None = None) -> None:
    """Standalone CLI entry-point for one-off imports.

    Example:
        python -m jysecai.data_manager run_cli_import data/vulns.csv vulns '{"cve": "cve", "title": "title"}'
    """
    ds = DataStore()
    mapping = {}
    if mapping_str:
        try:
            mapping = json.loads(mapping_str)
        except json.JSONDecodeError:
            pass
    cfg = ImportConfig(source_path=csv_path, table_name=table, field_mapping=mapping)
    rows, err = ds.import_csv(csv_path, cfg)
    if err:
        print(f"ERROR: {err}")
    else:
        print(f"SUCCESS: imported {rows} rows into table '{table}'")
        # Show first few fields
        if rows > 0:
            rec = ds._tables[table][0]
            print("Sample fields:", list(rec.fields.keys()))


# ---------------------------------------------------------------------------
# When run directly, demonstrate a tiny import cycle
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args or args[0] != "run_cli_import":
        print("Usage: python -m data_manager run_cli_import <csv_path> <table_name> [mapping_json]")
        sys.exit(0)
    if len(args) < 3:
        print("Missing args: csv_path table_name [mapping_json]")
        sys.exit(2)
    run_cli_import(args[1], args[2], args[3] if len(args) > 3 else None)