import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert('L')
a = np.array(im)
# binary: text=1, bg=0
b = (a < 140).astype(int)
h, w = b.shape
# render two halves for clarity, each char bigger
# full width ~ w, do height 40 rows, cols = w
rows = 40
cols = 80
im2 = Image.fromarray((b*255).astype(np.uint8)).resize((cols, rows))
c = np.array(im2) > 100
print("LEFT (cols 0-40):")
for r in range(rows):
    print("".join("#" if c[r,cc] else " " for cc in range(0,40)))
print("RIGHT (cols 40-80):")
for r in range(rows):
    print("".join("#" if c[r,cc] else " " for cc in range(40,80)))
