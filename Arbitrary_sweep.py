# This script runs a Hall sweep using a QD Dynacool PPMS cryostat
# and Keithley electronics. The Keithleys are controlled directly,
# while the cryostat is controlled through MultiVu via QD scripts
# in the PythonControl library.


import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
log - logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


import sys
import tempfile
import os
from time import sleep, time
from datetime import datetime
from pymeasure.log import console_log
from pymeasure.display.Qt import QtGui
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


class TransportMeas(Procedure):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        #self.meastype = meastype
        #self.tempset = tempset
        #self.maxb = maxb
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
    meastype = Parameter('Measurement Type', default='')
    tempset = FloatParameter('Temperature Set Point', default=300.)
    tempramp = FloatParameter('Temperature Ramp Rate', default=3.)
    maxfield = FloatParameter('Maximum Field', default=0.)
    fieldramp = FloatParameter('Magnetic Field Ramp Rate', default=100.)
    hysteresis = BooleanParameter('Do we expect a hysteresis?', default=False)
    pinconfig = Parameter('Pin Configuration', default='1vdP')

    if self.pinconfig == '1vdP':
        DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                        'R vdp 2', 'R Hall 1', 'R Hall 2']

    if self.pinconfig == '2vdP':
        DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                        'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                        'R vdp 22', 'R Hall 12', 'R Hall 22']

    if self.pinconfig == '2bridge':
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

        self.stable_field = r'"Holding (Driven)"'

        #for i in range(self.iterations):

        if self.meastype == 'Hall':

            bfld = 0.

            if self.hysteresis:
            # Do any extra leg if we expect hysteresis

                mv.set_field(self.host, self.port, -self.maxfield, 100)
                sleep(1.8)
                print('Hysteresis True so going to negative field.')

                done = False
                while not done: # wait until at max neg field
                    done =  bfield[1] == self.stable_field 


            mv.set_field(self.host, self.port, self.maxfield, self.fieldramp)
            sleep(1.8)

            done = False


            mv.set_field(self.host, self.port, self.maxfield, self.fieldramp)
            sleep(1.8)
            done = False
            print('about to measure')
            #while bfld < 0.999*self.maxb:


            while not done: # Run the first leg of the Hall sweep

                print('Doing done loop')
                bfield = self.in_loop(configs)
                print(bfield)
                bfld = bfield[0]

                done = bfield[1] == self.stable_field 

                print(bfield[1], done)

            mv.set_field(self.host, self.port, -self.maxfield, self.fieldramp)
            sleep(1.8)

            done = False

            while not done: # Run the middle leg of the Hall sweep

                bfield = self.in_loop(configs)
                print(bfield)
                bfld = bfield[0]

                done = bfield[1] == self.stable_field 

                print(bfield[1], done)


            print('About to set field to zero.')
            mv.set_field(self.host, self.port, 0.0, self.fieldramp)
            sleep(1.8)
        
            done = False

            while not done: # Run the last leg of the Hall sweep

                print('In last leg of sweep.')
                bfield = self.in_loop(configs)
                print(bfield)
                bfld = bfield[0]

                done = bfield[1] == self.stable_field 

                print(bfield[1], done)


        if self.meastype = 'Temp':
            mv.set_temp(self.host, self.port, self.tempset, self.ramprate)
            sleep(1.6)
            bfld = 0.
            done = False
            print('about to measure')
            #while bfld < 0.999*self.maxb:
            while not done:

                print('Doing done loop')
                temp = self.in_loop(configs)
                print(temp)
                tmp = temp[0]

                done = temp[1] == self.stable_temp

                print(temp[1], done)


    def in_loop(self, configs):

        ress = []
        # get_temp and get_field from Dynacool
        temp = mv.query_temp(self.host, self.port)[0]
        bfield = mv.query_field(self.host, self.port)
        print(bfield)
        tim = time() - self.starttime

        #print('Temp ', temp, 'Field ', bfield)

        # This is where comment starts for bridges
        for c in configs:

            ress.append(self.resistance_measure(c))
            print(ress[-1])

        print('about to emit', tim)

    if self.pinconfig == '1vdP':

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
            '\g(m)\-(0)H': bfield[0], \
            'R vdp 1': ress[0], \
            'R vdp 2': ress[1], \
            'R Hall 1': ress[2], \
            'R Hall 2': ress[3], \
            })


    if self.pinconfig == '2vdP':
        DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                        'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                        'R vdp 22', 'R Hall 12', 'R Hall 22']
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
 
    if self.pinconfig == '2bridge':
        DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R bridge 1', \
                        'R bridge 2']
        self.emit('results', {
            'Time': tim, \
            'Temperature': temp, \
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

        print('done emitting')

        return bfield


class MainWindow(ManagedWindow):

    def __init__(self):
        super(MainWindow, self).__init__(
            procedure_class=RandomProcedure,
            inputs=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            displays=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            x_axis='Iteration',
            y_axis='high_current',
            directory_input=True,
            sequencer=True,
            sequencer_inputs=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            #sequence_file="gui_sequencer_example_sequence.txt"
        )
        self.setWindowTitle('GUI Example')

    def queue(self, procedure=None):
        directory = self.directory
        print(self.directory)
        print('mydir', directory)
        #self.directory = r'C:\\Users\\Neil\\Documents'
        filename = unique_filename(directory)

        if procedure is None:
            procedure = self.make_procedure()

        #procedure = self.make_procedure()
        results = Results(procedure, filename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)



class HallSweep(Procedure):

    def __init__(self, host, port, maxb):
        self.host = host
        self.port = port
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
        temp = mv.query_temp(self.host, self.port)[0]
        bfield = mv.query_field(self.host, self.port)
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
            'R vdp 12': ress[4], \ # comment out for 1 vdp
            'R vdp 22': ress[5], \ # comment out for 1 vdp
            'R Hall 12': ress[6], \ # comment out for 1 vdp
            'R Hall 22': ress[7], \ # comment out for 1 vdp
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

        self.stable_field = r'"Holding (Driven)"'

        #for i in range(self.iterations):

        mv.set_field(self.host, self.port, self.maxb, 600)
        sleep(1.8)
        bfld = 0.
        done = False
        print('about to measure')
        #while bfld < 0.999*self.maxb:
        while not done:

            print('Doing done loop')
            bfield = self.in_loop(configs)
            print(bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field 

            print(bfield[1], done)

        mv.set_field(self.host, self.port, -self.maxb, 600)
        sleep(1.8)

        done = False

        while not done:

            bfield = self.in_loop(configs)
            print(bfield)
            bfld = bfield[0]

            done = bfield[1] == self.stable_field 

            print(bfield[1], done)


        print('About to set field to zero.')
        mv.set_field(self.host, self.port, 0.0, 600)
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

    app = QtGui.QApplications(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    directory = r'C:\Users\maglab\Documents\Python Scripts\qdppms\NSTO'
    os.chdir(directory)

    procedure = HallSweep(host, port, 50000)

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


    #'''

    data_filename = 'rho_v_B_350K_5T_NS035g_1.csv'
    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Hall Sweep')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min

    #'''




if __name__ == '__main__':
    main()
