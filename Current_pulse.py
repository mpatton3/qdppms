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
    pulse_current = FloatParameter("Pulse (switching) Current",
                                   units="A", default=10.e-6)
    pulse_length = FloatParameter("Pulse (switching) Length",
                                  units="s", default=0.1)
    wait = FloatParameter("Inter-Pulse Wait Time",
                          units="s", default=0.1)
    meas_current = FloatParameter("Pulse (Measurement) Current",
                                  units="A", default=1.e-6)
    nplc = IntegerParameter('Num Power Line Cycles', default=3)
    #rvng = FloatParameter('Voltmeter Range', units='V', default=1.e1)
    date = Parameter('Date Time', default='now')
    temperature = FloatParameter("Temperature", units="K")
    field = FloatParameter("Magnetic Field", units="Oe")
    pulse_ip = IntegerParameter("Switch Column for I+ Pulse", default=9)
    pulse_im = IntegerParameter("Switch Column for I- Pulse", default=2)
    meas_ip = IntegerParameter("Switch Column for I+ Measurement", default=9)
    meas_im = IntegerParameter("Switch Column for I- Measurement", default=2)
    meas_vp = IntegerParameter("Switch Column for V+ Measurement", default=6)
    meas_vm = IntegerParameter("Switch Column for V- Measurement", default=4)


    DATA_COLUMNS = ["Time", "Temperature", "B Field", "Pulse Current",
                    "Pulse Length", "Wait Time", "Measurement Current",
                    "Measurement Voltage"]


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
        self.currentsource.write("SYST:COMM:SER:SEND 'VOLT:RANG AUTO'")
        sleep(0.1)
        
        self.time_init = time()
        print("Done Startup")

    def execute(self):

        # Send the switching pulse
        self.switch.clos_custom(self.pulse_ip, self.pulse_im,
                                self.meas_vp, self.meas_vm)
        sleep(0.36)

        print("About to send switching pulse of ", self.pulse_current, " A")
        self.currentsource.send_pulse(self.pulse_current, self.pulse_length)

        print("Sent pulse")
        # Send the measurement pulse
        # possibly set switch matrix to new configuration
        sleep(self.wait)
        
        current_pol = np.sign(self.pulse_current+self.meas_current*10**-5)
        self.currentsource.arm_delta(current_pol*self.meas_current, 0., 1.e-3,
                                             10, 1, 10, self.nplc, 1.e1, 10)
        sleep(3.0)

        self.currentsource.write("FORM:ELEM DEF")

        #volts = self.currentsource.min_inloop_delta()
        volts = self.currentsource.meas_pulse(self.current, 10,
                                        keep_output=False)
        #volts = self.currentsource.meas_pulse(self.meas_current, 5)
        print("did meas pulse")
        print(volts)

        tim = time() - self.time_init
        temp = mv.query_temp(host, port)
        bfield = mv.query_field(host, port)
            
        #DATA_COLUMNS = ["Time", "Temperature", "B Field", "Pulse Current",
        #                "Pulse Length", "Wait Time", "Measurement Current",
        #                "Measurement Voltage"]

        print("About to emit")
        self.emit('results', {
            "Time": tim, \
            "Temperature": temp[0], \
            "B Field": bfield[0], \
            "Pulse Current": self.pulse_current, \
            "Pulse Length": self.pulse_length, \
            "Wait Time": self.wait, \
            "Measurement Current": self.meas_current, \
            "Measurement Voltage": volts[0] \
            })

        print("Emit Successful!")

        self.switch.open_all()


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
                procedure_class = CurrentPulse,
                inputs = ["iterations", "pulse_current", "pulse_length", "wait",\
                    "meas_current", "nplc", "date", "temperature", "field",\
                    "pulse_ip", "pulse_im", "meas_ip", "meas_im", "meas_vp",\
                    "meas_vm"],
                displays = ["iterations", "pulse_current", "pulse_length", "wait",\
                    "meas_current", "nplc", "date", "temperature", "field",\
                    "pulse_ip", "pulse_im", "meas_ip", "meas_im", "meas_vp",\
                    "meas_vm"],
                x_axis="Time", y_axis="Temperature",
                directory_input=True,
                sequencer=True,
                sequencer_inputs = ["iterations", "pulse_current", "pulse_length", "wait",\
                    "meas_current", "nplc", "date", "temperature", "field",\
                    "pulse_ip", "pulse_im", "meas_ip", "meas_im", "meas_vp",\
                    "meas_vm"],
                inputs_in_scrollarea=True)

        self.setWindowTitle("Pulsed Current")

    def queue(self, procedure=None):
        directory = self.directory
        mtype = getattr(self.inputs, "pulse_current").parameter.value
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
    procedure.pulse_current = 1.e-6 
    procedure.pulse_length = 0.5
    procedure.wait = 0.5
    procedure.meas_current = 1.e-6
    procedure.nplc = 3
    #rvng = FloatParameter('Voltmeter Range', units='V', default=1.e1)
    procedure.date = datetime.now()
    procedure.temperature = 300.
    procedure.field = 0.
    procedure.pulse_ip = 1
    procedure.pulse_im = 2
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

