"""
Ring Think - retouches du visuel nettoye (avant elargissement) : out/pedal_clean.npy -> out/pedal_clean2.npy
  1. ancienne encoche du 9V (en haut au centre) : la plaque superieure reprend sa forme normale,
     bord bas a gauche prolonge puis chanfrein a 45 degres jusqu'au niveau de droite (comme les autres rainures)
  2. bandeau du bas (ancien MADE BY STUDIO WIGA, sous le logo) : fond du bandeau refait proprement, sans taches
"""
import os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out')
a = np.load(os.path.join(OUT, 'pedal_clean.npy')).astype(np.float32)
src = a.copy()
rng = np.random.default_rng(7)

# 1. encoche du 9V : colonnes 503..616, lignes 18..84
Y0, Y1 = 29, 70                        # plaque superieure seulement (la rainure du dessous n'est pas touchee)
LBLK = (380, 496)                       # plaque de gauche saine (bord bas ligne 66)
RBLK = (640, 720)                       # plaque de droite saine (bord bas ligne 57)
X_A, X_CH, X_B = 503, 600, 622          # debut, debut du chanfrein (9 px), fin de la zone refaite
def col_left(x):  return src[Y0:Y1, LBLK[0] + (x - X_A) % (LBLK[1] - LBLK[0])]
def col_right(x): return src[Y0:Y1, RBLK[0] + (x - X_A) % (RBLK[1] - RBLK[0])]
EL, ER = 66, 57                         # bord bas de la plaque a gauche / a droite
for x in range(X_A, X_B):
    cl, cr = col_left(x), col_right(x)
    w = np.clip((x - (X_CH - 4)) / 12.0, 0, 1)           # fondu de la matiere gauche -> droite sur 12 colonnes
    c = cl * (1 - w) + cr * w
    s_ = int(np.clip(x - X_CH + 1, 0, EL - ER))           # chanfrein : le bord remonte d'une ligne par colonne (45 degres)
    if s_ > 0:
        e = EL - s_
        below = cl[EL - Y0 - 1:]                          # arete + creux sous la plaque (profil de gauche)
        c = c.copy(); n = min(len(below), Y1 - (e - 1))
        c[e - 1 - Y0:e - 1 - Y0 + n] = below[:n]
    a[Y0:Y1, x] = c
for k in range(4):                                        # raccords doux aux deux bouts
    t = (k + 1) / 5
    a[Y0:Y1, X_A + k] = a[Y0:Y1, X_A + k] * t + src[Y0:Y1, X_A + k] * (1 - t)
    a[Y0:Y1, X_B - 1 - k] = a[Y0:Y1, X_B - 1 - k] * t + src[Y0:Y1, X_B - 1 - k] * (1 - t)

# 2. fond du bandeau du bas : lignes 864..887, colonnes 446..727
xs = np.arange(440, 734)
for y in range(853, 863):                                 # plaque au-dessus du bandeau : grain repris a gauche (meme ligne)
    a[y, 440:734] = np.median(src[y, 250:425], axis=0) + rng.normal(0, 1.6, (len(xs), 1))
for y in range(863, 888):                                 # fond du bandeau : teinte interpolee entre les deux bouts propres
    lv = src[y, 428:440].mean(0); rv = src[y, 736:748].mean(0)
    t = ((xs - 440) / (733 - 440))[:, None]
    a[y, 440:734] = lv * (1 - t) + rv * t + rng.normal(0, 0.8, (len(xs), 1))

# 3. barre sombre derriere les LED PRESET / STATUS : reconstruite en continu (plus de zone sombre ni de cercle
#    laisses par l'effacement de l'ancienne LED) ; colonnes reprises de la partie saine de la barre, du cote libre
R0, R1 = 732, 786
def fill(xa, xb, tile):
    tw = tile[1] - tile[0]
    for x in range(xa, xb): a[R0:R1, x] = src[R0:R1, tile[0] + (x - xa) % tw]
def soft(xa, xb):
    for k in range(4):
        t = (k + 1) / 5
        a[R0:R1, xa + k] = a[R0:R1, xa + k] * t + src[R0:R1, xa + k] * (1 - t)
        a[R0:R1, xb - 1 - k] = a[R0:R1, xb - 1 - k] * t + src[R0:R1, xb - 1 - k] * (1 - t)
# STATUS : la barre de gauche passe derriere la LED jusqu'a son petit bout droit
cs = 714; fill(cs - 30, cs + 20, (cs - 62, cs - 31)); soft(cs - 30, cs + 20)
# PRESET : petite barre depuis le texte jusqu'a la LED, puis la grande plaque commence sous la LED (raccord cache)
cp = 406
def fill_flat(xa, xb, tile, grain=1.2):
    prof = np.median(src[R0:R1, tile[0]:tile[1]], axis=1)          # profil vertical constant (pas de motif repete)
    for x in range(xa, xb): a[R0:R1, x] = prof + rng.normal(0, grain, (R1 - R0, 1))
fill_flat(cp - 26, cp, (cp - 34, cp - 27))
fill_flat(cp, cp + 17, (cp + 17, cp + 21))
# la plaque s'arrete en arc autour de la LED (comme sur le visuel d'origine) : creux sombre concentrique
cy_p = 758.6; left_prof = np.median(src[R0:R1, cp - 34:cp - 27], axis=1)
for x in range(cp - 2, cp + 26):
    for y in range(R0, R1):
        d = np.hypot(x - cp, y - cy_p)
        t = np.clip((23.5 - d) / 1.4, 0, 1)
        if t > 0: a[y, x] = a[y, x] * (1 - t) + left_prof[y - R0] * t
for x in range(cp, cp + 17):                              # pas de bout de plaque au-dessus de l'arc
    a[R0:738, x] = left_prof[:738 - R0]
soft(cp - 26, cp + 17)

# 5. arete de la rainure sous le C de COARSE : petit decrochement (x 765..775) remis droit
for x in range(765, 776):
    a[313:323, x] = src[313:323, 760 - (x - 765) % 8]
for x in range(740, 800):                                 # luminosite de l'arete en fondu (pas de marche)
    t = np.clip((x - 740) / 60.0, 0, 1)
    for y in (315, 316, 317):
        ref_l = src[y, 736:744].mean(0); ref_r = src[y, 800:808].mean(0)
        a[y, x] = ref_l * (1 - t) + ref_r * t + rng.normal(0, 0.8, 3)

# 6. STATUS remonte de 2 px (au niveau de PRESET : capitales 750..767)
SX0, SX1, SY0, SY1, SDY = 746, 840, 746, 773, 2
sub = a[SY0:SY1, SX0:SX1].copy(); lum = sub.mean(2)
alpha = np.clip((lum - 40) / 190, 0, 1)[..., None]
plate = np.array([np.median(sub[y][lum[y] < 30], axis=0) if (lum[y] < 30).sum() > 5 else sub[y].min(0) for y in range(SY1 - SY0)])
clean = plate[:, None, :] + rng.normal(0, 0.6, sub.shape[:2] + (1,))
alpha2 = np.zeros_like(alpha); txt2 = np.zeros_like(sub)
alpha2[:-SDY] = alpha[SDY:]; txt2[:-SDY] = (sub * alpha)[SDY:]
a[SY0:SY1, SX0:SX1] = clean * (1 - alpha2) + txt2

# 4. BYPASS remonte de 2 px pour etre au niveau de PRESET / TUNE (meme hauteur de capitales 864..881)
BX0, BX1, BY0, BY1, DY = 864, 968, 860, 887, 2
sub = a[BY0:BY1, BX0:BX1].copy(); lum = sub.mean(2)
alpha = np.clip((lum - 40) / 190, 0, 1)[..., None]
plate = np.array([np.median(sub[y][lum[y] < 25], axis=0) if (lum[y] < 25).sum() > 5 else sub[y].min(0) for y in range(BY1 - BY0)])
clean = plate[:, None, :] + rng.normal(0, 0.6, sub.shape[:2] + (1,))
txt = sub * alpha
alpha2 = np.zeros_like(alpha); txt2 = np.zeros_like(txt)
alpha2[:-DY] = alpha[DY:]; txt2[:-DY] = txt[DY:]
a[BY0:BY1, BX0:BX1] = clean * (1 - alpha2) + txt2

np.save(os.path.join(OUT, 'pedal_clean2.npy'), a)
print('ok')
