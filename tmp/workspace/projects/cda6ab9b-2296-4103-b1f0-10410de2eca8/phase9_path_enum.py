#!/usr/bin/env python3
"""Phase 9: :4001 vitalSignVideoServer 业务路径枚举
尝试 Loopback 标准 RESTful 路由: /users /cases /patients /hospitals /vehicles /crews /dispatches /pcrs /records /staff /doctors /nurses /paramedics /ambulances /dispatchers /vitalSigns /vitalSignsVideos /ePCRs
"""
import http.client, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

paths = [
    # 标准 Loopback 资源
    '/users', '/accounts', '/customers', '/members',
    # 医疗业务
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
    # 现有已知端点（对比）
    '/events', '/imageData', '/videoData', '/trendings',
    # 通用 API
    '/api/users', '/api/cases', '/api/patients', '/api/hospitals', '/api/vehicles',
    '/api/crews', '/api/dispatches', '/api/pcrs', '/api/records', '/api/staff',
    '/api/v1/users', '/api/v1/cases', '/api/v1/patients',
    # 配置
    '/config', '/version', '/api/config', '/api/version',
    # 健康
    '/health', '/healthz', '/ready', '/readyz', '/ping', '/pong',
    # 已存在的子路径
    '/socket.io/', '/socket.io/?EIO=4&transport=polling',
    # 其他
    '/favicon.ico', '/robots.txt', '/static/', '/assets/', '/public/',
    '/uploads/', '/files/', '/downloads/', '/documents/', '/images/',
    '/videos/', '/medias/', '/photos/',
    # 管理类
    '/admin', '/admin/users', '/admin/cases', '/admin/login',
    # 调试
    '/debug', '/test', '/internal', '/private',
    '/api/debug', '/api/test', '/api/internal', '/api/private',
]

cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=30)
print(f"{'path':<60s} {'status':<6s} {'size':<8s} notes")
print("="*120)
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
                    note = f'JSON list, {len(j)} items, first keys={list(j[0].keys()) if j else "-"}'
                elif isinstance(j, dict):
                    note = f'JSON dict, keys={list(j.keys())}'
            except:
                if b[:50].startswith(b'<!DOCTYPE') or b'<' in b[:5]:
                    note = 'HTML'
                elif b[:4] == b'GIF8':
                    note = 'GIF'
                elif b[:5] == b'%PDF-':
                    note = 'PDF'
                else:
                    note = f'bytes prefix={b[:30]!r}'
        elif r.status in (401, 403):
            note = 'auth required'
        elif r.status == 404:
            note = ''
        elif r.status == 400:
            note = 'bad request'
        elif r.status == 500:
            note = 'server error'
        else:
            note = ''
        print(f"{path:<60s} {r.status:<6d} {size:<8d} {note}")
    except Exception as e:
        print(f"{path:<60s} ERR  {type(e).__name__}: {e}")
cn.close()