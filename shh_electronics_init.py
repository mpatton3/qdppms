# This script runs to initialize the electronics for SHH measurement.
# This script has two sections. The first turns on the KE6221 current
# source at the prescribed current amplitude and frequency. The second
# sets the lockin parameters to be ideal for signal measurement.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from time import sleep, time
from pymeasure.adapters import VISAAdapter
import ngcmeas.current_voltage as cv



def smth():

    print('Hi')


def find_sensitivity(init_guess):

    

    return senst


def main():


    # Connect to KE6221 and SRS830
    adapter = VISAAdapter("GPIB::12")
    KE6221 = cv.myKeithley6221(adapter)

    adapter2 = VISAAdapter("GPIB::8")
    LockIn = cv.mySR830(adapter2)

    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B015\test'
    os.chdir(directory)

    # Current Source parameters
    amplitude = 1.e-3 # Amps
    frequency = 587.37 # Hz
    offset = 0.0 # Amps

    turnon = True
    turnoff = False

    xs = []
    ys = []
    ovlds = []
    LockIn.set_sensitivity("1mV/nA")
    LockIn.set_time_constant("3ms")
    LockIn.set_harmonic(1)
    print(LockIn.query_ovld())
    KE6221.current_wave_set(amplitude, frequency, offset, turnon, turnoff)
    #'''
    for i in range(100):
        resp = LockIn.query_ovld()
        LockIn.read_one()
        xs.append(LockIn.X)
        ys.append(LockIn.Y)
        ovlds.append(resp)
        #print(int(resp[1]))
        sleep(0.05)


    LockIn.set_time_constant("1ms")
    sleep(1.0)
    
    for i in range(100):
        resp = LockIn.query_ovld()
        LockIn.read_one()
        xs.append(LockIn.X)
        ys.append(LockIn.Y)
        ovlds.append(resp)
        #print(int(resp[1]))
        sleep(0.05)


   #'''
    #LockIn.find_sensitivity("1mV/nA")

    #KE6221.current_wave_set(amplitude, frequency, offset, False, True)
    sleep(2.0)
    print(LockIn.query_ovld())
    print(LockIn.query_ovld())
    
    plt.plot(xs)
    plt.show()
    data = pd.DataFrame({'xs': pd.Series(xs), \
                         'ys': pd.Series(ys), \
                         'ovlds': pd.Series(ovlds)})

    data.to_csv('test2.txt', sep = "\t", index=False)



if __name__ == '__main__':
    main()


