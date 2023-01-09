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
    angle = FloatParameter('Probe Angle', units='deg', default=0.)
    start_temp = FloatParameter('Starting Temperature', units='K', default=300.)
    end_temp = FloatParameter('Ending Temperature', units='K', default=300.)
    temp_points = IntegerParameter('Number of Temp points', default = 50)
    temp_ramp = FloatParameter('Temperature Ramp Rate', units='K/min', default=3.)
    start_field = FloatParameter('Starting Field', units='Oe', default=0.)
    end_field = FloatParameter('Ending Field', units='Oe', default=0.)
    field_points = IntegerParameter('Number of Field points', default = 50)
    field_ramp = FloatParameter('Field Ramp Rate', units='Oe/s', default=50.)
    max_current = FloatParameter('Max Current', units='A', default=1.e-6)
    delay = FloatParameter('Delay', units='s', default=100.e-3)
    nplc = IntegerParameter('Num Power Line Cycles', default=3) #not used?
    date = Parameter('Date Time', default='')
    numberpoints = IntegerParameter('IV points 0 to maxI', default=10)
    num_IV = IntegerParameter('Number of IV sweeps to take at each point', default=1)
    sweep_type = Parameter('linear or log', default = 'linear')
    pulse_width = FloatParameter('Pulse Width', units='s', default=400.e-6)


    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'Angle', 'R', \
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
        self.field_to_meas = np.linspace(self.start_field, self.end_field,
                                         self.field_points)
        fields_pos = np.linspace(self.start_field, self.end_field,
                                         self.field_points)

        fields_neg = np.linspace(-self.start_field, -self.end_field,
                                          self.field_points)

        # Edit here to switch between field sweep and angular sweep
        #self.field_to_meas = np.concatenate(([20000], fields_pos,
        #                            [-20000], fields_neg)) # for field sweep
        self.field_to_meas = [self.start_field] # for angl sweep
        #print(self.field_to_meas)
        sleep(0.1)

        # Set Switch Matrix
        self.switch.open_all()
        sleep(0.6)
        #self.switch.set_pins(5, 1, 3, 8)
        #self.switch.clos_vdp2()
        self.switch.clos_custom(9, 8, 9, 8) #5, 1, 4, 8


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
            temp_stable = True


            while not (field_stable and temp_stable):
                b = mv.query_field(self.host, self.port)
                t = mv.query_temp(self.host, self.port)

                field_stable = b[1] == self.stable_field
                #temp_stable = t[1] == self.stable_temp
                #print(field_stable, temp_stable)
                #print((field_stable and temp_stable))
                #print((field_stable or temp_stable))
                sleep(0.2)


            print('Out of while loop and field ', b[0], ' temp ', t[0])
            tim = time() - self.starttime

            b = mv.query_field(self.host, self.port)
            t = mv.query_temp(self.host, self.port)
           
            for i in range(self.num_IV):
                measstart = time()
                self.currentsource.current_sweep_inloop()
                meas_time = time() - measstart
                print('IV time to run ', meas_time)
                self.currentsource.write_IV_file(t[0], b[0], self.max_current,\
                                         self.angle, self.sweep_type)

                res, nonlin = self.currentsource.IV_compute_res()
                self.emit('results', {
                        'Time': tim,\
                        'Temperature': t[0],\
                        '\g(m)\-(0)H': b[0],\
                        'Angle': self.angle,\
                        'R': res, \
                        'NonLinear': nonlin \
                        })

                print('Done Emitting')


        print('Done with Temps')


def main():

    host = "128.104.184.130"
    port = 5000

    now = datetime.now()

    # Start editing
    directory = (r'C:\Users\maglab\Documents\Python Scripts\data\Ma_group'
                 r'\AlN_Diamond_A5 and E3 for IV\400K_1T')
    os.chdir(directory)
    data_filename = 'IVsweeps_5mA_400K_1T_7878_ch3_0.csv'


    '''
    setpoint = 10000 # max B in Oe
    ramprate = 100   # field ramp in Oe/sec
    '''
    procedure = IVSweep(host, port)
    

    procedure.iterations = 1
    procedure.angle = 00.
    procedure.max_current = 5.0e-6 # Amps
    procedure.numberpoints = 53 # in IV sweep, for list can only do up to 100
    procedure.num_IV = 2 # Number of IV sweeps at each point
    procedure.start_temp = 400. # K
    procedure.end_temp = 400. # K
    procedure.temp_points = 1 # in Temp sweep
    procedure.temp_ramp = 3. # K/min ramp rate
    procedure.start_field = 10000. # Oe
    procedure.end_field = 1000. # Oe
    procedure.field_points = 29 # in Temp sweep
    procedure.field_ramp = 100. # K/min ramp rate
    procedure.sweep_type = 'list' # 'linear' for linear sweep, 'list' for custom
    # Stop editing

    procedure.delay = 1.e-1
    procedure.nplc = 3
    procedure.date = now.strftime("%m/%d/%Y, %H:%M:%S")

    procedure.pulse_width = 11000e-6
    procedure.rvng = 1.e1

    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting worker to run Hall Sweep')
    worker.start()

    worker.join(timeout=120) # wait at most 2 min

    #'''


if __name__ == '__main__':
    main()

