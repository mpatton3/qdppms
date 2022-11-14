# This script fits R_H v H values according to equation S2.6 in Fan etal
# Nature Materials 2014.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import root
import os


def anisotropy(thM, Bext, thB, K):

    kterm = K * np.cos(thM) * np.sin(thM)
    bterm1 = Bext * np.sin(thB) * np.cos(thM)
    bterm2 = Bext * np.cos(thB) * np.sin(thM)

    return kterm - bterm1 + bterm2

def find_thM(Bext, thB, K):
    
    thM = root(anisotropy, 0.2, (Bext, thB, K))

    return thM.x


def main():


    bs = np.linspace(-10000., 10000., 30)
    thB = np.pi/2.
    K = 5000.

    thM = []
    costhM = []
    for i in range(len(bs)):
        sol = find_thM(bs[i], thB, K)
        thM.append(sol)
        costhM.append(np.cos(sol))


    plt.plot(bs, thM)
    plt.plot(bs, costhM)
    plt.show()


if __name__ == "__main__":
    main()
