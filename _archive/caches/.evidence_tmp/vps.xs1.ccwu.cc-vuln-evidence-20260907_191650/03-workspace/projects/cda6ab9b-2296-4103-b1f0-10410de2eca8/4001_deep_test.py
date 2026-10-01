import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 深入测试 4001 /events
print('=== 4001 /events 深入测试 ===')

# 1. 获取完整的事件数据结构
print('1. GET /events (full response)...')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
conn.request('GET', '/events')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Content-Type: {resp.getheader("Content-Type")}')
print(f'  Data length: {len(data)} bytes')

# 解析 JSON
try:
    events = json.loads(data)
    print(f'  Total events: {len(events)}')

    # 显示前 3 个事件的完整结构
    print('\n2. First 3 events (full structure):')
    for i, event in enumerate(events[:3]):
        print(f'  Event {i+1}:')
        for key, value in event.items():
            print(f'    {key}: {value}')
        print()

    # 显示所有唯一的字段名
    print('3. All unique field names:')
    all_fields = set()
    for event in events:
        all_fields.update(event.keys())
    for field in sorted(all_fields):
        print(f'  - {field}')

    # 统计字段出现频率
    print('\n4. Field frequency:')
    field_count = {}
    for event in events:
        for key in event.keys():
            field_count[key] = field_count.get(key, 0) + 1
    for field, count in sorted(field_count.items(), key=lambda x: x[1], reverse=True):
        print(f'  {field}: {count}/{len(events)}')

    # 显示 CaseID 的唯一值
    print('\n5. Unique CaseID values:')
    case_ids = set(event.get('CaseID') for event in events if 'CaseID' in event)
    print(f'  Total unique CaseIDs: {len(case_ids)}')
    for case_id in list(case_ids)[:10]:
        print(f'  - {case_id}')

    # 显示时间范围
    print('\n6. Time range:')
    timestamps = [event.get('CreatedAt') or event.get('createdAt') or event.get('timestamp') for event in events]
    timestamps = [t for t in timestamps if t]
    if timestamps:
        print(f'  Min: {min(timestamps)}')
        print(f'  Max: {max(timestamps)}')

except json.JSONDecodeError as e:
    print(f'  JSON decode error: {e}')
    print(f'  Raw data: {data[:500]}')

conn.close()

# 2. 测试特定 CaseID 的查询
print('\n7. Testing specific CaseID query...')
# 使用之前发现的 CaseID
test_case_ids = ['180717152801fed7', 'Test180805142701', 'test-case-123', '1', '2', '3', '123', '456', '789', '000']

for case_id in test_case_ids:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
    conn.request('GET', f'/events?CaseID={case_id}')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  CaseID={case_id}: {resp.status} ({len(data)} bytes)')
    if resp.status == 200 and len(data) > 10:
        try:
            events = json.loads(data)
            print(f'    Events: {len(events)}')
            if events:
                print(f'    First event: {json.dumps(events[0], indent=2)[:300]}')
        except json.JSONDecodeError:
            print(f'    Data: {data[:200]}')
    conn.close()

# 3. 测试其他查询参数
print('\n8. Testing other query parameters...')
params = [
    'CaseID=180717152801fed7&TypeOfEventTxt=Test',
    'CaseID=180717152801fed7&Unit=1',
    'CaseID=180717152801fed7&Systolic=120',
    'CaseID=180717152801fed7&Diastolic=80',
    'CaseID=180717152801fed7&Mean=93',
    'recordUuid=Test180805142701',
    'CaseID=180717152801fed7&recordUuid=Test180805142701',
]

for param in params:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
    conn.request('GET', f'/events?{param}')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  /events?{param}')
    print(f'    Status: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        try:
            events = json.loads(data)
            print(f'    Events: {len(events)}')
        except json.JSONDecodeError:
            print(f'    Data: {data[:200]}')
    conn.close()
