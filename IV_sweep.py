# This script uses Pymeasure to run IV sweeps at set temps and fields
# as the user prescribes. The individual IV curves are saved in the directory,
# and summary parameters are saved in they PyMeasure results-based datafile.
# As a result, a new directory for every measurement is recommended.



import numpy as np
import pandas as pd
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


class IVSweep(Procedure):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        super().__init__()

    iterations = IntegerParameter('Measurement Number')
    start_temp = FloatParameter('Starting Temperature', units='K', default=300.)
    end_temp = FloatParameter('Ending Temperature', units='K', default=300.)
    temp_points = IntegerParameter('Number of Temp points', default = 50)
    start_field = FloatParameter('Starting Field', units='Oe', default=0.)
    end_field = FloatParameter('Ending Field', units='Oe', default=0.)
    max_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delay = FloatParameter('Delay', units='s', default=100.e-3)
    nplc = IntegerParameter('Num Power Line Cycles', default=3) #not used?
    date = Parameter('Date Time', default='')
    numberpoints = IntegerParameter('IV points 0 to maxI', default=10)
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
        self.currentsource.current_sweep_setup(self.max_current, \
                self.numberpoints, self.sweep_type, self.delay, \
                self.nplc, self.pulse_width)
    
        self.starttime = time()
        print('Done Startup')

        # Generate Temp list for measurement

        self.temp_to_meas = np.linspace(self.start_temp, self.end_temp, self.temp_points)
        #print(self.temp_to_meas)
        sleep(0.1)


    def execute(self):

        self.stable_field = r'"Holding (Driven)"'
        self.stable_temp = r'"Stable"' 

        for tmpmes in self.temp_to_meas:

            mv.set_temp(self.host, self.port, tmpmes, 1.0)

            print('going to '+str(tmpmes)+'K now')
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


            tim = time() - self.starttime
            measstart = time()
            self.currentsource.current_sweep_inloop()
            meas_time = time() - measstart
            print('IV time to run ', meas_time)

            res, nonlin = self.currentsource.IV_compute_res()
            self.emit('results', {
                    'Time': tim,\
                    'Temperature': t[0],\
                    '\g(m)\-(0)H': b[0],\
                    'R': res, \
                    'NonLinear': nonlin \
                    })

            print('Done Emitting')
            self.currentsource.write_IV_file(t[0], b[0], self.max_current,\
                                         self.sweep_type)

        print('Done with Temps')


def main():

    host = "128.104.184.130"
    port = 5000


    # Start editing
    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B015\IV_3K_9K_warm'
    os.chdir(directory)
    data_filename = 'IVsweeps_3K_9K_0T_B015_0.csv'


    '''
    setpoint = 10000 # max B in Oe
    ramprate = 100   # field ramp in Oe/sec
    '''
    procedure = IVSweep(host, port)
    
    procedure.iterations = 1
    procedure.max_current = 500.0e-6 # Amps
    procedure.numberpoints = 151 # in IV sweep
    procedure.start_temp = 3. # K
    procedure.end_temp = 9. # K
    procedure.temp_points = 31 # in Temp sweep
    # Stop editing

    procedure.delay = 1.e-1
    procedure.nplc = 3

    procedure.sweep_type = 'linear'
    procedure.pulse_width = 400e-6
    procedure.rvng = 1.e1
    now = datetime.now()

    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Hall Sweep')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min

    #'''


if __name__ == '__main__':
    main()

