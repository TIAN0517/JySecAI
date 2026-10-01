# -*- coding: utf-8 -*-
"""Parse a zoomEye batch log into per-dork host lists."""
import re, sys, os

src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/zc.log"
outdir = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/zoomeye_results"
base = os.path.splitext(os.path.basename(src))[0]
out = os.path.join(outdir, "county_hosts_%s.txt" % base)

sec = None
sections = {}
counts = {}
for line in open(src, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    m = re.match(r"^### (.+?)\s+\[(.*)\]$", line)
    if m:
        sec = m.group(1)
        sections.setdefault(sec, set())
        continue
    m = re.match(r"^total:\s*(\d+)", line)
    if m and sec:
        counts[sec] = int(m.group(1))
        continue
    if sec is None:
        continue
    parts = line.split()
    if len(parts) >= 3 and re.match(r"^\d+\.\d+\.\d+\.\d+$", parts[0]):
        dom = parts[2]
        sections[sec].add((parts[0], parts[1], dom))

fh = open(out, "w", encoding="utf-8")
print("== 各縣市 119/EPCR ZoomEye 資產（%s）==" % os.path.basename(src), file=fh)
for sec, items in sections.items():
    print("\n" + "=" * 70, file=fh)
    print("### %s   (total=%s, 擷取=%d)" % (sec, counts.get(sec, 0), len(items)), file=fh)
    for ip, port, dom in sorted(items, key=lambda x: (x[2], x[1])):
        print("  %-18s %-6s %s" % (ip, port, dom), file=fh)
fh.close()
print("written", out)
