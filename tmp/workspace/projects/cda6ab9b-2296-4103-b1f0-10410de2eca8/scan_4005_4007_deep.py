import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== 深入扫描 4005 (MonitorServer) ===\n")

port = 4005
endpoints = [
    # 基于 MonitorServer 的业务端点
    '/monitor',
    '/monitor/',
    '/monitors',
    '/monitor/list',
    '/monitor/get',
    '/monitor/all',
    '/monitor/data',
    '/monitor/realtime',
    '/monitor/status',
    '/monitor/info',
    '/monitor/health',
    '/monitor/vitals',
    '/monitor/events',
    '/monitor/cases',
    '/monitor/pcdt',
    '/monitor/live',
    '/monitor/stream',
    '/monitor/video',
    '/monitor/map',
    '/monitor/location',
    '/monitor/units',
    '/monitor/ambulances',
    '/monitor/vehicles',
    '/monitor/drivers',
    '/monitor/paramedics',
    '/monitor/staff',
    '/monitor/users',
    '/monitor/roles',
    '/monitor/permissions',
    '/monitor/settings',
    '/monitor/config',
    '/monitor/logs',
    '/monitor/alerts',
    '/monitor/notifications',
    '/monitor/reports',
    '/monitor/statistics',
    '/monitor/analytics',
    '/monitor/metrics',
    '/monitor/performance',
    '/monitor/system',
    '/monitor/server',
    '/monitor/api',
    '/monitor/socket',
    '/monitor/realtime',
    '/monitor/realtime/data',
    '/monitor/realtime/status',
    '/monitor/realtime/vitals',
    '/monitor/realtime/events',
    '/monitor/realtime/cases',
    '/monitor/realtime/pcdt',
    '/monitor/realtime/live',
    '/monitor/realtime/stream',
    '/monitor/realtime/video',
    '/monitor/realtime/map',
    '/monitor/realtime/location',
    '/monitor/realtime/units',
    '/monitor/realtime/ambulances',
    '/monitor/realtime/vehicles',
]

print(f"Port {port} 业务端点测试:\n")

for endpoint in endpoints:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=3, context=ctx)
        conn.request('GET', endpoint)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        status = resp.status
        conn.close()
        
        if status != 401 and status != 404:
            print(f"  GET {endpoint} -> {status}")
            if body:
                print(f"  Body: {body[:200]}")
    except Exception as e:
        pass

print("\n\n=== 深入扫描 4007 (EPCRServer - 与 4000 相同架构) ===\n")

port = 4007
endpoints_4007 = [
    # 基于 4000 已知的端点
    '/events',
    '/events/',
    '/events/list',
    '/events/get',
    '/events/all',
    '/events/data',
    '/events/realtime',
    '/events/status',
    '/events/info',
    '/events/health',
    '/events/vitals',
    '/events/cases',
    '/events/pcdt',
    '/events/live',
    '/events/stream',
    '/events/video',
    '/events/map',
    '/events/location',
    '/events/units',
    '/events/ambulances',
    '/events/vehicles',
    '/events/drivers',
    '/events/paramedics',
    '/events/staff',
    '/events/users',
    '/events/roles',
    '/events/permissions',
    '/events/settings',
    '/events/config',
    '/events/logs',
    '/events/alerts',
    '/events/notifications',
    '/events/reports',
    '/events/statistics',
    '/events/analytics',
    '/events/metrics',
    '/events/performance',
    '/events/system',
    '/events/server',
    '/events/api',
    '/events/socket',
    '/events/realtime',
    '/events/realtime/data',
    '/events/realtime/status',
    '/events/realtime/vitals',
    '/events/realtime/events',
    '/events/realtime/cases',
    '/events/realtime/pcdt',
    '/events/realtime/live',
    '/events/realtime/stream',
    '/events/realtime/video',
    '/events/realtime/map',
    '/events/realtime/location',
    '/events/realtime/units',
    '/events/realtime/ambulances',
    '/events/realtime/vehicles',
    # 其他可能的端点
    '/cases',
    '/cases/',
    '/cases/list',
    '/cases/get',
    '/cases/all',
    '/cases/data',
    '/pcdt',
    '/pcdt/',
    '/pcdt/list',
    '/pcdt/get',
    '/pcdt/all',
    '/pcdt/data',
    '/hospitals',
    '/hospitals/',
    '/hospitals/list',
    '/hospitals/get',
    '/hospitals/all',
    '/hospitals/data',
    '/doctors',
    '/doctors/',
    '/doctors/list',
    '/doctors/get',
    '/doctors/all',
    '/doctors/data',
    '/patients',
    '/patients/',
    '/patients/list',
    '/patients/get',
    '/patients/all',
    '/patients/data',
    '/vitals',
    '/vitals/',
    '/vitals/list',
    '/vitals/get',
    '/vitals/all',
    '/vitals/data',
    '/videos',
    '/videos/',
    '/videos/list',
    '/videos/get',
    '/videos/all',
    '/videos/data',
    '/streams',
    '/streams/',
    '/streams/list',
    '/streams/get',
    '/streams/all',
    '/streams/data',
    '/live',
    '/live/',
    '/live/list',
    '/live/get',
    '/live/all',
    '/live/data',
    '/rtmp',
    '/rtmp/',
    '/rtmp/list',
    '/rtmp/get',
    '/rtmp/all',
    '/rtmp/data',
]

print(f"Port {port} 业务端点测试:\n")

for endpoint in endpoints_4007:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=3, context=ctx)
        conn.request('GET', endpoint)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        status = resp.status
        conn.close()
        
        if status != 401 and status != 404:
            print(f"  GET {endpoint} -> {status}")
            if body:
                print(f"  Body: {body[:200]}")
    except Exception as e:
        pass
