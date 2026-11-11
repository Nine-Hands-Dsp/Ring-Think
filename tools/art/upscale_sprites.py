"""EDSR x2 des petits sprites (bouton MODE, PITCH-SHIFT, PHASER) : out/sr_<nom>.png (couleur et alpha agrandis)"""
import os, sys, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out'); sys.path.insert(0, HERE)
import upscale
SRC = {n: os.path.join(OUT, 'src_' + n + '.png') for n in ('pitchshift_white', 'pitchshift_yellow', 'cap_big')}
SRC.update({n: os.path.join('/home/claude/ring-think', n + '.png') for n in ('phaser_white', 'phaser_yellow')})
for n, p in SRC.items():
    arr = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
    pad = 8; arr = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)))
    rgb = upscale.sr2(np.ascontiguousarray(np.clip(arr[..., 2::-1], 0, 255).astype(np.uint8)))[..., ::-1]
    al = upscale.sr2(np.ascontiguousarray(np.repeat(arr[..., 3:4].astype(np.uint8), 3, 2))).mean(2)
    out = np.dstack([rgb, al])[2 * pad:-2 * pad, 2 * pad:-2 * pad]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'sr_' + n + '.png')); print(n, out.shape)
