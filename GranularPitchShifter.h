#pragma once
#include <JuceHeader.h>

class GranularPitchShifter
{
public:
    void prepare(double sampleRate, int samplesPerBlock);
    void processBlock(juce::AudioBuffer<float>& buffer);
    void setPitchSemitones(float semitones);

private:
    // Thread-safe parameter updates
    juce::CriticalSection paramLock;
    
    // Atomic parameter storage
    std::atomic<float> pitchRatio{1.0f};
    
    // Constants
    static constexpr int maxGrainSize = 1024; // Safer upper limit
    double sr = 44100.0;
    int grainSize = 512;

    // Delay lines with bounds checking
    juce::OwnedArray<juce::dsp::DelayLine<float>> delayLines;
};