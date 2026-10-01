import requests, urllib3
urllib3.disable_warnings()
S=requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
eps=["/config","/version","/Relationships/","/PcrCategories/","/DiagramInjuries/",
"/BurnLevels/","/Statuses/","/DeathAssessments/","/Awarenesses/","/Breaths/","/Sexs/",
"/Ambulances/byUserRole","/Branches?disabled=false","/Hospitals","/json/hasTP.json",
"/json/isSimulation.json","/Pcrs/pcrCaseList","/DispatchRecords",
"/Statuses?code[$between][0]=10000&code[$between][1]=19999"]
for base in ["http://35.234.50.28:8000","http://118.163.107.93:4000"]:
    print(f"\n########## {base} (NO JWT) ##########")
    for e in eps:
        try:
            r=S.get(base+e,timeout=8,headers=UA)
            body=r.text[:70].replace("\n"," ")
            mark=" <<< DATA" if r.status_code==200 and len(r.text)>10 and r.text.strip() not in ("[]","{}") else ""
            print(f"  [{r.status_code}] {e} len={len(r.text)}{mark} :: {body!r}")
        except Exception as ex: print(f"  [ERR] {e} {ex}")
print("done")
