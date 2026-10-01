import requests, urllib3, socket
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}

def dns(host):
    try:
        return socket.gethostbyname(host)
    except Exception as e:
        return f"ERR {e}"

print("===== DNS =====")
for h in ["mer2.tpf.gov.tw","mer2voip.tpf.gov.tw","cloud2.ntpc.gov.tw","epcr.tpf.gov.tw"]:
    print(f"  {h} => {dns(h)}")

print("\n===== SRS streaming mer2voip.tpf.gov.tw:30080 =====")
for p in ["/","/api/v1/version","/api/v1/info","/api/v1/streams","/stat.html","/index.html","/live","/live/","/streams"]:
    for scheme in ["https","http"]:
        try:
            r=S.get(f"{scheme}://mer2voip.tpf.gov.tw:30080{p}", timeout=8, headers=UA, allow_redirects=False)
            print(f"  [{r.status_code}] {scheme}://mer2voip:30080{p} :: {r.headers.get('server','?')[:20]} {r.text[:60]!r}")
            break
        except Exception as e:
            pass
    else:
        print(f"  [conn-fail] {scheme}://mer2voip:30080{p}")

print("\n===== Legacy MER (mer2.tpf.gov.tw) =====")
for port in [7000,80,443,4443,8443]:
    for scheme in ["https","http"]:
        try:
            r=S.get(f"{scheme}://mer2.tpf.gov.tw:{port}/", timeout=8, headers=UA, allow_redirects=False)
            print(f"  [{r.status_code}] {scheme}://mer2:{port}/ :: {r.headers.get('server','?')[:25]} {r.text[:80]!r}")
        except Exception:
            pass

print("\n===== cloud2.ntpc.gov.tw =====")
for port in [443,80,8443,4443,7000,8080]:
    for scheme in ["https","http"]:
        try:
            r=S.get(f"{scheme}://cloud2.ntpc.gov.tw:{port}/", timeout=8, headers=UA, allow_redirects=False)
            print(f"  [{r.status_code}] {scheme}://cloud2.ntpc:{port}/ :: {r.headers.get('server','?')[:25]} {r.text[:80]!r}")
        except Exception:
            pass
print("done")
