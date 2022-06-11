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


class OneDelta:


    def __init__(self, filename):

        self.data = pd.read_csv(filename, sep='\t+', engine='python')
        self.ordinal = ur.get_ordinal(filename)
        self.field = ur.get_field(filename)
        self.temp = ur.get_temp(filename)
        self.current = ur.get_current(filename, units='uA')

    def fit_lin(self, num_consider, num_fit, second_reject=True):

        #print(type(df['Voltage'][-num_fit:]))
        self.ind_norej = reject_outliers(self.data['Voltage'][-num_consider:], 0.85)
        ind_end = np.arange(len(self.data['Voltage']))[num_fit:]
        #ind_end = np.arange(len(df['Voltage']))[-2*num_fit:-num_fit]
        ind_tofit = np.intersect1d(self.ind_norej, ind_end)
        #print(ind_tofit)
        self.result = linregress(self.data['Time'][ind_tofit],
                            self.data['Voltage'][ind_tofit]) 

        #plt.plot(df['Time'][-200:], df['Voltage'][-200:])
        #plt.plot(df['Time'][ind_good], df['Voltage'][ind_good]+12.e-6)


        self.data_linsub = (self.data['Voltage'][ind_good] 
                    - self.data['Time'][ind_good]*self.result[0])
        self.ind_norej2 = reject_outliers(self.data_linsub, 0.4)
        #plt.plot(df['Time'][ind_good2], df['Voltage'][ind_good2]+24.e-6)

        #plt.show()
        self.ind_tofit = np.intersect1d(self.ind_norej2, ind_end)
        self.result2 = linregress(self.data['Time'][self.ind_tofit],
                                  self.data['Voltage'][self.ind_tofit]) 
        
        self.val_lin = (self.result2[0]
                        *self.data['Time'].iloc[-int(num_fit_lin/2)]
                        + self.result2[1])

    #def 



def reject_outliers(data, iq_range):
    # Higher iq_range will exclude fewer points.
    # iq_range = 0.5 will give 25, 50, 75%.
    
    pcnt = ( 1. - iq_range ) / 2.

    qlow, median, qhigh = data.quantile([pcnt, 0.5, 1-pcnt])
    iqr = qhigh - qlow 

    return data[(data - median).abs() <= 1.0*iqr].index

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

    num_plot = num_fit_lin+50
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

        '''
        if meas_num < 4:
            plt.plot(new_dat['Time'][-num_plot:], new_dat['Voltage'][-num_plot:])
            plt.plot(new_dat['Time'][-num_fit_lin:], \
                     params_lin[0]*new_dat['Time'][-num_fit_lin:] + params_lin[1])
            plt.plot(new_dat['Time'][-2*num_fit_lin:-num_fit_lin], \
                     params_lin[0]*new_dat['Time'][-2*num_fit_lin:-num_fit_lin] + \
                     params_lin[1])
        '''

    #print('Exponential Decay ', val_exp)
    print('Linear last point ', val_lin)
    #plt.show()
    meas = np.asarray(meas)
    #val_exp = np.asarray(val_exp)
    val_lin = np.asarray(val_lin)
    ordered = np.argsort(meas)
    meas = meas[ordered]
    #val_exp = val_exp[ordered]
    val_lin = val_lin[ordered]
 
    return val_lin

def main():

    directory = (r'R:\Lab Member Files\Tony Edgeton\Raw Data'
                   r'\Transport\PPMS\B015\220606\0deg'
                   r'\200K_from10kOe\highH\negIonly\down')

    os.chdir(directory)

    num_each = 1 # number of measurements done at each field during sweep
    repeat = 1 # number of measurements at each field in directory


    #fln = glob.glob('IV_sweep*_-300Oe_*neg*.txt')
    #flp = glob.glob('IV_sweep*_-300Oe_*pos*.txt')

    fln = glob.glob('IV_sweep*_-11000.00u*neg*.txt')
    flp = glob.glob('IV_sweep*_-11000.00u*pos*.txt')

    num_fit_lin = 30


    fields_neg = []
    for f in fln:
        #print('about to get ', f)
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
    print('number of fields ', num_files/repeat)
    
    diff_0 = []
    diff_1 = []
    diff_00 = []
    sum_00 = []
    diff_02 = []
    for_boxes = []
    for i in range(int(num_files/repeat)):
        flneg = [fln[j] for j in neg_inds[repeat*i:repeat*(i+1)]]
        flpos = [flp[j] for j in pos_inds[repeat*i:repeat*(i+1)]]

        #print('Working on Field ', ur.get_field(flneg[0]))
        print(flneg[0])

        if i == 25:
            print(flneg)

        val_lin_neg = get_data(flneg, num_fit_lin)
        val_lin_pos = get_data(flpos, num_fit_lin)

        neg_0 = np.mean(val_lin_neg[:num_each])
        neg_1 = np.mean(val_lin_neg[num_each:])
        pos_0 = np.mean(val_lin_pos[:num_each])
        pos_1 = np.mean(val_lin_pos[num_each:])

        diff_0.append( pos_0 + neg_0 )
        diff_1.append( pos_1 + neg_1 )
        diff_00.append(val_lin_pos[0] 
                       - val_lin_neg[0]*11./6.) # + for opposite currents
        sum_00.append(val_lin_pos[0] 
                      + val_lin_neg[0]*11./6.) # - for opposite currents
        #diff_02.append(val_lin_pos[2] + val_lin_neg[2])

        print(pos_0, neg_0)
        #print('differences', diff_0, diff_1)


        '''
        #plt.boxplot([val_lin_pos[:4]*-1, val_lin_pos[4:]*-1, \
        #            val_lin_neg[:4], val_lin_neg[4:]], \
        #            showmeans=True)

        for_boxes.append(val_lin_pos[:4]*-1)
        for_boxes.append(val_lin_neg[:4])

        plt.boxplot([val_lin_pos[:4]*-1, \
                    val_lin_neg[:4]], \
                    showmeans=True)

        plt.plot([1.1,1.1,1.1,1.1], val_lin_pos[:4]*-1, 'ko')
        #plt.plot([2,2,2,2], val_lin_pos[4:]*-1, 'ko')
        plt.plot([2.1,2.1,2.1,2.1], val_lin_neg[:4], 'ko')
        #plt.plot([4,4,4,4], val_lin_neg[4:], 'ko')

        plt.show()
        '''
    fld_ind = (np.arange(num_files/repeat)*repeat).astype(int)

    #plt.boxplot(for_boxes, showmeans=True)
    #plt.show()

    to_write = pd.DataFrame({'Fields': pd.Series(fields_pos[pos_inds[fld_ind]]), \
                             'V diff dn': pd.Series(diff_0, dtype='float64'), \
                             'V diff up': pd.Series(diff_1, dtype='float64'), \
                             'V diff 0': pd.Series(diff_00, dtype='float64'), \
                             'V sum 1': pd.Series(sum_00, dtype='float64'), \
                             'V diff 2': pd.Series(diff_02, dtype='float64')}) 

    to_write.to_csv('Delta_Summary_linear.txt', sep='\t', index=False)

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
