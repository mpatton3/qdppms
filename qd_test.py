# This tests the QD communications with MultiVu.


import numpy as np
import pandas as pd
import os
from PythonControl.QDInst import QDInstrument
from PythonControl.MultiVuDataFile import MultiVuDataFile
from datetime import datetime
import datetime
import pyvisa
import sys





QDI = QDInstrument()

print(f"The temperature is {QDI.temp} {QDI.temp_units}; status is {QDI.temp_status}")
