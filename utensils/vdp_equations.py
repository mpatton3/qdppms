# This script contains functions for solving van der Pauw transport.



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.optimize import root
from scipy.stats import linregress
from scipy.optimize import fsolve


def vdpthm(rho, rx, ry):

    return np.exp(-np.pi*rx/rho) + np.exp(-np.pi*ry/rho) - 1.


def getrsq(r1, r2):
    
    sol = root(vdpthm, np.pi*min([abs(r1), abs(r2)]), args=(abs(r1), abs(r2)))

    return sol.x[0]

def hall_params(hs, rhs, rsq, t):
    
    m, b, r, p, sd = linregress(hs, rhs)
    cd = 1/1.602e-19/t/(m*10**4)*10**-4
    mob = abs(m*10**8/rsq)

    return cd, mob, m

def vdpRmeas(rhos, lx, ly, rmx):

    ''' This function follows Bierman et al equation 10 to find the
    measurable Rxx as a function of the intrinsic resistivities and
    lengths between leads when in a rectuangular patter. '''

    #ly *= 0.5
    term1 = 8./np.pi*np.sqrt(rhos[0]*rhos[1])
    rrl = np.sqrt(rhos[0]/rhos[1])*ly/lx
    ns = [2.*x+1 for x in range(9)]
    term2 = sum([1/(n*np.sinh(rrl*np.pi*n)) for n in ns])

    return term1*term2 - rmx
def getRxx(rhoxx, rhoave, lx, ly, rmx):

    #print type(rhoxx)
    rhoyy = rhoave**2/rhoxx
    term1 = 8./np.pi*rhoave
    rrl = rhoxx/rhoave*ly/lx
    #print rrl, type(rrl)
    #print type(rrl)
    ns = [2.*x+1 for x in range(5)]
    term2= sum([1./(np.sinh(rrl*np.pi*n)) for n in ns])

    return term1*term2 - rmx

def anst_from_vdp(Rxx, Ryy, arat):
    
    '''This function takes the van der Pauw sheet resistance measurements
    and uses them to compute the resistivities in the corresponding directions
    along with the resistivity anisotropy.
    arat is ly/lx'''
    rguess = np.pi*min([Rxx, Ryy])

    rsq = root(vdpthm, rguess, args=(Rxx, Ryy))
    rhoave = rsq.x[0]

    soly = root(getRxx, rhoave, args=(rhoave, 1., arat, Rxx))
    solx = root(getRxx, rhoave, args=(rhoave, arat, 1., Ryy))
    
    rhoxx = solx.x[0]
    rhoyy = soly.x[0]
    a = min([rhoxx, rhoyy])/max([rhoxx, rhoyy])

    return rhoxx, rhoyy, a


def main():

    print('in main')


if __name__ == '__main__':
    main()
