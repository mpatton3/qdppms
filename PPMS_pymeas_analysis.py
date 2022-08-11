# This script reads in raw data files from PPMS measurements 
# in which the data file was written with a Pymeasure Results
# class.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
#from pathlib import Path

import utensils.vdp_equations as ve
import utensils.QD_PPMS_lib as qp
from scipy.stats import linregress



def main():

    #directory = r'R:\Lab Member Files\Neil Campbell\Materials\Bismuthate\B023'
    directory = (r"R:\Lab Member Files\Pratap Pal\PPMS"
                 r"\Jieun\08-11-22-KTO-jk246")
    os.chdir(directory)
    sname = 'jk246'

    #meas = 'temp' # hall or temp
    thick = 1. #32.03e-7  # thickness in cm
    chnl = 2 # first (1) or second (2) vdp set, takes integer
    anomalous = False # Do analysis for Anomalous Hall effect too?

    fl = glob.glob('rho_2022*.csv')
    print(fl)
    #name = r'rho_v_T_300K_2T_Hall_0.raw'

    # Start Reading in Data
    qp.read_metadata(fl[0])
    
    #if meas == 'hall':
    temps = []
    rv1s = []
    rv2s = []
    rh1s = []
    rh2s = []
    rsqs = []
    rhos = []
    rhox = []
    rhoy = []
    rhs = []
    cds = []
    mobs = []
    kfls = []
    lists = [rv1s, rv2s, rh1s, rh2s, rsqs, rhos, rhox, rhoy, \
             rhs, cds, mobs, kfls, temps]

    if anomalous == True:

        anom_offset = []
        rh_sat = []
        rh_zero = []
        rhall_sat = []
        lists.extend([anom_offset, rh_sat, rh_zero, rhall_sat])


    for i in range(len(fl)):

        print('File', fl[i])

        flist = list(fl[i])
        del flist[-4:]
        toappend = '_' + str(chnl) + '_rsq.txt'
        flist.append(toappend)
        flnew = ''.join(flist)
        print(flnew)
 
        # Compute Resistance data
        meas = qp.VdP_Measurement(fl[i], thick, chnl)
        meas.compute_resistances()
        if meas.metadata['Measurement Type'] == 'Hall':
            meas.compute_params()
            print('carriers, mobility ', meas.ncd, meas.mu)
            if anomalous == True:
                lists = meas.compute_anomalous(lists, 80000)
            lists = meas.list_append(lists)
        meas.write(flnew)

    # Order Hall params for writing the summary file
    ordarg = np.argsort([-1*x for x in lists[10]])

    sumdf = pd.DataFrame({'Temperature': pd.Series(lists[10])[ordarg], \
                          'R vdP 1': pd.Series(lists[0])[ordarg], \
                          'R vdP 2': pd.Series(lists[1])[ordarg], \
                          'R Hall 1': pd.Series(lists[2])[ordarg], \
                          'R Hall 2': pd.Series(lists[3])[ordarg], \
                          'Rsq': pd.Series(lists[4])[ordarg], \
                          '\g(r)': pd.Series(lists[5])[ordarg], \
                          'R\-(H)': pd.Series(lists[6])[ordarg], \
                          'n\-(3D)': pd.Series(lists[7])[ordarg], \
                          '\g(m)': pd.Series(lists[8])[ordarg], \
                          'Kfl': pd.Series(lists[9])[ordarg] })

    sumdf = sumdf[['Temperature', 'R vdP 1', 'R vdP 2', 'R Hall 1', \
                   'R Hall 2', 'Rsq', '\g(r)', 'R\-(H)', 'n\-(3D)',\
                   '\g(m)', 'Kfl']]

    flnew = 'Hall_Summary_' + sname + '_' + str(chnl) + '.txt'

    if anomalous == True:
        sumdf['\g(Dr)\-(Hall)'] = pd.Series(lists[11])[ordarg]
        sumdf['R\-(H) sat'] = pd.Series(lists[12])[ordarg]
        sumdf['R\-(H) zero'] = pd.Series(lists[13])[ordarg]
        sumdf['R\-(Hall) sat'] = pd.Series(lists[14])[ordarg]
       
        flnew = 'Hall_Summary_' + sname + '_anom_' + str(chnl) + '.txt'


    sumdf.to_csv(flnew, sep='\t', index=False)

    print('Done')


if __name__ =='__main__':
    main()
