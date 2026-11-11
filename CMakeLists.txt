cmake_minimum_required(VERSION 3.22)

# macOS: universal binary (Apple Silicon + Intel), minimum macOS 10.13 (must be set BEFORE project())
if(APPLE)
  set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "" FORCE)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.13" CACHE STRING "" FORCE)
endif()

project(WigaRingThink VERSION 3.0.3)

include(FetchContent)
FetchContent_Declare(JUCE
  GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
  GIT_TAG 8.0.15
  GIT_SHALLOW ON)
FetchContent_MakeAvailable(JUCE)

# images de la pedale (tools/export_plugin.py : fond 2350 x 1800, sprites 2x, halos des LED, calques du potard),
# police Poppins et logo NINE HANDS | DSP integres au plugin (rien a installer a cote)
juce_add_binary_data(RingAssets SOURCES
  background.png
  cap_big.png face_on.png label_rm.png label_ub.png label_lb.png
  pitchshift_white.png pitchshift_yellow.png phaser_white.png phaser_yellow.png
  ledS_on.png ledS_off.png ledP_on.png ledR_on.png
  glow_lad0.png glow_lad1.png glow_lad2.png glow_lad3.png glow_lad4.png glow_lad5.png glow_lad6.png glow_lad7.png glow_lad8.png
  glow_mode_rm.png glow_mode_ub.png glow_mode_lb.png glow_phaser.png glow_preset.png glow_status.png
  knob_shadow.png knob_crown.png knob_cap.png knob_marker.png knob_highlight.png
  Poppins-Regular.ttf Poppins-Medium.ttf Poppins-Bold.ttf
  NineHandsLogoWhite.svg)

# VST3 everywhere; Audio Unit in addition on macOS (Logic, GarageBand, ...)
if(APPLE)
  set(RING_FORMATS VST3 AU)
else()
  set(RING_FORMATS VST3)
endif()

juce_add_plugin(RingThingSSB
  COMPANY_NAME "NINE HANDS | DSP"
  PLUGIN_MANUFACTURER_CODE Wiga
  PLUGIN_CODE WgRt
  FORMATS ${RING_FORMATS}
  AU_MAIN_TYPE kAudioUnitType_MusicEffect
  VST3_CATEGORIES Fx Modulation
  IS_SYNTH FALSE
  NEEDS_MIDI_INPUT TRUE
  NEEDS_MIDI_OUTPUT FALSE
  PRODUCT_NAME "Ring Think"
  COPY_PLUGIN_AFTER_BUILD FALSE)

target_sources(RingThingSSB PRIVATE
  PluginProcessor.cpp
  PluginEditor.cpp)

target_compile_definitions(RingThingSSB PUBLIC
  JUCE_WEB_BROWSER=0
  JUCE_USE_CURL=0
  JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(RingThingSSB
  PRIVATE
    RingAssets
    juce::juce_audio_utils
  PUBLIC
    juce::juce_recommended_config_flags
    juce::juce_recommended_warning_flags)
