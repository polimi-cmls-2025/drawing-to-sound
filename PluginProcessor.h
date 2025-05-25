#pragma once
#include <JuceHeader.h>
#include "GranularPitchShifter.h"

class ShimmerReverbPlugin : public juce::AudioProcessor
{
public:
    ShimmerReverbPlugin();
    ~ShimmerReverbPlugin() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;

    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int index, const juce::String& newName) override;

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;
    
    juce::AudioProcessorValueTreeState parameters;
    juce::AudioProcessorValueTreeState& getValueTreeState() { return parameters; }

private:
    juce::dsp::Reverb reverb;
    juce::AudioBuffer<float> reverbBuffer;

    // Custom pitch shifter class
    GranularPitchShifter pitchShifter;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ShimmerReverbPlugin)
};
