#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package guiDeveloper
import optparse, os, pprint, sys, datetime, traceback, random, string, getpass, configparser, unittest
# import hashlib, time, base64
# from Crypto.Cipher import AES
# from Crypto.Hash import SHA256
# from Crypto import Random

# Pass any command line argument for Web use
# if web is False:  # default uses the tkinter GUI
import PySimpleGUI
# import PySimpleGUIWeb as PySimpleGUI
# else:  # if there is use the Web Interface
#    import remi
#    import PySimpleGUIWeb as PySimpleGUI
import src.software.DP.preprocessingAPI as DP
import src.software.TSV.generateTSBinaries
import src.software.TSV.formatTSFiles
import src.software.TSV.loadAndProbeSystem
import src.software.axon.packageInterface
import src.software.axon.axonInterface
import src.software.axon.axonMeta
import src.software.axon.axonProfile
import src.software.access.DriveInfo
import matplotlib.backends.backend_pdf as be
import src.software.container.basicTypes
import src.software.guiLayouts
import src.software.guiCommon
import src.software.guiOneShot
import src.software.autoAI.nlogPrediction as nlogPrediction

from src.software.JIRA.analysisGuide import AnalysisGuide
from src.software.utilsCommon import tryFile, tryFolder, DictionaryFlatten, getTimeStamp, cleanAndRecreatePath
from src.software.dAMP.reportGenerator import ReportGenerator
from src.software.dAMP.gatherMeta import GatherMeta
from src.software.debug import whoami


class GUIDeveloper(object):

    def __init__(self,
                 name=None,
                 label=None,
                 layout=None,
                 form=None,
                 windowActive=None,
                 button=None,
                 values=None,
                 debug=False):
        """
        Class to easily generate windows for a user friendly interface.

        :param name: Name of the window object.
        :param label: Label on the window.
        :param layout: List of content on a window.
        :param form: The free form configuration for the window.
        :param windowActive: active window object.
        :param button: The state of the buttons for a given window.
        :param values: Values from the input windows.
        :param debug: Debug flag to get more information.
        """

        if name is not None:
            self.name = name
        else:
            self.name = None

        if label is not None:
            self.label = label
        else:
            self.label = None

        if layout is not None:
            self.layout = layout
        else:
            self.layout = []

        if form is not None:
            self.form = form
        else:
            self.form = None

        if windowActive is not None:
            self.windowActive = windowActive
        else:
            self.windowActive = None

        if button is not None:
            self.button = button
        else:
            self.button = None

        if values is not None:
            self.values = values
        else:
            self.values = None

        if debug is True or debug is False:
            self.debug = debug
        else:
            self.debug = False

        self.LookFeelStatus = False

        # Interactive top menu
        self.menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                         ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                         ['Font &Size', ['Increase &+', 'Decrease &-']],
                         ['&Help', '&About...']]

        # Program label
        self.programLabel = ''.join('Rapid Automation-Analysis for Developers (RAAD), by Prof. Joseph Tarango')
        # Absolute path to data file that contains raw telemetry data gathered in .ini form
        self.dataFile = None
        self.tarFileName = None
        self.tarFilePath = None
        self.timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self.dataFileName = "time-series" + self.timeStamp + ".ini"
        self.dataDict = None
        self.dataDictFlat = None
        self.vizDict = None
        self.cGui = None
        self.zipName = None
        self.zipFile = None
        self.contentFile = None

        # Instantiate config parser for axon metadata control
        self.config = configparser.ConfigParser()

        # Function variables Default
        self.currentFontSize = 20
        self.appFont = ("Helvetica", self.currentFontSize)
        # (collect_button, collect_values) = (None, None)
        self.firstPass = False
        self.continueRun = True
        self.visible = True
        self.identity = 'DarthVader'
        self.major = '1'
        self.minor = '0'
        self.name = 'DarthVader'
        self.mode = 'gui'
        self.encryptionStatus = False
        self.url = 'http://www.intel.com'
        self.VARIABLE_DUMP_FILE = None
        self.optionsConfigFile = tryFile(fileName="../../.raadProfile/OneShotProfile.ini")
        # Password object for accessing data.
        self.defaultPasswordFile = tryFile(fileName=".raadProfile/credentials.conf", walkUpLimit=3)
        self.passwordEncodingObject = src.software.axon.packageInterface.Cipher_AES()
        self.username_FAHB = ""
        self.password_FAHB = ""
        # Command information for Axon
        self.displayInput = ''
        self.displayReport = ''
        self.axonDownloadOutput = ''
        self.axonDownload_exitCode = ''
        self.axonDownload_cmdOutput = ''
        self.axonDownload_cmdError = ''
        self.downloadID = None
        self.downloadDirectory = None
        self.uploadMode = None
        self.uploadSuccess = None
        self.uploadID = None
        # Device information
        self.driveSelectedInfo = "Generic Info = NVMe \n Drive Size = 42* GBs \n ... \n"
        self.driveHealth = "NVMe or SATA Reason code: Healthy, Warning, Fail, Unknown \n"
        self.driveName = None
        # Folders
        self.baseFilePath = os.path.dirname(os.path.abspath(__file__))
        self.baseFolderPath = os.path.abspath(os.getcwd())
        self.binLocation = tryFolder(path='data/inputSeries')
        self.location = tryFolder(path='data')
        self.workingDir = tryFolder(path='data')
        self.locationInput = tryFolder(path='data/input')
        self.locationOutput = tryFolder(path='data/output')
        self.locationAutoParse = tryFolder(path='Auto-Parse/decode/ADP_UV')
        self.locationNlogParse = tryFolder(path='src/software/parse/nlogParser')
        # Files
        self.keyLoc = tryFile(fileName='.raadProfile/key.pub')
        self.dirPathTimeSeries = tryFile(fileName='data/workload-healthy-ADP.ini')
        self.dirPathDefragHistory = tryFile(fileName='data/workload-fail-CDR.ini')
        self.dirPathRNN = tryFile(fileName='data/time-series-RNN.ini')
        self.nlogFolder = tryFolder(path="data/output/nlog")
        self.nlogParserFolder = tryFolder(path="software/parse/nlogParser")
        self.dirPathARMA = tryFile(fileName='data/time-series-ARMA.ini')
        self.dirPathUpload = tryFile(fileName='data/time-series.ini')
        self.debugHandbookFile = tryFile(fileName='.raadProfile/debugHandbookCache.ini')
        # Selection information.
        self.modeTranslate = {"CLI": 1, "TWIDL": 2, "PARSE": 3, "IMAS": 4}
        self.currentMode = None
        self.debugHandbookTranslate = {1: "Unknown", 2: "Live", 3: "Cache", 4: "Nil"}
        self.debugHandbookStatus = self.debugHandbookTranslate[1]
        # Object information.
        self.dataInTable = self.make_table(num_rows=20, num_cols=62)
        self.dataArray = None
        self.objectFileRNN = None
        self.objectFileARMA = None
        self.objectFileGeneric = None
        self.dhFile = None
        self.currentObjectRNN = None
        self.currentObjectARMA = None
        self.currentObjectGeneric = None
        self.objectDictGeneric = None
        self.currentName = None
        self.currentObjectNumber = None
        self.driveInfo = None
        self.rnn = None
        self.mep = None
        self.vts = None
        self.dhg = None
        self.axonProfiler = None
        self.axonIDs = None
        self.axonConfig = None
        self.reportDictionary = None
        self.reportFlatDictionary = None
        self.displayReport = None
        self.UIDList = None
        self.axonID = None
        self.metaFile = None
        self.AxonInterface = None
        self.downloadWindow = None
        self.objectDict = None
        self.gen = None
        self.parseList = None
        self.binList = None

        # API vars
        self.primaryVarLabelsRNN = ["Predictor.RNN.pfvar", "Predictor.RNN.psvar", "Predictor.RNN.ptvar",
                                    "Predictor.RNN.pfovar", "Predictor.RNN.pfivar"]
        self.secondaryVarLabelsRNN = ["Predictor.RNN.sfvar"]
        self.primaryVarLabelsGenericObject = ["data.telemetry.genericObject.metadata.timeseries.pfvar",
                                              "data.telemetry.genericObject.metadata.timeseries.psvar",
                                              "data.telemetry.genericObject.metadata.timeseries.ptvar"]
        self.secondaryVarLabelsGenericObject = ["data.telemetry.genericObject.metadata.timeseries.sfvar",
                                                "data.telemetry.genericObject.metadata.timeseries.ssvar",
                                                "data.telemetry.genericObject.metadata.timeseries.stvar"]
        self.setPointLabelsDict = {"data.telemetry.defragHistory.start": "start",
                                   "data.telemetry.defragHistory.normal": "normal",
                                   "data.telemetry.defragHistory.corner": "corner",
                                   "data.telemetry.defragHistory.urgent": "urgent",
                                   "data.telemetry.defragHistory.critical": "critical"}
        self.primaryVarLabelsDefragHistory = ["data.telemetry.defragHistory.pfvar", "data.telemetry.defragHistory.psvar",
                                              "data.telemetry.defragHistory.ptvar"]
        self.secondaryVarLabelsDefragHistory = ["data.telemetry.defragHistory.sfvar", "data.telemetry.defragHistory.ssvar",
                                                "data.telemetry.defragHistory.stvar"]
        # Init of data
        # Report
        self.reportDictionary = src.software.dAMP.gatherMeta.GatherMeta()
        self.reportFlatDictionary = self.reportDictionary.getClasstoDictionary()
        self.displayReport = pprint.pformat(self.reportFlatDictionary, indent=3, width=100)
        # Axon Variable update
        self.axonProfiler = src.software.axon.axonProfile.AxonProfile()
        (self.axonIDs, self.axonConfig) = self.axonProfiler.GetProfile()
        # Load Defaults if they exist.
        self.VARIABLE_DUMP_FILE = tryFile(fileName="data/gui.dump")
        # Constructing GUI Logo
        if sys.platform.startswith('win32'):
            self.logoLocation = ('{0}\src\software\{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))
            if os.path.isfile(self.logoLocation) is False:
                self.logoLocation = ('{0}\software\{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))
        else:
            self.logoLocation = ('{0}/src/software/{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))
            if os.path.isfile(self.logoLocation) is False:
                self.logoLocation = ('{0}/software/{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png'))

        if self.debug:
            self.print_all()
        return

    def print_packageLibraryVersion(self):
        """
        Print information related to the library currently in use.
        Args:
            self: Used to access debug flag.

        Returns: Python simple GUI information.

        """
        if self.debug:
            print(PySimpleGUI, PySimpleGUI.version)
        return

    def get_all(self):
        """
        Method to access self saved data.
        Args:
            self: All data related to internal tracked information.

        Returns: All data related to internal tracked information.
        """
        return self.label, self.layout, self.form, self.windowActive, self.button, self.values, self.LookFeelStatus, self.menu_def, self.programLabel

    def print_all(self):
        """
        Method to print out the current content in the class.
        Args:
            self: Internal variables
        Returns: None
        """
        print("Name {0}".format(self.name))
        print("Label {0}".format(self.label))
        print("Layout {0}".format(self.layout))
        print("Form {0}".format(self.form))
        print("Active Window {0}".format(self.windowActive))
        print("Button {0}".format(self.button))
        print("Values {0}".format(self.values))
        print("Look Feel Status {0}".format(self.LookFeelStatus))
        print("Menu Options {0}".format(self.menu_def))
        print("Program Label {0}".format(self.programLabel))
        return

    @staticmethod
    def get_tableOptions():
        """
        Method to get the python GUI table Options.
        Args: None
        Returns: all table options
        """
        return PySimpleGUI.LOOK_AND_FEEL_TABLE

    def get_windowInputs(self):
        """
        Returns current window information.
        Args:
            self: Internal value used in button and value tracking.

        Returns: Button status and value passed in.

        """
        return (self.button, self.values)

    def add_windowLabel(self, text='Please enter your System Information'):
        """
        Diag. box information for the layout.
        Args:
            text: Text box to display in layout.
        Returns:
        """
        self.layout.append([PySimpleGUI.Text(text)])
        return

    def add_selectDropDown(self, selectionList=None, size=(20, 3)):
        """
        Drop down menu example
        Args:
            selectionList: List of selection string options.
            size: Box size information.
        Returns: None
        """
        if selectionList is None:
            selectionList = ['Default', 'Ubuntu', 'Windows']
        self.layout.append([PySimpleGUI.InputCombo(selectionList, size=size)])
        return

    def add_selectFolder(self, text='Choose Content Folder', setupBox=('_' * 80), size=(35, 1)):
        """
        Selection to choose a local folder for a given operation.
        Args:
            text: Text box to display to user.
            setupBox: Horizontal line breaking text.
            size: Textbox size information.
        Returns: None
        """
        self.layout.append([[PySimpleGUI.Text(setupBox)], [PySimpleGUI.Text(text, size=size)]])
        return

    def add_typeTextBox(self, text='Please provide feedback based on experience', size=(35, 3)):
        """
        Add a text input box to the application.
        Args:
            text: Text box to let user be aware of the input intent.
            size: Text box size
        Returns: None
        """
        self.layout.append([PySimpleGUI.Multiline(default_text=text, size=size)])
        return

    def add_buttons(self):
        """
        Submit and cancel button for a layout.
        Returns: None
        """
        self.layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        'return'

    def display_windowInput(self):
        """
        Display the layout composed.
        Returns: None
        """
        self.windowActive = PySimpleGUI.Window(self.label, self.layout)

    def read_window(self):
        """
        Reads the active window.
        Returns: None
        """
        (self.button, self.values) = self.windowActive.read()
        return self.button, self.values

    def setAppearance(self, color='LightBlue'):
        """
        Method to set the color and feel of the layout.
        Args:
            color: Selected color from list.
        Returns: None
        """
        if color in self.get_tableOptions():
            PySimpleGUI.ChangeLookAndFeel(color)
            self.LookFeelStatus = True
        return self.LookFeelStatus

    def getMenu(self):
        """
        Gets the default menu selection.
        Returns: None
        """
        if self.menu_def is None:
            menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                        ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                        ['&Help', '&About...'], ]
        else:
            menu_def = self.menu_def
        return menu_def

    def getProgramLabel(self):
        """
        Gets the default label for the program.
        Returns: None
        """
        if self.programLabel is None:
            programLabel = ''.join(
                'Rapid Automation-Analysis for Developers (RAAD), '
                'by Prof. Joseph Tarango, '
            )
        else:
            programLabel = self.programLabel
        if self.debug:
            print(programLabel)
        return programLabel

    @staticmethod
    def check_flag(flag):
        """
        function for checking the value of a yes/no drop-down and returning the boolean value associated with
        the answer

        Args:
            flag: string representation of Yes/No option

        Returns:
    8                   booleanFlag: Boolean value for selected option ("Yes" = True, "No" = False)
        """
        booleanFlag = False
        if flag == "Yes":
            booleanFlag = True
        elif flag == "No":
            booleanFlag = False

        return booleanFlag

    @staticmethod
    def word(wordWidth=10):
        """
        Random word creator
        Args:
            wordWidth: Word length.
        Returns: String generated word.
        """
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(wordWidth))

    @staticmethod
    def number(max_val=4):
        """
        Generation of random numbers.
        Args:
            max_val: Total values to generate

        Returns: Random number vector.
        """
        startVal = 0
        return random.randint(startVal, max_val)

    def make_table(self, num_rows=1, num_cols=1):
        """
        Generation of tables.
        Args:
            num_rows: Number of rows to generate.
            num_cols: Number of columns to generate
        Returns: None
        """
        dataCreate = [[j for j in range(num_cols)] for _ in range(num_rows)]
        dataCreate[0] = (["uid", "Object Name"] + ["t_" + str(i) for i in range(num_cols - 2)])
        for i in range(1, num_rows):
            dataCreate[i] = [self.word(), *[self.number() for i in range(num_cols - 1)]]
        return dataCreate

    def updateTimeStamp(self):
        self.timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

    def loadAndProbeDrive(self, collect_values):
        inputFile = collect_values['data.drive.workload']
        driveNumber = collect_values['data.drive.number']
        driveName = collect_values['data.drive.name']
        identifier = collect_values['data.drive.identifier']
        outputDir = collect_values['data.drive.output']
        parseFlag = collect_values['data.drive.parse']
        volumeLabel = collect_values['data.drive.volumeLabel']
        volumeAllocUnit = collect_values['data.drive.volumeAllocUnit']
        volumeFS = collect_values['data.drive.volumeFS']
        volumeLetter = collect_values['data.drive.volumeLetter']
        partitionStyle = collect_values['data.drive.partitionStyle']
        partitionFlag = collect_values['data.drive.partition']
        prepFlag = collect_values['data.drive.prep']

        if parseFlag == 'Yes':
            parse = True
        else:
            parse = False

        if partitionFlag == 'Yes':
            partition = True
        else:
            partition = False

        if prepFlag == 'Yes':
            prep = True
        else:
            prep = False

        LS = src.software.TSV.loadAndProbeSystem.loadSystem(inputFile, driveNumber, driveName, identifier, outputDir,
                                                            self.debug)
        LS.loadSystemAPI(parse=parse, volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit, volumeFS=volumeFS,
                         volumeLetter=volumeLetter, partitionStyle=partitionStyle, partitionFlag=partition,
                         prepFlag=prep)

    def gatherTelemetryData(self, collect_values):
        """
        Reaction to pressing the Gather Data button on the gui. That button press kicks off a series of three major actions:
            1. Query and aggregate telemetry from the chosen SSD
            2. Format data into .ini and .txt files
            3. Package remaining data files into a compressed format and clean up the directory
        Args:
            collect_values: Array containing the user inputs from the graphical interface
        """
        # Gather import for gathering binaries
        GTSB = src.software.TSV.generateTSBinaries
        FTSF = src.software.TSV.formatTSFiles
        # PI = software.axon.packageInterface
        print("successfully imported")

        defaultFolderInput = tryFolder(path=self.location)
        defaultParserInput = tryFolder(path=self.locationAutoParse)
        defaultNlogInput = tryFolder(path=self.locationNlogParse)

        # Get common time stamps on files
        self.updateTimeStamp()

        # Define most recent data file name
        self.dataFileName = (''.join(['time-series_', str(self.timeStamp), '.ini']))
        dataFilePath = defaultFolderInput

        # Argument Dictionaries to translate bad inputs
        Classargs = dict(iterations=1, outpath=defaultFolderInput)
        APIargs = dict(mode='PARSE', time=2, driveNumber='1', inputFolder=defaultFolderInput)
        Formatargs = dict(fwDir=defaultParserInput, binDir=defaultFolderInput, outfile=self.dataFileName,
                          nlogFolder=defaultNlogInput, obj=None, mode=2)

        # Gather parameters for the gathering API
        try:
            # Get which flavor of telemetry the user wants to gather
            if collect_values['data.collect.toolChoice'] != '':
                APIargs["mode"] = self.modeTranslate[collect_values['data.collect.toolChoice']]

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
                self.locationAutoParse = collect_values['data.collect.fwParsers']

            # Gather directory to find directory for firmware parsers
            if collect_values['data.collect.nlogParsers'] != '':
                Formatargs["nlogFolder"] = collect_values['data.collect.nlogParsers']
                self.locationNlogParse = collect_values['data.collect.nlogParsers']

            # Gather directory to output files used
            if collect_values['data.collect.workingDirOutput'] != '':
                Classargs["outpath"] = collect_values['data.collect.workingDirOutput']
                Formatargs["binDir"] = collect_values['data.collect.workingDirOutput']
                self.binLocation = collect_values['data.collect.workingDirOutput']

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
        self.gen = GTSB.generateTSBinaries(**{key: inputVector for key, inputVector in Classargs.items() if (inputVector is not None)})
        self.parseList, self.binList = self.gen.generateTSBinariesAPI(**{key: inputVector for key, inputVector in APIargs.items() if (inputVector is not None)})

        # Add list of binaries returned from generate to format
        Formatargs["binList"] = self.binList
        Formatargs["debug"] = self.debug
        Formatargs["timeStamp"] = self.timeStamp

        # Format files into .txt and .ini formats
        self.form = FTSF.formatTSFiles(outpath=Classargs["outpath"], debug=self.debug)
        self.form.formatTSFilesAPI(**{key: inputVector for key, inputVector in Formatargs.items() if (inputVector is not None)})
        # fwDir=None, binDir="binaries", outfile="time-series.ini", obj=None, mode=1,binList=None
        # Grab path to data file and it should exist
        try:
            dataFilePath = Classargs["outpath"]
        except KeyError:
            print("Error in getting path for data file")

        if os.path.exists(os.path.join(dataFilePath, self.dataFileName)):
            self.dataFile = os.path.join(dataFilePath, self.dataFileName)

        # Compress created files
        self.zipName = "GatherData_" + self.timeStamp + ".zip"
        self.zipFile = src.software.axon.packageInterface.packageInterface(absPath=dataFilePath,
                                                                           timeSeriesFile=self.dataFile,
                                                                           debug=self.debug).createZIP(zipFileName=self.zipName)

        # Store name of fully compressed directory
        self.contentFile = self.zipName

        return self.dataFileName

    def refreshMetaTable(self):
        """
        refresh data in Meta Data Table in Graphical Interface
        """
        telemetryFeature = None
        # Check if there is no data file to pull data from
        if self.dataFile is None:
            dataFile = r"/home/lab/gui_tests/test_gui/test3/time-series.ini"
        else:
            dataFile = self.dataFile

        # Pull data file and store in a dictionary
        dataDictionary = DP.preprocessingAPI().loadDataDict(dataFile)

        # Initialize 2D array for meta data table
        dataTable = [["Telemetry Object", "Telemetry Feature"]]

        # Traverse dictionary and populate the table
        maxLen = 0  # Error catching for if any one time series is longer than the others
        # For each telemetry object pulled by telemetry
        for telemetryObject in dataDictionary:
            try:
                # For each feature in the telemetry object
                for telemetryFeature in dataDictionary[telemetryObject]:
                    try:
                        # Checkthe keys that were pulled point to the time series array
                        if not isinstance(dataDictionary[telemetryObject][telemetryFeature], list):
                            if self.debug:
                                ("Not Instance: [{0}][{1}] <== {2}".format(telemetryObject, telemetryFeature, dataDictionary[telemetryObject][telemetryFeature]))
                            continue

                        # Update length so table has the same length
                        if len(dataDictionary[telemetryObject][telemetryFeature]) > maxLen:
                            maxLen = len(dataDictionary[telemetryObject][telemetryFeature])

                        # Add line to the table
                        dataTable.append(
                            [telemetryObject, telemetryFeature] + dataDictionary[telemetryObject][telemetryFeature])

                    except KeyError:
                        print("Nested Key Error with keys: ", telemetryObject, " and ", telemetryFeature)
                        continue

            except KeyError:
                print("Outside Key Error with key: ", telemetryObject)
                continue

            except TypeError:
                print("Weird concat at: ", telemetryObject, " --- ", telemetryFeature, " --- ",
                      dataDictionary[telemetryObject][telemetryFeature])
                exit(1)

        # self.windowActive.Element('data.table.telemetryDataTable').Widget.setHorizontalHeaderLabels(dataTable[0])
        self.windowActive.Element('data.table.telemetryDataTable').ColumnHeadings = dataTable[0]
        self.windowActive.Element('data.table.telemetryDataTable').Update(values=dataTable[1:])

        return dataTable

    @staticmethod
    def getDataAsArray(DataDic, chosenKey="all", oneShot=False):
        # Initialize 2D array for meta data table
        if not oneShot:
            dataTable = [
                ["Telemetry Object", "Telemetry Feature"]
            ]
        else:
            dataTable = {}
        # dataTable = [["Telemetry Object", "Telemetry Feature"]]

        # Initialize headings
        headings = []

        # Traverse dictionary and populate the table
        # For each telemetry object pulled by telemetry
        for telemetryObject in DataDic:
            print("telemetryObject: ", telemetryObject)
            if telemetryObject == chosenKey or DataDic[telemetryObject]["name"] == chosenKey or chosenKey == "all":
                try:
                    # For each feature in the telemetry object
                    for telemetryFeature in DataDic[telemetryObject]:
                        print("telemetryFeature: ", telemetryFeature)
                        try:
                            # Check the keys that were pulled point to the time series array
                            # if not isinstance(DataDic[telemetryObject][telemetryFeature], list):
                            #     if self.debug:
                            #         ("Not Instance: [{0}][{1}] <== {2}".format(telemetryObject, telemetryFeature, dataDictionary[telemetryObject][telemetryFeature]))
                            #     continue
                            if not oneShot:
                                # Add line to the table
                                dataTable.append(
                                    [DataDic[telemetryObject]['name'], telemetryFeature] + DataDic[telemetryObject][
                                        telemetryFeature])
                            else:
                                try:
                                    dataTable[DataDic[telemetryObject]['name']].append(
                                        [DataDic[telemetryObject]['name'], telemetryFeature] + DataDic[telemetryObject][
                                            telemetryFeature]
                                    )
                                except KeyError:
                                    dataTable[DataDic[telemetryObject]['name']] = [
                                        [DataDic[telemetryObject]['name'], telemetryFeature] + DataDic[telemetryObject][
                                            telemetryFeature]
                                    ]

                            # print([telemetryObject, telemetryFeature] + DataDic[telemetryObject][telemetryFeature])

                            # Add time tag to headings
                            if len(headings) == 0:
                                headings = ["t_" + str(i) for i in range(len(DataDic[telemetryObject][telemetryFeature]))]

                        except KeyError as errorLocalOne:
                            print("Nested Key Error with keys: ", telemetryObject, " and ", telemetryFeature)
                            print("Error: ", errorLocalOne)

                        except TypeError as errorLocalTwo:
                            print("Weird concat at: ", telemetryObject, " --- ", telemetryFeature, " --- ",
                                  DataDic[telemetryObject][telemetryFeature])
                            print("TypeError: ", errorLocalTwo)

                except KeyError as errorLocalThree:
                    print("Outside Key Error with key: ", telemetryObject)
                    print("Error: ", errorLocalThree)

        if oneShot:
            for key in dataTable:
                dataTable[key] = [["Telemetry Object", "Telemetry Feature"] + headings] + dataTable[key]
            print("OneShot DataDic: ", DataDic)
            print("OneShot dataTable: ", dataTable)
        else:
            # Add headings
            dataTable[0] = dataTable[0] + headings
            print("DataDic: ", DataDic)
            print("dataTable: ", dataTable)

        return dataTable

    @staticmethod
    def getDataDic(dataFile):
        return DP.preprocessingAPI().loadDataDict(dataFile)

    @staticmethod
    def popupTableLayout(dataArray, headings):
        print("dataArray: ", dataArray[1:])
        print("headings: ", headings)
        pTable = [[PySimpleGUI.Column([[PySimpleGUI.Table(values=dataArray[1:][:],
                                                          headings=headings,
                                                          auto_size_columns=True,
                                                          background_color='lightblue',
                                                          display_row_numbers=True,
                                                          num_rows=40,
                                                          justification='right',
                                                          alternating_row_color='lightgreen',
                                                          vertical_scroll_only=True,
                                                          key='-TABLE-',
                                                          tooltip='Telemetry Data Table')]],
                                      scrollable=True,
                                      size=(800, 500))],
                  [PySimpleGUI.Button('Cancel')]
                  ]
        return pTable

    def popupTable(self, dataArray, programLabel, returnLayout=False):
        # print("Data array: ", dataArray)
        # Get heading for the table
        headings = [str(dataArray[0][x]) for x in range(len(dataArray[0]))]
        print("headings: ", headings)

        # Get the layout for the data table
        tableLayout = self.popupTableLayout(dataArray, headings)

        if returnLayout:
            return tableLayout

        tableWindow = PySimpleGUI.Window(programLabel, tableLayout)

        repeatEventLoop = True
        while repeatEventLoop:
            (collect_button, collect_values) = tableWindow.read()

            if collect_button == PySimpleGUI.WIN_CLOSED or collect_button == 'Cancel':
                repeatEventLoop = False

        # Close the spawned window
        tableWindow.close()

    def trackAXONUpload(self, axonID=0, metaData=None, axonFile='.raadProfile/axonProfile.ini'):
        """
        Function to pull in/create a hidden file in the current working directory and pull information about previously uploaded AXON records.
            Creates a file called .raadProfile/axonProfile.ini and stores metadata for each upload based on the metadata uploaded to AXON
        Returns:
            None
        """
        axonFile = os.path.abspath(os.path.join(os.getcwd(), axonFile))
        if self.debug:
            print(f"Axon file: {axonFile}")
        # # Instantiate profile for AXON
        profile = src.software.axon.axonProfile.AxonProfile()

        # Open and setup config parser for file
        profile.GetProfile(axonFile)

        # Populate the profile meta
        if metaData is not None:
            profile.AddSection(entry=metaData, ID=axonID)

        # Write config to file
        profile.SaveProfile(axonFile)
        return

    def GUIUpload(self, contentFile=None, mode="test", analysisReport=None):

        # First check telemetry pull has been executed at all and is there a recent telemtry pull to upload
        if self.contentFile is None:
            print("ERROR: No telemetry pull currently present for upload")
            return False, 0
        # Instantiate class for axon upload
        axonInt = src.software.axon.axonInterface.Axon_Interface(mode=mode)
        # Create metadats file for AXON upload
        metaData, metaDataFile = self.formMetaData(axonInt=axonInt, contentFile=contentFile)
        # Create metadats file for AXON upload
        success, axonID = axonInt.sendInfo(metaDataFile=metaDataFile, contentFile=contentFile)

        # Print return of Axon Upload
        if success:
            print("AXON Upload Successful!!! Returned AXON ID is ", axonID)
            self.axonID = axonID
            # Track AXON uploads in hidden file in central directory
            self.trackAXONUpload(axonID=axonID, metaData=metaData)
            if analysisReport is not None:
                analysisReport.setDataLakeMeta(axonID,
                                               axonURL=axonInt.GetURL(),
                                               MetaDataFile=metaDataFile,
                                               UploadedFile=contentFile)

        return success, axonID

    @staticmethod
    def GUIDownload(axonID, outputDirectory, mode="test", analysisReport=None):
        axonInt = src.software.axon.axonInterface.Axon_Interface(mode=mode)

        if outputDirectory is None:
            exitCode, cmdOutput, cmdError = axonInt.receiveCmd(axonID)
        else:
            exitCode, cmdOutput, cmdError = axonInt.receiveCmd(axonID, outputDirectory)

        print("Exit code returned from AXON download: ", exitCode)

        if exitCode == 0:
            success = axonInt.validateDownload(outputDirectory, axonID)
        else:
            success = False

        CommandOutput = {
            "success": success,
            "axonID": axonID,
            "downloadDirectory": os.path.join(outputDirectory, axonID),
            "exitCode": exitCode,
            "cmdOutput": cmdOutput,
            "cmdError": cmdError
        }

        print("analysisReport: ", analysisReport)
        if success and analysisReport is not None:
            metaDataFile = os.path.join(outputDirectory, axonID, "record-intel-driveinfo-json-v1.json")
            uploadFile = os.path.join(outputDirectory, axonID, "intel-driveinfo-zip-v1.zip")
            analysisReport.setDataLakeMeta(axonID, axonURL=axonInt.GetURL(), MetaDataFile=metaDataFile, UploadedFile=uploadFile)

        return CommandOutput

    @staticmethod
    def hostMetaData():
        """
        Get MetaData that has to do with who is retrieving the information
        Returns:
            dict[str: str] hostMeta: Contains the fields for host-specific data
        """
        # This dictionary holds all host-specific metadata and is updated with the corrollary fields
        hostMeta = dict()

        # Add field for the timestamp of the AXON upload
        hostMeta["timeStamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S:%f")  # Uses same format as given in axonMeta.py

        # Add field for the host username that is requesting the upload
        hostMeta["host"] = getpass.getuser()

        return hostMeta

    def formMetaData(self, axonInt, contentFile):
        """
        Creates metadata file for AXON upload
        Args:
        axonInt:
        contentFile:

        Returns: Path to MetaData file used for AXON upload

        """
        # collect_values: Array containing the user inputs from the graphical interface
        # Instantiate dictionary for metadata entries
        metaData = dict()

        # Populate Metadata with data from drive
        metaData.update(src.software.access.DriveInfo.DriveInfo().DriveInfoAPI())

        # Gather host specific metadata
        metaData.update(self.hostMetaData())

        # Create finished metadata file
        metaFile = axonInt.createContentsMetaData(metaData, contentFile)

        return metaData, metaFile

    def downloadAXONData(self):
        """
        Spawns new window to get information and then performs a download from the AXON database
        Returns:

        """

        # Create window for all information about
        self.downloadWindow = self.spawnAxonDownloadWindow()

        # Simple loop for user to input information
        while True:
            # Read from window
            event, values = self.downloadWindow.read()
            print("values: ", values)

            if event == PySimpleGUI.WIN_CLOSED:
                print("Cancelling...")
                break

            elif event == 'Cancel':
                print("Cancelling...")
                break

            elif event == 'Start Download':
                print(event, values)

                # Kick off download from AXON
                self.sendAXONDownloadCommand()
                break

            elif event == 'Refresh Info':
                print(event, values)

                # Populate info on window

        # Close the window we opened
        self.downloadWindow.close()

    def spawnAxonDownloadWindow(self):

        axonIDs = self.getAXONIDs()
        if axonIDs is None:
            print("Creating popup window has failed")

        layout = [
            [
                PySimpleGUI.Text('Download from AXON with ', auto_size_text=False),
                PySimpleGUI.InputCombo(axonIDs,
                                       key='axon.download.axonID',
                                       default_value=axonIDs[0],
                                       tooltip='')
            ],
            [
                PySimpleGUI.Button('Start Download', button_color=('black', 'lightblue')),
                PySimpleGUI.Button('Refresh Info', button_color=('black', 'lightgreen')),
                PySimpleGUI.Button('Cancel', button_color=('black', 'pink'))
            ],
        ]
        return PySimpleGUI.Window(title="AXON Download", layout=layout, resizable=True, auto_size_text=True,
                                  auto_size_buttons=True)

    def sendAXONDownloadCommand(self):
        """

        Returns:

        """
        return

    @staticmethod
    def getAXONIDs():
        """
        Gather a dictionary for details of previous AXON uploads
        Returns:
            axonList: list of python dictionaries that contain relevant details of previous axon uploads
                The dictionary follow this format: [{"descriptor": "value", ...}, ...]
        """
        return ["1234", "4444", "69420"]

    @staticmethod
    def display_dir_ARMA(window, objectFile, currentObject):
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
        window['Predictor.ARMA.field'].Update(value=trackingVars[0], values=trackingVars)

    @staticmethod
    def populate_object_ARMA(window, dirPath):
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
        objectFile = src.software.guiCommon.ObjectConfigARMA(str(dirPath))
        mep = objectFile.readConfigContent()
        dataKeys = ["None"] + list(objectFile.dataDict.keys())
        window["Predictor.ARMA.object"].Update(values=dataKeys)
        return mep, objectFile

    @staticmethod
    def create_new_graph_window_ARMA(values, mep, currentObject, pdf=None):
        """
        function for generating a new graph window using the matplot functionality of PySimpleGUI

        Args:
            values: List of values collected from window
            mep: MediaErrorPredictor instance
            currentObject: String for the name of the current object
            pdf: Instance of the PDF file descriptor where the graphs will be stored. If pdf==None, the plots will be
            directly displayed to the screen

        Returns:

        """

        subSeqLen = int(values["Predictor.ARMA.ssl"])
        matrixProfile = values['Predictor.ARMA.matrix']
        currentField = values['Predictor.ARMA.field']
        matrixProfileFlag = False
        if matrixProfile == "Yes":
            matrixProfileFlag = True
        elif matrixProfile == "No":
            matrixProfileFlag = False

        mep.setMatrixProfileFlag(matrixProfileFlag, subSeqLen=subSeqLen)
        mep.ARMAModel(currentObject=currentObject, currentField=currentField, pdf=pdf)
        return

    @staticmethod
    def display_dir_RNN(window, objectFile, currentObject, primaryVarLabelsRNN, secondaryVarLabelsRNN):
        """
        function for updating the values contained in the drop down menus for primary and secondary variables

        Args:
            window: window instance
            objectFile: ObjectConfig instance
            currentObject: String for the name of the current object
            primaryVarLabelsRNN: List of strings identifiers for the variable fields used as inputs in the RNN
            secondaryVarLabelsRNN: List of strings identifiers for the variable fields to be plotted

        Returns:

        """
        try:
            if objectFile.objectIDs[0] == "MEDIA_MADNESS":
                trackingVars = objectFile.columns
                primaryVars = ["None"] + list(trackingVars)
                secondaryVars = ["None"] + list(trackingVars)
                for name in primaryVarLabelsRNN:
                    window[name].Update(value=primaryVars[0], values=primaryVars)
                for name in secondaryVarLabelsRNN:
                    window[name].Update(value=secondaryVars[0], values=secondaryVars)
            else:
                trackingVars = objectFile.dataDict[currentObject].keys()
                primaryVars = ["None"] + list(trackingVars)
                secondaryVars = ["None"] + list(trackingVars)
                for name in primaryVarLabelsRNN:
                    window[name].Update(value=primaryVars[0], values=primaryVars)
                for name in secondaryVarLabelsRNN:
                    window[name].Update(value=secondaryVars[0], values=secondaryVars)
        except BaseException as ExceptionContext:
            pprint.pprint(whoami())
            print(ExceptionContext)
            pass

    @staticmethod
    def populate_object_RNN(window, dirPath):
        """
        function for populating the ObjectConfig instance and updating the drop down menu for the objects
        available in the configuration file

        Args:
            window: window instance
            dirPath: String for the path to the configuration file

        Returns:
            rnn: mediaPredictionRNN instance
            objectFile: ObjectConfig instance
            objectList: list of object names (ex. ThermalSensor)
        """
        objectFile = src.software.guiCommon.ObjectConfigRNN(str(dirPath))
        rnn = objectFile.readConfigContent(debug=True)
        objectList = list(objectFile.objectIDs)
        window["Predictor.RNN.object"].Update(values=objectList)
        return rnn, objectFile, objectList

    def create_new_graph_window_RNN(self, values, rnn, currentObject, primaryVarLabelsRNN, secondaryVarLabelsRNN):
        """
        function for generating a new graph window using the matplot functionality of PySimpleGUI

        Args:
            values: List of values collected from window
            rnn: mediaPredictionRNN instance
            currentObject: String for the name of the current object (ex. uid-6)
            primaryVarLabelsRNN:List of strings identifiers for the variable fields used as inputs in the RNN
            secondaryVarLabelsRNN: List of strings identifiers for the variable fields to be plotted

        Returns:

        """
        trackingVars = []
        plotVars = []

        for nameVar in primaryVarLabelsRNN:
            if values[nameVar] != "None":
                trackingVars.append(values[nameVar])

        for nameVar in secondaryVarLabelsRNN:
            if values[nameVar] != "None":
                plotVars.append(values[nameVar])

        if (len(trackingVars) > 0):
            inputWidth = int(values['Predictor.RNN.inputWidth'])
            labelWidth = int(values['Predictor.RNN.labelWidth'])
            shift = int(values['Predictor.RNN.shift'])
            hiddenLayers = int(values['Predictor.RNN.hiddenLayers'])
            subSeqLen = int(values['Predictor.RNN.ssl'])
            batchSize = int(values['Predictor.RNN.batchSize'])
            maxEpochs = int(values['Predictor.RNN.maxEpochs'])
            matrixProfile = values['Predictor.RNN.matrix']
            embeddedEncoding = values['Predictor.RNN.embedded']
            categoricalEncoding = values['Predictor.RNN.categorical']
            optimizer = values['Predictor.RNN.optimizer']
            lstm_activation = values['Predictor.RNN.lstm_activation']
            dense_activation = values['Predictor.RNN.dense_activation']
            lstm_initializer = values['Predictor.RNN.lstm_initializer']
            dense_initializer = values['Predictor.RNN.dense_initializer']
            dropout = values['Predictor.RNN.dropout']
            dropout = self.check_flag(dropout)
            matrixProfileFlag = self.check_flag(matrixProfile)
            embeddedEncodingFlag = self.check_flag(embeddedEncoding)
            categoricalEncodingFlag = self.check_flag(categoricalEncoding)

            rnn.setMatrixProfile(value=matrixProfileFlag, subSeqLen=subSeqLen)
            rnn.setEmbeddedEncoding(value=embeddedEncodingFlag)
            rnn.setCategoricalEncoding(value=categoricalEncodingFlag)
            rnn.timeSeriesPredictorAPI(inputWidth, labelWidth, shift, batchSize, hiddenLayers, currentObject,
                                       trackingVars, plotVars[0], maxEpochs, optimizer=optimizer,
                                       lstm_activation=lstm_activation, lstm_initializer=lstm_initializer,
                                       dense_activation=dense_activation, dense_initializer=dense_initializer,
                                       dropout=dropout)

    def execute_nlog_predictor(self, values):
        """
        function for executing the standard NLOG predictor. Access tot he terminal output is required to see the results

        Args:
            values: List of values collected from window

        Returns:

        """

        nlogFolder = values['Predictor.NLOG.nlogFolder']
        nlogParserFolder = values['Predictor.NLOG.nlogParserFolder']
        numComponents = int(values['Predictor.NLOG.numComponents'])
        maxNumParams = int(values['Predictor.NLOG.maxNumParams'])
        inputSize = int(values['Predictor.NLOG.inputSize'])
        maxOutputSize = int(values['Predictor.NLOG.maxOutputSize'])
        widthModelType = values['Predictor.NLOG.widthModelType']
        timeHiddenUnits = int(values['Predictor.NLOG.timeHiddenUnits'])
        eventsHiddenUnits = int(values['Predictor.NLOG.eventsHiddenUnits'])
        paramsHiddenUnits = int(values['Predictor.NLOG.paramsHiddenUnits'])
        timeMaxEpochs = int(values['Predictor.NLOG.timeMaxEpochs'])
        eventsMaxEpochs = int(values['Predictor.NLOG.eventsMaxEpochs'])
        paramsMaxEpochs = int(values['Predictor.NLOG.paramsMaxEpochs'])
        timeOptimizer = values['Predictor.NLOG.timeOptimizer']
        eventsOptimizer = values['Predictor.NLOG.eventsOptimizer']
        paramsOptimizer = values['Predictor.NLOG.paramsOptimizer']
        timeLstmActivation = values['Predictor.NLOG.timeLstmActivation']
        eventsLstmActivation = values['Predictor.NLOG.eventsLstmActivation']
        paramsLstmActivation = values['Predictor.NLOG.paramsLstmActivation']
        timeLstmInitializer = values['Predictor.NLOG.timeLstmInitializer']
        eventsLstmInitializer = values['Predictor.NLOG.eventsLstmInitializer']
        paramsLstmInitializer = values['Predictor.NLOG.paramsLstmInitializer']
        timeDropout = values['Predictor.NLOG.timeDropout']
        timeDropout = self.check_flag(timeDropout)
        eventsDropout = values['Predictor.NLOG.eventsDropout']
        eventsDropout = self.check_flag(eventsDropout)
        paramsDropout = values['Predictor.NLOG.paramsDropout']
        paramsDropout = self.check_flag(paramsDropout)

        nlogPredictor = nlogPrediction.NlogPredictor(nlogFolder=nlogFolder, nlogParserFolder=nlogParserFolder,
                                                     numComponents=numComponents, maxNumParams=maxNumParams,
                                                     inputSize=inputSize, maxOutputSize=maxOutputSize)

        nlogPredictor.nlogPredictorAPI(widthModelType=widthModelType, timeHiddenUnits=timeHiddenUnits,
                                       timeMaxEpochs=timeMaxEpochs, timeOptimizer=timeOptimizer,
                                       timeLstmActivation=timeLstmActivation, timeLstmInitializer=timeLstmInitializer,
                                       timeDropout=timeDropout, eventsHiddenUnits=eventsHiddenUnits,
                                       eventsMaxEpochs=eventsMaxEpochs, eventsOptimizer=eventsOptimizer,
                                       eventsLstmActivation=eventsLstmActivation,
                                       eventsLstmInitializer=eventsLstmInitializer, eventsDropout=eventsDropout,
                                       paramsHiddenUnits=paramsHiddenUnits, paramsMaxEpochs=paramsMaxEpochs,
                                       paramsOptimizer=paramsOptimizer, paramsLstmActivation=paramsLstmActivation,
                                       paramsLstmInitializer=paramsLstmInitializer, paramsDropout=paramsDropout)

    @staticmethod
    def display_dir_generic_object(window, objectFile, currentObject, primaryVarLabelsGenericObject, secondaryVarLabelsGenericObject):
        """
        function for updating the values contained in the drop down menus for primary and secondary variables

        Args:
            window: window instance
            objectFile: ObjectConfig instance
            currentObject: String for the name of the current object (ex. uid-6)
            primaryVarLabelsGenericObject: String identifier for the fields in the GUI that contains the variable names
            to be plotted in the main axis of the graph
            secondaryVarLabelsGenericObject:String identifier for the fields in the GUI that contains the variable names
            to be plotted in the secondary axis of the graph

        Returns:

        """
        trackingVars = objectFile.vizDict[currentObject].keys()
        primaryVars = ["None"] + list(trackingVars)
        secondaryVars = ["None"] + list(trackingVars)
        for name in primaryVarLabelsGenericObject:
            window[name].Update(value=primaryVars[0], values=primaryVars)
        for name in secondaryVarLabelsGenericObject:
            window[name].Update(value=secondaryVars[0], values=secondaryVars)

    @staticmethod
    def populate_object_generic_object(window, dirPath):
        """
        function for populating the ObjectConfig instance and updating the drop down menu for the objects
        available in the configuration file

        Args:
            window: window instance
            dirPath: String for the path to the configuration file

        Returns:
            vts: visualizeTS instance
            objectFile: ObjectConfig instance
            objectNamesDict: Dictionary of object identifiers (ex. uid-6) to object names (ex. ThermalSensor)
        """
        vts = None
        objectFile = None
        objectNamesDict = None
        try:
            objectFile = src.software.guiCommon.ObjectConfigGenericObject(str(dirPath))
            vts = objectFile.readConfigContent()
            objectList = list(objectFile.objectIDs)
            objectNamesDict = {}
            for key in objectList:
                currentObject = "uid-" + key
                currentName = objectFile.vizDict[currentObject]["name"]
                objectNamesDict[currentName] = key
            window["data.telemetry.genericObject.metadata.timeseries.object"].Update(values=list(objectNamesDict.keys()))
        except BaseException as ExceptionContext:
            pprint.pprint(whoami())
            print(ExceptionContext)
            pass
        return vts, objectFile, objectNamesDict

    @staticmethod
    def create_new_graph_window_generic_object(values, vts, objectFile, currentObject, primaryVarLabelsGenericObject, secondaryVarLabelsGenericObject):
        """
        function for generating a new graph window using the matplot functionality of PySimpleGUI

        Args:
            values: List of values collected from window
            vts: visualizeTS instance
            objectFile: ObjectConfig instance
            currentObject: String for the name of the current object (ex. uid-6)
            primaryVarLabelsGenericObject:String identifier for the fields in the GUI that contains the variable names
            to be plotted in the main axis of the graph
            secondaryVarLabelsGenericObject:String identifier for the fields in the GUI that contains the variable names
            to be plotted in the secondary axis of the graph

        Returns:

        """
        trackingVars = []
        secondaryVars = []

        for name in primaryVarLabelsGenericObject:
            if values[name] != "None":
                trackingVars.append(values[name])

        for name in secondaryVarLabelsGenericObject:
            if values[name] != "None":
                secondaryVars.append(values[name])

        if (len(trackingVars) > 0):
            currentObjects = [currentObject.strip("uid-")]
            print(str(currentObjects))
            dataDict = objectFile.vizDict
            start = values['data.telemetry.genericObject.metadata.timeseries.start']
            end = values['data.telemetry.genericObject.metadata.timeseries.end']
            matrixProfile = values['data.telemetry.genericObject.metadata.timeseries.matrix']
            pdfStrOption = values['data.telemetry.genericObject.metadata.timeseries.pdf']
            outpath = values['data.telemetry.genericObject.metadata.timeseries.output']

            matrixProfileFlag = False
            if matrixProfile == "Yes":
                matrixProfileFlag = True
            elif matrixProfile == "No":
                matrixProfileFlag = False

            pdfOption = False
            if pdfStrOption == "Yes":
                pdfOption = True
            elif pdfStrOption == "No":
                pdfOption = False

            unionFields = trackingVars + secondaryVars
            if matrixProfileFlag:
                dataDict = vts.generateMP(dataDict, obj=currentObjects, fields=unionFields, subSeqLen=20,
                                          visualizeAllObj=False, visualizeAllFields=False)
            if pdfOption is False:
                vts.generateTSVisualizationGUI(currentObject, dataDict[currentObject], trackingVars, secondaryVars,
                                               start, end)
            else:
                pdfFile = tryFolder(outpath) + "/time-series"
                vts.writeTSVisualizationToPDF(dataDict, obj=currentObjects, fields=unionFields, outfile=pdfFile)

    @staticmethod
    def display_dir_defrag(window, dirPath, mode, primaryVarLabelsDefragHistory, secondaryVarLabelsDefragHistory):
        """
        function for updating the values contained in the drop down menus for primary and secondary variables

        Args:
            window: window instance
            dirPath: String for the path to the configuration file
            mode: Integer for the mode of operation (1=ADP, 2=CDR)
            primaryVarLabelsDefragHistory: String identifier for the fields in the GUI that contains the variable names
            to be plotted in the main axis of the graph
            secondaryVarLabelsDefragHistory:String identifier for the fields in the GUI that contains the variable names
            to be plotted in the secondary axis of the graph

        Returns:
            dhg: DefragHistoryGrapher instance
            dhFile: DefragConfig instance

        """
        dhFile = src.software.guiCommon.DefragConfig(str(dirPath), mode)
        dhg = dhFile.readConfigContent()
        primaryVars = ["None"] + list(dhFile.trackingVars)
        secondaryVars = ["None"] + list(dhFile.secondaryVars)
        for name in primaryVarLabelsDefragHistory:
            window[name].Update(value=primaryVars[0], values=primaryVars)
        for name in secondaryVarLabelsDefragHistory:
            window[name].Update(value=secondaryVars[0], values=secondaryVars)
        return dhg, dhFile

    @staticmethod
    def create_new_graph_window_defrag(values, dhg, dhFile, setPointLabelsDict, primaryVarLabelsDefragHistory, secondaryVarLabelsDefragHistory):
        """
        function for generating a new graph window using the matplot functionality of PySimpleGUI

        Args:
            values: List of values collected from window
            dhg: DefragHistoryGrapher instance
            dhFile: DefragConfig instance
            setPointLabelsDict: List of window element names that that collect the setpoint values
            primaryVarLabelsDefragHistory: String identifier for the fields in the GUI that contains the variable names
            to be plotted in the main axis of the graph
            secondaryVarLabelsDefragHistory:String identifier for the fields in the GUI that contains the variable names
            to be plotted in the secondary axis of the graph

        Returns:

        """
        setPoints = []
        trackingVars = []
        secondaryVars = []
        for name in setPointLabelsDict.keys():
            if values[name] is True:
                setPoints.append(setPointLabelsDict[name])

        for name in primaryVarLabelsDefragHistory:
            if values[name] != "None":
                trackingVars.append(values[name])

        for name in secondaryVarLabelsDefragHistory:
            if values[name] != "None":
                secondaryVars.append(values[name])

        if (len(trackingVars) > 0):

            dhg.setSetPointNames(setPoints)
            dhg.setTrackingNames(trackingVars)
            dhg.setSecondaryVars(secondaryVars)

            dataDict = dhFile.vizDict
            object_t = "uid-41"
            numCores = values['data.telemetry.defragHistory.cores']
            bandwidth = values['data.telemetry.defragHistory.bandwidth']
            pdfStrOption = values['data.telemetry.defragHistory.pdf']
            outpath = values['data.telemetry.defragHistory.output']
            bandwidthFlag = False
            if bandwidth == "Yes":
                bandwidthFlag = True
            elif bandwidth == "No":
                bandwidthFlag = False

            pdfOption = False
            if pdfStrOption == "Yes":
                pdfOption = True
            elif pdfStrOption == "No":
                pdfOption = False
            driveName = values['data.telemetry.defragHistory.drive']
            start = values['data.telemetry.defragHistory.startPoint']
            end = values['data.telemetry.defragHistory.endPoint']
            if driveName == "ADP":
                if pdfOption is False:
                    dhg.generateTSVisualizationADP(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                   start=start, end=end)
                else:
                    pdfFile = tryFolder(outpath) + "/" + object_t + ".pdf"
                    with be.PdfPages(pdfFile) as pp:
                        dhg.generateTSVisualizationADP(object_t, dataDict, bandwidthFlag, numCores=numCores, pp=pp)
            elif driveName == "CDR":
                if pdfOption is False:
                    dhg.generateTSVisualizationCDR(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                   start=start, end=end)
                else:
                    pdfFile = tryFolder(outpath) + "/" + object_t + ".pdf"
                    with be.PdfPages(pdfFile) as pp:
                        dhg.generateTSVisualizationCDR(object_t, dataDict, bandwidthFlag, numCores=numCores, pp=pp)

    # noinspection PyTypeChecker
    def webAPI(self):
        PySimpleGUI.set_options(font=self.appFont, auto_size_text=True, auto_size_buttons=True)
        PySimpleGUI.ChangeLookAndFeel('DefaultNoMoreNagging')

        # Encase entire window in scrollable column
        layout = [
            ##################################
            # title.config.logo
            ##################################
            [PySimpleGUI.Text('Rapid Automation-Analysis for Developers (RAAD) powered by Machine Programming',
                              tooltip='RAAD Skynet AI systems,'
                                      'https://arxiv.org/abs/1803.07244', font=self.appFont,
                              key='title.config.RAADWeb', size=(111, 1))],
            [PySimpleGUI.Image(filename=self.logoLocation, size=(256, 300), key='title.config.logo')],
            [PySimpleGUI.Text('Hello Engineer, Below is general information.')],
            [PySimpleGUI.Text('System platform: {0}'.format(sys.platform))],
            [PySimpleGUI.Text('Location:'), PySimpleGUI.Text(str(self.baseFilePath), size=(len(self.baseFilePath), 1))],
            [PySimpleGUI.Text('Python Version:'), PySimpleGUI.Text(sys.version, size=(len(sys.version), 1))],
            [PySimpleGUI.Text(f'UTC Time: {self.timeStamp}')],
            ##################################
            # data.drive.load
            # data.drive.probe
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Load and Probe Drive for Data Collection', font=self.appFont)],
            [PySimpleGUI.Text('Drive Workload Configuration', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationInput),
                                   key='data.drive.workload'),
             PySimpleGUI.FileBrowse(initial_folder=str(self.locationInput), key=('data.drive.workload'))],
            [PySimpleGUI.Text('SSD Number', auto_size_text=False),
             PySimpleGUI.InputText(default_text='0', key='data.drive.number')],
            [PySimpleGUI.Text('SSD Name', auto_size_text=False),
             PySimpleGUI.InputText(default_text='/dev/nvme0n1', key='data.drive.name')],
            [PySimpleGUI.Text('Telemetry Pull Identifier', auto_size_text=False),
             PySimpleGUI.InputText(default_text='Tv2HiTAC', key='data.drive.identifier')],
            [PySimpleGUI.Text('Output directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationOutput), key='data.drive.output'),
             PySimpleGUI.FolderBrowse(initial_folder=str(self.locationOutput), key=('data.drive.output'))],
            [PySimpleGUI.Text('Volume Label (Windows Specific)', auto_size_text=False),
             PySimpleGUI.InputText(default_text='PERFTEST', key='data.drive.volumeLabel')],
            [PySimpleGUI.Text('Volume Allocation Unit (Windows Specific)', auto_size_text=False),
             PySimpleGUI.InputText(default_text='4096', key='data.drive.volumeAllocUnit')],
            [PySimpleGUI.Text('Volume File System (Windows Specific)', auto_size_text=False),
             PySimpleGUI.InputText(default_text='ntfs', key='data.drive.volumeFS')],
            [PySimpleGUI.Text('Volume Letter (Windows Specific)', auto_size_text=False),
             PySimpleGUI.InputText(default_text='G', key='data.drive.volumeLetter')],
            [PySimpleGUI.Text('Partition Style (Windows Specific)', auto_size_text=False),
             PySimpleGUI.InputText(default_text='mbr', key='data.drive.partitionStyle')],
            [PySimpleGUI.Text('Partition Drive (Windows Specific)?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='Yes', key='data.drive.partition',
                              enable_events=True)],
            [PySimpleGUI.Text('Prep Drive (Linux Specific)?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='Yes', key='data.drive.prep',
                              enable_events=True)],
            [PySimpleGUI.Text('Parse Binary Files?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='No', key='data.drive.parse',
                              enable_events=True)],
            [PySimpleGUI.Button('Load and Probe Drive', button_color=('white', 'purple'))],

            ##################################
            # data.collect
            # data.telemetry.decode
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Data Collect or Parse', font=self.appFont)],
            [PySimpleGUI.Text('Usage Case for Intel', auto_size_text=False),
             # PySimpleGUI.InputCombo(self.cGui.getVector('data.collect.toolChoice'))],
             PySimpleGUI.InputCombo(values=('PARSE', 'CLI', 'IMAS', 'TWIDL'),
                                    key='data.collect.toolChoice',
                                    default_value='PARSE',
                                    size=(7, 1),
                                    auto_size_text=False,
                                    tooltip='CLI is the NVMe-CLI Open Source Tool. TWIDL is the Intel internal tool. IMAS is the Intel Memory and Storage Tool')],
            [PySimpleGUI.Text('SSD Selection Name or Number', auto_size_text=False),
             PySimpleGUI.InputText(default_text='/dev/nvme0n1', key='data.collect.ssdChoice')],
            # PySimpleGUI.InputText(self.cGui.getVector('data.collect.ssdChoice'))],
            [PySimpleGUI.Text('Input directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationInput),
                                   key='data.collect.workingDirInput'),
             PySimpleGUI.FolderBrowse(initial_folder=str(self.locationInput),
                                      key=('data.collect.workingDirInput'))],
            [PySimpleGUI.Text('NLOG Parsers directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationNlogParse),
                                   key='data.collect.nlogParsers'),
             PySimpleGUI.FolderBrowse(target='data.collect.nlogParsers',
                                      initial_folder=str(self.locationNlogParse),
                                      key=('data.collect.parsers.location.folder'))],
            [PySimpleGUI.Text('Firmware Parsers directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationAutoParse),
                                   key='data.collect.fwParsers'),
             PySimpleGUI.FolderBrowse(target='data.collect.fwParsers',
                                      initial_folder=str(self.locationAutoParse),
                                      key=('data.collect.parsers.location.folder'))],
            [PySimpleGUI.Text('Output Working directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.locationOutput),
                                   key='data.collect.workingDirOutput'),
             PySimpleGUI.FolderBrowse(initial_folder=str(self.locationOutput),
                                      key=('data.collect.working.output.location.folder'))],
            [PySimpleGUI.Text('Number of Queries', auto_size_text=False),
             PySimpleGUI.InputText(default_text='10', key='data.collect.numberOfQueries')],
            [PySimpleGUI.Text('Time frame to collect', auto_size_text=False),
             PySimpleGUI.InputText(default_text='60', key='data.collect.timeFrame')],
            [PySimpleGUI.Button('Gather Data', button_color=('white', 'purple'))],
            [PySimpleGUI.Text('MP Decode *.ini file Location:'),
             PySimpleGUI.Text(text=str(self.locationOutput), key='data.telemetry.decode.timeseries.file')],
            [PySimpleGUI.Text('Telemetry Drive Information')],
            [PySimpleGUI.Multiline(
                default_text=pprint.pformat((self.driveSelectedInfo + self.driveHealth), indent=3, width=100),
                autoscroll=True,
                size=(100, 4),
                text_color='green',
                key='data.collect.report',
                do_not_clear=True,
                visible=self.visible)],
            ##################################
            # webpage.handbook.crawl
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Fault Analysis Handbook Webpage (FAH)', font=self.appFont)],
            [PySimpleGUI.Text('Username', auto_size_text=False),
             PySimpleGUI.Input(default_text="", key='webpage.debug.handbook.username')],
            [PySimpleGUI.Text('Password', auto_size_text=False),
             PySimpleGUI.InputText('', key='webpage.debug.handbook.password', password_char='*')],
            [PySimpleGUI.Text('Loaded AES-256 Password Hash Signature', auto_size_text=False),
             PySimpleGUI.Input(default_text='', key='webpage.debug.handbook.hash')],
            [PySimpleGUI.Multiline(default_text=f'Status: Unknown web access...{os.linesep}',
                                   autoscroll=True,
                                   size=(100, 2),
                                   text_color='blue',
                                   key='webpage.debug.handbook.status',
                                   do_not_clear=True,
                                   visible=self.visible)],
            [PySimpleGUI.Button(button_text='Handbook Access', button_color=('white', 'purple'))],
            ##################################
            # data.telemetry.decode
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Telemetry Data Table', font=self.appFont)],
            [PySimpleGUI.Text('Decoded *.ini File', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.dirPathTimeSeries),
                            key='data.telemetry.table.file',
                            enable_events=True),
             PySimpleGUI.FileBrowse(file_types=(("INI Files", "*.ini"),),
                                    initial_folder=str(self.dirPathTimeSeries),
                                    target='data.telemetry.table.file',
                                    key=('data.telemetry.table.file.selected'))],
            [PySimpleGUI.Text('Choose Object to decode or choose all', auto_size_text=False),
             PySimpleGUI.InputCombo(["all"],
                                    size=(10, 1),
                                    key='data.telemetry.table.choice',
                                    default_value='all',
                                    tooltip='Choice of uid to display in a table'),
             PySimpleGUI.Button('Refresh Object UIDs', button_color=('black', 'green'))],
            [PySimpleGUI.Button('Decode', button_color=('white', 'blue'))],
            ##################################
            # data.telemetry.genericObject.metadata.uid.timeseries
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Telemetry Generic Object Time Series Graph', font=self.appFont)],
            [PySimpleGUI.Text('Select Configuration File', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.dirPathTimeSeries),
                            key='data.telemetry.genericObject.metadata.timeseries.file',
                            enable_events=True),
             PySimpleGUI.FileBrowse(target='data.telemetry.genericObject.metadata.timeseries.file',
                                    file_types=(("INI Files", "*.ini"),),
                                    key='data.telemetry.genericObject.metadata.timeseries.file.selected',
                                    initial_folder=str(self.dirPathTimeSeries))],
            [PySimpleGUI.Text('Browse Output Location', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.locationOutput),
                            key='data.telemetry.genericObject.metadata.timeseries.output',
                            enable_events=True),
             PySimpleGUI.FolderBrowse(target='data.telemetry.genericObject.metadata.timeseries.output',
                                      key='data.telemetry.genericObject.metadata.timeseries.output.selected',
                                      initial_folder=str(self.locationOutput))],
            [PySimpleGUI.Text('Object Name', auto_size_text=False),
             PySimpleGUI.Drop(values=(), auto_size_text=True, default_value='Nil', size=(16, 1),
                              key='data.telemetry.genericObject.metadata.timeseries.object', enable_events=True),
             PySimpleGUI.Button('Select Generic Object')],
            [PySimpleGUI.Text('Select tracking variables', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Text('First Variable', auto_size_text=False, ),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.pfvar', enable_events=True)],
                 [PySimpleGUI.Text('Second Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.psvar', enable_events=True)],
                 [PySimpleGUI.Text('Third Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.ptvar', enable_events=True)]],
                 relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variables',
                 tooltip='Select the names for the variables to be graphed in the main axis')],
            [PySimpleGUI.Text('Select optional secondary variables', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Text('First Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.sfvar', enable_events=True)],
                 [PySimpleGUI.Text('Second Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.ssvar', enable_events=True)],
                 [PySimpleGUI.Text('Third Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.genericObject.metadata.timeseries.stvar', enable_events=True)]],
                 relief=PySimpleGUI.RELIEF_SUNKEN, title='Secondary Variables',
                 tooltip='Select the names for the variables to be graphed in the secondary axis')
             ],
            [PySimpleGUI.Text('Start % of data', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=0, resolution=1,
                                key='data.telemetry.genericObject.metadata.timeseries.start')],
            [PySimpleGUI.Text('End % of data', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=100, resolution=1,
                                key='data.telemetry.genericObject.metadata.timeseries.end')],
            [PySimpleGUI.Text('Get the matrix profile for the data?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='No',
                              key='data.telemetry.genericObject.metadata.timeseries.matrix',
                              enable_events=True)],
            [PySimpleGUI.Text('Save Figures to PDF?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='No',
                              key='data.telemetry.genericObject.metadata.timeseries.pdf',
                              enable_events=True)],
            [PySimpleGUI.Button('Plot Generic Object', button_color=('white', 'blue'))],
            ##################################
            # data.telemetry.defragHistory
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Telemetry Defrag History', font=self.appFont)],
            [PySimpleGUI.Text('Drive Type', auto_size_text=False),
             PySimpleGUI.Drop(default_value='CDR', values=('ADP', 'CDR'), size=(4, 1),
                              auto_size_text=True,
                              key='data.telemetry.defragHistory.drive',
                              enable_events=True)],
            [PySimpleGUI.Text('Browse Configuration File', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.dirPathDefragHistory),
                            key='data.telemetry.defragHistory.file',
                            enable_events=True),
             PySimpleGUI.FileBrowse(target='data.telemetry.defragHistory.file',
                                    file_types=(("INI Files", "*.ini"),),
                                    key='data.telemetry.defragHistory.file.selected',
                                    initial_folder=str(self.dirPathDefragHistory))],
            [PySimpleGUI.Text('Browse Output Location', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.locationOutput),
                            key='data.telemetry.defragHistory.output',
                            enable_events=True),
             PySimpleGUI.FolderBrowse(target='data.telemetry.defragHistory.output',
                                      key='data.telemetry.defragHistory.output.selected',
                                      initial_folder=str(self.locationOutput))],
            [PySimpleGUI.Text('Select set points', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Checkbox('start', key='data.telemetry.defragHistory.start', default=True)],
                 [PySimpleGUI.Checkbox('normal', key='data.telemetry.defragHistory.normal', default=True)],
                 [PySimpleGUI.Checkbox('corner', key='data.telemetry.defragHistory.corner', default=True)],
                 [PySimpleGUI.Checkbox('urgent', key='data.telemetry.defragHistory.urgent', default=True)],
                 [PySimpleGUI.Checkbox('critical', key='data.telemetry.defragHistory.critical', default=True)]],
                 title='Set Points', relief=PySimpleGUI.RELIEF_SUNKEN, tooltip='Select set points to be graphed')
             ],
            [PySimpleGUI.Text('Select tracking variables', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Text('First Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.pfvar', enable_events=True)],
                 [PySimpleGUI.Text('Second Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.psvar', enable_events=True)],
                 [PySimpleGUI.Text('Third Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.ptvar', enable_events=True)]
             ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variables',
                 tooltip='Select the names for the variables to be graphed in the main axis')],
            [PySimpleGUI.Text('Select optional secondary variables', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Text('First Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.sfvar', enable_events=True)],
                 [PySimpleGUI.Text('Second Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.ssvar', enable_events=True)],
                 [PySimpleGUI.Text('Third Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='data.telemetry.defragHistory.stvar', enable_events=True)]
             ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Secondary Variables',
                 tooltip='Select the names for the variables to be graphed in the secondary axis')],
            [PySimpleGUI.Text('Start % of data', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=0, resolution=1,
                                key='data.telemetry.defragHistory.startPoint')],
            [PySimpleGUI.Text('End % of data', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=100, resolution=1,
                                key='data.telemetry.defragHistory.endPoint')],
            [PySimpleGUI.Text('Is the secondary axis bandwidth?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='No',
                              key='data.telemetry.defragHistory.bandwidth',
                              enable_events=True)],
            [PySimpleGUI.Text('Select the number of cores', auto_size_text=False),
             PySimpleGUI.Drop(values=(1, 2, 3, 4), auto_size_text=True, default_value=2,
                              key='data.telemetry.defragHistory.cores',
                              enable_events=True)],
            [PySimpleGUI.Text('Save Figures to PDF?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='Yes',
                              key='data.telemetry.defragHistory.pdf',
                              enable_events=True)],
            [PySimpleGUI.Button('Decode Defrag Plot', button_color=('white', 'blue'))],
            ##################################
            # ML-Classify
            ##################################
            # [PySimpleGUI.Text('_' * 100)],
            # [PySimpleGUI.Text('Classification Neural Network Parameters', font=appFont)],
            # Parameters Section
            # [PySimpleGUI.Text('Configuration Parameters')],
            # [PySimpleGUI.Text('Passes', auto_size_text=False, justification='right'),
            # PySimpleGUI.Spin(values=[i for i in range(1, 1000)], initial_value=20,
            #                  key='ml.classify.passes')],
            # [PySimpleGUI.Text('Steps', auto_size_text=False, justification='right'),
            # PySimpleGUI.Spin(values=[i for i in range(1, 1000)], initial_value=20, key='ml.classify.steps')],
            # [PySimpleGUI.Text('OOA', auto_size_text=False, justification='right',
            #                  tooltip='Objective-Oriented Association'),
            # PySimpleGUI.In(default_text='6', key='ml.classify.ooa')],
            # [PySimpleGUI.Text('NN', auto_size_text=False, justification='right', tooltip='Nearest Neighbor'),
            # PySimpleGUI.In(default_text='10', key='ml.classify.nearestNeighbor')],
            # [PySimpleGUI.Text('Q', auto_size_text=False, justification='right', tooltip='Q-learning'),
            # PySimpleGUI.In(default_text='ff', key='ml.classify.qLearning',
            #                tooltip='Friend-or-foe-Q (ff), mini-max-Q (mn), correlated Q-learning (ce)')],
            # [PySimpleGUI.Text('N-Gram', auto_size_text=False, justification='right',
            #                  tooltip='Contiguous sequence of n items from a given sample'),
            # PySimpleGUI.In(default_text='5')],
            # [PySimpleGUI.Text('L', auto_size_text=False, justification='right', tooltip='Learning Rate'),
            # PySimpleGUI.In(default_text='0.4')],
            # [PySimpleGUI.Text('Layers', auto_size_text=False, justification='right',
            #                  tooltip='Each layer learns by itself, more independently'),
            # PySimpleGUI.Drop(values=('BatchNorm', 'other'))],
            # Flags Section
            # [PySimpleGUI.Text('Flags', font=appFont)],
            # [PySimpleGUI.Checkbox('Normalize', default=True),
            # PySimpleGUI.Checkbox('Verbose  ', default=False),
            # PySimpleGUI.Checkbox('Cluster  ', default=False)],
            # [PySimpleGUI.Checkbox('Flush    ', default=False, tooltip="Flush intermediate outputs"),
            # PySimpleGUI.Checkbox('Write    ', default=True, tooltip="Write result Data"),
            # PySimpleGUI.Checkbox('Keep     ', default=False, tooltip="Keep Intermediate Data")],
            # Loss Function Selection, Classification or Regression Selection
            # [PySimpleGUI.Text('Loss Functions', auto_size_text=False),
            # PySimpleGUI.Drop(
            #     values=('Cross-Entropy', 'Logistic', 'Hinge', 'Huber', 'Kullerback', 'MAE(L1)', 'MSE(L2)',
            #             'MB(L0)'))],
            # [PySimpleGUI.Button('Cluster', button_color=('white', 'green'))],
            ##################################
            # Predictor.ARMA
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('ARMA Prediction Plot', font=self.appFont)],
            [PySimpleGUI.Text('Browse Configuration File', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.dirPathARMA), key='Predictor.ARMA.file', enable_events=True),
             PySimpleGUI.FileBrowse(target='Predictor.ARMA.file',
                                    key='Predictor.ARMA.file.selected',
                                    initial_folder=str(self.dirPathARMA),
                                    file_types=(("ALL Files", "*.ini"),))],
            [PySimpleGUI.Text('Object Name', auto_size_text=False),
             PySimpleGUI.Drop(default_value='Nil ', values=('Nil'), size=(16, 1), auto_size_text=True,
                              key='Predictor.ARMA.object',
                              enable_events=True),
             PySimpleGUI.Button('Select Object for ARMA')],
            [PySimpleGUI.Text('Select tracking axis variable', auto_size_text=False),
             PySimpleGUI.Frame(layout=[[PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                                         key='Predictor.ARMA.field')]],
                               relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variable',
                               tooltip='Select the names for the variable to be graphed in the main axis')],
            [PySimpleGUI.Text('Length of Window to be considered for Matrix Profile', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=8, resolution=1,
                                key='Predictor.ARMA.ssl')],
            [PySimpleGUI.Text('Get the matrix profile for the data?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, default_value='No',
                              key='Predictor.ARMA.matrix',
                              enable_events=True)],
            [PySimpleGUI.Button('Plot ARMA Prediction', button_color=('white', 'blue'))],
            ##################################
            # Predictor.RNN
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('RNN Prediction Plot', font=self.appFont)],
            [PySimpleGUI.Text('Browse Configuration File', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.dirPathRNN), key='Predictor.RNN.file', enable_events=True),
             PySimpleGUI.FileBrowse(initial_folder=str(self.dirPathRNN),
                                    target='Predictor.RNN.file',
                                    key='Predictor.RNN.file.selected')],
            [PySimpleGUI.Text('Object Name', auto_size_text=False),
             PySimpleGUI.Drop(default_value='Nil', values=(), size=(16, 1), auto_size_text=True,
                              key='Predictor.RNN.object',
                              enable_events=True),
             PySimpleGUI.Button('Select Object for RNN')],
            [PySimpleGUI.Text('Select Field variables', auto_size_text=False),
             PySimpleGUI.Frame(layout=[
                 [PySimpleGUI.Text('First Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='Predictor.RNN.pfvar', enable_events=True)],
                 [PySimpleGUI.Text('Second Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='Predictor.RNN.psvar', enable_events=True)],
                 [PySimpleGUI.Text('Third Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='Predictor.RNN.ptvar', enable_events=True)],
                 [PySimpleGUI.Text('Fourth Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='Predictor.RNN.pfovar', enable_events=True)],
                 [PySimpleGUI.Text('Fifth Variable', auto_size_text=False),
                  PySimpleGUI.Drop(values=(), default_value='Nil', size=(16, 1),
                                   key='Predictor.RNN.pfivar', enable_events=True)],
             ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Input Variables',
                 tooltip='Select the names for the field variables to be fed into the neural networks as time series')],
            [PySimpleGUI.Text('Select Plot data', auto_size_text=False),
             PySimpleGUI.Frame(layout=[[PySimpleGUI.Text('Plot Variable', auto_size_text=False),
                                        PySimpleGUI.Drop(values=(), key='Predictor.RNN.sfvar', size=(16, 1),
                                                         enable_events=True)]],
                               relief=PySimpleGUI.RELIEF_SUNKEN, title='Plot Variable',
                               tooltip='Select the name for the variable to be graphed in the main axis')],
            [PySimpleGUI.Text('Input Width', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 10000), orientation='h', default_value=200, resolution=20, enable_events=True,
                                change_submits=True, key='Predictor.RNN.inputWidth'),
             PySimpleGUI.Spin([num for num in range(0, 10000, 20)], initial_value=200, enable_events=True,
                              change_submits=True, key='Predictor.RNN.inputWidthSpin')],
            [PySimpleGUI.Text('Label Width', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 10000), orientation='h', default_value=30, resolution=10, enable_events=True,
                                change_submits=True, key='Predictor.RNN.labelWidth'),
             PySimpleGUI.Spin([num for num in range(0, 10000, 20)], initial_value=30, enable_events=True,
                              change_submits=True, key='Predictor.RNN.labelWidthSpin')],
            [PySimpleGUI.Text('Shift', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 10000), orientation='h', default_value=30, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.RNN.shift'),
             PySimpleGUI.Spin([num for num in range(0, 10000, 2)], initial_value=30, enable_events=True,
                              change_submits=True, key='Predictor.RNN.shiftSpin')],
            [PySimpleGUI.Text('Neurons Per Hidden Layer', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 8192), orientation='h', default_value=256, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.RNN.hiddenLayers'),
             PySimpleGUI.Spin([num for num in range(2, 8192, 2)], initial_value=256, enable_events=True,
                              change_submits=True, key='Predictor.RNN.hiddenLayersSpin')],
            [PySimpleGUI.Text('Batch Size', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 512), orientation='h', default_value=64, resolution=2, enable_events=True, change_submits=True,
                                key='Predictor.RNN.batchSize'),
             PySimpleGUI.Spin([num for num in range(2, 512, 2)], initial_value=64, enable_events=True,
                              change_submits=True, key='Predictor.RNN.batchSizeSpin')],
            [PySimpleGUI.Text('Max Epochs', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 65536), orientation='h', default_value=2096, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.RNN.maxEpochs'),
             PySimpleGUI.Spin([num for num in range(2, 65536, 2)], initial_value=2096, enable_events=True,
                              change_submits=True, key='Predictor.RNN.maxEpochsSpin')],
            [PySimpleGUI.Text('Categorical Encoding for Data?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='No', key='Predictor.RNN.categorical',
                              enable_events=True)],
            [PySimpleGUI.Text('Embedded Encoding for Data?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='No', key='Predictor.RNN.embedded',
                              enable_events=True)],
            [PySimpleGUI.Text('Optimizer for Neural Network', auto_size_text=False),
             PySimpleGUI.Drop(values=('SGD', 'RMSprop', 'Adam', 'Adadelta', 'Adagrad', 'Adamax', 'Nadam', 'Ftrl'),
                              default_value='Adam', key='Predictor.RNN.optimizer', enable_events=True)],
            [PySimpleGUI.Text('Activation for LSTM Layers', auto_size_text=False),
             PySimpleGUI.Drop(values=('relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                      'exponential'),
                              default_value='tanh', key='Predictor.RNN.lstm_activation', enable_events=True)],
            [PySimpleGUI.Text('Activation for Dense Layer', auto_size_text=False),
             PySimpleGUI.Drop(values=('relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                      'exponential'),
                              default_value='sigmoid', key='Predictor.RNN.dense_activation', enable_events=True)],
            [PySimpleGUI.Text('Initializer for LSTM Layers', auto_size_text=False),
             PySimpleGUI.Drop(values=('random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                      'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                      'variance_scaling'),
                              default_value='glorot_uniform', key='Predictor.RNN.lstm_initializer',
                              enable_events=True)],
            [PySimpleGUI.Text('Initializer for Dense Layer', auto_size_text=False),
             PySimpleGUI.Drop(values=('random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                      'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                      'variance_scaling'),
                              default_value='glorot_uniform', key='Predictor.RNN.dense_initializer',
                              enable_events=True)],
            [PySimpleGUI.Text('Apply Dropout Between Layers?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='Yes', key='Predictor.RNN.dropout',
                              enable_events=True)],
            [PySimpleGUI.Text('Get the matrix profile for the data?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='No', key='Predictor.RNN.matrix',
                              enable_events=True)],
            [PySimpleGUI.Text('Length of Window to be considered for Matrix Profile', auto_size_text=False),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', default_value=8,
                                key='Predictor.RNN.ssl')],
            [PySimpleGUI.Button('Plot RNN Prediction', button_color=('white', 'blue'))],
            ##################################
            # Predictor.NLOG
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('NLOG Event Predictor', font=self.appFont)],
            [PySimpleGUI.Text('Browse NLOG folder', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.nlogFolder), key='Predictor.NLOG.nlogFolder', enable_events=True),
             PySimpleGUI.FileBrowse(initial_folder=str(self.nlogFolder),
                                    target='Predictor.NLOG.nlogFolder',
                                    key='Predictor.NLOG.nlogFolder.selected')],
            [PySimpleGUI.Text('Browse NLOG Parser folder', auto_size_text=False),
             PySimpleGUI.In(default_text=str(self.nlogParserFolder), key='Predictor.NLOG.nlogParserFolder', enable_events=True),
             PySimpleGUI.FileBrowse(initial_folder=str(self.nlogParserFolder),
                                    target='Predictor.NLOG.nlogParserFolder',
                                    key='Predictor.NLOG.nlogParserFolder.selected')],
            [PySimpleGUI.Text('Number of Components', auto_size_text=False),
             PySimpleGUI.Slider(range=(1, 800), orientation='h', default_value=50, resolution=1, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.numComponents'),
             PySimpleGUI.Spin([num for num in range(1, 800, 1)], initial_value=50, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.numComponentsSpin')],
            [PySimpleGUI.Text('Max Number of Parameters', auto_size_text=False),
             PySimpleGUI.Slider(range=(1, 10), orientation='h', default_value=8, resolution=1, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.maxNumParams'),
             PySimpleGUI.Spin([num for num in range(1, 10, 1)], initial_value=8, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.maxNumParamsSpin')],
            [PySimpleGUI.Text('Input Size', auto_size_text=False),
             PySimpleGUI.Slider(range=(100, 10000), orientation='h', default_value=4000, resolution=100,
                                enable_events=True, change_submits=True, key='Predictor.NLOG.inputSize'),
             PySimpleGUI.Spin([num for num in range(100, 10000, 100)], initial_value=4000, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.inputSizeSpin')],
            [PySimpleGUI.Text('Max Output Size', auto_size_text=False),
             PySimpleGUI.Slider(range=(100, 10000), orientation='h', default_value=1000, resolution=100,
                                enable_events=True, change_submits=True, key='Predictor.NLOG.maxOutputSize'),
             PySimpleGUI.Spin([num for num in range(1, 10000, 100)], initial_value=1000, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.maxOutputSizeSpin')],
            [PySimpleGUI.Text('Model Type for Width Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('elastic', 'lasso', 'ridge', 'default'),
                              default_value='elastic', key='Predictor.NLOG.widthModelType', enable_events=True)],
            [PySimpleGUI.Text('Neurons Per Hidden Layer For Time Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 8192), orientation='h', default_value=128, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.timeHiddenUnits'),
             PySimpleGUI.Spin([num for num in range(2, 8192, 2)], initial_value=128, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.timeHiddenUnitsSpin')],
            [PySimpleGUI.Text('Neurons Per Hidden Layer For Event Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 8192), orientation='h', default_value=128, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.eventsHiddenUnits'),
             PySimpleGUI.Spin([num for num in range(2, 8192, 2)], initial_value=128, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.eventsHiddenUnitsSpin')],
            [PySimpleGUI.Text('Neurons Per Hidden Layer For Parameter Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 8192), orientation='h', default_value=128, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.paramsHiddenUnits'),
             PySimpleGUI.Spin([num for num in range(2, 8192, 2)], initial_value=128, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.paramsHiddenUnitsSpin')],
            [PySimpleGUI.Text('Max Epochs For Time Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 65536), orientation='h', default_value=2096, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.timeMaxEpochs'),
             PySimpleGUI.Spin([num for num in range(2, 65536, 2)], initial_value=2096, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.timeMaxEpochsSpin')],
            [PySimpleGUI.Text('Max Epochs For Event Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 65536), orientation='h', default_value=2096, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.eventsMaxEpochs'),
             PySimpleGUI.Spin([num for num in range(2, 65536, 2)], initial_value=2096, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.eventsMaxEpochsSpin')],
            [PySimpleGUI.Text('Max Epochs For Parameter Predictor', auto_size_text=False),
             PySimpleGUI.Slider(range=(2, 65536), orientation='h', default_value=2096, resolution=2, enable_events=True,
                                change_submits=True, key='Predictor.NLOG.paramsMaxEpochs'),
             PySimpleGUI.Spin([num for num in range(2, 65536, 2)], initial_value=2096, enable_events=True,
                              change_submits=True, key='Predictor.NLOG.paramsMaxEpochsSpin')],
            [PySimpleGUI.Text('Optimizer for Time Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('SGD', 'RMSprop', 'Adam', 'Adadelta', 'Adagrad', 'Adamax', 'Nadam', 'Ftrl'),
                              default_value='Adam', key='Predictor.NLOG.timeOptimizer', enable_events=True)],
            [PySimpleGUI.Text('Optimizer for Event Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('SGD', 'RMSprop', 'Adam', 'Adadelta', 'Adagrad', 'Adamax', 'Nadam', 'Ftrl'),
                              default_value='Adam', key='Predictor.NLOG.eventsOptimizer', enable_events=True)],
            [PySimpleGUI.Text('Optimizer for Parameter Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('SGD', 'RMSprop', 'Adam', 'Adadelta', 'Adagrad', 'Adamax', 'Nadam', 'Ftrl'),
                              default_value='Adam', key='Predictor.NLOG.paramsOptimizer', enable_events=True)],
            [PySimpleGUI.Text('Activation for LSTM Layers in Time Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                      'exponential'),
                              default_value='tanh', key='Predictor.NLOG.timeLstmActivation', enable_events=True)],
            [PySimpleGUI.Text('Activation for LSTM Layers in Event Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                      'exponential'),
                              default_value='tanh', key='Predictor.NLOG.eventsLstmActivation', enable_events=True)],
            [PySimpleGUI.Text('Activation for LSTM Layers in Parameter Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                      'exponential'),
                              default_value='tanh', key='Predictor.NLOG.paramsLstmActivation', enable_events=True)],
            [PySimpleGUI.Text('Initializer for LSTM Layers in Time Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                      'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                      'variance_scaling'),
                              default_value='glorot_uniform', key='Predictor.NLOG.timeLstmInitializer',
                              enable_events=True)],
            [PySimpleGUI.Text('Initializer for LSTM Layers in Event Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                      'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                      'variance_scaling'),
                              default_value='glorot_uniform', key='Predictor.NLOG.eventsLstmInitializer',
                              enable_events=True)],
            [PySimpleGUI.Text('Initializer for LSTM Layers in Parameter Predictor', auto_size_text=False),
             PySimpleGUI.Drop(values=('random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                      'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                      'variance_scaling'),
                              default_value='glorot_uniform', key='Predictor.NLOG.paramsLstmInitializer',
                              enable_events=True)],
            [PySimpleGUI.Text('Apply Dropout Between Layers in Time Predictor?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='Yes', key='Predictor.NLOG.timeDropout',
                              enable_events=True)],
            [PySimpleGUI.Text('Apply Dropout Between Layers in Event Predictor?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='Yes', key='Predictor.NLOG.eventsDropout',
                              enable_events=True)],
            [PySimpleGUI.Text('Apply Dropout Between Layers in Parameter Predictor?', auto_size_text=False),
             PySimpleGUI.Drop(values=('Yes', 'No'), default_value='Yes', key='Predictor.NLOG.paramsDropout',
                              enable_events=True)],
            [PySimpleGUI.Button('Execute NLOG Prediction', button_color=('white', 'blue'))],
            ##################################
            # user.report
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('User Report', font=self.appFont, visible=self.visible)],
            [PySimpleGUI.Multiline(default_text=pprint.pformat(self.displayReport, indent=3, width=100),
                                   autoscroll=True,
                                   size=(100, 8),
                                   text_color='green',
                                   key='user.report',
                                   do_not_clear=True,
                                   visible=self.visible)],
            [PySimpleGUI.Button('Refresh Report', button_color=('white', 'green'))],
            ##################################
            # upload.content
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('AXON Database Upload', font=self.appFont)],
            [PySimpleGUI.Text('Please enter your upload Destination and the file to upload', auto_size_text=False),
             PySimpleGUI.InputCombo(('test', 'production', 'development'), default_value='test', key='uploadMode')],
            [PySimpleGUI.Text('Content File', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.dirPathUpload),
                                   key='upload.content.location'),
             PySimpleGUI.FileBrowse(file_types=(("COMPRESS Files", "*.zip"),),
                                    initial_folder=str(self.locationOutput),
                                    target='upload.content.location.folder',
                                    key='upload.content.location.folder.selected')],
            [PySimpleGUI.Button('Axon Upload', button_color=('black', '#475841'))],
            ##################################
            # Download
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('AXON Database Download', font=self.appFont)],
            [PySimpleGUI.Text('Choose download directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(os.getcwd()), key='download.location.directory'),
             PySimpleGUI.FolderBrowse(initial_folder=str(self.dirPathTimeSeries), key=('data.download.location.folder'))],
            [PySimpleGUI.Text('AXON IDs', auto_size_text=False),
             PySimpleGUI.InputCombo(self.axonIDs, size=(15, 1), enable_events=True, default_value='', key='-download.choice.ID-')],
            [PySimpleGUI.Text('Time created:', auto_size_text=False), PySimpleGUI.Text(key='-download.choice.time-')],
            [PySimpleGUI.Text('Product Name:', auto_size_text=False), PySimpleGUI.Text(key='-download.choice.product-')],
            [PySimpleGUI.Text('Serial Number:', auto_size_text=False), PySimpleGUI.Text(key='-download.choice.serial-')],
            [PySimpleGUI.Text('User:', auto_size_text=False), PySimpleGUI.Text(key='-download.choice.user-')],
            [PySimpleGUI.Button('Axon Download', button_color=('black', '#9FB8AD'))],
            [PySimpleGUI.Text('Download Information', visible=self.visible, auto_size_text=False)],
            [PySimpleGUI.Multiline(default_text=pprint.pformat(str(self.axonDownloadOutput), indent=3, width=100),
                                   autoscroll=True,
                                   size=(100, 8),
                                   text_color='green',
                                   key='data.download.report',
                                   do_not_clear=True,
                                   visible=self.visible)],
            ##################################
            # profile.user
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('User profile information', font=self.appFont)],
            [PySimpleGUI.Text('Enter identity number', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.identity), key='identity')],
            [PySimpleGUI.Text('Enter username', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.name), key='name')],
            [PySimpleGUI.Text('Enter mode', auto_size_text=False),
             PySimpleGUI.InputCombo(('cmd', 'gui'), default_value=self.mode, key='mode')],
            [PySimpleGUI.Text('Key encrypt-decrypt location', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.keyLoc), key='keyLoc'),
             PySimpleGUI.FolderBrowse(initial_folder=str(self.keyLoc),
                                      key=('profile.application.user.encryption.location.folder'))],
            [PySimpleGUI.Text('Enable Encryption', auto_size_text=False),
             PySimpleGUI.InputCombo(('True', 'False'), default_value=str(self.encryptionStatus),
                                    key='encryptionStatus')],
            [PySimpleGUI.Text('Enter working directory', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.workingDir), key='workingDir'),
             PySimpleGUI.FolderBrowse(initial_folder=self.workingDir,
                                      key=('profile.application.user.working.location.folder'))],
            [PySimpleGUI.Button('Update Profile', button_color=('black', 'orange'))],
            ##################################
            # profile.application.raad
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Application information for RAAD', font=self.appFont)],
            [PySimpleGUI.Text('Enter identity number', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.identity), key=('profile.application.raad.identity'))],
            [PySimpleGUI.Text('Enter major version number', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.major), key=('profile.application.raad.major'))],
            [PySimpleGUI.Text('Enter minor version number', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.minor), key=('profile.application.raad.minor'))],
            [PySimpleGUI.Text('Enter name', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.name), key=('profile.application.raad.name'))],
            [PySimpleGUI.Text('Execution location', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.location), key=('profile.application.raad.location')),
             PySimpleGUI.FolderBrowse(initial_folder=self.location, key=('profile.application.raad.location.folder'))],
            [PySimpleGUI.Text('Enter mode', auto_size_text=False),
             PySimpleGUI.InputCombo(('cmd', 'gui'), default_value=self.mode, key=('profile.application.raad.mode'))],
            [PySimpleGUI.Text('Enter URL', auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(self.url), key=('profile.application.raad.url'))],
            [PySimpleGUI.Button('Update Applications', button_color=('black', 'orange'))],
            ##################################
            # User.Feedback
            ##################################
            # [PySimpleGUI.Text('_' * 100)],
            # [PySimpleGUI.Text('User Feedback Comments', font=appFont)],
            # [PySimpleGUI.Multiline(default_text='Please provide feedback based on experience.',
            #                       size=(64, 8),
            #                       key='feedbackComment')],
            # [PySimpleGUI.Button('Send Feedback', button_color=('white', 'pink'))],
            ##################################
            # Debug.Dump
            ##################################
            [PySimpleGUI.Text('_' * 100)],
            [PySimpleGUI.Text('Console Value Dump Information', font=self.appFont, visible=self.visible)],
            [PySimpleGUI.Multiline(default_text=str(self.displayInput),
                                   autoscroll=True,
                                   size=(100, 8),
                                   text_color='green',
                                   key='_MULTIDEBUGOUT_',
                                   do_not_clear=True,
                                   visible=self.visible)],
            [PySimpleGUI.Text('Console Event Dump Information', visible=self.visible)],
            # [PySimpleGUI.MultilineOutput(default_text='Event Output',
            [PySimpleGUI.Multiline(default_text='Event Output',
                                   autoscroll=True,
                                   size=(100, 8),
                                   text_color='blue',
                                   key='_MULTIEVENTOUT_',
                                   do_not_clear=True,
                                   visible=self.visible)]
        ]

        # Add Menu and Buttons
        layout.insert(0, [PySimpleGUI.Menu(self.menu_def, key='_MENU_', tearoff=True)])
        layout.append([PySimpleGUI.Button('Exit', button_color=('white', 'black')),
                       PySimpleGUI.Cancel(button_color=('white', 'red'))])

        # Display collect form
        self.windowActive = PySimpleGUI.Window(title=self.programLabel,
                                               resizable=True,
                                               auto_size_text=True,
                                               auto_size_buttons=True,
                                               grab_anywhere=True,
                                               finalize=True).Layout(
            [[PySimpleGUI.Column(layout, scrollable=True, pad=((11, 11), (11, 11)))]])

        collect_button = None
        collect_values = None
        while self.continueRun:
            (collect_button, collect_values) = (self.windowActive).read()
            self.button = collect_button
            self.values = collect_values
            """
            if (firstPass is True):
                # Generic Object
                vts, objectFileGeneric, objectDictGeneric = populate_object_generic_object(self.windowActive, dirPathTimeSeries)
                display_dir_generic_object(self.windowActive, objectFileGeneric, currentObjectGeneric)
                create_new_graph_window_generic_object(collect_values, vts, objectFileGeneric, currentObjectGeneric)
                # Defrag History
                dhg, dhFile = display_dir_defrag(self.windowActive, dirPathDefragHistory, mode)
                create_new_graph_window_defrag(collect_values, dhg, dhFile)            
                # RNN
                rnn, objectFileRNN, objectDict = populate_object_RNN(self.windowActive, dirPathRNN)
                display_dir_RNN(self.windowActive, objectFileRNN, currentObjectRNN)
                create_new_graph_window_RNN(collect_values, rnn, currentObjectRNN)
                # ARMA
                mep, objectFileARMA = populate_object_ARMA(self.windowActive, dirPathARMA)
                display_dir_ARMA(self.windowActive, objectFileARMA, currentObjectARMA)
                create_new_graph_window_ARMA(collect_values, mep, currentObjectARMA)
                # AXON Upload
                # uploadSuccess, uploadID = GUI.GUIUpload(contentFile, mode=uploadMode)
                # axonDownload_exitCode, axonDownload_cmdOutput, axonDownload_cmdError = GUI.GUIDownload(downloadID, downloadDirectory)
                firstPass = False
            """
            try:
                # print("MENU")
                # print(pprint.pformat(collect_values['_MENU_'], indent=3, width=100))
                if ((collect_button is None) or
                        (collect_button == 'Cancel') or
                        (collect_button == 'Exit') or
                        (collect_values['_MENU_'] == 'Exit') or
                        (collect_button is PySimpleGUI.WIN_CLOSED)):  # if user closes window or clicks cancel
                    continueRun = False
                elif collect_values['_MENU_'] == "Save":
                    if self.VARIABLE_DUMP_FILE is not None:
                        self.windowActive.SaveToDisk(self.VARIABLE_DUMP_FILE)
                    else:
                        print("No save could be located")
                elif collect_values['_MENU_'] == "Load":
                    if self.VARIABLE_DUMP_FILE is not None:
                        self.windowActive.LoadFromDisk(self.VARIABLE_DUMP_FILE)
                    else:
                        print("No save could be located")
                elif collect_values['_MENU_'] == "About":
                    self.windowActive.disappear()
                    PySimpleGUI.Popup("Go to dox/build/index.html")
                    PySimpleGUI.popup('About this program', 'Version 1.0', 'RAAD Version', PySimpleGUI.version,
                                      grab_anywhere=True)
                    self.windowActive.reappear()
                # elif collect_values['_MENU_'] == 'Increase +':
                #    @TODO enable API font size changes.
                #    if ((currentFontSize >= 10) and (currentFontSize < 60)):
                #        currentFontSize = currentFontSize + 1
                #        appFont = ("Helvetica", currentFontSize)
                #        for keyWindow, valueWindow in enumerate(self.windowActive):
                #            print(keyWindow, " \n", valueWindow)
                #            self.windowActive.Element(keyWindow).Update(font=appFont)
                #        self.windowActive.Refresh()
                # elif collect_values['_MENU_'] == 'Decrease -':
                #    if ((currentFontSize >= 10) and (currentFontSize <= 60)):
                #        currentFontSize = currentFontSize - 1
                #        appFont = ("Helvetica", currentFontSize)
                #        for indexWindow in enumerate(self.windowActive):
                #            print(keyWindow, " \n", valueWindow)
                #            self.windowActive.Element(keyWindow).Update(font=appFont)
                #        self.windowActive.Refresh()
                # Assign Collect form Values
                # Check which button pressed and pass to corresponding functions
                elif collect_button == 'Cluster':
                    pass  # TODO
                elif collect_button == 'Update Profile':
                    pass  # TODO
                elif collect_button == 'Update Application':
                    pass  # TODO
                elif collect_button == 'Send Feedback':
                    pass  # TODO
                elif collect_button == 'Update Profile':
                    pass  # TODO
                elif collect_button == 'Update Application':
                    pass  # TODO
                elif collect_button == 'Send Feedback':
                    pass  # TODO
                elif collect_button == 'Load and Probe Drive':
                    self.loadAndProbeDrive(collect_values)
                elif collect_button == 'Gather Data':
                    # Delete output folder contents and recreate
                    cleanAndRecreatePath(locationOutput=self.locationOutput)
                    # User pressed the Gather Data button, so query device for telemetry data
                    self.dataFileName = self.gatherTelemetryData(collect_values)
                    # Translation for mode field
                    self.currentMode = self.modeTranslate[collect_values['data.collect.toolChoice']]
                    self.dataDict = self.getDataDic(self.dataFileName)
                    self.dataDictFlat = DictionaryFlatten(self.dataDict)
                    print(f"Len {self.dataDictFlat.getSize()}")
                    self.driveInfo = src.software.access.DriveInfo.DriveInfo().DriveInfoAPI(mode=self.currentMode, dataDict=self.dataDict)
                    if self.debug:
                        print("dataFileName: ", self.dataFileName)
                        print("driveInfo: ", self.driveInfo)
                    self.windowActive['data.telemetry.decode.timeseries.file'].update(self.dataFileName)
                    self.windowActive['data.collect.report'].update(pprint.pformat(self.driveInfo, indent=3, width=100))
                    # self.windowActive['data.telemetry.decode.Information'].update(software.access.DriveInfo.DriveInfo().DriveInfoAPI())
                    # reportDictionary.setDriveInfo()
                    self.reportDictionary.updateInitialize(binaryPath=self.binLocation,
                                                           fwDir=self.locationAutoParse,
                                                           nlogFolder=self.locationNlogParse,
                                                           configFileName=self.dataFileName,
                                                           resultsFolder=self.locationOutput,
                                                           useCSV=True,
                                                           debug=self.debug)
                    self.reportDictionary.updateReportMeta(uidsFound=list(self.dataDict.keys()),
                                                           deviceConfiguration=None,
                                                           dataDict=None, dataDictDimension=self.dataDictFlat.getSize(),
                                                           DFA=None, CFG=None, DFG=None,
                                                           MLProfiles=None,
                                                           assistedFigures=None,
                                                           timeSeriesSignatures=None)
                elif collect_button == 'Refresh':
                    # User refreshed the Meta Data section, so repopulate table with most recent data
                    self.refreshMetaTable()
                # Table Decode events
                elif collect_button == 'Refresh Object UIDs':
                    if os.path.exists(collect_values['data.telemetry.table.file']):
                        self.dataDict = self.getDataDic(collect_values['data.telemetry.table.file'])
                        self.UIDList = ["all"]
                        self.UIDList = self.UIDList + list(self.dataDict.keys())
                        if self.debug:
                            print("UID Keys: ", pprint.pformat(self.dataDict.keys()))
                            print(pprint.pformat(self.UIDList))
                        self.windowActive['data.telemetry.table.choice'].update(values=self.UIDList)
                elif collect_button == 'Decode':
                    if os.path.exists(collect_values['data.telemetry.table.file']):
                        # Get dictionary of the chosen file
                        self.dataArray = self.getDataAsArray(self.getDataDic(collect_values['data.telemetry.table.file']),
                                                             chosenKey=collect_values['data.telemetry.table.choice'])
                        print("dataArray: ", self.dataArray)
                        # Create table and spawn new window for it
                        self.popupTable(self.dataArray, self.programLabel)
                # Generic Object Graph events
                elif collect_button == 'data.telemetry.genericObject.metadata.timeseries.file':
                    self.dirPathTimeSeries = collect_values['data.telemetry.genericObject.metadata.timeseries.file']
                    self.vts, self.objectFileGeneric, self.objectDictGeneric = self.populate_object_generic_object(window=self.windowActive, dirPath=self.dirPathTimeSeries)
                elif collect_button == 'Select Generic Object':
                    self.currentName = collect_values['data.telemetry.genericObject.metadata.timeseries.object']
                    self.currentObjectNumber = self.objectDictGeneric[self.currentName]
                    self.currentObjectGeneric = ("uid-" + self.currentObjectNumber)
                    self.display_dir_generic_object(window=self.windowActive,
                                                    objectFile=self.objectFileGeneric,
                                                    currentObject=self.currentObjectGeneric,
                                                    primaryVarLabelsGenericObject=self.primaryVarLabelsGenericObject,
                                                    secondaryVarLabelsGenericObject=self.secondaryVarLabelsGenericObject)
                elif collect_button == 'Plot Generic Object':
                    self.create_new_graph_window_generic_object(values=collect_values, vts=self.vts,
                                                                objectFile=self.objectFileGeneric,
                                                                currentObject=self.currentObjectGeneric,
                                                                primaryVarLabelsGenericObject=self.primaryVarLabelsGenericObject,
                                                                secondaryVarLabelsGenericObject=self.secondaryVarLabelsGenericObject)
                # Fault Analysis Handbook Wiki Page Access
                elif collect_button == 'Handbook Access':
                    handbookInfo = None
                    # Get GUI information
                    username = collect_values['webpage.debug.handbook.username']
                    password = collect_values['webpage.debug.handbook.password']
                    passwordCheckObject = src.software.axon.packageInterface.Cipher_AES(key=self.passwordEncodingObject.get_key(), iv=self.passwordEncodingObject.get_iv())
                    passwordCheckObject.encrypt(text=password)
                    pastPWDvsNOWPWD = ((passwordCheckObject.get_encryptedText() != self.passwordEncodingObject.get_encryptedText()) and
                                       (self.passwordEncodingObject.get_encryptedText() is not None))
                    if pastPWDvsNOWPWD:
                        self.passwordEncodingObject = None
                        self.passwordEncodingObject = src.software.axon.packageInterface.Cipher_AES()
                    # User name and password Boolean checks
                    defaultPasswordInformation = (username == "" or password == "")
                    passwordObjectEmpty = (self.passwordEncodingObject.get_encryptedText() is None)
                    passwordFileExists = os.path.isfile(self.defaultPasswordFile)
                    updateDisplayUserPass = False
                    # Cases are Turing Complete.
                    if passwordFileExists and passwordObjectEmpty:
                        # Case 1: Password file exists and not encoded yet.
                        with open(self.defaultPasswordFile) as openFile:
                            fileMeta = openFile.read()
                            UserInfoTokens = fileMeta.split('\n')  # Separator is \n 3
                            username = UserInfoTokens[0]
                            self.windowActive['webpage.debug.handbook.username'].update(username)
                            self.passwordEncodingObject.encrypt(text=UserInfoTokens[1])
                            del UserInfoTokens, fileMeta, openFile  # Do not keep unencoded password
                        updateDisplayUserPass = True
                    elif passwordFileExists and not passwordObjectEmpty:
                        # Case 2: Password file exists and has been encoded yet.
                        updateDisplayUserPass = False
                    elif not passwordFileExists and passwordObjectEmpty:
                        # Case 3: Password file does not exist and not encoded yet.
                        if not defaultPasswordInformation:
                            # Encode user text since not default
                            self.passwordEncodingObject.encrypt(text=password)
                            updateDisplayUserPass = True
                        else:
                            updateDisplayUserPass = False
                    elif not passwordFileExists and not passwordObjectEmpty:
                        # Case 4: Password file does not exist and has been encoded yet.
                        print("Password file does not exist and has been encoded yet.")
                        updateDisplayUserPass = False
                    else:
                        # Case N: Catch all...
                        updateDisplayUserPass = False
                    if updateDisplayUserPass:
                        # password_utf = password.encode('utf-8')
                        # sha1hash = hashlib.sha1()
                        # sha1hash.update(password_utf)
                        # password_hash = sha1hash.hexdigest()
                        password_hash = self.passwordEncodingObject.get_encryptedText()
                        self.windowActive['webpage.debug.handbook.hash'].update(password_hash)
                        del password_hash
                    # @todo Add Wiki update.
                    password_hash = self.passwordEncodingObject.get_encryptedText()
                    wikiInterface = AnalysisGuide(debug=self.debug)
                    # @todo Add container passing to lower modules to ensure not secret data is decodable in DRAM/CPU Caches.

                    handbookInfo = wikiInterface.pythonAPI(selectedMode=1,
                                                           default_username=username,
                                                           default_password=self.passwordEncodingObject.decrypt(cipher_text=password_hash),
                                                           outputFile=self.debugHandbookFile,
                                                           searchString=None)
                    # Delete vars for in use.
                    del username, password, updateDisplayUserPass
                    del defaultPasswordInformation, passwordObjectEmpty
                    del passwordFileExists, passwordCheckObject
                    del pastPWDvsNOWPWD, password_hash

                    # Update system info.
                    self.windowActive.Element('user.report').Update(str(self.displayReport) + '\n', append=False)

                    # Update web access info.
                    debugHandbookStatus = self.windowActive.FindElement('webpage.debug.handbook.status').Widget
                    debugHandbookStatus.tag_config("info", background="blue", foreground="white")
                    debugHandbookStatus.tag_config("warning", background="green", foreground="white")
                    debugHandbookStatus.tag_config("critical", background="yellow", foreground="black")
                    debugHandbookStatus.tag_config("error", background="red", foreground="black")
                    if handbookInfo is not None:
                        debugHandbookStatus.insert("end", f"{getTimeStamp()} Status: Access, using live data.{os.linesep}", "info")
                        self.debugHandbookStatus = self.debugHandbookTranslate[2]
                    else:
                        handbookInfo = wikiInterface.loadCache(loadFile=self.debugHandbookFile)
                        if handbookInfo is not None:
                            debugHandbookStatus.insert("end", f"{getTimeStamp()} Status: No Access, using cache.{os.linesep}", "warning")
                            self.debugHandbookStatus = self.debugHandbookTranslate[3]
                        else:
                            debugHandbookStatus.insert("end", f"{getTimeStamp()} Status: No Access, at all.{os.linesep}", "critical")
                            debugHandbookStatus.insert("end", f"{getTimeStamp()} No reference meta data, providing raw data.{os.linesep}", "error")
                            self.debugHandbookStatus = self.debugHandbookTranslate[4]
                    del debugHandbookStatus, handbookInfo, wikiInterface

                # Defrag History Graph events
                elif collect_button == 'data.telemetry.defragHistory.file':
                    self.dirPathDefragHistory = collect_values['data.telemetry.defragHistory.file']
                    self.driveName = collect_values['data.telemetry.defragHistory.drive']
                    self.mode = 0
                    if self.driveName == 'ADP':
                        self.mode = 1
                    elif self.driveName == 'CDR':
                        self.mode = 2
                    self.dhg, self.dhFile = self.display_dir_defrag(window=self.windowActive,
                                                                    dirPath=self.dirPathDefragHistory,
                                                                    mode=self.mode,
                                                                    primaryVarLabelsDefragHistory=self.primaryVarLabelsDefragHistory,
                                                                    secondaryVarLabelsDefragHistory=self.secondaryVarLabelsDefragHistory)
                elif collect_button == 'Decode Defrag Plot':
                    print("plotting.....")
                    self.create_new_graph_window_defrag(values=collect_values,
                                                        dhg=self.dhg,
                                                        dhFile=self.dhFile,
                                                        setPointLabelsDict=self.setPointLabelsDict,
                                                        primaryVarLabelsDefragHistory=self.primaryVarLabelsDefragHistory,
                                                        secondaryVarLabelsDefragHistory=self.secondaryVarLabelsDefragHistory)

                # ARMA predictor events
                elif collect_button == 'Predictor.ARMA.file':
                    self.dirPathARMA = collect_values['Predictor.ARMA.file']
                    self.mep, self.objectFileARMA = self.populate_object_ARMA(window=self.windowActive, dirPath=self.dirPathARMA)
                elif collect_button == 'Select Object for ARMA':
                    self.currentObjectARMA = collect_values['Predictor.ARMA.object']
                    self.display_dir_ARMA(window=self.windowActive, objectFile=self.objectFileARMA, currentObject=self.currentObjectARMA)

                elif collect_button == 'Predictor.RNN.inputWidthSpin':
                    self.windowActive['Predictor.RNN.inputWidth'].update(int(collect_values['Predictor.RNN.inputWidthSpin']))
                elif collect_button == 'Predictor.RNN.labelWidthSpin':
                    self.windowActive['Predictor.RNN.labelWidth'].update(int(collect_values['Predictor.RNN.labelWidthSpin']))
                elif collect_button == 'Predictor.RNN.shiftSpin':
                    self.windowActive['Predictor.RNN.shift'].update(int(collect_values['Predictor.RNN.shiftSpin']))
                elif collect_button == 'Predictor.RNN.hiddenLayersSpin':
                    self.windowActive['Predictor.RNN.hiddenLayers'].update(int(collect_values['Predictor.RNN.hiddenLayersSpin']))
                elif collect_button == 'Predictor.RNN.batchSizeSpin':
                    self.windowActive['Predictor.RNN.batchSize'].update(int(collect_values['Predictor.RNN.batchSizeSpin']))
                elif collect_button == 'Predictor.RNN.maxEpochsSpin':
                    self.windowActive['Predictor.RNN.maxEpochs'].update(int(collect_values['Predictor.RNN.maxEpochsSpin']))

                elif collect_button == 'Predictor.RNN.inputWidth':
                    self.windowActive['Predictor.RNN.inputWidthSpin'].update(int(collect_values['Predictor.RNN.inputWidth']))
                elif collect_button == 'Predictor.RNN.labelWidth':
                    self.windowActive['Predictor.RNN.labelWidthSpin'].update(int(collect_values['Predictor.RNN.labelWidth']))
                elif collect_button == 'Predictor.RNN.shift':
                    self.windowActive['Predictor.RNN.shiftSpin'].update(int(collect_values['Predictor.RNN.shift']))
                elif collect_button == 'Predictor.RNN.hiddenLayers':
                    self.windowActive['Predictor.RNN.hiddenLayersSpin'].update(int(collect_values['Predictor.RNN.hiddenLayers']))
                elif collect_button == 'Predictor.RNN.batchSize':
                    self.windowActive['Predictor.RNN.batchSizeSpin'].update(int(collect_values['Predictor.RNN.batchSize']))
                elif collect_button == 'Predictor.RNN.maxEpochs':
                    self.windowActive['Predictor.RNN.maxEpochsSpin'].update(int(collect_values['Predictor.RNN.maxEpochs']))

                elif collect_button == 'Plot ARMA Prediction':
                    self.create_new_graph_window_ARMA(values=collect_values, mep=self.mep, currentObject=self.currentObjectARMA)

                # RNN Predictor Events
                elif collect_button == 'Predictor.RNN.file':
                    self.dirPathRNN = collect_values['Predictor.RNN.file']
                    self.rnn, self.objectFileRNN, self.objectDict = self.populate_object_RNN(self.windowActive, self.dirPathRNN)
                elif collect_button == 'Select Object for RNN':
                    self.currentObjectRNN = collect_values['Predictor.RNN.object']
                    # window, objectFile, currentObject, primaryVarLabelsRNN, secondaryVarLabelsRNN
                    self.display_dir_RNN(window=self.windowActive,
                                         objectFile=self.objectFileRNN,
                                         currentObject=self.currentObjectRNN,
                                         primaryVarLabelsRNN=self.primaryVarLabelsRNN,
                                         secondaryVarLabelsRNN=self.secondaryVarLabelsRNN)
                elif collect_button == 'Plot RNN Prediction':
                    print("plotting.....")
                    self.create_new_graph_window_RNN(values=collect_values,
                                                     rnn=self.rnn,
                                                     currentObject=self.currentObjectRNN,
                                                     primaryVarLabelsRNN=self.primaryVarLabelsRNN,
                                                     secondaryVarLabelsRNN=self.secondaryVarLabelsRNN)

                # NLOG Predictor Event
                elif collect_button == 'Predictor.NLOG.numComponentsSpin':
                    self.windowActive['Predictor.NLOG.numComponents'].update(int(collect_values['Predictor.NLOG.numComponentsSpin']))
                elif collect_button == 'Predictor.NLOG.maxNumParamsSpin':
                    self.windowActive['Predictor.NLOG.maxNumParams'].update(int(collect_values['Predictor.NLOG.maxNumParamsSpin']))
                elif collect_button == 'Predictor.NLOG.inputSizeSpin':
                    self.windowActive['Predictor.NLOG.inputSize'].update(int(collect_values['Predictor.NLOG.inputSizeSpin']))
                elif collect_button == 'Predictor.NLOG.maxOutputSizeSpin':
                    self.windowActive['Predictor.NLOG.maxOutputSize'].update(int(collect_values['Predictor.NLOG.maxOutputSizeSpin']))
                elif collect_button == 'Predictor.NLOG.timeHiddenUnitsSpin':
                    self.windowActive['Predictor.NLOG.timeHiddenUnits'].update(int(collect_values['Predictor.NLOG.timeHiddenUnitsSpin']))
                elif collect_button == 'Predictor.NLOG.eventsHiddenUnitsSpin':
                    self.windowActive['Predictor.NLOG.eventsHiddenUnits'].update(int(collect_values['Predictor.NLOG.eventsHiddenUnitsSpin']))
                elif collect_button == 'Predictor.NLOG.paramsHiddenUnitsSpin':
                    self.windowActive['Predictor.NLOG.paramsHiddenUnits'].update(int(collect_values['Predictor.NLOG.paramsHiddenUnitsSpin']))
                elif collect_button == 'Predictor.NLOG.timeMaxEpochsSpin':
                    self.windowActive['Predictor.NLOG.timeMaxEpochs'].update(int(collect_values['Predictor.NLOG.timeMaxEpochsSpin']))
                elif collect_button == 'Predictor.NLOG.eventsMaxEpochsSpin':
                    self.windowActive['Predictor.NLOG.eventsMaxEpochs'].update(int(collect_values['Predictor.NLOG.eventsMaxEpochsSpin']))
                elif collect_button == 'Predictor.NLOG.paramsMaxEpochsSpin':
                    self.windowActive['Predictor.NLOG.paramsMaxEpochs'].update(int(collect_values['Predictor.NLOG.paramsMaxEpochsSpin']))
                elif collect_button == 'Predictor.NLOG.timeMaxEpochsSpin':
                    self.windowActive['Predictor.NLOG.timeMaxEpochs'].update(int(collect_values['Predictor.NLOG.timeMaxEpochsSpin']))

                elif collect_button == 'Predictor.NLOG.numComponents':
                    self.windowActive['Predictor.NLOG.numComponentsSpin'].update(int(collect_values['Predictor.NLOG.numComponents']))
                elif collect_button == 'Predictor.NLOG.maxNumParams':
                    self.windowActive['Predictor.NLOG.maxNumParamsSpin'].update(int(collect_values['Predictor.NLOG.maxNumParams']))
                elif collect_button == 'Predictor.NLOG.inputSize':
                    self.windowActive['Predictor.NLOG.inputSizeSpin'].update(int(collect_values['Predictor.NLOG.inputSize']))
                elif collect_button == 'Predictor.NLOG.maxOutputSize':
                    self.windowActive['Predictor.NLOG.maxOutputSizeSpin'].update(int(collect_values['Predictor.NLOG.maxOutputSize']))
                elif collect_button == 'Predictor.NLOG.timeHiddenUnits':
                    self.windowActive['Predictor.NLOG.timeHiddenUnitsSpin'].update(int(collect_values['Predictor.NLOG.timeHiddenUnits']))
                elif collect_button == 'Predictor.NLOG.eventsHiddenUnits':
                    self.windowActive['Predictor.NLOG.eventsHiddenUnitsSpin'].update(int(collect_values['Predictor.NLOG.eventsHiddenUnits']))
                elif collect_button == 'Predictor.NLOG.paramsHiddenUnits':
                    self.windowActive['Predictor.NLOG.paramsHiddenUnitsSpin'].update(int(collect_values['Predictor.NLOG.paramsHiddenUnits']))
                elif collect_button == 'Predictor.NLOG.timeMaxEpochs':
                    self.windowActive['Predictor.NLOG.timeMaxEpochsSpin'].update(int(collect_values['Predictor.NLOG.timeMaxEpochs']))
                elif collect_button == 'Predictor.NLOG.eventsMaxEpoch':
                    self.windowActive['Predictor.NLOG.eventsMaxEpochsSpin'].update(int(collect_values['Predictor.NLOG.eventsMaxEpochs']))
                elif collect_button == 'Predictor.NLOG.paramsMaxEpochs':
                    self.windowActive['Predictor.NLOG.paramsMaxEpochsSpin'].update(int(collect_values['Predictor.NLOG.paramsMaxEpochs']))
                elif collect_button == 'Predictor.NLOG.timeMaxEpochs':
                    self.windowActive['Predictor.NLOG.timeMaxEpochsSpin'].update(int(collect_values['Predictor.NLOG.timeMaxEpochs']))
                elif collect_button == 'Execute NLOG Prediction':
                    print("Starting NLOG Predictor...")
                    self.execute_nlog_predictor(values=collect_values)

                # Report Generation
                elif collect_button == 'Refresh Report':
                    print("Refresh Report.....")
                    self.reportFlatDictionary = self.reportDictionary.getClasstoDictionary()
                    self.displayReport = pprint.pformat(self.reportFlatDictionary, indent=3, width=100)
                    self.windowActive.Element('user.report').Update(str(self.displayReport) + '\n', append=False)
                    reportItems = self.reportDictionary.getClasstoDictionary()  # self.reportDictionary.__repr__()
                    reportObj = ReportGenerator(outPath=self.locationOutput,
                                                fileName="RAADReport",
                                                logoImage=self.logoLocation,
                                                debug=self.debug)
                    reportObj.createDocumentRAAD(systemInfo=reportItems)

                # Assign Collect form Values
                elif collect_button == 'Axon Upload':
                    print("Uploading...")
                    # User Information
                    self.contentFile = collect_values['upload.content.location']
                    self.uploadMode = collect_values['uploadMode']

                    # User wants to upload the last content data file gathered to the AXON database.
                    self.uploadSuccess, self.uploadID = self.GUIUpload(self.contentFile, mode=self.uploadMode, analysisReport=self.reportDictionary)
                    print("Report: ", self.reportDictionary.getDataLakeMeta())
                    self.axonProfiler = src.software.axon.axonProfile.AxonProfile()
                    (self.axonIDs, self.axonConfig) = self.axonProfiler.GetProfile()

                # Axon Download
                elif collect_button == 'Axon Download':
                    # Check if user has chosen something
                    if collect_values['-download.choice.ID-'] == '':
                        continue
                    # User Information
                    self.downloadID = collect_values['-download.choice.ID-']
                    self.downloadDirectory = collect_values['download.location.directory']
                    # Download the File
                    # self.downloadAXONData()
                    self.axonDownloadOutput = self.GUIDownload(self.downloadID, self.downloadDirectory, analysisReport=self.reportDictionary)
                    print("Report: ", self.reportDictionary.getDataLakeMeta())
                    key = 'data.download.report'
                    self.axonProfiler = src.software.axon.axonProfile.AxonProfile()
                    (self.axonIDs, self.axonConfig) = self.axonProfiler.GetProfile()
                    print("Going into popup for Download")
                    print("doing: ", collect_values['_MULTIDEBUGOUT_'])
                    self.windowActive["data.download.report"].update(self.axonDownloadOutput)
                elif collect_button == '-download.choice.ID-':  # enable_events allows every change of choice in the dropdown to trigger this code
                    self.windowActive['-download.choice.time-'].update(self.axonConfig[collect_values['-download.choice.ID-']]['-download.choice.time-'])
                    self.windowActive['-download.choice.product-'].update(self.axonConfig[collect_values['-download.choice.ID-']]['-download.choice.product-'])
                    self.windowActive['-download.choice.serial-'].update(self.axonConfig[collect_values['-download.choice.ID-']]['-download.choice.serial-'])
                    self.windowActive['-download.choice.user-'].update(self.axonConfig[collect_values['-download.choice.ID-']]['-download.choice.user-'])

            except BaseException as exceptionLogs:
                pprint.pprint(whoami())
                print('Exception_Log():')
                print(exceptionLogs)
                print('print_exc():')
                traceback.print_exc(file=sys.stdout)
                print('print_exc(1):')
                traceback.print_exc(limit=1, file=sys.stdout)
                pass

            # Update debug windows
            if self.debug and self.firstPass is True:
                debugLocal = pprint.pformat(locals(), indent=3, width=100)
                debugGlobals = pprint.pformat(globals(), indent=3, width=100)
                displayInput = ('{0}\n{1}'.format(debugGlobals, debugLocal))
                pcollect_values = ('{0}\n'.format(collect_values))
                self.windowActive.Element('_MULTIDEBUGOUT_').Update(str(displayInput) + '\n', append=False)
                self.windowActive.Element('_MULTIEVENTOUT_').Update(str(pcollect_values) + '\n', append=True)
                PySimpleGUI.show_debugger_popout_window()  # PySimpleGUI.show_debugger_window()

        # Confirmation Box
        if self.debug:
            PySimpleGUI.PopupScrolled(pprint.pformat(collect_button, indent=3, width=100),
                                      pprint.pformat(collect_values, indent=3, width=100),
                                      size=(128, 32))
            print(pprint.pformat(collect_button, indent=3, width=100),
                  pprint.pformat(collect_values, indent=3, width=100))

        # Close window
        self.windowActive.close()
        return


def API(options=None):
    """
    API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    examples = GUIDeveloper(debug=options.debug)

    print("options: ", str(options.mode))

    if options.mode in ["1", "2", "3"]:
        examples.webAPI()  # Default simple one API
    # elif options.mode is "2":
    #    examples.API()  # Tab based API
    # elif options.mode is "3":
    #    examples.example.collect()
    #    examples.example.genericObjectGraph()
    #    examples.example.defragHistoryGraph()
    #    examples.example.RNNPredictorGraph()
    #    examples.example.ARMAPredictionGraph()
    #    examples.example.upload()
    #    examples.example.download()
    #    examples.example.profileUser()
    #    examples.example.profileApplication()
    #    examples.example.userFeedback()
    #    examples.example.neuralNetClassify()
    #    examples.example.dataTablePopulate()
    #    examples.example.debugComments(displayInput=pprint.pformat(locals(), indent=3, width=100)))
    elif options.mode == "4":
        src.software.guiOneShot.GUIOneShot(debug=False).Window()  # Tab based API
    elif options.mode == "5":
        src.software.guiOneShot.GUIOneShot(debug=False).OneShotExecuteAPI()
    elif options.mode == "Test":
        unittest.main(defaultTest='suite')
    else:
        examples.webAPI()  # Default simple one API


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default="Test", help="Mode of Operation.")
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
