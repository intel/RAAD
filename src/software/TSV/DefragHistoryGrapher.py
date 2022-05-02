# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""DefragHistoryGrapher.py

This module contains the basic functions for plotting DefragHistory time series generated from a configuration file.
To run this script you must use a GUI, as pyplot requires the environment variable $DISPLAY to be set
to generate the PDF files.

Args:
     --outfile: String for the name of the output file (without the suffix)
     --inputFile: String of the path name for the configuration file containing the data for the time-series
     --numCores: Integer for the number of cores from which data was pulled
     --mode: Integer value for run mode (1=ADP, 2=CDR)
     --encapStruct: String for the name of the struct where the set points are contained (ADP)
     --trackingNames: comma-separated strings for the names of the stats to be tracked in the main axis of the graph
     --secondaryVars: comma-separated strings for the names of the fields to be plotted in the secondary axis
     --bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
     --headerName: String for the name of the field associated with the header (ADP)
     --indexName: String for the name of the field associated with the index
     --timeLabel: String for the name of the field associated with time
     --coreLabel: String for the name of the struct associated with core number
     --logTypeLabel: String for the name of the field associated with the log type (ADP)
     --setPointNames: Comma-separated strings for the names of the set points to be used in the graph (ADP)
     --setPointValues: Comma-separated integers for the values of the set points to be used in the graph (CDR)
     --arbiterLabels: Comma-separated strings for the names of the set points contained in the arbiter structure (CDR)
     --colors: Comma-separated strings of the color names for the set points to be used in graph (ADP)
     --debug: Boolean flag to activate debug statements

Example:
    Default usage:
        $ python DefragHistoryGapher.py
    Specific usage:
        $ python DefragHistoryGapher.py --outfile test1 --inputFile time-series/time-series.ini --numCores 2
                                                                                                        --debug True

"""

# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys, re, traceback, datetime, optparse, pprint, os
from . import utilityTSV
import copy
import matplotlib.backends.backend_pdf as be
import matplotlib.pyplot as plt
import src.software.DP.preprocessingAPI as DP
from src.software.debug import whoami

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class DefragHistoryGrapher(object):
    """
    Class for graphing DefragHistory for both ADP and CDR drives

    Attributes:
            debug: Boolean flag to activate debug statements
            mode: Integer value for run mode (1=ADP, 2=CDR)
            defaultColors: List of strings for the names of standard colors to be used for plotting tracked and
            secondary variables
            encapsulatingStruct: String for the name of the struct where the set points are contained (ADP)
            setPointNames: List of strings for the names of the set points to be used in the graph (ADP)
            trackingNames: List of strings for the names of the fields to be graphed in the main axis
            secondaryVars: List of strings for the names of the fields to be graphed in the secondary axis
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            headerName: String for the name of the field associated with the header (ADP)
            indexName: String for the name of the field associated with the index
            logTypeLabel: String for the name of the field associated with the log type (ADP)
            timeLabel: String for the name of the field associated with time
            coreLabel: String for the name of the struct associated with core number
            colorDict: Dictionary of Set Point Names to string names for colors
            setPointDict: Dictionary of Set Point Names to integer values
            arbiterDict: Dictionary of Set Point Names to string names for the arbiter fields

    """

    class defragHistoryUtility():

        @staticmethod
        def getMaxAIU(mode, setPointNames, coreSetPoints, fieldData):
            """
            function for calculating the maximum AIU to be used in the graphs for both CDR and ADP

            Args:
                mode: Integer value for run mode (1=ADP, 2=CDR)
                setPointNames: List of strings for the names of the set points to be used in the graph
                coreSetPoints: Dictionary of set point names to series (ADP) or lists (CDR) of data values
                fieldData: List of data values for current field

            Returns:
                Float for the maximum value for AIU to be used in the graph

            """
            currentMax = 1
            if mode == 1:
                currentMax = max(fieldData)
                for field in setPointNames:
                    localMax = max(coreSetPoints[field].data)
                    if localMax > currentMax:
                        currentMax = localMax
            elif mode == 2:
                currentMax = max(fieldData)
                for field in setPointNames:
                    if int(coreSetPoints[field]) > currentMax:
                        currentMax = int(coreSetPoints[field])

            return 1.2 * float(currentMax)

        @staticmethod
        def initializeDataDicts(numCores=2, targetDict=None, defaultDict=None, manualSetPoints=False):
            """
            function for initializing the intermediate dictionaries that contain the data series to be plotted

            Args:
                numCores: Integer for the number of cores from which data was pulled
                targetDict: Dictionary where the values of the setPoints will be stored
                defaultDict: Dictionary with the default values for setPoints
                manualSetPoints: Boolean flag to indicate if the default set points should be used

            Returns:
                coresDict: Dictionary of data values for the fields to be plotted in the main axis
                coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis
                previousLogNumDict: Dictionary with the previous log number to be used as a sentinel value

            """
            coresDict = dict()
            coresSecondaryDict = dict()
            previousLogNumDict = dict()

            for core in range(numCores):
                coresDict[core] = dict()
                coresSecondaryDict[core] = dict()
                previousLogNumDict[core] = 0
                if manualSetPoints and targetDict is not None and defaultDict is not None:
                    targetDict[core] = defaultDict

            return coresDict, coresSecondaryDict, previousLogNumDict

        @staticmethod
        def calculateBandwidth(currentTime, currentCore, currentData, field, coresBandwidth, seriesDeltaClass):
            """
            function for calculating and appending the bandwidth value to the value list for a field

            Args:
                currentTime: Integer value for the time stamp collected in the dataDict
                currentCore: Integer value for the current core number being accessed
                currentData: Integer for the current data value being accessed
                field: String for the name of the field to be accessed
                coresBandwidth: Dictionary for the values to be plotted in the secondary axis
                seriesDeltaClass: Child class of Series containing fields for previous time and data

            Returns:

            """
            if field not in coresBandwidth[currentCore]:
                coresBandwidth[currentCore][field] = seriesDeltaClass()
            if currentTime - coresBandwidth[currentCore][field].lastTime >= 1000:
                if coresBandwidth[currentCore][field].lastData is not None:
                    coresBandwidth[currentCore][field].time.append(currentTime)
                    coresBandwidth[currentCore][field].data.append(
                        int(float(currentData - coresBandwidth[currentCore][field].lastData) / 2.048
                            / (currentTime - coresBandwidth[currentCore][field].lastTime)))
                coresBandwidth[currentCore][field].lastData = currentData
                coresBandwidth[currentCore][field].lastTime = currentTime

        @staticmethod
        def populateField(index, currentTime, currentCore, field, logDict, coresDict, seriesClass):
            """
            function for populating the field inside coresDict with the respective time and data

            Args:
                index: Integer for the position in the value list
                currentTime: Integer value for the time stamp collected in the dataDict
                currentCore: Integer value for the current core number being accessed
                field: String for the name of the field to be accessed
                logDict: Dictionary associated with the current log
                coresDict: Dictionary of data values for the fields to be plotted in the main axis
                seriesClass: Class containing lists for time and data

            Returns:

            """
            if field not in coresDict[currentCore]:
                coresDict[currentCore][field] = seriesClass()
            coresDict[currentCore][field].data.append(logDict[field][index])
            coresDict[currentCore][field].time.append(currentTime)

        @staticmethod
        def populateEncapsulatedField(index, currentTime, currentCore, field, encapStruct, logDict, coresDict, seriesClass):
            """
            function for populating the field inside coresDict with the respective time and data

            Args:
                encapStruct: Constant auto parse detection module.
                index: Integer for the position in the value list
                currentTime: Integer value for the time stamp collected in the dataDict
                currentCore: Integer value for the current core number being accessed
                field: String for the name of the field to be accessed
                logDict: Dictionary associated with the current log
                coresDict: Dictionary of data values for the fields to be plotted in the main axis
                seriesClass: Class containing lists for time and data

            Returns:

            """
            if field not in coresDict[currentCore]:
                coresDict[currentCore][field] = seriesClass()
            coresDict[currentCore][field].data.append(logDict[encapStruct][field][index])
            coresDict[currentCore][field].time.append(currentTime)
            return

        @staticmethod
        def generateTruncatedLists(coreElements: dict, field, start: int = 0, end: int = 100):
            """
            function for generating the time and data lists of the corresponding percentage of values

            Args:
                coreElements: Series dictionary containing the data and time values
                field: String for the name of the field to be accessed in the Series dictionary
                start: Integer value for the start percentage of the lists
                end: Integer value for the end percentage of the lists

            Returns:
                timeList: list containing the time values for the corresponding percentages
                dataList: list containing the data values for the corresponding percentages
            """
            if field in coreElements:
                startIndex = int(len(coreElements[field].time) * (start / 100))
                endIndex = int(len(coreElements[field].time) * (end / 100))
                dataList = coreElements[field].data[startIndex:endIndex]
                timeList = coreElements[field].time[startIndex:endIndex]
            else:
                timeList = None
                dataList = None
            return timeList, dataList

    def __init__(self,
                 mode=1,
                 encapsulatingStruct="__anuniontypedef115__",
                 trackingNames=None,
                 secondaryVars=None,
                 bandwidthFlag=True,
                 headerName="header",
                 indexName="index",
                 timeLabel="time",
                 coreLabel="core",
                 logTypeLabel="prevlogtype",
                 setPointNames=None,
                 setPointValues=None,
                 hostOperations=None,
                 ctxList=None,
                 NandOperations=None,
                 slotList=None,
                 colors=None,
                 arbiterLabels=None,
                 debug=False):
        """
        function for initializing a DefragHistoryGrapher structure

        Args:
            mode: Integer value for run mode (1=ADP, 2=CDR)
            encapsulatingStruct: String for the name of the struct where the set points are contained (ADP)
            trackingNames: List of strings for the names of the stat to be tracked in the main axis of the graph
            secondaryVars: List of strings for the names of the stat to be tracked in the secondary axis of the graph
            hostOperations: List of strings for the names of the host operations to be graphed
            ctxList: List of strings for the names of the ctx variables to be graphed
            NandOperations: List of strings for the names of the Nand operations to be graphed
            slotList: List of strings for the names of the slot variables to be graphed
            bandwidthFlag: Boolean flag indicating whether the secondaryNames are to be used as bandwidth variables
            headerName: String for the name of the field associated with the header (ADP)
            indexName: String for the name of the field associated with the index
            timeLabel: String for the name of the field associated with time
            coreLabel: String for the name of the struct associated with core number
            logTypeLabel: String for the name of the field associated with the log type (ADP)
            setPointNames: List of strings for the names of the set points to be used in the graph (ADP)
            setPointValues: List of integers for the values of the set points to be used in the graph
            colors: List of strings of the color names for the set points to be used in graph (ADP)
            arbiterLabels: List of strings for the names of the set points contained in the arbiter structure (CDR)
            debug: Boolean flag to activate debug statements

        Note: setPointNames, setPointValues, and colors must have the same size if they are going to be used for the
        graphs, as it is the case for CDR when no arbiter object is found within the configuration file

        Returns:

        """
        if setPointNames is None:
            setPointNames = ["start", "normal", "corner", "urgent", "critical"]
        if setPointValues is None:
            setPointValues = [29750000, 24750000, 14750000, 9750000, 4750000]
        if colors is None:
            colors = ['purple', 'green', 'yellow', 'orange', 'red']
        if arbiterLabels is None:
            arbiterLabels = ["startsetpoint", "normalsetpoint", "cornersetpoint", "urgentsetpoint", "criticalsetpoint"]
        if trackingNames is None:
            trackingNames = ["available"]
        if secondaryVars is None:
            secondaryVars = ["hostwrites"]
        if hostOperations is None:
            hostOperations = ["hostwrites", "hostreads"]
        if ctxList is None:
            ctxList = ["ctxbudget", "ctxsaveprogress"]
        if NandOperations is None:
            NandOperations = ["nandwrites"]
        if slotList is None:
            slotList = ["defragslots", "hostslots", "totalslots"]

        self.debug = debug
        self.mode = mode
        self.defaultColors = ["blue", "green", "red", "cyan", "magenta", "yellow", "black"]
        self.encapsulatingStruct = encapsulatingStruct
        self.setPointNames = setPointNames
        self.trackingNames = trackingNames
        self.secondaryVars = secondaryVars
        self.hostOperations = hostOperations
        self.ctxList = ctxList
        self.NandOperations = NandOperations
        self.slotList = slotList
        self.bandwidthFlag = bandwidthFlag
        self.headerName = headerName
        self.indexName = indexName
        self.logTypeLabelName = logTypeLabel
        self.timeLabel = timeLabel
        self.coreLabel = coreLabel
        self.colorDict = {self.setPointNames[i]: colors[i] for i in range(len(self.setPointNames))}
        self.setPointDict = {self.setPointNames[i]: setPointValues[i] for i in range(len(self.setPointNames))}
        self.arbiterDict = {self.setPointNames[i]: arbiterLabels[i] for i in range(len(self.setPointNames))}
        return

    def getDebug(self):
        """
        function for reading the debug flag stored in the DefragHistoryGrapher attributes

        Returns:
            Boolean flag to activate debug statements

        """
        return self.debug

    def setDebug(self, debug):
        """
        function for setting the debug flag stored in the DefragHistoryGrapher attributes

        Args:
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.debug = debug

    def getSetPointNames(self):
        """
        function for reading the list newSetPointNames stored in the DefragHistoryGrapher attributes

        Returns:
            List of strings for the names of the set points

        """
        result = copy.deepcopy(self.setPointNames)
        return result

    def setSetPointNames(self, newSetPointNames):
        """
        function for setting the list newSetPointNames stored in the DefragHistoryGrapher attributes

        Args:
            newSetPointNames: list of strings for the names of the set points

        Returns:

        """
        result = copy.deepcopy(newSetPointNames)
        self.setPointNames = result

    def getTrackingNames(self):
        """
        function for reading the list trackingNames stored in the DefragHistoryGrapher attributes

        Returns:
            List of strings with the names for the variables to be plotted in the main axis

        """
        result = copy.deepcopy(self.trackingNames)
        return result

    def setTrackingNames(self, trackingNames):
        """
        function for setting the list trackingNames stored in the DefragHistoryGrapher attributes

        Args:
            trackingNames: list of strings with the names for the variables to be plotted in the main axis

        Returns:

        """
        result = copy.deepcopy(trackingNames)
        self.trackingNames = result

    def getSecondaryVars(self):
        """
        function for reading the list secondaryVars stored in the DefragHistoryGrapher attributes

        Returns:
            List of strings with the names for the variables to be plotted in the secondary axis

        """
        result = copy.deepcopy(self.secondaryVars)
        return result

    def setSecondaryVars(self, secondaryVars):
        """
        function for setting the list secondaryVars stored in the DefragHistoryGrapher attributes

        Args:
            secondaryVars: list of strings with the names for the variables to be plotted in the secondary axis

        Returns:

        """
        result = copy.deepcopy(secondaryVars)
        self.secondaryVars = result

    def populateTSDataADP(self, object_t, numCores: int = 2, dataDict: dict = None, bandwidthFlag: bool = True, encapStruct="__anuniontypedef46__"):
        """
        @todo dgarces these should be dynamic based on the log type. The current code uses exceptions to bypass not found terms; however, these should be handled by the log type.
        function for filling the intermediate time-series data structures with the ADP data contained inside the
        given dictionary

        Args:
            encapStruct: Contant auto parse detection variable.
            object_t: String for the object identifier (ex. uid-6)
            numCores: Integer for the number of cores from which data was pulled
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth

        Returns:
            coresDict: Dictionary of data values for the fields to be plotted in the main axis
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis

        """

        class Series(object):
            def __init__(self):
                self.time = []
                self.data = []

            def pop(self, index):
                self.data.pop(index)

            def __str__(self):
                return str(self.data)

        class SeriesDelta(Series):
            def __init__(self):
                Series.__init__(self)
                self.lastTime = 0
                self.lastData = None

        try:
            subdict = dataDict[object_t]
        except Exception:
            print("DefragHistory object not found in the configuration file")
            return

        if self.debug is True:
            print("DefragHistory object found...")

        coresDict, coresSecondaryDict, previousLogNumDict = self.defragHistoryUtility.initializeDataDicts(numCores)

        for i in range(len(subdict[self.coreLabel])):
            try:
                currentCore = int(subdict[self.coreLabel][i])
                logNumber = int(subdict[self.headerName][self.indexName][i])
                logType = subdict[self.headerName][self.logTypeLabelName][i]
                # Please verify regular search expressions with a tool such as https://www.debuggex.com/
                # Note: Within the defrag history header the log type is set within the data structure in index->prevLogType.
                #      The series of decoding is based on a linked list traversal of identify then select decoder.
                litePattern = re.compile("(.+)?(LITE)(.+)?")
                normalPattern = re.compile("(.+)?(NORMAL)(.+)?")
                extendedPattern = re.compile("(.+)?(EXTENDED)(.+)?")

                if logNumber > int(previousLogNumDict[currentCore]):
                    accessLogValue = logNumber - int(previousLogNumDict[currentCore])
                else:
                    accessLogValue = 0

                if accessLogValue > 0:

                    if litePattern.match(logType, re.IGNORECASE):
                        logName = f"loglite[{str(logNumber)}]"
                    elif extendedPattern.match(logType, re.IGNORECASE):
                        logName = f"logextended[{str(logNumber)}]"
                    elif normalPattern.match(logType, re.IGNORECASE):
                        logName = f"lognormal[{str(logNumber)}]"
                    else:
                        raise Exception("Log type not found " + logType)
                    logDict = subdict[self.encapsulatingStruct][logName]
                    currentTime = int(logDict[self.timeLabel][i])

                    if currentTime == 0:
                        continue

                    try:
                        for field in self.setPointNames:
                            self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.trackingNames:
                            self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.secondaryVars:
                            currentData = int(logDict[field][i])
                            if bandwidthFlag:
                                self.defragHistoryUtility.calculateBandwidth(currentTime, currentCore, currentData, field, coresSecondaryDict, SeriesDelta)
                            else:
                                self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresSecondaryDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.hostOperations:
                            self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.ctxList:
                            self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.NandOperations:
                            self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                    try:
                        for field in self.slotList:
                            self.defragHistoryUtility.populateEncapsulatedField(i, currentTime, currentCore, field, encapStruct, logDict, coresDict, Series)
                    except BaseException as errorFoundInner:
                        if self.debug:
                            pprint.pprint(whoami())
                            print(errorFoundInner)
                        pass

                previousLogNumDict[currentCore] = logNumber
            except BaseException as errorFound:
                if self.debug:
                    pprint.pprint(whoami())
                    print(errorFound)
                pass
                continue

        return coresDict, coresSecondaryDict

    def graphTSVisualizationADPinPDF(self, coreNumber, coresDict, coresSecondaryDict, bandwidthFlag, pdf=None, start=0,
                                end=100):
        """
        function for creating and saving the time-series plot for available blocks and bandwidth

        Args:
            numCores: Integer for the number of cores from which data was collected in the configuration file
            coresDict: Dictionary of data values for the fields to be plotted in the main axis
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            pdf: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        # try:
        #for j in range(numCores):
        coreElements = coresDict[coreNumber]
        fig, ax1 = plt.subplots()
        ax1.set_title(f'Defrag History - Core {str(coreNumber)}')
        ax1.set_xlabel('Time')
        maxAIU = 0
        currentAvailableColors = copy.deepcopy(self.defaultColors)
        currentAvailableColors2 = copy.deepcopy(self.defaultColors)
        currentAvailableColors3 = copy.deepcopy(self.defaultColors)
        for field in self.setPointNames:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            ax1.plot(timeList, dataList, linestyle='--', label=field, color=self.colorDict[field])
        for field in self.trackingNames:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            if self.debug:
                print("Time:" + str(timeList))
                print("Data: " + str(dataList))
            print("Plotting " + field)
            if field == "available":
                ax1.set_ylabel('AIU')
            color = currentAvailableColors.pop(0)
            currentMaxAIU = self.defragHistoryUtility.getMaxAIU(self.mode, self.setPointNames, coreElements,
                                                                dataList)
            if currentMaxAIU > maxAIU:
                maxAIU = currentMaxAIU
            ax1.plot(timeList, dataList, label=field, color=color)
        ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax1.set_ylim([0, maxAIU])
        if len(self.secondaryVars) > 0:
            ax2 = ax1.twinx()
            maxSecondaryLim = 0
            for field in self.secondaryVars:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coresSecondaryDict[coreNumber],
                                                                                      field, start, end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))

                print("Plotting " + field)
                label = field
                color = currentAvailableColors.pop(0)
                if bandwidthFlag:
                    ax2.set_ylabel('MB/s')
                    label = "hMB/s"
                currentMaxLim = max(dataList)
                if currentMaxLim > maxSecondaryLim:
                    maxSecondaryLim = currentMaxLim
                ax2.plot(timeList, dataList, label=label, color=color)
            ax2.legend(bbox_to_anchor=(1.04, 0), loc="upper left")
            ax2.set_ylim([0, 1.2 * max(1, maxSecondaryLim)])
        fig.tight_layout()
        if pdf is not None:
            pdf.savefig()
            plt.close()

        #  Slot Graphs
        fig3, ax3 = plt.subplots()
        ax3.set_title(f'Defrag History - Core {str(coreNumber)}')
        ax3.set_xlabel('Time')
        for field in self.slotList:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            if self.debug:
                print("Time:" + str(timeList))
                print("Data: " + str(dataList))
            print("Plotting " + field)
            color = currentAvailableColors2.pop(0)
            ax3.plot(timeList, dataList, label=field, color=color)
        ax3.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax3.set_ylabel('Count')
        fig3.tight_layout()
        if pdf is not None:
            pdf.savefig()
            plt.close()

        # hostOperations graphs
        fig4, ax4 = plt.subplots()
        ax4.set_title(f'Defrag History - Core {str(coreNumber)}')
        ax4.set_xlabel('Time')
        for field in self.hostOperations:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            if self.debug:
                print("Time:" + str(timeList))
                print("Data: " + str(dataList))
            print("Plotting " + field)
            color = currentAvailableColors3.pop(0)
            ax4.plot(timeList, dataList, label=field, color=color)
        ax4.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax4.set_ylabel('Count')
        fig4.tight_layout()
        if pdf is not None:
            pdf.savefig()
            plt.close()

        # NandOperations graphs
        fig5, ax5 = plt.subplots()
        ax5.set_title(f'Defrag History - Core {str(coreNumber)}')
        ax5.set_xlabel('Time')
        for field in self.NandOperations:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            if self.debug:
                print("Time:" + str(timeList))
                print("Data: " + str(dataList))
            print("Plotting " + field)
            color = currentAvailableColors3.pop(0)
            ax5.plot(timeList, dataList, label=field, color=color)
        ax5.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax5.set_ylabel('Count')
        fig5.tight_layout()
        if pdf is not None:
            pdf.savefig()
            plt.close()

        # ctx graphs
        fig6, ax6 = plt.subplots()
        ax6.set_title(f'Defrag History - Core {str(coreNumber)}')
        ax6.set_xlabel('Time')
        for field in self.ctxList:
            timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                  end)
            if self.debug:
                print("Time:" + str(timeList))
                print("Data: " + str(dataList))
            print("Plotting " + field)
            color = currentAvailableColors2.pop(0)
            ax6.plot(timeList, dataList, label=field, color=color)
        ax6.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax6.set_ylabel('Count')
        fig6.tight_layout()
        if pdf is not None:
            pdf.savefig()
            plt.close()

        if pdf is None:
            plt.show()

        # except Exception as ero:
        #   print("Plotting failed....")
        #  print(ero)
        # plt.close('all')
        return

    def graphTSVisualizationADP(self, numCores, coresDict, coresSecondaryDict, bandwidthFlag, pdf=None, start=0,
                                end=100):
        """
        function for creating and saving the time-series plot for available blocks and bandwidth

        Args:
            numCores: Integer for the number of cores from which data was collected in the configuration file
            coresDict: Dictionary of data values for the fields to be plotted in the main axis
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            pdf: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        # try:
        for j in range(numCores):
            coreElements = coresDict[j]
            fig, ax1 = plt.subplots()
            ax1.set_title(f'Defrag History - Core {str(j)}')
            ax1.set_xlabel('Time')
            maxAIU = 0
            currentAvailableColors = copy.deepcopy(self.defaultColors)
            currentAvailableColors2 = copy.deepcopy(self.defaultColors)
            currentAvailableColors3 = copy.deepcopy(self.defaultColors)
            for field in self.setPointNames:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                ax1.plot(timeList, dataList, linestyle='--', label=field, color=self.colorDict[field])
            for field in self.trackingNames:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                if field == "available":
                    ax1.set_ylabel('AIU')
                color = currentAvailableColors.pop(0)
                currentMaxAIU = self.defragHistoryUtility.getMaxAIU(self.mode, self.setPointNames, coreElements,
                                                                    dataList)
                if currentMaxAIU > maxAIU:
                    maxAIU = currentMaxAIU
                ax1.plot(timeList, dataList, label=field, color=color)
            ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax1.set_ylim([0, maxAIU])
            if len(self.secondaryVars) > 0:
                ax2 = ax1.twinx()
                maxSecondaryLim = 0
                for field in self.secondaryVars:
                    timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coresSecondaryDict[j],
                                                                                          field, start, end)
                    if self.debug:
                        print("Time:" + str(timeList))
                        print("Data: " + str(dataList))

                    print("Plotting " + field)
                    label = field
                    color = currentAvailableColors.pop(0)
                    if bandwidthFlag:
                        ax2.set_ylabel('MB/s')
                        label = "hMB/s"
                    currentMaxLim = max(dataList)
                    if currentMaxLim > maxSecondaryLim:
                        maxSecondaryLim = currentMaxLim
                    ax2.plot(timeList, dataList, label=label, color=color)
                ax2.legend(bbox_to_anchor=(1.04, 0), loc="upper left")
                ax2.set_ylim([0, 1.2 * max(1, maxSecondaryLim)])
            fig.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()

            #  Slot Graphs
            fig3, ax3 = plt.subplots()
            ax3.set_title(f'Defrag History - Core {str(j)}')
            ax3.set_xlabel('Time')
            for field in self.slotList:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                color = currentAvailableColors2.pop(0)
                ax3.plot(timeList, dataList, label=field, color=color)
            ax3.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax3.set_ylabel('Count')
            fig3.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()

            # hostOperations graphs
            fig4, ax4 = plt.subplots()
            ax4.set_title(f'Defrag History - Core {str(j)}')
            ax4.set_xlabel('Time')
            for field in self.hostOperations:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                color = currentAvailableColors3.pop(0)
                ax4.plot(timeList, dataList, label=field, color=color)
            ax4.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax4.set_ylabel('Count')
            fig4.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()

            # NandOperations graphs
            fig5, ax5 = plt.subplots()
            ax5.set_title(f'Defrag History - Core {str(j)}')
            ax5.set_xlabel('Time')
            for field in self.NandOperations:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                color = currentAvailableColors3.pop(0)
                ax5.plot(timeList, dataList, label=field, color=color)
            ax5.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax5.set_ylabel('Count')
            fig5.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()

            # ctx graphs
            fig6, ax6 = plt.subplots()
            ax6.set_title(f'Defrag History - Core {str(j)}')
            ax6.set_xlabel('Time')
            for field in self.ctxList:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                color = currentAvailableColors2.pop(0)
                ax6.plot(timeList, dataList, label=field, color=color)
            ax6.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax6.set_ylabel('Count')
            fig6.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()

        if pdf is None:
            plt.show()

        # except Exception as ero:
        #   print("Plotting failed....")
        #  print(ero)
        # plt.close('all')
        return

    def generateTSVisualizationADP(self, object_t, dataDict: dict = None, bandwidthFlag: bool = True, numCores: int = 2, pp=None, start=0, end=100):
        """
        function for generating a line plot for the time series data collected from an ADP drive

        Args:
            object_t: String for the object identifier (ex. uid-6)
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            numCores: Integer for the number of cores from which data was pulled
            pp: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        coresDict, coresSecondaryDict = self.populateTSDataADP(object_t=object_t, numCores=numCores, dataDict=dataDict, bandwidthFlag=bandwidthFlag)
        self.graphTSVisualizationADP(numCores=numCores, coresDict=coresDict, coresSecondaryDict=coresSecondaryDict, bandwidthFlag=bandwidthFlag,
                                     pdf=pp, start=start, end=end)
        return

    def generateTSVisualizationADPinPDF(self, object_t, dataDict: dict = None, bandwidthFlag: bool = True, numCores: int = 2, pdfFiles=None, start=0, end=100):
        """
        function for generating a line plot for the time series data collected from an ADP drive

        Args:
            object_t: String for the object identifier (ex. uid-6)
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            numCores: Integer for the number of cores from which data was pulled
            pdfFiles: list of PDF files in which the figures will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        if pdfFiles is None:
            return

        coresDict, coresSecondaryDict = self.populateTSDataADP(object_t=object_t, numCores=numCores, dataDict=dataDict,
                                                               bandwidthFlag=bandwidthFlag)
        index = 0
        for file in pdfFiles:
            with be.PdfPages(file) as pp:
                self.graphTSVisualizationADPinPDF(coreNumber=index, coresDict=coresDict, coresSecondaryDict=coresSecondaryDict, bandwidthFlag=bandwidthFlag,
                                                    pdf=pp, start=start, end=end)
            index += 1
        return

    def getSetPointsCDR(self, dataDict, numCores, dataSetLength):
        """
        function for obtaining the set point values from the arbiter object for a CDR drive

        Args:
            dataDict: Dictionary containing all the objects from the configuration file
            numCores: Integer for the number of cores from which data was pulled
            dataSetLength: How many data points are in each field (EX: if 100 samples were taken for 2 cores,
            dataSetLength will be 200)

        Returns:
            setPointDict: Dictionary of set point values for each core
            colors: Dictionary of colors for data set point names

        """
        object_t = "uid-43"
        setPointDict = dict()
        colors = dict()
        try:
            subdict = dataDict[object_t]
        except Exception:
            print("Arbiter object not found in the configuration file")
            return setPointDict, colors
        if self.debug is True:
            print("Arbiter object found...")
        for i in range(numCores):
            setPointDict[i] = dict()
        for i in range(numCores):
            currentCore = int(subdict["core"][dataSetLength - (i + 1)])
            for field in self.setPointNames:
                setPointDict[currentCore][field] = int(subdict[self.arbiterDict[field]][dataSetLength - (i + 1)])

        for field in self.setPointNames:
            colors[field] = self.colorDict[field]

        return setPointDict, colors

    def populateTSDataCDR(self, object_t, numCores, dataDict, bandwidthFlag):
        """
        function for filling the intermediate time-series data structures with the CDR data contained inside the
        given dictionary

        Args:
            object_t: String for the object identifier (ex. uid-6)
            numCores: Integer for the number of cores from which data was collected in the configuration file
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth

        Returns:
            setPointsDict: Dictionary of set point values for each core
            colors: Dictionary of colors for data set point names
            coresDict: Dictionary of data values for the fields to be plotted in the main axis
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis

        """

        class Series(object):
            def __init__(self):
                self.time = []
                self.data = []

            def pop(self, index):
                self.data.pop(index)

            def __str__(self):
                return str(self.data)

        class SeriesDelta(Series):
            def __init__(self):
                Series.__init__(self)
                self.lastTime = 0
                self.lastData = None

        try:
            subdict = dataDict[object_t]
        except Exception:
            print("DefragHistory object not found in the configuration file")
            return
        if self.debug is True:
            print("DefragHistory object found...")
        manualSetPoints = False

        setPointsDict, colors = self.getSetPointsCDR(dataDict, numCores, len(subdict[self.coreLabel]))
        if not setPointsDict:
            setPointsDict = {}
            colors = self.colorDict
            manualSetPoints = True

        coresDict, coresSecondaryDict, previousLogNumDict = self.defragHistoryUtility.initializeDataDicts(numCores,
                                                                                                          targetDict=setPointsDict,
                                                                                                          defaultDict=self.setPointDict,
                                                                                                          manualSetPoints=manualSetPoints)

        for i in range(len(subdict[self.coreLabel])):
            currentCore = int(subdict[self.coreLabel][i])
            logNumber = int(subdict[self.indexName][i])

            if previousLogNumDict[currentCore] is None:
                previousLogNumDict[currentCore] = logNumber

            if logNumber - previousLogNumDict[currentCore] > 0:
                logName = f"log[{str(logNumber)}]"
                logDict = subdict[logName]
                currentTime = int(logDict[self.timeLabel][i])

                if currentTime == 0:
                    continue

                for field in self.trackingNames:
                    self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict, coresDict, Series)
                for field in self.secondaryVars:
                    currentData = int(logDict[field][i])
                    if bandwidthFlag:
                        self.defragHistoryUtility.calculateBandwidth(currentTime, currentCore, currentData, field,
                                                                     coresSecondaryDict, SeriesDelta)
                    else:
                        self.defragHistoryUtility.populateField(i, currentTime, currentCore, field, logDict,
                                                                coresSecondaryDict, Series)
            previousLogNumDict[currentCore] = logNumber

        return colors, setPointsDict, coresDict, coresSecondaryDict

    def graphTSVisualizationCDRinPDF(self, coreNumber, coresDict, setPointsDict, colors, coresSecondaryDict, bandwidthFlag,
                                pdf=None, start=0, end=100):
        """
        function for creating and saving the time-series plot for available blocks and bandwidth

        Args:
            coreNumber: number of the core to be graphed
            coresDict: Dictionary data values for the fields to be plotted in the main axis
            setPointsDict: Dictionary of set point values for each core
            colors: Dictionary of colors for data set point names
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            pdf: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        try:
            coreElements = coresDict[coreNumber]
            fig, ax1 = plt.subplots()
            ax1.set_title(f'Defrag History - Core {str(coreNumber)}')
            ax1.set_xlabel('Time')
            for field in self.setPointNames:
                ax1.axhline(y=setPointsDict[coreNumber][field], linestyle='--', label=field,
                            color=colors[field])

            maxAIU = 1
            currentAvailableColors = copy.deepcopy(self.defaultColors)
            for field in self.trackingNames:
                timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                      end)
                if self.debug:
                    print("Time:" + str(timeList))
                    print("Data: " + str(dataList))
                print("Plotting " + field)
                if field == "available":
                    ax1.set_ylabel('AIU')
                color = currentAvailableColors.pop(0)
                ax1.plot(timeList, dataList, label=field, color=color)

                currentMaxAIU = self.defragHistoryUtility.getMaxAIU(self.mode, self.setPointNames,
                                                                    setPointsDict[coreNumber],
                                                                    dataList)
                if currentMaxAIU > maxAIU:
                    maxAIU = currentMaxAIU

            ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
            ax1.set_ylim([0, maxAIU])
            if len(self.secondaryVars) > 0:
                ax2 = ax1.twinx()
                maxSecondaryLim = 0
                for field in self.secondaryVars:
                    timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coresSecondaryDict[coreNumber],
                                                                                          field, start, end)
                    if self.debug:
                        print("Time:" + str(timeList))
                        print("Data: " + str(dataList))
                    print("Plotting " + field)
                    label = field
                    color = currentAvailableColors.pop(0)
                    if bandwidthFlag:
                        ax2.set_ylabel('MB/s')
                        label = "hMB/s"
                    currentMaxLim = max(dataList)
                    if currentMaxLim > maxSecondaryLim:
                        maxSecondaryLim = currentMaxLim
                    ax2.plot(timeList, dataList, label=label, color=color)
                ax2.set_ylim([0, 1.2 * max(1, maxSecondaryLim)])
                ax2.legend(bbox_to_anchor=(1.04, 0), loc="upper left")
            fig.tight_layout()
            if pdf is not None:
                pdf.savefig()
                plt.close()
            else:
                plt.show()

        except Exception as ero:
            print("Plotting failed....")
            print(ero)
            plt.close('all')

    def graphTSVisualizationCDR(self, numCores, coresDict, setPointsDict, colors, coresSecondaryDict, bandwidthFlag,
                                pdf=None, start=0, end=100):
        """
        function for creating and saving the time-series plot for available blocks and bandwidth

        Args:
            numCores: Integer for the number of cores from which data was collected in the configuration file
            coresDict: Dictionary data values for the fields to be plotted in the main axis
            setPointsDict: Dictionary of set point values for each core
            colors: Dictionary of colors for data set point names
            coresSecondaryDict: Dictionary with the data values for the fields to be plotted in the secondary axis
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            pdf: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        try:
            for j in range(numCores):
                coreElements = coresDict[j]
                fig, ax1 = plt.subplots()
                ax1.set_title(f'Defrag History - Core {str(j)}')
                ax1.set_xlabel('Time')
                for field in self.setPointNames:
                    ax1.axhline(y=setPointsDict[j][field], linestyle='--', label=field,
                                color=colors[field])

                maxAIU = 1
                currentAvailableColors = copy.deepcopy(self.defaultColors)
                for field in self.trackingNames:
                    timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coreElements, field, start,
                                                                                          end)
                    if self.debug:
                        print("Time:" + str(timeList))
                        print("Data: " + str(dataList))
                    print("Plotting " + field)
                    if field == "available":
                        ax1.set_ylabel('AIU')
                    color = currentAvailableColors.pop(0)
                    ax1.plot(timeList, dataList, label=field, color=color)

                    currentMaxAIU = self.defragHistoryUtility.getMaxAIU(self.mode, self.setPointNames, setPointsDict[j],
                                                                        dataList)
                    if currentMaxAIU > maxAIU:
                        maxAIU = currentMaxAIU

                ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
                ax1.set_ylim([0, maxAIU])
                if len(self.secondaryVars) > 0:
                    ax2 = ax1.twinx()
                    maxSecondaryLim = 0
                    for field in self.secondaryVars:
                        timeList, dataList = self.defragHistoryUtility.generateTruncatedLists(coresSecondaryDict[j],
                                                                                              field, start, end)
                        if self.debug:
                            print("Time:" + str(timeList))
                            print("Data: " + str(dataList))
                        print("Plotting " + field)
                        label = field
                        color = currentAvailableColors.pop(0)
                        if bandwidthFlag:
                            ax2.set_ylabel('MB/s')
                            label = "hMB/s"
                        currentMaxLim = max(dataList)
                        if currentMaxLim > maxSecondaryLim:
                            maxSecondaryLim = currentMaxLim
                        ax2.plot(timeList, dataList, label=label, color=color)
                    ax2.set_ylim([0, 1.2 * max(1, maxSecondaryLim)])
                    ax2.legend(bbox_to_anchor=(1.04, 0), loc="upper left")
                fig.tight_layout()
                if pdf is not None:
                    pdf.savefig()
                    plt.close()
            if pdf is None:
                plt.show()

        except Exception as ero:
            print("Plotting failed....")
            print(ero)
            plt.close('all')

    def generateTSVisualizationCDR(self, object_t, dataDict, bandwidthFlag, numCores=2, pp=None, start=0, end=100):
        """
        function for generating a line plot for the time series of DefragHistory for a CDR drive

        Args:
            object_t: String for the object identifier (ex. uid-6)
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            numCores: Integer for the number of cores from which data was pulled
            pp: File descriptor for the PDF file where the plots will be saved
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """

        colors, setPointsDict, coresDict, coresSecondaryDict = self.populateTSDataCDR(object_t, numCores, dataDict,
                                                                                      bandwidthFlag)
        self.graphTSVisualizationCDR(numCores, coresDict, setPointsDict, colors, coresSecondaryDict, bandwidthFlag, pp,
                                     start, end)

    def generateTSVisualizationCDRinPDF(self, object_t, dataDict, bandwidthFlag, numCores=2, pdfFiles=None, start=0, end=100):
        """
        function for generating a line plot for the time series of DefragHistory for a CDR drive

        Args:
            object_t: String for the object identifier (ex. uid-6)
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            numCores: Integer for the number of cores from which data was pulled
            pdfFiles: list of pdf files in which the graphs will be stored
            start: Integer value for the start percentage of the lists to be graphed
            end: Integer value for the end percentage of the lists to be graphed

        Returns:

        """
        if pdfFiles is None:
            return

        colors, setPointsDict, coresDict, coresSecondaryDict = self.populateTSDataCDR(object_t, numCores, dataDict,
                                                                                      bandwidthFlag)
        index = 0

        for file in pdfFiles:
            with be.PdfPages(file) as pp:
                self.graphTSVisualizationCDRinPDF(index, coresDict, setPointsDict, colors, coresSecondaryDict, bandwidthFlag,
                                             pp, start, end)
            index += 1

    def generateDataDictFromConfig(self, input_t):
        """
        function for reading the config file into an intermediate dict, and transforming that intermediate dict to
        produce the nesting of the original object

        Args:
            input_t: String of the name for the configuration file containing the data for the time-series

        Returns:
            Dictionary containing all the time-series data with the appropriate nesting according to the fields

        """
        config = DP.preprocessingAPI.readFileIntoConfig(input_t)
        intermediateDict = DP.preprocessingAPI.loadConfigIntoDict(config, self.debug)
        resultDict = DP.preprocessingAPI.transformDict(intermediateDict, self.debug)
        return resultDict

    def writeTSVisualizationToPDF(self, object_t: str = "uid-41", dataDict: dict = None, bandwidthFlag: bool = True,
                                  out: str = "", numCores: int = 2, start=0, end=100):
        """
        function that generates the time series visualization for DefragHistory and saves it into a PDF file named
        with the prefix defined by out followed by a lower dash and the uid of the object

        Args:
            start: Starting point of time series
            end: end point of time series
            dataDict: Dictionary containing all the time-series data with the appropriate nesting
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
            out: String of the prefix for the output file
            numCores: Integer for the number of cores from which data was pulled

        Returns:

        """
        outSub = os.path.join(out, str(object_t))
        if not os.path.exists(outSub):
            os.makedirs(outSub, mode=0o777, exist_ok=True)

        PDFFiles = []
        for j in range(numCores):
            pdfFile = os.path.abspath(os.path.join(outSub, (str(object_t) + "_" + str(j) + ".pdf")))
            PDFFiles.append(pdfFile)

        if self.mode == 1:
            self.generateTSVisualizationADPinPDF(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                 pdfFiles=PDFFiles, start=start, end=end)
        elif self.mode == 2:
            self.generateTSVisualizationCDRinPDF(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                 pdfFiles=PDFFiles, start=start, end=end)
        return PDFFiles

    def DefragHistoryGrapherAPI(self, input_t: str = "time-series.ini", out: str = "telemetryDefault", numCores: int = 2, bandwidthFlag: bool = True):
        """
        API to replace standard command line call (the visualizeTS class has to instantiated before calling
        this method)

        Args:
            input_t: String of the name for the configuration file containing the data for the time-series
            out: String of the prefix for the output file
            numCores: Integer for the number of cores from which data was pulled
            bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth

        Returns:

        """
        dataDict = self.generateDataDictFromConfig(input_t)
        return self.writeTSVisualizationToPDF(dataDict=dataDict, bandwidthFlag=bandwidthFlag, out=out, numCores=numCores)


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--outfile",
                      dest='outfile',
                      default=None,
                      help='Name for the output file where the visualizations will stored')
    parser.add_option("--inputFile",
                      dest='inputFile',
                      default=None,
                      help='Path of the file containing the config that describes the DefragHistory time series')
    parser.add_option("--numCores",
                      dest='numCores',
                      default=None,
                      help='Integer for the number of cores from which data was pulled')
    parser.add_option("--mode",
                      dest='mode',
                      default=None,
                      help='Integer value for run mode (1=ADP, 2=CDR)')
    parser.add_option("--encapStruct",
                      dest='encapStruct',
                      default="__anuniontypedef115__",
                      help='String for the name of the struct where the set points are contained (ADP)')
    parser.add_option("--trackingNames",
                      dest='trackingNames',
                      default=None,
                      help='Comma-separated strings for the names of the stats to be tracked in the graph')
    parser.add_option("--secondaryVars",
                      dest='secondaryVars',
                      default=None,
                      help='Comma-separated strings for the names of the fields to be used in the secondary axis')
    parser.add_option("--bandwidthFlag",
                      dest='bandwidthFlag',
                      default=True,
                      help='Boolean flag that indicates if the secondary axis corresponds to bandwidth')
    parser.add_option("--headerName",
                      dest='headerName',
                      default="header",
                      help='String for the name of the field associated with the header (ADP)')
    parser.add_option("--indexName",
                      dest='indexName',
                      default="index",
                      help='String for the name of the field associated with the index')
    parser.add_option("--timeLabel",
                      dest='timeLabel',
                      default="time",
                      help='String for the name of the field associated with time')
    parser.add_option("--coreLabel",
                      dest='coreLabel',
                      default="core",
                      help='String for the name of the struct associated with core number')
    parser.add_option("--logTypeLabel",
                      dest='logTypeLabel',
                      default="prevlogtype",
                      help='String for the name of the field associated with the log type (ADP)')
    parser.add_option("--setPointNames",
                      dest='setPointNames',
                      default=None,
                      help='Comma-separated strings for the names of the set points to be used in the graph (ADP)')
    parser.add_option("--setPointValues",
                      dest='setPointValues',
                      default=None,
                      help='Comma-separated integers for the values of the set points to be used in the graph')
    parser.add_option("--arbiterLabels",
                      dest='arbiterLabels',
                      default=None,
                      help='Comma-separated strings for the names of the set points contained in the arbiter structure')
    parser.add_option("--colors",
                      dest='colors',
                      default=None,
                      help='Comma-separated strings of the color names for the set points to be used in graph (ADP)')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    out = utilityTSV.utilityTSV().checkOutfile(options.outfile)
    input_t = utilityTSV.utilityTSV().checkInputFile(options.inputFile)
    numCores = utilityTSV.utilityTSV().checkNumCores(options.numCores)
    mode = utilityTSV.utilityTSV().checkModeSelect(options.mode)
    debug = utilityTSV.utilityTSV().checkDebugOption(options.debug)
    bandwidthFlag = utilityTSV.utilityTSV().checkDebugOption(options.bandwidthFlag)

    if options.setPointNames is None:
        setPointNames = None
    else:
        setPointNames = options.setPointNames.split(",")

    if options.setPointValues is None:
        setPointValues = None
    else:
        premSetPointValues = options.setPointValues.split(",")
        setPointValues = map(int, premSetPointValues)

    if options.colors is None:
        colors = None
    else:
        colors = options.colors.split(",")

    if options.trackingNames is None:
        trackingNames = None
    else:
        trackingNames = options.trackingNames.split(",")

    if options.secondaryVars is None:
        secondaryVars = None
    else:
        secondaryVars = options.secondaryVars.split(",")

    if options.arbiterLabels is None:
        arbiterLabels = None
    else:
        arbiterLabels = options.arbiterLabels.split(",")

    viz = DefragHistoryGrapher(mode=mode, encapsulatingStruct=options.encapStruct, trackingNames=trackingNames,
                               secondaryVars=secondaryVars, headerName=options.headerName, indexName=options.indexName,
                               timeLabel=options.timeLabel, coreLabel=options.coreLabel, arbiterLabels=arbiterLabels,
                               logTypeLabel=options.logTypeLabel, setPointNames=setPointNames,
                               setPointValues=setPointValues, colors=colors, debug=debug)
    viz.DefragHistoryGrapherAPI(input_t=input_t, out=out, numCores=numCores, bandwidthFlag=bandwidthFlag)

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
