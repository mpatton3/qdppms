# This script does quick Lockin measurements. It assumes the current soucre
# and switch matrix are already set and will not change during the measurement.


import numpy as np
import pandas as pd
import os
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter
from time import sleep
from pymeasure.instruments.keithley import Keithley6221
from pymeasure.instruments.srs import SR830
import ngcmeas.current_voltage as cv
import MultiVu_talk_ngc as mv


def main():

    host = "128.104.184.130"
    port = 5000

    adapter2 = VISAAdapter("GPIB::8")
    LockIn = cv.mySR830(adapter2)


    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B016'
    os.chdir(directory)
    data_filename = 'volt_2w_Hall_v_B_1mA_1.2T_increasing_300K_phi90deg_B016_0.txt'


    num = 3
    volts = []
    voltx = []
    volty = []
    phis = []
    bflds = []
    done = False
    print("About to measure")
    #for i in range(num):
    while not done:

        meas = LockIn.read_one()
        
        volts.append(meas[2]*np.sqrt(2))
        voltx.append(meas[0])
        volty.append(meas[1])
        phis.append(meas[3])
        bfield = mv.query_field(host, port)
        bflds.append(bfield[0])
        sleep(0.05)
        done = bfield[1] == r'"Holding (Driven)"'

    #print("Volts: ", volts)
    #print("Phis: ", phis)
    #print("Bs: ", bflds)

    data = pd.DataFrame({"\g(m)\-(0)H": pd.Series(bflds), \
                      "phi": pd.Series(phis),\
                      "Volts": pd.Series(volts),\
                      "Voltx": pd.Series(voltx),\
                      "Volty": pd.Series(volty)})

    data.to_csv(data_filename, sep = "\t", index=False)
                    


if __name__ == "__main__":
    main()
