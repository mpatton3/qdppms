import win32com.client
import pythoncom
from PythonControl.DetectMultiVu import Instrument, MultiVuExeException
import sys


class QDInstrument:
    def __init__(self):
        if sys.platform == 'win32':
            try:
                self._mvu = win32com.client.Dispatch(Instrument(verbose=False).classId)
            except AttributeError:
                pass
        else:
            raise Exception('This must be running on a Windows machine')

        # All parameters are pulled at once with the aim of simultaneity

        # Grab temperature parameters
        temp_status_code = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)
        temperature = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        temp_err = self._mvu.GetTemperature(temp_status_code, temperature)

        self.temp = temperature.value
        self.temp_status_code = temp_status_code.value
        self._temp_err = temp_err

        # Translate the status code to human-readable text
        TempStates = {
            "1": "Stable",
            "2": "Tracking",
            "5": "Near",
            "6": "Chasing",
            "7": "Pot Operation",
            "10": "Standby",
            "13": "Diagnostic",
            "14": "Impedance Control Error",
            "15": "General Failure",
        }
        self.temp_status = TempStates[str(temp_status_code.value)]
        self.temp_unit = "K"

        # Grab field parameters
        field_status_code = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)
        field = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        field_err = self._mvu.GetField(field_status_code, field)

        self.field = field.value
        self.field_status_code = field_status_code.value
        self._field_err = field_err

        # Translate the status code to human-readable text
        MagStates = {
            "1": "Stable",
            "2": "Switch Warming",
            "3": "Switch Cooling",
            "4": "Holding (Driven)",
            "5": "Iterate",
            "6": "Ramping",
            "7": "Ramping",
            "8": "Resetting",
            "9": "Current Error",
            "10": "Switch Error",
            "11": "Quenching",
            "12": "Charging Error",
            "14": "PSU Error",
            "15": "General Failure",
        }
        self.field_status = MagStates[str(field_status_code.value)]
        self.field_unit = "Oe"

        # Grab chamber parameters
        chamber_status_code = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        chamber_err = self._mvu.GetChamber(chamber_status_code)

        self.chamber_status_code = chamber_status_code.value
        self._chamber_err = chamber_err

        # Translate the status code to human-readable text
        ChamberStates = {
            "0": "Sealed",
            "1": "Purged and Sealed",
            "2": "Vented and Sealed",
            "3": "Sealed",
            "4": "Performing Purge/Seal",
            "5": "Performing Vent/Seal",
            "6": "Pre-HiVac",
            "7": "HiVac",
            "8": "Pumping Coninuously",
            "9": "Flooding Continuously",
            "14": "HiVac Error",
            "15": "General Failure",
        }
        self.chamber_status = ChamberStates[str(chamber_status_code.value)]

        # Instantiate the 'set' class
        self.set = QDInstrument._set()

    class _set:
        def __init__(self):
            self._mvu = win32com.client.Dispatch(Instrument(verbose=False).classId)

        def temp(self, temperature, rate, approach):
            err = self._mvu.SetTemperature(temperature, rate, approach)
            return err
            # Approach Options: Fast Settle (0); No O'Shoot (1).

        def field(self, field, rate, approach, mag_state):
            err = self._mvu.SetField(field, rate, approach, mag_state)
            return err
            # Approach Options: Linear (0); No O'Shoot (1); Oscillate (2).
            # Magnet State Options: Persistent (0); Driven (1).

        def chamber(self, code):
            err = self._mvu.SetChamber(code)
            return err
