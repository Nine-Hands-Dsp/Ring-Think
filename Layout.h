// genere par tools/export_plugin.py - ne pas modifier a la main (repere 1175 x 900 unites, images 2x)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 1175.0f, frameH = 900.0f;
    // potards : blend, wave, filter, fine, coarse ; diametre du composant (couvre le potard du visuel)
    const juce::Point<float> knobPos[5] = { { 160.63f, 195.29f }, { 334.01f, 195.29f }, { 509.82f, 195.29f }, { 684.66f, 195.29f }, { 857.06f, 195.29f } };
    constexpr float knobD = 164.50f;
    const juce::Point<float> capPos { 1034.33f, 196.27f }; constexpr float capD = 135.50f, capDotR = 39.94f;   // bouton MODE
    const juce::Point<float> ladder[9] = { { 768.43f, 339.35f }, { 768.43f, 377.82f }, { 768.43f, 414.64f }, { 768.43f, 452.63f }, { 768.43f, 490.71f }, { 768.43f, 527.34f }, { 768.23f, 565.32f }, { 768.23f, 602.63f }, { 768.23f, 640.81f } };
    const juce::Point<float> modeLed[3] = { { 987.29f, 307.69f }, { 1032.48f, 336.62f }, { 1079.33f, 306.62f } };   // RM, UB, LB
    const juce::Point<float> face[3] = { { 986.61f, 324.84f }, { 1033.36f, 324.84f }, { 1080.11f, 324.84f } };
    constexpr float faceW = 42.86f, faceH = 95.45f;
    const juce::Point<float> label[3] = { { 986.12f, 342.86f }, { 1034.33f, 311.20f }, { 1080.60f, 343.34f } };
    const juce::Point<float> psPos { 1033.85f, 401.79f }, phLed { 765.50f, 52.11f };
    const juce::Point<float> phTxt { 817.04f, 52.02f };   // centre du mot PHASER
    const juce::Rectangle<float> phPill { 746.02f, 36.11f, 126.62f, 32.00f };
    const juce::Point<float> presetLed { 444.56f, 736.46f }, statusLed { 744.56f, 736.56f };
    const juce::Point<float> fsL { 248.30f, 759.25f }, fsR { 940.83f, 759.25f };
    constexpr float footR = 41.33f;   // rayon du bouton du footswitch
    const juce::Rectangle<float> presetRect { 387.50f, 767.53f, 400.00f, 38.00f };   // pastille presets / ligne d'etat (Strong Pickle)
    constexpr float presetFont = 23.0f;
    const juce::Point<float> logoPos { 618.43f, 850.32f }; constexpr float logoW = 230.00f;
    // halos des LED (calques alpha) : nom, x, y, w, h
    struct GlowRect { const char* name; float x, y, w, h; };
    const GlowRect glow[15] = { { "lad0", 707.00f, 278.00f, 122.50f, 122.50f }, { "lad1", 707.00f, 316.50f, 122.50f, 122.50f }, { "lad2", 707.00f, 353.00f, 122.50f, 122.50f }, { "lad3", 707.00f, 391.00f, 122.50f, 122.50f }, { "lad4", 707.00f, 429.00f, 122.50f, 122.50f }, { "lad5", 707.00f, 466.00f, 122.50f, 122.50f }, { "lad6", 706.50f, 504.00f, 122.50f, 122.50f }, { "lad7", 706.50f, 541.00f, 122.50f, 122.50f }, { "lad8", 706.50f, 579.50f, 122.50f, 122.50f }, { "mode_rm", 926.00f, 246.00f, 122.50f, 122.50f }, { "mode_ub", 971.00f, 275.00f, 122.50f, 122.50f }, { "mode_lb", 1018.00f, 245.00f, 122.50f, 122.50f }, { "phaser", 716.50f, 3.00f, 98.00f, 98.00f }, { "preset", 349.00f, 641.00f, 190.50f, 190.50f }, { "status", 649.00f, 641.00f, 190.50f, 190.50f } };
    // tailles des sprites (unites)
    constexpr float sz_ledS_on = 22.00f;
    constexpr float sz_ledP_on = 34.00f;
    constexpr float sz_ledR_on = 34.00f;
    constexpr float sz_face_on = 46.00f;
    const juce::Rectangle<float> boxRect { 14.53f, 0.0f, 1145.94f, 900.0f };   // boitier (notice)
}
