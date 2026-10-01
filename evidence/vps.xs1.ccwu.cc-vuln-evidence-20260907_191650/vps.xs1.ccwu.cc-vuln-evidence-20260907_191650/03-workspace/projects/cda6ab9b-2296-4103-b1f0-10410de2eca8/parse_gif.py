import struct
import sys

for fname in [
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess1.gif',
    '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess2.gif',
]:
    print(f"\n========== {fname} ==========")
    with open(fname, 'rb') as f:
        data = f.read()
    print(f"File size: {len(data)} bytes")

    sig = data[:6]
    print(f"Signature: {sig} ({sig.decode(errors='replace')})")

    w = struct.unpack('<H', data[6:8])[0]
    h = struct.unpack('<H', data[8:10])[0]
    packed = data[10]
    bg = data[11]
    ar = data[12]
    print(f"Width: {w}, Height: {h}")
    print(f"Packed byte: 0x{packed:02x} = {packed:08b}")
    print(f"  GCT Flag: {(packed >> 7) & 1}")
    print(f"  Color Res: {((packed >> 4) & 7) + 1} bits")
    print(f"  Sort: {(packed >> 3) & 1}")
    gct_size_n = packed & 7
    gct_n = 2 ** (gct_size_n + 1)
    print(f"  GCT Size N: {gct_size_n} -> {gct_n} colors")
    print(f"Background Color Index: {bg}")
    print(f"Pixel Aspect: {ar}")

    gct_bytes = 3 * gct_n
    print(f"\nGCT bytes: {gct_bytes}")
    gct = data[13:13+gct_bytes]
    print(f"GCT first 30 bytes: {gct[:30].hex()}")
    print(f"GCT last 6 bytes: {gct[-6:].hex()}")
    colors = [gct[i:i+3] for i in range(0, len(gct), 3)]
    print(f"Total colors: {len(colors)}")
    for ci, c in enumerate(colors):
        print(f"  Color {ci}: RGB=({c[0]:3d}, {c[1]:3d}, {c[2]:3d}) = 0x{c.hex()}")

    i = 13 + gct_bytes
    print(f"\nByte after GCT (offset 0x{i:02x}): 0x{data[i]:02x}")

    # Walk blocks
    blocks = []
    while i < len(data):
        b = data[i]
        if b == 0x2c:  # Image Descriptor
            i += 1
            l = struct.unpack('<H', data[i:i+2])[0]
            t = struct.unpack('<H', data[i+2:i+4])[0]
            iw = struct.unpack('<H', data[i+4:i+6])[0]
            ih = struct.unpack('<H', data[i+6:i+8])[0]
            p = data[i+8]
            lct_n = 2 ** ((p & 7) + 1) if (p & 0x80) else 0
            i += 9
            if lct_n > 0:
                i += lct_n * 3
            lzw_min = data[i]
            i += 1
            sub_blocks = []
            while True:
                sz = data[i]
                i += 1
                if sz == 0:
                    break
                sub_blocks.append((sz, i, data[i:i+sz]))
                i += sz
            total_data = sum(s for s, _, _ in sub_blocks)
            blocks.append(('IMG', {
                'left': l, 'top': t, 'w': iw, 'h': ih,
                'packed': p, 'lct_n': lct_n,
                'lzw_min': lzw_min,
                'sub_blocks': sub_blocks,
                'total_data': total_data,
            }))
        elif b == 0x21:
            label = data[i+1]
            i += 2
            content = b''
            while True:
                sz = data[i]
                i += 1
                if sz == 0:
                    break
                content += data[i:i+sz]
                i += sz
            blocks.append(('EXT', {'label': label, 'content': content}))
        elif b == 0x3b:
            blocks.append(('END', {}))
            break
        else:
            blocks.append(('UNK', {'byte': b, 'offset': i}))
            i += 1

    for kind, info in blocks:
        if kind == 'IMG':
            print(f"\nImage Descriptor:")
            print(f"  Left={info['left']}, Top={info['top']}, W={info['w']}, H={info['h']}")
            print(f"  Packed=0x{info['packed']:02x}, LCT={info['lct_n']}")
            print(f"  LZW min code size: {info['lzw_min']}")
            print(f"  Sub-blocks: {len(info['sub_blocks'])}")
            print(f"  Total LZW data: {info['total_data']} bytes")
            # Show first few sub-blocks
            for k, (sz, off, blk) in enumerate(info['sub_blocks'][:3]):
                print(f"    Block {k}: size={sz}, offset=0x{off:x}, first 20 bytes: {blk[:20].hex()}")
            if len(info['sub_blocks']) > 3:
                last_sz, last_off, last_blk = info['sub_blocks'][-1]
                print(f"    Last block: size={last_sz}, offset=0x{last_off:x}, first 20 bytes: {last_blk[:20].hex()}")
                # Also show termination byte
                print(f"    Block terminator at 0x{last_off + last_sz:x}: 0x{data[last_off + last_sz]:02x}")
        elif kind == 'EXT':
            print(f"\nExtension: label=0x{info['label']:02x}")
            print(f"  Content (first 50 bytes): {info['content'][:50].hex(errors='replace')}")
            if info['label'] == 0xff and len(info['content']) > 0:
                # Application extension - try to decode name
                try:
                    app_name = info['content'][:11].decode('ascii')
                    print(f"  Application: {app_name}")
                    if len(info['content']) > 11:
                        rest = info['content'][11:]
                        print(f"  Sub-data: {rest.hex()}")
                except:
                    pass
        elif kind == 'END':
            print(f"\nGIF Trailer at end")
        elif kind == 'UNK':
            print(f"\nUnknown block at 0x{info['offset']:02x}: byte=0x{info['byte']:02x}")

    # Find first 32 bytes and last 32 bytes
    print(f"\n--- First 64 bytes ---")
    print(data[:64].hex())
    print(f"\n--- Last 32 bytes ---")
    print(data[-32:].hex())

    # Diff with other file
    if 'sess2' in fname:
        with open('/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha_4004_sess1.gif', 'rb') as f:
            data1 = f.read()
        diffs = []
        for j in range(min(len(data), len(data1))):
            if data[j] != data1[j]:
                diffs.append(j)
        print(f"\n--- Diff between sess1 and sess2 ---")
        print(f"Total different bytes: {len(diffs)}")
        if len(diffs) > 0:
            print(f"First diff at offset: 0x{diffs[0]:02x}")
            print(f"Last diff at offset: 0x{diffs[-1]:02x}")
            if len(diffs) < 100:
                print(f"Diff offsets: {[f'0x{x:02x}' for x in diffs[:30]]}")
