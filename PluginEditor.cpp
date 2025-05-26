#include "PluginEditor.h"

ShimmerReverbPluginEditor::ShimmerReverbPluginEditor (ShimmerReverbPlugin& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
   auto& params = processorRef.getValueTreeState();

    auto styleSlider = [] (juce::Slider& s)
    {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::TextBoxBelow, true, 50, 20);
        s.setColour(juce::Slider::rotarySliderFillColourId, juce::Colours::skyblue);
    };

    // Pitch
    styleSlider(pitchSlider);
    pitchLabel.setText("Pitch", juce::dontSendNotification);
    addAndMakeVisible(pitchSlider);
    addAndMakeVisible(pitchLabel);
    pitchAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(params, "pitch", pitchSlider);

    // Decay
    styleSlider(decaySlider);
    decayLabel.setText("Decay", juce::dontSendNotification);
    addAndMakeVisible(decaySlider);
    addAndMakeVisible(decayLabel);
    decayAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(params, "decay", decaySlider);

    // Feedback
    styleSlider(feedbackSlider);
    feedbackLabel.setText("Feedback", juce::dontSendNotification);
    addAndMakeVisible(feedbackSlider);
    addAndMakeVisible(feedbackLabel);
    feedbackAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(params, "feedback", feedbackSlider);

    // Mix
    styleSlider(mixSlider);
    mixLabel.setText("Mix", juce::dontSendNotification);
    addAndMakeVisible(mixSlider);
    addAndMakeVisible(mixLabel);
    mixAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(params, "mix", mixSlider);

    setSize(400, 300);
}

ShimmerReverbPluginEditor::~ShimmerReverbPluginEditor() {}

void ShimmerReverbPluginEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colours::darkslategrey);
    g.setColour (juce::Colours::white);
    g.setFont (18.0f);
    g.drawFittedText ("Shimmer Reverb", getLocalBounds().removeFromTop(40), juce::Justification::centred, 1);
}

void ShimmerReverbPluginEditor::resized()
{
    auto area = getLocalBounds().reduced(20);
    auto sliderArea = area.removeFromBottom(200);
    auto labelHeight = 20;

    auto row = [&] (juce::Slider& s, juce::Label& l, juce::Rectangle<int> r)
    {
        l.setBounds(r.removeFromTop(labelHeight));
        s.setBounds(r);
    };

    auto quarter = sliderArea.removeFromLeft(sliderArea.getWidth() / 4);
    row(pitchSlider, pitchLabel, quarter);

    quarter = sliderArea.removeFromLeft(sliderArea.getWidth() / 3);
    row(decaySlider, decayLabel, quarter);

    quarter = sliderArea.removeFromLeft(sliderArea.getWidth() / 2);
    row(feedbackSlider, feedbackLabel, quarter);

    row(mixSlider, mixLabel, sliderArea);
}
