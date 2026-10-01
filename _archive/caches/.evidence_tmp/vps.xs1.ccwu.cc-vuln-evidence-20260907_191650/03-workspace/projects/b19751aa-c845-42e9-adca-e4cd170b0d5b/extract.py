import re, sys
s = open('/opt/CyberStrikeAI/tmp/workspace/projects/b19751aa-c845-42e9-adca-e4cd170b0d5b/bundle.js', encoding='utf-8', errors='replace').read()

def show(pattern, pre=60, post=500, maxn=12, label=None):
    print("\n####", label or pattern)
    n = 0
    for m in re.finditer(pattern, s):
        a = max(0, m.start()-pre)
        b = min(len(s), m.end()+post)
        print(s[a:b].replace('\n',' '))
        print("----")
        n += 1
        if n >= maxn: break

show(r'url:"/v2/register/', 60, 500, 8, "register")
show(r'url:"/v1/login"', 80, 260, 6, "login")
show(r'url:"/(v1|v2)/(forgot|sms/send|verify_email|contact|info|games)"', 30, 200, 12, "misc v1/v2")
# The Ot request helper & headers
show(r'Authorization', 120, 200, 8, "Authorization usage")
# request helper function that wraps baseURL /api
show(r'baseURL:"/api"', 200, 400, 4, "baseURL /api context")
# token storage keys
show(r'localStorage\.(get|set)Item\("([a-zA-Z]+)"\)', 20, 40, 40, "localStorage keys")
