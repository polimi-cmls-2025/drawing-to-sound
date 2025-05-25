#include "PluginProcessor.h"
#include "PluginEditor.h"

ShimmerReverbPlugin::ShimmerReverbPlugin()
    : parameters(*this, nullptr, "PARAMETERS", {
        std::make_unique<juce::AudioParameterFloat>("pitch", "Pitch Shift", -24.0f, 24.0f, 12.0f),
        std::make_unique<juce::AudioParameterFloat>("decay", "Reverb Decay", 0.1f, 10.0f, 2.0f),
        std::make_unique<juce::AudioParameterFloat>("feedback", "Feedback", 0.0f, 0.95f, 0.4f),
        std::make_unique<juce::AudioParameterFloat>("mix", "Wet/Dry Mix", 0.0f, 1.0f, 0.5f)
    })
{}

ShimmerReverbPlugin::~ShimmerReverbPlugin(){}

void ShimmerReverbPlugin::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    juce::dsp::ProcessSpec spec { sampleRate, static_cast<juce::uint32>(samplesPerBlock), 2 };
    reverb.prepare(spec);
    juce::dsp::Reverb::Parameters reverbParams;
    reverbParams.roomSize = 0.8f;
    reverbParams.damping = 0.7f;
    reverbParams.wetLevel = 0.6f;
    reverbParams.dryLevel = 0.4f;
    reverbParams.width = 0.5f;
    reverbParams.freezeMode = 0.0f;
    reverb.setParameters(reverbParams);

    pitchShifter.prepare(sampleRate, samplesPerBlock);
    pitchShifter.setPitchSemitones(*parameters.getRawParameterValue("pitch"));

    reverbBuffer.setSize(2, samplesPerBlock);
}

void ShimmerReverbPlugin::releaseResources()
{
    reverb.reset();
}

void ShimmerReverbPlugin::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    if (reverbBuffer.getNumSamples() != buffer.getNumSamples())
        reverbBuffer.setSize(2, buffer.getNumSamples(), false, false, true);

    juce::dsp::AudioBlock<float> block(buffer);
    juce::dsp::ProcessContextReplacing<float> context(block);

    reverb.process(context);

    reverbBuffer.makeCopyOf(buffer);

    pitchShifter.setPitchSemitones(*parameters.getRawParameterValue("pitch"));
    //pitchShifter.processBlock(reverbBuffer);

    float feedback = *parameters.getRawParameterValue("feedback");
    buffer.addFrom(0, 0, reverbBuffer, 0, 0, buffer.getNumSamples(), feedback);
    buffer.addFrom(1, 0, reverbBuffer, 1, 0, buffer.getNumSamples(), feedback);

    float mix = *parameters.getRawParameterValue("mix");
    for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
    {
        auto* dry = buffer.getReadPointer(ch);
        auto* wet = reverbBuffer.getReadPointer(ch);
        auto* out = buffer.getWritePointer(ch);

        for (int i = 0; i < buffer.getNumSamples(); ++i)
            out[i] = dry[i] * (1.0f - mix) + wet[i] * mix;
    }
}


bool ShimmerReverbPlugin::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    return layouts.getMainInputChannelSet() == juce::AudioChannelSet::stereo()
        && layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}


void ShimmerReverbPlugin::getStateInformation(juce::MemoryBlock& destData)
{
    auto state = parameters.copyState();
    std::unique_ptr<juce::XmlElement> xml (state.createXml());
    copyXmlToBinary (*xml, destData);
}

void ShimmerReverbPlugin::setStateInformation(const void* data, int sizeInBytes)
{
    std::unique_ptr<juce::XmlElement> xml (getXmlFromBinary (data, sizeInBytes));

    if (xml.get() != nullptr)
        if (xml->hasTagName (parameters.state.getType()))
            parameters.replaceState (juce::ValueTree::fromXml (*xml));
            
}


const juce::String ShimmerReverbPlugin::getName() const {
    return "ShimmerReverb";
}

bool ShimmerReverbPlugin::acceptsMidi() const { return false; }
bool ShimmerReverbPlugin::producesMidi() const { return false; }
bool ShimmerReverbPlugin::isMidiEffect() const { return false; }
double ShimmerReverbPlugin::getTailLengthSeconds() const { return 8.0; }

int ShimmerReverbPlugin::getNumPrograms() { return 1; }
int ShimmerReverbPlugin::getCurrentProgram() { return 0; }
void ShimmerReverbPlugin::setCurrentProgram (int index) { juce::ignoreUnused(index); }
const juce::String ShimmerReverbPlugin::getProgramName (int index) { juce::ignoreUnused(index); return {}; }
void ShimmerReverbPlugin::changeProgramName (int index, const juce::String& newName) { juce::ignoreUnused(index, newName); }


bool ShimmerReverbPlugin::hasEditor() const
{
    return true; 
}

juce::AudioProcessorEditor* ShimmerReverbPlugin::createEditor()
{
    return new ShimmerReverbPluginEditor(*this);
}



juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new ShimmerReverbPlugin();

}