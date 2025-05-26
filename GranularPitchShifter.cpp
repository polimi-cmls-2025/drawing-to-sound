#include "GranularPitchShifter.h"

void GranularPitchShifter::prepare(double sampleRate, int samplesPerBlock)
{
    const juce::ScopedLock sl(paramLock);
    
    sr = sampleRate;
    grainSize = juce::jmin(512, maxGrainSize); // Hard limit
    
    // Initialize delay lines safely
    delayLines.clear();
    for (int ch = 0; ch < 2; ++ch) // Fixed stereo
    {
        auto* delay = new juce::dsp::DelayLine<float>(maxGrainSize * 2); // Extra headroom
        delay->prepare({sampleRate, (juce::uint32)samplesPerBlock, 2});
        delayLines.add(delay);
    }
}

void GranularPitchShifter::setPitchSemitones(float semitones)
{
    const juce::ScopedLock sl(paramLock);
    pitchRatio.store(std::pow(2.0f, juce::jlimit(-24.0f, 24.0f, semitones) / 12.0f));
}

void GranularPitchShifter::processBlock(juce::AudioBuffer<float>& buffer)
{
    // 1. Input validation
    if (buffer.getNumSamples() <= 0 || delayLines.isEmpty()) 
        return;

    // 2. Get pitch ratio atomically
    const float currentPitchRatio = pitchRatio.load();

    // 3. Safe channel processing
    const int numChannels = juce::jmin(buffer.getNumChannels(), delayLines.size());
    
    for (int ch = 0; ch < numChannels; ++ch)
    {
        if (auto* delay = delayLines[ch])
        {
            auto* channelData = buffer.getWritePointer(ch);
            const int numSamples = buffer.getNumSamples();

            // 4. Sample-by-sample with bounds checking
            for (int i = 0; i < numSamples; ++i)
            {
                const float inputSample = channelData[i];
                delay->pushSample(ch, inputSample);

                // 5. Safe delay time calculation
                float readDelay = grainSize / currentPitchRatio;
                readDelay = juce::jlimit(1.0f, (float)(maxGrainSize - 1), readDelay);

                channelData[i] = delay->popSample(ch, readDelay, true); // Safe interpolation
            }
        }
    }
}