"""
Ring Think (NINE HANDS | DSP) - exporte les images du plugin et Layout.h a partir de make_art.py
  background.png   2350 x 1800 : facade + embases + sieges et LED eteintes + faces eteintes + footswitchs (fixes)
  sprites          LED allumees, touche RM/UB/LB allumee, inscriptions, PITCH-SHIFT / PHASER, bouton MODE
  glow_*.png       halo de chaque LED sur la facade (calque alpha, dose par le reglage Glow)
  knob_*.png       calques du potard (nh::Knob)
Repere du plugin = image / 2 (1175 x 900 unites).
"""
import os, sys, math, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_art as M

DST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(M.ROOT, 'out', 'plugin')
os.makedirs(DST, exist_ok=True)
pos, SPR, over = M.pos, M.SPR, M.over

def save(arr, name):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(DST, name), optimize=True)

# ---------------------------------------------------------------- fond : tout ce qui ne bouge pas
bg = M.canvas.copy()
for k in ('rm', 'ub', 'lb'): over(bg, SPR['face_off'], *pos['faces'][k])
for p in pos['ladder'] + list(pos['modeled'].values()) + [pos['phled']]: over(bg, SPR['seatS'], *p)
for p in (pos['presetled'], pos['statusled']): over(bg, SPR['seatP'], *p)
for p in pos['ladder'] + [pos['phled']]: over(bg, SPR['ledS_off'], *p)
over(bg, SPR['ledP_off'], *pos['presetled']); over(bg, SPR['ledR_off'], *pos['statusled'])
over(bg, SPR['fs'], *pos['fsL']); over(bg, SPR['fs'], *pos['fsR'])
save(bg, 'background.png')

# ---------------------------------------------------------------- sprites
for n in ('ledS_on', 'ledS_off', 'ledP_on', 'ledR_on', 'face_on', 'label_rm', 'label_ub', 'label_lb',
          'pitchshift_white', 'pitchshift_yellow', 'phaser_white', 'phaser_yellow', 'cap_big'):
    save(SPR[n], n + '.png')

# ---------------------------------------------------------------- halos (calculs sur le fond final)
M.bg_rgb = bg[..., :3]
glows = []
def glow(name, p, col, R):
    g, (gx, gy) = M.led_glow(p, col, R)
    save(g, 'glow_' + name + '.png')
    glows.append((name, gx / 2, gy / 2, g.shape[1] / 2, g.shape[0] / 2))
for i, p in enumerate(pos['ladder']): glow('lad%d' % i, p, M.AMBER, 9.0 * M.K)
for k in ('rm', 'ub', 'lb'): glow('mode_' + k, pos['modeled'][k], M.AMBER, 9.0 * M.K)
glow('phaser', pos['phled'], M.AMBER, 9.0 * M.K * 0.8)
glow('preset', pos['presetled'], M.AMBER, 14.0 * M.K)
glow('status', pos['statusled'], M.RED, 14.0 * M.K)

# ---------------------------------------------------------------- calques du potard (512 px)
for n in ('shadow', 'crown', 'cap', 'marker', 'highlight'):
    Image.open(os.path.join(M.ROOT, 'assets', 'knob', 'ring_knob_' + n + '.png')).resize((512, 512), Image.LANCZOS) \
         .save(os.path.join(DST, 'knob_' + n + '.png'), optimize=True)

# ---------------------------------------------------------------- Layout.h
U = lambda v: v / 2.0
def pt(p): return '{ %.2ff, %.2ff }' % (U(p[0]), U(p[1]))
def sz(n): return '%.2ff' % (SPR[n].shape[1] / 2.0)
L = []
L.append('// genere par tools/export_plugin.py - ne pas modifier a la main (repere 1175 x 900 unites, images 2x)')
L.append('#pragma once\n#include <juce_graphics/juce_graphics.h>\nnamespace layout\n{')
L.append('    constexpr float frameW = 1175.0f, frameH = 900.0f;')
L.append('    // potards : blend, wave, filter, fine, coarse ; diametre du composant (couvre le potard du visuel)')
L.append('    const juce::Point<float> knobPos[5] = { %s };' % ', '.join(pt(p) for p in pos['knobs']))
L.append('    constexpr float knobD = %.2ff;' % U(M.KD))
L.append('    const juce::Point<float> capPos %s; constexpr float capD = %s, capDotR = %.2ff;   // bouton MODE' % (pt(pos['capbig']), sz('cap_big'), 41.0 * M.K / 2))
L.append('    const juce::Point<float> ladder[9] = { %s };' % ', '.join(pt(p) for p in pos['ladder']))
L.append('    const juce::Point<float> modeLed[3] = { %s, %s, %s };   // RM, UB, LB' % tuple(pt(pos['modeled'][k]) for k in ('rm', 'ub', 'lb')))
L.append('    const juce::Point<float> face[3] = { %s, %s, %s };' % tuple(pt(pos['faces'][k]) for k in ('rm', 'ub', 'lb')))
L.append('    constexpr float faceW = %.2ff, faceH = %.2ff;' % (44 * M.K / 2, 98 * M.K / 2))
L.append('    const juce::Point<float> label[3] = { %s, %s, %s };' % tuple(pt(pos['labels'][k]) for k in ('rm', 'ub', 'lb')))
L.append('    const juce::Point<float> psPos %s, phLed %s;' % (pt(pos['ps']), pt(pos['phled'])))
L.append('    const juce::Point<float> phTxt { %.2ff, %.2ff };   // centre du mot PHASER' % (U(pos['phtxt'][0] + SPR['phaser_white'].shape[1] / 2), U(pos['phtxt'][1] + SPR['phaser_white'].shape[0] / 2)))
L.append('    const juce::Rectangle<float> phPill { %.2ff, %.2ff, %.2ff, %.2ff };' % (U(pos['phpill'][0][0]), U(pos['phpill'][0][1]) - 16, U(pos['phpill'][1][0] - pos['phpill'][0][0]), 32))
L.append('    const juce::Point<float> presetLed %s, statusLed %s;' % (pt(pos['presetled']), pt(pos['statusled'])))
L.append('    const juce::Point<float> fsL %s, fsR %s;' % (pt(pos['fsL']), pt(pos['fsR'])))
L.append('    constexpr float footR = %.2ff;   // rayon du bouton du footswitch' % U(M.fsBtn))
bx, by, bw_, bh_ = pos['bar']
L.append('    const juce::Rectangle<float> presetRect { %.2ff, %.2ff, %.2ff, %.2ff };   // pastille presets / ligne d\'etat (Strong Pickle)' % (U(bx) - bw_ / 4, U(by) - bh_ / 4, bw_ / 2, bh_ / 2))
L.append('    constexpr float presetFont = 23.0f;')
lx, ly, lw = pos['logo']
L.append('    const juce::Point<float> logoPos %s; constexpr float logoW = %.2ff;' % (pt((lx, ly)), lw / 2))
L.append('    // halos des LED (calques alpha) : nom, x, y, w, h')
L.append('    struct GlowRect { const char* name; float x, y, w, h; };')
L.append('    const GlowRect glow[%d] = { %s };' % (len(glows), ', '.join('{ "%s", %.2ff, %.2ff, %.2ff, %.2ff }' % g for g in glows)))
L.append('    // tailles des sprites (unites)')
for n in ('ledS_on', 'ledP_on', 'ledR_on', 'face_on'):
    L.append('    constexpr float sz_%s = %s;' % (n, sz(n)))
L.append('    const juce::Rectangle<float> boxRect { %.2ff, 0.0f, %.2ff, 900.0f };   // boitier (notice)' % (U(M.X0), U(M.BW)))
L.append('}')
open(os.path.join(DST, 'Layout.h'), 'w').write('\n'.join(L) + '\n')
print('export ok', DST, len(glows), 'halos')
