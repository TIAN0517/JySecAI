# -*- coding: utf-8 -*-
"""Find the record where the agent introduced DNS-scan tools / recommended buying ZoomEye.
Targeted SQL over hermes state.db messages."""
import sqlite3, os, sys

DB = "/home/bossjy/.hermes/state.db"
OUT = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/zoom_rec_recommendation.txt"

fh = open(OUT, "w", encoding="utf-8")
def emit(*a):
    print(*a, file=fh)

emit("DB size:", os.path.getsize(DB))
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
emit("tables:", [r[0] for r in c.execute("select name from sqlite_master where type='table'")])
for t in ("sessions", "messages"):
    emit("\n[%s] schema:" % t)
    for r in c.execute("pragma table_info(%s)" % t):
        emit("   ", tuple(r))

cols = [r[1] for r in c.execute("pragma table_info(messages)")]

emit("\n=== 訊息數 ===")
try:
    emit("messages:", c.execute("select count(*) from messages").fetchone()[0])
except Exception as e:
    emit("count fail", e)

QUERIES = [
    ("A 買+ZoomEye", "content like '%ZoomEye%' and (content like '%買%' or content like '%購買%')"),
    ("B 推薦+ZoomEye", "content like '%ZoomEye%' and content like '%推薦%'"),
    ("C 點數/方案/訂閱", "content like '%ZoomEye%' and (content like '%點數%' or content like '%方案%' or content like '%訂閱%' or content like '%付費%' or content like '%Personal%')"),
    ("D DNS 工具名", "content like '%subfinder%' or content like '%amass%' or content like '%dnsx%' or content like '%massdns%'"),
    ("E 掃描工具介紹", "content like '%掃描工具%' or content like '%子域名收集%' or content like '%子域名枚舉%'"),
]

for label, where in QUERIES:
    emit("\n" + "#" * 90)
    emit("### %s   WHERE %s" % (label, where))
    try:
        rows = c.execute(
            "select rowid, * from messages where %s order by rowid desc limit 8" % where
        ).fetchall()
    except Exception as e:
        emit("query-fail", e); continue
    emit("matched rows:", len(rows))
    for r in rows:
        d = dict(r)
        sid = d.get("session_id")
        role = d.get("role")
        content = str(d.get("content", ""))
        emit("\n--- rowid=%s session=%s role=%s len=%d ts=%s" % (d.get("rowid"), sid, role, len(content), d.get("created_at") or d.get("ts")))
        emit(content[:6000])

fh.close()
print("written", OUT)
