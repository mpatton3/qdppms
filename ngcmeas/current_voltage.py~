# This script contains classes, function,s and code for setting
# a Keithley 6221 and 2182a current source voltmeter tandem for
# meaurement functionality.
# Specifically, we separate the arming from a 'do one measurement'
# to allow for easy in-loop measurement.


import numpy as np
import pandas as pd
import os
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


    def AC_abort(self):

        self.write("SOUR:WAVE:ABOR")


    def AC_phasemark_on(self):

        self.write("SOUR:WAVE:PMAR:STAT ON")
        print("AC phase mark on")


    def AC_phasemark_off(self):

        self.write("SOUR:WAVE:PMAR:STAT OFF")
        print("AC phase mark off")



class mySR830(SR830):
    
    def config_params(self, inputconfig, shldgnd, cplng, lnfltr, sensty, tmcnst, \
                      lpfltsp, ref, harm, freq, offs):

       
        self.write("*RST")
        setdic = {inputconfig:{"A": 0, "A-B":1, "1MOhm":2, "100MOhm":3},\
                  shldgnd:{"Float":0, "Ground":1},\
                  cplng:{"AC":0, "DC":1},\
                  lnfltr:{"None":0, "1x Line":1, "2x Line":2, "Both":3},\
                  sensty:{"2nV/fA":0, "5nV/fA":1, "10nV/fA":2, "20nV/fA":3, \
                          "50nV/fA":4, "100nV/fA":5, "200nV/fA":6, "500nV/fA":7, \
                          "1uV/pA":8, "2uV/pA":9, "5uV/pA":10, "10uV/pA":11, \
                          "20uV/pA":12, "50uV/pA":13, "100uV/pA":14, "200uV/pA":15, \
                          "500uV/pA":16, "1mV/nA":17, "2mV/nA":18, "5mV/nA":19, \
                          "10mV/nA":20, "20mV/nA":21, "50mV/nA":22, "100mV/nA":23, \
                          "200mV/nA":24, "5000mV/nA":25},\
                  tmcnst:{"10us":0, "30us":1, "100us":2, "300us":3, "1ms":4, \
                          "3ms":5, "10ms":6, "30ms":7, "100ms":8, "300ms":9, \
                          "1s":10, "3s":11, "10s":12, "30s":13, "100s":14, \
                          "300s":15, "1ks":16, "3ks":17, "10ks":18, "30ks":19},\
                  lpfltsp:{"6dB/oct":0, "12dB/oct":1, "18dB/oct":2, "24dB/oct":3},\
                  ref:{"External":0, "Internal":1},\
                  }

        inputconfigstr = "ISRC " + str(setdic[inputconfig][inputconfig])
        self.write(inputconfigstr)

        shldgndstr = "IGND " + str(setdic[shldgnd][shldgnd])
        self.write(shldgndstr)

        cplngstr = "ICPL " + str(setdic[cplng][cplng])
        self.write(cplngstr)

        lnfltrstr = "ILIN " + str(setdic[lnfltr][lnfltr])
        self.write(lnfltrstr)

        freqstr = "FREQ " + str(freq)
        self.write(freqstr)

        refstr = "FMOD " + str(setdic[ref][ref])
        self.write(refstr)

        harmstr = "HARM " + str(harm)
        self.write(harmstr)

        senstystr = "SENS " + str(setdic[sensty][sensty])
        self.write(senstystr)

        tmcnststr = "OFLT " + str(setdic[tmcnst][tmcnst])
        self.write(tmcnststr)

        lpfltspstr = "OFSL " + str(setdic[lpfltsp][lpfltsp])
        self.write(lpfltspstr)
        
        self.write("RSLP 2")

        offsstr = "OEXP 1 " + str(offs)
        self.write(offsstr)
        offsstr = "OEXP 2 " + str(offs)
        self.write(offsstr)
        offsstr = "OEXP 3 " + str(offs)
        self.write(offsstr)

    
    def set_sensitivity(self, sensty):

        senstystr = "SENS " + str(setdic[sensty][sensty])
        self.write(senstystr)

        
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



    def read_2harm(self):

        print("Hi")




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
