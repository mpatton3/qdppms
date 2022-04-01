# This plots data taken with lockin_quickmeas.py


import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#import plotly.express as px
import os


def main():

    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B015'
    os.chdir(directory)
    data_filename = 'volt_2w_Hall_v_B_300K_B015_0.txt'

    data = pd.read_csv(data_filename, sep="\t+")

    
    print(data.head())

    data.plot(x='\g(m)\-(0)H', y="Volts", kind='scatter')


if __name__ =="__main__":
    main()
