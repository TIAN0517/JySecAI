#!/usr/bin/env python3
"""
Phase 9: Comprehensive subdomain carpet scan on all 119 dispatch domains.
Use subfinder + amass + FOFA API to find ALL subdomains.
"""
import subprocess, json, time, socket, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

domains = ["tfd.gov.tw", "119.gov.taipei", "tpf.gov.tw", "tfd.gov.tw"]
all_subs = set()

print("=" * 60)
print("SUBDOMAIN CARPET SCAN")
print("=" * 60)

# subfinder for each domain
for domain in ["tfd.gov.tw", "119.gov.taipei", "tpf.gov.tw"]:
    print(f"\n[*] subfinder -d {domain}")
    try:
        result = subprocess.run(
            ["subfinder", "-d", domain, "-silent", "-timeout", "10"],
            capture_output=True, text=True, timeout=60
        )
        subs = result.stdout.strip().split("\n") if result.stdout.strip() else []
        for s in subs:
            s = s.strip()
            if s and ("119" in s.lower() or "epcr" in s.lower() or "dispatch" in s.lower()
                      or "fire" in s.lower() or "ems" in s.lower() or "ambulance" in s.lower()
                      or "ohca" in s.lower() or "ohca" in s.lower() or "pcdt" in s.lower()
                      or "vitalsign" in s.lower() or "cer" in s.lower() or "csi" in s.lower()
                      or "mer" in s.lower() or "mci" in s.lower() or "monitor" in s.lower()
                      or "hospital" in s.lower() or "doctor" in s.lower()
                      or s.startswith("app") or s.startswith("admin") or s.startswith("login")
                      or s.startswith("portal") or s.startswith("web") or s.startswith("api")
                      or s.startswith("rtc") or s.startswith("turn") or s.startswith("gis")
                      or s.startswith("eoc") or s.startswith("safe") or s.startswith("check")
                      or s.startswith("report") or s.startswith("sport")
                      or s.startswith("epaper") or s.startswith("mer") or s.startswith("t.")
                      or s.startswith("e.") or s.startswith("co.") or s.startswith("e.")
                      or "taipei" in s.lower() or "tperf" in s.lower()):
                all_subs.add(s)
                print(f"  [+] {s}")
        print(f"  Found {len(subs)} total for {domain}")
    except Exception as e:
        print(f"  [ERR] {e}")

# amass for each domain
for domain in ["tfd.gov.tw", "119.gov.taipei", "tpf.gov.tw"]:
    print(f"\n[*] amass enum -d {domain}")
    try:
        result = subprocess.run(
            ["amass", "enum", "-d", domain, "-silent", "-timeout", "30"],
            capture_output=True, text=True, timeout=120
        )
        subs = result.stdout.strip().split("\n") if result.stdout.strip() else []
        for s in subs:
            s = s.strip()
            if s:
                all_subs.add(s)
                print(f"  [+] {s}")
        print(f"  Found {len(subs)} from amass for {domain}")
    except Exception as e:
        print(f"  [ERR] {e}")

print(f"\n[*] Total unique 119-related subdomains: {len(all_subs)}")
for s in sorted(all_subs):
    print(f"  {s}")

output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_subdomains_{int(time.time())}.txt"
with open(output_file, "w") as f:
    for s in sorted(all_subs):
        f.write(s + "\n")
print(f"\n[*] Saved to: {output_file}")
