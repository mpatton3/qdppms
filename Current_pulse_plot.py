# read in data from Current_pulse.py and quickly plot it.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob



directory = (r'C:\Users\maglab\Documents\Python Scripts\data'
               r'\MNN\76_77\Current Pulse\try_10')

os.chdir(directory)

files = glob.glob("*.csv")

x = []
y = []

for fname in files:

    data = pd.read_csv(fname, skiprows=18)
    print(data.head())

    sgn = np.sign(data.loc[0, "Pulse Current"])

    x.append(data.loc[0, "Pulse Current"])
    y.append(sgn*data.loc[0, "Measurement Voltage"])

plt.plot(x, y, 'bo-')
plt.xlabel("Pulse Current (A)")
plt.ylabel("Meas Volts (V)")
plt.tight_layout()
plt.show()
