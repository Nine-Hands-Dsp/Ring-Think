# Ring Think (NINE HANDS | DSP) - VST3 (Windows + macOS) and AU (macOS) - personal use

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest/download/RingThink-Notice.pdf"><img alt="Télécharger la notice (PDF)" src="https://img.shields.io/badge/%F0%9F%93%96%20Notice-PDF-919496?style=for-the-badge"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Ring-Think/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/Ring-Think?label=derni%C3%A8re%20version&color=919496"></a>
</p>

## Repository layout (everything at the ROOT of the repo, no sub-folder except .github)
    CMakeLists.txt
    PluginProcessor.h / PluginProcessor.cpp
    PluginEditor.h / PluginEditor.cpp
    background.png
    pitchshift_white.png
    pitchshift_yellow.png
    .github/workflows/build.yml

## Get the .vst3
1. Create a NEW empty GitHub repository, then "Add file > Upload files" and drop the files above.
2. Create .github/workflows/build.yml by hand if the upload skipped the hidden folder
   (Add file > Create new file, type the path .github/workflows/build.yml and paste the file content).
3. Actions tab > "Build Windows + macOS" > open the green run > Artifacts:
   - RingThink-VST3-Windows  (Windows)
   - RingThink-macOS-VST3-AU (macOS: universal Apple Silicon + Intel)

### Windows
Unzip, copy "Ring Think.vst3" to C:\Program Files\Common Files\VST3\ and rescan plugins in your DAW.

### macOS
1. Unzip the artifact. Copy "Ring Think.vst3" to /Library/Audio/Plug-Ins/VST3/
   and "Ring Think.component" (Audio Unit, for Logic/GarageBand) to /Library/Audio/Plug-Ins/Components/
   (or the same folders inside your user ~/Library).
2. The plugin is not notarized by Apple, so macOS blocks downloaded files. Open Terminal and run once:
       xattr -cr "/Library/Audio/Plug-Ins/VST3/Ring Think.vst3"
       xattr -cr "/Library/Audio/Plug-Ins/Components/Ring Think.component"
3. Rescan plugins in your DAW (Logic: restart it; AU validation runs automatically).

## User presets
Windows: %APPDATA%\WigaRingThink\user_presets.xml
macOS: ~/Library/WigaRingThink/user_presets.xml
(shared by every project).

## Plugin size (clic droit)
- *Plugin size* : 60 % (taille minimale), 75 %, 100 % ; taille actuelle cochée, « (default) » à côté de la taille par défaut.
- *Plugin size > Default size (new windows)* : taille d'ouverture des nouvelles fenêtres, mémorisée pour toutes les instances
  (comme Octopus) et appliquée tout de suite ; une taille choisie pour une instance reste enregistrée dans son projet.

## v2.3.0 - anti-gel v2 (fenêtre qui se fige sous Windows / Reaper)
- JUCE 8.0.15 (corrections Direct2D, mise à l'échelle Windows, redimensionnement).
- Fenêtre opaque, moteur de rendu logiciel réappliqué dès que l'hôte recrée la fenêtre.
- Fond mis à l'échelle par le timer uniquement (aucun calcul lourd pendant le dessin).
- Chien de garde : si une zone demandée n'est pas redessinée en 1,5 s, le rendu est relancé.
- Plus aucun appel à l'hôte depuis le thread audio (MIDI, footswitch, presets passent par un timer à 60 Hz).

## v2.2.2
- The plugin now opens on the "Ring Mod" sound (knob defaults were giving a ~15 Hz carrier, heard as a tremolo).
- Pitch shift (Sub Octave, Octave Up, Detune...): the grain window now locks onto the period of the played note, so the shifted note is in tune and no longer beats or wobbles. Chords and silence fall back to the previous fixed window.

## Files (v2.3.0)
All the PNG files at the repo root are the pedal artwork (background, knob caps, LEDs, labels...) and are embedded in the plugin by CMakeLists.txt: upload them all.

- v2.3.1 : menu de taille de fenêtre : « 60 % (default) », 75 %, 100 % (plus de taille en pixels)
- v2.4.0 : MIDI Learn au clic droit sur chaque commande (Clear MIDI, assignations sauvegardées avec le projet)
- v2.5.0 : clic droit > Plugin size > Default size (new windows) : taille par défaut des nouvelles fenêtres au choix, comme dans Octopus
