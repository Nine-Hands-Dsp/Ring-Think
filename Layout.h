// genere par tools/art/make_art_hd.py - ne pas modifier a la main (repere 1175 x 900 unites, images 2,5 px / unite)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 1175.0f, frameH = 900.0f, pxPerUnit = 2.50f;
    const juce::Point<float> knobPos[5] = { { 160.36f, 195.31f }, { 333.83f, 195.27f }, { 509.74f, 195.22f }, { 684.67f, 195.18f }, { 857.16f, 195.13f } };
    constexpr float knobD = 164.61f;
    const juce::Point<float> capPos { 1034.53f, 196.06f }; constexpr float capD = 135.60f, capDotR = 39.94f;   // bouton MODE
    const juce::Point<float> ladder[9] = { { 768.64f, 339.00f }, { 768.64f, 377.80f }, { 768.64f, 413.80f }, { 768.64f, 452.60f }, { 768.64f, 489.80f }, { 768.64f, 525.40f }, { 768.64f, 564.60f }, { 768.64f, 600.60f }, { 768.64f, 639.80f } };
    const juce::Point<float> modeLed[3] = { { 987.54f, 307.32f }, { 1032.78f, 336.19f }, { 1079.63f, 306.23f } };   // RM, UB, LB
    const juce::Point<float> face[3] = { { 986.88f, 324.44f }, { 1033.65f, 324.43f }, { 1080.43f, 324.42f } };
    constexpr float faceW = 42.86f, faceH = 95.45f;
    const juce::Point<float> label[3] = { { 986.40f, 342.43f }, { 1034.61f, 310.81f }, { 1080.93f, 342.89f } };
    const juce::Point<float> psPos { 1034.19f, 401.26f }, phLed { 766.00f, 51.20f }, phTxt { 823.20f, 51.20f };
    const juce::Rectangle<float> phPill { 746.00f, 36.80f, 127.20f, 28.80f };
    const juce::Point<float> presetLed { 442.20f, 735.40f }, statusLed { 745.40f, 735.40f };
    const juce::Point<float> fsL { 248.47f, 758.35f }, fsR { 941.37f, 758.17f };
    constexpr float footR = 41.33f;   // rayon du bouton du footswitch
    const juce::Rectangle<float> presetRect { 387.50f, 767.52f, 400.0f, 38.0f };   // pastille presets / ligne d'etat (Strong Pickle)
    constexpr float presetFont = 23.0f;
    const juce::Point<float> logoPos { 604.40f, 849.80f }; constexpr float logoW = 230.00f;
    struct GlowRect { const char* name; float x, y, w, h; };
    const GlowRect glow[15] = { { "lad0", 707.20f, 277.60f, 122.40f, 122.40f }, { "lad1", 707.20f, 316.40f, 122.40f, 122.40f }, { "lad2", 707.20f, 352.40f, 122.40f, 122.40f }, { "lad3", 707.20f, 391.20f, 122.40f, 122.40f }, { "lad4", 707.20f, 428.40f, 122.40f, 122.40f }, { "lad5", 707.20f, 464.00f, 122.40f, 122.40f }, { "lad6", 707.20f, 503.20f, 122.40f, 122.40f }, { "lad7", 707.20f, 539.20f, 122.40f, 122.40f }, { "lad8", 707.20f, 578.40f, 122.40f, 122.40f }, { "mode_rm", 926.00f, 246.00f, 122.40f, 122.40f }, { "mode_ub", 971.20f, 274.80f, 122.40f, 122.40f }, { "mode_lb", 1018.40f, 244.80f, 122.40f, 122.40f }, { "phaser", 716.80f, 2.00f, 98.00f, 98.00f }, { "preset", 346.80f, 640.00f, 190.80f, 190.80f }, { "status", 650.00f, 640.00f, 190.80f, 190.80f } };
    const juce::Rectangle<float> boxRect { 12.0f, 0.0f, 1151.0f, 900.0f };   // boitier (notice)
}
