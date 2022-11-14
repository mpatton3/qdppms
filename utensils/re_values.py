# This script contains functions related to extracting experiment
# values and paratemeters from strings.


import numpy as np
import re



def get_current(string, units='mA'):
    
    if units == 'mA':
        restring = ('(?<=B_)\d\d\d(?=mA)|(?<=B_)\d\d(?=mA)|(?<=B_)\d(?=mA)|'
                    '(?<=B_)\d\S\d(?=mA)|(?<=B_)\d\S\d\d(?=mA)|'
                    '(?<=B_)\d\d\S\d\d(?=mA)|(?<=B_)\d\d\S\d(?=mA)|'
                    '(?<=B_)\d\d\d\S\d\d(?=mA)|(?<=B_)\d\d\d\S\d(?=mA)'
                    )

    if units == 'uA':
        restring = ('(?<=Oe_)\d\d\d(?=uA)|(?<=Oe_)\d\d(?=uA)|(?<=Oe_)\d(?=uA)|'
                    '(?<=Oe_)\d\S\d(?=uA)|(?<=Oe_)\d\S\d\d(?=uA)|'
                    '(?<=Oe_)\d\d\S\d\d(?=uA)|(?<=Oe_)\d\d\S\d(?=uA)|'
                    '(?<=Oe_)\d\d\d\S\d\d(?=uA)|(?<=Oe_)\d\d\d\S\d(?=uA)|'
                    '(?<=Oe_)\d\d\d\d\d\S\d\d(?=uA)|'
                    '(?<=Oe_)\d\d\d\d\S\d\d(?=uA)'
                    )

    ang = re.findall(restring, string)
    angle = float(ang[0])
    #print('Currents ', ang)

    return angle


def get_field(string):
    
    restring = ('(?<=K_)\d(?=Oe)|(?<=K_)\d\d(?=Oe)|(?<=K_)\d\d\d(?=Oe)|'
                  '(?<=K_)\d\d\d\d(?=Oe)|(?<=K_)\d\d\d\d\d(?=Oe)|'
                  '(?<=K_)\d\d\d\d\d\d(?=Oe)|(?<=K_)\S\d(?=Oe)|'
                  '(?<=K_)\S\d\d(?=Oe)|(?<=K_)\S\d\d\d(?=Oe)|'
                  '(?<=K_)\S\d\d\d\d\d(?=Oe)|(?<=K_)\S\d\d\d\d(?=Oe)')

    ang = re.findall(restring, string)
    angle = float(ang[0])
    #print('Currents ', ang)

    return angle


def get_temp(string):
    
    restring = ('(?<=_)\d\d\d\S\d\d(?=K)|(?<=K_)\d\d\S\d\d(?=K)|'
                  '(?<=_)\d\S\d\d(?=K)|(?<=_)\d\d\d\S\d(?=K)|'
                  '(?<=_)\d\d\d(?=K)')

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

def get_angle(string):
    
    restring = '(?<=uA_)\d\d\d(?=deg)|(?<=uA_)\d\d(?=deg)|(?<=uA_)\d(?=deg)'

    ang = re.findall(restring, string)
    angle = float(ang[0])
    #print('Currents ', ang)

    return angle

def get_meta_field(string):

    restring = ''


def get_squid_range(string):
    """Get the 'squid range' parameter, which is used to scale the voltage
    data in the raw trace."""

    restring = ('(?<=ge\s=\s)\d\d\d(?=;giv)|(?<=ge\s=\s)\d\d(?=;giv)|'
                '(?<=ge\s=\s)\d(?=;giv)|(?<=ge\s=\s)\d\d\d\d(?=;giv)')

    srang = re.findall(restring, string)
    srange = float(srang[0])

    return srange


def get_low_field(string):
    """Get the 'low field' parameter, which is used to know the field value
    during the measurement."""

    restring = ('(?<=ld\s=\s)\d+\S\d+(?=\sOe;)|(?<=ld\s=\s)\S\d+\S\d+(?=\sOe;)|'
                '(?<=ld\s=\s)\d(?=\sOe;)|(?<=ld\s=\s)\d\d\d\d(?=\sOe;)')

    fiel = re.findall(restring, string)
    field = float(fiel[0])

    return field


def main():

    print('I compiled!')

if __name__ == '__main__':
    main()


