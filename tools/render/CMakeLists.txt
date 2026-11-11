# Outil hors plugin : compile le processeur + la fenetre de RING THINK sous Linux et exporte des captures PNG
cmake_minimum_required(VERSION 3.22)
project(RingThinkRender VERSION 1.0.0)
set(CMAKE_CXX_STANDARD 20)
add_subdirectory(${JUCE_DIR} JUCE)
set(W ${CMAKE_CURRENT_SOURCE_DIR}/../..)
file(STRINGS ${W}/CMakeLists.txt _ver REGEX "^project\\(WigaRingThink VERSION")
string(REGEX MATCH "[0-9]+\\.[0-9]+\\.[0-9]+" RT_VERSION "${_ver}")
set(ASSETS background.png cap_big.png face_on.png label_rm.png label_ub.png label_lb.png
  pitchshift_white.png pitchshift_yellow.png phaser_white.png phaser_yellow.png ledS_on.png ledS_off.png ledP_on.png ledR_on.png
  glow_lad0.png glow_lad1.png glow_lad2.png glow_lad3.png glow_lad4.png glow_lad5.png glow_lad6.png glow_lad7.png glow_lad8.png
  glow_mode_rm.png glow_mode_ub.png glow_mode_lb.png glow_phaser.png glow_preset.png glow_status.png
  knob_shadow.png knob_crown.png knob_cap.png knob_marker.png knob_highlight.png
  Poppins-Regular.ttf Poppins-Medium.ttf Poppins-Bold.ttf NineHandsLogoWhite.svg)
list(TRANSFORM ASSETS PREPEND ${W}/)
juce_add_binary_data(RingRenderAssets SOURCES ${ASSETS})
juce_add_console_app(RingThinkRender PRODUCT_NAME "RingThinkRender")
target_sources(RingThinkRender PRIVATE main.cpp ${W}/PluginProcessor.cpp ${W}/PluginEditor.cpp)
target_include_directories(RingThinkRender PRIVATE ${W})
target_compile_definitions(RingThinkRender PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_ALSA=0 JUCE_JACK=0
  JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0 JUCE_USE_XSHM=0 JucePlugin_Name="Ring Think" JucePlugin_Build_VST3=0
  JucePlugin_VersionString="${RT_VERSION}" JUCE_STANDALONE_APPLICATION=1 JUCE_MODAL_LOOPS_PERMITTED=1)
target_link_libraries(RingThinkRender PRIVATE RingRenderAssets juce::juce_audio_utils juce::juce_recommended_config_flags)
