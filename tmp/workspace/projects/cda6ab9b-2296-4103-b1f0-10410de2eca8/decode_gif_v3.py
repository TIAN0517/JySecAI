"""
GIF89a LZW decoder v3.
Key fix: GIF standard packs codes LSB-first within code, NOT MSB-first.
i.e. for code_size=5, bits[bp+0] is the LSB of the code, bits[bp+4] is the MSB.
"""
import struct

def read_sub_blocks(data, start):
    blocks = b''
    i = start
    while i < len(data):
        sz = data[i]
        i += 1
        if sz == 0:
            break
        blocks += data[i:i+sz]
        i += sz
    return blocks, i

def lzw_decode(min_code_size, compressed):
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    code_size = min_code_size + 1

    bits = []
    for b in compressed:
        for k in range(8):
            bits.append((b >> k) & 1)

    codes = []
    bp = 0
    while bp + code_size <= len(bits):
        # LSB-first: bits[bp] is LSB
        code = 0
        for k in range(code_size):
            code |= bits[bp + k] << k
        codes.append(code)
        bp += code_size

    table = {}
    for i in range(clear_code):
        table[i] = bytes([i])

    out = bytearray()
    prev = None
    codes_read = 0
    for code in codes:
        codes_read += 1
        if code == clear_code:
            table = {}
            for i in range(clear_code):
                table[i] = bytes([i])
            next_code = end_code + 1
            code_size = min_code_size + 1
            prev = None
            continue
        if code == end_code:
            print(f"End code at codes_read={codes_read}, output={len(out)} bytes")
            break

        if code in table:
            entry = table[code]
        elif code == next_code and prev is not None:
            entry = prev + bytes([prev[0]])
        else:
            raise Exception(f"Invalid code {code} (next={next_code}, prev={'None' if prev is None else 'set'}, codes_read={codes_read})")

        out.extend(entry)
        if prev is not None:
            table[next_code] = prev + bytes([entry[0]])
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        prev = entry
        if codes_read <= 30:
            print(f"  code #{codes_read}: code={code} (cs={code_size}) -> entry_len={len(entry)}, next_code now={next_code}")

    return bytes(out)


for fname in [
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess1.gif',
]:
    print(f"\n{'='*70}\n{fname}\n{'='*70}")
    with open(fname, 'rb') as f:
        data = f.read()

    lzw_min = data[0x47]
    compressed, end_i = read_sub_blocks(data, 0x48)
    print(f"LZW min: {lzw_min}")
    print(f"LZW compressed: {len(compressed)} bytes, end at 0x{end_i:x} = 0x{data[end_i]:02x}")

    try:
        pixels = lzw_decode(lzw_min, compressed)
        print(f"Decoded pixel bytes: {len(pixels)}")

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
            print(f"Not enough pixels: {len(pixels)} < {W*H}")
    except Exception as e:
        print(f"FAILED: {e}")