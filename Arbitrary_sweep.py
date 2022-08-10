# This script runs a Hall sweep using a QD Dynacool PPMS cryostat
# and Keithley electronics. The Keithleys are controlled directly,
# while the cryostat is controlled through MultiVu via QD scripts
# in the PythonControl library.


import numpy as np
import pandas as pd
import logging
#import matplotlib.pyplot as plt
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


import sys
import tempfile
import os
from time import sleep, time
from datetime import datetime
from pymeasure.log import console_log
from pymeasure.display.Qt import QtGui
#from PyQt5.QtWidgets import QApplication
from pymeasure.display.windows import ManagedWindow
from pymeasure.display import Plotter
from pymeasure.adapters import VISAAdapter
from pymeasure.experiment import Procedure, Results, Worker
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
from pymeasure.experiment.results import unique_filename
import ngcmeas.current_voltage as cv
import ngcmeas.switch_matrix as sm
import MultiVu_talk_ngc as mv
from PythonControl.parse_inputs import inputs

host = "128.104.184.130"
port = 5000


class TransportMeas(Procedure):

    #def __init__(self):
        #self.host = host
        #self.port = port
        #self.meastype = meastype
        #self.tempset = tempset
        #self.maxb = maxb
        #super().__init__()

    iterations = IntegerParameter('Measurement Number', default=1)
    high_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delta = FloatParameter('Delta', units='s', default=1.e-3)
    swpct1 = IntegerParameter('Sweep Count 1', default=10)
    swpct2 = IntegerParameter('Sweep Count 2', default=1)
    swpct3 = IntegerParameter('Sweep Count 3', default=10)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    rvng = FloatParameter('Voltmeter Range', units='V', default=1.e-5)
    date = Parameter('Date Time', default='now')
    meastype = Parameter('Measurement Type', default='Temp')
    tempset = FloatParameter('Temperature Set Point', units='K', default=300.)
    tempramp = FloatParameter('Temperature Ramp Rate', units='K/min', default=3.)
    maxfield = FloatParameter('Maximum Field', units='Oe', default=0.)
    fieldramp = FloatParameter('Magnetic Field Ramp Rate', units='Oe/min', default=100.)
    pinconfig = Parameter('Pin Configuration', default='2vdP')

    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
    #                'R vdp 2', 'R Hall 1', 'R Hall 2'] # Had to have something
    #                                                   # here with no logic in order 
                                                       # for MainWindow def__init__ 
                                                       # line to work

    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                    'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                    'R vdp 22', 'R Hall 12', 'R Hall 22']



    #if self.pinconfig == '1vdP':
    if pinconfig == '1vdP':
       DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                        'R vdp 2', 'R Hall 1', 'R Hall 2']

    #if self.pinconfig == '2vdP':
    if pinconfig == '2vdP':
       DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                        'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                        'R vdp 22', 'R Hall 12', 'R Hall 22']

    #if self.pinconfig == '2bridge':
    if pinconfig == '2bridge':
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
            self.switch.clos_vdp1()
        if config == 'vdp22':
            self.switch.clos_vdp2()
        if config == 'Hall12':
            self.switch.clos_Hall1()
        if config == 'Hall22':
            self.switch.clos_Hall2()
        if config == 'c1': 
            self.switch.clos_custom1()
        if config == 'c2': 
            self.switch.clos_custom2()


        sleep(0.36)

        res = self.currentsource.min_inloop_delta()
        self.switch.open_all()
        print('Done and opened switches', res)#/self.high_current)
        return res[0]/self.high_current


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
        print('Done Startup')

        self.currentsource.write("FORM:ELEM DEF")

        sleep(0.1)


    def execute(self):

        #self.maxb = 100000.
        self.switch.set_pins(1,3,4,2) #1,3,4,2
        self.switch.set_pins2(5,7,8,6) #1,3,4,2
        if self.pinconfig == '1vdP':
             configs = ['vdp1', 'vdp2', 'Hall1', 'Hall2']
        if self.pinconfig == '2vdP':
            configs = ['vdp1', 'vdp2', 'Hall1', 'Hall2', \
                       'vdp12', 'vdp22', 'Hall12', 'Hall22']
        if self.pinconfig == '2bridge':
            configs = ['c1', 'c2']
        ress = []
        ts = []
        bs = []
        self.starttime = time()

        if self.meastype == 'Temp':
            self.stable_relevant = r'"Stable"'

        if self.meastype == 'Hall':
            self.stable_relevant = r'"Holding (Driven)"'

            #mv.set_field(host, port, self.maxb, 600)

        #for i in range(self.iterations):

        if self.meastype == 'Hall':

            print('Selected Hall')

            mv.set_field(host, port, self.maxfield, self.fieldramp)
            sleep(1.8)
            print('Set Field')
            bfld = 0.
            done = False
            print('about to measure')
            #while bfld < 0.999*self.maxb:
            while not done: # Run the first leg of the Hall sweep

                print('Doing done loop')
                relevant = self.in_loop(configs)
                print(relevant)
                bfld = relevant[0]

                done = relevant[1] == self.stable_relevant 

                print(relevant[1], done)

            mv.set_field(host, port, -self.maxfield, self.fieldramp)
            sleep(1.8)

            done = False

            while not done: # Run the middle leg of the Hall sweep

                relevant = self.in_loop(configs)
                print(relevant)
                bfld = relevant[0]

                done = relevant[1] == self.stable_relevant 

                print(relevant[1], done)


            print('About to set field to zero.')
            mv.set_field(host, port, 0.0, self.fieldramp)
            sleep(1.8)
        
            done = False

            while not done: # Run the last leg of the Hall sweep

                print('In last leg of sweep.')
                relevant = self.in_loop(configs)
                print(relevant)
                bfld = relevant[0]

                done = relevant[1] == self.stable_relevant 

                print(relevant[1], done)

            print('Done Hall Sweep')

        if self.meastype == 'Temp':
            mv.set_temp(host, port, self.tempset, self.tempramp)
            sleep(1.6)
            bfld = 0.
            done = False
            print('about to measure')
            #while bfld < 0.999*self.maxb:
            while not done:
                relevant = self.in_loop(configs)
                print(relevant)
                bfld = relevant[0]

                done = relevant[1] == self.stable_relevant 

                print(relevant[1], done)

            print('Done Temp Sweep')


    def in_loop(self, configs):

        ress = []
        # get_temp and get_field from Dynacool
        temp = mv.query_temp(host, port)
        bfield = mv.query_field(host, port)
        print(bfield)
        tim = time() - self.starttime

        #print('Temp ', temp, 'Field ', bfield)

        # This is where comment starts for bridges
        print('Active configs are', configs)
        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

        if self.pinconfig == '1vdP':

            #print('In correct emitting block.', temp[0], bfield[0], ress)
            self.emit('results', {
                'Time': tim, \
                'Temperature': temp[0], \
                '\g(m)\-(0)H': bfield[0], \
                'R vdp 1': ress[0], \
                'R vdp 2': ress[1], \
                'R Hall 1': ress[2], \
                'R Hall 2': ress[3], \
                })

            print('Emit successful')

        if self.pinconfig == '2vdP':
            #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
            #                'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
            #                'R vdp 22', 'R Hall 12', 'R Hall 22']
            self.emit('results', {
                'Time': tim, \
                'Temperature': temp[0], \
                '\g(m)\-(0)H': bfield[0], \
                'R vdp 1': ress[0], \
                'R vdp 2': ress[1], \
                'R Hall 1': ress[2], \
                'R Hall 2': ress[3], \
                'R vdp 12': ress[4], \
                'R vdp 22': ress[5], \
                'R Hall 12': ress[6], \
                'R Hall 22': ress[7], \
                })
     
        if self.pinconfig == '2bridge':
            DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1', \
                            'R bridge 2']
            self.emit('results', {
                'Time': tim, \
                'Temperature': temp[0], \
                '\g(m)\-(0)H': bfield[0], \
                'R bridge 1': ress[0], \
                'R bridge 2': ress[1], \
                })
 

        sleep(0.01)
        '''

        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
            '\g(m)\-(0)H': bfield[0], \
            'R bridge 1': ress[0], \
            'R bridge 2': ress[1], \
            #'R Hall 1': ress[2], \
            #'R Hall 2': ress[3], \
            })
        sleep(0.01)

        '''

        if self.meastype == 'Temp':
            relevant = temp

        if self.meastype == 'Hall':
            relevant = bfield
        print('done emitting')

        return relevant


class MainWindow(ManagedWindow):

    def __init__(self):
        #super(MainWindow, self).__init__(
        super().__init__(
            procedure_class = TransportMeas,
            inputs=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'pinconfig'],
            displays=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'pinconfig'],
            x_axis='Time',
            y_axis='Temperature',
            directory_input=True,
            sequencer=True,
            sequencer_inputs=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'pinconfig'])#,
            #sequence_file="gui_sequencer_example_sequence.txt"
        #)
        self.setWindowTitle('Arbitrary Sweep')

    def queue(self, procedure=None):
        directory = self.directory
        print(self.directory)
        print('mydir', directory)
        #self.directory = r'C:\\Users\\Neil\\Documents'
        filename = unique_filename(directory)
        #procedure = self.make_procedure()

        if procedure is None:
            procedure = self.make_procedure()
        elif not procedure:
            print('making procedure my way')
            procedure = self.make_procedure()

        #procedure = self.make_procedure()
        results = Results(procedure, filename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)



class HallSweep(Procedure):

    def __init__(port, maxb):
        #self.host = host
        #self.port = port
        self.maxb = maxb
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

    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                    'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                    'R vdp 22', 'R Hall 12', 'R Hall 22']


    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1', \
    #                'R bridge 2']


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
            self.switch.clos_vdp1()
        if config == 'vdp22':
            self.switch.clos_vdp2()
        if config == 'Hall12':
            self.switch.clos_Hall1()
        if config == 'Hall22':
            self.switch.clos_Hall2()
        if config == 'c1': 
            self.switch.clos_custom1()
        if config == 'c2': 
            self.switch.clos_custom2()


        sleep(0.36)

        res = self.currentsource.min_inloop_delta()
        self.switch.open_all()
        return res/self.high_current




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
        print('Done Startup')


        sleep(0.1)

    def in_loop(self, configs):

        ress = []
        # get_temp and get_field from Dynacool
        temp = mv.query_temp(host, self.port)[0]
        bfield = mv.query_field(host, self.port)
        print(bfield)
        tim = time() - self.starttime

        #print('Temp ', temp, 'Field ', bfield)

        # This is where comment starts for bridges
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
            'R Hall 22': ress[7], \
            })
        sleep(0.01)
        '''

        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
            '\g(m)\-(0)H': bfield[0], \
            'R bridge 1': ress[0], \
            'R bridge 2': ress[1], \
            #'R Hall 1': ress[2], \
            #'R Hall 2': ress[3], \
            })
        sleep(0.01)

        '''

        print('done emitting')

        return bfield


    def execute(self):

        #self.maxb = 100000.
        self.switch.set_pins(1,3,4,2) #1,3,4,2
        configs = ['vdp1', 'vdp2', 'Hall1', 'Hall2', 'vdp12', 'vdp22', 'Hall12', 'Hall22']
        #configs = ['c1', 'c2']
        ress = []
        ts = []
        bs = []
        self.starttime = time()

        if self.meastype == 'Temp':
            self.stable_relevant = r'"Stable"'

        if self.meastype == 'Hall':
            self.stable_relevant = r'"Holding (Driven)"'

            mv.set_field(host, port, self.maxb, 600)

        #for i in range(self.iterations):

        sleep(1.8)
        bfld = 0.
        done = False
        print('about to measure')
        #while bfld < 0.999*self.maxb:
        while not done:

            print('Doing done loop')
            relevant = self.in_loop(configs)
            print('relevant is ', relevant)
            bfld = bfield[0]

            done = relevant[1] == self.stable_relevant 

            print(relevant[1], done)

        mv.set_field(host, port, -self.maxb, 600)
        sleep(1.8)

        done = False

        while not done:

            bfield = self.in_loop(configs)
            print(bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field 

            print(bfield[1], done)


        print('About to set field to zero.')
        mv.set_field(host, port, 0.0, 600)
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

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    directory = r'C:\Users\maglab\Documents\Python Scripts\qdppms\NSTO'
    os.chdir(directory)
    data_filename = 'rho_v_B_350K_5T_NS035g_1.csv'

    
    procedure = HallSweep(50000)

    procedure.iterations = 1
    procedure.high_current = 80.e-6
    procedure.delta = 1.e-3
    procedure.swpct1 = 10
    procedure.swpct2 = 1
    procedure.swpct2 = 1
    procedure.sswpct3 = 10
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


    '''

    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Hall Sweep')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min

    '''




if __name__ == '__main__':
    main()
