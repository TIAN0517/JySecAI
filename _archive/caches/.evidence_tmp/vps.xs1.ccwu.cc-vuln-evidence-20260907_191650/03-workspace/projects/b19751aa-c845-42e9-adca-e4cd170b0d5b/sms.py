import httpx, json
c=httpx.Client(verify=False,timeout=15)
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
P="886933333003"
r=c.post("https://ofa1777.ofa377.net/api/v2/sms/send",data=json.dumps({"phone_number":P}),headers=H)
print(r.status_code, r.text[:200])
