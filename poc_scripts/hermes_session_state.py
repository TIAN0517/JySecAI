# -*- coding: utf-8 -*-
"""Inspect one hermes session: resumability + last messages."""
import sqlite3, datetime, sys

SID = sys.argv[1] if len(sys.argv) > 1 else "20260924_164411_6ed7e1"
DB = "/home/bossjy/.hermes/state.db"
OUT = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/session_state_%s.txt" % SID

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
fh = open(OUT, "w", encoding="utf-8")
def emit(*a):
    print(*a, file=fh)

def ts(v):
    try:
        return datetime.datetime.fromtimestamp(float(v)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(v)

row = c.execute("select * from sessions where id=?", (SID,)).fetchone()
if row is None:
    emit("session not found:", SID)
else:
    d = dict(row)
    emit("=== sessions row ===")
    for k in ("id", "source", "display_name", "model", "parent_session_id", "message_count",
              "tool_call_count", "input_tokens", "output_tokens", "cwd", "end_reason",
              "archived", "git_branch", "estimated_cost_usd"):
        emit("  %-20s %s" % (k, d.get(k)))
    emit("  %-20s %s" % ("started_at", ts(d.get("started_at"))))
    emit("  %-20s %s" % ("ended_at", ts(d.get("ended_at")) if d.get("ended_at") else "(none — 未正式結束，可 resume)"))
    sp = d.get("system_prompt") or ""
    emit("  system_prompt len:", len(sp))
    emit("  system_prompt hash:", d.get("system_prompt_hash"))

cols = [r[1] for r in c.execute("pragma table_info(messages)")]
emit("\n=== messages columns ===")
emit(" ", cols)

emit("\n=== 最後 8 則訊息 ===")
order = "rowid"
qs = "select * from messages where session_id=? order by %s desc limit 8" % order
for r in c.execute(qs, (SID,)):
    d = dict(r)
    content = str(d.get("content", ""))
    emit("\n--- rowid=%s role=%s len=%d ts=%s" % (d.get("rowid"), d.get("role"), len(content), ts(d.get("created_at") or d.get("timestamp") or 0)))
    emit(content[:900])

emit("\n=== 訊息總數 ===")
emit(" ", c.execute("select count(*) from messages where session_id=?", (SID,)).fetchone()[0])
fh.close()
print("written", OUT)
