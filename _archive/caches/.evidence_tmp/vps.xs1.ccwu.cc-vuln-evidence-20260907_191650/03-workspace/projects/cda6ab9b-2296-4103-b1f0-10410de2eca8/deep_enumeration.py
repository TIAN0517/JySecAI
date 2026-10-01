import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 深度枚举 4000-4008 和 9000 端口
print('=== 深度端点枚举 ===')

# 常见 API 端点
api_endpoints = [
    # 4000 - epcrServer
    ('4000', '/api/cases', 'GET'),
    ('4000', '/api/patients', 'GET'),
    ('4000', '/api/dispatch', 'GET'),
    ('4000', '/api/ambulances', 'GET'),
    ('4000', '/api/hospitals', 'GET'),
    ('4000', '/api/doctors', 'GET'),
    ('4000', '/api/monitor', 'GET'),
    ('4000', '/api/vitals', 'GET'),
    ('4000', '/api/videos', 'GET'),
    ('4000', '/api/events', 'GET'),
    ('4000', '/cases', 'GET'),
    ('4000', '/patients', 'GET'),
    ('4000', '/dispatch', 'GET'),
    ('4000', '/ambulances', 'GET'),
    ('4000', '/hospitals', 'GET'),
    ('4000', '/doctors', 'GET'),
    ('4000', '/monitor', 'GET'),
    ('4000', '/vitals', 'GET'),
    ('4000', '/videos', 'GET'),
    ('4000', '/events', 'GET'),
    ('4000', '/api/v1/cases', 'GET'),
    ('4000', '/api/v1/patients', 'GET'),

    # 4001 - vitalSignVideoServer
    ('4001', '/events', 'GET'),
    ('4001', '/events/test', 'GET'),
    ('4001', '/videos', 'GET'),
    ('4001', '/videos/test', 'GET'),
    ('4001', '/vitals', 'GET'),
    ('4001', '/vitals/test', 'GET'),
    ('4001', '/api/events', 'GET'),
    ('4001', '/api/videos', 'GET'),
    ('4001', '/api/vitals', 'GET'),

    # 4002 - hospitalServer
    ('4002', '/hospitals', 'GET'),
    ('4002', '/hospitals/test', 'GET'),
    ('4002', '/api/hospitals', 'GET'),
    ('4002', '/api/v1/hospitals', 'GET'),
    ('4002', '/wards', 'GET'),
    ('4002', '/rooms', 'GET'),
    ('4002', '/beds', 'GET'),

    # 4003 - doctorServer
    ('4003', '/doctors', 'GET'),
    ('4003', '/doctors/test', 'GET'),
    ('4003', '/api/doctors', 'GET'),
    ('4003', '/api/v1/doctors', 'GET'),
    ('4003', '/specialties', 'GET'),
    ('4003', '/schedules', 'GET'),

    # 4004 - authServer
    ('4004', '/login', 'POST'),
    ('4004', '/logout', 'POST'),
    ('4004', '/refreshToken', 'POST'),
    ('4004', '/ssoLogin', 'POST'),
    ('4004', '/captcha', 'GET'),
    ('4004', '/users', 'GET'),
    ('4004', '/users/me', 'GET'),
    ('4004', '/api/login', 'POST'),
    ('4004', '/api/users', 'GET'),

    # 4005 - monitorServer
    ('4005', '/monitor', 'GET'),
    ('4005', '/monitor/test', 'GET'),
    ('4005', '/api/monitor', 'GET'),
    ('4005', '/api/v1/monitor', 'GET'),
    ('4005', '/alerts', 'GET'),
    ('4005', '/notifications', 'GET'),

    # 4006 - merBridge
    ('4006', '/bridge', 'GET'),
    ('4006', '/bridge/test', 'GET'),
    ('4006', '/api/bridge', 'GET'),
    ('4006', '/api/v1/bridge', 'GET'),

    # 4007 - statServer
    ('4007', '/stats', 'GET'),
    ('4007', '/stats/test', 'GET'),
    ('4007', '/api/stats', 'GET'),
    ('4007', '/api/v1/stats', 'GET'),
    ('4007', '/reports', 'GET'),
    ('4007', '/analytics', 'GET'),

    # 4008 - mciServer
    ('4008', '/mci', 'GET'),
    ('4008', '/mci/test', 'GET'),
    ('4008', '/api/mci', 'GET'),
    ('4008', '/api/v1/mci', 'GET'),

    # 9000 - printServer
    ('9000', '/print', 'POST'),
    ('9000', '/print/test', 'POST'),
    ('9000', '/api/print', 'POST'),
    ('9000', '/api/v1/print', 'POST'),
    ('9000', '/jobs', 'GET'),
    ('9000', '/status', 'GET'),
]

# 测试每个端点
print('Testing endpoints...')
results = {}

for port, endpoint, method in api_endpoints:
    try:
        if port == '9000':
            # 9000 是 HTTP
            conn = http.client.HTTPConnection('epcr.tpf.gov.tw', int(port), timeout=5)
        else:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', int(port), timeout=5, context=ctx)

        if method == 'GET':
            conn.request(method, endpoint)
        else:
            headers = {'Content-Type': 'application/json'}
            body = '{}'
            conn.request(method, endpoint, body=body, headers=headers)

        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')

        # 记录非 404 的响应
        if resp.status != 404:
            if port not in results:
                results[port] = []
            results[port].append({
                'endpoint': endpoint,
                'method': method,
                'status': resp.status,
                'size': len(data),
                'content': data[:200] if len(data) > 200 else data
            })
            print(f'  [{resp.status}] {port}{endpoint} ({len(data)} bytes)')

        conn.close()

    except Exception as e:
        pass

# 输出详细结果
print('\n=== Detailed Results ===')
for port in sorted(results.keys()):
    print(f'\nPort {port}:')
    for result in results[port]:
        print(f'  {result["method"]} {result["endpoint"]}')
        print(f'    Status: {result["status"]}')
        print(f'    Size: {result["size"]} bytes')
        print(f'    Content: {result["content"]}')
        print()
