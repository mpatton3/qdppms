# This script reads in IV_sweep.py individual IV files. Multiple
# IVs at the same conditions are averaged. The data
# are manipulated specifically to show nonlinear characteristics
# related to spin-torque effects in the Hall geometry.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.stats import linregress


def average_voltages(dflist):
    vs=[]
    for i in range(len(dflist[0])):
        vsrow = []
        for j in range(len(dflist)):

            vsrow.append(dflist[j].loc[i,'Voltage'])

        vs.append(np.mean(vsrow))

    data_avg = pd.DataFrame({'Current': dflist[0]['Current'], \
                                'Voltage': pd.Series(vs)})

    return data_avg


def voltage_difference(dfpos, dfneg):

    data_diff = dfpos['Voltage'] - dfneg['Voltage']
    print(type(data_diff))
    data_diff = pd.DataFrame({'Current': dfpos['Current'], \
                              'V diff': data_diff})
    params = linregress(data_diff['Current'], data_diff['V diff'])
    print(params.slope)
    data_diff['V diff - lin'] = data_diff['V diff'] -\
                             params.slope*data_diff['Current'] - params.intercept

    return data_diff



def main():


    directory = r'R:\Lab Member Files\Tony Edgeton\Raw Data\Transport\PPMS\B015\IV_SC_field\4.6K\long'

    os.chdir(directory)


    flneg = glob.glob('IV_sweep*_-4000Oe_*.txt')
    flzer = glob.glob('IV_sweep*_0Oe_*.txt')
    flpos = glob.glob('IV_sweep*_4000Oe_*.txt')


    dataneg = []
    for f in flneg:
        dataneg.append(pd.read_csv(f, sep='\t+', engine='python'))

    '''
    datazer = []
    for f in flzer:
        datazer.append(pd.read_csv(f, sep='\t+', engine='python'))
    '''

    datapos = []
    for f in flpos:
        datapos.append(pd.read_csv(f, sep='\t+', engine='python'))


    print(dataneg[0].iloc[0,1], dataneg[0].iloc[1,1])

    dataneg_avg = average_voltages(dataneg)
    #datazer_avg = average_voltages(datazer)
    datapos_avg = average_voltages(datapos)


    data_diff = datapos_avg.loc[:,'Voltage'] - dataneg_avg.loc[:,'Voltage']
    print(type(data_diff))
    data_diff = pd.DataFrame({'Current': dataneg[0].loc[:,'Current'], \
                              'V diff': data_diff})
    params = linregress(data_diff['Current'], data_diff['V diff'])
    print(params.slope)
    data_diff['V diff - lin'] = data_diff['V diff'] -\
                             params.slope*data_diff['Current'] - params.intercept

    data_diff_avg = voltage_difference(datapos_avg, dataneg_avg)
    data_diff = voltage_difference(datapos[1], dataneg[1])



    #dataneg[0].plot('Current', 'Voltage', kind='scatter')
    #dataneg_avg.plot('Current', 'Voltage', kind='scatter')
    #plt.show()
    #data_diff.plot('Current', 'V diff', kind='scatter')
    plt.plot(data_diff['Current'], data_diff['V diff - lin'], 'b')
    plt.plot(data_diff_avg['Current'], data_diff_avg['V diff - lin'], 'g')
    plt.show()
 




if __name__ == "__main__":
    main()






