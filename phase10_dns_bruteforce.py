#!/usr/bin/env python3
"""
Phase 10: DNS brute-force on tfd.gov.tw, tpf.gov.tw, 119.gov.taipei
Using the government subdomain dictionary from the attack-surface-recon skill.
Also resolve all subdomains found by subfinder.
"""
import subprocess, json, time, concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Subdomain prefixes from the government dictionary (relevant ones for 119)
prefixes = [
    "www", "service", "service119", "appservice119", "app119", "epcr",
    "epcrvoip", "mer2", "mer2voip", "mer", "mci", "monitor",
    "hospital", "doctor", "auth", "login", "admin",
    "portal", "api", "web", "ws", "app",
    "fire", "firefighting", "fireprotection", "firebusiness",
    "emergency", "dispatch", "ambulance", "ems",
    "ohca", "pcdt", "vitalsign", "vitalsignvideoserver",
    "csi", "cer", "ceri", "cpr",
    "rtc", "turnserver", "turn",
    "eoc", "eocr", "eocr2", "tdprc2",
    "safe", "safeap", "checkap", "checkapp",
    "report", "reports",
    "gis", "gis119", "119map", "map119",
    "taipeiepcr", "taipeiciiis", "taipeiciiis-dashboard", "taipeiciiis-dt",
    "smartems", "mntfd119web", "tqm", "tqm2", "tpesic",
    "inap", "ips", "message", "maintain",
    "dc", "ms2", "openfind", "ourap", "cva", "cpr",
    "tfd2dot", "tfms", "tpertc", "dptapp",
    "axuapweb", "rws", "srm",
    "119api", "119appapi", "119appcaseapi", "119appcasefile",
    "119epcrapi", "119firecaseapi", "119firecasefile",
    "119live", "119map", "119nfaapi", "119policetranapi",
    "119reort", "119verweb", "119websearch", "119web",
    "119webxuandao", "119webxuandao2", "119board",
    "af-search", "rfd119", "firesignal", "tpeusar",
    "camcall", "bnoc", "pnoc", "tfdus",
    "newebook", "newepaper", "epaper",
    "kemp2", "larzio", "sport", "sport-fire",
    "mailbox", "mail", "www1", "webmail",
    "co", "e", "t", "n",
    "ns1", "ns2", "mx", "mail", "smtp", "imap",
    "dev", "test", "staging", "uat", "demo", "old",
    "backup", "bak", "www1", "www2",
]

domains = ["tfd.gov.tw", "tpf.gov.tw", "119.gov.taipei", "tperf.gov.tw"]

print("=" * 60)
print("DNS BRUTE-FORCE CARPET SCAN")
print("=" * 60)

all_resolved = {}

def check_sub(domain, prefix):
    host = f"{prefix}.{domain}"
    try:
        result = subprocess.run(
            ["dig", "+short", host, "@8.8.8.8"],
            capture_output=True, text=True, timeout=5
        )
        ips = [ip.strip() for ip in result.stdout.strip().split("\n") if ip.strip() and not ip.startswith(";") and not ip.startswith("NOTE:")]
        if ips:
            return (host, ips)
    except:
        pass
    return None

results = {}
for domain in domains:
    print(f"\n[*] Domain: {domain}")
    domain_results = []
    
    # Use ThreadPoolExecutor for parallel DNS lookups
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_sub, domain, p) for p in prefixes]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                host, ips = result
                domain_results.append((host, ips))
                print(f"  [+] {host} -> {', '.join(ips)}")
    
    results[domain] = domain_results
    print(f"  Found {len(domain_results)} live subdomains for {domain}")

# Summary
print(f"\n{'=' * 60}")
print("ALL RESOLVED 119-RELATED HOSTS")
print("=" * 60)
total = 0
for domain, subs in results.items():
    print(f"\n{domain}:")
    for host, ips in subs:
        print(f"  {host} -> {', '.join(ips)}")
    total += len(subs)
print(f"\nTotal: {total} live hosts across {len(domains)} domains")

output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_dns_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Saved to: {output_file}")
