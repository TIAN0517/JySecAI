import requests, urllib3, json, time
urllib3.disable_warnings()
S=requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
def try_socket(base, extra=""):
    print(f"\n===== socket.io @ {base}{extra} =====")
    try:
        # Engine.IO v3 long-poll handshake
        r=S.get(f"{base}/socket.io/?EIO=3&transport=polling{extra}",timeout=10,headers=UA)
        print(f"  handshake [{r.status_code}] :: {r.text[:120]!r}")
        sid=r.text[1:] if r.text.startswith("0{") else None
        if not sid:
            return
        # open namespaces: default (40) + guesses
        for ns in ["", "/epcr","/monitor","/dispatch","/vitalsign","/realtime"]:
            for ev in [[], ["connect"], ["newDispatch"], ["getDispatch"], ["subscribe"],
                       ["getRecords"], ["request","/DispatchRecords"]]:
                payload=f"40" if ns=="" else f"40\"{ns}\""
                if ev:
                    payload=f"42{json.dumps(ev)}"
                try:
                    rr=S.get(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}",timeout=6,headers=UA,
                             params=None)
                    post=S.post(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}",data=payload,timeout=6,headers=UA)
                    if post.text and post.text not in ("2",):
                        print(f"    ns={ns!r} ev={ev} -> {post.text[:150]!r}")
                except Exception as e: pass
            break
        # poll a few times to capture any server-push data
        for i in range(3):
            pr=S.get(f"{base}/socket.io/?EIO=3&transport=polling&sid={sid}",timeout=4,headers=UA)
            if pr.text and pr.text not in ("2",):
                print(f"    poll {i}: {pr.text[:200]!r}")
            time.sleep(0.5)
    except Exception as ex:
        print(f"  [ERR] {type(ex).__name__} {ex}")
for base in ["http://35.234.50.28:8000","http://35.234.50.28:3500","http://35.234.50.28:3100","http://118.163.107.93:4002"]:
    try_socket(base)
print("done")
