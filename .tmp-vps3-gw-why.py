from pathlib import Path
import subprocess

home = Path(r"C:\Users\Administrator\AppData\Local\hermes")
for name in ("gateway.restart.log", "gateway.log", "logs/gateway.log"):
    p = home / name
    print("===", name, p.exists(), p.stat().st_size if p.exists() else 0)
    if p.exists():
        data = p.read_bytes()[-1500:]
        print(data.decode("utf-8", "replace")[-800:])

# find recent logs
logs = sorted(home.rglob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
print("=== recent logs ===")
for p in logs:
    print(int(p.stat().st_mtime), p.stat().st_size, str(p)[-80:])

q = subprocess.run(["schtasks", "/Query", "/TN", "Hermes_Gateway", "/XML"], capture_output=True, text=True, encoding="utf-8", errors="replace")
xml = q.stdout or ""
print("xml-len", len(xml), "rc", q.returncode)
for tag in ("Command", "Arguments", "WorkingDirectory"):
    if tag in xml:
        i = xml.find(tag)
        print(xml[max(0, i - 20): i + 180].encode("ascii", "replace").decode("ascii"))
