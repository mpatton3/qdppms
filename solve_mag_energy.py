# This script sovles for the M-H characteristic based on the anisotropy
# energy. It follows equation (5) in Hayashi, Kim et al PRB 89, 144425 (2014).


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, root_scalar, fmin

def dE_dth(theta, H):

    #return np.cos(theta+0.)/np.sin(2.*theta) -  1./H
    #return H*np.cos(theta+0.)/np.sin(2.*theta) -  1.
    return H*np.cos(theta+0.) -  1.*np.sin(2.*theta)



def dE_dth2(theta, dp0, dph, dth, H):

    keff = 1.
    ki = 1.
    first = (keff - ki*dp0)*np.sin(2.*theta)
    sec = (np.cos(theta)*(1-dp0**2-dph**2 + dp0*dph - dth**2)
           + np.sin(theta)*dth)

    return first - H*sec

def find_root(theta_guess, H, bracket):
    
    #x = fsolve(dE_dth, theta_guess, args=(H), factor=0.01)
    x = root_scalar(dE_dth,  args=(H), method='bisect', bracket=bracket,
                    x0=theta_guess, x1=0.1)

    return x

def find_root2(theta_guess, H, bracket):
    
    #x = fsolve(dE_dth, theta_guess, args=(H), factor=0.01)
    x = root_scalar(dE_dth2,  args=(0.20, 0.00, 0.00, H), method='bisect',
                    bracket=bracket, x0=theta_guess, x1=0.1)

    return x


def find_minimum(theta_guess, H):

    x = fmin(dE_dth, x0=theta_guess, args=(theta_guess, H))

    return x


def main():

    Hs = np.linspace(-1.55, 1.55, 120) 
    xs = []

    th_guess = 0.1
    for H in Hs:
        
        print(H)

        if H > 0.01:
            th_guess = 0.1
            bracket = [0.004, 1.2]
        if H < -0.01:
            print('not here')
            th_guess = -0.1
            bracket = [-1.56, -0.004]
        else:
            th_guess = 0.0

        #xs.append(find_root(th_guess, H, bracket)[0])
        xs.append(find_root2(th_guess, H, bracket).root)

        #print(find_minimum(th_guess, H))

        #th_guess = xs[-1]
        
    print(xs)

    ths = np.linspace(-np.pi*0.99, np.pi*0.99, 350)
    ms = [np.cos(x) for x in xs]
    plt.plot(Hs, ms)
    #plt.plot(ths, dE_dth2(ths, 0, 0, 0, -1.5))
    #plt.plot(ths, dE_dth2(ths, 0, 0, 0, 0.3441))
    #plt.plot(ths, dE_dth2(ths, 0.5, 0.5, 0.5, 0.3441), 'm')
    plt.plot(ths, [0.]*len(ths), 'k')
    plt.show()




if __name__ == '__main__':
    main()
