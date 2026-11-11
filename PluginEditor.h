#pragma once
#include "PluginProcessor.h"
#include "NineHandsMenu.h"

class PedalContent;

// Ring Think (NINE HANDS | DSP) v3 : pedale au format double, image 2350 x 1800 (repere 1175 x 900 unites),
// potards nh::Knob, LED du kit photo avec halo dose par Glow, pastille presets / ligne d'etat, menus d'Octopus.
class RingEditor : public juce::AudioProcessorEditor
{
public:
    explicit RingEditor (RingProcessor&);
    ~RingEditor() override;
    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
    void visibilityChanged() override;

    static constexpr int numSizes = 3;                // 60 % (defaut) / 75 % / 100 %
    static int sizeHeight (int idx);                  // hauteur de fenetre de chaque taille
    int  currentSizeIndex() const;                    // -1 = taille libre
    void setScaleIndex (int idx);                     // -1 = taille par defaut choisie, 0..2
    RingProcessor& getProc() { return proc; }

    // menus clic droit (design d'Octopus), toujours ouverts a l'endroit du clic
    void showContextMenu (int learnIdx);              // -1 = menu principal
    void showPresetMenu (juce::Rectangle<int> screenArea);
    void flash (const juce::String& text, double seconds = 2.5);

    NineHandsMenu::MenuLnf menuLnf;
    juce::Typeface::Ptr regularFace, mediumFace, boldFace;
    float glow = 1.0f;                                // reglage Glow (0,25 a 1)

private:
    friend class PedalContent;                        // son timer surveille le moteur de rendu (anti-gel v2)
    void useSoftwareRenderer();
    void checkRenderer();
    void resetRenderer();
    void* lastPeer = nullptr;
    juce::uint32 lastRendererCheck = 0;
    RingProcessor& proc;
    std::unique_ptr<PedalContent> content;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (RingEditor)
};
