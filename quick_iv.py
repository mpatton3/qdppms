# This script runs a quick IV curve to test the sweep methods in
# current_voltage.py.


import numpy as np
import pandas as pd
import os
from time import sleep
import ngcmeas.current_voltage as cv
from pymeasure.adapters import VISAAdapter



def main():


    adapter = VISAAdapter("GPIB0::12")
    ke6221 = cv.myKeithley6221(adapter)

    ke6221.current_sweep(5.e-6, 11, 'linear')
    #ke6221.current_sweep_trig()
    for i in range(18):
        ke6221.current_sweep_inloop()
    sleep(1.0)
    #ke6221.current_sweep_off()



if __name__ == "__main__":
    main()
