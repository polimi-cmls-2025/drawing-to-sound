Drawing Sound Project
====================

A real-time audio-visual application that converts drawings into sound using Python, SuperCollider and JUCE. 

The system is an interactive educational tool for children that fosters imagination and introduces the basic principles of sound. It provides a foundational understanding of waveforms, panning, pitch, and other core audio concepts. 

Users draw on a digital canvas using different colors and varying pressure, and hear audio output shaped by these and other parameters. 


Prerequisites
------------
- Python 3.x
- SuperCollider 3.x
    - VSTPlugin — SuperCollider extension
- Required Python packages:
  - PyQt5
  - python-osc
  - numpy
  - opencv-python
- Required Processing libraries:
  - OSCP5

Installation
-----------
1. Install Python dependencies:
   pip install PyQt5 python-osc numpy opencv-python

2. Install SuperCollider VSTPlugin extention from [supercollider.github.io](https://git.iem.at/pd/vstplugin/-/releases)

3. Install the oscP5 library in Processing:
   - Go to Sketch -> Import Library -> Add Library -> search "oscP5" and install it

Running the Application
----------------------
1. Clone the project from GitHub:
   - Locate the project file, the usual directory is C:\Users\<USERNAME>\PycharmProjects\CMLS_project25

2. Start SuperCollider first:
   - Open the SuperCollider file and run try.scd
   - Make sure to boot/reboot server each time
   - Run the SuperCollider code block by block (select and press Ctrl+Enter or Cmd+Enter)

3. Then run the Python application:
   - Run the main.py file
   - Draw with a tablet (or your mouse) to hear the resulting sounds

4. Finally, run the Processing visualization:
   - Run the processingFinal.pde file

Controls
--------
- Mouse/Tablet: Draw on the canvas
- Pressure: Controls line thickness and sound amplitude
- Position: Controls sound frequency and panning
- C: Open color picker
- H: Show help menu
- Z: Clear canvas

Shape Detection
--------------
The application detects different shapes and triggers corresponding sounds:
- Lines → Sawtooth wave
- Triangles → Triangle wave
- Rectangles → Square wave
- Other shapes → Sine wave

Visualisation Features
-------------------------------
The Processing component provides:
- Real-time display of drawn shapes
- Dual oscilloscope monitoring:
  - Individual shape waveforms (sine, square, triangle, sawtooth)
  - Combined output waveform
- Frequency analysis displays:
  - Per-shape frequency response
  - Overall frequency response
- Visual feedback for:
  - Pan position 
  - Frequency range 
- Automatic cleanup of expired shapes

Troubleshooting
--------------
If you encounter connection errors:
1. Make sure SuperCollider is running before starting Python
2. Check that port 57120 is available
3. If needed, restart applications

Project Structure
----------------
- main.py: Python application with GUI and drawing functionality
- try.scd: SuperCollider code for sound synthesis
- ShimmerEffectPlugin.vst3: VST plugin for audio effects
- processingFinal.pde: processing code for visualisation
