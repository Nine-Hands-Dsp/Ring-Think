# RING THINK (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin (tools/render).
# Usage : python3 tools/manual.py [<dossier des captures tools/render>] [<fichier PDF de sortie>]
#   sans dossier de captures : reprend les captures de tools/manual_assets/.
#   sortie par defaut : docs/RingThink_Notice_FR_v<version>.pdf (version lue dans CMakeLists.txt)
import os, sys, re, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, KeepTogether, CondPageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
VERSION = re.search(r"project\s*\(\s*\w+\s+VERSION\s+([0-9.]+)", open(os.path.join(ROOT, "CMakeLists.txt")).read()).group(1)
args = sys.argv[1:]
SHOTS = args[0] if args and os.path.isdir(args[0]) else None
OUT = [a for a in args if a.endswith(".pdf")]
OUT = OUT[0] if OUT else os.path.join(ROOT, "docs", "RingThink_Notice_FR_v" + VERSION + ".pdf")
FONTS = os.path.join(HERE, "fonts"); ASSETS = os.path.join(HERE, "manual_assets")
TMP = os.path.join(ASSETS, "_build"); os.makedirs(TMP, exist_ok=True)

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#F2541B"); ACC_L = colors.HexColor("#FF9A5C")          # orange du titre RING THINK
DARK = colors.HexColor("#1B1A19"); GREY = colors.HexColor("#6A6662"); LIGHT = colors.HexColor("#F6EEE8")
LAY = json.load(open(os.path.join(HERE, "layout.json")))                     # repere du plugin : 1175 x 900 unites
LOGO_PNG = os.path.join(ASSETS, "logo_white.png")

SHOT_NAMES = ["ringthink_100.png", "ringthink_status.png", "ringthink_preset4_bypass.png", "ringthink_modes.png",
              "ringthink_menu.png", "ringthink_menu_glow.png"]
if SHOTS:
    for n in SHOT_NAMES: shutil.copy(os.path.join(SHOTS, n), os.path.join(ASSETS, n))
def shot(n): return Image.open(os.path.join(ASSETS, n)).convert("RGB")

# ---------------------------------------------------------------- illustrations (rendu reel du plugin)
src = shot("ringthink_100.png"); k = src.height / 900.0
def crop_u(im, box): return im.crop(tuple(int(round(v * k)) for v in box))
def strip(parts, name, gap=18):
    s = Image.new("RGB", (sum(p.width for p in parts) + gap * (len(parts) - 1), max(p.height for p in parts)), (255, 255, 255))
    x = 0
    for p in parts: s.paste(p, (x, 0)); x += p.width + gap
    path = os.path.join(TMP, name); s.save(path); return path

kn = LAY["knobs"]; ld = LAY["ladder"]; md = LAY["modeled"]; cap = LAY["capbig"]
bx, by, bw, bh = LAY["bar"]
marks = [(1, kn[0][0] - 62, kn[0][1] - 80), (2, kn[1][0] - 70, kn[1][1] - 92), (3, kn[2][0] + 70, kn[2][1] - 76), (4, kn[3][0] + 70, kn[3][1] - 76),
         (5, kn[4][0] + 66, kn[4][1] - 76), (6, cap[0] - 82, cap[1] - 20), (7, md["rm"][0] - 34, md["rm"][1] + 66), (8, LAY["ps"][0] - 92, LAY["ps"][1]),
         (9, ld[0][0] - 30, ld[4][1]), (10, LAY["phpill"][0][0] - 22, LAY["phpill"][0][1]), (11, LAY["presetled"][0], LAY["presetled"][1] - 34),
         (12, LAY["statusled"][0], LAY["statusled"][1] - 34), (13, LAY["fsL"][0] - 92, LAY["fsL"][1]), (14, LAY["fsR"][0] + 92, LAY["fsR"][1]),
         (15, bx - bw / 2 - 22, by), (16, 52, 470), (17, 1122, 380)]
ann = src.copy(); dr = ImageDraw.Draw(ann)
fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), int(15 * k))
for n, x, y in marks:
    cx, cy, r = x * k, y * k, 16 * k
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(242, 84, 27), width=int(3 * k))
    dr.text((cx, cy + 1), str(n), font=fnt, fill=(27, 26, 25), anchor="mm")
annotated = os.path.join(TMP, "annotated.png"); ann.save(annotated)

knob_box = lambda i: (kn[i][0] - 92, kn[i][1] - 100, kn[i][0] + 92, kn[i][1] + 118)
knobs_img = [os.path.join(TMP, f"knob{i}.png") for i in range(5)]
for i in range(5): crop_u(src, knob_box(i)).save(knobs_img[i])
mode_img = strip([crop_u(src, (cap[0] - 112, 60, cap[0] + 110, 430)), crop_u(shot("ringthink_modes.png"), (cap[0] - 112, 60, cap[0] + 110, 430))], "modes.png")
lad_img = strip([crop_u(src, (ld[0][0] - 40, ld[0][1] - 26, ld[0][0] + 180, ld[8][1] + 26))], "ladder.png")
fs_box = (LAY["fsL"][0] - 110, LAY["presetled"][1] - 40, LAY["fsR"][0] + 115, 880)
fs_img = strip([crop_u(shot("ringthink_preset4_bypass.png"), fs_box), crop_u(src, fs_box)], "footswitches.png")
bar_box = (bx - bw / 2 - 8, by - bh / 2 - 8, bx + bw / 2 + 8, by + bh / 2 + 8)
bar_img = strip([crop_u(src, bar_box), crop_u(shot("ringthink_status.png"), bar_box)], "bar.png")
ph_img = strip([crop_u(src, (LAY["phpill"][0][0] - 10, 30, LAY["phpill"][1][0] + 10, 74)),
                crop_u(shot("ringthink_modes.png"), (LAY["phpill"][0][0] - 10, 30, LAY["phpill"][1][0] + 10, 74))], "phaser.png")
menu_img = strip([shot("ringthink_menu.png"), shot("ringthink_menu_glow.png")], "menus.png", gap=24)

# couverture : pedale detouree avec le canal alpha du fond (boitier + jacks), reflet au sol, halo orange tres doux
bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a); cut = cut.crop(cut.getbbox())
cw, ch = cut.size; pad = int(cw * 0.16)
canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
glow = np.exp(-(((xx - canvas.width / 2) / (cw * 0.62)) ** 2 + ((yy - pad - ch * 0.45) / (ch * 0.48)) ** 2)) * 30
glow *= np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1) ** 2
canvas = Image.alpha_composite(canvas, Image.fromarray(np.dstack([glow * 0.95, glow * 0.36, glow * 0.12, np.full_like(glow, 255)]).astype(np.uint8), "RGBA"))
refl = cut.transpose(Image.FLIP_TOP_BOTTOM); ra = np.array(refl).astype(np.float64)
ra[..., 3] *= (np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22)[:, None]
canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
canvas.alpha_composite(cut, (pad, pad))
canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
cover = os.path.join(TMP, "cover_cutout.png"); canvas.convert("RGB").save(cover)

def img(path, width):
    im = Image.open(path); return RLImage(path, width=width, height=width * im.height / im.width)

# ---------------------------------------------------------------- styles
st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=9, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "tip": ParagraphStyle("tip", fontName="Pop", fontSize=9.0, leading=12.4, textColor=DARK, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cells": ParagraphStyle("cells", fontName="Pop", fontSize=7.6, leading=9.6, textColor=DARK),
    "cellbs": ParagraphStyle("cellbs", fontName="PopM", fontSize=7.6, leading=9.6, textColor=DARK),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items, s="p"): return [P("&bull;&nbsp;&nbsp;" + i, s) for i in items]
def table(rows, widths, header=True, small=False):
    data = [[P(c, ("cellbs" if small else "cellb") if (header and r == 0) else ("cells" if small else "cell")) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E3D6CC")),
             ("TOPPADDING", (0, 0), (-1, -1), 2 if small else 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if small else 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
W = A4[0] - 36 * mm
def side(image, iw, flow):
    t = Table([[img(image, iw), flow]], colWidths=[iw + 5 * mm, W - iw - 5 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])); return t

# ---------------------------------------------------------------- contenu (identique au code livre)
f = [NextPageTemplate("p"), Spacer(1, 1), PageBreak()]
f += [P("1. Présentation", "h1"),
      P("<b>Ring Think</b> est un plugin de modulation NINE HANDS | DSP inspiré de l'<b>Electro-Harmonix Ring Thing</b>, modulateur à bande latérale unique construit autour du circuit EHX « Frequency Analyzer ». Dans une pédale au format double, il réunit un <b>modulateur en anneau</b>, un <b>décaleur de fréquence à bande latérale unique</b> (bande supérieure et inférieure), un <b>pitch shifter</b> et un <b>phaser</b> : du trémolo ou chorus discret jusqu'aux cloches, robots et timbres métalliques les plus extrêmes."),
      P("<b>Caractère sonore.</b> RM donne le son métallique et inharmonique classique du ring mod ; UB / LB décalent chaque partiel du même nombre de hertz (balayages « barber-pole », battements façon Uni-Vibe à très basse fréquence) ; le pitch shifter couvre désaccord, chorus, vibrato, cabine tournante et octaves ; le phaser ajoute un balayage liquide à six étages."),
      P("Le plugin <b>s'ouvre sur le son « Ring Mod »</b> (preset 1, moteur RM) : on entend tout de suite un vrai modulateur en anneau."),
      P("Trajet du signal", "h2"),
      P("Le moteur anneau / bandes latérales (RM · UB · LB + filtre passe-bas 18 dB/oct), le moteur Pitch-Shift (transposition + LFO) et le moteur Phaser (six étages passe-tout + balayage) travaillent en parallèle à partir de l'entrée. Leurs sorties sont additionnées avec compensation de niveau, puis mélangées au son direct par <b>Blend</b>. Le footswitch <b>Bypass</b> fait entrer et sortir tout l'effet en fondu. Sans moteur actif, le signal passe tel quel."),
      P("2. Installation", "h1"),
      P("Windows", "h2"),
      P("Téléchargez <b>RingThink-VST3-Windows.zip</b> (bouton « Télécharger Windows » du dépôt GitHub Nine-Hands-Dsp/Ring-Think : il donne toujours la dernière version), décompressez-le et copiez <b>Ring Think.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3\\</b>."),
      P("macOS", "h2"),
      P("Téléchargez <b>RingThink-VST3-macOS.zip</b> (binaire universel, Apple Silicon et Intel). Copiez <b>Ring Think.vst3</b> dans <b>/Library/Audio/Plug-Ins/VST3/</b> et <b>Ring Think.component</b> (Audio Unit, pour Logic / GarageBand) dans <b>/Library/Audio/Plug-Ins/Components/</b>. Le plugin n'est pas notarié par Apple : dans le Terminal, lancez une fois <b>xattr -cr \"/Library/Audio/Plug-Ins/VST3/Ring Think.vst3\"</b> (et la même commande pour le .component)."),
      P("Reaper", "h2"),
      P("Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Le plugin apparaît sous le nom <b>Ring Think (NINE HANDS | DSP)</b>. Pour le MIDI (M-Vave Chocolate Plus, pédales d'expression), la piste doit recevoir le MIDI de votre contrôleur (piste armée ou monitoring d'entrée, entrée MIDI réglée sur votre appareil)."),
      PageBreak()]
f += [P("3. Vue d'ensemble de l'interface", "h1"), img(annotated, W), Spacer(1, 3 * mm),
      table([["#", "Commande", "Rôle", "#", "Commande", "Rôle"],
             ["1", "BLEND", "Mélange direct / traité", "10", "PHASER", "Moteur phaser (LED + inscription jaune)"],
             ["2", "WAVE", "Forme d'onde de la porteuse ou du LFO", "11", "LED PRESET", "Fixe, clignote : réglages modifiés, accord"],
             ["3", "FILTER / RATE", "Filtre passe-bas ou vitesse du LFO", "12", "LED STATUS", "Rouge = effet actif"],
             ["4", "FINE / DEPTH", "Réglage fin ou profondeur du LFO", "13", "PRESET / TUNE", "Footswitch : preset suivant, maintien = accord"],
             ["5", "COARSE", "Porteuse, transposition ou centre du phaser", "14", "BYPASS", "Footswitch : effet on / off"],
             ["6", "Bouton MODE", "Tourner : presets · appui : moteurs · maintien : sauvegarde", "15", "Pastille", "Barre de presets / ligne d'état"],
             ["7", "RM · UB · LB", "Touches des moteurs anneau / bandes latérales", "16", "OUTPUTS", "Jacks MONO / L et R (décoratifs)"],
             ["8", "PITCH-SHIFT", "Moteur pitch-shift (jaune = actif)", "17", "INPUTS", "Jacks INST, MOD, EXP (décoratifs)"],
             ["9", "Échelle", "Presets 1 à 9, un clic charge", "", "", ""]],
            [7 * mm, 25 * mm, None, 8 * mm, 25 * mm, 50 * mm], small=True),
      Spacer(1, 2 * mm),
      P("Tirez un potard verticalement pour le régler (Maj = réglage fin), molette, double-clic = valeur par défaut. Les potards tournent avec leur ombre et un léger flou de mouvement ; la lumière reste fixe, en haut à gauche. <b>Clic droit sur une commande</b> : son menu MIDI Learn ; clic droit ailleurs : menu principal (section 7)."),
      PageBreak()]
KN = [("BLEND", "Mélange entre le signal direct et le signal traité, commun à tous les moteurs. 0 % = direct seul ; 100 % = traité seul (vibrato pur ou modulation en anneau totale). Pour le phaser, 50 % donne les creux les plus profonds. Défaut 60 %."),
      ("WAVE", "Forme d'onde, cinq formes enchaînées en continu : carré (0 %), sinus (25 %), rampe descendante (50 %), rampe montante (juste au-dessus de 50 %), triangle (100 %). En RM elle colore le timbre ; en UB / LB elle ajoute des harmoniques à la porteuse (50 % = décalage parfaitement pur) ; en PS / PH c'est la forme du LFO. Défaut 25 % (sinus)."),
      ("FILTER / RATE", "<b>RM · UB · LB</b> : filtre passe-bas 18 dB/oct, de 20 Hz à 20 kHz (grand ouvert vers 98 %). <b>PS</b> : vitesse du LFO, 0,1 à 500 Hz ; sous 2 % le LFO est arrêté et Fine/Depth devient un réglage fin. <b>PH</b> : vitesse du balayage, 0,05 à 10 Hz. Défaut 80 %."),
      ("FINE / DEPTH", "<b>RM · UB · LB</b> : accord fin de la porteuse, ±16,5 % autour de Coarse (50 % = aucune correction). <b>PS</b> : LFO actif, profondeur 0 à 150 cents ; LFO arrêté, réglage fin ±100 cents. <b>PH</b> : largeur du balayage, 0 à ±2 octaves. Défaut 50 %."),
      ("COARSE", "<b>RM · UB · LB</b> : porteuse de 0,1 Hz à 2 390 Hz (sous 20 Hz : trémolo, vibe, phasing ; au-dessus : timbres inharmoniques). <b>PS</b> : transposition en demi-tons, −24 à +24 (25 % = −12, 50 % = 0, 75 % = +12). <b>PH</b> : centre du balayage, 200 Hz à 4 kHz. Défaut 80 % (porteuse 318 Hz).")]
f += [P("4. Les commandes une par une", "h1"),
      P("Chaque potard agit selon les moteurs actifs : anneau / bandes latérales (<b>RM · UB · LB</b>), <b>Pitch-Shift (PS)</b> ou <b>Phaser (PH)</b>. Les pourcentages se rapportent à la course du potard (0 % = tout à gauche).")]
for i, (h, x) in enumerate(KN): f.append(side(knobs_img[i], 30 * mm, [P(h, "h2"), P(x)]))
f += [P("Valeurs de Filter / Rate", "h2"),
      table([["Potard", "Coupure (RM·UB·LB)", "Vitesse LFO (PS)", "Balayage (PH)"], ["0 %", "20,0 Hz", "LFO arrêté", "0,05 Hz"], ["30 %", "159 Hz", "1,14 Hz", "0,25 Hz"],
             ["50 %", "632 Hz", "6,48 Hz", "0,71 Hz"], ["75 %", "3,56 kHz", "56,9 Hz", "2,66 Hz"], ["100 %", "ouvert", "500 Hz", "10,0 Hz"]], [24 * mm, None, 45 * mm, 45 * mm], small=True),
      P("Valeurs de Coarse", "h2"),
      table([["Potard", "0 %", "25 %", "38 %", "50 %", "70 %", "80 %", "100 %"],
             ["Porteuse (Fine 50 %)", "0,10 Hz", "1,24 Hz", "4,61 Hz", "15,5 Hz", "116 Hz", "318 Hz", "2,39 kHz"],
             ["Transposition (PS)", "−24 dt", "−12 dt", "−6 dt", "0 dt", "+10 dt", "+14 dt", "+24 dt"],
             ["Centre phaser (PH)", "200 Hz", "423 Hz", "624 Hz", "894 Hz", "1,63 kHz", "2,20 kHz", "4,00 kHz"]], [38 * mm] + [None] * 7, small=True),
      CondPageBreak(110 * mm),
      P("Les cinq moteurs", "h2"),
      table([["Moteur", "Ce qu'il fait", "Pour commencer"],
             ["<b>RM</b> Modulation en anneau", "Le signal est multiplié par la porteuse : la note laisse place aux fréquences somme et différence. Cloches, métal, robots ; trémolo à basse fréquence.", "Coarse 70–80 %, Wave sinus, Filter 60–80 %, Blend 50–60 %"],
             ["<b>UB</b> Bande supérieure", "Ne garde que la somme : chaque partiel monte du même nombre de hertz. « Barber-pole » à très basse fréquence.", "Coarse 25–40 %, Wave 50 %, Blend 50 %"],
             ["<b>LB</b> Bande inférieure", "Ne garde que la différence : décalage vers le bas ; mélangé au direct à très basse fréquence, il bat comme un Uni-Vibe.", "Coarse 30–40 %, Wave 50 %, Blend 50 %"],
             ["<b>PS</b> Pitch-Shift", "Transpose sans changer la durée ; sur une note seule, la fenêtre se cale sur la période de la note (octaves justes) ; LFO pour vibrato, chorus, cabine tournante.", "Coarse 25 % ou 75 % (octave), Filter/Rate 0 %, Blend 50 %"],
             ["<b>PH</b> Phaser", "Six étages passe-tout, réinjection 40 % ; Filter/Rate = vitesse, Fine/Depth = largeur, Coarse = centre, Wave = forme du LFO.", "PH seul, Blend 50 %, Filter/Rate 40–50 %"]],
            [30 * mm, None, 42 * mm], small=True),
      Spacer(1, 2 * mm),
      side(mode_img, 62 * mm, [P("<b>Combiner les moteurs.</b> Cliquez sur RM, UB, LB, PITCH-SHIFT ou PHASER pour activer ou couper chaque moteur : la touche RM / UB / LB passe en orange et sa LED s'allume (la lumière éclaire la façade autour), les inscriptions PITCH-SHIFT et PHASER passent en jaune. Un appui court sur le bouton MODE fait défiler RM &gt; UB &gt; LB &gt; RM+UB &gt; UB+LB &gt; RM+LB &gt; RM+UB+LB &gt; PS &gt; PH &gt; RM."),
                                P("À gauche : RM seul ; à droite : UB + LB + PITCH-SHIFT + PHASER.", "small")]),
      PageBreak()]
f += [P("5. Footswitchs, LED, presets et accord", "h1"),
      P("Le bouton MODE", "h2"),
      table([["Geste", "Action"], ["Tourner / molette", "Fait défiler les presets 1 à 9 et les charge ; la position 0 est le mode live (potards utilisés tels quels). Le point gravé indique le preset."],
             ["Appui court", "Combinaison de moteurs suivante."], ["Maintien 3 s", "Enregistre le son actuel dans le preset affiché ; les LED clignotent pour confirmer (dès 2 s)."],
             ["Clic droit", "MIDI Learn du bouton de presets, et le menu principal (presets, taille, Glow, MIDI)."]], [32 * mm, None], small=True),
      Spacer(1, 2 * mm),
      side(lad_img, 42 * mm, [P("<b>Échelle de presets.</b> Cliquez sur une ligne pour charger ce preset (sa LED s'allume). Un preset rappelle les cinq potards et la combinaison de moteurs ; bouger ensuite un potard change le son sans toucher au preset enregistré tant qu'on ne l'enregistre pas de nouveau. Les 9 presets sont modifiables et la version usine se restaure à tout moment (clic droit &gt; Presets). Ils sont stockés dans %APPDATA%\\WigaRingThink\\user_presets.xml (Windows) ou ~/Library/WigaRingThink/user_presets.xml (macOS) et partagés par tous les projets.")]),
      P("<b>Accord de la porteuse (Tune).</b> Maintenez PRESET / TUNE plus d'une seconde en jouant une note à la fois : le plugin détecte la hauteur (30 Hz – 1,5 kHz) et cale exactement la porteuse dessus. Fonctionne en RM, UB et LB et suit l'entrée tant que le footswitch est maintenu. La ligne d'état affiche « TUNED … Hz » ; la valeur est enregistrée avec le preset et annulée dès qu'on touche Coarse ou Fine. L'accord n'agit pas quand l'effet est bypassé."),
      KeepTogether([img(fs_img, W), P("Bypass sur le preset 4 (LED STATUS éteinte), puis effet actif sur le preset 1.", "small")]),
      table([["Commande", "Fonction"], ["PRESET / TUNE", "Appui court : preset suivant (… 9, mode live, 1). Maintien ≥ 1 s : accord continu. Le bouton s'assombrit tant qu'on appuie."],
             ["BYPASS", "Effet on / off dès l'appui, avec un fondu de 10 ms sans clic."],
             ["LED PRESET", "Fixe : un preset est chargé. Clignotement rapide : réglages modifiés depuis le chargement. Clignotement lent : accord en cours."],
             ["LED STATUS", "Rouge = effet actif ; éteinte = bypass."]], [34 * mm, None], small=True),
      P("Les LED s'allument et s'éteignent en fondu, comme de vraies ampoules ; leur halo sur la façade se règle avec <b>Glow</b> (section 7).", "small"),
      PageBreak()]
f += [P("6. MIDI", "h1"),
      P("Toutes les commandes de la façade se pilotent en MIDI. Le plugin écoute <b>tous les canaux MIDI</b>. <b>Aucun CC n'est assigné par défaut</b> : tout passe par le <b>MIDI Learn</b>, et les assignations sont <b>sauvegardées avec le projet</b>."),
      P("MIDI Learn", "h2")]
f += bullets(["<b>Clic droit sur une commande</b> (potard, touche RM / UB / LB, PITCH-SHIFT ou PHASER, bouton MODE ou échelle, footswitch). L'en-tête du menu affiche son nom et son assignation (<b>MIDI: CC n</b> ou <b>MIDI: not assigned</b>).",
              "Choisissez <b>MIDI Learn: &lt;Nom&gt;</b>, puis bougez une pédale, un potard ou un bouton de votre contrôleur. La pastille affiche <b>MIDI LEARN &lt;Nom&gt;</b>, puis <b>&lt;Nom&gt; = CC n</b> une fois le CC reçu.",
              "<b>Clear MIDI: &lt;Nom&gt;</b> efface l'assignation ; <b>Cancel MIDI learn</b> arrête l'attente. Clic droit &gt; <b>MIDI</b> : la liste de toutes les commandes avec leur assignation et <b>Clear all MIDI assignments</b>.",
              "Un CC ne pilote qu'une commande : apprendre un CC déjà utilisé le retire de l'autre. Les deux footswitchs peuvent aussi apprendre une note MIDI (note-on = appui, note-off = relâché)."])
f += [KeepTogether([P("Commandes apprenables", "h2"),
      table([["Commande", "Type"], ["Blend · Wave · Filter/Rate · Fine/Depth · Coarse", "Continu (0–127 = toute la course)"],
             ["RM / UB / LB button · Pitch-Shift switch · Phaser switch", "Bascule : ≥ 64 = actif, &lt; 64 = coupé"],
             ["Preset knob", "Sélecteur 10 positions : mode live, presets 1 à 9"],
             ["Preset/Tune footswitch", "Momentané (CC ou note) : appui court = preset suivant, maintien ≥ 1 s = accord"],
             ["Bypass footswitch", "Chaque appui bascule l'effet ; option <b>MIDI footswitch latching</b> (clic droit sur BYPASS) pour les pédales à accrochage"]],
            [70 * mm, None], small=True)])]
f += bullets(["<b>Program Change</b> 0–9 : 0 = mode live, 1 à 9 = charge ce preset.",
              "Les valeurs reçues en MIDI sont transmises à l'hôte par un timer, jamais depuis le thread audio (anti-gel). Tous les paramètres sont aussi automatisables dans le DAW."])
f += [P("7. Fenêtre, menus et Glow", "h1"),
      P("Ring Think s'ouvre à la taille par défaut, <b>60 %</b> (la même hauteur que toutes les pédales doubles NINE HANDS | DSP), et la fenêtre ne peut jamais être plus petite. Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> pour cette instance, « (default) » indiquant la taille par défaut ; <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres (réglage commun, enregistré sur l'ordinateur). Vous pouvez aussi tirer le coin inférieur droit (proportions conservées)."),
      side(menu_img, 84 * mm, [P("<b>Menus clic droit</b> : même présentation que dans Octopus, ouverts là où l'on clique. Le menu principal propose <b>Plugin size</b>, <b>Glow</b>, <b>Presets</b> (charger, enregistrer, restaurer, son Phaser usine), <b>Next mode combination</b> et <b>MIDI</b>."),
                               P("<b>Glow (halo of the lights)</b> : intensité du halo des LED sur la façade, <b>25 %</b>, <b>50 %</b>, <b>75 %</b> ou <b>100 %</b> (défaut). La lumière des LED elle-même reste toujours à fond. Réglage commun à toutes les fenêtres de Ring Think.")]),
      Spacer(1, 2 * mm),
      KeepTogether(side(bar_img, 84 * mm, [P("<b>Pastille presets / ligne d'état.</b> Au repos, elle affiche le preset en cours (numéro et nom d'usine, « (user) » s'il a été réenregistré, « * » si les réglages ont changé, <i>Live knobs</i> en mode live) ; les flèches chargent le preset précédent / suivant et un clic sur le nom ouvre la liste des presets. Dès qu'un réglage bouge (souris, molette, automation, MIDI, footswitch), la ligne d'état prend sa place avec la valeur en direct (ex. <i>Blend 73 %</i>), puis s'efface 2,5 s après le dernier mouvement. Un clic sur la pastille fait revenir les presets tout de suite."),
                              P("La pastille au repos, puis pendant un réglage.", "small")])),
      P("8. Presets", "h1"),
      P("Neuf presets sont livrés avec le plugin (valeurs en % de la course des potards). Leurs noms apparaissent aussi dans le menu de programmes du DAW. Un son Phaser bonus est le dixième programme du DAW et se charge depuis le clic droit &gt; Presets &gt; <b>Load the factory Phaser sound</b> ; il n'occupe aucun de vos neuf emplacements."),
      table([["#", "Preset", "Mode", "Blend", "Wave", "Filter", "Fine", "Coarse", "Résultat"],
             ["1", "Ring Mod", "RM", "60 %", "25 %", "80 %", "50 %", "80 %", "Porteuse 318 Hz : cloche métallique / robot (son à l'ouverture)"],
             ["2", "Tremolo", "RM", "50 %", "25 %", "100 %", "50 %", "38 %", "Sinus 4,6 Hz : trémolo profond"],
             ["3", "Ring Vibe", "LB", "50 %", "50 %", "100 %", "50 %", "35 %", "Décalage de 3,4 Hz vers le bas : vibe tourbillonnante"],
             ["4", "Detune", "PS", "50 %", "25 %", "0 %", "60 %", "50 %", "+20 cents, sans LFO : doublage désaccordé"],
             ["5", "Chorus", "PS", "50 %", "25 %", "30 %", "15 %", "50 %", "LFO 1,1 Hz, ±22 cents : chorus doux"],
             ["6", "Vibrato", "PS", "100 %", "25 %", "50 %", "25 %", "50 %", "LFO 6,5 Hz, ±37 cents, 100 % traité"],
             ["7", "Sub Octave", "PS", "60 %", "25 %", "0 %", "50 %", "25 %", "−12 demi-tons, juste (fenêtre calée sur la note)"],
             ["8", "Octave Up", "PS", "50 %", "25 %", "0 %", "50 %", "75 %", "+12 demi-tons : brillance façon 12 cordes"],
             ["9", "Rotary Thing", "PS", "70 %", "25 %", "50 %", "35 %", "50 %", "LFO 6,5 Hz, ±52 cents : cabine rapide"],
             ["+", "Phaser", "PH", "50 %", "25 %", "45 %", "50 %", "50 %", "Balayage 0,54 Hz, ±1 octave autour de 894 Hz"]],
            [7 * mm, 22 * mm, 11 * mm, 12 * mm, 12 * mm, 12 * mm, 11 * mm, 13 * mm, None], small=True),
      PageBreak(), P("9. Conseils d'utilisation", "h1")]
f += bullets(["Dans Reaper, placez Ring Think <b>avant le simulateur d'ampli</b> (par exemple avant Ampire, suivi d'Impulse pour le baffle) : modulation en anneau et transposition marchent bien mieux sur un son clair. Mettez un drive après Ring Think pour des solos ring-mod hurlants.",
              "Avec une <b>7 cordes accordée en sol</b> ou plus bas, gardez une porteuse modérée (Coarse 60–75 %) et le filtre vers 60 % : les notes très graves créent des bandes latérales très denses. Sub Octave sur les cordes graves devient vite lourd : baissez Blend vers 40–50 %.",
              "Pour une cloche accordée, maintenez PRESET / TUNE sur une note tenue en RM, puis Blend 40–60 %, Filter ≈ 70 %.",
              "Apprenez Coarse sur une pédale d'expression (MIDI Learn) pour des sirènes et glissandos : la porteuse suit en douceur.",
              "PH seul, Blend 50 %, Filter/Rate 45 % : un phaser classique ; montez Fine pour un balayage plus large."], "tip")
f += [KeepTogether([P("10. Caractéristiques techniques", "h1"),
      table([["Format", "VST3 (Windows 64 bits, macOS universel) et Audio Unit (macOS) ; « Ring Think », fabricant « NINE HANDS | DSP »"],
             ["Canaux", "Mono ou stéréo ; entrée MIDI"],
             ["Anneau / SSB", "Porteuse anti-repliement (PolyBLEP), 5 formes d'onde, 0,1 Hz – 2,39 kHz ; bandes latérales par transformée de Hilbert ; passe-bas 18 dB/oct, 20 Hz – 20 kHz"],
             ["Pitch shift", "Deux têtes de lecture, ±24 demi-tons, LFO 0,1–500 Hz ; fenêtre calée sur la note jouée"],
             ["Phaser", "6 étages passe-tout, réinjection 40 %, centre 200 Hz – 4 kHz, LFO 0,05–10 Hz"],
             ["Accordeur", "Détection de hauteur YIN, 30 Hz – 1,5 kHz"],
             ["MIDI", "MIDI Learn sur 13 commandes (CC ; note pour les footswitchs), aucun CC par défaut, Program Change 0–9, tous canaux"],
             ["Fenêtre", "Plugin size 60 % / 75 % / 100 %, jamais sous 60 % ; Glow 25 / 50 / 75 / 100 % ; anti-gel v2 sous Windows (rendu logiciel, chien de garde)"],
             ["Version", VERSION]], [30 * mm, W - 30 * mm], header=False, small=True)])]

# ---------------------------------------------------------------- pages
def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Ring Think (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

# couverture « minimale » (modele 6) : gabarit fixe commun a toutes les notices, mesures en mm depuis le haut (logo et bandeau : depuis le bas)
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm; NAME_TOP, NAME_PT = 194 * mm, 30; SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm; BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line("FRANÇAIS", LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw_ = iw / 1.32; ch_ = (ih - int(cw_ * 0.16)) / 1.2; pad_ = int(cw_ * 0.16)
    kk = min(PEDAL_H / ch_, PEDAL_MAXW / cw_)
    dw, dh = iw * kk, ih * kk
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch_ * kk) / 2) + pad_ * kk
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line("RING THINK", NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line("Modulateur en anneau", SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="RING THINK - Notice v" + VERSION, author="NINE HANDS | DSP")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
doc.build(f)
shutil.rmtree(TMP, ignore_errors=True)
print(OUT)
