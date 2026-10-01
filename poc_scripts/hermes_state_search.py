# -*- coding: utf-8 -*-
"""Search hermes WSL state DBs for the record where the agent recommended DNS-scan tools
/ recommended buying ZoomEye. Dumps matches to a UTF-8 report file."""
import sqlite3, json, os

DBS = [
    "/home/bossjy/.hermes/state.db",
    "/home/bossjy/.hermes/kanban.db",
    "/home/bossjy/.hermes/shared-state.db",
]
KEYWORDS = [
    "zoomeye", "推薦", "購買", "方案", "subfinder", "dnsx", "amass", "massdns",
    "fierce", "dnsrecon", "掃描工具", "dns 掃描", "api-key", "apikey", "personal",
    "fofa", "censys", "shodan",
]
OUT = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/state_search.txt"

fh = open(OUT, "w", encoding="utf-8")
def emit(*a):
    print(*a, file=fh)

for db in DBS:
    if not os.path.exists(db):
        emit("MISSING", db); continue
    emit("=" * 80)
    emit("DB:", db, "size:", os.path.getsize(db))
    try:
        c = sqlite3.connect(db)
    except Exception as e:
        emit("open-fail", e); continue
    tables = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    emit("tables:", tables)
    for t in tables:
        if "fts" in t or t.startswith("sqlite_"):
            continue
        try:
            cols = [r[1] for r in c.execute("pragma table_info(%s)" % t)]
        except Exception:
            continue
        for col in cols:
            for kw in KEYWORDS:
                try:
                    rows = c.execute(
                        "select rowid, %s from %s where lower(cast(%s as text)) like ? limit 4"
                        % (col, t, col),
                        ("%" + kw.lower() + "%",),
                    ).fetchall()
                except Exception:
                    break
                for rid, val in rows:
                    s = str(val)
                    if len(s) < 10:
                        continue
                    i = s.lower().find(kw.lower())
                    emit("\n--- kw=%s table=%s col=%s rowid=%s len=%d" % (kw, t, col, rid, len(s)))
                    emit(s[max(0, i - 1500): i + 3500])
fh.close()
print("written", OUT)
