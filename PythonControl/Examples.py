# Required to communicate with the QD machine/instrument
from QDInst import QDInstrument

# Required to write .dat files readable in MultiVu
from MultiVuDataFile import MultiVuDataFile

# These are only used for demonstrating examples
from datetime import datetime
import time
import pyvisa
import sys

# Communicating with the QD machine/instrument
# To poll a new set of readings from the QD machine, QDInstrument() must be invoked
QDI = QDInstrument()

# From this reading, the temperature, field, and chamber parameters can be extracted
QDI.temp # Current temperature of machine {float}
QDI.temp_status_code # Temp status code {int}
QDI.temp_status # Human-readable temp status description {str}
QDI.temp_unit # Returns a string of "K" to indicate kelvin units {str}
print(f"The temperature is {QDI.temp} {QDI.temp_unit}; status is {QDI.temp_status}")

QDI.field # Current applied field of machine {float}
QDI.field_status_code # Field status code {int}
QDI.field_status # Human-readable field status description {str}
QDI.field_unit # Returns a string of "Oe" to indicate oersted units {str}
print(f"The field is at {QDI.field} {QDI.field_unit}; status is {QDI.field_status}")

QDI.chamber_status_code # Chamber status code {int}
QDI.chamber_status # Human-readable chamber status description {str}
print(f"The chamber status is {QDI.chamber_status}")

# Temperature, field, and chamber parameters can also be SET to desired values
QDI.set.temp(300, 20, 0)
# Tells MultiVu to set a temperature of 300 K at a rate of 20 K/min using the
# Fast Settle approach.
# Approach Options: Fast Settle (0); No O'Shoot (1).

QDI.set.field(0, 150, 0, 0)
# Tells MultiVu to set a field of 0 Oe at a rate of 150 Oe/sec using the Linear
# approach, leaving the magnet in the Persistent state.
# Approach Options: Linear (0); No O'Shoot (1); Oscillate (2).
# Magnet State Options: Persistent (0); Driven (1).



# Included functionality also enables writing MultiVu-readable .dat files
# Below is an example which logs the temperature, field and chamber status 
# values to a .dat file
# Declares the MV file object
mv = MultiVuDataFile()
# Adds a single column
mv.AddColumn('Temperature (K)')
# Adds multiple columns at once
mv.AddMultipleColumns(['Field (Oe)', 'Chamber Status', 'LS370 Ch 1 Resistance'])
mv.CreateFileAndWriteHeader('TestData.dat', 'Basic Logging Functionality')
# For this example, TestData.dat file is written to the script's root directory.
# The second field gives the TestData.dat the title 'Basic Logging Functionality'.


n = 0
while n < 30:
    # To poll a 'fresh' set of readings, QDInstrument() must be invoked on each iteration
    QDI = QDInstrument()

    # First argument specifies which column to write the data, second is the data itself
    mv.SetValue('Temperature (K)', QDI.temp)
    mv.SetValue('Field (Oe)', QDI.field)
    mv.SetValue('Chamber Status', QDI.chamber_status)

    # Write the data to the file
    mv.WriteData()

    n += 1
    # The above code runs quickly; a 'pause' here paces the results
    time.sleep(1)

sys.exit

# This last example shows a possible integration of 3rd party instruments using PyVISA
# NOTE: This code is demonstrative, and is not intended to be run exactly as shown

# the PyVISA module needs to be installed/imported
rm = pyvisa.ResourceManager()
# View rm.list_resources() in a debug mode to confirm your instrument appears as expected
rm.list_resources()
# Our example instrument is on GPIB0 at the address 18
inst = rm.open_resource('GPIB0::18::INSTR')
# A common serial command asking the instrument to identify itself; confirms communication
print(inst.query("*IDN?"))

# Similar MV file configuration as prior example
mv = MultiVuDataFile()
mv.AddColumn('Temperature (K)')
# Here we can name the column/units for the external instrument's data
mv.AddColumn('External Parameter (AU)')
mv.CreateFileAndWriteHeader('3rdParty.dat', 'External Measurement vs. Temp')

# .dat file writing loop now includes pulling data from external hardware as well as QD instrument
n = 0
while n < 30:
    QDI = QDInstrument()

    mv.SetValue('Temperature (K)', QDI.temp)
    mv.SetValue('External Parameter (AU)', inst.query_ascii_values('TAKEDATA? 1')[0])
    # the above serial command polls the external instrument using the 'TALKEDATA? 1' command.
    # see the instrument's manual for a listing of relevant commands

    mv.WriteData()

    n += 1
    time.sleep(1)