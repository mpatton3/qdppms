# This script reads the raw data from squid measurements and returns the
# fitted magnetizations based on the z-scan profiles.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statistics as st
from scipy.optimize import curve_fit
from scipy.fft import fft, ifft, fftfreq
import os
import re
import pickle

import utensils.QD_SQuID_lib as qs
import utensils.re_values as ur
import utensils.data_reduce as ud


def noise_osc(time, amp, freq, phase, offset):

    return offset + amp*np.cos(freq*time - phase)


def main():

    directory = (r'R:\Lab Member Files\Neil Campbell'
                 r'\Materials\antiperovskite\Mn3GaN\281')
    filename = r'M_v_H_360K_ip110_MGN281.rw.dat'
    os.chdir(directory)

    '''
    magmeas = qs.MagneticMeasurement('field', directory, filename)

    magmeas.find_meta_lines()
    print('Number of sweeps', len(magmeas.metalines))
    mynums = [0, 1, 15, 32]
    mynums = range(1385)
    #cs = []
    for i in mynums:
        magmeas.read_sweep(i)
        #cs.append(magmeas.z_sweeps[-1].cparam)
    #plt.show()

    magmeas.make_dataframe()
    with open('data_object', 'wb') as object_to_write:
        pickle.dump(magmeas, object_to_write)
    '''
    '''
    mynums = range(33, 66)
    cs2 = []
    for i in mynums:
        magmeas.read_sweep(i)
        cs2.append(magmeas.z_sweeps[-1].cparam)
    plt.show()
    '''

    with open('data_object', 'rb') as object_to_write:
        magmeas = pickle.load(object_to_write)

    #print('Meta Lines to Check')
    #print(magmeas.metalines[53])
    #print(magmeas.metalines[55])


    '''
    print(magmeas.measurement_summary.tail())
    magmeas.subtract_diamagnetic(-5.72e-3, -3.2e-3)
    magmeas.measurement_summary['MedianC'] = (
                            magmeas.measurement_summary.groupby('Field')
                            ['Cparam_Sub']
                            .transform('median')
                            )
    magmeas.measurement_summary['MedianCN'] = (
                            magmeas.measurement_summary.groupby('Field')
                            ['Cparam_Sub_NGC']
                            .transform('median')
                            )


    plt.plot(magmeas.measurement_summary.Field,
             magmeas.measurement_summary.Cparam_Sub)
    plt.plot(magmeas.measurement_summary.Field,
             magmeas.measurement_summary.MedianC)
    plt.plot(magmeas.measurement_summary.Field,
             magmeas.measurement_summary.MedianCN+3.)
    plt.show()


    onefield = magmeas.measurement_summary.index[
                        magmeas.measurement_summary['Field']==58356].tolist()

    forhist = [magmeas.z_sweeps[i].cparam for i in onefield]
    forhistn = [magmeas.z_sweeps[i].cparamn*1.84 for i in onefield]
    minind = forhist.index(min(forhist))
    medind = forhist.index(st.median(forhist+[0]))
    print('Min ind is ', minind)
    plt.hist(forhist, bins=18)
    plt.hist(forhistn, bins=18)
    plt.show()

    print(onefield)
    for i in [onefield[minind], onefield[medind]]:# onefield:
        x = magmeas.z_sweeps[i].possweep['Raw Position (mm)']
        y = (magmeas.z_sweeps[i].possweep['Raw Voltage (V)'] 
             -magmeas.z_sweeps[i].aparamn
             -magmeas.z_sweeps[i].bparamn * x)
        y2 = (magmeas.z_sweeps[i].possweep['Fit Signal NGC']
             -magmeas.z_sweeps[i].aparamn
             -magmeas.z_sweeps[i].bparamn * x)

        plt.plot(x, y)
        plt.plot(x, y2)
    plt.show()
    magmeas.z_sweeps[onefield[0]].possweep.to_csv('sample_trace.txt',
                                                  index=False)

    #sns.swarmplot(data=magmeas.measurement_summary,
    #              x='Field', y='Cparam_Sub')
    #plt.show()


    #cs_ser = pd.Series(cs)
    #cs2_ser = pd.Series(cs2)

    #gdinds = ud.reject_outliers(cs_ser, 0.60)
    #gdinds2 = ud.reject_outliers(cs2_ser, 0.60)
    #cs_sern = cs_ser[gdinds]
    #cs2_sern = cs2_ser[gdinds2]

    #bdinds = list(set(range(33)) - set(gdinds))
    #bdinds2 = list(set(range(33, 49)) - set(gdinds2+32))

    #print(gdinds, gdinds2)
    #print(bdinds, bdinds2)

    #print('As Measured Mean ', cs_ser.mean())
    #print('No Outliers Mean ', cs_sern.mean())
    #print('As Measured Mean2 ', cs2_ser.mean())
    #print('No Outliers Mean2 ', cs2_sern.mean())

    #plt.hist(cs_sern, bins=12)
    #plt.hist(cs2_sern, bins=12)
    #plt.show()
    '''
    x =  magmeas.z_sweeps[10].possweep['Time Stamp (sec)']
    y = magmeas.z_sweeps[10].possweep['Signal Subtracted NGC']
    
    num = len(y)
    yfft = fft(y.values)
    xf = fftfreq(num, (x.max()-x.min())/num)[:num//2]
    plt.plot(xf, abs(yfft[:num//2])**2)
    maxind = np.where(abs(yfft[:num//2]) == abs(yfft[:num//2]).max())[0][0]
    noise_ind = np.where(np.logical_and(xf >= 37, xf <41))[0]
    noise_ind2 = np.where(np.logical_and(xf >= 74, xf <82))[0]
    print('Index to blank is ', maxind)
    print('Noise indices are ', noise_ind, noise_ind2)
    endind = np.arange(93, num//2)
    yfft[np.concatenate((noise_ind, noise_ind2, endind))] = 0
    plt.plot(xf, abs(yfft[:num//2])**2)
    plt.show()
    
    yprime = ifft(yfft)
    plt.plot(x, y)
    plt.plot(x, yprime)
    plt.show()



    j=0
    #print(bdinds)
    #print(len(magmeas.z_sweeps))
    for i in [1, 2, 13, 15, 28, 14, 18, 29]: #range(len(bdinds)):
        j += 1
        x = magmeas.z_sweeps[i].possweep['Time Stamp (sec)']
        y = magmeas.z_sweeps[i].possweep['Signal Subtracted NGC']
        x2 = np.linspace(x.min(), x.max(), 436)

        p0 = [0.02, 2*np.pi*35, 2*np.pi*2, 0., 0., 0.]
        popt, pcov = curve_fit(qs.noise_osc, x, y, p0=p0)
        y2 = qs.noise_osc(x2, *p0) 
        y3 = qs.noise_osc(x2, *popt) 
        print('Fit params ', popt)

        #y2 = magmeas.z_sweeps[i].possweep['Fit Signal']

        plt.plot(x, y+j*0.1, color = (j/8., 0.3, 0.4))
        plt.plot(x2, y2+j*0.1 + 0.03, color = (j/8., 0.5, 0.4))
        plt.plot(x2, y3+j*0.1, color = (j/8., 0.6, 0.1))
    plt.show()

    print('everything imported!')


if __name__ == '__main__':
    main()
