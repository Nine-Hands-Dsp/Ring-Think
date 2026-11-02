#pragma once
#include "PluginProcessor.h"

class PedalContent;

class RingEditor : public juce::AudioProcessorEditor
{
public:
    explicit RingEditor (RingProcessor&);
    ~RingEditor() override;
    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
    void visibilityChanged() override;
    int  getScaleIndex() const;          // 1, 2 = 75 %, 100 %  (-1 = default / free size)
    void setScaleIndex (int idx);        // taille de cette instance : 0, 1, 2 = 60 % / 75 % / 100 %  (-1 = taille par defaut choisie)
    void applyScaleIndex (int idx);      // redimensionne seulement : 0, 1, 2 = 60 % (minimum) / 75 % / 100 %
    static constexpr int numSizes = 3;   // 60 % (defaut d'origine) / 75 % / 100 %
    RingProcessor& getProc() { return proc; }   // menus clic droit (MIDI Learn)

private:
    friend class PedalContent;           // son timer surveille le moteur de rendu (anti-gel v2)
    void useSoftwareRenderer();          // applique le moteur logiciel (Windows) si la fenêtre a changé
    void checkRenderer();                // depuis le timer : seulement si la fenêtre a changé ou au plus 1 fois / s
    void resetRenderer();                // chien de garde : oublie la fenêtre mémorisée et réapplique tout
    void* lastPeer = nullptr;
    juce::uint32 lastRendererCheck = 0;
    RingProcessor& proc;
    std::unique_ptr<PedalContent> content;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (RingEditor)
};
