import http.client
import json
import ssl
import requests

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== 测试 RTMP 视频流 ===\n")

# 1. 从 4001 /events 获取最近的 recordUuid
print("1. 获取最近的 recordUuid...\n")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
    conn.request('GET', '/events?sort=desc&limit=10')
    resp = conn.getresponse()
    events = json.loads(resp.read())
    conn.close()
    
    if events:
        print("最近的 10 条事件:")
        for i, event in enumerate(events):
            uuid = event.get('recordUuid', 'N/A')
            case_id = event.get('CaseID', 'N/A')
            caption = event.get('Caption', 'N/A')
            timestamp = event.get('Timestamp', 'N/A')
            print(f"  [{i+1}] UUID: {uuid}")
            print(f"      CaseID: {case_id}")
            print(f"      Caption: {caption}")
            print(f"      Timestamp: {timestamp}")
            print()
except Exception as e:
    print(f"  Error: {str(e)}")
    # 使用默认 UUID
    events = [{'recordUuid': f'Test{i:03d}', 'CaseID': f'Case{i:03d}'} for i in range(10)]

# 2. 测试 RTMP 流
print("2. 测试 RTMP 流访问...\n")
base_url = "https://mer2voip.tpf.gov.tw:30080"
test_uuids = [event.get('recordUuid', f'Test{i:03d}') for i, event in enumerate(events[:5])]

for uuid in test_uuids:
    print(f"  测试 UUID: {uuid}")
    
    # 测试 HTTP 流
    http_url = f"{base_url}/live/{uuid}.flv"
    try:
        resp = requests.get(http_url, timeout=5, verify=False)
        print(f"    HTTP {http_url}")
        print(f"    Status: {resp.status_code}")
        print(f"    Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print(f"    Content-Length: {resp.headers.get('Content-Length', 'N/A')}")
        if resp.status_code == 200 and len(resp.content) > 0:
            print(f"    ✓ 流可访问! 大小: {len(resp.content)} bytes")
        else:
            print(f"    ✗ 流不可访问或为空")
        print()
    except Exception as e:
        print(f"    HTTP Error: {str(e)[:80]}")
        print()
    
    # 测试 RTMP 流
    rtmp_url = f"rtmp://mer2voip.tpf.gov.tw:30080/live/{uuid}"
    print(f"    RTMP {rtmp_url}")
    print("    (需要 RTMP 客户端测试)")
    print()

# 3. 测试常见的流媒体端点
print("3. 测试常见流媒体端点...\n")
stream_endpoints = [
    '/live',
    '/live/',
    '/live/list',
    '/live/get',
    '/live/all',
    '/live/data',
    '/live/streams',
    '/live/channels',
    '/live/uuids',
    '/live/cases',
    '/live/events',
    '/live/pcdt',
    '/live/vitals',
    '/live/videos',
    '/live/realtime',
    '/live/status',
    '/live/info',
    '/live/health',
    '/live/config',
    '/live/api',
    '/live/socket',
    '/live/websocket',
    '/live/polling',
]

for endpoint in stream_endpoints:
    try:
        conn = http.client.HTTPSConnection('mer2voip.tpf.gov.tw', 30080, timeout=3, context=ctx)
        conn.request('GET', endpoint)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        status = resp.status
        conn.close()
        
        if status != 404:
            print(f"  GET {endpoint} -> {status}")
            if body:
                print(f"  Body: {body[:150]}")
            print()
    except Exception as e:
        pass

# 4. 测试 HTTP 流媒体格式
print("4. 测试 HTTP 流媒体格式...\n")
formats = ['.flv', '.mp4', '.m3u8', '.ts', '.mp3', '.aac']
base_uuid = test_uuids[0] if test_uuids else 'Test001'

for fmt in formats:
    url = f"{base_url}/live/{base_uuid}{fmt}"
    try:
        resp = requests.get(url, timeout=3, verify=False)
        print(f"  GET {url}")
        print(f"    Status: {resp.status_code}")
        print(f"    Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print()
    except Exception as e:
        print(f"  GET {url}")
        print(f"    Error: {str(e)[:80]}")
        print()
