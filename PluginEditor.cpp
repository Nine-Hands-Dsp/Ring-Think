#include "PluginEditor.h"
#include <BinaryData.h>
#include "WigaWindowSize.h"
#include "NineHandsGlow.h"
#include "NHKnob.h"
#include "Layout.h"

// Ring Think v3 (NINE HANDS | DSP) - format double, image 2350 x 1800 = repere 1175 x 900 unites (2 px par unite)
namespace
{
    constexpr float kW = layout::frameW, kH = layout::frameH;
    const int kHeights[3] = { 495, 557, 743 };            // 60 % (defaut = hauteur de reference des pedales doubles) / 75 / 100 %
    constexpr int kHeightMax = 1125;
    const juce::Colour kOrange (0xffff8a24), kMidiRing (0xffff9a1a), kYellow (0xffffd600);
    const juce::Colour barFill (0xf2080809), barEdge (0x46ffffff), barInk (0xffececec);
    const juce::Colour menuAccent (0xffff6a1a);           // pastille des en-tetes de menu (orange RING THINK)
    constexpr float arrowW = 34.0f;

    juce::Image png (const void* d, int n) { return juce::ImageCache::getFromMemory (d, n); }
    juce::Image named (const char* resource)
    {
        int n = 0;
        if (auto* d = BinaryData::getNamedResource (resource, n)) return juce::ImageCache::getFromMemory (d, n);
        return {};
    }

    // toutes les images de la pedale (fond 2x, sprites 2x : dessines a la moitie de leur taille en pixels)
    struct Art
    {
        Art()
        {
            bg       = png (BinaryData::background_png, BinaryData::background_pngSize);
            capBig   = png (BinaryData::cap_big_png, BinaryData::cap_big_pngSize);
            faceOn   = png (BinaryData::face_on_png, BinaryData::face_on_pngSize);
            lab[0]   = png (BinaryData::label_rm_png, BinaryData::label_rm_pngSize);
            lab[1]   = png (BinaryData::label_ub_png, BinaryData::label_ub_pngSize);
            lab[2]   = png (BinaryData::label_lb_png, BinaryData::label_lb_pngSize);
            psWhite  = png (BinaryData::pitchshift_white_png, BinaryData::pitchshift_white_pngSize);
            psYellow = png (BinaryData::pitchshift_yellow_png, BinaryData::pitchshift_yellow_pngSize);
            phWhite  = png (BinaryData::phaser_white_png, BinaryData::phaser_white_pngSize);
            phYellow = png (BinaryData::phaser_yellow_png, BinaryData::phaser_yellow_pngSize);
            ledSOn   = png (BinaryData::ledS_on_png, BinaryData::ledS_on_pngSize);
            ledSOff  = png (BinaryData::ledS_off_png, BinaryData::ledS_off_pngSize);
            ledPOn   = png (BinaryData::ledP_on_png, BinaryData::ledP_on_pngSize);
            ledROn   = png (BinaryData::ledR_on_png, BinaryData::ledR_on_pngSize);
            for (int i = 0; i < 15; ++i)
                glow[i] = named ((juce::String ("glow_") + layout::glow[i].name + "_png").toRawUTF8());
        }
        juce::Image bg, capBig, faceOn, lab[3], psWhite, psYellow, phWhite, phYellow, ledSOn, ledSOff, ledPOn, ledROn, glow[15];
    };

    // sprite 2x centre en c (unites)
    void drawCentred (juce::Graphics& g, const juce::Image& im, juce::Point<float> c, float scale = 1.0f, float alpha = 1.0f)
    {
        if (! im.isValid() || alpha <= 0.0f) return;
        const float w = (float) im.getWidth() / layout::pxPerUnit * scale, h = (float) im.getHeight() / layout::pxPerUnit * scale;
        g.setOpacity (juce::jmin (1.0f, alpha));
        g.drawImage (im, juce::Rectangle<float> (w, h).withCentre (c));
        g.setOpacity (1.0f);
    }

    void setParamGesture (juce::AudioProcessorValueTreeState& apvts, const char* id, float v, bool begin, bool end)
    {
        if (auto* p = apvts.getParameter (id))
        {
            if (begin) p->beginChangeGesture();
            p->setValueNotifyingHost (p->convertTo0to1 (v));
            if (end) p->endChangeGesture();
        }
    }

    // index des halos dans layout::glow : 0-8 echelle, 9-11 RM / UB / LB, 12 PHASER, 13 PRESET, 14 STATUS
    enum { gLad0 = 0, gMode0 = 9, gPhaser = 12, gPreset = 13, gStatus = 14 };
}

static RingEditor* editorOf (juce::Component* c)
{
    if (c == nullptr) return nullptr;
    if (auto* ed = dynamic_cast<RingEditor*> (c)) return ed;
    return c->findParentComponentOfClass<RingEditor>();
}

// ------------------------------------------------------------------ gros bouton MODE / presets
class BigKnob : public juce::Component, private juce::Timer
{
public:
    BigKnob (RingProcessor& p, const Art& a) : proc (p), art (a) {}

    bool isHeld() const { return holding; }
    bool isHoldBlinking() const { return holding && ! moved && (juce::Time::getMillisecondCounter() - downTime) > 2000; }

    void paint (juce::Graphics& g) override
    {
        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
        const auto c = getLocalBounds().toFloat().getCentre();
        const float sc = holding ? 0.955f : 1.0f;                 // le bouton s'enfonce
        const float rr = layout::capD * 0.5f;
        {
            const float oy = holding ? 1.0f : 2.8f;               // ombre de contact (plus serree quand on appuie)
            juce::ColourGradient cg (juce::Colours::black.withAlpha (holding ? 0.85f : 0.5f), c.x, c.y + oy,
                                     juce::Colours::black.withAlpha (0.0f), c.x, c.y + oy + rr * 1.14f, true);
            cg.addColour (0.86, juce::Colours::black.withAlpha (holding ? 0.85f : 0.5f));
            g.setGradientFill (cg);
            g.fillEllipse (juce::Rectangle<float> (rr * 2.28f, rr * 2.28f).withCentre ({ c.x, c.y + oy }));
        }
        drawCentred (g, art.capBig, c, sc);
        if (holding)
        {
            g.setColour (juce::Colours::black.withAlpha (0.16f));
            g.fillEllipse (juce::Rectangle<float> (2 * rr * sc, 2 * rr * sc).withCentre (c));
        }
        // point grave = preset choisi (tourne avec le numero du preset)
        const int slot = proc.getCurrentSlot();
        const float ang = juce::degreesToRadians (-135.0f + 270.0f * (float) slot / 9.0f);
        const float dr = layout::capDotR * sc;
        const juce::Point<float> d (c.x + std::sin (ang) * dr, c.y - std::cos (ang) * dr);
        g.setColour (juce::Colours::white.withAlpha (0.55f));
        g.fillEllipse (juce::Rectangle<float> (10.3f, 10.3f).withCentre (d.translated (0.9f, 1.05f)));
        juce::ColourGradient dg (juce::Colour (0xff2a2418), d.x - 2.0f, d.y - 2.0f, juce::Colour (0xff6d634a), d.x + 3.4f, d.y + 3.4f, false);
        g.setGradientFill (dg);
        g.fillEllipse (juce::Rectangle<float> (9.3f, 9.3f).withCentre (d));
    }

    bool hitTest (int x, int y) override
    {
        return getLocalBounds().toFloat().getCentre().getDistanceFrom ({ (float) x, (float) y }) <= layout::capD * 0.52f;
    }

    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (auto* ed = editorOf (this)) ed->showContextMenu (RingProcessor::lPresetKnob); return; }
        holding = true; moved = false; accum = 0.0f;
        lastPos = e.position; downTime = juce::Time::getMillisecondCounter();
        startTimerHz (20);
    }
    void mouseDrag (const juce::MouseEvent& e) override
    {
        if (! holding) return;
        if (e.getDistanceFromDragStart() > 3) moved = true;
        accum += (e.position.x - lastPos.x) - (e.position.y - lastPos.y);
        lastPos = e.position;
        while (accum >= 14.0f)  { accum -= 14.0f; step (+1); }
        while (accum <= -14.0f) { accum += 14.0f; step (-1); }
    }
    void mouseUp (const juce::MouseEvent&) override
    {
        if (! holding) return;
        holding = false; stopTimer();
        if (! moved && juce::Time::getMillisecondCounter() - downTime < 500) proc.cycleModes();   // appui = mode suivant
    }
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails& w) override { step (w.deltaY > 0 ? +1 : -1); }

private:
    void step (int d) { proc.loadPreset (juce::jlimit (0, 9, proc.getCurrentSlot() + d)); repaint(); }
    void timerCallback() override
    {
        if (! holding || moved) { stopTimer(); return; }
        if (juce::Time::getMillisecondCounter() - downTime >= 3000)
        {
            holding = false; stopTimer();
            if (proc.getCurrentSlot() > 0)
            {
                proc.saveUserPreset (proc.getCurrentSlot());                       // maintien 3 s = enregistrer
                if (auto* ed = editorOf (this)) ed->flash ("Saved to preset " + juce::String (proc.getCurrentSlot()));
            }
            repaint();
        }
    }

    RingProcessor& proc;
    const Art& art;
    bool holding = false, moved = false;
    float accum = 0.0f;
    juce::Point<float> lastPos;
    juce::uint32 downTime = 0;
};

// ------------------------------------------------------------------ zones cliquables (touches RM / UB / LB, PITCH-SHIFT, PHASER)
class ToggleZone : public juce::Component
{
public:
    ToggleZone (RingProcessor& p, const char* paramId, int learn) : proc (p), id (paramId), learnIdx (learn) {}
    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (auto* ed = editorOf (this)) ed->showContextMenu (learnIdx); return; }
        const float cur = proc.apvts.getRawParameterValue (id)->load();
        setParamGesture (proc.apvts, id, cur > 0.5f ? 0.0f : 1.0f, true, true);
    }
private:
    RingProcessor& proc; const char* id; int learnIdx;
};

class LadderZone : public juce::Component
{
public:
    explicit LadderZone (RingProcessor& p) : proc (p) {}
    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (auto* ed = editorOf (this)) ed->showContextMenu (RingProcessor::lPresetKnob); return; }
        const float y = e.position.y + (float) getY();
        int best = 0; float bd = 1.0e9f;
        for (int i = 0; i < 9; ++i) if (std::abs (y - layout::ladder[i].y) < bd) { bd = std::abs (y - layout::ladder[i].y); best = i; }
        proc.loadPreset (best + 1);
    }
private:
    RingProcessor& proc;
};

// ------------------------------------------------------------------ footswitchs (photo du kit dans le fond ; fonctionnement d'Echoflex)
class Footswitch : public juce::Component
{
public:
    Footswitch (RingProcessor& p, bool presetSwitch) : proc (p), isPreset (presetSwitch) {}
    ~Footswitch() override
    {
        if (down && isPreset) setParamGesture (proc.apvts, "presetfsw", 0.0f, false, true);   // jamais de footswitch bloque
    }
    int learnIdx() const { return isPreset ? RingProcessor::lPresetFsw : RingProcessor::lBypass; }
    bool learnRingShown() const { return proc.learnTarget.load() == learnIdx() && (juce::Time::getMillisecondCounter() / 300) % 2 == 0; }
    bool isDown() const { return down; }

    void paint (juce::Graphics& g) override
    {
        const auto c = getLocalBounds().toFloat().getCentre();
        if (down)                                                     // bouton assombri tant qu'on appuie
        {
            g.setColour (juce::Colours::black.withAlpha (0.25f));
            g.fillEllipse (juce::Rectangle<float> (layout::footR * 2.0f, layout::footR * 2.0f).withCentre (c));
        }
        if (learnRingShown())
        {
            g.setColour (kMidiRing);
            g.drawEllipse (juce::Rectangle<float> (layout::footR * 2.0f + 30.0f, layout::footR * 2.0f + 30.0f).withCentre (c), 3.0f);
        }
    }
    bool hitTest (int x, int y) override
    {
        return getLocalBounds().toFloat().getCentre().getDistanceFrom ({ (float) x, (float) y }) <= layout::footR * 1.35f;
    }
    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (auto* ed = editorOf (this)) ed->showContextMenu (learnIdx()); return; }
        down = true;
        if (isPreset) setParamGesture (proc.apvts, "presetfsw", 1.0f, true, false);
        else
        {
            const float cur = proc.apvts.getRawParameterValue ("active")->load();
            setParamGesture (proc.apvts, "active", cur > 0.5f ? 0.0f : 1.0f, true, true);   // bascule des l'appui
        }
        repaint();
    }
    void mouseUp (const juce::MouseEvent&) override
    {
        if (! down) return;
        down = false;
        if (isPreset) setParamGesture (proc.apvts, "presetfsw", 0.0f, false, true);
        repaint();
    }
private:
    RingProcessor& proc;
    bool isPreset, down = false;
};

// ------------------------------------------------------------------ la pedale entiere (repere 1175 x 900 unites)
class PedalContent : public juce::Component, private juce::Timer
{
public:
    explicit PedalContent (RingEditor& e, RingProcessor& p)
        : ed (e), proc (p), bigKnob (p, art), rmZone (p, "rm", 5), ubZone (p, "ub", 6), lbZone (p, "lb", 7),
          psZone (p, "ps", 8), phZone (p, "ph", 9), ladder (p), presetSw (p, true), bypassSw (p, false)
    {
        setSize ((int) kW, (int) kH);
        setOpaque (true);
        for (auto& l : lvl) l = 0.0f;
        if (auto xml = juce::XmlDocument::parse (juce::String::fromUTF8 (BinaryData::NineHandsLogoWhite_svg, BinaryData::NineHandsLogoWhite_svgSize)))
            logo = juce::Drawable::createFromSVG (*xml);

        nh::Knob::Layers L;
        L.shadow    = png (BinaryData::knob_shadow_png, BinaryData::knob_shadow_pngSize);
        L.crown     = png (BinaryData::knob_crown_png, BinaryData::knob_crown_pngSize);
        L.cap       = png (BinaryData::knob_cap_png, BinaryData::knob_cap_pngSize);
        L.marker    = png (BinaryData::knob_marker_png, BinaryData::knob_marker_pngSize);
        L.highlight = png (BinaryData::knob_highlight_png, BinaryData::knob_highlight_pngSize);
        for (int i = 0; i < 5; ++i)
        {
            knobs[i] = std::make_unique<nh::Knob> (*proc.apvts.getParameter (kIds[i]), L);
            knobs[i]->onRightClick = [this, i] (const juce::MouseEvent&) { ed.showContextMenu (i); };   // meme ordre que learnDef
            addAndMakeVisible (*knobs[i]);
            knobs[i]->setBounds (juce::Rectangle<float> (layout::knobD, layout::knobD).withCentre (layout::knobPos[i]).toNearestInt());
            lastKnob[i] = proc.apvts.getParameter (kIds[i])->getValue();
        }

        const float cw = layout::capD * 1.25f;
        addAndMakeVisible (bigKnob);  bigKnob.setBounds (juce::Rectangle<float> (cw, cw).withCentre (layout::capPos).toNearestInt());
        ToggleZone* faces[3] = { &rmZone, &ubZone, &lbZone };
        for (int i = 0; i < 3; ++i)
        {
            addAndMakeVisible (*faces[i]);
            faces[i]->setBounds (juce::Rectangle<float> (layout::faceW, layout::faceH).withCentre (layout::face[i]).toNearestInt());
        }
        addAndMakeVisible (psZone);   psZone.setBounds (juce::Rectangle<float> ((float) art.psWhite.getWidth() / layout::pxPerUnit + 16.0f, 30.0f).withCentre (layout::psPos).toNearestInt());
        addAndMakeVisible (phZone);   phZone.setBounds (layout::phPill.toNearestInt());
        addAndMakeVisible (ladder);
        ladder.setBounds (juce::Rectangle<float> (layout::ladder[0].x - 26.0f, layout::ladder[0].y - 19.0f, 205.0f,
                                                  layout::ladder[8].y - layout::ladder[0].y + 38.0f).toNearestInt());
        const float fw = layout::footR * 2.9f;
        addAndMakeVisible (presetSw); presetSw.setBounds (juce::Rectangle<float> (fw, fw).withCentre (layout::fsL).toNearestInt());
        addAndMakeVisible (bypassSw); bypassSw.setBounds (juce::Rectangle<float> (fw, fw).withCentre (layout::fsR).toNearestInt());

        lastModes = proc.getModes(); lastSlot = proc.getCurrentSlot();
        lastActive = proc.apvts.getRawParameterValue ("active")->load() > 0.5f;
        startTimerHz (30);
    }

    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { ed.showContextMenu (-1); return; }
        if (! layout::presetRect.contains (e.position)) return;
        if (statusAlpha > 0.0f) { statusUntil = 0.0; return; }                   // un clic fait revenir la barre de presets
        const auto r = layout::presetRect;
        if (e.position.x < r.getX() + arrowW)            proc.loadPreset (juce::jmax (0, proc.getCurrentSlot() - 1));
        else if (e.position.x > r.getRight() - arrowW)   proc.loadPreset (juce::jmin (9, proc.getCurrentSlot() + 1));
        else ed.showPresetMenu (localAreaToGlobal (r.toNearestInt()));
    }
    void mouseMove (const juce::MouseEvent& e) override { setHover (e.position); }
    void mouseExit (const juce::MouseEvent&) override   { setHover ({ -1.0f, -1.0f }); }

    void flash (const juce::String& t, double seconds)
    {
        statusText = t;
        statusUntil = juce::Time::getMillisecondCounterHiRes() + seconds * 1000.0;
    }

    void paint (juce::Graphics& g) override
    {
        // anti-gel v2 : on dessine le fond deja mis a l'echelle par le timer, rien de lourd ici
        lastPaintMs = juce::Time::getMillisecondCounter();
        repaintAskedMs = 0;
        g.fillAll (juce::Colour (0xff111112));                                  // autour des jacks : fond transparent
        g.setImageResamplingQuality (juce::Graphics::mediumResamplingQuality);
        g.drawImage (bgCache.isValid() ? bgCache : art.bg, juce::Rectangle<float> (kW, kH));
        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);

        const float gl = ed.glow;
        const int modes = proc.getModes();

        // halos sur la facade (doses par Glow), puis les lumieres elles-memes (jamais dosees)
        for (int i = 0; i < 15; ++i)
        {
            const float L = lvl[i] * gl;
            if (L > 0.004f && art.glow[i].isValid())
            {
                const auto& r = layout::glow[i];
                g.setOpacity (L);
                g.drawImage (art.glow[i], { r.x, r.y, r.w, r.h });
                g.setOpacity (1.0f);
            }
        }
        // touches RM / UB / LB : face orange quand le mode est actif, LED, inscription blanche
        for (int i = 0; i < 3; ++i)
        {
            const float L = lvl[gMode0 + i];
            drawCentred (g, art.faceOn, layout::face[i], 1.0f, L);
            if (L > 0.004f && art.glow[gMode0 + i].isValid())                  // le halo de la LED eclaire aussi la touche
            {
                const auto& r = layout::glow[gMode0 + i];
                g.saveState();
                g.reduceClipRegion (juce::Rectangle<float> (layout::faceW, layout::faceH).withCentre (layout::face[i]).toNearestInt());
                g.setOpacity (L * gl * 0.6f);
                g.drawImage (art.glow[gMode0 + i], { r.x, r.y, r.w, r.h });
                g.restoreState();
            }
            drawCentred (g, art.ledSOff, layout::modeLed[i]);
            drawCentred (g, art.ledSOn, layout::modeLed[i], 1.0f, L);
            drawCentred (g, art.lab[i], layout::label[i]);
        }
        for (int i = 0; i < 9; ++i) drawCentred (g, art.ledSOn, layout::ladder[i], 1.0f, lvl[gLad0 + i]);
        drawCentred (g, art.ledSOn, layout::phLed, 1.0f, lvl[gPhaser]);
        drawCentred (g, art.ledPOn, layout::presetLed, 1.0f, lvl[gPreset]);
        drawCentred (g, art.ledROn, layout::statusLed, 1.0f, lvl[gStatus]);

        // PITCH-SHIFT et PHASER : jaune = actif, blanc = inactif
        drawCentred (g, (modes & kPS) ? art.psYellow : art.psWhite, layout::psPos);
        drawCentred (g, (modes & kPH) ? art.phYellow : art.phWhite, layout::phTxt);

        // logo NINE HANDS | DSP (SVG officiel blanc, vectoriel)
        if (logo != nullptr)
        {
            const float lh = layout::logoW * 236.0f / 2510.0f;
            logo->drawWithin (g, juce::Rectangle<float> (layout::logoW, lh).withCentre (layout::logoPos), juce::RectanglePlacement::centred, 1.0f);
        }
        drawBar (g);
    }

    void editorResized() { resizeSettle = 4; }

private:
    static constexpr const char* kIds[5] = { "blend", "wave", "filter", "fine", "coarse" };
    static constexpr const char* kNames[5] = { "Blend", "Wave", "Filter / Rate", "Fine / Depth", "Coarse" };

    juce::String presetLine() const
    {
        const int s = proc.getCurrentSlot();
        if (s <= 0) return "Live knobs";
        juce::String t = juce::String (s) + juce::String (juce::CharPointer_UTF8 (" \xc2\xb7 "))
                       + (proc.isSlotFactory (s) ? juce::String (RingProcessor::factoryNames[s - 1]) : "Preset " + juce::String (s));
        if (proc.isPresetDirty()) t << "  *";
        return t;
    }

    void drawBar (juce::Graphics& g)
    {
        // pastille unique (400 x 38, reference Strong Pickle) : presets au repos, ligne d'etat pendant les reglages
        const auto r = layout::presetRect;
        const bool barHot = hover > 0 && statusAlpha <= 0.0f;
        g.setColour (barFill);
        g.fillRoundedRectangle (r, r.getHeight() * 0.5f);
        g.setColour (barEdge.withMultipliedAlpha (barHot ? 1.8f : 1.0f));
        g.drawRoundedRectangle (r.reduced (0.5f), r.getHeight() * 0.5f, 1.0f);
        g.setFont (NineHandsMenu::fnt (ed.mediumFace, layout::presetFont));
        if (statusAlpha > 0.0f)
        {
            g.setColour (barInk.withAlpha (statusAlpha));
            g.drawFittedText (statusText, r.reduced (r.getHeight() * 0.5f, 0.0f).toNearestInt(), juce::Justification::centred, 1, 0.6f);
        }
        const float a = 1.0f - statusAlpha;
        if (a <= 0.0f) return;
        auto arrow = [&] (juce::Rectangle<float> ar, bool left, bool hot)
        {
            juce::Path p; const auto c = ar.getCentre(); const float sz = 5.5f;
            if (left) p.addTriangle (c.x + sz * 0.6f, c.y - sz, c.x + sz * 0.6f, c.y + sz, c.x - sz * 0.8f, c.y);
            else      p.addTriangle (c.x - sz * 0.6f, c.y - sz, c.x - sz * 0.6f, c.y + sz, c.x + sz * 0.8f, c.y);
            g.setColour (barInk.withAlpha ((hot ? 1.0f : 0.6f) * a));
            g.fillPath (p);
        };
        arrow (r.withWidth (arrowW), true, hover == 1);
        arrow (r.withTrimmedLeft (r.getWidth() - arrowW), false, hover == 3);
        g.setColour (barInk.withAlpha ((hover == 2 ? 1.0f : 0.92f) * a));
        g.drawFittedText (presetLine(), r.reduced (arrowW, 0.0f).toNearestInt(), juce::Justification::centred, 1, 0.7f);
    }

    void setHover (juce::Point<float> p)
    {
        const auto r = layout::presetRect;
        int h = 0;
        if (r.contains (p)) h = p.x < r.getX() + arrowW ? 1 : (p.x > r.getRight() - arrowW ? 3 : 2);
        if (h != hover) { hover = h; askRepaint (r.toNearestInt().expanded (2)); }
    }

    // niveau de chaque lumiere : attaque rapide, courte remanence (fondu 0,45 / 0,28 par image)
    void updateLevels()
    {
        const auto now = juce::Time::getMillisecondCounter();
        const int modes = proc.getModes(), slot = proc.getCurrentSlot();
        const bool saveFlash = (now - proc.lastSaveMs) < 900 && ((now / 60) % 2 == 0);
        const bool holdBlink = bigKnob.isHoldBlinking() && ((now / 60) % 2 == 0);
        bool presetLit = slot > 0;
        if (slot > 0 && proc.isPresetDirty()) presetLit = (now / 120) % 2 == 0;   // potards bouges depuis le chargement
        if (proc.isTuning()) presetLit = (now / 250) % 2 == 0;                    // accordage en cours
        bool target[15];
        for (int i = 0; i < 9; ++i) target[gLad0 + i] = (i + 1 == slot) || saveFlash || holdBlink;
        target[gMode0 + 0] = (modes & kRM) != 0;
        target[gMode0 + 1] = (modes & kUB) != 0;
        target[gMode0 + 2] = (modes & kLB) != 0;
        target[gPhaser] = (modes & kPH) != 0;
        target[gPreset] = presetLit;
        target[gStatus] = proc.apvts.getRawParameterValue ("active")->load() > 0.5f;
        for (int i = 0; i < 15; ++i)
            lvl[i] += ((target[i] ? 1.0f : 0.0f) - lvl[i]) * (target[i] ? 0.45f : 0.28f);
    }

    void askRepaint (juce::Rectangle<int> r)
    {
        repaint (r);
        if (repaintAskedMs == 0) repaintAskedMs = juce::Time::getMillisecondCounter();
    }

    // fond a la taille reelle en pixels (fenetre x echelle de l'ecran) : refait par le timer seulement
    void updateBackgroundCache (juce::uint32 now)
    {
        if (now - lastScaleCheck >= 250)
        {
            lastScaleCheck = now;
            const float sc = juce::Component::getApproximateScaleFactorForComponent (&ed);
            if (std::abs (sc - displayScale) > 0.001f) { displayScale = sc; resizeSettle = juce::jmax (resizeSettle, 1); }
        }
        if (resizeSettle > 0 && --resizeSettle == 0)
        {
            const float px = (float) ed.getHeight() / kH * displayScale;
            const int tw = juce::jlimit (64, art.bg.getWidth(), (int) std::lround (kW * px));
            const int th = juce::jlimit (48, art.bg.getHeight(), (int) std::lround (kH * px));
            if (! bgCache.isValid() || bgCache.getWidth() != tw || bgCache.getHeight() != th)
            {
                bgCache = (tw == art.bg.getWidth()) ? art.bg : art.bg.rescaled (tw, th, juce::Graphics::highResamplingQuality);
                askRepaint (getLocalBounds());
            }
        }
    }

    void detectEvents()
    {
        // ligne d'etat : valeurs en direct pendant les reglages (souris, molette, automation, MIDI)
        for (int i = 0; i < 5; ++i)
        {
            const float v = proc.apvts.getParameter (kIds[i])->getValue();
            if (std::abs (v - lastKnob[i]) > 1.0e-4f)
            {
                lastKnob[i] = v;
                flash (juce::String (kNames[i]) + "   " + juce::String ((int) std::lround (v * 100.0f)) + " %", 2.5);
            }
        }
        const int modes = proc.getModes();
        if (modes != lastModes)
        {
            juce::StringArray m;
            if (modes & kRM) m.add ("RM");
            if (modes & kUB) m.add ("UB");
            if (modes & kLB) m.add ("LB");
            if (modes & kPS) m.add ("PITCH-SHIFT");
            if (modes & kPH) m.add ("PHASER");
            flash (m.isEmpty() ? juce::String ("Dry (no mode)") : m.joinIntoString (juce::String (juce::CharPointer_UTF8 (" \xc2\xb7 "))), 2.0);
            lastModes = modes;
        }
        const bool active = proc.apvts.getRawParameterValue ("active")->load() > 0.5f;
        if (active != lastActive) { flash (active ? "Effect on" : "Bypass", 1.6); lastActive = active; }
        const bool tuned = proc.isTunedActive();
        if (proc.isTuning()) flash ("TUNE  play a note...", 0.3);
        else if (tuned && ! lastTuned) flash ("TUNED  " + juce::String (proc.getTunedHz(), 1) + " Hz", 3.0);
        lastTuned = tuned;
        const int lt = proc.learnTarget.load();
        if (lt >= 0) flash (juce::String ("MIDI LEARN  ") + RingProcessor::learnDef (lt).name, 0.25);
        const int learned = proc.lastLearned.exchange (-1);
        if (learned >= 0) flash (juce::String (RingProcessor::learnDef (learned).name) + " = " + proc.learnAssignText (learned), 2.5);
    }

    void timerCallback() override
    {
        const auto nowMs = juce::Time::getMillisecondCounter();
        ed.checkRenderer();                                // fenetre recreee par l'hote (ecran, echelle...) ?
        updateBackgroundCache (nowMs);
        if (repaintAskedMs != 0 && nowMs - repaintAskedMs > 1500 && isShowing())   // chien de garde
        {
            repaintAskedMs = 0;
            ed.resetRenderer();
            repaint();
        }
        if (++glowTick >= 90)                              // reglage Glow commun a toutes les fenetres (relu toutes les 3 s)
        {
            glowTick = 0;
            const float gl = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;
            if (std::abs (gl - ed.glow) > 0.001f) { ed.glow = gl; askRepaint (getLocalBounds()); }
        }

        updateLevels();
        detectEvents();

        // on ne redessine une zone que si ce qu'elle affiche a change (aucun travail au repos)
        auto changed = [] (float& drawn, float now) { if (std::abs (drawn - now) < 0.002f) return false; drawn = now; return true; };
        for (int i = 0; i < 15; ++i)
            if (changed (drawnLvl[i], lvl[i]))
            {
                const auto& r = layout::glow[i];
                askRepaint (juce::Rectangle<float> (r.x, r.y, r.w, r.h).getSmallestIntegerContainer().expanded (2));
                if (i >= gMode0 && i < gMode0 + 3)
                    askRepaint (juce::Rectangle<float> (layout::faceW, layout::faceH).withCentre (layout::face[i - gMode0]).getSmallestIntegerContainer().expanded (3));
            }
        const int modes = proc.getModes();
        if ((modes ^ drawnModes) & kPS) askRepaint (juce::Rectangle<float> ((float) art.psWhite.getWidth() / layout::pxPerUnit + 4, (float) art.psWhite.getHeight() / layout::pxPerUnit + 4).withCentre (layout::psPos).toNearestInt());
        if ((modes ^ drawnModes) & kPH) askRepaint (juce::Rectangle<float> ((float) art.phWhite.getWidth() / layout::pxPerUnit + 4, (float) art.phWhite.getHeight() / layout::pxPerUnit + 4).withCentre (layout::phTxt).toNearestInt());
        drawnModes = modes;

        // pastille : fondu croise presets <-> ligne d'etat (~120 ms a l'apparition, ~300 ms au retour)
        const float st = juce::Time::getMillisecondCounterHiRes() < statusUntil ? 1.0f : 0.0f;
        statusAlpha += (st - statusAlpha) * (st > statusAlpha ? 0.45f : 0.30f);
        if (statusAlpha < 0.005f) statusAlpha = 0.0f;
        if (statusAlpha > 0.995f) statusAlpha = 1.0f;
        const auto pl = presetLine();
        if (changed (drawnStatus, statusAlpha) || statusText != drawnStatusText || pl != drawnPreset)
        {
            drawnStatusText = statusText; drawnPreset = pl;
            askRepaint (layout::presetRect.getSmallestIntegerContainer().expanded (2));
        }

        const int slot = proc.getCurrentSlot();
        if (slot != drawnSlot || bigKnob.isHeld() != drawnHeld) { drawnSlot = slot; drawnHeld = bigKnob.isHeld(); bigKnob.repaint(); }
        if (presetSw.learnRingShown() != drawnRingPreset) { drawnRingPreset = ! drawnRingPreset; presetSw.repaint(); }
        if (bypassSw.learnRingShown() != drawnRingBypass) { drawnRingBypass = ! drawnRingBypass; bypassSw.repaint(); }
    }

    RingEditor& ed;
    RingProcessor& proc;
    Art art;
    std::unique_ptr<juce::Drawable> logo;
    std::unique_ptr<nh::Knob> knobs[5];
    float lastKnob[5] {};
    int lastModes = -1, lastSlot = -1;
    bool lastActive = false, lastTuned = false;
    float lvl[15];
    float drawnLvl[15] = { -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 };
    int drawnModes = -1, drawnSlot = -1, hover = 0, glowTick = 0;
    bool drawnHeld = false, drawnRingPreset = false, drawnRingBypass = false;
    juce::String statusText, drawnStatusText, drawnPreset;
    double statusUntil = 0.0;
    float statusAlpha = 0.0f, drawnStatus = -1.0f;

    // anti-gel v2
    juce::Image bgCache;
    int resizeSettle = 2;
    float displayScale = 1.0f;
    juce::uint32 lastScaleCheck = 0, lastPaintMs = 0, repaintAskedMs = 0;

    BigKnob bigKnob;
    ToggleZone rmZone, ubZone, lbZone, psZone, phZone;
    LadderZone ladder;
    Footswitch presetSw, bypassSw;
};

// ------------------------------------------------------------------ fenetre
int RingEditor::sizeHeight (int idx) { return kHeights[juce::jlimit (0, numSizes - 1, idx)]; }

RingEditor::RingEditor (RingProcessor& p) : AudioProcessorEditor (&p), proc (p)
{
    setOpaque (true);
    mediumFace  = juce::Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace    = juce::Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    regularFace = juce::Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    menuLnf.f = { regularFace, mediumFace, boldFace };
    glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;

    content = std::make_unique<PedalContent> (*this, proc);
    addAndMakeVisible (*content);
    const double aspect = (double) kW / (double) kH;
    setResizable (true, true);
    setResizeLimits ((int) std::lround (kHeights[0] * aspect), kHeights[0], (int) std::lround (kHeightMax * aspect), kHeightMax);   // jamais plus petit que la taille par defaut
    getConstrainer()->setFixedAspectRatio (aspect);
    hostLock.setLimits ((int) std::lround (kHeights[0] * aspect), kHeights[0], (int) std::lround (kHeightMax * aspect), kHeightMax);
    // ouverture : taille enregistree pour cette instance (projet), sinon la taille par defaut choisie dans le menu
    const int saved = juce::jlimit (-1, 2, proc.uiScaleIdx.load());
    const int idx = saved >= 0 ? saved : WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes);
    setSize ((int) std::lround (sizeHeight (idx) * aspect), sizeHeight (idx));
}

RingEditor::~RingEditor()
{
    juce::PopupMenu::dismissAllActiveMenus();
}

// anti-gel (Windows) : moteur de rendu logiciel, reapplique si la fenetre de l'hote change
void RingEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer == nullptr) return;
   #if JUCE_WINDOWS
    int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
    if (sw < 0) sw = 0;
    if (peer->getCurrentRenderingEngine() != sw) peer->setCurrentRenderingEngine (sw);
   #endif
    if ((void*) peer != lastPeer) { lastPeer = (void*) peer; repaint(); }
    lastRendererCheck = juce::Time::getMillisecondCounter();
}
void RingEditor::checkRenderer()
{
    if ((void*) getPeer() != lastPeer || juce::Time::getMillisecondCounter() - lastRendererCheck >= 1000) useSoftwareRenderer();
    hostLock.track (*this);
}
void RingEditor::resetRenderer() { lastPeer = nullptr; useSoftwareRenderer(); repaint(); }
void RingEditor::paint (juce::Graphics& g) { g.fillAll (juce::Colour (0xff111112)); }
void RingEditor::parentHierarchyChanged() { useSoftwareRenderer(); hostLock.track (*this); }
void RingEditor::visibilityChanged() { useSoftwareRenderer(); if (isShowing()) repaint(); }

void RingEditor::resized()
{
    content->setTransform (juce::AffineTransform::scale ((float) getHeight() / kH));
    content->setBounds (0, 0, (int) kW, (int) kH);
    content->editorResized();                        // jamais de setSize ici (boucle avec l'hote a 125 / 150 %)
}

int RingEditor::currentSizeIndex() const
{
    for (int i = 0; i < numSizes; ++i) if (std::abs (getHeight() - kHeights[i]) <= 2) return i;
    return -1;
}

void RingEditor::setScaleIndex (int idx)
{
    idx = juce::jlimit (-1, numSizes - 1, idx);
    proc.uiScaleIdx = idx;
    const int i = idx < 0 ? WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes) : idx;
    setSize ((int) std::lround (sizeHeight (i) * (double) kW / (double) kH), sizeHeight (i));
    hostLock.enforce();
}

void RingEditor::flash (const juce::String& text, double seconds) { content->flash (text, seconds); }

// ------------------------------------------------------------------ menus (design d'Octopus, NineHandsMenu.h)
void RingEditor::showPresetMenu (juce::Rectangle<int> screenArea)
{
    juce::PopupMenu m;
    m.setLookAndFeel (&menuLnf);
    const int slot = proc.getCurrentSlot();
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoPreset, menuAccent, "Presets",
                              slot > 0 ? "Preset " + juce::String (slot) : juce::String ("Live knobs"));
    for (int s = 1; s <= 9; ++s)
        m.addItem (100 + s, "Preset " + juce::String (s) + (proc.isSlotFactory (s) ? "  " + juce::String (RingProcessor::factoryNames[s - 1]) : juce::String ("  (user)")),
                   true, slot == s);
    m.addItem (100, "Live knobs (no preset)", true, slot == 0);
    m.addSeparator();
    m.addItem (110, "Load the factory Phaser sound");
    m.showMenuAsync (juce::PopupMenu::Options().withTargetScreenArea (screenArea),
        [safe = juce::Component::SafePointer<RingEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            if (r >= 100 && r <= 109) safe->proc.loadPreset (r - 100);
            else if (r == 110) safe->proc.loadFactorySound (9);
        });
}

juce::PopupMenu RingEditor::buildContextMenu (int learnIdx)
{
    using namespace NineHandsMenu;
    juce::PopupMenu menu;
    menu.setLookAndFeel (&menuLnf);
    const int lt = proc.learnTarget.load();
    auto assign = [this] (int i) { const auto as = proc.learnAssignText (i); return as == "none" ? juce::String ("not assigned") : as; };
    if (learnIdx >= 0)
    {
        // menu d'une commande (tronc commun) : en-tete, MIDI Learn, Clear MIDI, Cancel MIDI learn
        const juce::String name = RingProcessor::learnDef (learnIdx).name;
        const int ico = learnIdx < 5 ? icoKnob : (learnIdx >= RingProcessor::lPresetFsw ? icoSwitch : (learnIdx == RingProcessor::lPresetKnob ? icoKnob : icoSwitch));
        addHeader (menu, menuLnf.f, ico, menuAccent, name, "MIDI: " + assign (learnIdx));
        menu.addItem (1000 + learnIdx, "MIDI Learn: " + name, true, lt == learnIdx);
        menu.addItem (1100 + learnIdx, "Clear MIDI: " + name, proc.learnAssignText (learnIdx) != "none");
        menu.addItem (1200, "Cancel MIDI learn", lt >= 0);
        return menu;
    }

    addHeader (menu, menuLnf.f, icoPedal, menuAccent, "Ring Think", "Ring modulator  v" + juce::String (JucePlugin_VersionString));
    const int slot = proc.getCurrentSlot();
    juce::PopupMenu factory, load, save;
    for (int i = 0; i < 10; ++i)
        factory.addItem (130 + i, juce::String (i + 1) + ". " + RingProcessor::factoryNames[i]);
    factory.addSeparator();
    factory.addItem (112, slot > 0 ? "Restore factory preset " + juce::String (slot) : juce::String ("Restore factory preset"), slot > 0);
    factory.addItem (113, "Restore ALL factory presets");
    menu.addSubMenu ("Factory presets", factory);
    for (int s = 1; s <= 9; ++s)
    {
        const juce::String what = proc.isSlotFactory (s) ? juce::String (RingProcessor::factoryNames[s - 1]) : juce::String ("user");
        load.addItem (100 + s, "Preset " + juce::String (s) + "  (" + what + ")", true, slot == s);
        save.addItem (140 + s, "Preset " + juce::String (s) + "  (overwrite)");
    }
    load.addSeparator();
    load.addItem (100, "Live knobs (no preset)", true, slot == 0);
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();
    menu.addItem (120, "Next mode combination (push the MODE knob)");
    menu.addSeparator();

    juce::PopupMenu midi;
    midi.addSectionHeader ("MIDI Learn");
    for (int i = 0; i < RingProcessor::numLearn; ++i)
        midi.addItem (1000 + i, juce::String ("Learn: ") + RingProcessor::learnDef (i).name + "  (" + assign (i) + ")", true, lt == i);
    midi.addSeparator();
    midi.addItem (1200, "Cancel MIDI learn", lt >= 0);
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    NineHandsWindow::addMidiFootswitchMode (midi, proc.isBypassLatching());
    midi.addSeparator();
    NineHandsWindow::addProgramChangeInfo (midi);
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();

    const char* names[numSizes] = { "60 %", "75 %", "100 %" };
    menu.addSubMenu ("Plugin size", NineHandsWindow::sizeMenu (JucePlugin_Name, numSizes, names, kHeights, getHeight()));
    menu.addSubMenu ("Glow intensity", NineHandsWindow::glowMenu (juce::roundToInt (glow * 100.0f)));
    return menu;
}

void RingEditor::showContextMenu (int learnIdx)
{
    auto menu = buildContextMenu (learnIdx);
    menu.showMenuAsync (juce::PopupMenu::Options().withMousePosition(),          // toujours la ou l'on clique
        [safe = juce::Component::SafePointer<RingEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& ed = *safe;
            auto& pr = ed.proc;
            const int s = pr.getCurrentSlot();
            int inst = pr.uiScaleIdx.load();
            const int sz = NineHandsWindow::handleSize (r, JucePlugin_Name, numSizes, inst);
            if (sz >= 0) { ed.setScaleIndex (inst); return; }
            if (const int pc = NineHandsWindow::handleGlow (r, JucePlugin_Name))
            {
                ed.glow = (float) pc / 100.0f;
                ed.repaint();
                ed.flash ("Glow  " + juce::String (pc) + " %");
                return;
            }
            if      (r == NineHandsWindow::idLatch)     pr.setBypassLatching (true);
            else if (r == NineHandsWindow::idMomentary) pr.setBypassLatching (false);
            else if (r >= 100 && r <= 109) pr.loadPreset (r - 100);
            else if (r >= 130 && r < 140) pr.loadFactorySound (r - 130);
            else if (r > 140 && r < 150) { pr.saveUserPreset (r - 140); pr.loadPreset (r - 140); ed.flash ("Saved to preset " + juce::String (r - 140)); }
            else if (r == 112) pr.restoreFactoryPreset (s);
            else if (r == 113) { pr.restoreAllFactory(); ed.flash ("Factory presets restored"); }
            else if (r == 120) pr.cycleModes();
            else if (r >= 1000 && r < 1000 + RingProcessor::numLearn)
                pr.learnTarget.store (pr.learnTarget.load() == r - 1000 ? -1 : r - 1000);
            else if (r >= 1100 && r < 1100 + RingProcessor::numLearn)
            {
                pr.clearLearn (r - 1100);
                ed.flash (juce::String (RingProcessor::learnDef (r - 1100).name) + "  MIDI cleared");
            }
            else if (r == 1200) pr.learnTarget.store (-1);
            else if (r == 1201) { pr.learnTarget.store (-1); pr.resetMidiMap(); ed.flash ("All MIDI cleared"); }
        });
}
