# This script contains classes, function,s and code for setting
# a Keithley 6221 and 2182a current source voltmeter tandem for
# meaurement functionality.
# Specifically, we separate the arming from a 'do one measurement'
# to allow for easy in-loop measurement.


import numpy as np
import pandas as pd
import os
import statistics as st
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter
from time import sleep
from pymeasure.instruments.keithley import Keithley6221
from pymeasure.instruments.srs import SR830


def int_to_bool_list(num):

    bin_string = format(num, '015b')
    return [x == '1' for x in bin_string[::-1]]


def meas_value(measstr):

    numbers = [float(x) for x in measstr.split(",")]

    inds = np.arange(len(numbers)/2)*2

    mn = np.mean(numbers[::2])
    std = np.std(numbers[::2])

    return mn, std



class myKeithley6221(Keithley6221):

    def arm_preloop_delta(self, highcurr, delta, swpct1, swpct2, swpct3, \
                          nplc, rvng, measnum):


        self.reset()


        self.write(":TRAC:CLE; :TRAC:FEED SENS1; :TRAC:FEED:CONT NEXT;")

        highcurrstr = ":SOUR:DELT:HIGH " + str(highcurr) + ";"
        lowcurrstr = ":SOUR:DELT:LOW " + str(-highcurr) + ";"
        deltastr = ":SOUR:DELT:DEL " + str(delta) + ";"
        swpct1str = ":SOUR:DELT:COUN " + str(swpct1) + ";"
        swpct2str = ":SOUR:SWE:COUN " + str(swpct2) + ";"
        nplcstr = ":SYST:COMM:SER:SEND ':SENS1:VOLT:NPLC " + str(nplc) + "';"
        swpct3str = ":SYST:COMM:SER:SEND ':SENS1:VOLT:DFIL:COUN " + str(swpct3) + "';"
        rvngstr = ":SYST:COMM:SER:SEND ':SENS1:VOLT:RANG " + str(rvng) + "';"

    
        self.write(highcurrstr + lowcurrstr + deltastr + swpct1str + swpct2str + \
                   nplcstr + swpct3str + rvngstr)

        #print(highcurrstr + lowcurrstr + deltastr + swpct1str + swpct2str + \
        #           nplcstr + swpct3str + rvngstr)

        sleep(1.0)

        self.write("UNIT V")

        self.write(":TRAC:POIN " + str(measnum))

        self.write(":SOUR:DELT:ARM")

        print("Waveform Armed")



    def min_inloop_delta(self):

        self.write(":INIT:IMM")
        sleep(0.1)
        stop = False
        while stop == False:
            self.write("STAT:MEAS:EVEN?")
            measstr = self.read()
            #print(measstr)
            #print('Ask', self.ask("STAT:MEAS:EVEN?"))
            bools = int_to_bool_list(int(measstr))
            #print(bools)
            stop = bools[9]
            #print(stop)
            sleep(0.001)

        self.write(":TRAC:DATA:TYPE?")
        self.read()
        self.write(":TRAC:DATA?")
        # might need to wait here...
        measdata = self.read()

        res, resstd = meas_value(measdata)

        #print('Res', res, 'Ohms', resstd)

        #sleep(0.5)
        self.write(":TRAC:CLE")

        return res


    def turn_off(self):
        self.write("OUTP:STAT off")



    def AC_config(self, amplitude, frequency, offset):


        amplitudestr = ":SOUR:WAVE:AMPL " + str(amplitude) + ";"
        frequencystr = ":SOUR:WAVE:FREQ " + str(frequency) + ";"
        offsetstr = ":SOUR:WAVE:OFFS " + str(offset) + ";"
 

        #*RST; 
        to_send = "*RST; SOUR:CLE; :SOUR:WAVE:FUNC SIN; " + amplitudestr \
                + frequencystr + offsetstr + ":SOUR:WAVE:PMAR:OLIN 3;"\
                + ":SOUR:WAVE:RANG BEST"

        self.write(to_send)
        #self.write("SOUR:CLE; :SOUR:WAVE:FUNC SIN") 
        #self.write("SOUR:WAVE:FUNC SIN")


    def AC_arminit(self):

        self.write("SOUR:WAVE:ARM")
        self.write("SOUR:WAVE:INIT")
        sleep(6.0)
        print("Current wave on")


    def AC_abort(self):

        self.write("SOUR:WAVE:ABOR")
        print("Current wave off")


    def AC_phasemark_on(self):

        self.write("SOUR:WAVE:PMAR:STAT ON")
        print("AC phase mark on")


    def AC_phasemark_off(self):

        self.write("SOUR:WAVE:PMAR:STAT OFF")
        print("AC phase mark off")


    def current_wave_set(self, amplitude, frequency, offset, turnon, turnoff):

        if turnon == True:
            self.AC_config(amplitude, frequency, offset)
            self.AC_phasemark_on()
            self.AC_arminit()

        if turnoff == True:
            self.AC_abort()


    def current_sweep(self, maxI, numpoints, sweeptype):
        # This is based on 4-9 of the KE6221 user manual

        if sweeptype == 'linear':
            swp = 'LIN'
        if sweeptype == 'log':
            swp = 'LOG'
        if sweeptype == 'logarithmic':
            swp = 'LOG'

        # Set up instrument for sweeps
        self.write(*RST)
        self.write("SOUR:CURR 0.0") # Set current to zero
        self.write("SOUR:CURR:COMP 10") # Set compliance to 10V

        # Configure the sweep
        self.write("SOUR:SWE:SPAC "+swp) # linear or log
        self.write("SOUR:CURR:STAR 0.0")
        self.write("SOUR:CURR:STOP "+str(maxI))
        self.write("SOUR:CURR:STEP "+str(maxI/(numpoints/2.)))
        self.write("SOUR:DEL 0.005") # DELAY 
        self.write("SOUR:SWE:RANG BEST") # BEST FIXED SOURCE RANGE 
        self.write("SOUR:SWE:COUN 1") # set sweep count to 1
        self.write("SOUR:SWE:CAB OFF") # disable compliance abort
        
        # Arm sweep
        self.write("SOUR:SWE:ARM")


    def current_sweep_trig(self):

        self.write("INIT")


    def current_sweep_off(self):

        self.write("OUTP OFF")


    def current_sweep_inloop(self):

        stop = False
        while stop == False:
            self.write("STAT:MEAS:EVEN?")
            measstr = self.read()
            #print(measstr)
            #print('Ask', self.ask("STAT:MEAS:EVEN?"))
            bools = int_to_bool_list(int(measstr))
            #print(bools)
            stop = bools[9]
            #print(stop)
            sleep(0.001)

        self.write(":TRAC:DATA:TYPE?")
        self.read()
        self.write(":TRAC:DATA?")
        # might need to wait here...
        measdata = self.read()

        print('Print Measured data', measdata)

        res, resstd = meas_value(measdata)


        #print('Res', res, 'Ohms', resstd)

        #sleep(0.5)
        self.write(":TRAC:CLE")



class mySR830(SR830):

    def __init__(self, resourceName):

        self.setdic =  {'inputconfig':{"A": 0, "A-B":1, "1MOhm":2, "100MOhm":3},\
                        'shldgnd':{"Float":0, "Ground":1},\
                        'cplng':{"AC":0, "DC":1},\
                        'lnfltr':{"None":0, "1x Line":1, "2x Line":2, "Both":3},\
                        'sensty':{"2nV/fA":0, "5nV/fA":1, "10nV/fA":2, "20nV/fA":3, \
                                "50nV/fA":4, "100nV/fA":5, "200nV/fA":6, "500nV/fA":7, \
                                "1uV/pA":8, "2uV/pA":9, "5uV/pA":10, "10uV/pA":11, \
                                "20uV/pA":12, "50uV/pA":13, "100uV/pA":14, "200uV/pA":15, \
                                "500uV/pA":16, "1mV/nA":17, "2mV/nA":18, "5mV/nA":19, \
                                "10mV/nA":20, "20mV/nA":21, "50mV/nA":22, "100mV/nA":23, \
                                "200mV/nA":24, "5000mV/nA":25},\
                        'tmcnst':{"10us":0, "30us":1, "100us":2, "300us":3, "1ms":4, \
                                "3ms":5, "10ms":6, "30ms":7, "100ms":8, "300ms":9, \
                                "1s":10, "3s":11, "10s":12, "30s":13, "100s":14, \
                                "300s":15, "1ks":16, "3ks":17, "10ks":18, "30ks":19},\
                        'lpfltsp':{"6dB/oct":0, "12dB/oct":1, "18dB/oct":2, "24dB/oct":3},\
                        'ref':{"External":0, "Internal":1},\
                        }
        self.sensdic_inv = {v: k for k, v in self.setdic['sensty'].items()}
        super().__init__(resourceName)


  
    def config_params(self, inputconfig, shldgnd, cplng, lnfltr, sensty, tmcnst, \
                      lpfltsp, ref, harm, freq, offs):

       
        self.write("*RST")
        inputconfigstr = "ISRC " + str(self.setdic['inputconfig'][inputconfig])
        self.write(inputconfigstr)

        shldgndstr = "IGND " + str(self.setdic['shldgnd'][shldgnd])
        self.write(shldgndstr)

        cplngstr = "ICPL " + str(self.setdic['cplng'][cplng])
        self.write(cplngstr)

        lnfltrstr = "ILIN " + str(self.setdic['lnfltr'][lnfltr])
        self.write(lnfltrstr)

        freqstr = "FREQ " + str(freq)
        self.write(freqstr)

        refstr = "FMOD " + str(self.setdic['ref'][ref])
        self.write(refstr)

        harmstr = "HARM " + str(harm)
        self.write(harmstr)

        senstystr = "SENS " + str(self.setdic['sensty'][sensty])
        self.write(senstystr)

        tmcnststr = "OFLT " + str(self.setdic['tmcnst'][tmcnst])
        self.write(tmcnststr)

        lpfltspstr = "OFSL " + str(self.setdic['lpfltsp'][lpfltsp])
        self.write(lpfltspstr)
        
        self.write("RSLP 2")

        offsstr = "OEXP 1 " + str(offs)
        self.write(offsstr)
        offsstr = "OEXP 2 " + str(offs)
        self.write(offsstr)
        offsstr = "OEXP 3 " + str(offs)
        self.write(offsstr)

    
    def set_sensitivity(self, sensty):

        senstystr = "SENS " + str(self.setdic['sensty'][sensty])
        self.write(senstystr)


    def set_time_constant(self, tmcnst):

       tmcnststr = "OFLT " + str(self.setdic['tmcnst'][tmcnst])
       self.write(tmcnststr)

        
    def set_defaults(self):
        
        inputconfig = "A-B"
        shldgnd  = "Float"
        cplng = "AC"
        lnfltr = "Both"
        sensty = "5mV/nA" #"5mV/nA"  #"2mV/nA"
        tmcnst = "300ms"
        lpfltsp = "12dB/oct"
        ref = "External"
        harm = 1
        freq = 58.737e2
        offs = 0.0

        self.config_params(inputconfig, shldgnd, cplng, lnfltr, sensty, tmcnst, \
                      lpfltsp, ref, harm, freq, offs)


    def read_one(self):

        self.write("SNAP ? 1,2,3,4,9,10")
        measstr = self.read()

        numbers = [float(x) for x in measstr.split(",")]
        self.X = numbers[0]
        self.Y = numbers[1]
        self.R = numbers[2]
        self.Th = numbers[3]
        self.Fr = numbers[4]
        self.C1 = numbers[5]

        return numbers

    
    def query_ovld(self):

        self.write("LIAS? 0") # Input/reserve overload
        self.lia0 = int(self.read())
        self.write("LIAS? 2") # Output overload, used for sensitivity
        self.lia2 = int(self.read())
        self.write("LIAS? 3") # Reference unlocked
        self.lia3 = int(self.read())
       #print(response, type(response))

        return [self.lia0, self.lia2, self.lia3] 


    def find_sensitivity(self, init_guess):
        
        self.guess = init_guess

        done = True
        hasfail = True
        lastgood = True
        while (done or hasfail or lastgood):

            self.set_sensitivity(self.guess)
            print('Set Sensitivity')
            sleep(0.1)
        
            self.rs = []
            self.os = []
            for i in range(20):
                self.read_one()
                self.query_ovld()
                self.rs.append(self.R)
                self.os.append(self.lia2)

            if self.os[-1] == 0:
                #print('sense okay')
                print(st.stdev(self.rs)/st.mean(self.rs))
                new_guess_num = self.setdic['sensty'][self.guess] - 1
                #print(new_guess_num)
                self.guess = self.sensdic_inv[new_guess_num]       
                done = False
                lastgood = False
                #print('done is False')

            else:
                #print('sense too low')
                new_guess_num = self.setdic['sensty'][self.guess] + 1
                #print(new_guess_num)
                self.guess = self.sensdic_inv[new_guess_num]
                hasfail = False 
                lastgood = True
                #print('hasfail is False')


    def find_time_constant(self, init_guess):

        set_time_constant(init_guess)

            print('Set Time Constant')
            sleep(0.1) # set in accordance with 5* time constant
        
            self.rs = []
            self.os = []
            for i in range(20):
                self.read_one()
                self.query_ovld()
                self.rs.append(self.R)
                self.os.append(self.lia2)
 
            sd = st.stdev(rs)
            av = st.mean(rs)




    def read_2harm(self):

        print("Hi, this doesn't work now.")




def main():

    adapter = VISAAdapter("GPIB::12")
    KE6221 = myKeithley6221(adapter)
    #KE6221.arm_preloop_delta(1.e-6, 0.005, 10, 1, 10, 3, 10e-6, 10)
    #KE6221.min_inloop_delta()

    adapter2 = VISAAdapter("GPIB::8")
    LockIn = mySR830(adapter2)

    inputconfig = "A-B"
    shldgnd  = "Float"
    cplng = "AC"
    lnfltr = "Both"
    sensty = "5mV/nA" #"5mV/nA"  #"2mV/nA"
    tmcnst = "300ms"
    lpfltsp = "12dB/oct"
    ref = "External"
    harm = 1
    freq = 58.737e2
    offs = 0.0


    LockIn.write("*IDN?")
    ans = LockIn.read()
    print("Lock In id: ", ans)
    LockIn.config_params(inputconfig, shldgnd, cplng, lnfltr, sensty, tmcnst, \
                      lpfltsp, ref, harm, freq, offs)


    amplitude = 50.e-6 # Amps
    frequency = freq # Hz
    offset = 0.0 # in Amps
 
    amps = [0.71e-3] # [10.e-6, 20.e-6, 30.e-6, 
    volts = []
    phis = []
    for i in range(len(amps)):

        KE6221.AC_config(amps[i], frequency, offset)
        KE6221.AC_phasemark_on()
        KE6221.AC_arminit()
        string = LockIn.read_one()
        KE6221.AC_abort()

        volts.append(string[2]*np.sqrt(2))
        phis.append(string[3])

    print("Voltages: ", volts)
    print("Phases: ", phis)

    print(string, type(string[0]))
    print("Res ", string[2]/amps[-1]*np.sqrt(2), " Ohms")


#    KE6221.write(':OUTP:LTE OFF')
#    KE6221.write(':OUTP:LTE?')
#    ans = KE6221.read()
#    print(ans)



if __name__ == '__main__':
    main()
