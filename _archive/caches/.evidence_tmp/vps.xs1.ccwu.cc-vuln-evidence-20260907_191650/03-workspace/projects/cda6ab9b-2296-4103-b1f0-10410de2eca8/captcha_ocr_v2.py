#!/usr/bin/env python3
"""Test ddddocr with beta/old models on 20 captcha samples."""
import requests, urllib3, io, json, sys, os
from PIL import Image
import ddddocr
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "http://35.234.50.28:3400/captcha"
OUTDIR = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-4103-b1f0-10410de2eca8/captcha_samples"
OUTDIR = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_samples"

# Test multiple ddddocr configs
configs = [
    ("default", ddddocr.DdddOcr(show_ad=False)),
    ("beta",    ddddocr.DdddOcr(show_ad=False, beta=True)),
    ("old",     ddddocr.DdddOcr(show_ad=False, old=True)),
]

for name, ocr in configs:
    print(f"\n===== {name} =====")
    for i in range(20):
        img_bytes = open(f"{OUTDIR}/c_{i:02d}.gif", 'rb').read()
        # Convert GIF to PNG since ddddocr may prefer PNG
        try:
            img = Image.open(io.BytesIO(img_bytes))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png_bytes = buf.getvalue()
            pred = ocr.classification(png_bytes)
        except Exception as e:
            pred = f"ERR:{e}"
        print(f"  [{i:02d}] -> {pred}")