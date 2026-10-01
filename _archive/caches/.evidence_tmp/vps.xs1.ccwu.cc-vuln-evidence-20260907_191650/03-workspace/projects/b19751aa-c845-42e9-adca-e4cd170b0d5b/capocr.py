import sys, numpy as np
from PIL import Image, ImageFilter

def ocr_captcha(path):
    im = Image.open(path).convert('L')
    big = im.resize((im.width*5, im.height*5), Image.LANCZOS)
    a = np.array(big)
    # black text on white -> threshold: text dark
    binv = Image.fromarray((a > 140).astype(np.uint8)*255)  # text=0(dark), bg=255
    binv = binv.filter(ImageFilter.MedianFilter(7))
    # pad white border
    p = Image.new('L', (binv.width+40, binv.height+40), 255)
    p.paste(binv, (20,20))
    out = path.replace('.png','') + '_ocr.png'
    p.save(out)
    return out

if __name__ == '__main__':
    print(ocr_captcha(sys.argv[1]))
