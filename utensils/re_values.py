# This script contains functions related to extracting experiment
# values and paratemeters from strings.


import numpy as np
import re



def get_current(string):
    
    restring = '(?<=B_)\d\d\d(?=mA)|(?<=B_)\d\d(?=mA)|(?<=B_)\d(?=mA)|' + \
               '(?<=B_)\d\S\d(?=mA)|(?<=B_)\d\S\d\d(?=mA)|' + \
               '(?<=B_)\d\d\S\d\d(?=mA)|(?<=B_)\d\d\S\d(?=mA)|' + \
               '(?<=B_)\d\d\d\S\d\d(?=mA)|(?<=B_)\d\d\d\S\d(?=mA)'

    ang = re.findall(restring, string)
    angle = float(ang[0])
    print('Currents ', ang)

    return angle


def get_field(string):
    
    restring = '(?<=K_)\d\d\d(?=Oe)|(?<=K_)\d\d(?=Oe)|(?<=K_)\d(?=Oe)|' + \
               '(?<=K_)\S\d\d(?=Oe)|(?<=K_)\S\d\d\d(?=Oe)|' + \
               '(?<=K_)\S\d\d\d\d(?=Oe)|(?<=K_)\S\d\d\d(?=Oe)|' + \
               '(?<=K_)\S\d\d\d\d\d(?=Oe)|(?<=K_)\S\d\d\d\d(?=Oe)'

    ang = re.findall(restring, string)
    angle = float(ang[0])
    #print('Currents ', ang)

    return angle


def get_ordinal(string):
    
    restring = '(?<=ve_)\d\d\d(?=.txt)|(?<=ve_)\d\d(?=.txt)|(?<=ve_)\d(?=.txt)'

    ang = re.findall(restring, string)
    angle = float(ang[0])
    #print('Currents ', ang)

    return angle





