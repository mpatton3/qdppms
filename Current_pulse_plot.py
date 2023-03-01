# read in data from Current_pulse.py and quickly plot it.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob



#directory1 = (r'C:\Users\maglab\Documents\Python Scripts\data'
#               r'\MNN\76_77\Current Pulse\10um device\10000Oe 0mA to 90mA Meas 100uA')
directory1 = (r'C:\Users\maglab\Documents\Python Scripts\data'
               r'\MNN\76_77\Current Pulse\10um device 2\try1')
#directory1 = (r'C:\Users\maglab\Documents\Python Scripts\data'
#               r'\MNN\76_77\Current Pulse\10um device\10000Oe -50mA to 50mA')
os.chdir(directory1)
files = glob.glob("*.csv")

x = []
y = []

for fname in files:

    data = pd.read_csv(fname, skiprows=18)
    #print(data.head())

    sgn = np.sign(data.loc[0, "Pulse Current"])

    x.append(data.loc[0, "Pulse Current"])
    y.append(data.loc[0, "Measurement Voltage"])

plt.plot(x, y, 'bo')
plt.xlabel("Pulse Current (A)")
plt.ylabel("Meas Volts (V)")
plt.ylim(-2.55E-5,1.55E-5)
plt.tight_layout()
plt.show()
