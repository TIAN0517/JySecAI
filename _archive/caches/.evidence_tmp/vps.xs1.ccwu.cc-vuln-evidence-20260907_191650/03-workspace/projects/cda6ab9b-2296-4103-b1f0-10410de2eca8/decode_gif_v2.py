"""
Decode GIF89a with proper sub-block parsing.
Start reading from the LZW min code size byte (offset 0x47),
then call read_sub_blocks from 0x48 (first sub-block size byte).
"""
import struct

def read_sub_blocks(data, start):
    """Read concatenated sub-block data from a GIF starting at the size byte."""
    blocks = b''
    i = start
    while True:
        if i >= len(data):
            break
        sz = data[i]
        i += 1
        if sz == 0:
            break
        blocks += data[i:i+sz]
        i += sz
    return blocks, i

def lzw_decode(min_code_size, compressed):
    """GIF LZW decompress - standard GIF89a algorithm."""
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    code_size = min_code_size + 1

    # Convert bytes to bit list (LSB-first within each byte)
    bits = []
    for b in compressed:
        for k in range(8):
            bits.append((b >> k) & 1)

    # Read codes MSB-first across bits
    codes = []
    bp = 0
    while bp + code_size <= len(bits):
        code = 0
        for k in range(code_size):
            code = (code << 1) | bits[bp + k]
        codes.append(code)
        bp += code_size

    # Initialize table: 0..clear_code-1 are bytes, clear_code and end_code are markers
    table = {}
    for i in range(clear_code):
        table[i] = bytes([i])
    # No entry for clear_code/end_code

    out = bytearray()
    prev = None
    for code in codes:
        if code == clear_code:
            # Reset
            table = {}
            for i in range(clear_code):
                table[i] = bytes([i])
            next_code = end_code + 1
            code_size = min_code_size + 1
            prev = None
            continue
        if code == end_code:
            break

        if code in table:
            entry = table[code]
        elif code == next_code and prev is not None:
            entry = prev + bytes([prev[0]])
        else:
            raise Exception(f"Invalid code {code} (next={next_code}, prev={'None' if prev is None else '...'})")

        out.extend(entry)
        if prev is not None:
            table[next_code] = prev + bytes([entry[0]])
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        prev = entry

    return bytes(out)


for fname in [
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess1.gif',
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess2.gif',
]:
    print(f"\n{'='*70}\n{fname}\n{'='*70}")
    with open(fname, 'rb') as f:
        data = f.read()

    # header 13 + GCT 48 = 61 = 0x3d
    # 0x3d: 0x2c Image Descriptor (9 bytes)
    # 0x47: LZW min code size
    # 0x48: first sub-block size byte
    lzw_min = data[0x47]
    compressed, end_i = read_sub_blocks(data, 0x48)
    print(f"LZW min: {lzw_min}")
    print(f"LZW compressed: {len(compressed)} bytes")
    print(f"End at offset 0x{end_i:x}, byte: 0x{data[end_i]:02x} (expected 0x3b trailer)")

    pixels = lzw_decode(lzw_min, compressed)
    print(f"Decoded pixel bytes: {len(pixels)}")
    print(f"Expected: 200*70 = {200*70}")

    # Render as ASCII
    W, H = 200, 70
    if len(pixels) >= W * H:
        print(f"\nASCII rendering (white=space, dark=#):")
        for y in range(H):
            row = ''
            for x in range(W):
                idx = pixels[y * W + x]
                row += ' ' if idx == 15 else '#'
            print(row)
    else:
        print(f"Not enough pixels decoded ({len(pixels)} < {W*H})")