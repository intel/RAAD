#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package guiLayouts
import optparse, re, os, pprint, datetime, traceback, getpass, random, string, copy
import PySimpleGUI

import src.software.TSV.DefragHistoryGrapher as DHG
import src.software.TSV.generateTSBinaries
import src.software.TSV.formatTSFiles
import src.software.axon.packageInterface
import src.software.axon.axonInterface
import src.software.axon.axonMeta
import src.software.axon.axonProfile
import src.software.access.DriveInfo
import src.software.container.basicTypes
import src.software.TSV.visualizeTS as VTS
import src.software.DP.preprocessingAPI as DP
import src.software.gui
import src.software.guiCommon


class dataTablePopulate():
    dataIn = None
    returnLayout = False
    charWidth = 25
    charHeight = 1
    debug = False

    def __init__(self, dataIn=None, returnLayout=False, charWidth=25, charHeight=1, debug=False):
        """
        Layout construction for an independent user profile.
        Args:
            dataIn: Data input into the interface to display.
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth:
            charHeight:
            debug:
        Returns: layout or input box information.
        """
        self.dataIn = dataIn
        self.returnLayout = returnLayout
        self.charWidth = charWidth
        self.charHeight = charHeight
        self.debug = debug

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

    @staticmethod
    def getDataAsArray(DataDic):
        # Initialize 2D array for meta data table
        dataTable = [
            ["Telemetry Object", "Telemetry Feature"]
        ]

        # Initialize headings
        headings = []
        telemetryFeature = None
        # Traverse dictionary and populate the table
        # For each telemetry object pulled by telemetry
        for telemetryObject in DataDic:
            try:
                # For each feature in the telemetry object
                for telemetryFeature in DataDic[telemetryObject]:
                    try:
                        # Check the keys that were pulled point to the time series array
                        # if not isinstance(DataDic[telemetryObject][telemetryFeature], list):
                        #     if self.debug: ("Not Instance: [{0}][{1}] <== {2}".format(telemetryObject, telemetryFeature, dataDictionary[telemetryObject][telemetryFeature]))
                        #     continue

                        # Add line to the table
                        dataTable.append(
                            [telemetryObject, telemetryFeature] + DataDic[telemetryObject][telemetryFeature])
                        # print([telemetryObject, telemetryFeature] + DataDic[telemetryObject][telemetryFeature])

                        # Add time tag to headings
                        if len(headings) == 0:
                            headings = ["t_" + str(i) for i in range(len(DataDic[telemetryObject][telemetryFeature]))]

                    except KeyError as errorLocal:
                        print("Nested Key Error with keys: ", telemetryObject, " and ", telemetryFeature)
                        print("Error: ", errorLocal)
                        continue

            except KeyError:
                print("Outside Key Error with key: ", telemetryObject)
                continue

            except TypeError:
                print("Weird concat at: ", telemetryObject, " --- ", telemetryFeature, " --- ",
                      DataDic[telemetryObject][telemetryFeature])
                # exit(1)

        # Add headings
        dataTable[0] = dataTable[0] + headings

        return dataTable

    @staticmethod
    def getDataDic(dataFile):
        return DP.preprocessingAPI().loadDataDict(dataFile)

    @staticmethod
    def popupTableLayout(dataArrayLocal, headings):
        return [[PySimpleGUI.Column(
            [[PySimpleGUI.Table(values=dataArrayLocal[1:][:],
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

    def popupTable(self, dataArrayLocal, programLabelLocal):
        # print("Data array: ", dataArray)
        # Get heading for the table
        headings = [str(dataArrayLocal[0][x]) for x in range(len(dataArrayLocal[0]))]
        print("headings: ", headings)

        # Get the layout for the data table
        tableLayout = self.popupTableLayout(dataArrayLocal, headings)

        tableWindow = PySimpleGUI.Window(programLabelLocal, tableLayout)

        repeatingEventLoop = True
        while repeatingEventLoop:
            (collect_button_local, collect_values_local) = tableWindow.read()

            if collect_button_local is PySimpleGUI.WIN_CLOSED or collect_button_local == 'Cancel':
                repeatingEventLoop = False

        # Close the spawned window
        tableWindow.close()

    def make_table(self, num_rows=1, num_cols=1):
        """
        Generation of tables.
        Args:
            num_rows: Number of rows to generate.
            num_cols: Number of columns to generate
        Returns: None
        """
        dataCreate = [[j for j in range(num_cols)] for _ in range(num_rows)]
        dataCreate[0] = [self.word() for _ in range(num_cols)]
        for i in range(1, num_rows):
            dataCreate[i] = [self.word(), *[self.number() for i in range(num_cols - 1)]]
        return dataCreate

    def main(self):
        # Input Verification
        dataInTable = copy.deepcopy(self.dataIn)
        if dataInTable is None or dataInTable is []:
            # Make data table
            dataInTable = self.make_table(num_rows=8, num_cols=4)
            if self.debug:
                pprint.pprint(dataInTable)

        if self.charWidth < 5:
            self.charWidth = 25
        if self.charHeight < 1:
            self.charHeight = 1

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if self.returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [[PySimpleGUI.Text('Telemetry Data Table', font=("Arial Bold", 16))],
                  [PySimpleGUI.Text('Decoded *.ini File', size=(self.charWidth, self.charHeight), auto_size_text=False),
                   PySimpleGUI.InputText(default_text=str(os.getcwd()), key='data.telemetry.table.file'),
                   PySimpleGUI.FileBrowse(file_types=(("INI Files", "*.ini"),),
                                          target='data.telemetry.table.file')],
                  [PySimpleGUI.Text('Choose Object to decode or choose all'),
                   PySimpleGUI.InputCombo(["all"],
                                          size=(16, 1),
                                          key='data.telemetry.table.choice',
                                          default_value='all',
                                          tooltip='Choice of uid to display in a table')]
                  ]

        if self.returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Button('Decode', button_color=('white', 'blue'))])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)

        repeatEventLoop = True
        collect_button = None
        collect_values = None
        while repeatEventLoop:
            (collect_button, collect_values) = windowActive.read()

            if collect_button is PySimpleGUI.WIN_CLOSED or collect_button == 'Cancel':
                repeatEventLoop = False
            elif collect_button == 'Read':
                # Check the file is real
                if os.path.exists(collect_values["dataDirInput"]):
                    # Get dictionary of the chosen file
                    dataArray = self.getDataAsArray(self.getDataDic(collect_values["dataDirInput"]))

                    # Create table and spawn new window for it
                    self.popupTable(dataArrayLocal=dataArray, programLabelLocal=programLabel)

                    repeatEventLoop = False

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        print(collect_button, collect_values)

        return (collect_values)


class GUILayouts():
    """
    List of example tabs for the baseline application.
    """
    debug = False

    def __init__(self, debug=False):
        self.debug = debug

    @staticmethod
    def profileUser(returnLayout=False, charWidth=25, charHeight=1,
                    identity=None,
                    name=None,
                    mode=None,
                    keyLoc=None,
                    encryptionStatus=None,
                    workingDir=None):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            identity: unique identification number for a  given application.
            name: String name of the application.
            mode: Operation mode of the given application.
            keyLoc: Location on the user system of the application.
            encryptionStatus: Flag to determine if the user is currently using encryption on the telemetry data.
            workingDir: The preferred working location for saving and managing telemetry data.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        if identity is None:
            identity = '1234567'
        if name is None:
            name = 'DarthVader'
        if mode is not None:
            mode = 'GUI'
        if keyLoc is None:
            keyLoc = os.getcwd()
        if encryptionStatus is None:
            encryptionStatus = False
        if workingDir is None:
            workingDir = os.getcwd()

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [
            [PySimpleGUI.Text('Please enter your User profile information')],

            [PySimpleGUI.Text('Enter identity number', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=identity, key='identity')],

            [PySimpleGUI.Text('Enter username', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=name, key='name')],

            [PySimpleGUI.Text('Enter mode', size=(charWidth, charHeight)),
             PySimpleGUI.InputCombo(('cmd', 'gui'), default_value=mode, key='mode', size=(charWidth, charHeight))],

            [PySimpleGUI.Text('Key encrypt-decrypt location', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=keyLoc, key='keyLoc'), PySimpleGUI.FolderBrowse()],

            [PySimpleGUI.Text('Enable Encryption', size=(charWidth, charHeight)),
             PySimpleGUI.InputCombo(('True', 'False'), default_value=str(encryptionStatus), key='encryptionStatus',
                                    size=(charWidth, charHeight))],

            [PySimpleGUI.Text('Enter working directory', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=workingDir, key='workingDir'), PySimpleGUI.FolderBrowse()]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            # User Information
            identity = int(collect_values['identity'])
            name = str(collect_values['name'])
            mode = str(collect_values['mode'])
            keyLoc = str(collect_values['keyLoc'])
            encryptionStatus = str(collect_values['encryptionStatus'])
            workingDir = str(collect_values['workingDir'])
        else:
            identity = None
            name = None
            mode = None
            keyLoc = None
            encryptionStatus = None
            workingDir = None

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        # print(collect_button, collect_values)
        return (identity, name, mode, keyLoc, encryptionStatus, workingDir)

    @staticmethod
    def profileApplication(returnLayout=False, charWidth=25, charHeight=1,
                           identity=None,
                           major=None,
                           minor=None,
                           name=None,
                           location=None,
                           mode=None,
                           url=None):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            identity: unique identification number for a  given application.
            major: Major version section to represent a unique organization of app-data.
            minor: Minor version section to represent an extension of the organization of app-data.
            name: String name of the application.
            location: Location on the user system of the application.
            mode: Operation mode of the given application.
            url: Application address for accessing data.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1

        if identity is None:
            identity = 1
        if major is None:
            major = 1
        if minor is None:
            minor = 1
        if name is None:
            name = 'raad'
        if location is None:
            location = os.getcwd()
        if mode is None:
            mode = 'GUI'
        if url is None:
            url = 'http://www.intel.com'
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        identityPrefix = ('application' + str(identity) + '_')
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [
            [PySimpleGUI.Text('Please enter your Application information')],

            [PySimpleGUI.Text('Enter identity number', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=identity, key=(identityPrefix + 'identity'))],

            [PySimpleGUI.Text('Enter major version number', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=major, key=(identityPrefix + 'major'))],

            [PySimpleGUI.Text('Enter minor version number', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=minor, key=(identityPrefix + 'minor'))],

            [PySimpleGUI.Text('Enter name', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=name, key=(identityPrefix + 'name'))],

            [PySimpleGUI.Text('Execution location', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=location, key=(identityPrefix + 'location')),
             PySimpleGUI.FolderBrowse()],

            [PySimpleGUI.Text('Enter mode', size=(charWidth, charHeight)),
             PySimpleGUI.InputCombo(('cmd', 'gui'), default_value=mode, key=(identityPrefix + 'mode'),
                                    size=(charWidth, charHeight))],

            [PySimpleGUI.Text('Enter URL', size=(charWidth, charHeight)),
             PySimpleGUI.InputText(default_text=url, key=(identityPrefix + 'url'))]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            # User Information
            identity = int(collect_values[identityPrefix + 'identity'])
            major = int(collect_values[identityPrefix + 'major'])
            minor = int(collect_values[identityPrefix + 'minor'])
            name = str(collect_values[identityPrefix + 'name'])
            location = str(collect_values[identityPrefix + 'location'])
            mode = str(collect_values[identityPrefix + 'mode'])
            url = str(collect_values[identityPrefix + 'url'])
        else:
            identity = None
            major = None
            minor = None
            name = None
            location = None
            mode = None
            url = None

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        print(collect_button, collect_values)

        return (identity, major, minor, name, location, mode, url)

    @staticmethod
    def collect(returnLayout=False, charWidth=20, charHeight=1, debug=False):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            debug: debug print flag.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 20
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################

        layout = [[PySimpleGUI.Text('Usage Case for Intel', size=(charWidth, charHeight)),
                   PySimpleGUI.InputCombo(('CLI', 'TWIDL', 'IMAS', 'PARSE'),
                                          key='toolChoice',
                                          default_value='CLI',
                                          tooltip='CLI is the NVMe-CLI Open Source Tool. TWIDL is the Intel internal tool. IMAS is the Intel Memory and Storage Tool')],
                  [PySimpleGUI.Text('SSD Selection Number', size=(charWidth, charHeight)),
                   PySimpleGUI.InputText(default_text='1', key='ssdChoice', size=(charWidth, charHeight))],
                  [PySimpleGUI.Text('Input Working directory', size=(charWidth, charHeight), auto_size_text=False),
                   PySimpleGUI.InputText(default_text=str(os.getcwd()), key='workingDirInput'),
                   PySimpleGUI.FolderBrowse()],
                  [PySimpleGUI.Text('Firmware Parsers directory', size=(charWidth, charHeight),
                                    auto_size_text=False),
                   PySimpleGUI.InputText(default_text=str(os.getcwd()), key='fwParsers'),
                   PySimpleGUI.FolderBrowse()],
                  [PySimpleGUI.Text('Output Working directory', size=(charWidth, charHeight), auto_size_text=False),
                   PySimpleGUI.InputText(default_text=str(os.getcwd()), key='workingDirOutput'),
                   PySimpleGUI.FolderBrowse()],
                  [PySimpleGUI.Text('Number of Queries', size=(charWidth, charHeight)),
                   PySimpleGUI.InputText(default_text='10', key='numberOfQueries', size=(charWidth, charHeight))],
                  [PySimpleGUI.Text('Time frame to collect', size=(charWidth, charHeight)),
                   PySimpleGUI.InputText(default_text='60', key='timeFrame', size=(charWidth, charHeight))]
                  ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            # User Information
            toolChoice = str(collect_values['toolChoice'])
            ssdChoice = str(collect_values['ssdChoice'])
            workingDirInput = str(collect_values['workingDirInput'])
            fwParsers = str(collect_values['fwParsers'])
            workingDirOutput = str(collect_values['workingDirOutput'])
            numberOfQueries = int(collect_values['numberOfQueries'])
            timeFrame = int(collect_values['timeFrame'])

            # Translation for mode field
            modeTranslate = {"CLI": 1, "TWIDL": 2, "IMAS": 4}

            # Get timestamp for start of collecting
            timeStamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")

            # Define most recent data file name
            dataFileName = "time-series_" + timeStamp + ".ini"

            # Collect telemetry
            print("Going into generate binaries")
            generateTS = src.software.TSV.generateTSBinaries.generateTSBinaries(outpath=workingDirOutput,
                                                                                iterations=numberOfQueries)
            generateTS.generateTSBinariesAPI(mode=modeTranslate[toolChoice], driveNumber=ssdChoice,
                                             inputFolder=workingDirInput, time=timeFrame)

            # Format collected telemetry
            formatTS = src.software.TSV.formatTSFiles.formatTSFiles(outpath=workingDirOutput)
            formatTS.formatTSFilesAPI(fwDir=fwParsers, binDir=workingDirOutput, outfile=dataFileName, mode=2)

            # Compress created files
            zipName = "GatherData_" + timeStamp + ".zip"
            src.software.axon.packageInterface.packageInterface(absPath=workingDirOutput, debug=debug).createZIP(
                zipFileName=zipName)

        else:
            toolChoice = None
            ssdChoice = None
            workingDirInput = None
            workingDirOutput = None
            numberOfQueries = None
            timeFrame = None

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        print(collect_button, collect_values)

        return (toolChoice, ssdChoice, workingDirInput, workingDirOutput, numberOfQueries, timeFrame)

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
        hostMeta["timeStamp"] = datetime.datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%S:%f")  # Uses same format as given in axonMeta.py

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

        if not os.path.exists(contentFile):
            print("File not found: ", contentFile)
            return False, 0

        axonInt = src.software.axon.axonInterface.Axon_Interface(mode=mode)

        metaData, metaDataFile = self.formMetaData(axonInt=axonInt, contentFile=contentFile)

        success, axonID = axonInt.sendInfo(metaDataFile=metaDataFile, contentFile=contentFile)

        print("axonID: ", axonID)

        if success:
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

    def upload(self, returnLayout=False, charWidth=25, charHeight=1):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
        Returns: layout or input box information.
        """
        if charWidth < 5:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic upload form.
        # Return values as a list.
        ###############################################################################
        layout = [
            [PySimpleGUI.Text('Please enter your upload Destination and the file you wish to upload')],
            [PySimpleGUI.Text('Content File', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=os.path.join(str(os.getcwd()), 'time-seris.ini'),
                                   key='upload.content.location'),
             PySimpleGUI.FileBrowse(file_types=(("ALL Files", "*.ini"),),
                                    initial_folder=os.path.join(str(os.getcwd()), 'time-seris.ini'))],
            [PySimpleGUI.InputCombo(('test', 'production', 'development'), default_value='test',
                                    key='upload.content.mode',
                                    size=(charWidth - 5, charHeight + 3))]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )

        # Display collect form
        windowActiveUpload = PySimpleGUI.Window(programLabel, layout)
        upload_button = None
        upload_values = None
        uploadMode = None
        uploadSuccess = None
        uploadID = None
        ContinueWindow = True
        while ContinueWindow:
            (upload_button, upload_values) = windowActiveUpload.read()

            # Assign Collect form Values
            if upload_button == 'Submit':
                print("Uploading...")
                # User Information
                contentFile = upload_values['upload.content.location']
                uploadMode = upload_values['upload.content.mode']

                # Upload the content file
                uploadSuccess, uploadID = self.GUIUpload(contentFile, mode=uploadMode)
                ContinueWindow = False
            elif upload_button == PySimpleGUI.WIN_CLOSED or upload_button == 'Cancel':
                ContinueWindow = False
                uploadMode = None
            else:
                uploadMode = None

        # Confirmation Box
        PySimpleGUI.Popup("uploadMode: " + uploadMode,
                          "uploadSuccess: " + str(uploadSuccess),
                          "uploadID: " + str(uploadID))

        # Close window
        windowActiveUpload.close()

        # Printing Selection
        print(upload_button, upload_values)
        return uploadMode, uploadSuccess, uploadID

    def download(self, returnLayout=False, charWidth=25, charHeight=1):
        """
        Layout construction for downloading AXON data
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
        Returns: layout or input box information.
        """

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        axonProfiler = src.software.axon.axonProfile.AxonProfile()
        axonIDs, axonConfig = axonProfiler.GetProfile()

        if charWidth < 5:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic upload form.
        # Return values as a list.
        ###############################################################################
        layout = [
            [PySimpleGUI.Text('Choose download directory', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=str(os.getcwd()), key='download.location.directory'),
             PySimpleGUI.FolderBrowse()],
            [PySimpleGUI.Text('Please choose your desired AXON upload')],
            [PySimpleGUI.InputCombo(('test', 'production', 'development'), default_value='test',
                                    key="download.content.mode")],
            [PySimpleGUI.InputCombo(axonIDs, enable_events=True, default_value='', key='-download.choice.ID-',
                                    size=(charWidth - 5, charHeight + 3))],
            [PySimpleGUI.Text('Time created:'), PySimpleGUI.Text(size=(15, 1), key='-download.choice.time-')],
            [PySimpleGUI.Text('Product Name:'), PySimpleGUI.Text(size=(15, 1), key='-download.choice.product-')],
            [PySimpleGUI.Text('Serial Number:'), PySimpleGUI.Text(size=(15, 1), key='-download.choice.serial-')],
            [PySimpleGUI.Text('User:'), PySimpleGUI.Text(size=(15, 1), key='-download.choice.user-')]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )

        # Display collect form
        windowActiveDownload = PySimpleGUI.Window(programLabel, layout)
        download_button = None
        download_values = None
        ContinueWindow = True
        while ContinueWindow:
            (download_button, download_values) = windowActiveDownload.read()

            print("buttons: ", download_button)
            print("values: ", download_values)

            # Assign Collect form Values
            if download_button == 'Submit':
                # Check if user has chosen something
                if download_values['-download.choice.ID-'] == '':
                    continue

                # User Information
                downloadID = download_values['-download.choice.ID-']
                downloadDirectory = download_values['download.location.directory']

                ContinueWindow = False

                # Download the File
                exitCode, cmdOutput, cmdError = self.GUIDownload(downloadID, downloadDirectory)

                print("exitCode: ", exitCode)
                print("cmdOutput: ", cmdOutput)
                print("cmdError: ", cmdError)

            elif download_button == PySimpleGUI.WIN_CLOSED or download_button == 'Cancel':

                ContinueWindow = False
            elif download_button == '-download.choice.ID-':  # enable_events allows every change of choice in the dropdown to trigger this code

                windowActiveDownload['-download.choice.time-'].update(
                    axonConfig[download_values['-download.choice.ID-']]['-download.choice.time-'])
                windowActiveDownload['-download.choice.product-'].update(
                    axonConfig[download_values['-download.choice.ID-']]['-download.choice.product-'])
                windowActiveDownload['-download.choice.serial-'].update(
                    axonConfig[download_values['-download.choice.ID-']]['-download.choice.serial-'])
                windowActiveDownload['-download.choice.user-'].update(
                    axonConfig[download_values['-download.choice.ID-']]['-download.choice.user-'])

        # Downloaded ID
        downloadID = download_values['-download.choice.ID-']

        # Confirmation Box
        PySimpleGUI.Popup(download_button, download_values)

        # Close window
        windowActiveDownload.close()

        # Printing Selection
        print(download_button, download_values)
        return downloadID

    @staticmethod
    def userFeedback(returnLayout=False, charWidth=25, charHeight=1):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic User feedback form.
        # Return values as a list.
        ###############################################################################
        layout = [[PySimpleGUI.Text('_' * 80)],
                  [PySimpleGUI.Text('User Feedback Comments', size=(charWidth + 10, charHeight))],
                  [PySimpleGUI.Multiline(default_text='Please provide feedback based on experience',
                                         key='feedbackComment', size=(charWidth + 10, charHeight + 3))]
                  ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )

        # Display collect form
        windowActiveFeedback = PySimpleGUI.Window(programLabel, layout)
        (layout_button, layout_values) = windowActiveFeedback.read()

        # Assign Collect form Values
        if layout_values == 'Submit':
            # User Information
            feedbackComment = int(layout_values['feedbackComment'])
        else:
            feedbackComment = None

        # Confirmation Box
        PySimpleGUI.Popup(layout_button, layout_values)

        # Close window
        windowActiveFeedback.close()

        # Printing Selection
        print(layout_button, layout_values)

        return feedbackComment

    @staticmethod
    def debugComments(returnLayout=False, displayInput=None, charWidth=93, charHeight=26, visible=True):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            displayInput: Strings variables to Display.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            visible: Visiblity of the given object.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic User feedback form.
        # Return values as a list.
        ###############################################################################
        layout = [[PySimpleGUI.Text('Dump Information', visible=visible)],
                  [PySimpleGUI.Multiline(default_text=str(displayInput),
                                         size=(charWidth, charHeight),
                                         autoscroll=True,
                                         do_not_clear=True,
                                         visible=visible)],
                  ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )

        # Display collect form
        windowActiveFeedback = PySimpleGUI.Window(programLabel, layout)
        (layout_button, layout_values) = windowActiveFeedback.read()

        # Close window
        windowActiveFeedback.close()

        # Printing Selection
        print(layout_button, layout_values)

        return None

    @staticmethod
    def ARMAPredictionGraph(returnLayout=False):
        """
        function for generating the graphical interface window for graphing media error predictions

        Args:
            returnLayout: Boolean flag to access the graphing layout produced in the function

        Returns:
            layout:  None or the layout of the window

        """

        def display_dir(windowLocal, objectFileLocal, currentObjectLocalVar):
            """
            function for updating the values contained in the drop down menus for tracking variables

            Args:
                windowLocal: window instance
                objectFileLocal: ObjectConfig instance
                currentObjectLocalVar: String for the name of the current object

            Returns:

            """
            trackingVars = objectFileLocal.dataDict[currentObjectLocalVar].keys()
            trackingVars = ["None"] + list(trackingVars)
            windowLocal['-FIELD-'].Update(values=trackingVars)

        def populate_object(windowLocal, dirPathLocal):
            """
            function for populating the ObjectConfig instance and updating the drop down menu for the objects
            available in the configuration file

            Args:
                windowLocal: window instance
                dirPathLocal: String for the path to the configuration file

            Returns:
                mepLocal: MediaErrorPredictor instance
                objectFile: ObjectConfig instance
            """
            objectFileLocal = src.software.guiCommon.ObjectConfigARMA(str(dirPathLocal))
            mep_Local = objectFile.readConfigContent()
            dataKeys = ["None"] + list(objectFileLocal.dataDict.keys())
            windowLocal["-OBJECT-"].Update(values=dataKeys)
            return mep_Local, objectFileLocal

        def create_new_graph_window(values_Local, mep_Local, currentObject_Local):
            """
            function for generating a new graph window using the matplot functionality of PySimpleGUI

            Args:
                values_Local: List of values collected from window
                mep_Local: MediaErrorPredictor instance
                currentObject_Local: String for the name of the current object

            Returns:

            """

            subSeqLen = int(values_Local['-SSL-'])
            matrixProfile = values_Local['-MATRIX-']
            currentField = values_Local['-FIELD-']
            matrixProfileFlag = False
            if matrixProfile == "Yes":
                matrixProfileFlag = True
            elif matrixProfile == "No":
                matrixProfileFlag = False

            mep_Local.setMatrixProfileFlag(matrixProfileFlag, subSeqLen=subSeqLen)
            mep_Local.ARMAModel(currentObject_Local, currentField)

        primaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(50, 1), key='-FIELD-')]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variable',
            tooltip='Select the names for the variable to be graphed in the main axis')

        # Window layout
        layout = [
            [PySimpleGUI.Text('Media Error Prediction Plot', justification='center', size=(65, 1),
                              relief=PySimpleGUI.RELIEF_SUNKEN)],
            [PySimpleGUI.Text('Browse Configuration File', size=(25, 1)),
             PySimpleGUI.In(key='-FILE-', enable_events=True, size=(25, 1)),
             PySimpleGUI.FileBrowse(size=(10, 1), target='-FILE-', file_types=(("INI Files", "*.ini"),))],
            [PySimpleGUI.Text('Object Name', size=(25, 1)),
             PySimpleGUI.Drop(values=(), auto_size_text=True, size=(23, 1), key='-OBJECT-',
                              enable_events=True),
             PySimpleGUI.Button('Select', size=(10, 1))],
            [PySimpleGUI.Text('Select tracking variable', size=(50, 1))],
            [primaryFrame],
            [PySimpleGUI.Text('Length of Window to be considered for Matrix Profile')],
            [PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0, key='-SSL-')],
            [PySimpleGUI.Text('Get the matrix profile for the data?')],
            [PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-MATRIX-',
                              enable_events=True)]
        ]
        if returnLayout is True:
            return layout

        layout.append([PySimpleGUI.Button('Plot', size=(10, 1))])

        window = PySimpleGUI.Window('Media Error Prediction Visualizer', layout)
        mepLocal = None
        objectFile = None
        currentObjectLocal = None
        while True:
            event, valuesLocal = window.read()
            if event is PySimpleGUI.WIN_CLOSED:
                break
            elif event == '-FILE-':
                dirPath = valuesLocal['-FILE-']
                mepLocal, objectFile = populate_object(window, dirPath)
            elif event == 'Select':
                currentObjectLocal = valuesLocal['-OBJECT-']
                display_dir(window, objectFile, currentObjectLocal)
            elif event == 'Plot':
                print("plotting.....")
                create_new_graph_window(valuesLocal, mepLocal, currentObjectLocal)
        window.close()
        return

    @staticmethod
    def RNNPredictorGraph(returnLayout=False):
        """
        function for generating the graphical interface window for graphing an RNN time series predictor object

        Args:
            returnLayout: Boolean flag to access the graphing layout produced in the function

        Returns:
            layout:  None or the layout of the window

        """
        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-", "-PFOVAR-", "-PFIVAR-"]
        secondaryVarLabels = ["-SFVAR-"]

        def display_dir(windowLocal, objectFileLocal, currentObject_Local):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                windowLocal: window instance
                objectFileLocal: ObjectConfig instance
                currentObject_Local: String for the name of the current object

            Returns:

            """
            trackingVars = objectFileLocal.dataDict[currentObject_Local].keys()
            primaryVars = ["None"] + list(trackingVars)
            secondaryVars = ["None"] + list(trackingVars)
            for name in primaryVarLabels:
                windowLocal[name].Update(values=primaryVars)
            for name in secondaryVarLabels:
                windowLocal[name].Update(values=secondaryVars)

        def populate_object(windowLocal, dirPathLocal):
            """
            function for populating the ObjectConfig instance and updating the drop down menu for the objects
            available in the configuration file

            Args:
                windowLocal: window instance
                dirPathLocal: String for the path to the configuration file

            Returns:
                rnn: mediaPredictionRNN instance
                objectFile: ObjectConfig instance
                objectList: list of object names (ex. ThermalSensor)
            """
            objectFileLocal = src.software.guiCommon.ObjectConfigRNN(str(dirPathLocal))
            rnn_Local = objectFile.readConfigContent(debug=True)
            objectList = list(objectFile.objectIDs)
            windowLocal["-OBJECT-"].Update(values=objectList)
            return rnn_Local, objectFileLocal, objectList

        def is_data_selected_from_fields(listLocal):
            """
            function for checking if data has been selected for a list

            Args:
                listLocal: list of data values

            Returns:
                Boolean indicating whether the list contains any data

            """
            return (len(listLocal) > 0)

        def check_flag(flag):
            """
            function for checking the value of a yes/no drop-down and returning the boolean value associated with
            the answer

            Args:
                flag: string representation of Yes/No option

            Returns:
               booleanFlag: Boolean value for selected option ("Yes" = True, "No" = False)
            """
            booleanFlag = False
            if flag == "Yes":
                booleanFlag = True
            elif flag == "No":
                booleanFlag = False

            return booleanFlag

        def create_new_graph_window(values_Local, rnn_Local, currentObject_Local):
            """
            function for generating a new graph window using the matplot functionality of PySimpleGUI

            Args:
                values_Local: List of values collected from window
                rnn_Local: mediaPredictionRNN instance
                currentObject_Local: String for the name of the current object (ex. uid-6)

            Returns:

            """
            trackingVars = []
            plotVars = []

            for name in primaryVarLabels:
                if values_Local[name] != "None":
                    trackingVars.append(values_Local[name])

            for name in secondaryVarLabels:
                if values_Local[name] != "None":
                    plotVars.append(values_Local[name])

            if is_data_selected_from_fields(trackingVars):
                inputWidth = int(values_Local['-INPUTWIDTH-'])
                labelWidth = int(values_Local['-LABELWIDTH-'])
                shift = int(values_Local['-SHIFT-'])
                hiddenLayers = int(values_Local['-HLAYERS-'])
                subSeqLen = int(values_Local['-SSL-'])
                batchSize = int(values_Local['-BS-'])
                maxEpochs = int(values_Local['-ME-'])
                matrixProfile = values_Local['-MATRIX-']
                embeddedEncoding = values_Local['-EE-']
                categoricalEncoding = values_Local['-CE-']
                matrixProfileFlag = check_flag(matrixProfile)
                embeddedEncodingFlag = check_flag(embeddedEncoding)
                categoricalEncodingFlag = check_flag(categoricalEncoding)

                rnn_Local.setMatrixProfile(value=matrixProfileFlag, subSeqLen=subSeqLen)
                rnn_Local.setEmbeddedEncoding(value=embeddedEncodingFlag)
                rnn_Local.setCategoricalEncoding(value=categoricalEncodingFlag)
                rnn_Local.timeSeriesPredictorAPI(inputWidth, labelWidth, shift, batchSize, hiddenLayers, currentObject_Local,
                                                 trackingVars, plotVars[0], maxEpochs)

        primaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('First Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PFVAR-', enable_events=True)],
            [PySimpleGUI.Text('Second Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PSVAR-', enable_events=True)],
            [PySimpleGUI.Text('Third Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PTVAR-', enable_events=True)],
            [PySimpleGUI.Text('Fourth Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PFOVAR-', enable_events=True)],
            [PySimpleGUI.Text('Fifth Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PFIVAR-', enable_events=True)],
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Input Variables',
            tooltip='Select the names for the field variables to be fed into the neural networks as time series')

        secondaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('Plot Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-SFVAR-', enable_events=True)]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Plot Variable',
            tooltip='Select the name for the variable to be graphed in the main axis')

        # Window layout
        layout = [
            [PySimpleGUI.Text('Time Series Prediction Plot', justification='center', size=(80, 1),
                              relief=PySimpleGUI.RELIEF_SUNKEN)],
            [PySimpleGUI.Text('Browse Configuration File', size=(25, 1)),
             PySimpleGUI.In(key='-FILE-', enable_events=True),
             PySimpleGUI.FileBrowse(size=(10, 1), target='-FILE-', file_types=(("ALL Files", "*.ini"),))],
            [PySimpleGUI.Text('Object Name', size=(25, 1)),
             PySimpleGUI.Drop(values=(), auto_size_text=True, size=(10, 1), key='-OBJECT-',
                              enable_events=True),
             PySimpleGUI.Button('Select', size=(10, 1))],
            [PySimpleGUI.Text('Select Field variables', size=(25, 1)),
             PySimpleGUI.Text('Select Plot variable', size=(25, 1))],
            [primaryFrame, secondaryFrame],
            [PySimpleGUI.Text('Input Width', size=(40, 1)), PySimpleGUI.Text('Label Width', size=(40, 1))],
            [PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0,
                                key='-INPUTWIDTH-'),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0,
                                key='-LABELWIDTH-')],
            [PySimpleGUI.Text('Shift', size=(40, 1)), PySimpleGUI.Text('Neurons Per Hidden Layer', size=(40, 1))],
            [PySimpleGUI.Slider(range=(0, 50), orientation='h', size=(35, 20), default_value=0,
                                key='-SHIFT-'),
             PySimpleGUI.Slider(range=(2, 512), orientation='h', size=(35, 20), default_value=2,
                                key='-HLAYERS-')],
            [PySimpleGUI.Text('Batch Size', size=(40, 1)), PySimpleGUI.Text('Max Epochs', size=(40, 1))],
            [PySimpleGUI.Slider(range=(2, 128), orientation='h', size=(35, 20), default_value=32,
                                key='-BS-'),
             PySimpleGUI.Slider(range=(1, 20000), orientation='h', size=(35, 20), default_value=200,
                                key='-ME-')],
            [PySimpleGUI.Text('Categorical Encoding for Data?', size=(25, 1)),
             PySimpleGUI.Text('Embedded Encoding for Data?', size=(25, 1))],
            [PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-CE-',
                              enable_events=True),
             PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-EE-',
                              enable_events=True)],
            [PySimpleGUI.Text('Get the matrix profile for the data?'),
             PySimpleGUI.Text('Length of Window to be considered for Matrix Profile')],
            [PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-MATRIX-',
                              enable_events=True),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0, key='-SSL-')]
        ]
        if returnLayout is True:
            return layout

        layout.append([PySimpleGUI.Button('Plot', size=(10, 1))])

        window = PySimpleGUI.Window('Defrag History Visualizer', layout)
        rnnLocal = None
        objectFile = None
        currentObjectLocal = None
        while True:
            event, valuesLocal = window.read()
            if event is PySimpleGUI.WIN_CLOSED:
                break
            elif event == '-FILE-':
                dirPath = valuesLocal['-FILE-']
                rnnLocal, objectFile, objectDict = populate_object(window, dirPath)
            elif event == 'Select':
                currentObjectLocal = valuesLocal['-OBJECT-']
                display_dir(window, objectFile, currentObjectLocal)
            elif event == 'Plot':
                print("plotting.....")
                create_new_graph_window(valuesLocal, rnnLocal, currentObjectLocal)
        window.close()
        return

    @staticmethod
    def defragHistoryGraph(returnLayout=False):
        """
        function for generating the graphical interface window for graphing a defragHistory object

        Args:
            returnLayout: Boolean flag to access the graphing layout produced in the function

        Returns:
            layout:  None or the layout of the window

        """
        setPointLabelsDict = {"-START-": "start", "-NORMAL-": "normal", "-CORNER-": "corner", "-URGENT-": "urgent",
                              "-CRITICAL-": "critical"}
        primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-"]
        secondaryVarLabels = ["-SFVAR-", "-SSVAR-", "-STVAR-"]

        def display_dir(windowLocal, dirPathLocal, modeLocal):
            """
            function for updating the values contained in the drop down menus for primary and secondary variables

            Args:
                windowLocal: window instance
                dirPathLocal: String for the path to the configuration file
                modeLocal: Integer for the mode of operation (1=ADP, 2=CDR)

            Returns:
                dhg: DefragHistoryGrapher instance
                dhFile: DefragConfig instance

            """
            dhFileLocal = src.software.guiCommon.DefragConfig(str(dirPathLocal), modeLocal)
            dhgLocal = dhFileLocal.readConfigContent()
            primaryVars = ["None"] + list(dhFileLocal.trackingVars)
            secondaryVars = ["None"] + list(dhFileLocal.secondaryVars)
            for name in primaryVarLabels:
                windowLocal[name].Update(values=primaryVars)
            for name in secondaryVarLabels:
                windowLocal[name].Update(values=secondaryVars)
            return dhgLocal, dhFileLocal

        def is_data_selected_from_fields(listVar):
            """
            function for checking if data has been selected for a list

            Args:
                listVar: list of data values

            Returns:

            """
            return (len(listVar) > 0)

        def create_new_graph_window(valuesLocal, dhgLocal, dhFileLocal):
            """
            function for generating a new graph window using the matplot functionality of PySimpleGUI

            Args:
                valuesLocal: List of values collected from window
                dhgLocal: DefragHistoryGrapher instance
                dhFileLocal: DefragConfig instance

            Returns:

            """
            setPoints = []
            trackingVars = []
            secondaryVars = []
            for name in setPointLabelsDict.keys():
                if valuesLocal[name] is True:
                    setPoints.append(setPointLabelsDict[name])

            for name in primaryVarLabels:
                if valuesLocal[name] != "None":
                    trackingVars.append(valuesLocal[name])

            for name in secondaryVarLabels:
                if valuesLocal[name] != "None":
                    secondaryVars.append(valuesLocal[name])

            if is_data_selected_from_fields(trackingVars):

                dhgLocal.setSetPointNames(setPoints)
                dhgLocal.setTrackingNames(trackingVars)
                dhgLocal.setSecondaryVars(secondaryVars)

                dataDict = dhFileLocal.vizDict
                object_t = "uid-41"
                numCores = valuesLocal['-CORES-']
                bandwidth = valuesLocal['-BANDWIDTH-']
                bandwidthFlag = False
                if bandwidth == "Yes":
                    bandwidthFlag = True
                elif bandwidth == "No":
                    bandwidthFlag = False
                driveNameLocal = valuesLocal['-DRIVE-']
                start = valuesLocal['-SSTART-']
                end = valuesLocal['-END-']
                if driveNameLocal == "ADP":
                    dhgLocal.generateTSVisualizationADP(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                        start=start, end=end)
                elif driveNameLocal == "CDR":
                    dhgLocal.generateTSVisualizationCDR(object_t, dataDict, bandwidthFlag, numCores=numCores,
                                                        start=start, end=end)

        checkboxFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Checkbox('start', size=(20, 1), key='-START-')],
            [PySimpleGUI.Checkbox('normal', size=(20, 1), key='-NORMAL-')],
            [PySimpleGUI.Checkbox('corner', size=(20, 1), key='-CORNER-')],
            [PySimpleGUI.Checkbox('urgent', size=(20, 1), key='-URGENT-')],
            [PySimpleGUI.Checkbox('critical', size=(20, 1), key='-CRITICAL-')],
        ], title='Set Points', relief=PySimpleGUI.RELIEF_SUNKEN, tooltip='Select set points to be graphed')

        primaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('First Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PFVAR-', enable_events=True)],
            [PySimpleGUI.Text('Second Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PSVAR-', enable_events=True)],
            [PySimpleGUI.Text('Third Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PTVAR-', enable_events=True)]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variables',
            tooltip='Select the names for the variables to be graphed in the main axis')

        secondaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('First Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-SFVAR-', enable_events=True)],
            [PySimpleGUI.Text('Second Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-SSVAR-', enable_events=True)],
            [PySimpleGUI.Text('Third Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-STVAR-', enable_events=True)]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Secondary Variables',
            tooltip='Select the names for the variables to be graphed in the secondary axis')

        # Window layout
        layout = [
            [PySimpleGUI.Text('Defrag History Plot', justification='center', size=(80, 1),
                              relief=PySimpleGUI.RELIEF_SUNKEN)],
            [PySimpleGUI.Text('Drive Type', size=(25, 1)),
             PySimpleGUI.Drop(values=('ADP', 'CDR'), auto_size_text=True, size=(10, 1), key='-DRIVE-',
                              enable_events=True, default_value='ADP')],
            [PySimpleGUI.Text('Browse Configuration File', size=(25, 1)),
             PySimpleGUI.In(key='-FILE-', enable_events=True),
             PySimpleGUI.FileBrowse(size=(10, 1), target='-FILE-', file_types=(("INI Files", "*.ini"),))],
            [PySimpleGUI.Text('Select set points', size=(25, 1)),
             PySimpleGUI.Text('Select tracking variables', size=(25, 1)),
             PySimpleGUI.Text('Select optional secondary variables', size=(25, 1))],
            [checkboxFrame,
             primaryFrame,
             secondaryFrame],
            [PySimpleGUI.Text('Start % of data', size=(40, 1)), PySimpleGUI.Text('End % of data', size=(40, 1))],
            [PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0, key='-SSTART-'),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=100, key='-END-')],
            [PySimpleGUI.Text('Is the secondary axis bandwidth?', size=(25, 1)),
             PySimpleGUI.Text('Select the number of cores', size=(25, 1))],
            [PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-BANDWIDTH-',
                              enable_events=True),
             PySimpleGUI.Drop(values=(1, 2, 3, 4), auto_size_text=True, size=(25, 1), key='-CORES-',
                              enable_events=True)]
        ]
        if returnLayout is True:
            return layout

        layout.append([PySimpleGUI.Button('Plot', size=(10, 1))])

        window = PySimpleGUI.Window('Defrag History Visualizer', layout)
        dhg = None
        dhFile = None
        while True:
            event, values = window.read()
            if event is PySimpleGUI.WIN_CLOSED:
                break
            elif event == '-FILE-':
                dirPath = values['-FILE-']
                driveName = values['-DRIVE-']
                mode = 0
                if driveName == 'ADP':
                    mode = 1
                elif driveName == 'CDR':
                    mode = 2
                dhg, dhFile = display_dir(window, dirPath, mode)
            elif event == 'Plot':
                print("plotting.....")
                create_new_graph_window(values, dhg, dhFile)
        window.close()
        return

    @staticmethod
    def neuralNetClassify(returnLayout=False):
        """
        Layout construction for an independent user profile.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
        Returns: layout or input box information.
        """
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic Neural Network form.
        # Return values as a list.
        ###############################################################################
        layout = [[PySimpleGUI.Text('Classification Neural Network Parameters')],

                  [PySimpleGUI.Text('_' * 100, size=(65, 1))],
                  # Parameters Section
                  [PySimpleGUI.Text('Configuration Parameters', justification='left')],
                  [PySimpleGUI.Text('Passes', size=(15, 1)),
                   PySimpleGUI.Spin(values=[i for i in range(1, 1000)], initial_value=20, size=(6, 1),
                                    key='passes'),
                   PySimpleGUI.Text('Steps', size=(18, 1)),
                   PySimpleGUI.Spin(values=[i for i in range(1, 1000)], initial_value=20, size=(6, 1))],
                  [PySimpleGUI.Text('ooa', size=(15, 1), tooltip='Objective-Oriented Association'),
                   PySimpleGUI.In(default_text='6', size=(10, 1)),
                   PySimpleGUI.Text('nn', size=(15, 1), tooltip='Nearest Neighbor'),
                   PySimpleGUI.In(default_text='10', size=(10, 1))],
                  [PySimpleGUI.Text('q', size=(15, 1), tooltip='Q-learning'),
                   PySimpleGUI.In(default_text='ff', size=(10, 1),
                                  tooltip='Friend-or-foe-Q (ff), mini-max-Q (mn), correlated Q-learning (ce)'),
                   PySimpleGUI.Text('n-gram', size=(15, 1),
                                    tooltip='Contiguous sequence of n items from a given sample'),
                   PySimpleGUI.In(default_text='5', size=(10, 1))],
                  [PySimpleGUI.Text('l', size=(15, 1), tooltip='Learning Rate'),
                   PySimpleGUI.In(default_text='0.4', size=(10, 1)),
                   PySimpleGUI.Text('Layers', size=(15, 1),
                                    tooltip='Each layer learns by itself, more independently'),
                   PySimpleGUI.Drop(values=('BatchNorm', 'other'), auto_size_text=True)],

                  # Flags Section
                  [PySimpleGUI.Text('_' * 100, size=(65, 1))],
                  [PySimpleGUI.Text('Flags', justification='left')],
                  [PySimpleGUI.Checkbox('Normalize', size=(12, 1), default=True),
                   PySimpleGUI.Checkbox('Verbose', size=(20, 1))],
                  [PySimpleGUI.Checkbox('Cluster', size=(12, 1)),
                   PySimpleGUI.Checkbox('Flush Output', size=(20, 1), default=True)],
                  [PySimpleGUI.Checkbox('Write Results', size=(12, 1)),
                   PySimpleGUI.Checkbox('Keep Intermediate Data', size=(20, 1))],

                  # Loss Function Selection, Classification or Regression Selection
                  [PySimpleGUI.Text('_' * 100, size=(65, 1))],
                  [PySimpleGUI.Text('Loss Functions', justification='left')],
                  [PySimpleGUI.Radio('Cross-Entropy', 'loss', tooltip='Classification, linear squared loss',
                                     size=(12, 1)),
                   PySimpleGUI.Radio('Logistic', 'loss', tooltip='Regression, linear squared loss', default=True,
                                     size=(12, 1))],
                  [PySimpleGUI.Radio('Hinge', 'loss', tooltip='Classification, maximum-margin', size=(12, 1)),
                   PySimpleGUI.Radio('Huber', 'loss', tooltip='Regression, Smooth Mean Absolute Error',
                                     size=(12, 1))],
                  [PySimpleGUI.Radio('Kullerback', 'loss', tooltip='Classification, Relative entropy',
                                     size=(12, 1)),
                   PySimpleGUI.Radio('MAE(L1)', 'loss',
                                     tooltip='Regression, Mean Absolute Error, L1 Loss, robust for outliers',
                                     size=(12, 1))],
                  [PySimpleGUI.Radio('MSE(L2)', 'loss',
                                     tooltip='Regression, Mean Square Error, Quadratic loss, L2 Loss, easier',
                                     size=(12, 1)),
                   PySimpleGUI.Radio('MB(L0)', 'loss', tooltip='Regression, Mean Bias Error', size=(12, 1))]
                  ]
        if returnLayout:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])

        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActiveFeedback = PySimpleGUI.Window(programLabel, layout)
        (neuralNet_button, neuralNet_values) = windowActiveFeedback.read()

        # Assign Collect form Values
        if neuralNet_values == 'Submit':
            # User Information
            passes = int(neuralNet_values['passes'])
        else:
            passes = None

        # Confirmation Box
        PySimpleGUI.Popup(neuralNet_button, neuralNet_values)

        # Close window
        windowActiveFeedback.close()

        # Printing Selection
        print(neuralNet_button, neuralNet_values)
        ######################################

        return passes

    # Object Time Series Visulization
    @staticmethod
    def objectTimeSeriesVisualizer(returnLayout=False):
        primaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('First Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PFVAR-', enable_events=True)],
            [PySimpleGUI.Text('Second Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PSVAR-', enable_events=True)],
            [PySimpleGUI.Text('Third Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-PTVAR-', enable_events=True)]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Primary Variables',
            tooltip='Select the names for the variables to be graphed in the main axis')

        secondaryFrame = PySimpleGUI.Frame(layout=[
            [PySimpleGUI.Text('First Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-SFVAR-', enable_events=True)],
            [PySimpleGUI.Text('Second Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-SSVAR-', enable_events=True)],
            [PySimpleGUI.Text('Third Variable', size=(25, 1))],
            [PySimpleGUI.Drop(values=(), auto_size_text=True, size=(20, 1), key='-STVAR-', enable_events=True)]
        ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Secondary Variables',
            tooltip='Select the names for the variables to be graphed in the secondary axis')

        # Window layout
        layout = [
            [PySimpleGUI.Text('Generic Object Plot', justification='center', size=(80, 1),
                              relief=PySimpleGUI.RELIEF_SUNKEN)],
            [PySimpleGUI.Text('Browse Configuration File', size=(25, 1)),
             PySimpleGUI.In(key='-FILE-', enable_events=True),
             PySimpleGUI.FileBrowse(size=(10, 1), target='-FILE-', file_types=(("ALL Files", "*.ini"),))],
            [PySimpleGUI.Text('Object Name', size=(25, 1)),
             PySimpleGUI.Drop(values=(), auto_size_text=True, size=(10, 1), key='-OBJECT-',
                              enable_events=True),
             PySimpleGUI.Button('Select', size=(10, 1))],
            [PySimpleGUI.Text('Select tracking variables', size=(25, 1)),
             PySimpleGUI.Text('Select optional secondary variables', size=(25, 1))],
            [primaryFrame,
             secondaryFrame],
            [PySimpleGUI.Text('Start % of data', size=(40, 1)), PySimpleGUI.Text('End % of data', size=(40, 1))],
            [PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=0, key='-START-'),
             PySimpleGUI.Slider(range=(0, 100), orientation='h', size=(35, 20), default_value=100, key='-END-')],
            [PySimpleGUI.Text('Get the matrix profile for the data?')],
            [PySimpleGUI.Drop(values=('Yes', 'No'), auto_size_text=True, size=(25, 1), key='-MATRIX-',
                              enable_events=True)]
        ]
        if returnLayout is True:
            return layout

        # Need to know if this will cause problems in the future, but I believe no use case with returnLayout == True will require the plot button
        layout.append([PySimpleGUI.Button('Plot', size=(10, 1))])

        window = PySimpleGUI.Window('Object Time Series Visualizer', layout)
        vtsVar = None
        objectFileVar = None
        currentObjectVar = None
        objectDict = None
        graphObj = src.software.guiCommon.GenericObjectGraph()
        while True:
            event, valuesVar = window.read()
            if event is PySimpleGUI.WIN_CLOSED:
                break
            elif event == '-FILE-':
                dirPath = valuesVar['-FILE-']
                vtsVar, objectFileVar, objectDict = graphObj.populate_object(window, dirPath)
            elif event == 'Select':
                currentName = valuesVar['-OBJECT-']
                currentObjectNumber = objectDict[currentName]
                currentObjectVar = "uid-" + currentObjectNumber
                # Update the values contained in the drop down menus for tracking variables
                trackingVars = objectFileVar.dataDict[currentObjectVar].keys()
                trackingVars = ["None"] + list(trackingVars)
                window['-FIELD-'].Update(values=trackingVars)

            elif event == 'Plot':
                print("plotting.....")
                graphObj.create_new_graph_window(valuesVar=valuesVar, vtsVar=vtsVar, objectFileVar=objectFileVar, currentObjectVar=currentObjectVar)
        window.close()
        return

    def tabAPI(self):
        import userConfigurationProfile, pprint, src.software.container.genericObjects

        # Create a dictionary find shortcut reference
        fSC = src.software.container.genericObjects.ObjectUtility.dictSearch

        userInstance = userConfigurationProfile.userConfigurationProfile(debug=False)

        profileExists = userInstance.profileExists()
        if (profileExists is False):
            userInstance.writeMetaProfile()
        userInstanceMetaData = userInstance.readProfileAsDictionary()

        if self.debug:
            print("Profile Info \n")
            print("Exists {0}".format(userInstance.profileExists()))
            userInstanceMetaData = userInstance.readProfileAsDictionary()
            pprint.pprint(object=userInstanceMetaData, indent=3, width=100)

        ##############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layoutProfileUser = GUILayouts.profileUser(returnLayout=True, charWidth=25, charHeight=1,
                                                   identity=fSC(data=userInstanceMetaData, path='user.identity'),
                                                   name=fSC(data=userInstanceMetaData, path='user.name'),
                                                   mode=fSC(data=userInstanceMetaData, path='user.mode'),
                                                   keyLoc=fSC(data=userInstanceMetaData, path='user.keysLocation'),
                                                   encryptionStatus=fSC(data=userInstanceMetaData,
                                                                        path='user.encryptionStatus'),
                                                   workingDir=fSC(data=userInstanceMetaData,
                                                                  path='user.workingDirectory'))
        layoutProfileApplicationRAD = GUILayouts.profileApplication(returnLayout=True,
                                                                    identity=fSC(data=userInstanceMetaData,
                                                                                 path='application_1.identity'),
                                                                    major=fSC(data=userInstanceMetaData,
                                                                              path='application_1.minor'),
                                                                    minor=fSC(data=userInstanceMetaData,
                                                                              path='application_1.major'),
                                                                    name=fSC(data=userInstanceMetaData,
                                                                             path='application_1.name'),
                                                                    location=fSC(data=userInstanceMetaData,
                                                                                 path='application_1.location'),
                                                                    mode=fSC(data=userInstanceMetaData,
                                                                             path='application_1.mode'),
                                                                    url=fSC(data=userInstanceMetaData,
                                                                            path='application_1.url'))
        layoutProfileApplicationAccess = GUILayouts.profileApplication(returnLayout=True,
                                                                       identity=fSC(data=userInstanceMetaData,
                                                                                    path='application_2.identity'),
                                                                       major=fSC(data=userInstanceMetaData,
                                                                                 path='application_2.minor'),
                                                                       minor=fSC(data=userInstanceMetaData,
                                                                                 path='application_2.major'),
                                                                       name=fSC(data=userInstanceMetaData,
                                                                                path='application_2.name'),
                                                                       location=fSC(data=userInstanceMetaData,
                                                                                    path='application_2.location'),
                                                                       mode=fSC(data=userInstanceMetaData,
                                                                                path='application_2.mode'),
                                                                       url=fSC(data=userInstanceMetaData,
                                                                               path='application_2.url'))
        layoutProfileApplicationCloud = GUILayouts.profileApplication(returnLayout=True,
                                                                      identity=fSC(data=userInstanceMetaData,
                                                                                   path='application_3.identity'),
                                                                      major=fSC(data=userInstanceMetaData,
                                                                                path='application_3.minor'),
                                                                      minor=fSC(data=userInstanceMetaData,
                                                                                path='application_1.major'),
                                                                      name=fSC(data=userInstanceMetaData,
                                                                               path='application_3.name'),
                                                                      location=fSC(data=userInstanceMetaData,
                                                                                   path='application_3.location'),
                                                                      mode=fSC(data=userInstanceMetaData,
                                                                               path='application_3.mode'),
                                                                      url=fSC(data=userInstanceMetaData,
                                                                              path='application_3.url'))
        layoutDataCollect = GUILayouts.collect(returnLayout=True, debug=self.debug)
        layoutDataTable = dataTablePopulate(returnLayout=True).main()
        layoutDataUpload = GUILayouts().upload(returnLayout=True)
        layoutMLClassify = GUILayouts.neuralNetClassify(returnLayout=True)

        debugLocal = pprint.pformat(locals(), indent=3, width=100)
        debugGlobals = pprint.pformat(globals(), indent=3, width=100)

        layoutDebugLocalsInfo = GUILayouts.debugComments(returnLayout=True, displayInput=debugLocal, charWidth=75,
                                                         charHeight=8)
        layoutDebugGlobalsInfo = GUILayouts.debugComments(returnLayout=True, displayInput=debugGlobals, charWidth=75,
                                                          charHeight=8)

        layout = [
            [PySimpleGUI.Menu(menu_def, size=(len(programLabel[0]), len(programLabel)), tearoff=True,
                              key='menuOptions')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('Profile-User', layoutProfileUser, key='profileUser'),
                PySimpleGUI.Tab('Profile-App-Raad', layoutProfileApplicationRAD, key='profileAppRAD'),
                PySimpleGUI.Tab('Profile-App-Access', layoutProfileApplicationAccess, key='profileAppAccess'),
                PySimpleGUI.Tab('Profile-App-Cloud', layoutProfileApplicationCloud, key='profileAppCloud'),
            ]], key='profileInfo')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('Data-Collect', layoutDataCollect, key='dataCollect'),
                PySimpleGUI.Tab('Data-Table', layoutDataTable, key='dataTable'),
                PySimpleGUI.Tab('Data-Upload', layoutDataUpload, key='dataUpload'),
                PySimpleGUI.Tab('ML-Classify', layoutMLClassify, key='machineLearningClassify'),
            ]], key='dataInfo')],
            [PySimpleGUI.Button('Refresh', button_color=('white', 'purple')),
             PySimpleGUI.Button('Gather Data', button_color=('white', 'blue')),
             PySimpleGUI.Button('Exit', button_color=('white', 'green')),
             PySimpleGUI.Button('Update Profile', button_color=('white', 'orange')),
             PySimpleGUI.Button('Send Feedback', button_color=('white', 'red')),
             ]
        ]

        """
        if self.debug:
            layout.append([PySimpleGUI.TabGroup([[PySimpleGUI.Tab('Debug-Locals', layoutDebugLocalsInfo, key='debugLocals'),
                                                  PySimpleGUI.Tab('Debug-Globals', layoutDebugGlobalsInfo, key='debugGlobals')]],
                                                key='debugInfo'
                                                )])
        """
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Refresh':
            # User Information
            print("Button Action")

        # Confirmation Box
        if self.debug:
            PySimpleGUI.PopupScrolled(pprint.pformat(collect_button, indent=3, width=100),
                                      pprint.pformat(collect_values, indent=3, width=100),
                                      size=(128, 32))
            print(pprint.pformat(collect_button, indent=3, width=100),
                  pprint.pformat(collect_values, indent=3, width=100))

        # Close window
        windowActive.close()

        # Printing Selection
        return None


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
    examples = GUILayouts(debug=options.debug)

    print("options: ", str(options.mode))

    if options.mode in ["1", "2", "3"]:
        examples.collect()
        examples.objectTimeSeriesVisualizer()
        examples.defragHistoryGraph()
        examples.RNNPredictorGraph()
        examples.ARMAPredictionGraph()
        examples.upload()
        examples.download()
        examples.profileUser()
        examples.profileApplication()
        examples.userFeedback()
        examples.neuralNetClassify()
        # examples.dataTablePopulate()
        examples.debugComments(displayInput=pprint.pformat(locals(), indent=3, width=100))
    else:
        print("Unknown")


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
