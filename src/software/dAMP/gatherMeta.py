#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package gatherMeta
# Future libraries
from __future__ import absolute_import, division, print_function, \
    unicode_literals, annotations  # , nested_scopes, generators, generator_stop, with_statement

# Standard libraries
import optparse, traceback, re, os, platform, socket, uuid, psutil, GPUtil, datetime, pprint
# import sys
from collections import OrderedDict

# Created libraries
from src.software.container.basicTypes import UID_Application, UID_Org
from src.software.TSV.generateTSBinaries import generateTSBinaries
from src.software.TSV.formatTSFiles import formatTSFiles
import src.software.TSV.DefragHistoryGrapher as TSVDefragHistory
import src.software.TSV.visualizeTS as TSVGenericGraph
import src.software.autoAI.mediaPredictionRNN as RNN
import src.software.MEP.mediaErrorPredictor as ARMA
from src.software.DP.preprocessingAPI import preprocessingAPI
from src.software.utilsCommon import DictionaryFlatten
# from src.software.utilsCommon import  getBytesSize, checkPythonVersion, strip_end, strip_start, strip_StartEnd
from src.software.debug import whoami
from src.software.threadModuleAPI import MassiveParallelismSingleFunctionManyParameters


class GatherMeta(object):
    # Application (100%) - General application information.
    version = UID_Application(uid=1, major=1, minor=1, data=None)
    org = UID_Org(vendor="Intel", bussinessUnit="NSG", group="STG", team="RAMP-RAAD-AMPERE")
    debug = False  # Developer debug information.
    binaryPath = None  # Relative path of binaries.
    fwDir = None  # Firmware directory.
    dataCntrlStructPath = None  # File path to data control structure
    nlogFolder = None
    configFileName = None  # Configuration file name for local information.
    resultsFolder = None  # Directory with the latest results.
    configData = None  # Configuration parser of meta settings.

    # Meta Data Dimensionality (100%) - Compiler labeling of machine programming systems.
    uidsFound = None  # Unique identifiers found in data dictionary.
    dataDictDimension = None  # Unique identifier dimensions of data dictionary.
    telemetryHeaderDict = None  # Telemetry header information.
    dataDict = None  # Unique identifier dictionary of parsers.
    deviceConfiguration = None  # Factory configuration of SSD.

    # Objects required:
    objectsOfInterest = [
        'uid-41',  # DefragHistory @todo no parser!
        'uid-44',  # DefragInfoSlow - Standard time-series, bar graph if singular point
        'uid-45',  # Defrag_DustingQueue
        'uid-46',  # Defrag_LockedQueue
        'uid-47',  # Defrag_WAQueue @todo no parser!
        'uid-48',  # Defrag_WearLevelQueue @todo no parser!
        'uid-49',  # DefragInfo - straight time-series
        'uid-58',  # fConfigInfoTable
        'uid-139',  # burninGate
        'uid-145',  # dramEccGate
        'uid-153',  # pliNandResetGate
        'uid-172',  # dmaDescMsgs
        'uid-181',  # band_EraseInfo - bar graph sorted by number for single file
        'uid-182',  # band_InvalidityInfo - graph band numbers sorted by invalidity
        'uid-185',  # bootProfileDRAM
        'uid-191',  # SlowCtx - @todo cannot add to telemetry
        'uid-196',  # NandChannelRegsDump
        'uid-198',  # band_States - enumeration table
        'uid-200',  # npsRegs
        'uid-201',  # dmtRegs
        'uid-205',  # CtxSave - inprogress, up to the total @todo add to telemetry
        'uid-216',  # dramEccInfo
        'uid-219',  # channelTimeout
        'uid-229',  # dmt_register_base
        'uid-235',  # dmtDebug0
        'uid-236',  # dmtDebug1
        'uid-237',  # dmtDebug2
        'uid-300',  # SdlSDMA_RD_RD
        'uid-301',  # SdlSDMA_WR_REGS
        'uid-307',  # SdlDramDescBuff
        'uid-382',  # iNQ
        'uid-1000140',  # channelMap
        'uid-1000170'  # eccErrorsLog
    ]

    # Detailed expert Analysis (20% => 25%), Intel Labs Compiler (25%) - Summary DFA, CFG, DFG, and maps of firmware.
    firmwareDFA = None  # Control, Data Flow state and transitions maps from firmware.
    DFA = None  # Deterministic Finitie Automata - Device State information.
    CFG = None  # Stack control flow graph.
    DFG = None  # Stack data flow graph.

    # Developer assisted Figures (50% => 85%) - Generated figures based on pertinent information highlighted in handbook.
    ARMAFigures = None  # Auto Agressive Time Series forcast figures.
    RNNFigures = None  # Recurent Neural Network (RNN) and Long-Short Term Memory (LSTM) figures.
    RNNAccuracy = None  # RNN-LSTM metrics for training.
    assistedFigures = None  # PDF list of figures from UIDs.

    # Machine Learning (20% => 100%) - Drive profile classification clustering - summary of data labeled based on state models
    MLProfiles = None  # Matrix profile data labeling of time series.
    systemInfo = None  # System information of the data being accessed from.
    MLMinedJira = None  # Mined JIRA Database nearest neighbor root cause speculation analysis.

    nlogTable = None

    # Time Series (60% -> 75%) - Summary of algorithms, labeling, models, expansion of datasets
    deviceSignature = None  # Telemetry header state of most recent Node or Timeseries.
    telemetryMetaStats = None  # Telemetry data machine learning information.
    timeSeriesSignatures = None  # Extracted series of data matrix or preprocess transformation on matrix meta data in time format.
    DataLakeMeta = None  # Data lake information from data upload

    def __init__(self,
                 binaryPath="data/inputSeries/",
                 fwDir="../Auto-Parse/decode/ADP_UV",
                 dataCntrlStructPath="../../Auto-Parse/datacontrol/structures.csv",
                 configFileName='data/workload-healthy-ADP.ini',
                 resultsFolder="data/output",
                 nlogFolder="software/parse/nlogParser",
                 useCSV=False,
                 debug=False):
        """
        Args:
            binaryPath: relative path to the folder where the telemetry binaries are stored
            fwDir: relative path to the folder where the firmware parsers are stored
            dataCntrlStructPath: relative path to the file where the data control structures are stored.
            configFileName: String representation of the name of the .ini file where the time series is stored or will
            be stored
            resultsFolder: relative path to folder where the results of intermediate operations will be stored
            debug: boolean flag for verbose printing
        """
        self.updateInitialize(binaryPath=binaryPath,
                              fwDir=fwDir,
                              dataCntrlStructPath=dataCntrlStructPath,
                              configFileName=configFileName,
                              resultsFolder=resultsFolder,
                              nlogFolder=nlogFolder,
                              useCSV=useCSV,
                              debug=debug)
        return

    def getUIDDescriptions(self, uidsFound: list = None):
        """
        Args:
            uidsFound: list of uids with the format 'uid-#'.
        Returns: dictionary that describes uids (key) with its global name and definition (value).
        """
        # Read csv file Auto-Parse/datacontrol/structures.csv
        import pandas as pd
        dataCntrlStruct = pd.read_csv(self.dataCntrlStructPath)
        dataCntrlStruct = dataCntrlStruct[dataCntrlStruct['Telemetry Version'] == 2.0]

        # Get global name and definition of each uid and add them.
        uidDescriptions = dict()
        for uidStr in uidsFound:
            uid = uidStr.split('-')[1]
            uidData = dataCntrlStruct[dataCntrlStruct['uniqueIdentifier'] == uid]
            if uidData.empty:
                print("Unknown uid: %s" % (uid))
                uidDescriptions[uidStr] = ['Unknown uid']
            elif len(uidData) > 1:
                print("Multiple uid rows are found in %s " % (self.dataCntrlStructPath))
                print(uidData)
                uidDescriptions[uidStr] = ['Multiple rows are found in %s' % (self.dataCntrlStructPath)]
            else:
                uidDescriptions[uidStr] = \
                    ['%s: %s' % (uidData['GlobalName'].values[0], uidData['Definition'].values[0])]
        return uidDescriptions

    def __repr__(self):
        tmp_SelfMeta = OrderedDict()

        # General Information (100%) - Collection of RAAD application meta.
        tmp_GenInfoDict = OrderedDict()
        tmp_GenInfoDict[
            'Description'] = f"Collection of information related around the RAAD API version, developer/poweruser/user classification, local collection information."
        tmp_GenInfoDict['Version'] = self.version.__repr__()
        tmp_GenInfoDict['Organization'] = self.org.__repr__()
        tmp_GenInfoDict['Application Debug Status'] = self.debug
        tmp_GenInfoDict['Binary Path'] = self.binaryPath
        tmp_GenInfoDict['Firmware Decode Directory'] = self.fwDir
        tmp_GenInfoDict['Data Control Structure Path'] = self.dataCntrlStructPath
        tmp_GenInfoDict['Extracted Information Formatted'] = self.configFileName
        tmp_GenInfoDict['Processed Information '] = self.resultsFolder
        # tmp_SelfMeta['configData'] = self.configData  # Not used yet.
        if not self._isNil(cObject=tmp_GenInfoDict):
            tmp_SelfMeta['General Information'] = tmp_GenInfoDict
        del tmp_GenInfoDict

        # Metadata Dimensionality (100%) - Compiler labeling of machine programming systems.
        tmp_UIDsFound = OrderedDict()
        if not self._isNil(cObject=self.telemetryHeaderDict):
            tmp_UIDsFound[
                'NVMe Standard and Intel Specific Identification (Telemetry header)'] = self.telemetryHeaderDict
        if not self._isNil(cObject=self.uidsFound):
            tmp_UIDsFound['Unique Identifiers Discovered'] = self.getUIDDescriptions(uidsFound=self.uidsFound)
        if not self._isNil(cObject=self.dataDictDimension):
            tmp_UIDsFound['Data Summary Size (width x length)'] = self.dataDictDimension
        if not self._isNil(cObject=self.systemInfo):
            tmp_UIDsFound[
                'Processing System Info'] = self.systemInfo  # System information of the data being accessed from.
        # @todo Contains too much data for the time being; will use a a basis for data processing...
        # if self.dataDict is not None:
        #    tmp_UIDsFound['Data Objects'] = self.dataDict
        # if self.deviceConfiguration is not None:
        #    tmp_UIDsFound['Device Configuration'] = self.deviceConfiguration
        if not self._isNil(cObject=tmp_UIDsFound):
            tmp_UIDsFound[
                'Description'] = "UID and content/sizing description for telemetry data objects found in the configuration file."
            tmp_UIDsFound.move_to_end('Description', last=False)
            tmp_SelfMeta["Meta Data Dimensionality"] = tmp_UIDsFound
        del tmp_UIDsFound

        # Time Series (60% => 75% => 100%) - Summary of algorithms, labeling, models, expansion of datasets
        # Developer assisted figures (50% => 85% => 100%) - Generated figures based on pertinent information highlighted in handbook.
        tmp_TS = OrderedDict()
        if not self._isNil(cObject=self.deviceSignature):
            tmp_TS[
                'Device Signature'] = self.deviceSignature  # Telemetry header state of most recent Node or time series.
        if not self._isNil(cObject=self.telemetryMetaStats):
            tmp_TS[
                'Machine learning Meta Statistics'] = self.telemetryMetaStats  # Telemetry data machine learning information.
        if not self._isNil(cObject=self.timeSeriesSignatures):
            tmp_TS['Series Signatures'] = self.timeSeriesSignatures
        if not self._isNil(cObject=self.assistedFigures):
            tmp_AF = OrderedDict()
            tmp_AF[
                'Description'] = "Generated figures from unique identifier object based on pertinent information highlighted in handbook.."
            tmp_AF['UID Figure(s)'] = self.assistedFigures  # PDF list of figures from UIDs.
            tmp_TS['Developer Figure(s)'] = tmp_AF
            del tmp_AF
        if not self._isNil(cObject=tmp_TS):
            tmp_TS[
                'Description'] = " Summary of algorithms, labeling, models, and expansion of datasets for the chronological sequences of telemetry object values collected in the processed configuration file (time-series of telemetry objects obtained during discrete, ordered telemetry pulls)"
            tmp_TS.move_to_end('Description', last=False)
            tmp_SelfMeta['Time Series'] = tmp_TS
        del tmp_TS

        # Machine Programming Research Engines
        # Machine Learning detailed expert analysis (20% => 25% => 50%), Intel Labs Compiler (25% => 35%) - Summary DFA, CFG, DFG, and maps of firmware.
        tmp_ExpertAnalysis = OrderedDict()
        if not self._isNil(cObject=self.firmwareDFA):
            tmp_firmwareDFA = OrderedDict()
            tmp_firmwareDFA[
                'Description'] = "Summary DFA, CFG, DFG, and maps of firmware. Memory, Control Flow, and Data Flow state in transitions maps from binary image."
            tmp_firmwareDFA[
                'Memory State'] = self.firmwareDFA  # Control, Data Flow state and transitions maps from firmware.
            tmp_ExpertAnalysis['Firmware Finite State Machine'] = tmp_firmwareDFA
        if not self._isNil(cObject=self.DFA):
            tmp_DFA = OrderedDict()
            tmp_DFA[
                'Description'] = 'Deterministic Finite Automata - Evaluation of control device state analysis information.'
            tmp_DFA['Analysis of State'] = self.DFA  # Deterministic Finite Automata - Device State information.
            tmp_ExpertAnalysis['Deterministic Finite Automata'] = tmp_DFA
        if not self._isNil(cObject=self.CFG):
            tmp_CFG = OrderedDict()
            tmp_CFG['Description'] = "Operating system task stack decoding."
            tmp_CFG['Control Flow Graphs'] = self.CFG  # Stack control flow graph.
            tmp_ExpertAnalysis['Control Flow Analysis'] = tmp_CFG
        # @todo too much data for now... so removing.
        # if not self._isNil(cObject=self.DFG):
        #    tmp_DFG = OrderedDict()
        #    tmp_DFG['Description'] = "Data Flow Meta context and data flow graph analysis from stack instance."
        #    tmp_DFG['Data Graph Analysis'] = self.DFG  # Stack data flow graph.
        #    tmp_ExpertAnalysis['Data Flow Graph'] = tmp_DFG
        if not self._isNil(cObject=self.MLMinedJira):
            tmpJiraInfo = OrderedDict()
            if self._isNil(self.telemetryHeaderDict):
                self.telemetryHeaderDict = dict()
                self.telemetryHeaderDict['reasonid.failuremodestring'] = 'ASSERT_DE003'  # @todo: code test overwrite
            tmpJiraInfo[
                'Description'] = f"Compiled nearest-neighbor Jira sets and clustering for {self.telemetryHeaderDict['reasonid.failuremodestring'][-1]}." + \
                                 " The tables display the nearest neighbors per Jira ID (i.e. the most similar Jiras per Jira ID). Each table contains a speculated and learned " + \
                                 "known-cause label for all contained Jiras." + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "Below you will also find a series of cluster plots, and a series of error-bar curve plots which evaluate the clustering quality. " + \
                                 "The vertical bars seen on the curve plots are representing the error or standard deviation found after training a clustering " + \
                                 "20 times and taking the average of a particular metric." + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "For each potential number of clusters k from 2 to 20, run the clustering 20 times and average the following:" + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "SSE: Sum of squared error/difference (SSE) between each node and the mean of the cluster it belongs/closest to. It can be used as a measure " + \
                                 "of variation within a cluster, and describes the average distance between each node in a cluster to it’s centroid (the center of mass of the cluster). " + \
                                 "Pick the value k right after the steepest slope in the curve (we want a high density within a cluster meaning the cluster is tightly packed)." + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "Silhouette Score: This corresponds to average distance between a node within a cluster and all other nodes in the same cluster, and the " + \
                                 "average distance between a node in one cluster and all other nodes in the next nearest cluster (measure how much a point is similar to its own " + \
                                 "cluster compared to other clusters; we want high separation between clusters; distance can be measured in different ways). Pick the k with " + \
                                 "the highest average score." + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "Distance (Jensen-Shannon) between two Gaussian Mixture Models (GMMs): Checks how much the GMMs trained on the two sets are similar, for each " + \
                                 "configuration of value k. The smaller is the JS-distance between the two GMMs, the more the GMMs agree on how to fit the data. This is focusing " + \
                                 "mainly on the reproducibility of the results between the two datasets. Pick the value k with the first largest sudden increase in distance, or " + \
                                 "the value k immediately after." + \
                                 f"{os.linesep}" + \
                                 f"{os.linesep}" + \
                                 "Gradient of BIC: Bayesian-Information Criterion (BIC) gives us an estimation on how good the GMM is in terms of predicting the data we " + \
                                 "have. The lower the BIC, the better the model is at predicting our distribution of data. To avoid overfitting, this technique penalizes " + \
                                 "models with a large number of clusters. However, this does not benefit complex distributions of data that might have many clusters. " + \
                                 "Usually, this score has smooth curve and can be seen to have level-sloped sections. Thus, this leads us to check the gradient of this curve " + \
                                 "as a better approach for the evaluation. The magnitude of the gradient tells us how much values are different. Pick the value " + \
                                 "k where the slope is equal to zero on average afterwards, or the first value k where the slope of the gradient suddenly changes from very " + \
                                 "steep upward slope to a more gentle upward slope."
            tmpJiraInfo['Data-mining for Jiras'] = self.MLMinedJira
            tmp_ExpertAnalysis['Jira Similarity Analysis and Clustering'] = tmpJiraInfo
            tempJiraTable = tmpJiraInfo['Nearest Neighbor Set Per Jira']
        else:
            tempJiraTable = None

        if not self._isNil(cObject=self.nlogTable):
            tmpNlogInfo = OrderedDict()
            tmpNlogInfo['Description'] = 'Compiled Chronological account of NLOG events.'
            tmpNlogInfo['Nlog Table'] = self.nlogTable
            tmp_ExpertAnalysis['NLOG Event Summary'] = tmpNlogInfo
            tempNlogTable = self.nlogTable
        else:
            tempNlogTable = None

        if not self._isNil(cObject=tmp_ExpertAnalysis):
            tmp_ExpertAnalysis[
                'Description'] = f" Summary DFA, CFG, DFG, maps of firmware, and speculative root cause classification."
            tmp_ExpertAnalysis.move_to_end('Description', last=False)
            tmp_SelfMeta['Machine Learning Expert Analysis'] = tmp_ExpertAnalysis
        del tmp_ExpertAnalysis
        # @todo Add JIRA speculative root cause evaluation.
        # @todo Add Auto-Perf, MISM, control flag, code repair recommendation, speculative fault module/changesets, recommended test case verification set, etc...

        # Artifical Intelligence expert forcast context (20% => 100%) - Drive profile classification - summary of data labeled based on state models
        tmp_DAF = OrderedDict()
        if not self._isNil(cObject=self.MLProfiles):
            tmp_MLPCC = OrderedDict()
            tmp_MLPCC[
                'Description'] = "Summary of data labeled based on state models profile classification clustering."
            tmp_MLPCC[
                'Machine Learning Data Profile(s)'] = self.MLProfiles  # Matrix profile data labeling of time series.
            tmp_DAF['Machine Learning Signature(s)'] = tmp_MLPCC
            del tmp_MLPCC
        if not self._isNil(cObject=self.ARMAFigures):
            tmp_ARMAF = OrderedDict()
            tmp_ARMAF[
                'Description'] = "Auto Aggressive Moving Average Forecast for historical to future trend speculation or predictions."
            tmp_ARMAF['ARMA Figures'] = self.ARMAFigures  # Auto Aggressive Time Series forecast figures.
            tmp_DAF["Assisted Graphs"] = tmp_ARMAF
            del tmp_ARMAF
        if not not self._isNil(cObject=self.RNNFigures) and not self._isNil(cObject=self.RNNAccuracy):
            tmp_RNNMeta = OrderedDict()
            tmp_RNNMeta[
                'Description'] = "Recurrent Neural Network (RNN) and Long-Short Term Memory Graphs and Metrics for Time series"
            tmp_RNNMeta[
                'Figures'] = self.RNNFigures  # Recurrent Neural Network (RNN) and Long-Short Term Memory (LSTM) figures.
            tmp_RNNMeta['Accuracy'] = self.RNNAccuracy  # RNN-LSTM metrics for training.
            tmp_DAF['AI-RNN-LSTM'] = tmp_RNNMeta
            del tmp_RNNMeta
        if not self._isNil(cObject=tmp_DAF):
            tmp_DAF[
                "Description"] = "Artificial Intelligence characteristics based on input meta data used in predictive classification, value, state forecasting etc."
            tmp_DAF.move_to_end('Description', last=False)
            tmp_SelfMeta['Developer Assisted Graphing'] = tmp_DAF
        del tmp_DAF

        # Database Upload (100%)
        if not self._isNil(cObject=self.DataLakeMeta):
            tmp_DU = OrderedDict()
            tmp_DU['Description'] = "Database upload meta information for signature."
            tmp_DU['Upload Meta'] = self.DataLakeMeta  # Data lake information from data upload
            tmp_SelfMeta['Database Context'] = tmp_DU
            del tmp_DU

        reducedDict = self._reduceDict(selfDict=tmp_SelfMeta)
        if tempJiraTable is not None:
            reducedDict['Machine Learning Expert Analysis']['Jira Similarity Analysis and Clustering'][
                'Data-mining for Jiras']['Nearest Neighbor Set Per Jira'] = tempJiraTable
        if tempNlogTable is not None:
            reducedDict['Machine Learning Expert Analysis']['NLOG Event Summary']['Nlog Table'] = tempNlogTable

        return reducedDict

    @staticmethod
    def _isNil(cObject=None, baseType=None):
        """
        Generic type default constructor compare to determine if data is filled.
        Args:
            cObject: Generic Object
            baseType: List of types for construction operator evaluation.

        Returns: default compare status.

        """
        sStatus = None
        if baseType is None:
            baseType = (str, list, set, dict, OrderedDict)

        if cObject is None:
            sStatus = True
        else:
            iType = type(cObject)
            if isinstance(iType, baseType):
                evalObj = iType()
                if cObject == evalObj:
                    sStatus = True
                elif cObject != evalObj:
                    sStatus = False
            else:
                print(f" Unknown {os.linesep}{pprint.pformat(whoami())}")
                sStatus = False
        return sStatus

    def _reduceDict(self, selfDict=None):
        if selfDict is None:
            return None

        if isinstance(selfDict, dict):
            inType = dict
        elif isinstance(selfDict, OrderedDict):
            inType = OrderedDict
        else:
            inType = dict
            print(f"API type usage issue due to inType={inType}:{os.linesep}{pprint.pformat(whoami)}")
            return None

        reducedDict = inType()
        try:
            for iKey, iValue in selfDict.items():
                try:
                    if isinstance(iValue, inType) and iValue != inType():
                        rValue = self._reduceDict(selfDict=iValue)
                        reducedDict[iKey] = rValue
                    elif isinstance(iValue, list) and iValue != list():
                        rValue = set(iValue)
                        reducedDict[iKey] = list(rValue)
                    elif iValue is not None and \
                            iValue != inType() and \
                            iValue != list() and \
                            iValue != set() and \
                            iValue != str():
                        rValue = iValue
                        reducedDict[iKey] = rValue
                except BaseException as ErrorInnerContext:
                    print(f"{whoami()} {ErrorInnerContext}")
                    # pass or continue
                    continue
        except BaseException as ErrorContext:
            print(f"{whoami()} {ErrorContext}")
        return reducedDict

    def updateInitialize(self,
                         binaryPath=None,
                         fwDir=None,
                         dataCntrlStructPath=None,
                         nlogFolder=None,
                         configFileName=None,
                         resultsFolder=None,
                         extractBinaries=False,
                         useCSV=False,
                         debug=False):
        """
        function for updating the initial values of the analysisReport

        Args:
            binaryPath: relative path to the folder where the telemetry binaries are stored
            fwDir: relative path to the folder where the firmware parsers are stored
            dataCntrlStructPath: relative path to the file where the data control structures are stored
            nlogFolder: Folder containing negative logs and tokenizers
            configFileName: String representation of the name of the .ini file where the time series is stored or will
            be stored
            resultsFolder: relative path to folder where the results of intermediate operations will be stored
            extractBinaries: boolean flag that indicates the choice using binary files in generate
            a time series automatically
            useCSV: Boolean flag to indicate that the file to be used is a .csv file instead of the .ini file
            debug: boolean flag for verbose printing
        """
        self.debug = debug
        self.org = UID_Org(vendor="Intel", bussinessUnit="NSG", group="STG", team="RAMP-RAAD-AMPERE")
        self.version = UID_Application(uid=1, major=1, minor=1, data=None)
        self.systemInfo = self.constructSystemInfo()  # System information of the data being accessed from.

        if binaryPath is not None:
            self.binaryPath = binaryPath  # relative path
        if fwDir is not None:
            self.fwDir = fwDir
        if dataCntrlStructPath is not None:
            self.dataCntrlStructPath = os.path.abspath(dataCntrlStructPath)
        if nlogFolder is not None:
            self.nlogFolder = nlogFolder
        if configFileName is not None:
            if useCSV:
                print("Replacing file name...")
                configFileName = configFileName.replace(".ini", ".csv")
            self.configFileName = configFileName
        if resultsFolder is not None:
            self.resultsFolder = resultsFolder
        if self.setTimeSeries(extractBinaries=extractBinaries, debug=debug) is False:
            print("Time Series could not be extracted correctly. Please try a different .ini file")
        self.setMLMinedJira()
        self.setNlogInfo()
        if self.setDeviceConfiguration() is False:
            print("Device Configuration could not be set correctly.")
        self.setFirmwareDFA()
        self.setDeviceSignature()
        self.setTelemetryMetaStats()
        if self.assistedFigures is None or self.assistedFigures is dict():
            self.setAssistedFigures()
        dataDictFlat = DictionaryFlatten(self.dataDict)
        self.dataDictDimension = dataDictFlat.getSize()
        if self.dataDict is not None:
            self.uidsFound = self.dataDict.keys()
        return

    def updateReportMeta(self,
                         uidsFound=None,
                         deviceConfiguration=None,
                         dataDict=None, dataDictDimension=None,
                         DFA=None, CFG=None, DFG=None,
                         MLProfiles=None,
                         jiraNeighbors=None,
                         jiraFigures=None,
                         tableTitles=None,
                         nlogTable=None,
                         assistedFigures=None,
                         timeSeriesSignatures=None):
        # @todo
        # Expected Report for Users
        # Application (100%)
        #    UIDs present
        #    version
        if uidsFound is not None:
            self.uidsFound = uidsFound
            self.uidsFound = sorted(self.uidsFound, key=self.getUIDValue)

        # Device Configuration (100%)
        if deviceConfiguration is not None:
            self.deviceConfiguration = deviceConfiguration

        # Metadata Dimensionality (100%)
        #    Compiler labeling of machine programming systems
        if dataDict is not None:
            self.dataDict = dataDict
            self.setDeviceConfiguration()
            self.extractTelemetryHeader()
            self.setFirmwareDFA()
            self.setDeviceSignature()
            self.setTelemetryMetaStats()

        if dataDictDimension is not None:
            self.dataDictDimension = dataDictDimension

        # Detailed expert Analysis (20%), Intel Labs Compiler (25%)
        #    Deterministic finite automaton
        #    Summary CFG or DFG and maps of firmware.
        # @todo
        if DFA is not None:
            self.DFA = DFA
        if CFG is not None:
            self.CFG = CFG
        if DFG is not None:
            self.DFG = DFG

        # Machine Learning (20%)
        #    Drive profile classification clustering - summary of data labeled based on state models
        if MLProfiles is not None:
            self.MLProfiles = MLProfiles
            # @todo Artificial Intelligence Neural Networks

        if jiraNeighbors is not None and jiraFigures is not None:
            if self.setMLMinedJira(nearNeighborTables=jiraNeighbors,
                                   jiraClusteringPDFList=jiraFigures,
                                   tableTitles=tableTitles) is False:
                print('Error when setting MLMinedJira in updateReportMeta()...')

        if nlogTable is not None:
            if self.setNlogInfo(nlogTable=nlogTable) is False:
                print('Error while handling NLOG parsing...')
        # Developer assisted Figures (50%)
        #    Generated figures based on pertinent information highlighted in handbook
        if assistedFigures is not None:
            self.assistedFigures = assistedFigures
        elif self.assistedFigures is None:
            self.setAssistedFigures()

        # Time Series (60%)
        #    Summary of algorithms, labeling, models, expansion of datasets
        if timeSeriesSignatures is not None:
            self.timeSeriesSignatures = timeSeriesSignatures
            # @todo ARMA, RNN-LSTM, uniqueData

        return

    def extractTelemetryHeader(self):
        """function for extracting the telemetry header

        Returns:
            telemetryHeader = dictionary for telemetry data object containing the header information
        """
        try:
            telemetryHeader = self.dataDict['uid-240']  # 240: telemetry header objects
            telemetryTokens = dict()
            for iKey, iValue in telemetryHeader.items():
                if 'reserved' not in iKey:
                    telemetryTokens[iKey] = iValue
            self.telemetryHeaderDict = telemetryTokens
        except:
            telemetryTokens = None
            print("Failed to extract telemetry header. The config file did not have it")
        return telemetryTokens

    def getInfo(self):
        return [self.version, self.org, self.systemInfo]

    def getTimeSeries(self):
        """
        function for obtaining the dictionary of the time series data
        Returns:
        """
        if self.dataDict is None:
            print("Time series have not been set. Please set the time series before calling other functions")

        return self.dataDict

    def setTimeSeries(self, extractBinaries=True, debug=False):
        """
        function for generating the dictionary of the time series data
        Returns:
        """

        try:
            if extractBinaries:
                binGen = generateTSBinaries(outpath="divided-bin", debug=debug)
                binGen.parseBinaryOnly(self.binaryPath)
                formatGen = formatTSFiles(outpath=self.resultsFolder, debug=debug)
                plainTextFiles, nlogFiles = formatGen.generatePlainText(fwDir=self.fwDir, nlogFolder=self.nlogFolder,
                                                                        binDir="divided-bin", mode=2)
                formatGen.digestTextFiles(plainTextFiles=plainTextFiles, nlogFiles=nlogFiles,
                                          outfile=self.configFileName, mode=2)
            if self.configFileName.find(".csv") != -1:
                print("Using CSV file...")
                self.configData = None
                self.dataDict = preprocessingAPI.loadCSVIntoDict(configFileName=self.configFileName, debug=debug)
                self.telemetryHeaderDict = self.extractTelemetryHeader()
            else:
                print("Using INI file...")
                self.configData = preprocessingAPI.readFileIntoConfig(configFileName=self.configFileName)
                self.dataDict = preprocessingAPI.loadConfigIntoDict(config=self.configData, debug=debug)
                self.telemetryHeaderDict = self.extractTelemetryHeader()
        except:
            print("Time series were not set correctly...")
            self.configData = None
            self.dataDict = None
            self.telemetryHeaderDict = None
            return False

        return True

    def constructSystemInfo(self):
        cpufreq = psutil.cpu_freq()
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
        swap = psutil.swap_memory()
        svmem = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        info = dict()
        # System Platform Info
        info['platform'] = platform.system()
        info['platform release'] = platform.release()
        info['platform version'] = platform.version()
        info['platform architecture'] = platform.machine()
        info['platform network name'] = platform.node()
        info['platform boot time'] = f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
        # System Socket Info
        info['socket hostname'] = str(socket.gethostname())
        info['socket ip address'] = str(socket.gethostbyname(socket.gethostname()))
        info['socket mac address'] = str(':'.join(re.findall('..', '%012x' % uuid.getnode())))
        # System CPU Info
        info['cpu processor'] = str(platform.processor())
        info['cpu cores physical'] = str(psutil.cpu_count(logical=False))
        info["cpu cores logical"] = str(psutil.cpu_count(logical=True))
        info['cpu frequency max'] = f"{cpufreq.max:.2f}Mhz"
        info['cpu frequency min'] = f"{cpufreq.min:.2f}Mhz"
        info['cpu frequency current'] = f"{cpufreq.current:.2f}Mhz"
        # System RAM
        info["ram total"] = (f"{self._getBytesSize(svmem.total)}")
        info["ram available"] = (f"{self._getBytesSize(svmem.available)}")
        info["ram used"] = (f"{self._getBytesSize(svmem.used)}")
        info["ram percentage"] = (f"{svmem.percent}%")
        # Operating System SWAP
        info['swap total'] = (f"{self._getBytesSize(swap.total)}")
        info['swap free'] = (f"{self._getBytesSize(swap.free)}")
        info['swap used'] = (f"{self._getBytesSize(swap.used)}")
        info['swap percentage'] = (f"{swap.percent}%")
        # Disk IO statistics since boot
        info["disk reads"] = f"{self._getBytesSize(disk_io.read_bytes)}"
        info["disk writes"] = f"{self._getBytesSize(disk_io.write_bytes)}"
        # Diskpart information
        partitions = psutil.disk_partitions()
        for partition in partitions:
            partitionPrefix = (f"{partition.device} {partition.mountpoint} {partition.fstype}")
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # This can be catched due to the disk that isn't ready
                continue
            info[f"partition size {partitionPrefix}"] = f"{self._getBytesSize(partition_usage.total)}"
            info[f"partition used {partitionPrefix}"] = f"{self._getBytesSize(partition_usage.used)}"
            info[f"partition free {partitionPrefix}"] = f"{self._getBytesSize(partition_usage.free)}"
            info[f"partition percentage {partitionPrefix}"] = f"{partition_usage.percent}%"
        # Network information
        # Get IO statistics since boot
        net_io = psutil.net_io_counters()
        info["network sent bytes"] = f"{self._getBytesSize(net_io.bytes_sent)}"
        info["network receive bytes"] = f"{self._getBytesSize(net_io.bytes_recv)}"
        # Get all network interfaces (virtual and physical)
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            for address in interface_addresses:
                if str(address.family) == 'AddressFamily.AF_INET':
                    info[f"interface ip address {interface_name}"] = f"{address.address}"
                    info[f"interface netmask {interface_name}"] = f"{address.netmask}"
                    info[f"interface broadcast ip {interface_name}"] = f"{address.broadcast}"
                elif str(address.family) == 'AddressFamily.AF_PACKET':
                    info[f"interface mac address {interface_name}"] = f"{address.address}"
                    info[f"interface netmask {interface_name}"] = f"{address.netmask}"
                    info[f"interface broadcast MAC {interface_name}"] = f"{address.broadcast}"
        # GPU information
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_id = gpu.id  # Get the GPU id
                gpu_name = gpu.name  # Name of GPU
                gpu_load = f"{gpu.load * 100}%"  # Get % percentage of GPU usage of that GPU
                gpu_free_memory = f"{gpu.memoryFree}MB"  # Get free memory in MB format
                gpu_used_memory = f"{gpu.memoryUsed}MB"  # Get used memory
                gpu_total_memory = f"{gpu.memoryTotal}MB"  # Get total memory
                gpu_temperature = f"{gpu.temperature}°C"  # Get GPU temperature in Celsius
                gpu_uuid = gpu.uuid  # GPU unique id
                gpuPrefix = f"gpu-{gpu_uuid}-{gpu_id}-{gpu_name}"
                info[f"gpu {gpuPrefix}"] = f"{gpu_load}"
                info[f"gpu {gpuPrefix}"] = f"{gpu_free_memory}"
                info[f"gpu {gpuPrefix}"] = f"{gpu_used_memory}"
                info[f"gpu {gpuPrefix}"] = f"{gpu_total_memory}"
                info[f"gpu {gpuPrefix}"] = f"{gpu_temperature}"
        except:
            print("Failed to access GPU information. check GPUtil installation")
        return info

    def getSystemInfo(self):
        return self.systemInfo

    def getApplications(self):
        """
        Applications [List]
        |-> Application (uID, Name, Version, Functions)
        Returns:
        """
        # @todo
        return

    def setApplications(self):
        """
        Applications [List]
        |-> Application (uID, Name, Version, Functions)
        Returns:
        """
        # @todo
        # Populate the class with unique id, name, version, and function of the class
        return

    def getDeviceConfiguration(self, sigMode="latest", index=0):
        """
        Solid State Device configuration
        Returns: (Meta of SSD, Factory Configuration of SSD)
        """
        deviceConfiguration = {}
        if self.deviceConfiguration is not None:
            fConfigInfoTable = {}
            factoryConfig = {}
            if sigMode == "latest":
                index = len(self.deviceConfiguration['factoryConfig']['uid'])

            for key in self.deviceConfiguration['fConfigInfoTable'].keys():
                fConfigInfoTable[key] = self.deviceConfiguration['fConfigInfoTable'][key][index]

            for key in self.deviceConfiguration['factoryConfig'].keys():
                factoryConfig[key] = self.deviceConfiguration['factoryConfig'][key][index]

            deviceConfiguration['factoryConfig'] = factoryConfig
            deviceConfiguration['fConfigInfoTable'] = fConfigInfoTable

        else:
            print('device configuration has not been set yet. Please set device configuration')
            deviceConfiguration = None

        return deviceConfiguration

    def setDeviceConfiguration(self):
        """
        Solid State Device configuration
        Returns: (Meta of SSD, Factory Configuration of SSD)
        """
        deviceConfiguration = dict()
        try:
            fConfigInfoTable = self.dataDict['uid-58']
            deviceConfiguration['fConfigInfoTable'] = fConfigInfoTable
            validState = True
        except:
            print('uid-58 device configuration could not be extracted from the config file')
            validState = False
        try:
            # Access static media saved config.
            factoryConfig = self.dataDict['uid-59']
            deviceConfiguration['factoryConfig'] = factoryConfig
            validState = (validState and True)
        except:
            try:
                # Access live stream config.
                factoryConfig = self.dataDict['uid-297']
                deviceConfiguration['factoryConfig'] = factoryConfig
                validState = (validState and True)
            except:
                validState = False
                print('uid-59 or uid-297 device configuration could not be extracted from the config file')
        self.deviceConfiguration = deviceConfiguration
        return validState

    def getDeviceSignature(self, sigMode="index", index=0):
        """
        Return the telemetry header state of most recent Node or Timeseries.
        sigMode: Mode of accessing data either by a given index or the entire series.
        Returns:
        """
        deviceSignature = {}
        if self.deviceSignature is not None:
            if sigMode == "latest":
                index = len(self.deviceSignature['reasonCode'])

            deviceSignature['reasonCode'] = self.deviceSignature['reasonCode'][index]
            deviceSignature['failureModeString'] = self.deviceSignature['failureModeString'][index]
            deviceSignature['fwRevision'] = self.deviceSignature['fwRevision'][index]
            deviceSignature['blRevision'] = self.deviceSignature['blRevision'][index]
            deviceSignature['serialNumber'] = self.deviceSignature['serialNumber'][index]

        else:
            print("device signature has not been set. Please set device signature")
            deviceSignature = None

        return deviceSignature

    def setDeviceSignature(self):
        """
        Return the telemetry header state of most recent Node or time series.
        sigMode: Mode of accessing data either by a given index or the entire series.
        Returns:
        """

        deviceSignature = dict()
        if self.telemetryHeaderDict is not None:
            if int(self.telemetryHeaderDict['reasonid.reason.reasoncode'][-1]) == 0:
                reasonCode = '0 : HEALTHY'
            else:
                reasonCode = '1 : ASSERT detected'
            deviceSignature['reasonCode'] = reasonCode
            deviceSignature['failureModeString'] = self.telemetryHeaderDict['reasonid.failuremodestring'][-1]
            deviceSignature['fwRevision'] = self.telemetryHeaderDict['reasonid.fwrevision']
            deviceSignature['blRevision'] = self.telemetryHeaderDict['reasonid.blrevision']
            deviceSignature['serialNumber'] = self.telemetryHeaderDict['reasonid.serialnumber']
        else:
            print("Telemetry header has not been extracted. Device signature has not been found")
            self.deviceSignature = None
            return False

        self.deviceSignature = deviceSignature
        return True

    def getTelemetryMetaStats(self):
        """
        Labeling of data for Machine Programming Learning systems
        Returns:
            Telemetry data machine learning information.
            [UID List]|
             |-> [Time indexs] |
                  |-> (dataSets, width, length)
                       |-> Meta Sets  width, length
            Time series List of Above
            -----------------------------------
            Telemetry: Telemetry information in respect the current payload
                Internal: Telemetry version is the internal tracking across all products.
                    Major: [1 to M]
                    Minor: [0 to K]
                Protocol Interface: = ["NVMe", "SATA-ACS"] - The specific protocol used.
                Type: ["Host", "Controller"] - Host or controller-initiated telemetry asynchronous command.
                Snapshots: Telemetry binary payloads names and path pairs.
                    Filenames: "PHAB8506001G3P8AGN_sample.bin" - File name on the host system.
                    Paths: "C:/Source/SSDDev/NAND/gen3/tools/telemetry/sample" - Path on the host system to binary.
                    PayloadValidity: ["Verified", "Unknown", "Corrupted"]
                    creationTime: [year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]]] - Represents the time at which the data object was imported to the tool.
        """
        return self.telemetryMetaStats

    def setTelemetryMetaStats(self):
        telemetryMetaStats = {}
        if self.dataDict is None:
            telemetryMetaStats['PayloadValidity'] = "Unknown"
            print("Payload has not been verified. Please try to set Time Series to verify the payload and generate the "
                  "general data dictionary")
            self.telemetryMetaStats = telemetryMetaStats
            return False
        else:
            if self.telemetryHeaderDict is not None:
                telemetryMetaStats['PayloadValidity'] = "Verified"
            else:
                telemetryMetaStats['PayloadValidity'] = "Corrupted"
                self.telemetryMetaStats = telemetryMetaStats
                print("Payload is corrupted. Telemetry Meta Stats will be incomplete. Please proceed with caution")
                return False
        telemetryMetaStats['UID-List'] = self.dataDict.keys()
        if self.binaryPath is None:
            print("Incorrect Binary path.")
            self.telemetryMetaStats = telemetryMetaStats
            return False
        else:
            telemetryMetaStats['Path'] = self.binaryPath
        telemetryMetaStats['Telemetry Header Major Version'] = self.telemetryHeaderDict['reasonid.majorversion']
        telemetryMetaStats['Telemetry Header Minor Version'] = self.telemetryHeaderDict['reasonid.minorversion']
        inputFolder = os.path.join(os.getcwd(), self.binaryPath)
        fileList = [os.path.join(inputFolder, file) for file in sorted(os.listdir(inputFolder),
                                                                       key=lambda dir_t:
                                                                       preprocessingAPI.getDateFromName(dir_t))
                    if os.path.isfile(os.path.join(inputFolder, file))]
        telemetryMetaStats['Filenames'] = fileList
        telemetryMetaStats['creationTime'] = list(map(preprocessingAPI.getDateFromName, fileList))
        if self.telemetryHeaderDict is None:
            print("Empty Telemetry header dictionary.")
            self.telemetryMetaStats = telemetryMetaStats
            return False
        else:
            numberOfTimeSteps = len(self.telemetryHeaderDict['name'])
            telemetryMetaStats['Time Indices'] = [range(0, numberOfTimeSteps - 1, 1)]

        telemetryMetaStats['dataSets'] = {}
        for objectDataDict in self.dataDict.keys():
            currentObject = self.dataDict[objectDataDict]
            subDict = dict()
            subDict['width'] = len(currentObject.keys())
            subDict['length'] = len(currentObject['core'])
            telemetryMetaStats['dataSets'][objectDataDict] = subDict

        self.telemetryMetaStats = telemetryMetaStats
        return True

    # ML Clustering+Profile functions
    def getMLClustering(self):
        # @todo
        return

    def setMLClustering(self):
        # @todo
        return

    def getMLProfiles(self):
        """
        Data labeled based on the state from models.
        Returns:
        """
        return self.MLProfiles

    def setMLProfiles(self, subSeqLen=None):
        # @todo validate generation of each object...
        """
        Data labeled based on the state from models.
        Returns:
        """
        if subSeqLen is None:
            subSeqLen = 4
        MLProfiles = {}
        try:
            MLProfiles['MP'] = preprocessingAPI().generateMP(self.dataDict, subSeqLen=subSeqLen)
            self.MLProfiles = MLProfiles
        except:
            self.MLProfiles = None
        return True

    def getMLMinedJira(self):
        return self.MLMinedJira

    def setMLMinedJira(self, nearNeighborTables=None, jiraClusteringPDFList=None, tableTitles=None):
        if nearNeighborTables is None or jiraClusteringPDFList is None or tableTitles is None:
            print('Nearest-neighbor data is undefined, failed setting MLMinedJira in gatherMeta')
            self.MLMinedJira = None
            return False
        tmpJiraInfo = dict()
        tmpJiraInfo['Nearest Neighbor Set Per Jira'] = nearNeighborTables
        tmpJiraInfo['Jira Cluster Figures'] = jiraClusteringPDFList
        tmpJiraInfo['Known Cause Table Titles'] = tableTitles
        self.MLMinedJira = tmpJiraInfo
        return True

    def getNlogInfo(self):
        return self.nlogTable

    def setNlogInfo(self, nlogTable=None):
        if nlogTable is None:
            self.nlogTable = None
            return False
        else:
            self.nlogTable = nlogTable
            return True

    # Assisted Figures Functions
    def getAssistedFigures(self):
        """
        Generated figures based on pertinent information highlighted in handbook.
        Returns:

        """
        if self.assistedFigures is None:
            print("Assisted figures have not been set. Please set assisted figures and try again")

        return self.assistedFigures

    def setAssistedFigures(self, outfile=None, numCores=None, driveType='ADP'):
        """
        Generated figures based on pertinent information highlighted in handbook.
        Returns:

        """
        if outfile is None:
            outfile = 'telemetryDefault'
        if numCores is None:
            numCores = 2
        if driveType == 'ADP':
            driveMode = 1
        else:
            driveMode = 2

        figures = {}
        fields = []
        statusFlag = True
        for objectID in self.objectsOfInterest:
            try:
                if objectID == 'uid-41':
                    dhg = TSVDefragHistory.DefragHistoryGrapher(mode=driveMode)
                    dhgDataDict = preprocessingAPI.transformDict(intermediateDict=self.dataDict, debug=self.debug)
                    currentPDF = dhg.writeTSVisualizationToPDF(dataDict=dhgDataDict, bandwidthFlag=True, out=outfile,
                                                               numCores=numCores)
                else:
                    vts = TSVGenericGraph.visualizeTS()
                    currentPDF = vts.generatePDFFile(dataDict=self.dataDict, objectID=objectID, outfile=outfile,
                                                     fields=fields, visualizeAllFields=True,
                                                     combine=False)
                figures[objectID] = currentPDF
            except BaseException as ErrorFound:
                errorString = (f"{ErrorFound} {whoami()}")
                print(f"Object with {objectID} was not contained in the configuration file. {errorString}")
                statusFlag = False
        self.assistedFigures = figures
        return statusFlag

    def setAssistedFiguresParallel(self, outfile=None, numCores=None, driveType='ADP',
                                   max_workers=None, timeOut=180, inOrder=True, runSequential=True, debug=False):
        """
        Generated figures based on pertinent information highlighted in handbook.
        Returns:

        """
        if outfile is None:
            outfile = 'telemetryDefault'
        if numCores is None:
            numCores = 2
        if driveType == 'ADP':
            driveMode = 1
        else:
            driveMode = 2

        figures = list()
        fields = list()
        kwargsList = list()
        statusFlag = True
        for objectID in self.objectsOfInterest:
            try:
                if objectID == 'uid-41':
                    dhg = TSVDefragHistory.DefragHistoryGrapher(mode=driveMode)
                    dhgDataDict = preprocessingAPI.transformDict(intermediateDict=self.dataDict, debug=self.debug)
                    currentPDF = dhg.writeTSVisualizationToPDF(dataDict=dhgDataDict, bandwidthFlag=True, out=outfile,
                                                               numCores=numCores)
                    if currentPDF is not None:
                        figures.append(currentPDF)
                else:
                    kwargsList_Obj = {'dataDict': self.dataDict,
                                      'objectID': objectID,
                                      'outfile': outfile,
                                      'fields': fields,
                                      'visualizeAllFields': True,
                                      'combine': False}
                    kwargsList.append(kwargsList_Obj)
            except BaseException as ErrorFound:
                errorString = (f"{ErrorFound} {whoami()}")
                print(f"Object with {objectID} was not contained in the configuration file. {errorString}")
                statusFlag = False
        try:
            functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                             functionName=TSVGenericGraph.visualizeTS().generatePDFFile,
                                                                             fParameters=kwargsList,
                                                                             workers=max_workers,
                                                                             timeOut=timeOut,
                                                                             inOrder=inOrder,
                                                                             runSequential=runSequential)
            iResults = functionContext.execute()
            for fig in iResults:
                if fig is not None:
                    figures.append(fig)
        except BaseException as ErrorFound:
            errorString = (f"{ErrorFound} {whoami()}")
            print(f"Object execution error: {errorString}")
            if statusFlag is True:
                statusFlag = False
        self.assistedFigures = figures
        return statusFlag

    # ARMA Functions
    def getARMAFigures(self):
        if self.ARMAFigures is None:
            print("ARMA figures have not been set. Please set ARMA figures and try again")
        return self.ARMAFigures

    def setARMAFigures(self, inputFile=None, matrixProfile=None, subSeqLen=None, targetObject=None, targetField=None,
                       debug=None):
        if inputFile is None or matrixProfile is None or subSeqLen is None or targetObject is None or targetField is None or debug is None:
            return

        figures = []
        arma = ARMA.MediaErrorPredictor(inputFile=inputFile, matrixProfile=matrixProfile, subSeqLen=subSeqLen,
                                        debug=debug)
        figures.append(arma.writeARMAToPDF(targetObject, targetField))
        self.ARMAFigures = figures
        return

    # RNN functions
    def getRNNFigures(self):
        if self.RNNFigures is None:
            print("ARMA figures have not been set. Please set ARMA figures and try again")

        return self.RNNFigures, self.RNNAccuracy

    def setRNNFigures(self, configFilePath=None, inputWidth=None, labelWidth=None, shift=None, batchSize=None,
                      hiddenLayers=None, targetObject=None, targetFields=None, plotColumn=None, maxEpochs=None,
                      matrixProfileFlag=None, subSeqLen=None,
                      embeddedEncoding=None, categoricalEncoding=None, debug=None):
        # Parameter verification.
        if configFilePath is None or inputWidth is None or labelWidth is None or shift is None or \
                batchSize is None or hiddenLayers is None or targetObject is None or \
                targetFields is None or plotColumn is None or maxEpochs is None or \
                matrixProfileFlag is None or subSeqLen is None or embeddedEncoding is None or \
                categoricalEncoding is None or debug is None:
            return

        figures = []
        rnn = RNN.timeSeriesRNN(configFilePath=configFilePath, matrixProfileFlag=matrixProfileFlag, subSeqLen=subSeqLen,
                                embeddedEncoding=embeddedEncoding, categoricalEncoding=categoricalEncoding, debug=debug)
        pdf, accuracy = rnn.writeRNNtoPDF(inputWidth, labelWidth, shift, batchSize, hiddenLayers, targetObject,
                                          targetFields, plotColumn, maxEpochs)
        figures.append(pdf)
        self.RNNFigures = figures
        self.RNNAccuracy = accuracy

    # DFA Functions
    def getFirmwareDFA(self, gitURL=None, changeset=None):
        """
        Control, Data Flow state and transitions maps from firmware.
        Args:
            gitURL: Source Code Repository
            changeset: Changeset associated with the code change.

        Returns:
        """
        if self.firmwareDFA is None:
            print("firmwareDFA has not been set. Please set firmwareDFA")
            print(gitURL, changeset)
        return self.firmwareDFA

    def setFirmwareDFA(self, gitURL=None, changeset=None):
        """
        Control, Data Flow state and transitions maps from firmware.
        Args:
            gitURL: Source Code Repository
            changeset: Changeset associated with the code change.

        Returns:
        """
        try:
            firmwareDFA = dict()
            firmwareDFA['fwRevision'] = self.telemetryHeaderDict['reasonid.fwrevision']
            firmwareDFA['blRevision'] = self.telemetryHeaderDict['reasonid.blrevision']
        except:
            print("firmware DFA was not set correctly...")
            print(gitURL, changeset)
            self.firmwareDFA = None
            return False
        self.firmwareDFA = firmwareDFA

        return True

    def getJIRA(self):
        """
        JIRA: (Identifiers: [“NSGSE-12345”], [URL: https://nsg-jira.intel.com/browse/], Major: [1 to M], Minor: [0 to K])
        """
        # @todo
        return

    def setJIRA(self):
        """
        JIRA: (Identifiers: [“NSGSE-12345”], [URL: https://nsg-jira.intel.com/browse/], Major: [1 to M], Minor: [0 to K])
        """
        # @todo
        return

    def getDataLakeMeta(self):
        """
        Data Lake: ( [Identifiers: “123456789”], [URL:  https://datalake.intel.com/browse/key=], Major: [1 to M], Minor: [0 to K]
        """
        if hasattr(self, "DataLakeMeta"):
            return self.DataLakeMeta
        else:
            return {}

    def setDataLakeMeta(self,
                        axonID,
                        axonURL="https://axon.intel.com",
                        MetaDataFile=None,
                        UploadedFile=None,
                        DownloadedFile=None):
        """
        Data Lake: ( [Identifiers: “123456789”], [URL:  https://datalake.intel.com/browse/key=], Major: [1 to M], Minor: [0 to K] )
        """

        # set Data Lake Meta by creating dictionary of data items
        self.DataLakeMeta = {
            "axonID": axonID,
            "URL": "{0}/app/view/{1}".format(axonURL, axonID),
            "Meta": MetaDataFile,
            "Upload": UploadedFile,
            "Download": DownloadedFile,
            "Major": 1,
            "Minor": 0
        }

        return

    def getClasstoDictionary(self):
        return self.__repr__()

    def getSuperDictionary(self):
        objDictAny = preprocessingAPI.classToDictionary(self, filterData=True)
        if self.debug:
            print(objDictAny, flush=True)
        objDictAny = self.getFlattenDictionary(dd=objDictAny, separator='_', prefix='')
        return objDictAny

    def getFlattenDictionary(self, dd, separator='_', prefix=''):
        return {prefix + separator + k if prefix else k: v
                for kk, vv in dd.items()
                for k, v in self.getFlattenDictionary(vv, separator, kk).items()
                } if isinstance(dd, dict) else {prefix: dd}

    def toString(self):
        strList = []
        for iterationItem in (self.version.getWalkList()):
            strList.append(iterationItem)
        for iterationItem in (self.org.getWalkList()):
            strList.append(iterationItem)
        if isinstance(self.systemInfo, dict):
            for iterationItem in list(self.systemInfo):
                strList.append(iterationItem)

    @staticmethod
    def _getBytesSize(bytesIn=0, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        bytesValue = bytesIn
        if bytesValue is None or 0:
            return int(0)
        elif (isinstance(bytesValue, int) or isinstance(bytesValue, float)) and (int(bytesValue) > 0):
            factor = 1024
            for unit in ["", "K", "M", "G", "T", "P"]:
                if bytesValue < factor:
                    return f"{bytesValue:.2f}{unit}{suffix}"
                bytesValue /= factor
            return bytesValue
        return int(0)

    @staticmethod
    def getUIDValue(stringInput=''):
        prefix = 'uid-'
        if not stringInput.startswith(prefix):
            partitionedString = stringInput
        else:
            partitionedString = stringInput[len(prefix):len(stringInput)]
        return int(partitionedString)


def testSuite(debug: bool = False):
    """
    Function Type: Method
    Run all test for the class.
    """
    print(debug)
    # testObj = RegressionUnitTestsCases(debug=debug)
    # testObj.run()
    return True


def API(options=None):
    """ API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    testSuite(debug=options.debug)
    return


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    API(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
