#!/usr/bin/env python3
# Convert config.yaml from GBK to UTF-8

with open('config.yaml', 'rb') as f:
    data = f.read()

print(f"Original file size: {len(data)} bytes")

# Try to decode as GBK (common Windows Chinese encoding)
try:
    text = data.decode('gbk')
    print("Successfully decoded as GBK")
except Exception as e:
    print(f"Failed to decode as GBK: {e}")
    try:
        text = data.decode('gb18030')
        print("Successfully decoded as gb18030")
    except Exception as e2:
        print(f"Failed gb18030 too: {e2}")
        import sys
        sys.exit(1)

# Re-encode as UTF-8
utf8_data = text.encode('utf-8')
print(f"UTF-8 output size: {len(utf8_data)} bytes")

# Write the converted file (without BOM to be safe)
with open('config_fixed.yaml', 'wb') as f:
    f.write(utf8_data)

print("Wrote config_fixed.yaml")