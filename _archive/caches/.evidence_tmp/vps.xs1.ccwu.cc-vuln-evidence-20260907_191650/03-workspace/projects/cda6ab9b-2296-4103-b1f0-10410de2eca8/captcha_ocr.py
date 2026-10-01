#!/usr/bin/env python3
"""OCR captcha with multiple preprocessing techniques."""
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract
import sys

path = sys.argv[1]
img = Image.open(path)
print(f"Format: {img.format}, Mode: {img.mode}, Size: {img.size}")

# Convert to RGB then grayscale
img = img.convert('RGB')
gray = img.convert('L')
gray.save('/tmp/captcha_gray.png')

# Save as larger version for better OCR
big = gray.resize((img.size[0] * 3, img.size[1] * 3), Image.LANCZOS)
big.save('/tmp/captcha_big.png')

# Threshold (binarize)
thresh = gray.point(lambda x: 0 if x < 128 else 255, '1')
thresh.save('/tmp/captcha_thresh.png')

# Inverse (in case text is light)
inv = ImageOps.invert(gray)
inv.save('/tmp/captcha_inv.png')

# Multiple PSMs with whitelist
configs = [
    ('psm7_default', '--psm 7'),
    ('psm8_single', '--psm 8'),
    ('psm10_single', '--psm 10'),
    ('psm7_wl', '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
    ('psm8_wl', '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
]

variants = {
    'gray': gray,
    'big': big,
    'thresh': thresh,
    'inv': inv,
}

for vname, vimg in variants.items():
    for cname, cfg in configs:
        try:
            txt = pytesseract.image_to_string(vimg, config=cfg).strip()
            if txt:
                print(f"  {vname:10s} {cname:14s}: '{txt}'")
        except Exception as e:
            print(f"  {vname:10s} {cname:14s}: ERROR {e}")

# Try binarized with Otsu-like threshold (auto)
from PIL import ImageFilter
# Sharpen
sharp = gray.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
sharp_big = sharp.resize((img.size[0] * 4, img.size[1] * 4), Image.LANCZOS)
sharp_big.save('/tmp/captcha_sharp_big.png')

# Enhance contrast
enhancer = ImageEnhance.Contrast(gray)
contrast = enhancer.enhance(2.0)
contrast.save('/tmp/captcha_contrast.png')

# Try on sharpened
for cname, cfg in configs[:3]:
    try:
        txt = pytesseract.image_to_string(sharp_big, config=cfg).strip()
        if txt:
            print(f"  sharp_big   {cname:14s}: '{txt}'")
    except Exception as e:
        pass

# Try on contrast
for cname, cfg in configs[:3]:
    try:
        txt = pytesseract.image_to_string(contrast, config=cfg).strip()
        if txt:
            print(f"  contrast    {cname:14s}: '{txt}'")
    except Exception as e:
        pass
