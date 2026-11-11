"""
Ring Think (NINE HANDS | DSP) - elargit le boitier sans rien etirer : insertion de coutures verticales (seam carving)
qui passent uniquement dans les zones vides de la facade (rainures horizontales), jamais dans un element.
Entree : out/pedal_clean.npy (1136 x 928, visuel nettoye). Sortie : out/pedal_wide.npy, out/seams.npy (x d'origine
de chaque couture, par ligne) ; map_x(x, y) donne la nouvelle abscisse d'un point du visuel d'origine.
"""
import os, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out')


RIM_T, RIM_B = 30, 32
PROTECT = ((950, 74, 1050, 140),        # MODE / TURN PRESETS
           (928, 127, 1082, 282),       # bouton MODE
           (930, 285, 1078, 390),       # touches RM / UB / LB
           (936, 396, 1077, 434),       # PITCH-SHIFT
           (60, 280, 170, 318),        # plaque BLEND
           (1089, 40, 1112, 470))      # couloir noir entre le panneau MODE et le bord : on ne l'elargit pas


def energy(img):
    g = img.mean(2)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))        # seulement le gradient en x : les rainures horizontales ne coutent rien
    lum = cv2.GaussianBlur(g, (0, 0), 1.5)
    col = img[..., 0] - img[..., 2]
    forb = ((lum > 105) | (col > 40)).astype(np.uint8)          # textes, potards, chrome, orange : interdit
    forb = cv2.dilate(forb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    H = img.shape[0]
    forb[:RIM_T] = 0; forb[H - RIM_B:] = 0                     # bord chrome haut / bas : horizontal, on peut le traverser
    yy, xx = np.mgrid[:H, :img.shape[1]]
    for cx in (114.0, 292.0, 472.5, 652.0, 829.0):              # potards (zone couverte par le potard anime)
        forb[np.hypot(xx - cx, yy - 203) < 76] = 1
    for (x0, y0, x1, y1) in PROTECT: forb[y0:y1, x0:x1] = 1
    e = gx + forb * 1e5
    for (x0, y0, x1, y1) in HARD: e[y0:y1, x0:x1] = 1e8          # coins arrondis du panneau : ne jamais les couper
    return e


HARD = ((1069, 56, 1100, 92), (1069, 428, 1100, 454), (908, 56, 946, 92), (908, 428, 935, 456))
BANDS = ((34, 100), (900, 1100))      # bandes sombres entre le bord chrome et les elements (gauche, droite)


def find_seams(img, n, band, pen=30.0, block=()):
    """n coutures dans la bande ; une couture peut repasser par la meme colonne (couloir etroit) :
    on ne retire rien, on penalise seulement le chemin deja pris pour repartir les suivantes."""
    H, W, _ = img.shape
    e = energy(img)
    out = np.ones(W, bool); out[band[0]:band[1]] = False
    e[:, out] = 1e6
    for (x0, y0, x1, y1) in block: e[y0:y1, x0:x1] = 1e7          # zone interdite a ce groupe de coutures
    seams = []
    for _ in range(n):
        M = e.copy(); back = np.zeros((H, W), np.int32)
        for y in range(1, H):
            prev = M[y - 1]
            L = np.r_[1e12, prev[:-1]]; R = np.r_[prev[1:], 1e12]
            st = np.vstack([L, prev, R]); k = st.argmin(0)
            M[y] += st[k, np.arange(W)]; back[y] = k - 1
        x = int(M[-1].argmin()); path = np.zeros(H, np.int32)
        for y in range(H - 1, -1, -1):
            path[y] = x
            if y > 0: x += back[y, x]
        seams.append(path)
        e[np.arange(H), path] += pen
    return np.array(seams)            # (n, H) abscisses d'origine


def insert(img, seams):
    H, W = img.shape[:2]; n = len(seams)
    out = np.zeros((H, W + n) + img.shape[2:], img.dtype)
    for y in range(H):
        cols = np.sort(seams[:, y]); row = img[y]; parts = []; last = 0
        for c in cols:
            parts.append(row[last:c + 1])
            nb = row[min(c + 1, W - 1)]
            parts.append(((row[c].astype(np.float32) + nb) / 2).astype(img.dtype)[None])
            last = c + 1
        parts.append(row[last:]); out[y] = np.concatenate(parts)
    return out


def map_x(seams, x, y):
    y = int(round(min(max(y, 0), seams.shape[1] - 1)))
    return x + float((seams[:, y] < x).sum())


if __name__ == '__main__':
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    a = np.load(os.path.join(OUT, 'pedal_clean2.npy'))
    nr = n // 4                                       # un quart a droite (dans le panneau MODE), le reste a gauche
    # panneau MODE elargi des deux cotes (moitie a l'interieur gauche, moitie a droite) : son contenu reste centre
    s = np.vstack([find_seams(a, n - nr, BANDS[0]),
                   find_seams(a, nr // 2, (900, 1010), block=((1000, 40, 1100, 470), (880, 56, 923, 720))),
                   find_seams(a, nr - nr // 2, (1036, 1100))])
    np.save(os.path.join(OUT, 'seams.npy'), s)
    np.save(os.path.join(OUT, 'pedal_wide.npy'), insert(a, s))
    print('coutures', s.shape, 'x min/max', s.min(), s.max())
