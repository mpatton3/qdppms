# This script runs a Hall sweep using a QD Dynacool PPMS cryostat
# and Keithley electronics. The Keithleys are controlled directly,
# while the cryostat is controlled through MultiVu via QD scripts
# in the PythonControl library.


import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import os
from time import sleep, time
from datetime import datetime
from pymeasure.display import plotter
from pymeasure.adapters import VISAAdapter
from pymeasure.experiment import Procedure, Results, Worker
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
import ngcmeas.current_voltage as cv
import ngcmeas.switch_matrix as sm
import MultiVu_talk_ngc as mv
from PythonControl.parse_inputs import inputs



class HallSweep(Procedure):

    def __init__(self, host, port, maxb, ramprate):
        self.host = host
        self.port = port
        self.maxb = maxb
        self.ramprate = ramprate
        super().__init__()

    iterations = IntegerParameter('Measurement Number')
    high_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delta = FloatParameter('Delta', units='s', default=1.e-3)
    swpct1 = IntegerParameter('Sweep Count 1', default=10)
    swpct2 = IntegerParameter('Sweep Count 2', default=1)
    swpct3 = IntegerParameter('Sweep Count 3', default=10)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    rvng = FloatParameter('Voltmeter Range', default=1.e-5)
    date = Parameter('Date Time', default='')

    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
    #                'R vdp 2', 'R Hall 1', 'R Hall 2']

    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1', \
    #              'R bridge 2', 'R bridge 3', 'R bridge 4']

    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1']


    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
    #                'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
    #                'R vdp 22', 'R Hall 12', 'R Hall 22']


    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1', \
                    'R bridge 2']


    def resistance_measure(self, config):

        print('in resistance_measure', config)
        if config == 'vdp1':
            self.switch.clos_vdp1()
        if config == 'vdp2':
            self.switch.clos_vdp2()
        if config == 'Hall1':
            self.switch.clos_Hall1()
        if config == 'Hall2':
            self.switch.clos_Hall2()
        if config == 'vdp12':
            self.switch.clos_vdp12()
        if config == 'vdp22':
            self.switch.clos_vdp22()
        if config == 'Hall12':
            self.switch.clos_Hall12()
        if config == 'Hall22':
            self.switch.clos_Hall22()
        if config == 'c1':
            self.switch.clos_custom1()
        if config == 'c2':
            self.switch.clos_custom2()
        if config == 'cust1':
            self.switch.clos_custom(5, 1, 4, 8) #5, 1, 6, 2
        if config == 'cust2':
            self.switch.clos_custom(5, 1, 4, 3)
        if config == 'cust3':
            self.switch.clos_custom(5, 2, 6, 1) #5, 1, 6, 2
        if config == 'cust4':
            self.switch.clos_custom(5, 2, 1, 4)

        sleep(0.36)

        volt, vstd = self.currentsource.min_inloop_delta()
        self.switch.open_all()
        return volt/self.high_current




    def startup(self):
        print('Starting Up')
        KE6221adapter = VISAAdapter("GPIB0::12")
        KE7001adapter = VISAAdapter("GPIB0::7")
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.switch = sm.Keithley7001(KE7001adapter, "SwitchMatrix")
        print('instruments mapped')
        self.currentsource.reset()
        self.currentsource.arm_preloop_delta(self.high_current, self.delta, self.swpct1, \
                                             self.swpct2, self.swpct3, self.nplc, self.rvng, \
                                             self.swpct1)
        #self.currentsource.arm_preloop_delta(self.high_current, delta, swpct1, \
        #                                     swpct2, swpct3, npld, rvng, \
        #                                     swpct1)

        self.currentsource.write("FORM:ELEM DEF")
        print('Done Startup')


        sleep(0.1)

    def in_loop(self, configs):

        ress = []
        # get_temp and get_field from Dynacool
        temp = mv.query_temp(self.host, self.port)[0]
        bfield = mv.query_field(self.host, self.port)
        print(bfield)
        tim = time() - self.starttime

        #print('Temp ', temp, 'Field ', bfield)


        # This is where comment starts for bridges
        '''
        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
            '\g(m)\-(0)H': bfield[0], \
            'R vdp 1': ress[0], \
            'R vdp 2': ress[1], \
            'R Hall 1': ress[2], \
            'R Hall 2': ress[3], \
            'R vdp 12': ress[4], \
            'R vdp 22': ress[5], \
            'R Hall 12': ress[6], \
            'R Hall 22': ress[7] \
            })
        sleep(0.01)
        # comment out last 4 in emit for 1 vdp

        '''

        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
            '\g(m)\-(0)H': bfield[0], \
            #'\g(phi)': self.angle,\
            'R bridge 1': ress[0], \
            'R bridge 2': ress[1]
            #'R bridge 3': ress[2],\
            #'R bridge 4': ress[3]
            })
        sleep(0.01)

        
        # Comment with 3 commas above for other config

        print('done emitting')

        return bfield


    def execute(self):

        #self.maxb = 100000.
        self.switch.set_pins(3,1,2,4) #1,3,4,2
        print('set some pins')
        rate = self.ramprate
        self.switch.set_pins2(7,5,6,8)
        print('set all pins')
        #configs = ['vdp1', 'vdp2', 'Hall1', 'Hall2', 'vdp12', 'vdp22', 'Hall12', 'Hall22']
        #configs = ['c1', 'c2']
        configs = ['cust1', 'cust2']#, 'cust3', 'cust4']

        ress = []
        ts = []
        bs = []
        self.starttime = time()

        self.stable_field = r'"Holding (Driven)"'

        #for i in range(self.iterations):

        mv.set_field(self.host, self.port, self.maxb, rate)
        sleep(1.8)
        bfld = 0.
        done = False
        print('about to measure')
        #while bfld < 0.999*self.maxb:
        while not done:

            print('Doing done loop in Hall')
            bfield = self.in_loop(configs)
            print("bfield here ", bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field

            print('Result ', bfield[1], done)

        mv.set_field(self.host, self.port, -self.maxb, rate)
        sleep(1.8)

        done = False

        while not done:

            bfield = self.in_loop(configs)
            print(bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field

            print(bfield[1], done)


        print('About to set field to zero.')
        mv.set_field(self.host, self.port, 0.0, rate)
        sleep(1.8)

        done = False

        while not done:

            print('In last leg of sweep.')
            bfield = self.in_loop(configs)
            print(bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field

            print(bfield[1], done)


            '''
            # get_temp and get_field from Dynacool
            temp = mv.query_temp(self.host, self.port)
            bfield = mv.query_field(self.host, self.port)
            tim = time() - starttime

            #print('Temp ', temp, 'Field ', bfield)

            for c in configs:

                ress.append(self.resistance_measure(c))
                #print(ress)

            print('about to emit', tim)

            self.emit('results', {
                'Time': tim, \
                'Temperature': temp, \
                '\g(m)\-(0)H': bfield, \
                'R vdp 1': ress[0], \
                'R vdp 2': ress[1], \
                'R Hall 1': ress[2], \
                'R Hall 2': ress[3], \
                })
            sleep(0.01)
            print('done emitting')

            '''
            #This is where the comment goes for bridges

        #Turn off Current
        self.currentsource.waveform_abort()

            #if self.should_stop():
            #    break


def field_ramp(host, port, maxb):

    flds = []

    mv.set_field(host, port, maxb, 600.)
    sleep(0.48)

    fld = 0.
    while fld < 0.99999*maxb:
        fld = mv.query_field(host, port)
        print(fld)
        flds.append(fld)
        sleep(1.0)


    mv.set_field(host, port, -1*maxb, 600.)
    sleep(0.48)

    while fld > -0.99999*maxb:
        fld = mv.query_field(host, port)
        print(fld)
        flds.append(fld)
        sleep(1.0)


    mv.set_field(host, port, 0., 600.)
    sleep(0.48)

    while fld < -0.10:
        fld = mv.query_field(host, port)
        print(fld)
        flds.append(fld)
        sleep(1.0)

    return flds



def main():

    host = "128.104.184.130"
    port = 5000

    #print('about to set field')
    #flds = field_ramp(host, port, 2000.)
    #print('field set')

    #plt.plot(flds)
    #plt.show()


    #start editing
    directory = (r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B028'
                 r'\dev10.8\220919')
    os.chdir(directory)
    data_filename = 'rho_v_B_300uA_300K_2.0T_00deg_B028_0.csv'


    setpoint = 20000 # max B in Oe
    ramprate = 30   # field ramp in Oe/sec
    procedure = HallSweep(host, port, setpoint, ramprate)

    procedure.iterations = 1
    procedure.high_current = 300.0e-6 # Amps
    # Stop editing
    procedure.delta = 1.e-3
    procedure.swpct1 = 10
    procedure.swpct2 = 1
    procedure.swpct3 = 10
    procedure.nplc = 3
    procedure.rvng = 1.e1
    now = datetime.now()
    #procedure.date = now.strftime("%m/%d/%Y, %H:%M:%s")

    #print('Params: ', procedure.parameter_objects())
    #procedure.startup()
    #procedure.execute()
    #hs = HallSweep(host, port)
    #hs.startup()
    #print('Hall sweep started up')


    #'''

    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Hall Sweep')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min

    #'''




if __name__ == '__main__':
    main()
