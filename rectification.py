# This script runs current pulse experiments. It uses the PyMeasure
# managed window to allow for easy user control of the pulses. The primary
# use of the pulses is to switch a magnetic state, and so each pulse
# will always be followed by a measurement pulse.

import numpy as np
import pandas as pd
import logging

log = logging.getLogger(__name__)
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
from pymeasure.experiment import IntegerParameter, FloatParameter, BooleanParameter, Parameter
from pymeasure.experiment.results import unique_filename
import ngcmeas.current_voltage as cv
import ngcmeas.switch_matrix as sm
import MultiVu_talk_ngc as mv
from PythonControl.parse_inputs import inputs


host = "128.104.184.130"
port = 5000


class CurrentPulse(Procedure):

    iterations = IntegerParameter("Measurement Number", default=1)
    current = FloatParameter("Pulse (switching) Current",
                                   units="A", default=10.e-6)
    pulse_length = FloatParameter("Pulse Length",
                                  units="s", default=5)
    pulse_number = FloatParameter("Number of pulses to measure", default=4)
    wait = FloatParameter("Inter-Pulse Wait Time",
                          units="s", default=0.1)
    #meas_current = FloatParameter("Pulse (Measurement) Current",
    #                              units="A", default=1.e-6)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    #rvng = FloatParameter('Voltmeter Range', units='V', default=1.e1)
    date = Parameter('Date Time', default='now')
    temperature = FloatParameter("Temperature", units="K")
    field = FloatParameter("Magnetic Field", units="Oe")
    meas_ip = IntegerParameter("Switch Column for I+ Measurement", default=4)
    meas_im = IntegerParameter("Switch Column for I- Measurement", default=7)
    meas_vp = IntegerParameter("Switch Column for V+ Measurement", default=2)
    meas_vm = IntegerParameter("Switch Column for V- Measurement", default=5)


    DATA_COLUMNS = ["Time", "Temperature", "B Field", "Pulse Num", "Current",
                    "Length", "Measurement Voltage"]


    def pulse_measure(self):

        self.switch.clos_custom(self.meas_ip, self.meas_im, self.meas_mp,
                            self.meas_vm)

        sleep(0.36)
    
    
    def startup(self):

        print("Starting Up")
        KE6221adapter = VISAAdapter("GPIB0::12")
        KE7001adapter = VISAAdapter("GPIB0::7")
        self.currentsource = cv.myKeithley6221(KE6221adapter)
        self.switch = sm.Keithley7001(KE7001adapter, "SwitchMatrix")
        print('instruments mapped')
        self.currentsource.reset()
        self.currentsource.write("SYST:COMM:SER:SEND 'VOLT:RANG:AUTO ON'")
        self.currentsource.write("SYST:COMM:SER:SEND 'TRAC:CLE'")

        #self.currensource.write("SYST:COMM:SER:SEND '*CLS'")
        #self.currensource.write("SYST:COMM:SER:SEND 'TRAC:CLE'")
        #self.currensource.write("SYST:COMM:SER:SEND 'FORM:ELEM READ,UNIT'")
        #self.currensource.write("SYST:COMM:SER:SEND 'SAMP:COUN 1'")
        #self.currensource.write("SYST:COMM:SER:SEND 'SENS:FUNC \"VOLT:DC\"'")
        #self.currentsource.write("SOUR:CURR:RANG 0.01") #+str(meas_current))
        #self.currentsource.write("SOUR:CURR "+str(self.current))
        #self.currentsource.write("SOUR:CURR:COMP 15")
        #sleep(0.1)
         
        # Clear the voltmeter buffer so it doesn't cause problems later.
        #self.currensource.write("SYST:COMM:SER:SEND ':FETC?'")
        #print("Successful write again")
        #sleep(0.50) # If this is shorter the response won't arrive in time for read
        #self.currentsource.write("SYST:COMM:SER:ENT?")
        #sleep(0.1)
        #resp = self.currentsource.read()

        print("Done Startup")

    def execute(self):

        # Set up the switch matrix
        self.switch.clos_custom(self.meas_ip, self.meas_im,
                                self.meas_vp, self.meas_vm)

        print("About to send pulses of ", self.current, " A current.`")


        # Set the Sourcemeter to return data in a good format.
        self.currentsource.write("FORM:ELEM DEF")

        # Start the current.
        current = self.current
        self.currentsource.start_current(current)
        curr_pol = np.sign(current)
        p_num = 1
        sleep(0.05)
        print("Started the current")

        # Loop through currents for all the pulses
        tim = 0.
        self.time_init = time()
        while tim < self.pulse_length*self.pulse_number:

            tim = time() - self.time_init
            print("Time (tim) is ", tim)
            print("len*num ", self.pulse_length*self.pulse_number)

            # Check if time to switch polarity.
            if tim > p_num*self.pulse_length: 
                print("Pulse number on ", p_num)
                p_num += 1
                current = -1 * current
                self.currentsource.start_current(current)
                print("Just wrote current ", current)
                curr_pol = np.sign(current)


            tim = time() - self.time_init
            temp = mv.query_temp(host, port)
            bfield = mv.query_field(host, port)
                
            volts = self.currentsource.meas_pulse(self.current, 3,
                                                  keep_output=False)

            #DATA_COLUMNS = ["Time", "Temperature", "B Field", "Pulse Current",
            #                "Pulse Length", "Wait Time", "Measurement Current",
            #                "Measurement Voltage"]
            print("Everything to emit", tim, temp[0], bfield[0], self.pulse_number,
                    current, self.pulse_length, volts)

            # Emit data to file
            print("About to emit")
            self.emit('results', {
                "Time": tim, \
                "Temperature": temp[0], \
                "B Field": bfield[0], \
                "Pulse Num": self.pulse_number, \
                "Current": current, \
                "Length": self.pulse_length, \
                "Measurement Voltage": volts \
                })

            print("Emit Successful!")


        self.switch.open_all()
        self.currentsource.write("OUTP OFF")


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
                procedure_class = CurrentPulse,
                inputs = ["iterations", "current", "pulse_length", "pulse_number",\
                    "wait", "nplc", "date", "temperature", "field",\
                    "meas_ip", "meas_im", "meas_vp", "meas_vm"],
                displays = ["iterations", "current", "pulse_length", "pulse_number",\
                    "wait", "nplc", "date", "temperature", "field",\
                    "meas_ip", "meas_im", "meas_vp", "meas_vm"],
                x_axis="Time", y_axis="Temperature",
                directory_input=True,
                sequencer=True,
                sequencer_inputs = ["iterations", "current", "pulse_length", "pulse_number",\
                    "wait", "nplc", "date", "temperature", "field",\
                    "meas_ip", "meas_im", "meas_vp", "meas_vm"],
                inputs_in_scrollarea=True)

        self.setWindowTitle("Pulsed Current")

    def queue(self, procedure=None):
        directory = self.directory
        mtype = getattr(self.inputs, "current").parameter.value
        print("About to Pulse {:.2E}A of current".format(mtype))
        prefix = "pulse_"
        filename = unique_filename(directory, prefix=prefix)
        #filename = tempfile.mktemp()
        #filename = "pulsed_current.csv" #filename(directory, prefix=prefix)


        if procedure is None:
            procedure = self.make_procedure()
        elif not procedure:
            print("making procedure my way")
            procedure = self.make_procedure()

        results = Results(procedure, filename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)

    
def main():

    host = "128.104.184.130"
    port = 5000

    #print('about to set field')
    #flds = field_ramp(host, port, 2000.)
    #print('field set')

    #plt.plot(flds)
    #plt.show()

    # Below is for running managed window
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    directory = r'C:\Users\maglab\Documents\Python Scripts\data\MNN\test_blank'
    os.chdir(directory)
    data_filename = 'funfunfun.csv'

    
    procedure = intentionalmessupCurrentPulse()
    procedure.iterations = 1
    procedure.current = 1.e-6 
    procedure.pulse_length = 0.5
    procedure.pulse_number = 4
    procedure.wait = 0.5
    #procedure.meas_current = 1.e-6
    procedure.nplc = 3
    #rvng = FloatParameter('Voltmeter Range', units='V', default=1.e1)
    procedure.date = datetime.now()
    procedure.temperature = 300.
    procedure.field = 0.
    procedure.meas_ip = 1
    procedure.meas_im = 2
    procedure.meas_vp = 3
    procedure.meas_vm = 4


    results = Results(procedure, data_filename)

    worker = Worker(results)
    print("Starting worker now.")
    worker.start()

    worker.join(timeout=100) # wait 1.67 min at most


if __name__ == "__main__":
    main()

