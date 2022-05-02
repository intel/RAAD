# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""visualizeTS.py

This module contains the basic functions for plotting time series generated from a configuration file.
Multiple transformations to the data can be applied using the enhance functions before visualization.
To run this script you must use a GUI, as pyplot requires the environment variable $DISPLAY to be set
to generate the PDF files. The execution of this module assumes that the configuration file only contains
data for a single core; data for multiple cores in a single config file will result in distorted graphs

Args:
     --outfile: String for the name of the output file (without the suffix)
     --targetObject: String for the object name to be processed
     --targetFields: Comma-separated strings for the names of the object's flatten fields to be processed
     --inputFile: String of the name for the configuration file containing the data for the time-series
     --combine: Boolean flag to indicate whether or not all fields should be combined in a single plot
     --subSeqLen: Integer value for the length of the sliding window to be used for generating the matrix profile
     --transformTS: Boolean flag to generate the matrix profile for the given time series
     --debug: Boolean flag to activate debug statements

Example:
    Default usage:
        $ python visualizeTS.py
    Specific usage:
        $ python visualizeTS.py --outfile test1 --targetObject ThermalSensor --targetFields logtimer,secondstimer
                                --inputFile time-series/time-series.ini --debug True

"""

# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys, traceback, datetime, optparse, copy, pathlib, os, pandas, pprint
import src.software.TSV.utilityTSV
import scipy.signal as sp
import numpy as np
import matplotlib.backends.backend_pdf as be
import matplotlib.pyplot as plt
import src.software.mp.matrixProfile as mp
import src.software.DP.preprocessingAPI as DP
from src.software.debug import whoami
from src.software.threadModuleAPI import MassiveParallelismSingleFunctionManyParameters
from statsmodels.tsa.stattools import adfuller

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class visualizeTS(object):
    class visualizeUtility:

        @staticmethod
        def generateTruncatedLists(subdict, field, start, end):
            """
            function for generating the data list of the corresponding percentage of values

            Args:
                subdict: Dictionary containing the data and values
                field: String for the name of the field to be accessed in the dictionary
                start: Integer value for the start percentage of the lists
                end: Integer value for the end percentage of the lists

            Returns:
                dataList: list containing the data values for the corresponding percentages

            """
            startIndex = int(len(subdict[field]) * (start / 100))
            endIndex = int(len(subdict[field]) * (end / 100))
            dataList = subdict[field][startIndex:endIndex]
            return dataList

    def __init__(self, debug=False):
        """
        function for initializing a visualizeTS structure

        Args:
            debug: Boolean flag to activate debug statements

        Attributes:
            debug: Boolean flag to activate debug statements

        """
        self.debug = debug
        self.defaultColors = ["blue", "green", "red", "cyan", "magenta", "yellow", "black"]

    def getDebug(self):
        """
        function for reading the debug flag stored in the visualizeTS attributes

        Returns:
            Boolean flag to activate debug statements

        """
        return self.debug

    def setDebug(self, debug):
        """
        function for setting the debug flag stored in the visualizeTS attributes

        Args:
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.debug = debug

    def populateMPStruct(self, MP, subdict, object_t, subSeqLen, fields, visualizeAllFields):
        """
        function for generating the dictionary with the matrix profile values for the time-series

        Args:
            MP: Dictionary where all the data lists will be stored
            subdict: Dictionary where the unprocessed data lists are contained
            object_t: String for the name of the object for which we are extracting the matrix profiles (ex. uid-6)
            subSeqLen: Integer for the window size to be used in the matrix profile generation
            fields: List of strings for the fields to be processed
            visualizeAllFields: Boolean flags to process all fields

        Returns:

        """
        MP[object_t] = {}
        if visualizeAllFields:
            for column in subdict.keys():
                if subdict[column][0].lower().islower():
                    MP[object_t][column] = subdict[column]
                    continue
                arr = sp.resample(subdict[column], len(subdict[column]))
                arr = np.random.normal(arr, np.finfo(float).eps)
                if self.debug is True:
                    print("Normalized array: " + str(arr))
                MP[object_t][column] = mp.stomp(arr, subSeqLen)[0].tolist()
        else:
            for column in fields:
                arr = sp.resample(subdict[column], len(subdict[column]))
                arr = np.random.normal(arr, np.finfo(float).eps)
                if self.debug is True:
                    print("Normalized array: " + str(arr))
                MP[object_t][column] = mp.stomp(arr, subSeqLen)[0].tolist()

    def generateMP(self, dataDict, obj=None, fields=None, subSeqLen=20, visualizeAllObj=True, visualizeAllFields=True):
        """
        function for generating a matrix profile for multiple time series contained in dataDict

        Args:
            dataDict: Dictionary containing all the time-series data
            obj: List of objects for which to generate a file containing all the desired plots
            fields: List of fields for which to generate a plot inside the output file
            subSeqLen: Integer value for the length of the sliding window to be used to generate the matrix profile
            visualizeAllObj: Boolean flag indicating that all objects in the configuration file should be considered
            visualizeAllFields: Boolean flag indicating that all fields for an object should be plotted

        Returns:
            A dictionary containing all the data for the matrix profiles associated with the given fields of the specified
            objects

        """

        if self.debug is True:
            print("Generating MP...")

        MP = {}
        if visualizeAllObj:
            for object_t in dataDict.keys():
                subdict = dataDict[object_t]
                self.populateMPStruct(MP, subdict, object_t, subSeqLen, fields, visualizeAllFields)
                MP[object_t]["name"] = dataDict[object_t]["name"]

        else:
            for uid in obj:
                objectID = "uid-" + uid
                subdict = dataDict[objectID]
                self.populateMPStruct(MP, subdict, objectID, subSeqLen, fields, visualizeAllFields)
                MP[objectID]["name"] = dataDict[objectID]["name"]

        return MP

    def check_stationarity(self, timeseriesCandidate):
        """
        Augmented Dickey-Fuller (ADF) test can be used to test the null hypothesis that the series is non-stationary. The ADF test helps to understand whether a change in Y is a linear trend or not. If there is a linear trend but the lagged value cannot explain the change in Y over time, then our data will be deemed non-stationary. The value of test statistics is less than 5% critical value and p-value is also less than 0.05 so we can reject the null hypothesis and Alternate Hypothesis that time series is Stationary seems to be true. When there is nothing unusual about the time plot and there appears to be no need to do any data adjustments. There is no evidence of changing variance also so we will not do a Box-Cox transformation.
        Args:
            timeseriesCandidate: Time series

        Returns: Determination of whether the data is stationary or not?

        """
        # Early abandon exit for same exact values in series.
        if len(set(timeseriesCandidate)) == 1:
            return True

        pValueThreshold = 0.05
        result = adfuller(timeseriesCandidate, autolag='AIC')
        if self.debug:
            dfoutput = pandas.Series((result[0:4]), index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
            # adfstat, pvalue, critvalues, resstore
            print(f'The test statistic: {dfoutput[0]}')
            print(f'p-value: %f' % (dfoutput[1]))
            print('Critical Values:')
            for key, value in (dfoutput[4].items()):
                print('%s: %.3f' % (key, value))
            pprint.pprint(dfoutput)
        dfoutput = pandas.Series((result[0:4]), index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
        if dfoutput[1] > pValueThreshold:
            return False
        else:
            return True

    def generateTSVisualizationGUI(self, name, subdict, mainFields, secondaryFields, start=0, end=100):
        """
        function for generating the time-series plots using GUI parameters and options

        Args:
            name: String for the name of the graph
            subdict: Dictionary containing all the data for an object
            mainFields: List of strings for the fields to be graphed in the primary axis
            secondaryFields: List of strings for the fields to be graphed in the secondary axis
            start: Integer value for the start percentage of the lists
            end: Integer value for the end percentage of the lists

        Returns:

        """
        fig, ax1 = plt.subplots()
        ax1.set_title(name)
        ax1.set_xlabel('Time Stamp')
        availableColors = copy.deepcopy(self.defaultColors)

        localMax = 1
        for field in mainFields:
            currentColor = availableColors.pop(0)
            data = self.visualizeUtility.generateTruncatedLists(subdict, field, start, end)
            currentMax = max(data)
            try:
                ax1.plot(data, label=field, color=currentColor)
                if currentMax > localMax:
                    localMax = currentMax
            except:
                plt.close()
        ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax1.set_ylim([0, 1.2 * localMax])

        if len(secondaryFields) > 0:
            ax2 = ax1.twinx()
            maxSecondaryLim = 1
            for field in secondaryFields:
                currentColor = availableColors.pop(0)
                data = self.visualizeUtility.generateTruncatedLists(subdict, field, start, end)
                currentMax = max(data)
                try:
                    ax2.plot(data, label=field, color=currentColor)
                    if currentMax > maxSecondaryLim:
                        maxSecondaryLim = currentMax
                except:
                    plt.close()
            ax2.legend(bbox_to_anchor=(1.04, 0), loc="upper left")
            ax2.set_ylim([0, 1.2 * maxSecondaryLim])

        fig.tight_layout()
        plt.show()

    def generatePDFPlots(self, subdict, ax, column, combine, pdf, start=0, end=100):
        """
        function for plotting the time-series and saving the plots in the specified pdf file

        Args:
            ax: matplotlib axis object where the data will be plotted
            subdict: Dictionary containing all the data for an object
            column: String for the name of the field to be processed
            combine: Boolean flag indicating whether or not to combine all fields in a single graph
            pdf: File descriptor for the pdf file where the plots will be stored
            start: Integer value for the start percentage of the lists
            end: Integer value for the end percentage of the lists

        Returns:

        """
        if self.debug is True:
            print("Field being processed: " + column)

        if combine:
            try:
                columnFields = column.split(".")
                ax.plot(subdict[column], label=columnFields[0])
                pdf.savefig()
                plt.close()
            except:
                plt.close()
            # columnFields = column.split(".")
            # ax.plot(subdict[column], label=columnFields[0])
        else:
            try:
                data = self.visualizeUtility.generateTruncatedLists(subdict, column, start, end)
                ax.title(column)
                ax.plot(data)
                pdf.savefig()
                plt.close()
            except:
                plt.close('all')

    def generateTSVisualizationCMD(self, subdict, objectID, fields, visualizeAllFields, combine, pdf, start=0, end=100):
        """
        function to generate the time-series plots using command-line parameters

        Args:
            objectID: string for the object ide to be used in the title
            subdict: Dictionary containing all the data for an object
            fields: List of fields for which to generate a plot inside the output file
            visualizeAllFields: Boolean flag indicating that all fields for an object should be plotted
            combine: Boolean flag indicating aggregate all fields in a single graph
            pdf: File descriptor for the pdf file where the plots will be stored
            start: Integer value for the start percentage of the lists
            end: Integer value for the end percentage of the lists

        Returns:

        """

        if visualizeAllFields:
            for column in subdict.keys():
                data = self.visualizeUtility.generateTruncatedLists(subdict, column, start, end)
                if self.check_stationarity(timeseriesCandidate=data):
                    continue
                try:
                    fig, ax1 = plt.subplots()
                    ax1.set_title(objectID + "-" + column)
                    ax1.set_xlabel('Time Stamp')
                    ax1.plot(data, label=column)
                    fig.tight_layout()
                    if pdf is not None:
                        pdf.savefig()
                    plt.close()
                except BaseException as error_t:
                    print(whoami())
                    print(f"Fail to graph field {column} and combine flag is {combine} with exception:{str(error_t)}")
        else:
            for field in fields:
                try:
                    fig, ax1 = plt.subplots()
                    ax1.set_title(objectID + "-" + field)
                    ax1.set_xlabel('Time Stamp')
                    data = self.visualizeUtility.generateTruncatedLists(subdict, field, start, end)
                    ax1.plot(data, label=field)
                    fig.tight_layout()
                    if pdf is not None:
                        pdf.savefig()
                    plt.close()
                except BaseException as error_t:
                    print(whoami())
                    print(f"Fail to graph field {field} and combine flag is {combine} with exception: {str(error_t)}")
            return

    def generatePDFFile(self, dataDict, objectID, outfile, fields, visualizeAllFields, combine, start=0, end=100):
        """
        function for generating a PDF file that contains the time-series plot for the data contained in dataDict

        Args:
            dataDict: Dictionary containing all the time-series data
            objectID: String for the name of the object to be processed (ex. uid-6)
            outfile: String of the prefix for the output file
            fields: List of fields for which to generate a plot inside the output file
            visualizeAllFields: Boolean flag indicating that all fields for an object should be plotted
            combine: Boolean flag indicating whether or not to combine all fields in a single graph
            start: Integer value for the start percentage of the lists
            end: Integer value for the end percentage of the lists

        Returns:

        """
        p = datetime.datetime.now()
        print(f"Object being processed: {objectID} @{p}")
        subdict = dataDict[objectID]
        outSub = os.path.join(outfile, str(objectID))
        if not os.path.exists(outSub):
            os.makedirs(outSub)

        fileCount = 0
        for path in pathlib.Path(outfile).iterdir():
            if path.is_file():
                fileCount += 1
        if fileCount > 256:
            print(f"{whoami()}")
            print(f"Total file count is: {fileCount}")

        pdfFile = os.path.abspath(os.path.join(outSub, (str(objectID) + ".pdf")))
        if not os.path.exists(outSub):
            os.makedirs(outSub)
        with be.PdfPages(pdfFile) as pp:
            self.generateTSVisualizationCMD(subdict=subdict, objectID=objectID, fields=fields, visualizeAllFields=visualizeAllFields, combine=combine, pdf=pp, start=start, end=end)
            # pp.close()
        if self.debug is True:
            q = datetime.datetime.now()
            print(f" Object done: {objectID} @{str(q - p)}")
        return pdfFile

    def writeTSVisualizationToPDF(self, dataDict, obj=None, outfile="telemetryDefault", fields=None, combine=False,
                                  subSeqLen=20, transformTS=False, visualizeAllObj=False, visualizeAllFields=False,
                                  raw_uid=False, inParallel=False, timeOut=180):
        """
        Function for generating a basic line plot for the time series data. It is assumed that the data is in
        order and its index represents the relative time of collection

        Args:
            inParallel: Flag to process all objects in parallel processes.
            raw_uid: Boolean flag to indicate whether the uid contains the prefix 'uid-'
            dataDict: Dictionary containing all the time-series data
            obj: List of objects for which to generate a file containing all the desired plots
            outfile: String of the prefix for the output file
            fields: List of fields for which to generate a plot inside the output file
            combine: Boolean flag indicating whether or not to combine all fields in a single graph
            subSeqLen: Integer value for the length of the sliding window to be used to generate the matrix profile
            transformTS: Boolean flag indicating that the matrix profile for the time series will be generated
            visualizeAllObj: Boolean flag indicating that all objects in the configuration file should be considered
            visualizeAllFields: Boolean flag indicating that all fields for an object should be plotted
            timeOut: Time before aborting computation.

        Returns:
        """
        if transformTS is True:
            dataDict = self.generateMP(dataDict=dataDict, obj=obj, subSeqLen=subSeqLen, fields=fields,
                                       visualizeAllFields=visualizeAllFields, visualizeAllObj=visualizeAllObj)

        if visualizeAllObj:
            walkDictObj = dataDict.keys()
        else:
            walkDictObj = obj

        runSequential = not inParallel
        kwargsList = list()
        for object_t in walkDictObj:
            if not visualizeAllObj and not raw_uid:
                uidObj = f"uid-{str(object_t)}"
            else:
                # (    visualizeAllObj and     raw_uid) or
                # (    visualizeAllObj and not raw_uid) or
                # (not visualizeAllObj and     raw_uid)
                uidObj = object_t

            dictElem = {'dataDict': dataDict,
                        'objectID': uidObj,
                        'outfile': outfile,
                        'fields': fields,
                        'visualizeAllFields': visualizeAllFields,
                        'combine': combine,
                        'start': 0,
                        'end': 100}
            kwargsList.append(dictElem)
        functionContext = MassiveParallelismSingleFunctionManyParameters(debug=self.debug,
                                                                         functionName=self.generatePDFFile,
                                                                         fParameters=kwargsList,
                                                                         workers=None,
                                                                         timeOut=timeOut,
                                                                         inOrder=True,
                                                                         runSequential=runSequential)
        iResults = functionContext.execute()
        pdfFiles = iResults
        return pdfFiles

    def visualizeTSAPI(self, obj=None, fields=None, input_t="time-series.ini", out="telemetryDefault", combine=False,
                       subSeqLen=20, transformTS=False, visualizeAllObj=False, visualizeAllFields=False,
                       raw_uid=False, inParallel=False, requiredList=None, timeOut=180):
        """
        API to replace standard command line call (the visualizeTS class has to instantiated before calling
        this method)

        Args:
            inParallel: Flag to process all objects in parallel processes.
            raw_uid: Boolean flag to indicate whether the uid contains the prefix 'uid-'
            requiredList: List of strings fort he names of objects to be processed if the useRequiredList flag is set.
                If None, the default list will be used. Indicates whether the objects to be processed should be limited to the ones
                contained in the requiredList.
            obj: List of object UIDs for which to generate a file containing all the desired plots
            fields: List of fields for which to generate a plot inside the output file
            input_t: String of the name for the configuration file containing the data for the time-series
            out: String of the prefix for the output file
            combine: Boolean flag indicating whether or not to combine all fields in a single graph
            subSeqLen: Integer value for the length of the sliding window to be used to generate the matrix profile
            transformTS: Boolean flag indicating that the matrix profile for the time series will be generated
            visualizeAllObj: Boolean flag indicating that all objects in the configuration file should be considered
            visualizeAllFields: Boolean flag indicating that all fields for an object should be plotted
            timeOut: Execution timeout

        Returns:

        """
        if obj is None:
            visualizeAllObj = True

        if fields is None:
            visualizeAllFields = True

        # Optional remove stationary data
        # if removeConstantFeatures is True:
        #   selectDict, isReduced = DictionaryPrune(queryDict=self.dataDict)
        #   if isReduced is True:
        #       self.dataDict = selectDict
        #       print(f"Reduced meta constants...")

        intermediateDict = DP.preprocessingAPI().loadDataDict(input_t)
        newDict = {}
        oldDictKeys = intermediateDict.keys()
        if requiredList is None:
            # Objects required:
            objectsOfInterest = [
                'uid-44',  # DefragInfoSlow - Standard time-series, bar graph if singular point
                'uid-45',  # Defrag_DustingQueue
                'uid-46',  # Defrag_LockedQueue
                'uid-47',  # Defrag_WAQueue
                'uid-48',  # Defrag_WearLevelQueue
                'uid-49',  # DefragInfo - straight time-series
                'uid-58',  # fConfigInfoTable
                'uid-181',  # band_EraseInfo - bar graph sorted by number for single file
                'uid-182',  # band_InvalidityInfo - graph band numbers sorted by invalidity
                'uid-191',  # SlowCtx
                'uid-198',  # band_States - enumeration table
                'uid-205',  # CtxSave - inprogress, up to the total
            ]
            requiredList = objectsOfInterest
        for object_t in requiredList:
            if object_t in oldDictKeys:
                newDict[object_t] = intermediateDict[object_t]
        intermediateDict = newDict
        pdfFileReturn = self.writeTSVisualizationToPDF(dataDict=intermediateDict, obj=obj, outfile=out, fields=fields, combine=combine,
                                                       subSeqLen=subSeqLen, transformTS=transformTS,
                                                       visualizeAllObj=visualizeAllObj, visualizeAllFields=visualizeAllFields,
                                                       raw_uid=raw_uid, inParallel=inParallel, timeOut=timeOut)

        return pdfFileReturn


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
    parser.add_option("--targetObjectUID",
                      dest='targetObjectUID',
                      default=None,
                      help='Object UIDs to be used for the visualizations')
    parser.add_option("--targetFields",
                      dest='targetFields',
                      default=None,
                      help='Object fields to be used for the visualizations')
    parser.add_option("--inputFile",
                      dest='inputFile',
                      default=None,
                      help='Path of the file containing the config that describes the time series')
    parser.add_option("--combine",
                      dest='combine',
                      default=None,
                      help='Boolean flag to combine multiple fields in a single graph')
    parser.add_option("--subSeqLen",
                      dest='subSeqLen',
                      default=None,
                      help='Length of the sliding window to be used for generating the matrix profile')
    parser.add_option("--transformTS",
                      dest='transformTS',
                      default=None,
                      help='Boolean flag to generate the matrix profile for the given time series')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    if options.targetObject is None:
        targetObjects = None
    else:
        targetObjects = options.targetObject.split(",")

    if options.targetFields is None:
        targetFields = None
    else:
        targetFields = options.targetFields.split(",")
    UT = src.software.TSV.utilityTSV
    out = UT.utilityTSV().checkOutfile(options.outfile)
    obj = targetObjects
    fields = targetFields
    combine = UT.utilityTSV().checkCombine(options.combine)
    input_t = UT.utilityTSV().checkInputFile(options.inputFile)
    subSeqLen = UT.utilityTSV().checkSubSeqLen(options.subSeqLen)
    transformTS = UT.utilityTSV().checkTransformTS(options.transformTS)
    debug = UT.utilityTSV().checkDebugOption(options.debug)
    viz = visualizeTS(debug=debug)
    viz.visualizeTSAPI(obj=obj, fields=fields, input_t=input_t, out=out, combine=combine, subSeqLen=subSeqLen, transformTS=transformTS)
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
