#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
"""transformCSV.py

This module contains the basic functions for creating the content of a configuration file from CSV.

Args:
    --inFile: Path for the configuration file where the time series data values CSV
    --outFile: Path for the configuration file where the time series data values INI
    --debug: Boolean flag to activate verbose printing for debug use

Example:
    Default usage:
        $ python transformCSV.py
    Specific usage:
        $ python transformCSV.py
          --inFile C:\raad\src\software\time-series.csv
          --outFile C:\raad\src\software\time-series.ini
          --debug True

"""
import sys
import datetime
import optparse
import traceback
import pandas
import numpy
import os
import pprint
import csv

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class TransformMetaData(object):
    debug = False
    fileName = None
    fileLocation = None
    columnsList = None
    analysisFrameFormat = None
    uniqueLists = None
    analysisFrame = None

    def __init__(self, inputFileName=None, debug=False, transform=False, sectionName=None, outFolder=None,
                 outFile='time-series-madness.ini'):
        if isinstance(debug, bool):
            self.debug = debug

        if inputFileName is None:
            return
        elif os.path.exists(os.path.abspath(inputFileName)):
            self.fileName = inputFileName
            self.fileLocation = os.path.exists(os.path.abspath(inputFileName))
        (analysisFrame, analysisFrameFormat, uniqueLists, columnNamesList) = self.CSVtoFrame(
            inputFileName=self.fileName)
        self.analysisFrame = analysisFrame
        self.columnsList = columnNamesList
        self.analysisFrameFormat = analysisFrameFormat
        self.uniqueLists = uniqueLists
        if transform:
            passWrite = self.frameToINI(analysisFrame=analysisFrame, sectionName=sectionName, outFolder=outFolder,
                                        outFile=outFile)
            print(f"Pass Status is : {passWrite}")
        return

    def getColumnList(self):
        return self.columnsList

    def getAnalysisFrameFormat(self):
        return self.analysisFrameFormat

    def getuniqueLists(self):
        return self.uniqueLists

    def getAnalysisFrame(self):
        return self.analysisFrame

    @staticmethod
    def getDateParser(formatString="%Y-%m-%d %H:%M:%S.%f"):
        return (lambda x: pandas.datetime.strptime(x, formatString))  # 2020-06-09 19:14:00.000

    def getHeaderFromFile(self, headerFilePath=None, method=1):
        if headerFilePath is None:
            return (None, None)

        if method == 1:
            fieldnames = pandas.read_csv(headerFilePath, index_col=0, nrows=0).columns.tolist()
        elif method == 2:
            with open(headerFilePath, 'r') as infile:
                reader = csv.DictReader(infile)
                fieldnames = list(reader.fieldnames)
        elif method == 3:
            fieldnames = list(pandas.read_csv(headerFilePath, nrows=1).columns)
        else:
            fieldnames = None

        fieldDict = {}
        for indexName, valueName in enumerate(fieldnames):
            fieldDict[valueName] = pandas.StringDtype()
        return (fieldnames, fieldDict)

    def CSVtoFrame(self, inputFileName=None):
        if inputFileName is None:
            return (None, None)

        # Load File
        print("Processing File: {0}...\n".format(inputFileName))
        self.fileLocation = inputFileName

        # Create data frame
        analysisFrame = pandas.DataFrame()

        analysisFrameFormat = self._getDataFormat()
        inputDataFrame = pandas.read_csv(filepath_or_buffer=inputFileName,
                                         sep='\t',
                                         names=self._getDataFormat(),
                                         # dtype=self._getDataFormat()
                                         # header=None
                                         # float_precision='round_trip'
                                         # engine='c',
                                         # parse_dates=['date_column'],
                                         # date_parser=True,
                                         # na_values=['NULL']
                                         )
        if self.debug:  # Preview data.
            print(inputDataFrame.head(5))

        # analysisFrame.astype(dtype=analysisFrameFormat)

        # Cleanup data
        analysisFrame = inputDataFrame.copy(deep=True)
        analysisFrame.apply(pandas.to_numeric, errors='coerce')  # Fill in bad data with Not-a-Number (NaN)

        # Create lists of unique strings
        uniqueLists = []
        columnNamesList = []
        for columnName in analysisFrame.columns:
            if self.debug:
                print('Column Name : ', columnName)
                print('Column Contents : ', analysisFrame[columnName].values)
            if isinstance(analysisFrame[columnName].dtypes, str):
                columnUniqueList = analysisFrame[columnName].unique().tolist()
            else:
                columnUniqueList = None
            columnNamesList.append(columnName)
            uniqueLists.append([columnName, columnUniqueList])
        if self.debug:  # Preview data.
            print(analysisFrame.head(5))

        return (analysisFrame, analysisFrameFormat, uniqueLists, columnNamesList)

    def frameToINI(self, analysisFrame=None, sectionName='Unknown', outFolder=None, outFile='nil.ini'):
        if analysisFrame is None:
            return False
        try:
            if outFolder is None:
                outFolder = os.getcwd()
            configFilePath = os.path.join(outFolder, outFile)
            configINI = cF.ConfigParser()
            configINI.add_section(sectionName)
            for (columnName, columnData) in analysisFrame:
                if self.debug:
                    print('Column Name : ', columnName)
                    print('Column Contents : ', columnData.values)
                    print("Column Contents Length:", len(columnData.values))
                    print("Column Contents Type", type(columnData.values))
                writeList = "["
                for colIndex, colValue in enumerate(columnData):
                    writeList = f"{writeList}'{colValue}'"
                    if colIndex < len(columnData) - 1:
                        writeList = f"{writeList}, "
                writeList = f"{writeList}]"
                configINI.set(sectionName, columnName, writeList)

            if not os.path.exists(configFilePath) or os.stat(configFilePath).st_size == 0:
                with open(configFilePath, 'w') as configWritingFile:
                    configINI.write(configWritingFile)
            noErrors = True
        except ValueError as e:
            errorString = ("ERROR in {__file__} @{framePrintNo} with {ErrorFound}".format(__file__=str(__file__),
                                                                                          framePrintNo=str(
                                                                                              sys._getframe().f_lineno),
                                                                                          ErrorFound=e))
            print(errorString)
            noErrors = False
        return noErrors

    @staticmethod
    def _validNumericalFloat(inValue):
        """
        Determines if the value is a valid numerical object.
        Args:
            inValue: floating-point value

        Returns: Value in floating-point or Not-A-Number.

        """
        try:
            return numpy.float128(inValue)
        except ValueError:
            return numpy.nan

    @staticmethod
    def _calculateMean(x):
        """
        Calculates the mean in a multiplication method since division produces an infinity or NaN
        Args:
            x: Input data set. We use a data frame.

        Returns: Calculated mean for a vector data frame.

        """
        try:
            mean = numpy.float128(numpy.average(x, weights=numpy.ones_like(numpy.float128(x)) / numpy.float128(x.size)))
        except ValueError:
            mean = 0
            pass
        return mean

    def _calculateStd(self, data):
        """
        Calculates the standard deviation in a multiplication method since division produces a infinity or NaN
        Args:
            data: Input data set. We use a data frame.

        Returns: Calculated standard deviation for a vector data frame.

        """
        sd = 0
        try:
            n = numpy.float128(data.size)
            if n <= 1:
                return numpy.float128(0.0)
            # Use multiplication version of mean since numpy bug causes infinity.
            mean = self._calculateMean(data)
            sd = numpy.float128(mean)
            # Calculate standard deviation
            for el in data:
                diff = numpy.float128(el) - numpy.float128(mean)
                sd += (diff) ** 2
            points = numpy.float128(n - 1)
            sd = numpy.float128(numpy.sqrt(numpy.float128(sd) / numpy.float128(points)))
        except ValueError:
            pass
        return sd

    def _determineQuickStats(self, dataAnalysisFrame, columnName=None, multiplierSigma=3.0):
        """
        Determines stats based on a vector to get the data shape.
        Args:
            dataAnalysisFrame: Dataframe to do analysis on.
            columnName: Column name of the data frame.
            multiplierSigma: Sigma range for the stats.

        Returns: Set of stats.

        """
        meanValue = 0
        sigmaValue = 0
        sigmaRangeValue = 0
        topValue = 0
        try:
            # Clean out anomoly due to random invalid inputs.
            if (columnName is not None):
                meanValue = self._calculateMean(dataAnalysisFrame[columnName])
                if meanValue == numpy.nan:
                    meanValue = numpy.float128(1)
                sigmaValue = self._calculateStd(dataAnalysisFrame[columnName])
                if float(sigmaValue) is float(numpy.nan):
                    sigmaValue = numpy.float128(1)
                multiplier = numpy.float128(multiplierSigma)  # Stats: 1 sigma = 68%, 2 sigma = 95%, 3 sigma = 99.7
                sigmaRangeValue = (sigmaValue * multiplier)
                if float(sigmaRangeValue) is float(numpy.nan):
                    sigmaRangeValue = numpy.float128(1)
                topValue = numpy.float128(meanValue + sigmaRangeValue)
                print("Name:{} Mean= {}, Sigma= {}, {}*Sigma= {}".format(columnName,
                                                                         meanValue,
                                                                         sigmaValue,
                                                                         multiplier,
                                                                         sigmaRangeValue))
        except ValueError:
            pass
        return (meanValue, sigmaValue, sigmaRangeValue, topValue)

    def _cleanZerosForColumnInFrame(self, dataAnalysisFrame, columnName='cycles'):
        """
        Cleans the data frame with data values that are invalid. I.E. inf, NaN
        Args:
            dataAnalysisFrame: Dataframe to do analysis on.
            columnName: Column name of the data frame.

        Returns: Cleaned dataframe.

        """
        dataAnalysisCleaned = None
        try:
            # Clean out anomoly due to random invalid inputs.
            (meanValue, sigmaValue, sigmaRangeValue, topValue) = self._determineQuickStats(
                dataAnalysisFrame=dataAnalysisFrame, columnName=columnName)

            # dataAnalysisCleaned = dataAnalysisFrame[dataAnalysisFrame[columnName] != 0]
            # When the cycles are negative or zero we missed cleaning up a row.
            # logicVector = (dataAnalysisFrame[columnName] != 0)
            # dataAnalysisCleaned = dataAnalysisFrame[logicVector]
            logicVector = (dataAnalysisCleaned[columnName] >= 1)
            dataAnalysisCleaned = dataAnalysisCleaned[logicVector]

            # These timed out mean + 2 * sd
            logicVector = (dataAnalysisCleaned[columnName] < topValue)  # Data range
            dataAnalysisCleaned = dataAnalysisCleaned[logicVector]
        except ValueError:
            pass
        return dataAnalysisCleaned

    def _cleanFrame(self, dataAnalysisTemp, cleanColumn=False, columnName='cycles'):
        """

        Args:
            dataAnalysisTemp: Dataframe to do analysis on.
            cleanColumn: Flag to clean the data frame.
            columnName: Column name of the data frame.

        Returns: cleaned dataframe

        """
        try:
            replacementList = [pandas.NaT, numpy.Infinity, numpy.NINF, 'NaN', 'inf', '-inf', 'NULL']
            if cleanColumn is True:
                dataAnalysisTemp = self._cleanZerosForColumnInFrame(dataAnalysisTemp, columnName=columnName)
            dataAnalysisTemp = dataAnalysisTemp.replace(to_replace=replacementList,
                                                        value=numpy.nan)
            dataAnalysisTemp = dataAnalysisTemp.dropna()
        except ValueError:
            pass
        return dataAnalysisTemp

    @staticmethod
    def _getDataFormat():
        """
        Return the dataframe setup for the CSV file generated from server.
        Returns: dictionary data format for pandas.
        """
        dataFormat = {
            "Serial_Number": pandas.StringDtype(),
            "LogTime0": pandas.StringDtype(),  # @todo force rename
            "Id0": pandas.StringDtype(),  # @todo force rename
            "DriveId": pandas.StringDtype(),
            "JobRunId": pandas.StringDtype(),
            "LogTime1": pandas.StringDtype(),  # @todo force rename
            "Comment0": pandas.StringDtype(),  # @todo force rename
            "CriticalWarning": pandas.StringDtype(),
            "Temperature": pandas.StringDtype(),
            "AvailableSpare": pandas.StringDtype(),
            "AvailableSpareThreshold": pandas.StringDtype(),
            "PercentageUsed": pandas.StringDtype(),
            "DataUnitsReadL": pandas.StringDtype(),
            "DataUnitsReadU": pandas.StringDtype(),
            "DataUnitsWrittenL": pandas.StringDtype(),
            "DataUnitsWrittenU": pandas.StringDtype(),
            "HostReadCommandsL": pandas.StringDtype(),
            "HostReadCommandsU": pandas.StringDtype(),
            "HostWriteCommandsL": pandas.StringDtype(),
            "HostWriteCommandsU": pandas.StringDtype(),
            "ControllerBusyTimeL": pandas.StringDtype(),
            "ControllerBusyTimeU": pandas.StringDtype(),
            "PowerCyclesL": pandas.StringDtype(),
            "PowerCyclesU": pandas.StringDtype(),
            "PowerOnHoursL": pandas.StringDtype(),
            "PowerOnHoursU": pandas.StringDtype(),
            "UnsafeShutdownsL": pandas.StringDtype(),
            "UnsafeShutdownsU": pandas.StringDtype(),
            "MediaErrorsL": pandas.StringDtype(),
            "MediaErrorsU": pandas.StringDtype(),
            "NumErrorInfoLogsL": pandas.StringDtype(),
            "NumErrorInfoLogsU": pandas.StringDtype(),
            "ProgramFailCountN": pandas.StringDtype(),
            "ProgramFailCountR": pandas.StringDtype(),
            "EraseFailCountN": pandas.StringDtype(),
            "EraseFailCountR": pandas.StringDtype(),
            "WearLevelingCountN": pandas.StringDtype(),
            "WearLevelingCountR": pandas.StringDtype(),
            "E2EErrorDetectCountN": pandas.StringDtype(),
            "E2EErrorDetectCountR": pandas.StringDtype(),
            "CRCErrorCountN": pandas.StringDtype(),
            "CRCErrorCountR": pandas.StringDtype(),
            "MediaWearPercentageN": pandas.StringDtype(),
            "MediaWearPercentageR": pandas.StringDtype(),
            "HostReadsN": pandas.StringDtype(),
            "HostReadsR": pandas.StringDtype(),
            "TimedWorkloadN": pandas.StringDtype(),
            "TimedWorkloadR": pandas.StringDtype(),
            "ThermalThrottleStatusN": pandas.StringDtype(),
            "ThermalThrottleStatusR": pandas.StringDtype(),
            "RetryBuffOverflowCountN": pandas.StringDtype(),
            "RetryBuffOverflowCountR": pandas.StringDtype(),
            "PLLLockLossCounterN": pandas.StringDtype(),
            "PLLLockLossCounterR": pandas.StringDtype(),
            "NandBytesWrittenN": pandas.StringDtype(),
            "NandBytesWrittenR": pandas.StringDtype(),
            "HostBytesWrittenN": pandas.StringDtype(),
            "HostBytesWrittenR": pandas.StringDtype(),
            "SystemAreaLifeRemainingN": pandas.StringDtype(),
            "SystemAreaLifeRemainingR": pandas.StringDtype(),
            "RelocatableSectorCountN": pandas.StringDtype(),
            "RelocatableSectorCountR": pandas.StringDtype(),
            "SoftECCErrorRateN": pandas.StringDtype(),
            "SoftECCErrorRateR": pandas.StringDtype(),
            "UnexpectedPowerLossN": pandas.StringDtype(),
            "UnexpectedPowerLossR": pandas.StringDtype(),
            "MediaErrorCountN": pandas.StringDtype(),
            "MediaErrorCountR": pandas.StringDtype(),
            "NandBytesReadN": pandas.StringDtype(),
            "NandBytesReadR": pandas.StringDtype(),
            "WarningCompTempTime": pandas.StringDtype(),
            "CriticalCompTempTime": pandas.StringDtype(),
            "TempSensor1": pandas.StringDtype(),
            "TempSensor2": pandas.StringDtype(),
            "TempSensor3": pandas.StringDtype(),
            "TempSensor4": pandas.StringDtype(),
            "TempSensor5": pandas.StringDtype(),
            "TempSensor6": pandas.StringDtype(),
            "TempSensor7": pandas.StringDtype(),
            "TempSensor8": pandas.StringDtype(),
            "ThermalManagementTemp1TransitionCount": pandas.StringDtype(),
            "ThermalManagementTemp2TransitionCount": pandas.StringDtype(),
            "TotalTimeForThermalManagementTemp1": pandas.StringDtype(),
            "TotalTimeForThermalManagementTemp2": pandas.StringDtype(),
            "Core_Num": pandas.StringDtype(),
            "Id1": pandas.StringDtype(),  # @todo force rename
            "Job_Run_Id": pandas.StringDtype(),
            "Stats_Time": pandas.StringDtype(),
            "HostReads": pandas.StringDtype(),
            "HostWrites": pandas.StringDtype(),
            "NandReads": pandas.StringDtype(),
            "NandWrites": pandas.StringDtype(),
            "ProgramErrors": pandas.StringDtype(),
            "EraseErrors": pandas.StringDtype(),
            "ErrorCount": pandas.StringDtype(),
            "BitErrorsHost1": pandas.StringDtype(),
            "BitErrorsHost2": pandas.StringDtype(),
            "BitErrorsHost3": pandas.StringDtype(),
            "BitErrorsHost4": pandas.StringDtype(),
            "BitErrorsHost5": pandas.StringDtype(),
            "BitErrorsHost6": pandas.StringDtype(),
            "BitErrorsHost7": pandas.StringDtype(),
            "BitErrorsHost8": pandas.StringDtype(),
            "BitErrorsHost9": pandas.StringDtype(),
            "BitErrorsHost10": pandas.StringDtype(),
            "BitErrorsHost11": pandas.StringDtype(),
            "BitErrorsHost12": pandas.StringDtype(),
            "BitErrorsHost13": pandas.StringDtype(),
            "BitErrorsHost14": pandas.StringDtype(),
            "BitErrorsHost15": pandas.StringDtype(),
            "ECCFail": pandas.StringDtype(),
            "GrownDefects": pandas.StringDtype(),
            "FreeMemory": pandas.StringDtype(),
            "WriteAllowance": pandas.StringDtype(),
            "ModelString": pandas.StringDtype(),
            "ValidBlocks": pandas.StringDtype(),
            "TokenBlocks": pandas.StringDtype(),
            "SpuriousPFCount": pandas.StringDtype(),
            "SpuriousPFLocations1": pandas.StringDtype(),
            "SpuriousPFLocations2": pandas.StringDtype(),
            "SpuriousPFLocations3": pandas.StringDtype(),
            "SpuriousPFLocations4": pandas.StringDtype(),
            "SpuriousPFLocations5": pandas.StringDtype(),
            "SpuriousPFLocations6": pandas.StringDtype(),
            "SpuriousPFLocations7": pandas.StringDtype(),
            "SpuriousPFLocations8": pandas.StringDtype(),
            "BitErrorsNonHost1": pandas.StringDtype(),
            "BitErrorsNonHost2": pandas.StringDtype(),
            "BitErrorsNonHost3": pandas.StringDtype(),
            "BitErrorsNonHost4": pandas.StringDtype(),
            "BitErrorsNonHost5": pandas.StringDtype(),
            "BitErrorsNonHost6": pandas.StringDtype(),
            "BitErrorsNonHost7": pandas.StringDtype(),
            "BitErrorsNonHost8": pandas.StringDtype(),
            "BitErrorsNonHost9": pandas.StringDtype(),
            "BitErrorsNonHost10": pandas.StringDtype(),
            "BitErrorsNonHost11": pandas.StringDtype(),
            "BitErrorsNonHost12": pandas.StringDtype(),
            "BitErrorsNonHost13": pandas.StringDtype(),
            "BitErrorsNonHost14": pandas.StringDtype(),
            "BitErrorsNonHost15": pandas.StringDtype(),
            "ECCFailNonHost": pandas.StringDtype(),
            "NSversion": pandas.StringDtype(),
            "numBands": pandas.StringDtype(),
            "minErase": pandas.StringDtype(),
            "maxErase": pandas.StringDtype(),
            "avgErase": pandas.StringDtype(),
            "minMVolt": pandas.StringDtype(),
            "maxMVolt": pandas.StringDtype(),
            "avgMVolt": pandas.StringDtype(),
            "minMAmp": pandas.StringDtype(),
            "maxMAmp": pandas.StringDtype(),
            "avgMAmp": pandas.StringDtype(),
            "comment1": pandas.StringDtype(),  # @todo force rename
            "minMVolt12v": pandas.StringDtype(),
            "maxMVolt12v": pandas.StringDtype(),
            "avgMVolt12v": pandas.StringDtype(),
            "minMAmp12v": pandas.StringDtype(),
            "maxMAmp12v": pandas.StringDtype(),
            "avgMAmp12v": pandas.StringDtype(),
            "nearMissSector": pandas.StringDtype(),
            "nearMissDefect": pandas.StringDtype(),
            "nearMissOverflow": pandas.StringDtype(),
            "replayUNC": pandas.StringDtype(),
            "Drive_Id": pandas.StringDtype(),
            "indirectionMisses": pandas.StringDtype(),
            "BitErrorsHost16": pandas.StringDtype(),
            "BitErrorsHost17": pandas.StringDtype(),
            "BitErrorsHost18": pandas.StringDtype(),
            "BitErrorsHost19": pandas.StringDtype(),
            "BitErrorsHost20": pandas.StringDtype(),
            "BitErrorsHost21": pandas.StringDtype(),
            "BitErrorsHost22": pandas.StringDtype(),
            "BitErrorsHost23": pandas.StringDtype(),
            "BitErrorsHost24": pandas.StringDtype(),
            "BitErrorsHost25": pandas.StringDtype(),
            "BitErrorsHost26": pandas.StringDtype(),
            "BitErrorsHost27": pandas.StringDtype(),
            "BitErrorsHost28": pandas.StringDtype(),
            "BitErrorsHost29": pandas.StringDtype(),
            "BitErrorsHost30": pandas.StringDtype(),
            "BitErrorsHost31": pandas.StringDtype(),
            "BitErrorsHost32": pandas.StringDtype(),
            "BitErrorsHost33": pandas.StringDtype(),
            "BitErrorsHost34": pandas.StringDtype(),
            "BitErrorsHost35": pandas.StringDtype(),
            "BitErrorsHost36": pandas.StringDtype(),
            "BitErrorsHost37": pandas.StringDtype(),
            "BitErrorsHost38": pandas.StringDtype(),
            "BitErrorsHost39": pandas.StringDtype(),
            "BitErrorsHost40": pandas.StringDtype(),
            "XORRebuildSuccess": pandas.StringDtype(),
            "XORRebuildFail": pandas.StringDtype(),
            "BandReloForError": pandas.StringDtype(),
            "mrrSuccess": pandas.StringDtype(),
            "mrrFail": pandas.StringDtype(),
            "mrrNudgeSuccess": pandas.StringDtype(),
            "mrrNudgeHarmless": pandas.StringDtype(),
            "mrrNudgeFail": pandas.StringDtype(),
            "totalErases": pandas.StringDtype(),
            "dieOfflineCount": pandas.StringDtype(),
            "curtemp": pandas.StringDtype(),
            "mintemp": pandas.StringDtype(),
            "maxtemp": pandas.StringDtype(),
            "oventemp": pandas.StringDtype(),
            "allZeroSectors": pandas.StringDtype(),
            "ctxRecoveryEvents": pandas.StringDtype(),
            "ctxRecoveryErases": pandas.StringDtype(),
            "NSversionMinor": pandas.StringDtype(),
            "lifeMinTemp": pandas.StringDtype(),
            "lifeMaxTemp": pandas.StringDtype(),
            "powerCycles": pandas.StringDtype(),
            "systemReads": pandas.StringDtype(),
            "systemWrites": pandas.StringDtype(),
            "readRetryOverflow": pandas.StringDtype(),
            "unplannedPowerCycles": pandas.StringDtype(),
            "unsafeShutdowns": pandas.StringDtype(),
            "defragForcedReloCount": pandas.StringDtype(),
            "bandReloForBDR": pandas.StringDtype(),
            "bandReloForDieOffline": pandas.StringDtype(),
            "bandReloForPFail": pandas.StringDtype(),
            "bandReloForWL": pandas.StringDtype(),
            "provisionalDefects": pandas.StringDtype(),
            "uncorrectableProgErrors": pandas.StringDtype(),
            "powerOnSeconds": pandas.StringDtype(),
            "bandReloForChannelTimeout": pandas.StringDtype(),
            "fwDowngradeCount": pandas.StringDtype(),
            "dramCorrectablesTotal": pandas.StringDtype(),
            "hb_id": pandas.StringDtype(),
            "dramCorrectables1to1": pandas.StringDtype(),
            "dramCorrectables4to1": pandas.StringDtype(),
            "dramCorrectablesSram": pandas.StringDtype(),
            "dramCorrectablesUnknown": pandas.StringDtype(),
            "pliCapTestInterval": pandas.StringDtype(),
            "pliCapTestCount": pandas.StringDtype(),
            "pliCapTestResult": pandas.StringDtype(),
            "pliCapTestTimeStamp": pandas.StringDtype(),
            "channelHangSuccess": pandas.StringDtype(),
            "channelHangFail": pandas.StringDtype(),
            "BitErrorsHost41": pandas.StringDtype(),
            "BitErrorsHost42": pandas.StringDtype(),
            "BitErrorsHost43": pandas.StringDtype(),
            "BitErrorsHost44": pandas.StringDtype(),
            "BitErrorsHost45": pandas.StringDtype(),
            "BitErrorsHost46": pandas.StringDtype(),
            "BitErrorsHost47": pandas.StringDtype(),
            "BitErrorsHost48": pandas.StringDtype(),
            "BitErrorsHost49": pandas.StringDtype(),
            "BitErrorsHost50": pandas.StringDtype(),
            "BitErrorsHost51": pandas.StringDtype(),
            "BitErrorsHost52": pandas.StringDtype(),
            "BitErrorsHost53": pandas.StringDtype(),
            "BitErrorsHost54": pandas.StringDtype(),
            "BitErrorsHost55": pandas.StringDtype(),
            "BitErrorsHost56": pandas.StringDtype(),
            "mrrNearMiss": pandas.StringDtype(),
            "mrrRereadAvg": pandas.StringDtype(),
            "readDisturbEvictions": pandas.StringDtype(),
            "L1L2ParityError": pandas.StringDtype(),
            "pageDefects": pandas.StringDtype(),
            "pageProvisionalTotal": pandas.StringDtype(),
            "ASICTemp": pandas.StringDtype(),
            "PMICTemp": pandas.StringDtype(),
            "size": pandas.StringDtype(),
            "lastWrite": pandas.StringDtype(),
            "timesWritten": pandas.StringDtype(),
            "maxNumContextBands": pandas.StringDtype(),
            "blankCount": pandas.StringDtype(),
            "cleanBands": pandas.StringDtype(),
            "avgTprog": pandas.StringDtype(),
            "avgEraseCount": pandas.StringDtype(),
            "edtcHandledBandCnt": pandas.StringDtype(),
            "bandReloForNLBA": pandas.StringDtype(),
            "bandCrossingDuringPliCount": pandas.StringDtype(),
            "bitErrBucketNum": pandas.StringDtype(),
            "sramCorrectablesTotal": pandas.StringDtype(),
            "l1SramCorrErrCnt": pandas.StringDtype(),
            "l2SramCorrErrCnt": pandas.StringDtype(),
            "parityErrorValue": pandas.StringDtype(),
            "parityErrorType": pandas.StringDtype(),
            "mrr_LutValidDataSize": pandas.StringDtype(),
            "pageProvisionalDefects": pandas.StringDtype(),
            "plisWithErasesInProgress": pandas.StringDtype(),
            "lastReplayDebug": pandas.StringDtype(),
            "externalPreReadFatals": pandas.StringDtype(),
            "hostReadCmd": pandas.StringDtype(),
            "hostWriteCmd": pandas.StringDtype(),
            "trimmedSectors": pandas.StringDtype(),
            "trimTokens": pandas.StringDtype(),
            "mrrEventsInCodewords": pandas.StringDtype(),
            "mrrEventsInSectors": pandas.StringDtype(),
            "powerOnMicroseconds": pandas.StringDtype(),
            "mrrInXorRecEvents": pandas.StringDtype(),
            "mrrFailInXorRecEvents": pandas.StringDtype(),
            "mrrUpperpageEvents": pandas.StringDtype(),
            "mrrLowerpageEvents": pandas.StringDtype(),
            "mrrSlcpageEvents": pandas.StringDtype(),
            "mrrReReadTotal": pandas.StringDtype(),
            "powerOnResets": pandas.StringDtype(),
            "powerOnMinutes": pandas.StringDtype(),
            "throttleOnMilliseconds": pandas.StringDtype(),
            "ctxTailMagic": pandas.StringDtype(),
            "contextDropCount": pandas.StringDtype(),
            "lastCtxSequenceId": pandas.StringDtype(),
            "currCtxSequenceId": pandas.StringDtype(),
            "mbliEraseCount": pandas.StringDtype(),
            "pageAverageProgramCount": pandas.StringDtype(),
            "bandAverageEraseCount": pandas.StringDtype(),
            "bandTotalEraseCount": pandas.StringDtype(),
            "bandReloForXorRebuildFail": pandas.StringDtype(),
            "defragSpeculativeMiss": pandas.StringDtype(),
            "uncorrectableBackgroundScan": pandas.StringDtype(),
            "BitErrorsHost57": pandas.StringDtype(),
            "BitErrorsHost58": pandas.StringDtype(),
            "BitErrorsHost59": pandas.StringDtype(),
            "BitErrorsHost60": pandas.StringDtype(),
            "BitErrorsHost61": pandas.StringDtype(),
            "BitErrorsHost62": pandas.StringDtype(),
            "BitErrorsHost63": pandas.StringDtype(),
            "BitErrorsHost64": pandas.StringDtype(),
            "BitErrorsHost65": pandas.StringDtype(),
            "BitErrorsHost66": pandas.StringDtype(),
            "BitErrorsHost67": pandas.StringDtype(),
            "BitErrorsHost68": pandas.StringDtype(),
            "BitErrorsHost69": pandas.StringDtype(),
            "BitErrorsHost70": pandas.StringDtype(),
            "BitErrorsHost71": pandas.StringDtype(),
            "BitErrorsHost72": pandas.StringDtype(),
            "BitErrorsHost73": pandas.StringDtype(),
            "BitErrorsHost74": pandas.StringDtype(),
            "BitErrorsHost75": pandas.StringDtype(),
            "BitErrorsHost76": pandas.StringDtype(),
            "BitErrorsHost77": pandas.StringDtype(),
            "BitErrorsHost78": pandas.StringDtype(),
            "BitErrorsHost79": pandas.StringDtype(),
            "BitErrorsHost80": pandas.StringDtype(),
            "bitErrBucketArray1": pandas.StringDtype(),
            "bitErrBucketArray2": pandas.StringDtype(),
            "bitErrBucketArray3": pandas.StringDtype(),
            "bitErrBucketArray4": pandas.StringDtype(),
            "bitErrBucketArray5": pandas.StringDtype(),
            "bitErrBucketArray6": pandas.StringDtype(),
            "bitErrBucketArray7": pandas.StringDtype(),
            "bitErrBucketArray8": pandas.StringDtype(),
            "bitErrBucketArray9": pandas.StringDtype(),
            "bitErrBucketArray10": pandas.StringDtype(),
            "bitErrBucketArray11": pandas.StringDtype(),
            "bitErrBucketArray12": pandas.StringDtype(),
            "bitErrBucketArray13": pandas.StringDtype(),
            "bitErrBucketArray14": pandas.StringDtype(),
            "bitErrBucketArray15": pandas.StringDtype(),
            "bitErrBucketArray16": pandas.StringDtype(),
            "bitErrBucketArray17": pandas.StringDtype(),
            "bitErrBucketArray18": pandas.StringDtype(),
            "bitErrBucketArray19": pandas.StringDtype(),
            "bitErrBucketArray20": pandas.StringDtype(),
            "bitErrBucketArray21": pandas.StringDtype(),
            "bitErrBucketArray22": pandas.StringDtype(),
            "bitErrBucketArray23": pandas.StringDtype(),
            "bitErrBucketArray24": pandas.StringDtype(),
            "bitErrBucketArray25": pandas.StringDtype(),
            "bitErrBucketArray26": pandas.StringDtype(),
            "bitErrBucketArray27": pandas.StringDtype(),
            "bitErrBucketArray28": pandas.StringDtype(),
            "bitErrBucketArray29": pandas.StringDtype(),
            "bitErrBucketArray30": pandas.StringDtype(),
            "bitErrBucketArray31": pandas.StringDtype(),
            "bitErrBucketArray32": pandas.StringDtype(),
            "bitErrBucketArray33": pandas.StringDtype(),
            "bitErrBucketArray34": pandas.StringDtype(),
            "bitErrBucketArray35": pandas.StringDtype(),
            "bitErrBucketArray36": pandas.StringDtype(),
            "bitErrBucketArray37": pandas.StringDtype(),
            "bitErrBucketArray38": pandas.StringDtype(),
            "bitErrBucketArray39": pandas.StringDtype(),
            "bitErrBucketArray40": pandas.StringDtype(),
            "bitErrBucketArray41": pandas.StringDtype(),
            "bitErrBucketArray42": pandas.StringDtype(),
            "bitErrBucketArray43": pandas.StringDtype(),
            "bitErrBucketArray44": pandas.StringDtype(),
            "bitErrBucketArray45": pandas.StringDtype(),
            "bitErrBucketArray46": pandas.StringDtype(),
            "bitErrBucketArray47": pandas.StringDtype(),
            "bitErrBucketArray48": pandas.StringDtype(),
            "bitErrBucketArray49": pandas.StringDtype(),
            "bitErrBucketArray50": pandas.StringDtype(),
            "bitErrBucketArray51": pandas.StringDtype(),
            "bitErrBucketArray52": pandas.StringDtype(),
            "bitErrBucketArray53": pandas.StringDtype(),
            "bitErrBucketArray54": pandas.StringDtype(),
            "bitErrBucketArray55": pandas.StringDtype(),
            "bitErrBucketArray56": pandas.StringDtype(),
            "bitErrBucketArray57": pandas.StringDtype(),
            "bitErrBucketArray58": pandas.StringDtype(),
            "bitErrBucketArray59": pandas.StringDtype(),
            "bitErrBucketArray60": pandas.StringDtype(),
            "bitErrBucketArray61": pandas.StringDtype(),
            "bitErrBucketArray62": pandas.StringDtype(),
            "bitErrBucketArray63": pandas.StringDtype(),
            "bitErrBucketArray64": pandas.StringDtype(),
            "bitErrBucketArray65": pandas.StringDtype(),
            "bitErrBucketArray66": pandas.StringDtype(),
            "bitErrBucketArray67": pandas.StringDtype(),
            "bitErrBucketArray68": pandas.StringDtype(),
            "bitErrBucketArray69": pandas.StringDtype(),
            "bitErrBucketArray70": pandas.StringDtype(),
            "bitErrBucketArray71": pandas.StringDtype(),
            "bitErrBucketArray72": pandas.StringDtype(),
            "bitErrBucketArray73": pandas.StringDtype(),
            "bitErrBucketArray74": pandas.StringDtype(),
            "bitErrBucketArray75": pandas.StringDtype(),
            "bitErrBucketArray76": pandas.StringDtype(),
            "bitErrBucketArray77": pandas.StringDtype(),
            "bitErrBucketArray78": pandas.StringDtype(),
            "bitErrBucketArray79": pandas.StringDtype(),
            "bitErrBucketArray80": pandas.StringDtype(),
            "mrr_successDistribution1": pandas.StringDtype(),
            "mrr_successDistribution2": pandas.StringDtype(),
            "mrr_successDistribution3": pandas.StringDtype(),
            "mrr_successDistribution4": pandas.StringDtype(),
            "mrr_successDistribution5": pandas.StringDtype(),
            "mrr_successDistribution6": pandas.StringDtype(),
            "mrr_successDistribution7": pandas.StringDtype(),
            "mrr_successDistribution8": pandas.StringDtype(),
            "mrr_successDistribution9": pandas.StringDtype(),
            "mrr_successDistribution10": pandas.StringDtype(),
            "mrr_successDistribution11": pandas.StringDtype(),
            "mrr_successDistribution12": pandas.StringDtype(),
            "mrr_successDistribution13": pandas.StringDtype(),
            "mrr_successDistribution14": pandas.StringDtype(),
            "mrr_successDistribution15": pandas.StringDtype(),
            "mrr_successDistribution16": pandas.StringDtype(),
            "mrr_successDistribution17": pandas.StringDtype(),
            "mrr_successDistribution18": pandas.StringDtype(),
            "mrr_successDistribution19": pandas.StringDtype(),
            "mrr_successDistribution20": pandas.StringDtype(),
            "mrr_successDistribution21": pandas.StringDtype(),
            "mrr_successDistribution22": pandas.StringDtype(),
            "mrr_successDistribution23": pandas.StringDtype(),
            "mrr_successDistribution24": pandas.StringDtype(),
            "mrr_successDistribution25": pandas.StringDtype(),
            "mrr_successDistribution26": pandas.StringDtype(),
            "mrr_successDistribution27": pandas.StringDtype(),
            "mrr_successDistribution28": pandas.StringDtype(),
            "mrr_successDistribution29": pandas.StringDtype(),
            "mrr_successDistribution30": pandas.StringDtype(),
            "mrr_successDistribution31": pandas.StringDtype(),
            "mrr_successDistribution32": pandas.StringDtype(),
            "mrr_successDistribution33": pandas.StringDtype(),
            "mrr_successDistribution34": pandas.StringDtype(),
            "mrr_successDistribution35": pandas.StringDtype(),
            "mrr_successDistribution36": pandas.StringDtype(),
            "mrr_successDistribution37": pandas.StringDtype(),
            "mrr_successDistribution38": pandas.StringDtype(),
            "mrr_successDistribution39": pandas.StringDtype(),
            "mrr_successDistribution40": pandas.StringDtype(),
            "mrr_successDistribution41": pandas.StringDtype(),
            "mrr_successDistribution42": pandas.StringDtype(),
            "mrr_successDistribution43": pandas.StringDtype(),
            "mrr_successDistribution44": pandas.StringDtype(),
            "mrr_successDistribution45": pandas.StringDtype(),
            "mrr_successDistribution46": pandas.StringDtype(),
            "mrr_successDistribution47": pandas.StringDtype(),
            "mrr_successDistribution48": pandas.StringDtype(),
            "mrr_successDistribution49": pandas.StringDtype(),
            "mrr_successDistribution50": pandas.StringDtype(),
            "mrr_successDistribution51": pandas.StringDtype(),
            "mrr_successDistribution52": pandas.StringDtype(),
            "mrr_successDistribution53": pandas.StringDtype(),
            "mrr_successDistribution54": pandas.StringDtype(),
            "mrr_successDistribution55": pandas.StringDtype(),
            "mrr_successDistribution56": pandas.StringDtype(),
            "mrr_successDistribution57": pandas.StringDtype(),
            "mrr_successDistribution58": pandas.StringDtype(),
            "mrr_successDistribution59": pandas.StringDtype(),
            "mrr_successDistribution60": pandas.StringDtype(),
            "mrr_successDistribution61": pandas.StringDtype(),
            "mrr_successDistribution62": pandas.StringDtype(),
            "mrr_successDistribution63": pandas.StringDtype(),
            "mrr_successDistribution64": pandas.StringDtype(),
            "blDowngradeCount": pandas.StringDtype(),
            "snapReads": pandas.StringDtype(),
            "pliCapTestTime": pandas.StringDtype(),
            "currentTimeToFreeSpaceRecovery": pandas.StringDtype(),
            "worstTimeToFreeSpaceRecovery": pandas.StringDtype(),
            "rspnandReads": pandas.StringDtype(),
            "cachednandReads": pandas.StringDtype(),
            "spnandReads": pandas.StringDtype(),
            "dpnandReads": pandas.StringDtype(),
            "qpnandReads": pandas.StringDtype(),
            "verifynandReads": pandas.StringDtype(),
            "softnandReads": pandas.StringDtype(),
            "spnandWrites": pandas.StringDtype(),
            "dpnandWrites": pandas.StringDtype(),
            "qpnandWrites": pandas.StringDtype(),
            "opnandWrites": pandas.StringDtype(),
            "xpnandWrites": pandas.StringDtype(),
            "unalignedHostWriteCmd": pandas.StringDtype(),
            "randomReadCmd": pandas.StringDtype(),
            "randomWriteCmd": pandas.StringDtype(),
            "secVenCmdCount": pandas.StringDtype(),
            "secVenCmdCountFails": pandas.StringDtype(),
            "mrrFailOnSlcOtfPages": pandas.StringDtype(),
            "mrrFailOnSlcOtfPageMarkedAsMBPD": pandas.StringDtype(),
            "lcorParitySeedErrors": pandas.StringDtype(),
            "fwDownloadFails": pandas.StringDtype(),
            "fwAuthenticationFails": pandas.StringDtype(),
            "fwSecurityRev": pandas.StringDtype(),
            "isCapacitorHealthly": pandas.StringDtype(),
            "fwWRCounter": pandas.StringDtype(),
            "sysAreaEraseFailCount": pandas.StringDtype(),
            "iusDefragRelocated4DataRetention": pandas.StringDtype(),
            "I2CTemp": pandas.StringDtype(),
            "lbaMismatchOnNandReads": pandas.StringDtype(),
            "currentWriteStreamsCount": pandas.StringDtype(),
            "nandWritesPerStream1": pandas.StringDtype(),
            "nandWritesPerStream2": pandas.StringDtype(),
            "nandWritesPerStream3": pandas.StringDtype(),
            "nandWritesPerStream4": pandas.StringDtype(),
            "nandWritesPerStream5": pandas.StringDtype(),
            "nandWritesPerStream6": pandas.StringDtype(),
            "nandWritesPerStream7": pandas.StringDtype(),
            "nandWritesPerStream8": pandas.StringDtype(),
            "nandWritesPerStream9": pandas.StringDtype(),
            "nandWritesPerStream10": pandas.StringDtype(),
            "nandWritesPerStream11": pandas.StringDtype(),
            "nandWritesPerStream12": pandas.StringDtype(),
            "nandWritesPerStream13": pandas.StringDtype(),
            "nandWritesPerStream14": pandas.StringDtype(),
            "nandWritesPerStream15": pandas.StringDtype(),
            "nandWritesPerStream16": pandas.StringDtype(),
            "nandWritesPerStream17": pandas.StringDtype(),
            "nandWritesPerStream18": pandas.StringDtype(),
            "nandWritesPerStream19": pandas.StringDtype(),
            "nandWritesPerStream20": pandas.StringDtype(),
            "nandWritesPerStream21": pandas.StringDtype(),
            "nandWritesPerStream22": pandas.StringDtype(),
            "nandWritesPerStream23": pandas.StringDtype(),
            "nandWritesPerStream24": pandas.StringDtype(),
            "nandWritesPerStream25": pandas.StringDtype(),
            "nandWritesPerStream26": pandas.StringDtype(),
            "nandWritesPerStream27": pandas.StringDtype(),
            "nandWritesPerStream28": pandas.StringDtype(),
            "nandWritesPerStream29": pandas.StringDtype(),
            "nandWritesPerStream30": pandas.StringDtype(),
            "nandWritesPerStream31": pandas.StringDtype(),
            "nandWritesPerStream32": pandas.StringDtype(),
            "hostSoftReadSuccess": pandas.StringDtype(),
            "xorInvokedCount": pandas.StringDtype(),
            "comresets": pandas.StringDtype(),
            "syncEscapes": pandas.StringDtype(),
            "rErrHost": pandas.StringDtype(),
            "rErrDevice": pandas.StringDtype(),
            "iCrcs": pandas.StringDtype(),
            "linkSpeedDrops": pandas.StringDtype(),
            "mrrXtrapageEvents": pandas.StringDtype(),
            "mrrToppageEvents": pandas.StringDtype(),
            "hostXorSuccessCount": pandas.StringDtype(),
            "hostXorFailCount": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream1": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream2": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream3": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream4": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream5": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream6": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream7": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream8": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream9": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream10": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream11": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream12": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream13": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream14": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream15": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream16": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream17": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream18": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream19": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream20": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream21": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream22": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream23": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream24": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream25": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream26": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream27": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream28": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream29": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream30": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream31": pandas.StringDtype(),
            "nandWritesWithPreReadPerStream32": pandas.StringDtype(),
            "dramCorrectables8to1": pandas.StringDtype(),
            "driveRecoveryCount": pandas.StringDtype(),
            "mprLiteReads": pandas.StringDtype(),
            "eccErrOnMprLiteReads": pandas.StringDtype(),
            "readForwardingXpPreReadCount": pandas.StringDtype(),
            "readForwardingUpPreReadCount": pandas.StringDtype(),
            "readForwardingLpPreReadCount": pandas.StringDtype(),
            "pweDefectCompensationCredit": pandas.StringDtype(),
            "planarXorRebuildFailure": pandas.StringDtype(),
            "itgXorRebuildFailure": pandas.StringDtype(),
            "planarXorRebuildSuccess": pandas.StringDtype(),
            "itgXorRebuildSuccess": pandas.StringDtype(),
            "xorLoggingSkippedSIcBand": pandas.StringDtype(),
            "xorLoggingSkippedDieOffline": pandas.StringDtype(),
            "xorLoggingSkippedDieAbsent": pandas.StringDtype(),
            "xorLoggingSkippedBandErased": pandas.StringDtype(),
            "xorLoggingSkippedNoEntry": pandas.StringDtype(),
            "xorAuditSuccess": pandas.StringDtype(),
            "maxSuspendCount": pandas.StringDtype(),
            "suspendLimitPerPrgm": pandas.StringDtype(),
            "psrCountStats": pandas.StringDtype(),
            "readNandBuffCount": pandas.StringDtype(),
            "readNandBufferRspErrorCount": pandas.StringDtype(),
            "ddpNandWrites": pandas.StringDtype(),
            "totalDeallocatedSectorsInCore": pandas.StringDtype(),
            "prefetchHostReads": pandas.StringDtype(),
            "hostReadtoDSMDCount": pandas.StringDtype(),
            "hostWritetoDSMDCount": pandas.StringDtype(),
            "snapReads4k": pandas.StringDtype(),
            "snapReads8k": pandas.StringDtype(),
            "snapReads16k": pandas.StringDtype(),
            "xorLoggingTriggered": pandas.StringDtype(),
            "xorLoggingAborted": pandas.StringDtype(),
            "xorLoggingSkippedHistory": pandas.StringDtype(),
            "deckDisturbRelocationUD": pandas.StringDtype(),
            "deckDisturbRelocationMD": pandas.StringDtype(),
            "deckDisturbRelocationLD": pandas.StringDtype(),
            "bbdProactiveReadRetry": pandas.StringDtype(),
            "statsRestoreRequired": pandas.StringDtype(),
            "statsAESCount": pandas.StringDtype(),
            "statsHESCount": pandas.StringDtype(),
            "psrCountStats1": pandas.StringDtype(),
            "psrCountStats2": pandas.StringDtype(),
            "psrCountStats3": pandas.StringDtype(),
            "psrCountStats4": pandas.StringDtype(),
            "psrCountStats5": pandas.StringDtype(),
            "psrCountStats6": pandas.StringDtype(),
            "psrCountStats7": pandas.StringDtype(),
            "psrCountStats8": pandas.StringDtype(),
            "psrCountStats9": pandas.StringDtype(),
            "psrCountStats10": pandas.StringDtype(),
            "psrCountStats11": pandas.StringDtype(),
            "psrCountStats12": pandas.StringDtype(),
            "psrCountStats13": pandas.StringDtype(),
            "psrCountStats14": pandas.StringDtype(),
            "psrCountStats15": pandas.StringDtype(),
            "psrCountStats16": pandas.StringDtype(),
            "psrCountStats17": pandas.StringDtype(),
            "psrCountStats18": pandas.StringDtype(),
            "psrCountStats19": pandas.StringDtype(),
            "psrCountStats20": pandas.StringDtype(),
            "psrCountStats21": pandas.StringDtype(),
            "psrCountStats22": pandas.StringDtype(),
            "psrCountStats23": pandas.StringDtype(),
            "psrCountStats24": pandas.StringDtype(),
            "psrCountStats25": pandas.StringDtype(),
            "psrCountStats26": pandas.StringDtype(),
            "psrCountStats27": pandas.StringDtype(),
            "psrCountStats28": pandas.StringDtype(),
            "psrCountStats29": pandas.StringDtype(),
            "psrCountStats30": pandas.StringDtype(),
            "psrCountStats31": pandas.StringDtype(),
            "psrCountStats32": pandas.StringDtype(),
            "psrCountStats33": pandas.StringDtype(),
            "psrCountStats34": pandas.StringDtype(),
            "psrCountStats35": pandas.StringDtype(),
            "psrCountStats36": pandas.StringDtype(),
            "psrCountStats37": pandas.StringDtype(),
            "psrCountStats38": pandas.StringDtype(),
            "psrCountStats39": pandas.StringDtype(),
            "psrCountStats40": pandas.StringDtype(),
            "psrCountStats41": pandas.StringDtype(),
            "psrCountStats42": pandas.StringDtype(),
            "psrCountStats43": pandas.StringDtype(),
            "psrCountStats44": pandas.StringDtype(),
            "psrCountStats45": pandas.StringDtype(),
            "psrCountStats46": pandas.StringDtype(),
            "psrCountStatsHigh1": pandas.StringDtype(),
            "psrCountStatsHigh2": pandas.StringDtype(),
            "psrCountStatsHigh3": pandas.StringDtype(),
            "psrCountStatsHigh4": pandas.StringDtype(),
            "psrCountStatsHigh5": pandas.StringDtype(),
            "psrCountStatsHigh6": pandas.StringDtype(),
            "psrCountStatsHigh7": pandas.StringDtype(),
            "psrCountStatsHigh8": pandas.StringDtype(),
            "psrCountStatsHigh9": pandas.StringDtype(),
            "psrCountStatsHigh10": pandas.StringDtype(),
            "psrCountStatsHigh11": pandas.StringDtype(),
            "psrCountStatsHigh12": pandas.StringDtype(),
            "psrCountStatsHigh13": pandas.StringDtype(),
            "psrCountStatsHigh14": pandas.StringDtype(),
            "vssSwitchCount": pandas.StringDtype(),
            "openBandReadCount": pandas.StringDtype(),
            "closedBandReadCount": pandas.StringDtype(),
            "minEraseSLC": pandas.StringDtype(),
            "maxEraseSLC": pandas.StringDtype(),
            "avgEraseSLC": pandas.StringDtype(),
            "totalErasesSLC": pandas.StringDtype(),
            "unexpectedPsrStateCount": pandas.StringDtype(),
            "lowPrioritySqReadCmds": pandas.StringDtype(),
            "mediumPrioritySqReadCmds": pandas.StringDtype(),
            "highPrioritySqReadCmds": pandas.StringDtype(),
            "urgentPrioritySqReadCmds": pandas.StringDtype(),
        }
        return dataFormat

    @staticmethod
    def _getDataFormat_Origin():
        """
        Return the dataframe setup for the CSV file generated from server.
        Returns: dictionary data format for pandas.
        """
        dataFormat = {
            "Serial_Number": pandas.StringDtype(),
            "LogTime0": pandas.StringDtype(),  # @todo force rename
            "Id0": pandas.StringDtype(),  # @todo force rename
            "DriveId": numpy.int64,
            "JobRunId": numpy.int64,
            "LogTime1": pandas.StringDtype(),  # @todo force rename
            "Comment0": pandas.StringDtype(),  # @todo force rename
            "CriticalWarning": numpy.int64,
            "Temperature": numpy.int64,
            "AvailableSpare": numpy.int64,
            "AvailableSpareThreshold": numpy.int64,
            "PercentageUsed": numpy.int64,
            "DataUnitsReadL": numpy.int64,
            "DataUnitsReadU": numpy.int64,
            "DataUnitsWrittenL": numpy.int64,
            "DataUnitsWrittenU": numpy.int64,
            "HostReadCommandsL": numpy.int64,
            "HostReadCommandsU": numpy.int64,
            "HostWriteCommandsL": numpy.int64,
            "HostWriteCommandsU": numpy.int64,
            "ControllerBusyTimeL": numpy.int64,
            "ControllerBusyTimeU": numpy.int64,
            "PowerCyclesL": numpy.int64,
            "PowerCyclesU": numpy.int64,
            "PowerOnHoursL": numpy.int64,
            "PowerOnHoursU": numpy.int64,
            "UnsafeShutdownsL": numpy.int64,
            "UnsafeShutdownsU": numpy.int64,
            "MediaErrorsL": numpy.int64,
            "MediaErrorsU": numpy.int64,
            "NumErrorInfoLogsL": numpy.int64,
            "NumErrorInfoLogsU": numpy.int64,
            "ProgramFailCountN": numpy.int64,
            "ProgramFailCountR": numpy.int64,
            "EraseFailCountN": numpy.int64,
            "EraseFailCountR": numpy.int64,
            "WearLevelingCountN": numpy.int64,
            "WearLevelingCountR": numpy.int64,
            "E2EErrorDetectCountN": numpy.int64,
            "E2EErrorDetectCountR": numpy.int64,
            "CRCErrorCountN": numpy.int64,
            "CRCErrorCountR": numpy.int64,
            "MediaWearPercentageN": numpy.int64,
            "MediaWearPercentageR": numpy.int64,
            "HostReadsN": numpy.int64,
            "HostReadsR": numpy.int64,
            "TimedWorkloadN": numpy.int64,
            "TimedWorkloadR": numpy.int64,
            "ThermalThrottleStatusN": numpy.int64,
            "ThermalThrottleStatusR": numpy.int64,
            "RetryBuffOverflowCountN": numpy.int64,
            "RetryBuffOverflowCountR": numpy.int64,
            "PLLLockLossCounterN": numpy.int64,
            "PLLLockLossCounterR": numpy.int64,
            "NandBytesWrittenN": numpy.int64,
            "NandBytesWrittenR": numpy.int64,
            "HostBytesWrittenN": numpy.int64,
            "HostBytesWrittenR": numpy.int64,
            "SystemAreaLifeRemainingN": numpy.int64,
            "SystemAreaLifeRemainingR": numpy.int64,
            "RelocatableSectorCountN": numpy.int64,
            "RelocatableSectorCountR": numpy.int64,
            "SoftECCErrorRateN": numpy.int64,
            "SoftECCErrorRateR": numpy.int64,
            "UnexpectedPowerLossN": numpy.int64,
            "UnexpectedPowerLossR": numpy.int64,
            "MediaErrorCountN": numpy.int64,
            "MediaErrorCountR": numpy.int64,
            "NandBytesReadN": numpy.int64,
            "NandBytesReadR": numpy.int64,
            "WarningCompTempTime": numpy.int64,
            "CriticalCompTempTime": numpy.int64,
            "TempSensor1": numpy.int64,
            "TempSensor2": numpy.int64,
            "TempSensor3": numpy.int64,
            "TempSensor4": numpy.int64,
            "TempSensor5": numpy.int64,
            "TempSensor6": numpy.int64,
            "TempSensor7": numpy.int64,
            "TempSensor8": numpy.int64,
            "ThermalManagementTemp1TransitionCount": numpy.int64,
            "ThermalManagementTemp2TransitionCount": numpy.int64,
            "TotalTimeForThermalManagementTemp1": numpy.int64,
            "TotalTimeForThermalManagementTemp2": numpy.int64,
            "Core_Num": numpy.int64,
            "Id1": numpy.int64,  # @todo force rename
            "Job_Run_Id": numpy.int64,
            "Stats_Time": numpy.int64,
            "HostReads": numpy.int64,
            "HostWrites": numpy.int64,
            "NandReads": numpy.int64,
            "NandWrites": numpy.int64,
            "ProgramErrors": numpy.int64,
            "EraseErrors": numpy.int64,
            "ErrorCount": numpy.int64,
            "BitErrorsHost1": numpy.int64,
            "BitErrorsHost2": numpy.int64,
            "BitErrorsHost3": numpy.int64,
            "BitErrorsHost4": numpy.int64,
            "BitErrorsHost5": numpy.int64,
            "BitErrorsHost6": numpy.int64,
            "BitErrorsHost7": numpy.int64,
            "BitErrorsHost8": numpy.int64,
            "BitErrorsHost9": numpy.int64,
            "BitErrorsHost10": numpy.int64,
            "BitErrorsHost11": numpy.int64,
            "BitErrorsHost12": numpy.int64,
            "BitErrorsHost13": numpy.int64,
            "BitErrorsHost14": numpy.int64,
            "BitErrorsHost15": numpy.int64,
            "ECCFail": numpy.int64,
            "GrownDefects": numpy.int64,
            "FreeMemory": numpy.int64,
            "WriteAllowance": numpy.int64,
            "ModelString": numpy.int64,
            "ValidBlocks": numpy.int64,
            "TokenBlocks": numpy.int64,
            "SpuriousPFCount": numpy.int64,
            "SpuriousPFLocations1": numpy.int64,
            "SpuriousPFLocations2": numpy.int64,
            "SpuriousPFLocations3": numpy.int64,
            "SpuriousPFLocations4": numpy.int64,
            "SpuriousPFLocations5": numpy.int64,
            "SpuriousPFLocations6": numpy.int64,
            "SpuriousPFLocations7": numpy.int64,
            "SpuriousPFLocations8": numpy.int64,
            "BitErrorsNonHost1": numpy.int64,
            "BitErrorsNonHost2": numpy.int64,
            "BitErrorsNonHost3": numpy.int64,
            "BitErrorsNonHost4": numpy.int64,
            "BitErrorsNonHost5": numpy.int64,
            "BitErrorsNonHost6": numpy.int64,
            "BitErrorsNonHost7": numpy.int64,
            "BitErrorsNonHost8": numpy.int64,
            "BitErrorsNonHost9": numpy.int64,
            "BitErrorsNonHost10": numpy.int64,
            "BitErrorsNonHost11": numpy.int64,
            "BitErrorsNonHost12": numpy.int64,
            "BitErrorsNonHost13": numpy.int64,
            "BitErrorsNonHost14": numpy.int64,
            "BitErrorsNonHost15": numpy.int64,
            "ECCFailNonHost": numpy.int64,
            "NSversion": numpy.int64,
            "numBands": numpy.int64,
            "minErase": numpy.int64,
            "maxErase": numpy.int64,
            "avgErase": numpy.int64,
            "minMVolt": numpy.int64,
            "maxMVolt": numpy.int64,
            "avgMVolt": numpy.int64,
            "minMAmp": numpy.int64,
            "maxMAmp": numpy.int64,
            "avgMAmp": numpy.int64,
            "comment1": pandas.StringDtype(),  # @todo force rename
            "minMVolt12v": numpy.int64,
            "maxMVolt12v": numpy.int64,
            "avgMVolt12v": numpy.int64,
            "minMAmp12v": numpy.int64,
            "maxMAmp12v": numpy.int64,
            "avgMAmp12v": numpy.int64,
            "nearMissSector": numpy.int64,
            "nearMissDefect": numpy.int64,
            "nearMissOverflow": numpy.int64,
            "replayUNC": numpy.int64,
            "Drive_Id": numpy.int64,
            "indirectionMisses": numpy.int64,
            "BitErrorsHost16": numpy.int64,
            "BitErrorsHost17": numpy.int64,
            "BitErrorsHost18": numpy.int64,
            "BitErrorsHost19": numpy.int64,
            "BitErrorsHost20": numpy.int64,
            "BitErrorsHost21": numpy.int64,
            "BitErrorsHost22": numpy.int64,
            "BitErrorsHost23": numpy.int64,
            "BitErrorsHost24": numpy.int64,
            "BitErrorsHost25": numpy.int64,
            "BitErrorsHost26": numpy.int64,
            "BitErrorsHost27": numpy.int64,
            "BitErrorsHost28": numpy.int64,
            "BitErrorsHost29": numpy.int64,
            "BitErrorsHost30": numpy.int64,
            "BitErrorsHost31": numpy.int64,
            "BitErrorsHost32": numpy.int64,
            "BitErrorsHost33": numpy.int64,
            "BitErrorsHost34": numpy.int64,
            "BitErrorsHost35": numpy.int64,
            "BitErrorsHost36": numpy.int64,
            "BitErrorsHost37": numpy.int64,
            "BitErrorsHost38": numpy.int64,
            "BitErrorsHost39": numpy.int64,
            "BitErrorsHost40": numpy.int64,
            "XORRebuildSuccess": numpy.int64,
            "XORRebuildFail": numpy.int64,
            "BandReloForError": numpy.int64,
            "mrrSuccess": numpy.int64,
            "mrrFail": numpy.int64,
            "mrrNudgeSuccess": numpy.int64,
            "mrrNudgeHarmless": numpy.int64,
            "mrrNudgeFail": numpy.int64,
            "totalErases": numpy.int64,
            "dieOfflineCount": numpy.int64,
            "curtemp": numpy.int64,
            "mintemp": numpy.int64,
            "maxtemp": numpy.int64,
            "oventemp": numpy.int64,
            "allZeroSectors": numpy.int64,
            "ctxRecoveryEvents": numpy.int64,
            "ctxRecoveryErases": numpy.int64,
            "NSversionMinor": numpy.int64,
            "lifeMinTemp": numpy.int64,
            "lifeMaxTemp": numpy.int64,
            "powerCycles": numpy.int64,
            "systemReads": numpy.int64,
            "systemWrites": numpy.int64,
            "readRetryOverflow": numpy.int64,
            "unplannedPowerCycles": numpy.int64,
            "unsafeShutdowns": numpy.int64,
            "defragForcedReloCount": numpy.int64,
            "bandReloForBDR": numpy.int64,
            "bandReloForDieOffline": numpy.int64,
            "bandReloForPFail": numpy.int64,
            "bandReloForWL": numpy.int64,
            "provisionalDefects": numpy.int64,
            "uncorrectableProgErrors": numpy.int64,
            "powerOnSeconds": numpy.int64,
            "bandReloForChannelTimeout": numpy.int64,
            "fwDowngradeCount": numpy.int64,
            "dramCorrectablesTotal": numpy.int64,
            "hb_id": numpy.int64,
            "dramCorrectables1to1": numpy.int64,
            "dramCorrectables4to1": numpy.int64,
            "dramCorrectablesSram": numpy.int64,
            "dramCorrectablesUnknown": numpy.int64,
            "pliCapTestInterval": numpy.int64,
            "pliCapTestCount": numpy.int64,
            "pliCapTestResult": numpy.int64,
            "pliCapTestTimeStamp": numpy.int64,
            "channelHangSuccess": numpy.int64,
            "channelHangFail": numpy.int64,
            "BitErrorsHost41": numpy.int64,
            "BitErrorsHost42": numpy.int64,
            "BitErrorsHost43": numpy.int64,
            "BitErrorsHost44": numpy.int64,
            "BitErrorsHost45": numpy.int64,
            "BitErrorsHost46": numpy.int64,
            "BitErrorsHost47": numpy.int64,
            "BitErrorsHost48": numpy.int64,
            "BitErrorsHost49": numpy.int64,
            "BitErrorsHost50": numpy.int64,
            "BitErrorsHost51": numpy.int64,
            "BitErrorsHost52": numpy.int64,
            "BitErrorsHost53": numpy.int64,
            "BitErrorsHost54": numpy.int64,
            "BitErrorsHost55": numpy.int64,
            "BitErrorsHost56": numpy.int64,
            "mrrNearMiss": numpy.int64,
            "mrrRereadAvg": numpy.int64,
            "readDisturbEvictions": numpy.int64,
            "L1L2ParityError": numpy.int64,
            "pageDefects": numpy.int64,
            "pageProvisionalTotal": numpy.int64,
            "ASICTemp": numpy.int64,
            "PMICTemp": numpy.int64,
            "size": numpy.int64,
            "lastWrite": numpy.int64,
            "timesWritten": numpy.int64,
            "maxNumContextBands": numpy.int64,
            "blankCount": numpy.int64,
            "cleanBands": numpy.int64,
            "avgTprog": numpy.int64,
            "avgEraseCount": numpy.int64,
            "edtcHandledBandCnt": numpy.int64,
            "bandReloForNLBA": numpy.int64,
            "bandCrossingDuringPliCount": numpy.int64,
            "bitErrBucketNum": numpy.int64,
            "sramCorrectablesTotal": numpy.int64,
            "l1SramCorrErrCnt": numpy.int64,
            "l2SramCorrErrCnt": numpy.int64,
            "parityErrorValue": numpy.int64,
            "parityErrorType": numpy.int64,
            "mrr_LutValidDataSize": numpy.int64,
            "pageProvisionalDefects": numpy.int64,
            "plisWithErasesInProgress": numpy.int64,
            "lastReplayDebug": numpy.int64,
            "externalPreReadFatals": numpy.int64,
            "hostReadCmd": numpy.int64,
            "hostWriteCmd": numpy.int64,
            "trimmedSectors": numpy.int64,
            "trimTokens": numpy.int64,
            "mrrEventsInCodewords": numpy.int64,
            "mrrEventsInSectors": numpy.int64,
            "powerOnMicroseconds": numpy.int64,
            "mrrInXorRecEvents": numpy.int64,
            "mrrFailInXorRecEvents": numpy.int64,
            "mrrUpperpageEvents": numpy.int64,
            "mrrLowerpageEvents": numpy.int64,
            "mrrSlcpageEvents": numpy.int64,
            "mrrReReadTotal": numpy.int64,
            "powerOnResets": numpy.int64,
            "powerOnMinutes": numpy.int64,
            "throttleOnMilliseconds": numpy.int64,
            "ctxTailMagic": numpy.int64,
            "contextDropCount": numpy.int64,
            "lastCtxSequenceId": numpy.int64,
            "currCtxSequenceId": numpy.int64,
            "mbliEraseCount": numpy.int64,
            "pageAverageProgramCount": numpy.int64,
            "bandAverageEraseCount": numpy.int64,
            "bandTotalEraseCount": numpy.int64,
            "bandReloForXorRebuildFail": numpy.int64,
            "defragSpeculativeMiss": numpy.int64,
            "uncorrectableBackgroundScan": numpy.int64,
            "BitErrorsHost57": numpy.int64,
            "BitErrorsHost58": numpy.int64,
            "BitErrorsHost59": numpy.int64,
            "BitErrorsHost60": numpy.int64,
            "BitErrorsHost61": numpy.int64,
            "BitErrorsHost62": numpy.int64,
            "BitErrorsHost63": numpy.int64,
            "BitErrorsHost64": numpy.int64,
            "BitErrorsHost65": numpy.int64,
            "BitErrorsHost66": numpy.int64,
            "BitErrorsHost67": numpy.int64,
            "BitErrorsHost68": numpy.int64,
            "BitErrorsHost69": numpy.int64,
            "BitErrorsHost70": numpy.int64,
            "BitErrorsHost71": numpy.int64,
            "BitErrorsHost72": numpy.int64,
            "BitErrorsHost73": numpy.int64,
            "BitErrorsHost74": numpy.int64,
            "BitErrorsHost75": numpy.int64,
            "BitErrorsHost76": numpy.int64,
            "BitErrorsHost77": numpy.int64,
            "BitErrorsHost78": numpy.int64,
            "BitErrorsHost79": numpy.int64,
            "BitErrorsHost80": numpy.int64,
            "bitErrBucketArray1": numpy.int64,
            "bitErrBucketArray2": numpy.int64,
            "bitErrBucketArray3": numpy.int64,
            "bitErrBucketArray4": numpy.int64,
            "bitErrBucketArray5": numpy.int64,
            "bitErrBucketArray6": numpy.int64,
            "bitErrBucketArray7": numpy.int64,
            "bitErrBucketArray8": numpy.int64,
            "bitErrBucketArray9": numpy.int64,
            "bitErrBucketArray10": numpy.int64,
            "bitErrBucketArray11": numpy.int64,
            "bitErrBucketArray12": numpy.int64,
            "bitErrBucketArray13": numpy.int64,
            "bitErrBucketArray14": numpy.int64,
            "bitErrBucketArray15": numpy.int64,
            "bitErrBucketArray16": numpy.int64,
            "bitErrBucketArray17": numpy.int64,
            "bitErrBucketArray18": numpy.int64,
            "bitErrBucketArray19": numpy.int64,
            "bitErrBucketArray20": numpy.int64,
            "bitErrBucketArray21": numpy.int64,
            "bitErrBucketArray22": numpy.int64,
            "bitErrBucketArray23": numpy.int64,
            "bitErrBucketArray24": numpy.int64,
            "bitErrBucketArray25": numpy.int64,
            "bitErrBucketArray26": numpy.int64,
            "bitErrBucketArray27": numpy.int64,
            "bitErrBucketArray28": numpy.int64,
            "bitErrBucketArray29": numpy.int64,
            "bitErrBucketArray30": numpy.int64,
            "bitErrBucketArray31": numpy.int64,
            "bitErrBucketArray32": numpy.int64,
            "bitErrBucketArray33": numpy.int64,
            "bitErrBucketArray34": numpy.int64,
            "bitErrBucketArray35": numpy.int64,
            "bitErrBucketArray36": numpy.int64,
            "bitErrBucketArray37": numpy.int64,
            "bitErrBucketArray38": numpy.int64,
            "bitErrBucketArray39": numpy.int64,
            "bitErrBucketArray40": numpy.int64,
            "bitErrBucketArray41": numpy.int64,
            "bitErrBucketArray42": numpy.int64,
            "bitErrBucketArray43": numpy.int64,
            "bitErrBucketArray44": numpy.int64,
            "bitErrBucketArray45": numpy.int64,
            "bitErrBucketArray46": numpy.int64,
            "bitErrBucketArray47": numpy.int64,
            "bitErrBucketArray48": numpy.int64,
            "bitErrBucketArray49": numpy.int64,
            "bitErrBucketArray50": numpy.int64,
            "bitErrBucketArray51": numpy.int64,
            "bitErrBucketArray52": numpy.int64,
            "bitErrBucketArray53": numpy.int64,
            "bitErrBucketArray54": numpy.int64,
            "bitErrBucketArray55": numpy.int64,
            "bitErrBucketArray56": numpy.int64,
            "bitErrBucketArray57": numpy.int64,
            "bitErrBucketArray58": numpy.int64,
            "bitErrBucketArray59": numpy.int64,
            "bitErrBucketArray60": numpy.int64,
            "bitErrBucketArray61": numpy.int64,
            "bitErrBucketArray62": numpy.int64,
            "bitErrBucketArray63": numpy.int64,
            "bitErrBucketArray64": numpy.int64,
            "bitErrBucketArray65": numpy.int64,
            "bitErrBucketArray66": numpy.int64,
            "bitErrBucketArray67": numpy.int64,
            "bitErrBucketArray68": numpy.int64,
            "bitErrBucketArray69": numpy.int64,
            "bitErrBucketArray70": numpy.int64,
            "bitErrBucketArray71": numpy.int64,
            "bitErrBucketArray72": numpy.int64,
            "bitErrBucketArray73": numpy.int64,
            "bitErrBucketArray74": numpy.int64,
            "bitErrBucketArray75": numpy.int64,
            "bitErrBucketArray76": numpy.int64,
            "bitErrBucketArray77": numpy.int64,
            "bitErrBucketArray78": numpy.int64,
            "bitErrBucketArray79": numpy.int64,
            "bitErrBucketArray80": numpy.int64,
            "mrr_successDistribution1": numpy.int64,
            "mrr_successDistribution2": numpy.int64,
            "mrr_successDistribution3": numpy.int64,
            "mrr_successDistribution4": numpy.int64,
            "mrr_successDistribution5": numpy.int64,
            "mrr_successDistribution6": numpy.int64,
            "mrr_successDistribution7": numpy.int64,
            "mrr_successDistribution8": numpy.int64,
            "mrr_successDistribution9": numpy.int64,
            "mrr_successDistribution10": numpy.int64,
            "mrr_successDistribution11": numpy.int64,
            "mrr_successDistribution12": numpy.int64,
            "mrr_successDistribution13": numpy.int64,
            "mrr_successDistribution14": numpy.int64,
            "mrr_successDistribution15": numpy.int64,
            "mrr_successDistribution16": numpy.int64,
            "mrr_successDistribution17": numpy.int64,
            "mrr_successDistribution18": numpy.int64,
            "mrr_successDistribution19": numpy.int64,
            "mrr_successDistribution20": numpy.int64,
            "mrr_successDistribution21": numpy.int64,
            "mrr_successDistribution22": numpy.int64,
            "mrr_successDistribution23": numpy.int64,
            "mrr_successDistribution24": numpy.int64,
            "mrr_successDistribution25": numpy.int64,
            "mrr_successDistribution26": numpy.int64,
            "mrr_successDistribution27": numpy.int64,
            "mrr_successDistribution28": numpy.int64,
            "mrr_successDistribution29": numpy.int64,
            "mrr_successDistribution30": numpy.int64,
            "mrr_successDistribution31": numpy.int64,
            "mrr_successDistribution32": numpy.int64,
            "mrr_successDistribution33": numpy.int64,
            "mrr_successDistribution34": numpy.int64,
            "mrr_successDistribution35": numpy.int64,
            "mrr_successDistribution36": numpy.int64,
            "mrr_successDistribution37": numpy.int64,
            "mrr_successDistribution38": numpy.int64,
            "mrr_successDistribution39": numpy.int64,
            "mrr_successDistribution40": numpy.int64,
            "mrr_successDistribution41": numpy.int64,
            "mrr_successDistribution42": numpy.int64,
            "mrr_successDistribution43": numpy.int64,
            "mrr_successDistribution44": numpy.int64,
            "mrr_successDistribution45": numpy.int64,
            "mrr_successDistribution46": numpy.int64,
            "mrr_successDistribution47": numpy.int64,
            "mrr_successDistribution48": numpy.int64,
            "mrr_successDistribution49": numpy.int64,
            "mrr_successDistribution50": numpy.int64,
            "mrr_successDistribution51": numpy.int64,
            "mrr_successDistribution52": numpy.int64,
            "mrr_successDistribution53": numpy.int64,
            "mrr_successDistribution54": numpy.int64,
            "mrr_successDistribution55": numpy.int64,
            "mrr_successDistribution56": numpy.int64,
            "mrr_successDistribution57": numpy.int64,
            "mrr_successDistribution58": numpy.int64,
            "mrr_successDistribution59": numpy.int64,
            "mrr_successDistribution60": numpy.int64,
            "mrr_successDistribution61": numpy.int64,
            "mrr_successDistribution62": numpy.int64,
            "mrr_successDistribution63": numpy.int64,
            "mrr_successDistribution64": numpy.int64,
            "blDowngradeCount": numpy.int64,
            "snapReads": numpy.int64,
            "pliCapTestTime": numpy.int64,
            "currentTimeToFreeSpaceRecovery": numpy.int64,
            "worstTimeToFreeSpaceRecovery": numpy.int64,
            "rspnandReads": numpy.int64,
            "cachednandReads": numpy.int64,
            "spnandReads": numpy.int64,
            "dpnandReads": numpy.int64,
            "qpnandReads": numpy.int64,
            "verifynandReads": numpy.int64,
            "softnandReads": numpy.int64,
            "spnandWrites": numpy.int64,
            "dpnandWrites": numpy.int64,
            "qpnandWrites": numpy.int64,
            "opnandWrites": numpy.int64,
            "xpnandWrites": numpy.int64,
            "unalignedHostWriteCmd": numpy.int64,
            "randomReadCmd": numpy.int64,
            "randomWriteCmd": numpy.int64,
            "secVenCmdCount": numpy.int64,
            "secVenCmdCountFails": numpy.int64,
            "mrrFailOnSlcOtfPages": numpy.int64,
            "mrrFailOnSlcOtfPageMarkedAsMBPD": numpy.int64,
            "lcorParitySeedErrors": numpy.int64,
            "fwDownloadFails": numpy.int64,
            "fwAuthenticationFails": numpy.int64,
            "fwSecurityRev": numpy.int64,
            "isCapacitorHealthly": numpy.int64,
            "fwWRCounter": numpy.int64,
            "sysAreaEraseFailCount": numpy.int64,
            "iusDefragRelocated4DataRetention": numpy.int64,
            "I2CTemp": numpy.int64,
            "lbaMismatchOnNandReads": numpy.int64,
            "currentWriteStreamsCount": numpy.int64,
            "nandWritesPerStream1": numpy.int64,
            "nandWritesPerStream2": numpy.int64,
            "nandWritesPerStream3": numpy.int64,
            "nandWritesPerStream4": numpy.int64,
            "nandWritesPerStream5": numpy.int64,
            "nandWritesPerStream6": numpy.int64,
            "nandWritesPerStream7": numpy.int64,
            "nandWritesPerStream8": numpy.int64,
            "nandWritesPerStream9": numpy.int64,
            "nandWritesPerStream10": numpy.int64,
            "nandWritesPerStream11": numpy.int64,
            "nandWritesPerStream12": numpy.int64,
            "nandWritesPerStream13": numpy.int64,
            "nandWritesPerStream14": numpy.int64,
            "nandWritesPerStream15": numpy.int64,
            "nandWritesPerStream16": numpy.int64,
            "nandWritesPerStream17": numpy.int64,
            "nandWritesPerStream18": numpy.int64,
            "nandWritesPerStream19": numpy.int64,
            "nandWritesPerStream20": numpy.int64,
            "nandWritesPerStream21": numpy.int64,
            "nandWritesPerStream22": numpy.int64,
            "nandWritesPerStream23": numpy.int64,
            "nandWritesPerStream24": numpy.int64,
            "nandWritesPerStream25": numpy.int64,
            "nandWritesPerStream26": numpy.int64,
            "nandWritesPerStream27": numpy.int64,
            "nandWritesPerStream28": numpy.int64,
            "nandWritesPerStream29": numpy.int64,
            "nandWritesPerStream30": numpy.int64,
            "nandWritesPerStream31": numpy.int64,
            "nandWritesPerStream32": numpy.int64,
            "hostSoftReadSuccess": numpy.int64,
            "xorInvokedCount": numpy.int64,
            "comresets": numpy.int64,
            "syncEscapes": numpy.int64,
            "rErrHost": numpy.int64,
            "rErrDevice": numpy.int64,
            "iCrcs": numpy.int64,
            "linkSpeedDrops": numpy.int64,
            "mrrXtrapageEvents": numpy.int64,
            "mrrToppageEvents": numpy.int64,
            "hostXorSuccessCount": numpy.int64,
            "hostXorFailCount": numpy.int64,
            "nandWritesWithPreReadPerStream1": numpy.int64,
            "nandWritesWithPreReadPerStream2": numpy.int64,
            "nandWritesWithPreReadPerStream3": numpy.int64,
            "nandWritesWithPreReadPerStream4": numpy.int64,
            "nandWritesWithPreReadPerStream5": numpy.int64,
            "nandWritesWithPreReadPerStream6": numpy.int64,
            "nandWritesWithPreReadPerStream7": numpy.int64,
            "nandWritesWithPreReadPerStream8": numpy.int64,
            "nandWritesWithPreReadPerStream9": numpy.int64,
            "nandWritesWithPreReadPerStream10": numpy.int64,
            "nandWritesWithPreReadPerStream11": numpy.int64,
            "nandWritesWithPreReadPerStream12": numpy.int64,
            "nandWritesWithPreReadPerStream13": numpy.int64,
            "nandWritesWithPreReadPerStream14": numpy.int64,
            "nandWritesWithPreReadPerStream15": numpy.int64,
            "nandWritesWithPreReadPerStream16": numpy.int64,
            "nandWritesWithPreReadPerStream17": numpy.int64,
            "nandWritesWithPreReadPerStream18": numpy.int64,
            "nandWritesWithPreReadPerStream19": numpy.int64,
            "nandWritesWithPreReadPerStream20": numpy.int64,
            "nandWritesWithPreReadPerStream21": numpy.int64,
            "nandWritesWithPreReadPerStream22": numpy.int64,
            "nandWritesWithPreReadPerStream23": numpy.int64,
            "nandWritesWithPreReadPerStream24": numpy.int64,
            "nandWritesWithPreReadPerStream25": numpy.int64,
            "nandWritesWithPreReadPerStream26": numpy.int64,
            "nandWritesWithPreReadPerStream27": numpy.int64,
            "nandWritesWithPreReadPerStream28": numpy.int64,
            "nandWritesWithPreReadPerStream29": numpy.int64,
            "nandWritesWithPreReadPerStream30": numpy.int64,
            "nandWritesWithPreReadPerStream31": numpy.int64,
            "nandWritesWithPreReadPerStream32": numpy.int64,
            "dramCorrectables8to1": numpy.int64,
            "driveRecoveryCount": numpy.int64,
            "mprLiteReads": numpy.int64,
            "eccErrOnMprLiteReads": numpy.int64,
            "readForwardingXpPreReadCount": numpy.int64,
            "readForwardingUpPreReadCount": numpy.int64,
            "readForwardingLpPreReadCount": numpy.int64,
            "pweDefectCompensationCredit": numpy.int64,
            "planarXorRebuildFailure": numpy.int64,
            "itgXorRebuildFailure": numpy.int64,
            "planarXorRebuildSuccess": numpy.int64,
            "itgXorRebuildSuccess": numpy.int64,
            "xorLoggingSkippedSIcBand": numpy.int64,
            "xorLoggingSkippedDieOffline": numpy.int64,
            "xorLoggingSkippedDieAbsent": numpy.int64,
            "xorLoggingSkippedBandErased": numpy.int64,
            "xorLoggingSkippedNoEntry": numpy.int64,
            "xorAuditSuccess": numpy.int64,
            "maxSuspendCount": numpy.int64,
            "suspendLimitPerPrgm": numpy.int64,
            "psrCountStats": numpy.int64,
            "readNandBuffCount": numpy.int64,
            "readNandBufferRspErrorCount": numpy.int64,
            "ddpNandWrites": numpy.int64,
            "totalDeallocatedSectorsInCore": numpy.int64,
            "prefetchHostReads": numpy.int64,
            "hostReadtoDSMDCount": numpy.int64,
            "hostWritetoDSMDCount": numpy.int64,
            "snapReads4k": numpy.int64,
            "snapReads8k": numpy.int64,
            "snapReads16k": numpy.int64,
            "xorLoggingTriggered": numpy.int64,
            "xorLoggingAborted": numpy.int64,
            "xorLoggingSkippedHistory": numpy.int64,
            "deckDisturbRelocationUD": numpy.int64,
            "deckDisturbRelocationMD": numpy.int64,
            "deckDisturbRelocationLD": numpy.int64,
            "bbdProactiveReadRetry": numpy.int64,
            "statsRestoreRequired": numpy.int64,
            "statsAESCount": numpy.int64,
            "statsHESCount": numpy.int64,
            "psrCountStats1": numpy.int64,
            "psrCountStats2": numpy.int64,
            "psrCountStats3": numpy.int64,
            "psrCountStats4": numpy.int64,
            "psrCountStats5": numpy.int64,
            "psrCountStats6": numpy.int64,
            "psrCountStats7": numpy.int64,
            "psrCountStats8": numpy.int64,
            "psrCountStats9": numpy.int64,
            "psrCountStats10": numpy.int64,
            "psrCountStats11": numpy.int64,
            "psrCountStats12": numpy.int64,
            "psrCountStats13": numpy.int64,
            "psrCountStats14": numpy.int64,
            "psrCountStats15": numpy.int64,
            "psrCountStats16": numpy.int64,
            "psrCountStats17": numpy.int64,
            "psrCountStats18": numpy.int64,
            "psrCountStats19": numpy.int64,
            "psrCountStats20": numpy.int64,
            "psrCountStats21": numpy.int64,
            "psrCountStats22": numpy.int64,
            "psrCountStats23": numpy.int64,
            "psrCountStats24": numpy.int64,
            "psrCountStats25": numpy.int64,
            "psrCountStats26": numpy.int64,
            "psrCountStats27": numpy.int64,
            "psrCountStats28": numpy.int64,
            "psrCountStats29": numpy.int64,
            "psrCountStats30": numpy.int64,
            "psrCountStats31": numpy.int64,
            "psrCountStats32": numpy.int64,
            "psrCountStats33": numpy.int64,
            "psrCountStats34": numpy.int64,
            "psrCountStats35": numpy.int64,
            "psrCountStats36": numpy.int64,
            "psrCountStats37": numpy.int64,
            "psrCountStats38": numpy.int64,
            "psrCountStats39": numpy.int64,
            "psrCountStats40": numpy.int64,
            "psrCountStats41": numpy.int64,
            "psrCountStats42": numpy.int64,
            "psrCountStats43": numpy.int64,
            "psrCountStats44": numpy.int64,
            "psrCountStats45": numpy.int64,
            "psrCountStats46": numpy.int64,
            "psrCountStatsHigh1": numpy.int64,
            "psrCountStatsHigh2": numpy.int64,
            "psrCountStatsHigh3": numpy.int64,
            "psrCountStatsHigh4": numpy.int64,
            "psrCountStatsHigh5": numpy.int64,
            "psrCountStatsHigh6": numpy.int64,
            "psrCountStatsHigh7": numpy.int64,
            "psrCountStatsHigh8": numpy.int64,
            "psrCountStatsHigh9": numpy.int64,
            "psrCountStatsHigh10": numpy.int64,
            "psrCountStatsHigh11": numpy.int64,
            "psrCountStatsHigh12": numpy.int64,
            "psrCountStatsHigh13": numpy.int64,
            "psrCountStatsHigh14": numpy.int64,
            "vssSwitchCount": numpy.int64,
            "openBandReadCount": numpy.int64,
            "closedBandReadCount": numpy.int64,
            "minEraseSLC": numpy.int64,
            "maxEraseSLC": numpy.int64,
            "avgEraseSLC": numpy.int64,
            "totalErasesSLC": numpy.int64,
            "unexpectedPsrStateCount": numpy.int64,
            "lowPrioritySqReadCmds": numpy.int64,
            "mediumPrioritySqReadCmds": numpy.int64,
            "highPrioritySqReadCmds": numpy.int64,
            "urgentPrioritySqReadCmds": numpy.int64,
        }
        return dataFormat


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--inFile",
                      dest='inFile',
                      default=None,
                      help='Path for the input CSV file separated by spaces.')
    parser.add_option("--outFile",
                      dest='outFile',
                      default=None,
                      help='Path for the tab separated format file where the time series ini')
    parser.add_option("--targetObject",
                      dest='targetObject',
                      default=None,
                      help='Data set name for the section field.')
    parser.add_option("--debug",
                      dest='debug',
                      default="False",
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    if (options.inFile is None):
        inFile = "time-series_media.csv"
        if not os.path.exists(os.path.abspath(inFile)):
            return 1
    else:
        inFile = options.inFile

    if (options.outFile is None):
        outFile = "time-series_media.ini"
    else:
        outFile = options.outFile

    if options.debug == "True":
        debug = True
    else:
        debug = False

    if options.targetObject is not None:
        targetObject = options.targetObject
    else:
        targetObject = 'MEDIA_MADNESS'

    mediaMadnessObject = TransformMetaData(inputFileName=inFile,
                                           debug=debug,
                                           sectionName=targetObject,
                                           outFolder=None,
                                           outFile=outFile)
    print("Column List:")
    pprint.pprint(mediaMadnessObject.getColumnList())
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
