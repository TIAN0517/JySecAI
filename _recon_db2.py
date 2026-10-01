#!/usr/bin/env python3
"""Pull the epcr.tpf.gov.tw vulns (all severities, open/confirmed) for the
14-critical summary + the 5 pending items. Print compact rows."""
import sqlite3

DB = "/mnt/c/Users/Administrator/Desktop/JySecAI/data/conversations.db"
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=== ALL critical rows (any status) ===")
for r in cur.execute("""
    SELECT id, severity, status, target, substr(title,1,90) AS title,
           substr(updated_at,1,16) AS upd
    FROM vulnerabilities
    WHERE severity='critical'
    ORDER BY updated_at DESC
"""):
    print(f"  [{r['id'][:8]}] {r['status']:10s} {r['target']:28s} {r['title']}  ({r['upd']})")

print("\n=== epcr.tpf.gov.tw rows, severity in (critical,high), status in (open,confirmed) ===")
for r in cur.execute("""
    SELECT id, severity, status, target, substr(title,1,80) AS title,
           substr(updated_at,1,16) AS upd
    FROM vulnerabilities
    WHERE target LIKE '%epcr%' AND severity IN ('critical','high')
      AND status IN ('open','confirmed')
    ORDER BY severity, updated_at DESC
"""):
    print(f"  [{r['id'][:8]}] {r['severity']:8s} {r['status']:10s} {r['target']:30s} {r['title']}  ({r['upd']})")

con.close()
