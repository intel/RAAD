#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re, sys, os, time, datetime

##############################################
# Python generic info
##############################################
"""
Requires
    https://graphviz.gitlab.io/_pages/Download/windows/graphviz-2.38.msi
    install path https://graphviz.gitlab.io/_pages/Download/windows/graphviz-2.38.msi
    Add to path C:\\Program Files (x86)\\Graphviz2.38\\bin\\dot.exe
"""
##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0], os.path.split(sys.argv[0])[1] + '.exe')

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0, twidlcore)

##############################################
# Libraries
##############################################
#### import test utilities
from src.software.parse.internal.drive_utility import testDrive
from src.software.parse.internal.drive_utility import driveList

#### import telemetry modules
from src.software.parse.telemetry_drive import logDevice
from src.software.parse.internal.getTelemetry import readTelemetryLog
from src.software.parse.telemetry_util import openWriteFile

##############################################
# Helpers for accessing data.
##############################################
def findExecutable(executable='', path=None):
    """Tries to find 'executable' in the directories listed in 'path'.
    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    if path is None:
        path = os.environ.get('PATH', os.defpath)

    paths = path.split(os.pathsep)
    # base, ext = os.path.splitext(executable)

    if (sys.platform == 'win32' or os.name == 'os2'):
        exts = ['.exe', '.bat', '']
    else:
        exts = ['', '.sh']

    if not os.path.isfile(executable):
        for ext in exts:
            newexe = executable + ext
            if os.path.isfile(newexe):
                return newexe
            else:
                for p in paths:
                    f = os.path.join(p, newexe)
                    if os.path.isfile(f):
                        # The file exists, we have a shot at spawn working
                        return f
    else:
        return executable
    return None


def IntelIMASCommand(tool='intelmas', operation='dump', outputFile='telemetry_data.bin', driveNumber=1):
    """
    Attributes
        @param tool is the tool command to send.
        @param operation is the operation to perform based on documentation.
        @param outputFile is the file name to save.
        @param driveNumberis the drive ID number.
    @return
    Notes:
        IMAS
            https://downloadmirror.intel.com/29337/eng/Intel_Memory_And_Storage_Tool_User%20Guide-Public-342245-001US.pdf
            https://downloadcenter.intel.com/download/29337/Intel-Memory-and-Storage-Tool-CLI-Command-Line-Interface-
            Commands
                intelmas show -o json -intelssd
                intelmas show -intelssd 1 -identify
                intelmas dump -destination telemetry_data.bin -intelssd 1 -telemetrylog
                intelmas dump -destination telemetry_data.bin -intelssd 1 -eventlog
        Generic Tools
            https://nsg-wiki.intel.com/pages/viewpage.action?pageId=168672650
            https://github.com/spdk/spdk
            Commands
                git clone https://github.com/spdk/spdk
                cd spdk
                git submodule update --init
                ./scripts/pkgdep.sh
                ./configure --with-shared
                make -j `nproc`
                cd build/lib
                cc -o libspdkfull.so -Wl,--no-as-needed --shared -L../../dpdk/build/lib  -L. -Wl,--whole-archive -Wl,--no-as-needed -lspdk -lspdk_env_dpdk -ldpdk -Wl,--no-whole-archive,-rpath='$ORIGIN'
                mkdir output
                cp build/lib/* output/
                cp dpdk/build/lib/* output/
                from ctypes import CDLL; assert CDLL('dpdk/build/lib/libspdkfull.so')
                from ctypes import CDLL; assert CDLL('dpdk/build/lib/libspdkfull.so').spdk_pci_device_cfg_write32
    """
    import subprocess
    ret = False
    if (tool is not None and
        operation is not None and
        outputFile is not None and
        driveNumber is not None and
        findExecutable(executable=tool) is not None):
        cmd = '"{0}" {1} -destination {2} -intelssd {3} -telemetrylog'.format(
            tool, operation, outputFile, driveNumber
            )
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            ret, output = proc.communicate()
        except:
            print('Executing: {0}'.format(cmd))
            print('The command "%(cmd)s" failed with error ', 'code %(ret)i.' % locals())
    return ret


def devGraphAll():
    ##############################################
    # Debug Graphing
    ##############################################
    #### import necessary paths
    importPath = os.path.abspath(os.getcwd())
    importPathNext = os.path.abspath(os.path.join(importPath, "pycallgraph"))
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    importPathNext = os.path.abspath(os.path.join(importPath, "pycallgraph", "output"))
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    importPathNext = os.path.abspath('C:\\Program Files (x86)\\Graphviz2.38\\bin\\dot.exe')
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    ##############################################
    # Library
    ##############################################
    # conda install -c conda-forge pycallgraph2
    from pycallgraph2 import PyCallGraph
    from pycallgraph2.output import GraphvizOutput
    from pycallgraph2 import Config

    ##############################################
    # Configuration
    ##############################################
    status = 0
    graphviz = GraphvizOutput()
    graphviz.output_type = 'svg'
    graphviz.output_file = 'pycallgraph.svg'

    configList = Config()
    configList.output = None
    configList.verbose = True
    configList.debug = False
    configList.groups = True
    configList.threaded = False
    configList.max_depth = 2 ** 31

    with PyCallGraph(output=graphviz, config=configList):
        callReturn = 1
        print("PyCallGraphReturn", callReturn)
        # status = testDrive(driveNumber) # Debug code goes here
    return status

class fileCollector():
    def __init__(self,
                 instanceName=None,
                 major=1,
                 minor=0,
                 folder="fileCollector",
                 debug=False,
                 verbose=False
                 ):
        # Instance Name
        self.instanceName = instanceName
        # VERSION Major
        self.major = major
        # VERSION Minor
        self.minor = minor
        # Collection staging area
        self.folder = folder
        self.fullPath = os.path.abspath(folder)
        # File list
        self.fileList = []
        # Debug and verbose mode enable.
        self.debug = debug
        self.verbose = verbose
        # File name expression Cache
        self.fileNameExpressionCache = None
        self.fileNameCompileExpressionCache = None

    def debugEnable(self):
        self.debug = True

    def debugDisable(self):
        self.debug = False

    def verboseEnable(self):
        self.verbose = True

    def verboseDisable(self):
        self.verbose = False

    def getFileCount(self):
        return len(self.fileList)

    def getAll(self):
        return (self.instanceName, self.major, self.minor, self.fileList)

    def printAll(self):
        print ("InstanceName ", self.instanceName)
        print (" Major ", self.major)
        print (" Minor ", self.minor)
        print (" Folder ", self.folder)
        print (" Full Folder Path ", self.fullPath)
        for indexer, itemName in enumerate(self.fileList):
            print (" FileList ", itemName)
        print(" File Name Expression Cache Status ", self.fileNameExpressionCache)
        print(" File Name Compile Expression Cache Status ", self.fileNameCompileExpressionCache)
        # Debug and verbose mode enable.
        print(" Debug Mode Status ", self.debug)
        print(" Verbose Mode Status ", self.verbose)
        return

    def setAll(self,
               instanceName=None,
               typeDef=None,
               major=None,
               minor=None,
               fileList=None):
        changeCount = 0
        if (instanceName is not None):
            self.instanceName = instanceName
            changeCount += 1
        if (major is not None):
            self.major = major
            changeCount += 1
        if (minor is not None):
            self.minor = minor
            changeCount += 1
        if (fileList is not None):
            self.fileList = fileList
            changeCount += 1
        return changeCount

    def appendFile(self, fileName=None):
        changeCount = 0
        if (fileName is not None):
            (self.fileList).append(fileName)
            changeCount += 1
        return changeCount

    def removeFile(self, fileName=None):
        changeCount = 0
        if (fileName in (self.fileList)):
            (self.fileList).remove(fileName)
            changeCount += 1
        return changeCount

    def getFile(self):
        from collections import deque
        dList = deque(self.fileList)
        return  (dList).popLeft()

    def clearFileList(self, fileList=None):
        changeCount = 0
        self.fileList = []
        changeCount += 1
        return changeCount

    def loadFiles(self, pathToSearch="C:\\Source\\test\\path\\", endSwitchName=".bin", saveInternal=True):
        foundList = []
        rootDir = pathToSearch
        isFirst = True
        for (folder, dirs, files) in os.walk(rootDir):
            for fileSelected in files:
                if isFirst is False:
                    matchStatus = self.__nameMatchUseCache(fileName=fileSelected)
                else:
                    matchStatus = self.__nameMatch(fileName=fileSelected, cacheExpression=True)
                    isFirst = False
                if (matchStatus is not None):
                    if (self.debug is True):
                        print("File Matched: ", fileSelected)
                    if (saveInternal is True):
                        self.fileList.append(fileSelected)
                else:
                    print("File Evaluated: ", fileSelected)
                    foundList.append(fileSelected)
        return foundList

    def __constructExpression(self, expression=None, cacheExpression=True):
        if (expression is None):
            # Pre-determined file name format, then underscore. I.E. 'Tv2HiTAC_'
            # UTC 4 digit year, then dash. I.E. '2020'
            # UTC 2-digit month Number, then dash. I.E. '05'
            # UTC 2-digit day Number, then underscore. I.E. '21'
            # UTC 2-digit hour Number, then dash. I.E. '20'
            # UTC 2-digit minute Number, then dash. I.E. '12'
            # UTC 2-digit second Number, then dash. I.E. '19'
            # UTC 6-digit milli-second Number. I.E. '246000'
            # Dot, then File extension string. I.E. '.bin'
            expression = ['[A-Z][a-z][0-9][A-Z][a-z][A-Z][A-Z][A-Z](_)',
                          '[0-9][0-9][0-9][0-9](-)',
                          '[0-9][0-9](-)',
                          '[0-9][0-9](_)',
                          '[0-9][0-9](-)',
                          '[0-9][0-9](-)',
                          '[0-9][0-9](-)',
                          '[0-9][0-9][0-9][0-9][0-9][0-9]',
                          '(.)(bin)']

        if self.fileNameExpressionCache is not None:
            compressedExpression = self.fileNameExpressionCache
        else:
            compressedExpression = ''
            for iterator, item in enumerate(expression):
                compressedExpression += expression[iterator]
            self.fileNameExpressionCache = compressedExpression
            if(self.debug): print("CompressedExpression ", compressedExpression)
        return compressedExpression

    def __nameMatchUseCache(self, fileName="Tv2HiTAC_2020-05-21-20-12-19-246000.bin"):
        if (self.fileNameExpressionCache is not None and
            self.fileNameCompileExpressionCache is not None):
            matchStatus = (self.fileNameCompileExpressionCache).match(fileName)
        else:
            matchStatus = None
            AssertionError("Error in nameMatchUseCache() one of the cache items are None.")
        return matchStatus

    def __nameMatch(self, fileName="Tv2HiTAC_2020-05-21-20-12-19-246000.bin", regularExpression=None,
                  cacheExpression=True):
        if cacheExpression is True:
            self.__nameMatchCacheUpdate(regularExpressionIn=regularExpression, cacheExpression=cacheExpression)
            matchStatus = (self.fileNameCompileExpressionCache).match(fileName)
        else:
            if regularExpression is None:
                regularExpression = self.__constructExpression(cacheExpression=cacheExpression)
            else:
                regularExpression = self.__constructExpression(expression=regularExpression,
                                                             cacheExpression=cacheExpression)
            fileNameCompileExpression = re.compile(regularExpression)
            matchStatus = (fileNameCompileExpression).match(fileName)
        return matchStatus

    def __nameMatchCacheUpdate(self, regularExpressionIn=None, cacheExpression=None):
        if regularExpressionIn is None:
            self.__constructExpression(cacheExpression=cacheExpression)
        else:
            self.__constructExpression(expression=regularExpressionIn, cacheExpression=cacheExpression)
        if cacheExpression is True:
            self.fileNameCompileExpressionCache = re.compile(self.fileNameExpressionCache)
        return None

    def __nameSplitter(self, nameToToken="Tv2HiTAC_2020-05-21-20-12-19-246000.bin", splitToken="_"):
        splitResult = nameToToken.split("_")  # Split on underscores
        sequenceName = splitResult[0]  # First part of the split is the sequence. Equates to Tv2HiTAC.
        timeUTC = splitResult[1]  # Second part of the split is the shot. Equates to 2020-05-21-20-12-19-246000.
        return sequenceName, timeUTC

    def __filePathSplitter(self, path, inFilePath=r"C:\\test\\path\\Tv2HiTAC_2020-05-21-20-12-19-246000.bin"):
        import os
        if os.path.exists(inFilePath):
            # Input split head = "C:\\test\\path\\", tail = "Tv2HiTAC_2020-05-21-20-12-19-246000.bin"
            (head, tail) = os.path.split(inFilePath)
            path = head
            fileName = tail
        else:
            path, fileName = None, None
        return path, fileName

def telemetrySave(options, selectNumber=1, hostLog=True,
                  block0Size=512, secondaryBlockSize=4096, createLog=True, doubleTOCRead=False,
                  outDir="streamTest", outFile="Tv2HiTAC",
                  totalTime=10, timeStep=5,
                  ):
    driveNumber = driveList.checkDriveIndex(selectNumber)
    if (driveNumber is None): AssertionError("Invalid drive number.")
    drive = testDrive(driveNumber)
    if (drive is None): AssertionError("Drive does not exist.")
    logDrive = logDevice(drive.getTestDrive(), hostLog)

    if os.path.exists(os.path.abspath(outDir)) is False: os.mkdir(outDir)
    if (options.verbose): print(" Path Folder", os.path.abspath(outDir))

    fileList = fileCollector(instanceName=outFile, major=1, minor=0, folder=outDir)
    currentTime = 0
    count = 0
    ##############################################
    # Collect the data in a streaming manner.
    ##############################################
    while (currentTime < totalTime):
        if (options.verbose is False and options.debug is False):
            print(".", end='')
        if (currentTime > totalTime):
            if (options.debug): print("Error in logic early return...")
            return 1

        startIteration = datetime.datetime.now()
        currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S-%f")

        ### Determine what to do.
        drive.globalDriveSpecificParams()
        if (options.debug): print("Get Id information")
        driveState = drive.toStr()
        driveState.strip()
        driveState.replace("\n", "\\n :: ")
        if (options.debug): print(driveState)

        ### Verify drive is not asserted.
        AssertedDrive = False
        if (drive.isDriveAsserted()):
            AssertedDrive = True
        if (options.verbose): print(" Drive Assert Status", AssertedDrive)

        ### Perform Test
        if (options.verbose): print(" Get log data... Iteration", count)
        fileNameString = outFile + "_" + currentTimeUTCString + ".bin"
        # Check for an output directory.
        outFileNameString = os.path.join(outDir, fileNameString)
        telemetryData = openWriteFile(outFileNameString)

        fileList.appendFile(fileNameString)

        if (telemetryData is not None):
            status, ciGeneration = readTelemetryLog(logDrive, telemetryData, secondaryBlockSize, block0Size, createLog,
                                                    doubleTOCRead)
        else:
            status = False

        if (options.verbose):
            if (True == status):
                print(" PASS Iteration", count, "UTC Time ",currentTimeUTCString)
            else:
                print(" FAIL Iteration", count, "UTC Time", currentTimeUTCString)

        stopIteration = datetime.datetime.now()
        if (options.verbose): print(" Iteration Execution time", (stopIteration - startIteration))

        time.sleep(timeStep)  # Wait for 5 seconds.

        waitIteration = datetime.datetime.now()
        if (options.verbose): print(" Iteration Wait time" + str(waitIteration))
        currentTime += int(timeStep)
        count += 1
    if (options.verbose is False and options.debug is False):
        print(" ")
    if (options.verbose): print("Streaming Complete...")
    print("Total Collected binaries are", count)
    if (options.verbose): fileList.printAll()
    return fileList

def telemetryLoad(options, selectNumber=1, hostLog=True,
                  outDir="streamTest", outFile="Tv2HiTAC",
                  ):
    if(options.verbose): print("Attempting Loading files...")
    loadList = fileCollector(instanceName=outFile, major=1, minor=0, folder=outDir, debug=options.debug, verbose=options.verbose)
    loadList.loadFiles(pathToSearch=outDir, endSwitchName=".bin", saveInternal=True)
    if (options.verbose): loadList.printAll()
    print("Total Found binaries are", str(loadList.getFileCount()))
    return loadList

def useAxon(contentFile = 'driveinfocontent.bin', metaFile = 'metadata.bin'):
    #### import necessary paths
    importPath = os.path.abspath(os.getcwd())
    importPathNext = os.path.abspath(os.path.join(importPath, "..\axon"))
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    from src.software.axon import axonInterface
    listAxon = axonInterface.Axon_Interface()
    listAxon.sendCmd(failureFile=None, contentFile=contentFile, metaDataFile=metaFile)

    return listAxon

def main():
    ##############################################
    # Main function, Options
    ##############################################
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                      help='Verbose printing for debug use.')
    parser.add_option("--timeTotal", action='store_true', dest='timeTotal', default=None, help='Total time in Minutes.')
    parser.add_option("--timeStep", action='store_true', dest='timeStep', default=None, help='Time steps in seconds.')
    parser.add_option("--targetFolder", action='store_true', dest='targetFolder', default=None,
                      help='Folder to target saving the files.')
    parser.add_option("--targetFileFormat", action='store_true', dest='targetFileFormat', default=None,
                      help='File format to target saving the files.')
    parser.add_option("--driveSelectNumber", action='store_true', dest='driveSelectNumber', default=None,
                      help='File format to target saving the files.')
    (options, args) = parser.parse_args()

    ##############################################
    # Constants
    ##############################################
    # NVMe configuration constants.
    block0Size = 512 # Header header size.
    secondaryBlockSize = 4096  # Max size is (4096*32) for block size to access data items.
    hostLog = True # Host initiated telemetry asynchronous command.
    createLog = True # We create log for each access.
    doubleTOCRead = False # Debug flag to ensure the header read is consistent.

    ##############################################
    # Options
    ##############################################
    print("Options")
    if (options.timeTotal):
        totalTime = options.timeTotal  # Seconds
    else:
        totalTime = 11  # Seconds
    print(" Total time to execute", totalTime)

    if (options.timeStep and (options.timeStep > totalTime)):
        timeStep = options.timeStep  # Seconds
    elif (totalTime < options.timeStep):
        timeStep = totalTime
    else:
        timeStep = 5  # Seconds.
    print(" Time Step between collections", timeStep)

    if (options.targetFolder):
        outDir = options.targetFolder
    else:
        outDir = "streamTest"
    print(" Output directory", outDir)

    if (options.targetFileFormat):
        outFile = options.targetFileFormat
    else:
        outFile = "Tv2HiTAC"
    print(" File name prefix", outFile)

    if (options.driveSelectNumber):
        driveSelectNumber = options.driveSelectNumber
    else:
        driveSelectNumber = 1
    print(" Selected drive number", driveSelectNumber)

    ##############################################
    # Main Save File List
    ##############################################
    fileList = telemetrySave(options, selectNumber=driveSelectNumber, hostLog=hostLog,
               block0Size=block0Size, secondaryBlockSize=secondaryBlockSize,
               createLog=createLog, doubleTOCRead=doubleTOCRead,
               outDir=outDir, outFile=outFile,
               totalTime=totalTime, timeStep=timeStep,
               )

    ##############################################
    # Main Load File Save List
    ##############################################
    loadList = telemetryLoad(options, selectNumber=driveSelectNumber, hostLog=hostLog,
               outDir=outDir, outFile=outFile,
               )

    if (options.debug): print("Printing Lists", fileList, loadList)

    if (options.debug): # @todo jdtarang in progress
        listFront = loadList.getFile()
        useAxon(contentFile=listFront)
    return 0

######## Main Execute #######
if __name__ == '__main__':
    p = datetime.datetime.now()
    main()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
