"""
Decode LZW stream from GIF to recover pixel data.
Strategy: walk the LZW code stream, decompress to a pixel array.
Then render as ASCII (white=space, dark=#).
"""
import struct

def read_sub_blocks(data, start):
    """Read concatenated sub-block data from a GIF starting at the size byte."""
    blocks = b''
    i = start
    while True:
        sz = data[i]
        i += 1
        if sz == 0:
            break
        blocks += data[i:i+sz]
        i += sz
    return blocks, i

def lzw_decode(min_code_size, compressed):
    """GIF LZW decompress."""
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    code_size = min_code_size + 1

    # Bit stream reader
    bits = []
    for b in compressed:
        for k in range(8):
            bits.append((b >> k) & 1)
    # Read codes MSB-first
    codes = []
    bp = 0
    while bp + code_size <= len(bits):
        code = 0
        for k in range(code_size):
            code = (code << 1) | bits[bp + k]
        codes.append(code)
        bp += code_size

    # Decode
    table = {}
    for i in range(clear_code):
        table[(i,)] = bytes([i])
    table[clear_code] = None
    table[end_code] = None

    out = bytearray()
    prev = None
    for code in codes:
        if code == clear_code:
            table = {}
            for i in range(clear_code):
                table[(i,)] = bytes([i])
            table[clear_code] = None
            table[end_code] = None
            next_code = end_code + 1
            code_size = min_code_size + 1
            prev = None
            continue
        if code == end_code:
            break

        if code in table and table[code] is not None:
            entry = table[code]
        elif code == next_code and prev is not None:
            entry = prev + bytes([prev[0]])
        else:
            raise Exception(f"Invalid code {code} (next={next_code})")

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

    # Skip header (13) + GCT (48) = 61. Then Image Descriptor is 9 bytes + 1 LZW min byte.
    # offset 0x3d = 0x2c (image desc start)
    i = 0x3d + 9 + 1  # 0x47
    compressed, end_i = read_sub_blocks(data, i)
    print(f"LZW compressed: {len(compressed)} bytes, ends at 0x{end_i:x}")

    pixels = lzw_decode(4, compressed)
    print(f"Decoded pixel bytes: {len(pixels)}")
    print(f"Expected: {200*70} = 14000")

    # Render as ASCII
    W, H = 200, 70
    print(f"\nASCII rendering (white=space, dark=#):")
    for y in range(H):
        row = ''
        for x in range(W):
            idx = pixels[y * W + x]
            if idx == 15:
                row += ' '  # white
            else:
                row += '#'  # dark (0-14 are all gray)
        print(row)