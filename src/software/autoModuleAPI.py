#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package autoModuleAPI
import optparse, datetime, traceback, pprint, os, sys, pandas,  shutil
# import concurrent.futures, pylatex, numpy, random, difflib, tensorflow, re
import src.software.TSV.visualizeTS
import src.software.TSV.generateTSBinaries
import src.software.TSV.formatTSFiles
import src.software.TSV.DefragHistoryGrapher
import src.software.MEP.mediaErrorPredictor
import src.software.axon.packageInterface
import src.software.axon.axonInterface
import src.software.axon.axonMeta
import src.software.axon.axonProfile
import src.software.access.DriveInfo
import src.software.container.basicTypes
import src.software.guiLayouts
import src.software.guiCommon
import src.software.guiOneShot
import src.software.guiDeveloper
import src.software.guiTests
import src.software.JIRA.analysisGuide
import src.software.MEP.loadAndProbeDrive
import src.software.TSV.loadAndProbeSystem
import src.software.autoAI.nlogPrediction
import src.software.DP.preprocessingAPI as DP
from src.software.JIRA.executeJiraMining import executeJiraMining, cleanSearchString
from src.software.utilsCommon import DictionaryFlatten, tryFile, tryFolder, getFileNameUTCTime, cleanFileName, flattenList, getTimeStamp, strip_start
from src.software.debug import whoami
from src.software.dAMP.reportGenerator import ReportGenerator
from src.software.dAMP.gatherMeta import GatherMeta
from src.software.threadModuleAPI import MassiveParallelismSingleFunctionManyParameters
# from collections import OrderedDict
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', 'statsmodels.tsa.ar_model.AR', FutureWarning)

# Constants
OI = [
    'uid-6',  # ThermalSensor
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

UIDs_Stack = [
    'uid-107',  # : 'ABT_Stack',
    'uid-111',  #: 'stackXORRecovery',
    'uid-112',  #: 'stackDefrag',
    'uid-113',  #: 'stackHalSvc',
    'uid-114',  #: 'stackWriteCache',
    'uid-115',  #: 'stackXportCmdDisp',
    'uid-116',  #: 'stackContextTask',
    'uid-117',  #: 'stackSecurityTask',
    'uid-118',  #: 'stackServiceTask',
    'uid-119',  #: 'stackCoreDispatch',
    'uid-120',  #: 'stackXfer',
    'uid-121',  #: 'IRQ_Stack',
    'uid-124',  #: 'stackCoreComplete',
    'uid-125',  #: 'stackIdle',
    'uid-127',  #: 'nandReadWriteWorkStack',
    'uid-128',  #: 'SYS_Stack',
    'uid-130',  #: 'HalCpu_ResetStack1',
    'uid-131',  #: 'HalCpu_ResetStack2',
    'uid-133',  #: 'pliSideTraceStackDump',
    'uid-162',  #: 'TransIcmdReservedReuseStack',
    'uid-163',  #: 'ActiveTaskStackPointer',
]


class autoModuleMeta:

    def __init__(self):
        return

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


def generateBinaryDataSet(driveNumber=0,
                          driveName=None,
                          inputFile=None,
                          identifier="Tv2HiTAC",
                          outputDir='.',
                          parse=False,
                          volumeLabel="perftest",
                          volumeAllocUnit="4096",
                          volumeFS="ntfs",
                          volumeLetter="g",
                          partitionStyle="mbr",
                          partitionFlag=True,
                          prepFlag=True,
                          debug=False,
                          performanceTest=True):
    """
    Preparation of NVMe drive then gathering of data based on performance or media collection benchmarks.
    Args:
        driveNumber: string representation of int for drive number.
        driveName: driveName: Name of device interface to get data from.
        inputFile: String for the path to the input file where the workload configuration is stored.
        identifier: String for the name of the data set that corresponds to the telemetry pull to be executed.
        outputDir: String for the path to the output directory where the binaries will be stored.
        parse: Boolean flag to parse the telemetry binaries pulled from the drive.
        volumeLabel: (Windows) String for the label to be used on the disk volume.
        volumeAllocUnit: (Windows) String for the volume allocation unit size.
        volumeFS: (Windows) String for the name of the file system to be used in the disk volume.
        volumeLetter: (Windows) String for the letter to be assigned to the disk volume.
        partitionStyle: (Windows) String for the name of the partition style to be used in the specified disk.
        partitionFlag: (Windows) Boolean flag to indicate if the program should partition the drive using the given parameters.
        prepFlag: (Linux) Boolean flag to indicate if the program should prep the drive before loading it.
        debug: Boolean flag to activate debug statements.
        performanceTest: Perform standard performance test or media profile test.
    Returns: Success of API 0 is good status.
    """
    if performanceTest:
        if inputFile is None:
            inputFile = os.path.abspath(r'software/TSV/workloads/windows/Thermal-4KSW1QD1W.csv')
        (options, args) = src.software.TSV.loadAndProbeSystem.inputsAPI(driveNumber=driveNumber, driveName=driveName, inputFile=inputFile, identifier=identifier, outputDir=outputDir, parse=parse, volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit, volumeFS=volumeFS, volumeLetter=volumeLetter, partitionStyle=partitionStyle, partitionFlag=partitionFlag, prepFlag=prepFlag, debug=debug)
        retCode = src.software.TSV.loadAndProbeSystem.API(options=options)
    else:
        if inputFile is None:
            inputFile = os.path.abspath(r'software/TSV/workloads/linux/rand-write.sh')
        # Media profiling Linux Only!
        (options, args) = src.software.MEP.loadAndProbeDrive.inputsAPI(driveNumber=driveNumber, driveName=driveName, inputFile=inputFile, identifier=identifier, outputDir=outputDir, parse=parse, volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit, volumeFS=volumeFS, volumeLetter=volumeLetter, partitionStyle=partitionStyle, partitionFlag=partitionFlag, prepFlag=prepFlag, debug=debug)
        retCode = src.software.MEP.loadAndProbeDrive.API(options=options)
    return retCode


def generateParseDataSet(containingFolder=".", autoParseFolder=".", outFolder=".", nlogFolder='.',
                         operationMode=3, autoParseMode=2, debug=False,
                         fileIdentifier="Tv2HiTAC",
                         timeName=None,
                         fileTokenName='TokenData.ini',
                         fileMetaName='MetaData.zip',
                         debugFile=None,
                         skipZip: bool = False):
    """Function to parse telemetry data payloads.
    Args:
        debugFile: data dictionary debug file.
        containingFolder: Folder with the input binary files.
        autoParseFolder: Folder with the auto parse decoders.
        outFolder: Folder to target generated files.
        nlogFolder: Log folder and tokenizers
        operationMode: 1:CLI, 2: TWIDL, 3: PARSE, 4: IMAS.
        autoParseMode: 1: bufferDictionary, 2: autoParsers.
        debug: Debug developer information.
        fileIdentifier: File prefix.
        timeName: Time token name.
        fileTokenName: Token ini name.
        fileMetaName: Meta Data zip name.
        skipZip: Parameter to skip zipping content
    Returns: Generated information and objects from data processsing.
    """
    # Nil constants
    driveName = "/dev/nvme0n1"  # Linux and Windows device handle
    driveNumber = None  # Value 0-K
    numTelemetryPayloads = 10
    timeLapse = 60
    objNames = None

    if timeName is None:
        timeName = getFileNameUTCTime()

    containingFolder = tryFolder(path=containingFolder)
    autoParseFolder = tryFolder(path=autoParseFolder)
    nlogFolder = tryFolder(path=nlogFolder)

    if debugFile is None:
        debugFile = str("dictionaryDebug_" + timeName + ".log")
        debugFile = os.path.join(outFolder, debugFile)

    dataFileName = ('_'.join([fileIdentifier, timeName, fileTokenName]))

    dataFileNameAbsolutePath = os.path.join(outFolder, dataFileName)

    dataZipFileName = ('_'.join([fileIdentifier, timeName, fileMetaName]))

    telemetryBinaryObj = src.software.TSV.generateTSBinaries.generateTSBinaries(iterations=numTelemetryPayloads,
                                                                                outpath=outFolder,
                                                                                debug=debug)
    parseBinList, binOutputFolder = telemetryBinaryObj.generateTSBinariesAPI(mode=operationMode, time=timeLapse,
                                                                             driveName=driveName,
                                                                             driveNumber=driveNumber,
                                                                             identifier=fileIdentifier,
                                                                             inputFolder=containingFolder)
    telemetryFormatObj = src.software.TSV.formatTSFiles.formatTSFiles(outpath=outFolder, debug=debug)
    validExtraction = telemetryFormatObj.formatTSFilesAPI(fwDir=autoParseFolder, binDir=outFolder,
                                                          outfile=dataFileName, obj=objNames, mode=autoParseMode,
                                                          binList=binOutputFolder, timeStamp=timeName,
                                                          debug=debug, nlogFolder=nlogFolder, debugFile=debugFile)
    if skipZip:
        packageObj = None
    else:
        packageObj = src.software.axon.packageInterface.packageInterface(absPath=outFolder,
                                                                         timeSeriesFile=dataFileNameAbsolutePath,
                                                                         debug=debug).createZIP(dataZipFileName)
    telemetryDataDictionary = DP.preprocessingAPI().loadDataDict(configFilePath=dataFileNameAbsolutePath)
    telemetryDataDictionaryFlat = DictionaryFlatten(telemetryDataDictionary)
    telemetryDataDictionaryFlatSize = telemetryDataDictionaryFlat.getSize()
    driveInfoObj = src.software.access.DriveInfo.DriveInfo(debug=debug)
    driveInformation = driveInfoObj.DriveInfoAPI(device=driveName,
                                                 mode=operationMode,
                                                 dataDict=telemetryDataDictionary)
    payload = (dataFileName, dataZipFileName,
               telemetryBinaryObj, parseBinList, binOutputFolder,
               telemetryFormatObj, validExtraction,
               packageObj, telemetryDataDictionary, telemetryDataDictionaryFlat, telemetryDataDictionaryFlatSize,
               driveInformation)
    return payload


def generateHandbook(username="PresidentSkroob@spaceballs.one", password="12345",
                     passwordEncodingObjectSaved=None,
                     defaultPasswordFile="../../.raadProfile/credentials.conf",
                     outCacheFile="../../.raadProfile/debugHandbookCache.ini",
                     searchString="ASSERT_DE003",  # "ASSERT_DF049"
                     similarityScoreThreshold=0.95,
                     debug=False):
    """ Wiki page download and save
    Args:
        username: Potential Username
        password: Potential Password
        passwordEncodingObjectSaved: Previously encoded username and password.
        defaultPasswordFile: Secret file location with username and password
        outCacheFile: Output wiki cache file.
        searchString: Debug string to look for.
        similarityScoreThreshold: similarity score for looking through debug items.
        debug: developer debug flag.
    Returns: Password object, hash of password
    """

    debugHandbookTranslate = {1: "Unknown", 2: "Live", 3: "Cache", 4: "Nil"}
    debugHandbookFile = outCacheFile
    if username is None:
        username = "PresidentSkroob@spaceballs.one"
    if password is None:
        password = "12345"
    if defaultPasswordFile is not None:
        defaultPasswordFile = tryFile(fileName=defaultPasswordFile, walkUpLimit=3)

    if username == "PresidentSkroob@spaceballs.one" and password == "12345" and defaultPasswordFile is None:
        if debug:
            print(f"Error default username={username} and password={password}, defaultPasswordFile={defaultPasswordFile}.")
        return (passwordEncodingObjectSaved, 'Nil', 'Nil', None)  # Error in input

    if passwordEncodingObjectSaved is None:
        passwordEncodingObject = src.software.axon.packageInterface.Cipher_AES()
    else:
        passwordEncodingObject = passwordEncodingObjectSaved

    passwordCheckObject = src.software.axon.packageInterface.Cipher_AES(key=passwordEncodingObject.get_key(), iv=passwordEncodingObject.get_iv())
    passwordCheckObject.encrypt(text=password)
    pastPWDvsNOWPWD = ((passwordCheckObject.get_encryptedText() != passwordEncodingObject.get_encryptedText()) and
                       (passwordEncodingObject.get_encryptedText() is not None))
    if pastPWDvsNOWPWD:
        del passwordEncodingObject
        passwordEncodingObject = src.software.axon.packageInterface.Cipher_AES()
    # Username and password Boolean checks
    defaultPasswordInformation = (username == "" or password == "")
    passwordObjectEmpty = (passwordEncodingObject.get_encryptedText() is None)
    if defaultPasswordFile is None:
        passwordFileExists = False
    else:
        passwordFileExists = os.path.isfile(defaultPasswordFile)

    # Cases are Turing Complete.
    if passwordFileExists and passwordObjectEmpty:
        # Case 1: Password file exists and not encoded yet.
        with open(defaultPasswordFile) as openFile:
            fileMeta = openFile.read()
            UserInfoTokens = fileMeta.split('\n')  # Separator is \n 3
            username = UserInfoTokens[0]
            passwordEncodingObject.encrypt(text=UserInfoTokens[1])
            del UserInfoTokens  # Do not keep unencoded password
            del fileMeta
        updateDisplayUserPass = True
    elif passwordFileExists and not passwordObjectEmpty:
        # Case 2: Password file exists and has been encoded yet.
        updateDisplayUserPass = False
    elif not passwordFileExists and passwordObjectEmpty:
        # Case 3: Password file does not exist and not encoded yet.
        if not defaultPasswordInformation:
            # Encode user text since not default
            passwordEncodingObject.encrypt(text=password)
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
        password_hash = passwordEncodingObject.get_encryptedText()
    else:
        password_hash = 'nil'

    # Wiki update.
    wikiInterface = src.software.JIRA.analysisGuide.AnalysisGuide(debug=debug)
    handbookInfo = wikiInterface.pythonAPI(selectedMode=1,
                                           defaultFile=defaultPasswordFile,
                                           default_username=username,
                                           default_password=passwordEncodingObject.decrypt(cipher_text=password_hash),
                                           outputFile=outCacheFile,
                                           searchString=searchString,
                                           simularityScoreThreshold=similarityScoreThreshold)
    # Delete vars for in use for security
    del updateDisplayUserPass
    del defaultPasswordInformation
    del passwordObjectEmpty
    del passwordFileExists
    del passwordCheckObject
    del pastPWDvsNOWPWD

    if handbookInfo is not None:
        message = f"{getTimeStamp()} Status: Access, using live data.{os.linesep}"
        debugHandbookStatus = debugHandbookTranslate[2]
    else:
        handbookInfoValidity = wikiInterface.loadCache(loadFile=debugHandbookFile)
        if handbookInfoValidity is True:
            handbookInfo = wikiInterface.getHandbookInfo()
            message = f"{getTimeStamp()} Status: No Access, using cache.{os.linesep}"
            debugHandbookStatus = debugHandbookTranslate[3]
        else:
            criticalCacheFile = tryFile(fileName="/.raadProfile/debugHandbookCache.ini", walkUpLimit=5)
            handbookInfoValidity = wikiInterface.loadCache(loadFile=criticalCacheFile)

            if criticalCacheFile is None:
                # Create cache file.
                f = open('.raadProfile/debugHandbookCache.ini', 'w+')
                f.write('')
                f.close()
                criticalCacheFile = tryFile(fileName="/.raadProfile/debugHandbookCache.ini", walkUpLimit=5)
                handbookInfoValidity = wikiInterface.loadCache(loadFile=criticalCacheFile)

            if handbookInfoValidity is True:
                handbookInfo = wikiInterface.getHandbookInfo()
                message = f"{getTimeStamp()} Status: No Access, using emergency cache.{os.linesep}"
                debugHandbookStatus = debugHandbookTranslate[3]
            else:
                message = f"{getTimeStamp()} Status: No Access, at all.{os.linesep}"
                message += f"{getTimeStamp()} No reference meta data, providing raw data.{os.linesep}"
                debugHandbookStatus = debugHandbookTranslate[4]

    if handbookInfo is not None:
        dataMatch = wikiInterface.searchForSignatureFromCode(signature=searchString, similarityScore=similarityScoreThreshold)
    else:
        dataMatch = None

    if debug:
        print(f"Debug {whoami()} {debugHandbookStatus} {message} DataMatch is {dataMatch} {os.linesep}")

    return (passwordEncodingObject, password_hash, handbookInfo, dataMatch)


def generateDataTables(inputINI=None, saveCVS=True, outputLocation='.', debug=False):
    """ Generates data tables from telemetry information
    Args:
        inputINI: input time series file to process.
        saveCVS: Flag to save data as CVS
        outputLocation: output folder save location
        debug: developer debug flag

    Returns: uid list, tables, size, and files

    """
    # Pull data file and store in a dictionary
    telemetryDataDictionary = DP.preprocessingAPI().loadDataDict(inputINI)
    # Traverse dictionary and populate the table
    maxLen = 0  # Error catching for if any one time series is longer than the others
    UIDList = list(telemetryDataDictionary.keys())
    # Initialize headings
    dataTables = []
    sizeTables = []
    fileNames = []
    # For each telemetry object pulled by telemetry
    for telemetryObject in telemetryDataDictionary:
        telemetryObjectDictionary = telemetryDataDictionary[telemetryObject]
        try:
            # Initialize 2D array for meta data table
            dataTable = [["Telemetry Object", "Telemetry Feature"]]
            headings = []
            # For each feature in the telemetry object
            for telemetryFeature in telemetryObjectDictionary:
                try:
                    # Checkthe keys that were pulled point to the time series array
                    if not isinstance(telemetryObjectDictionary[telemetryFeature], list):
                        if debug:
                            ("Not Instance: [{0}][{1}] <== {2}".format(telemetryObject, telemetryFeature, telemetryObjectDictionary[telemetryFeature]))
                        continue
                    # Update length so table has the same length
                    if len(telemetryObjectDictionary[telemetryFeature]) > maxLen:
                        maxLen = len(telemetryObjectDictionary[telemetryFeature])
                    # Add line to the table
                    dataTable.append([telemetryObject, telemetryFeature] + telemetryObjectDictionary[telemetryFeature])
                    # Add time tag to headings
                    if len(headings) == 0:
                        headings = ["t_" + str(i) for i in range(len(telemetryObjectDictionary[telemetryFeature]))]

                except BaseException as ErrorLocalOne:
                    print(f"Nested {ErrorLocalOne}: ", telemetryObject, ", ", telemetryFeature, telemetryObjectDictionary[telemetryFeature])
                    continue
            dataTable[0] = dataTable[0] + headings  # Insert table heading.
            # Determine table sizing
            rows = len(dataTable)
            columns = len(dataTable[0])
            # Create list of tables and sizes
            dataTables.append(dataTable)
            sizeTables.append([rows, columns])
            if saveCVS:
                dataFrame = pandas.DataFrame(data=dataTable)
                dataFrameCSVName = "{0}_{1}_{2}.csv".format("DataTable", str(telemetryObject), datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f"))
                dataFrameCSVLocation = os.path.join(outputLocation, dataFrameCSVName)
                dataFrame.to_csv(dataFrameCSVLocation)
                fileNames.append(dataFrameCSVLocation)
        except BaseException as ErrorLocalTwo:
            print(f"Outside {ErrorLocalTwo}: {telemetryObject}")
            continue

    return UIDList, dataTables, sizeTables, fileNames


def generateTimeSeriesGraphs(inputINI=None, outputFile="telemetryDefault", subSequenceLength=1, matrixProfileFlag=False,
                             inParallel=True, requiredList=None, debug=False, timeOut=180):
    """Generate all the graphs for the telemetry objects contained in inputINI
    Args:
        inParallel: Flag to process all objects in parallel processes.
        requiredList: List of strings fort he names of objects to be processed if the useRequiredList flag is set.
            If None, the default list will be used. Indicates whether the objects to be processed should be limited to the ones
            contained in the requiredList.
        inputINI: relative path to the .ini file where the time series are stored
        outputFile: string for the prefix to be used for the PDF file naming
        subSequenceLength: Integer for the length of the sliding window for matrix profile (only relevant, if matrix profile flag is set)
        matrixProfileFlag: Boolean flag to apply matrix profile to time series before plotting it
        debug: [True, False] developer debug statements.
        timeOut: Execution timeout.
    Returns: List of file names for the PDFs containing the graphs (one PDF for each object, and one graph per field)
    """
    validMetaFile = os.path.exists(os.path.abspath(inputINI))
    if validMetaFile is False:
        print("Configuration file does not exist. Unable to graph generic objects")
        return None

    if not os.path.exists(outputFile):
        os.makedirs(outputFile)

    viz = src.software.TSV.visualizeTS.visualizeTS(debug=debug)
    pdfFiles = viz.visualizeTSAPI(input_t=inputINI, out=outputFile, subSeqLen=subSequenceLength,
                                  transformTS=matrixProfileFlag, inParallel=inParallel, requiredList=requiredList, timeOut=timeOut)
    return pdfFiles


def generateDefragHistory(inputINI=None, outputFile="telemetryDefault", mode=1, numCores=1, bandwidthFlag=True, debug=False):
    """
    Generate all relevant graphs associated with the DefragHistory telemetry object
    Args:
        inputINI: relative path to the .ini file where the time series are stored
        outputFile: string for the prefix to be used for the PDF file naming
        mode: Integer value for run mode (1=ADP, 2=CDR)
        numCores: Integer for the number of cores from which data was pulled
        bandwidthFlag: Boolean flag that indicates if the secondary axis corresponds to bandwidth
        debug: [True, False] developer debug statements.
    Returns: Name of the PDF file where all the graphs are stored
    """
    validMetaFile = os.path.exists(os.path.abspath(inputINI))
    if validMetaFile:
        viz = src.software.TSV.DefragHistoryGrapher.DefragHistoryGrapher(mode=mode, debug=debug)
        outFileName = outputFile
        pdfFile = viz.DefragHistoryGrapherAPI(input_t=inputINI, out=outFileName, numCores=numCores,
                                              bandwidthFlag=bandwidthFlag)
    else:
        pdfFile = None
    return pdfFile


def generateARMA(inputINI=None, subSequenceLength=1, matrixProfileFlag=None, debug=False, inParallel=True,
                 requiredList=None, outFolder=None, timeOut=180, max_workers=None):
    """ Generate all ARMA models for data.
    Args:
        inParallel:
        requiredList: List of strings fort he names of objects to be processed if the useRequiredList flag is set.
            If None, the default list will be used. Indicates whether the objects to be processed should be limited to the ones
            contained in the requiredList.
        inputINI: *.ini with preprocessed time series.
        subSequenceLength: [1 to len(time_series)/3] sequence length for matrix profile.
        matrixProfileFlag: Boolean flag that enables matrix profile data generation.
        debug: [True, False] developer debug statements.
        outFolder: Output directory.
        timeOut: Execution timeout.
        max_workers: total number of threads.
    Returns: list of PDFs of ARMA models
    """
    pdfNameList = list()
    runSequential = not inParallel
    inOrder = True
    validMetaFile = os.path.exists(os.path.abspath(inputINI))
    if validMetaFile is False:
        return pdfNameList
    # Load file context
    MEP = src.software.MEP.mediaErrorPredictor.MediaErrorPredictor(inputFile=inputINI,
                                                                   matrixProfile=matrixProfileFlag,
                                                                   subSeqLen=subSequenceLength, debug=debug)
    oldDictKeys = MEP.dataDict.keys()
    if requiredList is None:
        requiredList = OI
    objectsOfInterest = list(set(requiredList).intersection(oldDictKeys))

    kwargsList = []
    if outFolder is None:
        outFolder = os.getcwd()
    saveFolder = os.path.join(outFolder, "telemetryDefault", "ARMA")
    # Prepare list of args to execute in open core threads.
    for itemObj in objectsOfInterest:
        trackingVars = MEP.dataDict[itemObj].keys()
        saveFolderItem = os.path.join(saveFolder, str(itemObj))
        for itemField in trackingVars:  # For each object use the data element.
            # Construct file name and filter invalid characters
            fileName = (str(itemObj) + '_' + str(itemField) + ".pdf")
            pdfName = cleanFileName(fileName=fileName)
            pdfName = os.path.join(saveFolderItem, str(pdfName))
            dictElem = {'targetObject': itemObj,
                        'targetField' : itemField,
                        'outFile'     : pdfName}
            kwargsList.append(dictElem)
    # Setup pool, run, and check pool results.
    functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                     functionName=MEP.writeARMAToPDF,
                                                                     fParameters=kwargsList,
                                                                     workers=max_workers,
                                                                     timeOut=timeOut,
                                                                     inOrder=inOrder,
                                                                     runSequential=runSequential)
    iResults = functionContext.execute()
    for validPDF in iResults:
        if validPDF is not None:
            pdfNameList.append(validPDF)
    # Create ARMA models for each object.
    # for itemObj in objectsOfInterest:
    #    trackingVars = MEP.dataDict[itemObj].keys()
    #    for itemField in trackingVars:  # For each object use the data element.
    #        # Construct file name and filter invalid characters
    #        fileName = (str(itemObj) + '_' + str(itemField))
    #        pdfName = cleanFileName(fileName=fileName)
    #        validPDF = MEP.writeARMAToPDF(targetObject=itemObj, targetField=itemField, outFile=pdfName)
    #        if validPDF is not None:
    #            pdfNameList.append(pdfName)
    if pdfNameList == list():
        pdfNameList = None
    return pdfNameList


def generateRNNLSTM(inputINI=None,
                    subSequenceLength=1, matrixProfileFlag=False,
                    inputWidth=70, labelWidth=20, shift=2, hiddenLayers=128,
                    batchSize=32, maxEpochs=2096,
                    embeddedEncodingFlag=False, categoricalEncodingFlag=False,
                    debug=False, inParallel=True, requiredList=None, useEntirePayload=False, timeOut=180,
                    max_workers=None, inOrder: bool = True):
    """ Generate all ARMA models for data.
    Args:
        inParallel: Boolean flag to kick off process in parallel
        requiredList: List of strings fort he names of objects to be processed if the useRequiredList flag is set.
            If None, the default list will be used. Indicates whether the objects to be processed should be limited to the ones
            contained in the requiredList.
        useEntirePayload: Boolean flag to indicate that the entire telemetry payload should be fed into the RNN model as
            an input
        inputINI: *.ini with preprocessed time series.
        inputWidth: Integer for the length of the input sequence to be considered for the prediction
        labelWidth: Integer for the length of the output sequence expected from the prediction
        shift: Integer for the shift to be considered when sliding the input window
        hiddenLayers: Integer for the number of neurons contained in each hidden layer
        subSequenceLength: [1 to len(time_series)/3] sequence length for matrix profile.
        batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN model.
        maxEpochs: Integer for the maximum number of epochs to be considered when training the model
        matrixProfileFlag: Boolean flag that enables matrix profile data generation.
        embeddedEncodingFlag: Boolean flag to apply embedded encoding to time series as the first layer in the RNN model
        categoricalEncodingFlag: Boolean flag to apply label encoding to the time series values (usually used for categorical values)
        debug: developer debug statements.
        timeOut: Execution timeout.
        max_workers: Number of tasks to execute on in parallel.
        inOrder: out-of-order or in-order execution. Dependencies on data should set flag to in-order.
    Returns: list of PDFs of ARMA models.
    """
    objectFile = src.software.guiCommon.ObjectConfigRNN(configFilePath=inputINI)
    objectFile.readConfigContent(debug=debug)
    objectList = list(objectFile.objectIDs)
    pdfNameList = list()
    timeName = getFileNameUTCTime()

    objectsOfInterest = list()
    oldDictKeys = objectList
    if requiredList is None:
        requiredList = OI
        for object_t in requiredList:
            if object_t in oldDictKeys:
                objectsOfInterest.append(object_t)
    else:
        objectsOfInterest = oldDictKeys

    newDataDict = dict()
    fieldsOfInterest = list()
    if useEntirePayload and objectFile.objectIDs[0] != "MEDIA_MADNESS":
        trackingObject = "TELEMETRY"
        newDataDict[trackingObject] = dict()
        for currentObject in objectsOfInterest:
            for currentField in objectFile.dataDict[currentObject].keys():
                newName = str(currentObject) + "_" + str(currentField)
                fieldsOfInterest.append(newName)
                newDataDict[trackingObject][newName] = objectFile.dataDict[currentObject][currentField]
        objectsOfInterest = [trackingObject]

    kwargsList = []
    accuracyList = []
    for currentObject in objectsOfInterest:
        currDataDict = None
        # Update the values contained in the drop down menus for primary and secondary variables
        if useEntirePayload and objectFile.objectIDs[0] != "MEDIA_MADNESS":
            trackingVars = fieldsOfInterest
            currDataDict = newDataDict
        elif objectFile.objectIDs[0] == "MEDIA_MADNESS":
            trackingVars = objectFile.columns
            matrixProfileFlag = False
        else:
            trackingVars = objectFile.dataDict[currentObject].keys()
        if (len(trackingVars) > 0):
            primaryVars = list(trackingVars)  # or ["None"] with up to 5
            trackingVars = primaryVars
            secondaryVars = list(trackingVars)  # or ["None"] best with 1
            plotVars = secondaryVars
            fileName = str(currentObject) + '_' + timeName
            pdfName = cleanFileName(fileName=str(fileName))
            if pdfName is not None:
                pdfNameList.append(pdfName)
            else:
                pdfNameList.append(str(currentObject))
                print(f"PDF Name Error {os.linesep} {whoami()}")
            dictElem = {'matrixProfileFlag'      : matrixProfileFlag,
                        'embeddedEncodingFlag'   : embeddedEncodingFlag,
                        'categoricalEncodingFlag': categoricalEncodingFlag,
                        'inputWidth'             : inputWidth,
                        'labelWidth'             : labelWidth,
                        'shift'                  : shift,
                        'batchSize'              : batchSize,
                        'hiddenLayers'           : hiddenLayers,
                        'maxEpochs'              : maxEpochs,
                        'subSequenceLength'      : subSequenceLength,
                        'targetObject'           : currentObject,
                        'targetFields'           : trackingVars,
                        'plotColumn'             : plotVars[0],
                        'pdf'                    : pdfName,
                        'currDataDict'           : currDataDict,
                        'debug'                  : debug}
            kwargsList.append(dictElem)

            # Setup pool, run, and check pool results.
            functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                             functionName=objectFile.readConfigContent().timeSeriesPredictorAllAPI,
                                                                             fParameters=kwargsList,
                                                                             workers=max_workers,
                                                                             timeOut=timeOut,
                                                                             inOrder=inOrder,
                                                                             runSequential=not inParallel)
            iResults = functionContext.execute()
            accuracyList = iResults
        if accuracyList == list() or \
                accuracyList is None or \
                len(accuracyList) < 1:
            pdfNameList = None
        if debug:
            print(f"RNN Files {os.linesep}"
                  f"{pprint.pformat(pdfNameList)} "
                  f"with accuracy of "
                  f"{pprint.pformat(accuracyList)}")
    return pdfNameList


def generateAXONUpload(contentFile=None, uploadMode="test", userName='lab', debug=False):
    """ User upload content data file gathered to the AXON database.
    Args:
        contentFile: Upload info filename for JSON creation.
        uploadMode: 'production', 'test', 'development', 'base'.
        userName: user name with ability to upload.
        debug: Developer debug statement.
    Returns: status information and meta data from upload.
    """
    # User wants to upload the last content data file gathered to the AXON database.
    axonURL = None
    if contentFile is None:
        print("ERROR: No telemetry pull currently present for upload")
        return (False, 0, None, None, None, None, None)
    # Instantiate class for axon upload
    axonInt = src.software.axon.axonInterface.Axon_Interface(mode=uploadMode)
    # Create metadata file for AXON upload
    metaData = dict()
    # Populate Metadata with data from drive
    driveInfoMeta = src.software.access.DriveInfo.DriveInfo().DriveInfoAPI()
    metaData.update(driveInfoMeta)
    hostMeta = dict()
    # Add field for the timestamp of the AXON upload
    hostMeta["timeStamp"] = getFileNameUTCTime()  # Uses same format as given in axonMeta.py
    # Add field for the host username that is requesting the upload
    hostMeta["host"] = userName
    # Gather host specific metadata
    metaData.update(hostMeta)
    # Create finished metadata file
    metaFile = axonInt.createContentsMetaData(metaData, contentFile)
    # Create metadata file for AXON upload
    success, axonID = axonInt.sendInfo(metaDataFile=metaFile, contentFile=contentFile)
    # Axon Upload return information.
    if success:
        # Track AXON uploads in hidden file in central directory
        axonFile = os.path.abspath(os.path.join(os.getcwd(), metaFile))
        if debug:
            print("AXON Upload Successful!!! Returned AXON ID is ", axonID)
            print(f"Axon file: {axonFile}")
        #  Instantiate profile for AXON
        profile = src.software.axon.axonProfile.AxonProfile()
        # Open and setup config parser for file
        profile.GetProfile(axonFile)
        # Populate the profile meta
        if metaData is not None:
            profile.AddSection(entry=metaData, ID=axonID)
        # Write config to file
        profile.SaveProfile(axonFile)
        axonURL = axonInt.GetURL()
    # Verify AXON INI download save.
    axonProfiler = src.software.axon.axonProfile.AxonProfile()
    (axonIDs, axonConfig) = axonProfiler.GetProfile()
    return (success, axonID, axonURL, metaFile, contentFile, axonIDs, axonConfig)


def generateAXONDownload(axonID=None, downloadDirectory=None, downloadMode='test', debug=False):
    """ User download content data file gathered to the AXON database.
    Args:
        axonID: identifier to download
        downloadDirectory: directory to save content
        downloadMode: search database
        debug: developer debug logs.
    Returns: status information and meta data from download.
    """
    if axonID is None:
        return (None, None, None, None, None, None, None)

    # Download the File
    axonInt = src.software.axon.axonInterface.Axon_Interface(mode=downloadMode)

    if downloadDirectory is None:
        exitCode, cmdOutput, cmdError = axonInt.receiveCmd(axonID)
    else:
        exitCode, cmdOutput, cmdError = axonInt.receiveCmd(axonID, downloadDirectory)

    if exitCode == 0:
        success = axonInt.validateDownload(downloadDirectory, axonID)
    else:
        success = False

    commandOutput = {"success"          : success,
                     "axonID"           : axonID,
                     "downloadDirectory": os.path.join(downloadDirectory, axonID),
                     "exitCode"         : exitCode,
                     "cmdOutput"        : cmdOutput,
                     "cmdError"         : cmdError}
    if debug:
        print("Status of AXON download: ", commandOutput)

    if success:
        metaDataFile = os.path.join(downloadDirectory, axonID, "record-intel-driveinfo-json-v1.json")
        uploadFile = os.path.join(downloadDirectory, axonID, "intel-driveinfo-zip-v1.zip")
        axonURL = axonInt.GetURL()
    else:
        metaDataFile = None
        uploadFile = None
        axonURL = None

    # Verify AXON INI download save.
    axonProfiler = src.software.axon.axonProfile.AxonProfile()
    (axonIDs, axonConfig) = axonProfiler.GetProfile()

    return (commandOutput, axonID, axonURL, metaDataFile, uploadFile, axonIDs, axonConfig)


def generateAllContent(debug=True,
                       logoFileName="software/Intel_IntelligentSystems.png",
                       inputFolder="data/inputSeries",
                       autoParseFolder="Auto-Parse/decode/ADP_UV",
                       dataCntrlFolder="Auto-Parse/datacontrol",
                       nlogFolder="software/parse/nlogParser",
                       outputFolder="data/output",
                       credentialsFile=".raadProfile/credentials.conf",
                       reportName="RAD_Report",
                       username="lab", password="lab",
                       axonMode="test",
                       subSequenceLength=1, matrixProfileFlag=False,
                       inputWidth=70, labelWidth=20, shift=2, hiddenLayers=128,
                       batchSize=32, maxEpochs=2096,
                       embeddedEncodingFlag=False, categoricalEncodingFlag=False,
                       inParallel=False,
                       inParallelLocal=False,
                       inOrder=True,
                       requiredList=None,
                       skipPhases=None):
    """ Generation of content in one simple API.
    Args:
        nlogFolder: Nlog meta folder
        debug: Developer debug flag.
        logoFileName: Product logo image.
        inputFolder: Input directory with telemetry binaries.
        autoParseFolder: auto parser folders.
        dataCntrlFolder: data control folder.
        outputFolder: output folder for generated files.
        credentialsFile: credential cache file with name and password.
        reportName: Output report name.
        username: User name for RAAD.
        password: Password name for RAAD.
        axonMode: Axon mode of operation.
        subSequenceLength: Sequence length for matrix profile.
        matrixProfileFlag: Flag to perform matrix profile.
        inputWidth: Input data width for AI NN.
        labelWidth: Label data width for AI NN.
        shift: AI shift variable.
        hiddenLayers: AI NN hidden layers.
        batchSize: AI batch size.
        maxEpochs: AI Epochs.
        embeddedEncodingFlag: AI embedded encoding for meta data.
        categoricalEncodingFlag: AI catagorical encoding flag for meta data.
        inParallel: Parallel sub-functions.
        inParallelLocal: Local parallel functions.
        inOrder: Flag to process out of order or in order. Be careful with data dependency.
        requiredList: List of strings fort he names of objects to be processed indicating whether the objects to be processed should be limited to the ones. Contained in the requiredList. If None, the default list will be used.
        skipPhases: Phases in the auto API to skip
    Returns: Display report dictionary.
    """
    runSequential = not inParallelLocal

    if skipPhases is None:
        skipPhases = [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14]  # [8, 9]  # [6, 7, 8, 9] [1, 4, 5, 6, 7, 8, 9]

    if requiredList is None:
        requiredList = OI

    # Create time series files.
    if inParallelLocal:
        max_workers = None
    else:
        max_workers = 1

    # Tracking variables for data generation
    pdfFilesTimeSeries = list()
    pdfFilesDH = list()
    pdfNameListARMA = list()
    pdfNameListRNN = list()

    timeOut = 60 * 60  # 60 seconds * 60 minutes := 1 hour

    logoFileName = tryFile(fileName=logoFileName)

    inputFolder = tryFolder(path=inputFolder)
    autoParseFolder = tryFolder(path=autoParseFolder)
    dataCntrlFolder = tryFolder(path=dataCntrlFolder)
    dataCntrlStructPath = tryFile(dataCntrlFolder, 'structures.csv', walkUpLimit=3)
    outputFolder = tryFolder(path=outputFolder)
    if outputFolder is None:
        outputFolder = os.path.abspath("../data/output")
    nlogFolder = tryFolder(path=nlogFolder)
    if nlogFolder is None:
        nlogFolder = os.path.abspath("software/parse/nlogParser")
    credentialsFile = tryFolder(path=credentialsFile)

    # Delete output folder contents and recreate
    try:
        shutil.rmtree(path=outputFolder, ignore_errors=True)
    except OSError as errorOccurrence:
        print(f"Error delete: {outputFolder} {errorOccurrence.strerror}")
        pass
    try:
        os.makedirs(outputFolder, mode=0o777, exist_ok=True)
    except OSError as errorOccurrence:
        print(f"Error create: {outputFolder} {errorOccurrence.strerror}")
        pass

    # Constants
    handBookFile = os.path.join(outputFolder, "debugHandbookCache.ini")
    timeSeriesFile = os.path.join(outputFolder, "telemetryDefault", "timeSeries")
    defragHistoryFile = os.path.join(outputFolder, "telemetryDefault", "defragHistory")

    filePrefix = "Tv2HiTAC"  # Gen file prefix
    fileTokenNamePostfix = 'TokenData.ini'  # Token postfix
    fileZipNamePostfix = 'MetaData.zip'  # Zip file postfix

    fileAnalysisLogName = os.path.join(outputFolder, "autoModule.log")
    fileAnalysisLog = open(fileAnalysisLogName, 'w')

    # Gather data from live drive.
    # Phase 1
    if 1 not in skipPhases:
        generateBinaryDataSet()

    # Parse data from input folder.
    # @todo note operationMode=3 is Parse
    # @todo autoParseMode is ADP or CDR flag, this should be pulled from the telemetry header
    # Phase 2
    if 2 not in skipPhases:
        (dataFileName, dataZipFileName,
         telemetryBinaryObj, parseBinList, binOutputFolder,
         telemetryFormatObj, validExtraction,
         packageObj, telemetryDataDictionary, telemetryDataDictionaryFlat, telemetryDataDictionaryFlatSize,
         driveInformation) = generateParseDataSet(containingFolder=inputFolder, autoParseFolder=autoParseFolder,
                                                  outFolder=outputFolder,
                                                  nlogFolder=nlogFolder,
                                                  operationMode=3, autoParseMode=2, debug=debug,
                                                  fileIdentifier=filePrefix,
                                                  timeName=None,
                                                  fileTokenName=fileTokenNamePostfix,
                                                  fileMetaName=fileZipNamePostfix,
                                                  skipZip=True)
        telemetryDataDictionaryUIDList = list((telemetryDataDictionary.keys()))
        telemetryDataDictionaryUIDList = sorted(telemetryDataDictionaryUIDList, key=lambda x: int(strip_start(stringInput=x, prefix='uid-')))
        pprint.pprint(object="generateParseDataSet()", stream=fileAnalysisLog)
        pprint.pprint(object=dataFileName, stream=fileAnalysisLog)
        pprint.pprint(object=dataZipFileName, stream=fileAnalysisLog)
        pprint.pprint(object=telemetryBinaryObj, stream=fileAnalysisLog)
        pprint.pprint(object=parseBinList, stream=fileAnalysisLog)
        pprint.pprint(object=binOutputFolder, stream=fileAnalysisLog)
        pprint.pprint(object=telemetryFormatObj, stream=fileAnalysisLog)
        pprint.pprint(object=validExtraction, stream=fileAnalysisLog)
        pprint.pprint(object=packageObj, stream=fileAnalysisLog)
        pprint.pprint(object=telemetryDataDictionary, stream=fileAnalysisLog)
        pprint.pprint(object=telemetryDataDictionaryFlat, stream=fileAnalysisLog)
        pprint.pprint(object=telemetryDataDictionaryFlatSize, stream=fileAnalysisLog)
        pprint.pprint(object=driveInformation, stream=fileAnalysisLog)
    else:
        dataFileName = None
        telemetryDataDictionaryFlatSize = None
        telemetryDataDictionary = None
        # dataZipFileName = None
        # telemetryBinaryObj = parseBinList = binOutputFolder = None
        # telemetryFormatObj = validExtraction = None
        # packageObj = telemetryDataDictionary = telemetryDataDictionaryFlat = telemetryDataDictionaryFlatSize = None
        driveInformation = None
        telemetryDataDictionaryUIDList = None

    # Gather debug handbook data.
    # @todo note searchString should be pulled from the telemetry header
    # Phase 3
    if 3 not in skipPhases:
        # fix incorrectness of searchString if any
        BADASSERTTAGS = {'ASSERT_DF0049': 'ASSERT_DF049'}
        final = cleanSearchString(searchString=driveInformation["DeviceStatus"])
        if final in BADASSERTTAGS:
            final = BADASSERTTAGS[final]

        (passwordEncodingObject, password_hash, handbookInfo, dataMatch) = generateHandbook(username=username, password=password,
                                                                                            passwordEncodingObjectSaved=None,
                                                                                            defaultPasswordFile=credentialsFile,
                                                                                            outCacheFile=handBookFile,
                                                                                            searchString=final,
                                                                                            similarityScoreThreshold=0.95,
                                                                                            debug=debug)
        pprint.pprint(object="generateHandbook()", stream=fileAnalysisLog)
        pprint.pprint(object=passwordEncodingObject, stream=fileAnalysisLog)
        pprint.pprint(object=password_hash, stream=fileAnalysisLog)
        pprint.pprint(object=handbookInfo, stream=fileAnalysisLog)
        pprint.pprint(object=dataMatch, stream=fileAnalysisLog)
    else:
        dataMatch = None

    # Prepare list of args to execute in open core threads.
    # Setup pool, run, and check pool results.
    # Phase 4
    if 4 not in skipPhases:
        kwargsList_TS = [{'inputINI'         : os.path.join(outputFolder, dataFileName),
                          'outputFile'       : timeSeriesFile,
                          'subSequenceLength': subSequenceLength,
                          'matrixProfileFlag': matrixProfileFlag,
                          'debug'            : debug,
                          'inParallel'       : inParallel,
                          'requiredList'     : requiredList,
                          'timeOut'          : timeOut}]
        functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                         functionName=generateTimeSeriesGraphs,
                                                                         fParameters=kwargsList_TS,
                                                                         workers=max_workers,
                                                                         timeOut=timeOut,
                                                                         inOrder=inOrder,
                                                                         runSequential=runSequential)
        iResults = functionContext.execute()
        pdfFilesTimeSeries = iResults
        pdfFilesTimeSeries = flattenList(inList=pdfFilesTimeSeries)
        pprint.pprint(object="generateTimeSeriesGraphs()", stream=fileAnalysisLog)
        pprint.pprint(object=pdfFilesTimeSeries, stream=fileAnalysisLog)
        pprint.pprint(object=pdfFilesTimeSeries)

    # Phase 5
    if 5 not in skipPhases:
        # @todo Mode is ADP or CDR flag, this should be pulled from the telemetry header
        productFamily = driveInformation["product"]

        if productFamily == 'Arbordale Plus':
            mode = 1
            numCores = 1  # Actually 4 cores, we use two media banks.
        elif productFamily == 'Cliffdale Refresh':
            mode = 2
            numCores = 1
        else:
            mode = 1
            numCores = 2  # Actually 4 cores, we use two media banks.
            print(f"Error in product map match {productFamily}")
        kwargsList_DH = [{'inputINI'     : os.path.join(outputFolder, dataFileName),
                          'outputFile'   : defragHistoryFile,
                          'mode'         : mode,
                          'numCores'     : numCores,
                          'bandwidthFlag': True,
                          'debug'        : debug}]
        functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                         functionName=generateDefragHistory,
                                                                         fParameters=kwargsList_DH,
                                                                         workers=max_workers,
                                                                         timeOut=timeOut,
                                                                         inOrder=inOrder,
                                                                         runSequential=runSequential)
        iResults = functionContext.execute()
        pdfFilesDH = iResults
        pdfFilesDH = flattenList(inList=pdfFilesDH)
        pprint.pprint(object="generateDefragHistory()", stream=fileAnalysisLog)
        pprint.pprint(object=pdfFilesDH, stream=fileAnalysisLog)

    # Phase 6
    if 6 not in skipPhases:
        kwargsList_ARMA = [{'inputINI'         : os.path.join(outputFolder, dataFileName),
                            'subSequenceLength': subSequenceLength,
                            'matrixProfileFlag': matrixProfileFlag,
                            'debug'            : debug,
                            'inParallel'       : inParallel,
                            'requiredList'     : requiredList,
                            'outFolder'        : outputFolder}]
        functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                         functionName=generateARMA,
                                                                         fParameters=kwargsList_ARMA,
                                                                         workers=max_workers,
                                                                         timeOut=timeOut,
                                                                         inOrder=inOrder,
                                                                         runSequential=runSequential)
        iResults = functionContext.execute()
        pdfNameListARMA = iResults
        pdfNameListARMA = flattenList(inList=pdfNameListARMA)
        pprint.pprint(object="generateARMA()", stream=fileAnalysisLog)
        pprint.pprint(object=pdfNameListARMA, stream=fileAnalysisLog)

    readDataFilePath = os.path.join(outputFolder, dataFileName)
    # Phase 7
    if 7 not in skipPhases:
        kwargsList_RNN = [{'inputINI'               : readDataFilePath,
                           'subSequenceLength'      : subSequenceLength,
                           'matrixProfileFlag'      : matrixProfileFlag,
                           'batchSize'              : batchSize,
                           'maxEpochs'              : maxEpochs,
                           'inputWidth'             : inputWidth,
                           'labelWidth'             : labelWidth,
                           'shift'                  : shift,
                           'hiddenLayers'           : hiddenLayers,
                           'embeddedEncodingFlag'   : embeddedEncodingFlag,
                           'categoricalEncodingFlag': categoricalEncodingFlag,
                           'debug'                  : debug,
                           'inParallel'             : inParallel,
                           'requiredList'           : requiredList,
                           'timeOut'                : timeOut,
                           'max_workers'            : max_workers}]
        functionContext = MassiveParallelismSingleFunctionManyParameters(debug=debug,
                                                                         functionName=generateRNNLSTM,
                                                                         fParameters=kwargsList_RNN,
                                                                         workers=max_workers,
                                                                         timeOut=timeOut,
                                                                         inOrder=inOrder,
                                                                         runSequential=runSequential)
        iResults = functionContext.execute()
        pdfNameListRNN = iResults
        pdfNameListRNN = flattenList(inList=pdfNameListRNN)
        pprint.pprint(object="generateRNNLSTM()", stream=fileAnalysisLog)
        pprint.pprint(object=pdfNameListRNN, stream=fileAnalysisLog)

    # Upload found content.
    # Phase 8
    if 8 not in skipPhases:
        (commandOutput, axonID, axonURL, metaDataFile, uploadFile, axonIDs, axonConfig) = generateAXONUpload(contentFile=dataFileName, uploadMode=axonMode, userName=username, debug=debug)
        pprint.pprint(object="generateAXONUpload()", stream=fileAnalysisLog)
        pprint.pprint(object=commandOutput, stream=fileAnalysisLog)
        pprint.pprint(object=axonID, stream=fileAnalysisLog)
        pprint.pprint(object=axonURL, stream=fileAnalysisLog)
        pprint.pprint(object=metaDataFile, stream=fileAnalysisLog)
        pprint.pprint(object=uploadFile, stream=fileAnalysisLog)
        pprint.pprint(object=axonIDs, stream=fileAnalysisLog)
        pprint.pprint(object=axonConfig, stream=fileAnalysisLog)
    else:
        # commandOutput = axonURL = metaDataFile = uploadFile = axonIDs = axonConfig = None
        axonID = None

    # Download content.
    # Phase 9
    if 9 not in skipPhases:
        (commandOutput, axonID, axonURL, metaDataFile, uploadFile, axonIDs, axonConfig) = generateAXONDownload(axonID=axonID, downloadDirectory=outputFolder, downloadMode=axonMode, debug=debug)
        pprint.pprint(object="generateAXONDownload()", stream=fileAnalysisLog)
        pprint.pprint(object=commandOutput, stream=fileAnalysisLog)
        pprint.pprint(object=axonID, stream=fileAnalysisLog)
        pprint.pprint(object=axonURL, stream=fileAnalysisLog)
        pprint.pprint(object=metaDataFile, stream=fileAnalysisLog)
        pprint.pprint(object=uploadFile, stream=fileAnalysisLog)
        pprint.pprint(object=axonIDs, stream=fileAnalysisLog)
        pprint.pprint(object=axonConfig, stream=fileAnalysisLog)

    # Phase 10
    if 10 not in skipPhases:
        # ###################### JIRA Mining Phase (Preprocessing/Analysis/Visualization) ######################
        execute = executeJiraMining(datakey=str(driveInformation['DeviceStatus']))
        success, finalTables, tableTitles = execute.executeAllJobs(embeddingType='bert',
                                                                   knownCauses=dataMatch['knownCauses'],
                                                                   credFile=credentialsFile)
        jiraAnalysisPDFList = [
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ClusterPlotPCA.pdf')),
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ClusterPlotTSNE.pdf')),
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ChooseClusterCount.pdf')),
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/DistanceBetweenGMMs.pdf')),
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/SilhouetteClusterCount.pdf')),
            os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/GradientBicScores.pdf'))
        ]
        if success:
            print(f'Successful mining of jiras with search string: {driveInformation["DeviceStatus"]}')
    else:
        finalTables = None
        jiraAnalysisPDFList = None
        tableTitles = None

    # Phase 11
    if 11 not in skipPhases:
        print("Executing Nlog Prediction ... ")
        nlogFileFolder = os.path.join(outputFolder, "nlog")
        nlogParserFolder = nlogFolder
        # Executing Nlog Prediction with default values for simplicity. For full execution, please refer to the script
        # or the GUI
        nlogPredictor = src.software.autoAI.nlogPrediction.NlogPredictor(nlogFolder=nlogFileFolder,
                                                                         nlogParserFolder=nlogParserFolder)
        nlogPredictor.nlogPredictorAPI()

    # Phase 12
    if 12 not in skipPhases:
        print("Extracting NLOG Table...")
        nlogFileName = dataFileName.replace(".ini", "_NLOG.txt")
        nlogFilePath = os.path.join(outputFolder, "nlog")
        nlogFilePath = os.path.join(nlogFilePath, nlogFileName)
        nlogTable = src.software.autoAI.nlogPrediction.NlogUtils().extractNlogTable(nlogFilePath)
    else:
        nlogTable = None

    # Phase 13
    if 13 not in skipPhases:
        # Prepare report
        # Generate LaTeX simulate generation of beautiful report.
        deviceConfiguration = telemetryDataDictionary["uid-58"] if "uid-58" in telemetryDataDictionary else None
        dataDict = telemetryDataDictionary
        dataDictDimensions = telemetryDataDictionaryFlatSize

        DFA = None

        DFG = dict()
        for tddKey in telemetryDataDictionary:
            tddContent = telemetryDataDictionary[tddKey]
            keyWithinOI = tddKey in OI
            keyWithinTDD = tddKey in telemetryDataDictionary.keys()
            if keyWithinOI and keyWithinTDD:
                DFG[tddKey] = tddContent
        if DFG == dict():
            DFG = None

        CFG = dict()
        for tddKey in telemetryDataDictionary:
            tddContent = telemetryDataDictionary[tddKey]
            keyWithinUIDStack = tddKey in UIDs_Stack
            keyWithinTDD = tddKey in telemetryDataDictionary.keys()
            if keyWithinUIDStack and keyWithinTDD:
                CFG[tddKey] = tddContent
        if CFG == dict():
            CFG = None

        MLProfiles = None
        assistedFigures = pdfFilesDH + pdfFilesTimeSeries
        timeSeriesSignatures = pdfNameListARMA + pdfNameListRNN
        configFile = os.path.join(outputFolder, dataFileName)
        reportDictionary = GatherMeta(binaryPath=inputFolder,
                                      fwDir=autoParseFolder,
                                      dataCntrlStructPath=dataCntrlStructPath,
                                      nlogFolder=nlogFolder,
                                      configFileName=configFile,
                                      resultsFolder=outputFolder,
                                      debug=debug)

        reportDictionary.updateReportMeta(uidsFound=telemetryDataDictionaryUIDList,
                                          deviceConfiguration=deviceConfiguration,
                                          dataDict=dataDict,
                                          dataDictDimension=dataDictDimensions,
                                          DFA=DFA,
                                          CFG=CFG,
                                          DFG=DFG,
                                          MLProfiles=MLProfiles,
                                          jiraNeighbors=finalTables,
                                          jiraFigures=jiraAnalysisPDFList,
                                          tableTitles=tableTitles,
                                          assistedFigures=assistedFigures,
                                          nlogTable=nlogTable,
                                          timeSeriesSignatures=timeSeriesSignatures)

        # Instantiate class for axon upload
        # axonInt = software.axon.axonInterface.Axon_Interface(mode=mode)
        # Create meta data file for AXON upload
        # metaData, metaDataFile = self.formMetaData(axonInt=axonInt, contentFile=zipFile)
        # Create meta data file for AXON upload
        # success, axonID = axonInt.sendInfo(metaDataFile=metaDataFile, contentFile=zipFile)
        # analysisReport.setDataLakeMeta(axonID, axonURL=axonInt.GetURL(), MetaDataFile=metaDataFile, UploadedFile=contentFile)
        reportItems = reportDictionary.getClasstoDictionary()  # reportDictionary.__repr__()
        pprint.pprint(reportItems)

        # Creation of Final Report
        reportObj = ReportGenerator(outPath=outputFolder,
                                    fileName=reportName,
                                    logoImage=logoFileName,
                                    debug=debug)

        reportObj.createDocumentRAAD(systemInfo=reportItems)
    else:
        reportDictionary = None

    sys.stdout.flush()  # Flush stream
    fileAnalysisLog.close()  # Close log file

    if 14 not in skipPhases:
        packageObj = src.software.axon.packageInterface.packageInterface(absPath=outputFolder,
                                                                         timeSeriesFile=readDataFilePath,
                                                                         debug=debug).createZIP(zipFileName=fileZipNamePostfix)
    else:
        packageObj = None

    return reportDictionary, packageObj


def generateJIRAClusters(debug=True,
                         faultSignature="ASSERT_DE003",
                         outputFolder="data/output",
                         credentialsFile=".raadProfile/credentials.conf",
                         logoFileName="software/Intel_IntelligentSystems.png",
                         inputFolder="data/inputSeries",
                         dataCntrlFolder="Auto-Parse/datacontrol",
                         autoParseFolder="Auto-Parse/decode/ADP_UV",
                         nlogFolder='.',
                         filePrefix="Tv2HiTAC",  # Gen file prefix
                         fileTokenNamePostfix='TokenData.ini',  # Token postfix
                         fileZipNamePostfix='MetaData.zip',  # Zip file postfix
                         fileAnalysisLogName="autoModule.log"):
    """
    Generation of content in one simple API.
    Args:
        fileAnalysisLogName: log analysis file
        fileZipNamePostfix: filename token
        fileTokenNamePostfix: filename token
        filePrefix: set Prefix for processing
        nlogFolder: negative log folder
        autoParseFolder: Tokenizers folder
        dataCntrlFolder: data control folder.
        inputFolder: input directory
        logoFileName: logo file to be used
        faultSignature: fault code.
        debug: Developer debug flag.
        outputFolder: output folder for generated files.
        credentialsFile: credential cache file with name and password.
    Returns: Display report dictionary.
    """
    logoFileName = tryFile(fileName=logoFileName)
    inputFolder = tryFolder(path=inputFolder)
    autoParseFolder = tryFolder(path=autoParseFolder)
    nlogFolder = tryFolder(path=nlogFolder)
    dataCntrlStructPath = tryFile(dataCntrlFolder, 'structures.csv', walkUpLimit=3)
    if nlogFolder is None:
        nlogFolder = os.path.abspath("software/parse/nlogParser")
    credentialsFile = tryFolder(path=credentialsFile)

    cacheFolder = tryFolder(path="../.raadProfile")
    if cacheFolder is None:
        cacheFolder = os.path.abspath("../.raadProfile")

    outputFolder = tryFolder(path=outputFolder)
    if outputFolder is None:
        outputFolder = os.path.abspath("../data/output")
    fileAnalysisLogName = os.path.join(outputFolder, fileAnalysisLogName)
    if not os.path.exists(fileAnalysisLogName):
        fileAnalysisLog = open(fileAnalysisLogName, 'w')
        pprint.pprint(object="", stream=fileAnalysisLog)
        sys.stdout.flush()  # Flush stream
        fileAnalysisLog.close()  # Close log file
    fileAnalysisLog = open(fileAnalysisLogName, 'w')

    # Delete output folder contents and recreate
    try:
        shutil.rmtree(path=outputFolder, ignore_errors=True)
    except OSError as errorOccurrence:
        print(f"Error delete: {outputFolder} {errorOccurrence.strerror}")
        pass
    try:
        os.makedirs(outputFolder, mode=0o777, exist_ok=True)
    except OSError as errorOccurrence:
        print(f"Error create: {outputFolder} {errorOccurrence.strerror}")
        pass

    handBookFile = os.path.join(cacheFolder, "debugHandbookCache.ini")
    if not os.path.exists(handBookFile):
        handBookFileLog = open(handBookFile, 'w')
        pprint.pprint(object="", stream=handBookFileLog)
        sys.stdout.flush()  # Flush stream
        handBookFileLog.close()  # Close log file
    # @todo: stella parse binary files by parser --> dictionary to store assert code and parser
    (dataFileName, dataZipFileName,
     telemetryBinaryObj, parseBinList, binOutputFolder,
     telemetryFormatObj, validExtraction,
     packageObj, telemetryDataDictionary, telemetryDataDictionaryFlat, telemetryDataDictionaryFlatSize,
     driveInformation) = generateParseDataSet(containingFolder=inputFolder, autoParseFolder=autoParseFolder,
                                              outFolder=outputFolder,
                                              nlogFolder=nlogFolder,
                                              operationMode=3, autoParseMode=2, debug=debug,  # @todo: replace operationMode with firmware version
                                              fileIdentifier=filePrefix,  # @ todo: stella replace
                                              timeName=None,
                                              fileTokenName=fileTokenNamePostfix,
                                              fileMetaName=fileZipNamePostfix,
                                              skipZip=True)
    telemetryDataDictionaryUIDList = list((telemetryDataDictionary.keys()))
    telemetryDataDictionaryUIDList = sorted(telemetryDataDictionaryUIDList,
                                            key=lambda x: int(strip_start(stringInput=x, prefix='uid-')))
    pprint.pprint(object=telemetryDataDictionaryUIDList, stream=fileAnalysisLog)
    pprint.pprint(object="generateParseDataSet()", stream=fileAnalysisLog)
    pprint.pprint(object=dataFileName, stream=fileAnalysisLog)
    pprint.pprint(object=dataZipFileName, stream=fileAnalysisLog)
    pprint.pprint(object=telemetryBinaryObj, stream=fileAnalysisLog)
    pprint.pprint(object=parseBinList, stream=fileAnalysisLog)
    pprint.pprint(object=binOutputFolder, stream=fileAnalysisLog)
    pprint.pprint(object=telemetryFormatObj, stream=fileAnalysisLog)
    pprint.pprint(object=validExtraction, stream=fileAnalysisLog)
    pprint.pprint(object=packageObj, stream=fileAnalysisLog)
    pprint.pprint(object=telemetryDataDictionary, stream=fileAnalysisLog)
    pprint.pprint(object=telemetryDataDictionaryFlat, stream=fileAnalysisLog)
    pprint.pprint(object=telemetryDataDictionaryFlatSize, stream=fileAnalysisLog)
    pprint.pprint(object=driveInformation, stream=fileAnalysisLog)

    # @todo hack for DE003 injection
    if isinstance(driveInformation["DeviceStatus"], str):
        faultSignature = cleanSearchString(searchString=driveInformation["DeviceStatus"])
    elif isinstance(faultSignature, str):
        driveInformation["DeviceStatus"] = faultSignature
    else:
        driveInformation["DeviceStatus"] = "ASSERT_DE003"
        faultSignature = driveInformation["DeviceStatus"]

    # Gather debug handbook data.
    # @todo note searchString should be pulled from the telemetry header
    # Phase 3
    (passwordEncodingObject, password_hash, handbookInfo, dataMatch) = generateHandbook(passwordEncodingObjectSaved=None,
                                                                                        defaultPasswordFile=credentialsFile,
                                                                                        outCacheFile=handBookFile,
                                                                                        searchString=faultSignature,
                                                                                        similarityScoreThreshold=0.95,
                                                                                        debug=debug)
    pprint.pprint(object="generateHandbook()", stream=fileAnalysisLog)
    pprint.pprint(object=passwordEncodingObject, stream=fileAnalysisLog)
    pprint.pprint(object=password_hash, stream=fileAnalysisLog)
    pprint.pprint(object=DictionaryFlatten().getSuperDictionary(inDictionary=handbookInfo), stream=fileAnalysisLog)
    pprint.pprint(object=dataMatch, stream=fileAnalysisLog)

    # Phase 10

    # ###################### JIRA Mining Phase (Preprocessing/Analysis/Visualization) ######################
    execute = executeJiraMining(datakey=str(faultSignature))
    success, finalTables, tableTitles = execute.executeAllJobs(embeddingType='bert',
                                                               knownCauses=dataMatch['knownCauses'],
                                                               credFile=credentialsFile)
    jiraAnalysisPDFList = [
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ClusterPlotPCA.pdf')),
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ClusterPlotTSNE.pdf')),
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/ChooseClusterCount.pdf')),
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/DistanceBetweenGMMs.pdf')),
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/SilhouetteClusterCount.pdf')),
        os.path.abspath(os.path.join(outputFolder, 'jiraDataStore/GradientBicScores.pdf'))
    ]
    if success:
        print(f'Successful mining of jiras with search string: {faultSignature}')

    # Finish report
    reportDictionary = GatherMeta(binaryPath=None,
                                  fwDir=None,
                                  dataCntrlStructPath=dataCntrlStructPath,
                                  nlogFolder=None,
                                  configFileName=None,
                                  resultsFolder=outputFolder,
                                  debug=debug)

    reportDictionary.updateReportMeta(uidsFound=None,
                                      deviceConfiguration=None,
                                      dataDict=None,
                                      dataDictDimension=None,
                                      DFA=None,
                                      CFG=None,
                                      DFG=None,
                                      MLProfiles=None,
                                      jiraNeighbors=finalTables,
                                      jiraFigures=jiraAnalysisPDFList,
                                      tableTitles=tableTitles,
                                      assistedFigures=None,
                                      nlogTable=None,
                                      timeSeriesSignatures=None)

    reportItems = reportDictionary.getClasstoDictionary()  # reportDictionary.__repr__()
    pprint.pprint(reportItems)

    # Creation of Final Report
    reportObj = ReportGenerator(outPath=outputFolder,
                                fileName="JiraReport",
                                logoImage=logoFileName,
                                debug=debug)

    reportObj.createDocumentRAAD(systemInfo=reportItems)

    return (success, finalTables, jiraAnalysisPDFList, tableTitles)


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
    print("options: ", str(options.mode))

    if options.mode:
        # Generic layouts for all APIs
        generateAllContent(debug=options.debug)
    else:
        print("Error in Selection")


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default=1, help="Mode of Operation.")
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
