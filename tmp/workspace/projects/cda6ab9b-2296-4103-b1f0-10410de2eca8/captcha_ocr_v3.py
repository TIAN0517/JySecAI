#!/usr/bin/env python3
"""Inspect captcha GIF frames + better OCR."""
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract
import sys

paths = [
    '/tmp/captcha_test_1.gif',
    '/tmp/captcha_test_2.gif',
    '/tmp/captcha_test_3.gif',
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_sportal.gif',
]

for path in paths:
    print(f"\n===== {path} =====")
    img = Image.open(path)
    print(f"  size={img.size} mode={img.mode} format={img.format} n_frames={getattr(img, 'n_frames', 1)}")
    n = getattr(img, 'n_frames', 1)
    for fi in range(n):
        img.seek(fi)
        rgb = img.convert('RGB')
        rgb.save(f'/tmp/captcha_{path.split("/")[-1].replace(".gif","")}_f{fi}.png')

    # For each frame try multiple OCR variants
    for fi in range(min(n, 5)):
        img.seek(fi)
        rgb = img.convert('RGB')
        # Convert to grayscale + threshold
        gray = rgb.convert('L')
        # Auto-contrast
        ac = ImageOps.autocontrast(gray)
        # Sharp
        sharp = ac.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
        # Big
        big = sharp.resize((rgb.size[0] * 6, rgb.size[1] * 6), Image.LANCZOS)
        big.save(f'/tmp/big_{path.split("/")[-1].replace(".gif","")}_f{fi}.png')
        # OCR
        for psm in [6, 7, 8, 13]:
            txt = pytesseract.image_to_string(
                big,
                config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            ).strip()
            if txt and len(txt) >= 3:
                print(f"  frame{fi} psm{psm}: '{txt}'")