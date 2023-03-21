This directory contains scripts for controlling experiments on a Quantum Design
Dynacool PPMS with external custom electronics. Scripts here were designed to
be run on a different computer than the one with MultiVu that directly controls
the PPMS. The computer this script runs on must have a direct ethernet
connection to the MultiVu PPMS computer, and this computer must have direct
communication, ie GPIB, with the external custom electronics.

=================== Setup Communication with MultiVu CPU ======================




======================= Get Started with Measurements =========================

Van der Pauw Measurements:

Van der Pauw meausurements are a great way to measure the sheet conduction of
this films. This is often done in a 4-corners configuration or a patterned
configuration such as a 'clover leaf.' This set up is configured to make
accurate measurement of the sheet resistance (resistivity), carrier density,
and mobility easy, quick, efficient, and reproducible. The setup also easily
handles other measurements such as basic superconductor characterization
and anomalous Hall measurements. Although IV_sweep.py should be used to get
the most accurate results for superconductors.

To get started, use the program Arbitrary_sweepy.py. This program is set up
to run temperature and magnetic field sweeps while continuously measureing
4 van der Pauw configurations (2 vdP, 2 Hall).

To start the program with no command prompt currently open.
Open a command prompt in administrator mode (click the windows button in the 
lower left, find command prompt, right click, and select run as 
administrator). Then navigate to the directory hosting the file, likely 
C:\Users\maglab\Documents\qdppms. To move up a directory type "cd maglab"
to go from Users to maglab, and so on. To move back type "cd..".

Start Program
Once the display line shows the correct directory, type 
"python Arbitrary_sweep.py" and press <enter>. This will compile and run the
program. After 10seconds or so a window will pop up on the screen that read
Arbitrary Sweep in the top left. 
For your measurement adjust the properties in the upper left corner of the
window, and be sure to scroll down. For temperature sweeps type "Temp" into
the Measurement Type input, and for field sweeps type "Hall" ino the input.

Temperature sweeps will set the temperature to the selected Temperature Set
Point, and continuously take meaurements until that set point is reached.
No magnetic field control occurs. 

Hall sweeps will ramp the magnetic field to +Maximum Field, -Maximum Field,
then back to 0, while measuring continuously. No temperature control occurs.

Set the following parameters for temperature sweeps: 
Max Current, Temperature Set Point, Temperature Ramp Rate, and Directory.

Set the followign parameters for field sweeps:
Max Current, Maximum field, Magnetic Field Ramp Rate (check box below to do
an extra half sweep if you expect a hysteresis).

Directory is selected by clicking to your desired directory. 

To start a measurement press the Queue button below the selected parameters.
The measurement will then start automatically and run until completion. 


Run Multiple Measurement in a Sequence.
Running individual measurements is time consuming, so this program has the 
feature that an experimenter can create a sequence of measurements to run
and queue them. Then all the measurements run in the prescribed order and
the experimenter can devote time to other tasks, such as reading or sleeping.

This is done most easily with by creating a sequence file and loading it. An
example file can be found in the same directory Arbitrary_sweep.py called
KTO_sequencer.txt.

The format of the sequencer file is simple, but must be executed perfectly.
Each line sets a parameter for a measurement. To set multiple parameters for
one measurement, each new line must contain one more "-" at the beginning than
the previous line. Each line contains a "-" followed by a space followed by 
the parameter name (same as in the gui) in double quotes followed by a space
followed by the desired value in double quotes and square brackets.

An example is below which does a Hall measurement then sets the temperature to
150 K.

- "Measurement Type", "['Hall']"
-- "Maximum Field", "[10000]"
--- "Magnetic Field Ramp Rate", "[60]"
- "Measurement Type", "['Temp']"
-- "Temperature Set Point", "[150]"
--- "Temperature Ramp Rate", "[15]"

Note that any parameters that are not set in the sequencer file will be the 
same as what is set in the gui when the measurements are queued.

To load a sequence file click the Load sequence button, and the details of the
sequence will appear in the box above. To start the measurement sequence click
Queue sequence. As a reminder, all parameters not set by the sequence file
will be match what has been selected in the input boxes above.
