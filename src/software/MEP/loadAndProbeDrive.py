# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
""" loadAndProbeSystem.py

This module contains the basic functions for generating a load, preparing a drive and pulling data values from it, using
test commands. The load is generated using FIO, so the input file must be a bash script (.sh file extension).The drive
number of the device to be tested must be passed in both, the load configuration file and as an argument. The load
configuration files must have time-based execution for proper execution of the script.

Args:
    --driveNumber: String representation for the drive number from which to pull the data values
    --driveName: String representation for the name of device interface to get data from
    --inputFile: String representation for the name of the input file where the workload configuration is stored
    --identifier: String representation for the name of the data set that corresponds to the data pull to be executed
    --iterations: String representation for the number of data points to be considered in the time series
    --outputDir: String representation for the name of the output directory where the text files will be stored
    --outFile: Output configuration file suffix (including .ini file extension) where the aggregated data will be stored
    --prepFlag: Boolean flag to indicate if the program should prep the drive before loading it
    --aggregateFlag: Boolean flag to indicate if the program should aggregate all the data into a configuration file
                    (.ini file extension)
    --debug: Boolean flag to activate verbose printing for debug use


Example:
    Default usage:
        $ sudo python loadAndProbeDrive.py
    Specific usage:
        $ sudo python loadAndProbeDrive.py --driveNumber 0 --driveName /dev/nvme0n1 --inputFile rand-write.sh
        --identifier Tv2Hi --iterations 200 --outputDir test1 outFile test1.ini --prepFlag True -- aggregateFlag True
        --debug True

"""
import os
import re
import sys
import optparse
import datetime
import traceback
import subprocess
import src.software.DP.preprocessingAPI as DP

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class loadDriveUtility:
    """
    Utility class containing helper methods
    """

    @staticmethod
    def createDir(dirName):
        """
        function for making a directory inside cwd using the specified name in dirName

        Args:
            dirName: String for path to destination directory

        Returns:

        """
        folder = os.path.join(os.getcwd(), dirName)
        if not os.path.exists(folder):
            os.mkdir(folder)

    @staticmethod
    def _processObjectContent(line, subdict, currentHeaders, prevLine):
        """
        function for processing the content of a line and adding it to its corresponding section of the subdict

        Args:
            line: String content of a line read from the data text file
            subdict: Dictionary containing the aggregated values for an object
            currentHeaders: Dictionary containing the corresponding level headers
            prevLine: String content of the previous line read

        Returns:
            String value for the current line or the value passed in as prevLine

        """
        indentNum = int((len(line) - len(line.lstrip())) / 2)
        commentPattern = re.compile("#")
        processedLine = line.strip()
        processedLine = processedLine.split(":")

        # Check to identify type of line
        if len(processedLine) == 1:
            processedLine = processedLine[0].split("=")
            if len(processedLine) == 1:
                return processedLine[0]

            # Content line with colon as separator
            else:
                if indentNum in currentHeaders:
                    for i in range(indentNum, len(currentHeaders)):
                        currentHeaders.pop(i)
                fieldName = ""
                for key in sorted(currentHeaders.keys()):
                    fieldName = fieldName + currentHeaders[key] + "."
                if processedLine[0].strip() == "":
                    processedLine[0] = prevLine
                fieldName = fieldName + processedLine[0].strip().replace(" ", "")
                values = processedLine[1].strip().split()
                value = values[0]
                if fieldName in subdict:
                    subdict[fieldName].append(value)
                else:
                    subdict[fieldName] = [value]

        # Header line
        elif processedLine[1] == "" or commentPattern.match(processedLine[1].strip()):
            headerValue = processedLine[0].strip()
            currentHeaders[indentNum] = headerValue

        # Content line with colon as separator
        else:
            if indentNum in currentHeaders:
                for i in range(indentNum, len(currentHeaders)):
                    currentHeaders.pop(i)
            fieldName = ""
            for key in sorted(currentHeaders.keys()):
                fieldName = fieldName + currentHeaders[key] + "."
            fieldName = fieldName + processedLine[0].strip()
            values = processedLine[1].strip().split()

            if len(values) == 1:
                value = values[0]
            else:
                value = values[1].strip("(")
                value = value.strip(")")

            if fieldName in subdict:
                subdict[fieldName].append(value)
            else:
                subdict[fieldName] = [value]

        return prevLine

    @staticmethod
    def processTextFile(openFile, resultDict, currentName, currentTime):
        """
        function that extracts the content of a file into a dictionary to be transferred into the configuration file

        Args:
            openFile: File descriptor for the open file
            resultDict: Dictionary containing the objects and fields previously found
            currentName: String for the current object being processed
            currentTime: Datetime object containing the time stamp for the current object being processed

        Returns:

        """
        subdict = {}
        currentHeaders = {}
        lines = openFile.readlines()
        timeElapsed = round(10 * ((currentTime.day * 86400) + (currentTime.hour * 3600) + (currentTime.minute * 60) +
                                  currentTime.second + (currentTime.microsecond / float(10 ** 6))))

        if currentName in resultDict:
            subdict = resultDict[currentName]

        prevLine = ""
        for line in lines:
            prevLine = loadDriveUtility()._processObjectContent(line, subdict, currentHeaders, prevLine)

        if "time" in subdict:
            subdict["time"].append(str(timeElapsed))
        else:
            subdict["time"] = [str(timeElapsed)]
        resultDict[currentName] = subdict

    @staticmethod
    def checkDriveNumber(driveNumber):
        """
        function to set the default value for driveNumber and turn it from
        a string into an int

        Args:
            driveNumber: string representation of int for drive number

        Returns:
            Int value for drive number

        """
        if driveNumber is None:
            return 0
        else:
            return int(driveNumber)

    @staticmethod
    def checkDriveName(driveName):
        """
        function to set the default value for driveName

        Args:
            driveName: Name of device interface to get data from

        Returns:
            String representation of the drive name

        """
        if driveName is None:
            return "/dev/nvme0n1"
        else:
            return driveName

    @staticmethod
    def checkIterations(iterations):
        """
        function to set the default value for iterations and turn it from
        a string into an int

        Args:
            iterations: string representation of int value for the number of iterations

        Returns:
            Int value for number of iterations

        """
        if iterations is None:
            return 200
        else:
            return int(iterations)

    @staticmethod
    def checkIdentifier(identifier):
        """
        function to set the default value for identifier

        Args:
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            String for the name of the data set

        """
        if identifier is None:
            return "test"
        else:
            return identifier

    @staticmethod
    def checkOutputDir(outputDir):
        """
        function to set the default value for outputDir

        Args:
            outputDir: path to the directory where the binaries will be stored

        Returns:
            String representation of the path to the output directory

        """
        if outputDir is None:
            return "media-data"
        else:
            return outputDir

    @staticmethod
    def checkOutFile(outFile):
        """
        function to set the default value for outFile

        Args:
            outFile: Output configuration file suffix (including .ini file extension) where the aggregated data will
                     be stored

        Returns:
            String representation of the output configuration file suffix (including .ini file extension) where the
            aggregated data will be stored

        """
        if outFile is None:
            return "time-series.ini"
        else:
            return outFile

    @staticmethod
    def checkBooleanOption(booleanOption):
        """
        function to set the default value for a boolean option to True and turn it from
        a string into a boolean value

        Args:
            booleanOption: string representation of boolean value for boolean flag

        Returns:
            Boolean value for boolean flag

        """
        if booleanOption is None:
            return True
        elif booleanOption == "False":
            return False
        else:
            return True

    @staticmethod
    def checkDebugOption(debugOptions):
        """
        function to set the default value for debugOptions and turn it from
        a string into a boolean value

        Args:
            debugOptions: string representation of boolean value for debug flag

        Returns:
            Boolean value for debug flag

        """
        if debugOptions is None:
            return False
        elif debugOptions == "True":
            return True
        else:
            return False

    @staticmethod
    def findExecutable(executable='', path=None):
        """
        function for finding 'executable' in the directories listed in 'path'.

        Args:
            executable: the name of the executable file
            path: A string listing directories separated by 'os.pathsep'; defaults to os.environ['PATH'].

        Returns:
            the complete filename or None if not found.
        """
        if path is None:
            path = os.environ.get('PATH', os.defpath)

        paths = path.split(os.pathsep)
        # base, ext = os.path.splitext(executable)

        if sys.platform == 'win32' or os.name == 'os2':
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

    def IntelIMASCommand(self, tool='intelmas', operation='dump', outputFile='telemetry_data.bin', driveNumber=1):
        """
        function for generating a telemetry log using the intelmas tool commands

        Args:
            tool: String representation of the tool set to be used for the telemetry pull
            operation: String representation of the operation to be performed (refer to the notes below or the
                        documentation for the tool chosen)
            outputFile: String of the name for the output file
            driveNumber: Integer value for the drive ID number

        Returns:

        Notes:
            IMAS
                https://downloadmirror.intel.com/29337/eng/Intel_Memory_And_Storage_Tool_User%20Guide-Public-342245-001US.pdf
                https://downloadcenter.intel.com/download/29337/Intel-Memory-and-Storage-Tool-CLI-Command-Line-Interface-
                Commands
                    intelmas show -o json -intelssd
                    intelmas show -intelssd 1 -identify
                    intelmas dump -destination telemetry_data.bin -intelssd 1 -telemetrylog
                    intelmas dump -destination telemetry_data.bin -intelssd 1 -eventlog
        """
        import subprocess
        ret = False
        if (tool is not None and
                operation is not None and
                outputFile is not None and
                driveNumber is not None and
                self.findExecutable(executable=tool) is not None):
            cmd = '"{0}" {1} -destination {2} -intelssd {3} -telemetrylog'.format(
                tool, operation, outputFile, driveNumber
            )
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                ret, output = proc.communicate()
            except:
                print('Executing: {0}'.format(cmd))
                print('The command "%(cmd)s" failed with error ', 'code %(ret)i.' % locals())
        else:
            print("Failed to find executable file for specified tools.")
        return ret


class loadDrive(object):

    def __init__(self, inputFile, driveNumber, driveName, identifier, iterations, outputDir, debug):
        """
        function for initializing the loadSystem structure

        Args:
            inputFile: String for the path to the input file where the workload configuration is stored
            driveNumber: Integer for the drive number from which to pull telemetry data
            driveName: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
            iterations: Integer value for the number of data points to be considered for the time series
            outputDir: String for the path to the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Attributes:
            inputFile: String for the path to the input file where the workload configuration is stored
            driveNumber: Integer for the drive number from which to pull telemetry data
            driveName: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
            iterations: Integer value for the number of data points to be considered for the time series
            outputDir: String for the path to the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.inputFile = inputFile
        self.driveNumber = driveNumber
        self.driveName = driveName
        self.identifier = identifier
        self.iterations = iterations
        self.outputDir = outputDir
        self.debug = debug

    def prepDriveLinux(self):
        """
        function for prepping the specified drive using an automatically generated FIO script

        Returns:

        """
        prepFile = open("prepDriveLinux.sh", "w")
        fileLines = []
        fileLines.append("[global]\n")
        fileLines.append("direct=1\n")
        fileLines.append("filename=%s\n" % self.driveName)
        fileLines.append("size=100%\n")
        fileLines.append("log_avg_msec=1000\n")
        fileLines.append("ioengine=libaio")
        fileLines.append("\n")
        fileLines.append("[disk_fill]\n")
        fileLines.append("rw=write\n")
        fileLines.append("bs=64k\n")
        fileLines.append("iodepth=2\n")
        prepFile.writelines(fileLines)
        prepFile.close()

        prep = subprocess.Popen(["fio", "prepDriveLinux.sh", "--debug", "process"], stdout=subprocess.PIPE,
                                universal_newlines=True)
        newLine = prep.stdout.readline()
        while prep.poll() is None:
            print(newLine)
            newLine = prep.stdout.readline()
        print(newLine)
        stdout, _ = prep.communicate()
        lines = stdout.split("\n")
        for line in lines:
            print(line)
        print("The drive was prepped successfully!")

    def logCommandExecution(self, status, fileList, outFile, currentName):
        """
        function for printing the status of the test command execution

        Args:
            status: Boolean value returned from the test command execution
            fileList: List containing all the files that were succesfully generated using the test command
            outFile: String representation for the name of the output file where the results of the test command were
                     stored
            currentName: String representation for the name of the object that the test command is accessing

        Returns:

        """
        if status is False:
            print("parse" + currentName + "Failed")
        else:
            fileList.append(outFile)
            print("Writing " + currentName + " to: " + outFile)

    def collectDriveData(self, time=None, start=None):
        """
        function for collecting data from the drive

        Args:
            time: Integer for the number of seconds that the collection process should last for
            start: Time stamp for the start point

        Returns:
            fileListBandSizes: List of plain text file names that contain the data values for BandSizes
            fileListBandStates: List of plain text file names that contain the data values for BandStates
            fileListNandStats: List of plain text file names that contain the data values for NandStats
            fileListRberStats: List of plain text file names that contain the data values for RberStats
            fileListTelemetry: List of binary file names that contain the data values for Telemetry

        """
        fileListBandSizes = []
        fileListBandStates = []
        fileListNandStats = []
        fileListRberStats = []
        fileListTelemetry = []
        try:
            from src.software.twidl import device  # TWIDL dependency
            myDevice = device.Device.getDevice(devicePath=self.driveName,
                                               flags=device.DEV_BATCH_MODE | device.DEV_QUIET_MODE)
        except:
            print("ERROR: TWIDL path does not exist")
            myDevice = None
            pass

        if start is None:
            start = datetime.datetime.utcnow()

        for i in range(self.iterations):
            timeElapsed = round((((datetime.datetime.utcnow() - start).seconds * 10 ** 6) +
                                 (datetime.datetime.utcnow() - start).microseconds) / float(10 ** 6))
            if time is not None:
                if timeElapsed >= time: break

            # Generate file names and paths
            currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
            outFileBandSizes = "BandSizes-" + self.identifier + "_" + currentTimeUTCString + ".txt"
            outFileBandStates = "BandStates-" + self.identifier + "_" + currentTimeUTCString + ".txt"
            outFileNandStats = "NandStats-" + self.identifier + "_" + currentTimeUTCString + ".txt"
            outFileRberStats = "RberStats-" + self.identifier + "_" + currentTimeUTCString + ".txt"
            outFileTelemetry = "Telemetry-" + self.identifier + "_" + currentTimeUTCString + ".bin"
            folder = os.path.join(os.getcwd(), self.outputDir)
            outFileBandSizes = os.path.join(folder, outFileBandSizes)
            outFileBandStates = os.path.join(folder, outFileBandStates)
            outFileNandStats = os.path.join(folder, outFileNandStats)
            outFileRberStats = os.path.join(folder, outFileRberStats)
            outFileTelemetry = os.path.join(folder, outFileTelemetry)

            # Execute test commands
            statusBandSizes = myDevice.parseBandSizes(outFile=outFileBandSizes)
            statusBandStates = myDevice.parseBandStates(outputFile=outFileBandStates)
            statusNandStats = myDevice.parseNandStats(outFile=outFileNandStats)
            statusRberStats = myDevice.parseRberStats(outFile=outFileRberStats)
            statusTelemetry = loadDriveUtility().IntelIMASCommand(tool='intelmas', operation='dump',
                                                                  outputFile=outFileTelemetry,
                                                                  driveNumber=self.driveNumber)

            # Log status of execution
            self.logCommandExecution(statusBandSizes, fileListBandSizes, outFileBandSizes, "BandSizes")
            self.logCommandExecution(statusBandStates, fileListBandStates, outFileBandStates, "BandStates")
            self.logCommandExecution(statusNandStats, fileListNandStats, outFileNandStats, "NandStats")
            self.logCommandExecution(statusRberStats, fileListRberStats, outFileRberStats, "RberStats")
            self.logCommandExecution(statusTelemetry, fileListTelemetry, outFileTelemetry, "Telemetry")

        return fileListBandSizes, fileListBandStates, fileListNandStats, fileListRberStats, fileListTelemetry

    def processTextFilesInList(self, fileList, resultDict, currentName):
        """
        function for processing all text files contained in a list

        Args:
            fileList: list of text files produced by the test command
            resultDict: Dictionary containing the fields and values of the objects specified in the text files
            currentName: String representation for the name of the object under evaluation

        Returns:

        """
        for file in fileList:
            currentTime = DP.preprocessingAPI.getDateFromName(file)
            with open(file, 'r') as openFile:
                if self.debug is True:
                    print("Digesting file: " + file)
                loadDriveUtility().processTextFile(openFile, resultDict, currentName, currentTime)

    def aggregateData(self, fileListBandSizes, fileListBandStates, fileListNandStats, fileListRberStats,
                      outFile="time-series.ini"):
        """
        function for aggregating data values into a configuration file

        Args:
            fileListBandSizes: list of text files produced by the test command parseBandSizes
            fileListBandStates: list of text files produced by the test command parseBandStates
            fileListNandStats: list of text files produced by the test command parseNandStats
            fileListRberStats: list of text files produced by the test command parseRberStats
            outFile: String representation for the name of the output configuration file where the aggregated data will
                     be stored

        Returns:

        """
        config = cF.ConfigParser()
        if fileListBandSizes is None or fileListBandStates is None or fileListNandStats is None or \
                (fileListRberStats is None):
            raise Exception("Please specify a list of plain text files")

        resultDict = {}

        self.processTextFilesInList(fileListBandSizes, resultDict, "BandSizes")
        self.processTextFilesInList(fileListBandStates, resultDict, "BandStates")
        self.processTextFilesInList(fileListNandStats, resultDict, "NandStats")
        self.processTextFilesInList(fileListRberStats, resultDict, "RberStats")

        DP.preprocessingAPI.loadDictIntoConfig(config, resultDict)
        outDir = os.path.join(os.getcwd(), self.outputDir)
        os.chdir(outDir)
        with open(outFile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    def prepAndLoadDriveLinux(self, prepFlag=True, aggregateFlag=True, outFile="time-series.ini"):
        """
        Driver function for Linux. It calls on FIO to prepare the drives and execute the performance test in an
        independent subprocess, while the main process collects data values through test commands and telemetry

        Args:
            prepFlag: Boolean flag to indicate if the program should prep the drive before loading it
            aggregateFlag: Boolean flag to activate data aggregation after collection
            outFile: String representation for the name of the output configuration file where the aggregated data will
                     be stored

        Returns:

        """
        bashFile = open(self.inputFile)
        bashContent = bashFile.readlines()
        time_t = 1
        for line in bashContent:
            m = re.match("runtime=(\d+)", line)
            if m is not None:
                time_t = int(m.group(1))
                if self.debug:
                    print("Process will run for: " + str(time_t) + " seconds after the drive has been prepped")
        bashFile.close()
        if prepFlag:
            self.prepDriveLinux()
        fio = subprocess.Popen(["fio", self.inputFile, "--debug", "process"], stdout=subprocess.PIPE,
                               universal_newlines=True, bufsize=0)
        runningPattern = re.compile("RUNNING")
        newLine = fio.stdout.readline()
        while not runningPattern.search(newLine):
            if fio.poll() is not None:
                return
            newLine = fio.stdout.readline()
        loadDriveUtility().createDir(self.outputDir)
        fileListBandSizes, fileListBandStates, fileListNandStats, fileListRberStats, fileListTelemetry = self.collectDriveData(
            time=time_t)
        fio.wait()
        if aggregateFlag:
            self.aggregateData(fileListBandSizes, fileListBandStates, fileListNandStats, fileListRberStats,
                               outFile=outFile)

    def loadDriveAPI(self, prepFlag=True, aggregateFlag=True, outFile="time-series.ini"):
        """
        API to replace standard command line call (the loadDrive class has to instantiated before calling
        this method). This function also checks that the input file exists and it has the correct suffix

        Args:
            prepFlag: Boolean flag to indicate if the program should prep the drive before loading it
            aggregateFlag: Boolean flag to activate data aggregation after collection
            outFile: String representation for the name of the output configuration file where the aggregated data will
                     be stored

        Returns:

        """
        cwd = os.getcwd()
        filePath = os.path.join(cwd, self.inputFile)
        if not os.path.exists(filePath):
            print("Input file provided could not be accessed")
            return
        if sys.platform.startswith('linux'):
            if self.debug:
                print("Running script for Linux based OS")
            if self.inputFile[-3:].lower() != ".sh":
                print("Input file must be a bash script")
                return
            self.prepAndLoadDriveLinux(prepFlag=prepFlag, aggregateFlag=aggregateFlag, outFile=outFile)


def API(options=None):
    if options is None:
        print(f"Input Warning {locals()}")
        (options, args) = inputsAPI()

    driveNumber = loadDriveUtility().checkDriveNumber(options.driveNumber)
    driveName = loadDriveUtility().checkDriveName(options.driveName)
    inputFile = options.inputFile
    identifier = loadDriveUtility().checkIdentifier(options.identifier)
    iterations = loadDriveUtility().checkIterations(options.iterations)
    outputDir = loadDriveUtility().checkOutputDir(options.outputDir)
    outFile = loadDriveUtility().checkOutFile(options.outFile)
    debug = loadDriveUtility().checkDebugOption(options.debug)
    prepFlag = loadDriveUtility().checkBooleanOption(options.prepFlag)
    aggregateFlag = loadDriveUtility().checkBooleanOption(options.aggregateFlag)

    LD = loadDrive(inputFile=inputFile, driveNumber=driveNumber, driveName=driveName, identifier=identifier,
                   iterations=iterations, outputDir=outputDir, debug=debug)
    LD.loadDriveAPI(prepFlag=prepFlag, aggregateFlag=aggregateFlag, outFile=outFile)
    return 0


def inputsAPI(driveNumber=0, driveName=None, inputFile=None, identifier="Tv2HiTAC", outputDir='.', parse=False,
              volumeLabel="perftest", volumeAllocUnit="4096", volumeFS="ntfs", volumeLetter="g", partitionStyle="mbr",
              partitionFlag=True, prepFlag=True, debug=False):
    (options, args) = parseInputs()
    options.driveNumber = driveNumber
    options.driveName = driveName
    options.inputFile = inputFile
    options.identifier = identifier
    options.outputDir = outputDir
    options.parse = parse
    options.volumeLabel = volumeLabel
    options.volumeAllocUnit = volumeAllocUnit
    options.volumeFS = volumeFS
    options.volumeLetter = volumeLetter
    options.partitionStyle = partitionStyle
    options.partitionFlag = partitionFlag
    options.prepFlag = prepFlag
    options.debug = debug
    return (options, args)


def parseInputs():
    parser = optparse.OptionParser()
    parser.add_option("--driveNumber",
                      dest='driveNumber',
                      default=None,
                      help='Drive number from which to pull telemetry data')
    parser.add_option("--driveName",
                      dest='driveName',
                      default=None,
                      help='Name of device interface to get data from')
    parser.add_option("--inputFile",
                      dest='inputFile',
                      default=None,
                      help='Input file where the workload configuration is stored')
    parser.add_option("--identifier",
                      dest='identifier',
                      default=None,
                      help='Name of the data set that corresponds to the telemetry pull to be executed')
    parser.add_option("--iterations",
                      dest='iterations',
                      default=None,
                      help='Number of data points to be considered in the time series')
    parser.add_option("--outputDir",
                      dest='outputDir',
                      default=None,
                      help='Output directory where the text files will be stored')
    parser.add_option("--outFile",
                      dest='outFile',
                      default=None,
                      help='Output configuration file suffix (including .ini file extension) where the aggregated '
                           'data will be stored')
    parser.add_option("--prepFlag",
                      dest='prepFlag',
                      default=None,
                      help='Boolean flag to indicate if the program should prep the drive before loading it')
    parser.add_option("--aggregateFlag",
                      dest='aggregateFlag',
                      default=None,
                      help='Boolean flag to indicate if the program should aggregate all the data into a configuration '
                           'file (.ini file extension)')
    parser.add_option("--debug",
                      dest='debug',
                      default=None,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    return (options, args)


def main():
    """
    main function to be called when the script is directly executed from the
    command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    (options, args) = parseInputs()

    ##############################################
    # Main
    ##############################################
    return API(options=options)


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
