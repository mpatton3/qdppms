# This script ramps the magnetic field from the high set point to the low, 
# then back and forth between the low field set points. This is crucial prep
# for good SHH 1w measurements.
# The scrip monitors the lockin voltage during the sweeps.


import numpy as np
import pandas as pd
import os
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter
from time import sleep, time
from datetime import datetime
from pymeasure.instruments.keithley import Keithley6221
from pymeasure.instruments.srs import SR830
from pymeasure.experiment import Procedure, Results, Worker
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
import ngcmeas.current_voltage as cv
import MultiVu_talk_ngc as mv



class Field_Initialize(Procedure):

    def __init__(self, host, port, max_field, ramp_rate, cycles):
        self.host = host
        self.port = port
        self.max_field = max_field
        self.ramp_rate = ramp_rate
        self.stable_field = r'"Holding (Driven)"'
        self.cycles = cycles
        self.init_sign = self.max_field/abs(self.max_field)
        super().__init__()

    iterations = IntegerParameter('Measurement Number')
    current_amp = FloatParameter('Current Amplitude', units='A', default = 1.e-3)
    current_freq = FloatParameter('Current Frequency', units='Hz', default = 123.456)
    current_offset = FloatParameter('Current Offset', units='A', default = 0.0)
    harmonic = IntegerParameter('Harmonic', default = 1)
    # Here down use defaults, and convert with dictionary in current_voltage mySRS830 class
    input_config = IntegerParameter('Input Configuration', default = 1) #Default is A-B
    shield_ground = IntegerParameter('Shield Ground', default = 0) # Default is Float
    cplng = IntegerParameter('AC or DC Coupling', default = 0) # Default is AC
    line_filter = IntegerParameter('Line Filter', default = 3) # Default is Both
    sensty = Parameter('Sensitivity') 
    tmcnst = Parameter('Time Constant')
    lpfltsp = IntegerParameter('Low Pass Filter', default = 2) # Default is 18dB/oct
    ref = IntegerParameter('Reference Signal', default = 0) # Default is External
    date = Parameter('Date and Time')


    DATA_COLUMNS = ['Time', 'Temperature', '\g(m)\-(0)H', 'phi', 'Volts', \
                    'Voltx', 'Volty']

    
    def startup(self):
        print('Starting Up')
        KE6221adapter = VISAAdapter('GPIB0::12')
        SRS830adapter = VISAAdapter("GPIB::8")
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.lockin = cv.mySR830(SRS830adapter)
        print('Instruments Mapped')
        # Configuration of KE6221 and SRS830 should be done in separate script beforehand.
        # The current should be running when this script starts.


        self.currentsource.write('OUTP?')
        if self.currentsource.read() == '1':
            print('Current is On')
        else:
            print('need to turn current on')

        print('Done Startup')
        print(mv.query_temp(self.host, self.port))


    def take_measurement(self):

        temp = mv.query_temp(self.host, self.port)
        bfield = mv.query_field(self.host, self.port)
        tim = time() - self.starttime
        numbers = self.lockin.read_one()

        self.emit('results', {
            'Time': tim, \
            'Temperature': temp[0], \
            '\g(m)\-(0)H': bfield[0], \
            'phi': numbers[3], \
            'Volts': numbers[2], \
            'Voltx': numbers[0], \
            'Volty': numbers[1] \
            })
        sleep(0.01)

        return bfield


    def execute(self):

        self.starttime = time()

        mv.set_field(self.host, self.port, self.max_field, self.ramp_rate)

        print('In execute')
        sleep(1.8)
        done = False
        print('about to go to Initial Field')
        while not done:

            bfield = self.take_measurement()  
            done = bfield[1] == self.stable_field


        mv.set_field(self.host, self.port, -self.max_field, self.ramp_rate)
        print('sweeping back')

        sleep(1.8)
        done = False
        while not done:

            bfield = self.take_measurement()  
            done = bfield[1] == self.stable_field

 
        '''
        for cyc in range(self.cycles):

            mv.set_field(self.host, self.port, -self.init_sign*self.low_field, self.ramp_rate)
            sleep(1.8)
            done = False
            print('visit number ', cyc, ' to low field')
            while not done:
      
                bfield = self.take_measurement()  
                done = bfield[1] == self.stable_field

            mv.set_field(self.host, self.port, self.init_sign*self.low_field, self.ramp_rate)
            sleep(1.8)
            done = False
            while not done:
      
                bfield = self.take_measurement()  
                done = bfield[1] == self.stable_field
        '''



def main():

    
    host = "128.104.184.130"
    port = 5000

    # Connect to KE6221 and SRS830
    adapter = VISAAdapter("GPIB::12")
    KE6221 = cv.myKeithley6221(adapter)

    adapter2 = VISAAdapter("GPIB::8")
    LockIn = cv.mySR830(adapter2)

    LockIn.get_params()

    now = datetime.now()


    directory = r'C:\Users\maglab\Documents\Python Scripts\data\BPBO\B015\test\2.5K'
    os.chdir(directory)
    data_filename = 'volt_2w_Hall_v_B_2mA_m0.32T_meas_2.5K_phi75deg_B015_0.txt'

    max_field = 0.32e4 # initial field in Oe
    #low_field = -0.43e4 # low field value to sweep beween and end at, always pos
    ramp_rate = 15 # field ramp rate in Oe/sec
    cycles = 4 # number of cyles between low fields before stopping

    procedure = Field_Initialize(host, port, max_field, ramp_rate, cycles)

    # After shh_electronics_init.py is written, modify this code to read those parameters.

    
    procedure.iterations = 1
    procedure.sensty = LockIn.sensty
    procedure.tmcnst = LockIn.tmcnst
    procedure.date = now.strftime("%m/%d/%Y, %H:%M:%S")
 
    results = Results(procedure, data_filename)

    worker = Worker(results)
    print('Starting Field Initialization.')
    worker.start()

    worker.join(timeout=120) # wait at most 2 minutes


if __name__ == '__main__':
    main()
