# This script contains classes, functions, and code for setting
# a Keithley 7001 switch matrix for measurement functionality.


import numpy as np
import pandas as pd
import os
from time import sleep
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter



class Keithley7001(Instrument):

    def set_pins(self, pinA, pinB, pinC, pinD):
        self.pinA = pinA
        self.pinB = pinB
        self.pinC = pinC
        self.pinD = pinD

    def set_pins2(self, pinE, pinF, pinG, pinH):
        self.pinE = pinE
        self.pinF = pinF
        self.pinG = pinG
        self.pinH = pinH


    def open_all(self):
        self.write(":ROUT:OPEN ALL")

    def clos_vdp1(self):
        row1str = "1!1!"+str(self.pinA)
        row2str = ", 1!2!"+str(self.pinB)
        row3str = ", 1!3!"+str(self.pinD)
        row4str = ", 1!4!"+str(self.pinC)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_vdp2(self):
        row1str = "1!1!"+str(self.pinA)
        row2str = ", 1!2!"+str(self.pinD)
        row3str = ", 1!3!"+str(self.pinB)
        row4str = ", 1!4!"+str(self.pinC)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_Hall1(self):
        row1str = "1!1!"+str(self.pinA)
        row2str = ", 1!2!"+str(self.pinC)
        row3str = ", 1!3!"+str(self.pinB)
        row4str = ", 1!4!"+str(self.pinD)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_Hall2(self):
        row1str = "1!1!"+str(self.pinB)
        row2str = ", 1!2!"+str(self.pinD)
        row3str = ", 1!3!"+str(self.pinC)
        row4str = ", 1!4!"+str(self.pinA)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_vdp12(self):
        row1str = "1!1!"+str(self.pinE)
        row2str = ", 1!2!"+str(self.pinF)
        row3str = ", 1!3!"+str(self.pinH)
        row4str = ", 1!4!"+str(self.pinG)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_vdp22(self):
        row1str = "1!1!"+str(self.pinE)
        row2str = ", 1!2!"+str(self.pinH)
        row3str = ", 1!3!"+str(self.pinF)
        row4str = ", 1!4!"+str(self.pinG)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_Hall12(self):
        row1str = "1!1!"+str(self.pinE)
        row2str = ", 1!2!"+str(self.pinG)
        row3str = ", 1!3!"+str(self.pinF)
        row4str = ", 1!4!"+str(self.pinH)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_Hall22(self):
        row1str = "1!1!"+str(self.pinF)
        row2str = ", 1!2!"+str(self.pinH)
        row3str = ", 1!3!"+str(self.pinG)
        row4str = ", 1!4!"+str(self.pinE)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

 
    def clos_bridge(self):

        # Closes so that pinA = I+, pinB = I-, pinC = V+, pinD = V-
        row1str = "1!1!"+str(self.pinA)
        row2str = ", 1!2!"+str(self.pinB)
        row3str = ", 1!3!"+str(self.pinC)
        row4str = ", 1!4!"+str(self.pinD)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_custom1(self):

        # Closes so that pinA = I+, pinB = I-, pinC = V+, pinD = V-
        row1str = "1!1!"+str(1)
        row2str = ", 1!2!"+str(2)
        row3str = ", 1!3!"+str(6)
        row4str = ", 1!4!"+str(5)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_custom2(self):

        # Closes so that pinA = I+, pinB = I-, pinC = V+, pinD = V-
        row1str = "1!1!"+str(1)
        row2str = ", 1!2!"+str(2)
        row3str = ", 1!3!"+str(4)
        row4str = ", 1!4!"+str(3)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")

    def clos_custom(self, ip, im, vp, vm):

        # Closes so that pinA = I+, pinB = I-, pinC = V+, pinD = V-
        row1str = "1!1!"+str(ip)
        row2str = ", 1!2!"+str(im)
        row3str = ", 1!3!"+str(vp)
        row4str = ", 1!4!"+str(vm)

        self.write(":CLOS (@" + row1str + row2str + row3str + row4str + ")")





def main():

    ke7001gpib = 7
    adapter = VISAAdapter("GPIB::7")
    KE7001SM = Keithley7001(adapter, "Switch")


    KE7001SM.open_all()
    sleep(1.0)
 
    KE7001SM.write(":CLOS (@ 1!1!7, 1!2!9, 1!3!7, 1!4!9)")
    #KE7001SM.open_all()
    sleep(1.0)

    pinA = 1
    pinB = 2
    pinC = 2
    pinD = 1

    #KE7001SM.set_pins(pinA, pinB, pinC, pinD)
    #KE7001SM.clos_vdp1()
    print(KE7001SM.ask(":ROUT:CLOS? (@ 1!1!4, 1!2!3)"))
    #KE7001SM.open_all()
    #print(KE7001SM.ask(":ROUT:CLOS? (@ 1!1!1, 1!1!2)"))
    #row1 = 3
    #row1str = ":CLSO(@ 1!1!" + str(row1) + ")"
    print("DONE")



if __name__ == '__main__':
    main()
