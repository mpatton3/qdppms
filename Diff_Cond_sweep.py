# This script runs Differential conductance measurements using pymeasure.


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from time import sleep, time
from datetime import datetime
import ngcmeas.current_voltage as cv
from pymeasure.adapters import VISAAdapter
from pymeasure.experiment import Procedure, Results, Worker
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
import ngcmeas.current_voltage as cv
import ngcmeas.switch_matrix as sm
import MultiVu_talk_ngc as mv
from PythonControl.parse_inputs import inputs



class DifCndSweep(Procedure):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        super().__init__()


    iterations = IntegerParameter('Measurement Number')
    start_temp = FloatParameter('Starting Temperature', units='K', default=300.)
    end_temp = FloatParameter('Ending Temperature', units='K', default=300.)
    temp_points = IntegerParameter('Number of Temp points', default = 50)
    temp_ramp = FloatParameter('Temperature Ramp Rate', units='K/min', default=3.)
    start_field = FloatParameter('Starting Field', units='Oe', default=0.)
    end_field = FloatParameter('Ending Field', units='Oe', default=0.)
    field_points = IntegerParameter('Number of Field points', default = 50)
    field_ramp = FloatParameter('Field Ramp Rate', units='Oe/s', default=50.)
    start_I = FloatParameter('Max Current', units='A', default=0.e-6)
    stop_I = FloatParameter('Max Current', units='A', default=100.e-6)
    step_I = FloatParameter('Max Current', units='A', default=5.e-6)
    delta_I = FloatParameter('Max Current', units='A', default=3.e-6)
    delay = FloatParameter('Delay', units='s', default=1.e-3)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    date = Parameter('Date Time', default='')
    num_IV = IntegerParameter('Number of IV sweeps to take at each point', default=1)
    sweep_type = Parameter('linear or log', default = 'linear')
    pulse_width = FloatParameter('Pulse Width', units='s', default=400.e-6)


    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R', \
                    'NonLinear']


    def startup(self):

        print('Starting Up')
        KE6221adapter = VISAAdapter("GPIB0::12")
        KE7001adapter = VISAAdapter("GPIB0::7")
        print('adapters done')
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.switch = sm.Keithley7001(KE7001adapter, "SwitchMatrix")
        print('instruments mapped')
        self.currentsource.reset() 
        self.currentsource.differential_cond_setup(self.start_I, \
                self.stop_I, self.step_I, self.delta_I, self.delay, \
                self.nplc)
    
        self.starttime = time()
        print('Done Startup')

        # Generate Temp list for measurement

        self.temp_to_meas = np.linspace(self.start_temp, self.end_temp, self.temp_points)
        self.field_to_meas = np.linspace(self.start_field, self.end_field, self.field_points)
        #print(self.field_to_meas)
        sleep(0.1)


    def execute(self):

        self.stable_field = r'"Holding (Driven)"'
        self.stable_temp = r'"Stable"' 

        #for tmpmes in self.temp_to_meas:
        for fldmes in self.field_to_meas:

            '''
            # For changing temp
            mv.set_temp(self.host, self.port, tmpmes, self.temp_ramp)

            print('going to '+str(tmpmes)+'K now')
            '''

            # For changing field
            mv.set_field(self.host, self.port, fldmes, self.field_ramp)

            print('going to '+str(fldmes)+'Oe now')

            sleep(1.8)

            field_stable = False
            temp_stable = False

            while not (field_stable and temp_stable):
                b = mv.query_field(self.host, self.port)
                t = mv.query_temp(self.host, self.port)

                field_stable = b[1] == self.stable_field
                temp_stable = t[1] == self.stable_temp
                #print(field_stable, temp_stable)
                #print((field_stable and temp_stable))
                #print((field_stable or temp_stable))
                sleep(0.1)


            print('Out of while loop and field ', b[0], ' temp ', t[0])
            tim = time() - self.starttime
            
            for i in range(self.num_IV):
                measstart = time()
                self.currentsource.differential_cond_inloop()
                meas_time = time() - measstart
                print('IV time to run ', meas_time)
                self.currentsource.write_IV_file(t[0], b[0], self.stop_I,\
                                         'linear')

                res, nonlin = self.currentsource.IV_compute_res()
                self.emit('results', {
                        'Time': tim,\
                        'Temperature': t[0],\
                        '\g(m)\-(0)H': b[0],\
                        'R': res, \
                        'NonLinear': nonlin \
                        })

                print('Done Emitting')


        self.currentsource.write("SOUR:SWE:ABOR")
        print('Done with Temps')



def main():

    host = "128.104.184.130"
    port = 5000


    # Start editing
    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B015\10K_check\dc_test'
    os.chdir(directory)
    data_filename = 'DCsweeps_12mA_10K_3kOe_3kOe_90deg_B015_0.csv'


    '''
    setpoint = 10000 # max B in Oe
    ramprate = 100   # field ramp in Oe/sec
    '''
    procedure = DifCndSweep(host, port)
    

    procedure.iterations = 1
    procedure.start_I = -500.0e-6 # Amps
    procedure.stop_I = 500.0e-6 # Amps
    procedure.step_I = 10.0e-6 # Amps
    procedure.delta_I = 15.0e-6 # Amps
    procedure.delay = 1.0e-3 # seconds
    procedure.nplc = 3 # power line cycles
    procedure.num_IV = 1 # Number of IV sweeps at each point
    procedure.start_temp = 10. # K
    procedure.end_temp = 10. # K
    procedure.temp_points = 9 # in Temp sweep
    procedure.temp_ramp = 3. # K/min ramp rate
    procedure.start_field = 3000. # K
    procedure.end_field = 3000. # K
    procedure.field_points = 2 # in Temp sweep
    procedure.field_ramp = 95. # K/min ramp rate
    # Stop editing

    procedure.delay = 1.e-1
    procedure.nplc = 3

    procedure.sweep_type = 'linear'
    procedure.pulse_width = 11000e-6
    procedure.rvng = 1.e1
    now = datetime.now()

    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Measurement')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min




if __name__ == "__main__":
    main()











