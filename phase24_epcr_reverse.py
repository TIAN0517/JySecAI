#!/usr/bin/env python3
"""
Phase 24: Reverse-engineer ALL 160 EPCR JS/HTML files.
Extract complete API surface, auth flows, data endpoints, real-time endpoints.
"""
import os, re, json, glob

LOGIN_PAGES_DIR = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/login_pages/'

# Collect all JS and HTML files
all_js = sorted(glob.glob(os.path.join(LOGIN_PAGES_DIR, 'epcr_js_*.js')))
all_html = sorted(glob.glob(os.path.join(LOGIN_PAGES_DIR, 'epcr_*.html')))

print(f"Found {len(all_js)} JS files and {len(all_html)} HTML files")
print(f"Total: {len(all_js) + len(all_html)} files")
print()

# Categories to extract
results = {
    'api_endpoints': {},       # url_path -> [files that reference it]
    'http_methods': {},        # (method, url) -> [files]
    'auth_flows': {},          # auth-related keywords -> [files]
    'data_entities': {},       # entity names -> [files]
    'realtime_endpoints': {},  # real-time/websocket endpoints
    'file_downloads': {},      # file download/upload endpoints
    'admin_endpoints': {},     # admin-only endpoints
    'vulnerable_patterns': {}, # potential vuln patterns
}

# Patterns to search for
patterns = {
    'http_calls': r'\$http\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    'url_strings': r'["\']([/][A-Za-z][A-Za-z0-9/_{}.:-]*[\?A-Za-z0-9/_{}.=&:-]*)["\']',
    'auth_keywords': r'(Bearer|Authorization|token|refreshToken|sessionId|ssoLogin|oauth|jwt|JWT|cookie|withCredentials)',
    'realtime': r'(socket\.io|websocket|ws:|wss:|rtmp://|WebRTC|video/stream|liveStream)',
    'file_ops': r'(getImage|getFile|getPdf|upload|download|file|File|image|video|audio)',
    'admin': r'(admin|administrator|root|superuser|manage|permission|role|auth)',
    'sql_vuln': r'(sql|query|filter|where|orderBy|sort|search|params|condition)',
    'id_or': r'(caseId|patientId|recordId|dispatchId|ambulanceId|emtId|branchId|hospitalId|userId)',
}

# Process each JS file
for js_file in all_js:
    fname = os.path.basename(js_file)
    with open(js_file, 'r', errors='replace') as f:
        content = f.read()
    
    # Extract HTTP calls
    for match in re.finditer(patterns['http_calls'], content):
        method = match.group(1).upper()
        url = match.group(2)
        key = f"{method} {url}"
        if key not in results['http_methods']:
            results['http_methods'][key] = []
        results['http_methods'][key].append(fname)
    
    # Extract all URL-like strings
    for match in re.finditer(patterns['url_strings'], content):
        url = match.group(1)
        # Skip bower_components and common paths
        if url.startswith('/bower') or url.startswith('/stylesheets') or url in ('/', '/js', '/css'):
            continue
        if len(url) > 120:
            continue
        if url not in results['api_endpoints']:
            results['api_endpoints'][url] = []
        results['api_endpoints'][url].append(fname)
    
    # Extract auth-related content
    for match in re.finditer(patterns['auth_keywords'], content, re.I):
        keyword = match.group(1).lower()
        if keyword not in results['auth_flows']:
            results['auth_flows'][keyword] = []
        results['auth_flows'][keyword].append(fname)
    
    # Extract data entity references
    for match in re.finditer(patterns['id_or'], content):
        entity = match.group(1)
        if entity not in results['data_entities']:
            results['data_entities'][entity] = []
        results['data_entities'][entity].append(fname)
    
    # Extract realtime
    for match in re.finditer(patterns['realtime'], content, re.I):
        rt = match.group(1)
        if rt not in results['realtime_endpoints']:
            results['realtime_endpoints'][rt] = []
        results['realtime_endpoints'][rt].append(fname)
    
    # Extract file operations
    for match in re.finditer(patterns['file_ops'], content, re.I):
        fo = match.group(1)
        if fo not in results['file_downloads']:
            results['file_downloads'][fo] = []
        results['file_downloads'][fo].append(fname)

# Also process HTML files for config data
for html_file in all_html:
    fname = os.path.basename(html_file)
    with open(html_file, 'r', errors='replace') as f:
        content = f.read()
    
    # Extract config constants
    for match in re.finditer(r"['\"]([A-Za-z]+)['\"]:\s*['\"]([^'\"]+)['\"]", content):
        key, val = match.group(1), match.group(2)
        if any(k in key.lower() for k in ['url', 'server', 'port', 'auth', 'config', 'key']):
            config_key = f"config.{key}"
            if config_key not in results['api_endpoints']:
                results['api_endpoints'][config_key] = []
            results['api_endpoints'][config_key].append(f"{fname}: {val}")

# Save comprehensive analysis
output_path = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_reverse_engineering.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Print summary
print("=== EPCR 完整逆向工程結果 ===\n")
print(f"HTTP 方法調用 ({len(results['http_methods'])} 個):")
for endpoint, files in sorted(results['http_methods'].items()):
    print(f"  {endpoint}  <- {', '.join(files[:3])}{'...' if len(files)>3 else ''}")

print(f"\n所有 URL/路徑 ({len(results['api_endpoints'])} 個):")
for url, files in sorted(results['api_endpoints'].items()):
    print(f"  {url}  <- {', '.join(set(files)[:2])}")

print(f"\nAuth 流程關鍵字 ({len(results['auth_flows'])} 個):")
for keyword, files in sorted(results['auth_flows'].items(), key=lambda x: -len(x[1])):
    print(f"  {keyword}: {len(files)} files")

print(f"\n數據實體 ({len(results['data_entities'])} 個):")
for entity, files in sorted(results['data_entities'].items(), key=lambda x: -len(x[1])):
    print(f"  {entity}: {len(files)} files")

print(f"\n即時/視訊端點 ({len(results['realtime_endpoints'])} 個):")
for rt, files in sorted(results['realtime_endpoints'].items(), key=lambda x: -len(x[1])):
    print(f"  {rt}: {len(files)} files")

print(f"\n文件操作 ({len(results['file_downloads'])} 個):")
for fo, files in sorted(results['file_downloads'].items(), key=lambda x: -len(x[1])):
    print(f"  {fo}: {len(files)} files")

print(f"\n結果已保存到: {output_path}")
