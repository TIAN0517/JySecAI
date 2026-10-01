#!/usr/bin/env python3
"""
Multi-source government EPCR asset discovery scanner.
Uses zoomeyeai CLI tool (verified working with Personal plan account).

Discovers EPCR/dispatch systems across Taiwan government domains.
"""
import json, time, os, subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Output paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_JSON = os.path.join(SCRIPT_DIR, "epcr_taiwan_gov_assets.json")
SUMMARY_JSON = os.path.join(SCRIPT_DIR, "epcr_discovery_summary.json")

QUERIES = [
    'app="EPCR" country="TW"',
    'title="EPCR" country="TW"',
    'port:4004 country="TW" title:"Auth"',
    'ssl.cert.subject.cn:"epcr*" country:"TW"',
    'ssl.cert.subject.cn:"119*" country:"TW"',
]

def zoomeye_cli_search(query, page=1, num=20):
    """Use zoomeyeai CLI to perform search."""
    try:
        cmd = ["zoomeyeai", "search", query, "--num", str(num), "--page", str(page)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"[-] CLI error for [{query} page={page}]: {result.stderr[:200]}")
            return []
        
        # Parse JSON output
        try:
            data = json.loads(result.stdout)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "list" in data:
                return data["list"]
            return []
        except json.JSONDecodeError as e:
            print(f"[-] JSON parse error: {e}")
            print(f"    Raw output: {result.stdout[:300]}")
            return []
            
    except subprocess.TimeoutExpired:
        print(f"[-] Timeout for [{query} page={page}]")
        return []
    except Exception as e:
        print(f"[-] Error for [{query}]: {e}")
        return []

def extract_assets(results):
    """Convert raw ZoomEye results to normalized assets."""
    assets = []
    for item in results:
        ip = item.get("ip", "")
        port = item.get("port", "")
        product = item.get("product", "")
        
        # Extract domains from SSL cert
        certs = item.get("cert", {})
        if isinstance(certs, str):
            try:
                certs = json.loads(certs)
            except:
                certs = {}
        
        subject = certs.get("subject", {}) if isinstance(certs, dict) else {}
        domains = subject.get("DNS", []) if isinstance(subject, dict) else []
        
        # Add CNAME domains
        cnames = item.get("cname", [])
        if isinstance(cnames, str):
            cnames = [cnames]
        
        all_domains = list(domains) + list(cnames)
        
        if not all_domains:
            # Fallback: use IP as identifier
            all_domains = [ip]
        
        for d in all_domains:
            if d and isinstance(d, str):
                assets.append({
                    "host": d.rstrip("."),
                    "ip": ip,
                    "port": port,
                    "product": product,
                    "ssl": bool(certs),
                    "query_source": "ZoomEye CLI",
                    "raw_data": item
                })
    return assets

def main():
    print("[*] Starting ZoomEye EPCR Scan via CLI...")
    print(f"[*] Queries: {len(QUERIES)} | Pages per query: 3")
    
    all_assets = []
    summary = {
        "scan_start": datetime.now().isoformat(),
        "queries": QUERIES,
        "total_results": 0,
        "total_assets": 0,
        "queries_performed": []
    }
    
    for q in QUERIES:
        query_assets = []
        for page in range(1, 4):
            results = zoomeye_cli_search(q, page=page, num=20)
            assets = extract_assets(results)
            query_assets.extend(assets)
            summary["total_results"] += len(results)
            
            print(f"[+] [{q}] Page {page} -> {len(assets)} assets")
            time.sleep(0.5)  # Rate limiting
        
        all_assets.extend(query_assets)
        summary["queries_performed"].append({
            "query": q,
            "assets_found": len(query_assets)
        })
        
    # Deduplicate by host
    seen = set()
    unique_assets = []
    for a in all_assets:
        key = a["host"]
        if key not in seen:
            seen.add(key)
            unique_assets.append(a)
    
    # Clean up raw data for final output
    for a in unique_assets:
        a.pop("raw_data", None)
    
    summary["scan_end"] = datetime.now().isoformat()
    summary["total_assets"] = len(unique_assets)
    
    # Save results
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(unique_assets, f, ensure_ascii=False, indent=2)
    
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n[✔] 發現 {len(unique_assets)} 個唯一 EPCR 相關資產")
    print(f"[✔] 結果已儲存至 {RESULTS_JSON}")
    print(f"[✔] 摘要資訊已儲存至 {SUMMARY_JSON}")
    
    # Print discovered hosts
    print("\n=== 發現的 EPCR 端點 ===")
    for a in unique_assets:
        print(f"  {a['host']} (IP: {a['ip']}, Port: {a.get('port', 'N/A')})")


if __name__ == "__main__":
    main()
