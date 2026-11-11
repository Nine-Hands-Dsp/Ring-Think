// Outil hors plugin : captures PNG de la vraie fenetre de Ring Think (meme code que le plugin) + apercu des menus.
#include "BinaryData.h"
#include "PluginProcessor.h"
#include "PluginEditor.h"
using namespace juce;

static void pump (int n) { for (int i = 0; i < n; ++i) MessageManager::getInstance()->runDispatchLoopUntil (20); }

static void save (const Image& img, const String& path)
{
    File f (path); f.deleteFile();
    FileOutputStream os (f); PNGImageFormat().writeImageToStream (img, os);
    std::printf ("%s (%d x %d)\n", path.toRawUTF8(), img.getWidth(), img.getHeight());
}

int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    const String out = argc > 1 ? argv[1] : ".";
    RingProcessor proc;
    proc.prepareToPlay (48000.0, 256);
    std::unique_ptr<AudioProcessorEditor> ed (proc.createEditor());
    auto* re = static_cast<RingEditor*> (ed.get());
    std::printf ("taille par defaut : %d x %d\n", ed->getWidth(), ed->getHeight());
    auto run = [&] { AudioBuffer<float> b (2, 256); MidiBuffer m; for (int i = 0; i < 4; ++i) { b.clear(); proc.processBlock (b, m); } };
    auto shot = [&] (const String& name, int sizeIdx, float scale)
    {
        re->setScaleIndex (sizeIdx);
        run(); pump (40);
        save (ed->createComponentSnapshot (ed->getLocalBounds(), true, scale), out + "/" + name + ".png");
    };
    proc.loadPreset (1); pump (150);
    shot ("ringthink_default", 0, 2.0f);
    shot ("ringthink_100", 2, 2.0f);
    proc.setParamValue ("blend", 0.73f); pump (6);
    shot ("ringthink_status", 2, 2.0f);
    proc.loadPreset (4); proc.setParamValue ("active", 0.0f); pump (150);
    shot ("ringthink_preset4_bypass", 2, 2.0f);
    proc.setParamValue ("active", 1.0f); proc.loadPreset (0);
    proc.setParamValue ("rm", 0.0f); proc.setParamValue ("ub", 1.0f); proc.setParamValue ("lb", 1.0f);
    proc.setParamValue ("ps", 1.0f); proc.setParamValue ("ph", 1.0f); pump (150);
    shot ("ringthink_modes", 2, 2.0f);
    re->setScaleIndex (-1);
    ed.reset();

    // apercu du menu clic droit (meme LookAndFeel que la fenetre)
    {
        NineHandsMenu::MenuLnf l;
        l.f = { Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize),
                Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize),
                Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize) };
        struct It { String t; bool sep, sub, tick, act, hi; };
        std::vector<It> items { { "Plugin size", 0,1,0,1,0 }, { "Glow (halo of the lights)", 0,1,0,1,1 }, { "", 1,0,0,0,0 },
            { "Presets", 0,1,0,1,0 }, { "Next mode combination (push the MODE knob)", 0,0,0,1,0 }, { "", 1,0,0,0,0 },
            { "MIDI", 0,1,0,1,0 }, { "", 1,0,0,0,0 }, { "Ring Think v" + String (JucePlugin_VersionString) + "  NINE HANDS | DSP", 0,0,0,0,0 } };
        std::vector<It> glowItems { { "Glow 25 %", 0,0,0,1,0 }, { "Glow 50 %", 0,0,0,1,0 }, { "Glow 75 %", 0,0,0,1,1 }, { "Glow 100 %  (default)", 0,0,1,1,0 } };
        auto renderList = [&] (std::vector<It>& list, const String& file, bool header)
        {
            NineHandsMenu::Header h (l.f, NineHandsMenu::icoPedal, Colour (0xffff6a1a), "Ring Think", "Ring modulator  v" + String (JucePlugin_VersionString));
            int W = 0, H = 14, hw = 0, hh = 0;
            if (header) { h.getIdealSize (hw, hh); W = hw; H += hh; }
            for (auto& it : list) { int w, hh2; l.getIdealPopupMenuItemSize (it.t, it.sep, 0, w, hh2); W = jmax (W, w); H += hh2; }
            W += 14;
            Image img (Image::ARGB, W * 2, H * 2, true);
            { Graphics g (img); g.addTransform (AffineTransform::scale (2.0f));
              l.drawPopupMenuBackground (g, W, H);
              int y = 7;
              if (header) { h.setBounds (7, y, W - 14, hh); { Graphics::ScopedSaveState s (g); g.setOrigin (7, y); h.paint (g); } y += hh; }
              for (auto& it : list) { int w, hh2; l.getIdealPopupMenuItemSize (it.t, it.sep, 0, w, hh2);
                  l.drawPopupMenuItem (g, { 7, y, W - 14, hh2 }, it.sep, it.act, it.hi, it.tick, it.sub, it.t, {}, nullptr, nullptr); y += hh2; } }
            save (img, out + "/" + file);
        };
        renderList (items, "ringthink_menu.png", true);
        renderList (glowItems, "ringthink_menu_glow.png", false);
    }
    return 0;
}
