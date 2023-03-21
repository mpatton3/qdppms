# This script runs Hall and Temperature sweeps using a QD Dynacool
# PPMS cryostat and Keithley electronics. The Keithleys are controlled
# directly, while the cryostat is controlled through MultiVu via QD scripts
# in the PythonControl library, and my wrapper MultiVu_talk_ngc. This script
# allows an arbitrary number of sweeps to be run one after the other and
# and parameters for each sweep to be selected customly. This allows a high 
# degree of automation when using custom pin configurations with the PPMS.


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
from pymeasure.experiment import IntegerParameter, FloatParameter, BooleanParameter, Parameter
from pymeasure.experiment.results import unique_filename
import ngcmeas.current_voltage as cv
import ngcmeas.switch_matrix as sm
import MultiVu_talk_ngc as mv
from PythonControl.parse_inputs import inputs


# Specific host and port for UW-Madison PPMS
host = "128.104.184.130"
port = 5000


class TransportMeas(Procedure):
    """
    This class allows either a Hall or Temp sweep to be performed, and it
    integrates with the ManagedWindow gui. The startup and execute methods
    are run by PyMeausre, and are what controls the exeperiment procedure.
    """
    
    # Experiment parameters for the sweeps.
    iterations = IntegerParameter('Measurement Number', default=1)
    high_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delta = FloatParameter('Delta', units='s', default=1.e-3)
    swpct1 = IntegerParameter('Sweep Count 1', default=10)
    swpct2 = IntegerParameter('Sweep Count 2', default=1)
    swpct3 = IntegerParameter('Sweep Count 3', default=10)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    rvng = FloatParameter('Voltmeter Range', units='V', default=1.e1)
    date = Parameter('Date Time', default='now')
    meastype = Parameter('Measurement Type', default='Temp')
    tempset = FloatParameter('Temperature Set Point', units='K', default=300.)
    tempramp = FloatParameter('Temperature Ramp Rate', units='K/min', default=3.)
    maxfield = FloatParameter('Maximum Field', units='Oe', default=0.)
    fieldramp = FloatParameter('Magnetic Field Ramp Rate', units='Oe/min', default=100.)
    hysteresis = BooleanParameter('Do we expect a hysteresis in B', default = False)
    pinconfig = Parameter('Pin Configuration', default='2vdP')

    #DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
    #                'R vdp 2', 'R Hall 1', 'R Hall 2'] # Had to have something
    #                                                   # here with no logic in order 
                                                       # for MainWindow def__init__ 
                                                       # line to work

    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R vdp 1', \
                    'R vdp 2', 'R Hall 1', 'R Hall 2', 'R vdp 12', \
                    'R vdp 22', 'R Hall 12', 'R Hall 22']


    # Check if these work at all to change the Data Columns
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


    def startup(self):
    """
    This method controls the device startup that occurs for every new sweep
    the user runs. This method connects to the voltmeter and switch matrix
    and initializes and arms the current source for specific measurement.
    """
        print('Starting Up')
        KE6221adapter = VISAAdapter("GPIB0::12")
        KE7001adapter = VISAAdapter("GPIB0::7")
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.switch = sm.Keithley7001(KE7001adapter, "SwitchMatrix")
        print('instruments mapped')
        self.currentsource.reset()
        self.currentsource.arm_preloop_delta(self.high_current, self.delta, 
                                             self.swpct1, self.swpct2, 
                                             self.swpct3, self.nplc, self.rvng,
                                             self.swpct1)
        #self.currentsource.arm_preloop_delta(self.high_current, delta, swpct1, \
        #                                     swpct2, swpct3, npld, rvng, \
        #                                     swpct1)
        print('Done Startup')

        # Assign host and port as attributes of class
        self.host = host
        self.port = port
        self.currentsource.write("FORM:ELEM DEF")

        sleep(0.1)


    def execute(self):

        #self.maxb = 100000.
        self.switch.set_pins(1,2,4,3) #1,3,4,2 Jieun wiring; 1243 Neil wiring
        self.switch.set_pins2(5,6,8,9) #1,3,4,2 # 7 -> 9 b/c 7 is bad at SM
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
            bfld = 0.

            if self.hysteresis:
            # Do an extra leg if we expect hysteresis

                mv.set_field(self.host, self.port, -self.maxfield, 100)
                sleep(1.8)
                print('Hysteresis True so going to negative field.')

                done = False
                while not done: # wait until at max neg field
                    done =  bfield[1] == self.stable_field 


            print("About to set field")
            mv.set_field(self.host, self.port, self.maxfield, self.fieldramp)
            sleep(1.8)
            print("set field")

            done = False


            mv.set_field(self.host, self.port, self.maxfield, self.fieldramp)
            sleep(1.8)

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
            inum = 0
            while not done:
                relevant = self.in_loop(configs)
                print(relevant)
                bfld = relevant[0]

                done = relevant[1] == self.stable_relevant 

                print(relevant[1], done)

                # Handle the PPMS not stabilizing at 2K
                if self.tempset < 2.3:
                    if relevant[0] < 2.3:
                        if inum > 10:
                            done = True
                        inum += 1

            print('Done Temp Sweep')


    def resistance_measure(self, config):
        """
        This function runs the individual resitance measurements, from setting
        the switch matrix pins, to actually collecting the voltage. Custom
        pin configurations for non-vdP situations are also set here.
        """

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

        # These are for bridges or other configurations that do not use van 
        # der Pauw configurations.
        if config == 'cust1':
            self.switch.clos_custom(1, 2, 3, 9) #5, 1, 6, 2
        if config == 'cust2':
            self.switch.clos_custom(1, 2, 3, 5)
        if config == 'cust3':
            self.switch.clos_custom(1, 2, 8, 4) #5, 1, 6, 2
        if config == 'cust4':
            self.switch.clos_custom(1, 2, 8, 6)



        sleep(0.36)

        # Below is where the voltage is actually measured
        volt = self.currentsource.min_inloop_delta()
        self.switch.open_all()
        print('Done and opened switches', volt)#/self.high_current)
        return volt[0]/self.high_current



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
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            displays=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            x_axis='Time',
            y_axis='R vdp 1',
            directory_input=True,
            sequencer=True,
            sequencer_inputs=['iterations', 'high_current', 'delta', 'swpct1', 'swpct2',\
                    'swpct3', 'nplc', 'rvng', 'date', 'meastype', 'tempset',\
                    'tempramp', 'maxfield', 'fieldramp', 'hysteresis', 'pinconfig'],
            inputs_in_scrollarea = True)#,
            #sequence_file="gui_sequencer_example_sequence.txt"
        #)
        self.setWindowTitle('Arbitrary Sweep')

    def queue(self, procedure=None):
        directory = self.directory
        print(self.directory)
        print('mydir', directory)
        #self.directory = r'C:\\Users\\Neil\\Documents'
        #print(self.inputs, 'meastype')
        mtype = getattr(self.inputs, 'meastype').parameter.value
        print('About to do meastype: ', mtype)
        prefix = 'rho_'# + mtype + '_'
        filename = unique_filename(directory, prefix=prefix)
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
