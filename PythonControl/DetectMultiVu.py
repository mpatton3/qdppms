import subprocess, re
import win32com.client
import sys
from enum import Enum, auto


class instrumentList(Enum):
    DYNACOOL = auto()
    PPMS = auto()
    VERSALAB = auto()
    MPMS3 = auto()
    OPTICOOL = auto()
    na = auto()

# TODO:  It appears to not know if MultiVu was open and is now closed.

class Instrument():
    def __init__(self, flavor='', verbose=True):
        '''
        This class is used to detect which flavor of MultiVu is installed
        on the computer.  It is also used to return the name of the .exe
        and the class ID, which can be used by win32com.client.

        Parameters
        ----------
        flavor : string, optional
            This is the common name of the MultiVu flavor being used.  If
            it is left blank, then the class finds the installed version
            of MultiVu to know which flavor to use.  The default is ''.
        verbose : bool, optional
            When set to True, the flavor of MultiVu is displayed
            on the command line. The default is True.
        '''
        if flavor == '':
            # If unspecified, find which version of MV if any is running and use that
            self.name = self.detect_multivu(verbose)
        else:
            # If specified, check that it's a allowed flavor; if not, print an error
            found = False
            for instrument in instrumentList:
                if instrument.name.upper() == flavor.upper():
                    self.name = flavor.upper()
                    found = True
                    break
            if not found:
                print("The specified MultiVu variant, {}, is not recognized.".format(flavor))
                sys.exit()

        self.exeName = ""
        self._getExe(self.name)
        self.classId = ""
        self._getClassId(self.name)

    def _getExe(self, inst):
        '''
        Returns the name of the MultiVu exe.

        Parameters
        ----------
        inst : instrumentType
            The flavor of QD instrument using the instrumentList enum.

        Returns
        -------
        TYPE
            A string of the specific MultiVu flavor .exe

        '''
        if inst.upper() == instrumentList.PPMS.name:
            name = inst.capitalize() + 'Mvu'
        elif inst.upper() == instrumentList.MPMS3.name:
            name = 'SquidVsm'
        else:
            name = inst.capitalize()
        self.exeName = name + '.exe'
        return self.exeName
    
    def _getClassId(self, inst):
        '''
        Parameters
        ----------
        inst : instrumentType
            The flavor of QD instrument using the instrumentList enum.

        Returns
        -------
        string
            The MultiVu class ID.  Used for things like opening MultiVu.

        '''
        self.classId = f'QD.MULTIVU.{inst}.1'
        return self.classId
    
    def detect_multivu(self, verbose=True):
        '''
        This looks in the file system for an installed version of
        MultiVu.  Once it find it, the function returns the name.

        Parameters
        ----------
        verbose : bool
            When this flag is set to True, it prints to the command
            line the flavor of MultiVu detected.

        Raises
        ------
        MultiVuExeException
            This is thrown if MultiVu is not running, or if multiple
            instances of MultiVu are running.

        Returns
        -------
        string
            Returns the common name of the QD instrument.

        '''
        # Build a list of enum, instrumentType
        instrumentNames = list(instrumentList)
        # Remove the last item (called na)
        instrumentNames.pop()
    
        # Use WMIC to get the list of running programs with 'multivu' in their path
        cmd = 'WMIC PROCESS WHERE "COMMANDLINE like \'%multivu%\'" GET '
        cmd += 'Caption,Commandline,Processid'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    
        # Attempt to match the expected MV executable names with the programs
        # in the list and instantiate the instrument and add to MultiVuList
        MultiVuList = []
        for line in proc.stdout:
            if (line == b'\r\r\n' or line == b'\r\n'):
                break
            for instr in instrumentNames:
                if re.findall(self._getExe(instr.name.capitalize()), line.decode()):
                    MultiVuList.append(instr.name)

        # Declare errors if to few or too many are found; for one found,
        # declare which version is identified
        if len(MultiVuList) == 0:
            errMsg = "No running instance of MultiVu was detected."
            errMsg += "  Please start MultiVu and retry."
            raise MultiVuExeException(errMsg)
    
        elif len(MultiVuList) > 1:
            errMsg = "There are multiple running instances of MultiVu {} ".format(MultiVuList)
            errMsg += "detected.  Please close all but one and retry."
            raise MultiVuExeException(errMsg)
    
        elif len(MultiVuList) == 1:
            self.name = MultiVuList[0]
            if verbose:
                print(MultiVuList[0] + " MultiVu detected.")
            return self.name
    
    # def OpenMultiVu(self):
    #     '''
    #     Opens MultiVu.

    #     Raises
    #     ------
    #     MultiVuExeException
    #         It could fail if it is unable to open MultiVu.

    #     Returns
    #     -------
    #     None.

    #     '''
    #     try:
    #         win32com.client.Dispatch(self.classId)
    #     except:
    #         errMsg = f'Failed to open {self.exeName}. Confirm '
    #         errMsg += 'that it is installed.'
    #         raise MultiVuExeException(errMsg)


class MultiVuExeException(Exception):
    """MultiVu Exception Error"""
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
    def __str__(self):
        return self.message
