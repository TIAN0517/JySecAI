#!/usr/bin/env python3
"""Read SQLite vulnerabilities table, print recent/interesting rows."""
import sqlite3, sys, json

DB = "/mnt/c/Users/Administrator/Desktop/JySecAI/data/conversations.db"
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=== tables ===")
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(" ", r["name"])

print("\n=== vulnerabilities schema ===")
try:
    for r in cur.execute("PRAGMA table_info(vulnerabilities)"):
        print(f"  {r['name']:20s} {r['type']}")
except Exception as e:
    print("  err", e)

print("\n=== row count by status ===")
try:
    for r in cur.execute("SELECT status, COUNT(*) c FROM vulnerabilities GROUP BY status"):
        print(f"  {r['status']}: {r['c']}")
except Exception as e:
    print("  err", e)

print("\n=== severity breakdown ===")
try:
    for r in cur.execute("SELECT severity, COUNT(*) c FROM vulnerabilities GROUP BY severity"):
        print(f"  {r['severity']}: {r['c']}")
except Exception as e:
    print("  err", e)
con.close()
