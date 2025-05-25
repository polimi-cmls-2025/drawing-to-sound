//official one
s.boot;
//VSTPlugin.search;

~greenThresh = 0.5;
~redThresh = 0.5;
~blueThresh = 0.5;

~effectsBus = Bus.audio(s, 2);

~vstdirectory = "";

(
var projectName = "Supercollider";
var projectDir;

if (thisProcess.nowExecutingPath.notNil) {
    var scriptDir = PathName(thisProcess.nowExecutingPath).pathOnly;
    projectDir = scriptDir;

    while { projectDir != "/" and: { projectDir.basename != projectName } } {
        projectDir = PathName(projectDir).parentPath;
    };

    if (projectDir.basename == projectName) {
        var vstDir = projectDir +/+ "vst";
		~vstdirectory = vstDir +/+ "ShimmerEffectPlugin.vst3";
        if (File.exists(vstDir)) {

            VSTPlugin.search(s, [vstDir]);
            ("Scanning VSTs in: " + vstDir).postln;
        } {
            ("VST directory not found in project: " + vstDir).warn;
        };
    } {
        ("Project directory '" ++ projectName ++ "' not found.").warn;
    };
} {
    "Could not determine script location.".warn;
};
)


// effects routing
SynthDef(\juce_effects, { |in, out|
    var sound = In.ar(in, 2);
    ReplaceOut.ar(out, VSTPlugin.ar(sound, 2, id: \juce_effects));
}).add;

SynthDef(\shapeSound, { |freq=440, amp=0.1, pan=0, waveType=0, sustain=1,
    doFM=0, doAM=0, greenVal=0, blueVal=0, out=0|

    var envSoft, envSharp, env, sig, mod, ampMod;
    var attackTime, releaseTime, sustainTime;
    var greenFactor, modFreq, modDepth, amFreq;

    greenFactor = greenVal.clip(~greenThresh, 1).linlin(~greenThresh, 1, 0.2, 0.5);
    attackTime = sustain * greenFactor;
    releaseTime = sustain * greenFactor;
    sustainTime = (sustain - attackTime - releaseTime).max(0.01);

    envSoft = Env.linen(attackTime, sustainTime, releaseTime, curve: 1).ar(doneAction: 2);
    envSharp = Env.perc(0.01, sustain, 1, curve: -4).ar(doneAction: 2);

    env = Select.kr((greenVal > ~greenThresh).asInteger, [envSharp, envSoft]);

    // FM Modulation (Red)
    modFreq = Select.kr((waveType == 3).asInteger, [freq * 3, freq * 0.05]);
    modDepth = Select.kr((waveType == 3).asInteger, [freq * 3, freq * 0.005]);
    mod = SinOsc.ar(modFreq, 0, modDepth) * doFM;

    // Oscillator
    sig = Select.ar(waveType, [
        SinOsc.ar(freq + mod),
        LFPulse.ar(freq + mod),
        LFTri.ar(freq + mod),
        Saw.ar(freq + mod)
    ]);

    // AM Modulation (Blue)
    amFreq = blueVal.clip(~blueThresh, 1).linlin(~blueThresh, 1, 1, 6);
    ampMod = (SinOsc.kr(amFreq).range(0.3, 1) * doAM) + ((1 - doAM) * 1);

    // Final output
    sig = sig * env * amp * ampMod;
    sig = Pan2.ar(sig, pan);
    Out.ar(out, sig);
}).add;

~juce_effects = VSTPluginController(Synth(\juce_effects, [\in, ~effectsBus, \out, 0]), id: \juce_effects);
~juce_effects.open(~vstdirectory, editor: true, verbose: true);
~juce_effects.editor;

//map a parameter
~juce_effects.map(1, Ndef(\mixControl).bus);
~juce_effects.map(0, Ndef(\noise).bus);

//LFOs

Ndef(\mixControl, {LFTri.kr(0.05,-1).range(0.4,1.0)});
Ndef(\rbControl, {LFNoise0.kr(1.0).range(0.0,1.0)});
Ndef(\rf, {LFTri.kr(0.1).range(80,5000)});
Ndef(\noise, {LFNoise1.kr(0.2).range(0.1,0.5)});


//OSC to processing
~processingAddr = NetAddr("127.0.0.1", 12000);

// Main OSC receiver for shapes
OSCdef(\shapeReceiver, { |msg|
	var category, x, y, width, height, r, g, b, pressure, total_length, num_points, contour_points;
	var freq, amp, pan, waveType, duration;
	var doFM, doAM, amFreq;


	category = msg[1].asString.toLower;
	x = msg[2].asFloat;
	y = msg[3].asFloat;
	width = msg[4].asFloat;
	height = msg[5].asFloat;
	r = msg[6].asFloat;
	g = msg[7].asFloat;
	b = msg[8].asFloat;
	pressure = msg[9].asFloat;
	total_length = msg[10].asFloat;

	postln("----------------------");
	postf("Shape: %\n", category);
	postf("Position: (%, %)\n", x, y);
	postf("Size: % x %\n", width, height);
	postf("Color: (%, %, %)\n", r, g, b);
	postf("Pressure: %\n", pressure);
	postf("Total Length: %\n", total_length);

	// Mappings
	freq = y.clip(0, 1).linexp(0, 1, 1760, 100);
	amp = pressure.clip(0, 1) * 0.2;
	pan = x.clip(0, 1).linlin(0, 1, -1, 1);
	duration = total_length * 0.02;

	doFM = (r > ~redThresh).asInteger;
	doAM = (b > ~blueThresh).asInteger;

	amFreq = b.clip(~blueThresh, 1).linlin(~blueThresh, 1, 3, 20);

	// Wave type detection
	if (category.contains("triangle")) {
		waveType = 2;
	} {
		if (category.contains("rect") or: { category.contains("square") }) {
			waveType = 1;
		} {
			if (category.contains("line")) {
				waveType = 3;
			} {
				waveType = 0;
			}
		}
	};

	postf("Sound params - Freq: %, Amp: %, Pan: %, Wave: %, Duration: %, FM: %, AM: %, GreenVal: %, AM Freq: %\n",
		freq, amp, pan, waveType, duration, doFM, doAM, g, amFreq);

	Synth(\shapeSound, [
		\freq, freq,
		\amp, amp,
		\pan, pan,
		\waveType, waveType,
		\sustain, duration,
		\doFM, doFM,
		\doAM, doAM,
		\greenVal, g,
		\blueVal, b,
		\out, ~effectsBus
	]);

	num_points = msg[11].asInteger;
    contour_points = msg.copyRange(12, 12 + (num_points * 2) - 1).asFloat;
	~processingAddr.sendMsg("/shapeContour",
        category,
        x, y, width, height,
        r, g, b,
        pressure,
        total_length,
        num_points,
        *contour_points
    );

}, '/shape');

OSCdef(\clearVisuals, { |msg|
    if(msg[1] == 1) {
        "Clearing visuals".postln;
        ~processingAddr.sendMsg("/clearVisuals");
    }
}, '/clearVisuals');
