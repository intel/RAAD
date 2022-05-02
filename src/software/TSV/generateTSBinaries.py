# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
""" generateTSBinaries.py

This module contains the basic functions for generating the telemetry binary files for a time series.
It is assumed that telemetry pulls take approximately the same amount of time and they are evenly
spaced during the iterations

Args:
     --driveNumber: Integer value for the number of the drive from which telemetry data will be pulled
     --driveName: String for name of device interface to get data from
     --outputDir: String for the path of the output directory where the binaries will be stored
     --inputDir: String for the path of the input directory where the binaries to be parsed are stored
     --debug: Boolean flag to activate debug statements
     --modeSelect: Integer value for run mode (1=hybrid/nvme-cli, 2=internal, 3=parse-only, 4=intelmas)
     --iterations: Integer number of data points to be considered in the time series
     --identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
     --time: Integer time (in seconds) for which data will be collected

Example:
    Default usage:
        $ python generateTSBinaries.py
    Specific usage (for extracting telemetry):
        $ python generateTSBinaries.py --driveNumber 0 --outputDir sample
                                    --debug True --modeSelect 2 --iterations 20 --time 6
    Specific usage (for parsing only):
        $ python generateTSBinaries.py --outputDir sample --inputDir ../AllBinaries --debug True --modeSelect 3

"""

# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import os
import sys
import traceback
import datetime
import optparse
import src.software.TSV.utilityTSV
import src.software.access.binaryInterface as bI


class generateTSBinaries(object):
    class generateUtility:
        """
        Utility class to be used inside generateTSBinaries

        """

        @staticmethod
        def createDir(dirName):
            """
            function for changing cwd to the directory specified in dirName

            Args:
                dirName: String for path to destination directory

            Returns:

            """
            folder = os.path.join(os.getcwd(), dirName)
            if not os.path.exists(folder):
                os.mkdir(folder)

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

    def __init__(self, iterations=500, outpath=None, debug=False):
        """
        function for initializing the generateTSBinaries structure

        Args:
            iterations: Integer number of data points to be considered in the time series
            outpath: String for the path of the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Attributes:
            iterations: Integer number of data points to be considered in the time series
            outpath: String for the path of the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.iterations = iterations
        self.outpath = outpath
        self.debug = debug
        return

    def getIterations(self):
        """
        function for reading the iterations stored in the generateTSBinaries attributes

        Returns:
            Integer number of data points to be considered in the time series

        """
        return self.iterations

    def getOutpath(self):
        """
        function for reading the outpath stored in the generateTSBinaries attributes

        Returns:
            String for the path of the output directory where the binaries will be stored

        """
        return self.outpath

    def getDebug(self):
        """
        function for reading the debug flag stored in the generateTSBinaries attributes

        Returns:
            Boolean flag to activate debug statements

        """
        return self.debug

    def setIterations(self, iterations):
        """
        function for setting the iterations stored in the generateTSBinaries attributes

        Returns:

        """
        self.iterations = iterations

    def setOutpath(self, outpath):
        """
        function for setting the outpath stored in the generateTSBinaries attributes

        Returns:

        """
        self.outpath = outpath

    def setDebug(self, debug):
        """
        function for setting the debug flag stored in the generateTSBinaries attributes

        Returns:

        """
        self.debug = debug

    def hybridGetTelemetry(self, time=None, start=None, device=None, identifier="Tv2HiTAC"):
        """
        function for getting telemetry binary using the nvme-cli interface

        Args:
            time: Integer time (in seconds) for which data will be collected
            start: Time at which the operation is supposed to start recording values
            device: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            A list of names for the telemetry bin files generated
        """
        fileList = []
        if start is None:
            start = datetime.datetime.utcnow()
        ncp = bI.nvmeCliProcesses(debug=self.debug)
        for i in range(self.iterations):
            timeElapsed = round((((datetime.datetime.utcnow() - start).seconds * 10 ** 6) +
                                 (datetime.datetime.utcnow() - start).microseconds) / float(10 ** 6))
            if time is not None:
                if timeElapsed >= time:
                    break
            currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
            outFile = identifier + "_" + currentTimeUTCString + ".bin"
            outFile = os.path.join(self.outpath, outFile)
            if self.debug is True:
                print("Writing to: " + outFile)

            ncp.readTelemetry(device, hostGenerate=True, outFile=outFile)
            fileList.append(outFile)
        return fileList

    def genericParseTelemetry(self, fileList=None):
        """
        function for parsing a list of binary files

        Args:
            fileList: List of binary files' names or paths

        Returns:
            A list of names for the folders where the parsed binary files are stored
        """
        iterator = 0
        folderList = []

        if self.iterations is not len(fileList):
            self.iterations = len(fileList)

        for file in fileList:
            if self.iterations is not None:
                if iterator == self.iterations:
                    break

            if os.path.isfile(file):
                fileName = os.path.basename(file)
                outFolder = fileName.replace(".bin", "")

                if self.outpath is not None:
                    outFolder = os.path.join(self.outpath, outFolder)

                binCache = bI.binProcesses(telemetryBinary=file, debug=self.debug)
                binCache.parseTelemetryBinaryFile(outpath=outFolder)
                if self.debug is True:
                    print("Parsed binary files stored in: " + outFolder)
                folderList.append(outFolder)
                iterator += 1
        return folderList

    def hybridGetBinary(self, time=None, device=None, identifier="Tv2HiTAC"):
        """
        function to generate the binary files using the nvme-cli commands

        Args:
            time: Integer time (in seconds) for which data will be collected
            device: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            Two lists: one for files and another one for folders generated

        """
        start = datetime.datetime.now()
        self.generateUtility().createDir(self.outpath)
        fileList = self.hybridGetTelemetry(time=time, device=device, identifier=identifier)
        folderList = self.genericParseTelemetry(fileList=fileList)
        stop = datetime.datetime.now()
        print("Execution time of hybrid mode: " + str(stop - start))
        return fileList, folderList

    def internalGetTelemetry(self, time=None, start=None, driveNum=None, identifier="Tv2HiTAC"):
        """
        Function for getting telemetry binary using the TWIDL interface

        Args:
            time: Integer time (in seconds) for which data will be collected
            start: Time at which the operation is supposed to start recording values
            driveNum: Integer value for the number of the drive from which telemetry data will be pulled
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            A list of names for the telemetry bin files generated

        """
        fileList = []
        if start is None:
            start = datetime.datetime.utcnow()
        for i in range(self.iterations):
            timeElapsed = round((((datetime.datetime.utcnow() - start).seconds * 10 ** 6) +
                                 (datetime.datetime.utcnow() - start).microseconds) / float(10 ** 6))
            if time is not None:
                if timeElapsed >= time:
                    break
            currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
            outFile = identifier + "_" + currentTimeUTCString + ".bin"
            outFile = os.path.join(self.outpath, outFile)
            if self.debug is True:
                print("Writing to: " + outFile)
            binCache = bI.binProcesses(telemetryBinary=outFile, debug=self.debug)
            binCache.readDrive(driveNum=driveNum)
            fileList.append(outFile)
        return fileList

    def internalGetBinary(self, time=None, driveNum=None, identifier="Tv2HiTAC"):
        """
        function to generate the binary files using the internal TWIDL commands

        Args:
            time: Integer time (in seconds) for which data will be collected
            driveNum: Integer value for the number of the drive from which telemetry data will be pulled
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            Two lists: one for files and another one for folders generated

        """
        start = datetime.datetime.now()
        self.generateUtility().createDir(self.outpath)
        fileList = self.internalGetTelemetry(time=time, driveNum=driveNum, identifier=identifier)
        folderList = self.genericParseTelemetry(fileList=fileList)
        stop = datetime.datetime.now()
        print("Execution time of internal mode: " + str(stop - start))
        return fileList, folderList

    @staticmethod
    def GetSortedConfigFiles(inputFolder, suffix=".bin", latest=False):
        fileList = None
        try:
            fileList = [os.path.join(inputFolder, file)
                        for file in sorted([file for file in os.listdir(inputFolder) if file.endswith(suffix)
                                            and src.software.TSV.utilityTSV.utilityTSV().getDateFromName(file, suffix=suffix) is not None],
                                           key=lambda dir_t:
                                           src.software.TSV.utilityTSV.utilityTSV().getDateFromName(dir_t, suffix=suffix))
                        ]
        except TypeError:
            exit(1)
        if fileList is None or fileList is []:
            return ""
        elif latest:
            try:
                return fileList[-1]
            except IndexError:
                return ""
        else:
            return fileList

    def parseBinaryOnly(self, inputFolder=None):
        """
        function for parsing all binary files contained in a given directory

        Args:
            inputFolder: String of the relative path to the directory containing all the binary files to be parsed

        Returns:
            Two lists: one for files parsed and another one for folders generated
        """
        start = datetime.datetime.now()

        if os.path.exists(inputFolder) is False:
            inputFolder = os.path.abspath(os.path.join(os.getcwd(), inputFolder))
        try:  # Try to process by file name
            fileList = self.GetSortedConfigFiles(inputFolder)

        except:  # Process by file creation date.
            fileList = [os.path.join(inputFolder, file) for file in os.listdir(inputFolder) if (file.lower().endswith('.bin'))]
            fileList.sort(key=os.path.getmtime)
            if self.debug:
                for file in sorted(fileList, key=os.path.getmtime):
                    print("Found File {}".format(file))

        if self.outpath is not None:
            try:
                outfolder = os.path.join(os.getcwd(), self.outpath)
            except:
                outfolder = os.path.abspath(self.outpath)
            if not os.path.exists(outfolder):
                os.mkdir(outfolder)

        folderList = self.genericParseTelemetry(fileList=fileList)
        stop = datetime.datetime.now()
        print("Execution time of parse-only mode: " + str(stop - start))
        return fileList, folderList

    def intelmasGetTelemetry(self, time=None, start=None, driveNum=None, identifier="Tv2HiTAC"):
        """
        Function for getting telemetry binary using intelmas commands

        Args:
            time: Integer time (in seconds) for which data will be collected
            start: Time at which the operation is supposed to start recording values
            driveNum: Integer value for the number of the drive from which telemetry data will be pulled
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            A list of names for the telemetry bin files generated

        """
        fileList = []
        if start is None:
            start = datetime.datetime.utcnow()
        for i in range(self.iterations):
            timeElapsed = round((((datetime.datetime.utcnow() - start).seconds * 10 ** 6) +
                                 (datetime.datetime.utcnow() - start).microseconds) / float(10 ** 6))
            if time is not None:
                if timeElapsed >= time:
                    break
            currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
            outFile = identifier + "_" + currentTimeUTCString + ".bin"
            outFile = os.path.join(self.outpath, outFile)
            if self.debug is True:
                print("Writing to: " + outFile)
            self.generateUtility().IntelIMASCommand(tool='intelmas', operation='dump', outputFile=outFile,
                                                    driveNumber=driveNum)
            fileList.append(outFile)
        return fileList

    def intelmasGetBinary(self, time=None, driveNum=None, identifier="Tv2HiTAC"):
        """
        function to generate the binary files using the intelmas commands

        Args:
            time: Integer time (in seconds) for which data will be collected
            driveNum: Integer value for the number of the drive from which telemetry data will be pulled
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed

        Returns:
            Two lists: one for files and another one for folders generated

        """
        start = datetime.datetime.now()
        self.generateUtility().createDir(self.outpath)
        fileList = self.intelmasGetTelemetry(time=time, driveNum=driveNum, identifier=identifier)
        folderList = self.genericParseTelemetry(fileList=fileList)
        stop = datetime.datetime.now()
        print("Execution time of intelmas mode: " + str(stop - start))
        return fileList, folderList

    def generateTSBinariesAPI(self, mode=3, time=None, driveName="/dev/nvme0n1", driveNumber=0, identifier="Tv2HiTAC",
                              inputFolder="input-binaries"):
        """
        API to replace standard command line call (the generateTSBinaries class has to instantiated before calling
        this method)

        Args:
            mode: Integer value for run mode (1=hybrid/nvme-cli, 2=internal, 3=parse-only)
            time: Integer time (in seconds) for which data will be collected
            driveName: String for name of device interface to get data from
            driveNumber: Integer value for the number of the drive from which telemetry data will be pulled
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
            inputFolder: String of the relative path to the directory containing all the binary files to be parsed

        Returns:

        """
        # {"CLI": 1, "TWIDL": 2, "PARSE": 3, "IMAS": 4}
        if mode == 1 or mode == "CLI":
            return self.hybridGetBinary(time=time, device=driveName, identifier=identifier)
        elif mode == 2 or mode == "TWIDL":
            return self.internalGetBinary(time=time, driveNum=driveNumber, identifier=identifier)
        elif mode == 3 or mode == "PARSE":
            return self.parseBinaryOnly(inputFolder=inputFolder)
        elif mode == 4 or mode == "IMAS":
            return self.intelmasGetBinary(time=time, driveNum=driveNumber, identifier=identifier)
        else:
            print("Invalid mode number. Please enter a valid mode (1-4).")


def main():
    """
    main function to be called when the script is directly executed from the
    command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--driveNumber",
                      dest='driveNumber',
                      default=None,
                      help='Drive number from which to pull telemetry data')
    parser.add_option("--driveName",
                      dest='driveName',
                      default=None,
                      help='Name of device interface to get data from')
    parser.add_option("--outputDir",
                      dest='outputDir',
                      default=None,
                      help='Output directory where the binaries will be stored')
    parser.add_option("--inputDir",
                      dest='inputDir',
                      default=None,
                      help='Input directory where the binaries to be parsed are stored (only used for mode 3)')
    parser.add_option("--debug",
                      dest='debug',
                      default=None,
                      help='Debug mode')
    parser.add_option("--modeSelect",
                      dest='modeSelect',
                      default=None,
                      help='Flag to indicate run mode (1=hybrid, 2=internal, 3=only-parsing)')
    parser.add_option("--iterations",
                      dest='iterations',
                      default=None,
                      help='Number of data points to be considered in the time series')
    parser.add_option("--time",
                      dest='time',
                      default=None,
                      help='Time (in seconds) for which data will be collected')
    parser.add_option("--identifier",
                      dest='identifier',
                      default=None,
                      help='Name of the data set that corresponds to the telemetry pull to be executed')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    driveNumber = src.software.TSV.utilityTSV.utilityTSV().checkDriveNumber(options.driveNumber)
    driveName = src.software.TSV.utilityTSV.utilityTSV().checkDriveName(options.driveName)
    outputDir = src.software.TSV.utilityTSV.utilityTSV().checkOutputDir(options.outputDir)
    inputDir = src.software.TSV.utilityTSV.utilityTSV().checkInputDir(options.inputDir)
    identifier = src.software.TSV.utilityTSV.utilityTSV().checkIdentifier(options.identifier)
    debug = src.software.TSV.utilityTSV.utilityTSV().checkDebugOption(options.debug)
    mode = src.software.TSV.utilityTSV.utilityTSV().checkModeSelect(options.modeSelect)
    iterations = src.software.TSV.utilityTSV.utilityTSV().checkIterations(options.iterations)

    if options.time is not None:
        time = int(options.time)
    else:
        time = options.time

    if debug is True:
        print("Mode is: " + str(mode))
        print("Iterations: " + str(iterations))
        print("OutputDir: " + outputDir)
        print("inputDir: " + inputDir)

    gen = generateTSBinaries(iterations=iterations, outpath=outputDir, debug=debug)
    gen.generateTSBinariesAPI(mode=mode, time=time, driveName=driveName, driveNumber=driveNumber,
                              identifier=identifier, inputFolder=inputDir)

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
