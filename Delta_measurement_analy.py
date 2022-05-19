# This script analyses complete Delta meaurement results to determine
# the actualy resistance with good precision.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.optimize import curve_fit
import utensils.re_values as ur
 

def exp_decay(time, A, tau, x0, y0):
    
    return A*np.exp(-(time-x0)/tau)+y0


def extract_voltage(dfl, npts, exp_fit):

    vs = []
    i = 0
    for df in dfl:
        voltage = np.mean(df[0]['Voltage'][-npts:])
        voltage = np.mean(df[0]['Voltage'][-50:])
        volt_std = np.std(df[0]['Voltage'][-npts:])

        print('standard dev ', volt_std)


        if exp_fit:
        #if (exp_fit and volt_std>5.e-7):
            print(df[1])

            p0=[-np.sign(voltage)*7.7e-5, 8., 10., voltage]

            lower = [-np.inf, 4., 3., -np.inf]
            upper = [np.inf, 20., 20., np.inf]
            try:
                params = curve_fit(exp_decay, df[0]['Time'][-npts:], \
                                   df[0]['Voltage'][-npts:], p0=p0, \
                                   bounds = [lower, upper])

            except RuntimeError:
                print('Got Runtime Error')
                print('Voltage is ', voltage)

                volt_fit = 0.

            else:
                volt_fit = params[0][-1]
                print(params[0])

            
            if i%2 == 0:
                fit = exp_decay(df[0]['Time'][-npts:], *params[0])
                resids = df[0]['Voltage'][-npts:] - fit

                #plt.plot(df[0]['Time'][-npts:], df[0]['Voltage'][-npts:], 'b-o')
                #plt.plot(df[0]['Time'][-npts:], fit )
                #plt.plot(df[0]['Time'][-npts:], resids)
                #plt.show()
            
        vs.append([voltage, volt_fit, df[1]])
        i += 1

    return vs
        

def combine_field(vl1, vl2, operation = 'add', same=False):

    combo = []
    for i in range(len(vl1)):

        field1 = vl1[i][2]

        for j in range(len(vl2)):

            if same:
                if i == j:
                    field2 = vl2[j][2]+10.
                    
                else:
                    field2 = vl2[j][2]

            else:
                field2 = vl2[j][2]


            if abs(field1 - field2) < 2:

                if operation == 'add':

                    combo.append([(vl1[i][0] + vl2[j][0])/2., \
                                  (vl1[i][1] + vl2[j][1])/2.,  field1])

                if operation == 'sub':

                    combo.append([(vl1[i][0] - vl2[j][0])/2., \
                                   (vl1[i][1] - vl2[j][1])/2.,  field1])

    return combo


def main():

    directory = r'R:\Lab Member Files\Tony Edgeton\Raw Data\Transport\PPMS\B015\30K_Delta\from15kOe\sweep_1'

    os.chdir(directory)


    fln = glob.glob('IV_sweep_*neg*.txt')
    flp = glob.glob('IV_sweep_*pos*.txt')
    #print(fln)
    

    datan = []
    for f in fln:
        field = ur.get_field(f)
        datan.append([pd.read_csv(f, sep='\t+', engine='python'), field])

    print('Done reading in negative currents')
    datap = []
    for f in flp:
        field = ur.get_field(f)
        datap.append([pd.read_csv(f, sep='\t+', engine='python'), field])

    print('Done reading in positive currents')

    vn = extract_voltage(datan, 350, True)
    vp = extract_voltage(datap, 350, True)
 
    # Average negative and positive values individually
    vn_avg = combine_field(vn, vn, 'add', same=True)
    vp_avg = combine_field(vp, vp, 'add', same=True)
    # match neg and pos values by field
    v_diff_avg = np.asarray(combine_field(vp_avg, vn_avg, 'add'))
    vn_avg = np.asarray(vn_avg)
    #print(vn_avg)

    vn = np.asarray(vn)
    vp = np.asarray(vp)
 
    number = len(vn)/2
    print('length', number)
    first = (np.arange(number)*2).astype(int)
    second = (np.arange(number)*2+1).astype(int)
    fourth = (np.arange(number)*4).astype(int)
    print(type(first))
    print('vn_avg', vn_avg)

    print('v_diff_avg', v_diff_avg)


    vn = np.asarray(vn)
    vp = np.asarray(vp)
    v_for_csv = pd.DataFrame({'Field': pd.Series(vn[first, 2]), \
                              'Vn 0': pd.Series(vn[first,1]), \
                              'Vn 1': pd.Series(vn[second,1]), \
                              'Vp 0': pd.Series(vp[first,1]), \
                              'Vp 1': pd.Series(vp[second,1]), \
                              'V diff avg': pd.Series(v_diff_avg[fourth,0]), \
                              'V diff fit': pd.Series(v_diff_avg[fourth,1]), \
                              })


    v_for_csv.to_csv('IV_summary.txt', sep='\t', index=False)
    
    #plt.plot(vn_avg[:,1], vn_avg[:,0], 'r-o')
    plt.plot(v_diff_avg[:,2], v_diff_avg[:,0], 'r-o')
    plt.plot(v_diff_avg[:,2], v_diff_avg[:,1], 'b-o')
    #plt.plot(hp, vp, 'b-o')
    plt.show()
    


if __name__ == "__main__":
    main()
