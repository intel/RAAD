# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
""" loadAndProbeSystem.py

This module contains the basic functions for generating a load, preparing a drive and pulling telemetry data from it.
It uses IOMeter when running on Windows and FIO when running in Linux. The input file must be a csv file when running
on Windows and a bash script when running on Linux. The drive number of the device to be tested must be passed in both,
the configuration file and as an argument. The configuration files must have time-based execution for proper telemetry
extraction.

Args:
    --driveNumber: Integer for the drive number from which to pull telemetry data
    --driveName: String for name of device interface to get data from
    --inputFile: String for the path to the input file where the workload configuration is stored
    --identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
    --outputDir: String for the path to the output directory where the binaries will be stored
    --parse: Boolean flag to parse the telemetry binaries pulled from the drive
    --volumeLabel: String for the label to be used on the disk volume
    --volumeAllocUnit: String for the volume allocation unit size
    --volumeFS: String for the name of the file system to be used in the disk volume
    --volumeLetter: String for the letter to be assigned to the disk volume
    --partitionStyle: String for the name of the partition style to be used in the specified disk
    --partitionFlag: Boolean flag to indicate if the program should partition the drive using the given parameters
    --prepFlag: Boolean flag to indicate if the program should prep the drive before loading it
    --debug: Boolean flag to activate verbose printing for debug use


Example:
    Default usage (Windows - must be run as administrator):
        $ python loadAndProbeSystem.py
    Default usage (Linux):
        $ sudo python loadAndProbeSystem.py
    Specific usage (Windows - must be run as administrator):
        $ python loadAndProbeSystem.py --driveNumber 1 --inputFile Thermal-4KSW1QD1W.csv --identifier Tv2Hi
            --parse True --outputDir binaries --debug True
    Specific usage (Linux):
        $ sudo python loadAndProbeSystem.py --driveNumber 0 --inputFile rand-write.sh --identifier Tv2Hi --parse True
            --outputDir binaries --debug True

"""
import os
import re
import sys
import csv
import optparse
import datetime
import traceback
import subprocess
import src.software.TSV.generateTSBinaries
import src.software.TSV.utilityTSV
from multiprocessing import Process


class loadSystem(object):

    def __init__(self, inputFile, driveNumber, driveName, identifier, outputDir, debug):
        """
        function for initializing the loadSystem structure

        Args:
            inputFile: String for the path to the input file where the workload configuration is stored
            driveNumber: Integer for the drive number from which to pull telemetry data
            driveName: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
            outputDir: String for the path to the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Attributes:
            inputFile: String for the path to the input file where the workload configuration is stored
            driveNumber: Integer for the drive number from which to pull telemetry data
            driveName: String for name of device interface to get data from
            identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
            outputDir: String for the path to the output directory where the binaries will be stored
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.inputFile = inputFile
        self.driveNumber = driveNumber
        self.driveName = driveName
        self.identifier = identifier
        self.outputDir = outputDir
        self.debug = debug
        return

    def partitionDriveWindows(self, volumeLabel="PERFTEST", volumeAllocUnit="4096", volumeFS="ntfs", volumeLetter="G",
                              partitionStyle="mbr"):
        """
        function for partitioning the specified drive using an automatically generated diskpart script for Windows

        Args:
            volumeLabel: String for the label to be used on the disk volume
            volumeAllocUnit: String for the volume allocation unit size
            volumeFS: String for the name of the file system to be used in the disk volume
            volumeLetter: String for the letter to be assigned to the disk volume
            partitionStyle: String for the name of the partition style to be used in the specified disk

        Returns:

        """
        diskpartFile = open("partitionDriveWindows.txt", "w")
        fileLines = []
        fileLines.append("select disk " + str(self.driveNumber) + "\n")
        fileLines.append("clean\n")
        fileLines.append("convert %s\n" % partitionStyle)
        fileLines.append("create partition primary\n")
        fileLines.append("format quick fs=%s label=\"%s\" unit=%s\n" % (volumeFS, volumeLabel, volumeAllocUnit))
        fileLines.append("assign letter=%s\n" % volumeLetter)
        fileLines.append("exit\n")
        diskpartFile.writelines(fileLines)
        diskpartFile.close()

        diskpart = subprocess.Popen("diskpart /s partitionDriveWindows.txt", stdout=subprocess.PIPE,
                                    universal_newlines=True)
        stdout, _ = diskpart.communicate()
        lines = stdout.split("\n")
        for line in lines:
            print(line)
        print("The drive was partitioned successfully!")

    def prepDriveWindows(self):
        """
        function for prepping the specified drive for testing. It uses the input file specified during initialization
        to obtain the configuration settings.

        Returns:
            testing: IometerTestSchedule object
        """
        import src.software.external.IOMeter.IometerTestSchedule as ITS
        print("Parsing Schedule File - %s" % (self.inputFile))
        testing = ITS.IometerTestSchedule(self.inputFile, 'result.csv')
        print("Parsing Complete")

        if ((testing.prepDrive >= 1) and (testing.physDrive == 0)):
            print("Preping drive(s) with 64KB sequential write.")
            testing.createPrepFile("driveprep.icf")
            iometer = subprocess.Popen("iometer.exe driveprep.icf driveprep.csv")
            iometer.wait()
            print("Drive prep complete.")

        if (testing.physDrive == 1):
            print(
                "Testing drive in physical mode.  No drive prep will be performed, be sure the drive is in the proper " +
                "state for testing.")

        return testing

    def loadDriveWindows(self, testSchedule):
        """
        function for loading the drive and executing the performance test

        Args:
            testSchedule: IometerTestSchedule object containing the input file

        Returns:

        """
        count = 0
        while (testSchedule.nextTestFile("testfile.icf")):
            testname = testSchedule.currTestName
            print("Running test %d - %s" % (count, testname))
            iometer = subprocess.Popen("iometer.exe testfile.icf %s.csv" % testname)
            iometer.wait()
            testSchedule.insertResult("inst%s.csv" % testname)
            count += 1

        print("All testing complete")

    def prepAndLoadDriveWindows(self, parse=False, volumeLabel="PERFTEST", volumeAllocUnit="4096", volumeFS="ntfs",
                                volumeLetter="G", partitionStyle="mbr", partitionFlag=True):
        """
        Driver function for windows. It calls on IOMeter to prepare the drives and execute the performance test in an
        independent process, while the main process collects telemetry via generateTSBinaries

        Args:
            parse: Boolean flag to parse the telemetry binaries pulled from the drive
            volumeLabel: String for the label to be used on the disk volume
            volumeAllocUnit: String for the volume allocation unit size
            volumeFS: String for the name of the file system to be used in the disk volume
            volumeLetter: String for the letter to be assigned to the disk volume
            partitionStyle: String for the name of the partition style to be used in the specified disk
            partitionFlag: Boolean flag to indicate if the program should partition the drive using the given parameters

        Returns:

        """
        csvFile = open(self.inputFile)
        csvSchedule = csv.reader(csvFile)
        time_t = 1
        for row in csvSchedule:
            if row[0] == 'RUN' and len(row) > 7:
                time_t = int(row[6])
            elif row[0] == "IDLE" and len(row) == 2:
                time_t = int(row[1])
        if time_t == 1:
            print("Invalid configuration for the CSV file, using 1s for time")
        print("Time used for collecting telemetry: " + str(time_t) + " seconds")
        csvFile.close()
        if partitionFlag:
            self.partitionDriveWindows(volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit, volumeFS=volumeFS,
                                       volumeLetter=volumeLetter, partitionStyle=partitionStyle)
        testSchedule = self.prepDriveWindows()
        p = Process(target=self.loadDriveWindows, args=(testSchedule,))
        gen = src.software.TSV.generateTSBinaries.generateTSBinaries(outpath=self.outputDir, debug=self.debug, iterations=100000)
        p.start()
        if self.debug:
            print("Pulling Telemetry from drive " + str(self.driveNumber) + " for " + str(time_t) + " seconds")
        gen.generateUtility().createDir(self.outputDir)

        fileList = gen.intelmasGetTelemetry(time=time_t, driveNum=self.driveNumber, identifier=self.identifier)
        print("Telemetry pull finished ...")
        p.join()
        if parse:
            if self.debug:
                print("Parsing binary files ...")
            gen.genericParseTelemetry(fileList=fileList)

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

    def prepAndLoadDriveLinux(self, parse=False, prepFlag=True):
        """
        Driver function for Linux. It calls on FIO to prepare the drives and execute the performance test in an
        independent subprocess, while the main process collects telemetry via generateTSBinaries

        Args:
            parse: Boolean flag to parse the telemetry binaries pulled from the drive
            prepFlag: Boolean flag to indicate if the program should prep the drive before loading it

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
        gen = src.software.TSV.generateTSBinaries.generateTSBinaries(outpath=self.outputDir, debug=self.debug)
        newLine = fio.stdout.readline()
        while (not runningPattern.search(newLine)):
            if fio.poll() is not None:
                return
            newLine = fio.stdout.readline()
        gen.generateUtility().createDir(self.outputDir)
        fileList = gen.intelmasGetTelemetry(time=time_t, driveNum=self.driveNumber, identifier=self.identifier)
        fio.wait()
        if parse:
            gen.genericParseTelemetry(fileList=fileList)

    def loadSystemAPI(self, parse=False, volumeLabel="PERFTEST", volumeAllocUnit="4096", volumeFS="ntfs",
                      volumeLetter="G", partitionStyle="mbr", partitionFlag=True, prepFlag=True):
        """
        API to replace standard command line call (the loadSystem class has to instantiated before calling
        this method). This function also checks that the input file exists and it has the correct suffix

        Args:
            parse: Boolean flag to parse the telemetry binaries pulled from the drive
            volumeLabel: (Windows) String for the label to be used on the disk volume
            volumeAllocUnit: (Windows) String for the volume allocation unit size
            volumeFS: (Windows) String for the name of the file system to be used in the disk volume
            volumeLetter: (Windows) String for the letter to be assigned to the disk volume
            partitionStyle: (Windows) String for the name of the partition style to be used in the specified disk
            partitionFlag: (Windows) Boolean flag to indicate if the program should partition the drive using the given
                            parameters
            prepFlag: (Linux) Boolean flag to indicate if the program should prep the drive before loading it

        Returns:

        """
        cwd = os.getcwd()
        filePath = os.path.join(cwd, self.inputFile)
        if not os.path.exists(filePath):
            print("Input file provided could not be accessed")
            return
        if sys.platform.startswith('win32'):
            if self.debug:
                print("Running script for Windows OS")
            if self.inputFile[-4:].lower() != ".csv":
                print("Input file must be a csv file")
                return
            self.prepAndLoadDriveWindows(parse=parse, volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit,
                                         volumeFS=volumeFS, volumeLetter=volumeLetter, partitionStyle=partitionStyle,
                                         partitionFlag=partitionFlag)
        elif sys.platform.startswith('linux'):
            if self.debug:
                print("Running script for Linux based OS")
            if self.inputFile[-3:].lower() != ".sh":
                print("Input file must be a bash script")
                return
            self.prepAndLoadDriveLinux(parse=parse, prepFlag=prepFlag)


def API(options=None):
    if options is None:
        print(f"Input Warning {locals()}")
        (options, args) = parseInputs()
    driveNumber = src.software.TSV.utilityTSV.utilityTSV().checkDriveNumber(options.driveNumber)
    driveName = src.software.TSV.utilityTSV.utilityTSV().checkDriveName(options.driveName)
    inputFile = options.inputFile
    identifier = src.software.TSV.utilityTSV.utilityTSV().checkIdentifier(options.identifier)
    outputDir = src.software.TSV.utilityTSV.utilityTSV().checkOutputDir(options.outputDir)
    debug = src.software.TSV.utilityTSV.utilityTSV().checkDebugOption(options.debug)
    parse = src.software.TSV.utilityTSV.utilityTSV().checkParseOption(options.parse)
    volumeLabel = options.volumeLabel
    volumeAllocUnit = options.volumeAllocUnit.lower()
    volumeFS = options.volumeFS.lower()
    volumeLetter = options.volumeLetter.lower()
    partitionStyle = options.partitionStyle.lower()
    partitionFlag = src.software.TSV.utilityTSV.utilityTSV().checkBooleanOption(options.partitionFlag)
    prepFlag = src.software.TSV.utilityTSV.utilityTSV().checkBooleanOption(options.prepFlag)
    LS = loadSystem(inputFile, driveNumber, driveName, identifier, outputDir, debug)
    LS.loadSystemAPI(parse=parse, volumeLabel=volumeLabel, volumeAllocUnit=volumeAllocUnit, volumeFS=volumeFS,
                     volumeLetter=volumeLetter, partitionStyle=partitionStyle, partitionFlag=partitionFlag,
                     prepFlag=prepFlag)
    return 0


def inputsAPI(driveNumber=0,
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
              debug=False):
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
    args = None
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
    parser.add_option("--outputDir",
                      dest='outputDir',
                      default='.',
                      help='Output directory where the binaries will be stored')
    parser.add_option("--parse",
                      dest='parse',
                      default='.',
                      help='Boolean flag to parse the telemetry binaries pulled from the drive')
    parser.add_option("--volumeLabel",
                      dest='volumeLabel',
                      default="PERFTEST",
                      help='String for the label to be used on the disk volume')
    parser.add_option("--volumeAllocUnit",
                      dest='volumeAllocUnit',
                      default="4096",
                      help='String for the volume allocation unit size')
    parser.add_option("--volumeFS",
                      dest='volumeFS',
                      default="ntfs",
                      help='String for the name of the file system to be used in the disk volume')
    parser.add_option("--volumeLetter",
                      dest='volumeLetter',
                      default="G",
                      help='String for the letter to be assigned to the disk volume')
    parser.add_option("--partitionStyle",
                      dest='partitionStyle',
                      default="mbr",
                      help='String for the name of the partition style to be used in the specified disk')
    parser.add_option("--partitionFlag",
                      dest='partitionFlag',
                      default=True,
                      help=' Boolean flag to indicate if the program should partition the drive using the given '
                           'parameters')
    parser.add_option("--prepFlag",
                      dest='prepFlag',
                      default=True,
                      help='Boolean flag to indicate if the program should prep the drive before loading it')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
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
