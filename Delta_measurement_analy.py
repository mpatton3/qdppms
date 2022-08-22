# This script analyses complete Delta meaurement results to determine
# the actualy resistance with good precision.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.optimize import curve_fit

import utensils.re_values as ur
import utensils.data_reduce as dr
 

def main():

    directory = (r'R:\Lab Member Files\Tony Edgeton\Raw Data\Transport'
                 r'\PPMS\B028\220816\300K_3.5mA_0')

    os.chdir(directory)

    #fln = glob.glob('IV_sweep_*Oe_12000.00uA*neg*.txt')
    #flp = glob.glob('IV_sweep_*Oe_12000.00uA*pos*.txt')
    #print(fln)

    glbstrs = ['IV_sweep_*Oe_3500.00uA*neg*.txt', 
               'IV_sweep_*Oe_3500.00uA*pos*.txt']
               
    measurement = dr.MeasDirectory(glbstrs)
    measurement.read_data(95, 75)

    print(measurement.lists_pos.fields, measurement.lists_pos.ordinals)

    measurement.compute_voltages()
    print(measurement.values.head())

    measurement.write_data('Asym_Delta_3.5mA_300K_summary_0.txt')

    #plt.plot(val_lin_pos, 'bo')
    #plt.plot(val_lin_neg, 'ro')
    #plt.show()
    measurement.values.plot('Field', 'V diff')
    measurement.values.plot('Field', 'V sum')
    plt.show()



if __name__ == "__main__":
    main()
