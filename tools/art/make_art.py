"""
Ring Think (NINE HANDS | DSP) - image du plugin au format double : PNG 2350 x 1800, pedale plein cadre.
  1. tools/clean_pedal.py : visuel de l'utilisateur nettoye (LED, potards, capuchons, textes 9V / Studio Wiga effaces)
  2. tools/widen.py       : boitier elargi par coutures dans les bandes sombres (rien n'est etire)
  3. ce script           : mise a l'echelle (1800 de haut), canal alpha (boitier + embases), 5 embases jack du kit photo,
                           sprites (LED du kit, faces des touches, capuchons, footswitch du kit) et apercu.
Repere du plugin = image / 2 (1175 x 900 unites). Ecrit out/layout.json et out/Layout.h.
"""
import os, sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, 'out')
sys.path.insert(0, HERE)
import widen, photo_controls as PC

IW, IH = 2350, 1800
G = json.load(open(os.path.join(HERE, 'geom.json'))); M0 = G['M']          # anciennes coordonnees (repere 1240 x 928, marge 52)
a = np.load(os.path.join(OUT, 'pedal_wide.npy')); seams = np.load(os.path.join(OUT, 'seams.npy'))
SH, SW = a.shape[:2]
CX0, CX1, CY0, CY1 = 0.0, 1176.5, 2.5, 926.5      # contour exterieur du boitier (bord chrome) dans le visuel elargi
CR = 57.0                                       # rayon des coins (mesure sur le bord chrome du visuel)
K = IH / (CY1 - CY0)                            # 1800 / 924
BW = (CX1 - CX0) * K; X0 = (IW - BW) / 2        # largeur et bord gauche du boitier dans l'image

def P(x_old, y):
    """point du visuel d'origine (repere 1240 x 928 de la v2) -> pixels de l'image 2350 x 1800"""
    xs = x_old - M0
    return X0 + (widen.map_x(seams, xs, y) - CX0) * K, (y - CY0) * K

# ---------------------------------------------------------------- 1. boitier mis a l'echelle + canal alpha (rectangle a coins arrondis)
bw = int(round(BW)); x0 = int(round(X0))
X2 = os.path.join(OUT, 'pedal_wide_x2.npy')
if os.path.exists(X2):                          # agrandissement x2 par super-resolution EDSR (tools/upscale.py), puis x0,97
    u8 = np.clip(np.load(X2), 0, 255).astype(np.uint8); k2 = K / 2
    Mx = np.float32([[k2, 0, -CX0 * K], [0, k2, -CY0 * K]])
    big = cv2.warpAffine(u8, Mx, (bw, IH), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
else:
    u8 = np.clip(a, 0, 255).astype(np.uint8)
    Mx = np.float32([[K, 0, -CX0 * K], [0, K, -CY0 * K]])
    big = cv2.warpAffine(u8, Mx, (bw, IH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    blur = cv2.GaussianBlur(big, (0, 0), 1.1); big = np.clip(big + 0.45 * (big - blur), 0, 255)
# bord chrome regenere sur les 4 cotes droits : profil propre de chaque cote, identique sur toute sa longueur
# (le visuel agrandi avait des bandes qui s'arretaient en cours de route), stries de brossage dans le sens du bord
src0 = np.load(os.path.join(OUT, 'pedal_clean2.npy'))
RIMW = 34.0
prof = {'L': src0[300:620, 0:40].mean(0),                               # d = 0 au bord exterieur
        'T': src0[2:42, 300:800].mean(1),
        'R': src0[300:620, 1088:1129].mean(0)[::-1],
        'B': src0[887:928, 300:800].mean(1)[::-1]}
off_ = {'L': 0.0, 'T': CY0 - 2.0, 'R': 0.5, 'B': 928 - CY1 - 1.0}        # decalage du bord exterieur dans chaque profil
rng_r = np.random.default_rng(11)
def rim_side(side, length):
    n = int(math.ceil(RIMW * K)) + 2; dsrc = np.arange(n) / K + off_[side]
    pr = prof[side]; col = np.stack([np.interp(dsrc, np.arange(len(pr)), pr[:, c]) for c in range(3)], -1)   # (n, 3)
    strip = np.broadcast_to(col[None], (length, n, 3)).copy()
    streak = cv2.GaussianBlur(rng_r.normal(0, 1, (length, n)).astype(np.float32), (0, 0), sigmaX=0.6, sigmaY=40)
    lum_ = col.mean(1)[None, :, None] / 255.0
    strip += (streak * 9.0)[..., None] * lum_                             # brossage visible sur le metal clair seulement
    w = np.clip((RIMW * K - np.arange(n)) / (1.5 * K), 0, 1)[None, :, None]   # fondu vers la facade au bord interieur
    return strip, w
yA, yB = int(CR * K), IH - int(CR * K)
xA, xB = int(CR * K), bw - int(CR * K)
def ramp(L_, m=2):
    return np.ones(L_)                                   # les coins sont regeneres aussi : raccord exact, pas de fondu
for side in 'LRTB':
    if side in 'LR':
        L_ = yB - yA; strip, w = rim_side(side, L_); n = strip.shape[1]
        w = w * ramp(L_)[:, None, None]
        if side == 'L': region = big[yA:yB, 0:n]; region[:] = region * (1 - w) + strip * w
        else:           region = big[yA:yB, bw - n:bw]; region[:] = region * (1 - w[:, ::-1]) + strip[:, ::-1] * w[:, ::-1]
    else:
        L_ = xB - xA; strip, w = rim_side(side, L_); n = strip.shape[1]
        w = w * ramp(L_)[:, None, None]
        strip = strip.transpose(1, 0, 2); w = w.transpose(1, 0, 2)
        if side == 'T': region = big[0:n, xA:xB]; region[:] = region * (1 - w) + strip * w
        else:           region = big[IH - n:IH, xA:xB]; region[:] = region * (1 - w[::-1]) + strip[::-1] * w[::-1]
# coins : meme profil, balaye en arc de cercle (rayon CR), passage progressif du profil d'un cote a l'autre
def prof_col(side, dsrc):
    pr = prof[side]; return np.stack([np.interp(dsrc, np.arange(len(pr)), pr[:, c]) for c in range(3)], -1)
Rc = CR * K; nC = int(math.ceil(Rc)) + 1
yy_, xx_ = np.mgrid[0:nC, 0:nC].astype(np.float64)
for (sh, sv, x0c, y0c, fx, fy) in (('L', 'T', 0, 0, 1, 1), ('R', 'T', bw - nC, 0, -1, 1), ('L', 'B', 0, IH - nC, 1, -1), ('R', 'B', bw - nC, IH - nC, -1, -1)):
    # repere local du coin : (u, v) = distance aux bords exterieurs gauche/droit et haut/bas
    u = xx_ if fx > 0 else (nC - 1 - xx_) + (bw - (x0c + nC))
    v = yy_ if fy > 0 else (nC - 1 - yy_) + (IH - (y0c + nC))
    du, dv = np.maximum(Rc - (u + 0.5), 0), np.maximum(Rc - (v + 0.5), 0)
    inside = (du > -1.0) & (dv > -1.0)
    dist = np.hypot(du, dv); d_in = Rc - dist                       # distance au bord exterieur, vers l'interieur
    phi = np.arctan2(dv, du)                                        # 0 = face au cote vertical, pi/2 = face au cote horizontal
    wv = np.clip(phi / (np.pi / 2), 0, 1); wv = wv * wv * (3 - 2 * wv)
    ch = prof_col(sh, d_in / K + off_[sh]); cv_ = prof_col(sv, d_in / K + off_[sv])
    col = ch * (1 - wv[..., None]) + cv_ * wv[..., None]
    ang_n = cv2.GaussianBlur(rng_r.normal(0, 1, (720, 1)).astype(np.float32), (0, 0), sigmaX=0.01, sigmaY=6)[:, 0]
    streak = ang_n[np.clip((phi / (np.pi / 2) * 719).astype(int), 0, 719)]
    col += (streak * 9.0)[..., None] * (col.mean(-1, keepdims=True) / 255.0)
    w = np.clip((RIMW * K - d_in) / (1.5 * K), 0, 1) * inside * (d_in > -2)
    region = big[y0c:y0c + nC, x0c:x0c + nC]
    region[:] = region * (1 - w[..., None]) + col * w[..., None]
SS = 4; mk = Image.new('L', (bw * SS, IH * SS), 0)
ImageDraw.Draw(mk).rounded_rectangle((0, 0, bw * SS - 1, IH * SS - 1), radius=CR * K * SS, fill=255)
balpha = np.asarray(mk.resize((bw, IH), Image.LANCZOS)).astype(np.float32)
canvas = np.zeros((IH, IW, 4), np.float32)
canvas[:, x0:x0 + bw, :3] = big; canvas[:, x0:x0 + bw, 3] = balpha

def over(dst, spr, cx, cy, opacity=1.0):
    """composite un sprite RGBA float centre en (cx, cy)"""
    h, w = spr.shape[:2]; X = int(round(cx - w / 2)); Y = int(round(cy - h / 2))
    xa, ya, xb, yb = max(X, 0), max(Y, 0), min(X + w, dst.shape[1]), min(Y + h, dst.shape[0])
    if xa >= xb or ya >= yb: return
    s = spr[ya - Y:yb - Y, xa - X:xb - X]; sa = s[..., 3:4] / 255.0 * opacity
    d = dst[ya:yb, xa:xb]; da = d[..., 3:4] / 255.0
    oa = sa + da * (1 - sa)
    d[..., :3] = np.where(oa > 1e-6, (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    d[..., 3:4] = oa * 255

# ---------------------------------------------------------------- 2. embases jack du kit (OUT a gauche, entrees a droite), sans ombre
JACK_LEN = 75.0 * K                              # longueur le long de la tranche (75 unites du visuel d'origine ; 3 jacks rapproches a droite)
JACKS = {'L': [544.5, 703.5], 'R': [485.5, 568.5, 651.5]}   # a droite : espacement regulier (83)   # a gauche : centres sur OUTPUTS et MONO
jack_px = {}
for side, ys in JACKS.items():
    spr, jw, jh = PC.jack_sprite(JACK_LEN, 1, -1 if side == 'L' else +1)
    for y in ys:
        cy = (y - CY0) * K
        cx = jw / 2 if side == 'L' else IW - jw / 2                   # le bout de l'embase touche le bord de l'image, la face sous l'arete
        over(canvas, spr, cx, cy)
        jack_px.setdefault(side, []).append((cx, cy, jw, jh))
pl = G['pill']; (px0, py0) = P(pl[0], pl[1]); (px1, py1) = P(pl[2], pl[3])
S4 = 4; pw_, ph_ = int(px1 - px0) + 16, int(py1 - py0) + 16
pi = Image.new('RGBA', (pw_ * S4, ph_ * S4), (0, 0, 0, 0))
ImageDraw.Draw(pi).rounded_rectangle((8 * S4, 8 * S4, (pw_ - 8) * S4, (ph_ - 8) * S4), radius=10 * K * S4, fill=(10, 10, 10, 255), outline=(240, 240, 240, 255), width=int(2.4 * K * S4))
pi = np.asarray(pi.resize((pw_, ph_), Image.LANCZOS)).astype(np.float32)
over(canvas, pi, (px0 + px1) / 2, (py0 + py1) / 2)
# zones de protection des LED PRESET / STATUS : petite plaque sombre arrondie, comme les plaques des inscriptions
def led_plate(c, R):
    S4 = 4; hw, hh = 1.62 * R, 1.62 * R; rad = 0.62 * hw; pad = 10
    W_, H_ = int(2 * hw) + 2 * pad, int(2 * hh) + 2 * pad
    im_ = Image.new('L', (W_ * S4, H_ * S4), 0)
    ImageDraw.Draw(im_).rounded_rectangle((pad * S4, pad * S4, (W_ - pad) * S4, (H_ - pad) * S4), radius=rad * S4, fill=255)
    m_ = np.asarray(im_.resize((W_, H_), Image.LANCZOS)).astype(np.float32) / 255
    sh_ = cv2.GaussianBlur(np.roll(np.roll(m_, 2, 0), 2, 1), (0, 0), 2.5) * 0.55 * (1 - m_)       # ombre douce bas-droite
    ed_ = np.clip(m_ - cv2.erode(m_, np.ones((3, 3))), 0, 1)                                    # arete fine
    col = np.zeros((H_, W_, 3), np.float32) + 8.0
    yy_, xx_ = np.mgrid[0:H_, 0:W_]; lit = np.clip(((xx_ - W_ / 2) + (yy_ - H_ / 2)) / (W_ / 2), 0, 1)   # arete eclairee en bas a droite
    col += (ed_ * (18 + 40 * lit))[..., None]
    alpha_ = np.clip(m_ * 0.97 + sh_, 0, 1)
    col = np.where(m_[..., None] > 0.01, col, 0)
    over(canvas, np.dstack([col, alpha_ * 255]), c[0], c[1])
for key in ('presetled', 'statusled'):
    led_plate(P(*G[key]), 14.0 * K)
Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'background.png'), optimize=True)
print('boitier', bw, 'x0', x0, 'jacks', {k: [round(v[0]) for v in vs] for k, vs in jack_px.items()}, 'saillie', round(jw, 1))

# ---------------------------------------------------------------- 3. positions (repere image px)
pos = {}
pos['knobs'] = [P(x, y) for x, y in G['knobs']]
pos['ladder'] = [P(x, y) for x, y in G['ladder']]
pos['modeled'] = {k: P(*v) for k, v in G['modeled'].items()}
pos['presetled'] = P(*G['presetled']); pos['statusled'] = P(*G['statusled'])
pos['capbig'] = P(*G['capbig']); pos['fsL'] = P(*G['capL']); pos['fsR'] = P(*G['capR'])
fx = G['face']; pos['faces'] = {k: P(fx[i] + fx[4] / 2, fx[3] + fx[5] / 2) for i, k in enumerate(('rm', 'ub', 'lb'))}
pos['labels'] = {k: P(v[0] + v[2] / 2, v[1] + v[3] / 2) for k, v in G['labels'].items()}
pos['ps'] = P(G['ps'][0] + G['ps'][2] / 2, G['ps'][1] + G['ps'][3] / 2)
pl = G['pill']; pos['phpill'] = (P(pl[0], (pl[1] + pl[3]) / 2), P(pl[2], (pl[1] + pl[3]) / 2))
pos['phled'] = P(*G['phled']); pos['phtxt'] = P(*G['phtxt'])
boxC = X0 + BW / 2
pos['bar'] = (boxC, (810 - CY0) * K, 800.0, 76.0)          # pastille presets / ligne d'etat (400 x 38 unites)
pos['logo'] = (*P(584.0 + M0, 875.5), 460.0)     # centre du cadre sombre du bas (x 424,5..743,5 / y 863..888 du visuel)
pos['box'] = (X0, 0.0, BW, float(IH))

# ---------------------------------------------------------------- 4. sprites
def load_src(n): return np.asarray(Image.open(os.path.join(OUT, 'src_' + n)).convert('RGBA')).astype(np.float32)
def scaled(arr, k=K):
    pm = arr.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
    h, w = arr.shape[:2]; r = cv2.resize(pm, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_CUBIC)
    al = np.clip(r[..., 3:4], 0, 255); r[..., :3] = np.where(al > 0.5, r[..., :3] * 255 / np.maximum(al, 1e-6), 0); r[..., 3:4] = al
    return np.clip(r, 0, 255)

SPR = {}
ledS_off, ledS_on, _ = PC.led_sprites(9.0 * K, 1, colour='amber')        # petites LED (echelle, touches de mode, phaser)
ledP_off, ledP_on, _ = PC.led_sprites(14.0 * K, 1, colour='amber')       # LED PRESET
ledR_off, ledR_on, _ = PC.led_sprites(14.0 * K, 1, colour='red')         # LED STATUS
fs, fs_refl, fsS, fsBtn = PC.footswitch_sprite(112.0 * K, 1)
SPR.update(ledS_off=ledS_off, ledS_on=ledS_on, ledP_off=ledP_off, ledP_on=ledP_on, ledR_off=ledR_off, ledR_on=ledR_on, fs=fs)
# sprites agrandis par EDSR x2 (tools/upscale_sprites.py, processus a part pour la memoire), ramenes a l'echelle K
def sr_load(n, w, h):
    arr = np.asarray(Image.open(os.path.join(OUT, 'sr_' + n + '.png')).convert('RGBA')).astype(np.float32)
    return np.clip(cv2.resize(arr, (max(1, round(w * K)), max(1, round(h * K))), interpolation=cv2.INTER_AREA), 0, 255)
for n in ('pitchshift_white', 'pitchshift_yellow', 'cap_big'):
    h_, w_ = load_src(n + '.png').shape[:2]; SPR[n] = sr_load(n, w_, h_)
def clean_cap(spr):
    """bouton MODE reconstruit parfaitement rond : profil radial moyen (anneaux concentriques) + lumiere fixe
    (harmoniques 1 et 2 selon l'angle, lumiere en haut a gauche) + grain fin de la face d'origine"""
    from scipy.ndimage import map_coordinates
    n = spr.shape[0]; c = (n - 1) / 2; R = n / 2
    pm = spr.copy(); pm[..., :3] *= pm[..., 3:4] / 255
    NA, NR = 2048, int(R * 4)
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)[:, None]; rr = np.linspace(0, R, NR)[None, :]
    Y = c + rr * np.sin(th); X = c + rr * np.cos(th)
    pol = np.stack([map_coordinates(pm[..., k], [Y, X], order=3, mode='nearest') for k in range(4)], -1)
    rec = np.repeat(pol.mean(0, keepdims=True), NA, 0)
    for h in (1, 2):
        cs, sn = np.cos(h * th)[..., None], np.sin(h * th)[..., None]
        A = 2 * (pol * cs).mean(0, keepdims=True); B = 2 * (pol * sn).mean(0, keepdims=True)
        rec = rec + A * cs + B * sn
    rec[..., 3] = pol[..., 3].mean(0, keepdims=True)
    # face : profil lisse (pas d'anneaux en cible au centre), les anneaux de la bague restent nets
    fz = np.clip((0.68 - rr / R) / 0.04, 0, 1)[..., None]
    rec = rec * (1 - fz) + cv2.GaussianBlur(rec, (0, 0), sigmaX=24, sigmaY=0.01) * fz
    face = np.clip((0.70 - rr / R) / 0.05, 0, 1)[..., None]                     # grain d'origine sur la face seulement
    grain = pol - cv2.GaussianBlur(pol, (0, 0), 3)
    rec[..., :3] += (grain[..., :3] * face)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64); d = np.hypot(xx - c, yy - c); ang = np.mod(np.arctan2(yy - c, xx - c), 2 * np.pi)
    ia = ang / (2 * np.pi) * NA; ir = d / R * (NR - 1)
    recw = np.concatenate([rec, rec[:4]])
    back = np.stack([map_coordinates(recw[..., k], [ia, ir], order=3, mode='nearest') for k in range(4)], -1)
    Rv = 69.2 * K; a_ = np.clip(Rv - d + 0.5, 0, 1)
    rgb = back[..., :3] / np.maximum(back[..., 3:4] / 255, 1e-3)
    return np.dstack([np.clip(rgb, 0, 255), a_ * 255]).astype(np.float32)
SPR['cap_big'] = clean_cap(SPR['cap_big'])
for n in ('phaser_white', 'phaser_yellow'):
    im_ = Image.open(os.path.join('/home/claude/ring-think', n + '.png')); SPR[n] = sr_load(n, im_.width, im_.height)
# touches RM / UB / LB redessinees en vectoriel (contours nets) + inscriptions en Poppins Bold
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def make_face(lit):
    w, h, r, S = 44 * K, 98 * K, 3.2 * K, 4
    W_, H_ = int(round(w)) + 6, int(round(h)) + 6
    yy = np.linspace(0, 1, H_ * S)[:, None]
    top, bot = (np.array([232, 56, 0.]), np.array([242, 66, 6.])) if lit else (np.array([31, 32, 33.]), np.array([39, 40, 41.]))
    col = np.broadcast_to(top + (bot - top) * yy[..., None], (H_ * S, W_ * S, 3)).copy()
    m = Image.new('L', (W_ * S, H_ * S), 0); ImageDraw.Draw(m).rounded_rectangle((3 * S, 3 * S, (W_ - 3) * S, (H_ - 3) * S), radius=r * S, fill=255)
    m = np.asarray(m).astype(np.float32) / 255
    # biseau : arete claire en haut a gauche, sombre en bas a droite (lumiere en haut a gauche)
    dist = cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / S
    gx = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=5)
    nrm = np.hypot(gx, gy) + 1e-6; facing = cv2.GaussianBlur(((gx + gy) / nrm / 1.414), (0, 0), 2 * S)   # >0 : arete tournee vers la lumiere
    edge = np.clip(1 - dist / 1.8, 0, 1)[..., None]
    lightc = np.array([255, 128, 64.]) if lit else np.array([78, 79, 80.])
    darkc = np.array([150, 30, 0.]) if lit else np.array([12, 12, 13.])
    f = np.clip(facing, -1, 1)[..., None]
    col = col * (1 - edge) + edge * np.where(f > 0, col * (1 - f) + lightc * f, col * (1 + f) - darkc * f)
    rng_ = np.random.default_rng(5); col += rng_.normal(0, 1.0, col.shape[:2])[..., None]
    out = np.dstack([np.clip(col, 0, 255), m * 255]).astype(np.float32)
    out = cv2.resize(out, (W_, H_), interpolation=cv2.INTER_AREA)
    # filet sombre autour (separe la touche de sa fente)
    ring = cv2.GaussianBlur(cv2.dilate((out[..., 3] > 30).astype(np.float32), np.ones((3, 3))), (0, 0), 0.6)
    a_ = out[..., 3:4] / 255; ra = np.clip(ring[..., None] - a_, 0, 1) * 0.85
    oa = a_ + ra; out[..., :3] = out[..., :3] * a_ / np.maximum(oa, 1e-6); out[..., 3:4] = oa * 255
    return out
def label_sprite(txt, cap_h):
    S = 4; f = ImageFont.truetype(FB, int(cap_h / 0.70 * S))
    bb = ImageDraw.Draw(Image.new('L', (8, 8))).textbbox((0, 0), txt, font=f)
    im = Image.new('L', (bb[2] - bb[0] + 8 * S, bb[3] - bb[1] + 8 * S), 0)
    ImageDraw.Draw(im).text((4 * S - bb[0], 4 * S - bb[1]), txt, font=f, fill=255)
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    arr = np.zeros((im.height, im.width, 4), np.float32); arr[..., :3] = 255; arr[..., 3] = np.asarray(im)
    return arr
SPR['face_on'] = make_face(True); SPR['face_off'] = make_face(False)
for k, t in (('rm', 'RM'), ('ub', 'UB'), ('lb', 'LB')): SPR['label_' + k] = label_sprite(t, 14.5 * K)
# siege des LED : trou sombre dans la facade, arete eclairee en bas a droite (lumiere en haut a gauche)
def seat_sprite(R):
    S = 4; n = int(R * 3.2) | 1; c = n * S / 2
    yy, xx = np.mgrid[0:n * S, 0:n * S].astype(np.float32); d = np.hypot(xx - c, yy - c) / S
    ang = np.arctan2(yy - c, xx - c); lit_ = np.clip(np.cos(ang - np.pi / 4), 0, 1)       # bas a droite
    ro = 1.16 * R
    a_ = np.clip((ro - d) * 1.5, 0, 1)
    rim = np.clip(1 - np.abs(d - (ro - 0.9)) / 0.9, 0, 1) * lit_
    col = np.zeros((n * S, n * S, 3), np.float32) + 4 + rim[..., None] * 70
    out = np.dstack([col, a_ * 235]); return cv2.resize(out, (n, n), interpolation=cv2.INTER_AREA)
SPR['seatS'] = seat_sprite(9.0 * K); SPR['seatP'] = seat_sprite(14.0 * K)
os.makedirs(os.path.join(OUT, 'sprites'), exist_ok=True)
for n, s in SPR.items(): Image.fromarray(np.clip(s, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'sprites', n + '.png'))

# ---------------------------------------------------------------- 5. halo des LED : la facade recoit la lumiere (calque alpha, dose par Glow)
bg_rgb = canvas[..., :3]
def led_glow(c, col, R):
    """lumiere ajoutee sur la facade par une LED en c (rayon de lentille R px) ; renvoie RGBA float (alpha = lumiere seule)"""
    n = int(R * 14); X = int(c[0] - n / 2); Y = int(c[1] - n / 2)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); d = np.hypot(xx - n / 2, yy - n / 2)
    def lamb(h): return (h * h / (h * h + d * d)) ** 1.5
    E = 0.8 * (4.5 * lamb(1.4 * R) + 1.1 * lamb(5.0 * R))                   # tache serree + diffusion large et faible
    E *= np.clip((d - 0.9 * R) / (0.25 * R), 0, 1)                     # rien sous la lentille (elle est dessinee par-dessus)
    sub = bg_rgb[max(Y, 0):Y + n, max(X, 0):X + n]
    E = E[max(Y, 0) - Y:max(Y, 0) - Y + sub.shape[0], max(X, 0) - X:max(X, 0) - X + sub.shape[1]]
    colv = np.array(col, np.float32) / 255.0
    smooth = cv2.GaussianBlur(sub, (0, 0), 2.0)                          # la lumiere suit le relief, pas les taches du grain
    add = (smooth * 2.2 + 0.5 * (sub - smooth).clip(-20, 20) + 18.0) * E[..., None] * colv                      # le grain de la facade s'allume, les creux restent sombres
    halo = 0.8 * 110.0 * (0.9 * R / np.maximum(d, 0.9 * R)) ** 2.2             # leger halo optique autour de la lentille
    add += halo[max(Y, 0) - Y:max(Y, 0) - Y + sub.shape[0], max(X, 0) - X:max(X, 0) - X + sub.shape[1], None] * colv
    out = np.zeros(sub.shape[:2] + (4,), np.float32)
    al = np.clip(add.max(2) / 255.0, 0, 1)
    out[..., :3] = np.clip(sub + add, 0, 255); out[..., 3] = al * 255
    return out, (max(X, 0), max(Y, 0))
AMBER = (255, 140, 40); RED = (255, 40, 30)

# ---------------------------------------------------------------- 6. apercu (etat par defaut : preset 1 Ring Mod, RM, effet actif)
def knob_layers(D):
    L = {}
    for n in ('shadow', 'crown', 'cap', 'marker', 'highlight'):
        L[n] = Image.open(os.path.join(ROOT, 'assets', 'knob', 'ring_knob_' + n + '.png')).resize((D, D), Image.LANCZOS)
    st = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    for n in ('crown', 'cap', 'marker'): st = Image.alpha_composite(st, L[n])
    return L, st
KD = int(round(169 * K))                      # le potard anime couvre entierement le potard du visuel (rayon 71 unites)

def preview(glow=1.0, values=(0.6, 0.25, 0.8, 0.5, 0.8), path='preview.png'):
    c = canvas.copy()
    lit = [(pos['ladder'][0], AMBER, 9.0 * K), (pos['modeled']['rm'], AMBER, 9.0 * K),
           (pos['presetled'], AMBER, 14.0 * K), (pos['statusled'], RED, 14.0 * K)]
    for p_, col, R in lit:
        gl, (gx, gy) = led_glow(p_, col, R)
        over(c, gl, gx + gl.shape[1] / 2, gy + gl.shape[0] / 2, glow)
    for k in ('rm', 'ub', 'lb'): over(c, SPR['face_on' if k == 'rm' else 'face_off'], *pos['faces'][k])
    for k in ('rm', 'ub', 'lb'): over(c, SPR['label_' + k], *pos['labels'][k])
    for p_ in pos['ladder'] + list(pos['modeled'].values()) + [pos['phled']]: over(c, SPR['seatS'], *p_)
    for p_ in (pos['presetled'], pos['statusled']): over(c, SPR['seatP'], *p_)
    for i, p_ in enumerate(pos['ladder']): over(c, SPR['ledS_on' if i == 0 else 'ledS_off'], *p_)
    for k, p_ in pos['modeled'].items(): over(c, SPR['ledS_on' if k == 'rm' else 'ledS_off'], *p_)
    over(c, SPR['ledP_on'], *pos['presetled']); over(c, SPR['ledR_on'], *pos['statusled'])
    over(c, SPR['pitchshift_white'], *pos['ps'])
    over(c, SPR['ledS_off'], *pos['phled']); over(c, SPR['phaser_white'], pos['phtxt'][0] + SPR['phaser_white'].shape[1] / 2, pos['phtxt'][1] + SPR['phaser_white'].shape[0] / 2)
    over(c, SPR['cap_big'], *pos['capbig'])
    # point grave du bouton MODE (preset 1) : creux sombre, liseré clair en bas a droite
    slot = 1; angd = math.radians(-135 + 270 * slot / 9); rr = 41.0 * K
    dx_, dy_ = pos['capbig'][0] + math.sin(angd) * rr, pos['capbig'][1] - math.cos(angd) * rr
    Sd = 4; nd = int(14 * K); dimg = Image.new('RGBA', (nd * Sd, nd * Sd), (0, 0, 0, 0)); dd_ = ImageDraw.Draw(dimg)
    cc = nd * Sd / 2; r1 = 5.3 * K * Sd; r2 = 4.8 * K * Sd; o1 = 0.9 * K * Sd
    dd_.ellipse((cc - r1 + o1, cc - r1 + 1.1 * K * Sd, cc + r1 + o1, cc + r1 + 1.1 * K * Sd), fill=(255, 255, 255, 140))
    g2 = Image.new('L', (nd * Sd, nd * Sd), 0); ImageDraw.Draw(g2).ellipse((cc - r2, cc - r2, cc + r2, cc + r2), fill=255)
    yy_, xx_ = np.mgrid[0:nd * Sd, 0:nd * Sd]; t_ = np.clip(((xx_ - cc) + (yy_ - cc)) / (2 * r2) + 0.5, 0, 1)[..., None]
    dc = np.array([42, 36, 24.]) * (1 - t_) + np.array([109, 99, 74.]) * t_
    dl = np.dstack([dc, np.asarray(g2)]).astype(np.uint8); dimg = Image.alpha_composite(dimg, Image.fromarray(dl, 'RGBA'))
    dimg = np.asarray(dimg.resize((nd, nd), Image.LANCZOS)).astype(np.float32); over(c, dimg, dx_, dy_)
    over(c, SPR['fs'], *pos['fsL']); over(c, SPR['fs'], *pos['fsR'])
    img = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), 'RGBA')
    L, st = knob_layers(KD); off = int(round(0.025 * KD))
    for (kx, ky), v in zip(pos['knobs'], values):
        ang = -135 + 270 * v
        img.alpha_composite(L['shadow'].rotate(-ang, resample=Image.BICUBIC), (int(kx - KD / 2) + off, int(ky - KD / 2) + off))
        img.alpha_composite(st.rotate(-ang, resample=Image.BICUBIC), (int(kx - KD / 2), int(ky - KD / 2)))
        img.alpha_composite(L['highlight'], (int(kx - KD / 2), int(ky - KD / 2)))
    # pastille presets / ligne d'etat (Strong Pickle : 400 x 38 unites, Poppins Medium 23)
    bx, by, bw_, bh_ = pos['bar']; S = 3
    pill = Image.new('RGBA', (int(bw_ * S) + 8, int(bh_ * S) + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(pill)
    d.rounded_rectangle((4, 4, bw_ * S + 4, bh_ * S + 4), radius=bh_ * S / 2, fill=(8, 8, 9, 236), outline=(255, 255, 255, 70), width=int(2 * S))
    f = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf', int(46 * S))
    txt = '1 · Ring Mod'; tb = d.textbbox((0, 0), txt, font=f); hb = f.getbbox('H')
    d.text(((bw_ * S + 8) / 2 - (tb[0] + tb[2]) / 2, (bh_ * S + 8) / 2 - (hb[1] + hb[3]) / 2), txt, font=f, fill=(236, 236, 236, 245))
    tri = 11 * S
    for side in (-1, 1):
        cx_ = (bw_ * S + 8) / 2 + side * (bw_ * S / 2 - 34 * S); cy_ = (bh_ * S + 8) / 2
        d.polygon([(cx_ - side * tri * 0.6, cy_ - tri), (cx_ - side * tri * 0.6, cy_ + tri), (cx_ + side * tri * 0.8, cy_)], fill=(255, 255, 255, 150))
    pill = pill.resize((int(pill.width / S), int(pill.height / S)), Image.LANCZOS)
    img.alpha_composite(pill, (int(bx - pill.width / 2), int(by - pill.height / 2)))
    # logo NINE HANDS | DSP (SVG officiel blanc ; dans le plugin il est dessine en vectoriel par l'editeur)
    lg = Image.open(os.path.join(OUT, 'logo_white_1600.png')); lx, ly, lw = pos['logo']
    lg = lg.resize((int(lw), int(round(lg.height * lw / lg.width))), Image.LANCZOS)
    img.alpha_composite(lg, (int(lx - lg.width / 2), int(ly - lg.height / 2)))
    img.save(os.path.join(OUT, path))
    return img

if __name__ == '__main__':
    full = preview()
    full.resize((1175, 900), Image.LANCZOS).save(os.path.join(OUT, 'preview_half.png'))
    # Glow 25 / 50 / 75 / 100 % : zone PRESET / STATUS
    tiles = []
    for gl in (0.25, 0.5, 0.75, 1.0):
        im = preview(gl, path='preview_glow.png')
        x_a = int(pos['presetled'][0] - 180); x_b = int(pos['statusled'][0] + 220); y_a = int(pos['presetled'][1] - 120)
        tiles.append(im.crop((x_a, y_a, x_b, y_a + 240)))
    tw, th = tiles[0].size; sheet = Image.new('RGB', (tw, th * 4 + 60), (17, 17, 18)); dd = ImageDraw.Draw(sheet)
    fnt = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf', 26)
    for i, t in enumerate(tiles):
        sheet.paste(t.convert('RGB'), (0, i * (th + 20))); dd.text((14, i * (th + 20) + 8), f'Glow {25 * (i + 1)} %', font=fnt, fill=(240, 240, 240))
    sheet.save(os.path.join(OUT, 'preview_glow_sheet.png'))
    def r2(t): return [r2(v) if isinstance(v, (tuple, list)) else round(float(v) / 2, 2) for v in t]
    lay = {k: (r2(v) if isinstance(v, tuple) else v) for k, v in pos.items() if isinstance(v, tuple)}
    lay.update(knobs=[r2(p) for p in pos['knobs']], ladder=[r2(p) for p in pos['ladder']],
               modeled={k: r2(v) for k, v in pos['modeled'].items()}, faces={k: r2(v) for k, v in pos['faces'].items()},
               labels={k: r2(v) for k, v in pos['labels'].items()}, phpill=[r2(pos['phpill'][0]), r2(pos['phpill'][1])],
               jacks={k: [r2(v[:2]) for v in vs] for k, vs in jack_px.items()}, knobD=KD / 2, fsBtnR=fsBtn / 2, fsS=fsS / 2, frame=[IW / 2, IH / 2])
    json.dump(lay, open(os.path.join(OUT, 'layout.json'), 'w'), indent=1)
    print('ok')
