# Ring Think (NINE HANDS | DSP)

Modulateur en anneau / décaleur de fréquence à bande latérale unique, pitch shifter et phaser, d'après l'Electro-Harmonix Ring Thing. VST3 pour Windows et macOS (+ AU sur macOS), au format pédale double.

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-Notice.pdf"><img alt="Télécharger la notice (PDF)" src="https://img.shields.io/badge/%F0%9F%93%96%20Notice-PDF-919496?style=for-the-badge"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/Ring-Think?label=derni%C3%A8re%20version&color=ff5a1f"></a>
</p>

## Installation
Les boutons ci-dessus téléchargent toujours la dernière version.

### Windows
Dézipper, copier « Ring Think.vst3 » dans `C:\Program Files\Common Files\VST3\` puis relancer la recherche de plugins du DAW.

### macOS
1. Dézipper. Copier « Ring Think.vst3 » dans `/Library/Audio/Plug-Ins/VST3/` (et « Ring Think.component » dans `/Library/Audio/Plug-Ins/Components/` pour Logic / GarageBand).
2. Le plugin n'est pas notarisé par Apple : dans le Terminal, une seule fois :
       xattr -cr "/Library/Audio/Plug-Ins/VST3/Ring Think.vst3"
       xattr -cr "/Library/Audio/Plug-Ins/Components/Ring Think.component"
3. Relancer la recherche de plugins du DAW.

## Presets utilisateur
Windows : `%APPDATA%\WigaRingThink\user_presets.xml` — macOS : `~/Library/WigaRingThink/user_presets.xml` (communs à tous les projets).

## Contenu du dépôt
- `CMakeLists.txt`, `PluginProcessor.*`, `PluginEditor.*`, `NHKnob.h` (potards animés), `NineHandsMenu.h` (menus d'Octopus), `NineHandsGlow.h`, `Layout.h` (repères générés).
- Images (fond 2350 x 1800, sprites, halos des LED, calques du potard), police Poppins et logo NINE HANDS | DSP : intégrés au plugin.
- `tools/art/` : `make_art_hd.py` fabrique les images à partir du visuel HD `hd.png` (anciens scripts de la v3.0.0 conservés) ; `tools/render/` : captures de la vraie fenêtre sous Linux ; `tools/manual.py` : notice.

## Historique
- v3.0.2 : nouveaux footswitchs (photo fournie : écrou hexagonal moleté, bouton en métal tourné).
- v3.0.1 : nouveau visuel haute définition (2938 x 2250, fourni par l'utilisateur, sans agrandissement) : net jusqu'à la taille maximale de la fenêtre, y compris sur écran Retina / 200 % ; inscriptions PITCH-SHIFT et PHASER en vectoriel.
- v3.0.0 : refonte aux règles NINE HANDS | DSP : image 2350 x 1800 plein cadre (boîtier élargi sans rien étirer), jacks photo du kit, footswitchs d'Echoflex, potards animés (index, chapeau, couronne et ombre solidaires, flou de mouvement, lumière fixe en haut à gauche), LED du kit avec halo sur la façade, réglage Glow 25 / 50 / 75 / 100 %, pastille presets / ligne d'état (taille Strong Pickle), menus clic droit d'Octopus ouverts là où l'on clique, logo NINE HANDS | DSP vectoriel.
- v2.5.0 : clic droit > Plugin size > Default size (new windows).
- v2.4.0 : MIDI Learn au clic droit sur chaque commande.
- v2.3.0 : anti-gel v2 (JUCE 8.0.15, rendu logiciel, chien de garde, aucun appel à l'hôte depuis le thread audio).
- v2.2.2 : ouverture sur le son « Ring Mod » ; pitch shift calé sur la période de la note jouée.
