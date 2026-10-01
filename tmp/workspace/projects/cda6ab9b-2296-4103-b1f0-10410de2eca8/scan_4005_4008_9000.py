import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== 扫描 4005-4008 和 9000 端口 ===\n")

ports_to_scan = [4005, 4006, 4007, 4008, 9000]

for port in ports_to_scan:
    print(f"\n{'='*50}")
    print(f"Port {port}:")
    print(f"{'='*50}")
    
    # 1. 测试根路径
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=5, context=ctx)
        conn.request('GET', '/')
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        print(f"\n  GET / -> {resp.status}")
        print(f"  Body: {body[:200]}")
        conn.close()
    except Exception as e:
        print(f"\n  GET / -> Error: {str(e)[:80]}")
    
    # 2. 测试常见端点
    endpoints = [
        '/config',
        '/version',
        '/version/',
        '/api',
        '/api/',
        '/health',
        '/status',
        '/info',
        '/debug',
        '/metrics',
        '/socket.io/?EIO=4&transport=polling',
        '/events',
        '/events/',
        '/data',
        '/vitals',
        '/pcdt',
        '/cases',
        '/hospitals',
        '/doctors',
    ]
    
    for endpoint in endpoints:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=3, context=ctx)
            conn.request('GET', endpoint)
            resp = conn.getresponse()
            body = resp.read().decode('utf-8', errors='replace')
            status = resp.status
            conn.close()
            
            # 只显示非 404 的结果
            if status != 404:
                print(f"\n  GET {endpoint} -> {status}")
                if body:
                    print(f"  Body: {body[:150]}")
        except Exception as e:
            # 忽略连接错误
            pass
    
    # 3. 测试 POST 端点
    print(f"\n  POST 测试:")
    post_endpoints = [
        ('/login', '{"username":"admin","password":"admin"}'),
        ('/api/login', '{"username":"admin","password":"admin"}'),
        ('/auth/login', '{"username":"admin","password":"admin"}'),
    ]
    
    for endpoint, body in post_endpoints:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=3, context=ctx)
            conn.request('POST', endpoint, body=body, 
                        headers={'Content-Type': 'application/json'})
            resp = conn.getresponse()
            resp_body = resp.read().decode('utf-8', errors='replace')
            status = resp.status
            conn.close()
            
            if status != 404:
                print(f"  POST {endpoint} -> {status}")
                if resp_body:
                    print(f"  Body: {resp_body[:100]}")
        except Exception:
            pass
