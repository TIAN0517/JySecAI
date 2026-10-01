import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert('L')
h, w = 34, 90
im2 = im.resize((w, h))
b = np.array(im2)
chars = " .:-=+*#%@"
for row in b:
    line = []
    for v in row:
        if v < 245:
            idx = min(9, int((255 - v) / 25.6))
            line.append(chars[idx])
        else:
            line.append(" ")
    print("".join(line))
