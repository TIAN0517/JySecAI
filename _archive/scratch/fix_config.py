#!/usr/bin/env python3
# Fix UTF-8 encoding issues in config.yaml
import sys

def fix_config(input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Check for BOM
    if data[:3] == b'\xef\xbb\xbf':
        print("Found UTF-8 BOM, removing it")
        data = data[3:]
    elif data[:2] == b'\xff\xfe':
        print("Found UTF-16 LE BOM, converting")
        # Convert UTF-16 LE to UTF-8
        import codecs
        data = codecs.BOM_UTF8 + data[2:].decode('utf-16-le').encode('utf-8')
    elif data[:2] == b'\xfe\xff':
        print("Found UTF-16 BE BOM, converting")
        import codecs
        data = codecs.BOM_UTF8 + data[2:].decode('utf-16-be').encode('utf-8')
    
    # Check for invalid UTF-8 leading bytes
    fixed = bytearray()
    i = 0
    errors = 0
    while i < len(data):
        b = data[i]
        if b >= 0x80:
            # Determine sequence length
            if b >= 0xF0 and b <= 0xF4:  # 4-byte
                if i + 3 < len(data):
                    trailing = all(data[i+j] & 0xC0 == 0x80 for j in range(1, 4))
                    if trailing:
                        # Check for overlong
                        c = ((b & 0x07) << 18) | ((data[i+1] & 0x3F) << 12) | ((data[i+2] & 0x3F) << 6) | (data[i+3] & 0x3F)
                        if c < 0x110000 and c >= 0x10000:
                            fixed.extend(data[i:i+4])
                            i += 4
                            continue
                errors += 1
                fixed.append(b)  # Keep as-is
                i += 1
            elif b >= 0xE0 and b <= 0xEF:  # 3-byte
                if i + 2 < len(data):
                    trailing = all(data[i+j] & 0xC0 == 0x80 for j in range(1, 3))
                    if trailing:
                        c = ((b & 0x0F) << 12) | ((data[i+1] & 0x3F) << 6) | (data[i+2] & 0x3F)
                        if c < 0x110000 and c >= 0x800:
                            fixed.extend(data[i:i+3])
                            i += 3
                            continue
                errors += 1
                fixed.append(b)
                i += 1
            elif b >= 0xC2 and b <= 0xDF:  # 2-byte
                if i + 1 < len(data) and data[i+1] & 0xC0 == 0x80:
                    c = ((b & 0x1F) << 6) | (data[i+1] & 0x3F)
                    if c < 0x110000 and c >= 0x80:
                        fixed.extend(data[i:i+2])
                        i += 2
                        continue
                errors += 1
                fixed.append(b)
                i += 1
            else:
                errors += 1
                fixed.append(b)
                i += 1
        else:
            fixed.append(b)
            i += 1
    
    print(f"Fixed {errors} encoding issues")
    print(f"Output size: {len(fixed)} bytes")
    
    with open(output_file, 'wb') as f:
        f.write(fixed)
    
    print(f"Wrote to {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_config.py <input> <output>")
        sys.exit(1)
    fix_config(sys.argv[1], sys.argv[2])