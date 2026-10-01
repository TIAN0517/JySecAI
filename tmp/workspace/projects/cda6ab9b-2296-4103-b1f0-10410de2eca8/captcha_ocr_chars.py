#!/usr/bin/env python3
"""OCR each char individually after cropping."""
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import sys

img = Image.open('/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_sportal.gif').convert('RGB')
print(f"Image size: {img.size}")

# Crop 4 char regions + a bit of padding
regions = [
    (0, 0, 22, 38),   # char 1
    (28, 0, 52, 38),  # char 2
    (56, 0, 78, 38),  # char 3
    (83, 0, 116, 38), # char 4
]

results = []
for idx, (x0, y0, x1, y1) in enumerate(regions):
    crop = img.crop((x0, y0, x1, y1))
    # Upscale 8x
    crop_big = crop.resize((crop.size[0] * 8, crop.size[1] * 8), Image.LANCZOS)
    gray = crop_big.convert('L')
    # Auto contrast + sharpen
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
    gray.save(f'/tmp/char_{idx}.png')

    # OCR
    for psm in [10, 8, 7, 13]:
        for wl in ['', '-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']:
            txt = pytesseract.image_to_string(gray, config=f'--psm {psm} {wl}').strip()
            if txt:
                print(f"  char{idx+1} (col{x0}-{x1}) psm{psm} wl={'yes' if wl else 'no'}: '{txt}'")
                results.append((idx+1, psm, wl, txt))

# Show most common
from collections import Counter
c = Counter([r[3] for r in results])
print("\nMost common:")
for txt, cnt in c.most_common(10):
    print(f"  '{txt}': {cnt}")