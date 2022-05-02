#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package guiOneShot
import re, os, pprint, sys, datetime, traceback, configparser, pandas
import PySimpleGUI

import src.software.TSV.DefragHistoryGrapher as DHG
import src.software.TSV.visualizeTS as VTS
import src.software.TSV.generateTSBinaries
import src.software.TSV.formatTSFiles
import src.software.axon.packageInterface
import src.software.axon.axonInterface
import src.software.axon.axonMeta
import src.software.axon.axonProfile
import src.software.access.DriveInfo
import src.software.MEP.mediaErrorPredictor as MEP
import src.software.autoAI.mediaPredictionRNN as RNN
import src.software.container.basicTypes
import src.software.dAMP.gatherMeta
import src.software.guiLayouts
import src.software.guiCommon
import src.software.guiDeveloper

from src.software.utilsCommon import tryFile, tryFolder


class GUIOneShot():
    """
    Function to define API to run all webAPI sections in one window
    """
    dataFileName = None
    timeStamp = None
    dataFile = None
    zipName = None
    zipFile = None
    contentFile = None
    debug = False
    collectTelemetry = None
    logoLocation = None
    configLocation = None
    baseFilePath = None
    inputLocation = None
    outputLocation = None
    reportDictionary = None
    reportFlatDictionary = None
    displayReport = None
    fwParsersLocation = None

    def __init__(self, debug=False):
        self.dataFileName = None
        self.timeStamp = None
        self.dataFile = None
        self.zipName = None
        self.zipFile = None
        self.contentFile = None
        self.debug = False
        self.logoLocation = None
        self.configLocation = None
        self.baseFilePath = None
        self.outputLocation = None
        self.inputLocation = None
        self.fwParsersLocation = None
        self.dataCntrlLocation = None
        self.dataCntrlStructPath = None
        self.reportDictionary = None
        self.reportFlatDictionary = None
        self.displayReport = None
        self.config = None
        self.telemFile = None
        self.uploadID = None
        self.axonProfiler = None
        self.axonIDs = None
        self.axonConfig = None
        self.axonDownloadOutput = None
        self.vizDict = None

        self.FullTaskList = [
            "data.collect.execute",
            "data.table.execute",
            "axon.upload.execute",
            "axon.download.execute",
            "data.graph.execute",
            "defrag.graph.execute",
            "arma.predict.execute",
            "rnn.predict.execute",
            "user.report.execute"
        ]

        self.StateMachineStages = [  # tuple of state machine functions to run and
            ("data.collect.execute", self.DataCollect, self.DataCollectConfig),
            ("data.table.execute", self.DataTable, self.DataTableConfig),
            ("axon.upload.execute", self.AxonUpload, self.AxonUploadConfig),
            ("axon.download.execute", self.AxonDownload, self.AxonDownloadConfig),
            ("data.graph.execute", src.software.guiCommon.GenericObjectDecode, self.GenericObjectDecodeConfig),  # @todo
            ("defrag.graph.execute", self.DefragObjectDecode, self.DefragObjectDecodeConfig),
            ("arma.predict.execute", self.ARMAModelPredict, self.ARMAModelPredictConfig),
            ("rnn.predict.execute", self.RNNModelPredict, self.RNNModelPredictConfig),
            ("user.report.execute", self.GetContentReport, self.DataCollectConfig),
        ]

        self.SetPaths()
        self.GetReport()
        self.GetConfig()
        self.debug = debug
        self.collectTelemetry = src.software.guiCommon.collectGUI()

        # set input/output/fwparser location defaults
        for dictElem in self.collectTelemetry.getDictSet():
            if dictElem.getKey() == 'data.collect.workingDirInput':
                dictElem.getDefault(self.inputLocation)
                dictElem.setPossible(self.inputLocation)
            elif dictElem.getKey() == 'data.collect.workingDirOutput':
                dictElem.setDefault(self.outputLocation)
                dictElem.setPossible([self.outputLocation])
            elif dictElem.getKey() == 'data.collect.fwParsers':
                dictElem.setDefault(self.fwParsersLocation)
                dictElem._possible = [f.path for f in os.scandir(tryFolder("Auto-Parse/decode", walkUpLimit=3)) if
                                      f.is_dir()]

    def SetPaths(self):
        """
        Set path variables that are used by the OneShotAPI
        Returns:
            None
        """
        # Set location of logo for the layout
        self.logoLocation = ('{0}/src/software/{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))
        if os.path.isfile(self.logoLocation) is False:
            self.logoLocation = ('{0}/software/{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))
        self.baseFilePath = os.path.dirname(os.path.abspath(__file__))

        self.outputLocation = tryFolder(path='data/output', walkUpLimit=3)
        self.inputLocation = tryFolder(path='data/input', walkUpLimit=3)
        self.fwParsersLocation = tryFolder(path='Auto-Parse/decode/ADP_UV', walkUpLimit=3)
        self.dataCntrlLocation = tryFolder(path='Auto-Parse/datacontrol', walkUpLimit=3)
        self.dataCntrlStructPath = tryFile(self.dataCntrlLocation, 'structures.csv', walkUpLimit=3)

    def GetReport(self):
        self.reportDictionary = src.software.dAMP.gatherMeta.GatherMeta(binaryPath='binaries',
                                                                        fwDir='ADP',
                                                                        dataCntrlStructPath=self.dataCntrlStructPath,
                                                                        configFileName='time-series.ini',
                                                                        resultsFolder='results',
                                                                        debug=self.debug)
        self.reportFlatDictionary = self.reportDictionary.getSuperDictionary()
        self.displayReport = pprint.pformat(self.reportFlatDictionary, indent=3, width=100)

    def GetConfig(self):
        """
        Look for the location of the config file and config the configparser memeber variable
        Returns:
            None
        """
        self.config = configparser.ConfigParser()

        # Look for OneShotProfile.ini
        self.configLocation = os.path.abspath(os.path.join(os.getcwd(), '.raadProfile/OneShotProfile.ini'))
        if os.path.exists(self.configLocation) is False:
            self.configLocation = os.path.abspath(os.path.join(os.getcwd(), '../.raadProfile/OneShotProfile.ini'))
        if os.path.exists(self.configLocation) is False:
            self.configLocation = os.path.abspath(os.path.join(os.getcwd(), '../../.raadProfile/OneShotProfile.ini'))

        # Read config or return None if can't open
        if os.path.exists(self.configLocation):
            self.config.read(self.configLocation)

    def GetDataFile(self, section, tag):
        if hasattr(self, "telemFile") and self.telemFile is not None and os.path.exists(self.telemFile):
            return self.telemFile
        else:
            if self.config.has_option(section, tag) and os.path.exists(self.config[section][tag]):
                return self.config[section][tag]
            else:
                print("Error: no valid file found for ", tag)
                return None

    def OneShotLayout(self):
        """
        Layout for OneShotAPI
        Returns:
            PysimpleGUI layout
        """

        defaultCheck = not self.debug

        return [
            [PySimpleGUI.Text('Rapid Automation-Analysis for Developers (RAAD)',
                              tooltip='RAAD Skynet AI systems',
                              key='_RADWeb_', size=(111, 1))],
            [PySimpleGUI.Image(filename=self.logoLocation, size=(256, 300), key='__IMAGE__', )],
            [PySimpleGUI.Text('Hello Engineer, Below is general information.')],
            [PySimpleGUI.T('System platform: {0}'.format(sys.platform))],
            [PySimpleGUI.T('Location:'),
             PySimpleGUI.T(self.baseFilePath, size=(len(self.baseFilePath), 1))],
            [PySimpleGUI.T('Python Version:'),
             PySimpleGUI.T(sys.version, size=(len(sys.version), 1))],
            [PySimpleGUI.Text('UTC Time: {0}'.format(datetime.datetime.utcnow()))],
            ##################################
            # OneShot.Run.Checklist
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text("-- Checklist of operations to execute --", size=(50, 1))],
            [PySimpleGUI.Checkbox("Data Collect", key="data.collect.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="data.collect.configure")],

            [PySimpleGUI.Checkbox("Data Table", key="data.table.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="data.table.configure")],

            [PySimpleGUI.Checkbox("Fault Analysis Handbook Webpage", key="debug.handbook.execute",
                                  default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="debug.handbook.configure")],

            [PySimpleGUI.Checkbox("Telemetry Generic Object time series graph", key="data.graph.execute",
                                  default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="data.graph.configure")],

            [PySimpleGUI.Checkbox("Telemetry Defrag History", key="defrag.graph.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="defrag.graph.configure")],

            [PySimpleGUI.Checkbox("ARMA Prediction Plot", key="arma.predict.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="arma.predict.configure")],

            [PySimpleGUI.Checkbox("RNN Prediction Plot", key="rnn.predict.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="rnn.predict.configure")],

            [PySimpleGUI.Checkbox("User Report", key="user.report.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="user.report.configure")],

            [PySimpleGUI.Checkbox("AXON Database Upload", key="axon.upload.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="axon.upload.configure")],

            [PySimpleGUI.Checkbox("AXON Database Download", key="axon.download.execute", default=defaultCheck),
             PySimpleGUI.Button(button_text="Configure", key="axon.download.configure")],

            # [PySimpleGUI.Checkbox("User profile information", key="Info.user.execute", default=defaultCheck),
            #  PySimpleGUI.Button(button_text="Configure", key="Info.user.configure")],
            #
            # [PySimpleGUI.Checkbox("Application information for RAAD", key="Info.app.execute", default=defaultCheck),
            #  PySimpleGUI.Button(button_text="Configure", key="Info.app.configure")],

            [PySimpleGUI.Button(button_text="Execute Tasks", key="oneshot.execute")],
            [PySimpleGUI.Multiline(
                default_text="Report...",
                autoscroll=True,
                size=(100, 8),
                text_color='green',
                key="data.oneshot.report",
                do_not_clear=True,
                visible=True)],
            [PySimpleGUI.Button("EXIT")]
        ]

    @staticmethod
    def FindExistingTelemetryINI():
        """
        Asssumes that a time-series_<date>.ini file exists in data/output, or data/
        Returns:
            any occurrence of a telemetry config file
        """

        year = datetime.datetime.utcnow().strftime("%Y")
        defaultPath = tryFolder(path='data/output', walkUpLimit=3)
        regex = re.compile('time-series_' + year + '*')
        defaultFile = ''
        for root, dirs, files in os.walk(defaultPath):
            for file in files:
                if regex.match(file):
                    print('Setting default file: {0}'.format(file))
                    defaultFile = tryFile(path=defaultPath, fileName=file, walkUpLimit=3)
                    return defaultFile
            break
        defaultPath = tryFolder(path='data/', walkUpLimit=3)
        for root, dirs, files in os.walk(defaultPath):
            for file in files:
                if regex.match(file):
                    print('Setting default file: {0}'.format(file))
                    defaultFile = tryFile(path=defaultPath, fileName=file, walkUpLimit=3)
                    return defaultFile
            break
        return defaultFile

    def writeOneShotProfile(self, section, fieldName, value):
        self.config.set(section, fieldName, value)
        with open(self.configLocation, 'w') as configFile:
            self.config.write(configFile)

    @staticmethod
    def DisplayDebugWindow(operation, dbugMsg):
        continueRun = True
        proceed = True
        ProgramLabel = operation + ' Debug Window'
        debugLayout = src.software.guiLayouts.GUILayouts().debugComments(returnLayout=True, displayInput=dbugMsg)
        debugLayout.append([PySimpleGUI.Button("Okay", key="debug.okay")])
        debugLayout.append([PySimpleGUI.Button("Cancel", key="debug.cancel")])
        windowActive = PySimpleGUI.Window(title=ProgramLabel,
                                          resizable=True,
                                          auto_size_text=True,
                                          auto_size_buttons=True,
                                          grab_anywhere=True,
                                          finalize=True).Layout([[PySimpleGUI.Column(debugLayout,
                                                                                     scrollable=True,
                                                                                     pad=((11, 11), (11, 11)))]]
                                                                )
        while continueRun:
            (collect_button, collect_values) = (windowActive).read()
            if collect_button == "debug.okay":
                continueRun = False
            elif collect_button == 'debug.cancel':
                continueRun = False
                proceed = False
            elif collect_button == PySimpleGUI.WIN_CLOSED:
                continueRun = False
        windowActive.close()
        return proceed

    def DataCollectConfig(self):
        """
        Spoawns window to change configurations for Data Table method
        Returns:

        """
        layout = src.software.guiLayouts.GUILayouts().collect(returnLayout=True, debug=self.debug)
        layout.append([PySimpleGUI.Button("Submit", key="data.collect.submit")])

        programLabel = "RAAD OneShot Data Collect Config"

        DataCollectConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        Closed = False

        try:
            # Configure choices in the gui
            DataCollectConfigWindow['toolChoice'].update(self.config['data.collect']['data.collect.toolchoice'])
            DataCollectConfigWindow['ssdChoice'].update(self.config['data.collect']['data.collect.ssdchoice'])
            DataCollectConfigWindow['workingDirInput'].update(
                self.config['data.collect']['data.collect.workingdirinput'])
            DataCollectConfigWindow['fwParsers'].update(self.config['data.collect']['data.collect.fwparsers'])
            DataCollectConfigWindow['workingDirOutput'].update(
                self.config['data.collect']['data.collect.workingdiroutput'])
            DataCollectConfigWindow['numberOfQueries'].update(
                self.config['data.collect']['data.collect.numberofqueries'])
            DataCollectConfigWindow['timeFrame'].update(self.config['data.collect']['data.collect.timeframe'])

        except KeyError:
            print("ERROR: config lacking configurations for Data Collect")

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = DataCollectConfigWindow.read()

            if collect_button == "data.collect.submit":
                try:
                    self.config['data.collect']['data.collect.toolchoice'] = collectvalues['toolChoice']
                    self.config['data.collect']['data.collect.ssdchoice'] = collectvalues['ssdChoice']
                    self.config['data.collect']['data.collect.workingdirinput'] = collectvalues['workingDirInput']
                    self.config['data.collect']['data.collect.fwparsers'] = collectvalues['fwParsers']
                    self.config['data.collect']['data.collect.workingdiroutput'] = collectvalues['workingDirOutput']
                    self.config['data.collect']['data.collect.numberofqueries'] = collectvalues['numberOfQueries']
                    self.config['data.collect']['data.collect.timeframe'] = collectvalues['timeFrame']
                except KeyError:
                    if not self.config.has_section('data.collect'):
                        self.config.add_section('data.collect')
                    if not self.config.has_option('data.collect', 'data.collect.toolchoice'):
                        self.config.set('data.collect', 'data.collect.toolchoice', collectvalues['toolChoice'])
                    if not self.config.has_option('data.collect', 'data.collect.ssdchoice'):
                        self.config.set('data.collect', 'data.collect.ssdchoice', collectvalues['ssdChoice'])
                    if not self.config.has_option('data.collect', 'data.collect.workingdirinput'):
                        self.config.set('data.collect', 'data.collect.workingdirinput',
                                        collectvalues['workingDirInput'])
                    if not self.config.has_option('data.collect', 'data.collect.fwparsers'):
                        self.config.set('data.collect', 'data.collect.fwparsers', collectvalues['fwParsers'])
                    if not self.config.has_option('data.collect', 'data.collect.workingdiroutput'):
                        self.config.set('data.collect', 'data.collect.workingdiroutput',
                                        collectvalues['workingDirOutput'])
                    if not self.config.has_option('data.collect', 'data.collect.numberofqueries'):
                        self.config.set('data.collect', 'data.collect.numberofqueries',
                                        collectvalues['numberOfQueries'])
                    if not self.config.has_option('data.collect', 'data.collect.timeframe'):
                        self.config.set('data.collect', 'data.collect.timeframe', collectvalues['timeFrame'])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                for dictElem in self.collectTelemetry.getDictSet():
                    if dictElem.getKey() == 'data.collect.workingDirInput':
                        if collectvalues['workingDirInput'] not in dictElem.getPossible():
                            dictElem.getPossible().append(collectvalues['workingDirInput'])
                    elif dictElem.getKey() == 'data.collect.workingDirOutput':
                        if collectvalues['workingDirOutput'] not in dictElem.getPossible():
                            dictElem.getPossible().append(collectvalues['workingDirOutput'])
                    elif dictElem.getKey() == 'data.collect.fwParsers':
                        if collectvalues['fwParsers'] not in dictElem.getPossible():
                            dictElem.getPossible().append(collectvalues['fwParsers'])

                repeatEventLoop = False

            if collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

        DataCollectConfigWindow.close()

        return Closed

    def validateDataCollectConfig(self, dictElem, case):
        dbugMsg = ''
        if case == 'workingdirinput' or case == 'fwparsers' or case == 'workingdiroutput':
            try:
                path = self.config['data.collect']['data.collect.' + case]
                if path == '' or os.path.exists(path) is False:
                    dbugMsg += case + ': ' + path + ' does not exist\n'
                    path = dictElem.getDefault()
                if path not in dictElem.getPossible():
                    dbugMsg += case + ': ' + path + ' not a valid choice for ' + case + '\n'
                    path = dictElem.getDefault()
            except KeyError:
                dbugMsg += 'Invalid entry in field data.collect.' + case + '\n'
                path = dictElem.getDefault()
            dictElem._value = path
            self.config.set('data.collect', 'data.collect.' + case, dictElem._value)
        else:
            try:
                option = self.config['data.collect']['data.collect.' + case]
                if case == 'toolchoice':
                    if option not in dictElem.getPossible():
                        dbugMsg += case + ' does not exist\n'
                        option = dictElem.getDefault()
                else:
                    try:
                        if case == 'ssdchoice':
                            if option not in dictElem.getPossible():
                                dbugMsg += case + ' does not exist\n'
                                option = dictElem.getDefault()
                        elif int(option) < dictElem.getPossible()[0] or int(option) > dictElem.getPossible()[1]:
                            dbugMsg += case + ' does not exist\n'
                            option = dictElem.getDefault()
                    except:
                        option = dictElem.getDefault()
                        dbugMsg += case + ' does not exist\n'
                self.config.set('data.collect', 'data.collect.' + case, option)
                dictElem._value = option
            except KeyError:
                dbugMsg += 'Invalid entry in field data.collect.' + case + '\n'
                dictElem._value = dictElem.getDefault()
                self.config.set('data.collect', 'data.collect.' + case, dictElem._value)
        return dbugMsg

    def DataCollect(self):
        specificElems = {}
        debugMessages = ''
        for dictElem in self.collectTelemetry.getDictSet():
            selectKey = dictElem.getKey()
            if selectKey == 'data.collect.toolChoice':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='toolchoice')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.ssdChoice':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='ssdchoice')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.workingDirInput':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='workingdirinput')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.fwParsers':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='fwparsers')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.workingDirOutput':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='workingdiroutput')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.numberOfQueries':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='numberofqueries')
                specificElems[selectKey] = dictElem.getValue()
            elif selectKey == 'data.collect.timeFrame':
                debugMessages += self.validateDataCollectConfig(dictElem=dictElem, case='timeframe')
                specificElems[selectKey] = dictElem.getValue()

        with open(self.configLocation, 'w') as configFile:
            self.config.write(configFile)

        if debugMessages != '':
            debugMessages += 'Select Okay to use defaults, or Cancel to reconfigure\n'
            proceed = self.DisplayDebugWindow(operation='Data Collect', dbugMsg=debugMessages)
            if not proceed:
                return
        telemFile, valid = self.gatherTelemetryData(collect_values=specificElems)
        if not valid:
            dbugMsg = 'Error with {0}, Please select Cancel to reconfigure\n'.format(telemFile)
            with open('time_series_errorlog.txt', 'r') as infile:
                dataarray = infile.readlines()
            for item in dataarray:
                dbugMsg += item
            proceed = self.DisplayDebugWindow(operation='Time Series', dbugMsg=dbugMsg)
            if not proceed:
                return

        # set the rest of the oneshot operations to the latest output file created from data collect
        OneShotOperations = ['data.telemetry.table', 'Data.object.decode', 'Data.defrag.decode']
        operationFields = ['data.telemetry.table.file', '-FILE-', '-FILE-']
        for i in range(len(OneShotOperations)):
            self.config.set(OneShotOperations[i], operationFields[i], self.dataFile)
        with open(self.configLocation, 'w') as configFile:
            self.config.write(configFile)

    def gatherTelemetryData(self, collect_values):
        """
        Near Replication of GUI.gatherTelemetryData() above. This executes the same series of tasks:
            1. Query and aggregate telemetry from the chosen SSD
            2. Format data into .ini and .txt files
            3. Package remaining data files into a compressed format and clean up the directory
        Args: collect_values (dict) containing specific configurations for gathering telemetry data

        Returns:
            dataFileName: datafile
            valid: boolean which equals true if telemetry is valid
        """
        # Gather import for gathering binaries
        GTSB = src.software.TSV.generateTSBinaries
        FTSF = src.software.TSV.formatTSFiles
        # PI = software.axon.packageInterface
        print("successfully imported")

        defaultFolderInput = tryFolder(path='data', walkUpLimit=3)
        defaultParserInput = tryFolder(path='Auto-Parse/decode/ADP_UV', walkUpLimit=3)

        # Translation for mode field
        modeTranslate = {"CLI": 1, "TWIDL": 2, "PARSE": 3, "IMAS": 4}

        # Get common timestamp on files
        self.timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

        # Define most recent data file name
        self.dataFileName = "time-series_" + self.timeStamp + ".ini"
        dataFilePath = defaultFolderInput

        # Argument Dictionaries to translate bad inputs
        Classargs = dict(iterations=1, outpath=defaultFolderInput)
        APIargs = dict(mode='PARSE', time=2, driveNumber='1', inputFolder=defaultParserInput)
        Formatargs = dict(fwDir=defaultFolderInput, binDir=defaultFolderInput, outfile=self.dataFileName, obj=None,
                          mode=2)

        # Gather parameters for the gathering API
        try:
            # Get which flavor of telemetry the user wants to gather
            if collect_values['data.collect.toolChoice'] != '':
                APIargs["mode"] = modeTranslate[collect_values['data.collect.toolChoice']]

            # Find which nvme device will be queried
            if collect_values['data.collect.ssdChoice'] != '':
                APIargs["driveNumber"] = collect_values['data.collect.ssdChoice']
                APIargs["driveName"] = collect_values['data.collect.ssdChoice']

            # Gather directory for input data
            if collect_values['data.collect.workingDirInput'] != '':
                APIargs["inputFolder"] = collect_values['data.collect.workingDirInput']

            # Gather directory to find directory for firmware parsers
            if collect_values['data.collect.fwParsers'] != '':
                Formatargs["fwDir"] = collect_values['data.collect.fwParsers']

            # Gather directory to output files used
            if collect_values['data.collect.workingDirOutput'] != '':
                Classargs["outpath"] = collect_values['data.collect.workingDirOutput']
                Formatargs["binDir"] = collect_values['data.collect.workingDirOutput']

            # Maximum number of queries to send to the device
            if collect_values['data.collect.numberOfQueries'] != '':
                Classargs["iterations"] = int(collect_values['data.collect.numberOfQueries'])

            # Maximum amount of time, in seconds, to query the device
            if collect_values['data.collect.timeFrame'] != '':
                APIargs["time"] = int(collect_values['data.collect.timeFrame'])

            if self.debug:
                print("toolChoice: ", APIargs["mode"])
                print("ssdChoice: ", APIargs["driveNumber"])
                print("workingDirInput: ", APIargs["inputFolder"])
                print("workingDirOutput: ", Classargs["outpath"])
                print("numberOfQueries: ", Classargs["iterations"])
                print("timeFrame: ", APIargs["time"])
                print("parserDir: ", Formatargs["fwDir"])

        except KeyError:
            print("**Invalid entry in field... using defaults**")

        # Execute the generation
        print("---- Starting Collection of Data ----")
        print("API arguments: ", APIargs)
        gen = GTSB.generateTSBinaries(
            **{key: inputVector for key, inputVector in Classargs.items() if (inputVector is not None)})
        parseList, binList = gen.generateTSBinariesAPI(
            **{key: inputVector for key, inputVector in APIargs.items() if (inputVector is not None)})

        # Add list of binaries returned from generate to format
        Formatargs["binList"] = binList

        # Format files into .txt and .ini formats
        form = FTSF.formatTSFiles(outpath=Classargs["outpath"])
        valid = form.formatTSFilesAPI(
            **{key: inputVector for key, inputVector in Formatargs.items() if (inputVector is not None)})

        # Grab path to data file now that file should exist
        try:
            dataFilePath = Classargs["outpath"]
        except KeyError:
            print("Error in getting path for data file")

        if os.path.exists(os.path.join(dataFilePath, self.dataFileName)):
            self.dataFile = os.path.join(dataFilePath, self.dataFileName)

        # Compress created files
        self.zipName = "GatherData_" + self.timeStamp + ".zip"
        self.zipFile = src.software.axon.packageInterface.packageInterface(absPath=dataFilePath,
                                                                           debug=self.debug).createZIP(
            zipFileName=self.zipName)

        # Store name of fully compressed directory
        self.contentFile = self.zipName

        # if self.debug: print

        return self.dataFile, valid

    def DataTable(self):
        """
        Splits data from .ini files into csv files
        Returns:
            None
        """

        dataFile = self.GetDataFile('data.telemetry.table', 'data.telemetry.table.file')
        if dataFile is None:
            print("Error: No viable datafile found for DataTable")
            return

        # Get Data File
        dataDictObj = (src.software.guiLayouts.dataTablePopulate().getDataAsArray(dataFile))
        chosenKeyObj = self.config['data.telemetry.table']['data.telemetry.table.choice']
        dataTable = src.software.guiDeveloper.GUIDeveloper().getDataAsArray(DataDic=dataDictObj, chosenKey=chosenKeyObj,
                                                                            oneShot=True)

        # For each entry name in
        for dataEntry in dataTable:
            splitFrame = pandas.DataFrame(data=dataTable[dataEntry])

            splitCSVName = "{0}_{1}_{2}.csv".format("DataTable",
                                                    dataEntry,
                                                    datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f"))

            splitLocation = os.path.join(self.outputLocation, splitCSVName)

            splitFrame.to_csv(splitLocation)

        return

    def DataTableConfig(self):
        """
        Spoawns window to change configurations for Data Table method
        Returns:

        """

        # @todo main
        layout = src.software.guiLayouts.dataTablePopulate(returnLayout=True).main()
        layout.append([PySimpleGUI.Button("Submit", key="data.telemetry.table.submit")])

        programLabel = "RAAD OneShot Data Table Config"

        DataTableConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        try:
            # Configure choices in the gui
            DataTableConfigWindow['data.telemetry.table.file'].update(
                self.config['data.telemetry.table']['data.telemetry.table.file'])
            DataTableConfigWindow['data.telemetry.table.choice'].update(
                self.config['data.telemetry.table']['data.telemetry.table.choice'])

            if os.path.exists(self.config['data.telemetry.table']['data.telemetry.table.file']):
                src.software.guiCommon.GenericObjectGraph().populate_object(windowVar=DataTableConfigWindow, dirPathVar=
                self.config['data.telemetry.table']['data.telemetry.table.file'])
        except KeyError:
            print("ERROR: config lacking configurations for Data Table")

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = DataTableConfigWindow.read()

            if collect_button == "data.telemetry.table.submit":
                try:
                    self.config['data.telemetry.table']['data.telemetry.table.file'] = collectvalues[
                        'data.telemetry.table.file']
                    self.config['data.telemetry.table']['data.telemetry.table.choice'] = collectvalues[
                        'data.telemetry.table.choice']
                except KeyError:
                    if not self.config.has_section('data.telemetry.table'):
                        self.config.add_section('data.telemetry.table')
                    if not self.config.has_option('data.telemetry.table', 'data.telemetry.table.file'):
                        self.config.set('data.telemetry.table', 'data.telemetry.table.file',
                                        collectvalues['data.telemetry.table.file'])
                    if not self.config.has_option('data.telemetry.table', 'data.telemetry.table.choice'):
                        self.config.set('data.telemetry.table', 'data.telemetry.table.choice',
                                        collectvalues['data.telemetry.table.choice'])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            elif collect_button == "data.telemetry.table.file":
                try:
                    if os.path.exists(self.config['data.telemetry.table']['data.telemetry.table.file']):
                        src.software.guiCommon.GenericObjectGraph().populate_object(windowVar=DataTableConfigWindow,
                                                                                    dirPathVar=
                                                                                    self.config['data.telemetry.table'][
                                                                                        'data.telemetry.table.file'])
                except KeyError as errorMsg:
                    print("Failed to populate object in Data Table Config")
                    print("Error: ", errorMsg)
        DataTableConfigWindow.close()

        return

    def AxonUpload(self):
        """
        Upload content file to AXON database
        Returns:
            None
        """

        dataFile = self.GetDataFile("Axon.upload", "upload.content.location")
        if dataFile is None:
            print("Error: No viable datafile found for AXON Upload")
            return

        # kickoff upload
        uploadSuccess, uploadID = src.software.guiLayouts.GUILayouts().GUI.GUIUpload(dataFile,
                                                                                     mode=self.config["Axon.upload"][
                                                                                         "upload.content.mode"],
                                                                                     analysisReport=self.reportDictionary)

        if uploadSuccess:
            self.uploadID = uploadID
        axonProfiler = src.software.axon.axonProfile.AxonProfile()
        (self.axonIDs, self.axonConfig) = axonProfiler.GetProfile()

        return

    def AxonUploadConfig(self):
        layout = src.software.guiExamples.GUI_Examples().upload(returnLayout=True)
        layout.append([PySimpleGUI.Button("Submit", key="Axon.upload.submit")])

        programLabel = "RAAD OneShot AXON Upload Config"

        AxonConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        try:
            # Configure choices in the gui
            AxonConfigWindow["upload.content.location"].update(
                self.config["Axon.upload"]["upload.content.location"])
            AxonConfigWindow["upload.content.mode"].update(self.config["Axon.upload"]["upload.content.mode"])
        except KeyError:
            print("ERROR: config lacking configurations for Axon Upload")

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = AxonConfigWindow.read()

            if collect_button == "Axon.upload.submit":
                try:
                    self.config["Axon.upload"]["upload.content.location"] = collectvalues[
                        "upload.content.location"]
                    self.config["Axon.upload"]["upload.content.mode"] = collectvalues[
                        "upload.content.mode"]
                except KeyError:
                    if not self.config.has_section("Axon.upload"):
                        self.config.add_section("Axon.upload")
                    if not self.config.has_option("Axon.upload", "upload.content.location"):
                        self.config.set("Axon.upload", "upload.content.location",
                                        collectvalues["upload.content.location"])
                    if not self.config.has_option("Axon.upload", "upload.content.mode"):
                        self.config.set("Axon.upload", "upload.content.mode",
                                        collectvalues["upload.content.mode"])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            if collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False

        AxonConfigWindow.close()

        return

    def AxonDownload(self):
        """
        Downloads content from axon with the configured ID
        Returns:
            None
        """

        dataFile = self.GetDataFile("Axon.download", "download.location.directory")
        if dataFile is None:
            print("Error: No viable datafile found for AXON Download")
            return

        self.axonDownloadOutput = src.software.guiLayouts.GUILayouts().GUIDownload(
            self.config["Axon.download"]["-download.choice.ID-"],
            dataFile,
            mode=self.config["Axon.download"]["download.content.mode"],
            analysisReport=self.reportDictionary)
        return

    def AxonDownloadConfig(self):
        """
        Configures fields and config file for downloading from the AXON database
        Returns:
            None
        """
        layout = src.software.guiExamples.GUI_Examples().download(returnLayout=True)  # @todo
        layout.append([PySimpleGUI.Button("Submit", key="Axon.download.submit")])

        programLabel = "RAAD OneShot AXON Upload Config"

        AxonConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        try:
            # Configure choices in the gui
            AxonConfigWindow["download.location.directory"].update(
                self.config["Axon.download"]["download.location.directory"])
            AxonConfigWindow["-download.choice.ID-"].update(
                self.config["Axon.download"]["-download.choice.ID-"])
            AxonConfigWindow["download.content.mode"].update(
                self.config["Axon.download"]["download.content.mode"])
        except KeyError:
            print("ERROR: config lacking configurations for Axon Download")

        repeatEventLoop = True
        Closed = False
        while repeatEventLoop:
            collect_button, collectvalues = AxonConfigWindow.read()

            if collect_button == "Axon.download.submit":
                try:
                    self.config["Axon.download"]["download.location.directory"] = collectvalues[
                        "download.location.directory"]
                    self.config["Axon.download"]["-download.choice.ID-"] = collectvalues[
                        "-download.choice.ID-"]
                    self.config["Axon.download"]["download.content.mode"] = collectvalues[
                        "download.content.mode"]
                except KeyError:
                    if not self.config.has_section("Axon.download"):
                        self.config.add_section("Axon.download")
                    if not self.config.has_option("Axon.download", "download.location.directory"):
                        self.config.set("Axon.download", "download.location.directory",
                                        collectvalues["download.location.directory"])
                    if not self.config.has_option("Axon.download", "-download.choice.ID-"):
                        self.config.set("Axon.download", "-download.choice.ID-",
                                        collectvalues["-download.choice.ID-"])
                    if not self.config.has_option("Axon.download", "download.content.mode"):
                        self.config.set("Axon.download", "download.content.mode",
                                        collectvalues["download.content.mode"])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            if collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

        AxonConfigWindow.close()

        return Closed

    def GenericObjectDecodeConfig(self):
        """

        Returns:
            None
        """

        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-"]
        secondaryVarLabels = ["-SFVAR-", "-SSVAR-", "-STVAR-"]

        class ObjectConfig:
            objectFilePath = None
            objectIDs = []

            def __init__(self, configFilePath):
                self.objectFilePath = configFilePath
                self.objectIDDecode = None
                self.vizDict = None

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the ObjectConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    vts: visualizeTS instance
                """
                vts = VTS.visualizeTS(debug)
                self.vizDict = vts.generateDataDictFromConfig(self.objectFilePath)
                self.objectIDs = list(map(lambda x: x.strip("uid-"), self.vizDict.keys()))
                self.objectIDDecode = {self.vizDict[uid]["name"]: uid for uid in self.vizDict.keys()}

                return vts

            def GetObjectIDDecode(self):
                return self.objectIDDecode

        def populate_object(window, dirPathLocal):
            """
            function for populating the ObjectConfig instance and updating the drop down menu for the objects
            available in the configuration file

            Args:
                window: window instance
                dirPathLocal: String for the path to the configuration file

            Returns:
                vts: visualizeTS instance
                objectFile: ObjectConfig instance
                objectNamesDict: Dictionary of object identifiers (ex. uid-6) to object names (ex. ThermalSensor)
            """
            objectFileLocal = ObjectConfig(str(dirPathLocal))
            vtsLocal = objectFileLocal.readConfigContent()
            objectList = list(objectFileLocal.objectIDs)
            objectNamesDict = {}
            objectIDsDictLocal = {}
            for key in objectList:
                currentObjectLocal = "uid-" + key
                currentNameLocal = objectFileLocal.vizDict[currentObjectLocal]["name"]
                objectNamesDict[currentNameLocal] = key
                objectIDsDictLocal[currentObjectLocal] = currentNameLocal
            window["-OBJECT-"].Update(values=list(objectNamesDict.keys()))
            return vtsLocal, objectFileLocal, objectNamesDict, objectIDsDictLocal

        def display_dir(window, objectFileLocal, currentObjectLocal):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                window: window instance
                objectFileLocal: ObjectConfig instance
                currentObjectLocal: String for the name of the current object (ex. uid-6)

            Returns:

            """
            trackingVars = objectFileLocal.vizDict[currentObjectLocal].keys()
            primaryVars = ["None"] + list(trackingVars)
            secondaryVars = ["None"] + list(trackingVars)
            for name in primaryVarLabels:
                window[name].Update(values=primaryVars)
            for name in secondaryVarLabels:
                window[name].Update(values=secondaryVars)

        def is_data_selected_from_fields(listLocal):
            """
            function for checking if data has been selected for a list

            Args:
                listLocal: list of data values

            Returns:

            """
            return (len(listLocal) > 0)

        def create_new_graph_window(values, vts, objectFile, currentObject):
            """
            function for generating a new graph window using the matplot functionality of PySimpleGUI

            Args:
                values: List of values collected from window
                vts: visualizeTS instance
                objectFile: ObjectConfig instance
                currentObject: String for the name of the current object (ex. uid-6)

            Returns:

            """
            trackingVars = []
            secondaryVars = []
            print(self.debug)
            for name in primaryVarLabels:
                if values[name] != "None":
                    trackingVars.append(values[name])

            for name in secondaryVarLabels:
                if values[name] != "None":
                    secondaryVars.append(values[name])

            if is_data_selected_from_fields(trackingVars):
                currentObjects = [currentObject.strip("uid-")]
                print(str(currentObjects))
                dataDict = objectFile.vizDict
                start = values['-START-']
                end = values['-END-']
                matrixProfile = values['-MATRIX-']
                matrixProfileFlag = False
                if matrixProfile == "Yes":
                    matrixProfileFlag = True
                elif matrixProfile == "No":
                    matrixProfileFlag = False

                if matrixProfileFlag:
                    unionFields = trackingVars + secondaryVars
                    dataDict = vts.generateMP(dataDict, obj=currentObjects, fields=unionFields, subSeqLen=20,
                                              visualizeAllObj=False, visualizeAllFields=False)
                vts.generateTSVisualizationGUI(currentObject, dataDict[currentObject], trackingVars, secondaryVars,
                                               start, end)

        def mainLoop():
            layout = src.software.guiExamples.GUI_Examples().collect(returnLayout=True, debug=self.debug)
            layout.append([PySimpleGUI.Button("Submit", key="Data.object.decode.submit")])

            programLabel = "RAAD OneShot Generic Object Decode Config"

            GenericObjectConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)
            defaultFile = None

            try:

                if os.path.exists(self.config["Data.object.decode"]["-FILE-"]):
                    dirPath = self.config["Data.object.decode"]["-FILE-"]
                    vts, objectFile, objectDict, objectIDsDict = populate_object(GenericObjectConfigWindow, dirPath)
                else:  # set a default file if the current one in the configuration is not detected
                    defaultPath = tryFolder(path='data', walkUpLimit=3)
                    regex = re.compile('time-series_2020*')
                    for root, dirs, files in os.walk(defaultPath):
                        for file in files:
                            if regex.match(file):
                                print(file)
                                defaultFile = tryFile(path=defaultPath, fileName=file, walkUpLimit=3)
                                break
                        break

                    if defaultFile is not None:
                        self.config.set('Data.object.decode', '-FILE-', defaultFile)
                    dirPath = self.config["Data.object.decode"]["-FILE-"]
                    vts, objectFile, objectDict, objectIDsDict = populate_object(GenericObjectConfigWindow, dirPath)

                # Configure choices in the gui
                GenericObjectConfigWindow["-FILE-"].update(
                    self.config["Data.object.decode"]["-FILE-"])
                GenericObjectConfigWindow["-OBJECT-"].update(
                    objectIDsDict[self.config["Data.object.decode"]["-OBJECT-"]])
                GenericObjectConfigWindow["-START-"].update(
                    self.config["Data.object.decode"]["-START-"])
                GenericObjectConfigWindow["-END-"].update(
                    self.config["Data.object.decode"]["-END-"])
                GenericObjectConfigWindow["-MATRIX-"].update(
                    self.config["Data.object.decode"]["-MATRIX-"])

                GenericObjectConfigWindow["-PFVAR-"].update(
                    self.config["Data.object.decode"]["-PFVAR-"])
                GenericObjectConfigWindow["-PSVAR-"].update(
                    self.config["Data.object.decode"]["-PSVAR-"])
                GenericObjectConfigWindow["-PTVAR-"].update(
                    self.config["Data.object.decode"]["-PTVAR-"])

                GenericObjectConfigWindow["-SFVAR-"].update(
                    self.config["Data.object.decode"]["-SFVAR-"])
                GenericObjectConfigWindow["-SSVAR-"].update(
                    self.config["Data.object.decode"]["-SSVAR-"])
                GenericObjectConfigWindow["-STVAR-"].update(
                    self.config["Data.object.decode"]["-STVAR-"])
            except KeyError:
                print("ERROR: config lacking configurations for Generic Object Decode")

            vts = None
            objectFile = None
            currentObject = None
            objectDict = None

            repeatEventLoop = True
            Closed = False
            while repeatEventLoop:
                collect_button, collectvalues = GenericObjectConfigWindow.read()

                if collect_button == PySimpleGUI.WIN_CLOSED:
                    repeatEventLoop = False
                    Closed = True

                elif collect_button == "Data.object.decode.submit":
                    try:

                        if objectFile is None or vts is None:
                            dirPath = collectvalues['-FILE-']
                            objectFile = ObjectConfig(str(dirPath))
                            vts = objectFile.readConfigContent()

                        self.config["Data.object.decode"]["-FILE-"] = \
                            collectvalues["-FILE-"]
                        try:
                            self.config["Data.object.decode"]["-OBJECT-"] = \
                                objectFile.GetObjectIDDecode()[collectvalues["-OBJECT-"]]
                        except KeyError as errorMsg:
                            print("Error in Generic Object Config: Could not find key: ", collectvalues["-OBJECT-"])
                            print("Error output: ", errorMsg)
                        self.config["Data.object.decode"]["-START-"] = \
                            str(collectvalues["-START-"])
                        self.config["Data.object.decode"]["-END-"] = \
                            str(collectvalues["-END-"])
                        self.config["Data.object.decode"]["-MATRIX-"] = \
                            collectvalues["-MATRIX-"]

                        self.config["Data.object.decode"]["-PFVAR-"] = \
                            collectvalues["-PFVAR-"]
                        self.config["Data.object.decode"]["-PSVAR-"] = \
                            collectvalues["-PSVAR-"]
                        self.config["Data.object.decode"]["-PTVAR-"] = \
                            collectvalues["-PTVAR-"]

                        self.config["Data.object.decode"]["-SFVAR-"] = \
                            collectvalues["-SFVAR-"]
                        self.config["Data.object.decode"]["-SSVAR-"] = \
                            collectvalues["-SSVAR-"]
                        self.config["Data.object.decode"]["-STVAR-"] = \
                            collectvalues["-STVAR-"]

                    except KeyError:

                        if not self.config.has_section("Data.object.decode"):
                            self.config.add_section("Data.object.decode")

                        if not self.config.has_option("Data.object.decode", "-FILE-"):
                            self.config.set("Data.object.decode", "-FILE-",
                                            collectvalues["-FILE-"])
                        if not self.config.has_option("Data.object.decode", "-OBJECT-"):
                            self.config.set("Data.object.decode", "-OBJECT-",
                                            collectvalues["-OBJECT-"])
                        if not self.config.has_option("Data.object.decode", "-START-"):
                            self.config.set("Data.object.decode", "-START-",
                                            str(collectvalues["-START-"]))
                        if not self.config.has_option("Data.object.decode", "-END-"):
                            self.config.set("Data.object.decode", "-END-",
                                            str(collectvalues["-END-"]))
                        if not self.config.has_option("Data.object.decode", "-MATRIX-"):
                            self.config.set("Data.object.decode", "-MATRIX-",
                                            collectvalues["-MATRIX-"])

                        if not self.config.has_option("Data.object.decode", "-PFVAR-"):
                            self.config.set("Data.object.decode", "-PFVAR-",
                                            collectvalues["-PFVAR-"])
                        if not self.config.has_option("Data.object.decode", "-PSVAR-"):
                            self.config.set("Data.object.decode", "-PSVAR-",
                                            collectvalues["-PSVAR-"])
                        if not self.config.has_option("Data.object.decode", "-PTVAR-"):
                            self.config.set("Data.object.decode", "-PTVAR-",
                                            collectvalues["-PTVAR-"])

                        if not self.config.has_option("Data.object.decode", "-SFVAR-"):
                            self.config.set("Data.object.decode", "-SFVAR-",
                                            collectvalues["-SFVAR-"])
                        if not self.config.has_option("Data.object.decode", "-SSVAR-"):
                            self.config.set("Data.object.decode", "-SSVAR-",
                                            collectvalues["-SSVAR-"])
                        if not self.config.has_option("Data.object.decode", "-STVAR-"):
                            self.config.set("Data.object.decode", "-STVAR-",
                                            collectvalues["-STVAR-"])

                    with open(self.configLocation, 'w') as configFile:
                        self.config.write(configFile)

                    repeatEventLoop = False

                elif collect_button == "-FILE-":
                    dirPath = collectvalues['-FILE-']
                    vts, objectFile, objectDict, objectIDsDict = populate_object(GenericObjectConfigWindow, dirPath)

                elif collect_button == "Select":
                    try:
                        if objectDict is None:
                            dirPath = collectvalues['-FILE-']
                            vts, objectFile, objectDict, objectIDsDict = populate_object(GenericObjectConfigWindow,
                                                                                         dirPath)
                        currentName = collectvalues['-OBJECT-']
                        currentObjectNumber = objectDict[currentName]
                        currentObject = "uid-" + currentObjectNumber
                        display_dir(GenericObjectConfigWindow, objectFile, currentObject)
                    except KeyError as e:
                        print("Error in Generic Object Config: Cannot find key ")
                        print("Error traceback: ", e)

            GenericObjectConfigWindow.close()

            return Closed

    def DefragObjectDecode(self):
        """

        Returns:
            None
        """
        setPointLabelsDict = {"-START-": "start", "-NORMAL-": "normal", "-CORNER-": "corner", "-URGENT-": "urgent",
                              "-CRITICAL-": "critical"}
        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-"]
        secondaryVarLabels = ["-SFVAR-", "-SSVAR-", "-STVAR-"]

        class DefragConfig_Obsolute():
            dhFilePath = None
            setPoints = []
            trackingVars = []
            secondaryVars = []

            def __init__(self, configFilePath, modeDC):
                self.dhFilePath = configFilePath
                self.mode = modeDC
                self.vizDict = None

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the DefragConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    dhg: DefragHistoryGrapher instance
                """
                dhgLocal = DHG.DefragHistoryGrapher(mode=self.mode)
                self.vizDict = dhgLocal.generateDataDictFromConfig(self.dhFilePath)
                self.setPoints = dhgLocal.getSetPointNames()
                object_t = "uid-41"
                try:
                    subdict = self.vizDict[object_t]
                except Exception:
                    print("DefragHistory object not found in the configuration file")
                    return
                if debug is True:
                    print("DefragHistory object found...")
                if self.mode == 1:
                    litePattern = re.compile("LITE")
                    normalPattern = re.compile("NORMAL")
                    extendedPattern = re.compile("EXTENDED")
                    logType = subdict["header"]["prevlogtype"][0]

                    if litePattern.search(logType):
                        logName = "loglite[0]"
                    elif extendedPattern.search(logType):
                        logName = "logextended[0]"
                    elif normalPattern.search(logType):
                        logName = "lognormal[0]"
                    else:
                        raise Exception("Log type not found " + logType)
                    logDict = subdict["__anuniontypedef125__"][logName]
                    self.trackingVars = logDict.keys()
                    self.secondaryVars = logDict.keys()
                elif self.mode == 2:
                    logName = "log[0]"
                    logDict = subdict[logName]
                    self.trackingVars = logDict.keys()
                    self.secondaryVars = logDict.keys()

                return dhgLocal

        def prepare_defrag_history_file(dirPath, modeLocal):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                dirPath: String for the path to the configuration file
                modeLocal: Integer for the mode of operation (1=ADP, 2=CDR)

            Returns:
                dhg: DefragHistoryGrapher instance
                dhFile: DefragConfig instance

            """
            dhFileLocal = src.software.guiCommon.DefragConfig(str(dirPath), modeLocal)
            dhgLocal = dhFileLocal.readConfigContent()
            return dhgLocal, dhFileLocal

        def is_data_selected_from_fields(listVar):
            """
            function for checking if data has been selected for a list

            Args:
                listVar: list of data values

            Returns:

            """
            return (len(listVar) > 0)

        # def create_defrag_history_pdf(values, dhg, dhFile):
        #     """
        #     function for generating a new graph window using the matplot functionality of PySimpleGUI
        #
        #     Args:
        #         values: List of values collected from window
        #         dhg: DefragHistoryGrapher instance
        #         dhFile: DefragConfig instance
        #
        #     Returns:
        #
        #     """
        #     setPoints = []
        #     trackingVars = []
        #     secondaryVars = []
        #     for name in setPointLabelsDict.keys():
        #         if values[name] is True:
        #             setPoints.append(setPointLabelsDict[name])
        #
        #     for name in primaryVarLabels:
        #         if values[name] != "None":
        #             trackingVars.append(values[name])
        #
        #     for name in secondaryVarLabels:
        #         if values[name] != "None":
        #             secondaryVars.append(values[name])
        #
        #     if is_data_selected_from_fields(trackingVars):
        #
        #         dhg.setSetPointNames(setPoints)
        #         dhg.setTrackingNames(trackingVars)
        #         dhg.setSecondaryVars(secondaryVars)
        #         numCores = self.config["Data.defrag.decode"]['-CORES-']
        #         bandwidthFlag = self.config["Data.defrag.decode"]["-BANDWIDTH-"]
        #         start = float(self.config["Data.defrag.decode"]['-SSTART-'])
        #         end = float(self.config["Data.defrag.decode"]['-END-']
        #         dhg.writeTSVisualizationToPDF(dataDict,
        #                                       bandwidthFlag,
        #                                       os.path.join(self.outputLocation, "Defrag_History_Graph_" + timeStamp),
        #                                       numCores=numCores,
        #                                       start=start,
        #                                       end=end)

        dataFile = self.GetDataFile("Data.defrag.decode", "-FILE-")
        if dataFile is None:
            print("Error: No viable datafile found for Defrag History Grapher")
            return

        driveName = self.config["Data.defrag.decode"]["-DRIVE-"]
        if driveName == "ADP":
            mode = 1
        elif driveName == "CDR":
            mode = 2
        else:
            mode = 1

        dhg, dhFile = prepare_defrag_history_file(dataFile, mode)

        if dhg is None:
            print("Error: could not find defrag history object in the current data file!!! Stopping Execution...")
            return

        setPoints = []
        trackingVars = []
        secondaryVars = []
        for name in setPointLabelsDict.keys():
            if self.config["Data.defrag.decode"][name] is True:
                setPoints.append(setPointLabelsDict[name])

        for name in primaryVarLabels:
            if self.config["Data.defrag.decode"][name] != "":
                trackingVars.append(self.config["Data.defrag.decode"][name])

        for name in secondaryVarLabels:
            if self.config["Data.defrag.decode"][name] != "":
                secondaryVars.append(self.config["Data.defrag.decode"][name])

        # Get timestamp for start of collecting
        timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

        if is_data_selected_from_fields(trackingVars):
            dhg.setSetPointNames(setPoints)
            dhg.setTrackingNames(trackingVars)
            dhg.setSecondaryVars(secondaryVars)
            numCores = self.config["Data.defrag.decode"]['-CORES-']
            bandwidthFlag = self.config["Data.defrag.decode"]["-BANDWIDTH-"] == "Yes"
            start = float(self.config["Data.defrag.decode"]['-SSTART-'])
            end = float(self.config["Data.defrag.decode"]['-END-'])
            dhg.writeTSVisualizationToPDF(dhFile.vizDict,
                                          bandwidthFlag,
                                          os.path.join(self.outputLocation, "Defrag_History_Graph_" + timeStamp),
                                          numCores=int(numCores),
                                          start=start,
                                          end=end)

        return

    def DefragObjectDecodeConfig(self):
        """

        Returns:
            None
        """

        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-"]
        secondaryVarLabels = ["-SFVAR-", "-SSVAR-", "-STVAR-"]

        primaryVarLabelsDefragHistory = ["data.telemetry.defragHistory.pfvar",
                                         "data.telemetry.defragHistory.psvar",
                                         "data.telemetry.defragHistory.ptvar"]
        secondaryVarLabelsDefragHistory = ["data.telemetry.defragHistory.sfvar",
                                           "data.telemetry.defragHistory.ssvar",
                                           "data.telemetry.defragHistory.stvar"]

        class DefragConfig():
            dhFilePath = None
            setPoints = []
            trackingVars = []
            secondaryVars = []

            def __init__(self, configFilePath, mode):
                self.dhFilePath = configFilePath
                self.mode = mode

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the DefragConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    dhg: DefragHistoryGrapher instance
                """
                dhg = DHG.DefragHistoryGrapher(mode=self.mode)
                self.vizDict = dhg.generateDataDictFromConfig(self.dhFilePath)
                self.setPoints = dhg.getSetPointNames()
                object_t = "uid-41"
                try:
                    subdict = self.vizDict[object_t]
                except Exception:
                    print("DefragHistory object not found in the configuration file")
                    return
                if debug is True:
                    print("DefragHistory object found...")
                if self.mode == 1:
                    litePattern = re.compile("LITE")
                    normalPattern = re.compile("NORMAL")
                    extendedPattern = re.compile("EXTENDED")
                    logType = subdict["header"]["prevlogtype"][0]

                    if litePattern.search(logType):
                        logName = "loglite[0]"
                    elif extendedPattern.search(logType):
                        logName = "logextended[0]"
                    elif normalPattern.search(logType):
                        logName = "lognormal[0]"
                    else:
                        raise Exception("Log type not found " + logType)
                    logDict = subdict["__anuniontypedef125__"][logName]
                    self.trackingVars = logDict.keys()
                    self.secondaryVars = logDict.keys()
                elif self.mode == 2:
                    logName = "log[0]"
                    logDict = subdict[logName]
                    self.trackingVars = logDict.keys()
                    self.secondaryVars = logDict.keys()

                return dhg

        def display_dir(window, dirPath, mode):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                window: window instance
                dirPath: String for the path to the configuration file
                mode: Integer for the mode of operation (1=ADP, 2=CDR)

            Returns:
                dhg: DefragHistoryGrapher instance
                dhFile: DefragConfig instance

            """
            dhFile = DefragConfig(str(dirPath), mode)
            dhg = dhFile.readConfigContent()
            primaryVars = ["None"] + list(dhFile.trackingVars)
            secondaryVars = ["None"] + list(dhFile.secondaryVars)
            for name in primaryVarLabels:
                window[name].Update(values=primaryVars)
            for name in secondaryVarLabels:
                window[name].Update(values=secondaryVars)
            return dhg, dhFile

        layout = src.software.guiLayouts.GUILayouts().defragHistoryGraph(returnLayout=True)
        layout.append([PySimpleGUI.Button("Submit", key="Data.defrag.decode.submit")])

        programLabel = "RAAD OneShot Generic Defrag History Graph Config"

        defragObjectConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        try:
            # Configure choices in the gui
            defragObjectConfigWindow["-FILE-"].update(
                self.config["Data.defrag.decode"]["-FILE-"])
            defragObjectConfigWindow["-DRIVE-"].update(
                self.config["Data.defrag.decode"]["-DRIVE-"])
            defragObjectConfigWindow["-SSTART-"].update(
                self.config["Data.defrag.decode"]["-SSTART-"])
            defragObjectConfigWindow["-END-"].update(
                self.config["Data.defrag.decode"]["-END-"])
            defragObjectConfigWindow["-BANDWIDTH-"].update(
                self.config["Data.defrag.decode"]["-BANDWIDTH-"])
            defragObjectConfigWindow["-CORES-"].update(
                self.config["Data.defrag.decode"]["-CORES-"])

            defragObjectConfigWindow["-START-"].update(
                self.config["Data.defrag.decode"]["-START-"] == "True")
            defragObjectConfigWindow["-NORMAL-"].update(
                self.config["Data.defrag.decode"]["-NORMAL-"] == "True")
            defragObjectConfigWindow["-CORNER-"].update(
                self.config["Data.defrag.decode"]["-CORNER-"] == "True")
            defragObjectConfigWindow["-URGENT-"].update(
                self.config["Data.defrag.decode"]["-URGENT-"] == "True")
            defragObjectConfigWindow["-CRITICAL-"].update(
                self.config["Data.defrag.decode"]["-CRITICAL-"] == "True")

            defragObjectConfigWindow["-PFVAR-"].update(
                self.config["Data.defrag.decode"]["-PFVAR-"])
            defragObjectConfigWindow["-PSVAR-"].update(
                self.config["Data.defrag.decode"]["-PSVAR-"])
            defragObjectConfigWindow["-PTVAR-"].update(
                self.config["Data.defrag.decode"]["-PTVAR-"])

            defragObjectConfigWindow["-SFVAR-"].update(
                self.config["Data.defrag.decode"]["-SFVAR-"])
            defragObjectConfigWindow["-SSVAR-"].update(
                self.config["Data.defrag.decode"]["-SSVAR-"])
            defragObjectConfigWindow["-STVAR-"].update(
                self.config["Data.defrag.decode"]["-STVAR-"])
        except KeyError as e:
            print("ERROR: config lacking configurations for Defrag history Decode")
            print("Error: ", e)

        if self.config.has_section("Data.defrag.decode"):
            if self.config.has_option("Data.defrag.decode", "-FILE-") and \
                    self.config.has_option("Data.defrag.decode", "-DRIVE-"):
                if os.path.exists(self.config["Data.defrag.decode"]["-FILE-"]):
                    dirPath = self.config["Data.defrag.decode"]["-FILE-"]
                    driveName = self.config["Data.defrag.decode"]["-DRIVE-"]
                    mode = 0
                    if driveName == 'ADP':
                        mode = 1
                    elif driveName == 'CDR':
                        mode = 2
                    dhg, dhFile = display_dir(defragObjectConfigWindow, dirPath, mode)

        Closed = False

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = defragObjectConfigWindow.read()

            if collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

            elif collect_button == "Data.defrag.decode.submit":
                try:

                    if dhg == None:
                        dirPath = collectvalues['-FILE-']
                        driveName = collectvalues['-DRIVE-']
                        mode = 0
                        if driveName == 'ADP':
                            mode = 1
                        elif driveName == 'CDR':
                            mode = 2
                        dhg, dhFile = display_dir(defragObjectConfigWindow, dirPath, mode)

                    self.config["Data.defrag.decode"]["-FILE-"] = \
                        collectvalues["-FILE-"]
                    self.config["Data.defrag.decode"]["-DRIVE-"] = \
                        collectvalues["-DRIVE-"]
                    self.config["Data.defrag.decode"]["-SSTART-"] = \
                        str(collectvalues["-SSTART-"])
                    self.config["Data.defrag.decode"]["-END-"] = \
                        str(collectvalues["-END-"])
                    self.config["Data.defrag.decode"]["-BANDWIDTH-"] = \
                        collectvalues["-BANDWIDTH-"]
                    self.config["Data.defrag.decode"]["-CORES-"] = \
                        str(collectvalues["-CORES-"])

                    self.config["Data.defrag.decode"]["-START-"] = \
                        str(collectvalues["-START-"])
                    self.config["Data.defrag.decode"]["-NORMAL-"] = \
                        str(collectvalues["-NORMAL-"])
                    self.config["Data.defrag.decode"]["-CORNER-"] = \
                        str(collectvalues["-CORNER-"])
                    self.config["Data.defrag.decode"]["-URGENT-"] = \
                        str(collectvalues["-URGENT-"])
                    self.config["Data.defrag.decode"]["-CRITICAL-"] = \
                        str(collectvalues["-CRITICAL-"])

                    self.config["Data.defrag.decode"]["-PFVAR-"] = \
                        collectvalues["-PFVAR-"]
                    self.config["Data.defrag.decode"]["-PSVAR-"] = \
                        collectvalues["-PSVAR-"]
                    self.config["Data.defrag.decode"]["-PTVAR-"] = \
                        collectvalues["-PTVAR-"]

                    self.config["Data.defrag.decode"]["-SFVAR-"] = \
                        collectvalues["-SFVAR-"]
                    self.config["Data.defrag.decode"]["-SSVAR-"] = \
                        collectvalues["-SSVAR-"]
                    self.config["Data.defrag.decode"]["-STVAR-"] = \
                        collectvalues["-STVAR-"]

                except KeyError:

                    if not self.config.has_section("Data.defrag.decode"): self.config.add_section(
                        "Data.defrag.decode")

                    if not self.config.has_option("Data.defrag.decode", "-FILE-"):
                        self.config.set("Data.defrag.decode", "-FILE-",
                                        collectvalues["-FILE-"])
                    if not self.config.has_option("Data.defrag.decode", "-DRIVE-"):
                        self.config.set("Data.defrag.decode", "-DRIVE-",
                                        collectvalues["-DRIVE-"])
                    if not self.config.has_option("Data.defrag.decode", "-SSTART-"):
                        self.config.set("Data.defrag.decode", "-SSTART-",
                                        str(collectvalues["-SSTART-"]))
                    if not self.config.has_option("Data.defrag.decode", "-END-"):
                        self.config.set("Data.defrag.decode", "-END-",
                                        str(collectvalues["-END-"]))
                    if not self.config.has_option("Data.defrag.decode", "-BANDWIDTH-"):
                        self.config.set("Data.defrag.decode", "-BANDWIDTH-",
                                        collectvalues["-BANDWIDTH-"])
                    if not self.config.has_option("Data.defrag.decode", "-CORES-"):
                        self.config.set("Data.defrag.decode", "-CORES-",
                                        str(collectvalues["-CORES-"]))

                    if not self.config.has_option("Data.defrag.decode", "-START-"):
                        self.config.set("Data.defrag.decode", "-START-",
                                        str(collectvalues["-START-"]))
                    if not self.config.has_option("Data.defrag.decode", "-NORMAL-"):
                        self.config.set("Data.defrag.decode", "-NORMAL-",
                                        str(collectvalues["-NORMAL-"]))
                    if not self.config.has_option("Data.defrag.decode", "-CORNER-"):
                        self.config.set("Data.defrag.decode", "-CORNER-",
                                        str(collectvalues["-CORNER-"]))
                    if not self.config.has_option("Data.defrag.decode", "-URGENT-"):
                        self.config.set("Data.defrag.decode", "-URGENT-",
                                        str(collectvalues["-URGENT-"]))
                    if not self.config.has_option("Data.defrag.decode", "-CRITICAL-"):
                        self.config.set("Data.defrag.decode", "-CRITICAL-",
                                        str(collectvalues["-CRITICAL-"]))

                    if not self.config.has_option("Data.defrag.decode", "-PFVAR-"):
                        self.config.set("Data.defrag.decode", "-PFVAR-",
                                        collectvalues["-PFVAR-"])
                    if not self.config.has_option("Data.defrag.decode", "-PSVAR-"):
                        self.config.set("Data.defrag.decode", "-PSVAR-",
                                        collectvalues["-PSVAR-"])
                    if not self.config.has_option("Data.defrag.decode", "-PTVAR-"):
                        self.config.set("Data.defrag.decode", "-PTVAR-",
                                        collectvalues["-PTVAR-"])

                    if not self.config.has_option("Data.defrag.decode", "-SFVAR-"):
                        self.config.set("Data.defrag.decode", "-SFVAR-",
                                        collectvalues["-SFVAR-"])
                    if not self.config.has_option("Data.defrag.decode", "-SSVAR-"):
                        self.config.set("Data.defrag.decode", "-SSVAR-",
                                        collectvalues["-SSVAR-"])
                    if not self.config.has_option("Data.defrag.decode", "-STVAR-"):
                        self.config.set("Data.defrag.decode", "-STVAR-",
                                        collectvalues["-STVAR-"])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            elif collect_button == "-FILE-":
                dirPath = collectvalues['-FILE-']
                driveName = collectvalues['-DRIVE-']
                mode = 0
                if driveName == 'ADP':
                    mode = 1
                elif driveName == 'CDR':
                    mode = 2
                dhg, dhFile = display_dir(defragObjectConfigWindow, dirPath, mode)

            elif collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

        defragObjectConfigWindow.close()

        return Closed

    def ARMAModelPredict(self):
        """

        Returns:
            None
        """

        class ObjectConfig:
            objectFilePath = None
            objectIDs = []
            trackingVars = []

            def __init__(self, configFilePath):
                self.objectFilePath = configFilePath

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the ObjectConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    mep: MediaErrorPredictor instance
                """
                mep = MEP.MediaErrorPredictor(self.objectFilePath, debug=debug)
                self.dataDict = mep.dataDict
                self.objectIDs = self.dataDict.keys()

                return mep

        dataFile = self.GetDataFile("ARMA.Predict", "-FILE-")
        if dataFile is None:
            print("Error: No viable datafile found for ARMA Prediction")
            return

        objectFile = ObjectConfig(dataFile)
        mep = objectFile.readConfigContent()

        try:
            currentObject = self.config["ARMA.Predict"]["-OBJECT-"]
            try:
                subSeqLen = int(self.config["ARMA.Predict"]["-SSL-"])
            except ValueError:
                subSeqLen = int(float(self.config["ARMA.Predict"]["-SSL-"]))
            matrixProfileFlag = self.config["ARMA.Predict"]["-MATRIX-"] == "Yes"
            currentField = self.config["ARMA.Predict"]["-FIELD-"]
        except KeyError as e:
            print("Error: option not set correctly for ARMA Model")
            print("Error key: ", e)

        # Get timestamp for start of collecting
        timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

        mep.setMatrixProfileFlag(matrixProfileFlag, subSeqLen=subSeqLen)
        mep.writeARMAToPDF(currentObject,
                           currentField,
                           outFile=os.path.join(self.outputLocation, "ARMA_Model_" + timeStamp + ".pdf"))

        return

    def ARMAModelPredictConfig(self):
        """

        Returns:
            None
        """

        class ObjectConfig:
            objectFilePath = None
            objectIDs = []
            trackingVars = []

            def __init__(self, configFilePath):
                self.objectFilePath = configFilePath

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the ObjectConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    mep: MediaErrorPredictor instance
                """
                mep = MEP.MediaErrorPredictor(self.objectFilePath, debug=debug)
                self.dataDict = mep.dataDict
                self.objectIDs = self.dataDict.keys()

                return mep

        def display_dir(window, objectFile, currentObject):
            """
            function for updating the values contained in the drop down menus for tracking variables

            Args:
                window: window instance
                objectFile: ObjectConfig instance
                currentObject: String for the name of the current object

            Returns:

            """
            trackingVars = objectFile.dataDict[currentObject].keys()
            trackingVars = ["None"] + list(trackingVars)
            window['-FIELD-'].Update(values=trackingVars)

        def populate_object(window, dirPath):
            """
            function for populating the ObjectConfig instance and updating the drop down menu for the objects
            available in the configuration file

            Args:
                window: window instance
                dirPath: String for the path to the configuration file

            Returns:
                mep: MediaErrorPredictor instance
                objectFile: ObjectConfig instance
            """
            objectFile = ObjectConfig(str(dirPath))
            mep = objectFile.readConfigContent()
            dataKeys = ["None"] + list(objectFile.dataDict.keys())
            window["-OBJECT-"].Update(values=dataKeys)
            return mep, objectFile

        layout = src.software.guiLayouts.GUILayouts().ARMAPredictionGraph(returnLayout=True)
        layout.append([PySimpleGUI.Button("Submit", key="ARMA.Predict.submit")])

        programLabel = "RAAD OneShot ARMA Model Predict Config"

        ARMAModelPredictConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)

        mep = None
        objectFileARMA = None
        Closed = False

        try:
            # Configure choices in the gui
            ARMAModelPredictConfigWindow["-FILE-"].update(
                self.config["ARMA.Predict"]["-FILE-"])
            ARMAModelPredictConfigWindow["-OBJECT-"].update(
                self.config["ARMA.Predict"]["-OBJECT-"])
            ARMAModelPredictConfigWindow["-FIELD-"].update(
                self.config["ARMA.Predict"]["-FIELD-"])
            try:
                ARMAModelPredictConfigWindow["-SSL-"].update(
                    int(self.config["ARMA.Predict"]["-SSL-"]))
            except ValueError:
                ARMAModelPredictConfigWindow["-SSL-"].update(
                    int(float(self.config["ARMA.Predict"]["-SSL-"])))
            ARMAModelPredictConfigWindow["-MATRIX-"].update(
                self.config["ARMA.Predict"]["-MATRIX-"])
        except KeyError:
            print("ERROR: config lacking configurations for ARMA Model Predict")

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = ARMAModelPredictConfigWindow.read()

            if collect_button == "ARMA.Predict.submit":
                try:
                    self.config["ARMA.Predict"]["-FILE-"] = collectvalues[
                        "-FILE-"]
                    self.config["ARMA.Predict"]["-OBJECT-"] = collectvalues[
                        "-OBJECT-"]
                    self.config["ARMA.Predict"]["-FIELD-"] = collectvalues[
                        "-FIELD-"]
                    self.config["ARMA.Predict"]["-SSL-"] = str(collectvalues[
                                                                   "-SSL-"])
                    self.config["ARMA.Predict"]["-MATRIX-"] = collectvalues[
                        "-MATRIX-"]
                except KeyError:
                    if not self.config.has_section("ARMA.Predict"): self.config.add_section(
                        "ARMA.Predict")
                    if not self.config.has_option("ARMA.Predict", "-FILE-"):
                        self.config.set("ARMA.Predict", "-FILE-",
                                        collectvalues["-FILE-"])
                    if not self.config.has_option("ARMA.Predict", "-OBJECT-"):
                        self.config.set("ARMA.Predict", "-OBJECT-",
                                        collectvalues["-OBJECT-"])
                    if not self.config.has_option("ARMA.Predict", "-FIELD-"):
                        self.config.set("ARMA.Predict", "-FIELD-",
                                        collectvalues["-FIELD-"])
                    if not self.config.has_option("ARMA.Predict", "-SSL-"):
                        self.config.set("ARMA.Predict", "-SSL-",
                                        str(collectvalues["-SSL-"]))
                    if not self.config.has_option("ARMA.Predict", "-MATRIX-"):
                        self.config.set("ARMA.Predict", "-MATRIX-",
                                        collectvalues["-MATRIX-"])

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            elif collect_button == "-FILE-":
                dirPathARMA = collectvalues["-FILE-"]
                if os.path.exists(dirPathARMA):
                    mep, objectFileARMA = populate_object(ARMAModelPredictConfigWindow, dirPathARMA)

            elif collect_button == "-OBJECT-":
                currentObjectARMA = collectvalues["-OBJECT-"]
                if objectFileARMA != None:
                    display_dir(ARMAModelPredictConfigWindow, objectFileARMA, currentObjectARMA)

            elif collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

        ARMAModelPredictConfigWindow.close()

        return Closed

    def RNNModelPredict(self):
        """

        Returns:
            None
        """

        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-", "-PFOVAR-", "-PFIVAR-"]
        secondaryVarLabels = ["-SFVAR-"]

        class ObjectConfigRNN:
            objectFilePath = None
            objectIDs = []

            def __init__(self, configFilePath):
                self.objectFilePath = configFilePath
                self.dataDict = None
                self.objectIDs = None

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the ObjectConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    rnn: mediaPredictionRNN instance
                """
                rnn = RNN.timeSeriesRNN(configFilePath=self.objectFilePath, debug=debug)
                self.dataDict = rnn.dataDict
                self.objectIDs = list(self.dataDict.keys())

                return rnn

        # if not os.path.exists(self.config["RNN.Predict"]["-FILE-"]):
        #     print("Error in OneShotAPI.: Input file not found, please choose an existing data file")
        #     print("Path: ", self.config["RNN.Predict"]["-FILE-"])
        #     return

        dataFile = self.GetDataFile("RNN.Predict", "-FILE-")
        if dataFile is None:
            print("Error: No viable datafile found for RNN Prediction")
            return

        # Command
        objectFile = ObjectConfigRNN(dataFile)
        rnn = objectFile.readConfigContent()

        try:

            trackingVars = []
            plotVars = []

            for name in primaryVarLabels:
                if self.config["RNN.Predict"][name] != "None":
                    trackingVars.append(self.config["RNN.Predict"][name])

            for name in secondaryVarLabels:
                if self.config["RNN.Predict"][name] != "None" and self.config["RNN.Predict"][name] != "":
                    plotVars.append(self.config["RNN.Predict"][name])

            if not all(plotVar in trackingVars for plotVar in plotVars):
                print("All plotted variables must be in tracking variables. Aborting...")

            inputWidth = int(float(self.config["RNN.Predict"]['-INPUTWIDTH-']))
            labelWidth = int(float(self.config["RNN.Predict"]['-LABELWIDTH-']))
            shift = int(float(self.config["RNN.Predict"]['-SHIFT-']))
            hiddenLayers = int(float(self.config["RNN.Predict"]['-HLAYERS-']))
            batchSize = int(float(self.config["RNN.Predict"]['-BS-']))
            maxEpochs = int(float(self.config["RNN.Predict"]['-ME-']))
            matrixProfileFlag = self.config["RNN.Predict"]['-MATRIX-'] == "Yes"
            embeddedEncodingFlag = self.config["RNN.Predict"]['-EE-'] == "Yes"
            categoricalEncodingFlag = self.config["RNN.Predict"]['-CE-'] == "Yes"
            currentObject = self.config["RNN.Predict"]["-OBJECT-"]

            try:
                subSeqLen = int(self.config["RNN.Predict"]["-SSL-"])
                inputWidth = int(self.config["RNN.Predict"]['-INPUTWIDTH-'])
                labelWidth = int(self.config["RNN.Predict"]['-LABELWIDTH-'])
                shift = int(self.config["RNN.Predict"]['-SHIFT-'])
                hiddenLayers = int(self.config["RNN.Predict"]['-HLAYERS-'])
                batchSize = int(self.config["RNN.Predict"]['-BS-'])
                maxEpochs = int(self.config["RNN.Predict"]['-ME-'])
            except ValueError:
                subSeqLen = int(float(self.config["RNN.Predict"]["-SSL-"]))
                inputWidth = int(float(self.config["RNN.Predict"]['-INPUTWIDTH-']))
                labelWidth = int(float(self.config["RNN.Predict"]['-LABELWIDTH-']))
                shift = int(float(self.config["RNN.Predict"]['-SHIFT-']))
                hiddenLayers = int(float(self.config["RNN.Predict"]['-HLAYERS-']))
                batchSize = int(float(self.config["RNN.Predict"]['-BS-']))
                maxEpochs = int(float(self.config["RNN.Predict"]['-ME-']))
            # input validation for RNN Model Predict
            # if inputWidth < 80:
            #     debugMessages += 'Input Width for RNN model is to small. Must be >= 80\n'
            #     inputWidth = 80
            #     self.config.set('RNN.Predict', '-INPUTWIDTH-', str(inputWidth))
            #     debug = True
            # if labelWidth < 20:
            #     debugMessages += 'Label Width for RNN model is to small. Must be >= 20\n'
            #     labelWidth = 20
            #     self.config.set('RNN.Predict', '-LABELWIDTH-', str(labelWidth))
            #     debug = True
            # if batchSize < 32:
            #     debugMessages += 'Batch size for RNN model is to small. Must be >= 32\n'
            #     batchSize = 32
            #     self.config.set('RNN.Predict', '-BS-', str(batchSize))
            #     debug = True
            # if shift < 2:
            #     debugMessages += 'Shift for RNN model is to small. Must be >= 2\n'
            #     shift = 2
            #     self.config.set('RNN.Predict', '-SHIFT-', str(shift))
            #     debug = True
            # if hiddenLayers < 128:
            #     debugMessages += 'Hidden layers for RNN model is to small. Must be >= 128\n'
            #     hiddenLayers = 128
            #     self.config.set('RNN.Predict', '-HLAYERS-', str(hiddenLayers))
            #     debug = True
            # if maxEpochs < 2000:
            #     debugMessages += 'Max Epochs for RNN model is to small. Must be >= 2000\n'
            #     maxEpochs = 2000
            #     self.config.set('RNN.Predict', '-ME-', str(maxEpochs))
            #     debug = True
        except KeyError as e:
            print("Error: option not set correctly for RNN Model")
            print("Error key: ", e)
            return

        # Get timestamp for start of collecting
        timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

        RNNFileName = "RNN_Prediction_{0}.pdf".format(timeStamp)
        print("Creating pdf file: ", RNNFileName)

        rnn.setMatrixProfile(value=matrixProfileFlag,
                             subSeqLen=subSeqLen)
        rnn.setEmbeddedEncoding(value=embeddedEncodingFlag)
        rnn.setCategoricalEncoding(value=categoricalEncodingFlag)
        rnn.writeRNNtoPDF(inputWidth,
                          labelWidth,
                          shift,
                          batchSize,
                          hiddenLayers,
                          currentObject,
                          trackingVars,
                          plotVars[0],
                          maxEpochs,
                          pdfFileName=os.path.join(self.outputLocation, RNNFileName))
        return

    def RNNModelPredictConfig(self):
        """

        Returns:
            None
        """

        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-", "-PFOVAR-", "-PFIVAR-"]
        secondaryVarLabels = ["-SFVAR-"]

        class ObjectConfigRNN_Obsolute:
            objectFilePath = None
            objectIDs = []

            def __init__(self, configFilePath):
                self.objectFilePath = configFilePath
                self.dataDict = None
                self.objectIDs = None

            def readConfigContent(self, debug=False):
                """
                function for reading the configuration file into a dictionary and populating the ObjectConfig
                instance

                Args:
                    debug: Boolean flag to activate debug statements

                Returns:
                    rnn: mediaPredictionRNN instance
                """
                rnnLocal = RNN.timeSeriesRNN(configFilePath=self.objectFilePath, debug=debug)
                self.dataDict = rnnLocal.dataDict
                self.objectIDs = list(self.dataDict.keys())

                return rnnLocal

        def display_dir_RNN(window, objectFileLocal, currentObjectLocal):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                window: window instance
                objectFileLocal: ObjectConfig instance
                currentObjectLocal: String for the name of the current object

            Returns:

            """
            try:
                trackingVars = objectFileLocal.dataDict[currentObjectLocal].keys()
                primaryVars = ["None"] + list(trackingVars)
                secondaryVars = ["None"] + list(trackingVars)
                for name in primaryVarLabels:
                    window[name].Update(value=primaryVars[0], values=primaryVars)
                for name in secondaryVarLabels:
                    window[name].Update(value=secondaryVars[0], values=secondaryVars)
            except:
                pass

        def populate_object_RNN(window, dirPathLocal):
            """
            function for populating the ObjectConfig instance and updating the drop down menu for the objects
            available in the configuration file

            Args:
                window: window instance
                dirPathLocal: String for the path to the configuration file

            Returns:
                rnn: mediaPredictionRNN instance
                objectFile: ObjectConfig instance
                objectList: list of object names (ex. ThermalSensor)
            """
            objectFileLocal = src.software.guiCommon.ObjectConfigRNN(str(dirPathLocal))
            rnnLocal = objectFileLocal.readConfigContent(debug=True)
            objectListLocal = list(objectFileLocal.objectIDs)
            objectNamesDict = {}
            objectIDsDictLocal = {}
            for key in objectListLocal:
                currentName = objectFileLocal.dataDict[key]["name"]
                objectNamesDict[currentName] = key
                objectIDsDictLocal[key] = currentName
            window["-OBJECT-"].Update(values=objectListLocal)
            return rnnLocal, objectFileLocal, objectListLocal, objectIDsDictLocal

        import src.software.guiLayouts  # @todo
        layout = src.software.guiLayouts.GUILayouts().RNNPredictorGraph(returnLayout=True)
        layout.append([PySimpleGUI.Button("Submit", key="RNN.Predict.submit")])

        programLabel = "RAAD OneShot RNN Model Config"

        RNNModelPredictConfigWindow = PySimpleGUI.Window(programLabel, layout, finalize=True)
        dirPath = None
        rnn = None
        objectFile = None
        currentObject = None
        objectList = None
        objectDict = None
        objectIDsDict = None
        Closed = False

        if self.config.has_section("RNN.Predict"):
            if self.config.has_option("RNN.Predict", "-FILE-") and \
                    self.config.has_option("RNN.Predict", "-OBJECT-"):
                if os.path.exists(self.config["RNN.Predict"]["-FILE-"]):
                    dirPath = self.config["RNN.Predict"]["-FILE-"]
                    currentObject = self.config["RNN.Predict"]["-OBJECT-"]
                    rnn, objectFile, objectDict, objectIDsDict = populate_object_RNN(RNNModelPredictConfigWindow,
                                                                                     dirPath)
                    try:
                        display_dir_RNN(RNNModelPredictConfigWindow, objectFile, currentObject)
                    except KeyError:
                        print("Stored object: ", currentObject, " is not present in the stored data file: ",
                              dirPath)
                        print("Please reconfigure the configurations for RNN prediction")
                else:
                    print("Configured file is not present, please reconfigure filepath to an existing file")

        try:
            # Configure choices in the gui
            RNNModelPredictConfigWindow["-FILE-"].update(
                self.config["RNN.Predict"]["-FILE-"])
            # try:
            #     RNNModelPredictConfigWindow["-OBJECT-"].update(
            #         objectIDsDict[self.config["RNN.Predict"]["-OBJECT-"]])
            # except TypeError:
            #     print("Can't correctly gather name of object, please reconfigure the object")
            RNNModelPredictConfigWindow["-OBJECT-"].update(
                self.config["RNN.Predict"]["-OBJECT-"])
            RNNModelPredictConfigWindow["-PFVAR-"].update(
                self.config["RNN.Predict"]["-PFVAR-"])
            RNNModelPredictConfigWindow["-PSVAR-"].update(
                self.config["RNN.Predict"]["-PSVAR-"])
            RNNModelPredictConfigWindow["-PTVAR-"].update(
                self.config["RNN.Predict"]["-PTVAR-"])
            RNNModelPredictConfigWindow["-PFOVAR-"].update(
                self.config["RNN.Predict"]["-PFOVAR-"])
            RNNModelPredictConfigWindow["-PFIVAR-"].update(
                self.config["RNN.Predict"]["-PFIVAR-"])
            RNNModelPredictConfigWindow["-SFVAR-"].update(
                self.config["RNN.Predict"]["-SFVAR-"])

            RNNModelPredictConfigWindow["-INPUTWIDTH-"].update(
                float(self.config["RNN.Predict"]["-INPUTWIDTH-"]))
            RNNModelPredictConfigWindow["-LABELWIDTH-"].update(
                float(self.config["RNN.Predict"]["-LABELWIDTH-"]))
            RNNModelPredictConfigWindow["-SHIFT-"].update(
                float(self.config["RNN.Predict"]["-SHIFT-"]))
            RNNModelPredictConfigWindow["-HLAYERS-"].update(
                float(self.config["RNN.Predict"]["-HLAYERS-"]))
            RNNModelPredictConfigWindow["-BS-"].update(
                float(self.config["RNN.Predict"]["-BS-"]))
            RNNModelPredictConfigWindow["-ME-"].update(
                float(self.config["RNN.Predict"]["-ME-"]))

            RNNModelPredictConfigWindow["-CE-"].update(
                self.config["RNN.Predict"]["-CE-"])
            RNNModelPredictConfigWindow["-EE-"].update(
                self.config["RNN.Predict"]["-EE-"])
            RNNModelPredictConfigWindow["-MATRIX-"].update(
                self.config["RNN.Predict"]["-MATRIX-"])
            RNNModelPredictConfigWindow["-SSL-"].update(
                float(self.config["RNN.Predict"]["-SSL-"]))
        except KeyError:
            print("ERROR: config lacking configurations for")

        repeatEventLoop = True
        while repeatEventLoop:
            collect_button, collectvalues = RNNModelPredictConfigWindow.read()

            if collect_button == "RNN.Predict.submit":
                try:
                    self.config["RNN.Predict"]["-FILE-"] = collectvalues[
                        "-FILE-"]
                    self.config["RNN.Predict"]["-OBJECT-"] = collectvalues[
                        "-OBJECT-"]

                    self.config["RNN.Predict"]["-PFVAR-"] = collectvalues[
                        "-PFVAR-"]
                    self.config["RNN.Predict"]["-PSVAR-"] = collectvalues[
                        "-PSVAR-"]
                    self.config["RNN.Predict"]["-PTVAR-"] = collectvalues[
                        "-PTVAR-"]
                    self.config["RNN.Predict"]["-PFOVAR-"] = collectvalues[
                        "-PFOVAR-"]
                    self.config["RNN.Predict"]["-PFIVAR-"] = collectvalues[
                        "-PFIVAR-"]
                    self.config["RNN.Predict"]["-SFVAR-"] = collectvalues[
                        "-SFVAR-"]

                    self.config["RNN.Predict"]["-INPUTWIDTH-"] = str(collectvalues[
                                                                         "-INPUTWIDTH-"])
                    self.config["RNN.Predict"]["-LABELWIDTH-"] = str(collectvalues[
                                                                         "-LABELWIDTH-"])
                    self.config["RNN.Predict"]["-SHIFT-"] = str(collectvalues[
                                                                    "-SHIFT-"])
                    self.config["RNN.Predict"]["-HLAYERS-"] = str(collectvalues[
                                                                      "-HLAYERS-"])
                    self.config["RNN.Predict"]["-BS-"] = str(collectvalues[
                                                                 "-BS-"])
                    self.config["RNN.Predict"]["-ME-"] = str(collectvalues[
                                                                 "-ME-"])

                    self.config["RNN.Predict"]["-CE-"] = collectvalues[
                        "-CE-"]
                    self.config["RNN.Predict"]["-EE-"] = collectvalues[
                        "-EE-"]
                    self.config["RNN.Predict"]["-MATRIX-"] = collectvalues[
                        "-MATRIX-"]
                    self.config["RNN.Predict"]["-SSL-"] = str(collectvalues[
                                                                  "-SSL-"])
                except KeyError:
                    if not self.config.has_section("RNN.Predict"): self.config.add_section(
                        "RNN.Predict")
                    if not self.config.has_option("RNN.Predict", "-FILE-"):
                        self.config.set("RNN.Predict", "-FILE-",
                                        collectvalues["-FILE-"])
                    if not self.config.has_option("RNN.Predict", "-OBJECT-"):
                        self.config.set("RNN.Predict", "-OBJECT-",
                                        collectvalues["-OBJECT-"])

                    if not self.config.has_option("RNN.Predict", "-PFVAR-"):
                        self.config.set("RNN.Predict", "-PFVAR-",
                                        collectvalues["-PFVAR-"])
                    if not self.config.has_option("RNN.Predict", "-PSVAR-"):
                        self.config.set("RNN.Predict", "-PSVAR-",
                                        collectvalues["-PSVAR-"])
                    if not self.config.has_option("RNN.Predict", "-PTVAR-"):
                        self.config.set("RNN.Predict", "-PTVAR-",
                                        collectvalues["-PTVAR-"])
                    if not self.config.has_option("RNN.Predict", "-PFOVAR-"):
                        self.config.set("RNN.Predict", "-PFOVAR-",
                                        collectvalues["-PFOVAR-"])
                    if not self.config.has_option("RNN.Predict", "-PFIVAR-"):
                        self.config.set("RNN.Predict", "-PFIVAR-",
                                        collectvalues["-PFIVAR-"])
                    if not self.config.has_option("RNN.Predict", "-SFVAR-"):
                        self.config.set("RNN.Predict", "-SFVAR-",
                                        collectvalues["-SFVAR-"])

                    if not self.config.has_option("RNN.Predict", "-INPUTWIDTH-"):
                        self.config.set("RNN.Predict", "-INPUTWIDTH-",
                                        str(collectvalues["-INPUTWIDTH-"]))
                    if not self.config.has_option("RNN.Predict", "-LABELWIDTH-"):
                        self.config.set("RNN.Predict", "-LABELWIDTH-",
                                        str(collectvalues["-LABELWIDTH-"]))
                    if not self.config.has_option("RNN.Predict", "-SHIFT-"):
                        self.config.set("RNN.Predict", "-SHIFT-",
                                        str(collectvalues["-SHIFT-"]))
                    if not self.config.has_option("RNN.Predict", "-HLAYERS-"):
                        self.config.set("RNN.Predict", "-HLAYERS-",
                                        str(collectvalues["-HLAYERS-"]))
                    if not self.config.has_option("RNN.Predict", "-BS-"):
                        self.config.set("RNN.Predict", "-BS-",
                                        str(collectvalues["-BS-"]))
                    if not self.config.has_option("RNN.Predict", "-ME-"):
                        self.config.set("RNN.Predict", "-ME-",
                                        str(collectvalues["-ME-"]))

                    if not self.config.has_option("RNN.Predict", "-CE-"):
                        self.config.set("RNN.Predict", "-CE-",
                                        collectvalues["-CE-"])
                    if not self.config.has_option("RNN.Predict", "-EE-"):
                        self.config.set("RNN.Predict", "-EE-",
                                        collectvalues["-EE-"])
                    if not self.config.has_option("RNN.Predict", "-MATRIX-"):
                        self.config.set("RNN.Predict", "-MATRIX-",
                                        collectvalues["-MATRIX-"])
                    if not self.config.has_option("RNN.Predict", "-SSL-"):
                        self.config.set("RNN.Predict", "-SSL-",
                                        str(collectvalues["-SSL-"]))

                with open(self.configLocation, 'w') as configFile:
                    self.config.write(configFile)

                repeatEventLoop = False

            elif collect_button == "-FILE-":
                dirPath = collectvalues['-FILE-']
                if os.path.exists(dirPath):
                    rnn, objectFile, objectDict, objectIDsDict = populate_object_RNN(RNNModelPredictConfigWindow,
                                                                                     dirPath)

            elif collect_button == "Select":
                currentObject = collectvalues['-OBJECT-']
                display_dir_RNN(RNNModelPredictConfigWindow, objectFile, currentObject)

            elif collect_button == PySimpleGUI.WIN_CLOSED:
                repeatEventLoop = False
                Closed = True

        RNNModelPredictConfigWindow.close()

        return Closed

    def GetContentReport(self):

        reportFlatDictionary = self.reportDictionary.getSuperDictionary()

        contentReportName = "Content_Report_" + datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f") + ".txt"

        with open(os.path.join(self.outputLocation, contentReportName), "w+") as contentReportFile:
            pprint.pprint(reportFlatDictionary, contentReportFile, indent=3, width=100)

        return

    def OneShotTaskConfig(self, collect_values):
        """
        Configures what tasks are executed by the system
        Args:
            collect_values: list of inputs the user put into the OneShot Window

        Returns:
            None

        """

        for taskName in self.FullTaskList:
            try:
                self.config["tasks.list"][taskName.lower()] = str(collect_values[taskName.lower()])
            except KeyError:
                if not self.config.has_section("tasks.list"):
                    self.config.add_section("tasks.list")
                self.config["tasks.list"][taskName.lower()] = str(collect_values[taskName.lower()])

    @staticmethod
    def ExecutePhase(phase):
        Success = False

        while not Success:

            try:

                print("Executing function...")
                phase[1]()
                Success = True

            except BaseException as exceptionLogs:

                print("Execption occurred, please reconfigure configuration for ", phase[0])

                print('Exception_Log():')
                print(exceptionLogs)
                print('print_exc():')
                traceback.print_exc(file=sys.stdout)
                print('print_exc(1):')
                traceback.print_exc(limit=1, file=sys.stdout)

                if phase[0] == "User.report.execute":
                    print(
                        "Error: no configuration changes for creation of user report, please look at traceback and remedy issue")
                    return
                else:
                    prematureClose = phase[2]()
                    if prematureClose is True:
                        print("User closed the window, skipping this phase")
                        return

    def ExecuteTasks(self, collect_values):
        """
        Execute tasks with given configurations for
        Returns:

        """

        if hasattr(self, "config"):

            self.OneShotTaskConfig(collect_values)

            with open(self.configLocation, 'w') as configFile:
                self.config.write(configFile)

            for Stage in self.StateMachineStages:
                executePhase = False
                if str(collect_values[Stage[0]]) == "True":
                    self.ExecutePhase(Stage)

    def Window(self):
        continueRun = True

        ProgramLabel = "OneShot Window"

        # Execute Setup Functions

        OneShotwindowActive = PySimpleGUI.Window(title=ProgramLabel,
                                                 resizable=True,
                                                 auto_size_text=True,
                                                 auto_size_buttons=True,
                                                 grab_anywhere=True,
                                                 finalize=True).Layout([[PySimpleGUI.Column(self.OneShotLayout(),
                                                                                            scrollable=True, pad=(
                (11, 11), (11, 11)))]]
                                                                       )

        while continueRun:
            (collect_button, collect_values) = (OneShotwindowActive).read()

            try:
                if collect_button == "EXIT":
                    continueRun = False
                elif collect_button == PySimpleGUI.WIN_CLOSED:
                    continueRun = False

                elif collect_button == "oneshot.execute":
                    self.ExecuteTasks(collect_values)

                elif collect_button == "data.collect.configure":
                    self.DataCollectConfig()
                elif collect_button == "axon.download.configure":
                    self.AxonDownloadConfig()
                elif collect_button == "axon.upload.configure":
                    self.AxonUploadConfig()
                elif collect_button == "data.table.configure":
                    self.DataTableConfig()
                elif collect_button == "data.graph.configure":
                    self.GenericObjectDecodeConfig()
                elif collect_button == "defrag.graph.configure":
                    self.DefragObjectDecodeConfig()
                elif collect_button == "arma.predict.configure":
                    self.ARMAModelPredictConfig()
                elif collect_button == "rnn.predict.configure":
                    self.RNNModelPredictConfig()
                # elif collect_button == "User.report.configure":
                #     self.GetContentReportConfig()

            except BaseException as exceptionLogs:
                print('Exception_Log():')
                print(exceptionLogs)
                print('print_exc():')
                traceback.print_exc(file=sys.stdout)
                print('print_exc(1):')
                traceback.print_exc(limit=1, file=sys.stdout)
                pass

        OneShotwindowActive.close()

    def OneShotExecuteAPI(self, ExecuteConfig=None):
        try:
            if ExecuteConfig is None:
                config = dict(self.config._sections["tasks.list"])
            elif isinstance(ExecuteConfig, configparser.ConfigParser):
                config = dict(ExecuteConfig._sections["tasks.list"])
            else:
                config = ExecuteConfig
        except KeyError:
            print("Task list not correctly configured, please configure your selections")
            config = None

        if config is not None:
            self.ExecuteTasks(config)
        return

    # def GetContentReportConfig(self):
    #     """
    #
    #     Returns:
    #         None
    #     """
    #
    #     layout = GUI.example.profileUser(returnLayout=True)
    #     layout.append([PySimpleGUI.Button("Submit", key="")])
    #
    #     programLabel = "RAAD OneShot Profile User Config"
    #
    #     profileUserWindow = PySimpleGUI.Window(programLabel, layout)
    #
    #     try:
    #         # Configure choices in the gui
    #         profileUserWindow[""].update(
    #             self.config[""][""])
    #         profileUserWindow[""].update(
    #             self.config[""][""])
    #         profileUserWindow[""].update(
    #             self.config[""][""])
    #     except KeyError:
    #         print("ERROR: config lacking configurations for")
    #
    #     repeatEventLoop = True
    #     while repeatEventLoop:
    #         collect_button, collectvalues = profileUserWindow.read()
    #
    #         if collect_button == "":
    #             try:
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #             except KeyError:
    #                 if not self.config.has_section(""): self.config.add_section(
    #                     "")
    #                 if not self.config.has_option("", ""):
    #                     self.config.set("", "",
    #                                     collectvalues[""])
    #
    #             with open(self.configLocation, 'w') as configFile:
    #                 self.config.write(configFile)
    #
    #             repeatEventLoop = False
    #
    #     profileUserWindow.close()
    #
    #     return

    #################### Config Execute Combo Template ######################################################################
    def GenericObjectDecode(self):
        """

         Returns:
             None
        """

        if not os.path.exists(self.config[""][""]):
            print("Error in OneShotAPI.: Output directory not found, please choose an existing directory")
            return

        # Command

        return

    # def GenericObjectDecodeConfig(self):
    #     """
    #
    #     Returns:
    #         None
    #     """
    #
    #
    #
    #     layout = GUI.example.(returnLayout=True)
    #     layout.append([PySimpleGUI.Button("Submit", key="")])
    #
    #     programLabel = "RAAD OneShot  Config"
    #
    #     AxonConfigWindow = PySimpleGUI.Window(programLabel, layout)
    #
    #     try:
    #         # Configure choices in the gui
    #         AxonConfigWindow[""].update(
    #             self.config[""][""])
    #         AxonConfigWindow[""].update(
    #             self.config[""][""])
    #         AxonConfigWindow[""].update(
    #             self.config[""][""])
    #     except KeyError:
    #         print("ERROR: config lacking configurations for")
    #
    #     repeatEventLoop = True
    #     while repeatEventLoop:
    #         collect_button, collectvalues = AxonConfigWindow.read()
    #
    #         if collect_button == "":
    #             try:
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #                 self.config[""][""] = collectvalues[
    #                     ""]
    #             except KeyError:
    #                 if not self.config.has_section(""): self.config.add_section(
    #                     "")
    #                 if not self.config.has_option("", ""):
    #                     self.config.set("", "",
    #                                     collectvalues[""])
    #
    #             with open(self.configLocation, 'w') as configFile:
    #                 self.config.write(configFile)
    #
    #             repeatEventLoop = False
    #
    #     AxonConfigWindow.close()
    #
    #     return

    #############################################################################
