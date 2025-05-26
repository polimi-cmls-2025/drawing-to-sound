#pragma once
#include <JuceHeader.h>
#include "PluginProcessor.h"

class ShimmerReverbPluginEditor  : public juce::AudioProcessorEditor
{
public:
    ShimmerReverbPluginEditor (ShimmerReverbPlugin&);
    ~ShimmerReverbPluginEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    ShimmerReverbPlugin& processorRef;

    juce::Slider pitchSlider;
    juce::Slider decaySlider;
    juce::Slider feedbackSlider;
    juce::Slider mixSlider;

    juce::Label pitchLabel;
    juce::Label decayLabel;
    juce::Label feedbackLabel;
    juce::Label mixLabel;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> pitchAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> decayAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> feedbackAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> mixAttachment;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ShimmerReverbPluginEditor)
};
