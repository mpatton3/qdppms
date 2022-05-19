# This script plots Delta measurements for checking analysis and
# if the data are good.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.optimize import curve_fit
from scipy.stats import linregress
import utensils.re_values as ur


def reject_outliers(data, iq_range):
    # Higher iq_range will exclude fewer points.
    # iq_range = 0.5 will give 25, 50, 75%.
    
    pcnt = ( 1. - iq_range ) / 2.

    qlow, median, qhigh = data.quantile([pcnt, 0.5, 1-pcnt])
    iqr = qhigh - qlow 

    return data[ (data - median).abs() <= 1.0*iqr ].index


def exp_decay(time, A, tau, x0, y0):
    
    return A*np.exp(-(time-x0)/tau)+y0


def fit_exp(df):

    voltage = np.mean(df['Voltage'][-30:])
    p0=[np.sign(voltage)*8.7e-5, 18., 8., voltage]

    #print(p0)

    lower = [-np.inf, 0., 3., -np.inf]
    upper = [np.inf, 40., 20., np.inf]

    params, cov = curve_fit(exp_decay, df['Time'][-350:], \
                        df['Voltage'][-350:], p0=p0, \
                        bounds = [lower, upper]) 

    return params
 
def fit_lin(df, num_fit):

    #print(type(df['Voltage'][-num_fit:]))
    ind_good = reject_outliers(df['Voltage'][-200:], 0.85)
    ind_end = np.arange(len(df['Voltage']))[num_fit:]
    #ind_end = np.arange(len(df['Voltage']))[-2*num_fit:-num_fit]
    ind_tofit = np.intersect1d(ind_good, ind_end)
    #print(ind_tofit)
    result = linregress(df['Time'][ind_tofit], df['Voltage'][ind_tofit]) 

    #plt.plot(df['Time'][-200:], df['Voltage'][-200:])
    #plt.plot(df['Time'][ind_good], df['Voltage'][ind_good]+12.e-6)


    d_linsub = df['Voltage'][ind_good] - df['Time'][ind_good]*result[0]
    ind_good2 = reject_outliers( d_linsub, 0.4 )
    #plt.plot(df['Time'][ind_good2], df['Voltage'][ind_good2]+24.e-6)

    #plt.show()
    ind_tofit = np.intersect1d(ind_good2, ind_end)
    result = linregress(df['Time'][ind_tofit], df['Voltage'][ind_tofit]) 


    return [result[0], result[1]]


def get_data(fl, num_fit_lin):

    meas = []
    data = []
    #val_exp = []
    val_lin = []

    for f in fl:
        
        meas_num = ur.get_ordinal(f)
        #print(meas_num)
        meas.append(meas_num)
        new_dat = pd.read_csv(f, sep='\t+', engine='python')

        
        #params_exp = fit_exp(new_dat)
        #print(params_exp)
        #val_exp.append(params_exp[-1])

        params_lin = fit_lin(new_dat, num_fit_lin)
        #print(params_lin)
        val_lin.append(params_lin[0]*new_dat['Time'].iloc[-int(num_fit_lin/2)] \
                       + params_lin[1])
        #val_lin.append(params_lin[0]*new_dat['Time'].iloc[-1] + params_lin[1])

        data.append(new_dat)

        #'''
        if meas_num < 4:
            plt.plot(new_dat['Time'][-200:], new_dat['Voltage'][-200:])
            plt.plot(new_dat['Time'][-num_fit_lin:], \
                     params_lin[0]*new_dat['Time'][-num_fit_lin:] + params_lin[1])
            #plt.plot(new_dat['Time'][-2*num_fit_lin:-num_fit_lin], \
            #         params_lin[0]*new_dat['Time'][-2*num_fit_lin:-num_fit_lin] + \
            #         params_lin[1])
        #'''

    #print('Exponential Decay ', val_exp)
    print('Linear last point  ', val_lin)
    plt.show()
    meas = np.asarray(meas)
    #val_exp = np.asarray(val_exp)
    val_lin = np.asarray(val_lin)
    ordered = np.argsort(meas)
    meas = meas[ordered]
    #val_exp = val_exp[ordered]
    val_lin = val_lin[ordered]
 
    return val_lin


def main():

    directory = r'R:\Lab Member Files\Tony Edgeton\Raw Data\Transport\PPMS\B015\30K_Delta\from15kOe\sweep_2'

    os.chdir(directory)


    #fln = glob.glob('IV_sweep*_-300Oe_*neg*.txt')
    #flp = glob.glob('IV_sweep*_-300Oe_*pos*.txt')

    fln = glob.glob('IV_sweep*_700Oe_*neg*.txt')
    flp = glob.glob('IV_sweep*_700Oe_*pos*.txt')

    num_fit_lin = 100


    fields_neg = []
    for f in fln:
        fields_neg.append(ur.get_field(f))

    fields_neg = np.asarray(fields_neg)
    neg_inds = np.argsort(fields_neg)
    #print(fields_neg[neg_inds])

    fields_pos = []
    for f in flp:
        fields_pos.append(ur.get_field(f))

    fields_pos = np.asarray(fields_pos)
    pos_inds = np.argsort(fields_pos)
    #print(fields_pos[pos_inds])

    num_files = len(fields_pos)
    repeat = 8
    print('number of fields ', num_files/repeat)
    
    diff_0 = []
    diff_1 = []
    for i in range(int(num_files/repeat)):
        flneg = [fln[j] for j in neg_inds[repeat*i:repeat*(i+1)]]
        flpos = [flp[j] for j in pos_inds[repeat*i:repeat*(i+1)]]

        if i == 25:
            print(flneg)

        val_lin_neg = get_data(flneg, num_fit_lin)
        val_lin_pos = get_data(flpos, num_fit_lin)

        neg_0 = np.mean(val_lin_neg[:4])
        neg_1 = np.mean(val_lin_neg[4:])
        pos_0 = np.mean(val_lin_pos[:4])
        pos_1 = np.mean(val_lin_pos[4:])

        diff_0.append( pos_0 + neg_0 )
        diff_1.append( pos_1 + neg_1 )

        print(pos_0, neg_0)
        print('differences', diff_0, diff_1)


        #'''
        #plt.boxplot([val_lin_pos[:4]*-1, val_lin_pos[4:]*-1, \
        #            val_lin_neg[:4], val_lin_neg[4:]], \
        #            showmeans=True)

        plt.boxplot([val_lin_pos[:4]*-1, \
                    val_lin_neg[:4]], \
                    showmeans=True)

        plt.plot([1.1,1.1,1.1,1.1], val_lin_pos[:4]*-1, 'ko')
        #plt.plot([2,2,2,2], val_lin_pos[4:]*-1, 'ko')
        plt.plot([2.1,2.1,2.1,2.1], val_lin_neg[:4], 'ko')
        #plt.plot([4,4,4,4], val_lin_neg[4:], 'ko')

        plt.show()
        #'''
    fld_ind = (np.arange(num_files/repeat)*repeat).astype(int)

    to_write = pd.DataFrame({'Fields': pd.Series(fields_pos[pos_inds[fld_ind]]), \
                             'V diff 0': pd.Series(diff_0), \
                             'V diff 1': pd.Series(diff_1)}) 

    #to_write.to_csv('Delta_Summary_linear.txt', sep='\t', index=False)

    #plt.plot(diff_0)
    #plt.plot(diff_1)
    #plt.show()


    '''
    val_lin_neg = get_data(fln, num_fit_lin)
    val_lin_pos = get_data(flp, num_fit_lin)

    neg_0 = np.mean(val_lin_neg[:4])
    neg_1 = np.mean(val_lin_neg[4:])
    pos_0 = np.mean(val_lin_pos[:4])
    pos_1 = np.mean(val_lin_pos[4:])

    diff_0 = pos_0 + neg_0
    diff_1 = pos_1 + neg_1
    print('differences', diff_0, diff_1)


    plt.boxplot([val_lin_pos[:4]*-1, val_lin_pos[4:]*-1, \
                val_lin_neg[:4], val_lin_neg[4:]], \
                showmeans=True)

    plt.plot([1,1,1,1], val_lin_pos[:4]*-1, 'ko')
    plt.plot([2,2,2,2], val_lin_pos[4:]*-1, 'ko')
    plt.plot([3,3,3,3], val_lin_neg[:4], 'ko')
    plt.plot([4,4,4,4], val_lin_neg[4:], 'ko')

    #plt.violinplot([val_exp[:4], val_exp[4:], val_lin[:4], val_lin[4:]], \
    #            showmeans=True)
    plt.show()
    #print(fln)

    '''



if __name__ == "__main__":
    main()
