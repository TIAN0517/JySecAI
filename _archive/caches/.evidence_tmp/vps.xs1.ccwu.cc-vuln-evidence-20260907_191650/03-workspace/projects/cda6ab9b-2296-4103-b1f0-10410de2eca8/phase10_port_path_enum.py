#!/usr/bin/env python3
"""Phase 10: 路径枚举扩展到 :4003 (doctorServer) 和 :4007 (statUrl)
确认其他端口的端点矩阵
"""
import http.client, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

paths = [
    # 标准 Loopback 资源
    '/users', '/accounts', '/customers', '/members',
    '/cases', '/case', '/caseList', '/patientCases',
    '/patients', '/patient', '/patientList',
    '/hospitals', '/hospital', '/hospitalList', '/hospitalCapabilities',
    '/vehicles', '/vehicle', '/vehicleList', '/ambulances', '/ambulance', '/ambulanceList',
    '/crews', '/crew', '/crewList',
    '/dispatches', '/dispatch', '/dispatchList', '/dispatchRecords',
    '/pcrs', '/pcr', '/pcrList', '/pcrRecords',
    '/records', '/record', '/recordList',
    '/staff', '/doctor', '/doctors', '/doctorList',
    '/nurses', '/nurse', '/nurseList',
    '/paramedics', '/paramedic', '/paramedicList',
    '/dispatchers', '/dispatcher', '/dispatcherList',
    # 已有端点
    '/events', '/imageData', '/videoData', '/trendings',
    # API
    '/api/users', '/api/cases', '/api/patients', '/api/hospitals', '/api/vehicles',
    '/api/crews', '/api/dispatches', '/api/pcrs', '/api/records', '/api/staff',
    '/api/v1/users', '/api/v1/cases', '/api/v1/patients',
    # 配置
    '/config', '/version', '/api/config', '/api/version', '/api/health',
    # 健康
    '/health', '/healthz', '/ready', '/readyz', '/ping', '/pong',
    # 静态资源
    '/js/app.js', '/js/AuthService.js', '/js/services.js',
    '/js/directives.js', '/js/controllers.js',
    # 公开目录
    '/static/', '/assets/', '/public/', '/uploads/', '/files/',
    '/downloads/', '/documents/', '/images/', '/videos/', '/medias/', '/photos/',
    '/favicon.ico', '/robots.txt',
    # socket.io
    '/socket.io/', '/socket.io/?EIO=4&transport=polling',
    # 管理
    '/admin', '/admin/users', '/admin/cases', '/admin/login',
    '/debug', '/test', '/internal', '/private',
    '/api/debug', '/api/test', '/api/internal', '/api/private',
]

for port in [4003, 4007]:
    print()
    print("="*120)
    print(f"Phase 10: port {port}")
    print("="*120)
    cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, context=ctx, timeout=15)
    for path in paths:
        try:
            cn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0'})
            r = cn.getresponse()
            b = r.read()
            size = len(b)
            note = ''
            if r.status == 200 and size > 0:
                try:
                    j = json.loads(b[:200])
                    if isinstance(j, list):
                        note = f'JSON list, {len(j)} items'
                    elif isinstance(j, dict):
                        note = f'JSON dict, keys={list(j.keys())}'
                except:
                    if b[:5] == b'<!DOC':
                        note = 'HTML'
                    elif b[:4] == b'GIF8':
                        note = 'GIF'
                    elif b[:2] == b'PK':
                        note = 'ZIP'
                    else:
                        note = f'bytes prefix={b[:30]!r}'
            print(f"{path:<60s} {r.status:<6d} {size:<8d} {note}")
        except Exception as e:
            print(f"{path:<60s} ERR  {type(e).__name__}: {e}")
    cn.close()