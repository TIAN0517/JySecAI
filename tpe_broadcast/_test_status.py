import sys, json
sys.path.insert(0, '.')
from login import AutoLoginService119

bot = AutoLoginService119()
cases = bot.fetch_cases()
if cases:
    print(f"Total cases: {len(cases)}")
    for c in cases:
        print(f"  status={c.get('caseStatus','')} time={c.get('inTime','')} addr={c.get('csPlace','')[:30]} cars={c.get('dispCarList','')[:30]}")
else:
    print("No cases")