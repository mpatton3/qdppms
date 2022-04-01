# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 14:23:28 2020

@author: Quantum Design, Inc.
"""


import pandas as pd
import sys
import os
import time
import re
import subprocess
from threading import Lock
from enum import Enum, auto, IntEnum
from datetime import datetime
from PythonControl.valid_path import is_pathname_valid

LINE_TERM = '\r\n'
COMMENT_COL_HEADER = 'Comment'
TIME_COL_HEADER = 'Time Stamp (sec)'


class TScaleType(Enum):
    mvLinearScale = auto()
    mvLogScale = auto()


class TStartupAxisType(IntEnum):
    mvStartupAxisNone = 0
    mvStartupAxisX = 1
    mvStartupAxisY1 = 2
    mvStartupAxisY2 = 4
    mvStartupAxisY3 = 8
    mvStartupAxisY4 = 16


class TTimeUnits(Enum):
    mvMinutes = auto()
    mvSeconds = auto()


class TTimeMode(Enum):
    mvRelative = auto()
    mvAbsolute = auto()


class DataColumn():
    def __init__(self):
        self.index = 0
        self.Label = ''
        self.Value = 0
        self.ScaleType = TScaleType.mvLinearScale
        self.StartupAxis = TStartupAxisType.mvStartupAxisNone
        self.FieldGroup = ''
        self.Persistent = False
        self.IsFresh = False


class LabelResult(Enum):
    Success = auto()
    Blank = auto()
    OnlySpaces = auto()
    ContainsQuotes = auto()


class MultiVuDataFile():
    """
    This class is used to save data in the proper MultiVu file format.
    An example for how to use this class may be:
        >>>> import pandas as pd
        >>>>
        >>>> mv = MultiVuDataFile()
        >>>> mv.AddColumn('myY2Column', TStartupAxisType.mvStartupAxisY2)
        >>>> mv.AddMultipleColumns(['myColumnA', 'myColumnB', 'myColumnC'])
        >>>> mv.CreateFileAndWriteHeader('myMultiVuFile.dat', 'Using Python is fun')
        >>>> mv.SetValue('myY2Column', 2.718)
        >>>> mv.SetValue('myColumnA', 42)
        >>>> mv.SetValue('myColumnB', 3.14159)
        >>>> mv.SetValue('myColumnC', 9.274e-21)
        >>>> mv.WriteData()
        >>>>
        >>>> pd.myDataFrame = mv.parseMVuDataFile('myMultiVuFile.dat')

    """

    def __init__(self):
        # Make it so that we can add columns
        self.__HaveWrittenHeader = False
        self.FileName = ''
        self.FullPath = ''
        # System.Text.UTF8Encoding()
        # self.__UTF8Enc
        # Add default columns
        self._ColumnList = []
        self.AddColumn(COMMENT_COL_HEADER)
        self.AddColumn(TIME_COL_HEADER, TStartupAxisType.mvStartupAxisX)

    def GetCommentCol(self):
        return COMMENT_COL_HEADER

    def GetTimeCol(self):
        return TIME_COL_HEADER

    def _CreateFile(self, FileName):
        """
        Create the MultiVu file, if it doesn't already exist'

        Parameters
        ----------
        fileName : string
            Path the to file name.

        Returns
        -------
        newFile : boolean
            True if the file already exists, False if it did not exist

        Example
        -------
        >>> _CreateFile('myFile.dat')
            False

        """
        self.FullPath = os.path.abspath(FileName)
        dirName, FileName = os.path.split(self.FullPath)
        try:
            if not dirName:
                raise NotADirectoryError(f'Invalid file path: {FileName}. Please use a valid path.')
        except NotADirectoryError as e:# NGC #'d out
            if not(is_pathname_valid(FileName)): #NGC #'d out
                raise NotADirectoryError(f'File path {FileName} is invalid.') # NGC #'d out

        # Make sure we have the folder which is supposed to hold the
        # file in question.  If the folder already exists, move on,
        # if the folder does not exist, then create it.
        # NGC #'d out the next 7 lines'
        if not os.path.exists(dirName):
            try:
                os.mkdir(dirName)
            except PermissionError as e:
                errorMessage = f'Failed to create directory {dirName}. Verify'
                errorMessage += ' that you have permission to create this directory.'
                raise PermissionError(errorMessage)
        self.FileName = FileName
        # return FALSE if file already existed, TRUE if this was a new creation
        newFile = not os.path.isfile(self.FullPath)
        # open the file, which will create it if it doesn't already exist
        if newFile:
            self.__OpenFile()
            self.__CloseFile()
        return newFile

    def __OpenFile(self):
        numTries = 10
        while (numTries > 0):
            try:
                self.__FS = open(self.FullPath, 'w')
                numTries = -1
            except PermissionError as e:
                # we might have had a race condition trying to open the
                # file - we'll just try again
                numTries -= 1
                self.__FS.Close()
                time.sleep(0.100)  # milliseconds
        if (numTries == 0):
            errorMessage = f'Failed to open MultiVu data file after {numTries}'
            errorMessage += ' attempts. Verify that you have permission to'
            errorMessage += f' write to {self.FullPath}.'
            raise PermissionError(errorMessage)

    def __CloseFile(self):
        self.__FS.close()

    def TestLabel(self, Label) -> LabelResult:
        """
        Return the type of label.

        Parameters
        ----------
        Label : string

        Returns
        -------
        LabelResult.Success : LabelResults

        Example
        -------
        >>> TestLabel('Comment')
            Success

        """
        m = re.compile('^ +$')

        # Check if Label is a string
        if not Label:
            return LabelResult.Blank
        if m.search(Label):
            return LabelResult.OnlySpaces
        if '"' in Label:
            return LabelResult.ContainsQuotes
        return LabelResult.Success

    def bit_not(self, n, numbits=4):
        """
        bytewise NOT

        Parameters
        ----------
        n : numberic
        numbits : numberic, optional

        Returns
        -------
        bit_not : numeric

        Example
        -------
        >>> bin(bit_not(1))
            0b1110

        """
        return (1 << numbits) - 1 - n

    def AddColumn(self,
                  Label,
                  StartupAxis=TStartupAxisType.mvStartupAxisNone,
                  ScaleType=TScaleType.mvLinearScale,
                  Persistent=False,
                  FieldGroup=''):
        """
        Add a column to be used with the datafile.

        Parameters
        ----------
        Label : string
            Column name
        StartupAxis : TStartupAxisType, optional
            Used to specify which axis to use when plotting the column.
            TStartupAxisType.mvStartupAxisNone (default)
            TStartupAxisType.mvStartupAxisX (by default, this will be the time axis)
            TStartupAxisType.mvStartupAxisY1
            TStartupAxisType.mvStartupAxisY2
            TStartupAxisType.mvStartupAxisY3
            TStartupAxisType.mvStartupAxisY4
        ScaleType : TScaleType, optional
            TScaleType.mvLinearScale (default)
            TScaleType.mvLogScale
        Persistentm : boolean, optional
            Columns marked True have the prvious value saved each time data
            is written to the file.  Default is False
        FieldGroup : string, optional

        Raises
        ------
        MultiVuFileException
            Can only write the header once.

        Returns
        -------
        None.

        Example
        -------
        >>> AddColumn('MyDataColumn')
        """

        result = self.TestLabel(Label)
        if result != LabelResult.Success:
            raise MultiVuFileException(f'Error in column label: {result.ToString}')

        if self.__HaveWrittenHeader is True:
            errorMessage = f"Not adding column '{Label}' because the file"
            errorMessage += f" header has already been written to file '{self.FullPath}'."
            raise MultiVuFileException(errorMessage)
            return

        # if we already have a column with the same name, remove
        # it before adding the new one
        # for item in self._ColumnList:
        #     if Label in item.Label:
        #         self._ColumnList.pop()
        for i in range(len(self._ColumnList)):
            if Label in self._ColumnList[i].Label:
                self._ColumnList.pop(i)
                break

        if ((StartupAxis & TStartupAxisType.mvStartupAxisX) != 0):
            # Unset all others because we can have only one x-axis
            tempList = []
            for item in self._ColumnList:
                if ((item.StartupAxis & TStartupAxisType.mvStartupAxisX) != 0):
                    tempList.append(item)
            for item in tempList:
                item.StartupAxis = TStartupAxisType(item.StartupAxis.value &
                                                    (self.bit_not(TStartupAxisType.mvStartupAxisX.value)))

        dc = DataColumn()
        dc.Label = Label
        # make sure that comment/time columns are always the
        # first two columns in the data file
        if (Label == COMMENT_COL_HEADER):
            dc.index = 1
        elif (Label == TIME_COL_HEADER):
            dc.index = 2
        else:
            maxIndex = 0
            for item in self._ColumnList:
                maxIndex = max(maxIndex, item.index)
            dc.index = maxIndex + 1

        # Set the startup axes to the requested values (can be
        # added for multiple axes per column)
        dc.StartupAxis = StartupAxis
        dc.ScaleType = ScaleType
        dc.Persistent = Persistent
        dc.FieldGroup = FieldGroup
        dc.IsFresh = False
        dc.Value = None

        self._ColumnList.append(dc)

    def AddMultipleColumns(self, ColumnNames):
        """
        Add a column to be used with the datafile.

        Parameters
        ----------
        ColumnNames : list
            List of strings that have column names

        Returns
        -------
        None.

        Example
        -------
        >>> AddMultipleColumns(['MyDataColumn1', 'MyDataColumn2'])
        """
        for name in ColumnNames:
            self.AddColumn(name)

    def __GetIndex(self, e):
        '''

        Parameters
        ----------
        e : DataColumn class
            Used to sort a list of DataColumns by index number.

        Returns
        -------
        DataColumn.index

        '''
        return e.index

    def CreateFileAndWriteHeader(self,
                                 FileName,
                                 Title,
                                 timeUnits=TTimeUnits.mvSeconds,
                                 timeMode=TTimeMode.mvRelative):
        '''
        Create the file if it doesn't already exist.  If it already exists,
        exit the function so we don't write the header again. If it does not
        already exist, write the header.

        Parameters
        ----------
        FileName : string
            The path for where to save the MultiVu file
        Title : string
            MultiVu file title.
        timeUnits : TTimeUnits, optional
            TTimeUnits.mvMinutes
            TTimeUnits.mvSeconds (default)
        timeMode : TTimeMode, optional
            TTimeMode.mvRelative (default)
            TTimeMode.mvAbsolute

        Raises
        ------
        MultiVuFileException
            DESCRIPTION.

        Returns
        -------
        None.

        Example
        -------
        >>> CreateFileAndWriteHeader('myMvFile', 'my sample')

        '''

        fileExists = self._CreateFile(FileName)
        if not fileExists:
            # parse the existing headers so that we can verify that we have
            # all the columns we need and set their order to the order in
            # the data file
            inHeaders = True
            columnHeaders = ''
            with open(FileName) as f:
                for raw_line in f:
                    line = raw_line.rstrip()
                    if inHeaders:
                        inHeaders = (line != '[Data]')
                    else:
                        columnHeaders = line
                        break

            if (columnHeaders != ''):
                columnHeaders = columnHeaders.lstrip('"')
                columnHeaders = columnHeaders.rstrip('"')
                existingColumnHeaders = columnHeaders.split('","')
                if (len(self._ColumnList) != len(existingColumnHeaders)):
                    errorMessage = f"Failed to append to existing file '{FileName}'"
                    errorMessage += " - mismatch in number of columns."
                    raise MultiVuFileException(errorMessage)
                    return
                else:
                    # Column count is correct. See if the columns match. If
                    # so, append to the file. If not, throw an exception
                    for i in range(len(sorted(self._ColumnList, key=self.__GetIndex))):
                        if self._ColumnList[i].Label != existingColumnHeaders[i]:
                            errorMessage = f"Failed to append to existing file '{FileName}'"
                            errorMessage += f" - mismatch in column titles:{LINE_TERM}"
                            errorMessage += f" New title: '{self._ColumnList[i].Label}' {LINE_TERM}"
                            errorMessage += f" Existing title: '{existingColumnHeaders[i - 1]}'"
                            raise MultiVuFileException(errorMessage)
                        else:
                            self.__HaveWrittenHeader = True
                    return


            # Make sure we don't add any more columns after this
            self.__HaveWrittenHeader = True
            return
        # Make sure we don't add any more columns after this
        self.__HaveWrittenHeader = True

        # Standard header items
        with open(FileName, "a") as f:
            f.write('[Header]\n')
            f.write('; Copyright (c) 2003-2013, Quantum Design, Inc. All rights reserved.\n')
            fileTime = datetime.now()
            f.write(f"FILEOPENTIME, {fileTime.timestamp()}, {fileTime.strftime('%m/%d/%Y, %H:%M:%S %p')}\n")
            f.write('BYAPP, MultiVuDataFile Python class\n')
            f.write(f'TITLE, {Title}\n')
            f.write('DATATYPE, COMMENT,1\n')
            f.write('DATATYPE, TIME,2\n')
            timeUnitsString = ''
            if timeUnits == TTimeUnits.mvMinutes:
                timeUnitsString = 'MINUTES'
            else:
                timeUnitsString = 'SECONDS'
            timeModeString = ''
            if timeMode == TTimeMode.mvAbsolute:
                timeModeString = 'ABSOLUTE'
            else:
                timeModeString = 'RELATIVE'
            f.write(f'TIMEMODE, {timeUnitsString}, {timeModeString}\n')

        # Generate list of FieldGroups
        FieldGroups = []
        for col in self._ColumnList:
            if col.FieldGroup != '':
                FieldGroups.append(str(col.FieldGroup))

        # Write out FieldGroups
        # Columns where the FieldGroup is set are added to their
        # specific FieldGroup
        # Columns where the FieldGroup is not set (blank string) are
        # added to ALL FieldGroups (they are global)
        with open(FileName, "a") as f:
            for fg in FieldGroups:
                # Safer to use local variable rather than iteration variable in
                # the conditional test below
                currentFieldGroup = fg
                fieldGroupColumnNumbers = []
                for columnInFieldGroup in self._ColumnList:
                    if (columnInFieldGroup.FieldGroup == currentFieldGroup) or \
                            (columnInFieldGroup.FieldGroup == ''):
                        fieldGroupColumnNumbers.append(str(columnInFieldGroup.index))

                f.write(', '.join(['FIELDGROUP',
                                      currentFieldGroup,
                                      ', '.join(fieldGroupColumnNumbers)]) + '\n')
            f.write('STARTUPGROUP, All\n')

        # Find the first item that wants to be the x axis
        with open(FileName, "a") as f:
            for xColumn in sorted(self._ColumnList, key=self.__GetIndex):
                if (xColumn.StartupAxis & TStartupAxisType.mvStartupAxisX) != 0:
                    writeString = f'STARTUPAXIS, X, {xColumn.index}, '
                    writeString += f'{self.__ScaleTypeString(xColumn.ScaleType)}, '
                    writeString += 'AUTO\n'
                    f.write(writeString)
                    # We can only have one x column so we bail after
                    # setting the first one (there really shouldn't be more
                    # than one anyway due to our AddColumn() checks)
                    break


        # Find up to four items that want to be y-axes
        with open(FileName, "a") as f:
            NumYAxesFound = 0
            for yColumn in sorted(self._ColumnList, key=self.__GetIndex):
                if (yColumn.StartupAxis > TStartupAxisType.mvStartupAxisX):
                    for j in range(1, 5):
                        if (yColumn.StartupAxis & (1 << j)) != 0:
                            NumYAxesFound += 1
                            writeString = 'STARTUPAXIS, '
                            writeString += f'Y{j}, '
                            writeString += f'{yColumn.index}, '
                            writeString += f'{self.__ScaleTypeString(yColumn.ScaleType)}, '
                            writeString += 'AUTO\n'
                            f.write(writeString)
                            if NumYAxesFound >= 4:
                                # We've got 4 y-axes, so it's time to
                                # stop looking for more
                                break
                    if NumYAxesFound >= 4:
                        break

        with open(FileName, "a") as f:
            f.write('[Data]\n')

            allColumnHeaders = []
            for col in sorted(self._ColumnList, key=self.__GetIndex):
                allColumnHeaders.append(f'"{col.Label}"')

            # Write out the column headers
            f.write(','.join(allColumnHeaders) + '\n')

    def __ScaleTypeString(self, ScaleType):
        '''
        Private method to convert the scale type into a string

        Parameters
        ----------
        ScaleType : TScaleType
            TScaleType.mvLinearScale
            TScaleType.mvLogScale

        Returns
        -------
        scaleTypeString : str

        Example
        -------
        >>> __ScaleTypeString(TScaleType.mvLinearScale)

        '''
        scaleTypeString = 'LINEAR'
        if ScaleType == TScaleType.mvLogScale:
            scaleTypeString = 'LOG'
        return scaleTypeString

    def SetValue(self, Label, Value):
        '''
        Sets a value for a given column.  After calling this method, a call
        to WriteData() will save this to the file.

        Parameters
        ----------
        Label : string
            The name of the data column.
        Value : string or numeric
            The data that needs to be saved.

        Raises
        ------
        MultiVuFileException
            The Label must have been written to the file.

        Returns
        -------
        None.

        Example
        -------
        >>> SetValue('myColumn', 42)

        '''
        LabelInList = False
        for item in self._ColumnList:
            if item.Label == Label:
                if (Label == COMMENT_COL_HEADER) or (type(Value) == str):
                    # Sanitize comments by replacing all commas with
                    # semicolons in order not to break the file
                    # structure. Multivu does not handle
                    # commas, even if you put strings in quotes!
                    Value = Value.replace(',', ';')
                else:
                    Value = str(Value)

                item.Value = Value
                item.IsFresh = True
                return
        if not LabelInList:
            errorString = f"Error writing value '{Value}' to "
            errorString += f"column '{Label}'. Column not found."
            raise MultiVuFileException(errorString)
            return

    def GetValue(self, Label):
        '''
        Returns the last value that was saved using SetValue(Label, Value)

        Parameters
        ----------
        Label : str
            Column name.

        Raises
        ------
        MultiVuFileException
            The Label must have been written to the file.

        Returns
        -------
        str or numeric
            The last value saved using SetValue(Label, Value).

        Example
        -------
        >>> GetValue('myColumn')
        >>> 42

        '''
        LabelInList = False
        for item in self._ColumnList:
            if item.Label == Label:
                return item.Value

        if not LabelInList:
            errorString = f"Error getting value from column '{Label}'. "
            errorString += "Column not found."
            raise MultiVuFileException(errorString)
            return

    def GetFreshStatus(self, Label):
        '''
        After calling SetValue(Label, Value), the value is considered Fresh
        and is waiting to be written to the MultiVu file using WriteData()

        Parameters
        ----------
        Label : str
            Column name.

        Raises
        ------
        MultiVuFileException
            The Label must have been written to the file.

        Returns
        -------
        boolean
            True means the value has not yet been saved to the file

        Example
        -------
        >>> GetFreshStatus('myColumn')
        >>> True

        '''
        LabelInList = False
        for item in self._ColumnList:
            if item.Label == Label:
                return item.IsFresh

        if not LabelInList:
            errorString = f"Error getting value from column '{Label}'."
            errorString += ' Column not found.'
            raise MultiVuFileException(errorString)
            return

    def SetFreshStatus(self, Label, status):
        '''
        This allows one to manually set the Fresh status, which is used
        to decide if the data will be written to the file when calling
        WriteData()

        Parameters
        ----------
        Label : str
            Column name.
        status : boolean
            True (False) means the Value in the column Label
            will (not) be written.

        Raises
        ------
        MultiVuFileException
            The Label must have been written to the file.

        Returns
        -------
        None.

        Example
        -------
        >>> SetFreshStatus('myColumn', True)

        '''
        LabelInList = False
        for item in self._ColumnList:
            if item.Label == Label:
                item.IsFresh = status
                LabelInList = True

        if not LabelInList:
            errorString = f"Error setting value for column '{Label}'."
            errorString += ' Column not found.'
            raise MultiVuFileException(errorString)

    def WriteData(self, GetTimeNow=True):
        '''
        Writes all fresh or persistent data to the MultiVu file.

        Parameters
        ----------
        GetTimeNow : boolean, optional
            By default, the time when this method is called will be
            written to the MultiVu file. The default is True.

        Raises
        ------
        MultiVuFileException
            CreateFileAndWriteHeader() must be called first.

        Returns
        -------
        None.

        Example
        -------
        >>> WriteData()

        '''
        if not self.__HaveWrittenHeader:
            errorString = 'Must write the header file before writing data. '
            errorString += 'Call the CreateFileAndWriteHeader() method first.'
            raise MultiVuFileException(errorString)
            return

        lock = Lock()
        lock.acquire()
        if GetTimeNow:
            self.SetValue(TIME_COL_HEADER, datetime.now().timestamp())

        # Add data for those columns where there is valid data
        # present and it is (fresh or persistent)
        currentValues = []
        for item in sorted(self._ColumnList, key=self.__GetIndex):
            if item.Value != '' and (item.Persistent or item.IsFresh):
                currentValues.append(item.Value)
            else:
                currentValues.append('')

        with open(self.FullPath, "a") as f:
            f.write(','.join(currentValues))
            f.write('\n')

        # Mark all data as no longer being fresh
        for item in self._ColumnList:
            item.IsFresh = False
        lock.release()

    def WriteDataUsingList(self, dataList, GetTimeNow=True):
        '''
        Function to set values fromm list and then write them to data file
        Format of list is ColKey1, Value1, ColKey2, Value2, ...
        The list can contain values for all columns or a subset of columns,
        in any order

        Parameters
        ----------
        dataList : list
            A list of column names and values.
        GetTimeNow : boolean, optional
            By default, the time when this method is called will be
            written to the MultiVu file. The default is True.

        Raises
        ------
        MultiVuFileException
            The number of columns and data must be equal, which means
            that the list needs to have an even number of items.

        Returns
        -------
        None.

        Example
        -------
        >>> WriteDataUsingList(['myColumn1', 42, 'myColumn2', 3.14159])

        '''
        i = 0

        NumEntries = len(dataList)

        if ((NumEntries % 2) != 0):
            errorMessage = 'Error in WriteDataUsingList(). dataList'
            errorMessage += f' contains {NumEntries} entries. It should'
            errorMessage += ' contain an even number of entries'
            raise MultiVuFileException(errorMessage)
            return
        for i in range(0, len(dataList), 2):
            self.SetValue(dataList[i], dataList[i + 1])
        self.WriteData(GetTimeNow)

    def parseMVuDataFile(self, filePath) -> pd.DataFrame:
        '''
        Returns a pandas DataFrame of all data points in the given file

        Parameters
        ----------
        filePath : str
            Path to the MultiVu file.

        Returns
        -------
        pandas.DataFrame
            A dataframe which includes all of the columns and data.

        Example
        -------
        >>> parseMVuDataFile('myMvFile.dat')

        '''
        allLines = []

        # parse the existing headers so that we can verify that we have
        # all the columns we need and set their order to the order in
        # the data file
        inHeaders = True
        columnHeaders = ''
        with open(filePath) as f:
            for raw_line in f:
                line = raw_line.rstrip()
                if inHeaders:
                    inHeaders = not (line == '[Data]')
                else:
                    if (columnHeaders == ''):
                        columnHeaders = line
                    else:
                        dataDict = self.__parseMVuDataFileLine(line, columnHeaders)
                        allLines.append(dataDict)
        return pd.DataFrame(allLines)


    def __parseMVuDataFileLine(self, line, columnHeaders) -> dict():
        '''
        Parse an individual data line from a MultiVu file into a dictionary
        keyed by the header titles.  A private method.

        Parameters
        ----------
        line : str
            An individual line of data from a MultiVu file.
        columnHeaders : str
            The column names found in a MultiVu file.

        Raises
        ------
        MultiVuFileException
            The column names and the number of data points mus be equal.

        Returns
        -------
        dict()
            A dictionary of the data.  The key is the column name.

        Example
        -------
        >>> __parseMVuDataFileLine('"",1620348924.0125,42','Comment,Time Stamp (sec),myColumn')

        '''
        headerArray = self.__parseCSVLine(columnHeaders)

        dataArray = self.__parseCSVLine(line)

        if len(dataArray) != len(headerArray):
            errorMessage = 'Error in __parseMVuDataFileLine(). Line contains'
            errorMessage += ' a different number of values than the header.'
            raise MultiVuFileException(errorMessage)
            return

        columnDict = dict()
        for i in range(len(dataArray)):
            try:
                value = float(dataArray[i])
            except ValueError:
                value = dataArray[i]

            columnDict[headerArray[i].replace('"', '')] = value

        return columnDict

    def __parseCSVLine(self, line) -> {}:
        '''
        Takes a comma-seperated line of data from a MultiVu file and
        converts it to a list

        Parameters
        ----------
        line : str
            comma-separated string of data.

        Raises
        ------
        MultiVuFileException
            The line of data must be in the proper format.

        Returns
        -------
        list
            A list of data found in a line of MultiVu data.

        Example
        -------
        >>> __parseCSVLine('"",1620348924.0125,42')
        >>> ['',1620348924.0125,42]

        '''
        try:
            return line.split(',')
        except MultiVuFileException as e:
            errorMessage = 'Malformed line in file. Unable to '
            errorMessage += f'process: {LINE_TERM} {line}'
            raise MultiVuFileException(errorMessage)


class MultiVuFileException(Exception):
    """MultiVu File Exception Error"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
