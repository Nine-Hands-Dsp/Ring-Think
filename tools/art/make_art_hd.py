"""
Ring Think (NINE HANDS | DSP) - image du plugin en haute definition a partir du visuel HD fourni par l'utilisateur
(hd.png, 2938 x 2250, facade sans commandes). Aucun agrandissement : le fond est le visuel tel quel.
Repere du plugin = 1175 x 900 unites, 2,5 px par unite (net jusqu'a la taille maximale de la fenetre sur ecran HiDPI).
Ajoute : jacks photo du kit, footswitchs photo du kit, sieges et LED eteintes, faces des touches, plaques de protection des LED
PRESET / STATUS ; calcule les sprites (LED, touches, inscriptions), les halos des LED et Layout.h.
"""
import os, sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import photo_controls as PC

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'hd.png')
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out_hd')
OLDLAY = os.path.join(HERE, 'layout_v3.json')          # repere de la v3.0.0 (unites)
KNOBS = os.path.join(HERE, 'knob')                       # calques du potard (ChatGPT, 1024 px)
CAP = os.path.join(HERE, 'cap_big_src.png')              # bouton MODE (sprite de la v3.0.0, 2 px / unite)
FB = os.path.join(HERE, '..', 'fonts', 'Poppins-Bold.ttf') if os.path.exists(os.path.join(HERE, '..', 'fonts', 'Poppins-Bold.ttf')) else '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
os.makedirs(DST, exist_ok=True)

PXU = 2.5                                                # pixels par unite
IW, IH = 2938, 2250
KV = IH / 924.0                                          # unites du visuel d'origine (928 px) -> pixels de cette image
hd = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.float32)
assert hd.shape[1] == IW and hd.shape[0] == IH, hd.shape
canvas = hd.copy()
L = json.load(open(OLDLAY))
Waff = np.array([[1.0005430e+00, 6.9701375e-04, -1.2425759e+00], [-2.5710929e-04, 9.9840438e-01, 9.3388993e-01]])   # v3 -> visuel HD (ECC)
def mp(u): x, y = Waff @ np.array([u[0] * PXU, u[1] * PXU, 1.0]); return (float(x), float(y))

# ---------------------------------------------------------------- positions (pixels de l'image)
pos = {}
pos['knobs'] = [mp(p) for p in L['knobs']]
# creux des LED mesures sur le visuel HD (cercles de Hough) : l'echelle de presets et les LED PRESET / STATUS
pos['ladder'] = [(1920.5, 847.5), (1922.5, 944.5), (1921.5, 1034.5), (1923.5, 1131.5), (1923.5, 1224.5),
                 (1921.5, 1313.5), (1920.5, 1411.5), (1919.5, 1501.5), (1923.5, 1599.5)]
pos['ladder'] = [(1921.6, y) for _, y in pos['ladder']]                                  # meme colonne pour les 9 LED
pos['presetled'] = (1105.5, 1838.5); pos['statusled'] = (1863.5, 1838.5)
pos['modeled'] = {k: mp(v) for k, v in L['modeled'].items()}
pos['faces'] = {k: mp(v) for k, v in L['faces'].items()}
pos['labels'] = {k: mp(v) for k, v in L['labels'].items()}
pos['ps'] = mp(L['ps']); pos['capbig'] = mp(L['capbig'])
pos['fsL'] = mp(L['fsL']); pos['fsR'] = mp(L['fsR'])
pos['phpill'] = (1865.0, 92.0, 2183.0, 164.0)                                             # contour de la pastille PHASER (mesure)
pos['phled'] = (1865.0 + 50.0, 128.0)
pos['phtxt'] = (2058.0, 128.0)
pos['bar'] = (1468.75, 1966.3, 1000.0, 95.0)                                              # pastille presets / etat (400 x 38 unites)
pos['logo'] = (1511.0, 2124.5, 575.0)                                                     # centre du cadre sombre du bas (mesure)
JACKS = {'L': [L['jacks']['L'][0][1], L['jacks']['L'][1][1]], 'R': [v[1] for v in L['jacks']['R']]}

def over(dst, spr, cx, cy, opacity=1.0):
    h, w = spr.shape[:2]; X = int(round(cx - w / 2)); Y = int(round(cy - h / 2))
    xa, ya, xb, yb = max(X, 0), max(Y, 0), min(X + w, dst.shape[1]), min(Y + h, dst.shape[0])
    if xa >= xb or ya >= yb: return
    s = spr[ya - Y:yb - Y, xa - X:xb - X]; sa = s[..., 3:4] / 255.0 * opacity
    d = dst[ya:yb, xa:xb]; da = d[..., 3:4] / 255.0
    oa = sa + da * (1 - sa)
    d[..., :3] = np.where(oa > 1e-6, (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    d[..., 3:4] = oa * 255

# ---------------------------------------------------------------- 1. nettoyage du visuel
# pastille presets : le texte imprime par ChatGPT (« 1 · Ring Mod ») est retire, le plugin dessine la sienne par-dessus
bx, by, bw, bh = pos['bar']
mk = Image.new('L', (IW, IH), 0)
ImageDraw.Draw(mk).rounded_rectangle((bx - bw / 2 - 4, by - bh / 2 - 6, bx + bw / 2 + 4, by + bh / 2 + 6), radius=bh / 2 + 6, fill=255)
m = np.asarray(mk.resize((IW, IH))).astype(np.float32)[..., None] / 255
rng = np.random.default_rng(5)
canvas[..., :3] = canvas[..., :3] * (1 - m) + (np.array([9.0, 9.0, 10.0]) + rng.normal(0, 0.8, (IH, IW, 1))) * m

# ---------------------------------------------------------------- 2. jacks photo du kit (OUT a gauche, entrees a droite), sans ombre
JACK_LEN = 75.0 * KV
for side, ys in JACKS.items():
    spr, jw, jh = PC.jack_sprite(JACK_LEN, 1, -1 if side == 'L' else +1)
    for yu in ys:
        cy = yu * PXU
        cx = jw / 2 if side == 'L' else IW - jw / 2
        over(canvas, spr, cx, cy)

# ---------------------------------------------------------------- 3. sprites
SPR = {}
ledS_off, ledS_on, _ = PC.led_sprites(9.0 * KV, 1, colour='amber')
ledP_off, ledP_on, _ = PC.led_sprites(14.0 * KV, 1, colour='amber')
ledR_off, ledR_on, _ = PC.led_sprites(14.0 * KV, 1, colour='red')
fs, fs_refl, fsS, fsBtn = PC.footswitch_sprite(112.0 * KV, 1)
SPR.update(ledS_off=ledS_off, ledS_on=ledS_on, ledP_off=ledP_off, ledP_on=ledP_on, ledR_off=ledR_off, ledR_on=ledR_on, fs=fs)

def make_face(lit):
    w, h, r, S = 44 * KV, 98 * KV, 3.2 * KV, 4
    W_, H_ = int(round(w)) + 6, int(round(h)) + 6
    yy = np.linspace(0, 1, H_ * S)[:, None]
    top, bot = (np.array([232, 56, 0.]), np.array([242, 66, 6.])) if lit else (np.array([31, 32, 33.]), np.array([39, 40, 41.]))
    col = np.broadcast_to(top + (bot - top) * yy[..., None], (H_ * S, W_ * S, 3)).copy()
    mm = Image.new('L', (W_ * S, H_ * S), 0); ImageDraw.Draw(mm).rounded_rectangle((3 * S, 3 * S, (W_ - 3) * S, (H_ - 3) * S), radius=r * S, fill=255)
    mm = np.asarray(mm).astype(np.float32) / 255
    dist = cv2.distanceTransform((mm > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / S
    gx = cv2.Sobel(mm, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(mm, cv2.CV_32F, 0, 1, ksize=5)
    facing = cv2.GaussianBlur(((gx + gy) / (np.hypot(gx, gy) + 1e-6) / 1.414), (0, 0), 2 * S)
    edge = np.clip(1 - dist / 2.2, 0, 1)[..., None]
    lightc = np.array([255, 128, 64.]) if lit else np.array([78, 79, 80.])
    darkc = np.array([150, 30, 0.]) if lit else np.array([12, 12, 13.])
    f = np.clip(facing, -1, 1)[..., None]
    col = col * (1 - edge) + edge * np.where(f > 0, col * (1 - f) + lightc * f, col * (1 + f) - darkc * f)
    col += np.random.default_rng(5).normal(0, 1.0, col.shape[:2])[..., None]
    out = np.dstack([np.clip(col, 0, 255), mm * 255]).astype(np.float32)
    out = cv2.resize(out, (W_, H_), interpolation=cv2.INTER_AREA)
    ring = cv2.GaussianBlur(cv2.dilate((out[..., 3] > 30).astype(np.float32), np.ones((3, 3))), (0, 0), 0.6)
    a_ = out[..., 3:4] / 255; ra = np.clip(ring[..., None] - a_, 0, 1) * 0.85
    oa = a_ + ra; out[..., :3] = out[..., :3] * a_ / np.maximum(oa, 1e-6); out[..., 3:4] = oa * 255
    return out
def text_sprite(txt, cap_px, rgb=(255, 255, 255), track=0.0):
    S = 4; f = ImageFont.truetype(FB, int(cap_px / 0.70 * S))
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    ws = [d0.textlength(ch, font=f) for ch in txt]; tot = sum(ws) + track * S * (len(txt) - 1)
    bb = f.getbbox('H')
    im = Image.new('L', (int(tot) + 16 * S, int(cap_px * 2 * S)), 0); dd = ImageDraw.Draw(im); x = 8 * S
    for ch, w in zip(txt, ws): dd.text((x, int(cap_px * 0.5 * S) - bb[1]), ch, font=f, fill=255); x += w + track * S
    im = im.crop(im.getbbox()); im = im.resize((max(1, im.width // S), max(1, im.height // S)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); pad = 4
    arr = np.zeros((a.shape[0] + 2 * pad, a.shape[1] + 2 * pad, 4), np.float32); arr[..., :3] = rgb; arr[pad:-pad, pad:-pad, 3] = a
    return arr
def fit_text(txt, width_px, rgb, track=0.0):
    t = text_sprite(txt, 20, rgb, track); k = width_px / (t.shape[1] - 8)
    return text_sprite(txt, 20 * k, rgb, track * k)
SPR['face_on'] = make_face(True); SPR['face_off'] = make_face(False)
for k, t in (('rm', 'RM'), ('ub', 'UB'), ('lb', 'LB')): SPR['label_' + k] = text_sprite(t, 14.5 * KV)
# inscriptions qui changent de couleur, dessinees en vectoriel (Poppins Bold) a la taille de celles du visuel
PSW = 141 * KV; PHW = (pos['phpill'][2] - pos['phpill'][0]) * 0.52
for nm, rgb in (('white', (255, 255, 255)), ('yellow', (255, 214, 0))):
    SPR['pitchshift_' + nm] = fit_text('PITCH-SHIFT', PSW, rgb, 1.0)
    SPR['phaser_' + nm] = fit_text('PHASER', PHW, rgb, 2.0)
# bouton MODE : sprite rond de la v3.0.0, reconstruit parfaitement rond, mis a l'echelle 2,5 px / unite
cap = np.asarray(Image.open(CAP).convert('RGBA')).astype(np.float32)
n = int(round(cap.shape[0] * PXU / 2.0)); pm = cap.copy(); pm[..., :3] *= pm[..., 3:4] / 255
pm = cv2.resize(pm, (n, n), interpolation=cv2.INTER_CUBIC); a_ = np.clip(pm[..., 3:4], 0, 255)
pm[..., :3] = np.where(a_ > 0.5, pm[..., :3] * 255 / np.maximum(a_, 1e-6), 0); pm[..., 3:4] = a_
SPR['cap_big'] = np.clip(pm, 0, 255)

def seat_sprite(R):
    S = 4; nn = int(R * 3.2) | 1; c = nn * S / 2
    yy, xx = np.mgrid[0:nn * S, 0:nn * S].astype(np.float32); d = np.hypot(xx - c, yy - c) / S
    lit_ = np.clip(np.cos(np.arctan2(yy - c, xx - c) - np.pi / 4), 0, 1)
    ro = 1.16 * R; a_ = np.clip((ro - d) * 1.5, 0, 1)
    rim = np.clip(1 - np.abs(d - (ro - 0.9)) / 0.9, 0, 1) * lit_
    col = np.zeros((nn * S, nn * S, 3), np.float32) + 4 + rim[..., None] * 70
    return cv2.resize(np.dstack([col, a_ * 235]), (nn, nn), interpolation=cv2.INTER_AREA)
SPR['seatS'] = seat_sprite(9.0 * KV); SPR['seatP'] = seat_sprite(14.0 * KV)

# ---------------------------------------------------------------- 4. fond : plaques de protection des LED, sieges, LED eteintes, faces, footswitchs
def led_plate(c, R):
    S4 = 4; hw = 1.62 * R; rad = 0.62 * hw; pad = 12
    W_ = H_ = int(2 * hw) + 2 * pad
    im_ = Image.new('L', (W_ * S4, H_ * S4), 0)
    ImageDraw.Draw(im_).rounded_rectangle((pad * S4, pad * S4, (W_ - pad) * S4, (H_ - pad) * S4), radius=rad * S4, fill=255)
    m_ = np.asarray(im_.resize((W_, H_), Image.LANCZOS)).astype(np.float32) / 255
    sh_ = cv2.GaussianBlur(np.roll(np.roll(m_, 2, 0), 2, 1), (0, 0), 3) * 0.55 * (1 - m_)
    ed_ = np.clip(m_ - cv2.erode(m_, np.ones((3, 3))), 0, 1)
    yy_, xx_ = np.mgrid[0:H_, 0:W_]; lit = np.clip(((xx_ - W_ / 2) + (yy_ - H_ / 2)) / (W_ / 2), 0, 1)
    col = np.zeros((H_, W_, 3), np.float32) + 8.0 + (ed_ * (18 + 40 * lit))[..., None]
    over(canvas, np.dstack([np.where(m_[..., None] > 0.01, col, 0), np.clip(m_ * 0.97 + sh_, 0, 1) * 255]), c[0], c[1])
led_plate(pos['presetled'], 14.0 * KV); led_plate(pos['statusled'], 14.0 * KV)
bg = canvas
for k in ('rm', 'ub', 'lb'): over(bg, SPR['face_off'], *pos['faces'][k])
for p in pos['ladder'] + list(pos['modeled'].values()) + [pos['phled']]: over(bg, SPR['seatS'], *p)
for p in (pos['presetled'], pos['statusled']): over(bg, SPR['seatP'], *p)
for p in pos['ladder'] + [pos['phled']]: over(bg, SPR['ledS_off'], *p)
over(bg, SPR['ledP_off'], *pos['presetled']); over(bg, SPR['ledR_off'], *pos['statusled'])
over(bg, SPR['fs'], *pos['fsL']); over(bg, SPR['fs'], *pos['fsR'])

def save(arr, name): Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(DST, name), optimize=True)
save(bg, 'background.png')
for nm in ('ledS_on', 'ledS_off', 'ledP_on', 'ledR_on', 'face_on', 'label_rm', 'label_ub', 'label_lb',
           'pitchshift_white', 'pitchshift_yellow', 'phaser_white', 'phaser_yellow', 'cap_big'):
    save(SPR[nm], nm + '.png')

# ---------------------------------------------------------------- 5. halos des LED (la facade recoit la lumiere ; doses par Glow)
bg_rgb = bg[..., :3]
def led_glow(c, col, R):
    nn = int(R * 14); X = int(c[0] - nn / 2); Y = int(c[1] - nn / 2)
    yy, xx = np.mgrid[0:nn, 0:nn].astype(np.float32); d = np.hypot(xx - nn / 2, yy - nn / 2)
    def lamb(h): return (h * h / (h * h + d * d)) ** 1.5
    E = 0.8 * (4.5 * lamb(1.4 * R) + 1.1 * lamb(5.0 * R)) * np.clip((d - 0.9 * R) / (0.25 * R), 0, 1)
    ya, xa = max(Y, 0), max(X, 0)
    sub = bg_rgb[ya:Y + nn, xa:X + nn]; E = E[ya - Y:ya - Y + sub.shape[0], xa - X:xa - X + sub.shape[1]]
    colv = np.array(col, np.float32) / 255.0
    smooth = cv2.GaussianBlur(sub, (0, 0), 2.5)
    add = (smooth * 2.2 + 0.5 * (sub - smooth).clip(-20, 20) + 18.0) * E[..., None] * colv
    halo = 0.8 * 110.0 * (0.9 * R / np.maximum(d, 0.9 * R)) ** 2.2
    add += halo[ya - Y:ya - Y + sub.shape[0], xa - X:xa - X + sub.shape[1], None] * colv
    out = np.zeros(sub.shape[:2] + (4,), np.float32)
    out[..., :3] = np.clip(sub + add, 0, 255); out[..., 3] = np.clip(add.max(2) / 255.0, 0, 1) * 255
    return out, (xa, ya)
AMBER = (255, 140, 40); RED = (255, 40, 30)
glows = []
def glow(name, p, col, R):
    g, (gx, gy) = led_glow(p, col, R); save(g, 'glow_' + name + '.png')
    glows.append((name, gx / PXU, gy / PXU, g.shape[1] / PXU, g.shape[0] / PXU))
for i, p in enumerate(pos['ladder']): glow('lad%d' % i, p, AMBER, 9.0 * KV)
for k in ('rm', 'ub', 'lb'): glow('mode_' + k, pos['modeled'][k], AMBER, 9.0 * KV)
glow('phaser', pos['phled'], AMBER, 9.0 * KV * 0.8)
glow('preset', pos['presetled'], AMBER, 14.0 * KV)
glow('status', pos['statusled'], RED, 14.0 * KV)
for nm in ('shadow', 'crown', 'cap', 'marker', 'highlight'):
    Image.open(os.path.join(KNOBS, 'ring_knob_' + nm + '.png')).resize((512, 512), Image.LANCZOS).save(os.path.join(DST, 'knob_' + nm + '.png'), optimize=True)

# ---------------------------------------------------------------- 6. Layout.h et layout.json (unites)
U = lambda v: v / PXU
def pt(p): return '{ %.2ff, %.2ff }' % (U(p[0]), U(p[1]))
KD = 169 * KV                                            # le potard anime couvre entierement le potard d'origine
Ls = ['// genere par tools/art/make_art_hd.py - ne pas modifier a la main (repere 1175 x 900 unites, images 2,5 px / unite)',
      '#pragma once\n#include <juce_graphics/juce_graphics.h>\nnamespace layout\n{',
      '    constexpr float frameW = 1175.0f, frameH = 900.0f, pxPerUnit = %.2ff;' % PXU,
      '    const juce::Point<float> knobPos[5] = { %s };' % ', '.join(pt(p) for p in pos['knobs']),
      '    constexpr float knobD = %.2ff;' % U(KD),
      '    const juce::Point<float> capPos %s; constexpr float capD = %.2ff, capDotR = %.2ff;   // bouton MODE' % (pt(pos['capbig']), U(SPR['cap_big'].shape[1]), U(41.0 * KV)),
      '    const juce::Point<float> ladder[9] = { %s };' % ', '.join(pt(p) for p in pos['ladder']),
      '    const juce::Point<float> modeLed[3] = { %s, %s, %s };   // RM, UB, LB' % tuple(pt(pos['modeled'][k]) for k in ('rm', 'ub', 'lb')),
      '    const juce::Point<float> face[3] = { %s, %s, %s };' % tuple(pt(pos['faces'][k]) for k in ('rm', 'ub', 'lb')),
      '    constexpr float faceW = %.2ff, faceH = %.2ff;' % (U(44 * KV), U(98 * KV)),
      '    const juce::Point<float> label[3] = { %s, %s, %s };' % tuple(pt(pos['labels'][k]) for k in ('rm', 'ub', 'lb')),
      '    const juce::Point<float> psPos %s, phLed %s, phTxt %s;' % (pt(pos['ps']), pt(pos['phled']), pt(pos['phtxt'])),
      '    const juce::Rectangle<float> phPill { %.2ff, %.2ff, %.2ff, %.2ff };' % (U(pos['phpill'][0]), U(pos['phpill'][1]), U(pos['phpill'][2] - pos['phpill'][0]), U(pos['phpill'][3] - pos['phpill'][1])),
      '    const juce::Point<float> presetLed %s, statusLed %s;' % (pt(pos['presetled']), pt(pos['statusled'])),
      '    const juce::Point<float> fsL %s, fsR %s;' % (pt(pos['fsL']), pt(pos['fsR'])),
      '    constexpr float footR = %.2ff;   // rayon du bouton du footswitch' % U(fsBtn),
      '    const juce::Rectangle<float> presetRect { %.2ff, %.2ff, 400.0f, 38.0f };   // pastille presets / ligne d\'etat (Strong Pickle)' % (U(bx) - 200, U(by) - 19),
      '    constexpr float presetFont = 23.0f;',
      '    const juce::Point<float> logoPos %s; constexpr float logoW = %.2ff;' % (pt(pos['logo'][:2]), U(pos['logo'][2])),
      '    struct GlowRect { const char* name; float x, y, w, h; };',
      '    const GlowRect glow[%d] = { %s };' % (len(glows), ', '.join('{ "%s", %.2ff, %.2ff, %.2ff, %.2ff }' % g for g in glows)),
      '    const juce::Rectangle<float> boxRect { 12.0f, 0.0f, 1151.0f, 900.0f };   // boitier (notice)',
      '}']
open(os.path.join(DST, 'Layout.h'), 'w').write('\n'.join(Ls) + '\n')
lay = {'presetled': [U(v) for v in pos['presetled']], 'statusled': [U(v) for v in pos['statusled']], 'capbig': [U(v) for v in pos['capbig']],
       'fsL': [U(v) for v in pos['fsL']], 'fsR': [U(v) for v in pos['fsR']], 'ps': [U(v) for v in pos['ps']],
       'phpill': [[U(pos['phpill'][0]), U((pos['phpill'][1] + pos['phpill'][3]) / 2)], [U(pos['phpill'][2]), U((pos['phpill'][1] + pos['phpill'][3]) / 2)]],
       'phled': [U(v) for v in pos['phled']], 'bar': [U(bx), U(by), 400.0, 38.0], 'logo': [U(pos['logo'][0]), U(pos['logo'][1]), U(pos['logo'][2])],
       'knobs': [[U(a), U(b)] for a, b in pos['knobs']], 'ladder': [[U(a), U(b)] for a, b in pos['ladder']],
       'modeled': {k: [U(a), U(b)] for k, (a, b) in pos['modeled'].items()}, 'faces': {k: [U(a), U(b)] for k, (a, b) in pos['faces'].items()},
       'jacks': L['jacks'], 'knobD': U(KD), 'frame': [1175.0, 900.0]}
json.dump(lay, open(os.path.join(DST, 'layout.json'), 'w'), indent=1)
print('ok', DST)
