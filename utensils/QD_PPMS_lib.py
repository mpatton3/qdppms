# This is a library for classes and functions related to QD PPMS data
# files. Both reading, writing, and data reduction/computation.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import linregress
from scipy.optimize import root
from scipy.optimize import fsolve
import utensils.vdp_equations as ve


def split_datafile(data):

    ln = len(data)/4

    first = [[4*i, 4*i+1] for i in range(ln)]
    first_flat = [item for sublist in first for item in sublist]
    second = [[4*i+2, 4*i+3] for i in range(ln)]
    sec_flat = [item for sublist in second for item in sublist]
    data1 = data.iloc[first_flat,:]
    data2 = data.iloc[sec_flat,:]
    print(len(data1), len(data2), len(data))

    return data1, data2



def vdpthm(rho, rx, ry):

    return np.exp(-np.pi*rx/rho) + np.exp(-np.pi*ry/rho) - 1.


def getrsq(r1, r2):
    
    sol = root(vdpthm, np.pi*min([abs(r1), abs(r2)]), args=(abs(r1), abs(r2)))

    return sol.x[0]


class Measurement:

    '''This class stores all the measurements values for one data point. This
    pertains to vdP measurements, so it is 2 vdP resistances, 2 Hall resistances,
    and associated derived parameters along with the thermo conditions.'''

    def __init__(self, temp, bfld, thick):
    
        self.temp = temp
        self.bfld = bfld

    
    def get_resistances(self, data, index, hall=True):

        if data.iloc[index*4, 4] == 1:
            self.resv1 = data.iloc[index*4,8]
        else:
            print('Data not structured as anticipated. VdP 1', index)

        if data.iloc[index*4+1, 4] == 1:
            self.resv2 = data.iloc[index*4+1,8]
        else:
            print('Data not structured as anticipated. VdP 2', index)
            

        if hall == True:
            if data.iloc[index*4+2, 4] == 2:
                self.resh1 = data.iloc[index*4+2,8]
            else:
                print(data.tail(4))
                print('Data not structured as anticipated. Hall 1', index*4+2)
        
            if data.iloc[index*4+3, 4] == 2:
                self.resh2 = data.iloc[index*4+3,8]
            else:
                print('Data not structured as anticipated. Hall 2', index*4+3)
                print(data.iloc[index*4+3, 8])

            self.resh = (self.resh1 + self.resh2)/2.

        else: 
            self.resh = 0.


        return


    def get_resistances_2samp(self, data, index, hall=True):

        if data.iloc[index*8, 4] == 1:
            self.resv11 = data.iloc[index*8,8]
        else:
            print('Data not structured as anticipated. VdP 1', index)

        if data.iloc[index*8+1, 4] == 1:
            self.resv21 = data.iloc[index*8+1,8]
        else:
            print('Data not structured as anticipated. VdP 1', index)


        if data.iloc[index*8+2, 4] == 1:
            self.resv12 = data.iloc[index*8+2,8]
        else:
            print('Data not structured as anticipated. VdP 2', index)
        if data.iloc[index*8+3, 4] == 1:
            self.resv22 = data.iloc[index*8+3,8]
        else:
            print('Data not structured as anticipated. VdP 2', index)
            

        if hall == True:
            if data.iloc[index*8+4, 4] == 2:
                self.resh11 = data.iloc[index*8+4,8]
            else:
                print(data.tail(4))
                print('Data not structured as anticipated. Hall 1', index*8+4)

            if data.iloc[index*8+5, 4] == 2:
                self.resh21 = data.iloc[index*8+5,8]
            else:
                print(data.tail(4))
                print('Data not structured as anticipated. Hall 1', index*8+5)
        
            if data.iloc[index*8+6, 4] == 2:
                self.resh12 = data.iloc[index*8+6,8]
            else:
                print('Data not structured as anticipated. Hall 2', index*8+6)
                print(data.iloc[index*8+6, 8])

            if data.iloc[index*8+7, 4] == 2:
                self.resh22 = data.iloc[index*8+7,8]
            else:
                print('Data not structured as anticipated. Hall 2', index*8+7)
                print(data.iloc[index*8+7, 8])

            self.resh1 = (self.resh11 + self.resh12)/2.

            self.resh2 = (self.resh21 + self.resh22)/2.


        else: 
            self.resh = 0.


        self.rsq1 = getrsq(self.resv11, self.resv12)
        self.rsq2 = getrsq(self.resv21, self.resv22)


        return
 

    def comp_rsq(self):

        self.rsq = getrsq(self.resv1, self.resv2)

        return

def read_metadata(filename):

    metadata = {}

    with open(filename, 'r') as f:

        stillmeta = True 

        i = 0
        while stillmeta:
            line = f.readline().strip()
            print(line)
            i += 1
            if line[0] != '#':
                stillmeta = False

            else:
                line = line.replace('#\t', '')
                metaval = [x.strip() for x in line.split(':')]

                try:
                    metaval[1] = float(metaval[1])
                except ValueError:
                    pass

                metadata[metaval[0]] = metaval[1]

    print(i, metadata)
    return metadata, i


class VdP_Measurement:

    '''This class handles the structure of a Hall sweep measurement done in a
    vdP contact configuration.'''

    def __init__(self, filename, thick, channel=1):

        self.thick = thick
        self.channel = channel

        metafacts = read_metadata(filename)
        self.metadata = metafacts[0]
        self.data = pd.read_csv(filename, skiprows = metafacts[1]-1,
                                engine='python')

        print(self.data.head())

        self.temp = self.data['Temperature'].mean()
        self.field = self.data['\g(m)\-(0)H'].mean()
        self.length = len(self.data)

        print(self.temp, self.field)

        if self.channel == 1:
            self.namevdp1 = 'R vdp 1'
            self.namevdp2 = 'R vdp 2'
            self.namehall1 = 'R Hall 1'
            self.namehall2 = 'R Hall 2'
        if self.channel == 2:
            self.namevdp1 = 'R vdp 12'
            self.namevdp2 = 'R vdp 22'
            self.namehall1 = 'R Hall 12'
            self.namehall2 = 'R Hall 22'
        if self.channel == "hb1":
            self.namelng = "R Long 1"
            self.namehll = "R Hall 1"
        if self.channel == "hb2":
            self.namelng = "R Long 2"
            self.namehll = "R Hall 2"
 
    def compute_resistances(self):
        
        self.rsqs = []
        self.halls = []
        self.rhoxs = []
        self.rhoys = []
        
        for i in range(self.length):

            if (self.channel == 1 or self.channel == 2):
                self.rsqs.append(getrsq(self.data[self.namevdp1].loc[i],
                                 self.data[self.namevdp2].loc[i]))

                self.halls.append((self.data[self.namehall1].loc[i] 
                                   + self.data[self.namehall2].loc[i])/2.)

                rhoanis = ve.anst_from_vdp(self.data[self.namevdp1].loc[i],
                                        self.data[self.namevdp2].loc[i], 1.)
                self.rhoxs.append(rhoanis[0])
                self.rhoys.append(rhoanis[1])

            if (self.channel == 'hb1' or self.channel == 'hb2'):
                self.rsqs.append(self.data[self.namelng].loc[i])
                self.halls.append(self.data[self.namehll].loc[i])
                self.rhoxs.append(0.)
                self.rhoys.append(0.)
 
        self.halls = pd.Series(self.halls)

    def compute_resistances_hb(self):
        """Same as compute_resistances() above, but for a Hall bar scenario.
        Actually ended up implementing it in the above method by adding if
        statement and using the self.channel attribute."""

        self.rsqs = []
        self.halls = []
        self.rhoxs = []
        self.rhoys = []
 
        for i in range(self.length):
            self.rsqs.append(self.data[self.namelng].loc[i])
            self.halls.append(self.data[self.namehll].loc[i])
            self.rhoxs.append(0.)
            self.rhoys.append(0.)
        

    def compute_params(self):


        self.ncd, self.mu, self.m = ve.hall_params(self.data['\g(m)\-(0)H'], \
                        self.halls, self.rsqs[-1], self.thick)

        self.vnum = (3*np.pi)**(2./3.)*1.0546e-34*abs(self.m*self.thick*10**8)**(1./3.)
        self.vdem = (self.rsqs[-1]*self.thick*(1.602e-19)**(5./3.))


    def compute_anomalous(self, lists, bfldcut):


        nezero = np.where(abs(self.data['\g(m)\-(0)H'])<bfldcut)[0]
        arzero = np.where(abs(self.data['\g(m)\-(0)H'])>2.)[0]
        nearzero = np.intersect1d(nezero, arzero) # exclue points at B=0

        farzerpos = np.where(self.data['\g(m)\-(0)H']>bfldcut)[0]
        farzerneg = np.where(self.data['\g(m)\-(0)H']<-bfldcut)[0]
        mp, bp, r, p, sd =  linregress(self.data['\g(m)\-(0)H'].iloc[farzerpos],\
                            self.halls.iloc[farzerpos])
        mn, bn, r, p, sd =  linregress(self.data['\g(m)\-(0)H'].iloc[farzerneg],\
                            self.halls.iloc[farzerneg])
#       mn, bn, r, p, sd =  linregress(self.data[farzerpos,13], rhal[farzerpos])
        mz, bz, r, p, sd =  linregress(self.data['\g(m)\-(0)H'].iloc[nearzero],\
                            self.halls.iloc[nearzero])

        #plt.plot(self.data['\g(m)\-(0)H'], self.data['\g(m)\-(0)H']*mp+bp, 'b-')
        #plt.plot(self.data['\g(m)\-(0)H'], self.data['\g(m)\-(0)H']*mn+bn, 'g-')
        #plt.plot(self.data['\g(m)\-(0)H'], self.halls, 'r-')
        #plt.show()


        rhalpos = np.mean(self.halls.iloc[farzerpos]
                          -mp*self.data['\g(m)\-(0)H'].iloc[farzerpos])
        rhalneg = np.mean(self.halls.iloc[farzerneg]
                          -mn*self.data['\g(m)\-(0)H'].iloc[farzerneg])
        rhalsat =  (rhalpos-rhalneg)/2.
        rhalsatavg = (rhalpos+rhalneg)/2.
        m = (mp + mn)/2.
        b = (bp - bn)/2.

        lists[11].append(b*self.thick)
        lists[12].append(m*self.thick*10**8)
        lists[13].append(mz*self.thick*10**8)
        lists[14].append(rhalsat)

        return lists


    def list_append(self, lists):

        if (self.channel == 1 or self.channel == 2):
            lists[0].append(self.data[self.namevdp1].iloc[-1])
            lists[1].append(self.data[self.namevdp2].iloc[-1])
            lists[2].append(self.data[self.namehall1].iloc[-1])
            lists[3].append(self.data[self.namehall2].iloc[-1])
        if (self.channel == "hb1" or self.channel == "hb2"):
            lists[0].append(self.data[self.namelng].iloc[-1])
            lists[1].append(0.)
            lists[2].append(self.data[self.namehll].iloc[-1])
            lists[3].append(0.)

        lists[4].append(self.rsqs[-1])
        lists[5].append(self.rsqs[-1]*self.thick)
        lists[6].append(self.m*self.thick*10**8)
        lists[7].append(self.ncd)
        lists[8].append(self.mu)
        lists[9].append(self.vnum/self.vdem)
        lists[10].append(self.temp)

        return lists


    def write(self, newname):

        if (self.channel == 1 or self.channel == 2):
            df = pd.DataFrame({'Temperature': self.data['Temperature'], \
                           '\g(m)\-(0)H': self.data['\g(m)\-(0)H'], \
                           'R vdP 1': self.data[self.namevdp1], \
                           'R vdP 2': self.data[self.namevdp2], \
                           'R Hall 1': self.data[self.namehall1], \
                           'R Hall 2': self.data[self.namehall2], \
                           'Rsq': pd.Series(self.rsqs) , \
                           '\g(r)': pd.Series(self.rsqs)*self.thick , \
                           '\g(r)\-(xx)': pd.Series(self.rhoxs), \
                           '\g(r)\-(yy)': pd.Series(self.rhoys), \
                           'R\-(Hall)': self.halls })

        if (self.channel == "hb1" or self.channel == "hb2"):
            df = pd.DataFrame({'Temperature': self.data['Temperature'], \
                           '\g(m)\-(0)H': self.data['\g(m)\-(0)H'], \
                           'R vdP 1': self.data[self.namelng], \
                           'R vdP 2': np.zeros(self.length), \
                           'R Hall 1': self.data[self.namehll], \
                           'R Hall 2': np.zeros(self.length), \
                           'Rsq': pd.Series(self.rsqs) , \
                           '\g(r)': pd.Series(self.rsqs)*self.thick , \
                           '\g(r)\-(xx)': pd.Series(self.rhoxs), \
                           '\g(r)\-(yy)': pd.Series(self.rhoys), \
                           'R\-(Hall)': self.halls })

      
        df = df[['Temperature', '\g(m)\-(0)H', 'R vdP 1', 'R vdP 2', \
                 'R Hall 1', 'R Hall 2', 'Rsq', '\g(r)', \
                 '\g(r)\-(xx)', '\g(r)\-(yy)', 'R\-(Hall)']]


        print('writing to new file')
        df.to_csv(newname, sep='\t', index=False)


class rho_v_temp:

    def __init__(self, data):

        self.data = data
        self.temps = data['Temperature (K)']
        self.angle = data['Sample Position (deg)']
        self.ress = data['Resistance Ch1 (Ohms)']
        self.harm2 = data['2nd Harmonic Ch1 (dB)']
        self.harm2 = np.array([self.ress[i]*10.**(self.harm2[i]/10) 
                              for i in range(len(self.data))])

        print(self.temps[:3])
        print(self.ress[:3])

        return


    def plot(self):
        
        plt.plot(self.temps, self.ress, 'bo-')
        plt.xlabel('Temperatue (K)')
        plt.ylabel(r'Resistance ($\Omega$)')
        plt.show()

        return


    def write(self, newname):

        df = pd.DataFrame({'Temperature': self.temps, \
                           'Angle': self.angle, \
                           'Resistance': self.ress, \
                           '2nd Harm': self.harm2 })

        df = df[['Temperature', 'Angle', 'Resistance', '2nd Harm']]

        df.to_csv(newname, sep='\t', index=False)

        return


