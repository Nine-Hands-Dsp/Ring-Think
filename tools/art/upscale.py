"""agrandissement x2 du visuel elargi par super-resolution EDSR (OpenCV dnn_superres), par tuiles avec recouvrement"""
import os, sys, numpy as np, cv2, time
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out')
MODEL = '/home/claude/models/EDSR_x2_noD2S.pb'      # EDSR x2, noeud DepthToSpace remplace par Identity (fait en numpy)
_NET = None
def sr2(img, tile=200, ov=12):
    global _NET
    if _NET is None: _NET = cv2.dnn.readNetFromTensorflow(MODEL)      # un seul reseau par processus (memoire)
    net = _NET
    MEAN = np.array([103.1545, 111.5410, 114.3555], np.float32)       # moyenne BGR du modele EDSR (comme dnn_superres)
    class _SR:
        def upsample(self, im):
            blob = cv2.dnn.blobFromImage(im.astype(np.float32) - MEAN, 1.0, swapRB=False, crop=False)
            net.setInput(blob); o = net.forward('add_99')[0]          # (12, h, w)
            h, w = o.shape[1:]; r = np.zeros((2 * h, 2 * w, 3), np.float32)
            for i in range(2):
                for j in range(2):
                    for c in range(3): r[i::2, j::2, c] = o[(i * 2 + j) * 3 + c]
            return np.clip(r + MEAN, 0, 255)
    sr = _SR()
    H, W = img.shape[:2]; out = np.zeros((2 * H, 2 * W, 3), np.float32); wsum = np.zeros((2 * H, 2 * W, 1), np.float32)
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            y0, x0 = max(0, y - ov), max(0, x - ov); y1, x1 = min(H, y + tile + ov), min(W, x + tile + ov)
            r = sr.upsample(img[y0:y1, x0:x1]).astype(np.float32)
            h, w = r.shape[:2]
            wy = np.minimum(np.arange(h) + 1, np.arange(h)[::-1] + 1).clip(max=2 * ov) / (2 * ov)
            wx = np.minimum(np.arange(w) + 1, np.arange(w)[::-1] + 1).clip(max=2 * ov) / (2 * ov)
            if y0 == 0: wy[:2 * ov] = 1
            if x0 == 0: wx[:2 * ov] = 1
            if y1 == H: wy[-2 * ov:] = 1
            if x1 == W: wx[-2 * ov:] = 1
            wgt = (wy[:, None] * wx[None, :])[..., None]
            out[2 * y0:2 * y1, 2 * x0:2 * x1] += r * wgt; wsum[2 * y0:2 * y1, 2 * x0:2 * x1] += wgt
    return out / np.maximum(wsum, 1e-6)
if __name__ == '__main__':
    a = np.load(os.path.join(OUT, sys.argv[1] if len(sys.argv) > 1 else 'pedal_wide.npy'))
    t = time.time(); u = sr2(np.clip(a, 0, 255).astype(np.uint8)[..., ::-1])[..., ::-1]
    np.save(os.path.join(OUT, 'pedal_wide_x2.npy'), u.astype(np.float32)); print('x2', u.shape, round(time.time() - t), 's')
