# This script uses Pymeasure to run IV sweeps at set temps and fields
# as the user prescribes. The individual IV curves are saved in the directory,
# and summary parameters are saved in they PyMeasure results-based datafile.
# As a result, a new directory for every measurement is recommended.



import numpy as np
import pandas as pd
import os
from time import sleep, time
import ngcmeas.current_voltage as cv
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
    start_field = FloatParameter('Starting Field', units='Oe', default=0.)
    end_field = FloatParameter('Ending Field', units='Oe', default=0.)
    max_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delay = FloatParameter('Delay', units='s', default=100.e-3)
    nplc = IntegerParameter('Num Power Line Cycles', default=3) #not used?
    date = Parameter('Date Time', default='')
    numberpoints = IntegerParameter('IV points 0 to maxI', default=10)
    sweep_type = Parameter('linear or log', default = 'lin')
    pulse_width = FloatParameter('Pulse Width', units='s', default=400.e-6)


    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'R', \
                    'NonLinear']


    def startup(self):

        print('Starting Up')
        KE6221adapter = VISAAdapter("GPIB0::12")
        KE7001adapter = VISAAdapter("GPIB0::7")
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.switch = sm.Keithley7001(KE7001adapter, "SwitchMatrix")
        print('instruments mapped')
        self.currentsource.reset() 
        self.currentsource.current_sweep_setup(self.max_current, \
                self.numberpoints, self.sweep_type, self.delay, \
                self.nplc, self.pulse_width)
    
        print('Done Startup')

        sleep(0.1)


    def execute(self):

        self.stable_field = r'"Holding (Driven)"'
        self.stable_temp = r'"Stable"' 
        field_stable = False
        temp_stable = False

        while not (field_stable or temp_stable):
            b = mv.query_field(self.host, self.port)
            t = mv.query_temp(self.host, self.port)

            field_stable = b[1] == self.stable_field
            temp_stable = t[1] == self.stable_temp

        self.currentsource.current_sweep_inloop()
        res, nonlin = self.currentsource.IV_compute_res()
        self.emit('results', {
                'Time': ,\
                'Temperature': t[0],\
                '\g(m)\-(0)H': b[0],\
                'R': res, \
                'NonLinear': nonlin \
                })

        print('Done Emitting')
        self.currentsource.write_IV_file(t[0], b[0], self.max_current,\
                                         self.sweep_type)


def main():

    host = "128.104.184.130"
    port = 5000


    # Start editing
    directory = r'C:\Users\maglab\Documents\Python Scripts\data\KTO\jk167'
    os.chdir(directory)
    data_filename = 'rho_v_B_50K_1T_KTO_jk167_0.csv'


    setpoint = 10000 # max B in Oe
    ramprate = 100   # field ramp in Oe/sec
    procedure = HallSweep(host, port, setpoint, ramprate)

    procedure.iterations = 1
    procedure.high_current = 5.0e-6 # Amps
    # Stop editing

    procedure.delta = 1.e-3
    procedure.swpct1 = 10
    procedure.swpct2 = 1
    procedure.swpct2 = 1
    procedure.sswpct3 = 10
    procedure.nplc = 3
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

