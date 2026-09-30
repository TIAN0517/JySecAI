import sys, os, json
sys.path.insert(0, '.')
from login import AutoLoginService119

bot = AutoLoginService119()
print("[*] Fetching cases via bot.fetch_cases()...")
cases = bot.fetch_cases()
if cases is None:
    print("  Result: None (API error)")
elif len(cases) == 0:
    print("  Result: [] (no cases)")
else:
    print(f"  Result: {len(cases)} cases")
    for c in cases[:3]:
        print(f"  - status={c.get('caseStatus','?',)} time={c.get('inTime','')} addr={c.get('csPlace','')[:50]}")
    scene = [c for c in cases if "到現場" in (c.get("caseStatus","") or "")]
    print(f"  Scene cases (到現場): {len(scene)}")