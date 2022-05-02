# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""utilityTSV.py

"""
import re
import datetime, os


class utilityTSV:
    @staticmethod
    def getDateFromName(dirName="sample", suffix=".bin"):
        """
        function to extract datetime object from directory name

        Args:
            dirName: String representation of the directory name

        Returns:
            datetime object containing the date parsed in the dirName

        """
        if not isinstance(dirName, str): dirName = str(dirName)
        components = dirName.replace(suffix, "").split("_")
        print("components: ", components)
        if len(components) < 2: return None
        date = components[-1][0:26]
        option = re.match('.*?([0-9]+)$', components[0])
        if option is not None:
            number = int(option.group(1))
        else:
            number = 0
        try:
            return datetime.datetime.strptime(date, '%Y-%m-%d-%H-%M-%S-%f'), number
        except:
            print("Bad input file in getDateFromName: ", dirName)

    @staticmethod
    def checkIniOutfile(outfile):
        """
        function to set the default value for outfile

        Args:
            outfile: name for the output file where the configs will be stored

        Returns:
            String value for the name of the output file

        """
        if outfile is None:
            return "time-series.ini"
        else:
            return outfile

    @staticmethod
    def checkOutpath(outpath):
        """
        function to set the default value for outfile

        Args:
            outpath: path for the output directory where the intermediate and output files will be stored

        Returns:
            String value for the path of the output directory

        """
        if outpath is None:
            return "telemetryDefault"
        else:
            return outpath

    @staticmethod
    def checkFWDir(fwDir):
        """
        function to set the default value for fwDir

        Args:
            fwDir: path to the firmware build directory containing the python parsers

        Returns:
            String representation of the path to the firmware build directory

        """
        if fwDir is None:
            return "project"
        else:
            return fwDir

    @staticmethod
    def checkBinDir(binDir):
        """
        function to set the default value for binDir

        Args:
            binDir: path to the root directory containing the bin directories for the time series

        Returns:
            String representation of the path to the root bin directory

        """
        if binDir is None:
            return "binaries"
        else:
            return binDir

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
        function to set the default value for driveName for the nvme-cli interface

        Args:
            driveName: Name of device interface to get data from

        Returns:
            String representation of the drive name

        """
        # @todo dgarces add windows varient detection.
        if driveName is None:
            return "/dev/nvme0n1"
        else:
            return driveName

    @staticmethod
    def checkInputDir(inputDir):
        """
        function to set the default value for inputDir

        Args:
            inputDir: path to the directory where the binaries are stored

        Returns:
            String representation of the path to the input directory

        """
        if inputDir is None:
            return "input-binaries"
        else:
            return inputDir

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
            return "binaries"
        else:
            return outputDir

    @staticmethod
    def checkModeSelect(modeSelect):
        """
        function to set the default value for modeSelect and turn it from
        a string into an int

        Args:
            modeSelect: string representation of int value for modeSelect flag

        Returns:
            Int value for modeSelect flag

        """
        if modeSelect is None:
            return 1
        else:
            return int(modeSelect)

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
    def checkNumCores(numCores):
        """
        function to set the default value for numCores and turn it from
        a string into an int

        Args:
            numCores: string representation of int value for the number of cores from which data was pulled

        Returns:
            Int value for number of cores

        """
        if numCores is None:
            return 1
        else:
            return int(numCores)

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
            return "Tv2HiTAC"
        else:
            return identifier

    @staticmethod
    def checkOutfile(outfile):
        """
        function to set the default value for outfile

        Args:
            outfile: Name for the output file where the visualizations will stored

        Returns:
            String representation of the name for the output file (without suffix)

        """
        if outfile is None:
            return "telemetryDefault"
        else:
            return outfile

    @staticmethod
    def checkInputFile(inputFile):
        """
        function to set the default value for inputFile

        Args:
            inputFile: Path of the file containing the config that describes the time series

        Returns:
            String representation of the path to the file containing the config for the time series

        """
        if inputFile is None:
            return "time-series.ini"
        else:
            return inputFile

    @staticmethod
    def checkCombine(combine):
        """
        function to set the default value for combine and turn it from
        a string into a boolean value

        Args:
            combine: string representation of boolean value for combine flag

        Returns:
            Boolean value for combine flag

        """
        if combine is None:
            return False
        elif combine == "True":
            return True
        else:
            return False

    @staticmethod
    def checkSubSeqLen(subSeqLen):
        """
        function to set the default value for subSeqLen and turn it from
        a string into an integer value

        Args:
            subSeqLen: string representation of integer value for length of sliding window for Matrix profile

        Returns:
            Integer value for the sliding window length

        """
        if subSeqLen is None:
            return 20
        else:
            return int(subSeqLen)

    @staticmethod
    def checkTransformTS(transformTS):
        """
        function to set the default value for transformTS and turn it from
        a string into a boolean value

        Args:
            transformTS: string representation of boolean value for transformTS flag

        Returns:
            Boolean value for transformTS flag

        """
        if transformTS is None:
            return False
        elif transformTS == "True":
            return True
        else:
            return False

    @staticmethod
    def checkParseOption(parseFlag):
        """
        function to set the default value for parse flag and turn it from
        a string into a boolean value

        Args:
            parseFlag: string representation of boolean value for parse flag

        Returns:
            Boolean value for parse flag

        """
        if parseFlag is None:
            return False
        elif parseFlag == "True":
            return True
        else:
            return False

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
