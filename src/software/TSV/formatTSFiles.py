# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Tyler Woods
# *****************************************************************************/
""" formatTSFiles.py

This module contains the basic functions for generating the plain text files and the ini files for a time series.
The plain text files have .txt suffix, while the ini files have .ini suffix

Args:
     --outfile: String for the name of the output file (must contain the .ini suffix)
     --outpath: String for the path of the output directory where the intermediate files will be stored
     --targetObject: String for the object name to be processed
     --fwDir: String for the path to the firmware build directory containing the python parsers
     --binDir: String for the path to the root directory containing the bin directories for the time series
     --mode: Integer value for run mode (1=buffDict, 2=autoParsers)
     --debug: Boolean flag to activate debug statements

Example:
    Default usage:
        $ python formatTSFiles.py
    Specific usage:
        $ python formatTSFiles.py --outfile time-series.ini --outpath ./time-series --targetObject ThermalSensor
                                    --fwDir ../projects/arbordaleplus_t2 --binDir ./binaries --debug True

"""
# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys, re, os, traceback, datetime, optparse, pprint, csv

sys.path.append('raad/src/software')
sys.path.append('raad/src/software/parse')
import src.software.parse.pacmanIC
import src.software.TSV.utilityTSV
import src.software.DP.preprocessingAPI as DP

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class formatTSFiles(object):
    debug = False

    class formatUtility:
        """
        Utility class to be used inside formatTSFiles

        """
        debug = False

        def __init__(self, debug=False):
            """
            function for initializing a formatTSFiles structure

            Args:
                debug: Boolean flag to activate debug statements

            Attributes:
                debug: Boolean flag to activate debug statements

            Returns:

            """
            self.debug = debug
            return

        def processDict(self, resultDict):
            """
            function that flattens the dictionary to be written into the csv file

            Args:
                resultDict: Dictionary to be flatten

            Returns:
                Flatten dictionary

            """
            flattenDict = {}
            for section in sorted(resultDict.keys()):
                subdict = resultDict[section]
                for option in sorted(subdict.keys()):
                    newName = str(section) + "." + str(option)
                    flattenDict[newName] = subdict[option]
            return flattenDict

        def _processObjectSignature(self, processedLine, resultDict, obj, processAll):
            """
            function for processing an object signature as contained in a single line of the plain text file

            Args:
                processedLine: String representation of the line to be processed
                resultDict: Dictionary containing all the structures for the objects processed so far
                obj: String for the name of the objects to be processed
                processAll: Boolean flag to indicate if all objects should be parsed (if True, obj will be ignored)

            Returns:
                3-element tuple of the identifier (uid-#) for the current object, its associated sub-directory of fields,
                and the string of the human-readable object name

            """
            currentObject = ""
            currentName = ""
            subdict = {}
            currentCore = 0
            for i in range(len(processedLine)):
                elements = processedLine[i].split()

                if i == 0:
                    currentObject = processedLine[i]
                    if currentObject in obj or processAll:
                        continue
                    else:
                        break
                elif i == 1:
                    currentCore = elements[1]
                elif i == 2:
                    currentName = "uid-" + elements[1]

                    if currentName not in resultDict:
                        resultDict[currentName] = {}
                    subdict = resultDict[currentName]

                    subdict["name"] = currentObject
                    if "core" in subdict:
                        subdict["core"].append(int(currentCore))
                    else:
                        subdict["core"] = [int(currentCore)]
                    subdict["uid"] = int(elements[1])

                else:
                    if len(elements) > 2:
                        fieldName = elements[0] + "-" + elements[1]
                        if fieldName in subdict:
                            subdict[fieldName].append(int(elements[2]))
                        else:
                            subdict[fieldName] = [int(elements[2])]
                    elif len(elements) > 1:
                        if elements[0] in subdict:
                            subdict[elements[0]].append(int(elements[1]))
                        else:
                            subdict[elements[0]] = [int(elements[1])]
                    else:
                        subdict["ref"] = elements[0]
            return currentName, subdict, currentObject

        def _processObjectContentBuffDict(self, line, processedLine, resultDict, subdict, currentName,
                                          objectFound, obj, processAll):
            """
            function for parsing an object's content into the general dictionary

            Args:
                line: Raw String representation for the line to be processed
                processedLine: String representation for the line externally modified
                resultDict: Dictionary containing all the structures for the objects processed so far
                subdict: Dictionary for the fields contained in the current object to be processed
                currentName: String for the name (uid-#) for the object to be processed
                objectFound: Boolean flag to indicate whether or not the current object is valid
                obj: String for the name of the objects to be processed
                processAll: Boolean flag to indicate if all objects should be parsed (if True, obj will be ignored)

            Returns:
                Tuple of a boolean flag to indicate if the next object is valid the next object's sub-directory of fields

            """
            objectPattern = re.compile("([A-Z,a-z]*):")
            flag = objectFound

            match = objectPattern.search(line)
            if match is not None:
                find = match.group(1)
                currentObj = find.replace(":", "")

                if currentObj in obj or processAll:
                    if currentName not in resultDict:
                        resultDict[currentName] = {}
                    subdict = resultDict[currentName]
                    flag = True
                else:
                    flag = False

            else:
                if objectFound:
                    if processedLine[0] in subdict:
                        subdict[processedLine[0]].append(int(processedLine[1]))
                    else:
                        subdict[processedLine[0]] = [int(processedLine[1])]

            return flag, subdict

        def _processObjectContentAutoParsers(self, line, subdict, currentHeaders):
            """
            function for parsing an object's content into the general dictionary

            Args:
                line: Raw String representation for the line to be processed
                subdict: Dictionary for the fields contained in the current object to be processed)
                currentHeaders: Dictionary containing the corresponding level headers

            Returns:

            """

            indentNum = int((len(line) - len(line.lstrip())) / 4)
            processedLine = line.strip()
            processedLine = processedLine.split(":")
            if len(processedLine) == 1:
                return
            elif processedLine[1] == "":
                headerValue = processedLine[0].strip()
                currentHeaders[indentNum] = headerValue
            else:
                for i in range(indentNum, len(currentHeaders)):
                    if indentNum in currentHeaders:
                        try:
                            currentHeaders.pop(i)
                        except Exception as ErrorFound:
                            # @todo dgarces
                            print(f"Error in {__file__} @{sys._getframe().f_lineno} with {ErrorFound}")
                    elif self.debug:
                        print(f"Error in {__file__} @{sys._getframe().f_lineno}")
                        print("Error objects: ", pprint.pformat(indentNum), pprint.pformat(currentHeaders))
                fieldName = ""
                for key in sorted(currentHeaders.keys()):
                    fieldName = fieldName + currentHeaders[key] + "."
                fieldName = fieldName + processedLine[0].strip()
                value = processedLine[1].strip()
                if fieldName in subdict:
                    subdict[fieldName].append(value)
                else:
                    subdict[fieldName] = [value]
            return

        def _processObjects(self, openFile, resultDict, obj=None, mode=1, processAll=False):
            """
            function that extracts the telemetry objects into a dictionary to be transferred to the ConfigParser

            Args:
                openFile: File descriptor for the open file
                resultDict: Dictionary containing the objects and fields previously found
                obj: String for the name of telemetry objects to be extracted from the plain text file
                mode: Integer value for run mode (1=buffDict, 2=autoParsers)
                processAll: Boolean flag to indicate if all objects should be parsed (if True, obj will be ignored)

            Returns:

            """
            textPattern = re.compile("[A-Z,a-z]")
            stopPattern = re.compile("#########")
            subdict = {}
            currentHeaders = {}
            objectFound = False
            currentName = ""
            currentObject = ""
            lines = openFile.readlines()

            if obj is None:
                obj = []

            for line in lines:
                if not textPattern.findall(line) or stopPattern.findall(line):
                    if objectFound:
                        objectFound = False
                    continue

                l = line.strip()
                match = re.search(",", line)

                if match is None:
                    l = l.split()
                else:
                    l = l.split(",")

                if len(l) == 8:
                    currentName, subdict, currentObject = self._processObjectSignature(l, resultDict, obj, processAll)
                    currentHeaders = {}
                    continue

                if mode == 1:
                    objectFound, subdict = self._processObjectContentBuffDict(line, l, resultDict, subdict, currentName,
                                                                              objectFound, obj, processAll)
                elif mode == 2:
                    if currentObject in obj or processAll:
                        self._processObjectContentAutoParsers(line, subdict, currentHeaders)
            return

        def processTextFile(self, openFile, resultDict, obj=None, mode=1):
            """
            function to process a single plain text file into the dictionary structure

            Args:
                openFile: File descriptor for the open file
                resultDict: Dictionary structure that will cantain all the objects, fields, and their respective values
                obj: String for the name of telemetry objects to be extracted from the plain text file
                mode: Integer value for run mode (1=buffDict, 2=autoParsers)

            Returns:

            """

            if obj is None:
                self._processObjects(openFile, resultDict, obj, mode=mode, processAll=True)
            else:
                obj = obj.split(",")
                self._processObjects(openFile, resultDict, obj, mode=mode, processAll=False)

    def __init__(self, outpath="sample", debug=False):
        """
        function for initializing a formatTSFiles structure

        Args:
            outpath: String for the path of the output directory where the plain text files will be stored
            debug: Boolean flag to activate debug statements

        Attributes:
            outpath: String for the path of the output directory where the plain text files will be stored
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.outpath = outpath
        self.debug = debug

    def getOutpath(self):
        """
        function for reading the outpath stored in the formatTSFiles attributes

        Returns:
            String for the path of the output directory where the plain text files will be stored

        """
        return self.outpath

    def getDebug(self):
        """
        function for reading the debug flag stored in the formatTSFiles attributes

        Returns:
            Boolean flag to activate debug statements

        """
        return self.debug

    def setOutpath(self, outpath):
        """
        function for setting the outpath stored in the formatTSFiles attributes

        Args:
            outpath: String for the path of the output directory where the plain text files will be stored

        Returns:

        """
        self.outpath = outpath

    def setDebug(self, debug):
        """
        function for setting the debug flag stored in the formatTSFiles attributes

        Args:
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.debug = debug

    def generatePlainText(self, fwDir=None, binDir="binaries", nlogFolder=None, mode=1, binList=None):
        """
        function to generate plain text files from the telemetry binary files

        Args:
            fwDir: String for the path to the firmware build directory containing the python parsers
            binDir: String for the path to the root directory containing the bin directories for the time series
            mode: Integer value for run mode (1=buffDict, 2=autoParsers)

        Returns:
            A list of plain text files generated from the telemetry binary files

        """
        outputFiles = []
        outputNlogFiles = []
        folder = os.path.join(os.getcwd(), binDir)
        if self.debug:
            print("Folder: " + folder)
        folder = os.path.abspath(folder)
        outDir = os.path.join(os.getcwd(), self.outpath)
        if not os.path.exists(outDir):
            os.mkdir(outDir)

        if self.debug:
            print("binList: ", binList)

        if os.path.exists(folder):

            if binList is None:
                premList = [dirName for dirName in os.listdir(folder) if
                            os.path.isdir(os.path.join(folder, dirName)) and
                            src.software.TSV.utilityTSV.utilityTSV().getDateFromName(dirName) is not None]
            else:
                premList = binList
            for dirName in sorted(premList,
                                  key=lambda dir_t: src.software.TSV.utilityTSV.utilityTSV().getDateFromName(dir_t)):
                if self.debug:
                    print("dirName: ", dirName)
                candidate = os.path.join(folder, dirName)

                if os.path.isdir(candidate):
                    outfile = dirName + ".txt"
                    outfileNlog = dirName + "_NLOG.txt"
                    if self.debug is True:
                        print("Generating: " + candidate)
                    out = os.path.join(outDir, outfile)
                    nlogDir = os.path.join(outDir, 'nlog')

                    if not os.path.exists(nlogDir):
                        os.mkdir(nlogDir)

                    outNlog = os.path.join(nlogDir, os.path.basename(outfileNlog))
                    print(outNlog)
                    pic = src.software.parse.pacmanIC.pacManIC(outLoc=out, nlogLoc=outNlog, debug=self.debug,
                                                           bin_t=candidate, projDir=fwDir, nlogDir=nlogFolder,
                                                           verbose=self.debug, mode=mode)
                    pic.pacmanICAPI()
                    outputFiles.append(out)
                    outputNlogFiles.append(outNlog)
            if self.debug:
                print("Output Files: " + str(outputFiles))
                print("NLOG Files: " + str(outputFiles))
            return outputFiles, outputNlogFiles
        else:
            raise Exception("Invalid root bin directory: " + folder)

    def processPlainTextFiles(self, plainTextFiles=None, outfile="time-series.ini", dataDictionaryDebugFileName=None, obj=None, mode=1):
        """

        Args:
            plainTextFiles:
            outfile:
            dataDictionaryDebugFileName:
            obj:
            mode:

        Returns:

        """

        if dataDictionaryDebugFileName is None:
            dataDictionaryDebugFileName = "dictionaryDebug" + datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f") + ".log"
            dataDictionaryDebugFileName = os.path.join(self.outpath, dataDictionaryDebugFileName)
        config = cF.ConfigParser()
        if plainTextFiles is None:
            raise Exception("Please specify a list of plain text files")

        resultDict = {}

        for plainTextFile in plainTextFiles:
            fileName = os.path.basename(plainTextFile)
            fileNameFields = fileName.split('_')
            dateField = fileNameFields[-1]
            dateField = dateField.replace('.txt', '')

            # additional object to keep time stamps
            objectName = "uid-4294967292"
            if objectName in resultDict:
                resultDict[objectName]['timestamp'].append(dateField)
                resultDict[objectName]['core'].append(0)
            else:
                resultDict[objectName] = {}
                resultDict[objectName]['timestamp'] = [dateField]
                resultDict[objectName]['core'] = [0]
                resultDict[objectName]['name'] = 'timestamp'

            with open(plainTextFile, 'r') as openFile:
                if self.debug is True:
                    print("Digesting file: " + plainTextFile)
                self.formatUtility().processTextFile(openFile, resultDict, obj=obj, mode=mode)

        if self.debug:
            print(f"Formatting Dictionary Debug File, depending on data size this can take sometime.")
            outDebugFile = os.path.join(self.outpath, dataDictionaryDebugFileName)
            with open(outDebugFile, 'w') as dictionaryCache:
                dictionaryCacheText = pprint.pformat(resultDict)
                dictionaryCache.write(dictionaryCacheText)
                dictionaryCache.close()
            print(f" Dictionary Debug File: {outDebugFile}")

        telemetyPayloadValidity = self.isTelemetryValid(resultDict=resultDict, threshold=0.6)
        if not telemetyPayloadValidity:
            print("Warning: Error with the dictionary files. Enable debug to get file dump.")
            return False

        DP.preprocessingAPI.loadDictIntoConfig(config, resultDict)
        csvDictionary = self.formatUtility().processDict(resultDict)
        outDir = os.path.join(os.getcwd(), self.outpath)
        outfile = os.path.join(outDir, outfile)
        with open(outfile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

        csvFileName = outfile.replace('.ini', '.csv')
        with open(csvFileName, 'w', newline='') as csvfile:
            telemetryWriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for field in csvDictionary:
                dataRow = list()
                dataRow.append(field.lower())
                if type(csvDictionary[field]) == 'list':
                    dataRow = dataRow + csvDictionary[field]
                    telemetryWriter.writerow(dataRow)
                else:
                    dataRow.append(csvDictionary[field])
                    telemetryWriter.writerow(dataRow)

        return True

    def extractNlogTime(self, line):
        if not isinstance(line, str): line = str(line)
        components = line.replace("*", "").split()
        dateComp = components[0]
        if dateComp.isdigit():
            dateComp = components[1]
        try:
            timeList = dateComp.split(":")
            hours = float(timeList[0])
            minutes = float(timeList[1])
            seconds = float(timeList[2])
            return (hours*60*60)+(minutes*60)+seconds
        except:
            print("Bad input line in extractNlogTime: ", line)


    def processNlogFiles(self, nlogFiles=None, outfile="time-series.ini"):
        """

        Args:
            nlogFiles:
            outfile:

        Returns:

        """

        if nlogFiles is None:
            raise Exception("Please specify a list of plain text files")

        nlogSet = set()
        headerNlog = []
        nlogEvents = []

        for nlogFile in nlogFiles:
            if self.debug is True:
                print("Digesting file: " + nlogFile)

            # fileName = os.path.basename(nlogFile)
            # fileNameFields = fileName.split('_')
            # dateField = fileNameFields[-2]

            openFile = open(nlogFile, 'r')
            index = 0
            for line in openFile:
                if line not in nlogSet:
                    nlogSet.add(line)
                    if index < 5:
                        headerNlog.append(line)
                        index += 1
                    else:
                        nlogEvents.append(line)
                        index += 1
                else:
                    index += 1
            openFile.close()


        newFileLines = sorted(nlogEvents, key=lambda line: self.extractNlogTime(line))

        outDir = os.path.join(os.getcwd(), self.outpath)
        outDir = os.path.join(outDir, "nlog")


        try:
            nlogFileName = outfile.replace('.ini', '_NLOG.txt')
            nlogFileName = os.path.join(outDir, nlogFileName)
            nlogOutFile = open(nlogFileName, 'w')
            nlogOutFile.writelines(headerNlog)
            nlogOutFile.writelines(newFileLines)
            nlogOutFile.close()
        except Exception as e:
            print("Fail to write combined NlogFile")
            print(e)
            return False

        return True

    def digestTextFiles(self, plainTextFiles=None, nlogFiles=None, outfile="time-series.ini", dataDictionaryDebugFileName=None, obj=None, mode=1):
        """
        function to accumulate the telemetry plain text files into a single configuration file to be used for the time series

        Args:
            plainTextFiles: List of plain text file names to be parsed into the configuration file
            outfile: String for the name of the output file (must contain the .ini suffix)
            dataDictionaryDebugFileName: debug data dump file for all uid tokens.
            obj: String for the name of telemetry objects to be extracted from the plain text files
            mode: Integer value for run mode (1=buffDict, 2=autoParsers)

        Returns: True if telemetry is valid

        """
        plainTextStatus = self.processPlainTextFiles(plainTextFiles=plainTextFiles, outfile=outfile,
                                                     dataDictionaryDebugFileName=dataDictionaryDebugFileName, obj=obj,
                                                     mode=mode)
        nlogStatus = self.processNlogFiles(nlogFiles=nlogFiles, outfile=outfile)

        return plainTextStatus and nlogStatus

    def formatTSFilesAPI(self, fwDir=None, binDir="binaries", outfile="time-series.ini", obj=None, mode=1,
                         binList=None, nlogFolder=None, timeStamp=None, debugFile=None, debug=None):
        """
        API to replace standard command line call (the formatTSFiles class has to instantiated before calling
        this method)

        Args:
            debugFile: data debug log file for understanding parser info.
            debug: developer debug flag.
            timeStamp: file formated time stamp
            binList:
            fwDir: String for the path to the firmware build directory containing the python parsers
            binDir: String for the path to the root directory containing the bin directories for the time series
            outfile: String for the name of the output file (must contain the .ini suffix)
            obj: String for the name of telemetry objects to be extracted from the plain text files
            mode: Integer value for run mode (1=buffDict, 2=autoParsers)

        Returns:

        """
        if debug is not None:
            self.debug = debug
        plainTextFiles, nlogFiles = self.generatePlainText(fwDir=fwDir, binDir=binDir, nlogFolder=nlogFolder, mode=mode, binList=binList)
        if debugFile is None:
            dataDictionaryFileName = str("dictionaryDebug_" + timeStamp + ".log")
        else:
            dataDictionaryFileName = debugFile
        return self.digestTextFiles(plainTextFiles=plainTextFiles, nlogFiles=nlogFiles, outfile=outfile,
                                    dataDictionaryDebugFileName=dataDictionaryFileName, obj=obj, mode=mode)

    def isTelemetryValid(self, resultDict, threshold=0.6):
        """
        Validate the collected telemetry data. For each data object, Check if each field is non-empty

        Args: None

        Returns: boolean (true if valid)
        """
        totalObj = len(resultDict)  # unused for now
        brokenFields = []
        for key, dataObject in resultDict.items():
            numBroken = 0
            for fieldkey, field in dataObject.items():
                if type(field) == list:
                    if len(field) <= 0:
                        numBroken += 1
                        brokenFields.append((key, fieldkey))
            percentage = numBroken / len(dataObject.keys())
            if percentage >= threshold:
                print("WARNING: Detected errors in gathered telemetry. Data-objects and broken fields include:")
                print(brokenFields)
                # log brokenFields to some file
                with open('time_series_errorlog.txt', 'w') as of:
                    for item in brokenFields:
                        of.write("%s\n" % str(item))
                return False
        return True


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--outfile",
                      dest='outfile',
                      default=None,
                      help='Output file where the condensed data will be stored')
    parser.add_option("--outpath",
                      dest='outpath',
                      default=None,
                      help='Output folder where the output file and intermediate files will be stored')
    parser.add_option("--targetObject",
                      dest='targetObject',
                      default=None,
                      help='Object name for the desired field to be processed')
    parser.add_option("--fwDir",
                      dest='fwDir',
                      default=None,
                      help='Path to the firmware build directory containing the python parsers')
    parser.add_option("--binDir",
                      dest='binDir',
                      default=None,
                      help='Path to the root directory containing the bin directories for the time series')
    parser.add_option("--modeSelect",
                      dest='mode',
                      default=None,
                      help='Integer value for run mode (1=buffDict, 2=autoParsers)')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    outfile = src.software.TSV.utilityTSV.utilityTSV().checkIniOutfile(options.outfile)
    outpath = src.software.TSV.utilityTSV.utilityTSV().checkOutpath(options.outpath)
    obj = options.targetObject
    fwd = src.software.TSV.utilityTSV.utilityTSV().checkFWDir(options.fwDir)
    bin_t = src.software.TSV.utilityTSV.utilityTSV().checkBinDir(options.binDir)
    mode = src.software.TSV.utilityTSV.utilityTSV().checkModeSelect(options.mode)
    debug = src.software.TSV.utilityTSV.utilityTSV().checkDebugOption(options.debug)

    formTSFiles = formatTSFiles(outpath=outpath, debug=debug)
    formTSFiles.formatTSFilesAPI(fwDir=fwd, binDir=bin_t, outfile=outfile, obj=obj, mode=mode)
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
