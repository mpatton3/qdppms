# This script contains classes, function,s and code for setting
# a Keithley 6221 and 2182a current source voltmeter tandem for
# meaurement functionality.
# Specifically, we separate the arming from a 'do one measurement'
# to allow for easy in-loop measurement.

# Search for 'FORM:ELEM' and check the correct one is chosen.


import numpy as np
import pandas as pd
import os
import statistics as st
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter
from time import sleep, time
from pymeasure.instruments.keithley import Keithley6221
from pymeasure.instruments.srs import SR830


def int_to_bool_list(num):

    bin_string = format(num, '015b')
    return [x == '1' for x in bin_string[::-1]]


def meas_value(measstr):

    numbers = [float(x) for x in measstr.split(",")]

    inds = np.arange(len(numbers)/2)*2

    print(min(numbers))
    mn = np.mean(numbers[::2])
    std = np.std(numbers[::2])

    return mn, std


def iv_meas_parse(measstr):

    print('In IV_parse')
    # Split and strip the string from the 6221 into floats.
    numbers = [float(x.rstrip('ADC VDC SECS \n')) for x in measstr.split(",")]
    num = len(numbers)
    points = int(num/3) 

    volt_ind = np.arange(num/3, dtype=int)*3
    time_ind = np.arange(num/3, dtype=int)*3+1
    curr_ind = np.arange(num/3, dtype=int)*3+2
    print('split big string')
 

    #print(numbers[1])
    #print(numbers[(1,2,3)])
    #print(numbers[np.arange(3)])
    # Put each measurement type into its own array.
    volt = [numbers[volt_ind[i]] for i in range(points)]
    time = [numbers[time_ind[i]] for i in range(points)]
    curr = [numbers[curr_ind[i]] for i in range(points)]

    print('Big string split')

    #print(volt)
    #print(time)
    #print(curr)

    return time, curr, volt


def dc_meas_parse(measstr):

    # Split and strip the string from the 6221 into floats.
    numbers = [float(x.rstrip('ADC VDC SECS \n')) for x in measstr.split(",")]
    num = len(numbers)
    points = int(num/3) 

    volt_ind = np.arange(num/3, dtype=int)*3
    time_ind = np.arange(num/3, dtype=int)*3+1
    curr_ind = np.arange(num/3, dtype=int)*3+2


    #print(numbers[1])
    #print(numbers[(1,2,3)])
    #print(numbers[np.arange(3)])
    # Put each measurement type into its own array.
    volt = [numbers[volt_ind[i]] for i in range(points)]
    time = [numbers[time_ind[i]] for i in range(points)]
    curr = [numbers[curr_ind[i]] for i in range(points)]

    #print(volt)
    #print(time)
    #print(curr)

    return time, curr, volt



class myKeithley6221(Keithley6221):

    def arm_delta(self, highcurr, lowcurr, delta, swpct1, swpct2, swpct3, \
                          nplc, rvng, measnum):

        print('in arm delta')
        self.reset()

        self.write(":TRAC:CLE; :TRAC:FEED SENS1; :TRAC:FEED:CONT NEXT;")

        highcurrstr = ":SOUR:DELT:HIGH " + str(highcurr) + ";"
        lowcurrstr = ":SOUR:DELT:LOW " + str(lowcurr) + ";"
        deltastr = ":SOUR:DELT:DEL " + str(delta) + ";"
        swpct1str = ":SOUR:DELT:COUN " + str(swpct1) + ";"
        swpct2str = ":SOUR:SWE:COUN " + str(swpct2) + ";"
        nplcstr = "SYST:COMM:SER:SEND ':SENS1:VOLT:NPLC " + str(nplc) + "';"
        swpct3str = ":SYST:COMM:SER:SEND ':SENS1:VOLT:DFIL:COUN " + str(swpct3) + "';"
        rvngstr = ":SYST:COMM:SER:SEND ':SENS1:VOLT:RANG " + str(rvng) + "';"
        #rvngstr = ":SYST:COMM:SER:SEND ':SENS1:VOLT:RANG " + 'AUTO' + "';"


    
        self.write(highcurrstr + lowcurrstr + deltastr + swpct1str + swpct2str + \
                   swpct3str + rvngstr)
                   #nplcstr + swpct3str + rvngstr)


        #print(highcurrstr + lowcurrstr + deltastr + swpct1str + swpct2str + \
        #           nplcstr + swpct3str + rvngstr)

        sleep(1.0)

        #print('post settings', self.ask("SYST:ERR?"))


        self.write("UNIT V")

        #self.write("FORM:ELEM DEF") # return just reading and time stamp
        self.write("FORM:ELEM READ,TST,UNIT,SOUR") # return all elments from list


        self.write(":TRAC:POIN " + str(measnum))


        self.write(":SOUR:DELT:ARM")

        #print('post arming', self.ask("SYST:ERR?"))

        print("Waveform Armed")


    def arm_preloop_delta(self, highcurr, delta, swpct1, swpct2, swpct3, \
                          nplc, rvng, measnum):


        self.arm_delta(highcurr, -highcurr, delta, swpct1, swpct2, swpct3, \
                          nplc, rvng, measnum)



    def min_inloop_delta(self):

        self.write(":INIT:IMM")
        sleep(0.5)
        stop = False
        print('postinit', self.ask("SYST:ERR?"))

        while stop == False:
            self.write("STAT:MEAS:EVEN?")
            measstr = self.read()
            #print('sent and read measurement event')
            #print(measstr)
            #print('Ask', self.ask("STAT:MEAS:EVEN?"))
            bools = int_to_bool_list(int(measstr))
            #print(bools)
            stop = bools[9]
            #print(stop)
            sleep(0.9)

        self.write(":TRAC:DATA:TYPE?")
        self.read()
        self.write(":TRAC:DATA?")
        # might need to wait here...
        measdata = self.read()

        #print(measdata)
        volt, voltstd = meas_value(measdata)

        #print('Res', res, 'Ohms', resstd)

        #sleep(0.5)
        self.write(":TRAC:CLE")

        #print('made it herer!', volt, voltstd)
        return volt, voltstd


    def inloop_delta(self):

        self.write(":INIT:IMM")
        sleep(0.5)
        stop = False
        print('postinit', self.ask("SYST:ERR?"))

        while stop == False:
            self.write("STAT:MEAS:EVEN?")
            measstr = self.read()
            #print('sent and read measurement event')
            #print(measstr)
            #print('Ask', self.ask("STAT:MEAS:EVEN?"))
            bools = int_to_bool_list(int(measstr))
            #print(bools)
            stop = bools[9]
            #print(stop)
            sleep(0.2)

        self.write(":TRAC:DATA:TYPE?")
        self.read()
        self.write(":TRAC:DATA?")
        # might need to wait here...
        measdata = self.read()

        #volt, voltstd = meas_value(measdata)
        print('read data')
        self.time, self.curr, self.volt = iv_meas_parse(measdata)

        volt = np.mean(self.volt[-30:])
        voltstd = np.std(self.volt[-30:])

        #print('Res', res, 'Ohms', resstd)

        #sleep(0.5)
        self.write(":TRAC:CLE")

        return volt, voltstd


    def write_delta_file(self, temp, field, maxI):

        num = 0
        found_name = False
        while found_name == False:
            filename = 'IV_sweep_' + "{:.2f}".format(temp) + 'K_' + \
                       "{:.0f}".format(round(field/10.)*10) + 'Oe_' + \
                       "{:.2f}".format(maxI*10**6) + 'uA_' + \
                       sweeptype + '_'+str(num) + '.txt'

            if os.path.isfile(filename):
                num += 1
            else:
                found_name = True
    

        data = pd.DataFrame({'Time': pd.Series(self.time), \
                             'Current': pd.Series(self.curr), \
                             'Voltage': pd.Series(self.volt)})                               

        data = data[['Time', 'Current', 'Voltage']]

        data.to_csv(filename, sep = '\t', index=False)
        print('IV file written')



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


    def current_sweep_setup(self, maxI, numpoints, sweeptype, delay, nplc,
                            pulse_width):
        # This is based on 4-9 of the KE6221 user manual, 
        # and pulsed delta section

        if sweeptype == 'lin':
            swp = 'LIN'
        if sweeptype == 'linear':
            swp = 'LIN'
        if sweeptype == 'log':
            swp = 'LOG'
        if sweeptype == 'logarithmic':
            swp = 'LOG'
        if sweeptype == 'list':
            swp = 'LIST'
            crntup = np.linspace(-maxI, maxI, numpoints)
            crntdn = np.linspace(maxI, -maxI, numpoints)
            crnts = np.concatenate((crntup, crntdn))
            dly = np.array([delay]*len(crnts))
            tot_pts = len(crnts)
            num_sends = int(tot_pts/90.) + (tot_pts % 90 > 0)

            #crntlist = str(crnts).replace('[', '').replace(']', '').replace('  ', ',').lstrip(',')
            crntlist = []
            delaylist = []
            for n in range(num_sends):
                crntlist.append(','.join([str(x) for x in crnts[n*90:(n+1)*90]]))

                delaylist.append(','.join([str(x) for x in dly[n*90:(n+1)*90]]))


            #print('currents are', crntlist)
            #print('delays are', delaylist)



        # Set up instrument for sweeps
        self.write("*RST")
        self.write("SOUR:CURR 0.0") # Set current to zero
        self.write("SOUR:CURR:COMP 10") # Set compliance to 10V


        #self.write("SOUR:PDEL:HIGH 5.e-6")
        self.write("SOUR:PDEL:LOW 0")
        self.write("SOUR:PDEL:WIDT "+str(pulse_width))

        self.write("syst:err?")
        print(self.read())
        #self.write("SOUR:PDEL:SDEL 100E-6")
        self.write("SOUR:PDEL:COUN 1")
        #self.write("SOUR:PDEL:RANG BEST")
        #self.write("SOUR:PDEL:INT 5")
        self.write("SOUR:PDEL:SWE ON")
        self.write("SOUR:PDEL:LME 2")

        # Configure the sweep
        self.write("SOUR:SWE:SPAC "+swp) # linear or log or list
        if sweeptype == 'list':
            print('in second sweep type list')
            #crntlist = "0.001, 0.002, 0.003, 0.004, 0.003, 0.002, 0.001, 0.00"
            self.write("SOUR:LIST:CURR "+crntlist[0]) #Only loads up to 100 at a time

            for n in range(num_sends-1):
                self.write("SOUR:LIST:CURR:APP "+crntlist[n+1])

            self.write("SOUR:LIST:DEL "+delaylist[0]) # DELAY 

            for n in range(num_sends-1):
                self.write("SOUR:LIST:DEL:APP "+delaylist[n+1]) # DELAY 

            self.write("SOUR:LIST:CURR:POIN?")
            response = self.read()

            print('Num I pts is ', response)
 
        else:
            self.write("SOUR:CURR:STAR "+str(-maxI))
            self.write("SOUR:CURR:STOP "+str(maxI))
            self.write("SOUR:CURR:STEP "+str(maxI/(numpoints-1.)))
            print("SOUR:CURR:STEP "+str(maxI/(numpoints-1.)))

            self.write("SOUR:DEL "+str(delay)) # DELAY 
        self.write("SOUR:SWE:RANG BEST") # BEST FIXED SOURCE RANGE 
        self.write("SOUR:SWE:COUN 1") # set sweep count to 1
        self.write("SOUR:SWE:CAB OFF") # disable compliance abort

        self.write("UNIT V")
        self.write("FORM:ELEM READ,TST,UNIT,SOUR")
        self.write("TRAC:CLE") 
        # Read the Operations Event Register to clear it before starting.
        self.write("STAT:OPER:EVEN?")
        measstr = self.read()
        self.write("SOUR:PDEL:ARM") # Arming sets buffer to sweep size.
        sleep(1.5)


    def current_sweep_trig(self):
        # This is more efficiently done in the current_sweep_inloop() method.
        
        # Read buffer to clear it
        self.write("STAT:OPER:EVEN?")
        measstr = self.read()
 
        self.write("INIT")


    def current_sweep_off(self):

        self.write("OUTP OFF")


    def current_sweep_inloop(self):

        self.write("INIT:IMM")
        print('PDEL initiated')
        stop = False

        print('Going into meas loop')
        num = 0
        while stop == False:
            self.write("STAT:OPER:EVEN?")
            measstr = self.read()
            bools = int_to_bool_list(int(measstr))
            stop = bools[1] # sense the bit the tells 'sweep done'
            sleep(0.15)
            num += 1


        self.write("TRAC:DATA?")
        # Don't need to wait here...
        measdata = self.read()

        #print('Print Measured data', measdata)

        self.time, self.curr, self.volt = iv_meas_parse(measdata)

        #sleep(0.5)
        self.write(":TRAC:CLE")


    def IV_compute_res(self):

        # Compute resistance from IV curve
        num = len(self.curr)
        numin = int(num/6.)
        
        #print(self.volt)
        p = np.polyfit(self.curr, self.volt, deg=1)

        # Check IV curve for nonlinearity by comparing low-values fit
        # to fit for all data.
        pin = np.polyfit(self.curr[2*numin:4*numin], \
                         self.volt[2*numin:4*numin], deg=1)

        if p[0] > 1.1*pin[0] or p[0] < 0.9*pin[0]:
            print('NonLinear IV')
            nonlin = True
        else:
            nonlin = False
        
        return p[0], nonlin

    
    def write_IV_file(self, temp, field, maxI, angle, sweeptype):

        
        num = 0 # change back to zero
        found_name = False
        while found_name == False:
            filename = 'IV_sweep_' + "{:.0f}".format(temp) + 'K_' + \
                       "{:.0f}".format(round(field)) + 'Oe_' + \
                       "{:.2f}".format(maxI*10**6) + 'uA_' + \
                       "{:.0f}".format(angle) + 'deg_' + \
                       sweeptype + '_'+str(num) + '.txt'

            if os.path.isfile(filename):
                num += 1
            else:
                found_name = True
    
        data = pd.DataFrame({'Time': pd.Series(self.time), \
                             'Current': pd.Series(self.curr), \
                             'Voltage': pd.Series(self.volt)})                               

        data = data[['Time', 'Current', 'Voltage']]

        data.to_csv(filename, sep = '\t', index=False)
        print('IV file written')


    def differential_cond_setup(self, start_I, stop_I, step_I, delta_I, delay, nplc):
        # This is based on 5-62 of the KE6221 user manual, 
        # the differential conductance section.

        # Set up instrument for sweeps
        self.write("*RST")
        self.write("SOUR:CURR 0.0") # Set current to zero
        self.write("SOUR:CURR:COMP 10") # Set compliance to 10V


        self.write("SOUR:DCON:STAR "+str(start_I))
        self.write("SOUR:DCON:STOP "+str(stop_I))
        self.write("SOUR:DCON:STEP "+str(step_I))
        self.write("SOUR:DCON:DELT "+str(delta_I))
        self.write("SOUR:DCON:DEL "+str(delay))
        self.write("SOUR:DCON:CAB OFF") # disable compliance abort


        self.write("syst:err?")
        print(self.read())

        self.write("UNIT V")
        self.write("FORM:ELEM READ,TST,UNIT,SOUR")
        #self.write("FORM:ELEM all")
        self.write("TRAC:CLE") 
        # Read the Operations Event Register to clear it before starting.
        self.write("STAT:OPER:EVEN?")
        measstr = self.read()
        print('Oper Event reg ', measstr)
        self.write("SOUR:DCON:ARM") # Arming sets buffer to sweep size.
        sleep(1.5)
        self.write("syst:err?")
        print('After arming ', self.read())



    def differential_cond_inloop(self):

        self.write("INIT:IMM")
        print('DCON initiated')
        stop = False

        sleep(0.5) # Important for this to be here, and at least 0.5s long

        self.write("syst:err?")
        print('After init', self.read())


        print('Going into meas loop')
        num = 0
        while stop == False:

            self.write("STAT:OPER:EVEN?")

            measstr = self.read()

            bools = int_to_bool_list(int(measstr))
            stop = bools[1] # sense the bit the tells 'sweep done'
            sleep(0.15)
            num += 1


        self.write("TRAC:DATA?")
        # Don't need to wait here...
        measdata = self.read()

        print('Print Measured data', measdata)

        self.time, self.curr, self.volt = iv_meas_parse(measdata)

        #sleep(0.5)
        self.write(":TRAC:CLE")


    def write_DC_file(self, temp, field, maxI, sweeptype):

        num = 0
        found_name = False
        while found_name == False:
            filename = 'IV_sweep_' + "{:.2f}".format(temp) + 'K_' + \
                       "{:.0f}".format(field) + 'Oe_' + \
                       "{:.2f}".format(maxI*10**6) + 'uA_' + \
                       sweeptype + '_'+str(num) + '.txt'

            if os.path.isfile(filename):
                num += 1
            else:
                found_name = True
    

        data = pd.DataFrame({'Time': pd.Series(self.time), \
                             'Current': pd.Series(self.curr), \
                             'Voltage': pd.Series(self.volt)})                               

        data = data[['Time', 'Current', 'Voltage']]

        data.to_csv(filename, sep = '\t', index=False)
        print('IV file written')

    def send_pulse(self, pulse_current, pulse_length):

        source_str = "SOUR:CURR "+str(pulse_current)
        self.write("SOUR:CURR:RANG 0.1")#+str(pulse_current))
        self.write(source_str)
        self.write("CURR:COMP 15")
        self.write("SYST:ERR?")
        sleep(0.1)
        resp = self.read()
        print("Switch Pulse", resp)
        print(source_str)
        sleep(0.05)

        self.write("OUTP ON")
        sleep(pulse_length)
        self.write("OUTP OFF")

    def start_current(self, current):

        self.write("OUTP OFF")
        sleep(0.2)

        source_str = "SOUR:CURR "+str(pulse_current)
        self.write("SOUR:CURR:RANG 0.1")#+str(pulse_current))
        self.write(source_str)
        self.write("CURR:COMP 15")
        self.write("SYST:ERR?")
        sleep(0.1)
        resp = self.read()
        print("Switch Pulse", resp)
        print(source_str)
        sleep(0.05)

        self.write("OUTP ON")
 
    def meas_pulse(self, meas_current, num, keep_output=True):


        self.write("SOUR:CURR:RANG 0.01") #+str(meas_current))
        self.write("SOUR:CURR "+str(meas_current))
        self.write("SOUR:CURR:COMP 15")
        sleep(0.05)
        self.write("SYST:ERR?")
        sleep(0.1)
        resp = self.read()
        print("Meas Pulse", resp)
 
        if keep_output:
            self.write("OUTP ON")
            sleep(0.3)
            print("Meas current on")

        # This syntax is from 6221 ref p. 5-29
        vs = []
        for i in range(num):

            self.write("SYST:COMM:SER:SEND '*CLS'")
            self.write("SYST:COMM:SER:SEND 'TRAC:CLE'")
            self.write("SYST:COMM:SER:SEND 'FORM:ELEM READ,UNIT'")
            self.write("SYST:COMM:SER:SEND 'SAMP:COUN 1'")
  
            self.write("SYST:COMM:SER:SEND 'SENS:FUNC VOLT'")
            self.write("SYST:COMM:SER:SEND 'SENS:DATA:FRES?'")
            print("Successful write again")
            sleep(0.50)
            self.write("SYST:COMM:SER:ENT?")
            sleep(0.1)
            resp = self.read()
            print('original', resp)
            resp = resp.strip().rstrip("VDC")
            print('stripped', resp)
            resp = float(resp)
            #print('floating', resp)
            sleep(0.03)
            #print(resp)
            vs.append(resp)
        print("out of loop")
        #vs = np.asarray(vs)
        #print("cast as array")
        print(vs)
        voltage = np.median(vs)
        print("computed median", voltage)

        if keep_output:
            self.write("OUTP OFF")

        return voltage


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
        self.sensty_inv = {v: k for k, v in self.setdic['sensty'].items()}
        self.inputconfig_inv = {v: k for k, v in self.setdic['inputconfig'].items()}
        self.tmcnst_inv = {v: k for k, v in self.setdic['tmcnst'].items()}
        self.lpfltsp_inv = {v: k for k, v in self.setdic['lpfltsp'].items()}
        self.ref_inv = {v: k for k, v in self.setdic['ref'].items()}
        self.shldgnd_inv = {v: k for k, v in self.setdic['shldgnd'].items()}
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


    def get_params(self):

        self.write("ISRC?")
        value = int(self.read())
        self.inputconfig = self.inputconfig_inv[value]

        self.write("IGND?")
        value = int(self.read())
        self.shieldground = self.shldgnd_inv[value]

        self.write("FMOD?")
        value = int(self.read())
        self.ref = self.ref_inv[value]

        self.write("SENS?")
        value = int(self.read())
        self.sensty = self.sensty_inv[value]

        self.write("OFLT?")
        value = int(self.read())
        self.tmcnst = self.tmcnst_inv[value]
        
        self.write("OFSL?")
        value = int(self.read())
        self.lpfltsp = self.lpfltsp_inv[value]



    
    def set_sensitivity(self, sensty):

        senstystr = "SENS " + str(self.setdic['sensty'][sensty])
        self.write(senstystr)


    def set_time_constant(self, tmcnst):

        tmcnststr = "OFLT " + str(self.setdic['tmcnst'][tmcnst])
        self.write(tmcnststr)


    def set_harmonic(self, harm):

        harmstr ="HARM " + str(harm)
        self.write(harmstr)

       
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
                self.guess = self.sensty_inv[new_guess_num]       
                done = False
                lastgood = False
                #print('done is False')

            else:
                #print('sense too low')
                new_guess_num = self.setdic['sensty'][self.guess] + 1
                #print(new_guess_num)
                self.guess = self.sensty_inv[new_guess_num]
                hasfail = False 
                lastgood = True
                #print('hasfail is False')


    def find_time_constant(self, init_guess):

        self.set_time_constant(init_guess)

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

    #KE6221.arm_delta(1.e-3, 0.e-3, 1.e-3, 10, 1, 10, 4, 10, 10)

    '''
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
    '''


#    KE6221.write(':OUTP:LTE OFF')
#    KE6221.write(':OUTP:LTE?')
#    ans = KE6221.read()
#    print(ans)



if __name__ == '__main__':
    main()
