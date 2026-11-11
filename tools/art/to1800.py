"""ramene les images de make_art_hd.py (2,5 px / unite, fond 2938 x 2250) a 2 px / unite (fond 2350 x 1800, regle des pedales doubles)"""
import os, sys, re, numpy as np, cv2
from PIL import Image
SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True); k = 2.0 / 2.5
for n in os.listdir(SRC):
    if not n.endswith('.png') or n.startswith('knob_'):
        continue
    a = np.asarray(Image.open(os.path.join(SRC, n)).convert('RGBA')).astype(np.float32)
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4] / 255
    w, h = (2350, 1800) if n == 'background.png' else (max(1, round(a.shape[1] * k)), max(1, round(a.shape[0] * k)))
    r = cv2.resize(pm, (w, h), interpolation=cv2.INTER_AREA); al = np.clip(r[..., 3:4], 0, 255)
    r[..., :3] = np.where(al > 0.5, r[..., :3] * 255 / np.maximum(al, 1e-6), 0); r[..., 3:4] = al
    Image.fromarray(np.clip(r, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(DST, n), optimize=True)
s = open(os.path.join(SRC, 'Layout.h')).read().replace('pxPerUnit = 2.50f', 'pxPerUnit = 2.00f').replace('images 2,5 px / unite', 'images 2 px / unite (fond 2350 x 1800)')
open(os.path.join(DST, 'Layout.h'), 'w').write(s)
print('ok')
