# This script reads in SHH data taken at low fields, with out-of-plane
# magnetization and fits it to determine Hdl and SOT efficiency


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.optimize import curve_fit
import re
import utensils.re_value as ur


def find_line(fn, strng):
    # Find the line number at which a certain string resides in a .txt file
    # The search goes through line by line starting at the line set by ln.   ln = 0

    ln = 0
    with open(fn, 'r') as input_data:
        for line in input_data:
            ln = ln+1
            if line.strip() == strng:
                break
    input_data.close()
    
    return ln-1


def get_current(string):
    
    restring = '(?<=B_)\d\d\d(?=mA)|(?<=B_)\d\d(?=mA)|(?<=B_)\d(?=mA)|' + \
               '(?<=B_)\d\S\d(?=mA)|(?<=B_)\d\S\d\d(?=mA)|' + \
               '(?<=B_)\d\d\S\d\d(?=mA)|(?<=B_)\d\d\S\d(?=mA)|' + \
               '(?<=B_)\d\d\d\S\d\d(?=mA)|(?<=B_)\d\d\d\S\d(?=mA)'

    ang = re.findall(restring, string)
    angle = float(ang[0])
    print('Currents ', ang)

    return angle


def get_temperature(string):
    
    ang = re.findall('\d(?=K_)|\d\d(?=K_)|\d\d\d(?=K_)', string)
    angle = float(ang[0])

    return angle


def get_ch(string):
    
    ch = re.findall('(?<=ch)\d\d|(?<=ch)\d', string)
    crhr = int(ch[0])

    return crh


def values_and_names(strptrn):

    fl = glob.glob(strptrn)

    values = []
    for i in range(len(fl)):
        ic = get_current(fl[i])
        tt = get_temperature(fl[i])
        values.append([tt, ic, fl[i]])
    
    return values


def V1w_H(x, a, c):

    return a*x**2 + c


def V2w_H(x, b, c):

    return b*x + c


def separate_data(data, lowHcut, x_name = r'\g(m)\-(0)H'):
    # Separate data based on field increasing/decreasing and pos/neg.
    
    dfs = np.diff(data[x_name])

    inc_ind = np.where(dfs > 0.08)
    dec_ind = np.where(dfs < -0.08)
    pos_ind = np.where(data[x_name] > lowHcut)
    neg_ind = np.where(data[x_name] < -lowHcut)

    pos_inc_ind = np.intersect1d(inc_ind, pos_ind)
    pos_dec_ind = np.intersect1d(dec_ind, pos_ind)
    neg_inc_ind = np.intersect1d(inc_ind, neg_ind)
    neg_dec_ind = np.intersect1d(dec_ind, neg_ind)

    return [pos_inc_ind, pos_dec_ind, neg_inc_ind, neg_dec_ind]


def fit_model(data, indices, function, x_name=r'\g(m)\-(0)H', y_name='Voltx'):

    # Fit individual segments of the data to relevant model.

    ps = []
    for i in range(len(indices)):
        ps.append(curve_fit(function, data.loc[indices[i], x_name], \
                  data.loc[indices[i], y_name])[0])

    return ps # order is p_pos_inc, p_pos_dec, p_neg_inc, p_neg_dec]


def fit_func_vals(data, indices, params, function, x_name=r'\g(m)\-(0)H'):

    funcs = []

    for i in range(len(params)):
        funcs.append(function(data.loc[indices[i], x_name], *params[i]))

    return funcs # order is func_pos_inc, func_pos_dec, func_neg_inc, func_neg_dec]


def plot_fits(data, indices, fit_funcs, x_name = r'\g(m)\-(0)H', y_name='Voltx'):

    # Check fits with plots of the individual fits of segments.
    # Order correspondes to order of fit_funcs.
    for i in range(len(indices)):
        plt.plot(data.loc[indices[i], x_name], \
                 data.loc[indices[i], y_name])
        plt.plot(data.loc[indices[i], x_name], fit_funcs[i])
        plt.show()

def init_file(temp, sample):

    filename = 'SHH_summary_'+ "{:.2f}".format(temp) + 'K_' + \
                   sample + '.txt'
    
    if os.path.isfile(filename):
        os.remove(filename)

    column_names = 'Temperature\tCurrent\tH\\-(DL) posinc\t' + \
                   'H\\-(DL) posdec\tH\\-(DL) neginc\t' + \
                   'H\\-(DL) negdec\tH\\-(DL) mean\tH\\-(DL) std'

    column_units = 'K\tA\tOe\tOe\tOe\tOe\tOe\tOe'

    with open(filename, 'w') as f:
        f.write(column_names)
        f.write('\n')
        f.write(column_units)
        f.write('\n')


class SweepData_1w:

    def __init__(self, filename):

        self.header = find_line(filename, "#Data:")
        self.data = pd.read_csv(filename, sep = ',', header=self.header+1, engine='python')
   

    def fit_V_v_H(self, lowHcut, plot=False):
        
        # Separate data based on field increasing/decreasing and pos/neg.
        self.indices = separate_data(self.data, lowHcut, r'\g(m)\-(0)H')


        # Fit individual segments of the data to ax^2 + c model.
        self.params = fit_model(self.data, self.indices, V1w_H, \
                                   x_name=r'\g(m)\-(0)H', y_name='Voltx')

        self.fit_funcs = fit_func_vals(self.data, self.indices, \
                                    self.params, V1w_H, x_name=r'\g(m)\-(0)H')


        if plot:
            # Check fits with plots of the individual fits of segments.
            plot_fits(self.data, self.indices, self.fit_funcs, \
                      x_name = r'\g(m)\-(0)H', y_name='Voltx')


class SweepData_2w:

    def __init__(self, filename):

        self.header = find_line(filename, "#Data:")
        self.data = pd.read_csv(filename, sep = ',', header=self.header+1, engine='python')
   

    def fit_V_v_H(self, lowHcut, plot=False):
        
        # Separate data based on field increasing/decreasing and pos/neg.
        self.indices = separate_data(self.data, lowHcut, r'\g(m)\-(0)H')


        # Fit individual segments of the data to ax^2 + c model.
        self.params = fit_model(self.data, self.indices, V2w_H, \
                                   x_name=r'\g(m)\-(0)H', y_name='Volty')

        self.fit_funcs = fit_func_vals(self.data, self.indices, \
                                    self.params, V2w_H, x_name=r'\g(m)\-(0)H')


        if plot:
            # Check fits with plots of the individual fits of segments.
            plot_fits(self.data, self.indices, self.fit_funcs, \
                      x_name = r'\g(m)\-(0)H', y_name='Volty')


class SHH_Measurement:

    def __init__(self, temp, current, sample, write = False):

        self.temp = temp
        self.current = current
        self.sample = sample

        self.filename = 'SHH_summary_'+ "{:.2f}".format(self.temp) + 'K_' + \
                       self.sample + '.txt'
        

    def first_harmonic(self, filename, lowHcut, plot=False):

        self.data_1w = SweepData_1w(filename)
        params = self.data_1w.fit_V_v_H(lowHcut, plot)


    def second_harmonic(self, filename, lowHcut, plot=False):

        self.data_2w = SweepData_2w(filename)
        params = self.data_2w.fit_V_v_H(lowHcut, plot)


    def calculate_Hdl(self):

        self.Hdls = []
        for i in range(len(self.data_1w.params)):
            self.Hdls.append(-2.*self.data_2w.params[i][0]/(2*self.data_1w.params[i][0]))

        self.Hdl_mean = np.mean(self.Hdls)
        self.Hdl_std = np.std(self.Hdls)
        print(self.Hdls)
        print('Hdl = ', self.Hdl_mean, '\pm ', self.Hdl_std)


    def write_summary_file(self):
       
        dataline = "{:.2f}".format(self.temp) + '\t' + \
                   "{:.2e}".format(self.current) + '\t' 

        for value in self.Hdls:
            dataline +=  "{:.4f}".format(value) + '\t'

        dataline +=  "{:.4f}".format(self.Hdl_mean) + '\t'
        dataline +=  "{:.4f}".format(self.Hdl_std) + '\t'

        with open(self.filename, 'a') as f:
            f.write(dataline)
            f.write('\n')




def main():

    # PARAMETERS TO SET
    directory = r'R:\Lab Member Files\Tony Edgeton\Raw Data\Transport\PPMS\B015\test\10K'

    sample = 'B015test' # sample name, type = string
    write_summary = True # Whether to write a file summarizing reduced data.
    show_plots = False # Show plots of data with fits.
    lowHcut = 500. # Oe field magnitude above which to fit data.

    # Stop setting params

    os.chdir(directory)
    # Get filenames and Temp and Current
    values1 = values_and_names('volt_1w_Hall*_*meas_*.txt')
    print(values1)
 
    # Get filenames and Temp and Current
    values2 = values_and_names('volt_2w_Hall*_meas_*.txt')

    #filename2 = r'volt_2w_Hall_v_B_8mA_m0.43T_meas_30K_phi75deg_B015_0.txt'

    # Initialize summary file
    if write_summary:
        init_file(values1[0][0], sample)

    # pair files with the same currents for analysis
    for i in range(len(values1)):
        j = 0
        found = False
        compute = False
        while not found:

            if values1[i][1] == values2[j][1]:
                
                print('Doing ', values1[i][0], 'K', values1[i][1], 'mA')
                found = True
                compute = True

            else:

                j+=1

                if j == len(values2):
                    found= True
                    print('2w file not found for ', values1[i][0], \
                            'K ', values1[i][1], 'mA :(')

        if compute:
            shh_meas = SHH_Measurement(values1[i][0], values1[i][1]*10**-3,\
                                      sample, write = write_summary)
            shh_meas.first_harmonic(values1[i][2], lowHcut, plot=show_plots)
            shh_meas.second_harmonic(values2[j][2], lowHcut, plot=show_plots)
            shh_meas.calculate_Hdl()
            if write_summary:
                shh_meas.write_summary_file()


if __name__ == "__main__":
    main()



