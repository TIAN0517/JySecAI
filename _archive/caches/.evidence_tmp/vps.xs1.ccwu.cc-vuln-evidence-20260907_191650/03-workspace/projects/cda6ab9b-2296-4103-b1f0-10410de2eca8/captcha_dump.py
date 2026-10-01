#!/usr/bin/env python3
"""Dump 20 captcha samples from GCP 3400 and run ddddocr on each."""
import requests, urllib3, io, json, sys
from PIL import Image
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "http://35.234.50.28:3400/captcha"
OUTDIR = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_samples"

import os
os.makedirs(OUTDIR, exist_ok=True)

# 20 samples
samples = []
for i in range(20):
    s = requests.Session()
    r = s.get(URL, timeout=10, verify=False)
    # Response is GIF89a image
    samples.append({
        "i": i,
        "status": r.status_code,
        "ct": r.headers.get('Content-Type'),
        "len": len(r.content),
        "cookies": dict(s.cookies),
    })
    fn = f"{OUTDIR}/c_{i:02d}.gif"
    open(fn, 'wb').write(r.content)
    print(f"  [{i:02d}] {r.status_code} {r.headers.get('Content-Type')} {len(r.content)}B cookies={dict(s.cookies)} -> {fn}")

# Run ddddocr with default model
try:
    import ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)
    print("\n===== ddddocr default model =====")
    preds = []
    for i in range(20):
        img = open(f"{OUTDIR}/c_{i:02d}.gif", 'rb').read()
        try:
            pred = ocr.classification(img)
        except Exception as e:
            pred = f"ERR:{e}"
        preds.append((i, pred))
        print(f"  [{i:02d}] -> {pred}")
    # Save predictions
    with open(f"{OUTDIR}/preds.json", "w") as f:
        json.dump([{"i": i, "pred": p} for i, p in preds], f)
except ImportError:
    print("[!] ddddocr not installed")
